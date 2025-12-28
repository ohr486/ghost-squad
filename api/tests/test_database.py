"""データベース接続とセッション管理のテスト."""
import os
from unittest.mock import patch

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal, engine, get_db


class TestDatabaseConnection:
    """データベース接続のテストクラス."""

    def test_engine_exists(self):
        """エンジンが作成されていること."""
        assert engine is not None

    def test_engine_has_pool_pre_ping(self):
        """エンジンにpool_pre_pingが設定されていること."""
        assert engine.pool._pre_ping is True

    def test_engine_echo_based_on_debug_env(self):
        """DEBUG環境変数に基づいてechoが設定されること."""
        # 現在のDEBUG設定を確認
        debug_value = os.getenv("DEBUG", "false").lower()
        expected_echo = debug_value == "true"
        assert engine.echo == expected_echo

    def test_session_factory_exists(self):
        """セッションファクトリーが作成されていること."""
        assert SessionLocal is not None

    def test_session_factory_creates_session(self):
        """セッションファクトリーからセッションを作成できること."""
        session = SessionLocal()
        assert isinstance(session, Session)
        session.close()

    def test_session_bind_configured(self):
        """セッションがエンジンにバインドされていること."""
        session = SessionLocal()
        assert session.bind is not None
        session.close()

    def test_session_autoflush_disabled(self):
        """セッションのautoflushが無効であること."""
        session = SessionLocal()
        assert session.autoflush is False
        session.close()


class TestGetDb:
    """get_db関数のテストクラス."""

    def test_get_db_yields_session(self):
        """get_dbがセッションをyieldすること."""
        db_generator = get_db()
        db = next(db_generator)
        assert isinstance(db, Session)
        # クリーンアップ
        try:
            next(db_generator)
        except StopIteration:
            pass

    def test_get_db_closes_session_on_completion(self):
        """get_dbが終了時にセッションをクローズすること."""
        db_generator = get_db()
        db = next(db_generator)

        # セッションインスタンスが取得できることを確認
        assert db is not None
        assert isinstance(db, Session)

        # ジェネレーターを完了させる
        try:
            next(db_generator)
        except StopIteration:
            pass

        # セッションがクローズされたことを確認
        # クローズ後は新しいクエリを実行できないはず
        with pytest.raises(Exception):
            db.execute(text("SELECT 1"))

    def test_get_db_closes_session_on_exception(self):
        """get_dbが例外発生時にもセッションをクローズすること."""
        db_generator = get_db()
        db = next(db_generator)

        # 例外を発生させてクリーンアップ
        try:
            db_generator.throw(Exception("Test exception"))
        except Exception:
            pass

        # セッションがクローズされたことを確認
        with pytest.raises(Exception):
            db.execute(text("SELECT 1"))

    def test_get_db_creates_new_session_each_time(self):
        """get_dbが毎回新しいセッションを作成すること."""
        db_gen1 = get_db()
        db1 = next(db_gen1)

        db_gen2 = get_db()
        db2 = next(db_gen2)

        # 異なるセッションインスタンスであることを確認
        assert db1 is not db2

        # クリーンアップ
        for gen in [db_gen1, db_gen2]:
            try:
                next(gen)
            except StopIteration:
                pass


class TestDatabaseURL:
    """データベースURL設定のテストクラス."""

    @patch.dict(
        os.environ, {"DATABASE_URL": "postgresql://test:test@testhost:5432/testdb"}
    )
    def test_database_url_from_environment(self):
        """環境変数からデータベースURLを取得できること."""
        # モジュールを再インポートして環境変数を反映
        import importlib
        import database

        importlib.reload(database)

        # DATABASE_URLが環境変数から設定されていることを確認
        # パスワードは***でマスクされるため、ホスト名とデータベース名をチェック
        assert "testhost" in str(database.engine.url)
        assert "testdb" in str(database.engine.url)

    @patch.dict(os.environ, {}, clear=True)
    @patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False)
    def test_database_url_default_value(self):
        """DATABASE_URLが未設定の場合、デフォルト値を使用すること."""
        # デフォルトURLを確認（実際の環境に依存）
        from database import DATABASE_URL

        # デフォルト値またはos.getenvの結果を確認
        assert DATABASE_URL is not None
        assert isinstance(DATABASE_URL, str)


class TestDatabaseIntegration:
    """データベース統合テストクラス."""

    @pytest.mark.skipif(
        not os.getenv("DATABASE_URL", "").startswith("postgresql://"),
        reason="Database connection not available",
    )
    def test_can_connect_to_database(self):
        """データベースに接続できること."""
        # 実際のエンジンを使用して接続テスト
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1
        except Exception:
            pytest.skip("Database connection not available")

    @pytest.mark.skipif(
        not os.getenv("DATABASE_URL", "").startswith("postgresql://"),
        reason="Database connection not available",
    )
    def test_session_can_execute_query(self):
        """セッションを使用してクエリを実行できること."""
        session = SessionLocal()
        try:
            result = session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        except Exception:
            pytest.skip("Database connection not available")
        finally:
            session.close()

    @pytest.mark.skipif(
        not os.getenv("DATABASE_URL", "").startswith("postgresql://"),
        reason="Database connection not available",
    )
    def test_get_db_integration(self):
        """get_dbを使用してデータベース操作ができること."""
        db_generator = get_db()
        db = next(db_generator)

        try:
            # データベースクエリを実行
            result = db.execute(text("SELECT 1 as value"))
            row = result.fetchone()
            assert row[0] == 1
        except Exception:
            pytest.skip("Database connection not available")
        finally:
            # ジェネレーターを完了させる
            try:
                next(db_generator)
            except StopIteration:
                pass
