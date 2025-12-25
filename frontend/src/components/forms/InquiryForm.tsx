import React, { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Send, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";
import { InquiryService } from "../../services";
import type { InquiryCreateRequest, InquiryResponse } from "../../types/api";

// Form validation schema
const inquiryFormSchema = z.object({
  content: z
    .string()
    .min(10, "問い合わせ内容は10文字以上で入力してください")
    .max(5000, "問い合わせ内容は5000文字以内で入力してください"),
  language: z.enum(["ja", "en"]).default("ja"),
});

type InquiryFormData = z.infer<typeof inquiryFormSchema>;

interface InquiryFormProps {
  onSuccess?: (inquiry: InquiryResponse) => void;
  onError?: (error: Error) => void;
  className?: string;
  /**
   * User ID to associate with the inquiry.
   * Defaults to "user-001" until authentication is implemented.
   * This should be replaced with the actual authenticated user ID from auth context.
   */
  userId?: string;
}

const InquiryForm: React.FC<InquiryFormProps> = ({
  onSuccess,
  onError,
  className = "",
  userId = "user-001",
}) => {
  const [submitState, setSubmitState] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isValid },
  } = useForm<InquiryFormData>({
    resolver: zodResolver(inquiryFormSchema),
    defaultValues: {
      content: "",
      language: "ja",
    },
    mode: "onBlur",
  });

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const contentValue = watch("content");
  const characterCount = contentValue?.length || 0;

  const onSubmit = async (data: InquiryFormData) => {
    try {
      setSubmitState("loading");

      // Create the request payload
      const requestData: InquiryCreateRequest = {
        content: data.content.trim(),
        language: data.language,
        user_id: userId,
      };

      // Submit the inquiry
      const response = await InquiryService.createInquiry(requestData);

      setSubmitState("success");
      toast.success("問い合わせを送信しました");

      // Reset form after successful submission
      reset();

      // Call success callback if provided
      if (onSuccess) {
        onSuccess(response);
      }

      // Reset success state after 3 seconds
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        setSubmitState("idle");
      }, 3000);
    } catch (error) {
      setSubmitState("error");
      const errorMessage =
        error instanceof Error ? error.message : "送信に失敗しました";
      toast.error(`エラー: ${errorMessage}`);

      // Call error callback if provided
      if (onError) {
        onError(error instanceof Error ? error : new Error(errorMessage));
      }

      // Reset error state after 5 seconds
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        setSubmitState("idle");
      }, 5000);
    }
  };

  const getSubmitButtonContent = () => {
    switch (submitState) {
      case "loading":
        return (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            送信中...
          </>
        );
      case "success":
        return (
          <>
            <CheckCircle className="w-4 h-4 mr-2" />
            送信完了
          </>
        );
      case "error":
        return (
          <>
            <AlertCircle className="w-4 h-4 mr-2" />
            再試行
          </>
        );
      default:
        return (
          <>
            <Send className="w-4 h-4 mr-2" />
            送信
          </>
        );
    }
  };

  const getSubmitButtonClass = () => {
    const baseClass =
      "inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200";

    switch (submitState) {
      case "loading":
        return `${baseClass} text-white bg-blue-400 cursor-not-allowed`;
      case "success":
        return `${baseClass} text-white bg-green-600 hover:bg-green-700 focus:ring-green-500`;
      case "error":
        return `${baseClass} text-white bg-red-600 hover:bg-red-700 focus:ring-red-500`;
      default:
        return `${baseClass} text-white bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed`;
    }
  };

  const getSubmitButtonAriaLabel = () => {
    switch (submitState) {
      case "loading":
        return "問い合わせを送信中です";
      case "success":
        return "問い合わせの送信が完了しました";
      case "error":
        return "送信に失敗しました。再試行してください";
      default:
        return "問い合わせを送信";
    }
  };

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 ${className}`}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Form Header */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            新しい問い合わせ
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            自然言語で問い合わせを入力してください。AIが自動的にストーリーに変換します。
          </p>
        </div>

        {/* Language Selection */}
        <div>
          <label
            htmlFor="language"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            問い合わせの言語
          </label>
          <select
            {...register("language")}
            id="language"
            className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="ja">日本語</option>
            <option value="en">English</option>
          </select>
        </div>

        {/* Content Textarea */}
        <div>
          <label
            htmlFor="content"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            問い合わせ内容
          </label>
          <textarea
            {...register("content")}
            id="content"
            rows={6}
            placeholder="例: ユーザー登録機能を追加したいです。メールアドレスとパスワードで登録できるようにして、確認メールも送信したいです。"
            className={`block w-full px-3 py-2 border rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 sm:text-sm ${
              errors.content
                ? "border-red-300 dark:border-red-600 focus:ring-red-500 focus:border-red-500"
                : "border-gray-300 dark:border-gray-600 focus:ring-blue-500 focus:border-blue-500"
            }`}
            style={{
              resize: "vertical",
              minHeight: "120px",
            }}
            aria-invalid={errors.content ? "true" : "false"}
            aria-describedby={
              errors.content ? "content-error" : "content-character-count"
            }
          />

          {/* Character Count */}
          <div className="flex justify-between items-center mt-1">
            <div>
              {errors.content && (
                <p
                  id="content-error"
                  className="text-sm text-red-600 dark:text-red-400"
                  role="alert"
                  aria-live="assertive"
                >
                  {errors.content.message}
                </p>
              )}
            </div>
            <p
              id="content-character-count"
              className={`text-xs ${
                characterCount > 4500
                  ? "text-red-600 dark:text-red-400"
                  : characterCount > 4000
                    ? "text-yellow-600 dark:text-yellow-400"
                    : "text-gray-500 dark:text-gray-400"
              }`}
              aria-live="polite"
              aria-label={`問い合わせ内容の文字数: ${characterCount}文字（最大5000文字まで）`}
            >
              {characterCount} / 5000
            </p>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!isValid || submitState === "loading"}
            className={getSubmitButtonClass()}
            aria-label={getSubmitButtonAriaLabel()}
            aria-busy={submitState === "loading"}
          >
            {getSubmitButtonContent()}
          </button>
        </div>

        {/* Status Messages */}
        {submitState === "success" && (
          <div
            className="rounded-md bg-green-50 dark:bg-green-900/20 p-4"
            role="status"
            aria-live="polite"
          >
            <div className="flex">
              <CheckCircle
                className="h-5 w-5 text-green-400"
                aria-hidden="true"
              />
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  問い合わせが正常に送信されました
                </p>
                <p className="mt-1 text-sm text-green-700 dark:text-green-300">
                  AIによるストーリー生成が開始されました。しばらくお待ちください。
                </p>
              </div>
            </div>
          </div>
        )}

        {submitState === "error" && (
          <div
            className="rounded-md bg-red-50 dark:bg-red-900/20 p-4"
            role="alert"
            aria-live="assertive"
          >
            <div className="flex">
              <AlertCircle
                className="h-5 w-5 text-red-400"
                aria-hidden="true"
              />
              <div className="ml-3">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  送信に失敗しました
                </p>
                <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                  ネットワーク接続を確認して、もう一度お試しください。
                </p>
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

export default InquiryForm;
