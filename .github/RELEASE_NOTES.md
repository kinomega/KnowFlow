# KnowFlow v1.0 - 首个开源版本

## 📝 简介

对话式笔记工具，边聊天边记笔记，自动整理概念关系。

## ✨ 主要功能

- **对话式探索**：逐层深入概念，避免重复
- **自动笔记**：生成结构化笔记和概念关系图
- **语义搜索**：智能检索已有笔记内容
- **双模式**：可集成Obsidian或独立使用
- **多LLM支持**：Claude、OpenAI、DeepSeek、通义千问、Ollama等

## 🚀 快速开始

### Windows用户（推荐）

1. 下载 `KnowFlow-v1.0-Windows.zip`
2. 解压到任意目录
3. 双击 `KnowFlow.exe`
4. 首次运行会创建配置文件，填入API Key后重启

### 开发者

```bash
git clone https://github.com/lqn2005/KnowFlow.git
cd KnowFlow
pip install -r requirements.txt
cp config.yaml.example config.yaml
# 编辑config.yaml填入API Key
python start_desktop.py
```

## 📄 许可证

GPL v3 - 衍生作品必须开源

## 🐛 问题反馈

[提交Issue](https://github.com/lqn2005/KnowFlow/issues)
