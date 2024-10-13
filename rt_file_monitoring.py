import time
import os
import tkinter as tk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from plyer import notification
from FIC import FileIntegrityCheckerApp

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, files_to_monitor):
        # Convert all file paths to absolute paths to ensure correct matching
        self.files_to_monitor = {os.path.abspath(file) for file in files_to_monitor}

    def show_notification(self, title, message):
        """Show a system notification"""
        notification.notify(
            title=title,
            message=message,
            app_name="Integrisecure",
            timeout=3  # duration in seconds
        )

    def on_modified(self, event):
        if event.src_path in self.files_to_monitor:
            print(f"File modified: {event.src_path}")
            self.show_notification("File Modified", f"{event.src_path} was modified.")

    def on_created(self, event):
        if event.src_path in self.files_to_monitor:
            print(f"File created: {event.src_path}")
            self.show_notification("File Created", f"{event.src_path} was created.")

    def on_deleted(self, event):
        if event.src_path in self.files_to_monitor:
            print(f"File deleted: {event.src_path}")
            self.show_notification("File Deleted", f"{event.src_path} was deleted.")

    def on_moved(self, event):
        if event.src_path in self.files_to_monitor:
            print(f"File moved or renamed from {event.src_path} to {event.dest_path}")
            self.show_notification("File Moved", f"{event.src_path} was moved or renamed.")

def monitor_files(files_to_monitor):
    # Ensure all files exist
    for file in files_to_monitor:
        if not os.path.isfile(file):
            print(f"Warning: {file} does not exist and won't be monitored.")

    event_handler = FileChangeHandler(files_to_monitor)
    observer = Observer()
    
    # Monitor the parent directories of the files
    parent_directories = {os.path.dirname(os.path.abspath(file)) for file in files_to_monitor}
    
    for directory in parent_directories:
        print(f"Monitoring directory: {directory}")
        observer.schedule(event_handler, directory, recursive=False)

    observer.start()

    try:
        while True:
            time.sleep(1)  # Keep the script running
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    # Create a Tkinter root instance (needed to initialize the app)
    root = tk.Tk()
    # Create an instance of the FileIntegrityCheckerApp
    app = FileIntegrityCheckerApp(root)
    
    # Get the list of files to monitor
    files_to_monitor = app.get_files_to_check()
    
    # Close the Tkinter window (optional, as you might not need it for monitoring)
    root.destroy()  

    # Start monitoring the files
    monitor_files(files_to_monitor)
