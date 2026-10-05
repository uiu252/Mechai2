"""Convenience launcher: reuse a running Merch AI instance or start a local server."""
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

ROOT=Path(__file__).resolve().parent
URL='http://127.0.0.1:8501'

def healthy():
    try:
        with urllib.request.urlopen(URL+'/_stcore/health',timeout=2) as response:
            return response.status==200
    except Exception: return False

def main():
    if healthy():
        print('A Streamlit app is already running at '+URL+'. Opening it.')
        webbrowser.open(URL)
        return
    def open_when_ready():
        for _ in range(45):
            if healthy(): webbrowser.open(URL);return
            time.sleep(1)
    threading.Thread(target=open_when_ready,daemon=True).start()
    print('Starting Merch AI. Leave this terminal open while you use the app.')
    print('Press Ctrl+C to stop. '+URL)
    try:
        subprocess.run([sys.executable,'-m','streamlit','run',str(ROOT/'app.py'),
            '--server.address','127.0.0.1','--server.port','8501','--server.headless','true'],cwd=ROOT,check=True)
    except KeyboardInterrupt: pass

if __name__=='__main__':main()
