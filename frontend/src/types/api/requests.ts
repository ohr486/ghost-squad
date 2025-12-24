/**
 * API request types
 */
import { StoryCategory, Priority } from "../enums";

export interface InquiryCreateRequest {
  content: string;
  language?: "ja" | "en";
  userId: string;
}

export interface StoryUpdateRequest {
  title?: string;
  description?: string;
  category?: StoryCategory;
  priority?: Priority;
  estimatedEffort?: number;
  deadline?: string; // ISO string format
  assignee?: string;
  tags?: string[];
  dependencies?: number[];
}

export interface RejectRequest {
  reason?: string;
}
