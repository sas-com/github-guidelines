module github.com/sas-com/github-webhook-security-server

go 1.21

require (
	github.com/gin-gonic/gin v1.9.1
	github.com/prometheus/client_golang v1.17.0
	github.com/sirupsen/logrus v1.9.3
	github.com/stretchr/testify v1.8.4
	github.com/go-playground/validator/v10 v10.16.0
	golang.org/x/time v0.5.0
	gopkg.in/yaml.v3 v3.0.1
)

require (
	// Core HTTP framework
	github.com/gin-contrib/cors v1.5.0
	github.com/gin-contrib/gzip v0.0.6
	github.com/gin-contrib/secure v0.0.1
	github.com/gin-contrib/timeout v0.0.3
	
	// Rate limiting & middleware
	github.com/ulule/limiter/v3 v3.11.2
	github.com/gin-contrib/sessions v0.0.5
	
	// Security & crypto
	golang.org/x/crypto v0.16.0
	github.com/google/uuid v1.4.0
	
	// JSON processing
	github.com/json-iterator/go v1.1.12
	github.com/tidwall/gjson v1.17.0
	
	// Network & IP utilities
	github.com/asaskevich/govalidator v0.0.0-20230301143203-a9d515a09cc2
	
	// Configuration
	github.com/joho/godotenv v1.4.0
	github.com/spf13/viper v1.17.0
	github.com/kelseyhightower/envconfig v1.4.0
	
	// Database & caching
	github.com/go-redis/redis/v8 v8.11.5
	github.com/lib/pq v1.10.9
	github.com/jmoiron/sqlx v1.3.5
	
	// Logging & monitoring
	github.com/prometheus/client_golang v1.17.0
	github.com/elastic/go-elasticsearch/v8 v8.11.0
	go.uber.org/zap v1.26.0
	go.uber.org/zap/zapcore v1.26.0
	
	// Testing
	github.com/stretchr/testify v1.8.4
	github.com/golang/mock v1.6.0
	github.com/gavv/httpexpect/v2 v2.16.0
	
	// HTTP client
	github.com/go-resty/resty/v2 v2.10.0
	
	// Date/time utilities
	github.com/jinzhu/now v1.1.5
	
	// Validation
	github.com/go-playground/validator/v10 v10.16.0
	github.com/go-playground/universal-translator v0.18.1
	
	// Context & cancellation
	golang.org/x/context v0.0.0-20230301143203-a9d515a09cc2
	golang.org/x/sync v0.5.0
	
	// OS signal handling
	golang.org/x/sys v0.15.0
	
	// Performance & profiling
	github.com/pkg/profile v1.7.0
	
	// Utilities
	github.com/mitchellh/mapstructure v1.5.0
	github.com/fatih/color v1.16.0
)

require (
	// Indirect dependencies (managed automatically)
	github.com/beorn7/perks v1.0.1 // indirect
	github.com/bytedance/sonic v1.9.1 // indirect
	github.com/cespare/xxhash/v2 v2.2.0 // indirect
	github.com/chenzhuoyu/base64x v0.0.0-20221115062448-fe3a3abad311 // indirect
	github.com/davecgh/go-spew v1.1.2-0.20180830191138-d8f796af33cc // indirect
	github.com/gabriel-vasile/mimetype v1.4.2 // indirect
	github.com/gin-contrib/sse v0.1.0 // indirect
	github.com/go-playground/locales v0.14.1 // indirect
	github.com/go-playground/universal-translator v0.18.1 // indirect
	github.com/goccy/go-json v0.10.2 // indirect
	github.com/golang/protobuf v1.5.3 // indirect
	github.com/klauspost/cpuid/v2 v2.2.4 // indirect
	github.com/leodido/go-urn v1.2.4 // indirect
	github.com/mattn/go-isatty v0.0.19 // indirect
	github.com/matttproud/golang_protobuf_extensions v1.0.4 // indirect
	github.com/modern-go/concurrent v0.0.0-20180306012644-bacd9c7ef1dd // indirect
	github.com/modern-go/reflect2 v1.0.2 // indirect
	github.com/pelletier/go-toml/v2 v2.0.8 // indirect
	github.com/pmezard/go-difflib v1.0.1-0.20181226105442-5d4384ee4fb2 // indirect
	github.com/prometheus/client_model v0.4.1-0.20230718164431-9a2bf3000d16 // indirect
	github.com/prometheus/common v0.44.0 // indirect
	github.com/prometheus/procfs v0.11.1 // indirect
	github.com/twitchyliquid64/golang-asm v0.15.1 // indirect
	github.com/ugorji/go/codec v1.2.11 // indirect
	golang.org/x/arch v0.3.0 // indirect
	golang.org/x/net v0.19.0 // indirect
	golang.org/x/text v0.14.0 // indirect
	google.golang.org/protobuf v1.31.0 // indirect
)

// Replace directives for development (if needed)
// replace github.com/gin-gonic/gin => ../gin