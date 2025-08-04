#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索工具客户端 - 用于连接外部搜索引擎
Search Tool Client - for connecting to external search engines
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests

# 🔧 新增：支持真实DuckDuckGo搜索
try:
    from duckduckgo_search import DDGS
    REAL_SEARCH_AVAILABLE = True
except ImportError:
    REAL_SEARCH_AVAILABLE = False
    logging.warning("⚠️ duckduckgo-search库未安装，将使用模拟搜索结果")

# 导入配置
try:
    from config import RAG_CONFIG
except ImportError:
    # 默认配置（如果无法导入）
    RAG_CONFIG = {"enable_real_web_search": False}

logger = logging.getLogger(__name__)

# 全局搜索请求管理器，用于控制请求频率
class SearchRateLimiter:
    """搜索速率限制管理器"""
    def __init__(self):
        self.last_request_time = 0
        # 从配置获取请求间隔，如果配置不存在则使用默认值
        self.min_interval = RAG_CONFIG.get("search_rate_limit_interval", 1.5)
    
    def wait_if_needed(self):
        """如果需要，等待到下一个允许的请求时间"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            logger.debug(f"⏳ 速率限制等待: {wait_time:.1f}秒")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()

# 全局速率限制器实例
_rate_limiter = SearchRateLimiter()

@dataclass
class SearchResult:
    """搜索结果数据结构"""
    title: str
    snippet: str
    url: str
    relevance_score: float = 0.0

@dataclass
class SearchResponse:
    """搜索响应数据结构"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float
    success: bool = True
    error_message: str = ""

@dataclass
class IdeaVerificationResult:
    """想法验证结果数据结构"""
    idea_text: str
    feasibility_score: float
    analysis_summary: str
    search_results: List[SearchResult]
    success: bool = True
    error_message: str = ""

class WebSearchClient:
    """网络搜索客户端"""
    
    def __init__(self, search_engine: str = "duckduckgo", max_results: int = 5):
        """
        初始化搜索客户端
        
        Args:
            search_engine: 搜索引擎类型 ("duckduckgo", "bing", "google")
            max_results: 最大结果数量
        """
        self.search_engine = search_engine
        self.max_results = max_results
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 搜索统计
        self.search_stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'total_search_time': 0.0,
            'avg_search_time': 0.0
        }
        
        logger.info(f"🔍 WebSearchClient初始化完成 - 使用{search_engine}搜索引擎")
    
    def search(self, query: str, max_results: Optional[int] = None) -> SearchResponse:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数量（覆盖默认值）
            
        Returns:
            SearchResponse: 搜索响应
        """
        start_time = time.time()
        max_results = max_results or self.max_results
        
        logger.info(f"🔍 开始搜索: {query[:50]}...")
        
        try:
            if self.search_engine == "duckduckgo":
                response = self._search_duckduckgo(query, max_results)
            elif self.search_engine == "bing":
                response = self._search_bing(query, max_results)
            else:
                response = self._search_fallback(query, max_results)
            
            search_time = time.time() - start_time
            response.search_time = search_time
            
            # 更新统计
            self._update_search_stats(search_time, response.success)
            
            logger.info(f"🔍 搜索完成: 找到{len(response.results)}个结果，耗时{search_time:.2f}秒")
            return response
            
        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"❌ 搜索失败: {e}")
            
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_time=search_time,
                success=False,
                error_message=str(e)
            )
    
    def _search_duckduckgo(self, query: str, max_results: int) -> SearchResponse:
        """使用DuckDuckGo搜索 - 带智能备用机制"""
        
        # 🔧 检查是否启用真实搜索
        if RAG_CONFIG.get("enable_real_web_search", False) and REAL_SEARCH_AVAILABLE:
            # 尝试真实搜索
            response = self._search_duckduckgo_real(query, max_results)
            
            # 如果真实搜索失败，检查是否应该暂时禁用真实搜索
            if not response.success:
                logger.warning(f"🚨 DuckDuckGo真实搜索持续失败，建议暂时切换到模拟搜索模式")
                logger.info(f"💡 解决方案：在config.py中设置 'enable_real_web_search': False")
            
            return response
        else:
            return self._search_duckduckgo_mock(query, max_results)
    
    def _search_duckduckgo_real(self, query: str, max_results: int) -> SearchResponse:
        """真实的DuckDuckGo搜索 - 带速率限制处理和重试机制"""
        max_retries = RAG_CONFIG.get("search_max_retries", 3)
        base_delay = RAG_CONFIG.get("search_retry_base_delay", 1.0)
        
        for attempt in range(max_retries):
            try:
                # 应用全局速率限制
                _rate_limiter.wait_if_needed()
                
                # 添加额外的请求间隔以避免速率限制
                if attempt > 0:
                    delay = base_delay * (2 ** attempt)  # 指数退避
                    logger.info(f"⏳ 第{attempt + 1}次尝试，等待{delay:.1f}秒...")
                    time.sleep(delay)
                
                logger.info(f"🌐 开始真实DuckDuckGo搜索: {query} (尝试 {attempt + 1}/{max_retries})")
                search_start_time = time.time()
                
                # 使用最保守的搜索配置避免速率限制
                with DDGS() as ddgs:
                    # 执行搜索，使用默认后端自动选择
                    ddgs_results = list(ddgs.text(
                        keywords=query,
                        max_results=max_results,
                        region='wt-wt',  # 全球搜索
                        safesearch='moderate',
                        timelimit=None
                        # 不指定backend，让系统自动选择最稳定的
                    ))
                
                search_time = time.time() - search_start_time
                
                # 转换结果格式
                results = []
                for result in ddgs_results:
                    results.append(SearchResult(
                        title=result.get('title', ''),
                        snippet=result.get('body', ''),
                        url=result.get('href', ''),
                        relevance_score=0.8  # DuckDuckGo不提供相关性分数，使用默认值
                    ))
                
                logger.info(f"✅ 真实搜索成功: 找到{len(results)}个结果，耗时{search_time:.2f}秒")
                
                return SearchResponse(
                    query=query,
                    results=results,
                    total_results=len(results),
                    search_time=search_time,
                    success=True
                )
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # 检查是否是速率限制错误
                if any(keyword in error_msg for keyword in ['rate', 'limit', '202', 'too many']):
                    logger.warning(f"⚠️ 遇到速率限制 (尝试 {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        continue  # 继续重试
                    else:
                        logger.error(f"❌ 达到最大重试次数，速率限制仍然存在")
                else:
                    # 其他错误，立即降级
                    logger.error(f"❌ 真实DuckDuckGo搜索失败 (非速率限制): {e}")
                    break
        
        # 所有重试都失败了，降级到模拟搜索
        logger.warning("🔄 降级到模拟搜索结果")
        return self._search_duckduckgo_mock(query, max_results)
    
    def _search_duckduckgo_mock(self, query: str, max_results: int) -> SearchResponse:
        """模拟DuckDuckGo搜索结果"""
        logger.debug(f"🎭 使用模拟DuckDuckGo搜索: {query}")
        
        # 模拟网络延迟
        import random
        mock_delay = random.uniform(0.1, 0.5)
        time.sleep(mock_delay)
        
        mock_results = [
            SearchResult(
                title=f"关于'{query}'的技术解决方案",
                snippet=f"这是关于{query}的详细技术分析和实现方案，包含了最佳实践和常见问题解决方法。",
                url=f"https://example.com/tech-solution-{hash(query) % 1000}",
                relevance_score=0.9
            ),
            SearchResult(
                title=f"'{query}'实施指南和案例研究",
                snippet=f"通过实际案例了解{query}的实施过程，包括技术选型、架构设计和性能优化。",
                url=f"https://example.com/implementation-guide-{hash(query) % 1000}",
                relevance_score=0.8
            ),
            SearchResult(
                title=f"'{query}'的挑战与风险分析",
                snippet=f"深入分析{query}可能面临的技术挑战、潜在风险以及相应的应对策略。",
                url=f"https://example.com/risk-analysis-{hash(query) % 1000}",
                relevance_score=0.7
            )
        ]
        
        return SearchResponse(
            query=query,
            results=mock_results[:max_results],
            total_results=len(mock_results),
            search_time=mock_delay,  # 🔧 修复：现在显示真实的模拟延迟时间
            success=True
        )
    
    def _search_bing(self, query: str, max_results: int) -> SearchResponse:
        """使用Bing搜索（需要API密钥）"""
        # 这里可以集成真实的Bing Search API
        return self._search_fallback(query, max_results)
    
    def _search_fallback(self, query: str, max_results: int) -> SearchResponse:
        """备用搜索方法"""
        logger.warning("⚠️ 使用备用搜索方法（模拟结果）")
        
        fallback_results = [
            SearchResult(
                title=f"技术文档: {query}",
                snippet=f"这是关于{query}的技术文档和指南，提供了基础的实现方法。",
                url="https://docs.example.com/tech-docs",
                relevance_score=0.6
            ),
            SearchResult(
                title=f"社区讨论: {query}",
                snippet=f"开发者社区关于{query}的讨论和经验分享。",
                url="https://community.example.com/discussions",
                relevance_score=0.5
            )
        ]
        
        return SearchResponse(
            query=query,
            results=fallback_results[:max_results],
            total_results=len(fallback_results),
            search_time=0.0,
            success=True
        )
    
    def _update_search_stats(self, search_time: float, success: bool):
        """更新搜索统计"""
        self.search_stats['total_searches'] += 1
        if success:
            self.search_stats['successful_searches'] += 1
        
        self.search_stats['total_search_time'] += search_time
        self.search_stats['avg_search_time'] = (
            self.search_stats['total_search_time'] / self.search_stats['total_searches']
        )
    
    def get_search_stats(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        return self.search_stats.copy()

class IdeaVerificationSearchClient:
    """想法验证专用搜索客户端"""
    
    def __init__(self, web_search_client: WebSearchClient):
        """
        初始化想法验证搜索客户端
        
        Args:
            web_search_client: 网络搜索客户端
        """
        self.web_search_client = web_search_client
        self.verification_cache = {}  # 验证结果缓存
        
        logger.info("🔍 IdeaVerificationSearchClient初始化完成")
    
    def search_for_idea_verification(self, idea_text: str, context: Optional[Dict] = None) -> SearchResponse:
        """
        为想法验证进行专门的搜索
        
        Args:
            idea_text: 需要验证的想法文本
            context: 上下文信息
            
        Returns:
            SearchResponse: 搜索响应
        """
        # 检查缓存
        cache_key = f"{idea_text}_{hash(str(context))}"
        if cache_key in self.verification_cache:
            logger.debug(f"📋 使用缓存的验证搜索结果: {cache_key}")
            return self.verification_cache[cache_key]
        
        # 构建搜索查询
        search_query = self._build_verification_query(idea_text, context)
        
        # 执行搜索
        search_response = self.web_search_client.search(search_query, max_results=5)
        
        # 缓存结果
        if search_response.success:
            self.verification_cache[cache_key] = search_response
        
        return search_response
    
    def _build_verification_query(self, idea_text: str, context: Optional[Dict] = None) -> str:
        """
        构建用于想法验证的搜索查询
        
        Args:
            idea_text: 想法文本
            context: 上下文
            
        Returns:
            str: 搜索查询字符串
        """
        # 提取关键概念
        key_concepts = self._extract_key_concepts(idea_text)
        
        # 构建查询
        if len(key_concepts) >= 2:
            query = f"'{key_concepts[0]} {key_concepts[1]}' 可行性 实现方法 技术风险"
        else:
            query = f"'{idea_text[:50]}' 技术方案 实施指南 挑战"
        
        # 添加上下文信息
        if context and 'domain' in context:
            query = f"{query} {context['domain']}"
        
        logger.debug(f"🔍 构建验证查询: {query}")
        return query
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """提取文本中的关键概念"""
        # 简化的关键概念提取（实际应用中可以使用更复杂的NLP方法）
        tech_keywords = [
            'API', 'api', '算法', '数据库', '系统', '架构', '优化',
            '机器学习', 'ML', 'AI', '人工智能', '深度学习',
            '网络', '爬虫', '数据分析', '实时', '性能', '安全',
            '并发', '分布式', '微服务', '容器', '云计算'
        ]
        
        concepts = []
        for keyword in tech_keywords:
            if keyword in text:
                concepts.append(keyword)
        
        return concepts[:3]  # 返回前3个关键概念
    
    def verify_idea_feasibility(self, idea_text: str, context: Optional[Dict] = None) -> IdeaVerificationResult:
        """
        验证想法的可行性
        
        Args:
            idea_text: 需要验证的想法文本
            context: 上下文信息
            
        Returns:
            IdeaVerificationResult: 验证结果
        """
        try:
            logger.info(f"🔍 开始验证想法可行性: {idea_text[:50]}...")
            
            # 执行专门的验证搜索
            search_response = self.search_for_idea_verification(idea_text, context)
            
            if not search_response.success:
                return IdeaVerificationResult(
                    idea_text=idea_text,
                    feasibility_score=0.0,
                    analysis_summary="搜索失败，无法进行可行性验证",
                    search_results=[],
                    success=False,
                    error_message=search_response.error_message
                )
            
            # 分析搜索结果计算可行性分数
            feasibility_score = self._calculate_feasibility_score(search_response.results, idea_text)
            
            # 生成分析摘要
            analysis_summary = self._generate_analysis_summary(search_response.results, idea_text, feasibility_score)
            
            logger.info(f"✅ 想法验证完成 - 可行性分数: {feasibility_score:.2f}")
            
            return IdeaVerificationResult(
                idea_text=idea_text,
                feasibility_score=feasibility_score,
                analysis_summary=analysis_summary,
                search_results=search_response.results,
                success=True,
                error_message=""
            )
            
        except Exception as e:
            logger.error(f"❌ 想法验证失败: {e}")
            return IdeaVerificationResult(
                idea_text=idea_text,
                feasibility_score=0.0,
                analysis_summary=f"验证过程发生错误: {str(e)}",
                search_results=[],
                success=False,
                error_message=str(e)
            )
    
    def _calculate_feasibility_score(self, search_results: List[SearchResult], idea_text: str) -> float:
        """
        基于搜索结果计算可行性分数
        
        Args:
            search_results: 搜索结果列表
            idea_text: 想法文本
            
        Returns:
            float: 可行性分数 (0.0-1.0)
        """
        if not search_results:
            return 0.1  # 如果没有搜索结果，给一个很低的分数
        
        # 关键指标
        total_score = 0.0
        max_score = 0.0
        
        # 1. 结果数量指标 (权重: 0.2)
        result_count_score = min(len(search_results) / 5.0, 1.0)  # 5个结果为满分
        total_score += result_count_score * 0.2
        max_score += 0.2
        
        # 2. 内容相关性指标 (权重: 0.4)
        key_concepts = self._extract_key_concepts(idea_text)
        relevance_scores = []
        
        for result in search_results:
            content = (result.title + " " + result.snippet).lower()
            concept_matches = sum(1 for concept in key_concepts if concept.lower() in content)
            relevance = concept_matches / max(len(key_concepts), 1)
            relevance_scores.append(relevance)
        
        if relevance_scores:
            avg_relevance = sum(relevance_scores) / len(relevance_scores)
            total_score += avg_relevance * 0.4
        max_score += 0.4
        
        # 3. 实现可能性指标 (权重: 0.3)
        implementation_keywords = [
            '实现', '方法', '技术', '解决方案', '开发', '构建', '设计',
            'implement', 'solution', 'method', 'approach', 'technology'
        ]
        
        implementation_scores = []
        for result in search_results:
            content = (result.title + " " + result.snippet).lower()
            keyword_matches = sum(1 for keyword in implementation_keywords if keyword in content)
            impl_score = min(keyword_matches / 3.0, 1.0)  # 3个关键词为满分
            implementation_scores.append(impl_score)
        
        if implementation_scores:
            avg_implementation = sum(implementation_scores) / len(implementation_scores)
            total_score += avg_implementation * 0.3
        max_score += 0.3
        
        # 4. 风险指标 (权重: 0.1，负面影响)
        risk_keywords = [
            '困难', '挑战', '问题', '风险', '限制', '障碍',
            'difficult', 'challenge', 'problem', 'risk', 'limitation', 'obstacle'
        ]
        
        risk_scores = []
        for result in search_results:
            content = (result.title + " " + result.snippet).lower()
            risk_matches = sum(1 for keyword in risk_keywords if keyword in content)
            risk_score = min(risk_matches / 2.0, 1.0)  # 风险指标，越高越不好
            risk_scores.append(risk_score)
        
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            risk_penalty = avg_risk * 0.1
            total_score = max(0, total_score - risk_penalty)
        
        # 归一化分数
        final_score = total_score / max_score if max_score > 0 else 0.0
        
        # 确保分数在合理范围内
        return max(0.0, min(1.0, final_score))
    
    def _generate_analysis_summary(self, search_results: List[SearchResult], 
                                 idea_text: str, feasibility_score: float) -> str:
        """
        生成分析摘要
        
        Args:
            search_results: 搜索结果
            idea_text: 想法文本
            feasibility_score: 可行性分数
            
        Returns:
            str: 分析摘要
        """
        if not search_results:
            return "未找到相关信息，可行性分析受限。"
        
        # 根据可行性分数生成基础评估
        if feasibility_score >= 0.8:
            base_assessment = "该想法具有很高的可行性"
        elif feasibility_score >= 0.6:
            base_assessment = "该想法具有较好的可行性" 
        elif feasibility_score >= 0.4:
            base_assessment = "该想法具有一定的可行性，但需要谨慎评估"
        elif feasibility_score >= 0.2:
            base_assessment = "该想法可行性较低，存在较大挑战"
        else:
            base_assessment = "该想法可行性很低，实现困难"
        
        # 提取关键信息
        key_findings = []
        
        # 统计相关结果数量
        key_findings.append(f"搜索到{len(search_results)}个相关结果")
        
        # 分析技术关键词
        tech_keywords = self._extract_key_concepts(idea_text)
        if tech_keywords:
            key_findings.append(f"涉及技术领域: {', '.join(tech_keywords[:3])}")
        
        # 分析搜索结果质量
        if search_results:
            has_detailed_content = sum(1 for r in search_results if len(r.snippet) > 50)
            if has_detailed_content >= len(search_results) * 0.6:
                key_findings.append("找到了详细的技术资料")
            else:
                key_findings.append("相关资料有限")
        
        # 构建完整摘要
        summary_parts = [base_assessment]
        
        if key_findings:
            summary_parts.append("。分析发现：" + "，".join(key_findings))
        
        summary_parts.append(f"。综合评估可行性得分为{feasibility_score:.1f}/1.0。")
        
        return "".join(summary_parts)