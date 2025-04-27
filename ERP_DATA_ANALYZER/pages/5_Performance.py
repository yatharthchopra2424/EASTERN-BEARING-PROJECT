# ========== File: pages\7_Quality.py ==========

import streamlit as st
from sqlalchemy.orm import Session
from backend.models import ProductionRecordGRD
from backend.config import Config
import pandas as pd
import altair as alt
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import math

logger = logging.getLogger(__name__)

# --- Database Setup ---
try:
    engine_grd = create_engine(Config.SQLALCHEMY_BINDS['grd'])
    SessionLocal = sessionmaker(binds={ProductionRecordGRD: engine_grd})
    logger.info("Database engine created successfully for Quality page.")
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
st.title("Quality Rate Analysis")
st.markdown("Daily average Quality Rate values (0-100%), faceted by month. Use filters in the sidebar.") # Updated description
st.markdown("---")

# --- Data Fetching (Revised Structure V4 - Simpler) ---
@st.cache_data(ttl=600)
def fetch_metric_data(_session, metric_name):
    required_metric = metric_name
    logger.info(f"Fetching data for metric: {required_metric}")

    try:
        metric_attribute_map = {
            "oee_new": ProductionRecordGRD.oee_new,
            "availability": ProductionRecordGRD.availability,
            "performance": ProductionRecordGRD.performance,
            "quality_rate": ProductionRecordGRD.quality_rate,
        }

        if required_metric not in metric_attribute_map:
            err_msg = f"Configuration Error: Metric name '{required_metric}' is not recognized."
            st.error(err_msg); logger.error(err_msg); return pd.DataFrame()

        metric_column_to_alias = metric_attribute_map[required_metric]

        columns_to_query = {
            'posting_date': ProductionRecordGRD.posting_date, 'machine_no': ProductionRecordGRD.machine_no,
            'work_shift_code': ProductionRecordGRD.work_shift_code, 'operator_name': ProductionRecordGRD.operator_name,
            'metric_value': metric_column_to_alias.label('metric_value'), 'id': ProductionRecordGRD.id,
            'document_no': ProductionRecordGRD.document_no, 'oee_new': ProductionRecordGRD.oee_new,
            'availability': ProductionRecordGRD.availability, 'performance': ProductionRecordGRD.performance,
            'quality_rate': ProductionRecordGRD.quality_rate, 'plan_time': ProductionRecordGRD.plan_time,
            'loss_time': ProductionRecordGRD.loss_time, 'actual_run_time': ProductionRecordGRD.actual_run_time,
            'output_quantity': ProductionRecordGRD.output_quantity, 'rejection_qty': ProductionRecordGRD.rejection_qty,
            'current_c_t': ProductionRecordGRD.current_c_t, 'rework_qty': ProductionRecordGRD.rework_qty,
        }

        if required_metric in columns_to_query:
            del columns_to_query[required_metric]

        query = _session.query(*columns_to_query.values())
        logger.debug(f"Executing database query for {required_metric}...")
        data = query.all(); logger.debug(f"Query returned {len(data)} raw results.")
        if not data: logger.warning(f"No data found for {required_metric}."); return pd.DataFrame()

        df = pd.DataFrame(data, columns=columns_to_query.keys())
        logger.info(f"Fetched {len(df)} records into DataFrame for {required_metric}.")
        logger.debug(f"DataFrame columns after fetch: {df.columns.tolist()}")
        if df.columns.duplicated().any():
            logger.error(f"DUPLICATE COLUMNS DETECTED fetch: {df.columns[df.columns.duplicated()].tolist()}")
            df = df.loc[:, ~df.columns.duplicated()]; logger.warning(f"Cols now: {df.columns.tolist()}")

        if "posting_date" in df.columns:
            df["posting_date"] = pd.to_datetime(df["posting_date"], format="%d-%m-%Y", dayfirst=True, errors="coerce")
            df = df.dropna(subset=["posting_date"])
            df['month_year'] = df['posting_date'].dt.strftime('%b, %Y'); df['month_order'] = df['posting_date'].dt.strftime('%Y%m')
            df['day'] = df['posting_date'].dt.day
            if not df.empty: logger.info(f"[FETCH DEBUG] Unique months fetched: {sorted(df['month_year'].unique())}")
            else: logger.info(f"[FETCH DEBUG] DataFrame empty after date parsing.")
        else: st.error("Critical error: 'posting_date' column missing."); logger.error("posting_date missing."); return pd.DataFrame()

        if 'metric_value' not in df.columns:
            err_msg = f"Internal Error: Aliased 'metric_value' not found. Cols: {df.columns.tolist()}"; st.error(err_msg); logger.error(err_msg); return pd.DataFrame()

        df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')

        # Quality is 0-100
        df_filtered = df[df['metric_value'].between(0, 100, inclusive='both')].copy()
        df_filtered = df_filtered.dropna(subset=['metric_value'])
        logger.info(f"{len(df_filtered)} valid (0-100) records for {required_metric}.")

        for col in df_filtered.columns:
            if col not in ['posting_date','machine_no','work_shift_code','operator_name','document_no','month_year','month_order','day']:
                 if not pd.api.types.is_numeric_dtype(df_filtered[col]) and col != 'metric_value':
                    try: df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')
                    except Exception as e: logger.warning(f"Could not convert '{col}' to numeric: {e}")

        logger.debug(f"Returning filtered DataFrame cols: {df_filtered.columns.tolist()}")
        return df_filtered

    except SQLAlchemyError as e: err_msg = f"DB Query Error for '{required_metric}': {e}."; st.error(err_msg); logger.error(err_msg, exc_info=True); return pd.DataFrame()
    except Exception as e: logger.error(f"Error fetching {required_metric}: {e}", exc_info=True); st.error(f"Error fetching data: {e}"); return pd.DataFrame()


# --- Sidebar Filters ---
st.sidebar.header("Filters")
metric_to_display = "quality_rate"
metric_title = "Quality Rate"
chart_color = "#e74c3c" # Quality color
try:
    session = SessionLocal()
    # df_display has all valid (0-100) data BEFORE sidebar filters
    df_display = fetch_metric_data(session, metric_to_display)
finally:
    if session: session.close()

# df_filtered_display starts as a copy, sidebar filters apply to this
df_filtered_display = df_display.copy()

# --->>> DEBUGGING: Log DataFrame before sidebar filters <<<---
if not df_filtered_display.empty:
     logger.info(f"[SIDEBAR DEBUG] Before filters - Shape: {df_filtered_display.shape}, Months: {sorted(df_filtered_display['month_year'].unique())}")
else:
     logger.info("[SIDEBAR DEBUG] Before filters - DataFrame is empty.")
# --->>> END DEBUGGING <<<---

# --- Filtering Logic ---
if not df_display.empty: # Base filtering on the initially fetched data (df_display)
    min_date_overall = df_display["posting_date"].min().date()
    max_date_overall = df_display["posting_date"].max().date()

    if min_date_overall <= max_date_overall:
        date_range = st.sidebar.date_input(
            "Select Date Range", value=(min_date_overall, max_date_overall),
            min_value=min_date_overall, max_value=max_date_overall,
            key=f"{metric_to_display}_date_range"
        )
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            df_filtered_display = df_filtered_display[
                (df_filtered_display["posting_date"] >= start_date) &
                (df_filtered_display["posting_date"] <= end_date)
            ]
    else: st.sidebar.warning("Invalid date range.")
    if "machine_no" in df_filtered_display.columns:
        unique_machines = sorted(df_filtered_display["machine_no"].dropna().astype(str).unique())
        default_machines = unique_machines if unique_machines else []
        selected_machines = st.sidebar.multiselect("Select Machines", unique_machines, default=default_machines, key=f"{metric_to_display}_machines")
        if selected_machines: df_filtered_display = df_filtered_display[df_filtered_display["machine_no"].isin(selected_machines)]
    if "work_shift_code" in df_filtered_display.columns:
        unique_shifts = sorted(df_filtered_display["work_shift_code"].dropna().astype(str).unique())
        default_shifts = unique_shifts if unique_shifts else []
        selected_shifts = st.sidebar.multiselect("Select Shifts", unique_shifts, default=default_shifts, key=f"{metric_to_display}_shifts")
        if selected_shifts: df_filtered_display = df_filtered_display[df_filtered_display["work_shift_code"].isin(selected_shifts)]
    if "operator_name" in df_filtered_display.columns:
        unique_operators = sorted(df_filtered_display["operator_name"].dropna().astype(str).unique())
        default_operators = unique_operators if unique_operators else []
        selected_operators = st.sidebar.multiselect("Select Operators", unique_operators, default=default_operators, key=f"{metric_to_display}_operators")
        if selected_operators: df_filtered_display = df_filtered_display[df_filtered_display["operator_name"].isin(selected_operators)]

# This df_filtered_display now contains 0-100 Quality data matching sidebar filters
df_plot_data = df_filtered_display # Use this potentially filtered data for plotting

# --->>> DEBUGGING: Log DataFrame after sidebar filters <<<---
if not df_plot_data.empty:
     logger.info(f"[PLOT DEBUG] After filters - Shape: {df_plot_data.shape}, Months: {sorted(df_plot_data['month_year'].unique())}")
else:
     logger.info("[PLOT DEBUG] After filters - DataFrame is empty.")
# --->>> END DEBUGGING <<<---


# Warning if initial fetch failed
if df_display.empty:
    st.warning(f"No valid data (0-100%) available for {metric_title}. Please upload/process files.")

# --- Main Chart Display ---
st.subheader(f"Daily Average {metric_title} Trend by Month")

if not df_plot_data.empty: # Check if data remains after sidebar filters

    # Define Tooltips (Fixed Formatting)
    base_tooltip_list = [
        alt.Tooltip('posting_date:T', title='Date', format="%Y-%m-%d"),
        alt.Tooltip('day:O', title='Day'),
        alt.Tooltip('mean(metric_value):Q', title=f'Avg {metric_title} (%)', format=".1f"),
    ]
    tooltip_cols_formats = { # Map column to format and title
        'oee_new': ('.1f', 'Avg OEE (%)'), 'availability': ('.1f', 'Avg Availability (%)'),
        'performance': ('.1f', 'Avg Performance (%)'), 'quality_rate': ('.1f', 'Avg Quality (%)'),
        'plan_time': ('.0f', 'Avg Plan Time (s)'), 'loss_time': ('.0f', 'Avg Loss Time (s)'),
        'actual_run_time': ('.0f', 'Avg Run Time (s)'), 'output_quantity': ('.0f', 'Avg Output Qty'),
        'rejection_qty': ('.0f', 'Avg Reject Qty'), 'rework_qty': ('.0f', 'Avg Rework Qty'),
        'current_c_t': ('.1f', 'Avg Current C/T (s)'), 'machine_no': (None, 'Machine'),
        'work_shift_code': (None, 'Shift'), 'operator_name': (None, 'Operator'),
        'document_no': (None, 'Document No.'), 'id': (None, 'Record ID'),
        'count()': ('.0f', 'Record Count')
    }
    for col, (fmt, title) in tooltip_cols_formats.items():
        if col in df_plot_data.columns and col != metric_to_display:
            is_numeric_kpi = col in ['oee_new', 'availability', 'performance', 'quality_rate', 'plan_time', 'loss_time', 'actual_run_time', 'output_quantity', 'rejection_qty', 'rework_qty', 'current_c_t']
            col_ref = f'mean({col}):Q' if is_numeric_kpi else col
            if fmt: base_tooltip_list.append(alt.Tooltip(col_ref, title=title, format=fmt))
            else: base_tooltip_list.append(alt.Tooltip(col, title=title))
    base_tooltip_list = [tip for tip in base_tooltip_list if tip is not None]


    # --- Charting Logic: Average Daily Line Plot ---
    y_scale = alt.Scale(domain=[0, 100]) # Quality is always 0-100

    line = alt.Chart(df_plot_data).mark_line(point=True, color=chart_color).encode(
        x=alt.X('day:O', title='Day of Month', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('mean(metric_value):Q', title=f'Avg {metric_title} (%)', scale=y_scale),
        tooltip=base_tooltip_list,
        facet=alt.Facet('month_year:N', columns=3, title=None, sort=alt.SortField(field="month_order")),
        order='day:O'
    ).properties(
        # title=f"Daily Average {metric_title} by Month"
    ).interactive()

    # --- Display Chart ---
    try:
        st.altair_chart(line, use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying chart: {e}")
        logger.error(f"Altair chart error: {e}", exc_info=True)

# Handle case where sidebar filters cleared all data
elif not df_display.empty: # Check if data existed before sidebar filtering
     st.warning("No data matches the selected filters.")
# Initial empty data case handled near the top fetch

# --- Display Data Table (Corrected Column Selection V2) ---
st.markdown("---")
table_header_range = "(0-100%)" # Quality is always 0-100
st.subheader(f"Filtered Detailed Data Table {table_header_range}")

# Use df_filtered_display (which has Quality 0-100 and matches sidebar filters)
df_table_data = df_filtered_display.rename(columns={'metric_value': metric_to_display})

# Define the desired display order
display_cols_order = [
    'posting_date', 'day', 'month_year', 'machine_no', 'work_shift_code', 'operator_name',
    metric_to_display, # The specific metric for this page (quality_rate)
    'oee_new', 'availability', 'performance', # Add all other KPIs
    'output_quantity', 'rejection_qty', 'rework_qty', # Quality inputs
    'plan_time', 'loss_time', 'actual_run_time', 'current_c_t', # Other inputs
    'document_no', 'id'
]

# Create the list of columns that actually exist in the dataframe AND are unique
final_cols_to_show = []
seen_cols = set()
for col in display_cols_order:
    if col in df_table_data.columns and col not in seen_cols:
        is_generic_kpi = col in ['oee_new', 'availability', 'performance', 'quality_rate']
        if is_generic_kpi and col == metric_to_display and metric_to_display not in seen_cols:
             final_cols_to_show.append(metric_to_display); seen_cols.add(metric_to_display)
        elif col not in seen_cols:
             final_cols_to_show.append(col); seen_cols.add(col)

logger.debug(f"Final columns for st.dataframe: {final_cols_to_show}")

# Display the table using the final, de-duplicated list of columns
if not df_table_data.empty:
    df_table_data_final = df_table_data[final_cols_to_show]
    if df_table_data_final.columns.duplicated().any():
         logger.error(f"Duplicate columns detected before st.dataframe: {df_table_data_final.columns[df_table_data_final.columns.duplicated()].tolist()}")
         st.error("Internal error: Duplicate columns identified before displaying table.")
         try: st.dataframe(df_table_data_final.loc[:, ~df_table_data_final.columns.duplicated()])
         except Exception as display_err: logger.error(f"Error displaying table after dedup: {display_err}", exc_info=True); st.error(f"Further error displaying table: {display_err}")
    else:
         try: st.dataframe(df_table_data_final)
         except Exception as e: logger.error(f"Error displaying dataframe: {e}", exc_info=True); st.error(f"Error displaying table: {e}")
else:
     if not df_display.empty: st.warning("No data matches filters for table display.")