"""
XBRL ETL 主要執行模組
替代原有的問題版本，提供更穩定的 XBRL 資料處理功能
"""

import os
import logging
import sys
from datetime import datetime
from typing import Optional

# 添加項目根目錄到路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.xbrl_etl.core_parser import run_xbrl_etl_pipeline, check_tej_parser_availability

# 設置日誌
logger = logging.getLogger(__name__)

def setup_logging():
    """設置日誌配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/xbrl_etl.log', encoding='utf-8')
        ]
    )

from typing import Optional

def run_xbrl_etl(year: Optional[int] = None, quarter: Optional[int] = None, 
                cache_dir: str = "./cache") -> bool:
    """
    執行 XBRL ETL 主流程
    
    Args:
        year: 年份（預設為當前年份）
        quarter: 季度（預設為當前季度）
        cache_dir: 快取目錄
        
    Returns:
        執行是否成功
    """
    # 設置日誌
    setup_logging()
    
    try:
        # 設置預設值
        if year is None:
            year = datetime.now().year
        if quarter is None:
            current_month = datetime.now().month
            quarter = (current_month - 1) // 3 + 1
        
        logger.info("========== XBRL ETL Pipeline 開始執行 ==========")
        logger.info(f"目標期間: {year}年第{quarter}季")
        logger.info(f"快取目錄: {cache_dir}")
        
        # 檢查 tej_xbrl_parser 狀態
        logger.info("--- 步驟0: 檢查系統依賴 ---")
        tej_available = check_tej_parser_availability()
        if not tej_available:
            logger.warning("tej_xbrl_parser 未安裝，將使用基本解析功能")
            logger.info("如需完整功能，請安裝: pip install tej_xbrl_parser")
        
        # 確保目錄存在
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # 執行主要流程
        start_time = datetime.now()
        success = run_xbrl_etl_pipeline(year, quarter, cache_dir)
        end_time = datetime.now()
        duration = end_time - start_time
        
        if success:
            logger.info(f"========== XBRL ETL Pipeline 執行完成 ==========")
            logger.info(f"執行時間: {duration}")
            logger.info("所有步驟已成功完成")
        else:
            logger.error(f"========== XBRL ETL Pipeline 執行失敗 ==========")
            logger.error(f"執行時間: {duration}")
            logger.error("請檢查上述錯誤訊息")
        
        return success
        
    except Exception as e:
        logger.error(f"XBRL ETL Pipeline 發生未預期錯誤: {e}")
        logger.exception("完整錯誤追蹤:")
        return False

def main():
    """命令列入口點"""
    import argparse
    
    parser = argparse.ArgumentParser(description='XBRL ETL Pipeline')
    parser.add_argument('--year', type=int, help='目標年份')
    parser.add_argument('--quarter', type=int, choices=[1, 2, 3, 4], help='目標季度')
    parser.add_argument('--cache-dir', default='./cache', help='快取目錄')
    
    args = parser.parse_args()
    
    success = run_xbrl_etl(args.year, args.quarter, args.cache_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
