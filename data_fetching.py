import requests
import pandas as pd
import os
from dotenv import load_dotenv

# 載入環境變數（API金鑰）
load_dotenv()

class YongFengAPI:
    """永豐API客戶端"""
    def __init__(self):
        self.base_url = "https://api.yongfeng.com.tw/v1"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('YONGFENG_API_KEY')}",
            "Content-Type": "application/json"
        }
    
    def get_industries(self):
        """取得台股產業清單"""
        try:
            response = requests.get(f"{self.base_url}/industries", headers=self.headers)
            response.raise_for_status()
            return pd.DataFrame(response.json()['data'])
        except Exception as e:
            print(f"永豐API產業清單取得失敗: {e}")
            return self._fallback_industries()

    def get_industry_stocks(self, industry_code):
        """取得特定產業成分股"""
        try:
            response = requests.get(f"{self.base_url}/industries/{industry_code}/stocks", headers=self.headers)
            response.raise_for_status()
            return pd.DataFrame(response.json()['data'])
        except Exception as e:
            print(f"永豐API成分股取得失敗: {e}")
            return self._fallback_industry_stocks(industry_code)

    def get_stock_data(self, stock_codes):
        """取得多檔股票資料（現價/EPS/成長率）"""
        try:
            response = requests.post(
                f"{self.base_url}/stocks/batch",
                headers=self.headers,
                json={"symbols": stock_codes}
            )
            response.raise_for_status()
            
            data = response.json()['data']
            return pd.DataFrame([
                {
                    'symbol': item['symbol'],
                    'price': item['price'],
                    'eps': item['eps'],
                    'growth_rate': item['growthRate']
                } for item in data
            ])
        except Exception as e:
            print(f"永豐API股票資料取得失敗: {e}")
            return self._fallback_stock_data(stock_codes)

    def _fallback_industries(self):
        """公開資料備援（示範資料）"""
        return pd.DataFrame({
            'code': ['1101', '1102', '1103'],
            'name': ['電子業', '金融業', '傳產業']
        })

    def _fallback_industry_stocks(self, industry_code):
        """公開資料備援（示範資料）"""
        sample_stocks = {
            '1101': [{'symbol': '2330', 'industry_code': '1101'}, 
                     {'symbol': '2412', 'industry_code': '1101'}, 
                     {'symbol': '2416', 'industry_code': '1101'}],
            '1102': [{'symbol': '2880', 'industry_code': '1102'}, 
                     {'symbol': '2881', 'industry_code': '1102'}, 
                     {'symbol': '2882', 'industry_code': '1102'}],
            '1103': [{'symbol': '1101', 'industry_code': '1103'}, 
                     {'symbol': '1102', 'industry_code': '1103'}, 
                     {'symbol': '1103', 'industry_code': '1103'}]
        }
        return pd.DataFrame(sample_stocks.get(industry_code, []))

    def _fallback_stock_data(self, stock_codes):
        """公開資料備援（示範資料）"""
        return pd.DataFrame({
            'symbol': stock_codes,
            'price': [500, 300, 200],
            'eps': [50, 30, 20],
            'growth_rate': [0.15, 0.10, 0.08],
            'industry_code': ['1101', '1101', '1101']
        })


def fetch_industry_data():
    """完整產業資料取得流程"""
    api = YongFengAPI()
    
    # 1. 取得產業清單
    industries = api.get_industries()
    
    # 2. 選擇電子產業 (code: 1101) 進行示範
    selected_industry = industries.iloc[0]
    stocks = api.get_industry_stocks(selected_industry['code'])
    # 確保 stocks 有 industry_code 欄位
    if 'industry_code' not in stocks.columns:
        stocks['industry_code'] = selected_industry['code']
    # 3. 取得成分股資料
    stock_data = api.get_stock_data(stocks['symbol'].tolist())
    # 確保 stock_data 有 industry_code 欄位
    if 'industry_code' not in stock_data.columns:
        stock_data['industry_code'] = selected_industry['code']
    # 4. 合併資料
    result = pd.merge(stocks, stock_data, on=['symbol', 'industry_code'])
    result = pd.merge(result, industries, left_on='industry_code', right_on='code')
    return result[['symbol', 'price', 'eps', 'growth_rate', 'name']]


if __name__ == "__main__":
    # 測試程式
    data = fetch_industry_data()
    print("取得的產業資料：")
    print(data)
    print(f"\n總共取得 {len(data)} 檔股票資料")
