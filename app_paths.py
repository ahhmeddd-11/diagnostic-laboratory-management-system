import os
import sys


# ==========================================================
# APPLICATION ROOT (Read-only files)
# ==========================================================
if getattr(sys, "frozen", False):
    exe_dir = os.path.dirname(sys.executable)

    # PyInstaller one-folder build stores resources in _internal
    internal_dir = os.path.join(exe_dir, "_internal")

    if os.path.isdir(internal_dir):
        APP_ROOT = internal_dir
    else:
        # Fallback for source or one-file builds
        APP_ROOT = exe_dir

else:
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))


# ==========================================================
# USER DATA DIRECTORY (Writable files)
# ==========================================================
APPDATA = os.getenv("APPDATA") or os.path.expanduser("~")

USER_DATA_DIR = os.path.join(APPDATA, "UnilabDiagnostics")


# ==========================================================
# CREATE REQUIRED FOLDERS
# ==========================================================
DATABASE_DIR = os.path.join(USER_DATA_DIR, "database")
MEDIA_DIR = os.path.join(USER_DATA_DIR, "media")
REPORTS_DIR = os.path.join(USER_DATA_DIR, "bulk_reports")
LOGS_DIR = os.path.join(USER_DATA_DIR, "logs")
CONFIG_DIR = os.path.join(USER_DATA_DIR, "config")

for folder in (
    USER_DATA_DIR,
    DATABASE_DIR,
    MEDIA_DIR,
    REPORTS_DIR,
    LOGS_DIR,
    CONFIG_DIR,
):
    os.makedirs(folder, exist_ok=True)


# ==========================================================
# READ-ONLY RESOURCE DIRECTORIES
# ==========================================================
STATIC_DIR = os.path.join(APP_ROOT, "static")
TEMPLATES_DIR = os.path.join(APP_ROOT, "templates")
ASSETS_DIR = os.path.join(APP_ROOT, "assets")


# ==========================================================
# COMMON FILES
# ==========================================================
WINDOW_STATE_FILE = os.path.join(CONFIG_DIR, "window_state.json")
STDOUT_LOG = os.path.join(LOGS_DIR, "stdout.log")
STDERR_LOG = os.path.join(LOGS_DIR, "stderr.log")
DB_CONFIG_FILE = os.path.join(CONFIG_DIR, "db_config.json")