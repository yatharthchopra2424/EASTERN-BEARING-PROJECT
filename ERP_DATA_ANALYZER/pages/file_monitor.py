import streamlit as st
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from backend.utilities import process_csv_file, allowed_file
from backend.config import Config
from backend.models import ProductionRecordGRD
import os
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from threading import Thread, Lock
import queue

logger = logging.getLogger(__name__)

# --- Database Setup ---
# Create engine and session factory once
try:
    engine_grd = create_engine(Config.SQLALCHEMY_BINDS['grd'])
    SessionLocal = sessionmaker(binds={ProductionRecordGRD: engine_grd})
    logger.info("Database engine created successfully for File Monitor.")
except Exception as e:
    logger.error(f"Error creating database engine for monitor: {e}", exc_info=True)
    st.error(f"Database connection failed for monitoring: {e}")
    st.stop()
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
st.title("File Monitoring")
st.write(f"Watching folder: `{Config.UPLOAD_FOLDER}` for new `.csv` files.")
st.caption("New files dropped here will be automatically processed and added to the database.")

# --- State and Threading Setup ---
# Use Streamlit session state for observer, thread, and messages
if 'monitor_observer' not in st.session_state:
    st.session_state['monitor_observer'] = None
if 'monitor_thread' not in st.session_state:
    st.session_state['monitor_thread'] = None
if 'monitor_messages' not in st.session_state:
    # Initialize with a list to hold messages persistently across reruns
    st.session_state['monitor_messages'] = []
if 'monitor_running' not in st.session_state:
    st.session_state['monitor_running'] = False
if 'last_processed' not in st.session_state:
    st.session_state['last_processed'] = {} # Track processed files

# Use a thread-safe queue for messages from the handler to the main thread
# This prevents direct manipulation of st.session_state from the handler thread
message_queue = queue.Queue()

# --- Watchdog Handler ---
class CSVHandler(FileSystemEventHandler):
    def __init__(self, msg_queue):
        self.msg_queue = msg_queue
        self.processing_files = set() # Prevent processing the same file if events fire rapidly

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        filename = os.path.basename(file_path)

        # Basic check before potentially long processing
        if not allowed_file(filename):
            logger.debug(f"Ignoring non-CSV/disallowed file: {filename}")
            return
        if filename.startswith('.'): # Ignore hidden/temp files
            logger.debug(f"Ignoring hidden/temp file: {filename}")
            return

        # Avoid race conditions if multiple events fire
        # Check processing_files first
        if file_path in self.processing_files:
             logger.debug(f"Already processing {filename}, skipping duplicate event.")
             return
        self.processing_files.add(file_path)


        logger.info(f"Detected new file: {filename}")
        self.msg_queue.put(f"Detected: {filename}. Waiting...")

        # Wait a bit for the file write to potentially finish
        # This is crucial on some systems/network drives
        time.sleep(2.0) # Increased wait time

        session = None # Create session within the handler thread
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File {filename} disappeared before processing.")
                self.msg_queue.put(f"Skipped: {filename} (disappeared).")
                return

            file_mtime = os.path.getmtime(file_path)
            # Check if already processed (using session_state for persistence across Streamlit reruns)
            # Access session_state carefully from threads - reading is generally okay, writing needs caution.
            # Reading last_processed should be safe here.
            last_processed_time = st.session_state.get('last_processed', {}).get(file_path)

            if last_processed_time is not None and last_processed_time == file_mtime:
                logger.info(f"Skipping already processed file version: {filename}")
                self.msg_queue.put(f"Skipped: {filename} (already processed).")
                return

            self.msg_queue.put(f"Processing: {filename}...")
            session = SessionLocal() # Create a new session for this file processing task
            count = process_csv_file(file_path, session) # process_csv_file handles commit/rollback

            # Update session_state only after successful processing via queue later if needed,
            # or accept potential minor race condition if watchdog stops exactly during this update.
            # For simplicity, we will update last_processed directly here, accepting minimal risk.
            # A more robust way would be to send success msg back to main thread to update state.
            st.session_state.setdefault('last_processed', {})[file_path] = file_mtime

            self.msg_queue.put(f"✅ Processed {filename} ({count} records)")
            logger.info(f"Processed {file_path} with {count} records")
            # Signal main thread to clear cache (using None as a special message)
            self.msg_queue.put(None)


        except Exception as e:
            self.msg_queue.put(f"❌ Failed to process {filename}: {str(e)}")
            logger.error(f"Failed to process {file_path}: {str(e)}", exc_info=True)
        finally:
            if session:
                session.close() # Ensure session is closed
            if file_path in self.processing_files:
                 self.processing_files.remove(file_path) # Remove from processing set

# --- Monitoring Control Functions ---
def start_monitoring(msg_queue):
    if not st.session_state.get('monitor_running', False):
        upload_folder = Config.UPLOAD_FOLDER
        if not os.path.exists(upload_folder):
            try:
                os.makedirs(upload_folder)
                msg_queue.put(f"Created monitoring folder: {upload_folder}")
            except OSError as e:
                 msg_queue.put(f"Error creating upload directory: {e}")
                 logger.error(f"Error creating upload directory: {e}")
                 return None, None # Indicate failure

        observer = Observer()
        event_handler = CSVHandler(msg_queue)
        try:
            observer.schedule(event_handler, upload_folder, recursive=False)
            observer.start()
            st.session_state['monitor_running'] = True
            # Don't put start message in queue, add directly to persistent list
            st.session_state['monitor_messages'].insert(0, "🟢 Monitoring started.")
            logger.info(f"Watchdog observer started for {upload_folder}")
            return observer, observer # Return observer twice (thread is part of observer)
        except Exception as e:
            # Don't put start message in queue, add directly to persistent list
            st.session_state['monitor_messages'].insert(0, f"❌ Failed to start monitoring: {e}")
            logger.error(f"Failed to start watchdog observer: {e}", exc_info=True)
            st.session_state['monitor_running'] = False
            return None, None
    return st.session_state.get('monitor_observer'), st.session_state.get('monitor_observer')


def stop_monitoring(msg_queue):
    observer = st.session_state.get('monitor_observer')
    if observer and observer.is_alive():
        try:
            observer.stop()
            observer.join(timeout=5) # Wait max 5 seconds for thread to finish
            if observer.is_alive():
                 logger.warning("Watchdog thread did not stop gracefully.")
                 st.session_state['monitor_messages'].insert(0,"⚠️ Watchdog thread did not stop gracefully.")

            st.session_state['monitor_running'] = False
            st.session_state['monitor_observer'] = None
            st.session_state['monitor_thread'] = None # Clear thread state too
            st.session_state['monitor_messages'].insert(0,"🔴 Monitoring stopped.")
            logger.info("Watchdog observer stopped.")
        except Exception as e:
            st.session_state['monitor_messages'].insert(0,f"❌ Error stopping monitoring: {e}")
            logger.error(f"Error stopping watchdog observer: {e}", exc_info=True)
    else:
        # Only add message if it wasn't already stopped
        if not st.session_state.get('monitor_running', False) and observer is None:
             st.session_state['monitor_messages'].insert(0,"ℹ️ Monitoring was not running.")
        st.session_state['monitor_running'] = False # Ensure state is correct
        st.session_state['monitor_observer'] = None
        st.session_state['monitor_thread'] = None

# --- Streamlit UI Elements ---
col1, col2 = st.columns(2)

with col1:
    if st.button("Start Monitoring", disabled=st.session_state.get('monitor_running', False)):
        obs, thr = start_monitoring(message_queue) # Use the thread-safe queue
        if obs:
             st.session_state['monitor_observer'] = obs
             st.rerun()

with col2:
    if st.button("Stop Monitoring", disabled=not st.session_state.get('monitor_running', False)):
        stop_monitoring(message_queue) # Use the thread-safe queue
        st.rerun()


# Display monitoring status
is_alive = False
observer_state = st.session_state.get('monitor_observer')
if observer_state and hasattr(observer_state, 'is_alive'):
    is_alive = observer_state.is_alive()

status = "Running" if st.session_state.get('monitor_running', False) and is_alive else "Stopped"
st.metric("Monitoring Status", status)


# Process messages from the queue and add to persistent list
new_messages = False
while not message_queue.empty():
    try:
        message = message_queue.get_nowait()
        if message is None: # Special message to clear cache
            st.cache_data.clear()
            logger.info("Cache cleared due to file processing signal.")
        else:
            st.session_state['monitor_messages'].insert(0, message) # Add to front (newest first)
            new_messages = True
    except queue.Empty:
        break

# Limit displayed messages to avoid overly long lists
MAX_LOG_MESSAGES = 100
if len(st.session_state['monitor_messages']) > MAX_LOG_MESSAGES:
    st.session_state['monitor_messages'] = st.session_state['monitor_messages'][:MAX_LOG_MESSAGES]

# Display messages in a scrollable container
st.subheader("Monitoring Log")
log_container = st.container(height=300) # Makes it scrollable if content exceeds height

with log_container:
    for message in st.session_state['monitor_messages']: # Already newest first due to insert(0,...)
        st.text(message)

# Keep the monitoring thread alive if it's running
# The observer thread runs independently. We just need to ensure Streamlit
# periodically checks the message queue if the observer is active.
if st.session_state.get('monitor_running', False) and is_alive:
    time.sleep(2) # Brief pause to allow messages to queue
    st.rerun() # Rerun to check queue and update log display

# Automatically attempt to start monitoring on first load if not already running/started
# This prevents restarting if user navigates away and back
if 'monitor_init_done' not in st.session_state:
    logger.info("First load of monitor page, attempting to auto-start monitoring.")
    obs, thr = start_monitoring(message_queue)
    if obs:
        st.session_state['monitor_observer'] = obs
    st.session_state['monitor_init_done'] = True # Mark init as done
    st.rerun() # Rerun immediately to show status and start periodic checks