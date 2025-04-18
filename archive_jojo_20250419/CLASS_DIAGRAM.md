# JoJoTrading 類圖（Mermaid 語法）

> 本類圖涵蓋主架構、核心類別、主要 App 與 GUI 關聯，適合貼到 markdown 或用 mermaid.live/PlantUML 轉圖。

```mermaid
classDiagram
    %% Core Engine
    class MainEngine {
        +apps: Dict
        +gateways: Dict
        +add_app()
        +start_app()
        +get_app()
        +add_gateway()
        +connect()
        +write_log()
    }
    class BaseApp {
        <<abstract>>
        +start()
        +stop()
        +close()
    }
    class EventEngine {
        +register()
        +unregister()
        +put()
        +start()
    }

    %% Gateway
    class ShioajiGateway
    class SimulationGateway
    class ApiGateway

    %% App Modules
    class MarketDataApp {
        +ticks: Dict
        +process_event()
        +get_tick()
    }
    class LeftValueZoneApp
    class StockFilterApp {
        +stocks: Dict
        +categories: Dict
        +filters: Dict
        +get_filtered_stocks()
    }

    %% GUI
    class TradingWindow {
        +main_engine: MainEngine
        +event_engine: EventEngine
        +sidebar_widget
        +content_widget
    }
    class MarketDataPanel
    class LeftValueZoneGUI
    class StockListPanel
    class StockFilterPanel

    %% 關聯/繼承
    MainEngine "1" o-- "*" BaseApp : apps
    MainEngine "1" o-- "*" ShioajiGateway : gateways
    MainEngine "1" o-- "*" SimulationGateway
    MainEngine "1" o-- "*" ApiGateway

    BaseApp <|-- MarketDataApp
    BaseApp <|-- LeftValueZoneApp
    BaseApp <|-- StockFilterApp

    TradingWindow "1" *-- "1" MainEngine
    TradingWindow "1" *-- "1" EventEngine
    TradingWindow o-- MarketDataPanel
    TradingWindow o-- LeftValueZoneGUI
    TradingWindow o-- StockListPanel
    TradingWindow o-- StockFilterPanel

    %% App 與 GUI 面板對應
    MarketDataApp .. MarketDataPanel
    LeftValueZoneApp .. LeftValueZoneGUI
    StockFilterApp .. StockFilterPanel

    %% 其他
    note for MainEngine "管理所有 App、Gateway，負責事件分發與資源協調"
    note for BaseApp "所有功能模組的抽象基底"
    note for TradingWindow "PyQt6 主視窗，負責組合與切換各功能面板"
```

---

## 使用說明
- 可直接貼到 [mermaid.live](https://mermaid.live/) 產生圖形。
- 若需 PlantUML 版本或更細節的類圖，請告知。
- 可依需求擴充欄位、方法、模組。

---
