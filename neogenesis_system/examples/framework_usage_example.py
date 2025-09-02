#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
框架使用示例 - Framework Usage Examples
演示如何使用新定义的数据结构和抽象接口来构建模块化的Agent

这个示例展示了：
1. 如何使用基础数据结构 (Action, Plan, Observation)
2. 如何实现抽象接口 (BasePlanner, BaseToolExecutor, BaseMemory, BaseAgent)
3. 如何组装完整的Agent系统
4. 如何扩展框架以支持新的功能
"""

import time
import json
from typing import Any, Dict, List, Optional

# 导入框架核心组件
from neogenesis_system import (
    # 数据结构
    Action, Plan, Observation, ExecutionContext, AgentState,
    ActionStatus, PlanStatus,
    
    # 抽象接口
    BasePlanner, BaseToolExecutor, BaseMemory, BaseAgent, create_agent
)


# =============================================================================
# 示例工具实现
# =============================================================================

class MockSearchTool:
    """模拟搜索工具"""
    
    def search(self, query: str) -> str:
        """模拟搜索功能"""
        # 模拟搜索延迟
        time.sleep(0.1)
        return f"搜索结果：关于'{query}'的信息已找到。"


class MockCalculatorTool:
    """模拟计算器工具"""
    
    def calculate(self, expression: str) -> str:
        """模拟计算功能"""
        try:
            result = eval(expression)  # 注意：实际应用中不要使用eval
            return f"计算结果：{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"


# =============================================================================
# 实现具体的规划器
# =============================================================================

class SimplePlanner(BasePlanner):
    """简单规划器实现示例"""
    
    def __init__(self):
        super().__init__(
            name="SimplePlanner",
            description="基于关键词匹配的简单规划器"
        )
    
    def create_plan(self, query: str, memory: Any, context: Optional[Dict[str, Any]] = None) -> Plan:
        """
        创建执行计划
        
        这个简单的实现基于关键词匹配来决定使用哪些工具
        """
        actions = []
        thought = f"分析查询：'{query}'"
        
        # 基于关键词决定行动
        if "搜索" in query or "查找" in query or "信息" in query:
            search_query = query.replace("搜索", "").replace("查找", "").strip()
            action = Action(
                tool_name="search",
                tool_input={"query": search_query}
            )
            actions.append(action)
            thought += f" -> 需要搜索：{search_query}"
        
        if "计算" in query or "=" in query or any(op in query for op in ["+", "-", "*", "/"]):
            # 提取计算表达式
            expression = query
            for word in ["计算", "等于多少", "结果是"]:
                expression = expression.replace(word, "").strip()
            
            action = Action(
                tool_name="calculator", 
                tool_input={"expression": expression}
            )
            actions.append(action)
            thought += f" -> 需要计算：{expression}"
        
        # 如果没有识别到需要工具的任务，直接回答
        if not actions:
            return Plan(
                thought=thought + " -> 直接回答",
                final_answer=f"我理解您的查询：{query}，但我需要更多信息来帮助您。"
            )
        
        return Plan(
            thought=thought,
            actions=actions
        )
    
    def validate_plan(self, plan: Plan) -> bool:
        """验证计划的有效性"""
        if plan.is_direct_answer:
            return plan.final_answer is not None
        
        # 检查所有行动是否有效
        for action in plan.actions:
            if not action.tool_name or not action.tool_input:
                return False
        
        return True


# =============================================================================
# 实现具体的工具执行器
# =============================================================================

class SimpleToolExecutor(BaseToolExecutor):
    """简单工具执行器实现示例"""
    
    def __init__(self):
        super().__init__(
            name="SimpleToolExecutor",
            description="基本的工具执行器，支持搜索和计算"
        )
        
        # 注册可用工具
        self.register_tool("search", MockSearchTool())
        self.register_tool("calculator", MockCalculatorTool())
    
    def execute_plan(self, plan: Plan, context: Optional[ExecutionContext] = None) -> List[Observation]:
        """执行计划中的所有行动"""
        observations = []
        
        plan.start_execution()
        
        for action in plan.actions:
            observation = self.execute_action(action)
            observations.append(observation)
            
            # 如果某个行动失败，记录但继续执行
            if not observation.success:
                print(f"⚠️ 行动失败: {action.tool_name} - {observation.error_message}")
        
        # 根据执行结果更新计划状态
        if all(obs.success for obs in observations):
            plan.complete_execution()
        else:
            plan.fail_execution()
        
        return observations
    
    def execute_action(self, action: Action) -> Observation:
        """执行单个行动"""
        action.start_execution()
        start_time = time.time()
        
        try:
            # 检查工具是否存在
            if action.tool_name not in self.available_tools:
                raise ValueError(f"工具 '{action.tool_name}' 不存在")
            
            tool = self.available_tools[action.tool_name]
            
            # 根据工具类型调用相应方法
            if action.tool_name == "search":
                output = tool.search(action.tool_input["query"])
            elif action.tool_name == "calculator":
                output = tool.calculate(action.tool_input["expression"])
            else:
                raise ValueError(f"不支持的工具：{action.tool_name}")
            
            action.complete_execution()
            execution_time = time.time() - start_time
            
            return Observation(
                action=action,
                output=output,
                success=True,
                execution_time=execution_time
            )
            
        except Exception as e:
            action.fail_execution()
            execution_time = time.time() - start_time
            
            return Observation(
                action=action,
                output="",
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )


# =============================================================================
# 实现具体的记忆模块
# =============================================================================

class SimpleMemory(BaseMemory):
    """简单内存记忆模块实现示例"""
    
    def __init__(self):
        super().__init__(
            name="SimpleMemory",
            description="基于字典的简单内存存储"
        )
        self._storage = {}
        self._metadata = {}
    
    def store(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """存储信息到内存"""
        try:
            self._storage[key] = value
            self._metadata[key] = {
                "stored_at": time.time(),
                "type": type(value).__name__,
                **(metadata or {})
            }
            return True
        except Exception:
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """从内存检索信息"""
        return self._storage.get(key)
    
    def delete(self, key: str) -> bool:
        """从内存删除信息"""
        if key in self._storage:
            del self._storage[key]
            if key in self._metadata:
                del self._metadata[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._storage
    
    def search(self, pattern: str, limit: Optional[int] = None) -> List[str]:
        """搜索匹配的键"""
        matches = [key for key in self._storage.keys() if pattern in key]
        if limit:
            matches = matches[:limit]
        return matches
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "total_items": len(self._storage),
            "keys": list(self._storage.keys()),
            "memory_usage": sum(len(str(v)) for v in self._storage.values())
        }


# =============================================================================
# 实现具体的Agent
# =============================================================================

class SimpleAgent(BaseAgent):
    """简单Agent实现示例"""
    
    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        运行Agent处理用户查询
        
        实现标准的Agent工作流程：
        1. 规划任务
        2. 执行计划
        3. 存储结果
        4. 返回答案
        """
        print(f"🤖 Agent开始处理查询: {query}")
        start_time = time.time()
        
        try:
            # 第1步：创建执行计划
            print("📋 创建执行计划...")
            plan = self.plan_task(query, context)
            
            # 验证计划
            if not self.planner.validate_plan(plan):
                return "抱歉，无法为您的查询创建有效的执行计划。"
            
            print(f"💭 思考过程: {plan.thought}")
            
            # 如果是直接回答，无需执行工具
            if plan.is_direct_answer:
                print("✅ 直接回答，无需调用工具")
                result = plan.final_answer
            else:
                # 第2步：执行计划
                print(f"🔧 执行计划 (包含 {len(plan.actions)} 个行动)...")
                observations = self.execute_plan(plan)
                
                # 第3步：组合结果
                result_parts = []
                for obs in observations:
                    if obs.success:
                        result_parts.append(obs.output)
                        print(f"✅ {obs.tool_name}: {obs.output}")
                    else:
                        result_parts.append(f"错误: {obs.error_message}")
                        print(f"❌ {obs.tool_name}: {obs.error_message}")
                
                result = "\n".join(result_parts)
            
            # 第4步：存储到记忆
            execution_time = time.time() - start_time
            self.store_memory(
                key=f"query_{int(time.time())}",
                value={
                    "query": query,
                    "result": result,
                    "execution_time": execution_time,
                    "plan_size": len(plan.actions)
                },
                metadata={"timestamp": time.time(), "success": True}
            )
            
            # 更新性能统计
            self.update_stats(True, execution_time, len(plan.actions))
            
            print(f"✨ 查询处理完成 (耗时: {execution_time:.2f}秒)")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"处理查询时发生错误: {str(e)}"
            
            # 存储错误信息
            self.store_memory(
                key=f"error_{int(time.time())}",
                value={"query": query, "error": error_msg},
                metadata={"timestamp": time.time(), "success": False}
            )
            
            # 更新性能统计
            self.update_stats(False, execution_time, 0)
            
            print(f"❌ 查询处理失败: {error_msg}")
            return error_msg


# =============================================================================
# 使用示例
# =============================================================================

def main():
    """主函数 - 演示框架使用"""
    print("🚀 Neogenesis框架使用示例")
    print("=" * 50)
    
    # 方法1：手动创建Agent
    print("\n📦 方法1：手动创建Agent组件")
    planner = SimplePlanner()
    executor = SimpleToolExecutor()
    memory = SimpleMemory()
    agent = SimpleAgent(planner, executor, memory, "示例Agent", "演示用的简单Agent")
    
    # 方法2：使用工厂函数创建Agent
    print("\n🏭 方法2：使用工厂函数创建Agent")
    # agent2 = create_agent(
    #     SimplePlanner, SimpleToolExecutor, SimpleMemory,
    #     agent_name="工厂Agent"
    # )
    
    # 测试不同类型的查询
    test_queries = [
        "搜索人工智能的最新发展",
        "计算 25 * 4 + 10",
        "你好，今天天气怎么样？",
        "搜索Python编程教程，然后计算 100 / 5"
    ]
    
    print(f"\n🧪 测试 {len(test_queries)} 个查询:")
    print("-" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n【测试 {i}】")
        result = agent.run(query)
        print(f"📤 结果: {result}")
        print(f"📊 Agent状态: 成功率 {agent.success_rate:.1%}, 平均耗时 {agent.average_execution_time:.2f}s")
    
    # 显示Agent状态和记忆统计
    print(f"\n📈 最终Agent状态:")
    status = agent.get_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    print(f"\n🧠 记忆统计:")
    memory_stats = agent.memory.get_stats()
    print(json.dumps(memory_stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
