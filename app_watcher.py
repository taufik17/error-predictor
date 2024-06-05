from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import subprocess
import sys

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, app_process):
        self.app_process = app_process

    def on_modified(self, event):
        if event.src_path.endswith('.py') or event.src_path.endswith('.html'):
            print(f"File changed: {event.src_path}. Restarting server.")
            self.app_process.terminate()
            self.app_process.wait()  # Ensure the process has terminated before starting a new one
            self.app_process = subprocess.Popen([sys.executable, "app.py"])

if __name__ == "__main__":
    app_process = subprocess.Popen([sys.executable, "app.py"])
    event_handler = ReloadHandler(app_process)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    app_process.terminate()
