#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模块接口定义 - Module Interface Abstractions
定义框架中所有核心组件的抽象基类，确保模块化和可扩展性

这些抽象基类定义了框架的"合同"，任何想要集成到框架中的组件都必须遵守这些接口规范。
通过这种设计，我们实现了真正的模块化：不同的实现可以无缝替换，只要它们遵守相同的接口。
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncIterator
try:
    from .data_structures import Plan, Action, Observation, ExecutionContext, AgentState
except ImportError:
    from neogenesis_system.data_structures import Plan, Action, Observation, ExecutionContext, AgentState


class BasePlanner(ABC):
    """
    规划器抽象基类 - 所有规划器的"合同"
    
    规划器负责理解用户查询，分析任务需求，并生成包含思考过程和具体行动的执行计划。
    任何规划器实现都必须遵守这个接口，确保系统可以无缝切换不同的规划策略。
    
    核心职责：
    1. 分析用户查询和上下文
    2. 利用Agent的记忆进行决策
    3. 生成标准格式的Plan对象
    4. 支持不同复杂度的任务规划
    """
    
    def __init__(self, name: str, description: str):
        """
        初始化规划器
        
        Args:
            name: 规划器名称
            description: 规划器描述
        """
        self.name = name
        self.description = description
        self.metadata = {
            "version": "1.0.0",
            "created_at": None,
            "author": "Neogenesis Framework"
        }
    
    @abstractmethod
    def create_plan(self, query: str, memory: Any, context: Optional[Dict[str, Any]] = None) -> Plan:
        """
        创建执行计划 - 核心抽象方法
        
        这是规划器的核心功能，必须实现。根据用户查询和Agent记忆生成执行计划。
        
        Args:
            query: 用户查询字符串
            memory: Agent的记忆对象，包含历史信息和学习数据
            context: 可选的额外上下文信息
            
        Returns:
            Plan: 标准格式的执行计划对象
            
        Note:
            - 如果任务可以直接回答，Plan应包含final_answer
            - 如果需要工具执行，Plan应包含actions列表
            - 必须在thought字段中解释规划思路
        """
        pass
    
    @abstractmethod
    def validate_plan(self, plan: Plan) -> bool:
        """
        验证计划的有效性
        
        检查生成的计划是否符合逻辑，所有必要的信息是否完整。
        
        Args:
            plan: 要验证的计划对象
            
        Returns:
            bool: 计划是否有效
        """
        pass
    
    def estimate_complexity(self, query: str, context: Optional[Dict[str, Any]] = None) -> float:
        """
        估算任务复杂度 - 可选实现
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            float: 复杂度分数 (0.0-1.0)
        """
        return 0.5
    
    def can_handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        判断是否能处理该查询 - 可选实现
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            bool: 是否能处理
        """
        return True


class BaseToolExecutor(ABC):
    """
    工具执行器抽象基类 - 所有工具执行器的"合同"
    
    工具执行器负责执行计划中的所有行动，调用相应的工具，并收集执行结果。
    支持同步和异步执行模式，以及串行和并行执行策略。
    
    核心职责：
    1. 解析执行计划中的行动
    2. 调用相应的工具
    3. 收集和包装执行结果
    4. 处理执行过程中的错误
    """
    
    def __init__(self, name: str, description: str):
        """
        初始化工具执行器
        
        Args:
            name: 执行器名称
            description: 执行器描述
        """
        self.name = name
        self.description = description
        self.available_tools = {}
        self.metadata = {
            "version": "1.0.0",
            "created_at": None,
            "author": "Neogenesis Framework"
        }
    
    @abstractmethod
    def execute_plan(self, plan: Plan, context: Optional[ExecutionContext] = None) -> List[Observation]:
        """
        执行计划 - 核心抽象方法
        
        接收一个Plan对象，执行其中的所有Action，并返回观察结果列表。
        
        Args:
            plan: 要执行的计划对象
            context: 可选的执行上下文
            
        Returns:
            List[Observation]: 所有行动的执行结果
            
        Note:
            - 必须按顺序执行计划中的行动
            - 每个行动的结果都要包装成Observation对象
            - 如果某个行动失败，需要记录错误信息
        """
        pass
    
    @abstractmethod
    def execute_action(self, action: Action) -> Observation:
        """
        执行单个行动
        
        Args:
            action: 要执行的行动对象
            
        Returns:
            Observation: 执行结果观察
        """
        pass
    
    def register_tool(self, tool_name: str, tool_instance: Any):
        """
        注册工具 - 可选实现
        
        Args:
            tool_name: 工具名称
            tool_instance: 工具实例
        """
        self.available_tools[tool_name] = tool_instance
    
    def get_available_tools(self) -> List[str]:
        """
        获取可用工具列表
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self.available_tools.keys())
    
    def validate_action(self, action: Action) -> bool:
        """
        验证行动的有效性
        
        Args:
            action: 要验证的行动
            
        Returns:
            bool: 行动是否有效
        """
        return action.tool_name in self.available_tools


class BaseAsyncToolExecutor(BaseToolExecutor):
    """
    异步工具执行器抽象基类
    
    扩展BaseToolExecutor，添加异步执行能力，支持高并发和非阻塞操作。
    """
    
    @abstractmethod
    async def execute_plan_async(self, plan: Plan, context: Optional[ExecutionContext] = None) -> List[Observation]:
        """
        异步执行计划
        
        Args:
            plan: 要执行的计划对象
            context: 可选的执行上下文
            
        Returns:
            List[Observation]: 所有行动的执行结果
        """
        pass
    
    @abstractmethod
    async def execute_action_async(self, action: Action) -> Observation:
        """
        异步执行单个行动
        
        Args:
            action: 要执行的行动对象
            
        Returns:
            Observation: 执行结果观察
        """
        pass
    
    async def execute_actions_parallel(self, actions: List[Action]) -> List[Observation]:
        """
        并行执行多个行动 - 可选实现
        
        Args:
            actions: 要并行执行的行动列表
            
        Returns:
            List[Observation]: 执行结果列表
        """
        tasks = [self.execute_action_async(action) for action in actions]
        return await asyncio.gather(*tasks)


class BaseMemory(ABC):
    """
    记忆模块抽象基类 - 所有记忆模块的"合同"
    
    记忆模块负责存储和检索Agent的经验、学习数据和上下文信息。
    支持不同类型的存储后端和检索策略。
    
    核心职责：
    1. 存储执行历史和学习数据
    2. 支持灵活的检索机制
    3. 管理记忆的生命周期
    4. 提供记忆统计和分析
    """
    
    def __init__(self, name: str, description: str):
        """
        初始化记忆模块
        
        Args:
            name: 记忆模块名称
            description: 记忆模块描述
        """
        self.name = name
        self.description = description
        self.metadata = {
            "version": "1.0.0",
            "created_at": None,
            "author": "Neogenesis Framework"
        }
    
    @abstractmethod
    def store(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        存储信息 - 核心抽象方法
        
        Args:
            key: 存储键
            value: 要存储的值
            metadata: 可选的元数据
            
        Returns:
            bool: 存储是否成功
        """
        pass
    
    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        """
        检索信息 - 核心抽象方法
        
        Args:
            key: 检索键
            
        Returns:
            Optional[Any]: 检索到的值，如果不存在返回None
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除信息
        
        Args:
            key: 要删除的键
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 要检查的键
            
        Returns:
            bool: 键是否存在
        """
        pass
    
    def search(self, pattern: str, limit: Optional[int] = None) -> List[str]:
        """
        搜索匹配的键 - 可选实现
        
        Args:
            pattern: 搜索模式
            limit: 结果数量限制
            
        Returns:
            List[str]: 匹配的键列表
        """
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息 - 可选实现
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {}
    
    def cleanup(self, retention_days: Optional[int] = None):
        """
        清理过期记忆 - 可选实现
        
        Args:
            retention_days: 保留天数
        """
        pass


class BaseAgent(ABC):
    """
    Agent抽象基类 - 所有Agent的"合同"
    
    Agent是框架的顶层设计，由Planner、ToolExecutor和Memory三个核心组件组成。
    Agent负责协调这些组件，实现完整的任务处理流程。
    
    核心职责：
    1. 协调Planner、ToolExecutor和Memory组件
    2. 管理完整的任务执行生命周期
    3. 处理异常和错误恢复
    4. 维护Agent状态和性能指标
    """
    
    def __init__(self, 
                 planner: BasePlanner, 
                 tool_executor: Union[BaseToolExecutor, BaseAsyncToolExecutor], 
                 memory: BaseMemory,
                 name: str = "Agent",
                 description: str = "Generic Agent"):
        """
        初始化Agent
        
        Args:
            planner: 规划器实例
            tool_executor: 工具执行器实例
            memory: 记忆模块实例
            name: Agent名称
            description: Agent描述
        """
        self.planner = planner
        self.tool_executor = tool_executor
        self.memory = memory
        self.name = name
        self.description = description
        
        # Agent状态
        self.state = AgentState()
        self.is_running = False
        
        # 性能统计
        self.stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time": 0.0,
            "average_plan_size": 0.0
        }
        
        self.metadata = {
            "version": "1.0.0",
            "created_at": None,
            "author": "Neogenesis Framework"
        }
    
    @abstractmethod
    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        运行Agent - 核心抽象方法
        
        这是Agent的主要入口点，接收用户查询并返回处理结果。
        
        Args:
            query: 用户查询字符串
            context: 可选的上下文信息
            
        Returns:
            str: 处理结果
            
        Note:
            实现应该遵循以下流程：
            1. 使用Planner生成计划
            2. 使用ToolExecutor执行计划
            3. 将结果存储到Memory
            4. 返回最终结果
        """
        pass
    
    def plan_task(self, query: str, context: Optional[Dict[str, Any]] = None) -> Plan:
        """
        规划任务 - 使用Planner生成计划
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            Plan: 执行计划
        """
        return self.planner.create_plan(query, self.memory, context)
    
    def execute_plan(self, plan: Plan) -> List[Observation]:
        """
        执行计划 - 使用ToolExecutor执行计划
        
        Args:
            plan: 要执行的计划
            
        Returns:
            List[Observation]: 执行结果
        """
        return self.tool_executor.execute_plan(plan)
    
    def store_memory(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        存储记忆
        
        Args:
            key: 存储键
            value: 要存储的值
            metadata: 元数据
            
        Returns:
            bool: 存储是否成功
        """
        return self.memory.store(key, value, metadata)
    
    def retrieve_memory(self, key: str) -> Optional[Any]:
        """
        检索记忆
        
        Args:
            key: 检索键
            
        Returns:
            Optional[Any]: 检索到的值
        """
        return self.memory.retrieve(key)
    
    def update_stats(self, success: bool, execution_time: float, plan_size: int):
        """
        更新性能统计
        
        Args:
            success: 任务是否成功
            execution_time: 执行时间
            plan_size: 计划大小
        """
        self.stats["total_tasks"] += 1
        if success:
            self.stats["successful_tasks"] += 1
        else:
            self.stats["failed_tasks"] += 1
        
        self.stats["total_execution_time"] += execution_time
        
        # 更新平均计划大小
        total_tasks = self.stats["total_tasks"]
        current_avg = self.stats["average_plan_size"]
        self.stats["average_plan_size"] = ((current_avg * (total_tasks - 1)) + plan_size) / total_tasks
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.stats["total_tasks"]
        if total == 0:
            return 0.0
        return self.stats["successful_tasks"] / total
    
    @property
    def average_execution_time(self) -> float:
        """计算平均执行时间"""
        total = self.stats["total_tasks"]
        if total == 0:
            return 0.0
        return self.stats["total_execution_time"] / total
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取Agent状态信息
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        return {
            "name": self.name,
            "is_running": self.is_running,
            "components": {
                "planner": self.planner.name,
                "tool_executor": self.tool_executor.name,
                "memory": self.memory.name
            },
            "stats": self.stats.copy(),
            "success_rate": self.success_rate,
            "average_execution_time": self.average_execution_time
        }


class BaseAsyncAgent(BaseAgent):
    """
    异步Agent抽象基类
    
    扩展BaseAgent，添加异步执行能力，支持高并发任务处理。
    """
    
    @abstractmethod
    async def run_async(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        异步运行Agent
        
        Args:
            query: 用户查询字符串
            context: 可选的上下文信息
            
        Returns:
            str: 处理结果
        """
        pass
    
    async def execute_plan_async(self, plan: Plan) -> List[Observation]:
        """
        异步执行计划
        
        Args:
            plan: 要执行的计划
            
        Returns:
            List[Observation]: 执行结果
        """
        if isinstance(self.tool_executor, BaseAsyncToolExecutor):
            return await self.tool_executor.execute_plan_async(plan)
        else:
            # 如果工具执行器不支持异步，在线程池中执行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.tool_executor.execute_plan, plan)


# 工厂函数
def create_agent(planner_class, executor_class, memory_class, 
                planner_config: Optional[Dict] = None,
                executor_config: Optional[Dict] = None,
                memory_config: Optional[Dict] = None,
                agent_name: str = "CustomAgent") -> BaseAgent:
    """
    Agent工厂函数 - 简化Agent创建过程
    
    Args:
        planner_class: 规划器类
        executor_class: 执行器类
        memory_class: 记忆模块类
        planner_config: 规划器配置
        executor_config: 执行器配置
        memory_config: 记忆模块配置
        agent_name: Agent名称
        
    Returns:
        BaseAgent: 创建的Agent实例
    """
    # 创建组件实例
    planner = planner_class(**(planner_config or {}))
    executor = executor_class(**(executor_config or {}))
    memory = memory_class(**(memory_config or {}))
    
    # 使用默认Agent实现（需要用户提供）
    class DefaultAgent(BaseAgent):
        def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
            # 基本实现
            plan = self.plan_task(query, context)
            if plan.is_direct_answer:
                return plan.final_answer
            
            observations = self.execute_plan(plan)
            # 简单地返回最后一个观察的输出
            if observations:
                return observations[-1].output
            return "No results"
    
    return DefaultAgent(planner, executor, memory, agent_name)
