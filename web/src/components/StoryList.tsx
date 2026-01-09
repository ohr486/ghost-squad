/**
 * StoryList コンポーネント
 *
 * ストーリー一覧表示、ページネーション、フィルタリング、ソート機能を提供
 * 要件: 5.1, 5.4, 5.5, 5.14, 5.15
 */

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listStories } from "../services/storyApi";
import type { StoryStatus, Priority, ListStoriesParams } from "../types";

export interface StoryListProps {
  onStoryClick: (storyId: number) => void;
  onCreateStoryClick: () => void;
}

/**
 * ステータス表示用ラベル
 */
const STATUS_LABELS: Record<StoryStatus, string> = {
  waiting_review: "レビュー待ち",
  approved: "承認済み",
  rejected: "却下",
};

/**
 * 優先度表示用ラベル
 */
const PRIORITY_LABELS: Record<Priority, string> = {
  low: "低",
  medium: "中",
  high: "高",
  urgent: "緊急",
};

/**
 * ソート項目表示用ラベル
 */
const SORT_BY_LABELS: Record<string, string> = {
  created_at: "作成日時",
  updated_at: "更新日時",
  priority: "優先度",
  estimated_effort: "推定工数",
  assignee: "担当者",
  deadline: "期限",
};

/**
 * StoryList コンポーネント
 */
const StoryList: React.FC<StoryListProps> = ({
  onStoryClick,
  onCreateStoryClick,
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedStatus, setSelectedStatus] = useState<StoryStatus | "">("");
  const [sortBy, setSortBy] =
    useState<ListStoriesParams["sort_by"]>("created_at");
  const [sortOrder] = useState<"asc" | "desc">("desc");
  const limit = 20;

  // TanStack React Query でストーリー一覧を取得
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["stories", currentPage, selectedStatus, sortBy, sortOrder],
    queryFn: () =>
      listStories({
        page: currentPage,
        limit,
        ...(selectedStatus && { status: selectedStatus }),
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  });

  /**
   * 前ページボタンハンドラ
   */
  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  /**
   * 次ページボタンハンドラ
   */
  const handleNextPage = () => {
    if (data?.meta.has_next) {
      setCurrentPage(currentPage + 1);
    }
  };

  /**
   * 行クリックハンドラ
   */
  const handleRowClick = (storyId: number) => {
    onStoryClick(storyId);
  };

  /**
   * ステータスフィルター変更ハンドラ
   */
  const handleStatusFilterChange = (
    event: React.ChangeEvent<HTMLSelectElement>,
  ) => {
    const newStatus = event.target.value as StoryStatus | "";
    setSelectedStatus(newStatus);
    setCurrentPage(1); // フィルター変更時は1ページ目にリセット
  };

  /**
   * ソート順変更ハンドラ
   */
  const handleSortChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newSortBy = event.target.value as ListStoriesParams["sort_by"];
    setSortBy(newSortBy);
    setCurrentPage(1); // ソート変更時は1ページ目にリセット
  };

  /**
   * 説明文を100文字で省略
   */
  const truncateDescription = (
    description: string,
    maxLength: number = 100,
  ): string => {
    if (description.length <= maxLength) {
      return description;
    }
    return description.substring(0, maxLength) + "...";
  };

  /**
   * タイムスタンプをフォーマット
   */
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
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
        {/* ステータスフィルター - 常に表示 */}
        <div className="flex items-center gap-2">
          <label
            htmlFor="status-filter"
            className="text-sm font-medium text-gray-700"
          >
            ステータスフィルター
          </label>
          <select
            id="status-filter"
            value={selectedStatus}
            onChange={handleStatusFilterChange}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="ステータスフィルター"
          >
            <option value="">すべて</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-800">
            ストーリーの読み込みに失敗しました:{" "}
            {error instanceof Error ? error.message : "不明なエラー"}
          </p>
        </div>
      </div>
    );
  }

  const hasData = data && data.data && data.data.length > 0;

  return (
    <div className="space-y-4">
      {/* ヘッダー: フィルター、ソート、新規作成ボタン */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          {/* ステータスフィルター */}
          <div className="flex items-center gap-2">
            <label
              htmlFor="status-filter"
              className="text-sm font-medium text-gray-700"
            >
              ステータスフィルター
            </label>
            <select
              id="status-filter"
              value={selectedStatus}
              onChange={handleStatusFilterChange}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="ステータスフィルター"
            >
              <option value="">すべて</option>
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* ソート順 */}
          <div className="flex items-center gap-2">
            <label
              htmlFor="sort-select"
              className="text-sm font-medium text-gray-700"
            >
              ソート順
            </label>
            <select
              id="sort-select"
              value={sortBy}
              onChange={handleSortChange}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="ソート順"
            >
              {Object.entries(SORT_BY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 新規ストーリー作成ボタン */}
        <button
          onClick={onCreateStoryClick}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          新規ストーリー作成
        </button>
      </div>

      {/* コンテンツエリア - 条件付きレンダリング */}
      {!hasData ? (
        <div className="p-8 text-center text-gray-600 bg-white rounded-lg border border-gray-200">
          ストーリーが見つかりませんでした。
        </div>
      ) : (
        <>
          {/* ストーリーテーブル */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    タイトル
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    説明
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    優先度
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ステータス
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    作成日時
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.data.map((story) => (
                  <tr
                    key={story.id}
                    onClick={() => handleRowClick(story.id)}
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        handleRowClick(story.id);
                      }
                    }}
                    className="hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{story.id}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {story.title}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {truncateDescription(story.description)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-purple-100 text-purple-800">
                        {PRIORITY_LABELS[story.priority]}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {STATUS_LABELS[story.status]}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatTimestamp(story.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* ページネーションコントロール */}
          <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
            <div className="flex flex-1 justify-between sm:hidden">
              <button
                onClick={handlePrevPage}
                disabled={currentPage === 1}
                className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                前へ
              </button>
              <button
                onClick={handleNextPage}
                disabled={!data.meta.has_next}
                className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                次へ
              </button>
            </div>
            <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  全 <span className="font-medium">{data.meta.total}</span> 件中{" "}
                  <span className="font-medium">
                    {(currentPage - 1) * limit + 1}
                  </span>{" "}
                  -{" "}
                  <span className="font-medium">
                    {Math.min(currentPage * limit, data.meta.total)}
                  </span>{" "}
                  件を表示
                </p>
              </div>
              <div>
                <nav
                  className="isolate inline-flex -space-x-px rounded-md shadow-sm"
                  aria-label="Pagination"
                >
                  <button
                    onClick={handlePrevPage}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="前のページへ"
                  >
                    前へ
                  </button>
                  <span className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300">
                    {currentPage}
                  </span>
                  <button
                    onClick={handleNextPage}
                    disabled={!data.meta.has_next}
                    className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="次のページへ"
                  >
                    次へ
                  </button>
                </nav>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default StoryList;
