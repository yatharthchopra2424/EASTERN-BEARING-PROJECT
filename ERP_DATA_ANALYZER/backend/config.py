import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file if present
load_dotenv()

class Config:
    # General Flask/App settings (though not Flask, SECRET_KEY is good practice)
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-very-secret-key-please-change')

    # Project Root Directory
    # Assumes config.py is in streamlit_app subdirectory
    PROJECT_ROOT = Path(__file__).parent.parent.resolve()

    # Instance folder for database, logs etc. (relative to project root)
    INSTANCE_PATH = os.getenv('INSTANCE_PATH', str(PROJECT_ROOT / 'instance'))

    # Upload folder for incoming CSVs (relative to project root)
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(PROJECT_ROOT / 'uploads'))

    # Allowed file extensions (lowercase)
    ALLOWED_EXTENSIONS = {'csv'}

    # Logging level
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

    # Database Configuration
    # Using SQLite located in the instance folder
    # Define the main database URI (even if using binds primarily)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(INSTANCE_PATH, "main_app.sqlite")}' # Not actively used if binds cover all models

    # Define specific database binds
    SQLALCHEMY_BINDS = {
        'grd': f'sqlite:///{os.path.join(INSTANCE_PATH, "grd_db.sqlite")}'
        # Add other binds here if needed, e.g.:
        # 'another_db': 'postgresql://user:password@host/dbname'
    }

    # SQLAlchemy performance setting
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Ensure instance and upload paths exist
    @staticmethod
    def ensure_paths_exist():
        paths_to_check = [Config.INSTANCE_PATH, Config.UPLOAD_FOLDER]
        for path in paths_to_check:
            try:
                Path(path).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                # Log error if directory creation fails
                # Using print here as logger might not be configured yet
                print(f"Error creating directory {path}: {e}")


# Automatically ensure paths exist when Config class is defined
Config.ensure_paths_exist()