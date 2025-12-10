"""
评估服务集成模块
提供统一的评估接口，支持本地评估和API评估两种模式
"""

from typing import Optional, Dict
from pathlib import Path
import os

# 尝试导入评估API客户端
try:
    from .eval_api_client import EvaluationAPIClient, EvaluationScore, create_eval_client_from_config
    HAS_API_CLIENT = True
except ImportError:
    HAS_API_CLIENT = False
    EvaluationAPIClient = None
    EvaluationScore = None
    create_eval_client_from_config = None

# 尝试导入本地评估器（如果可用）
try:
    import sys
    import importlib.util
    
    # 尝试从共享评估库导入
    current_file = Path(__file__).resolve()
    evaluator_lib = current_file.parent.parent.parent.parent / "translation_evaluator"
    if not evaluator_lib.exists():
        evaluator_lib = current_file.parent.parent.parent / "translation_evaluator"
    
    if evaluator_lib.exists():
        sys.path.insert(0, str(evaluator_lib))
    
    from translation_evaluator import UnifiedEvaluator, PaperGradeScore
    HAS_LOCAL_EVALUATOR = True
except ImportError:
    HAS_LOCAL_EVALUATOR = False
    UnifiedEvaluator = None
    PaperGradeScore = None


class EvaluationService:
    """评估服务（支持API和本地两种模式）"""
    
    def __init__(
        self,
        use_api: bool = True,
        api_base_url: Optional[str] = None,
        api_timeout: int = 300,
        api_key: Optional[str] = None
    ):
        """
        初始化评估服务
        
        Args:
            use_api: 是否使用API模式（True=API模式，False=本地模式）
            api_base_url: API服务器地址（如果为None，从配置文件读取）
            api_timeout: API请求超时时间
            api_key: API密钥（可选）
        """
        self.use_api = use_api
        self.api_client = None
        self.local_evaluator = None
        
        if use_api:
            if not HAS_API_CLIENT:
                raise ImportError("评估API客户端不可用，请安装 requests: pip install requests")
            
            # 从配置文件创建客户端，或使用提供的参数
            if api_base_url is None:
                self.api_client = create_eval_client_from_config()
                if self.api_client is None:
                    # 使用默认配置
                    self.api_client = EvaluationAPIClient(
                        base_url="http://localhost:5001",
                        timeout=api_timeout,
                        api_key=api_key
                    )
            else:
                self.api_client = EvaluationAPIClient(
                    base_url=api_base_url,
                    timeout=api_timeout,
                    api_key=api_key
                )
            
            # 检查服务是否可用
            if not self.api_client.health_check():
                print("[WARN] 评估API服务不可用，请确保服务已启动")
        else:
            if not HAS_LOCAL_EVALUATOR:
                raise ImportError("本地评估器不可用，请安装 translation_evaluator 库")
            
            # 使用本地评估器
            from src.utils.evaluator_env import setup_evaluator_environment
            evaluator_lib = Path(__file__).parent.parent.parent.parent / "translation_evaluator"
            if not evaluator_lib.exists():
                evaluator_lib = Path(__file__).parent.parent.parent / "translation_evaluator"
            
            setup_evaluator_environment(evaluator_lib)
            
            self.local_evaluator = UnifiedEvaluator(
                use_bleu=True,
                use_comet=True,
                use_bleurt=True,
                use_bertscore=True,
                use_mqm=True,
                use_chrf=True
            )
            self.local_evaluator.initialize()
    
    def evaluate(
        self,
        translation: str,
        reference: str,
        source: Optional[str] = None,
        mqm_score: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        评估翻译质量
        
        Args:
            translation: 翻译文本
            reference: 参考翻译
            source: 源文本（可选）
            mqm_score: MQM评分（可选）
            
        Returns:
            Dict: 评估结果，包含所有评分指标
        """
        if self.use_api:
            if self.api_client is None:
                return None
            
            score = self.api_client.evaluate(
                translation=translation,
                reference=reference,
                source=source,
                mqm_score=mqm_score
            )
            
            if score is None:
                return None
            
            return {
                "bleu": score.bleu,
                "comet": score.comet,
                "bleurt": score.bleurt,
                "bertscore_f1": score.bertscore_f1,
                "chrf": score.chrf,
                "mqm_adequacy": score.mqm_adequacy,
                "mqm_fluency": score.mqm_fluency,
                "mqm_terminology": score.mqm_terminology,
                "mqm_overall": score.mqm_overall,
                "final_score": score.final_score,
                "model_info": score.model_info
            }
        else:
            if self.local_evaluator is None:
                return None
            
            score = self.local_evaluator.score(
                source=source or "",
                translation=translation,
                reference=reference,
                mqm_score=mqm_score
            )
            
            return {
                "bleu": score.bleu,
                "comet": score.comet,
                "bleurt": score.bleurt,
                "bertscore_f1": score.bertscore_f1,
                "chrf": score.chrf,
                "mqm_adequacy": mqm_score.get("adequacy", 0.0) if mqm_score else 0.0,
                "mqm_fluency": mqm_score.get("fluency", 0.0) if mqm_score else 0.0,
                "mqm_terminology": mqm_score.get("terminology", 0.0) if mqm_score else 0.0,
                "mqm_overall": score.mqm_overall if hasattr(score, 'mqm_overall') else (mqm_score.get("overall", 0.0) if mqm_score else 0.0),
                "final_score": score.final_score,
                "model_info": {}
            }
    
    def is_available(self) -> bool:
        """
        检查评估服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        if self.use_api:
            return self.api_client is not None and self.api_client.health_check()
        else:
            return self.local_evaluator is not None


def create_evaluation_service(use_api: Optional[bool] = None) -> Optional[EvaluationService]:
    """
    从配置文件创建评估服务
    
    Args:
        use_api: 是否使用API模式（None=从配置文件读取）
        
    Returns:
        EvaluationService: 评估服务实例
    """
    from pathlib import Path
    import yaml
    
    config_path = Path(__file__).parent.parent.parent / "config" / "evaluation.yaml"
    
    if not config_path.exists():
        # 默认使用API模式
        if use_api is None:
            use_api = True
        return EvaluationService(use_api=use_api)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        api_config = config.get('api', {})
        
        # 如果未指定，从配置文件读取
        if use_api is None:
            use_api = api_config.get('enabled', False)
        
        if use_api:
            base_url = api_config.get('base_url', 'http://localhost:5001')
            timeout = api_config.get('timeout', 300)
            api_key = api_config.get('api_key')
            
            if api_key and api_key.startswith('$'):
                env_key = api_key[1:]
                api_key = os.getenv(env_key)
            
            return EvaluationService(
                use_api=True,
                api_base_url=base_url,
                api_timeout=timeout,
                api_key=api_key
            )
        else:
            return EvaluationService(use_api=False)
    except Exception as e:
        print(f"[WARN] 读取评估配置失败: {e}")
        # 默认使用API模式
        return EvaluationService(use_api=True)

