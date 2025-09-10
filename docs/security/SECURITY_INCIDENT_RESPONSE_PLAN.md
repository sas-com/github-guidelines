# セキュリティインシデント対応計画

**エス・エー・エス株式会社**  
*GitHub環境における包括的セキュリティインシデント対応フレームワーク*

## 目次

1. [概要](#概要)
2. [インシデント重要度分類](#インシデント重要度分類)
3. [インシデント対応体制](#インシデント対応体制)
4. [インシデント対応フロー](#インシデント対応フロー)
5. [自動化システム](#自動化システム)
6. [コミュニケーション計画](#コミュニケーション計画)
7. [事後活動](#事後活動)
8. [付録](#付録)

## 概要

### 目的
本計画は、エス・エー・エス株式会社のGitHub環境で発生するセキュリティインシデントに対して、迅速かつ効果的に対応するための包括的フレームワークを提供します。

### 適用範囲
- GitHub Organization (sas-com) 全体
- 全リポジトリ・プロジェクト
- 開発・運用に関わる全従業員
- 外部連携システム・サービス

### 基本原則
1. **迅速性**: 検知から初動対応まで最短時間で実施
2. **透明性**: ステークホルダーへの適切な情報共有
3. **学習**: インシデントから得た教訓の組織的活用
4. **自動化**: 人的ミスの削減と効率化
5. **準拠性**: 法規制・コンプライアンス要件の遵守

## インシデント重要度分類

### P0 - Critical (緊急対応必須)

**定義**: 事業継続に重大な影響を及ぼす最重要インシデント

**該当条件**:
- 本番環境への不正アクセス・データ漏洩
- 顧客データの漏洩・改ざん
- 認証システムの完全な侵害
- ランサムウェア感染
- GitHub Organization全体の権限昇格攻撃

**対応時間**:
- 検知: 即座（自動監視）
- 初動: 15分以内
- エスカレーション: 即座
- 復旧目標: 4時間以内

**対応チーム**:
- インシデントコマンダー（CTO or 代理）
- セキュリティチーム全員
- 該当サービス開発チーム
- 法務・コンプライアンス担当
- 広報担当（必要に応じて）

### P1 - High (高優先度)

**定義**: サービス機能に重大な影響がある高優先度インシデント

**該当条件**:
- 開発環境への不正アクセス
- Critical/High CVSSスコアの脆弱性発見
- 複数の認証失敗試行（ブルートフォース攻撃）
- 悪意のあるコードのコミット検知
- Secretの漏洩（非本番環境）

**対応時間**:
- 検知: 5分以内
- 初動: 1時間以内
- エスカレーション: 30分以内
- 復旧目標: 24時間以内

**対応チーム**:
- セキュリティ担当者
- 開発チームリーダー
- DevOpsエンジニア

### P2 - Medium (中優先度)

**定義**: 限定的な影響があるが緊急性は低いインシデント

**該当条件**:
- Medium CVSSスコアの脆弱性
- 設定ミス・ポリシー違反
- 異常なリポジトリアクティビティ
- 依存関係の脆弱性（非Critical）
- 不正なWebhook設定

**対応時間**:
- 検知: 1時間以内
- 初動: 4時間以内
- エスカレーション: 2時間以内
- 復旧目標: 72時間以内

**対応チーム**:
- セキュリティ担当者
- 該当チーム開発者

### P3 - Low (低優先度)

**定義**: 軽微な影響で計画的対応が可能なインシデント

**該当条件**:
- Low CVSSスコアの脆弱性
- ベストプラクティス違反
- 軽微なポリシー違反
- 情報レベルのセキュリティ警告

**対応時間**:
- 検知: 24時間以内
- 初動: 翌営業日
- エスカレーション: 必要に応じて
- 復旧目標: 1週間以内

**対応チーム**:
- 該当チーム開発者
- セキュリティ担当者（アドバイザリー）

## インシデント対応体制

### 組織構造

```
┌─────────────────────────┐
│   インシデントコマンダー    │
│      (CTO/代理)         │
└────────────┬────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼───┐       ┌───▼───┐
│技術対応│       │連絡調整│
│リーダー│       │リーダー│
└───┬───┘       └───┬───┘
    │                 │
┌───▼───────────────▼───┐
│   対応実行チーム        │
│ - セキュリティ担当      │
│ - 開発者              │
│ - インフラ担当         │
└─────────────────────┘
```

### 役割と責任

#### インシデントコマンダー
- インシデント対応の全体統括
- 重要な意思決定の実施
- 外部機関との調整
- 経営層への報告

#### 技術対応リーダー
- 技術的調査の指揮
- 封じ込め・復旧作業の管理
- 技術的解決策の評価・決定
- エビデンス収集の監督

#### 連絡調整リーダー
- ステークホルダーへの連絡
- 状況報告の作成・配信
- 外部コミュニケーション管理
- ドキュメント管理

#### 対応実行チーム
- 実際の調査・分析作業
- 技術的対策の実装
- モニタリング・検証
- 詳細レポート作成

### 連絡先リスト

| 役割 | 主担当 | 副担当 | 連絡方法 |
|------|--------|--------|----------|
| インシデントコマンダー | CTO | 技術部長 | Teams/携帯 |
| セキュリティリーダー | セキュリティ責任者 | シニアエンジニア | Teams/メール |
| 開発リーダー | 開発部長 | チームリーダー | Teams/メール |
| 法務担当 | 法務責任者 | 外部弁護士 | メール/電話 |
| 広報担当 | 広報責任者 | マーケティング部長 | Teams/メール |

## インシデント対応フロー

### Phase 1: 検知と分析 (Detection & Analysis)

#### 1.1 検知メカニズム
- **自動検知**:
  - GitHub Security Alerts
  - SAST/DAST スキャン結果
  - 監視システムアラート
  - Webhook異常検知
  - ログ分析システム

- **手動報告**:
  - 開発者からの報告
  - 外部セキュリティ研究者
  - 顧客からの通報
  - パートナー企業からの連絡

#### 1.2 初期分析
```yaml
初期分析チェックリスト:
  - インシデントの種類特定
  - 影響範囲の概算
  - 重要度レベルの判定
  - 緊急度の評価
  - 関係者の特定
  - 初期エビデンスの収集
```

#### 1.3 エスカレーション判定
- P0: 即座にインシデントコマンダーへ
- P1: 30分以内にセキュリティリーダーへ
- P2: 2時間以内に担当チームリーダーへ
- P3: 翌営業日に報告

### Phase 2: 封じ込めと根絶 (Containment & Eradication)

#### 2.1 短期封じ込め
**即座に実施する措置**:
- 影響を受けたアカウントの無効化
- 不正なアクセストークンの取り消し
- 悪意のあるコードの隔離
- ネットワークアクセスの制限
- 該当リポジトリの一時的な保護

#### 2.2 証拠保全
```bash
# 証拠収集スクリプトの実行
./scripts/incident-tools/evidence-collector.sh \
  --incident-id INC-2025-001 \
  --priority P0 \
  --collect-all
```

**収集対象**:
- GitHub Audit Logs
- アプリケーションログ
- システムログ
- ネットワークトラフィック
- データベース変更履歴
- 設定変更履歴

#### 2.3 長期封じ込め
- 脆弱性の修正パッチ適用
- セキュリティ設定の強化
- アクセス制御の見直し
- 監視ルールの追加
- セキュリティポリシーの更新

#### 2.4 根絶作業
- マルウェアの完全除去
- バックドアの排除
- 不正アカウントの削除
- 脆弱な設定の修正
- セキュリティホールの閉鎖

### Phase 3: 復旧と検証 (Recovery & Validation)

#### 3.1 システム復旧
**復旧手順**:
1. クリーンな環境の準備
2. バックアップからのデータ復元
3. セキュリティパッチの適用
4. 設定の再検証
5. 段階的なサービス再開

#### 3.2 監視強化
```yaml
強化監視項目:
  - 復旧システムの挙動監視
  - 異常トラフィックの検知
  - ログの詳細分析
  - パフォーマンス監視
  - セキュリティイベント追跡
```

#### 3.3 検証テスト
- ペネトレーションテスト
- 脆弱性スキャン
- 設定監査
- アクセス権限レビュー
- バックアップ復元テスト

### Phase 4: 事後活動 (Post-Incident Activities)

#### 4.1 インシデント報告書
**必須記載事項**:
- エグゼクティブサマリー
- インシデントタイムライン
- 影響範囲と被害状況
- 実施した対応措置
- 根本原因分析
- 改善提案
- 学んだ教訓

#### 4.2 改善活動
- プロセスの見直し
- ツールの改善
- トレーニングの実施
- ポリシーの更新
- 技術的対策の強化

## 自動化システム

### GitHub Actions統合

#### インシデント自動対応ワークフロー
```yaml
name: Incident Response Automation

on:
  repository_dispatch:
    types: [security-incident]
  workflow_dispatch:
    inputs:
      severity:
        description: 'Incident Severity'
        required: true
        type: choice
        options:
          - P0
          - P1
          - P2
          - P3

jobs:
  respond:
    runs-on: ubuntu-latest
    steps:
      - name: Initialize Response
        run: |
          echo "Incident detected: ${{ github.event.client_payload.severity }}"
          
      - name: Collect Evidence
        run: |
          ./scripts/collect-evidence.sh
          
      - name: Notify Team
        run: |
          ./scripts/notify-team.sh
          
      - name: Apply Containment
        if: github.event.client_payload.severity == 'P0' || github.event.client_payload.severity == 'P1'
        run: |
          ./scripts/apply-containment.sh
```

### 自動通知システム

#### Teams/Slack統合
```python
# scripts/incident-tools/notification-handler.py
import requests
import json
from datetime import datetime

class IncidentNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send_alert(self, incident):
        """インシデントアラートを送信"""
        message = {
            "title": f"🚨 Security Incident: {incident['id']}",
            "severity": incident['severity'],
            "description": incident['description'],
            "timestamp": datetime.now().isoformat(),
            "actions": self._get_response_actions(incident['severity'])
        }
        
        response = requests.post(
            self.webhook_url,
            json=message,
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code == 200
    
    def _get_response_actions(self, severity):
        """重要度に応じた対応アクション"""
        actions = {
            'P0': ['緊急招集', 'システム隔離', '経営層通知'],
            'P1': ['チーム招集', '調査開始', 'モニタリング強化'],
            'P2': ['担当者アサイン', '分析実施', '定期報告'],
            'P3': ['チケット作成', '計画的対応', '週次レビュー']
        }
        return actions.get(severity, [])
```

### 証拠収集自動化

```bash
#!/bin/bash
# scripts/incident-tools/evidence-collector.sh

INCIDENT_ID=$1
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EVIDENCE_DIR="/secure/evidence/${INCIDENT_ID}_${TIMESTAMP}"

# ディレクトリ作成
mkdir -p ${EVIDENCE_DIR}/{logs,configs,artifacts}

# GitHub Audit Logの取得
echo "Collecting GitHub Audit Logs..."
gh api /orgs/sas-com/audit-log \
  --paginate \
  > ${EVIDENCE_DIR}/logs/github_audit.json

# リポジトリ情報の収集
echo "Collecting Repository Information..."
gh api /orgs/sas-com/repos \
  --paginate \
  > ${EVIDENCE_DIR}/configs/repositories.json

# セキュリティアラートの収集
echo "Collecting Security Alerts..."
for repo in $(gh repo list sas-com --json name -q '.[].name'); do
  gh api /repos/sas-com/${repo}/security-advisories \
    > ${EVIDENCE_DIR}/logs/${repo}_security.json
done

# システムログの収集
echo "Collecting System Logs..."
journalctl --since "1 hour ago" > ${EVIDENCE_DIR}/logs/system.log

# ハッシュ値の計算
echo "Calculating Hash Values..."
find ${EVIDENCE_DIR} -type f -exec sha256sum {} \; \
  > ${EVIDENCE_DIR}/checksums.txt

# 証拠の圧縮と暗号化
echo "Compressing and Encrypting Evidence..."
tar czf - ${EVIDENCE_DIR} | \
  gpg --encrypt --recipient security@sas-com.com \
  > ${EVIDENCE_DIR}.tar.gz.gpg

echo "Evidence collection completed: ${EVIDENCE_DIR}.tar.gz.gpg"
```

## コミュニケーション計画

### 内部コミュニケーション

#### 通知マトリックス

| 重要度 | 初回通知 | 更新頻度 | 通知対象 | 通知方法 |
|--------|----------|----------|----------|----------|
| P0 | 即座 | 30分毎 | 全経営層、全技術チーム | Teams通話、SMS |
| P1 | 15分以内 | 1時間毎 | 技術リーダー、関係チーム | Teams、メール |
| P2 | 1時間以内 | 4時間毎 | 担当チーム | Teams、メール |
| P3 | 翌営業日 | 日次 | 担当者 | メール、チケット |

#### 状況報告テンプレート
```markdown
## インシデント状況報告

**報告日時**: 2025-XX-XX HH:MM JST
**インシデントID**: INC-2025-XXX
**重要度**: P0/P1/P2/P3

### 現在の状況
- 影響範囲: [影響を受けているシステム/ユーザー]
- 現在のステータス: [調査中/封じ込め中/復旧中]
- 対応進捗: [完了した作業と現在の作業]

### 次のステップ
- [予定されている対応作業]
- 予想完了時間: [ETA]

### 必要なサポート
- [必要なリソース/承認事項]
```

### 外部コミュニケーション

#### 顧客向け通知
**P0/P1インシデントの場合**:
- 初回通知: 検知から2時間以内
- 更新: 4時間毎または重大な進展時
- 最終報告: 解決から24時間以内

#### 規制当局への報告
**データ漏洩の場合**:
- 個人情報保護委員会: 72時間以内
- 影響を受けた個人: 遅滞なく
- 報告書提出: 30日以内

## 事後活動

### ポストモーテム実施

#### タイムライン
- インシデント解決後48時間以内: 初期レビュー
- 1週間以内: 詳細分析とレポート作成
- 2週間以内: 改善計画の策定
- 1ヶ月以内: 改善実施と効果測定

#### ポストモーテムテンプレート
```markdown
# インシデントポストモーテム

## 概要
- インシデントID:
- 発生日時:
- 解決日時:
- 影響時間:
- 影響範囲:

## タイムライン
[時系列での出来事記載]

## 根本原因
### 技術的要因
### プロセス要因
### 人的要因

## 良かった点
[効果的だった対応]

## 改善点
[改善が必要な領域]

## アクションアイテム
| No | 内容 | 担当者 | 期限 | 状態 |
|----|------|--------|------|------|
| 1 | | | | |

## 学んだ教訓
[組織として学んだこと]
```

### 継続的改善

#### メトリクス追跡
- **MTTD (Mean Time To Detect)**: 検知までの平均時間
- **MTTR (Mean Time To Respond)**: 対応開始までの平均時間
- **MTTR (Mean Time To Recover)**: 復旧までの平均時間
- **インシデント再発率**: 同種インシデントの再発頻度
- **自動化率**: 自動対応の割合

#### 定期レビュー
- 月次: インシデント統計レビュー
- 四半期: プロセス改善レビュー
- 年次: 包括的セキュリティ評価

## 付録

### A. ツールとリソース

#### 必須ツール
- GitHub CLI (gh)
- Security scanning tools
- Log analysis tools
- Incident tracking system
- Communication platforms

#### 参考リソース
- [NIST Incident Response Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf)
- [SANS Incident Handler's Handbook](https://www.sans.org/white-papers/)
- [GitHub Security Best Practices](https://docs.github.com/security)

### B. 連絡先一覧

| 組織/役割 | 連絡先 | 備考 |
|-----------|--------|------|
| GitHub管理チーム | github@sas-com.com | 24/7対応 |
| セキュリティチーム | security@sas-com.com | 緊急時対応 |
| 法務部門 | legal@sas-com.com | コンプライアンス |
| 広報部門 | pr@sas-com.com | 外部対応 |
| JPCERT/CC | 03-6271-8901 | インシデント報告 |

### C. チェックリスト集

#### 初動対応チェックリスト
- [ ] インシデントの確認と記録
- [ ] 重要度レベルの判定
- [ ] 初期影響範囲の特定
- [ ] エスカレーションの実施
- [ ] 証拠保全の開始
- [ ] 初期封じ込めの実施
- [ ] ステークホルダーへの通知
- [ ] 対応体制の確立

#### 復旧前チェックリスト
- [ ] 脆弱性の完全な修正確認
- [ ] セキュリティ設定の検証
- [ ] バックアップの確認
- [ ] 監視体制の強化
- [ ] 復旧計画の承認
- [ ] ロールバック計画の準備
- [ ] コミュニケーション準備

### D. 演習シナリオ

#### シナリオ1: Secretの漏洩
- 開発者が誤って本番環境のAPIキーをコミット
- GitHub Secret Scanningで検知
- 影響範囲の特定と対応

#### シナリオ2: 不正アクセス
- 退職者のアカウントからの不正アクセス
- 複数リポジトリへの変更試行
- アクセス制御と監査

#### シナリオ3: サプライチェーン攻撃
- 依存パッケージへの悪意のあるコード混入
- Dependabotアラート
- 影響調査と対策

---

**改訂履歴**
- 2025-09-10: 初版作成
- [更新日]: [更新内容]

**次回レビュー予定**: 2026-03-10