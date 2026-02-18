"""デフォルトプロンプト定義.

システム全体で使用されるAIプロンプトのデフォルト値を定義する。
これらのプロンプトはアプリ起動時にシード処理でDBに投入される。

現在ハードコードされている以下のプロンプトを移行:
- StoryGenerationService: ストーリー生成システム/ユーザープロンプト
- OpenAIProvider/AnthropicProvider: ANALYSIS_SYSTEM_PROMPT

Requirements: 4.1, 4.2
"""
from typing import Any, Dict, List

from models.enums.prompt_category import PromptCategory

# ストーリー生成システムプロンプト
# 元: StoryGenerationService._call_openai_api() の system メッセージ
_STORY_GENERATION_SYSTEM_CONTENT = (
    "あなたはアジャイル開発の専門家です。"
    "問い合わせから適切なユーザーストーリーを生成してください。"
)

# ストーリー生成ユーザープロンプト
# 元: StoryGenerationService._call_openai_api() の user メッセージ
_STORY_GENERATION_USER_CONTENT = """\
以下の問い合わせから、アジャイル開発で使用するユーザーストーリーを生成してください。

問い合わせ内容：
{inquiry_content}

出力形式（JSON）：
{{
    "title": "簡潔なタイトル（500文字以内）",
    "description": "詳細な説明",
    "priority": "low/medium/high/urgent のいずれか",
    "estimated_effort": 推定工数（数値、オプショナル）
}}

JSON形式のみで応答してください（説明文は不要）。"""

# インポート解析システムプロンプト
# 元: OpenAIProvider/AnthropicProvider の ANALYSIS_SYSTEM_PROMPT
_IMPORT_ANALYSIS_SYSTEM_CONTENT = """\
あなたは問い合わせ解析の専門家です。
与えられたメールやメッセージを分析し、以下の情報をJSON形式で出力してください。

出力形式（必ずこの形式で出力してください）:
{{
    "title": "問い合わせタイトル（簡潔に30文字以内）",
    "content": "構造化された問い合わせ内容（箇条書きで整理）",
    "priority": "優先度（low/medium/high/urgentのいずれか）",
    "category": "カテゴリ（development/testing/documentation/research/maintenance/custom）",
    "confidence_score": 0.0〜1.0の数値（解析の確信度）
}}

優先度の判断基準:
- urgent: 緊急、至急、障害、エラー、ダウン等の緊急性を示す語がある
- high: 重要、早急、優先等の語がある、または期限が迫っている
- medium: 通常の問い合わせ、質問、依頼
- low: 参考、確認、将来的な検討事項

カテゴリの判断基準:
- development: 新機能開発、機能追加、実装依頼
- testing: テスト、検証、品質確認
- documentation: ドキュメント作成、マニュアル
- research: 調査、技術検討、PoC
- maintenance: 保守、バグ修正、障害対応
- custom: 上記に該当しない場合

信頼度スコアの基準:
- 0.9以上: 明確な内容で高い確信度
- 0.7〜0.9: 標準的な問い合わせ
- 0.5〜0.7: 曖昧な部分がある
- 0.5未満: 内容が不明確、追加情報が必要

必ず有効なJSONのみを出力してください。説明や追加のテキストは含めないでください。"""

# デフォルトプロンプト定義リスト
# 各エントリにはPromptSeederが使用するフィールドが含まれる
DEFAULT_PROMPTS: List[Dict[str, Any]] = [
    {
        "key": "story_generation_system",
        "name": "ストーリー生成システムプロンプト",
        "description": "ストーリー生成時にAIに送信するシステムプロンプト。"
        "AIの役割と応答方針を定義する。",
        "category": PromptCategory.STORY_GENERATION,
        "content": _STORY_GENERATION_SYSTEM_CONTENT,
        "variables": [],
    },
    {
        "key": "story_generation_user",
        "name": "ストーリー生成ユーザープロンプト",
        "description": "ストーリー生成時にAIに送信するユーザープロンプトテンプレート。"
        "問い合わせ内容をプレースホルダーで埋め込む。",
        "category": PromptCategory.STORY_GENERATION,
        "content": _STORY_GENERATION_USER_CONTENT,
        "variables": ["inquiry_content"],
    },
    {
        "key": "import_analysis_system",
        "name": "インポート解析システムプロンプト",
        "description": "インポートされたメールやメッセージの解析時にAIに送信する"
        "システムプロンプト。解析形式と判断基準を定義する。",
        "category": PromptCategory.IMPORT_ANALYSIS,
        "content": _IMPORT_ANALYSIS_SYSTEM_CONTENT,
        "variables": [],
    },
]
