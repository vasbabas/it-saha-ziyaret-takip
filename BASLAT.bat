@echo off
title IT Saha Ziyaret Takip Uygulamasi
echo.
echo  ==========================================
echo   IT Saha Ziyaret ve Takip Uygulamasi
echo  ==========================================
echo.
echo  [1/3] Python onbellek temizleniyor...
if exist __pycache__ rmdir /s /q __pycache__
echo  [2/3] AG erisimi icin port 8501 aciliyor...
netsh advfirewall firewall add rule name="IT Saha Takip 8501" dir=in action=allow protocol=TCP localport=8501 >nul 2>&1
echo  [3/3] Uygulama baslatiliyor...
echo.
echo  Bu bilgisayardan : http://localhost:8501
echo  Ayni agdaki diger : http://192.168.1.100:8501
echo.
python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
pause
