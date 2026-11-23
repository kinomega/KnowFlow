# -*- coding: utf-8 -*-
"""
笔记生成模块
将LLM分析结果保存为Markdown文件
"""
from pathlib import Path
from datetime import datetime
from typing import Optional


class NoteGenerator:
    """笔记生成器"""

    def __init__(self, vault_path: str, target_folder: str = "0-inbox"):
        self.vault_path = Path(vault_path)
        self.target_folder = target_folder

    def save_note(self, content: str, filename: str, metadata: dict = None) -> Optional[str]:
        """
        保存笔记（通用方法）

        Args:
            content: 笔记内容
            filename: 文件名
            metadata: 元数据字典

        Returns:
            str: 保存的文件路径，失败返回None
        """
        target_dir = self.vault_path / self.target_folder
        if not target_dir.exists():
            print(f"❌ 目标目录不存在: {target_dir}")
            return None

        filepath = target_dir / filename

        # 生成frontmatter
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        frontmatter = "---\n"
        if metadata:
            for key, value in metadata.items():
                frontmatter += f"{key}: {value}\n"
        frontmatter += f"created: {now}\n"
        frontmatter += "---\n\n"

        full_content = frontmatter + content

        try:
            filepath.write_text(full_content, encoding='utf-8')
            return str(filepath)
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return None

    def save_conversation(self, full_content: str, title: str,
                         initial_query: str, domain: str,
                         concepts: list, depth: int) -> Optional[str]:
        """
        保存对话探索记录

        Args:
            full_content: 完整对话内容
            title: 笔记标题
            initial_query: 初始查询
            domain: 领域
            concepts: 涉及的所有概念
            depth: 对话深度

        Returns:
            str: 保存的文件路径，失败返回None
        """
        # 构建目标目录
        target_dir = self.vault_path / self.target_folder
        if not target_dir.exists():
            print(f"❌ 目标目录不存在: {target_dir}")
            return None

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title}_探索_{timestamp}.md"
        filepath = target_dir / filename

        # 生成frontmatter
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        concepts_yaml = "\n    - ".join(concepts) if concepts else ""
        domain_line = f"  domain: {domain}" if domain else ""

        frontmatter = f"""---
title: {title}探索
created: {now}
grepro:
  source: conversation_exploration
  initial_query: {initial_query}
{domain_line}
  conversation_depth: {depth}
  concepts:
    - {concepts_yaml}
  relations: []
  last_accessed: {now}
---

"""

        full_note = frontmatter + full_content

        # 保存文件
        try:
            filepath.write_text(full_note, encoding='utf-8')
            return str(filepath)
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return None
        """
        保存笔记到Obsidian

        Args:
            content: 笔记内容（Markdown）
            title: 笔记标题
            source: 来源说明

        Returns:
            str: 保存的文件路径，失败返回None
        """
        # 构建目标目录
        target_dir = self.vault_path / self.target_folder
        if not target_dir.exists():
            print(f"❌ 目标目录不存在: {target_dir}")
            print(f"请检查config.yaml中的vault_path和target_folder配置")
            return None

        # 生成文件名（避免重复）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title}_{timestamp}.md"
        filepath = target_dir / filename

        # 生成完整内容（添加元数据）
        full_content = self._build_full_note(content, title, source)

        # 保存文件
        try:
            filepath.write_text(full_content, encoding='utf-8')
            return str(filepath)
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return None

    def _build_full_note(self, content: str, title: str, source: str) -> str:
        """构建完整笔记内容"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        frontmatter = f"""---
title: {title}
created: {now}
source: {source}
kb_level: 0
kb_mastery: 0
---

"""
        return frontmatter + content
