@echo off
cd /d "%~dp0"
title IT Saha Ziyaret Takip Arka Plan Sureci

:: Python onbellek temizligi
if exist __pycache__ rmdir /s /q __pycache__

:: Streamlit uygulamasini sessiz modda baslat
python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
