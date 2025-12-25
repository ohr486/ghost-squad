# ストーリーボード機能 研究・設計決定ログ

## 概要

- **機能**: storyboard
- **Discoveryスコープ**: Complex Integration（AI統合を含む既存システム拡張）
- **主要な発見事項**:
  - OpenAI API統合には構造化出力とリトライ戦略が必須
  - python-statemachine ライブラリが承認ワークフローに最適
  - TanStack Query v5 の無限スクロール機能がページネーションに適合

## 研究ログ

### OpenAI API統合パターン

- **コンテキスト**: 問い合わせからストーリーへの自動変換にAIを利用する必要がある
- **調査ソース**:
  - [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
  - [Best practices for prompt engineering with the OpenAI API](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api)
  - [Prompt Engineering Guide 2025](https://www.lakera.ai/blog/prompt-engineering-guide)

- **発見事項**:
  - **構造化出力**: GPT-4以降のモデルは`response_format`パラメータでJSON Schemaベースの構造化出力をサポート
  - **Pydanticとの統合**: OpenAI Python SDKは[Pydantic v2モデルを直接サポート](https://docs.pydantic.dev/latest/concepts/json_schema/)し、自動的にJSON Schemaを生成
  - **プロンプト戦略**: 明示的な指示、Few-shot例、出力フォーマット指定が重要
  - **モデル固定**: 本番環境では特定のモデルスナップショット（例: `gpt-4-turbo-2024-04-09`）を使用し、一貫性を確保すべき
  - **メタプロンプト**: Playgroundの「Generate」機能でタスク説明からプロンプトを自動生成可能

- **アーキテクチャへの影響**:
  - サービス層に`AIService`クラスを作成し、プロンプト管理と応答パース処理を集約
  - Pydantic Response Modelで構造化出力を定義（`StoryGenerationResponse`）
  - エラーハンドリングとリトライロジックを組み込む必要あり

### レート制限とリトライ戦略

- **コンテキスト**: OpenAI APIのレート制限を適切に処理しシステムの信頼性を確保
- **調査ソース**:
  - [OpenAI Rate Limits Guide](https://platform.openai.com/docs/guides/rate-limits)
  - [How to handle rate limits - OpenAI Cookbook](https://cookbook.openai.com/examples/how_to_handle_rate_limits)
  - [Tenacity retry implementation examples](https://www.restack.io/p/openai-python-answer-retry-implementation-cat-ai)

- **発見事項**:
  - **推奨ライブラリ**: OpenAI公式が`tenacity`ライブラリを推奨
  - **リトライパターン**: Exponential backoff with jitter（1-60秒の待機時間、最大6回リトライ）
  - **対象エラー**: `RateLimitError`, `APIError`, `Timeout`
  - **公式サンプルコード**:
    ```python
    from tenacity import retry, stop_after_attempt, wait_random_exponential

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6)
    )
    def completion_with_backoff(**kwargs):
        return client.completions.create(**kwargs)
    ```
  - **重要な注意点**: 失敗したリクエストもレート制限にカウントされるため、単純な再送信は効果なし

- **アーキテクチャへの影響**:
  - `requirements.txt`に`tenacity`を追加（バージョン: 最新の8.x系）
  - `AIService`クラスの全OpenAI API呼び出しにデコレータ適用
  - エラーログとメトリクス記録を統合し、レート制限の監視を実現

### Pydantic構造化バリデーション

- **コンテキスト**: AI応答の構造検証と型安全性を確保
- **調査ソース**:
  - [Structured Outputs - OpenAI API](https://platform.openai.com/docs/guides/structured-outputs)
  - [Pydantic validation with OpenAI](https://pydantic.dev/articles/llm-intro)
  - [JSON Schema Production Guide](https://superjson.ai/blog/2025-08-24-json-schema-validation-python-pydantic-guide/)

- **発見事項**:
  - **互換性の課題**: Pydantic v2とOpenAIのJSON Schema実装には微妙な差異が存在（特に`Optional`フィールドのデフォルト値）
  - **推奨アプローチ**: OpenAI SDKのネイティブPydanticサポートを使用し、型定義とJSON Schemaの乖離を防ぐ
  - **ネストされた構造**: Pydanticは複雑なネスト構造をサポートし、リスト、辞書、カスタムオブジェクトを処理可能
  - **パフォーマンス**: FastAPI、LangChain、466,400以上のGitHubリポジトリで採用され、実績あり

- **アーキテクチャへの影響**:
  - `backend/models/ai/` ディレクトリにAI応答用のPydanticモデルを作成
  - `StoryGenerationResponse`モデルで`title`, `description`, `acceptance_criteria`, `category`, `priority`, `estimated_effort`を定義
  - バリデーションエラー時の詳細なエラーメッセージ生成

### ステートマシン実装パターン

- **コンテキスト**: 問い合わせの承認・却下ワークフローでステータス遷移ルールを管理
- **調査ソース**:
  - [python-statemachine Documentation](https://python-statemachine.readthedocs.io/en/latest/readme.html)
  - [Building State-Aware Applications with FSM and FastAPI](https://medium.com/@tech-adventurer/building-state-aware-applications-with-finite-state-machines-and-fastapi-11d9b2894f3a)
  - [Approval Workflow with FastAPI](https://medium.com/@asc686f61/building-an-approval-workflow-with-slack-fastapi-redis-and-ngrok-895d4d9319f2)

- **発見事項**:
  - **python-statemachine ライブラリ**: 宣言的APIで状態遷移を定義、asyncio完全サポート
  - **コールバックパターン**: `before_[event]`, `on_enter_[state]`, `on_exit_[state]`, `after_[event]`で拡張可能
  - **FastAPI統合**: 依存性注入パターンで状態マシンをエンドポイントに組み込み可能
  - **グラフ検証**: コンパイル時に状態マシングラフの正しさを検証（単一初期状態、到達可能性など）
  - **ドメインモデル統合**: Mixinパターンで既存モデルに状態マシンを埋め込み可能

- **アーキテクチャへの影響**:
  - `backend/services/workflow_service.py`に`InquiryStateMachine`クラスを実装
  - 状態: `RECEIVED`, `APPROVED`, `REJECTED`, `PROCESSING`, `COMPLETED`, `FAILED`
  - イベント: `approve`, `reject`, `start_conversion`, `complete`, `fail`
  - `inquiry_metadata`に遷移履歴（タイムスタンプ、実行者）を記録

### React TanStack Query ページネーション

- **コンテキスト**: 問い合わせとストーリーの一覧表示で無限スクロールを実装
- **調査ソース**:
  - [TanStack Query Infinite Queries Guide](https://tanstack.com/query/latest/docs/framework/react/guides/infinite-queries)
  - [Infinite Scroll with React 19](https://makersden.io/blog/infinite-scroll-streaming-data-tanstack-query-react19)
  - [Caching, Pagination, and Infinite Scrolling](https://medium.com/@lakshaykapoor08/%EF%B8%8F-caching-pagination-and-infinite-scrolling-with-tanstack-query-4212b24d3806)

- **発見事項**:
  - **useInfiniteQuery**: 無限スクロール専用フック、`getNextPageParam`と`getPreviousPageParam`で追加データ取得を管理
  - **Refetchロジック**: ステールデータのリフェッチ時、最初のグループから順次取得し、カーソル整合性を保証
  - **React 19統合**: Concurrent Renderingで非ブロッキングUI更新を実現、React 19ではさらにスムーズに
  - **メモリ管理**: Windowingテクニック（近隣ページのみ状態保持）で無制限メモリ成長を防止
  - **Intersection Observer**: スクロール検知と自動フェッチトリガーに最適

- **アーキテクチャへの影響**:
  - `frontend/src/hooks/useInfiniteInquiries.ts`カスタムフックを作成
  - `limit`/`offset`ベースのページネーション（バックエンドAPI仕様に合致）
  - `hasNextPage`と`fetchNextPage`でUI制御
  - Intersection Observerでスクロール末尾の自動ロード

## アーキテクチャパターン評価

| オプション | 説明 | 強み | リスク / 制約 | 備考 |
|-----------|------|------|--------------|------|
| **レイヤードアーキテクチャ（既存）** | API層 → サービス層 → リポジトリ層 → モデル層 | 既存システムと一貫、チーム習熟度高い | サービス層が未実装で新規作成必要 | 推奨：既存パターン踏襲 |
| **ヘキサゴナル（ポート＆アダプター）** | ドメイン中心、外部依存を抽象化 | AI統合の分離が明確、テスト容易 | 実装コスト高、既存との整合性課題 | AI統合部分のみ適用検討 |
| **イベント駆動** | ストーリー生成をイベントで非同期処理 | スケーラビリティ高、疎結合 | 複雑性増大、デバッグ困難 | 将来拡張として保留 |

**選定パターン**: **レイヤードアーキテクチャ（サービス層追加）**

## 設計決定

### 決定1: OpenAI APIモデル選択

- **コンテキスト**: ストーリー生成の品質とコストのバランス
- **検討した選択肢**:
  1. **GPT-4 Turbo** (`gpt-4-turbo-2024-04-09`) - 高品質、高コスト
  2. **GPT-4o** (`gpt-4o-2024-08-06`) - バランス型、構造化出力最適化
  3. **GPT-3.5 Turbo** - 低コスト、品質劣る

- **選択したアプローチ**: **GPT-4o** (`gpt-4o-2024-08-06`)

- **根拠**:
  - 構造化出力のネイティブサポート（`response_format`パラメータ）
  - コストパフォーマンス良好（GPT-4 Turboの1/2のコスト）
  - ストーリー生成タスクに十分な精度
  - OpenAI公式推奨（2024年8月リリース、最新モデル）

- **トレードオフ**:
  - ✅ 品質とコストのバランス
  - ✅ 構造化出力の信頼性
  - ❌ GPT-4 Turboより若干精度低下の可能性（実測で検証必要）

- **フォローアップ**:
  - 実装後、生成品質の評価を実施
  - 必要に応じてGPT-4 Turboへのアップグレード検討
  - プロンプトテンプレートのA/Bテストで最適化

### 決定2: ステートマシンライブラリ選択

- **コンテキスト**: 問い合わせワークフローのステータス遷移管理
- **検討した選択肢**:
  1. **python-statemachine** - 宣言的、asyncサポート、グラフ検証
  2. **transitions** - 柔軟、PyPI人気高い
  3. **カスタム実装** - 完全制御、依存なし

- **選択したアプローチ**: **python-statemachine** (v2.5.0+)

- **根拠**:
  - FastAPIとの統合実績あり
  - Async/awaitネイティブサポート
  - コンパイル時グラフ検証でバグ早期発見
  - コールバックパターンが拡張性高い

- **トレードオフ**:
  - ✅ 宣言的でコード可読性向上
  - ✅ 既存コミュニティとドキュメント充実
  - ❌ 新規依存関係追加（軽量ライブラリだが）

- **フォローアップ**:
  - `requirements.txt`に追加
  - 状態遷移図をMermaidで文書化
  - 不正遷移のテストケース作成

### 決定3: プロンプト管理方法

- **コンテキスト**: ストーリー生成プロンプトの保守性と柔軟性
- **検討した選択肢**:
  1. **コード内ハードコード** - シンプル、バージョン管理容易
  2. **データベース管理** - 動的更新可能、UI編集可能
  3. **設定ファイル（YAML/JSON）** - コードと分離、環境別管理

- **選択したアプローチ**: **コード内ハードコード（初期実装）** → **データベース管理（将来）**

- **根拠**:
  - MVP段階ではプロンプト変更頻度低い
  - Gitでプロンプト履歴管理が有益
  - 将来的にStoryTemplateModelを活用した動的管理に移行可能

- **トレードオフ**:
  - ✅ 初期実装コスト最小
  - ✅ バージョン管理とコードレビュー可能
  - ❌ プロンプト変更時にデプロイ必要

- **フォローアップ**:
  - `backend/services/prompts.py`にプロンプトテンプレートを定義
  - テンプレート変数（`{inquiry_content}`, `{template_hint}`）を設計
  - 将来的にDB移行時のマイグレーションパス検討

### 決定4: フロントエンド状態管理戦略

- **コンテキスト**: サーバーデータとUI状態の管理
- **検討した選択肢**:
  1. **TanStack Query単独** - サーバー状態専用
  2. **Redux + TanStack Query** - グローバル状態 + サーバー状態
  3. **Zustand + TanStack Query** - 軽量グローバル状態 + サーバー状態

- **選択したアプローチ**: **TanStack Query単独**

- **根拠**:
  - 現在のアプリはサーバー状態が支配的（問い合わせ、ストーリー）
  - グローバルクライアント状態が最小限（ダークモード程度）
  - 既にプロジェクトに統合済み（追加依存なし）

- **トレードオフ**:
  - ✅ シンプル、学習曲線緩やか
  - ✅ キャッシュ戦略自動化
  - ❌ 複雑なクライアント状態には不向き（将来拡張時に再評価）

- **フォローアップ**:
  - キャッシュ戦略設定（`staleTime`, `cacheTime`）
  - 楽観的更新（Optimistic Updates）の適用範囲決定
  - グローバル状態が必要になった時点でZustand導入検討

## リスクと対応策

| リスク | 影響度 | 確率 | 対応策 |
|--------|--------|------|--------|
| **OpenAI API応答品質の変動** | High | Medium | プロンプトテンプレートのA/Bテスト、Few-shot例の充実、フォールバック処理 |
| **レート制限によるサービス停止** | High | Low | Tenacityリトライ、使用量モニタリング、エラー通知、段階的スケールアップ |
| **ステータス遷移ルールの複雑化** | Medium | Medium | FSMグラフ可視化、包括的テストスイート、ドキュメント整備 |
| **無限スクロールのメモリリーク** | Medium | Low | Windowing実装、ページ上限設定、定期的なクリーンアップ |
| **Pydantic検証の互換性問題** | Low | Medium | OpenAI SDKネイティブサポート使用、検証エラーの詳細ログ |

## 参考文献

### OpenAI関連
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Best practices for prompt engineering with the OpenAI API](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api)
- [The Ultimate Guide to Prompt Engineering in 2025](https://www.lakera.ai/blog/prompt-engineering-guide)
- [OpenAI Rate Limits Guide](https://platform.openai.com/docs/guides/rate-limits)
- [How to handle rate limits - OpenAI Cookbook](https://cookbook.openai.com/examples/how_to_handle_rate_limits)
- [Structured Outputs - OpenAI API](https://platform.openai.com/docs/guides/structured-outputs)

### Pydantic & Python
- [Pydantic validation with OpenAI](https://pydantic.dev/articles/llm-intro)
- [Pydantic JSON Schema Documentation](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [JSON Schema Production Guide](https://superjson.ai/blog/2025-08-24-json-schema-validation-python-pydantic-guide/)

### State Machine
- [python-statemachine Documentation](https://python-statemachine.readthedocs.io/en/latest/readme.html)
- [python-statemachine PyPI](https://pypi.org/project/python-statemachine/)
- [Building State-Aware Applications with FSM and FastAPI](https://medium.com/@tech-adventurer/building-state-aware-applications-with-finite-state-machines-and-fastapi-11d9b2894f3a)
- [Approval Workflow with FastAPI](https://medium.com/@asc686f61/building-an-approval-workflow-with-slack-fastapi-redis-and-ngrok-895d4d9319f2)

### React & TanStack Query
- [TanStack Query Infinite Queries Guide](https://tanstack.com/query/latest/docs/framework/react/guides/infinite-queries)
- [Infinite Scroll with React 19](https://makersden.io/blog/infinite-scroll-streaming-data-tanstack-query-react19)
- [Caching, Pagination, and Infinite Scrolling with TanStack Query](https://medium.com/@lakshaykapoor08/%EF%B8%8F-caching-pagination-and-infinite-scrolling-with-tanstack-query-4212b24d3806)
- [TanStack Query Load More Example](https://tanstack.com/query/latest/docs/framework/react/examples/load-more-infinite-scroll)
