#!/bin/bash
"""
統合デプロイスクリプト
AWS Service Catalog の自動デプロイメントを統合管理
設定ファイル解析とAWS CLI実行を連携し、詳細なログ出力を提供
"""

set -euo pipefail

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ログレベル設定
LOG_LEVEL="${LOG_LEVEL:-INFO}"  # DEBUG, INFO, WARN, ERROR

# ログ関数
log_debug() {
    [[ "$LOG_LEVEL" == "DEBUG" ]] && echo "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_info() {
    [[ "$LOG_LEVEL" =~ ^(DEBUG|INFO)$ ]] && echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_warn() {
    [[ "$LOG_LEVEL" =~ ^(DEBUG|INFO|WARN)$ ]] && echo "[WARN] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_success() {
    [[ "$LOG_LEVEL" =~ ^(DEBUG|INFO)$ ]] && echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# エラーハンドリング
handle_error() {
    local exit_code=$?
    local line_number=$1
    log_error "スクリプトがライン $line_number で失敗しました (終了コード: $exit_code)"
    
    # デバッグ情報の出力
    if [[ "$LOG_LEVEL" == "DEBUG" ]]; then
        log_debug "スタックトレース:"
        local frame=0
        while caller $frame; do
            ((frame++))
        done
    fi
    
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# 使用方法を表示
show_usage() {
    cat << EOF
使用方法: $0 <command> [options]

コマンド:
  deploy [portfolio_path]           指定されたポートフォリオまたは全体をデプロイ
  deploy-changes                    変更検知に基づいてデプロイ
  validate [portfolio_path]         設定ファイルとテンプレートを検証
  status [portfolio_name]           デプロイ状況を確認
  cleanup [portfolio_name]          指定されたポートフォリオを削除

例:
  $0 deploy                                    # 全ポートフォリオをデプロイ
  $0 deploy portfolios/development             # 特定のポートフォリオをデプロイ
  $0 deploy-changes                            # 変更されたもののみデプロイ
  $0 validate portfolios/development           # 特定のポートフォリオを検証
  $0 status "Development Portfolio"            # デプロイ状況を確認
  $0 cleanup "Development Portfolio"           # ポートフォリオを削除

環境変数:
  AWS_REGION                  AWSリージョン (デフォルト: us-east-1)
  DRY_RUN                     1に設定すると実際の操作を行わない
  LOG_LEVEL                   ログレベル (DEBUG, INFO, WARN, ERROR)
  S3_BUCKET                   大きなテンプレート用のS3バケット
  PARALLEL_JOBS               並列実行数 (デフォルト: 3)
EOF
}

# 依存関係チェック
check_dependencies() {
    log_info "依存関係をチェック中..."
    
    # 必要なコマンドの確認
    local required_commands=("aws" "python3" "jq")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "必要なコマンドがインストールされていません: $cmd"
            exit 1
        fi
    done
    
    # Python依存関係の確認
    if ! python3 -c "import yaml" 2>/dev/null; then
        log_error "PyYAMLがインストールされていません。pip install PyYAMLでインストールしてください"
        exit 1
    fi
    
    # AWS CLI認証の確認
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS認証が設定されていません。aws configure または OIDC認証を確認してください"
        exit 1
    fi
    
    # スクリプトファイルの存在確認
    local required_scripts=("config_parser.py" "detect-changes.py" "manage-portfolio.sh" "manage-product.sh")
    for script in "${required_scripts[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$script" ]]; then
            log_error "必要なスクリプトが見つかりません: $SCRIPT_DIR/$script"
            exit 1
        fi
    done
    
    log_success "依存関係チェック完了"
}

# 設定ファイルの検証
validate_configurations() {
    local portfolio_path="${1:-portfolios}"
    
    log_info "設定ファイルの検証を開始: $portfolio_path"
    
    if [[ ! -d "$portfolio_path" ]]; then
        log_error "ポートフォリオディレクトリが見つかりません: $portfolio_path"
        exit 1
    fi
    
    local validation_errors=0
    
    # ポートフォリオ設定の検証
    while IFS= read -r -d '' portfolio_yaml; do
        log_debug "ポートフォリオ設定を検証中: $portfolio_yaml"
        
        if ! python3 "$SCRIPT_DIR/config_parser.py" validate-portfolio "$portfolio_yaml" 2>/dev/null; then
            log_error "ポートフォリオ設定の検証に失敗: $portfolio_yaml"
            ((validation_errors++))
        else
            log_debug "ポートフォリオ設定の検証に成功: $portfolio_yaml"
        fi
    done < <(find "$portfolio_path" -name "portfolio.yaml" -print0)
    
    # プロダクト設定の検証
    while IFS= read -r -d '' product_yaml; do
        log_debug "プロダクト設定を検証中: $product_yaml"
        
        if ! python3 "$SCRIPT_DIR/config_parser.py" validate-product "$product_yaml" 2>/dev/null; then
            log_error "プロダクト設定の検証に失敗: $product_yaml"
            ((validation_errors++))
        else
            log_debug "プロダクト設定の検証に成功: $product_yaml"
        fi
    done < <(find "$portfolio_path" -name "product.yaml" -print0)
    
    # CloudFormationテンプレートの検証
    while IFS= read -r -d '' template_yaml; do
        log_debug "CloudFormationテンプレートを検証中: $template_yaml"
        
        if ! python3 "$SCRIPT_DIR/config_parser.py" validate-template "$template_yaml" 2>/dev/null; then
            log_error "CloudFormationテンプレートの検証に失敗: $template_yaml"
            ((validation_errors++))
        else
            log_debug "CloudFormationテンプレートの検証に成功: $template_yaml"
        fi
    done < <(find "$portfolio_path" -name "template.yaml" -print0)
    
    if [[ $validation_errors -gt 0 ]]; then
        log_error "検証エラーが $validation_errors 件見つかりました"
        exit 1
    fi
    
    log_success "すべての設定ファイルの検証に成功しました"
}

# ポートフォリオ構造の解析
analyze_portfolio_structure() {
    local portfolio_path="${1:-portfolios}"
    
    log_info "ポートフォリオ構造を解析中: $portfolio_path"
    
    # Python スクリプトを使用してポートフォリオ情報を取得
    local portfolios_json
    portfolios_json=$(python3 -c "
import sys
import json
sys.path.append('$SCRIPT_DIR')
from config_parser import ConfigParser

try:
    parser = ConfigParser()
    portfolios = parser.discover_portfolios('$portfolio_path')
    
    # JSON形式で出力
    result = []
    for portfolio in portfolios:
        portfolio_data = {
            'path': portfolio['path'],
            'name': portfolio['name'],
            'config': {
                'name': portfolio['config'].name,
                'description': portfolio['config'].description,
                'owner': portfolio['config'].owner
            },
            'products': []
        }
        
        for product in portfolio['products']:
            product_data = {
                'path': product['path'],
                'name': product['name'],
                'config': {
                    'name': product['config'].name,
                    'description': product['config'].description,
                    'owner': product['config'].owner,
                    'support_description': product['config'].support_description,
                    'support_email': product['config'].support_email,
                    'support_url': product['config'].support_url
                },
                'versions': product['versions']
            }
            portfolio_data['products'].append(product_data)
        
        result.append(portfolio_data)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f'エラー: {str(e)}', file=sys.stderr)
    sys.exit(1)
")
    
    if [[ $? -ne 0 ]]; then
        log_error "ポートフォリオ構造の解析に失敗しました"
        exit 1
    fi
    
    echo "$portfolios_json"
}

# 単一ポートフォリオのデプロイ
deploy_portfolio() {
    local portfolio_data="$1"
    
    local portfolio_name
    portfolio_name=$(echo "$portfolio_data" | jq -r '.config.name')
    local portfolio_path
    portfolio_path=$(echo "$portfolio_data" | jq -r '.path')
    
    log_info "ポートフォリオをデプロイ中: $portfolio_name"
    
    # ポートフォリオの作成/更新
    log_debug "ポートフォリオ管理スクリプトを実行中..."
    if ! "$SCRIPT_DIR/manage-portfolio.sh" create "$portfolio_path"; then
        log_error "ポートフォリオの作成/更新に失敗: $portfolio_name"
        return 1
    fi
    
    # プロダクトのデプロイ
    local products_count
    products_count=$(echo "$portfolio_data" | jq '.products | length')
    
    if [[ $products_count -gt 0 ]]; then
        log_info "プロダクトをデプロイ中: $products_count 個"
        
        # 並列実行の準備
        local max_jobs="${PARALLEL_JOBS:-3}"
        local job_count=0
        local pids=()
        
        while IFS= read -r product_data; do
            local product_name
            product_name=$(echo "$product_data" | jq -r '.config.name')
            local product_path
            product_path=$(echo "$product_data" | jq -r '.path')
            
            # 並列実行制御
            if [[ $job_count -ge $max_jobs ]]; then
                # 完了したジョブを待つ
                for i in "${!pids[@]}"; do
                    if ! kill -0 "${pids[$i]}" 2>/dev/null; then
                        wait "${pids[$i]}"
                        unset "pids[$i]"
                        ((job_count--))
                        break
                    fi
                done
            fi
            
            # プロダクトのデプロイ（バックグラウンド実行）
            (
                log_debug "プロダクトをデプロイ中: $product_name"
                
                # プロダクトの作成/更新
                if ! "$SCRIPT_DIR/manage-product.sh" create "$product_path" "$portfolio_name"; then
                    log_error "プロダクトの作成/更新に失敗: $product_name"
                    exit 1
                fi
                
                # 追加バージョンのデプロイ
                local versions
                versions=$(echo "$product_data" | jq -r '.versions[1:] | .[] | .version')
                
                for version in $versions; do
                    log_debug "プロダクトバージョンを追加中: $product_name v$version"
                    if ! "$SCRIPT_DIR/manage-product.sh" add-version "$product_path" "$version"; then
                        log_warn "プロダクトバージョンの追加に失敗: $product_name v$version"
                    fi
                done
                
                log_success "プロダクトのデプロイ完了: $product_name"
            ) &
            
            pids+=($!)
            ((job_count++))
            
        done < <(echo "$portfolio_data" | jq -c '.products[]')
        
        # 残りのジョブの完了を待つ
        for pid in "${pids[@]}"; do
            wait "$pid"
        done
    fi
    
    log_success "ポートフォリオのデプロイ完了: $portfolio_name"
}

# 全体デプロイ
deploy_all() {
    local portfolio_path="${1:-portfolios}"
    
    log_info "全体デプロイを開始: $portfolio_path"
    
    # 設定ファイルの検証
    validate_configurations "$portfolio_path"
    
    # ポートフォリオ構造の解析
    local portfolios_json
    portfolios_json=$(analyze_portfolio_structure "$portfolio_path")
    
    local portfolios_count
    portfolios_count=$(echo "$portfolios_json" | jq '. | length')
    
    if [[ $portfolios_count -eq 0 ]]; then
        log_warn "デプロイするポートフォリオが見つかりません: $portfolio_path"
        return 0
    fi
    
    log_info "デプロイ対象ポートフォリオ数: $portfolios_count"
    
    # 各ポートフォリオのデプロイ
    local deploy_errors=0
    while IFS= read -r portfolio_data; do
        if ! deploy_portfolio "$portfolio_data"; then
            ((deploy_errors++))
        fi
    done < <(echo "$portfolios_json" | jq -c '.[]')
    
    if [[ $deploy_errors -gt 0 ]]; then
        log_error "デプロイエラーが $deploy_errors 件発生しました"
        exit 1
    fi
    
    log_success "全体デプロイが正常に完了しました"
}

# 変更ベースデプロイ
deploy_changes() {
    log_info "変更検知ベースデプロイを開始"
    
    # 変更検知スクリプトの実行
    local changes_json
    changes_json=$(python3 "$SCRIPT_DIR/detect-changes.py" 2>/dev/null | tail -n 1)
    
    if [[ -z "$changes_json" ]]; then
        log_warn "変更が検知されませんでした"
        return 0
    fi
    
    log_debug "検知された変更: $changes_json"
    
    local portfolios_count
    portfolios_count=$(echo "$changes_json" | jq '.portfolios | length')
    
    if [[ $portfolios_count -eq 0 ]]; then
        log_info "デプロイが必要な変更はありません"
        return 0
    fi
    
    log_info "変更が検知されたポートフォリオ数: $portfolios_count"
    
    # 変更されたポートフォリオのデプロイ
    while IFS= read -r portfolio_change; do
        local portfolio_name
        portfolio_name=$(echo "$portfolio_change" | jq -r '.name')
        local portfolio_path="portfolios/$portfolio_name"
        
        log_info "変更されたポートフォリオをデプロイ中: $portfolio_name"
        
        # ポートフォリオ構造の解析
        local portfolio_json
        portfolio_json=$(analyze_portfolio_structure "$portfolio_path")
        
        # 該当するポートフォリオデータを抽出
        local portfolio_data
        portfolio_data=$(echo "$portfolio_json" | jq --arg name "$portfolio_name" '.[] | select(.name == $name)')
        
        if [[ -n "$portfolio_data" ]]; then
            deploy_portfolio "$portfolio_data"
        else
            log_warn "ポートフォリオデータが見つかりません: $portfolio_name"
        fi
        
    done < <(echo "$changes_json" | jq -c '.portfolios[]')
    
    log_success "変更ベースデプロイが正常に完了しました"
}

# デプロイ状況の確認
check_status() {
    local portfolio_name="${1:-}"
    
    log_info "デプロイ状況を確認中..."
    
    if [[ -n "$portfolio_name" ]]; then
        # 特定のポートフォリオの状況確認
        log_info "ポートフォリオ状況: $portfolio_name"
        "$SCRIPT_DIR/manage-portfolio.sh" check "$portfolio_name" || true
        "$SCRIPT_DIR/manage-product.sh" list "$portfolio_name" || true
    else
        # 全体の状況確認
        log_info "全ポートフォリオ状況:"
        "$SCRIPT_DIR/manage-portfolio.sh" list || true
        "$SCRIPT_DIR/manage-product.sh" list || true
    fi
}

# クリーンアップ
cleanup_portfolio() {
    local portfolio_name="$1"
    
    log_warn "ポートフォリオのクリーンアップを開始: $portfolio_name"
    
    # 確認プロンプト
    if [[ "${DRY_RUN:-0}" != "1" ]]; then
        echo "警告: ポートフォリオ '$portfolio_name' とそのすべてのプロダクトを削除します。"
        echo "この操作は元に戻せません。続行しますか？ (yes/no)"
        read -r confirmation
        if [[ "$confirmation" != "yes" ]]; then
            log_info "クリーンアップ操作がキャンセルされました"
            return 0
        fi
    fi
    
    # ポートフォリオの削除
    "$SCRIPT_DIR/manage-portfolio.sh" delete "$portfolio_name"
    
    log_success "ポートフォリオのクリーンアップが完了しました: $portfolio_name"
}

# メイン処理
main() {
    # 引数チェック
    if [[ $# -lt 1 ]]; then
        show_usage
        exit 1
    fi
    
    local command="$1"
    shift
    
    # 依存関係チェック
    check_dependencies
    
    # AWS リージョンの設定
    export AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}"
    log_info "使用するAWSリージョン: $AWS_DEFAULT_REGION"
    
    # DRY_RUN モードの表示
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        log_warn "DRY_RUN モードで実行中 - 実際の変更は行われません"
    fi
    
    # コマンドの実行
    case "$command" in
        "deploy")
            deploy_all "${1:-portfolios}"
            ;;
        "deploy-changes")
            deploy_changes
            ;;
        "validate")
            validate_configurations "${1:-portfolios}"
            ;;
        "status")
            check_status "${1:-}"
            ;;
        "cleanup")
            if [[ $# -lt 1 ]]; then
                log_error "ポートフォリオ名が必要です"
                show_usage
                exit 1
            fi
            cleanup_portfolio "$1"
            ;;
        *)
            log_error "不明なコマンド: $command"
            show_usage
            exit 1
            ;;
    esac
}

# スクリプトが直接実行された場合のみメイン処理を実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi