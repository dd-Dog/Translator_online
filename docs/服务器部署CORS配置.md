# 服务器部署 CORS 配置指南

## 问题描述

当将前端部署到服务器（如 `http://47.254.82.238:8088`）时，如果后端运行在 `localhost:8000`，会出现以下错误：

```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/translate' from origin 'http://47.254.82.238:8088' has been blocked by CORS policy
```

这是因为浏览器的安全策略不允许从公网IP访问localhost。

## 解决方案

### 方案1: 配置后端允许前端域名（推荐）

#### 1. 修改后端 `.env` 文件

在 `web/backend/.env` 文件中添加：

```env
# 允许的前端域名（多个用逗号分隔）
ALLOWED_ORIGINS=http://47.254.82.238:8088,http://47.254.82.238:3000
```

#### 2. 确保后端绑定到 0.0.0.0

启动后端时使用：

```bash
cd web/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**注意**：`--host 0.0.0.0` 很重要，这样后端才能从外部访问。

#### 3. 前端自动检测API地址

前端代码已更新，会自动检测当前域名并使用对应的API地址。如果前端运行在 `http://47.254.82.238:8088`，会自动使用 `http://47.254.82.238:8000` 作为API地址。

### 方案2: 使用环境变量配置前端API地址

#### 1. 创建前端 `.env` 文件

在 `web/frontend/` 目录下创建 `.env` 文件：

```env
# API基础地址
VITE_API_BASE_URL=http://47.254.82.238:8000

# WebSocket地址（可选，会自动从API地址推导）
VITE_WS_BASE_URL=ws://47.254.82.238:8000

# API端口（可选，默认8000）
VITE_API_PORT=8000
```

#### 2. 重新构建前端

```bash
cd web/frontend
npm run build
```

### 方案3: 使用Nginx反向代理（生产环境推荐）

#### 1. Nginx配置示例

```nginx
server {
    listen 80;
    server_name 47.254.82.238;

    # 前端静态文件
    location / {
        root /path/to/web/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 2. 修改后端CORS配置

使用Nginx后，前端和后端在同一域名下，CORS配置可以更宽松：

```env
# .env 文件
ALLOWED_ORIGINS=http://47.254.82.238
```

## 快速检查清单

- [ ] 后端已绑定到 `0.0.0.0`（不是 `localhost`）
- [ ] 后端 `.env` 中配置了 `ALLOWED_ORIGINS`，包含前端域名
- [ ] 后端防火墙已开放8000端口
- [ ] 前端能访问后端API（测试：`curl http://47.254.82.238:8000/health`）
- [ ] 浏览器控制台没有CORS错误

## 测试步骤

### 1. 测试后端是否可访问

```bash
# 从服务器本地测试
curl http://localhost:8000/health

# 从外部测试（替换为你的服务器IP）
curl http://47.254.82.238:8000/health
```

### 2. 测试CORS配置

在浏览器控制台执行：

```javascript
fetch('http://47.254.82.238:8000/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

如果没有CORS错误，说明配置正确。

### 3. 检查后端日志

启动后端后，查看日志中是否有：

```
✅ 配置验证通过
🚀 多模型协作翻译系统 v1.0.0 启动成功
```

## 常见问题

### Q: 为什么前端还是访问 localhost:8000？

A: 前端代码已更新为自动检测。如果还是访问localhost，可能是：
1. 浏览器缓存了旧的前端代码，需要强制刷新（Ctrl+F5）
2. 前端没有重新构建，需要 `npm run build` 或 `npm run dev`

### Q: WebSocket连接失败？

A: 确保：
1. WebSocket地址使用 `ws://`（HTTP）或 `wss://`（HTTPS）
2. 后端已启动并绑定到 `0.0.0.0`
3. 防火墙允许WebSocket连接

### Q: 生产环境应该使用什么方案？

A: 推荐使用 **方案3（Nginx反向代理）**，因为：
- 前端和后端在同一域名下，避免CORS问题
- 可以使用HTTPS（Let's Encrypt）
- 更好的安全性和性能
- 更容易管理

## 安全建议

1. **生产环境**：使用HTTPS和WSS
2. **IP白名单**：在 `app/config.py` 中配置 `ALLOWED_IPS`
3. **Token认证**：在 `.env` 中配置 `SHARED_TOKEN`
4. **防火墙**：只开放必要的端口（80, 443, 8000）

