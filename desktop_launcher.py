"""
UNILAB DIAGNOSTICS - Standalone Desktop Launcher
This script orchestrates the startup sequence of the Unilab application:
1. Enforces single instance execution using a Windows named mutex and focuses the running app.
2. Starts the Django Waitress server in a background thread, silencing non-fatal server logs.
3. Displays a custom styled native Tkinter splash screen.
4. Polls the Django server health status and displays startup progress.
5. Restores the last window size and position or centers the window by default.
6. Launches a native, resizable PyWebView container (disabling dev tools).
7. Exits cleanly, releasing the port and threads upon closing.

PyInstaller Build Command Recommendation:
    pyinstaller --noconsole --onefile --icon=application.ico --name="UnilabSystem" desktop_launcher.py

Hidden Imports required for Django packaging:
    --hidden-import="django.contrib.admin"
    --hidden-import="django.contrib.auth"
    --hidden-import="django.contrib.contenttypes"
    --hidden-import="django.contrib.sessions"
    --hidden-import="django.contrib.messages"
    --hidden-import="django.contrib.staticfiles"
    --hidden-import="pymysql"
    --hidden-import="mysql.connector"

Data Assets to bundle:
    --add-data "static;static"
    --add-data "templates;templates"
    --add-data "database;database"
    --add-data "bulk_reports;bulk_reports"
"""

import os
import sys
import time
import socket
import threading
import json
import ctypes
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

from app_paths import (
    APP_ROOT,
    MEDIA_DIR,
    REPORTS_DIR,
    WINDOW_STATE_FILE,
    STDOUT_LOG,
    STDERR_LOG,
)

# Defer expensive imports to improve initial startup load speed
requests = None
webview = None

# Redirect stdout/stderr when packaged under --noconsole / windowed execution
if sys.stdout is None:
    sys.stdout = open(STDOUT_LOG, "w")
if sys.stderr is None:
    sys.stderr = open(STDERR_LOG, "w")

SERVER_URL = "http://127.0.0.1:8000"
mutex = None
window = None

# ==========================================
# WINDOWS SINGLE INSTANCE ENFORCEMENT
# ==========================================
def enforce_single_instance():
    global mutex
    try:
        # Set AppUserModelID to ensure taskbar grouping and icon display works
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("UnilabDiagnostics.LaboratorySystem.1.0")
    except Exception:
        pass

    CreateMutex = ctypes.windll.kernel32.CreateMutexW
    GetLastError = ctypes.windll.kernel32.GetLastError
    ERROR_ALREADY_EXISTS = 183
    MUTEX_NAME = "Local\\UnilabDiagnosticsMutex"
    
    mutex = CreateMutex(None, False, MUTEX_NAME)
    if GetLastError() == ERROR_ALREADY_EXISTS:
        # Existing instance running, focus and foreground the window
        hWnd = ctypes.windll.user32.FindWindowW(None, "UNILAB Diagnostic Laboratory Management System")
        if hWnd:
            ctypes.windll.user32.ShowWindow(hWnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hWnd)
        sys.exit(0)

# ==========================================
# WINDOW STATE PERSISTENCE (Size & Position)
# ==========================================
def get_window_state_path():
    return WINDOW_STATE_FILE

def load_window_state():
    path = get_window_state_path()
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_window_state(x, y, width, height):
    path = get_window_state_path()
    try:
        with open(path, 'w') as f:
            json.dump({'x': int(x), 'y': int(y), 'width': int(width), 'height': int(height)}, f)
    except Exception:
        pass

# ==========================================
# NATIVE DESKTOP SPLASH SCREEN WINDOW
# ==========================================
def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = APP_ROOT
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

class SplashWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)  # Frameless window
        self.attributes('-topmost', True)  # Always on top
        
        # Center splash window
        width = 700
        height = 420
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.configure(bg="#0F172A")
        
        icon_path = resource_path("assets/icons/logo.ico")

        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Load and resize logo proportionally using Pillow with LANCZOS resampling
        logo_path = resource_path("assets/images/logo.png")
        try:
            original_img = Image.open(logo_path)
            original_img.thumbnail((130, 130), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(original_img)
        except Exception:
            self.logo_img = None

        if self.logo_img:
            lbl_logo = tk.Label(self, image=self.logo_img, bg="#0F172A")
            lbl_logo.pack(pady=(45, 10))
        else:
            lbl_logo = tk.Label(self, text="UNILAB", font=("Segoe UI", 26, "bold"), fg="white", bg="#0F172A")
            lbl_logo.pack(pady=(45, 10))

        # Title Label: UNILAB (font 26 bold white)
        lbl_title = tk.Label(self, text="UNILAB", font=("Segoe UI", 26, "bold"), fg="white", bg="#0F172A")
        lbl_title.pack(pady=(0, 5))

        # Subtitle Label: Diagnostic Laboratory Management System (font 14, color #D1D5DB)
        lbl_subtitle = tk.Label(self, text="Diagnostic Laboratory Management System", font=("Segoe UI", 14), fg="#D1D5DB", bg="#0F172A")
        lbl_subtitle.pack(pady=(0, 5))

        # Version Label: Version 1.0.0 (font 11)
        lbl_version = tk.Label(self, text="Version 1.0.0", font=("Segoe UI", 11), fg="#9CA3AF", bg="#0F172A")
        lbl_version.pack(pady=(0, 15))

        # Initializing Label: Initializing application... (font 11)
        lbl_init = tk.Label(self, text="Initializing application...", font=("Segoe UI", 11), fg="#9CA3AF", bg="#0F172A")
        lbl_init.pack(pady=(0, 10))

        # Modern ttk Style for Progressbar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("blue.Horizontal.TProgressbar",
                        troughcolor="#1E293B",
                        background="#3B82F6",
                        lightcolor="#3B82F6",
                        darkcolor="#3B82F6",
                        bordercolor="#0F172A",
                        thickness=8)

        # Progressbar: Length 430, determinate
        self.progress_bar = ttk.Progressbar(self, style="blue.Horizontal.TProgressbar", length=430, mode="determinate")
        self.progress_bar.pack(pady=(0, 10))

        # Status Label: Loading modules...
        self.lbl_status = tk.Label(self, text="Loading modules...", font=("Segoe UI", 11), fg="#9CA3AF", bg="#0F172A")
        self.lbl_status.pack(pady=(0, 20))

        self.update()

    def update_progress(self, value, status_text):
        if not self.winfo_exists():
            return
        self.progress_bar['value'] = value
        self.lbl_status.config(text=status_text)
        self.update_idletasks()
        
    def set_status(self, text):
        if not self.winfo_exists():
            return
        self.lbl_status.config(text=text)
        self.update_idletasks()

# ==========================================
# SERVICE LAUNCH & CLEANUP MECHANISMS
# ==========================================
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def run_django_server():
    """Runs the Waitress server inside a background thread, silencing logs."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unilab_project.settings')
    
    # Silence waitress access logs
    import logging
    logging.getLogger('waitress').setLevel(logging.ERROR)
    
    import django
    django.setup()
    
    from django.core.wsgi import get_wsgi_application
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from waitress import serve
    
    application = StaticFilesHandler(get_wsgi_application())
    serve(application, host='127.0.0.1', port=8000, threads=6)

def start_server():
    if is_port_in_use(8000):
        # Port 8000 is occupied, abort and alert user
        messagebox.showerror("Conflict Error", "Port 8000 is already in use by another application. Please free the port before starting Unilab Diagnostics.")
        sys.exit(1)
        
    try:
        # Launch Django server thread in background (daemon mode)
        server_thread = threading.Thread(target=run_django_server, daemon=True)
        server_thread.start()
    except Exception as e:
        messagebox.showerror("Launch Error", f"Failed to start the Django application server:\n{str(e)}")
        sys.exit(1)

def set_window_icon():
    """Sets the native Windows window icon dynamically if application.ico exists."""
    time.sleep(1.2)
    hWnd = ctypes.windll.user32.FindWindowW(None, "UNILAB Diagnostic Laboratory Management System")

    icon_path = resource_path("assets/icons/logo.ico")
    if hWnd and os.path.exists(icon_path):
        try:
            # LoadIcon API to assign small and large icons
            hIcon = ctypes.windll.user32.LoadImageW(
                None,
                icon_path,
                1,
                0,
                0,
                0x00000010 | 0x00000020
            )  # IMAGE_ICON = 1, LR_LOADFROMFILE = 0x10, LR_DEFAULTSIZE = 0x20
            if hIcon:
                # Send WM_SETICON messages
                ctypes.windll.user32.SendMessageW(hWnd, 0x0080, 0, hIcon) # ICON_SMALL
                ctypes.windll.user32.SendMessageW(hWnd, 0x0080, 1, hIcon) # ICON_BIG
        except Exception:
            pass

# ==========================================
# MAIN EXECUTION ROUTINE
# ==========================================
if __name__ == "__main__":
    # Ensure only a single desktop instance runs
    enforce_single_instance()
    
    # Ensure media and reports directories are created automatically if missing
    os.makedirs(MEDIA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # Start Waitress server in a background thread
    start_server()
    
    # Run Tkinter splash screen loader
    splash = SplashWindow()
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    start_time = time.time()
    current_stage = 0
    transitioning = False
    
    def check_server_status():
        global requests, current_stage, transitioning
        
        if transitioning:
            return
            
        # Defer import of requests for faster startup
        if requests is None:
            import requests as _requests
            requests = _requests
            
        elapsed = time.time() - start_time
        
        # Determine current stage based on elapsed time (up to 70%)
        if current_stage < 3:
            if elapsed >= 2.0:
                current_stage = 3
            elif elapsed >= 1.2:
                current_stage = 2
            elif elapsed >= 0.4:
                current_stage = 1
            else:
                current_stage = 0
                
        # Update progress and status according to current stage
        if current_stage == 0:
            splash.update_progress(10, "Preparing environment")
        elif current_stage == 1:
            splash.update_progress(25, "Loading Django")
        elif current_stage == 2:
            splash.update_progress(45, "Starting Waitress")
        elif current_stage == 3:
            splash.update_progress(70, "Connecting to local server")
            
        # Check server status
        server_ready = False
        try:
            response = requests.get(SERVER_URL, timeout=1)
            if response.status_code == 200:
                server_ready = True
        except Exception:
            pass
            
        if server_ready:
            transitioning = True
            
            def set_ready():
                splash.update_progress(100, "Ready")
                splash.after(300, splash.quit)
                
            splash.update_progress(90, "Launching desktop interface")
            splash.after(150, set_ready)
            return
            
        # Check for server timeout (15 seconds)
        if elapsed > 15:
            splash.destroy()
            messagebox.showerror("Server Error", "Unable to start the UNILAB server.\n\nPlease verify your configuration and try again.")
            sys.exit(1)
            
        splash.after(200, check_server_status)
        
    splash.after(200, check_server_status)
    splash.mainloop()

    try:
        splash.destroy()
    except tk.TclError:
        pass
    
    # Defer import of webview
    if webview is None:
        import webview as _webview
        webview = _webview
        
    # Load last size and position if saved
    saved_state = load_window_state()
    kwargs = {
        'title': "UNILAB Diagnostic Laboratory Management System",
        'url': SERVER_URL,
        'width': saved_state.get('width', 1400) if saved_state else 1400,
        'height': saved_state.get('height', 900) if saved_state else 900,
        'min_size': (1200, 800),
        'resizable': True
    }
    
    if saved_state and 'x' in saved_state and 'y' in saved_state:
        # Validate that window is within screen boundaries before placing
        if 0 <= saved_state['x'] < screen_w and 0 <= saved_state['y'] < screen_h:
            kwargs['x'] = saved_state['x']
            kwargs['y'] = saved_state['y']
            
    # Initialize PyWebView main window
    window = webview.create_window(**kwargs)
    
    # Save window state coordinates on closing
    def on_closing():
        save_window_state(window.x, window.y, window.width, window.height)
        
    window.events.closing += on_closing
    
    # Thread to set window icon once created
    threading.Thread(target=set_window_icon, daemon=True).start()
    
    # Start PyWebView application loop (disable dev tools)
    webview.start(debug=False)