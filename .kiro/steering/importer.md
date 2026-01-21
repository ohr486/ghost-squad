---
inclusion: always
updated_at: 2026-01-22
---

# Importer機能 開発ガイドライン

Importer機能は外部データソースから問い合わせを自動取り込みし、AIで解析して構造化されたデータを生成する拡張可能なサブシステムです。

## アーキテクチャパターン

### ダブルプラグインアーキテクチャ

Importerは**データソース層**と**AIプロバイダー層**の二層拡張構造を採用。

```
ImporterService（統括）
    │
    ├── PluginRegistry ─── DataSourcePlugin（データソース層）
    │                        └── EmailPlugin, [将来: SentryPlugin, SlackPlugin]
    │
    └── AIProviderRegistry ─── AIProvider（AIプロバイダー層）
                                 └── OpenAIProvider, AnthropicProvider
```

**設計意図**: データソースとAI解析を独立して拡張可能にし、組み合わせの柔軟性を確保。

### Result型によるエラーハンドリング

Rust風のResult型パターンを採用し、例外に頼らないエラー伝播を実現。

```python
# services/importer/result.py
from services.importer.result import Result, BaseError

# 成功
Result.ok(value)

# 失敗
Result.err(BaseError(code="GS-301", message="エラーメッセージ"))

# 使用例
result = service.execute_import("email")
if result.is_ok:
    import_result = result.unwrap()
else:
    error = result.unwrap_err()
```

**メリット**: 呼び出し元でのエラーハンドリング強制、エラー情報の明示的な型付け。

## コンポーネント構成

### サービス層 (`services/importer/`)

| ファイル | 役割 | 契約 |
|---------|------|------|
| `importer_service.py` | インポート統括、問い合わせ生成 | プラグイン→解析→Inquiry作成 |
| `analysis_service.py` | AI解析統括、信頼度判定 | confidence < 0.8 → needs_review |
| `plugin_registry.py` | データソースプラグイン管理 | 同一plugin_type重複禁止 |
| `ai_provider_registry.py` | AIプロバイダー管理 | デフォルトは1つのみ |
| `importer_config_loader.py` | YAML設定読み込み、レジストリ初期化 | 環境変数展開対応 |
| `import_error_log_repository.py` | エラーログ永続化、統計 | 90日保持ポリシー |

### プラグイン基盤

```python
# 新しいデータソースプラグインの実装パターン
from services.importer.plugin_base import DataSourcePlugin, RawImportData

class NewPlugin(DataSourcePlugin[NewPluginConfig]):
    @property
    def plugin_type(self) -> str:
        return "new_source"  # 一意な識別子

    def validate_config(self, config: NewPluginConfig) -> ValidationResult: ...
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def fetch(self) -> List[RawImportData]: ...
    def mark_as_processed(self, source_id: str) -> None: ...
```

### AIプロバイダー基盤

```python
# 新しいAIプロバイダーの実装パターン
from services.importer.ai_provider_base import AIProvider, AIProviderType

class NewProvider(AIProvider[NewProviderConfig]):
    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.NEW  # 列挙型に追加必要

    @property
    def supported_models(self) -> List[str]: ...
    def validate_config(self, config: NewProviderConfig) -> ValidationResult: ...
    def initialize(self) -> None: ...
    def analyze(self, request: AIAnalysisRequest) -> Result[AIAnalysisResponse, AIProviderError]: ...
    def health_check(self) -> bool: ...
```

## 設定管理

### YAML設定ファイル (`config/importer_config.yaml`)

```yaml
plugins:
  email:
    enabled: true
    config:
      imap_server: ${IMAP_SERVER}  # 環境変数展開
      imap_port: 993
      username: ${IMAP_USERNAME}
      password: ${IMAP_PASSWORD}

ai_providers:
  default: openai
  providers:
    openai:
      enabled: true
      api_key: ${OPENAI_API_KEY}
      model: "gpt-4"
    anthropic:
      enabled: false
      api_key: ${ANTHROPIC_API_KEY}
      model: "claude-3-sonnet-20240229"
```

**設定読み込み**: `ImporterConfigLoader`がアプリ起動時にレジストリを初期化。

## エラーコード体系

| 範囲 | カテゴリ | 説明 |
|------|----------|------|
| GS-301〜GS-309 | プラグイン管理 | 未検出、初期化失敗、重複等 |
| GS-310〜GS-319 | メール設定 | 必須フィールド、ポート範囲等 |
| GS-320〜GS-329 | メール接続 | IMAP接続、認証、フォルダ不在等 |

## データモデル統合

### ImporterMetadata（inquiry_metadata内）

```python
# Inquiryのinquiry_metadataフィールドに格納
{
    "importer": {
        "source_type": "email",
        "source_id": "<message-id>",  # 重複検出キー
        "imported_at": "2026-01-22T10:00:00Z",
        "confidence_score": 0.85,
        "needs_review": false,
        "original_subject": "件名",
        "original_sender": "sender@example.com",
        "ai_provider": "openai",
        "ai_model": "gpt-4",
        "ai_generated_title": "AIが生成したタイトル",
        "ai_generated_priority": "medium"
    }
}
```

**重複検出**: `source_type + source_id`の組み合わせでGINインデックス検索。

## リトライ戦略

- **指数バックオフ**: 2^n秒、最大3回
- **連続エラー閾値**: 5件でアラートログ出力
- **手動リトライ**: `ImporterService.retry_failed()`でsource_ids指定

## テストパターン

```python
# AIプロバイダーのモックパターン
@pytest.fixture
def mock_ai_provider():
    provider = Mock(spec=AIProvider)
    provider.analyze.return_value = Result.ok(AIAnalysisResponse(...))
    return provider

# IMAPサーバーのモックパターン
@pytest.fixture
def mock_imap():
    with patch('imaplib.IMAP4_SSL') as mock:
        yield mock
```

## 拡張ガイドライン

### 新しいデータソース追加時

1. `DataSourcePlugin`を継承したクラスを作成
2. `plugin_type`プロパティで一意識別子を定義
3. 設定用データクラスを定義
4. `ImporterConfigLoader.SUPPORTED_PLUGINS`に追加
5. YAML設定スキーマを更新

### 新しいAIプロバイダー追加時

1. `AIProvider`を継承したクラスを作成
2. `AIProviderType`列挙型に値を追加
3. 設定用データクラスを定義
4. `ImporterConfigLoader.SUPPORTED_AI_PROVIDERS`に追加
5. YAML設定スキーマを更新

## 実装状況

- ✅ プラグイン基盤（DataSourcePlugin、PluginRegistry）
- ✅ AIプロバイダー基盤（AIProvider、AIProviderRegistry）
- ✅ EmailPlugin（IMAP接続、メール取得・解析）
- ✅ OpenAIProvider、AnthropicProvider
- ✅ ImporterAnalysisService（信頼度判定、needs_review）
- ✅ ImporterService（インポート実行、リトライ）
- ✅ ImporterConfigLoader（YAML設定、環境変数展開）
- ✅ ImportErrorLogRepository（エラーログ永続化）
- ✅ API層（`routers/importer.py`）
- 🚧 フロントエンドコンポーネント（Task 12-14）
