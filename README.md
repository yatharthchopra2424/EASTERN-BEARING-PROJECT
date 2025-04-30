# EASTERN BEARING PROJECT
 A SOLUTION TO THE PROBLEM SPECIFIED BY ARB BEARING



https://github.com/user-attachments/assets/00b32016-5159-4627-8a74-0683d1c47637


## DIAGRAM 
```mermaid
graph TB
    %% Data Sources
    CSV["User Uploads (CSV)"]:::dataSource
    click CSV "https://github.com/yatharthchopra2424/eastern-bearing-project/tree/main/ERP_DATA_ANALYZER/uploads"

    %% Ingestion Layer
    subgraph "Ingestion Layer"
        FM["file_monitor.py"]:::backend
        DM["data_management.py"]:::backend
    end
    click FM "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/pages/file_monitor.py"
    click DM "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/pages/data_management.py"

    %% Backend Services
    subgraph "Backend Services"
        Cfg["config.py"]:::backend
        Mdl["models.py"]:::backend
        Ut["utilities.py"]:::backend
    end
    click Cfg "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/backend/config.py"
    click Mdl "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/backend/models.py"
    click Ut "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/backend/utilities.py"

    %% Storage Layer
    DB["SQLite Database (grd_db.sqlite)"]:::storage
    LOG["Application Logs (app.log)"]:::storage
    click DB "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/instance/grd_db.sqlite"
    click LOG "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/instance/logs/app.log"

    %% Frontend: Streamlit UI
    subgraph "Streamlit UI"
        App["app.py"]:::frontend
        UIcfg["config.toml"]:::frontend
        Pages["Pages (Overview, OEE, ... Quality_Errors)"]:::frontend
    end
    click App "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/app.py"
    click UIcfg "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/.streamlit/config.toml"
    click Pages "https://github.com/yatharthchopra2424/eastern-bearing-project/tree/main/ERP_DATA_ANALYZER/pages"

    %% Power BI Layer
    subgraph "Power BI Layer"
        PBScr["st.py"]:::frontend
        PBDash["Power BI Dashboard"]:::frontend
        PBreq["requirements.txt"]:::frontend
        PBread["README.md"]:::frontend
    end
    click PBScr "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/DASHBOARD_POWER_BI/st.py"
    click PBreq "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/DASHBOARD_POWER_BI/requirements.txt"
    click PBread "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/DASHBOARD_POWER_BI/README.md"

    %% Dependencies Files
    ERPreq["requirements.txt"]:::backend
    click ERPreq "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/requirements.txt"

    %% Data Flow
    CSV -->|"upload CSV"| FM
    FM -->|"detect files"| DM
    DM -->|"execute ETL"| Ut
    Ut -->|"use ORM"| Mdl
    Mdl -->|"read/write"| DB

    %% Configuration & Logging
    Cfg --> FM
    Cfg --> DM
    Cfg --> Mdl
    Cfg --> Ut
    Cfg --> App
    Cfg --> PBScr
    FM --> LOG
    DM --> LOG
    Ut --> LOG
    Mdl --> LOG
    App --> LOG

    %% UI & Reporting Flows
    DB -->|"query data"| Pages
    Pages -->|"render charts"| App
    DB -->|"export data"| PBScr
    PBScr -->|"generate dataset"| PBDash

    %% Class Definitions
    classDef dataSource fill:#a2fca2,stroke:#333,stroke-width:1px
    classDef backend fill:#bbdefb,stroke:#333,stroke-width:1px
    classDef storage fill:#90caf9,stroke:#333,stroke-width:1px
    classDef frontend fill:#ffcc80,stroke:#333,stroke-width:1px
