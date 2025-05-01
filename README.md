 # EASTERN BEARING PROJECT
 A SOLUTION TO THE PROBLEM SPECIFIED BY ARB BEARING



https://github.com/user-attachments/assets/00b32016-5159-4627-8a74-0683d1c47637

[progress report Mini project.pdf](https://github.com/user-attachments/files/19996720/progress.report.Mini.project.pdf)


https://github.com/user-attachments/assets/21431ffd-9480-4c1a-98d6-5badc15447c1

## Check dashboard here 
https://arbbearing-pvt-ltd.streamlit.app/

## DIAGRAM 
```mermaid
graph LR
    %% Data Source
    CSV["📂 User Uploads (CSV)"]:::dataSource
    click CSV "https://github.com/yatharthchopra2424/eastern-bearing-project/tree/main/ERP_DATA_ANALYZER/uploads"

    %% Ingestion Layer
    subgraph Ingestion
        FM["🛠 file_monitor.py"]:::backend
        DM["🔄 data_management.py"]:::backend
    end
    click FM "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/pages/file_monitor.py"
    click DM "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/pages/data_management.py"

    %% Backend Core
    subgraph Backend
        Cfg["⚙️ config.py"]:::backend
        Mdl["📦 models.py"]:::backend
        Ut["🧰 utilities.py"]:::backend
        ERPreq["📜 requirements.txt"]:::backend
    end
    click Cfg "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/backend/config.py"
    click Mdl "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/backend/models.py"
    click Ut "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/backend/utilities.py"
    click ERPreq "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/requirements.txt"

    %% Storage
    subgraph Storage
        DB["💾 SQLite DB"]:::storage
        LOG["🧾 app.log"]:::storage
    end
    click DB "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/instance/grd_db.sqlite"
    click LOG "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/instance/logs/app.log"

    %% Frontend (Streamlit)
    subgraph "Frontend UI"
        App["🖥️ app.py"]:::frontend
        UIcfg["⚙️ config.toml"]:::frontend
        Pages["📄 Pages (Overview, OEE, etc.)"]:::frontend
    end
    click App "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/app.py"
    click UIcfg "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/ERP_DATA_ANALYZER/.streamlit/config.toml"
    click Pages "https://github.com/yatharthchopra2424/eastern-bearing-project/tree/main/ERP_DATA_ANALYZER/pages"

    %% Power BI
    subgraph "Power BI Layer"
        PBScr["📊 st.py"]:::frontend
        PBDash["📈 Dashboard"]:::frontend
        PBreq["📜 requirements.txt"]:::frontend
        PBread["📘 README.md"]:::frontend
    end
    click PBScr "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/DASHBOARD_POWER_BI/st.py"
    click PBreq "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/DASHBOARD_POWER_BI/requirements.txt"
    click PBread "https://github.com/yatharthchopra2424/eastern-bearing-project/blob/main/DASHBOARD_POWER_BI/README.md"

    %% Flow Connections
    CSV --> FM --> DM --> Ut --> Mdl --> DB
    Mdl --> LOG
    FM --> LOG
    DM --> LOG
    Ut --> LOG
    App --> LOG

    DB --> Pages --> App
    DB --> PBScr --> PBDash

    Cfg --> FM
    Cfg --> DM
    Cfg --> Mdl
    Cfg --> Ut
    Cfg --> App
    Cfg --> PBScr

    %% Styles
    classDef dataSource fill:#a2fca2,stroke:#333,stroke-width:1px;
    classDef backend fill:#bbdefb,stroke:#333,stroke-width:1px;
    classDef storage fill:#90caf9,stroke:#333,stroke-width:1px;
    classDef frontend fill:#ffcc80,stroke:#333,stroke-width:1px;

