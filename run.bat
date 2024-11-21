@echo off

:: 백엔드 실행
echo Starting Python backend...
start cmd /k "cd pyback && python -m pyback.main"

:: Flutter 실행
echo Starting Flutter frontend...
cd qr_scanner_app
flutter run

:: 종료 처리
echo Backend and frontend have been started.
pause
