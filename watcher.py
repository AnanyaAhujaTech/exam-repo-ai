import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import your pipeline trigger
from pipeline.orchestrator import process_exam_async

INBOX_DIR = "Inbox"
os.makedirs(INBOX_DIR, exist_ok=True)

class ExamDropHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Ignore directory creations, we only care about files
        if event.is_directory:
            return
            
        # Only process PDFs or DOCX files
        if event.src_path.lower().endswith(('.pdf', '.docx')):
            # CRITICAL: Wait 2 seconds to ensure the OS has finished copying the file
            # before our pipeline tries to open and read it.
            time.sleep(2) 
            
            print(f"New file detected in Inbox: {event.src_path}")
            # Trigger the background pipeline!
            process_exam_async(event.src_path)

def start_watcher():
    """Starts the background watchdog observer."""
    observer = Observer()
    event_handler = ExamDropHandler()
    
    # Schedule the watcher on the Inbox folder
    observer.schedule(event_handler, INBOX_DIR, recursive=False)
    observer.start()
    
    print(f"Watchdog started. Listening for new files in './{INBOX_DIR}'...")
    return observer
