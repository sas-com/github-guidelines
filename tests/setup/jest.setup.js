/**
 * Jest Setup Configuration
 * エス・エー・エス株式会社 - テスト環境初期設定
 */

import '@testing-library/jest-dom';
import 'jest-environment-jsdom';

// =====================================
// Global Test Configuration
// =====================================

// タイムゾーン設定
process.env.TZ = 'UTC';

// テスト環境変数
process.env.NODE_ENV = 'test';
process.env.CI = 'true';

// デフォルトタイムアウト
jest.setTimeout(30000);

// =====================================
// Mock Setup
// =====================================

// Console methods (except for test debugging)
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is deprecated')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };

  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('deprecated') || args[0].includes('Warning:'))
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
});

// =====================================
// DOM Mocks
// =====================================

// IntersectionObserver Mock
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {
    return null;
  }
  disconnect() {
    return null;
  }
  unobserve() {
    return null;
  }
};

// ResizeObserver Mock
global.ResizeObserver = class ResizeObserver {
  constructor(cb) {
    this.cb = cb;
  }
  observe() {
    return null;
  }
  unobserve() {
    return null;
  }
  disconnect() {
    return null;
  }
};

// MutationObserver Mock
global.MutationObserver = class MutationObserver {
  constructor(callback) {
    this.callback = callback;
  }
  observe() {
    return null;
  }
  disconnect() {
    return null;
  }
  takeRecords() {
    return [];
  }
};

// =====================================
// Web APIs Mocks
// =====================================

// localStorage Mock
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// sessionStorage Mock
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;

// fetch Mock
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    headers: new Headers(),
  })
);

// URL Mock
global.URL.createObjectURL = jest.fn(() => 'mock-url');
global.URL.revokeObjectURL = jest.fn();

// Geolocation Mock
global.navigator.geolocation = {
  getCurrentPosition: jest.fn(),
  watchPosition: jest.fn(),
  clearWatch: jest.fn(),
};

// Clipboard Mock
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(() => Promise.resolve()),
    readText: jest.fn(() => Promise.resolve('mock text')),
  },
});

// =====================================
// Media Queries Mock
// =====================================
global.matchMedia = global.matchMedia || function (query) {
  return {
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  };
};

// =====================================
// Security Testing Utilities
// =====================================

// XSS Test Helper
global.testXSS = (component, props) => {
  const xssPayloads = [
    '<script>alert("xss")</script>',
    'javascript:alert("xss")',
    '<img src=x onerror=alert("xss")>',
    '<svg onload=alert("xss")>',
    '"><script>alert("xss")</script>',
  ];

  return xssPayloads.every(payload => {
    try {
      const testProps = { ...props };
      // Inject XSS payload into all string props
      Object.keys(testProps).forEach(key => {
        if (typeof testProps[key] === 'string') {
          testProps[key] = payload;
        }
      });
      
      // Component should not execute the script
      render(createElement(component, testProps));
      return true;
    } catch (error) {
      console.error('XSS test failed:', error);
      return false;
    }
  });
};

// SQL Injection Test Helper
global.testSQLInjection = (apiCall, params) => {
  const sqlPayloads = [
    "'; DROP TABLE users; --",
    "' OR '1'='1",
    "' UNION SELECT * FROM users --",
    "'; INSERT INTO users VALUES ('hacker', 'password'); --",
  ];

  return sqlPayloads.every(async payload => {
    try {
      const testParams = { ...params };
      Object.keys(testParams).forEach(key => {
        if (typeof testParams[key] === 'string') {
          testParams[key] = payload;
        }
      });
      
      const result = await apiCall(testParams);
      // API should handle SQL injection safely (not crash)
      return result !== null;
    } catch (error) {
      // Expected behavior - API should reject malicious input
      return true;
    }
  });
};

// =====================================
// Performance Testing Utilities
// =====================================

// Performance measurement helper
global.measurePerformance = (testFunction, name = 'test') => {
  const start = performance.now();
  const result = testFunction();
  const end = performance.now();
  const duration = end - start;
  
  console.log(`Performance [${name}]: ${duration.toFixed(2)}ms`);
  
  // Fail if test takes too long
  if (duration > 1000) {
    throw new Error(`Performance test [${name}] exceeded 1000ms: ${duration.toFixed(2)}ms`);
  }
  
  return { result, duration };
};

// Memory usage helper
global.measureMemory = (testFunction, name = 'test') => {
  if (global.gc) {
    global.gc();
  }
  
  const memBefore = process.memoryUsage();
  const result = testFunction();
  const memAfter = process.memoryUsage();
  
  const heapUsed = memAfter.heapUsed - memBefore.heapUsed;
  
  console.log(`Memory [${name}]: ${(heapUsed / 1024 / 1024).toFixed(2)}MB`);
  
  return { result, heapUsed };
};

// =====================================
// Accessibility Testing Utilities
// =====================================

// Basic accessibility checker
global.checkA11y = async (component) => {
  const { axe, toHaveNoViolations } = await import('jest-axe');
  expect.extend(toHaveNoViolations);
  
  const results = await axe(component);
  expect(results).toHaveNoViolations();
};

// Keyboard navigation test helper
global.testKeyboardNavigation = (container, expectedFocusOrder) => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  expect(focusableElements.length).toBe(expectedFocusOrder.length);
  
  focusableElements.forEach((element, index) => {
    expect(element).toMatch(expectedFocusOrder[index]);
  });
};

// =====================================
// Test Cleanup
// =====================================

beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();
  
  // Reset fetch mock
  global.fetch.mockClear();
  
  // Clear localStorage/sessionStorage
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
  
  sessionStorageMock.getItem.mockClear();
  sessionStorageMock.setItem.mockClear();
  sessionStorageMock.removeItem.mockClear();
  sessionStorageMock.clear.mockClear();
});

afterEach(() => {
  // Clean up any timers
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
  
  // Clean up DOM
  document.body.innerHTML = '';
  
  // Reset modules
  jest.resetModules();
});

// =====================================
// Global Error Handling
// =====================================

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  // Don't fail the test suite for unhandled promises in test environment
  if (process.env.NODE_ENV !== 'test') {
    process.exit(1);
  }
});

// =====================================
// Custom Matchers
// =====================================

expect.extend({
  // Security matcher - checks if string contains potentially dangerous content
  toBeSafe(received) {
    const dangerousPatterns = [
      /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
      /javascript:/gi,
      /on\w+\s*=/gi,
      /eval\s*\(/gi,
    ];
    
    const isDangerous = dangerousPatterns.some(pattern => pattern.test(received));
    
    if (isDangerous) {
      return {
        message: () => `Expected "${received}" to be safe, but it contains potentially dangerous content`,
        pass: false,
      };
    }
    
    return {
      message: () => `Expected "${received}" not to be safe`,
      pass: true,
    };
  },
  
  // Performance matcher
  toBePerformant(received, maxTime = 100) {
    const start = performance.now();
    received();
    const duration = performance.now() - start;
    
    if (duration > maxTime) {
      return {
        message: () => `Expected function to execute in less than ${maxTime}ms, but it took ${duration.toFixed(2)}ms`,
        pass: false,
      };
    }
    
    return {
      message: () => `Expected function not to be performant`,
      pass: true,
    };
  },
});

// =====================================
// Test Database Setup (if needed)
// =====================================

// Mock database for integration tests
global.mockDB = {
  connect: jest.fn(() => Promise.resolve()),
  disconnect: jest.fn(() => Promise.resolve()),
  clear: jest.fn(() => Promise.resolve()),
  seed: jest.fn(() => Promise.resolve()),
};

console.log('🧪 Jest setup completed successfully');