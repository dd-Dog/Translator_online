"""
FastAPI主应用
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import app_config, security_config
from app.middleware.ip_whitelist import IPWhitelistMiddleware
from app.middleware.token_auth import TokenAuthMiddleware
from app.api import translate, history, glossary, config, websocket, evaluation

# 创建FastAPI应用
app = FastAPI(
    title=app_config.APP_NAME,
    version=app_config.APP_VERSION,
    description="多模型协作翻译系统Web API"
)

# 速率限制
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全中间件
# 只有当ALLOWED_IPS不为空时才启用IP白名单
allowed_ips = security_config.ALLOWED_IPS
if allowed_ips:
    app.add_middleware(IPWhitelistMiddleware, allowed_ips=allowed_ips)
    print(f"🔒 IP白名单中间件已启用: {allowed_ips}")
else:
    print("⚠️  IP白名单中间件未启用（允许所有IP访问）")

if security_config.USE_TOKEN_AUTH:
    app.add_middleware(TokenAuthMiddleware)


# 健康检查
@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "version": app_config.APP_VERSION}


# 注册路由
app.include_router(translate.router)
app.include_router(history.router)
app.include_router(glossary.router)
app.include_router(config.router)
app.include_router(websocket.router)
app.include_router(evaluation.router)


# 启动事件
@app.on_event("startup")
async def startup():
    """启动时执行"""
    # 验证配置
    errors = security_config.validate()
    if errors:
        print("⚠️ 配置警告:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 配置验证通过")
    
    print(f"🚀 {app_config.APP_NAME} v{app_config.APP_VERSION} 启动成功")
    print(f"📝 API文档: http://localhost:8000/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=app_config.DEBUG
    )

