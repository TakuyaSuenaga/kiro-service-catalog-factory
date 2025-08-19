#!/bin/bash
"""
プロダクト管理スクリプト
AWS Service Catalog のプロダクト作成・更新・バージョン管理機能を提供
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
  create <product_path> <portfolio_name>    新しいプロダクトを作成
  update <product_path> <portfolio_name>    既存のプロダクトを更新
  add-version <product_path> <version>      プロダクトに新しいバージョンを追加
  check <product_name>                      プロダクトの存在確認
  list [portfolio_name]                     プロダクトを一覧表示
  validate-template <template_path>         CloudFormationテンプレートを検証

例:
  $0 create portfolios/development/ec2-instances "Development Portfolio"
  $0 update portfolios/development/ec2-instances "Development Portfolio"
  $0 add-version portfolios/development/ec2-instances v1.1.0
  $0 check "EC2 Instances"
  $0 list "Development Portfolio"
  $0 validate-template portfolios/development/ec2-instances/v1.0.0/template.yaml

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

# プロダクト設定ファイルの解析
parse_product_config() {
    local product_path="$1"
    local config_file="$product_path/product.yaml"
    
    if [[ ! -f "$config_file" ]]; then
        log_error "プロダクト設定ファイルが見つかりません: $config_file"
        exit 1
    fi
    
    # Python スクリプトを使用して設定を解析
    python3 "$SCRIPT_DIR/config_parser.py" validate-product "$config_file" > /dev/null
    
    # 設定値を抽出
    PRODUCT_NAME=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from config_parser import ConfigParser
parser = ConfigParser()
config = parser.parse_product_config('$config_file')
print(config.name)
")
    
    PRODUCT_DESCRIPTION=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from config_parser import ConfigParser
parser = ConfigParser()
config = parser.parse_product_config('$config_file')
print(config.description)
")
    
    PRODUCT_OWNER=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from config_parser import ConfigParser
parser = ConfigParser()
config = parser.parse_product_config('$config_file')
print(config.owner)
")
    
    PRODUCT_SUPPORT_DESCRIPTION=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from config_parser import ConfigParser
parser = ConfigParser()
config = parser.parse_product_config('$config_file')
print(config.support_description)
")
    
    PRODUCT_SUPPORT_EMAIL=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from config_parser import ConfigParser
parser = ConfigParser()
config = parser.parse_product_config('$config_file')
print(config.support_email)
")
    
    PRODUCT_SUPPORT_URL=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from config_parser import ConfigParser
parser = ConfigParser()
config = parser.parse_product_config('$config_file')
print(config.support_url)
")
    
    log_info "プロダクト設定解析完了: $PRODUCT_NAME"
}

# ポートフォリオIDの取得
get_portfolio_id() {
    local portfolio_name="$1"
    
    local portfolio_id
    portfolio_id=$(aws servicecatalog list-portfolios \
        --query "PortfolioDetails[?DisplayName=='$portfolio_name'].Id" \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$portfolio_id" && "$portfolio_id" != "None" ]]; then
        echo "$portfolio_id"
        return 0
    else
        log_error "ポートフォリオが見つかりません: $portfolio_name"
        exit 1
    fi
}

# プロダクトの存在確認
check_product_exists() {
    local product_name="$1"
    
    log_info "プロダクトの存在確認: $product_name"
    
    local product_id
    product_id=$(aws servicecatalog search-products-as-admin \
        --query "ProductViewDetails[?ProductViewSummary.Name=='$product_name'].ProductViewSummary.ProductId" \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$product_id" && "$product_id" != "None" ]]; then
        echo "$product_id"
        return 0
    else
        return 1
    fi
}

# CloudFormationテンプレートの検証
validate_cloudformation_template() {
    local template_path="$1"
    
    log_info "CloudFormationテンプレートを検証中: $template_path"
    
    if [[ ! -f "$template_path" ]]; then
        log_error "テンプレートファイルが見つかりません: $template_path"
        exit 1
    fi
    
    # Python スクリプトでの基本検証
    python3 "$SCRIPT_DIR/config_parser.py" validate-template "$template_path"
    
    # AWS CLI での検証
    if [[ "${DRY_RUN:-0}" != "1" ]]; then
        aws cloudformation validate-template \
            --template-body "file://$template_path" \
            --output json > /dev/null
        log_success "CloudFormationテンプレートの検証に成功しました"
    else
        log_info "[DRY RUN] CloudFormationテンプレートの検証をスキップしました"
    fi
}

# S3にテンプレートをアップロード（大きなテンプレート用）
upload_template_to_s3() {
    local template_path="$1"
    local s3_bucket="${S3_BUCKET:-}"
    
    if [[ -z "$s3_bucket" ]]; then
        # S3バケットが指定されていない場合はローカルファイルを使用
        echo "file://$template_path"
        return 0
    fi
    
    local template_name
    template_name="$(basename "$(dirname "$template_path")")/$(basename "$template_path")"
    local s3_key="service-catalog-templates/$template_name"
    
    log_info "テンプレートをS3にアップロード中: s3://$s3_bucket/$s3_key"
    
    if [[ "${DRY_RUN:-0}" != "1" ]]; then
        aws s3 cp "$template_path" "s3://$s3_bucket/$s3_key"
        echo "https://$s3_bucket.s3.amazonaws.com/$s3_key"
    else
        log_info "[DRY RUN] S3アップロードをスキップしました"
        echo "file://$template_path"
    fi
}

# プロダクトの作成
create_product() {
    local product_path="$1"
    local portfolio_name="$2"
    
    log_info "プロダクト作成開始: $product_path"
    
    # 設定ファイルの解析
    parse_product_config "$product_path"
    
    # ポートフォリオIDの取得
    local portfolio_id
    portfolio_id=$(get_portfolio_id "$portfolio_name")
    
    # 既存プロダクトの確認
    if check_product_exists "$PRODUCT_NAME" > /dev/null; then
        log_info "プロダクトは既に存在します: $PRODUCT_NAME"
        log_info "更新を実行します..."
        update_product "$product_path" "$portfolio_name"
        return 0
    fi
    
    # 最初のバージョンのテンプレートを探す
    local first_version_dir
    first_version_dir=$(find "$product_path" -maxdepth 1 -type d -name "v*" | sort | head -n 1)
    
    if [[ -z "$first_version_dir" ]]; then
        log_error "バージョンディレクトリが見つかりません: $product_path"
        exit 1
    fi
    
    local template_path="$first_version_dir/template.yaml"
    if [[ ! -f "$template_path" ]]; then
        log_error "テンプレートファイルが見つかりません: $template_path"
        exit 1
    fi
    
    # テンプレートの検証
    validate_cloudformation_template "$template_path"
    
    # テンプレートのURL取得
    local template_url
    template_url=$(upload_template_to_s3 "$template_path")
    
    # DRY_RUN チェック
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        log_info "[DRY RUN] プロダクトを作成します:"
        log_info "[DRY RUN]   名前: $PRODUCT_NAME"
        log_info "[DRY RUN]   説明: $PRODUCT_DESCRIPTION"
        log_info "[DRY RUN]   所有者: $PRODUCT_OWNER"
        log_info "[DRY RUN]   ポートフォリオID: $portfolio_id"
        log_info "[DRY RUN]   テンプレートURL: $template_url"
        return 0
    fi
    
    # プロダクトの作成
    log_info "AWS Service Catalog プロダクトを作成中..."
    
    local create_result
    if [[ "$template_url" == file://* ]]; then
        # ローカルファイルの場合
        create_result=$(aws servicecatalog create-product \
            --name "$PRODUCT_NAME" \
            --description "$PRODUCT_DESCRIPTION" \
            --owner "$PRODUCT_OWNER" \
            --support-description "$PRODUCT_SUPPORT_DESCRIPTION" \
            --support-email "$PRODUCT_SUPPORT_EMAIL" \
            --support-url "$PRODUCT_SUPPORT_URL" \
            --provisioning-artifact-parameters "Name=$(basename "$first_version_dir"),Description=Initial version,Info={LoadTemplateFromURL=$template_url}" \
            --output json)
    else
        # S3 URLの場合
        create_result=$(aws servicecatalog create-product \
            --name "$PRODUCT_NAME" \
            --description "$PRODUCT_DESCRIPTION" \
            --owner "$PRODUCT_OWNER" \
            --support-description "$PRODUCT_SUPPORT_DESCRIPTION" \
            --support-email "$PRODUCT_SUPPORT_EMAIL" \
            --support-url "$PRODUCT_SUPPORT_URL" \
            --provisioning-artifact-parameters "Name=$(basename "$first_version_dir"),Description=Initial version,Info={LoadTemplateFromURL=$template_url}" \
            --output json)
    fi
    
    local product_id
    product_id=$(echo "$create_result" | jq -r '.ProductViewDetail.ProductViewSummary.ProductId')
    
    if [[ -n "$product_id" && "$product_id" != "null" ]]; then
        log_success "プロダクトが正常に作成されました"
        log_success "  プロダクトID: $product_id"
        log_success "  名前: $PRODUCT_NAME"
        
        # ポートフォリオにプロダクトを関連付け
        log_info "プロダクトをポートフォリオに関連付け中..."
        aws servicecatalog associate-product-with-portfolio \
            --product-id "$product_id" \
            --portfolio-id "$portfolio_id" \
            --output json > /dev/null
        
        log_success "プロダクトがポートフォリオに正常に関連付けられました"
        echo "$product_id"
    else
        log_error "プロダクトの作成に失敗しました"
        echo "$create_result" >&2
        exit 1
    fi
}

# プロダクトの更新
update_product() {
    local product_path="$1"
    local portfolio_name="$2"
    
    log_info "プロダクト更新開始: $product_path"
    
    # 設定ファイルの解析
    parse_product_config "$product_path"
    
    # 既存プロダクトの確認
    local product_id
    if ! product_id=$(check_product_exists "$PRODUCT_NAME"); then
        log_error "更新対象のプロダクトが見つかりません: $PRODUCT_NAME"
        log_info "新規作成を実行します..."
        create_product "$product_path" "$portfolio_name"
        return 0
    fi
    
    # DRY_RUN チェック
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        log_info "[DRY RUN] プロダクトを更新します:"
        log_info "[DRY RUN]   ID: $product_id"
        log_info "[DRY RUN]   名前: $PRODUCT_NAME"
        log_info "[DRY RUN]   説明: $PRODUCT_DESCRIPTION"
        return 0
    fi
    
    # プロダクトの更新
    log_info "AWS Service Catalog プロダクトを更新中..."
    
    aws servicecatalog update-product \
        --id "$product_id" \
        --name "$PRODUCT_NAME" \
        --description "$PRODUCT_DESCRIPTION" \
        --owner "$PRODUCT_OWNER" \
        --support-description "$PRODUCT_SUPPORT_DESCRIPTION" \
        --support-email "$PRODUCT_SUPPORT_EMAIL" \
        --support-url "$PRODUCT_SUPPORT_URL" \
        --output json > /dev/null
    
    log_success "プロダクトが正常に更新されました"
    log_success "  プロダクトID: $product_id"
    log_success "  名前: $PRODUCT_NAME"
    echo "$product_id"
}

# プロダクトバージョンの追加
add_product_version() {
    local product_path="$1"
    local version="$2"
    
    log_info "プロダクトバージョン追加開始: $product_path/$version"
    
    # 設定ファイルの解析
    parse_product_config "$product_path"
    
    # 既存プロダクトの確認
    local product_id
    if ! product_id=$(check_product_exists "$PRODUCT_NAME"); then
        log_error "プロダクトが見つかりません: $PRODUCT_NAME"
        exit 1
    fi
    
    # バージョンディレクトリとテンプレートの確認
    local version_dir="$product_path/$version"
    local template_path="$version_dir/template.yaml"
    
    if [[ ! -d "$version_dir" ]]; then
        log_error "バージョンディレクトリが見つかりません: $version_dir"
        exit 1
    fi
    
    if [[ ! -f "$template_path" ]]; then
        log_error "テンプレートファイルが見つかりません: $template_path"
        exit 1
    fi
    
    # テンプレートの検証
    validate_cloudformation_template "$template_path"
    
    # テンプレートのURL取得
    local template_url
    template_url=$(upload_template_to_s3 "$template_path")
    
    # DRY_RUN チェック
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        log_info "[DRY RUN] プロダクトバージョンを追加します:"
        log_info "[DRY RUN]   プロダクトID: $product_id"
        log_info "[DRY RUN]   バージョン: $version"
        log_info "[DRY RUN]   テンプレートURL: $template_url"
        return 0
    fi
    
    # プロダクトバージョンの追加
    log_info "AWS Service Catalog プロダクトバージョンを追加中..."
    
    local create_result
    if [[ "$template_url" == file://* ]]; then
        # ローカルファイルの場合
        create_result=$(aws servicecatalog create-provisioning-artifact \
            --product-id "$product_id" \
            --parameters "Name=$version,Description=Version $version,Info={LoadTemplateFromURL=$template_url}" \
            --output json)
    else
        # S3 URLの場合
        create_result=$(aws servicecatalog create-provisioning-artifact \
            --product-id "$product_id" \
            --parameters "Name=$version,Description=Version $version,Info={LoadTemplateFromURL=$template_url}" \
            --output json)
    fi
    
    local artifact_id
    artifact_id=$(echo "$create_result" | jq -r '.ProvisioningArtifactDetail.Id')
    
    if [[ -n "$artifact_id" && "$artifact_id" != "null" ]]; then
        log_success "プロダクトバージョンが正常に追加されました"
        log_success "  プロダクトID: $product_id"
        log_success "  バージョン: $version"
        log_success "  アーティファクトID: $artifact_id"
        echo "$artifact_id"
    else
        log_error "プロダクトバージョンの追加に失敗しました"
        echo "$create_result" >&2
        exit 1
    fi
}

# プロダクトの一覧表示
list_products() {
    local portfolio_name="${1:-}"
    
    if [[ -n "$portfolio_name" ]]; then
        log_info "ポートフォリオ内のプロダクト一覧を取得中: $portfolio_name"
        
        local portfolio_id
        portfolio_id=$(get_portfolio_id "$portfolio_name")
        
        local products
        products=$(aws servicecatalog search-products-as-admin \
            --portfolio-id "$portfolio_id" \
            --output json)
        
        echo "=== ポートフォリオ '$portfolio_name' のプロダクト一覧 ==="
        echo "$products" | jq -r '.ProductViewDetails[] | "ID: \(.ProductViewSummary.ProductId)\n名前: \(.ProductViewSummary.Name)\n説明: \(.ProductViewSummary.ShortDescription)\n所有者: \(.ProductViewSummary.Owner)\n作成日: \(.CreatedTime)\n---"'
    else
        log_info "全プロダクト一覧を取得中..."
        
        local products
        products=$(aws servicecatalog search-products-as-admin --output json)
        
        echo "=== AWS Service Catalog プロダクト一覧 ==="
        echo "$products" | jq -r '.ProductViewDetails[] | "ID: \(.ProductViewSummary.ProductId)\n名前: \(.ProductViewSummary.Name)\n説明: \(.ProductViewSummary.ShortDescription)\n所有者: \(.ProductViewSummary.Owner)\n作成日: \(.CreatedTime)\n---"'
    fi
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
            if [[ $# -lt 2 ]]; then
                log_error "プロダクトパスとポートフォリオ名が必要です"
                show_usage
                exit 1
            fi
            create_product "$1" "$2"
            ;;
        "update")
            if [[ $# -lt 2 ]]; then
                log_error "プロダクトパスとポートフォリオ名が必要です"
                show_usage
                exit 1
            fi
            update_product "$1" "$2"
            ;;
        "add-version")
            if [[ $# -lt 2 ]]; then
                log_error "プロダクトパスとバージョンが必要です"
                show_usage
                exit 1
            fi
            add_product_version "$1" "$2"
            ;;
        "check")
            if [[ $# -lt 1 ]]; then
                log_error "プロダクト名が必要です"
                show_usage
                exit 1
            fi
            if product_id=$(check_product_exists "$1"); then
                log_success "プロダクトが見つかりました: $1 (ID: $product_id)"
                echo "$product_id"
            else
                log_info "プロダクトが見つかりません: $1"
                exit 1
            fi
            ;;
        "list")
            list_products "${1:-}"
            ;;
        "validate-template")
            if [[ $# -lt 1 ]]; then
                log_error "テンプレートパスが必要です"
                show_usage
                exit 1
            fi
            validate_cloudformation_template "$1"
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