# 架构设计文档

## 设计目标

本框架旨在构建一个**可扩展、模块化、策略化**的多模型翻译系统，支持：

1. **多模型集成**：轻松接入不同的大模型API
2. **灵活策略**：支持多种翻译结果融合策略
3. **易于扩展**：便于添加新模型、新策略、新功能
4. **配置驱动**：通过配置文件管理，无需修改代码

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    TranslatorAgent                       │
│  (协调模型和策略，提供统一翻译接口)                        │
└──────────────┬──────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────────┐
│   Models    │  │   Strategies     │
│  (模型层)    │  │   (策略层)        │
└─────────────┘  └──────────────────┘
```

## 核心模块

### 1. 模型层 (Models Layer)

**职责**：封装不同大模型API，提供统一接口

**设计模式**：策略模式 + 工厂模式

**核心类**：
- `BaseModel`: 抽象基类，定义统一接口
- `OpenAIModel`: OpenAI实现
- `GeminiModel`: Gemini实现

**接口设计**：
```python
class BaseModel:
    async def translate(request: TranslationRequest) -> TranslationResponse
    def validate_config() -> bool
    def get_model_info() -> Dict
```

**扩展方式**：
1. 继承 `BaseModel`
2. 实现 `translate()` 方法
3. 在配置中启用

### 2. 策略层 (Strategies Layer)

**职责**：定义如何合并多个模型的翻译结果

**设计模式**：策略模式

**核心类**：
- `BaseStrategy`: 策略基类
- `VotingStrategy`: 投票策略
- `WeightedStrategy`: 加权策略

**策略接口**：
```python
class BaseStrategy:
    async def combine_translations(
        request: TranslationRequest,
        responses: List[TranslationResponse]
    ) -> TranslationResponse
```

**现有策略**：

1. **投票策略 (VotingStrategy)**
   - 原理：统计各模型翻译结果，选择出现次数最多的
   - 适用：模型质量相近，追求一致性
   - 参数：`min_models`（最少模型数）

2. **加权策略 (WeightedStrategy)**
   - 原理：根据模型权重加权选择
   - 适用：模型质量有差异，需要突出优质模型
   - 参数：`model_weights`（模型权重字典）

**扩展方式**：
1. 继承 `BaseStrategy`
2. 实现 `combine_translations()` 方法
3. 在 `TranslatorAgent` 中注册

### 3. Agent层 (Agent Layer)

**职责**：协调模型和策略，提供高级翻译功能

**核心类**：
- `TranslatorAgent`: 主Agent类

**工作流程**：
```
1. 接收翻译请求
2. 并发调用所有模型
3. 收集所有响应
4. 使用策略合并结果
5. 返回最终翻译
```

**关键特性**：
- 异步并发：同时调用多个模型，提高效率
- 错误处理：单个模型失败不影响整体
- 动态配置：支持运行时添加/移除模型

## 数据流

```
用户请求
    ↓
TranslatorAgent.translate()
    ↓
创建 TranslationRequest
    ↓
并发调用所有模型
    ├─→ OpenAI.translate()
    ├─→ Gemini.translate()
    └─→ ...
    ↓
收集 TranslationResponse[]
    ↓
策略合并结果
    ├─→ VotingStrategy.combine_translations()
    └─→ WeightedStrategy.combine_translations()
    ↓
返回最终 TranslationResponse
```

## 配置系统

### 配置文件结构

```
config/
├── config.yaml      # 主配置（策略、日志等）
└── models.yaml      # 模型配置（API密钥、参数等）
```

### 配置加载流程

1. 加载 `config/config.yaml` → 获取策略配置
2. 加载 `config/models.yaml` → 获取模型配置
3. 从环境变量读取API密钥
4. 创建模型实例
5. 创建策略实例
6. 组装Agent

## 扩展点设计

### 1. 添加新模型

**步骤**：
1. 在 `src/models/` 创建新文件（如 `claude.py`）
2. 继承 `BaseModel`，实现接口
3. 在 `src/models/__init__.py` 导出
4. 在 `config/models.yaml` 配置

**示例**：
```python
class ClaudeModel(BaseModel):
    async def translate(self, request):
        # 实现Claude API调用
        pass
```

### 2. 添加新策略

**步骤**：
1. 在 `src/agents/strategies/` 创建新文件
2. 继承 `BaseStrategy`，实现 `combine_translations()`
3. 在 `TranslatorAgent._create_strategy()` 注册

**示例策略**：
- **置信度策略**：选择置信度最高的翻译
- **相似度策略**：基于embedding选择最相似的翻译
- **混合策略**：结合投票和加权

### 3. 添加新功能

**可扩展功能**：
- 翻译缓存
- 质量评估
- 批量处理
- 流式输出
- 上下文管理

## 设计原则

1. **单一职责**：每个类只负责一个功能
2. **开闭原则**：对扩展开放，对修改关闭
3. **依赖倒置**：依赖抽象而非具体实现
4. **接口隔离**：接口精简，职责明确

## 性能考虑

1. **并发处理**：使用 `asyncio.gather()` 并发调用模型
2. **超时控制**：避免单个模型阻塞整体
3. **错误隔离**：单个模型失败不影响其他模型
4. **资源管理**：合理控制并发数量

## 未来优化方向

### 短期（框架完善）
- [ ] 添加更多模型支持（Claude、文心一言等）
- [ ] 实现置信度评估策略
- [ ] 添加单元测试和集成测试
- [ ] 性能优化和监控

### 中期（功能增强）
- [ ] 翻译质量评估指标
- [ ] 缓存机制（减少API调用）
- [ ] 批量翻译优化
- [ ] 上下文感知翻译

### 长期（研究探索）
- [ ] 基于embedding的相似度匹配
- [ ] 领域自适应翻译
- [ ] 主动学习机制
- [ ] 成本优化策略

## 总结

本框架采用**分层架构**和**策略模式**，实现了：

✅ **高可扩展性**：易于添加新模型和新策略  
✅ **高可维护性**：模块化设计，职责清晰  
✅ **高灵活性**：配置驱动，支持多种使用场景  
✅ **高可靠性**：错误隔离，容错机制完善

为后续的研究和优化提供了坚实的基础。

