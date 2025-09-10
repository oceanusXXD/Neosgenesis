"""
Neogenesis System API 数据模型

定义 FastAPI 接口使用的 Pydantic 数据模型，包括请求和响应结构。
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field, validator


# ==================== 基础模型 ====================

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="操作是否成功")
    timestamp: datetime = Field(..., description="响应时间戳")
    message: Optional[str] = Field(None, description="响应消息")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


# ==================== 健康检查和系统状态 ====================

class HealthResponse(BaseResponse):
    """健康检查响应"""
    status: str = Field(..., description="系统状态: healthy, degraded, unhealthy")
    components: Dict[str, bool] = Field(default_factory=dict, description="各组件状态")
    core_available: bool = Field(..., description="核心组件是否可用")


class SystemStatusResponse(BaseResponse):
    """系统状态响应"""
    status: str = Field(..., description="系统运行状态")
    system_info: Dict[str, Any] = Field(..., description="系统详细信息")


# ==================== 规划相关模型 ====================

class PlanningRequest(BaseModel):
    """规划请求模型"""
    query: str = Field(..., min_length=1, max_length=1000, description="规划查询内容")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    priority: int = Field(1, ge=1, le=10, description="优先级 (1-10)")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('查询内容不能为空')
        return v.strip()


class ActionModel(BaseModel):
    """行动模型"""
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    description: Optional[str] = Field(None, description="行动描述")


class PlanModel(BaseModel):
    """计划模型"""
    plan_id: str = Field(..., description="计划ID")
    query: str = Field(..., description="原始查询")
    actions: List[ActionModel] = Field(..., description="行动列表")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    estimated_duration: Optional[int] = Field(None, description="预估执行时间(秒)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")


class PlanningResponse(BaseResponse):
    """规划响应模型"""
    plan: Optional[PlanModel] = Field(None, description="生成的计划")


# ==================== 认知处理模型 ====================

class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CognitiveRequest(BaseModel):
    """认知处理请求模型"""
    task: str = Field(..., min_length=1, max_length=2000, description="认知任务描述")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="任务优先级")
    context: Optional[Dict[str, Any]] = Field(None, description="任务上下文")
    timeout: Optional[int] = Field(30, ge=1, le=300, description="超时时间(秒)")
    
    @validator('task')
    def validate_task(cls, v):
        if not v.strip():
            raise ValueError('任务描述不能为空')
        return v.strip()


class CognitiveResult(BaseModel):
    """认知处理结果"""
    task_id: str = Field(..., description="任务ID")
    result: Any = Field(..., description="处理结果")
    confidence: float = Field(..., ge=0.0, le=1.0, description="结果置信度")
    processing_time: float = Field(..., description="处理耗时(秒)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="结果元数据")


class CognitiveResponse(BaseResponse):
    """认知处理响应模型"""
    result: Optional[CognitiveResult] = Field(None, description="认知处理结果")


# ==================== 知识搜索模型 ====================

class KnowledgeSearchRequest(BaseModel):
    """知识搜索请求模型"""
    query: str = Field(..., min_length=1, max_length=500, description="搜索查询")
    limit: Optional[int] = Field(10, ge=1, le=100, description="结果数量限制")
    filters: Optional[Dict[str, Any]] = Field(None, description="搜索过滤器")
    include_metadata: bool = Field(True, description="是否包含元数据")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('搜索查询不能为空')
        return v.strip()


class KnowledgeItem(BaseModel):
    """知识项模型"""
    id: str = Field(..., description="知识项ID")
    title: str = Field(..., description="知识项标题")
    content: str = Field(..., description="知识项内容")
    source: Optional[str] = Field(None, description="知识来源")
    confidence: float = Field(..., ge=0.0, le=1.0, description="相关度评分")
    metadata: Optional[Dict[str, Any]] = Field(None, description="知识项元数据")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class KnowledgeSearchResponse(BaseResponse):
    """知识搜索响应模型"""
    results: List[KnowledgeItem] = Field(default_factory=list, description="搜索结果")
    total_results: int = Field(0, description="总结果数")
    query_time: Optional[float] = Field(None, description="查询耗时(秒)")


# ==================== 回顾和学习模型 ====================

class RetrospectionRequest(BaseModel):
    """回顾请求模型"""
    session_id: str = Field(..., description="会话ID")
    include_performance: bool = Field(True, description="是否包含性能分析")
    include_improvements: bool = Field(True, description="是否包含改进建议")


class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    total_tasks: int = Field(..., description="总任务数")
    successful_tasks: int = Field(..., description="成功任务数")
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="平均置信度")
    average_response_time: float = Field(..., description="平均响应时间(秒)")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="错误率")


class ImprovementSuggestion(BaseModel):
    """改进建议模型"""
    category: str = Field(..., description="改进类别")
    description: str = Field(..., description="改进描述")
    priority: int = Field(..., ge=1, le=10, description="优先级")
    expected_impact: str = Field(..., description="预期影响")


class RetrospectionResult(BaseModel):
    """回顾结果模型"""
    session_id: str = Field(..., description="会话ID")
    performance_metrics: Optional[PerformanceMetrics] = Field(None, description="性能指标")
    improvements: List[ImprovementSuggestion] = Field(default_factory=list, description="改进建议")
    summary: str = Field(..., description="回顾总结")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")


class RetrospectionResponse(BaseResponse):
    """回顾响应模型"""
    result: Optional[RetrospectionResult] = Field(None, description="回顾结果")


# ==================== 配置和设置模型 ====================

class ConfigurationRequest(BaseModel):
    """配置请求模型"""
    component: str = Field(..., description="要配置的组件名称")
    settings: Dict[str, Any] = Field(..., description="配置设置")
    apply_immediately: bool = Field(True, description="是否立即应用配置")


class ConfigurationResponse(BaseResponse):
    """配置响应模型"""
    component: str = Field(..., description="配置的组件名称")
    applied_settings: Dict[str, Any] = Field(..., description="已应用的设置")
    restart_required: bool = Field(False, description="是否需要重启")


# ==================== 批量操作模型 ====================

class BatchRequest(BaseModel):
    """批量请求模型"""
    requests: List[Union[PlanningRequest, CognitiveRequest, KnowledgeSearchRequest]] = Field(
        ..., description="批量请求列表"
    )
    parallel: bool = Field(True, description="是否并行处理")
    fail_fast: bool = Field(False, description="是否快速失败")


class BatchResult(BaseModel):
    """批量结果项"""
    index: int = Field(..., description="请求索引")
    success: bool = Field(..., description="是否成功")
    result: Optional[Any] = Field(None, description="结果数据")
    error: Optional[str] = Field(None, description="错误信息")


class BatchResponse(BaseResponse):
    """批量响应模型"""
    results: List[BatchResult] = Field(..., description="批量结果列表")
    total_requests: int = Field(..., description="总请求数")
    successful_requests: int = Field(..., description="成功请求数")
    failed_requests: int = Field(..., description="失败请求数")


# ==================== 实用工具函数 ====================

def create_error_response(error_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> ErrorResponse:
    """创建错误响应的便利函数"""
    return ErrorResponse(
        error=error_type,
        message=message,
        details=details or {}
    )


def create_success_response(data: Optional[Any] = None, message: str = "操作成功") -> BaseResponse:
    """创建成功响应的便利函数"""
    return BaseResponse(
        success=True,
        timestamp=datetime.utcnow(),
        message=message
    )


# ==================== 模型导出 ====================

__all__ = [
    # 基础模型
    "BaseResponse",
    "ErrorResponse",
    
    # 健康检查和系统状态
    "HealthResponse", 
    "SystemStatusResponse",
    
    # 规划相关
    "PlanningRequest",
    "PlanningResponse", 
    "ActionModel",
    "PlanModel",
    
    # 认知处理
    "TaskPriority",
    "CognitiveRequest",
    "CognitiveResponse",
    "CognitiveResult",
    
    # 知识搜索
    "KnowledgeSearchRequest",
    "KnowledgeSearchResponse",
    "KnowledgeItem",
    
    # 回顾和学习
    "RetrospectionRequest",
    "RetrospectionResponse",
    "RetrospectionResult",
    "PerformanceMetrics",
    "ImprovementSuggestion",
    
    # 配置
    "ConfigurationRequest",
    "ConfigurationResponse",
    
    # 批量操作
    "BatchRequest",
    "BatchResponse", 
    "BatchResult",
    
    # 工具函数
    "create_error_response",
    "create_success_response",
]
