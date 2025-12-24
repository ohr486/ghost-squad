/**
 * Inquiry model types
 */
import { InquiryStatus } from "../enums";

export interface Inquiry {
  id: number;
  userId: string;
  content: string;
  language: "ja" | "en";
  timestamp: Date;
  status: InquiryStatus;
  metadata: {
    source: string;
    processingTime?: number;
    aiModel?: string;
  };
}

export interface InquiryResult {
  inquiryId: number;
  status: "processing" | "needs_clarification" | "task_working" | "completed";
  generatedStories?: import("./story").Story[];
  clarificationQuestions?: string[];
}
