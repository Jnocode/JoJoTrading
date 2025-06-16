#!/bin/bash

# 🚀 JoJo Trading AWS 自動化部署腳本
# 此腳本自動化整個 AWS 部署流程

set -e

# 配置變數
AWS_REGION="ap-northeast-1"
ENVIRONMENT="production"
STACK_NAME="jojo-trading-${ENVIRONMENT}"
ECR_REPOSITORY="jojo-trading"
IMAGE_TAG="latest"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 檢查必要工具
check_prerequisites() {
    echo_info "檢查部署必要工具..."
    
    if ! command -v aws &> /dev/null; then
        echo_error "AWS CLI 未安裝，請先安裝 AWS CLI"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo_error "Docker 未安裝，請先安裝 Docker"
        exit 1
    fi
    
    # 檢查 AWS 認證
    if ! aws sts get-caller-identity &> /dev/null; then
        echo_error "AWS 認證失敗，請執行 'aws configure'"
        exit 1
    fi
    
    echo_success "所有必要工具已就緒"
}

# 獲取 AWS 帳戶 ID
get_account_id() {
    echo_info "獲取 AWS 帳戶 ID..."
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo_success "AWS 帳戶 ID: $ACCOUNT_ID"
}

# 創建 ECR 倉庫
create_ecr_repository() {
    echo_info "創建 ECR 倉庫..."
    
    # 檢查倉庫是否存在
    if aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION &> /dev/null; then
        echo_warning "ECR 倉庫 $ECR_REPOSITORY 已存在"
    else
        aws ecr create-repository \
            --repository-name $ECR_REPOSITORY \
            --region $AWS_REGION \
            --image-scanning-configuration scanOnPush=true
        echo_success "ECR 倉庫創建成功"
    fi
}

# 構建並推送 Docker 映像
build_and_push_image() {
    echo_info "構建 Docker 映像..."
    
    # 獲取 ECR 登入權杖
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    
    # 構建映像
    cd ../../
    docker build -t $ECR_REPOSITORY:$IMAGE_TAG -f Dockerfile .
    
    # 標記映像
    docker tag $ECR_REPOSITORY:$IMAGE_TAG $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
    
    # 推送映像
    docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
    
    echo_success "Docker 映像推送成功"
}

# 部署 CloudFormation 堆疊
deploy_infrastructure() {
    echo_info "部署基礎設施..."
    
    # 更新 CloudFormation 模板中的映像 URI
    sed -i "s|jojo-trading:latest|$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG|g" cloudformation-infrastructure.yml
    
    aws cloudformation deploy \
        --template-file cloudformation-infrastructure.yml \
        --stack-name $STACK_NAME \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides \
            Environment=$ENVIRONMENT \
        --region $AWS_REGION \
        --no-fail-on-empty-changeset
    
    echo_success "基礎設施部署成功"
}

# 獲取部署結果
get_deployment_info() {
    echo_info "獲取部署資訊..."
    
    # 獲取 Load Balancer URL
    LB_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
        --output text)
    
    echo_success "=== 部署完成 ==="
    echo_info "應用程式 URL: $LB_URL"
    echo_info "監控面板: https://$AWS_REGION.console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters"
    echo_info "日誌查看: https://$AWS_REGION.console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups"
}

# 健康檢查
health_check() {
    echo_info "執行健康檢查..."
    
    # 等待服務啟動
    echo_info "等待服務啟動（這可能需要幾分鐘）..."
    sleep 120
    
    # 檢查服務狀態
    SERVICE_STATUS=$(aws ecs describe-services \
        --cluster "${ENVIRONMENT}-jojo-trading-cluster" \
        --services "${ENVIRONMENT}-jojo-trading-service" \
        --region $AWS_REGION \
        --query 'services[0].status' \
        --output text)
    
    if [ "$SERVICE_STATUS" = "ACTIVE" ]; then
        echo_success "ECS 服務運行正常"
        
        # 測試應用程式端點
        if curl -f -s "$LB_URL/_stcore/health" > /dev/null; then
            echo_success "應用程式健康檢查通過"
        else
            echo_warning "應用程式可能還在啟動中，請稍候再試"
        fi
    else
        echo_warning "ECS 服務狀態: $SERVICE_STATUS"
    fi
}

# 清理函數
cleanup() {
    echo_info "如需清理資源，請執行："
    echo "aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION"
}

# 主執行流程
main() {
    echo_info "🚀 開始 JoJo Trading AWS 部署流程"
    echo_info "環境: $ENVIRONMENT"
    echo_info "區域: $AWS_REGION"
    
    check_prerequisites
    get_account_id
    create_ecr_repository
    build_and_push_image
    deploy_infrastructure
    get_deployment_info
    health_check
    
    echo_success "🎉 部署完成！JoJo Trading 現在運行在 AWS 上"
    echo_info "請訪問: $LB_URL"
    
    echo_info "部署詳細資訊已保存，如需清理資源請執行 cleanup 函數"
}

# 如果腳本被直接執行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
