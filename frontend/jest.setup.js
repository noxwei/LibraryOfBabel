import "@testing-library/jest-dom";

// Mock fetch for tests
global.fetch = jest.fn();

// Mock console methods to reduce noise in tests
console.warn = jest.fn();
console.error = jest.fn();
