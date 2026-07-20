@echo off
title Masaustune Kisayol Olusturuluyor...
cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'IT Saha Takip Otomasyonu.lnk')); $s.TargetPath = '%~dp0BASLAT_SESSİZ.vbs'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = 'shell32.dll, 14'; $s.Save()"

echo  ======================================================
echo   Masaustune 'IT Saha Takip Otomasyonu' Kisayolu Eklendi!
echo  ======================================================
