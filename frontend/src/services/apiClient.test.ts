import apiClient from "./apiClient";

// Mock axios to avoid actual HTTP requests in tests
jest.mock("axios", () => ({
  create: jest.fn(() => ({
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  })),
}));

describe("API Client", () => {
  it("should be defined", () => {
    expect(apiClient).toBeDefined();
  });

  it("should have interceptors configured", () => {
    expect(apiClient.interceptors).toBeDefined();
    expect(apiClient.interceptors.request).toBeDefined();
    expect(apiClient.interceptors.response).toBeDefined();
  });
});
