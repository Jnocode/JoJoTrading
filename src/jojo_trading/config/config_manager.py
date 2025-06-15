"""
Configuration Management Module
配置管理模組 - 集中管理應用程式配置
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class DCFConfig:
    """DCF計算配置"""
    default_discount_rate: float = 0.08
    default_growth_rate: float = 0.08
    default_terminal_growth: float = 0.03
    default_projection_years: int = 5
    min_discount_rate: float = 0.05
    max_discount_rate: float = 0.15
    min_growth_rate: float = -0.10
    max_growth_rate: float = 0.30


@dataclass
class ScreeningConfig:
    """篩選配置"""
    default_risk_preference: float = 0.08
    default_return_threshold: float = 0.15
    min_return_threshold: float = 0.05
    max_return_threshold: float = 0.50
    default_revenue_cagr_threshold: float = 10.0
    default_eps_cagr_threshold: float = 15.0
    default_roe_threshold: float = 15.0


@dataclass
class UIConfig:
    """UI配置"""
    page_title: str = "JoJo Trading DCF分析系統"
    page_icon: str = "📊"
    layout: str = "wide"
    sidebar_state: str = "expanded"


@dataclass
class AppConfig:
    """應用程式總配置"""
    dcf: DCFConfig
    screening: ScreeningConfig
    ui: UIConfig
    debug_mode: bool = False
    cache_enabled: bool = True
    log_level: str = "INFO"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路徑，預設為 None（使用默認路徑）
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[AppConfig] = None
        self.load_config()
    
    def _get_default_config_path(self) -> str:
        """獲取默認配置文件路徑"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(os.path.dirname(current_dir), 'config')
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'app_config.json')
    
    def load_config(self) -> AppConfig:
        """載入配置
        
        Returns:
            AppConfig: 應用程式配置
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                
                # 將字典轉換為配置物件
                self._config = AppConfig(
                    dcf=DCFConfig(**config_dict.get('dcf', {})),
                    screening=ScreeningConfig(**config_dict.get('screening', {})),
                    ui=UIConfig(**config_dict.get('ui', {})),
                    debug_mode=config_dict.get('debug_mode', False),
                    cache_enabled=config_dict.get('cache_enabled', True),
                    log_level=config_dict.get('log_level', 'INFO')
                )
            except Exception as e:
                print(f"載入配置失敗: {e}，使用默認配置")
                self._config = self._create_default_config()
        else:
            self._config = self._create_default_config()
            self.save_config()
        
        return self._config
    
    def _create_default_config(self) -> AppConfig:
        """創建默認配置
        
        Returns:
            AppConfig: 默認配置
        """
        return AppConfig(
            dcf=DCFConfig(),
            screening=ScreeningConfig(),
            ui=UIConfig()
        )
    
    def save_config(self) -> None:
        """保存配置"""
        if self._config is None:
            return
        
        try:
            # 確保配置目錄存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # 將配置對象轉換為字典
            config_dict = {
                'dcf': asdict(self._config.dcf),
                'screening': asdict(self._config.screening),
                'ui': asdict(self._config.ui),
                'debug_mode': self._config.debug_mode,
                'cache_enabled': self._config.cache_enabled,
                'log_level': self._config.log_level
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存配置失敗: {e}")
    
    @property
    def config(self) -> AppConfig:
        """獲取配置物件"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def get_dcf_defaults(self) -> Dict[str, Any]:
        """獲取DCF默認值
        
        Returns:
            Dict[str, Any]: DCF默認參數
        """
        dcf_config = self.config.dcf
        return {
            'discount_rate': dcf_config.default_discount_rate * 100,  # 轉換為百分比
            'growth_rate': dcf_config.default_growth_rate * 100,
            'terminal_growth': dcf_config.default_terminal_growth * 100,
            'projection_years': dcf_config.default_projection_years
        }
    
    def get_screening_defaults(self) -> Dict[str, Any]:
        """獲取篩選默認值
        
        Returns:
            Dict[str, Any]: 篩選默認參數
        """
        screening_config = self.config.screening
        return {
            'risk_preference': screening_config.default_risk_preference * 100,
            'return_threshold': screening_config.default_return_threshold * 100,
            'revenue_cagr_threshold': screening_config.default_revenue_cagr_threshold,
            'eps_cagr_threshold': screening_config.default_eps_cagr_threshold,
            'roe_threshold': screening_config.default_roe_threshold
        }
    
    def get_ui_config(self) -> Dict[str, str]:
        """獲取UI配置
        
        Returns:
            Dict[str, str]: UI配置參數
        """
        ui_config = self.config.ui
        return {
            'page_title': ui_config.page_title,
            'page_icon': ui_config.page_icon,
            'layout': ui_config.layout,
            'sidebar_state': ui_config.sidebar_state        }
    
    def update_dcf_config(self, **kwargs) -> None:
        """更新DCF配置
        
        Args:
            **kwargs: DCF配置參數
        """
        if self._config is None:
            self.load_config()
          # 確保配置已載入
        if self._config is not None:
            for key, value in kwargs.items():
                if hasattr(self._config.dcf, key):
                    setattr(self._config.dcf, key, value)
            self.save_config()
    
    def update_screening_config(self, **kwargs) -> None:
        """更新篩選配置
        
        Args:
            **kwargs: 篩選配置參數
        """
        if self._config is None:
            self.load_config()
          # 確保配置已載入
        if self._config is not None:
            for key, value in kwargs.items():
                if hasattr(self._config.screening, key):
                    setattr(self._config.screening, key, value)
            
            self.save_config()
    
    def update_ui_config(self, **kwargs) -> None:
        """更新UI配置
        
        Args:
            **kwargs: UI配置參數
        """
        if self._config is None:
            self.load_config()
        
        # 確保配置已載入
        if self._config is not None:
            for key, value in kwargs.items():
                if hasattr(self._config.ui, key):
                    setattr(self._config.ui, key, value)
            
            self.save_config()
    
    def reset_to_defaults(self) -> None:
        """重置為默認配置"""
        self._config = self._create_default_config()
        self.save_config()
    
    def is_debug_mode(self) -> bool:
        """檢查是否為調試模式
        
        Returns:
            bool: 是否為調試模式
        """
        return self.config.debug_mode
    
    def is_cache_enabled(self) -> bool:
        """檢查是否啟用快取
        
        Returns:
            bool: 是否啟用快取
        """
        return self.config.cache_enabled


# 全局配置管理器實例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """獲取全局配置管理器實例
    
    Returns:
        ConfigManager: 配置管理器實例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_app_config() -> AppConfig:
    """快捷方式：獲取應用程式配置
    
    Returns:
        AppConfig: 應用程式配置
    """
    return get_config_manager().config
