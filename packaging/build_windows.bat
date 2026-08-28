@echo off
REM ============================================
REM 小七 Windows 构建脚本
REM 用法: packaging\build_windows.bat
REM 生成: dist\xiaoqi\xiaoqi.exe
REM ============================================
setlocal

cd /d "%~dp0"

echo [1/3] 检查依赖...
python -c "import PyInstaller" 2>nul || (
  echo 安装 pyinstaller...
  pip install pyinstaller pywebview
)

echo [2/3] 构建 EXE...
pyinstaller xiaoqi.spec --noconfirm

echo [3/3] 完成
echo 输出: dist\xiaoqi\xiaoqi.exe
echo 测试: dist\xiaoqi\xiaoqi.exe

endlocal