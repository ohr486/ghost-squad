import React from "react";
import { CheckSquare, Filter } from "lucide-react";

const TasksPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
            <CheckSquare className="w-6 h-6 mr-2" />
            タスク管理
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            生成されたストーリーをレビューし、タスクとして管理します
          </p>
        </div>
        <button className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors duration-200">
          <Filter className="w-4 h-4 mr-2" />
          フィルター
        </button>
      </div>

      {/* Content Area */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border dark:border-gray-700">
        <div className="p-6">
          <div className="text-center py-12">
            <CheckSquare className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              タスク一覧
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              この機能は将来のタスクで実装予定です
            </p>
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-4 max-w-md mx-auto">
              <p className="text-sm text-green-800 dark:text-green-300">
                <strong>実装予定:</strong>
                <br />
                • ストーリー一覧表示
                <br />
                • ストーリーレビュー機能
                <br />
                • 承認・拒否ワークフロー
                <br />• 外部システム連携
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TasksPage;
