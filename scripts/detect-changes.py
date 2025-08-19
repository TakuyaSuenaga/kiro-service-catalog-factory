#!/usr/bin/env python3
"""
変更検知スクリプト
portfoliosフォルダの変更を検知し、影響を受けるポートフォリオとプロダクトを特定する
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple


def get_changed_files() -> List[str]:
    """
    Gitで変更されたファイルのリストを取得
    """
    try:
        # GitHub Actionsの場合、前のコミットとの差分を取得
        if os.getenv('GITHUB_ACTIONS'):
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
        else:
            # ローカル実行の場合、ステージングエリアとの差分を取得
            result = subprocess.run(
                ['git', 'diff', '--name-only', '--cached'],
                capture_output=True,
                text=True,
                check=True
            )
        
        changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
        return changed_files
    
    except subprocess.CalledProcessError as e:
        print(f"Git コマンドエラー: {e}")
        return []


def parse_portfolio_path(file_path: str) -> Tuple[str, str, str]:
    """
    ファイルパスからポートフォリオ、プロダクト、バージョン情報を抽出
    
    Args:
        file_path: portfolios/portfolio-name/product-name/version/template.yaml 形式のパス
        
    Returns:
        (portfolio_name, product_name, version) のタプル
    """
    path_parts = Path(file_path).parts
    
    if len(path_parts) < 2 or path_parts[0] != 'portfolios':
        return ('', '', '')
    
    portfolio_name = path_parts[1] if len(path_parts) > 1 else ''
    product_name = path_parts[2] if len(path_parts) > 2 else ''
    version = path_parts[3] if len(path_parts) > 3 else ''
    
    return (portfolio_name, product_name, version)


def detect_changes() -> Dict[str, List[Dict[str, str]]]:
    """
    変更されたファイルを解析し、影響を受けるポートフォリオとプロダクトを特定
    
    Returns:
        {
            'portfolios': [
                {
                    'name': 'portfolio-name',
                    'products': [
                        {
                            'name': 'product-name',
                            'versions': ['v1.0.0', 'v1.1.0'],
                            'config_changed': True/False
                        }
                    ],
                    'config_changed': True/False
                }
            ]
        }
    """
    changed_files = get_changed_files()
    
    # portfoliosフォルダ内の変更のみをフィルタリング
    portfolio_changes = [f for f in changed_files if f.startswith('portfolios/')]
    
    if not portfolio_changes:
        print("portfoliosフォルダに変更はありません")
        return {'portfolios': []}
    
    print(f"検出された変更ファイル: {portfolio_changes}")
    
    # ポートフォリオごとに変更を整理
    portfolio_data: Dict[str, Dict] = {}
    
    for file_path in portfolio_changes:
        portfolio_name, product_name, version = parse_portfolio_path(file_path)
        
        if not portfolio_name:
            continue
            
        # ポートフォリオ初期化
        if portfolio_name not in portfolio_data:
            portfolio_data[portfolio_name] = {
                'name': portfolio_name,
                'products': {},
                'config_changed': False
            }
        
        # ポートフォリオ設定ファイルの変更チェック
        if file_path.endswith('portfolio.yaml'):
            portfolio_data[portfolio_name]['config_changed'] = True
            continue
        
        # プロダクト関連の変更
        if product_name:
            if product_name not in portfolio_data[portfolio_name]['products']:
                portfolio_data[portfolio_name]['products'][product_name] = {
                    'name': product_name,
                    'versions': set(),
                    'config_changed': False
                }
            
            # プロダクト設定ファイルの変更チェック
            if file_path.endswith('product.yaml'):
                portfolio_data[portfolio_name]['products'][product_name]['config_changed'] = True
            
            # バージョン情報の追加
            if version:
                portfolio_data[portfolio_name]['products'][product_name]['versions'].add(version)
    
    # 結果を整形
    result = {'portfolios': []}
    
    for portfolio_name, portfolio_info in portfolio_data.items():
        portfolio_result = {
            'name': portfolio_name,
            'products': [],
            'config_changed': portfolio_info['config_changed']
        }
        
        for product_name, product_info in portfolio_info['products'].items():
            product_result = {
                'name': product_name,
                'versions': sorted(list(product_info['versions'])),
                'config_changed': product_info['config_changed']
            }
            portfolio_result['products'].append(product_result)
        
        result['portfolios'].append(portfolio_result)
    
    return result


def main():
    """
    メイン実行関数
    """
    print("=== AWS Service Catalog 変更検知 ===")
    
    changes = detect_changes()
    
    # 結果をJSON形式で出力（GitHub Actionsで使用）
    print("\n=== 検知結果 ===")
    print(json.dumps(changes, indent=2, ensure_ascii=False))
    
    # GitHub Actions用の出力設定
    if os.getenv('GITHUB_ACTIONS'):
        # 変更があった場合のフラグ
        has_changes = len(changes['portfolios']) > 0
        
        # GitHub Actionsの出力変数に設定
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"has-changes={str(has_changes).lower()}\n")
            f.write(f"changes={json.dumps(changes)}\n")
        
        print(f"\nGitHub Actions出力: has-changes={str(has_changes).lower()}")
    
    # 変更がある場合は終了コード0、ない場合も0（エラーではないため）
    return 0


if __name__ == '__main__':
    sys.exit(main())