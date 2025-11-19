import os
import requests
import pandas as pd
from datetime import datetime

def get_minguo_year(dt: datetime):
    """西元轉民國年"""
    return dt.year - 1911

def download_twse_capital_change_csv(target_date: datetime, cache_dir="cache/twse_capital_change"):
    """
    自動下載指定年月的股本異動彙總表（CSV），並快取於本地。
    :param target_date: datetime 對齊財報期末
    :param cache_dir: 本地快取目錄
    :return: pd.DataFrame or None
    """
    os.makedirs(cache_dir, exist_ok=True)
    minguo_year = get_minguo_year(target_date)
    month = target_date.month
    cache_path = os.path.join(cache_dir, f"capital_change_{minguo_year}_{month:02d}.csv")
    if os.path.exists(cache_path):
        try:
            df = pd.read_csv(cache_path, encoding="utf-8")
            if not df.empty:
                return df
        except Exception:
            pass
    url = f"https://mops.twse.com.tw/server-java/t05st10_ifrs?step=1&TYPEK=sii&year={minguo_year}&month={month:02d}&firstin=1"
    try:
        resp = requests.get(url, timeout=20, verify=False)
        resp.encoding = "utf-8"
        content = resp.content.decode("utf-8", errors="ignore")
        # 嘗試自動偵測資料起始行
        lines = content.splitlines()
        header_idx = None
        for idx, line in enumerate(lines):
            if "公司代號" in line and "普通股股數" in line:
                header_idx = idx
                break
        if header_idx is not None:
            df = pd.read_csv(pd.compat.StringIO("\n".join(lines[header_idx:])), encoding="utf-8")
            df.to_csv(cache_path, index=False, encoding="utf-8")
            return df
    except Exception as e:
        print(f"[data_fetching] 無法下載或解析股本異動表: {url}，錯誤: {e}")
    return None

def get_shares_outstanding_from_twse_csv(stock_code: str, report_date: str):
    """
    依據財報期末日期，自動下載/解析對應期數的股本異動表，回傳該股票的流通在外股數（int），找不到則回傳 None。
    :param stock_code: 股票代號
    :param report_date: 財報期末日期（YYYY-MM-DD）
    :return: 流通在外股數（int）或 None
    """
    try:
        dt = pd.to_datetime(report_date)
        df = download_twse_capital_change_csv(dt)
        if df is not None:
            # 嘗試標準化欄位
            code_col = [col for col in df.columns if "公司代號" in col][0]
            shares_col = [col for col in df.columns if "普通股股數" in col or "流通在外" in col][0]
            row = df[df[code_col].astype(str) == str(stock_code)]
            if not row.empty:
                so_str = str(row.iloc[0][shares_col]).replace(",", "")
                so = int(float(so_str))
                return so
    except Exception as e:
        print(f"[data_fetching] 解析股本異動表失敗: {e}")
    return None
