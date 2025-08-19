# トラブルシューティングガイド

このガイドでは、AWS Service Catalog 自動化システムでよく発生する問題とその解決方法について説明します。

## 🚨 緊急時の対応

### システム全体が動作しない場合

1. **GitHub Actions の確認**
   ```bash
   # リポジトリのActionsタブで最新のワークフロー実行を確認
   # エラーログを詳細に確認
   ```

2. **AWS認証の確認**
   ```bash
   # ローカルでAWS認証をテスト
   aws sts get-caller-identity
   ```

3. **緊急停止**
   ```bash
   # GitHub Actionsワークフローを無効化
   # .github/workflows/service-catalog.yml を一時的にリネーム
   mv .github/workflows/service-catalog.yml .github/workflows/service-catalog.yml.disabled
   git add .
   git commit -m "Temporarily disable workflow for emergency"
   git push
   ```

## 🔐 認証・権限関連の問題

### 1. OIDC認証エラー

#### エラーメッセージ例
```
Error: Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity
```

#### 原因と解決方法

**原因1: IAMロールの信頼ポリシーが正しくない**

```bash
# 現在の信頼ポリシーを確認
aws iam get-role --role-name GitHubActionsServiceCatalogRole --query 'Role.AssumeRolePolicyDocument'

# 正しい信頼ポリシーに更新
cat > trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*"
                }
            }
        }
    ]
}
EOF

aws iam update-assume-role-policy \
    --role-name GitHubActionsServiceCatalogRole \
    --policy-document file://trust-policy.json
```

**原因2: GitHub Secretsの値が間違っている**

GitHub リポジトリの Settings > Secrets and variables > Actions で以下を確認：

| シークレット名 | 確認方法 |
|---|---|
| `AWS_ACCOUNT_ID` | `aws sts get-caller-identity --query Account --output text` |
| `AWS_REGION` | 有効なAWSリージョン名（例：`us-east-1`） |
| `AWS_ROLE_ARN` | `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsServiceCatalogRole` |

**原因3: OIDCプロバイダーが存在しない**

```bash
# OIDCプロバイダーの確認
aws iam list-open-id-connect-providers

# 存在しない場合は作成
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. AWS CLI権限エラー

#### エラーメッセージ例
```
User: arn:aws:sts::123456789012:assumed-role/GitHubActionsServiceCatalogRole/GitHubActions is not authorized to perform: servicecatalog:CreatePortfolio
```

#### 解決方法

```bash
# 必要な権限ポリシーをアタッチ
aws iam attach-role-policy \
    --role-name GitHubActionsServiceCatalogRole \
    --policy-arn arn:aws:iam::aws:policy/ServiceCatalogAdminFullAccess

aws iam attach-role-policy \
    --role-name GitHubActionsServiceCatalogRole \
    --policy-arn arn:aws:iam::aws:policy/CloudFormationFullAccess

# カスタムポリシーが必要な場合
cat > service-catalog-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "servicecatalog:*",
                "cloudformation:ValidateTemplate",
                "cloudformation:DescribeStacks",
                "iam:ListRoles",
                "iam:PassRole"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam create-policy \
    --policy-name ServiceCatalogAutomationPolicy \
    --policy-document file://service-catalog-policy.json

aws iam attach-role-policy \
    --role-name GitHubActionsServiceCatalogRole \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/ServiceCatalogAutomationPolicy
```

## 📄 設定ファイル関連の問題

### 1. YAML構文エラー

#### エラーメッセージ例
```
YAML解析エラー in portfolios/development/portfolio.yaml: found character '\t' that cannot start any token
```

#### 解決方法

```bash
# YAMLファイルの構文チェック
python3 -c "import yaml; yaml.safe_load(open('portfolios/development/portfolio.yaml'))"

# 一般的な問題と修正
# 1. タブ文字の使用（スペースに変更）
sed -i 's/\t/  /g' portfolios/development/portfolio.yaml

# 2. 不正な文字エンコーディング
file portfolios/development/portfolio.yaml  # エンコーディング確認
iconv -f ISO-8859-1 -t UTF-8 portfolios/development/portfolio.yaml > temp.yaml
mv temp.yaml portfolios/development/portfolio.yaml

# 3. YAML構文の検証
yamllint portfolios/development/portfolio.yaml  # yamllintがインストールされている場合
```

### 2. 必須フィールドエラー

#### エラーメッセージ例
```
必須フィールド 'owner' が見つかりません in portfolios/development/portfolio.yaml
```

#### 解決方法

**portfolio.yaml の必須フィールド**:
```yaml
name: "Portfolio Name"                    # 必須
description: "Portfolio Description"      # 必須
owner: "owner@company.com"               # 必須（@を含む有効なメール）
```

**product.yaml の必須フィールド**:
```yaml
name: "Product Name"                     # 必須
description: "Product Description"       # 必須
owner: "owner@company.com"              # 必須（@を含む有効なメール）
support_description: "Support info"     # 必須
support_email: "support@company.com"    # 必須（@を含む有効なメール）
support_url: "https://support.com"     # 必須（http://またはhttps://で始まる）
```

### 3. メールアドレス形式エラー

#### エラーメッセージ例
```
owner フィールドは有効なメールアドレスである必要があります
```

#### 解決方法

```bash
# 有効なメールアドレス形式の例
owner: "team@company.com"           # ✓ 正しい
owner: "user.name@domain.co.jp"     # ✓ 正しい
owner: "team"                       # ✗ 間違い（@がない）
owner: "@company.com"               # ✗ 間違い（ローカル部がない）
```

## 🏗️ CloudFormation関連の問題

### 1. テンプレート検証エラー

#### エラーメッセージ例
```
Template format error: JSON not well-formed. (Service: AmazonCloudFormation; Status Code: 400)
```

#### 解決方法

```bash
# ローカルでテンプレート検証
aws cloudformation validate-template \
    --template-body file://portfolios/development/ec2-instances/v1.0.0/template.yaml

# 一般的な問題と修正
# 1. YAML構文エラー
python3 -c "import yaml; print(yaml.safe_load(open('portfolios/development/ec2-instances/v1.0.0/template.yaml')))"

# 2. CloudFormation固有の構文エラー
# - 不正な関数名（!Ref, !GetAtt など）
# - 存在しないリソースタイプ
# - 循環参照

# 3. テンプレートの最小要件確認
cat > minimal-template.yaml << EOF
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Minimal template'
Resources:
  DummyResource:
    Type: AWS::CloudFormation::WaitConditionHandle
EOF
```

### 2. リソース作成エラー

#### エラーメッセージ例
```
Resource creation failed: The specified key pair 'my-key' does not exist
```

#### 解決方法

```bash
# 1. パラメータの確認
# テンプレートで使用されているパラメータが実際に存在するか確認

# 2. リソースの依存関係確認
# DependsOn属性や!Refで参照されるリソースが正しく定義されているか

# 3. リージョン固有のリソース確認
# AMI ID、キーペア名などがデプロイ先リージョンで有効か

# 4. 権限の確認
# CloudFormationが必要なリソースを作成する権限があるか
```

### 3. スタック更新エラー

#### エラーメッセージ例
```
No updates are to be performed
```

#### 解決方法

```bash
# 1. 実際に変更があるか確認
git diff HEAD~1 portfolios/development/ec2-instances/v1.0.0/template.yaml

# 2. CloudFormationの変更検知
# 一部の変更（タグ、説明など）はCloudFormationで検知されない場合がある

# 3. 強制更新
# テンプレートに意味のある変更を加える（パラメータのデフォルト値変更など）
```

## 🔄 GitHub Actions関連の問題

### 1. ワークフローがトリガーされない

#### 原因と解決方法

**原因1: パストリガーの設定**

```yaml
# .github/workflows/service-catalog.yml
on:
  push:
    branches: [ main ]
    paths:
      - 'portfolios/**'  # portfoliosフォルダの変更のみトリガー
```

**原因2: ブランチ保護ルール**

```bash
# mainブランチに直接プッシュできない場合
# プルリクエスト経由でマージする
```

**原因3: ワークフローファイルの構文エラー**

```bash
# GitHub Actionsの構文チェック
# リポジトリのActionsタブでエラーメッセージを確認
```

### 2. ワークフローが途中で失敗する

#### デバッグ方法

```yaml
# デバッグ用ステップを追加
- name: Debug Environment
  run: |
    echo "Current directory: $(pwd)"
    echo "Files in portfolios:"
    find portfolios/ -type f -name "*.yaml" | head -10
    echo "Environment variables:"
    env | grep AWS
    echo "Git changes:"
    git diff --name-only HEAD~1 HEAD
```

### 3. 並列実行の問題

#### エラーメッセージ例
```
Another workflow is currently running
```

#### 解決方法

```yaml
# .github/workflows/service-catalog.yml
concurrency:
  group: service-catalog-${{ github.ref }}
  cancel-in-progress: true  # 新しい実行で古い実行をキャンセル
```

## 🐛 スクリプト実行エラー

### 1. Python依存関係エラー

#### エラーメッセージ例
```
ModuleNotFoundError: No module named 'yaml'
```

#### 解決方法

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 仮想環境の使用（推奨）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. シェルスクリプト権限エラー

#### エラーメッセージ例
```
Permission denied: scripts/deploy-catalog.sh
```

#### 解決方法

```bash
# 実行権限を付与
chmod +x scripts/*.sh

# 権限の確認
ls -la scripts/
```

### 3. jqコマンドエラー

#### エラーメッセージ例
```
jq: command not found
```

#### 解決方法

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# CentOS/RHEL
sudo yum install jq

# Windows (WSL)
sudo apt-get install jq
```

## 🌐 ネットワーク関連の問題

### 1. AWS API接続エラー

#### エラーメッセージ例
```
Could not connect to the endpoint URL: "https://servicecatalog.us-east-1.amazonaws.com/"
```

#### 解決方法

```bash
# 1. ネットワーク接続の確認
ping servicecatalog.us-east-1.amazonaws.com

# 2. プロキシ設定の確認
echo $HTTP_PROXY
echo $HTTPS_PROXY

# 3. AWS CLIの設定確認
aws configure list
aws configure list-profiles

# 4. リージョンの確認
aws configure get region
```

### 2. タイムアウトエラー

#### エラーメッセージ例
```
Read timeout on endpoint URL
```

#### 解決方法

```bash
# AWS CLIのタイムアウト設定
aws configure set cli_read_timeout 300
aws configure set cli_connect_timeout 60

# 環境変数での設定
export AWS_CLI_READ_TIMEOUT=300
export AWS_CLI_CONNECT_TIMEOUT=60
```

## 📊 パフォーマンス関連の問題

### 1. 大量ファイル処理の遅延

#### 症状
- デプロイに異常に時間がかかる
- GitHub Actionsがタイムアウトする

#### 解決方法

```bash
# 1. 並列処理数の調整
export PARALLEL_JOBS=2  # デフォルトは3

# 2. 変更検知の最適化
# 不要なファイルを.gitignoreに追加

# 3. ファイルサイズの確認
find portfolios/ -name "*.yaml" -size +1M  # 1MB以上のファイル
```

### 2. メモリ不足エラー

#### エラーメッセージ例
```
MemoryError: Unable to allocate array
```

#### 解決方法

```bash
# 1. 大きなテンプレートファイルの分割
# 2. S3を使用した大きなテンプレートの管理
export S3_BUCKET=your-template-bucket

# 3. GitHub Actionsのリソース制限確認
# 無料プランの場合は制限あり
```

## 🔍 デバッグとログ分析

### 1. 詳細ログの有効化

```bash
# ローカル実行時
export LOG_LEVEL=DEBUG
scripts/deploy-catalog.sh deploy portfolios/development

# GitHub Actions
# ワークフローファイルで環境変数を設定
env:
  LOG_LEVEL: DEBUG
```

### 2. ログファイルの分析

```bash
# GitHub Actionsログのダウンロード
# リポジトリのActionsタブから実行結果をダウンロード

# ローカルログの確認
tail -f /tmp/service-catalog-deploy.log  # ログファイルがある場合
```

### 3. ステップバイステップデバッグ

```bash
# 1. 設定ファイルの検証のみ
scripts/deploy-catalog.sh validate

# 2. DRY_RUNモードでの実行
DRY_RUN=1 scripts/deploy-catalog.sh deploy

# 3. 個別コンポーネントのテスト
scripts/manage-portfolio.sh create portfolios/development
scripts/manage-product.sh create portfolios/development/ec2-instances "Development Portfolio"
```

## 🆘 サポートとヘルプ

### 1. ログ情報の収集

問題報告時に以下の情報を収集してください：

```bash
# システム情報
uname -a
aws --version
python3 --version
jq --version

# AWS設定
aws configure list
aws sts get-caller-identity

# Git情報
git log --oneline -5
git status

# ファイル構造
find portfolios/ -name "*.yaml" | head -20
```

### 2. 問題の再現手順

1. 具体的な操作手順
2. エラーメッセージの全文
3. 期待される結果と実際の結果
4. 環境情報（OS、ブラウザなど）

### 3. 緊急時の連絡先

- GitHub Issues: プロジェクトリポジトリのIssuesタブ
- 社内チャット: #infrastructure-support
- メール: infrastructure-team@company.com

## 📋 チェックリスト

### デプロイ前チェック

- [ ] 設定ファイルの構文確認
- [ ] CloudFormationテンプレートの検証
- [ ] AWS認証の確認
- [ ] GitHub Secretsの設定確認
- [ ] テスト環境での動作確認

### エラー発生時チェック

- [ ] エラーメッセージの詳細確認
- [ ] ログファイルの分析
- [ ] 最近の変更内容の確認
- [ ] 類似問題の過去事例確認
- [ ] 必要に応じてロールバック実行

### 復旧後チェック

- [ ] 全機能の動作確認
- [ ] 監視アラートの解除
- [ ] 問題の根本原因分析
- [ ] 再発防止策の実装
- [ ] ドキュメントの更新

このトラブルシューティングガイドを参考に、問題の迅速な解決と予防に努めてください。