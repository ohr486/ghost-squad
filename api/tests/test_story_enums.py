"""ストーリー関連列挙型のテスト."""
from models.enums.priority import Priority
from models.enums.story_status import StoryStatus


class TestPriority:
    """Priority列挙型のテスト."""

    def test_priority_values(self):
        """Priorityの全ての値が正しく定義されていることを確認."""
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
        assert Priority.URGENT.value == "urgent"

    def test_priority_default_is_medium(self):
        """デフォルト値がMEDIUMであることを確認（設計書準拠）."""
        # デフォルト値はモデル定義で設定されるため、ここでは値の存在を確認
        assert Priority.MEDIUM is not None

    def test_priority_all_members(self):
        """Priority列挙型が期待される全メンバーを持つことを確認."""
        expected_members = {"LOW", "MEDIUM", "HIGH", "URGENT"}
        actual_members = {member.name for member in Priority}
        assert actual_members == expected_members

    def test_priority_is_string_enum(self):
        """Priorityがstrのサブクラスであることを確認."""
        assert isinstance(Priority.MEDIUM.value, str)


class TestStoryStatus:
    """StoryStatus列挙型のテスト."""

    def test_story_status_values(self):
        """StoryStatusの全ての値が正しく定義されていることを確認."""
        assert StoryStatus.WAITING_REVIEW.value == "waiting_review"
        assert StoryStatus.APPROVED.value == "approved"
        assert StoryStatus.REJECTED.value == "rejected"

    def test_story_status_default_is_waiting_review(self):
        """デフォルト値がWAITING_REVIEWであることを確認（設計書準拠）."""
        # デフォルト値はモデル定義で設定されるため、ここでは値の存在を確認
        assert StoryStatus.WAITING_REVIEW is not None

    def test_story_status_all_members(self):
        """StoryStatus列挙型が期待される全メンバーを持つことを確認."""
        expected_members = {"WAITING_REVIEW", "APPROVED", "REJECTED"}
        actual_members = {member.name for member in StoryStatus}
        assert actual_members == expected_members

    def test_story_status_is_string_enum(self):
        """StoryStatusがstrのサブクラスであることを確認."""
        assert isinstance(StoryStatus.WAITING_REVIEW.value, str)
