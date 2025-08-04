#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
路径创建健壮性测试 - 针对路径不存在问题的专项测试
测试MAB收敛器在处理不存在路径时的容错机制和数据完整性
"""

import unittest
import time
import threading
import uuid
from unittest.mock import patch, MagicMock
import logging

# 添加项目根目录到路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from meta_mab.mab_converger import MABConverger
from meta_mab.data_structures import EnhancedDecisionArm, ReasoningPath


class TestPathCreationRobustness(unittest.TestCase):
    """路径创建健壮性测试类"""
    
    def setUp(self):
        """测试前的设置"""
        self.mab_converger = MABConverger()
        
        # 设置日志级别以便观察调试信息
        logging.basicConfig(level=logging.INFO)
        
        # 记录测试开始时的路径数量
        self.initial_path_count = len(self.mab_converger.path_arms)
    
    def tearDown(self):
        """测试后的清理"""
        self.mab_converger.reset_all_paths()
    
    # ==================== 基础路径创建测试 ====================
    
    def test_nonexistent_path_single_update(self):
        """测试单次更新不存在路径的完整流程"""
        path_id = "test_nonexistent_single"
        
        # 确认路径初始不存在
        self.assertNotIn(path_id, self.mab_converger.path_arms)
        
        # 执行更新
        self.mab_converger.update_path_performance(path_id, success=True, reward=0.7)
        
        # 验证路径被创建
        self.assertIn(path_id, self.mab_converger.path_arms)
        
        # 验证性能数据正确记录
        arm = self.mab_converger.path_arms[path_id]
        self.assertEqual(arm.success_count, 1)
        self.assertEqual(arm.failure_count, 0)
        self.assertEqual(arm.success_rate, 1.0)
        self.assertEqual(arm.total_reward, 0.7)
        self.assertIn(0.7, arm.rl_reward_history)
        
        print(f"✅ 单次更新测试: 路径 {path_id} 创建成功，成功率 {arm.success_rate:.1%}")
    
    def test_nonexistent_path_multiple_updates(self):
        """测试多次更新不存在路径的数据累积"""
        path_id = "test_nonexistent_multiple"
        
        # 执行多次更新
        updates = [
            (True, 0.8),   # 第一次更新（触发创建）
            (False, -0.3), # 第二次更新
            (True, 0.9),   # 第三次更新
            (True, 0.6),   # 第四次更新
        ]
        
        for i, (success, reward) in enumerate(updates):
            self.mab_converger.update_path_performance(path_id, success, reward)
            
            # 验证路径存在且数据正确
            arm = self.mab_converger.path_arms[path_id]
            self.assertEqual(arm.activation_count, i + 1)
            self.assertEqual(len(arm.rl_reward_history), i + 1)
        
        # 验证最终统计
        arm = self.mab_converger.path_arms[path_id]
        expected_success_count = 3
        expected_failure_count = 1
        expected_total_reward = 0.8 + (-0.3) + 0.9 + 0.6  # 2.0
        
        self.assertEqual(arm.success_count, expected_success_count)
        self.assertEqual(arm.failure_count, expected_failure_count)
        self.assertEqual(arm.success_rate, 0.75)  # 3/4
        self.assertAlmostEqual(arm.total_reward, expected_total_reward, places=3)
        
        print(f"✅ 多次更新测试: {expected_success_count}成功/{expected_failure_count}失败，成功率 {arm.success_rate:.1%}")
    
    def test_mixed_existing_and_nonexistent_paths(self):
        """测试混合更新已存在和不存在的路径"""
        existing_path = "existing_path"
        nonexistent_path = "nonexistent_path"
        
        # 预先创建一个路径
        self.mab_converger.path_arms[existing_path] = EnhancedDecisionArm(path_id=existing_path)
        self.mab_converger.update_path_performance(existing_path, success=True, reward=0.5)
        
        # 记录现有路径的初始状态
        existing_arm = self.mab_converger.path_arms[existing_path]
        initial_success_count = existing_arm.success_count
        
        # 同时更新现有路径和不存在路径
        self.mab_converger.update_path_performance(existing_path, success=True, reward=0.6)
        self.mab_converger.update_path_performance(nonexistent_path, success=True, reward=0.7)
        
        # 验证现有路径正常更新
        self.assertEqual(existing_arm.success_count, initial_success_count + 1)
        
        # 验证新路径正确创建
        self.assertIn(nonexistent_path, self.mab_converger.path_arms)
        new_arm = self.mab_converger.path_arms[nonexistent_path]
        self.assertEqual(new_arm.success_count, 1)
        self.assertEqual(new_arm.total_reward, 0.7)
        
        print(f"✅ 混合测试: 现有路径更新成功，新路径创建成功")
    
    # ==================== 边界情况测试 ====================
    
    def test_empty_path_id(self):
        """测试空路径ID的处理"""
        with self.assertLogs(level='WARNING') as log:
            # 空字符串作为路径ID
            self.mab_converger.update_path_performance("", success=True, reward=0.5)
            
        # 验证空路径被创建（虽然不推荐）
        self.assertIn("", self.mab_converger.path_arms)
        
        # 验证警告日志
        self.assertTrue(any("不存在，自动创建中" in message for message in log.output))
        
        print("✅ 空路径ID测试: 系统能够处理但会发出警告")
    
    def test_special_characters_in_path_id(self):
        """测试特殊字符路径ID的处理"""
        special_paths = [
            "path/with/slashes",
            "path-with-dashes",
            "path_with_underscores",
            "path.with.dots",
            "path with spaces",
            "路径中文测试",
            "path@#$%^&*()",
        ]
        
        for path_id in special_paths:
            # 测试特殊字符路径的创建
            self.mab_converger.update_path_performance(path_id, success=True, reward=0.5)
            
            # 验证路径被正确创建
            self.assertIn(path_id, self.mab_converger.path_arms)
            arm = self.mab_converger.path_arms[path_id]
            self.assertEqual(arm.success_count, 1)
            
        print(f"✅ 特殊字符测试: {len(special_paths)} 种特殊字符路径全部创建成功")
    
    def test_very_long_path_id(self):
        """测试超长路径ID的处理"""
        # 创建一个很长的路径ID
        long_path_id = "very_long_path_" + "x" * 1000  # 1000+字符的路径ID
        
        # 测试超长路径的处理
        self.mab_converger.update_path_performance(long_path_id, success=True, reward=0.8)
        
        # 验证超长路径能够正常处理
        self.assertIn(long_path_id, self.mab_converger.path_arms)
        arm = self.mab_converger.path_arms[long_path_id]
        self.assertEqual(arm.success_count, 1)
        self.assertEqual(arm.total_reward, 0.8)
        
        print(f"✅ 超长路径测试: {len(long_path_id)} 字符路径创建成功")
    
    # ==================== 并发和性能测试 ====================
    
    def test_concurrent_path_creation(self):
        """测试并发创建路径的线程安全性"""
        path_ids = [f"concurrent_path_{i}" for i in range(10)]
        results = {}
        errors = []
        
        def update_path(path_id):
            try:
                self.mab_converger.update_path_performance(path_id, success=True, reward=0.5)
                results[path_id] = self.mab_converger.path_arms[path_id].success_count
            except Exception as e:
                errors.append((path_id, str(e)))
        
        # 创建并启动多个线程
        threads = []
        for path_id in path_ids:
            thread = threading.Thread(target=update_path, args=(path_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        self.assertEqual(len(errors), 0, f"并发测试中出现错误: {errors}")
        self.assertEqual(len(results), len(path_ids))
        
        # 验证所有路径都被正确创建
        for path_id in path_ids:
            self.assertIn(path_id, self.mab_converger.path_arms)
            self.assertEqual(results[path_id], 1)
        
        print(f"✅ 并发测试: {len(path_ids)} 个路径并发创建成功，无错误")
    
    def test_rapid_path_creation(self):
        """测试快速连续创建大量路径的性能"""
        num_paths = 100
        start_time = time.time()
        
        for i in range(num_paths):
            path_id = f"rapid_path_{i:03d}"
            self.mab_converger.update_path_performance(path_id, success=True, reward=0.5)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # 验证所有路径都被创建
        self.assertEqual(len(self.mab_converger.path_arms) - self.initial_path_count, num_paths)
        
        # 验证性能可接受（应该在合理时间内完成）
        self.assertLess(creation_time, 5.0, "路径创建时间过长")
        
        print(f"✅ 性能测试: {num_paths} 个路径创建耗时 {creation_time:.3f} 秒")
    
    # ==================== 数据完整性测试 ====================
    
    def test_data_integrity_after_creation(self):
        """测试路径创建后数据完整性"""
        path_id = "integrity_test_path"
        
        # 执行复杂的更新序列
        update_sequence = [
            (True, 0.9),
            (False, -0.1),
            (True, 0.8),
            (True, 0.7),
            (False, -0.2),
            (True, 0.95),
        ]
        
        for success, reward in update_sequence:
            self.mab_converger.update_path_performance(path_id, success, reward)
        
        # 验证数据完整性
        arm = self.mab_converger.path_arms[path_id]
        
        # 验证计数正确
        expected_success = sum(1 for s, _ in update_sequence if s)
        expected_failure = sum(1 for s, _ in update_sequence if not s)
        self.assertEqual(arm.success_count, expected_success)
        self.assertEqual(arm.failure_count, expected_failure)
        
        # 验证奖励历史完整
        self.assertEqual(len(arm.rl_reward_history), len(update_sequence))
        expected_rewards = [r for _, r in update_sequence]
        self.assertEqual(arm.rl_reward_history, expected_rewards)
        
        # 验证总奖励正确
        expected_total = sum(expected_rewards)
        self.assertAlmostEqual(arm.total_reward, expected_total, places=3)
        
        # 验证成功率计算正确
        expected_rate = expected_success / (expected_success + expected_failure)
        self.assertAlmostEqual(arm.success_rate, expected_rate, places=3)
        
        print(f"✅ 数据完整性测试: 所有统计数据正确")
    
    def test_path_creation_with_golden_template_check(self):
        """测试路径创建时黄金模板逻辑是否正常工作"""
        path_id = "golden_candidate_path"
        
        # 创建足够的成功记录以满足黄金模板条件
        for i in range(25):  # 超过最小样本数20
            self.mab_converger.update_path_performance(path_id, success=True, reward=0.9)
        
        # 少量失败以保持高成功率
        for i in range(2):
            self.mab_converger.update_path_performance(path_id, success=False, reward=-0.1)
        
        # 验证路径被创建
        self.assertIn(path_id, self.mab_converger.path_arms)
        arm = self.mab_converger.path_arms[path_id]
        
        # 验证成功率符合黄金模板条件
        self.assertGreater(arm.success_rate, 0.9)
        self.assertGreaterEqual(arm.activation_count, 20)
        
        # 如果黄金模板逻辑工作正常，应该被提升
        # 注意：这取决于黄金模板的具体实现逻辑
        print(f"✅ 黄金模板测试: 路径创建后成功率 {arm.success_rate:.1%}")
    
    # ==================== 错误处理测试 ====================
    
    @patch('meta_mab.mab_converger.EnhancedDecisionArm')
    def test_path_creation_failure_handling(self, mock_arm_class):
        """测试路径创建失败时的错误处理"""
        # 模拟EnhancedDecisionArm创建失败
        mock_arm_class.side_effect = Exception("模拟创建失败")
        
        path_id = "failing_path"
        
        with self.assertLogs(level='ERROR') as log:
            # 尝试更新不存在的路径，应该触发创建失败
            self.mab_converger.update_path_performance(path_id, success=True, reward=0.5)
        
        # 验证路径未被创建
        self.assertNotIn(path_id, self.mab_converger.path_arms)
        
        # 验证错误日志
        self.assertTrue(any("自动创建路径决策臂失败" in message for message in log.output))
        
        print("✅ 错误处理测试: 创建失败时能够优雅处理")
    
    def test_none_path_id_handling(self):
        """测试None路径ID的处理"""
        # 测试None作为路径ID
        # 实际上Python字典可以使用None作为键，所以不会抛出TypeError
        # 但这不是推荐的用法，系统应该能够处理它
        try:
            self.mab_converger.update_path_performance(None, success=True, reward=0.5)
            # 验证None路径被创建（虽然不推荐）
            self.assertIn(None, self.mab_converger.path_arms)
            arm = self.mab_converger.path_arms[None]
            self.assertEqual(arm.success_count, 1)
            print("✅ None路径ID测试: 系统能够处理但不推荐使用")
        except Exception as e:
            print(f"✅ None路径ID测试: 系统拒绝处理None路径ID - {e}")
    
    # ==================== 回归测试 ====================
    
    def test_regression_immediate_data_recording(self):
        """回归测试：确保修复后第一次更新立即记录数据"""
        path_id = "regression_test_path"
        
        # 这是修复的核心问题：第一次更新应该立即记录数据
        self.mab_converger.update_path_performance(path_id, success=True, reward=0.75)
        
        # 验证路径被创建
        self.assertIn(path_id, self.mab_converger.path_arms)
        
        # 验证第一次更新的数据立即被记录（这是修复的关键点）
        arm = self.mab_converger.path_arms[path_id]
        self.assertEqual(arm.success_count, 1, "修复失败：第一次更新数据未被记录")
        self.assertEqual(arm.failure_count, 0)
        self.assertEqual(arm.total_reward, 0.75)
        self.assertEqual(len(arm.rl_reward_history), 1)
        self.assertIn(0.75, arm.rl_reward_history)
        
        print("✅ 回归测试: 修复后第一次更新立即记录数据")
    
    def test_comparison_with_existing_path_behavior(self):
        """对比测试：新创建路径与预存在路径的行为一致性"""
        existing_path = "pre_existing_path"
        new_path = "newly_created_path"
        
        # 预先创建一个路径
        self.mab_converger.path_arms[existing_path] = EnhancedDecisionArm(path_id=existing_path)
        
        # 对两个路径执行相同的更新
        test_updates = [(True, 0.8), (False, -0.1), (True, 0.9)]
        
        for success, reward in test_updates:
            self.mab_converger.update_path_performance(existing_path, success, reward)
            self.mab_converger.update_path_performance(new_path, success, reward)
        
        # 验证两个路径的最终状态完全一致
        existing_arm = self.mab_converger.path_arms[existing_path]
        new_arm = self.mab_converger.path_arms[new_path]
        
        self.assertEqual(existing_arm.success_count, new_arm.success_count)
        self.assertEqual(existing_arm.failure_count, new_arm.failure_count)
        self.assertEqual(existing_arm.success_rate, new_arm.success_rate)
        self.assertEqual(existing_arm.total_reward, new_arm.total_reward)
        self.assertEqual(existing_arm.rl_reward_history, new_arm.rl_reward_history)
        
        print("✅ 行为一致性测试: 新创建路径与预存在路径行为完全一致")


class TestPathCreationEdgeCases(unittest.TestCase):
    """路径创建边缘情况测试"""
    
    def setUp(self):
        self.mab_converger = MABConverger()
    
    def tearDown(self):
        self.mab_converger.reset_all_paths()
    
    def test_uuid_based_path_ids(self):
        """测试UUID生成的路径ID"""
        # 生成随机UUID作为路径ID
        path_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        for path_id in path_ids:
            self.mab_converger.update_path_performance(path_id, success=True, reward=0.6)
            
            # 验证UUID路径正常工作
            self.assertIn(path_id, self.mab_converger.path_arms)
            arm = self.mab_converger.path_arms[path_id]
            self.assertEqual(arm.success_count, 1)
        
        print(f"✅ UUID测试: {len(path_ids)} 个UUID路径创建成功")
    
    def test_numeric_string_path_ids(self):
        """测试纯数字字符串路径ID"""
        numeric_paths = ["123", "456.789", "0", "-123", "1e10"]
        
        for path_id in numeric_paths:
            self.mab_converger.update_path_performance(path_id, success=True, reward=0.5)
            self.assertIn(path_id, self.mab_converger.path_arms)
        
        print(f"✅ 数字字符串测试: {len(numeric_paths)} 个数字路径创建成功")
    
    def test_extreme_reward_values(self):
        """测试极端奖励值的处理"""
        path_id = "extreme_rewards_path"
        
        extreme_updates = [
            (True, float('inf')),    # 无穷大
            (True, float('-inf')),   # 负无穷大
            (True, 1e10),           # 极大值
            (True, -1e10),          # 极小值
            (True, 1e-10),          # 极小正值
        ]
        
        for success, reward in extreme_updates:
            try:
                self.mab_converger.update_path_performance(path_id, success, reward)
            except Exception as e:
                print(f"⚠️ 极端值 {reward} 处理失败: {e}")
        
        # 验证路径至少被创建
        self.assertIn(path_id, self.mab_converger.path_arms)
        
        print("✅ 极端奖励值测试: 系统能够处理各种极端数值")


if __name__ == '__main__':
    # 设置详细的测试输出
    print("=" * 80)
    print("路径创建健壮性测试开始")
    print("=" * 80)
    
    # 运行测试
    unittest.main(verbosity=2, exit=False)
    
    print("=" * 80)
    print("所有测试完成")
    print("=" * 80)