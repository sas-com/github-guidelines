/**
 * Jest Global Setup
 * エス・エー・エス株式会社 - テスト環境グローバル初期化
 */

const { spawn } = require('child_process');
const path = require('path');

module.exports = async () => {
  console.log('🚀 Starting global test setup...');

  // =====================================
  // Environment Variables Setup
  // =====================================
  process.env.NODE_ENV = 'test';
  process.env.TZ = 'UTC';
  process.env.SUPPRESS_NO_CONFIG_WARNING = 'true';
  
  // Security test environment
  process.env.SECURITY_TEST_MODE = 'true';
  process.env.DISABLE_AUTH_FOR_TESTING = 'true';
  
  // Database test environment
  process.env.DATABASE_URL = process.env.TEST_DATABASE_URL || 'sqlite://test.db';
  process.env.REDIS_URL = process.env.TEST_REDIS_URL || 'redis://localhost:6379/1';

  // =====================================
  // Test Database Setup
  // =====================================
  console.log('📊 Setting up test database...');
  
  try {
    // Create test database if needed
    if (process.env.DATABASE_URL?.includes('postgres')) {
      await setupPostgresTestDB();
    } else if (process.env.DATABASE_URL?.includes('mysql')) {
      await setupMysqlTestDB();
    }
    console.log('✅ Test database ready');
  } catch (error) {
    console.warn('⚠️ Test database setup failed:', error.message);
  }

  // =====================================
  // Cache and Temporary Directories
  // =====================================
  console.log('📁 Setting up test directories...');
  
  const fs = require('fs');
  const testDirs = [
    'test-results',
    'coverage',
    'security-reports',
    'performance-reports',
    'temp'
  ];

  testDirs.forEach(dir => {
    const dirPath = path.join(process.cwd(), dir);
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  });

  // =====================================
  // Performance Monitoring Setup
  // =====================================
  console.log('⚡ Setting up performance monitoring...');
  
  global.testStartTime = Date.now();
  global.performanceMetrics = {
    totalTests: 0,
    passedTests: 0,
    failedTests: 0,
    totalTime: 0,
    averageTime: 0,
    slowTests: [],
  };

  // =====================================
  // Security Testing Setup
  // =====================================
  console.log('🔒 Initializing security testing framework...');
  
  global.securityTestConfig = {
    enableXSSTests: true,
    enableSQLInjectionTests: true,
    enableCSRFTests: true,
    enableAuthTests: true,
    strictMode: process.env.CI === 'true',
  };

  // =====================================
  // Test Data Generation
  // =====================================
  console.log('🎲 Generating test data...');
  
  await generateTestData();

  // =====================================
  // External Services Mocking
  // =====================================
  console.log('🎭 Setting up external service mocks...');
  
  setupExternalMocks();

  // =====================================
  // Resource Monitoring
  // =====================================
  if (process.env.MONITOR_RESOURCES === 'true') {
    console.log('📊 Starting resource monitoring...');
    startResourceMonitoring();
  }

  console.log('✅ Global test setup completed successfully');
};

// =====================================
// Helper Functions
// =====================================

async function setupPostgresTestDB() {
  const { Client } = require('pg');
  const url = new URL(process.env.DATABASE_URL);
  const dbName = url.pathname.substring(1);
  
  // Connect without database name to create it
  const adminClient = new Client({
    host: url.hostname,
    port: url.port,
    user: url.username,
    password: url.password,
    database: 'postgres',
  });
  
  try {
    await adminClient.connect();
    
    // Drop existing test database
    try {
      await adminClient.query(`DROP DATABASE IF EXISTS "${dbName}"`);
    } catch (error) {
      // Database might not exist
    }
    
    // Create fresh test database
    await adminClient.query(`CREATE DATABASE "${dbName}"`);
    
    await adminClient.end();
  } catch (error) {
    console.warn('PostgreSQL setup warning:', error.message);
    await adminClient.end();
  }
}

async function setupMysqlTestDB() {
  const mysql = require('mysql2/promise');
  const url = new URL(process.env.DATABASE_URL.replace('mysql:', 'mysql2:'));
  const dbName = url.pathname.substring(1);
  
  const connection = await mysql.createConnection({
    host: url.hostname,
    port: url.port,
    user: url.username,
    password: url.password,
  });
  
  try {
    await connection.execute(`DROP DATABASE IF EXISTS \`${dbName}\``);
    await connection.execute(`CREATE DATABASE \`${dbName}\``);
  } catch (error) {
    console.warn('MySQL setup warning:', error.message);
  } finally {
    await connection.end();
  }
}

async function generateTestData() {
  const fs = require('fs').promises;
  const path = require('path');
  
  const testData = {
    users: [
      {
        id: 1,
        name: 'Test User',
        email: 'test@example.com',
        role: 'user',
        createdAt: '2023-01-01T00:00:00Z',
      },
      {
        id: 2,
        name: 'Admin User',
        email: 'admin@example.com',
        role: 'admin',
        createdAt: '2023-01-01T00:00:00Z',
      },
    ],
    products: [
      {
        id: 1,
        name: 'Test Product',
        price: 100,
        category: 'test',
      },
    ],
    // Security test data
    securityTestCases: {
      xssPayloads: [
        '<script>alert("xss")</script>',
        'javascript:alert("xss")',
        '<img src=x onerror=alert("xss")>',
        '"><script>alert("xss")</script>',
      ],
      sqlInjectionPayloads: [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "admin'/*",
      ],
      csrfTokens: [
        'invalid-token',
        '',
        'expired-token-12345',
      ],
    },
  };
  
  const fixturesDir = path.join(process.cwd(), 'tests', 'fixtures');
  await fs.mkdir(fixturesDir, { recursive: true });
  await fs.writeFile(
    path.join(fixturesDir, 'testData.json'),
    JSON.stringify(testData, null, 2)
  );
}

function setupExternalMocks() {
  // Mock external APIs
  global.mockExternalAPIs = {
    githubAPI: {
      getUser: jest.fn().mockResolvedValue({ login: 'testuser' }),
      getRepo: jest.fn().mockResolvedValue({ name: 'test-repo' }),
    },
    stripeAPI: {
      createPayment: jest.fn().mockResolvedValue({ id: 'payment_123' }),
    },
    sendgridAPI: {
      sendEmail: jest.fn().mockResolvedValue({ messageId: 'email_123' }),
    },
  };
  
  // Mock file system operations
  global.mockFS = {
    readFile: jest.fn(),
    writeFile: jest.fn(),
    exists: jest.fn(),
  };
}

function startResourceMonitoring() {
  const resourceMonitor = {
    memoryUsage: [],
    cpuUsage: [],
    intervalId: null,
  };
  
  resourceMonitor.intervalId = setInterval(() => {
    const memUsage = process.memoryUsage();
    const cpuUsage = process.cpuUsage();
    
    resourceMonitor.memoryUsage.push({
      timestamp: Date.now(),
      heapUsed: memUsage.heapUsed,
      heapTotal: memUsage.heapTotal,
    });
    
    resourceMonitor.cpuUsage.push({
      timestamp: Date.now(),
      user: cpuUsage.user,
      system: cpuUsage.system,
    });
    
    // Keep only last 100 measurements
    if (resourceMonitor.memoryUsage.length > 100) {
      resourceMonitor.memoryUsage = resourceMonitor.memoryUsage.slice(-100);
    }
    if (resourceMonitor.cpuUsage.length > 100) {
      resourceMonitor.cpuUsage = resourceMonitor.cpuUsage.slice(-100);
    }
  }, 1000);
  
  global.resourceMonitor = resourceMonitor;
  
  // Cleanup function
  global.cleanupResourceMonitor = () => {
    if (resourceMonitor.intervalId) {
      clearInterval(resourceMonitor.intervalId);
    }
  };
}