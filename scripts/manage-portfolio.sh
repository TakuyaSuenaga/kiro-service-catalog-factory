#!/bin/bash
"""
ポートフォリオ管理スクリプト
AWS Service Catalog のポートフォリオ作成・更新・確認機能を提供
"""

set -euo pipefail

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ログ関数
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_success() {
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# エラーハンドリング
handle_error() {
    local exit_code=$?
    local line_number=$1
    log_error "スクリプトがライン $line_number で失敗しました (終了コード: $exit_code)"
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# 使用方法を表示
show_usage() {
    cat << EOF
使用方法: $0 <command> [options]

コマンド:
  create <portfolio_path>     新しいポートフォリオを作成
  update <portfolio_path>     既存のポートフォリオを更新
  check <portfolio_name>      ポートフォリオの存在確認
  list                        すべてのポートフォリオを一覧表示
  delete <portfolio_name>     ポートフォリオを削除（注意: 危険な操作）

例:
  $0 create portfolios/development
  $0 update portfolios/development
  $0 check "Development Portfolio"
  $0 list

環境変数:
  AWS_REGION                  AWSリージョン (デフォルト: us-east-1)
  DRY_RUN                     1に設定すると実際の操作を行わない
EOF
}

# AWS CLI の存在確認
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI がインストールされていません"
        exit 1
    fi
    
    # AWS認証の確認
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS認証が設定されていません。aws configure または OIDC認証を確認してください"
        exit 1
    fi
    
    log_info "AWS CLI 認証確認完了"
}

# ポートフォリオ設定ファイルの解析
parse_portfolio_config() {
    local portfolio_path="$1"
    local config_file="$portfolio_path/portfolio.yaml"
    
    if [[ ! -f "$config_file" ]]; then
        log_error "ポートフォリオ設定ファイルが見つかりません: $config_file"
        exit 1
    fi
    
    # Python スクリプトを使用して設定を解析
    python3 "$SCRIPT_DIR/config_parser.py" validate-portfolio "$config_file" > /dev/null
    
    # 設定値を抽出
    PORTFOLIO_NAME=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from config_parser import ConfigParser
parser = ConfigParser()
config = parser.parse_portfolio_config('$config_file')
print(config.name)
")
    
    PORTFOLIO_DESCRIPTION=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from config_parser import ConfigParser
parser = ConfigParser()
config = parser.parse_portfolio_config('$config_file')
print(config.description)
")
    
    PORTFOLIO_OWNER=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from config_parser import ConfigParser
parser = ConfigParser()
config = parser.parse_portfolio_config('$config_file')
print(config.owner)
")
    
    log_info "ポートフォリオ設定解析完了: $PORTFOLIO_NAME"
}

# ポートフォリオの存在確認
check_portfolio_exists() {
    local portfolio_name="$1"
    
    log_info "ポートフォリオの存在確認: $portfolio_name"
    
    local portfolio_id
    portfolio_id=$(aws servicecatalog list-portfolios \
        --query "PortfolioDetails[?DisplayName=='$portfolio_name'].Id" \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$portfolio_id" && "$portfolio_id" != "None" ]]; then
        echo "$portfolio_id"
        return 0
    else
        return 1
    fi
}

# ポートフォリオの作成
create_portfolio() {
    local portfolio_path="$1"
    
    log_info "ポートフォリオ作成開始: $portfolio_path"
    
    # 設定ファイルの解析
    parse_portfolio_config "$portfolio_path"
    
    # 既存ポートフォリオの確認
    if check_portfolio_exists "$PORTFOLIO_NAME" > /dev/null; then
        log_info "ポートフォリオは既に存在します: $PORTFOLIO_NAME"
        log_info "更新を実行します..."
        update_portfolio "$portfolio_path"
        return 0
    fi
    
    # DRY_RUN チェック
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        log_info "[DRY RUN] ポートフォリオを作成します:"
        log_info "[DRY RUN]   名前: $PORTFOLIO_NAME"
        log_info "[DRY RUN]   説明: $PORTFOLIO_DESCRIPTION"
        log_info "[DRY RUN]   所有者: $PORTFOLIO_OWNER"
        return 0
    fi
    
    # ポートフォリオの作成
    log_info "AWS Service Catalog ポートフォリオを作成中..."
    
    local create_result
    create_result=$(aws servicecatalog create-portfolio \
        --display-name "$PORTFOLIO_NAME" \
        --description "$PORTFOLIO_DESCRIPTION" \
        --provider-name "$PORTFOLIO_OWNER" \
        --output json)
    
    local portfolio_id
    portfolio_id=$(echo "$create_result" | jq -r '.PortfolioDetail.Id')
    
    if [[ -n "$portfolio_id" && "$portfolio_id" != "null" ]]; then
        log_success "ポートフォリオが正常に作成されました"
        log_success "  ポートフォリオID: $portfolio_id"
        log_success "  名前: $PORTFOLIO_NAME"
        echo "$portfolio_id"
    else
        log_error "ポートフォリオの作成に失敗しました"
        echo "$create_result" >&2
        exit 1
    fi
}

# ポートフォリオの更新
update_portfolio() {
    local portfolio_path="$1"
    
    log_info "ポートフォリオ更新開始: $portfolio_path"
    
    # 設定ファイルの解析
    parse_portfolio_config "$portfolio_path"
    
    # 既存ポートフォリオの確認
    local portfolio_id
    if ! portfolio_id=$(check_portfolio_exists "$PORTFOLIO_NAME"); then
        log_error "更新対象のポートフォリオが見つかりません: $PORTFOLIO_NAME"
        log_info "新規作成を実行します..."
        create_portfolio "$portfolio_path"
        return 0
    fi
    
    # DRY_RUN チェック
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        log_info "[DRY RUN] ポートフォリオを更新します:"
        log_info "[DRY RUN]   ID: $portfolio_id"
        log_info "[DRY RUN]   名前: $PORTFOLIO_NAME"
        log_info "[DRY RUN]   説明: $PORTFOLIO_DESCRIPTION"
        log_info "[DRY RUN]   所有者: $PORTFOLIO_OWNER"
        return 0
    fi
    
    # ポートフォリオの更新
    log_info "AWS Service Catalog ポートフォリオを更新中..."
    
    aws servicecatalog update-portfolio \
        --id "$portfolio_id" \
        --display-name "$PORTFOLIO_NAME" \
        --description "$PORTFOLIO_DESCRIPTION" \
        --provider-name "$PORTFOLIO_OWNER" \
        --output json > /dev/null
    
    log_success "ポートフォリオが正常に更新されました"
    log_success "  ポートフォリオID: $portfolio_id"
    log_success "  名前: $PORTFOLIO_NAME"
    echo "$portfolio_id"
}

# ポートフォリオの一覧表示
list_portfolios() {
    log_info "ポートフォリオ一覧を取得中..."
    
    local portfolios
    portfolios=$(aws servicecatalog list-portfolios --output json)
    
    echo "=== AWS Service Catalog ポートフォリオ一覧 ==="
    echo "$portfolios" | jq -r '.PortfolioDetails[] | "ID: \(.Id)\n名前: \(.DisplayName)\n説明: \(.Description)\n所有者: \(.ProviderName)\n作成日: \(.CreatedTime)\n---"'
}

# ポートフォリオの削除
delete_portfolio() {
    local portfolio_name="$1"
    
    log_info "ポートフォリオ削除開始: $portfolio_name"
    
    # 既存ポートフォリオの確認
    local portfolio_id
    if ! portfolio_id=$(check_portfolio_exists "$portfolio_name"); then
        log_error "削除対象のポートフォリオが見つかりません: $portfolio_name"
        exit 1
    fi
    
    # 確認プロンプト（DRY_RUNでない場合）
    if [[ "${DRY_RUN:-0}" != "1" ]]; then
        echo "警告: ポートフォリオ '$portfolio_name' (ID: $portfolio_id) を削除しようとしています。"
        echo "この操作は元に戻せません。続行しますか？ (yes/no)"
        read -r confirmation
        if [[ "$confirmation" != "yes" ]]; then
            log_info "削除操作がキャンセルされました"
            exit 0
        fi
    fi
    
    # DRY_RUN チェック
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        log_info "[DRY RUN] ポートフォリオを削除します:"
        log_info "[DRY RUN]   ID: $portfolio_id"
        log_info "[DRY RUN]   名前: $portfolio_name"
        return 0
    fi
    
    # ポートフォリオの削除
    log_info "AWS Service Catalog ポートフォリオを削除中..."
    
    aws servicecatalog delete-portfolio \
        --id "$portfolio_id" \
        --output json > /dev/null
    
    log_success "ポートフォリオが正常に削除されました: $portfolio_name"
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
    
    # AWS CLI の確認
    check_aws_cli
    
    # AWS リージョンの設定
    export AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}"
    log_info "使用するAWSリージョン: $AWS_DEFAULT_REGION"
    
    # コマンドの実行
    case "$command" in
        "create")
            if [[ $# -lt 1 ]]; then
                log_error "ポートフォリオパスが必要です"
                show_usage
                exit 1
            fi
            create_portfolio "$1"
            ;;
        "update")
            if [[ $# -lt 1 ]]; then
                log_error "ポートフォリオパスが必要です"
                show_usage
                exit 1
            fi
            update_portfolio "$1"
            ;;
        "check")
            if [[ $# -lt 1 ]]; then
                log_error "ポートフォリオ名が必要です"
                show_usage
                exit 1
            fi
            if portfolio_id=$(check_portfolio_exists "$1"); then
                log_success "ポートフォリオが見つかりました: $1 (ID: $portfolio_id)"
                echo "$portfolio_id"
            else
                log_info "ポートフォリオが見つかりません: $1"
                exit 1
            fi
            ;;
        "list")
            list_portfolios
            ;;
        "delete")
            if [[ $# -lt 1 ]]; then
                log_error "ポートフォリオ名が必要です"
                show_usage
                exit 1
            fi
            delete_portfolio "$1"
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