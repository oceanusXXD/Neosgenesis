#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
单元测试运行器
整合所有模块的单元测试，提供统一的测试入口
"""

import unittest
import sys
import os
import time
from io import StringIO

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入所有测试模块
from tests.unit.test_reasoner import TestPriorReasoner, TestPriorReasonerEdgeCases
from tests.unit.test_rag_seed_generator import (
    TestRAGSeedGenerator, 
    TestRAGSeedGeneratorIntegration, 
    TestRAGSeedGeneratorPerformance
)
from tests.unit.test_mab_converger import (
    TestMABConverger, 
    TestMABConvergerGoldenTemplateManagement,
    TestMABConvergerConfidenceSystem
)


class ColoredTextTestResult(unittest.TextTestResult):
    """带颜色输出的测试结果类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.success_count = 0
        self.start_time = None
    
    def startTest(self, test):
        super().startTest(test)
        if self.start_time is None:
            self.start_time = time.time()
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        print(f"  ✅ {test._testMethodName}")
    
    def addError(self, test, err):
        super().addError(test, err)
        print(f"  ❌ {test._testMethodName} - ERROR")
        
    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(f"  ❌ {test._testMethodName} - FAILED")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        print(f"  ⏭️ {test._testMethodName} - SKIPPED: {reason}")


class UnitTestRunner:
    """单元测试运行器主类"""
    
    def __init__(self):
        self.test_modules = {
            'reasoner': {
                'name': 'PriorReasoner（轻量级分析助手）',
                'test_classes': [TestPriorReasoner, TestPriorReasonerEdgeCases],
                'description': '测试任务置信度评估和复杂度分析功能'
            },
            'rag_seed_generator': {
                'name': 'RAGSeedGenerator（RAG种子生成器）',
                'test_classes': [TestRAGSeedGenerator, TestRAGSeedGeneratorIntegration, TestRAGSeedGeneratorPerformance],
                'description': '测试搜索策略规划、结果过滤和信息综合（使用Mocking）'
            },
            'mab_converger': {
                'name': 'MABConverger（MAB收敛器）',
                'test_classes': [TestMABConverger, TestMABConvergerGoldenTemplateManagement, TestMABConvergerConfidenceSystem],
                'description': '测试路径选择算法、性能更新和黄金模板系统'
            }
        }
    
    def run_all_tests(self, verbosity=2):
        """运行所有单元测试"""
        print("🚀 开始运行 Neogenesis System 单元测试套件")
        print("=" * 70)
        
        total_start_time = time.time()
        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_skipped = 0
        
        # 为每个模块运行测试
        for module_key, module_info in self.test_modules.items():
            print(f"\n📦 测试模块: {module_info['name']}")
            print(f"📝 描述: {module_info['description']}")
            print("-" * 50)
            
            module_start_time = time.time()
            module_tests = 0
            module_failures = 0
            module_errors = 0
            module_skipped = 0
            
            # 运行该模块的所有测试类
            for test_class in module_info['test_classes']:
                print(f"\n🔍 测试类: {test_class.__name__}")
                
                # 创建测试套件
                suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
                
                # 使用自定义的测试结果类
                stream = StringIO()
                runner = unittest.TextTestRunner(
                    stream=stream,
                    verbosity=verbosity,
                    resultclass=ColoredTextTestResult
                )
                
                # 运行测试
                result = runner.run(suite)
                
                # 统计结果
                module_tests += result.testsRun
                module_failures += len(result.failures)
                module_errors += len(result.errors)
                module_skipped += len(result.skipped)
                
                # 显示详细的错误信息
                if result.failures:
                    print("\n❌ 失败的测试:")
                    for test, traceback in result.failures:
                        print(f"  - {test}: {traceback}")
                
                if result.errors:
                    print("\n💥 错误的测试:")
                    for test, traceback in result.errors:
                        print(f"  - {test}: {traceback}")
            
            # 模块测试总结
            module_duration = time.time() - module_start_time
            module_success = module_tests - module_failures - module_errors
            
            print(f"\n📊 {module_info['name']} 测试总结:")
            print(f"  总测试数: {module_tests}")
            print(f"  成功: {module_success}")
            print(f"  失败: {module_failures}")
            print(f"  错误: {module_errors}")
            print(f"  跳过: {module_skipped}")
            print(f"  耗时: {module_duration:.2f}秒")
            
            if module_failures == 0 and module_errors == 0:
                print(f"  ✅ {module_info['name']} 全部测试通过!")
            else:
                print(f"  ⚠️ {module_info['name']} 存在测试问题")
            
            # 累加到总计
            total_tests += module_tests
            total_failures += module_failures
            total_errors += module_errors
            total_skipped += module_skipped
        
        # 总体测试结果
        total_duration = time.time() - total_start_time
        total_success = total_tests - total_failures - total_errors
        
        print("\n" + "=" * 70)
        print("🎯 所有单元测试执行完成")
        print("=" * 70)
        print(f"📈 总体统计:")
        print(f"  总测试数: {total_tests}")
        print(f"  成功: {total_success}")
        print(f"  失败: {total_failures}")
        print(f"  错误: {total_errors}")
        print(f"  跳过: {total_skipped}")
        print(f"  成功率: {(total_success/total_tests)*100:.1f}%" if total_tests > 0 else "  成功率: 0%")
        print(f"  总耗时: {total_duration:.2f}秒")
        
        if total_failures == 0 and total_errors == 0:
            print("\n🎉 恭喜！所有测试都通过了！")
            print("✨ Neogenesis System 的核心组件运行正常")
        else:
            print(f"\n⚠️ 发现 {total_failures + total_errors} 个测试问题需要修复")
        
        return total_failures == 0 and total_errors == 0
    
    def run_specific_module(self, module_name, verbosity=2):
        """运行特定模块的测试"""
        if module_name not in self.test_modules:
            print(f"❌ 未找到模块 '{module_name}'")
            print(f"可用的模块: {list(self.test_modules.keys())}")
            return False
        
        module_info = self.test_modules[module_name]
        print(f"🔍 运行 {module_info['name']} 的单元测试")
        print(f"📝 {module_info['description']}")
        print("-" * 50)
        
        all_passed = True
        for test_class in module_info['test_classes']:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            runner = unittest.TextTestRunner(verbosity=verbosity)
            result = runner.run(suite)
            
            if result.failures or result.errors:
                all_passed = False
        
        return all_passed
    
    def run_specific_test(self, module_name, test_class_name, test_method=None, verbosity=2):
        """运行特定的测试类或测试方法"""
        if module_name not in self.test_modules:
            print(f"❌ 未找到模块 '{module_name}'")
            return False
        
        module_info = self.test_modules[module_name]
        
        # 查找测试类
        target_class = None
        for test_class in module_info['test_classes']:
            if test_class.__name__ == test_class_name:
                target_class = test_class
                break
        
        if target_class is None:
            print(f"❌ 在模块 '{module_name}' 中未找到测试类 '{test_class_name}'")
            available_classes = [cls.__name__ for cls in module_info['test_classes']]
            print(f"可用的测试类: {available_classes}")
            return False
        
        # 创建测试套件
        if test_method:
            # 运行特定测试方法
            suite = unittest.TestSuite()
            suite.addTest(target_class(test_method))
            print(f"🎯 运行测试: {test_class_name}.{test_method}")
        else:
            # 运行整个测试类
            suite = unittest.TestLoader().loadTestsFromTestCase(target_class)
            print(f"🎯 运行测试类: {test_class_name}")
        
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        
        return not (result.failures or result.errors)
    
    def list_all_tests(self):
        """列出所有可用的测试"""
        print("📋 Neogenesis System 单元测试清单")
        print("=" * 50)
        
        for module_key, module_info in self.test_modules.items():
            print(f"\n📦 模块: {module_key}")
            print(f"   名称: {module_info['name']}")
            print(f"   描述: {module_info['description']}")
            print("   测试类:")
            
            for test_class in module_info['test_classes']:
                print(f"   └── {test_class.__name__}")
                
                # 列出测试方法
                test_methods = [method for method in dir(test_class) 
                              if method.startswith('test_')]
                for method in test_methods[:3]:  # 只显示前3个方法
                    print(f"       ├── {method}")
                if len(test_methods) > 3:
                    print(f"       └── ... 还有 {len(test_methods) - 3} 个测试方法")


def main():
    """主函数 - 命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Neogenesis System 单元测试运行器')
    parser.add_argument('--module', '-m', help='运行特定模块的测试 (reasoner/rag_seed_generator/mab_converger)')
    parser.add_argument('--class', '-c', dest='test_class', help='运行特定测试类')
    parser.add_argument('--method', '-t', help='运行特定测试方法')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有可用的测试')
    parser.add_argument('--verbose', '-v', action='count', default=2, help='详细程度 (-v, -vv)')
    
    args = parser.parse_args()
    
    runner = UnitTestRunner()
    
    if args.list:
        runner.list_all_tests()
        return
    
    if args.module:
        if args.test_class:
            # 运行特定测试类或方法
            success = runner.run_specific_test(args.module, args.test_class, args.method, args.verbose)
        else:
            # 运行特定模块
            success = runner.run_specific_module(args.module, args.verbose)
    else:
        # 运行所有测试
        success = runner.run_all_tests(args.verbose)
    
    # 退出代码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()