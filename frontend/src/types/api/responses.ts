/**
 * API response types
 */
import { InquiryStatus, StoryStatus, StoryCategory, Priority } from '../enums';
import { StoryMetadata } from '../models';

export interface InquiryResponse {
  id: string;
  userId: string;
  content: string;
  language: 'ja' | 'en';
  timestamp: string; // ISO string format for API
  status: InquiryStatus;
  metadata: {
    source: string;
    processingTime?: number;
    aiModel?: string;
  };
}

export interface StoryResponse {
  id: string;
  inquiryId: string;
  title: string;
  description: string;
  category: StoryCategory;
  priority: Priority;
  estimatedEffort: number;
  deadline?: string; // ISO string format for API
  status: StoryStatus;
  assignee?: string;
  tags: string[];
  dependencies: string[];
  metadata: StoryMetadata;
  createdAt: string; // ISO string format for API
  updatedAt: string; // ISO string format for API
}

export interface StoryGenerationResponse {
  inquiryId: string;
  stories: StoryResponse[];
  status: 'success' | 'partial' | 'failed';
  message?: string;
}

export interface GenerationStatusResponse {
  inquiryId: string;
  status: 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  message?: string;
}