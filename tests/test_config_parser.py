#!/usr/bin/env python3
"""
config_parser.py の単体テスト
設定ファイル解析機能のテストを実装
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# テスト対象モジュールのインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from config_parser import (
    ConfigParser, PortfolioConfig, ProductConfig, 
    ConfigValidationError
)


class TestPortfolioConfig(unittest.TestCase):
    """PortfolioConfig データクラスのテスト"""
    
    def test_from_dict_valid_data(self):
        """有効なデータからPortfolioConfigを作成"""
        data = {
            'name': 'Test Portfolio',
            'description': 'テスト用ポートフォリオ',
            'owner': 'test@example.com'
        }
        config = PortfolioConfig.from_dict(data)
        
        self.assertEqual(config.name, 'Test Portfolio')
        self.assertEqual(config.description, 'テスト用ポートフォリオ')
        self.assertEqual(config.owner, 'test@example.com')
    
    def test_from_dict_missing_field(self):
        """必須フィールドが不足している場合のエラー"""
        data = {
            'name': 'Test Portfolio',
            'description': 'テスト用ポートフォリオ'
            # owner フィールドが不足
        }
        with self.assertRaises(KeyError):
            PortfolioConfig.from_dict(data)


class TestProductConfig(unittest.TestCase):
    """ProductConfig データクラスのテスト"""
    
    def test_from_dict_valid_data(self):
        """有効なデータからProductConfigを作成"""
        data = {
            'name': 'Test Product',
            'description': 'テスト用プロダクト',
            'owner': 'test@example.com',
            'support_description': 'サポート説明',
            'support_email': 'support@example.com',
            'support_url': 'https://example.com/support'
        }
        config = ProductConfig.from_dict(data)
        
        self.assertEqual(config.name, 'Test Product')
        self.assertEqual(config.description, 'テスト用プロダクト')
        self.assertEqual(config.owner, 'test@example.com')
        self.assertEqual(config.support_description, 'サポート説明')
        self.assertEqual(config.support_email, 'support@example.com')
        self.assertEqual(config.support_url, 'https://example.com/support')


class TestConfigParser(unittest.TestCase):
    """ConfigParser クラスのテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.parser = ConfigParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_yaml_file_valid(self):
        """有効なYAMLファイルの読み込み"""
        yaml_content = """
name: "Test Portfolio"
description: "テスト用ポートフォリオ"
owner: "test@example.com"
"""
        temp_file = os.path.join(self.temp_dir, 'test.yaml')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        data = self.parser.load_yaml_file(temp_file)
        
        self.assertEqual(data['name'], 'Test Portfolio')
        self.assertEqual(data['description'], 'テスト用ポートフォリオ')
        self.assertEqual(data['owner'], 'test@example.com')
    
    def test_load_yaml_file_not_found(self):
        """存在しないファイルの読み込みエラー"""
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.load_yaml_file('/nonexistent/file.yaml')
        
        self.assertIn('ファイルが見つかりません', str(cm.exception))
    
    def test_load_yaml_file_empty(self):
        """空のYAMLファイルのエラー"""
        temp_file = os.path.join(self.temp_dir, 'empty.yaml')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write('')
        
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.load_yaml_file(temp_file)
        
        self.assertIn('空のYAMLファイル', str(cm.exception))
    
    def test_load_yaml_file_invalid_syntax(self):
        """無効なYAML構文のエラー"""
        yaml_content = """
name: "Test Portfolio
description: invalid yaml
"""
        temp_file = os.path.join(self.temp_dir, 'invalid.yaml')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.load_yaml_file(temp_file)
        
        self.assertIn('YAML解析エラー', str(cm.exception))
    
    def test_validate_portfolio_config_valid(self):
        """有効なポートフォリオ設定の検証"""
        data = {
            'name': 'Test Portfolio',
            'description': 'テスト用ポートフォリオ',
            'owner': 'test@example.com'
        }
        
        # エラーが発生しないことを確認
        try:
            self.parser.validate_portfolio_config(data, 'test.yaml')
        except ConfigValidationError:
            self.fail('有効な設定でConfigValidationErrorが発生しました')
    
    def test_validate_portfolio_config_missing_field(self):
        """必須フィールドが不足している場合のエラー"""
        data = {
            'name': 'Test Portfolio',
            'description': 'テスト用ポートフォリオ'
            # owner フィールドが不足
        }
        
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.validate_portfolio_config(data, 'test.yaml')
        
        self.assertIn('必須フィールド', str(cm.exception))
        self.assertIn('owner', str(cm.exception))
    
    def test_validate_portfolio_config_empty_field(self):
        """空のフィールドのエラー"""
        data = {
            'name': '',
            'description': 'テスト用ポートフォリオ',
            'owner': 'test@example.com'
        }
        
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.validate_portfolio_config(data, 'test.yaml')
        
        self.assertIn('空でない文字列である必要があります', str(cm.exception))
    
    def test_validate_portfolio_config_invalid_email(self):
        """無効なメールアドレスのエラー"""
        data = {
            'name': 'Test Portfolio',
            'description': 'テスト用ポートフォリオ',
            'owner': 'invalid-email'
        }
        
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.validate_portfolio_config(data, 'test.yaml')
        
        self.assertIn('有効なメールアドレスである必要があります', str(cm.exception))
    
    def test_validate_product_config_valid(self):
        """有効なプロダクト設定の検証"""
        data = {
            'name': 'Test Product',
            'description': 'テスト用プロダクト',
            'owner': 'test@example.com',
            'support_description': 'サポート説明',
            'support_email': 'support@example.com',
            'support_url': 'https://example.com/support'
        }
        
        # エラーが発生しないことを確認
        try:
            self.parser.validate_product_config(data, 'test.yaml')
        except ConfigValidationError:
            self.fail('有効な設定でConfigValidationErrorが発生しました')
    
    def test_validate_product_config_invalid_url(self):
        """無効なURLのエラー"""
        data = {
            'name': 'Test Product',
            'description': 'テスト用プロダクト',
            'owner': 'test@example.com',
            'support_description': 'サポート説明',
            'support_email': 'support@example.com',
            'support_url': 'invalid-url'
        }
        
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.validate_product_config(data, 'test.yaml')
        
        self.assertIn('有効なURLである必要があります', str(cm.exception))
    
    def test_parse_portfolio_config_success(self):
        """ポートフォリオ設定ファイルの正常な解析"""
        yaml_content = """
name: "Test Portfolio"
description: "テスト用ポートフォリオ"
owner: "test@example.com"
"""
        temp_file = os.path.join(self.temp_dir, 'portfolio.yaml')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        config = self.parser.parse_portfolio_config(temp_file)
        
        self.assertIsInstance(config, PortfolioConfig)
        self.assertEqual(config.name, 'Test Portfolio')
        self.assertEqual(config.description, 'テスト用ポートフォリオ')
        self.assertEqual(config.owner, 'test@example.com')
    
    def test_parse_product_config_success(self):
        """プロダクト設定ファイルの正常な解析"""
        yaml_content = """
name: "Test Product"
description: "テスト用プロダクト"
owner: "test@example.com"
support_description: "サポート説明"
support_email: "support@example.com"
support_url: "https://example.com/support"
"""
        temp_file = os.path.join(self.temp_dir, 'product.yaml')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        config = self.parser.parse_product_config(temp_file)
        
        self.assertIsInstance(config, ProductConfig)
        self.assertEqual(config.name, 'Test Product')
        self.assertEqual(config.support_email, 'support@example.com')
    
    def test_validate_cloudformation_template_valid(self):
        """有効なCloudFormationテンプレートの検証"""
        template_content = """
AWSTemplateFormatVersion: '2010-09-09'
Description: 'テスト用テンプレート'
Resources:
  TestResource:
    Type: 'AWS::S3::Bucket'
    Properties:
      BucketName: 'test-bucket'
"""
        temp_file = os.path.join(self.temp_dir, 'template.yaml')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        result = self.parser.validate_cloudformation_template(temp_file)
        self.assertTrue(result)
    
    def test_validate_cloudformation_template_no_resources(self):
        """Resourcesセクションがないテンプレートのエラー"""
        template_content = """
AWSTemplateFormatVersion: '2010-09-09'
Description: 'テスト用テンプレート'
"""
        temp_file = os.path.join(self.temp_dir, 'template.yaml')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.validate_cloudformation_template(temp_file)
        
        self.assertIn('Resources セクションが必要です', str(cm.exception))
    
    def test_validate_cloudformation_template_empty_resources(self):
        """空のResourcesセクションのエラー"""
        template_content = """
AWSTemplateFormatVersion: '2010-09-09'
Description: 'テスト用テンプレート'
Resources: {}
"""
        temp_file = os.path.join(self.temp_dir, 'template.yaml')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.validate_cloudformation_template(temp_file)
        
        self.assertIn('少なくとも1つのリソースが必要です', str(cm.exception))
    
    def test_discover_portfolios_empty_directory(self):
        """空のポートフォリオディレクトリの処理"""
        portfolios = self.parser.discover_portfolios(self.temp_dir)
        self.assertEqual(len(portfolios), 0)
    
    def test_discover_portfolios_with_data(self):
        """ポートフォリオデータがある場合の探索"""
        # ポートフォリオディレクトリ構造を作成
        portfolio_dir = os.path.join(self.temp_dir, 'test-portfolio')
        product_dir = os.path.join(portfolio_dir, 'test-product')
        version_dir = os.path.join(product_dir, 'v1.0.0')
        
        os.makedirs(version_dir)
        
        # ポートフォリオ設定ファイル
        portfolio_yaml = os.path.join(portfolio_dir, 'portfolio.yaml')
        with open(portfolio_yaml, 'w', encoding='utf-8') as f:
            f.write("""
name: "Test Portfolio"
description: "テスト用ポートフォリオ"
owner: "test@example.com"
""")
        
        # プロダクト設定ファイル
        product_yaml = os.path.join(product_dir, 'product.yaml')
        with open(product_yaml, 'w', encoding='utf-8') as f:
            f.write("""
name: "Test Product"
description: "テスト用プロダクト"
owner: "test@example.com"
support_description: "サポート説明"
support_email: "support@example.com"
support_url: "https://example.com/support"
""")
        
        # テンプレートファイル
        template_yaml = os.path.join(version_dir, 'template.yaml')
        with open(template_yaml, 'w', encoding='utf-8') as f:
            f.write("""
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  TestResource:
    Type: 'AWS::S3::Bucket'
""")
        
        portfolios = self.parser.discover_portfolios(self.temp_dir)
        
        self.assertEqual(len(portfolios), 1)
        self.assertEqual(portfolios[0]['name'], 'test-portfolio')
        self.assertEqual(portfolios[0]['config'].name, 'Test Portfolio')
        self.assertEqual(len(portfolios[0]['products']), 1)
        self.assertEqual(portfolios[0]['products'][0]['name'], 'test-product')
        self.assertEqual(len(portfolios[0]['products'][0]['versions']), 1)
        self.assertEqual(portfolios[0]['products'][0]['versions'][0]['version'], 'v1.0.0')


class TestConfigParserErrorHandling(unittest.TestCase):
    """ConfigParser のエラーハンドリングテスト"""
    
    def setUp(self):
        self.parser = ConfigParser()
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_load_yaml_file_permission_error(self, mock_file):
        """ファイル読み込み権限エラーのハンドリング"""
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.load_yaml_file('test.yaml')
        
        self.assertIn('ファイル読み込みエラー', str(cm.exception))
    
    def test_validate_portfolio_config_non_string_field(self):
        """文字列以外のフィールド値のエラー"""
        data = {
            'name': 123,  # 数値
            'description': 'テスト用ポートフォリオ',
            'owner': 'test@example.com'
        }
        
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.validate_portfolio_config(data, 'test.yaml')
        
        self.assertIn('空でない文字列である必要があります', str(cm.exception))
    
    def test_discover_portfolios_nonexistent_directory(self):
        """存在しないディレクトリの処理"""
        with self.assertRaises(ConfigValidationError) as cm:
            self.parser.discover_portfolios('/nonexistent/directory')
        
        self.assertIn('ポートフォリオディレクトリが見つかりません', str(cm.exception))


if __name__ == '__main__':
    unittest.main()