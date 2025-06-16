#!/usr/bin/env python3
"""
🐳 JoJo Trading - Docker 管理腳本
提供便捷的 Docker 操作命令
"""

import subprocess
import sys
import argparse
import time
from pathlib import Path

def run_command(cmd, check=True):
    """執行命令並顯示輸出"""
    print(f"🔄 執行: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode == 0

def build_image(tag="latest", no_cache=False):
    """建構 Docker 映像"""
    print("🏗️  建構 JoJo Trading Docker 映像...")
    cache_flag = "--no-cache" if no_cache else ""
    cmd = f"docker build {cache_flag} -t jojo-trading:{tag} ."
    return run_command(cmd)

def start_development():
    """啟動開發環境"""
    print("🛠️  啟動開發環境...")
    cmd = "docker-compose up -d"
    return run_command(cmd)

def start_production():
    """啟動生產環境"""
    print("🚀 啟動生產環境...")
    cmd = "docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d"
    return run_command(cmd)

def stop_all():
    """停止所有容器"""
    print("⏹️  停止所有容器...")
    cmd = "docker-compose down"
    return run_command(cmd)

def view_logs(service="jojo-trading", follow=True):
    """查看服務日誌"""
    print(f"📋 查看 {service} 日誌...")
    follow_flag = "-f" if follow else ""
    cmd = f"docker-compose logs {follow_flag} {service}"
    return run_command(cmd)

def health_check():
    """檢查服務健康狀態"""
    print("🏥 檢查服務健康狀態...")
    
    # 檢查容器狀態
    cmd = "docker-compose ps"
    if not run_command(cmd, check=False):
        print("❌ 無法獲取容器狀態")
        return False
    
    # 檢查應用程式健康
    print("⏳ 等待應用程式啟動...")
    time.sleep(10)
    
    health_cmd = "curl -f http://localhost:8501/_stcore/health"
    if run_command(health_cmd, check=False):
        print("✅ 應用程式健康檢查通過")
        return True
    else:
        print("❌ 應用程式健康檢查失敗")
        return False

def clean_up():
    """清理 Docker 資源"""
    print("🧹 清理 Docker 資源...")
    
    # 停止容器
    run_command("docker-compose down", check=False)
    
    # 清理無用映像
    run_command("docker image prune -f", check=False)
    
    # 清理無用卷
    run_command("docker volume prune -f", check=False)
    
    print("✅ 清理完成")

def reset_environment():
    """重置整個環境"""
    print("🔄 重置 Docker 環境...")
    
    # 停止並移除所有相關容器
    run_command("docker-compose down --volumes --remove-orphans", check=False)
    
    # 移除相關映像
    run_command("docker rmi jojo-trading:latest", check=False)
    
    # 重新建構
    build_image(no_cache=True)
    
    print("✅ 環境重置完成")

def quick_deploy():
    """快速部署（建構+啟動）"""
    print("⚡ 快速部署 JoJo Trading...")
    
    # 建構映像
    if not build_image():
        print("❌ 映像建構失敗")
        return False
    
    # 啟動開發環境
    if not start_development():
        print("❌ 容器啟動失敗")
        return False
    
    # 健康檢查
    if not health_check():
        print("❌ 部署驗證失敗")
        return False
    
    print("🎉 部署成功！訪問 http://localhost:8501")
    return True

def main():
    parser = argparse.ArgumentParser(description="JoJo Trading Docker 管理工具")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 建構命令
    build_parser = subparsers.add_parser('build', help='建構 Docker 映像')
    build_parser.add_argument('--tag', default='latest', help='映像標籤')
    build_parser.add_argument('--no-cache', action='store_true', help='不使用緩存')
    
    # 啟動命令
    subparsers.add_parser('start-dev', help='啟動開發環境')
    subparsers.add_parser('start-prod', help='啟動生產環境')
    
    # 停止命令
    subparsers.add_parser('stop', help='停止所有容器')
    
    # 日誌命令
    logs_parser = subparsers.add_parser('logs', help='查看日誌')
    logs_parser.add_argument('--service', default='jojo-trading', help='服務名稱')
    logs_parser.add_argument('--no-follow', action='store_true', help='不持續跟蹤')
    
    # 其他命令
    subparsers.add_parser('health', help='健康檢查')
    subparsers.add_parser('clean', help='清理 Docker 資源')
    subparsers.add_parser('reset', help='重置環境')
    subparsers.add_parser('deploy', help='快速部署')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 確保在正確的目錄
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # 執行命令
    if args.command == 'build':
        build_image(args.tag, args.no_cache)
    elif args.command == 'start-dev':
        start_development()
    elif args.command == 'start-prod':
        start_production()
    elif args.command == 'stop':
        stop_all()
    elif args.command == 'logs':
        view_logs(args.service, not args.no_follow)
    elif args.command == 'health':
        health_check()
    elif args.command == 'clean':
        clean_up()
    elif args.command == 'reset':
        reset_environment()
    elif args.command == 'deploy':
        quick_deploy()

if __name__ == "__main__":
    import os
    main()
