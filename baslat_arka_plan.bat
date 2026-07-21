@echo off
cd /d "%~dp0"
title IT Saha Ziyaret Takip Arka Plan Sureci

:: Port 8501 ve 8502'yi kullanan eski surecleri temizle
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8502') do taskkill /f /pid %%a >nul 2>&1

:: Python onbellek temizligi
if exist __pycache__ rmdir /s /q __pycache__

:: Mobil Esitleme REST API Sunucusunu Arka Planda Baslat (Port 8502)
start /b "" "C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe" -c "import sync_server, time; sync_server.start_sync_server_once(8502); time.sleep(999999)"

:: Streamlit uygulamasini sessiz modda baslat (Port 8501)
"C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
