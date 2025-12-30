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
} from './inquiryApi';

export { default as inquiryApi } from './inquiryApi';
