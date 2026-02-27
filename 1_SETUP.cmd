@echo off
setlocal

if not exist .venv (
  py -m venv .venv
  if errorlevel 1 (
    echo [ERROR] venv 생성 실패
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate
if errorlevel 1 (
  echo [ERROR] 가상환경 활성화 실패
  pause
  exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] pip 업그레이드 실패
  pause
  exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] requirements.txt 설치 실패
  pause
  exit /b 1
)

echo Setup complete.
pause
