/**
 * Test Helper Utilities
 * エス・エー・エス株式会社 - 包括的テストユーティリティ
 */

const { render, screen, fireEvent, waitFor } = require('@testing-library/react');
const { act } = require('react-dom/test-utils');

// =====================================
// React Testing Utilities
// =====================================

/**
 * Enhanced render function with common providers
 */
export const renderWithProviders = (ui, options = {}) => {
  const {
    theme = 'light',
    initialState = {},
    route = '/',
    user = null,
    ...renderOptions
  } = options;

  // Mock providers wrapper
  const AllTheProviders = ({ children }) => {
    return (
      <ThemeProvider theme={theme}>
        <RouterProvider initialRoute={route}>
          <UserProvider user={user}>
            <QueryProvider>
              {children}
            </QueryProvider>
          </UserProvider>
        </RouterProvider>
      </ThemeProvider>
    );
  };

  return render(ui, { wrapper: AllTheProviders, ...renderOptions });
};

/**
 * Wait for component to be fully loaded
 */
export const waitForComponentToLoad = async (testId, timeout = 5000) => {
  return waitFor(() => expect(screen.getByTestId(testId)).toBeInTheDocument(), {
    timeout,
  });
};

/**
 * Simulate user interaction with delay
 */
export const userEvent = {
  async click(element, delay = 0) {
    if (delay > 0) {
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, delay));
      });
    }
    fireEvent.click(element);
  },

  async type(element, text, delay = 0) {
    if (delay > 0) {
      for (let i = 0; i < text.length; i++) {
        fireEvent.change(element, { target: { value: text.slice(0, i + 1) } });
        await act(async () => {
          await new Promise(resolve => setTimeout(resolve, delay));
        });
      }
    } else {
      fireEvent.change(element, { target: { value: text } });
    }
  },

  async selectOption(element, option) {
    fireEvent.change(element, { target: { value: option } });
  },
};

// =====================================
// API Testing Utilities
// =====================================

/**
 * Mock API response helper
 */
export const mockAPIResponse = (data, status = 200, delay = 0) => {
  return jest.fn(() =>
    new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: status >= 200 && status < 300,
          status,
          json: () => Promise.resolve(data),
          text: () => Promise.resolve(JSON.stringify(data)),
          headers: new Headers({ 'Content-Type': 'application/json' }),
        });
      }, delay);
    })
  );
};

/**
 * Mock API error helper
 */
export const mockAPIError = (message = 'API Error', status = 500, delay = 0) => {
  return jest.fn(() =>
    new Promise((resolve, reject) => {
      setTimeout(() => {
        reject(new Error(message));
      }, delay);
    })
  );
};

/**
 * Test API endpoint with different scenarios
 */
export const testAPIEndpoint = async (apiCall, testCases) => {
  const results = [];

  for (const testCase of testCases) {
    const { name, input, expectedStatus, expectedData, shouldFail = false } = testCase;

    try {
      const result = await apiCall(input);

      if (shouldFail) {
        results.push({
          name,
          passed: false,
          error: 'Expected API call to fail but it succeeded',
        });
      } else {
        const passed = 
          (!expectedStatus || result.status === expectedStatus) &&
          (!expectedData || JSON.stringify(result.data) === JSON.stringify(expectedData));

        results.push({ name, passed, result });
      }
    } catch (error) {
      if (shouldFail) {
        results.push({ name, passed: true, error: error.message });
      } else {
        results.push({ name, passed: false, error: error.message });
      }
    }
  }

  return results;
};

// =====================================
// Security Testing Utilities
// =====================================

/**
 * XSS Payload Generator
 */
export const generateXSSPayloads = () => [
  '<script>alert("xss")</script>',
  '<img src=x onerror=alert("xss")>',
  '<svg onload=alert("xss")>',
  'javascript:alert("xss")',
  '"><script>alert("xss")</script>',
  '<iframe src="javascript:alert(`xss`)">',
  '<object data="javascript:alert(`xss`)">',
  '<embed src="javascript:alert(`xss`)">',
  '<link rel="stylesheet" href="javascript:alert(`xss`)">',
  '<style>@import "javascript:alert(`xss`)";</style>',
];

/**
 * SQL Injection Payload Generator
 */
export const generateSQLInjectionPayloads = () => [
  "'; DROP TABLE users; --",
  "' OR '1'='1",
  "' OR '1'='1' --",
  "' OR '1'='1' /*",
  "' UNION SELECT * FROM users --",
  "'; INSERT INTO users VALUES ('hacker', 'password'); --",
  "admin'/*",
  "' AND (SELECT COUNT(*) FROM users) > 0 --",
];

/**
 * CSRF Token Testing
 */
export const testCSRFProtection = async (apiCall, validToken, invalidTokens = []) => {
  const results = [];

  // Test with valid token
  try {
    await apiCall({ csrfToken: validToken });
    results.push({ type: 'valid', passed: true });
  } catch (error) {
    results.push({ type: 'valid', passed: false, error: error.message });
  }

  // Test with invalid tokens
  for (const invalidToken of invalidTokens) {
    try {
      await apiCall({ csrfToken: invalidToken });
      results.push({ type: 'invalid', token: invalidToken, passed: false, error: 'Should have been rejected' });
    } catch (error) {
      results.push({ type: 'invalid', token: invalidToken, passed: true });
    }
  }

  return results;
};

/**
 * Authentication Testing
 */
export const testAuthentication = async (apiCall, validCredentials, invalidCredentials = []) => {
  const results = [];

  // Test with valid credentials
  try {
    const result = await apiCall(validCredentials);
    results.push({
      type: 'valid_credentials',
      passed: !!result.token || !!result.success,
      result,
    });
  } catch (error) {
    results.push({
      type: 'valid_credentials',
      passed: false,
      error: error.message,
    });
  }

  // Test with invalid credentials
  for (const credentials of invalidCredentials) {
    try {
      const result = await apiCall(credentials);
      results.push({
        type: 'invalid_credentials',
        credentials,
        passed: !result.token && !result.success,
        result,
      });
    } catch (error) {
      results.push({
        type: 'invalid_credentials',
        credentials,
        passed: true, // Expected to fail
      });
    }
  }

  return results;
};

// =====================================
// Performance Testing Utilities
// =====================================

/**
 * Measure function execution time
 */
export const measureExecutionTime = async (func, iterations = 1) => {
  const times = [];

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await func();
    const end = performance.now();
    times.push(end - start);
  }

  return {
    times,
    average: times.reduce((sum, time) => sum + time, 0) / times.length,
    min: Math.min(...times),
    max: Math.max(...times),
    median: times.sort((a, b) => a - b)[Math.floor(times.length / 2)],
  };
};

/**
 * Memory usage measurement
 */
export const measureMemoryUsage = async (func) => {
  if (global.gc) {
    global.gc();
  }

  const memBefore = process.memoryUsage();
  const result = await func();
  const memAfter = process.memoryUsage();

  return {
    result,
    heapUsed: memAfter.heapUsed - memBefore.heapUsed,
    heapTotal: memAfter.heapTotal - memBefore.heapTotal,
    external: memAfter.external - memBefore.external,
    rss: memAfter.rss - memBefore.rss,
  };
};

/**
 * Load testing helper
 */
export const loadTest = async (func, options = {}) => {
  const {
    concurrent = 10,
    duration = 5000,
    warmup = 1000,
  } = options;

  // Warmup
  console.log('🔥 Warming up...');
  const warmupEnd = Date.now() + warmup;
  while (Date.now() < warmupEnd) {
    await func();
  }

  // Load test
  console.log(`⚡ Starting load test (${concurrent} concurrent, ${duration}ms duration)...`);
  
  const results = [];
  const startTime = Date.now();
  const endTime = startTime + duration;

  const workers = Array(concurrent).fill(null).map(async () => {
    const workerResults = [];
    
    while (Date.now() < endTime) {
      const start = performance.now();
      try {
        await func();
        workerResults.push({
          success: true,
          duration: performance.now() - start,
        });
      } catch (error) {
        workerResults.push({
          success: false,
          duration: performance.now() - start,
          error: error.message,
        });
      }
    }
    
    return workerResults;
  });

  const allResults = (await Promise.all(workers)).flat();

  const successful = allResults.filter(r => r.success);
  const failed = allResults.filter(r => !r.success);

  return {
    total: allResults.length,
    successful: successful.length,
    failed: failed.length,
    successRate: successful.length / allResults.length,
    averageResponseTime: successful.reduce((sum, r) => sum + r.duration, 0) / successful.length,
    rps: allResults.length / (duration / 1000),
    errors: failed.map(f => f.error),
  };
};

// =====================================
// Accessibility Testing Utilities
// =====================================

/**
 * Test keyboard navigation
 */
export const testKeyboardNavigation = (container, expectedOrder = []) => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  let currentIndex = 0;

  focusableElements.forEach((element, index) => {
    element.focus();
    
    if (expectedOrder.length > 0) {
      expect(element).toMatch(expectedOrder[index]);
    }
    
    expect(element).toHaveFocus();
    
    // Simulate Tab key
    fireEvent.keyDown(element, { key: 'Tab', code: 'Tab' });
    currentIndex = (currentIndex + 1) % focusableElements.length;
  });

  return {
    totalFocusableElements: focusableElements.length,
    keyboardAccessible: true,
  };
};

/**
 * Test screen reader compatibility
 */
export const testScreenReaderCompatibility = (container) => {
  const issues = [];

  // Check for images without alt text
  const images = container.querySelectorAll('img:not([alt])');
  if (images.length > 0) {
    issues.push(`${images.length} images missing alt text`);
  }

  // Check for form inputs without labels
  const inputs = container.querySelectorAll('input:not([aria-label]):not([aria-labelledby])');
  inputs.forEach(input => {
    const label = container.querySelector(`label[for="${input.id}"]`);
    if (!label && !input.getAttribute('aria-label')) {
      issues.push(`Input ${input.type} missing label`);
    }
  });

  // Check for headings hierarchy
  const headings = Array.from(container.querySelectorAll('h1, h2, h3, h4, h5, h6'));
  let previousLevel = 0;
  
  headings.forEach(heading => {
    const currentLevel = parseInt(heading.tagName[1]);
    if (currentLevel > previousLevel + 1) {
      issues.push(`Heading hierarchy skip from h${previousLevel} to h${currentLevel}`);
    }
    previousLevel = currentLevel;
  });

  return {
    issues,
    accessible: issues.length === 0,
  };
};

// =====================================
// Data Generation Utilities
// =====================================

/**
 * Generate test user data
 */
export const generateTestUser = (overrides = {}) => ({
  id: Math.floor(Math.random() * 10000),
  name: 'Test User',
  email: `test${Math.floor(Math.random() * 1000)}@example.com`,
  role: 'user',
  createdAt: new Date().toISOString(),
  ...overrides,
});

/**
 * Generate test API data
 */
export const generateTestAPIData = (count = 10, generator = generateTestUser) => {
  return Array(count).fill(null).map(() => generator());
};

/**
 * Generate random string
 */
export const generateRandomString = (length = 10, charset = 'abcdefghijklmnopqrstuvwxyz0123456789') => {
  let result = '';
  for (let i = 0; i < length; i++) {
    result += charset.charAt(Math.floor(Math.random() * charset.length));
  }
  return result;
};

// =====================================
// Test Environment Utilities
// =====================================

/**
 * Create isolated test environment
 */
export const createTestEnvironment = (config = {}) => {
  const env = {
    cleanup: [],
    
    addCleanup(func) {
      this.cleanup.push(func);
    },
    
    async teardown() {
      for (const func of this.cleanup.reverse()) {
        await func();
      }
      this.cleanup = [];
    },
    
    mockTimers() {
      jest.useFakeTimers();
      this.addCleanup(() => jest.useRealTimers());
    },
    
    mockDate(date = new Date('2023-01-01')) {
      const spy = jest.spyOn(global.Date, 'now').mockReturnValue(date.getTime());
      this.addCleanup(() => spy.mockRestore());
      return date;
    },
    
    mockConsole() {
      const originalConsole = { ...console };
      ['log', 'warn', 'error', 'info'].forEach(method => {
        console[method] = jest.fn();
      });
      
      this.addCleanup(() => {
        Object.assign(console, originalConsole);
      });
      
      return console;
    },
  };

  return env;
};

// =====================================
// Async Testing Utilities
// =====================================

/**
 * Wait for condition with timeout
 */
export const waitForCondition = (condition, timeout = 5000, interval = 100) => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const check = () => {
      if (condition()) {
        resolve(true);
      } else if (Date.now() - startTime > timeout) {
        reject(new Error(`Condition not met within ${timeout}ms`));
      } else {
        setTimeout(check, interval);
      }
    };
    
    check();
  });
};

/**
 * Retry function until success
 */
export const retryUntilSuccess = async (func, maxAttempts = 3, delay = 1000) => {
  let lastError;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await func();
    } catch (error) {
      lastError = error;
      
      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
};

export default {
  renderWithProviders,
  waitForComponentToLoad,
  userEvent,
  mockAPIResponse,
  mockAPIError,
  testAPIEndpoint,
  generateXSSPayloads,
  generateSQLInjectionPayloads,
  testCSRFProtection,
  testAuthentication,
  measureExecutionTime,
  measureMemoryUsage,
  loadTest,
  testKeyboardNavigation,
  testScreenReaderCompatibility,
  generateTestUser,
  generateTestAPIData,
  generateRandomString,
  createTestEnvironment,
  waitForCondition,
  retryUntilSuccess,
};