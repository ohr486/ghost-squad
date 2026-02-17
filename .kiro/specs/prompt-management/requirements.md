# Requirements Document

## Introduction

Ghost Squadでは、ストーリー生成（StoryGenerationService）やImporter解析（ImporterAnalysisService、OpenAIProvider、AnthropicProvider）など、複数のサブシステムでAIプロンプトを使用している。現在これらのプロンプトはソースコード内にハードコードされており、変更にはコード修正・デプロイが必要である。

本機能は、システム全体で使用されるAIプロンプトを一元管理し、コード変更なしで動的に編集できる管理基盤を提供する。これにより、プロンプトの改善サイクルを高速化し、AI出力品質の継続的な向上を実現する。

## Requirements

### Requirement 1: プロンプト一覧・閲覧

**Objective:** As a 管理者, I want システムで使用中の全プロンプトを一覧表示・閲覧したい, so that 各プロンプトの内容・用途・利用状況を把握できる

#### Acceptance Criteria
1. When 管理者がプロンプト管理画面にアクセスした時, the Prompt Management Service shall 登録されている全プロンプトの一覧を表示する（名前、カテゴリ、最終更新日時、ステータスを含む）
2. When 管理者がプロンプト一覧でプロンプトを選択した時, the Prompt Management Service shall プロンプトの詳細情報を表示する（本文、説明、カテゴリ、変数プレースホルダー、作成日時、最終更新日時を含む）
3. When 管理者がカテゴリフィルターを適用した時, the Prompt Management Service shall 指定カテゴリに属するプロンプトのみを一覧に表示する
4. The Prompt Management Service shall プロンプトのカテゴリとして以下を提供する: story_generation（ストーリー生成）、import_analysis（インポート解析）、general（汎用）

### Requirement 2: プロンプト編集・更新

**Objective:** As a 管理者, I want プロンプトの内容をWebUIから編集・保存したい, so that コード変更なしでAIへの指示を改善できる

#### Acceptance Criteria
1. When 管理者がプロンプト詳細画面で編集ボタンを押した時, the Prompt Management Service shall プロンプト本文を編集可能なテキストエリアで表示する
2. When 管理者が編集済みプロンプトを保存した時, the Prompt Management Service shall プロンプトの内容をデータベースに永続化し、更新日時を記録する
3. When 管理者がプロンプト本文に変数プレースホルダー（例: `{inquiry_content}`、`{template_content}`）を含めた時, the Prompt Management Service shall プレースホルダーの構文を検証し、有効であることを確認する
4. If 管理者が空のプロンプト本文で保存しようとした場合, the Prompt Management Service shall バリデーションエラーを表示し保存を拒否する
5. While プロンプトが編集中の状態で, the Prompt Management Service shall 他の管理者に対して編集中であることを表示する

### Requirement 3: プロンプトテスト・プレビュー

**Objective:** As a 管理者, I want プロンプトを保存する前にテスト実行してAI出力を確認したい, so that 意図通りの結果が得られることを事前に検証できる

#### Acceptance Criteria
1. When 管理者がプロンプト編集画面でテスト実行ボタンを押した時, the Prompt Management Service shall サンプル入力データを使用してAIにプロンプトを送信し、結果をプレビュー表示する
2. When 管理者がテスト実行時にカスタム入力データを指定した時, the Prompt Management Service shall 指定されたデータでプレースホルダーを置換してAIに送信する
3. While テスト実行中の状態で, the Prompt Management Service shall 実行中であることを示すインジケーターを表示する
4. If テスト実行がタイムアウトした場合（30秒）, the Prompt Management Service shall タイムアウトエラーを表示し、再実行オプションを提供する

### Requirement 4: デフォルトプロンプト初期設定・リセット

**Objective:** As a 管理者, I want システム初回起動時にデフォルトプロンプトが事前登録されており、いつでもデフォルトに戻したい, so that すぐにシステムを利用開始でき、カスタマイズ後も安全に初期状態に復帰できる

#### Acceptance Criteria
1. The Prompt Management Service shall システム初回起動時（またはマイグレーション時）に、ストーリー生成用・インポート解析用の各デフォルトプロンプトをデータベースに自動登録する（シードデータ）
2. The Prompt Management Service shall デフォルトプロンプトの内容を不変のシステム定義として保持し、管理者による削除・上書きから保護する
3. The Prompt Management Service shall 各プロンプトに対して、現在のカスタム内容とは別にデフォルト値を常に参照可能な状態で保持する
4. When 管理者がデフォルトリセットを実行した時, the Prompt Management Service shall プロンプトの内容をシステムデフォルト値に戻し、更新日時を記録する
5. When 管理者がプロンプトを閲覧した時, the Prompt Management Service shall 現在の内容がデフォルトから変更されているかどうかを視覚的に表示する
6. When 管理者がデフォルトリセット前に確認ダイアログが表示された時, the Prompt Management Service shall 現在の内容とデフォルト内容の差分を表示し、確認後にリセットを実行する

### Requirement 5: プロンプトのシステム統合

**Objective:** As a 開発者, I want サービス層からプロンプト管理システムのプロンプトを取得したい, so that ハードコードされたプロンプトの代わりに管理されたプロンプトを使用できる

#### Acceptance Criteria
1. The Prompt Management Service shall StoryGenerationServiceが使用するストーリー生成プロンプトを提供するAPIを公開する
2. The Prompt Management Service shall ImporterAnalysisServiceが使用するインポート解析プロンプトを提供するAPIを公開する
3. When サービスがプロンプトを取得した時, the Prompt Management Service shall プロンプトの本文とメタデータ（変数一覧）を返却する
4. If 指定されたキーのプロンプトが存在しない場合, the Prompt Management Service shall システムデフォルトプロンプトをフォールバックとして返却する
5. While データベースへの接続が失われた状態で, the Prompt Management Service shall インメモリキャッシュからプロンプトを提供する
