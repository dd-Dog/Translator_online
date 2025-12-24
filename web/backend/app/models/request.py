"""
请求模型
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict


class ModelConfig(BaseModel):
    """模型配置"""
    model_type: str = Field(..., description="模型类型（如deepseek, qwen, doubao等）")
    api_key: str = Field(..., min_length=1, description="API密钥")
    
    class Config:
        extra = "allow"  # 允许额外字段


class TranslateRequest(BaseModel):
    """翻译请求"""
    text: str = Field(..., min_length=1, max_length=10000, description="待翻译文本")
    source_lang: str = Field(default="auto", description="源语言，auto表示自动检测")
    target_lang: str = Field(default="zh", description="目标语言")
    style: str = Field(default="general", description="翻译风格")
    glossary: Dict[str, str] = Field(default_factory=dict, description="术语表")
    stream: bool = Field(default=False, description="是否流式返回进度")
    # 每个阶段的模型配置（可选，如果不提供则使用默认配置）
    model_configs: Optional[Dict[str, ModelConfig]] = Field(
        default=None,
        description="各阶段的模型配置，格式：{'planner': {'model_type': 'deepseek', 'api_key': 'xxx'}, ...}"
    )
    
    @validator('text')
    def validate_text(cls, v):
        if len(v) > 10000:
            raise ValueError('文本长度不能超过10000字符')
        if not v.strip():
            raise ValueError('文本不能为空')
        return v.strip()
    
    @validator('style')
    def validate_style(cls, v):
        allowed = ["general", "native", "business", "academic", 
                  "technical", "literary", "news", "colloquial", "legal"]
        if v not in allowed:
            raise ValueError(f'不支持的风格: {v}')
        return v
    
    @validator('glossary')
    def validate_glossary(cls, v):
        if len(v) > 100:
            raise ValueError('术语表不能超过100条')
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError('术语表格式错误')
            if len(key) > 50 or len(value) > 100:
                raise ValueError('术语或翻译过长')
        return v


class GlossaryUpdateRequest(BaseModel):
    """术语表更新请求"""
    glossary: Dict[str, str] = Field(..., description="术语表")


class GlossaryItemRequest(BaseModel):
    """单个术语请求"""
    term: str = Field(..., min_length=1, max_length=50, description="术语")
    translation: str = Field(..., min_length=1, max_length=100, description="翻译")

