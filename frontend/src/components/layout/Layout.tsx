import React from "react";
import { Link, useLocation } from "react-router-dom";
import { MessageSquare, CheckSquare, Home, Moon, Sun } from "lucide-react";
import { useDarkMode } from "../../hooks/useDarkMode";

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const { isDarkMode, toggleDarkMode } = useDarkMode();

  const navigation = [
    { name: "ホーム", href: "/", icon: Home },
    { name: "問い合わせ", href: "/inquiries", icon: MessageSquare },
    { name: "タスク", href: "/tasks", icon: CheckSquare },
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Navigation Header */}
      <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              {/* Logo */}
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Ghost Squad
                </h1>
                <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                  ストーリーボード
                </span>
              </div>

              {/* Navigation Links */}
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`${
                        isActive(item.href)
                          ? "border-blue-500 text-gray-900 dark:text-white"
                          : "border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-300"
                      } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors duration-200`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Dark Mode Toggle */}
            <div className="flex items-center">
              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
                aria-label={
                  isDarkMode
                    ? "ライトモードに切り替え"
                    : "ダークモードに切り替え"
                }
              >
                {isDarkMode ? (
                  <Sun className="w-5 h-5" />
                ) : (
                  <Moon className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        <div className="sm:hidden">
          <div className="pt-2 pb-3 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`${
                    isActive(item.href)
                      ? "bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-700 dark:text-blue-300"
                      : "border-transparent text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-300"
                  } block pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-colors duration-200`}
                >
                  <div className="flex items-center">
                    <Icon className="w-4 h-4 mr-3" />
                    {item.name}
                  </div>
                </Link>
              );
            })}

            {/* Mobile Dark Mode Toggle */}
            <div className="pl-3 pr-4 py-2">
              <button
                onClick={toggleDarkMode}
                className="flex items-center w-full text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors duration-200"
                aria-label={
                  isDarkMode
                    ? "ライトモードに切り替え（モバイル）"
                    : "ダークモードに切り替え（モバイル）"
                }
              >
                {isDarkMode ? (
                  <>
                    <Sun className="w-4 h-4 mr-3" />
                    ライトモード
                  </>
                ) : (
                  <>
                    <Moon className="w-4 h-4 mr-3" />
                    ダークモード
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">{children}</div>
      </main>
    </div>
  );
};

export default Layout;
