# -*- coding: utf-8 -*-
"""
知识分析模块
基于LLM分析文本生成结构化知识笔记
"""
from typing import Optional, List, Dict
from .llm_client import LLMClient


class KnowledgeAnalyzer:
    """知识分析器"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def analyze_keywords(self, keywords: str, domain: str = "", mode: str = "overview",
                        related_notes: List[Dict] = None,
                        explored_concepts: List[str] = None,
                        parent_concept: str = None,
                        depth: int = 0,
                        language: str = 'zh') -> Optional[str]:
        """
        分析关键词生成知识笔记

        Args:
            keywords: 用户提供的关键词逗号分隔
            domain: 领域/上下文可选
            mode: "overview"概览模式 / "deep"深入模式
            related_notes: 检索到的相关笔记
            explored_concepts: 已探索的概念列表避免重复
            parent_concept: 父概念深入时的上级概念
            depth: 当前深度第几层

        Returns:
            str: Markdown格式的知识笔记
        """
        system_prompt = "你是知识整理助手帮助用户构建结构化的知识笔记"

        domain_hint = f"\n领域/上下文{domain}" if domain else ""

        # 构建相关笔记上下文
        related_context = ""
        if related_notes:
            related_context = "\n\n**用户已有的相关笔记**\n"
            for note in related_notes:
                related_context += f"- [[{note['title']}]] (相似度: {note['similarity']*100:.0f}%)\n"
                if note.get('preview'):
                    preview = note['preview'][:100].replace('\n', ' ')
                    related_context += f"  预览: {preview}...\n"

        if mode == "overview":
            # 概览模式提供框架+可深入的概念
            prompt = f"""关键词{keywords}{domain_hint}{related_context}

请提供概览分析

## 核心定义
准确解释这个概念1-2段用自然语言描述

## 主要特点/应用场景
核心特点或典型应用3-5点用文字描述不要写代码

## 相关概念
列出可深入学习的概念格式[数字] 概念名 | 领域/方向 | 类型
**重要必须使用[1][2][3]这样的方括号格式不要使用1.2.3.格式**
**重要编号从[1]开始不要使用[0]**
**每个概念标题行后必须另起一行写1-2句简短描述说明这个概念是什么为什么重要**

示例
[1] 神经网络基本原理 | 机器学习/数学基础 | 基石
模拟生物神经元的计算模型，是深度学习的数学基础。理解权重、激活函数等核心要素。

[2] 模型训练流程 | 机器学习/核心框架 | 框架
数据准备、前向传播、损失计算、反向传播的完整流程。掌握训练的核心步骤。

[3] 超参数调优技巧 | 机器学习/优化技术 | 拓展
学习率、批大小、正则化参数等的选择方法。提升模型性能的实用技巧。

类型说明
- **基石**底层原理和核心数学/逻辑基础缺少会影响整个知识体系的理解
- **框架**主体知识结构和核心流程是知识的骨架
- **拓展**拓展应用实践技巧和工具使用非必需但能提升实际效果

要求
- 核心定义要准确完整
- 特点/应用要具体实用
- 相关概念编号从[1]开始
- 相关概念数量不固定根据实际关联度决定可能3-15个
- 只列出真正相关且值得深入的概念不要滥竽充数
- 按重要性排序基石概念优先然后框架最后拓展
- 必须为每个概念添加准确的类型标签基石/框架/拓展
- **不要生成代码示例**用自然语言描述即可
{f"- 关联用户已有笔记内容" if related_notes else ""}
"""
        else:
            # 深入模式详细分析
            # 构建已探索概念提示
            explored_hint = ""
            if explored_concepts:
                explored_hint = f"\n\n**已探索过的概念请避免重复**\n{', '.join(explored_concepts)}"

            parent_hint = ""
            if parent_concept:
                parent_hint = f"\n\n**当前正在深入分析的是**{parent_concept}父概念的子概念"

            depth_hint = ""
            if depth > 0:
                depth_hint = f"\n\n**当前深度**第{depth + 1}层请提供更细粒度更具体的子概念而不是泛泛的大概念"

            prompt = f"""关键词{keywords}{domain_hint}{related_context}{parent_hint}{depth_hint}{explored_hint}

请深度分析

## 核心概念解释
准确深入的定义包含背景和原理

## 工作原理/实现机制
底层机制技术实现核心流程用文字描述不要写代码示例

## 实际应用
详细的使用场景案例最佳实践注意事项用文字描述应用方式

## 相关概念向下细化不要横向发散
列出可以继续深入的**子概念**更细粒度更具体格式[数字] 概念名 | 领域/方向
**重要必须使用[1][2][3]这样的方括号格式不要使用1.2.3.或其他格式**
**每个概念标题行后必须另起一行写1-2句简短描述说明这个子概念的核心内容**

示例
[1] 注意力机制计算公式 | Transformer/数学原理
Query、Key、Value的矩阵运算和softmax归一化过程。理解注意力权重如何计算。

[2] 多头注意力实现 | Transformer/架构设计
并行计算多组注意力的方法和信息融合机制。提升模型的表达能力。

**重要**
- 推荐的概念应该是当前概念的**子概念/组成部分/细化方向**而不是平级或更广的概念
- 像生物分类界门纲目科属种一样逐层细化不要每次都推荐最顶层的大概念
- 已探索过的概念不要再推荐
- 深度{depth + 1}层应该比深度{depth}层更具体更细粒度
- 数量不固定可能3-15个根据实际关联度和重要性决定
- 只推荐真正值得深入的子概念不要为了凑数而列出弱相关的概念
- 高频常见对理解当前概念至关重要的优先
- **不要生成代码示例**用自然语言描述原理和应用即可

{f"- 和用户已有笔记建立联系" if related_notes else ""}
"""

        # 根据语言添加指示
        if language == 'en':
            prompt += "\n\nIMPORTANT: Please respond in English. All analysis, explanations, concept descriptions, and output should be in English."

        return self.llm.generate(prompt, system_prompt)
        """
        分析关键词生成知识笔记

        Args:
            keywords: 用户提供的关键词逗号分隔
            domain: 领域/上下文可选
            mode: "overview"概览模式 / "deep"深入模式

        Returns:
            str: Markdown格式的知识笔记
        """
        system_prompt = "你是知识整理助手帮助用户构建结构化的知识笔记"

        domain_hint = f"\n领域/上下文{domain}" if domain else ""

        if mode == "overview":
            # 概览模式提供框架+可深入的概念
            prompt = f"""关键词{keywords}{domain_hint}

请提供概览分析**必须**包含

## 核心概念解释
每个关键词的准确定义聚焦在指定领域

## 实际应用
怎么用使用场景具体案例

## 相关概念
列出可以深入学习的相关概念用[数字]标记

格式示例
[1] 概念A - 简短说明
[2] 概念B - 简短说明
[3] 概念C - 简短说明

**要求**
- 概念解释要准确但不过于深入
- 相关概念要有实质联系
- 用[数字]标记所有可深入的概念
"""
        else:
            # 深入模式详细分析
            prompt = f"""关键词{keywords}{domain_hint}

请深度分析**必须**包含

## 核心概念解释
准确深入的定义

## 工作原理
底层机制实现方式

## 实际应用
详细的使用场景案例最佳实践

## 相关概念
列出可以继续深入的概念用[数字]标记

格式示例
[1] 概念A - 简短说明
[2] 概念B - 简短说明

**要求**
- 分析要深入全面
- 原理要讲清楚
- 用[数字]标记可深入的概念
"""

        return self.llm.generate(prompt, system_prompt)

    def analyze_content(self, content: str, domain: str = "") -> Optional[str]:
        """
        分析长文本内容生成归纳总结

        Args:
            content: 用户提供的文本内容
            domain: 领域/上下文可选

        Returns:
            str: Markdown格式的知识笔记
        """
        system_prompt = "你是知识整理助手擅长归纳总结和概念提取"

        domain_hint = f"\n领域/上下文{domain}" if domain else ""

        prompt = f"""请对以下内容进行深度分析和归纳总结{domain_hint}

{content}

---

请生成结构化知识笔记**必须**包含

## 核心观点
提炼3-5条主要观点

## 实际应用
怎么用使用场景

**可选**包含

## 关键概念
提取专业术语和重要概念并解释

## 论证逻辑
如何推导论证结构

## 个人思考
留空供用户补充

**要求**
- 必填部分必须有实质内容
- 提炼要精准不遗漏核心内容
- 概念解释要准确
- 保持客观不过度解读
"""

        return self.llm.generate(prompt, system_prompt)

    def analyze_document(self, text: str, filename: str, domain: str = "") -> Optional[str]:
        """
        分析文档内容可能较长

        Args:
            text: 文档文本
            filename: 文件名
            domain: 领域/上下文可选

        Returns:
            str: Markdown格式的知识笔记
        """
        system_prompt = "你是知识整理助手擅长处理文档并提取关键信息"

        domain_hint = f"\n领域/上下文{domain}" if domain else ""

        # 文档较短直接分析
        if len(text) <= 3000:
            prompt = f"""请分析以下文档内容
文件名{filename}{domain_hint}

{text}

---

生成结构化知识笔记**必须**包含

## 文档概述
文档类型主要讲什么

## 核心内容
主要观点关键信息

**可选**包含

## 重要概念
提取的专业术语和概念

## 知识关联
和哪些已有知识相关

## 实际价值
这份文档的价值在哪里

**要求**
- 必填部分必须有实质内容
- 全面但不冗长
- 突出重点
"""
            return self.llm.generate(prompt, system_prompt)

        # 文档较长提取摘要
        else:
            # 截取前3000字
            preview = text[:3000]
            prompt = f"""请分析以下文档内容已截取前3000字
文件名{filename}{domain_hint}

{preview}

---

注这是长文档以上是前半部分

生成结构化知识笔记**必须**包含

## 文档概述
文档类型主题

## 核心内容
从已读部分提取的主要观点

**可选**包含

## 重要概念
专业术语和关键概念

## 待补充
标注这是部分分析可能需要继续阅读全文

**要求**
- 必填部分必须有实质内容
- 标注这是基于部分内容的分析
"""
            return self.llm.generate(prompt, system_prompt)
