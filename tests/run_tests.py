#!/usr/bin/env python3
"""
テスト実行スクリプト
すべての単体テストを実行し、結果をレポートする
"""

import unittest
import sys
import os
from io import StringIO


def run_all_tests():
    """すべてのテストを実行"""
    # テストディレクトリをPythonパスに追加
    test_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, test_dir)
    
    # テストスイートを作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # テストモジュールを追加
    test_modules = [
        'test_config_parser',
        'test_detect_changes_fixed',
        'test_aws_cli_commands',
        'test_end_to_end_workflow',
        'test_sample_data_validation'
    ]
    
    for module_name in test_modules:
        try:
            module = __import__(module_name)
            suite.addTests(loader.loadTestsFromModule(module))
            print(f"✓ テストモジュール '{module_name}' を読み込みました")
        except ImportError as e:
            print(f"✗ テストモジュール '{module_name}' の読み込みに失敗: {e}")
            return False
    
    # テストを実行
    print("\n" + "="*60)
    print("AWS Service Catalog 自動化システム - 単体テスト実行")
    print("="*60)
    
    # 詳細な結果出力用のテストランナー
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True
    )
    
    result = runner.run(suite)
    
    # 結果を表示
    output = stream.getvalue()
    print(output)
    
    # サマリーを表示
    print("\n" + "="*60)
    print("テスト結果サマリー")
    print("="*60)
    print(f"実行されたテスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    # 失敗したテストの詳細
    if result.failures:
        print(f"\n失敗したテスト ({len(result.failures)}件):")
        for test, traceback in result.failures:
            print(f"  ✗ {test}")
            print(f"    {traceback.split('AssertionError:')[-1].strip()}")
    
    # エラーが発生したテストの詳細
    if result.errors:
        print(f"\nエラーが発生したテスト ({len(result.errors)}件):")
        for test, traceback in result.errors:
            print(f"  ✗ {test}")
            print(f"    {traceback.split('Exception:')[-1].strip()}")
    
    # 成功率を計算
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
        print(f"\n成功率: {success_rate:.1f}%")
    
    print("="*60)
    
    # 終了コードを返す
    return len(result.failures) == 0 and len(result.errors) == 0


def run_specific_test(test_name):
    """特定のテストを実行"""
    print(f"テスト '{test_name}' を実行中...")
    
    # テストディレクトリをPythonパスに追加
    test_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, test_dir)
    
    try:
        # テストスイートを作成
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(test_name)
        
        # テストを実行
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"テストの実行に失敗しました: {e}")
        return False


def check_dependencies():
    """テスト実行に必要な依存関係をチェック"""
    print("依存関係をチェック中...")
    
    required_modules = ['yaml', 'unittest']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"✗ {module} (未インストール)")
    
    if missing_modules:
        print(f"\n以下のモジュールをインストールしてください:")
        for module in missing_modules:
            if module == 'yaml':
                print(f"  pip install PyYAML")
            else:
                print(f"  pip install {module}")
        return False
    
    print("✓ すべての依存関係が満たされています\n")
    return True


def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        # 特定のテストを実行
        test_name = sys.argv[1]
        if not check_dependencies():
            sys.exit(1)
        
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    else:
        # すべてのテストを実行
        if not check_dependencies():
            sys.exit(1)
        
        success = run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()