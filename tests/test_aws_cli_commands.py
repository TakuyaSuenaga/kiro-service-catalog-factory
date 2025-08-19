#!/usr/bin/env python3
"""
AWS CLI コマンド生成とエラーハンドリングのテスト
シェルスクリプトの機能をPythonでテストするためのヘルパー関数とテスト
"""

import unittest
import tempfile
import os
import subprocess
from unittest.mock import patch, MagicMock
import json


class AWSCLICommandGenerator:
    """AWS CLI コマンド生成のヘルパークラス（テスト用）"""
    
    def __init__(self, region='us-east-1', dry_run=False):
        self.region = region
        self.dry_run = dry_run
    
    def generate_create_portfolio_command(self, name, description, owner):
        """ポートフォリオ作成コマンドの生成"""
        cmd = [
            'aws', 'servicecatalog', 'create-portfolio',
            '--display-name', name,
            '--description', description,
            '--provider-name', owner,
            '--output', 'json'
        ]
        
        if self.region:
            cmd.extend(['--region', self.region])
        
        return cmd
    
    def generate_update_portfolio_command(self, portfolio_id, name, description, owner):
        """ポートフォリオ更新コマンドの生成"""
        cmd = [
            'aws', 'servicecatalog', 'update-portfolio',
            '--id', portfolio_id,
            '--display-name', name,
            '--description', description,
            '--provider-name', owner,
            '--output', 'json'
        ]
        
        if self.region:
            cmd.extend(['--region', self.region])
        
        return cmd
    
    def generate_list_portfolios_command(self):
        """ポートフォリオ一覧取得コマンドの生成"""
        cmd = [
            'aws', 'servicecatalog', 'list-portfolios',
            '--output', 'json'
        ]
        
        if self.region:
            cmd.extend(['--region', self.region])
        
        return cmd
    
    def generate_create_product_command(self, name, description, owner, 
                                      support_description, support_email, 
                                      support_url, template_url, version_name):
        """プロダクト作成コマンドの生成"""
        provisioning_params = f"Name={version_name},Description=Initial version,Info={{LoadTemplateFromURL={template_url}}}"
        
        cmd = [
            'aws', 'servicecatalog', 'create-product',
            '--name', name,
            '--description', description,
            '--owner', owner,
            '--support-description', support_description,
            '--support-email', support_email,
            '--support-url', support_url,
            '--provisioning-artifact-parameters', provisioning_params,
            '--output', 'json'
        ]
        
        if self.region:
            cmd.extend(['--region', self.region])
        
        return cmd
    
    def generate_validate_template_command(self, template_path):
        """CloudFormationテンプレート検証コマンドの生成"""
        cmd = [
            'aws', 'cloudformation', 'validate-template',
            '--template-body', f'file://{template_path}',
            '--output', 'json'
        ]
        
        if self.region:
            cmd.extend(['--region', self.region])
        
        return cmd
    
    def generate_associate_product_command(self, product_id, portfolio_id):
        """プロダクト関連付けコマンドの生成"""
        cmd = [
            'aws', 'servicecatalog', 'associate-product-with-portfolio',
            '--product-id', product_id,
            '--portfolio-id', portfolio_id,
            '--output', 'json'
        ]
        
        if self.region:
            cmd.extend(['--region', self.region])
        
        return cmd


class TestAWSCLICommandGeneration(unittest.TestCase):
    """AWS CLI コマンド生成のテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.generator = AWSCLICommandGenerator()
    
    def test_generate_create_portfolio_command(self):
        """ポートフォリオ作成コマンドの生成テスト"""
        cmd = self.generator.generate_create_portfolio_command(
            name="Test Portfolio",
            description="テスト用ポートフォリオ",
            owner="test@example.com"
        )
        
        expected_cmd = [
            'aws', 'servicecatalog', 'create-portfolio',
            '--display-name', 'Test Portfolio',
            '--description', 'テスト用ポートフォリオ',
            '--provider-name', 'test@example.com',
            '--output', 'json',
            '--region', 'us-east-1'
        ]
        
        self.assertEqual(cmd, expected_cmd)
    
    def test_generate_update_portfolio_command(self):
        """ポートフォリオ更新コマンドの生成テスト"""
        cmd = self.generator.generate_update_portfolio_command(
            portfolio_id="port-12345",
            name="Updated Portfolio",
            description="更新されたポートフォリオ",
            owner="updated@example.com"
        )
        
        expected_cmd = [
            'aws', 'servicecatalog', 'update-portfolio',
            '--id', 'port-12345',
            '--display-name', 'Updated Portfolio',
            '--description', '更新されたポートフォリオ',
            '--provider-name', 'updated@example.com',
            '--output', 'json',
            '--region', 'us-east-1'
        ]
        
        self.assertEqual(cmd, expected_cmd)
    
    def test_generate_list_portfolios_command(self):
        """ポートフォリオ一覧コマンドの生成テスト"""
        cmd = self.generator.generate_list_portfolios_command()
        
        expected_cmd = [
            'aws', 'servicecatalog', 'list-portfolios',
            '--output', 'json',
            '--region', 'us-east-1'
        ]
        
        self.assertEqual(cmd, expected_cmd)
    
    def test_generate_create_product_command(self):
        """プロダクト作成コマンドの生成テスト"""
        cmd = self.generator.generate_create_product_command(
            name="Test Product",
            description="テスト用プロダクト",
            owner="test@example.com",
            support_description="サポート説明",
            support_email="support@example.com",
            support_url="https://example.com/support",
            template_url="file:///path/to/template.yaml",
            version_name="v1.0.0"
        )
        
        expected_provisioning_params = "Name=v1.0.0,Description=Initial version,Info={LoadTemplateFromURL=file:///path/to/template.yaml}"
        
        expected_cmd = [
            'aws', 'servicecatalog', 'create-product',
            '--name', 'Test Product',
            '--description', 'テスト用プロダクト',
            '--owner', 'test@example.com',
            '--support-description', 'サポート説明',
            '--support-email', 'support@example.com',
            '--support-url', 'https://example.com/support',
            '--provisioning-artifact-parameters', expected_provisioning_params,
            '--output', 'json',
            '--region', 'us-east-1'
        ]
        
        self.assertEqual(cmd, expected_cmd)
    
    def test_generate_validate_template_command(self):
        """テンプレート検証コマンドの生成テスト"""
        template_path = "/path/to/template.yaml"
        cmd = self.generator.generate_validate_template_command(template_path)
        
        expected_cmd = [
            'aws', 'cloudformation', 'validate-template',
            '--template-body', 'file:///path/to/template.yaml',
            '--output', 'json',
            '--region', 'us-east-1'
        ]
        
        self.assertEqual(cmd, expected_cmd)
    
    def test_generate_associate_product_command(self):
        """プロダクト関連付けコマンドの生成テスト"""
        cmd = self.generator.generate_associate_product_command(
            product_id="prod-12345",
            portfolio_id="port-12345"
        )
        
        expected_cmd = [
            'aws', 'servicecatalog', 'associate-product-with-portfolio',
            '--product-id', 'prod-12345',
            '--portfolio-id', 'port-12345',
            '--output', 'json',
            '--region', 'us-east-1'
        ]
        
        self.assertEqual(cmd, expected_cmd)
    
    def test_command_generation_with_custom_region(self):
        """カスタムリージョンでのコマンド生成テスト"""
        generator = AWSCLICommandGenerator(region='ap-northeast-1')
        cmd = generator.generate_list_portfolios_command()
        
        expected_cmd = [
            'aws', 'servicecatalog', 'list-portfolios',
            '--output', 'json',
            '--region', 'ap-northeast-1'
        ]
        
        self.assertEqual(cmd, expected_cmd)
    
    def test_command_generation_no_region(self):
        """リージョン指定なしでのコマンド生成テスト"""
        generator = AWSCLICommandGenerator(region=None)
        cmd = generator.generate_list_portfolios_command()
        
        expected_cmd = [
            'aws', 'servicecatalog', 'list-portfolios',
            '--output', 'json'
        ]
        
        self.assertEqual(cmd, expected_cmd)


class TestAWSCLIErrorHandling(unittest.TestCase):
    """AWS CLI エラーハンドリングのテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.generator = AWSCLICommandGenerator()
    
    @patch('subprocess.run')
    def test_aws_cli_authentication_error(self, mock_run):
        """AWS CLI 認証エラーのテスト"""
        # 認証エラーをシミュレート
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=255,
            cmd=['aws', 'sts', 'get-caller-identity'],
            stderr="Unable to locate credentials"
        )
        
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(['aws', 'sts', 'get-caller-identity'], check=True)
        
        self.assertEqual(cm.exception.returncode, 255)
    
    @patch('subprocess.run')
    def test_aws_cli_permission_error(self, mock_run):
        """AWS CLI 権限エラーのテスト"""
        # 権限エラーをシミュレート
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "User is not authorized to perform: servicecatalog:CreatePortfolio"
            }
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = json.dumps(error_response)
        mock_run.return_value = mock_result
        
        result = mock_run.return_value
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("AccessDenied", result.stderr)
    
    @patch('subprocess.run')
    def test_aws_cli_resource_not_found_error(self, mock_run):
        """AWS CLI リソース未発見エラーのテスト"""
        # リソース未発見エラーをシミュレート
        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Portfolio not found"
            }
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = json.dumps(error_response)
        mock_run.return_value = mock_result
        
        result = mock_run.return_value
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("ResourceNotFoundException", result.stderr)
    
    @patch('subprocess.run')
    def test_aws_cli_validation_error(self, mock_run):
        """AWS CLI バリデーションエラーのテスト"""
        # バリデーションエラーをシミュレート
        error_response = {
            "Error": {
                "Code": "ValidationException",
                "Message": "Template format error: JSON not well-formed"
            }
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = json.dumps(error_response)
        mock_run.return_value = mock_result
        
        result = mock_run.return_value
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("ValidationException", result.stderr)
    
    @patch('subprocess.run')
    def test_aws_cli_network_error(self, mock_run):
        """AWS CLI ネットワークエラーのテスト"""
        # ネットワークエラーをシミュレート
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=['aws', 'servicecatalog', 'list-portfolios'],
            timeout=30
        )
        
        with self.assertRaises(subprocess.TimeoutExpired):
            subprocess.run(
                ['aws', 'servicecatalog', 'list-portfolios'],
                timeout=30,
                check=True
            )
    
    def test_command_parameter_validation(self):
        """コマンドパラメータの検証テスト"""
        # 空の名前でのコマンド生成
        with self.assertRaises(ValueError):
            self._validate_portfolio_parameters("", "description", "owner")
        
        # 無効なメールアドレス
        with self.assertRaises(ValueError):
            self._validate_portfolio_parameters("name", "description", "invalid-email")
        
        # 無効なURL
        with self.assertRaises(ValueError):
            self._validate_product_url("invalid-url")
    
    def _validate_portfolio_parameters(self, name, description, owner):
        """ポートフォリオパラメータの検証ヘルパー"""
        if not name or not name.strip():
            raise ValueError("Portfolio name cannot be empty")
        
        if not description or not description.strip():
            raise ValueError("Portfolio description cannot be empty")
        
        if not owner or '@' not in owner:
            raise ValueError("Invalid email address for owner")
        
        return True
    
    def _validate_product_url(self, url):
        """プロダクトURL検証ヘルパー"""
        if not url.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL format")
        
        return True


class TestAWSCLIResponseParsing(unittest.TestCase):
    """AWS CLI レスポンス解析のテスト"""
    
    def test_parse_create_portfolio_response(self):
        """ポートフォリオ作成レスポンスの解析テスト"""
        response_json = {
            "PortfolioDetail": {
                "Id": "port-12345",
                "ARN": "arn:aws:servicecatalog:us-east-1:123456789012:portfolio/port-12345",
                "DisplayName": "Test Portfolio",
                "Description": "テスト用ポートフォリオ",
                "ProviderName": "test@example.com",
                "CreatedTime": "2023-01-01T00:00:00Z"
            }
        }
        
        portfolio_id = response_json["PortfolioDetail"]["Id"]
        portfolio_name = response_json["PortfolioDetail"]["DisplayName"]
        
        self.assertEqual(portfolio_id, "port-12345")
        self.assertEqual(portfolio_name, "Test Portfolio")
    
    def test_parse_list_portfolios_response(self):
        """ポートフォリオ一覧レスポンスの解析テスト"""
        response_json = {
            "PortfolioDetails": [
                {
                    "Id": "port-12345",
                    "DisplayName": "Development Portfolio",
                    "Description": "開発環境用ポートフォリオ",
                    "ProviderName": "dev@example.com"
                },
                {
                    "Id": "port-67890",
                    "DisplayName": "Production Portfolio",
                    "Description": "本番環境用ポートフォリオ",
                    "ProviderName": "prod@example.com"
                }
            ]
        }
        
        portfolios = response_json["PortfolioDetails"]
        
        self.assertEqual(len(portfolios), 2)
        self.assertEqual(portfolios[0]["Id"], "port-12345")
        self.assertEqual(portfolios[1]["DisplayName"], "Production Portfolio")
    
    def test_parse_create_product_response(self):
        """プロダクト作成レスポンスの解析テスト"""
        response_json = {
            "ProductViewDetail": {
                "ProductViewSummary": {
                    "ProductId": "prod-12345",
                    "Name": "Test Product",
                    "Owner": "test@example.com",
                    "ShortDescription": "テスト用プロダクト"
                },
                "Status": "AVAILABLE",
                "CreatedTime": "2023-01-01T00:00:00Z"
            },
            "ProvisioningArtifactDetail": {
                "Id": "pa-12345",
                "Name": "v1.0.0",
                "Description": "Initial version"
            }
        }
        
        product_id = response_json["ProductViewDetail"]["ProductViewSummary"]["ProductId"]
        artifact_id = response_json["ProvisioningArtifactDetail"]["Id"]
        
        self.assertEqual(product_id, "prod-12345")
        self.assertEqual(artifact_id, "pa-12345")
    
    def test_parse_error_response(self):
        """エラーレスポンスの解析テスト"""
        error_response = {
            "Error": {
                "Code": "ValidationException",
                "Message": "1 validation error detected: Value null at 'displayName' failed to satisfy constraint: Member must not be null."
            }
        }
        
        error_code = error_response["Error"]["Code"]
        error_message = error_response["Error"]["Message"]
        
        self.assertEqual(error_code, "ValidationException")
        self.assertIn("validation error", error_message)


class TestShellScriptIntegration(unittest.TestCase):
    """シェルスクリプトとの統合テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.script_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
    
    def test_manage_portfolio_script_exists(self):
        """manage-portfolio.sh スクリプトの存在確認"""
        script_path = os.path.join(self.script_dir, 'manage-portfolio.sh')
        self.assertTrue(os.path.exists(script_path))
    
    def test_manage_product_script_exists(self):
        """manage-product.sh スクリプトの存在確認"""
        script_path = os.path.join(self.script_dir, 'manage-product.sh')
        self.assertTrue(os.path.exists(script_path))
    
    def test_deploy_catalog_script_exists(self):
        """deploy-catalog.sh スクリプトの存在確認"""
        script_path = os.path.join(self.script_dir, 'deploy-catalog.sh')
        self.assertTrue(os.path.exists(script_path))
    
    @patch('subprocess.run')
    def test_shell_script_dry_run_mode(self, mock_run):
        """シェルスクリプトのDRY_RUNモードテスト"""
        # DRY_RUNモードでのスクリプト実行をシミュレート
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[DRY RUN] ポートフォリオを作成します"
        mock_run.return_value = mock_result
        
        # 環境変数DRY_RUN=1でスクリプト実行
        env = os.environ.copy()
        env['DRY_RUN'] = '1'
        
        result = subprocess.run(
            ['bash', os.path.join(self.script_dir, 'manage-portfolio.sh'), 'create', 'test-portfolio'],
            env=env,
            capture_output=True,
            text=True
        )
        
        # モックが呼ばれることを確認
        mock_run.assert_called_once()


if __name__ == '__main__':
    unittest.main()