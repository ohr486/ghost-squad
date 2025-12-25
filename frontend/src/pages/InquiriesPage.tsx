import React, { useState } from "react";
import { MessageSquare, Plus, X } from "lucide-react";
import { InquiryForm } from "../components/forms";
import type { InquiryResponse } from "../types/api";

const InquiriesPage: React.FC = () => {
  const [showForm, setShowForm] = useState(false);

  const handleInquirySuccess = (inquiry: InquiryResponse) => {
    console.log("Inquiry created successfully:", inquiry);
    // TODO: Refresh inquiry list when implemented
    setShowForm(false);
  };

  const handleInquiryError = (error: Error) => {
    console.error("Failed to create inquiry:", error);
    // Error is already handled by the form component with toast
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
            <MessageSquare className="w-6 h-6 mr-2" />
            問い合わせ管理
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            自然言語での問い合わせを入力し、AIがストーリーに変換します
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 transition-colors duration-200"
          aria-label={showForm ? "フォームを閉じる" : "新しい問い合わせを作成"}
        >
          {showForm ? (
            <>
              <X className="w-4 h-4 mr-2" />
              閉じる
            </>
          ) : (
            <>
              <Plus className="w-4 h-4 mr-2" />
              新しい問い合わせ
            </>
          )}
        </button>
      </div>

      {/* Inquiry Form */}
      {showForm && (
        <InquiryForm
          onSuccess={handleInquirySuccess}
          onError={handleInquiryError}
        />
      )}

      {/* Content Area */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border dark:border-gray-700">
        <div className="p-6">
          {!showForm ? (
            <div className="text-center py-12">
              <MessageSquare className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                問い合わせを作成
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6">
                「新しい問い合わせ」ボタンをクリックして開始してください
              </p>
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-4 max-w-md mx-auto">
                <p className="text-sm text-blue-800 dark:text-blue-300">
                  <strong>利用可能な機能:</strong>
                  <br />
                  ✅ 問い合わせ入力フォーム
                  <br />
                  <strong>実装予定:</strong>
                  <br />
                  • 問い合わせ履歴表示
                  <br />• AIストーリー生成機能
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                問い合わせ履歴
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                問い合わせ履歴表示機能は次のタスクで実装予定です
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InquiriesPage;
