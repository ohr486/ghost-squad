"""InquiryWorkflowServiceのユニットテスト.

要件3.1-3.12をカバーするワークフローサービスのテスト。
"""
from datetime import datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.database.base import BaseModel
from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus
from services.inquiry_repository import CreateInquiryData, InquiryRepository
from services.inquiry_workflow_service import (
    InquiryWorkflowService,
    InvalidStateTransitionError,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    BaseModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestInquiryWorkflowService:
    """InquiryWorkflowServiceのテストクラス."""

    @pytest.fixture
    def repository(self, db_session: Session) -> InquiryRepository:
        """InquiryRepositoryのフィクスチャ."""
        return InquiryRepository(db_session)

    @pytest.fixture
    def workflow_service(self, repository: InquiryRepository) -> InquiryWorkflowService:
        """InquiryWorkflowServiceのフィクスチャ."""
        return InquiryWorkflowService(repository)

    @pytest.fixture
    def received_inquiry(self, repository: InquiryRepository) -> InquiryModel:
        """RECEIVEDステータスの問い合わせフィクスチャ."""
        data = CreateInquiryData(
            user_id="test_user",
            content="テスト問い合わせ",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        return repository.create(data)

    # 要件3.1-3.3: 承認機能のテスト
    def test_approve_inquiry_success(
        self,
        workflow_service: InquiryWorkflowService,
        received_inquiry: InquiryModel,
    ) -> None:
        """承認フローの正常系テスト（received → task_working）.

        要件3.1: 問い合わせを承認すると、ステータスが「task_working」に更新される
        要件3.2: 承認時にupdated_atタイムスタンプが更新される
        """
        # 承認前のupdated_atを記録
        old_updated_at = received_inquiry.updated_at

        # 承認実行
        result = workflow_service.approve_inquiry(received_inquiry.id)

        # アサーション
        assert result.id == received_inquiry.id
        assert result.status == InquiryStatus.TASK_WORKING
        assert result.updated_at > old_updated_at

    def test_approve_inquiry_records_status_history(
        self,
        workflow_service: InquiryWorkflowService,
        received_inquiry: InquiryModel,
    ) -> None:
        """承認時にステータス変更履歴が記録されることを確認.

        要件3.12: ステータス変更履歴をメタデータに記録する
        """
        # 承認実行
        result = workflow_service.approve_inquiry(received_inquiry.id)

        # ステータス変更履歴の確認
        assert "status_history" in result.inquiry_metadata
        history = result.inquiry_metadata["status_history"]
        assert len(history) == 1
        assert history[0]["from_status"] == InquiryStatus.RECEIVED.value
        assert history[0]["to_status"] == InquiryStatus.TASK_WORKING.value
        assert "changed_at" in history[0]

    # 要件3.4-3.9: 却下機能のテスト
    def test_reject_inquiry_without_reason_success(
        self,
        workflow_service: InquiryWorkflowService,
        received_inquiry: InquiryModel,
    ) -> None:
        """却下理由なしでの却下フローの正常系テスト（received → rejected）.

        要件3.4: 問い合わせを却下すると、ステータスが「rejected」に更新される
        要件3.7: 却下時にupdated_atタイムスタンプが更新される
        """
        # 却下前のupdated_atを記録
        old_updated_at = received_inquiry.updated_at

        # 却下実行（却下理由なし）
        result = workflow_service.reject_inquiry(received_inquiry.id)

        # アサーション
        assert result.id == received_inquiry.id
        assert result.status == InquiryStatus.REJECTED
        assert result.updated_at > old_updated_at

    def test_reject_inquiry_with_reason_success(
        self,
        workflow_service: InquiryWorkflowService,
        received_inquiry: InquiryModel,
    ) -> None:
        """却下理由ありでの却下フローの正常系テスト.

        要件3.5: 却下時に却下理由の入力を許可する
        要件3.6: 却下理由を問い合わせのメタデータに保存する
        要件3.7: 却下日時を記録する
        """
        # 却下実行（却下理由あり）
        reason = "要件が不明確なため"
        result = workflow_service.reject_inquiry(received_inquiry.id, reason=reason)

        # アサーション
        assert result.status == InquiryStatus.REJECTED
        assert "rejection" in result.inquiry_metadata
        rejection_data = result.inquiry_metadata["rejection"]
        assert rejection_data["reason"] == reason
        assert "rejected_at" in rejection_data

        # rejected_atが有効なISO 8601形式の日時であることを確認
        rejected_at = datetime.fromisoformat(rejection_data["rejected_at"])
        assert rejected_at.tzinfo is not None  # タイムゾーン情報があることを確認

    def test_reject_inquiry_records_status_history(
        self,
        workflow_service: InquiryWorkflowService,
        received_inquiry: InquiryModel,
    ) -> None:
        """却下時にステータス変更履歴が記録されることを確認.

        要件3.12: ステータス変更履歴をメタデータに記録する
        """
        # 却下実行
        result = workflow_service.reject_inquiry(received_inquiry.id, reason="テスト")

        # ステータス変更履歴の確認
        assert "status_history" in result.inquiry_metadata
        history = result.inquiry_metadata["status_history"]
        assert len(history) == 1
        assert history[0]["from_status"] == InquiryStatus.RECEIVED.value
        assert history[0]["to_status"] == InquiryStatus.REJECTED.value
        assert "changed_at" in history[0]

    # 要件3.10-3.11: ステータス遷移制約のテスト
    @pytest.mark.parametrize(
        "status,expected_error",
        [
            (InquiryStatus.TASK_WORKING, "received"),
            (InquiryStatus.REJECTED, "received"),
            (InquiryStatus.COMPLETED, "received"),
        ],
    )
    def test_approve_from_invalid_status_fails(
        self,
        workflow_service: InquiryWorkflowService,
        repository: InquiryRepository,
        status: InquiryStatus,
        expected_error: str,
    ) -> None:
        """無効なステータスからの承認は失敗する.

        要件3.10: RECEIVEDステータスの問い合わせのみ承認・却下を許可する
        要件3.11: 承認済み・却下済みの問い合わせの再承認・再却下を禁止する
        """
        # 指定されたステータスの問い合わせを作成
        data = CreateInquiryData(
            user_id="test_user",
            content=f"ステータス: {status.value}",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=status,
        )
        inquiry = repository.create(data)

        # 承認を試みる
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            workflow_service.approve_inquiry(inquiry.id)

        assert expected_error in str(exc_info.value).lower()

    @pytest.mark.parametrize(
        "status,expected_error",
        [
            (InquiryStatus.TASK_WORKING, "received"),
            (InquiryStatus.REJECTED, "received"),
            (InquiryStatus.COMPLETED, "received"),
        ],
    )
    def test_reject_from_invalid_status_fails(
        self,
        workflow_service: InquiryWorkflowService,
        repository: InquiryRepository,
        status: InquiryStatus,
        expected_error: str,
    ) -> None:
        """無効なステータスからの却下は失敗する.

        要件3.10: RECEIVEDステータスの問い合わせのみ承認・却下を許可する
        要件3.11: 承認済み・却下済みの問い合わせの再承認・再却下を禁止する
        """
        # 指定されたステータスの問い合わせを作成
        data = CreateInquiryData(
            user_id="test_user",
            content=f"ステータス: {status.value}",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=status,
        )
        inquiry = repository.create(data)

        # 却下を試みる
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            workflow_service.reject_inquiry(inquiry.id, reason="テスト")

        assert expected_error in str(exc_info.value).lower()

    def test_approve_nonexistent_inquiry_fails(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """存在しない問い合わせの承認は失敗する."""
        nonexistent_id = 999999

        with pytest.raises(ValueError) as exc_info:
            workflow_service.approve_inquiry(nonexistent_id)

        assert "not found" in str(exc_info.value).lower()

    def test_reject_nonexistent_inquiry_fails(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """存在しない問い合わせの却下は失敗する."""
        nonexistent_id = 999999

        with pytest.raises(ValueError) as exc_info:
            workflow_service.reject_inquiry(nonexistent_id, reason="テスト")

        assert "not found" in str(exc_info.value).lower()

    # canTransitionToメソッドのテスト
    def test_can_transition_to_received_to_task_working(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """received → task_workingの遷移は許可される."""
        assert workflow_service.can_transition_to(
            InquiryStatus.RECEIVED,
            InquiryStatus.TASK_WORKING,
        )

    def test_can_transition_to_received_to_rejected(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """received → rejectedの遷移は許可される."""
        assert workflow_service.can_transition_to(
            InquiryStatus.RECEIVED,
            InquiryStatus.REJECTED,
        )

    def test_can_transition_to_task_working_to_task_working(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """task_working → task_workingの遷移は許可されない."""
        assert not workflow_service.can_transition_to(
            InquiryStatus.TASK_WORKING,
            InquiryStatus.TASK_WORKING,
        )

    def test_can_transition_to_rejected_to_task_working(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """rejected → task_workingの遷移は許可されない."""
        assert not workflow_service.can_transition_to(
            InquiryStatus.REJECTED,
            InquiryStatus.TASK_WORKING,
        )

    def test_can_transition_to_completed_to_rejected(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """completed → rejectedの遷移は許可されない."""
        assert not workflow_service.can_transition_to(
            InquiryStatus.COMPLETED,
            InquiryStatus.REJECTED,
        )

    def test_multiple_status_changes_accumulate_history(
        self,
        workflow_service: InquiryWorkflowService,
        repository: InquiryRepository,
    ) -> None:
        """複数回のステータス変更で履歴が蓄積されることを確認.

        要件3.12: ステータス変更履歴をメタデータに記録する
        """
        # RECEIVEDステータスの問い合わせを作成
        data = CreateInquiryData(
            user_id="test_user",
            content="複数回変更テスト",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry = repository.create(data)

        # 承認実行（received → task_working）
        result1 = workflow_service.approve_inquiry(inquiry.id)
        assert len(result1.inquiry_metadata["status_history"]) == 1

        # ステータスを手動でRECEIVEDに戻す（テスト用）。
        # このテストでは「同一問い合わせに対して複数回ステータス変更を行った場合に」
        # メタデータの履歴が正しく蓄積されるかのみを検証しているため、
        # ワークフローサービスの状態遷移ロジックはあえて経由せず、直接DBの状態を調整している。
        # （実運用の状態遷移の正当性は他のテストケースで検証する前提）
        result1.status = InquiryStatus.RECEIVED
        repository.session.commit()

        # 却下実行（received → rejected）
        result2 = workflow_service.reject_inquiry(inquiry.id, reason="テスト却下")

        # 履歴が2つになっていることを確認
        assert len(result2.inquiry_metadata["status_history"]) == 2
        assert (
            result2.inquiry_metadata["status_history"][0]["to_status"]
            == InquiryStatus.TASK_WORKING.value
        )
        assert (
            result2.inquiry_metadata["status_history"][1]["to_status"]
            == InquiryStatus.REJECTED.value
        )

    # 明確化要求機能のテスト
    def test_request_clarification_with_reason_success(
        self,
        workflow_service: InquiryWorkflowService,
        received_inquiry: InquiryModel,
    ) -> None:
        """明確化要求フローの正常系テスト（理由あり）.

        明確化要求理由ありで明確化要求できることを確認する。
        """
        # 明確化要求前のupdated_atを記録
        old_updated_at = received_inquiry.updated_at

        # 明確化要求実行（理由あり）
        reason = "追加情報が必要です"
        result = workflow_service.request_clarification(
            received_inquiry.id, reason=reason
        )

        # アサーション
        assert result.id == received_inquiry.id
        assert result.status == InquiryStatus.NEEDS_CLARIFICATION
        assert result.updated_at > old_updated_at
        assert "clarification_request" in result.inquiry_metadata
        clarification_data = result.inquiry_metadata["clarification_request"]
        assert clarification_data["reason"] == reason
        assert "requested_at" in clarification_data

        # requested_atが有効なISO 8601形式の日時であることを確認
        requested_at = datetime.fromisoformat(clarification_data["requested_at"])
        assert requested_at.tzinfo is not None  # タイムゾーン情報があることを確認

    def test_request_clarification_without_reason_success(
        self,
        workflow_service: InquiryWorkflowService,
        received_inquiry: InquiryModel,
    ) -> None:
        """明確化要求フローの正常系テスト（理由なし）.

        明確化要求理由なしで明確化要求できることを確認する。
        """
        # 明確化要求実行（理由なし）
        result = workflow_service.request_clarification(received_inquiry.id)

        # アサーション
        assert result.status == InquiryStatus.NEEDS_CLARIFICATION
        assert "clarification_request" in result.inquiry_metadata
        clarification_data = result.inquiry_metadata["clarification_request"]
        assert "reason" not in clarification_data  # 理由が保存されていないことを確認
        assert "requested_at" in clarification_data

    def test_request_clarification_records_status_history(
        self,
        workflow_service: InquiryWorkflowService,
        received_inquiry: InquiryModel,
    ) -> None:
        """明確化要求時にステータス変更履歴が記録されることを確認."""
        # 明確化要求実行
        result = workflow_service.request_clarification(
            received_inquiry.id, reason="テスト"
        )

        # ステータス変更履歴の確認
        assert "status_history" in result.inquiry_metadata
        history = result.inquiry_metadata["status_history"]
        assert len(history) == 1
        assert history[0]["from_status"] == InquiryStatus.RECEIVED.value
        assert history[0]["to_status"] == InquiryStatus.NEEDS_CLARIFICATION.value
        assert "changed_at" in history[0]

    def test_request_clarification_from_invalid_status_fails(
        self,
        workflow_service: InquiryWorkflowService,
        repository: InquiryRepository,
    ) -> None:
        """無効なステータスからの明確化要求は失敗する."""
        # TASK_WORKINGステータスの問い合わせを作成
        data = CreateInquiryData(
            user_id="test_user",
            content="タスク作業中の問い合わせ",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        inquiry = repository.create(data)

        # 明確化要求を試みる
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            workflow_service.request_clarification(inquiry.id, reason="テスト")

        assert "received" in str(exc_info.value).lower()

    def test_request_clarification_nonexistent_inquiry_fails(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """存在しない問い合わせの明確化要求は失敗する."""
        nonexistent_id = 999999

        with pytest.raises(ValueError) as exc_info:
            workflow_service.request_clarification(nonexistent_id, reason="テスト")

        assert "not found" in str(exc_info.value).lower()

    def test_complete_clarification_success(
        self,
        workflow_service: InquiryWorkflowService,
        repository: InquiryRepository,
    ) -> None:
        """明確化完了フローの正常系テスト.

        明確化完了でステータスがreceivedに戻ることを確認する。
        """
        # NEEDS_CLARIFICATIONステータスの問い合わせを作成
        data = CreateInquiryData(
            user_id="test_user",
            content="明確化が必要な問い合わせ",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.NEEDS_CLARIFICATION,
        )
        inquiry = repository.create(data)

        # メタデータに明確化要求情報を設定
        inquiry.inquiry_metadata = {
            "clarification_request": {
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "reason": "追加情報が必要です",
            }
        }
        repository.session.commit()

        # 明確化完了前のupdated_atを記録
        old_updated_at = inquiry.updated_at

        # 明確化完了実行
        result = workflow_service.complete_clarification(inquiry.id)

        # アサーション
        assert result.id == inquiry.id
        assert result.status == InquiryStatus.RECEIVED
        assert result.updated_at > old_updated_at
        assert "clarification_request" in result.inquiry_metadata
        assert "completed_at" in result.inquiry_metadata["clarification_request"]

        # completed_atが有効なISO 8601形式の日時であることを確認
        completed_at = datetime.fromisoformat(
            result.inquiry_metadata["clarification_request"]["completed_at"]
        )
        assert completed_at.tzinfo is not None

    def test_complete_clarification_records_status_history(
        self,
        workflow_service: InquiryWorkflowService,
        repository: InquiryRepository,
    ) -> None:
        """明確化完了時にステータス変更履歴が記録されることを確認."""
        # NEEDS_CLARIFICATIONステータスの問い合わせを作成
        data = CreateInquiryData(
            user_id="test_user",
            content="明確化が必要な問い合わせ",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.NEEDS_CLARIFICATION,
        )
        inquiry = repository.create(data)

        # 明確化完了実行
        result = workflow_service.complete_clarification(inquiry.id)

        # ステータス変更履歴の確認
        assert "status_history" in result.inquiry_metadata
        history = result.inquiry_metadata["status_history"]
        assert len(history) == 1
        assert history[0]["from_status"] == InquiryStatus.NEEDS_CLARIFICATION.value
        assert history[0]["to_status"] == InquiryStatus.RECEIVED.value
        assert "changed_at" in history[0]

    def test_complete_clarification_from_invalid_status_fails(
        self,
        workflow_service: InquiryWorkflowService,
        received_inquiry: InquiryModel,
    ) -> None:
        """無効なステータスからの明確化完了は失敗する."""
        # RECEIVEDステータスの問い合わせで明確化完了を試みる
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            workflow_service.complete_clarification(received_inquiry.id)

        assert "needs_clarification" in str(exc_info.value).lower()

    def test_complete_clarification_nonexistent_inquiry_fails(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """存在しない問い合わせの明確化完了は失敗する."""
        nonexistent_id = 999999

        with pytest.raises(ValueError) as exc_info:
            workflow_service.complete_clarification(nonexistent_id)

        assert "not found" in str(exc_info.value).lower()

    def test_can_transition_to_received_to_needs_clarification(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """received → needs_clarificationの遷移は許可される."""
        assert workflow_service.can_transition_to(
            InquiryStatus.RECEIVED,
            InquiryStatus.NEEDS_CLARIFICATION,
        )

    def test_can_transition_to_needs_clarification_to_received(
        self,
        workflow_service: InquiryWorkflowService,
    ) -> None:
        """needs_clarification → receivedの遷移は許可される."""
        assert workflow_service.can_transition_to(
            InquiryStatus.NEEDS_CLARIFICATION,
            InquiryStatus.RECEIVED,
        )
