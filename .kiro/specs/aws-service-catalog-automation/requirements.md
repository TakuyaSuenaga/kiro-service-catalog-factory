# 要件定義書

## 概要

AWS CDKを使用してAWSサービスカタログにポートフォリオとプロダクトを登録する最小限のシステム。GitHub Actionsの手動実行により、既存のファイル構造からポートフォリオとプロダクトをAWSサービスカタログに登録する。

## 要件

### 要件1

**ユーザーストーリー:** 開発者として、GitHub Actionsを手動実行してAWSサービスカタログにポートフォリオとプロダクトを登録したい。これにより、必要な時にのみサービスカタログを更新できる。

#### 受け入れ基準

1. WHEN GitHub Actionsワークフローを手動実行する場合 THEN AWS CDKを使用してポートフォリオとプロダクトがAWSサービスカタログに登録される
2. WHEN ワークフローを実行する場合 THEN 既存のportfolios/development/portfolio.yamlファイルを読み込んでポートフォリオを作成する
3. WHEN プロダクトを登録する場合 THEN portfolios/development/ec2-instances/product.yamlとportfolios/development/ec2-instances/v1.0.0/template.yamlファイルを使用する

### 要件2

**ユーザーストーリー:** インフラ管理者として、既存のファイル構造を活用してサービスカタログを管理したい。これにより、現在のファイル構成を変更せずにシステムを利用できる。

#### 受け入れ基準

1. WHEN ポートフォリオを作成する場合 THEN portfolios/development/portfolio.yamlファイルの設定を使用する
2. WHEN プロダクトを作成する場合 THEN portfolios/development/ec2-instances/product.yamlファイルの設定を使用する
3. WHEN CloudFormationテンプレートを登録する場合 THEN portfolios/development/ec2-instances/v1.0.0/template.yamlファイルを使用する

### 要件3

**ユーザーストーリー:** セキュリティ管理者として、OIDC認証を使用してAWSに安全に接続したい。これにより、長期間有効なアクセスキーを使用せずに済む。

#### 受け入れ基準

1. WHEN GitHub ActionsがAWSに接続する場合 THEN OIDC認証を使用してアクセスキーを使わずに認証する
2. WHEN AWS認証を設定する場合 THEN configure-aws-credentialsアクションでOIDCプロバイダーを使用する
3. WHEN IAMロールを指定する場合 THEN GitHubシークレット変数でロールARNを管理する

### 要件4

**ユーザーストーリー:** 開発者として、AWS CDKを使用してシンプルにサービスカタログを管理したい。これにより、複雑な設定や処理を避けて最小限の実装で目的を達成できる。

#### 受け入れ基準

1. WHEN サービスカタログリソースを作成する場合 THEN AWS CDKのPythonコードで実装する
2. WHEN ポートフォリオとプロダクトを登録する場合 THEN 単一のCDKスタックで処理する
3. WHEN 実装する場合 THEN テスト機能やエラーハンドリングは含めない