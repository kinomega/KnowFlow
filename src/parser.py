# -*- coding: utf-8 -*-
"""
文档解析模块
支持: .md, .txt, .docx, .pdf
"""
from pathlib import Path
from typing import Optional
import docx
import PyPDF2


class DocumentParser:
    """文档解析器"""

    @staticmethod
    def parse(file_path: str) -> Optional[str]:
        """
        解析文档，提取纯文本

        Args:
            file_path: 文件路径

        Returns:
            str: 提取的文本内容，失败返回None
        """
        path = Path(file_path)

        if not path.exists():
            print(f"❌ 文件不存在: {file_path}")
            return None

        ext = path.suffix.lower()

        try:
            if ext == '.md' or ext == '.txt':
                return DocumentParser._parse_text(path)
            elif ext == '.docx':
                return DocumentParser._parse_docx(path)
            elif ext == '.pdf':
                return DocumentParser._parse_pdf(path)
            else:
                print(f"❌ 不支持的格式: {ext}")
                return None
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            return None

    @staticmethod
    def _parse_text(path: Path) -> str:
        """解析纯文本/Markdown"""
        return path.read_text(encoding='utf-8')

    @staticmethod
    def _parse_docx(path: Path) -> str:
        """解析Word文档"""
        doc = docx.Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n\n'.join(paragraphs)

    @staticmethod
    def _parse_pdf(path: Path) -> str:
        """解析PDF文档"""
        with open(path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)
            return '\n\n'.join(text_parts)


class TextChunker:
    """文本切片器"""

    def __init__(self, chunk_size: int = 800, overlap: int = 150,
                 min_size: int = 200, max_size: int = 1500):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_size = min_size
        self.max_size = max_size

    def chunk(self, text: str) -> list[str]:
        """
        切分文本

        Args:
            text: 原始文本

        Returns:
            list[str]: 切分后的片段列表
        """
        if len(text) <= self.max_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size

            # 最后一段
            if end >= text_len:
                chunk = text[start:]
                if len(chunk) >= self.min_size:
                    chunks.append(chunk)
                elif chunks:
                    # 太短，合并到上一段
                    chunks[-1] += '\n\n' + chunk
                else:
                    chunks.append(chunk)
                break

            # 提取片段
            chunk = text[start:end]
            chunks.append(chunk)

            # 下一段起点（保留重叠）
            start = end - self.overlap

        return chunks
