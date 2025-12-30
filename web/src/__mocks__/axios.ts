/**
 * Axios manual mock for testing
 */

// Store the error interceptor handler
let errorInterceptor: ((error: any) => any) | null = null;

export const mockAxiosInstance = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: {
      use: jest.fn(),
      eject: jest.fn(),
      clear: jest.fn(),
    },
    response: {
      use: jest.fn((_successHandler, errorHandler) => {
        // Capture the error handler for use in tests
        errorInterceptor = errorHandler;
        return 0; // Return interceptor id
      }),
      eject: jest.fn(),
      clear: jest.fn(),
    },
  },
};

// Helper function to apply error interceptor (for testing)
export const applyErrorInterceptor = (error: any) => {
  if (errorInterceptor) {
    return errorInterceptor(error);
  }
  return Promise.reject(error);
};

const mock = {
  create: jest.fn(() => mockAxiosInstance),
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
};

export default mock;
