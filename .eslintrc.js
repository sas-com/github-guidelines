/**
 * ESLint Configuration for PR Testing
 * エス・エー・エス株式会社 - セキュリティと品質重視のリンティング設定
 */

module.exports = {
  root: true,
  
  // Parser configuration
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
    project: './tsconfig.json',
    tsconfigRootDir: __dirname,
  },

  // Environment configuration
  env: {
    browser: true,
    node: true,
    es2022: true,
    jest: true,
  },

  // Extends configurations
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    '@typescript-eslint/recommended-requiring-type-checking',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'plugin:security/recommended',
    'plugin:no-secrets/recommended',
    'plugin:sonarjs/recommended',
    'prettier',
  ],

  // Plugins
  plugins: [
    '@typescript-eslint',
    'react',
    'react-hooks',
    'jsx-a11y',
    'import',
    'security',
    'no-secrets',
    'sonarjs',
    'promise',
    'unicorn',
  ],

  // Global settings
  settings: {
    react: {
      version: 'detect',
    },
    'import/resolver': {
      typescript: {
        alwaysTryTypes: true,
        project: './tsconfig.json',
      },
      node: {
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
      },
    },
  },

  // Rules configuration
  rules: {
    // =====================================
    // セキュリティ関連ルール (最優先)
    // =====================================
    'security/detect-unsafe-regex': 'error',
    'security/detect-non-literal-regexp': 'warn',
    'security/detect-non-literal-fs-filename': 'error',
    'security/detect-eval-with-expression': 'error',
    'security/detect-pseudoRandomBytes': 'error',
    'security/detect-possible-timing-attacks': 'warn',
    'security/detect-unsafe-regex': 'error',
    'no-secrets/no-secrets': ['error', {
      tolerance: 4.2,
      additionalRegexes: {
        'JWT Token': 'eyJ[A-Za-z0-9-_=]+\\.[A-Za-z0-9-_=]+\\.?[A-Za-z0-9-_.+/=]*',
        'API Key': '[a-zA-Z0-9]{32,}',
        'Private Key': '-----BEGIN [A-Z ]+ PRIVATE KEY-----',
      }
    }],

    // =====================================
    // TypeScript特化ルール
    // =====================================
    '@typescript-eslint/no-unused-vars': ['error', { 
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_',
    }],
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unsafe-assignment': 'error',
    '@typescript-eslint/no-unsafe-member-access': 'error',
    '@typescript-eslint/no-unsafe-call': 'error',
    '@typescript-eslint/no-unsafe-return': 'error',
    '@typescript-eslint/prefer-nullish-coalescing': 'error',
    '@typescript-eslint/prefer-optional-chain': 'error',
    '@typescript-eslint/strict-boolean-expressions': ['error', {
      allowString: false,
      allowNumber: false,
      allowNullableObject: false,
    }],

    // =====================================
    // React特化ルール
    // =====================================
    'react/prop-types': 'off', // TypeScriptで型チェックするため
    'react/react-in-jsx-scope': 'off', // React 17+では不要
    'react/jsx-uses-react': 'off', // React 17+では不要
    'react/jsx-props-no-spreading': ['warn', {
      html: 'enforce',
      custom: 'enforce',
      explicitSpread: 'ignore',
    }],
    'react/jsx-no-useless-fragment': 'error',
    'react/jsx-boolean-value': ['error', 'never'],
    'react/self-closing-comp': 'error',
    'react/jsx-curly-brace-presence': ['error', { props: 'never', children: 'never' }],
    'react-hooks/exhaustive-deps': 'error',
    
    // =====================================
    // アクセシビリティルール
    // =====================================
    'jsx-a11y/alt-text': 'error',
    'jsx-a11y/aria-props': 'error',
    'jsx-a11y/aria-proptypes': 'error',
    'jsx-a11y/aria-unsupported-elements': 'error',
    'jsx-a11y/role-has-required-aria-props': 'error',
    'jsx-a11y/role-supports-aria-props': 'error',
    'jsx-a11y/click-events-have-key-events': 'warn',
    'jsx-a11y/no-static-element-interactions': 'warn',

    // =====================================
    // Import/Export ルール
    // =====================================
    'import/order': ['error', {
      groups: [
        'builtin',
        'external', 
        'internal',
        ['parent', 'sibling', 'index']
      ],
      'newlines-between': 'always',
      alphabetize: {
        order: 'asc',
        caseInsensitive: true,
      },
    }],
    'import/no-unresolved': 'error',
    'import/no-cycle': 'error',
    'import/no-self-import': 'error',
    'import/no-duplicates': 'error',
    'import/first': 'error',
    'import/newline-after-import': 'error',

    // =====================================
    // コード品質ルール
    // =====================================
    'sonarjs/cognitive-complexity': ['error', 15],
    'sonarjs/no-duplicate-string': ['error', 3],
    'sonarjs/no-identical-functions': 'error',
    'sonarjs/no-redundant-boolean': 'error',
    'sonarjs/no-unused-collection': 'error',
    'sonarjs/prefer-immediate-return': 'error',

    // =====================================
    // Promise/Async ルール
    // =====================================
    'promise/always-return': 'error',
    'promise/no-return-wrap': 'error',
    'promise/param-names': 'error',
    'promise/catch-or-return': 'error',
    'promise/no-nesting': 'warn',
    'promise/no-promise-in-callback': 'warn',
    'promise/no-callback-in-promise': 'warn',
    'promise/avoid-new': 'off',
    'promise/no-new-statics': 'error',
    'promise/no-return-in-finally': 'warn',
    'promise/valid-params': 'warn',

    // =====================================
    // パフォーマンス関連ルール
    // =====================================
    'unicorn/prefer-array-flat': 'error',
    'unicorn/prefer-array-flat-map': 'error',
    'unicorn/prefer-includes': 'error',
    'unicorn/prefer-string-starts-ends-with': 'error',
    'unicorn/prefer-query-selector': 'error',
    'unicorn/no-array-for-each': 'warn',
    'unicorn/no-for-loop': 'error',

    // =====================================
    // 一般的なベストプラクティス
    // =====================================
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
    'no-alert': 'error',
    'no-eval': 'error',
    'no-implied-eval': 'error',
    'no-new-func': 'error',
    'no-script-url': 'error',
    'no-proto': 'error',
    'no-iterator': 'error',
    'no-with': 'error',
    'prefer-const': 'error',
    'no-var': 'error',
    'object-shorthand': 'error',
    'prefer-arrow-callback': 'error',
    'prefer-template': 'error',
    'no-useless-concat': 'error',
    'no-useless-return': 'error',
    'no-unreachable': 'error',
    'no-duplicate-case': 'error',
    'default-case': 'error',
    'eqeqeq': 'error',
    'no-empty': 'error',
    'no-extra-semi': 'error',
    'no-func-assign': 'error',
    'no-inner-declarations': 'error',
    'no-irregular-whitespace': 'error',
    'no-sparse-arrays': 'error',
    'use-isnan': 'error',
    'valid-typeof': 'error',
  },

  // =====================================
  // 環境別設定のオーバーライド
  // =====================================
  overrides: [
    // テストファイル専用設定
    {
      files: ['**/*.test.{js,jsx,ts,tsx}', '**/*.spec.{js,jsx,ts,tsx}', '**/tests/**/*'],
      env: {
        jest: true,
      },
      rules: {
        '@typescript-eslint/no-explicit-any': 'warn',
        '@typescript-eslint/no-unsafe-assignment': 'warn',
        'sonarjs/no-duplicate-string': 'off',
        'no-console': 'off',
      },
    },
    
    // 設定ファイル専用設定
    {
      files: ['*.config.{js,ts}', '.eslintrc.js', 'webpack.config.js'],
      env: {
        node: true,
      },
      rules: {
        '@typescript-eslint/no-require-imports': 'off',
        'import/no-default-export': 'off',
      },
    },
    
    // Next.js pages専用設定
    {
      files: ['pages/**/*', 'src/pages/**/*'],
      rules: {
        'import/no-default-export': 'off',
        'react/jsx-props-no-spreading': 'off',
      },
    },

    // セキュリティクリティカルなファイル
    {
      files: ['**/auth/**/*', '**/security/**/*', '**/api/**/*'],
      rules: {
        'security/detect-non-literal-regexp': 'error',
        'security/detect-possible-timing-attacks': 'error',
        '@typescript-eslint/no-explicit-any': 'error',
        'no-secrets/no-secrets': ['error', { tolerance: 3.5 }],
      },
    },

    // JavaScript専用設定（TypeScriptルールを無効化）
    {
      files: ['**/*.js', '**/*.jsx'],
      rules: {
        '@typescript-eslint/no-unsafe-assignment': 'off',
        '@typescript-eslint/no-unsafe-member-access': 'off',
        '@typescript-eslint/no-unsafe-call': 'off',
        '@typescript-eslint/no-unsafe-return': 'off',
        '@typescript-eslint/restrict-template-expressions': 'off',
        '@typescript-eslint/no-floating-promises': 'off',
      },
    },
  ],

  // 無視するファイル・ディレクトリ
  ignorePatterns: [
    'node_modules/',
    'build/',
    'dist/',
    'coverage/',
    '.next/',
    '.vercel/',
    '*.min.js',
    'public/',
    '*.d.ts',
  ],
};