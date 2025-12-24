# Web界面设计方案

## 一、方案概述

### 1.1 目标
为多模型协作翻译系统开发一个现代化的Web界面，让非技术用户也能方便地使用翻译功能。

### 1.2 核心功能
- ✅ 文本翻译（单句/段落/长文本）
- ✅ 翻译风格选择（9种风格）
- ✅ 术语表管理
- ✅ 翻译历史记录
- ✅ 实时翻译进度显示
- ✅ 翻译结果详情（可解释性报告）
- ✅ 批量翻译（文件上传）
- ✅ 翻译质量评分展示

### 1.3 技术选型

#### 后端框架
- **FastAPI** (推荐)
  - 异步支持好，性能优秀
  - 自动生成API文档
  - 类型提示完善
  - 与现有asyncio代码兼容性好

#### 前端框架
- **Vue 3 + Vite** (推荐)
  - 现代化、响应式
  - 组件化开发
  - 生态丰富
  - 或 **React + Vite**（根据团队偏好）

#### UI组件库
- **Element Plus** (Vue) 或 **Ant Design** (React)
  - 中文支持好
  - 组件丰富
  - 文档完善

#### 实时通信
- **WebSocket** (用于实时进度更新)
- 或 **Server-Sent Events (SSE)** (单向推送)

## 二、系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────┐
│          Web前端 (Vue/React)            │
│  - 用户界面                              │
│  - 状态管理                              │
│  - WebSocket客户端                       │
└──────────────┬──────────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼──────────────────────────┐
│       FastAPI后端服务                     │
│  ┌──────────────────────────────────┐   │
│  │  API路由层                        │   │
│  │  - /api/translate                │   │
│  │  - /api/history                  │   │
│  │  - /api/glossary                 │   │
│  │  - /api/status                   │   │
│  └──────────┬───────────────────────┘   │
│  ┌──────────▼───────────────────────┐   │
│  │  业务逻辑层                        │   │
│  │  - 翻译任务管理                    │   │
│  │  - 任务队列                        │   │
│  │  - 进度跟踪                        │   │
│  └──────────┬───────────────────────┘   │
│  ┌──────────▼───────────────────────┐   │
│  │  翻译服务层                        │   │
│  │  - TranslationPipeline            │   │
│  │  - 模型管理                        │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 2.2 目录结构

```
Translator_online/
├── web/                              # Web应用目录（新建）
│   ├── backend/                      # 后端服务
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py               # FastAPI应用入口
│   │   │   ├── config.py             # 配置管理
│   │   │   ├── dependencies.py       # 依赖注入
│   │   │   ├── api/                  # API路由
│   │   │   │   ├── __init__.py
│   │   │   │   ├── translate.py      # 翻译API
│   │   │   │   ├── history.py        # 历史记录API
│   │   │   │   ├── glossary.py       # 术语表API
│   │   │   │   └── websocket.py      # WebSocket端点
│   │   │   ├── services/             # 业务服务
│   │   │   │   ├── __init__.py
│   │   │   │   ├── translation_service.py  # 翻译服务
│   │   │   │   ├── task_manager.py   # 任务管理
│   │   │   │   └── history_service.py # 历史记录服务
│   │   │   ├── models/               # 数据模型
│   │   │   │   ├── __init__.py
│   │   │   │   ├── request.py        # 请求模型
│   │   │   │   ├── response.py       # 响应模型
│   │   │   │   └── database.py       # 数据库模型（可选）
│   │   │   └── utils/                # 工具函数
│   │   │       ├── __init__.py
│   │   │       └── websocket_manager.py # WebSocket管理
│   │   ├── requirements.txt          # 后端依赖
│   │   └── .env.example              # 环境变量示例
│   │
│   └── frontend/                     # 前端应用
│       ├── public/                   # 静态资源
│       ├── src/
│       │   ├── main.js               # 入口文件
│       │   ├── App.vue               # 根组件
│       │   ├── router/               # 路由配置
│       │   ├── views/                # 页面组件
│       │   │   ├── Home.vue          # 首页（翻译界面）
│       │   │   ├── History.vue       # 历史记录
│       │   │   ├── Glossary.vue      # 术语表管理
│       │   │   └── Settings.vue      # 设置
│       │   ├── components/           # 通用组件
│       │   │   ├── TranslationForm.vue    # 翻译表单
│       │   │   ├── TranslationResult.vue  # 翻译结果
│       │   │   ├── ProgressBar.vue        # 进度条
│       │   │   ├── StyleSelector.vue      # 风格选择器
│       │   │   └── GlossaryEditor.vue      # 术语表编辑器
│       │   ├── stores/               # 状态管理（Pinia）
│       │   │   ├── translation.js    # 翻译状态
│       │   │   ├── history.js        # 历史记录状态
│       │   │   └── glossary.js       # 术语表状态
│       │   ├── api/                  # API客户端
│       │   │   ├── index.js          # API配置
│       │   │   ├── translate.js      # 翻译API
│       │   │   └── websocket.js      # WebSocket客户端
│       │   └── utils/                # 工具函数
│       ├── package.json
│       └── vite.config.js
│
└── ... (现有代码)
```

## 三、API设计

### 3.1 RESTful API

#### 1. 翻译接口

**POST /api/v1/translate**
```json
请求体:
{
  "text": "待翻译文本",
  "source_lang": "en",  // 可选，auto表示自动检测
  "target_lang": "zh",
  "style": "general",   // 可选，默认general
  "glossary": {         // 可选
    "AI": "人工智能",
    "ML": "机器学习"
  },
  "stream": false       // 是否流式返回进度
}

响应:
{
  "task_id": "uuid",
  "status": "processing",
  "message": "翻译任务已创建"
}
```

**GET /api/v1/translate/{task_id}**
```json
响应:
{
  "task_id": "uuid",
  "status": "completed",  // processing, completed, failed
  "result": {
    "translated_text": "翻译结果",
    "source_lang": "en",
    "target_lang": "zh",
    "explainability_report": {
      "modifications": [...],
      "quality_improvements": {...},
      "final_quality_score": {
        "adequacy": 0.95,
        "fluency": 0.92,
        "terminology": 0.98,
        "overall": 0.95
      }
    },
    "processing_stages": ["planner", "translator_a", ...]
  },
  "error": null,
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:00:10Z"
}
```

#### 2. 历史记录接口

**GET /api/v1/history**
```json
查询参数:
- page: 页码（默认1）
- page_size: 每页数量（默认20）
- source_lang: 筛选源语言
- style: 筛选风格

响应:
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "task_id": "uuid",
      "source_text": "原文",
      "translated_text": "译文",
      "source_lang": "en",
      "target_lang": "zh",
      "style": "general",
      "quality_score": 0.95,
      "created_at": "2024-01-01T00:00:00Z"
    },
    ...
  ]
}
```

**GET /api/v1/history/{task_id}**
- 获取单条历史记录的详细信息

**DELETE /api/v1/history/{task_id}**
- 删除历史记录

#### 3. 术语表接口

**GET /api/v1/glossary**
```json
响应:
{
  "glossary": {
    "AI": "人工智能",
    "ML": "机器学习",
    ...
  }
}
```

**POST /api/v1/glossary**
```json
请求体:
{
  "glossary": {
    "AI": "人工智能",
    "ML": "机器学习"
  }
}
```

**PUT /api/v1/glossary/{term}**
```json
请求体:
{
  "translation": "新翻译"
}
```

**DELETE /api/v1/glossary/{term}**
- 删除术语

#### 4. 配置接口

**GET /api/v1/config/styles**
```json
响应:
{
  "styles": [
    {
      "id": "general",
      "name": "通用风格",
      "description": "..."
    },
    ...
  ]
}
```

**GET /api/v1/config/models**
```json
响应:
{
  "models": {
    "planner": "gpt-4",
    "translator_a": "google/gemini-2.5-flash",
    ...
  },
  "status": {
    "planner": "available",
    "translator_a": "available",
    ...
  }
}
```

### 3.2 WebSocket API

**WS /ws/translate/{task_id}**

用于实时推送翻译进度：

```json
消息格式:
{
  "type": "progress",  // progress, stage_complete, completed, error
  "task_id": "uuid",
  "data": {
    "stage": "translator_a",  // planner, translator_a, translator_b, checker, stylist, aggregator
    "progress": 50,           // 0-100
    "message": "正在执行主翻译..."
  }
}
```

## 四、前端界面设计

### 4.1 页面结构

#### 1. 首页 - 翻译界面

```
┌─────────────────────────────────────────────────┐
│  多模型协作翻译系统                    [设置] [历史] │
├─────────────────────────────────────────────────┤
│                                                   │
│  源语言: [自动检测 ▼]  目标语言: [中文 ▼]         │
│  翻译风格: [通用风格 ▼]                           │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │ 请输入要翻译的文本...                    │    │
│  │                                          │    │
│  │                                          │    │
│  │                                          │    │
│  │                                          │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  [术语表管理] [上传文件]                          │
│                                                   │
│  [开始翻译]                                       │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │ 翻译结果                                 │    │
│  │                                          │    │
│  │ [进度条: ████████░░ 80%]                │    │
│  │ 当前阶段: 风格化处理...                  │    │
│  │                                          │    │
│  │ 翻译文本:                                │    │
│  │ [翻译结果将显示在这里]                   │    │
│  │                                          │    │
│  │ [查看详情] [复制] [下载] [保存]          │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │ 质量评分                                 │    │
│  │ 充分性: ████████░░ 0.95                 │    │
│  │ 流畅性: ███████░░░ 0.92                 │    │
│  │ 术语准确性: ██████████ 0.98              │    │
│  │ 总体评分: ████████░░ 0.95               │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

#### 2. 历史记录页面

```
┌─────────────────────────────────────────────────┐
│  翻译历史                            [返回]       │
├─────────────────────────────────────────────────┤
│  筛选: [全部语言 ▼] [全部风格 ▼] [搜索...]       │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │ 2024-01-01 12:00:00                      │    │
│  │ 原文: Machine learning is...            │    │
│  │ 译文: 机器学习是...                      │    │
│  │ 风格: 通用 | 评分: 0.95                  │    │
│  │ [查看详情] [复制] [删除]                  │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │ 2024-01-01 11:30:00                      │    │
│  │ ...                                      │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  [上一页] [1] [2] [3] [下一页]                    │
└─────────────────────────────────────────────────┘
```

#### 3. 术语表管理页面

```
┌─────────────────────────────────────────────────┐
│  术语表管理                          [返回]       │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │ 术语          │ 翻译          │ 操作    │    │
│  ├─────────────────────────────────────────┤    │
│  │ AI           │ 人工智能      │ [编辑][删除]│
│  │ ML           │ 机器学习      │ [编辑][删除]│
│  │ NLP          │ 自然语言处理  │ [编辑][删除]│
│  └─────────────────────────────────────────┘    │
│                                                   │
│  [添加术语]                                       │
│  术语: [______]  翻译: [______]  [添加]          │
│                                                   │
│  [导入] [导出] [清空]                             │
└─────────────────────────────────────────────────┘
```

#### 4. 翻译详情弹窗

```
┌─────────────────────────────────────────────────┐
│  翻译详情                            [关闭]      │
├─────────────────────────────────────────────────┤
│                                                   │
│  原文: Machine learning is a subset of AI.      │
│  译文: 机器学习是人工智能的一个子集。              │
│                                                   │
│  ┌─ 处理阶段 ────────────────────────────────┐   │
│  │ ✓ 任务规划                                │   │
│  │ ✓ 主翻译 (Gemini)                         │   │
│  │ ✓ 对照翻译 (Qwen)                         │   │
│  │ ✓ 质量检查 (GPT-4)                        │   │
│  │ ✓ 风格化 (Qwen)                           │   │
│  │ ✓ 最终整合 (GPT-4)                        │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  ┌─ 质量评分 ────────────────────────────────┐   │
│  │ 充分性: 0.95 | 流畅性: 0.92 | 术语: 0.98  │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  ┌─ 修改记录 ────────────────────────────────┐   │
│  │ [可展开查看详细修改记录]                   │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  [复制译文] [下载报告]                            │
└─────────────────────────────────────────────────┘
```

### 4.2 组件设计

#### 核心组件

1. **TranslationForm.vue**
   - 文本输入框
   - 语言选择器
   - 风格选择器
   - 术语表快速编辑
   - 文件上传

2. **TranslationResult.vue**
   - 翻译结果显示
   - 进度条
   - 质量评分展示
   - 操作按钮（复制、下载、保存）

3. **ProgressBar.vue**
   - 实时进度显示
   - 阶段信息
   - WebSocket连接状态

4. **StyleSelector.vue**
   - 风格选择下拉框
   - 风格说明提示

5. **GlossaryEditor.vue**
   - 术语表列表
   - 添加/编辑/删除术语
   - 导入/导出功能

## 五、实现步骤

### 阶段1: 后端API开发（1-2周）

1. **搭建FastAPI项目结构**
   - 创建项目目录
   - 配置依赖
   - 设置CORS

2. **实现翻译API**
   - 集成现有TranslationPipeline
   - 实现任务队列管理
   - 实现WebSocket进度推送

3. **实现其他API**
   - 历史记录API
   - 术语表API
   - 配置API

4. **测试API**
   - 单元测试
   - 集成测试
   - API文档验证

### 阶段2: 前端开发（2-3周）

1. **搭建前端项目**
   - 初始化Vue/React项目
   - 配置路由
   - 配置状态管理

2. **开发核心组件**
   - 翻译表单组件
   - 结果展示组件
   - 进度条组件

3. **实现页面**
   - 首页翻译界面
   - 历史记录页面
   - 术语表管理页面

4. **集成WebSocket**
   - WebSocket客户端
   - 实时进度更新
   - 错误处理

### 阶段3: 功能完善（1周）

1. **优化用户体验**
   - 加载状态
   - 错误提示
   - 响应式设计

2. **添加高级功能**
   - 批量翻译
   - 文件上传/下载
   - 翻译报告导出

3. **性能优化**
   - 代码分割
   - 懒加载
   - 缓存策略

### 阶段4: 测试与部署（1周）

1. **测试**
   - 功能测试
   - 兼容性测试
   - 性能测试

2. **部署**
   - 后端部署（Docker/云服务）
   - 前端部署（静态托管/CDN）
   - 域名配置

## 六、技术细节

### 6.1 任务管理

使用异步任务队列管理翻译任务：

```python
# 使用asyncio.Queue或Celery
class TaskManager:
    def __init__(self):
        self.tasks = {}  # task_id -> Task
        self.queue = asyncio.Queue()
    
    async def create_task(self, request):
        task_id = str(uuid.uuid4())
        task = TranslationTask(task_id, request)
        self.tasks[task_id] = task
        await self.queue.put(task)
        return task_id
    
    async def process_task(self, task_id):
        # 执行翻译并推送进度
        ...
```

### 6.2 WebSocket实现

```python
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.connections = {}  # task_id -> [WebSocket]
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.connections:
            self.connections[task_id] = []
        self.connections[task_id].append(websocket)
    
    async def send_progress(self, task_id: str, progress: dict):
        if task_id in self.connections:
            for ws in self.connections[task_id]:
                await ws.send_json(progress)
```

### 6.3 前端状态管理

使用Pinia（Vue）或Redux（React）管理状态：

```javascript
// stores/translation.js
export const useTranslationStore = defineStore('translation', {
  state: () => ({
    currentTask: null,
    history: [],
    glossary: {},
    styles: []
  }),
  
  actions: {
    async translate(text, options) {
      // 调用API并建立WebSocket连接
    },
    
    async loadHistory() {
      // 加载历史记录
    }
  }
})
```

## 七、部署方案

### 7.1 开发环境

```bash
# 后端
cd web/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd web/frontend
npm install
npm run dev
```

### 7.2 生产环境

#### 选项1: Docker部署

```dockerfile
# Dockerfile.backend
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 选项2: 云服务部署

- **后端**: Railway, Render, Fly.io, 或自建服务器
- **前端**: Vercel, Netlify, 或CDN

## 八、安全考虑（组内使用简化版）

> **重要说明**: 对于组内使用的服务，我们采用**简化但必要**的安全措施，既保证基本安全，又不过度复杂化。

### 8.1 必须实施的安全措施 ⚠️

#### 1. API密钥保护（最高优先级）
**为什么必须**: API密钥泄露会导致账户被盗用，产生高额费用。

**实现方式**:
```python
# 后端：所有API密钥只存在于服务器端
# .env 文件（不提交到Git）
OPENROUTER_API_KEY=sk-or-v1-xxx
QWEN_API_KEY=xxx

# 前端：绝对不包含任何API密钥
# 所有翻译请求都通过后端API转发
```

**检查清单**:
- ✅ API密钥只存在于后端环境变量
- ✅ `.env` 文件已加入 `.gitignore`
- ✅ 前端代码中没有任何API密钥
- ✅ 不在日志中输出完整密钥

#### 2. 基本访问控制（防止外部访问）
**为什么必须**: 防止服务被外部滥用，保护API配额。

**实现方式**:

**方案A: IP白名单（推荐，最简单）**
```python
# backend/app/middleware/ip_whitelist.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

ALLOWED_IPS = [
    "192.168.1.0/24",  # 内网段
    "10.0.0.0/8",      # 内网段
    "127.0.0.1",       # 本地
]

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if not self.is_allowed(client_ip):
            raise HTTPException(status_code=403, detail="Access denied")
        return await call_next(request)
```

**方案B: 简单Token认证（更灵活）**
```python
# 在环境变量中设置一个简单的共享Token
SHARED_TOKEN = os.getenv("SHARED_TOKEN", "your-group-secret-token")

# API请求头中携带
# Authorization: Bearer your-group-secret-token

@app.middleware("http")
async def verify_token(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token != SHARED_TOKEN:
            return JSONResponse({"detail": "Invalid token"}, status_code=403)
    return await call_next(request)
```

**推荐**: 对于组内使用，**方案A（IP白名单）**更简单，如果部署在内网，基本就足够了。

#### 3. 请求限制（防止误用）
**为什么必须**: 防止误操作或恶意请求导致API费用过高。

**实现方式**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/translate")
@limiter.limit("10/minute")  # 每分钟最多10次请求
async def translate(request: Request, ...):
    ...
```

**建议限制**:
- 单次翻译: 10次/分钟
- 文本长度: 最大10000字符
- 文件大小: 最大5MB

#### 4. 输入验证（防止恶意输入）
**为什么必须**: 防止恶意输入导致服务异常或安全问题。

**实现方式**:
```python
from pydantic import BaseModel, validator

class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "zh"
    style: str = "general"
    
    @validator('text')
    def validate_text(cls, v):
        if len(v) > 10000:
            raise ValueError('文本长度不能超过10000字符')
        if not v.strip():
            raise ValueError('文本不能为空')
        return v.strip()
    
    @validator('style')
    def validate_style(cls, v):
        allowed_styles = ["general", "native", "business", "academic", 
                         "technical", "literary", "news", "colloquial", "legal"]
        if v not in allowed_styles:
            raise ValueError(f'不支持的风格: {v}')
        return v
```

#### 5. CORS配置（限制来源）
**为什么必须**: 防止其他网站调用你的API。

**实现方式**:
```python
from fastapi.middleware.cors import CORSMiddleware

# 开发环境：允许本地访问
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite默认端口
    "http://127.0.0.1:3000",
]

# 生产环境：只允许组内域名
if os.getenv("ENV") == "production":
    allowed_origins = [
        "https://your-internal-domain.com",
        "http://192.168.1.100:3000",  # 内网地址
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 8.2 可选的安全措施（根据需求）

#### 1. 简单密码保护（如果需要）
如果担心IP白名单不够，可以加一个简单的密码：

```python
# 在环境变量中设置
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "")

# 前端首次访问时输入密码，保存在localStorage
# 后端验证密码后返回一个简单的session token
```

**实现复杂度**: 低
**推荐度**: 如果部署在公网，建议添加

#### 2. 使用统计和监控（推荐）
虽然不是安全措施，但对组内使用很有用：

```python
# 记录每次翻译的使用情况
# - 谁使用了（IP地址）
# - 什么时候使用
# - 使用了多少token
# - 费用估算

# 可以设置每日/每月使用限额
DAILY_LIMIT = 100  # 每天最多100次翻译
```

### 8.3 不需要的复杂功能 ❌

对于组内使用，**不需要**以下功能：

1. ❌ **完整的用户系统**（注册/登录/权限管理）
   - 原因: 组内使用，不需要区分用户
   - 替代: IP白名单或简单Token即可

2. ❌ **JWT Token认证**
   - 原因: 过于复杂，组内使用不需要
   - 替代: 简单的共享Token或IP白名单

3. ❌ **数据库存储用户信息**
   - 原因: 不需要用户管理
   - 替代: 历史记录可以存储在文件或简单的SQLite

4. ❌ **OAuth/第三方登录**
   - 原因: 完全不需要

### 8.4 安全配置示例

#### 最小化安全配置（推荐）

```python
# backend/app/config.py
import os
from typing import List

class SecurityConfig:
    # API密钥（从环境变量读取，不硬编码）
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    QWEN_API_KEY = os.getenv("QWEN_API_KEY")
    
    # 访问控制
    ALLOWED_IPS: List[str] = [
        "127.0.0.1",
        "192.168.1.0/24",  # 内网段
    ]
    
    # 可选：简单Token（如果IP白名单不够）
    SHARED_TOKEN = os.getenv("SHARED_TOKEN", "")
    USE_TOKEN_AUTH = bool(SHARED_TOKEN)
    
    # 请求限制
    RATE_LIMIT = "10/minute"  # 每分钟10次
    MAX_TEXT_LENGTH = 10000   # 最大文本长度
    
    # CORS
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    # 生产环境配置
    if os.getenv("ENV") == "production":
        ALLOWED_ORIGINS = [
            os.getenv("FRONTEND_URL", "http://localhost:3000")
        ]
```

#### 环境变量示例（.env）

```bash
# API密钥（必须）
OPENROUTER_API_KEY=sk-or-v1-your-key-here
QWEN_API_KEY=your-qwen-key-here

# 访问控制（可选）
SHARED_TOKEN=your-group-secret-token-12345

# 环境配置
ENV=development  # development 或 production
FRONTEND_URL=http://localhost:3000

# 使用限制（可选）
DAILY_LIMIT=100
```

### 8.5 安全检查清单

部署前请确认：

- [ ] ✅ API密钥只存在于后端环境变量，不在代码中
- [ ] ✅ `.env` 文件已加入 `.gitignore`
- [ ] ✅ 已配置IP白名单或Token认证
- [ ] ✅ 已配置CORS，限制允许的来源
- [ ] ✅ 已配置请求速率限制
- [ ] ✅ 已配置输入验证（文本长度、格式等）
- [ ] ✅ 前端代码中没有任何API密钥
- [ ] ✅ 日志中不输出敏感信息（完整密钥等）
- [ ] ✅ 如果部署在公网，已配置防火墙规则

### 8.6 总结

**组内使用推荐的安全方案**:

1. **必须**: API密钥保护 + IP白名单 + 请求限制 + 输入验证 + CORS
2. **可选**: 简单Token认证（如果IP白名单不够灵活）
3. **不需要**: 用户系统、JWT、OAuth等复杂认证

**实现复杂度**: 低（1-2天即可完成）
**安全级别**: 中等（适合组内使用，不适合公开服务）

## 九、后续扩展

1. **用户系统**
   - 用户注册/登录
   - 个人历史记录
   - 个人术语表

2. **高级功能**
   - 翻译记忆库（TM）
   - 协作翻译
   - API密钥管理界面

3. **移动端**
   - 响应式设计优化
   - PWA支持
   - 移动App

4. **分析统计**
   - 使用统计
   - 质量分析
   - 性能监控

## 十、开发资源

### 推荐学习资源

- FastAPI官方文档: https://fastapi.tiangolo.com/
- Vue 3文档: https://vuejs.org/
- Element Plus文档: https://element-plus.org/
- WebSocket教程: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket

### 开发工具

- **后端**: VS Code, PyCharm
- **前端**: VS Code, WebStorm
- **API测试**: Postman, Insomnia
- **版本控制**: Git

---

## 总结

本方案提供了一个完整的Web界面开发计划，包括：
- ✅ 清晰的技术选型
- ✅ 详细的架构设计
- ✅ 完整的API设计
- ✅ 具体的实现步骤
- ✅ 部署和安全考虑

建议按照阶段逐步实施，先完成核心功能，再逐步完善。

