import pandas as pd
import os
import logging
from pathlib import Path
from backend.models import ProductionRecordGRD
from backend.config import Config
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import math # For isnan check and floor

# Configure logging
log_dir = Path(Config.INSTANCE_PATH) / "logs"
log_dir.mkdir(parents=True, exist_ok=True) # Ensure log dir exists within instance path
log_file = log_dir / "app.log"

# Create logger instance
logger = logging.getLogger(__name__)
logger.setLevel(Config.LOG_LEVEL)

# Prevent adding multiple handlers if script is re-run in some environments (like Streamlit)
if not logger.handlers:
    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8') # Specify encoding
    fh.setLevel(Config.LOG_LEVEL)
    # Stream handler (console)
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO) # Console logs might be less verbose
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    # Add handlers
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.info("Logger configured.") # Log confirmation

def allowed_file(filename):
    """Checks if the filename has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def determine_db_type(filename):
    """Determines the database model and bind key based on filename."""
    filename_upper = filename.upper()
    if '_GRD' in filename_upper:
        return ProductionRecordGRD, 'grd'
    else:
        logger.warning(f"Could not determine database type for filename: {filename}. Assuming 'grd'.")
        return ProductionRecordGRD, 'grd'

def safe_float_conversion(value, default=0.0):
    """Safely converts a value to float, handling potential errors and NaN/NA."""
    if pd.isna(value): return default
    if isinstance(value, str) and value.strip() == '': return default
    try:
        f_value = float(value)
        if math.isnan(f_value) or math.isinf(f_value): return default
        return f_value
    except (ValueError, TypeError): return default

def time_to_seconds(time_value):
    """Converts various time representations (HH:MM:SS, seconds as number) to integer seconds."""
    if pd.isna(time_value): return 0
    if isinstance(time_value, str):
        time_value = time_value.strip()
        if time_value == '': return 0
    if isinstance(time_value, (int, float)):
        if math.isnan(time_value) or math.isinf(time_value): return 0
        try: return int(round(time_value))
        except (ValueError, TypeError): return 0
    if isinstance(time_value, str):
        parts = time_value.split(':')
        try:
            if len(parts) == 3:
                h, m, s = map(int, parts)
                if 0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59: return h * 3600 + m * 60 + s
                else: return 0
            elif len(parts) == 2:
                h, m = map(int, parts)
                if 0 <= h <= 23 and 0 <= m <= 59: return h * 3600 + m * 60
                else: return 0
            elif len(parts) == 1:
                 num_val = safe_float_conversion(parts[0], None)
                 return int(round(num_val)) if num_val is not None else 0
            else: return 0
        except (ValueError, IndexError, TypeError): return 0
    return 0

# --- Calculation Functions ---
# (Keep calc functions as they were, they rely on correct input)
def calc_availability(plan_time_s, loss_time_s):
    plan_time = safe_float_conversion(plan_time_s, 0.0)
    loss_time = safe_float_conversion(loss_time_s, 0.0)
    if plan_time <= 0: return 0.0
    available_time = max(0.0, plan_time - loss_time)
    availability_ratio = available_time / plan_time
    return max(0.0, min(100.0, availability_ratio * 100))

def calc_quality_rate(output_qty, reject_qty, rework_qty=0):
    total_produced = safe_float_conversion(output_qty, 0.0)
    reject_qty = safe_float_conversion(reject_qty, 0.0)
    if total_produced <= 0: return 0.0 if reject_qty > 0 else 100.0
    reject_qty = min(reject_qty, total_produced)
    good_qty = total_produced - reject_qty
    quality_ratio = good_qty / total_produced
    return max(0.0, min(100.0, quality_ratio * 100))

def calc_performance(output_qty, current_ct_s, actual_run_time_s):
    output_qty = safe_float_conversion(output_qty, 0.0)
    ideal_cycle_time = safe_float_conversion(current_ct_s, 0.0)
    run_time = safe_float_conversion(actual_run_time_s, 0.0)
    if run_time <= 0 or ideal_cycle_time <= 0 or output_qty <= 0: return 0.0
    ideal_total_time = output_qty * ideal_cycle_time
    performance_ratio = ideal_total_time / run_time
    return max(0.0, performance_ratio * 100)

def calc_shift_type(actual_run_time_s):
    run_time = safe_float_conversion(actual_run_time_s, 0.0)
    return "Active" if run_time > 0 else "Idle" # Example logic, may need refinement

def calc_oee_new(availability, performance, quality_rate):
    avail_ratio = safe_float_conversion(availability, 0.0) / 100.0
    perf_ratio = safe_float_conversion(performance, 0.0) / 100.0
    qual_ratio = safe_float_conversion(quality_rate, 0.0) / 100.0
    avail_ratio = max(0.0, min(1.0, avail_ratio))
    qual_ratio = max(0.0, min(1.0, qual_ratio))
    perf_ratio = max(0.0, perf_ratio)
    oee_ratio = avail_ratio * perf_ratio * qual_ratio
    return max(0.0, oee_ratio * 100)


def process_csv_file(file_path: str, db_session: Session):
    file_name = os.path.basename(file_path)
    logger.info(f"Starting processing for: {file_name}")

    try:
        # 1. Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found during processing: {file_name}")
            raise FileNotFoundError(f"File not found: {file_path}")

        # 3. Determine Model Type
        model, bind_key = determine_db_type(file_name)

        # 4. Read CSV
        logger.debug(f"Reading CSV: {file_name}")
        try:
            # Read all as string initially to handle variations, then convert
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False, dtype=str, on_bad_lines='warn')
            if df.empty:
                logger.warning(f"Empty CSV file: {file_name}")
                return 0
        except Exception as e:
             logger.error(f"Error reading CSV {file_name}: {e}", exc_info=True)
             raise IOError(f"Could not read CSV: {file_name}") from e

        total_rows = len(df)
        logger.info(f"Read {total_rows} rows from {file_name}")

        # 5. Clean Column Names
        original_columns = df.columns.tolist()
        df.columns = [str(col).lower().strip().replace(' ', '_').replace('/', '_').replace('.', '').replace('(','').replace(')','').replace('-','_') for col in df.columns]
        cleaned_columns = df.columns.tolist()
        logger.debug(f"Cleaned original columns: {original_columns}")
        logger.debug(f"Cleaned columns result: {cleaned_columns}")

        # --- Updated & Comprehensive Column Mapping ---
        column_map = {
            # Exact matches from image (after cleaning) mapped to model names
            'posting_date': 'posting_date',
            'document_no': 'document_no',
            'order_no': 'order_no',
            'item_no': 'item_no',
            'operation_no': 'operation_no',
            'operation_description': 'operation_description',
            'order_line_no': 'order_line_no',
            'type': 'type',
            'machine_no': 'machine_no',
            'current_c_t': 'current_c_t', # Cleaned from 'Current C/T'
            'output_quantity': 'output_quantity',
            'rejection_qty': 'rejection_qty',
            'rejection_reson': 'rejection_reason', # *** Fix mapping ***
            're_work_qty': 'rework_qty',          # *** Fix mapping ***
            're_work_reason': 'rework_reason',     # *** Fix mapping ***
            'work_shift_code': 'work_shift_code',
            'start_time': 'start_time',
            'end_time': 'end_time',
            'plan_time': 'plan_time',             # Cleaned from 'Plan time'
            'actual_run_time': 'actual_run_time',
            'loss_time': 'loss_time',
            'remarks': 'remarks',
            'operator_name': 'operator_name',
            'loss_time_should_be': 'loss_time_should_be',
            'oee': 'oee',                         # Original OEE column from CSV
            'reason_code': 'reason_code',
            'reason_time_hm': 'reason_time_hm',
            'loss_time_remark': 'loss_time_remark',

            # Add other potential variations if observed elsewhere
            'currentct': 'current_c_t',
            'rejectionreason': 'rejection_reason',
            'reworkqty': 'rework_qty',
            'reworkreason': 'rework_reason',
            'actualruntime': 'actual_run_time',
            'losstime_shouldbe': 'loss_time_should_be',
            'reasontimehm': 'reason_time_hm',
            'losstimeremark': 'loss_time_remark',
            'operatorname': 'operator_name'
        }
        df = df.rename(columns=lambda c: column_map.get(c, c)) # Apply mapping
        final_columns_after_map = df.columns.tolist()
        logger.debug(f"Columns after mapping: {final_columns_after_map}")

        # 6. Define Model Columns & Check for Missing/Extra relative to *Mapped* DF
        # Include calculated columns here if they are part of the model
        model_columns_dict = {c.name: c for c in model.__table__.columns if c.name != 'id'}
        # Columns expected *from the CSV* based on the model (excluding calculated ones for now)
        expected_csv_cols = {k for k, v in model_columns_dict.items() if k not in ['availability', 'performance', 'quality_rate', 'oee_new', 'shift_type']}

        # What columns does the *mapped* dataframe actually have?
        actual_mapped_cols = set(df.columns)

        missing_from_csv = expected_csv_cols - actual_mapped_cols
        extra_in_csv = actual_mapped_cols - expected_csv_cols

        # Add missing expected CSV columns and fill with None
        if missing_from_csv:
            logger.warning(f"Columns expected from CSV mapping not found: {missing_from_csv}. Filling with None.")
            for col in missing_from_csv:
                df[col] = None # Add missing columns with None value

        # Drop extra columns found in CSV that don't map to model expectations
        if extra_in_csv:
             logger.warning(f"Extra columns after mapping ignored: {extra_in_csv}.")
             df = df.drop(columns=list(extra_in_csv))

        # 7. Data Type Conversion and Cleaning
        logger.debug(f"Aligning data types for {file_name}...")
        # Now apply type conversions based on the model definition
        for col_name, col_def in model_columns_dict.items():
            if col_name not in df.columns: continue # Skip if column still missing (shouldn't happen now)
            if col_name in ['availability', 'performance', 'quality_rate', 'oee_new', 'shift_type']: continue # Skip calculated columns for now

            target_type = col_def.type.python_type
            logger.debug(f"Aligning column: '{col_name}' to target type: {target_type}")

            # Apply time/float conversions first if not done by dtype=str read
            if col_name in ['plan_time', 'actual_run_time', 'loss_time', 'loss_time_should_be', 'reason_time_hm']:
                df[col_name] = df[col_name].apply(time_to_seconds)
                target_type = int # Target is now integer seconds
            elif col_name == 'current_c_t':
                 df[col_name] = df[col_name].apply(safe_float_conversion)
                 target_type = float

            if target_type == int:
                numeric_series = pd.to_numeric(df[col_name], errors='coerce')
                not_na_mask = numeric_series.notna()
                fractional_mask = (numeric_series[not_na_mask].apply(lambda x: not math.isclose(x, math.floor(x), abs_tol=1e-9)))
                if fractional_mask.any():
                    examples = numeric_series[not_na_mask][fractional_mask].unique()[:5]
                    logger.warning(f"Column '{col_name}' contains fractional values. Truncating. Examples: {examples}")
                    numeric_series.loc[not_na_mask & fractional_mask] = numeric_series.loc[not_na_mask & fractional_mask].apply(math.floor)
                try:
                    df[col_name] = numeric_series.astype('Int64')
                except TypeError as e: raise TypeError(f"Cannot cast column '{col_name}' to Int64: {e}") from e

            elif target_type == float:
                 if col_name != 'current_c_t': df[col_name] = df[col_name].apply(safe_float_conversion)
                 df[col_name] = pd.to_numeric(df[col_name], errors='coerce').astype('Float64')

            elif target_type == str:
                 df[col_name] = df[col_name].fillna('').astype(str).replace({'nan': '', 'None': '', '<NA>': ''}, regex=False)

            elif col_name == 'posting_date':
                 df[col_name] = pd.to_datetime(df[col_name], format='%d-%m-%Y', dayfirst=True, errors='coerce').dt.strftime('%d-%m-%Y').fillna('')

            elif col_name in ['start_time', 'end_time']:
                 df[col_name] = df[col_name].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).fillna("00:00:00")

        # 8. Perform Calculations
        logger.debug(f"Calculating metrics for {file_name}...")
        try:
            # Ensure input columns for calculations exist and are correct type before applying
            # Calculation functions handle potential NA inputs via safe_float_conversion
            df['availability'] = df.apply(lambda row: calc_availability(row.get('plan_time'), row.get('loss_time')), axis=1)
            df['quality_rate'] = df.apply(lambda row: calc_quality_rate(row.get('output_quantity'), row.get('rejection_qty')), axis=1)
            df['performance'] = df.apply(lambda row: calc_performance(row.get('output_quantity'), row.get('current_c_t'), row.get('actual_run_time')), axis=1)
            df['oee_new'] = df.apply(lambda row: calc_oee_new(row.get('availability'), row.get('performance'), row.get('quality_rate')), axis=1)
            df['shift_type'] = df.apply(lambda row: calc_shift_type(row.get('actual_run_time')), axis=1) # Add shift type calc
            logger.debug(f"Finished calculating metrics for {file_name}.")
        except Exception as calc_error:
             logger.error(f"Error during metric calculation for {file_name}: {calc_error}", exc_info=True)
             raise RuntimeError(f"Metric calculation failed for {file_name}") from calc_error


        # 9. Prepare for Bulk Insert
        # Now select *all* columns defined in the model
        columns_to_insert = list(model_columns_dict.keys())

        # Ensure calculated columns exist before selection
        for calc_col in ['availability', 'quality_rate', 'performance', 'oee_new', 'shift_type']:
             if calc_col not in df.columns:
                  logger.warning(f"Calculated column '{calc_col}' missing before final selection. Setting to None.")
                  df[calc_col] = None

        # Final check that all model columns are present in df
        missing_final_check = set(columns_to_insert) - set(df.columns)
        if missing_final_check:
             logger.error(f"Columns missing just before creating df_final: {missing_final_check}")
             # Add them back if missing - this indicates a logic error above
             for col in missing_final_check: df[col] = None


        df_final = df[[col for col in columns_to_insert if col in df.columns]].copy()

        # Replace pandas NA/NaN/NaT with Python None using .where()
        df_final = df_final.where(pd.notna(df_final), None)
        logger.debug("Applied .where(pd.notna(df_final), None) to replace missing values.")

        records = df_final.to_dict('records')
        logger.debug(f"Prepared {len(records)} records for insertion from {file_name}.")

        # 10. Bulk Insert
        if records:
            logger.info(f"Attempting bulk insert for {len(records)} records from {file_name}...")
            try:
                db_session.bulk_insert_mappings(model, records)
                db_session.commit()
                inserted_count = len(records)
                logger.info(f"Successfully inserted {inserted_count} records from {file_name}.")
                return inserted_count
            except SQLAlchemyError as e:
                db_session.rollback()
                logger.error(f"Database error during bulk insert from {file_name}. Rolled back. Error: {e}", exc_info=True)
                raise IOError(f"Database insertion failed for {file_name}. Check logs.") from e
            except Exception as e:
                 db_session.rollback()
                 logger.error(f"Unexpected error during bulk insert from {file_name}: {e}", exc_info=True)
                 raise RuntimeError(f"Unexpected error during database insert for {file_name}.") from e
        else:
            logger.info(f"No valid records to insert from {file_name}.")
            return 0

    except FileNotFoundError: raise
    except (ValueError, IOError, RuntimeError, TypeError) as e:
        logger.error(f"Failed to process {file_name} due to: {e}", exc_info=True)
        if db_session and db_session.is_active: db_session.rollback()
        raise
    except Exception as e:
        logger.error(f"An critical unexpected error occurred processing {file_name}: {str(e)}", exc_info=True)
        if db_session and db_session.is_active: db_session.rollback()
        raise RuntimeError(f"Critical unexpected error processing {file_name}.") from e
    finally:
        logger.info(f"Finished processing attempt for: {file_name}")