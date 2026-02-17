"""プロンプトカテゴリ列挙型のテスト."""
from models.enums.prompt_category import PromptCategory


class TestPromptCategory:
    """PromptCategory列挙型のテスト."""

    def test_prompt_category_values(self):
        """PromptCategoryの全ての値が正しく定義されていることを確認."""
        assert PromptCategory.STORY_GENERATION.value == "story_generation"
        assert PromptCategory.IMPORT_ANALYSIS.value == "import_analysis"
        assert PromptCategory.GENERAL.value == "general"

    def test_prompt_category_all_members(self):
        """PromptCategory列挙型が期待される全メンバーを持つことを確認."""
        expected_members = {"STORY_GENERATION", "IMPORT_ANALYSIS", "GENERAL"}
        actual_members = {member.name for member in PromptCategory}
        assert actual_members == expected_members

    def test_prompt_category_is_string_enum(self):
        """PromptCategoryがstrのサブクラスであることを確認."""
        assert isinstance(PromptCategory.STORY_GENERATION.value, str)

    def test_prompt_category_member_count(self):
        """PromptCategoryが3つのメンバーを持つことを確認."""
        assert len(PromptCategory) == 3
