@echo off
echo ======================================
echo  테리크 지식인 시스템 - 초기 설정
echo ======================================
echo.

echo [1/3] Python 가상환경 생성 중...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo [2/3] 패키지 설치 중...
pip install -r requirements.txt

echo.
echo [3/3] 환경 변수 파일 생성 중...
if not exist .env (
    copy .env.example .env
    echo .env 파일이 생성되었습니다.
    echo .env 파일을 열어서 API 키를 입력하세요!
) else (
    echo .env 파일이 이미 존재합니다.
)

echo.
echo ======================================
echo  설정 완료!
echo.
echo  다음 단계:
echo  1. .env 파일을 메모장으로 열기
echo  2. 네이버 API, Claude API, 이메일 설정 입력
echo  3. run.bat 실행
echo ======================================
pause
