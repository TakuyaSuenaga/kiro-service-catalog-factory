# AWS Service Catalog 自動化システム

AWS CDKを使用してAWSサービスカタログにポートフォリオとプロダクトを登録する最小限のシステムです。GitHub Actionsの手動実行により、既存のファイル構造からポートフォリオとプロダクトをAWSサービスカタログに登録します。

## 🚀 主な機能

- **手動実行**: GitHub Actionsを手動で実行してサービスカタログを更新
- **OIDC認証**: 長期間有効なアクセスキーを使わない安全な認証
- **AWS CDK**: Pythonを使用したシンプルな実装
- **既存ファイル活用**: 現在のportfolios/development/構造をそのまま使用
- **最小限の構成**: テストやエラーハンドリングを除外したシンプルな設計

## 📁 プロジェクト構造

```
├── .github/workflows/
│   └── service-catalog.yml         # 手動実行用GitHub Actions
├── cdk/
│   ├── app.py                      # CDKアプリケーションエントリーポイント
│   ├── service_catalog_stack.py    # Service Catalogスタック
│   ├── cdk.json                    # CDK設定ファイル
│   └── requirements.txt            # Python依存関係
└── portfolios/
    └── development/
        ├── portfolio.yaml          # ポートフォリオ設定
        └── ec2-instances/
            ├── product.yaml        # プロダクト設定
            └── v1.0.0/
                └── template.yaml   # CloudFormationテンプレート
```

## 🛠️ セットアップ手順

### 1. 前提条件

- AWS アカウント
- GitHub リポジトリ
- AWS CLI v2 以上

### 2. AWS OIDC設定

#### OIDCプロバイダーの作成

```bash
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

#### IAMロールの作成

```bash
# 信頼ポリシーファイルを作成
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
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:ref:refs/heads/main"
                }
            }
        }
    ]
}
EOF

# IAMロールを作成
aws iam create-role \
    --role-name GitHubActionsServiceCatalogRole \
    --assume-role-policy-document file://trust-policy.json

# 必要な権限ポリシーをアタッチ
aws iam attach-role-policy \
    --role-name GitHubActionsServiceCatalogRole \
    --policy-arn arn:aws:iam::aws:policy/ServiceCatalogAdminFullAccess

aws iam attach-role-policy \
    --role-name GitHubActionsServiceCatalogRole \
    --policy-arn arn:aws:iam::aws:policy/CloudFormationFullAccess
```

### 3. GitHub Secrets の設定

GitHubリポジトリの Settings > Secrets and variables > Actions で以下のシークレットを設定：

| シークレット名 | 値 | 説明 |
|---|---|---|
| `AWS_REGION` | `us-east-1` | AWSリージョン |
| `AWS_ROLE_ARN` | `arn:aws:iam::123456789012:role/GitHubActionsServiceCatalogRole` | IAMロールARN |

## 📝 使用方法

### 手動実行

1. GitHubリポジトリの「Actions」タブに移動
2. 「Deploy AWS Service Catalog」ワークフローを選択
3. 「Run workflow」ボタンをクリック
4. 「Run workflow」を再度クリックして実行

### ファイル構造

システムは以下の既存ファイルを使用します：

#### ポートフォリオ設定
```yaml
# portfolios/development/portfolio.yaml
name: "Development Portfolio"
description: "開発環境用のリソーステンプレート"
owner: "development-team@company.com"
```

#### プロダクト設定
```yaml
# portfolios/development/ec2-instances/product.yaml
name: "EC2 Instances"
description: "Ubuntu 24.04 ARM SSM対応EC2インスタンス"
owner: "infrastructure-team@company.com"
support_description: "インフラチームがサポートします"
support_email: "infrastructure-team@company.com"
support_url: "https://wiki.company.com/ec2-support"
```

#### CloudFormationテンプレート
```yaml
# portfolios/development/ec2-instances/v1.0.0/template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Ubuntu 24.04 ARM SSM対応EC2インスタンス'
# ... CloudFormationテンプレートの内容
```

## 🔧 ローカル開発

### CDKの実行

```bash
# CDKディレクトリに移動
cd cdk

# 依存関係をインストール
pip install -r requirements.txt

# CDKをデプロイ（AWS認証が必要）
cdk deploy
```

## 🚨 トラブルシューティング

### よくある問題

#### 1. OIDC認証エラー
**エラー**: `Error: Could not assume role with OIDC`

**解決方法**:
- IAMロールの信頼ポリシーを確認
- GitHub Secretsの値を確認
- リポジトリ名とブランチ名が正しいか確認

#### 2. CDKデプロイエラー
**エラー**: `CDK deploy failed`

**解決方法**:
- AWS認証情報を確認
- 必要なIAM権限があるか確認
- CloudFormationテンプレートの構文を確認

#### 3. ファイル読み込みエラー
**エラー**: `File not found`

**解決方法**:
- ファイルパスが正しいか確認
- ファイルが存在するか確認
- YAML構文が正しいか確認

## 📚 参考資料

- [AWS Service Catalog 開発者ガイド](https://docs.aws.amazon.com/servicecatalog/latest/dg/)
- [AWS CDK Python リファレンス](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [GitHub Actions での OIDC 使用](https://docs.github.com/ja/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

---

**注意**: このシステムは最小限の機能のみを提供します。本番環境での使用前に十分なテストを行ってください。