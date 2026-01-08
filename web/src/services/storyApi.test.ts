/**
 * ストーリーAPI クライアント - ユニットテスト
 * 要件: 2.1, 2.5, 2.6
 */

import type {
  StoryResponse,
  CreateStoryRequest,
  PaginatedResponse,
  ErrorResponse,
  BatchApproveResponse,
} from "../types";
import axios from "axios";
import {
  createStory,
  generateStory,
  listStories,
  listStoriesByInquiry,
  getStory,
  updateStory,
  deleteStory,
  approveStory,
  rejectStory,
  batchApproveStories,
} from "./storyApi";

// axiosのマニュアルモックを使用
jest.mock("axios");

// モックインスタンスを型安全に取得
const mockAxiosInstance = (axios as any).create() as {
  get: jest.Mock;
  post: jest.Mock;
  put: jest.Mock;
  delete: jest.Mock;
};

// Get the applyErrorInterceptor helper from the mocked module
const axiosMock = axios as any;
const applyErrorInterceptor = axiosMock.applyErrorInterceptor;

describe("storyApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("createStory", () => {
    it("should create a story manually", async () => {
      const inquiryId = 1;
      const requestData: CreateStoryRequest = {
        title: "新しいストーリー",
        description: "ストーリーの説明",
        priority: "medium",
        estimated_effort: 5,
      };

      const responseData: StoryResponse = {
        id: 1,
        inquiry_id: inquiryId,
        title: "新しいストーリー",
        description: "ストーリーの説明",
        priority: "medium",
        status: "waiting_review",
        estimated_effort: 5,
        deadline: null,
        assignee: null,
        story_metadata: {},
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:00Z",
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData });

      const result = await createStory(inquiryId, requestData);

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        `/api/inquiries/${inquiryId}/stories`,
        requestData,
      );
    });

    it("should handle validation errors", async () => {
      const inquiryId = 1;
      const requestData: CreateStoryRequest = {
        title: "",
        description: "説明",
        priority: "medium",
      };

      const errorResponse: ErrorResponse = {
        errors: [
          {
            code: "GS-201",
            message: "タイトルは必須です",
            field: "title",
          },
        ],
        timestamp: "2025-12-30T00:00:00Z",
      };

      const axiosError = {
        response: {
          data: errorResponse,
        },
      };

      mockAxiosInstance.post.mockImplementationOnce(() =>
        applyErrorInterceptor(axiosError),
      );

      await expect(createStory(inquiryId, requestData)).rejects.toEqual(
        errorResponse,
      );
    });
  });

  describe("generateStory", () => {
    it("should generate a story using AI", async () => {
      const inquiryId = 1;

      const responseData: StoryResponse = {
        id: 1,
        inquiry_id: inquiryId,
        title: "AI生成ストーリー",
        description: "AI生成の説明",
        priority: "medium",
        status: "waiting_review",
        estimated_effort: null,
        deadline: null,
        assignee: null,
        story_metadata: {},
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:00Z",
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData });

      const result = await generateStory(inquiryId);

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        `/api/inquiries/${inquiryId}/stories`,
        {},
      );
    });

    it("should handle AI generation errors", async () => {
      const inquiryId = 1;

      const errorResponse: ErrorResponse = {
        errors: [
          {
            code: "GS-206",
            message: "AI生成に失敗しました",
          },
        ],
        timestamp: "2025-12-30T00:00:00Z",
      };

      const axiosError = {
        response: {
          data: errorResponse,
        },
      };

      mockAxiosInstance.post.mockImplementationOnce(() =>
        applyErrorInterceptor(axiosError),
      );

      await expect(generateStory(inquiryId)).rejects.toEqual(errorResponse);
    });
  });

  describe("listStories", () => {
    it("should list all stories with pagination", async () => {
      const responseData: PaginatedResponse<StoryResponse> = {
        data: [
          {
            id: 1,
            inquiry_id: 1,
            title: "ストーリー1",
            description: "説明1",
            priority: "medium",
            status: "waiting_review",
            estimated_effort: 5,
            deadline: null,
            assignee: null,
            story_metadata: {},
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

      const result = await listStories({ page: 1, limit: 20 });

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.get).toHaveBeenCalled();
    });

    it("should handle filtering by status and priority", async () => {
      const responseData: PaginatedResponse<StoryResponse> = {
        data: [],
        meta: {
          page: 1,
          limit: 20,
          total: 0,
          has_next: false,
        },
        timestamp: "2025-12-30T00:00:00Z",
      };

      mockAxiosInstance.get.mockResolvedValueOnce({ data: responseData });

      await listStories({
        status: "approved",
        priority: "high",
      });

      expect(mockAxiosInstance.get).toHaveBeenCalled();
    });
  });

  describe("listStoriesByInquiry", () => {
    it("should list stories for a specific inquiry", async () => {
      const inquiryId = 1;

      const responseData: PaginatedResponse<StoryResponse> = {
        data: [
          {
            id: 1,
            inquiry_id: inquiryId,
            title: "ストーリー1",
            description: "説明1",
            priority: "medium",
            status: "waiting_review",
            estimated_effort: 5,
            deadline: null,
            assignee: null,
            story_metadata: {},
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

      const result = await listStoriesByInquiry(inquiryId);

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        `/api/inquiries/${inquiryId}/stories`,
        { params: {} },
      );
    });
  });

  describe("getStory", () => {
    it("should get story by id", async () => {
      const responseData: StoryResponse = {
        id: 1,
        inquiry_id: 1,
        title: "ストーリー",
        description: "説明",
        priority: "medium",
        status: "waiting_review",
        estimated_effort: 5,
        deadline: null,
        assignee: null,
        story_metadata: {},
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:00Z",
      };

      mockAxiosInstance.get.mockResolvedValueOnce({ data: responseData });

      const result = await getStory(1);

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith("/api/stories/1");
    });

    it("should handle 404 errors", async () => {
      const errorResponse: ErrorResponse = {
        errors: [
          {
            code: "NOT_FOUND",
            message: "ストーリーが見つかりません",
          },
        ],
        timestamp: "2025-12-30T00:00:00Z",
      };

      const axiosError = {
        response: {
          status: 404,
          data: errorResponse,
        },
      };

      mockAxiosInstance.get.mockImplementationOnce(() =>
        applyErrorInterceptor(axiosError),
      );

      await expect(getStory(999)).rejects.toEqual(errorResponse);
    });
  });

  describe("updateStory", () => {
    it("should update story successfully", async () => {
      const updateData = {
        title: "更新されたストーリー",
        estimated_effort: 8,
      };

      const responseData: StoryResponse = {
        id: 1,
        inquiry_id: 1,
        title: "更新されたストーリー",
        description: "説明",
        priority: "medium",
        status: "waiting_review",
        estimated_effort: 8,
        deadline: null,
        assignee: null,
        story_metadata: {},
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:01Z",
      };

      mockAxiosInstance.put.mockResolvedValueOnce({ data: responseData });

      const result = await updateStory(1, updateData);

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        "/api/stories/1",
        updateData,
      );
    });
  });

  describe("deleteStory", () => {
    it("should delete story successfully", async () => {
      const responseData = { success: true };

      mockAxiosInstance.delete.mockResolvedValueOnce({ data: responseData });

      const result = await deleteStory(1);

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith("/api/stories/1");
    });
  });

  describe("approveStory", () => {
    it("should approve story successfully", async () => {
      const approveData = {
        approver: "test_user",
      };

      const responseData: StoryResponse = {
        id: 1,
        inquiry_id: 1,
        title: "ストーリー",
        description: "説明",
        priority: "medium",
        status: "approved",
        estimated_effort: 5,
        deadline: null,
        assignee: null,
        story_metadata: {
          approval: {
            approved_at: "2025-12-30T00:00:01Z",
            approver: "test_user",
          },
        },
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:01Z",
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData });

      const result = await approveStory(1, approveData);

      expect(result).toEqual(responseData);
      expect(result.status).toBe("approved");
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/api/stories/1/approve",
        approveData,
      );
    });

    it("should handle invalid status transition", async () => {
      const approveData = {
        approver: "test_user",
      };

      const errorResponse: ErrorResponse = {
        errors: [
          {
            code: "GS-203",
            message: "waiting_review状態のみ承認可能です",
          },
        ],
        timestamp: "2025-12-30T00:00:00Z",
      };

      const axiosError = {
        response: {
          status: 422,
          data: errorResponse,
        },
      };

      mockAxiosInstance.post.mockImplementationOnce(() =>
        applyErrorInterceptor(axiosError),
      );

      await expect(approveStory(1, approveData)).rejects.toEqual(errorResponse);
    });
  });

  describe("rejectStory", () => {
    it("should reject story with reason", async () => {
      const rejectData = {
        rejector: "test_user",
        reason: "要件が不明確",
      };

      const responseData: StoryResponse = {
        id: 1,
        inquiry_id: 1,
        title: "ストーリー",
        description: "説明",
        priority: "medium",
        status: "rejected",
        estimated_effort: 5,
        deadline: null,
        assignee: null,
        story_metadata: {
          rejection: {
            rejected_at: "2025-12-30T00:00:01Z",
            rejector: "test_user",
            reason: "要件が不明確",
          },
        },
        created_at: "2025-12-30T00:00:00Z",
        updated_at: "2025-12-30T00:00:01Z",
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData });

      const result = await rejectStory(1, rejectData);

      expect(result).toEqual(responseData);
      expect(result.status).toBe("rejected");
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/api/stories/1/reject",
        rejectData,
      );
    });

    it("should handle missing rejection reason", async () => {
      const rejectData = {
        rejector: "test_user",
        reason: "",
      };

      const errorResponse: ErrorResponse = {
        errors: [
          {
            code: "GS-207",
            message: "却下理由は必須です",
          },
        ],
        timestamp: "2025-12-30T00:00:00Z",
      };

      const axiosError = {
        response: {
          status: 400,
          data: errorResponse,
        },
      };

      mockAxiosInstance.post.mockImplementationOnce(() =>
        applyErrorInterceptor(axiosError),
      );

      await expect(rejectStory(1, rejectData)).rejects.toEqual(errorResponse);
    });
  });

  describe("batchApproveStories", () => {
    it("should batch approve multiple stories", async () => {
      const batchData = {
        story_ids: [1, 2, 3],
        approver: "test_user",
      };

      const responseData: BatchApproveResponse = {
        results: [
          { id: 1, success: true },
          { id: 2, success: true },
          { id: 3, success: false, error: "ステータスが無効です" },
        ],
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData });

      const result = await batchApproveStories(batchData);

      expect(result).toEqual(responseData);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/api/stories/batch-approve",
        batchData,
      );
    });
  });

  describe("Error handling", () => {
    it("should handle network errors", async () => {
      const networkError = {
        message: "Network Error",
        // No response property - simulates connection failure
      };

      mockAxiosInstance.get.mockImplementationOnce(() =>
        applyErrorInterceptor(networkError),
      );

      await expect(getStory(1)).rejects.toMatchObject({
        errors: [
          {
            code: "NETWORK_ERROR",
            message: expect.stringContaining("ネットワークエラー"),
          },
        ],
        timestamp: expect.any(String),
      });
    });

    it("should handle timeout errors", async () => {
      const timeoutError = {
        code: "ECONNABORTED",
        message: "timeout of 30000ms exceeded",
      };

      mockAxiosInstance.post.mockImplementationOnce(() =>
        applyErrorInterceptor(timeoutError),
      );

      await expect(generateStory(1)).rejects.toMatchObject({
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
