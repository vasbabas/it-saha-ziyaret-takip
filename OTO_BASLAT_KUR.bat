@echo off
title IT Saha Ziyaret Takip - Otomatik Baslangic Kurulumu
chcp 65001 >nul
cd /d "%~dp0"

echo  ==================================================
echo   IT Saha Ziyaret ve Takip Otomasyonu
echo   Otomatik Baslangic (Windows Startup) Kurulumu
echo  ==================================================
echo.
echo   Bu arac, bilgisayariniz her acildiginda uygulamanin
echo   arka planda otomatik ve sessizce baslamasini saglar.
echo   Böylece siteye tarayicinizdan her an ulasabilirsiniz.
echo.

set "startup_folder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "vbs_file=%startup_folder%\IT_Saha_Takip_OtoBaslat.vbs"

:: Otomatik baslatma VBScript dosyasini Windows Baslangic (Startup) klasorune olustur
echo Set WshShell = CreateObject("WScript.Shell") > "%vbs_file%"
echo WshShell.CurrentDirectory = "%~dp0" >> "%vbs_file%"
echo WshShell.Run "cmd.exe /c baslat_arka_plan.bat", 0, false >> "%vbs_file%"

echo  [TAMAM] Otomatik baslatma kisayolu Windows Baslangic klasorune eklendi!
echo  Yol: %vbs_file%
echo.
echo  Artık bilgisayariniz her acildiginda uygulama arka planda otomatik calisacaktir.
echo  Denemek icin bilgisayarinizi yeniden baslatabilir veya
echo  uygulamayi hemen baslatmak icin 'BASLAT_SESSİZ.vbs' dosyasini calistirabilirsiniz.
echo.
pause
