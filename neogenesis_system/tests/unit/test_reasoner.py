#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
reasoner.py 单元测试
测试轻量级分析助手的核心功能
"""

import unittest
import time
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cognitive_engine.reasoner import PriorReasoner


class TestPriorReasoner(unittest.TestCase):
    """PriorReasoner 单元测试类"""
    
    def setUp(self):
        """测试前的设置"""
        self.reasoner = PriorReasoner()
    
    def tearDown(self):
        """测试后的清理"""
        self.reasoner.reset_cache()
    
    # ==================== assess_task_confidence 测试 ====================
    
    def test_assess_task_confidence_short_query(self):
        """测试短查询的置信度评估"""
        short_query = "帮助我"
        confidence = self.reasoner.assess_task_confidence(short_query)
        
        # 短查询应该有较高的置信度（基础0.7 + 短查询奖励0.1 + 明确性关键词0.03）
        self.assertGreaterEqual(confidence, 0.7)
        self.assertLessEqual(confidence, 1.0)
        print(f"短查询置信度: {confidence:.3f}")
    
    def test_assess_task_confidence_long_query(self):
        """测试长查询的置信度评估"""
        long_query = """
        请帮我设计一个复杂的分布式机器学习系统，需要考虑高并发、实时性、
        多步骤数据处理流程、异步任务调度、复杂的算法优化、高级架构设计，
        同时还要考虑性能瓶颈、数据一致性、容错机制等多个专业技术难点。
        这是一个非常困难和挑战性的高级专业任务。
        """
        confidence = self.reasoner.assess_task_confidence(long_query)
        
        # 长查询且包含复杂关键词，置信度应该降低
        self.assertGreaterEqual(confidence, 0.2)  # 最低限制
        self.assertLess(confidence, 0.7)  # 应该低于基础置信度
        print(f"长复杂查询置信度: {confidence:.3f}")
    
    def test_assess_task_confidence_tech_terms(self):
        """测试包含技术术语的查询"""
        tech_query = "如何优化API性能，使用机器学习算法分析数据库查询模式"
        confidence = self.reasoner.assess_task_confidence(tech_query)
        
        # 包含技术术语应该增加置信度
        self.assertGreaterEqual(confidence, 0.7)
        self.assertLessEqual(confidence, 1.0)
        print(f"技术术语查询置信度: {confidence:.3f}")
    
    def test_assess_task_confidence_with_execution_context(self):
        """测试带执行上下文的置信度评估"""
        query = "实现一个网络爬虫"
        context = {
            'real_time_requirements': True,
            'performance_critical': True,
            'user_type': 'expert',
            'priority': 'high'
        }
        confidence = self.reasoner.assess_task_confidence(query, context)
        
        # 实时和性能要求应该降低置信度，但更多上下文信息会增加置信度
        self.assertGreaterEqual(confidence, 0.2)
        self.assertLessEqual(confidence, 1.0)
        print(f"带上下文查询置信度: {confidence:.3f}")
    
    def test_assess_task_confidence_caching(self):
        """测试置信度评估的缓存机制"""
        query = "测试缓存功能"
        
        # 第一次调用
        start_time = time.time()
        confidence1 = self.reasoner.assess_task_confidence(query)
        first_duration = time.time() - start_time
        
        # 第二次调用（应该使用缓存）
        start_time = time.time()
        confidence2 = self.reasoner.assess_task_confidence(query)
        second_duration = time.time() - start_time
        
        # 结果应该相同
        self.assertEqual(confidence1, confidence2)
        
        # 第二次应该更快（使用缓存）
        # 注意：这个测试可能因为执行速度太快而不明显
        print(f"第一次耗时: {first_duration:.6f}s, 第二次耗时: {second_duration:.6f}s")
        
        # 检查缓存是否生效
        self.assertTrue(len(self.reasoner.assessment_cache) > 0)
    
    def test_assess_task_confidence_range_validation(self):
        """测试置信度分数的范围验证"""
        test_cases = [
            "简单任务",
            "中等复杂度的API设计任务",  
            "极其复杂困难的分布式系统架构设计，涉及多个专业高级技术难点和挑战性问题" * 3
        ]
        
        for query in test_cases:
            confidence = self.reasoner.assess_task_confidence(query)
            
            # 所有置信度分数都应该在 [0.0, 1.0] 范围内
            self.assertGreaterEqual(confidence, 0.0, f"查询 '{query[:30]}...' 的置信度低于0.0")
            self.assertLessEqual(confidence, 1.0, f"查询 '{query[:30]}...' 的置信度超过1.0")
    
    # ==================== analyze_task_complexity 测试 ====================
    
    def test_analyze_task_complexity_simple_task(self):
        """测试简单任务的复杂度分析"""
        simple_query = "如何创建文件"
        result = self.reasoner.analyze_task_complexity(simple_query)
        
        # 验证返回的字典结构
        self.assertIsInstance(result, dict)
        self.assertIn('complexity_score', result)
        self.assertIn('estimated_domain', result)
        self.assertIn('requires_multi_step', result)
        self.assertIn('complexity_factors', result)
        
        # 简单任务的复杂度应该较低
        self.assertLessEqual(result['complexity_score'], 0.7)
        self.assertIsInstance(result['requires_multi_step'], bool)
        
        print(f"简单任务复杂度分析: {result}")
    
    def test_analyze_task_complexity_complex_task(self):
        """测试复杂任务的复杂度分析"""
        complex_query = "设计一个分布式机器学习系统，包含多步骤数据处理、实时优化算法和高性能架构"
        result = self.reasoner.analyze_task_complexity(complex_query)
        
        # 复杂任务的复杂度应该较高
        self.assertGreaterEqual(result['complexity_score'], 0.7)
        
        # 应该检测到多步骤需求
        self.assertTrue(result['requires_multi_step'])
        
        # 应该有复杂度因子
        self.assertGreater(len(result['complexity_factors']), 0)
        
        # 领域推断应该合理
        self.assertIsInstance(result['estimated_domain'], str)
        
        print(f"复杂任务复杂度分析: {result}")
    
    def test_analyze_task_complexity_domain_inference(self):
        """测试领域推断功能"""
        test_cases = [
            ("创建一个网站前端", ["web_development", "general"]),
            ("数据分析和机器学习模型训练", ["data_science", "general"]),
            ("API接口设计", ["api_development", "general"]),
            ("爬虫程序开发", ["web_scraping", "general"]),
            ("数据库查询优化", ["database", "general"]),
            ("系统部署和运维", ["system_admin", "general"]),
            ("一般性问题", ["general"])
        ]
        
        for query, expected_domains in test_cases:
            result = self.reasoner.analyze_task_complexity(query)
            domain = result['estimated_domain']
            
            self.assertIn(domain, expected_domains, 
                         f"查询 '{query}' 的领域推断 '{domain}' 不在预期范围 {expected_domains}")
            print(f"'{query}' -> 领域: {domain}")
    
    def test_analyze_task_complexity_multistep_detection(self):
        """测试多步骤检测功能"""
        multistep_queries = [
            "首先分析数据，然后训练模型，最后部署系统",
            "第一步创建数据库，第二步设计API，第三步开发前端",
            "依次执行数据收集、处理、分析和可视化步骤"
        ]
        
        single_step_queries = [
            "创建一个文件",
            "查询数据库",
            "发送HTTP请求"
        ]
        
        # 测试多步骤查询
        for query in multistep_queries:
            result = self.reasoner.analyze_task_complexity(query)
            self.assertTrue(result['requires_multi_step'], 
                          f"查询 '{query}' 应该被识别为多步骤任务")
        
        # 测试单步骤查询
        for query in single_step_queries:
            result = self.reasoner.analyze_task_complexity(query)
            self.assertFalse(result['requires_multi_step'], 
                           f"查询 '{query}' 不应该被识别为多步骤任务")
    
    def test_analyze_task_complexity_score_range(self):
        """测试复杂度分数的范围验证"""
        test_queries = [
            "简单",
            "中等复杂度的算法设计",
            "极其复杂的分布式系统架构设计，涉及机器学习、深度学习、高性能计算、多步骤处理、实时优化等高级技术"
        ]
        
        for query in test_queries:
            result = self.reasoner.analyze_task_complexity(query)
            score = result['complexity_score']
            
            # 复杂度分数应该在 [0.0, 1.0] 范围内
            self.assertGreaterEqual(score, 0.0, f"查询 '{query}' 的复杂度分数低于0.0")
            self.assertLessEqual(score, 1.0, f"查询 '{query}' 的复杂度分数超过1.0")
    
    # ==================== 其他功能测试 ====================
    
    def test_get_thinking_seed_compatibility(self):
        """测试思维种子生成的兼容性"""
        query = "如何优化数据库性能"
        
        seed = self.reasoner.get_thinking_seed(query)
        
        # 验证种子生成
        self.assertIsInstance(seed, str)
        self.assertGreater(len(seed), 0)
        self.assertIn("数据库", seed)  # 应该包含原始查询的关键信息
        
        print(f"生成的思维种子长度: {len(seed)} 字符")
        print(f"种子预览: {seed[:100]}...")
    
    def test_get_quick_analysis_summary(self):
        """测试快速分析总结功能"""
        query = "开发一个机器学习推荐系统"
        context = {'performance_critical': True}
        
        summary = self.reasoner.get_quick_analysis_summary(query, context)
        
        # 验证摘要结构
        required_keys = ['domain', 'complexity_score', 'confidence_score', 
                        'requires_multi_step', 'key_factors', 'recommendation']
        for key in required_keys:
            self.assertIn(key, summary, f"快速分析摘要缺少 '{key}' 字段")
        
        # 验证数据类型
        self.assertIsInstance(summary['complexity_score'], float)
        self.assertIsInstance(summary['confidence_score'], float)
        self.assertIsInstance(summary['requires_multi_step'], bool)
        self.assertIsInstance(summary['key_factors'], list)
        
        print(f"快速分析摘要: {summary}")
    
    def test_confidence_feedback_system(self):
        """测试置信度反馈系统"""
        # 添加一些反馈数据
        self.reasoner.update_confidence_feedback(0.8, True, 2.5)
        self.reasoner.update_confidence_feedback(0.6, False, 1.2)
        self.reasoner.update_confidence_feedback(0.9, True, 1.8)
        
        # 获取统计信息
        stats = self.reasoner.get_confidence_statistics()
        
        # 验证统计结构
        self.assertIn('total_assessments', stats)
        self.assertIn('avg_confidence', stats)
        self.assertIn('confidence_trend', stats)
        
        # 验证数据
        self.assertEqual(stats['total_assessments'], 3)
        self.assertGreater(stats['avg_confidence'], 0)
        
        print(f"置信度统计: {stats}")


class TestPriorReasonerEdgeCases(unittest.TestCase):
    """PriorReasoner 边界条件测试"""
    
    def setUp(self):
        self.reasoner = PriorReasoner()
    
    def test_empty_query(self):
        """测试空查询"""
        confidence = self.reasoner.assess_task_confidence("")
        complexity = self.reasoner.analyze_task_complexity("")
        
        # 空查询应该有合理的默认值
        self.assertGreaterEqual(confidence, 0.2)
        self.assertLessEqual(confidence, 1.0)
        
        self.assertIsInstance(complexity, dict)
        self.assertIn('complexity_score', complexity)
    
    def test_very_long_query(self):
        """测试超长查询"""
        very_long_query = "测试查询 " * 1000  # 创建非常长的查询
        
        confidence = self.reasoner.assess_task_confidence(very_long_query)
        complexity = self.reasoner.analyze_task_complexity(very_long_query)
        
        # 超长查询应该降低置信度
        self.assertLess(confidence, 0.7)
        
        # 复杂度分析应该正常工作
        self.assertIsInstance(complexity, dict)
    
    def test_special_characters_query(self):
        """测试包含特殊字符的查询"""
        special_query = "如何处理 @#$%^&*()_+{}[]|\\:;\"'<>?,./~` 这些特殊字符？"
        
        confidence = self.reasoner.assess_task_confidence(special_query)
        complexity = self.reasoner.analyze_task_complexity(special_query)
        
        # 特殊字符不应该导致错误
        self.assertIsInstance(confidence, float)
        self.assertIsInstance(complexity, dict)
    
    def test_cache_overflow(self):
        """测试缓存溢出处理"""
        # 生成大量不同的查询来触发缓存清理
        for i in range(150):  # 超过默认缓存大小100
            query = f"测试查询 {i}"
            self.reasoner.assess_task_confidence(query)
        
        # 缓存大小应该被限制
        self.assertLessEqual(len(self.reasoner.assessment_cache), 100)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)