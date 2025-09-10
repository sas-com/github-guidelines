# インシデント対応トレーニングガイド

**エス・エー・エス株式会社**  
*セキュリティインシデント対応チーム向け包括的トレーニング資料*

## 目次

1. [トレーニング概要](#トレーニング概要)
2. [基礎知識編](#基礎知識編)
3. [実践スキル編](#実践スキル編)
4. [シミュレーション演習](#シミュレーション演習)
5. [ツール習熟](#ツール習熟)
6. [ケーススタディ](#ケーススタディ)
7. [認定プログラム](#認定プログラム)

## トレーニング概要

### 対象者
- インシデント対応チームメンバー
- 開発チームリーダー
- DevOpsエンジニア
- セキュリティ担当者

### 学習目標
1. インシデント対応の基本原則を理解する
2. 当社の対応プロセスを習得する
3. 必要なツールを使いこなせるようになる
4. 実際のインシデントに対応できる能力を身につける

### トレーニング構成
- **Phase 1**: 基礎知識（8時間）
- **Phase 2**: 実践スキル（16時間）
- **Phase 3**: シミュレーション（8時間）
- **Phase 4**: 認定試験（2時間）

## 基礎知識編

### Module 1: セキュリティインシデントの理解

#### 1.1 インシデントの定義と分類

**インシデントとは**
- セキュリティポリシー違反
- システムへの不正アクセス
- データの漏洩・改ざん
- サービスの妨害

**インシデントタイプ**
```
┌─────────────────────────────────┐
│      インシデント分類体系         │
├─────────────────────────────────┤
│ 1. データ侵害                   │
│   - 個人情報漏洩               │
│   - 企業機密流出               │
│   - 認証情報露出               │
│                                 │
│ 2. システム侵害                 │
│   - マルウェア感染             │
│   - 不正アクセス               │
│   - 権限昇格                   │
│                                 │
│ 3. サービス妨害                 │
│   - DDoS攻撃                   │
│   - リソース枯渇               │
│   - システム破壊               │
│                                 │
│ 4. ポリシー違反                 │
│   - 内部不正                   │
│   - 設定ミス                   │
│   - コンプライアンス違反       │
└─────────────────────────────────┘
```

#### 1.2 インシデントの影響度評価

**ビジネスインパクト分析**
- 財務的損失
- レピュテーション損害
- 法的責任
- 運用への影響

**リスクマトリックス**
```
影響度
  ↑
高│ P2  P1  P0
  │
中│ P3  P2  P1
  │
低│ P3  P3  P2
  └──────────→
    低  中  高
    発生可能性
```

### Module 2: 法的・規制要件

#### 2.1 日本の法規制

**個人情報保護法**
- 漏洩時の報告義務（72時間以内）
- 本人への通知義務
- 個人情報保護委員会への報告

**サイバーセキュリティ基本法**
- 重要インフラ事業者の責務
- 情報共有の推進
- 人材育成の義務

#### 2.2 国際規格・標準

**ISO/IEC 27035**
- インシデント管理の国際標準
- PDCAサイクルの適用
- 継続的改善

**NIST Framework**
- 識別（Identify）
- 防御（Protect）
- 検知（Detect）
- 対応（Respond）
- 復旧（Recover）

### Module 3: 組織体制と役割

#### 3.1 インシデント対応体制

```
        ┌──────────────────┐
        │  経営層/CTO      │
        └────────┬─────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
┌─────▼──────┐      ┌──────▼─────┐
│インシデント │      │ 広報・法務  │
│コマンダー   │      │   チーム    │
└─────┬──────┘      └────────────┘
      │
┌─────▼──────────────────┐
│  技術対応チーム         │
│  - セキュリティ担当     │
│  - 開発チーム           │
│  - インフラチーム       │
└─────────────────────────┘
```

#### 3.2 各役割の責任

**インシデントコマンダー**
- 全体指揮・意思決定
- リソース配分
- エスカレーション判断

**技術対応チーム**
- 技術的調査・分析
- 封じ込め・復旧作業
- 証拠収集・保全

**広報・法務チーム**
- 対外コミュニケーション
- 法的対応
- コンプライアンス確保

## 実践スキル編

### Module 4: 検知と初動対応

#### 4.1 アラート評価

**評価チェックリスト**
```python
def evaluate_alert(alert):
    """アラート評価プロセス"""
    
    # 1. 真正性の確認
    if not verify_alert_source(alert):
        return "False Positive"
    
    # 2. 影響範囲の特定
    scope = determine_scope(alert)
    
    # 3. 緊急度の判定
    severity = calculate_severity(
        data_sensitivity=scope['data_type'],
        user_impact=scope['affected_users'],
        system_criticality=scope['systems']
    )
    
    # 4. 対応優先度の決定
    priority = assign_priority(severity, scope)
    
    return {
        'valid': True,
        'severity': severity,
        'priority': priority,
        'action_required': get_required_actions(priority)
    }
```

#### 4.2 初動対応手順

**Golden Hour対応**（最初の1時間）
1. アラート確認（5分）
2. 影響範囲特定（10分）
3. 封じ込め実施（15分）
4. 証拠保全開始（10分）
5. 関係者通知（10分）
6. 詳細調査開始（10分）

### Module 5: 調査と分析技術

#### 5.1 ログ分析

**分析対象ログ**
- GitHub Audit Logs
- Application Logs
- System Logs
- Network Logs
- Security Tool Logs

**分析手法**
```bash
# 異常パターンの検出
grep -E "unauthorized|denied|failed|error" /var/log/auth.log | \
  awk '{print $1, $2, $3, $11}' | \
  sort | uniq -c | sort -rn

# タイムライン作成
for log in $(ls /var/log/*.log); do
  echo "=== $log ===" 
  grep "2025-09-10" $log | head -20
done | less

# 相関分析
correlate_events() {
  local timewindow=$1
  local pattern=$2
  
  find /var/log -name "*.log" -exec grep -l "$pattern" {} \; | \
  while read logfile; do
    echo "Found in: $logfile"
    grep -C 5 "$pattern" "$logfile"
  done
}
```

#### 5.2 フォレンジック分析

**メモリフォレンジック**
```python
# Volatility Frameworkの使用例
import volatility

def analyze_memory_dump(dump_file):
    """メモリダンプ分析"""
    
    # プロセスリスト取得
    processes = vol_cmd("pslist", dump_file)
    
    # ネットワーク接続確認
    connections = vol_cmd("netscan", dump_file)
    
    # 悪意のあるプロセス検出
    suspicious = detect_malicious_processes(processes)
    
    return {
        'processes': processes,
        'connections': connections,
        'suspicious': suspicious
    }
```

### Module 6: 封じ込めと根絶

#### 6.1 封じ込め戦略

**短期封じ込め**
- アカウント無効化
- ネットワーク隔離
- プロセス停止
- アクセス制限

**長期封じ込め**
- パッチ適用
- 設定変更
- ルール更新
- システム再構築

#### 6.2 マルウェア除去

```bash
#!/bin/bash
# マルウェア除去スクリプト

# 1. 悪意のあるファイルの特定
find / -type f -name "*.suspicious" -o -name "*.malware"

# 2. プロセスの停止
for pid in $(ps aux | grep malicious | awk '{print $2}'); do
  kill -9 $pid
done

# 3. 自動起動の無効化
systemctl disable malicious.service
rm -f /etc/systemd/system/malicious.service

# 4. ファイルの隔離
mkdir -p /quarantine
mv /path/to/malicious/file /quarantine/

# 5. システムスキャン
clamscan -r --remove /
```

## シミュレーション演習

### 演習1: ランサムウェア対応

**シナリオ**
```
時刻: 月曜日 09:15
状況: 複数のサーバーでファイルが暗号化されている
影響: 本番データベースサーバー3台
発見: 開発者がアクセス不能を報告
```

**対応手順**
1. **即座の対応**（0-15分）
   - 影響システムの隔離
   - バックアップシステムの保護
   - 経営層への報告

2. **調査と分析**（15-60分）
   - 感染経路の特定
   - 影響範囲の確認
   - 攻撃者の要求確認

3. **復旧計画**（60-120分）
   - バックアップからの復元
   - クリーンシステムの準備
   - 段階的復旧

### 演習2: 内部不正調査

**シナリオ**
```
時刻: 金曜日 17:30
状況: 退職予定者による大量データダウンロード検知
影響: 顧客データベースへのアクセス
証拠: アクセスログに異常なクエリ
```

**調査プロセス**
```python
def investigate_insider_threat(user_id, timeframe):
    """内部脅威調査"""
    
    evidence = {
        'access_logs': [],
        'file_operations': [],
        'network_activity': [],
        'email_activity': []
    }
    
    # GitHubアクティビティ
    github_activity = check_github_activity(user_id, timeframe)
    
    # ファイルアクセス
    file_access = check_file_access(user_id, timeframe)
    
    # データエクスポート
    data_exports = check_data_exports(user_id, timeframe)
    
    # 異常パターン検出
    anomalies = detect_anomalies(
        github_activity,
        file_access,
        data_exports
    )
    
    return compile_investigation_report(evidence, anomalies)
```

### 演習3: サプライチェーン攻撃

**シナリオ**
```
時刻: 水曜日 14:00
状況: 依存パッケージに悪意のあるコード発見
影響: 10個のマイクロサービス
発見: Dependabotアラート
```

**対応アクション**
1. 影響調査
2. 脆弱なバージョンの特定
3. 緊急パッチの作成
4. ロールアウト計画
5. 監視強化

## ツール習熟

### 必須ツール一覧

#### コマンドラインツール
```bash
# GitHub CLI
gh auth login
gh issue create --title "Security Incident" --label security
gh api /orgs/sas-com/audit-log

# 証拠収集
./scripts/incident-tools/evidence-collector.sh \
  --incident-id INC-001 \
  --priority P0 \
  --type all

# インシデント管理
python scripts/incident-tools/incident-tracker.py create \
  --severity P1 \
  --type unauthorized_access \
  --title "Suspicious login activity"
```

#### 分析ツール
- **Wireshark**: ネットワークトラフィック分析
- **Volatility**: メモリフォレンジック
- **YARA**: マルウェアパターンマッチング
- **ELK Stack**: ログ分析・可視化

### ツール実習

#### Lab 1: GitHub セキュリティ機能

```bash
# Secret Scanningの設定
gh api \
  --method PUT \
  /repos/sas-com/test-repo/secret-scanning \
  -f enabled=true

# Code Scanningの有効化
gh api \
  --method PUT \
  /repos/sas-com/test-repo/code-scanning \
  -f tool=CodeQL \
  -f enabled=true

# Dependabotの設定
cat > .github/dependabot.yml << EOF
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "daily"
    open-pull-requests-limit: 10
EOF
```

#### Lab 2: ログ分析実習

```python
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def analyze_security_logs(log_file):
    """セキュリティログ分析"""
    
    # ログ読み込み
    df = pd.read_csv(log_file)
    
    # 時系列分析
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # 異常検出
    anomalies = detect_anomalies(df)
    
    # 可視化
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # イベント頻度
    df.resample('1H').size().plot(ax=axes[0, 0])
    axes[0, 0].set_title('Event Frequency')
    
    # エラー率
    error_rate = df[df['level'] == 'ERROR'].resample('1H').size()
    error_rate.plot(ax=axes[0, 1], color='red')
    axes[0, 1].set_title('Error Rate')
    
    # ユーザー別アクティビティ
    df.groupby('user')['action'].count().plot(
        kind='bar', ax=axes[1, 0]
    )
    axes[1, 0].set_title('User Activity')
    
    # 異常スコア
    anomalies['score'].plot(ax=axes[1, 1], color='orange')
    axes[1, 1].set_title('Anomaly Score')
    
    plt.tight_layout()
    plt.savefig('security_analysis.png')
    
    return anomalies
```

## ケーススタディ

### Case 1: GitHub Enterprise Serverへの不正アクセス

**背景**
- 2025年8月、異常なAPI呼び出しを検知
- 複数のプライベートリポジトリへのアクセス
- 海外IPアドレスからの接続

**対応プロセス**
1. **検知**（T+0分）
   - SIEM システムがアラート生成
   - APIレート制限を超過

2. **初動**（T+15分）
   - 該当IPアドレスをブロック
   - 影響を受けたトークンを無効化

3. **調査**（T+30分）
   - アクセスログの詳細分析
   - 漏洩データの特定

4. **封じ込め**（T+60分）
   - 全APIトークンのローテーション
   - 2FA必須化

5. **復旧**（T+120分）
   - 正規ユーザーのアクセス復旧
   - 監視強化

**教訓**
- APIトークンの定期的なローテーション
- 異常検知ルールの調整
- インシデント対応の自動化

### Case 2: サプライチェーン攻撃（npm パッケージ）

**背景**
- 人気npmパッケージに悪意のあるコード
- 自動ビルドプロセスで実行
- 環境変数を外部サーバーに送信

**タイムライン**
```
Day 0, 10:00 - Dependabotアラート受信
Day 0, 10:15 - 影響範囲の調査開始
Day 0, 10:30 - 15個のサービスが影響を受けていることを確認
Day 0, 11:00 - 緊急パッチの作成開始
Day 0, 14:00 - パッチ適用完了
Day 0, 16:00 - 全システム正常動作確認
Day 1, 10:00 - ポストモーテム実施
```

**対策実装**
- 依存関係の固定化
- プライベートレジストリの使用
- ビルド環境の隔離

## 認定プログラム

### 認定レベル

#### Level 1: Responder（初級）
- 基本的なインシデント対応
- ツールの基本操作
- 手順書に従った対応

**必要スキル**
- インシデント分類
- 基本的な調査
- 証拠収集
- レポート作成

#### Level 2: Analyst（中級）
- 複雑なインシデントの分析
- 根本原因分析
- 改善提案

**必要スキル**
- 高度なログ分析
- フォレンジック
- マルウェア分析
- 脅威インテリジェンス

#### Level 3: Commander（上級）
- インシデント指揮
- 戦略的判断
- チーム管理

**必要スキル**
- リーダーシップ
- 危機管理
- ステークホルダー管理
- 事業継続計画

### 認定試験

#### 試験構成
- **筆記試験**（60分）
  - 多肢選択：30問
  - 記述式：5問

- **実技試験**（120分）
  - シミュレーション対応
  - ツール操作
  - レポート作成

#### 評価基準
```
合格ライン: 80%以上

配点:
- 知識理解: 30%
- 実践スキル: 40%
- 判断力: 20%
- コミュニケーション: 10%
```

### 継続教育

#### 年間トレーニング計画

**Q1: 基礎強化**
- セキュリティ基礎
- 脅威動向
- 新ツール導入

**Q2: 実践演習**
- Table Top Exercise
- Red Team演習
- インシデント対応訓練

**Q3: 専門深化**
- フォレンジック
- マルウェア解析
- 脅威ハンティング

**Q4: 総合演習**
- 大規模演習
- 外部連携訓練
- 年次評価

### トレーニングリソース

#### 推奨書籍
- "Incident Response & Computer Forensics" (McGraw-Hill)
- "The Practice of Network Security Monitoring" (No Starch Press)
- "Applied Incident Response" (Wiley)

#### オンラインコース
- SANS FOR508: Advanced Incident Response
- Coursera: Incident Response and Forensics
- GitHub Learning Lab: Security courses

#### コミュニティ
- JPCERT/CC
- ISAC (Information Sharing and Analysis Center)
- GitHub Security Community

---

**改訂履歴**
- 2025-09-10: 初版作成

**次回更新予定**: 2026-01-10