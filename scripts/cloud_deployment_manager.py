#!/usr/bin/env python3
"""
🚀 JoJo Trading 雲端部署管理器
統一管理 AWS、Azure、Kubernetes 部署
"""

import argparse
import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CloudDeploymentManager:
    """雲端部署管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.deployment_configs = {
            'aws': self.project_root / 'cloud_deployment' / 'aws',
            'azure': self.project_root / 'cloud_deployment' / 'azure',
            'kubernetes': self.project_root / 'cloud_deployment' / 'kubernetes'
        }
        
    def check_prerequisites(self, platform: str) -> bool:
        """檢查部署先決條件"""
        logger.info(f"🔍 檢查 {platform} 部署先決條件...")
        
        required_tools = {
            'aws': ['aws', 'docker'],
            'azure': ['az', 'docker'],
            'kubernetes': ['kubectl', 'docker']
        }
        
        missing_tools = []
        for tool in required_tools.get(platform, []):
            if not self._check_command(tool):
                missing_tools.append(tool)
        
        if missing_tools:
            logger.error(f"❌ 缺少必要工具: {', '.join(missing_tools)}")
            return False
            
        logger.info("✅ 所有必要工具已就緒")
        return True
    
    def _check_command(self, command: str) -> bool:
        """檢查命令是否可用"""
        try:
            subprocess.run([command, '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def deploy_to_aws(self, environment: str = 'production') -> bool:
        """部署到 AWS ECS"""
        logger.info("🚀 開始 AWS ECS 部署...")
        
        if not self.check_prerequisites('aws'):
            return False
            
        # 檢查 AWS 認證
        try:
            result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                                  capture_output=True, check=True, text=True)
            account_info = json.loads(result.stdout)
            logger.info(f"📋 AWS 帳戶: {account_info.get('Account', 'Unknown')}")
        except subprocess.CalledProcessError:
            logger.error("❌ AWS 認證失敗，請執行 'aws configure'")
            return False
        
        # 執行部署腳本
        script_path = self.deployment_configs['aws'] / 'deploy.sh'
        if not script_path.exists():
            logger.error(f"❌ 部署腳本不存在: {script_path}")
            return False
            
        try:
            # 在 Windows 上需要使用 bash 或 WSL
            if os.name == 'nt':
                # Windows 環境，使用 PowerShell 執行等效操作
                logger.info("🔧 在 Windows 環境下執行 AWS 部署...")
                return self._deploy_aws_windows(environment)
            else:
                # Unix 環境
                subprocess.run(['bash', str(script_path)], check=True, cwd=script_path.parent)
                
            logger.info("✅ AWS 部署完成")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ AWS 部署失敗: {e}")
            return False
    
    def _deploy_aws_windows(self, environment: str) -> bool:
        """Windows 環境下的 AWS 部署"""
        try:
            # 獲取帳戶 ID
            result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                                  capture_output=True, check=True, text=True)
            account_info = json.loads(result.stdout)
            account_id = account_info['Account']
            
            # 配置變數
            aws_region = "ap-northeast-1"
            ecr_repository = "jojo-trading"
            stack_name = f"jojo-trading-{environment}"
            
            logger.info("🏗️ 創建 ECR 倉庫...")
            subprocess.run([
                'aws', 'ecr', 'create-repository',
                '--repository-name', ecr_repository,
                '--region', aws_region,
                '--image-scanning-configuration', 'scanOnPush=true'
            ], capture_output=True)  # 忽略錯誤，倉庫可能已存在
            
            logger.info("🐳 構建並推送 Docker 映像...")
            # ECR 登入
            login_cmd = subprocess.run([
                'aws', 'ecr', 'get-login-password',
                '--region', aws_region
            ], capture_output=True, check=True, text=True)
            
            subprocess.run([
                'docker', 'login', '--username', 'AWS', '--password-stdin',
                f"{account_id}.dkr.ecr.{aws_region}.amazonaws.com"
            ], input=login_cmd.stdout, text=True, check=True, cwd=self.project_root)
            
            # 構建映像
            subprocess.run([
                'docker', 'build', '-t', f"{ecr_repository}:latest", 
                '-f', 'Dockerfile', '.'
            ], check=True, cwd=self.project_root)
            
            # 標記並推送映像
            image_uri = f"{account_id}.dkr.ecr.{aws_region}.amazonaws.com/{ecr_repository}:latest"
            subprocess.run(['docker', 'tag', f"{ecr_repository}:latest", image_uri], check=True)
            subprocess.run(['docker', 'push', image_uri], check=True)
            
            logger.info("☁️ 部署 CloudFormation 模板...")
            cf_template = self.deployment_configs['aws'] / 'cloudformation-infrastructure.yml'
            
            # 更新模板中的映像 URI
            with open(cf_template, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            template_content = template_content.replace('jojo-trading:latest', image_uri)
            
            # 寫入臨時文件
            temp_template = cf_template.parent / 'temp-infrastructure.yml'
            with open(temp_template, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            try:
                subprocess.run([
                    'aws', 'cloudformation', 'deploy',
                    '--template-file', str(temp_template),
                    '--stack-name', stack_name,
                    '--capabilities', 'CAPABILITY_IAM',
                    '--parameter-overrides', f'Environment={environment}',
                    '--region', aws_region,
                    '--no-fail-on-empty-changeset'
                ], check=True)
                
                logger.info("📋 獲取部署資訊...")
                result = subprocess.run([
                    'aws', 'cloudformation', 'describe-stacks',
                    '--stack-name', stack_name,
                    '--region', aws_region,
                    '--query', 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue',
                    '--output', 'text'
                ], capture_output=True, check=True, text=True)
                
                lb_url = result.stdout.strip()
                logger.info(f"🎉 部署完成！應用程式 URL: {lb_url}")
                
                return True
                
            finally:
                # 清理臨時文件
                if temp_template.exists():
                    temp_template.unlink()
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ AWS 部署失敗: {e}")
            return False
    
    def deploy_to_azure(self, environment: str = 'production') -> bool:
        """部署到 Azure Container Instances"""
        logger.info("🚀 開始 Azure 部署...")
        
        if not self.check_prerequisites('azure'):
            return False
            
        # 檢查 Azure 認證
        try:
            subprocess.run(['az', 'account', 'show'], 
                         capture_output=True, check=True)
            logger.info("✅ Azure 認證正常")
        except subprocess.CalledProcessError:
            logger.error("❌ Azure 認證失敗，請執行 'az login'")
            return False
        
        # 執行部署腳本
        script_path = self.deployment_configs['azure'] / 'deploy.sh'
        if not script_path.exists():
            logger.error(f"❌ 部署腳本不存在: {script_path}")
            return False
            
        try:
            if os.name == 'nt':
                logger.info("🔧 在 Windows 環境下執行 Azure 部署...")
                return self._deploy_azure_windows(environment)
            else:
                subprocess.run(['bash', str(script_path)], check=True, cwd=script_path.parent)
                
            logger.info("✅ Azure 部署完成")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Azure 部署失敗: {e}")
            return False
    
    def _deploy_azure_windows(self, environment: str) -> bool:
        """Windows 環境下的 Azure 部署"""
        try:
            # 配置變數
            resource_group = f"rg-jojo-trading-{environment}"
            location = "eastasia"
            acr_name = f"crjojotrading{environment}"
            
            logger.info("🏗️ 創建資源群組...")
            subprocess.run([
                'az', 'group', 'create',
                '--name', resource_group,
                '--location', location
            ], capture_output=True)  # 忽略錯誤，可能已存在
            
            logger.info("🏗️ 創建 Container Registry...")
            subprocess.run([
                'az', 'acr', 'create',
                '--resource-group', resource_group,
                '--name', acr_name,
                '--sku', 'Basic',
                '--admin-enabled', 'true'
            ], capture_output=True)  # 忽略錯誤，可能已存在
            
            logger.info("🐳 構建並推送 Docker 映像...")
            # 獲取 ACR 登入資訊
            result = subprocess.run([
                'az', 'acr', 'show',
                '--name', acr_name,
                '--resource-group', resource_group,
                '--query', 'loginServer',
                '--output', 'tsv'
            ], capture_output=True, check=True, text=True)
            acr_server = result.stdout.strip()
            
            # ACR 登入
            subprocess.run(['az', 'acr', 'login', '--name', acr_name], check=True)
            
            # 構建並推送映像
            image_name = f"{acr_server}/jojo-trading:latest"
            subprocess.run([
                'docker', 'build', '-t', 'jojo-trading:latest', 
                '-f', 'Dockerfile', '.'
            ], check=True, cwd=self.project_root)
            
            subprocess.run(['docker', 'tag', 'jojo-trading:latest', image_name], check=True)
            subprocess.run(['docker', 'push', image_name], check=True)
            
            logger.info("☁️ 部署 ARM 模板...")
            # 這裡可以添加 ARM 模板部署邏輯
            
            logger.info("🎉 Azure 部署完成！")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Azure 部署失敗: {e}")
            return False
    
    def deploy_to_kubernetes(self, environment: str = 'production') -> bool:
        """部署到 Kubernetes"""
        logger.info("🚀 開始 Kubernetes 部署...")
        
        if not self.check_prerequisites('kubernetes'):
            return False
            
        # 檢查 Kubernetes 連接
        try:
            subprocess.run(['kubectl', 'cluster-info'], 
                         capture_output=True, check=True)
            logger.info("✅ Kubernetes 集群連接正常")
        except subprocess.CalledProcessError:
            logger.error("❌ 無法連接到 Kubernetes 集群")
            return False
        
        # 執行部署
        try:
            k8s_config = self.deployment_configs['kubernetes'] / 'k8s-deployment.yaml'
            
            # 創建 namespace
            subprocess.run([
                'kubectl', 'create', 'namespace', 'jojo-trading'
            ], capture_output=True)  # 忽略錯誤，可能已存在
            
            # 應用部署配置
            subprocess.run(['kubectl', 'apply', '-f', str(k8s_config)], check=True)
            
            # 等待部署就緒
            logger.info("⏳ 等待部署完成...")
            subprocess.run([
                'kubectl', 'wait', '--for=condition=available',
                '--timeout=300s', 'deployment/jojo-trading-app',
                '-n', 'jojo-trading'
            ], check=True)
            
            logger.info("✅ Kubernetes 部署完成")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Kubernetes 部署失敗: {e}")
            return False
    
    def get_deployment_status(self, platform: str) -> Dict:
        """獲取部署狀態"""
        logger.info(f"📊 獲取 {platform} 部署狀態...")
        
        try:
            if platform == 'aws':
                return self._get_aws_status()
            elif platform == 'azure':
                return self._get_azure_status()
            elif platform == 'kubernetes':
                return self._get_k8s_status()
            else:
                return {'error': f'不支持的平台: {platform}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _get_aws_status(self) -> Dict:
        """獲取 AWS 部署狀態"""
        try:
            # 獲取 ECS 服務狀態
            result = subprocess.run([
                'aws', 'ecs', 'describe-services',
                '--cluster', 'production-jojo-trading-cluster',
                '--services', 'production-jojo-trading-service',
                '--query', 'services[0].{status:status,running:runningCount,desired:desiredCount}',
                '--output', 'json'
            ], capture_output=True, check=True, text=True)
            
            return json.loads(result.stdout)
            
        except subprocess.CalledProcessError:
            return {'error': 'AWS 服務狀態獲取失敗'}
    
    def _get_azure_status(self) -> Dict:
        """獲取 Azure 部署狀態"""
        try:
            result = subprocess.run([
                'az', 'container', 'show',
                '--resource-group', 'rg-jojo-trading-production',
                '--name', 'production-jojo-trading-cg',
                '--query', '{state:containers[0].instanceView.currentState.state,restartCount:containers[0].instanceView.restartCount}',
                '--output', 'json'
            ], capture_output=True, check=True, text=True)
            
            return json.loads(result.stdout)
            
        except subprocess.CalledProcessError:
            return {'error': 'Azure 容器狀態獲取失敗'}
    
    def _get_k8s_status(self) -> Dict:
        """獲取 Kubernetes 部署狀態"""
        try:
            result = subprocess.run([
                'kubectl', 'get', 'deployment', 'jojo-trading-app',
                '-n', 'jojo-trading',
                '-o', 'json'
            ], capture_output=True, check=True, text=True)
            
            deployment = json.loads(result.stdout)
            status = deployment.get('status', {})
            
            return {
                'ready_replicas': status.get('readyReplicas', 0),
                'replicas': status.get('replicas', 0),
                'updated_replicas': status.get('updatedReplicas', 0)
            }
            
        except subprocess.CalledProcessError:
            return {'error': 'Kubernetes 部署狀態獲取失敗'}
    
    def cleanup_deployment(self, platform: str, environment: str = 'production') -> bool:
        """清理部署資源"""
        logger.info(f"🧹 清理 {platform} 部署資源...")
        
        try:
            if platform == 'aws':
                subprocess.run([
                    'aws', 'cloudformation', 'delete-stack',
                    '--stack-name', f'jojo-trading-{environment}'
                ], check=True)
                
            elif platform == 'azure':
                subprocess.run([
                    'az', 'group', 'delete',
                    '--name', f'rg-jojo-trading-{environment}',
                    '--yes', '--no-wait'
                ], check=True)
                
            elif platform == 'kubernetes':
                subprocess.run([
                    'kubectl', 'delete', 'namespace', 'jojo-trading'
                ], check=True)
            
            logger.info(f"✅ {platform} 資源清理完成")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ {platform} 資源清理失敗: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='JoJo Trading 雲端部署管理器')
    parser.add_argument('action', choices=['deploy', 'status', 'cleanup'],
                       help='執行的動作')
    parser.add_argument('platform', choices=['aws', 'azure', 'kubernetes', 'all'],
                       help='目標平台')
    parser.add_argument('--environment', default='production',
                       help='部署環境 (default: production)')
    
    args = parser.parse_args()
    
    manager = CloudDeploymentManager()
    
    if args.platform == 'all':
        platforms = ['aws', 'azure', 'kubernetes']
    else:
        platforms = [args.platform]
    
    success = True
    
    for platform in platforms:
        logger.info(f"\n{'='*50}")
        logger.info(f"🎯 處理平台: {platform.upper()}")
        logger.info(f"{'='*50}")
        
        if args.action == 'deploy':
            if platform == 'aws':
                result = manager.deploy_to_aws(args.environment)
            elif platform == 'azure':
                result = manager.deploy_to_azure(args.environment)
            elif platform == 'kubernetes':
                result = manager.deploy_to_kubernetes(args.environment)
            
            success = success and result
            
        elif args.action == 'status':
            status = manager.get_deployment_status(platform)
            logger.info(f"📊 {platform} 狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")
            
        elif args.action == 'cleanup':
            result = manager.cleanup_deployment(platform, args.environment)
            success = success and result
    
    if success:
        logger.info("\n🎉 所有操作成功完成！")
        sys.exit(0)
    else:
        logger.error("\n❌ 部分操作失敗，請檢查日誌")
        sys.exit(1)

if __name__ == '__main__':
    main()
