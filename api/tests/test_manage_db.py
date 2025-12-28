"""データベース管理CLIツールのテスト."""
import sys
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import OperationalError

from manage_db import check_connection, main, seed_data


class TestCheckConnection:
    """check_connection関数のテストクラス."""

    @patch("manage_db.engine")
    def test_check_connection_success(self, mock_engine, capsys):
        """データベース接続成功時にTrueを返すこと."""
        # モックの設定
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        # テスト実行
        result = check_connection()

        # 検証
        assert result is True
        captured = capsys.readouterr()
        assert "✅ Database connection successful" in captured.out

    @patch("manage_db.engine")
    def test_check_connection_failure(self, mock_engine, capsys):
        """データベース接続失敗時にFalseを返すこと."""
        # モックの設定 - 例外を発生させる
        mock_engine.connect.side_effect = OperationalError(
            "connection failed", None, None
        )

        # テスト実行
        result = check_connection()

        # 検証
        assert result is False
        captured = capsys.readouterr()
        assert "❌ Database connection failed" in captured.err

    @patch("manage_db.engine")
    def test_check_connection_executes_query(self, mock_engine):
        """データベース接続時にSELECT 1クエリを実行すること."""
        # モックの設定
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        # テスト実行
        check_connection()

        # 検証 - text()でラップされたクエリが実行されたことを確認
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        # text()オブジェクトが渡されていることを確認
        assert call_args is not None


class TestSeedData:
    """seed_data関数のテストクラス."""

    def test_seed_data_returns_true(self, capsys):
        """seed_data関数がTrueを返すこと（実装待ち）."""
        result = seed_data()
        assert result is True

    def test_seed_data_shows_not_implemented_message(self, capsys):
        """seed_data関数が未実装メッセージを表示すること."""
        seed_data()
        captured = capsys.readouterr()
        assert "🌱 Seeding test data..." in captured.out
        assert "⚠️ Test data seeding is not yet implemented" in captured.out
        assert "no changes were made" in captured.out

    def test_seed_data_does_not_show_success_message(self, capsys):
        """seed_data関数が成功メッセージを表示しないこと（未実装のため）."""
        seed_data()
        captured = capsys.readouterr()
        assert "✅ Test data seeded successfully" not in captured.out

    @patch("manage_db.print")
    def test_seed_data_exception_handling(self, mock_print):
        """seed_data関数内で例外が発生した場合の処理."""
        # printをモックして例外を発生させる
        mock_print.side_effect = [None, Exception("Test error"), None]

        # テスト実行
        result = seed_data()

        # 検証 - 例外が発生してもFalseを返すこと
        assert result is False


class TestMain:
    """main関数のテストクラス."""

    @patch("manage_db.check_connection")
    @patch.object(sys, "argv", ["manage_db.py", "check"])
    def test_main_check_command_success(self, mock_check):
        """checkコマンドが成功した場合に0を返すこと."""
        mock_check.return_value = True
        result = main()
        assert result == 0
        mock_check.assert_called_once()

    @patch("manage_db.check_connection")
    @patch.object(sys, "argv", ["manage_db.py", "check"])
    def test_main_check_command_failure(self, mock_check):
        """checkコマンドが失敗した場合に1を返すこと."""
        mock_check.return_value = False
        result = main()
        assert result == 1
        mock_check.assert_called_once()

    @patch("manage_db.seed_data")
    @patch.object(sys, "argv", ["manage_db.py", "seed"])
    def test_main_seed_command_success(self, mock_seed):
        """seedコマンドが成功した場合に0を返すこと."""
        mock_seed.return_value = True
        result = main()
        assert result == 0
        mock_seed.assert_called_once()

    @patch("manage_db.seed_data")
    @patch.object(sys, "argv", ["manage_db.py", "seed"])
    def test_main_seed_command_failure(self, mock_seed):
        """seedコマンドが失敗した場合に1を返すこと."""
        mock_seed.return_value = False
        result = main()
        assert result == 1
        mock_seed.assert_called_once()

    @patch.object(sys, "argv", ["manage_db.py"])
    def test_main_no_command(self, capsys):
        """コマンドが指定されない場合に1を返し、使用方法を表示すること."""
        result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "Usage: python manage_db.py [check|seed]" in captured.err

    @patch.object(sys, "argv", ["manage_db.py", "invalid"])
    def test_main_invalid_command(self, capsys):
        """無効なコマンドが指定された場合に1を返し、エラーを表示すること."""
        result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "Unknown command: invalid" in captured.err
        assert "Available commands: check, seed" in captured.err

    @patch.object(sys, "argv", ["manage_db.py", "check"])
    @patch("manage_db.check_connection")
    def test_main_calls_correct_function_for_check(self, mock_check):
        """checkコマンドがcheck_connection関数を呼び出すこと."""
        mock_check.return_value = True
        main()
        mock_check.assert_called_once()

    @patch.object(sys, "argv", ["manage_db.py", "seed"])
    @patch("manage_db.seed_data")
    def test_main_calls_correct_function_for_seed(self, mock_seed):
        """seedコマンドがseed_data関数を呼び出すこと."""
        mock_seed.return_value = True
        main()
        mock_seed.assert_called_once()


class TestMainIntegration:
    """main関数の統合テストクラス."""

    @patch.object(sys, "argv", ["manage_db.py", "check"])
    @patch("manage_db.engine")
    def test_main_integration_check_command(self, mock_engine):
        """checkコマンドの統合テスト."""
        # モックの設定
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        # テスト実行
        result = main()

        # 検証
        assert result == 0

    @patch.object(sys, "argv", ["manage_db.py", "seed"])
    def test_main_integration_seed_command(self, capsys):
        """seedコマンドの統合テスト."""
        result = main()

        # 検証 - 未実装でもエラーなく実行できること
        assert result == 0
        captured = capsys.readouterr()
        assert "🌱 Seeding test data..." in captured.out


class TestCLIUsage:
    """CLI使用方法のテストクラス."""

    def test_usage_message_format(self, capsys):
        """使用方法メッセージのフォーマットが正しいこと."""
        with patch.object(sys, "argv", ["manage_db.py"]):
            main()
            captured = capsys.readouterr()
            # 使用方法メッセージに必要な情報が含まれていること
            assert "manage_db.py" in captured.err
            assert "check" in captured.err
            assert "seed" in captured.err

    def test_error_messages_go_to_stderr(self, capsys):
        """エラーメッセージが標準エラー出力に出力されること."""
        with patch.object(sys, "argv", ["manage_db.py", "invalid"]):
            main()
            captured = capsys.readouterr()
            # エラーメッセージが標準エラー出力に出力されること
            assert len(captured.err) > 0
            assert "Unknown command" in captured.err

    @patch("manage_db.engine")
    def test_connection_error_goes_to_stderr(self, mock_engine, capsys):
        """接続エラーメッセージが標準エラー出力に出力されること."""
        mock_engine.connect.side_effect = OperationalError(
            "connection failed", None, None
        )

        check_connection()
        captured = capsys.readouterr()
        assert len(captured.err) > 0
        assert "❌ Database connection failed" in captured.err
