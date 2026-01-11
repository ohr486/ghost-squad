# Research & Design Decisions: Importer機能

---
**Purpose**: 技術設計を情報提供するための発見結果、アーキテクチャ調査、および根拠を記録する。
---

## Summary
- **Feature**: importer
- **Discovery Scope**: New Feature（プラグインアーキテクチャは新規、既存Inquiry APIとの統合あり）
- **Key Findings**:
  - 既存のStoryGenerationServiceのAI統合パターン（OpenAI、リトライ戦略）を再利用可能
  - Python標準ライブラリ（imaplib、email）でメール取り込みを実装可能
  - 既存のInquiry API（InquiryRepository）を直接利用して問い合わせを作成可能
  - プラグインアーキテクチャはAbstract Base Class（ABC）パターンで実装

## Research Log

### プラグインアーキテクチャパターン
- **Context**: 複数のデータソース（メール、Sentry、Slack等）に対応するプラグインシステムの設計
- **Sources Consulted**:
  - Python ABC（Abstract Base Class）ドキュメント
  - 既存のService層パターン（`api/services/`）
- **Findings**:
  - Python ABCを使用して共通インターフェースを定義
  - プラグインレジストリパターンで動的な登録・解除を実現
  - 各プラグインは独立したモジュールとして実装
- **Implications**:
  - `services/importer/plugins/base.py`に抽象基底クラスを定義
  - `services/importer/plugins/registry.py`でプラグイン管理

### メール取り込み技術選定
- **Context**: IMAP/POP3プロトコルによるメールサーバー接続
- **Sources Consulted**:
  - Python imaplibドキュメント
  - Python emailライブラリドキュメント
- **Findings**:
  - `imaplib`はPython標準ライブラリでIMAP4プロトコルをサポート
  - `email`パッケージでMIMEメッセージのパースが可能
  - SSL/TLS接続は`imaplib.IMAP4_SSL`で対応
  - Message-IDヘッダーで重複検出が可能
- **Implications**:
  - 追加の外部依存関係は不要
  - Message-IDベースの重複検出を採用

### AI統合パターン
- **Context**: 既存のOpenAI API統合パターンの再利用
- **Sources Consulted**:
  - `api/services/story_generation_service.py`
  - OpenAI API公式ドキュメント
- **Findings**:
  - StoryGenerationServiceのパターンを踏襲可能
  - リトライ戦略（指数バックオフ、3回リトライ）
  - 入力サニタイズ（最大文字数制限、制御文字除去）
  - JSON形式でのレスポンス解析
- **Implications**:
  - ImporterAnalysisServiceはStoryGenerationServiceと同様のパターンで実装
  - プロンプトのみ変更（問い合わせ解析用）

### 既存Inquiry APIとの統合
- **Context**: 問い合わせ自動生成時の既存API利用
- **Sources Consulted**:
  - `api/services/inquiry_repository.py`
  - `api/models/database/inquiry.py`
  - `api/models/schemas/inquiry.py`
- **Findings**:
  - `InquiryRepository.create()`で問い合わせ作成
  - `inquiry_metadata` JSONフィールドでインポート情報を格納
  - `CreateInquiryData`スキーマを使用
- **Implications**:
  - 新規データモデルは不要（既存Inquiryモデルを使用）
  - メタデータ拡張のみで対応

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Option A: 既存拡張 | 既存Service層に追加 | 学習コスト低、即時活用 | 将来の拡張性が限定的 | MVPには適するが長期的に不向き |
| Option B: 新規作成 | プラグインアーキテクチャ新規構築 | 明確な責務分離、拡張容易 | 初期コストやや高 | **推奨**: 要件に最適 |
| Option C: ハイブリッド | 段階的な実装 | リスク軽減、早期FB | フェーズ間整合性管理 | 中規模チーム向け |

**選択**: Option B（新規コンポーネント作成）
- プラグインアーキテクチャの要件に最適
- 将来のデータソース追加（Sentry、Slack等）を考慮
- 既存コードへの影響を最小化

## Design Decisions

### Decision: プラグインインターフェース設計
- **Context**: 複数のデータソースに対応する共通インターフェースが必要
- **Alternatives Considered**:
  1. 単純な関数ベースのプラグイン
  2. ABC（Abstract Base Class）ベースのクラス設計
- **Selected Approach**: ABCベースのクラス設計
- **Rationale**: 型安全性、IDE補完、テスト容易性
- **Trade-offs**: やや複雑だが、拡張性と保守性が向上
- **Follow-up**: 各プラグインの設定スキーマ定義

### Decision: 重複検出方式
- **Context**: 同一メールの重複取り込みを防止
- **Alternatives Considered**:
  1. Message-IDヘッダーベース
  2. コンテンツハッシュベース
  3. 複合キー（Message-ID + 送信者 + 日時）
- **Selected Approach**: Message-IDヘッダーベース
- **Rationale**: RFC標準に準拠、一意性が保証される
- **Trade-offs**: Message-IDがないメールは処理対象外
- **Follow-up**: inquiry_metadataにsource_idとして格納

### Decision: エラーコード範囲
- **Context**: 既存エラーコード体系（GS-xxx）の拡張
- **Alternatives Considered**:
  1. 新しい接頭辞（IMP-xxx）
  2. 既存体系の拡張（GS-3xx）
- **Selected Approach**: GS-301〜GS-399の範囲を使用
- **Rationale**: 既存体系との一貫性
- **Trade-offs**: なし
- **Follow-up**: エラーコード一覧のドキュメント化

## Risks & Mitigations
- **Risk 1: メールサーバー接続の不安定性** — リトライ戦略（指数バックオフ）で対応、接続タイムアウト設定
- **Risk 2: AI解析精度のばらつき** — 信頼度スコアを導入し、低スコア時はレビューフラグを設定
- **Risk 3: 大量メール取り込み時の負荷** — バッチサイズ制限、処理間隔設定で対応

## References
- [Python imaplib ドキュメント](https://docs.python.org/3/library/imaplib.html) — IMAP4プロトコル実装
- [Python email パッケージ](https://docs.python.org/3/library/email.html) — MIMEメッセージ処理
- [OpenAI API ドキュメント](https://platform.openai.com/docs/api-reference) — GPT-4 API統合
- [RFC 5322 Message-ID](https://datatracker.ietf.org/doc/html/rfc5322#section-3.6.4) — メッセージID標準
