import streamlit as st
from sqlalchemy.orm import Session
from backend.models import ProductionRecordGRD
from backend.config import Config
import pandas as pd
import altair as alt
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# --- Database Setup ---
try:
    engine_grd = create_engine(Config.SQLALCHEMY_BINDS['grd'])
    SessionLocal = sessionmaker(binds={ProductionRecordGRD: engine_grd})
    logger.info("Database engine created successfully for OEE Errors page.")
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
st.title("OEE Errors (> 100%)")
st.markdown("This page shows records where the calculated OEE value is greater than 100%.")
st.markdown("---")

# --- Data Fetching for Errors ---
@st.cache_data(ttl=600)
def fetch_error_data(_session, metric_name):
    required_metric = metric_name
    try:
        query = _session.query(ProductionRecordGRD) # Fetch all columns for detail
        data = query.all()

        if not data:
            logger.warning(f"No data found for {required_metric} error check.")
            return pd.DataFrame()

        # Convert records to dictionaries, excluding the internal SQLAlchemy state
        records = [
            {c.name: getattr(d, c.name) for c in d.__table__.columns}
            for d in data
        ]
        df = pd.DataFrame(records)
        logger.info(f"Fetched {len(df)} records for {required_metric} error check.")

        if "posting_date" in df.columns:
            df["posting_date"] = pd.to_datetime(df["posting_date"], format="%d-%m-%Y", dayfirst=True, errors="coerce")
            df = df.dropna(subset=["posting_date"])
        else:
            st.warning("Required column 'posting_date' is missing.")
            return pd.DataFrame()

        if required_metric not in df.columns:
            st.warning(f"Required column '{required_metric}' is missing.")
            return pd.DataFrame()

        df[required_metric] = pd.to_numeric(df[required_metric], errors='coerce')
        error_df = df[df[required_metric] > 100].copy() # Filter only > 100 strictly
        logger.info(f"Found {len(error_df)} records with {required_metric} > 100.")

        error_df = error_df.sort_values(by="posting_date")
        return error_df

    except AttributeError:
        st.error(f"Configuration Error: Metric column '{required_metric}' not found.")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching/processing {required_metric} error data: {e}", exc_info=True)
        st.error(f"An error occurred fetching error data: {e}")
        return pd.DataFrame()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
metric_to_display = "oee_new"
metric_title = "OEE"
try:
    session = SessionLocal()
    df_errors = fetch_error_data(session, metric_to_display)
finally:
    session.close()

df_filtered_errors = df_errors.copy()

if not df_filtered_errors.empty:
    # Date Range Filter
    min_date_err = df_filtered_errors["posting_date"].min().date()
    max_date_err = df_filtered_errors["posting_date"].max().date()
    date_range_err = st.sidebar.date_input(
        "Select Date Range", value=(min_date_err, max_date_err), min_value=min_date_err, max_value=max_date_err,
        key=f"{metric_to_display}_err_date_range" # Unique key for OEE error date
    )
    if len(date_range_err) == 2:
        start_date_err, end_date_err = pd.to_datetime(date_range_err[0]), pd.to_datetime(date_range_err[1])
        df_filtered_errors = df_filtered_errors[(df_filtered_errors["posting_date"] >= start_date_err) & (df_filtered_errors["posting_date"] <= end_date_err)]

    # Machine Filter
    if "machine_no" in df_filtered_errors.columns:
        unique_machines_err = sorted(df_filtered_errors["machine_no"].dropna().astype(str).unique())
        default_machines_err = unique_machines_err if unique_machines_err else []
        selected_machines_err = st.sidebar.multiselect(
            "Select Machines", options=unique_machines_err, default=default_machines_err,
            key=f"{metric_to_display}_err_machines" # Unique key for OEE error machines
        )
        if selected_machines_err:
            df_filtered_errors = df_filtered_errors[df_filtered_errors["machine_no"].isin(selected_machines_err)]

    # Shift Filter
    if "work_shift_code" in df_filtered_errors.columns:
        unique_shifts_err = sorted(df_filtered_errors["work_shift_code"].dropna().astype(str).unique())
        default_shifts_err = unique_shifts_err if unique_shifts_err else []
        selected_shifts_err = st.sidebar.multiselect(
            "Select Shifts", options=unique_shifts_err, default=default_shifts_err,
            key=f"{metric_to_display}_err_shifts" # Unique key for OEE error shifts
        )
        if selected_shifts_err:
            df_filtered_errors = df_filtered_errors[df_filtered_errors["work_shift_code"].isin(selected_shifts_err)]

    # Operator Filter <-- NEW
    if "operator_name" in df_filtered_errors.columns:
        unique_operators_err = sorted(df_filtered_errors["operator_name"].dropna().astype(str).unique())
        default_operators_err = unique_operators_err if unique_operators_err else []
        selected_operators_err = st.sidebar.multiselect(
            "Select Operators", options=unique_operators_err, default=default_operators_err,
            key=f"{metric_to_display}_err_operators" # Unique key for OEE error operators
        )
        if selected_operators_err:
            df_filtered_errors = df_filtered_errors[df_filtered_errors["operator_name"].isin(selected_operators_err)]

# --- Error Data Display ---
st.subheader(f"Records with {metric_title} > 100%")

if not df_filtered_errors.empty:
    st.info(f"Found {len(df_filtered_errors)} record(s) with {metric_title} exceeding 100% matching the current filters.")
    # Display the table of errors
    display_cols_err = [
        'posting_date', 'machine_no', 'work_shift_code', 'operator_name', metric_to_display,
        'availability', 'performance', 'quality_rate', # Other relevant KPIs
        'plan_time', 'loss_time', 'actual_run_time', 'output_quantity', # Inputs for OEE
        'rejection_qty', 'current_c_t', 'document_no', 'id'
    ]
    cols_to_show_err = [col for col in display_cols_err if col in df_filtered_errors.columns]
    st.dataframe(df_filtered_errors[cols_to_show_err])

    st.markdown("---")
    st.subheader(f"{metric_title} Error Values Trend (> 100%)")
     # Create the line chart for error values (unchanged chart type)
    error_chart = alt.Chart(df_filtered_errors).mark_line(point=True, color='red').encode(
        x=alt.X('posting_date:T', title='Date', axis=alt.Axis(format="%Y-%m-%d", labelAngle=-45)),
        y=alt.Y(f'{metric_to_display}:Q', title=f'{metric_title} (%)', scale=alt.Scale(domainMin=100)), # Start Y axis at 100
        tooltip=[
            alt.Tooltip('posting_date:T', title='Date', format="%Y-%m-%d"),
            alt.Tooltip(f'{metric_to_display}:Q', title=f'{metric_title} (%)', format=".1f"),
            alt.Tooltip('machine_no:N', title='Machine'),
            alt.Tooltip('work_shift_code:N', title='Shift'),
            alt.Tooltip('operator_name:N', title='Operator'),
            alt.Tooltip('document_no:N', title='Document No.'),
            alt.Tooltip('id:Q', title='Record ID')
        ]
    ).interactive()
    st.altair_chart(error_chart, use_container_width=True)

else:
    if df_errors.empty: # Check original unfiltered errors
        st.success(f"No records found with {metric_title} > 100% in the database.")
    else:
        st.warning(f"No {metric_title} errors match the selected filters.")