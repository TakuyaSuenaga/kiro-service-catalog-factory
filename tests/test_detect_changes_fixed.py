#!/usr/bin/env python3
"""
detect-changes.py の単体テスト
変更検知機能のテストを実装
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock
import subprocess
import importlib.util

# テスト対象モジュールのインポート
script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'detect-changes.py')
spec = importlib.util.spec_from_file_location("detect_changes", script_path)
detect_changes_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(detect_changes_module)

get_changed_files = detect_changes_module.get_changed_files
parse_portfolio_path = detect_changes_module.parse_portfolio_path
detect_changes = detect_changes_module.detect_changes


class TestGetChangedFiles(unittest.TestCase):
    """get_changed_files 関数のテスト"""
    
    @patch('subprocess.run')
    @patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'})
    def test_get_changed_files_github_actions(self, mock_run):
        """GitHub Actions環境での変更ファイル取得"""
        # モックの設定
        mock_result = MagicMock()
        mock_result.stdout = 'portfolios/dev/ec2/v1.0.0/template.yaml\nportfolios/prod/rds/product.yaml\n'
        mock_run.return_value = mock_result
        
        files = get_changed_files()
        
        expected_files = [
            'portfolios/dev/ec2/v1.0.0/template.yaml',
            'portfolios/prod/rds/product.yaml'
        ]
        self.assertEqual(files, expected_files)
    
    @patch('subprocess.run')
    def test_get_changed_files_git_error(self, mock_run):
        """Gitコマンドエラーの処理"""
        # CalledProcessErrorを発生させる
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')
        
        files = get_changed_files()
        
        # エラー時は空のリストを返す
        self.assertEqual(files, [])


class TestParsePortfolioPath(unittest.TestCase):
    """parse_portfolio_path 関数のテスト"""
    
    def test_parse_portfolio_path_full_path(self):
        """完全なパスの解析"""
        path = 'portfolios/development/ec2-instances/v1.0.0/template.yaml'
        portfolio, product, version = parse_portfolio_path(path)
        
        self.assertEqual(portfolio, 'development')
        self.assertEqual(product, 'ec2-instances')
        self.assertEqual(version, 'v1.0.0')
    
    def test_parse_portfolio_path_portfolio_only(self):
        """ポートフォリオレベルのパス"""
        path = 'portfolios/development/portfolio.yaml'
        portfolio, product, version = parse_portfolio_path(path)
        
        self.assertEqual(portfolio, 'development')
        self.assertEqual(product, 'portfolio.yaml')  # ファイル名が product として返される
        self.assertEqual(version, '')
    
    def test_parse_portfolio_path_non_portfolio(self):
        """portfoliosフォルダ以外のパス"""
        path = 'src/main.py'
        portfolio, product, version = parse_portfolio_path(path)
        
        self.assertEqual(portfolio, '')
        self.assertEqual(product, '')
        self.assertEqual(version, '')


class TestDetectChanges(unittest.TestCase):
    """detect_changes 関数のテスト"""
    
    @patch.object(detect_changes_module, 'get_changed_files')
    def test_detect_changes_no_portfolio_changes(self, mock_get_files):
        """portfoliosフォルダ以外の変更のみ"""
        mock_get_files.return_value = [
            'src/main.py',
            'README.md',
            '.github/workflows/test.yml'
        ]
        
        result = detect_changes()
        
        self.assertEqual(result['portfolios'], [])
    
    @patch.object(detect_changes_module, 'get_changed_files')
    def test_detect_changes_portfolio_config_only(self, mock_get_files):
        """ポートフォリオ設定ファイルのみの変更"""
        mock_get_files.return_value = [
            'portfolios/development/portfolio.yaml'
        ]
        
        result = detect_changes()
        
        self.assertEqual(len(result['portfolios']), 1)
        portfolio = result['portfolios'][0]
        self.assertEqual(portfolio['name'], 'development')
        self.assertTrue(portfolio['config_changed'])
        self.assertEqual(len(portfolio['products']), 0)
    
    @patch.object(detect_changes_module, 'get_changed_files')
    def test_detect_changes_template_changes(self, mock_get_files):
        """テンプレートファイルの変更"""
        mock_get_files.return_value = [
            'portfolios/development/ec2-instances/v1.0.0/template.yaml',
            'portfolios/development/ec2-instances/v1.1.0/template.yaml'
        ]
        
        result = detect_changes()
        
        self.assertEqual(len(result['portfolios']), 1)
        portfolio = result['portfolios'][0]
        self.assertEqual(portfolio['name'], 'development')
        self.assertFalse(portfolio['config_changed'])
        self.assertEqual(len(portfolio['products']), 1)
        
        product = portfolio['products'][0]
        self.assertEqual(product['name'], 'ec2-instances')
        self.assertFalse(product['config_changed'])
        self.assertEqual(sorted(product['versions']), ['v1.0.0', 'v1.1.0'])
    
    @patch.object(detect_changes_module, 'get_changed_files')
    def test_detect_changes_empty_changes(self, mock_get_files):
        """変更がない場合"""
        mock_get_files.return_value = []
        
        result = detect_changes()
        
        self.assertEqual(result['portfolios'], [])


if __name__ == '__main__':
    unittest.main()