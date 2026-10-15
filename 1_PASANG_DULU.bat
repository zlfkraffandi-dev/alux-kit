@echo off
setlocal
title ALUX Kit - Pasang
echo === ALUX Kit: pasang (aman diulang) ===
set "HB=%LOCALAPPDATA%\hermes\bridge"
set "EXT=%APPDATA%\Adobe\CEP\extensions\com.hermes.bridge"
set "SK=%LOCALAPPDATA%\hermes\skills\productivity\alux-pick-ingest"
set "KIT=%~dp0"

where python >nul 2>nul || (echo [GAGAL] Python tidak ada di PATH. Pasang Hermes/Python dulu. & pause & exit /b 1)
where ffprobe >nul 2>nul || if not exist "%LOCALAPPDATA%\hermes\tools\ffmpeg*" echo [PERINGATAN] ffprobe/ffmpeg tidak ketemu. Pasang ffmpeg dan masukkan ke PATH.

echo 1/5 Python websockets...
python -m pip install --quiet websockets || (echo [GAGAL] pip install websockets & pause & exit /b 1)

echo 2/5 Hermes Bridge (script)...
if not exist "%HB%" mkdir "%HB%"
if not exist "%HB%\hermes_bridge.py" (copy /y "%KIT%bridge\hermes_bridge.py" "%HB%\" >nul & echo   dipasang) else echo   sudah ada, tidak ditimpa

echo 3/5 Panel Premiere...
if not exist "%EXT%\index.html" (xcopy /e /i /y /q "%KIT%panel" "%EXT%" >nul & echo   dipasang) else echo   sudah ada, tidak ditimpa

echo 4/5 PlayerDebugMode (panel tak bertanda tangan boleh jalan)...
for %%V in (9 10 11 12 13) do reg add "HKCU\Software\Adobe\CSXS.%%V" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul

echo 5/5 Skill + skrip ingest...
if not exist "%SK%\scripts" mkdir "%SK%\scripts"
copy /y "%KIT%skill\SKILL.md" "%SK%\" >nul
copy /y "%KIT%ingest.py" "%SK%\scripts\" >nul

echo.
echo SELESAI. Langkah berikut:
echo  1. RESTART Premiere, buka salinan master.
echo  2. Window ^> Extensions ^> Hermes Bridge  (biarkan tab ini TERLIHAT di depan).
echo  3. Klik sekali di timeline supaya sequence aktif.
echo  4. Double-click 2_BUKA_CHROME.bat, login Envato di jendela itu.
echo  5. Bilang ke Hermes: "ingest footage dari folder pilihan saya".
if /i not "%1"=="nopause" pause
