"""
应用配置
"""
import os
from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载.env文件
# 优先从web/backend目录查找，如果不存在则从项目根目录查找
env_file = Path(__file__).parent.parent / ".env"
if not env_file.exists():
    env_file = Path(__file__).parent.parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # 如果都不存在，尝试从当前工作目录加载
    load_dotenv()


class SecurityConfig:
    """安全配置"""
    
    # 访问控制
    ALLOWED_IPS: List[str] = [
        "127.0.0.1",
        "192.168.1.0/24",  # 内网段，根据实际情况修改
        "10.0.0.0/8",      # 内网段
    ]
    
    # 请求限制
    RATE_LIMIT_TRANSLATE: str = "10/minute"
    RATE_LIMIT_HISTORY: str = "30/minute"
    RATE_LIMIT_GLOSSARY: str = "60/minute"
    
    # 输入限制
    MAX_TEXT_LENGTH: int = 10000
    MAX_GLOSSARY_SIZE: int = 100
    
    # CORS
    # 从环境变量读取允许的源，如果没有则使用默认值
    # 格式：ALLOWED_ORIGINS=http://example.com,http://example2.com
    _allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
    ALLOWED_ORIGINS: List[str] = (
        _allowed_origins_env.split(",") if _allowed_origins_env else [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )
    
    def __init__(self):
        # API密钥（必须从环境变量读取，在load_dotenv之后）
        self._openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self._qwen_key = os.getenv("QWEN_API_KEY")
        self._deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        self._shared_token = os.getenv("SHARED_TOKEN", "")
        self._env = os.getenv("ENV", "development")
    
    @property
    def OPENROUTER_API_KEY(self) -> Optional[str]:
        return self._openrouter_key
    
    @property
    def QWEN_API_KEY(self) -> Optional[str]:
        return self._qwen_key
    
    @property
    def DEEPSEEK_API_KEY(self) -> Optional[str]:
        return self._deepseek_key
    
    @property
    def SHARED_TOKEN(self) -> str:
        return self._shared_token
    
    @property
    def USE_TOKEN_AUTH(self) -> bool:
        return bool(self._shared_token)
    
    @property
    def ENV(self) -> str:
        return self._env
    
    @classmethod
    def validate(cls) -> List[str]:
        """验证配置"""
        errors = []
        # 重新读取环境变量（确保是最新的）
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not openrouter_key and not deepseek_key:
            errors.append("至少需要配置 OPENROUTER_API_KEY 或 DEEPSEEK_API_KEY")
            errors.append(f"当前 OPENROUTER_API_KEY: {'已配置' if openrouter_key else '未配置'}")
            errors.append(f"当前 DEEPSEEK_API_KEY: {'已配置' if deepseek_key else '未配置'}")
            # 检查.env文件位置
            env_file_path = Path(__file__).parent.parent / ".env"
            if not env_file_path.exists():
                env_file_path = Path(__file__).parent.parent.parent.parent / ".env"
            errors.append(f".env文件位置: {env_file_path} ({'存在' if env_file_path.exists() else '不存在'})")
            errors.append("提示: 请确保.env文件在web/backend目录或项目根目录，并且变量名拼写正确（DEEPSEEK_API_KEY，不是DEEKSEEK_API_KEY）")
        
        env = os.getenv("ENV", "development")
        shared_token = os.getenv("SHARED_TOKEN", "")
        if env == "production" and not shared_token and not cls.ALLOWED_IPS:
            errors.append("生产环境必须配置访问控制（IP白名单或Token）")
        return errors


class AppConfig(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "多模型协作翻译系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("ENV", "development") == "development"
    
    # 项目根目录
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
    
    # 配置文件路径
    CONFIG_DIR: Path = PROJECT_ROOT / "config"
    MODELS_CONFIG: Path = CONFIG_DIR / "models.yaml"
    STYLES_CONFIG: Path = CONFIG_DIR / "styles.yaml"
    
    # 数据存储
    DATA_DIR: Path = PROJECT_ROOT / "web" / "backend" / "data"
    HISTORY_FILE: Path = DATA_DIR / "history.jsonl"
    GLOSSARY_FILE: Path = DATA_DIR / "glossary.json"
    
    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = 30  # 秒
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略未定义的环境变量，避免与 SecurityConfig 冲突


# 全局配置实例
app_config = AppConfig()
security_config = SecurityConfig()

# 确保数据目录存在
app_config.DATA_DIR.mkdir(parents=True, exist_ok=True)

