"""Importerバックエンド統合テスト.

Task 14.1: バックエンド統合テストの実装
- EmailPlugin + IMAPサーバーモックによる統合テスト
- OpenAIProvider + OpenAI APIモックによる統合テスト
- AnthropicProvider + Anthropic APIモックによる統合テスト
- AnalysisService + AIProviderモックによる統合テスト
- ImporterService + InquiryRepositoryによる統合テスト
- 完全なインポートフロー（メール取得→解析→問い合わせ作成）
- AIプロバイダー切り替えフロー
- エラーハンドリングフロー（接続失敗→リトライ→成功）
- 重複検出フロー

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6,
              3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5,
              5.1, 5.2, 5.3, 5.4, 5.5
"""
import socket
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.database.base import Base
from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus
from models.enums.priority import Priority
from services.importer.ai_provider_base import (AIAnalysisRequest,
                                                AIAnalysisResponse,
                                                AIProviderType)
from services.importer.ai_provider_registry import AIProviderRegistryService
from services.importer.analysis_service import (AnalysisResult,
                                                ImporterAnalysisService)
from services.importer.anthropic_provider import (AnthropicProvider,
                                                  AnthropicProviderConfig)
from services.importer.email_plugin import EmailPlugin, EmailPluginConfig
from services.importer.importer_service import ImporterService
from services.importer.openai_provider import (OpenAIProvider,
                                               OpenAIProviderConfig)
from services.importer.plugin_base import RawImportData
from services.importer.plugin_registry import PluginRegistryService
from tests.conftest import MockDataSourcePlugin

# ==============================================================================
# テスト用フィクスチャ
# ==============================================================================


@pytest.fixture
def test_engine():
    """インメモリSQLiteデータベースエンジンを作成."""
    # SQLiteではJSONBがサポートされないため、JSON型を使用
    engine = create_engine("sqlite:///:memory:")
    # テーブルを作成
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_session(test_engine) -> Session:
    """テスト用セッションを作成."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_imap():
    """IMAPサーバーモックを作成."""
    mock = MagicMock()
    mock.login.return_value = ("OK", [b"Logged in"])
    mock.select.return_value = ("OK", [b"1"])
    mock.search.return_value = ("OK", [b""])
    return mock


@pytest.fixture
def mock_openai_client():
    """OpenAIクライアントモックを作成."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[
        0
    ].message.content = """
{
    "title": "テスト問い合わせ",
    "content": "構造化されたテスト内容",
    "priority": "medium",
    "category": "development",
    "confidence_score": 0.85
}
"""
    mock.chat.completions.create.return_value = mock_response
    mock.models.list.return_value = MagicMock()
    return mock


@pytest.fixture
def mock_anthropic_client():
    """Anthropicクライアントモックを作成."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[
        0
    ].text = """
{
    "title": "Anthropic解析結果",
    "content": "Anthropicによる構造化内容",
    "priority": "high",
    "category": "maintenance",
    "confidence_score": 0.92
}
"""
    mock.messages.create.return_value = mock_response
    return mock


@pytest.fixture
def sample_email_bytes() -> bytes:
    """サンプルメールデータを作成."""
    email_content = """From: sender@example.com
Subject: =?utf-8?B?44OG44K544OI5ZWP44GE5ZCI44KP44Gb?=
Date: Sat, 11 Jan 2026 10:30:00 +0900
Message-ID: <test-message-id-001@example.com>
Content-Type: text/plain; charset=utf-8

これはテスト問い合わせの本文です。
システムに問題が発生しています。
至急対応をお願いします。
"""
    return email_content.encode("utf-8")


# ==============================================================================
# EmailPlugin + IMAPサーバーモック統合テスト
# ==============================================================================


class TestEmailPluginIMAPIntegration:
    """EmailPlugin + IMAPサーバーモックによる統合テスト."""

    def test_connect_fetch_disconnect_flow(self, mock_imap, sample_email_bytes) -> None:
        """接続→取得→切断の完全なフローが動作することを確認."""
        # モックの設定
        mock_imap.search.return_value = ("OK", [b"1"])
        mock_imap.fetch.return_value = (
            "OK",
            [(b"1 (RFC822 {1234}", sample_email_bytes)],
        )

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = EmailPluginConfig(
                imap_server="imap.example.com",
                username="user@example.com",
                password="secret123",
            )
            plugin = EmailPlugin(config)

            # 接続
            plugin.connect()
            assert plugin.is_connected is True

            # データ取得
            raw_data_list = plugin.fetch()
            assert len(raw_data_list) == 1
            assert raw_data_list[0].source_type == "email"
            assert raw_data_list[0].source_id == "<test-message-id-001@example.com>"

            # 既読マーク
            mock_imap.search.return_value = ("OK", [b"1"])
            mock_imap.store.return_value = ("OK", [b"1 (FLAGS (\\Seen))"])
            plugin.mark_as_processed(raw_data_list[0].source_id)

            # 切断
            plugin.disconnect()
            assert plugin.is_connected is False

    def test_connection_retry_with_backoff(self, mock_imap) -> None:
        """接続リトライと指数バックオフが正しく動作することを確認."""
        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
        ) as mock_imap_class, patch(
            "services.importer.email_plugin.time.sleep"
        ) as mock_sleep:
            # 2回失敗、3回目で成功
            mock_imap_success = MagicMock()
            mock_imap_success.login.return_value = ("OK", [b"Logged in"])
            mock_imap_success.select.return_value = ("OK", [b"1"])

            mock_imap_class.side_effect = [
                socket.error("Connection refused"),
                socket.timeout("Connection timed out"),
                mock_imap_success,
            ]

            config = EmailPluginConfig(
                imap_server="imap.example.com",
                username="user@example.com",
                password="secret123",
                retry_max=3,
            )
            plugin = EmailPlugin(config)
            plugin.connect()

            # 3回呼ばれることを確認
            assert mock_imap_class.call_count == 3
            # 指数バックオフで待機
            assert mock_sleep.call_count == 2

    def test_fetch_multiple_emails(self, mock_imap) -> None:
        """複数メールの取得が正しく動作することを確認."""

        # メール作成ヘルパー
        def create_email(msg_id: str, subject: str) -> bytes:
            return f"""From: sender@example.com
Subject: {subject}
Date: Sat, 11 Jan 2026 10:30:00 +0900
Message-ID: {msg_id}
Content-Type: text/plain; charset=utf-8

本文
""".encode(
                "utf-8"
            )

        mock_imap.search.return_value = ("OK", [b"1 2 3"])
        mock_imap.fetch.side_effect = [
            ("OK", [(b"1 (RFC822 {1234}", create_email("<msg1>", "件名1"))]),
            ("OK", [(b"2 (RFC822 {1234}", create_email("<msg2>", "件名2"))]),
            ("OK", [(b"3 (RFC822 {1234}", create_email("<msg3>", "件名3"))]),
        ]

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = EmailPluginConfig(
                imap_server="imap.example.com",
                username="user@example.com",
                password="secret123",
            )
            plugin = EmailPlugin(config)
            plugin.connect()

            raw_data_list = plugin.fetch()

            assert len(raw_data_list) == 3
            assert raw_data_list[0].source_id == "<msg1>"
            assert raw_data_list[1].source_id == "<msg2>"
            assert raw_data_list[2].source_id == "<msg3>"


# ==============================================================================
# OpenAIProvider + OpenAI APIモック統合テスト
# ==============================================================================


class TestOpenAIProviderIntegration:
    """OpenAIProvider + OpenAI APIモックによる統合テスト."""

    def test_initialize_and_analyze_flow(self, mock_openai_client) -> None:
        """初期化→解析の完全なフローが動作することを確認."""
        with patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ):
            config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
            )
            provider = OpenAIProvider(config)

            # 初期化
            provider.initialize()

            # ヘルスチェック
            assert provider.health_check() is True

            # 解析リクエストを作成
            request = AIAnalysisRequest(
                content="テスト問い合わせの本文です。",
                subject="テスト件名",
                sender="test@example.com",
                source_type="email",
            )

            # 解析実行
            response = provider.analyze(request)

            assert isinstance(response, AIAnalysisResponse)
            assert response.title == "テスト問い合わせ"
            assert response.priority == "medium"
            assert response.confidence_score == 0.85
            assert response.provider_type == "openai"
            assert response.model == "gpt-4"

    def test_analyze_with_retry(self, mock_openai_client) -> None:
        """APIエラー時のリトライが正しく動作することを確認."""
        mock_success_response = MagicMock()
        mock_success_response.choices = [MagicMock()]
        mock_success_response.choices[
            0
        ].message.content = """
{"title": "リトライ成功", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""

        # 2回失敗、3回目で成功
        mock_openai_client.chat.completions.create.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            mock_success_response,
        ]

        with patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ), patch("time.sleep"):
            config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
                retry_max=3,
            )
            provider = OpenAIProvider(config)
            provider.initialize()

            request = AIAnalysisRequest(
                content="テスト",
                subject="件名",
                sender="test@example.com",
                source_type="email",
            )

            response = provider.analyze(request)

            assert response.title == "リトライ成功"
            assert mock_openai_client.chat.completions.create.call_count == 3


# ==============================================================================
# AnthropicProvider + Anthropic APIモック統合テスト
# ==============================================================================


class TestAnthropicProviderIntegration:
    """AnthropicProvider + Anthropic APIモックによる統合テスト."""

    def test_initialize_and_analyze_flow(self, mock_anthropic_client) -> None:
        """初期化→解析の完全なフローが動作することを確認."""
        with patch(
            "services.importer.anthropic_provider.Anthropic",
            return_value=mock_anthropic_client,
        ):
            config = AnthropicProviderConfig(
                api_key="sk-ant-test-key",
                model="claude-3-sonnet-20240229",
            )
            provider = AnthropicProvider(config)

            # 初期化
            provider.initialize()

            # ヘルスチェック
            assert provider.health_check() is True

            # 解析リクエストを作成
            request = AIAnalysisRequest(
                content="テスト問い合わせの本文です。",
                subject="テスト件名",
                sender="test@example.com",
                source_type="email",
            )

            # 解析実行
            response = provider.analyze(request)

            assert isinstance(response, AIAnalysisResponse)
            assert response.title == "Anthropic解析結果"
            assert response.priority == "high"
            assert response.confidence_score == 0.92
            assert response.provider_type == "anthropic"

    def test_analyze_japanese_content(self, mock_anthropic_client) -> None:
        """日本語コンテンツの解析が正しく動作することを確認."""
        # 日本語レスポンスを設定
        mock_anthropic_client.messages.create.return_value.content[
            0
        ].text = """
{
    "title": "【緊急】システム障害報告",
    "content": "本番環境でデータベース接続エラーが発生しています。",
    "priority": "urgent",
    "category": "maintenance",
    "confidence_score": 0.95
}
"""

        with patch(
            "services.importer.anthropic_provider.Anthropic",
            return_value=mock_anthropic_client,
        ):
            config = AnthropicProviderConfig(
                api_key="sk-ant-test-key",
                model="claude-3-sonnet-20240229",
            )
            provider = AnthropicProvider(config)
            provider.initialize()

            request = AIAnalysisRequest(
                content="本番環境でDBエラーが発生しています。至急対応が必要です。",
                subject="【緊急】システム障害について",
                sender="田中太郎 <tanaka@example.co.jp>",
                source_type="email",
            )

            response = provider.analyze(request)

            assert "緊急" in response.title
            assert response.priority == "urgent"


# ==============================================================================
# AnalysisService + AIProvider統合テスト
# ==============================================================================


class TestAnalysisServiceIntegration:
    """AnalysisService + AIProviderモックによる統合テスト."""

    def test_analyze_with_default_provider(
        self, mock_openai_client, mock_anthropic_client
    ) -> None:
        """デフォルトプロバイダーでの解析が動作することを確認."""
        with patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ):
            # レジストリを作成してプロバイダーを登録
            registry = AIProviderRegistryService()

            openai_config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
            )
            registry.register(OpenAIProvider, openai_config)
            registry.set_default(AIProviderType.OPENAI)

            # 解析サービスを作成
            analysis_service = ImporterAnalysisService(registry)

            # サンプルデータ
            raw_data = RawImportData(
                source_id="test-001",
                source_type="email",
                content="テスト問い合わせの本文です。",
                subject="テスト件名",
                sender="test@example.com",
                received_at=datetime.now(UTC),
                raw_metadata={},
            )

            # 解析実行
            result = analysis_service.analyze(raw_data)

            assert result.is_ok
            analysis_result = result.unwrap()
            assert isinstance(analysis_result, AnalysisResult)
            assert analysis_result.title == "テスト問い合わせ"
            assert analysis_result.priority == Priority.MEDIUM
            assert analysis_result.confidence_score == 0.85
            assert analysis_result.needs_review is False  # 0.85 >= 0.8

    def test_analyze_with_specified_provider(
        self, mock_openai_client, mock_anthropic_client
    ) -> None:
        """指定プロバイダーでの解析が動作することを確認."""
        with patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ), patch(
            "services.importer.anthropic_provider.Anthropic",
            return_value=mock_anthropic_client,
        ):
            # レジストリを作成して両方のプロバイダーを登録
            registry = AIProviderRegistryService()

            openai_config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
            )
            anthropic_config = AnthropicProviderConfig(
                api_key="sk-ant-test-key",
                model="claude-3-sonnet-20240229",
            )

            registry.register(OpenAIProvider, openai_config)
            registry.register(AnthropicProvider, anthropic_config)
            registry.set_default(AIProviderType.OPENAI)

            # 解析サービスを作成
            analysis_service = ImporterAnalysisService(registry)

            # サンプルデータ
            raw_data = RawImportData(
                source_id="test-002",
                source_type="email",
                content="テスト問い合わせの本文です。",
                subject="テスト件名",
                sender="test@example.com",
                received_at=datetime.now(UTC),
                raw_metadata={},
            )

            # Anthropicを指定して解析実行
            result = analysis_service.analyze(
                raw_data, provider_type=AIProviderType.ANTHROPIC
            )

            assert result.is_ok
            analysis_result = result.unwrap()
            assert analysis_result.provider_type == "anthropic"
            assert analysis_result.title == "Anthropic解析結果"
            assert analysis_result.priority == Priority.HIGH

    def test_needs_review_flag_based_on_confidence(self, mock_openai_client) -> None:
        """信頼度に基づくneeds_reviewフラグが正しく設定されることを確認."""
        # 低信頼度レスポンスを設定
        mock_openai_client.chat.completions.create.return_value.choices[
            0
        ].message.content = """
{
    "title": "低信頼度解析",
    "content": "曖昧な内容",
    "priority": "medium",
    "confidence_score": 0.5
}
"""

        with patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ):
            registry = AIProviderRegistryService()
            openai_config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
            )
            registry.register(OpenAIProvider, openai_config)
            registry.set_default(AIProviderType.OPENAI)

            analysis_service = ImporterAnalysisService(registry)

            raw_data = RawImportData(
                source_id="test-low-confidence",
                source_type="email",
                content="曖昧な内容...",
                subject="不明な件名",
                sender="unknown@example.com",
                received_at=datetime.now(UTC),
                raw_metadata={},
            )

            result = analysis_service.analyze(raw_data)

            assert result.is_ok
            analysis_result = result.unwrap()
            assert analysis_result.confidence_score == 0.5
            assert analysis_result.needs_review is True  # 0.5 < 0.8


# ==============================================================================
# ImporterService + InquiryRepository統合テスト
# ==============================================================================


class TestImporterServiceIntegration:
    """ImporterService + InquiryRepositoryによる統合テスト."""

    def test_complete_import_flow(
        self, test_session: Session, mock_openai_client
    ) -> None:
        """完全なインポートフロー（メール取得→解析→問い合わせ作成）を確認."""
        with patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ):
            # プラグインレジストリを作成
            plugin_registry = PluginRegistryService()
            plugin_registry.register(MockDataSourcePlugin, {})

            # プラグインにデータを設定
            plugin = plugin_registry.get_plugin("mock_plugin")
            assert plugin is not None
            plugin.set_data(
                [
                    RawImportData(
                        source_id="<import-test-001>",
                        source_type="email",
                        content="テスト問い合わせの本文です。",
                        subject="テスト件名",
                        sender="test@example.com",
                        received_at=datetime.now(UTC),
                        raw_metadata={"header": "value"},
                    )
                ]
            )

            # AIプロバイダーレジストリを作成
            ai_registry = AIProviderRegistryService()
            openai_config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
            )
            ai_registry.register(OpenAIProvider, openai_config)
            ai_registry.set_default(AIProviderType.OPENAI)

            # 解析サービスを作成
            analysis_service = ImporterAnalysisService(ai_registry)

            # ImporterServiceを作成
            importer_service = ImporterService(
                session=test_session,
                plugin_registry=plugin_registry,
                analysis_service=analysis_service,
            )

            # インポート実行
            result = importer_service.execute_import("mock_plugin")

            # 結果を検証
            assert result.is_ok
            import_result = result.unwrap()
            assert import_result.total_fetched == 1
            assert import_result.total_imported == 1
            assert import_result.total_skipped == 0
            assert import_result.total_failed == 0
            assert len(import_result.imported_inquiry_ids) == 1

            # 問い合わせがDBに作成されたことを確認
            inquiry_id = import_result.imported_inquiry_ids[0]
            inquiry = (
                test_session.query(InquiryModel)
                .filter(InquiryModel.id == inquiry_id)
                .first()
            )
            assert inquiry is not None
            assert inquiry.status == InquiryStatus.RECEIVED

            # メタデータが設定されていることを確認
            metadata = inquiry.inquiry_metadata
            assert metadata is not None
            assert "importer" in metadata
            assert metadata["importer"]["source_type"] == "mock_plugin"
            assert metadata["importer"]["source_id"] == "<import-test-001>"
            assert metadata["importer"]["ai_provider"] == "openai"
            assert metadata["importer"]["ai_model"] == "gpt-4"

    def test_duplicate_detection_flow(
        self, test_session: Session, mock_openai_client
    ) -> None:
        """重複検出フローが正しく動作することを確認."""
        with patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ):
            # プラグインレジストリを作成
            plugin_registry = PluginRegistryService()
            plugin_registry.register(MockDataSourcePlugin, {})

            # プラグインにデータを設定
            plugin = plugin_registry.get_plugin("mock_plugin")
            assert plugin is not None

            raw_data = RawImportData(
                source_id="<duplicate-test-001>",
                source_type="email",
                content="重複テスト",
                subject="重複件名",
                sender="dup@example.com",
                received_at=datetime.now(UTC),
                raw_metadata={},
            )
            plugin.set_data([raw_data])

            # AIプロバイダーレジストリを作成
            ai_registry = AIProviderRegistryService()
            openai_config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
            )
            ai_registry.register(OpenAIProvider, openai_config)
            ai_registry.set_default(AIProviderType.OPENAI)

            # 解析サービスを作成
            analysis_service = ImporterAnalysisService(ai_registry)

            # ImporterServiceを作成
            importer_service = ImporterService(
                session=test_session,
                plugin_registry=plugin_registry,
                analysis_service=analysis_service,
            )

            # 1回目のインポート
            result1 = importer_service.execute_import("mock_plugin")
            assert result1.is_ok
            assert result1.unwrap().total_imported == 1

            # 2回目のインポート（同じデータ）
            result2 = importer_service.execute_import("mock_plugin")
            assert result2.is_ok
            import_result2 = result2.unwrap()
            assert import_result2.total_fetched == 1
            assert import_result2.total_imported == 0  # 重複のためインポートされない
            assert import_result2.total_skipped == 1  # スキップされる

    def test_ai_provider_switch_flow(
        self, test_session: Session, mock_openai_client, mock_anthropic_client
    ) -> None:
        """AIプロバイダー切り替えフローが正しく動作することを確認."""
        with patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ), patch(
            "services.importer.anthropic_provider.Anthropic",
            return_value=mock_anthropic_client,
        ):
            # プラグインレジストリを作成
            plugin_registry = PluginRegistryService()
            plugin_registry.register(MockDataSourcePlugin, {})

            # AIプロバイダーレジストリを作成
            ai_registry = AIProviderRegistryService()

            openai_config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
            )
            anthropic_config = AnthropicProviderConfig(
                api_key="sk-ant-test-key",
                model="claude-3-sonnet-20240229",
            )

            ai_registry.register(OpenAIProvider, openai_config)
            ai_registry.register(AnthropicProvider, anthropic_config)
            ai_registry.set_default(AIProviderType.OPENAI)

            # 解析サービスを作成
            analysis_service = ImporterAnalysisService(ai_registry)

            # ImporterServiceを作成
            importer_service = ImporterService(
                session=test_session,
                plugin_registry=plugin_registry,
                analysis_service=analysis_service,
            )

            # プラグインにデータを設定（OpenAI用）
            plugin = plugin_registry.get_plugin("mock_plugin")
            plugin.set_data(
                [
                    RawImportData(
                        source_id="<openai-test-001>",
                        source_type="email",
                        content="OpenAIで解析",
                        subject="OpenAI件名",
                        sender="openai@example.com",
                        received_at=datetime.now(UTC),
                        raw_metadata={},
                    )
                ]
            )

            # OpenAIでインポート（デフォルト）
            result1 = importer_service.execute_import("mock_plugin")
            assert result1.is_ok
            inquiry1 = (
                test_session.query(InquiryModel)
                .filter(InquiryModel.id == result1.unwrap().imported_inquiry_ids[0])
                .first()
            )
            assert inquiry1.inquiry_metadata["importer"]["ai_provider"] == "openai"

            # プラグインにデータを設定（Anthropic用）
            plugin.set_data(
                [
                    RawImportData(
                        source_id="<anthropic-test-001>",
                        source_type="email",
                        content="Anthropicで解析",
                        subject="Anthropic件名",
                        sender="anthropic@example.com",
                        received_at=datetime.now(UTC),
                        raw_metadata={},
                    )
                ]
            )

            # Anthropicを指定してインポート
            result2 = importer_service.execute_import(
                "mock_plugin",
                ai_provider_type=AIProviderType.ANTHROPIC,
            )
            assert result2.is_ok
            inquiry2 = (
                test_session.query(InquiryModel)
                .filter(InquiryModel.id == result2.unwrap().imported_inquiry_ids[0])
                .first()
            )
            assert inquiry2.inquiry_metadata["importer"]["ai_provider"] == "anthropic"


# ==============================================================================
# エラーハンドリングフロー統合テスト
# ==============================================================================


class TestErrorHandlingIntegration:
    """エラーハンドリングフロー（接続失敗→リトライ→成功）の統合テスト."""

    def test_connection_failure_error_handling(self, test_session: Session) -> None:
        """接続失敗時のエラーハンドリングが正しく動作することを確認."""
        # 接続失敗するプラグインを登録
        plugin_registry = PluginRegistryService()
        plugin_registry.register(MockDataSourcePlugin, {"fail_connect": True})

        # ダミーの解析サービス（接続失敗で使用されない）
        mock_analysis_service = MagicMock(spec=ImporterAnalysisService)

        importer_service = ImporterService(
            session=test_session,
            plugin_registry=plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = importer_service.execute_import("mock_plugin")

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-303"
        assert "接続に失敗" in error.message

    def test_fetch_failure_error_handling(self, test_session: Session) -> None:
        """データ取得失敗時のエラーハンドリングが正しく動作することを確認."""
        # データ取得失敗するプラグインを登録
        plugin_registry = PluginRegistryService()
        plugin_registry.register(MockDataSourcePlugin, {"fail_fetch": True})

        # ダミーの解析サービス
        mock_analysis_service = MagicMock(spec=ImporterAnalysisService)

        importer_service = ImporterService(
            session=test_session,
            plugin_registry=plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = importer_service.execute_import("mock_plugin")

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-306"
        assert "データ取得に失敗" in error.message

    def test_analysis_failure_partial_import(self, test_session: Session) -> None:
        """解析失敗時に部分インポートが正しく動作することを確認."""
        # カスタムモックを使って1件目は成功、2件目はAPI例外を発生させる
        mock_openai_client = MagicMock()
        mock_openai_client.models.list.return_value = MagicMock()

        # 成功レスポンス
        mock_success = MagicMock()
        mock_success.choices = [MagicMock()]
        mock_success.choices[
            0
        ].message.content = """
{"title": "成功", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""

        # 2件目のデータでAPI例外を発生させる（リトライ後も失敗）
        mock_openai_client.chat.completions.create.side_effect = [
            mock_success,
            Exception("API rate limit exceeded"),
            Exception("API rate limit exceeded"),
            Exception("API rate limit exceeded"),
            Exception("API rate limit exceeded"),
        ]

        with patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ), patch("time.sleep"):
            plugin_registry = PluginRegistryService()
            plugin_registry.register(MockDataSourcePlugin, {})

            plugin = plugin_registry.get_plugin("mock_plugin")
            plugin.set_data(
                [
                    RawImportData(
                        source_id="<success-001>",
                        source_type="email",
                        content="成功データ",
                        subject="成功",
                        sender="success@example.com",
                        received_at=datetime.now(UTC),
                        raw_metadata={},
                    ),
                    RawImportData(
                        source_id="<fail-001>",
                        source_type="email",
                        content="失敗データ",
                        subject="失敗",
                        sender="fail@example.com",
                        received_at=datetime.now(UTC),
                        raw_metadata={},
                    ),
                ]
            )

            ai_registry = AIProviderRegistryService()
            openai_config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
                retry_max=3,  # 3回リトライ
            )
            ai_registry.register(OpenAIProvider, openai_config)
            ai_registry.set_default(AIProviderType.OPENAI)

            analysis_service = ImporterAnalysisService(ai_registry)

            importer_service = ImporterService(
                session=test_session,
                plugin_registry=plugin_registry,
                analysis_service=analysis_service,
            )

            result = importer_service.execute_import("mock_plugin")

            assert result.is_ok
            import_result = result.unwrap()
            assert import_result.total_fetched == 2
            assert import_result.total_imported == 1
            assert import_result.total_failed == 1
            assert len(import_result.errors) == 1
            assert import_result.errors[0].source_id == "<fail-001>"

    def test_analysis_json_parse_fallback(self, test_session: Session) -> None:
        """JSONパース失敗時にフォールバック値が使用されることを確認."""
        mock_openai_client = MagicMock()
        mock_openai_client.models.list.return_value = MagicMock()

        # 不正なJSONレスポンス（フォールバック動作をテスト）
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "invalid json response"
        mock_openai_client.chat.completions.create.return_value = mock_response

        with patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ):
            plugin_registry = PluginRegistryService()
            plugin_registry.register(MockDataSourcePlugin, {})

            plugin = plugin_registry.get_plugin("mock_plugin")
            plugin.set_data(
                [
                    RawImportData(
                        source_id="<fallback-test-001>",
                        source_type="email",
                        content="テストデータ",
                        subject="件名",
                        sender="test@example.com",
                        received_at=datetime.now(UTC),
                        raw_metadata={},
                    ),
                ]
            )

            ai_registry = AIProviderRegistryService()
            openai_config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
            )
            ai_registry.register(OpenAIProvider, openai_config)
            ai_registry.set_default(AIProviderType.OPENAI)

            analysis_service = ImporterAnalysisService(ai_registry)

            importer_service = ImporterService(
                session=test_session,
                plugin_registry=plugin_registry,
                analysis_service=analysis_service,
            )

            result = importer_service.execute_import("mock_plugin")

            # フォールバック値が使用されても、インポート自体は成功する
            assert result.is_ok
            import_result = result.unwrap()
            assert import_result.total_imported == 1

            # 問い合わせを確認
            inquiry = (
                test_session.query(InquiryModel)
                .filter(InquiryModel.id == import_result.imported_inquiry_ids[0])
                .first()
            )
            assert inquiry is not None
            # フォールバック値：confidence_score=0.5なのでneeds_reviewはTrue
            assert inquiry.inquiry_metadata["importer"]["needs_review"] is True
            assert inquiry.inquiry_metadata["importer"]["confidence_score"] == 0.5


# ==============================================================================
# 完全なE2Eインポートフロー統合テスト
# ==============================================================================


class TestE2EImportFlow:
    """完全なE2Eインポートフローの統合テスト."""

    def test_email_to_inquiry_full_flow(
        self,
        test_session: Session,
        mock_imap,
        mock_openai_client,
        sample_email_bytes,
    ) -> None:
        """メール取得→AI解析→問い合わせ作成の完全なE2Eフローを確認."""
        # IMAPサーバーのレスポンスを設定
        mock_imap.search.return_value = ("OK", [b"1"])
        mock_imap.fetch.return_value = (
            "OK",
            [(b"1 (RFC822 {1234}", sample_email_bytes)],
        )

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ), patch(
            "services.importer.openai_provider.OpenAI",
            return_value=mock_openai_client,
        ):
            # EmailPluginを登録
            plugin_registry = PluginRegistryService()
            email_config = EmailPluginConfig(
                imap_server="imap.example.com",
                username="user@example.com",
                password="secret123",
            )
            plugin_registry.register(EmailPlugin, email_config)

            # OpenAIProviderを登録
            ai_registry = AIProviderRegistryService()
            openai_config = OpenAIProviderConfig(
                api_key="sk-test-key",
                model="gpt-4",
            )
            ai_registry.register(OpenAIProvider, openai_config)
            ai_registry.set_default(AIProviderType.OPENAI)

            # サービスを作成
            analysis_service = ImporterAnalysisService(ai_registry)
            importer_service = ImporterService(
                session=test_session,
                plugin_registry=plugin_registry,
                analysis_service=analysis_service,
            )

            # インポート実行
            result = importer_service.execute_import("email")

            # 結果を検証
            assert result.is_ok
            import_result = result.unwrap()
            assert import_result.total_fetched == 1
            assert import_result.total_imported == 1

            # 問い合わせの詳細を検証
            inquiry = (
                test_session.query(InquiryModel)
                .filter(InquiryModel.id == import_result.imported_inquiry_ids[0])
                .first()
            )

            assert inquiry is not None
            assert inquiry.status == InquiryStatus.RECEIVED
            assert inquiry.user_id == "importer:email"

            # メタデータを検証
            metadata = inquiry.inquiry_metadata["importer"]
            assert metadata["source_type"] == "email"
            assert metadata["source_id"] == "<test-message-id-001@example.com>"
            assert metadata["ai_provider"] == "openai"
            assert metadata["ai_model"] == "gpt-4"
            assert metadata["confidence_score"] == 0.85
            assert metadata["needs_review"] is False
