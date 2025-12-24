"""
评估API
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import Optional
import os
import sys
from pathlib import Path
from app.config import security_config

router = APIRouter(prefix="/api/v1", tags=["evaluation"])

# 速率限制
limiter = Limiter(key_func=get_remote_address)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 尝试导入评估服务
try:
    from src.utils.evaluation_service import EvaluationService
    HAS_EVALUATION_SERVICE = True
except ImportError:
    HAS_EVALUATION_SERVICE = False
    EvaluationService = None


class EvaluateRequest(BaseModel):
    """评估请求"""
    source: str
    translation: str
    reference: Optional[str] = None


@router.post("/evaluation/evaluate")
@limiter.limit("5/minute")
async def evaluate(request: Request, evaluate_request: EvaluateRequest):
    """
    评估翻译结果
    使用项目中的评估服务模块
    """
    try:
        # 优先使用项目中的评估服务
        if HAS_EVALUATION_SERVICE:
            try:
                # 尝试使用API模式
                eval_service = EvaluationService(use_api=True)
                result = eval_service.evaluate(
                    translation=evaluate_request.translation,
                    reference=evaluate_request.reference or evaluate_request.translation,  # 如果没有参考译文，使用翻译本身
                    source=evaluate_request.source
                )
                
                if result:
                    # 转换为前端需要的格式
                    scores = {}
                    if result.get('bleu') is not None:
                        scores['BLEU'] = result['bleu']
                    if result.get('bertscore_f1') is not None:
                        scores['BERTScore'] = result['bertscore_f1']
                    if result.get('comet') is not None:
                        scores['COMET'] = result['comet']
                    if result.get('bleurt') is not None:
                        scores['BLEURT'] = result['bleurt']
                    if result.get('chrf') is not None:
                        scores['ChrF'] = result['chrf']
                    
                    # 计算总体评分
                    overall = result.get('final_score', 0.0)
                    if overall == 0.0 and scores:
                        overall = sum(scores.values()) / len(scores)
                    
                    return {
                        "scores": scores,
                        "overall": overall,
                        "message": "评估完成（API模式）"
                    }
            except Exception as e:
                # 如果API模式失败，尝试本地模式
                try:
                    eval_service = EvaluationService(use_api=False)
                    result = eval_service.evaluate(
                        translation=evaluate_request.translation,
                        reference=evaluate_request.reference or evaluate_request.translation,
                        source=evaluate_request.source
                    )
                    
                    if result:
                        scores = {}
                        if result.get('bleu') is not None:
                            scores['BLEU'] = result['bleu']
                        if result.get('bertscore_f1') is not None:
                            scores['BERTScore'] = result['bertscore_f1']
                        if result.get('comet') is not None:
                            scores['COMET'] = result['comet']
                        if result.get('bleurt') is not None:
                            scores['BLEURT'] = result['bleurt']
                        if result.get('chrf') is not None:
                            scores['ChrF'] = result['chrf']
                        
                        overall = result.get('final_score', 0.0)
                        if overall == 0.0 and scores:
                            overall = sum(scores.values()) / len(scores)
                        
                        return {
                            "scores": scores,
                            "overall": overall,
                            "message": "评估完成（本地模式）"
                        }
                except Exception as e2:
                    return {
                        "scores": {},
                        "overall": 0.0,
                        "error": f"评估失败: {str(e2)}",
                        "message": "评估服务不可用，请检查评估服务配置"
                    }
        
        # 如果没有评估服务，返回错误
        return {
            "scores": {},
            "overall": 0.0,
            "error": "评估服务不可用",
            "message": "请配置评估服务（EVALUATION_SERVICE_URL环境变量或本地评估库）"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluation/{task_id}")
async def get_evaluation_result(task_id: str):
    """
    获取评估结果
    """
    # TODO: 实现获取评估结果的逻辑
    raise HTTPException(status_code=501, detail="功能开发中")

