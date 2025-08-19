#!/usr/bin/env python3
"""
AWS CDK アプリケーションのエントリーポイント
Service Catalog の自動化システム用 CDK スタック
"""

import aws_cdk as cdk
from service_catalog_stack import ServiceCatalogStack


app = cdk.App()

# Service Catalog スタックを作成
ServiceCatalogStack(
    app, 
    "ServiceCatalogStack",
    description="AWS Service Catalog automation backup implementation"
)

app.synth()