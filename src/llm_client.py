# -*- coding: utf-8 -*-
"""
LLM客户端模块
支持: Ollama本地, Anthropic Claude, OpenAI兼容接口（OpenAI/DeepSeek/通义千问/智谱/Kimi/中转API等）
"""
import requests
import time
import sys
from typing import Optional, Dict, Any


class LLMClient:
    """LLM客户端"""

    def __init__(self, provider: str = "ollama", model: str = "qwen2.5:7b",
                 base_url: str = "http://localhost:11434", temperature: float = 0.7,
                 api_key: str = ""):
        self.provider = provider
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.temperature = temperature
        self.api_key = api_key

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        生成文本

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            str: 生成的文本失败返回None
        """
        # 显示进度提示
        print(" 思考中...", end="", flush=True)
        start_time = time.time()

        try:
            if self.provider == "ollama":
                result = self._ollama_generate(prompt, system_prompt)
            elif self.provider == "anthropic":
                result = self._anthropic_generate(prompt, system_prompt)
            elif self.provider == "openai":
                result = self._openai_compatible_generate(prompt, system_prompt)
            else:
                print(f"\n ✗ 不支持的provider: {self.provider}")
                print(f"   支持的provider: ollama, anthropic, openai")
                return None

            # 计算耗时
            elapsed = time.time() - start_time

            # 清除进度提示并显示完成信息
            print(f"\r 完成 ({elapsed:.1f}s)    ")

            return result

        except KeyboardInterrupt:
            elapsed = time.time() - start_time
            print(f"\n  已中断 ({elapsed:.1f}s)")
            return None  # 返回None而不是raise让调用方决定如何处理
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n 失败 ({elapsed:.1f}s): {e}")
            return None

    def _ollama_generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """调用Ollama API"""
        try:
            url = f"{self.base_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.ConnectionError:
            print(f" 无法连接到Ollama服务: {self.base_url}")
            print("请确认Ollama已启动: ollama serve")
            return None
        except requests.exceptions.Timeout:
            print(" 请求超时180秒")
            print("可能原因")
            print("  - LLM服务卡住或响应慢")
            print("  - CPU推理速度较慢正常")
            print("  - 输入内容过长")
            print("建议等待完成或简化输入")
            return None
        except Exception as e:
            print(f" LLM调用失败: {e}")
            return None

    def check_health(self) -> bool:
        """检查服务可用性"""
        try:
            if self.provider == "ollama":
                url = f"{self.base_url}/api/tags"
                response = requests.get(url, timeout=5)
                return response.status_code == 200
            elif self.provider == "anthropic":
                # Anthropic不需要检查直接返回True
                if not self.api_key:
                    print(" 未配置API Key")
                    return False
                return True
            elif self.provider == "openai":
                # OpenAI兼容接口检查API Key
                if not self.api_key:
                    print(" 未配置API Key")
                    return False
                return True
        except:
            return False
        return False

    def _anthropic_generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """调用Anthropic API"""
        try:
            url = f"{self.base_url}/v1/messages"

            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            payload = {
                "model": self.model,
                "max_tokens": 8192,  # 增加到8192以支持更完整的内容
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result["content"][0]["text"].strip()

        except requests.exceptions.HTTPError as e:
            print(f" API调用失败: {e}")
            if hasattr(e.response, 'text'):
                print(f"详细错误: {e.response.text}")
            return None
        except requests.exceptions.Timeout:
            print(" 请求超时60秒")
            return None
        except Exception as e:
            print(f" LLM调用失败: {e}")
            return None

    def _openai_compatible_generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        OpenAI兼容接口生成（支持OpenAI、DeepSeek、通义千问、智谱AI、Kimi、中转API等）

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            str: 生成的文本，失败返回None
        """
        try:
            url = f"{self.base_url}/v1/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

        except requests.exceptions.HTTPError as e:
            print(f" API调用失败: {e}")
            if hasattr(e.response, 'text'):
                print(f"详细错误: {e.response.text}")
            return None
        except requests.exceptions.Timeout:
            print(" 请求超时（60秒）")
            return None
        except KeyError as e:
            print(f" 响应格式错误: {e}")
            return None
        except Exception as e:
            print(f" OpenAI兼容接口调用失败: {e}")
            return None
