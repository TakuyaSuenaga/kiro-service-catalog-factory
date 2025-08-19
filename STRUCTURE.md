# AWS Service Catalog 自動化システム - プロジェクト構造

このドキュメントでは、AWS Service Catalog 自動化システムの最小限のプロジェクト構造について説明します。

## 🏗️ アーキテクチャ概要

```
GitHub Actions (手動実行) → OIDC認証 → AWS CDK → Service Catalog
```

## 📁 ディレクトリ構造

```
aws-service-catalog-automation/
├── 📂 .github/
│   └── 📂 workflows/
│       └── 📄 service-catalog.yml         # 手動実行ワークフロー
├── 📂 .kiro/
│   └── 📂 specs/                          # Kiro仕様書
│       └── 📂 aws-service-catalog-automation/
│           ├── 📄 requirements.md         # 要件定義
│           ├── 📄 design.md              # 設計書
│           └── 📄 tasks.md               # 実装タスク
├── 📂 cdk/                               # ☁️ AWS CDK
│   ├── 🐍 app.py                        # CDKアプリケーション
│   ├── 🐍 service_catalog_stack.py      # Service Catalogスタック
│   ├── 📄 cdk.json                      # CDK設定
│   └── 📄 requirements.txt              # Python依存関係
├── 📂 portfolios/                        # 🎯 メインコンテンツ
│   └── 📂 development/                   # 開発環境
│       ├── 📄 portfolio.yaml            # ポートフォリオ設定
│       └── 📂 ec2-instances/             # プロダクト
│           ├── 📄 product.yaml          # プロダクト設定
│           └── 📂 v1.0.0/               # バージョン
│               └── 📄 template.yaml     # CloudFormationテンプレート
├── 📄 README.md                          # メインドキュメント
└── 📄 STRUCTURE.md                       # このファイル
```

## 🎯 主要コンポーネント

### 1. .github/workflows/ - 手動実行パイプライン

**目的**: GitHub Actionsによる手動デプロイ

**ワークフロー**:
```yaml
name: Deploy AWS Service Catalog
on:
  workflow_dispatch:  # 手動実行のみ
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ secrets.AWS_REGION }}
      - name: Deploy CDK
        run: |
          cd cdk
          pip install -r requirements.txt
          npm install -g aws-cdk
          cdk deploy --require-approval never
```

**特徴**:
- 手動実行のみ（workflow_dispatch）
- OIDC認証
- シンプルなデプロイフロー

### 2. cdk/ - AWS CDK実装

**目的**: Service Catalogリソースの作成

**構成**:
- `app.py`: CDKアプリケーションエントリーポイント
- `service_catalog_stack.py`: ポートフォリオとプロダクトの定義
- `cdk.json`: CDK設定ファイル
- `requirements.txt`: Python依存関係

**特徴**:
- 単一スタック
- YAMLファイル読み込み
- 最小限の実装

### 3. portfolios/ - コンテンツ管理

**目的**: AWS Service Catalog のポートフォリオとプロダクトを定義

**構造**:
```
portfolios/
└── development/
    ├── portfolio.yaml              # ポートフォリオ設定
    └── ec2-instances/
        ├── product.yaml            # プロダクト設定
        └── v1.0.0/
            └── template.yaml       # CloudFormationテンプレート
```

**特徴**:
- 固定のファイルパス
- 既存ファイル構造の活用
- シンプルな設定

## 🔄 データフロー

### 手動実行フロー

```
1. 開発者がGitHub Actionsを手動実行
2. OIDC認証でAWSに接続
3. CDKがYAMLファイルを読み込み
4. Service Catalogにポートフォリオとプロダクトを作成
5. 完了
```

## 🛠️ 技術スタック

### 言語・フレームワーク

| 技術 | 用途 | バージョン |
|---|---|---|
| Python | CDK実装 | 3.9+ |
| YAML | 設定ファイル | 1.2 |
| AWS CDK | インフラ定義 | 2.x |

### AWS サービス

| サービス | 用途 |
|---|---|
| Service Catalog | プロダクト管理 |
| CloudFormation | リソース定義 |
| IAM | OIDC認証 |

### 開発ツール

| ツール | 用途 |
|---|---|
| GitHub Actions | 手動実行 |
| AWS CDK CLI | デプロイ |
| PyYAML | YAML解析 |

## 🔒 セキュリティ

### OIDC認証

- 長期間有効なアクセスキー不要
- 特定リポジトリからのみアクセス
- 最小権限のIAMロール

### 設定管理

- GitHub Secretsで認証情報管理
- 固定ファイルパスで予測可能な動作

## 📊 システムの特徴

### 最小限の設計

- テスト機能なし
- エラーハンドリング最小限
- 自動実行なし（手動のみ）
- 単一環境対応

### シンプルな運用

- 手動実行による制御
- 既存ファイル構造の活用
- 設定変更不要

## 🚀 使用方法

### 1. セットアップ
1. AWS OIDC設定
2. GitHub Secrets設定
3. ファイル確認

### 2. 実行
1. GitHub Actionsページに移動
2. 「Deploy AWS Service Catalog」選択
3. 「Run workflow」クリック

### 3. 確認
1. AWS Service Catalogコンソールで確認
2. GitHub Actionsログで結果確認

この最小限の構造により、シンプルで保守しやすいAWS Service Catalog自動化システムを実現しています。