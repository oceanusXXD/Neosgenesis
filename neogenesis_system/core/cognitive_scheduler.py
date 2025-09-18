#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认知调度器 - Cognitive Scheduler
赋予 Agent "空闲"概念的智能后台调度系统

这个模块实现了从"被动应激"到"主动认知"的范式转换：
- 空闲状态检测：监控系统状态，识别任务间隙
- 后台认知循环：在空闲期间启动主动反思和创想过程  
- 认知状态管理：协调任务驱动模式与自我驱动模式的切换
- 知识沉淀触发：激活任务回溯引擎和主动创想模块

核心理念：让AI从"任务奴隶"升级为"自主思考者"
"""

import time
import threading
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty
import json

from ..shared.state_manager import StateManager, TaskPhase, GoalStatus
from .retrospection_engine import TaskRetrospectionEngine, RetrospectionStrategy
from ..providers.knowledge_explorer import KnowledgeExplorer, ExplorationStrategy

logger = logging.getLogger(__name__)


class CognitiveMode(Enum):
    """认知模式枚举"""
    TASK_DRIVEN = "task_driven"        # 任务驱动模式（正常工作状态）
    COGNITIVE_IDLE = "cognitive_idle"  # 认知空闲模式（浅层后台思考）
    DEEP_REFLECTION = "deep_reflection" # 深度反思模式（深度复盘分析）
    CREATIVE_IDEATION = "creative_ideation" # 主动创想模式（突破性思考）
    KNOWLEDGE_EXPLORATION = "knowledge_exploration" # 知识探索模式（主动探索外部世界）


@dataclass
class CognitiveTask:
    """认知任务数据结构"""
    task_id: str
    task_type: str  # "retrospection", "ideation", "knowledge_synthesis", "knowledge_exploration"
    priority: int   # 1-10, 10为最高优先级
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    estimated_duration: float = 30.0  # 预估执行时间(秒)
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"{self.task_type}_{int(time.time() * 1000)}"


class CognitiveScheduler:
    """
    🧠 认知调度器 - Agent的"内在独白循环"
    
    核心职责：
    1. 空闲状态检测 - 判断何时可以进行后台认知
    2. 认知任务调度 - 管理回溯、创想等认知任务队列
    3. 模式切换控制 - 协调任务驱动与自我驱动模式
    4. 认知资源管理 - 合理分配计算资源给后台思考
    
    设计原则：
    - 非侵入性：不影响正常任务执行
    - 可配置性：支持灵活的调度策略
    - 渐进式：从简单空闲检测到复杂认知调度
    """
    
    def __init__(self, 
                 state_manager: StateManager,
                 llm_client=None,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化认知调度器
        
        Args:
            state_manager: 状态管理器实例
            llm_client: LLM客户端（用于认知任务）
            config: 调度器配置
        """
        self.state_manager = state_manager
        self.llm_client = llm_client
        
        # 配置参数
        self.config = {
            # 空闲检测配置
            "idle_detection": {
                "min_idle_duration": 10.0,      # 最小空闲时间(秒)
                "max_idle_duration": 300.0,     # 最大空闲时间(秒)  
                "task_completion_buffer": 5.0,   # 任务完成后缓冲时间
                "check_interval": 2.0            # 状态检查间隔
            },
            
            # 认知任务配置
            "cognitive_tasks": {
                "retrospection_interval": 60.0,     # 回溯任务间隔
                "ideation_interval": 120.0,          # 创想任务间隔
                "exploration_interval": 180.0,       # 知识探索任务间隔
                "max_concurrent_tasks": 2,           # 最大并发认知任务数
                "task_timeout": 180.0                # 认知任务超时时间
            },
            
            # 🌐 知识探索配置 - 双轨探索系统
            "knowledge_exploration": {
                # 通用配置
                "max_exploration_depth": 3,         # 最大探索深度
                "enable_web_search": True,          # 启用网络搜索
                "enable_trend_analysis": True,      # 启用趋势分析
                "knowledge_threshold": 0.7,         # 知识质量阈值
                
                # 自主探索配置
                "exploration_strategies": [
                    "domain_expansion",      # 领域扩展
                    "trend_monitoring",      # 趋势监控
                    "gap_analysis",         # 知识缺口分析
                    "cross_domain_learning" # 跨域学习
                ],
                "exploration_timeout": 120.0,       # 自主探索超时
                
                # 🎯 用户指令驱动探索配置
                "user_directed_timeout": 60.0,      # 用户指令探索超时（更短）
                "user_directed_strategies": [
                    "expert_knowledge",      # 专家知识获取
                    "domain_expansion",      # 领域扩展
                    "competitive_intelligence", # 竞争情报
                    "trend_monitoring"       # 趋势监控
                ],
                
                # 🎯 双轨平衡机制
                "dual_track_config": {
                    "user_directed_priority": 10,   # 用户指令最高优先级
                    "autonomous_priority": 3,       # 自主探索较低优先级
                    "max_concurrent_user_tasks": 3, # 最大并发用户任务
                    "max_concurrent_autonomous": 1, # 最大并发自主任务
                    "user_task_preemption": True,   # 允许用户任务抢占
                    "balance_threshold": 0.8         # 平衡阈值
                }
            },
            
            # 资源管理配置
            "resource_limits": {
                "max_cpu_usage": 0.3,               # 最大CPU使用率
                "max_memory_usage": 0.2,             # 最大内存使用率
                "enable_adaptive_scheduling": True    # 启用自适应调度
            }
        }
        
        # 合并用户配置
        if config:
            self._merge_config(self.config, config)
        
        # 核心状态
        self.current_mode = CognitiveMode.TASK_DRIVEN
        self.is_running = False
        self.is_idle = False
        self.last_activity_time = time.time()
        self.last_task_completion_time = None
        
        # 认知任务管理
        self.cognitive_task_queue = Queue()
        self.active_cognitive_tasks: Dict[str, CognitiveTask] = {}
        self.cognitive_history: List[Dict[str, Any]] = []
        
        # 🔍 任务回溯引擎 - 新增功能
        self.retrospection_engine = None
        if state_manager and llm_client:
            try:
                # 创建回溯引擎需要PathGenerator和MABConverger
                # 这些通常在上层的Agent或Planner中可用
                self.retrospection_engine = TaskRetrospectionEngine(
                    llm_client=llm_client,
                    config=config.get('retrospection_config', {}) if config else {}
                )
                logger.info("🔍 任务回溯引擎已集成 - 深度记忆分析能力就绪")
            except Exception as e:
                logger.warning(f"⚠️ 任务回溯引擎初始化失败: {e}")
                logger.info("💡 将使用基础回溯分析功能")
        
        # 🌐 知识探勘器 - 新增核心模块
        self.knowledge_explorer = None
        if llm_client:
            try:
                explorer_config = config.get('knowledge_exploration', {}) if config else {}
                self.knowledge_explorer = KnowledgeExplorer(
                    llm_client=llm_client,
                    web_search_client=None,  # 可以从上层传入
                    config=explorer_config
                )
                logger.info("🌐 知识探勘器已集成 - 外部智慧连接器就绪")
            except Exception as e:
                logger.warning(f"⚠️ 知识探勘器初始化失败: {e}")
                logger.info("💡 将使用基础探索分析功能")
        
        # 线程管理
        self.scheduler_thread: Optional[threading.Thread] = None
        self.cognitive_workers: List[threading.Thread] = []
        self.stop_event = threading.Event()
        
        # 性能统计
        self.stats = {
            "total_idle_periods": 0,
            "total_idle_time": 0.0,
            "cognitive_tasks_completed": 0,
            "retrospection_sessions": 0,
            "ideation_sessions": 0,
            "knowledge_synthesis_sessions": 0,
            "knowledge_exploration_sessions": 0  # 新增：知识探索会话数
        }
        
        # 🌐 知识探索相关状态 - 新增
        self.exploration_history: List[Dict[str, Any]] = []
        self.last_exploration_time = 0.0  # 上次探索时间
        self.exploration_topics_cache: List[str] = []  # 探索主题缓存
        self.discovered_knowledge: Dict[str, Any] = {}  # 发现的新知识
        
        # 注册状态变化监听器
        self.state_manager.add_state_change_listener(self._on_state_change)
        
        logger.info("🧠 CognitiveScheduler 初始化完成")
        logger.info(f"   空闲检测间隔: {self.config['idle_detection']['check_interval']}s")
        logger.info(f"   最小空闲触发时间: {self.config['idle_detection']['min_idle_duration']}s")
        logger.info(f"   回溯引擎: {'已集成' if self.retrospection_engine else '未集成'}")
        logger.info(f"   知识探勘器: {'已集成' if self.knowledge_explorer else '未集成'}")
        logger.info("💡 主动认知模式已就绪 - 从'任务奴隶'升级为'自主思考者'")
    
    def start(self):
        """启动认知调度器"""
        if self.is_running:
            logger.warning("⚠️ 认知调度器已经在运行")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        # 启动主调度线程
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_main_loop,
            name="CognitiveScheduler",
            daemon=True
        )
        self.scheduler_thread.start()
        
        # 启动认知工作线程
        max_workers = self.config["cognitive_tasks"]["max_concurrent_tasks"]
        for i in range(max_workers):
            worker = threading.Thread(
                target=self._cognitive_worker_loop,
                name=f"CognitiveWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.cognitive_workers.append(worker)
        
        logger.info("🚀 认知调度器已启动")
        logger.info(f"   主调度线程: {self.scheduler_thread.name}")
        logger.info(f"   认知工作线程数: {len(self.cognitive_workers)}")
    
    def stop(self):
        """停止认知调度器"""
        if not self.is_running:
            logger.warning("⚠️ 认知调度器未在运行")
            return
        
        logger.info("🛑 正在停止认知调度器...")
        
        self.is_running = False
        self.stop_event.set()
        
        # 等待主调度线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5.0)
        
        # 等待工作线程结束
        for worker in self.cognitive_workers:
            if worker.is_alive():
                worker.join(timeout=5.0)
        
        logger.info("✅ 认知调度器已停止")
        self._log_final_stats()
    
    def _scheduler_main_loop(self):
        """主调度循环 - 监控空闲状态并触发认知任务"""
        logger.info("🔄 认知调度主循环已启动")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # 检测当前状态
                self._detect_idle_state()
                
                # 根据状态执行相应逻辑
                if self.is_idle:
                    self._handle_idle_state()
                else:
                    self._handle_active_state()
                
                # 调度认知任务
                self._schedule_cognitive_tasks()
                
                # 清理过期任务
                self._cleanup_expired_tasks()
                
                # 等待下一个检查周期
                check_interval = self.config["idle_detection"]["check_interval"]
                self.stop_event.wait(check_interval)
                
            except Exception as e:
                logger.error(f"❌ 认知调度循环出错: {e}")
                time.sleep(5.0)  # 错误恢复延迟
        
        logger.info("🔚 认知调度主循环已结束")
    
    def _detect_idle_state(self):
        """检测系统空闲状态"""
        current_time = time.time()
        current_state = self.state_manager.get_current_state()
        
        # 获取状态信息
        current_phase = current_state.get("current_phase", "initialization")
        current_goal = current_state.get("current_goal", {})
        goal_status = current_goal.get("status", "pending")
        
        # 判断是否处于空闲状态
        is_task_completed = (
            current_phase == "completion" or 
            goal_status in ["achieved", "failed"]
        )
        
        # 计算空闲时间
        if is_task_completed and self.last_task_completion_time is None:
            self.last_task_completion_time = current_time
        
        idle_duration = 0.0
        if self.last_task_completion_time:
            idle_duration = current_time - self.last_task_completion_time
        
        # 更新空闲状态
        min_idle_duration = self.config["idle_detection"]["min_idle_duration"]
        was_idle = self.is_idle
        
        self.is_idle = (
            is_task_completed and 
            idle_duration >= min_idle_duration
        )
        
        # 空闲状态变化时记录日志
        if self.is_idle and not was_idle:
            self._enter_idle_state(idle_duration)
        elif not self.is_idle and was_idle:
            self._exit_idle_state()
    
    def _enter_idle_state(self, idle_duration: float):
        """进入空闲状态"""
        self.current_mode = CognitiveMode.COGNITIVE_IDLE
        self.stats["total_idle_periods"] += 1
        
        logger.info("😴 系统进入认知空闲状态")
        logger.info(f"   空闲时长: {idle_duration:.1f}s")
        logger.info("💭 开始主动认知模式...")
        
        # 立即安排一个回溯任务
        self._schedule_retrospection_task()
    
    def _exit_idle_state(self):
        """退出空闲状态"""
        idle_start_time = self.last_task_completion_time
        if idle_start_time:
            idle_duration = time.time() - idle_start_time
            self.stats["total_idle_time"] += idle_duration
            
            logger.info("🔄 系统退出空闲状态")
            logger.info(f"   本次空闲时长: {idle_duration:.1f}s")
        
        self.current_mode = CognitiveMode.TASK_DRIVEN
        self.last_task_completion_time = None
        
        # 暂停低优先级认知任务
        self._pause_low_priority_cognitive_tasks()
    
    def _handle_idle_state(self):
        """处理空闲状态逻辑"""
        current_time = time.time()
        
        # 检查是否需要安排创想任务
        ideation_interval = self.config["cognitive_tasks"]["ideation_interval"]
        if (current_time - self.last_activity_time) >= ideation_interval:
            if not self._has_active_task_type("ideation"):
                self._schedule_ideation_task()
        
        # 🌐 新增：检查是否需要安排知识探索任务
        exploration_interval = self.config["cognitive_tasks"]["exploration_interval"]
        if (current_time - self.last_exploration_time) >= exploration_interval:
            if not self._has_active_task_type("knowledge_exploration"):
                self._schedule_knowledge_exploration_task()
        
        # 检查是否需要知识综合
        if self._should_trigger_knowledge_synthesis():
            self._schedule_knowledge_synthesis_task()
    
    def _handle_active_state(self):
        """处理活跃状态逻辑"""
        self.last_activity_time = time.time()
    
    def _schedule_cognitive_tasks(self):
        """调度认知任务"""
        # 这里是任务调度的核心逻辑
        # 当前只是基础框架，后续会扩展
        pass
    
    def _schedule_retrospection_task(self):
        """安排回溯任务"""
        task = CognitiveTask(
            task_id="",
            task_type="retrospection", 
            priority=7,
            context={
                "session_state": self.state_manager.get_current_state(),
                "trigger_reason": "idle_detection"
            },
            estimated_duration=45.0
        )
        
        self.cognitive_task_queue.put(task)
        logger.info("📚 已安排任务回溯分析")
    
    def _schedule_ideation_task(self):
        """安排创想任务"""
        task = CognitiveTask(
            task_id="",
            task_type="ideation",
            priority=5, 
            context={
                "session_insights": self._extract_session_insights(),
                "trigger_reason": "periodic_ideation"
            },
            estimated_duration=60.0
        )
        
        self.cognitive_task_queue.put(task)
        logger.info("💡 已安排主动创想任务")
    
    def _schedule_knowledge_synthesis_task(self):
        """安排知识综合任务"""
        task = CognitiveTask(
            task_id="",
            task_type="knowledge_synthesis",
            priority=6,
            context={
                "cognitive_history": self.cognitive_history[-10:],  # 最近10次认知结果
                "trigger_reason": "knowledge_accumulation"
            },
            estimated_duration=90.0
        )
        
        self.cognitive_task_queue.put(task)
        logger.info("🧩 已安排知识综合任务")
    
    def _schedule_knowledge_exploration_task(self, user_query: Optional[str] = None, user_context: Optional[Dict[str, Any]] = None):
        """🌐 安排知识探索任务 - 双轨探索目标系统
        
        Args:
            user_query: 用户查询，如果提供则创建用户指令驱动的高优先级探索任务
            user_context: 用户上下文信息（可选）
        """
        current_time = time.time()
        
        # 🎯 双轨探索模式判断
        if user_query:
            # 用户指令驱动的高优先级探索模式
            logger.info(f"🎯 启动用户指令驱动探索模式: {user_query[:50]}...")
            
            task = CognitiveTask(
                task_id="",
                task_type="knowledge_exploration",
                priority=10,  # 最高优先级 - 用户指令驱动
                context={
                    "exploration_mode": "user_directed",
                    "user_query": user_query,
                    "user_context": user_context or {},
                    "trigger_reason": "user_instruction",
                    "immediate_priority": True,
                    # 基于用户查询生成的探索上下文
                    "exploration_opportunities": self._analyze_user_query_exploration_opportunities(user_query, user_context),
                    "exploration_strategies": self._select_user_directed_strategies(user_query),
                    "session_insights": self._extract_session_insights(),
                    "current_knowledge_gaps": self._identify_knowledge_gaps(),
                    "created_at": current_time
                },
                estimated_duration=self.config["knowledge_exploration"]["user_directed_timeout"]
            )
            
            # 🚀 立即插入到队列前端，确保优先执行
            self._insert_high_priority_task(task)
            
            logger.info("🎯 用户指令驱动探索任务已创建 - 最高优先级")
            logger.info(f"   用户查询: {user_query[:100]}...")
            logger.info(f"   探索策略: {task.context.get('exploration_strategies', [])[:2]}")
            
        else:
            # 系统自主探索的低优先级模式（原有逻辑）
            logger.info("🔄 启动系统自主探索模式")
            
            # 分析当前知识状态，确定探索方向
            exploration_context = self._analyze_exploration_opportunities()
            
            task = CognitiveTask(
                task_id="",
                task_type="knowledge_exploration",
                priority=3,  # 较低优先级 - 系统自主探索
                context={
                    "exploration_mode": "autonomous",
                    "exploration_opportunities": exploration_context,
                    "session_insights": self._extract_session_insights(),
                    "current_knowledge_gaps": self._identify_knowledge_gaps(),
                    "exploration_strategies": self.config["knowledge_exploration"]["exploration_strategies"],
                    "trigger_reason": "proactive_exploration",
                    "immediate_priority": False,
                    "created_at": current_time
                },
                estimated_duration=self.config["knowledge_exploration"]["exploration_timeout"]
            )
            
            self.cognitive_task_queue.put(task)
            
            logger.info("🔄 自主探索任务已安排 - 常规优先级")
            logger.info(f"   探索机会数量: {len(exploration_context)}")
            logger.info(f"   探索策略: {task.context['exploration_strategies'][:2]}...")
        
        self.last_exploration_time = current_time
    
    def _analyze_user_query_exploration_opportunities(self, user_query: str, user_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """🎯 分析用户查询中的探索机会 - 用户指令驱动模式"""
        opportunities = []
        
        try:
            # 基础关键词提取
            query_keywords = self._extract_query_keywords(user_query)
            
            # 识别用户查询中的领域和主题
            query_domains = self._identify_query_domains(user_query)
            
            # 构建针对用户查询的探索机会
            for domain in query_domains:
                opportunities.append({
                    "type": "user_query_domain",
                    "domain": domain,
                    "query": user_query,
                    "keywords": query_keywords,
                    "priority": "high",
                    "exploration_focus": f"深入了解用户关于'{domain}'的具体需求",
                    "search_terms": self._generate_user_focused_search_terms(user_query, domain)
                })
            
            # 添加相关主题探索
            if len(opportunities) < 3:  # 确保有足够的探索方向
                opportunities.extend([
                    {
                        "type": "related_topics",
                        "query": user_query,
                        "keywords": query_keywords,
                        "priority": "medium",
                        "exploration_focus": f"寻找与'{user_query[:30]}...'相关的信息和案例",
                        "search_terms": query_keywords[:5]
                    }
                ])
            
            logger.debug(f"🎯 用户查询探索机会分析完成: {len(opportunities)} 个机会")
            
        except Exception as e:
            logger.warning(f"⚠️ 用户查询探索机会分析失败: {e}")
            # 提供基础的探索机会
            opportunities.append({
                "type": "basic_user_query",
                "query": user_query,
                "priority": "high",
                "exploration_focus": f"基于用户查询的基础信息收集"
            })
        
        return opportunities
    
    def _select_user_directed_strategies(self, user_query: str) -> List[str]:
        """🎯 为用户指令选择最适合的探索策略"""
        query_lower = user_query.lower()
        strategies = []
        
        # 基于查询内容选择策略
        if any(keyword in query_lower for keyword in ['最新', '趋势', '发展', '动态', 'latest', 'trend']):
            strategies.extend(['trend_monitoring', 'domain_expansion'])
        
        if any(keyword in query_lower for keyword in ['如何', '方法', '解决', 'how', 'solution', 'method']):
            strategies.extend(['expert_knowledge', 'gap_analysis'])
        
        if any(keyword in query_lower for keyword in ['比较', '对比', 'compare', 'versus', 'vs']):
            strategies.extend(['competitive_intelligence', 'cross_domain_learning'])
        
        if any(keyword in query_lower for keyword in ['创新', '新颖', 'innovative', 'creative', 'novel']):
            strategies.extend(['serendipity_discovery', 'cross_domain_learning'])
        
        # 默认策略
        if not strategies:
            strategies = ['domain_expansion', 'expert_knowledge']
        
        # 限制策略数量，避免过度探索
        return strategies[:3]
    
    def _insert_high_priority_task(self, task: CognitiveTask):
        """🚀 插入高优先级任务到队列前端"""
        try:
            # 由于Queue不支持优先级插入，我们使用一个临时列表来重组队列
            temp_tasks = []
            
            # 先取出所有现有任务
            while not self.cognitive_task_queue.empty():
                try:
                    existing_task = self.cognitive_task_queue.get_nowait()
                    temp_tasks.append(existing_task)
                except Empty:
                    break
            
            # 首先插入高优先级任务
            self.cognitive_task_queue.put(task)
            
            # 然后按优先级重新插入其他任务
            temp_tasks.sort(key=lambda t: t.priority, reverse=True)
            for existing_task in temp_tasks:
                self.cognitive_task_queue.put(existing_task)
            
            logger.debug(f"🚀 高优先级任务已插入队列前端: {task.task_id}")
            
        except Exception as e:
            logger.error(f"❌ 插入高优先级任务失败: {e}")
            # 回退到普通插入
            self.cognitive_task_queue.put(task)
    
    def _extract_query_keywords(self, user_query: str) -> List[str]:
        """提取用户查询中的关键词"""
        import re
        
        # 简单的关键词提取（可以后续用更高级的NLP方法替换）
        words = re.findall(r'\b\w+\b', user_query.lower())
        
        # 过滤停用词和短词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '然而', '因此', 'the', 'is', 'in', 'and', 'or', 'but', 'how', 'what', 'where', 'when', 'why'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords[:8]  # 返回前8个关键词
    
    def _identify_query_domains(self, user_query: str) -> List[str]:
        """识别用户查询所属的领域"""
        query_lower = user_query.lower()
        domains = []
        
        domain_keywords = {
            "技术": ['api', '算法', '编程', '代码', '系统', '架构', '数据库', '机器学习', 'ai', 'python', 'java'],
            "商业": ['市场', '营销', '销售', '商业', '管理', '策略', '投资', '创业', '公司'],
            "学术": ['研究', '论文', '理论', '学术', '科学', '实验', '分析', '方法'],
            "健康": ['健康', '医疗', '疾病', '治疗', '保健', '医学', '药物'],
            "教育": ['学习', '教育', '培训', '课程', '知识', '技能', '学校'],
            "生活": ['生活', '日常', '家居', '旅行', '美食', '娱乐', '休闲']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                domains.append(domain)
        
        # 如果没有匹配到特定领域，返回通用领域
        if not domains:
            domains = ["通用"]
        
        return domains[:2]  # 最多返回2个主要领域
    
    def _generate_user_focused_search_terms(self, user_query: str, domain: str) -> List[str]:
        """为用户查询生成针对性的搜索词条"""
        base_terms = self._extract_query_keywords(user_query)
        
        # 根据领域添加相关的搜索增强词
        domain_enhancers = {
            "技术": ["最佳实践", "教程", "案例", "解决方案"],
            "商业": ["案例研究", "市场分析", "成功案例", "策略"],
            "学术": ["最新研究", "文献综述", "方法论", "实证分析"],
            "健康": ["专业建议", "临床研究", "预防方法", "治疗方案"],
            "教育": ["学习资源", "教学方法", "实践指南", "技能培养"],
            "生活": ["实用指南", "经验分享", "推荐", "评价"]
        }
        
        enhancers = domain_enhancers.get(domain, ["详细信息", "指南", "建议"])
        
        # 组合生成搜索词条
        search_terms = base_terms[:3]  # 基础关键词
        search_terms.extend(enhancers[:2])  # 增强词
        
        return search_terms
    
    def schedule_user_directed_exploration(self, user_query: str, user_context: Optional[Dict[str, Any]] = None):
        """🎯 公共接口：为用户指令安排高优先级探索任务"""
        logger.info(f"🎯 接收到用户指令驱动的探索请求: {user_query[:50]}...")
        
        # 记录用户指令统计
        if "user_directed_explorations" not in self.stats:
            self.stats["user_directed_explorations"] = 0
        self.stats["user_directed_explorations"] += 1
        
        # 调用内部方法创建探索任务
        self._schedule_knowledge_exploration_task(user_query=user_query, user_context=user_context)
        
        logger.info("🎯 用户指令驱动探索任务已安排完成")
    
    def _cognitive_worker_loop(self):
        """认知工作线程循环"""
        worker_name = threading.current_thread().name
        logger.info(f"🔨 {worker_name} 认知工作线程已启动")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # 获取认知任务（阻塞等待，超时5秒）
                task = self.cognitive_task_queue.get(timeout=5.0)
                
                # 执行认知任务
                self._execute_cognitive_task(task, worker_name)
                
                # 标记任务完成
                self.cognitive_task_queue.task_done()
                
            except Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                logger.error(f"❌ {worker_name} 执行认知任务出错: {e}")
        
        logger.info(f"🔚 {worker_name} 认知工作线程已结束")
    
    def _execute_cognitive_task(self, task: CognitiveTask, worker_name: str):
        """执行具体的认知任务"""
        start_time = time.time()
        
        try:
            logger.info(f"🧠 {worker_name} 开始执行认知任务: {task.task_type}")
            
            # 记录活跃任务
            self.active_cognitive_tasks[task.task_id] = task
            
            # 根据任务类型执行不同逻辑
            result = {}
            if task.task_type == "retrospection":
                result = self._execute_retrospection_task(task)
            elif task.task_type == "ideation":  
                result = self._execute_ideation_task(task)
            elif task.task_type == "knowledge_synthesis":
                result = self._execute_knowledge_synthesis_task(task)
            elif task.task_type == "knowledge_exploration":  # 🌐 新增
                result = self._execute_knowledge_exploration_task(task)
            else:
                logger.warning(f"⚠️ 未知认知任务类型: {task.task_type}")
                return
            
            # 记录认知结果
            execution_time = time.time() - start_time
            cognitive_result = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "result": result,
                "execution_time": execution_time,
                "worker_name": worker_name,
                "timestamp": time.time()
            }
            
            self.cognitive_history.append(cognitive_result)
            self.stats["cognitive_tasks_completed"] += 1
            
            logger.info(f"✅ {worker_name} 完成认知任务 {task.task_type} (耗时: {execution_time:.1f}s)")
            
        except Exception as e:
            logger.error(f"❌ {worker_name} 认知任务执行失败: {e}")
        finally:
            # 清理活跃任务记录
            self.active_cognitive_tasks.pop(task.task_id, None)
    
    def _execute_retrospection_task(self, task: CognitiveTask) -> Dict[str, Any]:
        """执行回溯任务 - 分析过往决策模式和经验教训"""
        self.stats["retrospection_sessions"] += 1
        
        # 🔍 使用专业回溯引擎进行深度分析
        if self.retrospection_engine:
            try:
                logger.info("🔍 启动专业回溯引擎进行深度分析...")
                
                # 从任务上下文获取触发原因，选择合适的回溯策略
                trigger_reason = task.context.get("trigger_reason", "idle_detection")
                strategy = self._determine_retrospection_strategy(trigger_reason, task.context)
                
                # 执行完整的三阶段回溯流程
                retrospection_result = self.retrospection_engine.perform_retrospection(
                    state_manager=self.state_manager,
                    strategy=strategy
                )
                
                # 转换为认知调度器的分析格式
                analysis = self._convert_retrospection_result(retrospection_result)
                
                logger.info("✅ 专业回溯引擎分析完成")
                logger.info(f"   LLM维度: {len(retrospection_result.llm_dimensions)} 个")
                logger.info(f"   创意路径: {len(retrospection_result.aha_moment_paths)} 条")
                logger.info(f"   沉淀策略: {len(retrospection_result.assimilated_strategies)} 个")
                
                return analysis
                
            except Exception as e:
                logger.error(f"❌ 专业回溯引擎执行失败: {e}")
                logger.info("🔄 回退到基础回溯分析...")
        
        # 基础分析（回退机制）
        session_state = task.context.get("session_state", {})
        conversation_history = session_state.get("conversation", {})
        mab_stats = session_state.get("mab", {})
        
        analysis = {
            "session_insights": {
                "total_turns": conversation_history.get("total_turns", 0),
                "success_patterns": self._identify_success_patterns(session_state),
                "failure_patterns": self._identify_failure_patterns(session_state),
                "decision_efficiency": mab_stats.get("decision_patterns", {})
            },
            "improvement_suggestions": [
                "基础回溯分析完成，建议启用专业回溯引擎获得更深入洞察"
            ],
            "golden_templates": self._extract_golden_decision_templates(session_state)
        }
        
        logger.info("🔍 完成基础任务回溯分析")
        logger.debug(f"   分析见解: {len(analysis['session_insights'])} 项")
        
        return analysis
    
    def _execute_ideation_task(self, task: CognitiveTask) -> Dict[str, Any]:
        """执行创想任务 - 主动产生创新思路和突破性想法"""
        self.stats["ideation_sessions"] += 1
        
        # 获取会话见解
        session_insights = task.context.get("session_insights", {})
        
        # 基础创想（后续会由ProactiveIdeationModule处理）
        ideation_result = {
            "creative_dimensions": [
                "基于历史模式的创新维度",
                "跨领域思维迁移方向", 
                "突破性问题重构角度"
            ],
            "novel_approaches": [
                "待LLMDrivenDimensionCreator在主动模式下生成"
            ],
            "breakthrough_concepts": {
                "concept_seeds": ["创新概念种子1", "创新概念种子2"],
                "application_domains": ["应用领域建议"]
            }
        }
        
        logger.info("💡 完成主动创想分析")
        logger.debug(f"   生成创意维度: {len(ideation_result['creative_dimensions'])} 个")
        
        return ideation_result
    
    def _execute_knowledge_synthesis_task(self, task: CognitiveTask) -> Dict[str, Any]:
        """执行知识综合任务 - 整合和沉淀认知成果"""
        self.stats["knowledge_synthesis_sessions"] += 1
        
        cognitive_history = task.context.get("cognitive_history", [])
        
        # 基础知识综合
        synthesis_result = {
            "synthesized_knowledge": {
                "core_patterns": self._synthesize_core_patterns(cognitive_history),
                "meta_insights": self._extract_meta_insights(cognitive_history), 
                "knowledge_graph": "知识图谱构建将在后续版本实现"
            },
            "actionable_recommendations": [
                "基于综合分析的可执行建议"
            ]
        }
        
        logger.info("🧩 完成知识综合任务")
        
        return synthesis_result
    
    def _execute_knowledge_exploration_task(self, task: CognitiveTask) -> Dict[str, Any]:
        """🌐 执行知识探索任务 - 主动探索外部世界，发现新的思维种子"""
        self.stats["knowledge_exploration_sessions"] += 1
        
        logger.info("🌐 开始知识探索 - 播下探索的种子")
        
        exploration_opportunities = task.context.get("exploration_opportunities", [])
        knowledge_gaps = task.context.get("current_knowledge_gaps", [])
        exploration_strategies = task.context.get("exploration_strategies", [])
        
        # 🌐 使用专业知识探勘器执行探索
        if self.knowledge_explorer:
            try:
                logger.info("🔍 启动专业知识探勘器进行深度探索...")
                
                # 创建探索目标
                targets = self.knowledge_explorer.create_exploration_targets_from_context(task.context)
                
                # 选择探索策略
                strategy = self._map_to_exploration_strategy(exploration_strategies)
                
                # 执行专业探索
                explorer_result = self.knowledge_explorer.explore_knowledge(targets, strategy)
                
                # 转换为认知调度器格式
                exploration_results = self._convert_explorer_result_to_scheduler_format(
                    explorer_result, task.task_id
                )
                
                logger.info("✅ 专业知识探勘器探索完成")
                logger.info(f"   探索质量评分: {explorer_result.quality_score:.2f}")
                logger.info(f"   探索成功率: {explorer_result.success_rate:.2f}")
                
            except Exception as e:
                logger.error(f"❌ 专业知识探勘器执行失败: {e}")
                logger.info("🔄 回退到基础探索分析...")
                exploration_results = self._execute_basic_exploration(task)
        else:
            # 基础探索（回退机制）
            logger.info("💡 使用基础探索分析功能...")
            exploration_results = self._execute_basic_exploration(task)
        
        # 更新探索历史和缓存
        self._update_exploration_caches(exploration_results)
        
        # 将发现的知识加入认知飞轮
        self._integrate_discovered_knowledge_to_flywheel(exploration_results)
        
        logger.info("🌐 知识探索完成")
        logger.info(f"   发现新知识项: {len(exploration_results['discovered_knowledge'])}")
        logger.info(f"   生成思维种子: {len(exploration_results['generated_thinking_seeds'])}")
        logger.info(f"   识别趋势数量: {len(exploration_results['identified_trends'])}")
        logger.info(f"   跨域连接数量: {len(exploration_results['cross_domain_connections'])}")
        
        return exploration_results
    
    def _execute_basic_exploration(self, task: CognitiveTask) -> Dict[str, Any]:
        """基础探索实现（回退机制）"""
        exploration_opportunities = task.context.get("exploration_opportunities", [])
        knowledge_gaps = task.context.get("current_knowledge_gaps", [])
        exploration_strategies = task.context.get("exploration_strategies", [])
        
        # 基础探索实现
        exploration_results = {
            "exploration_metadata": {
                "exploration_session_id": task.task_id,
                "strategies_used": exploration_strategies,
                "opportunities_explored": len(exploration_opportunities),
                "gaps_addressed": len(knowledge_gaps),
                "execution_mode": "basic_exploration"
            },
            
            # 探索发现的新知识
            "discovered_knowledge": self._discover_new_knowledge(
                exploration_opportunities, 
                knowledge_gaps,
                exploration_strategies
            ),
            
            # 生成的思维种子
            "generated_thinking_seeds": self._generate_exploration_based_seeds(
                exploration_opportunities,
                knowledge_gaps
            ),
            
            # 识别的趋势和模式
            "identified_trends": self._identify_domain_trends(exploration_opportunities),
            
            # 跨域连接
            "cross_domain_connections": self._find_cross_domain_connections(
                exploration_opportunities
            ),
            
            # 待进一步探索的方向
            "future_exploration_directions": self._suggest_future_explorations(
                exploration_opportunities,
                knowledge_gaps
            )
        }
        
        return exploration_results
    
    def _map_to_exploration_strategy(self, strategy_names: List[str]) -> Optional[ExplorationStrategy]:
        """将策略名称映射到ExplorationStrategy枚举"""
        if not strategy_names:
            return None
        
        strategy_mapping = {
            "domain_expansion": ExplorationStrategy.DOMAIN_EXPANSION,
            "trend_monitoring": ExplorationStrategy.TREND_MONITORING,
            "gap_analysis": ExplorationStrategy.GAP_ANALYSIS,
            "cross_domain_learning": ExplorationStrategy.CROSS_DOMAIN_LEARNING,
            "serendipity_discovery": ExplorationStrategy.SERENDIPITY_DISCOVERY
        }
        
        # 使用第一个匹配的策略
        for strategy_name in strategy_names:
            if strategy_name in strategy_mapping:
                return strategy_mapping[strategy_name]
        
        return ExplorationStrategy.DOMAIN_EXPANSION  # 默认策略
    
    def _convert_explorer_result_to_scheduler_format(self, 
                                                   explorer_result, 
                                                   task_id: str) -> Dict[str, Any]:
        """将KnowledgeExplorer的结果转换为CognitiveScheduler格式"""
        
        # 转换发现的知识
        discovered_knowledge = []
        for knowledge_item in explorer_result.discovered_knowledge:
            discovered_knowledge.append({
                "knowledge_id": knowledge_item.knowledge_id,
                "content": knowledge_item.content,
                "source": knowledge_item.source,
                "quality": knowledge_item.quality.value,
                "confidence_score": knowledge_item.confidence_score,
                "relevance_score": knowledge_item.relevance_score,
                "novelty_score": knowledge_item.novelty_score,
                "tags": knowledge_item.tags,
                "discovered_at": knowledge_item.discovered_at
            })
        
        # 转换生成的种子
        generated_thinking_seeds = []
        for seed in explorer_result.generated_seeds:
            generated_thinking_seeds.append({
                "seed_id": seed.seed_id,
                "seed_content": seed.seed_content,
                "creativity_level": seed.creativity_level,
                "confidence": seed.confidence,
                "potential_applications": seed.potential_applications,
                "source_knowledge": seed.source_knowledge,
                "suggested_reasoning_paths": seed.suggested_reasoning_paths,
                "cross_domain_connections": seed.cross_domain_connections,
                "generated_at": seed.generated_at
            })
        
        # 构建完整结果
        scheduler_result = {
            "exploration_metadata": {
                "exploration_session_id": task_id,
                "explorer_id": explorer_result.exploration_id,
                "strategy_used": explorer_result.strategy.value,
                "targets_explored": len(explorer_result.targets),
                "execution_time": explorer_result.execution_time,
                "success_rate": explorer_result.success_rate,
                "quality_score": explorer_result.quality_score,
                "execution_mode": "professional_explorer"
            },
            
            "discovered_knowledge": discovered_knowledge,
            "generated_thinking_seeds": generated_thinking_seeds,
            "identified_trends": explorer_result.identified_trends,
            "cross_domain_connections": [
                {
                    "connection_id": insight.get("insight_id", "unknown"),
                    "description": insight.get("description", ""),
                    "confidence": insight.get("confidence", 0.5)
                }
                for insight in explorer_result.cross_domain_insights
            ],
            
            # 保持原有格式的字段
            "future_exploration_directions": self._suggest_future_explorations_from_explorer_result(
                explorer_result
            )
        }
        
        return scheduler_result
    
    def _suggest_future_explorations_from_explorer_result(self, 
                                                        explorer_result) -> List[Dict[str, Any]]:
        """基于探勘器结果建议未来探索方向"""
        directions = []
        
        # 基于发现的知识建议后续探索
        high_quality_knowledge = [
            k for k in explorer_result.discovered_knowledge 
            if k.confidence_score > 0.7
        ]
        
        for knowledge in high_quality_knowledge[:2]:
            direction = {
                "direction_id": f"future_{knowledge.knowledge_id}",
                "exploration_focus": f"深入探索{knowledge.tags[0] if knowledge.tags else '相关领域'}",
                "recommended_strategies": ["deep_dive_analysis", "expert_consultation"],
                "priority": knowledge.confidence_score,
                "estimated_effort": "medium",
                "expected_outcomes": [
                    f"深化{knowledge.tags[0] if knowledge.tags else '相关'}领域知识",
                    "发现更多创新机会"
                ]
            }
            directions.append(direction)
        
        return directions
    
    # ==================== 辅助方法 ====================
    
    def _on_state_change(self, event_type: str, event_data: Dict[str, Any], state_manager):
        """状态变化监听器回调"""
        if event_type == "goal_progress":
            self.last_activity_time = time.time()
        elif event_type == "turn_completed":
            success = event_data.get("success", False)
            if success:
                self.last_activity_time = time.time()
    
    def _merge_config(self, base_config: Dict, user_config: Dict):
        """递归合并配置"""
        for key, value in user_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def _has_active_task_type(self, task_type: str) -> bool:
        """检查是否有指定类型的活跃认知任务"""
        return any(task.task_type == task_type for task in self.active_cognitive_tasks.values())
    
    def _should_trigger_knowledge_synthesis(self) -> bool:
        """判断是否应该触发知识综合"""
        # 简单实现：当认知历史达到一定数量时触发
        return len(self.cognitive_history) > 0 and len(self.cognitive_history) % 5 == 0
    
    def _extract_session_insights(self) -> Dict[str, Any]:
        """从当前会话中提取见解"""
        current_state = self.state_manager.get_current_state()
        return {
            "recent_patterns": "会话模式分析",
            "decision_trends": "决策趋势分析",
            "context_evolution": "上下文演化分析"
        }
    
    def _identify_success_patterns(self, session_state: Dict) -> List[str]:
        """识别成功模式"""
        return ["成功模式1", "成功模式2"]  # 简化实现
    
    def _identify_failure_patterns(self, session_state: Dict) -> List[str]:
        """识别失败模式"""  
        return ["失败模式1", "失败模式2"]  # 简化实现
    
    def _extract_golden_decision_templates(self, session_state: Dict) -> List[str]:
        """提取黄金决策模板"""
        return ["黄金模板1", "黄金模板2"]  # 简化实现
    
    def _synthesize_core_patterns(self, cognitive_history: List) -> List[str]:
        """综合核心模式"""
        return ["核心模式1", "核心模式2"]  # 简化实现
        
    def _extract_meta_insights(self, cognitive_history: List) -> List[str]:
        """提取元见解"""
        return ["元见解1", "元见解2"]  # 简化实现
    
    # 🌐 ==================== 知识探索辅助方法 ====================
    
    def _analyze_exploration_opportunities(self) -> List[Dict[str, Any]]:
        """分析当前的知识探索机会"""
        current_state = self.state_manager.get_current_state()
        conversation_history = current_state.get("conversation", {})
        
        # 基础机会识别（后续可通过LLM增强）
        opportunities = [
            {
                "opportunity_id": "domain_trends",
                "type": "trend_monitoring",
                "description": "监控相关领域的最新发展趋势",
                "priority": 0.8,
                "exploration_keywords": ["AI trends", "technology developments", "emerging patterns"]
            },
            {
                "opportunity_id": "knowledge_gaps",
                "type": "gap_analysis",
                "description": "识别当前知识体系中的空白区域",
                "priority": 0.7,
                "exploration_keywords": ["missing concepts", "unexplored areas", "knowledge boundaries"]
            },
            {
                "opportunity_id": "cross_domain",
                "type": "cross_domain_learning",
                "description": "寻找跨领域的知识连接和启发",
                "priority": 0.6,
                "exploration_keywords": ["interdisciplinary", "cross-field applications", "analogies"]
            }
        ]
        
        return opportunities
    
    def _identify_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """识别当前知识体系中的缺口"""
        # 分析历史对话和决策，找出知识盲区
        gaps = [
            {
                "gap_id": "emerging_tech",
                "area": "新兴技术",
                "description": "对最新技术发展的了解不足",
                "impact": "high",
                "exploration_priority": 0.9
            },
            {
                "gap_id": "domain_best_practices",
                "area": "领域最佳实践", 
                "description": "缺乏特定领域的最佳实践知识",
                "impact": "medium",
                "exploration_priority": 0.7
            }
        ]
        
        return gaps
    
    def _discover_new_knowledge(self, 
                               opportunities: List[Dict[str, Any]], 
                               gaps: List[Dict[str, Any]], 
                               strategies: List[str]) -> List[Dict[str, Any]]:
        """发现新知识（基础实现，后续可集成网络搜索和LLM分析）"""
        discovered_knowledge = []
        
        # 对每个探索机会进行知识发现
        for opportunity in opportunities[:2]:  # 限制探索数量
            knowledge_item = {
                "knowledge_id": f"discovery_{opportunity['opportunity_id']}_{int(time.time())}",
                "source_opportunity": opportunity["opportunity_id"],
                "knowledge_type": opportunity["type"],
                "content": f"基于{opportunity['description']}的新发现",
                "confidence_score": 0.6,
                "exploration_method": "cognitive_analysis",
                "discovery_timestamp": time.time(),
                "potential_applications": [
                    "思维路径优化",
                    "决策策略改进",
                    "创新思维激发"
                ]
            }
            discovered_knowledge.append(knowledge_item)
        
        return discovered_knowledge
    
    def _generate_exploration_based_seeds(self, 
                                        opportunities: List[Dict[str, Any]], 
                                        gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于探索结果生成新的思维种子"""
        thinking_seeds = []
        
        # 为每个探索机会生成对应的思维种子
        for opportunity in opportunities[:3]:  # 生成前3个机会的种子
            seed = {
                "seed_id": f"exploration_seed_{opportunity['opportunity_id']}_{int(time.time())}",
                "seed_content": f"基于{opportunity['description']}的探索性思维种子",
                "source_type": "knowledge_exploration",
                "creativity_level": "high",
                "potential_paths": [
                    f"{opportunity['type']}_analytical_path",
                    f"{opportunity['type']}_creative_path",
                    f"{opportunity['type']}_systematic_path"
                ],
                "confidence": 0.7,
                "generated_timestamp": time.time()
            }
            thinking_seeds.append(seed)
        
        return thinking_seeds
    
    def _identify_domain_trends(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别领域趋势"""
        trends = []
        
        for opportunity in opportunities:
            if opportunity["type"] == "trend_monitoring":
                trend = {
                    "trend_id": f"trend_{opportunity['opportunity_id']}",
                    "trend_name": f"基于{opportunity['description']}的趋势",
                    "confidence": 0.6,
                    "time_horizon": "short_term",
                    "impact_areas": ["cognitive_strategies", "decision_making"],
                    "identified_at": time.time()
                }
                trends.append(trend)
        
        return trends
    
    def _find_cross_domain_connections(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """发现跨域连接"""
        connections = []
        
        # 寻找机会之间的潜在连接
        for i, opp1 in enumerate(opportunities):
            for opp2 in opportunities[i+1:]:
                connection = {
                    "connection_id": f"cross_{opp1['opportunity_id']}_{opp2['opportunity_id']}",
                    "domain1": opp1["type"],
                    "domain2": opp2["type"],
                    "connection_strength": 0.5,
                    "potential_synergies": [
                        f"结合{opp1['type']}和{opp2['type']}的综合方法"
                    ],
                    "discovered_at": time.time()
                }
                connections.append(connection)
        
        return connections
    
    def _suggest_future_explorations(self, 
                                   opportunities: List[Dict[str, Any]], 
                                   gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """建议未来的探索方向"""
        future_directions = []
        
        # 基于当前探索结果，推荐下一步探索方向
        for gap in gaps[:2]:  # 针对前2个知识缺口
            direction = {
                "direction_id": f"future_{gap['gap_id']}",
                "exploration_focus": gap["area"],
                "recommended_strategies": ["deep_dive_analysis", "expert_consultation"],
                "priority": gap["exploration_priority"],
                "estimated_effort": "medium",
                "expected_outcomes": [
                    f"填补{gap['area']}的知识空白",
                    "增强相关领域的决策能力"
                ]
            }
            future_directions.append(direction)
        
        return future_directions
    
    def _update_exploration_caches(self, exploration_results: Dict[str, Any]):
        """更新探索历史和缓存"""
        # 更新探索历史
        exploration_record = {
            "exploration_id": exploration_results["exploration_metadata"]["exploration_session_id"],
            "timestamp": time.time(),
            "knowledge_discovered": len(exploration_results["discovered_knowledge"]),
            "seeds_generated": len(exploration_results["generated_thinking_seeds"]),
            "trends_identified": len(exploration_results["identified_trends"])
        }
        self.exploration_history.append(exploration_record)
        
        # 更新发现的知识缓存
        for knowledge_item in exploration_results["discovered_knowledge"]:
            self.discovered_knowledge[knowledge_item["knowledge_id"]] = knowledge_item
        
        # 更新探索主题缓存
        for seed in exploration_results["generated_thinking_seeds"]:
            if seed["seed_content"] not in self.exploration_topics_cache:
                self.exploration_topics_cache.append(seed["seed_content"])
        
        # 限制缓存大小
        if len(self.exploration_history) > 50:
            self.exploration_history = self.exploration_history[-30:]
        
        if len(self.exploration_topics_cache) > 100:
            self.exploration_topics_cache = self.exploration_topics_cache[-60:]
    
    def _integrate_discovered_knowledge_to_flywheel(self, exploration_results: Dict[str, Any]):
        """🔄 将发现的知识整合到认知飞轮中"""
        logger.info("🔄 开始将探索知识整合到认知飞轮...")
        
        # 1. 将生成的思维种子添加到种子库
        thinking_seeds = exploration_results.get("generated_thinking_seeds", [])
        for seed in thinking_seeds:
            # 这里将与回溯引擎和MAB系统集成
            # 将新种子作为候选路径加入决策系统
            logger.debug(f"   集成思维种子: {seed['seed_id']}")
        
        # 2. 将发现的趋势更新到知识库
        trends = exploration_results.get("identified_trends", [])
        for trend in trends:
            # 趋势信息可以影响未来的路径选择权重
            logger.debug(f"   集成趋势信息: {trend['trend_id']}")
        
        # 3. 跨域连接信息可以增强创意突破能力
        connections = exploration_results.get("cross_domain_connections", [])
        for connection in connections:
            # 跨域连接可以触发新的Aha-Moment路径
            logger.debug(f"   集成跨域连接: {connection['connection_id']}")
        
        logger.info(f"🔄 认知飞轮整合完成: {len(thinking_seeds)} 种子, {len(trends)} 趋势, {len(connections)} 连接")
    
    def _determine_retrospection_strategy(self, 
                                       trigger_reason: str, 
                                       context: Dict[str, Any]) -> RetrospectionStrategy:
        """
        根据触发原因确定回溯策略
        
        Args:
            trigger_reason: 触发原因
            context: 任务上下文
            
        Returns:
            合适的回溯策略
        """
        # 根据不同的触发原因选择最佳回溯策略
        if trigger_reason == "idle_detection":
            # 空闲检测触发：使用随机采样获得多样性
            return RetrospectionStrategy.RANDOM_SAMPLING
        
        elif trigger_reason == "failure_analysis":
            # 失败分析触发：专注分析失败案例
            return RetrospectionStrategy.FAILURE_FOCUSED
        
        elif trigger_reason == "performance_review":
            # 性能评估触发：基于复杂度选择
            return RetrospectionStrategy.COMPLEXITY_BASED
        
        elif trigger_reason == "periodic_ideation":
            # 定期创想触发：选择最近的任务
            return RetrospectionStrategy.RECENT_TASKS
        
        else:
            # 默认策略
            return RetrospectionStrategy.RANDOM_SAMPLING
    
    def _convert_retrospection_result(self, 
                                    retrospection_result) -> Dict[str, Any]:
        """
        将TaskRetrospectionEngine的结果转换为CognitiveScheduler的分析格式
        
        Args:
            retrospection_result: 回溯引擎的结果
            
        Returns:
            转换后的分析结果
        """
        if not retrospection_result or not retrospection_result.task:
            return {
                "status": "no_analysis",
                "message": "回溯引擎未能产生有效分析结果"
            }
        
        # 提取核心信息
        task_info = retrospection_result.task
        original_turn = task_info.original_turn
        
        # 构建详细分析
        analysis = {
            "retrospection_metadata": {
                "retrospection_id": retrospection_result.retrospection_id,
                "selected_task_id": task_info.task_id,
                "selection_strategy": task_info.selection_strategy.value,
                "execution_time": retrospection_result.execution_time,
                "complexity_score": task_info.complexity_score
            },
            
            "task_analysis": {
                "original_question": original_turn.user_input,
                "original_success": original_turn.success,
                "tool_calls_count": len(original_turn.tool_calls),
                "mab_decisions_count": len(original_turn.mab_decisions),
                "task_phase": original_turn.phase.value
            },
            
            "creative_insights": {
                "llm_dimensions": [
                    {
                        "dimension_id": dim.get("dimension_id", "unknown"),
                        "description": dim.get("description", "新思维维度"),
                        "creativity_level": dim.get("creativity_level", "medium")
                    }
                    for dim in retrospection_result.llm_dimensions
                ],
                "aha_moment_paths": [
                    {
                        "path_id": getattr(path, "path_id", "unknown"),
                        "path_type": getattr(path, "path_type", "creative"),
                        "confidence": getattr(path, "confidence_score", 0.5)
                    }
                    for path in retrospection_result.aha_moment_paths
                ]
            },
            
            "extracted_insights": retrospection_result.insights,
            "success_patterns": retrospection_result.success_patterns,
            "failure_causes": retrospection_result.failure_causes,
            "improvement_suggestions": retrospection_result.improvement_suggestions,
            
            "knowledge_assimilation": {
                "assimilated_strategies": retrospection_result.assimilated_strategies,
                "mab_updates_count": len(retrospection_result.mab_updates),
                "total_new_knowledge_items": (
                    len(retrospection_result.llm_dimensions) + 
                    len(retrospection_result.aha_moment_paths)
                )
            },
            
            "retrospection_summary": {
                "total_insights": len(retrospection_result.insights),
                "actionable_improvements": len(retrospection_result.improvement_suggestions),
                "creative_breakthroughs": (
                    len(retrospection_result.llm_dimensions) + 
                    len(retrospection_result.aha_moment_paths)
                ),
                "knowledge_integration_success": len(retrospection_result.assimilated_strategies) > 0
            }
        }
        
        return analysis
    
    def update_retrospection_dependencies(self, 
                                        path_generator=None, 
                                        mab_converger=None):
        """
        更新回溯引擎的依赖组件
        
        这个方法允许外部（如Agent或Planner）向认知调度器提供
        回溯引擎所需的PathGenerator和MABConverger组件
        
        Args:
            path_generator: 路径生成器实例
            mab_converger: MAB收敛器实例
        """
        if not self.retrospection_engine:
            logger.warning("⚠️ 回溯引擎未初始化，无法更新依赖")
            return False
        
        updated_components = []
        
        if path_generator:
            self.retrospection_engine.path_generator = path_generator
            updated_components.append("PathGenerator")
        
        if mab_converger:
            self.retrospection_engine.mab_converger = mab_converger
            updated_components.append("MABConverger")
        
        if updated_components:
            logger.info(f"🔧 回溯引擎依赖组件已更新: {', '.join(updated_components)}")
            logger.info("✅ 回溯引擎现可执行完整的三阶段流程")
            return True
        
        return False
    
    def update_knowledge_explorer_dependencies(self, 
                                             web_search_client=None,
                                             additional_config: Optional[Dict[str, Any]] = None):
        """
        更新知识探勘器的依赖组件
        
        这个方法允许外部（如Agent或Planner）向认知调度器提供
        知识探勘器所需的依赖组件
        
        Args:
            web_search_client: 网络搜索客户端实例
            additional_config: 额外的配置参数
        """
        if not self.knowledge_explorer:
            logger.warning("⚠️ 知识探勘器未初始化，无法更新依赖")
            return False
        
        updated_components = []
        
        if web_search_client:
            self.knowledge_explorer.web_search_client = web_search_client
            updated_components.append("WebSearchClient")
        
        if additional_config:
            self.knowledge_explorer._merge_config(
                self.knowledge_explorer.config, 
                additional_config
            )
            updated_components.append("Config")
        
        if updated_components:
            logger.info(f"🔧 知识探勘器依赖组件已更新: {', '.join(updated_components)}")
            logger.info("✅ 知识探勘器现可执行完整的外部智慧连接")
            return True
        
        return False
    
    def _pause_low_priority_cognitive_tasks(self):
        """暂停低优先级认知任务"""
        # 简化实现，后续可以添加任务优先级管理
        pass
    
    def _cleanup_expired_tasks(self):
        """清理过期任务"""
        current_time = time.time()
        timeout = self.config["cognitive_tasks"]["task_timeout"]
        
        expired_tasks = []
        for task_id, task in self.active_cognitive_tasks.items():
            if (current_time - task.created_at) > timeout:
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            self.active_cognitive_tasks.pop(task_id, None)
            logger.warning(f"⏰ 认知任务超时被清理: {task_id}")
    
    def _log_final_stats(self):
        """记录最终统计信息"""
        logger.info("📊 认知调度器最终统计:")
        logger.info(f"   总空闲周期: {self.stats['total_idle_periods']}")
        logger.info(f"   总空闲时间: {self.stats['total_idle_time']:.1f}s") 
        logger.info(f"   完成认知任务: {self.stats['cognitive_tasks_completed']}")
        logger.info(f"   回溯会话: {self.stats['retrospection_sessions']}")
        logger.info(f"   创想会话: {self.stats['ideation_sessions']}")
        logger.info(f"   知识综合: {self.stats['knowledge_synthesis_sessions']}")
        logger.info(f"   🌐 知识探索: {self.stats['knowledge_exploration_sessions']}")  # 新增
        
        # 🌐 新增：知识探索详细统计
        if hasattr(self, 'exploration_history') and self.exploration_history:
            total_knowledge_discovered = sum(record.get('knowledge_discovered', 0) for record in self.exploration_history)
            total_seeds_generated = sum(record.get('seeds_generated', 0) for record in self.exploration_history)
            logger.info(f"   探索发现知识: {total_knowledge_discovered} 项")
            logger.info(f"   生成思维种子: {total_seeds_generated} 个")
            logger.info(f"   探索主题缓存: {len(self.exploration_topics_cache)} 个")
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "current_mode": self.current_mode.value,
            "is_idle": self.is_idle,
            "active_cognitive_tasks": len(self.active_cognitive_tasks),
            "queued_cognitive_tasks": self.cognitive_task_queue.qsize(),
            "stats": self.stats.copy()
        }
