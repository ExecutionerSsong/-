@echo off
chcp 65001 > nul
title 刃桌宠-启动脚本
set "CONDA_EXE="

:: 自动查找Conda路径，适配Anaconda/Miniconda
for /f "delims=" %%i in ('where conda 2^>nul') do (
    set "CONDA_EXE=%%i"
    goto :find_conda
)
:find_conda
if not defined CONDA_EXE (
    echo 错误：未找到Conda环境，请确认已安装Anaconda/Miniconda！
    pause
    exit /b 1
)

:: 提取Anaconda根目录并激活刃桌宠环境
set "CONDA_PATH=%CONDA_EXE:\Scripts\conda.exe=%"
call "%CONDA_PATH%\Scripts\activate.bat" xilian-pet > nul

:: 检查环境激活状态
if not "%CONDA_DEFAULT_ENV%"=="xilian-pet" (
    echo 错误：激活xilian-pet环境失败，请手动在终端执行 conda activate xilian-pet
    pause
    exit /b 1
)

:: 运行桌宠（自动定位当前文件夹的main.py）
echo 正在召唤刃桌宠...
python "%~dp0main.py"

exit /b 0