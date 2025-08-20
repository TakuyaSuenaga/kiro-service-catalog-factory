import os
import yaml
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_servicecatalog as servicecatalog,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
)
from constructs import Construct


class ServiceCatalogStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load portfolio configuration
        portfolio_config = self._load_yaml_file("../portfolios/development/portfolio.yaml")
        
        # Load product configuration
        product_config = self._load_yaml_file("../portfolios/development/ec2-instances/product.yaml")

        # Get bucket name from context or use default
        template_bucket_name = self.node.try_get_context("template_bucket_name")
        
        if template_bucket_name:
            # Use existing bucket specified in cdk.json
            template_bucket = s3.Bucket.from_bucket_name(
                self, "TemplateBucket", template_bucket_name
            )
        else:
            # Create new bucket with predictable name
            default_bucket_name = f"service-catalog-templates-{self.account}-{self.region}"
            template_bucket = s3.Bucket(
                self, "TemplateBucket",
                bucket_name=default_bucket_name,
                versioned=True,
                public_read_access=False,
                removal_policy=RemovalPolicy.RETAIN,  # Keep bucket when stack is deleted
                auto_delete_objects=False,  # Don't auto-delete objects for safety
            )

        # Upload CloudFormation template to S3
        template_deployment = s3deploy.BucketDeployment(
            self, "TemplateDeployment",
            sources=[s3deploy.Source.asset("../portfolios/development/ec2-instances/v1.0.0")],
            destination_bucket=template_bucket,
            destination_key_prefix="templates/",
        )

        # Create Service Catalog portfolio
        portfolio = servicecatalog.Portfolio(
            self, "Portfolio",
            display_name=portfolio_config.get("name", "Default Portfolio"),
            description=portfolio_config.get("description", "Default Description"),
            provider_name=portfolio_config.get("owner", "Default Owner"),
        )

        # Create CloudFormation product
        product = servicecatalog.CloudFormationProduct(
            self, "Product",
            product_name=product_config.get("name", "Default Product"),
            owner=product_config.get("owner", "Default Owner"),
            description=product_config.get("description", "Default Description"),
            support_description=product_config.get("support_description", ""),
            support_email=product_config.get("support_email", ""),
            support_url=product_config.get("support_url", ""),
            product_versions=[
                servicecatalog.CloudFormationProductVersion(
                    product_version_name="v1.0.0",
                    cloud_formation_template=servicecatalog.CloudFormationTemplate.from_url(
                        f"https://{template_bucket.bucket_name}.s3.{self.region}.amazonaws.com/templates/template.yaml"
                    ),
                )
            ],
        )

        # Add product to portfolio
        portfolio.add_product(product)

        # Ensure template is uploaded before product creation
        product.node.add_dependency(template_deployment)

    def _load_yaml_file(self, file_path: str) -> dict:
        """Load and parse YAML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found. Using default values.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {file_path}: {e}")
            return {}