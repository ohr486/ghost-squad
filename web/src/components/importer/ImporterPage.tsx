/**
 * ImporterPage コンポーネント
 *
 * インポーター機能の管理画面を提供
 * 要件: MVP UI
 */

import React from "react";
import ImportExecutorComponent from "./ImportExecutorComponent";
import PluginListComponent from "./PluginListComponent";
import AIProviderListComponent from "./AIProviderListComponent";
import ErrorStatsComponent from "./ErrorStatsComponent";

/**
 * ImporterPage プロパティ
 */
export interface ImporterPageProps {}

/**
 * ImporterPage コンポーネント
 *
 * プラグイン、AIプロバイダー、インポート実行、エラー統計の各コンポーネントを統合
 */
const ImporterPage: React.FC<ImporterPageProps> = () => {
  return (
    <main className="importer-page space-y-8 p-6" role="main">
      <h1 className="text-2xl font-bold text-gray-900">インポーター管理</h1>

      {/* インポート実行セクション */}
      <section className="importer-section">
        <ImportExecutorComponent />
      </section>

      {/* プラグイン一覧セクション */}
      <section className="plugin-section">
        <PluginListComponent />
      </section>

      {/* AIプロバイダー一覧セクション */}
      <section className="ai-provider-section">
        <AIProviderListComponent />
      </section>

      {/* エラー統計セクション */}
      <section className="stats-section">
        <ErrorStatsComponent />
      </section>
    </main>
  );
};

export default ImporterPage;
