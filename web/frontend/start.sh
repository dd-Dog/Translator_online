#!/bin/bash

echo "===================================="
echo "启动前端开发服务器"
echo "===================================="
echo

cd "$(dirname "$0")"

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请先安装Node.js"
    exit 1
fi

echo "Node.js版本: $(node --version)"
echo

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "依赖未安装，正在安装..."
    npm install
    if [ $? -ne 0 ]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
fi

echo "启动开发服务器..."
echo "访问地址: http://localhost:3000"
echo
echo "按 Ctrl+C 停止服务"
echo

npm run dev

