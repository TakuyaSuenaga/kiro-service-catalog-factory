# AWS Service Catalog CDK バックアップ実装

このディレクトリには、AWS CLI で実装が困難な Service Catalog 操作のフォールバック実装が含まれています。

## 概要

CDK (Cloud Development Kit) を使用して以下の機能を提供します：

- 複雑なポートフォリオ・プロダクト関係の管理
- エラーハンドリングとロールバック機能
- 詳細なログ出力とモニタリング
- CloudFormation テンプレートの S3 保存

## ファイル構成

```
cdk/
├── app.py                    # CDK アプリケーションエントリーポイント
├── service_catalog_stack.py  # Service Catalog スタック実装
├── cdk.json                  # CDK 設定ファイル
├── requirements.txt          # Python 依存関係
└── README.md                # このファイル
```

## セットアップ

1. Python 仮想環境の作成と有効化：
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate.bat  # Windows
```

2. 依存関係のインストール：
```bash
pip install -r requirements.txt
```

3. CDK のブートストラップ（初回のみ）：
```bash
cdk bootstrap
```

## 使用方法

### スタックのデプロイ

```bash
cdk deploy
```

### スタックの削除

```bash
cdk destroy
```

### 差分の確認

```bash
cdk diff
```

### CloudFormation テンプレートの生成

```bash
cdk synth
```

## 主要コンポーネント

### ServiceCatalogStack

メインの CDK スタッククラス。以下のリソースを管理：

- **S3 バケット**: CloudFormation テンプレートの保存
- **IAM ロール**: Service Catalog 操作用の権限
- **CloudWatch Logs**: 操作ログの記録
- **Service Catalog リソース**: ポートフォリオとプロダクト

### 主要メソッド

- `create_portfolio()`: ポートフォリオの作成
- `create_product()`: プロダクトの作成とポートフォリオへの関連付け

## エラーハンドリング

CDK 実装では以下のエラーハンドリング機能を提供：

- 詳細なログ出力
- 例外の適切なキャッチと再発生
- リソース作成失敗時の自動ロールバック

## AWS CLI との使い分け

- **AWS CLI 優先**: シンプルな操作は AWS CLI を使用
- **CDK フォールバック**: 複雑な操作や高度なエラーハンドリングが必要な場合に CDK を使用

## 要件対応

この実装は以下の要件に対応：

- **要件 7.2**: AWS CLI で困難な操作の CDK による実装
- シンプルで保守しやすい実装の提供
- 適切な技術選択（AWS CLI > CDK の優先順位）