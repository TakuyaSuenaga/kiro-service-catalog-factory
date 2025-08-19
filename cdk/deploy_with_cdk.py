#!/usr/bin/env python3
"""
CDK を使用した Service Catalog デプロイメントスクリプト

AWS CLI で困難な操作の場合に CDK フォールバック機能を使用
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# プロジェクトルートを Python パスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.config_parser import load_portfolio_config, load_product_config
from utils import find_template_versions, get_template_s3_key


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def deploy_portfolio_with_cdk(portfolio_path: str) -> bool:
    """
    CDK を使用してポートフォリオをデプロイ
    
    Args:
        portfolio_path: ポートフォリオディレクトリのパス
        
    Returns:
        デプロイ成功可否
    """
    try:
        logger.info(f"Starting CDK deployment for portfolio: {portfolio_path}")
        
        # ポートフォリオ設定を読み込み
        portfolio_config = load_portfolio_config(portfolio_path)
        if not portfolio_config:
            logger.error(f"Failed to load portfolio config: {portfolio_path}")
            return False
        
        # CDK デプロイコマンドを実行
        cdk_command = [
            "cdk", "deploy",
            "--context", f"portfolio_path={portfolio_path}",
            "--context", f"portfolio_config={json.dumps(portfolio_config)}",
            "--require-approval", "never"
        ]
        
        result = os.system(" ".join(cdk_command))
        
        if result == 0:
            logger.info(f"CDK deployment successful for portfolio: {portfolio_path}")
            return True
        else:
            logger.error(f"CDK deployment failed for portfolio: {portfolio_path}")
            return False
            
    except Exception as e:
        logger.error(f"CDK deployment error for portfolio {portfolio_path}: {str(e)}")
        return False


def deploy_product_with_cdk(portfolio_path: str, product_path: str) -> bool:
    """
    CDK を使用してプロダクトをデプロイ
    
    Args:
        portfolio_path: ポートフォリオディレクトリのパス
        product_path: プロダクトディレクトリのパス
        
    Returns:
        デプロイ成功可否
    """
    try:
        logger.info(f"Starting CDK deployment for product: {product_path}")
        
        # 設定を読み込み
        portfolio_config = load_portfolio_config(portfolio_path)
        product_config = load_product_config(product_path)
        
        if not portfolio_config or not product_config:
            logger.error(f"Failed to load configs for product: {product_path}")
            return False
        
        # テンプレートバージョンを検索
        versions = find_template_versions(product_path)
        if not versions:
            logger.error(f"No template versions found for product: {product_path}")
            return False
        
        # テンプレート内容を読み込み
        template_versions = {}
        for version in versions:
            template_file = Path(product_path) / version / "template.yaml"
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_versions[version] = f.read()
        
        # CDK デプロイコマンドを実行
        cdk_command = [
            "cdk", "deploy",
            "--context", f"portfolio_path={portfolio_path}",
            "--context", f"product_path={product_path}",
            "--context", f"portfolio_config={json.dumps(portfolio_config)}",
            "--context", f"product_config={json.dumps(product_config)}",
            "--context", f"template_versions={json.dumps(template_versions)}",
            "--require-approval", "never"
        ]
        
        result = os.system(" ".join(cdk_command))
        
        if result == 0:
            logger.info(f"CDK deployment successful for product: {product_path}")
            return True
        else:
            logger.error(f"CDK deployment failed for product: {product_path}")
            return False
            
    except Exception as e:
        logger.error(f"CDK deployment error for product {product_path}: {str(e)}")
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="CDK Service Catalog Deployment")
    parser.add_argument("--portfolio", required=True, help="Portfolio directory path")
    parser.add_argument("--product", help="Product directory path (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    
    args = parser.parse_args()
    
    try:
        if args.dry_run:
            logger.info("Running in dry-run mode")
            # CDK diff コマンドを実行
            os.system("cdk diff")
            return
        
        # ポートフォリオのデプロイ
        portfolio_success = deploy_portfolio_with_cdk(args.portfolio)
        
        if args.product:
            # プロダクトのデプロイ
            product_success = deploy_product_with_cdk(args.portfolio, args.product)
            
            if portfolio_success and product_success:
                logger.info("All CDK deployments completed successfully")
                sys.exit(0)
            else:
                logger.error("One or more CDK deployments failed")
                sys.exit(1)
        else:
            if portfolio_success:
                logger.info("Portfolio CDK deployment completed successfully")
                sys.exit(0)
            else:
                logger.error("Portfolio CDK deployment failed")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"CDK deployment script error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()