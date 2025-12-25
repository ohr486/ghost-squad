import { InquiryService } from "./inquiryService";
import apiClient from "./apiClient";
import type { InquiryCreateRequest, InquiryResponse } from "../types/api";

// Mock the apiClient module
jest.mock("./apiClient");

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe("InquiryService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("createInquiry", () => {
    it("should create an inquiry successfully", async () => {
      const mockRequest: InquiryCreateRequest = {
        content: "テスト問い合わせ内容です。",
        language: "ja",
        user_id: "user-001",
      };

      const mockResponse: InquiryResponse = {
        id: 1,
        user_id: "user-001",
        content: "テスト問い合わせ内容です。",
        language: "ja",
        timestamp: "2024-01-01T00:00:00Z",
        status: "received" as any,
        metadata: {
          source: "web",
        },
      };

      mockApiClient.post.mockResolvedValue({ data: mockResponse });

      const result = await InquiryService.createInquiry(mockRequest);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        "/api/inquiries",
        mockRequest,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle creation error", async () => {
      const mockRequest: InquiryCreateRequest = {
        content: "テスト問い合わせ内容です。",
        language: "ja",
        user_id: "user-001",
      };

      const mockError = new Error("Network error");
      mockApiClient.post.mockRejectedValue(mockError);

      await expect(InquiryService.createInquiry(mockRequest)).rejects.toThrow(
        "Network error",
      );
      expect(mockApiClient.post).toHaveBeenCalledWith(
        "/api/inquiries",
        mockRequest,
      );
    });

    it("should create inquiry with English language", async () => {
      const mockRequest: InquiryCreateRequest = {
        content: "This is a test inquiry.",
        language: "en",
        user_id: "user-002",
      };

      const mockResponse: InquiryResponse = {
        id: 2,
        user_id: "user-002",
        content: "This is a test inquiry.",
        language: "en",
        timestamp: "2024-01-01T00:00:00Z",
        status: "received" as any,
        metadata: {
          source: "web",
        },
      };

      mockApiClient.post.mockResolvedValue({ data: mockResponse });

      const result = await InquiryService.createInquiry(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(result.language).toBe("en");
    });
  });

  describe("getInquiries", () => {
    it("should get inquiries with default pagination", async () => {
      const mockResponse = {
        data: [
          {
            id: 1,
            user_id: "user-001",
            content: "First inquiry",
            language: "ja" as const,
            timestamp: "2024-01-01T00:00:00Z",
            status: "received" as any,
            metadata: { source: "web" },
          },
          {
            id: 2,
            user_id: "user-001",
            content: "Second inquiry",
            language: "ja" as const,
            timestamp: "2024-01-02T00:00:00Z",
            status: "processing" as any,
            metadata: { source: "web" },
          },
        ],
        meta: {
          page: 1,
          limit: 20,
          total: 2,
          has_next: false,
        },
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await InquiryService.getInquiries();

      expect(mockApiClient.get).toHaveBeenCalledWith("/api/inquiries", {
        params: { page: 1, limit: 20 },
      });
      expect(result).toEqual(mockResponse);
      expect(result.data).toHaveLength(2);
    });

    it("should get inquiries with custom pagination", async () => {
      const mockResponse = {
        data: [
          {
            id: 3,
            user_id: "user-001",
            content: "Third inquiry",
            language: "ja" as const,
            timestamp: "2024-01-03T00:00:00Z",
            status: "completed" as any,
            metadata: { source: "web" },
          },
        ],
        meta: {
          page: 2,
          limit: 10,
          total: 11,
          has_next: false,
        },
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await InquiryService.getInquiries(2, 10);

      expect(mockApiClient.get).toHaveBeenCalledWith("/api/inquiries", {
        params: { page: 2, limit: 10 },
      });
      expect(result.meta.page).toBe(2);
      expect(result.meta.limit).toBe(10);
    });

    it("should handle get inquiries error", async () => {
      const mockError = new Error("Failed to fetch inquiries");
      mockApiClient.get.mockRejectedValue(mockError);

      await expect(InquiryService.getInquiries()).rejects.toThrow(
        "Failed to fetch inquiries",
      );
    });

    it("should return has_next flag correctly", async () => {
      const mockResponse = {
        data: [],
        meta: {
          page: 1,
          limit: 20,
          total: 25,
          has_next: true,
        },
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await InquiryService.getInquiries(1, 20);

      expect(result.meta.has_next).toBe(true);
      expect(result.meta.total).toBe(25);
    });
  });

  describe("getInquiry", () => {
    it("should get a single inquiry by ID", async () => {
      const mockResponse: InquiryResponse = {
        id: 1,
        user_id: "user-001",
        content: "Test inquiry content",
        language: "ja",
        timestamp: "2024-01-01T00:00:00Z",
        status: "received" as any,
        metadata: {
          source: "web",
        },
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await InquiryService.getInquiry(1);

      expect(mockApiClient.get).toHaveBeenCalledWith("/api/inquiries/1");
      expect(result).toEqual(mockResponse);
      expect(result.id).toBe(1);
    });

    it("should handle get inquiry error for non-existent ID", async () => {
      const mockError = new Error("Inquiry not found");
      mockApiClient.get.mockRejectedValue(mockError);

      await expect(InquiryService.getInquiry(999)).rejects.toThrow(
        "Inquiry not found",
      );
      expect(mockApiClient.get).toHaveBeenCalledWith("/api/inquiries/999");
    });

    it("should get inquiry with different statuses", async () => {
      const mockResponse: InquiryResponse = {
        id: 2,
        user_id: "user-002",
        content: "Processing inquiry",
        language: "en",
        timestamp: "2024-01-01T00:00:00Z",
        status: "processing" as any,
        metadata: {
          source: "api",
        },
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await InquiryService.getInquiry(2);

      expect(result.status).toBe("processing");
    });
  });

  describe("updateInquiry", () => {
    it("should update an inquiry successfully", async () => {
      const mockUpdateData = {
        content: "Updated content",
        status: "completed" as any,
      };

      const mockResponse: InquiryResponse = {
        id: 1,
        user_id: "user-001",
        content: "Updated content",
        language: "ja",
        timestamp: "2024-01-01T00:00:00Z",
        status: "completed" as any,
        metadata: {
          source: "web",
        },
      };

      mockApiClient.put.mockResolvedValue({ data: mockResponse });

      const result = await InquiryService.updateInquiry(1, mockUpdateData);

      expect(mockApiClient.put).toHaveBeenCalledWith(
        "/api/inquiries/1",
        mockUpdateData,
      );
      expect(result).toEqual(mockResponse);
      expect(result.status).toBe("completed");
    });

    it("should handle partial updates", async () => {
      const mockUpdateData = {
        status: "processing" as any,
      };

      const mockResponse: InquiryResponse = {
        id: 2,
        user_id: "user-001",
        content: "Original content",
        language: "ja",
        timestamp: "2024-01-01T00:00:00Z",
        status: "processing" as any,
        metadata: {
          source: "web",
        },
      };

      mockApiClient.put.mockResolvedValue({ data: mockResponse });

      const result = await InquiryService.updateInquiry(2, mockUpdateData);

      expect(mockApiClient.put).toHaveBeenCalledWith(
        "/api/inquiries/2",
        mockUpdateData,
      );
      expect(result.status).toBe("processing");
    });

    it("should handle update error when endpoint not implemented", async () => {
      const mockUpdateData = {
        content: "Updated content",
      };

      const mockError = new Error("Endpoint not implemented");
      mockApiClient.put.mockRejectedValue(mockError);

      await expect(
        InquiryService.updateInquiry(1, mockUpdateData),
      ).rejects.toThrow("Endpoint not implemented");
      expect(mockApiClient.put).toHaveBeenCalledWith(
        "/api/inquiries/1",
        mockUpdateData,
      );
    });

    it("should update inquiry metadata", async () => {
      const mockUpdateData = {
        metadata: {
          source: "api",
          updated_by: "admin",
        },
      };

      const mockResponse: InquiryResponse = {
        id: 3,
        user_id: "user-001",
        content: "Test content",
        language: "ja",
        timestamp: "2024-01-01T00:00:00Z",
        status: "received" as any,
        metadata: {
          source: "api",
          updated_by: "admin",
        },
      };

      mockApiClient.put.mockResolvedValue({ data: mockResponse });

      const result = await InquiryService.updateInquiry(3, mockUpdateData);

      expect(result.metadata).toEqual({
        source: "api",
        updated_by: "admin",
      });
    });
  });
});
