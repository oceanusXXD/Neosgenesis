#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语义分析器 - 基于LLM的智能文本分析
Semantic Analyzer - LLM-based intelligent text analysis

核心职责：
1. 替换硬编码关键词判断，使用LLM进行语义理解
2. 支持多任务并行分析（意图识别、情感分析、复杂度评估等）
3. 返回结构化的JSON分析结果
4. 提供可扩展的分析任务框架

设计理念：
- 智能而非死板：理解同义词、上下文和复杂句式
- 可配置任务：支持自定义分析任务和输出格式
- 高效可靠：内置缓存、错误处理和降级机制
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class AnalysisTaskType(Enum):
    """分析任务类型枚举"""
    INTENT_DETECTION = "intent_detection"           # 意图识别
    SENTIMENT_ANALYSIS = "sentiment_analysis"       # 情感分析
    COMPLEXITY_ASSESSMENT = "complexity_assessment" # 复杂度评估
    DOMAIN_CLASSIFICATION = "domain_classification" # 领域分类
    URGENCY_EVALUATION = "urgency_evaluation"       # 紧急程度评估
    KEYWORD_EXTRACTION = "keyword_extraction"       # 关键词提取
    TOPIC_MODELING = "topic_modeling"               # 主题建模
    LANGUAGE_DETECTION = "language_detection"       # 语言检测
    CUSTOM_ANALYSIS = "custom_analysis"             # 自定义分析

@dataclass
class AnalysisTask:
    """单个分析任务定义"""
    task_type: AnalysisTaskType
    description: str
    expected_output_format: Dict[str, Any]
    prompt_template: Optional[str] = None
    confidence_threshold: float = 0.7
    
@dataclass 
class AnalysisResult:
    """单个分析结果"""
    task_type: AnalysisTaskType
    result: Dict[str, Any]
    confidence: float
    processing_time: float
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class SemanticAnalysisResponse:
    """完整的语义分析响应"""
    input_text: str
    analysis_results: Dict[str, AnalysisResult]
    total_processing_time: float
    overall_success: bool
    cache_hit: bool = False
    llm_provider: Optional[str] = None
    
class SemanticAnalyzer:
    """语义分析器 - 基于LLM的智能文本分析引擎"""
    
    def __init__(self, llm_manager=None, config: Optional[Dict] = None):
        """
        初始化语义分析器
        
        Args:
            llm_manager: LLM管理器实例，如果为None则自动创建
            config: 配置字典，包含分析参数和LLM设置
        """
        self.llm_manager = llm_manager
        self.config = config or self._get_default_config()
        
        # 分析结果缓存
        self.analysis_cache = {}
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 5分钟缓存
        
        # 统计信息
        self.stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'total_processing_time': 0.0
        }
        
        # 预定义分析任务模板
        self.builtin_tasks = self._initialize_builtin_tasks()
        
        logger.info("🔍 SemanticAnalyzer 已初始化")
        
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'cache_ttl': 300,  # 缓存时间
            'max_retries': 3,  # 最大重试次数
            'timeout': 30,     # 请求超时时间
            'batch_size': 5,   # 批处理大小
            'enable_fallback': True,  # 启用降级机制
            'confidence_threshold': 0.7,  # 默认置信度阈值
            'model_name': 'deepseek-chat',  # 默认模型
            'temperature': 0.1,  # 低温度保证结果稳定性
        }
        
    def _initialize_builtin_tasks(self) -> Dict[str, AnalysisTask]:
        """初始化内置分析任务"""
        tasks = {}
        
        # 意图识别任务
        tasks['intent_detection'] = AnalysisTask(
            task_type=AnalysisTaskType.INTENT_DETECTION,
            description="识别用户输入的意图和目的",
            expected_output_format={
                "primary_intent": "string",  # 主要意图
                "secondary_intents": ["string"],  # 次要意图
                "confidence": "float",  # 置信度
                "intent_category": "string",  # 意图类别
                "action_required": "boolean"  # 是否需要行动
            },
            prompt_template="""请分析以下文本的意图：

文本: "{text}"

请识别用户的意图并返回JSON格式结果：
{{
    "primary_intent": "主要意图（如：信息查询、问题解决、任务执行等）",
    "secondary_intents": ["次要意图列表"],
    "confidence": 0.0-1.0之间的置信度分数,
    "intent_category": "意图类别（如：question, request, command, greeting等）",
    "action_required": true/false 是否需要具体行动
}}

请仅返回JSON，不要其他内容。"""
        )
        
        # 情感分析任务
        tasks['sentiment_analysis'] = AnalysisTask(
            task_type=AnalysisTaskType.SENTIMENT_ANALYSIS,
            description="分析文本的情感倾向和情绪状态",
            expected_output_format={
                "overall_sentiment": "string",  # 总体情感
                "sentiment_score": "float",     # 情感分数
                "emotions": {"emotion": "float"},  # 具体情绪
                "emotional_intensity": "string"   # 情感强度
            },
            prompt_template="""请分析以下文本的情感和情绪：

文本: "{text}"

请返回JSON格式的情感分析结果：
{{
    "overall_sentiment": "positive/negative/neutral",
    "sentiment_score": -1.0到1.0之间的分数（-1最负面，1最正面），
    "emotions": {{
        "joy": 0.0-1.0,
        "anger": 0.0-1.0,
        "fear": 0.0-1.0,
        "sadness": 0.0-1.0,
        "surprise": 0.0-1.0,
        "trust": 0.0-1.0
    }},
    "emotional_intensity": "low/medium/high"
}}

请仅返回JSON，不要其他内容。"""
        )
        
        # 复杂度评估任务
        tasks['complexity_assessment'] = AnalysisTask(
            task_type=AnalysisTaskType.COMPLEXITY_ASSESSMENT,
            description="评估任务或问题的复杂程度",
            expected_output_format={
                "complexity_level": "string",      # 复杂度等级
                "complexity_score": "float",       # 复杂度分数
                "complexity_factors": ["string"],  # 复杂度因素
                "estimated_effort": "string",      # 预估工作量
                "requires_expertise": "boolean"    # 是否需要专业知识
            },
            prompt_template="""请评估以下任务或问题的复杂程度：

文本: "{text}"

请返回JSON格式的复杂度评估结果：
{{
    "complexity_level": "low/medium/high/expert",
    "complexity_score": 0.0-1.0之间的复杂度分数,
    "complexity_factors": ["导致复杂的具体因素列表"],
    "estimated_effort": "minimal/moderate/substantial/extensive",
    "requires_expertise": true/false
}}

评估标准：
- Low: 简单直接的任务，几分钟内可完成
- Medium: 需要一些思考和步骤的任务
- High: 复杂的多步骤任务，需要深入分析
- Expert: 需要专业知识和大量时间的任务

请仅返回JSON，不要其他内容。"""
        )
        
        # 领域分类任务
        tasks['domain_classification'] = AnalysisTask(
            task_type=AnalysisTaskType.DOMAIN_CLASSIFICATION,
            description="识别文本所属的专业领域或主题域",
            expected_output_format={
                "primary_domain": "string",        # 主要领域
                "secondary_domains": ["string"],   # 次要领域  
                "domain_confidence": "float",      # 领域置信度
                "is_interdisciplinary": "boolean", # 是否跨领域
                "technical_level": "string"        # 技术水平
            },
            prompt_template="""请识别以下文本所属的专业领域：

文本: "{text}"

请返回JSON格式的领域分类结果：
{{
    "primary_domain": "主要专业领域",
    "secondary_domains": ["相关的次要领域"],
    "domain_confidence": 0.0-1.0之间的置信度,
    "is_interdisciplinary": true/false,
    "technical_level": "basic/intermediate/advanced/expert"
}}

领域包括但不限于：
技术（programming, ai, database, system），商业（marketing, finance, strategy），
学术（research, theory, analysis），生活（health, travel, education），
创意（design, art, writing）等

请仅返回JSON，不要其他内容。"""
        )
        
        # 紧急程度评估任务
        tasks['urgency_evaluation'] = AnalysisTask(
            task_type=AnalysisTaskType.URGENCY_EVALUATION,
            description="评估任务的紧急程度和优先级",
            expected_output_format={
                "urgency_level": "string",         # 紧急程度
                "urgency_score": "float",          # 紧急度分数
                "time_sensitivity": "string",      # 时间敏感度
                "consequences": "string",          # 延迟后果
                "priority_rank": "integer"         # 优先级排名
            },
            prompt_template="""请评估以下任务的紧急程度：

文本: "{text}"

请返回JSON格式的紧急程度评估：
{{
    "urgency_level": "low/medium/high/critical",
    "urgency_score": 0.0-1.0之间的紧急度分数,
    "time_sensitivity": "flexible/moderate/strict/immediate",
    "consequences": "延迟处理的后果描述",
    "priority_rank": 1-10之间的优先级排名（10最高）
}}

评估标准：
- Low: 可以稍后处理，无明确时间限制
- Medium: 建议及时处理，有一定时间要求
- High: 需要尽快处理，有明确期限
- Critical: 需要立即处理，延迟会有严重后果

请仅返回JSON，不要其他内容。"""
        )
        
        return tasks
    
    def analyze(self, 
                text: str, 
                tasks: Union[List[str], List[AnalysisTask], str],
                **kwargs) -> SemanticAnalysisResponse:
        """
        执行语义分析
        
        Args:
            text: 要分析的文本
            tasks: 分析任务列表，可以是任务名称字符串列表、AnalysisTask对象列表或单个任务名
            **kwargs: 额外的分析参数
            
        Returns:
            SemanticAnalysisResponse: 分析结果
        """
        start_time = time.time()
        self.stats['total_analyses'] += 1
        
        try:
            # 统一任务格式
            task_list = self._prepare_tasks(tasks)
            
            # 检查缓存
            cache_key = self._generate_cache_key(text, task_list)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.stats['cache_hits'] += 1
                logger.debug(f"🎯 缓存命中: {cache_key}")
                return cached_result
                
            # 执行分析
            results = {}
            overall_success = True
            llm_provider = None
            
            for task in task_list:
                try:
                    result = self._execute_single_task(text, task, **kwargs)
                    results[task.task_type.value] = result
                    
                    if not result.success:
                        overall_success = False
                        
                    # 记录使用的LLM提供商
                    if llm_provider is None and hasattr(self.llm_manager, 'last_used_provider'):
                        llm_provider = getattr(self.llm_manager, 'last_used_provider', None)
                        
                except Exception as e:
                    logger.error(f"❌ 任务执行失败 {task.task_type.value}: {e}")
                    results[task.task_type.value] = AnalysisResult(
                        task_type=task.task_type,
                        result={},
                        confidence=0.0,
                        processing_time=0.0,
                        success=False,
                        error_message=str(e)
                    )
                    overall_success = False
            
            # 创建响应对象
            total_time = time.time() - start_time
            response = SemanticAnalysisResponse(
                input_text=text,
                analysis_results=results,
                total_processing_time=total_time,
                overall_success=overall_success,
                cache_hit=False,
                llm_provider=llm_provider
            )
            
            # 缓存结果
            self._cache_result(cache_key, response)
            
            # 更新统计
            if overall_success:
                self.stats['successful_analyses'] += 1
            else:
                self.stats['failed_analyses'] += 1
            self.stats['total_processing_time'] += total_time
            
            logger.info(f"🔍 语义分析完成: {len(results)}项任务, 耗时{total_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"❌ 语义分析失败: {e}")
            self.stats['failed_analyses'] += 1
            
            return SemanticAnalysisResponse(
                input_text=text,
                analysis_results={},
                total_processing_time=time.time() - start_time,
                overall_success=False,
                cache_hit=False,
                llm_provider=None
            )
    
    def _prepare_tasks(self, tasks: Union[List[str], List[AnalysisTask], str]) -> List[AnalysisTask]:
        """准备分析任务列表"""
        if isinstance(tasks, str):
            # 单个任务名称
            if tasks in self.builtin_tasks:
                return [self.builtin_tasks[tasks]]
            else:
                raise ValueError(f"未知的内置任务: {tasks}")
                
        elif isinstance(tasks, list):
            task_list = []
            for task in tasks:
                if isinstance(task, str):
                    # 任务名称字符串
                    if task in self.builtin_tasks:
                        task_list.append(self.builtin_tasks[task])
                    else:
                        raise ValueError(f"未知的内置任务: {task}")
                elif isinstance(task, AnalysisTask):
                    # AnalysisTask对象
                    task_list.append(task)
                else:
                    raise ValueError(f"不支持的任务类型: {type(task)}")
            return task_list
        else:
            raise ValueError(f"不支持的任务格式: {type(tasks)}")
    
    def _execute_single_task(self, text: str, task: AnalysisTask, **kwargs) -> AnalysisResult:
        """执行单个分析任务"""
        start_time = time.time()
        
        try:
            # 准备提示词
            prompt = task.prompt_template.format(text=text) if task.prompt_template else f"请分析: {text}"
            
            # 调用LLM (这里需要实现LLM调用逻辑)
            llm_response = self._call_llm(prompt, task, **kwargs)
            
            # 解析响应
            try:
                result_data = json.loads(llm_response) if isinstance(llm_response, str) else llm_response
                confidence = result_data.get('confidence', task.confidence_threshold)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON解析失败，使用降级处理: {e}")
                result_data = {"raw_response": llm_response, "parse_error": str(e)}
                confidence = 0.5
            
            processing_time = time.time() - start_time
            
            return AnalysisResult(
                task_type=task.task_type,
                result=result_data,
                confidence=confidence,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ 任务执行异常 {task.task_type.value}: {e}")
            
            return AnalysisResult(
                task_type=task.task_type,
                result={},
                confidence=0.0,
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _call_llm(self, prompt: str, task: AnalysisTask, **kwargs) -> str:
        """调用LLM进行分析"""
        if not self.llm_manager:
            # 如果没有LLM管理器，尝试创建一个
            try:
                from ..providers.llm_manager import LLMManager
                self.llm_manager = LLMManager()
                logger.info("🤖 自动创建LLM管理器")
            except ImportError:
                logger.error("❌ 无法导入LLMManager，SemanticAnalyzer需要LLM支持")
                if self.config['enable_fallback']:
                    return self._fallback_analysis(prompt, task)
                raise RuntimeError("SemanticAnalyzer requires LLM support")
        
        try:
            # 构建系统消息
            system_message = "你是一个专业的语义分析助手，专门负责分析文本并返回结构化的JSON结果。请严格按照要求的JSON格式返回，不要包含其他文字说明。"
            
            # 准备消息列表
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
            
            # 使用LLM管理器调用
            response = self.llm_manager.chat_completion(
                messages=messages,
                model=kwargs.get('model', self.config['model_name']),
                temperature=kwargs.get('temperature', self.config['temperature']),
                max_tokens=kwargs.get('max_tokens', 2000),
                timeout=kwargs.get('timeout', self.config['timeout'])
            )
            
            if response and response.success:
                # 记录使用的提供商
                if hasattr(response, 'provider'):
                    self.llm_manager.last_used_provider = response.provider
                return response.content.strip()
            else:
                error_msg = response.error_message if response else "LLM调用无响应"
                logger.warning(f"⚠️ LLM调用失败: {error_msg}")
                
                if self.config['enable_fallback']:
                    return self._fallback_analysis(prompt, task)
                else:
                    raise RuntimeError(f"LLM调用失败: {error_msg}")
                
        except Exception as e:
            logger.error(f"❌ LLM调用异常: {e}")
            if self.config['enable_fallback']:
                return self._fallback_analysis(prompt, task)
            else:
                raise
    
    def _fallback_analysis(self, prompt: str, task: AnalysisTask) -> str:
        """降级分析方法 - 当LLM不可用时的简单规则分析"""
        logger.warning("⚠️ 使用降级分析方法")
        
        # 提取文本进行简单分析
        text = prompt.split('"')[1] if '"' in prompt else prompt
        
        # 简单的规则based分析作为降级
        fallback_results = {
            AnalysisTaskType.INTENT_DETECTION: self._fallback_intent_detection(text),
            AnalysisTaskType.SENTIMENT_ANALYSIS: self._fallback_sentiment_analysis(text),
            AnalysisTaskType.COMPLEXITY_ASSESSMENT: self._fallback_complexity_assessment(text),
            AnalysisTaskType.DOMAIN_CLASSIFICATION: self._fallback_domain_classification(text),
            AnalysisTaskType.URGENCY_EVALUATION: self._fallback_urgency_evaluation(text)
        }
        
        result = fallback_results.get(task.task_type, {"status": "fallback_analysis", "confidence": 0.2})
        return json.dumps(result, ensure_ascii=False)
    
    def _fallback_intent_detection(self, text: str) -> Dict[str, Any]:
        """降级意图识别"""
        text_lower = text.lower()
        
        # 简单的关键词匹配
        question_indicators = ['什么', '如何', '怎么', '为什么', '哪里', '谁', 'what', 'how', 'why', 'where', 'who']
        request_indicators = ['帮助', '需要', '请', '能否', '可以', 'help', 'please', 'can you', 'could you']
        urgent_indicators = ['紧急', '急需', '立即', '马上', 'urgent', 'asap', 'immediately']
        
        primary_intent = "information_seeking"
        confidence = 0.4
        action_required = True
        
        if any(indicator in text_lower for indicator in question_indicators):
            primary_intent = "question_asking"
            confidence = 0.6
        elif any(indicator in text_lower for indicator in request_indicators):
            primary_intent = "help_request"
            confidence = 0.7
        elif any(indicator in text_lower for indicator in urgent_indicators):
            primary_intent = "urgent_request"
            confidence = 0.8
        elif any(greeting in text_lower for greeting in ['你好', 'hello', 'hi']):
            primary_intent = "greeting"
            confidence = 0.9
            action_required = False
        
        return {
            "primary_intent": primary_intent,
            "secondary_intents": [],
            "confidence": confidence,
            "intent_category": "query" if primary_intent in ["question_asking", "information_seeking"] else "request",
            "action_required": action_required
        }
    
    def _fallback_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """降级情感分析"""
        # 简单的正负面词汇统计
        positive_words = ['好', '优秀', '棒', '赞', '喜欢', '满意', '成功', '有效', '创新', 'good', 'great', 'excellent', 'love', 'like']
        negative_words = ['差', '坏', '糟糕', '失败', '问题', '困难', '错误', '不好', 'bad', 'terrible', 'fail', 'problem', 'difficult']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            overall_sentiment = "positive"
            sentiment_score = min(0.8, 0.5 + (positive_count - negative_count) * 0.1)
            intensity = "medium" if positive_count > 2 else "low"
        elif negative_count > positive_count:
            overall_sentiment = "negative"
            sentiment_score = max(-0.8, -0.5 - (negative_count - positive_count) * 0.1)
            intensity = "medium" if negative_count > 2 else "low"
        else:
            overall_sentiment = "neutral"
            sentiment_score = 0.0
            intensity = "low"
        
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": sentiment_score,
            "emotions": {"trust": 0.5, "joy": max(0, sentiment_score)},
            "emotional_intensity": intensity
        }
    
    def _fallback_complexity_assessment(self, text: str) -> Dict[str, Any]:
        """降级复杂度评估"""
        text_lower = text.lower()
        
        # 基于文本长度和关键词的简单评估
        complexity_score = 0.3  # 基础分数
        
        # 长度因素
        if len(text) > 200:
            complexity_score += 0.3
        elif len(text) > 100:
            complexity_score += 0.2
        elif len(text) > 50:
            complexity_score += 0.1
        
        # 复杂性指标
        complex_indicators = ['设计', '架构', '系统', '算法', '优化', '深度', '详细', '全面', 'architecture', 'system', 'complex', 'advanced']
        complexity_score += min(0.4, len([ind for ind in complex_indicators if ind in text_lower]) * 0.1)
        
        complexity_score = min(1.0, complexity_score)
        
        if complexity_score >= 0.7:
            level = "high"
            effort = "substantial"
            expertise = True
        elif complexity_score >= 0.5:
            level = "medium"
            effort = "moderate"
            expertise = False
        else:
            level = "low"
            effort = "minimal"
            expertise = False
        
        return {
            "complexity_level": level,
            "complexity_score": complexity_score,
            "complexity_factors": ["文本长度", "技术术语"] if complexity_score > 0.5 else ["简单任务"],
            "estimated_effort": effort,
            "requires_expertise": expertise
        }
    
    def _fallback_domain_classification(self, text: str) -> Dict[str, Any]:
        """降级领域分类"""
        text_lower = text.lower()
        
        # 领域关键词映射
        domain_keywords = {
            "technology": ['技术', '编程', 'api', '算法', '数据库', '系统', '架构', 'programming', 'algorithm', 'database', 'system'],
            "business": ['商业', '市场', '营销', '销售', '商务', '管理', 'business', 'marketing', 'sales', 'management'],
            "academic": ['学术', '研究', '论文', '理论', '分析', '学习', 'academic', 'research', 'study', 'analysis'],
            "creative": ['创意', '设计', '艺术', '创作', '想象', 'creative', 'design', 'art', 'imagination'],
            "health": ['健康', '医疗', '保健', '医学', 'health', 'medical', 'healthcare'],
            "general": []
        }
        
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                domain_scores[domain] = score / len(keywords) if keywords else 0
        
        if domain_scores:
            primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
            confidence = min(0.8, domain_scores[primary_domain] * 2)
        else:
            primary_domain = "general"
            confidence = 0.3
        
        return {
            "primary_domain": primary_domain,
            "secondary_domains": [d for d, s in domain_scores.items() if d != primary_domain and s > 0],
            "domain_confidence": confidence,
            "is_interdisciplinary": len(domain_scores) > 2,
            "technical_level": "intermediate" if primary_domain == "technology" else "basic"
        }
    
    def _fallback_urgency_evaluation(self, text: str) -> Dict[str, Any]:
        """降级紧急程度评估"""
        text_lower = text.lower()
        
        urgency_indicators = {
            "critical": ['紧急', '急需', '立即', '马上', '现在', 'urgent', 'asap', 'immediately', 'now', 'critical'],
            "high": ['尽快', '较快', '快速', 'soon', 'quickly', 'fast'],
            "medium": ['一般', '普通', '正常', 'normal', 'regular'],
            "low": ['慢慢', '有时间', '不急', '随时', 'whenever', 'no rush', 'slowly']
        }
        
        urgency_level = "medium"  # 默认
        urgency_score = 0.5
        
        for level, indicators in urgency_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                urgency_level = level
                if level == "critical":
                    urgency_score = 0.9
                elif level == "high":
                    urgency_score = 0.7
                elif level == "medium":
                    urgency_score = 0.5
                else:  # low
                    urgency_score = 0.3
                break
        
        time_sensitivity_map = {
            "critical": "immediate",
            "high": "strict", 
            "medium": "moderate",
            "low": "flexible"
        }
        
        priority_map = {
            "critical": 9,
            "high": 7,
            "medium": 5,
            "low": 3
        }
        
        return {
            "urgency_level": urgency_level,
            "urgency_score": urgency_score,
            "time_sensitivity": time_sensitivity_map[urgency_level],
            "consequences": "可能影响后续工作" if urgency_score > 0.6 else "影响较小",
            "priority_rank": priority_map[urgency_level]
        }
    
    def _generate_cache_key(self, text: str, tasks: List[AnalysisTask]) -> str:
        """生成缓存键"""
        task_signatures = [f"{task.task_type.value}:{task.description[:50]}" for task in tasks]
        combined = f"{text}|{','.join(task_signatures)}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[SemanticAnalysisResponse]:
        """获取缓存结果"""
        if cache_key in self.analysis_cache:
            cached_data, timestamp = self.analysis_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                cached_data.cache_hit = True
                return cached_data
            else:
                # 缓存已过期
                del self.analysis_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: SemanticAnalysisResponse):
        """缓存分析结果"""
        self.analysis_cache[cache_key] = (result, time.time())
        
        # 简单的缓存清理：如果缓存过多，清理一半
        if len(self.analysis_cache) > 1000:
            keys_to_remove = list(self.analysis_cache.keys())[:500]
            for key in keys_to_remove:
                del self.analysis_cache[key]
            logger.info("🧹 缓存清理完成")
    
    def add_custom_task(self, task: AnalysisTask) -> None:
        """添加自定义分析任务"""
        self.builtin_tasks[task.task_type.value] = task
        logger.info(f"✅ 已添加自定义任务: {task.task_type.value}")
    
    def get_available_tasks(self) -> Dict[str, str]:
        """获取可用的分析任务列表"""
        return {task_id: task.description for task_id, task in self.builtin_tasks.items()}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取分析统计信息"""
        stats = self.stats.copy()
        stats['cache_hit_rate'] = (
            self.stats['cache_hits'] / max(self.stats['total_analyses'], 1)
        )
        stats['success_rate'] = (
            self.stats['successful_analyses'] / max(self.stats['total_analyses'], 1)  
        )
        stats['average_processing_time'] = (
            self.stats['total_processing_time'] / max(self.stats['total_analyses'], 1)
        )
        return stats
    
    def clear_cache(self):
        """清空分析缓存"""
        self.analysis_cache.clear()
        logger.info("🧹 分析缓存已清空")
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'total_processing_time': 0.0
        }
        logger.info("📊 统计信息已重置")


# 便捷函数
def create_semantic_analyzer(llm_manager=None, config=None) -> SemanticAnalyzer:
    """创建语义分析器实例"""
    return SemanticAnalyzer(llm_manager=llm_manager, config=config)

def quick_analyze(text: str, tasks: Union[List[str], str] = "intent_detection", 
                 llm_manager=None) -> Dict[str, Any]:
    """快速语义分析 - 便捷方法"""
    analyzer = create_semantic_analyzer(llm_manager)
    response = analyzer.analyze(text, tasks)
    
    # 返回简化的结果字典
    results = {}
    for task_type, result in response.analysis_results.items():
        if result.success:
            results[task_type] = result.result
        else:
            results[task_type] = {"error": result.error_message}
    
    return results


if __name__ == "__main__":
    # 简单测试
    print("🔍 SemanticAnalyzer 测试")
    
    # 创建分析器
    analyzer = create_semantic_analyzer()
    
    # 测试分析
    test_text = "我急需一个高性能的机器学习API解决方案"
    test_tasks = ['intent_detection', 'sentiment_analysis', 'complexity_assessment', 'domain_classification']
    
    print(f"测试文本: {test_text}")
    print(f"分析任务: {test_tasks}")
    
    # 注意：这个测试需要有LLM管理器支持才能正常运行
    try:
        response = analyzer.analyze(test_text, test_tasks)
        print(f"分析结果: {response}")
        print(f"统计信息: {analyzer.get_stats()}")
    except Exception as e:
        print(f"测试失败（正常，需要LLM支持）: {e}")
    
    print("✅ SemanticAnalyzer 模块加载成功")
