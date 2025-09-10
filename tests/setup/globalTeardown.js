/**
 * Jest Global Teardown
 * エス・エー・エス株式会社 - テスト環境グローバル終了処理
 */

const fs = require('fs').promises;
const path = require('path');

module.exports = async () => {
  console.log('🧹 Starting global test teardown...');

  // =====================================
  // Performance Report Generation
  // =====================================
  console.log('📊 Generating performance report...');
  
  try {
    const endTime = Date.now();
    const totalTestTime = endTime - global.testStartTime;
    
    const performanceReport = {
      summary: {
        totalDuration: totalTestTime,
        totalTests: global.performanceMetrics?.totalTests || 0,
        passedTests: global.performanceMetrics?.passedTests || 0,
        failedTests: global.performanceMetrics?.failedTests || 0,
        averageTestTime: global.performanceMetrics?.averageTime || 0,
      },
      slowTests: global.performanceMetrics?.slowTests || [],
      timestamp: new Date().toISOString(),
    };
    
    await fs.writeFile(
      path.join(process.cwd(), 'test-results', 'performance-report.json'),
      JSON.stringify(performanceReport, null, 2)
    );
    
    console.log(`✅ Performance report saved (Total time: ${totalTestTime}ms)`);
  } catch (error) {
    console.warn('⚠️ Performance report generation failed:', error.message);
  }

  // =====================================
  // Resource Monitoring Cleanup
  // =====================================
  if (global.resourceMonitor) {
    console.log('📊 Finalizing resource monitoring...');
    
    try {
      // Stop monitoring
      if (global.cleanupResourceMonitor) {
        global.cleanupResourceMonitor();
      }
      
      // Generate resource usage report
      const resourceReport = {
        memory: {
          peak: Math.max(...global.resourceMonitor.memoryUsage.map(m => m.heapUsed)),
          average: global.resourceMonitor.memoryUsage.reduce((sum, m) => sum + m.heapUsed, 0) / global.resourceMonitor.memoryUsage.length,
          measurements: global.resourceMonitor.memoryUsage.length,
        },
        cpu: {
          totalUser: global.resourceMonitor.cpuUsage.reduce((sum, c) => sum + c.user, 0),
          totalSystem: global.resourceMonitor.cpuUsage.reduce((sum, c) => sum + c.system, 0),
          measurements: global.resourceMonitor.cpuUsage.length,
        },
        timestamp: new Date().toISOString(),
      };
      
      await fs.writeFile(
        path.join(process.cwd(), 'test-results', 'resource-usage.json'),
        JSON.stringify(resourceReport, null, 2)
      );
      
      console.log('✅ Resource usage report saved');
    } catch (error) {
      console.warn('⚠️ Resource monitoring cleanup failed:', error.message);
    }
  }

  // =====================================
  // Database Cleanup
  // =====================================
  console.log('🗄️ Cleaning up test database...');
  
  try {
    if (process.env.DATABASE_URL?.includes('postgres')) {
      await cleanupPostgresTestDB();
    } else if (process.env.DATABASE_URL?.includes('mysql')) {
      await cleanupMysqlTestDB();
    } else if (process.env.DATABASE_URL?.includes('sqlite')) {
      await cleanupSqliteTestDB();
    }
    console.log('✅ Test database cleaned up');
  } catch (error) {
    console.warn('⚠️ Database cleanup failed:', error.message);
  }

  // =====================================
  // Temporary Files Cleanup
  // =====================================
  console.log('🗂️ Cleaning up temporary files...');
  
  try {
    const tempDirs = ['temp', '.tmp'];
    
    for (const dir of tempDirs) {
      const dirPath = path.join(process.cwd(), dir);
      try {
        await fs.rmdir(dirPath, { recursive: true });
      } catch (error) {
        // Directory might not exist
      }
    }
    
    console.log('✅ Temporary files cleaned up');
  } catch (error) {
    console.warn('⚠️ Temporary files cleanup failed:', error.message);
  }

  // =====================================
  // Test Results Summary
  // =====================================
  console.log('📋 Generating test results summary...');
  
  try {
    const testSummary = {
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        ci: process.env.CI === 'true',
        testMode: process.env.NODE_ENV,
      },
      security: {
        securityTestsEnabled: global.securityTestConfig?.enableXSSTests || false,
        strictMode: global.securityTestConfig?.strictMode || false,
      },
      performance: global.performanceMetrics || {},
      resources: global.resourceMonitor ? {
        memoryPeak: Math.max(...global.resourceMonitor.memoryUsage.map(m => m.heapUsed)),
        monitoringEnabled: true,
      } : { monitoringEnabled: false },
      timestamp: new Date().toISOString(),
      completedAt: new Date().toISOString(),
    };
    
    await fs.writeFile(
      path.join(process.cwd(), 'test-results', 'test-summary.json'),
      JSON.stringify(testSummary, null, 2)
    );
    
    console.log('✅ Test results summary saved');
  } catch (error) {
    console.warn('⚠️ Test summary generation failed:', error.message);
  }

  // =====================================
  // Coverage Report Enhancement
  // =====================================
  console.log('📈 Enhancing coverage reports...');
  
  try {
    await enhanceCoverageReport();
    console.log('✅ Coverage report enhanced');
  } catch (error) {
    console.warn('⚠️ Coverage report enhancement failed:', error.message);
  }

  // =====================================
  // Security Test Results
  // =====================================
  if (global.securityTestResults) {
    console.log('🔒 Generating security test report...');
    
    try {
      await fs.writeFile(
        path.join(process.cwd(), 'test-results', 'security-test-results.json'),
        JSON.stringify(global.securityTestResults, null, 2)
      );
      
      console.log('✅ Security test results saved');
    } catch (error) {
      console.warn('⚠️ Security test results saving failed:', error.message);
    }
  }

  // =====================================
  // Final Cleanup and Exit
  // =====================================
  console.log('🏁 Finalizing teardown...');
  
  // Clear global variables
  delete global.testStartTime;
  delete global.performanceMetrics;
  delete global.resourceMonitor;
  delete global.securityTestConfig;
  delete global.securityTestResults;

  console.log('✅ Global test teardown completed successfully');
};

// =====================================
// Helper Functions
// =====================================

async function cleanupPostgresTestDB() {
  const { Client } = require('pg');
  const url = new URL(process.env.DATABASE_URL);
  const dbName = url.pathname.substring(1);
  
  const adminClient = new Client({
    host: url.hostname,
    port: url.port,
    user: url.username,
    password: url.password,
    database: 'postgres',
  });
  
  try {
    await adminClient.connect();
    
    // Terminate active connections to test database
    await adminClient.query(`
      SELECT pg_terminate_backend(pid) 
      FROM pg_stat_activity 
      WHERE datname = '${dbName}' AND pid != pg_backend_pid()
    `);
    
    // Drop test database
    await adminClient.query(`DROP DATABASE IF EXISTS "${dbName}"`);
  } catch (error) {
    console.warn('PostgreSQL cleanup warning:', error.message);
  } finally {
    await adminClient.end();
  }
}

async function cleanupMysqlTestDB() {
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
  } catch (error) {
    console.warn('MySQL cleanup warning:', error.message);
  } finally {
    await connection.end();
  }
}

async function cleanupSqliteTestDB() {
  const sqliteFiles = ['test.db', 'test.db-journal', 'test.db-wal', 'test.db-shm'];
  
  for (const file of sqliteFiles) {
    try {
      await fs.unlink(path.join(process.cwd(), file));
    } catch (error) {
      // File might not exist
    }
  }
}

async function enhanceCoverageReport() {
  const coveragePath = path.join(process.cwd(), 'coverage');
  
  try {
    // Check if coverage directory exists
    await fs.access(coveragePath);
    
    // Read coverage summary
    const coverageSummaryPath = path.join(coveragePath, 'coverage-summary.json');
    try {
      const coverageSummary = JSON.parse(await fs.readFile(coverageSummaryPath, 'utf8'));
      
      // Calculate additional metrics
      const enhancedSummary = {
        ...coverageSummary,
        metadata: {
          generatedAt: new Date().toISOString(),
          testEnvironment: process.env.NODE_ENV,
          ciMode: process.env.CI === 'true',
        },
        quality: {
          highCoverage: coverageSummary.total?.lines?.pct >= 90,
          acceptableCoverage: coverageSummary.total?.lines?.pct >= 80,
          needsImprovement: coverageSummary.total?.lines?.pct < 80,
        },
      };
      
      await fs.writeFile(
        path.join(coveragePath, 'enhanced-summary.json'),
        JSON.stringify(enhancedSummary, null, 2)
      );
    } catch (error) {
      // Coverage summary might not exist
    }
  } catch (error) {
    // Coverage directory doesn't exist
  }
}