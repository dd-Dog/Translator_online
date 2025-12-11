"""
评估API客户端
用于翻译模块通过HTTP API调用评估服务
"""

import requests
from typing import Optional, Dict, List
from dataclasses import dataclass
import os
from pathlib import Path
import yaml


@dataclass
class EvaluationScore:
    """评估分数结果"""
    bleu: float = 0.0
    comet: float = 0.0
    bleurt: float = 0.0
    bertscore_f1: float = 0.0
    chrf: float = 0.0
    mqm_adequacy: float = 0.0
    mqm_fluency: float = 0.0
    mqm_terminology: float = 0.0
    mqm_overall: float = 0.0
    final_score: float = 0.0
    model_info: Dict = None
    
    def __post_init__(self):
        if self.model_info is None:
            self.model_info = {}


class EvaluationAPIClient:
    """评估API客户端"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:5001",
        timeout: int = 300,
        api_key: Optional[str] = None
    ):
        """
        初始化评估API客户端
        
        Args:
            base_url: 评估API服务器地址
            timeout: 请求超时时间（秒）
            api_key: API密钥（可选，用于认证）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.api_key = api_key
        self._session = requests.Session()
        
        if api_key:
            self._session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
    
    def health_check(self) -> bool:
        """
        检查评估服务是否可用
        
        Returns:
            bool: 服务是否健康
        """
        try:
            response = self._session.get(
                f"{self.base_url}/health",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            return False
        except Exception as e:
            print(f"[WARN] 评估服务健康检查失败: {e}")
            return False
    
    def evaluate(
        self,
        translation: str,
        reference: str,
        source: Optional[str] = None,
        mqm_score: Optional[Dict] = None
    ) -> Optional[EvaluationScore]:
        """
        评估单个翻译样本
        
        Args:
            translation: 翻译文本
            reference: 参考翻译
            source: 源文本（可选）
            mqm_score: MQM评分（可选）
            
        Returns:
            EvaluationScore: 评估分数，如果失败返回None
        """
        try:
            # 验证必需字段
            if not translation:
                print("[ERROR] translation字段为空")
                return None
            if not reference:
                print("[ERROR] reference字段为空，BLEURT需要reference字段")
                return None
            
            payload = {
                "translation": translation,
                "reference": reference
            }
            
            if source:
                payload["source"] = source
            
            if mqm_score:
                payload["mqm_score"] = mqm_score
            
            # 调试日志：确认payload包含reference
            print(f"[DEBUG] API请求payload包含字段: {list(payload.keys())}")
            print(f"[DEBUG] reference字段长度: {len(reference) if reference else 0} 字符")
            
            response = self._session.post(
                f"{self.base_url}/eval",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                score_data = result.get("score", {})
                return EvaluationScore(
                    bleu=score_data.get("bleu", 0.0),
                    comet=score_data.get("comet", 0.0),
                    bleurt=score_data.get("bleurt", 0.0),
                    bertscore_f1=score_data.get("bertscore_f1", 0.0),
                    chrf=score_data.get("chrf", 0.0),
                    mqm_adequacy=score_data.get("mqm_adequacy", 0.0),
                    mqm_fluency=score_data.get("mqm_fluency", 0.0),
                    mqm_terminology=score_data.get("mqm_terminology", 0.0),
                    mqm_overall=score_data.get("mqm_overall", 0.0),
                    final_score=score_data.get("final_score", 0.0),
                    model_info=score_data.get("model_info", {})
                )
            else:
                error = result.get("error", "未知错误")
                print(f"[ERROR] 评估失败: {error}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] 评估API请求失败: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] 评估处理失败: {e}")
            return None
    
    def evaluate_batch(
        self,
        translations: List[str],
        references: List[str],
        sources: Optional[List[str]] = None,
        mqm_scores: Optional[List[Dict]] = None
    ) -> Optional[List[EvaluationScore]]:
        """
        批量评估翻译样本
        
        Args:
            translations: 翻译文本列表
            references: 参考翻译列表
            sources: 源文本列表（可选）
            mqm_scores: MQM评分列表（可选）
            
        Returns:
            List[EvaluationScore]: 评估分数列表，如果失败返回None
        """
        try:
            if len(translations) != len(references):
                raise ValueError("翻译和参考文本数量必须相同")
            
            payload = {
                "translations": translations,
                "references": references
            }
            
            if sources:
                if len(sources) != len(translations):
                    raise ValueError("源文本数量必须与翻译数量相同")
                payload["sources"] = sources
            
            if mqm_scores:
                if len(mqm_scores) != len(translations):
                    raise ValueError("MQM评分数量必须与翻译数量相同")
                payload["mqm_scores"] = mqm_scores
            
            response = self._session.post(
                f"{self.base_url}/eval/batch",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                scores_data = result.get("scores", [])
                scores = []
                for score_data in scores_data:
                    scores.append(EvaluationScore(
                        bleu=score_data.get("bleu", 0.0),
                        comet=score_data.get("comet", 0.0),
                        bleurt=score_data.get("bleurt", 0.0),
                        bertscore_f1=score_data.get("bertscore_f1", 0.0),
                        chrf=score_data.get("chrf", 0.0),
                        mqm_adequacy=score_data.get("mqm_adequacy", 0.0),
                        mqm_fluency=score_data.get("mqm_fluency", 0.0),
                        mqm_terminology=score_data.get("mqm_terminology", 0.0),
                        mqm_overall=score_data.get("mqm_overall", 0.0),
                        final_score=score_data.get("final_score", 0.0),
                        model_info=score_data.get("model_info", {})
                    ))
                return scores
            else:
                error = result.get("error", "未知错误")
                print(f"[ERROR] 批量评估失败: {error}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] 评估API请求失败: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] 批量评估处理失败: {e}")
            return None


def create_eval_client_from_config(config_path: Optional[Path] = None) -> Optional[EvaluationAPIClient]:
    """
    从配置文件创建评估API客户端
    
    Args:
        config_path: 配置文件路径，默认为 config/evaluation.yaml
        
    Returns:
        EvaluationAPIClient: 评估API客户端，如果配置不存在返回None
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "evaluation.yaml"
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        api_config = config.get('api', {})
        
        if not api_config.get('enabled', False):
            return None
        
        base_url = api_config.get('base_url', 'http://localhost:5001')
        timeout = api_config.get('timeout', 300)
        api_key = api_config.get('api_key')
        
        # 如果配置了环境变量，优先使用环境变量
        if api_key and api_key.startswith('$'):
            env_key = api_key[1:]
            api_key = os.getenv(env_key)
        
        return EvaluationAPIClient(
            base_url=base_url,
            timeout=timeout,
            api_key=api_key
        )
    except Exception as e:
        print(f"[WARN] 读取评估API配置失败: {e}")
        return None

