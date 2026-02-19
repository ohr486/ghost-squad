import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  getPrompt,
  updatePrompt,
  testPrompt,
  resetPrompt,
  acquireLock,
  releaseLock,
} from "../services/promptApi";
import type {
  PromptCategory,
  TestPromptResult,
} from "../types/prompt";

export interface PromptDetailProps {
  promptKey: string;
}

const CATEGORY_LABELS: Record<PromptCategory, string> = {
  story_generation: "ストーリー生成",
  import_analysis: "インポート解析",
  general: "汎用",
};

const PromptDetail: React.FC<PromptDetailProps> = ({ promptKey }) => {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [showResetDialog, setShowResetDialog] = useState(false);

  // テスト実行用state
  const [testVariables, setTestVariables] = useState<Record<string, string>>(
    {},
  );
  const [testProvider, setTestProvider] = useState<string>("");
  const [testResult, setTestResult] = useState<TestPromptResult | null>(null);

  // Fetch prompt details
  const {
    data: prompt,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["prompt", promptKey],
    queryFn: () => getPrompt(promptKey),
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (content: string) =>
      updatePrompt(promptKey, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompt", promptKey] });
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      setIsEditing(false);
      releaseLock(promptKey).catch(() => {});
      toast.success("プロンプトを更新しました");
    },
    onError: () => {
      toast.error("プロンプトの更新に失敗しました");
    },
  });

  // Test execution mutation
  const testMutation = useMutation({
    mutationFn: () =>
      testPrompt({
        content: prompt?.content || "",
        variables: testVariables,
        ...(testProvider ? { provider: testProvider as "openai" | "anthropic" } : {}),
      }),
    onSuccess: (result) => {
      setTestResult(result);
    },
    onError: () => {
      toast.error("テスト実行に失敗しました");
    },
  });

  // Reset mutation
  const resetMutation = useMutation({
    mutationFn: () => resetPrompt(promptKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompt", promptKey] });
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      setShowResetDialog(false);
      toast.success("プロンプトをデフォルトにリセットしました");
    },
    onError: () => {
      toast.error("リセットに失敗しました");
    },
  });

  const handleEdit = async () => {
    if (!prompt) return;
    try {
      await acquireLock(promptKey, { user_id: "current_user" });
      setEditedContent(prompt.content);
      setIsEditing(true);
    } catch {
      toast.error("編集ロックの取得に失敗しました");
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedContent("");
    releaseLock(promptKey).catch(() => {});
  };

  const handleSave = () => {
    if (editedContent.trim()) {
      updateMutation.mutate(editedContent);
    }
  };

  const handleTestExecute = () => {
    testMutation.mutate();
  };

  const handleTestVariableChange = (variable: string, value: string) => {
    setTestVariables((prev) => ({ ...prev, [variable]: value }));
  };

  const handleResetClick = () => {
    setShowResetDialog(true);
  };

  const handleConfirmReset = () => {
    resetMutation.mutate();
  };

  const handleCancelReset = () => {
    setShowResetDialog(false);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <p className="text-gray-600">読み込み中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <p className="text-red-600">プロンプトの取得に失敗しました</p>
      </div>
    );
  }

  if (!prompt) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white shadow rounded-lg p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">プロンプト詳細</h1>
          <h2 className="text-xl font-semibold mb-2">{prompt.name}</h2>
          {prompt.description && (
            <p className="text-gray-600 mb-2">{prompt.description}</p>
          )}
          <div className="text-sm text-gray-600">
            <p>
              <span className="font-semibold">キー:</span> {prompt.key}
            </p>
            <p>
              <span className="font-semibold">カテゴリ:</span>{" "}
              {CATEGORY_LABELS[prompt.category]}
            </p>
            <p>
              <span className="font-semibold">作成日時:</span>{" "}
              {new Date(prompt.created_at).toLocaleString("ja-JP")}
            </p>
            <p>
              <span className="font-semibold">更新日時:</span>{" "}
              {new Date(prompt.updated_at).toLocaleString("ja-JP")}
            </p>
            <p>
              <span className="font-semibold">変更状態:</span>{" "}
              {prompt.is_modified ? (
                <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                  変更済み
                </span>
              ) : (
                <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                  デフォルト
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Edit Lock Warning */}
        {prompt.editing_by && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-yellow-800">
              {prompt.editing_by} が編集中です
              {prompt.editing_since && (
                <span className="text-sm text-yellow-600 ml-2">
                  （{new Date(prompt.editing_since).toLocaleString("ja-JP")}
                  から）
                </span>
              )}
            </p>
          </div>
        )}

        {/* Variables */}
        {prompt.variables.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2">変数</h3>
            <div className="flex flex-wrap gap-2">
              {prompt.variables.map((variable) => (
                <span
                  key={variable}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                >
                  {variable}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">プロンプト本文</h3>
          {isEditing ? (
            <textarea
              className="w-full p-3 border rounded-md min-h-[300px] font-mono text-sm"
              aria-label="プロンプト本文を編集"
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
            />
          ) : (
            <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-md text-sm font-mono">
              {prompt.content}
            </pre>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mb-6">
          {isEditing ? (
            <>
              <button
                onClick={handleSave}
                disabled={updateMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                保存
              </button>
              <button
                onClick={handleCancelEdit}
                disabled={updateMutation.isPending}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 disabled:opacity-50"
              >
                キャンセル
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleEdit}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                編集
              </button>
              {prompt.is_modified && (
                <button
                  onClick={handleResetClick}
                  className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
                >
                  デフォルトにリセット
                </button>
              )}
            </>
          )}
        </div>

        {/* Test Execution Panel */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold mb-4">テスト実行</h3>

          {/* Variable inputs */}
          {prompt.variables.length > 0 && (
            <div className="mb-4 space-y-3">
              {prompt.variables.map((variable) => (
                <div key={variable}>
                  <label
                    htmlFor={`test-var-${variable}`}
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    {variable}
                  </label>
                  <input
                    id={`test-var-${variable}`}
                    type="text"
                    aria-label={variable}
                    value={testVariables[variable] || ""}
                    onChange={(e) =>
                      handleTestVariableChange(variable, e.target.value)
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder={`${variable}の値を入力`}
                  />
                </div>
              ))}
            </div>
          )}

          {/* Provider selection */}
          <div className="mb-4">
            <label
              htmlFor="test-provider"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              AIプロバイダー
            </label>
            <select
              id="test-provider"
              aria-label="AIプロバイダー"
              value={testProvider}
              onChange={(e) => setTestProvider(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">デフォルト</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>

          {/* Execute button */}
          <button
            onClick={handleTestExecute}
            disabled={testMutation.isPending}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
          >
            {testMutation.isPending ? "実行中..." : "実行"}
          </button>

          {/* Test result */}
          {testResult && (
            <div className="mt-4 p-4 bg-gray-50 border rounded-md">
              <h4 className="font-semibold mb-2">テスト結果</h4>
              <pre className="whitespace-pre-wrap text-sm mb-2">
                {testResult.output}
              </pre>
              <div className="text-xs text-gray-500">
                <span>プロバイダー: {testResult.provider}</span>
                <span className="ml-4">モデル: {testResult.model}</span>
                <span className="ml-4">実行時間: {testResult.elapsed_ms}ms</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Reset Confirmation Dialog */}
      {showResetDialog && prompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div
            className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
            role="dialog"
            aria-modal="true"
            aria-labelledby="resetDialogTitle"
          >
            <h3
              id="resetDialogTitle"
              className="text-lg font-semibold mb-4"
            >
              デフォルトにリセットしますか？
            </h3>

            <div className="mb-4">
              <h4 className="font-medium mb-1">現在の内容:</h4>
              <pre className="whitespace-pre-wrap bg-red-50 p-3 rounded border border-red-200 text-sm font-mono max-h-40 overflow-y-auto">
                {prompt.content}
              </pre>
            </div>

            <div className="mb-4">
              <h4 className="font-medium mb-1">デフォルト内容:</h4>
              <pre className="whitespace-pre-wrap bg-green-50 p-3 rounded border border-green-200 text-sm font-mono max-h-40 overflow-y-auto">
                {prompt.default_content}
              </pre>
            </div>

            <div className="flex gap-2 justify-end">
              <button
                onClick={handleCancelReset}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                キャンセル
              </button>
              <button
                onClick={handleConfirmReset}
                disabled={resetMutation.isPending}
                className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
              >
                リセット実行
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PromptDetail;
