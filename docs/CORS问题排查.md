# CORS 问题排查指南

## 问题现象

使用 Nginx 后，前端访问后端 API 时出现 CORS 错误：
```
Access to XMLHttpRequest at 'http://47.254.82.238:8000/api/v1/translate' 
from origin 'http://47.254.82.238:8088' 
has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## 解决方案

### 方案1: 后端直接处理 CORS（最简单）

#### 步骤1: 修改后端 `.env` 文件

在 `web/backend/.env` 中添加：

```env
# 允许所有源（开发/测试环境）
ALLOWED_ORIGINS=*

# 或指定具体域名（生产环境推荐）
ALLOWED_ORIGINS=http://47.254.82.238:8088,http://47.254.82.238
```

#### 步骤2: 重启后端服务

```bash
# 停止当前服务（Ctrl+C）
cd ~/agent/translator_online/Translator_online/web/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 步骤3: 验证

在浏览器控制台测试：

```javascript
fetch('http://47.254.82.238:8000/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

如果没有 CORS 错误，说明配置成功。

### 方案2: Nginx 处理 CORS

如果后端无法修改或需要 Nginx 统一处理，使用以下配置：

#### Nginx 配置

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
        
        # CORS 头
        add_header 'Access-Control-Allow-Origin' '$http_origin' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        
        # 处理 OPTIONS 预检请求
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '$http_origin' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
```

#### 应用配置

```bash
# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

### 方案3: 使用同一域名（最佳实践）

将前端和后端都通过 Nginx 代理，使用同一域名，完全避免 CORS 问题。

#### Nginx 配置

```nginx
server {
    listen 80;
    server_name 47.254.82.238;

    # 前端静态文件
    location / {
        root /path/to/web/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理（同一域名，无需CORS）
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
```

#### 修改前端 API 地址

修改 `web/frontend/src/api/index.js`：

```javascript
// 使用相对路径，自动使用当前域名
const api = axios.create({
  baseURL: '/api',  // 而不是 'http://47.254.82.238:8000'
  timeout: 30000,
  // ...
})
```

修改 `web/frontend/src/stores/translation.js` 中的 WebSocket 地址：

```javascript
// 使用相对路径
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsUrl = `${protocol}//${window.location.host}/ws/translate/${response.task_id}`
```

## 排查步骤

### 1. 检查后端 CORS 配置

```bash
# 查看后端日志
tail -f /path/to/backend/logs/app.log

# 检查 .env 文件
cat web/backend/.env | grep ALLOWED_ORIGINS
```

### 2. 测试后端 API

```bash
# 直接测试后端
curl -v http://127.0.0.1:8000/health

# 检查响应头
curl -v -H "Origin: http://47.254.82.238:8088" \
  http://127.0.0.1:8000/health
```

应该看到响应头中包含：
```
Access-Control-Allow-Origin: http://47.254.82.238:8088
```

### 3. 测试 Nginx 代理

```bash
# 测试 Nginx 代理
curl -v http://47.254.82.238/api/health

# 检查响应头
curl -v -H "Origin: http://47.254.82.238:8088" \
  http://47.254.82.238/api/health
```

### 4. 检查浏览器网络请求

1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 查看失败的请求
4. 检查 Request Headers 和 Response Headers
5. 确认是否有 `Access-Control-Allow-Origin` 头

### 5. 检查 Nginx 日志

```bash
# 查看访问日志
sudo tail -f /var/log/nginx/access.log

# 查看错误日志
sudo tail -f /var/log/nginx/error.log
```

## 常见问题

### Q: 设置了 `ALLOWED_ORIGINS=*` 还是不行？

A: 检查：
1. 后端服务是否重启
2. `.env` 文件是否在正确位置
3. 环境变量是否正确加载（查看后端启动日志）

### Q: Nginx 配置了 CORS 还是不行？

A: 检查：
1. Nginx 配置是否正确重载：`sudo systemctl reload nginx`
2. `add_header` 指令是否在正确的位置
3. OPTIONS 预检请求是否正确处理

### Q: 使用同一域名后还是报错？

A: 检查：
1. 前端 API 地址是否改为相对路径
2. WebSocket 地址是否改为相对路径
3. 前端是否重新构建：`npm run build`

## 快速修复命令

```bash
# 1. 修改后端 .env
echo "ALLOWED_ORIGINS=*" >> web/backend/.env

# 2. 重启后端
cd web/backend
source venv/bin/activate
pkill -f uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 3. 测试
curl -v -H "Origin: http://47.254.82.238:8088" \
  http://127.0.0.1:8000/health
```

## 推荐方案

**开发/测试环境**：使用方案1（后端直接处理，设置 `ALLOWED_ORIGINS=*`）

**生产环境**：使用方案3（同一域名，通过 Nginx 代理，完全避免 CORS）

