/**
 * AIProviderListComponent コンポーネント
 *
 * AIプロバイダーの一覧表示とデフォルト設定機能を提供
 * 要件: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listAIProviders,
  setDefaultAIProvider,
} from "../../services/importerApi";
import type {
  AIProviderStatus,
  ImporterErrorResponse,
} from "../../types/importer";

/**
 * 初期化状態の表示用ラベル
 */
const INITIALIZATION_LABELS: Record<string, string> = {
  initialized: "接続済み",
  error: "エラー",
};

/**
 * AIProviderListComponent プロパティ
 */
export interface AIProviderListComponentProps {}

/**
 * AIProviderListComponent コンポーネント
 *
 * AIプロバイダー一覧テーブルの表示とデフォルト選択操作を管理
 */
const AIProviderListComponent: React.FC<AIProviderListComponentProps> = () => {
  const queryClient = useQueryClient();
  const [isSettingDefault, setIsSettingDefault] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // AIプロバイダー一覧取得
  const {
    data: providersResponse,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["ai-providers"],
    queryFn: listAIProviders,
  });

  // デフォルト設定mutation
  const setDefaultMutation = useMutation({
    mutationFn: setDefaultAIProvider,
    onMutate: () => {
      setIsSettingDefault(true);
      setErrorMessage(null);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-providers"] });
    },
    onError: (error: ImporterErrorResponse) => {
      setErrorMessage(
        error.errors?.[0]?.message || "デフォルト設定に失敗しました",
      );
    },
    onSettled: () => {
      setIsSettingDefault(false);
    },
  });

  /**
   * デフォルト設定ハンドラ
   */
  const handleSetDefault = (provider: AIProviderStatus) => {
    if (!provider.is_default) {
      setDefaultMutation.mutate(provider.provider_type);
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
        <h2 className="text-lg font-semibold text-gray-900">AIプロバイダー</h2>
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-800">
            AIプロバイダーの読み込みに失敗しました:{" "}
            {error instanceof Error ? error.message : "不明なエラー"}
          </p>
        </div>
      </div>
    );
  }

  const providers = providersResponse?.data || [];
  const hasData = providers.length > 0;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">AIプロバイダー</h2>

      {/* エラーメッセージ表示 */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-800">{errorMessage}</p>
        </div>
      )}

      {/* プロバイダーなしの場合 */}
      {!hasData ? (
        <div className="p-8 text-center text-gray-600 bg-white rounded-lg border border-gray-200">
          登録されているAIプロバイダーはありません
        </div>
      ) : (
        /* プロバイダーテーブル */
        <div className="overflow-x-auto">
          <table
            className="min-w-full divide-y divide-gray-200"
            aria-label="AIプロバイダー一覧"
          >
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  プロバイダー
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  モデル
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状態
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  デフォルト
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {providers.map((provider) => (
                <tr key={provider.provider_type}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {provider.provider_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {provider.model}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          provider.initialized
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {provider.initialized
                          ? INITIALIZATION_LABELS.initialized
                          : INITIALIZATION_LABELS.error}
                      </span>
                      {provider.error_message && (
                        <span className="mt-1 text-xs text-red-600">
                          {provider.error_message}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="radio"
                      name="default-provider"
                      checked={provider.is_default}
                      disabled={isSettingDefault}
                      onChange={() => handleSetDefault(provider)}
                      aria-label={`${provider.provider_type}をデフォルトに設定`}
                      className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
                    />
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

export default AIProviderListComponent;
