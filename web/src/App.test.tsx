import { render, screen, waitFor } from "@testing-library/react";
import App from "./App";
import * as inquiryApi from "./services/inquiryApi";

// Mock the inquiry API
jest.mock("./services/inquiryApi");

const mockInquiryApi = inquiryApi as jest.Mocked<typeof inquiryApi>;

beforeEach(() => {
  jest.clearAllMocks();
  // Mock listInquiries to return empty data by default
  mockInquiryApi.listInquiries.mockResolvedValue({
    data: [],
    meta: {
      page: 1,
      limit: 20,
      total: 0,
      has_next: false,
    },
    timestamp: new Date().toISOString(),
  });
});

test("renders Ghost Squad heading", async () => {
  render(<App />);
  const headingElement = screen.getByText(/Ghost Squad/i);
  expect(headingElement).toBeInTheDocument();

  // Wait for the component to finish loading
  await waitFor(() => {
    expect(mockInquiryApi.listInquiries).toHaveBeenCalled();
  });
});

test("renders platform description", async () => {
  render(<App />);
  const descriptionElement = screen.getByText(
    /AI-Driven Task Management Platform/i,
  );
  expect(descriptionElement).toBeInTheDocument();

  // Wait for the component to finish loading
  await waitFor(() => {
    expect(mockInquiryApi.listInquiries).toHaveBeenCalled();
  });
});
