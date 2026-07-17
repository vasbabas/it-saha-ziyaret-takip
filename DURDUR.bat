@echo off
title IT Saha Ziyaret Takip - Durdurucu
echo.
echo  ==================================================
echo   IT Saha Ziyaret ve Takip Otomasyonu Durdurucu
echo  ==================================================
echo.
echo  Port 8501'i kullanan Streamlit uygulamasi araniyor...
echo.

:: Port 8501'i dinleyen PID'yi bul ve zorla kapat
set "found=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501') do (
    taskkill /f /pid %%a >nul 2>&1
    set "found=1"
)

if "%found%"=="1" (
    echo  [TAMAM] Arka planda calisan Streamlit sureci sonlandirildi.
) else (
    echo  [BILGI] Port 8501'de calisan aktif bir surec bulunamadi.
)

echo.
echo  Uygulama durduruldu. Bu pencereyi kapatabilirsiniz.
echo.
pause
