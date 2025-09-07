#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自主知识探勘模块 - Knowledge Explorer
Agent连接外部智慧的桥梁

这个模块实现了认知飞轮的"探索触角"，负责：
1. 主动探勘外部世界的新知识和智慧
2. 多源信息的获取、整合和质量评估
3. 基于探索结果生成新的思维种子
4. 为认知飞轮提供持续的"营养输入"

核心理念：让AI从内向型思维扩展为外向型认知探索者
"""

import time
import random
import logging
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json

try:
    from .search_tools import WebSearchClient
except ImportError:
    WebSearchClient = None

logger = logging.getLogger(__name__)


class ExplorationStrategy(Enum):
    """探索策略枚举"""
    DOMAIN_EXPANSION = "domain_expansion"           # 领域扩展探索
    TREND_MONITORING = "trend_monitoring"           # 趋势监控探索
    GAP_ANALYSIS = "gap_analysis"                   # 知识缺口分析
    CROSS_DOMAIN_LEARNING = "cross_domain_learning" # 跨域学习探索
    SERENDIPITY_DISCOVERY = "serendipity_discovery" # 偶然发现探索
    EXPERT_KNOWLEDGE = "expert_knowledge"           # 专家知识获取
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence" # 竞争情报分析


class KnowledgeQuality(Enum):
    """知识质量等级"""
    EXCELLENT = "excellent"     # 优秀：高可信度、高创新性
    GOOD = "good"              # 良好：中等质量，有一定价值
    FAIR = "fair"              # 一般：基础信息，参考价值
    POOR = "poor"              # 较差：质量存疑，需要验证
    UNRELIABLE = "unreliable"   # 不可靠：不建议使用


@dataclass
class ExplorationTarget:
    """探索目标数据结构"""
    target_id: str
    target_type: str  # "concept", "trend", "technology", "methodology", "domain"
    description: str
    keywords: List[str] = field(default_factory=list)
    priority: float = 0.5  # 0-1, 1为最高优先级
    exploration_depth: int = 1  # 探索深度层级
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class KnowledgeItem:
    """知识项数据结构"""
    knowledge_id: str
    content: str
    source: str
    source_type: str  # "web_search", "api_call", "database", "expert_system"
    quality: KnowledgeQuality
    confidence_score: float = 0.5  # 0-1, 置信度分数
    relevance_score: float = 0.5   # 0-1, 相关性分数
    novelty_score: float = 0.5     # 0-1, 新颖性分数
    
    # 元数据
    extraction_method: str = ""
    language: str = "zh"
    discovered_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    
    # 验证状态
    is_verified: bool = False
    verification_method: str = ""
    verification_score: float = 0.0


@dataclass
class ThinkingSeed:
    """思维种子数据结构"""
    seed_id: str
    seed_content: str
    source_knowledge: List[str] = field(default_factory=list)  # 来源知识项ID列表
    creativity_level: str = "medium"  # "low", "medium", "high"
    potential_applications: List[str] = field(default_factory=list)
    generated_strategy: str = ""
    confidence: float = 0.5
    
    # 认知路径相关
    suggested_reasoning_paths: List[str] = field(default_factory=list)
    cross_domain_connections: List[str] = field(default_factory=list)
    
    # 元数据
    generated_at: float = field(default_factory=time.time)
    generation_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExplorationResult:
    """探索结果数据结构"""
    exploration_id: str
    strategy: ExplorationStrategy
    targets: List[ExplorationTarget]
    
    # 探索成果
    discovered_knowledge: List[KnowledgeItem] = field(default_factory=list)
    generated_seeds: List[ThinkingSeed] = field(default_factory=list)
    identified_trends: List[Dict[str, Any]] = field(default_factory=list)
    cross_domain_insights: List[Dict[str, Any]] = field(default_factory=list)
    
    # 执行统计
    execution_time: float = 0.0
    success_rate: float = 0.0
    quality_score: float = 0.0
    
    # 元数据
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)


class KnowledgeExplorer:
    """
    🌐 自主知识探勘模块 - Agent的"外部智慧连接器"
    
    核心职责：
    1. 主动探勘外部世界的新知识和趋势
    2. 多源信息获取：网络搜索、API调用、专家系统
    3. 智能知识质量评估和过滤机制
    4. 基于探索发现生成高质量思维种子
    5. 为认知飞轮提供持续的知识"营养输入"
    
    设计原则：
    - 主动性：不等待指令，主动发现机会
    - 多样性：支持多种探索策略和信息源
    - 质量优先：严格的知识质量评估体系
    - 适应性：根据探索效果动态调整策略
    """
    
    def __init__(self, 
                 llm_client=None,
                 web_search_client=None,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化知识探勘模块
        
        Args:
            llm_client: LLM客户端（用于智能分析）
            web_search_client: 网络搜索客户端
            config: 探勘配置参数
        """
        self.llm_client = llm_client
        self.web_search_client = web_search_client
        
        # 配置参数
        self.config = {
            # 探索策略配置
            "exploration_strategies": {
                "default_strategy": ExplorationStrategy.DOMAIN_EXPANSION,
                "strategy_rotation": True,              # 是否轮换策略
                "max_parallel_explorations": 3,        # 最大并行探索数
                "exploration_timeout": 120.0           # 探索超时时间
            },
            
            # 质量控制配置
            "quality_control": {
                "min_confidence_threshold": 0.4,       # 最小置信度阈值
                "min_relevance_threshold": 0.3,        # 最小相关性阈值
                "enable_cross_validation": True,       # 启用交叉验证
                "quality_decay_factor": 0.1            # 质量衰减因子
            },
            
            # 种子生成配置
            "seed_generation": {
                "max_seeds_per_exploration": 5,        # 每次探索最大种子数
                "creativity_boost_factor": 1.2,        # 创意提升因子
                "cross_domain_bonus": 0.3,            # 跨域连接奖励
                "enable_serendipity": True             # 启用偶然发现
            },
            
            # 信息源配置
            "information_sources": {
                "enable_web_search": True,             # 启用网络搜索
                "enable_api_calls": False,             # 启用API调用
                "enable_database_query": False,       # 启用数据库查询
                "max_results_per_source": 10          # 每个信息源最大结果数
            }
        }
        
        # 合并用户配置
        if config:
            self._merge_config(self.config, config)
        
        # 初始化信息源客户端
        if not self.web_search_client and self.config["information_sources"]["enable_web_search"]:
            try:
                if WebSearchClient:
                    self.web_search_client = WebSearchClient(
                        max_results=self.config["information_sources"]["max_results_per_source"]
                    )
                    logger.info("🌐 网络搜索客户端已初始化")
                else:
                    logger.warning("⚠️ WebSearchClient 不可用，网络搜索功能将被禁用")
            except Exception as e:
                logger.warning(f"⚠️ 网络搜索客户端初始化失败: {e}")
        
        # 探索历史和统计
        self.exploration_history: List[ExplorationResult] = []
        self.knowledge_cache: Dict[str, KnowledgeItem] = {}
        self.seed_cache: Dict[str, ThinkingSeed] = {}
        
        # 策略性能统计
        self.strategy_performance: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"success_rate": 0.0, "avg_quality": 0.0, "total_seeds": 0}
        )
        
        # 探索目标管理
        self.active_targets: List[ExplorationTarget] = []
        self.completed_targets: List[ExplorationTarget] = []
        
        # 性能统计
        self.stats = {
            "total_explorations": 0,
            "successful_explorations": 0,
            "total_knowledge_discovered": 0,
            "total_seeds_generated": 0,
            "average_quality_score": 0.0,
            "average_execution_time": 0.0
        }
        
        logger.info("🌐 KnowledgeExplorer 初始化完成")
        logger.info(f"   网络搜索: {'启用' if self.web_search_client else '禁用'}")
        logger.info(f"   LLM分析: {'启用' if self.llm_client else '禁用'}")
        logger.info("🔍 外部智慧连接器已就绪 - 主动探索模式启动")
    
    def explore_knowledge(self, 
                         targets: List[ExplorationTarget],
                         strategy: Optional[ExplorationStrategy] = None) -> ExplorationResult:
        """
        执行知识探勘任务 - 核心入口方法
        
        Args:
            targets: 探索目标列表
            strategy: 探索策略（可选）
            
        Returns:
            完整的探索结果
        """
        start_time = time.time()
        exploration_id = f"exploration_{int(time.time() * 1000)}"
        
        # 确定探索策略
        if not strategy:
            strategy = self._select_optimal_strategy(targets)
        
        logger.info(f"🌐 开始知识探勘: {exploration_id}")
        logger.info(f"   策略: {strategy.value}")
        logger.info(f"   目标数量: {len(targets)}")
        
        try:
            # 创建探索结果对象
            result = ExplorationResult(
                exploration_id=exploration_id,
                strategy=strategy,
                targets=targets
            )
            
            # 执行探索流程
            self._execute_exploration_pipeline(result)
            
            # 计算执行统计
            result.execution_time = time.time() - start_time
            result.success_rate = self._calculate_success_rate(result)
            result.quality_score = self._calculate_quality_score(result)
            
            # 更新缓存和统计
            self._update_caches_and_stats(result)
            
            logger.info(f"✅ 知识探勘完成: {exploration_id}")
            logger.info(f"   执行时间: {result.execution_time:.2f}s")
            logger.info(f"   发现知识: {len(result.discovered_knowledge)} 项")
            logger.info(f"   生成种子: {len(result.generated_seeds)} 个")
            logger.info(f"   质量评分: {result.quality_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 知识探勘失败: {exploration_id} - {e}")
            # 返回空结果但包含错误信息
            return ExplorationResult(
                exploration_id=exploration_id,
                strategy=strategy,
                targets=targets,
                execution_time=time.time() - start_time,
                context={"error": str(e)}
            )
    
    def _execute_exploration_pipeline(self, result: ExplorationResult):
        """执行完整的探索流水线"""
        logger.info("🔄 执行探索流水线...")
        
        # 阶段1: 信息收集
        logger.info("📡 阶段1: 信息收集")
        raw_information = self._collect_information(result.targets, result.strategy)
        
        # 阶段2: 知识提取和质量评估
        logger.info("🔍 阶段2: 知识提取和质量评估")
        result.discovered_knowledge = self._extract_and_evaluate_knowledge(
            raw_information, result.targets
        )
        
        # 阶段3: 思维种子生成
        logger.info("🌱 阶段3: 思维种子生成")
        result.generated_seeds = self._generate_thinking_seeds(
            result.discovered_knowledge, result.strategy
        )
        
        # 阶段4: 趋势分析
        logger.info("📈 阶段4: 趋势分析")
        result.identified_trends = self._analyze_trends(
            result.discovered_knowledge, result.targets
        )
        
        # 阶段5: 跨域洞察发现
        logger.info("🔗 阶段5: 跨域洞察发现")
        result.cross_domain_insights = self._discover_cross_domain_insights(
            result.discovered_knowledge, result.generated_seeds
        )
        
        logger.info("✅ 探索流水线执行完成")
    
    def _collect_information(self, 
                           targets: List[ExplorationTarget], 
                           strategy: ExplorationStrategy) -> List[Dict[str, Any]]:
        """信息收集阶段 - 从多个信息源获取原始信息"""
        raw_information = []
        
        for target in targets[:self.config["exploration_strategies"]["max_parallel_explorations"]]:
            logger.debug(f"🎯 收集目标信息: {target.target_id}")
            
            # 网络搜索
            if (self.web_search_client and 
                self.config["information_sources"]["enable_web_search"]):
                web_results = self._search_web_information(target, strategy)
                raw_information.extend(web_results)
            
            # API调用（预留接口）
            if self.config["information_sources"]["enable_api_calls"]:
                api_results = self._query_api_sources(target, strategy)
                raw_information.extend(api_results)
            
            # 数据库查询（预留接口）
            if self.config["information_sources"]["enable_database_query"]:
                db_results = self._query_database_sources(target, strategy)
                raw_information.extend(db_results)
        
        logger.info(f"📡 信息收集完成: 获取 {len(raw_information)} 条原始信息")
        return raw_information
    
    def _search_web_information(self, 
                              target: ExplorationTarget, 
                              strategy: ExplorationStrategy) -> List[Dict[str, Any]]:
        """执行网络搜索"""
        if not self.web_search_client:
            return []
        
        try:
            # 构建搜索查询
            search_queries = self._build_search_queries(target, strategy)
            web_results = []
            
            for query in search_queries[:3]:  # 限制查询数量
                logger.debug(f"🔍 搜索查询: {query}")
                
                results = self.web_search_client.search(query)
                for result in results:
                    web_results.append({
                        "content": result.get("snippet", ""),
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "source": "web_search",
                        "query": query,
                        "target_id": target.target_id,
                        "collected_at": time.time()
                    })
            
            logger.debug(f"🌐 网络搜索完成: {len(web_results)} 条结果")
            return web_results
            
        except Exception as e:
            logger.error(f"❌ 网络搜索失败: {e}")
            return []
    
    def _build_search_queries(self, 
                            target: ExplorationTarget, 
                            strategy: ExplorationStrategy) -> List[str]:
        """构建针对不同策略的搜索查询"""
        base_keywords = target.keywords + [target.description]
        queries = []
        
        if strategy == ExplorationStrategy.TREND_MONITORING:
            for keyword in base_keywords[:2]:
                queries.extend([
                    f"{keyword} 最新趋势 2024",
                    f"{keyword} 发展动态",
                    f"{keyword} 未来展望"
                ])
        
        elif strategy == ExplorationStrategy.DOMAIN_EXPANSION:
            for keyword in base_keywords[:2]:
                queries.extend([
                    f"{keyword} 相关技术",
                    f"{keyword} 应用领域",
                    f"{keyword} 创新应用"
                ])
        
        elif strategy == ExplorationStrategy.GAP_ANALYSIS:
            for keyword in base_keywords[:2]:
                queries.extend([
                    f"{keyword} 挑战问题",
                    f"{keyword} 技术瓶颈",
                    f"{keyword} 解决方案"
                ])
        
        elif strategy == ExplorationStrategy.CROSS_DOMAIN_LEARNING:
            for keyword in base_keywords[:2]:
                queries.extend([
                    f"{keyword} 跨学科应用",
                    f"{keyword} 其他领域",
                    f"{keyword} 融合创新"
                ])
        
        elif strategy == ExplorationStrategy.EXPERT_KNOWLEDGE:
            for keyword in base_keywords[:2]:
                queries.extend([
                    f"{keyword} 专家观点",
                    f"{keyword} 最佳实践",
                    f"{keyword} 专业方法论",
                    f"{keyword} 行业经验",
                    f"{keyword} 权威指南"
                ])
        
        else:
            # 默认查询
            queries.extend(base_keywords[:3])
        
        return queries[:5]  # 限制查询数量
    
    def _query_api_sources(self, 
                         target: ExplorationTarget, 
                         strategy: ExplorationStrategy) -> List[Dict[str, Any]]:
        """查询API信息源（预留接口）"""
        # 这里可以集成各种API：
        # - 学术论文API (arXiv, PubMed等)
        # - 新闻API (News API等)
        # - 技术文档API (GitHub, Stack Overflow等)
        # - 专业数据库API
        
        return []  # 当前为空实现
    
    def _query_database_sources(self, 
                              target: ExplorationTarget, 
                              strategy: ExplorationStrategy) -> List[Dict[str, Any]]:
        """查询数据库信息源（预留接口）"""
        # 这里可以集成：
        # - 内部知识库
        # - 行业数据库
        # - 历史探索缓存
        
        return []  # 当前为空实现
    
    def _extract_and_evaluate_knowledge(self, 
                                      raw_information: List[Dict[str, Any]], 
                                      targets: List[ExplorationTarget]) -> List[KnowledgeItem]:
        """知识提取和质量评估"""
        knowledge_items = []
        
        for info in raw_information:
            try:
                # 提取知识内容
                knowledge_item = self._extract_knowledge_from_info(info, targets)
                if knowledge_item:
                    # 评估知识质量
                    self._evaluate_knowledge_quality(knowledge_item)
                    
                    # 质量过滤
                    if self._passes_quality_filter(knowledge_item):
                        knowledge_items.append(knowledge_item)
                        logger.debug(f"✅ 知识提取成功: {knowledge_item.knowledge_id}")
                    else:
                        logger.debug(f"❌ 知识质量不合格: {knowledge_item.knowledge_id}")
            
            except Exception as e:
                logger.debug(f"⚠️ 知识提取失败: {e}")
                continue
        
        logger.info(f"🔍 知识提取完成: {len(knowledge_items)} 项高质量知识")
        return knowledge_items
    
    def _extract_knowledge_from_info(self, 
                                   info: Dict[str, Any], 
                                   targets: List[ExplorationTarget]) -> Optional[KnowledgeItem]:
        """从原始信息中提取知识项"""
        content = info.get("content", "")
        if not content or len(content.strip()) < 10:
            return None
        
        # 生成知识ID
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        knowledge_id = f"knowledge_{content_hash}_{int(time.time())}"
        
        # 创建知识项
        knowledge_item = KnowledgeItem(
            knowledge_id=knowledge_id,
            content=content,
            source=info.get("url", info.get("source", "unknown")),
            source_type=info.get("source", "unknown"),
            quality=KnowledgeQuality.FAIR,  # 初始质量等级
            extraction_method="automatic_extraction",
            tags=self._extract_tags_from_content(content),
            related_concepts=self._extract_concepts_from_content(content, targets)
        )
        
        return knowledge_item
    
    def _evaluate_knowledge_quality(self, knowledge_item: KnowledgeItem):
        """评估知识质量 - 多维度评估体系"""
        
        # 1. 置信度评估（基于来源可信度）
        confidence_score = self._assess_source_credibility(knowledge_item.source_type)
        
        # 2. 相关性评估（基于内容相关度）
        relevance_score = self._assess_content_relevance(knowledge_item.content)
        
        # 3. 新颖性评估（基于内容独特性）
        novelty_score = self._assess_content_novelty(knowledge_item.content)
        
        # 4. 综合质量评估
        overall_score = (confidence_score * 0.4 + 
                        relevance_score * 0.4 + 
                        novelty_score * 0.2)
        
        # 更新知识项评分
        knowledge_item.confidence_score = confidence_score
        knowledge_item.relevance_score = relevance_score
        knowledge_item.novelty_score = novelty_score
        
        # 确定质量等级
        if overall_score >= 0.8:
            knowledge_item.quality = KnowledgeQuality.EXCELLENT
        elif overall_score >= 0.6:
            knowledge_item.quality = KnowledgeQuality.GOOD
        elif overall_score >= 0.4:
            knowledge_item.quality = KnowledgeQuality.FAIR
        elif overall_score >= 0.2:
            knowledge_item.quality = KnowledgeQuality.POOR
        else:
            knowledge_item.quality = KnowledgeQuality.UNRELIABLE
        
        logger.debug(f"📊 质量评估完成: {knowledge_item.knowledge_id} - {knowledge_item.quality.value}")
    
    def _assess_source_credibility(self, source_type: str) -> float:
        """评估信息源可信度"""
        credibility_scores = {
            "web_search": 0.6,
            "academic_paper": 0.9,
            "expert_system": 0.8,
            "database": 0.7,
            "api_call": 0.6,
            "unknown": 0.3
        }
        return credibility_scores.get(source_type, 0.3)
    
    def _assess_content_relevance(self, content: str) -> float:
        """评估内容相关性（简化实现）"""
        # 基于内容长度和关键词密度的简单评估
        content_length = len(content)
        if content_length < 50:
            return 0.3
        elif content_length < 200:
            return 0.5
        elif content_length < 500:
            return 0.7
        else:
            return 0.8
    
    def _assess_content_novelty(self, content: str) -> float:
        """评估内容新颖性"""
        # 检查是否与已有知识重复
        for cached_item in list(self.knowledge_cache.values())[-10:]:  # 检查最近10项
            if self._calculate_content_similarity(content, cached_item.content) > 0.8:
                return 0.2  # 高度相似，新颖性低
        
        return 0.6  # 默认中等新颖性
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似性（简化实现）"""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _passes_quality_filter(self, knowledge_item: KnowledgeItem) -> bool:
        """知识质量过滤器"""
        min_confidence = self.config["quality_control"]["min_confidence_threshold"]
        min_relevance = self.config["quality_control"]["min_relevance_threshold"]
        
        return (knowledge_item.confidence_score >= min_confidence and
                knowledge_item.relevance_score >= min_relevance and
                knowledge_item.quality != KnowledgeQuality.UNRELIABLE)
    
    def _generate_thinking_seeds(self, 
                               knowledge_items: List[KnowledgeItem], 
                               strategy: ExplorationStrategy) -> List[ThinkingSeed]:
        """基于发现的知识生成思维种子"""
        thinking_seeds = []
        max_seeds = self.config["seed_generation"]["max_seeds_per_exploration"]
        
        # 按质量排序知识项
        sorted_knowledge = sorted(knowledge_items, 
                                key=lambda k: (k.confidence_score + k.relevance_score + k.novelty_score) / 3, 
                                reverse=True)
        
        # 为高质量知识生成种子
        for knowledge_item in sorted_knowledge[:max_seeds]:
            seed = self._create_thinking_seed_from_knowledge(knowledge_item, strategy)
            if seed:
                thinking_seeds.append(seed)
        
        # 生成跨知识融合种子
        if len(knowledge_items) >= 2:
            fusion_seeds = self._create_fusion_thinking_seeds(knowledge_items[:3], strategy)
            thinking_seeds.extend(fusion_seeds)
        
        # 限制种子数量
        thinking_seeds = thinking_seeds[:max_seeds]
        
        logger.info(f"🌱 思维种子生成完成: {len(thinking_seeds)} 个")
        return thinking_seeds
    
    def _create_thinking_seed_from_knowledge(self, 
                                           knowledge_item: KnowledgeItem, 
                                           strategy: ExplorationStrategy) -> Optional[ThinkingSeed]:
        """从单个知识项创建思维种子"""
        
        # 基于策略调整种子内容
        if strategy == ExplorationStrategy.TREND_MONITORING:
            seed_content = f"基于趋势监控发现：{knowledge_item.content[:100]}..."
            creativity_level = "medium"
        
        elif strategy == ExplorationStrategy.CROSS_DOMAIN_LEARNING:
            seed_content = f"跨域学习洞察：{knowledge_item.content[:100]}..."
            creativity_level = "high"
        
        elif strategy == ExplorationStrategy.GAP_ANALYSIS:
            seed_content = f"缺口分析发现：{knowledge_item.content[:100]}..."
            creativity_level = "medium"
        
        elif strategy == ExplorationStrategy.EXPERT_KNOWLEDGE:
            seed_content = f"专家知识洞察：{knowledge_item.content[:100]}..."
            creativity_level = "high"
        
        else:
            seed_content = f"探索发现：{knowledge_item.content[:100]}..."
            creativity_level = "medium"
        
        # 生成种子ID
        seed_id = f"seed_{knowledge_item.knowledge_id}_{int(time.time())}"
        
        # 创建思维种子
        thinking_seed = ThinkingSeed(
            seed_id=seed_id,
            seed_content=seed_content,
            source_knowledge=[knowledge_item.knowledge_id],
            creativity_level=creativity_level,
            potential_applications=self._suggest_applications(knowledge_item),
            generated_strategy=strategy.value,
            confidence=min(knowledge_item.confidence_score * 1.1, 1.0),  # 轻微提升
            suggested_reasoning_paths=self._suggest_reasoning_paths(knowledge_item, strategy),
            generation_context={
                "strategy": strategy.value,
                "source_quality": knowledge_item.quality.value,
                "generated_from": "single_knowledge_item"
            }
        )
        
        return thinking_seed
    
    def _create_fusion_thinking_seeds(self, 
                                    knowledge_items: List[KnowledgeItem], 
                                    strategy: ExplorationStrategy) -> List[ThinkingSeed]:
        """创建融合思维种子 - 整合多个知识项的创新种子"""
        fusion_seeds = []
        
        if len(knowledge_items) < 2:
            return fusion_seeds
        
        # 创建知识融合种子
        fusion_content = self._fuse_knowledge_contents(knowledge_items)
        fusion_id = f"fusion_seed_{int(time.time())}"
        
        fusion_seed = ThinkingSeed(
            seed_id=fusion_id,
            seed_content=f"融合洞察：{fusion_content}",
            source_knowledge=[k.knowledge_id for k in knowledge_items],
            creativity_level="high",  # 融合种子通常更有创意
            potential_applications=self._suggest_fusion_applications(knowledge_items),
            generated_strategy=strategy.value,
            confidence=sum(k.confidence_score for k in knowledge_items) / len(knowledge_items),
            cross_domain_connections=self._identify_cross_domain_connections(knowledge_items),
            generation_context={
                "strategy": strategy.value,
                "generated_from": "knowledge_fusion",
                "fusion_count": len(knowledge_items)
            }
        )
        
        fusion_seeds.append(fusion_seed)
        return fusion_seeds
    
    def _fuse_knowledge_contents(self, knowledge_items: List[KnowledgeItem]) -> str:
        """融合多个知识项的内容"""
        contents = [k.content[:50] for k in knowledge_items[:3]]  # 取前50字符
        return "、".join(contents) + " 的综合创新思路"
    
    def _suggest_applications(self, knowledge_item: KnowledgeItem) -> List[str]:
        """建议知识应用领域"""
        base_applications = [
            "问题解决策略",
            "创新思维路径",
            "决策优化方案"
        ]
        
        # 基于知识标签增加特定应用
        specific_applications = []
        for tag in knowledge_item.tags[:2]:
            specific_applications.append(f"{tag}相关应用")
        
        return base_applications + specific_applications
    
    def _suggest_reasoning_paths(self, 
                               knowledge_item: KnowledgeItem, 
                               strategy: ExplorationStrategy) -> List[str]:
        """建议推理路径"""
        base_paths = ["analytical_reasoning", "creative_synthesis"]
        
        strategy_specific_paths = {
            ExplorationStrategy.TREND_MONITORING: ["trend_analysis_path", "predictive_reasoning"],
            ExplorationStrategy.CROSS_DOMAIN_LEARNING: ["analogical_reasoning", "cross_domain_transfer"],
            ExplorationStrategy.GAP_ANALYSIS: ["problem_solving_path", "systematic_analysis"],
            ExplorationStrategy.DOMAIN_EXPANSION: ["exploratory_reasoning", "domain_bridging"],
            ExplorationStrategy.EXPERT_KNOWLEDGE: ["expert_reasoning_path", "professional_methodology"]
        }
        
        specific_paths = strategy_specific_paths.get(strategy, [])
        return base_paths + specific_paths
    
    def _suggest_fusion_applications(self, knowledge_items: List[KnowledgeItem]) -> List[str]:
        """建议融合知识的应用"""
        return [
            "跨领域创新解决方案",
            "综合决策优化策略",
            "多维度问题分析方法",
            "系统性思维升级路径"
        ]
    
    def _identify_cross_domain_connections(self, knowledge_items: List[KnowledgeItem]) -> List[str]:
        """识别跨域连接"""
        connections = []
        domains = set()
        
        # 从标签中提取领域信息
        for item in knowledge_items:
            domains.update(item.tags[:2])  # 取前2个标签作为领域
        
        # 生成跨域连接描述
        domain_list = list(domains)
        for i in range(len(domain_list)):
            for j in range(i+1, len(domain_list)):
                connections.append(f"{domain_list[i]}与{domain_list[j]}的融合创新")
        
        return connections[:3]  # 限制连接数量
    
    def _analyze_trends(self, 
                       knowledge_items: List[KnowledgeItem], 
                       targets: List[ExplorationTarget]) -> List[Dict[str, Any]]:
        """分析识别的趋势"""
        trends = []
        
        # 基于知识内容识别趋势关键词
        trend_keywords = self._extract_trend_keywords(knowledge_items)
        
        for keyword in trend_keywords[:3]:  # 限制趋势数量
            trend = {
                "trend_id": f"trend_{keyword}_{int(time.time())}",
                "trend_name": f"{keyword}相关趋势",
                "confidence": 0.6,
                "supporting_knowledge": [k.knowledge_id for k in knowledge_items 
                                       if keyword.lower() in k.content.lower()],
                "time_horizon": "short_term",
                "impact_prediction": f"{keyword}将在相关领域产生重要影响",
                "identified_at": time.time()
            }
            trends.append(trend)
        
        logger.info(f"📈 趋势分析完成: 识别 {len(trends)} 个趋势")
        return trends
    
    def _extract_trend_keywords(self, knowledge_items: List[KnowledgeItem]) -> List[str]:
        """提取趋势关键词"""
        keyword_frequency = defaultdict(int)
        
        for item in knowledge_items:
            words = item.content.lower().split()
            for word in words:
                if len(word) > 3:  # 过滤短词
                    keyword_frequency[word] += 1
        
        # 返回频次最高的关键词
        sorted_keywords = sorted(keyword_frequency.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:5] if freq > 1]
    
    def _discover_cross_domain_insights(self, 
                                      knowledge_items: List[KnowledgeItem], 
                                      thinking_seeds: List[ThinkingSeed]) -> List[Dict[str, Any]]:
        """发现跨域洞察"""
        insights = []
        
        # 基于思维种子的跨域连接
        for seed in thinking_seeds:
            if seed.cross_domain_connections:
                insight = {
                    "insight_id": f"cross_domain_{seed.seed_id}",
                    "insight_type": "cross_domain_connection",
                    "description": f"发现{seed.cross_domain_connections[0]}的创新机会",
                    "supporting_seeds": [seed.seed_id],
                    "potential_impact": "high",
                    "confidence": seed.confidence,
                    "discovered_at": time.time()
                }
                insights.append(insight)
        
        logger.info(f"🔗 跨域洞察发现完成: {len(insights)} 个洞察")
        return insights
    
    def _extract_tags_from_content(self, content: str) -> List[str]:
        """从内容中提取标签（简化实现）"""
        # 这里可以使用NLP技术进行关键词提取
        words = content.lower().split()
        tags = [word for word in words if len(word) > 4][:5]  # 简单取长词作为标签
        return tags
    
    def _extract_concepts_from_content(self, 
                                     content: str, 
                                     targets: List[ExplorationTarget]) -> List[str]:
        """从内容中提取相关概念"""
        concepts = []
        content_lower = content.lower()
        
        # 基于目标关键词提取相关概念
        for target in targets:
            for keyword in target.keywords:
                if keyword.lower() in content_lower:
                    concepts.append(keyword)
        
        return concepts[:3]  # 限制概念数量
    
    # ==================== 策略选择与优化 ====================
    
    def _select_optimal_strategy(self, targets: List[ExplorationTarget]) -> ExplorationStrategy:
        """基于目标和历史表现选择最优探索策略"""
        
        # 如果没有历史数据，使用默认策略
        if not self.strategy_performance:
            return self.config["exploration_strategies"]["default_strategy"]
        
        # 基于历史表现选择策略
        best_strategy = None
        best_score = 0.0
        
        for strategy_name, performance in self.strategy_performance.items():
            # 综合评分：成功率 * 0.6 + 平均质量 * 0.4
            score = (performance["success_rate"] * 0.6 + 
                    performance["avg_quality"] * 0.4)
            
            if score > best_score:
                best_score = score
                try:
                    best_strategy = ExplorationStrategy(strategy_name)
                except ValueError:
                    continue
        
        return best_strategy or self.config["exploration_strategies"]["default_strategy"]
    
    def _calculate_success_rate(self, result: ExplorationResult) -> float:
        """计算探索成功率"""
        if not result.targets:
            return 0.0
        
        successful_targets = 0
        for target in result.targets:
            # 如果目标产生了知识或种子，视为成功
            target_knowledge = [k for k in result.discovered_knowledge 
                              if target.target_id in k.related_concepts]
            target_seeds = [s for s in result.generated_seeds 
                          if any(target.target_id in s.generation_context.get("related_targets", []))]
            
            if target_knowledge or target_seeds:
                successful_targets += 1
        
        return successful_targets / len(result.targets)
    
    def _calculate_quality_score(self, result: ExplorationResult) -> float:
        """计算整体质量评分"""
        if not result.discovered_knowledge:
            return 0.0
        
        total_score = 0.0
        for knowledge in result.discovered_knowledge:
            knowledge_score = (knowledge.confidence_score + 
                             knowledge.relevance_score + 
                             knowledge.novelty_score) / 3
            total_score += knowledge_score
        
        return total_score / len(result.discovered_knowledge)
    
    def _update_caches_and_stats(self, result: ExplorationResult):
        """更新缓存和统计信息"""
        # 更新探索历史
        self.exploration_history.append(result)
        
        # 更新知识缓存
        for knowledge in result.discovered_knowledge:
            self.knowledge_cache[knowledge.knowledge_id] = knowledge
        
        # 更新种子缓存
        for seed in result.generated_seeds:
            self.seed_cache[seed.seed_id] = seed
        
        # 更新策略性能
        strategy_name = result.strategy.value
        self.strategy_performance[strategy_name]["success_rate"] = (
            (self.strategy_performance[strategy_name]["success_rate"] + result.success_rate) / 2
        )
        self.strategy_performance[strategy_name]["avg_quality"] = (
            (self.strategy_performance[strategy_name]["avg_quality"] + result.quality_score) / 2
        )
        self.strategy_performance[strategy_name]["total_seeds"] += len(result.generated_seeds)
        
        # 更新全局统计
        self.stats["total_explorations"] += 1
        if result.success_rate > 0.5:
            self.stats["successful_explorations"] += 1
        self.stats["total_knowledge_discovered"] += len(result.discovered_knowledge)
        self.stats["total_seeds_generated"] += len(result.generated_seeds)
        
        # 更新平均值
        total_explorations = self.stats["total_explorations"]
        self.stats["average_quality_score"] = (
            (self.stats["average_quality_score"] * (total_explorations - 1) + result.quality_score) / 
            total_explorations
        )
        self.stats["average_execution_time"] = (
            (self.stats["average_execution_time"] * (total_explorations - 1) + result.execution_time) / 
            total_explorations
        )
        
        # 清理过期缓存
        self._cleanup_caches()
    
    def _cleanup_caches(self):
        """清理过期缓存"""
        max_history = 100
        max_knowledge_cache = 500
        max_seed_cache = 300
        
        # 清理探索历史
        if len(self.exploration_history) > max_history:
            self.exploration_history = self.exploration_history[-max_history//2:]
        
        # 清理知识缓存（保留最新的）
        if len(self.knowledge_cache) > max_knowledge_cache:
            sorted_knowledge = sorted(
                self.knowledge_cache.items(),
                key=lambda x: x[1].discovered_at,
                reverse=True
            )
            self.knowledge_cache = dict(sorted_knowledge[:max_knowledge_cache//2])
        
        # 清理种子缓存（保留最新的）
        if len(self.seed_cache) > max_seed_cache:
            sorted_seeds = sorted(
                self.seed_cache.items(),
                key=lambda x: x[1].generated_at,
                reverse=True
            )
            self.seed_cache = dict(sorted_seeds[:max_seed_cache//2])
    
    # ==================== 公共接口方法 ====================
    
    def create_exploration_targets_from_context(self, 
                                              context: Dict[str, Any]) -> List[ExplorationTarget]:
        """基于上下文创建探索目标"""
        targets = []
        
        # 从上下文提取关键信息
        session_insights = context.get("session_insights", {})
        knowledge_gaps = context.get("current_knowledge_gaps", [])
        
        # 基于知识缺口创建目标
        for gap in knowledge_gaps[:3]:  # 限制目标数量
            target = ExplorationTarget(
                target_id=f"gap_target_{gap.get('gap_id', 'unknown')}",
                target_type="knowledge_gap",
                description=gap.get("description", "知识缺口探索"),
                keywords=gap.get("keywords", [gap.get("area", "")]),
                priority=gap.get("exploration_priority", 0.5)
            )
            targets.append(target)
        
        # 如果没有明确的缺口，创建通用探索目标
        if not targets:
            general_target = ExplorationTarget(
                target_id=f"general_target_{int(time.time())}",
                target_type="general_exploration",
                description="通用知识探索",
                keywords=["技术趋势", "创新方法", "最佳实践"],
                priority=0.6
            )
            targets.append(general_target)
        
        return targets
    
    def get_exploration_stats(self) -> Dict[str, Any]:
        """获取探索统计信息"""
        return {
            **self.stats,
            "strategy_performance": dict(self.strategy_performance),
            "cache_status": {
                "knowledge_cache_size": len(self.knowledge_cache),
                "seed_cache_size": len(self.seed_cache),
                "exploration_history_size": len(self.exploration_history)
            },
            "recent_explorations": len([r for r in self.exploration_history 
                                      if time.time() - r.timestamp < 3600])  # 最近1小时
        }
    
    def _merge_config(self, base_config: Dict, user_config: Dict):
        """递归合并配置"""
        for key, value in user_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value
