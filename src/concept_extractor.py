# -*- coding: utf-8 -*-
"""
概念提取模块
从LLM输出中提取可深入的概念
"""
import re
from typing import List, Dict, Optional


class ConceptExtractor:
    """概念提取器"""

    @staticmethod
    def extract_from_text(text: str) -> List[Dict]:
        """
        从文本中提取概念（基于标记格式）

        LLM输出中用 [数字] 标记可深入的概念
        例如：[1] LangGraph BaseStore | AI Agent/记忆系统

        Args:
            text: LLM生成的文本

        Returns:
            list: [{"id": 1, "name": "概念名", "domain": "领域", "query": "查询关键词"}]
        """
        concepts = []

        # 匹配模式：[数字] 概念名 | 领域
        # 也兼容旧格式：[数字] 概念名
        pattern = r'\[(\d+)\]\s*([^\|\n\-：\(=]+?)(?:\s*\|\s*([^\n]+))?(?:\n|$)'

        matches = re.findall(pattern, text)

        for match in matches:
            concept_id = int(match[0])
            concept_name = match[1].strip()
            domain = match[2].strip() if match[2] else ""

            # 过滤掉不合理的概念（包含代码特征）
            if any(ch in concept_name for ch in ['=', '(', ')', 'invoke', 'result', 'def ', 'class ']):
                continue

            # 过滤掉太短的（可能是误匹配）
            if len(concept_name) < 2:
                continue

            concepts.append({
                "id": concept_id,
                "name": concept_name,
                "domain": domain,
                "query": concept_name  # 默认用名称作为查询关键词
            })

        return concepts

    @staticmethod
    def format_concepts_in_prompt(concepts: List[str]) -> str:
        """
        在Prompt中格式化概念列表

        Args:
            concepts: 概念列表

        Returns:
            str: 格式化后的文本
        """
        if not concepts:
            return ""

        lines = []
        for i, concept in enumerate(concepts, 1):
            lines.append(f"[{i}] {concept}")

        return "\n".join(lines)

    @staticmethod
    def validate_concept_id(concepts: List[Dict], concept_id: int) -> Optional[Dict]:
        """
        验证概念ID是否有效

        Args:
            concepts: 概念列表
            concept_id: 用户输入的ID

        Returns:
            dict: 对应的概念，无效返回None
        """
        for concept in concepts:
            if concept['id'] == concept_id:
                return concept
        return None
