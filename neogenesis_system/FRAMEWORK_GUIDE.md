# Neogenesis框架架构指南

## 概述

Neogenesis框架是一个模块化的智能决策系统，通过定义通用数据结构和抽象接口，实现了高度可扩展和可定制的Agent架构。

## 核心设计理念

### 1. 模块化设计
框架采用"积木式"设计，每个组件都有明确的职责和标准接口，可以独立开发、测试和替换。

### 2. 契约式编程
通过抽象基类定义"合同"，确保所有实现都遵循相同的接口规范。

### 3. 数据驱动
使用标准化的数据结构在组件间传递信息，确保数据格式一致性。

## 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                          │
├─────────────────────────────────────────────────────────────┤
│                    BaseAgent                               │
│  ┌─────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │BasePlanner  │ │BaseToolExecutor │ │   BaseMemory    │  │
│  └─────────────┘ └─────────────────┘ └─────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                 Data Structures                            │
│     Action, Plan, Observation, ExecutionContext           │
└─────────────────────────────────────────────────────────────┘
```

## 核心数据结构

### Action (行动)
最基本的指令单元，代表一次工具调用。

```python
from neogenesis_system import Action

action = Action(
    tool_name="search",
    tool_input={"query": "人工智能"}
)
```

**关键属性:**
- `tool_name`: 要使用的工具名称
- `tool_input`: 工具输入参数
- `status`: 行动状态 (PENDING, EXECUTING, COMPLETED, FAILED)
- `execution_time`: 执行耗时

### Plan (计划)
规划器的输出，包含思考过程和行动序列。

```python
from neogenesis_system import Plan, Action

plan = Plan(
    thought="用户想了解AI，需要搜索相关信息",
    actions=[
        Action("search", {"query": "人工智能发展"})
    ]
)

# 或者直接回答
direct_plan = Plan(
    thought="这是简单问候，直接回答",
    final_answer="你好！有什么可以帮助您的吗？"
)
```

**关键属性:**
- `thought`: Agent的思考过程
- `actions`: 要执行的行动列表
- `final_answer`: 直接答案（无需工具时）
- `is_direct_answer`: 判断是否为直接回答

### Observation (观察)
执行行动后的结果记录。

```python
from neogenesis_system import Observation

observation = Observation(
    action=action,
    output="搜索找到了相关的AI信息...",
    success=True,
    execution_time=0.5
)
```

**关键属性:**
- `action`: 执行的行动
- `output`: 工具返回的结果
- `success`: 执行是否成功
- `error_message`: 错误信息（如果失败）

## 抽象接口

### BasePlanner (规划器接口)
负责分析用户查询并生成执行计划。

```python
from neogenesis_system import BasePlanner

class MyPlanner(BasePlanner):
    def create_plan(self, query: str, memory: Any, context=None) -> Plan:
        # 分析查询，生成计划
        return Plan(...)
    
    def validate_plan(self, plan: Plan) -> bool:
        # 验证计划有效性
        return True
```

**核心方法:**
- `create_plan()`: 创建执行计划（必须实现）
- `validate_plan()`: 验证计划有效性（必须实现）
- `estimate_complexity()`: 估算任务复杂度（可选）

### BaseToolExecutor (工具执行器接口)
负责执行计划中的工具调用。

```python
from neogenesis_system import BaseToolExecutor

class MyExecutor(BaseToolExecutor):
    def execute_plan(self, plan: Plan, context=None) -> List[Observation]:
        # 执行计划中的所有行动
        return observations
    
    def execute_action(self, action: Action) -> Observation:
        # 执行单个行动
        return observation
```

**核心方法:**
- `execute_plan()`: 执行完整计划（必须实现）
- `execute_action()`: 执行单个行动（必须实现）
- `register_tool()`: 注册可用工具（可选）

### BaseMemory (记忆模块接口)
负责存储和检索Agent的记忆。

```python
from neogenesis_system import BaseMemory

class MyMemory(BaseMemory):
    def store(self, key: str, value: Any, metadata=None) -> bool:
        # 存储信息
        return True
    
    def retrieve(self, key: str) -> Optional[Any]:
        # 检索信息
        return value
    
    def delete(self, key: str) -> bool:
        # 删除信息
        return True
    
    def exists(self, key: str) -> bool:
        # 检查是否存在
        return True
```

**核心方法:**
- `store()`: 存储信息（必须实现）
- `retrieve()`: 检索信息（必须实现）
- `delete()`: 删除信息（必须实现）
- `exists()`: 检查存在性（必须实现）

### BaseAgent (Agent接口)
顶层Agent抽象，协调所有组件。

```python
from neogenesis_system import BaseAgent

class MyAgent(BaseAgent):
    def run(self, query: str, context=None) -> str:
        # 1. 创建计划
        plan = self.plan_task(query, context)
        
        # 2. 执行计划
        if plan.is_direct_answer:
            return plan.final_answer
        
        observations = self.execute_plan(plan)
        
        # 3. 处理结果
        result = self.process_observations(observations)
        
        # 4. 存储记忆
        self.store_memory(f"task_{time.time()}", {
            "query": query,
            "result": result
        })
        
        return result
```

**核心方法:**
- `run()`: 主要处理入口（必须实现）
- `plan_task()`: 使用规划器创建计划
- `execute_plan()`: 使用执行器执行计划
- `store_memory()`: 存储到记忆模块

## 快速开始

### 1. 创建简单Agent

```python
from neogenesis_system import create_agent
from neogenesis_system.examples.framework_usage_example import (
    SimplePlanner, SimpleToolExecutor, SimpleMemory
)

# 使用工厂函数创建Agent
agent = create_agent(
    SimplePlanner, 
    SimpleToolExecutor, 
    SimpleMemory,
    agent_name="我的Agent"
)

# 运行查询
result = agent.run("搜索Python编程教程")
print(result)
```

### 2. 手动组装Agent

```python
from neogenesis_system import BasePlanner, BaseToolExecutor, BaseMemory, BaseAgent

# 创建组件
planner = SimplePlanner()
executor = SimpleToolExecutor()
memory = SimpleMemory()

# 创建自定义Agent
class MyAgent(BaseAgent):
    def run(self, query: str, context=None) -> str:
        # 自定义处理逻辑
        pass

agent = MyAgent(planner, executor, memory)
```

### 3. 扩展新功能

```python
# 添加新工具
class WeatherTool:
    def get_weather(self, city: str) -> str:
        return f"{city}今天晴天，20℃"

executor.register_tool("weather", WeatherTool())

# 扩展规划器支持天气查询
class WeatherPlanner(SimplePlanner):
    def create_plan(self, query: str, memory: Any, context=None) -> Plan:
        if "天气" in query:
            city = self.extract_city(query)
            return Plan(
                thought=f"用户询问{city}天气",
                actions=[Action("weather", {"city": city})]
            )
        return super().create_plan(query, memory, context)
```

## 异步支持

框架支持异步操作，适用于高并发场景：

```python
from neogenesis_system import BaseAsyncToolExecutor, BaseAsyncAgent

class AsyncAgent(BaseAsyncAgent):
    async def run_async(self, query: str, context=None) -> str:
        plan = self.plan_task(query, context)
        if plan.is_direct_answer:
            return plan.final_answer
        
        observations = await self.execute_plan_async(plan)
        return self.process_observations(observations)

# 使用异步Agent
import asyncio

async def main():
    result = await agent.run_async("搜索异步编程教程")
    print(result)

asyncio.run(main())
```

## 最佳实践

### 1. 错误处理
```python
def execute_action(self, action: Action) -> Observation:
    try:
        result = self.call_tool(action)
        return Observation(action, result, success=True)
    except Exception as e:
        return Observation(
            action, "", success=False, 
            error_message=str(e)
        )
```

### 2. 性能监控
```python
def run(self, query: str, context=None) -> str:
    start_time = time.time()
    try:
        result = self.process_query(query)
        self.update_stats(True, time.time() - start_time, 1)
        return result
    except Exception as e:
        self.update_stats(False, time.time() - start_time, 0)
        raise
```

### 3. 记忆管理
```python
def store_conversation(self, query: str, result: str):
    self.store_memory(
        f"conv_{int(time.time())}", 
        {"query": query, "result": result},
        metadata={"type": "conversation", "timestamp": time.time()}
    )
```

## 与现有系统集成

框架设计为与现有的Neogenesis Meta MAB系统无缝集成：

```python
# 使用现有的MAB组件作为规划器
from neogenesis_system.meta_mab import MainController

class MABPlanner(BasePlanner):
    def __init__(self, api_key: str):
        super().__init__("MABPlanner", "基于Meta MAB的智能规划器")
        self.controller = MainController(api_key)
    
    def create_plan(self, query: str, memory: Any, context=None) -> Plan:
        # 使用MAB决策
        decision = self.controller.make_decision(query)
        # 转换为标准Plan格式
        return self.convert_to_plan(decision)
```

## 总结

Neogenesis框架通过统一的数据结构和抽象接口，提供了：

- **模块化**: 组件可独立开发和替换
- **可扩展**: 轻松添加新工具和功能
- **标准化**: 统一的数据格式和接口
- **灵活性**: 支持同步和异步操作
- **兼容性**: 与现有系统无缝集成

这个架构使得开发者可以专注于业务逻辑，而不用担心组件间的协调问题。
