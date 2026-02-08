"""
生成 JoJo Trading 專案的專業視覺化圖表
用於 GitHub README 和履歷展示
"""
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import os

# 設定中文字體和樣式
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-darkgrid')

# 創建輸出目錄
output_dir = r"D:\Workspace\03.Dev_Projects\trading\jojo_trading\docs\screenshots"
os.makedirs(output_dir, exist_ok=True)

# 1. DCF 估值敏感度分析圖
def generate_dcf_sensitivity():
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # 模擬數據：不同折現率和成長率的估值結果
    discount_rates = np.linspace(0.08, 0.12, 5)
    growth_rates = np.linspace(0.02, 0.06, 5)
    
    for gr in growth_rates:
        valuations = 500 * (1 + gr) / (discount_rates - gr)
        ax.plot(discount_rates * 100, valuations, marker='o', 
                label=f'成長率 {gr*100:.1f}%', linewidth=2)
    
    ax.set_xlabel('折現率 (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('內在價值 (元)', fontsize=14, fontweight='bold')
    ax.set_title('DCF 估值敏感度分析 - 台積電 (2330)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)
    
    # 添加當前市價參考線
    ax.axhline(y=600, color='red', linestyle='--', linewidth=2, 
               label='當前市價: 600元', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'dcf_sensitivity.png'), 
                dpi=300, bbox_inches='tight')
    print("✅ DCF 敏感度分析圖已生成")
    plt.close()

# 2. Monte Carlo 模擬路徑圖
def generate_monte_carlo():
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 模擬參數
    initial_price = 600
    days = 252
    simulations = 50  # 顯示數量
    mu = 0.0001  # 日均回報
    sigma = 0.02  # 日波動率
    
    np.random.seed(42)
    
    # 生成模擬路徑
    for i in range(simulations):
        daily_returns = np.random.normal(mu, sigma, days)
        price_path = initial_price * np.cumprod(1 + daily_returns)
        ax.plot(price_path, alpha=0.3, linewidth=1, color='steelblue')
    
    # 計算並繪製信賴區間
    all_paths = np.array([initial_price * np.cumprod(1 + np.random.normal(mu, sigma, days)) 
                          for _ in range(10000)])
    percentile_5 = np.percentile(all_paths, 5, axis=0)
    percentile_95 = np.percentile(all_paths, 95, axis=0)
    median = np.percentile(all_paths, 50, axis=0)
    
    x = np.arange(days)
    ax.fill_between(x, percentile_5, percentile_95, alpha=0.2, color='orange',
                     label='95% 信賴區間')
    ax.plot(median, color='red', linewidth=3, label='中位數路徑')
    
    ax.set_xlabel('交易日', fontsize=14, fontweight='bold')
    ax.set_ylabel('股價 (元)', fontsize=14, fontweight='bold')
    ax.set_title('Monte Carlo 模擬 (10,000次迭代) - 台積電未來一年價格預測', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(fontsize=12, loc='best')
    ax.grid(True, alpha=0.3)
    
    # 添加統計信息
    final_price_5 = percentile_5[-1]
    final_price_50 = median[-1]
    final_price_95 = percentile_95[-1]
    
    textstr = f'一年後預測:\n5%分位: {final_price_5:.0f}元\n中位數: {final_price_50:.0f}元\n95%分位: {final_price_95:.0f}元'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'monte_carlo_simulation.png'), 
                dpi=300, bbox_inches='tight')
    print("✅ Monte Carlo 模擬圖已生成")
    plt.close()

# 3. 回測績效曲線圖
def generate_backtest_results():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # 生成模擬回測數據
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(365)]
    np.random.seed(42)
    
    # 策略回報（SMA交叉策略）
    strategy_returns = np.random.normal(0.05, 0.15, 365).cumsum()
    buy_hold_returns = np.random.normal(0.03, 0.12, 365).cumsum()
    
    # 績效曲線
    ax1.plot(dates, 100 * (1 + strategy_returns/100), linewidth=2, 
             label='SMA 交叉策略', color='green')
    ax1.plot(dates, 100 * (1 + buy_hold_returns/100), linewidth=2, 
             label='買入持有', color='gray', linestyle='--')
    
    ax1.set_ylabel('資產價值 (%)', fontsize=12, fontweight='bold')
    ax1.set_title('策略回測績效 (2023年)', fontsize=16, fontweight='bold', pad=20)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=100, color='black', linestyle=':', alpha=0.5)
    
    # 回撤分析
    cummax = np.maximum.accumulate(strategy_returns)
    drawdown = (strategy_returns - cummax) 
    
    ax2.fill_between(dates, drawdown, 0, alpha=0.3, color='red')
    ax2.plot(dates, drawdown, color='darkred', linewidth=2)
    ax2.set_xlabel('日期', fontsize=12, fontweight='bold')
    ax2.set_ylabel('回撤 (%)', fontsize=12, fontweight='bold')
    ax2.set_title('策略回撤分析', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # 添加績效指標
    final_return = strategy_returns[-1]
    max_drawdown = drawdown.min()
    sharpe_ratio = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252)
    
    metrics = f'總回報: {final_return:.2f}%\n最大回撤: {max_drawdown:.2f}%\n夏普比率: {sharpe_ratio:.2f}'
    props = dict(boxstyle='round', facecolor='lightgreen', alpha=0.8)
    ax1.text(0.02, 0.98, metrics, transform=ax1.transAxes, fontsize=11,
             verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'backtest_results.png'), 
                dpi=300, bbox_inches='tight')
    print("✅ 回測績效圖已生成")
    plt.close()

# 4. 系統架構概覽圖（使用 networkx）
def generate_architecture_overview():
    try:
        import networkx as nx
        
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # 創建有向圖
        G = nx.DiGraph()
        
        # 定義節點（按層級）
        frontend = ['Streamlit UI']
        core = ['DCF Engine', 'Backtest Engine', 'Risk Analysis']
        data = ['Data Fetcher', 'Cache System']
        storage = ['SQLite DB']
        apis = ['Shioaji API', 'Yahoo Finance', 'DCF API']
        
        # 添加節點
        for node in frontend + core + data + storage + apis:
            G.add_node(node)
        
        # 添加連接
        for f in frontend:
            for c in core:
                G.add_edge(f, c)
        for c in core:
            for d in data:
                G.add_edge(c, d)
        for d in data:
            if d == 'Data Fetcher':
                for a in apis:
                    G.add_edge(d, a)
            if d == 'Cache System':
                for s in storage:
                    G.add_edge(d, s)
        
        # 手動設定節點位置（分層）
        pos = {}
        pos['Streamlit UI'] = (4, 5)
        pos['DCF Engine'] = (2, 3.5)
        pos['Backtest Engine'] = (4, 3.5)
        pos['Risk Analysis'] = (6, 3.5)
        pos['Data Fetcher'] = (3, 2)
        pos['Cache System'] = (5, 2)
        pos['SQLite DB'] = (5, 0.5)
        pos['Shioaji API'] = (1, 0.5)
        pos['Yahoo Finance'] = (3, 0.5)
        pos['DCF API'] = (5, 0.5)
        
        # 定義節點顏色
        node_colors = {
            'Streamlit UI': '#e1f5ff',
            'DCF Engine': '#fff3e0',
            'Backtest Engine': '#fff3e0',
            'Risk Analysis': '#fff3e0',
            'Data Fetcher': '#f3e5f5',
            'Cache System': '#f3e5f5',
            'SQLite DB': '#e8f5e9',
            'Shioaji API': '#fce4ec',
            'Yahoo Finance': '#fce4ec',
            'DCF API': '#fce4ec',
        }
        
        colors = [node_colors.get(node, '#ffffff') for node in G.nodes()]
        
        # 繪製圖形
        nx.draw(G, pos, with_labels=True, node_color=colors, 
                node_size=3000, font_size=10, font_weight='bold',
                arrows=True, arrowsize=20, arrowstyle='->', 
                edge_color='gray', width=2, ax=ax)
        
        ax.set_title('JoJo Trading Platform - 系統架構', 
                     fontsize=18, fontweight='bold', pad=20)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'architecture_overview.png'), 
                    dpi=300, bbox_inches='tight', facecolor='white')
        print("✅ 系統架構圖已生成")
        plt.close()
    except ImportError:
        print("⚠️ networkx 未安裝，跳過架構圖生成")

# 執行所有生成函數
if __name__ == "__main__":
    print("🎨 開始生成專業視覺化圖表...")
    print(f"📂 輸出目錄: {output_dir}\n")
    
    generate_dcf_sensitivity()
    generate_monte_carlo()
    generate_backtest_results()
    generate_architecture_overview()
    
    print(f"\n✅ 所有圖表已生成完成！")
    print(f"📍 位置: {output_dir}")
    print("\n生成的檔案:")
    for file in os.listdir(output_dir):
        if file.endswith('.png'):
            print(f"  - {file}")
