"""
评估器环境配置工具
支持从指定的 conda 环境导入 translation_evaluator
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
import yaml


def find_conda_python(env_name: str) -> Optional[Path]:
    """
    查找 conda 环境的 Python 可执行文件路径
    
    Args:
        env_name: conda 环境名称
        
    Returns:
        Python 可执行文件路径，如果未找到则返回 None
    """
    # 方法1: 使用 conda info 查找环境路径
    try:
        result = subprocess.run(
            ["conda", "info", "--envs"],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.splitlines():
            # 跳过注释行和空行
            if line.startswith("#") or not line.strip():
                continue
            # 检查是否包含环境名称（精确匹配，避免部分匹配）
            parts = line.split()
            if len(parts) >= 2 and parts[0] == env_name:
                # 取最后一个部分作为路径（处理路径中可能有空格的情况）
                env_path_str = parts[-1]
                env_path = Path(env_path_str)
                python_path = env_path / "python.exe" if os.name == "nt" else env_path / "bin" / "python"
                if python_path.exists():
                    return python_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # 方法2: 尝试常见的 conda 安装路径
    common_conda_paths = [
        Path.home() / "miniconda3" / "envs" / env_name,
        Path.home() / "anaconda3" / "envs" / env_name,
        Path("C:/Users") / os.getenv("USERNAME", "") / "miniconda3" / "envs" / env_name,
        Path("C:/Users") / os.getenv("USERNAME", "") / "anaconda3" / "envs" / env_name,
    ]
    
    for env_path in common_conda_paths:
        python_path = env_path / "python.exe" if os.name == "nt" else env_path / "bin" / "python"
        if python_path.exists():
            return python_path
    
    # 方法3: 使用 conda run（如果可用）
    try:
        result = subprocess.run(
            ["conda", "run", "-n", env_name, "which", "python"],
            capture_output=True,
            text=True,
            check=True
        )
        python_path = Path(result.stdout.strip())
        if python_path.exists():
            return python_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return None


def get_evaluator_python_path(config_path: Optional[Path] = None) -> Optional[Path]:
    """
    从配置文件读取评估器环境配置，返回 Python 路径
    
    Args:
        config_path: 配置文件路径，默认为 config/evaluation.yaml
        
    Returns:
        Python 可执行文件路径，如果使用当前环境则返回 None
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "evaluation.yaml"
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        evaluator_config = config.get('evaluator_env', {})
        
        # 如果明确设置了 use_current_env: true，则使用当前环境
        if evaluator_config.get('use_current_env') is True:
            return None
        
        # 方式1: 使用 conda 环境名称（优先）
        if 'conda_env_name' in evaluator_config:
            env_name = evaluator_config['conda_env_name']
            python_path = find_conda_python(env_name)
            if python_path:
                return python_path
            else:
                print(f"[WARN] 未找到 conda 环境: {env_name}")
        
        # 方式2: 直接指定 Python 路径
        if 'python_path' in evaluator_config:
            python_path = Path(evaluator_config['python_path'])
            if python_path.exists():
                return python_path
            else:
                print(f"[WARN] Python 路径不存在: {python_path}")
        
        # 如果都没有配置，默认使用当前环境
        return None
        
    except Exception as e:
        print(f"[WARN] 读取评估器配置失败: {e}")
    
    return None


def add_evaluator_to_path(python_path: Optional[Path] = None, evaluator_lib_path: Optional[Path] = None):
    """
    将评估器库添加到 sys.path
    
    Args:
        python_path: 评估器环境的 Python 路径（如果指定了 conda 环境）
        evaluator_lib_path: 评估器库的路径
    """
    if python_path is None:
        # 使用当前环境，直接添加库路径
        if evaluator_lib_path and evaluator_lib_path.exists():
            sys.path.insert(0, str(evaluator_lib_path))
            # 也添加 site-packages 路径（如果库已安装）
            site_packages = evaluator_lib_path / "translation_evaluator"
            if site_packages.exists():
                sys.path.insert(0, str(evaluator_lib_path))
        return
    
    # 使用指定环境的 Python，添加其 site-packages 到路径
    if python_path.exists():
        # 找到 site-packages 目录
        if os.name == "nt":  # Windows
            env_root = python_path.parent.parent
        else:  # Linux/Mac
            env_root = python_path.parent.parent
        
        # 尝试多个可能的 site-packages 路径
        possible_paths = [
            env_root / "Lib" / "site-packages",  # Windows
            env_root / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",  # Linux/Mac
        ]
        
        for site_packages in possible_paths:
            if site_packages.exists():
                sys.path.insert(0, str(site_packages))
                print(f"[OK] 已添加评估器环境 site-packages: {site_packages}")
                break
        
        # 如果库路径存在，也添加
        if evaluator_lib_path and evaluator_lib_path.exists():
            sys.path.insert(0, str(evaluator_lib_path))
            print(f"[OK] 已添加评估库路径: {evaluator_lib_path}")


def setup_evaluator_environment(evaluator_lib_path: Optional[Path] = None) -> Tuple[Optional[Path], bool]:
    """
    设置评估器环境
    
    Args:
        evaluator_lib_path: 评估器库的路径（可选，会自动查找）
        
    Returns:
        (python_path, success): Python 路径和是否成功设置
    """
    # 读取配置
    python_path = get_evaluator_python_path()
    
    # 如果未指定库路径，尝试自动查找
    if evaluator_lib_path is None:
        current_file = Path(__file__).resolve()
        evaluator_lib_path = current_file.parent.parent.parent.parent / "translation_evaluator"
        if not evaluator_lib_path.exists():
            evaluator_lib_path = current_file.parent.parent.parent / "translation_evaluator"
    
    # 添加路径
    add_evaluator_to_path(python_path, evaluator_lib_path)
    
    if python_path:
        print(f"[OK] 使用评估器 conda 环境: {python_path}")
        return python_path, True
    else:
        print("[OK] 使用当前 Python 环境")
        return None, True

