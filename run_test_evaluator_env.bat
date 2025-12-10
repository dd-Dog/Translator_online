@echo off
REM 评估器环境测试启动脚本（Windows）
REM 自动使用 translator_eval 环境的 Python 运行测试

set EVAL_ENV=translator_eval

REM 尝试从配置文件读取环境名称
for /f "tokens=2 delims=:" %%a in ('findstr /C:"conda_env_name" config\evaluation.yaml 2^>nul') do (
    set EVAL_ENV=%%a
    set EVAL_ENV=!EVAL_ENV:"=!
    set EVAL_ENV=!EVAL_ENV: =!
)

REM 尝试多个可能的路径
set PYTHON_PATH=%USERPROFILE%\miniconda3\envs\%EVAL_ENV%\python.exe
if not exist "%PYTHON_PATH%" (
    set PYTHON_PATH=%USERPROFILE%\anaconda3\envs\%EVAL_ENV%\python.exe
)
if not exist "%PYTHON_PATH%" (
    set PYTHON_PATH=C:\Users\%USERNAME%\miniconda3\envs\%EVAL_ENV%\python.exe
)
if not exist "%PYTHON_PATH%" (
    set PYTHON_PATH=C:\Users\%USERNAME%\anaconda3\envs\%EVAL_ENV%\python.exe
)

if not exist "%PYTHON_PATH%" (
    echo [ERROR] 未找到 Python 环境: %EVAL_ENV%
    echo 尝试的路径:
    echo   %USERPROFILE%\miniconda3\envs\%EVAL_ENV%\python.exe
    echo   %USERPROFILE%\anaconda3\envs\%EVAL_ENV%\python.exe
    echo.
    echo 请检查:
    echo   1. conda 环境名称是否正确（当前: %EVAL_ENV%）
    echo   2. conda 是否安装在默认位置
    echo   3. 或手动编辑此脚本，设置正确的 Python 路径
    pause
    exit /b 1
)

echo ================================================================================
echo 使用评估器环境运行测试: %EVAL_ENV%
echo Python 路径: %PYTHON_PATH%
echo ================================================================================
echo.

"%PYTHON_PATH%" test_evaluator_env.py

pause

