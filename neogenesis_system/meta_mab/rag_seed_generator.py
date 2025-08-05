
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAG种子生成器 - 基于检索增强生成的智能思维种子创建器
RAG Seed Generator - Intelligent thinking seed creator based on Retrieval-Augmented Generation

核心职责：
1. 理解问题并构思搜索策略：分析用户查询，生成精准搜索关键词
2. 执行网络搜索：调用WebSearchClient获取实时信息
3. 综合信息生成种子：结合用户问题和搜索结果，生成基于事实的思维种子

技术特色：
- 基于Anthropic的contextual retrieval理念
- 多源信息验证和交叉引用
- 上下文感知的信息整合
- 实时信息获取能力
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils.search_client import WebSearchClient, SearchResult, SearchResponse
# from .utils.client_adapter import DeepSeekClientAdapter  # 不再需要，使用依赖注入
from .utils.common_utils import parse_json_response
from config import PROMPT_TEMPLATES, RAG_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class RAGSearchStrategy:
    """RAG搜索策略数据结构"""
    primary_keywords: List[str]      # 主要关键词
    secondary_keywords: List[str]    # 次要关键词  
    search_intent: str              # 搜索意图
    domain_focus: str               # 领域聚焦
    information_types: List[str]    # 需要的信息类型
    search_depth: str               # 搜索深度 (shallow/medium/deep)


@dataclass
class RAGInformationSynthesis:
    """RAG信息综合结果"""
    contextual_seed: str            # 上下文感知的思维种子
    information_sources: List[str]  # 信息来源
    confidence_score: float         # 信息可信度
    key_insights: List[str]         # 关键洞察
    knowledge_gaps: List[str]       # 知识缺口
    verification_status: str        # 验证状态


class RAGSeedGenerator:
    """
    RAG种子生成器 - 专门负责基于实时信息检索的思维种子生成
    
    设计理念：
    - 采用"理解-搜索-综合"三阶段流程
    - 实现上下文感知的信息检索
    - 多源信息验证和交叉引用
    - 生成具有丰富上下文的思维种子
    """
    
    def __init__(self, api_key: str = "", search_engine: str = "duckduckgo", 
                 web_search_client=None, llm_client=None):
        """
        初始化RAG种子生成器
        
        Args:
            api_key: LLM API密钥（向后兼容）
            search_engine: 搜索引擎类型（向后兼容）
            web_search_client: 共享的Web搜索客户端（依赖注入）
            llm_client: 共享的LLM客户端（依赖注入）
        """
        self.api_key = api_key
        self.search_engine = search_engine
        
        # 🔧 依赖注入：优先使用传入的搜索客户端
        if web_search_client:
            self.web_search_client = web_search_client
            logger.info("🔍 RAG种子生成器使用共享搜索客户端")
        else:
            # 向后兼容：创建自己的搜索客户端
            self.web_search_client = WebSearchClient(
                search_engine=search_engine, 
                max_results=RAG_CONFIG.get("max_search_results", 8)
            )
            logger.info("🔍 RAG种子生成器创建独立搜索客户端")
        
        # 🔧 依赖注入：使用传入的LLM客户端（纯依赖注入模式）
        self.llm_client = llm_client
        if self.llm_client:
            logger.info("🧠 RAG种子生成器使用共享LLM客户端")
        else:
            logger.warning("⚠️ 未提供LLM客户端，RAG将运行在仅搜索模式")
            logger.info("💡 请确保从上层（MainController）传入有效的llm_client")
        
        # 性能统计和缓存
        self.performance_stats = {
            'total_generations': 0,
            'successful_generations': 0,
            'avg_generation_time': 0.0,
            'search_success_rate': 0.0,
            'synthesis_success_rate': 0.0
        }
        
        # 搜索策略缓存
        self.strategy_cache = {}  # 查询模式 -> 搜索策略
        self.information_cache = {}  # 关键词 -> 搜索结果
        self.synthesis_cache = {}  # 查询+信息哈希 -> 综合结果
        
        # RAG质量跟踪
        self.rag_quality_metrics = {
            'information_diversity': defaultdict(float),  # 信息多样性
            'source_reliability': defaultdict(float),    # 来源可靠性
            'contextual_relevance': defaultdict(float),  # 上下文相关性
            'factual_accuracy': defaultdict(float)       # 事实准确性
        }
        
        logger.info("🚀 RAG种子生成器初始化完成")
        logger.info(f"   🔍 搜索引擎: {search_engine}")
        logger.info(f"   🧠 AI分析: {'启用' if self.llm_client else '禁用'}")
    
    def generate_rag_seed(self, user_query: str, execution_context: Optional[Dict] = None) -> str:
        """
        生成基于RAG的思维种子 - 三阶段核心流程
        
        Args:
            user_query: 用户查询
            execution_context: 执行上下文
            
        Returns:
            基于实时信息的思维种子
        """
        start_time = time.time()
        self.performance_stats['total_generations'] += 1
        
        logger.info(f"🎯 开始RAG种子生成: {user_query[:50]}...")
        
        try:
            # 阶段一：理解问题并构思搜索策略
            search_strategy = self._analyze_and_plan_search(user_query, execution_context)
            logger.info(f"📋 搜索策略: {search_strategy.search_intent}")
            
            # 阶段二：执行网络搜索
            search_results = self._execute_web_search(search_strategy)
            logger.info(f"🔍 搜索完成: 获取 {len(search_results)} 条结果")
            
            # 阶段三：综合信息并生成种子
            synthesis_result = self._synthesize_information(
                user_query, search_strategy, search_results, execution_context
            )
            
            # 更新性能统计
            generation_time = time.time() - start_time
            self.performance_stats['successful_generations'] += 1
            self._update_performance_stats(generation_time)
            
            logger.info(f"✅ RAG种子生成成功 (耗时: {generation_time:.2f}s)")
            logger.info(f"   📊 信息可信度: {synthesis_result.confidence_score:.2f}")
            logger.info(f"   📚 信息源数量: {len(synthesis_result.information_sources)}")
            
            return synthesis_result.contextual_seed
            
        except Exception as e:
            logger.error(f"❌ RAG种子生成失败: {e}")
            # 回退到基础分析模式
            return self._generate_fallback_seed(user_query, execution_context)
    
    def _analyze_and_plan_search(self, user_query: str, execution_context: Optional[Dict]) -> RAGSearchStrategy:
        """
        阶段一：分析用户问题并规划搜索策略
        
        核心任务：
        1. 理解用户问题的核心意图
        2. 识别关键概念和实体
        3. 确定搜索领域和信息类型
        4. 生成多层次搜索关键词
        
        Args:
            user_query: 用户查询
            execution_context: 执行上下文
            
        Returns:
            搜索策略对象
        """
        # 检查策略缓存
        cache_key = f"{user_query}_{hash(str(execution_context))}"
        if cache_key in self.strategy_cache:
            logger.debug("📋 使用缓存的搜索策略")
            return self.strategy_cache[cache_key]
        
        if self.llm_client:
            try:
                return self._llm_based_search_planning(user_query, execution_context)
            except Exception as e:
                logger.warning(f"⚠️ LLM搜索规划失败，使用启发式方法: {e}")
        
        # 启发式搜索策略生成
        return self._heuristic_search_planning(user_query, execution_context)
    
    def _llm_based_search_planning(self, user_query: str, execution_context: Optional[Dict]) -> RAGSearchStrategy:
        """使用LLM进行智能搜索策略规划"""
        
        # 检查缓存
        cache_key = f"{user_query}_{hash(str(execution_context))}"
        if cache_key in self.strategy_cache:
            logger.debug("📋 使用缓存的LLM搜索策略")
            return self.strategy_cache[cache_key]
        
        context_info = ""
        if execution_context:
            context_items = [f"- {k}: {v}" for k, v in execution_context.items()]
            context_info = f"\n\n📋 **执行上下文**:\n" + "\n".join(context_items)
        
        planning_prompt = f"""
作为一个专业的信息检索策略师，请为以下用户问题制定精准的搜索策略。

🎯 **用户问题**: {user_query}
{context_info}

📝 **任务要求**:
1. 深度理解用户问题的核心意图和信息需求
2. 识别关键概念、实体和技术术语
3. 确定最佳搜索领域和信息类型
4. 生成多层次、多角度的搜索关键词组合
5. 评估搜索深度需求

🔍 **输出格式** (严格按照JSON格式):
```json
{{
    "search_intent": "用户搜索的核心意图描述",
    "domain_focus": "主要领域（如：技术、商业、学术、新闻等）",
    "primary_keywords": ["主要关键词1", "主要关键词2", "主要关键词3"],
    "secondary_keywords": ["补充关键词1", "补充关键词2"],
    "information_types": ["需要的信息类型，如：定义、教程、案例、统计数据"],
    "search_depth": "shallow/medium/deep（搜索深度）"
}}
```

请基于问题的复杂性和时效性需求，制定最优的搜索策略。
"""
        
        llm_response = self.llm_client.call_api(planning_prompt, temperature=0.3)
        strategy_data = parse_json_response(llm_response)
        
        # 检查是否包含有效的搜索策略字段
        required_fields = ['search_intent', 'domain_focus', 'primary_keywords']
        if strategy_data and all(field in strategy_data for field in required_fields):
            strategy = RAGSearchStrategy(
                primary_keywords=strategy_data.get('primary_keywords', []),
                secondary_keywords=strategy_data.get('secondary_keywords', []),
                search_intent=strategy_data.get('search_intent', ''),
                domain_focus=strategy_data.get('domain_focus', 'general'),
                information_types=strategy_data.get('information_types', []),
                search_depth=strategy_data.get('search_depth', 'medium')
            )
            
            # 缓存策略
            self.strategy_cache[cache_key] = strategy
            
            return strategy
        else:
            raise ValueError("LLM搜索策略解析失败")
    
    def _heuristic_search_planning(self, user_query: str, execution_context: Optional[Dict]) -> RAGSearchStrategy:
        """基于启发式规则的搜索策略生成"""
        
        # 基础关键词提取
        import re
        words = re.findall(r'\b\w+\b', user_query.lower())
        
        # 技术术语识别（包含中英文）
        tech_terms = [
            'api', 'algorithm', 'database', 'system', 'architecture', 'optimization',
            'machine learning', 'ml', 'ai', 'artificial intelligence', 'deep learning',
            'network', 'crawler', 'data analysis', 'real-time', 'performance',
            'rag', 'retrieval', 'generation', 'llm', 'transformer',
            # 中文技术术语
            '机器学习', '算法', '架构', '数据库', '系统', '优化', '人工智能',
            '深度学习', '网络', '性能', '分布式', '实时', '高性能'
        ]
        
        primary_keywords = []
        secondary_keywords = []
        
        # 识别技术关键词
        for term in tech_terms:
            if term in user_query.lower():
                primary_keywords.append(term)
        
        # 添加原始查询的主要词汇
        important_words = [w for w in words if len(w) > 3][:5]
        primary_keywords.extend(important_words)
        
        # 去重
        primary_keywords = list(set(primary_keywords))[:6]
        
        # 确定领域和意图
        if any(term in user_query.lower() for term in ['how', 'what', 'why', '如何', '什么', '为什么']):
            search_intent = "寻找解释或指导信息"
            information_types = ["教程", "定义", "指南"]
        elif any(term in user_query.lower() for term in ['best', 'compare', '最好', '比较']):
            search_intent = "寻找比较和推荐信息"
            information_types = ["比较", "评测", "推荐"]
        else:
            search_intent = "寻找相关事实信息"
            information_types = ["事实", "数据", "案例"]
        
        # 判断搜索深度
        if len(user_query) > 100 or any(term in user_query.lower() for term in ['complex', 'advanced', '复杂', '高级']):
            search_depth = "deep"
        elif len(user_query) < 30:
            search_depth = "shallow"
        else:
            search_depth = "medium"
        
        return RAGSearchStrategy(
            primary_keywords=primary_keywords,
            secondary_keywords=secondary_keywords,
            search_intent=search_intent,
            domain_focus="技术" if any(t in primary_keywords for t in tech_terms) else "通用",
            information_types=information_types,
            search_depth=search_depth
        )
    
    def _execute_web_search(self, strategy: RAGSearchStrategy) -> List[SearchResult]:
        """
        阶段二：执行网络搜索（支持并行优化）
        
        核心任务：
        1. 基于搜索策略执行多轮搜索
        2. 组合不同关键词进行全面检索
        3. 过滤和去重搜索结果
        4. 按相关性排序
        
        🚀 性能优化：
        - 支持并行搜索，大幅缩短总耗时
        - 智能配置并发数量
        - 完整的错误处理和降级
        
        Args:
            strategy: 搜索策略
            
        Returns:
            搜索结果列表
        """
        all_results = []
        search_queries = []
        
        # 构建搜索查询
        # 主要关键词组合
        for keyword in strategy.primary_keywords[:3]:  # 限制主要搜索次数
            search_queries.append(keyword)
        
        # 组合查询（主要+次要关键词）
        if strategy.secondary_keywords:
            for primary in strategy.primary_keywords[:2]:
                for secondary in strategy.secondary_keywords[:2]:
                    search_queries.append(f"{primary} {secondary}")
        
        # 限制总搜索次数
        search_queries = search_queries[:5]
        
        logger.info(f"🔍 执行 {len(search_queries)} 轮搜索查询")
        
        # 🚀 决定使用并行搜索还是串行搜索
        enable_parallel = RAG_CONFIG.get("enable_parallel_search", True)
        max_workers = RAG_CONFIG.get("max_search_workers", 3)
        
        if enable_parallel and len(search_queries) > 1:
            logger.info(f"⚡ 启用并行搜索模式 - 最大并发数: {max_workers}")
            all_results = self._execute_parallel_search(search_queries, max_workers)
        else:
            logger.info("📊 使用传统串行搜索模式")
            all_results = self._execute_serial_search(search_queries)
        
        # 去重和过滤
        unique_results = self._filter_and_deduplicate_results(all_results, strategy)
        
        logger.info(f"🎯 搜索完成: {len(all_results)} -> {len(unique_results)} (去重后)")
        return unique_results
    
    def _execute_parallel_search(self, search_queries: List[str], max_workers: int) -> List[SearchResult]:
        """
        并行执行多个搜索查询
        
        Args:
            search_queries: 搜索查询列表
            max_workers: 最大并发工作线程数
            
        Returns:
            搜索结果列表
        """
        all_results = []
        start_time = time.time()
        
        # 创建搜索任务
        def search_single_query(query: str) -> Tuple[str, List[SearchResult]]:
            """执行单个搜索查询"""
            try:
                logger.debug(f"   🔍 并行搜索: {query}")
                response = self.web_search_client.search(query)
                
                if response and response.results:
                    logger.debug(f"   ✅ 搜索成功: {query} -> {len(response.results)} 条结果")
                    return query, response.results
                else:
                    logger.debug(f"   🔍 搜索无结果: {query}")
                    return query, []
                    
            except Exception as e:
                logger.warning(f"⚠️ 搜索失败 '{query}': {e}")
                return query, []
        
        # 使用线程池并行执行搜索
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有搜索任务
            future_to_query = {
                executor.submit(search_single_query, query): query 
                for query in search_queries
            }
            
            # 收集结果
            completed_count = 0
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    query_name, results = future.result()
                    all_results.extend(results)
                    completed_count += 1
                    
                    logger.debug(f"✅ 搜索完成 ({completed_count}/{len(search_queries)}): {query_name}")
                    
                except Exception as e:
                    logger.error(f"❌ 搜索任务执行失败: {query} - {e}")
        
        duration = time.time() - start_time
        logger.info(f"🎯 并行搜索完成 - 耗时: {duration:.2f}s, 获得 {len(all_results)} 条结果")
        
        return all_results
    
    def _execute_serial_search(self, search_queries: List[str]) -> List[SearchResult]:
        """
        串行执行搜索查询（兼容模式）
        
        Args:
            search_queries: 搜索查询列表
            
        Returns:
            搜索结果列表
        """
        all_results = []
        
        for query in search_queries:
            try:
                logger.debug(f"   搜索: {query}")
                response = self.web_search_client.search(query)
                
                if response and response.results:
                    all_results.extend(response.results)
                    logger.debug(f"   获得 {len(response.results)} 条结果")
                else:
                    logger.debug(f"   搜索无结果: {query}")
                    
            except Exception as e:
                logger.warning(f"⚠️ 搜索失败 '{query}': {e}")
                continue
        
        return all_results
    
    def _filter_and_deduplicate_results(self, results: List[SearchResult], 
                                       strategy: RAGSearchStrategy) -> List[SearchResult]:
        """过滤和去重搜索结果"""
        if not results:
            return []
        
        # 按URL去重
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # 按相关性排序（基于标题和摘要中关键词匹配度）
        def relevance_score(result: SearchResult) -> float:
            score = 0.0
            text = f"{result.title} {result.snippet}".lower()
            
            # 主要关键词权重更高
            for keyword in strategy.primary_keywords:
                if keyword.lower() in text:
                    score += 2.0
            
            # 次要关键词权重较低
            for keyword in strategy.secondary_keywords:
                if keyword.lower() in text:
                    score += 1.0
            
            return score
        
        # 排序并返回前N个结果
        unique_results.sort(key=relevance_score, reverse=True)
        return unique_results[:8]  # 返回最相关的8个结果
    
    def _synthesize_information(self, user_query: str, strategy: RAGSearchStrategy, 
                               search_results: List[SearchResult], 
                               execution_context: Optional[Dict]) -> RAGInformationSynthesis:
        """
        阶段三：综合信息并生成思维种子
        
        核心任务：
        1. 分析所有搜索结果的内容
        2. 识别关键信息和洞察
        3. 验证信息一致性和可靠性
        4. 生成上下文丰富的思维种子
        
        Args:
            user_query: 用户查询
            strategy: 搜索策略
            search_results: 搜索结果
            execution_context: 执行上下文
            
        Returns:
            信息综合结果
        """
        if not search_results:
            logger.warning("⚠️ 无搜索结果，生成基础种子")
            return RAGInformationSynthesis(
                contextual_seed=f"基于用户问题'{user_query}'的基础分析。由于缺乏实时信息，建议进一步调研相关资料。",
                information_sources=[],
                confidence_score=0.3,
                key_insights=["需要更多信息"],
                knowledge_gaps=["实时数据缺失"],
                verification_status="insufficient_data"
            )
        
        if self.llm_client:
            try:
                return self._llm_based_synthesis(user_query, strategy, search_results, execution_context)
            except Exception as e:
                logger.warning(f"⚠️ LLM信息综合失败，使用基础方法: {e}")
        
        # 基础信息综合
        return self._basic_information_synthesis(user_query, strategy, search_results)
    
    def _llm_based_synthesis(self, user_query: str, strategy: RAGSearchStrategy,
                            search_results: List[SearchResult], 
                            execution_context: Optional[Dict]) -> RAGInformationSynthesis:
        """使用LLM进行高级信息综合"""
        
        # 构建搜索结果摘要
        results_summary = []
        for i, result in enumerate(search_results[:6], 1):  # 限制结果数量避免token超限
            results_summary.append(f"""
**来源 {i}**: {result.title}
- URL: {result.url}  
- 摘要: {result.snippet}
""")
        
        context_info = ""
        if execution_context:
            context_items = [f"- {k}: {v}" for k, v in execution_context.items()]
            context_info = f"\n\n📋 **执行上下文**:\n" + "\n".join(context_items)
        
        synthesis_prompt = f"""
作为一个专业的信息分析师，请基于用户问题和搜索到的实时信息，生成一个全面、客观、基于事实的思维种子。

🎯 **用户问题**: {user_query}

🔍 **搜索策略**: {strategy.search_intent}
**关注领域**: {strategy.domain_focus}

📚 **搜索结果**:
{"".join(results_summary)}
{context_info}

📝 **综合要求**:
1. **上下文感知**: 充分理解用户问题的背景和意图
2. **事实基础**: 基于搜索结果的真实信息，避免猜测
3. **信息整合**: 将多个来源的信息进行有机整合
4. **关键洞察**: 提取最重要的观点和发现
5. **知识缺口**: 识别信息不足或需要进一步验证的领域
6. **实用导向**: 生成对后续决策有帮助的思考方向

🎯 **输出格式** (严格按照JSON格式):
```json
{{
    "contextual_seed": "基于实时信息的全面思维种子（200-400字）",
    "key_insights": ["关键洞察1", "关键洞察2", "关键洞察3"],
    "knowledge_gaps": ["需要进一步了解的方面1", "需要进一步了解的方面2"],
    "confidence_score": 0.85,
    "information_sources": ["可靠来源1", "可靠来源2"],
    "verification_status": "verified/partially_verified/needs_verification"
}}
```

请确保生成的思维种子具有丰富的上下文信息，能够为后续的思维路径选择提供坚实的事实基础。
"""
        
        llm_response = self.llm_client.call_api(synthesis_prompt, temperature=0.4)
        synthesis_data = parse_json_response(llm_response)
        
        if synthesis_data:
            return RAGInformationSynthesis(
                contextual_seed=synthesis_data.get('contextual_seed', ''),
                information_sources=synthesis_data.get('information_sources', []),
                confidence_score=float(synthesis_data.get('confidence_score', 0.5)),
                key_insights=synthesis_data.get('key_insights', []),
                knowledge_gaps=synthesis_data.get('knowledge_gaps', []),
                verification_status=synthesis_data.get('verification_status', 'unknown')
            )
        else:
            raise ValueError("LLM信息综合解析失败")
    
    def _basic_information_synthesis(self, user_query: str, strategy: RAGSearchStrategy,
                                   search_results: List[SearchResult]) -> RAGInformationSynthesis:
        """基础信息综合方法"""
        
        # 提取关键信息
        all_snippets = [result.snippet for result in search_results if result.snippet]
        all_titles = [result.title for result in search_results if result.title]
        
        # 生成基础种子
        seed_parts = [
            f"基于对'{user_query}'的搜索调研，",
            f"从{len(search_results)}个信息源获得以下关键信息：",
        ]
        
        # 添加主要信息点
        for i, snippet in enumerate(all_snippets[:3], 1):
            seed_parts.append(f"{i}. {snippet[:100]}...")
        
        # 添加结论
        seed_parts.append(f"这些信息表明{strategy.search_intent.lower()}的重要性，")
        seed_parts.append("建议在制定解决方案时充分考虑这些实时信息。")
        
        contextual_seed = " ".join(seed_parts)
        
        return RAGInformationSynthesis(
            contextual_seed=contextual_seed,
            information_sources=[result.url for result in search_results[:3]],
            confidence_score=0.6,
            key_insights=all_titles[:3],
            knowledge_gaps=["需要更详细的分析"],
            verification_status="basic_verified"
        )
    
    def _generate_fallback_seed(self, user_query: str, execution_context: Optional[Dict]) -> str:
        """生成回退思维种子"""
        logger.info("🔄 使用回退模式生成思维种子")
        
        fallback_seed = f"""
基于对问题'{user_query}'的分析，这是一个需要综合考虑的问题。
虽然当前无法获取实时信息，但可以从以下角度进行思考：
1. 问题的核心要求和约束条件
2. 可能的解决方案和实现路径  
3. 需要考虑的风险和挑战
4. 相关的最佳实践和经验
建议在具体实施前获取最新的相关信息和数据。
"""
        return fallback_seed.strip()
    
    def _update_performance_stats(self, generation_time: float):
        """更新性能统计"""
        total = self.performance_stats['total_generations']
        current_avg = self.performance_stats['avg_generation_time']
        
        # 计算移动平均时间
        if total == 1:
            self.performance_stats['avg_generation_time'] = generation_time
        else:
            self.performance_stats['avg_generation_time'] = (
                current_avg * (total - 1) + generation_time
            ) / total
        
        # 更新成功率
        success_count = self.performance_stats['successful_generations']
        self.performance_stats['search_success_rate'] = success_count / total
    
    def get_rag_performance_stats(self) -> Dict[str, Any]:
        """获取RAG性能统计"""
        return {
            'component': 'RAG_Seed_Generator',
            'performance_stats': self.performance_stats.copy(),
            'cache_stats': {
                'strategy_cache_size': len(self.strategy_cache),
                'information_cache_size': len(self.information_cache),
                'synthesis_cache_size': len(self.synthesis_cache)
            },
            'quality_metrics': {
                'information_diversity': dict(self.rag_quality_metrics['information_diversity']),
                'source_reliability': dict(self.rag_quality_metrics['source_reliability']),
                'contextual_relevance': dict(self.rag_quality_metrics['contextual_relevance'])
            }
        }
    
    def clear_cache(self):
        """清空所有缓存"""
        self.strategy_cache.clear()
        self.information_cache.clear() 
        self.synthesis_cache.clear()
        logger.info("🧹 RAG种子生成器缓存已清空")
