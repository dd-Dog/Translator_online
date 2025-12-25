# Nginx 配置示例

## 问题描述

使用 Nginx 反向代理后，前端访问后端 API 时出现 CORS 错误。

## 解决方案

### 方案1: Nginx 处理 CORS（推荐）

在 Nginx 配置中添加 CORS 头，让 Nginx 处理跨域请求。

#### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name 47.254.82.238;

    # 前端静态文件
    location / {
        root /path/to/web/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # 后端API代理
    location /api {
        # 代理到后端
        proxy_pass http://127.0.0.1:8000;
        
        # 基本代理设置
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS 头设置
        add_header 'Access-Control-Allow-Origin' '$http_origin' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
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
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 超时设置
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
```

### 方案2: 后端处理 CORS（如果 Nginx 不处理）

如果 Nginx 不处理 CORS，确保后端配置正确。

#### 后端 `.env` 配置

```env
# 允许的前端域名
ALLOWED_ORIGINS=http://47.254.82.238:8088,http://47.254.82.238
```

#### 后端 CORS 配置检查

确保 `web/backend/app/config.py` 中的 `ALLOWED_ORIGINS` 包含前端域名。

### 方案3: 使用同一域名（最佳实践）

将前端和后端都通过 Nginx 代理，使用同一域名，避免 CORS 问题。

#### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name 47.254.82.238;

    # 前端静态文件
    location / {
        root /path/to/web/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # 后端API代理（同一域名）
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理（同一域名）
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
```

#### 前端配置调整

如果使用同一域名，前端 API 地址应该改为相对路径：

```javascript
// web/frontend/src/api/index.js
const api = axios.create({
  baseURL: '/api',  // 使用相对路径
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})
```

## 配置步骤

### 1. 创建 Nginx 配置文件

```bash
sudo nano /etc/nginx/sites-available/translator
```

### 2. 复制上述配置（根据你的需求选择方案）

### 3. 创建符号链接

```bash
sudo ln -s /etc/nginx/sites-available/translator /etc/nginx/sites-enabled/
```

### 4. 测试配置

```bash
sudo nginx -t
```

### 5. 重载 Nginx

```bash
sudo systemctl reload nginx
```

## 常见问题

### Q: 仍然出现 CORS 错误？

A: 检查以下几点：
1. Nginx 配置是否正确重载：`sudo systemctl reload nginx`
2. 后端 `.env` 中的 `ALLOWED_ORIGINS` 是否包含前端域名
3. 浏览器缓存：清除缓存或使用无痕模式
4. 检查 Nginx 错误日志：`sudo tail -f /var/log/nginx/error.log`

### Q: WebSocket 连接失败？

A: 确保：
1. Nginx 配置中包含 `/ws` 的代理配置
2. `proxy_set_header Upgrade` 和 `Connection` 设置正确
3. 超时时间设置足够长

### Q: 前端无法访问后端？

A: 检查：
1. 后端服务是否运行：`ps aux | grep uvicorn`
2. 后端端口是否正确：`netstat -tulpn | grep 8000`
3. Nginx 代理地址是否正确：`proxy_pass http://127.0.0.1:8000`

## 调试技巧

### 查看 Nginx 访问日志

```bash
sudo tail -f /var/log/nginx/access.log
```

### 查看 Nginx 错误日志

```bash
sudo tail -f /var/log/nginx/error.log
```

### 测试后端 API

```bash
curl -X GET http://127.0.0.1:8000/health
```

### 测试 Nginx 代理

```bash
curl -X GET http://47.254.82.238/api/health
```

## 完整配置示例（生产环境）

```nginx
# /etc/nginx/sites-available/translator

# 限制请求大小
client_max_body_size 10M;

# 上游后端服务器
upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name 47.254.82.238;

    # 日志
    access_log /var/log/nginx/translator_access.log;
    error_log /var/log/nginx/translator_error.log;

    # 前端静态文件
    location / {
        root /path/to/web/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端API代理
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # CORS 头（如果需要）
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
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 超时设置
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_connect_timeout 60s;
    }
}
```

## 注意事项

1. **路径替换**：将 `/path/to/web/frontend/dist` 替换为实际的前端构建目录路径
2. **域名替换**：将 `47.254.82.238` 替换为你的实际域名或IP
3. **HTTPS**：生产环境建议使用 HTTPS，可以使用 Let's Encrypt 免费证书
4. **防火墙**：确保防火墙允许 80 和 443 端口

