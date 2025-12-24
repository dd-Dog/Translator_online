# Web前端应用

## 快速开始

### 1. 安装依赖

```bash
cd web/frontend
npm install
```

### 2. 配置环境变量（可选）

复制 `.env.example` 为 `.env.local`：

```bash
cp .env.example .env.local
```

编辑 `.env.local`（如果需要）：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SHARED_TOKEN=your-group-secret-token-12345
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:3000

### 4. 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录。

## 项目结构

```
src/
├── api/              # API客户端
├── stores/           # Pinia状态管理
├── views/            # 页面组件
├── router/           # 路由配置
└── App.vue          # 根组件
```

## 功能

- ✅ 文本翻译（支持9种风格）
- ✅ 实时进度显示（WebSocket）
- ✅ 翻译历史记录
- ✅ 术语表管理
- ✅ 质量评分展示

## 注意事项

1. 确保后端服务已启动（默认 http://localhost:8000）
2. 如果后端启用了Token认证，需要在 `.env.local` 中配置 `VITE_SHARED_TOKEN`
3. 如果后端启用了IP白名单，确保前端访问的IP在允许列表中

