
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
轻量级分析助手 - 专注于快速任务评估和复杂度分析
Lightweight Analysis Assistant - focused on rapid task assessment and complexity analysis

核心职责：
1. 任务复杂度分析 (快速启发式方法)
2. 任务置信度评估 (基于历史数据和模式)
3. 领域推断和统计分析 (辅助决策支持)

注意：思维种子生成功能已移交给RAGSeedGenerator专门处理
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 注意：不再导入DeepSeekClientAdapter，专注于轻量级启发式分析

logger = logging.getLogger(__name__)


@dataclass  
class PriorReasoner:
    """轻量级分析助手 - 专注于快速任务评估和复杂度分析"""
    
    def __init__(self, api_key: str = ""):
        """
        初始化轻量级分析助手
        
        注意：不再需要API调用器，专注于快速启发式分析
        
        Args:
            api_key: 保留用于向后兼容，但不再使用
        """
        self.api_key = api_key  # 保留用于向后兼容
        self.assessment_cache = {}  # 评估缓存
        self.confidence_history = []  # 置信度历史
        
        logger.info("🧠 PriorReasoner 已初始化 (轻量级分析助手模式 - 专注于快速评估)")
        
    def assess_task_confidence(self, user_query: str, execution_context: Optional[Dict] = None) -> float:
        """
        评估任务的置信度
        
        Args:
            user_query: 用户查询
            execution_context: 执行上下文
            
        Returns:
            置信度分数 (0.0-1.0)
        """
        # 检查缓存
        cache_key = f"{user_query}_{hash(str(execution_context))}"
        if cache_key in self.assessment_cache:
            logger.debug(f"📋 使用缓存的置信度评估: {cache_key}")
            return self.assessment_cache[cache_key]
        
        # 基于查询复杂度的评估
        base_confidence = 0.7
        
        # 查询长度影响
        query_length = len(user_query)
        if query_length < 20:
            base_confidence += 0.1
        elif query_length > 100:
            base_confidence -= 0.1
        elif query_length > 200:
            base_confidence -= 0.2
            
        # 技术术语检测
        tech_terms = [
            'API', 'api', '算法', '数据库', '系统', '架构', '优化',
            '机器学习', 'ML', 'AI', '人工智能', '深度学习',
            '网络', '爬虫', '数据分析', '实时', '性能'
        ]
        tech_count = sum(1 for term in tech_terms if term in user_query)
        if tech_count > 0:
            base_confidence += min(0.15, tech_count * 0.05)
        
        # 复杂度关键词检测
        complexity_indicators = [
            '复杂', '困难', '挑战', '高级', '专业',
            '多步骤', '分布式', '并发', '异步', '集成'
        ]
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in user_query)
        if complexity_count > 0:
            base_confidence -= min(0.2, complexity_count * 0.05)
        
        # 明确性关键词检测
        clarity_indicators = [
            '简单', '直接', '基础', '快速', '标准',
            '帮助', '请', '如何', '怎么', '什么'
        ]
        clarity_count = sum(1 for indicator in clarity_indicators if indicator in user_query)
        if clarity_count > 0:
            base_confidence += min(0.1, clarity_count * 0.03)
        
        # 执行上下文影响
        if execution_context:
            context_factors = len(execution_context)
            if context_factors > 3:
                base_confidence += 0.05  # 更多上下文信息提高置信度
            
            # 实时性要求
            if execution_context.get('real_time_requirements'):
                base_confidence -= 0.05
            
            # 性能要求
            if execution_context.get('performance_critical'):
                base_confidence -= 0.03
        
        # 限制在合理范围内
        final_confidence = min(1.0, max(0.2, base_confidence))
        
        # 缓存结果
        self.assessment_cache[cache_key] = final_confidence
        
        # 限制缓存大小
        if len(self.assessment_cache) > 100:
            # 移除最旧的缓存项
            oldest_key = next(iter(self.assessment_cache))
            del self.assessment_cache[oldest_key]
        
        logger.info(f"📊 任务置信度评估: {final_confidence:.3f} (查询长度:{query_length}, 技术词汇:{tech_count})")
        return final_confidence
    
    def get_thinking_seed(self, user_query: str, execution_context: Optional[Dict] = None) -> str:
        """
        生成思维种子 - 兼容性适配器方法
        
        注意：此方法现在基于轻量级分析功能重新实现，保持与原有接口的兼容性
        
        Args:
            user_query: 用户查询
            execution_context: 执行上下文
            
        Returns:
            基于快速分析生成的思维种子
        """
        logger.info(f"🔄 使用轻量级分析生成思维种子: {user_query[:30]}...")
        
        try:
            # 使用新的快速分析功能生成思维种子
            analysis = self.get_quick_analysis_summary(user_query, execution_context)
            
            # 构建结构化的思维种子
            seed_parts = []
            
            # 问题理解部分
            seed_parts.append(f"这是一个{analysis['domain']}领域的任务。")
            
            # 复杂度分析
            complexity = analysis['complexity_score']
            if complexity > 0.8:
                seed_parts.append("任务具有高复杂度，需要系统性和多步骤的解决方案。")
            elif complexity > 0.5:
                seed_parts.append("任务复杂度适中，需要结构化的分析方法。")
            else:
                seed_parts.append("任务相对简单，可以采用直接的解决方法。")
            
            # 置信度考虑
            confidence = analysis['confidence_score']
            if confidence > 0.8:
                seed_parts.append("基于问题描述，我们有较高的信心找到有效解决方案。")
            elif confidence > 0.5:
                seed_parts.append("问题需要进一步分析以确定最佳方法。")
            else:
                seed_parts.append("问题可能需要额外信息或澄清来制定有效方案。")
            
            # 关键因素
            if analysis['key_factors']:
                factors_text = "、".join(analysis['key_factors'][:3])
                seed_parts.append(f"关键考虑因素包括：{factors_text}。")
            
            # 推荐策略
            seed_parts.append(f"建议采用的策略：{analysis['recommendation']}")
            
            # 多步骤检测
            if analysis['requires_multi_step']:
                seed_parts.append("这是一个多阶段任务，需要按步骤逐一执行。")
            
            # 执行上下文考虑
            if execution_context:
                if execution_context.get('real_time_requirements'):
                    seed_parts.append("需要特别注意实时性要求。")
                if execution_context.get('performance_critical'):
                    seed_parts.append("性能优化是关键考虑因素。")
            
            thinking_seed = " ".join(seed_parts)
            
            logger.info(f"✅ 思维种子生成完成 (长度: {len(thinking_seed)}字符)")
            logger.debug(f"🌱 种子内容: {thinking_seed[:100]}...")
            
            return thinking_seed
            
        except Exception as e:
            logger.error(f"⚠️ 轻量级思维种子生成失败: {e}")
            
            # 最终回退：使用基础分析生成简单种子
            try:
                complexity_info = self.analyze_task_complexity(user_query)
                confidence_score = self.assess_task_confidence(user_query, execution_context)
                
                fallback_seed = (
                    f"这是一个关于'{user_query}'的{complexity_info['estimated_domain']}任务。"
                    f"复杂度评估为{complexity_info['complexity_score']:.2f}，"
                    f"置信度为{confidence_score:.2f}。"
                    f"建议采用系统性的方法来分析和解决这个问题。"
                )
                
                logger.info(f"🔧 使用回退种子生成 (长度: {len(fallback_seed)}字符)")
                return fallback_seed
                
            except Exception as fallback_error:
                logger.error(f"⚠️ 回退种子生成也失败: {fallback_error}")
                
                # 绝对最终回退
                default_seed = (
                    f"针对'{user_query}'这个任务，需要进行系统性的分析。"
                    f"建议首先理解问题的核心需求，然后制定分步骤的解决方案，"
                    f"最后验证方案的可行性和有效性。"
                )
                
                logger.info("🔧 使用默认通用种子")
                return default_seed
    
    def analyze_task_complexity(self, user_query: str) -> Dict[str, Any]:
        """
        分析任务复杂度
        
        Args:
            user_query: 用户查询
            
        Returns:
            复杂度分析结果
        """
        complexity_score = 0.5
        complexity_factors = {}
        
        # 关键词复杂度指标
        complexity_keywords = {
            '多步骤': 0.15,
            '集成': 0.12,
            '优化': 0.10,
            '分析': 0.08,
            '设计': 0.08,
            '架构': 0.12,
            '分布式': 0.15,
            '并发': 0.13,
            '实时': 0.10,
            '高性能': 0.11,
            '机器学习': 0.14,
            '深度学习': 0.16,
            '算法': 0.09,
            '数据库': 0.07,
            '网络': 0.06,
            '安全': 0.08
        }
        
        for keyword, weight in complexity_keywords.items():
            if keyword in user_query:
                complexity_score += weight
                complexity_factors[keyword] = weight
                logger.debug(f"🔍 检测到复杂度关键词: {keyword} (+{weight})")
        
        # 句法复杂度
        sentences = user_query.split('。')
        if len(sentences) > 3:
            syntax_complexity = min(0.1, (len(sentences) - 3) * 0.02)
            complexity_score += syntax_complexity
            complexity_factors['多句表达'] = syntax_complexity
        
        # 字符长度复杂度
        if len(user_query) > 150:
            length_complexity = min(0.08, (len(user_query) - 150) / 1000)
            complexity_score += length_complexity
            complexity_factors['表达长度'] = length_complexity
        
        # 技术词汇密度
        tech_words = ['API', 'HTTP', 'JSON', 'SQL', 'Python', 'JavaScript', 'REST', 'GraphQL']
        tech_density = sum(1 for word in tech_words if word in user_query) / max(len(user_query.split()), 1)
        if tech_density > 0.1:
            tech_complexity = min(0.12, tech_density * 2)
            complexity_score += tech_complexity
            complexity_factors['技术词汇密度'] = tech_complexity
        
        # 领域推断
        domain = self._infer_domain(user_query)
        
        # 多步骤检测
        requires_multi_step = any(word in user_query for word in [
            '步骤', '阶段', '分步', '然后', '接下来', '首先', '最后',
            '第一', '第二', '第三', '依次', '顺序'
        ])
        
        # 限制复杂度分数
        final_complexity = min(1.0, complexity_score)
        
        result = {
            'complexity_score': final_complexity,
            'complexity_factors': complexity_factors,
            'estimated_domain': domain,
            'requires_multi_step': requires_multi_step,
            'sentence_count': len(sentences),
            'word_count': len(user_query.split()),
            'tech_density': tech_density
        }
        
        logger.info(f"🧮 复杂度分析完成: {final_complexity:.3f} (因子数:{len(complexity_factors)})")
        return result
    
    def _infer_domain(self, user_query: str) -> str:
        """
        推断任务领域
        
        Args:
            user_query: 用户查询
            
        Returns:
            推断的领域
        """
        query_lower = user_query.lower()
        
        domain_indicators = {
            'web_development': ['网站', 'web', 'html', 'css', 'javascript', '前端', '后端'],
            'data_science': ['数据分析', '数据科学', 'pandas', 'numpy', '机器学习', '模型', '预测'],
            'api_development': ['api', '接口', 'rest', 'restful', 'graphql', 'endpoints'],
            'web_scraping': ['爬虫', 'spider', 'scrapy', '抓取', '爬取', 'crawl'],
            'database': ['数据库', 'sql', 'mysql', 'postgresql', 'mongodb', '查询'],
            'system_admin': ['系统', '服务器', '部署', '运维', 'docker', 'kubernetes'],
            'mobile_development': ['移动', 'app', '安卓', 'android', 'ios', 'react native'],
            'security': ['安全', '加密', '认证', '授权', '防护', 'security'],
            'performance': ['性能', '优化', '速度', '效率', 'benchmark', '负载'],
            'automation': ['自动化', '脚本', '定时', '批处理', 'cron', 'schedule']
        }
        
        domain_scores = {}
        for domain, keywords in domain_indicators.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            inferred_domain = max(domain_scores, key=domain_scores.get)
            logger.debug(f"🏷️ 推断领域: {inferred_domain} (匹配度:{domain_scores[inferred_domain]})")
            return inferred_domain
        
        return 'general'
    
    def get_confidence_statistics(self) -> Dict[str, Any]:
        """
        获取置信度统计信息
        
        Returns:
            置信度统计数据
        """
        if not self.confidence_history:
            return {
                'total_assessments': 0,
                'avg_confidence': 0.0,
                'confidence_trend': 'insufficient_data',
                'cache_size': len(self.assessment_cache)
            }
        
        confidences = [item['predicted_confidence'] for item in self.confidence_history]
        avg_confidence = sum(confidences) / len(confidences)
        
        # 计算趋势
        if len(confidences) >= 5:
            recent_avg = sum(confidences[-5:]) / 5
            earlier_avg = sum(confidences[-10:-5]) / 5 if len(confidences) >= 10 else avg_confidence
            
            if recent_avg > earlier_avg + 0.05:
                trend = 'improving'
            elif recent_avg < earlier_avg - 0.05:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'total_assessments': len(self.confidence_history),
            'avg_confidence': avg_confidence,
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'confidence_trend': trend,
            'cache_size': len(self.assessment_cache),
            'recent_confidences': confidences[-5:] if len(confidences) >= 5 else confidences
        }
    
    def update_confidence_feedback(self, predicted_confidence: float, 
                                 actual_success: bool, execution_time: float):
        """
        更新置信度反馈，用于改进预测准确性
        
        Args:
            predicted_confidence: 预测的置信度
            actual_success: 实际执行是否成功
            execution_time: 执行时间
        """
        feedback_record = {
            'timestamp': time.time(),
            'predicted_confidence': predicted_confidence,
            'actual_success': actual_success,
            'execution_time': execution_time,
            'confidence_accuracy': abs(predicted_confidence - (1.0 if actual_success else 0.0))
        }
        
        self.confidence_history.append(feedback_record)
        
        # 限制历史长度
        if len(self.confidence_history) > 200:
            self.confidence_history = self.confidence_history[-100:]
        
        logger.debug(f"📈 更新置信度反馈: 预测={predicted_confidence:.3f}, 实际={'成功' if actual_success else '失败'}")
    
    def get_quick_analysis_summary(self, user_query: str, execution_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        获取快速分析总结 - PriorReasoner的新核心功能
        
        提供任务的快速概览，包括复杂度、置信度、领域等关键信息
        
        Args:
            user_query: 用户查询
            execution_context: 执行上下文
            
        Returns:
            快速分析总结
        """
        start_time = time.time()
        
        # 快速分析
        complexity_analysis = self.analyze_task_complexity(user_query)
        confidence_score = self.assess_task_confidence(user_query, execution_context)
        
        analysis_time = time.time() - start_time
        
        summary = {
            'domain': complexity_analysis.get('estimated_domain', 'general'),
            'complexity_score': complexity_analysis.get('complexity_score', 0.5),
            'confidence_score': confidence_score,
            'requires_multi_step': complexity_analysis.get('requires_multi_step', False),
            'key_factors': list(complexity_analysis.get('complexity_factors', {}).keys())[:3],
            'analysis_time': analysis_time,
            'recommendation': self._get_analysis_recommendation(
                complexity_analysis.get('complexity_score', 0.5), 
                confidence_score
            )
        }
        
        logger.info(f"⚡ 快速分析完成: {summary['domain']}领域, 复杂度{summary['complexity_score']:.2f}, 置信度{summary['confidence_score']:.2f}")
        return summary
    
    def _get_analysis_recommendation(self, complexity_score: float, confidence_score: float) -> str:
        """
        基于分析结果提供建议
        
        Args:
            complexity_score: 复杂度分数
            confidence_score: 置信度分数
            
        Returns:
            分析建议
        """
        if complexity_score > 0.8 and confidence_score < 0.4:
            return "高复杂度低置信度任务，建议采用多阶段验证和保守策略"
        elif complexity_score > 0.7:
            return "复杂任务，建议采用系统分析和分步执行"
        elif confidence_score > 0.8:
            return "高置信度任务，可以采用直接执行策略"
        elif confidence_score < 0.3:
            return "低置信度任务，建议寻求额外信息或澄清"
        else:
            return "中等复杂度任务，建议采用平衡的分析和执行策略"
    
    def reset_cache(self):
        """重置评估缓存"""
        self.assessment_cache.clear()
        logger.info("🔄 轻量级分析助手缓存已重置")