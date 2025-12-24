# Web后端服务

## 快速开始

### 1. 安装依赖

```bash
cd web/backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的API密钥：

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
QWEN_API_KEY=your-qwen-key-here
DEEPSEEK_API_KEY=your-deepseek-key-here

# 可选：Token认证
SHARED_TOKEN=your-group-secret-token-12345

ENV=development
```

### 3. 配置IP白名单（可选）

编辑 `app/config.py` 中的 `ALLOWED_IPS`：

```python
ALLOWED_IPS: List[str] = [
    "127.0.0.1",
    "192.168.1.0/24",  # 你的内网段
]
```

### 4. 启动服务

```bash
# 方式1: 使用uvicorn直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式2: 使用Python运行
python -m app.main
```

### 5. 访问API文档

打开浏览器访问：http://localhost:8000/docs

## API端点

- `POST /api/v1/translate` - 创建翻译任务
- `GET /api/v1/translate/{task_id}` - 获取翻译结果
- `GET /api/v1/translate/{task_id}/status` - 获取任务状态
- `GET /api/v1/history` - 获取翻译历史
- `DELETE /api/v1/history/{task_id}` - 删除历史记录
- `GET /api/v1/glossary` - 获取术语表
- `POST /api/v1/glossary` - 更新术语表
- `GET /api/v1/config/styles` - 获取翻译风格列表
- `GET /api/v1/config/models` - 获取模型配置
- `WS /ws/translate/{task_id}` - WebSocket实时进度

## 安全配置

参考 `docs/组内使用安全配置指南.md`

## 注意事项

1. 确保项目根目录的 `config/models.yaml` 配置正确
2. 确保API密钥已正确配置
3. 如果使用IP白名单，确保前端访问的IP在允许列表中
4. 如果使用Token认证，前端需要在请求头中携带Token

