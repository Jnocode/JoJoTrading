# 測試 XBRL ETL 流程：直接解析已解壓的 2025Q1 XBRL
import os
from modules.xbrl_etl import parse_xbrl_folder
import pandas as pd
import logging

# 設定日誌記錄
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def test_parse_xbrl_folder_2025q1():
    # 直接解析已解壓的 2025Q1 XBRL
    xbrl_folder = "cache/xbrl_unzip/2025Q1"
    logging.info(f"=== 開始測試解析 {xbrl_folder} ===")
    
    assert os.path.exists(xbrl_folder), f"錯誤：XBRL 資料夾 {xbrl_folder} 不存在。"
    
    if not os.listdir(xbrl_folder):
        logging.warning(f"警告：XBRL 資料夾 {xbrl_folder} 為空。測試可能無法驗證完整功能。")
        # 即使資料夾為空，也應該能正常執行 parse_xbrl_folder 並回傳空 DataFrame 或 None
        df = parse_xbrl_folder(xbrl_folder)
        if df is not None:
            assert df.empty, "對於空資料夾，預期回傳空的 DataFrame。"
        else:
            # 根據 parse_xbrl_folder 的設計，如果資料夾為空，它可能會回傳 None 或空 DataFrame
            logging.info("parse_xbrl_folder 對於空資料夾回傳 None，符合預期。")
        return # 空資料夾測試結束

    logging.info(f"在資料夾 {xbrl_folder} 中找到 {len(os.listdir(xbrl_folder))} 個檔案。")
    
    df = parse_xbrl_folder(xbrl_folder)
    
    assert df is not None, "parse_xbrl_folder 不應回傳 None 當資料夾存在且非空。"
    assert not df.empty, "對於非空資料夾，預期回傳非空的 DataFrame。"

    logging.info(f"DataFrame shape: {df.shape}")
    logging.info(f"欄位名稱: {list(df.columns)}")
    logging.info("前 5 筆資料:")
    logging.info(df.head())

    # 驗證特定公司（如台積電 2330）資料
    tsmc_stock_id = "2330"
    tsmc_rows = df[df["source_file"].str.contains(f"-{tsmc_stock_id}-")]
    
    if not tsmc_rows.empty:
        logging.info(f"台積電 ({tsmc_stock_id}) 財報資料：")
        logging.info(tsmc_rows)
    else:
        logging.warning(f"在解析結果中找不到台積電 ({tsmc_stock_id}) 的資料。")
        files_containing_stock_id = [f for f in df["source_file"].unique() if f"-{tsmc_stock_id}-" in f]
        if files_containing_stock_id:
            logging.info(f"找到以下包含 '{tsmc_stock_id}' 的檔案名稱：{files_containing_stock_id}")
        else:
            logging.warning(f"在 source_file 中也未找到包含 '-{tsmc_stock_id}-' 的檔案。")
    
    logging.info(f"=== 測試解析 {xbrl_folder} 完成 ===")

if __name__ == "__main__":
    # 若要手動執行此測試腳本，可以取消以下註解
    # test_parse_xbrl_folder_2025q1()
    # print("手動執行測試完成。")
    pass
