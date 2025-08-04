#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
rag_seed_generator.py 单元测试
使用模拟（Mocking）技术测试RAG种子生成器的核心功能
"""

import unittest
import json
from unittest.mock import patch, MagicMock, Mock
from typing import List, Dict, Any

# 添加项目根目录到路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from meta_mab.rag_seed_generator import (
    RAGSeedGenerator, 
    RAGSearchStrategy, 
    RAGInformationSynthesis
)
from meta_mab.utils.search_client import SearchResult, SearchResponse


class TestRAGSeedGenerator(unittest.TestCase):
    """RAG种子生成器单元测试类"""
    
    def setUp(self):
        """测试前的设置"""
        # 创建模拟的搜索客户端
        self.mock_web_search_client = MagicMock()
        
        # 创建模拟的LLM客户端
        self.mock_llm_client = MagicMock()
        
        # 初始化RAG种子生成器（使用依赖注入）
        self.rag_generator = RAGSeedGenerator(
            web_search_client=self.mock_web_search_client,
            llm_client=self.mock_llm_client
        )
    
    def tearDown(self):
        """测试后的清理"""
        self.rag_generator.clear_cache()
    
    # ==================== _heuristic_search_planning 测试 ====================
    
    def test_heuristic_search_planning_simple_query(self):
        """测试启发式搜索规划 - 简单查询"""
        query = "如何学习Python"
        context = None
        
        strategy = self.rag_generator._heuristic_search_planning(query, context)
        
        # 验证返回的策略对象
        self.assertIsInstance(strategy, RAGSearchStrategy)
        
        # 验证策略内容
        self.assertIsInstance(strategy.primary_keywords, list)
        self.assertIsInstance(strategy.secondary_keywords, list)
        self.assertIsInstance(strategy.search_intent, str)
        self.assertIsInstance(strategy.domain_focus, str)
        self.assertIsInstance(strategy.information_types, list)
        self.assertIn(strategy.search_depth, ['shallow', 'medium', 'deep'])
        
        # 简单查询应该是浅层搜索
        self.assertEqual(strategy.search_depth, 'shallow')
        
        # 应该包含原查询的关键词
        self.assertTrue(any('python' in kw.lower() for kw in strategy.primary_keywords))
        
        print(f"简单查询搜索策略: {strategy}")
    
    def test_heuristic_search_planning_complex_query(self):
        """测试启发式搜索规划 - 复杂查询"""
        complex_query = "如何设计一个高性能的分布式机器学习系统，需要考虑算法优化和架构设计的复杂问题"
        context = {'performance_critical': True}
        
        strategy = self.rag_generator._heuristic_search_planning(complex_query, context)
        
        # 复杂查询应该是深层搜索
        self.assertEqual(strategy.search_depth, 'deep')
        
        # 应该检测到技术关键词（中文或英文）
        all_keywords = strategy.primary_keywords + strategy.secondary_keywords
        all_keywords_text = ' '.join(all_keywords).lower()
        
        # 检查中文技术术语
        chinese_tech_keywords = ['机器学习', '算法', '架构', '系统', '性能', '分布式']
        # 检查英文技术术语
        english_tech_keywords = ['machine learning', 'algorithm', 'architecture', 'system', 'performance']
        
        has_chinese_tech = any(tech in all_keywords_text for tech in chinese_tech_keywords)
        has_english_tech = any(tech in all_keywords_text for tech in english_tech_keywords)
        
        self.assertTrue(has_chinese_tech or has_english_tech, 
                       f"应该检测到技术术语，但关键词列表是: {all_keywords}")
        
        # 技术领域应该被正确识别
        self.assertEqual(strategy.domain_focus, '技术')
        
        print(f"复杂查询搜索策略: {strategy}")
    
    def test_heuristic_search_planning_how_question(self):
        """测试启发式搜索规划 - "如何"类问题"""
        how_query = "如何提高网站性能"
        
        strategy = self.rag_generator._heuristic_search_planning(how_query, None)
        
        # "如何"问题应该寻找解释或指导信息
        self.assertEqual(strategy.search_intent, "寻找解释或指导信息")
        self.assertIn("教程", strategy.information_types)
        self.assertIn("定义", strategy.information_types)
        self.assertIn("指南", strategy.information_types)
        
        print(f"如何问题搜索策略: {strategy}")
    
    def test_heuristic_search_planning_comparison_question(self):
        """测试启发式搜索规划 - 比较类问题"""
        comparison_query = "最好的Python框架比较"
        
        strategy = self.rag_generator._heuristic_search_planning(comparison_query, None)
        
        # 比较问题应该寻找比较和推荐信息
        self.assertEqual(strategy.search_intent, "寻找比较和推荐信息")
        self.assertIn("比较", strategy.information_types)
        self.assertIn("评测", strategy.information_types)
        self.assertIn("推荐", strategy.information_types)
        
        print(f"比较问题搜索策略: {strategy}")
    
    # ==================== _llm_based_search_planning 测试 ====================
    
    def test_llm_based_search_planning_success(self):
        """测试LLM搜索规划 - 成功场景"""
        query = "如何优化数据库查询性能"
        context = {'database_type': 'PostgreSQL'}
        
        # 模拟LLM返回的JSON响应
        mock_llm_response = json.dumps({
            "search_intent": "寻找数据库性能优化技术",
            "domain_focus": "数据库技术",
            "primary_keywords": ["数据库优化", "查询性能", "PostgreSQL"],
            "secondary_keywords": ["索引优化", "SQL调优"],
            "information_types": ["技术指南", "最佳实践", "案例研究"],
            "search_depth": "medium"
        }, ensure_ascii=False)
        
        # 配置模拟客户端
        self.mock_llm_client.call_api.return_value = mock_llm_response
        
        # 执行测试
        strategy = self.rag_generator._llm_based_search_planning(query, context)
        
        # 验证结果
        self.assertIsInstance(strategy, RAGSearchStrategy)
        self.assertEqual(strategy.search_intent, "寻找数据库性能优化技术")
        self.assertEqual(strategy.domain_focus, "数据库技术")
        self.assertIn("数据库优化", strategy.primary_keywords)
        self.assertEqual(strategy.search_depth, "medium")
        
        # 验证LLM被正确调用
        self.mock_llm_client.call_api.assert_called_once()
        call_args = self.mock_llm_client.call_api.call_args
        self.assertIn("数据库查询性能", call_args[0][0])  # 查询应该在prompt中
        
        print(f"LLM搜索策略: {strategy}")
    
    def test_llm_based_search_planning_invalid_json(self):
        """测试LLM搜索规划 - 无效JSON响应"""
        query = "测试查询"
        
        # 模拟LLM返回无效JSON
        self.mock_llm_client.call_api.return_value = "这不是有效的JSON格式"
        
        # 应该抛出异常
        with self.assertRaises(ValueError):
            self.rag_generator._llm_based_search_planning(query, None)
    
    def test_llm_based_search_planning_with_context(self):
        """测试LLM搜索规划 - 包含执行上下文"""
        query = "机器学习模型部署"
        context = {
            'real_time_requirements': True,
            'performance_critical': True,
            'target_platform': 'cloud'
        }
        
        # 模拟LLM响应
        mock_response = json.dumps({
            "search_intent": "寻找ML模型部署方案",
            "domain_focus": "机器学习",
            "primary_keywords": ["模型部署", "实时推理"],
            "secondary_keywords": ["云平台", "性能优化"],
            "information_types": ["部署指南", "架构设计"],
            "search_depth": "deep"
        })
        
        self.mock_llm_client.call_api.return_value = mock_response
        
        strategy = self.rag_generator._llm_based_search_planning(query, context)
        
        # 验证上下文信息被传递给LLM
        call_args = self.mock_llm_client.call_api.call_args[0][0]
        self.assertIn("real_time_requirements", call_args)
        self.assertIn("performance_critical", call_args)
        self.assertIn("target_platform", call_args)
        
        print(f"带上下文的LLM搜索策略: {strategy}")
    
    # ==================== _filter_and_deduplicate_results 测试 ====================
    
    def test_filter_and_deduplicate_results_basic(self):
        """测试搜索结果过滤和去重 - 基础功能"""
        # 创建测试搜索结果，包含重复URL
        search_results = [
            SearchResult(
                title="Python教程1",
                url="https://example.com/python1",
                snippet="学习Python编程的基础教程"
            ),
            SearchResult(
                title="Python教程2",
                url="https://example.com/python1",  # 重复URL
                snippet="Python编程入门指南"
            ),
            SearchResult(
                title="Java教程",
                url="https://example.com/java",
                snippet="Java编程学习资源"
            ),
            SearchResult(
                title="Python高级教程",
                url="https://example.com/python2",
                snippet="高级Python编程技巧和最佳实践"
            )
        ]
        
        # 创建搜索策略
        strategy = RAGSearchStrategy(
            primary_keywords=["Python", "编程"],
            secondary_keywords=["教程", "学习"],
            search_intent="学习编程",
            domain_focus="编程",
            information_types=["教程"],
            search_depth="medium"
        )
        
        # 执行过滤和去重
        filtered_results = self.rag_generator._filter_and_deduplicate_results(search_results, strategy)
        
        # 验证去重功能
        urls = [result.url for result in filtered_results]
        self.assertEqual(len(urls), len(set(urls)), "应该移除重复的URL")
        
        # 验证结果数量
        self.assertLessEqual(len(filtered_results), len(search_results))
        
        # 验证相关性排序（Python相关的应该排在前面）
        python_results = [r for r in filtered_results if 'python' in r.title.lower() or 'python' in r.snippet.lower()]
        self.assertGreater(len(python_results), 0, "应该有Python相关的结果")
        
        print(f"过滤前: {len(search_results)} 条结果")
        print(f"过滤后: {len(filtered_results)} 条结果")
        for result in filtered_results:
            print(f"  - {result.title}: {result.url}")
    
    def test_filter_and_deduplicate_results_relevance_scoring(self):
        """测试搜索结果的相关性评分"""
        # 创建不同相关性的搜索结果
        search_results = [
            SearchResult(
                title="无关内容",
                url="https://example.com/unrelated",
                snippet="这是一个完全无关的内容"
            ),
            SearchResult(
                title="机器学习算法详解",
                url="https://example.com/ml-algo",
                snippet="深入介绍各种机器学习算法的原理和应用"
            ),
            SearchResult(
                title="AI算法优化技术",
                url="https://example.com/ai-opt",
                snippet="人工智能算法的性能优化方法和最佳实践"
            )
        ]
        
        strategy = RAGSearchStrategy(
            primary_keywords=["机器学习", "算法"],
            secondary_keywords=["优化", "AI"],
            search_intent="技术学习",
            domain_focus="技术",
            information_types=["技术文档"],
            search_depth="deep"
        )
        
        filtered_results = self.rag_generator._filter_and_deduplicate_results(search_results, strategy)
        
        # 高相关性的结果应该排在前面
        self.assertGreater(len(filtered_results), 0)
        
        # 验证排序：机器学习相关的应该在前面
        if len(filtered_results) > 1:
            first_result = filtered_results[0]
            self.assertTrue(
                '机器学习' in first_result.title or '机器学习' in first_result.snippet or
                '算法' in first_result.title or '算法' in first_result.snippet,
                "最相关的结果应该排在第一位"
            )
        
        print(f"按相关性排序的结果:")
        for i, result in enumerate(filtered_results):
            print(f"  {i+1}. {result.title}")
    
    def test_filter_and_deduplicate_results_empty_input(self):
        """测试空输入的处理"""
        empty_results = []
        strategy = RAGSearchStrategy(
            primary_keywords=["test"],
            secondary_keywords=[],
            search_intent="test",
            domain_focus="test",
            information_types=["test"],
            search_depth="shallow"
        )
        
        filtered_results = self.rag_generator._filter_and_deduplicate_results(empty_results, strategy)
        
        # 空输入应该返回空列表
        self.assertEqual(len(filtered_results), 0)
    
    def test_filter_and_deduplicate_results_max_limit(self):
        """测试结果数量限制"""
        # 创建大量搜索结果
        search_results = []
        for i in range(20):  # 创建20个结果
            search_results.append(SearchResult(
                title=f"测试结果 {i}",
                url=f"https://example.com/test{i}",
                snippet=f"这是第 {i} 个测试结果，包含相关关键词"
            ))
        
        strategy = RAGSearchStrategy(
            primary_keywords=["测试", "关键词"],
            secondary_keywords=[],
            search_intent="测试",
            domain_focus="测试",
            information_types=["测试"],
            search_depth="medium"
        )
        
        filtered_results = self.rag_generator._filter_and_deduplicate_results(search_results, strategy)
        
        # 结果数量应该被限制在8个以内（根据代码中的限制）
        self.assertLessEqual(len(filtered_results), 8)
        
        print(f"大量结果过滤: {len(search_results)} -> {len(filtered_results)}")


class TestRAGSeedGeneratorIntegration(unittest.TestCase):
    """RAG种子生成器集成测试"""
    
    def setUp(self):
        """测试前的设置"""
        # 创建更复杂的模拟设置
        self.mock_web_search_client = MagicMock()
        self.mock_llm_client = MagicMock()
        
        self.rag_generator = RAGSeedGenerator(
            web_search_client=self.mock_web_search_client,
            llm_client=self.mock_llm_client
        )
    
    def test_generate_rag_seed_full_pipeline(self):
        """测试完整的RAG种子生成流程"""
        query = "如何提高Python代码性能"
        context = {'programming_language': 'Python'}
        
        # 模拟搜索结果
        mock_search_results = [
            SearchResult(
                title="Python性能优化指南",
                url="https://example.com/python-performance",
                snippet="详细介绍Python代码性能优化的各种技巧和方法"
            ),
            SearchResult(
                title="高效Python编程技巧",
                url="https://example.com/efficient-python",
                snippet="提升Python程序运行效率的实用建议"
            )
        ]
        
        # 配置搜索客户端模拟
        mock_response = SearchResponse(
            query="python performance optimization",
            results=mock_search_results,
            total_results=2,
            search_time=0.1
        )
        self.mock_web_search_client.search.return_value = mock_response
        
        # 模拟LLM规划响应
        planning_response = json.dumps({
            "search_intent": "寻找Python性能优化技术",
            "domain_focus": "编程技术",
            "primary_keywords": ["Python", "性能优化"],
            "secondary_keywords": ["代码效率", "程序优化"],
            "information_types": ["技术指南", "最佳实践"],
            "search_depth": "medium"
        })
        
        # 模拟LLM综合响应
        synthesis_response = json.dumps({
            "contextual_seed": "基于搜索结果，Python性能优化可以通过多种技术实现。首先，选择合适的数据结构和算法是关键。其次，利用内置函数和库可以显著提升性能。最后，代码分析和性能测试能帮助识别瓶颈。这些方法结合使用，能够有效提升Python程序的运行效率。",
            "key_insights": ["数据结构选择很重要", "内置函数性能更好", "性能测试不可缺少"],
            "knowledge_gaps": ["具体的性能测试工具", "大规模应用的优化策略"],
            "confidence_score": 0.85,
            "information_sources": ["Python性能优化指南", "高效Python编程技巧"],
            "verification_status": "verified"
        })
        
        # 设置LLM调用的返回值（第一次用于规划，第二次用于综合）
        self.mock_llm_client.call_api.side_effect = [planning_response, synthesis_response]
        
        # 执行RAG种子生成
        result_seed = self.rag_generator.generate_rag_seed(query, context)
        
        # 验证结果
        self.assertIsInstance(result_seed, str)
        self.assertGreater(len(result_seed), 0)
        self.assertIn("Python", result_seed)
        self.assertIn("性能", result_seed)
        
        # 验证搜索客户端被调用
        self.mock_web_search_client.search.assert_called()
        
        # 验证LLM客户端被调用两次（规划 + 综合）
        self.assertEqual(self.mock_llm_client.call_api.call_count, 2)
        
        print(f"生成的RAG种子: {result_seed}")
        
        # 验证性能统计被更新
        stats = self.rag_generator.get_rag_performance_stats()
        self.assertEqual(stats['performance_stats']['total_generations'], 1)
        self.assertEqual(stats['performance_stats']['successful_generations'], 1)
    
    def test_generate_rag_seed_fallback_mode(self):
        """测试RAG种子生成的回退模式"""
        query = "测试回退功能"
        
        # 模拟搜索失败
        self.mock_web_search_client.search.side_effect = Exception("搜索服务不可用")
        
        # 模拟LLM失败
        self.mock_llm_client.call_api.side_effect = Exception("LLM服务不可用")
        
        # 执行生成（应该使用回退模式）
        result_seed = self.rag_generator.generate_rag_seed(query)
        
        # 验证回退种子被生成
        self.assertIsInstance(result_seed, str)
        self.assertGreater(len(result_seed), 0)
        self.assertIn("测试回退功能", result_seed)
        
        print(f"回退模式生成的种子: {result_seed}")
    
    def test_generate_rag_seed_no_search_results(self):
        """测试无搜索结果时的处理"""
        query = "非常罕见的查询内容"
        
        # 模拟无搜索结果
        empty_response = SearchResponse(
            query=query,
            results=[],
            total_results=0,
            search_time=0.05
        )
        self.mock_web_search_client.search.return_value = empty_response
        
        # 模拟LLM规划成功
        planning_response = json.dumps({
            "search_intent": "寻找相关信息",
            "domain_focus": "通用",
            "primary_keywords": ["罕见", "查询"],
            "secondary_keywords": [],
            "information_types": ["信息"],
            "search_depth": "shallow"
        })
        self.mock_llm_client.call_api.return_value = planning_response
        
        result_seed = self.rag_generator.generate_rag_seed(query)
        
        # 无搜索结果时应该生成基础种子
        self.assertIsInstance(result_seed, str)
        self.assertGreater(len(result_seed), 0)
        
        print(f"无搜索结果时的种子: {result_seed}")


class TestRAGSeedGeneratorPerformance(unittest.TestCase):
    """RAG种子生成器性能相关测试"""
    
    def setUp(self):
        self.mock_web_search_client = MagicMock()
        self.mock_llm_client = MagicMock()
        self.rag_generator = RAGSeedGenerator(
            web_search_client=self.mock_web_search_client,
            llm_client=self.mock_llm_client
        )
    
    def test_caching_functionality(self):
        """测试缓存功能"""
        query = "测试缓存功能"
        
        # 模拟LLM响应
        planning_response = json.dumps({
            "search_intent": "测试缓存",
            "domain_focus": "测试",
            "primary_keywords": ["缓存", "测试"],
            "secondary_keywords": [],
            "information_types": ["技术"],
            "search_depth": "shallow"
        })
        self.mock_llm_client.call_api.return_value = planning_response
        
        # 第一次调用
        strategy1 = self.rag_generator._llm_based_search_planning(query, None)
        
        # 第二次调用（应该使用缓存）
        strategy2 = self.rag_generator._llm_based_search_planning(query, None)
        
        # 验证结果相同
        self.assertEqual(strategy1.search_intent, strategy2.search_intent)
        self.assertEqual(strategy1.primary_keywords, strategy2.primary_keywords)
        
        # LLM应该只被调用一次（第二次使用缓存）
        self.assertEqual(self.mock_llm_client.call_api.call_count, 1)
        
        # 验证缓存状态
        self.assertGreater(len(self.rag_generator.strategy_cache), 0)
    
    def test_performance_stats_tracking(self):
        """测试性能统计跟踪"""
        # 获取初始统计
        initial_stats = self.rag_generator.get_rag_performance_stats()
        self.assertEqual(initial_stats['performance_stats']['total_generations'], 0)
        
        # 模拟成功的LLM响应
        planning_response = json.dumps({
            "search_intent": "测试性能统计",
            "domain_focus": "测试",
            "primary_keywords": ["测试", "性能"],
            "secondary_keywords": ["统计"],
            "information_types": ["技术"],
            "search_depth": "shallow"
        })
        self.mock_llm_client.call_api.return_value = planning_response
        
        # 模拟成功的搜索过程
        self.mock_web_search_client.search.return_value = SearchResponse("test", [], 0, 0.02)
        
        # 执行生成
        self.rag_generator.generate_rag_seed("测试查询")
        
        # 检查统计更新
        updated_stats = self.rag_generator.get_rag_performance_stats()
        self.assertEqual(updated_stats['performance_stats']['total_generations'], 1)
        self.assertEqual(updated_stats['performance_stats']['successful_generations'], 1)
        self.assertGreater(updated_stats['performance_stats']['avg_generation_time'], 0)


if __name__ == '__main__':
    # 设置详细的测试输出
    unittest.main(verbosity=2)