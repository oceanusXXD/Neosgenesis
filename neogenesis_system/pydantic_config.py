#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 Pydantic配置管理系统 - 强化的配置管理
Enhanced Configuration Management with Pydantic

特性:
- 自动数据类型验证和转换
- 环境变量自动加载
- 配置项嵌套和继承
- IDE智能提示支持
- 配置验证和错误报告
- 默认值管理
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

try:
    from pydantic import BaseModel, Field, validator, root_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    # 如果pydantic不可用，提供基本的兼容类
    PYDANTIC_AVAILABLE = False
    
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class BaseSettings(BaseModel):
        pass
    
    def Field(default=None, **kwargs):
        return default
    
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def root_validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class SettingsConfigDict:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)


# ==================== 🔧 LLM配置 ====================

class LLMProviderConfig(BaseSettings):
    """LLM提供商配置"""
    model_config = SettingsConfigDict(
        env_prefix="NEOGENESIS_LLM_",
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )
    
    # 基础配置
    api_key: str = Field(
        default="",
        description="API密钥",
        min_length=1
    )
    
    base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="API基础URL"
    )
    
    model_name: str = Field(
        default="deepseek-chat",
        description="模型名称"
    )
    
    # 请求配置
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="生成温度"
    )
    
    max_tokens: int = Field(
        default=2000,
        gt=0,
        le=32000,
        description="最大令牌数"
    )
    
    timeout: float = Field(
        default=60.0,
        gt=0,
        description="请求超时时间（秒）"
    )
    
    # 重试配置
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="最大重试次数"
    )
    
    retry_delay_base: float = Field(
        default=2.0,
        gt=0,
        description="重试延迟基数"
    )
    
    request_interval: float = Field(
        default=1.0,
        ge=0,
        description="请求间隔时间（秒）"
    )
    
    # 缓存配置
    enable_cache: bool = Field(
        default=True,
        description="启用缓存"
    )
    
    cache_ttl: int = Field(
        default=3600,
        gt=0,
        description="缓存TTL（秒）"
    )
    
    # 代理配置
    proxies: Optional[Dict[str, str]] = Field(
        default=None,
        description="代理配置"
    )
    
    @validator('api_key')
    def validate_api_key(cls, v):
        """验证API密钥"""
        if not v or v.strip() == "":
            # 尝试从环境变量加载
            env_keys = [
                'DEEPSEEK_API_KEY',
                'OPENAI_API_KEY', 
                'ANTHROPIC_API_KEY',
                'NEOGENESIS_API_KEY'
            ]
            for key in env_keys:
                env_value = os.getenv(key)
                if env_value:
                    logger.info(f"✅ 从环境变量 {key} 加载API密钥")
                    return env_value.strip()
            
            logger.warning("⚠️ 未设置API密钥，某些功能可能不可用")
        return v.strip() if v else ""
    
    @validator('proxies', pre=True)
    def validate_proxies(cls, v):
        """验证代理配置"""
        if v is None:
            return {'http': None, 'https': None}
        if isinstance(v, dict):
            return v
        return {'http': None, 'https': None}


class DeepSeekConfig(LLMProviderConfig):
    """DeepSeek专用配置"""
    model_config = SettingsConfigDict(
        env_prefix="DEEPSEEK_",
        env_file=".env",
        case_sensitive=False
    )
    
    model_name: str = Field(default="deepseek-chat")
    base_url: str = Field(default="https://api.deepseek.com/v1")


class OpenAIConfig(LLMProviderConfig):
    """OpenAI专用配置"""
    model_config = SettingsConfigDict(
        env_prefix="OPENAI_",
        env_file=".env",
        case_sensitive=False
    )
    
    model_name: str = Field(default="gpt-3.5-turbo")
    base_url: str = Field(default="https://api.openai.com/v1")


# ==================== 🎯 MAB算法配置 ====================

class MABConfig(BaseSettings):
    """多臂老虎机算法配置"""
    model_config = SettingsConfigDict(
        env_prefix="MAB_",
        env_file=".env",
        case_sensitive=False
    )
    
    convergence_threshold: float = Field(
        default=0.05,
        ge=0.001,
        le=0.5,
        description="收敛阈值"
    )
    
    min_samples: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="最小样本数"
    )
    
    base_exploration_rate: float = Field(
        default=0.1,
        ge=0.01,
        le=1.0,
        description="基础探索率"
    )
    
    exploration_decay: float = Field(
        default=0.99,
        ge=0.9,
        le=1.0,
        description="探索率衰减"
    )
    
    min_exploration_rate: float = Field(
        default=0.05,
        ge=0.001,
        le=0.2,
        description="最小探索率"
    )
    
    # 工具选择特定配置
    tool_selection_enabled: bool = Field(
        default=True,
        description="启用工具选择MAB"
    )
    
    tool_convergence_threshold: float = Field(
        default=0.3,
        ge=0.1,
        le=1.0,
        description="工具选择收敛阈值"
    )


# ==================== 🏗️ 系统配置 ====================

class SystemLimitsConfig(BaseSettings):
    """系统限制配置"""
    model_config = SettingsConfigDict(
        env_prefix="SYSTEM_",
        env_file=".env",
        case_sensitive=False
    )
    
    max_decision_history: int = Field(
        default=1000,
        gt=0,
        description="最大决策历史记录数"
    )
    
    max_performance_history: int = Field(
        default=50,
        gt=0,
        description="最大性能历史记录数"
    )
    
    max_concurrent_requests: int = Field(
        default=5,
        ge=1,
        le=50,
        description="最大并发请求数"
    )
    
    max_memory_usage: int = Field(
        default=512,
        ge=128,
        le=4096,
        description="最大内存使用量（MB）"
    )
    
    session_timeout: int = Field(
        default=3600,
        ge=300,
        description="会话超时时间（秒）"
    )


class FeatureFlagsConfig(BaseSettings):
    """功能开关配置"""
    model_config = SettingsConfigDict(
        env_prefix="FEATURE_",
        env_file=".env",
        case_sensitive=False
    )
    
    enable_performance_optimization: bool = Field(
        default=False,
        description="启用性能优化"
    )
    
    enable_advanced_reasoning: bool = Field(
        default=True,
        description="启用高级推理"
    )
    
    enable_caching: bool = Field(
        default=True,
        description="启用缓存"
    )
    
    enable_metrics: bool = Field(
        default=True,
        description="启用性能指标"
    )
    
    enable_debug_logging: bool = Field(
        default=False,
        description="启用调试日志"
    )
    
    enable_async_mode: bool = Field(
        default=True,
        description="启用异步模式"
    )
    
    enable_state_manager: bool = Field(
        default=True,
        description="启用状态管理器"
    )


class PerformanceConfig(BaseSettings):
    """性能优化配置"""
    model_config = SettingsConfigDict(
        env_prefix="PERF_",
        env_file=".env",
        case_sensitive=False
    )
    
    connection_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="连接池大小"
    )
    
    request_timeout: float = Field(
        default=30.0,
        gt=0,
        description="请求超时时间"
    )
    
    parallel_verification_workers: int = Field(
        default=3,
        ge=1,
        le=20,
        description="并行验证工作线程数"
    )
    
    cache_size: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="缓存大小"
    )
    
    enable_keep_alive: bool = Field(
        default=True,
        description="启用连接保持"
    )


# ==================== 🌍 主配置类 ====================

class NeogenesisConfig(BaseSettings):
    """Neogenesis系统主配置"""
    model_config = SettingsConfigDict(
        env_prefix="NEOGENESIS_",
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )
    
    # 系统基础配置
    environment: str = Field(
        default="development",
        description="运行环境"
    )
    
    debug: bool = Field(
        default=False,
        description="调试模式"
    )
    
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )
    
    # 子配置
    llm: LLMProviderConfig = Field(default_factory=LLMProviderConfig)
    deepseek: DeepSeekConfig = Field(default_factory=DeepSeekConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    mab: MABConfig = Field(default_factory=MABConfig)
    system_limits: SystemLimitsConfig = Field(default_factory=SystemLimitsConfig)
    features: FeatureFlagsConfig = Field(default_factory=FeatureFlagsConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    @root_validator
    def validate_config(cls, values):
        """根级别配置验证"""
        # 验证环境配置
        env = values.get('environment', 'development')
        if env == 'production' and values.get('debug', False):
            logger.warning("⚠️ 生产环境不建议启用调试模式")
        
        # 验证日志级别
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        log_level = values.get('log_level', 'INFO').upper()
        if log_level not in valid_levels:
            values['log_level'] = 'INFO'
            logger.warning(f"⚠️ 无效的日志级别，已重置为INFO")
        
        return values
    
    def get_llm_config(self, provider: str = "deepseek") -> LLMProviderConfig:
        """获取特定LLM提供商配置"""
        if provider.lower() == "deepseek":
            return self.deepseek
        elif provider.lower() == "openai":
            return self.openai
        else:
            return self.llm
    
    def to_legacy_dict(self) -> Dict[str, Any]:
        """转换为传统字典格式（向后兼容）"""
        return {
            "API_CONFIG": {
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "timeout": self.llm.timeout,
                "max_retries": self.llm.max_retries,
                "retry_delay_base": self.llm.retry_delay_base,
                "proxies": self.llm.proxies,
                "request_interval": self.llm.request_interval,
                "enable_cache": self.llm.enable_cache,
            },
            "MAB_CONFIG": {
                "convergence_threshold": self.mab.convergence_threshold,
                "min_samples": self.mab.min_samples,
                "base_exploration_rate": self.mab.base_exploration_rate,
                "exploration_decay": self.mab.exploration_decay,
                "min_exploration_rate": self.mab.min_exploration_rate,
            },
            "SYSTEM_LIMITS": {
                "max_decision_history": self.system_limits.max_decision_history,
                "max_performance_history": self.system_limits.max_performance_history,
                "max_concurrent_requests": self.system_limits.max_concurrent_requests,
                "max_memory_usage": self.system_limits.max_memory_usage,
                "session_timeout": self.system_limits.session_timeout,
            },
            "FEATURE_FLAGS": {
                "enable_performance_optimization": self.features.enable_performance_optimization,
                "enable_advanced_reasoning": self.features.enable_advanced_reasoning,
                "enable_caching": self.features.enable_caching,
                "enable_metrics": self.features.enable_metrics,
                "enable_debug_logging": self.features.enable_debug_logging,
                "enable_async_mode": self.features.enable_async_mode,
                "enable_state_manager": self.features.enable_state_manager,
            },
            "PERFORMANCE_CONFIG": {
                "connection_pool_size": self.performance.connection_pool_size,
                "request_timeout": self.performance.request_timeout,
                "parallel_verification_workers": self.performance.parallel_verification_workers,
                "cache_size": self.performance.cache_size,
                "enable_keep_alive": self.performance.enable_keep_alive,
            }
        }


# ==================== 🚀 配置管理器 ====================

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self._config: Optional[NeogenesisConfig] = None
        self._initialized = False
    
    def load_config(self, config_file: Optional[str] = None) -> NeogenesisConfig:
        """加载配置"""
        if not PYDANTIC_AVAILABLE:
            logger.warning("⚠️ Pydantic未安装，使用基本配置模式")
            return self._create_basic_config()
        
        try:
            # 设置环境文件路径
            if config_file:
                os.environ.setdefault('NEOGENESIS_ENV_FILE', config_file)
            
            self._config = NeogenesisConfig()
            self._initialized = True
            
            logger.info("✅ Pydantic配置系统初始化成功")
            logger.debug(f"📋 环境: {self._config.environment}")
            logger.debug(f"🔧 调试模式: {self._config.debug}")
            logger.debug(f"📊 异步模式: {self._config.features.enable_async_mode}")
            
            return self._config
            
        except Exception as e:
            logger.error(f"❌ 配置加载失败: {e}")
            return self._create_basic_config()
    
    def _create_basic_config(self) -> NeogenesisConfig:
        """创建基本配置（fallback）"""
        logger.info("🔧 使用基本配置模式")
        # 返回带有默认值的配置
        return NeogenesisConfig()
    
    @property
    def config(self) -> NeogenesisConfig:
        """获取当前配置"""
        if not self._initialized:
            self.load_config()
        return self._config
    
    def reload_config(self, config_file: Optional[str] = None) -> NeogenesisConfig:
        """重新加载配置"""
        self._initialized = False
        return self.load_config(config_file)
    
    def validate_config(self) -> bool:
        """验证配置"""
        try:
            config = self.config
            
            # 基本验证
            if not config.llm.api_key:
                logger.warning("⚠️ 未设置API密钥")
                return False
            
            if config.llm.timeout <= 0:
                logger.error("❌ 超时时间必须大于0")
                return False
            
            if config.mab.convergence_threshold <= 0:
                logger.error("❌ MAB收敛阈值必须大于0")
                return False
            
            logger.info("✅ 配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置验证失败: {e}")
            return False


# ==================== 全局配置实例 ====================

# 全局配置管理器
config_manager = ConfigManager()

def get_config() -> NeogenesisConfig:
    """获取全局配置"""
    return config_manager.config

def reload_config(config_file: Optional[str] = None) -> NeogenesisConfig:
    """重新加载全局配置"""
    return config_manager.reload_config(config_file)

def validate_config() -> bool:
    """验证全局配置"""
    return config_manager.validate_config()


# ==================== 便捷访问函数 ====================

def get_llm_config(provider: str = "deepseek") -> LLMProviderConfig:
    """获取LLM配置"""
    return get_config().get_llm_config(provider)

def get_mab_config() -> MABConfig:
    """获取MAB配置"""
    return get_config().mab

def get_system_limits() -> SystemLimitsConfig:
    """获取系统限制配置"""
    return get_config().system_limits

def get_feature_flags() -> FeatureFlagsConfig:
    """获取功能开关配置"""
    return get_config().features

def get_performance_config() -> PerformanceConfig:
    """获取性能配置"""
    return get_config().performance

def is_debug_mode() -> bool:
    """是否为调试模式"""
    return get_config().debug

def is_async_mode_enabled() -> bool:
    """是否启用异步模式"""
    return get_config().features.enable_async_mode


if __name__ == "__main__":
    # 测试配置系统
    print("🔧 测试Pydantic配置系统")
    
    config = get_config()
    print(f"✅ 配置加载成功")
    print(f"🔑 API Key存在: {'是' if config.llm.api_key else '否'}")
    print(f"🌡️ 温度: {config.llm.temperature}")
    print(f"🔢 最大Token: {config.llm.max_tokens}")
    print(f"🎯 MAB收敛阈值: {config.mab.convergence_threshold}")
    print(f"🚀 异步模式: {'启用' if config.features.enable_async_mode else '禁用'}")
    
    # 验证配置
    if validate_config():
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败")
