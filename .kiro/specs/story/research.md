# ストーリー管理機能 調査・設計決定ドキュメント

## 概要
- **機能**: story
- **発見スコープ**: Extension（既存Inquiryシステムの拡張）
- **主要な発見事項**:
  - 既存Inquiry機能の完全実装により、同様のアーキテクチャパターンを適用可能
  - Repository + Service層の分離パターンが確立されており、Story機能でも同様のレイヤー構造を採用
  - OpenAI API統合が必要な新規外部依存関係として識別

## 調査ログ

### 既存システムアーキテクチャ分析
- **コンテキスト**: Story機能はInquiry機能に依存するため、既存アーキテクチャパターンの理解が必要
- **調査対象**:
  - `api/models/database/inquiry.py` - InquiryModel（SQLAlchemy ORM）
  - `api/models/schemas/inquiry.py` - Pydanticスキーマ（API層）
  - `api/services/inquiry_repository.py` - データアクセス層
  - `api/services/inquiry_workflow_service.py` - ワークフロー管理
  - `.kiro/specs/inquiry/design.md` - Inquiry設計書
- **発見事項**:
  - レイヤー構造: API層 → サービス層（Validator/Repository/Query/Workflow） → データアクセス層
  - BaseModel継承によるID、created_at、updated_atの共通フィールド管理
  - Pydantic 2.x使用（CreateRequest、UpdateRequest、Responseの分離パターン）
  - InquiryStatusはEnum型で管理、JSON metadataフィールドで拡張情報を保持
  - ステータス遷移ロジックはWorkflowServiceで集中管理
- **影響**:
  - Story機能も同様のレイヤー構造を採用（StoryRepository、StoryValidator、StoryWorkflowService）
  - StoryModelはBaseModelを継承し、inquiry_idを外部キーとして持つ
  - StoryStatus（pending_review/approved/rejected）、Priority（low/medium/high/urgent）をEnum管理
  - AI生成ロジックは新規StoryGenerationServiceとして分離

### OpenAI API統合調査
- **コンテキスト**: 要件1（AI変換）実現のため、OpenAI APIの統合方法を検証
- **調査対象**:
  - プロジェクト既存依存関係（`api/requirements.txt`）- OpenAI API 1.3.7使用
  - `.kiro/steering/tech.md` - AI統合ガイドライン
  - `.kiro/steering/product.md` - AI品質保証要件
- **発見事項**:
  - 既にOpenAI API 1.3.7が依存関係として定義済み
  - プロンプト構造化パターンが定義済み（STORY_GENERATION_PROMPT）
  - リトライ戦略の実装ガイドライン存在（`@retry`デコレータ、3回リトライ、指数バックオフ）
  - 生成結果の構造検証、不適切コンテンツフィルタリング、タイムアウト設定が必要
- **影響**:
  - StoryGenerationServiceでOpenAI API呼び出しをカプセル化
  - プロンプトテンプレート管理を独立化
  - AI生成結果のバリデーション層を実装（必須フィールドチェック、500文字制限検証）
  - エラー時のリトライ処理とタイムアウト処理を実装

### データモデル設計分析
- **コンテキスト**: Story要件4（データモデル）を実現するためのスキーマ設計
- **調査対象**:
  - 要件4の受入基準（1-13）
  - `.kiro/steering/product.md` - ドメインモデル定義
- **発見事項**:
  - Story固有フィールド: title（最大500文字）、description、priority、estimated_effort、deadline、assignee、tags、dependencies
  - inquiry_idはオプショナル（AI生成ストーリーは持つが、手動作成ストーリーは持たない）
  - story_metadataでJSON形式の拡張情報を保持（承認・却下情報、ステータス履歴）
  - 外部キー制約でInquiryとの参照整合性を保証
- **影響**:
  - StoryModelにinquiry_id（nullable=True）を定義
  - titleにCheckConstraint（500文字制限）を設定
  - priorityとstatusはEnum型で型安全性を保証
  - Alembicマイグレーションで外部キー制約とインデックスを設定

### UI要件分析
- **コンテキスト**: 要件5（Web UI）を実現するためのフロントエンド設計
- **調査対象**:
  - `.kiro/steering/implementation-status.md` - フロントエンド実装状況
  - 既存InquiryForm、InquiryList、InquiryDetailコンポーネント
- **発見事項**:
  - React Hook Form + Zod バリデーションパターンが確立
  - TanStack React Query 5.8.4でサーバー状態管理
  - Axiosクライアント（30秒タイムアウト、エラーインターセプター）
  - ページネーション、フィルタリング、ソートの共通UIパターン存在
- **影響**:
  - StoryForm、StoryList、StoryDetailコンポーネントを既存パターンに沿って実装
  - TypeScript型定義（StoryResponse、CreateStoryRequest、UpdateStoryRequest）をバックエンドスキーマと同期
  - storyApi.tsでAxiosクライアント実装
  - 既存UI/UXパターンを再利用（ローディング表示、エラートースト、モーダルダイアログ）

## アーキテクチャパターン評価

| オプション | 説明 | 強み | リスク/制限 | 備考 |
|-----------|------|------|------------|------|
| Repository + Service分離 | InquiryリポジトリパターンをStoryにも適用 | 明確な境界、テスト容易性、既存パターンとの一貫性 | レイヤー数の増加 | **選択**。既存アーキテクチャとの整合性が最優先 |
| AI統合をServiceとして分離 | StoryGenerationServiceを独立コンポーネント化 | 責任の分離、モックテストの容易性、AI提供者の切り替えやすさ | サービス数の増加 | **選択**。要件1.10（複数AIプロバイダー対応）を満たす |
| Inquiryとの結合度 | 疎結合（外部キー参照のみ） | Inquiryの変更がStoryに波及しない | inquiry_id nullableの複雑性 | **選択**。要件2.14（手動作成ストーリーはinquiry不要）に対応 |

## 設計決定

### 決定: レイヤー構造とコンポーネント分離
- **コンテキスト**: Story機能の責任範囲と既存システムとの統合方法
- **検討した代替案**:
  1. すべてのロジックをStoryServiceに集約 - シンプルだが責任過多
  2. Repository + Validator + Workflow + Generation分離 - 既存パターンに整合
- **選択したアプローチ**: Repository + Service層の分離（Inquiry機能と同様）
  - StoryRepository: CRUD、フィルタリング、ソート、ページネーション
  - StoryValidator: 入力検証、ビジネスルール検証
  - StoryWorkflowService: ステータス遷移管理（pending_review → approved/rejected）
  - StoryGenerationService: AI変換ロジック（OpenAI API呼び出し、プロンプト管理、リトライ）
- **理由**: 既存アーキテクチャとの一貫性、責任の明確化、テスト容易性の確保
- **トレードオフ**: レイヤー数増加によるボイラープレートの増加 vs 保守性・拡張性の向上
- **フォローアップ**: 実装時にStoryGenerationServiceのモックテストを優先実装

### 決定: AI生成ストーリーの検証戦略
- **コンテキスト**: 要件1.8（生成ストーリーの構造検証）と要件1.9（タイトル500文字制限）
- **検討した代替案**:
  1. OpenAI APIレスポンスをそのまま保存 - 検証なし、品質リスク高
  2. Pydanticスキーマで検証 - 型安全性、明示的エラー処理
  3. カスタムバリデータ実装 - 柔軟だが複雑
- **選択したアプローチ**: Pydanticスキーマ（GeneratedStorySchema）で検証
  - 必須フィールド: title、description、priority
  - タイトル: 最大500文字制限
  - 優先度: Enum型による値検証
  - 受入基準: オプショナルフィールド（リスト形式）
- **理由**: Pydantic 2.xの強力なバリデーション機能、型安全性、エラーメッセージの標準化
- **トレードオフ**: スキーマ定義の手間 vs 実行時エラーの削減
- **フォローアップ**: AI生成結果が検証失敗した場合のフォールバック戦略を実装フェーズで決定

### 決定: ストーリーとInquiryの関連性管理
- **コンテキスト**: 要件4.3（inquiry_idオプショナル）と要件2.14（手動作成）の両立
- **検討した代替案**:
  1. inquiry_id必須 - シンプルだが手動作成不可
  2. inquiry_id nullable + 外部キー制約 - 柔軟性とデータ整合性の両立
  3. 別テーブルで関連管理 - 複雑、オーバーエンジニアリング
- **選択したアプローチ**: inquiry_id nullable + 外部キー制約
  - StoryModel.inquiry_id: Optional[int]（nullable=True）
  - 外部キー制約: FOREIGN KEY (inquiry_id) REFERENCES inquiries(id)
  - インデックス: CREATE INDEX ix_stories_inquiry_id ON stories(inquiry_id)
- **理由**: 要件を満たしつつ参照整合性を保証、既存パターンとの一貫性
- **トレードオフ**: NULL値の扱いによるクエリの複雑化 vs データ整合性の保証
- **フォローアップ**: inquiry_idがNULLのストーリーをフィルタリングするクエリメソッドを追加

## リスクと軽減策
- **OpenAI APIレート制限・コスト** - 軽減策: リトライ戦略、タイムアウト設定、使用量監視
- **AI生成品質のばらつき** - 軽減策: プロンプト最適化、構造検証、人間によるレビュー必須（pending_review）
- **Inquiryとの結合度** - 軽減策: inquiry_id nullableで疎結合、外部キー制約で整合性保証
- **UI/UXの一貫性** - 軽減策: 既存InquiryコンポーネントパターンをStoryに適用

## 参考資料
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference) - API仕様
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/) - サービス層注入パターン
- [SQLAlchemy 2.0 ORM](https://docs.sqlalchemy.org/en/20/orm/) - ORM仕様
- [Pydantic V2](https://docs.pydantic.dev/latest/) - バリデーション
- [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview) - React Query仕様
