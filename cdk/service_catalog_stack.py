from aws_cdk import (
    Stack,
    aws_servicecatalog as servicecatalog,
    aws_s3 as s3,
    aws_iam as iam,
)
from constructs import Construct


class ServiceCatalogStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket for CloudFormation templates
        template_bucket = s3.Bucket(
            self, "TemplateBucket",
            bucket_name=f"service-catalog-templates-{self.account}-{self.region}",
            versioned=True,
            public_read_access=False,
        )

        # Create Service Catalog portfolio
        portfolio = servicecatalog.Portfolio(
            self, "Portfolio",
            display_name="AWS Service Catalog Portfolio",
            description="Portfolio for AWS Service Catalog products",
            provider_name="IT Department",
        )

        # Create IAM role for Service Catalog launch constraint
        launch_role = iam.Role(
            self, "LaunchRole",
            assumed_by=iam.ServicePrincipal("servicecatalog.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("PowerUserAccess")
            ],
        )

        # Add launch constraint to portfolio
        portfolio.add_product(
            servicecatalog.CloudFormationProduct(
                self, "SampleProduct",
                product_name="Sample EC2 Instance",
                owner="IT Department",
                product_versions=[
                    servicecatalog.CloudFormationProductVersion(
                        product_version_name="v1.0",
                        cloud_formation_template=servicecatalog.CloudFormationTemplate.from_url(
                            f"https://{template_bucket.bucket_name}.s3.{self.region}.amazonaws.com/ec2-instance.yaml"
                        ),
                    )
                ],
            )
        )