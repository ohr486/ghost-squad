"""プロンプトシーダー.

アプリ起動時にデフォルトプロンプトをDBに投入する。
冪等な処理で、既存プロンプトは上書きしない。

Requirements: 4.1, 4.2
"""
import logging
from dataclasses import dataclass

from services.prompt_defaults import DEFAULT_PROMPTS
from services.prompt_repository import CreatePromptData, PromptRepository

logger = logging.getLogger(__name__)


@dataclass
class SeedResult:
    """シード処理結果.

    Attributes:
        created: 新規作成されたプロンプト数
        skipped: 既存のためスキップされたプロンプト数
    """

    created: int
    skipped: int

    @property
    def total(self) -> int:
        """処理された総プロンプト数."""
        return self.created + self.skipped


class PromptSeeder:
    """デフォルトプロンプトのシーダー.

    アプリ起動時（lifespan処理）に呼び出され、
    デフォルトプロンプトをDBに冪等に投入する。
    既存プロンプトは上書きしない（INSERT IF NOT EXISTS）。
    """

    def __init__(self, repository: PromptRepository) -> None:
        """Initialize PromptSeeder.

        Args:
            repository: プロンプトリポジトリ
        """
        self.repository = repository

    def seed(self) -> SeedResult:
        """デフォルトプロンプトをDBに投入する.

        冪等な処理: 既存プロンプトは上書きしない。

        Returns:
            SeedResult: 作成数・スキップ数
        """
        created = 0
        skipped = 0

        for prompt_def in DEFAULT_PROMPTS:
            key = prompt_def["key"]

            # 既存チェック（冪等性）
            existing = self.repository.find_by_key(key)
            if existing is not None:
                logger.debug("プロンプト '%s' は既に存在します。スキップします。", key)
                skipped += 1
                continue

            # 新規作成
            data = CreatePromptData(
                key=key,
                name=prompt_def["name"],
                description=prompt_def.get("description"),
                category=prompt_def["category"],
                content=prompt_def["content"],
                default_content=prompt_def["content"],
                variables=prompt_def["variables"],
            )
            self.repository.create(data)
            logger.info("デフォルトプロンプトを作成しました: '%s'", key)
            created += 1

        logger.info(
            "プロンプトシード完了: 作成=%d, スキップ=%d",
            created,
            skipped,
        )
        return SeedResult(created=created, skipped=skipped)
