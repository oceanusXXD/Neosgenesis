#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - LangChain使用示例
展示LangChain用户如何轻松使用Neogenesis的五个阶段功能
"""

import logging
import json
from typing import Dict, List, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def example_individual_stages():
    """示例1：单独使用各个阶段的工具"""
    print("🔧 示例1：单独使用各个阶段的LangChain工具")
    print("=" * 60)
    
    try:
        from ..tools import (
            NeogenesisThinkingSeedTool,
            NeogenesisPathGeneratorTool, 
            NeogenesisMABDecisionTool,
            NeogenesisIdeaVerificationTool
        )
        
        # 用户查询
        user_query = "如何提高团队的工作效率和协作能力？"
        print(f"📝 用户查询: {user_query}")
        
        # 阶段一：思维种子生成
        print("\n🧠 阶段一：思维种子生成")
        thinking_tool = NeogenesisThinkingSeedTool()
        seed_result = thinking_tool.run(user_query)
        seed_data = json.loads(seed_result)
        thinking_seed = seed_data.get("thinking_seed", "")
        print(f"✅ 思维种子: {thinking_seed[:100]}...")
        
        # 阶段二：种子验证（可选）
        print("\n🔍 阶段二：种子验证检查")
        verification_tool = NeogenesisIdeaVerificationTool()
        verification_result = verification_tool.run(thinking_seed)
        verification_data = json.loads(verification_result)
        print(f"✅ 验证结果: {verification_data.get('verification_success', False)}")
        
        # 阶段三：路径生成
        print("\n🛤️ 阶段三：思维路径生成")
        path_tool = NeogenesisPathGeneratorTool()
        paths_result = path_tool.run(f"thinking_seed: {thinking_seed}, task: {user_query}")
        paths_data = json.loads(paths_result)
        reasoning_paths = paths_data.get("reasoning_paths", [])
        print(f"✅ 生成路径: {len(reasoning_paths)} 条")
        for i, path in enumerate(reasoning_paths[:3]):
            print(f"   {i+1}. {path.get('path_type', '')}: {path.get('description', '')[:50]}...")
        
        # 阶段四：路径验证（批量验证）
        print("\n🔬 阶段四：路径验证学习")
        verified_paths = []
        for path in reasoning_paths:
            path_text = f"{path.get('path_type', '')}: {path.get('description', '')}"
            path_verification = verification_tool.run(path_text)
            path_verification_data = json.loads(path_verification)
            path["verification_result"] = path_verification_data
            verified_paths.append(path)
        print(f"✅ 路径验证: {len(verified_paths)} 条路径已验证")
        
        # 阶段五：MAB决策
        print("\n🏆 阶段五：智能最终决策")
        mab_tool = NeogenesisMABDecisionTool()
        decision_result = mab_tool.run(f"reasoning_paths: {json.dumps(verified_paths)}, user_query: {user_query}")
        decision_data = json.loads(decision_result)
        selected_path = decision_data.get("selected_path", {})
        print(f"✅ 最终决策: {selected_path.get('path_type', '')} - {selected_path.get('description', '')[:100]}...")
        
        print("\n🎉 五阶段流程完成！每个阶段都可以作为独立的LangChain工具使用。")
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保Neogenesis工具已正确安装")
    except Exception as e:
        print(f"❌ 执行错误: {e}")

def example_integrated_five_stage_tool():
    """示例2：使用集成的五阶段决策工具"""
    print("\n🔗 示例2：使用集成的五阶段决策工具")
    print("=" * 60)
    
    try:
        from ..tools import NeogenesisFiveStageDecisionTool
        
        # 创建五阶段决策工具
        five_stage_tool = NeogenesisFiveStageDecisionTool()
        
        # 用户查询
        user_query = "我们公司应该如何进入AI市场？"
        print(f"📝 用户查询: {user_query}")
        
        # 一次性执行完整的五阶段决策
        print("\n🚀 执行完整五阶段决策流程...")
        complete_result = five_stage_tool.run(user_query)
        result_data = json.loads(complete_result)
        
        if result_data.get("success", False):
            print("✅ 五阶段决策成功完成！")
            print(f"⏱️ 执行时间: {result_data.get('execution_time', 0):.2f} 秒")
            print(f"📊 成功率: {result_data.get('summary', {}).get('success_rate', 0):.1f}%")
            print(f"🛤️ 生成路径: {result_data.get('summary', {}).get('paths_generated', 0)} 条")
            
            # 显示最终建议
            final_rec = result_data.get("final_recommendation", {})
            print(f"\n🎯 最终建议:")
            print(f"   类型: {final_rec.get('path_type', '未知')}")
            print(f"   描述: {final_rec.get('description', '无描述')[:150]}...")
            print(f"   置信度: {final_rec.get('confidence_score', 0):.2f}")
        else:
            print(f"❌ 决策失败: {result_data.get('error', '未知错误')}")
        
        print("\n🌟 优势：一次调用完成所有阶段，获得完整的决策报告！")
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
    except Exception as e:
        print(f"❌ 执行错误: {e}")

def example_langchain_agent_integration():
    """示例3：集成到LangChain Agent中"""
    print("\n🤖 示例3：集成到LangChain Agent中")
    print("=" * 60)
    
    try:
        # 检查LangChain是否可用
        try:
            from langchain.agents import initialize_agent, AgentType
            from langchain.llms import OpenAI
        except ImportError:
            print("⚠️ LangChain未安装，无法演示Agent集成")
            print("安装命令: pip install langchain")
            return
        
        from ..tools import get_all_neogenesis_tools
        
        # 获取所有Neogenesis工具
        neogenesis_tools = get_all_neogenesis_tools()
        print(f"🔧 获取到 {len(neogenesis_tools)} 个Neogenesis工具:")
        for tool in neogenesis_tools:
            print(f"   - {tool.name}: {tool.description.split('.')[0]}...")
        
        print("\n📝 Agent集成代码示例:")
        agent_code = '''
# 创建LangChain Agent并集成Neogenesis工具
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from neogenesis_langchain import get_all_neogenesis_tools

# 初始化LLM
llm = OpenAI(temperature=0)

# 获取Neogenesis工具
tools = get_all_neogenesis_tools(api_key="your_api_key")

# 创建Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# 使用Agent进行复杂决策
result = agent.run("帮我分析一下是否应该投资加密货币，并给出详细的决策过程")
'''
        print(agent_code)
        
        print("🌟 优势：")
        print("   - Neogenesis工具自动成为Agent的能力")
        print("   - Agent可以智能选择合适的阶段工具")
        print("   - 支持复杂的多轮对话和决策")
        
    except Exception as e:
        print(f"❌ 示例生成错误: {e}")

def example_langchain_chain_integration():
    """示例4：集成到LangChain Chain中"""
    print("\n⛓️ 示例4：集成到LangChain Chain中")
    print("=" * 60)
    
    try:
        # 检查LangChain是否可用
        try:
            from langchain.chains import LLMChain
            from langchain.prompts import PromptTemplate
        except ImportError:
            print("⚠️ LangChain未安装，无法演示Chain集成")
            return
        
        from ..chains.chains import NeogenesisFiveStageChain, create_enhanced_neogenesis_chain
        
        print("📝 Neogenesis决策链使用示例:")
        chain_code = '''
# 方式1：使用预构建的Neogenesis决策链
from neogenesis_langchain.chains import NeogenesisFiveStageChain

# 创建五阶段决策链
decision_chain = NeogenesisFiveStageChain(
    api_key="your_api_key",
    search_engine="duckduckgo"
)

# 执行决策
result = decision_chain({
    "user_query": "我们应该采用哪种营销策略来推广新产品？",
    "use_rag_enhancement": True,
    "max_paths": 5
})

# 方式2：使用增强的协调器链（如果第二阶段可用）
from neogenesis_langchain.chains import create_enhanced_neogenesis_chain

enhanced_chain = create_enhanced_neogenesis_chain(
    chain_type="coordinated",
    api_key="your_api_key"
)

# 执行增强决策
enhanced_result = enhanced_chain({
    "user_query": "如何优化我们的供应链管理？",
    "execution_mode": "adaptive"
})
'''
        print(chain_code)
        
        print("🌟 Chain模式优势：")
        print("   - 标准的LangChain Chain接口")
        print("   - 可以与其他Chain组合")
        print("   - 支持流式处理和回调")
        print("   - 完整的错误处理和恢复机制")
        
    except Exception as e:
        print(f"❌ 示例生成错误: {e}")

def example_configuration_and_customization():
    """示例5：配置和定制化"""
    print("\n⚙️ 示例5：配置和定制化")
    print("=" * 60)
    
    config_code = '''
# 自定义配置示例
from neogenesis_langchain import NeogenesisFiveStageDecisionTool

# 基础配置
tool = NeogenesisFiveStageDecisionTool(
    api_key="your_openai_api_key",
    search_engine="duckduckgo"  # 或 "google", "bing"
)

# 高级配置：禁用某些阶段
result = tool.run(
    user_query="你的问题",
    use_rag_enhancement=False,       # 禁用RAG增强
    enable_seed_verification=True,   # 启用种子验证
    max_paths=3,                     # 限制路径数量
    enable_path_verification=False,  # 禁用路径验证
    use_mab_algorithm=True          # 使用MAB算法
)

# 批量工具创建
from neogenesis_langchain import get_all_neogenesis_tools

# 创建所有工具，可以选择性使用
all_tools = get_all_neogenesis_tools(
    api_key="your_api_key",
    search_engine="google",
    llm_client=your_custom_llm,
    web_search_client=your_custom_search_client
)

# 选择特定工具
thinking_tool = all_tools[0]  # NeogenesisThinkingSeedTool
path_tool = all_tools[2]      # NeogenesisPathGeneratorTool
five_stage_tool = all_tools[-1]  # NeogenesisFiveStageDecisionTool
'''
    print(config_code)
    
    print("🔧 可配置选项：")
    print("   - API密钥和客户端配置")
    print("   - 搜索引擎选择（DuckDuckGo/Google/Bing）")
    print("   - 各阶段的启用/禁用")
    print("   - 路径生成数量控制")
    print("   - MAB算法参数调整")

def run_all_examples():
    """运行所有示例"""
    print("🎯 Neogenesis × LangChain 集成示例")
    print("展示LangChain用户如何轻松使用Neogenesis的五个阶段功能")
    print("=" * 80)
    
    # 运行各个示例
    example_individual_stages()
    example_integrated_five_stage_tool()
    example_langchain_agent_integration()
    example_langchain_chain_integration() 
    example_configuration_and_customization()
    
    print("\n" + "=" * 80)
    print("🎉 所有示例展示完成！")
    print("\n📚 总结：Neogenesis与LangChain的集成方式")
    print("1. 🔧 单独工具模式：每个阶段作为独立的LangChain工具")
    print("2. 🔗 集成工具模式：五阶段流程封装为单一工具")
    print("3. 🤖 Agent集成模式：工具自动集成到LangChain Agent")
    print("4. ⛓️ Chain集成模式：作为LangChain Chain的一部分")
    print("5. ⚙️ 灵活配置模式：支持各种定制化需求")
    print("\n✨ 核心优势：不修改原有核心代码，通过适配器模式实现完美兼容！")

if __name__ == "__main__":
    run_all_examples()
