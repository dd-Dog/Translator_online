"""
IP白名单中间件
"""
import ipaddress
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import security_config


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP白名单中间件"""
    
    def __init__(self, app, allowed_ips: list = None):
        super().__init__(app)
        self.allowed_ips = []
        allowed = allowed_ips or security_config.ALLOWED_IPS
        
        for ip in allowed:
            try:
                # 支持CIDR格式，如 "192.168.1.0/24"
                self.allowed_ips.append(ipaddress.ip_network(ip, strict=False))
            except ValueError:
                # 单个IP地址
                try:
                    self.allowed_ips.append(ipaddress.ip_address(ip))
                except ValueError:
                    print(f"无效的IP地址: {ip}")
    
    def is_allowed(self, client_ip: str) -> bool:
        """检查IP是否允许"""
        if not self.allowed_ips:
            return True  # 如果没有配置，允许所有
        
        try:
            client = ipaddress.ip_address(client_ip)
            for allowed in self.allowed_ips:
                if isinstance(allowed, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
                    if client in allowed:
                        return True
                else:
                    if client == allowed:
                        return True
            return False
        except ValueError:
            return False
    
    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查等公开端点
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        if not self.is_allowed(client_ip):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied from {client_ip}"
            )
        return await call_next(request)

