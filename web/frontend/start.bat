@echo off
echo ====================================
echo 启动前端开发服务器
echo ====================================
echo.

cd /d %~dp0

echo 检查Node.js...
node --version
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

echo.
echo 检查依赖...
if not exist "node_modules" (
    echo 依赖未安装，正在安装...
    call npm install
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动开发服务器...
echo 访问地址: http://localhost:3000
echo.
echo 按 Ctrl+C 停止服务
echo.

npm run dev

pause

