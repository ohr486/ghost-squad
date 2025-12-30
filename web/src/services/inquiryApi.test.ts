/**
 * 問い合わせAPI クライアント - ユニットテスト
 */

import type {
  InquiryResponse,
  CreateInquiryRequest,
  PaginatedResponse,
  ErrorResponse,
} from "../types";
import axios from "axios";
import {
  createInquiry,
  listInquiries,
  getInquiry,
  updateInquiry,
  approveInquiry,
  rejectInquiry,
  healthCheck,
} from "./inquiryApi";

// axiosのマニュアルモックを使用（jest.mockはホイストされるため、インポート後に記述可能）
jest.mock("axios");

// モックインスタンスを型安全に取得
// __mocks__/axios.ts で export した mockAxiosInstance にアクセス
const mockAxiosInstance = (axios as any).create() as {
  get: jest.Mock;
  post: jest.Mock;
  put: jest.Mock;
  delete: jest.Mock;
};

// Get the applyErrorInterceptor helper from the mocked module
const axiosMock = axios as any;
const applyErrorInterceptor = axiosMock.applyErrorInterceptor;

describe("inquiryApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("createInquiry", () => {
    it("should create an inquiry successfully", async () => {
      const requestData: CreateInquiryRequest = {
        user_id: "test_user",
        content: "テスト問い合わせ",
        source_system: "manual",
      };

      const responseData: InquiryResponse = {
        id: 1,
        user_id: "test_user",
        content: "テスト問い合わせ",
        source_system: "manual",
        timestamp: "2025-12-30T00:00:00Z",
        status: "received",
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:00Z",
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData });

      const result = await createInquiry(requestData);

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/api/inquiries",
        requestData,
      );
    });
  });

  describe("listInquiries", () => {
    it("should list inquiries with pagination", async () => {
      const responseData: PaginatedResponse<InquiryResponse> = {
        data: [
          {
            id: 1,
            user_id: "test_user",
            content: "テスト問い合わせ1",
            source_system: "manual",
            timestamp: "2025-12-30T00:00:00Z",
            status: "received",
            created_at: "2025-12-30T00:00:00Z",
            updated_at: "2025-12-30T00:00:00Z",
          },
        ],
        meta: {
          page: 1,
          limit: 20,
          total: 1,
          has_next: false,
        },
        timestamp: "2025-12-30T00:00:00Z",
      };

      mockAxiosInstance.get.mockResolvedValueOnce({ data: responseData });

      const result = await listInquiries({ page: 1, limit: 20 });

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.get).toHaveBeenCalled();
    });
  });

  describe("getInquiry", () => {
    it("should get inquiry by id", async () => {
      const responseData: InquiryResponse = {
        id: 1,
        user_id: "test_user",
        content: "テスト問い合わせ",
        source_system: "manual",
        timestamp: "2025-12-30T00:00:00Z",
        status: "received",
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:00Z",
      };

      mockAxiosInstance.get.mockResolvedValueOnce({ data: responseData });

      const result = await getInquiry(1);

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith("/api/inquiries/1");
    });
  });

  describe("updateInquiry", () => {
    it("should update inquiry successfully", async () => {
      const updateData = {
        content: "更新された問い合わせ",
      };

      const responseData: InquiryResponse = {
        id: 1,
        user_id: "test_user",
        content: "更新された問い合わせ",
        source_system: "manual",
        timestamp: "2025-12-30T00:00:00Z",
        status: "received",
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:01Z",
      };

      mockAxiosInstance.put.mockResolvedValueOnce({ data: responseData });

      const result = await updateInquiry(1, updateData);

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        "/api/inquiries/1",
        updateData,
      );
    });
  });

  describe("approveInquiry", () => {
    it("should approve inquiry successfully", async () => {
      const responseData: InquiryResponse = {
        id: 1,
        user_id: "test_user",
        content: "テスト問い合わせ",
        source_system: "manual",
        timestamp: "2025-12-30T00:00:00Z",
        status: "task_working",
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:01Z",
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData });

      const result = await approveInquiry(1);

      expect(result).toEqual(responseData);
      expect(result.status).toBe("task_working");
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/api/inquiries/1/approve",
      );
    });
  });

  describe("rejectInquiry", () => {
    it("should reject inquiry with reason", async () => {
      const responseData: InquiryResponse = {
        id: 1,
        user_id: "test_user",
        content: "テスト問い合わせ",
        source_system: "manual",
        timestamp: "2025-12-30T00:00:00Z",
        status: "rejected",
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:01Z",
        inquiry_metadata: {
          rejection: {
            reason: "テスト却下",
            rejected_at: "2025-12-30T00:00:01Z",
          },
        },
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData });

      const result = await rejectInquiry(1, { reason: "テスト却下" });

      expect(result).toEqual(responseData);
      expect(result.status).toBe("rejected");
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/api/inquiries/1/reject",
        { reason: "テスト却下" },
      );
    });
  });

  describe("healthCheck", () => {
    it("should check health successfully", async () => {
      const responseData = { status: "ok" };

      mockAxiosInstance.get.mockResolvedValueOnce({ data: responseData });

      const result = await healthCheck();

      expect(result).toEqual(responseData);
      expect(result.status).toBe("ok");
      expect(mockAxiosInstance.get).toHaveBeenCalledWith("/health");
    });
  });

  describe("Error Handling", () => {
    it("should handle backend error responses with ErrorResponse structure", async () => {
      const backendError: ErrorResponse = {
        errors: [
          {
            code: "VALIDATION_ERROR",
            message: "Invalid input data",
            field: "content",
          },
        ],
        timestamp: "2025-12-30T00:00:00Z",
      };

      // Simulate a backend error response and apply interceptor
      const axiosError = {
        response: {
          data: backendError,
        },
      };

      mockAxiosInstance.post.mockImplementationOnce(() =>
        applyErrorInterceptor(axiosError),
      );

      await expect(
        createInquiry({
          user_id: "test_user",
          content: "",
          source_system: "manual",
        }),
      ).rejects.toEqual(backendError);
    });

    it("should transform network errors to generic NETWORK_ERROR format", async () => {
      // Simulate a network error (no response from backend)
      const networkError = {
        message: "Network Error",
        // No response property - simulates connection failure
      };

      mockAxiosInstance.get.mockImplementationOnce(() =>
        applyErrorInterceptor(networkError),
      );

      await expect(getInquiry(1)).rejects.toMatchObject({
        errors: [
          {
            code: "NETWORK_ERROR",
            message: expect.stringContaining("ネットワークエラー"),
          },
        ],
        timestamp: expect.any(String),
      });
    });

    it("should pass through error.response.data when available", async () => {
      const backendError: ErrorResponse = {
        errors: [
          {
            code: "NOT_FOUND",
            message: "Inquiry not found",
          },
        ],
        timestamp: "2025-12-30T00:00:00Z",
      };

      // Simulate a 404 error from backend
      const axiosError = {
        response: {
          status: 404,
          data: backendError,
        },
      };

      mockAxiosInstance.get.mockImplementationOnce(() =>
        applyErrorInterceptor(axiosError),
      );

      await expect(getInquiry(999)).rejects.toEqual(backendError);
    });

    it("should handle server errors with proper structure", async () => {
      const serverError: ErrorResponse = {
        errors: [
          {
            code: "INTERNAL_ERROR",
            message: "Internal server error occurred",
          },
        ],
        timestamp: "2025-12-30T00:00:00Z",
      };

      const axiosError = {
        response: {
          status: 500,
          data: serverError,
        },
      };

      mockAxiosInstance.put.mockImplementationOnce(() =>
        applyErrorInterceptor(axiosError),
      );

      await expect(updateInquiry(1, { content: "test" })).rejects.toEqual(
        serverError,
      );
    });

    it("should handle timeout errors as network errors", async () => {
      // Simulate a timeout error
      const timeoutError = {
        code: "ECONNABORTED",
        message: "timeout of 30000ms exceeded",
      };

      mockAxiosInstance.post.mockImplementationOnce(() =>
        applyErrorInterceptor(timeoutError),
      );

      await expect(approveInquiry(1)).rejects.toMatchObject({
        errors: [
          {
            code: "NETWORK_ERROR",
          },
        ],
        timestamp: expect.any(String),
      });
    });
  });
});
