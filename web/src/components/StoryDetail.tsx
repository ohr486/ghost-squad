/**
 * StoryDetail コンポーネント
 *
 * ストーリー詳細表示・編集・承認・却下機能を提供
 * - TanStack React Query でストーリー詳細を取得
 * - 読み取りモードと編集モードの切り替え
 * - インライン編集フォーム
 * - 承認・却下ボタン（ステータス=waiting_reviewのみ表示）
 * - 確認ダイアログ（承認・却下・削除）
 * - ローディングインジケーター、成功・エラーメッセージ
 *
 * 要件: 2.5, 2.6, 2.7, 2.8, 2.9, 3.1, 3.4, 3.5, 5.2, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  getStory,
  updateStory,
  deleteStory,
  approveStory,
  rejectStory,
} from "../services/storyApi";
import type { UpdateStoryRequest, Priority, StoryStatus } from "../types";

/**
 * StoryDetail プロパティ
 */
export interface StoryDetailProps {
  /** ストーリーID */
  storyId: number;
  /** 戻るボタンのコールバック */
  onBack?: () => void;
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
 * StoryDetail コンポーネント
 */
const StoryDetail: React.FC<StoryDetailProps> = ({ storyId, onBack }) => {
  const queryClient = useQueryClient();

  // UI状態管理
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState("");
  const [editedDescription, setEditedDescription] = useState("");
  const [editedPriority, setEditedPriority] = useState<Priority>("medium");
  const [editedEstimatedEffort, setEditedEstimatedEffort] = useState<
    string | undefined
  >("");
  const [editedAssignee, setEditedAssignee] = useState("");
  const [editedDeadline, setEditedDeadline] = useState("");

  // ダイアログ状態管理
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [rejectReasonError, setRejectReasonError] = useState("");

  // ストーリー詳細取得
  const {
    data: story,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["story", storyId],
    queryFn: () => getStory(storyId),
  });

  // 更新mutation
  const updateMutation = useMutation({
    mutationFn: (data: UpdateStoryRequest) => updateStory(storyId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["story", storyId] });
      queryClient.invalidateQueries({ queryKey: ["stories"] });
      setIsEditing(false);
      toast.success("ストーリーを更新しました");
    },
    onError: () => {
      toast.error("ストーリーの更新に失敗しました");
    },
  });

  // 削除mutation
  const deleteMutation = useMutation({
    mutationFn: () => deleteStory(storyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stories"] });
      setShowDeleteDialog(false);
      toast.success("ストーリーを削除しました");
      onBack?.();
    },
    onError: () => {
      toast.error("ストーリーの削除に失敗しました");
    },
  });

  // 承認mutation
  const approveMutation = useMutation({
    mutationFn: () => approveStory(storyId, { approver: "current_user" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["story", storyId] });
      queryClient.invalidateQueries({ queryKey: ["stories"] });
      setShowApproveDialog(false);
      toast.success("ストーリーを承認しました");
    },
    onError: () => {
      toast.error("ストーリーの承認に失敗しました");
    },
  });

  // 却下mutation
  const rejectMutation = useMutation({
    mutationFn: (reason: string) =>
      rejectStory(storyId, { rejector: "current_user", reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["story", storyId] });
      queryClient.invalidateQueries({ queryKey: ["stories"] });
      setShowRejectDialog(false);
      setRejectReason("");
      setRejectReasonError("");
      toast.success("ストーリーを却下しました");
    },
    onError: () => {
      toast.error("ストーリーの却下に失敗しました");
    },
  });

  // 編集モード開始
  const handleEdit = () => {
    if (story) {
      setEditedTitle(story.title);
      setEditedDescription(story.description);
      setEditedPriority(story.priority);
      setEditedEstimatedEffort(story.estimated_effort?.toString() || "");
      setEditedAssignee(story.assignee || "");
      setEditedDeadline(story.deadline ? story.deadline.split("T")[0] : "");
      setIsEditing(true);
    }
  };

  // 編集キャンセル
  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedTitle("");
    setEditedDescription("");
    setEditedPriority("medium");
    setEditedEstimatedEffort("");
    setEditedAssignee("");
    setEditedDeadline("");
  };

  // 保存
  const handleSave = () => {
    const updateData: UpdateStoryRequest = {
      title: editedTitle,
      description: editedDescription,
      priority: editedPriority,
    };

    if (editedEstimatedEffort) {
      updateData.estimated_effort = parseFloat(editedEstimatedEffort);
    }

    if (editedAssignee) {
      updateData.assignee = editedAssignee;
    }

    if (editedDeadline) {
      updateData.deadline = new Date(editedDeadline).toISOString();
    }

    updateMutation.mutate(updateData);
  };

  // 承認確認
  const handleConfirmApprove = () => {
    approveMutation.mutate();
  };

  // 承認キャンセル
  const handleCancelApprove = () => {
    setShowApproveDialog(false);
  };

  // 却下確認
  const handleConfirmReject = () => {
    if (!rejectReason.trim()) {
      setRejectReasonError("却下理由は必須です");
      return;
    }
    setRejectReasonError("");
    rejectMutation.mutate(rejectReason.trim());
  };

  // 却下キャンセル
  const handleCancelReject = () => {
    setShowRejectDialog(false);
    setRejectReason("");
    setRejectReasonError("");
  };

  // 削除確認
  const handleConfirmDelete = () => {
    deleteMutation.mutate();
  };

  // 削除キャンセル
  const handleCancelDelete = () => {
    setShowDeleteDialog(false);
  };

  // タイムスタンプフォーマット
  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString("ja-JP");
  };

  // ローディング状態
  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <p className="text-gray-600">読み込み中...</p>
      </div>
    );
  }

  // エラー状態
  if (error) {
    return (
      <div className="p-8">
        <p className="text-red-600">ストーリーの取得に失敗しました</p>
      </div>
    );
  }

  // ストーリーが存在しない場合
  if (!story) {
    return null;
  }

  // 承認・却下ボタン表示可否
  const canApproveOrReject = story.status === "waiting_review";

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white shadow rounded-lg p-6">
        {/* ヘッダー */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">ストーリー詳細</h1>
          <div className="text-sm text-gray-600">
            <p>
              <span className="font-semibold">ID:</span> {story.id}
            </p>
            <p>
              <span className="font-semibold">問い合わせID:</span>{" "}
              {story.inquiry_id}
            </p>
            <p>
              <span className="font-semibold">ステータス:</span>{" "}
              <span
                className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                  story.status === "waiting_review"
                    ? "bg-yellow-100 text-yellow-800"
                    : story.status === "approved"
                      ? "bg-green-100 text-green-800"
                      : "bg-red-100 text-red-800"
                }`}
              >
                {STATUS_LABELS[story.status]}
              </span>
            </p>
            <p>
              <span className="font-semibold">優先度:</span>{" "}
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800">
                {PRIORITY_LABELS[story.priority]}
              </span>
            </p>
            <p>
              <span className="font-semibold">作成日時:</span>{" "}
              {formatTimestamp(story.created_at)}
            </p>
            <p>
              <span className="font-semibold">更新日時:</span>{" "}
              {formatTimestamp(story.updated_at)}
            </p>
            {story.estimated_effort && (
              <p>
                <span className="font-semibold">推定工数:</span>{" "}
                {story.estimated_effort}時間
              </p>
            )}
            {story.assignee && (
              <p>
                <span className="font-semibold">担当者:</span> {story.assignee}
              </p>
            )}
            {story.deadline && (
              <p>
                <span className="font-semibold">期限:</span>{" "}
                {formatTimestamp(story.deadline)}
              </p>
            )}
          </div>
        </div>

        {/* タイトルと説明 */}
        <div className="mb-6">
          {isEditing ? (
            <div className="space-y-4">
              {/* タイトル編集 */}
              <div>
                <label
                  htmlFor="edit-title"
                  className="block text-sm font-medium mb-2"
                >
                  タイトル
                </label>
                <input
                  id="edit-title"
                  type="text"
                  className="w-full p-3 border rounded-md"
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  maxLength={500}
                />
              </div>

              {/* 説明編集 */}
              <div>
                <label
                  htmlFor="edit-description"
                  className="block text-sm font-medium mb-2"
                >
                  説明
                </label>
                <textarea
                  id="edit-description"
                  className="w-full p-3 border rounded-md min-h-[200px]"
                  value={editedDescription}
                  onChange={(e) => setEditedDescription(e.target.value)}
                />
              </div>

              {/* 優先度編集 */}
              <div>
                <label
                  htmlFor="edit-priority"
                  className="block text-sm font-medium mb-2"
                >
                  優先度
                </label>
                <select
                  id="edit-priority"
                  className="w-full p-3 border rounded-md"
                  value={editedPriority}
                  onChange={(e) =>
                    setEditedPriority(e.target.value as Priority)
                  }
                >
                  <option value="low">{PRIORITY_LABELS.low}</option>
                  <option value="medium">{PRIORITY_LABELS.medium}</option>
                  <option value="high">{PRIORITY_LABELS.high}</option>
                  <option value="urgent">{PRIORITY_LABELS.urgent}</option>
                </select>
              </div>

              {/* 推定工数編集 */}
              <div>
                <label
                  htmlFor="edit-effort"
                  className="block text-sm font-medium mb-2"
                >
                  推定工数（時間）
                </label>
                <input
                  id="edit-effort"
                  type="number"
                  step="0.5"
                  min="0"
                  className="w-full p-3 border rounded-md"
                  value={editedEstimatedEffort}
                  onChange={(e) => setEditedEstimatedEffort(e.target.value)}
                />
              </div>

              {/* 担当者編集 */}
              <div>
                <label
                  htmlFor="edit-assignee"
                  className="block text-sm font-medium mb-2"
                >
                  担当者
                </label>
                <input
                  id="edit-assignee"
                  type="text"
                  className="w-full p-3 border rounded-md"
                  value={editedAssignee}
                  onChange={(e) => setEditedAssignee(e.target.value)}
                  maxLength={50}
                />
              </div>

              {/* 期限編集 */}
              <div>
                <label
                  htmlFor="edit-deadline"
                  className="block text-sm font-medium mb-2"
                >
                  期限
                </label>
                <input
                  id="edit-deadline"
                  type="date"
                  className="w-full p-3 border rounded-md"
                  value={editedDeadline}
                  onChange={(e) => setEditedDeadline(e.target.value)}
                />
              </div>
            </div>
          ) : (
            <>
              <h2 className="text-lg font-semibold mb-2">{story.title}</h2>
              <p className="whitespace-pre-wrap bg-gray-50 p-4 rounded-md">
                {story.description}
              </p>
            </>
          )}
        </div>

        {/* 承認情報 */}
        {story.status === "approved" && story.story_metadata?.approval && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
            <h2 className="text-lg font-semibold mb-2 text-green-800">
              承認情報
            </h2>
            <div className="text-sm text-gray-700">
              <p>
                <span className="font-semibold">承認日時:</span>{" "}
                {formatTimestamp(story.story_metadata.approval.approved_at)}
              </p>
              <p>
                <span className="font-semibold">承認者:</span>{" "}
                {story.story_metadata.approval.approver}
              </p>
            </div>
          </div>
        )}

        {/* 却下情報 */}
        {story.status === "rejected" && story.story_metadata?.rejection && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <h2 className="text-lg font-semibold mb-2 text-red-800">
              却下情報
            </h2>
            <div className="text-sm text-gray-700">
              <p>
                <span className="font-semibold">却下日時:</span>{" "}
                {formatTimestamp(story.story_metadata.rejection.rejected_at)}
              </p>
              <p>
                <span className="font-semibold">却下者:</span>{" "}
                {story.story_metadata.rejection.rejector}
              </p>
              <div className="mt-2">
                <span className="font-semibold">却下理由:</span>
                <p className="mt-1 whitespace-pre-wrap bg-white p-3 rounded border border-red-200">
                  {story.story_metadata.rejection.reason}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* アクションボタン */}
        <div className="flex gap-2 flex-wrap">
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
              {canApproveOrReject && (
                <>
                  <button
                    onClick={() => setShowApproveDialog(true)}
                    disabled={approveMutation.isPending}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    承認
                  </button>
                  <button
                    onClick={() => setShowRejectDialog(true)}
                    disabled={rejectMutation.isPending}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                  >
                    却下
                  </button>
                </>
              )}
              <button
                onClick={() => setShowDeleteDialog(true)}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
              >
                削除
              </button>
            </>
          )}
        </div>
      </div>

      {/* 承認確認ダイアログ */}
      {showApproveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div
            className="bg-white rounded-lg p-6 max-w-md w-full"
            role="dialog"
            aria-modal="true"
            aria-labelledby="approveDialogTitle"
          >
            <h3 id="approveDialogTitle" className="text-lg font-semibold mb-4">
              ストーリーの承認
            </h3>
            <p className="mb-4 text-gray-600">
              このストーリーを承認してもよろしいですか？
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={handleCancelApprove}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                キャンセル
              </button>
              <button
                onClick={handleConfirmApprove}
                disabled={approveMutation.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
              >
                確認
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 却下確認ダイアログ */}
      {showRejectDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div
            className="bg-white rounded-lg p-6 max-w-md w-full"
            role="dialog"
            aria-modal="true"
            aria-labelledby="rejectDialogTitle"
          >
            <h3 id="rejectDialogTitle" className="text-lg font-semibold mb-4">
              ストーリーの却下
            </h3>
            <div className="mb-4">
              <label
                htmlFor="rejectReason"
                className="block text-sm font-medium mb-2"
              >
                却下理由 <span className="text-red-500">*</span>
              </label>
              <textarea
                id="rejectReason"
                className={`w-full p-2 border rounded-md min-h-[100px] ${
                  rejectReasonError ? "border-red-500" : ""
                }`}
                value={rejectReason}
                onChange={(e) => {
                  setRejectReason(e.target.value);
                  if (rejectReasonError && e.target.value.trim()) {
                    setRejectReasonError("");
                  }
                }}
                placeholder="却下理由を入力してください（必須）"
              />
              {rejectReasonError && (
                <p className="mt-1 text-sm text-red-600">{rejectReasonError}</p>
              )}
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={handleCancelReject}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                キャンセル
              </button>
              <button
                onClick={handleConfirmReject}
                disabled={rejectMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                確認
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 削除確認ダイアログ */}
      {showDeleteDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div
            className="bg-white rounded-lg p-6 max-w-md w-full"
            role="dialog"
            aria-modal="true"
            aria-labelledby="deleteDialogTitle"
          >
            <h3 id="deleteDialogTitle" className="text-lg font-semibold mb-4">
              ストーリーの削除
            </h3>
            <p className="mb-4 text-gray-600">
              このストーリーを削除してもよろしいですか？この操作は取り消せません。
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={handleCancelDelete}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                キャンセル
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                確認
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StoryDetail;
