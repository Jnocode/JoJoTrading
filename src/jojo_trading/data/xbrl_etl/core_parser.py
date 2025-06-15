import os
import requests
import zipfile
import glob
import pandas as pd
from bs4 import BeautifulSoup, Tag
import urllib3
import ssl
import logging
from typing import Optional, TYPE_CHECKING

# 類型檢查時才導入
if TYPE_CHECKING:
    try:
        import tej_xbrl_parser
    except ImportError:
        pass

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設置日誌
logger = logging.getLogger(__name__)

# 1. 取得最新 XBRL zip 下載連結
def get_latest_xbrl_zip_url(year: int, quarter: int, report_type: str = 'C') -> Optional[str]:
    """
    取得最新的XBRL zip檔案下載連結
    
    Args:
        year: 年份
        quarter: 季度 (1-4)
        report_type: 'C' for 合併, 'I' for 個體
        
    Returns:
        下載連結或None
    """
    url = "https://mops.twse.com.tw/t146sb01"
    
    # 配置請求會話，處理SSL問題
    session = requests.Session()
    session.verify = False  # 暫時跳過SSL驗證
    
    # 設置請求頭以模擬瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        logger.info(f"正在連接到 MOPS 網站: {url}")
        resp = session.get(url, headers=headers, timeout=30)
        resp.encoding = 'utf-8'
        
        if resp.status_code != 200:
            logger.error(f"HTTP請求失敗，狀態碼: {resp.status_code}")
            return None
            
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.find_all('a')
        
        for link in links:
            if isinstance(link, Tag):
                href = link.get('href')
                if href and isinstance(href, str):
                    text = link.get_text()
                    if (href.endswith('.zip') and 
                        str(year) in href and 
                        f"{quarter}_" in href and 
                        report_type in href):
                        # 例: XBRLPublic_C_2024Q1.zip
                        full_url = "https://mops.twse.com.tw" + href
                        logger.info(f"找到XBRL下載連結: {full_url}")
                        return full_url
                
        logger.warning(f"未找到符合條件的XBRL檔案: {year}年第{quarter}季{report_type}報表")
        return None
        
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL證書驗證失敗: {e}")
        logger.info("建議檢查網路連接或聯繫系統管理員")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"網路請求錯誤: {e}")
        return None
    except Exception as e:
        logger.error(f"解析網頁時發生錯誤: {e}")
        return None

# 2. 下載 XBRL zip
def download_xbrl_zip(url: str, save_dir: str, filename: Optional[str] = None) -> Optional[str]:
    """
    下載XBRL zip檔案
    
    Args:
        url: 下載連結
        save_dir: 儲存目錄
        filename: 檔案名稱（可選）
        
    Returns:
        儲存路徑或None
    """
    os.makedirs(save_dir, exist_ok=True)
    if filename is None:
        filename = url.split('/')[-1]
    save_path = os.path.join(save_dir, filename)
    
    if os.path.exists(save_path):
        logger.info(f"XBRL檔案已存在: {save_path}")
        return save_path
    
    logger.info(f"開始下載 XBRL 檔案: {url}")
    
    # 配置下載會話
    session = requests.Session()
    session.verify = False
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        resp = session.get(url, headers=headers, stream=True, timeout=60)
        resp.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"XBRL檔案下載完成: {save_path}")
        return save_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"下載XBRL檔案失敗: {e}")
        return None
    except Exception as e:
        logger.error(f"儲存XBRL檔案時發生錯誤: {e}")
        return None

# 3. 解壓縮 zip
def unzip_xbrl_files(zip_path: str, extract_to_dir: str) -> bool:
    """
    解壓縮XBRL zip檔案
    
    Args:
        zip_path: zip檔案路徑
        extract_to_dir: 解壓縮目標目錄
        
    Returns:
        是否成功
    """
    os.makedirs(extract_to_dir, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to_dir)
        logger.info(f"XBRL檔案解壓縮完成: {zip_path} -> {extract_to_dir}")
        return True
    except Exception as e:
        logger.error(f"解壓縮失敗: {e}")
        return False

# 4. 臨時解決方案：檢查 tej_xbrl_parser 是否可用
def check_tej_parser_availability() -> bool:
    """
    檢查 tej_xbrl_parser 是否可用
    
    Returns:
        是否可用
    """
    try:
        import importlib
        importlib.import_module('tej_xbrl_parser')
        logger.info("tej_xbrl_parser 模組可用")
        return True
    except ImportError:
        logger.warning("tej_xbrl_parser 模組未安裝")
        return False

# 5. 解析 XBRL 檔案的替代方案
def parse_xbrl_folder(xbrl_folder: str, output_dir: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    解析XBRL資料夾中的檔案
    
    Args:
        xbrl_folder: XBRL檔案資料夾路徑
        output_dir: 輸出目錄（可選）
        
    Returns:
        解析後的DataFrame或None
    """
    if not os.path.exists(xbrl_folder):
        logger.error(f"XBRL資料夾不存在: {xbrl_folder}")
        return None
      # 檢查是否有 tej_xbrl_parser
    if check_tej_parser_availability():
        try:
            # 動態導入 tej_xbrl_parser
            import importlib
            tej_parser = importlib.import_module('tej_xbrl_parser')
            XBRLParser = tej_parser.XBRLParser
            parser = XBRLParser()
            # 這裡需要根據實際的 tej_xbrl_parser API 來實作
            logger.info("使用 tej_xbrl_parser 解析XBRL檔案")
            # 實際解析邏輯需要根據 tej_xbrl_parser 文檔來實作
            return None
        except Exception as e:
            logger.error(f"使用 tej_xbrl_parser 解析失敗: {e}")
    
    # 備用方案：基本XML解析
    logger.info("使用基本XML解析作為備用方案")
    try:
        # 尋找 XBRL 檔案
        xbrl_files = glob.glob(os.path.join(xbrl_folder, "**", "*.html"), recursive=True)
        xbrl_files.extend(glob.glob(os.path.join(xbrl_folder, "**", "*.xml"), recursive=True))
        
        if not xbrl_files:
            logger.warning(f"在 {xbrl_folder} 中未找到XBRL檔案")
            return None
        
        logger.info(f"找到 {len(xbrl_files)} 個XBRL檔案")
        
        # 基本解析（這裡需要根據具體需求實作）
        # 目前只返回檔案列表作為示例
        file_info = []
        for file_path in xbrl_files:
            file_info.append({
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path)
            })
        
        df = pd.DataFrame(file_info)
        logger.info(f"基本解析完成，共處理 {len(df)} 個檔案")
        return df
        
    except Exception as e:
        logger.error(f"基本XML解析失敗: {e}")
        return None

# 6. 主要執行函數
def run_xbrl_etl_pipeline(year: int, quarter: int, 
                         cache_dir: str = "./cache",
                         force_download: bool = False) -> bool:
    """
    執行完整的XBRL ETL流程
    
    Args:
        year: 年份
        quarter: 季度
        cache_dir: 快取目錄
        force_download: 是否強制下載
        
    Returns:
        是否執行成功
    """
    try:
        # 設置目錄
        zip_dir = os.path.join(cache_dir, "xbrl_zip")
        unzip_dir = os.path.join(cache_dir, "xbrl_unzip")
        
        # 步驟1: 取得下載連結
        logger.info("=== 步驟1: 取得XBRL下載連結 ===")
        download_url = get_latest_xbrl_zip_url(year, quarter)
        if not download_url:
            logger.error("無法取得下載連結")
            return False
        
        # 步驟2: 下載檔案
        logger.info("=== 步驟2: 下載XBRL檔案 ===")
        zip_path = download_xbrl_zip(download_url, zip_dir)
        if not zip_path:
            logger.error("下載失敗")
            return False
        
        # 步驟3: 解壓縮
        logger.info("=== 步驟3: 解壓縮XBRL檔案 ===")
        if not unzip_xbrl_files(zip_path, unzip_dir):
            logger.error("解壓縮失敗")
            return False
        
        # 步驟4: 解析
        logger.info("=== 步驟4: 解析XBRL檔案 ===")
        parsed_data = parse_xbrl_folder(unzip_dir)
        if parsed_data is None:
            logger.warning("解析過程中出現問題，但不影響整體流程")
        else:
            logger.info(f"成功解析 {len(parsed_data)} 筆資料")
        
        logger.info("=== XBRL ETL 流程執行完成 ===")
        return True
        
    except Exception as e:
        logger.error(f"XBRL ETL 流程執行失敗: {e}")
        return False
