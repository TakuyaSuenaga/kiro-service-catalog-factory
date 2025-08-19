#!/usr/bin/env python3
"""
設定ファイル解析スクリプト
portfolio.yaml と product.yaml を解析し、検証する機能を提供
"""

try:
    import yaml
except ImportError:
    print("警告: PyYAMLがインストールされていません。pip install PyYAMLでインストールしてください。")
    import json
    yaml = None
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PortfolioConfig:
    """ポートフォリオ設定を表すデータクラス"""
    name: str
    description: str
    owner: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioConfig':
        """辞書からPortfolioConfigインスタンスを作成"""
        return cls(
            name=data['name'],
            description=data['description'],
            owner=data['owner']
        )


@dataclass
class ProductConfig:
    """プロダクト設定を表すデータクラス"""
    name: str
    description: str
    owner: str
    support_description: str
    support_email: str
    support_url: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductConfig':
        """辞書からProductConfigインスタンスを作成"""
        return cls(
            name=data['name'],
            description=data['description'],
            owner=data['owner'],
            support_description=data['support_description'],
            support_email=data['support_email'],
            support_url=data['support_url']
        )


class ConfigValidationError(Exception):
    """設定ファイル検証エラー"""
    pass


class ConfigParser:
    """設定ファイル解析クラス"""
    
    def __init__(self):
        self.portfolio_required_fields = ['name', 'description', 'owner']
        self.product_required_fields = [
            'name', 'description', 'owner', 'support_description', 
            'support_email', 'support_url'
        ]
    
    def load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """YAMLファイルを読み込む"""
        if yaml is None:
            raise ConfigValidationError("PyYAMLがインストールされていません。pip install PyYAMLでインストールしてください。")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                if data is None:
                    raise ConfigValidationError(f"空のYAMLファイル: {file_path}")
                return data
        except FileNotFoundError:
            raise ConfigValidationError(f"ファイルが見つかりません: {file_path}")
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"YAML解析エラー in {file_path}: {str(e)}")
        except Exception as e:
            raise ConfigValidationError(f"ファイル読み込みエラー {file_path}: {str(e)}")
    
    def validate_portfolio_config(self, data: Dict[str, Any], file_path: str) -> None:
        """ポートフォリオ設定の検証"""
        # 必須フィールドの確認
        for field in self.portfolio_required_fields:
            if field not in data:
                raise ConfigValidationError(
                    f"必須フィールド '{field}' が見つかりません in {file_path}"
                )
            if not isinstance(data[field], str) or not data[field].strip():
                raise ConfigValidationError(
                    f"フィールド '{field}' は空でない文字列である必要があります in {file_path}"
                )
        
        # メールアドレスの簡単な検証
        if '@' not in data['owner']:
            raise ConfigValidationError(
                f"owner フィールドは有効なメールアドレスである必要があります in {file_path}"
            )
    
    def validate_product_config(self, data: Dict[str, Any], file_path: str) -> None:
        """プロダクト設定の検証"""
        # 必須フィールドの確認
        for field in self.product_required_fields:
            if field not in data:
                raise ConfigValidationError(
                    f"必須フィールド '{field}' が見つかりません in {file_path}"
                )
            if not isinstance(data[field], str) or not data[field].strip():
                raise ConfigValidationError(
                    f"フィールド '{field}' は空でない文字列である必要があります in {file_path}"
                )
        
        # メールアドレスの検証
        for email_field in ['owner', 'support_email']:
            if '@' not in data[email_field]:
                raise ConfigValidationError(
                    f"{email_field} フィールドは有効なメールアドレスである必要があります in {file_path}"
                )
        
        # URLの簡単な検証
        if not (data['support_url'].startswith('http://') or 
                data['support_url'].startswith('https://')):
            raise ConfigValidationError(
                f"support_url フィールドは有効なURLである必要があります in {file_path}"
            )
    
    def parse_portfolio_config(self, file_path: str) -> PortfolioConfig:
        """ポートフォリオ設定ファイルを解析"""
        data = self.load_yaml_file(file_path)
        self.validate_portfolio_config(data, file_path)
        return PortfolioConfig.from_dict(data)
    
    def parse_product_config(self, file_path: str) -> ProductConfig:
        """プロダクト設定ファイルを解析"""
        data = self.load_yaml_file(file_path)
        self.validate_product_config(data, file_path)
        return ProductConfig.from_dict(data)
    
    def discover_portfolios(self, portfolios_dir: str = "portfolios") -> List[Dict[str, Any]]:
        """ポートフォリオディレクトリを探索し、設定情報を収集"""
        portfolios = []
        portfolios_path = Path(portfolios_dir)
        
        if not portfolios_path.exists():
            raise ConfigValidationError(f"ポートフォリオディレクトリが見つかりません: {portfolios_dir}")
        
        for portfolio_dir in portfolios_path.iterdir():
            if not portfolio_dir.is_dir():
                continue
            
            portfolio_yaml = portfolio_dir / "portfolio.yaml"
            if not portfolio_yaml.exists():
                print(f"警告: portfolio.yaml が見つかりません in {portfolio_dir}")
                continue
            
            try:
                portfolio_config = self.parse_portfolio_config(str(portfolio_yaml))
                portfolio_info = {
                    'path': str(portfolio_dir),
                    'name': portfolio_dir.name,
                    'config': portfolio_config,
                    'products': []
                }
                
                # プロダクトを探索
                for product_dir in portfolio_dir.iterdir():
                    if not product_dir.is_dir() or product_dir.name.startswith('.'):
                        continue
                    
                    product_yaml = product_dir / "product.yaml"
                    if not product_yaml.exists():
                        print(f"警告: product.yaml が見つかりません in {product_dir}")
                        continue
                    
                    try:
                        product_config = self.parse_product_config(str(product_yaml))
                        
                        # バージョンディレクトリを探索
                        versions = []
                        for version_dir in product_dir.iterdir():
                            if (version_dir.is_dir() and 
                                not version_dir.name.startswith('.') and
                                version_dir.name != 'product.yaml'):
                                
                                template_file = version_dir / "template.yaml"
                                if template_file.exists():
                                    versions.append({
                                        'version': version_dir.name,
                                        'template_path': str(template_file)
                                    })
                        
                        product_info = {
                            'path': str(product_dir),
                            'name': product_dir.name,
                            'config': product_config,
                            'versions': versions
                        }
                        portfolio_info['products'].append(product_info)
                        
                    except ConfigValidationError as e:
                        print(f"エラー: プロダクト設定の解析に失敗 {product_dir}: {e}")
                        continue
                
                portfolios.append(portfolio_info)
                
            except ConfigValidationError as e:
                print(f"エラー: ポートフォリオ設定の解析に失敗 {portfolio_dir}: {e}")
                continue
        
        return portfolios
    
    def validate_cloudformation_template(self, template_path: str) -> bool:
        """CloudFormationテンプレートの基本的な検証"""
        try:
            data = self.load_yaml_file(template_path)
            
            # CloudFormationテンプレートの必須フィールド確認
            if 'AWSTemplateFormatVersion' not in data and 'Resources' not in data:
                raise ConfigValidationError(
                    f"有効なCloudFormationテンプレートではありません: {template_path}"
                )
            
            if 'Resources' not in data or not isinstance(data['Resources'], dict):
                raise ConfigValidationError(
                    f"Resources セクションが必要です: {template_path}"
                )
            
            if len(data['Resources']) == 0:
                raise ConfigValidationError(
                    f"少なくとも1つのリソースが必要です: {template_path}"
                )
            
            return True
            
        except ConfigValidationError:
            raise
        except Exception as e:
            raise ConfigValidationError(f"テンプレート検証エラー {template_path}: {str(e)}")


def main():
    """メイン関数 - コマンドライン実行用"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python config_parser.py discover [portfolios_dir]")
        print("  python config_parser.py validate-portfolio <portfolio.yaml>")
        print("  python config_parser.py validate-product <product.yaml>")
        print("  python config_parser.py validate-template <template.yaml>")
        sys.exit(1)
    
    parser = ConfigParser()
    command = sys.argv[1]
    
    try:
        if command == "discover":
            portfolios_dir = sys.argv[2] if len(sys.argv) > 2 else "portfolios"
            portfolios = parser.discover_portfolios(portfolios_dir)
            
            print(f"発見されたポートフォリオ: {len(portfolios)}")
            for portfolio in portfolios:
                print(f"\nポートフォリオ: {portfolio['name']}")
                print(f"  パス: {portfolio['path']}")
                print(f"  名前: {portfolio['config'].name}")
                print(f"  説明: {portfolio['config'].description}")
                print(f"  所有者: {portfolio['config'].owner}")
                print(f"  プロダクト数: {len(portfolio['products'])}")
                
                for product in portfolio['products']:
                    print(f"    プロダクト: {product['name']}")
                    print(f"      バージョン数: {len(product['versions'])}")
                    for version in product['versions']:
                        print(f"        - {version['version']}: {version['template_path']}")
        
        elif command == "validate-portfolio":
            if len(sys.argv) < 3:
                print("エラー: portfolio.yaml ファイルパスが必要です")
                sys.exit(1)
            
            config = parser.parse_portfolio_config(sys.argv[2])
            print("ポートフォリオ設定の検証に成功しました")
            print(f"名前: {config.name}")
            print(f"説明: {config.description}")
            print(f"所有者: {config.owner}")
        
        elif command == "validate-product":
            if len(sys.argv) < 3:
                print("エラー: product.yaml ファイルパスが必要です")
                sys.exit(1)
            
            config = parser.parse_product_config(sys.argv[2])
            print("プロダクト設定の検証に成功しました")
            print(f"名前: {config.name}")
            print(f"説明: {config.description}")
            print(f"所有者: {config.owner}")
        
        elif command == "validate-template":
            if len(sys.argv) < 3:
                print("エラー: template.yaml ファイルパスが必要です")
                sys.exit(1)
            
            parser.validate_cloudformation_template(sys.argv[2])
            print("CloudFormationテンプレートの検証に成功しました")
        
        else:
            print(f"不明なコマンド: {command}")
            sys.exit(1)
    
    except ConfigValidationError as e:
        print(f"検証エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()