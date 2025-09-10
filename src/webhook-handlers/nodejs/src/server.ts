/**
 * GitHub Webhook Security Server
 * エス・エー・エス株式会社 GitHub Webhook セキュリティサーバー (Node.js/TypeScript)
 */

import express from 'express';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import cors from 'cors';
import compression from 'compression';
import morgan from 'morgan';
import { v4 as uuidv4 } from 'uuid';
import dotenv from 'dotenv';
import 'express-async-errors';

import {
  WebhookSecurityConfig,
  ServerConfig,
  WebhookEventType,
  WebhookRequest,
  WebhookResponse,
  WebhookError,
  HealthCheckResult
} from './types/webhook.types.js';

import { WebhookSecurityValidator } from './security/webhook-validator.js';
import { Logger } from './logging/audit-logger.js';
import { MetricsCollector } from './monitoring/metrics-collector.js';

// 環境変数の読み込み
dotenv.config();

class GitHubWebhookSecurityServer {
  private app: express.Application;
  private server: any;
  private config: ServerConfig;
  private validator: WebhookSecurityValidator;
  private logger: Logger;
  private metrics: MetricsCollector;
  private startTime: Date;
  private activeConnections: Set<any> = new Set();
  private gracefulShutdownTimeout: NodeJS.Timeout | null = null;

  constructor() {
    this.startTime = new Date();
    this.config = this.loadConfiguration();
    this.app = express();
    
    // 依存サービスの初期化
    this.logger = new Logger({
      level: this.config.log_level,
      environment: this.config.environment,
      service: 'github-webhook-security-server',
      enableConsole: true,
      enableFile: true,
      enableElasticsearch: process.env.ELASTICSEARCH_ENABLED === 'true',
      elasticsearch: process.env.ELASTICSEARCH_ENABLED === 'true' ? {
        level: 'info',
        clientOpts: {
          node: process.env.ELASTICSEARCH_URL || 'http://localhost:9200',
          auth: process.env.ELASTICSEARCH_USERNAME ? {
            username: process.env.ELASTICSEARCH_USERNAME,
            password: process.env.ELASTICSEARCH_PASSWORD || '',
          } : undefined,
        },
        index: 'webhook-security-logs',
      } : undefined,
      file: {
        filename: 'logs/webhook-security.log',
        maxsize: 10 * 1024 * 1024, // 10MB
        maxFiles: 5,
      },
    });

    this.metrics = new MetricsCollector({
      enabled: this.config.enable_metrics,
      collectDefaultMetrics: true,
      defaultMetricsInterval: 10000,
      prefix: 'github_webhook',
      labels: {
        service: 'github-webhook-security-server',
        environment: this.config.environment,
        version: process.env.npm_package_version || '1.0.0',
      },
    });

    this.validator = new WebhookSecurityValidator(this.config.security, this.logger);

    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
    this.setupGracefulShutdown();

    this.logger.info('GitHub Webhook Security Server initialized', {
      environment: this.config.environment,
      port: this.config.port,
      securityEnabled: true,
      metricsEnabled: this.config.enable_metrics,
    });
  }

  private loadConfiguration(): ServerConfig {
    const defaultConfig: ServerConfig = {
      port: parseInt(process.env.PORT || '3000', 10),
      host: process.env.HOST || '0.0.0.0',
      environment: (process.env.NODE_ENV as 'development' | 'staging' | 'production') || 'development',
      log_level: process.env.LOG_LEVEL || 'info',
      enable_metrics: process.env.ENABLE_METRICS === 'true',
      enable_health_check: process.env.ENABLE_HEALTH_CHECK !== 'false',
      enable_swagger: process.env.ENABLE_SWAGGER === 'true',
      cors_enabled: process.env.CORS_ENABLED === 'true',
      compression_enabled: process.env.COMPRESSION_ENABLED !== 'false',
      trust_proxy: process.env.TRUST_PROXY === 'true',
      request_timeout_ms: parseInt(process.env.REQUEST_TIMEOUT_MS || '30000', 10),
      body_limit: process.env.BODY_LIMIT || '10mb',
      security: {
        webhook_secret: process.env.WEBHOOK_SECRET || '',
        allowed_ips: (process.env.ALLOWED_IPS || '').split(',').filter(ip => ip.trim()),
        rate_limits: {
          global_per_minute: parseInt(process.env.RATE_LIMIT_GLOBAL || '1000', 10),
          per_ip_per_minute: parseInt(process.env.RATE_LIMIT_PER_IP || '60', 10),
          per_hook_per_minute: parseInt(process.env.RATE_LIMIT_PER_HOOK || '120', 10),
          per_repository_per_minute: parseInt(process.env.RATE_LIMIT_PER_REPO || '100', 10),
          burst_capacity: parseInt(process.env.RATE_LIMIT_BURST || '20', 10),
        },
        max_payload_size_bytes: parseInt(process.env.MAX_PAYLOAD_SIZE || '10485760', 10), // 10MB
        signature_algorithm: 'sha256' as const,
        ip_validation_strict: process.env.IP_VALIDATION_STRICT === 'true',
        geo_restrictions: (process.env.GEO_RESTRICTIONS || 'JP,US').split(','),
        custom_allowlist: (process.env.CUSTOM_IP_ALLOWLIST || '').split(',').filter(ip => ip.trim()),
      },
    };

    // 必須設定の検証
    if (!defaultConfig.security.webhook_secret) {
      throw new Error('WEBHOOK_SECRET environment variable is required');
    }

    return defaultConfig;
  }

  private setupMiddleware(): void {
    // Trust proxy設定
    if (this.config.trust_proxy) {
      this.app.set('trust proxy', true);
    }

    // セキュリティヘッダー設定
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'none'"],
          objectSrc: ["'none'"],
          styleSrc: ["'self'", "'unsafe-inline'"], // Swagger UI用
          imgSrc: ["'self'", 'data:'],
          fontSrc: ["'self'"],
          connectSrc: ["'self'"],
          mediaSrc: ["'none'"],
          frameSrc: ["'none'"],
          childSrc: ["'none'"],
          workerSrc: ["'none'"],
          manifestSrc: ["'self'"],
        },
      },
      crossOriginEmbedderPolicy: false, // Swagger UI用
      hsts: {
        maxAge: 31536000, // 1年
        includeSubDomains: true,
        preload: true,
      },
      noSniff: true,
      frameguard: { action: 'deny' },
      xssFilter: true,
    }));

    // CORS設定
    if (this.config.cors_enabled) {
      this.app.use(cors({
        origin: process.env.ALLOWED_ORIGINS?.split(',') || false,
        credentials: false,
        methods: ['POST', 'GET'],
        allowedHeaders: [
          'Content-Type',
          'X-GitHub-Delivery',
          'X-GitHub-Event',
          'X-GitHub-Hook-ID',
          'X-GitHub-Hook-Installation-Target-ID',
          'X-Hub-Signature-256',
          'User-Agent',
        ],
      }));
    }

    // 圧縮
    if (this.config.compression_enabled) {
      this.app.use(compression());
    }

    // ログ設定
    this.app.use(morgan('combined', {
      stream: {
        write: (message: string) => {
          this.logger.info(message.trim());
        },
      },
    }));

    // Rate Limiting - Global
    const globalLimiter = rateLimit({
      windowMs: 60 * 1000, // 1分
      max: this.config.security.rate_limits.global_per_minute,
      standardHeaders: true,
      legacyHeaders: false,
      keyGenerator: (req) => 'global',
      handler: (req, res) => {
        this.logger.logSecurityEvent({
          type: 'RATE_LIMIT_EXCEEDED',
          ip: req.ip,
          timestamp: new Date(),
          severity: 'medium',
          details: { 
            path: req.path,
            method: req.method,
            limitType: 'global',
          },
        });

        this.metrics.recordRateLimitExceeded('global', req.ip, req.get('user-agent'));

        res.status(429).json({
          error: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests globally',
          details: 'Global rate limit exceeded',
          timestamp: new Date().toISOString(),
          request_id: this.generateRequestId(),
        });
      },
    });

    // Rate Limiting - Per IP
    const perIpLimiter = rateLimit({
      windowMs: 60 * 1000, // 1分
      max: this.config.security.rate_limits.per_ip_per_minute,
      standardHeaders: true,
      legacyHeaders: false,
      keyGenerator: (req) => req.ip,
      handler: (req, res) => {
        this.logger.logSecurityEvent({
          type: 'RATE_LIMIT_EXCEEDED',
          ip: req.ip,
          timestamp: new Date(),
          severity: 'high',
          details: {
            path: req.path,
            method: req.method,
            limitType: 'per_ip',
          },
        });

        this.metrics.recordRateLimitExceeded('per_ip', req.ip, req.get('user-agent'));

        res.status(429).json({
          error: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests from this IP',
          details: 'Per-IP rate limit exceeded',
          timestamp: new Date().toISOString(),
          request_id: this.generateRequestId(),
        });
      },
    });

    this.app.use(globalLimiter);
    this.app.use(perIpLimiter);

    // リクエストID追加
    this.app.use((req, res, next) => {
      req.id = this.generateRequestId();
      res.setHeader('X-Request-ID', req.id);
      next();
    });

    // 接続数追跡
    this.app.use((req, res, next) => {
      this.activeConnections.add(req);
      this.metrics.setActiveConnections(this.activeConnections.size);

      res.on('finish', () => {
        this.activeConnections.delete(req);
        this.metrics.setActiveConnections(this.activeConnections.size);
      });

      next();
    });

    // Body parser (raw bodyを保持)
    this.app.use('/webhook', express.raw({ 
      type: 'application/json',
      limit: this.config.body_limit,
    }));

    // JSON parser for other routes
    this.app.use(express.json({ 
      limit: '1mb',
      type: (req) => !req.path.startsWith('/webhook'),
    }));
  }

  private setupRoutes(): void {
    // ヘルスチェック
    if (this.config.enable_health_check) {
      this.app.get('/health', this.handleHealthCheck.bind(this));
      this.app.get('/healthz', this.handleHealthCheck.bind(this)); // Kubernetes用
      this.app.get('/ready', this.handleReadinessCheck.bind(this));
    }

    // メトリクス
    if (this.config.enable_metrics) {
      this.app.get('/metrics', this.handleMetrics.bind(this));
    }

    // Webhook受信エンドポイント
    this.app.post('/webhook/github', this.handleWebhook.bind(this));

    // 設定情報（非機密情報のみ）
    this.app.get('/config', this.handleConfig.bind(this));

    // 404ハンドラー
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'NOT_FOUND',
        message: 'Endpoint not found',
        path: req.originalUrl,
        timestamp: new Date().toISOString(),
        request_id: req.id,
      });
    });
  }

  private async handleWebhook(req: express.Request, res: express.Response): Promise<void> {
    const startTime = Date.now();
    const deliveryId = req.headers['x-github-delivery'] as string;
    const eventType = req.headers['x-github-event'] as WebhookEventType;
    const signature = req.headers['x-hub-signature-256'] as string;
    const userAgent = req.headers['user-agent'] as string;

    try {
      // 基本的な入力検証
      if (!deliveryId || !eventType || !signature) {
        throw this.validator.createWebhookError(
          'MISSING_HEADERS',
          'Required headers are missing',
          400,
          'Missing one or more required headers: X-GitHub-Delivery, X-GitHub-Event, X-Hub-Signature-256',
          deliveryId
        );
      }

      // セキュリティチェック実行
      const securityResult = await this.validator.performSecurityCheck(
        req.ip,
        req.headers as any,
        req.body as Buffer,
        eventType
      );

      if (!securityResult.passed) {
        // セキュリティチェック失敗
        this.logger.logSecurityEvent({
          type: 'SUSPICIOUS_ACTIVITY',
          ip: req.ip,
          timestamp: new Date(),
          deliveryId,
          severity: securityResult.threatLevel,
          details: {
            checks: securityResult.checks,
            actionsTaken: securityResult.actionsTaken,
            eventType,
            userAgent,
          },
        });

        this.metrics.recordSecurityEvent(
          'security_check_failed',
          securityResult.threatLevel,
          req.ip,
          securityResult.actionsTaken.join(',')
        );

        // 脅威レベルに応じたレスポンス
        let statusCode = 400;
        let errorCode = 'SECURITY_CHECK_FAILED';
        
        if (!securityResult.checks.signature_valid) {
          statusCode = 401;
          errorCode = 'INVALID_SIGNATURE';
        } else if (!securityResult.checks.ip_allowed) {
          statusCode = 403;
          errorCode = 'FORBIDDEN_IP';
        } else if (!securityResult.checks.payload_size_ok) {
          statusCode = 413;
          errorCode = 'PAYLOAD_TOO_LARGE';
        }

        throw this.validator.createWebhookError(
          errorCode,
          'Security validation failed',
          statusCode,
          `Security checks failed: ${securityResult.actionsTaken.join(', ')}`,
          deliveryId
        );
      }

      // ペイロード解析
      let payload: any;
      try {
        payload = JSON.parse(req.body.toString('utf8'));
      } catch (error) {
        throw this.validator.createWebhookError(
          'INVALID_PAYLOAD',
          'Invalid JSON payload',
          400,
          'Failed to parse JSON payload',
          deliveryId
        );
      }

      // ペイロード検証
      const validationResult = await this.validator.validatePayload(payload, eventType);
      if (!validationResult.isValid) {
        throw this.validator.createWebhookError(
          'INVALID_PAYLOAD',
          'Payload validation failed',
          400,
          validationResult.errors.join(', '),
          deliveryId
        );
      }

      // ペイロードサニタイゼーション
      const sanitizedPayload = this.validator.sanitizePayload(payload);

      // イベント処理
      await this.processWebhookEvent(eventType, sanitizedPayload, deliveryId, req.ip);

      const processingTime = Date.now() - startTime;

      // 成功ログ
      this.logger.logWebhookReceived({
        deliveryId,
        event: eventType,
        repository: sanitizedPayload.repository?.full_name,
        sender: sanitizedPayload.sender?.login,
        ip: req.ip,
        timestamp: new Date(),
        processingTime,
        payloadSize: req.body.length,
        securityChecks: securityResult,
        userAgent,
      });

      // メトリクス更新
      this.metrics.recordWebhookReceived(
        eventType,
        'success',
        sanitizedPayload.repository?.full_name,
        sanitizedPayload.sender?.login,
        processingTime,
        req.body.length
      );

      this.metrics.recordSecurityCheckResult(securityResult);

      // レスポンス送信
      const response: WebhookResponse = {
        status: 'success',
        delivery_id: deliveryId,
        event_type: eventType,
        processing_time_ms: processingTime,
        timestamp: new Date().toISOString(),
        metadata: {
          repository: sanitizedPayload.repository?.full_name,
          sender: sanitizedPayload.sender?.login,
          action: sanitizedPayload.action,
          security_checks_passed: true,
          sensitive_data_detected: validationResult.warnings?.some(w => w.includes('Sensitive data')) || false,
        },
      };

      res.status(200).json(response);

    } catch (error) {
      const processingTime = Date.now() - startTime;

      if (error instanceof WebhookError || error.code) {
        // 既知のWebhookエラー
        this.logger.logError({
          type: 'WEBHOOK_PROCESSING_ERROR',
          deliveryId,
          error: error.message,
          stack: error.stack,
          timestamp: new Date(),
          ip: req.ip,
          eventType,
        });

        this.metrics.recordWebhookError(error.code, eventType);
        this.metrics.recordWebhookReceived(eventType, 'error', undefined, undefined, processingTime);

        res.status(error.statusCode || 500).json({
          error: error.code,
          message: error.message,
          details: error.details,
          timestamp: new Date().toISOString(),
          request_id: req.id,
          delivery_id: deliveryId,
          correlation_id: error.correlationId,
        });
      } else {
        // 未知のエラー
        this.logger.logError({
          type: 'WEBHOOK_PROCESSING_ERROR',
          deliveryId,
          error: error.message,
          stack: error.stack,
          timestamp: new Date(),
          ip: req.ip,
          eventType,
        });

        this.metrics.recordWebhookError('INTERNAL_SERVER_ERROR', eventType);
        this.metrics.recordWebhookReceived(eventType, 'error', undefined, undefined, processingTime);

        res.status(500).json({
          error: 'INTERNAL_SERVER_ERROR',
          message: 'An unexpected error occurred',
          timestamp: new Date().toISOString(),
          request_id: req.id,
          delivery_id: deliveryId,
        });
      }
    }
  }

  private async processWebhookEvent(
    eventType: WebhookEventType,
    payload: any,
    deliveryId: string,
    clientIp: string
  ): Promise<void> {
    // イベント別処理ロジック
    switch (eventType) {
      case 'push':
        await this.handlePushEvent(payload, deliveryId, clientIp);
        break;

      case 'pull_request':
        await this.handlePullRequestEvent(payload, deliveryId, clientIp);
        break;

      case 'issues':
        await this.handleIssuesEvent(payload, deliveryId, clientIp);
        break;

      case 'repository':
        await this.handleRepositoryEvent(payload, deliveryId, clientIp);
        break;

      case 'organization':
        await this.handleOrganizationEvent(payload, deliveryId, clientIp);
        break;

      case 'member':
        await this.handleMemberEvent(payload, deliveryId, clientIp);
        break;

      case 'team':
        await this.handleTeamEvent(payload, deliveryId, clientIp);
        break;

      case 'installation':
        await this.handleInstallationEvent(payload, deliveryId, clientIp);
        break;

      case 'secret_scanning_alert':
        await this.handleSecretScanningEvent(payload, deliveryId, clientIp);
        break;

      case 'code_scanning_alert':
        await this.handleCodeScanningEvent(payload, deliveryId, clientIp);
        break;

      case 'dependabot_alert':
        await this.handleDependabotEvent(payload, deliveryId, clientIp);
        break;

      default:
        this.logger.logWarning({
          type: 'UNKNOWN_EVENT_TYPE',
          event: eventType,
          deliveryId,
          timestamp: new Date(),
          message: `Received unsupported event type: ${eventType}`,
        });
    }
  }

  // イベントハンドラー（各イベント別処理）
  private async handlePushEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    const { repository, pusher, commits } = payload;
    
    this.logger.info('Processing push event', {
      deliveryId,
      repository: repository.full_name,
      pusher: pusher.name,
      commitCount: commits?.length || 0,
    });

    // セキュリティスキャン実行
    if (commits?.length > 0) {
      for (const commit of commits) {
        if (this.containsSensitiveData(commit)) {
          this.logger.logSecurityEvent({
            type: 'SENSITIVE_DATA_DETECTED',
            ip: clientIp,
            timestamp: new Date(),
            deliveryId,
            severity: 'critical',
            details: {
              repository: repository.full_name,
              pusher: pusher.name,
              commitSha: commit.id,
              commitMessage: commit.message,
            },
          });

          this.metrics.recordSensitiveDataDetection('commit_data', 'push', repository.full_name);
        }
      }
    }
  }

  private async handlePullRequestEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    const { action, pull_request, repository } = payload;
    
    this.logger.info('Processing pull request event', {
      deliveryId,
      action,
      repository: repository.full_name,
      prNumber: pull_request.number,
      prState: pull_request.state,
    });

    // セキュリティレビューが必要かチェック
    if (this.requiresSecurityReview(pull_request)) {
      await this.triggerSecurityReview(pull_request, deliveryId);
    }
  }

  private async handleSecretScanningEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    const { action, alert, repository } = payload;
    
    this.logger.logSecurityEvent({
      type: 'SENSITIVE_DATA_DETECTED',
      ip: clientIp,
      timestamp: new Date(),
      deliveryId,
      severity: 'critical',
      details: {
        action,
        repository: repository.full_name,
        secretType: alert.secret_type,
        alertNumber: alert.number,
      },
    });

    this.metrics.recordSensitiveDataDetection('secret_scanning', 'secret_scanning_alert', repository.full_name);
  }

  private async handleCodeScanningEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    const { action, alert, repository } = payload;
    
    this.logger.logSecurityEvent({
      type: 'SUSPICIOUS_ACTIVITY',
      ip: clientIp,
      timestamp: new Date(),
      deliveryId,
      severity: alert.rule.severity === 'error' ? 'high' : 'medium',
      details: {
        action,
        repository: repository.full_name,
        ruleId: alert.rule.id,
        severity: alert.rule.severity,
        alertNumber: alert.number,
      },
    });
  }

  private async handleDependabotEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    const { action, alert, repository } = payload;
    
    this.logger.logSecurityEvent({
      type: 'SUSPICIOUS_ACTIVITY',
      ip: clientIp,
      timestamp: new Date(),
      deliveryId,
      severity: alert.security_advisory.severity === 'critical' ? 'critical' : 'high',
      details: {
        action,
        repository: repository.full_name,
        vulnerability: alert.security_advisory.ghsa_id,
        severity: alert.security_advisory.severity,
        packageName: alert.dependency.package.name,
      },
    });
  }

  // 他のイベントハンドラー（簡略版）
  private async handleIssuesEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    this.logger.debug('Processing issues event', { deliveryId, action: payload.action });
  }

  private async handleRepositoryEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    this.logger.info('Processing repository event', { deliveryId, action: payload.action });
  }

  private async handleOrganizationEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    this.logger.info('Processing organization event', { deliveryId, action: payload.action });
  }

  private async handleMemberEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    this.logger.info('Processing member event', { deliveryId, action: payload.action });
  }

  private async handleTeamEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    this.logger.info('Processing team event', { deliveryId, action: payload.action });
  }

  private async handleInstallationEvent(payload: any, deliveryId: string, clientIp: string): Promise<void> {
    this.logger.info('Processing installation event', { deliveryId, action: payload.action });
  }

  // ユーティリティメソッド
  private containsSensitiveData(commit: any): boolean {
    const sensitivePatterns = [
      /password\s*[=:]\s*["'][^"']+["']/gi,
      /api[_-]?key\s*[=:]\s*["'][^"']+["']/gi,
      /secret\s*[=:]\s*["'][^"']+["']/gi,
      /token\s*[=:]\s*["'][^"']+["']/gi,
      /-----BEGIN [A-Z ]+PRIVATE KEY-----/gi,
    ];

    const message = commit.message || '';
    const modifiedFiles = [...(commit.added || []), ...(commit.modified || [])];
    
    return sensitivePatterns.some(pattern => 
      pattern.test(message) || 
      modifiedFiles.some(file => pattern.test(file))
    );
  }

  private requiresSecurityReview(pullRequest: any): boolean {
    const securityFiles = [
      '.github/workflows/',
      'Dockerfile',
      'docker-compose.yml',
      'package.json',
      'requirements.txt',
      'pom.xml',
      'build.gradle',
      '.env',
    ];

    // ファイルパスベースの判定は実際のPRデータが必要
    return pullRequest.title?.toLowerCase().includes('security') ||
           pullRequest.body?.toLowerCase().includes('security');
  }

  private async triggerSecurityReview(pullRequest: any, deliveryId: string): Promise<void> {
    this.logger.info('Security review triggered', {
      deliveryId,
      prNumber: pullRequest.number,
      title: pullRequest.title,
    });
    
    // 実際の実装では、セキュリティチームへの通知、ラベル追加等を実行
  }

  // API エンドポイントハンドラー
  private async handleHealthCheck(req: express.Request, res: express.Response): Promise<void> {
    try {
      const uptime = Math.floor((Date.now() - this.startTime.getTime()) / 1000);
      const memUsage = process.memoryUsage();
      const healthMetrics = this.metrics.getHealthMetrics();

      const health: HealthCheckResult = {
        status: healthMetrics.status,
        timestamp: new Date().toISOString(),
        version: process.env.npm_package_version || '1.0.0',
        service: 'github-webhook-security-server',
        uptime_seconds: uptime,
        dependencies: {
          database: 'healthy', // 実際の実装では実際のヘルスチェックを実行
          redis: 'healthy',
          elasticsearch: 'healthy',
        },
        checks: {
          memory_usage: memUsage.heapUsed < 1024 * 1024 * 1024, // 1GB未満
          disk_space: true, // 実際の実装ではディスク容量チェック
          network_connectivity: true, // 実際の実装ではネットワークチェック
          external_services: true, // 実際の実装では外部サービスチェック
        },
      };

      const statusCode = health.status === 'healthy' ? 200 : 503;
      res.status(statusCode).json(health);

    } catch (error) {
      this.logger.error('Health check failed', { error: error.message });
      res.status(503).json({
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: 'Health check failed',
      });
    }
  }

  private async handleReadinessCheck(req: express.Request, res: express.Response): Promise<void> {
    // Kubernetes Readiness Probe用
    res.status(200).json({ status: 'ready', timestamp: new Date().toISOString() });
  }

  private async handleMetrics(req: express.Request, res: express.Response): Promise<void> {
    try {
      const metrics = await this.metrics.getMetrics();
      res.set('Content-Type', 'text/plain; charset=utf-8');
      res.send(metrics);
    } catch (error) {
      this.logger.error('Failed to get metrics', { error: error.message });
      res.status(500).send('# Failed to retrieve metrics\n');
    }
  }

  private handleConfig(req: express.Request, res: express.Response): void {
    // 機密情報を除く設定情報を返す
    const safeConfig = {
      version: process.env.npm_package_version || '1.0.0',
      environment: this.config.environment,
      rate_limits: {
        global_per_minute: this.config.security.rate_limits.global_per_minute,
        per_ip_per_minute: this.config.security.rate_limits.per_ip_per_minute,
        per_hook_per_minute: this.config.security.rate_limits.per_hook_per_minute,
        per_repository_per_minute: this.config.security.rate_limits.per_repository_per_minute,
      },
      security: {
        allowed_events: ['push', 'pull_request', 'issues', 'repository', 'organization', 'member', 'team', 'installation'],
        max_payload_size_mb: this.config.security.max_payload_size_bytes / 1024 / 1024,
        signature_algorithm: this.config.security.signature_algorithm,
        ip_validation_strict: this.config.security.ip_validation_strict,
      },
      features: {
        metrics_enabled: this.config.enable_metrics,
        health_check_enabled: this.config.enable_health_check,
        cors_enabled: this.config.cors_enabled,
        compression_enabled: this.config.compression_enabled,
      },
    };

    res.json(safeConfig);
  }

  // エラーハンドリング設定
  private setupErrorHandling(): void {
    // 非同期エラーハンドラー
    this.app.use((error: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
      this.logger.logError({
        type: 'WEBHOOK_PROCESSING_ERROR',
        error: error.message,
        stack: error.stack,
        timestamp: new Date(),
        ip: req.ip,
      });

      if (error instanceof WebhookError) {
        res.status(error.statusCode).json({
          error: error.code,
          message: error.message,
          details: error.details,
          timestamp: new Date().toISOString(),
          request_id: req.id,
        });
      } else {
        res.status(500).json({
          error: 'INTERNAL_SERVER_ERROR',
          message: 'An unexpected error occurred',
          timestamp: new Date().toISOString(),
          request_id: req.id,
        });
      }
    });

    // Uncaught Exception Handler
    process.on('uncaughtException', (error) => {
      this.logger.error('Uncaught Exception', { error: error.message, stack: error.stack });
      this.gracefulShutdown('SIGTERM');
    });

    // Unhandled Rejection Handler
    process.on('unhandledRejection', (reason, promise) => {
      this.logger.error('Unhandled Rejection', { reason, promise });
      this.gracefulShutdown('SIGTERM');
    });
  }

  // Graceful Shutdown設定
  private setupGracefulShutdown(): void {
    const signals = ['SIGTERM', 'SIGINT', 'SIGUSR2'];
    
    signals.forEach(signal => {
      process.on(signal, () => {
        this.gracefulShutdown(signal);
      });
    });
  }

  private async gracefulShutdown(signal: string): Promise<void> {
    this.logger.info(`Received ${signal}, starting graceful shutdown...`);

    // 新しい接続を拒否
    if (this.server) {
      this.server.close(() => {
        this.logger.info('HTTP server closed');
      });
    }

    // タイムアウト設定（30秒後に強制終了）
    this.gracefulShutdownTimeout = setTimeout(() => {
      this.logger.error('Graceful shutdown timeout, forcing exit');
      process.exit(1);
    }, 30000);

    try {
      // アクティブな接続の完了を待つ
      while (this.activeConnections.size > 0) {
        this.logger.info(`Waiting for ${this.activeConnections.size} active connections to close...`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      // リソースのクリーンアップ
      await this.logger.close();
      this.metrics.cleanup();

      this.logger.info('Graceful shutdown completed');
      
      if (this.gracefulShutdownTimeout) {
        clearTimeout(this.gracefulShutdownTimeout);
      }
      
      process.exit(0);
    } catch (error) {
      this.logger.error('Error during graceful shutdown', { error: error.message });
      process.exit(1);
    }
  }

  // ヘルパーメソッド
  private generateRequestId(): string {
    return `req_${uuidv4().replace(/-/g, '')}`;
  }

  // サーバー開始
  public async start(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.server = this.app.listen(this.config.port, this.config.host, () => {
          this.logger.info(`GitHub Webhook Security Server started`, {
            port: this.config.port,
            host: this.config.host,
            environment: this.config.environment,
            processId: process.pid,
          });
          resolve();
        });

        this.server.on('error', (error: any) => {
          if (error.code === 'EADDRINUSE') {
            this.logger.error(`Port ${this.config.port} is already in use`);
          } else {
            this.logger.error('Server error', { error: error.message });
          }
          reject(error);
        });

      } catch (error) {
        this.logger.error('Failed to start server', { error: error.message });
        reject(error);
      }
    });
  }

  // サーバー停止
  public async stop(): Promise<void> {
    if (this.server) {
      return new Promise((resolve) => {
        this.server.close(() => {
          this.logger.info('Server stopped');
          resolve();
        });
      });
    }
  }
}

// Express リクエストオブジェクト拡張
declare global {
  namespace Express {
    interface Request {
      id?: string;
    }
  }
}

// アプリケーション起動
async function main() {
  try {
    const server = new GitHubWebhookSecurityServer();
    await server.start();
    
    console.log(`
🚀 GitHub Webhook Security Server Started Successfully!

📋 Configuration:
   Port: ${process.env.PORT || 3000}
   Environment: ${process.env.NODE_ENV || 'development'}
   Metrics Enabled: ${process.env.ENABLE_METRICS === 'true'}

🔗 Endpoints:
   POST /webhook/github - Webhook受信エンドポイント
   GET  /health        - ヘルスチェック
   GET  /metrics       - Prometheusメトリクス
   GET  /config        - 設定情報

🛡️ Security Features:
   ✅ HMAC-SHA256 Signature Verification
   ✅ IP Address Validation
   ✅ Rate Limiting
   ✅ Payload Sanitization
   ✅ Audit Logging
   ✅ Security Monitoring

⚡ Ready to receive GitHub webhooks securely!
    `);

  } catch (error) {
    console.error('❌ Failed to start server:', error.message);
    process.exit(1);
  }
}

// 直接実行時にサーバーを開始
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { GitHubWebhookSecurityServer };