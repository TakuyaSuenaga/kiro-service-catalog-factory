#!/usr/bin/env python3
"""
AWS CLI と CDK の統合フォールバック機能

AWS CLI で失敗した操作を CDK で再試行する機能を提供
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# プロジェクトルートを Python パスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.config_parser import load_portfolio_config, load_product_config
except ImportError:
    # フォールバック用の簡易実装
    import yaml
    
    def load_portfolio_config(portfolio_path: str) -> Optional[Dict[str, Any]]:
        config_file = Path(portfolio_path) / "portfolio.yaml"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None
    
    def load_product_config(product_path: str) -> Optional[Dict[str, Any]]:
        config_file = Path(product_path) / "product.yaml"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CDKFallbackManager:
    """CDK フォールバック機能を管理するクラス"""
    
    def __init__(self, cdk_dir: str = "cdk"):
        self.cdk_dir = Path(cdk_dir)
        self.project_root = self.cdk_dir.parent
        
    def is_cdk_available(self) -> bool:
        """CDK が利用可能かチェック"""
        try:
            result = subprocess.run(
                ["cdk", "--version"], 
                capture_output=True, 
                text=True, 
                cwd=self.cdk_dir
            )
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("CDK CLI not found")
            return False
    
    def bootstrap_cdk_if_needed(self) -> bool:
        """必要に応じて CDK をブートストラップ"""
        try:
            logger.info("Checking CDK bootstrap status...")
            
            # CDK bootstrap の確認
            result = subprocess.run(
                ["cdk", "bootstrap", "--show-template"],
                capture_output=True,
                text=True,
                cwd=self.cdk_dir
            )
            
            if result.returncode != 0:
                logger.info("Bootstrapping CDK...")
                bootstrap_result = subprocess.run(
                    ["cdk", "bootstrap"],
                    cwd=self.cdk_dir
                )
                return bootstrap_result.returncode == 0
            
            return True
            
        except Exception as e:
            logger.error(f"CDK bootstrap failed: {str(e)}")
            return False
    
    def try_portfolio_creation_with_cdk(self, portfolio_path: str) -> Tuple[bool, str]:
        """
        CDK を使用してポートフォリオ作成を試行
        
        Args:
            portfolio_path: ポートフォリオディレクトリのパス
            
        Returns:
            (成功可否, エラーメッセージ)
        """
        try:
            logger.info(f"Attempting portfolio creation with CDK fallback: {portfolio_path}")
            
            if not self.is_cdk_available():
                return False, "CDK CLI not available"
            
            # ポートフォリオ設定を読み込み
            portfolio_config = load_portfolio_config(portfolio_path)
            if not portfolio_config:
                return False, f"Failed to load portfolio config: {portfolio_path}"
            
            # CDK コンテキストを準備
            context_args = [
                "--context", f"operation=create_portfolio",
                "--context", f"portfolio_path={portfolio_path}",
                "--context", f"portfolio_config={json.dumps(portfolio_config)}"
            ]
            
            # CDK デプロイを実行
            result = subprocess.run(
                ["cdk", "deploy", "--require-approval", "never"] + context_args,
                cwd=self.cdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"CDK portfolio creation successful: {portfolio_path}")
                return True, "Success"
            else:
                error_msg = f"CDK deployment failed: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"CDK fallback error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def try_product_creation_with_cdk(self, portfolio_path: str, product_path: str) -> Tuple[bool, str]:
        """
        CDK を使用してプロダクト作成を試行
        
        Args:
            portfolio_path: ポートフォリオディレクトリのパス
            product_path: プロダクトディレクトリのパス
            
        Returns:
            (成功可否, エラーメッセージ)
        """
        try:
            logger.info(f"Attempting product creation with CDK fallback: {product_path}")
            
            if not self.is_cdk_available():
                return False, "CDK CLI not available"
            
            # 設定を読み込み
            portfolio_config = load_portfolio_config(portfolio_path)
            product_config = load_product_config(product_path)
            
            if not portfolio_config or not product_config:
                return False, "Failed to load configuration files"
            
            # テンプレートバージョンを収集
            template_versions = self._collect_template_versions(product_path)
            if not template_versions:
                return False, "No template versions found"
            
            # CDK コンテキストを準備
            context_args = [
                "--context", f"operation=create_product",
                "--context", f"portfolio_path={portfolio_path}",
                "--context", f"product_path={product_path}",
                "--context", f"portfolio_config={json.dumps(portfolio_config)}",
                "--context", f"product_config={json.dumps(product_config)}",
                "--context", f"template_versions={json.dumps(template_versions)}"
            ]
            
            # CDK デプロイを実行
            result = subprocess.run(
                ["cdk", "deploy", "--require-approval", "never"] + context_args,
                cwd=self.cdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"CDK product creation successful: {product_path}")
                return True, "Success"
            else:
                error_msg = f"CDK deployment failed: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"CDK fallback error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _collect_template_versions(self, product_path: str) -> Dict[str, str]:
        """プロダクトディレクトリからテンプレートバージョンを収集"""
        template_versions = {}
        product_dir = Path(product_path)
        
        if not product_dir.exists():
            return template_versions
        
        for item in product_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                template_file = item / "template.yaml"
                if template_file.exists():
                    try:
                        with open(template_file, 'r', encoding='utf-8') as f:
                            template_versions[item.name] = f.read()
                    except Exception as e:
                        logger.warning(f"Failed to read template {template_file}: {str(e)}")
        
        return template_versions


def main():
    """CLI エントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CDK Fallback Integration")
    parser.add_argument("operation", choices=["portfolio", "product"], help="Operation type")
    parser.add_argument("--portfolio-path", required=True, help="Portfolio directory path")
    parser.add_argument("--product-path", help="Product directory path (for product operation)")
    
    args = parser.parse_args()
    
    manager = CDKFallbackManager()
    
    if args.operation == "portfolio":
        success, message = manager.try_portfolio_creation_with_cdk(args.portfolio_path)
    elif args.operation == "product":
        if not args.product_path:
            logger.error("Product path required for product operation")
            sys.exit(1)
        success, message = manager.try_product_creation_with_cdk(args.portfolio_path, args.product_path)
    
    if success:
        logger.info(f"CDK fallback successful: {message}")
        sys.exit(0)
    else:
        logger.error(f"CDK fallback failed: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()