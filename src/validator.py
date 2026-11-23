# -*- coding: utf-8 -*-
"""
输出验证模块
验证LLM输出是否包含必填部分
"""
from typing import List, Tuple


class OutputValidator:
    """输出验证器"""

    @staticmethod
    def validate_keywords_output(content: str) -> Tuple[bool, List[str]]:
        """
        验证关键词分析输出

        Args:
            content: LLM生成的内容

        Returns:
            (is_valid, missing_sections): 是否有效，缺失的部分
        """
        required_sections = [
            "## 核心概念解释",
            "## 实际应用"
        ]

        missing = []
        for section in required_sections:
            if section not in content:
                missing.append(section)

        return len(missing) == 0, missing

    @staticmethod
    def validate_content_output(content: str) -> Tuple[bool, List[str]]:
        """
        验证内容分析输出

        Args:
            content: LLM生成的内容

        Returns:
            (is_valid, missing_sections): 是否有效，缺失的部分
        """
        required_sections = [
            "## 核心观点",
            "## 实际应用"
        ]

        missing = []
        for section in required_sections:
            if section not in content:
                missing.append(section)

        return len(missing) == 0, missing

    @staticmethod
    def validate_document_output(content: str) -> Tuple[bool, List[str]]:
        """
        验证文档分析输出

        Args:
            content: LLM生成的内容

        Returns:
            (is_valid, missing_sections): 是否有效，缺失的部分
        """
        required_sections = [
            "## 文档概述",
            "## 核心内容"
        ]

        missing = []
        for section in required_sections:
            if section not in content:
                missing.append(section)

        return len(missing) == 0, missing
