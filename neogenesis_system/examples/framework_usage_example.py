#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeogenesisPlanner 框架使用示例 - Framework Usage Examples
演示如何使用重构后的智能规划器来构建高级Agent系统

这个示例展示了：
1. 如何正确初始化 NeogenesisPlanner 及其依赖组件
2. 如何调用 planner.create_plan() 进行智能规划
3. 如何解析和处理返回的 Plan 对象和 Action 列表
4. 如何在新架构中处理执行反馈和学习
5. NeogenesisPlanner 的最佳实践和常见使用模式
"""

import time
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

# 导入框架核心组件
try:
    from neogenesis_system import (
        # 数据结构
        Action, Plan, Observation, ExecutionContext,
        
        # 抽象接口
        BasePlanner, BaseToolExecutor, BaseMemory, BaseAgent
    )
    
    # 导入 NeogenesisPlanner 及其依赖
    from neogenesis_system.planners.neogenesis_planner import NeogenesisPlanner
    from neogenesis_system.meta_mab.reasoner import PriorReasoner
    from neogenesis_system.meta_mab.path_generator import PathGenerator
    from neogenesis_system.meta_mab.mab_converger import MABConverger
    from neogenesis_system.meta_mab.utils.tool_abstraction import (
        global_tool_registry, execute_tool, ToolResult
    )
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    exit(1)


# =============================================================================
# 第1步：演示如何初始化 NeogenesisPlanner
# =============================================================================

class NeogenesisPlannerFactory:
    """NeogenesisPlanner 工厂类 - 展示最佳初始化实践"""
    
    @staticmethod
    def create_basic_planner(api_key: str = "", config: Optional[Dict] = None) -> NeogenesisPlanner:
        """
        创建基础的 NeogenesisPlanner
        
        这是最简单的初始化方式，适合大多数使用场景
        """
        print("🏭 创建基础 NeogenesisPlanner...")
        
        # 设置环境变量（如果提供了API密钥）
        if api_key:
            os.environ.setdefault("DEEPSEEK_API_KEY", api_key)
        
        # 创建依赖组件
        prior_reasoner = PriorReasoner(api_key)
        
        # 创建LLM客户端（如果可能）
        llm_client = None
        if api_key:
            try:
                from neogenesis_system.meta_mab.utils.client_adapter import DeepSeekClientAdapter
                llm_client = DeepSeekClientAdapter(api_key)
                print("✅ LLM客户端创建成功")
            except Exception as e:
                print(f"⚠️ LLM客户端创建失败，使用离线模式: {e}")
        
        path_generator = PathGenerator(api_key, llm_client=llm_client)
        mab_converger = MABConverger()
        
        # 创建 NeogenesisPlanner（依赖注入）
        planner = NeogenesisPlanner(
            prior_reasoner=prior_reasoner,
            path_generator=path_generator,
            mab_converger=mab_converger,
            tool_registry=global_tool_registry,
            config=config or {}
        )
        
        print("✅ NeogenesisPlanner 创建完成")
        return planner
    
    @staticmethod
    def create_advanced_planner(api_key: str = "", custom_config: Optional[Dict] = None) -> NeogenesisPlanner:
        """
        创建高级配置的 NeogenesisPlanner
        
        展示如何进行高级配置和自定义
        """
        print("🔧 创建高级配置 NeogenesisPlanner...")
        
        # 高级配置示例
        advanced_config = {
            "max_reasoning_paths": 8,  # 增加推理路径数量
            "verification_enabled": True,  # 启用验证
            "learning_rate": 0.1,  # 学习率
            "exploration_factor": 0.3,  # 探索因子
            **(custom_config or {})
        }
        
        return NeogenesisPlannerFactory.create_basic_planner(api_key, advanced_config)


# =============================================================================
# 第2步：演示如何调用 planner.create_plan()
# =============================================================================

class PlanningDemonstrator:
    """规划演示器 - 展示如何正确使用 NeogenesisPlanner"""
    
    def __init__(self, planner: NeogenesisPlanner):
        self.planner = planner
        self.planning_history = []
    
    def demonstrate_basic_planning(self, query: str, context: Optional[Dict] = None) -> Plan:
        """
        演示基础规划调用
        
        这是最基本的使用方式
        """
        print(f"\n📋 基础规划演示")
        print(f"查询: {query}")
        print("-" * 50)
        
        start_time = time.time()
        
        # 调用 NeogenesisPlanner 进行规划
        plan = self.planner.create_plan(
            query=query,
            memory=None,  # 在实际应用中，这里会传入Agent的记忆对象
            context=context or {}
        )
        
        execution_time = time.time() - start_time
        
        # 记录规划历史
        self.planning_history.append({
            "query": query,
            "plan": plan,
            "execution_time": execution_time,
            "timestamp": datetime.now()
        })
        
        print(f"⏱️ 规划耗时: {execution_time:.3f}秒")
        return plan
    
    def demonstrate_advanced_planning(self, query: str, user_context: Dict) -> Plan:
        """
        演示高级规划调用
        
        展示如何传入复杂的上下文信息
        """
        print(f"\n🔧 高级规划演示")
        print(f"查询: {query}")
        print(f"上下文: {json.dumps(user_context, ensure_ascii=False, indent=2)}")
        print("-" * 50)
        
        # 构建丰富的执行上下文
        rich_context = {
            "user_preferences": user_context.get("preferences", {}),
            "domain": user_context.get("domain", "general"),
            "urgency": user_context.get("urgency", "normal"),
            "confidence_requirement": user_context.get("confidence", 0.7),
            "resource_constraints": user_context.get("constraints", {}),
            "timestamp": time.time()
        }
        
        plan = self.planner.create_plan(
            query=query,
            memory=None,
            context=rich_context
        )
        
        return plan
    
    def get_planning_statistics(self) -> Dict[str, Any]:
        """获取规划统计信息"""
        if not self.planning_history:
            return {"message": "还没有规划历史"}
        
        total_plans = len(self.planning_history)
        avg_time = sum(p["execution_time"] for p in self.planning_history) / total_plans
        
        # 分析Plan类型分布
        direct_answers = sum(1 for p in self.planning_history if p["plan"].is_direct_answer)
        action_plans = total_plans - direct_answers
        
        return {
            "total_plans": total_plans,
            "average_execution_time": avg_time,
            "direct_answers": direct_answers,
            "action_plans": action_plans,
            "planner_stats": self.planner.get_stats()
        }


# =============================================================================
# 第3步：演示如何解析返回的 Plan 对象和 Action
# =============================================================================

class PlanAnalyzer:
    """Plan分析器 - 展示如何正确解析和处理Plan对象"""
    
    @staticmethod
    def analyze_plan_structure(plan: Plan) -> Dict[str, Any]:
        """
        分析Plan的结构和内容
        
        展示Plan对象的所有重要属性
        """
        print(f"\n🔍 Plan结构分析")
        print("=" * 50)
        
        analysis = {
            "plan_type": "direct_answer" if plan.is_direct_answer else "action_based",
            "thought_process": plan.thought,
            "action_count": len(plan.actions),
            "has_final_answer": plan.final_answer is not None,
            "metadata_keys": list(plan.metadata.keys()) if plan.metadata else [],
            "plan_status": plan.status.value if hasattr(plan, 'status') else "unknown"
        }
        
        print(f"📊 Plan类型: {analysis['plan_type']}")
        print(f"💭 思考过程: {plan.thought}")
        
        if plan.is_direct_answer:
            print(f"💬 直接回答: {plan.final_answer}")
        else:
            print(f"🔧 计划行动数量: {analysis['action_count']}")
        
        if plan.metadata:
            print(f"📋 元数据: {list(plan.metadata.keys())}")
        
        return analysis
    
    @staticmethod
    def analyze_actions(plan: Plan) -> List[Dict[str, Any]]:
        """
        详细分析Plan中的每个Action
        
        展示如何正确处理Action列表
        """
        if plan.is_direct_answer:
            print("ℹ️ 这是直接回答类型的Plan，没有Action需要执行")
            return []
        
        print(f"\n🔧 Action详细分析")
        print("=" * 50)
        
        action_analyses = []
        
        for i, action in enumerate(plan.actions, 1):
            analysis = {
                "index": i,
                "tool_name": action.tool_name,
                "tool_input": action.tool_input,
                "input_keys": list(action.tool_input.keys()) if isinstance(action.tool_input, dict) else [],
                "is_executable": PlanAnalyzer._check_action_executability(action)
            }
            
            print(f"  Action {i}:")
            print(f"    🛠️  工具: {action.tool_name}")
            print(f"    📥 输入: {action.tool_input}")
            print(f"    ✅ 可执行: {analysis['is_executable']}")
            
            action_analyses.append(analysis)
        
        return action_analyses
    
    @staticmethod
    def _check_action_executability(action: Action) -> bool:
        """检查Action是否可执行"""
        # 基本检查
        if not action.tool_name or not action.tool_input:
            return False
        
        # 检查工具是否在注册表中
        try:
            return global_tool_registry.has_tool(action.tool_name)
        except Exception:
            return False
    
    @staticmethod
    def extract_neogenesis_metadata(plan: Plan) -> Dict[str, Any]:
        """
        提取NeogenesisPlanner特有的元数据
        
        展示如何访问五阶段决策的详细信息
        """
        print(f"\n🧠 NeogenesisPlanner元数据分析")
        print("=" * 50)
        
        neogenesis_data = plan.metadata.get('neogenesis_decision', {})
        
        if not neogenesis_data:
            print("ℹ️ 没有找到NeogenesisPlanner的决策元数据")
            return {}
        
        chosen_path = neogenesis_data.get('chosen_path')
        chosen_path_type = 'unknown'
        if chosen_path:
            chosen_path_type = getattr(chosen_path, 'path_type', 'unknown')
        
        metadata_summary = {
            "thinking_seed": neogenesis_data.get('thinking_seed', ''),
            "chosen_path_type": chosen_path_type,
            "total_paths_considered": len(neogenesis_data.get('available_paths', [])),
            "verification_enabled": neogenesis_data.get('verification_enabled', False),
            "decision_algorithm": neogenesis_data.get('selection_algorithm', 'unknown'),
            "performance_metrics": neogenesis_data.get('performance_metrics', {})
        }
        
        print(f"🌱 思维种子: {metadata_summary['thinking_seed'][:100]}...")
        print(f"🎯 选择的路径类型: {metadata_summary['chosen_path_type']}")
        print(f"🛤️ 考虑的路径总数: {metadata_summary['total_paths_considered']}")
        print(f"🔬 验证功能: {'启用' if metadata_summary['verification_enabled'] else '禁用'}")
        print(f"🤖 决策算法: {metadata_summary['decision_algorithm']}")
        
        return metadata_summary


# =============================================================================
# 第4步：重新设计执行反馈和学习机制
# =============================================================================

class SmartToolExecutor(BaseToolExecutor):
    """
    智能工具执行器
    
    展示在新架构中如何处理执行反馈和学习
    注意：update_performance_feedback 的功能现在分布在执行和学习过程中
    """
    
    def __init__(self, planner: NeogenesisPlanner):
        super().__init__(
            name="SmartToolExecutor",
            description="集成NeogenesisPlanner反馈学习的智能执行器"
        )
        self.planner = planner
        self.execution_history = []
        
        # 注册一些模拟工具
        self.register_tool("web_search", self._mock_web_search)
        self.register_tool("idea_verification", self._mock_idea_verification)
        self.register_tool("calculator", self._mock_calculator)
    
    def execute_plan(self, plan: Plan, context: Optional[ExecutionContext] = None) -> List[Observation]:
        """
        执行计划 - 实现BaseToolExecutor的抽象方法
        
        Args:
            plan: 要执行的计划
            context: 执行上下文
            
        Returns:
            List[Observation]: 执行结果列表
        """
        return self.execute_plan_with_learning(plan, context)
    
    def execute_plan_with_learning(self, plan: Plan, context: Optional[ExecutionContext] = None) -> List[Observation]:
        """
        执行Plan并提供学习反馈
        
        这是新架构中处理"性能反馈"的推荐方式
        """
        print(f"\n🚀 开始执行Plan（包含学习反馈）")
        print("-" * 40)
        
        observations = []
        execution_start = time.time()
        
        # 执行所有Action
        for i, action in enumerate(plan.actions, 1):
            print(f"执行Action {i}/{len(plan.actions)}: {action.tool_name}")
            
            observation = self.execute_action(action)
            observations.append(observation)
            
            # 实时反馈：向NeogenesisPlanner报告执行结果
            self._provide_execution_feedback(action, observation)
            
            if observation.success:
                print(f"  ✅ 成功: {observation.output[:100]}...")
            else:
                print(f"  ❌ 失败: {observation.error_message}")
        
        # 整体执行反馈
        total_execution_time = time.time() - execution_start
        overall_success = all(obs.success for obs in observations)
        
        self._provide_plan_feedback(plan, observations, overall_success, total_execution_time)
        
        return observations
    
    def _provide_execution_feedback(self, action: Action, observation: Observation):
        """向NeogenesisPlanner提供单个Action的执行反馈"""
        # 在新架构中，反馈是通过MABConverger的学习机制实现的
        # 这里我们可以调用planner内部的学习方法
        
        try:
            # 提取Action对应的路径信息
            # 注意：这需要访问plan的metadata来获取路径映射关系
            
            # 简化版本：基于工具执行结果进行反馈
            if hasattr(self.planner, 'mab_converger'):
                # 假设我们有一种方式将action映射到路径
                tool_performance_score = 1.0 if observation.success else 0.0
                
                # 这里可以调用MAB系统的更新方法
                # 实际实现中需要更复杂的映射逻辑
                pass
                
        except Exception as e:
            print(f"⚠️ 反馈学习失败: {e}")
    
    def _provide_plan_feedback(self, plan: Plan, observations: List[Observation], 
                             success: bool, execution_time: float):
        """向NeogenesisPlanner提供整体Plan的执行反馈"""
        
        feedback_data = {
            "plan_success": success,
            "execution_time": execution_time,
            "action_success_rate": sum(1 for obs in observations if obs.success) / len(observations) if observations else 0,
            "timestamp": time.time()
        }
        
        # 记录执行历史（代替旧的update_performance_feedback）
        self.execution_history.append({
            "plan_metadata": plan.metadata,
            "feedback": feedback_data,
            "observations": observations
        })
        
        print(f"📊 Plan执行反馈:")
        print(f"  ✅ 整体成功: {success}")
        print(f"  ⏱️ 执行时间: {execution_time:.3f}s")
        print(f"  📈 Action成功率: {feedback_data['action_success_rate']:.1%}")
    
    def execute_action(self, action: Action) -> Observation:
        """执行单个Action"""
        start_time = time.time()
        
        try:
            if action.tool_name in self.available_tools:
                tool_func = self.available_tools[action.tool_name]
                result = tool_func(action.tool_input)
                
                return Observation(
                    action=action,
                    output=result,
                    success=True,
                    execution_time=time.time() - start_time
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
    
    # 模拟工具实现
    def _mock_web_search(self, params: Dict) -> str:
        """模拟网页搜索工具"""
        query = params.get("query", "")
        time.sleep(0.1)  # 模拟网络延迟
        return f"搜索结果：关于'{query}'的相关信息已找到，包括最新发展和详细资料。"
    
    def _mock_idea_verification(self, params: Dict) -> str:
        """模拟想法验证工具"""
        idea = params.get("idea_text", "")
        time.sleep(0.05)  # 模拟处理时间
        return f"验证结果：想法'{idea[:50]}...'经过分析具有较高的可行性评分。"
    
    def _mock_calculator(self, params: Dict) -> str:
        """模拟计算器工具"""
        expression = params.get("expression", "")
        try:
            result = eval(expression)  # 注意：实际使用中需要安全的计算方法
            return f"计算结果：{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"


# =============================================================================
# 第5步：完整的使用示例和最佳实践
# =============================================================================

class NeogenesisPlannerBestPractices:
    """NeogenesisPlanner最佳实践演示"""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.planner = None
        self.executor = None
        self.demo_results = []
    
    def setup_complete_system(self):
        """设置完整的NeogenesisPlanner系统"""
        print("🏗️ 设置完整的NeogenesisPlanner系统")
        print("=" * 60)
        
        # 1. 创建NeogenesisPlanner
        self.planner = NeogenesisPlannerFactory.create_advanced_planner(
            api_key=self.api_key,
            custom_config={
                "max_reasoning_paths": 6,
                "verification_enabled": True,
                "learning_enabled": True
            }
        )
        
        # 2. 创建智能执行器
        self.executor = SmartToolExecutor(self.planner)
        
        print("✅ 系统设置完成")
    
    def demonstrate_complete_workflow(self):
        """演示完整的工作流程"""
        print("\n🎯 完整工作流程演示")
        print("=" * 60)
        
        # 测试查询集合
        test_cases = [
            {
                "query": "搜索人工智能在医疗领域的最新应用",
                "context": {"domain": "healthcare", "urgency": "high"},
                "description": "搜索类任务"
            },
            {
                "query": "分析区块链技术的优缺点",
                "context": {"domain": "technology", "confidence": 0.8},
                "description": "分析类任务"
            },
            {
                "query": "验证量子计算在密码学中的应用可行性",
                "context": {"domain": "research", "verification_required": True},
                "description": "验证类任务"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"【演示 {i}/{len(test_cases)}】{test_case['description']}")
            print(f"查询: {test_case['query']}")
            print(f"{'='*80}")
            
            self._run_single_demo(test_case)
            
            time.sleep(1)  # 短暂休息
        
        self._show_final_statistics()
    
    def _run_single_demo(self, test_case: Dict):
        """运行单个演示案例"""
        query = test_case["query"]
        context = test_case["context"]
        
        try:
            # 第1步：创建Plan
            demonstrator = PlanningDemonstrator(self.planner)
            plan = demonstrator.demonstrate_advanced_planning(query, context)
            
            # 第2步：分析Plan
            PlanAnalyzer.analyze_plan_structure(plan)
            action_analyses = PlanAnalyzer.analyze_actions(plan)
            neogenesis_metadata = PlanAnalyzer.extract_neogenesis_metadata(plan)
            
            # 第3步：执行Plan（如果有Action）
            observations = []
            if not plan.is_direct_answer:
                observations = self.executor.execute_plan_with_learning(plan)
            
            # 第4步：记录结果
            demo_result = {
                "test_case": test_case,
                "plan": plan,
                "action_analyses": action_analyses,
                "neogenesis_metadata": neogenesis_metadata,
                "observations": observations,
                "execution_success": all(obs.success for obs in observations) if observations else True,
                "timestamp": datetime.now()
            }
            
            self.demo_results.append(demo_result)
            
            # 显示最终结果
            if plan.is_direct_answer:
                print(f"\n📤 最终结果: {plan.final_answer}")
            else:
                print(f"\n📤 执行结果:")
                for obs in observations:
                    status = "✅" if obs.success else "❌"
                    print(f"  {status} {obs.action.tool_name}: {obs.output[:100]}...")
            
        except Exception as e:
            print(f"❌ 演示过程中出现错误: {e}")
    
    def _show_final_statistics(self):
        """显示最终统计信息"""
        print(f"\n📊 最终统计报告")
        print("=" * 60)
        
        if not self.demo_results:
            print("没有演示数据")
            return
        
        total_demos = len(self.demo_results)
        successful_demos = sum(1 for result in self.demo_results if result["execution_success"])
        
        print(f"总演示数量: {total_demos}")
        print(f"成功演示: {successful_demos}")
        print(f"成功率: {successful_demos/total_demos:.1%}")
        
        # NeogenesisPlanner统计
        if self.planner:
            planner_stats = self.planner.get_stats()
            print(f"\n🧠 NeogenesisPlanner统计:")
            print(f"  总决策轮数: {planner_stats.get('total_rounds', 0)}")
            print(f"  平均决策时间: {planner_stats.get('performance_stats', {}).get('avg_decision_time', 0):.3f}s")
        
        # 执行器统计
        if self.executor and hasattr(self.executor, 'execution_history'):
            print(f"\n🚀 执行器统计:")
            print(f"  总执行历史: {len(self.executor.execution_history)}")


# =============================================================================
# 主演示函数
# =============================================================================

def main():
    """主演示函数 - 展示NeogenesisPlanner的完整使用方法"""
    print("🚀 NeogenesisPlanner 框架使用示例")
    print("🎯 展示智能规划器的完整使用方法和最佳实践")
    print("=" * 80)
    
    # 获取API密钥（可选）
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not api_key:
        print("⚠️ 未检测到DEEPSEEK_API_KEY，将运行模拟模式")
        print("💡 设置环境变量可体验完整的AI功能")
    else:
        print("✅ 检测到API密钥，将使用完整功能")
    
    try:
        # 创建并运行完整演示
        demo = NeogenesisPlannerBestPractices(api_key)
        demo.setup_complete_system()
        demo.demonstrate_complete_workflow()
        
        print(f"\n🎉 演示完成！")
        print("\n📚 关键要点总结:")
        print("  ✅ NeogenesisPlanner使用依赖注入模式初始化")
        print("  ✅ create_plan()方法进行智能规划")
        print("  ✅ Plan对象包含thought、actions或final_answer")
        print("  ✅ 通过metadata访问五阶段决策详情")
        print("  ✅ 执行反馈通过执行器的学习机制实现")
        print("  ✅ 新架构支持更灵活的组件组合")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


def quick_demo():
    """快速演示 - 展示最基本的使用方法"""
    print("⚡ NeogenesisPlanner 快速演示")
    print("-" * 40)
    
    try:
        # 1. 创建NeogenesisPlanner
        planner = NeogenesisPlannerFactory.create_basic_planner()
        
        # 2. 创建计划
        query = "搜索Python编程的最佳实践"
        plan = planner.create_plan(query=query, memory=None, context={})
        
        # 3. 分析结果
        print(f"思考过程: {plan.thought}")
        
        if plan.is_direct_answer:
            print(f"直接回答: {plan.final_answer}")
        else:
            print(f"计划行动: {len(plan.actions)} 个")
            for i, action in enumerate(plan.actions, 1):
                print(f"  {i}. {action.tool_name}: {action.tool_input}")
        
        print("✅ 快速演示完成")
        
    except Exception as e:
        print(f"❌ 快速演示失败: {e}")


if __name__ == "__main__":
    # 根据命令行参数选择演示模式
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_demo()
    else:
        main()