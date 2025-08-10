#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具抽象基类 - Tool Abstraction Base Classes
定义所有工具必须遵守的统一接口，确保系统任何部分都可以用同样的方式与任何工具交互
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具类别枚举"""
    SEARCH = "search"           # 搜索类工具
    LLM = "llm"                # LLM调用类工具
    SYSTEM = "system"          # 系统管理类工具
    OPTIMIZATION = "optimization"  # 性能优化类工具
    DATA_PROCESSING = "data_processing"  # 数据处理类工具
    COMMUNICATION = "communication"      # 通信类工具


class ToolStatus(Enum):
    """工具状态枚举"""
    READY = "ready"           # 准备就绪
    BUSY = "busy"             # 忙碌中
    ERROR = "error"           # 错误状态
    UNAVAILABLE = "unavailable"  # 不可用


@dataclass
class ToolResult:
    """工具执行结果统一数据结构"""
    success: bool                    # 执行是否成功
    data: Any = None                # 返回的数据
    error_message: str = ""         # 错误信息
    execution_time: float = 0.0     # 执行时间(秒)
    metadata: Dict[str, Any] = None # 额外的元数据
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolCapability:
    """工具能力描述"""
    supported_inputs: List[str]      # 支持的输入类型
    output_types: List[str]          # 输出类型
    async_support: bool = False      # 是否支持异步执行
    batch_support: bool = False      # 是否支持批量处理
    requires_auth: bool = False      # 是否需要认证
    rate_limited: bool = False       # 是否有速率限制


class BaseTool(ABC):
    """
    工具抽象基类 - 所有工具必须继承此类
    
    借鉴LangChain的Tool思想，每个工具都有：
    1. 清晰的名称和描述（让LLM理解工具用途）
    2. 统一的执行接口
    3. 标准化的结果格式
    4. 能力描述和状态管理
    """
    
    def __init__(self, name: str, description: str, category: ToolCategory):
        """
        初始化工具基类
        
        Args:
            name: 工具名称，必须唯一且描述性强
            description: 工具描述，详细说明工具的功能、使用场景和输入要求
            category: 工具类别
        """
        self.name = name
        self.description = description
        self.category = category
        self.status = ToolStatus.READY
        self.usage_count = 0
        self.last_used = None
        
        # 工具元数据
        self.metadata = {
            "created_at": None,
            "version": "1.0.0",
            "author": "Neogenesis System"
        }
        
        logger.debug(f"🔧 工具初始化: {self.name} ({self.category.value})")
    
    @property
    @abstractmethod
    def capabilities(self) -> ToolCapability:
        """
        返回工具能力描述
        子类必须实现此属性，说明工具的具体能力
        """
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> ToolResult:
        """
        执行工具的主要方法
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            ToolResult: 统一的执行结果
            
        Note:
            子类必须实现此方法，这是工具的核心功能入口
        """
        pass
    
    def validate_input(self, *args, **kwargs) -> bool:
        """
        验证输入参数
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            bool: 输入是否有效
            
        Note:
            子类可以重写此方法实现自定义验证逻辑
        """
        return True
    
    def get_usage_info(self) -> Dict[str, Any]:
        """
        获取工具使用信息
        
        Returns:
            Dict: 包含使用次数、最后使用时间等信息
        """
        return {
            "name": self.name,
            "category": self.category.value,
            "status": self.status.value,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "capabilities": {
                "supported_inputs": self.capabilities.supported_inputs,
                "output_types": self.capabilities.output_types,
                "async_support": self.capabilities.async_support,
                "batch_support": self.capabilities.batch_support,
                "requires_auth": self.capabilities.requires_auth,
                "rate_limited": self.capabilities.rate_limited
            }
        }
    
    def get_help(self) -> str:
        """
        获取工具帮助信息
        
        Returns:
            str: 格式化的帮助文本
        """
        help_text = f"""
🔧 工具: {self.name}
📝 描述: {self.description}
📂 类别: {self.category.value}
📊 状态: {self.status.value}

🔍 能力信息:
- 支持的输入类型: {', '.join(self.capabilities.supported_inputs)}
- 输出类型: {', '.join(self.capabilities.output_types)}
- 异步支持: {'✅' if self.capabilities.async_support else '❌'}
- 批量处理: {'✅' if self.capabilities.batch_support else '❌'}
- 需要认证: {'✅' if self.capabilities.requires_auth else '❌'}
- 速率限制: {'✅' if self.capabilities.rate_limited else '❌'}

📈 使用统计:
- 使用次数: {self.usage_count}
- 最后使用: {self.last_used or '从未使用'}
        """.strip()
        
        return help_text
    
    def _update_usage_stats(self):
        """更新使用统计"""
        import time
        self.usage_count += 1
        self.last_used = time.time()
    
    def _set_status(self, status: ToolStatus):
        """设置工具状态"""
        old_status = self.status
        self.status = status
        if old_status != status:
            logger.debug(f"🔧 工具 {self.name} 状态变更: {old_status.value} -> {status.value}")
    
    def __str__(self) -> str:
        return f"Tool({self.name}, {self.category.value}, {self.status.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', category='{self.category.value}')>"


class AsyncBaseTool(BaseTool):
    """
    异步工具抽象基类
    为支持异步执行的工具提供扩展接口
    """
    
    @abstractmethod
    async def execute_async(self, *args, **kwargs) -> ToolResult:
        """
        异步执行工具的主要方法
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            ToolResult: 统一的执行结果
            
        Note:
            支持异步的子类必须实现此方法
        """
        pass


class BatchProcessingTool(BaseTool):
    """
    批量处理工具抽象基类
    为支持批量处理的工具提供扩展接口
    """
    
    @abstractmethod
    def execute_batch(self, input_list: List[Any], **kwargs) -> List[ToolResult]:
        """
        批量执行工具操作
        
        Args:
            input_list: 输入数据列表
            **kwargs: 关键字参数
            
        Returns:
            List[ToolResult]: 执行结果列表
            
        Note:
            支持批量处理的子类必须实现此方法
        """
        pass


# 工具注册表，用于管理所有注册的工具
class ToolRegistry:
    """
    工具注册表 - 统一管理和访问所有可用的工具
    
    提供完整的工具生命周期管理：
    - 工具注册与注销
    - 工具发现与查询
    - 工具状态监控
    - 使用统计与性能分析
    - 健康检查与故障恢复
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[ToolCategory, List[str]] = {}
        self._tool_aliases: Dict[str, str] = {}  # 工具别名映射
        self._disabled_tools: set = set()        # 已禁用的工具
        
        # 管理器状态
        self._registry_stats = {
            "created_at": time.time(),
            "total_registrations": 0,
            "total_unregistrations": 0,
            "total_tool_executions": 0,
            "failed_executions": 0
        }
        
        logger.info("🔧 工具注册表初始化完成")
        
    def register_tool(self, tool: BaseTool, aliases: Optional[List[str]] = None, 
                     overwrite: bool = False) -> bool:
        """
        注册工具到注册表
        
        Args:
            tool: 要注册的工具实例
            aliases: 工具别名列表
            overwrite: 是否覆盖已存在的工具
            
        Returns:
            bool: 注册是否成功
        """
        # 检查工具是否已存在
        if tool.name in self._tools and not overwrite:
            logger.warning(f"⚠️ 工具 {tool.name} 已存在，跳过注册（使用 overwrite=True 强制覆盖）")
            return False
        
        # 验证工具有效性
        if not self._validate_tool(tool):
            logger.error(f"❌ 工具 {tool.name} 验证失败，注册取消")
            return False
        
        # 注册工具
        old_tool = self._tools.get(tool.name)
        self._tools[tool.name] = tool
        
        # 更新类别索引
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        
        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)
        
        # 注册别名
        if aliases:
            for alias in aliases:
                if alias in self._tool_aliases:
                    logger.warning(f"⚠️ 别名 {alias} 已存在，跳过")
                    continue
                self._tool_aliases[alias] = tool.name
                logger.debug(f"🔗 已注册别名: {alias} -> {tool.name}")
        
        # 更新统计
        if old_tool is None:
            self._registry_stats["total_registrations"] += 1
        
        action = "覆盖" if old_tool else "注册"
        logger.info(f"✅ 工具{action}成功: {tool.name} ({tool.category.value})")
        
        return True
    
    def unregister_tool(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称或别名
            
        Returns:
            bool: 注销是否成功
        """
        # 解析真实工具名称
        real_name = self._resolve_tool_name(name)
        if not real_name:
            logger.warning(f"⚠️ 工具 {name} 不存在，无法注销")
            return False
        
        # 移除工具
        tool = self._tools.pop(real_name, None)
        if not tool:
            return False
        
        # 从类别索引中移除
        if tool.category in self._categories:
            try:
                self._categories[tool.category].remove(real_name)
                if not self._categories[tool.category]:
                    del self._categories[tool.category]
            except ValueError:
                pass
        
        # 移除别名
        aliases_to_remove = [alias for alias, target in self._tool_aliases.items() if target == real_name]
        for alias in aliases_to_remove:
            del self._tool_aliases[alias]
        
        # 从禁用列表移除
        self._disabled_tools.discard(real_name)
        
        # 更新统计
        self._registry_stats["total_unregistrations"] += 1
        
        logger.info(f"🗑️ 工具注销成功: {real_name}")
        return True
    
    def get_tool(self, name: str, enable_if_disabled: bool = False) -> Optional[BaseTool]:
        """
        获取指定名称的工具
        
        Args:
            name: 工具名称或别名
            enable_if_disabled: 如果工具被禁用，是否自动启用
            
        Returns:
            Optional[BaseTool]: 工具实例，如果不存在则返回None
        """
        real_name = self._resolve_tool_name(name)
        if not real_name:
            return None
        
        # 检查工具是否被禁用
        if real_name in self._disabled_tools:
            if enable_if_disabled:
                self.enable_tool(real_name)
                logger.info(f"🔓 工具已自动启用: {real_name}")
            else:
                logger.warning(f"⚠️ 工具 {real_name} 已被禁用")
                return None
        
        return self._tools.get(real_name)
    
    def execute_tool(self, name: str, *args, **kwargs) -> Optional[ToolResult]:
        """
        执行指定工具并记录统计信息
        
        Args:
            name: 工具名称或别名
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Optional[ToolResult]: 执行结果，如果工具不存在则返回None
        """
        tool = self.get_tool(name)
        if not tool:
            logger.error(f"❌ 工具 {name} 不存在或已禁用")
            return None
        
        try:
            # 记录执行开始
            start_time = time.time()
            logger.debug(f"🚀 开始执行工具: {tool.name}")
            
            # 执行工具
            result = tool.execute(*args, **kwargs)
            
            # 更新统计
            self._registry_stats["total_tool_executions"] += 1
            if not result.success:
                self._registry_stats["failed_executions"] += 1
            
            execution_time = time.time() - start_time
            logger.debug(f"✅ 工具执行完成: {tool.name}，耗时 {execution_time:.3f}秒")
            
            return result
            
        except Exception as e:
            self._registry_stats["failed_executions"] += 1
            logger.error(f"❌ 工具执行异常: {tool.name} - {e}")
            return ToolResult(
                success=False,
                error_message=f"工具执行异常: {e}",
                execution_time=time.time() - start_time
            )
    
    def get_tools_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """获取指定类别的所有工具"""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name not in self._disabled_tools]
    
    def list_all_tools(self, include_disabled: bool = False) -> List[str]:
        """
        列出所有已注册的工具名称
        
        Args:
            include_disabled: 是否包含已禁用的工具
            
        Returns:
            List[str]: 工具名称列表
        """
        if include_disabled:
            return list(self._tools.keys())
        else:
            return [name for name in self._tools.keys() if name not in self._disabled_tools]
    
    def search_tools(self, query: str, category: Optional[ToolCategory] = None) -> List[BaseTool]:
        """
        搜索工具（按名称或描述模糊匹配）
        
        Args:
            query: 搜索查询字符串
            category: 可选的类别过滤
            
        Returns:
            List[BaseTool]: 匹配的工具列表
        """
        query_lower = query.lower()
        results = []
        
        for name, tool in self._tools.items():
            # 跳过已禁用的工具
            if name in self._disabled_tools:
                continue
            
            # 类别过滤
            if category and tool.category != category:
                continue
            
            # 模糊匹配工具名称或描述
            if (query_lower in name.lower() or 
                query_lower in tool.description.lower()):
                results.append(tool)
        
        return results
    
    def disable_tool(self, name: str) -> bool:
        """
        禁用工具
        
        Args:
            name: 工具名称或别名
            
        Returns:
            bool: 禁用是否成功
        """
        real_name = self._resolve_tool_name(name)
        if not real_name:
            logger.warning(f"⚠️ 工具 {name} 不存在，无法禁用")
            return False
        
        self._disabled_tools.add(real_name)
        logger.info(f"🔒 工具已禁用: {real_name}")
        return True
    
    def enable_tool(self, name: str) -> bool:
        """
        启用工具
        
        Args:
            name: 工具名称或别名
            
        Returns:
            bool: 启用是否成功
        """
        real_name = self._resolve_tool_name(name)
        if not real_name:
            logger.warning(f"⚠️ 工具 {name} 不存在，无法启用")
            return False
        
        self._disabled_tools.discard(real_name)
        logger.info(f"🔓 工具已启用: {real_name}")
        return True
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具的详细信息
        
        Args:
            name: 工具名称或别名
            
        Returns:
            Optional[Dict]: 工具信息字典
        """
        tool = self.get_tool(name, enable_if_disabled=False)
        if not tool:
            return None
        
        real_name = self._resolve_tool_name(name)
        aliases = [alias for alias, target in self._tool_aliases.items() if target == real_name]
        
        return {
            "name": tool.name,
            "description": tool.description,
            "category": tool.category.value,
            "status": tool.status.value,
            "enabled": real_name not in self._disabled_tools,
            "aliases": aliases,
            "capabilities": {
                "supported_inputs": tool.capabilities.supported_inputs,
                "output_types": tool.capabilities.output_types,
                "async_support": tool.capabilities.async_support,
                "batch_support": tool.capabilities.batch_support,
                "requires_auth": tool.capabilities.requires_auth,
                "rate_limited": tool.capabilities.rate_limited
            },
            "usage": tool.get_usage_info()
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        uptime = time.time() - self._registry_stats["created_at"]
        
        return {
            **self._registry_stats,
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "total_tools": len(self._tools),
            "enabled_tools": len(self._tools) - len(self._disabled_tools),
            "disabled_tools": len(self._disabled_tools),
            "total_categories": len(self._categories),
            "total_aliases": len(self._tool_aliases),
            "categories": {cat.value: len(tools) for cat, tools in self._categories.items()},
            "success_rate": (
                (self._registry_stats["total_tool_executions"] - self._registry_stats["failed_executions"]) 
                / max(1, self._registry_stats["total_tool_executions"])
            )
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        执行健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        health_status = {
            "overall_status": "healthy",
            "total_tools": len(self._tools),
            "healthy_tools": 0,
            "unhealthy_tools": 0,
            "disabled_tools": len(self._disabled_tools),
            "tool_details": {}
        }
        
        for name, tool in self._tools.items():
            try:
                # 检查工具基本状态
                tool_health = {
                    "status": tool.status.value,
                    "enabled": name not in self._disabled_tools,
                    "usage_count": tool.usage_count,
                    "last_used": tool.last_used
                }
                
                if tool.status == ToolStatus.ERROR:
                    health_status["unhealthy_tools"] += 1
                    tool_health["health"] = "unhealthy"
                else:
                    health_status["healthy_tools"] += 1
                    tool_health["health"] = "healthy"
                
                health_status["tool_details"][name] = tool_health
                
            except Exception as e:
                health_status["unhealthy_tools"] += 1
                health_status["tool_details"][name] = {
                    "health": "error",
                    "error": str(e)
                }
        
        # 确定整体健康状态
        if health_status["unhealthy_tools"] > 0:
            health_status["overall_status"] = "degraded"
        
        if health_status["healthy_tools"] == 0:
            health_status["overall_status"] = "critical"
        
        return health_status
    
    def export_registry_config(self) -> Dict[str, Any]:
        """
        导出注册表配置（用于备份和恢复）
        
        Returns:
            Dict[str, Any]: 配置数据
        """
        return {
            "tools": {
                name: {
                    "class": tool.__class__.__name__,
                    "category": tool.category.value,
                    "enabled": name not in self._disabled_tools
                }
                for name, tool in self._tools.items()
            },
            "aliases": self._tool_aliases,
            "disabled_tools": list(self._disabled_tools),
            "export_time": time.time()
        }
    
    def _resolve_tool_name(self, name: str) -> Optional[str]:
        """解析工具真实名称（处理别名）"""
        if name in self._tools:
            return name
        return self._tool_aliases.get(name)
    
    def _validate_tool(self, tool: BaseTool) -> bool:
        """验证工具是否有效"""
        try:
            # 检查必要属性
            if not hasattr(tool, 'name') or not tool.name:
                logger.error(f"❌ 工具缺少有效名称")
                return False
            
            if not hasattr(tool, 'description') or not tool.description:
                logger.error(f"❌ 工具 {tool.name} 缺少描述")
                return False
            
            if not hasattr(tool, 'category'):
                logger.error(f"❌ 工具 {tool.name} 缺少类别")
                return False
            
            # 检查必要方法
            if not callable(getattr(tool, 'execute', None)):
                logger.error(f"❌ 工具 {tool.name} 缺少execute方法")
                return False
            
            if not hasattr(tool, 'capabilities'):
                logger.error(f"❌ 工具 {tool.name} 缺少capabilities属性")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 工具 {getattr(tool, 'name', 'unknown')} 验证异常: {e}")
            return False
    
    def __len__(self) -> int:
        """返回已注册工具的数量"""
        return len([name for name in self._tools.keys() if name not in self._disabled_tools])
    
    def __contains__(self, name: str) -> bool:
        """检查工具是否存在且已启用"""
        real_name = self._resolve_tool_name(name)
        return real_name is not None and real_name not in self._disabled_tools
    
    def __iter__(self):
        """迭代所有启用的工具"""
        for name, tool in self._tools.items():
            if name not in self._disabled_tools:
                yield tool


# 全局工具注册表实例
global_tool_registry = ToolRegistry()


def register_tool(tool: BaseTool, aliases: Optional[List[str]] = None, overwrite: bool = False) -> bool:
    """便捷函数：注册工具到全局注册表"""
    return global_tool_registry.register_tool(tool, aliases, overwrite)


def unregister_tool(name: str) -> bool:
    """便捷函数：从全局注册表注销工具"""
    return global_tool_registry.unregister_tool(name)


def get_tool(name: str, enable_if_disabled: bool = False) -> Optional[BaseTool]:
    """便捷函数：从全局注册表获取工具"""
    return global_tool_registry.get_tool(name, enable_if_disabled)


def execute_tool(name: str, *args, **kwargs) -> Optional[ToolResult]:
    """便捷函数：通过全局注册表执行工具"""
    return global_tool_registry.execute_tool(name, *args, **kwargs)


def list_available_tools(include_disabled: bool = False) -> List[str]:
    """便捷函数：列出所有可用工具"""
    return global_tool_registry.list_all_tools(include_disabled)


def search_tools(query: str, category: Optional[ToolCategory] = None) -> List[BaseTool]:
    """便捷函数：搜索工具"""
    return global_tool_registry.search_tools(query, category)


def get_tools_by_category(category: ToolCategory) -> List[BaseTool]:
    """便捷函数：按类别获取工具"""
    return global_tool_registry.get_tools_by_category(category)


def disable_tool(name: str) -> bool:
    """便捷函数：禁用工具"""
    return global_tool_registry.disable_tool(name)


def enable_tool(name: str) -> bool:
    """便捷函数：启用工具"""
    return global_tool_registry.enable_tool(name)


def get_tool_info(name: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取工具详细信息"""
    return global_tool_registry.get_tool_info(name)


def get_registry_stats() -> Dict[str, Any]:
    """便捷函数：获取注册表统计信息"""
    return global_tool_registry.get_registry_stats()


def health_check() -> Dict[str, Any]:
    """便捷函数：执行健康检查"""
    return global_tool_registry.health_check()


def export_registry_config() -> Dict[str, Any]:
    """便捷函数：导出注册表配置"""
    return global_tool_registry.export_registry_config()
