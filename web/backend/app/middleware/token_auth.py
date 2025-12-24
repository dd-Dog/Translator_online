"""
Token认证中间件
"""
import os
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import security_config


class TokenAuthMiddleware(BaseHTTPMiddleware):
    """Token认证中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.token = security_config.SHARED_TOKEN
        self.use_auth = security_config.USE_TOKEN_AUTH
    
    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查等公开端点
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
        
        # 检查API端点
        if request.url.path.startswith("/api/"):
            if self.use_auth and self.token:
                auth_header = request.headers.get("Authorization", "")
                token = auth_header.replace("Bearer ", "").strip()
                
                if token != self.token:
                    raise HTTPException(
                        status_code=403,
                        detail="Invalid or missing token"
                    )
            elif os.getenv("ENV") == "production" and not self.token:
                raise HTTPException(
                    status_code=500,
                    detail="Token authentication not configured for production"
                )
        
        return await call_next(request)

