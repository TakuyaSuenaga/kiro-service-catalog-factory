#!/usr/bin/env python3
"""
CDK セットアップのテストスクリプト

CDK プロジェクトが正しく設定されているかを検証
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_cdk_installation():
    """CDK CLI のインストール確認"""
    try:
        result = subprocess.run(
            ["cdk", "--version"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            logger.info(f"CDK CLI installed: {result.stdout.strip()}")
            return True
        else:
            logger.error("CDK CLI not found")
            return False
    except FileNotFoundError:
        logger.error("CDK CLI not installed")
        return False


def test_python_dependencies():
    """Python 依存関係の確認"""
    try:
        import aws_cdk
        import constructs
        import yaml
        
        logger.info(f"aws-cdk-lib version: {aws_cdk.__version__}")
        logger.info("All Python dependencies available")
        return True
        
    except ImportError as e:
        logger.error(f"Missing Python dependency: {str(e)}")
        return False


def test_cdk_project_structure():
    """CDK プロジェクト構造の確認"""
    required_files = [
        "app.py",
        "service_catalog_stack.py",
        "cdk.json",
        "requirements.txt",
        "utils.py",
        "deploy_with_cdk.py",
        "fallback_integration.py"
    ]
    
    missing_files = []
    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        logger.error(f"Missing CDK project files: {missing_files}")
        return False
    else:
        logger.info("All required CDK project files present")
        return True


def test_cdk_synth():
    """CDK synth の実行テスト"""
    try:
        result = subprocess.run(
            ["cdk", "synth"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            logger.info("CDK synth successful")
            return True
        else:
            logger.error(f"CDK synth failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"CDK synth error: {str(e)}")
        return False


def main():
    """メインテスト関数"""
    logger.info("Starting CDK setup validation...")
    
    tests = [
        ("CDK CLI Installation", test_cdk_installation),
        ("Python Dependencies", test_python_dependencies),
        ("CDK Project Structure", test_cdk_project_structure),
        ("CDK Synth", test_cdk_synth)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✓ {test_name}: PASSED")
            else:
                logger.error(f"✗ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name}: ERROR - {str(e)}")
            results.append((test_name, False))
    
    # 結果サマリー
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\nTest Summary: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All CDK setup tests passed! ✓")
        sys.exit(0)
    else:
        logger.error("Some CDK setup tests failed! ✗")
        sys.exit(1)


if __name__ == "__main__":
    main()