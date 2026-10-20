@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title MediClear Cidar Hesabı

echo.
echo   MediClear - Daldırma Cidar Kalınlığı Hesabı
echo   ============================================
echo.

rem --- Program zaten açıksa yalnızca tarayıcıyı aç ---------------------------------
netstat -ano | findstr /r /c:":8501 .*LISTENING" >nul
if not errorlevel 1 goto :zaten_acik

rem --- Önceki kurulum bu bilgisayarda çalışıyor mu? (klasör taşınınca bozulur) -------
if not exist ".venv\Scripts\python.exe" goto :kurulum
".venv\Scripts\python.exe" -c "import streamlit, scipy, plotly, openpyxl" >nul 2>nul
if not errorlevel 1 goto :calistir
echo   Önceki kurulum bu bilgisayarda çalışmıyor; yeniden kurulacak.
rmdir /s /q ".venv"

:kurulum
call :python_bul
if not defined PY goto :python_yok
echo   İlk çalıştırma: gerekli paketler kuruluyor.
echo   İnternet bağlantısı gerekir ve birkaç dakika sürebilir.
echo   Lütfen bu pencereyi kapatma...
echo.
%PY% -m venv .venv
if errorlevel 1 goto :kurulum_hata
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 goto :kurulum_hata
echo   Kurulum tamamlandı.
echo.

:calistir
echo   Program açılıyor; tarayıcı birkaç saniye içinde kendiliğinden açılacak.
echo   Programı kapatmak için bu siyah pencereyi kapat.
echo.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 120;$i++){try{Invoke-WebRequest 'http://localhost:8501/_stcore/health' -UseBasicParsing -TimeoutSec 2 | Out-Null; Start-Process 'http://localhost:8501'; break}catch{Start-Sleep -Seconds 1}}"
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.address localhost
if errorlevel 1 goto :beklenmedik
exit /b 0

:zaten_acik
echo   Program zaten açık; tarayıcıda gösteriliyor.
start "" http://localhost:8501
timeout /t 3 >nul
exit /b 0

:python_bul
set "PY="
for %%V in (3.12 3.13 3.11 3.14) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V"
  )
)
if defined PY exit /b 0
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul && set "PY=python"
exit /b 0

:python_yok
echo   [HATA] Bu bilgisayarda Python 3.11 veya daha yenisi bulunamadı.
echo.
echo   1. https://www.python.org/downloads/ adresinden Python'u indir.
echo   2. Kurulumun ilk ekranında "Add python.exe to PATH" kutusunu MUTLAKA işaretle.
echo   3. Kurulum bitince bu dosyaya (baslat.bat) yeniden çift tıkla.
echo.
echo   Ayrıntı: KULLANIM.md dosyasındaki "1. Python kurulumu" bölümü.
echo.
pause
exit /b 1

:kurulum_hata
echo.
echo   [HATA] Paketler kurulamadı. İnternet bağlantını kontrol edip baslat.bat'ı yeniden çalıştır.
echo   Sorun sürerse klasördeki ".venv" klasörünü silip tekrar dene.
echo.
pause
exit /b 1

:beklenmedik
echo.
echo   Program beklenmedik şekilde kapandı. Yukarıdaki mesajı grup arkadaşlarınla paylaş.
echo.
pause
exit /b 1
