/**
 * Export and Kanban integration types
 */

export interface AuthConfig {
  type: "api_key" | "oauth" | "basic";
  credentials: Record<string, string>;
}

export interface FieldMapping {
  title: string;
  description: string;
  category?: string;
  priority?: string;
  deadline?: string;
  assignee?: string;
}

export interface KanbanSystem {
  name: string;
  apiEndpoint: string;
  authConfig: AuthConfig;
  fieldMapping: FieldMapping;
}

export interface ExportResult {
  success: boolean;
  exportedStories: number[]; // Story IDs
  errors?: string[];
  externalIds?: Record<number, string>; // storyId -> externalTaskId mapping
}

export interface SyncStatus {
  storyId: number;
  externalTaskId?: string; // Kanban task ID
  status: "pending" | "synced" | "failed";
  lastSyncAt?: Date;
  error?: string;
}

export interface NotificationSettings {
  email: boolean;
  inApp: boolean;
  webhook?: string;
  deadlineReminder: number; // days before deadline
}
