# 実装タスク

## タスク概要

問い合わせ管理機能の実装タスクです。Option A（簡略化アプローチ）に基づき、以下の方針で実装します:
- Pydantic スキーマバリデーションを使用（InquiryValidator は不要）
- API ルートが直接 Repository に接続（InquiryQueryService は不要）
- InquiryWorkflowService のみ実装

## 実装タスク

- [ ] 1. データベース・モデル層の実装
- [ ] 1.1 (P) InquiryStatus 列挙型に REJECTED ステータスを追加
  - backend/models/enums/inquiry_status.py に REJECTED = "rejected" を追加
  - frontend/src/types/enums/inquiry-status.ts に REJECTED を追加
  - 両方の列挙型定義が完全に一致することを確認
  - _Requirements: 3.4_

- [ ] 1.2 (P) inquiry_metadata フィールドのスキーマ定義を実装
  - RejectionMetadata 型の定義（却下理由、却下日時、却下者）
  - StatusHistoryEntry 型の定義（ステータス変更履歴）
  - InquiryMetadata 型の定義（rejection, status_history, source, tags）
  - JSON スキーマバリデーションの実装
  - _Requirements: 3.6, 3.7, 3.12_

- [ ] 1.3 データベーススキーマに source_system と updated_at フィールドを追加
  - Alembic マイグレーションファイルの作成
  - source_system カラムの追加（String型、必須、デフォルト値なし）
  - updated_at カラムの追加（DateTime型、自動更新トリガー設定）
  - 既存データへの影響を最小化するマイグレーション戦略
  - マイグレーションのロールバック手順の確認
  - _Requirements: 1.2, 2.9_

- [ ] 2. バックエンド API 層の実装
- [ ] 2.1 (P) Pydantic スキーマの実装
  - CreateInquiryRequest スキーマ（user_id, content, source_system のバリデーション）
  - UpdateInquiryRequest スキーマ（content, source_system のオプショナルバリデーション）
  - InquiryResponse スキーマ（全フィールドのシリアライゼーション）
  - RejectInquiryRequest スキーマ（reason のオプショナルバリデーション、最大1000文字）
  - エラーメッセージを日本語で定義
  - _Requirements: 1.4, 2.8, 3.5_

- [ ] 2.2 InquiryRepository の実装
  - create メソッド（問い合わせ作成、初期ステータスは received）
  - findById メソッド（ID による問い合わせ取得）
  - findMany メソッド（フィルタリング、ソート、ページネーション対応）
  - count メソッド（フィルタ条件に一致する問い合わせ数）
  - update メソッド（問い合わせ内容の更新、updated_at 自動更新）
  - updateStatus メソッド（ステータス更新、metadata 更新）
  - SQLAlchemy セッション管理と依存性注入
  - _Requirements: 1.1, 1.2, 2.3, 2.5, 2.8, 3.1, 3.4_

- [ ] 2.3 PUT /api/inquiries/{id} エンドポイントの実装
  - UpdateInquiryRequest スキーマによる入力バリデーション
  - 問い合わせの存在確認（404 エラー処理）
  - Repository の update メソッド呼び出し
  - updated_at タイムスタンプの自動更新
  - InquiryResponse でレスポンス返却
  - _Requirements: 2.8, 2.9_

- [ ] 2.4 (P) エラーハンドリングとバリデーションの実装
  - ValidationError のハンドリング（400 Bad Request）
  - EntityNotFoundError のハンドリング（404 Not Found）
  - InvalidStateTransitionError のハンドリング（409 Conflict）
  - DatabaseError のハンドリング（500 Internal Server Error）
  - エラーコード体系の実装（GS-001 から GS-011）
  - 日本語エラーメッセージの定義
  - _Requirements: 1.3, 2.6_

- [ ] 3. ワークフロー機能の実装
- [ ] 3.1 InquiryWorkflowService の実装
  - approveInquiry メソッド（ステータスを task_working に変更）
  - rejectInquiry メソッド（ステータスを rejected に変更、却下理由を metadata に保存）
  - canTransitionTo メソッド（ステータス遷移検証ロジック）
  - ステータス変更履歴の metadata への記録
  - トランザクション境界の管理
  - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6, 3.7, 3.10, 3.11, 3.12_

- [ ] 3.2 POST /api/inquiries/{id}/approve エンドポイントの実装
  - InquiryWorkflowService の approveInquiry メソッド呼び出し
  - 問い合わせの存在確認（404 エラー処理）
  - ステータス遷移の妥当性検証（409 エラー処理）
  - InquiryResponse でレスポンス返却
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 3.3 POST /api/inquiries/{id}/reject エンドポイントの実装
  - RejectInquiryRequest スキーマによる入力バリデーション
  - InquiryWorkflowService の rejectInquiry メソッド呼び出し
  - 問い合わせの存在確認（404 エラー処理）
  - ステータス遷移の妥当性検証（409 エラー処理）
  - 却下理由の metadata への保存
  - 却下日時の記録
  - InquiryResponse でレスポンス返却
  - _Requirements: 3.4, 3.5, 3.6, 3.7, 3.8_

- [ ] 3.4 (P) ステータス遷移ロジックのテスト
  - received → task_working 遷移のテスト
  - received → rejected 遷移のテスト
  - 無効な遷移のテスト（task_working → rejected など）
  - 再承認・再却下の禁止ルールのテスト
  - ステータス変更履歴の記録テスト
  - _Requirements: 3.10, 3.11, 3.12_

- [ ] 4. フロントエンド基盤の実装
- [ ] 4.1 (P) TypeScript 型定義の更新
  - InquiryStatus 型に REJECTED を追加
  - RejectionMetadata インターフェースの定義
  - StatusHistoryEntry インターフェースの定義
  - InquiryMetadata インターフェースの定義
  - UpdateInquiryRequest インターフェースの定義
  - RejectInquiryRequest インターフェースの定義
  - _Requirements: 3.4, 3.6, 3.7, 3.12_

- [ ] 4.2 (P) API クライアントサービスの拡張
  - updateInquiry メソッドの実装（PUT /api/inquiries/{id}）
  - approveInquiry メソッドの実装（POST /api/inquiries/{id}/approve）
  - rejectInquiry メソッドの実装（POST /api/inquiries/{id}/reject）
  - エラーハンドリングの実装
  - TypeScript 型定義との統合
  - _Requirements: 2.8, 3.1, 3.4_

- [ ] 4.3 (P) React Hook の実装
  - useUpdateInquiry フック（TanStack Query の useMutation）
  - useApproveInquiry フック（TanStack Query の useMutation）
  - useRejectInquiry フック（TanStack Query の useMutation）
  - キャッシュ無効化とリフレッシュ処理
  - 楽観的更新の実装
  - _Requirements: 2.8, 3.1, 3.4_

- [ ] 5. 問い合わせ管理 UI の実装
- [ ] 5.1 問い合わせ一覧コンポーネントの実装
  - InquiryList コンポーネントの作成
  - TanStack Query によるページネーションの実装
  - 問い合わせの表示（ID、内容、ステータス、タイムスタンプ）
  - ステータスフィルタードロップダウンの実装
  - ページネーションコントロール（前へ/次へ/ページ番号）
  - 行クリックで詳細ページへ遷移
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 4.4_

- [ ] 5.2 問い合わせ詳細・編集コンポーネントの実装
  - InquiryDetail コンポーネントの作成
  - 読み取りモードと編集モードの切り替え
  - インライン編集機能の実装
  - React Hook Form と Zod によるバリデーション
  - 更新履歴の時系列表示
  - エラーメッセージの表示
  - _Requirements: 2.5, 2.8, 2.9, 4.5_

- [ ] 5.3 承認・却下 UI の実装
  - 承認ボタンの実装（received ステータスの問い合わせのみ表示）
  - 却下ボタンと却下理由入力ダイアログの実装
  - 却下理由のバリデーション（最大1000文字）
  - ステータスに応じたボタンの表示制御
  - 承認・却下アクションの確認ダイアログ
  - 成功・エラーメッセージの表示（react-hot-toast）
  - _Requirements: 3.3, 3.8, 3.9, 3.10, 3.11_

- [ ] 5.4 (P) バリデーションとエラー表示の実装
  - フォームバリデーションルールの定義
  - バリデーションエラーメッセージの日本語化
  - フィールド単位のエラー表示
  - サーバーエラーのエラーバナー表示
  - ローディング状態の表示
  - _Requirements: 4.2, 4.3_

- [ ] 6. 統合テスト
- [ ] 6.1 (P) バックエンド統合テストの実装
  - 問い合わせ作成 API のテスト
  - 問い合わせ一覧取得 API のテスト（ページネーション、フィルタリング）
  - 問い合わせ更新 API のテスト
  - 承認・却下ワークフローのテスト
  - エラーケースのテスト
  - pytest カバレッジ 80% 以上を目標
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8, 2.9, 3.1, 3.2, 3.4, 3.5, 3.6, 3.7, 3.10, 3.11, 3.12_

- [ ] 6.2 (P) フロントエンド統合テストの実装
  - InquiryForm コンポーネントのテスト
  - InquiryList コンポーネントのテスト
  - InquiryDetail コンポーネントのテスト
  - 承認・却下 UI のテスト
  - バリデーションのテスト
  - Jest + React Testing Library カバレッジ 70% 以上を目標
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6.3 E2E テストの実装
  - 問い合わせ作成から承認までのフローテスト
  - 問い合わせ作成から却下までのフローテスト
  - 問い合わせ編集フローのテスト
  - エラーケースのテスト
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8, 2.9, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 4.1, 4.2, 4.3, 4.4, 4.5_

## タスク進行の注意事項

### 並列実行可能なタスク
- `(P)` マークの付いたタスクは並列実行可能です
- ただし、同じフェーズ内での並列実行を推奨します
- データベースマイグレーション（1.3）は他のタスクより先に完了させる必要があります

### 依存関係
- フェーズ 1（データベース・モデル層）→ フェーズ 2（バックエンド API 層）
- フェーズ 2（バックエンド API 層）→ フェーズ 3（ワークフロー機能）
- フェーズ 2（バックエンド API 層）→ フェーズ 4（フロントエンド基盤）
- フェーズ 4（フロントエンド基盤）→ フェーズ 5（問い合わせ管理 UI）
- すべてのフェーズ → フェーズ 6（統合テスト）

### テスト要件
- すべての実装タスクには対応するテストが必要です
- バックエンド: pytest カバレッジ 80% 以上
- フロントエンド: Jest + RTL カバレッジ 70% 以上

### コード品質
- バックエンド: black, flake8, mypy, bandit
- フロントエンド: prettier, ESLint, TypeScript strict mode
- コミット前に `make lint` と `make test` を実行
