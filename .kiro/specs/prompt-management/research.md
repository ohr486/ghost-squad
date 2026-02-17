# Research & Design Decisions

---
**Purpose**: prompt-management機能のディスカバリー結果と設計判断の根拠を記録する。
---

## Summary
- **Feature**: `prompt-management`
- **Discovery Scope**: Extension（既存システムの拡張 — 既存パターンに準拠した新規コンポーネント群）
- **Key Findings**:
  - システム内に3箇所・5つのハードコードされたプロンプトが存在し、OpenAI/Anthropicプロバイダーで同一プロンプトが重複コピーされている
  - 既存のレイヤードアーキテクチャ（Router → Service → Repository → Model）を完全に踏襲可能
  - デフォルトプロンプトの初期投入はアプリ起動時lifespan処理で実現可能（Importerと同様のパターン）

## Research Log

### ハードコードされたプロンプトの分析
- **Context**: 管理対象となるプロンプトの特定と構造分析
- **Sources Consulted**: `story_generation_service.py`, `openai_provider.py`, `anthropic_provider.py`
- **Findings**:
  - **ストーリー生成**: システムプロンプト（role: system）+ ユーザープロンプト（テンプレート変数: `{inquiry_content}`）
  - **インポート解析**: システムプロンプト `ANALYSIS_SYSTEM_PROMPT`（両プロバイダーで重複）+ ユーザープロンプト `_build_user_prompt`（変数: `{subject}`, `{sender}`, `{source_type}`, `{content}`）
  - プロンプトの変数はPython f-string形式（`{variable_name}`）で統一されている
- **Implications**: プロンプトキーとして `story_generation_system`, `story_generation_user`, `import_analysis_system`, `import_analysis_user` の4つを初期デフォルトとして登録する

### 編集ロック方式の検討
- **Context**: Req 2.5「編集中であることを他の管理者に表示」の実現方式
- **Sources Consulted**: 既存コードベースのパターン分析
- **Findings**:
  - 現時点では認証・ユーザー管理が未実装（将来実装予定）
  - 悲観的ロック（DB行ロック）はセッション管理が複雑
  - **アドバイザリーロック方式**: `editing_by`（ユーザーID）+ `editing_since`（タイムスタンプ）フィールドで簡易実装可能
  - タイムアウト（例: 30分）で自動解除すれば、ブラウザクローズ時の孤立ロックを防止
- **Implications**: 厳密な排他制御ではなくアドバイザリー（助言的）なロックとし、警告表示のみで編集自体はブロックしない

### デフォルトプロンプト初期投入方式
- **Context**: Req 4.1「システム初回起動時にデフォルトプロンプトを自動登録」
- **Sources Consulted**: `main.py` lifespan処理、Alembicマイグレーション
- **Findings**:
  - Alembicマイグレーションでの投入: スキーマ変更と同時にデータ投入可能だが、プロンプト内容変更時にマイグレーション追加が必要
  - **lifespan初期化パターン**: `main.py`のlifespan処理でImporterConfigLoaderと同様に初期化可能。起動時にDBを確認し、未登録のデフォルトプロンプトのみ挿入する冪等性のある設計
  - Pythonコード内の定数としてデフォルト値を定義し、DBの`default_content`カラムにも保持
- **Implications**: lifespan初期化パターンを採用。デフォルト値はPython定数 → DB `default_content` に保持し、コードとDBの両方から参照可能

### テスト実行のAIプロバイダー選択
- **Context**: Req 3「プロンプトテスト・プレビュー」で使用するAIプロバイダー
- **Sources Consulted**: 既存AI統合パターン（StoryGenerationService, AIProviderRegistry）
- **Findings**:
  - StoryGenerationServiceはOpenAI固定、ImporterはAIProviderRegistryでプロバイダー選択可能
  - テスト実行はプロンプトの動作確認が目的であり、プロバイダー選択は二次的
  - **OpenAI固定（StoryGenerationServiceのクライアント再利用）**が最もシンプル
- **Implications**: テスト実行APIはOpenAI APIを使用。将来的にプロバイダー選択パラメータを追加可能

### キャッシュ戦略
- **Context**: Req 5.5「DB接続喪失時のインメモリキャッシュフォールバック」
- **Sources Consulted**: 既存コードベース（キャッシュ実装なし）
- **Findings**:
  - 現時点ではRedis等の外部キャッシュは導入されていない
  - プロンプト数は少数（初期4件、最大でも数十件）のため、Python辞書によるインメモリキャッシュで十分
  - Write-throughパターン: 更新時にDBとキャッシュを同時更新
- **Implications**: `Dict[str, PromptCacheEntry]`によるシンプルなインメモリキャッシュを実装。TTLは不要（更新時にキャッシュクリア）

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| レイヤードアーキテクチャ（採用） | Router → Service → Repository → Model | 既存パターンと完全一致、実装コスト低 | 特になし | Inquiry/Story/Importerと同一構造 |
| イベント駆動 | プロンプト更新時にイベント発行 | 疎結合、リアルタイム反映 | 過剰設計、メッセージングインフラ不在 | 将来的な拡張として検討可能 |

## Design Decisions

### Decision: デフォルトプロンプトの保持方式
- **Context**: デフォルト値をどこに保持し、リセット時にどう参照するか
- **Alternatives Considered**:
  1. DBの`default_content`カラムに保持（更新不可）
  2. Pythonコード内の定数のみ（DBには保持しない）
  3. 外部YAMLファイルで管理
- **Selected Approach**: Option 1 — DBの`default_content`カラム + Pythonコード定数の併用
- **Rationale**: DB内に保持することでAPIから直接デフォルト値を返却可能。Python定数はシード投入時のソースとして使用
- **Trade-offs**: DBカラム追加のコストは最小。デフォルト値の変更時はコード変更 + マイグレーション or シード再実行が必要
- **Follow-up**: `default_content`カラムへの直接UPDATE防止（アプリレベルで制御）

### Decision: 編集ロック方式
- **Context**: 複数管理者の同時編集制御
- **Alternatives Considered**:
  1. 悲観的ロック（DB行ロック）
  2. 楽観的ロック（updated_at比較）
  3. アドバイザリーロック（editing_by + editing_since）
- **Selected Approach**: Option 3 — アドバイザリーロック
- **Rationale**: ユーザー認証が未実装の現段階では、簡易的な警告表示で十分。編集開始時にフィールドを設定し、30分経過で自動解除
- **Trade-offs**: 厳密な排他制御ではないが、実装コストが低く要件を満たす
- **Follow-up**: 認証実装後に`editing_by`を実際のユーザーIDに置換

### Decision: プロンプト取得のキャッシュ戦略
- **Context**: サービス層からのプロンプト取得パフォーマンスとDB障害時のフォールバック
- **Alternatives Considered**:
  1. Redis外部キャッシュ
  2. Pythonインメモリ辞書
  3. キャッシュなし（毎回DB読み取り）
- **Selected Approach**: Option 2 — Pythonインメモリ辞書
- **Rationale**: プロンプト数が少数のため外部キャッシュは過剰。インメモリ辞書でDB障害時フォールバック要件（5.5）も満たせる
- **Trade-offs**: マルチプロセス時にキャッシュが分散するが、現在のUvicorn単一プロセス構成では問題なし
- **Follow-up**: スケールアウト時にRedis導入を検討

## Risks & Mitigations
- **既存サービス改修の影響範囲**: StoryGenerationService、OpenAIProvider、AnthropicProviderの3サービスを改修 → 改修は限定的（プロンプト取得元の変更のみ）、既存テストで回帰検証
- **DB障害時のキャッシュ一貫性**: キャッシュが古い可能性 → プロンプト更新頻度は低いため実用上問題なし。ログで警告出力
- **アドバイザリーロックの孤立**: ブラウザクローズで解除されない → 30分タイムアウトで自動解除

## References
- Ghost Squad既存アーキテクチャ: `.kiro/steering/structure.md`, `.kiro/steering/tech.md`
- 既存プロンプト: `api/services/story_generation_service.py`, `api/services/importer/openai_provider.py`, `api/services/importer/anthropic_provider.py`
