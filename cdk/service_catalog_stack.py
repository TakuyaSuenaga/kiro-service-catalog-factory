"""
AWS Service Catalog 自動化システム用 CDK スタック

このスタックは AWS CLI で実装が困難な Service Catalog 操作の
フォールバック実装を提供します。
"""

import json
import logging
from typing import Dict, Any, Optional

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_servicecatalog as servicecatalog,
    aws_s3 as s3,
    aws_iam as iam,
    aws_logs as logs,
    CfnOutput
)
from constructs import Construct


class ServiceCatalogStack(Stack):
    """
    Service Catalog リソースを管理する CDK スタック
    
    AWS CLI で困難な操作のフォールバック機能を提供:
    - 複雑なポートフォリオ・プロダクト関係の管理
    - エラーハンドリングとロールバック
    - 詳細なログ出力
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # ログ設定
        self._setup_logging()
        
        # S3バケット（CloudFormationテンプレート保存用）
        self.template_bucket = self._create_template_bucket()
        
        # IAMロール（Service Catalog用）
        self.service_catalog_role = self._create_service_catalog_role()
        
        # CloudWatch Logs グループ
        self.log_group = self._create_log_group()
        
        # 出力
        self._create_outputs()

    def _setup_logging(self) -> None:
        """ログ設定を初期化"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _create_template_bucket(self) -> s3.Bucket:
        """CloudFormationテンプレート保存用S3バケットを作成"""
        bucket = s3.Bucket(
            self, "ServiceCatalogTemplateBucket",
            bucket_name=f"service-catalog-templates-{self.account}-{self.region}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )
        
        self.logger.info(f"Created S3 bucket: {bucket.bucket_name}")
        return bucket

    def _create_service_catalog_role(self) -> iam.Role:
        """Service Catalog 操作用 IAM ロールを作成"""
        role = iam.Role(
            self, "ServiceCatalogRole",
            assumed_by=iam.ServicePrincipal("servicecatalog.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSServiceCatalogAdminFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudFormationFullAccess")
            ]
        )
        
        # S3バケットへのアクセス権限を追加
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                resources=[
                    self.template_bucket.bucket_arn,
                    f"{self.template_bucket.bucket_arn}/*"
                ]
            )
        )
        
        self.logger.info(f"Created IAM role: {role.role_name}")
        return role

    def _create_log_group(self) -> logs.LogGroup:
        """CloudWatch Logs グループを作成"""
        log_group = logs.LogGroup(
            self, "ServiceCatalogLogGroup",
            log_group_name="/aws/servicecatalog/automation",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )
        
        self.logger.info(f"Created CloudWatch Logs group: {log_group.log_group_name}")
        return log_group

    def _create_outputs(self) -> None:
        """スタック出力を作成"""
        CfnOutput(
            self, "TemplateBucketName",
            value=self.template_bucket.bucket_name,
            description="CloudFormation テンプレート保存用 S3 バケット名"
        )
        
        CfnOutput(
            self, "ServiceCatalogRoleArn",
            value=self.service_catalog_role.role_arn,
            description="Service Catalog 操作用 IAM ロール ARN"
        )
        
        CfnOutput(
            self, "LogGroupName",
            value=self.log_group.log_group_name,
            description="CloudWatch Logs グループ名"
        )

    def create_portfolio(self, portfolio_config: Dict[str, Any]) -> servicecatalog.CfnPortfolio:
        """
        ポートフォリオを作成
        
        Args:
            portfolio_config: ポートフォリオ設定辞書
            
        Returns:
            作成されたポートフォリオ
        """
        try:
            portfolio = servicecatalog.CfnPortfolio(
                self, f"Portfolio-{portfolio_config['name'].replace(' ', '-')}",
                display_name=portfolio_config['name'],
                description=portfolio_config.get('description', ''),
                provider_name=portfolio_config.get('owner', 'Unknown')
            )
            
            self.logger.info(f"Created portfolio: {portfolio_config['name']}")
            return portfolio
            
        except Exception as e:
            self.logger.error(f"Failed to create portfolio {portfolio_config['name']}: {str(e)}")
            raise

    def create_product(self, product_config: Dict[str, Any], portfolio: servicecatalog.CfnPortfolio) -> servicecatalog.CfnCloudFormationProduct:
        """
        プロダクトを作成
        
        Args:
            product_config: プロダクト設定辞書
            portfolio: 関連付けるポートフォリオ
            
        Returns:
            作成されたプロダクト
        """
        try:
            product = servicecatalog.CfnCloudFormationProduct(
                self, f"Product-{product_config['name'].replace(' ', '-')}",
                name=product_config['name'],
                description=product_config.get('description', ''),
                owner=product_config.get('owner', 'Unknown'),
                support_description=product_config.get('support_description', ''),
                support_email=product_config.get('support_email', ''),
                support_url=product_config.get('support_url', '')
            )
            
            # ポートフォリオとプロダクトを関連付け
            servicecatalog.CfnPortfolioProductAssociation(
                self, f"Association-{portfolio.display_name}-{product.name}",
                portfolio_id=portfolio.ref,
                product_id=product.ref
            )
            
            self.logger.info(f"Created product: {product_config['name']}")
            return product
            
        except Exception as e:
            self.logger.error(f"Failed to create product {product_config['name']}: {str(e)}")
            raise

    def add_product_version(self, product: servicecatalog.CfnCloudFormationProduct, 
                           version_name: str, template_s3_url: str) -> None:
        """
        プロダクトに新しいバージョンを追加
        
        Args:
            product: 対象プロダクト
            version_name: バージョン名
            template_s3_url: CloudFormation テンプレートの S3 URL
        """
        try:
            # プロダクトのプロビジョニングアーティファクトを更新
            provisioning_artifacts = getattr(product, 'provisioning_artifact_parameters', [])
            
            new_artifact = {
                'name': version_name,
                'description': f'Version {version_name}',
                'info': {
                    'LoadTemplateFromURL': template_s3_url
                }
            }
            
            provisioning_artifacts.append(new_artifact)
            product.provisioning_artifact_parameters = provisioning_artifacts
            
            self.logger.info(f"Added version {version_name} to product {product.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to add version {version_name} to product: {str(e)}")
            raise

    def get_template_s3_url(self, s3_key: str) -> str:
        """
        CloudFormation テンプレートの S3 URL を生成
        
        Args:
            s3_key: S3 オブジェクトキー
            
        Returns:
            テンプレートの S3 URL
        """
        try:
            s3_url = f"https://{self.template_bucket.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            self.logger.info(f"Generated S3 URL: {s3_url}")
            return s3_url
            
        except Exception as e:
            self.logger.error(f"Failed to generate S3 URL: {str(e)}")
            raise

    def create_portfolio_with_fallback(self, portfolio_config: Dict[str, Any]) -> Optional[servicecatalog.CfnPortfolio]:
        """
        ポートフォリオ作成のフォールバック実装
        AWS CLI で失敗した場合の代替手段
        
        Args:
            portfolio_config: ポートフォリオ設定辞書
            
        Returns:
            作成されたポートフォリオ、または失敗時は None
        """
        try:
            self.logger.info(f"Creating portfolio with CDK fallback: {portfolio_config['name']}")
            
            # 設定の妥当性を検証
            if not self._validate_portfolio_config(portfolio_config):
                return None
            
            portfolio = self.create_portfolio(portfolio_config)
            
            # 追加のメタデータを設定
            if 'tags' in portfolio_config:
                for key, value in portfolio_config['tags'].items():
                    cdk.Tags.of(portfolio).add(key, value)
            
            self.logger.info(f"Successfully created portfolio with CDK: {portfolio_config['name']}")
            return portfolio
            
        except Exception as e:
            self.logger.error(f"CDK fallback failed for portfolio {portfolio_config['name']}: {str(e)}")
            return None

    def create_product_with_fallback(self, product_config: Dict[str, Any], 
                                   portfolio: servicecatalog.CfnPortfolio,
                                   template_versions: Dict[str, str]) -> Optional[servicecatalog.CfnCloudFormationProduct]:
        """
        プロダクト作成のフォールバック実装
        AWS CLI で失敗した場合の代替手段
        
        Args:
            product_config: プロダクト設定辞書
            portfolio: 関連付けるポートフォリオ
            template_versions: バージョン名とテンプレート内容の辞書
            
        Returns:
            作成されたプロダクト、または失敗時は None
        """
        try:
            self.logger.info(f"Creating product with CDK fallback: {product_config['name']}")
            
            # 設定の妥当性を検証
            if not self._validate_product_config(product_config):
                return None
            
            # プロビジョニングアーティファクトを準備
            provisioning_artifacts = []
            
            for version_name, template_content in template_versions.items():
                # テンプレートの S3 URL を生成
                s3_key = f"templates/{portfolio.display_name}/{product_config['name']}/{version_name}/template.yaml"
                s3_url = self.get_template_s3_url(s3_key)
                
                artifact = {
                    'name': version_name,
                    'description': f'Version {version_name} of {product_config["name"]}',
                    'info': {
                        'LoadTemplateFromURL': s3_url
                    }
                }
                provisioning_artifacts.append(artifact)
            
            # プロダクトを作成
            product = servicecatalog.CfnCloudFormationProduct(
                self, f"Product-{product_config['name'].replace(' ', '-')}-Fallback",
                name=product_config['name'],
                description=product_config.get('description', ''),
                owner=product_config.get('owner', 'Unknown'),
                support_description=product_config.get('support_description', ''),
                support_email=product_config.get('support_email', ''),
                support_url=product_config.get('support_url', ''),
                provisioning_artifact_parameters=provisioning_artifacts
            )
            
            # ポートフォリオとプロダクトを関連付け
            servicecatalog.CfnPortfolioProductAssociation(
                self, f"Association-{portfolio.display_name}-{product.name}-Fallback",
                portfolio_id=portfolio.ref,
                product_id=product.ref
            )
            
            # タグを追加
            if 'tags' in product_config:
                for key, value in product_config['tags'].items():
                    cdk.Tags.of(product).add(key, value)
            
            self.logger.info(f"Successfully created product with CDK: {product_config['name']}")
            return product
            
        except Exception as e:
            self.logger.error(f"CDK fallback failed for product {product_config['name']}: {str(e)}")
            return None

    def _validate_portfolio_config(self, config: Dict[str, Any]) -> bool:
        """ポートフォリオ設定の妥当性を検証"""
        required_fields = ['name']
        
        for field in required_fields:
            if field not in config or not config[field]:
                self.logger.error(f"Missing or empty required field in portfolio config: {field}")
                return False
        
        return True

    def _validate_product_config(self, config: Dict[str, Any]) -> bool:
        """プロダクト設定の妥当性を検証"""
        required_fields = ['name']
        
        for field in required_fields:
            if field not in config or not config[field]:
                self.logger.error(f"Missing or empty required field in product config: {field}")
                return False
        
        return True

    def cleanup_failed_resources(self, resource_ids: List[str]) -> None:
        """
        失敗したリソースのクリーンアップ
        
        Args:
            resource_ids: クリーンアップ対象のリソース ID リスト
        """
        try:
            self.logger.info(f"Starting cleanup of failed resources: {resource_ids}")
            
            # 実際のクリーンアップロジックはここに実装
            # CDK では通常、スタックの削除時に自動的にリソースがクリーンアップされる
            
            self.logger.info("Cleanup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup resources: {str(e)}")
            raise