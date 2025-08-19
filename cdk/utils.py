"""
CDK スタック用ユーティリティ関数

設定ファイルの読み込みやバリデーション機能を提供
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


def load_portfolio_config(portfolio_path: str) -> Optional[Dict[str, Any]]:
    """
    ポートフォリオ設定ファイルを読み込み
    
    Args:
        portfolio_path: ポートフォリオディレクトリのパス
        
    Returns:
        ポートフォリオ設定辞書、またはエラー時は None
    """
    config_file = Path(portfolio_path) / "portfolio.yaml"
    
    if not config_file.exists():
        logger.warning(f"Portfolio config file not found: {config_file}")
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded portfolio config: {config_file}")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load portfolio config {config_file}: {str(e)}")
        return None


def load_product_config(product_path: str) -> Optional[Dict[str, Any]]:
    """
    プロダクト設定ファイルを読み込み
    
    Args:
        product_path: プロダクトディレクトリのパス
        
    Returns:
        プロダクト設定辞書、またはエラー時は None
    """
    config_file = Path(product_path) / "product.yaml"
    
    if not config_file.exists():
        logger.warning(f"Product config file not found: {config_file}")
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded product config: {config_file}")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load product config {config_file}: {str(e)}")
        return None


def validate_portfolio_config(config: Dict[str, Any]) -> bool:
    """
    ポートフォリオ設定の妥当性を検証
    
    Args:
        config: ポートフォリオ設定辞書
        
    Returns:
        妥当性検証結果
    """
    required_fields = ['name']
    
    for field in required_fields:
        if field not in config:
            logger.error(f"Missing required field in portfolio config: {field}")
            return False
    
    return True


def validate_product_config(config: Dict[str, Any]) -> bool:
    """
    プロダクト設定の妥当性を検証
    
    Args:
        config: プロダクト設定辞書
        
    Returns:
        妥当性検証結果
    """
    required_fields = ['name']
    
    for field in required_fields:
        if field not in config:
            logger.error(f"Missing required field in product config: {field}")
            return False
    
    return True


def find_template_versions(product_path: str) -> List[str]:
    """
    プロダクトディレクトリ内のテンプレートバージョンを検索
    
    Args:
        product_path: プロダクトディレクトリのパス
        
    Returns:
        バージョンディレクトリのリスト
    """
    product_dir = Path(product_path)
    versions = []
    
    if not product_dir.exists():
        logger.warning(f"Product directory not found: {product_dir}")
        return versions
    
    for item in product_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            template_file = item / "template.yaml"
            if template_file.exists():
                versions.append(item.name)
                logger.info(f"Found template version: {item.name}")
    
    return sorted(versions)


def get_template_s3_key(portfolio_name: str, product_name: str, version: str) -> str:
    """
    S3 キーを生成
    
    Args:
        portfolio_name: ポートフォリオ名
        product_name: プロダクト名
        version: バージョン
        
    Returns:
        S3 オブジェクトキー
    """
    return f"templates/{portfolio_name}/{product_name}/{version}/template.yaml"