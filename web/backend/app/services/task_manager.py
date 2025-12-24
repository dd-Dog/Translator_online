"""
任务管理器
"""
import uuid
import asyncio
from typing import Dict, Optional
from datetime import datetime
from app.models.request import TranslateRequest
from app.models.response import TaskStatus, TranslationResult, QualityScore
from app.dependencies import get_or_create_pipeline
from app.utils.websocket_manager import ws_manager
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 使用loguru进行日志输出
try:
    from loguru import logger
except ImportError:
    # 如果没有loguru，使用print
    class SimpleLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def success(self, msg): print(f"[SUCCESS] {msg}")
        def warning(self, msg): print(f"[WARNING] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
        def debug(self, msg): print(f"[DEBUG] {msg}")
    logger = SimpleLogger()


class Task:
    """翻译任务"""
    
    def __init__(self, task_id: str, request: TranslateRequest):
        self.task_id = task_id
        self.request = request
        self.status = "pending"
        self.result: Optional[TranslationResult] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.current_stage = ""
        self.progress = 0
        self.history_saved = False  # 标记是否已保存到历史记录


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    def create_task(self, request: TranslateRequest) -> str:
        """创建任务"""
        task_id = str(uuid.uuid4())
        task = Task(task_id, request)
        self.tasks[task_id] = task
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    async def execute_task(self, task_id: str):
        """执行翻译任务"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.status = "processing"
        
        logger.info("=" * 80)
        logger.info(f"开始执行翻译任务 [Task ID: {task_id}]")
        logger.info(f"原文: {task.request.text[:100]}{'...' if len(task.request.text) > 100 else ''}")
        logger.info(f"源语言: {task.request.source_lang}, 目标语言: {task.request.target_lang}, 风格: {task.request.style}")
        logger.info("=" * 80)
        
        try:
            # 发送开始消息
            await ws_manager.send_to_all(
                task_id,
                "progress",
                {
                    "stage": "starting",
                    "progress": 0,
                    "message": "翻译任务开始..."
                }
            )
            
            # 获取Pipeline - 如果请求中提供了model_configs，使用它们创建Pipeline
            # 注意：每次任务都创建新的Pipeline实例，确保不同客户端的API_KEY不会混用
            logger.info("[步骤0] 初始化翻译Pipeline...")
            pipeline_configs = None
            if task.request.model_configs and len(task.request.model_configs) > 0:
                # 转换前端传入的配置格式
                # Pydantic会将ModelConfig对象转换为字典，但我们需要处理两种情况：
                # 1. 已经是字典格式
                # 2. 是ModelConfig对象（有dict()方法或可以直接访问属性）
                pipeline_configs = {}
                for stage, config in task.request.model_configs.items():
                    # 如果是ModelConfig对象，转换为字典
                    if hasattr(config, 'dict'):
                        config_dict = config.dict()
                    elif hasattr(config, 'model_dump'):  # Pydantic v2
                        config_dict = config.model_dump()
                    elif isinstance(config, dict):
                        config_dict = config
                    else:
                        # 尝试直接访问属性（Pydantic模型对象）
                        config_dict = {
                            'model_type': getattr(config, 'model_type', 'deepseek'),
                            'api_key': getattr(config, 'api_key', '')
                        }
                    
                    # 获取API_KEY（保留原始值，包括空字符串，用于强制使用用户配置）
                    api_key = str(config_dict.get('api_key', '')).strip()
                    model_type = config_dict.get('model_type', 'deepseek')
                    
                    # 记录配置信息
                    logger.info(f"[配置验证] 阶段 {stage}: model_type={model_type}, api_key长度={len(api_key)}, api_key前8位={api_key[:8] if len(api_key) >= 8 else 'N/A'}")
                    
                    # 如果API_KEY为空，抛出错误（不允许空值）
                    if not api_key:
                        raise ValueError(f"阶段 {stage} 的API_KEY不能为空")
                    
                    pipeline_configs[stage] = {
                        'model_type': model_type,
                        'api_key': api_key  # 使用用户提供的API_KEY，即使是错误的也要使用
                    }
                
                # 同时保存配置信息到pipeline_configs中，用于后续验证
                # 注意：这里保存的是用户传入的配置，用于后续对比验证
                
                # 详细记录Pipeline配置（用于确认配置生效）
                logger.info("=" * 80)
                logger.info(f"[Pipeline配置] 任务ID: {task_id}")
                logger.info(f"[Pipeline配置] 使用自定义模型配置，各阶段配置如下：")
                stage_names = {
                    'planner': '任务规划',
                    'translator_a': '主翻译',
                    'translator_b': '对照翻译',
                    'checker': '质量检查',
                    'stylist': '风格化',
                    'aggregator': '最终整合'
                }
                for stage, config in pipeline_configs.items():
                    model_type = config.get('model_type', '未知')
                    api_key_preview = config.get('api_key', '')[:8] + '...' if len(config.get('api_key', '')) > 8 else config.get('api_key', '')
                    logger.info(f"  [{stage_names.get(stage, stage)}] 模型类型: {model_type}, API_KEY: {api_key_preview}")
                logger.info("=" * 80)
                logger.info(f"[步骤0] 注意：每个任务使用独立的Pipeline实例，确保API_KEY隔离")
            else:
                logger.info("[步骤0] 使用默认模型配置（从yaml文件读取）")
                # 记录默认配置
                from app.dependencies import load_models_config
                config = load_models_config()
                workflow_config = config.get('workflow', {})
                logger.info("=" * 80)
                logger.info(f"[Pipeline配置] 任务ID: {task_id}")
                logger.info(f"[Pipeline配置] 使用默认模型配置（从yaml文件读取），各阶段配置如下：")
                for stage in ['planner', 'translator_a', 'translator_b', 'checker', 'stylist', 'aggregator']:
                    stage_config = workflow_config.get(stage, 'deepseek')
                    model_type = stage_config if isinstance(stage_config, str) else stage_config.get('model', 'deepseek')
                    logger.info(f"  [{stage}] 模型类型: {model_type}")
                logger.info("=" * 80)
            
            # 每次任务都创建新的Pipeline实例，确保不同客户端的API_KEY不会混用
            pipeline = get_or_create_pipeline(pipeline_configs)
            logger.success("[步骤0] Pipeline初始化完成")
            
            # 执行翻译 - 手动执行各阶段以获取进度
            stages = [
                ("planner", "任务规划", 0),
                ("translator_a", "主翻译", 20),
                ("translator_b", "对照翻译", 40),
                ("checker", "质量检查", 60),
                ("stylist", "风格化", 80),
                ("aggregator", "最终整合", 95)
            ]
            
            # 更新进度
            async def update_progress(stage: str, progress: int, message: str):
                task.current_stage = stage
                task.progress = progress
                # 发送进度消息
                await ws_manager.send_to_all(
                    task_id,
                    "progress",
                    {
                        "stage": stage,
                        "progress": progress,
                        "message": message
                    }
                )
                logger.info(f"[WebSocket] 发送进度消息: stage={stage}, progress={progress}, message={message}")
            
            # 执行翻译 - 使用Pipeline，但在各阶段前后发送进度
            # 由于Pipeline内部执行，我们需要在调用前后发送进度
            await update_progress("planner", 10, "开始任务规划...")
            
            # 直接调用Pipeline的translate方法，它会执行完整的6个阶段
            # 但为了获取进度，我们需要手动执行各阶段
            from src.agents.workflow import TaskPlan
            
            # 阶段1: 任务规划
            logger.info("-" * 80)
            logger.info("[步骤1] 开始任务规划 (Planner)...")
            logger.info(f"  输入文本长度: {len(task.request.text)} 字符")
            # 打印实际使用的模型信息
            if hasattr(pipeline, 'planner') and hasattr(pipeline.planner, 'model') and pipeline.planner.model:
                planner_model = pipeline.planner.model
                model_name = getattr(planner_model, 'model_name', '未知')
                api_key = getattr(planner_model, 'api_key', '')
                api_key_preview = api_key[:8] + '...' if len(api_key) > 8 else api_key
                base_url = getattr(planner_model, 'base_url', '默认')
                logger.info(f"  [实际调用模型] model_name: {model_name}, base_url: {base_url}, api_key: {api_key_preview}")
            task_plan = await pipeline.planner.plan(
                task.request.text,
                task.request.source_lang if task.request.source_lang != "auto" else None,
                task.request.target_lang
            )
            logger.success(f"[步骤1] 任务规划完成")
            logger.info(f"  检测到的源语言: {task_plan.source_lang}")
            logger.info(f"  目标语言: {task_plan.target_lang}")
            logger.info(f"  任务数量: {len(task_plan.tasks)} 个段落")
            logger.info("  任务详情:")
            for i, t in enumerate(task_plan.tasks):
                logger.info(f"    任务{i+1} [ID: {t.get('segment_id', 'N/A')}]:")
                logger.info(f"      类型: {t.get('type', 'unknown')}")
                logger.info(f"      文本: {t['text']}")
                if t.get('needs_double_translation'):
                    logger.info(f"      需要双重翻译: 是")
                if t.get('needs_multi_review'):
                    logger.info(f"      需要多重审核: 是")
            await update_progress("planner", 15, "任务规划完成")
            
            # 处理每个任务
            final_segments = []
            all_explainability_reports = []
            total_tasks = len(task_plan.tasks)
            # 收集所有阶段的详细信息
            all_stage_details = []
            
            logger.info(f"开始处理 {total_tasks} 个翻译段落...")
            await update_progress("planner", 20, f"开始处理 {total_tasks} 个段落...")
            
            # 保存阶段1（任务规划）的详细信息
            # 获取planner使用的模型信息
            planner_model_info = "planner"  # 默认值
            if pipeline_configs and 'planner' in pipeline_configs:
                planner_model_info = pipeline_configs['planner'].get('model_type', 'planner')
            elif hasattr(pipeline, 'planner') and hasattr(pipeline.planner, 'model') and pipeline.planner.model:
                planner_model_info = getattr(pipeline.planner.model, 'model_name', 'planner') if hasattr(pipeline.planner.model, 'model_name') else 'planner'
            
            logger.info(f"  Planner使用模型: {planner_model_info}")
            
            all_stage_details.append({
                "stage": "planner",
                "stage_name": "任务规划",
                "input": task.request.text,
                "output": {
                    "source_lang": task_plan.source_lang,
                    "target_lang": task_plan.target_lang,
                    "tasks_count": len(task_plan.tasks),
                    "tasks": [{"segment_id": t.get('segment_id'), "text": t.get('text', '')[:100]} for t in task_plan.tasks]
                },
                "model": planner_model_info
            })
            
            # 发送阶段1完成进度和结果（包含模型信息）
            await ws_manager.send_to_all(
                task_id,
                "stage_result",
                {
                    "stage": "planner",
                    "stage_name": "任务规划",
                    "translated_text": f"检测到源语言: {task_plan.source_lang}, 目标语言: {task_plan.target_lang}, 任务数量: {len(task_plan.tasks)}",
                    "model": planner_model_info,  # 添加模型信息
                    "progress": 15
                }
            )
            
            for idx, task_item in enumerate(task_plan.tasks):
                segment_id = task_item['segment_id']
                segment_text = task_item['text']
                progress_base = 15 + (idx * 70 / total_tasks)
                
                # 阶段2: 主翻译
                logger.info("-" * 80)
                logger.info(f"[步骤2] 开始主翻译 (Translator-A) [段落 {idx+1}/{total_tasks}]")
                logger.info(f"  段落ID: {segment_id}")
                logger.info(f"  原文: {segment_text}")
                # 打印实际使用的模型信息
                if hasattr(pipeline, 'translator_a') and hasattr(pipeline.translator_a, 'model') and pipeline.translator_a.model:
                    translator_a_model = pipeline.translator_a.model
                    model_name = getattr(translator_a_model, 'model_name', '未知')
                    api_key = getattr(translator_a_model, 'api_key', '')
                    api_key_preview = api_key[:8] + '...' if len(api_key) > 8 else api_key
                    base_url = getattr(translator_a_model, 'base_url', '默认')
                    logger.info(f"  [实际调用模型] model_name: {model_name}, base_url: {base_url}, api_key: {api_key_preview}")
                await update_progress("translator_a", int(progress_base + 5), f"执行主翻译（{idx+1}/{total_tasks}）...")
                draft_a = await pipeline.translator_a.translate(
                    segment_text,
                    task_plan.source_lang,
                    task_plan.target_lang,
                    segment_id
                )
                logger.success(f"[步骤2] 主翻译完成")
                model_name_a = draft_a.model_name if hasattr(draft_a, 'model_name') else '未知'
                logger.info(f"  使用模型: {model_name_a}")
                logger.info(f"  翻译结果（完整）:")
                if draft_a.translated_text:
                    logger.info(f"    {draft_a.translated_text}")
                else:
                    logger.error(f"    [错误] 翻译结果为空！")
                    # 检查是否有错误信息
                    if hasattr(draft_a, 'self_check_report') and draft_a.self_check_report:
                        if hasattr(draft_a.self_check_report, 'suggestions'):
                            for suggestion in draft_a.self_check_report.suggestions:
                                if 'balance' in suggestion.lower() or 'insufficient' in suggestion.lower() or '402' in suggestion:
                                    logger.error(f"    [API错误] 检测到API余额不足或配置问题")
                    logger.warning(f"    可能的原因:")
                    logger.warning(f"      1. API余额不足 - 请检查账户余额")
                    logger.warning(f"      2. API密钥配置错误 - 请检查.env文件中的API密钥")
                    logger.warning(f"      3. 网络连接问题 - 请检查网络连接")
                    logger.warning(f"      4. 模型服务暂时不可用 - 请稍后重试")
                if hasattr(draft_a, 'self_check_report') and draft_a.self_check_report:
                    logger.info(f"  自检报告:")
                    if hasattr(draft_a.self_check_report, 'uncertain_segments'):
                        logger.info(f"    不确定段落数: {len(draft_a.self_check_report.uncertain_segments)}")
                    if hasattr(draft_a.self_check_report, 'confidence_scores'):
                        logger.info(f"    置信度: {draft_a.self_check_report.confidence_scores}")
                
                # 保存阶段2的详细信息
                all_stage_details.append({
                    "stage": "translator_a",
                    "stage_name": "主翻译",
                    "segment_id": segment_id,
                    "input": segment_text,
                    "output": draft_a.translated_text or "",
                    "model": model_name_a,
                    "self_check": {
                        "uncertain_segments": len(draft_a.self_check_report.uncertain_segments) if hasattr(draft_a, 'self_check_report') and draft_a.self_check_report and hasattr(draft_a.self_check_report, 'uncertain_segments') else 0,
                        "confidence_scores": draft_a.self_check_report.confidence_scores if hasattr(draft_a, 'self_check_report') and draft_a.self_check_report and hasattr(draft_a.self_check_report, 'confidence_scores') else None
                    } if hasattr(draft_a, 'self_check_report') and draft_a.self_check_report else None
                })
                # 发送阶段2完成进度
                await update_progress("translator_a", int(progress_base + 10), f"主翻译完成（{idx+1}/{total_tasks}）")
                # 发送阶段2结果
                await ws_manager.send_to_all(
                    task_id,
                    "stage_result",
                    {
                        "stage": "translator_a",
                        "stage_name": "主翻译",
                        "translated_text": draft_a.translated_text,
                        "model": model_name_a,  # 添加模型信息
                        "progress": int(progress_base + 10)
                    }
                )
                
                # 阶段3: 对照翻译
                logger.info("-" * 80)
                logger.info(f"[步骤3] 开始对照翻译 (Translator-B) [段落 {idx+1}/{total_tasks}]")
                # 打印实际使用的模型信息
                if hasattr(pipeline, 'translator_b') and hasattr(pipeline.translator_b, 'model') and pipeline.translator_b.model:
                    translator_b_model = pipeline.translator_b.model
                    model_name = getattr(translator_b_model, 'model_name', '未知')
                    api_key = getattr(translator_b_model, 'api_key', '')
                    api_key_preview = api_key[:8] + '...' if len(api_key) > 8 else api_key
                    base_url = getattr(translator_b_model, 'base_url', '默认')
                    logger.info(f"  [实际调用模型] model_name: {model_name}, base_url: {base_url}, api_key: {api_key_preview}")
                await update_progress("translator_b", int(progress_base + 15), f"执行对照翻译（{idx+1}/{total_tasks}）...")
                draft_b = await pipeline.translator_b.translate(
                    segment_text,
                    task_plan.source_lang,
                    task_plan.target_lang,
                    segment_id
                )
                logger.success(f"[步骤3] 对照翻译完成")
                model_name_b = draft_b.model_name if hasattr(draft_b, 'model_name') else '未知'
                logger.info(f"  使用模型: {model_name_b}")
                logger.info(f"  翻译结果（完整）:")
                logger.info(f"    {draft_b.translated_text}")
                if hasattr(draft_b, 'self_check_report') and draft_b.self_check_report:
                    logger.info(f"  自检报告:")
                    if hasattr(draft_b.self_check_report, 'uncertain_segments'):
                        logger.info(f"    不确定段落数: {len(draft_b.self_check_report.uncertain_segments)}")
                    if hasattr(draft_b.self_check_report, 'confidence_scores'):
                        logger.info(f"    置信度: {draft_b.self_check_report.confidence_scores}")
                
                # 保存阶段3的详细信息
                all_stage_details.append({
                    "stage": "translator_b",
                    "stage_name": "对照翻译",
                    "segment_id": segment_id,
                    "input": segment_text,
                    "output": draft_b.translated_text or "",
                    "model": model_name_b,
                    "self_check": {
                        "uncertain_segments": len(draft_b.self_check_report.uncertain_segments) if hasattr(draft_b, 'self_check_report') and draft_b.self_check_report and hasattr(draft_b.self_check_report, 'uncertain_segments') else 0,
                        "confidence_scores": draft_b.self_check_report.confidence_scores if hasattr(draft_b, 'self_check_report') and draft_b.self_check_report and hasattr(draft_b.self_check_report, 'confidence_scores') else None
                    } if hasattr(draft_b, 'self_check_report') and draft_b.self_check_report else None
                })
                # 发送阶段3完成进度
                await update_progress("translator_b", int(progress_base + 25), f"对照翻译完成（{idx+1}/{total_tasks}）")
                # 发送阶段3结果
                await ws_manager.send_to_all(
                    task_id,
                    "stage_result",
                    {
                        "stage": "translator_b",
                        "stage_name": "对照翻译",
                        "translated_text": draft_b.translated_text,
                        "model": model_name_b,  # 添加模型信息
                        "progress": int(progress_base + 25)
                    }
                )
                
                # 阶段4: 一致性检查
                logger.info("-" * 80)
                logger.info(f"[步骤4] 开始质量检查 (Checker) [段落 {idx+1}/{total_tasks}]")
                logger.info(f"  对比两个翻译版本...")
                # 打印实际使用的模型信息
                if hasattr(pipeline, 'checker') and hasattr(pipeline.checker, 'model') and pipeline.checker.model:
                    checker_model = pipeline.checker.model
                    model_name = getattr(checker_model, 'model_name', '未知')
                    api_key = getattr(checker_model, 'api_key', '')
                    api_key_preview = api_key[:8] + '...' if len(api_key) > 8 else api_key
                    base_url = getattr(checker_model, 'base_url', '默认')
                    logger.info(f"  [实际调用模型] model_name: {model_name}, base_url: {base_url}, api_key: {api_key_preview}")
                await update_progress("checker", int(progress_base + 30), f"执行质量检查（{idx+1}/{total_tasks}）...")
                checker_report = await pipeline.checker.check(
                    segment_text,
                    draft_a,
                    draft_b,
                    segment_id
                )
                logger.success(f"[步骤4] 质量检查完成")
                logger.info(f"  检查报告详情:")
                if hasattr(checker_report, 'consistent_segments'):
                    logger.info(f"    一致段落数: {len(checker_report.consistent_segments)}")
                    if checker_report.consistent_segments:
                        logger.info(f"    一致段落ID: {checker_report.consistent_segments}")
                if hasattr(checker_report, 'conflicting_segments'):
                    logger.info(f"    冲突段落数: {len(checker_report.conflicting_segments)}")
                    for conflict in checker_report.conflicting_segments[:3]:  # 只打印前3个冲突
                        logger.info(f"      冲突段落 {conflict.get('segment_id', 'N/A')}: {conflict.get('issue', 'N/A')}")
                if hasattr(checker_report, 'omissions'):
                    logger.info(f"    遗漏数: {len(checker_report.omissions)}")
                if hasattr(checker_report, 'misinterpretations'):
                    logger.info(f"    误解数: {len(checker_report.misinterpretations)}")
                if hasattr(checker_report, 'quality_scores') and segment_id in checker_report.quality_scores:
                    qs = checker_report.quality_scores[segment_id]
                    logger.info(f"  质量评分:")
                    logger.info(f"    充分性 (Adequacy): {qs.adequacy:.3f}")
                    logger.info(f"    流畅性 (Fluency): {qs.fluency:.3f}")
                    logger.info(f"    术语准确性 (Terminology): {qs.terminology:.3f}")
                    logger.info(f"    总体评分 (Overall): {qs.overall:.3f}")
                # 发送阶段4结果（检查后的最佳翻译）
                import inspect
                if hasattr(pipeline, '_select_best_draft'):
                    best_draft = pipeline._select_best_draft(draft_a, draft_b, checker_report)
                else:
                    best_draft = draft_a
                logger.info(f"  选择的最佳翻译（完整）:")
                logger.info(f"    {best_draft.translated_text}")
                
                # 从pipeline.checker.model获取模型名称
                checker_model_name = '未知'
                if hasattr(pipeline, 'checker') and hasattr(pipeline.checker, 'model') and pipeline.checker.model:
                    checker_model_name = getattr(pipeline.checker.model, 'model_name', '未知')
                
                # 保存阶段4的详细信息
                checker_details = {
                    "stage": "checker",
                    "stage_name": "质量检查",
                    "segment_id": segment_id,
                    "input": {
                        "source_text": segment_text,
                        "draft_a": draft_a.translated_text or "",
                        "draft_b": draft_b.translated_text or ""
                    },
                    "output": best_draft.translated_text or "",
                    "model": checker_model_name,
                    "report": {
                        "consistent_segments": checker_report.consistent_segments if hasattr(checker_report, 'consistent_segments') else [],
                        "conflicting_segments_count": len(checker_report.conflicting_segments) if hasattr(checker_report, 'conflicting_segments') else 0,
                        "omissions_count": len(checker_report.omissions) if hasattr(checker_report, 'omissions') else 0,
                        "misinterpretations_count": len(checker_report.misinterpretations) if hasattr(checker_report, 'misinterpretations') else 0
                    }
                }
                if hasattr(checker_report, 'quality_scores') and segment_id in checker_report.quality_scores:
                    qs = checker_report.quality_scores[segment_id]
                    checker_details["report"]["quality_scores"] = {
                        "adequacy": qs.adequacy,
                        "fluency": qs.fluency,
                        "terminology": qs.terminology,
                        "overall": qs.overall
                    }
                all_stage_details.append(checker_details)
                
                # 发送阶段4完成进度
                await update_progress("checker", int(progress_base + 40), f"质量检查完成（{idx+1}/{total_tasks}）")
                await ws_manager.send_to_all(
                    task_id,
                    "stage_result",
                    {
                        "stage": "checker",
                        "stage_name": "质量检查",
                        "translated_text": best_draft.translated_text,
                        "model": checker_model_name,  # 添加模型信息
                        "progress": int(progress_base + 40)
                    }
                )
                
                # 阶段5: 风格化
                logger.info("-" * 80)
                logger.info(f"[步骤5] 开始风格化 (Stylist) [段落 {idx+1}/{total_tasks}]")
                logger.info(f"  目标风格: {task.request.style}")
                # 打印实际使用的模型信息
                if hasattr(pipeline, 'stylist') and hasattr(pipeline.stylist, 'model') and pipeline.stylist.model:
                    stylist_model = pipeline.stylist.model
                    model_name = getattr(stylist_model, 'model_name', '未知')
                    api_key = getattr(stylist_model, 'api_key', '')
                    api_key_preview = api_key[:8] + '...' if len(api_key) > 8 else api_key
                    base_url = getattr(stylist_model, 'base_url', '默认')
                    logger.info(f"  [实际调用模型] model_name: {model_name}, base_url: {base_url}, api_key: {api_key_preview}")
                await update_progress("stylist", int(progress_base + 50), f"执行风格化（{idx+1}/{total_tasks}）...")
                stylist_result = await pipeline.stylist.style(
                    best_draft.translated_text,
                    segment_text
                )
                logger.success(f"[步骤5] 风格化完成")
                logger.info(f"  风格化结果（完整）:")
                logger.info(f"    {stylist_result.styled_text}")
                if hasattr(stylist_result, 'terminology_changes') and stylist_result.terminology_changes:
                    logger.info(f"  术语变更详情:")
                    for change in stylist_result.terminology_changes:
                        logger.info(f"    {change.get('original', 'N/A')} -> {change.get('unified', 'N/A')} (原因: {change.get('reason', 'N/A')})")
                if hasattr(stylist_result, 'style_changes') and stylist_result.style_changes:
                    logger.info(f"  风格变更详情:")
                    for change in stylist_result.style_changes[:5]:  # 只打印前5个变更
                        logger.info(f"    段落 {change.get('segment_id', 'N/A')}: {change.get('reason', 'N/A')}")
                        logger.info(f"      原文: {change.get('original', 'N/A')[:50]}...")
                        logger.info(f"      修改后: {change.get('modified', 'N/A')[:50]}...")
                    if len(stylist_result.style_changes) > 5:
                        logger.info(f"    ... 还有 {len(stylist_result.style_changes) - 5} 个风格变更")
                
                # 保存阶段5的详细信息
                # 从pipeline.stylist.model获取模型名称
                stylist_model = '未知'
                if hasattr(pipeline, 'stylist') and hasattr(pipeline.stylist, 'model') and pipeline.stylist.model:
                    stylist_model = getattr(pipeline.stylist.model, 'model_name', '未知')
                all_stage_details.append({
                    "stage": "stylist",
                    "stage_name": "风格化",
                    "segment_id": segment_id,
                    "input": {
                        "text": best_draft.translated_text or "",
                        "style": task.request.style
                    },
                    "output": stylist_result.styled_text or "",
                    "model": stylist_model,
                    "changes": {
                        "terminology_changes": stylist_result.terminology_changes if hasattr(stylist_result, 'terminology_changes') else [],
                        "style_changes_count": len(stylist_result.style_changes) if hasattr(stylist_result, 'style_changes') else 0
                    }
                })
                # 发送阶段5完成进度
                await update_progress("stylist", int(progress_base + 60), f"风格化完成（{idx+1}/{total_tasks}）")
                # 发送阶段5结果
                await ws_manager.send_to_all(
                    task_id,
                    "stage_result",
                    {
                        "stage": "stylist",
                        "stage_name": "风格化",
                        "translated_text": stylist_result.styled_text,
                        "model": stylist_model,  # 添加模型信息
                        "progress": int(progress_base + 60)
                    }
                )
                
                # 阶段6: 最终整合
                logger.info("-" * 80)
                logger.info(f"[步骤6] 开始最终整合 (Aggregator) [段落 {idx+1}/{total_tasks}]")
                # 打印实际使用的模型信息
                if hasattr(pipeline, 'aggregator') and hasattr(pipeline.aggregator, 'model') and pipeline.aggregator.model:
                    aggregator_model = pipeline.aggregator.model
                    model_name = getattr(aggregator_model, 'model_name', '未知')
                    api_key = getattr(aggregator_model, 'api_key', '')
                    api_key_preview = api_key[:8] + '...' if len(api_key) > 8 else api_key
                    base_url = getattr(aggregator_model, 'base_url', '默认')
                    logger.info(f"  [实际调用模型] model_name: {model_name}, base_url: {base_url}, api_key: {api_key_preview}")
                await update_progress("aggregator", int(progress_base + 65), f"执行最终整合（{idx+1}/{total_tasks}）...")
                final_result = await pipeline.aggregator.aggregate(
                    segment_text,
                    [draft_a, draft_b],
                    checker_report,
                    stylist_result,
                    segment_id
                )
                logger.success(f"[步骤6] 最终整合完成")
                logger.info(f"  最终翻译结果（完整）:")
                logger.info(f"    {final_result.translated_text}")
                if hasattr(final_result, 'explainability_report') and final_result.explainability_report:
                    logger.info(f"  可解释性报告:")
                    if hasattr(final_result.explainability_report, 'modifications'):
                        logger.info(f"    修改记录数: {len(final_result.explainability_report.modifications)}")
                        for mod in final_result.explainability_report.modifications[:5]:  # 只打印前5个修改
                            logger.info(f"      修改 [{mod.get('stage', 'N/A')}] 段落 {mod.get('segment_id', 'N/A')}:")
                            logger.info(f"        原因: {mod.get('reason', 'N/A')}")
                            logger.info(f"        原文: {mod.get('original', 'N/A')[:80]}...")
                            logger.info(f"        修改后: {mod.get('modified', 'N/A')[:80]}...")
                        if len(final_result.explainability_report.modifications) > 5:
                            logger.info(f"      ... 还有 {len(final_result.explainability_report.modifications) - 5} 个修改记录")
                    if hasattr(final_result.explainability_report, 'quality_improvements'):
                        logger.info(f"    质量改进:")
                        for metric, improvement in list(final_result.explainability_report.quality_improvements.items())[:5]:
                            logger.info(f"      {metric}: {improvement}")
                    if hasattr(final_result.explainability_report, 'final_quality_score') and final_result.explainability_report.final_quality_score:
                        qs = final_result.explainability_report.final_quality_score
                        logger.info(f"    最终质量评分:")
                        logger.info(f"      充分性: {qs.adequacy:.3f}, 流畅性: {qs.fluency:.3f}, 术语: {qs.terminology:.3f}, 总体: {qs.overall:.3f}")
                
                # 保存阶段6的详细信息
                # 从pipeline.aggregator.model获取模型名称
                aggregator_model = '未知'
                if hasattr(pipeline, 'aggregator') and hasattr(pipeline.aggregator, 'model') and pipeline.aggregator.model:
                    aggregator_model = getattr(pipeline.aggregator.model, 'model_name', '未知')
                all_stage_details.append({
                    "stage": "aggregator",
                    "stage_name": "最终整合",
                    "segment_id": segment_id,
                    "input": {
                        "source_text": segment_text,
                        "draft_a": draft_a.translated_text or "",
                        "draft_b": draft_b.translated_text or "",
                        "stylist_result": stylist_result.styled_text or ""
                    },
                    "output": final_result.translated_text or "",
                    "model": aggregator_model
                })
                # 发送阶段6完成进度
                await update_progress("aggregator", int(progress_base + 80), f"最终整合完成（{idx+1}/{total_tasks}）")
                # 发送阶段6结果
                await ws_manager.send_to_all(
                    task_id,
                    "stage_result",
                    {
                        "stage": "aggregator",
                        "stage_name": "最终整合",
                        "translated_text": final_result.translated_text,
                        "model": aggregator_model,  # 添加模型信息
                        "progress": int(progress_base + 80)
                    }
                )
                
                final_segments.append({
                    'segment_id': segment_id,
                    'text': final_result.translated_text
                })
                if final_result.explainability_report:
                    all_explainability_reports.append(final_result.explainability_report)
            
            # 合并所有段落
            logger.info("-" * 80)
            logger.info("[最终处理] 合并所有段落...")
            translated_text = " ".join([seg['text'] for seg in final_segments])
            logger.info(f"  合并后总长度: {len(translated_text)} 字符")
            logger.info(f"  段落数量: {len(final_segments)}")
            
            # 构建最终结果
            from src.agents.workflow import FinalTranslation, ExplainabilityReport
            
            # 合并所有可解释性报告
            all_modifications = []
            all_quality_improvements = {}
            final_quality_score = None
            
            for report in all_explainability_reports:
                if report and hasattr(report, 'modifications') and report.modifications:
                    all_modifications.extend(report.modifications)
                if report and hasattr(report, 'quality_improvements') and report.quality_improvements:
                    all_quality_improvements.update(report.quality_improvements)
                if report and hasattr(report, 'final_quality_score') and report.final_quality_score:
                    final_quality_score = report.final_quality_score
            
            explainability_report = ExplainabilityReport(
                modifications=all_modifications,
                quality_improvements=all_quality_improvements,
                final_quality_score=final_quality_score
            )
            
            result = FinalTranslation(
                translated_text=translated_text,
                explainability_report=explainability_report,
                source_lang=task_plan.source_lang,
                target_lang=task_plan.target_lang,
                processing_stages=["planner", "translator_a", "translator_b", "checker", "stylist", "aggregator"]
            )
            
            # 构建响应（不包含质量评分）
            task.result = TranslationResult(
                translated_text=result.translated_text,
                source_lang=result.source_lang,
                target_lang=result.target_lang,
                style=task.request.style,
                quality_score=None,  # 不再返回质量评分
                processing_stages=all_stage_details,  # 保存详细的阶段信息
                explainability_report={
                    "modifications": [
                        {
                            "stage": getattr(m, 'stage', '') if hasattr(m, 'stage') else m.get("stage", ""),
                            "segment_id": getattr(m, 'segment_id', '') if hasattr(m, 'segment_id') else m.get("segment_id", ""),
                            "original": getattr(m, 'original', '') if hasattr(m, 'original') else m.get("original", ""),
                            "modified": getattr(m, 'modified', '') if hasattr(m, 'modified') else m.get("modified", ""),
                            "reason": getattr(m, 'reason', '') if hasattr(m, 'reason') else m.get("reason", "")
                        }
                        for m in (result.explainability_report.modifications if result.explainability_report and hasattr(result.explainability_report, 'modifications') else [])
                    ],
                    "quality_improvements": result.explainability_report.quality_improvements if result.explainability_report and hasattr(result.explainability_report, 'quality_improvements') else {},
                }
            )
            
            task.status = "completed"
            task.completed_at = datetime.now()
            task.progress = 100
            
            logger.info("=" * 80)
            logger.success(f"翻译任务完成 [Task ID: {task_id}]")
            logger.info(f"最终翻译结果（完整）:")
            logger.info(f"  {translated_text}")
            logger.info(f"处理统计:")
            logger.info(f"  总段落数: {len(final_segments)}")
            logger.info(f"  处理时间: {(task.completed_at - task.created_at).total_seconds():.2f} 秒")
            logger.info(f"  平均每段落: {(task.completed_at - task.created_at).total_seconds() / len(final_segments) if final_segments else 0:.2f} 秒")
            logger.info("=" * 80)
            
            # 发送完成消息
            await ws_manager.send_to_all(
                task_id,
                "completed",
                {
                    "message": "翻译完成",
                    "result": task.result.dict()
                }
            )
            
            # 保存到历史记录（只在任务完成时保存一次）
            if not task.history_saved:
                try:
                    from app.services.history_service import history_service
                    await history_service.save(
                        task_id=task_id,
                        source_text=task.request.text,
                        translated_text=translated_text,
                        source_lang=result.source_lang,
                        target_lang=result.target_lang,
                        style=task.request.style,
                        quality_score=None,
                        processing_stages=all_stage_details,
                        explainability_report={
                            "modifications": [
                                {
                                    "stage": getattr(m, 'stage', '') if hasattr(m, 'stage') else m.get("stage", ""),
                                    "segment_id": getattr(m, 'segment_id', '') if hasattr(m, 'segment_id') else m.get("segment_id", ""),
                                    "original": getattr(m, 'original', '') if hasattr(m, 'original') else m.get("original", ""),
                                    "modified": getattr(m, 'modified', '') if hasattr(m, 'modified') else m.get("modified", ""),
                                    "reason": getattr(m, 'reason', '') if hasattr(m, 'reason') else m.get("reason", "")
                                }
                                for m in (result.explainability_report.modifications if result.explainability_report and hasattr(result.explainability_report, 'modifications') else [])
                            ],
                            "quality_improvements": result.explainability_report.quality_improvements if result.explainability_report and hasattr(result.explainability_report, 'quality_improvements') else {},
                        }
                    )
                    task.history_saved = True
                    logger.info(f"历史记录已保存 [Task ID: {task_id}]")
                except Exception as e:
                    logger.error(f"保存历史记录失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            
            logger.error("=" * 80)
            logger.error(f"翻译任务失败 [Task ID: {task_id}]")
            logger.error(f"错误信息: {str(e)}")
            
            # 检查是否是API相关错误
            error_str = str(e)
            user_friendly_message = str(e)
            if '402' in error_str or 'Insufficient Balance' in error_str or '余额不足' in error_str:
                user_friendly_message = "API余额不足，请检查账户余额并充值后重试"
                logger.error("⚠️  检测到API余额不足错误")
            elif '401' in error_str or 'Unauthorized' in error_str or 'Invalid API key' in error_str:
                user_friendly_message = "API密钥无效，请检查API密钥配置"
                logger.error("⚠️  检测到API密钥错误")
            elif '429' in error_str or 'Rate limit' in error_str:
                user_friendly_message = "请求频率过高，请稍后重试"
                logger.error("⚠️  检测到频率限制错误")
            
            import traceback
            logger.error(f"错误堆栈:\n{traceback.format_exc()}")
            logger.error("=" * 80)
            
            # 发送错误消息
            await ws_manager.send_to_all(
                task_id,
                "error",
                {
                    "message": f"翻译失败: {user_friendly_message}",
                    "error": str(e)
                }
            )
        
        finally:
            # 清理运行中的任务
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    async def start_task(self, task_id: str):
        """启动任务（异步执行）"""
        if task_id in self.running_tasks:
            return  # 任务已在运行
        
        task_coro = self.execute_task(task_id)
        self.running_tasks[task_id] = asyncio.create_task(task_coro)
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return TaskStatus(
            task_id=task.task_id,
            status=task.status,
            message=task.current_stage or "等待中",
            created_at=task.created_at,
            completed_at=task.completed_at
        )


# 全局任务管理器实例
task_manager = TaskManager()

