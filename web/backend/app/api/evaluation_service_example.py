"""
评估服务API调用示例
这个文件展示了如何调用外部评估服务API
"""

import os
import requests
from typing import Dict, Optional


def call_evaluation_service(
    source: str,
    translation: str,
    reference: Optional[str] = None,
    evaluation_service_url: Optional[str] = None
) -> Dict:
    """
    调用外部评估服务API
    
    Args:
        source: 源文本
        translation: 翻译文本
        reference: 参考译文（可选）
        evaluation_service_url: 评估服务URL（可选，从环境变量读取）
    
    Returns:
        评估结果字典，包含各种评估指标
    """
    # 从环境变量获取评估服务URL
    if not evaluation_service_url:
        evaluation_service_url = os.getenv(
            "EVALUATION_SERVICE_URL",
            "http://localhost:8001"  # 默认评估服务地址
        )
    
    try:
        # 调用评估服务API
        response = requests.post(
            f"{evaluation_service_url}/api/evaluate",
            json={
                "source": source,
                "translation": translation,
                "reference": reference
            },
            timeout=30  # 30秒超时
        )
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        # 如果评估服务不可用，返回错误信息
        return {
            "error": f"评估服务调用失败: {str(e)}",
            "scores": {}
        }


# 使用示例：
# 在 evaluation.py 中导入并使用：
# from app.api.evaluation_service_example import call_evaluation_service
# 
# result = call_evaluation_service(
#     source=evaluate_request.source,
#     translation=evaluate_request.translation,
#     reference=evaluate_request.reference
# )

