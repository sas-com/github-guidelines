/**
 * Webhook Security Validator
 * エス・エー・エス株式会社 GitHub Webhook セキュリティ検証
 */

import crypto from 'crypto';
import { IPCidr } from 'ip-cidr';
import Joi from 'joi';
import {
  WebhookSecurityConfig,
  ValidationResult,
  SecurityCheckResult,
  WebhookPayload,
  WebhookEventType,
  WebhookHeaders,
  WebhookError,
  AuditLogEntry
} from '@/types/webhook.types.js';
import { Logger } from '@/logging/audit-logger.js';

export class WebhookSecurityValidator {
  private readonly config: WebhookSecurityConfig;
  private readonly logger: Logger;
  private readonly allowedIpRanges: IPCidr[];

  // GitHub公式IP範囲（定期的に更新が必要）
  private readonly githubIpRanges: string[] = [
    '140.82.112.0/20',
    '143.55.64.0/20',
    '185.199.108.0/22',
    '192.30.252.0/22',
    '20.201.28.151/32',
    '20.205.243.166/32',
    '20.248.137.48/32',
    '20.207.73.82/32',
    '20.27.177.113/32',
    '20.200.245.247/32',
    '20.233.54.53/32'
  ];

  // 機密データ検出パターン
  private readonly sensitivePatterns: RegExp[] = [
    // パスワード関連
    /password\s*[=:]\s*["']([^"']+)["']/gi,
    /passwd\s*[=:]\s*["']([^"']+)["']/gi,
    /pwd\s*[=:]\s*["']([^"']+)["']/gi,
    
    // API関連
    /api[_-]?key\s*[=:]\s*["']([^"']+)["']/gi,
    /apikey\s*[=:]\s*["']([^"']+)["']/gi,
    /api[_-]?secret\s*[=:]\s*["']([^"']+)["']/gi,
    
    // 認証トークン
    /access[_-]?token\s*[=:]\s*["']([^"']+)["']/gi,
    /auth[_-]?token\s*[=:]\s*["']([^"']+)["']/gi,
    /bearer\s+([a-zA-Z0-9\-_.]+)/gi,
    
    // データベース接続
    /database[_-]?url\s*[=:]\s*["']([^"']+)["']/gi,
    /connection[_-]?string\s*[=:]\s*["']([^"']+)["']/gi,
    /db[_-]?password\s*[=:]\s*["']([^"']+)["']/gi,
    
    // AWS関連
    /aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*["']([^"']+)["']/gi,
    /aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*["']([^"']+)["']/gi,
    /akia[0-9a-z]{16}/gi,
    
    // プライベートキー
    /-----BEGIN [A-Z ]+PRIVATE KEY-----/gi,
    /-----BEGIN OPENSSH PRIVATE KEY-----/gi,
    /-----BEGIN RSA PRIVATE KEY-----/gi,
    /-----BEGIN DSA PRIVATE KEY-----/gi,
    /-----BEGIN EC PRIVATE KEY-----/gi,
    
    // クレジットカード番号（基本的なパターン）
    /(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})/g,
    
    // 日本の個人情報
    /\d{3}-?\d{4}-?\d{4}/g, // 電話番号パターン
    /\d{7}-?\d{4}-?\d{4}-?\d{1}/g, // マイナンバーパターン（基本的な形式）
    
    // その他のシークレット
    /secret\s*[=:]\s*["']([^"']+)["']/gi,
    /private[_-]?key\s*[=:]\s*["']([^"']+)["']/gi,
    /encryption[_-]?key\s*[=:]\s*["']([^"']+)["']/gi
  ];

  // サポート対象イベント
  private readonly supportedEvents: WebhookEventType[] = [
    'push',
    'pull_request',
    'issues',
    'repository',
    'organization',
    'member',
    'team',
    'installation',
    'secret_scanning_alert',
    'code_scanning_alert',
    'dependabot_alert'
  ];

  constructor(config: WebhookSecurityConfig, logger: Logger) {
    this.config = config;
    this.logger = logger;
    
    // IP範囲を事前に解析
    const allIpRanges = [
      ...this.githubIpRanges,
      ...this.config.allowed_ips,
      ...this.config.custom_allowlist
    ];
    
    this.allowedIpRanges = allIpRanges.map(range => {
      try {
        return new IPCidr(range);
      } catch (error) {
        this.logger.warn(`Invalid IP range: ${range}`, { error: error.message });
        return null;
      }
    }).filter(Boolean) as IPCidr[];

    this.logger.info(`Initialized WebhookSecurityValidator with ${this.allowedIpRanges.length} IP ranges`);
  }

  /**
   * GitHub Webhook署名を検証
   */
  public verifySignature(payload: Buffer, signature: string): boolean {
    try {
      if (!signature || !signature.startsWith('sha256=')) {
        return false;
      }

      const expectedSignature = crypto
        .createHmac('sha256', this.config.webhook_secret)
        .update(payload)
        .digest('hex');

      const expected = `sha256=${expectedSignature}`;

      // タイミング攻撃を防ぐため定数時間比較を使用
      return crypto.timingSafeEqual(
        Buffer.from(signature),
        Buffer.from(expected)
      );
    } catch (error) {
      this.logger.error('Signature verification failed', {
        error: error.message,
        signatureLength: signature?.length || 0,
        hasSecret: !!this.config.webhook_secret
      });
      return false;
    }
  }

  /**
   * IPアドレスが許可範囲内かチェック
   */
  public verifyIpAddress(clientIp: string): boolean {
    try {
      // ローカル開発環境での特別処理
      if (!this.config.ip_validation_strict && 
          (clientIp === '127.0.0.1' || clientIp === '::1' || clientIp === 'localhost')) {
        this.logger.debug('Allowing local IP for development', { ip: clientIp });
        return true;
      }

      // IPv6のIPv4マッピング形式を正規化
      const normalizedIp = clientIp.replace(/^::ffff:/, '');

      for (const range of this.allowedIpRanges) {
        if (range.contains(normalizedIp)) {
          return true;
        }
      }

      this.logger.warn('IP address not in allowed ranges', {
        ip: normalizedIp,
        allowedRanges: this.allowedIpRanges.length
      });
      
      return false;
    } catch (error) {
      this.logger.error('IP verification failed', {
        error: error.message,
        ip: clientIp
      });
      return false;
    }
  }

  /**
   * 必須ヘッダーを検証
   */
  public validateHeaders(headers: Partial<WebhookHeaders>): ValidationResult {
    const errors: string[] = [];

    // 必須ヘッダーのチェック
    const requiredHeaders = [
      'x-github-delivery',
      'x-github-event',
      'x-hub-signature-256',
      'user-agent'
    ];

    for (const header of requiredHeaders) {
      if (!headers[header as keyof WebhookHeaders]) {
        errors.push(`Missing required header: ${header}`);
      }
    }

    // ヘッダー値の形式検証
    if (headers['x-github-delivery']) {
      const deliveryIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
      if (!deliveryIdPattern.test(headers['x-github-delivery'])) {
        errors.push('Invalid x-github-delivery format (must be UUID)');
      }
    }

    if (headers['x-github-event']) {
      if (!this.supportedEvents.includes(headers['x-github-event'])) {
        errors.push(`Unsupported event type: ${headers['x-github-event']}`);
      }
    }

    if (headers['x-hub-signature-256']) {
      const signaturePattern = /^sha256=[a-f0-9]{64}$/;
      if (!signaturePattern.test(headers['x-hub-signature-256'])) {
        errors.push('Invalid x-hub-signature-256 format');
      }
    }

    if (headers['user-agent']) {
      const userAgentPattern = /^GitHub-Hookshot\/[a-f0-9]+$/;
      if (!userAgentPattern.test(headers['user-agent'])) {
        errors.push('Invalid user-agent format (must be GitHub-Hookshot/*)');
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * ペイロードを検証・サニタイズ
   */
  public async validatePayload(payload: unknown, eventType: WebhookEventType): Promise<ValidationResult> {
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // 基本的なJSON構造検証
      if (!payload || typeof payload !== 'object') {
        errors.push('Invalid payload: must be a valid JSON object');
        return { isValid: false, errors, warnings };
      }

      // ペイロードサイズチェック（バイト数は事前に確認済み）
      const payloadStr = JSON.stringify(payload);
      if (payloadStr.length > 1024 * 1024) { // 1MB
        warnings.push('Large payload detected');
      }

      // イベント別バリデーション
      const validationSchema = this.getValidationSchema(eventType);
      if (validationSchema) {
        const { error } = validationSchema.validate(payload, {
          allowUnknown: true, // GitHubは新しいフィールドを追加する可能性があるため
          stripUnknown: false
        });

        if (error) {
          errors.push(...error.details.map(detail => detail.message));
        }
      }

      // 機密データ検出
      const sensitiveDataFound = this.detectSensitiveData(payloadStr);
      if (sensitiveDataFound.length > 0) {
        warnings.push(`Sensitive data patterns detected: ${sensitiveDataFound.join(', ')}`);
        
        // 機密データが検出された場合はセキュリティログに記録
        this.logger.warn('Sensitive data detected in webhook payload', {
          eventType,
          patterns: sensitiveDataFound,
          payloadSize: payloadStr.length
        });
      }

    } catch (error) {
      errors.push(`Payload validation error: ${error.message}`);
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * 包括的セキュリティチェック
   */
  public async performSecurityCheck(
    clientIp: string,
    headers: Partial<WebhookHeaders>,
    payload: Buffer,
    eventType: WebhookEventType
  ): Promise<SecurityCheckResult> {
    const checks = {
      signature_valid: false,
      ip_allowed: false,
      rate_limit_ok: true, // Rate limitはミドルウェアでチェック済みと仮定
      payload_size_ok: false,
      headers_valid: false,
      sensitive_data_detected: false
    };

    let threatLevel: 'low' | 'medium' | 'high' | 'critical' = 'low';
    const actionsTaken: string[] = [];

    try {
      // 署名検証
      if (headers['x-hub-signature-256']) {
        checks.signature_valid = this.verifySignature(payload, headers['x-hub-signature-256']);
        if (!checks.signature_valid) {
          threatLevel = 'high';
          actionsTaken.push('signature_verification_failed');
        }
      }

      // IP制限チェック
      checks.ip_allowed = this.verifyIpAddress(clientIp);
      if (!checks.ip_allowed) {
        threatLevel = 'critical';
        actionsTaken.push('ip_blocked');
      }

      // ペイロードサイズチェック
      checks.payload_size_ok = payload.length <= this.config.max_payload_size_bytes;
      if (!checks.payload_size_ok) {
        threatLevel = Math.max(threatLevel === 'low' ? 'medium' : threatLevel, 'medium') as any;
        actionsTaken.push('payload_too_large');
      }

      // ヘッダー検証
      const headerValidation = this.validateHeaders(headers);
      checks.headers_valid = headerValidation.isValid;
      if (!checks.headers_valid) {
        threatLevel = Math.max(threatLevel === 'low' ? 'medium' : threatLevel, 'medium') as any;
        actionsTaken.push('invalid_headers');
      }

      // 機密データ検出
      if (payload.length < 1024 * 1024) { // 1MB以下のペイロードのみスキャン
        const payloadStr = payload.toString('utf8');
        const sensitivePatterns = this.detectSensitiveData(payloadStr);
        checks.sensitive_data_detected = sensitivePatterns.length > 0;
        
        if (checks.sensitive_data_detected) {
          threatLevel = 'critical';
          actionsTaken.push('sensitive_data_detected');
        }
      }

      // 脅威レベルの最終評価
      if (!checks.signature_valid || !checks.ip_allowed) {
        threatLevel = 'critical';
      } else if (checks.sensitive_data_detected) {
        threatLevel = 'critical';
      } else if (!checks.headers_valid || !checks.payload_size_ok) {
        threatLevel = 'medium';
      }

    } catch (error) {
      threatLevel = 'high';
      actionsTaken.push('security_check_error');
      this.logger.error('Security check failed', {
        error: error.message,
        clientIp,
        eventType
      });
    }

    const passed = Object.values(checks).every(check => check === true || check === false && !checks.sensitive_data_detected);

    return {
      passed,
      checks,
      threatLevel,
      actionsTaken
    };
  }

  /**
   * 機密データパターンを検出
   */
  private detectSensitiveData(content: string): string[] {
    const foundPatterns: string[] = [];

    for (let i = 0; i < this.sensitivePatterns.length; i++) {
      const pattern = this.sensitivePatterns[i];
      if (pattern.test(content)) {
        foundPatterns.push(`pattern_${i + 1}`);
      }
      // Reset regex lastIndex to ensure consistent results
      pattern.lastIndex = 0;
    }

    return foundPatterns;
  }

  /**
   * イベント別バリデーションスキーマを取得
   */
  private getValidationSchema(eventType: WebhookEventType): Joi.ObjectSchema | null {
    const baseRepositorySchema = Joi.object({
      id: Joi.number().required(),
      name: Joi.string().required(),
      full_name: Joi.string().required(),
      private: Joi.boolean().required(),
      html_url: Joi.string().uri().required(),
      description: Joi.string().allow(null),
      default_branch: Joi.string().required()
    }).unknown(true);

    const baseUserSchema = Joi.object({
      id: Joi.number().required(),
      login: Joi.string().required(),
      avatar_url: Joi.string().uri().required(),
      html_url: Joi.string().uri().required(),
      type: Joi.string().valid('User', 'Bot', 'Organization').required()
    }).unknown(true);

    switch (eventType) {
      case 'push':
        return Joi.object({
          ref: Joi.string().required(),
          before: Joi.string().pattern(/^[a-f0-9]{40}$/).required(),
          after: Joi.string().pattern(/^[a-f0-9]{40}$/).required(),
          commits: Joi.array().items(Joi.object({
            id: Joi.string().pattern(/^[a-f0-9]{40}$/).required(),
            message: Joi.string().required(),
            timestamp: Joi.string().isoDate().required(),
            author: Joi.object({
              name: Joi.string().required(),
              email: Joi.string().email().required()
            }).required(),
            added: Joi.array().items(Joi.string()),
            removed: Joi.array().items(Joi.string()),
            modified: Joi.array().items(Joi.string())
          }).unknown(true)).required(),
          repository: baseRepositorySchema.required(),
          pusher: Joi.object({
            name: Joi.string().required(),
            email: Joi.string().email().required()
          }).required(),
          sender: baseUserSchema.required()
        }).unknown(true);

      case 'pull_request':
        return Joi.object({
          action: Joi.string().valid(
            'assigned', 'auto_merge_disabled', 'auto_merge_enabled', 'closed',
            'converted_to_draft', 'demilestoned', 'dequeued', 'edited',
            'labeled', 'locked', 'milestoned', 'opened', 'queued',
            'ready_for_review', 'reopened', 'review_request_removed',
            'review_requested', 'synchronize', 'unassigned', 'unlabeled', 'unlocked'
          ).required(),
          number: Joi.number().required(),
          pull_request: Joi.object({
            id: Joi.number().required(),
            number: Joi.number().required(),
            state: Joi.string().valid('open', 'closed').required(),
            title: Joi.string().required(),
            body: Joi.string().allow(null),
            user: baseUserSchema.required(),
            head: Joi.object({
              ref: Joi.string().required(),
              sha: Joi.string().pattern(/^[a-f0-9]{40}$/).required(),
              repo: baseRepositorySchema.allow(null)
            }).unknown(true).required(),
            base: Joi.object({
              ref: Joi.string().required(),
              sha: Joi.string().pattern(/^[a-f0-9]{40}$/).required(),
              repo: baseRepositorySchema.required()
            }).unknown(true).required()
          }).unknown(true).required(),
          repository: baseRepositorySchema.required(),
          sender: baseUserSchema.required()
        }).unknown(true);

      case 'issues':
        return Joi.object({
          action: Joi.string().valid(
            'assigned', 'closed', 'deleted', 'demilestoned', 'edited',
            'labeled', 'locked', 'milestoned', 'opened', 'pinned',
            'reopened', 'transferred', 'unassigned', 'unlabeled',
            'unlocked', 'unpinned'
          ).required(),
          issue: Joi.object({
            id: Joi.number().required(),
            number: Joi.number().required(),
            title: Joi.string().required(),
            body: Joi.string().allow(null),
            user: baseUserSchema.required(),
            state: Joi.string().valid('open', 'closed').required()
          }).unknown(true).required(),
          repository: baseRepositorySchema.required(),
          sender: baseUserSchema.required()
        }).unknown(true);

      case 'repository':
        return Joi.object({
          action: Joi.string().valid(
            'archived', 'created', 'deleted', 'edited', 'privatized',
            'publicized', 'renamed', 'transferred', 'unarchived'
          ).required(),
          repository: baseRepositorySchema.required(),
          sender: baseUserSchema.required()
        }).unknown(true);

      case 'secret_scanning_alert':
        return Joi.object({
          action: Joi.string().valid('created', 'reopened', 'resolved', 'revoked').required(),
          alert: Joi.object({
            number: Joi.number().required(),
            secret_type: Joi.string().required(),
            secret_type_display_name: Joi.string().required(),
            secret: Joi.string().required(),
            resolution: Joi.string().valid('false_positive', 'wont_fix', 'revoked', 'used_in_tests').allow(null)
          }).unknown(true).required(),
          repository: baseRepositorySchema.required(),
          sender: baseUserSchema.required()
        }).unknown(true);

      case 'code_scanning_alert':
        return Joi.object({
          action: Joi.string().valid(
            'appeared_in_branch', 'closed_by_user', 'created', 'fixed', 'reopened', 'reopened_by_user'
          ).required(),
          alert: Joi.object({
            number: Joi.number().required(),
            state: Joi.string().valid('open', 'dismissed', 'fixed').required(),
            rule: Joi.object({
              id: Joi.string().required(),
              severity: Joi.string().valid('error', 'warning', 'note').required(),
              description: Joi.string().required()
            }).unknown(true).required(),
            tool: Joi.object({
              name: Joi.string().required()
            }).unknown(true).required()
          }).unknown(true).required(),
          repository: baseRepositorySchema.required(),
          sender: baseUserSchema.required()
        }).unknown(true);

      case 'dependabot_alert':
        return Joi.object({
          action: Joi.string().valid('created', 'dismissed', 'fixed', 'reintroduced', 'reopened').required(),
          alert: Joi.object({
            number: Joi.number().required(),
            state: Joi.string().valid('auto_dismissed', 'dismissed', 'fixed', 'open').required(),
            dependency: Joi.object({
              package: Joi.object({
                ecosystem: Joi.string().required(),
                name: Joi.string().required()
              }).required()
            }).unknown(true).required(),
            security_advisory: Joi.object({
              ghsa_id: Joi.string().required(),
              summary: Joi.string().required(),
              description: Joi.string().required(),
              severity: Joi.string().valid('low', 'moderate', 'high', 'critical').required()
            }).unknown(true).required()
          }).unknown(true).required(),
          repository: baseRepositorySchema.required(),
          sender: baseUserSchema.required()
        }).unknown(true);

      default:
        // 基本的な構造のみ検証
        return Joi.object({
          repository: baseRepositorySchema,
          sender: baseUserSchema.required()
        }).unknown(true);
    }
  }

  /**
   * ペイロードをサニタイズ
   */
  public sanitizePayload(payload: WebhookPayload): WebhookPayload {
    try {
      // Deep clone to avoid modifying original
      const sanitized = JSON.parse(JSON.stringify(payload));
      
      // 再帰的にサニタイズ
      return this.sanitizeObject(sanitized);
    } catch (error) {
      this.logger.error('Payload sanitization failed', { error: error.message });
      return payload; // サニタイズに失敗した場合は元のペイロードを返す
    }
  }

  /**
   * オブジェクトを再帰的にサニタイズ
   */
  private sanitizeObject(obj: any): any {
    if (obj === null || obj === undefined) {
      return obj;
    }

    if (typeof obj === 'string') {
      return this.sanitizeString(obj);
    }

    if (Array.isArray(obj)) {
      return obj.map(item => this.sanitizeObject(item));
    }

    if (typeof obj === 'object') {
      const sanitized: any = {};
      for (const [key, value] of Object.entries(obj)) {
        sanitized[key] = this.sanitizeObject(value);
      }
      return sanitized;
    }

    return obj;
  }

  /**
   * 文字列をサニタイズ
   */
  private sanitizeString(str: string): string {
    if (typeof str !== 'string') return str;

    return str
      // HTML tags removal (basic)
      .replace(/<script[^>]*>.*?<\/script>/gi, '')
      .replace(/<[^>]*>/g, '')
      // JavaScript event handlers
      .replace(/on\w+\s*=\s*"[^"]*"/gi, '')
      .replace(/on\w+\s*=\s*'[^']*'/gi, '')
      // JavaScript: protocol
      .replace(/javascript:/gi, '')
      // SQL injection basic patterns
      .replace(/(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)/gi, '')
      // Control characters (except newline, carriage return, tab)
      .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '')
      // Null bytes
      .replace(/\x00/g, '')
      // Excessive whitespace
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * カスタムエラーを作成
   */
  public createWebhookError(
    code: string,
    message: string,
    statusCode: number,
    details?: string,
    deliveryId?: string
  ): WebhookError {
    const error = new Error(message) as WebhookError;
    error.code = code;
    error.statusCode = statusCode;
    error.details = details;
    error.deliveryId = deliveryId;
    error.correlationId = crypto.randomBytes(16).toString('hex');
    return error;
  }
}