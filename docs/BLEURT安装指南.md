# BLEURT 安装指南

## 问题说明

如果你看到以下错误：
```
❌ 请安装BLEURT: pip install bleurt
⚠️  BLEURT模型加载失败，将跳过
```

或者：
```
ModuleNotFoundError: No module named 'tensorflow'
```

这是因为 **BLEURT 需要 TensorFlow 作为依赖**，但环境中没有安装。

## 安装步骤

### 1. 激活评估器环境

```bash
conda activate translator_eval
```

### 2. 安装 TensorFlow

**选项1: 安装完整版 TensorFlow（推荐，如果有 GPU）**
```bash
pip install tensorflow
```

**选项2: 安装 CPU 版本（如果只有 CPU 或想节省空间）**
```bash
pip install tensorflow-cpu
```

### 3. 验证安装

```bash
python -c "import tensorflow as tf; print('TensorFlow版本:', tf.__version__)"
```

### 4. 验证 BLEURT

```bash
python -c "from bleurt import score; print('BLEURT可用')"
```

## 完整安装命令

```bash
# 激活环境
conda activate translator_eval

# 安装 TensorFlow（CPU版本，更轻量）
pip install tensorflow-cpu

# 验证
python -c "import tensorflow; from bleurt import score; print('✅ BLEURT 已就绪')"
```

## 系统要求

- **TensorFlow**: >= 1.15.0（BLEURT 要求）
- **Python**: 3.7-3.10（TensorFlow 兼容性）
- **内存**: 建议 8GB+（BLEURT 模型较大）

## 常见问题

### Q: 应该安装哪个版本的 TensorFlow？

A: 
- 如果有 NVIDIA GPU 且已安装 CUDA/cuDNN：使用 `tensorflow`（GPU 版本）
- 如果只有 CPU 或不确定：使用 `tensorflow-cpu`（更轻量，安装更快）

### Q: TensorFlow 安装失败怎么办？

A: 
1. 检查 Python 版本（建议 3.8-3.10）
2. 尝试使用 conda 安装：`conda install tensorflow`
3. 如果网络问题，使用国内镜像：
   ```bash
   pip install tensorflow-cpu -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### Q: BLEURT 模型下载失败？

A: BLEURT 会自动下载模型文件（约 500MB）。如果下载失败：
1. 检查网络连接
2. 配置 HuggingFace 镜像或代理
3. 手动下载模型到缓存目录

### Q: 安装后仍然报错？

A: 
1. 确认在正确的环境中：`conda activate translator_eval`
2. 重新运行测试脚本
3. 检查错误信息，确认是 TensorFlow 问题还是其他问题

## 验证安装

运行测试脚本：
```bash
python test_evaluator_env.py
```

应该看到：
```
[OK] BLEURT 模块可用
[OK] TensorFlow 已安装（版本: x.x.x）
✓ BLEURT模型加载成功
✅ BLEURT模型已加载
```

## 参考

- [BLEURT GitHub](https://github.com/google-research/bleurt)
- [TensorFlow 安装指南](https://www.tensorflow.org/install)

