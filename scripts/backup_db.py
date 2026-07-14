import os
import time
import subprocess
import logging
import sys
from datetime import datetime

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Determine a safe, user-writable backup directory (Documents folder)
documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')
backup_dir = os.path.join(documents_dir, 'Unilab Backups')

try:
    os.makedirs(backup_dir, exist_ok=True)
except Exception as e:
    # Fallback to APPDATA if Documents fails
    app_data_dir = os.getenv('APPDATA') or os.path.expanduser('~')
    backup_dir = os.path.join(app_data_dir, 'UnilabDiagnostics', 'Backups')
    os.makedirs(backup_dir, exist_ok=True)

# Set up logging
log_file = os.path.join(backup_dir, 'backup_log.txt')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def backup_database():
    """Dumps the MySQL database and prunes old backups."""
    
    db_host = Config.MYSQL_HOST
    db_user = Config.MYSQL_USER
    db_pass = Config.MYSQL_PASSWORD
    db_name = Config.MYSQL_DB
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_file = os.path.join(backup_dir, f'backup_{db_name}_{timestamp}.sql')
    
    # Locate mysqldump (assumes it is in PATH or standard MySQL installation)
    mysqldump_cmd = f'mysqldump -h {db_host} -u {db_user} -p"{db_pass}" {db_name} > "{backup_file}"'
    
    logging.info(f"Starting backup for database: {db_name}")
    
    try:
        # We use shell=True because we are redirecting output (>)
        result = subprocess.run(mysqldump_cmd, shell=True, check=True, stderr=subprocess.PIPE)
        logging.info(f"Backup successful: {backup_file}")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        logging.error(f"Backup failed: {error_msg}")
        print(f"Error during backup: {error_msg}")
        return
        
    # Prune old backups (keep only last 7)
    cleanup_old_backups(7)

def cleanup_old_backups(keep_count):
    """Keeps the most recent `keep_count` backups and deletes the rest."""
    try:
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.sql'):
                filepath = os.path.join(backup_dir, filename)
                backups.append((filepath, os.path.getctime(filepath)))
                
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x[1], reverse=True)
        
        # Delete backups beyond the keep_count
        if len(backups) > keep_count:
            for old_backup in backups[keep_count:]:
                os.remove(old_backup[0])
                logging.info(f"Pruned old backup: {old_backup[0]}")
    except Exception as e:
        logging.error(f"Error during backup pruning: {e}")

if __name__ == "__main__":
    backup_database()

