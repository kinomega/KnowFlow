# KnowFlow

**English | [简体中文](./README.md)**

> **Record the trajectory of knowledge flowing through your cognition**
> This is not a document storage system — it records the complete process of how you understand knowledge.

> ⚠️ **Note**: This is a personal tool built for my own learning habits. It's open-sourced for reference and inspiration, but may not suit everyone's workflow.  
> Not a repository for storing materials, but a record of your complete process of understanding knowledge

## 💡 What is Knowledge Flow

**Knowledge Flow** differs from traditional note-taking tools:

- **Traditional Notes**: Stored and done (static)
- **Knowledge Flow**: Records how knowledge flows through your cognition (dynamic)

**Complete Knowledge Flow Cycle**:
1. **Inflow** → Standard definition + Q&A understanding → Crystallize your comprehension
2. **Circulation** → Associate similar notes → Form knowledge network
3. **Outflow** → Review thinking trajectory → Reactivate cognition

Use Q&A to crystallize your understanding, use associations to retrace your thinking.

---

## ✨ Core Features

### 🌊 Three Stages of Knowledge Flow

**📥 Inflow: From Concept to Understanding**
- Input a concept, get standard definition
- Record your understanding process through Q&A dialogue
- Store not just "what it is", but "how you understand it"

**🔄 Circulation: Dynamic Knowledge Network**
- Automatically associate similar notes (vector retrieval)
- Build concept relationship graph (parent-child, related, prerequisite)
- Dynamic centralization: form the "source" of knowledge system

**📤 Outflow: Retrace Thinking Trajectory**
- Complete record of Q&A path and thinking process
- Reactivate your understanding when reviewing
- Rethink along the trajectory, not rote memorization

### 🎯 Multi-dimensional Knowledge Model

- **Hierarchical Progression**: Explore in taxonomy-like structure, avoid repetition
- **Knowledge Graph**: Visualize concept relationship network
- **Vector Space**: Semantic similarity retrieval
- **Time Dimension**: Track learning history
- **Socratic Dialogue**: Reflective deepening of understanding

### 🔌 Universal LLM Interface
Support multiple AI providers, switch by configuration:
- **Anthropic Claude** (Official)
- **OpenAI** (GPT series)
- **DeepSeek** (Cost-effective Chinese provider)
- **Tongyi Qianwen** (Alibaba Cloud)
- **Zhipu AI** (GLM series)
- **Moonshot** (Kimi)
- **Ollama** (Local models)
- **Relay API** (Custom compatible interface)

### 📝 Dual Mode System
- **Obsidian Mode**: Connect existing Obsidian vault, bi-directional sync
- **Standalone Mode**: Independent from Obsidian, standalone notes directory

### 🔄 Bi-directional Sync
- Automatically monitor file changes
- Modifications in Obsidian sync to index in real-time
- Support manual note editing

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/lqn2005/KnowFlow.git
cd KnowFlow
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy configuration template
cp config.yaml.example config.yaml

# Edit configuration file
# Fill in your API Key and paths
notepad config.yaml  # Windows
# or vim config.yaml  # Linux/Mac
```

**Basic Configuration Example**:

```yaml
# Working mode
mode: "standalone"  # or "obsidian"

# LLM configuration
llm:
  provider: "anthropic"  # or openai / ollama
  model: "claude-sonnet-4-6"
  api_key: "your-api-key-here"
  base_url: "https://api.anthropic.com"

# Standalone mode (without Obsidian)
standalone:
  notes_path: "./notes"

# Obsidian mode (optional)
obsidian:
  vault_path: "D:/Obsidian/mine"
  target_folder: "mine"
```

### 3. Launch

**Desktop Application** (Recommended):
```bash
python start_desktop.py
```

**API Service**:
```bash
python api_server.py
# Visit http://localhost:8001
```

## 📖 Configuration Details

### LLM Provider Configuration

<details>
<summary>Click to view provider configuration examples</summary>

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

**4. Tongyi Qianwen**
```yaml
llm:
  provider: "openai"
  model: "qwen-turbo"
  api_key: "sk-..."
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

**5. Ollama (Local)**
```yaml
llm:
  provider: "ollama"
  model: "qwen2.5:7b"
  api_key: ""
  base_url: "http://localhost:11434"
```

**6. Relay API**
```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "your-key"
  base_url: "https://api.your-proxy.com/v1"
```

</details>

### Mode Selection

**Standalone Mode** (Recommended for beginners):
```yaml
mode: "standalone"
standalone:
  notes_path: "./notes"  # Notes storage directory
```

**Obsidian Mode** (For existing Obsidian users):
```yaml
mode: "obsidian"
obsidian:
  vault_path: "D:/Obsidian/mine"
  target_folder: "mine"
  watch_files: true  # Bi-directional sync
```

## 📚 Knowledge Flow Cycle: Complete Cognitive Flow Process

### 1️⃣ Inflow Stage: From Concept to Understanding

```
Input Concept → Get Standard Definition → Q&A Dialogue → Record Understanding
```

**Example**: Input "Transformer"
- 📖 System provides standard definition
- 💬 Q&A interaction: "What do you think is the core of attention mechanism?"
- 💡 Record your answer and thinking process
- 💾 Save complete understanding trajectory

### 2️⃣ Circulation Stage: Build Knowledge Network

```
New Note → Associate Similar Content → Form Knowledge Graph → Dynamic Centralization
```

- 🔗 Automatically associate existing similar notes
- 🕸️ Build concept relationship network (parent, child, prerequisite)
- 🌳 Form the "source" of knowledge system (not just points, but system)

### 3️⃣ Outflow Stage: Retrace and Rethink

```
View Note → Standard Definition + Q&A Trajectory → Reactivate Cognition
```

- 📝 See not just conclusions, but the thinking process at that time
- 🔄 Rethink along the Q&A trajectory
- 🧠 Reactivate cognition, not rote memorization

### 🎨 Visualized Knowledge Graph

- Graphically display concept relationship network
- Track learning path
- Discover knowledge gaps

## 🛠️ Tech Stack

- **Backend**: Python + FastAPI
- **LLM**: Anthropic/OpenAI/Ollama, etc.
- **Knowledge Graph**: NetworkX
- **Vector Retrieval**: ChromaDB / Simplified version (optional)
- **Frontend**: Native JS + Cytoscape.js
- **Desktop App**: pywebview
- **File Monitoring**: watchdog

## 📦 Packaging

```bash
pyinstaller knowflow.spec
```

Executable file located at `dist/KnowFlow/KnowFlow.exe`

## 🗂️ Project Structure

```
KnowFlow/
├── src/                    # Core modules
│   ├── llm_client.py      # LLM client (multi-provider support)
│   ├── analyzer.py        # Knowledge analyzer
│   ├── knowledge_graph.py # Knowledge graph
│   ├── conversation_manager.py  # Conversation manager (hierarchical progression)
│   └── ...
├── web/                   # Web frontend
│   └── index.html
├── api_server.py         # API service
├── start_desktop.py      # Desktop app launcher
├── config.yaml.example   # Configuration template
└── README.md
```

## 📄 License

GNU General Public License v3.0 (GPL-3.0)

Free to use, modify, and redistribute, but derivative works must be open-sourced under the same license.

## 🤝 Contributing

Issues and Pull Requests are welcome!

---

**Multi-dimensional Model Details**: See [多维模型实现总结.md](./多维模型实现总结.md)

**Feedback**: [GitHub Issues](https://github.com/lqn2005/KnowFlow/issues)
