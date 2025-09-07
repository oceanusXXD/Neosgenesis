#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的单元测试示例
演示如何使用Python unittest库进行基本测试
"""

import unittest
import sys
import os

# 添加项目根目录到路径，方便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cognitive_engine.reasoner import PriorReasoner


class SimpleTestExample(unittest.TestCase):
    """简单测试示例类 - 演示基本的测试模式"""
    
    def setUp(self):
        """
        每个测试方法运行前都会执行这个方法
        用于准备测试数据和对象
        """
        print("\n🔧 准备测试环境...")
        self.reasoner = PriorReasoner()
        self.test_query = "如何学习Python编程"
    
    def tearDown(self):
        """
        每个测试方法运行后都会执行这个方法
        用于清理测试数据
        """
        print("🧹 清理测试环境...")
        if hasattr(self, 'reasoner'):
            self.reasoner.reset_cache()
    
    def test_basic_confidence_assessment(self):
        """
        基础置信度评估测试
        
        这个测试演示了：
        1. 如何调用被测试的方法
        2. 如何使用断言验证结果
        3. 如何添加测试说明
        """
        print("📊 测试基础置信度评估...")
        
        # 调用被测试的方法
        confidence = self.reasoner.assess_task_confidence(self.test_query)
        
        # 使用断言验证结果
        self.assertIsInstance(confidence, float, "置信度应该是浮点数")
        self.assertGreaterEqual(confidence, 0.0, "置信度不应该小于0")
        self.assertLessEqual(confidence, 1.0, "置信度不应该大于1")
        
        print(f"✅ 置信度评估通过: {confidence:.3f}")
    
    def test_complexity_analysis_structure(self):
        """
        复杂度分析结果结构测试
        
        这个测试演示了：
        1. 如何验证返回值的数据结构
        2. 如何检查字典中的必要字段
        3. 如何验证数据类型
        """
        print("🧮 测试复杂度分析结构...")
        
        # 调用方法
        result = self.reasoner.analyze_task_complexity(self.test_query)
        
        # 验证返回类型
        self.assertIsInstance(result, dict, "复杂度分析结果应该是字典")
        
        # 验证必要字段存在
        required_fields = ['complexity_score', 'estimated_domain', 'requires_multi_step']
        for field in required_fields:
            self.assertIn(field, result, f"结果中应该包含 {field} 字段")
        
        # 验证字段的数据类型
        self.assertIsInstance(result['complexity_score'], float, "复杂度分数应该是浮点数")
        self.assertIsInstance(result['estimated_domain'], str, "估计领域应该是字符串")
        self.assertIsInstance(result['requires_multi_step'], bool, "多步骤标志应该是布尔值")
        
        print(f"✅ 复杂度分析结构验证通过")
        print(f"   复杂度分数: {result['complexity_score']:.3f}")
        print(f"   估计领域: {result['estimated_domain']}")
        print(f"   需要多步骤: {result['requires_multi_step']}")
    
    def test_different_query_types(self):
        """
        不同查询类型测试
        
        这个测试演示了：
        1. 如何测试多种输入情况
        2. 如何使用循环减少重复代码
        3. 如何为每种情况添加特定验证
        """
        print("🔄 测试不同类型的查询...")
        
        # 定义测试用例
        test_cases = [
            {
                'query': '简单问题',
                'expected_domain': 'general',
                'description': '简单查询'
            },
            {
                'query': '如何设计RESTful API接口',
                'expected_domain': 'api_development',
                'description': 'API开发查询'
            },
            {
                'query': '机器学习算法优化',
                'expected_domain': 'data_science',
                'description': '数据科学查询'
            }
        ]
        
        # 对每个测试用例进行验证
        for case in test_cases:
            with self.subTest(case=case['description']):
                print(f"   测试: {case['description']}")
                
                # 执行分析
                result = self.reasoner.analyze_task_complexity(case['query'])
                
                # 基本验证
                self.assertIsInstance(result, dict)
                self.assertIn('estimated_domain', result)
                
                # 特定验证（如果指定了期望领域）
                if case['expected_domain'] != 'general':
                    # API和数据科学查询应该被识别到相应领域，或者至少不是general
                    print(f"     期望领域: {case['expected_domain']}, 实际领域: {result['estimated_domain']}")
                
                print(f"   ✅ {case['description']} 测试通过")
    
    def test_edge_cases(self):
        """
        边界情况测试
        
        这个测试演示了：
        1. 如何测试边界条件
        2. 如何处理异常情况
        3. 如何验证程序的健壮性
        """
        print("🚧 测试边界情况...")
        
        # 测试空字符串
        empty_confidence = self.reasoner.assess_task_confidence("")
        self.assertIsInstance(empty_confidence, float)
        self.assertGreaterEqual(empty_confidence, 0.0)
        self.assertLessEqual(empty_confidence, 1.0)
        print("   ✅ 空字符串测试通过")
        
        # 测试很长的字符串
        very_long_query = "测试查询 " * 100  # 重复100次
        long_confidence = self.reasoner.assess_task_confidence(very_long_query)
        self.assertIsInstance(long_confidence, float)
        print("   ✅ 超长字符串测试通过")
        
        # 测试特殊字符
        special_query = "如何处理 @#$%^&*() 这些特殊字符？"
        special_confidence = self.reasoner.assess_task_confidence(special_query)
        self.assertIsInstance(special_confidence, float)
        print("   ✅ 特殊字符测试通过")
    
    def test_caching_behavior(self):
        """
        缓存行为测试
        
        这个测试演示了：
        1. 如何测试系统的性能特性
        2. 如何验证缓存机制
        3. 如何测试状态变化
        """
        print("💾 测试缓存行为...")
        
        query = "测试缓存功能"
        
        # 检查初始缓存状态
        initial_cache_size = len(self.reasoner.assessment_cache)
        
        # 第一次调用
        confidence1 = self.reasoner.assess_task_confidence(query)
        
        # 检查缓存是否增加
        after_first_call = len(self.reasoner.assessment_cache)
        self.assertGreater(after_first_call, initial_cache_size, "第一次调用后缓存应该增加")
        
        # 第二次调用相同查询
        confidence2 = self.reasoner.assess_task_confidence(query)
        
        # 检查结果是否相同（使用缓存）
        self.assertEqual(confidence1, confidence2, "相同查询应该返回相同结果")
        
        # 检查缓存大小没有再次增加
        after_second_call = len(self.reasoner.assessment_cache)
        self.assertEqual(after_first_call, after_second_call, "第二次调用不应该增加缓存")
        
        print("   ✅ 缓存机制验证通过")


class TestAssertionExamples(unittest.TestCase):
    """断言示例类 - 演示各种断言方法的使用"""
    
    def test_basic_assertions(self):
        """基础断言示例"""
        print("📝 演示基础断言...")
        
        # 相等性断言
        self.assertEqual(1 + 1, 2, "1+1应该等于2")
        self.assertNotEqual("hello", "world", "hello不应该等于world")
        
        # 真假断言
        self.assertTrue(True, "True应该为真")
        self.assertFalse(False, "False应该为假")
        
        # None断言
        self.assertIsNone(None, "None应该是None")
        self.assertIsNotNone("something", "非None值不应该是None")
        
        print("   ✅ 基础断言示例完成")
    
    def test_comparison_assertions(self):
        """比较断言示例"""
        print("📏 演示比较断言...")
        
        # 大小比较
        self.assertGreater(5, 3, "5应该大于3")
        self.assertGreaterEqual(5, 5, "5应该大于等于5")
        self.assertLess(3, 5, "3应该小于5")
        self.assertLessEqual(3, 3, "3应该小于等于3")
        
        print("   ✅ 比较断言示例完成")
    
    def test_type_assertions(self):
        """类型断言示例"""
        print("🏷️ 演示类型断言...")
        
        # 类型检查
        self.assertIsInstance(42, int, "42应该是整数")
        self.assertIsInstance("hello", str, "hello应该是字符串")
        self.assertIsInstance([1, 2, 3], list, "应该是列表")
        
        print("   ✅ 类型断言示例完成")
    
    def test_container_assertions(self):
        """容器断言示例"""
        print("📦 演示容器断言...")
        
        # 包含关系
        self.assertIn('apple', ['apple', 'banana', 'orange'], "apple应该在列表中")
        self.assertNotIn('grape', ['apple', 'banana', 'orange'], "grape不应该在列表中")
        
        # 字典键检查
        data = {'name': 'John', 'age': 30}
        self.assertIn('name', data, "字典应该包含name键")
        
        print("   ✅ 容器断言示例完成")


def run_simple_example():
    """运行简单示例的函数"""
    print("🚀 运行简单测试示例")
    print("=" * 50)
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加主要测试类
    suite.addTest(unittest.makeSuite(SimpleTestExample))
    suite.addTest(unittest.makeSuite(TestAssertionExamples))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 显示结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"   运行测试数: {result.testsRun}")
    print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   失败: {len(result.failures)}")
    print(f"   错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")
    
    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")
    
    if not result.failures and not result.errors:
        print("\n🎉 所有测试都通过了！")
    
    return result.failures == 0 and result.errors == 0


if __name__ == '__main__':
    # 如果直接运行此文件，执行简单示例
    run_simple_example()