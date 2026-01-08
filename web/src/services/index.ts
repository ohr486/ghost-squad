/**
 * Ghost Squad - サービスエクスポート
 */

export {
  createInquiry,
  listInquiries,
  getInquiry,
  updateInquiry,
  approveInquiry,
  rejectInquiry,
  healthCheck,
} from "./inquiryApi";

export { default as inquiryApi } from "./inquiryApi";

export {
  createStory,
  generateStory,
  listStories,
  listStoriesByInquiry,
  getStory,
  updateStory,
  deleteStory,
  approveStory,
  rejectStory,
  batchApproveStories,
} from "./storyApi";

export { default as storyApi } from "./storyApi";
