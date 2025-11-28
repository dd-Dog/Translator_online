# 工作流架构文档

## 概述

本系统采用**多阶段、多模型协作**的翻译工作流架构，将翻译任务分解为6个专业阶段，每个阶段由专门的Agent负责，充分发挥不同模型的优势。

## 工作流架构图

```
用户输入文本
    ↓
┌─────────────────────────────────────────┐
│ 1. Task Planner (ChatGPT)               │
│    - 语言检测                            │
│    - 任务拆分（句子/段落）                │
│    - 识别需要双重翻译的段落              │
│    - 识别需要多重审核的段落              │
└──────────────┬──────────────────────────┘
               ↓
    ┌──────────┴──────────┐
    │                     │
┌───▼──────┐      ┌───────▼──────┐
│ 2. Translator-A│      │ 3. Translator-B│
│ (Gemini)        │      │ (Qwen/DeepSeek)│
│ 主译            │      │ 对照译          │
│ - 多语言通用翻译 │      │ - 中文自然表达  │
│ - 输出初稿+自检  │      │ - 输出二稿+自检 │
└───┬──────┘      └───────┬──────┘
    │                     │
    └──────────┬──────────┘
               ↓
┌─────────────────────────────────────────┐
│ 4. Checker (ChatGPT)                    │
│    - 一致性检查（冲突、遗漏、误解）        │
│    - MQM质量评分                         │
│      * 充分性 (Adequacy)                 │
│      * 流畅性 (Fluency)                  │
│      * 术语准确性 (Terminology)          │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 5. Stylist (Qwen/DeepSeek)              │
│    - 术语统一（基于术语表）               │
│    - 风格统一（学术/正式/口语等）         │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 6. Aggregator (ChatGPT)                 │
│    - 整合所有结果                        │
│    - 生成最终翻译                        │
│    - 生成可解释性报告                    │
└──────────────┬──────────────────────────┘
               ↓
        最终翻译结果
    + 可解释性报告
```

## 各阶段详细说明

### 阶段1: Task Planner (任务规划)

**模型**: ChatGPT (GPT-4)

**职责**:
- 自动检测源语言
- 将文本拆分为合适的翻译单元（句子级或段落级）
- 识别需要双重翻译的段落（复杂、专业术语多、歧义等）
- 识别需要多重审核的段落（重要内容、关键信息等）

**输出**: `TaskPlan`
- 源语言和目标语言
- 任务列表（每个任务包含文本、类型、是否需要双重翻译等）

### 阶段2: Translator-A (主译)

**模型**: Gemini (gemini-pro)

**优势**: 擅长多语言通用机器翻译

**职责**:
- 执行主翻译
- 生成自检报告（标记不确定的段落）

**输出**: `TranslationDraft`
- 翻译文本
- 自检报告（不确定段落、置信度、建议）

### 阶段3: Translator-B (对照译)

**模型**: Qwen (qwen-turbo) 或 DeepSeek (deepseek-chat)

**优势**: 擅长中文相关内容，自然流畅的表达

**职责**:
- 执行对照翻译
- 生成自检报告

**输出**: `TranslationDraft`
- 翻译文本
- 自检报告

### 阶段4: Checker (一致性检查)

**模型**: ChatGPT (GPT-4)

**职责**:
- 对比两个翻译版本
- 识别一致的句子/段落
- 识别冲突的句子/段落，说明冲突原因
- 检查遗漏内容
- 检查误解或误译
- 进行MQM质量评分

**输出**: `CheckerReport`
- 一致/冲突的段落列表
- 遗漏和误解列表
- 质量评分（充分性、流畅性、术语准确性）

### 阶段5: Stylist (风格化)

**模型**: Qwen 或 DeepSeek

**职责**:
- 根据术语表统一专业术语
- 统一写作风格（学术论文、正式公文、口语等）
- 保持翻译的准确性和流畅性

**输出**: `StylistResult`
- 风格化后的文本
- 术语变更记录
- 风格变更记录

### 阶段6: Aggregator (最终整合)

**模型**: ChatGPT (GPT-4)

**职责**:
- 基于检查报告和风格化结果，生成最终最佳翻译
- 记录所有修改和原因
- 评估质量改进情况
- 生成可解释性报告（用于论文）

**输出**: `FinalTranslation`
- 最终翻译文本
- 可解释性报告
  - 修改记录（阶段、段落、原文、修改后、原因）
  - 质量改进（指标、改进前、改进后、改进值）
  - 最终质量评分

## 数据流

```
用户输入
    ↓
TaskPlan (任务计划)
    ↓
TranslationDraft[] (翻译草稿列表)
    ├─→ Translator-A Draft
    └─→ Translator-B Draft
    ↓
CheckerReport (检查报告)
    ↓
StylistResult (风格化结果)
    ↓
FinalTranslation (最终结果)
    ├─→ translated_text
    └─→ explainability_report
```

## 模型分工策略

### 为什么这样分工？

1. **ChatGPT (GPT-4)**
   - **用于**: Planner, Checker, Aggregator
   - **原因**: 擅长理解、分析、推理任务，适合规划、检查和整合

2. **Gemini**
   - **用于**: Translator-A
   - **原因**: 多语言能力强，适合通用翻译任务

3. **Qwen/DeepSeek**
   - **用于**: Translator-B, Stylist
   - **原因**: 中文表达自然流畅，适合中文相关内容和风格化

## 优势

1. **质量提升**: 双重翻译 + 一致性检查 + 质量评分
2. **专业分工**: 每个模型专注于自己擅长的任务
3. **可解释性**: 详细的修改记录和质量改进报告
4. **灵活性**: 支持术语表、风格定制
5. **可扩展**: 易于添加新的Agent或模型

## 使用示例

```python
from src.agents.pipeline import TranslationPipeline
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel
from src.models.qwen import QwenModel

# 创建模型
planner = OpenAIModel("gpt-4", api_key="...")
translator_a = GeminiModel("gemini-pro", api_key="...")
translator_b = QwenModel("qwen-turbo", api_key="...")
checker = OpenAIModel("gpt-4", api_key="...")
stylist = QwenModel("qwen-turbo", api_key="...")
aggregator = OpenAIModel("gpt-4", api_key="...")

# 创建工作流
pipeline = TranslationPipeline(
    planner_model=planner,
    translator_a_model=translator_a,
    translator_b_model=translator_b,
    checker_model=checker,
    stylist_model=stylist,
    aggregator_model=aggregator,
    glossary={"AI": "人工智能"},
    style="academic"
)

# 执行翻译
result = await pipeline.translate(
    text="Machine learning is a subset of AI.",
    source_lang="en",
    target_lang="zh"
)

# 获取结果
print(result.translated_text)
print(result.explainability_report)
```

## 未来优化

1. **并行处理**: 某些阶段可以并行执行
2. **缓存机制**: 缓存中间结果，减少重复计算
3. **自适应选择**: 根据文本特点动态选择模型
4. **质量阈值**: 设置质量阈值，自动决定是否需要重新翻译
5. **批量处理**: 优化批量翻译的性能

