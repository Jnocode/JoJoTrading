# JoJoTrading (Streamlit Version) - Architecture Diagram

## 1. Class and Module Diagram

```mermaid
classDiagram
    direction LR

    package "jojo_state_machine.py" {
        class JoJoState {
            <<enumeration>>
            CONFIG_LOAD
            UI_INIT
            INDUSTRY_PROCESS
            DATA_FETCH
            VALUATION
            FILTERING
            RESULTS_DISPLAY
            EXPORT
            ERROR
            END
        }

        class BaseState {
            <<Abstract>>
            +execute(context) JoJoState
            +on_enter(context) void
            +on_exit(context) void
        }

        class ConfigLoadState
        class UiInitState
        class IndustryProcessState
        class DataFetchState
        class ValuationState
        class FilteringState
        class ResultsDisplayState
        class ExportState
        class ErrorState
        class EndState

        ConfigLoadState --|> BaseState
        UiInitState --|> BaseState
        IndustryProcessState --|> BaseState
        DataFetchState --|> BaseState
        ValuationState --|> BaseState
        FilteringState --|> BaseState
        ResultsDisplayState --|> BaseState
        ExportState --|> BaseState
        ErrorState --|> BaseState
        EndState --|> BaseState

        class JoJoStateMachine {
            -current_jojo_state_enum JoJoState
            -context dict
            -states dict~JoJoState, BaseState~
            +run() void
            +__init__() void
        }
        JoJoStateMachine o-- JoJoState : "current state"
        JoJoStateMachine *-- BaseState : "manages state objects"
    }

    package "app.py" {
        class StreamlitApp {
            <<Streamlit Script>>
            -machine JoJoStateMachine
            +render_ui()
            +handle_user_interaction()
        }
    }
    StreamlitApp ..> JoJoStateMachine : creates & drives

    package "data_handler.py" {
        class DataHandlerModule {
            <<Module>>
            +get_all_companies_basic_data(context) list
            +filter_industry_stocks(selected_industry_name, name_to_code_map, all_companies_data) list
            +get_financial_reports_for_stock(stock_detail, context) tuple
            +fetch_stock_financials_from_downloaded(stock_code, api_suffix, downloaded_reports) dict
            +calculate_dcf_valuation(stock_code, financials, risk_preference, context) dict
        }
    }
    DataFetchState ..> DataHandlerModule : uses functions from
    ValuationState ..> DataHandlerModule : uses functions from
    ConfigLoadState ..> DataHandlerModule : (implicitly, for industries.json)


    package "Configuration" {
        class industries_json {
            <<JSON File>>
            industries: list
            default_risk_premium: float
            risk_premium_options: dict
        }
        class env_file {
            <<.env File>>
            API_KEY_XXX (example)
        }
    }
    ConfigLoadState ..> industries_json : reads
    ConfigLoadState ..> env_file : reads (via dotenv)
    
    note for DataHandlerModule "Contains functions for API interaction and data processing."
    note for StreamlitApp "Main Streamlit application script that orchestrates UI and state machine."
```

## 2. Data Flow / Interaction Overview (Sequence Diagram)

```mermaid
sequenceDiagram
    participant User
    participant StreamlitApp as UI (app.py)
    participant JoJoStateMachine as State Machine
    participant ConfigLoadState
    participant UiInitState
    participant IndustryProcessState
    participant DataFetchState
    participant DataHandlerModule as Data Handler
    participant ValuationState
    participant FilteringState
    participant ResultsDisplayState
    participant ExportState

    User->>StreamlitApp: Interacts (e.g., selects industry, clicks button)
    StreamlitApp->>JoJoStateMachine: Updates context, drives state transition
    
    JoJoStateMachine->>ConfigLoadState: execute()
    ConfigLoadState->>DataHandlerModule: (reads industries.json, .env)
    DataHandlerModule-->>ConfigLoadState: config data (implicitly via context)
    ConfigLoadState-->>JoJoStateMachine: next_state = UI_INIT
    
    JoJoStateMachine->>UiInitState: execute() (renders UI, waits for input)
    UiInitState-->>JoJoStateMachine: next_state = UI_INIT (or INDUSTRY_PROCESS on button click)

    Note over StreamlitApp, JoJoStateMachine: On "Start Filter" click
    StreamlitApp->>JoJoStateMachine: context.user_clicked_filter_button = True
    JoJoStateMachine->>UiInitState: execute()
    UiInitState-->>JoJoStateMachine: next_state = INDUSTRY_PROCESS
    
    JoJoStateMachine->>IndustryProcessState: execute()
    IndustryProcessState-->>JoJoStateMachine: next_state = DATA_FETCH
    
    JoJoStateMachine->>DataFetchState: execute()
    DataFetchState->>DataHandlerModule: get_all_companies_basic_data()
    DataHandlerModule-->>DataFetchState: all_companies_data
    DataFetchState->>DataHandlerModule: filter_industry_stocks()
    DataHandlerModule-->>DataFetchState: industry_stocks_details
    loop For each stock_detail in industry_stocks_details
        DataFetchState->>DataHandlerModule: get_financial_reports_for_stock(stock_detail)
        DataHandlerModule-->>DataFetchState: (downloaded_reports, api_suffix)
        DataFetchState->>DataHandlerModule: fetch_stock_financials_from_downloaded(code, suffix, reports)
        DataHandlerModule-->>DataFetchState: financials_for_stock
    end
    DataFetchState-->>JoJoStateMachine: next_state = VALUATION
    
    JoJoStateMachine->>ValuationState: execute()
    loop For each stock with financials
        ValuationState->>DataHandlerModule: calculate_dcf_valuation(stock, financials, risk, context)
        DataHandlerModule-->>ValuationState: valuation_result
    end
    ValuationState-->>JoJoStateMachine: next_state = FILTERING
    
    JoJoStateMachine->>FilteringState: execute() (TODO: implement filtering logic)
    FilteringState-->>JoJoStateMachine: next_state = RESULTS_DISPLAY
    
    JoJoStateMachine->>ResultsDisplayState: execute() (renders results table in UI)
    ResultsDisplayState-->>JoJoStateMachine: next_state = RESULTS_DISPLAY (or EXPORT / UI_INIT on button click)

    Note over StreamlitApp, JoJoStateMachine: On "Export" click
    StreamlitApp->>JoJoStateMachine: context.user_clicked_export_button = True
    JoJoStateMachine->>ResultsDisplayState: execute()
    ResultsDisplayState-->>JoJoStateMachine: next_state = EXPORT

    JoJoStateMachine->>ExportState: execute() (TODO: implement export logic)
    ExportState-->>JoJoStateMachine: next_state = RESULTS_DISPLAY
```

This updated diagram attempts to show the main Python files/modules (`jojo_state_machine.py`, `app.py`, `data_handler.py`) as packages containing their respective classes or representing a collection of functions. It also includes configuration files.
