@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║     IT Saha Takip - Android SDK Otomatik Kurulum        ║
echo ║     Bu pencereyi KAPATMAYIN, bitene kadar bekleyin.     ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

set FLUTTER_BIN=C:\flutter\flutter_windows_3.44.7-stable\flutter\bin
set SDK_ROOT=C:\Android\Sdk
set CMDTOOLS_ROOT=%SDK_ROOT%\cmdline-tools\latest
set CMDTOOLS_ZIP=%TEMP%\cmdline-tools.zip

:: Flutter PATH
set PATH=%FLUTTER_BIN%;%PATH%

:: Java kontrolü
echo [1/6] Java kontrolü yapılıyor...
java -version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Java bulunamadı! Java 17 JDK kurulumu gerekiyor.
    echo Şu adresten indirin: https://adoptium.net/
    pause
    exit /b 1
)
echo [OK] Java bulundu.

:: Android SDK klasörü oluştur
echo.
echo [2/6] Android SDK klasörü oluşturuluyor: %SDK_ROOT%
if not exist "%SDK_ROOT%" mkdir "%SDK_ROOT%"
if not exist "%CMDTOOLS_ROOT%" mkdir "%CMDTOOLS_ROOT%"

:: Command Line Tools indir
echo.
echo [3/6] Android Command Line Tools indiriliyor (~150 MB)...
echo     Lütfen bekleyin, internet hızınıza göre birkaç dakika sürebilir.
curl.exe -L -o "%CMDTOOLS_ZIP%" "https://dl.google.com/android/repository/commandlinetools-win-13114758_latest.zip"
if errorlevel 1 (
    echo [HATA] İndirme başarısız oldu. İnternet bağlantınızı kontrol edin.
    pause
    exit /b 1
)
echo [OK] İndirme tamamlandı.

:: Zip çıkart
echo.
echo [4/6] Dosyalar çıkartılıyor...
powershell -command "Expand-Archive -Path '%CMDTOOLS_ZIP%' -DestinationPath '%TEMP%\cmdtools_extracted' -Force"
if exist "%TEMP%\cmdtools_extracted\cmdline-tools\bin" (
    xcopy /E /I /Y "%TEMP%\cmdtools_extracted\cmdline-tools" "%CMDTOOLS_ROOT%" >nul
) else (
    xcopy /E /I /Y "%TEMP%\cmdtools_extracted" "%CMDTOOLS_ROOT%" >nul
)
del "%CMDTOOLS_ZIP%" >nul 2>&1
echo [OK] Çıkartma tamamlandı.

:: SDK lisanslarını kabul et ve paketleri kur
echo.
echo [5/6] Android SDK paketleri kuruluyor (platform-tools + Android 35)...
echo     Bu işlem ~5-10 dakika sürebilir. Lütfen bekleyin...
set ANDROID_HOME=%SDK_ROOT%
set PATH=%CMDTOOLS_ROOT%\bin;%SDK_ROOT%\platform-tools;%PATH%

echo y | "%CMDTOOLS_ROOT%\bin\sdkmanager.bat" --sdk_root="%SDK_ROOT%" "platform-tools" "platforms;android-35" "build-tools;35.0.0" 2>&1

:: Flutter'a Android SDK yerini söyle
echo.
echo [6/6] Flutter Android SDK yapılandırması...
"%FLUTTER_BIN%\flutter.bat" config --android-sdk "%SDK_ROOT%" --no-analytics
echo y | "%FLUTTER_BIN%\flutter.bat" doctor --android-licenses

:: PATH'e kalıcı ekle
setx ANDROID_HOME "%SDK_ROOT%" /M >nul 2>&1
setx PATH "%PATH%;%SDK_ROOT%\platform-tools;%CMDTOOLS_ROOT%\bin" /M >nul 2>&1

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║  ✅ Android SDK kurulumu tamamlandı!                    ║
echo ║  Şimdi ANDROID_APK_DERLE.bat dosyasını çalıştırın.     ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
pause
