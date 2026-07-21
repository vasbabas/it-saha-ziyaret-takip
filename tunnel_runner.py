"""
tunnel_runner.py
----------------
Cloudflare Tunnel uzerinden Streamlit (Port 8501) ve Sync API (Port 8502) icin
otomatik HTTPS baglantisi olusturur.
"""

import subprocess
import re
import os
import time

def start_tunnels():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cloudflared = os.path.join(base_dir, "cloudflared.exe")
    
    if not os.path.exists(cloudflared):
        print("cloudflared.exe bulunamadi.")
        return

    # 1. Streamlit Tunnel (Port 8501)
    cmd_app = [cloudflared, "tunnel", "--url", "http://localhost:8501"]
    proc_app = subprocess.Popen(cmd_app, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore')

    # 2. Sync API Tunnel (Port 8502)
    cmd_sync = [cloudflared, "tunnel", "--url", "http://localhost:8502"]
    proc_sync = subprocess.Popen(cmd_sync, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore')

    url_file_app = os.path.join(base_dir, ".cloudflare_tunnel_url")
    url_file_sync = os.path.join(base_dir, ".cloudflare_sync_url")

    def monitor(proc, url_file, label):
        found = False
        for line in proc.stdout:
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match and not found:
                url = match.group(0)
                found = True
                with open(url_file, "w", encoding="utf-8") as f:
                    f.write(url)
                print(f"[{label} HTTPS TUNNEL]: {url}")
        proc.wait()

    import threading
    t1 = threading.Thread(target=monitor, args=(proc_app, url_file_app, "STREAMLIT"), daemon=True)
    t2 = threading.Thread(target=monitor, args=(proc_sync, url_file_sync, "SYNC_API"), daemon=True)
    t1.start()
    t2.start()

    print("Cloudflare tünelleri başlatıldı. HTTPS URL'leri üretiliyor...")
    time.sleep(3)

if __name__ == "__main__":
    start_tunnels()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
