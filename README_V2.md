# V2版本说明

## 版本对比

| 特性 | V1（基线版本） | V2（专业版本） |
|-----|-------------|-------------|
| 评估指标 | BLEU + MQM | BLEU + BERTScore + COMET + MQM |
| 评分方式 | 单模型（GPT-4） | 多模型 + 神经网络 |
| 论文标准 | 基础 | 专业（WMT标准） |
| 资源需求 | 低 | 中等 |
| 评估模式 | 单一 | 分级（开发/论文/完整） |

---

## V2核心改进

### 1. 专业评估模型集成

**集成的模型**:
- ✅ **BERTScore**: 语义相似度（轻量级）
- ✅ **COMET**: WMT官方模型（论文标准）
- ⚠️ **BLEURT**: Google模型（可选，需GPU）

**分级使用策略**:
- **开发阶段**: 只用BERTScore（快速）
- **论文阶段**: 启用COMET（完整）
- **完整评估**: 全部启用（需GPU）

### 2. 多模式配置

**模式配置**: `config/evaluation.yaml`

#### 开发模式（默认）
```yaml
development:
  models:
    use_bertscore: true
    use_comet: false
    use_bleurt: false
  performance:
    time_per_10: "20-30秒"
```

#### 论文模式
```yaml
paper:
  models:
    use_bertscore: true
    use_comet: true
    use_bleurt: false
  performance:
    time_per_10: "2-3分钟"
```

### 3. 动态权重分配

根据启用的模型自动调整权重：

**开发模式**:
```
Score = BERTScore × 50% + MQM × 30% + BLEU × 20%
```

**论文模式**:
```
Score = COMET × 35% + BERTScore × 25% + MQM × 25% + BLEU × 15%
```

---

## 快速开始

### 步骤1: 安装BERTScore（开发用）

```bash
pip install bert-score
```

**测试**:
```bash
python evaluate_simple.py
```

**性能**: 10句约20-30秒

### 步骤2: 安装COMET（论文用）

**等需要写论文时再安装**:
```bash
pip install unbabel-comet
```

**首次运行**: 会自动下载模型（~1.5GB），需要5-10分钟

---

## 使用示例

### 开发模式（日常使用）

```python
from src.evaluation.combined_scorer import CombinedQualityScorer

# 轻量级配置
scorer = CombinedQualityScorer(
    use_comet=False,
    use_bleurt=False,
    use_bertscore=True
)
scorer.initialize()

# 快速评估
score = scorer.score(
    source="Hello, world!",
    translation="你好，世界！",
    reference="你好，世界！",
    mqm_score={'overall': 0.90}
)

print(f"综合评分: {score.final_score:.4f}")
# 综合 = BERTScore×50% + MQM×30% + BLEU×20%
```

### 论文模式（写论文时）

```python
# 完整配置
scorer = CombinedQualityScorer(
    use_comet=True,       # 启用COMET
    use_bleurt=False,
    use_bertscore=True,
    comet_model="Unbabel/wmt22-cometkiwi-da"
)
scorer.initialize()

# 完整评估
score = scorer.score(
    source="Hello, world!",
    translation="你好，世界！",
    reference="你好，世界！",
    mqm_score={'overall': 0.90}
)

print(f"BLEU: {score.bleu:.4f}")
print(f"BERTScore: {score.bertscore_f1:.4f}")
print(f"COMET: {score.comet:.4f}")
print(f"MQM: {score.mqm_overall:.4f}")
print(f"综合评分: {score.final_score:.4f}")
# 综合 = COMET×35% + BERTScore×25% + MQM×25% + BLEU×15%
```

---

## 评估脚本

### 快速评估（开发）

```bash
python evaluate_simple.py
```
- 使用：BERTScore + MQM + BLEU
- 速度：20-30秒/10句
- 适合：日常开发、调试

### 完整评估（论文）

```bash
python evaluate_with_professional_metrics.py
```
- 使用：COMET + BERTScore + MQM + BLEU
- 速度：2-3分钟/10句
- 适合：论文实验、最终评估

---

## 资源需求总结

| 模式 | 内存 | 硬盘 | 时间(10句) | 适用场景 |
|-----|------|------|-----------|---------|
| **开发** | 3-4GB | 1GB | 20-30秒 | 日常开发 ✅ |
| **论文** | 6-8GB | 3GB | 2-3分钟 | 论文实验 ✅ |
| **完整** | 12GB+ | 8GB | 5分钟+ | GPU环境 ⚠️ |

---

## 论文中的使用

### 开发阶段

使用BERTScore进行快速验证：
- 快速迭代
- 及时发现问题
- 调整系统参数

### 论文撰写阶段

启用COMET进行完整评估：
- 符合WMT标准
- 学术认可度高
- 可与其他工作对比

### 论文实验部分

```markdown
## Evaluation Metrics

We employ multiple automatic evaluation metrics:

1. **BLEU**: Traditional n-gram matching metric
2. **BERTScore** (Zhang et al., 2020): Semantic similarity using BERT embeddings
3. **COMET** (Rei et al., 2020): Neural quality estimation, official WMT metric
4. **MQM**: Multi-dimensional quality metrics (adequacy, fluency, terminology)

The final score is a weighted combination:
- Development: Score = 0.5×BERTScore + 0.3×MQM + 0.2×BLEU
- Paper: Score = 0.35×COMET + 0.25×BERTScore + 0.25×MQM + 0.15×BLEU
```

---

## 安装指南

### 现在安装（开发用）

```bash
# 只安装BERTScore
pip install bert-score

# 测试
python evaluate_simple.py
```

### 以后安装（论文用）

```bash
# 再安装COMET
pip install unbabel-comet

# 测试
python evaluate_with_professional_metrics.py
```

---

## 常见问题

### Q: 我现在需要安装所有模型吗？

**A**: 不需要！
- **现在**: 只装BERTScore（5分钟）
- **写论文时**: 再装COMET（10分钟）
- **BLEURT**: 不需要装（太重）

### Q: BERTScore够用吗？

**A**: 对于开发阶段，完全够用！
- ✅ 快速（20秒/10句）
- ✅ 语义评估
- ✅ 高引用论文
- ✅ 足够调试和优化

### Q: 什么时候需要COMET？

**A**: 写论文的时候
- 📝 撰写论文实验部分
- 📊 生成最终评估结果
- 📈 与其他工作对比

---

## 推荐工作流程

```
第1-2周：开发优化
  ↓
  使用BERTScore（快速）
  ↓
第3周：准备论文
  ↓
  安装COMET
  ↓
  运行完整评估（可以晚上跑）
  ↓
第4周：撰写论文
  ↓
  使用完整评估结果
```

---

**创建时间**: 2025-12-04  
**版本**: V2.0  
**状态**: 分级配置已完成

