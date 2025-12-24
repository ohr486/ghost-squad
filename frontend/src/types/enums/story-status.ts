/**
 * Story status enumeration (renamed from TaskStatus to avoid confusion with Kanban tasks)
 */
export enum StoryStatus {
  PENDING_REVIEW = 'pending_review',
  APPROVED = 'approved',
  EXPORTED = 'exported',
  REJECTED = 'rejected'
}