# JoJoTrading 優化後DCF配置
# 基於診斷結果的最佳配置: 調整後預設配置

DCF_OPTIMIZED_CONFIG = {
    # DCF 計算參數
    'dcf_short_term_growth_rate': 0.1,
    'dcf_terminal_growth_rate': 0.035,
    'risk_preference': 0.07,
    'dcf_projection_years': 5,
    
    # 計算方法設定
    'calculation_method': 'enhanced',
    'enable_anomaly_detection': True,
    'anomaly_threshold': 1.2,
    
    # 篩選參數
    'screening_threshold': 0.15,
    
    # FCF 計算優化
    'fcf_optimization': {
        'maintenance_capex_ratio': 0.6,      # 重資產股票的維持性資本支出比例
        'working_capital_limit': 0.3,        # 營運資金變化限制（佔淨利比例）
        'heavy_asset_threshold': 0.15,       # 重資產判定閾值（資本支出佔營收比例）
        'min_fcf_eps_threshold': -50          # FCF_EPS最低限制
    }
}

# 使用說明
USAGE_INSTRUCTIONS = """
使用方法:
1. 在 app.py 中導入: from dcf_optimized_config import DCF_OPTIMIZED_CONFIG
2. 將配置應用於DCF計算: calculate_dcf_valuation(..., context=DCF_OPTIMIZED_CONFIG)
3. 根據實際表現進一步調整參數
"""
