"""
JoJoTrading 用戶介面模組

包含Streamlit應用和相關UI組件：
- 主應用程式狀態機驅動器
"""

try:
    from .app import drive_state_machine
    __all__ = [
        "drive_state_machine",
    ]
except ImportError as e:
    # 如果導入失敗，記錄錯誤但不中斷
    import warnings
    warnings.warn(f"UI模組導入警告: {e}", ImportWarning)
    __all__ = []
