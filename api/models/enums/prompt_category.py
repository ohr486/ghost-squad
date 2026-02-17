"""プロンプトカテゴリ列挙型."""
from enum import Enum


class PromptCategory(str, Enum):
    """プロンプトカテゴリ."""

    STORY_GENERATION = "story_generation"  # ストーリー生成
    IMPORT_ANALYSIS = "import_analysis"  # インポート解析
    GENERAL = "general"  # 汎用
