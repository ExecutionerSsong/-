@echo off
chcp 65001 > nul
title 刃桌宠-打包EXE脚本
set "CONDA_EXE="
set "PROJECT_PATH=%~dp0"

:: 自动查找Conda
for /f "delims=" %%i in ('where conda 2^>nul') do (
    set "CONDA_EXE=%%i"
    goto :find_conda
)
:find_conda
if not defined CONDA_EXE (
    echo 错误：未找到Conda环境！
    pause
    exit /b 1
)

:: 激活环境
set "CONDA_PATH=%CONDA_EXE:\Scripts\conda.exe=%"
call "%CONDA_PATH%\Scripts\activate.bat" xilian-pet > nul
if not "%CONDA_DEFAULT_ENV%"=="xilian-pet" (
    echo 错误：激活环境失败！
    pause
    exit /b 1
)

:: 安装/更新pyinstaller
echo 正在安装打包工具...
pip install pyinstaller -q --upgrade

:: 打包为单EXE，隐藏控制台，设置图标
echo 正在打包刃桌宠...
pyinstaller -w -F -i "%PROJECT_PATH%resource\icon.ico" "%PROJECT_PATH%main.py" ^
--distpath "%PROJECT_PATH%dist" ^
--workpath "%PROJECT_PATH%build" ^
--specpath "%PROJECT_PATH%build" ^
--noconfirm

:: 打包完成提示
if exist "%PROJECT_PATH%dist\main.exe" (
    echo ==============================================
    echo ✅ 打包成功！EXE路径：%PROJECT_PATH%dist\main.exe
    echo ⚠️  关键：将resource文件夹复制到main.exe同目录！
    echo ==============================================
) else (
    echo ❌ 打包失败，请检查PyCharm终端报错信息！
)
pause
exit /b 0