# AWS Service Catalog 自動化システム

AWSサービスカタログへのプロダクト登録を自動化するGitHub Actionsワークフローシステムです。CloudFormationテンプレートをバージョン管理し、OIDC認証を使用してAWSに安全に接続し、サービスカタログのポートフォリオとプロダクトを自動的に管理します。

## 🚀 主な機能

- **自動デプロイ**: GitHubリポジトリへのプッシュで自動的にAWSサービスカタログにプロダクトを登録
- **バージョン管理**: フォルダ構造でプロダクトのバージョンを管理
- **OIDC認証**: 長期間有効なアクセスキーを使わない安全な認証
- **変更検知**: 変更されたポートフォリオ・プロダクトのみを自動デプロイ
- **エラーハンドリング**: 詳細なログ出力と適切なエラー処理
- **日本語サポート**: 完全な日本語ドキュメントとログメッセージ

## 📁 プロジェクト構造

```
├── .github/workflows/
│   └── service-catalog.yml          # GitHub Actionsワークフロー
├── portfolios/                      # ポートフォリオ定義
│   └── [ポートフォリオ名]/
│       ├── portfolio.yaml           # ポートフォリオ設定
│       └── [プロダクト名]/
│           ├── product.yaml         # プロダクト設定
│           └── [バージョン]/
│               └── template.yaml    # CloudFormationテンプレート
├── scripts/                         # 管理スクリプト
│   ├── config_parser.py            # 設定ファイル解析
│   ├── detect-changes.py           # 変更検知
│   ├── manage-portfolio.sh         # ポートフォリオ管理
│   ├── manage-product.sh           # プロダクト管理
│   └── deploy-catalog.sh           # 統合デプロイ
├── cdk/                            # AWS CDK バックアップ実装
├── templates/                      # 設定ファイルテンプレート
└── tests/                          # 単体テスト
```

## 🛠️ セットアップ手順

### 1. 前提条件

- AWS アカウント
- GitHub リポジトリ
- AWS CLI v2 以上
- Python 3.8 以上
- jq コマンド

### 2. AWS 設定

#### OIDC プロバイダーの設定

```bash
# AWS CLI でOIDCプロバイダーを作成
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

#### IAM ロールの作成

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
| `AWS_ACCOUNT_ID` | `123456789012` | AWSアカウントID |
| `AWS_ROLE_ARN` | `arn:aws:iam::123456789012:role/GitHubActionsServiceCatalogRole` | IAMロールARN |

### 4. リポジトリのクローンと初期設定

```bash
# リポジトリをクローン
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# 依存関係をインストール
pip install -r requirements.txt

# スクリプトに実行権限を付与
chmod +x scripts/*.sh
```

## 📝 使用方法

### ポートフォリオの作成

1. `portfolios/` ディレクトリに新しいポートフォリオフォルダを作成
2. `portfolio.yaml` ファイルを作成

```yaml
# portfolios/development/portfolio.yaml
name: "Development Portfolio"
description: "開発環境用のリソーステンプレート"
owner: "development-team@company.com"
```

### プロダクトの作成

1. ポートフォリオフォルダ内にプロダクトフォルダを作成
2. `product.yaml` ファイルを作成

```yaml
# portfolios/development/ec2-instances/product.yaml
name: "EC2 Instances"
description: "Ubuntu 24.04 ARM SSM対応EC2インスタンス"
owner: "infrastructure-team@company.com"
support_description: "インフラチームがサポートします"
support_email: "infrastructure-team@company.com"
support_url: "https://wiki.company.com/ec2-support"
```

### バージョンの追加

1. プロダクトフォルダ内にバージョンフォルダを作成（例：`v1.0.0`）
2. CloudFormationテンプレート `template.yaml` を配置

```yaml
# portfolios/development/ec2-instances/v1.0.0/template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Ubuntu 24.04 ARM SSM対応EC2インスタンス'

Parameters:
  InstanceType:
    Type: String
    Default: t4g.micro
    Description: EC2インスタンスタイプ

Resources:
  EC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0c02fb55956c7d316  # Ubuntu 24.04 ARM
      InstanceType: !Ref InstanceType
      IamInstanceProfile: !Ref InstanceProfile
      # ... その他の設定
```

### 自動デプロイ

ファイルをコミットしてプッシュすると、GitHub Actionsが自動的に実行されます：

```bash
git add portfolios/
git commit -m "Add new EC2 instances product"
git push origin main
```

## 🔧 手動実行

### ローカルでの検証

```bash
# 設定ファイルの検証
python3 scripts/config_parser.py validate-portfolio portfolios/development/portfolio.yaml
python3 scripts/config_parser.py validate-product portfolios/development/ec2-instances/product.yaml
python3 scripts/config_parser.py validate-template portfolios/development/ec2-instances/v1.0.0/template.yaml

# 変更検知のテスト
python3 scripts/detect-changes.py

# 全体の検証
scripts/deploy-catalog.sh validate portfolios/development
```

### 手動デプロイ

```bash
# DRY_RUNモードでテスト
DRY_RUN=1 scripts/deploy-catalog.sh deploy portfolios/development

# 実際のデプロイ
scripts/deploy-catalog.sh deploy portfolios/development

# 特定のポートフォリオのみ
scripts/manage-portfolio.sh create portfolios/development

# 特定のプロダクトのみ
scripts/manage-product.sh create portfolios/development/ec2-instances "Development Portfolio"
```

## 🧪 テスト実行

```bash
# 全テストの実行
python3 tests/run_tests.py

# 特定のテストの実行
python3 tests/run_tests.py test_config_parser.TestConfigParser.test_load_yaml_file_valid

# テスト依存関係のインストール
pip install -r tests/requirements.txt
```

## 📊 監視とログ

### GitHub Actions ログ

- GitHub リポジトリの Actions タブでワークフロー実行状況を確認
- 各ステップの詳細ログを確認可能
- エラー時は詳細なスタックトレースを表示

### AWS コンソールでの確認

1. **Service Catalog コンソール**
   - ポートフォリオ一覧でデプロイされたポートフォリオを確認
   - プロダクト詳細でバージョン履歴を確認

2. **CloudFormation コンソール**
   - テンプレートの検証結果を確認
   - スタック作成時のエラーログを確認

### ローカルでの状況確認

```bash
# デプロイ状況の確認
scripts/deploy-catalog.sh status

# 特定のポートフォリオの状況
scripts/deploy-catalog.sh status "Development Portfolio"

# ポートフォリオ一覧
scripts/manage-portfolio.sh list

# プロダクト一覧
scripts/manage-product.sh list "Development Portfolio"
```

## 🔒 セキュリティ考慮事項

### 認証・認可

- **OIDC認証**: 長期間有効なアクセスキーを使用しない
- **最小権限**: 必要最小限のIAM権限のみを付与
- **リポジトリ制限**: 特定のリポジトリからのみアクセス可能

### テンプレート検証

- **事前検証**: デプロイ前にCloudFormationテンプレートを検証
- **構文チェック**: YAML構文とCloudFormation仕様の確認
- **リソース制限**: 危険なリソース作成の防止

### ログ管理

- **機密情報の保護**: ログに機密情報を出力しない
- **監査ログ**: すべての操作を記録
- **エラー情報**: 適切なマスキングを実施

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. OIDC認証エラー

**エラー**: `Error: Could not assume role with OIDC`

**原因**: 
- IAMロールの信頼ポリシーが正しく設定されていない
- GitHub Secretsの値が間違っている

**解決方法**:
```bash
# IAMロールの信頼ポリシーを確認
aws iam get-role --role-name GitHubActionsServiceCatalogRole

# GitHub Secretsの値を確認
# - AWS_ACCOUNT_ID: 正しいアカウントID
# - AWS_ROLE_ARN: 正しいロールARN
# - AWS_REGION: 有効なリージョン
```

#### 2. CloudFormationテンプレートエラー

**エラー**: `Template format error: JSON not well-formed`

**原因**: 
- YAML構文エラー
- CloudFormation仕様違反

**解決方法**:
```bash
# ローカルでテンプレートを検証
python3 scripts/config_parser.py validate-template portfolios/development/ec2-instances/v1.0.0/template.yaml

# AWS CLIでの検証
aws cloudformation validate-template --template-body file://portfolios/development/ec2-instances/v1.0.0/template.yaml
```

#### 3. 権限エラー

**エラー**: `User is not authorized to perform: servicecatalog:CreatePortfolio`

**原因**: IAMロールに必要な権限がない

**解決方法**:
```bash
# 必要な権限ポリシーをアタッチ
aws iam attach-role-policy \
    --role-name GitHubActionsServiceCatalogRole \
    --policy-arn arn:aws:iam::aws:policy/ServiceCatalogAdminFullAccess
```

#### 4. リソース競合エラー

**エラー**: `Portfolio with name 'Development Portfolio' already exists`

**原因**: 同名のポートフォリオが既に存在

**解決方法**:
- システムは自動的に更新モードに切り替わります
- 手動で確認する場合: `scripts/manage-portfolio.sh check "Development Portfolio"`

#### 5. ネットワークエラー

**エラー**: `Connection timeout`

**原因**: 
- AWSサービスへの接続問題
- GitHub Actionsの一時的な問題

**解決方法**:
- ワークフローを再実行
- AWS Status ページで障害情報を確認
- 必要に応じてタイムアウト値を調整

### デバッグ方法

#### 1. 詳細ログの有効化

```bash
# 環境変数でログレベルを設定
export LOG_LEVEL=DEBUG
scripts/deploy-catalog.sh deploy portfolios/development
```

#### 2. DRY_RUNモードでのテスト

```bash
# 実際の変更を行わずにテスト
export DRY_RUN=1
scripts/deploy-catalog.sh deploy portfolios/development
```

#### 3. 段階的なデバッグ

```bash
# 1. 設定ファイルの検証
scripts/deploy-catalog.sh validate portfolios/development

# 2. AWS認証の確認
aws sts get-caller-identity

# 3. 個別コンポーネントのテスト
scripts/manage-portfolio.sh create portfolios/development
scripts/manage-product.sh create portfolios/development/ec2-instances "Development Portfolio"
```

## 🔄 アップデート手順

### システムの更新

```bash
# 最新版を取得
git pull origin main

# 依存関係を更新
pip install -r requirements.txt --upgrade

# スクリプトの権限を確認
chmod +x scripts/*.sh
```

### 設定の移行

新しいバージョンで設定形式が変更された場合：

1. `CHANGELOG.md` で変更内容を確認
2. 既存の設定ファイルをバックアップ
3. 新しい形式に合わせて設定を更新
4. テスト環境で動作確認

## 📚 参考資料

### AWS ドキュメント

- [AWS Service Catalog 開発者ガイド](https://docs.aws.amazon.com/servicecatalog/latest/dg/)
- [CloudFormation ユーザーガイド](https://docs.aws.amazon.com/cloudformation/latest/userguide/)
- [GitHub Actions での OIDC 使用](https://docs.github.com/ja/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)

### 関連ツール

- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [jq コマンド](https://stedolan.github.io/jq/)
- [PyYAML](https://pyyaml.org/)

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は `LICENSE` ファイルを参照してください。

## 📞 サポート

問題や質問がある場合：

1. [Issues](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/issues) で既存の問題を検索
2. 新しい Issue を作成して詳細を記載
3. [Discussions](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/discussions) で質問や提案を投稿

---

**注意**: このシステムは本番環境での使用を想定して設計されていますが、重要なリソースをデプロイする前に必ずテスト環境で十分な検証を行ってください。