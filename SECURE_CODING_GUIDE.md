# セキュアコーディングガイド

**エス・エー・エス株式会社**  
*最終更新日: 2025年9月10日*  
*バージョン: 1.0.0*

## 📚 概要

本ガイドは、エス・エー・エス株式会社の開発者向けセキュアコーディング実践ガイドです。
OWASP、CERT、SANSなどの業界標準に基づき、実践的なセキュリティ実装方法を提供します。

## 🎯 基本原則

### セキュアコーディングの7原則

1. **最小権限の原則** - 必要最小限の権限のみを付与
2. **深層防御** - 多層的なセキュリティ対策を実装
3. **フェイルセキュア** - エラー時も安全な状態を維持
4. **ゼロトラスト** - すべての入力を信頼しない
5. **セキュリティバイデザイン** - 設計段階からセキュリティを組み込む
6. **最小攻撃面** - 攻撃可能な領域を最小化
7. **監査とログ** - すべての重要な操作を記録

---

## 🔐 言語別セキュアコーディング

### JavaScript/TypeScript

#### 入力検証とサニタイゼーション

```typescript
// ❌ 悪い例：入力をそのまま使用
const searchUser = (query: string) => {
  const sql = `SELECT * FROM users WHERE name = '${query}'`;
  return db.execute(sql);
};

// ✅ 良い例：パラメータ化クエリを使用
const searchUser = async (query: string) => {
  // 入力検証
  if (!isValidInput(query)) {
    throw new ValidationError('Invalid input');
  }
  
  // パラメータ化クエリ
  const sql = 'SELECT * FROM users WHERE name = ?';
  return await db.execute(sql, [query]);
};

// 入力検証関数
const isValidInput = (input: string): boolean => {
  // ホワイトリスト検証
  const allowedPattern = /^[a-zA-Z0-9\s\-_.@]+$/;
  const maxLength = 100;
  
  return input.length <= maxLength && allowedPattern.test(input);
};
```

#### XSS対策

```typescript
// ❌ 悪い例：HTMLを直接挿入
const displayUserContent = (content: string) => {
  document.getElementById('output').innerHTML = content;
};

// ✅ 良い例：適切なエスケープとサニタイゼーション
import DOMPurify from 'dompurify';

const displayUserContent = (content: string) => {
  // テキストコンテンツとして挿入
  document.getElementById('output').textContent = content;
  
  // HTMLが必要な場合はDOMPurifyでサニタイズ
  const cleanHTML = DOMPurify.sanitize(content, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a'],
    ALLOWED_ATTR: ['href']
  });
  document.getElementById('output').innerHTML = cleanHTML;
};

// React/Next.jsでの安全な実装
const SafeComponent: React.FC<{content: string}> = ({ content }) => {
  // dangerouslySetInnerHTMLは極力避ける
  return <div>{content}</div>; // 自動的にエスケープされる
};
```

#### 認証・セッション管理

```typescript
// セキュアなセッション設定
import session from 'express-session';
import crypto from 'crypto';

app.use(session({
  secret: process.env.SESSION_SECRET || crypto.randomBytes(64).toString('hex'),
  name: 'sessionId', // デフォルト名を変更
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: true, // HTTPS必須
    httpOnly: true, // XSS対策
    sameSite: 'strict', // CSRF対策
    maxAge: 15 * 60 * 1000, // 15分
    domain: '.example.com',
    path: '/'
  },
  rolling: true, // アクティビティでセッション延長
  genid: () => crypto.randomBytes(32).toString('hex')
}));

// JWTの安全な実装
import jwt from 'jsonwebtoken';

const generateToken = (userId: string): string => {
  return jwt.sign(
    { 
      userId,
      iat: Math.floor(Date.now() / 1000),
      jti: crypto.randomBytes(16).toString('hex') // JWT ID for revocation
    },
    process.env.JWT_SECRET!,
    { 
      expiresIn: '1h',
      algorithm: 'RS256', // 非対称暗号を推奨
      issuer: 'https://api.example.com',
      audience: 'https://app.example.com'
    }
  );
};

// トークン検証
const verifyToken = (token: string): any => {
  try {
    return jwt.verify(token, process.env.JWT_PUBLIC_KEY!, {
      algorithms: ['RS256'],
      issuer: 'https://api.example.com',
      audience: 'https://app.example.com',
      clockTolerance: 30 // 30秒の時刻ずれを許容
    });
  } catch (error) {
    logger.warn('Invalid token attempt', { error });
    throw new UnauthorizedError('Invalid token');
  }
};
```

### Python

#### SQLインジェクション対策

```python
import psycopg2
from psycopg2 import sql
import secrets
import hashlib
import hmac

# ❌ 悪い例：文字列結合でSQL構築
def bad_get_user(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()

# ✅ 良い例：パラメータ化クエリ
def secure_get_user(username):
    # 入力検証
    if not validate_username(username):
        raise ValueError("Invalid username format")
    
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    return cursor.fetchone()

def validate_username(username):
    """ユーザー名の検証"""
    import re
    pattern = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
    return pattern.match(username) is not None

# ORMを使用した安全な実装（SQLAlchemy）
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def orm_get_user(session, username):
    # SQLAlchemyは自動的にエスケープ
    user = session.query(User).filter(
        User.username == username
    ).first()
    return user

# 動的クエリが必要な場合
def dynamic_query(table_name, column_name):
    # テーブル名とカラム名をホワイトリスト検証
    allowed_tables = ['users', 'products', 'orders']
    allowed_columns = ['id', 'name', 'created_at']
    
    if table_name not in allowed_tables:
        raise ValueError("Invalid table name")
    if column_name not in allowed_columns:
        raise ValueError("Invalid column name")
    
    # sql.Identifierで安全にエスケープ
    query = sql.SQL("SELECT {} FROM {}").format(
        sql.Identifier(column_name),
        sql.Identifier(table_name)
    )
    cursor.execute(query)
```

#### パスワード管理

```python
import bcrypt
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

class SecurePasswordManager:
    def __init__(self):
        # Argon2を推奨（bcryptも可）
        self.ph = PasswordHasher(
            time_cost=2,      # イテレーション回数
            memory_cost=65536, # メモリ使用量(KB)
            parallelism=1,     # 並列度
            hash_len=32,       # ハッシュ長
            salt_len=16        # ソルト長
        )
    
    def hash_password(self, password: str) -> str:
        """パスワードのハッシュ化"""
        # パスワード強度チェック
        if not self.check_password_strength(password):
            raise ValueError("Password does not meet requirements")
        
        # Argon2でハッシュ化
        return self.ph.hash(password)
    
    def verify_password(self, password: str, hash: str) -> bool:
        """パスワード検証"""
        try:
            self.ph.verify(hash, password)
            # 必要に応じてリハッシュ
            if self.ph.check_needs_rehash(hash):
                return True, self.ph.hash(password)
            return True, None
        except VerifyMismatchError:
            # タイミング攻撃対策で固定時間待機
            import time
            time.sleep(secrets.randbelow(100) / 1000)
            return False, None
    
    def check_password_strength(self, password: str) -> bool:
        """パスワード強度チェック"""
        import re
        
        # 最小12文字
        if len(password) < 12:
            return False
        
        # 大文字、小文字、数字、特殊文字を含む
        patterns = [
            r'[A-Z]',  # 大文字
            r'[a-z]',  # 小文字
            r'[0-9]',  # 数字
            r'[!@#$%^&*(),.?":{}|<>]'  # 特殊文字
        ]
        
        return all(re.search(pattern, password) for pattern in patterns)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """セキュアなトークン生成"""
        return secrets.token_urlsafe(length)
```

#### ファイルアップロード処理

```python
import os
import magic
import hashlib
from werkzeug.utils import secure_filename
from PIL import Image
import io

class SecureFileUploader:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = '/secure/uploads/'
    
    def validate_and_save_file(self, file_stream, filename):
        """ファイルの検証と保存"""
        
        # 1. ファイル名のサニタイゼーション
        safe_filename = secure_filename(filename)
        if not safe_filename:
            raise ValueError("Invalid filename")
        
        # 2. 拡張子チェック
        ext = self._get_extension(safe_filename)
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {ext} not allowed")
        
        # 3. ファイルサイズチェック
        file_content = file_stream.read(self.MAX_FILE_SIZE + 1)
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValueError("File too large")
        
        # 4. MIMEタイプ検証（マジックナンバー）
        mime_type = magic.from_buffer(file_content, mime=True)
        if not self._validate_mime_type(mime_type, ext):
            raise ValueError("File content does not match extension")
        
        # 5. 画像の場合は追加検証
        if ext in {'png', 'jpg', 'jpeg', 'gif'}:
            self._validate_image(file_content)
        
        # 6. ウイルススキャン（ClamAV等）
        if not self._scan_for_malware(file_content):
            raise ValueError("Malware detected")
        
        # 7. ユニークなファイル名生成
        unique_filename = self._generate_unique_filename(ext)
        
        # 8. 安全な場所に保存
        file_path = os.path.join(self.UPLOAD_FOLDER, unique_filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 9. ファイル権限設定
        os.chmod(file_path, 0o644)
        
        return unique_filename
    
    def _validate_image(self, file_content):
        """画像ファイルの検証"""
        try:
            img = Image.open(io.BytesIO(file_content))
            img.verify()  # 画像の整合性チェック
            
            # 画像サイズ制限
            if img.width > 4000 or img.height > 4000:
                raise ValueError("Image dimensions too large")
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")
    
    def _generate_unique_filename(self, extension):
        """ユニークなファイル名生成"""
        import uuid
        return f"{uuid.uuid4().hex}.{extension}"
```

### Java

#### セキュアな入力処理

```java
import org.owasp.encoder.Encode;
import org.apache.commons.validator.routines.EmailValidator;
import java.util.regex.Pattern;
import javax.validation.constraints.*;

public class SecureInputHandler {
    
    // 入力検証用のパターン
    private static final Pattern ALPHANUMERIC = Pattern.compile("^[a-zA-Z0-9]+$");
    private static final Pattern USERNAME = Pattern.compile("^[a-zA-Z0-9_-]{3,20}$");
    private static final int MAX_INPUT_LENGTH = 1000;
    
    /**
     * SQLインジェクション対策 - PreparedStatement使用
     */
    public User getUserById(Long userId) {
        String sql = "SELECT * FROM users WHERE id = ?";
        
        try (Connection conn = dataSource.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            
            ps.setLong(1, userId);
            
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    return mapResultSetToUser(rs);
                }
            }
        } catch (SQLException e) {
            logger.error("Database error", e);
            throw new DataAccessException("Failed to fetch user");
        }
        return null;
    }
    
    /**
     * XSS対策 - 出力エンコーディング
     */
    public String renderUserContent(String userInput) {
        // 入力検証
        if (userInput == null || userInput.length() > MAX_INPUT_LENGTH) {
            throw new ValidationException("Invalid input");
        }
        
        // HTMLコンテキストでエンコード
        String htmlEncoded = Encode.forHtml(userInput);
        
        // JavaScriptコンテキストでエンコード
        String jsEncoded = Encode.forJavaScript(userInput);
        
        // URLコンテキストでエンコード
        String urlEncoded = Encode.forUriComponent(userInput);
        
        return htmlEncoded;
    }
    
    /**
     * Bean Validationを使用した入力検証
     */
    public class UserRegistrationDto {
        @NotNull(message = "Username is required")
        @Size(min = 3, max = 20)
        @Pattern(regexp = "^[a-zA-Z0-9_-]+$")
        private String username;
        
        @NotNull(message = "Email is required")
        @Email(message = "Invalid email format")
        private String email;
        
        @NotNull(message = "Password is required")
        @Size(min = 12, message = "Password must be at least 12 characters")
        @Pattern(regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]+$",
                message = "Password must contain uppercase, lowercase, number and special character")
        private String password;
        
        // Getters and setters with additional validation
        public void setEmail(String email) {
            if (!EmailValidator.getInstance().isValid(email)) {
                throw new ValidationException("Invalid email format");
            }
            this.email = email;
        }
    }
    
    /**
     * ファイルパストラバーサル対策
     */
    public File getSecureFile(String filename) {
        // ヌルチェック
        if (filename == null || filename.isEmpty()) {
            throw new IllegalArgumentException("Filename cannot be empty");
        }
        
        // パストラバーサル文字を除去
        String cleanFilename = filename.replaceAll("\\.\\.|/|\\\\", "");
        
        // ホワイトリスト検証
        if (!ALPHANUMERIC.matcher(cleanFilename).matches()) {
            throw new SecurityException("Invalid filename");
        }
        
        // 安全なディレクトリ内でのみファイルアクセス
        File baseDir = new File("/safe/upload/directory");
        File file = new File(baseDir, cleanFilename);
        
        // 正規化してディレクトリトラバーサルを防ぐ
        try {
            if (!file.getCanonicalPath().startsWith(baseDir.getCanonicalPath())) {
                throw new SecurityException("Path traversal attempt detected");
            }
        } catch (IOException e) {
            throw new SecurityException("Invalid file path");
        }
        
        return file;
    }
}
```

#### 暗号化実装

```java
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.security.SecureRandom;
import java.util.Base64;

public class SecureEncryption {
    
    private static final String ALGORITHM = "AES/GCM/NoPadding";
    private static final int GCM_TAG_LENGTH = 128;
    private static final int GCM_IV_LENGTH = 12;
    private static final int AES_KEY_SIZE = 256;
    
    /**
     * AES-GCM暗号化
     */
    public EncryptedData encrypt(String plaintext, SecretKey key) throws Exception {
        // セキュアな乱数生成器でIV生成
        SecureRandom random = new SecureRandom();
        byte[] iv = new byte[GCM_IV_LENGTH];
        random.nextBytes(iv);
        
        // 暗号化設定
        Cipher cipher = Cipher.getInstance(ALGORITHM);
        GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
        cipher.init(Cipher.ENCRYPT_MODE, key, spec);
        
        // 暗号化実行
        byte[] ciphertext = cipher.doFinal(plaintext.getBytes("UTF-8"));
        
        return new EncryptedData(
            Base64.getEncoder().encodeToString(ciphertext),
            Base64.getEncoder().encodeToString(iv)
        );
    }
    
    /**
     * AES-GCM復号化
     */
    public String decrypt(EncryptedData encryptedData, SecretKey key) throws Exception {
        // Base64デコード
        byte[] ciphertext = Base64.getDecoder().decode(encryptedData.getCiphertext());
        byte[] iv = Base64.getDecoder().decode(encryptedData.getIv());
        
        // 復号化設定
        Cipher cipher = Cipher.getInstance(ALGORITHM);
        GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
        cipher.init(Cipher.DECRYPT_MODE, key, spec);
        
        // 復号化実行
        byte[] plaintext = cipher.doFinal(ciphertext);
        return new String(plaintext, "UTF-8");
    }
    
    /**
     * セキュアな鍵生成
     */
    public SecretKey generateKey() throws Exception {
        KeyGenerator keyGenerator = KeyGenerator.getInstance("AES");
        keyGenerator.init(AES_KEY_SIZE, new SecureRandom());
        return keyGenerator.generateKey();
    }
    
    /**
     * パスワードベース暗号化（PBKDF2）
     */
    public SecretKey deriveKeyFromPassword(String password, byte[] salt) throws Exception {
        int iterations = 100000;  // 最小推奨値
        int keyLength = 256;
        
        PBEKeySpec spec = new PBEKeySpec(
            password.toCharArray(),
            salt,
            iterations,
            keyLength
        );
        
        SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        byte[] keyBytes = factory.generateSecret(spec).getEncoded();
        return new SecretKeySpec(keyBytes, "AES");
    }
    
    /**
     * 暗号化データクラス
     */
    public static class EncryptedData {
        private final String ciphertext;
        private final String iv;
        
        public EncryptedData(String ciphertext, String iv) {
            this.ciphertext = ciphertext;
            this.iv = iv;
        }
        
        // Getters
        public String getCiphertext() { return ciphertext; }
        public String getIv() { return iv; }
    }
}
```

### Go

#### セキュアなHTTPハンドラ

```go
package main

import (
    "context"
    "crypto/rand"
    "crypto/subtle"
    "encoding/base64"
    "fmt"
    "html/template"
    "log"
    "net/http"
    "regexp"
    "strings"
    "time"
    
    "golang.org/x/crypto/bcrypt"
    "golang.org/x/time/rate"
    "github.com/gorilla/csrf"
    "github.com/gorilla/sessions"
)

// セキュアなセッション管理
var store = sessions.NewCookieStore([]byte(generateRandomKey(32)))

func init() {
    store.Options = &sessions.Options{
        Path:     "/",
        MaxAge:   900, // 15分
        HttpOnly: true,
        Secure:   true,
        SameSite: http.SameSiteStrictMode,
    }
}

// レート制限の実装
type RateLimiter struct {
    limiter  *rate.Limiter
    visitors map[string]*rate.Limiter
    mu       sync.RWMutex
}

func NewRateLimiter() *RateLimiter {
    return &RateLimiter{
        limiter:  rate.NewLimiter(10, 100), // 10 req/s, burst 100
        visitors: make(map[string]*rate.Limiter),
    }
}

func (rl *RateLimiter) GetVisitor(ip string) *rate.Limiter {
    rl.mu.Lock()
    defer rl.mu.Unlock()
    
    limiter, exists := rl.visitors[ip]
    if !exists {
        limiter = rate.NewLimiter(1, 5) // 1 req/s per IP
        rl.visitors[ip] = limiter
    }
    
    return limiter
}

// レート制限ミドルウェア
func RateLimitMiddleware(rl *RateLimiter) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            ip := getClientIP(r)
            limiter := rl.GetVisitor(ip)
            
            if !limiter.Allow() {
                http.Error(w, "Too Many Requests", http.StatusTooManyRequests)
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}

// 入力検証
type InputValidator struct {
    usernameRegex *regexp.Regexp
    emailRegex    *regexp.Regexp
}

func NewInputValidator() *InputValidator {
    return &InputValidator{
        usernameRegex: regexp.MustCompile(`^[a-zA-Z0-9_-]{3,20}$`),
        emailRegex:    regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`),
    }
}

func (v *InputValidator) ValidateUsername(username string) error {
    if !v.usernameRegex.MatchString(username) {
        return fmt.Errorf("invalid username format")
    }
    return nil
}

func (v *InputValidator) ValidateEmail(email string) error {
    if !v.emailRegex.MatchString(email) {
        return fmt.Errorf("invalid email format")
    }
    return nil
}

// SQLインジェクション対策
func GetUserByID(db *sql.DB, userID int64) (*User, error) {
    // パラメータ化クエリを使用
    query := `SELECT id, username, email, created_at FROM users WHERE id = $1`
    
    var user User
    err := db.QueryRow(query, userID).Scan(
        &user.ID,
        &user.Username,
        &user.Email,
        &user.CreatedAt,
    )
    
    if err == sql.ErrNoRows {
        return nil, fmt.Errorf("user not found")
    }
    if err != nil {
        log.Printf("Database error: %v", err)
        return nil, fmt.Errorf("internal server error")
    }
    
    return &user, nil
}

// XSS対策 - テンプレートの自動エスケープ
func RenderHTML(w http.ResponseWriter, data interface{}) {
    tmpl := template.Must(template.New("page").Parse(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{{.Title}}</title>
        </head>
        <body>
            <h1>{{.Heading}}</h1>
            <p>{{.Content}}</p>
        </body>
        </html>
    `))
    
    // template.HTMLはエスケープを自動的に行う
    err := tmpl.Execute(w, data)
    if err != nil {
        http.Error(w, "Internal Server Error", http.StatusInternalServerError)
    }
}

// パスワードハッシュ化
func HashPassword(password string) (string, error) {
    // パスワード強度チェック
    if len(password) < 12 {
        return "", fmt.Errorf("password must be at least 12 characters")
    }
    
    // bcryptでハッシュ化（コスト14を推奨）
    hashedBytes, err := bcrypt.GenerateFromPassword([]byte(password), 14)
    if err != nil {
        return "", err
    }
    
    return string(hashedBytes), nil
}

func VerifyPassword(hashedPassword, password string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(password))
    
    // タイミング攻撃対策
    if err != nil {
        // ランダムな遅延を追加
        time.Sleep(time.Millisecond * time.Duration(rand.Intn(100)))
        return false
    }
    
    return true
}

// CSRF対策
func SetupCSRF() func(http.Handler) http.Handler {
    return csrf.Protect(
        []byte(generateRandomKey(32)),
        csrf.Secure(true),
        csrf.HttpOnly(true),
        csrf.SameSite(csrf.SameSiteStrictMode),
        csrf.ErrorHandler(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            http.Error(w, "CSRF token validation failed", http.StatusForbidden)
        })),
    )
}

// セキュアなランダムキー生成
func generateRandomKey(length int) string {
    bytes := make([]byte, length)
    if _, err := rand.Read(bytes); err != nil {
        panic(err)
    }
    return base64.StdEncoding.EncodeToString(bytes)
}

// セキュアなファイルアップロード
func HandleFileUpload(w http.ResponseWriter, r *http.Request) {
    // ファイルサイズ制限（10MB）
    r.ParseMultipartForm(10 << 20)
    
    file, handler, err := r.FormFile("file")
    if err != nil {
        http.Error(w, "Failed to get file", http.StatusBadRequest)
        return
    }
    defer file.Close()
    
    // ファイル名のサニタイゼーション
    filename := sanitizeFilename(handler.Filename)
    
    // 拡張子チェック
    allowedExts := map[string]bool{
        ".jpg": true, ".jpeg": true, ".png": true, ".pdf": true,
    }
    
    ext := strings.ToLower(filepath.Ext(filename))
    if !allowedExts[ext] {
        http.Error(w, "File type not allowed", http.StatusBadRequest)
        return
    }
    
    // MIMEタイプ検証
    buffer := make([]byte, 512)
    _, err = file.Read(buffer)
    if err != nil {
        http.Error(w, "Failed to read file", http.StatusBadRequest)
        return
    }
    
    contentType := http.DetectContentType(buffer)
    if !isAllowedContentType(contentType) {
        http.Error(w, "Invalid file content", http.StatusBadRequest)
        return
    }
    
    // ユニークなファイル名生成
    newFilename := fmt.Sprintf("%s_%s%s", 
        generateRandomKey(16), 
        time.Now().Format("20060102150405"),
        ext,
    )
    
    // 安全な場所に保存
    dst, err := os.Create(filepath.Join("/secure/uploads", newFilename))
    if err != nil {
        http.Error(w, "Failed to save file", http.StatusInternalServerError)
        return
    }
    defer dst.Close()
    
    // ファイルをコピー
    file.Seek(0, 0)
    if _, err := io.Copy(dst, file); err != nil {
        http.Error(w, "Failed to save file", http.StatusInternalServerError)
        return
    }
    
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{
        "filename": newFilename,
        "message":  "File uploaded successfully",
    })
}
```

---

## 🛡️ API セキュリティ

### RESTful API セキュリティベストプラクティス

```typescript
// API認証とレート制限の実装
import express from 'express';
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import cors from 'cors';

const app = express();

// セキュリティヘッダー設定
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },
}));

// CORS設定
const corsOptions = {
  origin: (origin, callback) => {
    const allowedOrigins = [
      'https://app.example.com',
      'https://admin.example.com',
    ];
    
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  optionsSuccessStatus: 200,
};

app.use(cors(corsOptions));

// レート制限設定
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分
  max: 100, // 最大100リクエスト
  message: 'Too many requests from this IP',
  standardHeaders: true,
  legacyHeaders: false,
  // IPアドレス取得（プロキシ考慮）
  keyGenerator: (req) => {
    return req.ip || req.headers['x-forwarded-for'] || req.connection.remoteAddress;
  },
});

// ログイン試行の厳しい制限
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  skipSuccessfulRequests: true,
});

app.use('/api/', limiter);
app.use('/api/auth/login', loginLimiter);

// API認証ミドルウェア
const authenticateAPI = async (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  const token = req.headers.authorization?.split(' ')[1];
  
  try {
    if (apiKey) {
      // APIキー認証
      const isValid = await validateAPIKey(apiKey);
      if (!isValid) {
        return res.status(401).json({ error: 'Invalid API key' });
      }
    } else if (token) {
      // JWT認証
      const decoded = await verifyJWT(token);
      req.user = decoded;
    } else {
      return res.status(401).json({ error: 'Authentication required' });
    }
    
    next();
  } catch (error) {
    logger.error('Authentication error:', error);
    res.status(401).json({ error: 'Authentication failed' });
  }
};

// 入力検証ミドルウェア
const validateInput = (schema) => {
  return (req, res, next) => {
    const { error } = schema.validate(req.body, {
      abortEarly: false,
      stripUnknown: true,
    });
    
    if (error) {
      const errors = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message,
      }));
      
      return res.status(400).json({ errors });
    }
    
    next();
  };
};

// エラーハンドリング
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', {
    error: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    ip: req.ip,
  });
  
  // 本番環境では詳細なエラー情報を隠す
  const message = process.env.NODE_ENV === 'production'
    ? 'Internal Server Error'
    : err.message;
  
  res.status(err.status || 500).json({
    error: message,
    ...(process.env.NODE_ENV !== 'production' && { stack: err.stack }),
  });
});
```

### GraphQL セキュリティ

```typescript
// GraphQLセキュリティ実装
import { GraphQLSchema, GraphQLError } from 'graphql';
import depthLimit from 'graphql-depth-limit';
import costAnalysis from 'graphql-cost-analysis';
import { createRateLimitDirective } from 'graphql-rate-limit';

// クエリ深度制限
const depthLimitRule = depthLimit(5);

// クエリコスト分析
const costAnalysisRule = costAnalysis({
  maximumCost: 1000,
  defaultCost: 1,
  scalarCost: 1,
  objectCost: 2,
  listFactor: 10,
  introspectionCost: 1000,
  enforceIntrospectionCost: true,
});

// レート制限ディレクティブ
const rateLimitDirective = createRateLimitDirective({
  identifyContext: (ctx) => ctx.user?.id || ctx.ip,
});

// GraphQLサーバー設定
const server = new ApolloServer({
  schema,
  validationRules: [depthLimitRule, costAnalysisRule],
  introspection: process.env.NODE_ENV !== 'production',
  playground: process.env.NODE_ENV !== 'production',
  
  formatError: (err) => {
    // エラー情報のサニタイズ
    if (process.env.NODE_ENV === 'production') {
      // 本番環境では詳細を隠す
      if (err.extensions?.code === 'INTERNAL_SERVER_ERROR') {
        return new GraphQLError('Internal server error');
      }
    }
    
    // ログに記録
    logger.error('GraphQL error:', err);
    
    return err;
  },
  
  context: async ({ req }) => {
    // 認証情報の検証
    const token = req.headers.authorization?.replace('Bearer ', '');
    const user = token ? await verifyToken(token) : null;
    
    return {
      user,
      ip: req.ip,
      dataloaders: createDataLoaders(), // N+1問題対策
    };
  },
});

// フィールドレベルの認可
const resolvers = {
  Query: {
    sensitiveData: async (parent, args, context) => {
      // 認証チェック
      if (!context.user) {
        throw new ForbiddenError('Authentication required');
      }
      
      // 認可チェック
      if (!context.user.roles.includes('ADMIN')) {
        throw new ForbiddenError('Insufficient permissions');
      }
      
      // レート制限チェック
      await checkRateLimit(context.user.id, 'sensitiveData', 10, 3600);
      
      return await fetchSensitiveData(args);
    },
  },
  
  Mutation: {
    updateUser: async (parent, args, context) => {
      // 入力検証
      const { error } = updateUserSchema.validate(args.input);
      if (error) {
        throw new UserInputError('Invalid input', { validationErrors: error.details });
      }
      
      // 権限チェック（自分自身または管理者のみ）
      if (context.user.id !== args.id && !context.user.roles.includes('ADMIN')) {
        throw new ForbiddenError('Cannot update other users');
      }
      
      return await updateUser(args);
    },
  },
};
```

---

## 🔒 データベースセキュリティ

### セキュアなデータベース接続

```javascript
// MongoDB接続のセキュリティ設定
const mongoose = require('mongoose');
const { MongoClient } = require('mongodb');

// 接続文字列は環境変数から取得
const mongoUri = process.env.MONGODB_URI;

// セキュアな接続オプション
const mongoOptions = {
  useNewUrlParser: true,
  useUnifiedTopology: true,
  authSource: 'admin',
  ssl: true,
  sslValidate: true,
  sslCA: fs.readFileSync('/path/to/ca.pem'),
  sslCert: fs.readFileSync('/path/to/client-cert.pem'),
  sslKey: fs.readFileSync('/path/to/client-key.pem'),
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000,
  maxPoolSize: 50,
  minPoolSize: 10,
  maxIdleTimeMS: 10000,
  
  // 認証メカニズム
  authMechanism: 'SCRAM-SHA-256',
  
  // 読み取り設定
  readPreference: 'primary',
  readConcern: { level: 'majority' },
  
  // 書き込み設定
  writeConcern: {
    w: 'majority',
    j: true,
    wtimeout: 5000,
  },
};

// データの暗号化
const encryptionSchema = new mongoose.Schema({
  // フィールドレベル暗号化
  ssn: {
    type: String,
    required: true,
    encrypt: true, // mongoose-encryption
  },
  creditCard: {
    type: String,
    required: true,
    encrypt: true,
  },
  // 通常フィールド
  name: String,
  email: {
    type: String,
    lowercase: true,
    index: true,
  },
});

// 暗号化プラグイン設定
encryptionSchema.plugin(mongooseEncryption, {
  encryptionKey: process.env.ENCRYPTION_KEY,
  signingKey: process.env.SIGNING_KEY,
  encryptedFields: ['ssn', 'creditCard'],
  additionalAuthenticatedFields: ['email'],
});

// インジェクション対策
async function secureQuery(userInput) {
  // NoSQLインジェクション対策
  const sanitized = {};
  
  // 型チェックと検証
  if (typeof userInput.username === 'string') {
    sanitized.username = userInput.username.replace(/[^\w\s]/gi, '');
  }
  
  // $演算子の使用を防ぐ
  for (const key in userInput) {
    if (key.startsWith('$') || userInput[key]?.$regex) {
      throw new Error('Invalid query parameter');
    }
  }
  
  // セキュアなクエリ実行
  return await User.findOne(sanitized)
    .select('-password -__v') // パスワードフィールドを除外
    .lean() // プレーンオブジェクトを返す
    .exec();
}
```

---

## 🚨 エラーハンドリングとログ

### セキュアなエラーハンドリング

```typescript
// エラーハンドリングのベストプラクティス
class SecureErrorHandler {
  private readonly isDevelopment = process.env.NODE_ENV !== 'production';
  
  // エラーレスポンスのサニタイズ
  public handleError(error: Error, req: Request, res: Response): void {
    // エラーログ記録（詳細情報含む）
    this.logError(error, req);
    
    // クライアントへのレスポンス（サニタイズ済み）
    const sanitizedError = this.sanitizeError(error);
    res.status(sanitizedError.status).json(sanitizedError);
  }
  
  private sanitizeError(error: any): SanitizedError {
    // 既知のエラータイプ
    if (error instanceof ValidationError) {
      return {
        status: 400,
        message: 'Validation failed',
        errors: error.errors, // 検証エラーの詳細は含める
      };
    }
    
    if (error instanceof UnauthorizedError) {
      return {
        status: 401,
        message: 'Authentication required',
      };
    }
    
    if (error instanceof ForbiddenError) {
      return {
        status: 403,
        message: 'Access denied',
      };
    }
    
    // 本番環境では詳細を隠す
    if (!this.isDevelopment) {
      return {
        status: 500,
        message: 'Internal server error',
        reference: error.id, // エラー追跡用ID
      };
    }
    
    // 開発環境では詳細を含める
    return {
      status: error.status || 500,
      message: error.message,
      stack: error.stack,
    };
  }
  
  private logError(error: Error, req: Request): void {
    const errorLog = {
      timestamp: new Date().toISOString(),
      level: 'error',
      message: error.message,
      stack: error.stack,
      request: {
        method: req.method,
        url: req.url,
        headers: this.sanitizeHeaders(req.headers),
        body: this.sanitizeBody(req.body),
        ip: req.ip,
        userAgent: req.get('user-agent'),
      },
      user: req.user?.id,
      correlationId: req.id,
    };
    
    // 構造化ログ出力
    logger.error(errorLog);
    
    // 重大なエラーはアラート送信
    if (this.isCriticalError(error)) {
      this.sendAlert(errorLog);
    }
  }
  
  private sanitizeHeaders(headers: any): any {
    const sanitized = { ...headers };
    // 機密情報を除去
    delete sanitized.authorization;
    delete sanitized.cookie;
    delete sanitized['x-api-key'];
    return sanitized;
  }
  
  private sanitizeBody(body: any): any {
    if (!body) return {};
    
    const sanitized = { ...body };
    // パスワードや機密情報を除去
    const sensitiveFields = ['password', 'token', 'apiKey', 'secret', 'creditCard', 'ssn'];
    
    for (const field of sensitiveFields) {
      if (sanitized[field]) {
        sanitized[field] = '[REDACTED]';
      }
    }
    
    return sanitized;
  }
}

// セキュアなログ設定
const winston = require('winston');
const crypto = require('crypto');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json(),
    // PII除去
    winston.format.printf((info) => {
      // 個人情報のマスキング
      if (info.email) {
        info.email = info.email.replace(/(?<=.{3}).(?=.*@)/g, '*');
      }
      if (info.phone) {
        info.phone = info.phone.replace(/\d(?=\d{4})/g, '*');
      }
      if (info.creditCard) {
        info.creditCard = '**** **** **** ' + info.creditCard.slice(-4);
      }
      return JSON.stringify(info);
    }),
  ),
  transports: [
    // ファイル出力（ローテーション付き）
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    }),
    new winston.transports.File({
      filename: 'logs/combined.log',
      maxsize: 5242880,
      maxFiles: 5,
    }),
  ],
  // 監査ログ用の設定
  auditLog: {
    enabled: true,
    events: ['login', 'logout', 'dataAccess', 'dataModification', 'privilegedAction'],
    storage: 'secure-audit-storage',
    encryption: true,
    tamperProtection: true,
  },
});

// 監査ログ記録
function auditLog(action: string, details: any): void {
  const auditEntry = {
    timestamp: new Date().toISOString(),
    action,
    user: details.userId,
    ip: details.ip,
    resource: details.resource,
    result: details.result,
    // ハッシュによる改ざん検知
    hash: crypto.createHash('sha256')
      .update(JSON.stringify({ action, ...details }))
      .digest('hex'),
  };
  
  logger.audit(auditEntry);
}
```

---

## 🔐 セキュリティテスト

### ユニットテストでのセキュリティ検証

```javascript
// セキュリティテストの実装例
const request = require('supertest');
const app = require('../app');

describe('Security Tests', () => {
  // SQLインジェクションテスト
  describe('SQL Injection Prevention', () => {
    const sqlInjectionPayloads = [
      "' OR '1'='1",
      "1; DROP TABLE users;--",
      "admin'--",
      "' UNION SELECT * FROM users--",
      "1' AND '1' = '1",
    ];
    
    sqlInjectionPayloads.forEach(payload => {
      it(`should prevent SQL injection with payload: ${payload}`, async () => {
        const response = await request(app)
          .get('/api/users')
          .query({ username: payload });
        
        expect(response.status).toBe(400);
        expect(response.body).not.toContain('SQL');
        expect(response.body).not.toContain('users');
      });
    });
  });
  
  // XSSテスト
  describe('XSS Prevention', () => {
    const xssPayloads = [
      '<script>alert("XSS")</script>',
      '<img src=x onerror=alert("XSS")>',
      'javascript:alert("XSS")',
      '<svg onload=alert("XSS")>',
      '"><script>alert("XSS")</script>',
    ];
    
    xssPayloads.forEach(payload => {
      it(`should sanitize XSS payload: ${payload}`, async () => {
        const response = await request(app)
          .post('/api/comments')
          .send({ content: payload });
        
        expect(response.body.content).not.toContain('<script>');
        expect(response.body.content).not.toContain('javascript:');
        expect(response.body.content).not.toContain('onerror');
      });
    });
  });
  
  // 認証テスト
  describe('Authentication', () => {
    it('should reject requests without authentication', async () => {
      const response = await request(app)
        .get('/api/protected');
      
      expect(response.status).toBe(401);
    });
    
    it('should reject invalid tokens', async () => {
      const response = await request(app)
        .get('/api/protected')
        .set('Authorization', 'Bearer invalid-token');
      
      expect(response.status).toBe(401);
    });
    
    it('should reject expired tokens', async () => {
      const expiredToken = generateExpiredToken();
      const response = await request(app)
        .get('/api/protected')
        .set('Authorization', `Bearer ${expiredToken}`);
      
      expect(response.status).toBe(401);
    });
  });
  
  // レート制限テスト
  describe('Rate Limiting', () => {
    it('should enforce rate limits', async () => {
      const requests = [];
      
      // 制限を超えるリクエストを送信
      for (let i = 0; i < 102; i++) {
        requests.push(
          request(app).get('/api/data')
        );
      }
      
      const responses = await Promise.all(requests);
      const tooManyRequests = responses.filter(r => r.status === 429);
      
      expect(tooManyRequests.length).toBeGreaterThan(0);
    });
  });
  
  // セキュリティヘッダーテスト
  describe('Security Headers', () => {
    it('should set security headers', async () => {
      const response = await request(app).get('/');
      
      expect(response.headers['x-content-type-options']).toBe('nosniff');
      expect(response.headers['x-frame-options']).toBe('DENY');
      expect(response.headers['x-xss-protection']).toBe('1; mode=block');
      expect(response.headers['strict-transport-security']).toContain('max-age=');
      expect(response.headers['content-security-policy']).toBeDefined();
    });
  });
});
```

---

## 📋 セキュリティチェックリスト

### コードレビュー時の確認項目

```yaml
authentication:
  - [ ] パスワードは適切にハッシュ化されているか
  - [ ] セッション管理は適切か
  - [ ] MFAが実装されているか（重要機能）
  - [ ] トークンの有効期限は適切か

authorization:
  - [ ] すべてのエンドポイントで認可チェックがあるか
  - [ ] 最小権限の原則に従っているか
  - [ ] リソースベースの認可が実装されているか

input_validation:
  - [ ] すべての入力が検証されているか
  - [ ] ホワイトリスト検証を使用しているか
  - [ ] 長さ制限が設定されているか
  - [ ] 型チェックが実施されているか

output_encoding:
  - [ ] HTMLコンテキストでエスケープされているか
  - [ ] JavaScriptコンテキストでエスケープされているか
  - [ ] URLコンテキストでエンコードされているか
  - [ ] SQLクエリでパラメータ化されているか

cryptography:
  - [ ] 強力な暗号アルゴリズムを使用しているか
  - [ ] 鍵管理は適切か
  - [ ] ランダム値生成は安全か
  - [ ] TLS/HTTPSが使用されているか

error_handling:
  - [ ] エラーメッセージに機密情報が含まれていないか
  - [ ] スタックトレースが本番で表示されないか
  - [ ] ログに機密情報が記録されていないか

security_headers:
  - [ ] CSPが設定されているか
  - [ ] HSTSが有効か
  - [ ] X-Frame-Optionsが設定されているか
  - [ ] X-Content-Type-Optionsが設定されているか

dependencies:
  - [ ] 既知の脆弱性がないか
  - [ ] 最新バージョンを使用しているか
  - [ ] ライセンスは適切か
  - [ ] 不要な依存関係はないか
```

---

## 📚 参考資料とツール

### セキュリティリソース

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [CERT Secure Coding Standards](https://wiki.sei.cmu.edu/confluence/display/seccode)
- [SANS Secure Coding](https://www.sans.org/secure-coding/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

### 静的解析ツール

| 言語 | ツール | 用途 |
|------|--------|------|
| JavaScript | ESLint Security Plugin | セキュリティルール |
| TypeScript | TSLint Security Rules | TypeScript専用 |
| Python | Bandit | Pythonセキュリティ |
| Java | SpotBugs | バグ・脆弱性検出 |
| Go | Gosec | Goセキュリティ |
| C/C++ | Flawfinder | C/C++脆弱性 |
| All | Semgrep | 多言語対応 |
| All | SonarQube | 包括的分析 |

### 動的テストツール

- OWASP ZAP - Webアプリケーションスキャナ
- Burp Suite - プロフェッショナル向けツール
- SQLMap - SQLインジェクションテスト
- Nikto - Webサーバースキャナ
- Nmap - ネットワークスキャナ

---

**© 2025 エス・エー・エス株式会社 - セキュアコーディングガイド**