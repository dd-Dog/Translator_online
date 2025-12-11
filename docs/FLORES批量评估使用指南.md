# FLORES数据集批量评估使用指南

## 📋 概述

`evaluate_flores_batch.py` 脚本用于在FLORES数据集上进行批量翻译和评估，支持多种语言到中文的翻译测试。

## 🚀 快速开始

### 1. 准备工作

确保以下条件已满足：

1. **FLORES数据集已下载**:
   - 数据集应位于 `datasets/flores200_dataset/` 目录
   - 包含 `dev/` 和 `devtest/` 子目录

2. **评估API服务已启动**（推荐）:
   ```bash
   # 在评估环境中
   conda activate translator_eval
   python eval_server.py
   ```

3. **API密钥已配置**:
   - 确保 `.env` 文件中包含所有必需的API密钥
   - 参考 `config/models.yaml` 中的配置

### 2. 配置参数

编辑 `evaluate_flores_batch.py` 中的配置参数：

```python
# 配置参数
LANGUAGES = ["en", "de", "vi", "km", "ms"]  # 要测试的语言
DATASET_TYPE = "dev"  # 使用dev数据集
MAX_SAMPLES = 50  # 每种语言最多测试50条（可根据需要调整）
BATCH_SIZE = 10  # 每批翻译10条
```

**参数说明**:
- `LANGUAGES`: 要测试的语言代码列表
  - `"en"`: 英语
  - `"de"`: 德语
  - `"vi"`: 越南语
  - `"km"`: 柬埔寨语
  - `"ms"`: 马来语
- `DATASET_TYPE`: 数据集类型（`"dev"` 或 `"devtest"`）
- `MAX_SAMPLES`: 每种语言的最大样本数（`None` 表示全部）
- `BATCH_SIZE`: 每批翻译的样本数（建议10-50，根据API限流调整）

### 3. 运行脚本

```bash
python evaluate_flores_batch.py
```

## 📊 输出结果

脚本会在 `results/flores_evaluation/` 目录下生成结果文件：

### JSON格式 (`flores_{lang_code}_{timestamp}.json`)

包含完整的翻译和评估数据：

```json
{
  "language": "英语",
  "lang_code": "en",
  "timestamp": "20250109_143022",
  "total_samples": 50,
  "results": [
    {
      "index": 0,
      "source": "原文...",
      "translation": "翻译...",
      "reference": null,
      "mqm_score": {
        "adequacy": 0.9,
        "fluency": 0.85,
        "terminology": 0.95,
        "overall": 0.9
      },
      "evaluation": {
        "bleu": 0.85,
        "comet": 0.92,
        "bleurt": 0.88,
        "bertscore_f1": 0.88,
        "chrf": 0.87,
        "final_score": 0.89
      }
    }
  ]
}
```

### Markdown报告 (`flores_{lang_code}_{timestamp}.md`)

包含：
- 统计摘要（平均分、各指标平均分）
- 每个样本的详细结果
- 评估指标（BLEU, COMET, BLEURT, BERTScore, ChrF）

## ⚙️ 高级配置

### 调整批次大小

根据API限流情况调整 `BATCH_SIZE`:

- **小批次（5-10）**: 适合API限流较严格的情况
- **中批次（10-20）**: 平衡速度和稳定性
- **大批次（20-50）**: 适合API限流较宽松的情况

### 调整样本数量

- **快速测试**: `MAX_SAMPLES = 10`
- **中等测试**: `MAX_SAMPLES = 50`
- **完整测试**: `MAX_SAMPLES = None`（使用全部数据）

### 使用不同的数据集

修改 `DATASET_TYPE`:
- `"dev"`: 开发集（默认）
- `"devtest"`: 开发测试集

## 🔧 故障排除

### 问题1: 数据文件未找到

**错误**: `FileNotFoundError: 数据文件不存在`

**解决**:
1. 检查数据集是否已下载到 `datasets/flores200_dataset/` 目录
2. 检查语言代码是否正确（参考 `FLORES_LANG_MAP`）

### 问题2: API限流

**错误**: 翻译请求失败，出现限流错误

**解决**:
1. 减小 `BATCH_SIZE`（例如改为5）
2. 增加批次间的等待时间（修改脚本中的 `await asyncio.sleep(2)`）

### 问题3: 评估服务不可用

**错误**: `评估服务不可用`

**解决**:
1. 确保评估API服务已启动: `python eval_server.py`
2. 检查 `config/evaluation.yaml` 中的API配置
3. 或切换到本地模式（修改 `evaluation_service.py`）

### 问题4: 内存不足

**错误**: 处理大量数据时内存不足

**解决**:
1. 减小 `MAX_SAMPLES`
2. 减小 `BATCH_SIZE`
3. 分批处理不同语言（修改 `LANGUAGES` 列表）

## 📈 性能优化建议

1. **批量处理**: 使用合适的 `BATCH_SIZE` 平衡速度和稳定性
2. **并行处理**: 如果API支持，可以考虑并行处理多个批次
3. **结果缓存**: 如果中断后重新运行，可以考虑跳过已处理的样本
4. **监控进度**: 脚本会显示详细的进度信息，便于监控

## 📝 注意事项

1. **Token消耗**: 批量翻译会消耗大量API token，请确保账户有足够余额
2. **时间成本**: 完整评估可能需要数小时，建议先用小样本测试
3. **结果保存**: 结果会自动保存，即使中断也不会丢失已完成的部分
4. **参考翻译**: 脚本会自动加载中文参考翻译，确保源文本和参考翻译数量匹配

## 🎯 使用示例

### 示例1: 快速测试（10条样本，每批5条）

```python
LANGUAGES = ["en"]  # 只测试英语
MAX_SAMPLES = 10
BATCH_SIZE = 5
```

### 示例2: 完整评估（所有语言，50条样本）

```python
LANGUAGES = ["en", "de", "vi", "km", "ms"]
MAX_SAMPLES = 50
BATCH_SIZE = 10
```

### 示例3: 单语言完整测试

```python
LANGUAGES = ["en"]
MAX_SAMPLES = None  # 使用全部数据
BATCH_SIZE = 20
```

## 📞 支持

如有问题，请：
1. 检查日志输出
2. 查看生成的错误报告
3. 参考其他文档（`API服务使用指南.md`、`评估器环境配置指南.md`）

