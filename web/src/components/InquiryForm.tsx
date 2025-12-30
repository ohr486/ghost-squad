/**
 * InquiryFormコンポーネント
 *
 * 問い合わせ入力フォーム
 * - React Hook Formでフォーム状態管理
 * - Zodスキーマでクライアント側バリデーション
 * - react-hot-toastで成功・エラーメッセージ表示
 *
 * 要件: 1.1, 1.3, 1.4, 4.1, 4.2, 4.3
 */

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";
import type { CreateInquiryRequest, ErrorResponse } from "../types";

/**
 * フォームバリデーションスキーマ
 *
 * バリデーションルール:
 * - content: 必須、最大10,000文字
 * - user_id: 必須、英数字とアンダースコアのみ、最大50文字
 * - source_system: デフォルト "manual"
 */
const inquiryFormSchema = z.object({
  user_id: z
    .string()
    .min(1, "ユーザーIDは必須です")
    .max(50, "ユーザーIDは50文字以内で入力してください")
    .regex(
      /^[a-zA-Z0-9_]+$/,
      "ユーザーIDは英数字とアンダースコアのみ使用できます",
    ),
  content: z
    .string()
    .min(1, "問い合わせ内容は必須です")
    .max(10000, "問い合わせ内容は10,000文字以内で入力してください"),
  source_system: z.string(),
});

type InquiryFormData = z.infer<typeof inquiryFormSchema>;

/**
 * InquiryFormプロパティ
 */
export interface InquiryFormProps {
  /** フォーム送信時のコールバック */
  onSubmit: (data: CreateInquiryRequest) => Promise<void>;
  /** キャンセルボタンクリック時のコールバック（オプション） */
  onCancel?: () => void;
  /** ローディング状態（外部から制御する場合） */
  isLoading?: boolean;
  /** フォームの初期データ（編集時など） */
  initialData?: Partial<CreateInquiryRequest>;
}

/**
 * InquiryFormコンポーネント
 */
export const InquiryForm: React.FC<InquiryFormProps> = ({
  onSubmit,
  onCancel,
  isLoading: externalIsLoading = false,
  initialData,
}) => {
  // ローディング状態管理
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const isLoading = externalIsLoading || isSubmitting;

  // React Hook Form初期化
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<InquiryFormData>({
    resolver: zodResolver(inquiryFormSchema),
    defaultValues: {
      user_id: initialData?.user_id || "",
      content: initialData?.content || "",
      source_system: initialData?.source_system || "manual",
    },
  });

  /**
   * フォーム送信ハンドラ
   */
  const onSubmitHandler = async (data: InquiryFormData) => {
    setIsSubmitting(true);
    setServerError(null);

    try {
      await onSubmit(data);

      // 成功時の処理
      toast.success("問い合わせを送信しました");
      reset(); // フォームをリセット
    } catch (error) {
      // エラーハンドリング
      if (isErrorResponse(error)) {
        // バックエンドから返されたエラーレスポンス
        const errorMessage =
          error.errors.map((e) => e.message).join(", ") ||
          "エラーが発生しました";
        setServerError(errorMessage);
        toast.error(errorMessage);
      } else {
        // その他のエラー（ネットワークエラーなど）
        const genericError = "エラーが発生しました。もう一度お試しください。";
        setServerError(genericError);
        toast.error(genericError);
      }
    } finally {
      setIsSubmitting(false);
    }
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

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
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

        {/* ユーザーIDフィールド */}
        <div>
          <label
            htmlFor="user_id"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            ユーザーID <span className="text-red-500">*</span>
          </label>
          <input
            id="user_id"
            type="text"
            {...register("user_id")}
            className={`
              w-full px-3 py-2 border rounded-md shadow-sm
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              ${errors.user_id ? "border-red-500" : "border-gray-300"}
            `}
            placeholder="例: user_001"
            disabled={isLoading}
          />
          {errors.user_id && (
            <p className="mt-1 text-sm text-red-600" role="alert">
              {errors.user_id.message}
            </p>
          )}
        </div>

        {/* 問い合わせ内容フィールド */}
        <div>
          <label
            htmlFor="content"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            問い合わせ内容 <span className="text-red-500">*</span>
          </label>
          <textarea
            id="content"
            {...register("content")}
            rows={6}
            className={`
              w-full px-3 py-2 border rounded-md shadow-sm
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              ${errors.content ? "border-red-500" : "border-gray-300"}
            `}
            placeholder="問い合わせ内容を入力してください"
            disabled={isLoading}
          />
          {errors.content && (
            <p className="mt-1 text-sm text-red-600" role="alert">
              {errors.content.message}
            </p>
          )}
          <p className="mt-1 text-sm text-gray-500">
            {/* 文字数カウンター（将来実装） */}
            最大10,000文字まで入力できます
          </p>
        </div>

        {/* 送信元システム（hidden field） */}
        <input type="hidden" name="source_system" value="manual" />

        {/* ボタン */}
        <div className="flex gap-4">
          <button
            type="submit"
            disabled={isLoading}
            className={`
              flex-1 px-4 py-2 text-white font-medium rounded-md
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
              ${
                isLoading
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700"
              }
            `}
          >
            {isLoading ? "送信中..." : "送信"}
          </button>

          {onCancel && (
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
          )}
        </div>
      </form>
    </div>
  );
};
