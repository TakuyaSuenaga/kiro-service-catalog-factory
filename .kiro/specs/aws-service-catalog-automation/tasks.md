# 実装計画

- [x] 1. CDK プロジェクトの基本構造を作成

  - cdk.json ファイルを作成して CDK アプリケーションのエントリーポイントを設定
  - requirements.txt ファイルを作成して AWS CDK と PyYAML の依存関係を定義
  - _要件: 4.1, 4.2_

- [x] 2. CDK アプリケーションエントリーポイントを実装

  - app.py ファイルを作成して CDK アプリケーションを初期化
  - ServiceCatalogStack をインスタンス化してデプロイ対象として設定
  - _要件: 4.1, 4.2_

- [x] 3. YAML ファイル読み込み機能を実装

  - service_catalog_stack.py に YAML ファイル読み込み関数を作成
  - portfolios/development/portfolio.yaml を読み込む機能を実装
  - portfolios/development/ec2-instances/product.yaml を読み込む機能を実装
  - _要件: 1.2, 2.1, 2.2, 2.3_

- [x] 4. Service Catalog ポートフォリオリソースを作成

  - CDK スタック内で aws_servicecatalog.Portfolio リソースを作成
  - portfolio.yaml から読み込んだ設定値を適用
  - ポートフォリオ名、説明、所有者を設定
  - _要件: 1.2, 2.1_

- [x] 5. Service Catalog プロダクトリソースを作成

  - CDK スタック内で aws_servicecatalog.CloudFormationProduct リソースを作成
  - product.yaml から読み込んだ設定値を適用
  - CloudFormation テンプレートファイル（portfolios/development/ec2-instances/v1.0.0/template.yaml）を指定
  - _要件: 1.2, 2.2, 2.3_

- [x] 6. ポートフォリオとプロダクトの関連付けを実装

  - aws_servicecatalog.PortfolioProductAssociation リソースを作成
  - 作成したポートフォリオとプロダクトを関連付け
  - _要件: 1.1_

- [x] 7. GitHub Actions 手動実行ワークフローを作成
  - .github/workflows/service-catalog.yml ファイルを作成
  - workflow_dispatch トリガーで手動実行を設定
  - OIDC 認証を使用した configure-aws-credentials ステップを追加
  - Python 環境セットアップと CDK 依存関係インストールステップを追加
  - CDK デプロイ実行ステップを追加
  - _要件: 1.1, 3.1, 3.2, 3.3_
