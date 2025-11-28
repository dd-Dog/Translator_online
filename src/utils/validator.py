"""
配置验证工具
"""

from typing import Dict, Any
from pathlib import Path
import yaml


def validate_config(config_path: str) -> bool:
    """
    验证配置文件是否存在且格式正确
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        bool: 配置是否有效
    """
    path = Path(config_path)
    if not path.exists():
        return False
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        return True
    except Exception:
        return False


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Dict: 配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

