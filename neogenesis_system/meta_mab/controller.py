#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主控制器 - 协调各个组件的工作
Main Controller - coordinates the work of all components
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .reasoner import PriorReasoner
from .path_generator import PathGenerator
from .mab_converger import MABConverger
from .data_structures import DecisionResult, SystemStatus
# 🗑️ 已移除：不再直接导入搜索客户端，所有搜索功能通过ToolRegistry进行
# from .utils.search_client import WebSearchClient, IdeaVerificationSearchClient, SearchResponse
from .utils.performance_optimizer import PerformanceOptimizer
from .utils.shutdown_manager import shutdown_neogenesis_system, register_for_shutdown

# 🔧 新增：导入统一工具抽象接口
from .utils.tool_abstraction import (
    ToolRegistry, 
    global_tool_registry,
    register_tool,
    get_tool,
    execute_tool,
    search_tools,
    ToolCategory,
    ToolResult
)
from .utils.search_tools import (
    WebSearchTool,
    IdeaVerificationTool,
    create_and_register_search_tools
)

from config import SYSTEM_LIMITS, FEATURE_FLAGS, PROMPT_TEMPLATES, PERFORMANCE_CONFIG

logger = logging.getLogger(__name__)




@dataclass
class MainController:
    """主控制器 - 协调各个组件的工作"""
    
    def __init__(self, api_key: str = "", config=None):
        self.api_key = api_key
        self.config = config
        
        # 🏗️ 多LLM支持：使用统一的LLM管理器
        from .llm_manager import LLMManager
        
        logger.info(f"🔧 正在初始化LLM管理器...")
        
        # 如果提供了API密钥，设置环境变量（向后兼容）
        if api_key and api_key.strip():
            import os
            os.environ.setdefault("DEEPSEEK_API_KEY", api_key.strip())
            logger.info(f"🔑 API密钥已设置为DEEPSEEK_API_KEY环境变量")
        
        # 创建LLM管理器
        try:
            self.llm_manager = LLMManager()
            self.llm_client = self.llm_manager  # 向后兼容
            
            status = self.llm_manager.get_provider_status()
            logger.info("🧠 LLM管理器初始化完成")
            logger.info(f"   总提供商: {status['total_providers']}")
            logger.info(f"   健康提供商: {status['healthy_providers']}")
            logger.info(f"   初始化状态: {'✅' if status['initialized'] else '❌'}")
            
        except Exception as e:
            logger.error(f"❌ LLM管理器初始化失败: {e}")
            import traceback
            logger.error(f"   详细堆栈: {traceback.format_exc()}")
            
            # 回退到单一客户端模式
            logger.warning("🔄 回退到单一DeepSeek客户端模式")
            self.llm_manager = None
            self.llm_client = self._create_fallback_client(api_key)
        
        # 🔧 初始化工具注册表系统
        self._initialize_tool_registry()
        
        # 🗑️ 已移除：不再需要直接的搜索客户端，所有搜索功能通过ToolRegistry进行
        
        # 完成剩余的初始化工作
        self._complete_initialization()
    
    def _create_fallback_client(self, api_key: str):
        """创建回退客户端"""
        if api_key and api_key.strip():
            try:
                from .utils.client_adapter import DeepSeekClientAdapter
                return DeepSeekClientAdapter(api_key.strip())
            except Exception as e:
                logger.error(f"❌ 回退客户端创建失败: {e}")
                return None
        return None
    
    def _initialize_tool_registry(self):
        """初始化工具注册表系统"""
        try:
            # 使用全局工具注册表
            self.tool_registry = global_tool_registry
            
            # 创建并注册搜索工具
            tools = create_and_register_search_tools()
            
            logger.info(f"🔧 工具注册表初始化完成，已注册 {len(tools)} 个工具")
            for tool_name in tools:
                logger.debug(f"   - {tool_name}")
                
        except Exception as e:
            logger.error(f"❌ 工具注册表初始化失败: {e}")
            self.tool_registry = None
    
    def _execute_llm_with_tools(self, prompt: str, context: Optional[Dict] = None, 
                               available_tools: Optional[List[str]] = None,
                               max_tool_calls: int = 3) -> Dict[str, Any]:
        """
        增强的LLM执行方法 - 支持工具调用
        
        这个方法允许LLM在推理过程中智能地调用工具来获取信息或执行操作。
        工具调用结果会被融入到LLM的思考过程中，实现真正的工具增强推理。
        
        Args:
            prompt: LLM提示词
            context: 上下文信息 
            available_tools: 可用工具列表（如果为None，则使用所有已注册工具）
            max_tool_calls: 最大工具调用次数
            
        Returns:
            包含LLM响应和工具调用结果的字典
        """
        start_time = time.time()
        
        # 准备工具信息
        tool_descriptions = self._prepare_tool_descriptions(available_tools)
        
        # 构建增强的提示词
        enhanced_prompt = self._build_tool_enhanced_prompt(prompt, tool_descriptions, context)
        
        # 执行结果
        result = {
            'llm_response': '',
            'tool_calls': [],
            'tool_results': {},
            'execution_time': 0.0,
            'success': True,
            'error_message': '',
            'context_updates': {}
        }
        
        try:
            # 初始LLM调用
            logger.debug(f"🧠 执行工具增强LLM推理，最大工具调用: {max_tool_calls}")
            
            if self.llm_manager:
                llm_result = self.llm_manager.chat_completion(enhanced_prompt)
                if llm_result.success:
                    llm_response = llm_result.content
                else:
                    raise Exception(f"LLM调用失败: {llm_result.error_message}")
            elif self.llm_client:
                llm_response = self.llm_client.call_api(enhanced_prompt)
            else:
                raise Exception("没有可用的LLM客户端")
            
            result['llm_response'] = llm_response
            
            # 解析并执行工具调用
            tool_calls_made = 0
            current_response = llm_response
            
            while tool_calls_made < max_tool_calls:
                # 检测工具调用意图
                tool_call_request = self._detect_tool_call_intent(current_response)
                
                if not tool_call_request:
                    break
                
                # 执行工具调用
                tool_result = self._execute_detected_tool_call(tool_call_request)
                
                if tool_result:
                    result['tool_calls'].append(tool_call_request)
                    result['tool_results'][tool_call_request['tool_name']] = tool_result
                    
                    # 将工具结果融入到下一次LLM调用中
                    followup_prompt = self._build_tool_followup_prompt(
                        original_prompt=prompt,
                        previous_response=current_response,
                        tool_call=tool_call_request,
                        tool_result=tool_result
                    )
                    
                    # 下一次LLM调用
                    if self.llm_manager:
                        llm_result = self.llm_manager.chat_completion(followup_prompt)
                        if llm_result.success:
                            current_response = llm_result.content
                        else:
                            raise Exception(f"LLM调用失败: {llm_result.error_message}")
                    elif self.llm_client:
                        current_response = self.llm_client.call_api(followup_prompt)
                    
                    result['llm_response'] = current_response  # 更新最终响应
                    tool_calls_made += 1
                    
                    logger.debug(f"🔧 工具调用 {tool_calls_made}: {tool_call_request['tool_name']}")
                else:
                    break
            
            result['execution_time'] = time.time() - start_time
            logger.debug(f"✅ 工具增强LLM执行完成，调用了 {tool_calls_made} 个工具")
            
        except Exception as e:
            result['success'] = False
            result['error_message'] = str(e)
            result['execution_time'] = time.time() - start_time
            logger.error(f"❌ 工具增强LLM执行失败: {e}")
        
        return result
    
    def _prepare_tool_descriptions(self, available_tools: Optional[List[str]] = None) -> str:
        """准备工具描述信息"""
        if not self.tool_registry:
            return "当前没有可用工具。"
        
        if available_tools:
            # 使用指定的工具列表
            tool_list = []
            for tool_name in available_tools:
                tool = get_tool(tool_name)
                if tool:
                    tool_list.append(f"- {tool.name}: {tool.description}")
        else:
            # 使用所有已注册工具
            all_tools = [tool for tool in self.tool_registry]
            tool_list = [f"- {tool.name}: {tool.description}" for tool in all_tools]
        
        if not tool_list:
            return "当前没有可用工具。"
        
        return "可用工具:\n" + "\n".join(tool_list)
    
    def _build_tool_enhanced_prompt(self, original_prompt: str, tool_descriptions: str, 
                                   context: Optional[Dict] = None) -> str:
        """构建工具增强的提示词"""
        enhanced_prompt = f"""
你是一个智能AI助手，具有使用工具的能力。在回答问题时，你可以调用以下工具来获取信息或执行操作：

{tool_descriptions}

调用工具的格式：
**TOOL_CALL**: [工具名称] | [调用参数]

例如：
**TOOL_CALL**: web_search | Python编程最佳实践

请根据以下任务思考是否需要使用工具，如果需要，请按照上述格式调用工具：

{original_prompt}

如果你需要调用工具，请在回答中明确表明，并使用正确的格式。如果不需要工具，请直接回答问题。
"""
        
        if context:
            enhanced_prompt += f"\n\n上下文信息：{context}"
        
        return enhanced_prompt
    
    def _detect_tool_call_intent(self, response: str) -> Optional[Dict[str, Any]]:
        """检测LLM响应中的工具调用意图"""
        import re
        
        # 查找工具调用模式
        pattern = r'\*\*TOOL_CALL\*\*:\s*([^\|]+)\|\s*(.+)'
        match = re.search(pattern, response)
        
        if match:
            tool_name = match.group(1).strip()
            tool_params = match.group(2).strip()
            
            return {
                'tool_name': tool_name,
                'tool_params': tool_params,
                'raw_call': match.group(0)
            }
        
        return None
    
    def _execute_detected_tool_call(self, tool_call_request: Dict[str, Any]) -> Optional[ToolResult]:
        """执行检测到的工具调用"""
        try:
            tool_name = tool_call_request['tool_name']
            tool_params = tool_call_request['tool_params']
            
            # 通过工具注册表执行工具
            result = execute_tool(tool_name, tool_params)
            
            if result and result.success:
                logger.debug(f"✅ 工具 {tool_name} 执行成功")
                return result
            else:
                logger.warning(f"⚠️ 工具 {tool_name} 执行失败: {result.error_message if result else '未知错误'}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 工具调用异常: {e}")
            return None
    
    def _build_tool_followup_prompt(self, original_prompt: str, previous_response: str,
                                   tool_call: Dict[str, Any], tool_result: ToolResult) -> str:
        """构建工具调用后的跟进提示词"""
        
        tool_result_summary = ""
        if tool_result.success and tool_result.data:
            # 根据工具类型格式化结果
            if isinstance(tool_result.data, dict) and 'results' in tool_result.data:
                # 搜索结果格式化
                results = tool_result.data['results'][:3]  # 只取前3个结果
                tool_result_summary = f"搜索到 {len(results)} 个相关结果：\n"
                for i, item in enumerate(results, 1):
                    tool_result_summary += f"{i}. {item.get('title', '无标题')}\n   {item.get('snippet', '无摘要')[:100]}...\n"
            else:
                tool_result_summary = str(tool_result.data)[:500] + "..."
        else:
            tool_result_summary = f"工具调用失败: {tool_result.error_message}"
        
        followup_prompt = f"""
原始任务: {original_prompt}

你刚才调用了工具: {tool_call['tool_name']}
工具调用参数: {tool_call['tool_params']}

工具返回的结果:
{tool_result_summary}

请基于这些工具获取的信息，继续完成原始任务。如果还需要调用其他工具，请继续使用 **TOOL_CALL** 格式。否则，请提供最终答案。
"""
        
        return followup_prompt
    
    def _complete_initialization(self):
        """完成剩余的初始化工作"""
        # 🔧 初始化各个组件 - 注入共享依赖
        self.prior_reasoner = PriorReasoner(self.api_key)  # 轻量级，不需要LLM客户端
        self.path_generator = PathGenerator(self.api_key, llm_client=self.llm_client)  # 注入LLM客户端
        self.mab_converger = MABConverger()
        
        # 🚀 新增：性能优化器
        if FEATURE_FLAGS.get("enable_performance_optimization", False):
            self.performance_optimizer = PerformanceOptimizer(PERFORMANCE_CONFIG)
            logger.info("🚀 性能优化器已启用")
        else:
            self.performance_optimizer = None
            logger.info("📊 性能优化器已禁用")
        
        # 注册系统关闭回调 - 暂时禁用避免递归问题
        # register_for_shutdown(lambda: shutdown_neogenesis_system(self), "MainController")
        logger.debug("⚠️ 关闭回调已禁用，避免递归问题")
        
        # 系统状态
        self.total_rounds = 0
        self.decision_history = []
        
        # 性能统计
        self.performance_stats = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'avg_decision_time': 0.0,
            'component_performance': {
                'prior_reasoner': {'calls': 0, 'avg_time': 0.0},
                'path_generator': {'calls': 0, 'avg_time': 0.0},
                'mab_converger': {'calls': 0, 'avg_time': 0.0},
                'idea_verification': {'calls': 0, 'avg_time': 0.0, 'success_rate': 0.0}  # 新增验证统计
            }
        }
        
        # 💡 Aha-Moment决策系统
        self.aha_moment_stats = {
            'consecutive_failures': 0,         # 连续失败次数
            'last_failure_timestamp': None,    # 最后失败时间
            'total_aha_moments': 0,            # 总Aha-Moment次数
            'aha_success_rate': 0.0,           # Aha-Moment成功率
            'last_decision_success': True,     # 上次决策是否成功
            'failure_threshold': 3,            # 连续失败阈值
            'confidence_threshold': 0.3,       # 置信度阈值
            'aha_decision_history': []         # Aha-Moment决策历史
        }
        
        logger.info("🚀 MainController初始化完成 - 使用工具增强的五阶段决策系统")
        logger.info(f"🔧 工具注册表已装备: {'✅' if self.tool_registry else '❌'} 统一工具接口")
        
        # 显示已注册工具
        if self.tool_registry:
            from .utils.tool_abstraction import list_available_tools
            tools = list_available_tools()
            logger.info(f"🔍 已注册工具: {len(tools)} 个 ({', '.join(tools)})")
        
        # 显示LLM系统状态
        if self.llm_manager:
            status = self.llm_manager.get_provider_status()
            logger.info(f"🧠 LLM系统已装备: ✅ 管理器模式")
            logger.info(f"   可用提供商: {status['healthy_providers']}/{status['total_providers']}")
            
            # 显示主要提供商
            if status['providers']:
                healthy_providers = [name for name, info in status['providers'].items() if info['healthy']]
                if healthy_providers:
                    logger.info(f"   活跃提供商: {', '.join(healthy_providers)}")
        else:
            logger.info(f"🧠 LLM系统已装备: {'✅' if self.llm_client else '❌'} 回退模式")
    
    def make_decision(self, user_query: str, deepseek_confidence: float = 0.5, 
                     execution_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        🚀 五阶段智能验证-学习决策流程 - 内置搜索验证系统
        
        阶段一：思维种子生成 (PriorReasoner) - 理解问题，生成思维种子
        阶段二：种子验证检查 (新增) - 验证思维种子的宏观方向
        阶段三：思维路径生成 (PathGenerator) - 基于种子生成多条路径
        阶段四：路径验证学习 (核心创新) - 逐一验证路径并即时学习
        阶段五：智能最终决策 (升级) - 基于验证结果智能决策
        
        核心创新：AI在思考阶段就获得即时反馈，不再等待最终执行结果
        
        Args:
            user_query: 用户查询
            deepseek_confidence: DeepSeek对该任务的置信度
            execution_context: 执行上下文
            
        Returns:
            决策结果
        """
        start_time = time.time()
        self.total_rounds += 1
        
        logger.info(f"🚀 开始第 {self.total_rounds} 轮五阶段智能验证-学习决策")
        logger.info(f"   查询: {user_query[:50]}...")
        logger.info(f"   DeepSeek置信度: {deepseek_confidence:.2f}")
        
        try:
            # 🧠 阶段一：先验推理 - 生成思维种子（不变）
            reasoner_start = time.time()
            thinking_seed = self.prior_reasoner.get_thinking_seed(user_query, execution_context)
            
            # 兼容性：同时获取旧格式的数据用于向后兼容
            task_confidence = self.prior_reasoner.assess_task_confidence(user_query, execution_context)
            complexity_info = self.prior_reasoner.analyze_task_complexity(user_query)
            
            reasoner_time = time.time() - reasoner_start
            self._update_component_performance('prior_reasoner', reasoner_time)
            
            logger.info(f"🧠 阶段一完成: 思维种子生成 (长度: {len(thinking_seed)} 字符)")
            logger.debug(f"🌱 思维种子预览: {thinking_seed[:100]}...")
            
            # 🔍 阶段二：验证思维种子（新增）- 对宏观方向进行快速验证
            seed_verification_start = time.time()
            seed_verification_result = self.verify_idea_feasibility(
                idea_text=thinking_seed,
                context={
                    'stage': 'thinking_seed',
                    'domain': 'strategic_planning',
                    'query': user_query,
                    **(execution_context if execution_context else {})
                }
            )
            seed_verification_time = time.time() - seed_verification_start
            
            # 分析种子验证结果
            seed_feasibility = seed_verification_result.get('feasibility_analysis', {}).get('feasibility_score', 0.5)
            seed_reward = seed_verification_result.get('reward_score', 0.0)
            
            logger.info(f"🔍 阶段二完成: 思维种子验证 (可行性: {seed_feasibility:.2f}, 奖励: {seed_reward:+.3f})")
            
            if seed_feasibility < 0.3:
                logger.warning(f"⚠️ 思维种子方向存在问题 (可行性: {seed_feasibility:.2f})，但继续执行")
            
            # 🛤️ 阶段三：路径生成 - 基于（已验证的）思维种子生成思维路径列表（不变）
            generator_start = time.time()
            all_reasoning_paths = self.path_generator.generate_paths(
                thinking_seed=thinking_seed, 
                task=user_query,
                max_paths=6  # 限制路径数量以提高性能
            )
            generator_time = time.time() - generator_start
            self._update_component_performance('path_generator', generator_time)
            
            logger.info(f"🛤️ 阶段三完成: 生成了 {len(all_reasoning_paths)} 条思维路径")
            for i, path in enumerate(all_reasoning_paths[:3], 1):  # 记录前3个路径
                logger.debug(f"   路径{i}: {path.path_type} (ID: {path.path_id})")
            
            # 🚀 阶段四：路径验证学习（核心创新）- 逐一验证路径并即时学习
            path_verification_start = time.time()
            # 🚀 性能优化：智能路径验证（支持并行化和自适应）
            verified_paths = []
            all_infeasible = True  # 标记是否所有路径都不可行
            
            # 确定要验证的路径数量（自适应优化）
            original_path_count = len(all_reasoning_paths)
            if self.performance_optimizer and PERFORMANCE_CONFIG.get("enable_adaptive_path_count", False):
                # 提取复杂度分数
                complexity_score = complexity_info.get('overall_score', 0.5) if isinstance(complexity_info, dict) else 0.5
                optimal_count = self.performance_optimizer.adaptive_selector.get_optimal_path_count(
                    confidence=deepseek_confidence,
                    complexity=complexity_score
                )
                # 只验证前N条最有潜力的路径
                paths_to_verify = all_reasoning_paths[:optimal_count]
                logger.info(f"🎯 自适应优化: 从{original_path_count}条路径中选择{optimal_count}条进行验证")
            else:
                paths_to_verify = all_reasoning_paths
            
            logger.info(f"🔬 阶段四开始: 验证 {len(paths_to_verify)} 条思维路径")
            
            # 🚀 并行验证路径（性能优化）
            if (self.performance_optimizer and 
                PERFORMANCE_CONFIG.get("enable_parallel_path_verification", False) and 
                len(paths_to_verify) > 1):
                
                logger.info(f"⚡ 启用并行验证模式 - 最大并发数: {PERFORMANCE_CONFIG.get('max_concurrent_verifications', 3)}")
                
                # 创建验证任务
                def create_verification_task(path):
                    def verify_single_path(p):
                        return self.verify_idea_feasibility(
                            idea_text=f"{p.path_type}: {p.description}",
                            context={
                                'stage': 'reasoning_path',
                                'path_id': p.path_id,
                                'path_type': p.path_type,
                                'query': user_query,
                                **(execution_context if execution_context else {})
                            }
                        )
                    return (path, verify_single_path)
                
                verification_tasks = [create_verification_task(path) for path in paths_to_verify]
                
                # 并行执行验证
                parallel_results = self.performance_optimizer.parallel_verifier.verify_paths_parallel(verification_tasks)
                
                # 处理并行验证结果
                for i, (path, result) in enumerate(zip(paths_to_verify, parallel_results)):
                    if result is None:
                        logger.warning(f"⚠️ 路径 {path.path_type} 并行验证失败，跳过")
                        continue
                    
                    # 提取验证结果
                    path_feasibility = result.get('feasibility_analysis', {}).get('feasibility_score', 0.5)
                    path_reward = result.get('reward_score', 0.0)
                    verification_success = not result.get('fallback', False)
                    
                    # 💡 即时学习：立即将验证结果反馈给MAB系统
                    if verification_success and path_feasibility > 0.3:
                        # 可行的路径 - 正面学习信号
                        self.mab_converger.update_path_performance(
                            path_id=path.strategy_id,  # 🎯 根源修复：使用策略ID进行学习
                            success=True,
                            reward=path_reward
                        )
                        all_infeasible = False  # 至少有一个路径可行
                        logger.debug(f"✅ 路径 {path.path_type} 验证通过: 可行性={path_feasibility:.2f}, 奖励={path_reward:+.3f}")
                    else:
                        # 不可行的路径 - 负面学习信号
                        self.mab_converger.update_path_performance(
                            path_id=path.strategy_id,  # 🎯 根源修复：使用策略ID进行学习
                            success=False,
                            reward=path_reward  # 可能是负值
                        )
                        logger.debug(f"❌ 路径 {path.path_type} 验证失败: 可行性={path_feasibility:.2f}, 奖励={path_reward:+.3f}")
                    
                    # 记录验证结果
                    verified_paths.append({
                        'path': path,
                        'verification_result': result,
                        'feasibility_score': path_feasibility,
                        'reward_score': path_reward,
                        'is_feasible': path_feasibility > 0.3
                    })
                    
                    # 🔄 早期终止检查（性能优化）
                    if (PERFORMANCE_CONFIG.get("enable_early_termination", False) and 
                        len(verified_paths) >= 3 and
                        self.performance_optimizer.adaptive_selector.should_early_terminate(verified_paths)):
                        logger.info(f"🔄 早期终止: 已验证{len(verified_paths)}条路径，结果一致性足够")
                        break
                
            else:
                # 🔄 传统串行验证（兼容模式）
                logger.info("📊 使用传统串行验证模式")
                
                for i, path in enumerate(paths_to_verify, 1):
                    logger.debug(f"🔬 验证路径 {i}/{len(paths_to_verify)}: {path.path_type}")
                    
                    # 🧠 智能缓存检查
                    cache_key = f"{path.path_type}_{path.description[:50]}"
                    cached_result = None
                    if (self.performance_optimizer and 
                        PERFORMANCE_CONFIG.get("enable_intelligent_caching", False)):
                        cached_result = self.performance_optimizer.cache.get(cache_key, execution_context)
                    
                    if cached_result:
                        logger.debug(f"💾 使用缓存结果: {path.path_type}")
                        path_verification_result = cached_result
                    else:
                        # 验证单个路径
                        path_verification_result = self.verify_idea_feasibility(
                            idea_text=f"{path.path_type}: {path.description}",
                            context={
                                'stage': 'reasoning_path',
                                'path_id': path.path_id,
                                'path_type': path.path_type,
                                'query': user_query,
                                **(execution_context if execution_context else {})
                            }
                        )
                        
                        # 💾 缓存结果
                        if (self.performance_optimizer and 
                            PERFORMANCE_CONFIG.get("enable_intelligent_caching", False)):
                            self.performance_optimizer.cache.set(cache_key, path_verification_result, execution_context)
                    
                    # 提取验证结果
                    path_feasibility = path_verification_result.get('feasibility_analysis', {}).get('feasibility_score', 0.5)
                    path_reward = path_verification_result.get('reward_score', 0.0)
                    verification_success = not path_verification_result.get('fallback', False)
                    
                    # 💡 即时学习：立即将验证结果反馈给MAB系统
                    if verification_success and path_feasibility > 0.3:
                        # 可行的路径 - 正面学习信号
                        self.mab_converger.update_path_performance(
                            path_id=path.strategy_id,  # 🎯 根源修复：使用策略ID进行学习
                            success=True,
                            reward=path_reward
                        )
                        all_infeasible = False  # 至少有一个路径可行
                        logger.debug(f"✅ 路径 {path.path_type} 验证通过: 可行性={path_feasibility:.2f}, 奖励={path_reward:+.3f}")
                    else:
                        # 不可行的路径 - 负面学习信号
                        self.mab_converger.update_path_performance(
                            path_id=path.strategy_id,  # 🎯 根源修复：使用策略ID进行学习
                            success=False,
                            reward=path_reward  # 可能是负值
                        )
                        logger.debug(f"❌ 路径 {path.path_type} 验证失败: 可行性={path_feasibility:.2f}, 奖励={path_reward:+.3f}")
                    
                    # 记录验证结果
                    verified_paths.append({
                        'path': path,
                        'verification_result': path_verification_result,
                        'feasibility_score': path_feasibility,
                        'reward_score': path_reward,
                        'is_feasible': path_feasibility > 0.3
                    })
                    
                    # 🔄 早期终止检查（性能优化）
                    if (self.performance_optimizer and 
                        PERFORMANCE_CONFIG.get("enable_early_termination", False) and 
                        len(verified_paths) >= 3 and
                        self.performance_optimizer.adaptive_selector.should_early_terminate(verified_paths)):
                        logger.info(f"🔄 早期终止: 已验证{len(verified_paths)}条路径，结果一致性足够")
                        break
            
            path_verification_time = time.time() - path_verification_start
            feasible_count = sum(1 for vp in verified_paths if vp['is_feasible'])
            
            logger.info(f"🔬 阶段四完成: {feasible_count}/{len(all_reasoning_paths)} 条路径可行")
            logger.info(f"   💡 即时学习: MAB系统已更新所有路径权重")
            
            # 🎯 阶段五：智能最终决策（升级）- 基于验证结果智能决策
            final_decision_start = time.time()
            
            if all_infeasible:
                # 🚨 所有路径都不可行 - 触发智能绕道思考
                logger.warning("🚨 所有思维路径都被验证为不可行，触发智能绕道思考")
                
                # 这是更智能的Aha-Moment触发器
                chosen_path, mab_decision = self._execute_intelligent_detour_thinking(
                    user_query, thinking_seed, all_reasoning_paths, verified_paths
                )
                
                mab_decision.update({
                    'selection_algorithm': 'intelligent_detour',
                    'all_paths_infeasible': True,
                    'detour_triggered': True,
                    'verification_triggered_detour': True
                })
                
                logger.info(f"🚀 智能绕道完成: 选择创新路径 '{chosen_path.path_type}'")
                
            else:
                # ✅ 至少有可行路径 - 使用增强的MAB选择
                logger.info("✅ 发现可行路径，使用验证增强的MAB决策")
                
                # MAB现在已经有了即时学习的权重，会自然倾向于可行路径
                chosen_path = self.mab_converger.select_best_path(all_reasoning_paths)
                
                # 检查是否需要传统的Aha-Moment（作为额外保险）
                aha_triggered, aha_reason = self._check_aha_moment_trigger(chosen_path)
                
                if aha_triggered:
                    logger.info(f"💡 额外触发传统Aha-Moment: {aha_reason}")
                    chosen_path, _ = self._execute_aha_moment_thinking(
                        user_query, thinking_seed, chosen_path, all_reasoning_paths
                    )
                
                mab_decision = {
                    'chosen_path': chosen_path,
                    'available_paths': all_reasoning_paths,
                    'verified_paths': verified_paths,
                    'selection_algorithm': 'verification_enhanced_mab',
                    'converged': self.mab_converger.check_path_convergence(),
                    'all_paths_infeasible': False,
                    'feasible_paths_count': feasible_count,
                    'total_paths_count': len(all_reasoning_paths),
                    'verification_triggered_detour': False,
                    'traditional_aha_triggered': aha_triggered
                }
                
                logger.info(f"🎯 智能决策完成: 选择验证优化路径 '{chosen_path.path_type}'")
            
            final_decision_time = time.time() - final_decision_start
            total_mab_time = path_verification_time + final_decision_time
            self._update_component_performance('mab_converger', total_mab_time)
            
            # 计算总体决策时间
            total_decision_time = time.time() - start_time
            
            # 构建升级版五阶段决策结果
            decision_result = {
                # 基本信息
                'timestamp': time.time(),
                'round_number': self.total_rounds,
                'user_query': user_query,
                'deepseek_confidence': deepseek_confidence,
                'execution_context': execution_context,
                
                # 🚀 五阶段决策结果
                'thinking_seed': thinking_seed,  # 阶段一：思维种子
                'seed_verification': seed_verification_result,  # 阶段二：种子验证
                'chosen_path': chosen_path,  # 最终选中的思维路径
                'available_paths': all_reasoning_paths,  # 阶段三：所有候选路径
                'verified_paths': verified_paths,  # 阶段四：验证结果
                'mab_decision': mab_decision,  # 阶段五：最终决策详情
                
                # 向后兼容字段
                'selected_path': chosen_path,  # 兼容旧接口
                'task_confidence': task_confidence,
                'complexity_analysis': complexity_info,
                
                # 决策元信息
                'reasoning': f"五阶段智能验证-学习决策: {chosen_path.path_type} - {chosen_path.description}",
                'path_count': len(all_reasoning_paths),
                'feasible_path_count': feasible_count,
                'architecture_version': '5-stage-verification',  # 新增：架构版本标识
                'verification_enabled': True,  # 标识启用验证
                'instant_learning_enabled': True,  # 标识启用即时学习
                
                # 🔬 验证统计
                'verification_stats': {
                    'seed_feasibility': seed_feasibility,
                    'seed_reward': seed_reward,
                    'paths_verified': len(verified_paths),
                    'feasible_paths': feasible_count,
                    'infeasible_paths': len(verified_paths) - feasible_count,
                    'all_paths_infeasible': all_infeasible,
                    'average_path_feasibility': sum(vp['feasibility_score'] for vp in verified_paths) / len(verified_paths) if verified_paths else 0.0,
                    'total_verification_time': seed_verification_time + path_verification_time
                },
                
                # 性能指标
                'performance_metrics': {
                    'total_time': total_decision_time,
                    'stage1_reasoner_time': reasoner_time,
                    'stage2_seed_verification_time': seed_verification_time,
                    'stage3_generator_time': generator_time,
                    'stage4_path_verification_time': path_verification_time,
                    'stage5_final_decision_time': final_decision_time,
                    'stages_breakdown': {
                        'thinking_seed_generation': reasoner_time,
                        'seed_verification': seed_verification_time,
                        'path_generation': generator_time,
                        'path_verification_learning': path_verification_time,
                        'intelligent_final_decision': final_decision_time
                    }
                }
            }
            
            # 记录决策历史
            self.decision_history.append(decision_result)
            
            # 限制历史记录长度
            max_history = SYSTEM_LIMITS["max_decision_history"]
            if len(self.decision_history) > max_history:
                self.decision_history = self.decision_history[-max_history//2:]
            
            # 更新性能统计
            self.performance_stats['total_decisions'] += 1
            self._update_avg_decision_time(total_decision_time)
            
            logger.info(f"🎉 五阶段智能验证-学习决策完成:")
            logger.info(f"   🌱 思维种子: {len(thinking_seed)}字符 (可行性: {seed_feasibility:.2f})")
            logger.info(f"   🛤️ 生成路径: {len(all_reasoning_paths)}条")
            logger.info(f"   🔬 验证结果: {feasible_count}条可行/{len(verified_paths)}条总数")
            logger.info(f"   🎯 最终选择: {chosen_path.path_type}")
            logger.info(f"   💡 即时学习: MAB权重已更新")
            logger.info(f"   ⏱️ 总耗时: {total_decision_time:.3f}s")
            logger.info(f"      - 阶段一(种子生成): {reasoner_time:.3f}s")
            logger.info(f"      - 阶段二(种子验证): {seed_verification_time:.3f}s")
            logger.info(f"      - 阶段三(路径生成): {generator_time:.3f}s") 
            logger.info(f"      - 阶段四(路径验证): {path_verification_time:.3f}s")
            logger.info(f"      - 阶段五(智能决策): {final_decision_time:.3f}s")
            
            return decision_result
            
        except Exception as e:
            logger.error(f"❌ 决策过程失败: {e}")
            # 返回错误决策结果
            return self._create_error_decision_result(user_query, str(e), time.time() - start_time)
    
    def _update_component_performance(self, component_name: str, execution_time: float):
        """更新组件性能统计"""
        component_stats = self.performance_stats['component_performance'][component_name]
        component_stats['calls'] += 1
        
        # 计算移动平均
        current_avg = component_stats['avg_time']
        call_count = component_stats['calls']
        component_stats['avg_time'] = (current_avg * (call_count - 1) + execution_time) / call_count
    
    def _update_avg_decision_time(self, decision_time: float):
        """更新平均决策时间"""
        current_avg = self.performance_stats['avg_decision_time']
        total_decisions = self.performance_stats['total_decisions']
        
        if total_decisions == 1:
            self.performance_stats['avg_decision_time'] = decision_time
        else:
            self.performance_stats['avg_decision_time'] = (
                current_avg * (total_decisions - 1) + decision_time
            ) / total_decisions
    
    def _create_error_decision_result(self, user_query: str, error_msg: str, execution_time: float) -> Dict[str, Any]:
        """创建错误决策结果"""
        return {
            'timestamp': time.time(),
            'round_number': self.total_rounds,
            'user_query': user_query,
            'selected_dimensions': {},
            'confidence_scores': {},
            'task_confidence': 0.0,
            'complexity_analysis': {'complexity_score': 0.5, 'estimated_domain': 'error'},
            'mab_decisions': {},
            'reasoning': f"决策失败: {error_msg}",
            'fallback_used': True,
            'component_architecture': True,
            'error': error_msg,
            'performance_metrics': {
                'total_time': execution_time,
                'error_occurred': True
            }
        }
    
    def update_performance_feedback(self, decision_result: Dict[str, Any], 
                                  execution_success: bool, execution_time: float = 30.0,
                                  user_satisfaction: float = 0.5, rl_reward: float = 0.5):
        """
        更新三阶段决策性能反馈 - 升级版组件化架构
        
        Args:
            decision_result: 决策结果
            execution_success: 执行是否成功
            execution_time: 执行时间
            user_satisfaction: 用户满意度
            rl_reward: 强化学习奖励
        """
        try:
            # 🎯 核心更新：基于选中的思维路径更新MAB性能
            chosen_path = decision_result.get('chosen_path') or decision_result.get('selected_path')
            if chosen_path:
                # 使用升级后的路径性能更新方法
                self.mab_converger.update_path_performance(
                    path_id=chosen_path.strategy_id,  # 🎯 根源修复：使用策略ID进行学习
                    success=execution_success,
                    reward=rl_reward
                )
                logger.debug(f"🎰 已更新路径性能: {chosen_path.strategy_id} -> 成功={execution_success}, 奖励={rl_reward:.3f}")
            else:
                logger.warning("⚠️ 未找到选中的思维路径，无法更新MAB性能")
            
            # 📊 更新先验推理器的置信度历史
            task_confidence = decision_result.get('task_confidence', 0.5)
            if hasattr(self.prior_reasoner, 'update_confidence_feedback'):
                self.prior_reasoner.update_confidence_feedback(
                    task_confidence, execution_success, execution_time
                )
            
            # 🧠 新增：更新思维种子的效果跟踪
            thinking_seed = decision_result.get('thinking_seed')
            if thinking_seed and hasattr(self.prior_reasoner, 'update_seed_feedback'):
                self.prior_reasoner.update_seed_feedback(
                    thinking_seed, execution_success, rl_reward
                )
            
            # 📈 更新系统级性能统计
            if execution_success:
                self.performance_stats['successful_decisions'] += 1
            
            # 💡 更新Aha-Moment决策反馈
            self.update_aha_moment_feedback(execution_success)
            
            # 📝 标记决策历史中的执行结果（用于后续失败检测）
            if self.decision_history:
                self.decision_history[-1]['execution_success'] = execution_success
            
            # 🕒 记录详细反馈到决策历史中
            if self.decision_history and self.decision_history[-1]['round_number'] == decision_result.get('round_number'):
                feedback_data = {
                    'execution_success': execution_success,
                    'execution_time': execution_time,
                    'user_satisfaction': user_satisfaction,
                    'rl_reward': rl_reward,
                    'feedback_timestamp': time.time(),
                    'architecture_version': '3-stage',  # 标识为三阶段架构反馈
                    'strategy_id': chosen_path.strategy_id if chosen_path else None,  # 🎯 根源修复：记录策略ID
                    'instance_id': chosen_path.instance_id if chosen_path else None,  # 保留实例ID用于追踪
                    'path_type': chosen_path.path_type if chosen_path else None
                }
                self.decision_history[-1]['feedback'] = feedback_data
            
            # 📊 计算并记录性能指标
            success_rate = self.performance_stats['successful_decisions'] / max(self.performance_stats['total_decisions'], 1)
            
            logger.info(f"📈 三阶段性能反馈已更新:")
            logger.info(f"   🎯 路径: {chosen_path.path_type if chosen_path else 'Unknown'}")
            logger.info(f"   ✅ 执行: 成功={execution_success}, 耗时={execution_time:.2f}s")
            logger.info(f"   🎁 奖励: RL={rl_reward:.3f}, 满意度={user_satisfaction:.3f}")
            logger.info(f"   📊 整体成功率: {success_rate:.1%}")
            
        except Exception as e:
            logger.error(f"❌ 更新三阶段性能反馈失败: {e}")
            logger.exception("详细错误信息:")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取三阶段智能决策系统状态"""
        try:
            # 计算成功率
            success_rate = 0.0
            if self.performance_stats['total_decisions'] > 0:
                success_rate = self.performance_stats['successful_decisions'] / self.performance_stats['total_decisions']
            
            # 获取各组件统计（安全调用，避免方法不存在的错误）
            prior_reasoner_stats = {}
            if hasattr(self.prior_reasoner, 'get_confidence_statistics'):
                prior_reasoner_stats = self.prior_reasoner.get_confidence_statistics()
            else:
                prior_reasoner_stats = {'total_assessments': 0, 'avg_confidence': 0.5, 'confidence_trend': 'stable'}
            
            path_generator_stats = {}
            if hasattr(self.path_generator, 'get_generation_statistics'):
                path_generator_stats = self.path_generator.get_generation_statistics()
            else:
                path_generator_stats = {'total_generations': 0, 'fallback_usage_rate': 0.0, 'avg_dimensions_per_generation': 0}
            
            # 使用升级后的MAB状态获取方法
            mab_stats = self.mab_converger.get_system_status()
            
            # 获取路径级统计
            path_summary = {}
            if hasattr(self.mab_converger, 'get_system_path_summary'):
                path_summary = self.mab_converger.get_system_path_summary()
            
            return {
                # 基本信息
                'total_rounds': self.total_rounds,
                'architecture_version': '3-stage',  # 标识架构版本
                'component_architecture': True,  # 向后兼容
                
                # 系统性能
                'system_performance': {
                    'success_rate': success_rate,
                    'avg_decision_time': self.performance_stats['avg_decision_time'],
                    'total_decisions': self.performance_stats['total_decisions'],
                    'successful_decisions': self.performance_stats['successful_decisions']
                },
                
                # 三阶段组件状态
                'component_status': {
                    'stage1_prior_reasoner': {
                        'assessments_count': prior_reasoner_stats.get('total_assessments', 0),
                        'avg_confidence': prior_reasoner_stats.get('avg_confidence', 0.5),
                        'confidence_trend': prior_reasoner_stats.get('confidence_trend', 'stable'),
                        'thinking_seeds_generated': self.total_rounds,  # 近似值
                        'performance': self.performance_stats['component_performance']['prior_reasoner']
                    },
                    'stage2_path_generator': {
                        'generations_count': path_generator_stats.get('total_generations', 0),
                        'fallback_rate': path_generator_stats.get('fallback_usage_rate', 0.0),
                        'avg_paths_per_generation': path_generator_stats.get('avg_dimensions_per_generation', 0),
                        'performance': self.performance_stats['component_performance']['path_generator']
                    },
                    'stage3_mab_converger': {
                        'mode': mab_stats.get('mode', 'path_selection'),
                        'total_paths': mab_stats.get('total_paths', 0),
                        'active_paths': mab_stats.get('active_paths', 0),
                        'total_selections': mab_stats.get('total_selections', 0),
                        'convergence_level': mab_stats.get('convergence_level', 0.0),
                        'most_popular_path_type': mab_stats.get('most_popular_path_type'),
                        'performance': self.performance_stats['component_performance']['mab_converger']
                    }
                },
                
                # 路径选择状态
                'path_selection_status': {
                    'total_paths_tracked': path_summary.get('total_paths', 0),
                    'is_converged': path_summary.get('is_converged', False),
                    'convergence_level': path_summary.get('convergence_level', 0.0),
                    'most_used_path': path_summary.get('most_used_path'),
                    'best_performing_path': path_summary.get('best_performing_path'),
                    'algorithm_performance': path_summary.get('algorithm_performance', {})
                },
                
                # 系统资源使用
                'memory_usage': {
                    'decision_history_size': len(self.decision_history),
                    'path_arms_count': len(getattr(self.mab_converger, 'path_arms', {})),
                    'path_generation_cache_size': len(getattr(self.path_generator, 'path_generation_cache', {})),
                    'confidence_cache_size': len(getattr(self.prior_reasoner, 'assessment_cache', {}))
                },
                
                # 🚀 性能优化器状态
                'performance_optimization': self._get_performance_optimization_status(),
                
                # 扩展功能状态
                'extended_features': {
                    'thinking_seed_tracking': True,  # 新功能标识
                    'path_performance_tracking': True,
                    'multi_algorithm_mab': True,
                    'aha_moment_decision_enabled': True  # 💡 新增：Aha-Moment决策功能
                },
                
                # 💡 Aha-Moment决策系统状态
                'aha_moment_system': self.get_aha_moment_stats(),
                
                # 💡 路径置信度分析
                'confidence_analysis': self.mab_converger.get_confidence_analysis(),
                
                # 💡 创造性绕道统计
                'creative_bypass_stats': self.path_generator.get_creative_bypass_stats(),
                
                # 🏆 黄金模板系统状态（如果可用）
                'golden_template_system': mab_stats.get('golden_template_system', {}),
                
                # 向后兼容字段
                'recent_decisions': len(self.decision_history)
            }
            
        except Exception as e:
            logger.error(f"❌ 获取系统状态失败: {e}")
            return {
                'error': str(e),
                'total_rounds': self.total_rounds,
                'component_architecture': True
            }
    
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取决策历史记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            决策历史记录列表
        """
        return self.decision_history[-limit:] if self.decision_history else []
    
    def _get_performance_optimization_status(self) -> Dict[str, Any]:
        """获取性能优化器状态"""
        if not self.performance_optimizer:
            return {
                'enabled': False,
                'status': 'disabled',
                'message': '性能优化器未启用'
            }
        
        try:
            optimization_report = self.performance_optimizer.get_performance_report()
            
            return {
                'enabled': True,
                'status': 'active',
                'features': {
                    'parallel_verification': PERFORMANCE_CONFIG.get("enable_parallel_path_verification", False),
                    'intelligent_caching': PERFORMANCE_CONFIG.get("enable_intelligent_caching", False),
                    'adaptive_path_count': PERFORMANCE_CONFIG.get("enable_adaptive_path_count", False),
                    'early_termination': PERFORMANCE_CONFIG.get("enable_early_termination", False)
                },
                'cache_stats': optimization_report.get('cache_stats', {}),
                'performance_improvements': optimization_report.get('optimization_stats', {}),
                'config': {
                    'max_concurrent_verifications': PERFORMANCE_CONFIG.get("max_concurrent_verifications", 3),
                    'cache_ttl_seconds': PERFORMANCE_CONFIG.get("cache_ttl_seconds", 3600),
                    'path_consistency_threshold': PERFORMANCE_CONFIG.get("path_consistency_threshold", 0.8)
                },
                'uptime_hours': optimization_report.get('uptime_hours', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ 获取性能优化器状态失败: {e}")
            return {
                'enabled': True,
                'status': 'error',
                'error': str(e)
            }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取详细性能报告"""
        try:
            report = {
                'overview': {
                    'total_decisions': self.performance_stats['total_decisions'],
                    'successful_decisions': self.performance_stats['successful_decisions'],
                    'success_rate': 0.0,
                    'avg_decision_time': self.performance_stats['avg_decision_time']
                },
                'component_performance': self.performance_stats['component_performance'].copy(),
                'recent_trends': self._analyze_recent_trends(),
                'bottlenecks': self._identify_performance_bottlenecks(),
                'recommendations': self._generate_performance_recommendations()
            }
            
            # 计算成功率
            if report['overview']['total_decisions'] > 0:
                report['overview']['success_rate'] = (
                    report['overview']['successful_decisions'] / report['overview']['total_decisions']
                )
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 生成性能报告失败: {e}")
            return {'error': str(e)}
    
    def _analyze_recent_trends(self) -> Dict[str, Any]:
        """分析最近的性能趋势"""
        if len(self.decision_history) < 5:
            return {'status': 'insufficient_data'}
        
        recent_decisions = self.decision_history[-10:]
        
        # 分析成功率趋势
        recent_successes = [
            1 if d.get('feedback', {}).get('execution_success', False) else 0 
            for d in recent_decisions if 'feedback' in d
        ]
        
        # 分析决策时间趋势
        recent_times = [
            d.get('performance_metrics', {}).get('total_time', 0) 
            for d in recent_decisions
        ]
        
        trends = {
            'success_rate_trend': 'stable',
            'decision_time_trend': 'stable',
            'recent_success_rate': 0.0,
            'recent_avg_time': 0.0
        }
        
        if recent_successes:
            trends['recent_success_rate'] = sum(recent_successes) / len(recent_successes)
            
        if recent_times:
            trends['recent_avg_time'] = sum(recent_times) / len(recent_times)
            
            # 简单趋势分析
            if len(recent_times) >= 5:
                first_half_avg = sum(recent_times[:len(recent_times)//2]) / (len(recent_times)//2)
                second_half_avg = sum(recent_times[len(recent_times)//2:]) / (len(recent_times) - len(recent_times)//2)
                
                if second_half_avg > first_half_avg * 1.2:
                    trends['decision_time_trend'] = 'increasing'
                elif second_half_avg < first_half_avg * 0.8:
                    trends['decision_time_trend'] = 'decreasing'
        
        return trends
    
    def _identify_performance_bottlenecks(self) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        # 分析组件性能
        component_perfs = self.performance_stats['component_performance']
        
        # 找出最慢的组件
        slowest_component = max(component_perfs.items(), key=lambda x: x[1]['avg_time'])
        if slowest_component[1]['avg_time'] > 2.0:  # 超过2秒
            bottlenecks.append(f"{slowest_component[0]}响应时间过长 ({slowest_component[1]['avg_time']:.2f}s)")
        
        # 检查缓存命中率
        if hasattr(self.path_generator, 'generation_cache') and len(self.path_generator.generation_cache) > 20:
            bottlenecks.append("路径生成缓存可能过大，影响内存使用")
        
        # 检查决策历史大小
        if len(self.decision_history) > SYSTEM_LIMITS["max_decision_history"] * 0.8:
            bottlenecks.append("决策历史接近上限，可能影响性能")
        
        return bottlenecks
    
    def _generate_performance_recommendations(self) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        # 基于成功率的建议
        success_rate = 0.0
        if self.performance_stats['total_decisions'] > 0:
            success_rate = self.performance_stats['successful_decisions'] / self.performance_stats['total_decisions']
        
        if success_rate < 0.7:
            recommendations.append("成功率较低，建议检查维度生成策略和MAB算法参数")
        
        # 基于决策时间的建议
        if self.performance_stats['avg_decision_time'] > 3.0:
            recommendations.append("平均决策时间较长，建议优化API调用或增加缓存")
        
        # 基于组件性能的建议
        component_perfs = self.performance_stats['component_performance']
        for component_name, perf in component_perfs.items():
            if perf['avg_time'] > 1.5:
                recommendations.append(f"优化{component_name}组件性能，当前平均耗时{perf['avg_time']:.2f}秒")
        
        if not recommendations:
            recommendations.append("系统性能良好，无特别优化建议")
        
        return recommendations
    
    # ==================== 💡 Aha-Moment决策系统实现 ====================
    
    def _check_aha_moment_trigger(self, chosen_path) -> Tuple[bool, str]:
        """
        检查是否需要触发Aha-Moment决策（绕道思考）
        
        Args:
            chosen_path: MAB选择的思维路径
            
        Returns:
            (是否触发, 触发原因)
        """
        # 触发条件1：路径置信度过低
        if hasattr(chosen_path, 'strategy_id'):
            path_confidence = self.mab_converger.get_path_confidence(chosen_path.strategy_id)
            
            if path_confidence < self.aha_moment_stats['confidence_threshold']:
                return True, f"选中路径置信度过低 ({path_confidence:.3f} < {self.aha_moment_stats['confidence_threshold']})"
        
        # 触发条件2：所有路径都表现很差
        is_low_confidence_scenario = self.mab_converger.check_low_confidence_scenario(
            threshold=self.aha_moment_stats['confidence_threshold']
        )
        
        if is_low_confidence_scenario:
            return True, "所有可用路径的置信度都偏低，需要创造性突破"
        
        # 触发条件3：连续失败次数过多
        if self.aha_moment_stats['consecutive_failures'] >= self.aha_moment_stats['failure_threshold']:
            return True, f"连续失败 {self.aha_moment_stats['consecutive_failures']} 次，超过阈值 {self.aha_moment_stats['failure_threshold']}"
        
        # 触发条件4：特定时间间隔内的失败密度过高
        recent_failures = self._count_recent_failures(time_window=300)  # 5分钟内
        if recent_failures >= 3:
            return True, f"最近5分钟内失败 {recent_failures} 次，频率过高"
        
        return False, "常规决策路径表现正常"
    
    def _execute_aha_moment_thinking(self, user_query: str, thinking_seed: str, 
                                   original_path, original_paths) -> Tuple[Any, List[Any]]:
        """
        执行Aha-Moment绕道思考
        
        Args:
            user_query: 用户查询
            thinking_seed: 原始思维种子
            original_path: 原始选择的路径
            original_paths: 原始路径列表
            
        Returns:
            (新选择的路径, 新的路径列表)
        """
        aha_start_time = time.time()
        self.aha_moment_stats['total_aha_moments'] += 1
        
        logger.info("💡 开始执行Aha-Moment绕道思考...")
        logger.info(f"   原始路径: {original_path.path_type}")
        logger.info(f"   原始路径数量: {len(original_paths)}")
        
        try:
            # Step 1: 生成创造性绕道路径
            logger.info("🌟 生成创造性思维路径...")
            creative_paths = self.path_generator.generate_paths(
                thinking_seed=thinking_seed,
                task=user_query,
                max_paths=4,  # 减少数量，专注质量
                mode='creative_bypass'  # 创造性绕道模式
            )
            
            logger.info(f"🌟 生成了 {len(creative_paths)} 条创造性路径")
            for i, path in enumerate(creative_paths, 1):
                logger.info(f"   创造性路径{i}: {path.path_type}")
            
            # Step 2: 合并原始路径和创造性路径
            combined_paths = original_paths + creative_paths
            
            # Step 3: 使用MAB重新选择（现在有更多选择）
            logger.info("🎯 在扩展路径集合中重新选择最优路径...")
            final_chosen_path = self.mab_converger.select_best_path(combined_paths)
            
            # Step 4: 记录Aha-Moment决策历史
            aha_record = {
                'timestamp': time.time(),
                'trigger_reason': 'low_confidence_scenario',
                'original_path': original_path.path_type,
                'creative_paths_generated': len(creative_paths),
                'final_chosen_path': final_chosen_path.path_type,
                'was_creative_path_chosen': final_chosen_path in creative_paths,
                'aha_thinking_time': time.time() - aha_start_time
            }
            
            self.aha_moment_stats['aha_decision_history'].append(aha_record)
            
            # 限制历史记录长度
            if len(self.aha_moment_stats['aha_decision_history']) > 100:
                self.aha_moment_stats['aha_decision_history'] = self.aha_moment_stats['aha_decision_history'][-50:]
            
            logger.info(f"💡 Aha-Moment思考完成:")
            logger.info(f"   最终路径: {final_chosen_path.path_type}")
            logger.info(f"   是否选择创造性路径: {'是' if final_chosen_path in creative_paths else '否'}")
            logger.info(f"   绕道思考耗时: {time.time() - aha_start_time:.3f}s")
            
            return final_chosen_path, combined_paths
            
        except Exception as e:
            logger.error(f"❌ Aha-Moment思考过程失败: {e}")
            logger.warning("🔄 回退到原始路径选择")
            return original_path, original_paths
    
    def _count_recent_failures(self, time_window: int = 300) -> int:
        """
        统计最近时间窗口内的失败次数
        
        Args:
            time_window: 时间窗口（秒）
            
        Returns:
            失败次数
        """
        if not self.decision_history:
            return 0
        
        current_time = time.time()
        failure_count = 0
        
        for decision in reversed(self.decision_history):
            if current_time - decision.get('timestamp', 0) > time_window:
                break  # 超出时间窗口
            
            # 检查这个决策是否被标记为失败
            # 这需要在update_performance_feedback中设置
            if decision.get('execution_success', True) is False:
                failure_count += 1
        
        return failure_count
    
    def update_aha_moment_feedback(self, success: bool):
        """
        更新Aha-Moment决策的反馈
        
        Args:
            success: 决策是否成功
        """
        if success:
            self.aha_moment_stats['consecutive_failures'] = 0
            self.aha_moment_stats['last_decision_success'] = True
            logger.debug("✅ 决策成功，重置连续失败计数")
        else:
            self.aha_moment_stats['consecutive_failures'] += 1
            self.aha_moment_stats['last_decision_success'] = False
            self.aha_moment_stats['last_failure_timestamp'] = time.time()
            logger.debug(f"❌ 决策失败，连续失败次数: {self.aha_moment_stats['consecutive_failures']}")
        
        # 更新Aha-Moment成功率统计
        if self.aha_moment_stats['aha_decision_history']:
            aha_successes = sum(1 for record in self.aha_moment_stats['aha_decision_history'] 
                              if record.get('success', False))
            total_aha = len(self.aha_moment_stats['aha_decision_history'])
            self.aha_moment_stats['aha_success_rate'] = aha_successes / total_aha
    
    def get_aha_moment_stats(self) -> Dict[str, any]:
        """
        获取Aha-Moment决策系统的统计信息
        
        Returns:
            统计信息字典
        """
        recent_aha_count = sum(1 for record in self.aha_moment_stats['aha_decision_history']
                              if time.time() - record['timestamp'] < 3600)  # 最近1小时
        
        return {
            'total_aha_moments': self.aha_moment_stats['total_aha_moments'],
            'consecutive_failures': self.aha_moment_stats['consecutive_failures'],
            'aha_success_rate': self.aha_moment_stats['aha_success_rate'],
            'recent_aha_count': recent_aha_count,
            'failure_threshold': self.aha_moment_stats['failure_threshold'],
            'confidence_threshold': self.aha_moment_stats['confidence_threshold'],
            'last_failure_timestamp': self.aha_moment_stats['last_failure_timestamp'],
            'last_decision_success': self.aha_moment_stats['last_decision_success'],
            'history_count': len(self.aha_moment_stats['aha_decision_history'])
        }
    
    def reset_system(self, preserve_learnings: bool = True):
        """
        重置系统状态
        
        Args:
            preserve_learnings: 是否保留学习到的知识
        """
        logger.info("🔄 开始重置系统...")
        
        # 重置计数器
        self.total_rounds = 0
        self.decision_history.clear()
        
        # 重置性能统计
        self.performance_stats = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'avg_decision_time': 0.0,
            'component_performance': {
                'prior_reasoner': {'calls': 0, 'avg_time': 0.0},
                'path_generator': {'calls': 0, 'avg_time': 0.0},
                'mab_converger': {'calls': 0, 'avg_time': 0.0},
                'idea_verification': {'calls': 0, 'avg_time': 0.0, 'success_rate': 0.0}  # 包含新的验证统计
            }
        }
        
        if not preserve_learnings:
            # 清除所有学习数据
            self.prior_reasoner.reset_cache()
            self.path_generator.clear_cache()
            # MAB数据不清除，因为它是核心学习机制
            logger.info("🧹 已清除缓存和临时数据")
        
        logger.info("✅ 系统重置完成")
        
        # 🗑️ 已移除：不再需要清理验证客户端缓存，工具缓存由ToolRegistry管理
    
    # ================================
    # 🔬 新增：想法验证研究员能力
    # ================================
    
    def verify_idea_feasibility(self, idea_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        🔧 工具增强的想法验证流程 - 从硬编码搜索升级为灵活工具调用
        
        原有方法本质上是一个硬编码的"搜索工具"调用。现在升级为：
        1. 智能工具选择：根据验证需求选择最合适的工具
        2. 工具增强推理：LLM可以调用多个工具获取信息
        3. 动态验证策略：根据想法类型采用不同验证方法
        4. 学习反馈机制：工具使用结果影响MAB学习
        
        Args:
            idea_text: 需要验证的想法文本（思维种子或思维路径描述）
            context: 上下文信息
            
        Returns:
            增强的验证结果字典
        """
        start_time = time.time()
        logger.info(f"🔬 开始想法验证研究: {idea_text[:50]}...")
        
        try:
            # 🔧 使用工具增强的验证流程（无回退机制）
            verification_result = self._enhanced_verification_with_tools(idea_text, context)
            
            # 如果工具增强验证失败，直接返回失败结果
            if not verification_result.get('success', False):
                logger.error("❌ 工具增强验证失败，无回退机制")
                execution_time = time.time() - start_time
                return self._create_direct_failure_result(
                    idea_text, 
                    verification_result.get('error_message', '工具增强验证失败'), 
                    execution_time
                )
            
            # 统计和学习反馈
            execution_time = time.time() - start_time
            self._update_verification_stats(verification_result, execution_time)
            
            logger.info(f"✅ 想法验证完成: 可行性={verification_result.get('feasibility_analysis', {}).get('feasibility_score', 0):.2f}")
            return verification_result
            
        except Exception as e:
            logger.error(f"❌ 想法验证异常: {e}")
            execution_time = time.time() - start_time
            return self._create_direct_failure_result(
                idea_text, f"验证异常: {e}", execution_time
            )
    
    def _enhanced_verification_with_tools(self, idea_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        🔧 工具增强的验证方法 - 核心升级
        
        这个方法展示了如何将原有的硬编码搜索改造为灵活的工具调用：
        1. 智能工具选择：根据想法类型选择最合适的验证工具
        2. 多步骤验证：可以连续使用多个工具
        3. 上下文感知：根据验证阶段调整工具使用策略
        """
        try:
            # 构建验证提示词
            verification_prompt = self._build_verification_prompt(idea_text, context)
            
            # 选择适合验证的工具
            available_tools = self._select_verification_tools(idea_text, context)
            
            # 使用工具增强的LLM推理
            llm_result = self._execute_llm_with_tools(
                prompt=verification_prompt,
                context=context,
                available_tools=available_tools,
                max_tool_calls=2  # 验证阶段限制工具调用次数
            )
            
            if not llm_result['success']:
                return {'success': False, 'error_message': llm_result['error_message']}
            
            # 解析LLM的验证结果
            verification_analysis = self._parse_verification_response(llm_result['llm_response'])
            
            # 计算奖励分数（考虑工具使用效果）
            reward_score = self._calculate_enhanced_reward(verification_analysis, llm_result['tool_calls'])
            
            return {
                'success': True,
                'idea_text': idea_text,
                'feasibility_analysis': verification_analysis,
                'reward_score': reward_score,
                'tool_calls_made': len(llm_result['tool_calls']),
                'tool_results': llm_result['tool_results'],
                'execution_time': llm_result['execution_time'],
                'verification_method': 'tool_enhanced'
            }
            
        except Exception as e:
            logger.error(f"❌ 工具增强验证失败: {e}")
            return {'success': False, 'error_message': str(e)}
    
    def _build_verification_prompt(self, idea_text: str, context: Optional[Dict] = None) -> str:
        """构建验证提示词"""
        stage = context.get('stage', 'unknown') if context else 'unknown'
        
        prompt = f"""
请分析以下想法的可行性，并提供详细的评估报告。你可以使用搜索工具来获取相关信息：

想法内容：{idea_text}

分析阶段：{stage}
"""
        
        if context:
            if 'query' in context:
                prompt += f"\n原始查询：{context['query']}"
            if 'domain' in context:
                prompt += f"\n应用领域：{context['domain']}"
        
        prompt += """

请从以下角度进行分析：
1. 技术可行性 - 从技术角度评估实现难度
2. 市场需求 - 分析是否有实际需求
3. 资源要求 - 评估所需资源和成本
4. 风险评估 - 识别潜在风险和挑战
5. 创新程度 - 评估想法的新颖性

如果需要获取最新信息，请使用搜索工具。

最后，请给出一个0-1之间的可行性评分，并简要说明理由。
"""
        
        return prompt
    
    def _select_verification_tools(self, idea_text: str, context: Optional[Dict] = None) -> List[str]:
        """根据验证需求选择合适的工具"""
        available_tools = ["web_search"]  # 基础搜索工具
        
        # 根据想法类型和上下文选择额外工具
        if context:
            stage = context.get('stage', '')
            if stage == 'thinking_seed':
                # 思维种子阶段：需要广泛的信息收集
                available_tools.extend(["idea_verification"])
            elif stage == 'reasoning_path':
                # 推理路径阶段：需要深度验证
                available_tools.extend(["idea_verification"])
        
        # 根据想法内容推断需要的工具
        idea_lower = idea_text.lower()
        if any(keyword in idea_lower for keyword in ['技术', 'technology', '编程', 'programming']):
            # 技术类想法可能需要更多技术资源
            pass  # 未来可以添加技术类验证工具
        
        return available_tools
    
    def _parse_verification_response(self, llm_response: str) -> Dict[str, Any]:
        """解析LLM的验证响应"""
        # 尝试从响应中提取可行性评分
        import re
        
        # 查找评分
        score_patterns = [
            r'可行性评分[：:]\s*([0-9]*\.?[0-9]+)',
            r'评分[：:]\s*([0-9]*\.?[0-9]+)',
            r'score[：:]?\s*([0-9]*\.?[0-9]+)',
            r'([0-9]*\.?[0-9]+)\s*/\s*1',
            r'([0-9]*\.?[0-9]+)\s*分'
        ]
        
        feasibility_score = 0.5  # 默认值
        for pattern in score_patterns:
            match = re.search(pattern, llm_response, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    if score > 1:  # 可能是百分制
                        score = score / 100
                    feasibility_score = max(0, min(1, score))  # 限制在0-1范围
                    break
                except ValueError:
                    continue
        
        # 提取关键分析要点
        analysis_summary = llm_response[:500] + "..." if len(llm_response) > 500 else llm_response
        
        return {
            'feasibility_score': feasibility_score,
            'analysis_summary': analysis_summary,
            'full_response': llm_response
        }
    
    def _calculate_enhanced_reward(self, verification_analysis: Dict[str, Any], tool_calls: List[Dict]) -> float:
        """计算增强的奖励分数（考虑工具使用效果）"""
        base_score = verification_analysis.get('feasibility_score', 0.5)
        
        # 工具使用奖励
        tool_bonus = 0.0
        if tool_calls:
            # 成功使用工具获得小幅奖励
            tool_bonus = min(0.1, len(tool_calls) * 0.05)
        
        # 最终奖励分数
        reward = base_score + tool_bonus - 0.5  # 转换为[-0.5, 0.6]范围
        
        return reward
    

    def _update_verification_stats(self, verification_result: Dict[str, Any], execution_time: float):
        """更新验证统计信息"""
        success = verification_result.get('success', False)
        
        # 更新组件性能统计
        current_stats = self.performance_stats['component_performance']['idea_verification']
        current_stats['calls'] += 1
        
        # 更新平均时间
        if current_stats['calls'] == 1:
            current_stats['avg_time'] = execution_time
        else:
            current_stats['avg_time'] = (current_stats['avg_time'] * (current_stats['calls'] - 1) + execution_time) / current_stats['calls']
        
        # 更新成功率
        if 'total_success' not in current_stats:
            current_stats['total_success'] = 0
        
        if success:
            current_stats['total_success'] += 1
        
        current_stats['success_rate'] = current_stats['total_success'] / current_stats['calls']
        
        # 记录工具使用统计
        verification_method = verification_result.get('verification_method', 'unknown')
        tool_calls_made = verification_result.get('tool_calls_made', 0)
        
        if 'verification_methods' not in current_stats:
            current_stats['verification_methods'] = {}
        
        if verification_method not in current_stats['verification_methods']:
            current_stats['verification_methods'][verification_method] = 0
        current_stats['verification_methods'][verification_method] += 1
        
        if 'tool_usage' not in current_stats:
            current_stats['tool_usage'] = {'total_calls': 0, 'calls_per_verification': 0}
        
        current_stats['tool_usage']['total_calls'] += tool_calls_made
        current_stats['tool_usage']['calls_per_verification'] = current_stats['tool_usage']['total_calls'] / current_stats['calls']
        
        logger.debug(f"📊 验证统计更新: 成功率={current_stats['success_rate']:.1%}, 方法={verification_method}, 工具调用={tool_calls_made}")
    
    def _create_direct_failure_result(self, idea_text: str, error_message: str, execution_time: float = 0.0) -> Dict[str, Any]:
        """创建直接失败结果（无回退机制）"""
        return {
            'success': False,
            'idea_text': idea_text,
            'feasibility_analysis': {
                'feasibility_score': 0.0,  # 失败时给予最低评分
                'analysis_summary': f"工具增强验证失败: {error_message}。系统将依赖MAB学习避免此类路径。"
            },
            'reward_score': -0.5,  # 强负奖励，让MAB系统学会避免导致失败的路径
            'error_message': error_message,
            'execution_time': execution_time,
            'verification_method': 'tool_enhanced_failed',
            'tool_calls_made': 0,
            'tool_results': {}
        }
    
    def _preprocess_idea_text(self, idea_text: str) -> str:
        """预处理想法文本"""
        # 清理和标准化文本
        cleaned = idea_text.strip()
        
        # 限制长度（避免过长的搜索查询）
        if len(cleaned) > 200:
            cleaned = cleaned[:200] + "..."
            
        return cleaned
    
    def _generate_verification_query(self, idea_text: str, context: Optional[Dict] = None) -> str:
        """
        生成验证查询 - 将想法转换成适合搜索的问题
        
        Args:
            idea_text: 想法文本
            context: 上下文
            
        Returns:
            搜索查询字符串
        """
        # 提取核心技术概念
        tech_concepts = self._extract_technical_concepts(idea_text)
        
        # 构建查询模板
        if tech_concepts:
            query_template = f"'{' '.join(tech_concepts[:2])}' 技术可行性 实现方法 潜在风险 最佳实践"
        else:
            query_template = f"'{idea_text[:50]}' 解决方案 技术实现 挑战分析"
        
        # 添加领域上下文
        if context and 'domain' in context:
            query_template += f" {context['domain']}"
        
        return query_template
    
    def _extract_technical_concepts(self, text: str) -> List[str]:
        """提取技术概念"""
        tech_terms = [
            'API', 'api', '算法', '数据库', '系统', '架构', '优化',
            '机器学习', 'ML', 'AI', '人工智能', '深度学习',
            '网络', '爬虫', '数据分析', '实时', '性能', '安全',
            '并发', '分布式', '微服务', '容器', '云计算', '区块链',
            'Python', 'Java', 'JavaScript', 'React', 'Node.js'
        ]
        
        found_concepts = []
        text_lower = text.lower()
        
        for term in tech_terms:
            if term.lower() in text_lower:
                found_concepts.append(term)
        
        return found_concepts[:3]  # 返回前3个概念
    
    # 🗑️ 已移除 _analyze_idea_feasibility - 传统验证系统的一部分
    
    # 🗑️ 已移除 _build_feasibility_analysis_prompt - 传统验证系统的一部分
    
    # 🗑️ 已移除 _parse_feasibility_analysis - 传统验证系统的一部分
    
    # 🗑️ 已移除 _create_default_analysis_result - 传统验证系统的一部分
    
    # 🗑️ 已移除 _heuristic_feasibility_analysis - 传统验证系统的一部分
    
    # 🗑️ 已移除 _calculate_verification_reward - 传统验证系统的一部分
    

    def _update_verification_performance(self, verification_result: Dict[str, Any]):
        """更新验证性能统计"""
        perf_stats = self.performance_stats['component_performance']['idea_verification']
        
        # 更新调用次数
        perf_stats['calls'] += 1
        
        # 更新平均时间
        if perf_stats['calls'] == 1:
            perf_stats['avg_time'] = verification_result['verification_time']
        else:
            perf_stats['avg_time'] = (
                (perf_stats['avg_time'] * (perf_stats['calls'] - 1) + verification_result['verification_time'])
                / perf_stats['calls']
            )
        
        # 更新成功率
        success = not verification_result.get('fallback', False)
        if perf_stats['calls'] == 1:
            perf_stats['success_rate'] = 1.0 if success else 0.0
        else:
            current_success_count = perf_stats['success_rate'] * (perf_stats['calls'] - 1)
            if success:
                current_success_count += 1
            perf_stats['success_rate'] = current_success_count / perf_stats['calls']
    
    # ================================
    # 🚀 智能绕道思考系统（全新Aha-Moment）
    # ================================
    
    def _execute_intelligent_detour_thinking(self, user_query: str, thinking_seed: str, 
                                           original_paths: List, verified_paths: List) -> Tuple[Any, Dict]:
        """
        智能绕道思考 - 当所有常规路径都被验证为不可行时的创新决策
        
        这是基于验证结果的新型Aha-Moment触发器，比传统方法更智能
        
        Args:
            user_query: 用户查询
            thinking_seed: 思维种子
            original_paths: 原始路径列表
            verified_paths: 验证结果列表
            
        Returns:
            Tuple[chosen_path, mab_decision]
        """
        logger.info("🚀 开始智能绕道思考 - 寻找创新解决方案")
        
        try:
            # 分析失败模式 - 从验证结果中学习
            failure_patterns = self._analyze_verification_failures(verified_paths)
            logger.debug(f"📊 失败模式分析: {failure_patterns}")
            
            # 基于失败分析生成创新种子
            innovative_seed = self._generate_innovative_thinking_seed(
                user_query, thinking_seed, failure_patterns
            )
            
            # 生成创新路径
            if innovative_seed:
                logger.info("💡 基于失败分析生成创新思维种子")
                innovative_paths = self.path_generator.generate_paths(
                    thinking_seed=innovative_seed,
                    task=user_query,
                    max_paths=3  # 专注于少数创新路径
                )
            else:
                innovative_paths = []
            
            # 如果创新路径生成失败，使用应急创新路径
            if not innovative_paths:
                logger.warning("⚠️ 创新路径生成失败，使用应急创新路径")
                innovative_paths = self._create_emergency_innovative_paths(user_query, failure_patterns)
            
            # 验证创新路径
            best_innovative_path = None
            best_feasibility = 0.0
            
            for path in innovative_paths:
                path_verification = self.verify_idea_feasibility(
                    idea_text=f"创新方案: {path.path_type}: {path.description}",
                    context={
                        'stage': 'innovative_detour',
                        'original_failure': True,
                        'query': user_query
                    }
                )
                
                feasibility = path_verification.get('feasibility_analysis', {}).get('feasibility_score', 0.0)
                
                if feasibility > best_feasibility:
                    best_feasibility = feasibility
                    best_innovative_path = path
                
                # 更新MAB学习（即使是创新路径也要学习）
                self.mab_converger.update_path_performance(
                    path_id=path.path_id,
                    success=feasibility > 0.4,  # 创新路径的成功阈值稍低
                    reward=path_verification.get('reward_score', 0.0)
                )
            
            # 选择最佳创新路径
            if best_innovative_path and best_feasibility > 0.2:
                chosen_path = best_innovative_path
                logger.info(f"✅ 选择创新路径: {chosen_path.path_type} (可行性: {best_feasibility:.2f})")
            else:
                # 最后的应急方案
                logger.warning("🆘 所有创新尝试失败，使用保守应急方案")
                chosen_path = self._create_conservative_emergency_path(user_query)
            
            # 构建决策结果
            mab_decision = {
                'chosen_path': chosen_path,
                'available_paths': original_paths + innovative_paths,
                'innovative_paths': innovative_paths,
                'failure_patterns': failure_patterns,
                'innovative_seed': innovative_seed if 'innovative_seed' in locals() else None,
                'best_innovative_feasibility': best_feasibility,
                'detour_success': best_feasibility > 0.2
            }
            
            # 记录智能绕道统计
            self.aha_moment_stats['total_aha_moments'] += 1
            self.aha_moment_stats['aha_decision_history'].append({
                'timestamp': time.time(),
                'type': 'intelligent_detour',
                'trigger_reason': 'all_paths_verification_failed',
                'innovative_paths_count': len(innovative_paths),
                'best_feasibility': best_feasibility,
                'success': best_feasibility > 0.2
            })
            
            return chosen_path, mab_decision
            
        except Exception as e:
            logger.error(f"❌ 智能绕道思考失败: {e}")
            # 返回最保守的应急方案
            emergency_path = self._create_conservative_emergency_path(user_query)
            emergency_decision = {
                'chosen_path': emergency_path,
                'available_paths': original_paths,
                'detour_error': str(e),
                'emergency_fallback': True
            }
            return emergency_path, emergency_decision
    
    def _analyze_verification_failures(self, verified_paths: List[Dict]) -> Dict[str, Any]:
        """分析验证失败的模式"""
        if not verified_paths:
            return {'error': 'no_paths_to_analyze'}
        
        # 收集失败原因
        low_feasibility_paths = [vp for vp in verified_paths if vp['feasibility_score'] < 0.3]
        common_issues = []
        
        # 分析共同的失败模式
        for vp in low_feasibility_paths:
            verification_result = vp.get('verification_result', {})
            risk_analysis = verification_result.get('feasibility_analysis', {}).get('risk_analysis', {})
            key_risks = risk_analysis.get('key_risks', [])
            common_issues.extend(key_risks)
        
        # 统计最常见的问题
        from collections import Counter
        issue_counts = Counter(common_issues)
        
        return {
            'total_failed_paths': len(low_feasibility_paths),
            'average_feasibility': sum(vp['feasibility_score'] for vp in verified_paths) / len(verified_paths),
            'common_failure_reasons': dict(issue_counts.most_common(3)),
            'risk_patterns': [issue for issue, count in issue_counts.most_common(3)]
        }
    
    def _generate_innovative_thinking_seed(self, user_query: str, original_seed: str, 
                                         failure_patterns: Dict) -> str:
        """基于失败分析生成创新思维种子"""
        if not self.llm_client:
            return self._heuristic_innovative_seed(user_query, failure_patterns)
        
        try:
            innovation_prompt = f"""
基于失败分析，重新思考问题的解决方案：

🎯 **原始问题**: {user_query}

🌱 **原始思维种子**: {original_seed[:200]}...

❌ **验证失败模式**:
- 失败路径数: {failure_patterns.get('total_failed_paths', 0)}
- 平均可行性: {failure_patterns.get('average_feasibility', 0):.2f}
- 主要风险: {failure_patterns.get('risk_patterns', [])}

💡 **创新思考要求**:
1. 避开已验证的失败模式
2. 从不同角度重新定义问题
3. 考虑非常规、创新性的解决路径
4. 降低已识别的风险因素

请生成一个全新的创新思维种子，避开失败模式，提供创新视角：
"""
            
            # 使用正确的LLM调用接口
            if self.llm_manager:
                llm_result = self.llm_manager.chat_completion(innovation_prompt, temperature=0.8)
                if llm_result.success:
                    innovative_response = llm_result.content
                else:
                    raise Exception(f"LLM调用失败: {llm_result.error_message}")
            elif self.llm_client:
                innovative_response = self.llm_client.call_api(innovation_prompt, temperature=0.8)
            else:
                raise Exception("没有可用的LLM客户端")
            
            # 简单提取响应内容
            if len(innovative_response) > 50:
                return innovative_response
            else:
                return self._heuristic_innovative_seed(user_query, failure_patterns)
                
        except Exception as e:
            logger.warning(f"⚠️ LLM创新种子生成失败: {e}")
            return self._heuristic_innovative_seed(user_query, failure_patterns)
    
    def _heuristic_innovative_seed(self, user_query: str, failure_patterns: Dict) -> str:
        """启发式创新种子生成"""
        innovation_approaches = [
            f"重新定义问题角度: {user_query}",
            f"逆向思维解决: {user_query}",
            f"跨领域借鉴方法: {user_query}",
            f"简化到核心需求: {user_query}",
            f"分阶段渐进解决: {user_query}"
        ]
        
        import random
        return random.choice(innovation_approaches)
    
    def _create_emergency_innovative_paths(self, user_query: str, failure_patterns: Dict) -> List:
        """创建应急创新路径"""
        from .data_structures import ReasoningPath
        
        emergency_paths = [
            ReasoningPath(
                path_id="emergency_innovative_1",
                path_type="问题重定义型",
                description="重新定义问题的核心需求，寻找更简单的解决方案",
                prompt_template="让我们重新审视这个问题的本质需求：{task}"
            ),
            ReasoningPath(
                path_id="emergency_innovative_2", 
                path_type="分步简化型",
                description="将复杂问题分解为多个简单步骤",
                prompt_template="将复杂任务拆分为可管理的子任务：{task}"
            ),
            ReasoningPath(
                path_id="emergency_innovative_3",
                path_type="替代方案型", 
                description="寻找实现相同目标的替代方法",
                prompt_template="探索达成目标的不同路径：{task}"
            )
        ]
        
        return emergency_paths
    
    # ==================== 多LLM管理方法 ====================
    
    def switch_llm_provider(self, provider_name: str) -> bool:
        """
        切换LLM提供商
        
        Args:
            provider_name: 提供商名称
            
        Returns:
            bool: 是否切换成功
        """
        if not self.llm_manager:
            logger.warning("⚠️ LLM管理器未初始化，无法切换提供商")
            return False
        
        success = self.llm_manager.switch_primary_provider(provider_name)
        if success:
            logger.info(f"🔄 已切换到LLM提供商: {provider_name}")
        else:
            logger.error(f"❌ 切换LLM提供商失败: {provider_name}")
        
        return success
    
    def get_llm_provider_status(self) -> Dict[str, Any]:
        """
        获取LLM提供商状态
        
        Returns:
            Dict[str, Any]: 提供商状态信息
        """
        if not self.llm_manager:
            return {
                'initialized': False,
                'error': 'LLM管理器未初始化',
                'fallback_mode': True,
                'available_providers': []
            }
        
        return self.llm_manager.get_provider_status()
    
    def get_available_llm_models(self, provider_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        获取可用的LLM模型
        
        Args:
            provider_name: 提供商名称（可选）
            
        Returns:
            Dict[str, List[str]]: 提供商和对应的模型列表
        """
        if not self.llm_manager:
            return {"error": "LLM管理器未初始化"}
        
        return self.llm_manager.get_available_models(provider_name)
    
    def run_llm_health_check(self, force: bool = False) -> Dict[str, bool]:
        """
        运行LLM提供商健康检查
        
        Args:
            force: 是否强制检查
            
        Returns:
            Dict[str, bool]: 各提供商的健康状态
        """
        if not self.llm_manager:
            return {"error": "LLM管理器未初始化"}
        
        return self.llm_manager.health_check(force)
    
    def get_llm_cost_summary(self) -> Dict[str, Any]:
        """
        获取LLM使用成本总结
        
        Returns:
            Dict[str, Any]: 成本总结信息
        """
        if not self.llm_manager:
            return {"error": "LLM管理器未初始化"}
        
        status = self.llm_manager.get_provider_status()
        cost_data = status.get('stats', {}).get('cost_tracking', {})
        
        total_cost = sum(cost_data.values())
        
        return {
            'total_cost_usd': total_cost,
            'cost_by_provider': dict(cost_data),
            'total_requests': status.get('stats', {}).get('total_requests', 0),
            'successful_requests': status.get('stats', {}).get('successful_requests', 0),
            'fallback_count': status.get('stats', {}).get('fallback_count', 0)
        }
    
    def _create_conservative_emergency_path(self, user_query: str):
        """创建保守的应急路径"""
        from .data_structures import ReasoningPath
        
        return ReasoningPath(
            path_id="conservative_emergency",
            path_type="保守应急型",
            description="使用最基础、最可靠的方法处理问题",
            prompt_template="使用最直接、最基础的方法处理：{task}"
        )
