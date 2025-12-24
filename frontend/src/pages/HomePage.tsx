import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MessageSquare, CheckSquare, Zap, ArrowRight } from "lucide-react";
import apiClient from "../services/apiClient";

const HomePage: React.FC = () => {
  const [apiStatus, setApiStatus] = useState<"loading" | "connected" | "error">(
    "loading",
  );
  const [apiMessage, setApiMessage] = useState<string>("");

  useEffect(() => {
    // Check API connection
    const checkApiConnection = async () => {
      try {
        await apiClient.get("/health");
        setApiStatus("connected");
        setApiMessage("バックエンドAPIに正常に接続されています");
      } catch (error) {
        setApiStatus("error");
        setApiMessage("バックエンドAPIに接続できませんでした");
      }
    };

    checkApiConnection();
  }, []);

  const features = [
    {
      name: "問い合わせ管理",
      description: "自然言語での問い合わせを入力し、AIがストーリーに変換します",
      icon: MessageSquare,
      href: "/inquiries",
      color: "text-blue-600 dark:text-blue-400",
      bgColor: "bg-blue-100 dark:bg-blue-900/20",
    },
    {
      name: "タスク管理",
      description: "生成されたストーリーをレビューし、タスクとして管理します",
      icon: CheckSquare,
      href: "/tasks",
      color: "text-green-600 dark:text-green-400",
      bgColor: "bg-green-100 dark:bg-green-900/20",
    },
    {
      name: "AI統合",
      description: "OpenAI APIを使用した高精度なストーリー生成機能",
      icon: Zap,
      href: "/inquiries",
      color: "text-purple-600 dark:text-purple-400",
      bgColor: "bg-purple-100 dark:bg-purple-900/20",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white sm:text-5xl">
          Ghost Squad
        </h1>
        <p className="mt-4 text-xl text-gray-600 dark:text-gray-300">
          AI駆動ストーリーボード機能
        </p>
        <p className="mt-2 text-lg text-gray-500 dark:text-gray-400">
          自然言語の問い合わせを構造化されたユーザーストーリーに変換
        </p>
      </div>

      {/* API Status */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border dark:border-gray-700 p-6">
        <div className="flex items-center">
          <div
            className={`w-3 h-3 rounded-full mr-3 ${
              apiStatus === "connected"
                ? "bg-green-500"
                : apiStatus === "error"
                  ? "bg-red-500"
                  : "bg-yellow-500"
            }`}
          />
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            システム状態:
          </span>
          <span
            className={`ml-2 text-sm ${
              apiStatus === "connected"
                ? "text-green-600 dark:text-green-400"
                : apiStatus === "error"
                  ? "text-red-600 dark:text-red-400"
                  : "text-yellow-600 dark:text-yellow-400"
            }`}
          >
            {apiStatus === "loading" ? "確認中..." : apiMessage}
          </span>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Link
              key={feature.name}
              to={feature.href}
              className="group relative bg-white dark:bg-gray-800 p-6 rounded-lg shadow border dark:border-gray-700 hover:shadow-md dark:hover:shadow-lg transition-shadow duration-200"
            >
              <div>
                <span
                  className={`inline-flex p-3 rounded-lg ${feature.bgColor}`}
                >
                  <Icon className={`w-6 h-6 ${feature.color}`} />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-200">
                  {feature.name}
                  <ArrowRight className="inline-block w-4 h-4 ml-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                </h3>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  {feature.description}
                </p>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border dark:border-gray-700 p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          クイックアクション
        </h2>
        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            to="/inquiries"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 transition-colors duration-200"
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            新しい問い合わせを作成
          </Link>
          <Link
            to="/tasks"
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors duration-200"
          >
            <CheckSquare className="w-4 h-4 mr-2" />
            タスクを確認
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
