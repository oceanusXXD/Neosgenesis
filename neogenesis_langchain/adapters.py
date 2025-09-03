#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - LangChain Adapters
为Neogenesis System提供LangChain集成适配器
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

try:
    from langchain.agents import initialize_agent, AgentType
    from langchain.agents.agent import AgentExecutor
    from langchain.tools import BaseTool
    from langchain.schema import BaseLanguageModel
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # 类型别名定义
    class BaseLanguageModel:
        pass
    
    class AgentExecutor:
        pass

# 导入Neogenesis组件
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from neogenesis_system.meta_mab.controller import MainController
from .tools import get_all_neogenesis_tools, create_neogenesis_toolset
from .chains.chains import create_neogenesis_decision_chain
from .state.state_management import NeogenesisStateManager, DecisionStage

logger = logging.getLogger(__name__)

# =============================================================================
# 核心适配器类
# =============================================================================

class NeogenesisAdapter:
    """
    Neogenesis-LangChain适配器
    
    功能：
    - 将完整的Neogenesis System包装为LangChain兼容的接口
    - 提供工具和链两种使用模式
    - 管理状态和配置
    """
    
    def __init__(self,
                 api_key: str = "",
                 search_engine: str = "duckduckgo",
                 llm_client=None,
                 web_search_client=None,
                 enable_state_management: bool = True,
                 storage_path: str = "./neogenesis_state"):
        """
        初始化适配器
        
        Args:
            api_key: API密钥
            search_engine: 搜索引擎类型
            llm_client: LLM客户端
            web_search_client: 网络搜索客户端
            enable_state_management: 是否启用状态管理
            storage_path: 状态存储路径
        """
        self.api_key = api_key
        self.search_engine = search_engine
        self.llm_client = llm_client
        self.web_search_client = web_search_client
        
        # 初始化Neogenesis原生控制器（用于混合模式）
        try:
            self.neogenesis_controller = MainController()
            self.has_native_controller = True
            logger.info("🧠 Neogenesis原生控制器已加载")
        except Exception as e:
            self.neogenesis_controller = None
            self.has_native_controller = False
            logger.warning(f"⚠️ Neogenesis原生控制器加载失败: {e}")
        
        # 状态管理
        self.state_manager = None
        if enable_state_management:
            try:
                self.state_manager = NeogenesisStateManager(storage_path=storage_path)
                logger.info("🗃️ 状态管理器已启用")
            except Exception as e:
                logger.warning(f"⚠️ 状态管理器初始化失败: {e}")
        
        # 缓存工具和链
        self._tools_cache = None
        self._chains_cache = {}
        
        logger.info("🔗 NeogenesisAdapter 初始化完成")
    
    def get_tools(self) -> List[BaseTool]:
        """
        获取Neogenesis工具列表
        
        Returns:
            工具列表
        """
        if self._tools_cache is None:
            self._tools_cache = get_all_neogenesis_tools(
                api_key=self.api_key,
                search_engine=self.search_engine,
                llm_client=self.llm_client,
                web_search_client=self.web_search_client
            )
        
        return self._tools_cache
    
    def get_tool_dict(self) -> Dict[str, BaseTool]:
        """
        获取工具字典
        
        Returns:
            工具名称到工具对象的映射
        """
        tools = self.get_tools()
        return {tool.name: tool for tool in tools}
    
    def get_decision_chain(self, chain_type: str = "basic"):
        """
        获取决策链
        
        Args:
            chain_type: 链类型（"basic" 或 "five_stage"）
            
        Returns:
            决策链实例
        """
        if chain_type not in self._chains_cache:
            self._chains_cache[chain_type] = create_neogenesis_decision_chain(
                api_key=self.api_key,
                search_engine=self.search_engine,
                llm_client=self.llm_client,
                web_search_client=self.web_search_client,
                chain_type=chain_type
            )
        
        return self._chains_cache[chain_type]
    
    def create_agent(self, 
                    llm,  # BaseLanguageModel
                    agent_type: str = "zero-shot-react-description",
                    include_other_tools: List = None,  # List[BaseTool]
                    **kwargs):
        """
        创建集成Neogenesis工具的LangChain Agent
        
        Args:
            llm: 语言模型
            agent_type: Agent类型
            include_other_tools: 包含的其他工具
            **kwargs: 其他参数
            
        Returns:
            Agent执行器
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain not available. Please install langchain package.")
        
        # 获取Neogenesis工具
        neogenesis_tools = self.get_tools()
        
        # 合并其他工具
        all_tools = neogenesis_tools.copy()
        if include_other_tools:
            all_tools.extend(include_other_tools)
        
        # 映射agent类型
        agent_type_mapping = {
            "zero-shot-react-description": AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            "structured-chat": AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            "conversational": AgentType.CONVERSATIONAL_REACT_DESCRIPTION
        }
        
        langchain_agent_type = agent_type_mapping.get(agent_type, AgentType.ZERO_SHOT_REACT_DESCRIPTION)
        
        # 创建agent
        agent = initialize_agent(
            tools=all_tools,
            llm=llm,
            agent=langchain_agent_type,
            verbose=kwargs.get("verbose", True),
            **kwargs
        )
        
        logger.info(f"🤖 创建Neogenesis增强Agent: {len(all_tools)}个工具")
        return agent
    
    def run_decision_process(self,
                           user_query: str,
                           process_type: str = "tools",
                           **kwargs) -> Dict[str, Any]:
        """
        运行完整的决策过程
        
        Args:
            user_query: 用户查询
            process_type: 处理类型（"tools", "chain", "native"）
            **kwargs: 其他参数
            
        Returns:
            决策结果
        """
        session_id = kwargs.get("session_id", str(uuid.uuid4()))
        
        # 创建会话状态
        if self.state_manager:
            self.state_manager.create_session(
                session_id=session_id,
                user_query=user_query,
                execution_context=kwargs.get("execution_context")
            )
        
        try:
            if process_type == "native" and self.has_native_controller:
                # 使用原生Neogenesis控制器
                result = self._run_native_process(user_query, session_id, **kwargs)
            elif process_type == "chain":
                # 使用LangChain链
                result = self._run_chain_process(user_query, session_id, **kwargs)
            else:
                # 使用工具组合
                result = self._run_tools_process(user_query, session_id, **kwargs)
            
            # 完成会话
            if self.state_manager:
                self.state_manager.complete_session(session_id, result)
            
            return result
            
        except Exception as e:
            error_msg = f"决策过程执行失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # 更新会话状态
            if self.state_manager:
                self.state_manager.update_session_stage(
                    session_id=session_id,
                    stage=DecisionStage.ERROR,
                    success=False,
                    data={"error": error_msg},
                    execution_time=0.0,
                    error_message=error_msg
                )
            
            return {
                "success": False,
                "error": error_msg,
                "session_id": session_id,
                "process_type": process_type
            }
    
    def _run_native_process(self, user_query: str, session_id: str, **kwargs) -> Dict[str, Any]:
        """使用原生Neogenesis控制器运行决策过程"""
        deepseek_confidence = kwargs.get("deepseek_confidence", 0.5)
        execution_context = kwargs.get("execution_context")
        
        result = self.neogenesis_controller.make_decision(
            user_query=user_query,
            deepseek_confidence=deepseek_confidence,
            execution_context=execution_context
        )
        
        return {
            "success": True,
            "process_type": "native",
            "session_id": session_id,
            "native_result": result
        }
    
    def _run_chain_process(self, user_query: str, session_id: str, **kwargs) -> Dict[str, Any]:
        """使用LangChain链运行决策过程"""
        chain_type = kwargs.get("chain_type", "basic")
        chain = self.get_decision_chain(chain_type)
        
        chain_inputs = {
            "user_query": user_query,
            **kwargs
        }
        
        chain_result = chain(chain_inputs)
        
        return {
            "success": True,
            "process_type": "chain",
            "chain_type": chain_type,
            "session_id": session_id,
            "chain_result": chain_result
        }
    
    def _run_tools_process(self, user_query: str, session_id: str, **kwargs) -> Dict[str, Any]:
        """使用工具组合运行决策过程"""
        tools = self.get_tool_dict()
        
        # 按序执行工具
        results = {}
        
        # 1. 思维种子生成
        if self.state_manager:
            self.state_manager.update_session_stage(
                session_id, DecisionStage.THINKING_SEED, True, {}, 0.0
            )
        
        seed_tool = tools.get("neogenesis_thinking_seed")
        if seed_tool:
            seed_result = seed_tool.run(
                user_query=user_query,
                execution_context=kwargs.get("execution_context")
            )
            results["thinking_seed"] = json.loads(seed_result)
        
        # 2. 路径生成
        if results.get("thinking_seed"):
            if self.state_manager:
                self.state_manager.update_session_stage(
                    session_id, DecisionStage.PATH_GENERATION, True, {}, 0.0
                )
            
            path_tool = tools.get("neogenesis_path_generator")
            if path_tool:
                thinking_seed = results["thinking_seed"].get("thinking_seed", "")
                path_result = path_tool.run(
                    thinking_seed=thinking_seed,
                    task=user_query,
                    max_paths=kwargs.get("max_paths", 4)
                )
                results["path_generation"] = json.loads(path_result)
        
        # 3. MAB决策
        if results.get("path_generation"):
            if self.state_manager:
                self.state_manager.update_session_stage(
                    session_id, DecisionStage.MAB_DECISION, True, {}, 0.0
                )
            
            mab_tool = tools.get("neogenesis_mab_decision")
            if mab_tool:
                reasoning_paths = results["path_generation"].get("reasoning_paths", [])
                mab_result = mab_tool.run(
                    reasoning_paths=reasoning_paths,
                    user_query=user_query,
                    execution_context=kwargs.get("execution_context")
                )
                results["mab_decision"] = json.loads(mab_result)
        
        return {
            "success": True,
            "process_type": "tools",
            "session_id": session_id,
            "tools_results": results
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        status = {
            "adapter_initialized": True,
            "langchain_available": LANGCHAIN_AVAILABLE,
            "native_controller_available": self.has_native_controller,
            "state_management_enabled": self.state_manager is not None,
            "tools_count": len(self.get_tools()),
            "chains_cached": len(self._chains_cache)
        }
        
        if self.state_manager:
            status["session_statistics"] = self.state_manager.get_session_statistics()
        
        return status

# =============================================================================
# 便捷函数
# =============================================================================

def create_neogenesis_agent(
    llm,  # BaseLanguageModel
    api_key: str = "",
    search_engine: str = "duckduckgo",
    agent_type: str = "zero-shot-react-description",
    include_other_tools: List = None,  # List[BaseTool]
    **kwargs
):
    """
    快速创建Neogenesis增强的LangChain Agent
    
    Args:
        llm: 语言模型
        api_key: API密钥
        search_engine: 搜索引擎
        agent_type: Agent类型
        include_other_tools: 其他工具
        **kwargs: 其他参数
        
    Returns:
        Agent执行器
    """
    adapter = NeogenesisAdapter(
        api_key=api_key,
        search_engine=search_engine,
        **kwargs
    )
    
    return adapter.create_agent(
        llm=llm,
        agent_type=agent_type,
        include_other_tools=include_other_tools,
        **kwargs
    )

def create_hybrid_agent(
    llm,  # BaseLanguageModel
    api_key: str = "",
    use_native_fallback: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    创建混合模式的Agent（同时支持LangChain和原生Neogenesis）
    
    Args:
        llm: 语言模型
        api_key: API密钥
        use_native_fallback: 是否使用原生回退
        **kwargs: 其他参数
        
    Returns:
        混合Agent配置
    """
    adapter = NeogenesisAdapter(api_key=api_key, **kwargs)
    
    # 创建LangChain agent
    langchain_agent = None
    if LANGCHAIN_AVAILABLE:
        try:
            langchain_agent = adapter.create_agent(llm=llm, **kwargs)
        except Exception as e:
            logger.warning(f"⚠️ LangChain Agent创建失败: {e}")
    
    # 创建原生控制器
    native_controller = adapter.neogenesis_controller if use_native_fallback else None
    
    return {
        "adapter": adapter,
        "langchain_agent": langchain_agent,
        "native_controller": native_controller,
        "tools": adapter.get_tool_dict(),
        "chains": {
            "basic": adapter.get_decision_chain("basic"),
            "five_stage": adapter.get_decision_chain("five_stage")
        }
    }

def quick_decision(
    user_query: str,
    api_key: str = "",
    process_type: str = "tools",
    **kwargs
) -> Dict[str, Any]:
    """
    快速执行决策过程
    
    Args:
        user_query: 用户查询
        api_key: API密钥
        process_type: 处理类型
        **kwargs: 其他参数
        
    Returns:
        决策结果
    """
    adapter = NeogenesisAdapter(api_key=api_key, **kwargs)
    return adapter.run_decision_process(
        user_query=user_query,
        process_type=process_type,
        **kwargs
    )

# =============================================================================
# 演示和测试
# =============================================================================

class NeogenesisDemo:
    """Neogenesis演示类"""
    
    def __init__(self, api_key: str = ""):
        self.adapter = NeogenesisAdapter(api_key=api_key)
        logger.info("🎯 NeogenesisDemo 初始化完成")
    
    def demo_tools_usage(self, user_query: str = "如何优化网站性能？"):
        """演示工具使用"""
        print(f"🧪 演示工具使用: {user_query}")
        
        tools = self.adapter.get_tool_dict()
        print(f"✅ 可用工具: {list(tools.keys())}")
        
        # 演示思维种子生成
        if "neogenesis_thinking_seed" in tools:
            result = tools["neogenesis_thinking_seed"].run(user_query=user_query)
            print(f"🧠 思维种子生成结果: {result[:100]}...")
        
        return tools
    
    def demo_chain_usage(self, user_query: str = "如何优化网站性能？"):
        """演示链使用"""
        print(f"🔗 演示链使用: {user_query}")
        
        try:
            chain = self.adapter.get_decision_chain("basic")
            result = chain({"user_query": user_query})
            print(f"✅ 决策链结果: {result}")
            return result
        except Exception as e:
            print(f"❌ 链使用失败: {e}")
            return None
    
    def demo_full_process(self, user_query: str = "如何优化网站性能？"):
        """演示完整决策过程"""
        print(f"🚀 演示完整决策过程: {user_query}")
        
        result = self.adapter.run_decision_process(
            user_query=user_query,
            process_type="tools"
        )
        
        print(f"✅ 决策结果: {result.get('success', False)}")
        return result
    
    def show_system_status(self):
        """显示系统状态"""
        status = self.adapter.get_system_status()
        print("📊 系统状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        return status

# =============================================================================
# 兼容性检查
# =============================================================================

def check_integration_compatibility() -> Dict[str, Any]:
    """
    检查集成兼容性
    
    Returns:
        兼容性信息
    """
    compatibility = {
        "langchain_available": LANGCHAIN_AVAILABLE,
        "neogenesis_components_available": True,
        "state_management_available": True,
        "recommended_packages": [
            "langchain>=0.1.0",
            "langchain-core",
            "langchain-openai",
            "duckduckgo-search"
        ]
    }
    
    # 检查LangChain版本
    if LANGCHAIN_AVAILABLE:
        try:
            import langchain
            compatibility["langchain_version"] = langchain.__version__
        except:
            compatibility["langchain_version"] = "unknown"
    
    # 检查Neogenesis组件
    try:
        from neogenesis_system.meta_mab.controller import MainController
        compatibility["neogenesis_controller_available"] = True
    except:
        compatibility["neogenesis_controller_available"] = False
    
    return compatibility

if __name__ == "__main__":
    # 运行演示
    print("🧪 Neogenesis-LangChain集成演示")
    
    # 检查兼容性
    compat_info = check_integration_compatibility()
    print(f"🔧 兼容性检查: {compat_info}")
    
    # 创建演示实例
    try:
        demo = NeogenesisDemo()
        
        # 显示系统状态
        demo.show_system_status()
        
        # 演示工具使用
        demo.demo_tools_usage()
        
        # 演示完整流程
        demo.demo_full_process()
        
        print("✅ 演示完成")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
