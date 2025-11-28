# 多模型翻译Agent

基于在线大模型的智能翻译系统，通过集成多个大模型API提高翻译准确率和可靠性。

## 项目结构

```
Translator_online/
├── config/                 # 配置文件
│   ├── config.yaml        # 主配置文件
│   └── models.yaml        # 模型配置
├── src/
│   ├── agents/            # Agent核心模块
│   │   ├── __init__.py
│   │   ├── translator.py  # 主翻译Agent
│   │   └── strategies/    # 翻译策略
│   │       ├── __init__.py
│   │       ├── base.py    # 策略基类
│   │       ├── voting.py  # 投票策略
│   │       └── weighted.py # 加权策略
│   ├── models/            # 大模型接口
│   │   ├── __init__.py
│   │   ├── base.py        # 模型基类
│   │   ├── openai.py      # OpenAI接口
│   │   ├── gemini.py      # Google Gemini接口
│   │   └── claude.py      # Anthropic Claude接口
│   ├── utils/             # 工具类
│   │   ├── __init__.py
│   │   ├── logger.py      # 日志工具
│   │   └── validator.py   # 验证工具
│   └── main.py            # 入口文件
├── tests/                 # 测试文件
├── requirements.txt       # 依赖包
└── README.md
```

## 核心设计理念

1. **可扩展性**：通过抽象基类设计，易于添加新的大模型接口
2. **策略模式**：支持多种翻译策略（投票、加权、置信度评估等）
3. **配置驱动**：通过配置文件管理模型和策略参数
4. **模块化**：各模块职责清晰，便于维护和测试

## 未来优化方向

- 多模型投票机制
- 置信度评估和质量检测
- 领域自适应翻译
- 上下文感知翻译
- 翻译后处理和优化
- 成本优化策略

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

创建 `.env` 文件（参考 `.env.example`）：

```bash
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 3. 运行示例

```bash
# 运行主程序
python src/main.py

# 或运行详细示例
python examples/basic_usage.py
```

## 使用示例

### 基础用法

```python
import asyncio
from src.agents.translator import TranslatorAgent
from src.models.openai import OpenAIModel

async def main():
    # 创建模型
    model = OpenAIModel(
        model_name="gpt-3.5-turbo",
        api_key="your_api_key"
    )
    
    # 创建Agent
    agent = TranslatorAgent(models=[model])
    
    # 翻译
    result = await agent.translate(
        text="Hello, world!",
        source_lang="en",
        target_lang="zh"
    )
    
    print(result.translated_text)

asyncio.run(main())
```

### 多模型投票策略

```python
from src.agents.translator import TranslatorAgent
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel

# 创建多个模型
models = [
    OpenAIModel(model_name="gpt-3.5-turbo", api_key="..."),
    GeminiModel(model_name="gemini-pro", api_key="...")
]

# 使用投票策略
agent = TranslatorAgent(
    models=models,
    strategy_type="voting",
    strategy_config={"min_models": 2}
)

result = await agent.translate("Hello", source_lang="en", target_lang="zh")
```

## 架构说明

### 核心组件

1. **模型层 (src/models/)**
   - `BaseModel`: 模型抽象基类
   - `OpenAIModel`: OpenAI接口实现
   - `GeminiModel`: Google Gemini接口实现
   - 易于扩展新模型（如Claude、文心一言等）

2. **策略层 (src/agents/strategies/)**
   - `BaseStrategy`: 策略基类
   - `VotingStrategy`: 投票策略（选择出现次数最多的翻译）
   - `WeightedStrategy`: 加权策略（根据模型权重选择）
   - 可扩展新策略（如置信度评估、相似度匹配等）

3. **Agent层 (src/agents/)**
   - `TranslatorAgent`: 主翻译Agent，协调模型和策略

### 扩展指南

#### 添加新模型

1. 继承 `BaseModel` 类
2. 实现 `translate()` 和 `validate_config()` 方法
3. 在 `src/models/__init__.py` 中导出

#### 添加新策略

1. 继承 `BaseStrategy` 类
2. 实现 `combine_translations()` 方法
3. 在 `src/agents/strategies/__init__.py` 中导出
4. 在 `TranslatorAgent._create_strategy()` 中添加策略类型

## 未来研究方向

框架设计支持以下优化方向：

1. **置信度评估**
   - 基于模型输出的logprobs计算置信度
   - 多模型结果一致性分析

2. **相似度匹配**
   - 使用embedding计算翻译结果相似度
   - 改进投票策略的匹配机制

3. **领域自适应**
   - 根据文本领域选择最适合的模型
   - 领域特定的提示词优化

4. **上下文感知**
   - 利用对话历史提升翻译质量
   - 术语一致性保证

5. **成本优化**
   - 根据文本复杂度选择模型
   - 缓存机制减少API调用

6. **后处理优化**
   - 翻译结果质量检测
   - 自动修正和润色

## 开发计划

- [ ] 添加Claude模型支持
- [ ] 实现置信度评估策略
- [ ] 添加翻译质量评估指标
- [ ] 实现缓存机制
- [ ] 添加批量翻译API
- [ ] 性能优化和并发控制
- [ ] 单元测试和集成测试

## 许可证

MIT License

