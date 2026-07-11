import threading
import webbrowser
import time
from waitress import serve
from app import create_app

app = create_app()

def open_browser():
    """Waits for the server to start, then opens the default web browser."""
    time.sleep(2)
    try:
        webbrowser.open('http://localhost:5000')
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

if __name__ == '__main__':
    # Start the browser automatically in a background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the Waitress production server
    print("==================================================")
    print("   UNILAB DIAGNOSTIC MANAGEMENT SYSTEM STARTED    ")
    print("==================================================")
    print("-> Local access (this computer): http://localhost:5000")
    print("-> LAN access (other computers): http://<THIS_COMPUTERS_IP>:5000")
    print("\nPress Ctrl+C to shut down the server.")
    
    serve(app, host='0.0.0.0', port=5000, threads=6)
