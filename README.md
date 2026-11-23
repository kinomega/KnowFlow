# KnowFlow - 知流

**[English](./README_EN.md) | 简体中文**

> **记录知识在你认知中流动的轨迹**  
> 不是存资料的知识库，而是记录你理解知识的完整过程

> ⚠️ **注意**：这是一个为自己的学习习惯定制的个人工具，开源仅供参考和借鉴，不一定适合所有人的使用场景。

## 💡 什么是知流

**知流（Knowledge Flow）** 不同于传统笔记工具：

- **传统笔记**：存下来就结束了（静态）
- **知流**：记录知识怎么流过你的认知（动态）

**完整的知识流动循环**：
1. **流入** → 标准定义 + 问答理解 → 沉淀你的理解
2. **流转** → 关联相似笔记 → 形成知识网络
3. **流出** → 回看思考轨迹 → 重新激活认知

用问答方式沉淀你的理解，用关联方式回溯你的思考。

---

## ✨ 核心特性

### 🌊 知识流动的三个阶段

**📥 流入：从概念到理解**
- 输入一个概念，获取标准定义
- 通过问答对话，记录你的理解过程
- 不只存"是什么"，还存"你怎么理解的"

**🔄 流转：动态知识网络**
- 自动关联相似笔记（向量检索）
- 构建概念关系图谱（父子、关联、前置）
- 动态中心化：形成知识体系的"水源"

**📤 流出：回溯思考轨迹**
- 完整记录问答路径和思考过程
- 回看时能重新激活当时的理解
- 顺着轨迹重新思考，而非死记硬背

### 🎯 多维知识模型

- **纵深递进**：界门纲目科属种式探索，避免重复
- **知识图谱**：可视化概念关系网络
- **向量空间**：语义相似度检索
- **时间维度**：追溯学习历史
- **苏格拉底对话**：反思式深化理解

### 🔌 通用LLM接口
支持多种AI提供商，配置即切换：
- **Anthropic Claude**（官方）
- **OpenAI**（GPT系列）
- **DeepSeek**（国产高性价比）
- **通义千问**（阿里云）
- **智谱AI**（GLM系列）
- **Moonshot**（Kimi）
- **Ollama**（本地模型）
- **中转API**（自定义兼容接口）

### 📝 双模式系统
- **Obsidian模式**：关联已有Obsidian vault，双向同步
- **独立模式**：不依赖Obsidian，独立笔记目录

### 🔄 双向同步
- 自动监听文件变化
- Obsidian中的修改实时同步到索引
- 支持手动编辑笔记

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/lqn2005/KnowFlow.git
cd KnowFlow
pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 编辑配置文件
# 填入你的API Key和路径
notepad config.yaml  # Windows
# 或 vim config.yaml  # Linux/Mac
```

**基本配置示例**：

```yaml
# 工作模式
mode: "standalone"  # 或 "obsidian"

# LLM配置
llm:
  provider: "anthropic"  # 或 openai / ollama
  model: "claude-sonnet-4-6"
  api_key: "your-api-key-here"
  base_url: "https://api.anthropic.com"

# 独立模式（不使用Obsidian）
standalone:
  notes_path: "./notes"

# Obsidian模式（可选）
obsidian:
  vault_path: "D:/Obsidian/mine"
  target_folder: "mine"
```

### 3. 启动

**桌面应用**（推荐）：
```bash
python start_desktop.py
```

**命令行模式**：
```bash
python api_server.py
# 访问 http://localhost:8001
```

## 📖 配置详解

### LLM提供商配置

<details>
<summary>点击查看各提供商配置示例</summary>

**1. Anthropic Claude**
```yaml
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-6"
  api_key: "sk-ant-..."
  base_url: "https://api.anthropic.com"
```

**2. OpenAI**
```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "sk-..."
  base_url: "https://api.openai.com"
```

**3. DeepSeek**
```yaml
llm:
  provider: "openai"
  model: "deepseek-chat"
  api_key: "sk-..."
  base_url: "https://api.deepseek.com"
```

**4. 通义千问**
```yaml
llm:
  provider: "openai"
  model: "qwen-turbo"
  api_key: "sk-..."
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

**5. Ollama（本地）**
```yaml
llm:
  provider: "ollama"
  model: "qwen2.5:7b"
  api_key: ""
  base_url: "http://localhost:11434"
```

**6. 中转API**
```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "your-key"
  base_url: "https://api.your-proxy.com/v1"
```

</details>

### 模式选择

**独立模式**（推荐新手）：
```yaml
mode: "standalone"
standalone:
  notes_path: "./notes"  # 笔记存储目录
```

**Obsidian模式**（已有Obsidian用户）：
```yaml
mode: "obsidian"
obsidian:
  vault_path: "D:/Obsidian/mine"
  target_folder: "mine"
  watch_files: true  # 双向同步
```

## 📚 知流循环：完整的认知流动过程

### 1️⃣ 流入阶段：从概念到理解

```
输入概念 → 获取标准定义 → 问答对话 → 记录理解
```

**示例**：输入"Transformer"
- 📖 系统提供标准定义
- 💬 问答互动："你觉得注意力机制的核心是什么？"
- 💡 记录你的回答和思考过程
- 💾 保存完整的理解轨迹

### 2️⃣ 流转阶段：构建知识网络

```
新笔记 → 关联相似内容 → 形成知识图谱 → 动态中心化
```

- 🔗 自动关联已有的相似笔记
- 🕸️ 构建概念关系网络（父概念、子概念、前置知识）
- 🌳 形成知识体系的"水源"（不只是单点，而是体系）

### 3️⃣ 流出阶段：回溯与重新思考

```
查看笔记 → 标准定义 + 问答轨迹 → 重新激活认知
```

- 📝 不只看结论，还能看到当时的思考过程
- 🔄 顺着问答轨迹重新思考
- 🧠 重新激活认知，而非死记硬背

### 🎨 可视化知识图谱

- 图形化展示概念关系网络
- 追踪学习路径
- 发现知识盲区

## 🛠️ 技术栈

- **后端**：Python + FastAPI
- **LLM**：Anthropic/OpenAI/Ollama等
- **知识图谱**：NetworkX
- **向量检索**：暂未启用（预留接口）
- **前端**：原生JS + Cytoscape.js
- **桌面应用**：pywebview
- **文件监听**：watchdog

## 📦 打包

```bash
pyinstaller knowflow.spec
```

可执行文件位于 `dist/KnowFlow/KnowFlow.exe`

## 🗂️ 项目结构

```
KnowFlow/
├── src/                    # 核心模块
│   ├── llm_client.py      # LLM客户端（支持多提供商）
│   ├── analyzer.py        # 知识分析器
│   ├── knowledge_graph.py # 知识图谱
│   └── socratic_dialogue.py # 苏格拉底对话
├── web/                   # Web前端
│   └── index_cmd_style.html
├── api_server.py         # API服务
├── start_desktop.py      # 桌面应用启动器
├── config.yaml.example   # 配置模板
└── README.md
```

## 📄 开源协议

GNU General Public License v3.0（GPL-3.0）

允许自由使用、修改和再发布，但衍生作品必须以相同协议开源。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**问题反馈**：[GitHub Issues](https://github.com/lqn2005/KnowFlow/issues)
