# フォルダ構造とファイル形式

このドキュメントでは、AWS Service Catalog 自動化システムのフォルダ構造と各ファイルの形式について詳しく説明します。

## 📁 全体構造

```
aws-service-catalog-automation/
├── .github/
│   └── workflows/
│       └── service-catalog.yml          # GitHub Actionsワークフロー
├── .kiro/
│   └── specs/                           # Kiro仕様書（開発用）
├── portfolios/                          # ポートフォリオ定義（メイン）
│   ├── development/                     # 開発環境ポートフォリオ
│   │   ├── portfolio.yaml              # ポートフォリオ設定
│   │   └── ec2-instances/               # EC2インスタンスプロダクト
│   │       ├── product.yaml            # プロダクト設定
│   │       ├── v1.0.0/                 # バージョン1.0.0
│   │       │   └── template.yaml       # CloudFormationテンプレート
│   │       └── v1.1.0/                 # バージョン1.1.0
│   │           └── template.yaml       # CloudFormationテンプレート
│   └── production/                      # 本番環境ポートフォリオ
│       ├── portfolio.yaml
│       └── database-services/
│           ├── product.yaml
│           └── v1.0.0/
│               └── template.yaml
├── scripts/                             # 管理スクリプト
│   ├── config_parser.py                # 設定ファイル解析
│   ├── detect-changes.py               # 変更検知
│   ├── manage-portfolio.sh             # ポートフォリオ管理
│   ├── manage-product.sh               # プロダクト管理
│   └── deploy-catalog.sh               # 統合デプロイ
├── cdk/                                 # AWS CDK バックアップ実装
│   ├── app.py                          # CDKアプリケーション
│   ├── service_catalog_stack.py        # Service Catalogスタック
│   └── requirements.txt                # Python依存関係
├── templates/                           # 設定ファイルテンプレート
│   ├── portfolio.yaml.template         # ポートフォリオテンプレート
│   └── product.yaml.template           # プロダクトテンプレート
├── tests/                               # 単体テスト
│   ├── test_config_parser.py           # 設定解析テスト
│   ├── test_detect_changes_fixed.py    # 変更検知テスト
│   ├── test_aws_cli_commands.py        # AWS CLIテスト
│   └── run_tests.py                    # テスト実行スクリプト
├── docs/                                # ドキュメント
│   ├── FOLDER_STRUCTURE.md             # このファイル
│   └── TROUBLESHOOTING.md              # トラブルシューティング
├── README.md                            # メインドキュメント
├── requirements.txt                     # Python依存関係
└── STRUCTURE.md                         # プロジェクト構造概要
```

## 📂 portfolios/ ディレクトリ

### 概要

`portfolios/` ディレクトリは、AWS Service Catalog のポートフォリオとプロダクトを定義するメインディレクトリです。

### 命名規則

- **ポートフォリオ名**: 小文字、ハイフン区切り（例：`development`, `production`, `staging`）
- **プロダクト名**: 小文字、ハイフン区切り（例：`ec2-instances`, `rds-databases`, `s3-buckets`）
- **バージョン名**: セマンティックバージョニング（例：`v1.0.0`, `v2.1.3`）

### ディレクトリ構造の例

```
portfolios/
├── development/                         # 開発環境
│   ├── portfolio.yaml                  # ポートフォリオ設定
│   ├── ec2-instances/                  # EC2インスタンス
│   │   ├── product.yaml
│   │   ├── v1.0.0/
│   │   │   └── template.yaml
│   │   └── v1.1.0/
│   │       └── template.yaml
│   ├── rds-databases/                  # RDSデータベース
│   │   ├── product.yaml
│   │   └── v1.0.0/
│   │       └── template.yaml
│   └── s3-buckets/                     # S3バケット
│       ├── product.yaml
│       └── v1.0.0/
│           └── template.yaml
├── staging/                            # ステージング環境
│   ├── portfolio.yaml
│   └── web-applications/
│       ├── product.yaml
│       └── v1.0.0/
│           └── template.yaml
└── production/                         # 本番環境
    ├── portfolio.yaml
    ├── high-availability-ec2/
    │   ├── product.yaml
    │   ├── v1.0.0/
    │   │   └── template.yaml
    │   └── v2.0.0/
    │       └── template.yaml
    └── managed-databases/
        ├── product.yaml
        └── v1.0.0/
            └── template.yaml
```

## 📄 設定ファイル形式

### portfolio.yaml

ポートフォリオの基本情報を定義します。

```yaml
# 必須フィールド
name: "Development Portfolio"                    # ポートフォリオ表示名
description: "開発環境用のリソーステンプレート"      # ポートフォリオ説明
owner: "development-team@company.com"            # 所有者メールアドレス

# オプションフィールド（将来の拡張用）
tags:                                           # タグ（オプション）
  Environment: "Development"
  Team: "Infrastructure"
  CostCenter: "Engineering"
```

#### フィールド詳細

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | string | ✓ | AWS Service Catalog で表示されるポートフォリオ名 |
| `description` | string | ✓ | ポートフォリオの説明文 |
| `owner` | string | ✓ | 所有者のメールアドレス（@を含む有効な形式） |
| `tags` | object | - | 将来の拡張用タグ（現在は未使用） |

### product.yaml

プロダクトの詳細情報を定義します。

```yaml
# 必須フィールド
name: "EC2 Instances"                           # プロダクト表示名
description: "Ubuntu 24.04 ARM SSM対応EC2インスタンス"  # プロダクト説明
owner: "infrastructure-team@company.com"        # 所有者メールアドレス
support_description: "インフラチームがサポートします"    # サポート説明
support_email: "infrastructure-team@company.com"       # サポートメールアドレス
support_url: "https://wiki.company.com/ec2-support"    # サポートURL

# オプションフィールド（将来の拡張用）
tags:                                           # タグ（オプション）
  Category: "Compute"
  OS: "Ubuntu"
  Architecture: "ARM64"
constraints:                                    # 制約（オプション）
  regions:                                      # 利用可能リージョン
    - "us-east-1"
    - "ap-northeast-1"
  instance_types:                               # 利用可能インスタンスタイプ
    - "t4g.micro"
    - "t4g.small"
    - "t4g.medium"
```

#### フィールド詳細

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | string | ✓ | AWS Service Catalog で表示されるプロダクト名 |
| `description` | string | ✓ | プロダクトの説明文 |
| `owner` | string | ✓ | 所有者のメールアドレス |
| `support_description` | string | ✓ | サポートに関する説明 |
| `support_email` | string | ✓ | サポート用メールアドレス |
| `support_url` | string | ✓ | サポート用URL（http://またはhttps://で始まる） |
| `tags` | object | - | 将来の拡張用タグ |
| `constraints` | object | - | 将来の拡張用制約 |

### template.yaml

CloudFormationテンプレートファイルです。標準的なCloudFormation形式に従います。

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Ubuntu 24.04 ARM SSM対応EC2インスタンス'

# パラメータ定義
Parameters:
  InstanceType:
    Type: String
    Default: t4g.micro
    AllowedValues:
      - t4g.micro
      - t4g.small
      - t4g.medium
    Description: EC2インスタンスタイプ
  
  KeyPairName:
    Type: AWS::EC2::KeyPair::KeyName
    Description: EC2インスタンス用のキーペア名
    ConstraintDescription: 既存のキーペア名を指定してください

# メタデータ（オプション）
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: "インスタンス設定"
        Parameters:
          - InstanceType
          - KeyPairName
    ParameterLabels:
      InstanceType:
        default: "インスタンスタイプ"
      KeyPairName:
        default: "キーペア名"

# リソース定義
Resources:
  # IAMロール
  EC2Role:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
      Tags:
        - Key: Name
          Value: !Sub "${AWS::StackName}-EC2Role"

  # インスタンスプロファイル
  InstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      Roles:
        - !Ref EC2Role

  # セキュリティグループ
  SecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: !Sub "${AWS::StackName} Security Group"
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 10.0.0.0/8
          Description: "SSH access from private networks"
      Tags:
        - Key: Name
          Value: !Sub "${AWS::StackName}-SecurityGroup"

  # EC2インスタンス
  EC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0c02fb55956c7d316  # Ubuntu 24.04 LTS ARM64
      InstanceType: !Ref InstanceType
      KeyName: !Ref KeyPairName
      IamInstanceProfile: !Ref InstanceProfile
      SecurityGroupIds:
        - !Ref SecurityGroup
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          apt-get update
          apt-get install -y awscli
          
          # SSM Agentは既にインストール済み（Ubuntu 24.04）
          systemctl enable amazon-ssm-agent
          systemctl start amazon-ssm-agent
          
          # CloudWatch Agentのインストール（オプション）
          wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/arm64/latest/amazon-cloudwatch-agent.deb
          dpkg -i amazon-cloudwatch-agent.deb
      Tags:
        - Key: Name
          Value: !Sub "${AWS::StackName}-Instance"
        - Key: Environment
          Value: !Ref "AWS::StackName"

# 出力値
Outputs:
  InstanceId:
    Description: EC2インスタンスID
    Value: !Ref EC2Instance
    Export:
      Name: !Sub "${AWS::StackName}-InstanceId"
  
  PublicIP:
    Description: パブリックIPアドレス
    Value: !GetAtt EC2Instance.PublicIp
    Export:
      Name: !Sub "${AWS::StackName}-PublicIP"
  
  PrivateIP:
    Description: プライベートIPアドレス
    Value: !GetAtt EC2Instance.PrivateIp
    Export:
      Name: !Sub "${AWS::StackName}-PrivateIP"
  
  SSMSessionCommand:
    Description: SSM Session Manager接続コマンド
    Value: !Sub "aws ssm start-session --target ${EC2Instance}"
```

#### CloudFormationテンプレートの要件

1. **必須セクション**:
   - `AWSTemplateFormatVersion`: CloudFormationバージョン
   - `Resources`: 少なくとも1つのリソース定義

2. **推奨セクション**:
   - `Description`: テンプレートの説明
   - `Parameters`: ユーザー入力パラメータ
   - `Outputs`: 作成されたリソースの情報

3. **ベストプラクティス**:
   - リソースにタグを付与
   - パラメータに適切な制約を設定
   - 出力値でリソース情報を提供
   - メタデータでUI表示を改善

## 🔧 scripts/ ディレクトリ

### 概要

システムの管理と自動化を行うスクリプト群です。

### ファイル詳細

#### config_parser.py

設定ファイルの解析と検証を行うPythonスクリプト。

**主な機能**:
- YAML設定ファイルの読み込み
- 設定値の検証
- ポートフォリオ構造の探索
- CloudFormationテンプレートの基本検証

**使用例**:
```bash
# ポートフォリオ設定の検証
python3 scripts/config_parser.py validate-portfolio portfolios/development/portfolio.yaml

# プロダクト設定の検証
python3 scripts/config_parser.py validate-product portfolios/development/ec2-instances/product.yaml

# テンプレートの検証
python3 scripts/config_parser.py validate-template portfolios/development/ec2-instances/v1.0.0/template.yaml

# ポートフォリオ構造の探索
python3 scripts/config_parser.py discover portfolios/
```

#### detect-changes.py

Git変更を検知し、影響を受けるポートフォリオ・プロダクトを特定するスクリプト。

**主な機能**:
- Git差分の取得
- ポートフォリオパスの解析
- 変更影響の分析
- GitHub Actions用出力

**使用例**:
```bash
# 変更検知の実行
python3 scripts/detect-changes.py

# GitHub Actions環境での実行
GITHUB_ACTIONS=true python3 scripts/detect-changes.py
```

#### manage-portfolio.sh

ポートフォリオの作成・更新・管理を行うBashスクリプト。

**主な機能**:
- ポートフォリオの作成
- ポートフォリオの更新
- ポートフォリオの存在確認
- ポートフォリオの一覧表示

**使用例**:
```bash
# ポートフォリオの作成
scripts/manage-portfolio.sh create portfolios/development

# ポートフォリオの更新
scripts/manage-portfolio.sh update portfolios/development

# ポートフォリオの存在確認
scripts/manage-portfolio.sh check "Development Portfolio"

# ポートフォリオの一覧表示
scripts/manage-portfolio.sh list
```

#### manage-product.sh

プロダクトの作成・更新・バージョン管理を行うBashスクリプト。

**主な機能**:
- プロダクトの作成
- プロダクトの更新
- プロダクトバージョンの追加
- CloudFormationテンプレートの検証

**使用例**:
```bash
# プロダクトの作成
scripts/manage-product.sh create portfolios/development/ec2-instances "Development Portfolio"

# プロダクトバージョンの追加
scripts/manage-product.sh add-version portfolios/development/ec2-instances v1.1.0

# テンプレートの検証
scripts/manage-product.sh validate-template portfolios/development/ec2-instances/v1.0.0/template.yaml
```

#### deploy-catalog.sh

全体の統合デプロイを管理するメインスクリプト。

**主な機能**:
- 全体デプロイの実行
- 変更ベースデプロイ
- 設定ファイルの一括検証
- デプロイ状況の確認

**使用例**:
```bash
# 全体デプロイ
scripts/deploy-catalog.sh deploy

# 特定ポートフォリオのデプロイ
scripts/deploy-catalog.sh deploy portfolios/development

# 変更ベースデプロイ
scripts/deploy-catalog.sh deploy-changes

# 設定の検証
scripts/deploy-catalog.sh validate

# デプロイ状況の確認
scripts/deploy-catalog.sh status
```

## 🏗️ cdk/ ディレクトリ

### 概要

AWS CLIで実装困難な操作のフォールバック用AWS CDK実装です。

### ファイル詳細

- `app.py`: CDKアプリケーションのエントリーポイント
- `service_catalog_stack.py`: Service Catalogリソースの定義
- `requirements.txt`: Python依存関係

## 📋 templates/ ディレクトリ

### 概要

新しいポートフォリオ・プロダクト作成時のテンプレートファイルです。

### 使用方法

```bash
# 新しいポートフォリオの作成
cp templates/portfolio.yaml.template portfolios/new-portfolio/portfolio.yaml

# 新しいプロダクトの作成
cp templates/product.yaml.template portfolios/new-portfolio/new-product/product.yaml
```

## 🧪 tests/ ディレクトリ

### 概要

システムの単体テストとテスト実行環境です。

### テスト実行

```bash
# 全テストの実行
python3 tests/run_tests.py

# 特定テストの実行
python3 tests/run_tests.py test_config_parser

# 依存関係のインストール
pip install -r tests/requirements.txt
```

## 📚 docs/ ディレクトリ

### 概要

追加のドキュメントファイルです。

- `FOLDER_STRUCTURE.md`: このファイル
- `TROUBLESHOOTING.md`: トラブルシューティングガイド

## 🔄 バージョン管理のベストプラクティス

### ブランチ戦略

```
main                    # 本番環境用
├── develop            # 開発統合用
├── feature/new-ec2    # 新機能開発用
└── hotfix/fix-auth    # 緊急修正用
```

### コミットメッセージ

```bash
# 新しいポートフォリオ追加
git commit -m "feat: add production portfolio with RDS products"

# 既存プロダクトの更新
git commit -m "update: improve EC2 instance template with enhanced security"

# バグ修正
git commit -m "fix: resolve OIDC authentication issue in GitHub Actions"

# ドキュメント更新
git commit -m "docs: update troubleshooting guide with new error cases"
```

### タグ付け

```bash
# リリースタグ
git tag -a v1.0.0 -m "Initial release"
git tag -a v1.1.0 -m "Add support for multiple regions"

# プロダクトバージョンタグ
git tag -a ec2-v1.0.0 -m "EC2 instances product version 1.0.0"
```

## 🔍 ファイル検証

### 自動検証

システムは以下の検証を自動的に実行します：

1. **YAML構文検証**: すべての設定ファイル
2. **必須フィールド確認**: portfolio.yaml, product.yaml
3. **CloudFormation検証**: template.yaml
4. **メールアドレス形式**: owner, support_email
5. **URL形式**: support_url

### 手動検証

```bash
# 設定ファイルの検証
find portfolios/ -name "*.yaml" -exec python3 scripts/config_parser.py validate-portfolio {} \;

# CloudFormationテンプレートの検証
find portfolios/ -name "template.yaml" -exec aws cloudformation validate-template --template-body file://{} \;
```

## 📊 監視とメトリクス

### ファイル統計

```bash
# ポートフォリオ数
find portfolios/ -name "portfolio.yaml" | wc -l

# プロダクト数
find portfolios/ -name "product.yaml" | wc -l

# バージョン数
find portfolios/ -name "template.yaml" | wc -l

# ファイルサイズ統計
find portfolios/ -name "*.yaml" -exec ls -la {} \; | awk '{sum+=$5} END {print "Total size:", sum, "bytes"}'
```

### 構造検証

```bash
# 構造の整合性確認
python3 scripts/config_parser.py discover portfolios/ | jq '.[] | {name: .name, products: (.products | length), versions: (.products[].versions | length)}'
```

この構造とファイル形式に従うことで、AWS Service Catalog 自動化システムが正常に動作し、効率的なリソース管理が可能になります。