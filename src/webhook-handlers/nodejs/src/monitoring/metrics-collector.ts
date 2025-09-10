/**
 * Metrics Collector
 * エス・エー・エス株式会社 GitHub Webhook メトリクス収集
 */

import client from 'prom-client';
import {
  WebhookEventType,
  WebhookMetrics,
  SecurityCheckResult
} from '@/types/webhook.types.js';

export interface MetricsConfig {
  enabled: boolean;
  collectDefaultMetrics: boolean;
  defaultMetricsInterval: number;
  prefix: string;
  labels: Record<string, string>;
}

export class MetricsCollector {
  private config: MetricsConfig;
  
  // Counter metrics
  private webhookRequestsTotal: client.Counter<string>;
  private webhookErrorsTotal: client.Counter<string>;
  private webhookSecurityEventsTotal: client.Counter<string>;
  private rateLimitExceededTotal: client.Counter<string>;
  
  // Histogram metrics
  private webhookProcessingDuration: client.Histogram<string>;
  private webhookPayloadSize: client.Histogram<string>;
  
  // Gauge metrics
  private activeConnections: client.Gauge<string>;
  private memoryUsage: client.Gauge<string>;
  private cpuUsage: client.Gauge<string>;
  private webhookQueueSize: client.Gauge<string>;
  
  // Summary metrics
  private webhookResponseTime: client.Summary<string>;
  
  // Custom metrics
  private securityCheckResults: client.Counter<string>;
  private ipBlockedTotal: client.Counter<string>;
  private sensitiveDataDetected: client.Counter<string>;

  constructor(config: MetricsConfig) {
    this.config = config;
    
    if (!this.config.enabled) {
      console.warn('Metrics collection is disabled');
      return;
    }

    this.initializeMetrics();
    this.setupDefaultMetrics();
    this.startSystemMetricsCollection();
  }

  private initializeMetrics(): void {
    const prefix = this.config.prefix;
    const defaultLabels = this.config.labels;

    // Counter Metrics
    this.webhookRequestsTotal = new client.Counter({
      name: `${prefix}_webhook_requests_total`,
      help: 'Total number of webhook requests received',
      labelNames: ['event_type', 'status', 'repository', 'sender'],
      registers: [client.register],
    });

    this.webhookErrorsTotal = new client.Counter({
      name: `${prefix}_webhook_errors_total`,
      help: 'Total number of webhook processing errors',
      labelNames: ['error_type', 'event_type', 'repository'],
      registers: [client.register],
    });

    this.webhookSecurityEventsTotal = new client.Counter({
      name: `${prefix}_webhook_security_events_total`,
      help: 'Total number of security events detected',
      labelNames: ['event_type', 'severity', 'source_ip', 'action_taken'],
      registers: [client.register],
    });

    this.rateLimitExceededTotal = new client.Counter({
      name: `${prefix}_webhook_rate_limit_exceeded_total`,
      help: 'Total number of rate limit violations',
      labelNames: ['limit_type', 'source_ip', 'user_agent'],
      registers: [client.register],
    });

    this.securityCheckResults = new client.Counter({
      name: `${prefix}_webhook_security_checks_total`,
      help: 'Total number of security checks performed',
      labelNames: ['check_type', 'result', 'threat_level'],
      registers: [client.register],
    });

    this.ipBlockedTotal = new client.Counter({
      name: `${prefix}_webhook_ip_blocked_total`,
      help: 'Total number of requests blocked by IP restrictions',
      labelNames: ['source_ip', 'reason'],
      registers: [client.register],
    });

    this.sensitiveDataDetected = new client.Counter({
      name: `${prefix}_webhook_sensitive_data_detected_total`,
      help: 'Total number of payloads with sensitive data detected',
      labelNames: ['pattern_type', 'event_type', 'repository'],
      registers: [client.register],
    });

    // Histogram Metrics
    this.webhookProcessingDuration = new client.Histogram({
      name: `${prefix}_webhook_processing_duration_seconds`,
      help: 'Webhook processing duration in seconds',
      labelNames: ['event_type', 'repository', 'status'],
      buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30],
      registers: [client.register],
    });

    this.webhookPayloadSize = new client.Histogram({
      name: `${prefix}_webhook_payload_size_bytes`,
      help: 'Webhook payload size in bytes',
      labelNames: ['event_type', 'repository'],
      buckets: [100, 1000, 10000, 100000, 1000000, 10000000],
      registers: [client.register],
    });

    // Gauge Metrics
    this.activeConnections = new client.Gauge({
      name: `${prefix}_webhook_active_connections`,
      help: 'Number of active webhook connections',
      registers: [client.register],
    });

    this.memoryUsage = new client.Gauge({
      name: `${prefix}_webhook_memory_usage_bytes`,
      help: 'Memory usage in bytes',
      labelNames: ['type'],
      registers: [client.register],
    });

    this.cpuUsage = new client.Gauge({
      name: `${prefix}_webhook_cpu_usage_percent`,
      help: 'CPU usage percentage',
      registers: [client.register],
    });

    this.webhookQueueSize = new client.Gauge({
      name: `${prefix}_webhook_queue_size`,
      help: 'Number of webhooks in processing queue',
      registers: [client.register],
    });

    // Summary Metrics
    this.webhookResponseTime = new client.Summary({
      name: `${prefix}_webhook_response_time_seconds`,
      help: 'Webhook response time in seconds',
      labelNames: ['event_type', 'status'],
      percentiles: [0.5, 0.75, 0.9, 0.95, 0.99],
      registers: [client.register],
    });

    console.log(`Metrics collector initialized with prefix: ${prefix}`);
  }

  private setupDefaultMetrics(): void {
    if (this.config.collectDefaultMetrics) {
      client.collectDefaultMetrics({
        timeout: this.config.defaultMetricsInterval,
        prefix: `${this.config.prefix}_`,
        register: client.register,
      });
    }
  }

  private startSystemMetricsCollection(): void {
    // システムメトリクスを定期的に収集
    setInterval(() => {
      this.collectSystemMetrics();
    }, 10000); // 10秒間隔

    // プロセス終了時のクリーンアップ
    process.on('SIGTERM', () => {
      this.cleanup();
    });

    process.on('SIGINT', () => {
      this.cleanup();
    });
  }

  private collectSystemMetrics(): void {
    try {
      const memUsage = process.memoryUsage();
      
      this.memoryUsage.set({ type: 'rss' }, memUsage.rss);
      this.memoryUsage.set({ type: 'heap_used' }, memUsage.heapUsed);
      this.memoryUsage.set({ type: 'heap_total' }, memUsage.heapTotal);
      this.memoryUsage.set({ type: 'external' }, memUsage.external);

      // CPU使用率の計算（簡略版）
      const cpuUsage = process.cpuUsage();
      const totalUsage = (cpuUsage.user + cpuUsage.system) / 1000000; // マイクロ秒から秒に変換
      this.cpuUsage.set(totalUsage);

    } catch (error) {
      console.error('Failed to collect system metrics:', error);
    }
  }

  // Webhook関連メトリクス記録メソッド

  /**
   * Webhook受信メトリクスを記録
   */
  public recordWebhookReceived(
    eventType: WebhookEventType,
    status: 'success' | 'error',
    repository?: string,
    sender?: string,
    processingTime?: number,
    payloadSize?: number
  ): void {
    if (!this.config.enabled) return;

    try {
      this.webhookRequestsTotal.inc({
        event_type: eventType,
        status,
        repository: repository || 'unknown',
        sender: sender || 'unknown',
      });

      if (processingTime !== undefined) {
        this.webhookProcessingDuration.observe(
          {
            event_type: eventType,
            repository: repository || 'unknown',
            status,
          },
          processingTime / 1000 // ミリ秒を秒に変換
        );

        this.webhookResponseTime.observe(
          {
            event_type: eventType,
            status,
          },
          processingTime / 1000
        );
      }

      if (payloadSize !== undefined) {
        this.webhookPayloadSize.observe(
          {
            event_type: eventType,
            repository: repository || 'unknown',
          },
          payloadSize
        );
      }
    } catch (error) {
      console.error('Failed to record webhook metrics:', error);
    }
  }

  /**
   * エラーメトリクスを記録
   */
  public recordWebhookError(
    errorType: string,
    eventType?: WebhookEventType,
    repository?: string
  ): void {
    if (!this.config.enabled) return;

    try {
      this.webhookErrorsTotal.inc({
        error_type: errorType,
        event_type: eventType || 'unknown',
        repository: repository || 'unknown',
      });
    } catch (error) {
      console.error('Failed to record error metrics:', error);
    }
  }

  /**
   * セキュリティイベントメトリクスを記録
   */
  public recordSecurityEvent(
    eventType: string,
    severity: 'low' | 'medium' | 'high' | 'critical',
    sourceIp?: string,
    actionTaken?: string
  ): void {
    if (!this.config.enabled) return;

    try {
      this.webhookSecurityEventsTotal.inc({
        event_type: eventType,
        severity,
        source_ip: this.anonymizeIpForMetrics(sourceIp || 'unknown'),
        action_taken: actionTaken || 'none',
      });
    } catch (error) {
      console.error('Failed to record security event metrics:', error);
    }
  }

  /**
   * Rate Limitメトリクスを記録
   */
  public recordRateLimitExceeded(
    limitType: 'global' | 'per_ip' | 'per_hook' | 'per_repository',
    sourceIp?: string,
    userAgent?: string
  ): void {
    if (!this.config.enabled) return;

    try {
      this.rateLimitExceededTotal.inc({
        limit_type: limitType,
        source_ip: this.anonymizeIpForMetrics(sourceIp || 'unknown'),
        user_agent: userAgent ? userAgent.substring(0, 50) : 'unknown', // 長いUser-Agentを切り詰め
      });
    } catch (error) {
      console.error('Failed to record rate limit metrics:', error);
    }
  }

  /**
   * セキュリティチェック結果を記録
   */
  public recordSecurityCheckResult(result: SecurityCheckResult): void {
    if (!this.config.enabled) return;

    try {
      const checks = result.checks;
      
      Object.entries(checks).forEach(([checkType, passed]) => {
        this.securityCheckResults.inc({
          check_type: checkType,
          result: passed ? 'pass' : 'fail',
          threat_level: result.threatLevel,
        });
      });

      if (!result.checks.ip_allowed) {
        this.ipBlockedTotal.inc({
          source_ip: 'anonymized',
          reason: 'not_in_allowlist',
        });
      }

      if (result.checks.sensitive_data_detected) {
        this.sensitiveDataDetected.inc({
          pattern_type: 'unknown',
          event_type: 'unknown',
          repository: 'unknown',
        });
      }
    } catch (error) {
      console.error('Failed to record security check metrics:', error);
    }
  }

  /**
   * 機密データ検出メトリクスを記録
   */
  public recordSensitiveDataDetection(
    patternType: string,
    eventType: WebhookEventType,
    repository?: string
  ): void {
    if (!this.config.enabled) return;

    try {
      this.sensitiveDataDetected.inc({
        pattern_type: patternType,
        event_type: eventType,
        repository: repository || 'unknown',
      });
    } catch (error) {
      console.error('Failed to record sensitive data detection metrics:', error);
    }
  }

  /**
   * アクティブ接続数を更新
   */
  public setActiveConnections(count: number): void {
    if (!this.config.enabled) return;

    try {
      this.activeConnections.set(count);
    } catch (error) {
      console.error('Failed to update active connections metric:', error);
    }
  }

  /**
   * キューサイズを更新
   */
  public setQueueSize(size: number): void {
    if (!this.config.enabled) return;

    try {
      this.webhookQueueSize.set(size);
    } catch (error) {
      console.error('Failed to update queue size metric:', error);
    }
  }

  /**
   * カスタムメトリクスを記録
   */
  public recordCustomMetric(
    name: string,
    value: number,
    labels?: Record<string, string>,
    help?: string
  ): void {
    if (!this.config.enabled) return;

    try {
      const fullName = `${this.config.prefix}_${name}`;
      
      // 既存メトリクスをチェック
      let metric = client.register.getSingleMetric(fullName);
      
      if (!metric) {
        // 新しいGaugeメトリクスを作成
        metric = new client.Gauge({
          name: fullName,
          help: help || `Custom metric: ${name}`,
          labelNames: labels ? Object.keys(labels) : [],
          registers: [client.register],
        });
      }

      if (metric instanceof client.Gauge) {
        metric.set(labels || {}, value);
      }
    } catch (error) {
      console.error('Failed to record custom metric:', error);
    }
  }

  /**
   * Prometheusメトリクスを文字列として取得
   */
  public async getMetrics(): Promise<string> {
    if (!this.config.enabled) {
      return '# Metrics collection is disabled\n';
    }

    try {
      return await client.register.metrics();
    } catch (error) {
      console.error('Failed to get metrics:', error);
      return '# Error retrieving metrics\n';
    }
  }

  /**
   * メトリクス統計情報を取得
   */
  public getMetricsStatistics(): WebhookMetrics {
    if (!this.config.enabled) {
      return this.getEmptyMetrics();
    }

    try {
      // 実際の実装では、メトリクスレジストリから値を取得
      // ここでは簡略化した実装を提供
      return {
        requests_total: 0,
        requests_per_event_type: {} as Record<WebhookEventType, number>,
        errors_total: 0,
        errors_per_type: {},
        processing_duration_seconds: [],
        rate_limit_exceeded_total: 0,
        security_events_total: 0,
        active_connections: 0,
        memory_usage_bytes: process.memoryUsage().heapUsed,
        cpu_usage_percent: 0,
      };
    } catch (error) {
      console.error('Failed to get metrics statistics:', error);
      return this.getEmptyMetrics();
    }
  }

  private getEmptyMetrics(): WebhookMetrics {
    return {
      requests_total: 0,
      requests_per_event_type: {} as Record<WebhookEventType, number>,
      errors_total: 0,
      errors_per_type: {},
      processing_duration_seconds: [],
      rate_limit_exceeded_total: 0,
      security_events_total: 0,
      active_connections: 0,
      memory_usage_bytes: 0,
      cpu_usage_percent: 0,
    };
  }

  /**
   * メトリクス用にIPアドレスを匿名化
   */
  private anonymizeIpForMetrics(ip: string): string {
    if (ip === 'unknown' || ip === 'internal') {
      return ip;
    }

    // IPv4の場合、最後のオクテットを0にマスク
    const parts = ip.split('.');
    if (parts.length === 4) {
      return `${parts[0]}.${parts[1]}.${parts[2]}.0`;
    }

    // IPv6等の場合は後半をマスク
    if (ip.includes(':')) {
      const parts = ip.split(':');
      const masked = parts.slice(0, Math.ceil(parts.length / 2)).concat(
        Array(Math.floor(parts.length / 2)).fill('xxxx')
      );
      return masked.join(':');
    }

    return 'anonymized';
  }

  /**
   * ヘルスチェック用メトリクス
   */
  public getHealthMetrics(): {
    status: 'healthy' | 'unhealthy' | 'degraded';
    metrics: {
      total_requests: number;
      error_rate: number;
      avg_response_time: number;
      memory_usage_mb: number;
      cpu_usage_percent: number;
    };
  } {
    if (!this.config.enabled) {
      return {
        status: 'degraded',
        metrics: {
          total_requests: 0,
          error_rate: 0,
          avg_response_time: 0,
          memory_usage_mb: 0,
          cpu_usage_percent: 0,
        },
      };
    }

    try {
      const memUsage = process.memoryUsage();
      const memUsageMB = memUsage.heapUsed / 1024 / 1024;

      // 簡略化したヘルスチェック
      let status: 'healthy' | 'unhealthy' | 'degraded' = 'healthy';

      if (memUsageMB > 1024) { // 1GB超過
        status = 'degraded';
      }

      if (memUsageMB > 2048) { // 2GB超過
        status = 'unhealthy';
      }

      return {
        status,
        metrics: {
          total_requests: 0, // 実際の値を取得
          error_rate: 0, // 実際の値を計算
          avg_response_time: 0, // 実際の値を計算
          memory_usage_mb: memUsageMB,
          cpu_usage_percent: 0, // 実際の値を計算
        },
      };
    } catch (error) {
      console.error('Failed to get health metrics:', error);
      return {
        status: 'unhealthy',
        metrics: {
          total_requests: 0,
          error_rate: 100,
          avg_response_time: 0,
          memory_usage_mb: 0,
          cpu_usage_percent: 0,
        },
      };
    }
  }

  /**
   * メトリクスのリセット（テスト用）
   */
  public resetMetrics(): void {
    if (!this.config.enabled) return;

    try {
      client.register.clear();
      this.initializeMetrics();
      console.log('Metrics reset successfully');
    } catch (error) {
      console.error('Failed to reset metrics:', error);
    }
  }

  /**
   * クリーンアップ処理
   */
  public cleanup(): void {
    try {
      if (this.config.enabled) {
        client.register.clear();
        console.log('Metrics collector cleaned up');
      }
    } catch (error) {
      console.error('Failed to cleanup metrics collector:', error);
    }
  }

  /**
   * メトリクス設定を更新
   */
  public updateConfig(newConfig: Partial<MetricsConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    if (!this.config.enabled) {
      this.cleanup();
    } else {
      // 必要に応じてメトリクスを再初期化
      console.log('Metrics configuration updated');
    }
  }
}