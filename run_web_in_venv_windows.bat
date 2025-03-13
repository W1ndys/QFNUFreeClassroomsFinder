@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

REM 设置控制台字体和窗口标题
title 曲阜师范大学教室课表查询系统 - 网页版

echo ======================================
echo  曲阜师范大学教室课表查询系统 - 网页版
echo  By W1ndys
echo  https://github.com/W1ndys
echo ======================================
echo.

REM 检查venv目录是否存在
if not exist venv (
    echo Virtual environment does not exist. Please run create_venv_windows.bat first.
    exit /b 1
)

REM 激活虚拟环境
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM 检查是否成功激活
if errorlevel 1 (
    echo Failed to activate virtual environment. Please check venv directory.
    exit /b 1
)

echo Virtual environment activated.
echo.

REM 自动打开浏览器访问网页
echo 正在打开浏览器...
start http://127.0.0.1:5000

REM 运行网页应用
echo Starting web service...
python run_web.py

REM 如果程序异常退出，保持窗口打开
if errorlevel 1 (
    echo.
    echo Program exited with error code: %errorlevel%
    pause
)

REM 退出虚拟环境
call venv\Scripts\deactivate.bat

endlocal 