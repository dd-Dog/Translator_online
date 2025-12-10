#!/bin/bash
# 评估器环境测试启动脚本（Linux/Mac）
# 自动使用 translator_eval 环境的 Python 运行测试

EVAL_ENV="translator_eval"
PYTHON_PATH="$HOME/miniconda3/envs/$EVAL_ENV/bin/python"

# 尝试其他可能的路径
if [ ! -f "$PYTHON_PATH" ]; then
    PYTHON_PATH="$HOME/anaconda3/envs/$EVAL_ENV/bin/python"
fi

if [ ! -f "$PYTHON_PATH" ]; then
    echo "[ERROR] 未找到 Python 环境: $PYTHON_PATH"
    echo "请检查 conda 环境名称是否正确"
    exit 1
fi

echo "================================================================================"
echo "使用评估器环境运行测试: $EVAL_ENV"
echo "Python 路径: $PYTHON_PATH"
echo "================================================================================"
echo ""

$PYTHON_PATH test_evaluator_env.py

