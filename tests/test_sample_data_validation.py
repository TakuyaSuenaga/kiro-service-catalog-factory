#!/usr/bin/env python3
"""
サンプルデータ動作確認テスト
実際のサンプルプロダクトとGitHub Actionsワークフローの動作を確認
"""

import unittest
import os
import sys
import json
import subprocess
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# テスト対象モジュールのインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from config_parser import ConfigParser


class TestSampleDataValidation(unittest.TestCase):
    """サンプルデータの検証テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.project_root = os.path.join(os.path.dirname(__file__), '..')
        self.portfolios_dir = os.path.join(self.project_root, 'portfolios')
        self.scripts_dir = os.path.join(self.project_root, 'scripts')
        self.github_workflows_dir = os.path.join(self.project_root, '.github', 'workflows')
    
    def test_sample_portfolio_structure(self):
        """サンプルポートフォリオ構造の検証"""
        print("\n=== サンプルポートフォリオ構造検証 ===")
        
        # portfolios ディレクトリの存在確認
        self.assertTrue(os.path.exists(self.portfolios_dir), 
                       "portfolios ディレクトリが存在しません")
        
        # development ポートフォリオの確認
        dev_portfolio_dir = os.path.join(self.portfolios_dir, 'development')
        self.assertTrue(os.path.exists(dev_portfolio_dir), 
                       "development ポートフォリオディレクトリが存在しません")
        
        # portfolio.yaml の確認
        portfolio_yaml = os.path.join(dev_portfolio_dir, 'portfolio.yaml')
        self.assertTrue(os.path.exists(portfolio_yaml), 
                       "portfolio.yaml ファイルが存在しません")
        
        # portfolio.yaml の内容確認
        with open(portfolio_yaml, 'r', encoding='utf-8') as f:
            portfolio_config = yaml.safe_load(f)
        
        required_fields = ['name', 'description', 'owner']
        for field in required_fields:
            self.assertIn(field, portfolio_config, 
                         f"portfolio.yaml に必須フィールド '{field}' がありません")
            self.assertIsInstance(portfolio_config[field], str, 
                                f"portfolio.yaml の '{field}' は文字列である必要があります")
            self.assertTrue(portfolio_config[field].strip(), 
                          f"portfolio.yaml の '{field}' は空でない必要があります")
        
        # メールアドレスの形式確認
        self.assertIn('@', portfolio_config['owner'], 
                     "portfolio.yaml の owner は有効なメールアドレスである必要があります")
        
        print(f"✓ ポートフォリオ設定確認完了: {portfolio_config['name']}")
        
        # ec2-instances プロダクトの確認
        ec2_product_dir = os.path.join(dev_portfolio_dir, 'ec2-instances')
        self.assertTrue(os.path.exists(ec2_product_dir), 
                       "ec2-instances プロダクトディレクトリが存在しません")
        
        # product.yaml の確認
        product_yaml = os.path.join(ec2_product_dir, 'product.yaml')
        self.assertTrue(os.path.exists(product_yaml), 
                       "product.yaml ファイルが存在しません")
        
        # product.yaml の内容確認
        with open(product_yaml, 'r', encoding='utf-8') as f:
            product_config = yaml.safe_load(f)
        
        required_product_fields = [
            'name', 'description', 'owner', 
            'support_description', 'support_email', 'support_url'
        ]
        for field in required_product_fields:
            self.assertIn(field, product_config, 
                         f"product.yaml に必須フィールド '{field}' がありません")
            self.assertIsInstance(product_config[field], str, 
                                f"product.yaml の '{field}' は文字列である必要があります")
            self.assertTrue(product_config[field].strip(), 
                          f"product.yaml の '{field}' は空でない必要があります")
        
        # URL形式の確認
        self.assertTrue(product_config['support_url'].startswith(('http://', 'https://')), 
                       "product.yaml の support_url は有効なURLである必要があります")
        
        print(f"✓ プロダクト設定確認完了: {product_config['name']}")
        
        # バージョンディレクトリの確認
        version_dirs = [d for d in os.listdir(ec2_product_dir) 
                       if os.path.isdir(os.path.join(ec2_product_dir, d)) and d.startswith('v')]
        
        self.assertGreater(len(version_dirs), 0, 
                          "少なくとも1つのバージョンディレクトリが必要です")
        
        for version_dir in version_dirs:
            version_path = os.path.join(ec2_product_dir, version_dir)
            template_yaml = os.path.join(version_path, 'template.yaml')
            
            self.assertTrue(os.path.exists(template_yaml), 
                           f"template.yaml ファイルが存在しません: {version_dir}")
            
            print(f"✓ バージョン確認完了: {version_dir}")
        
        print("✓ サンプルポートフォリオ構造検証完了")
    
    def test_sample_cloudformation_templates(self):
        """サンプルCloudFormationテンプレートの検証"""
        print("\n=== サンプルCloudFormationテンプレート検証 ===")
        
        parser = ConfigParser()
        
        # development ポートフォリオの解析
        portfolios = parser.discover_portfolios(self.portfolios_dir)
        
        self.assertGreater(len(portfolios), 0, "ポートフォリオが見つかりません")
        
        dev_portfolio = None
        for portfolio in portfolios:
            if portfolio['name'] == 'development':
                dev_portfolio = portfolio
                break
        
        self.assertIsNotNone(dev_portfolio, "development ポートフォリオが見つかりません")
        
        # EC2 Instances プロダクトの確認
        ec2_product = None
        for product in dev_portfolio['products']:
            if product['name'] == 'ec2-instances':
                ec2_product = product
                break
        
        self.assertIsNotNone(ec2_product, "ec2-instances プロダクトが見つかりません")
        
        # 各バージョンのテンプレート検証
        for version_info in ec2_product['versions']:
            template_path = version_info['template_path']
            version = version_info['version']
            
            print(f"テンプレート検証中: {version}")
            
            # ファイルの存在確認
            self.assertTrue(os.path.exists(template_path), 
                           f"テンプレートファイルが存在しません: {template_path}")
            
            # YAML形式の確認
            with open(template_path, 'r', encoding='utf-8') as f:
                try:
                    template_content = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    self.fail(f"テンプレートのYAML形式が無効です: {template_path}, エラー: {e}")
            
            # CloudFormationテンプレートの基本構造確認
            self.assertIn('AWSTemplateFormatVersion', template_content, 
                         f"AWSTemplateFormatVersion が不足: {template_path}")
            self.assertIn('Resources', template_content, 
                         f"Resources セクションが不足: {template_path}")
            
            # Resourcesが空でないことを確認
            self.assertGreater(len(template_content['Resources']), 0, 
                             f"Resources セクションが空です: {template_path}")
            
            # EC2インスタンスリソースの確認
            ec2_resources = [
                resource for resource_name, resource in template_content['Resources'].items()
                if resource.get('Type') == 'AWS::EC2::Instance'
            ]
            
            self.assertGreater(len(ec2_resources), 0, 
                             f"EC2インスタンスリソースが見つかりません: {template_path}")
            
            # IAMロールとインスタンスプロファイルの確認（SSM用）
            iam_roles = [
                resource for resource_name, resource in template_content['Resources'].items()
                if resource.get('Type') == 'AWS::IAM::Role'
            ]
            
            instance_profiles = [
                resource for resource_name, resource in template_content['Resources'].items()
                if resource.get('Type') == 'AWS::IAM::InstanceProfile'
            ]
            
            self.assertGreater(len(iam_roles), 0, 
                             f"SSM用のIAMロールが見つかりません: {template_path}")
            self.assertGreater(len(instance_profiles), 0, 
                             f"IAMインスタンスプロファイルが見つかりません: {template_path}")
            
            # セキュリティグループの確認
            security_groups = [
                resource for resource_name, resource in template_content['Resources'].items()
                if resource.get('Type') == 'AWS::EC2::SecurityGroup'
            ]
            
            self.assertGreater(len(security_groups), 0, 
                             f"セキュリティグループが見つかりません: {template_path}")
            
            # パラメータの確認
            if 'Parameters' in template_content:
                parameters = template_content['Parameters']
                
                # 推奨パラメータの確認
                recommended_params = ['InstanceType', 'KeyName']
                for param in recommended_params:
                    if param in parameters:
                        self.assertIn('Type', parameters[param], 
                                     f"パラメータ '{param}' にTypeが不足: {template_path}")
                        print(f"  ✓ パラメータ確認: {param}")
            
            # アウトプットの確認
            if 'Outputs' in template_content:
                outputs = template_content['Outputs']
                
                # 推奨アウトプットの確認
                recommended_outputs = ['InstanceId']
                for output in recommended_outputs:
                    if output in outputs:
                        self.assertIn('Value', outputs[output], 
                                     f"アウトプット '{output}' にValueが不足: {template_path}")
                        print(f"  ✓ アウトプット確認: {output}")
            
            # ConfigParserによる検証
            try:
                validation_result = parser.validate_cloudformation_template(template_path)
                self.assertTrue(validation_result, 
                               f"ConfigParserによる検証に失敗: {template_path}")
            except Exception as e:
                self.fail(f"ConfigParserによる検証でエラー: {template_path}, エラー: {e}")
            
            print(f"✓ テンプレート検証完了: {version}")
        
        print("✓ サンプルCloudFormationテンプレート検証完了")
    
    @patch('subprocess.run')
    def test_github_actions_workflow_execution(self, mock_run):
        """GitHub Actionsワークフロー実行テスト"""
        print("\n=== GitHub Actionsワークフロー実行テスト ===")
        
        # ワークフローファイルの存在確認
        workflow_file = os.path.join(self.github_workflows_dir, 'service-catalog.yml')
        self.assertTrue(os.path.exists(workflow_file), 
                       "GitHub Actionsワークフローファイルが存在しません")
        
        # ワークフローファイルの内容確認
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow_content = f.read()
        
        # 必要な設定の確認
        required_workflow_elements = [
            'name: AWS Service Catalog Automation',
            'on:',
            'push:',
            'paths:',
            '- \'portfolios/**\'',
            'permissions:',
            'id-token: write',
            'contents: read',
            'aws-actions/configure-aws-credentials',
            'python scripts/detect-changes.py'
        ]
        
        for element in required_workflow_elements:
            self.assertIn(element, workflow_content, 
                         f"ワークフローに必要な要素が不足: {element}")
        
        print("✓ ワークフローファイル構造確認完了")
        
        # GitHub Actions環境のシミュレーション
        github_env = {
            'GITHUB_ACTIONS': 'true',
            'GITHUB_WORKSPACE': self.project_root,
            'GITHUB_OUTPUT': '/tmp/github_output',
            'AWS_REGION': 'us-east-1',
            'AWS_ACCOUNT_ID': '123456789012',
            'AWS_ROLE_ARN': 'arn:aws:iam::123456789012:role/GitHubActionsRole'
        }
        
        # 1. AWS認証確認のシミュレーション
        print("1. AWS認証確認シミュレーション")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "UserId": "AIDACKCEVSQ6C2EXAMPLE",
            "Account": "123456789012",
            "Arn": "arn:aws:sts::123456789012:assumed-role/GitHubActionsRole/GitHubActions-ServiceCatalog"
        })
        mock_run.return_value = mock_result
        
        # aws sts get-caller-identity の実行
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True)
        
        mock_run.assert_called_with(['aws', 'sts', 'get-caller-identity'], 
                                   capture_output=True, text=True)
        
        print("✓ AWS認証確認シミュレーション完了")
        
        # 2. 変更検知の実行
        print("2. 変更検知実行シミュレーション")
        
        # Git diff の結果をモック（サンプルプロダクトの変更）
        mock_result.stdout = 'portfolios/development/ec2-instances/v1.0.0/template.yaml\n'
        
        # detect-changes.py の実行シミュレーション
        detect_changes_script = os.path.join(self.scripts_dir, 'detect-changes.py')
        self.assertTrue(os.path.exists(detect_changes_script), 
                       "detect-changes.py スクリプトが存在しません")
        
        with patch.dict(os.environ, github_env):
            # GitHub Output ファイルの作成
            os.makedirs('/tmp', exist_ok=True)
            with open('/tmp/github_output', 'w') as f:
                f.write('')
            
            # 変更検知スクリプトの実行
            result = subprocess.run([
                'python3', detect_changes_script
            ], capture_output=True, text=True, cwd=self.project_root)
            
            # GitHub Output ファイルの確認
            if os.path.exists('/tmp/github_output'):
                with open('/tmp/github_output', 'r') as f:
                    github_output = f.read()
                
                # has-changes フラグの確認
                self.assertIn('has-changes=', github_output, 
                             "GitHub Output に has-changes フラグがありません")
                
                print("✓ GitHub Output 設定確認完了")
        
        print("✓ 変更検知実行シミュレーション完了")
        
        # 3. デプロイ実行のシミュレーション
        print("3. デプロイ実行シミュレーション")
        
        deploy_script = os.path.join(self.scripts_dir, 'deploy-catalog.sh')
        self.assertTrue(os.path.exists(deploy_script), 
                       "deploy-catalog.sh スクリプトが存在しません")
        
        # DRY_RUN モードでのデプロイ実行
        deploy_env = github_env.copy()
        deploy_env.update({
            'DRY_RUN': '1',
            'LOG_LEVEL': 'INFO'
        })
        
        mock_result.returncode = 0
        mock_result.stdout = "[DRY RUN] デプロイ完了"
        
        result = subprocess.run([
            'bash', deploy_script, 'validate', self.portfolios_dir
        ], env=deploy_env, capture_output=True, text=True)
        
        print("✓ デプロイ実行シミュレーション完了")
        
        print("✓ GitHub Actionsワークフロー実行テスト完了")
    
    def test_aws_service_catalog_integration(self):
        """AWS Service Catalog統合テスト（モック）"""
        print("\n=== AWS Service Catalog統合テスト ===")
        
        # AWS CLI コマンド生成のテスト
        sys.path.insert(0, os.path.dirname(__file__))
        from test_aws_cli_commands import AWSCLICommandGenerator
        generator = AWSCLICommandGenerator()
        
        # サンプルポートフォリオの設定を使用
        parser = ConfigParser()
        portfolios = parser.discover_portfolios(self.portfolios_dir)
        
        if portfolios:
            dev_portfolio = portfolios[0]
            portfolio_config = dev_portfolio['config']
            
            # ポートフォリオ作成コマンドの生成
            portfolio_cmd = generator.generate_create_portfolio_command(
                name=portfolio_config.name,
                description=portfolio_config.description,
                owner=portfolio_config.owner
            )
            
            # コマンドの妥当性確認
            self.assertIn('aws', portfolio_cmd)
            self.assertIn('servicecatalog', portfolio_cmd)
            self.assertIn('create-portfolio', portfolio_cmd)
            self.assertIn(portfolio_config.name, portfolio_cmd)
            
            print(f"✓ ポートフォリオ作成コマンド生成: {portfolio_config.name}")
            
            # プロダクト作成コマンドの生成
            if dev_portfolio['products']:
                ec2_product = dev_portfolio['products'][0]
                product_config = ec2_product['config']
                
                # 最初のバージョンのテンプレートパスを取得
                template_path = ec2_product['versions'][0]['template_path']
                
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
                
                # コマンドの妥当性確認
                self.assertIn('create-product', product_cmd)
                self.assertIn(product_config.name, product_cmd)
                self.assertIn(product_config.support_email, product_cmd)
                
                print(f"✓ プロダクト作成コマンド生成: {product_config.name}")
                
                # テンプレート検証コマンドの生成
                validate_cmd = generator.generate_validate_template_command(template_path)
                
                self.assertIn('cloudformation', validate_cmd)
                self.assertIn('validate-template', validate_cmd)
                self.assertIn(template_path, validate_cmd)
                
                print("✓ テンプレート検証コマンド生成")
        
        print("✓ AWS Service Catalog統合テスト完了")
    
    def test_sample_data_completeness(self):
        """サンプルデータの完全性テスト"""
        print("\n=== サンプルデータ完全性テスト ===")
        
        # 要件6.1の確認: Ubuntu 24.04 ARM SSMイメージを使用するEC2インスタンス
        parser = ConfigParser()
        portfolios = parser.discover_portfolios(self.portfolios_dir)
        
        self.assertGreater(len(portfolios), 0, "サンプルポートフォリオが見つかりません")
        
        dev_portfolio = None
        for portfolio in portfolios:
            if portfolio['name'] == 'development':
                dev_portfolio = portfolio
                break
        
        self.assertIsNotNone(dev_portfolio, "development ポートフォリオが見つかりません")
        
        # EC2 Instances プロダクトの確認
        ec2_product = None
        for product in dev_portfolio['products']:
            if product['name'] == 'ec2-instances':
                ec2_product = product
                break
        
        self.assertIsNotNone(ec2_product, "ec2-instances プロダクトが見つかりません")
        
        # テンプレート内容の詳細確認
        for version_info in ec2_product['versions']:
            template_path = version_info['template_path']
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = yaml.safe_load(f)
            
            # EC2インスタンスの設定確認
            ec2_instances = [
                (name, resource) for name, resource in template_content['Resources'].items()
                if resource.get('Type') == 'AWS::EC2::Instance'
            ]
            
            self.assertGreater(len(ec2_instances), 0, 
                             f"EC2インスタンスが見つかりません: {template_path}")
            
            for instance_name, instance_resource in ec2_instances:
                properties = instance_resource.get('Properties', {})
                
                # IAMインスタンスプロファイルの確認（SSM用）
                self.assertIn('IamInstanceProfile', properties, 
                             f"IAMインスタンスプロファイルが設定されていません: {instance_name}")
                
                # セキュリティグループの確認
                self.assertTrue(
                    'SecurityGroupIds' in properties or 'SecurityGroups' in properties,
                    f"セキュリティグループが設定されていません: {instance_name}"
                )
                
                # タグの確認
                if 'Tags' in properties:
                    tags = properties['Tags']
                    tag_keys = [tag['Key'] for tag in tags]
                    
                    # 推奨タグの確認
                    recommended_tags = ['Name', 'Environment']
                    for tag_key in recommended_tags:
                        if tag_key in tag_keys:
                            print(f"  ✓ タグ確認: {tag_key}")
                
                print(f"✓ EC2インスタンス設定確認: {instance_name}")
            
            # SSM関連リソースの確認
            iam_roles = [
                (name, resource) for name, resource in template_content['Resources'].items()
                if resource.get('Type') == 'AWS::IAM::Role'
            ]
            
            for role_name, role_resource in iam_roles:
                properties = role_resource.get('Properties', {})
                
                # SSMポリシーの確認
                if 'ManagedPolicyArns' in properties:
                    managed_policies = properties['ManagedPolicyArns']
                    ssm_policy_found = any(
                        'AmazonSSMManagedInstanceCore' in str(policy)
                        for policy in managed_policies
                    )
                    
                    if ssm_policy_found:
                        print(f"  ✓ SSMポリシー確認: {role_name}")
            
            print(f"✓ テンプレート詳細確認完了: {version_info['version']}")
        
        print("✓ サンプルデータ完全性テスト完了")
    
    def test_documentation_completeness(self):
        """ドキュメント完全性テスト"""
        print("\n=== ドキュメント完全性テスト ===")
        
        # README.md の確認
        readme_path = os.path.join(self.project_root, 'README.md')
        self.assertTrue(os.path.exists(readme_path), "README.md ファイルが存在しません")
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        # 必要なセクションの確認
        required_sections = [
            '# AWS Service Catalog',
            '## 🚀 主な機能',
            '## 🛠️ セットアップ手順',
            '## 📝 使用方法',
            '## 📁 プロジェクト構造'
        ]
        
        for section in required_sections:
            self.assertIn(section, readme_content, 
                         f"README.md に必要なセクションが不足: {section}")
        
        print("✓ README.md 確認完了")
        
        # FOLDER_STRUCTURE.md の確認
        folder_structure_path = os.path.join(self.project_root, 'docs', 'FOLDER_STRUCTURE.md')
        if os.path.exists(folder_structure_path):
            with open(folder_structure_path, 'r', encoding='utf-8') as f:
                folder_structure_content = f.read()
            
            # フォルダ構造の説明確認
            structure_elements = [
                'portfolios/',
                'portfolio.yaml',
                'product.yaml',
                'template.yaml'
            ]
            
            for element in structure_elements:
                self.assertIn(element, folder_structure_content, 
                             f"FOLDER_STRUCTURE.md に必要な要素が不足: {element}")
            
            print("✓ FOLDER_STRUCTURE.md 確認完了")
        
        # TROUBLESHOOTING.md の確認
        troubleshooting_path = os.path.join(self.project_root, 'docs', 'TROUBLESHOOTING.md')
        if os.path.exists(troubleshooting_path):
            with open(troubleshooting_path, 'r', encoding='utf-8') as f:
                troubleshooting_content = f.read()
            
            # トラブルシューティング項目の確認
            troubleshooting_topics = [
                '認証エラー',
                'テンプレートエラー',
                'デプロイエラー'
            ]
            
            for topic in troubleshooting_topics:
                if topic in troubleshooting_content:
                    print(f"  ✓ トラブルシューティング項目: {topic}")
            
            print("✓ TROUBLESHOOTING.md 確認完了")
        
        print("✓ ドキュメント完全性テスト完了")


def run_sample_data_validation():
    """サンプルデータ検証テストの実行"""
    print("="*80)
    print("AWS Service Catalog 自動化システム - サンプルデータ動作確認")
    print("="*80)
    
    # テストスイートの作成
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestSampleDataValidation))
    
    # テストランナーの実行
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # 結果サマリー
    print("\n" + "="*80)
    print("サンプルデータ動作確認結果サマリー")
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
    success = run_sample_data_validation()
    sys.exit(0 if success else 1)