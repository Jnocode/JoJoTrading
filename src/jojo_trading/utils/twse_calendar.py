
import datetime

class TWSECalendar:
    """
    Gestion of Taiwan Stock Exchange (TWSE) Trading Days.
    Includes logic for Weekends and National Holidays.
    
    Data Source: 2026 (Republic of China Year 115) Calendar
    """
    
    # 2026 Estimated Holidays (User should update this based on official announce)
    # Format: "YYYY-MM-DD"
    HOLIDAYS_2026 = {
        "2026-01-01", # New Year (元旦)
        
        # Lunar New Year (Estimated: Feb 17 is CNY)
        # Usually off from shortly before to shortly after. 
        # Let's mark the likely heavy closure period.
        "2026-02-13", "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20", 
        
        "2026-02-27", # Peace Day Bridge? (2/28 is Sat)
        
        "2026-04-03", # Children's Day / Tomb Sweeping (Observed)
        "2026-04-06", # Tomb Sweeping (Observed)
        
        "2026-05-01", # Labor Day (勞動節)
        
        "2026-06-19", # Dragon Boat (Estimated)
        
        "2026-09-25", # Moon Festival (Estimated)
        
        "2026-10-09", # Double Tenth (Bridge)
    }

    @staticmethod
    def is_holiday(date_obj: datetime.date) -> bool:
        """Check if a specific date is a holiday"""
        date_str = date_obj.strftime("%Y-%m-%d")
        return date_str in TWSECalendar.HOLIDAYS_2026

    @staticmethod
    def is_trading_day(date_obj: datetime.date) -> bool:
        """
        Check if market is open (Not Weekend AND Not Holiday)
        Note: Does not cover 'Makeup Saturdays' (補班日獨家開市), 
        but usually stock market is closed on makeup Saturdays in recent years.
        """
        # 1. Check Weekend (Sat=5, Sun=6)
        if date_obj.weekday() >= 5:
            return False
            
        # 2. Check Holiday
        if TWSECalendar.is_holiday(date_obj):
            return False
            
        return True
