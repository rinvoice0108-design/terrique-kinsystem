@echo off
echo ======================================
echo  테리크 지식인 모니터링 시스템 시작
echo ======================================
echo.
call venv\Scripts\activate.bat
echo  서버 주소: http://localhost:5000
echo  종료하려면 Ctrl+C 를 누르세요
echo.
python app.py
pause
