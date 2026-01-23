/**
 * PluginListComponent コンポーネント
 *
 * データソースプラグインの一覧表示と有効/無効切り替え機能を提供
 * 要件: 1.1, 1.2
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listPlugins,
  enablePlugin,
  disablePlugin,
} from "../../services/importerApi";
import type { PluginStatus, ImporterErrorResponse } from "../../types/importer";

/**
 * 初期化状態の表示用ラベル
 */
const INITIALIZATION_LABELS: Record<string, string> = {
  initialized: "初期化済み",
  error: "エラー",
};

/**
 * PluginListComponent プロパティ
 */
export interface PluginListComponentProps {}

/**
 * PluginListComponent コンポーネント
 *
 * プラグイン一覧テーブルの表示と有効/無効トグル操作を管理
 */
const PluginListComponent: React.FC<PluginListComponentProps> = () => {
  const queryClient = useQueryClient();
  const [togglingPlugins, setTogglingPlugins] = useState<Set<string>>(
    new Set(),
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // プラグイン一覧取得
  const {
    data: pluginsResponse,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["plugins"],
    queryFn: listPlugins,
  });

  // プラグイン有効化mutation
  const enableMutation = useMutation({
    mutationFn: enablePlugin,
    onMutate: (pluginType: string) => {
      setTogglingPlugins((prev) => new Set(prev).add(pluginType));
      setErrorMessage(null);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plugins"] });
    },
    onError: (error: ImporterErrorResponse, pluginType: string) => {
      setErrorMessage(
        error.errors?.[0]?.message || "プラグインの有効化に失敗しました",
      );
      setTogglingPlugins((prev) => {
        const newSet = new Set(prev);
        newSet.delete(pluginType);
        return newSet;
      });
    },
    onSettled: (_data, _error, pluginType) => {
      setTogglingPlugins((prev) => {
        const newSet = new Set(prev);
        newSet.delete(pluginType);
        return newSet;
      });
    },
  });

  // プラグイン無効化mutation
  const disableMutation = useMutation({
    mutationFn: disablePlugin,
    onMutate: (pluginType: string) => {
      setTogglingPlugins((prev) => new Set(prev).add(pluginType));
      setErrorMessage(null);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plugins"] });
    },
    onError: (error: ImporterErrorResponse, pluginType: string) => {
      setErrorMessage(
        error.errors?.[0]?.message || "プラグインの無効化に失敗しました",
      );
      setTogglingPlugins((prev) => {
        const newSet = new Set(prev);
        newSet.delete(pluginType);
        return newSet;
      });
    },
    onSettled: (_data, _error, pluginType) => {
      setTogglingPlugins((prev) => {
        const newSet = new Set(prev);
        newSet.delete(pluginType);
        return newSet;
      });
    },
  });

  /**
   * トグル切り替えハンドラ
   */
  const handleToggle = async (plugin: PluginStatus) => {
    if (plugin.enabled) {
      disableMutation.mutate(plugin.plugin_type);
    } else {
      enableMutation.mutate(plugin.plugin_type);
    }
  };

  /**
   * ローディング状態
   */
  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }

  /**
   * エラー状態
   */
  if (isError) {
    return (
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">
          データソースプラグイン
        </h2>
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-800">
            プラグインの読み込みに失敗しました:{" "}
            {error instanceof Error ? error.message : "不明なエラー"}
          </p>
        </div>
      </div>
    );
  }

  const plugins = pluginsResponse?.data || [];
  const hasData = plugins.length > 0;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">
        データソースプラグイン
      </h2>

      {/* エラーメッセージ表示 */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-800">{errorMessage}</p>
        </div>
      )}

      {/* プラグインなしの場合 */}
      {!hasData ? (
        <div className="p-8 text-center text-gray-600 bg-white rounded-lg border border-gray-200">
          登録されているプラグインはありません
        </div>
      ) : (
        /* プラグインテーブル */
        <div className="overflow-x-auto">
          <table
            className="min-w-full divide-y divide-gray-200"
            aria-label="データソースプラグイン一覧"
          >
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  プラグイン
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状態
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  有効/無効
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {plugins.map((plugin) => (
                <tr key={plugin.plugin_type}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {plugin.plugin_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          plugin.initialized
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {plugin.initialized
                          ? INITIALIZATION_LABELS.initialized
                          : INITIALIZATION_LABELS.error}
                      </span>
                      {plugin.error_message && (
                        <span className="mt-1 text-xs text-red-600">
                          {plugin.error_message}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={plugin.enabled}
                        disabled={togglingPlugins.has(plugin.plugin_type)}
                        onChange={() => handleToggle(plugin)}
                        aria-label={`${plugin.plugin_type}プラグインの有効/無効切り替え`}
                      />
                      <div
                        className={`w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 ${
                          togglingPlugins.has(plugin.plugin_type)
                            ? "opacity-50"
                            : ""
                        }`}
                      ></div>
                    </label>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PluginListComponent;
