import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  getInquiry,
  updateInquiry,
  approveInquiry,
  rejectInquiry,
} from "../services/inquiryApi";

export interface InquiryDetailProps {
  inquiryId: number;
}

/**
 * InquiryDetail is responsible for displaying and managing the lifecycle of a single inquiry.
 *
 * It fetches the inquiry details, allows authorized users to edit the content, and provides
 * actions to approve or reject the inquiry with an optional rejection reason. The component
 * keeps the local UI state in sync with the server by invalidating the corresponding
 * react-query cache entries after each mutation and surfaces operation results via toast
 * notifications.
 *
 * Requirements / behavior mapping:
 * - Presents the full details of an inquiry for review.
 * - Supports updating the inquiry content while handling loading and error states.
 * - Enables approving or rejecting an inquiry as part of the inquiry workflow, including
 *   capturing and submitting a rejection reason when provided.
 *
 * @component
 * @param {InquiryDetailProps} props - The props for the component.
 * @param {number} props.inquiryId - The identifier of the inquiry whose details are shown
 * and managed.
 */
const InquiryDetail: React.FC<InquiryDetailProps> = ({ inquiryId }) => {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  // Fetch inquiry details
  const {
    data: inquiry,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["inquiry", inquiryId],
    queryFn: () => getInquiry(inquiryId),
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (content: string) => updateInquiry(inquiryId, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inquiry", inquiryId] });
      setIsEditing(false);
      toast.success("問い合わせを更新しました");
    },
    onError: () => {
      toast.error("問い合わせの更新に失敗しました");
    },
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: () => approveInquiry(inquiryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inquiry", inquiryId] });
      toast.success("問い合わせを承認しました");
    },
    onError: () => {
      toast.error("問い合わせの承認に失敗しました");
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: (reason?: string) =>
      rejectInquiry(inquiryId, reason ? { reason } : undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inquiry", inquiryId] });
      setShowRejectDialog(false);
      setRejectReason("");
      toast.success("問い合わせを却下しました");
    },
    onError: () => {
      toast.error("問い合わせの却下に失敗しました");
    },
  });

  const handleEdit = () => {
    if (inquiry) {
      setEditedContent(inquiry.content);
      setIsEditing(true);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedContent("");
  };

  const handleSave = () => {
    if (editedContent.trim()) {
      updateMutation.mutate(editedContent);
    }
  };

  const handleApprove = () => {
    approveMutation.mutate();
  };

  const handleReject = () => {
    setShowRejectDialog(true);
  };

  const handleConfirmReject = () => {
    const reason = rejectReason.trim() || undefined;
    rejectMutation.mutate(reason);
  };

  const handleCancelReject = () => {
    setShowRejectDialog(false);
    setRejectReason("");
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
        <p className="text-red-600">問い合わせの取得に失敗しました</p>
      </div>
    );
  }

  if (!inquiry) {
    return null;
  }

  const canEdit = inquiry.status === "received";

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white shadow rounded-lg p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">問い合わせ詳細</h1>
          <div className="text-sm text-gray-600">
            <p>
              <span className="font-semibold">ID:</span> {inquiry.id}
            </p>
            <p>
              <span className="font-semibold">ユーザーID:</span>{" "}
              {inquiry.user_id}
            </p>
            <p>
              <span className="font-semibold">ステータス:</span>{" "}
              {inquiry.status}
            </p>
            <p>
              <span className="font-semibold">作成日時:</span>{" "}
              {new Date(inquiry.created_at).toLocaleString("ja-JP")}
            </p>
            <p>
              <span className="font-semibold">更新日時:</span>{" "}
              {new Date(inquiry.updated_at).toLocaleString("ja-JP")}
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">問い合わせ内容</h2>
          {isEditing ? (
            <textarea
              className="w-full p-3 border rounded-md min-h-[200px]"
              aria-label="問い合わせ内容を編集"
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
            />
          ) : (
            <p className="whitespace-pre-wrap bg-gray-50 p-4 rounded-md">
              {inquiry.content}
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
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
              {canEdit && (
                <>
                  <button
                    onClick={handleApprove}
                    disabled={approveMutation.isPending}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    承認
                  </button>
                  <button
                    onClick={handleReject}
                    disabled={rejectMutation.isPending}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                  >
                    却下
                  </button>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Reject Dialog */}
      {showRejectDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div
            className="bg-white rounded-lg p-6 max-w-md w-full"
            role="dialog"
            aria-modal="true"
            aria-labelledby="rejectDialogTitle"
          >
            <h3 id="rejectDialogTitle" className="text-lg font-semibold mb-4">
              問い合わせの却下
            </h3>
            <div className="mb-4">
              <label
                htmlFor="rejectReason"
                className="block text-sm font-medium mb-2"
              >
                却下理由（任意）
              </label>
              <textarea
                id="rejectReason"
                className="w-full p-2 border rounded-md min-h-[100px]"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="却下理由を入力してください（任意）"
              />
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
    </div>
  );
};

export default InquiryDetail;
