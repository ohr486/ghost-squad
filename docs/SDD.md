# Spec-Driven Development (SDD)

Ghost SquadプロジェクトにおけるKiro-style Spec-Driven Developmentの実践ガイドです。

## 概要

Ghost Squadは **AI-DLC (AI Development Life Cycle)** におけるKiro-style Spec-Driven Developmentを採用しています。これは、仕様策定から実装まで段階的に進め、各フェーズで人間のレビューと承認を経る開発手法です。

## Kiro開発フロー

### Phase 0: Steering（プロジェクト設定）- オプション

プロジェクト全体のルールとコンテキストを設定します。

```bash
# Steeringドキュメント管理
/kiro:steering

# カスタムSteeringドキュメント作成
/kiro:steering-custom
```

**Steeringドキュメントの種類**:
- `product.md` - プロダクトガイドライン
- `tech.md` - 技術スタック・開発環境
- `structure.md` - プロジェクト構造・組織化

### Phase 1: Specification（仕様策定）

機能の要件定義、設計、タスク分解を行います。

#### 1-1. 仕様の初期化

```bash
/kiro:spec-init "機能の説明"
```

**例**:
```bash
/kiro:spec-init "ユーザーが問い合わせを入力・管理できる機能"
```

これにより `.kiro/specs/{feature}/` ディレクトリが作成され、以下のファイルが初期化されます：
- `spec.json` - 仕様のメタデータ
- `requirements-init.md` - 初期要件（ユーザー入力から生成）

#### 1-2. 要件の生成

```bash
/kiro:spec-requirements {feature}
```

**例**:
```bash
/kiro:spec-requirements inquiry
```

生成されるドキュメント: `requirements.md`

**内容**:
- 機能概要
- ユーザーストーリー
- 機能要件
- 非機能要件
- 制約事項
- 受け入れ基準

**承認が必要**: 生成後、内容を確認して承認する必要があります。

#### 1-3. ギャップ分析（オプション）

既存コードベースとの差分を分析します。

```bash
/kiro:validate-gap {feature}
```

**例**:
```bash
/kiro:validate-gap inquiry
```

**出力**:
- 既存の実装状況
- 不足している機能
- 修正が必要な箇所
- 実装の推奨アプローチ

#### 1-4. 技術設計の作成

```bash
/kiro:spec-design {feature} [-y]
```

**例**:
```bash
# 通常（レビュー後に承認が必要）
/kiro:spec-design inquiry

# 自動承認モード（注意：慎重に使用）
/kiro:spec-design inquiry -y
```

生成されるドキュメント: `design.md`

**内容**:
- アーキテクチャ設計
- データモデル設計
- API設計
- セキュリティ考慮事項
- パフォーマンス要件

**承認が必要**: `-y`フラグを使用しない限り、承認が必要です。

#### 1-5. 設計レビュー（オプション）

設計の品質を検証します。

```bash
/kiro:validate-design {feature}
```

**例**:
```bash
/kiro:validate-design inquiry
```

**チェック項目**:
- 設計の完全性
- セキュリティリスク
- パフォーマンスボトルネック
- 保守性・拡張性

#### 1-6. 実装タスクの生成

```bash
/kiro:spec-tasks {feature} [-y]
```

**例**:
```bash
# 通常（レビュー後に承認が必要）
/kiro:spec-tasks inquiry

# 自動承認モード
/kiro:spec-tasks inquiry -y
```

生成されるドキュメント: `tasks.md`

**内容**:
- タスク一覧（優先順位付き）
- 各タスクの詳細説明
- 依存関係
- 見積もり工数

**承認が必要**: `-y`フラグを使用しない限り、承認が必要です。

### Phase 2: Implementation（実装）

TDD（テスト駆動開発）手法で実装を進めます。

#### 2-1. タスクの実装

```bash
/kiro:spec-impl {feature} [tasks]
```

**例**:
```bash
# 全タスクを実装
/kiro:spec-impl inquiry

# 特定のタスクのみ実装
/kiro:spec-impl inquiry "タスク1,タスク3,タスク5"
```

**実装プロセス**:
1. テストファイルの作成
2. テストの実装（失敗するテスト）
3. 機能の実装
4. テストの通過確認
5. リファクタリング
6. 次のタスクへ

#### 2-2. 実装の検証（オプション）

要件・設計・タスクに対する実装の妥当性を検証します。

```bash
/kiro:validate-impl {feature}
```

**例**:
```bash
/kiro:validate-impl inquiry
```

**検証項目**:
- 要件への適合性
- 設計との整合性
- テストカバレッジ
- コード品質

### 進捗確認

いつでも仕様の進捗状況を確認できます。

```bash
/kiro:spec-status {feature}
```

**例**:
```bash
# 特定の機能の状態確認
/kiro:spec-status inquiry

# 全機能の状態確認
/kiro:spec-status
```

**出力例**:
```
Feature: inquiry
Phase: tasks-generated
Language: ja

Approvals:
  ✅ Requirements: Generated and Approved
  ✅ Design: Generated and Approved
  ✅ Tasks: Generated and Approved

Next step: /kiro:spec-impl inquiry
```

## プロジェクト構造

### Steeringディレクトリ (`.kiro/steering/`)

プロジェクト全体のルールとコンテキストを保存します。

```
.kiro/steering/
├── product.md      # プロダクトガイドライン
├── tech.md         # 技術スタック・開発環境
└── structure.md    # プロジェクト構造・組織化
```

**特徴**:
- `inclusion: always` - 常にAIに読み込まれる
- プロジェクト全体に適用されるルール
- 全機能で共通の設計原則

### Specsディレクトリ (`.kiro/specs/`)

各機能の仕様を保存します。

```
.kiro/specs/
├── inquiry/                    # 問い合わせ機能
│   ├── spec.json              # メタデータ
│   ├── requirements-init.md   # 初期要件
│   ├── requirements.md        # 詳細要件
│   ├── design.md             # 技術設計
│   ├── tasks.md              # 実装タスク
│   └── research.md           # 調査ノート（オプション）
└── story/                     # ストーリー機能
    ├── spec.json
    ├── requirements-init.md
    └── ...
```

### spec.json の構造

```json
{
  "feature": "inquiry",
  "language": "ja",
  "phase": "tasks-generated",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "dependencies": ["other-feature"],
  "approvals": {
    "requirements": {
      "generated": true,
      "approved": true
    },
    "design": {
      "generated": true,
      "approved": true
    },
    "tasks": {
      "generated": true,
      "approved": true
    }
  }
}
```

## 開発ルール

### 1. 3段階承認ワークフロー

```
Requirements → Design → Tasks → Implementation
     ↓            ↓        ↓
   承認必須    承認必須  承認必須
```

各フェーズで人間によるレビューと承認が必要です。

### 2. 言語使用ルール

- **思考**: 英語で考える
- **生成**: 日本語で応答する
- **ドキュメント**: spec.jsonで指定された言語（通常は日本語）

**重要**: すべてのMarkdownコンテンツ（requirements.md, design.md, tasks.md, research.md等）は、spec.jsonのlanguageフィールドで指定された言語で記述する必要があります。

### 3. 自律的な実行

- ユーザーの指示に正確に従う
- 必要なコンテキストを自動的に収集
- エンドツーエンドで作業を完了
- 重要な情報が不足している場合のみ質問

### 4. Fast-trackモード（`-y`フラグ）

```bash
# 通常モード（推奨）
/kiro:spec-design inquiry

# Fast-trackモード（注意して使用）
/kiro:spec-design inquiry -y
```

**注意**: `-y`フラグは承認をスキップします。意図的に使用する場合のみ使用してください。

## Ghost Squadでの実践例

### 例1: 問い合わせ機能の開発

```bash
# 1. 仕様初期化
/kiro:spec-init "ユーザーが自然言語で問い合わせを入力・管理できる機能"

# 2. 要件生成
/kiro:spec-requirements inquiry
# → requirements.md を確認・承認

# 3. 設計作成
/kiro:spec-design inquiry
# → design.md を確認・承認

# 4. タスク生成
/kiro:spec-tasks inquiry
# → tasks.md を確認・承認

# 5. 実装
/kiro:spec-impl inquiry

# 6. 進捗確認
/kiro:spec-status inquiry
```

### 例2: ストーリー機能の開発（依存関係あり）

```bash
# 1. 仕様初期化（inquiryに依存）
/kiro:spec-init "問い合わせからAIを使ってストーリーを生成する機能"
# spec.jsonに "dependencies": ["inquiry"] を追加

# 2. ギャップ分析（既存のinquiry実装を確認）
/kiro:validate-gap story

# 3. 要件生成
/kiro:spec-requirements story

# 4. 設計レビュー
/kiro:spec-design story
/kiro:validate-design story
# → フィードバックを受けて design.md を修正・再承認

# 5. タスク生成
/kiro:spec-tasks story

# 6. 実装
/kiro:spec-impl story

# 7. 実装検証
/kiro:validate-impl story
```

## よくある質問

### Q1: いつSteeringドキュメントを更新すべきですか？

**A**: 以下の場合に更新します：
- プロジェクトの方向性が変わった時
- 新しい技術スタックを導入する時
- アーキテクチャパターンが確立した時
- チームの開発プロセスが変わった時

### Q2: 複数の機能を並行開発できますか？

**A**: はい、ただし以下に注意：
- 依存関係を spec.json に明記する
- 依存元の機能が実装完了していることを確認
- `/kiro:spec-status` で全体の進捗を確認

### Q3: 要件や設計を後から変更できますか？

**A**: はい、以下の手順で：
1. requirements.md または design.md を手動で編集
2. spec.json の approvals を false に戻す
3. 再度レビュー・承認
4. 必要に応じて `/kiro:spec-tasks` で タスクを再生成

### Q4: `-y` フラグはいつ使うべきですか？

**A**: 以下の場合のみ推奨：
- プロトタイプやPoC（概念実証）の作成時
- 非常にシンプルな機能の場合
- 既に詳細なレビューを行った後の再生成時

通常の開発では使用せず、各フェーズで人間のレビューを行うことを推奨します。

### Q5: 既存コードに機能を追加する場合は？

**A**: `/kiro:validate-gap` を活用：
```bash
# 1. 仕様初期化
/kiro:spec-init "既存の問い合わせ機能に検索機能を追加"

# 2. ギャップ分析（既存実装を確認）
/kiro:validate-gap inquiry-search

# 3. 分析結果を参考に要件・設計を作成
/kiro:spec-requirements inquiry-search
/kiro:spec-design inquiry-search

# 4. タスク生成・実装
/kiro:spec-tasks inquiry-search
/kiro:spec-impl inquiry-search
```

## ベストプラクティス

### 1. 小さく始める

- 大きな機能は小さなサブ機能に分割
- 各サブ機能を独立した spec として管理
- 依存関係を明確にする

### 2. ドキュメントを最新に保つ

- 実装中に気づいた点を research.md に記録
- 設計変更があれば design.md を更新
- spec.json の phase と approvals を正確に管理

### 3. 検証ツールを活用

- `/kiro:validate-gap` - 実装前のギャップ確認
- `/kiro:validate-design` - 設計品質の検証
- `/kiro:validate-impl` - 実装後の妥当性確認

### 4. 定期的な進捗確認

```bash
# 毎日の開発開始時
/kiro:spec-status

# 機能完了時
/kiro:spec-status {feature}
/kiro:validate-impl {feature}
```

## トラブルシューティング

### 仕様ファイルが見つからない

**問題**: `/kiro:spec-requirements inquiry` でエラー

**解決**:
```bash
# 1. 仕様が初期化されているか確認
ls -la .kiro/specs/inquiry/

# 2. 初期化されていなければ実行
/kiro:spec-init "問い合わせ機能"

# 3. 再試行
/kiro:spec-requirements inquiry
```

### 承認状態がおかしい

**問題**: spec.json の承認状態が実際と異なる

**解決**:
```bash
# spec.json を手動で編集
vim .kiro/specs/inquiry/spec.json

# approvals セクションを修正
{
  "approvals": {
    "requirements": {
      "generated": true,
      "approved": true  # <- 実際の状態に合わせる
    },
    ...
  }
}
```

### ドキュメントの言語が間違っている

**問題**: ドキュメントが英語で生成された

**解決**:
```bash
# spec.json を確認
cat .kiro/specs/inquiry/spec.json

# language フィールドを確認・修正
{
  "language": "ja"  # <- "ja" になっているか確認
}

# ドキュメントを再生成
/kiro:spec-requirements inquiry
```

## 関連ドキュメント

- [API仕様](API.md)
- [データベース管理ガイド](DATABASE.md)
- [README](../README.md)
- [CLAUDE.md](../CLAUDE.md) - AI開発アシスタント向けガイド
