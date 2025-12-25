# ストーリーボード機能 ギャップ分析

## 分析サマリー

- **スコープ**: 問い合わせの受付・編集・承認・却下、および問い合わせからストーリーへの変換機能のエンドツーエンド実装
- **主要な課題**:
  - ストーリー管理APIが未実装（バックエンド）
  - 問い合わせ更新APIが未実装（バックエンド）
  - AI変換機能（OpenAI統合）が未実装
  - フロントエンド表示・編集コンポーネントが部分実装
  - 承認・却下ワークフローの実装が必要
- **推奨アプローチ**: ハイブリッドアプローチ（既存パターン拡張 + 新規コンポーネント作成）
- **実装規模**: Medium-Large（要件が5つ、複数層にまたがる統合が必要）
- **リスク**: Medium（既存パターン活用可能だが、AI統合とワークフロー実装に不確実性あり）

---

## 1. 現状調査

### 1.1 既存のドメイン関連資産

#### データベースモデル（完全実装済み）

**InquiryModel** (`backend/models/database/inquiry.py`)
- ✅ 全必須フィールド実装済み
  - `id` (BigInteger), `user_id`, `content`, `language`, `timestamp`
  - `status` (InquiryStatus enum)
  - `inquiry_metadata` (JSON)
- ✅ StoryModelとのリレーションシップ設定済み
- ✅ マイグレーション適用済み（`initial_schema_for_storyboard.py`）

**StoryModel** (`backend/models/database/story.py`)
- ✅ 全必須フィールド実装済み
  - `id` (BigInteger), `inquiry_id` (外部キー), `title`, `description`
  - `category`, `priority`, `estimated_effort`, `deadline`
  - `status` (StoryStatus enum), `assignee`, `tags`, `dependencies`
  - `story_metadata` (JSON), `created_at`, `updated_at`
- ✅ InquiryModelとのリレーションシップ設定済み
- ✅ マイグレーション適用済み

**Enumクラス** (`backend/models/enums/`)
- ✅ `InquiryStatus`: RECEIVED, PROCESSING, NEEDS_CLARIFICATION, TASK_WORKING, COMPLETED, FAILED
- ✅ `StoryStatus`: PENDING_REVIEW, APPROVED, EXPORTED, REJECTED
- ✅ `Priority`, `StoryCategory`, `StoryPattern` も実装済み

#### API層（部分実装）

**問い合わせAPI** (`backend/api/inquiries.py`)
- ✅ `POST /api/inquiries` - 問い合わせ作成（完全実装）
- ✅ `GET /api/inquiries` - 一覧取得（ページネーション対応）
- ✅ `GET /api/inquiries/{id}` - 個別取得
- ❌ `PUT /api/inquiries/{id}` - 問い合わせ更新（未実装）
- ❌ 承認・却下エンドポイント（未実装）

**ストーリーAPI**
- ❌ `backend/api/stories.py` ファイル自体が存在しない
- ❌ ストーリーCRUD操作が全て未実装
- ❌ AI変換エンドポイントが未実装

#### フロントエンド（部分実装）

**実装済みコンポーネント**
- ✅ `InquiryForm.tsx` - React Hook Form + Zod バリデーション（完全実装）
- ✅ `InquiryService.ts` - API呼び出しサービス（一部実装）
- ✅ 型定義 - 42ファイル、バックエンドと完全対応

**未実装コンポーネント**
- ❌ 問い合わせ一覧表示コンポーネント（`InquiriesPage.tsx`は骨格のみ）
- ❌ 問い合わせ編集コンポーネント
- ❌ 承認・却下UIコンポーネント
- ❌ ストーリー表示・編集コンポーネント
- ❌ ストーリー一覧表示

### 1.2 既存の設計パターンと規約

**API設計パターン**（`backend/api/inquiries.py`から抽出）
- FastAPI Router使用（`APIRouter(prefix="/resource", tags=["resource"])`）
- Pydantic Request/Responseモデル使用
- 依存性注入によるDBセッション管理（`Depends(get_db)`）
- 日本語エラーメッセージ
- 詳細なエラーハンドリング（SQLAlchemyError, ValidationError, 一般Exception）
- ロギング（`logger.error`）
- HTTPステータスコード適切使用

**命名規則**
- ファイル: `snake_case.py`
- クラス: `PascalCase`（例: `InquiryModel`, `InquiryService`）
- 関数・変数: `snake_case`
- Enumメンバー: `UPPER_SNAKE_CASE`

**ディレクトリ構造**
```
backend/
  api/
    __init__.py
    inquiries.py      # ← 既存パターン
    (stories.py)      # ← 新規作成が必要
  models/
    database/         # ORMモデル（実装済み）
    schemas/          # Pydanticスキーマ（実装済み）
    api/              # Request/Responseモデル（実装済み）
    enums/            # 列挙型（実装済み）
  services/           # ← ディレクトリ自体が未作成
```

**フロントエンドパターン**（`InquiryForm.tsx`, `inquiryService.ts`から抽出）
- React Hook Form + Zodバリデーション
- TanStack React Query使用想定（設定済みだが未使用）
- Axiosベースのサービス層（`services/inquiryService.ts`）
- Tailwind CSS + Lucide Reactアイコン
- ダークモード対応
- アクセシビリティ考慮（aria属性、role属性）

### 1.3 統合ポイント

**既存の統合箇所**
- ✅ FastAPI CORS設定（localhost:3000, Docker内部通信）
- ✅ PostgreSQL接続管理（`database.py`）
- ✅ Alembicマイグレーション管理
- ✅ 環境変数管理（`.env`）
- ✅ Docker Compose統合
- ✅ OpenAI API依存関係（`requirements.txt`にopenai==1.3.7）

**不足している統合箇所**
- ❌ OpenAI APIクライアント実装
- ❌ ストーリー変換サービス層
- ❌ フロントエンド - バックエンド間のストーリーAPI統合

---

## 2. 要件の実現可能性分析

### 要件1: 問い合わせの受付と保存と編集

**技術的ニーズ**
- データモデル: ✅ InquiryModel（実装済み）
- API:
  - ✅ POST /api/inquiries（実装済み）
  - ❌ PUT /api/inquiries/{id}（未実装）
- UI:
  - ✅ InquiryForm（実装済み）
  - ❌ 編集フォーム（未実装）

**ギャップ**
- **Missing**: 問い合わせ更新APIエンドポイント
- **Missing**: フロントエンド編集UIコンポーネント

**制約**
- 既存のInquiryModelスキーマ維持必須
- BigInteger ID使用（変更不可）

### 要件2: 問い合わせの承認と却下

**技術的ニーズ**
- データモデル: ✅ InquiryModel.status（実装済み）
- API:
  - ❌ PATCH /api/inquiries/{id}/approve（新規必要）
  - ❌ PATCH /api/inquiries/{id}/reject（新規必要）
  - または PUT /api/inquiries/{id} でステータス更新
- ビジネスロジック:
  - ステータス遷移ルール（RECEIVED → APPROVED/REJECTED）
  - タイムスタンプ・ユーザー名記録

**ギャップ**
- **Missing**: 承認・却下APIエンドポイント
- **Missing**: ステータス遷移バリデーション
- **Missing**: 承認者情報の記録（InquiryModel.inquiry_metadataに格納可能）
- **Missing**: フロントエンド承認・却下UIコンポーネント

**複雑性**
- ステータス遷移ルールの実装（有限状態機械パターン推奨）

### 要件3: 問い合わせからストーリーへの変換機能

**技術的ニーズ**
- データモデル: ✅ StoryModel（実装済み）
- AI統合:
  - ❌ OpenAI APIクライアント（未実装）
  - ❌ ストーリー生成プロンプト設計（未実装）
  - ❌ AI応答のパース・バリデーション（未実装）
- API:
  - ❌ POST /api/stories/generate（未実装）
  - ❌ POST /api/inquiries/{id}/convert（代替案）
- ビジネスロジック:
  - 承認済み問い合わせのみ変換可能
  - 変換失敗時のエラーハンドリング
  - ストーリーと問い合わせの関連付け（外部キー）

**ギャップ**
- **Missing**: OpenAI統合サービス層（`services/ai_service.py`など）
- **Missing**: ストーリー生成APIエンドポイント
- **Missing**: プロンプトテンプレート管理
- **Missing**: AI応答パーサー
- **Unknown**: OpenAI API使用量制限・コスト管理

**制約**
- OpenAI API依存（外部サービス）
- API応答時間の不確実性（タイムアウト設定必要）

**Research Needed**
- OpenAI API最適なモデル選択（GPT-4 vs GPT-3.5-turbo）
- プロンプトエンジニアリングのベストプラクティス
- 生成品質の評価手法

### 要件4: ユーザーインターフェース

**技術的ニーズ**
- UI:
  - ✅ InquiryForm（実装済み）
  - ❌ 問い合わせ一覧・表示（未実装）
  - ❌ ストーリー一覧・表示・編集（未実装）
  - ❌ 検索・フィルタリングUI（未実装）
- バリデーション:
  - ✅ Zodスキーマ（InquiryForm実装済み）
  - ❌ ストーリー編集用Zodスキーマ（未実装）

**ギャップ**
- **Missing**: 問い合わせ一覧表示コンポーネント（TanStack Queryでページネーション）
- **Missing**: ストーリー表示・編集コンポーネント
- **Missing**: 検索・フィルタリングUI
- **Missing**: エラー表示UI（toast通知は実装済み）

### 要件5: データの永続化と整合性

**技術的ニーズ**
- データベース: ✅ PostgreSQL（実装済み）
- ORM: ✅ SQLAlchemy（実装済み）
- マイグレーション: ✅ Alembic（実装済み）
- 外部キー制約: ✅ InquiryModel ↔ StoryModel（実装済み）
- トランザクション管理: ✅ SQLAlchemyセッション管理（実装済み）
- エラーハンドリング: ✅ リトライロジック（APIレベルで実装可能）

**ギャップ**
- **Missing**: リトライロジックの明示的実装（現在はエラーレスポンスのみ）
- **Constraint**: 既存のBigInteger ID型（変更不可）

**実装済み**
- ✅ UTCタイムゾーン統一
- ✅ JSON列のデフォルト値設定
- ✅ 外部キー制約

---

## 3. 実装アプローチのオプション

### オプションA: 既存コンポーネント拡張

**拡張対象**
- `backend/api/inquiries.py` に承認・却下エンドポイント追加
- `frontend/src/services/inquiryService.ts` に承認・却下メソッド追加
- `frontend/src/pages/InquiriesPage.tsx` に一覧表示・承認UI追加

**互換性評価**
- ✅ 既存のInquiryModelスキーマと完全互換
- ✅ 既存のAPI設計パターンと一貫性維持
- ✅ 後方互換性：既存エンドポイントに影響なし

**複雑性と保守性**
- ✅ 認知負荷：低（既存パターン踏襲）
- ⚠️ ファイルサイズ：inquiries.pyが300行程度に増加（許容範囲内）
- ✅ 単一責任原則：問い合わせ関連操作で一貫

**トレードオフ**
- ✅ 最小限の新規ファイル
- ✅ 既存パターン活用で開発速度向上
- ✅ テストの拡張が容易
- ❌ inquiries.py が肥大化する可能性
- ❌ ストーリー関連機能は別ファイル必須（混在不可）

### オプションB: 新規コンポーネント作成

**新規作成対象**
- `backend/api/stories.py` - ストーリーCRUD操作
- `backend/services/ai_service.py` - OpenAI統合
- `backend/services/story_service.py` - ストーリー生成ビジネスロジック
- `frontend/src/services/storyService.ts` - ストーリーAPIクライアント
- `frontend/src/components/stories/` - ストーリー表示・編集コンポーネント

**統合ポイント**
- FastAPIのルーター統合（`main.py`に`api_router.include_router(story_router)`追加）
- InquiryModel ↔ StoryModel間のリレーションシップ活用
- 共通のエラーハンドリング・ロギングパターン使用

**責任境界**
- **stories.py**: ストーリーCRUD、AI変換トリガー
- **ai_service.py**: OpenAI API呼び出し、プロンプト管理
- **story_service.py**: ビジネスロジック、バリデーション
- 既存の`inquiries.py`との明確な分離

**トレードオフ**
- ✅ 関心の分離が明確
- ✅ 既存コンポーネントへの影響最小
- ✅ テストの独立性向上
- ✅ 将来の拡張性向上
- ❌ ファイル数増加（ナビゲーション複雑化）
- ❌ 初期開発コスト高

### オプションC: ハイブリッドアプローチ（推奨）

**戦略**
- **既存拡張**: 問い合わせ更新・承認・却下は`inquiries.py`に追加
- **新規作成**: ストーリー管理とAI統合は新規ファイル
- **段階実装**:
  1. Phase 1: 問い合わせ更新・承認API実装（inquiries.py拡張）
  2. Phase 2: ストーリーCRUD API実装（stories.py新規）
  3. Phase 3: AI統合（ai_service.py, story_service.py新規）
  4. Phase 4: フロントエンド統合

**リスク軽減**
- 段階的なリリースで問題の早期発見
- 各フェーズでのテスト充実
- AI統合の技術的不確実性を後期フェーズに隔離

**トレードオフ**
- ✅ バランスの取れたアプローチ
- ✅ 段階的な価値提供
- ✅ リスクの分散
- ❌ フェーズ間の調整コスト
- ❌ 初期フェーズで全機能提供不可

---

## 4. 実装複雑性とリスク

### 実装規模

**Effort: M-L (Medium-Large, 1-2週間)**

**根拠**
- 問い合わせ更新・承認API: 2-3日（既存パターン活用）
- ストーリーCRUD API: 3-4日（新規だが既存パターン参考）
- AI統合サービス: 4-5日（OpenAI統合、プロンプト設計、テスト）
- フロントエンドコンポーネント: 3-4日（一覧、編集、承認UI）
- 統合テスト・デバッグ: 2-3日

### リスク評価

**Risk: Medium**

**High Riskの要素**
- **AI統合の不確実性**:
  - OpenAI APIの応答品質（プロンプトチューニング必要）
  - APIレスポンス時間の変動
  - 使用量制限・コスト管理
- **ワークフロー複雑性**:
  - ステータス遷移ルールの正確な実装
  - 承認・却下権限管理（現状未定義）

**Medium Riskの要素**
- **新規パターン導入**:
  - サービス層の設計（既存に前例なし）
  - AI応答パーサーの実装
- **統合テスト範囲**:
  - フロントエンド ↔ バックエンド統合
  - AI ↔ データベース統合

**Low Riskの要素**
- **既存パターン活用**:
  - 問い合わせAPI拡張（inquiries.pyパターン踏襲）
  - データベーススキーマ（変更不要）
  - フロントエンドサービス層（InquiryService参考）

---

## 5. 要件-資産マップ

| 要件 | 必要な資産 | 状態 | ギャップ |
|------|-----------|------|---------|
| **要件1: 問い合わせの受付と保存と編集** | | | |
| | InquiryModel | ✅ 実装済み | - |
| | POST /api/inquiries | ✅ 実装済み | - |
| | PUT /api/inquiries/{id} | ❌ 未実装 | **Missing**: 更新APIエンドポイント |
| | InquiryForm | ✅ 実装済み | - |
| | 編集UIコンポーネント | ❌ 未実装 | **Missing**: 編集フォーム |
| **要件2: 問い合わせの承認と却下** | | | |
| | InquiryModel.status | ✅ 実装済み | - |
| | 承認・却下API | ❌ 未実装 | **Missing**: PATCH /approve, /reject エンドポイント |
| | ステータス遷移バリデーション | ❌ 未実装 | **Missing**: FSMパターン実装 |
| | 承認UIコンポーネント | ❌ 未実装 | **Missing**: 承認・却下ボタンUI |
| **要件3: 問い合わせからストーリーへの変換** | | | |
| | StoryModel | ✅ 実装済み | - |
| | OpenAI APIクライアント | ❌ 未実装 | **Missing**: ai_service.py |
| | ストーリー生成API | ❌ 未実装 | **Missing**: POST /api/stories/generate |
| | プロンプト管理 | ❌ 未実装 | **Unknown**: プロンプト設計 |
| | AI応答パーサー | ❌ 未実装 | **Missing**: レスポンス処理ロジック |
| **要件4: ユーザーインターフェース** | | | |
| | 問い合わせ一覧UI | ❌ 未実装 | **Missing**: InquiriesPageの完全実装 |
| | ストーリー表示UI | ❌ 未実装 | **Missing**: Storyコンポーネント群 |
| | 検索・フィルタリングUI | ❌ 未実装 | **Missing**: 検索コンポーネント |
| **要件5: データの永続化と整合性** | | | |
| | PostgreSQL + SQLAlchemy | ✅ 実装済み | - |
| | 外部キー制約 | ✅ 実装済み | - |
| | トランザクション管理 | ✅ 実装済み | - |
| | リトライロジック | ❌ 未実装 | **Missing**: 明示的リトライ実装 |

---

## 6. 設計フェーズへの推奨事項

### 推奨アプローチ

**オプションC（ハイブリッドアプローチ）を推奨**

**理由**
1. 既存のinquiries.pyパターンを活用しつつ、ストーリー管理は新規分離
2. 段階的な実装でリスク軽減
3. AI統合の不確実性を後期フェーズに隔離
4. テスト戦略が明確（フェーズごとのテスト）

### 主要な設計決定事項

**Phase 1: 問い合わせ管理完成**
1. **決定**: PUT /api/inquiries/{id} 実装方法
   - オプションA: 汎用的なPUTエンドポイント（全フィールド更新可能）
   - オプションB: 専用エンドポイント（PATCH /approve, /reject）
   - 推奨: オプションA + 専用エンドポイント併用

2. **決定**: ステータス遷移ルール
   - 有限状態機械（FSM）パターン使用
   - 許可されない遷移時のエラーハンドリング

**Phase 2: ストーリー管理API**
1. **決定**: ストーリーCRUD APIの設計
   - RESTful設計（GET, POST, PUT, DELETE）
   - フィルタリング・ソート機能

2. **決定**: ストーリーと問い合わせの関連管理
   - 問い合わせ削除時のストーリーカスケード処理
   - 複数ストーリー生成の可否

**Phase 3: AI統合**
1. **決定**: OpenAI APIモデル選択
   - GPT-4（高品質、高コスト）vs GPT-3.5-turbo（バランス）
   - Research Needed: 生成品質の比較評価

2. **決定**: プロンプト管理方法
   - オプションA: コード内ハードコード
   - オプションB: データベース管理（templates table）
   - オプションC: 設定ファイル管理
   - 推奨: オプションA（初期）→ オプションB（将来）

3. **決定**: AI生成失敗時のハンドリング
   - リトライ戦略（指数バックオフ）
   - フォールバック処理
   - ユーザーへのエラー通知

**Phase 4: フロントエンド統合**
1. **決定**: 状態管理戦略
   - TanStack React Query活用（サーバー状態管理）
   - 楽観的更新（Optimistic Updates）の適用範囲

2. **決定**: リアルタイム更新
   - オプションA: ポーリング
   - オプションB: WebSocket（将来機能）
   - 推奨: オプションA（初期）

### Research Items（設計フェーズで調査）

1. **OpenAI統合**
   - ベストプラクティス調査（プロンプトエンジニアリング）
   - レート制限・コスト管理手法
   - エラーハンドリングパターン

2. **FSMパターン実装**
   - Pythonでの実装例（transitions library検討）
   - テスト戦略

3. **フロントエンドコンポーネント設計**
   - 既存のデザインシステム確認
   - アクセシビリティガイドライン適用

---

## 7. 次のステップ

### 設計フェーズへの移行

**完了条件**
- ✅ ギャップ分析完了
- ✅ 実装アプローチ決定（ハイブリッド推奨）
- ✅ 主要な設計課題の特定

**設計フェーズで実施すべき内容**
1. 詳細なAPI設計（OpenAPI仕様）
2. サービス層の設計（クラス図、シーケンス図）
3. AI統合の詳細設計（プロンプトテンプレート、エラーハンドリング）
4. フロントエンドコンポーネント設計（コンポーネント階層、状態管理）
5. テスト戦略策定（ユニット、統合、E2E）

**設計ドキュメント生成コマンド**
```bash
/kiro:spec-design storyboard
```

または要件を自動承認して直接設計フェーズに進む場合
```bash
/kiro:spec-design storyboard -y
```

---

## 付録: 技術スタック確認

### 既存の依存関係（活用可能）

**バックエンド**
- ✅ FastAPI 0.104.1
- ✅ SQLAlchemy 2.0.23
- ✅ Pydantic 2.5.0
- ✅ OpenAI 1.3.7（依存関係追加済み、未使用）
- ✅ pytest 7.4.3 + hypothesis 6.92.1（PBT）

**フロントエンド**
- ✅ React 18.2.0 + TypeScript 4.9.5
- ✅ TanStack React Query 5.8.4（設定済み、未使用）
- ✅ React Hook Form 7.43.0 + Zod 3.22.4
- ✅ Tailwind CSS 3.3.5
- ✅ Axios 1.6.2

### 追加が必要な可能性のある依存関係

**調査が必要**
- FSMライブラリ（transitions等）
- OpenAI APIレート制限管理ライブラリ
- リトライライブラリ（tenacity等、既存ではデコレータ未使用）
