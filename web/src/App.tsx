import { useState } from "react";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import InquiryList from "./components/InquiryList";
import InquiryDetail from "./components/InquiryDetail";
import { InquiryForm } from "./components/InquiryForm";
import { StoryForm } from "./components/StoryForm";
import StoryList from "./components/StoryList";
import StoryDetail from "./components/StoryDetail";
import { ImporterPage } from "./components/importer";
import { createInquiry, listInquiries } from "./services/inquiryApi";
import { createStory } from "./services/storyApi";
import type { CreateStoryRequest } from "./types";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

type Tab = "inquiries" | "stories" | "importer";

/**
 * アプリケーションのメインコンテンツ
 * QueryClientProvider内で使用される
 */
function AppContent(): JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>("inquiries");
  const [selectedInquiryId, setSelectedInquiryId] = useState<number | null>(
    null,
  );
  const [selectedStoryId, setSelectedStoryId] = useState<number | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showStoryForm, setShowStoryForm] = useState(false);

  // QueryClientを取得（ストーリー作成後のキャッシュ更新用）
  const queryClientFromContext = useQueryClient();

  // 問い合わせ一覧を取得（StoryForm用）
  // APIの制限により、limitは最大100まで
  // 100件以上の問い合わせがある場合は、検索機能の導入を検討する
  const { data: inquiriesData, isLoading: isLoadingInquiries } = useQuery({
    queryKey: ["inquiries-for-story-form"],
    queryFn: () => listInquiries({ limit: 100 }),
    enabled: showStoryForm, // StoryFormが表示されている時のみ取得
  });

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
    setSelectedStoryId(storyId);
    setShowStoryForm(false);
  };

  const handleBackToStoryList = () => {
    setSelectedStoryId(null);
  };

  const handleCreateStoryClick = () => {
    setShowStoryForm(true);
  };

  const handleStoryFormClose = () => {
    setShowStoryForm(false);
  };

  const handleStoryFormSubmit = async (
    inquiryId: number,
    data: CreateStoryRequest | undefined,
  ) => {
    if (data) {
      await createStory(inquiryId, data);
      // ストーリー一覧を再取得
      queryClientFromContext.invalidateQueries({ queryKey: ["stories"] });
    }
  };

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    setSelectedInquiryId(null);
    setSelectedStoryId(null);
    setShowCreateForm(false);
    setShowStoryForm(false);
  };

  return (
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
            <button
              onClick={() => handleTabChange("importer")}
              className={`${
                activeTab === "importer"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              インポーター
            </button>
          </nav>
        </div>
      </div>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {activeTab === "inquiries" && (
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
        )}

        {activeTab === "stories" && (
          // ストーリータブのコンテンツ
          <>
            {selectedStoryId ? (
              <div className="px-4 py-6 sm:px-0">
                <div className="mb-4">
                  <button
                    onClick={handleBackToStoryList}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    ← 一覧に戻る
                  </button>
                </div>
                <StoryDetail
                  storyId={selectedStoryId}
                  onBack={handleBackToStoryList}
                />
              </div>
            ) : (
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
          </>
        )}

        {activeTab === "importer" && (
          // インポータータブのコンテンツ
          <div className="px-4 py-6 sm:px-0">
            <ImporterPage />
          </div>
        )}
      </main>

      {/* ストーリー作成フォームモーダル */}
      <StoryForm
        isOpen={showStoryForm}
        inquiries={inquiriesData?.data || []}
        onSubmit={handleStoryFormSubmit}
        onClose={handleStoryFormClose}
        onCancel={handleStoryFormClose}
        isLoading={isLoadingInquiries}
      />
    </div>
  );
}

/**
 * アプリケーションのルートコンポーネント
 * QueryClientProviderを提供
 */
function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
