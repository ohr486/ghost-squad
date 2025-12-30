import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import InquiryList from "./components/InquiryList";
import InquiryDetail from "./components/InquiryDetail";
import { InquiryForm } from "./components/InquiryForm";
import { createInquiry } from "./services/inquiryApi";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App(): JSX.Element {
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

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
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
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
