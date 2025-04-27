import streamlit as st
from sqlalchemy.orm import Session
from backend.models import ProductionRecordGRD
# Removed total_records_inserted import as it's less reliable across sessions/restarts
from backend.config import Config
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# --- Database Setup ---
try:
    engine_grd = create_engine(Config.SQLALCHEMY_BINDS['grd'])
    SessionLocal = sessionmaker(binds={ProductionRecordGRD: engine_grd})
    logger.info("Database engine created successfully for Data Management page.")
except Exception as e:
    logger.error(f"Error creating database engine: {e}", exc_info=True)
    st.error(f"Database connection failed: {e}")
    st.stop()

st.title("Data Management")
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

def display_summary(session):
    """Queries and displays the total record count."""
    try:
        grd_count = session.query(ProductionRecordGRD).count()
        st.metric("Total GRD Records in Database", grd_count)
        # st.write(f"Note: 'Processed Records' count is session-specific and may reset.")
    except Exception as e:
        logger.error(f"Error displaying summary: {str(e)}")
        st.error(f"Failed to display summary: {str(e)}")

# Display initial summary
session = None
try:
    session = SessionLocal()
    with st.spinner("Counting records..."):
        display_summary(session)
finally:
    if session:
        session.close() # Ensure session is closed

if st.button("Refresh Count"):
    session = None
    try:
        session = SessionLocal()
        with st.spinner("Counting records..."):
             # Clear cache if necessary, though count is usually fast
             # st.cache_data.clear() # Might impact other pages if used heavily
             display_summary(session)
        st.success("Record count refreshed.")
    except Exception as e:
        st.error(f"Failed to refresh count: {e}")
    finally:
        if session:
             session.close()