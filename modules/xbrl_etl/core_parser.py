import os
import requests
import zipfile
import glob
import pandas as pd
from bs4 import BeautifulSoup
# 預留：未來將改用 arelle 解析 XBRL
# from tej_xbrl_parser import XBRLParser

# 1. 取得最新 XBRL zip 下載連結
def get_latest_xbrl_zip_url(year, quarter, report_type='C'):
    """
    report_type: 'C' for 合併, 'I' for 個體
    """
    url = "https://mops.twse.com.tw/t146sb01"
    resp = requests.get(url)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.find_all('a')
    for link in links:
        href = link.get('href', '')
        text = link.text
        if href.endswith('.zip') and str(year) in href and f"{quarter}_" in href and report_type in href:
            # 例: XBRLPublic_C_2024Q1.zip
            return "https://mops.twse.com.tw" + href
    return None

# 2. 下載 XBRL zip
def download_xbrl_zip(url, save_dir, filename=None):
    os.makedirs(save_dir, exist_ok=True)
    if filename is None:
        filename = url.split('/')[-1]
    save_path = os.path.join(save_dir, filename)
    if os.path.exists(save_path):
        print(f"[xbrl_etl] Zip already exists: {save_path}")
        return save_path
    print(f"[xbrl_etl] Downloading {url} ...")
    resp = requests.get(url, stream=True)
    with open(save_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"[xbrl_etl] Downloaded to {save_path}")
    return save_path

# 3. 解壓縮 zip
def unzip_xbrl_files(zip_path, extract_to_dir):
    os.makedirs(extract_to_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to_dir)
    print(f"[xbrl_etl] Unzipped {zip_path} to {extract_to_dir}")

# 4. 解析 XBRL 資料夾
def parse_xbrl_folder(xbrl_folder_path):
    """
    使用 arelle 解析指定資料夾內所有 XBRL 檔案，根據映射表回傳結構化財務數據 DataFrame
    """
    from arelle import Cntlr
    import os
    from modules.xbrl_etl.financial_items_mapping import FINANCIAL_ITEMS_MAPPING

    xbrl_files = [f for f in os.listdir(xbrl_folder_path) if f.endswith(".xml") or f.endswith(".xbrl") or f.endswith(".html")]
    all_data = []
    for file in xbrl_files:
        file_path = os.path.join(xbrl_folder_path, file)
        try:
            cntlr = Cntlr.Cntlr(logFileName=None)
            model_xbrl = cntlr.modelManager.load(file_path)
            # 建立一個 dict 來存放每個財務科目的值
            item_dict = {"source_file": file}
            for zh_name, tag_list in FINANCIAL_ITEMS_MAPPING.items():
                found = False
                for fact in model_xbrl.facts:
                    if fact.concept is None:
                        continue
                    # 只比對 concept.name（不含 namespace）
                    if fact.concept.name in tag_list:
                        item_dict[zh_name] = fact.value
                        found = True
                        break
                if not found:
                    item_dict[zh_name] = None
            all_data.append(item_dict)
            cntlr.modelManager.close()
        except Exception as e:
            print(f"[xbrl_etl] Arelle parse failed: {file_path}, {e}")
    if all_data:
        final_df = pd.DataFrame(all_data)
        print(f"[xbrl_etl] Parsed {len(all_data)} files with arelle mapping, shape={final_df.shape}")
        return final_df
    else:
        print("[xbrl_etl] No XBRL files parsed by arelle.")
        return pd.DataFrame()

# 5. 儲存解析後資料
def save_parsed_xbrl_data(df, year, quarter, report_type, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    fname = f"{year}_Q{quarter}_{report_type}_parsed.parquet"
    path = os.path.join(save_dir, fname)
    df.to_parquet(path)
    print(f"[xbrl_etl] Saved parsed data to {path}")
    return path

# 6. 載入解析後資料
def load_parsed_xbrl_data(year, quarter, report_type, load_dir):
    fname = f"{year}_Q{quarter}_{report_type}_parsed.parquet"
    path = os.path.join(load_dir, fname)
    if os.path.exists(path):
        return pd.read_parquet(path)
    else:
        print(f"[xbrl_etl] No parsed data found at {path}")
        return None

# 7. 更新單一期別
def update_xbrl_data_for_period(year, quarter, report_type='C', force_update=False):
    zip_dir = "./cache/xbrl_zip"
    unzip_dir = "./cache/xbrl_unzip"
    parsed_dir = "./cache/xbrl_parsed_data"
    # 檢查是否已存在
    fname = f"{year}_Q{quarter}_{report_type}_parsed.parquet"
    parsed_path = os.path.join(parsed_dir, fname)
    if os.path.exists(parsed_path) and not force_update:
        print(f"[xbrl_etl] Parsed data already exists: {parsed_path}")
        return parsed_path
    # 取得下載連結
    zip_url = get_latest_xbrl_zip_url(year, quarter, report_type)
    if not zip_url:
        print(f"[xbrl_etl] No zip url found for {year} Q{quarter} {report_type}")
        return None
    # 下載
    zip_path = download_xbrl_zip(zip_url, zip_dir)
    # 解壓縮
    unzip_xbrl_files(zip_path, unzip_dir)
    # 解析
    df = parse_xbrl_folder(unzip_dir)
    # 儲存
    save_parsed_xbrl_data(df, year, quarter, report_type, parsed_dir)
    return parsed_path

# 8. 批次檢查/更新多期
def ensure_latest_xbrl_data(num_past_quarters=8, start_year=None, start_quarter=None, report_type='C'):
    import datetime
    now = datetime.date.today()
    if start_year is None:
        start_year = now.year
    if start_quarter is None:
        # 推估目前季度
        m = now.month
        if m <= 3:
            start_quarter = 4
            start_year -= 1
        elif m <= 5:
            start_quarter = 1
        elif m <= 8:
            start_quarter = 2
        elif m <= 11:
            start_quarter = 3
        else:
            start_quarter = 4
    y, q = start_year, start_quarter
    for i in range(num_past_quarters):
        print(f"[xbrl_etl] Checking {y} Q{q} ...")
        update_xbrl_data_for_period(y, q, report_type)
        # 前一期
        if q == 1:
            q = 4
            y -= 1
        else:
            q -= 1
