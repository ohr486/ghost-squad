/**
 * ErrorStatsComponent コンポーネント
 *
 * エラー統計の表示機能を提供
 * 要件: 5.4
 */

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { getErrorStats } from "../../services/importerApi";

/**
 * ErrorStatsComponent プロパティ
 */
export interface ErrorStatsComponentProps {}

/**
 * ErrorStatsComponent コンポーネント
 *
 * エラー統計テーブルの表示と自動更新を管理
 */
const ErrorStatsComponent: React.FC<ErrorStatsComponentProps> = () => {
  // エラー統計取得（30秒ごとに自動更新）
  const {
    data: statsResponse,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["error-stats"],
    queryFn: () => getErrorStats(),
    refetchInterval: 30000, // 30秒ごとに自動更新
  });

  /**
   * 日時をフォーマット
   */
  const formatDateTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleString("ja-JP");
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
        <h2 className="text-lg font-semibold text-gray-900">エラー統計</h2>
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-800">
            エラー統計の読み込みに失敗しました:{" "}
            {error instanceof Error ? error.message : "不明なエラー"}
          </p>
        </div>
      </div>
    );
  }

  const stats = statsResponse?.data || [];
  const hasData = stats.length > 0;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">エラー統計</h2>

      {/* エラーなしの場合 */}
      {!hasData ? (
        <div className="p-8 text-center text-gray-600 bg-white rounded-lg border border-gray-200">
          エラーはありません
        </div>
      ) : (
        /* エラー統計テーブル */
        <div className="overflow-x-auto">
          <table
            className="min-w-full divide-y divide-gray-200"
            aria-label="エラー統計一覧"
          >
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  エラーコード
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  発生回数
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  最終発生
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {stats.map((stat) => (
                <tr key={stat.error_code}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                      {stat.error_code}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {stat.count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDateTime(stat.last_occurred)}
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

export default ErrorStatsComponent;
