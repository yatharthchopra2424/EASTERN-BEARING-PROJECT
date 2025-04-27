import streamlit as st
from sqlalchemy.orm import Session
from backend.models import ProductionRecordGRD
from backend.config import Config
import pandas as pd
import altair as alt
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import math

logger = logging.getLogger(__name__)

# --- Database Setup ---
try:
    engine_grd = create_engine(Config.SQLALCHEMY_BINDS['grd'])
    SessionLocal = sessionmaker(binds={ProductionRecordGRD: engine_grd})
    logger.info("Database engine created successfully for Overview page.")
except Exception as e:
    logger.error(f"Error creating database engine: {e}", exc_info=True)
    st.error(f"Database connection failed: {e}")
    st.stop()

st.set_page_config(layout="wide")
st.markdown("""
    <style>
        /* Hide header and footer */
        header, footer, [data-testid="stToolbar"] {
            display: none !important;
        }
        /* Apply padding to block-container for content spacing */
        .block-container {
            padding: 1rem 1rem 1rem 1rem !important; /* Adjust T R B L padding as needed */
            margin: 0 !important;
            width: 100% !important; /* Ensure it uses full width */
            max-width: 100% !important;
        }
        /* Remove padding from the absolute main container if necessary */
        .main > div {
             padding-top: 1rem !important; /* Minimal top padding */
             padding-left: 1rem !important;
             padding-right: 1rem !important;
             padding-bottom: 1rem !important;
        }
        /* Ensure main uses full height if desired, but be careful with overflow */
        html, body, .main {
            /* height: 100%; */ /* Uncomment if you REALLY want fixed height */
            /* width: 100%; */
            /* overflow: auto; */ /* Allow scrolling if needed */
        }
        /* Hide scrollbar (Optional - can hide necessary scrollbars) */
        /*
        ::-webkit-scrollbar {
            display: none;
        }
        */
    </style>
""", unsafe_allow_html=True)
st.title("Monthly Performance Overview (Averages)")
st.markdown("Monthly average of KPIs (0-100%). Use filters in the sidebar.")
st.markdown("---")

# --- Data Fetching ---
@st.cache_data(ttl=600)
def fetch_overview_data(_session):
    try:
        # Fetch relevant columns including operator name
        query = _session.query(
            ProductionRecordGRD.posting_date,
            ProductionRecordGRD.machine_no,
            ProductionRecordGRD.work_shift_code,
            ProductionRecordGRD.operator_name, # <-- Added Operator Name
            ProductionRecordGRD.oee_new,
            ProductionRecordGRD.availability,
            ProductionRecordGRD.performance,
            ProductionRecordGRD.quality_rate
            )
        data = query.all()

        if not data:
            logger.warning("No data found for overview.")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        logger.info(f"Fetched {len(df)} records for overview.")

        if "posting_date" in df.columns:
            df["posting_date"] = pd.to_datetime(df["posting_date"], format="%d-%m-%Y", dayfirst=True, errors="coerce")
            df = df.dropna(subset=["posting_date"])
        else:
            st.warning("Required column 'posting_date' is missing.")
            return pd.DataFrame()

        required_cols = ["oee_new", "availability", "performance", "quality_rate"]
        existing_cols = [col for col in required_cols if col in df.columns]
        if len(existing_cols) < len(required_cols):
             missing = list(set(required_cols) - set(existing_cols))
             logger.warning(f"Missing KPI columns for overview: {missing}")
             # Don't display warning here, handle empty state later if needed
             # st.warning(f"Missing KPI columns: {', '.join(missing)}")
        if not existing_cols: return pd.DataFrame() # Return empty if no metrics exist

        # Convert metrics to numeric, coercing errors to NaN
        valid_df = df.copy()
        for col in existing_cols:
             valid_df[col] = pd.to_numeric(valid_df[col], errors='coerce')
             # Filter for valid data (0 to 100 range, inclusive) before grouping
             valid_df = valid_df[valid_df[col].between(0, 100, inclusive="both")]

        if valid_df.empty:
             logger.warning("No valid data (0-100) found after filtering for overview.")
             # Return empty so filters don't try to operate on it
             return pd.DataFrame()

        logger.info(f"{len(valid_df)} valid records remain for overview calculation.")
        return valid_df

    except Exception as e:
        logger.error(f"Error fetching/processing overview data: {e}", exc_info=True)
        st.error(f"An error occurred fetching overview data: {e}")
        return pd.DataFrame()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
try:
    session = SessionLocal()
    df = fetch_overview_data(session)
finally:
    session.close()

df_filtered = df.copy()

if not df_filtered.empty:
    # Date Range Filter
    min_date = df_filtered["posting_date"].min().date()
    max_date = df_filtered["posting_date"].max().date()
    date_range = st.sidebar.date_input(
        "Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date,
        key="overview_date_range"
    )
    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        df_filtered = df_filtered[(df_filtered["posting_date"] >= start_date) & (df_filtered["posting_date"] <= end_date)]

    # Machine Filter
    if "machine_no" in df_filtered.columns:
        unique_machines = sorted(df_filtered["machine_no"].dropna().unique())
        default_machines = unique_machines if unique_machines else []
        selected_machines = st.sidebar.multiselect(
            "Select Machines", options=unique_machines, default=default_machines,
            key="overview_machines"
        )
        if selected_machines:
            df_filtered = df_filtered[df_filtered["machine_no"].isin(selected_machines)]

    # Shift Filter
    if "work_shift_code" in df_filtered.columns:
        unique_shifts = sorted(df_filtered["work_shift_code"].dropna().unique())
        default_shifts = unique_shifts if unique_shifts else []
        selected_shifts = st.sidebar.multiselect(
            "Select Shifts", options=unique_shifts, default=default_shifts,
            key="overview_shifts"
        )
        if selected_shifts:
            df_filtered = df_filtered[df_filtered["work_shift_code"].isin(selected_shifts)]

    # Operator Filter <-- NEW
    if "operator_name" in df_filtered.columns:
        # Handle potential NaN/None before sorting/displaying
        unique_operators = sorted(df_filtered["operator_name"].astype(str).dropna().unique())
        default_operators = unique_operators if unique_operators else []
        selected_operators = st.sidebar.multiselect(
            "Select Operators", options=unique_operators, default=default_operators,
            key="overview_operators" # Unique key
        )
        if selected_operators:
            df_filtered = df_filtered[df_filtered["operator_name"].isin(selected_operators)]

else:
     # Only show warning if initial fetch was empty
     if df.empty:
        st.warning("No valid data (0-100%) available for overview. Please upload/process files.")

# --- Calculations and Charting ---
if not df_filtered.empty:
    df_filtered["month_year"] = df_filtered["posting_date"].dt.strftime("%b, %y")
    metrics_to_display = [col for col in ["oee_new", "availability", "performance", "quality_rate"] if col in df_filtered.columns]

    if metrics_to_display:
        monthly_avg = df_filtered.groupby("month_year", as_index=False)[metrics_to_display].mean()
        # Add sort key for proper month ordering
        try:
            monthly_avg["sort_date"] = pd.to_datetime(monthly_avg["month_year"], format="%b, %y")
            monthly_avg = monthly_avg.sort_values("sort_date").drop(columns=["sort_date"])
        except ValueError:
            logger.warning("Could not parse month_year for sorting, using alphabetical.")
            # Fallback to alphabetical sort if parsing fails
            monthly_avg = monthly_avg.sort_values("month_year")


        for col in metrics_to_display:
            monthly_avg[f"{col}_label"] = monthly_avg[col].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "N/A")

        def create_overview_chart(data, column, y_title, color):
            bars = alt.Chart(data).mark_bar(color=color).encode(
                x=alt.X("month_year:N", title="Month, Year", sort=None, axis=alt.Axis(labelAngle=0)), # Use explicit sort=None
                y=alt.Y(f"{column}:Q", title=y_title, scale=alt.Scale(domain=[0, 100])), # Force 0-100
                tooltip=[
                    alt.Tooltip("month_year:N", title="Month"),
                    alt.Tooltip(f"{column}:Q", title=y_title, format=".1f")
                ]
            )
            text = alt.Chart(data).mark_text(align="center", baseline="middle", dy=-10, color="black", fontSize=10).encode(
                x=alt.X("month_year:N", sort=None),
                y=alt.Y(f"{column}:Q"),
                text=f"{column}_label:N",
                opacity=alt.condition(alt.datum[column] > 0, alt.value(1.0), alt.value(0.0))
            )
            # Adjust width dynamically or use fixed steps
            return (bars + text).properties(width=alt.Step(max(40, 600 // len(data) if len(data) > 0 else 40))) # Dynamic width


        st.subheader("📊 Monthly KPI Averages")
        metric_colors = {"oee_new": "#4a90e2", "availability": "#2ecc71", "performance": "#f1c40f", "quality_rate": "#e74c3c"}
        num_metrics = len(metrics_to_display)
        # Use st.columns layout - adjust number based on metrics found
        if num_metrics > 0:
            cols = st.columns(num_metrics)
            for i, metric in enumerate(metrics_to_display):
                with cols[i]:
                    metric_title_disp = metric.replace('_', ' ').title()
                    st.markdown(f"**{metric_title_disp} (%)**")
                    chart = create_overview_chart(monthly_avg, metric, f"Avg {metric_title_disp} (%)", metric_colors.get(metric, "#888888"))
                    st.altair_chart(chart, use_container_width=True)
        else:
             st.warning("No KPI columns with valid data found after filtering to display averages.")
    else:
        st.warning("No KPI columns found in the data to display averages.")

# Handle cases where df_filtered became empty *after* applying filters
elif not df.empty: # Check if data existed before filtering
     st.warning("No data matches the selected filters.")
# Initial empty data case handled above filters