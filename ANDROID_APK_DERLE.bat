@echo off
setlocal enabledelayedexpansion

set FLUTTER_BIN=C:\flutter\flutter_windows_3.44.7-stable\flutter\bin
set SDK_ROOT=C:\Android\Sdk
set CMDTOOLS_ROOT=%SDK_ROOT%\cmdline-tools\latest
set JAVA17_HOME=C:\Program Files\Java\jdk-17

title IT Saha Takip - APK Build

echo.
echo ================================================
echo   IT Saha Takip - Android APK Derleme
echo   Bu pencereyi KAPATMAYIN!
echo ================================================
echo.

set PATH=%JAVA17_HOME%\bin;%FLUTTER_BIN%;%CMDTOOLS_ROOT%\bin;%SDK_ROOT%\platform-tools;%PATH%
set ANDROID_HOME=%SDK_ROOT%
set JAVA_HOME=%JAVA17_HOME%

REM ---- Java kontrol ----
echo [1/4] Java 17 kontrol ediliyor...
java -version 2>&1 | findstr "17\." >nul 2>&1
if errorlevel 1 (
    echo [HATA] Java 17 bulunamadi: %JAVA17_HOME%
    echo        Lutfen Java 17 JDK kurulu oldugundan emin olun.
    pause
    exit /b 1
)
echo [OK] Java 17 aktif.

REM ---- Android SDK kontrol ----
echo.
echo [2/4] Android SDK kontrol ediliyor...
if not exist "%CMDTOOLS_ROOT%\bin\sdkmanager.bat" (
    echo [HATA] Android SDK bulunamadi: %CMDTOOLS_ROOT%
    echo        ANDROID_APK_DERLE.bat'i tekrar calistirin.
    pause
    exit /b 1
)
echo [OK] Android SDK mevcut.

REM ---- Lisans kabul ----
echo.
echo [3/4] Flutter Android yapilandirmasi...
flutter config --android-sdk "%SDK_ROOT%" --no-analytics >nul 2>&1
echo y | flutter doctor --android-licenses >nul 2>&1
echo [OK] Lisanslar kabul edildi.

REM ---- APK derle ----
echo.
echo [4/4] APK derleniyor...
echo       Ilk seferinde Gradle indirecegi icin 10-20 dakika surebilir.
echo       Lutfen bekleyin, pencereyi kapatmayin!
echo.

cd it_saha_takip_mobile
flutter pub get
if errorlevel 1 (
    echo [HATA] flutter pub get basarisiz!
    cd ..
    pause
    exit /b 1
)

flutter build apk --release
if errorlevel 1 (
    echo.
    echo [HATA] APK derlenemedi!
    cd ..
    pause
    exit /b 1
)
cd ..

REM APK'yi static klasorune kopyala
if exist "it_saha_takip_mobile\build\app\outputs\flutter-apk\app-release.apk" (
    if not exist "static" mkdir "static"
    copy /Y "it_saha_takip_mobile\build\app\outputs\flutter-apk\app-release.apk" "static\IT_Saha_Takip.apk" >nul
    echo [OK] APK: static\IT_Saha_Takip.apk
)

echo.
echo ================================================
echo   APK BASARIYLA DERLENDI!
echo.
echo   Dosya: it_saha_takip_mobile\build\app\
echo          outputs\flutter-apk\app-release.apk
echo.
echo   Telefona kurmak icin:
echo   1. USB kablo ile kopyalayin
echo   2. VEYA tarayicidan:
echo      http://192.168.1.100:8501/app/static/IT_Saha_Takip.apk
echo ================================================
echo.
pause
