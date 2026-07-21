@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set FLUTTER_BIN=C:\flutter\flutter_windows_3.44.7-stable\flutter\bin
set SDK_ROOT=C:\Android\Sdk
set CMDTOOLS_ROOT=%SDK_ROOT%\cmdline-tools\latest
set JDK_URL=https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.15+6/OpenJDK17U-jdk_x64_windows_hotspot_17.0.15_6.msi
set JDK_MSI=%TEMP%\jdk17.msi

title IT Saha Takip - Android APK Kurulum ve Derleme

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║   IT Saha Takip - Android APK Otomatik Kurulum ve Derleme      ║
echo ║   Bu pencereyi KAPATMAYIN - bitene kadar bekleyin!              ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

:: PATH ayarları
set PATH=%FLUTTER_BIN%;%PATH%

:: ─────────────────────────────────────────
:: ADIM 1: Java 17 JDK kontrolü ve kurulumu
:: ─────────────────────────────────────────
echo [1/5] Java 17 kontrolü yapılıyor...
java -version 2>&1 | findstr "17\." >nul 2>&1
if not errorlevel 1 (
    echo [OK] Java 17 mevcut.
    goto :check_sdk
)

echo [!] Java 17 bulunamadı. İndiriliyor (~160 MB)...
echo     Bu işlem internet hızınıza bağlı olarak 2-5 dakika sürebilir.
curl.exe -L --progress-bar -o "%JDK_MSI%" "%JDK_URL%"
if errorlevel 1 (
    echo [HATA] Java 17 indirilemedi. İnternet bağlantısını kontrol edin.
    pause & exit /b 1
)
echo [OK] İndirme tamamlandı. Kuruluyor...
msiexec /i "%JDK_MSI%" /qn ADDLOCAL=FeatureMain,FeatureEnvironment,FeatureJarFileRunWith,FeatureJavaHome REBOOT=Suppress
del "%JDK_MSI%" >nul 2>&1
:: Refresh PATH for java
for /f "tokens=*" %%i in ('where java 2^>nul') do set JAVA_EXE=%%i
if not defined JAVA_EXE (
    set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.15.6-hotspot
    set PATH=%JAVA_HOME%\bin;%PATH%
)
echo [OK] Java 17 kuruldu.

:check_sdk
:: ─────────────────────────────────────────
:: ADIM 2: Android Command Line Tools
:: ─────────────────────────────────────────
echo.
echo [2/5] Android SDK kontrolü...
if exist "%CMDTOOLS_ROOT%\bin\sdkmanager.bat" (
    echo [OK] Android SDK mevcut.
    goto :configure_flutter
)

echo [!] Android SDK bulunamadı. İndiriliyor (~150 MB)...
if not exist "%SDK_ROOT%" mkdir "%SDK_ROOT%"
if not exist "%CMDTOOLS_ROOT%" mkdir "%CMDTOOLS_ROOT%"
set CMDTOOLS_ZIP=%TEMP%\cmdtools.zip
curl.exe -L --progress-bar -o "%CMDTOOLS_ZIP%" "https://dl.google.com/android/repository/commandlinetools-win-13114758_latest.zip"
if errorlevel 1 (
    echo [HATA] Android SDK indirilemedi.
    pause & exit /b 1
)
echo [OK] İndirme tamamlandı. Çıkartılıyor...
powershell -command "Expand-Archive -Path '%CMDTOOLS_ZIP%' -DestinationPath '%TEMP%\cmdtools_ext' -Force"
xcopy /E /I /Y "%TEMP%\cmdtools_ext\cmdline-tools" "%CMDTOOLS_ROOT%" >nul 2>&1
if not exist "%CMDTOOLS_ROOT%\bin" xcopy /E /I /Y "%TEMP%\cmdtools_ext" "%CMDTOOLS_ROOT%" >nul 2>&1
del "%CMDTOOLS_ZIP%" >nul 2>&1
echo [OK] Android SDK hazır.

:configure_flutter
:: ─────────────────────────────────────────
:: ADIM 3: SDK paketleri kurulumu
:: ─────────────────────────────────────────
echo.
echo [3/5] Android SDK paketleri kuruluyor (platform-tools + Android 35)...
echo     Bu işlem 5-10 dakika sürebilir...
set ANDROID_HOME=%SDK_ROOT%
set PATH=%CMDTOOLS_ROOT%\bin;%SDK_ROOT%\platform-tools;%PATH%
echo y | "%CMDTOOLS_ROOT%\bin\sdkmanager.bat" --sdk_root="%SDK_ROOT%" "platform-tools" "platforms;android-35" "build-tools;35.0.0" 2>&1 | findstr /V "Downloading\|Unzipping\|Installing"
echo [OK] SDK paketleri kuruldu.

:: ─────────────────────────────────────────
:: ADIM 4: Flutter yapılandırması
:: ─────────────────────────────────────────
echo.
echo [4/5] Flutter Android yapılandırması...
setx ANDROID_HOME "%SDK_ROOT%" >nul 2>&1
"%FLUTTER_BIN%\flutter.bat" config --android-sdk "%SDK_ROOT%" --no-analytics >nul 2>&1
echo y | "%FLUTTER_BIN%\flutter.bat" doctor --android-licenses >nul 2>&1
echo [OK] Flutter yapılandırıldı.

:: ─────────────────────────────────────────
:: ADIM 5: APK derleme
:: ─────────────────────────────────────────
echo.
echo [5/5] APK derleniyor... (5-10 dakika sürebilir)
echo     İlk derleme Gradle indirmesi nedeniyle uzun sürebilir. Lütfen bekleyin.
cd it_saha_takip_mobile
"%FLUTTER_BIN%\flutter.bat" pub get 2>&1 | findstr /V "Downloading"
"%FLUTTER_BIN%\flutter.bat" build apk --release --no-shrink 2>&1
if errorlevel 1 (
    echo.
    echo [HATA] APK derlenemedi. Hata mesajını yukarıda okuyun.
    cd ..
    pause & exit /b 1
)
cd ..

:: APK'yı static klasörüne kopyala (telefondan indirilebilsin)
if exist "it_saha_takip_mobile\build\app\outputs\flutter-apk\app-release.apk" (
    copy /Y "it_saha_takip_mobile\build\app\outputs\flutter-apk\app-release.apk" "static\IT_Saha_Takip.apk" >nul
    echo [OK] APK static klasörüne kopyalandı.
)

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║  🎉 APK BAŞARIYLA DERLENDI!                                     ║
echo ║                                                                  ║
echo ║  APK Konumu:                                                     ║
echo ║  it_saha_takip_mobile\build\app\outputs\flutter-apk\            ║
echo ║  app-release.apk                                                 ║
echo ║                                                                  ║
echo ║  Telefona Kurulum İçin:                                          ║
echo ║  1. Bilgisayar uygulamasını başlatın (baslat_arka_plan.bat)     ║
echo ║  2. Telefonunuzdan tarayıcıyı açın ve şunu yazın:               ║
echo ║     http://[BİLGİSAYAR_IP]:8501/app/static/IT_Saha_Takip.apk   ║
echo ║  3. İndirin ve kurun (Bilinmeyen kaynak izni gerekebilir)        ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
pause
