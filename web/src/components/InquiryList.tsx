import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listInquiries } from "../services/inquiryApi";
import type { InquiryStatus } from "../types/inquiry";

interface InquiryListProps {
  onInquiryClick: (inquiryId: number) => void;
  onApprove?: (inquiryId: number) => Promise<void>;
  onReject?: (inquiryId: number) => Promise<void>;
  statusFilter?: InquiryStatus[];
}

const STATUS_LABELS: Record<InquiryStatus, string> = {
  received: "受付済み",
  processing: "処理中",
  needs_clarification: "明確化要求",
  task_working: "タスク作業中",
  completed: "完了",
  rejected: "却下済み",
  failed: "失敗",
};

const InquiryList: React.FC<InquiryListProps> = ({
  onInquiryClick,
  statusFilter,
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedStatus, setSelectedStatus] = useState<InquiryStatus | "">("");
  const limit = 20;

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["inquiries", currentPage, selectedStatus],
    queryFn: () =>
      listInquiries({
        page: currentPage,
        limit,
        ...(selectedStatus && { status: selectedStatus }),
      }),
  });

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (data?.meta.has_next) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handleRowClick = (inquiryId: number) => {
    onInquiryClick(inquiryId);
  };

  const handleStatusFilterChange = (
    event: React.ChangeEvent<HTMLSelectElement>,
  ) => {
    const newStatus = event.target.value as InquiryStatus | "";
    setSelectedStatus(newStatus);
    setCurrentPage(1); // Reset to first page when filtering
  };

  const truncateContent = (
    content: string,
    maxLength: number = 100,
  ): string => {
    if (content.length <= maxLength) {
      return content;
    }
    return content.substring(0, maxLength) + "...";
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString("ja-JP");
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded">
        <p className="text-red-800">
          問い合わせの読み込みに失敗しました:{" "}
          {error instanceof Error ? error.message : "不明なエラー"}
        </p>
      </div>
    );
  }

  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="p-8 text-center text-gray-600">
        問い合わせが見つかりませんでした。
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Status Filter */}
      <div className="flex items-center gap-2">
        <label
          htmlFor="status-filter"
          className="text-sm font-medium text-gray-700"
        >
          ステータスフィルター
        </label>
        <select
          id="status-filter"
          value={selectedStatus}
          onChange={handleStatusFilterChange}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="ステータスフィルター"
        >
          <option value="">すべて</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* Inquiry Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                内容
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ステータス
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                作成日時
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.data.map((inquiry) => (
              <tr
                key={inquiry.id}
                onClick={() => handleRowClick(inquiry.id)}
                className="hover:bg-gray-50 cursor-pointer"
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  #{inquiry.id}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  {truncateContent(inquiry.content)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                    {STATUS_LABELS[inquiry.status]}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatTimestamp(inquiry.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
        <div className="flex flex-1 justify-between sm:hidden">
          <button
            onClick={handlePrevPage}
            disabled={currentPage === 1}
            className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            前へ
          </button>
          <button
            onClick={handleNextPage}
            disabled={!data.meta.has_next}
            className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            次へ
          </button>
        </div>
        <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-gray-700">
              全 <span className="font-medium">{data.meta.total}</span> 件中{" "}
              <span className="font-medium">
                {(currentPage - 1) * limit + 1}
              </span>{" "}
              -{" "}
              <span className="font-medium">
                {Math.min(currentPage * limit, data.meta.total)}
              </span>{" "}
              件を表示
            </p>
          </div>
          <div>
            <nav
              className="isolate inline-flex -space-x-px rounded-md shadow-sm"
              aria-label="Pagination"
            >
              <button
                onClick={handlePrevPage}
                disabled={currentPage === 1}
                className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="sr-only">前へ</span>
                前へ
              </button>
              <span className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300">
                {currentPage}
              </span>
              <button
                onClick={handleNextPage}
                disabled={!data.meta.has_next}
                className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="sr-only">次へ</span>
                次へ
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InquiryList;
