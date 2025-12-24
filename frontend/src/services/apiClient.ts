import axios, { AxiosInstance, AxiosResponse, AxiosError } from "axios";
import toast from "react-hot-toast";

// API base configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem("authToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle common errors
    if (error.response) {
      const status = error.response.status;
      const message =
        (error.response.data as any)?.message || "エラーが発生しました";

      switch (status) {
        case 400:
          toast.error(`入力エラー: ${message}`);
          break;
        case 401:
          toast.error("認証が必要です");
          // Redirect to login if needed
          break;
        case 403:
          toast.error("アクセス権限がありません");
          break;
        case 404:
          toast.error("リソースが見つかりません");
          break;
        case 500:
          toast.error("サーバーエラーが発生しました");
          break;
        default:
          toast.error(`エラー: ${message}`);
      }
    } else if (error.request) {
      toast.error("ネットワークエラーが発生しました");
    } else {
      toast.error("予期しないエラーが発生しました");
    }

    return Promise.reject(error);
  },
);

export default apiClient;
