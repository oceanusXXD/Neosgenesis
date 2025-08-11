#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - LangChain Integration Examples
展示如何使用Neogenesis-LangChain集成的各种示例
"""

import json
import logging
from typing import Any, Dict, List

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入Neogenesis-LangChain集成组件
from .adapters import (
    NeogenesisAdapter,
    create_neogenesis_agent,
    create_hybrid_agent,
    quick_decision,
    NeogenesisDemo
)
from .tools import get_all_neogenesis_tools
from .chains import create_neogenesis_decision_chain
from .state_management import NeogenesisStateManager

# =============================================================================
# 示例1：基础工具使用
# =============================================================================

def example_basic_tools_usage():
    """示例：基础工具使用"""
    print("\n" + "="*60)
    print("🛠️ 示例1：Neogenesis工具基础使用")
    print("="*60)
    
    try:
        # 获取所有工具
        tools = get_all_neogenesis_tools(api_key="demo_key")
        print(f"✅ 成功加载 {len(tools)} 个Neogenesis工具")
        
        # 展示每个工具
        for tool in tools:
            print(f"\n🔧 {tool.name}:")
            print(f"   描述: {tool.description[:100]}...")
        
        # 使用思维种子工具
        thinking_seed_tool = tools[0]  # 第一个是ThinkingSeedTool
        user_query = "如何设计一个高性能的Web应用架构？"
        
        print(f"\n💭 使用思维种子工具处理查询: {user_query}")
        result = thinking_seed_tool.run(user_query=user_query)
        
        # 解析结果
        result_data = json.loads(result)
        thinking_seed = result_data.get("thinking_seed", "")
        confidence = result_data.get("confidence_score", 0)
        
        print(f"✅ 思维种子生成完成:")
        print(f"   置信度: {confidence:.3f}")
        print(f"   种子预览: {thinking_seed[:150]}...")
        
        return {"success": True, "tools_count": len(tools), "sample_result": result_data}
        
    except Exception as e:
        print(f"❌ 示例1执行失败: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# 示例2：决策链使用
# =============================================================================

def example_decision_chain_usage():
    """示例：决策链使用"""
    print("\n" + "="*60)
    print("🔗 示例2：Neogenesis决策链使用")
    print("="*60)
    
    try:
        # 创建基础决策链
        chain = create_neogenesis_decision_chain(
            api_key="demo_key",
            chain_type="basic"
        )
        print("✅ 基础决策链创建成功")
        
        # 准备输入
        user_query = "开发一个AI驱动的客户服务系统"
        chain_input = {
            "user_query": user_query,
            "execution_context": {"domain": "AI_application", "priority": "high"},
            "use_rag_enhancement": False,  # 简化演示
            "max_paths": 3
        }
        
        print(f"\n🚀 执行决策链处理: {user_query}")
        print(f"   配置: RAG增强={chain_input['use_rag_enhancement']}, 最大路径数={chain_input['max_paths']}")
        
        # 执行链
        result = chain(chain_input)
        decision_result = result.get("decision_result", {})
        
        if decision_result.get("decision_success", False):
            print("✅ 决策链执行成功")
            print(f"   思维种子: {decision_result.get('thinking_seed', '')[:100]}...")
            print(f"   生成路径数: {len(decision_result.get('reasoning_paths', []))}")
            
            selected_path = decision_result.get("selected_path", {})
            if selected_path:
                print(f"   选择路径: {selected_path.get('path_type', 'unknown')}")
                print(f"   路径描述: {selected_path.get('description', '')[:100]}...")
        else:
            print(f"❌ 决策链执行失败: {decision_result.get('error', 'unknown error')}")
        
        return {"success": True, "chain_result": decision_result}
        
    except Exception as e:
        print(f"❌ 示例2执行失败: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# 示例3：完整的五阶段决策过程
# =============================================================================

def example_five_stage_process():
    """示例：完整的五阶段决策过程"""
    print("\n" + "="*60)
    print("🏆 示例3：五阶段Neogenesis决策过程")
    print("="*60)
    
    try:
        # 创建五阶段决策链
        five_stage_chain = create_neogenesis_decision_chain(
            api_key="demo_key",
            chain_type="five_stage"
        )
        print("✅ 五阶段决策链创建成功")
        
        # 准备复杂的决策场景
        user_query = "为初创公司设计一套完整的技术架构，包括后端、前端、数据库和部署策略"
        
        chain_input = {
            "user_query": user_query,
            "execution_context": {
                "company_size": "startup",
                "budget": "limited", 
                "timeline": "3_months",
                "technical_complexity": "high"
            },
            "deepseek_confidence": 0.7,
            "use_rag_enhancement": False,  # 简化演示
            "max_paths": 4,
            "enable_verification": True
        }
        
        print(f"\n🚀 执行五阶段决策处理:")
        print(f"   查询: {user_query}")
        print(f"   上下文: {chain_input['execution_context']}")
        print(f"   置信度: {chain_input['deepseek_confidence']}")
        
        # 执行五阶段链
        result = five_stage_chain(chain_input)
        five_stage_result = result.get("five_stage_result", {})
        
        if five_stage_result.get("five_stage_success", False):
            print("\n✅ 五阶段决策过程执行成功")
            
            # 展示各阶段结果
            stage_results = five_stage_result.get("stage_results", {})
            
            print(f"\n📊 阶段执行摘要:")
            for stage_name, stage_data in stage_results.items():
                stage_type = stage_data.get("type", "unknown")
                print(f"   {stage_name}: {stage_type}")
            
            # 展示最终决策
            final_decision = five_stage_result.get("final_decision", {})
            if final_decision:
                print(f"\n🎯 最终决策:")
                print(f"   选择路径: {final_decision.get('path_type', 'unknown')}")
                print(f"   决策描述: {final_decision.get('description', '')[:150]}...")
            
            # 展示元数据
            metadata = five_stage_result.get("chain_metadata", {})
            print(f"\n📈 执行统计:")
            print(f"   总阶段数: {metadata.get('total_stages', 0)}")
            print(f"   生成路径数: {metadata.get('total_paths_generated', 0)}")
            print(f"   验证路径数: {metadata.get('total_paths_verified', 0)}")
            
        else:
            print(f"❌ 五阶段决策失败: {five_stage_result.get('error', 'unknown error')}")
            
            # 显示部分结果
            partial_results = five_stage_result.get("partial_results", {})
            if partial_results:
                print(f"   完成阶段: {list(partial_results.keys())}")
        
        return {"success": True, "five_stage_result": five_stage_result}
        
    except Exception as e:
        print(f"❌ 示例3执行失败: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# 示例4：适配器使用
# =============================================================================

def example_adapter_usage():
    """示例：适配器使用"""
    print("\n" + "="*60)
    print("🔗 示例4：Neogenesis适配器使用")
    print("="*60)
    
    try:
        # 创建适配器
        adapter = NeogenesisAdapter(
            api_key="demo_key",
            search_engine="duckduckgo",
            enable_state_management=True
        )
        print("✅ Neogenesis适配器创建成功")
        
        # 显示系统状态
        status = adapter.get_system_status()
        print(f"\n📊 系统状态:")
        for key, value in status.items():
            if key != "session_statistics":
                print(f"   {key}: {value}")
        
        # 使用工具模式运行决策
        user_query = "构建一个可扩展的微服务架构"
        
        print(f"\n🛠️ 使用工具模式执行决策: {user_query}")
        
        tools_result = adapter.run_decision_process(
            user_query=user_query,
            process_type="tools",
            execution_context={"architecture_type": "microservices"},
            max_paths=3
        )
        
        if tools_result.get("success", False):
            print("✅ 工具模式决策成功")
            
            tools_results = tools_result.get("tools_results", {})
            print(f"   执行工具: {list(tools_results.keys())}")
            
            # 显示思维种子结果
            if "thinking_seed" in tools_results:
                seed_data = tools_results["thinking_seed"]
                print(f"   思维种子置信度: {seed_data.get('confidence_score', 0):.3f}")
            
            # 显示路径生成结果
            if "path_generation" in tools_results:
                path_data = tools_results["path_generation"]
                paths = path_data.get("reasoning_paths", [])
                print(f"   生成思维路径: {len(paths)}条")
                for i, path in enumerate(paths[:2]):  # 显示前2个
                    print(f"     路径{i+1}: {path.get('path_type', 'unknown')}")
            
            # 显示MAB决策结果
            if "mab_decision" in tools_results:
                mab_data = tools_results["mab_decision"]
                selected = mab_data.get("selected_path", {})
                print(f"   MAB选择: {selected.get('path_type', 'unknown')}")
        else:
            print(f"❌ 工具模式决策失败: {tools_result.get('error', 'unknown')}")
        
        return {"success": True, "adapter_result": tools_result, "system_status": status}
        
    except Exception as e:
        print(f"❌ 示例4执行失败: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# 示例5：状态管理
# =============================================================================

def example_state_management():
    """示例：状态管理"""
    print("\n" + "="*60)
    print("🗃️ 示例5：Neogenesis状态管理")
    print("="*60)
    
    try:
        # 创建状态管理器
        state_manager = NeogenesisStateManager(
            storage_path="./demo_state",
            max_sessions=10
        )
        print("✅ 状态管理器创建成功")
        
        # 创建测试会话
        session_id = "demo_session_001"
        user_query = "开发智能推荐系统"
        
        session = state_manager.create_session(
            session_id=session_id,
            user_query=user_query,
            execution_context={"domain": "recommendation_system"}
        )
        print(f"✅ 创建会话: {session_id}")
        
        # 模拟阶段更新
        from .state_management import DecisionStage
        
        # 阶段1：思维种子生成
        state_manager.update_session_stage(
            session_id=session_id,
            stage=DecisionStage.THINKING_SEED,
            success=True,
            data={"thinking_seed": "智能推荐系统需要考虑用户行为、物品特征和算法选择..."},
            execution_time=1.2
        )
        print("   ✅ 阶段1：思维种子生成完成")
        
        # 阶段2：路径生成
        state_manager.update_session_stage(
            session_id=session_id,
            stage=DecisionStage.PATH_GENERATION,
            success=True,
            data={
                "reasoning_paths": [
                    {"path_type": "协同过滤型", "path_id": "cf_001"},
                    {"path_type": "内容推荐型", "path_id": "cb_001"},
                    {"path_type": "深度学习型", "path_id": "dl_001"}
                ]
            },
            execution_time=2.5
        )
        print("   ✅ 阶段2：路径生成完成")
        
        # 阶段3：MAB决策
        state_manager.update_session_stage(
            session_id=session_id,
            stage=DecisionStage.MAB_DECISION,
            success=True,
            data={
                "selected_path": {"path_type": "混合推荐型", "path_id": "hybrid_001"},
                "mab_statistics": {"confidence": 0.85}
            },
            execution_time=1.8
        )
        print("   ✅ 阶段3：MAB决策完成")
        
        # 获取会话状态
        updated_session = state_manager.get_session(session_id)
        if updated_session:
            completion_rate = updated_session.get_completion_rate()
            print(f"\n📊 会话状态:")
            print(f"   完成率: {completion_rate:.1%}")
            print(f"   当前阶段: {updated_session.current_stage.value}")
            print(f"   思维种子: {updated_session.thinking_seed[:50]}...")
            print(f"   选择路径: {updated_session.selected_path}")
        
        # 获取统计信息
        stats = state_manager.get_session_statistics()
        print(f"\n📈 管理器统计:")
        print(f"   活跃会话: {stats['active_sessions']}")
        print(f"   平均完成率: {stats['avg_completion_rate']:.1%}")
        print(f"   MAB轮次: {stats['mab_total_rounds']}")
        
        # 完成会话
        state_manager.complete_session(session_id, {"final_result": "推荐系统设计完成"})
        print(f"✅ 会话完成: {session_id}")
        
        return {"success": True, "session_id": session_id, "statistics": stats}
        
    except Exception as e:
        print(f"❌ 示例5执行失败: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# 示例6：快速决策函数
# =============================================================================

def example_quick_decision():
    """示例：快速决策函数"""
    print("\n" + "="*60)
    print("⚡ 示例6：快速决策函数")
    print("="*60)
    
    try:
        # 场景1：使用工具模式
        query1 = "设计一个分布式缓存系统"
        print(f"\n🛠️ 场景1 - 工具模式: {query1}")
        
        result1 = quick_decision(
            user_query=query1,
            api_key="demo_key",
            process_type="tools",
            max_paths=2
        )
        
        if result1.get("success", False):
            print("   ✅ 工具模式决策成功")
            tools_results = result1.get("tools_results", {})
            print(f"   执行结果: {list(tools_results.keys())}")
        else:
            print(f"   ❌ 工具模式决策失败: {result1.get('error', '')}")
        
        # 场景2：使用链模式
        query2 = "构建实时数据处理管道"
        print(f"\n🔗 场景2 - 链模式: {query2}")
        
        result2 = quick_decision(
            user_query=query2,
            api_key="demo_key",
            process_type="chain",
            chain_type="basic",
            max_paths=3
        )
        
        if result2.get("success", False):
            print("   ✅ 链模式决策成功")
            chain_result = result2.get("chain_result", {})
            decision_data = chain_result.get("decision_result", {})
            if decision_data.get("decision_success", False):
                print(f"   思维路径数: {len(decision_data.get('reasoning_paths', []))}")
                selected = decision_data.get("selected_path", {})
                print(f"   选择方案: {selected.get('path_type', 'unknown')}")
        else:
            print(f"   ❌ 链模式决策失败: {result2.get('error', '')}")
        
        return {
            "success": True, 
            "tools_result": result1, 
            "chain_result": result2
        }
        
    except Exception as e:
        print(f"❌ 示例6执行失败: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# 示例7：演示类使用
# =============================================================================

def example_demo_class():
    """示例：演示类使用"""
    print("\n" + "="*60)
    print("🎯 示例7：Neogenesis演示类")
    print("="*60)
    
    try:
        # 创建演示实例
        demo = NeogenesisDemo(api_key="demo_key")
        print("✅ 演示类创建成功")
        
        # 演示系统状态
        print("\n📊 显示系统状态:")
        status = demo.show_system_status()
        
        # 演示工具使用
        print("\n🛠️ 演示工具使用:")
        tools = demo.demo_tools_usage("如何优化数据库查询性能？")
        
        # 演示完整流程
        print("\n🚀 演示完整决策流程:")
        full_result = demo.demo_full_process("设计一个高可用的Web服务架构")
        
        return {
            "success": True,
            "demo_status": status,
            "tools_demo": len(tools) if tools else 0,
            "full_process_success": full_result.get("success", False) if full_result else False
        }
        
    except Exception as e:
        print(f"❌ 示例7执行失败: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# 主运行函数
# =============================================================================

def run_all_examples():
    """运行所有示例"""
    print("🚀 Neogenesis-LangChain集成示例演示")
    print("="*80)
    
    examples = [
        ("基础工具使用", example_basic_tools_usage),
        ("决策链使用", example_decision_chain_usage),
        ("五阶段决策过程", example_five_stage_process),
        ("适配器使用", example_adapter_usage),
        ("状态管理", example_state_management),
        ("快速决策函数", example_quick_decision),
        ("演示类使用", example_demo_class)
    ]
    
    results = {}
    
    for name, example_func in examples:
        try:
            print(f"\n{'='*20} 开始执行: {name} {'='*20}")
            result = example_func()
            results[name] = result
            
            if result.get("success", False):
                print(f"✅ {name} 执行成功")
            else:
                print(f"❌ {name} 执行失败: {result.get('error', 'unknown error')}")
                
        except Exception as e:
            print(f"❌ {name} 执行异常: {e}")
            results[name] = {"success": False, "error": str(e)}
    
    # 总结
    print("\n" + "="*80)
    print("📊 示例执行总结")
    print("="*80)
    
    success_count = sum(1 for result in results.values() if result.get("success", False))
    total_count = len(results)
    
    print(f"总示例数: {total_count}")
    print(f"成功执行: {success_count}")
    print(f"成功率: {success_count/total_count:.1%}")
    
    print(f"\n详细结果:")
    for name, result in results.items():
        status = "✅" if result.get("success", False) else "❌"
        print(f"  {status} {name}")
        if not result.get("success", False):
            print(f"      错误: {result.get('error', 'unknown')}")
    
    return results

if __name__ == "__main__":
    # 运行所有示例
    results = run_all_examples()
    
    print(f"\n🎯 示例演示完成，详细结果已保存")
    print("💡 您可以单独运行任何示例函数来查看具体实现")
