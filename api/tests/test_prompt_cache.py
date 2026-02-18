"""Test PromptCache.

タスク 3.2: TTL付きインメモリキャッシュ機能を実装する
- キーベースのインメモリキャッシュをTTL（60秒）付きで実装する
- DB障害時フォールバック用のget_fallbackメソッドを実装する
- キャッシュの無効化（単一キー、全体）機能を実装する
- TTL動作、キャッシュヒット/ミス、フォールバック、無効化のユニットテストを作成する
"""

import time

from services.prompt_cache import PromptCache, PromptCacheEntry


class TestPromptCacheEntry:
    """PromptCacheEntryのテスト."""

    def test_cache_entry_structure(self):
        """PromptCacheEntryが正しい構造を持つ."""
        entry = PromptCacheEntry(
            id=1,
            key="story_generation_system",
            content="プロンプト本文",
            default_content="デフォルト本文",
            variables=["inquiry_content"],
        )

        assert entry.key == "story_generation_system"
        assert entry.content == "プロンプト本文"
        assert entry.default_content == "デフォルト本文"
        assert entry.variables == ["inquiry_content"]

    def test_cache_entry_optional_fields(self):
        """PromptCacheEntryのオプショナルフィールド."""
        entry = PromptCacheEntry(
            id=1,
            key="test",
            content="本文",
            default_content="デフォルト",
            variables=[],
        )

        assert entry.variables == []


class TestPromptCacheInit:
    """PromptCacheの初期化テスト."""

    def test_default_ttl(self):
        """デフォルトTTLが60秒であること."""
        cache = PromptCache()

        assert cache.ttl_seconds == 60

    def test_custom_ttl(self):
        """カスタムTTLが設定できること."""
        cache = PromptCache(ttl_seconds=120)

        assert cache.ttl_seconds == 120


class TestPromptCacheSetAndGet:
    """set/getのテスト."""

    def test_set_and_get(self):
        """キャッシュに設定したエントリを取得できる."""
        cache = PromptCache(ttl_seconds=60)
        entry = PromptCacheEntry(
            id=1,
            key="story_generation_system",
            content="プロンプト本文",
            default_content="デフォルト本文",
            variables=["inquiry_content"],
        )

        cache.set("story_generation_system", entry)
        result = cache.get("story_generation_system")

        assert result is not None
        assert result.key == "story_generation_system"
        assert result.content == "プロンプト本文"

    def test_get_nonexistent_key(self):
        """存在しないキーを取得するとNoneを返す."""
        cache = PromptCache(ttl_seconds=60)

        result = cache.get("nonexistent_key")

        assert result is None

    def test_set_overwrite(self):
        """同じキーに再設定すると上書きされる."""
        cache = PromptCache(ttl_seconds=60)
        entry1 = PromptCacheEntry(
            id=1,
            key="test_key",
            content="本文1",
            default_content="デフォルト",
            variables=[],
        )
        entry2 = PromptCacheEntry(
            id=1,
            key="test_key",
            content="本文2",
            default_content="デフォルト",
            variables=[],
        )

        cache.set("test_key", entry1)
        cache.set("test_key", entry2)
        result = cache.get("test_key")

        assert result is not None
        assert result.content == "本文2"

    def test_set_multiple_keys(self):
        """複数のキーを設定・取得できる."""
        cache = PromptCache(ttl_seconds=60)
        entry1 = PromptCacheEntry(
            id=1,
            key="key1",
            content="本文1",
            default_content="デフォルト1",
            variables=[],
        )
        entry2 = PromptCacheEntry(
            id=1,
            key="key2",
            content="本文2",
            default_content="デフォルト2",
            variables=[],
        )

        cache.set("key1", entry1)
        cache.set("key2", entry2)

        assert cache.get("key1") is not None
        assert cache.get("key1").content == "本文1"
        assert cache.get("key2") is not None
        assert cache.get("key2").content == "本文2"


class TestPromptCacheTTL:
    """TTLのテスト."""

    def test_get_within_ttl(self):
        """TTL内のエントリは取得できる."""
        cache = PromptCache(ttl_seconds=60)
        entry = PromptCacheEntry(
            id=1,
            key="test",
            content="本文",
            default_content="デフォルト",
            variables=[],
        )

        cache.set("test", entry)
        result = cache.get("test")

        assert result is not None

    def test_get_expired_ttl(self):
        """TTL超過のエントリはNoneを返す."""
        cache = PromptCache(ttl_seconds=0)  # 即座に期限切れ
        entry = PromptCacheEntry(
            id=1,
            key="test",
            content="本文",
            default_content="デフォルト",
            variables=[],
        )

        cache.set("test", entry)
        time.sleep(0.01)  # 確実にTTL超過させる
        result = cache.get("test")

        assert result is None

    def test_get_short_ttl_expires(self):
        """短いTTL（1秒）が正しく動作する."""
        cache = PromptCache(ttl_seconds=1)
        entry = PromptCacheEntry(
            id=1,
            key="test",
            content="本文",
            default_content="デフォルト",
            variables=[],
        )

        cache.set("test", entry)

        # TTL内
        result = cache.get("test")
        assert result is not None

        # TTL超過
        time.sleep(1.1)
        result = cache.get("test")
        assert result is None


class TestPromptCacheGetFallback:
    """get_fallbackのテスト（DB障害時フォールバック用）."""

    def test_get_fallback_within_ttl(self):
        """TTL内のエントリをフォールバックで取得できる."""
        cache = PromptCache(ttl_seconds=60)
        entry = PromptCacheEntry(
            id=1,
            key="test",
            content="本文",
            default_content="デフォルト",
            variables=[],
        )

        cache.set("test", entry)
        result = cache.get_fallback("test")

        assert result is not None
        assert result.content == "本文"

    def test_get_fallback_expired_ttl(self):
        """TTL超過のエントリもフォールバックで取得できる."""
        cache = PromptCache(ttl_seconds=0)  # 即座に期限切れ
        entry = PromptCacheEntry(
            id=1,
            key="test",
            content="本文",
            default_content="デフォルト",
            variables=[],
        )

        cache.set("test", entry)
        time.sleep(0.01)

        # 通常のgetはNone
        assert cache.get("test") is None

        # フォールバックは取得できる
        result = cache.get_fallback("test")
        assert result is not None
        assert result.content == "本文"

    def test_get_fallback_nonexistent_key(self):
        """存在しないキーのフォールバックはNoneを返す."""
        cache = PromptCache(ttl_seconds=60)

        result = cache.get_fallback("nonexistent")

        assert result is None


class TestPromptCacheInvalidate:
    """invalidateのテスト."""

    def test_invalidate_existing_key(self):
        """既存のキーを無効化できる."""
        cache = PromptCache(ttl_seconds=60)
        entry = PromptCacheEntry(
            id=1,
            key="test",
            content="本文",
            default_content="デフォルト",
            variables=[],
        )

        cache.set("test", entry)
        assert cache.get("test") is not None

        cache.invalidate("test")
        assert cache.get("test") is None

    def test_invalidate_nonexistent_key(self):
        """存在しないキーの無効化はエラーにならない."""
        cache = PromptCache(ttl_seconds=60)

        # エラーが発生しないことを確認
        cache.invalidate("nonexistent")

    def test_invalidate_does_not_affect_others(self):
        """特定キーの無効化は他のキーに影響しない."""
        cache = PromptCache(ttl_seconds=60)
        entry1 = PromptCacheEntry(
            id=1,
            key="key1",
            content="本文1",
            default_content="デフォルト1",
            variables=[],
        )
        entry2 = PromptCacheEntry(
            id=1,
            key="key2",
            content="本文2",
            default_content="デフォルト2",
            variables=[],
        )

        cache.set("key1", entry1)
        cache.set("key2", entry2)

        cache.invalidate("key1")

        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key2").content == "本文2"

    def test_invalidate_removes_from_fallback(self):
        """無効化したキーはフォールバックでも取得できない."""
        cache = PromptCache(ttl_seconds=60)
        entry = PromptCacheEntry(
            id=1,
            key="test",
            content="本文",
            default_content="デフォルト",
            variables=[],
        )

        cache.set("test", entry)
        cache.invalidate("test")

        assert cache.get_fallback("test") is None


class TestPromptCacheInvalidateAll:
    """invalidate_allのテスト."""

    def test_invalidate_all_clears_all_entries(self):
        """全エントリを無効化できる."""
        cache = PromptCache(ttl_seconds=60)
        entry1 = PromptCacheEntry(
            id=1,
            key="key1",
            content="本文1",
            default_content="デフォルト1",
            variables=[],
        )
        entry2 = PromptCacheEntry(
            id=1,
            key="key2",
            content="本文2",
            default_content="デフォルト2",
            variables=[],
        )

        cache.set("key1", entry1)
        cache.set("key2", entry2)

        cache.invalidate_all()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_invalidate_all_empty_cache(self):
        """空のキャッシュで全無効化してもエラーにならない."""
        cache = PromptCache(ttl_seconds=60)

        # エラーが発生しないことを確認
        cache.invalidate_all()

    def test_invalidate_all_removes_from_fallback(self):
        """全無効化後はフォールバックでも取得できない."""
        cache = PromptCache(ttl_seconds=60)
        entry = PromptCacheEntry(
            id=1,
            key="test",
            content="本文",
            default_content="デフォルト",
            variables=[],
        )

        cache.set("test", entry)
        cache.invalidate_all()

        assert cache.get_fallback("test") is None


class TestPromptCacheSetAfterInvalidate:
    """無効化後の再設定テスト."""

    def test_set_after_invalidate(self):
        """無効化後に再設定できる."""
        cache = PromptCache(ttl_seconds=60)
        entry1 = PromptCacheEntry(
            id=1,
            key="test",
            content="本文1",
            default_content="デフォルト",
            variables=[],
        )
        entry2 = PromptCacheEntry(
            id=1,
            key="test",
            content="本文2",
            default_content="デフォルト",
            variables=[],
        )

        cache.set("test", entry1)
        cache.invalidate("test")
        cache.set("test", entry2)

        result = cache.get("test")
        assert result is not None
        assert result.content == "本文2"

    def test_set_after_invalidate_all(self):
        """全無効化後に再設定できる."""
        cache = PromptCache(ttl_seconds=60)
        entry = PromptCacheEntry(
            id=1,
            key="test",
            content="本文",
            default_content="デフォルト",
            variables=[],
        )

        cache.invalidate_all()
        cache.set("test", entry)

        result = cache.get("test")
        assert result is not None
        assert result.content == "本文"
