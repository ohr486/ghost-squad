"""InquiryWorkflowService: 問い合わせワークフロー管理サービス.

問い合わせのワークフロー制御（承認・却下）とステータス遷移管理を提供する。
要件3.1-3.12をカバーする。
"""
from datetime import datetime, timezone
from typing import Optional

from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus
from services.inquiry_repository import InquiryRepository


class InvalidStateTransitionError(Exception):
    """無効なステータス遷移エラー.

    要件3.10-3.11に違反するステータス遷移を試みた場合にスローされる。
    """


class InquiryWorkflowService:
    """問い合わせワークフローサービス.

    問い合わせの承認・却下、ステータス遷移制御を提供する。
    """

    def __init__(self, repository: InquiryRepository):
        """Initialize InquiryWorkflowService.

        Args:
            repository: InquiryRepositoryインスタンス
        """
        self.repository = repository

    def approve_inquiry(self, inquiry_id: int) -> InquiryModel:
        """問い合わせを承認する（要件3.1-3.3）.

        Args:
            inquiry_id: 問い合わせID

        Returns:
            InquiryModel: 承認された問い合わせエンティティ

        Raises:
            ValueError: 問い合わせが存在しない場合
            InvalidStateTransitionError: 無効なステータス遷移の場合

        Note:
            - ステータスを「task_working」に更新する（要件3.1）
            - updated_atタイムスタンプを更新する（要件3.2）
            - ステータス変更履歴をメタデータに記録する（要件3.12）
            - RECEIVEDステータスの問い合わせのみ承認可能（要件3.10）
        """
        # 問い合わせを取得
        inquiry = self.repository.find_by_id(inquiry_id)
        if inquiry is None:
            raise ValueError(f"Inquiry with id {inquiry_id} not found")

        # ステータス遷移検証（要件3.10-3.11）
        if not self.can_transition_to(inquiry.status, InquiryStatus.TASK_WORKING):
            raise InvalidStateTransitionError(
                f"Cannot approve inquiry with status '{inquiry.status.value}'. "
                "Only 'received' status inquiries can be approved."
            )

        # 現在のステータスを記録（履歴用）
        old_status = inquiry.status

        # ステータス変更履歴を記録（要件3.12）
        self._record_status_change(
            inquiry=inquiry,
            from_status=old_status,
            to_status=InquiryStatus.TASK_WORKING,
        )

        # ステータスを更新（要件3.1）
        # update_statusメソッドはupdated_atを自動更新する（要件3.2）
        return self.repository.update_status(inquiry_id, InquiryStatus.TASK_WORKING)

    def reject_inquiry(
        self,
        inquiry_id: int,
        reason: Optional[str] = None,
    ) -> InquiryModel:
        """問い合わせを却下する（要件3.4-3.9）.

        Args:
            inquiry_id: 問い合わせID
            reason: 却下理由（オプショナル）

        Returns:
            InquiryModel: 却下された問い合わせエンティティ

        Raises:
            ValueError: 問い合わせが存在しない場合
            InvalidStateTransitionError: 無効なステータス遷移の場合

        Note:
            - ステータスを「rejected」に更新する（要件3.4）
            - 却下理由の入力を許可する（要件3.5）
            - 却下理由をメタデータに保存する（要件3.6）
            - updated_atタイムスタンプと却下日時を記録する（要件3.7）
            - ステータス変更履歴をメタデータに記録する（要件3.12）
            - RECEIVEDステータスの問い合わせのみ却下可能（要件3.10）
        """
        # 問い合わせを取得
        inquiry = self.repository.find_by_id(inquiry_id)
        if inquiry is None:
            raise ValueError(f"Inquiry with id {inquiry_id} not found")

        # ステータス遷移検証（要件3.10-3.11）
        if not self.can_transition_to(inquiry.status, InquiryStatus.REJECTED):
            raise InvalidStateTransitionError(
                f"Cannot reject inquiry with status '{inquiry.status.value}'. "
                "Only 'received' status inquiries can be rejected."
            )

        # 現在のステータスを記録（履歴用）
        old_status = inquiry.status

        # 却下情報をメタデータに保存（要件3.6-3.7）
        rejection_data = {
            "rejected_at": datetime.now(timezone.utc).isoformat(),
        }
        if reason is not None:
            rejection_data["reason"] = reason

        # メタデータを更新
        if inquiry.inquiry_metadata is None:
            inquiry.inquiry_metadata = {}
        inquiry.inquiry_metadata["rejection"] = rejection_data

        # ステータス変更履歴を記録（要件3.12）
        self._record_status_change(
            inquiry=inquiry,
            from_status=old_status,
            to_status=InquiryStatus.REJECTED,
        )

        # ステータスを更新（要件3.4）
        # update_statusメソッドはupdated_atを自動更新し、一度のトランザクションで全変更をコミットする（要件3.7）
        return self.repository.update_status(inquiry_id, InquiryStatus.REJECTED)

    def can_transition_to(
        self,
        current_status: InquiryStatus,
        new_status: InquiryStatus,
    ) -> bool:
        """ステータス遷移が可能かを検証する（要件3.10-3.12）.

        Args:
            current_status: 現在のステータス
            new_status: 遷移先のステータス

        Returns:
            bool: 遷移可能な場合はTrue、不可能な場合はFalse

        Note:
            許可される遷移:
            - received → task_working (承認)
            - received → rejected (却下)
            - received → processing (AI処理開始、story specで実装)
            - processing → task_working (AI処理成功、story specで実装)
            - processing → failed (AI処理失敗、story specで実装)
            - task_working → completed (タスク完了、story specで実装)

            要件3.10-3.11:
            - RECEIVEDステータスの問い合わせのみ承認・却下を許可する
            - 承認済み・却下済みの問い合わせの再承認・再却下を禁止する
        """
        # 承認フロー（received → task_working）
        if (
            current_status == InquiryStatus.RECEIVED
            and new_status == InquiryStatus.TASK_WORKING
        ):
            return True

        # 却下フロー（received → rejected）
        if (
            current_status == InquiryStatus.RECEIVED
            and new_status == InquiryStatus.REJECTED
        ):
            return True

        # 将来実装: AI処理開始フロー（received → processing）
        if (
            current_status == InquiryStatus.RECEIVED
            and new_status == InquiryStatus.PROCESSING
        ):
            return True

        # 将来実装: AI処理成功フロー（processing → task_working）
        if (
            current_status == InquiryStatus.PROCESSING
            and new_status == InquiryStatus.TASK_WORKING
        ):
            return True

        # 将来実装: AI処理失敗フロー（processing → failed）
        if (
            current_status == InquiryStatus.PROCESSING
            and new_status == InquiryStatus.FAILED
        ):
            return True

        # 将来実装: タスク完了フロー（task_working → completed）
        if (
            current_status == InquiryStatus.TASK_WORKING
            and new_status == InquiryStatus.COMPLETED
        ):
            return True

        # その他の遷移は禁止
        return False

    def _record_status_change(
        self,
        inquiry: InquiryModel,
        from_status: InquiryStatus,
        to_status: InquiryStatus,
    ) -> None:
        """ステータス変更履歴を記録する（要件3.12）.

        Args:
            inquiry: 問い合わせエンティティ
            from_status: 変更前のステータス
            to_status: 変更後のステータス

        Note:
            inquiry.inquiry_metadataのstatus_history配列に変更履歴を追加する。
        """
        # メタデータの初期化
        if inquiry.inquiry_metadata is None:
            inquiry.inquiry_metadata = {}

        if "status_history" not in inquiry.inquiry_metadata:
            inquiry.inquiry_metadata["status_history"] = []

        # 変更履歴を追加
        history_entry = {
            "from_status": from_status.value,
            "to_status": to_status.value,
            "changed_at": datetime.now(timezone.utc).isoformat(),
        }
        inquiry.inquiry_metadata["status_history"].append(history_entry)

        # 変更をマーク（SQLAlchemyがJSON変更を検知するため）
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(inquiry, "inquiry_metadata")
