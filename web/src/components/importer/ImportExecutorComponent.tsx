/**
 * ImportExecutorComponent コンポーネント
 *
 * インポート実行と結果表示機能を提供
 * 要件: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5
 */

import React, { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  listPlugins,
  listAIProviders,
  executeImport,
} from "../../services/importerApi";
import type { ImportResult, ImporterErrorResponse } from "../../types/importer";

/**
 * ImportExecutorComponent プロパティ
 */
export interface ImportExecutorComponentProps {}

/**
 * ImportExecutorComponent コンポーネント
 *
 * データソース選択、AIプロバイダー選択、インポート実行、結果表示を管理
 */
const ImportExecutorComponent: React.FC<ImportExecutorComponentProps> = () => {
  const [selectedPlugin, setSelectedPlugin] = useState<string>("");
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [result, setResult] = useState<ImportResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // プラグイン一覧取得
  const {
    data: pluginsResponse,
    isLoading: isLoadingPlugins,
    isError: isPluginsError,
    error: pluginsError,
  } = useQuery({
    queryKey: ["plugins"],
    queryFn: listPlugins,
  });

  // AIプロバイダー一覧取得
  const {
    data: providersResponse,
    isLoading: isLoadingProviders,
    isError: isProvidersError,
    error: providersError,
  } = useQuery({
    queryKey: ["ai-providers"],
    queryFn: listAIProviders,
  });

  // インポート実行mutation
  const executeMutation = useMutation({
    mutationFn: executeImport,
    onMutate: () => {
      setResult(null);
      setErrorMessage(null);
    },
    onSuccess: (data: ImportResult) => {
      setResult(data);
    },
    onError: (error: ImporterErrorResponse) => {
      setErrorMessage(
        error.errors?.[0]?.message || "インポートの実行に失敗しました",
      );
    },
  });

  /**
   * インポート実行ハンドラ
   */
  const handleExecute = () => {
    executeMutation.mutate({
      plugin_type: selectedPlugin,
      ai_provider_type: selectedProvider || null,
    });
  };

  /**
   * ローディング状態
   */
  if (isLoadingPlugins || isLoadingProviders) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }

  /**
   * エラー状態
   */
  if (isPluginsError) {
    return (
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">インポート実行</h2>
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-800">
            プラグインの読み込みに失敗しました:{" "}
            {pluginsError instanceof Error
              ? pluginsError.message
              : "不明なエラー"}
          </p>
        </div>
      </div>
    );
  }

  const plugins = pluginsResponse?.data || [];
  const providers = providersResponse?.data || [];
  const enabledPlugins = plugins.filter((p) => p.enabled && p.initialized);
  const enabledProviders = providers.filter((p) => p.enabled && p.initialized);

  const isExecuting = executeMutation.isPending;
  const canExecute = selectedPlugin !== "" && !isExecuting;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">インポート実行</h2>

      {/* AIプロバイダー読み込みエラー表示 */}
      {isProvidersError && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-yellow-800">
            AIプロバイダーの読み込みに失敗しました:{" "}
            {providersError instanceof Error
              ? providersError.message
              : "不明なエラー"}
          </p>
          <p className="text-sm text-yellow-700 mt-1">
            プラグインのみを使用してインポートを実行できます
          </p>
        </div>
      )}

      {/* エラーメッセージ表示 */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-800">{errorMessage}</p>
        </div>
      )}

      {/* 実行フォーム */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* データソース選択 */}
          <div>
            <label
              htmlFor="plugin-select"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              データソース
            </label>
            <select
              id="plugin-select"
              value={selectedPlugin}
              onChange={(e) => setSelectedPlugin(e.target.value)}
              disabled={isExecuting}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="データソース"
            >
              <option value="">選択してください</option>
              {enabledPlugins.map((plugin) => (
                <option key={plugin.plugin_type} value={plugin.plugin_type}>
                  {plugin.plugin_type}
                </option>
              ))}
            </select>
          </div>

          {/* AIプロバイダー選択 */}
          <div>
            <label
              htmlFor="provider-select"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              AIプロバイダー（オプション）
            </label>
            <select
              id="provider-select"
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              disabled={isExecuting}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="AIプロバイダー（オプション）"
            >
              <option value="">デフォルトを使用</option>
              {enabledProviders.map((provider) => (
                <option
                  key={provider.provider_type}
                  value={provider.provider_type}
                >
                  {provider.provider_type}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 実行ボタン */}
        <div className="mt-4">
          <button
            onClick={handleExecute}
            disabled={!canExecute}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExecuting ? "実行中..." : "インポート実行"}
          </button>
        </div>
      </div>

      {/* 実行結果表示 */}
      {result && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-md font-semibold text-gray-900 mb-4">実行結果</h3>

          {/* 結果サマリー */}
          <dl className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded">
              <dt className="text-sm font-medium text-gray-500">取得件数</dt>
              <dd className="text-2xl font-semibold text-gray-900">
                {result.total_fetched}
              </dd>
            </div>
            <div className="bg-green-50 p-4 rounded">
              <dt className="text-sm font-medium text-green-600">
                インポート成功
              </dt>
              <dd className="text-2xl font-semibold text-green-700">
                {result.total_imported}
              </dd>
            </div>
            <div className="bg-yellow-50 p-4 rounded">
              <dt className="text-sm font-medium text-yellow-600">
                スキップ（重複）
              </dt>
              <dd className="text-2xl font-semibold text-yellow-700">
                {result.total_skipped}
              </dd>
            </div>
            <div className="bg-red-50 p-4 rounded">
              <dt className="text-sm font-medium text-red-600">失敗</dt>
              <dd className="text-2xl font-semibold text-red-700">
                {result.total_failed}
              </dd>
            </div>
          </dl>

          {/* エラー詳細 */}
          {result.errors.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">
                エラー詳細
              </h4>
              <div className="space-y-2">
                {result.errors.map((error, index) => (
                  <div
                    key={index}
                    className="p-3 bg-red-50 border border-red-200 rounded text-sm"
                  >
                    <span className="font-medium text-red-800">
                      [{error.error_code}]
                    </span>{" "}
                    <span className="text-red-700">{error.error_message}</span>
                    <span className="text-red-500 ml-2 text-xs">
                      (ID: {error.source_id})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ImportExecutorComponent;
