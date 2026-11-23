# -*- coding: utf-8 -*-
"""
知识图谱构建器
基于探索历史和向量相似度构建多维知识图谱
"""
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime


class KnowledgeNode:
    """知识节点"""

    def __init__(self, concept_id: str, name: str, domain: str = "",
                 depth: int = 0, learned_at: str = ""):
        self.id = concept_id
        self.name = name
        self.domain = domain  # 领域（AI Agent、数据库等）
        self.depth = depth  # 学习深度
        self.learned_at = learned_at  # 学习时间
        self.visit_count = 0  # 访问次数

        # 关系
        self.children: Set[str] = set()  # 子概念
        self.related: Dict[str, float] = {}  # 相关概念及相似度
        self.parent: Optional[str] = None  # 父概念

        # 元数据
        self.note_path: Optional[str] = None  # 关联的笔记路径
        self.tags: Set[str] = set()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "depth": self.depth,
            "learned_at": self.learned_at,
            "visit_count": self.visit_count,
            "children": list(self.children),
            "related": self.related,
            "parent": self.parent,
            "note_path": self.note_path,
            "tags": list(self.tags)
        }

    @staticmethod
    def from_dict(data: Dict) -> 'KnowledgeNode':
        """从字典创建"""
        node = KnowledgeNode(
            concept_id=data["id"],
            name=data["name"],
            domain=data.get("domain", ""),
            depth=data.get("depth", 0),
            learned_at=data.get("learned_at", "")
        )
        node.visit_count = data.get("visit_count", 0)
        node.children = set(data.get("children", []))
        node.related = data.get("related", {})
        node.parent = data.get("parent")
        node.note_path = data.get("note_path")
        node.tags = set(data.get("tags", []))
        return node


class KnowledgeGraph:
    """知识图谱"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.storage_path = storage_path

        # 加载已有图谱
        if storage_path and storage_path.exists():
            self.load()

    def add_node(self, node: KnowledgeNode) -> None:
        """添加节点"""
        if node.id in self.nodes:
            # 更新已有节点
            existing = self.nodes[node.id]
            existing.visit_count += 1
            existing.depth = max(existing.depth, node.depth)
            if node.domain and not existing.domain:
                existing.domain = node.domain
        else:
            self.nodes[node.id] = node

    def add_edge(self, parent_id: str, child_id: str) -> None:
        """添加父子关系"""
        if parent_id in self.nodes and child_id in self.nodes:
            self.nodes[parent_id].children.add(child_id)
            self.nodes[child_id].parent = parent_id

    def add_relation(self, concept1_id: str, concept2_id: str,
                    similarity: float) -> None:
        """添加相关关系（双向）"""
        if concept1_id in self.nodes:
            self.nodes[concept1_id].related[concept2_id] = similarity
        if concept2_id in self.nodes:
            self.nodes[concept2_id].related[concept1_id] = similarity

    def get_subgraph(self, center_id: str, max_depth: int = 2) -> Dict:
        """
        获取以某个概念为中心的子图

        Args:
            center_id: 中心节点ID
            max_depth: 最大遍历深度

        Returns:
            dict: {
                "center": 中心节点,
                "nodes": 相关节点列表,
                "edges": 边列表
            }
        """
        if center_id not in self.nodes:
            return {"center": None, "nodes": [], "edges": []}

        # BFS遍历
        visited = set()
        queue = [(center_id, 0)]
        nodes = []
        edges = []

        while queue:
            node_id, depth = queue.pop(0)

            if node_id in visited or depth > max_depth:
                continue

            visited.add(node_id)
            node = self.nodes[node_id]
            nodes.append(node.to_dict())

            # 添加子节点
            for child_id in node.children:
                if child_id not in visited:
                    queue.append((child_id, depth + 1))
                    edges.append({
                        "source": node_id,
                        "target": child_id,
                        "type": "parent-child",
                        "value": 1.0
                    })

            # 添加强相关节点（相似度>0.6）
            for related_id, similarity in node.related.items():
                if similarity > 0.6 and related_id not in visited and related_id in self.nodes:
                    queue.append((related_id, depth + 1))
                    edges.append({
                        "source": node_id,
                        "target": related_id,
                        "type": "related",
                        "value": similarity
                    })

        return {
            "center": self.nodes[center_id].to_dict(),
            "nodes": nodes,
            "edges": edges
        }

    def get_learning_path(self, start_id: str, end_id: str) -> List[str]:
        """
        获取两个概念之间的学习路径（最短路径）

        Returns:
            list: 概念ID列表
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return []

        # BFS查找最短路径
        queue = [(start_id, [start_id])]
        visited = {start_id}

        while queue:
            current_id, path = queue.pop(0)

            if current_id == end_id:
                return path

            node = self.nodes[current_id]

            # 遍历所有邻居（子节点 + 相关节点）
            neighbors = list(node.children) + list(node.related.keys())

            for neighbor_id in neighbors:
                if neighbor_id not in visited and neighbor_id in self.nodes:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return []  # 无路径

    def get_centrality_ranking(self) -> List[Tuple[str, float]]:
        """
        计算节点中心度排名（基于度中心度）

        Returns:
            list: [(node_id, centrality_score)]
        """
        centrality = {}

        for node_id, node in self.nodes.items():
            # 度中心度 = 子节点数 + 相关节点数 + 访问次数
            degree = len(node.children) + len(node.related) + node.visit_count
            centrality[node_id] = degree

        # 排序
        ranked = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return ranked

    def get_domain_clusters(self) -> Dict[str, List[str]]:
        """按领域聚类"""
        clusters = {}

        for node_id, node in self.nodes.items():
            domain = node.domain or "未分类"
            if domain not in clusters:
                clusters[domain] = []
            clusters[domain].append(node_id)

        return clusters

    def save(self) -> None:
        """保存图谱"""
        if not self.storage_path:
            return

        data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "nodes": {node_id: node.to_dict()
                     for node_id, node in self.nodes.items()}
        }

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> None:
        """加载图谱"""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.nodes = {
            node_id: KnowledgeNode.from_dict(node_data)
            for node_id, node_data in data.get("nodes", {}).items()
        }

    def get_stats(self) -> Dict:
        """获取统计信息"""
        domains = self.get_domain_clusters()
        top_concepts = self.get_centrality_ranking()[:10]

        return {
            "total_nodes": len(self.nodes),
            "total_domains": len(domains),
            "domains": {k: len(v) for k, v in domains.items()},
            "top_concepts": [(self.nodes[nid].name, score)
                            for nid, score in top_concepts]
        }
