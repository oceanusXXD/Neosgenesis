#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
框架核心组件单元测试 - Framework Core Unit Tests
测试新定义的数据结构和抽象接口的功能正确性

这些测试确保：
1. 数据结构按预期工作
2. 抽象接口能正确约束实现
3. 组件间能正确协作
4. 错误处理机制有效
"""

import unittest
import time
import sys
import os
from typing import Any, Dict, Optional, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from neogenesis_system.shared.data_structures import (
        Action, Plan, Observation, ExecutionContext, AgentState,
        ActionStatus, PlanStatus
    )
    from neogenesis_system.abstractions import (
        BasePlanner, BaseToolExecutor, BaseMemory, BaseAgent
    )
except ImportError:
    # 如果导入失败，直接执行文件内容
    exec(open('neogenesis_system/data_structures.py', encoding='utf-8').read())
    
    from abc import ABC, abstractmethod
    
    
    class BasePlanner(ABC):
        def __init__(self, name: str, description: str):
            self.name = name
            self.description = description
        
        @abstractmethod
        def create_plan(self, query: str, memory: Any, context: Optional[Dict[str, Any]] = None) -> Plan:
            pass
        
        @abstractmethod
        def validate_plan(self, plan: Plan) -> bool:
            pass
    
    class BaseToolExecutor(ABC):
        def __init__(self, name: str, description: str):
            self.name = name
            self.description = description
        
        @abstractmethod
        def execute_plan(self, plan: Plan, context: Optional[ExecutionContext] = None) -> List[Observation]:
            pass
        
        @abstractmethod
        def execute_action(self, action: Action) -> Observation:
            pass
    
    class BaseMemory(ABC):
        def __init__(self, name: str, description: str):
            self.name = name
            self.description = description
        
        @abstractmethod
        def store(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
            pass
        
        @abstractmethod
        def retrieve(self, key: str) -> Optional[Any]:
            pass
        
        @abstractmethod
        def delete(self, key: str) -> bool:
            pass
        
        @abstractmethod
        def exists(self, key: str) -> bool:
            pass
    
    class BaseAgent(ABC):
        def __init__(self, planner: BasePlanner, tool_executor: BaseToolExecutor, memory: BaseMemory, name: str = "Agent"):
            self.planner = planner
            self.tool_executor = tool_executor
            self.memory = memory
            self.name = name
            self.stats = {"total_tasks": 0, "successful_tasks": 0, "failed_tasks": 0, "total_execution_time": 0.0}
        
        @abstractmethod
        def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
            pass
        
        def update_stats(self, success: bool, execution_time: float, plan_size: int):
            self.stats["total_tasks"] += 1
            if success:
                self.stats["successful_tasks"] += 1
            else:
                self.stats["failed_tasks"] += 1
            self.stats["total_execution_time"] += execution_time
        
        @property
        def success_rate(self) -> float:
            total = self.stats["total_tasks"]
            return self.stats["successful_tasks"] / total if total > 0 else 0.0


class TestDataStructures(unittest.TestCase):
    """测试数据结构的基本功能"""
    
    def test_action_creation(self):
        """测试Action创建和基本操作"""
        action = Action("test_tool", {"param": "value"})
        
        # 基本属性测试
        self.assertEqual(action.tool_name, "test_tool")
        self.assertEqual(action.tool_input, {"param": "value"})
        self.assertEqual(action.status, ActionStatus.PENDING)
        self.assertIsInstance(action.created_at, float)
        self.assertTrue(action.action_id.startswith("action_test_tool_"))
        
        # 状态转换测试
        action.start_execution()
        self.assertEqual(action.status, ActionStatus.EXECUTING)
        self.assertIsNotNone(action.started_at)
        
        action.complete_execution()
        self.assertEqual(action.status, ActionStatus.COMPLETED)
        self.assertIsNotNone(action.completed_at)
        self.assertIsNotNone(action.execution_time)
        self.assertGreater(action.execution_time, 0)
    
    def test_action_failure(self):
        """测试Action失败处理"""
        action = Action("test_tool", {"param": "value"})
        action.start_execution()
        action.fail_execution()
        
        self.assertEqual(action.status, ActionStatus.FAILED)
        self.assertIsNotNone(action.completed_at)
    
    def test_plan_creation(self):
        """测试Plan创建和操作"""
        action1 = Action("tool1", {"param": "value1"})
        action2 = Action("tool2", {"param": "value2"})
        
        # 包含行动的计划
        plan = Plan("测试思考过程", [action1, action2])
        
        self.assertEqual(plan.thought, "测试思考过程")
        self.assertEqual(len(plan.actions), 2)
        self.assertIsNone(plan.final_answer)
        self.assertFalse(plan.is_direct_answer)
        self.assertEqual(plan.action_count, 2)
        self.assertEqual(plan.status, PlanStatus.CREATED)
        self.assertTrue(plan.plan_id.startswith("plan_"))
        
        # 直接回答的计划
        direct_plan = Plan("直接回答", final_answer="这是直接答案")
        self.assertTrue(direct_plan.is_direct_answer)
        self.assertEqual(direct_plan.action_count, 0)
    
    def test_plan_status_transitions(self):
        """测试Plan状态转换"""
        plan = Plan("测试计划")
        
        plan.start_execution()
        self.assertEqual(plan.status, PlanStatus.EXECUTING)
        
        plan.complete_execution()
        self.assertEqual(plan.status, PlanStatus.COMPLETED)
        
        # 测试失败状态
        plan2 = Plan("测试计划2")
        plan2.start_execution()
        plan2.fail_execution()
        self.assertEqual(plan2.status, PlanStatus.FAILED)
    
    def test_observation_creation(self):
        """测试Observation创建"""
        action = Action("test_tool", {"param": "value"})
        observation = Observation(action, "测试输出", True, None, 0.5)
        
        self.assertEqual(observation.action, action)
        self.assertEqual(observation.output, "测试输出")
        self.assertTrue(observation.success)
        self.assertIsNone(observation.error_message)
        self.assertEqual(observation.execution_time, 0.5)
        self.assertTrue(observation.is_successful())
        self.assertEqual(observation.action_id, action.action_id)
        self.assertEqual(observation.tool_name, action.tool_name)
    
    def test_observation_failure(self):
        """测试Observation失败情况"""
        action = Action("test_tool", {"param": "value"})
        observation = Observation(action, "", False, "测试错误", 0.1)
        
        self.assertFalse(observation.success)
        self.assertEqual(observation.error_message, "测试错误")
        self.assertFalse(observation.is_successful())
    
    def test_execution_context(self):
        """测试ExecutionContext"""
        plan = Plan("测试计划")
        context = ExecutionContext(plan)
        
        self.assertEqual(context.plan, plan)
        self.assertEqual(len(context.observations), 0)
        self.assertTrue(context.context_id.startswith("ctx_"))
        self.assertEqual(context.success_rate, 0.0)
        
        # 添加观察结果
        action = Action("test_tool", {"param": "value"})
        obs1 = Observation(action, "成功", True)
        obs2 = Observation(action, "", False, "失败")
        
        context.add_observation(obs1)
        context.add_observation(obs2)
        
        self.assertEqual(len(context.observations), 2)
        self.assertEqual(context.success_rate, 0.5)
        self.assertEqual(len(context.successful_observations), 1)
        self.assertEqual(len(context.failed_observations), 1)


class TestMockImplementations(unittest.TestCase):
    """测试模拟实现以验证抽象接口"""
    
    def setUp(self):
        """设置测试环境"""
        
        class MockPlanner(BasePlanner):
            def create_plan(self, query: str, memory: Any, context: Optional[Dict[str, Any]] = None) -> Plan:
                if "直接" in query:
                    return Plan("直接回答", final_answer="直接答案")
                return Plan("需要工具", [Action("mock_tool", {"query": query})])
            
            def validate_plan(self, plan: Plan) -> bool:
                return True
        
        class MockExecutor(BaseToolExecutor):
            def execute_plan(self, plan: Plan, context: Optional[ExecutionContext] = None) -> List[Observation]:
                observations = []
                for action in plan.actions:
                    obs = self.execute_action(action)
                    observations.append(obs)
                return observations
            
            def execute_action(self, action: Action) -> Observation:
                return Observation(action, f"模拟输出: {action.tool_input}", True, 0.1)
        
        class MockMemory(BaseMemory):
            def __init__(self):
                super().__init__("MockMemory", "模拟内存")
                self._data = {}
            
            def store(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
                self._data[key] = value
                return True
            
            def retrieve(self, key: str) -> Optional[Any]:
                return self._data.get(key)
            
            def delete(self, key: str) -> bool:
                if key in self._data:
                    del self._data[key]
                    return True
                return False
            
            def exists(self, key: str) -> bool:
                return key in self._data
        
        class MockAgent(BaseAgent):
            def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
                start_time = time.time()
                try:
                    plan = self.planner.create_plan(query, self.memory, context)
                    
                    if plan.is_direct_answer:
                        result = plan.final_answer
                        self.update_stats(True, time.time() - start_time, 0)
                        return result
                    
                    observations = self.tool_executor.execute_plan(plan)
                    result = observations[0].output if observations else "无结果"
                    self.update_stats(True, time.time() - start_time, len(plan.actions))
                    return result
                except Exception as e:
                    self.update_stats(False, time.time() - start_time, 0)
                    return f"错误: {str(e)}"
        
        self.planner = MockPlanner("MockPlanner", "模拟规划器")
        self.executor = MockExecutor("MockExecutor", "模拟执行器")
        self.memory = MockMemory()
        self.agent = MockAgent(self.planner, self.executor, self.memory, "MockAgent")
    
    def test_planner_interface(self):
        """测试规划器接口"""
        # 测试直接回答
        plan = self.planner.create_plan("直接回答测试", None)
        self.assertTrue(plan.is_direct_answer)
        self.assertEqual(plan.final_answer, "直接答案")
        
        # 测试工具使用
        plan = self.planner.create_plan("需要工具处理", None)
        self.assertFalse(plan.is_direct_answer)
        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.actions[0].tool_name, "mock_tool")
        
        # 测试验证
        self.assertTrue(self.planner.validate_plan(plan))
    
    def test_executor_interface(self):
        """测试执行器接口"""
        action = Action("mock_tool", {"test": "data"})
        plan = Plan("测试执行", [action])
        
        # 测试单个行动执行
        observation = self.executor.execute_action(action)
        self.assertTrue(observation.success)
        self.assertIn("模拟输出", observation.output)
        
        # 测试计划执行
        observations = self.executor.execute_plan(plan)
        self.assertEqual(len(observations), 1)
        self.assertTrue(observations[0].success)
    
    def test_memory_interface(self):
        """测试内存接口"""
        # 测试存储和检索
        self.assertTrue(self.memory.store("test_key", "test_value"))
        self.assertEqual(self.memory.retrieve("test_key"), "test_value")
        self.assertTrue(self.memory.exists("test_key"))
        
        # 测试不存在的键
        self.assertIsNone(self.memory.retrieve("non_existent"))
        self.assertFalse(self.memory.exists("non_existent"))
        
        # 测试删除
        self.assertTrue(self.memory.delete("test_key"))
        self.assertFalse(self.memory.exists("test_key"))
        self.assertFalse(self.memory.delete("non_existent"))
    
    def test_agent_integration(self):
        """测试Agent集成"""
        # 测试直接回答
        result = self.agent.run("直接回答测试")
        self.assertEqual(result, "直接答案")
        
        # 测试工具使用
        result = self.agent.run("需要工具处理")
        self.assertIn("模拟输出", result)
        
        # 测试统计
        self.assertEqual(self.agent.stats["total_tasks"], 2)


class TestErrorHandling(unittest.TestCase):
    """测试错误处理机制"""
    
    def test_action_error_handling(self):
        """测试Action错误处理"""
        action = Action("", {})  # 空工具名
        self.assertEqual(action.tool_name, "")
        
        # 测试失败状态
        action.start_execution()
        action.fail_execution()
        self.assertEqual(action.status, ActionStatus.FAILED)
    
    def test_observation_error_handling(self):
        """测试Observation错误处理"""
        action = Action("error_tool", {})
        observation = Observation(action, "", False, "严重错误", 0)
        
        self.assertFalse(observation.success)
        self.assertEqual(observation.error_message, "严重错误")
        self.assertFalse(observation.is_successful())
    
    def test_plan_validation(self):
        """测试Plan验证"""
        # 空计划
        empty_plan = Plan("空思考")
        self.assertEqual(len(empty_plan.actions), 0)
        self.assertFalse(empty_plan.is_direct_answer)
        
        # 无效状态转换
        plan = Plan("测试")
        plan.complete_execution()  # 直接完成，跳过执行状态
        self.assertEqual(plan.status, PlanStatus.COMPLETED)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
