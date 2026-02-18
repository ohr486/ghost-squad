"""プロンプトキャッシュサービス.

タスク 3.2: TTL付きインメモリキャッシュ機能を実装する
- キーベースのインメモリキャッシュをTTL（60秒）付きで実装する
- DB障害時フォールバック用のget_fallbackメソッドを実装する（TTL超過エントリも返却）
- キャッシュの無効化（単一キー、全体）機能を実装する
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class PromptCacheEntry:
    """キャッシュエントリ.

    Attributes:
        key: プロンプトキー
        content: プロンプト本文
        default_content: デフォルトプロンプト本文
        variables: プレースホルダー変数リスト
    """

    key: str
    content: str
    default_content: str
    variables: List[str] = field(default_factory=list)


class PromptCache:
    """プロンプトのインメモリキャッシュ.

    キーベースのインメモリキャッシュをTTL付きで提供する。
    DB障害時にはTTL超過エントリもフォールバックとして返却する。
    """

    def __init__(self, ttl_seconds: int = 60) -> None:
        """TTL付きインメモリキャッシュを初期化する.

        Args:
            ttl_seconds: キャッシュの有効期間（秒）。デフォルト60秒。
        """
        self.ttl_seconds = ttl_seconds
        # {key: (entry, timestamp)}
        self._cache: Dict[str, Tuple[PromptCacheEntry, float]] = {}

    def get(self, key: str) -> Optional[PromptCacheEntry]:
        """キャッシュからプロンプトを取得する（TTL超過時はNone）.

        Args:
            key: プロンプトキー

        Returns:
            TTL内のキャッシュエントリ、またはNone
        """
        cached = self._cache.get(key)
        if cached is None:
            return None

        entry, timestamp = cached
        if time.monotonic() - timestamp > self.ttl_seconds:
            return None

        return entry

    def get_fallback(self, key: str) -> Optional[PromptCacheEntry]:
        """DB障害時フォールバック用。TTL超過エントリも返却する.

        Args:
            key: プロンプトキー

        Returns:
            キャッシュエントリ（TTL超過含む）、またはNone
        """
        cached = self._cache.get(key)
        if cached is None:
            return None

        entry, _ = cached
        return entry

    def set(self, key: str, entry: PromptCacheEntry) -> None:
        """キャッシュにプロンプトを設定する（タイムスタンプ記録）.

        Args:
            key: プロンプトキー
            entry: キャッシュエントリ
        """
        self._cache[key] = (entry, time.monotonic())

    def invalidate(self, key: str) -> None:
        """指定キーのキャッシュを無効化する.

        Args:
            key: プロンプトキー
        """
        self._cache.pop(key, None)

    def invalidate_all(self) -> None:
        """全キャッシュを無効化する."""
        self._cache.clear()
