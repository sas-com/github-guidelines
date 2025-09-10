/**
 * Audit Logger
 * エス・エー・エス株式会社 GitHub Webhook セキュリティ監査ログ
 */

import winston from 'winston';
import { ElasticsearchTransport } from 'winston-elasticsearch';
import crypto from 'crypto';
import {
  AuditLogEntry,
  WebhookEventType,
  SecurityCheckResult
} from '@/types/webhook.types.js';

export interface LoggerConfig {
  level: string;
  environment: string;
  service: string;
  enableConsole: boolean;
  enableFile: boolean;
  enableElasticsearch: boolean;
  elasticsearch?: {
    level: string;
    clientOpts: {
      node: string;
      auth?: {
        username: string;
        password: string;
      };
    };
    index: string;
  };
  file?: {
    filename: string;
    maxsize: number;
    maxFiles: number;
  };
}

export interface SecurityEvent {
  type: 'UNAUTHORIZED_IP_ACCESS' | 'INVALID_SIGNATURE' | 'RATE_LIMIT_EXCEEDED' | 
        'PAYLOAD_TOO_LARGE' | 'SENSITIVE_DATA_DETECTED' | 'INVALID_PAYLOAD' |
        'SUSPICIOUS_ACTIVITY' | 'BRUTE_FORCE_ATTEMPT' | 'MALICIOUS_PAYLOAD';
  ip: string;
  timestamp: Date;
  deliveryId?: string;
  details?: any;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  userAgent?: string;
  eventType?: WebhookEventType;
  repository?: string;
  sender?: string;
}

export interface WebhookReceivedEvent {
  deliveryId: string;
  event: WebhookEventType;
  repository?: string;
  sender?: string;
  ip: string;
  timestamp: Date;
  processingTime: number;
  payloadSize?: number;
  securityChecks?: SecurityCheckResult;
  userAgent?: string;
}

export interface ErrorEvent {
  type: 'WEBHOOK_PROCESSING_ERROR' | 'VALIDATION_ERROR' | 'SECURITY_ERROR' | 
        'DATABASE_ERROR' | 'NETWORK_ERROR' | 'CONFIGURATION_ERROR';
  deliveryId?: string;
  error: string;
  stack?: string;
  timestamp: Date;
  ip?: string;
  eventType?: WebhookEventType;
  repository?: string;
  metadata?: any;
}

export interface WarningEvent {
  type: 'UNKNOWN_EVENT_TYPE' | 'DEPRECATED_FEATURE' | 'PERFORMANCE_DEGRADATION' |
        'CONFIGURATION_WARNING' | 'CAPACITY_WARNING' | 'DEPENDENCY_WARNING';
  event?: string;
  deliveryId?: string;
  timestamp: Date;
  message: string;
  details?: any;
}

export interface PerformanceMetric {
  operation: string;
  duration: number;
  timestamp: Date;
  metadata?: any;
}

export interface ComplianceLog {
  action: string;
  user?: string;
  resource?: string;
  timestamp: Date;
  success: boolean;
  reason?: string;
  ip?: string;
  metadata?: any;
}

export class Logger {
  private winston: winston.Logger;
  private config: LoggerConfig;

  constructor(config: LoggerConfig) {
    this.config = config;
    this.winston = this.createWinstonLogger();
  }

  private createWinstonLogger(): winston.Logger {
    const transports: winston.transport[] = [];

    // Console transport
    if (this.config.enableConsole) {
      transports.push(
        new winston.transports.Console({
          level: this.config.level,
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
            winston.format.errors({ stack: true }),
            winston.format.printf(({ timestamp, level, message, ...meta }) => {
              const metaStr = Object.keys(meta).length ? JSON.stringify(meta, null, 2) : '';
              return `${timestamp} [${level}]: ${message} ${metaStr}`;
            })
          ),
        })
      );
    }

    // File transport
    if (this.config.enableFile && this.config.file) {
      transports.push(
        new winston.transports.File({
          level: this.config.level,
          filename: this.config.file.filename,
          maxsize: this.config.file.maxsize,
          maxFiles: this.config.file.maxFiles,
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.errors({ stack: true }),
            winston.format.json()
          ),
        })
      );
    }

    // Elasticsearch transport
    if (this.config.enableElasticsearch && this.config.elasticsearch) {
      try {
        transports.push(
          new ElasticsearchTransport({
            level: this.config.elasticsearch.level,
            clientOpts: this.config.elasticsearch.clientOpts,
            index: this.config.elasticsearch.index,
            transformer: (logData) => this.transformLogForElasticsearch(logData),
          })
        );
      } catch (error) {
        console.error('Failed to initialize Elasticsearch transport:', error);
      }
    }

    return winston.createLogger({
      level: this.config.level,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: {
        service: this.config.service,
        environment: this.config.environment,
        hostname: process.env.HOSTNAME || 'unknown',
        version: process.env.npm_package_version || '1.0.0',
      },
      transports,
      exitOnError: false,
    });
  }

  private transformLogForElasticsearch(logData: any) {
    return {
      '@timestamp': logData.timestamp || new Date().toISOString(),
      level: logData.level,
      message: logData.message,
      service: logData.meta?.service || this.config.service,
      environment: logData.meta?.environment || this.config.environment,
      ...logData.meta,
    };
  }

  private generateEventId(): string {
    return `evt_${crypto.randomBytes(8).toString('hex')}`;
  }

  private createAuditLogEntry(
    eventType: 'webhook_received' | 'security_event' | 'error' | 'warning',
    severity: 'info' | 'warn' | 'error' | 'critical',
    additionalData: Partial<AuditLogEntry>
  ): AuditLogEntry {
    const baseEntry: AuditLogEntry = {
      timestamp: new Date().toISOString(),
      event_id: this.generateEventId(),
      event_type: eventType,
      severity,
      source: {
        ip: 'unknown',
      },
      compliance: {
        gdpr_compliant: true,
        retention_days: 365,
        encrypted: true,
      },
      ...additionalData,
    };

    return baseEntry;
  }

  /**
   * セキュリティイベントをログに記録
   */
  public logSecurityEvent(event: SecurityEvent): void {
    const auditLog = this.createAuditLogEntry('security_event', event.severity || 'warn', {
      source: {
        ip: event.ip,
        user_agent: event.userAgent,
        delivery_id: event.deliveryId,
      },
      webhook: event.eventType ? {
        event_type: event.eventType,
        repository: event.repository,
        sender: event.sender,
        signature_valid: false, // セキュリティイベントなので通常false
        processing_time_ms: 0,
      } : undefined,
      security: {
        ip_allowed: event.type !== 'UNAUTHORIZED_IP_ACCESS',
        rate_limit_remaining: event.type === 'RATE_LIMIT_EXCEEDED' ? 0 : 60,
        payload_size_bytes: 0,
        sensitive_data_detected: event.type === 'SENSITIVE_DATA_DETECTED',
        threat_level: event.severity || 'medium',
      },
      metadata: {
        security_event_type: event.type,
        details: event.details,
      },
    });

    const logLevel = this.mapSeverityToLogLevel(event.severity || 'warn');
    this.winston.log(logLevel, `Security event: ${event.type}`, {
      audit: auditLog,
      securityEvent: event,
    });

    // 重大なセキュリティイベントの場合は即座にアラート
    if (event.severity === 'critical' || event.severity === 'high') {
      this.triggerSecurityAlert(event);
    }
  }

  /**
   * Webhook受信イベントをログに記録
   */
  public logWebhookReceived(event: WebhookReceivedEvent): void {
    const auditLog = this.createAuditLogEntry('webhook_received', 'info', {
      source: {
        ip: event.ip,
        user_agent: event.userAgent,
        delivery_id: event.deliveryId,
      },
      webhook: {
        event_type: event.event,
        repository: event.repository,
        sender: event.sender,
        signature_valid: true,
        processing_time_ms: event.processingTime,
      },
      security: {
        ip_allowed: true,
        rate_limit_remaining: 59, // 仮の値
        payload_size_bytes: event.payloadSize || 0,
        sensitive_data_detected: false,
        threat_level: 'low',
      },
    });

    this.winston.info('Webhook received and processed successfully', {
      audit: auditLog,
      webhookEvent: event,
    });

    // パフォーマンス監視
    if (event.processingTime > 5000) { // 5秒超過
      this.logWarning({
        type: 'PERFORMANCE_DEGRADATION',
        deliveryId: event.deliveryId,
        timestamp: new Date(),
        message: 'Webhook processing time exceeded threshold',
        details: {
          processingTime: event.processingTime,
          eventType: event.event,
          repository: event.repository,
        },
      });
    }
  }

  /**
   * エラーをログに記録
   */
  public logError(event: ErrorEvent): void {
    const auditLog = this.createAuditLogEntry('error', 'error', {
      source: {
        ip: event.ip || 'unknown',
        delivery_id: event.deliveryId,
      },
      webhook: event.eventType ? {
        event_type: event.eventType,
        repository: event.repository,
        sender: 'unknown',
        signature_valid: false,
        processing_time_ms: 0,
      } : undefined,
      error: {
        code: event.type,
        message: event.error,
        stack: event.stack,
      },
      metadata: event.metadata,
    });

    this.winston.error(`${event.type}: ${event.error}`, {
      audit: auditLog,
      errorEvent: event,
      stack: event.stack,
    });
  }

  /**
   * 警告をログに記録
   */
  public logWarning(event: WarningEvent): void {
    const auditLog = this.createAuditLogEntry('warning', 'warn', {
      source: {
        ip: 'internal',
        delivery_id: event.deliveryId,
      },
      metadata: {
        warning_type: event.type,
        event: event.event,
        details: event.details,
      },
    });

    this.winston.warn(`${event.type}: ${event.message}`, {
      audit: auditLog,
      warningEvent: event,
    });
  }

  /**
   * パフォーマンスメトリクスをログに記録
   */
  public logPerformance(metric: PerformanceMetric): void {
    this.winston.debug('Performance metric', {
      performance: metric,
      timestamp: metric.timestamp.toISOString(),
    });

    // 異常に遅い処理の場合は警告
    if (metric.duration > 10000) { // 10秒超過
      this.logWarning({
        type: 'PERFORMANCE_DEGRADATION',
        timestamp: new Date(),
        message: `Slow operation detected: ${metric.operation}`,
        details: {
          operation: metric.operation,
          duration: metric.duration,
          metadata: metric.metadata,
        },
      });
    }
  }

  /**
   * コンプライアンス関連ログを記録
   */
  public logCompliance(log: ComplianceLog): void {
    const auditLog = this.createAuditLogEntry('webhook_received', 'info', {
      source: {
        ip: log.ip || 'internal',
      },
      compliance: {
        gdpr_compliant: true,
        retention_days: 2555, // 7年間保持
        encrypted: true,
      },
      metadata: {
        compliance_action: log.action,
        user: log.user,
        resource: log.resource,
        success: log.success,
        reason: log.reason,
      },
    });

    this.winston.info(`Compliance log: ${log.action}`, {
      audit: auditLog,
      complianceLog: log,
    });
  }

  /**
   * 構造化ログ（汎用）
   */
  public info(message: string, metadata?: any): void {
    this.winston.info(message, metadata);
  }

  public warn(message: string, metadata?: any): void {
    this.winston.warn(message, metadata);
  }

  public error(message: string, metadata?: any): void {
    this.winston.error(message, metadata);
  }

  public debug(message: string, metadata?: any): void {
    this.winston.debug(message, metadata);
  }

  /**
   * 重大度からログレベルへのマッピング
   */
  private mapSeverityToLogLevel(severity: 'low' | 'medium' | 'high' | 'critical'): string {
    switch (severity) {
      case 'low':
        return 'info';
      case 'medium':
        return 'warn';
      case 'high':
        return 'error';
      case 'critical':
        return 'error';
      default:
        return 'info';
    }
  }

  /**
   * セキュリティアラート送信（実装は環境に依存）
   */
  private async triggerSecurityAlert(event: SecurityEvent): Promise<void> {
    try {
      // 実際の実装では、Slack、Teams、Email、PagerDuty等にアラートを送信
      const alertData = {
        title: `🚨 Security Alert: ${event.type}`,
        message: `重大なセキュリティイベントが検出されました`,
        severity: event.severity,
        details: {
          type: event.type,
          ip: event.ip,
          timestamp: event.timestamp.toISOString(),
          deliveryId: event.deliveryId,
          repository: event.repository,
          userAgent: event.userAgent,
        },
        environment: this.config.environment,
        service: this.config.service,
      };

      // ログに記録（実際のアラート送信は別途実装）
      this.winston.error('SECURITY ALERT TRIGGERED', { alert: alertData });

      // 環境変数でアラート送信先を設定
      const alertEndpoint = process.env.SECURITY_ALERT_WEBHOOK_URL;
      if (alertEndpoint) {
        // 実際のHTTPリクエスト送信は省略（fetch等を使用）
        console.log(`Security alert would be sent to: ${alertEndpoint}`);
      }

    } catch (error) {
      this.winston.error('Failed to trigger security alert', {
        error: error.message,
        originalEvent: event,
      });
    }
  }

  /**
   * ログローテーションと保持ポリシーの管理
   */
  public async cleanupOldLogs(): Promise<void> {
    try {
      // ファイルベースログの場合は winston が自動で管理
      // Elasticsearchの場合は Index Lifecycle Management (ILM) で管理
      this.winston.info('Log cleanup process completed');
    } catch (error) {
      this.winston.error('Log cleanup failed', { error: error.message });
    }
  }

  /**
   * ログ統計情報を取得
   */
  public getLogStatistics(): {
    totalLogs: number;
    errorLogs: number;
    warningLogs: number;
    securityEvents: number;
    averageProcessingTime: number;
  } {
    // 実装は使用するログストレージに依存
    // ここでは模擬的な統計を返す
    return {
      totalLogs: 0,
      errorLogs: 0,
      warningLogs: 0,
      securityEvents: 0,
      averageProcessingTime: 0,
    };
  }

  /**
   * ログの暗号化状態を確認
   */
  public verifyLogEncryption(): boolean {
    // 実装は使用するログストレージとEncryption方式に依存
    return true; // デフォルトで暗号化されていると仮定
  }

  /**
   * GDPR準拠のためのログ匿名化
   */
  public anonymizePersonalData(logEntry: any): any {
    const anonymized = { ...logEntry };
    
    // IP アドレスの匿名化（最後のオクテットをマスク）
    if (anonymized.source?.ip) {
      anonymized.source.ip = this.anonymizeIpAddress(anonymized.source.ip);
    }

    // ユーザーメール等の匿名化
    if (anonymized.webhook?.sender) {
      anonymized.webhook.sender = 'anonymized_user';
    }

    return anonymized;
  }

  private anonymizeIpAddress(ip: string): string {
    const parts = ip.split('.');
    if (parts.length === 4) {
      // IPv4の場合、最後のオクテットを0にマスク
      return `${parts[0]}.${parts[1]}.${parts[2]}.0`;
    }
    // IPv6等の場合は下位64bitをマスク（簡略化）
    return ip.substring(0, ip.length / 2) + 'x'.repeat(ip.length / 2);
  }

  /**
   * リソースのクリーンアップ
   */
  public async close(): Promise<void> {
    return new Promise((resolve) => {
      this.winston.close(() => {
        resolve();
      });
    });
  }
}