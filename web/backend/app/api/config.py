"""
配置API
"""
from fastapi import APIRouter
import yaml
from pathlib import Path
from app.models.response import ConfigResponse, StyleInfo
from app.config import app_config

router = APIRouter(prefix="/api/v1", tags=["config"])


@router.get("/config/styles", response_model=list[StyleInfo])
async def get_styles():
    """
    获取翻译风格列表
    """
    try:
        if app_config.STYLES_CONFIG.exists():
            with open(app_config.STYLES_CONFIG, 'r', encoding='utf-8') as f:
                styles_config = yaml.safe_load(f)
            
            styles = []
            for style_id, style_data in styles_config.get('styles', {}).items():
                styles.append(StyleInfo(
                    id=style_id,
                    name=style_data.get('name', style_id),
                    description=style_data.get('description', '')
                ))
            return styles
        return []
    except Exception as e:
        print(f"加载风格配置失败: {e}")
        return []


@router.get("/config/models")
async def get_models():
    """
    获取模型配置和状态
    """
    try:
        if app_config.MODELS_CONFIG.exists():
            with open(app_config.MODELS_CONFIG, 'r', encoding='utf-8') as f:
                models_config = yaml.safe_load(f)
            
            workflow = models_config.get('workflow', {})
            models = {}
            model_status = {}
            
            # 获取工作流中使用的模型
            for agent, model_config in workflow.items():
                model_type = model_config.get('model', '') if isinstance(model_config, dict) else model_config
                models[agent] = model_type
                
                # 检查模型是否启用
                model_enabled = models_config.get('models', {}).get(model_type, {}).get('enabled', False)
                model_status[agent] = "available" if model_enabled else "disabled"
            
            return {
                "models": models,
                "model_status": model_status
            }
        return {"models": {}, "model_status": {}}
    except Exception as e:
        print(f"加载模型配置失败: {e}")
        return {"models": {}, "model_status": {}}

