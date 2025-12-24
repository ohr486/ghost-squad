import apiClient from "./apiClient";
import type { InquiryCreateRequest, InquiryResponse } from "../types/api";
import type { Inquiry } from "../types/models";

export class InquiryService {
  /**
   * Create a new inquiry
   */
  static async createInquiry(
    data: InquiryCreateRequest,
  ): Promise<InquiryResponse> {
    const response = await apiClient.post<InquiryResponse>(
      "/api/inquiries",
      data,
    );
    return response.data;
  }

  /**
   * Get all inquiries with pagination
   */
  static async getInquiries(
    page: number = 1,
    limit: number = 20,
  ): Promise<{
    data: InquiryResponse[];
    meta: {
      page: number;
      limit: number;
      total: number;
      has_next: boolean;
    };
  }> {
    const response = await apiClient.get<{
      data: InquiryResponse[];
      meta: {
        page: number;
        limit: number;
        total: number;
        has_next: boolean;
      };
    }>("/api/inquiries", {
      params: { page, limit },
    });
    return response.data;
  }

  /**
   * Get a specific inquiry by ID
   */
  static async getInquiry(id: number): Promise<InquiryResponse> {
    const response = await apiClient.get<InquiryResponse>(
      `/api/inquiries/${id}`,
    );
    return response.data;
  }

  /**
   * Update an inquiry (future implementation)
   */
  static async updateInquiry(
    id: number,
    data: Partial<Inquiry>,
  ): Promise<InquiryResponse> {
    const response = await apiClient.put<InquiryResponse>(
      `/api/inquiries/${id}`,
      data,
    );
    return response.data;
  }
}

export default InquiryService;
