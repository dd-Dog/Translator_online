"""
响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Union, Any
from datetime import datetime


class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    status: str = Field(..., description="任务状态: pending, processing, completed, failed")
    message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class QualityScore(BaseModel):
    """质量评分"""
    adequacy: float = Field(..., ge=0, le=1, description="充分性")
    fluency: float = Field(..., ge=0, le=1, description="流畅性")
    terminology: float = Field(..., ge=0, le=1, description="术语准确性")
    overall: float = Field(..., ge=0, le=1, description="总体评分")


class TranslationResult(BaseModel):
    """翻译结果"""
    translated_text: str
    source_lang: str
    target_lang: str
    style: str
    quality_score: Optional[QualityScore] = None
    processing_stages: List[Union[str, Dict[str, Any]]] = Field(default_factory=list, description="处理阶段列表，可以是字符串或包含详细信息的字典")
    explainability_report: Optional[Dict] = None


class TranslateResponse(BaseModel):
    """翻译响应"""
    task_id: str
    status: str
    message: str
    result: Optional[TranslationResult] = None
    error: Optional[str] = None


class HistoryItem(BaseModel):
    """历史记录项"""
    task_id: str
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    style: str
    quality_score: Optional[float] = None
    created_at: datetime
    evaluation_result: Optional[dict] = None  # 评估结果，用于显示评分
    
    class Config:
        # 允许额外字段，以便前端可以访问evaluation_result
        extra = "allow"


class HistoryResponse(BaseModel):
    """历史记录响应"""
    total: int
    page: int
    page_size: int
    items: List[HistoryItem]


class GlossaryResponse(BaseModel):
    """术语表响应"""
    glossary: Dict[str, str]


class StyleInfo(BaseModel):
    """风格信息"""
    id: str
    name: str
    description: str


class ConfigResponse(BaseModel):
    """配置响应"""
    styles: List[StyleInfo]
    models: Dict[str, str]
    model_status: Dict[str, str]


class WebSocketMessage(BaseModel):
    """WebSocket消息"""
    type: str = Field(..., description="消息类型: progress, stage_complete, completed, error")
    task_id: str
    data: Dict

