import threading
import webbrowser
import time
import os
import sys
from waitress import serve

# Establish the settings module environment for Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unilab_project.settings')

# Boot up the Django application registry
import django
django.setup()

# Retrieve the WSGI application callable wrapped in StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

# Wrapping the WSGI app ensures Waitress serves static assets dynamically
application = StaticFilesHandler(get_wsgi_application())

def open_browser():
    """Waits for the Waitress server to start, then spawns the system's default browser."""
    time.sleep(2)
    try:
        webbrowser.open('http://localhost:8000')
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

if __name__ == '__main__':
    # Serve using the production Waitress server
    print("==================================================")
    print("   UNILAB DJANGO MANAGEMENT SYSTEM STARTED        ")
    print("==================================================")
    print("-> Local access (this computer): http://localhost:8000")
    print("\nPress Ctrl+C to shut down the server.")

    serve(application, host='0.0.0.0', port=8000, threads=6)
