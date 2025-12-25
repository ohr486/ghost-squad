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
    const response = await apiClient.post<InquiryResponse>("/inquiries", data);
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
    }>("/inquiries", {
      params: { page, limit },
    });
    return response.data;
  }

  /**
   * Get a specific inquiry by ID
   */
  static async getInquiry(id: number): Promise<InquiryResponse> {
    const response = await apiClient.get<InquiryResponse>(`/inquiries/${id}`);
    return response.data;
  }

  /**
   * Update an inquiry
   *
   * @param id - The inquiry ID to update
   * @param data - Partial inquiry data to update
   * @returns Promise<InquiryResponse> - The updated inquiry
   *
   * @note This method is fully implemented on the frontend but requires
   *       the backend PUT /inquiries/{id} endpoint to be implemented.
   *       Currently returns a network error as the endpoint does not exist.
   */
  static async updateInquiry(
    id: number,
    data: Partial<Inquiry>,
  ): Promise<InquiryResponse> {
    const response = await apiClient.put<InquiryResponse>(
      `/inquiries/${id}`,
      data,
    );
    return response.data;
  }
}

export default InquiryService;
