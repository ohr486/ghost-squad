import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listPrompts } from "../services/promptApi";
import type { PromptCategory, PromptResponse } from "../types/prompt";

export interface PromptListProps {
  onPromptClick: (promptKey: string) => void;
}

const CATEGORY_LABELS: Record<PromptCategory, string> = {
  story_generation: "ストーリー生成",
  import_analysis: "インポート解析",
  general: "汎用",
};

const PromptList: React.FC<PromptListProps> = ({ onPromptClick }) => {
  const [selectedCategory, setSelectedCategory] = useState<
    PromptCategory | ""
  >("");

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["prompts", selectedCategory],
    queryFn: () =>
      listPrompts(selectedCategory ? selectedCategory : undefined),
  });

  const handleRowClick = (prompt: PromptResponse) => {
    onPromptClick(prompt.key);
  };

  const handleCategoryFilterChange = (
    event: React.ChangeEvent<HTMLSelectElement>,
  ) => {
    setSelectedCategory(event.target.value as PromptCategory | "");
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString("ja-JP");
  };

  // Category filter component (always visible)
  const categoryFilter = (
    <div className="flex items-center gap-2">
      <label
        htmlFor="category-filter"
        className="text-sm font-medium text-gray-700"
      >
        カテゴリフィルター
      </label>
      <select
        id="category-filter"
        value={selectedCategory}
        onChange={handleCategoryFilterChange}
        className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label="カテゴリフィルター"
      >
        <option value="">すべて</option>
        {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
    </div>
  );

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-4">
        {categoryFilter}
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-800">
            プロンプトの読み込みに失敗しました:{" "}
            {error instanceof Error ? error.message : "不明なエラー"}
          </p>
        </div>
      </div>
    );
  }

  const hasData = data && data.data && data.data.length > 0;

  return (
    <div className="space-y-4">
      {categoryFilter}

      {!hasData ? (
        <div className="p-8 text-center text-gray-600 bg-white rounded-lg border border-gray-200">
          プロンプトが見つかりませんでした。
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  名前
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  カテゴリ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  最終更新日時
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  変更状態
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.data.map((prompt) => (
                <tr
                  key={prompt.key}
                  onClick={() => handleRowClick(prompt)}
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      handleRowClick(prompt);
                    }
                  }}
                  className="hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    {prompt.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                      {CATEGORY_LABELS[prompt.category]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatTimestamp(prompt.updated_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {prompt.is_modified ? (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                        変更済み
                      </span>
                    ) : (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        デフォルト
                      </span>
                    )}
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

export default PromptList;
