#!/bin/bash

# 🚀 JoJo Trading Azure 自動化部署腳本
# 此腳本自動化整個 Azure 部署流程

set -e

# 配置變數
AZURE_REGION="eastasia"
ENVIRONMENT="production"
RESOURCE_GROUP_NAME="rg-jojo-trading-${ENVIRONMENT}"
CONTAINER_REGISTRY_NAME="crjojotrading${ENVIRONMENT}"
IMAGE_NAME="jojo-trading"
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
    
    if ! command -v az &> /dev/null; then
        echo_error "Azure CLI 未安裝，請先安裝 Azure CLI"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo_error "Docker 未安裝，請先安裝 Docker"
        exit 1
    fi
    
    # 檢查 Azure 認證
    if ! az account show &> /dev/null; then
        echo_error "Azure 認證失敗，請執行 'az login'"
        exit 1
    fi
    
    echo_success "所有必要工具已就緒"
}

# 創建資源群組
create_resource_group() {
    echo_info "創建資源群組..."
    
    if az group show --name $RESOURCE_GROUP_NAME &> /dev/null; then
        echo_warning "資源群組 $RESOURCE_GROUP_NAME 已存在"
    else
        az group create \
            --name $RESOURCE_GROUP_NAME \
            --location $AZURE_REGION \
            --tags Environment=$ENVIRONMENT Project=JoJoTrading
        echo_success "資源群組創建成功"
    fi
}

# 創建 Azure Container Registry
create_container_registry() {
    echo_info "創建 Azure Container Registry..."
    
    if az acr show --name $CONTAINER_REGISTRY_NAME --resource-group $RESOURCE_GROUP_NAME &> /dev/null; then
        echo_warning "Container Registry $CONTAINER_REGISTRY_NAME 已存在"
    else
        az acr create \
            --resource-group $RESOURCE_GROUP_NAME \
            --name $CONTAINER_REGISTRY_NAME \
            --sku Basic \
            --admin-enabled true
        echo_success "Container Registry 創建成功"
    fi
}

# 構建並推送 Docker 映像
build_and_push_image() {
    echo_info "構建並推送 Docker 映像..."
    
    # 獲取 ACR 登入伺服器
    ACR_LOGIN_SERVER=$(az acr show --name $CONTAINER_REGISTRY_NAME --resource-group $RESOURCE_GROUP_NAME --query loginServer --output tsv)
    
    # 登入 ACR
    az acr login --name $CONTAINER_REGISTRY_NAME
    
    # 構建映像
    cd ../../
    docker build -t $IMAGE_NAME:$IMAGE_TAG -f Dockerfile .
    
    # 標記映像
    docker tag $IMAGE_NAME:$IMAGE_TAG $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG
    
    # 推送映像
    docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG
    
    echo_success "Docker 映像推送成功"
}

# 取得 Container Registry 認證
get_acr_credentials() {
    echo_info "獲取 Container Registry 認證..."
    
    ACR_LOGIN_SERVER=$(az acr show --name $CONTAINER_REGISTRY_NAME --resource-group $RESOURCE_GROUP_NAME --query loginServer --output tsv)
    ACR_USERNAME=$(az acr credential show --name $CONTAINER_REGISTRY_NAME --resource-group $RESOURCE_GROUP_NAME --query username --output tsv)
    ACR_PASSWORD=$(az acr credential show --name $CONTAINER_REGISTRY_NAME --resource-group $RESOURCE_GROUP_NAME --query passwords[0].value --output tsv)
    
    echo_success "Container Registry 認證獲取成功"
}

# 部署 ARM 模板
deploy_infrastructure() {
    echo_info "部署 Azure 基礎設施..."
    
    # 提示輸入 FinMind Token
    if [ -z "$FINMIND_TOKEN" ]; then
        echo_info "請輸入 FinMind API Token（留空將使用預設值）:"
        read -s FINMIND_TOKEN
        if [ -z "$FINMIND_TOKEN" ]; then
            FINMIND_TOKEN="your-finmind-token-here"
        fi
    fi
    
    az deployment group create \
        --resource-group $RESOURCE_GROUP_NAME \
        --template-file azure-template.json \
        --parameters \
            environment=$ENVIRONMENT \
            containerImageName="${IMAGE_NAME}:${IMAGE_TAG}" \
            containerRegistryUrl=$ACR_LOGIN_SERVER \
            containerRegistryUsername=$ACR_USERNAME \
            containerRegistryPassword=$ACR_PASSWORD \
            finmindToken=$FINMIND_TOKEN
    
    echo_success "基礎設施部署成功"
}

# 獲取部署結果
get_deployment_info() {
    echo_info "獲取部署資訊..."
    
    # 獲取應用程式 URL
    APP_URL=$(az deployment group show \
        --resource-group $RESOURCE_GROUP_NAME \
        --name azure-template \
        --query properties.outputs.applicationUrl.value \
        --output tsv)
    
    # 獲取公共 IP
    PUBLIC_IP=$(az deployment group show \
        --resource-group $RESOURCE_GROUP_NAME \
        --name azure-template \
        --query properties.outputs.publicIPAddress.value \
        --output tsv)
    
    echo_success "=== 部署完成 ==="
    echo_info "應用程式 URL: $APP_URL"
    echo_info "公共 IP: $PUBLIC_IP"
    echo_info "Azure Portal: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP_NAME"
}

# 健康檢查
health_check() {
    echo_info "執行健康檢查..."
    
    # 等待服務啟動
    echo_info "等待服務啟動（這可能需要幾分鐘）..."
    sleep 180
    
    # 檢查容器群組狀態
    CONTAINER_STATE=$(az container show \
        --resource-group $RESOURCE_GROUP_NAME \
        --name "${ENVIRONMENT}-jojo-trading-cg" \
        --query containers[0].instanceView.currentState.state \
        --output tsv 2>/dev/null || echo "Unknown")
    
    echo_info "容器狀態: $CONTAINER_STATE"
    
    # 測試應用程式端點
    if [ -n "$APP_URL" ]; then
        if curl -f -s "${APP_URL}/_stcore/health" > /dev/null; then
            echo_success "應用程式健康檢查通過"
        else
            echo_warning "應用程式可能還在啟動中，請稍候再試"
            echo_info "手動檢查: ${APP_URL}/_stcore/health"
        fi
    fi
}

# 設置監控和告警
setup_monitoring() {
    echo_info "設置監控和告警..."
    
    # 創建動作群組（用於告警通知）
    az monitor action-group create \
        --resource-group $RESOURCE_GROUP_NAME \
        --name "jojo-trading-alerts" \
        --short-name "JoJoAlerts" \
        --action email admin admin@yourcompany.com
    
    # 創建 CPU 使用率告警
    az monitor metrics alert create \
        --resource-group $RESOURCE_GROUP_NAME \
        --name "high-cpu-usage" \
        --description "JoJo Trading High CPU Usage Alert" \
        --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.ContainerInstance/containerGroups/${ENVIRONMENT}-jojo-trading-cg" \
        --condition "avg Percentage CPU > 80" \
        --window-size 5m \
        --evaluation-frequency 1m \
        --action "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP_NAME/providers/microsoft.insights/actionGroups/jojo-trading-alerts"
    
    echo_success "監控和告警設置完成"
}

# 清理函數
cleanup() {
    echo_info "如需清理資源，請執行："
    echo "az group delete --name $RESOURCE_GROUP_NAME --yes --no-wait"
}

# 主執行流程
main() {
    echo_info "🚀 開始 JoJo Trading Azure 部署流程"
    echo_info "環境: $ENVIRONMENT"
    echo_info "區域: $AZURE_REGION"
    echo_info "資源群組: $RESOURCE_GROUP_NAME"
    
    check_prerequisites
    create_resource_group
    create_container_registry
    build_and_push_image
    get_acr_credentials
    deploy_infrastructure
    get_deployment_info
    setup_monitoring
    health_check
    
    echo_success "🎉 部署完成！JoJo Trading 現在運行在 Azure 上"
    echo_info "請訪問: $APP_URL"
    
    echo_info "部署詳細資訊已保存，如需清理資源請執行 cleanup 函數"
}

# 如果腳本被直接執行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
