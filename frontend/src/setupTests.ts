// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import "@testing-library/jest-dom";

// Configure React Testing Library
import { configure } from "@testing-library/react";

/**
 * Suppress specific console warnings that are known to be safe to ignore during testing.
 *
 * IMPORTANT: This configuration only suppresses specific, well-known warnings that are:
 * 1. Related to testing environment differences (ReactDOMTestUtils deprecation)
 * 2. React Router future flags that don't affect current functionality
 * 3. React act() warnings that are handled by Testing Library
 *
 * Any other warnings will still be displayed to help catch real issues.
 */
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  console.error = (...args: any[]) => {
    if (typeof args[0] === "string") {
      // Suppress specific React testing warnings
      if (
        args[0].includes("`ReactDOMTestUtils.act` is deprecated") ||
        args[0].includes("Warning: An update to") ||
        args[0].startsWith(
          "Warning: You called act(async () => ...) without await",
        )
      ) {
        return;
      }
    }
    originalError.call(console, ...args);
  };

  console.warn = (...args: any[]) => {
    if (typeof args[0] === "string") {
      // Suppress specific React Router future flag warnings
      if (
        args[0].includes("React Router Future Flag Warning") ||
        args[0].includes("v7_startTransition") ||
        args[0].includes("v7_relativeSplatPath")
      ) {
        return;
      }
    }
    originalWarn.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
});

configure({
  testIdAttribute: "data-testid",
});

// Mock IntersectionObserver for tests
global.IntersectionObserver = class IntersectionObserver {
  root = null;
  rootMargin = "";
  thresholds = [];

  disconnect() {}
  observe() {}
  unobserve() {}
  takeRecords() {
    return [];
  }
} as any;

// Mock ResizeObserver for tests
global.ResizeObserver = class ResizeObserver {
  disconnect() {}
  observe() {}
  unobserve() {}
} as any;

// Mock matchMedia for tests
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});
