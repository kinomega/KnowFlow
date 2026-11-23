# -*- coding: utf-8 -*-
"""
对话管理模块
管理对话历史、概念跳转、返回上层
"""
from typing import List, Dict, Optional
from datetime import datetime


class ConversationNode:
    """对话节点"""

    def __init__(self, query: str, content: str, concepts: List[Dict], depth: int = 0):
        self.query = query          # 查询内容
        self.content = content      # LLM返回的内容
        self.concepts = concepts    # 提取的概念列表 [{"id": 1, "name": "...", "query": "..."}]
        self.depth = depth          # 深度（第几层）
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ConversationManager:
    """对话管理器"""

    def __init__(self):
        self.history: List[ConversationNode] = []  # 对话历史栈
        self.current_node: Optional[ConversationNode] = None  # 当前节点
        self.initial_query: str = ""  # 初始查询
        self.domain: str = ""  # 领域

    def start_conversation(self, query: str, domain: str = ""):
        """开始新对话"""
        self.history = []
        self.current_node = None
        self.initial_query = query
        self.domain = domain

    def push_node(self, node: ConversationNode):
        """进入下一层（深入某个概念）"""
        if self.current_node:
            self.history.append(self.current_node)
        self.current_node = node

    def pop_node(self) -> bool:
        """返回上一层"""
        if not self.history:
            return False
        self.current_node = self.history.pop()
        return True

    def get_depth(self) -> int:
        """获取当前深度"""
        return len(self.history)

    def get_current_query(self) -> str:
        """获取当前查询"""
        return self.current_node.query if self.current_node else ""

    def get_current_content(self) -> str:
        """获取当前内容"""
        return self.current_node.content if self.current_node else ""

    def get_current_concepts(self) -> List[Dict]:
        """获取当前可深入的概念"""
        return self.current_node.concepts if self.current_node else []

    def generate_full_conversation(self) -> str:
        """生成完整对话记录（用于保存）"""
        lines = []

        # 标题
        lines.append(f"# {self.initial_query}探索")
        lines.append("")
        lines.append(f"**初始查询**: {self.initial_query}")
        if self.domain:
            lines.append(f"**领域**: {self.domain}")
        lines.append(f"**对话深度**: {self.get_depth() + 1}")
        lines.append(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 探索路径
        path = []
        for node in self.history:
            path.append(node.query)
        if self.current_node:
            path.append(self.current_node.query)

        lines.append("## 探索路径")
        lines.append(" → ".join(path))
        lines.append("")
        lines.append("---")
        lines.append("")

        # 完整对话内容
        all_nodes = self.history + ([self.current_node] if self.current_node else [])

        for i, node in enumerate(all_nodes, 1):
            lines.append(f"## 第{i}层：{node.query}")
            lines.append("")
            lines.append(node.content)
            lines.append("")

            if node.concepts:
                lines.append("### 相关概念")
                for concept in node.concepts:
                    lines.append(f"- [{concept['id']}] {concept['name']}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # 个人思考（留空）
        lines.append("## 个人思考")
        lines.append("")
        lines.append("（待补充）")
        lines.append("")

        return "\n".join(lines)

    def extract_all_concepts(self) -> List[str]:
        """提取所有涉及的概念（用于frontmatter）"""
        concepts = set()
        concepts.add(self.initial_query)

        all_nodes = self.history + ([self.current_node] if self.current_node else [])
        for node in all_nodes:
            concepts.add(node.query)
            for concept in node.concepts:
                concepts.add(concept['name'])

        return list(concepts)
