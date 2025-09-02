#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeogenesisPlanner使用演示
展示如何使用重构后的智能规划器来构建完整的Agent系统

这个示例展示了：
1. 如何组装NeogenesisPlanner的依赖组件
2. 如何将NeogenesisPlanner集成到Agent中
3. 五阶段智能决策的完整工作流程
4. 与传统规划器的对比
"""

import time
import os
import sys
from typing import Dict, Any, Optional, List

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

try:
    from neogenesis_system import (
        # 框架核心
        BasePlanner, BaseToolExecutor, BaseMemory, BaseAgent,
        Action, Plan, Observation,
        # 具体实现
        NeogenesisPlanner
    )
    
    # 导入Meta MAB组件
    from neogenesis_system.meta_mab.reasoner import PriorReasoner
    from neogenesis_system.meta_mab.path_generator import PathGenerator
    from neogenesis_system.meta_mab.mab_converger import MABConverger
    from neogenesis_system.meta_mab.llm_manager import LLMManager
    from neogenesis_system.meta_mab.utils.tool_abstraction import global_tool_registry
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)


# =============================================================================
# 模拟组件实现（用于演示）
# =============================================================================

class MockMemory(BaseMemory):
    """模拟记忆模块"""
    
    def __init__(self):
        super().__init__("MockMemory", "演示用记忆模块")
        self._data = {}
    
    def store(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        self._data[key] = {"value": value, "metadata": metadata, "timestamp": time.time()}
        return True
    
    def retrieve(self, key: str) -> Optional[Any]:
        return self._data.get(key, {}).get("value")
    
    def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None
    
    def exists(self, key: str) -> bool:
        return key in self._data


class MockToolExecutor(BaseToolExecutor):
    """模拟工具执行器"""
    
    def __init__(self):
        super().__init__("MockToolExecutor", "演示用工具执行器")
        self._tools = {
            "web_search": self._mock_web_search,
            "idea_verification": self._mock_idea_verification
        }
    
    def execute_plan(self, plan: Plan, context=None) -> List[Observation]:
        observations = []
        for action in plan.actions:
            obs = self.execute_action(action)
            observations.append(obs)
        return observations
    
    def execute_action(self, action: Action) -> Observation:
        start_time = time.time()
        
        try:
            if action.tool_name in self._tools:
                result = self._tools[action.tool_name](action.tool_input)
                execution_time = time.time() - start_time
                
                return Observation(
                    action=action,
                    output=result,
                    success=True,
                    execution_time=execution_time
                )
            else:
                return Observation(
                    action=action,
                    output="",
                    success=False,
                    error_message=f"工具 '{action.tool_name}' 不存在",
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return Observation(
                action=action,
                output="",
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _mock_web_search(self, params: Dict) -> str:
        """模拟网页搜索"""
        query = params.get("query", "")
        time.sleep(0.1)  # 模拟网络延迟
        return f"搜索'{query}'的模拟结果：找到了相关的信息和资料。"
    
    def _mock_idea_verification(self, params: Dict) -> str:
        """模拟想法验证"""
        idea = params.get("idea_text", "")
        time.sleep(0.05)  # 模拟处理时间
        return f"对想法'{idea[:50]}...'的验证结果：该想法具有一定的可行性。"


class NeogenesisAgent(BaseAgent):
    """使用NeogenesisPlanner的智能Agent"""
    
    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """运行Agent处理用户查询"""
        print(f"\n🤖 NeogenesisAgent开始处理: {query}")
        start_time = time.time()
        
        try:
            # 1. 使用NeogenesisPlanner创建计划
            print("🧠 调用NeogenesisPlanner进行五阶段智能规划...")
            plan = self.plan_task(query, context)
            
            # 2. 验证计划
            if not self.planner.validate_plan(plan):
                return "❌ 生成的计划无效，无法执行。"
            
            # 3. 处理计划
            if plan.is_direct_answer:
                result = plan.final_answer
                print(f"✅ 直接回答: {result}")
            else:
                print(f"🔧 执行计划: {len(plan.actions)} 个行动")
                
                # 显示计划详情
                for i, action in enumerate(plan.actions, 1):
                    print(f"   行动{i}: {action.tool_name} - {action.tool_input}")
                
                # 执行计划
                observations = self.execute_plan(plan)
                
                # 处理执行结果
                results = []
                for obs in observations:
                    if obs.success:
                        results.append(obs.output)
                        print(f"✅ {obs.action.tool_name}: {obs.output}")
                    else:
                        print(f"❌ {obs.action.tool_name}: {obs.error_message}")
                
                result = "\n".join(results) if results else "执行过程中遇到问题"
            
            # 4. 存储到记忆
            execution_time = time.time() - start_time
            self.store_memory(f"query_{int(time.time())}", {
                "query": query,
                "result": result,
                "execution_time": execution_time,
                "plan_metadata": plan.metadata
            })
            
            # 5. 更新统计
            self.update_stats(True, execution_time, len(plan.actions) if not plan.is_direct_answer else 0)
            
            print(f"⏱️ 处理完成，耗时: {execution_time:.3f}秒")
            
            # 显示NeogenesisPlanner的统计信息
            if hasattr(self.planner, 'get_stats'):
                planner_stats = self.planner.get_stats()
                print(f"📊 规划器统计: {planner_stats['total_rounds']} 轮决策")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"处理失败: {str(e)}"
            self.update_stats(False, execution_time, 0)
            print(f"❌ {error_msg}")
            return error_msg


# =============================================================================
# 工厂方法模式 - 创建不同类型的Agent
# =============================================================================

class AgentFactory:
    """Agent工厂 - 使用工厂方法模式创建不同类型的Agent"""
    
    @staticmethod
    def create_neogenesis_agent(api_key: str = "", config: Optional[Dict] = None) -> NeogenesisAgent:
        """
        创建使用NeogenesisPlanner的Agent
        
        Args:
            api_key: LLM API密钥
            config: 配置字典
            
        Returns:
            NeogenesisAgent: 配置好的智能Agent
        """
        print("🏭 工厂正在创建NeogenesisAgent...")
        
        try:
            # 设置环境变量
            if api_key:
                os.environ.setdefault("DEEPSEEK_API_KEY", api_key)
            
            # 1. 创建LLM管理器（如果可能的话）
            try:
                llm_manager = LLMManager()
                print("✅ LLM管理器创建成功")
            except Exception as e:
                print(f"⚠️ LLM管理器创建失败，使用模拟模式: {e}")
                llm_manager = None
            
            # 2. 创建Meta MAB组件
            print("🧠 创建Meta MAB组件...")
            
            # 创建先验推理器
            if llm_manager:
                prior_reasoner = PriorReasoner(llm_manager)
            else:
                # 模拟模式
                prior_reasoner = MockPriorReasoner()
            
            # 创建路径生成器
            if llm_manager:
                path_generator = PathGenerator(llm_manager)
            else:
                path_generator = MockPathGenerator()
            
            # 创建MAB收敛器
            mab_converger = MABConverger()
            
            print("✅ Meta MAB组件创建完成")
            
            # 3. 创建NeogenesisPlanner（依赖注入）
            neogenesis_planner = NeogenesisPlanner(
                prior_reasoner=prior_reasoner,
                path_generator=path_generator,
                mab_converger=mab_converger,
                tool_registry=global_tool_registry,
                config=config or {}
            )
            
            # 4. 创建其他组件
            tool_executor = MockToolExecutor()
            memory = MockMemory()
            
            # 5. 组装Agent
            agent = NeogenesisAgent(
                planner=neogenesis_planner,
                tool_executor=tool_executor,
                memory=memory,
                name="NeogenesisAgent"
            )
            
            print("🎉 NeogenesisAgent创建完成！")
            return agent
            
        except Exception as e:
            print(f"❌ Agent创建失败: {e}")
            # 返回一个基本的Agent作为回退
            return AgentFactory.create_fallback_agent()
    
    @staticmethod
    def create_fallback_agent() -> NeogenesisAgent:
        """创建回退Agent（使用模拟组件）"""
        print("🔄 创建回退Agent...")
        
        # 使用完全模拟的组件
        planner = MockNeogenesisPlanner()
        executor = MockToolExecutor()
        memory = MockMemory()
        
        return NeogenesisAgent(planner, executor, memory, "FallbackAgent")


# =============================================================================
# 模拟组件（当真实组件不可用时）
# =============================================================================

class MockPriorReasoner:
    """模拟先验推理器"""
    
    def get_thinking_seed(self, query: str, context=None) -> str:
        return f"对于查询'{query}'的思维种子：需要深入分析用户意图并制定合适策略"
    
    def assess_task_confidence(self, query: str, context=None) -> float:
        return 0.7
    
    def analyze_task_complexity(self, query: str) -> Dict:
        return {"overall_score": 0.5, "domain": "general"}


class MockPathGenerator:
    """模拟路径生成器"""
    
    def generate_paths(self, thinking_seed: str, task: str, max_paths: int = 6) -> List:
        from neogenesis_system.meta_mab.data_structures import ReasoningPath
        
        paths = []
        for i in range(min(3, max_paths)):
            path = ReasoningPath(
                path_id=f"mock_path_{i}",
                path_type=f"模拟策略{i+1}",
                description=f"针对'{task}'的第{i+1}种解决方案",
                prompt_template=f"使用策略{i+1}处理用户查询",
                strategy_id=f"mock_strategy_{i}",
                instance_id=f"mock_instance_{i}_{int(time.time())}"
            )
            paths.append(path)
        
        return paths


class MockNeogenesisPlanner(BasePlanner):
    """模拟NeogenesisPlanner（当真实组件不可用时）"""
    
    def __init__(self):
        super().__init__("MockNeogenesisPlanner", "模拟的Neogenesis规划器")
    
    def create_plan(self, query: str, memory: Any, context=None) -> Plan:
        # 简单的模拟逻辑
        if "搜索" in query or "查找" in query:
            return Plan(
                thought="用户需要搜索信息",
                actions=[Action("web_search", {"query": query})]
            )
        else:
            return Plan(
                thought="直接回答用户查询",
                final_answer=f"这是对'{query}'的模拟回答"
            )
    
    def validate_plan(self, plan: Plan) -> bool:
        return True


# =============================================================================
# 装饰器模式 - 增强功能
# =============================================================================

def performance_monitoring_decorator(planner_class):
    """性能监控装饰器"""
    
    class MonitoredPlanner(planner_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._call_count = 0
            self._total_time = 0.0
        
        def create_plan(self, query: str, memory: Any, context=None) -> Plan:
            self._call_count += 1
            start_time = time.time()
            
            print(f"📊 [监控] 第{self._call_count}次规划调用开始...")
            
            try:
                plan = super().create_plan(query, memory, context)
                execution_time = time.time() - start_time
                self._total_time += execution_time
                
                print(f"📊 [监控] 规划完成: {execution_time:.3f}s (平均: {self._total_time/self._call_count:.3f}s)")
                return plan
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"📊 [监控] 规划失败: {execution_time:.3f}s, 错误: {e}")
                raise
    
    return MonitoredPlanner


# =============================================================================
# 演示函数
# =============================================================================

def demo_neogenesis_planner():
    """演示NeogenesisPlanner的使用"""
    print("🎯 NeogenesisPlanner演示")
    print("=" * 50)
    
    # 测试查询
    test_queries = [
        "搜索人工智能的最新发展趋势",
        "如何学习Python编程？",
        "分析区块链技术的优缺点",
        "什么是量子计算？"
    ]
    
    try:
        # 创建Agent（尝试使用真实组件）
        print("🏭 正在创建NeogenesisAgent...")
        agent = AgentFactory.create_neogenesis_agent()
        
        # 测试每个查询
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"【测试 {i}/{len(test_queries)}】: {query}")
            print(f"{'='*60}")
            
            result = agent.run(query)
            print(f"\n📤 最终结果:")
            print(f"   {result}")
            
            # 显示Agent状态
            if hasattr(agent, 'success_rate'):
                print(f"📈 Agent状态: 成功率 {agent.success_rate:.1%}")
            
            time.sleep(0.5)  # 短暂休息
        
        print(f"\n🎉 演示完成！")
        
        # 显示最终统计
        if hasattr(agent, 'get_status'):
            status = agent.get_status()
            print(f"\n📊 最终统计:")
            print(f"   总任务: {status.get('stats', {}).get('total_tasks', 0)}")
            print(f"   成功率: {status.get('success_rate', 0):.1%}")
            print(f"   平均耗时: {status.get('average_execution_time', 0):.3f}s")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


def demo_decorator_enhancement():
    """演示装饰器增强功能"""
    print("\n🎨 装饰器增强演示")
    print("=" * 30)
    
    # 使用装饰器增强MockNeogenesisPlanner
    @performance_monitoring_decorator
    class EnhancedMockPlanner(MockNeogenesisPlanner):
        pass
    
    planner = EnhancedMockPlanner()
    memory = MockMemory()
    
    # 测试装饰器效果
    for i in range(3):
        query = f"测试查询 {i+1}"
        plan = planner.create_plan(query, memory)
        print(f"   生成计划: {plan.thought}")


def main():
    """主演示函数"""
    print("🚀 NeogenesisPlanner完整演示")
    print("🔧 展示重构后的智能规划器系统")
    print("=" * 60)
    
    # 主要演示
    demo_neogenesis_planner()
    
    # 装饰器演示
    demo_decorator_enhancement()
    
    print("\n✨ 所有演示完成！")
    print("\n📚 重要特性总结:")
    print("   ✅ 五阶段智能决策流程")
    print("   ✅ 依赖注入式组件协作")
    print("   ✅ 标准Plan输出格式")
    print("   ✅ 工厂方法模式")
    print("   ✅ 装饰器功能增强")
    print("   ✅ 完整的错误处理")


if __name__ == "__main__":
    main()
