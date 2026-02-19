"""既存サービスのプロンプト管理統合テスト.

Task 7.1: StoryGenerationServiceのプロンプト取得元切り替え
Task 7.2: OpenAI/AnthropicProviderのプロンプト取得元切り替え

Requirements: 5.1, 5.2, 5.3, 5.4
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from services.importer.ai_provider_base import (
    AIAnalysisRequest,
)
from services.importer.anthropic_provider import (
    ANALYSIS_SYSTEM_PROMPT as ANTHROPIC_DEFAULT_PROMPT,
)
from services.importer.anthropic_provider import (
    AnthropicProvider,
    AnthropicProviderConfig,
)
from services.importer.openai_provider import (
    ANALYSIS_SYSTEM_PROMPT as OPENAI_DEFAULT_PROMPT,
)
from services.importer.openai_provider import (
    OpenAIProvider,
    OpenAIProviderConfig,
)
from services.prompt_defaults import (
    _IMPORT_ANALYSIS_SYSTEM_CONTENT,
    _STORY_GENERATION_SYSTEM_CONTENT,
    _STORY_GENERATION_USER_CONTENT,
)


# =========================================================================
# Task 7.1: StoryGenerationService プロンプト統合
# =========================================================================


class TestStoryGenerationPromptIntegration:
    """StoryGenerationServiceのプロンプト取得元統合テスト."""

    @pytest.fixture
    def mock_session(self):
        """モックセッションを作成する."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_prompt_service(self):
        """モックPromptServiceを作成する."""
        from services.prompt_service import PromptData

        svc = MagicMock()

        system_prompt = PromptData(
            id=1,
            key="story_generation_system",
            name="システムプロンプト",
            description=None,
            category="story_generation",
            content="カスタムシステムプロンプト",
            default_content=_STORY_GENERATION_SYSTEM_CONTENT,
            variables=[],
            is_modified=True,
        )
        user_prompt = PromptData(
            id=2,
            key="story_generation_user",
            name="ユーザープロンプト",
            description=None,
            category="story_generation",
            content="カスタムユーザープロンプト: {inquiry_content}",
            default_content=_STORY_GENERATION_USER_CONTENT,
            variables=["inquiry_content"],
            is_modified=True,
        )

        def side_effect(key):
            if key == "story_generation_system":
                return system_prompt
            elif key == "story_generation_user":
                return user_prompt
            raise Exception(f"Unknown key: {key}")

        svc.get_prompt.side_effect = side_effect
        return svc

    @pytest.fixture
    def service_with_prompts(
        self, mock_session, mock_prompt_service
    ):
        """PromptService付きのStoryGenerationServiceを作成."""
        from services.story_generation_service import (
            StoryGenerationService,
        )

        with patch(
            "services.story_generation_service.OpenAI"
        ) as mock_openai, patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test-key-1234567890ab"},
        ):
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            svc = StoryGenerationService(
                mock_session,
                prompt_service=mock_prompt_service,
            )
            svc._test_mock_client = mock_client
            return svc

    @pytest.fixture
    def service_without_prompts(self, mock_session):
        """PromptServiceなしのStoryGenerationServiceを作成."""
        from services.story_generation_service import (
            StoryGenerationService,
        )

        with patch(
            "services.story_generation_service.OpenAI"
        ) as mock_openai, patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test-key-1234567890ab"},
        ):
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            svc = StoryGenerationService(mock_session)
            svc._test_mock_client = mock_client
            return svc

    def test_accepts_prompt_service_parameter(
        self, service_with_prompts
    ):
        """prompt_serviceパラメータを受け取れる."""
        assert service_with_prompts._prompt_service is not None

    def test_prompt_service_defaults_to_none(
        self, service_without_prompts
    ):
        """prompt_serviceはデフォルトでNone."""
        assert service_without_prompts._prompt_service is None

    def test_uses_prompt_service_for_system_prompt(
        self, service_with_prompts, mock_prompt_service
    ):
        """PromptServiceからシステムプロンプトを取得する."""
        system_prompt, user_prompt = (
            service_with_prompts._get_prompts("テスト内容")
        )
        assert system_prompt == "カスタムシステムプロンプト"
        mock_prompt_service.get_prompt.assert_any_call(
            "story_generation_system"
        )

    def test_uses_prompt_service_for_user_prompt(
        self, service_with_prompts, mock_prompt_service
    ):
        """PromptServiceからユーザープロンプトを取得する."""
        system_prompt, user_prompt = (
            service_with_prompts._get_prompts("テスト内容")
        )
        assert "カスタムユーザープロンプト" in user_prompt
        assert "テスト内容" in user_prompt
        mock_prompt_service.get_prompt.assert_any_call(
            "story_generation_user"
        )

    def test_fallback_when_prompt_service_is_none(
        self, service_without_prompts
    ):
        """PromptServiceがNoneの場合、ハードコードにフォールバック."""
        system_prompt, user_prompt = (
            service_without_prompts._get_prompts("テスト内容")
        )
        assert "アジャイル開発の専門家" in system_prompt
        assert "テスト内容" in user_prompt

    def test_fallback_when_prompt_service_raises(
        self, service_with_prompts, mock_prompt_service
    ):
        """PromptServiceが例外を投げた場合、フォールバック."""
        mock_prompt_service.get_prompt.side_effect = (
            Exception("DB接続エラー")
        )
        system_prompt, user_prompt = (
            service_with_prompts._get_prompts("テスト内容")
        )
        assert "アジャイル開発の専門家" in system_prompt
        assert "テスト内容" in user_prompt

    def test_existing_service_works_without_prompt_service(
        self, service_without_prompts
    ):
        """PromptServiceなしでも既存機能が動作する."""
        # _get_prompts はフォールバックで動作するはず
        system_prompt, user_prompt = (
            service_without_prompts._get_prompts(
                "ログイン機能が欲しい"
            )
        )
        assert len(system_prompt) > 0
        assert len(user_prompt) > 0
        assert "ログイン機能が欲しい" in user_prompt

    def test_story_generation_prompts_no_double_braces(self):
        """ストーリー生成プロンプトに無効な二重波括弧がないこと."""
        # JSON例は有効なJSONとなるように単一波括弧のみを使用する。
        assert "{{" not in _STORY_GENERATION_SYSTEM_CONTENT
        assert "}}" not in _STORY_GENERATION_SYSTEM_CONTENT
        assert "{{" not in _STORY_GENERATION_USER_CONTENT
        assert "}}" not in _STORY_GENERATION_USER_CONTENT

        # 重要な日本語フレーズが含まれていることを確認する。
        assert "アジャイル開発の専門家" in _STORY_GENERATION_SYSTEM_CONTENT
        assert "出力形式（JSON）" in _STORY_GENERATION_USER_CONTENT


# =========================================================================
# Task 7.2: OpenAIProvider プロンプト統合
# =========================================================================


class TestOpenAIProviderPromptIntegration:
    """OpenAIProviderのプロンプト取得元統合テスト."""

    @pytest.fixture
    def config(self):
        """テスト用設定を作成する."""
        return OpenAIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
        )

    @pytest.fixture
    def custom_prompt_getter(self):
        """カスタムプロンプトゲッターを作成する."""
        return lambda: "カスタム解析プロンプト"

    @pytest.fixture
    def provider_with_getter(self, config, custom_prompt_getter):
        """ゲッター付きプロバイダーを作成する."""
        return OpenAIProvider(
            config,
            system_prompt_getter=custom_prompt_getter,
        )

    @pytest.fixture
    def provider_without_getter(self, config):
        """ゲッターなしプロバイダーを作成する."""
        return OpenAIProvider(config)

    def test_accepts_system_prompt_getter(
        self, provider_with_getter
    ):
        """system_prompt_getterパラメータを受け取れる."""
        assert (
            provider_with_getter._system_prompt_getter
            is not None
        )

    def test_system_prompt_getter_defaults_to_none(
        self, provider_without_getter
    ):
        """system_prompt_getterはデフォルトでNone."""
        assert (
            provider_without_getter._system_prompt_getter
            is None
        )

    def test_get_system_prompt_uses_getter(
        self, provider_with_getter
    ):
        """ゲッターが設定されている場合、それを使用する."""
        prompt = provider_with_getter._get_system_prompt()
        assert prompt == "カスタム解析プロンプト"

    def test_get_system_prompt_fallback_without_getter(
        self, provider_without_getter
    ):
        """ゲッターがない場合、デフォルト定数にフォールバック."""
        prompt = provider_without_getter._get_system_prompt()
        assert prompt == OPENAI_DEFAULT_PROMPT

    def test_get_system_prompt_fallback_on_error(
        self, config
    ):
        """ゲッターが例外を投げた場合、デフォルトにフォールバック."""

        def error_getter():
            raise Exception("DB接続エラー")

        provider = OpenAIProvider(
            config, system_prompt_getter=error_getter
        )
        prompt = provider._get_system_prompt()
        assert prompt == OPENAI_DEFAULT_PROMPT

    def test_analyze_uses_custom_prompt(
        self, provider_with_getter
    ):
        """analyze()がカスタムプロンプトを使用する."""
        provider_with_getter._client = MagicMock()
        provider_with_getter._initialized = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_msg = mock_response.choices[0].message
        mock_msg.content = (
            '{"title": "test", "content": "test",'
            ' "priority": "medium",'
            ' "confidence_score": 0.8}'
        )
        create_fn = (
            provider_with_getter._client
            .chat.completions.create
        )
        create_fn.return_value = mock_response

        request = AIAnalysisRequest(
            content="テスト",
            subject="件名",
            sender="送信者",
            source_type="test",
        )
        provider_with_getter.analyze(request)

        call_args = create_fn.call_args
        messages = call_args.kwargs.get(
            "messages", call_args[1].get("messages", [])
        )
        system_msg = messages[0]["content"]
        assert system_msg == "カスタム解析プロンプト"

    def test_analyze_uses_default_without_getter(
        self, provider_without_getter
    ):
        """ゲッターなしではデフォルトプロンプトを使用する."""
        provider_without_getter._client = MagicMock()
        provider_without_getter._initialized = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_msg = mock_response.choices[0].message
        mock_msg.content = (
            '{"title": "test", "content": "test",'
            ' "priority": "medium",'
            ' "confidence_score": 0.8}'
        )
        create_fn = (
            provider_without_getter._client
            .chat.completions.create
        )
        create_fn.return_value = mock_response

        request = AIAnalysisRequest(
            content="テスト",
            subject="件名",
            sender="送信者",
            source_type="test",
        )
        provider_without_getter.analyze(request)

        call_args = create_fn.call_args
        messages = call_args.kwargs.get(
            "messages", call_args[1].get("messages", [])
        )
        system_msg = messages[0]["content"]
        assert system_msg == OPENAI_DEFAULT_PROMPT


# =========================================================================
# Task 7.2: AnthropicProvider プロンプト統合
# =========================================================================


class TestAnthropicProviderPromptIntegration:
    """AnthropicProviderのプロンプト取得元統合テスト."""

    @pytest.fixture
    def config(self):
        """テスト用設定を作成する."""
        return AnthropicProviderConfig(
            api_key="sk-ant-test-key",
            model="claude-3-sonnet-20240229",
        )

    @pytest.fixture
    def custom_prompt_getter(self):
        """カスタムプロンプトゲッターを作成する."""
        return lambda: "カスタムAnthropic解析プロンプト"

    @pytest.fixture
    def provider_with_getter(self, config, custom_prompt_getter):
        """ゲッター付きプロバイダーを作成する."""
        return AnthropicProvider(
            config,
            system_prompt_getter=custom_prompt_getter,
        )

    @pytest.fixture
    def provider_without_getter(self, config):
        """ゲッターなしプロバイダーを作成する."""
        return AnthropicProvider(config)

    def test_accepts_system_prompt_getter(
        self, provider_with_getter
    ):
        """system_prompt_getterパラメータを受け取れる."""
        assert (
            provider_with_getter._system_prompt_getter
            is not None
        )

    def test_system_prompt_getter_defaults_to_none(
        self, provider_without_getter
    ):
        """system_prompt_getterはデフォルトでNone."""
        assert (
            provider_without_getter._system_prompt_getter
            is None
        )

    def test_get_system_prompt_uses_getter(
        self, provider_with_getter
    ):
        """ゲッターが設定されている場合、それを使用する."""
        prompt = provider_with_getter._get_system_prompt()
        assert prompt == "カスタムAnthropic解析プロンプト"

    def test_get_system_prompt_fallback_without_getter(
        self, provider_without_getter
    ):
        """ゲッターがない場合、デフォルト定数にフォールバック."""
        prompt = provider_without_getter._get_system_prompt()
        assert prompt == ANTHROPIC_DEFAULT_PROMPT

    def test_get_system_prompt_fallback_on_error(
        self, config
    ):
        """ゲッターが例外を投げた場合、デフォルトにフォールバック."""

        def error_getter():
            raise Exception("DB接続エラー")

        provider = AnthropicProvider(
            config, system_prompt_getter=error_getter
        )
        prompt = provider._get_system_prompt()
        assert prompt == ANTHROPIC_DEFAULT_PROMPT

    def test_analyze_uses_custom_prompt(
        self, provider_with_getter
    ):
        """analyze()がカスタムプロンプトを使用する."""
        provider_with_getter._client = MagicMock()
        provider_with_getter._initialized = True

        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = (
            '{"title": "test", "content": "test",'
            ' "priority": "medium",'
            ' "confidence_score": 0.8}'
        )
        mock_response.content = [mock_content]
        create_fn = (
            provider_with_getter._client.messages.create
        )
        create_fn.return_value = mock_response

        request = AIAnalysisRequest(
            content="テスト",
            subject="件名",
            sender="送信者",
            source_type="test",
        )
        provider_with_getter.analyze(request)

        call_args = create_fn.call_args
        system_arg = call_args.kwargs.get(
            "system", call_args[1].get("system", "")
        )
        assert system_arg == "カスタムAnthropic解析プロンプト"

    def test_analyze_uses_default_without_getter(
        self, provider_without_getter
    ):
        """ゲッターなしではデフォルトプロンプトを使用する."""
        provider_without_getter._client = MagicMock()
        provider_without_getter._initialized = True

        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = (
            '{"title": "test", "content": "test",'
            ' "priority": "medium",'
            ' "confidence_score": 0.8}'
        )
        mock_response.content = [mock_content]
        create_fn = (
            provider_without_getter._client.messages.create
        )
        create_fn.return_value = mock_response

        request = AIAnalysisRequest(
            content="テスト",
            subject="件名",
            sender="送信者",
            source_type="test",
        )
        provider_without_getter.analyze(request)

        call_args = create_fn.call_args
        system_arg = call_args.kwargs.get(
            "system", call_args[1].get("system", "")
        )
        assert system_arg == ANTHROPIC_DEFAULT_PROMPT


# =========================================================================
# プロンプト一元化の検証
# =========================================================================


class TestPromptUnification:
    """プロンプト一元化の検証テスト."""

    def test_openai_and_anthropic_default_prompts_match(
        self,
    ):
        """OpenAIとAnthropicのデフォルトプロンプトが同一."""
        assert OPENAI_DEFAULT_PROMPT == ANTHROPIC_DEFAULT_PROMPT

    def test_default_prompts_match_prompt_defaults(self):
        """デフォルトプロンプトがprompt_defaultsの定義と一致."""
        # _IMPORT_ANALYSIS_SYSTEM_CONTENT を単一のソース・オブ・トゥルースとし、
        # 各プロバイダのデフォルトプロンプトが完全一致することを検証する。
        assert (
            OPENAI_DEFAULT_PROMPT == ANTHROPIC_DEFAULT_PROMPT
        ), "OpenAI/Anthropic のデフォルトプロンプトは完全に一致する必要があります"

        # プロバイダが使用するデフォルトプロンプトは prompt_defaults の定義と
        # 完全に一致している必要がある。
        assert (
            OPENAI_DEFAULT_PROMPT == _IMPORT_ANALYSIS_SYSTEM_CONTENT
        ), "プロバイダのデフォルトプロンプトは prompt_defaults の内容と一致していません"

        # プロンプト内の JSON 例は有効な JSON となるように単一波括弧のみを使用する。
        assert "{{" not in _IMPORT_ANALYSIS_SYSTEM_CONTENT
        assert "}}" not in _IMPORT_ANALYSIS_SYSTEM_CONTENT

        # 重要な日本語フレーズが含まれていることを確認する。
        assert "問い合わせ解析の専門家" in _IMPORT_ANALYSIS_SYSTEM_CONTENT
