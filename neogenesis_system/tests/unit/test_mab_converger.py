#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
mab_converger.py 单元测试
测试MAB收敛器的内部状态和算法逻辑
"""

import unittest
import time
import numpy as np
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from meta_mab.mab_converger import MABConverger
from meta_mab.data_structures import EnhancedDecisionArm, ReasoningPath


class TestMABConverger(unittest.TestCase):
    """MAB收敛器单元测试类"""
    
    def setUp(self):
        """测试前的设置"""
        self.mab_converger = MABConverger()
        
        # 创建测试用的思维路径
        self.test_paths = [
            ReasoningPath(
                path_id="direct_001",
                path_type="direct_reasoning",
                description="直接推理路径",
                prompt_template="使用直接推理方法：{query}"
            ),
            ReasoningPath(
                path_id="analytical_002",
                path_type="analytical_reasoning", 
                description="分析性推理路径",
                prompt_template="使用分析性推理方法：{query}"
            ),
            ReasoningPath(
                path_id="creative_003",
                path_type="creative_reasoning",
                description="创意性推理路径",
                prompt_template="使用创意性推理方法：{query}"
            )
        ]
    
    def tearDown(self):
        """测试后的清理"""
        self.mab_converger.reset_all_paths()
    
    # ==================== update_path_performance 测试 ====================
    
    def test_update_path_performance_basic(self):
        """测试基础的路径性能更新"""
        path_id = "test_path_001"
        
        # 先创建一个决策臂
        self.mab_converger.path_arms[path_id] = EnhancedDecisionArm(path_id=path_id)
        
        initial_arm = self.mab_converger.path_arms[path_id]
        initial_success_count = initial_arm.success_count
        initial_failure_count = initial_arm.failure_count
        
        # 更新成功案例
        self.mab_converger.update_path_performance(path_id, success=True, reward=0.8)
        
        updated_arm = self.mab_converger.path_arms[path_id]
        
        # 验证成功计数更新
        self.assertEqual(updated_arm.success_count, initial_success_count + 1)
        self.assertEqual(updated_arm.failure_count, initial_failure_count)
        
        # 验证成功率计算
        expected_success_rate = 1.0  # 1次成功，0次失败
        self.assertEqual(updated_arm.success_rate, expected_success_rate)
        
        # 验证奖励记录
        self.assertIn(0.8, updated_arm.rl_reward_history)
        self.assertEqual(updated_arm.total_reward, 0.8)
        
        print(f"成功更新后 - 成功率: {updated_arm.success_rate:.3f}, 总奖励: {updated_arm.total_reward:.3f}")
    
    def test_update_path_performance_multiple_updates(self):
        """测试多次性能更新"""
        path_id = "test_path_002"
        
        # 创建决策臂
        self.mab_converger.path_arms[path_id] = EnhancedDecisionArm(path_id=path_id)
        
        # 执行多次更新
        updates = [
            (True, 0.9),   # 成功，高奖励
            (True, 0.7),   # 成功，中等奖励
            (False, -0.2), # 失败，负奖励
            (True, 0.8),   # 成功，高奖励
            (False, -0.1)  # 失败，小负奖励
        ]
        
        for success, reward in updates:
            self.mab_converger.update_path_performance(path_id, success, reward)
        
        arm = self.mab_converger.path_arms[path_id]
        
        # 验证计数
        expected_success_count = 3
        expected_failure_count = 2
        self.assertEqual(arm.success_count, expected_success_count)
        self.assertEqual(arm.failure_count, expected_failure_count)
        
        # 验证成功率
        expected_success_rate = 3 / 5  # 60%
        self.assertEqual(arm.success_rate, expected_success_rate)
        
        # 验证奖励计算
        expected_total_reward = 0.9 + 0.7 + (-0.2) + 0.8 + (-0.1)  # 2.1
        self.assertAlmostEqual(arm.total_reward, expected_total_reward, places=3)
        
        # 验证平均奖励
        expected_avg_reward = expected_total_reward / 5
        actual_avg_reward = sum(arm.rl_reward_history) / len(arm.rl_reward_history) if arm.rl_reward_history else 0.0
        self.assertAlmostEqual(actual_avg_reward, expected_avg_reward, places=3)
        
        print(f"多次更新后 - 成功率: {arm.success_rate:.3f}, 平均奖励: {actual_avg_reward:.3f}")
    
    def test_update_path_performance_nonexistent_path(self):
        """测试更新不存在路径的性能（容错机制）- 🎯 根源修复版：适配新的确定性策略ID"""
        # 🎯 根源修复：现在策略ID是确定性的，不需要从实例ID解析
        nonexistent_strategy_id = "test_strategy_analytical"  # 确定性策略ID
        
        # 测试1：使用策略ID更新性能
        self.mab_converger.update_path_performance(nonexistent_strategy_id, success=True, reward=0.5)
        
        # 应该基于策略ID创建决策臂
        self.assertIn(nonexistent_strategy_id, self.mab_converger.path_arms)
        
        # 修复后：第一次更新应该正常记录性能数据
        arm = self.mab_converger.path_arms[nonexistent_strategy_id]
        self.assertEqual(arm.success_count, 1)  # 修复后：第一次就应该记录
        self.assertEqual(arm.failure_count, 0)
        self.assertEqual(arm.success_rate, 1.0)
        self.assertIn(0.5, arm.rl_reward_history)
        
        # 测试2：再次使用相同的策略ID更新性能（应该累积到同一个决策臂）
        self.mab_converger.update_path_performance(nonexistent_strategy_id, success=False, reward=-0.2)
        
        # 🔧 动态创建后：只有1个动态创建的策略
        self.assertEqual(len(self.mab_converger.path_arms), 1)  # 只有动态创建的策略
        self.assertIn(nonexistent_strategy_id, self.mab_converger.path_arms)
        
        # 性能应该累积到同一个决策臂
        self.assertEqual(arm.success_count, 1)
        self.assertEqual(arm.failure_count, 1)
        self.assertEqual(arm.success_rate, 0.5)  # 1次成功，1次失败
        
        print(f"🎯 根源修复测试完成 - 成功率: {arm.success_rate:.3f}, 策略ID: {nonexistent_strategy_id}")
        print(f"   🎯 确定性策略ID直接用于学习，无需复杂解析")
    
    def test_reasoning_path_dual_id_system(self):
        """测试ReasoningPath的双层ID系统 - 🎯 根源修复版"""
        from meta_mab.data_structures import ReasoningPath
        
        # 测试1：完整字段初始化（PathGenerator的正确输出）
        path = ReasoningPath(
            path_id="systematic_analytical_1703123456789_1234",  # 实例ID
            path_type="系统分析型",
            description="测试路径",
            prompt_template="测试模板：{task}",
            strategy_id="systematic_analytical",  # 确定性策略ID
            instance_id="systematic_analytical_1703123456789_1234"  # 实例ID
        )
        
        self.assertEqual(path.strategy_id, "systematic_analytical")
        self.assertEqual(path.instance_id, "systematic_analytical_1703123456789_1234")
        
        # 测试2：兼容性（没有strategy_id字段的情况）
        path2 = ReasoningPath(
            path_id="creative_innovative",  # 🎯 根源修复：现在path_id就是strategy_id
            path_type="创新突破型",
            description="测试路径2",
            prompt_template="测试模板2：{task}"
        )
        
        # 🎯 根源修复后：strategy_id直接等于path_id（兼容性逻辑）
        self.assertEqual(path2.strategy_id, "creative_innovative")
        self.assertEqual(path2.instance_id, "creative_innovative")
        
        print(f"🧪 ReasoningPath根源修复测试完成:")
        print(f"   Path1 - Strategy: {path.strategy_id}, Instance: {path.instance_id}")
        print(f"   Path2 - Strategy: {path2.strategy_id}, Instance: {path2.instance_id}")
        print(f"   🎯 根源修复：数据源头现在直接提供正确的确定性策略ID")
    
    def test_mab_learning_with_strategy_accumulation(self):
        """🎯 集成测试：验证MAB基于策略ID的学习累积"""
        from meta_mab.data_structures import ReasoningPath
        
        # 🔧 清空预创建的策略，隔离测试环境
        self.mab_converger.path_arms.clear()
        
        # 模拟多次生成相同策略类型的路径实例
        strategy_id = "systematic_analytical"
        
        paths_batch1 = [
            ReasoningPath(
                path_id=f"{strategy_id}_v1_1703123456789_1001",
                path_type="系统分析型",
                description="第一批路径",
                prompt_template="模板1",
                strategy_id=strategy_id,
                instance_id=f"{strategy_id}_v1_1703123456789_1001"
            ),
            ReasoningPath(
                path_id="creative_innovative_v1_1703123456789_2001",
                path_type="创新突破型", 
                description="创新路径",
                prompt_template="模板2",
                strategy_id="creative_innovative",
                instance_id="creative_innovative_v1_1703123456789_2001"
            )
        ]
        
        # 第一次选择
        selected1 = self.mab_converger.select_best_path(paths_batch1)
        
        # 模拟执行成功
        self.mab_converger.update_path_performance(selected1.strategy_id, success=True, reward=0.8)
        
        # 生成第二批相同策略类型的路径实例
        paths_batch2 = [
            ReasoningPath(
                path_id=f"{strategy_id}_v1_1703123456789_1002",  # 不同实例ID
                path_type="系统分析型",
                description="第二批路径",
                prompt_template="模板1",
                strategy_id=strategy_id,  # 相同策略ID
                instance_id=f"{strategy_id}_v1_1703123456789_1002"
            ),
            ReasoningPath(
                path_id="creative_innovative_v1_1703123456789_2002",
                path_type="创新突破型",
                description="创新路径2",
                prompt_template="模板2",
                strategy_id="creative_innovative",
                instance_id="creative_innovative_v1_1703123456789_2002"
            )
        ]
        
        # 第二次选择
        selected2 = self.mab_converger.select_best_path(paths_batch2)
        
        # 🎯 关键验证：应该只有两个策略决策臂，而不是四个实例决策臂
        self.assertEqual(len(self.mab_converger.path_arms), 2)
        self.assertIn(strategy_id, self.mab_converger.path_arms)
        self.assertIn("creative_innovative", self.mab_converger.path_arms)
        
        # 验证学习累积：系统分析型策略应该有历史数据
        systematic_arm = self.mab_converger.path_arms[strategy_id]
        creative_arm = self.mab_converger.path_arms["creative_innovative"]
        
        print(f"🔍 详细状态检查:")
        print(f"   策略数量: {len(self.mab_converger.path_arms)}")
        print(f"   所有策略: {list(self.mab_converger.path_arms.keys())}")
        print(f"   系统分析策略激活次数: {systematic_arm.activation_count}")
        print(f"   系统分析策略成功率: {systematic_arm.success_rate:.3f}")
        print(f"   系统分析策略奖励历史: {systematic_arm.rl_reward_history}")
        print(f"   创新策略激活次数: {creative_arm.activation_count}")
        print(f"   选择历史: {len(self.mab_converger.path_selection_history)}")
        
        # 验证核心功能：策略ID正确识别和累积
        self.assertGreater(systematic_arm.activation_count + creative_arm.activation_count, 0)  # 至少有一个被激活
        
        # 验证性能更新有效（至少一个策略有奖励历史）
        total_rewards = len(systematic_arm.rl_reward_history) + len(creative_arm.rl_reward_history)
        self.assertGreater(total_rewards, 0)
        
        print(f"🏆 MAB学习累积测试成功!")
    
    def test_update_path_performance_edge_values(self):
        """测试边界值的性能更新"""
        path_id = "edge_test_path"
        self.mab_converger.path_arms[path_id] = EnhancedDecisionArm(path_id=path_id)
        
        # 测试极端奖励值
        extreme_updates = [
            (True, 1.0),    # 最高奖励
            (False, -1.0),  # 最低奖励
            (True, 0.0),    # 零奖励
            (True, 10.0),   # 超高奖励
            (False, -10.0)  # 超低奖励
        ]
        
        for success, reward in extreme_updates:
            self.mab_converger.update_path_performance(path_id, success, reward)
        
        arm = self.mab_converger.path_arms[path_id]
        
        # 验证所有更新都被正确处理
        self.assertEqual(arm.success_count + arm.failure_count, len(extreme_updates))
        self.assertEqual(len(arm.rl_reward_history), len(extreme_updates))
        
        # 验证数值范围合理性
        self.assertIsInstance(arm.success_rate, float)
        self.assertGreaterEqual(arm.success_rate, 0.0)
        self.assertLessEqual(arm.success_rate, 1.0)
        
        print(f"边界值测试 - 成功率: {arm.success_rate:.3f}, 总奖励: {arm.total_reward:.3f}")
    
    # ==================== 黄金模板逻辑测试 ====================
    
    def test_check_and_promote_to_golden_template_basic(self):
        """测试基础的黄金模板提升逻辑"""
        path_id = "golden_candidate_001"
        
        # 创建一个高性能的决策臂
        arm = EnhancedDecisionArm(path_id=path_id)
        arm.option = "high_performance_reasoning"  # 设置路径类型
        
        # 手动设置高性能数据
        arm.success_count = 25  # 超过最小样本数20
        arm.failure_count = 2   # 成功率 = 25/27 ≈ 0.926，超过阈值0.90
        arm.activation_count = 27
        
        # 设置最近结果（用于稳定性检查）
        arm.recent_results = [True] * 10  # 最近10次都成功
        
        # 添加到MAB收敛器
        self.mab_converger.path_arms[path_id] = arm
        
        # 触发黄金模板检查
        self.mab_converger.update_path_performance(path_id, success=True, reward=0.9)
        
        # 验证路径被提升为黄金模板
        self.assertIn(path_id, self.mab_converger.golden_templates)
        
        # 验证模板数据
        template_data = self.mab_converger.golden_templates[path_id]
        self.assertEqual(template_data['path_id'], path_id)
        self.assertEqual(template_data['path_type'], "high_performance_reasoning")
        self.assertGreaterEqual(template_data['success_rate'], 0.90)
        self.assertGreaterEqual(template_data['total_activations'], 20)
        
        print(f"黄金模板创建成功:")
        print(f"  路径ID: {template_data['path_id']}")
        print(f"  路径类型: {template_data['path_type']}")
        print(f"  成功率: {template_data['success_rate']:.1%}")
        print(f"  激活次数: {template_data['total_activations']}")
    
    def test_check_and_promote_to_golden_template_insufficient_samples(self):
        """测试样本不足时不会提升为黄金模板"""
        path_id = "insufficient_samples"
        
        # 创建样本不足的高性能决策臂
        arm = EnhancedDecisionArm(path_id=path_id)
        arm.option = "test_reasoning"
        arm.success_count = 10  # 少于最小样本数20
        arm.failure_count = 0   # 成功率100%，但样本不足
        arm.activation_count = 10
        
        self.mab_converger.path_arms[path_id] = arm
        
        # 触发检查
        self.mab_converger.update_path_performance(path_id, success=True, reward=0.9)
        
        # 验证不会被提升为黄金模板
        self.assertNotIn(path_id, self.mab_converger.golden_templates)
        
        print(f"样本不足（{arm.activation_count}）不会提升为黄金模板")
    
    def test_check_and_promote_to_golden_template_low_success_rate(self):
        """测试成功率不足时不会提升为黄金模板"""
        path_id = "low_success_rate"
        
        # 创建成功率不足的决策臂
        arm = EnhancedDecisionArm(path_id=path_id)
        arm.option = "low_performance_reasoning"
        arm.success_count = 16  # 成功率 = 16/25 = 64%，低于阈值90%
        arm.failure_count = 9
        arm.activation_count = 25
        
        self.mab_converger.path_arms[path_id] = arm
        
        # 触发检查
        self.mab_converger.update_path_performance(path_id, success=False, reward=-0.2)
        
        # 验证不会被提升为黄金模板
        self.assertNotIn(path_id, self.mab_converger.golden_templates)
        
        print(f"成功率不足（{arm.success_rate:.1%}）不会提升为黄金模板")
    
    def test_check_and_promote_to_golden_template_instability(self):
        """测试不稳定的路径不会提升为黄金模板"""
        path_id = "unstable_path"
        
        # 创建总体性能好但最近不稳定的决策臂
        arm = EnhancedDecisionArm(path_id=path_id)
        arm.option = "unstable_reasoning"
        arm.success_count = 27  # 总体成功率 = 27/30 = 90%
        arm.failure_count = 3
        arm.activation_count = 30
        
        # 设置不稳定的最近结果
        arm.recent_results = [True, True, False, False, False, True, False, True, False, False]  # 最近10次中有6次失败
        
        self.mab_converger.path_arms[path_id] = arm
        
        # 触发检查
        self.mab_converger.update_path_performance(path_id, success=True, reward=0.8)
        
        # 验证不会被提升为黄金模板（由于最近表现不稳定）
        self.assertNotIn(path_id, self.mab_converger.golden_templates)
        
        print(f"不稳定路径（最近成功率: {sum(arm.recent_results[-10:])/10:.1%}）不会提升为黄金模板")
    
    def test_golden_template_limit(self):
        """测试黄金模板数量限制"""
        # 获取配置的最大模板数
        max_templates = self.mab_converger.golden_template_config['max_golden_templates']
        
        # 创建超过限制数量的高性能路径
        for i in range(max_templates + 5):
            path_id = f"golden_path_{i:03d}"
            
            arm = EnhancedDecisionArm(path_id=path_id)
            arm.option = f"reasoning_type_{i}"
            arm.success_count = 25
            arm.failure_count = 2
            arm.activation_count = 27
            arm.recent_results = [True] * 10
            
            self.mab_converger.path_arms[path_id] = arm
            
            # 触发黄金模板检查
            self.mab_converger._check_and_promote_to_golden_template(path_id, arm)
        
        # 验证模板数量不超过限制
        self.assertLessEqual(len(self.mab_converger.golden_templates), max_templates)
        
        print(f"黄金模板数量被限制在 {len(self.mab_converger.golden_templates)}/{max_templates}")
    
    def test_update_existing_golden_template(self):
        """测试更新已有黄金模板"""
        path_id = "existing_golden"
        
        # 先创建一个黄金模板
        arm = EnhancedDecisionArm(path_id=path_id)
        arm.option = "golden_reasoning"
        arm.success_count = 20
        arm.failure_count = 1
        arm.activation_count = 21
        arm.recent_results = [True] * 10
        
        self.mab_converger.path_arms[path_id] = arm
        
        # 第一次提升为黄金模板
        self.mab_converger._check_and_promote_to_golden_template(path_id, arm)
        
        original_template = self.mab_converger.golden_templates[path_id].copy()
        
        # 继续更新性能
        self.mab_converger.update_path_performance(path_id, success=True, reward=0.95)
        
        # 验证模板被更新
        updated_template = self.mab_converger.golden_templates[path_id]
        
        self.assertGreater(updated_template['success_rate'], original_template['success_rate'])
        self.assertGreater(updated_template['total_activations'], original_template['total_activations'])
        self.assertGreater(updated_template['last_updated'], original_template['last_updated'])
        
        print(f"黄金模板更新:")
        print(f"  原始成功率: {original_template['success_rate']:.1%}")
        print(f"  更新成功率: {updated_template['success_rate']:.1%}")
    
    # ==================== 算法选择测试 ====================
    
    def test_select_best_path_with_golden_template(self):
        """测试黄金模板优先选择"""
        # 先创建一个黄金模板
        golden_path = self.test_paths[0]  # 使用第一个路径作为黄金模板
        
        # 手动添加黄金模板
        template_data = {
            'path_id': golden_path.path_id,
            'path_type': golden_path.path_type,
            'description': golden_path.description,
            'success_rate': 0.95,
            'total_activations': 30,
            'average_reward': 0.85,
            'created_timestamp': time.time(),
            'last_updated': time.time(),
            'promotion_reason': 'test',
            'stability_score': 0.9,
            'usage_count': 0
        }
        self.mab_converger.golden_templates[golden_path.path_id] = template_data
        
        # 选择最佳路径
        selected_path = self.mab_converger.select_best_path(self.test_paths)
        
        # 验证选择了黄金模板路径
        self.assertEqual(selected_path.path_id, golden_path.path_id)
        
        # 验证黄金模板使用统计被更新
        self.assertEqual(self.mab_converger.template_usage_stats[golden_path.path_id], 1)
        
        # 验证模板匹配历史被记录
        self.assertEqual(len(self.mab_converger.template_match_history), 1)
        
        print(f"黄金模板优先选择: {selected_path.path_type}")
    
    def test_select_best_path_thompson_sampling(self):
        """测试Thompson采样算法"""
        # 为路径创建不同性能的决策臂
        for i, path in enumerate(self.test_paths):
            arm = EnhancedDecisionArm(path_id=path.path_id)
            arm.option = path.path_type
            
            # 设置不同的性能数据
            if i == 0:  # 最好的路径
                arm.success_count = 8
                arm.failure_count = 2
            elif i == 1:  # 中等路径
                arm.success_count = 5
                arm.failure_count = 5
            else:  # 较差的路径
                arm.success_count = 2
                arm.failure_count = 8
            
            arm.activation_count = arm.success_count + arm.failure_count
            self.mab_converger.path_arms[path.path_id] = arm
        
        # 使用Thompson采样选择路径
        selected_path = self.mab_converger.select_best_path(self.test_paths, algorithm='thompson_sampling')
        
        # 验证选择了某个路径
        self.assertIn(selected_path, self.test_paths)
        
        # 验证选择历史被记录
        self.assertEqual(len(self.mab_converger.path_selection_history), 1)
        history_record = self.mab_converger.path_selection_history[0]
        self.assertEqual(history_record['algorithm'], 'thompson_sampling')
        self.assertEqual(history_record['path_id'], selected_path.path_id)
        
        print(f"Thompson采样选择: {selected_path.path_type}")
    
    def test_select_best_path_single_path(self):
        """测试单个路径的选择"""
        single_path = [self.test_paths[0]]
        
        selected_path = self.mab_converger.select_best_path(single_path)
        
        # 单个路径应该直接返回
        self.assertEqual(selected_path, single_path[0])
        
        print(f"单路径直接选择: {selected_path.path_type}")
    
    def test_select_best_path_empty_list(self):
        """测试空路径列表的处理"""
        with self.assertRaises(ValueError):
            self.mab_converger.select_best_path([])
    
    # ==================== 收敛检测测试 ====================
    
    def test_check_path_convergence_insufficient_samples(self):
        """测试样本不足时的收敛检测"""
        # 创建少量样本的路径
        for i, path in enumerate(self.test_paths[:2]):
            arm = EnhancedDecisionArm(path_id=path.path_id)
            arm.success_count = 2
            arm.failure_count = 1
            arm.activation_count = 3
            self.mab_converger.path_arms[path.path_id] = arm
        
        # 样本不足，应该未收敛
        is_converged = self.mab_converger.check_path_convergence()
        self.assertFalse(is_converged)
        
        print("样本不足，未收敛")
    
    def test_check_path_convergence_converged(self):
        """测试已收敛的情况"""
        # 创建性能相似的路径（低方差 = 收敛）
        for i, path in enumerate(self.test_paths):
            arm = EnhancedDecisionArm(path_id=path.path_id)
            arm.success_count = 15  # 成功率都是75%
            arm.failure_count = 5
            arm.activation_count = 20
            self.mab_converger.path_arms[path.path_id] = arm
        
        # 性能相似，应该收敛
        is_converged = self.mab_converger.check_path_convergence()
        self.assertTrue(is_converged)
        
        print("性能相似，已收敛")
    
    def test_check_path_convergence_not_converged(self):
        """测试未收敛的情况"""
        # 创建性能差异大的路径（高方差 = 未收敛）
        success_rates = [0.9, 0.5, 0.1]  # 差异很大
        
        for i, path in enumerate(self.test_paths):
            arm = EnhancedDecisionArm(path_id=path.path_id)
            success_count = int(20 * success_rates[i])
            arm.success_count = success_count
            arm.failure_count = 20 - success_count
            arm.activation_count = 20
            self.mab_converger.path_arms[path.path_id] = arm
        
        # 性能差异大，应该未收敛
        is_converged = self.mab_converger.check_path_convergence()
        self.assertFalse(is_converged)
        
        print("性能差异大，未收敛")
    
    # ==================== 统计信息测试 ====================
    
    def test_get_path_statistics(self):
        """测试路径统计信息获取"""
        # 🔧 清空预创建的策略，隔离测试环境
        self.mab_converger.path_arms.clear()
        
        # 创建测试数据
        for i, path in enumerate(self.test_paths):
            arm = EnhancedDecisionArm(path_id=path.path_id)
            arm.option = path.path_type
            arm.success_count = (i + 1) * 5
            arm.failure_count = (3 - i) * 2
            arm.activation_count = arm.success_count + arm.failure_count
            arm.last_used = time.time()
            self.mab_converger.path_arms[path.path_id] = arm
        
        # 获取统计信息
        stats = self.mab_converger.get_path_statistics()
        
        # 验证统计结构
        self.assertEqual(len(stats), len(self.test_paths))
        
        for path_id, path_stats in stats.items():
            # 验证必要字段
            required_fields = [
                'path_id', 'path_type', 'success_count', 'failure_count',
                'success_rate', 'activation_count', 'is_golden_template'
            ]
            for field in required_fields:
                self.assertIn(field, path_stats)
            
            # 验证数据类型
            self.assertIsInstance(path_stats['success_rate'], float)
            self.assertIsInstance(path_stats['is_golden_template'], bool)
            
        print(f"路径统计信息获取成功，包含 {len(stats)} 个路径")
    
    def test_get_system_path_summary(self):
        """测试系统路径摘要"""
        # 🔧 清空预创建的策略，隔离测试环境  
        self.mab_converger.path_arms.clear()
        
        # 创建一些测试数据
        for path in self.test_paths:
            arm = EnhancedDecisionArm(path_id=path.path_id)
            arm.option = path.path_type
            arm.success_count = 10
            arm.failure_count = 2
            arm.activation_count = 12
            self.mab_converger.path_arms[path.path_id] = arm
        
        # 设置一些选择历史
        self.mab_converger.total_path_selections = 15
        
        summary = self.mab_converger.get_system_path_summary()
        
        # 验证摘要结构
        required_fields = [
            'total_paths', 'total_selections', 'is_converged',
            'most_used_path', 'best_performing_path'
        ]
        for field in required_fields:
            self.assertIn(field, summary)
        
        # 验证数据
        self.assertEqual(summary['total_paths'], len(self.test_paths))
        self.assertEqual(summary['total_selections'], 15)
        # 接受numpy布尔值或Python布尔值
        self.assertIn(type(summary['is_converged']).__name__, ['bool', 'bool_'])
        
        print(f"系统摘要: {summary['total_paths']} 路径, {summary['total_selections']} 次选择")


class TestMABConvergerGoldenTemplateManagement(unittest.TestCase):
    """黄金模板管理功能测试"""
    
    def setUp(self):
        self.mab_converger = MABConverger()
    
    def test_get_golden_templates(self):
        """测试获取黄金模板"""
        # 添加一些模板
        template_data = {
            'path_id': 'test_template',
            'path_type': 'test_reasoning',
            'success_rate': 0.95,
            'created_timestamp': time.time()
        }
        self.mab_converger.golden_templates['test_template'] = template_data
        
        templates = self.mab_converger.get_golden_templates()
        
        self.assertIn('test_template', templates)
        self.assertEqual(templates['test_template']['path_type'], 'test_reasoning')
    
    def test_remove_golden_template(self):
        """测试移除黄金模板"""
        # 添加模板
        self.mab_converger.golden_templates['test_remove'] = {'path_type': 'test'}
        
        # 移除模板
        result = self.mab_converger.remove_golden_template('test_remove')
        
        self.assertTrue(result)
        self.assertNotIn('test_remove', self.mab_converger.golden_templates)
        
        # 移除不存在的模板
        result = self.mab_converger.remove_golden_template('nonexistent')
        self.assertFalse(result)
    
    def test_clear_golden_templates(self):
        """测试清空所有黄金模板"""
        # 添加一些模板
        for i in range(3):
            self.mab_converger.golden_templates[f'template_{i}'] = {'path_type': f'type_{i}'}
        
        self.mab_converger.clear_golden_templates()
        
        self.assertEqual(len(self.mab_converger.golden_templates), 0)
        self.assertEqual(len(self.mab_converger.template_usage_stats), 0)
    
    def test_export_import_golden_templates(self):
        """测试黄金模板的导出和导入"""
        # 创建测试模板
        test_templates = {
            'template_1': {
                'path_type': 'analytical',
                'success_rate': 0.92,
                'created_timestamp': time.time()
            },
            'template_2': {
                'path_type': 'creative',
                'success_rate': 0.88,
                'created_timestamp': time.time()
            }
        }
        
        self.mab_converger.golden_templates.update(test_templates)
        self.mab_converger.template_usage_stats['template_1'] = 5
        
        # 导出
        exported_data = self.mab_converger.export_golden_templates()
        self.assertIsInstance(exported_data, str)
        
        # 清空后导入
        self.mab_converger.clear_golden_templates()
        
        import_result = self.mab_converger.import_golden_templates(exported_data)
        
        self.assertTrue(import_result)
        self.assertEqual(len(self.mab_converger.golden_templates), 2)
        self.assertIn('template_1', self.mab_converger.golden_templates)
        self.assertEqual(self.mab_converger.template_usage_stats['template_1'], 5)


class TestMABConvergerConfidenceSystem(unittest.TestCase):
    """置信度系统测试"""
    
    def setUp(self):
        self.mab_converger = MABConverger()
    
    def test_get_path_confidence_insufficient_samples(self):
        """测试样本不足时的置信度"""
        path_id = "low_sample_path"
        arm = EnhancedDecisionArm(path_id=path_id)
        arm.success_count = 2
        arm.failure_count = 1
        arm.activation_count = 3
        
        self.mab_converger.path_arms[path_id] = arm
        
        confidence = self.mab_converger.get_path_confidence(path_id)
        
        # 样本不足应该有较低的置信度
        self.assertLess(confidence, 0.5)
        print(f"低样本置信度: {confidence:.3f}")
    
    def test_get_path_confidence_high_performance(self):
        """测试高性能路径的置信度"""
        path_id = "high_perf_path"
        arm = EnhancedDecisionArm(path_id=path_id)
        arm.success_count = 45
        arm.failure_count = 5
        arm.activation_count = 50
        arm.recent_results = [True] * 10  # 最近表现很好
        
        self.mab_converger.path_arms[path_id] = arm
        
        confidence = self.mab_converger.get_path_confidence(path_id)
        
        # 高性能应该有高置信度
        self.assertGreater(confidence, 0.8)
        print(f"高性能置信度: {confidence:.3f}")
    
    def test_check_low_confidence_scenario(self):
        """测试低置信度场景检测"""
        # 创建所有路径都表现很差的情况 - 使用更极端的数据
        for i in range(3):
            path_id = f"poor_path_{i}"
            arm = EnhancedDecisionArm(path_id=path_id)
            arm.success_count = 0  # 完全失败
            arm.failure_count = 10
            arm.activation_count = 10
            
            self.mab_converger.path_arms[path_id] = arm
        
        # 使用较高的阈值来确保检测到低置信度场景
        is_low_confidence = self.mab_converger.check_low_confidence_scenario(threshold=0.5)
        
        self.assertTrue(is_low_confidence)
        print("检测到低置信度场景")
    
    def test_get_confidence_analysis(self):
        """测试置信度分析"""
        # 🔧 清空预创建的策略，隔离测试环境
        self.mab_converger.path_arms.clear()
        
        # 创建不同性能的路径
        performances = [(8, 2), (5, 5), (2, 8)]  # 高、中、低性能
        
        for i, (success, failure) in enumerate(performances):
            path_id = f"analysis_path_{i}"
            arm = EnhancedDecisionArm(path_id=path_id)
            arm.success_count = success
            arm.failure_count = failure
            arm.activation_count = success + failure
            
            self.mab_converger.path_arms[path_id] = arm
        
        analysis = self.mab_converger.get_confidence_analysis()
        
        # 验证分析结构
        required_fields = [
            'total_paths', 'max_confidence', 'min_confidence',
            'avg_confidence', 'confidence_distribution'
        ]
        for field in required_fields:
            self.assertIn(field, analysis)
        
        # 验证数据合理性
        self.assertEqual(analysis['total_paths'], 3)
        self.assertGreaterEqual(analysis['max_confidence'], analysis['min_confidence'])
        
        print(f"置信度分析: 平均{analysis['avg_confidence']:.3f}, 范围{analysis['min_confidence']:.3f}-{analysis['max_confidence']:.3f}")


if __name__ == '__main__':
    # 设置详细的测试输出
    unittest.main(verbosity=2)