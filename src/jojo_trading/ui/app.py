"""
JoJo Trading DCF Analysis Application - Refactored
重構後的 JoJo Trading DCF 分析應用程式

這是基於 DCF 估值模型的台股篩選系統的主要使用者介面，
採用模組化設計提供乾淨、可維護的代碼結構。

系統架構：
- 配置管理模組 (config)
- UI 組件模組 (components)
- 核心業務邏輯 (core)
- 響應式 Web 介面設計

主要功能模組：
1. 增強版個股DCF分析 (EnhancedIndividualDCFComponent) - 自動抓取財報數據
2. 類股篩選DCF (SectorScreeningComponent)
3. 配置管理 (ConfigManager)
4. 通用UI組件 (CommonWidgets)

技術特色：
- 模組化設計確保代碼可維護性
- 配置集中管理
- 組件化UI設計
- 清晰的關注點分離
"""

import streamlit as st
import sys
import os

# 確保能夠導入模組
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_dir = os.path.join(project_root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 導入配置管理
from jojo_trading.config import get_config_manager

# 導入UI組件
from jojo_trading.ui.components import (
    EnhancedIndividualDCFComponent,
    SectorScreeningComponent,
    CommonWidgets
)


class JoJoTradingApp:
    """JoJo Trading DCF 分析應用程式主類"""
    
    def __init__(self):
        """初始化應用程式"""
        self.config_manager = get_config_manager()
        self.individual_dcf = EnhancedIndividualDCFComponent()
        self.sector_screening = SectorScreeningComponent()
        self.common_widgets = CommonWidgets()
        
        # 跳過頁面配置設置（由主應用程式處理）
        # self._setup_page_config()
    
    def render_header(self) -> None:
        """渲染頁面標題"""
        self.common_widgets.render_page_header(
            title="📊 DCF 估值分析系統",
            description="**D**iscounted **C**ash **F**low 現金流折現模型股票估值工具"
        )
    
    def render_navigation_tabs(self) -> None:
        """渲染導航標籤"""
        tab1, tab2 = st.tabs(["📈 個股DCF分析", "🎯 類股篩選DCF"])
        
        with tab1:
            self.render_individual_dcf_analysis()
        
        with tab2:
            self.render_sector_dcf_screening()
    
    def render_individual_dcf_analysis(self) -> None:
        """渲染個股DCF分析頁面"""
        try:
            self.individual_dcf.render()
        except Exception as e:
            self.common_widgets.render_error_message(
                error=f"個股DCF分析模組載入失敗: {str(e)}",
                show_details=self.config_manager.is_debug_mode()
            )
    
    def render_sector_dcf_screening(self) -> None:
        """渲染類股篩選DCF分析頁面"""
        try:
            self.sector_screening.render()
        except Exception as e:
            self.common_widgets.render_error_message(
                error=f"類股篩選DCF模組載入失敗: {str(e)}",
                show_details=self.config_manager.is_debug_mode()
            )
    
    def render_debug_info(self) -> None:
        """渲染調試信息（僅在調試模式下顯示）"""
        if self.config_manager.is_debug_mode():
            with st.sidebar:
                st.markdown("---")
                st.markdown("### 🔧 調試信息")
                
                # 顯示配置信息
                with st.expander("配置信息"):
                    st.json({
                        "DCF配置": self.config_manager.get_dcf_defaults(),
                        "篩選配置": self.config_manager.get_screening_defaults(),
                        "UI配置": self.config_manager.get_ui_config()
                    })
                
                # 顯示會話狀態
                with st.expander("會話狀態"):
                    st.json(dict(st.session_state))
    
    def render_footer(self) -> None:
        """渲染頁腳"""
        self.common_widgets.render_disclaimer()
    
    def run(self) -> None:
        """運行應用程式"""
        try:
            # 渲染主要內容
            self.render_header()
            self.render_navigation_tabs()
            self.render_debug_info()
            self.render_footer()
            
        except Exception as e:
            st.error(f"應用程式運行時發生錯誤: {str(e)}")
            if self.config_manager.is_debug_mode():
                import traceback
                st.code(traceback.format_exc())


def main():
    """
    主要執行函數，啟動 DCF 估值分析系統
    
    這是重構後的主函數，使用模組化設計：
    - 配置管理集中化
    - UI組件模組化  
    - 錯誤處理完善
    - 調試支持
    """
    try:
        # 創建並運行應用程式
        app = JoJoTradingApp()
        app.run()
        
    except Exception as e:
        st.error(f"應用程式初始化失敗: {str(e)}")
        st.markdown("""
        ### 故障排除建議：
        1. 檢查所有相依模組是否正確安裝
        2. 確認 Python 路徑設定正確
        3. 檢查配置文件是否存在問題
        4. 查看錯誤詳情並聯繫技術支援
        """)
        
        # 顯示詳細錯誤（調試模式）
        with st.expander("🔍 詳細錯誤信息"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()