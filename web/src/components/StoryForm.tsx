/**
 * StoryFormコンポーネント
 *
 * ストーリー作成フォーム（新規作成モード）
 * - モーダルダイアログで表示
 * - React Hook Formでフォーム状態管理
 * - Zodスキーマでクライアント側バリデーション
 * - 問い合わせID選択（ドロップダウン）
 * - react-hot-toastで成功・エラーメッセージ表示
 *
 * 要件: 2.11, 2.12, 2.13, 2.14, 5.15, 5.16, 5.17, 5.18, 5.19, 5.20, 5.21, 5.22
 */

import React, { useState, useEffect, useMemo } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";
import type {
  CreateStoryRequest,
  ErrorResponse,
  InquiryResponse,
  Priority,
} from "../types";

/**
 * フォームバリデーションスキーマ
 *
 * バリデーションルール:
 * - inquiry_id: 必須
 * - title: 必須、最大500文字
 * - description: 必須
 * - priority: 必須、列挙型
 * - estimated_effort: オプショナル、0以上の数値
 * - assignee: オプショナル、最大50文字
 * - deadline: オプショナル、ISO 8601形式
 */
const storyFormSchema = z.object({
  inquiry_id: z
    .number({
      required_error: "問い合わせを選択してください",
      invalid_type_error: "問い合わせを選択してください",
    })
    .positive("問い合わせを選択してください"),
  title: z
    .string()
    .min(1, "タイトルは必須です")
    .max(500, "タイトルは500文字以内で入力してください"),
  description: z.string().min(1, "説明は必須です"),
  priority: z.enum(["low", "medium", "high", "urgent"], {
    required_error: "優先度を選択してください",
  }),
  estimated_effort: z
    .union([
      z.number().min(0, "推定工数は0以上の数値を入力してください"),
      z.null(),
    ])
    .optional()
    .transform((val) => (val == null ? undefined : val)),
  assignee: z
    .string()
    .max(50, "担当者は50文字以内で入力してください")
    .optional()
    .transform((val) => (val === "" ? undefined : val)),
  deadline: z
    .string()
    .optional()
    .transform((val) => (val === "" ? undefined : val)),
});

type StoryFormData = z.infer<typeof storyFormSchema>;

/**
 * 優先度ラベルマッピング
 */
const PRIORITY_LABELS: Record<Priority, string> = {
  low: "低",
  medium: "中",
  high: "高",
  urgent: "緊急",
};

/**
 * ステータスラベルマッピング
 */
const STATUS_LABELS: Record<string, string> = {
  received: "受付済み",
  processing: "AI処理中",
  needs_clarification: "明確化要求",
  task_working: "タスク作業中",
  completed: "完了",
  rejected: "却下済み",
  failed: "失敗",
};

/**
 * ErrorResponse型ガード
 */
const isErrorResponse = (error: unknown): error is ErrorResponse => {
  return (
    typeof error === "object" &&
    error !== null &&
    "errors" in error &&
    Array.isArray((error as ErrorResponse).errors)
  );
};

/**
 * StoryFormプロパティ
 */
export interface StoryFormProps {
  /** 問い合わせリスト */
  inquiries: InquiryResponse[];
  /** フォーム送信時のコールバック */
  onSubmit: (
    inquiryId: number,
    data: CreateStoryRequest | undefined,
  ) => Promise<void>;
  /** モーダルを閉じる時のコールバック */
  onClose?: () => void;
  /** キャンセルボタンクリック時のコールバック */
  onCancel?: () => void;
  /** モーダルの表示状態 */
  isOpen?: boolean;
  /** ローディング状態（外部から制御する場合） */
  isLoading?: boolean;
  /** 初期選択する問い合わせID */
  initialInquiryId?: number;
}

/**
 * StoryFormコンポーネント
 */
export const StoryForm: React.FC<StoryFormProps> = ({
  inquiries,
  onSubmit,
  onClose,
  onCancel,
  isOpen = false,
  isLoading: externalIsLoading = false,
  initialInquiryId,
}) => {
  // ローディング状態管理
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const isLoading = externalIsLoading || isSubmitting;

  // React Hook Form初期化
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
    reset,
    watch,
    setValue,
  } = useForm<StoryFormData>({
    resolver: zodResolver(storyFormSchema),
    defaultValues: {
      inquiry_id: initialInquiryId,
      title: "",
      description: "",
      priority: "medium",
      estimated_effort: undefined,
      assignee: "",
      deadline: "",
    },
  });

  // 選択された問い合わせIDを監視
  const selectedInquiryId = watch("inquiry_id");

  // 選択された問い合わせ情報を取得
  const selectedInquiry = useMemo(() => {
    if (!selectedInquiryId) return null;
    return (
      inquiries.find((inquiry) => inquiry.id === selectedInquiryId) || null
    );
  }, [selectedInquiryId, inquiries]);

  // initialInquiryIdが変更された場合にフォームを更新
  useEffect(() => {
    if (initialInquiryId) {
      setValue("inquiry_id", initialInquiryId);
    }
  }, [initialInquiryId, setValue]);

  // モーダルが閉じられた時にフォームをリセット
  useEffect(() => {
    if (!isOpen) {
      reset();
      setServerError(null);
    }
  }, [isOpen, reset]);

  /**
   * フォーム送信ハンドラ
   */
  const onSubmitHandler = async (data: StoryFormData) => {
    setIsSubmitting(true);
    setServerError(null);

    try {
      // CreateStoryRequestを構築
      const storyRequest: CreateStoryRequest = {
        title: data.title,
        description: data.description,
        priority: data.priority as Priority,
      };

      // オプションフィールドを追加
      if (
        data.estimated_effort !== undefined &&
        data.estimated_effort !== null
      ) {
        storyRequest.estimated_effort = data.estimated_effort;
      }
      if (data.assignee) {
        storyRequest.assignee = data.assignee;
      }
      if (data.deadline) {
        // 日付をISO 8601形式に変換
        storyRequest.deadline = new Date(data.deadline).toISOString();
      }

      await onSubmit(data.inquiry_id, storyRequest);

      // 成功時の処理
      toast.success("ストーリーを作成しました");
      reset();
      onClose?.();
    } catch (error) {
      // エラーハンドリング
      if (isErrorResponse(error)) {
        const errorMessage =
          error.errors.map((e) => e.message).join(", ") ||
          "エラーが発生しました";
        setServerError(errorMessage);
        toast.error(errorMessage);
      } else {
        const genericError = "エラーが発生しました。もう一度お試しください。";
        setServerError(genericError);
        toast.error(genericError);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * 背景クリックハンドラ
   */
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onCancel?.();
    }
  };

  // モーダルが開いていない場合は何も表示しない
  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      data-testid="modal-overlay"
      onClick={handleOverlayClick}
    >
      <div
        className="w-full max-w-2xl mx-4 bg-white rounded-lg shadow-xl"
        role="dialog"
        aria-labelledby="story-form-title"
        aria-modal="true"
      >
        {/* モーダルヘッダー */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2
            id="story-form-title"
            className="text-xl font-semibold text-gray-900"
          >
            新規ストーリー作成
          </h2>
        </div>

        {/* モーダルボディ */}
        <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
          <form onSubmit={handleSubmit(onSubmitHandler)} className="space-y-6">
            {/* サーバーエラーバナー */}
            {serverError && (
              <div
                className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md"
                role="alert"
              >
                <p className="font-medium">エラーが発生しました</p>
                <p className="text-sm mt-1">{serverError}</p>
              </div>
            )}

            {/* 問い合わせ選択フィールド */}
            <div>
              <label
                htmlFor="inquiry_id"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                問い合わせ <span className="text-red-500">*</span>
              </label>
              <Controller
                name="inquiry_id"
                control={control}
                render={({ field }) => (
                  <select
                    id="inquiry_id"
                    {...field}
                    value={field.value || ""}
                    onChange={(e) => {
                      const value = e.target.value;
                      field.onChange(value ? Number(value) : undefined);
                    }}
                    className={`
                      w-full px-3 py-2 border rounded-md shadow-sm
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                      ${errors.inquiry_id ? "border-red-500" : "border-gray-300"}
                    `}
                    disabled={isLoading}
                  >
                    <option value="">問い合わせを選択してください</option>
                    {inquiries.map((inquiry) => (
                      <option key={inquiry.id} value={inquiry.id}>
                        {inquiry.content.length > 50
                          ? `${inquiry.content.substring(0, 50)}...`
                          : inquiry.content}
                      </option>
                    ))}
                  </select>
                )}
              />
              {errors.inquiry_id && (
                <p className="mt-1 text-sm text-red-600" role="alert">
                  {errors.inquiry_id.message}
                </p>
              )}

              {/* 問い合わせプレビュー */}
              {selectedInquiry && (
                <div className="mt-2 p-3 bg-gray-50 rounded-md border border-gray-200">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">ステータス: </span>
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        selectedInquiry.status === "task_working"
                          ? "bg-blue-100 text-blue-800"
                          : selectedInquiry.status === "received"
                            ? "bg-yellow-100 text-yellow-800"
                            : selectedInquiry.status === "completed"
                              ? "bg-green-100 text-green-800"
                              : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {STATUS_LABELS[selectedInquiry.status] ||
                        selectedInquiry.status}
                    </span>
                  </p>
                  <p className="mt-1 text-sm text-gray-600">
                    <span className="font-medium">内容: </span>
                    {selectedInquiry.content}
                  </p>
                </div>
              )}
            </div>

            {/* タイトルフィールド */}
            <div>
              <label
                htmlFor="title"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                タイトル <span className="text-red-500">*</span>
              </label>
              <input
                id="title"
                type="text"
                {...register("title")}
                className={`
                  w-full px-3 py-2 border rounded-md shadow-sm
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                  ${errors.title ? "border-red-500" : "border-gray-300"}
                `}
                placeholder="ストーリーのタイトルを入力"
                disabled={isLoading}
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600" role="alert">
                  {errors.title.message}
                </p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                最大500文字まで入力できます
              </p>
            </div>

            {/* 説明フィールド */}
            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                説明 <span className="text-red-500">*</span>
              </label>
              <textarea
                id="description"
                {...register("description")}
                rows={4}
                className={`
                  w-full px-3 py-2 border rounded-md shadow-sm
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                  ${errors.description ? "border-red-500" : "border-gray-300"}
                `}
                placeholder="ストーリーの詳細な説明を入力"
                disabled={isLoading}
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600" role="alert">
                  {errors.description.message}
                </p>
              )}
            </div>

            {/* 優先度フィールド */}
            <div>
              <label
                htmlFor="priority"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                優先度 <span className="text-red-500">*</span>
              </label>
              <select
                id="priority"
                {...register("priority")}
                className={`
                  w-full px-3 py-2 border rounded-md shadow-sm
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                  ${errors.priority ? "border-red-500" : "border-gray-300"}
                `}
                disabled={isLoading}
              >
                <option value="low">{PRIORITY_LABELS.low}</option>
                <option value="medium">{PRIORITY_LABELS.medium}</option>
                <option value="high">{PRIORITY_LABELS.high}</option>
                <option value="urgent">{PRIORITY_LABELS.urgent}</option>
              </select>
              {errors.priority && (
                <p className="mt-1 text-sm text-red-600" role="alert">
                  {errors.priority.message}
                </p>
              )}
            </div>

            {/* オプションフィールドセクション */}
            <div className="border-t border-gray-200 pt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-4">
                オプション項目
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 推定工数フィールド */}
                <div>
                  <label
                    htmlFor="estimated_effort"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    推定工数（時間）
                  </label>
                  <Controller
                    name="estimated_effort"
                    control={control}
                    render={({ field }) => (
                      <input
                        id="estimated_effort"
                        type="number"
                        step="0.5"
                        min="0"
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) => {
                          const value = e.target.value;
                          field.onChange(
                            value === "" ? undefined : Number(value),
                          );
                        }}
                        className={`
                          w-full px-3 py-2 border rounded-md shadow-sm
                          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                          ${errors.estimated_effort ? "border-red-500" : "border-gray-300"}
                        `}
                        placeholder="例: 8"
                        disabled={isLoading}
                      />
                    )}
                  />
                  {errors.estimated_effort && (
                    <p className="mt-1 text-sm text-red-600" role="alert">
                      {errors.estimated_effort.message}
                    </p>
                  )}
                </div>

                {/* 担当者フィールド */}
                <div>
                  <label
                    htmlFor="assignee"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    担当者
                  </label>
                  <input
                    id="assignee"
                    type="text"
                    {...register("assignee")}
                    className={`
                      w-full px-3 py-2 border rounded-md shadow-sm
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                      ${errors.assignee ? "border-red-500" : "border-gray-300"}
                    `}
                    placeholder="例: developer_001"
                    disabled={isLoading}
                  />
                  {errors.assignee && (
                    <p className="mt-1 text-sm text-red-600" role="alert">
                      {errors.assignee.message}
                    </p>
                  )}
                </div>

                {/* 期限フィールド */}
                <div className="md:col-span-2">
                  <label
                    htmlFor="deadline"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    期限
                  </label>
                  <input
                    id="deadline"
                    type="date"
                    {...register("deadline")}
                    className={`
                      w-full px-3 py-2 border rounded-md shadow-sm
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                      ${errors.deadline ? "border-red-500" : "border-gray-300"}
                    `}
                    disabled={isLoading}
                  />
                  {errors.deadline && (
                    <p className="mt-1 text-sm text-red-600" role="alert">
                      {errors.deadline.message}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* ボタン */}
            <div className="flex justify-end gap-4 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onCancel}
                disabled={isLoading}
                className={`
                  px-4 py-2 border border-gray-300 text-gray-700 font-medium rounded-md
                  focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500
                  ${
                    isLoading
                      ? "bg-gray-100 cursor-not-allowed"
                      : "bg-white hover:bg-gray-50"
                  }
                `}
              >
                キャンセル
              </button>

              <button
                type="submit"
                disabled={isLoading}
                className={`
                  px-4 py-2 text-white font-medium rounded-md
                  focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                  ${
                    isLoading
                      ? "bg-gray-400 cursor-not-allowed"
                      : "bg-blue-600 hover:bg-blue-700"
                  }
                `}
              >
                {isLoading ? "作成中..." : "作成"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
