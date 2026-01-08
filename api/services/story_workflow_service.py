"""StoryWorkflowService: ストーリーワークフロー管理サービス.

ストーリーのワークフロー制御（承認・却下・一括承認）とステータス遷移管理を提供する。
要件3.1-3.11をカバーする。
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm.attributes import flag_modified

from models.database.story import StoryModel
from models.enums.story_status import StoryStatus
from services.story_repository import StoryRepository


class InvalidStatusTransitionError(Exception):
    """無効なステータス遷移エラー.

    要件3.8に違反するステータス遷移を試みた場合にスローされる。
    """


class StoryWorkflowService:
    """ストーリーワークフローサービス.

    ストーリーの承認・却下、一括承認、ステータス遷移制御を提供する。
    """

    def __init__(self, repository: StoryRepository):
        """Initialize StoryWorkflowService.

        Args:
            repository: StoryRepositoryインスタンス
        """
        self.repository = repository

    def approve_story(self, story_id: int, approver: str) -> StoryModel:
        """ストーリーを承認する（要件3.1-3.3）.

        Args:
            story_id: ストーリーID
            approver: 承認者

        Returns:
            StoryModel: 承認されたストーリーエンティティ

        Raises:
            ValueError: ストーリーが存在しない場合
            InvalidStatusTransitionError: 無効なステータス遷移の場合

        Note:
            - ステータスを「approved」に更新する（要件3.2）
            - 承認日時と承認者をメタデータに記録する（要件3.3）
            - updated_atタイムスタンプを更新する
            - ステータス変更履歴をメタデータに記録する（要件3.9）
            - WAITING_REVIEWステータスのストーリーのみ承認可能（要件3.1, 3.8）
        """
        # ストーリーを取得
        story = self.repository.find_by_id(story_id)
        if story is None:
            raise ValueError(f"Story with id {story_id} not found")

        # ステータス遷移検証（要件3.1, 3.8）
        if not self.can_transition_to(story.status, StoryStatus.APPROVED):
            raise InvalidStatusTransitionError(
                f"Cannot approve story with status '{story.status.value}'. "
                "Only 'waiting_review' status stories can be approved."
            )

        # 現在のステータスを記録（履歴用）
        old_status = story.status

        # 承認情報をメタデータに保存（要件3.3）
        approval_data = {
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approver": approver,
        }

        # メタデータを更新
        if story.story_metadata is None:
            story.story_metadata = {}
        story.story_metadata["approval"] = approval_data

        # ステータス変更履歴を記録（要件3.9）
        self._record_status_change(
            story=story,
            from_status=old_status,
            to_status=StoryStatus.APPROVED,
        )

        # ステータスを更新（要件3.2）
        story.status = StoryStatus.APPROVED
        story.updated_at = datetime.now(timezone.utc)

        # 変更をマーク（SQLAlchemyがJSON変更を検知するため）
        flag_modified(story, "story_metadata")

        # 変更を保存
        self.repository.session.commit()
        self.repository.session.refresh(story)

        return story

    def reject_story(
        self,
        story_id: int,
        rejector: str,
        reason: Optional[str] = None,
    ) -> StoryModel:
        """ストーリーを却下する（要件3.4-3.7）.

        Args:
            story_id: ストーリーID
            rejector: 却下者
            reason: 却下理由（オプショナル、要件3.5）

        Returns:
            StoryModel: 却下されたストーリーエンティティ

        Raises:
            ValueError: ストーリーが存在しない場合
            InvalidStatusTransitionError: 無効なステータス遷移の場合

        Note:
            - ステータスを「rejected」に更新する（要件3.6）
            - 却下理由をメタデータに保存する（要件3.5, 3.7）
            - 却下日時と却下者を記録する（要件3.7）
            - updated_atタイムスタンプを更新する
            - ステータス変更履歴をメタデータに記録する（要件3.9）
            - WAITING_REVIEWステータスのストーリーのみ却下可能（要件3.4, 3.8）
        """
        # ストーリーを取得
        story = self.repository.find_by_id(story_id)
        if story is None:
            raise ValueError(f"Story with id {story_id} not found")

        # ステータス遷移検証（要件3.4, 3.8）
        if not self.can_transition_to(story.status, StoryStatus.REJECTED):
            raise InvalidStatusTransitionError(
                f"Cannot reject story with status '{story.status.value}'. "
                "Only 'waiting_review' status stories can be rejected."
            )

        # 現在のステータスを記録（履歴用）
        old_status = story.status

        # 却下情報をメタデータに保存（要件3.5, 3.7）
        rejection_data = {
            "rejected_at": datetime.now(timezone.utc).isoformat(),
            "rejector": rejector,
        }
        if reason is not None:
            rejection_data["reason"] = reason

        # メタデータを更新
        if story.story_metadata is None:
            story.story_metadata = {}
        story.story_metadata["rejection"] = rejection_data

        # ステータス変更履歴を記録（要件3.9）
        self._record_status_change(
            story=story,
            from_status=old_status,
            to_status=StoryStatus.REJECTED,
        )

        # ステータスを更新（要件3.6）
        story.status = StoryStatus.REJECTED
        story.updated_at = datetime.now(timezone.utc)

        # 変更をマーク（SQLAlchemyがJSON変更を検知するため）
        flag_modified(story, "story_metadata")

        # 変更を保存
        self.repository.session.commit()
        self.repository.session.refresh(story)

        return story

    def batch_approve(
        self,
        story_ids: list[int],
        approver: str,
    ) -> list[tuple[int, bool, Optional[str]]]:
        """複数ストーリーを一括承認する（要件3.10-3.11）.

        各ストーリーのステータスを個別に検証し、成功/失敗を記録する。

        Args:
            story_ids: ストーリーIDのリスト
            approver: 承認者

        Returns:
            list[tuple[int, bool, Optional[str]]]:
                (story_id, success, error_message)のリスト
                - story_id: ストーリーID
                - success: 承認成功時はTrue、失敗時はFalse
                - error_message: 失敗時のエラーメッセージ、成功時はNone

        Note:
            - 各ストーリーを個別に承認試行する（要件3.11）
            - 一部のストーリーが失敗しても他のストーリーは承認される
            - 存在しないストーリーや無効なステータスのストーリーはスキップされる
        """
        results: list[tuple[int, bool, Optional[str]]] = []

        for story_id in story_ids:
            try:
                # 個別に承認試行
                self.approve_story(story_id, approver)
                results.append((story_id, True, None))
            except ValueError as e:
                # ストーリーが存在しない場合
                results.append((story_id, False, str(e)))
            except InvalidStatusTransitionError as e:
                # 無効なステータス遷移の場合
                results.append((story_id, False, str(e)))

        return results

    def can_transition_to(
        self,
        current_status: StoryStatus,
        new_status: StoryStatus,
    ) -> bool:
        """ステータス遷移が可能かを検証する（要件3.8）.

        Args:
            current_status: 現在のステータス
            new_status: 遷移先のステータス

        Returns:
            bool: 遷移可能な場合はTrue、不可能な場合はFalse

        Note:
            許可される遷移:
            - waiting_review → approved (承認)
            - waiting_review → rejected (却下)

            禁止される遷移:
            - approved → * (承認済みは変更不可)
            - rejected → * (却下済みは変更不可)
            - waiting_review → waiting_review (同じステータスへの遷移)
        """
        # 承認フロー（waiting_review → approved）
        if (
            current_status == StoryStatus.WAITING_REVIEW
            and new_status == StoryStatus.APPROVED
        ):
            return True

        # 却下フロー（waiting_review → rejected）
        if (
            current_status == StoryStatus.WAITING_REVIEW
            and new_status == StoryStatus.REJECTED
        ):
            return True

        # その他の遷移は禁止
        return False

    def _record_status_change(
        self,
        story: StoryModel,
        from_status: StoryStatus,
        to_status: StoryStatus,
    ) -> None:
        """ステータス変更履歴を記録する（要件3.9）.

        Args:
            story: ストーリーエンティティ
            from_status: 変更前のステータス
            to_status: 変更後のステータス

        Note:
            story.story_metadataのstatus_history配列に変更履歴を追加する。
        """
        # メタデータの初期化
        if story.story_metadata is None:
            story.story_metadata = {}

        if "status_history" not in story.story_metadata:
            story.story_metadata["status_history"] = []

        # 変更履歴を追加
        history_entry = {
            "from_status": from_status.value,
            "to_status": to_status.value,
            "changed_at": datetime.now(timezone.utc).isoformat(),
        }
        story.story_metadata["status_history"].append(history_entry)

        # 変更をマーク（SQLAlchemyがJSON変更を検知するため）
        flag_modified(story, "story_metadata")
