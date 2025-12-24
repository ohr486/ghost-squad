/**
 * API response types
 */
import { InquiryStatus, StoryStatus, StoryCategory, Priority } from "../enums";
import { StoryMetadata } from "../models";

export interface InquiryResponse {
  id: number;
  userId: string;
  content: string;
  language: "ja" | "en";
  timestamp: string; // ISO string format for API
  status: InquiryStatus;
  metadata: {
    source: string;
    processingTime?: number;
    aiModel?: string;
  };
}

export interface StoryResponse {
  id: number;
  inquiryId: number;
  title: string;
  description: string;
  category: StoryCategory;
  priority: Priority;
  estimatedEffort: number;
  deadline?: string; // ISO string format for API
  status: StoryStatus;
  assignee?: string;
  tags: string[];
  dependencies: number[];
  metadata: StoryMetadata;
  createdAt: string; // ISO string format for API
  updatedAt: string; // ISO string format for API
}

export interface StoryGenerationResponse {
  inquiryId: number;
  stories: StoryResponse[];
  status: "success" | "partial" | "failed";
  message?: string;
}

export interface GenerationStatusResponse {
  inquiryId: number;
  status: "processing" | "completed" | "failed";
  progress: number; // 0-100
  message?: string;
}
