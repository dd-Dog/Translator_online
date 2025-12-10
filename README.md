# 多模型协作翻译系统 V3.0

一个基于大语言模型的多阶段、多模型协作翻译系统，支持多种语言翻译成中文。

**V3.0 更新**: 翻译系统与评估系统已完全分离，评估功能已迁移到独立的共享评估库 [`translation_evaluator`](https://github.com/your-org/translation_evaluator)。

## ✨ 核心特性

### 🎯 多阶段翻译流程
- **任务规划 (Planner)**: 自动检测源语言，拆分翻译任务
- **主翻译 (Translator-A)**: 使用Gemini进行初步翻译
- **对照翻译 (Translator-B)**: 使用Qwen进行对比翻译
- **质量检查 (Checker)**: 使用GPT-4进行一致性检查和MQM评分
- **风格化 (Stylist)**: 根据目标风格优化翻译
- **最终整合 (Aggregator)**: 综合所有结果生成最终翻译

### 📊 评估系统（已分离）

**V3.0 重要变更**: 评估功能已迁移到独立的共享评估库。

如需使用专业评估功能，请使用 [`translation_evaluator`](https://github.com/your-org/translation_evaluator) 库：

- **BLEU**: 传统n-gram匹配指标
- **COMET**: WMT官方质量评估模型（论文模式）
- **BLEURT**: Google BERT-based评估模型
- **BERTScore**: 语义相似度评估
- **MQM**: 多维度质量指标（系统内置）
- **ChrF**: 字符级F-score指标
- **综合评分**: 加权组合多个评估指标

详细使用说明请参考: `docs/评估器环境配置指南.md`

### 🌍 多语言支持
- 支持多种语言翻译成中文（英语、日语、法语等）
- 自动语言检测
- 可配置翻译风格（通用、商务、学术、技术等9种风格）

## 📋 系统要求

- Python 3.8+
- 8GB+ 内存（推荐）
- 网络连接（用于API调用）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd Translator_online
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

**注意**: V3.0 版本中，评估功能已分离到独立的评估库。如需使用评估功能，请：

1. 安装共享评估库（如果尚未安装）
2. 参考 `docs/评估器环境配置指南.md` 配置评估环境
3. 使用 `test_evaluator_env.py` 测试评估环境

### 3. 配置API密钥

#### 方法1: 使用环境变量文件（推荐）

1. 复制示例配置文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的API密钥：

```env
# OpenRouter API密钥（用于访问GPT-4、Gemini、Claude）
# 注册地址: https://openrouter.ai/
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here

# Qwen API密钥（可选，用于Qwen模型）
# 注册地址: https://dashscope.aliyun.com/
QWEN_API_KEY=your-qwen-api-key-here

# DeepSeek API密钥（可选）
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

**⚠️ 重要**: `.env` 文件已加入 `.gitignore`，不会被提交到GitHub，请放心填写你的真实密钥。

#### 方法2: 设置系统环境变量

在Windows PowerShell中：
```powershell
$env:OPENROUTER_API_KEY="sk-or-v1-your-api-key-here"
```

在Linux/Mac中：
```bash
export OPENROUTER_API_KEY="sk-or-v1-your-api-key-here"
```

### 4. 配置模型

编辑 `config/models.yaml`，确保所需模型已启用：

```yaml
models:
  openai:
    enabled: true
    api_key_env: "OPENROUTER_API_KEY"
    # ...
  gemini:
    enabled: true
    api_key_env: "OPENROUTER_API_KEY"
    # ...
```

### 5. 运行测试

```bash
python quick_test.py
```

如果看到 "✓ 所有API密钥配置正确"，说明配置成功！

## 📖 使用方法

### 基础翻译

```python
import asyncio
from src.agents.pipeline import TranslationPipeline
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel
from src.models.qwen import QwenModel
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    # 创建模型实例
    planner = OpenAIModel(
        "gpt-4",
        os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        use_openrouter=True
    )
    
    translator_a = GeminiModel(
        "google/gemini-2.5-flash",
        os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        use_openrouter=True
    )
    
    translator_b = QwenModel(
        "qwen-turbo",
        os.getenv("QWEN_API_KEY")
    )
    
    checker = OpenAIModel(
        "gpt-4",
        os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        use_openrouter=True
    )
    
    stylist = QwenModel(
        "qwen-turbo",
        os.getenv("QWEN_API_KEY")
    )
    
    aggregator = OpenAIModel(
        "gpt-4",
        os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        use_openrouter=True
    )
    
    # 创建翻译管道
    pipeline = TranslationPipeline(
        planner_model=planner,
        translator_a_model=translator_a,
        translator_b_model=translator_b,
        checker_model=checker,
        stylist_model=stylist,
        aggregator_model=aggregator,
        style="general"  # 可选: general, business, academic, technical等
    )
    
    # 执行翻译
    result = await pipeline.translate(
        text="Machine learning is a subset of artificial intelligence.",
        source_lang="en",
        target_lang="zh"
    )
    
    print(f"翻译结果: {result.translated_text}")
    print(f"质量评分: {result.explainability_report.final_quality_score.overall}")

asyncio.run(main())
```

### 快速开始脚本

```bash
python quick_start.py
```

### 翻译与评估集成示例

```bash
# 确保评估API服务已启动（在另一个终端）
# conda activate translator_eval
# python eval_server.py

# 运行集成示例
python examples/translation_with_eval_api.py
```

### 测试评估环境

V3.0 版本中，评估功能已分离。测试评估环境：

**快速测试（推荐）**:
```bash
# 使用固定文本快速测试（不进行翻译）
python test_evaluation_quick.py
```

**完整测试**:
```bash
# Windows
run_test_evaluator_env.bat

# Linux/Mac
./run_test_evaluator_env.sh

# 或直接运行
python test_evaluator_env.py
```

详细配置说明请参考: `docs/评估器环境配置指南.md`

## 📁 项目结构

```
Translator_online/
├── config/                 # 配置文件
│   ├── models.yaml        # 模型配置
│   ├── config.yaml        # 主配置
│   ├── styles.yaml         # 翻译风格配置
│   └── evaluation.yaml     # 评估模式配置
├── src/
│   ├── agents/            # Agent核心模块
│   │   ├── pipeline.py    # 工作流编排器
│   │   ├── planner.py     # 任务规划
│   │   ├── translator_a.py # 主翻译
│   │   ├── translator_b.py # 对照翻译
│   │   ├── checker.py     # 质量检查
│   │   ├── stylist.py     # 风格化
│   │   └── aggregator.py # 最终整合
│   ├── models/            # 大模型接口
│   │   ├── openai.py      # OpenAI/GPT-4
│   │   ├── gemini.py      # Google Gemini
│   │   ├── qwen.py        # Qwen
│   │   └── claude.py      # Claude
│   └── utils/            # 工具模块
│       ├── evaluator_env.py # 评估器环境配置工具
│       ├── eval_api_client.py # 评估API客户端
│       └── evaluation_service.py # 评估服务集成（支持API和本地模式）
├── test_data/             # 测试数据
├── examples/              # 使用示例
├── docs/                  # 文档
│   ├── 评估器环境配置指南.md  # 评估环境配置
│   └── 评估器环境使用说明.md  # 评估环境使用
├── test_evaluator_env.py  # 评估环境测试脚本
├── run_test_evaluator_env.bat  # Windows启动脚本
├── run_test_evaluator_env.sh   # Linux/Mac启动脚本
├── API服务使用指南.md     # 评估API服务使用文档
├── .env.example           # 环境变量示例
├── requirements.txt       # Python依赖
└── README.md              # 本文档
```

## 🔧 配置说明

### 模型配置 (`config/models.yaml`)

系统支持以下模型：

- **OpenAI (GPT-4)**: 用于Planner、Checker、Aggregator
- **Gemini**: 用于主翻译（Translator-A）
- **Qwen**: 用于对照翻译（Translator-B）和风格化（Stylist）
- **Claude**: 可选，用于Checker
- **DeepSeek**: 可选

### 翻译风格 (`config/styles.yaml`)

系统支持9种翻译风格：

- `general`: 通用风格（默认）
- `native`: 地道风格
- `business`: 商务风格
- `academic`: 学术风格
- `technical`: 技术文档风格
- `literary`: 文学风格
- `news`: 新闻风格
- `colloquial`: 口语风格
- `legal`: 法律风格

### 评估配置 (`config/evaluation.yaml`)

V3.0 版本中，评估功能已分离到独立的评估库。此配置文件用于配置评估器环境：

- **评估器环境**: 指定 conda 环境名称或 Python 路径
- **评估模式**: 开发模式、论文模式、完整模式

详细配置请参考: `docs/评估器环境配置指南.md`

## 📊 评估功能

V3.0 版本中，评估功能已迁移到独立的共享评估库 [`translation_evaluator`](https://github.com/your-org/translation_evaluator)。

### 使用评估库

1. **配置评估环境**: 参考 `docs/评估器环境配置指南.md`
2. **测试环境**: 运行 `test_evaluator_env.py`
3. **在代码中使用**:

```python
from translation_evaluator import UnifiedEvaluator

evaluator = UnifiedEvaluator(
    use_bleu=True,
    use_comet=True,
    use_bleurt=True,
    use_bertscore=True,
    use_mqm=True,
    use_chrf=True
)
evaluator.initialize()

score = evaluator.score(
    source="Hello world",
    translation="你好世界",
    reference="你好世界"
)
```

## 🔒 安全说明

### API密钥保护

1. **环境变量**: 所有API密钥都通过环境变量读取，不会硬编码在代码中
2. **.gitignore**: `.env` 文件已加入 `.gitignore`，不会被提交到GitHub
3. **示例文件**: `.env.example` 只包含占位符，不包含真实密钥

### 检查密钥是否泄露

运行以下命令检查是否有硬编码的密钥：

```bash
# 检查是否包含真实的API密钥
grep -r "sk-or-v1-" . --exclude-dir=.git
```

如果发现任何输出，请立即更换密钥！

## 🐛 常见问题

### Q: 提示"未找到API密钥"

**A**: 请确保：
1. `.env` 文件存在于项目根目录
2. `.env` 文件中包含正确的环境变量名
3. 环境变量值没有引号（如 `OPENROUTER_API_KEY=sk-or-v1-xxx`，不是 `OPENROUTER_API_KEY="sk-or-v1-xxx"`）

### Q: OpenRouter API调用失败

**A**: 可能原因：
1. API密钥无效或已过期
2. 账户余额不足
3. 网络连接问题

检查方法：
```bash
python test_openrouter.py
```

### Q: 如何使用评估功能？

**A**: V3.0 版本支持两种模式：

**API模式（推荐）**:
1. 启动评估API服务: `python eval_server.py`（在评估环境中）
2. 配置 `config/evaluation.yaml` 启用API模式
3. 使用 `EvaluationService` 调用评估API

**本地模式**:
1. 参考 `docs/评估器环境配置指南.md` 配置评估环境
2. 运行 `test_evaluator_env.py` 测试环境
3. 使用 `EvaluationService(use_api=False)` 创建本地评估服务

### Q: 评估API服务连接失败？

**A**: 请检查：
1. 评估API服务是否已启动: `python eval_server.py`
2. 服务地址是否正确（`config/evaluation.yaml` 中的 `api.base_url`）
3. 防火墙是否阻止了连接
4. 参考 `API服务使用指南.md` 排查问题

### Q: 评估环境配置失败？

**A**: 请检查：
1. conda 环境名称是否正确（`config/evaluation.yaml`）
2. 评估库是否已安装到指定环境
3. 参考 `docs/评估器环境使用说明.md` 排查问题

## 📈 性能指标

### 翻译速度
- 单句翻译: 约15-20秒
- 10句批量: 约3-5分钟

### 评估速度（使用独立评估库）
- **开发模式**: BERTScore + MQM + BLEU + ChrF（约20-30秒/10句）
- **论文模式**: COMET + BERTScore + MQM + BLEU + ChrF（约2-3分钟/10句）
- **完整模式**: 所有模型（需要GPU，约30秒/10句）

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

[根据实际情况填写]

## 🙏 致谢

- OpenRouter: 提供统一的API访问多个大模型
- translation_evaluator: 共享评估库（V3.0新增）
- BERTScore: 语义相似度评估
- COMET: WMT官方质量评估模型
- BLEURT: Google BERT-based评估模型

## 📝 版本历史

### V3.0 (当前版本)
- ✅ 翻译系统与评估系统完全分离
- ✅ 支持API服务模式：通过HTTP API调用评估服务
- ✅ 支持本地评估模式：使用共享评估库
- ✅ 支持独立的 conda 环境配置
- ✅ 改进的错误提示和文档
- ✅ 统一的评估服务接口（`EvaluationService`）

### V2.0
- ✅ 集成专业评估模型（COMET, BLEURT, BERTScore）
- ✅ 多维度质量评估（BLEU, MQM, ChrF）
- ✅ 可配置的翻译风格

### V1.0
- ✅ 基础多阶段翻译流程
- ✅ 多模型协作机制

## 📞 联系方式

如有问题，请提交Issue或联系项目维护者。

---

**⚠️ 重要提醒**: 
- 请妥善保管你的API密钥，不要分享给他人
- 定期检查API使用量，避免意外费用
- 如果发现密钥泄露，请立即更换

