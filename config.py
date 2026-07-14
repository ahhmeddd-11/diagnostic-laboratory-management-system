import os
import json
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-diagnostic'
    
    # Defaults
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'diagnostic_lab'
    IS_CONFIGURED = False

    # Save config in APPDATA to survive PyInstaller temp dirs and avoid permission issues
    app_data_dir = os.getenv('APPDATA')
    if not app_data_dir:
        app_data_dir = os.path.expanduser('~')
    config_dir = os.path.join(app_data_dir, 'UnilabDiagnostics')
    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir)
        except Exception:
            pass
            
    config_path = os.path.join(config_dir, 'db_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                MYSQL_HOST = data.get('host', 'localhost')
                MYSQL_USER = data.get('user', 'root')
                MYSQL_PASSWORD = data.get('password', '')
                MYSQL_DB = data.get('database', 'diagnostic_lab')
                
                # Verify connection actually works
                import mysql.connector
                conn = mysql.connector.connect(
                    host=MYSQL_HOST,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    database=MYSQL_DB
                )
                conn.close()
                IS_CONFIGURED = True
        except Exception:
            IS_CONFIGURED = False
