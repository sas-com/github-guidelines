// GitHub Webhook Security Server - Go/Gin Implementation
// エス・エー・エス株式会社 GitHub Webhook セキュリティサーバー

package main

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"regexp"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-contrib/gzip"
	"github.com/gin-contrib/secure"
	"github.com/gin-gonic/gin"
	"github.com/go-playground/validator/v10"
	"github.com/google/uuid"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/sirupsen/logrus"
	"github.com/ulule/limiter/v3"
	"github.com/ulule/limiter/v3/drivers/middleware/gin"
	"github.com/ulule/limiter/v3/drivers/store/memory"
	"golang.org/x/time/rate"
)

// ===========================
// Configuration Structures
// ===========================

// Config アプリケーション設定
type Config struct {
	Server   ServerConfig   `json:"server"`
	Security SecurityConfig `json:"security"`
	Logging  LoggingConfig  `json:"logging"`
	Metrics  MetricsConfig  `json:"metrics"`
}

// ServerConfig サーバー設定
type ServerConfig struct {
	Host               string        `json:"host" env:"HOST" envDefault:"0.0.0.0"`
	Port               int           `json:"port" env:"PORT" envDefault:"8080"`
	Environment        string        `json:"environment" env:"ENVIRONMENT" envDefault:"development"`
	ReadTimeout        time.Duration `json:"read_timeout" env:"READ_TIMEOUT" envDefault:"30s"`
	WriteTimeout       time.Duration `json:"write_timeout" env:"WRITE_TIMEOUT" envDefault:"30s"`
	IdleTimeout        time.Duration `json:"idle_timeout" env:"IDLE_TIMEOUT" envDefault:"60s"`
	ShutdownTimeout    time.Duration `json:"shutdown_timeout" env:"SHUTDOWN_TIMEOUT" envDefault:"30s"`
	MaxHeaderSize      int           `json:"max_header_size" env:"MAX_HEADER_SIZE" envDefault:"1048576"`
	EnableCORS         bool          `json:"enable_cors" env:"ENABLE_CORS" envDefault:"false"`
	EnableCompression  bool          `json:"enable_compression" env:"ENABLE_COMPRESSION" envDefault:"true"`
	EnableHealthCheck  bool          `json:"enable_health_check" env:"ENABLE_HEALTH_CHECK" envDefault:"true"`
	EnableMetrics      bool          `json:"enable_metrics" env:"ENABLE_METRICS" envDefault:"true"`
}

// SecurityConfig セキュリティ設定
type SecurityConfig struct {
	WebhookSecret         string   `json:"-" env:"WEBHOOK_SECRET" validate:"required"`
	AllowedIPs            []string `json:"allowed_ips" env:"ALLOWED_IPS" envSeparator:","`
	RateLimitGlobal       int      `json:"rate_limit_global" env:"RATE_LIMIT_GLOBAL" envDefault:"1000"`
	RateLimitPerIP        int      `json:"rate_limit_per_ip" env:"RATE_LIMIT_PER_IP" envDefault:"60"`
	RateLimitPerHook      int      `json:"rate_limit_per_hook" env:"RATE_LIMIT_PER_HOOK" envDefault:"120"`
	RateLimitPerRepo      int      `json:"rate_limit_per_repo" env:"RATE_LIMIT_PER_REPO" envDefault:"100"`
	MaxPayloadSizeMB      int      `json:"max_payload_size_mb" env:"MAX_PAYLOAD_SIZE_MB" envDefault:"10"`
	IPValidationStrict    bool     `json:"ip_validation_strict" env:"IP_VALIDATION_STRICT" envDefault:"true"`
	GeoRestrictions       []string `json:"geo_restrictions" env:"GEO_RESTRICTIONS" envSeparator:"," envDefault:"JP,US"`
	EnableSignatureVerify bool     `json:"enable_signature_verify" env:"ENABLE_SIGNATURE_VERIFY" envDefault:"true"`
}

// LoggingConfig ログ設定
type LoggingConfig struct {
	Level  string `json:"level" env:"LOG_LEVEL" envDefault:"info"`
	Format string `json:"format" env:"LOG_FORMAT" envDefault:"json"`
	Output string `json:"output" env:"LOG_OUTPUT" envDefault:"stdout"`
}

// MetricsConfig メトリクス設定
type MetricsConfig struct {
	Enabled   bool   `json:"enabled" env:"METRICS_ENABLED" envDefault:"true"`
	Namespace string `json:"namespace" env:"METRICS_NAMESPACE" envDefault:"github_webhook"`
	Subsystem string `json:"subsystem" env:"METRICS_SUBSYSTEM" envDefault:"security_server"`
}

// ===========================
// GitHub Webhook Models
// ===========================

// GitHubRepository GitHub リポジトリ
type GitHubRepository struct {
	ID          int    `json:"id" validate:"required"`
	Name        string `json:"name" validate:"required"`
	FullName    string `json:"full_name" validate:"required"`
	Private     bool   `json:"private"`
	HTMLURL     string `json:"html_url" validate:"required,url"`
	Description string `json:"description"`
}

// GitHubUser GitHub ユーザー
type GitHubUser struct {
	ID        int    `json:"id" validate:"required"`
	Login     string `json:"login" validate:"required"`
	AvatarURL string `json:"avatar_url" validate:"required,url"`
	HTMLURL   string `json:"html_url" validate:"required,url"`
	Type      string `json:"type" validate:"required"`
}

// GitHubCommit GitHub コミット
type GitHubCommit struct {
	ID        string                 `json:"id" validate:"required"`
	Message   string                 `json:"message" validate:"required"`
	Timestamp time.Time              `json:"timestamp" validate:"required"`
	Author    map[string]interface{} `json:"author" validate:"required"`
	Added     []string               `json:"added"`
	Removed   []string               `json:"removed"`
	Modified  []string               `json:"modified"`
}

// PushEventPayload Push イベント ペイロード
type PushEventPayload struct {
	Ref        string           `json:"ref" validate:"required"`
	Before     string           `json:"before" validate:"required"`
	After      string           `json:"after" validate:"required"`
	Commits    []GitHubCommit   `json:"commits" validate:"required"`
	Repository GitHubRepository `json:"repository" validate:"required"`
	Pusher     GitHubUser       `json:"pusher" validate:"required"`
	Sender     GitHubUser       `json:"sender" validate:"required"`
}

// WebhookRequest Webhook リクエスト
type WebhookRequest struct {
	Headers   map[string]string      `json:"headers"`
	Body      map[string]interface{} `json:"body"`
	RawBody   []byte                 `json:"-"`
	ClientIP  string                 `json:"client_ip"`
	EventType string                 `json:"event_type"`
}

// WebhookResponse Webhook レスポンス
type WebhookResponse struct {
	Status           string                 `json:"status"`
	DeliveryID       string                 `json:"delivery_id"`
	EventType        string                 `json:"event_type,omitempty"`
	ProcessingTimeMs int64                  `json:"processing_time_ms,omitempty"`
	Timestamp        time.Time              `json:"timestamp"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
}

// ErrorResponse エラー レスポンス
type ErrorResponse struct {
	Error     string    `json:"error"`
	Message   string    `json:"message"`
	Details   string    `json:"details,omitempty"`
	Timestamp time.Time `json:"timestamp"`
	RequestID string    `json:"request_id"`
}

// HealthCheckResponse ヘルスチェック レスポンス
type HealthCheckResponse struct {
	Status        string            `json:"status"`
	Timestamp     time.Time         `json:"timestamp"`
	Version       string            `json:"version"`
	Service       string            `json:"service"`
	UptimeSeconds int64             `json:"uptime_seconds"`
	Dependencies  map[string]string `json:"dependencies,omitempty"`
}

// ===========================
// Security Validator
// ===========================

// WebhookSecurityValidator セキュリティ検証
type WebhookSecurityValidator struct {
	config           SecurityConfig
	logger           *logrus.Logger
	allowedNetworks  []*net.IPNet
	sensitivePatterns []*regexp.Regexp
}

// NewWebhookSecurityValidator 新しいセキュリティバリデーターを作成
func NewWebhookSecurityValidator(config SecurityConfig, logger *logrus.Logger) *WebhookSecurityValidator {
	validator := &WebhookSecurityValidator{
		config: config,
		logger: logger,
	}

	// GitHubの公式IP範囲
	githubIPRanges := []string{
		"140.82.112.0/20",
		"143.55.64.0/20",
		"185.199.108.0/22",
		"192.30.252.0/22",
		"20.201.28.151/32",
		"20.205.243.166/32",
	}

	// 許可IP範囲を解析
	allIPRanges := append(githubIPRanges, config.AllowedIPs...)
	for _, ipRange := range allIPRanges {
		_, network, err := net.ParseCIDR(ipRange)
		if err != nil {
			logger.WithField("ip_range", ipRange).Warn("Invalid IP range")
			continue
		}
		validator.allowedNetworks = append(validator.allowedNetworks, network)
	}

	// 機密データ検出パターン
	patterns := []string{
		`(?i)password\s*[=:]\s*["']([^"']+)["']`,
		`(?i)api[_-]?key\s*[=:]\s*["']([^"']+)["']`,
		`(?i)secret\s*[=:]\s*["']([^"']+)["']`,
		`(?i)token\s*[=:]\s*["']([^"']+)["']`,
		`(?i)-----BEGIN [A-Z ]+PRIVATE KEY-----`,
		`(?i)akia[0-9a-z]{16}`,
		`\d{3}-?\d{4}-?\d{4}`,
	}

	for _, pattern := range patterns {
		regex, err := regexp.Compile(pattern)
		if err != nil {
			logger.WithField("pattern", pattern).Warn("Invalid regex pattern")
			continue
		}
		validator.sensitivePatterns = append(validator.sensitivePatterns, regex)
	}

	return validator
}

// VerifySignature GitHub Webhook署名検証
func (v *WebhookSecurityValidator) VerifySignature(payload []byte, signature string) bool {
	if !strings.HasPrefix(signature, "sha256=") {
		return false
	}

	mac := hmac.New(sha256.New, []byte(v.config.WebhookSecret))
	mac.Write(payload)
	expectedSignature := "sha256=" + hex.EncodeToString(mac.Sum(nil))

	return hmac.Equal([]byte(signature), []byte(expectedSignature))
}

// VerifyIPAddress IP制限検証
func (v *WebhookSecurityValidator) VerifyIPAddress(clientIP string) bool {
	// 開発環境での特別処理
	if !v.config.IPValidationStrict && (clientIP == "127.0.0.1" || clientIP == "::1") {
		return true
	}

	ip := net.ParseIP(clientIP)
	if ip == nil {
		v.logger.WithField("ip", clientIP).Error("Invalid IP address")
		return false
	}

	for _, network := range v.allowedNetworks {
		if network.Contains(ip) {
			return true
		}
	}

	return false
}

// ValidateHeaders 必須ヘッダー検証
func (v *WebhookSecurityValidator) ValidateHeaders(headers map[string]string) error {
	requiredHeaders := []string{
		"X-Github-Delivery",
		"X-Github-Event",
		"X-Hub-Signature-256",
		"User-Agent",
	}

	for _, header := range requiredHeaders {
		if _, exists := headers[header]; !exists {
			return fmt.Errorf("missing required header: %s", header)
		}
	}

	// ヘッダー形式検証
	deliveryID := headers["X-Github-Delivery"]
	if matched, _ := regexp.MatchString(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`, deliveryID); !matched {
		return fmt.Errorf("invalid X-Github-Delivery format")
	}

	signature := headers["X-Hub-Signature-256"]
	if matched, _ := regexp.MatchString(`^sha256=[a-f0-9]{64}$`, signature); !matched {
		return fmt.Errorf("invalid X-Hub-Signature-256 format")
	}

	userAgent := headers["User-Agent"]
	if matched, _ := regexp.MatchString(`^GitHub-Hookshot/[a-f0-9]+$`, userAgent); !matched {
		return fmt.Errorf("invalid User-Agent format")
	}

	return nil
}

// DetectSensitiveData 機密データ検出
func (v *WebhookSecurityValidator) DetectSensitiveData(content string) []string {
	var detectedPatterns []string

	for i, pattern := range v.sensitivePatterns {
		if pattern.MatchString(content) {
			detectedPatterns = append(detectedPatterns, fmt.Sprintf("pattern_%d", i+1))
		}
	}

	return detectedPatterns
}

// SanitizePayload ペイロードサニタイゼーション
func (v *WebhookSecurityValidator) SanitizePayload(payload map[string]interface{}) map[string]interface{} {
	sanitized := make(map[string]interface{})

	for key, value := range payload {
		switch v := value.(type) {
		case string:
			sanitized[key] = v.sanitizeString(v)
		case map[string]interface{}:
			sanitized[key] = v.SanitizePayload(v)
		case []interface{}:
			sanitized[key] = v.sanitizeArray(v)
		default:
			sanitized[key] = value
		}
	}

	return sanitized
}

func (v *WebhookSecurityValidator) sanitizeString(input string) string {
	// 基本的なサニタイゼーション
	sanitized := input
	sanitized = regexp.MustCompile(`(?i)<script[^>]*>.*?</script>`).ReplaceAllString(sanitized, "")
	sanitized = regexp.MustCompile(`<[^>]*>`).ReplaceAllString(sanitized, "")
	sanitized = regexp.MustCompile(`(?i)javascript:`).ReplaceAllString(sanitized, "")
	sanitized = regexp.MustCompile(`[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]`).ReplaceAllString(sanitized, "")
	return strings.TrimSpace(sanitized)
}

func (v *WebhookSecurityValidator) sanitizeArray(input []interface{}) []interface{} {
	sanitized := make([]interface{}, len(input))
	for i, item := range input {
		switch v := item.(type) {
		case string:
			sanitized[i] = v.sanitizeString(v)
		case map[string]interface{}:
			sanitized[i] = v.SanitizePayload(v)
		case []interface{}:
			sanitized[i] = v.sanitizeArray(v)
		default:
			sanitized[i] = item
		}
	}
	return sanitized
}

// ===========================
// Metrics
// ===========================

var (
	webhookRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "github_webhook_requests_total",
			Help: "Total number of GitHub webhook requests",
		},
		[]string{"event_type", "status", "repository"},
	)

	webhookErrorsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "github_webhook_errors_total",
			Help: "Total number of GitHub webhook errors",
		},
		[]string{"error_type", "event_type"},
	)

	webhookProcessingDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name: "github_webhook_processing_duration_seconds",
			Help: "GitHub webhook processing duration in seconds",
			Buckets: prometheus.ExponentialBuckets(0.01, 2, 10),
		},
		[]string{"event_type", "status"},
	)

	webhookSecurityEventsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "github_webhook_security_events_total",
			Help: "Total number of security events detected",
		},
		[]string{"event_type", "severity"},
	)

	activeConnections = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "github_webhook_active_connections",
			Help: "Number of active webhook connections",
		},
	)
)

// ===========================
// Application
// ===========================

// Application メインアプリケーション
type Application struct {
	config    Config
	logger    *logrus.Logger
	validator *WebhookSecurityValidator
	server    *http.Server
	startTime time.Time
}

// NewApplication 新しいアプリケーションを作成
func NewApplication(config Config) *Application {
	// ログ設定
	logger := logrus.New()
	level, _ := logrus.ParseLevel(config.Logging.Level)
	logger.SetLevel(level)

	if config.Logging.Format == "json" {
		logger.SetFormatter(&logrus.JSONFormatter{})
	}

	// セキュリティバリデーター作成
	validator := NewWebhookSecurityValidator(config.Security, logger)

	return &Application{
		config:    config,
		logger:    logger,
		validator: validator,
		startTime: time.Now(),
	}
}

// setupRouter ルーター設定
func (app *Application) setupRouter() *gin.Engine {
	// Ginのモード設定
	if app.config.Server.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()

	// ミドルウェア設定
	router.Use(gin.Logger())
	router.Use(gin.Recovery())

	// セキュリティヘッダー
	router.Use(secure.New(secure.Config{
		SSLRedirect:          false,
		STSSeconds:           31536000,
		STSIncludeSubdomains: true,
		FrameDeny:            true,
		ContentTypeNosniff:   true,
		BrowserXssFilter:     true,
		ReferrerPolicy:       "strict-origin-when-cross-origin",
	}))

	// 圧縮
	if app.config.Server.EnableCompression {
		router.Use(gzip.Gzip(gzip.DefaultCompression))
	}

	// CORS
	if app.config.Server.EnableCORS {
		corsConfig := cors.DefaultConfig()
		corsConfig.AllowOrigins = []string{"https://*.sas-com.com"}
		if app.config.Server.Environment == "development" {
			corsConfig.AllowAllOrigins = true
		}
		corsConfig.AllowMethods = []string{"GET", "POST"}
		corsConfig.AllowHeaders = []string{
			"Content-Type",
			"X-GitHub-Delivery",
			"X-GitHub-Event",
			"X-Hub-Signature-256",
			"User-Agent",
		}
		router.Use(cors.New(corsConfig))
	}

	// Rate Limiting - Global
	globalLimiter := limiter.New(
		memory.NewStore(),
		limiter.Rate{
			Period: time.Minute,
			Limit:  int64(app.config.Security.RateLimitGlobal),
		},
	)
	router.Use(gin.NewGinMiddleware(globalLimiter))

	// Rate Limiting - Per IP
	ipLimiter := limiter.New(
		memory.NewStore(),
		limiter.Rate{
			Period: time.Minute,
			Limit:  int64(app.config.Security.RateLimitPerIP),
		},
	)
	router.Use(gin.NewGinMiddleware(ipLimiter))

	// カスタムミドルウェア
	router.Use(app.requestIDMiddleware())
	router.Use(app.metricsMiddleware())
	router.Use(app.securityMiddleware())

	// ルート設定
	app.setupRoutes(router)

	return router
}

// setupRoutes ルート設定
func (app *Application) setupRoutes(router *gin.Engine) {
	// ヘルスチェック
	if app.config.Server.EnableHealthCheck {
		router.GET("/health", app.healthCheckHandler)
		router.GET("/healthz", app.healthCheckHandler) // Kubernetes用
		router.GET("/ready", app.readinessCheckHandler)
	}

	// メトリクス
	if app.config.Server.EnableMetrics {
		router.GET("/metrics", gin.WrapH(promhttp.Handler()))
	}

	// 設定情報
	router.GET("/config", app.configHandler)

	// Webhook受信エンドポイント
	router.POST("/webhook/github", app.webhookHandler)
}

// ===========================
// Middleware
// ===========================

// requestIDMiddleware リクエストID ミドルウェア
func (app *Application) requestIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := uuid.New().String()
		c.Header("X-Request-ID", requestID)
		c.Set("request_id", requestID)
		c.Next()
	}
}

// metricsMiddleware メトリクス ミドルウェア
func (app *Application) metricsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// アクティブ接続数を増加
		activeConnections.Inc()
		defer activeConnections.Dec()

		c.Next()
	}
}

// securityMiddleware セキュリティ ミドルウェア
func (app *Application) securityMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// セキュリティヘッダーを追加
		c.Header("X-Content-Type-Options", "nosniff")
		c.Header("X-Frame-Options", "DENY")
		c.Header("X-XSS-Protection", "1; mode=block")
		c.Header("Referrer-Policy", "strict-origin-when-cross-origin")

		c.Next()
	}
}

// ===========================
// Handlers
// ===========================

// webhookHandler Webhook ハンドラー
func (app *Application) webhookHandler(c *gin.Context) {
	startTime := time.Now()
	requestID, _ := c.Get("request_id")

	// ヘッダー取得
	headers := make(map[string]string)
	for key, values := range c.Request.Header {
		if len(values) > 0 {
			headers[key] = values[0]
		}
	}

	deliveryID := c.GetHeader("X-GitHub-Delivery")
	eventType := c.GetHeader("X-GitHub-Event")
	signature := c.GetHeader("X-Hub-Signature-256")
	clientIP := c.ClientIP()

	// ログフィールド設定
	logger := app.logger.WithFields(logrus.Fields{
		"request_id":  requestID,
		"delivery_id": deliveryID,
		"event_type":  eventType,
		"client_ip":   clientIP,
	})

	// 基本検証
	if deliveryID == "" || eventType == "" || signature == "" {
		logger.Error("Missing required headers")
		webhookErrorsTotal.WithLabelValues("missing_headers", eventType).Inc()
		c.JSON(http.StatusBadRequest, ErrorResponse{
			Error:     "MISSING_HEADERS",
			Message:   "Required headers are missing",
			Timestamp: time.Now(),
			RequestID: requestID.(string),
		})
		return
	}

	// ペイロード読み取り
	rawBody, err := io.ReadAll(c.Request.Body)
	if err != nil {
		logger.WithError(err).Error("Failed to read request body")
		webhookErrorsTotal.WithLabelValues("read_body_error", eventType).Inc()
		c.JSON(http.StatusBadRequest, ErrorResponse{
			Error:     "INVALID_PAYLOAD",
			Message:   "Failed to read request body",
			Timestamp: time.Now(),
			RequestID: requestID.(string),
		})
		return
	}

	// ペイロードサイズチェック
	maxSize := app.config.Security.MaxPayloadSizeMB * 1024 * 1024
	if len(rawBody) > maxSize {
		logger.Errorf("Payload size exceeded: %d bytes", len(rawBody))
		webhookErrorsTotal.WithLabelValues("payload_too_large", eventType).Inc()
		c.JSON(http.StatusRequestEntityTooLarge, ErrorResponse{
			Error:     "PAYLOAD_TOO_LARGE",
			Message:   fmt.Sprintf("Payload size exceeded %dMB limit", app.config.Security.MaxPayloadSizeMB),
			Timestamp: time.Now(),
			RequestID: requestID.(string),
		})
		return
	}

	// ヘッダー検証
	if err := app.validator.ValidateHeaders(headers); err != nil {
		logger.WithError(err).Error("Header validation failed")
		webhookErrorsTotal.WithLabelValues("invalid_headers", eventType).Inc()
		c.JSON(http.StatusBadRequest, ErrorResponse{
			Error:     "INVALID_HEADERS",
			Message:   "Header validation failed",
			Details:   err.Error(),
			Timestamp: time.Now(),
			RequestID: requestID.(string),
		})
		return
	}

	// 署名検証
	if app.config.Security.EnableSignatureVerify && !app.validator.VerifySignature(rawBody, signature) {
		logger.Error("Signature verification failed")
		webhookSecurityEventsTotal.WithLabelValues("signature_verification_failed", "high").Inc()
		webhookErrorsTotal.WithLabelValues("invalid_signature", eventType).Inc()
		c.JSON(http.StatusUnauthorized, ErrorResponse{
			Error:     "INVALID_SIGNATURE",
			Message:   "Webhook signature verification failed",
			Timestamp: time.Now(),
			RequestID: requestID.(string),
		})
		return
	}

	// IP制限チェック
	if !app.validator.VerifyIPAddress(clientIP) {
		logger.Error("Unauthorized IP access")
		webhookSecurityEventsTotal.WithLabelValues("unauthorized_ip", "critical").Inc()
		webhookErrorsTotal.WithLabelValues("forbidden_ip", eventType).Inc()
		c.JSON(http.StatusForbidden, ErrorResponse{
			Error:     "FORBIDDEN_IP",
			Message:   "Access denied: IP not allowed",
			Timestamp: time.Now(),
			RequestID: requestID.(string),
		})
		return
	}

	// JSON解析
	var payload map[string]interface{}
	if err := json.Unmarshal(rawBody, &payload); err != nil {
		logger.WithError(err).Error("JSON parsing failed")
		webhookErrorsTotal.WithLabelValues("json_parse_error", eventType).Inc()
		c.JSON(http.StatusBadRequest, ErrorResponse{
			Error:     "INVALID_PAYLOAD",
			Message:   "Invalid JSON payload",
			Details:   err.Error(),
			Timestamp: time.Now(),
			RequestID: requestID.(string),
		})
		return
	}

	// 機密データ検出
	sensitivePatterns := app.validator.DetectSensitiveData(string(rawBody))
	if len(sensitivePatterns) > 0 {
		logger.WithField("patterns", sensitivePatterns).Warn("Sensitive data detected")
		webhookSecurityEventsTotal.WithLabelValues("sensitive_data_detected", "critical").Inc()
	}

	// ペイロードサニタイゼーション
	sanitizedPayload := app.validator.SanitizePayload(payload)

	// イベント処理
	if err := app.processWebhookEvent(eventType, sanitizedPayload, deliveryID, clientIP); err != nil {
		logger.WithError(err).Error("Event processing failed")
		webhookErrorsTotal.WithLabelValues("processing_error", eventType).Inc()
		c.JSON(http.StatusInternalServerError, ErrorResponse{
			Error:     "PROCESSING_ERROR",
			Message:   "Event processing failed",
			Details:   err.Error(),
			Timestamp: time.Now(),
			RequestID: requestID.(string),
		})
		return
	}

	// 処理時間計算
	processingTime := time.Since(startTime)
	processingTimeMs := processingTime.Milliseconds()

	// メトリクス更新
	webhookRequestsTotal.WithLabelValues(eventType, "success", getRepositoryName(sanitizedPayload)).Inc()
	webhookProcessingDuration.WithLabelValues(eventType, "success").Observe(processingTime.Seconds())

	// 成功ログ
	logger.WithFields(logrus.Fields{
		"processing_time_ms":      processingTimeMs,
		"payload_size":            len(rawBody),
		"sensitive_data_detected": len(sensitivePatterns) > 0,
	}).Info("Webhook processed successfully")

	// レスポンス
	response := WebhookResponse{
		Status:           "success",
		DeliveryID:       deliveryID,
		EventType:        eventType,
		ProcessingTimeMs: processingTimeMs,
		Timestamp:        time.Now(),
		Metadata: map[string]interface{}{
			"repository":               getRepositoryName(sanitizedPayload),
			"sender":                   getSenderName(sanitizedPayload),
			"security_checks_passed":   true,
			"sensitive_data_detected":  len(sensitivePatterns) > 0,
		},
	}

	c.JSON(http.StatusOK, response)
}

// processWebhookEvent Webhookイベント処理
func (app *Application) processWebhookEvent(eventType string, payload map[string]interface{}, deliveryID, clientIP string) error {
	logger := app.logger.WithFields(logrus.Fields{
		"event_type":  eventType,
		"delivery_id": deliveryID,
		"client_ip":   clientIP,
	})

	switch eventType {
	case "push":
		return app.handlePushEvent(payload, deliveryID, logger)
	case "pull_request":
		return app.handlePullRequestEvent(payload, deliveryID, logger)
	case "secret_scanning_alert":
		return app.handleSecretScanningEvent(payload, deliveryID, logger)
	case "code_scanning_alert":
		return app.handleCodeScanningEvent(payload, deliveryID, logger)
	case "dependabot_alert":
		return app.handleDependabotEvent(payload, deliveryID, logger)
	default:
		logger.Info("Unhandled event type")
	}

	return nil
}

// handlePushEvent Pushイベント処理
func (app *Application) handlePushEvent(payload map[string]interface{}, deliveryID string, logger *logrus.Entry) error {
	repository := getRepositoryName(payload)
	commits, ok := payload["commits"].([]interface{})
	if !ok {
		commits = []interface{}{}
	}

	logger.WithFields(logrus.Fields{
		"repository":   repository,
		"commit_count": len(commits),
	}).Info("Processing push event")

	// コミット内の機密データチェック
	for _, commit := range commits {
		commitMap, ok := commit.(map[string]interface{})
		if !ok {
			continue
		}

		if app.containsSensitiveData(commitMap) {
			logger.WithFields(logrus.Fields{
				"commit_id": commitMap["id"],
				"message":   commitMap["message"],
			}).Critical("Sensitive data detected in commit")
		}
	}

	return nil
}

// handlePullRequestEvent Pull Requestイベント処理
func (app *Application) handlePullRequestEvent(payload map[string]interface{}, deliveryID string, logger *logrus.Entry) error {
	action, _ := payload["action"].(string)
	repository := getRepositoryName(payload)

	logger.WithFields(logrus.Fields{
		"action":     action,
		"repository": repository,
	}).Info("Processing pull request event")

	return nil
}

// handleSecretScanningEvent Secret Scanningイベント処理
func (app *Application) handleSecretScanningEvent(payload map[string]interface{}, deliveryID string, logger *logrus.Entry) error {
	repository := getRepositoryName(payload)
	alert, _ := payload["alert"].(map[string]interface{})

	logger.WithFields(logrus.Fields{
		"repository":    repository,
		"alert_number":  alert["number"],
		"secret_type":   alert["secret_type"],
	}).Critical("Secret scanning alert received")

	return nil
}

// handleCodeScanningEvent Code Scanningイベント処理
func (app *Application) handleCodeScanningEvent(payload map[string]interface{}, deliveryID string, logger *logrus.Entry) error {
	repository := getRepositoryName(payload)
	alert, _ := payload["alert"].(map[string]interface{})

	logger.WithFields(logrus.Fields{
		"repository":   repository,
		"alert_number": alert["number"],
		"rule_id":      getNestedValue(alert, "rule.id"),
		"severity":     getNestedValue(alert, "rule.severity"),
	}).Warning("Code scanning alert received")

	return nil
}

// handleDependabotEvent Dependabotイベント処理
func (app *Application) handleDependabotEvent(payload map[string]interface{}, deliveryID string, logger *logrus.Entry) error {
	repository := getRepositoryName(payload)
	alert, _ := payload["alert"].(map[string]interface{})

	logger.WithFields(logrus.Fields{
		"repository":     repository,
		"alert_number":   alert["number"],
		"vulnerability":  getNestedValue(alert, "security_advisory.ghsa_id"),
		"severity":       getNestedValue(alert, "security_advisory.severity"),
	}).Warning("Dependabot alert received")

	return nil
}

// healthCheckHandler ヘルスチェック ハンドラー
func (app *Application) healthCheckHandler(c *gin.Context) {
	uptime := int64(time.Since(app.startTime).Seconds())

	response := HealthCheckResponse{
		Status:        "healthy",
		Timestamp:     time.Now(),
		Version:       "1.0.0",
		Service:       "GitHub Webhook Security Server",
		UptimeSeconds: uptime,
		Dependencies: map[string]string{
			"memory": "healthy",
			"disk":   "healthy",
		},
	}

	c.JSON(http.StatusOK, response)
}

// readinessCheckHandler Readinessチェック ハンドラー
func (app *Application) readinessCheckHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "ready",
		"timestamp": time.Now(),
	})
}

// configHandler 設定情報 ハンドラー
func (app *Application) configHandler(c *gin.Context) {
	config := map[string]interface{}{
		"version":     "1.0.0",
		"environment": app.config.Server.Environment,
		"rate_limits": map[string]int{
			"global":         app.config.Security.RateLimitGlobal,
			"per_ip":         app.config.Security.RateLimitPerIP,
			"per_hook":       app.config.Security.RateLimitPerHook,
			"per_repository": app.config.Security.RateLimitPerRepo,
		},
		"security": map[string]interface{}{
			"max_payload_size_mb":   app.config.Security.MaxPayloadSizeMB,
			"ip_validation_strict":  app.config.Security.IPValidationStrict,
			"signature_verification": app.config.Security.EnableSignatureVerify,
		},
		"features": map[string]bool{
			"metrics_enabled":      app.config.Server.EnableMetrics,
			"health_check_enabled": app.config.Server.EnableHealthCheck,
			"cors_enabled":         app.config.Server.EnableCORS,
			"compression_enabled":  app.config.Server.EnableCompression,
		},
	}

	c.JSON(http.StatusOK, config)
}

// ===========================
// Helper Functions
// ===========================

// containsSensitiveData コミット内機密データ検出
func (app *Application) containsSensitiveData(commit map[string]interface{}) bool {
	message, _ := commit["message"].(string)
	added, _ := commit["added"].([]interface{})
	modified, _ := commit["modified"].([]interface{})

	sensitiveKeywords := []string{
		"password", "secret", "key", "token", "credential",
		"aws_access_key", "api_key", "private_key",
	}

	// コミットメッセージチェック
	messageLower := strings.ToLower(message)
	for _, keyword := range sensitiveKeywords {
		if strings.Contains(messageLower, keyword) {
			return true
		}
	}

	// ファイル名チェック
	sensitiveFiles := []string{".env", "credentials", "secrets", "private_key"}
	allFiles := append(interfaceSliceToStringSlice(added), interfaceSliceToStringSlice(modified)...)

	for _, file := range allFiles {
		fileLower := strings.ToLower(file)
		for _, sensitive := range sensitiveFiles {
			if strings.Contains(fileLower, sensitive) {
				return true
			}
		}
	}

	return false
}

// getRepositoryName リポジトリ名取得
func getRepositoryName(payload map[string]interface{}) string {
	if repo, ok := payload["repository"].(map[string]interface{}); ok {
		if name, ok := repo["full_name"].(string); ok {
			return name
		}
	}
	return "unknown"
}

// getSenderName 送信者名取得
func getSenderName(payload map[string]interface{}) string {
	if sender, ok := payload["sender"].(map[string]interface{}); ok {
		if login, ok := sender["login"].(string); ok {
			return login
		}
	}
	return "unknown"
}

// getNestedValue ネストされた値取得
func getNestedValue(data map[string]interface{}, path string) interface{} {
	keys := strings.Split(path, ".")
	current := data

	for _, key := range keys {
		if value, ok := current[key]; ok {
			if nextMap, ok := value.(map[string]interface{}); ok {
				current = nextMap
			} else {
				return value
			}
		} else {
			return nil
		}
	}

	return current
}

// interfaceSliceToStringSlice interface{}[]をstring[]に変換
func interfaceSliceToStringSlice(input []interface{}) []string {
	output := make([]string, len(input))
	for i, v := range input {
		if str, ok := v.(string); ok {
			output[i] = str
		}
	}
	return output
}

// ===========================
// Server Management
// ===========================

// Start サーバー開始
func (app *Application) Start() error {
	router := app.setupRouter()

	app.server = &http.Server{
		Addr:           fmt.Sprintf("%s:%d", app.config.Server.Host, app.config.Server.Port),
		Handler:        router,
		ReadTimeout:    app.config.Server.ReadTimeout,
		WriteTimeout:   app.config.Server.WriteTimeout,
		IdleTimeout:    app.config.Server.IdleTimeout,
		MaxHeaderBytes: app.config.Server.MaxHeaderSize,
	}

	app.logger.WithFields(logrus.Fields{
		"host":        app.config.Server.Host,
		"port":        app.config.Server.Port,
		"environment": app.config.Server.Environment,
	}).Info("Starting GitHub Webhook Security Server")

	return app.server.ListenAndServe()
}

// Stop サーバー停止
func (app *Application) Stop() error {
	ctx, cancel := context.WithTimeout(context.Background(), app.config.Server.ShutdownTimeout)
	defer cancel()

	app.logger.Info("Shutting down server gracefully...")
	return app.server.Shutdown(ctx)
}

// ===========================
// Main Function
// ===========================

func main() {
	// 設定読み込み
	config := Config{
		Server: ServerConfig{
			Host:               getEnvString("HOST", "0.0.0.0"),
			Port:               getEnvInt("PORT", 8080),
			Environment:        getEnvString("ENVIRONMENT", "development"),
			ReadTimeout:        getEnvDuration("READ_TIMEOUT", 30*time.Second),
			WriteTimeout:       getEnvDuration("WRITE_TIMEOUT", 30*time.Second),
			IdleTimeout:        getEnvDuration("IDLE_TIMEOUT", 60*time.Second),
			ShutdownTimeout:    getEnvDuration("SHUTDOWN_TIMEOUT", 30*time.Second),
			MaxHeaderSize:      getEnvInt("MAX_HEADER_SIZE", 1048576),
			EnableCORS:         getEnvBool("ENABLE_CORS", false),
			EnableCompression:  getEnvBool("ENABLE_COMPRESSION", true),
			EnableHealthCheck:  getEnvBool("ENABLE_HEALTH_CHECK", true),
			EnableMetrics:      getEnvBool("ENABLE_METRICS", true),
		},
		Security: SecurityConfig{
			WebhookSecret:         getEnvString("WEBHOOK_SECRET", ""),
			AllowedIPs:            getEnvStringSlice("ALLOWED_IPS", []string{}),
			RateLimitGlobal:       getEnvInt("RATE_LIMIT_GLOBAL", 1000),
			RateLimitPerIP:        getEnvInt("RATE_LIMIT_PER_IP", 60),
			RateLimitPerHook:      getEnvInt("RATE_LIMIT_PER_HOOK", 120),
			RateLimitPerRepo:      getEnvInt("RATE_LIMIT_PER_REPO", 100),
			MaxPayloadSizeMB:      getEnvInt("MAX_PAYLOAD_SIZE_MB", 10),
			IPValidationStrict:    getEnvBool("IP_VALIDATION_STRICT", true),
			GeoRestrictions:       getEnvStringSlice("GEO_RESTRICTIONS", []string{"JP", "US"}),
			EnableSignatureVerify: getEnvBool("ENABLE_SIGNATURE_VERIFY", true),
		},
		Logging: LoggingConfig{
			Level:  getEnvString("LOG_LEVEL", "info"),
			Format: getEnvString("LOG_FORMAT", "json"),
			Output: getEnvString("LOG_OUTPUT", "stdout"),
		},
		Metrics: MetricsConfig{
			Enabled:   getEnvBool("METRICS_ENABLED", true),
			Namespace: getEnvString("METRICS_NAMESPACE", "github_webhook"),
			Subsystem: getEnvString("METRICS_SUBSYSTEM", "security_server"),
		},
	}

	// Webhook秘密鍵の検証
	if config.Security.WebhookSecret == "" {
		log.Fatal("WEBHOOK_SECRET environment variable is required")
	}

	// アプリケーション作成
	app := NewApplication(config)

	// グレースフルシャットダウンの設定
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-quit
		app.logger.Info("Received shutdown signal")
		if err := app.Stop(); err != nil {
			app.logger.WithError(err).Error("Failed to shutdown server gracefully")
		}
	}()

	// サーバー開始
	if err := app.Start(); err != nil && err != http.ErrServerClosed {
		app.logger.WithError(err).Fatal("Failed to start server")
	}

	app.logger.Info("Server stopped")
}

// ===========================
// Environment Helpers
// ===========================

func getEnvString(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if parsed, err := strconv.Atoi(value); err == nil {
			return parsed
		}
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if parsed, err := strconv.ParseBool(value); err == nil {
			return parsed
		}
	}
	return defaultValue
}

func getEnvDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if parsed, err := time.ParseDuration(value); err == nil {
			return parsed
		}
	}
	return defaultValue
}

func getEnvStringSlice(key string, defaultValue []string) []string {
	if value := os.Getenv(key); value != "" {
		return strings.Split(value, ",")
	}
	return defaultValue
}