# -*- coding: utf-8 -*-
"""
Obsidian Local REST API 客户端
用于KnowFlow与Obsidian的双向通信
"""

import requests
import urllib3
from typing import Optional, Dict, List, Any
from pathlib import Path

# 禁用SSL警告（本地自签名证书）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ObsidianClient:
    """Obsidian REST API客户端"""

    def __init__(self, api_key: str, base_url: str = "https://127.0.0.1:27124"):
        """
        初始化客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def _request(self, method: str, endpoint: str, custom_headers: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            endpoint: API端点
            custom_headers: 自定义请求头（会覆盖默认headers）
            **kwargs: 其他requests参数

        Returns:
            响应JSON
        """
        url = f"{self.base_url}{endpoint}"

        # 使用自定义headers或默认headers
        if custom_headers:
            kwargs['headers'] = custom_headers
        else:
            kwargs['headers'] = self.headers

        kwargs['verify'] = False  # 忽略SSL证书验证

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()

            # 如果有返回内容，尝试解析JSON
            if response.text.strip():
                try:
                    return response.json()
                except:
                    # 如果不是JSON，返回纯文本
                    return response.text
            else:
                return {'success': True}

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            raise

    def test_connection(self) -> bool:
        """
        测试连接

        Returns:
            是否连接成功
        """
        try:
            # 尝试多个端点测试连接
            endpoints = ['/vault/', '/active/', '/']

            for endpoint in endpoints:
                try:
                    self._request('GET', endpoint)
                    print("[OK] Obsidian connection successful")
                    return True
                except:
                    continue

            print("[ERROR] All connection attempts failed")
            return False

        except Exception as e:
            print(f"[ERROR] Obsidian connection failed: {e}")
            return False

    def create_note(self, path: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        创建笔记

        Args:
            path: 笔记路径（相对vault根目录，如 "notes/test.md"）
            content: 笔记内容（Markdown）
            tags: 标签列表

        Returns:
            创建结果
        """
        # 构建frontmatter
        frontmatter = ""
        if tags:
            frontmatter = "---\n"
            frontmatter += f"tags: [{', '.join(tags)}]\n"
            frontmatter += "---\n\n"

        full_content = frontmatter + content

        try:
            # PUT请求，body直接是文本内容
            custom_headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'text/markdown'
            }
            result = self._request('PUT', f'/vault/{path}',
                                 custom_headers=custom_headers,
                                 data=full_content.encode('utf-8'))
            print(f"[OK] Note created: {path}")
            return result
        except Exception as e:
            print(f"[ERROR] Failed to create note: {e}")
            raise

    def read_note(self, path: str) -> str:
        """
        读取笔记内容

        Args:
            path: 笔记路径

        Returns:
            笔记内容
        """
        try:
            result = self._request('GET', f'/vault/{path}')
            # API可能直接返回文本内容，或返回包含content字段的JSON
            if isinstance(result, str):
                return result
            elif isinstance(result, dict):
                return result.get('content', '')
            else:
                return str(result)
        except Exception as e:
            print(f"[ERROR] Failed to read note: {e}")
            raise

    def update_note(self, path: str, content: str) -> Dict[str, Any]:
        """
        更新笔记内容

        Args:
            path: 笔记路径
            content: 新内容

        Returns:
            更新结果
        """
        try:
            # PATCH请求，body直接是文本内容
            custom_headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'text/markdown'
            }
            result = self._request('PATCH', f'/vault/{path}',
                                 custom_headers=custom_headers,
                                 data=content.encode('utf-8'))
            print(f"[OK] Note updated: {path}")
            return result
        except Exception as e:
            print(f"[ERROR] Failed to update note: {e}")
            raise

    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索笔记

        Args:
            query: 搜索查询

        Returns:
            搜索结果列表
        """
        try:
            # 使用POST请求和query参数
            result = self._request('POST', '/search/simple/', params={'query': query})
            # API可能直接返回列表，或返回包含results字段的字典
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return result.get('results', [])
            else:
                return []
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            raise

    def list_tags(self) -> List[str]:
        """
        获取所有标签

        Returns:
            标签列表
        """
        try:
            result = self._request('GET', '/tags/')
            # API可能直接返回列表，或返回包含tags字段的字典
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return result.get('tags', [])
            else:
                return []
        except Exception as e:
            print(f"[ERROR] Failed to get tags: {e}")
            raise

    def get_notes_by_tag(self, tag: str) -> List[str]:
        """
        根据标签获取笔记

        Args:
            tag: 标签名

        Returns:
            笔记路径列表
        """
        try:
            result = self._request('GET', f'/tags/{tag}/')
            return result.get('files', [])
        except Exception as e:
            print(f"[ERROR] Failed to get notes by tag: {e}")
            raise


def test_obsidian_client():
    """测试Obsidian客户端功能"""

    # 配置（从环境变量读取，或使用默认的测试值）
    import os
    API_KEY = os.getenv("OBSIDIAN_API_KEY", "your-api-key-here")
    BASE_URL = "https://127.0.0.1:27124"

    if API_KEY == "your-api-key-here":
        print("错误：请设置 OBSIDIAN_API_KEY 环境变量")
        print("或在代码中修改 API_KEY 的值")
        return

    print("=" * 50)
    print("测试 Obsidian REST API 客户端")
    print("=" * 50)

    # 创建客户端
    client = ObsidianClient(api_key=API_KEY, base_url=BASE_URL)

    # 测试1: 连接测试
    print("\n[测试1] 连接测试")
    if not client.test_connection():
        return

    # 测试2: 创建测试笔记
    print("\n[测试2] 创建测试笔记")
    test_path = "0-inbox/knowflow_test.md"
    test_content = """# KnowFlow测试笔记

这是一个测试笔记，由KnowFlow自动生成。

## 测试内容

- 连接成功 ✅
- 笔记创建 ✅
- 标签支持 ✅

创建时间：2026-11-06
"""

    try:
        client.create_note(
            path=test_path,
            content=test_content,
            tags=["knowflow", "test"]
        )
    except Exception as e:
        print(f"创建笔记失败: {e}")

    # 测试3: 读取笔记
    print("\n[测试3] 读取笔记")
    try:
        content = client.read_note(test_path)
        print(f"读取成功，内容长度: {len(content)} 字符")
    except Exception as e:
        print(f"读取笔记失败: {e}")

    # 测试4: 搜索笔记
    print("\n[测试4] 搜索笔记")
    try:
        results = client.search_notes("KnowFlow")
        print(f"搜索结果: {len(results)} 条")
    except Exception as e:
        print(f"搜索失败: {e}")

    # 测试5: 标签功能
    print("\n[测试5] 标签功能")
    try:
        tags = client.list_tags()
        print(f"Vault中的标签: {len(tags)} 个")

        # 标签可能是字符串或字典格式
        tag_names = []
        for t in tags:
            if isinstance(t, str):
                tag_names.append(t.lstrip('#'))
            elif isinstance(t, dict) and 'tag' in t:
                tag_names.append(t['tag'].lstrip('#'))

        if "knowflow" in tag_names:
            notes = client.get_notes_by_tag("knowflow")
            print(f"标签 #knowflow 的笔记: {len(notes)} 个")
    except Exception as e:
        print(f"标签操作失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == '__main__':
    test_obsidian_client()
