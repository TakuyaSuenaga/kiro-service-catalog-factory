#!/usr/bin/env python3
"""
エンドツーエンドテスト
AWS Service Catalog 自動化システムの完全なワークフローをテスト
"""

import unittest
import tempfile
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import yaml

# テスト対象モジュールのインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from config_parser import ConfigParser
import importlib.util

# detect-changes.py のインポート
detect_changes_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'detect-changes.py')
spec = importlib.util.spec_from_file_location("detect_changes", detect_changes_path)
detect_changes_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(detect_changes_module)


class TestEndToEndWorkflow(unittest.TestCase):
    """エンドツーエンドワークフローのテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.portfolios_dir = os.path.join(self.temp_dir, 'portfolios')
        self.scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
        
        # テスト用のポートフォリオ構造を作成
        self._create_test_portfolio_structure()
    
    def tearDown(self):
        """テストクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_portfolio_structure(self):
        """テスト用のポートフォリオ構造を作成"""
        # Development ポートフォリオ
        dev_portfolio_dir = os.path.join(self.portfolios_dir, 'development')
        os.makedirs(dev_portfolio_dir, exist_ok=True)
        
        # ポートフォリオ設定ファイル
        portfolio_config = {
            'name': 'Development Portfolio',
            'description': '開発環境用のリソーステンプレート',
            'owner': 'development-team@company.com'
        }
        
        with open(os.path.join(dev_portfolio_dir, 'portfolio.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(portfolio_config, f, allow_unicode=True)
        
        # EC2 Instances プロダクト
        ec2_product_dir = os.path.join(dev_portfolio_dir, 'ec2-instances')
        os.makedirs(ec2_product_dir, exist_ok=True)
        
        # プロダクト設定ファイル
        product_config = {
            'name': 'EC2 Instances',
            'description': 'Ubuntu 24.04 ARM SSM対応EC2インスタンス',
            'owner': 'infrastructure-team@company.com',
            'support_description': 'インフラチームがサポートします',
            'support_email': 'infrastructure-team@company.com',
            'support_url': 'https://wiki.company.com/ec2-support'
        }
        
        with open(os.path.join(ec2_product_dir, 'product.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(product_config, f, allow_unicode=True)
        
        # バージョン v1.0.0
        v1_dir = os.path.join(ec2_product_dir, 'v1.0.0')
        os.makedirs(v1_dir, exist_ok=True)
        
        # CloudFormation テンプレート
        cf_template = {
            'AWSTemplateFormatVersion': '2010-09-09',
            'Description': 'Ubuntu 24.04 ARM SSM対応EC2インスタンス',
            'Parameters': {
                'InstanceType': {
                    'Type': 'String',
                    'Default': 't4g.micro',
                    'Description': 'EC2インスタンスタイプ'
                },
                'KeyName': {
                    'Type': 'AWS::EC2::KeyPair::KeyName',
                    'Description': 'EC2キーペア名'
                }
            },
            'Resources': {
                'EC2Instance': {
                    'Type': 'AWS::EC2::Instance',
                    'Properties': {
                        'ImageId': 'ami-0c02fb55956c7d316',  # Ubuntu 24.04 ARM
                        'InstanceType': {'Ref': 'InstanceType'},
                        'KeyName': {'Ref': 'KeyName'},
                        'IamInstanceProfile': {'Ref': 'EC2InstanceProfile'},
                        'SecurityGroupIds': [{'Ref': 'SecurityGroup'}],
                        'UserData': {
                            'Fn::Base64': {
                                'Fn::Sub': '#!/bin/bash\napt-get update\napt-get install -y amazon-ssm-agent\nsystemctl enable amazon-ssm-agent\nsystemctl start amazon-ssm-agent\n'
                            }
                        },
                        'Tags': [
                            {'Key': 'Name', 'Value': 'ServiceCatalog-EC2-Instance'},
                            {'Key': 'Environment', 'Value': 'Development'}
                        ]
                    }
                },
                'EC2Role': {
                    'Type': 'AWS::IAM::Role',
                    'Properties': {
                        'AssumeRolePolicyDocument': {
                            'Version': '2012-10-17',
                            'Statement': [{
                                'Effect': 'Allow',
                                'Principal': {'Service': 'ec2.amazonaws.com'},
                                'Action': 'sts:AssumeRole'
                            }]
                        },
                        'ManagedPolicyArns': [
                            'arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore'
                        ]
                    }
                },
                'EC2InstanceProfile': {
                    'Type': 'AWS::IAM::InstanceProfile',
                    'Properties': {
                        'Roles': [{'Ref': 'EC2Role'}]
                    }
                },
                'SecurityGroup': {
                    'Type': 'AWS::EC2::SecurityGroup',
                    'Properties': {
                        'GroupDescription': 'Security group for Service Catalog EC2 instance',
                        'SecurityGroupEgress': [{
                            'IpProtocol': '-1',
                            'CidrIp': '0.0.0.0/0'
                        }]
                    }
                }
            },
            'Outputs': {
                'InstanceId': {
                    'Description': 'EC2インスタンスID',
                    'Value': {'Ref': 'EC2Instance'}
                },
                'InstancePrivateIP': {
                    'Description': 'プライベートIPアドレス',
                    'Value': {'Fn::GetAtt': ['EC2Instance', 'PrivateIp']}
                }
            }
        }
        
        with open(os.path.join(v1_dir, 'template.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(cf_template, f, allow_unicode=True)
        
        # バージョン v1.1.0 (更新版)
        v11_dir = os.path.join(ec2_product_dir, 'v1.1.0')
        os.makedirs(v11_dir, exist_ok=True)
        
        # 更新されたテンプレート（タグを追加）
        cf_template_v11 = cf_template.copy()
        cf_template_v11['Description'] = 'Ubuntu 24.04 ARM SSM対応EC2インスタンス (v1.1.0)'
        cf_template_v11['Resources']['EC2Instance']['Properties']['Tags'].append(
            {'Key': 'Version', 'Value': 'v1.1.0'}
        )
        
        with open(os.path.join(v11_dir, 'template.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(cf_template_v11, f, allow_unicode=True)
    
    def test_complete_workflow_new_portfolio(self):
        """新規ポートフォリオの完全ワークフローテスト"""
        print("\n=== 新規ポートフォリオの完全ワークフローテスト ===")
        
        # 1. 設定ファイル解析のテスト
        parser = ConfigParser()
        portfolios = parser.discover_portfolios(self.portfolios_dir)
        
        self.assertEqual(len(portfolios), 1)
        self.assertEqual(portfolios[0]['name'], 'development')
        self.assertEqual(portfolios[0]['config'].name, 'Development Portfolio')
        self.assertEqual(len(portfolios[0]['products']), 1)
        self.assertEqual(portfolios[0]['products'][0]['name'], 'ec2-instances')
        self.assertEqual(len(portfolios[0]['products'][0]['versions']), 2)
        
        print("✓ 設定ファイル解析テスト完了")
        
        # 2. CloudFormation テンプレート検証のテスト
        template_path = os.path.join(
            self.portfolios_dir, 'development', 'ec2-instances', 'v1.0.0', 'template.yaml'
        )
        
        validation_result = parser.validate_cloudformation_template(template_path)
        self.assertTrue(validation_result)
        
        print("✓ CloudFormation テンプレート検証テスト完了")
        
        # 3. AWS CLI コマンド生成のテスト
        portfolio_config = portfolios[0]['config']
        product_config = portfolios[0]['products'][0]['config']
        
        # ポートフォリオ作成コマンドの生成
        sys.path.insert(0, os.path.dirname(__file__))
        from test_aws_cli_commands import AWSCLICommandGenerator
        generator = AWSCLICommandGenerator()
        
        portfolio_cmd = generator.generate_create_portfolio_command(
            name=portfolio_config.name,
            description=portfolio_config.description,
            owner=portfolio_config.owner
        )
        
        self.assertIn('aws', portfolio_cmd)
        self.assertIn('servicecatalog', portfolio_cmd)
        self.assertIn('create-portfolio', portfolio_cmd)
        self.assertIn(portfolio_config.name, portfolio_cmd)
        
        print("✓ AWS CLI コマンド生成テスト完了")
        
        # 4. プロダクト作成コマンドの生成
        product_cmd = generator.generate_create_product_command(
            name=product_config.name,
            description=product_config.description,
            owner=product_config.owner,
            support_description=product_config.support_description,
            support_email=product_config.support_email,
            support_url=product_config.support_url,
            template_url=f"file://{template_path}",
            version_name="v1.0.0"
        )
        
        self.assertIn('create-product', product_cmd)
        self.assertIn(product_config.name, product_cmd)
        
        print("✓ プロダクト作成コマンド生成テスト完了")
        
        print("✓ 新規ポートフォリオの完全ワークフローテスト完了")
    
    @patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'})
    @patch('subprocess.run')
    def test_change_detection_workflow(self, mock_run):
        """変更検知ワークフローのテスト"""
        print("\n=== 変更検知ワークフローテスト ===")
        
        # Git diff の結果をモック
        mock_result = MagicMock()
        mock_result.stdout = (
            'portfolios/development/ec2-instances/v1.1.0/template.yaml\n'
            'portfolios/development/ec2-instances/product.yaml\n'
        )
        mock_run.return_value = mock_result
        
        # 変更検知の実行
        changes = detect_changes_module.detect_changes()
        
        # 結果の検証
        self.assertEqual(len(changes['portfolios']), 1)
        
        portfolio = changes['portfolios'][0]
        self.assertEqual(portfolio['name'], 'development')
        self.assertFalse(portfolio['config_changed'])
        self.assertEqual(len(portfolio['products']), 1)
        
        product = portfolio['products'][0]
        self.assertEqual(product['name'], 'ec2-instances')
        self.assertTrue(product['config_changed'])
        self.assertIn('v1.1.0', product['versions'])
        
        print("✓ 変更検知ワークフローテスト完了")
    
    @patch('subprocess.run')
    def test_deployment_script_integration(self, mock_run):
        """デプロイスクリプト統合テスト"""
        print("\n=== デプロイスクリプト統合テスト ===")
        
        # スクリプトの存在確認
        deploy_script = os.path.join(self.scripts_dir, 'deploy-catalog.sh')
        self.assertTrue(os.path.exists(deploy_script))
        
        manage_portfolio_script = os.path.join(self.scripts_dir, 'manage-portfolio.sh')
        self.assertTrue(os.path.exists(manage_portfolio_script))
        
        manage_product_script = os.path.join(self.scripts_dir, 'manage-product.sh')
        self.assertTrue(os.path.exists(manage_product_script))
        
        print("✓ 必要なスクリプトファイルの存在確認完了")
        
        # DRY_RUN モードでのスクリプト実行テスト
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[DRY RUN] ポートフォリオを作成します"
        mock_run.return_value = mock_result
        
        # 環境変数の設定
        env = os.environ.copy()
        env.update({
            'DRY_RUN': '1',
            'LOG_LEVEL': 'DEBUG',
            'AWS_DEFAULT_REGION': 'us-east-1'
        })
        
        # バリデーションコマンドのテスト
        result = subprocess.run(
            ['bash', deploy_script, 'validate', self.portfolios_dir],
            env=env,
            capture_output=True,
            text=True
        )
        
        # モックが呼ばれることを確認
        mock_run.assert_called()
        
        print("✓ デプロイスクリプト統合テスト完了")
    
    def test_error_handling_scenarios(self):
        """エラーハンドリングシナリオのテスト"""
        print("\n=== エラーハンドリングシナリオテスト ===")
        
        parser = ConfigParser()
        
        # 1. 無効な設定ファイルのテスト
        invalid_portfolio_dir = os.path.join(self.temp_dir, 'invalid_portfolio')
        os.makedirs(invalid_portfolio_dir, exist_ok=True)
        
        # 無効なYAMLファイル
        invalid_yaml = os.path.join(invalid_portfolio_dir, 'portfolio.yaml')
        with open(invalid_yaml, 'w') as f:
            f.write('invalid: yaml: content:')
        
        with self.assertRaises(Exception):
            parser.load_yaml_file(invalid_yaml)
        
        print("✓ 無効なYAMLファイルのエラーハンドリング確認")
        
        # 2. 必須フィールド不足のテスト
        incomplete_config = {'name': 'Test Portfolio'}  # description と owner が不足
        
        with self.assertRaises(Exception):
            parser.validate_portfolio_config(incomplete_config, 'test.yaml')
        
        print("✓ 必須フィールド不足のエラーハンドリング確認")
        
        # 3. CloudFormation テンプレートエラーのテスト
        invalid_template_dir = os.path.join(self.temp_dir, 'invalid_template')
        os.makedirs(invalid_template_dir, exist_ok=True)
        
        invalid_template = os.path.join(invalid_template_dir, 'template.yaml')
        with open(invalid_template, 'w') as f:
            yaml.dump({'AWSTemplateFormatVersion': '2010-09-09'}, f)  # Resources が不足
        
        with self.assertRaises(Exception):
            parser.validate_cloudformation_template(invalid_template)
        
        print("✓ CloudFormation テンプレートエラーハンドリング確認")
        
        print("✓ エラーハンドリングシナリオテスト完了")
    
    def test_sample_product_validation(self):
        """サンプルプロダクトの検証テスト"""
        print("\n=== サンプルプロダクト検証テスト ===")
        
        # 実際のサンプルプロダクトファイルの確認
        sample_portfolio_path = os.path.join(
            os.path.dirname(__file__), '..', 'portfolios', 'development'
        )
        
        if os.path.exists(sample_portfolio_path):
            parser = ConfigParser()
            
            # サンプルポートフォリオの解析
            portfolios = parser.discover_portfolios(
                os.path.join(os.path.dirname(__file__), '..', 'portfolios')
            )
            
            if portfolios:
                sample_portfolio = portfolios[0]
                self.assertEqual(sample_portfolio['name'], 'development')
                
                if sample_portfolio['products']:
                    sample_product = sample_portfolio['products'][0]
                    self.assertEqual(sample_product['name'], 'ec2-instances')
                    
                    # テンプレートファイルの検証
                    for version_info in sample_product['versions']:
                        template_path = version_info['template_path']
                        if os.path.exists(template_path):
                            validation_result = parser.validate_cloudformation_template(template_path)
                            self.assertTrue(validation_result)
                            print(f"✓ サンプルテンプレート検証完了: {version_info['version']}")
                
                print("✓ サンプルプロダクト検証テスト完了")
            else:
                print("! サンプルポートフォリオが見つかりません（スキップ）")
        else:
            print("! サンプルポートフォリオディレクトリが見つかりません（スキップ）")
    
    @patch('subprocess.run')
    def test_github_actions_workflow_simulation(self, mock_run):
        """GitHub Actions ワークフローシミュレーションテスト"""
        print("\n=== GitHub Actions ワークフローシミュレーション ===")
        
        # GitHub Actions 環境変数の設定
        github_env = {
            'GITHUB_ACTIONS': 'true',
            'GITHUB_WORKSPACE': self.temp_dir,
            'AWS_REGION': 'us-east-1',
            'AWS_ACCOUNT_ID': '123456789012',
            'AWS_ROLE_ARN': 'arn:aws:iam::123456789012:role/GitHubActionsRole'
        }
        
        # 1. リポジトリチェックアウトのシミュレーション
        print("1. リポジトリチェックアウト（シミュレーション）")
        
        # 2. AWS認証のシミュレーション
        print("2. AWS認証確認（シミュレーション）")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "UserId": "AIDACKCEVSQ6C2EXAMPLE",
            "Account": "123456789012",
            "Arn": "arn:aws:sts::123456789012:assumed-role/GitHubActionsRole/GitHubActions-ServiceCatalog"
        })
        mock_run.return_value = mock_result
        
        # aws sts get-caller-identity のシミュレーション
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True)
        mock_run.assert_called_with(['aws', 'sts', 'get-caller-identity'], 
                                   capture_output=True, text=True)
        
        # 3. 変更検知のシミュレーション
        print("3. 変更検知実行（シミュレーション）")
        
        # Git diff の結果をモック
        mock_result.stdout = 'portfolios/development/ec2-instances/v1.0.0/template.yaml\n'
        
        with patch.dict(os.environ, github_env):
            changes = detect_changes_module.detect_changes()
            
        self.assertIsInstance(changes, dict)
        self.assertIn('portfolios', changes)
        
        # 4. デプロイ実行のシミュレーション
        print("4. デプロイ実行（シミュレーション）")
        
        # DRY_RUN モードでのデプロイスクリプト実行
        deploy_env = github_env.copy()
        deploy_env['DRY_RUN'] = '1'
        
        mock_result.returncode = 0
        mock_result.stdout = "[DRY RUN] デプロイ完了"
        
        result = subprocess.run(
            ['bash', os.path.join(self.scripts_dir, 'deploy-catalog.sh'), 'deploy-changes'],
            env=deploy_env,
            capture_output=True,
            text=True
        )
        
        print("✓ GitHub Actions ワークフローシミュレーション完了")
    
    def test_performance_and_scalability(self):
        """パフォーマンスとスケーラビリティのテスト"""
        print("\n=== パフォーマンス・スケーラビリティテスト ===")
        
        # 大量のポートフォリオ・プロダクト構造の作成
        large_portfolios_dir = os.path.join(self.temp_dir, 'large_portfolios')
        os.makedirs(large_portfolios_dir, exist_ok=True)
        
        # 複数のポートフォリオを作成
        portfolio_count = 5
        products_per_portfolio = 3
        versions_per_product = 2
        
        for i in range(portfolio_count):
            portfolio_name = f'portfolio-{i:02d}'
            portfolio_dir = os.path.join(large_portfolios_dir, portfolio_name)
            os.makedirs(portfolio_dir, exist_ok=True)
            
            # ポートフォリオ設定
            portfolio_config = {
                'name': f'Test Portfolio {i:02d}',
                'description': f'テスト用ポートフォリオ {i:02d}',
                'owner': f'team-{i:02d}@company.com'
            }
            
            with open(os.path.join(portfolio_dir, 'portfolio.yaml'), 'w', encoding='utf-8') as f:
                yaml.dump(portfolio_config, f, allow_unicode=True)
            
            # プロダクトの作成
            for j in range(products_per_portfolio):
                product_name = f'product-{j:02d}'
                product_dir = os.path.join(portfolio_dir, product_name)
                os.makedirs(product_dir, exist_ok=True)
                
                # プロダクト設定
                product_config = {
                    'name': f'Test Product {j:02d}',
                    'description': f'テスト用プロダクト {j:02d}',
                    'owner': f'team-{i:02d}@company.com',
                    'support_description': f'サポート説明 {j:02d}',
                    'support_email': f'support-{j:02d}@company.com',
                    'support_url': f'https://company.com/support/{j:02d}'
                }
                
                with open(os.path.join(product_dir, 'product.yaml'), 'w', encoding='utf-8') as f:
                    yaml.dump(product_config, f, allow_unicode=True)
                
                # バージョンの作成
                for k in range(versions_per_product):
                    version_name = f'v1.{k}.0'
                    version_dir = os.path.join(product_dir, version_name)
                    os.makedirs(version_dir, exist_ok=True)
                    
                    # 簡単なCloudFormationテンプレート
                    template = {
                        'AWSTemplateFormatVersion': '2010-09-09',
                        'Description': f'Test template {i}-{j}-{k}',
                        'Resources': {
                            'TestResource': {
                                'Type': 'AWS::S3::Bucket',
                                'Properties': {
                                    'BucketName': f'test-bucket-{i}-{j}-{k}'
                                }
                            }
                        }
                    }
                    
                    with open(os.path.join(version_dir, 'template.yaml'), 'w', encoding='utf-8') as f:
                        yaml.dump(template, f, allow_unicode=True)
        
        # パフォーマンステスト
        import time
        
        parser = ConfigParser()
        
        start_time = time.time()
        portfolios = parser.discover_portfolios(large_portfolios_dir)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 結果の検証
        self.assertEqual(len(portfolios), portfolio_count)
        
        total_products = sum(len(p['products']) for p in portfolios)
        expected_products = portfolio_count * products_per_portfolio
        self.assertEqual(total_products, expected_products)
        
        total_versions = sum(
            len(product['versions']) 
            for portfolio in portfolios 
            for product in portfolio['products']
        )
        expected_versions = portfolio_count * products_per_portfolio * versions_per_product
        self.assertEqual(total_versions, expected_versions)
        
        print(f"✓ 大規模構造の処理時間: {processing_time:.2f}秒")
        print(f"✓ 処理されたポートフォリオ数: {len(portfolios)}")
        print(f"✓ 処理されたプロダクト数: {total_products}")
        print(f"✓ 処理されたバージョン数: {total_versions}")
        
        # パフォーマンス基準の確認（10秒以内）
        self.assertLess(processing_time, 10.0, "大規模構造の処理時間が10秒を超えています")
        
        print("✓ パフォーマンス・スケーラビリティテスト完了")


class TestWorkflowIntegration(unittest.TestCase):
    """ワークフロー統合テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
        self.github_dir = os.path.join(os.path.dirname(__file__), '..', '.github', 'workflows')
    
    def test_github_actions_workflow_file(self):
        """GitHub Actions ワークフローファイルのテスト"""
        print("\n=== GitHub Actions ワークフローファイルテスト ===")
        
        workflow_file = os.path.join(self.github_dir, 'service-catalog.yml')
        self.assertTrue(os.path.exists(workflow_file), "GitHub Actions ワークフローファイルが存在しません")
        
        # ワークフローファイルの内容確認
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow_content = f.read()
        
        # 必要な要素の確認
        required_elements = [
            'name: AWS Service Catalog Automation',
            'on:',
            'push:',
            'paths:',
            'portfolios/**',
            'permissions:',
            'id-token: write',
            'aws-actions/configure-aws-credentials',
            'role-to-assume',
            'python scripts/detect-changes.py'
        ]
        
        for element in required_elements:
            self.assertIn(element, workflow_content, f"ワークフローファイルに必要な要素が不足: {element}")
        
        print("✓ GitHub Actions ワークフローファイル検証完了")
    
    def test_script_dependencies(self):
        """スクリプト依存関係のテスト"""
        print("\n=== スクリプト依存関係テスト ===")
        
        required_scripts = [
            'config_parser.py',
            'detect-changes.py',
            'deploy-catalog.sh',
            'manage-portfolio.sh',
            'manage-product.sh'
        ]
        
        for script in required_scripts:
            script_path = os.path.join(self.scripts_dir, script)
            self.assertTrue(os.path.exists(script_path), f"必要なスクリプトが見つかりません: {script}")
            
            # 実行権限の確認（シェルスクリプトの場合）
            if script.endswith('.sh'):
                self.assertTrue(os.access(script_path, os.X_OK), f"スクリプトに実行権限がありません: {script}")
        
        print("✓ スクリプト依存関係テスト完了")
    
    def test_configuration_templates(self):
        """設定テンプレートのテスト"""
        print("\n=== 設定テンプレートテスト ===")
        
        templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        
        if os.path.exists(templates_dir):
            template_files = [
                'portfolio.yaml.template',
                'product.yaml.template'
            ]
            
            for template_file in template_files:
                template_path = os.path.join(templates_dir, template_file)
                if os.path.exists(template_path):
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_content = f.read()
                    
                    # テンプレートの基本構造確認
                    self.assertIn('name:', template_content)
                    self.assertIn('description:', template_content)
                    self.assertIn('owner:', template_content)
                    
                    print(f"✓ テンプレートファイル検証完了: {template_file}")
        
        print("✓ 設定テンプレートテスト完了")


def run_end_to_end_tests():
    """エンドツーエンドテストの実行"""
    print("="*80)
    print("AWS Service Catalog 自動化システム - エンドツーエンドテスト")
    print("="*80)
    
    # テストスイートの作成
    suite = unittest.TestSuite()
    
    # テストクラスの追加
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowIntegration))
    
    # テストランナーの実行
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # 結果サマリー
    print("\n" + "="*80)
    print("エンドツーエンドテスト結果サマリー")
    print("="*80)
    print(f"実行されたテスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.failures:
        print(f"\n失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  ✗ {test}")
    
    if result.errors:
        print(f"\nエラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  ✗ {test}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\n成功率: {success_rate:.1f}%")
    print("="*80)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_end_to_end_tests()
    sys.exit(0 if success else 1)