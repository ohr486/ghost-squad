import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import InquiryList from "./components/InquiryList";
import InquiryDetail from "./components/InquiryDetail";
import { InquiryForm } from "./components/InquiryForm";
import StoryList from "./components/StoryList";
import { createInquiry } from "./services/inquiryApi";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

type Tab = "inquiries" | "stories";

function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>("inquiries");
  const [selectedInquiryId, setSelectedInquiryId] = useState<number | null>(
    null,
  );
  const [showCreateForm, setShowCreateForm] = useState(false);

  const handleInquiryClick = (id: number) => {
    setSelectedInquiryId(id);
    setShowCreateForm(false);
  };

  const handleBackToList = () => {
    setSelectedInquiryId(null);
    setShowCreateForm(false);
  };

  const handleCreateClick = () => {
    setShowCreateForm(true);
    setSelectedInquiryId(null);
  };

  const handleFormSubmit = async (data: {
    user_id: string;
    content: string;
    source_system: string;
  }) => {
    await createInquiry(data);
    setShowCreateForm(false);
  };

  const handleStoryClick = (storyId: number) => {
    console.log("Story clicked:", storyId);
    // TODO: ストーリー詳細画面への遷移（タスク11で実装予定）
  };

  const handleCreateStoryClick = () => {
    console.log("Create story clicked");
    // TODO: ストーリー作成フォーム表示（タスク10で実装予定）
  };

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    setSelectedInquiryId(null);
    setShowCreateForm(false);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <Toaster position="top-right" />
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-gray-900">Ghost Squad</h1>
            <p className="mt-1 text-sm text-gray-600">
              AI-Driven Task Management Platform
            </p>
          </div>
        </header>

        {/* タブナビゲーション */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              <button
                onClick={() => handleTabChange("inquiries")}
                className={`${
                  activeTab === "inquiries"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                問い合わせ
              </button>
              <button
                onClick={() => handleTabChange("stories")}
                className={`${
                  activeTab === "stories"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                ストーリー
              </button>
            </nav>
          </div>
        </div>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {activeTab === "inquiries" ? (
            // 問い合わせタブのコンテンツ
            <>
              {showCreateForm ? (
                <div className="px-4 py-6 sm:px-0">
                  <div className="mb-4">
                    <button
                      onClick={handleBackToList}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      ← 一覧に戻る
                    </button>
                  </div>
                  <div className="bg-white shadow rounded-lg p-6">
                    <h2 className="text-2xl font-bold mb-4">新規問い合わせ</h2>
                    <InquiryForm
                      onSubmit={handleFormSubmit}
                      onCancel={handleBackToList}
                    />
                  </div>
                </div>
              ) : selectedInquiryId ? (
                <div className="px-4 py-6 sm:px-0">
                  <div className="mb-4">
                    <button
                      onClick={handleBackToList}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      ← 一覧に戻る
                    </button>
                  </div>
                  <InquiryDetail inquiryId={selectedInquiryId} />
                </div>
              ) : (
                <div className="px-4 py-6 sm:px-0">
                  <div className="mb-4">
                    <button
                      onClick={handleCreateClick}
                      className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                    >
                      新規作成
                    </button>
                  </div>
                  <InquiryList onInquiryClick={handleInquiryClick} />
                </div>
              )}
            </>
          ) : (
            // ストーリータブのコンテンツ
            <div className="px-4 py-6 sm:px-0">
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4">ストーリー一覧</h2>
                <StoryList
                  onStoryClick={handleStoryClick}
                  onCreateStoryClick={handleCreateStoryClick}
                />
              </div>
            </div>
          )}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
