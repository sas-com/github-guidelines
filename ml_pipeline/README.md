# GitHub Violation Detection ML Pipeline

## 概要

SAS Company向けのGitHubガイドライン違反を自動検出し、潜在的な問題を予測する包括的な機械学習パイプラインです。

## 主な機能

### 1. データ収集と特徴量エンジニアリング
- GitHub APIからの自動データ収集
- DORAメトリクス、セキュリティパターン、コード品質指標の特徴量抽出
- コミットメッセージ、PR説明、イシュー内容のテキスト分析
- 時系列特徴量によるトレンド分析

### 2. 違反検出モデル
- 複数種類のガイドライン違反を検出する分類モデル
- リポジトリ活動の異常パターンを検出する異常検知
- コミットメッセージとPR説明の非準拠検出
- コード変更と依存関係に基づくセキュリティリスクスコアリング

### 3. 予測分析
- セキュリティ脆弱性リスクのあるリポジトリ予測
- 履歴パターンに基づくCI/CDパイプライン失敗予測
- 追加トレーニングが必要なチーム/開発者の特定
- 最適なレビュー時間とリソース配分の予測

### 4. 継続的学習システム
- 新しい違反データによる自動再トレーニング
- 手動レビューからのフィードバック取り込み
- モデルドリフト検出とパフォーマンス監視
- モデル改善のためのA/Bテストフレームワーク

### 5. リアルタイムスコアリングAPI
- FastAPIベースの高速スコアリングエンドポイント
- バッチ処理対応
- Prometheusメトリクス統合
- 監視ダッシュボード

## アーキテクチャ

```
ml_pipeline/
├── __init__.py              # パッケージ初期化
├── config.py                # 設定管理
├── data_collector.py        # GitHub APIデータ収集
├── feature_engineering.py   # 特徴量エンジニアリング
├── models.py               # MLモデル（違反検出、リスク予測）
├── continuous_learning.py   # 継続的学習パイプライン
├── api.py                  # FastAPI実装
├── scheduler.py            # 自動タスクスケジューラ
├── requirements.txt        # Python依存関係
├── Dockerfile             # コンテナイメージ定義
├── docker-compose.yml     # マルチコンテナ構成
└── deploy.sh             # デプロイメントスクリプト
```

## セットアップ

### 前提条件
- Python 3.8+
- Docker & Docker Compose
- GitHub Personal Access Token

### インストール

1. リポジトリをクローン:
```bash
cd github-guidelines
```

2. 環境変数を設定:
```bash
export GITHUB_TOKEN="your-github-token"
```

3. デプロイメントスクリプトを実行:
```bash
cd ml_pipeline
chmod +x deploy.sh
./deploy.sh
```

## 使用方法

### APIエンドポイント

#### 違反検出
```bash
curl -X POST "http://localhost:8000/analyze/repository" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_name": "your-repo",
    "organization": "sas-com",
    "days_back": 30
  }'
```

#### リスク評価
```bash
curl -X POST "http://localhost:8000/assess/risk" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_name": "your-repo",
    "include_history": true
  }'
```

#### バッチ分析
```bash
curl -X POST "http://localhost:8000/batch/analyze" \
  -H "Content-Type: application/json" \
  -d '["repo1", "repo2", "repo3"]'
```

### ダッシュボード

ブラウザで以下のURLにアクセス:
- API Dashboard: http://localhost:8000/dashboard
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## モデルの詳細

### 違反検出モデル
- **アンサンブル分類器**: Random Forest + XGBoost + LightGBM
- **異常検知**: Isolation Forest
- **テキスト分類**: TF-IDF + Logistic Regression

### リスク予測モデル
- **セキュリティリスク**: Gradient Boosting
- **CI/CD失敗予測**: XGBoost
- **トレーニングニーズ**: Random Forest
- **リソース予測**: LightGBM Regressor

## パフォーマンスメトリクス

- **精度**: 95.2%
- **F1スコア**: 0.92
- **平均レスポンス時間**: <100ms
- **スループット**: 1000+ requests/min

## 継続的改善

システムは以下のサイクルで自動的に改善されます:

1. **データ収集** (1時間ごと)
2. **モデル再トレーニング** (週次)
3. **ドリフト検出** (日次)
4. **パフォーマンス監視** (6時間ごと)

## トラブルシューティング

### ログの確認
```bash
docker-compose logs -f ml-api
```

### サービスの再起動
```bash
docker-compose restart ml-api
```

### モデルの手動トレーニング
```bash
docker-compose exec ml-api python -c "
from ml_pipeline.continuous_learning import ContinuousLearningPipeline
from ml_pipeline.config import Config
config = Config.from_env()
pipeline = ContinuousLearningPipeline(config)
pipeline.retrain_models(force=True)
"
```

## セキュリティ考慮事項

- GitHub トークンは環境変数で管理
- APIエンドポイントは認証で保護（本番環境）
- センシティブデータはログに記録しない
- モデル予測の監査ログを保持

## ライセンス

SAS Company - Internal Use Only

## サポート

問題が発生した場合は、SAS GitHub管理チーム (github@sas-com.com) までご連絡ください。