import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import Config
from backend.models import ProductionRecordGRD
from backend.utilities import process_csv_file
import os
import logging
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup database
if not os.path.exists(Config.INSTANCE_PATH):
    os.makedirs(Config.INSTANCE_PATH)

try:
    engine_grd = create_engine(Config.SQLALCHEMY_BINDS['grd'])
    SessionLocal = sessionmaker(binds={
        ProductionRecordGRD: engine_grd
    })
    # Create tables if they don't exist
    ProductionRecordGRD.__table__.create(engine_grd, checkfirst=True)
    logger.info("Database connected and table checked/created.")
except Exception as e:
    logger.error(f"Database connection failed: {e}", exc_info=True)
    st.error(f"Fatal Error: Could not connect to the database. Please check configuration and logs. Error: {e}")
    st.stop()

# Streamlit configuration
st.set_page_config(page_title="Production Dashboard", layout="wide")

# --- Main App Entry ---
# Displayed only when visiting the base URL (app.py)
st.title("Welcome to the Production Monitoring System")
st.markdown("""
Navigate through the pages using the sidebar to view different aspects of the production data:
*   **Overview:** Monthly average performance metrics.
*   **OEE / Availability / Performance / Quality:** Daily trends for each specific metric (values 0-100%).
*   **Metric Errors:** Records where the specific metric calculation resulted in a value > 100%.
*   **Data Management:** View record counts.
*   **File Monitoring:** Monitor the upload folder for new CSV files (runs in the background).

You can upload new GRD CSV files using the uploader below.
""")
st.markdown("---")

# Sidebar for navigation and file upload
st.sidebar.title("Navigation & Upload")
st.sidebar.info("Select a page from above or upload files below.")

# File uploader in sidebar for multiple files
uploaded_files = st.sidebar.file_uploader("Upload GRD CSV files", type=["csv"], accept_multiple_files=True, key="main_uploader")

if uploaded_files:
    upload_folder = Config.UPLOAD_FOLDER
    if not os.path.exists(upload_folder):
        try:
            os.makedirs(upload_folder)
        except OSError as e:
            st.sidebar.error(f"Error creating upload directory: {e}")
            st.stop()

    # Use a single session for all uploads in this batch
    session = None
    try:
        session = SessionLocal()
        st.sidebar.write("Processing uploaded files...")
        progress_bar = st.sidebar.progress(0)
        processed_count = 0
        for i, uploaded_file in enumerate(uploaded_files):
            file_path = os.path.join(upload_folder, uploaded_file.name)
            try:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.sidebar.write(f"Processing: {uploaded_file.name}...")
                count = process_csv_file(file_path, session) # Pass session
                st.sidebar.success(f"Processed {uploaded_file.name} ({count} records)")
                processed_count += 1
            except Exception as e:
                st.sidebar.error(f"Error processing {uploaded_file.name}: {str(e)}")
                logger.error(f"Error processing {uploaded_file.name}: {str(e)}", exc_info=True)
                # Optionally remove the failed file
                # if os.path.exists(file_path):
                #     os.remove(file_path)
            progress_bar.progress((i + 1) / len(uploaded_files))
        st.sidebar.write(f"Finished processing {processed_count}/{len(uploaded_files)} files.")
        st.sidebar.info("Data might take a minute to reflect in dashboards. You may need to refresh.")
        # Clear cache related to data fetching after upload
        st.cache_data.clear()
    except Exception as e:
        st.sidebar.error(f"A general error occurred during processing: {str(e)}")
        logger.error(f"General file processing error: {str(e)}", exc_info=True)
    finally:
        if session:
            session.close() # Ensure session is closed