/**
 * Story model types (renamed from Task to avoid confusion with Kanban tasks)
 */
import { StoryStatus, StoryCategory, Priority } from '../enums';

export interface StoryMetadata {
  originalInquiry: string;
  generationLog: string[];
  appliedTemplate?: string;
  confidence: number; // 0-1
  reviewNotes?: string[];
}

export interface Story {
  id: string;
  inquiryId: string;
  title: string;
  description: string;
  category: StoryCategory;
  priority: Priority;
  estimatedEffort: number; // 時間単位
  deadline?: Date;
  status: StoryStatus;
  assignee?: string;
  tags: string[];
  dependencies: string[]; // 他のストーリーID
  metadata: StoryMetadata;
  createdAt: Date;
  updatedAt: Date;
}