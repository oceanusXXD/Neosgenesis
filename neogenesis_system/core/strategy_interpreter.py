#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
策略解释器 - 多阶段决策链条的核心组件
完美体现LLM策略建议 → MAB数据驱动选择 → 策略解析生成工具调用的设计理念
"""

from typing import Dict, List, Any, Optional
import logging
import time
import random

logger = logging.getLogger(__name__)


class StrategyInterpreter:
    """
    策略解释器 - 将思维路径的策略特征转换为具体的工具调用策略
    
    这是连接"宏观策略"和"具体行动"的关键桥梁组件，
    避免了简单的关键词匹配，而是基于策略的深层语义特征。
    """
    
    def __init__(self):
        self.name = "StrategyInterpreter"
        
        # 策略特征到工具策略的映射表
        self.strategy_feature_mappings = {
            # 系统分析型策略特征
            'systematic_analytical': {
                'primary_tools': ['knowledge_query', 'data_analysis'],
                'secondary_tools': ['web_search'],
                'execution_pattern': 'sequential',  # 顺序执行
                'confidence_threshold': 0.7,
                'description': '逻辑分析、结构化思考'
            },
            
            # 探索研究型策略特征  
            'exploratory_investigative': {
                'primary_tools': ['web_search', 'tavily_search'],
                'secondary_tools': ['firecrawl_scrape'],
                'execution_pattern': 'parallel',  # 并行执行
                'confidence_threshold': 0.6,
                'description': '深入调研、信息收集'
            },
            
            # 批判质疑型策略特征
            'critical_questioning': {
                'primary_tools': ['idea_verification', 'text_analysis'],
                'secondary_tools': ['web_search'],
                'execution_pattern': 'validation_focused',
                'confidence_threshold': 0.8,
                'description': '质疑分析、风险评估'
            },
            
            # 实用导向型策略特征
            'practical_pragmatic': {
                'primary_tools': ['knowledge_query'],
                'secondary_tools': ['web_search'],
                'execution_pattern': 'direct',  # 直接高效
                'confidence_threshold': 0.5,
                'description': '实际可行、效率优先'
            },
            
            # 创新直觉型策略特征
            'creative_innovative': {
                'primary_tools': [],  # 主要依靠LLM创意，少用工具
                'secondary_tools': ['web_search'],
                'execution_pattern': 'creative_direct',
                'confidence_threshold': 0.9,  # 高置信度才使用工具
                'description': '创造性思维、突破常规'
            },
            
            # 综合全面型策略特征
            'holistic_comprehensive': {
                'primary_tools': ['web_search', 'knowledge_query', 'data_analysis'],
                'secondary_tools': ['idea_verification'],
                'execution_pattern': 'comprehensive',
                'confidence_threshold': 0.6,
                'description': '整体考虑、全局思维'
            },
            
            # 🚨 新增：创新绕道思考策略特征
            '创新绕道思考': {
                'primary_tools': [],  # 主要依靠直接回答，避免过度工具化
                'secondary_tools': ['knowledge_query'],
                'execution_pattern': 'direct_creative',  # 创新直接回答模式
                'confidence_threshold': 0.3,  # 低阈值，优先直接回答
                'description': '突破常规，创新思维回答'
            },
            
            # 自适应灵活型策略特征
            'adaptive_flexible': {
                'primary_tools': [],  # 根据情况灵活选择
                'secondary_tools': ['knowledge_query', 'web_search'],
                'execution_pattern': 'adaptive_direct',
                'confidence_threshold': 0.4,
                'description': '灵活适应、因情而变'
            }
        }
        
        # 查询上下文分析器
        self.context_analyzers = {
            'domain_specific': self._analyze_domain_context,
            'urgency_level': self._analyze_urgency_context,
            'complexity_level': self._analyze_complexity_context
        }
        
        logger.info("🧠 策略解释器初始化完成")
    
    def interpret_strategy_to_actions(self, chosen_path, query: str, 
                                    mab_confidence: float, decision_context: Dict) -> List:
        """
        核心方法：将选中的思维路径策略解释为具体的工具调用行动
        
        Args:
            chosen_path: MAB选中的最优思维路径
            query: 原始用户查询
            mab_confidence: MAB对这个选择的置信度
            decision_context: 决策上下文
            
        Returns:
            具体的Action列表
        """
        logger.info(f"🎯 开始策略解释: {chosen_path.path_type}")
        logger.info(f"   MAB置信度: {mab_confidence:.2f}")
        
        # 1. 获取策略特征
        strategy_features = self._extract_strategy_features(chosen_path)
        
        # 2. 分析查询上下文
        query_context = self._analyze_query_context(query, decision_context)
        
        # 3. 策略适配决策
        action_strategy = self._decide_action_strategy(
            strategy_features, query_context, mab_confidence
        )
        
        # 4. 生成具体行动
        actions = self._generate_concrete_actions(
            action_strategy, chosen_path, query, query_context
        )
        
        logger.info(f"✅ 策略解释完成: 生成 {len(actions)} 个行动")
        return actions
    
    def _extract_strategy_features(self, chosen_path) -> Dict[str, Any]:
        """提取思维路径的策略特征"""
        path_type = chosen_path.path_type.lower()
        
        # 从映射表获取策略特征
        if path_type in self.strategy_feature_mappings:
            base_features = self.strategy_feature_mappings[path_type].copy()
        else:
            # 未知策略类型，使用默认特征
            logger.warning(f"⚠️ 未知策略类型: {path_type}，使用默认特征")
            base_features = self.strategy_feature_mappings['practical_pragmatic'].copy()
        
        # 增强特征：分析路径描述中的语义信息
        description_features = self._analyze_path_description(chosen_path.description)
        base_features.update(description_features)
        
        # 增强特征：从prompt_template中提取执行提示
        template_features = self._analyze_prompt_template(getattr(chosen_path, 'prompt_template', ''))
        base_features.update(template_features)
        
        return base_features
    
    def _analyze_path_description(self, description: str) -> Dict[str, Any]:
        """分析路径描述中的语义特征"""
        features = {}
        description_lower = description.lower() if description else ""
        
        # 信息收集倾向分析
        if any(word in description_lower for word in ['搜索', '调研', '探索', '收集', '查找']):
            features['requires_information_gathering'] = True
            features['information_depth'] = 'deep' if '深入' in description_lower else 'surface'
        
        # 验证需求分析
        if any(word in description_lower for word in ['验证', '确认', '检查', '审查', '质疑']):
            features['requires_verification'] = True
            features['verification_strictness'] = 'high' if '严格' in description_lower else 'moderate'
        
        # 创新需求分析
        if any(word in description_lower for word in ['创新', '创意', '突破', '新颖']):
            features['innovation_focus'] = True
            features['tool_dependency'] = 'low'  # 创新型路径较少依赖工具
        
        return features
    
    def _analyze_prompt_template(self, prompt_template: str) -> Dict[str, Any]:
        """分析提示模板中的执行指示"""
        features = {}
        template_lower = prompt_template.lower() if prompt_template else ""
        
        # 分析模板中的工具使用暗示
        if '搜索' in template_lower or 'search' in template_lower:
            features['template_suggests_search'] = True
        
        if '分析' in template_lower or 'analyze' in template_lower:
            features['template_suggests_analysis'] = True
            
        if '验证' in template_lower or 'verify' in template_lower:
            features['template_suggests_verification'] = True
        
        return features
    
    def _analyze_query_context(self, query: str, decision_context: Dict) -> Dict[str, Any]:
        """综合分析查询上下文"""
        context = {}
        
        # 应用所有上下文分析器
        for analyzer_name, analyzer_func in self.context_analyzers.items():
            try:
                context[analyzer_name] = analyzer_func(query, decision_context)
            except Exception as e:
                logger.warning(f"⚠️ 上下文分析器 {analyzer_name} 失败: {e}")
                context[analyzer_name] = {}
        
        return context
    
    def _analyze_domain_context(self, query: str, context: Dict) -> Dict[str, Any]:
        """分析领域上下文"""
        query_lower = query.lower()
        
        domain_indicators = {
            'technical': ['技术', '编程', '代码', '算法', '系统', 'python', 'java'],
            'business': ['商业', '商务', '市场', '营销', '销售', '管理'],
            'academic': ['学术', '研究', '论文', '理论', '分析'],
            'general': []  # 默认
        }
        
        for domain, keywords in domain_indicators.items():
            if any(keyword in query_lower for keyword in keywords):
                return {'domain': domain, 'specificity': 'high'}
        
        return {'domain': 'general', 'specificity': 'low'}
    
    def _analyze_urgency_context(self, query: str, context: Dict) -> Dict[str, Any]:
        """分析紧急程度上下文"""
        urgency_keywords = {
            'high': ['紧急', '急需', '立即', '马上', 'urgent', 'asap'],
            'medium': ['尽快', '较快', 'soon'],
            'low': ['什么时候', '有时间', '慢慢']
        }
        
        query_lower = query.lower()
        for level, keywords in urgency_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return {'level': level}
        
        return {'level': 'medium'}  # 默认中等紧急程度
    
    def _analyze_complexity_context(self, query: str, context: Dict) -> Dict[str, Any]:
        """分析复杂程度上下文"""
        # 基于查询长度和复杂度指标评估
        complexity_score = 0
        
        # 长度因素
        if len(query) > 100:
            complexity_score += 2
        elif len(query) > 50:
            complexity_score += 1
        
        # 复杂度关键词
        complex_keywords = ['如何实现', '设计方案', '架构', '系统', '详细', '全面']
        complexity_score += sum(1 for keyword in complex_keywords if keyword in query)
        
        if complexity_score >= 3:
            return {'level': 'high', 'requires_comprehensive_approach': True}
        elif complexity_score >= 1:
            return {'level': 'medium', 'requires_balanced_approach': True}
        else:
            return {'level': 'low', 'requires_simple_approach': True}
    
    def _decide_action_strategy(self, strategy_features: Dict, query_context: Dict, 
                              mab_confidence: float) -> Dict[str, Any]:
        """基于策略特征和查询上下文决定行动策略"""
        
        # 基础工具选择
        primary_tools = strategy_features.get('primary_tools', [])
        secondary_tools = strategy_features.get('secondary_tools', [])
        
        # 根据MAB置信度调整工具使用策略
        confidence_threshold = strategy_features.get('confidence_threshold', 0.6)
        
        if mab_confidence < confidence_threshold:
            # 低置信度：更保守，使用更多验证工具
            logger.info(f"🔍 MAB置信度 ({mab_confidence:.2f}) 低于阈值 ({confidence_threshold})，采用保守策略")
            if 'idea_verification' not in primary_tools:
                secondary_tools.append('idea_verification')
        
        # 根据查询复杂度调整策略
        complexity = query_context.get('complexity_level', {}).get('level', 'medium')
        if complexity == 'high':
            # 高复杂度：使用更全面的工具组合
            if 'web_search' not in primary_tools:
                primary_tools.append('web_search')
            if strategy_features.get('execution_pattern') != 'creative_direct':
                primary_tools.append('data_analysis')
        
        # 根据紧急程度调整策略
        urgency = query_context.get('urgency_level', {}).get('level', 'medium')
        execution_pattern = strategy_features.get('execution_pattern', 'sequential')
        
        if urgency == 'high':
            # 高紧急：优化执行模式，减少工具数量
            execution_pattern = 'direct'
            primary_tools = primary_tools[:2]  # 限制最多2个主要工具
        
        return {
            'primary_tools': primary_tools,
            'secondary_tools': secondary_tools,
            'execution_pattern': execution_pattern,
            'max_parallel_tools': 3 if urgency != 'high' else 1,
            'strategy_confidence': mab_confidence,
            'context_factors': {
                'complexity': complexity,
                'urgency': urgency,
                'domain': query_context.get('domain_specific', {}).get('domain', 'general')
            }
        }
    
    def _generate_concrete_actions(self, action_strategy: Dict, chosen_path, 
                                 query: str, query_context: Dict) -> List:
        """生成具体的工具调用行动"""
        try:
            from neogenesis_system.abstractions import Action
        except ImportError:
            # 回退到简单的Action定义
            class Action:
                def __init__(self, tool_name, tool_input):
                    self.tool_name = tool_name
                    self.tool_input = tool_input
                    self.execution_mode = 'sequential'
        
        actions = []
        primary_tools = action_strategy['primary_tools']
        execution_pattern = action_strategy['execution_pattern']
        
        logger.info(f"🔧 生成具体行动: {len(primary_tools)} 个主要工具")
        logger.info(f"   执行模式: {execution_pattern}")
        
        # 🚨 新增：对特定执行模式优先选择直接回答
        if execution_pattern in ['direct_creative', 'adaptive_direct', 'creative_direct']:
            logger.info(f"🎯 检测到直接回答优先模式: {execution_pattern}")
            # 返回空的actions列表，让planner使用直接回答
            return []
        
        for tool_name in primary_tools:
            try:
                action = self._create_tool_action(tool_name, query, chosen_path, query_context)
                if action:
                    actions.append(action)
            except Exception as e:
                logger.warning(f"⚠️ 创建工具行动失败 {tool_name}: {e}")
        
        # 根据执行模式调整行动属性
        if execution_pattern == 'parallel' and len(actions) > 1:
            # 标记为可并行执行
            for action in actions:
                if hasattr(action, 'execution_mode'):
                    action.execution_mode = 'parallel'
        
        return actions
    
    def _create_tool_action(self, tool_name: str, query: str, chosen_path,
                          query_context: Dict):
        """为特定工具创建行动"""
        try:
            from neogenesis_system.abstractions import Action
        except ImportError:
            class Action:
                def __init__(self, tool_name, tool_input):
                    self.tool_name = tool_name
                    self.tool_input = tool_input
        
        # 根据工具类型生成合适的输入参数
        if tool_name == 'web_search' or tool_name == 'tavily_search':
            search_query = self._optimize_search_query(query, chosen_path, query_context)
            return Action(tool_name, {"query": search_query, "max_results": 5})
        
        elif tool_name == 'idea_verification':
            idea_to_verify = self._extract_verification_target(query, chosen_path)
            return Action(tool_name, {"idea_text": idea_to_verify})
        
        elif tool_name == 'knowledge_query':
            topic = self._extract_knowledge_topic(query, chosen_path)
            return Action(tool_name, {"topic": topic})
        
        elif tool_name == 'data_analysis':
            return Action(tool_name, {
                "data_type": "text",
                "data": query,
                "analysis_type": "comprehensive"
            })
        
        else:
            logger.warning(f"⚠️ 未知工具类型: {tool_name}")
            return None
    
    def _optimize_search_query(self, original_query: str, chosen_path, query_context: Dict) -> str:
        """优化搜索查询"""
        # 基础查询
        optimized_query = original_query
        
        # 根据策略类型优化
        if chosen_path.path_type == 'exploratory_investigative':
            optimized_query += " 深入分析 最新发展"
        elif chosen_path.path_type == 'critical_questioning':
            optimized_query += " 风险 挑战 问题"
        elif chosen_path.path_type == 'systematic_analytical':
            optimized_query += " 系统方法 解决方案"
        
        # 根据领域优化
        domain = query_context.get('domain_specific', {}).get('domain', 'general')
        if domain == 'technical':
            optimized_query += " 技术实现"
        elif domain == 'business':
            optimized_query += " 商业应用"
        
        return optimized_query
    
    def _extract_verification_target(self, query: str, chosen_path) -> str:
        """提取需要验证的目标"""
        # 如果查询中包含明确的想法或方案，提取出来
        verification_phrases = ['这个想法', '这个方案', '这种方法', '可行吗', '是否可行']
        
        for phrase in verification_phrases:
            if phrase in query:
                return query
        
        # 否则基于路径类型构造验证目标
        return f"关于'{query}'的可行性和潜在风险"
    
    def _extract_knowledge_topic(self, query: str, chosen_path) -> str:
        """提取知识查询主题"""
        return query[:100]  # 限制长度
    
    def _extract_analysis_target(self, query: str) -> str:
        """提取分析目标"""
        return query


class ImprovedMockNeogenesisPlanner:
    """
    改进的Mock规划器 - 在简化环境下也体现多阶段决策思想
    
    即使在Mock环境中，也要体现:
    1. 策略生成 (简化版PathGenerator)
    2. 策略选择 (简化版MAB)  
    3. 策略解析 (使用StrategyInterpreter)
    """
    
    def __init__(self):
        self.name = "ImprovedMockNeogenesisPlanner"
        self.strategy_interpreter = StrategyInterpreter()
        
        # 简化的策略模板
        self.mock_strategy_templates = {
            'search_focused': {
                'path_type': 'exploratory_investigative',
                'description': '信息搜索和调研导向的策略',
                'prompt_template': '深入搜索和研究关于{task}的信息',
                'trigger_keywords': ['搜索', '查找', '信息', '资料', '了解', '什么是']
            },
            'verification_focused': {
                'path_type': 'critical_questioning',
                'description': '验证和质疑导向的策略',
                'prompt_template': '批判性分析和验证{task}的可行性',
                'trigger_keywords': ['验证', '可行', '风险', '问题', '缺点', '是否']
            },
            'analysis_focused': {
                'path_type': 'systematic_analytical',
                'description': '系统分析导向的策略',
                'prompt_template': '系统性分析{task}的各个方面',
                'trigger_keywords': ['分析', '如何', '方法', '步骤', '实现', '设计']
            },
            'direct_answer': {
                'path_type': 'practical_pragmatic',
                'description': '实用直接回答策略',
                'prompt_template': '基于现有知识直接回答{task}',
                'trigger_keywords': ['你好', 'hello', '介绍', '帮助']
            }
        }
        
        # 简化的选择统计 (模拟MAB)
        self.strategy_success_stats = {
            'search_focused': {'success_count': 10, 'total_count': 15},
            'verification_focused': {'success_count': 8, 'total_count': 12},
            'analysis_focused': {'success_count': 12, 'total_count': 18},
            'direct_answer': {'success_count': 20, 'total_count': 25}
        }
        
        logger.info("🤖 改进的Mock规划器初始化完成")
    
    def create_plan(self, query: str, memory, context=None):
        """改进的计划创建 - 体现简化的多阶段决策"""
        try:
            from neogenesis_system.abstractions import Plan
        except ImportError:
            class Plan:
                def __init__(self, thought, final_answer=None, actions=None):
                    self.thought = thought
                    self.final_answer = final_answer
                    self.actions = actions or []
                    self.is_direct_answer = final_answer is not None
        
        logger.info(f"🤖 Mock规划器开始多阶段决策: {query[:50]}...")
        
        # 阶段1: 策略候选生成 (简化的PathGenerator)
        candidate_strategies = self._generate_candidate_strategies(query)
        logger.info(f"🧠 生成策略候选: {[s['path_type'] for s in candidate_strategies]}")
        
        # 阶段2: 策略选择 (简化的MAB)
        chosen_strategy = self._select_best_strategy(candidate_strategies, query)
        logger.info(f"🎯 选择策略: {chosen_strategy['path_type']}")
        
        # 阶段3: 策略解析为行动 (使用StrategyInterpreter)
        mock_reasoning_path = self._create_mock_reasoning_path(chosen_strategy, query)
        
        # 使用策略解释器生成行动
        try:
            actions = self.strategy_interpreter.interpret_strategy_to_actions(
                chosen_path=mock_reasoning_path,
                query=query,
                mab_confidence=0.8,  # Mock置信度
                decision_context=context or {}
            )
        except Exception as e:
            logger.warning(f"⚠️ 策略解释器调用失败，使用简化逻辑: {e}")
            actions = self._fallback_action_generation(chosen_strategy, query)
        
        # 构建最终计划
        if not actions:
            # 🔧 关键修复：恢复直接回答模式，针对简单问候和介绍类问题
            # 避免所有问题都被强制进入工具执行路径
            
            # 检查是否为简单的直接回答类型
            query_lower = query.lower().strip()
            is_simple_greeting = any(greeting in query_lower for greeting in ['你好', 'hello', 'hi', '您好'])
            is_simple_intro = "介绍" in query_lower and ("自己" in query_lower or "你" in query_lower)
            is_simple_thanks = any(thanks in query_lower for thanks in ['谢谢', 'thanks', 'thank you', '感谢'])
            is_simple_help = any(help_word in query_lower for help_word in ['帮助', '能做什么', '功能'])
            
            if is_simple_greeting or is_simple_intro or is_simple_thanks or is_simple_help:
                # 使用直接回答模式 - 不需要工具调用
                return Plan(
                    thought=f"基于多阶段决策，识别为简单问候/介绍类查询，选择直接回答策略",
                    final_answer=self._generate_direct_answer_for_simple_query(query)
                )
            
            # 对于其他复杂问题，生成工具调用
            if chosen_strategy['path_type'] == 'practical_pragmatic':
                actions = [Action("knowledge_query", {"topic": query})]
            elif chosen_strategy['path_type'] == 'exploratory_investigative':
                actions = [Action("web_search", {"query": query})]
            elif chosen_strategy['path_type'] == 'critical_questioning':
                actions = [Action("idea_verification", {"idea_text": query})]
            else:
                # 默认使用knowledge_query工具
                actions = [Action("knowledge_query", {"topic": query})]
        
        # 工具执行模式
        return Plan(
            thought=f"基于多阶段决策，选择'{chosen_strategy['path_type']}'策略，通过工具调用生成专业回答（{len(actions)}个行动）",
            actions=actions
        )
    
    def _generate_direct_answer_for_simple_query(self, query: str) -> str:
        """为简单查询生成直接回答"""
        query_lower = query.lower().strip()
        
        # 问候类
        if any(greeting in query_lower for greeting in ['你好', 'hello', 'hi', '您好']):
            return "你好！我是Neogenesis智能助手，很高兴为您服务。有什么我可以帮助您的吗？"
        
        # 介绍类  
        if "介绍" in query_lower and ("自己" in query_lower or "你" in query_lower):
            return "我是Neogenesis智能助手，可以帮助您进行信息查询、问题分析、创意思考等多种任务。我会根据不同问题智能选择最合适的处理方式，为您提供准确有用的帮助。"
        
        # 感谢类
        if any(thanks in query_lower for thanks in ['谢谢', 'thanks', 'thank you', '感谢']):
            return "不客气！如果还有其他问题，随时可以问我。"
        
        # 功能查询类
        if any(help_word in query_lower for help_word in ['帮助', '能做什么', '功能']):
            return "我可以帮您搜索信息、分析问题、验证想法、回答各领域问题等。我的特点是能根据不同问题智能选择最合适的处理方式，为您提供有价值的帮助。"
        
        # 默认回答 - 使用LLM或诚实说明限制，避免预设模板
        try:
            # 尝试使用LLM生成简洁回答
            from neogenesis_system.providers.impl.deepseek_client import DeepSeekClient, ClientConfig
            import os
            
            api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('NEOGENESIS_API_KEY')
            if api_key:
                client_config = ClientConfig(
                    api_key=api_key,
                    model="deepseek-chat",
                    temperature=0.7,
                    max_tokens=300
                )
                client = DeepSeekClient(client_config)
                
                prompt = f"""请简洁回答用户问题：{query}

如果无法准确回答，请诚实说明限制。保持友好语气："""
                
                api_response = client.simple_chat(prompt=prompt, max_tokens=300, temperature=0.7)
                llm_response = api_response.content if hasattr(api_response, 'content') else str(api_response)
                
                if llm_response and llm_response.strip():
                    return llm_response.strip()
                    
        except Exception as e:
            logger.warning(f"⚠️ 策略解释器默认LLM调用失败: {e}")
        
        # 最终诚实回答 - 不使用预设模板
        if "时间" in query_lower or "几点" in query_lower:
            return "抱歉，我无法获取当前的实时时间信息。建议您查看您的设备时钟或搜索引擎获取准确时间。"
        elif "天气" in query_lower:
            return "抱歉，我无法获取实时天气信息。建议您查看天气应用或网站获取最新天气预报。"
        else:
            return f"关于您的问题「{query}」，我很愿意帮助您，但我可能需要更多信息才能提供准确的回答。请问您能提供更多具体细节吗？"

    def _generate_candidate_strategies(self, query: str) -> List[Dict]:
        """生成候选策略 - 简化版PathGenerator"""
        candidates = []
        query_lower = query.lower()
        
        # 为每个策略模板计算相关度
        for strategy_id, template in self.mock_strategy_templates.items():
            relevance_score = 0
            
            # 基于关键词匹配计算相关度
            for keyword in template['trigger_keywords']:
                if keyword in query_lower:
                    relevance_score += 1
            
            # 标准化相关度分数
            max_possible_score = len(template['trigger_keywords'])
            normalized_score = relevance_score / max_possible_score if max_possible_score > 0 else 0.1
            
            candidates.append({
                'strategy_id': strategy_id,
                'relevance_score': normalized_score,
                **template
            })
        
        # 按相关度排序
        candidates.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # 返回前3个最相关的策略
        return candidates[:3]
    
    def _select_best_strategy(self, candidates: List[Dict], query: str) -> Dict:
        """选择最佳策略 - 简化版MAB"""
        if not candidates:
            return self.mock_strategy_templates['direct_answer']
        
        best_strategy = None
        best_score = -1
        
        for candidate in candidates:
            strategy_id = candidate['strategy_id']
            
            # 获取历史成功率 (模拟MAB数据)
            stats = self.strategy_success_stats.get(strategy_id, {'success_count': 1, 'total_count': 2})
            success_rate = stats['success_count'] / stats['total_count']
            
            # 结合相关度和成功率 (简化的UCB算法)
            exploration_bonus = 0.1  # 简化的探索奖励
            combined_score = (
                candidate['relevance_score'] * 0.6 +  # 相关度权重
                success_rate * 0.3 +                  # 成功率权重
                exploration_bonus * 0.1               # 探索奖励权重
            )
            
            if combined_score > best_score:
                best_score = combined_score
                best_strategy = candidate
        
        # 更新选择统计 (模拟MAB学习)
        if best_strategy:
            strategy_id = best_strategy['strategy_id']
            self.strategy_success_stats[strategy_id]['total_count'] += 1
        
        return best_strategy or self.mock_strategy_templates['direct_answer']
    
    def _create_mock_reasoning_path(self, strategy: Dict, query: str):
        """创建Mock的ReasoningPath对象"""
        try:
            from neogenesis_system.cognitive_engine.path_generator import ReasoningPath
        except ImportError:
            # 简单的Mock ReasoningPath
            class ReasoningPath:
                def __init__(self, path_id, path_type, description, prompt_template, strategy_id):
                    self.path_id = path_id
                    self.path_type = path_type
                    self.description = description
                    self.prompt_template = prompt_template
                    self.strategy_id = strategy_id
        
        return ReasoningPath(
            path_id=f"mock_{strategy['strategy_id']}",
            path_type=strategy['path_type'],
            description=strategy['description'],
            prompt_template=strategy['prompt_template'].format(task=query),
            strategy_id=strategy['strategy_id']
        )
    
    def _fallback_action_generation(self, strategy: Dict, query: str) -> List:
        """简化的行动生成回退逻辑"""
        try:
            from neogenesis_system.abstractions import Action
        except ImportError:
            class Action:
                def __init__(self, tool_name, tool_input):
                    self.tool_name = tool_name
                    self.tool_input = tool_input
        
        actions = []
        strategy_type = strategy['path_type']
        
        if strategy_type == 'exploratory_investigative':
            actions.append(Action("web_search", {"query": query}))
        elif strategy_type == 'critical_questioning':
            actions.append(Action("idea_verification", {"idea_text": query}))
        elif strategy_type == 'systematic_analytical':
            actions.append(Action("knowledge_query", {"topic": query}))
        
        return actions
    
    def _generate_mock_direct_answer(self, strategy: Dict, query: str) -> str:
        """生成Mock直接回答 - 移除预设回答，确保使用真实的多决策链条"""
        strategy_type = strategy['path_type']
        
        # 🔧 重要修改：移除所有预设回答，包括问候语的预设回复
        # 确保所有问题都通过真正的多阶段决策和工具调用来处理
        
        # 不再提供预设的问候回答，而是返回None或空字符串，
        # 这样会强制系统使用工具执行流程
        return ""  # 返回空字符串，强制走工具执行流程
    
    def validate_plan(self, plan):
        """验证计划"""
        return True
    
    def get_stats(self):
        """获取统计信息"""
        return {
            "name": self.name,
            "total_rounds": 0,
            "strategy_success_stats": self.strategy_success_stats
        }
