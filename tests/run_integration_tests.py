#!/usr/bin/env python3
"""
統合テスト実行スクリプト
エンドツーエンドテストとサンプルデータ検証を統合実行
"""

import unittest
import sys
import os
from io import StringIO

# テストモジュールのインポート
from test_end_to_end_workflow import TestEndToEndWorkflow, TestWorkflowIntegration
from test_sample_data_validation import TestSampleDataValidation


def run_integration_tests():
    """統合テストの実行"""
    print("="*80)
    print("AWS Service Catalog 自動化システム - 統合テスト実行")
    print("="*80)
    
    # テストスイートの作成
    suite = unittest.TestSuite()
    
    # エンドツーエンドテストの追加
    print("\n統合テストスイートを構築中...")
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestSampleDataValidation))
    
    print("✓ テストスイート構築完了")
    
    # 詳細な結果出力用のテストランナー
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True
    )
    
    print("\n統合テストを実行中...")
    result = runner.run(suite)
    
    # 結果を表示
    output = stream.getvalue()
    print(output)
    
    # 詳細サマリーを表示
    print("\n" + "="*80)
    print("統合テスト結果サマリー")
    print("="*80)
    
    # テストカテゴリ別の結果
    categories = {
        'エンドツーエンドワークフロー': 'TestEndToEndWorkflow',
        'ワークフロー統合': 'TestWorkflowIntegration',
        'サンプルデータ検証': 'TestSampleDataValidation'
    }
    
    for category_name, class_name in categories.items():
        category_tests = [test for test in result.testsRun if class_name in str(test)]
        if category_tests:
            print(f"\n{category_name}:")
            print(f"  実行されたテスト数: {len(category_tests)}")
    
    # 全体結果
    print(f"\n全体結果:")
    print(f"  実行されたテスト数: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失敗: {len(result.failures)}")
    print(f"  エラー: {len(result.errors)}")
    
    # 失敗したテストの詳細
    if result.failures:
        print(f"\n失敗したテスト ({len(result.failures)}件):")
        for test, traceback in result.failures:
            print(f"  ✗ {test}")
            # エラーメッセージの抽出
            error_lines = traceback.split('\n')
            for line in error_lines:
                if 'AssertionError:' in line:
                    print(f"    理由: {line.split('AssertionError:')[-1].strip()}")
                    break
    
    # エラーが発生したテストの詳細
    if result.errors:
        print(f"\nエラーが発生したテスト ({len(result.errors)}件):")
        for test, traceback in result.errors:
            print(f"  ✗ {test}")
            # エラーメッセージの抽出
            error_lines = traceback.split('\n')
            for line in error_lines:
                if any(error_type in line for error_type in ['Exception:', 'Error:', 'ImportError:']):
                    print(f"    エラー: {line.strip()}")
                    break
    
    # 成功率を計算
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
        print(f"\n成功率: {success_rate:.1f}%")
        
        # 成功率に基づく評価
        if success_rate == 100:
            print("🎉 すべてのテストが成功しました！")
        elif success_rate >= 90:
            print("✅ 優秀な結果です。")
        elif success_rate >= 80:
            print("⚠️  良好な結果ですが、いくつかの問題があります。")
        elif success_rate >= 70:
            print("⚠️  改善が必要です。")
        else:
            print("❌ 重大な問題があります。修正が必要です。")
    
    # 推奨事項
    print(f"\n推奨事項:")
    if result.failures or result.errors:
        print("  - 失敗したテストのエラーメッセージを確認してください")
        print("  - 必要に応じて設定ファイルやスクリプトを修正してください")
        print("  - 個別のテストを実行して詳細を確認してください")
    else:
        print("  - すべてのテストが成功しています")
        print("  - システムは本番環境での使用準備が整っています")
    
    print("="*80)
    
    # 終了コードを返す
    return len(result.failures) == 0 and len(result.errors) == 0


def run_specific_category(category):
    """特定のカテゴリのテストを実行"""
    print(f"カテゴリ '{category}' のテストを実行中...")
    
    suite = unittest.TestSuite()
    
    if category.lower() == 'workflow':
        loader = unittest.TestLoader()
        suite.addTests(loader.loadTestsFromTestCase(TestEndToEndWorkflow))
        suite.addTests(loader.loadTestsFromTestCase(TestWorkflowIntegration))
    elif category.lower() == 'sample':
        loader = unittest.TestLoader()
        suite.addTests(loader.loadTestsFromTestCase(TestSampleDataValidation))
    elif category.lower() == 'all':
        return run_integration_tests()
    else:
        print(f"不明なカテゴリ: {category}")
        print("利用可能なカテゴリ: workflow, sample, all")
        return False
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def check_test_environment():
    """テスト環境の確認"""
    print("テスト環境を確認中...")
    
    # 必要なディレクトリの確認
    required_dirs = [
        'scripts',
        'portfolios',
        '.github/workflows',
        'tests'
    ]
    
    project_root = os.path.join(os.path.dirname(__file__), '..')
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = os.path.join(project_root, dir_name)
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_name)
        else:
            print(f"✓ {dir_name}")
    
    if missing_dirs:
        print(f"\n不足しているディレクトリ:")
        for dir_name in missing_dirs:
            print(f"  ✗ {dir_name}")
        return False
    
    # 必要なファイルの確認
    required_files = [
        'scripts/config_parser.py',
        'scripts/detect-changes.py',
        'scripts/deploy-catalog.sh',
        '.github/workflows/service-catalog.yml'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        file_path = os.path.join(project_root, file_name)
        if not os.path.exists(file_path):
            missing_files.append(file_name)
        else:
            print(f"✓ {file_name}")
    
    if missing_files:
        print(f"\n不足しているファイル:")
        for file_name in missing_files:
            print(f"  ✗ {file_name}")
        return False
    
    print("✓ テスト環境の確認完了")
    return True


def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        # 特定のカテゴリを実行
        category = sys.argv[1]
        
        if not check_test_environment():
            print("テスト環境に問題があります。")
            sys.exit(1)
        
        success = run_specific_category(category)
        sys.exit(0 if success else 1)
    else:
        # 全統合テストを実行
        if not check_test_environment():
            print("テスト環境に問題があります。")
            sys.exit(1)
        
        success = run_integration_tests()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()