#!/bin/bash

# 🚀 JoJo Trading Kubernetes 自動化部署腳本
# 此腳本自動化整個 Kubernetes 部署流程

set -e

# 配置變數
NAMESPACE="jojo-trading"
IMAGE_NAME="jojo-trading"
IMAGE_TAG="latest"
REGISTRY_URL="your-registry.com"  # 請替換為您的 Container Registry URL
DOMAIN="jojo-trading.yourdomain.com"  # 請替換為您的域名

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
    
    if ! command -v kubectl &> /dev/null; then
        echo_error "kubectl 未安裝，請先安裝 kubectl"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo_error "Docker 未安裝，請先安裝 Docker"
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        echo_warning "Helm 未安裝，建議安裝 Helm 以獲得更好的體驗"
    fi
    
    # 檢查 kubectl 連接
    if ! kubectl cluster-info &> /dev/null; then
        echo_error "無法連接到 Kubernetes 集群，請檢查 kubeconfig"
        exit 1
    fi
    
    echo_success "所有必要工具已就緒"
}

# 獲取集群資訊
get_cluster_info() {
    echo_info "獲取 Kubernetes 集群資訊..."
    
    CLUSTER_NAME=$(kubectl config current-context)
    CLUSTER_VERSION=$(kubectl version --short --client | grep Client | awk '{print $3}')
    
    echo_info "當前集群: $CLUSTER_NAME"
    echo_info "kubectl 版本: $CLUSTER_VERSION"
    
    # 檢查節點狀態
    NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
    echo_info "可用節點數: $NODE_COUNT"
}

# 構建並推送 Docker 映像
build_and_push_image() {
    echo_info "構建並推送 Docker 映像..."
    
    # 構建映像
    cd ../../
    docker build -t $IMAGE_NAME:$IMAGE_TAG -f Dockerfile .
    
    # 標記映像
    docker tag $IMAGE_NAME:$IMAGE_TAG $REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG
    
    # 推送映像（需要事先登入 registry）
    echo_info "推送映像到 $REGISTRY_URL..."
    docker push $REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG
    
    echo_success "Docker 映像推送成功"
}

# 創建 namespace
create_namespace() {
    echo_info "創建 Kubernetes namespace..."
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        echo_warning "Namespace $NAMESPACE 已存在"
    else
        kubectl create namespace $NAMESPACE
        echo_success "Namespace $NAMESPACE 創建成功"
    fi
}

# 配置 secrets
setup_secrets() {
    echo_info "設置 Kubernetes secrets..."
    
    # 提示輸入 FinMind Token
    if [ -z "$FINMIND_TOKEN" ]; then
        echo_info "請輸入 FinMind API Token:"
        read -s FINMIND_TOKEN
    fi
    
    # 創建或更新 secret
    kubectl create secret generic jojo-trading-secrets \
        --from-literal=finmind-token="$FINMIND_TOKEN" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    echo_success "Secrets 設置完成"
}

# 部署應用程式
deploy_application() {
    echo_info "部署 JoJo Trading 應用程式..."
    
    # 更新部署文件中的映像 URL
    sed -i "s|jojo-trading:latest|$REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG|g" k8s-deployment.yaml
    sed -i "s|jojo-trading.yourdomain.com|$DOMAIN|g" k8s-deployment.yaml
    
    # 應用部署配置
    kubectl apply -f k8s-deployment.yaml
    
    echo_success "應用程式部署完成"
}

# 等待部署完成
wait_for_deployment() {
    echo_info "等待部署完成..."
    
    # 等待 deployment 就緒
    kubectl wait --for=condition=available --timeout=300s deployment/jojo-trading-app -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/redis -n $NAMESPACE
    
    echo_success "部署就緒"
}

# 設置 NGINX Ingress Controller
setup_ingress_controller() {
    echo_info "檢查 NGINX Ingress Controller..."
    
    # 檢查是否已安裝 NGINX Ingress Controller
    if ! kubectl get deployment ingress-nginx-controller -n ingress-nginx &> /dev/null; then
        echo_info "安裝 NGINX Ingress Controller..."
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
        
        # 等待 Ingress Controller 就緒
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/component=controller \
            --timeout=120s
    else
        echo_success "NGINX Ingress Controller 已存在"
    fi
}

# 設置 cert-manager
setup_cert_manager() {
    echo_info "檢查 cert-manager..."
    
    # 檢查是否已安裝 cert-manager
    if ! kubectl get deployment cert-manager -n cert-manager &> /dev/null; then
        echo_info "安裝 cert-manager..."
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
        
        # 等待 cert-manager 就緒
        kubectl wait --for=condition=available --timeout=300s deployment/cert-manager -n cert-manager
        kubectl wait --for=condition=available --timeout=300s deployment/cert-manager-cainjector -n cert-manager
        kubectl wait --for=condition=available --timeout=300s deployment/cert-manager-webhook -n cert-manager
        
        # 創建 ClusterIssuer
        cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
    else
        echo_success "cert-manager 已存在"
    fi
}

# 獲取部署資訊
get_deployment_info() {
    echo_info "獲取部署資訊..."
    
    # 獲取 pods 狀態
    echo_info "Pods 狀態:"
    kubectl get pods -n $NAMESPACE
    
    # 獲取 services
    echo_info "Services:"
    kubectl get services -n $NAMESPACE
    
    # 獲取 ingress
    echo_info "Ingress:"
    kubectl get ingress -n $NAMESPACE
    
    # 獲取外部 IP
    EXTERNAL_IP=$(kubectl get service ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    
    echo_success "=== 部署完成 ==="
    echo_info "應用程式 URL: https://$DOMAIN"
    echo_info "外部 IP: $EXTERNAL_IP"
    echo_info "請確保 DNS 記錄 $DOMAIN 指向 $EXTERNAL_IP"
}

# 監控部署狀態
monitor_deployment() {
    echo_info "監控部署狀態..."
    
    # 顯示資源使用情況
    echo_info "資源使用情況:"
    kubectl top pods -n $NAMESPACE || echo_warning "Metrics server 可能未安裝"
    
    # 顯示 HPA 狀態
    echo_info "自動擴展狀態:"
    kubectl get hpa -n $NAMESPACE
    
    # 檢查日誌
    echo_info "應用程式日誌（最近 10 行）:"
    kubectl logs -n $NAMESPACE deployment/jojo-trading-app --tail=10
}

# 健康檢查
health_check() {
    echo_info "執行健康檢查..."
    
    # 檢查 pod 狀態
    READY_PODS=$(kubectl get pods -n $NAMESPACE -l app=jojo-trading --no-headers | grep "Running" | wc -l)
    TOTAL_PODS=$(kubectl get pods -n $NAMESPACE -l app=jojo-trading --no-headers | wc -l)
    
    echo_info "就緒的 Pods: $READY_PODS/$TOTAL_PODS"
    
    if [ "$READY_PODS" -eq "$TOTAL_PODS" ] && [ "$TOTAL_PODS" -gt 0 ]; then
        echo_success "所有 Pods 運行正常"
        
        # 測試應用程式端點
        if [ "$EXTERNAL_IP" != "pending" ] && [ -n "$EXTERNAL_IP" ]; then
            echo_info "測試應用程式端點..."
            if curl -f -s -k "https://$DOMAIN/_stcore/health" > /dev/null; then
                echo_success "應用程式健康檢查通過"
            else
                echo_warning "應用程式可能還在啟動中，或 DNS 未正確配置"
            fi
        else
            echo_warning "外部 IP 還在分配中，請稍候"
        fi
    else
        echo_warning "部分 Pods 可能還在啟動中"
    fi
}

# 擴展功能 - 設置監控
setup_monitoring() {
    echo_info "設置 Prometheus 監控（可選）..."
    
    read -p "是否安裝 Prometheus 監控？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 使用 Helm 安裝 Prometheus
        if command -v helm &> /dev/null; then
            helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
            helm repo update
            helm install prometheus prometheus-community/kube-prometheus-stack \
                --namespace monitoring \
                --create-namespace \
                --set grafana.adminPassword=admin123
            
            echo_success "Prometheus 監控已安裝"
            echo_info "Grafana 密碼: admin123"
        else
            echo_warning "Helm 未安裝，跳過 Prometheus 安裝"
        fi
    fi
}

# 清理函數
cleanup() {
    echo_info "如需清理資源，請執行："
    echo "kubectl delete namespace $NAMESPACE"
    echo "kubectl delete clusterissuer letsencrypt-prod"
}

# 故障排除提示
troubleshooting() {
    echo_info "=== 故障排除提示 ==="
    echo "1. 檢查 Pod 狀態: kubectl get pods -n $NAMESPACE"
    echo "2. 查看 Pod 日誌: kubectl logs -n $NAMESPACE -l app=jojo-trading"
    echo "3. 檢查 Ingress: kubectl describe ingress -n $NAMESPACE"
    echo "4. 檢查 Services: kubectl get services -n $NAMESPACE"
    echo "5. 檢查事件: kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'"
}

# 主執行流程
main() {
    echo_info "🚀 開始 JoJo Trading Kubernetes 部署流程"
    echo_info "目標域名: $DOMAIN"
    echo_info "映像: $REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG"
    
    check_prerequisites
    get_cluster_info
    
    # 提示用戶確認配置
    echo_warning "請確認以下配置正確:"
    echo "- Container Registry: $REGISTRY_URL"
    echo "- 域名: $DOMAIN"
    echo "- Namespace: $NAMESPACE"
    read -p "繼續部署？(Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        exit 0
    fi
    
    build_and_push_image
    create_namespace
    setup_secrets
    setup_ingress_controller
    setup_cert_manager
    deploy_application
    wait_for_deployment
    get_deployment_info
    monitor_deployment
    health_check
    setup_monitoring
    
    echo_success "🎉 部署完成！JoJo Trading 現在運行在 Kubernetes 上"
    echo_info "請訪問: https://$DOMAIN"
    
    troubleshooting
    echo_info "部署詳細資訊已保存，如需清理資源請執行 cleanup 函數"
}

# 如果腳本被直接執行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
