# 评估API快速开始指南

## 📋 概述

V3.0 版本支持通过HTTP API调用评估服务，实现翻译与评估环境的完全分离。

## 🚀 快速开始

### 步骤1: 启动评估API服务

在评估环境中启动API服务：

```bash
# 激活评估环境
conda activate translator_eval

# 启动API服务
python eval_server.py

# 或指定端口
python eval_server.py --port 5001
```

服务启动后会显示：
```
 * Running on http://0.0.0.0:5001
```

### 步骤2: 配置翻译模块

编辑 `config/evaluation.yaml`，启用API模式：

```yaml
api:
  enabled: true
  base_url: "http://localhost:5001"
  timeout: 300
```

### 步骤3: 在代码中使用

```python
from src.utils.evaluation_service import create_evaluation_service

# 创建评估服务（自动从配置文件读取，使用API模式）
eval_service = create_evaluation_service()

# 评估翻译
result = eval_service.evaluate(
    translation="机器学习是人工智能的一个子集。",
    reference="机器学习是人工智能的一个子集。",
    source="Machine learning is a subset of AI."
)

if result:
    print(f"综合评分: {result['final_score']:.4f}")
    print(f"BLEU: {result['bleu']:.4f}")
    print(f"COMET: {result['comet']:.4f}")
    print(f"BERTScore: {result['bertscore_f1']:.4f}")
```

### 步骤4: 运行集成示例

```bash
# 确保评估API服务已启动（步骤1）

# 运行集成示例
python examples/translation_with_eval_api.py
```

## 📝 完整示例

### 示例1: 翻译并评估

```python
import asyncio
from src.agents.pipeline import TranslationPipeline
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel
from src.models.qwen import QwenModel
from src.utils.evaluation_service import create_evaluation_service
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    # 1. 创建翻译Pipeline
    pipeline = TranslationPipeline(
        planner_model=OpenAIModel(...),
        translator_a_model=GeminiModel(...),
        translator_b_model=QwenModel(...),
        checker_model=OpenAIModel(...),
        stylist_model=QwenModel(...),
        aggregator_model=OpenAIModel(...)
    )
    
    # 2. 执行翻译
    result = await pipeline.translate(
        text="Machine learning is a subset of AI.",
        source_lang="en",
        target_lang="zh"
    )
    
    # 3. 创建评估服务
    eval_service = create_evaluation_service()
    
    # 4. 评估翻译质量
    eval_result = eval_service.evaluate(
        translation=result.translated_text,
        reference="机器学习是人工智能的一个子集。",
        source="Machine learning is a subset of AI."
    )
    
    print(f"翻译: {result.translated_text}")
    print(f"评分: {eval_result['final_score']:.4f}")

asyncio.run(main())
```

### 示例2: 批量评估

```python
from src.utils.eval_api_client import EvaluationAPIClient

client = EvaluationAPIClient(base_url="http://localhost:5001")

scores = client.evaluate_batch(
    translations=["翻译1", "翻译2", "翻译3"],
    references=["参考1", "参考2", "参考3"]
)

for i, score in enumerate(scores):
    print(f"样本 {i+1}: {score.final_score:.4f}")
```

## 🔧 配置选项

### API配置 (`config/evaluation.yaml`)

```yaml
api:
  enabled: true              # 启用API模式
  base_url: "http://localhost:5001"  # API服务器地址
  timeout: 300              # 请求超时（秒）
  api_key: null             # API密钥（可选，用于认证）
```

### 环境变量

也可以使用环境变量：

```bash
export EVAL_API_URL="http://localhost:5001"
export EVAL_API_KEY="your-api-key"
```

## 🐛 故障排除

### 问题1: 无法连接到评估服务

**错误**: `Connection refused` 或 `评估API服务不可用`

**解决**:
1. 检查评估API服务是否已启动
2. 检查服务地址是否正确（`config/evaluation.yaml`）
3. 检查防火墙设置

### 问题2: 评估请求超时

**错误**: `Request timeout`

**解决**:
1. 增加超时时间: `timeout: 600`（在配置文件中）
2. 检查网络连接
3. 首次使用COMET需要下载模型，需要等待

### 问题3: 评估结果为空

**错误**: `评估失败` 或返回 `None`

**解决**:
1. 检查评估服务日志
2. 检查请求参数是否正确
3. 检查评估服务是否正常初始化

## 📊 性能优化

1. **保持服务运行**: 评估服务启动后，模型已加载到内存，响应快速
2. **批量评估**: 使用 `evaluate_batch` 可以提高效率
3. **并发请求**: API服务支持多线程，可以同时处理多个请求

## 🔐 安全建议

生产环境部署时：

1. **使用HTTPS**: 配置SSL证书
2. **添加认证**: 使用API密钥或JWT
3. **限制访问**: 使用反向代理和防火墙
4. **监控日志**: 记录所有请求

详细说明请参考: `API服务使用指南.md`

