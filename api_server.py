# -*- coding: utf-8 -*-
"""
KnowFlow Web API
FastAPI后端服务
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
from pathlib import Path
import sys
import os
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# 获取资源路径（支持打包后的环境）
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

# 添加src到路径
sys.path.insert(0, str(BASE_DIR / 'src'))

from src.knowledge_graph import KnowledgeGraph
from src.llm_client import LLMClient
from src.analyzer import KnowledgeAnalyzer

app = FastAPI(title="KnowFlow API")

# CORS配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（前端页面）
app.mount("/web", StaticFiles(directory=str(BASE_DIR / "web")), name="web")

# 全局实例
kg = None
llm = None
analyzer = None
# 全局配置（从config.yaml加载）
VAULT_PATH = None
TARGET_FOLDER = None
MODE = None  # 工作模式：obsidian / standalone
# 文件监听器
file_observer = None


class NoteFileHandler(FileSystemEventHandler):
    """笔记文件变化监听器"""

    def __init__(self, knowledge_graph, vault_path: Path, target_folder: str):
        self.kg = knowledge_graph
        self.vault_path = vault_path
        self.target_folder = target_folder
        self.watch_path = vault_path / target_folder

    def _is_valid_note(self, file_path: str) -> bool:
        """检查是否是有效的笔记文件"""
        if not file_path.endswith('.md'):
            return False
        # 忽略临时文件
        if any(x in file_path for x in ['.tmp', '.swp', '~']):
            return False
        return True

    def _process_note_file(self, file_path: str):
        """处理笔记文件变化"""
        try:
            note_file = Path(file_path)
            if not note_file.exists():
                return

            # 计算相对路径
            relative_path = str(note_file.relative_to(self.vault_path))

            # 读取文件内容
            content = note_file.read_text(encoding='utf-8')

            # 解析 frontmatter
            if not content.startswith('---'):
                print(f"[文件监听] 跳过无frontmatter的文件: {note_file.name}")
                return

            parts = content.split('---', 2)
            if len(parts) < 3:
                return

            import yaml
            metadata = yaml.safe_load(parts[1]) or {}

            # 提取概念信息
            concept_name = metadata.get('concept')
            if not concept_name:
                # 尝试从其他字段提取
                if 'grepro' in metadata and isinstance(metadata['grepro'], dict):
                    concept_name = metadata['grepro'].get('initial_query')
                elif 'title' in metadata:
                    concept_name = metadata['title'].replace('探索', '').replace('理解', '').strip()

            if not concept_name:
                print(f"[文件监听] 无法提取概念名: {note_file.name}")
                return

            # 生成节点ID
            concept_id = concept_name.lower().replace(' ', '_').replace('-', '')

            # 在索引中查找或创建节点
            from src.knowledge_graph import KnowledgeNode
            if concept_id in self.kg.nodes:
                # 更新已存在的节点
                node = self.kg.nodes[concept_id]
                node.note_path = relative_path
                print(f"[文件监听] 更新索引: {concept_id} -> {relative_path}")
            else:
                # 创建新节点
                node = KnowledgeNode(
                    id=concept_id,
                    name=concept_name,
                    domain=metadata.get('domain', ''),
                    depth=0,
                    learned_at=metadata.get('created', '')
                )
                node.note_path = relative_path
                self.kg.add_node(node)
                print(f"[文件监听] 新增索引: {concept_id} -> {relative_path}")

            # 持久化索引
            self.kg.save()

        except Exception as e:
            print(f"[文件监听] 处理文件失败: {file_path}, 错误: {e}")

    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return
        if self._is_valid_note(event.src_path):
            print(f"[文件监听] 检测到新文件: {Path(event.src_path).name}")
            self._process_note_file(event.src_path)

    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
        if self._is_valid_note(event.src_path):
            print(f"[文件监听] 检测到文件修改: {Path(event.src_path).name}")
            self._process_note_file(event.src_path)

    def on_deleted(self, event):
        """文件删除事件"""
        if event.is_directory:
            return
        if self._is_valid_note(event.src_path):
            try:
                note_file = Path(event.src_path)
                relative_path = str(note_file.relative_to(self.vault_path))

                # 在索引中查找对应的节点
                for node_id, node in self.kg.nodes.items():
                    if node.note_path == relative_path:
                        node.note_path = None
                        print(f"[文件监听] 移除笔记路径: {node_id}")
                        self.kg.save()
                        break

            except Exception as e:
                print(f"[文件监听] 处理删除事件失败: {event.src_path}, 错误: {e}")


# 请求模型
class ExploreRequest(BaseModel):
    concept: str
    parent_concept: Optional[str] = None
    depth: int = 0
    existing_roots: Optional[List[str]] = None
    language: str = 'zh'  # 语言设置：zh=中文，en=英文

class QuestionRequest(BaseModel):
    question: str
    context: Optional[str] = None
    concept: Optional[str] = None
    history: Optional[List[Dict]] = None
    language: str = 'zh'

class SaveNoteRequest(BaseModel):
    concept: str
    content: str
    domain: Optional[str] = None
    parent_concept: Optional[str] = None
    qa_history: Optional[List[Dict]] = None
    language: str = 'zh'


def extract_concepts_from_note(content: str) -> List[Dict]:
    """从笔记中提取相关概念列表

    解析笔记的"相关概念"部分，提取格式：
    [1] 概念名 | 领域/方向 | 类型
    简短描述
    """
    concepts = []
    lines = content.split('\n')
    current_concept = None
    in_concepts_section = False

    for line in lines:
        line_stripped = line.strip()

        # 检测相关概念章节开始
        if '## 相关概念' in line_stripped:
            in_concepts_section = True
            continue

        # 遇到下一个章节标题，停止提取
        if in_concepts_section and line_stripped.startswith('##'):
            break

        if in_concepts_section:
            # 匹配 [1] 概念名 | 领域 | 类型 格式
            if line_stripped.startswith('[') and ']' in line_stripped:
                # 保存上一个概念
                if current_concept:
                    concepts.append(current_concept)

                try:
                    # 提取完整信息
                    parts = line_stripped.split(']', 1)[1].strip()
                    current_concept = {
                        "name": parts,
                        "description": ""
                    }
                except:
                    current_concept = None
                    continue

            # 如果当前有概念且当前行不是新概念，作为描述
            elif current_concept and line_stripped and not line_stripped.startswith('['):
                if current_concept["description"]:
                    current_concept["description"] += " " + line_stripped
                else:
                    current_concept["description"] = line_stripped

    # 添加最后一个概念


def add_obsidian_links(content: str) -> str:
    """为笔记内容添加Obsidian链接格式

    在"相关概念"部分，将概念名包裹在 [[]] 中
    格式: [1] 概念名 | 领域 -> [1] [[概念名]] | 领域
    """
    lines = content.split('\n')
    result = []
    in_concepts_section = False

    for line in lines:
        line_stripped = line.strip()

        # 检测相关概念章节
        if '## 相关概念' in line_stripped or '##相关概念' in line_stripped:
            in_concepts_section = True
            result.append(line)
            continue

        # 遇到下一个章节，停止处理
        if in_concepts_section and line_stripped.startswith('##'):
            in_concepts_section = False

        # 在相关概念部分处理链接
        if in_concepts_section and line_stripped.startswith('[') and ']' in line_stripped:
            # 格式: [1] 概念名 | 领域 | 类型
            parts = line.split(']', 1)
            if len(parts) == 2:
                prefix = parts[0] + ']'
                rest = parts[1].strip()
                # 提取概念名（第一个 | 之前的部分）
                if '|' in rest:
                    concept_name = rest.split('|')[0].strip()
                    remaining = '|'.join(rest.split('|')[1:])
                    # 添加链接
                    processed_line = f"{prefix} [[{concept_name}]] | {remaining}"
                else:
                    # 没有 |，整个就是概念名
                    processed_line = f"{prefix} [[{rest}]]"
                result.append(processed_line)
                continue

        result.append(line)

    return '\n'.join(result)


def generate_tags(domain: str, concept: str) -> List[str]:
    """根据领域和概念生成标签列表

    Args:
        domain: 领域信息，如 "Transformer/推理优化"
        concept: 概念名称

    Returns:
        标签列表
    """
    tags = ["knowflow"]  # 通用标签

    # 从 domain 中提取标签
    if domain:
        # 按 / 或 - 分割
        parts = domain.replace('-', '/').split('/')
        for part in parts:
            part = part.strip()
            if part and part not in tags:
                tags.append(part)

    return tags
    if current_concept:
        concepts.append(current_concept)

    return concepts


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global kg, llm, analyzer, vector_engine, VAULT_PATH, TARGET_FOLDER, MODE, file_observer

    # 查找配置文件（兼容打包后的环境）
    config_path = None
    search_paths = [
        Path.cwd() / "config.yaml",  # 当前工作目录
        Path(__file__).parent / "config.yaml",  # 脚本所在目录
    ]

    # 如果是打包后的环境，添加 exe 所在目录
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        search_paths.insert(0, exe_dir / "config.yaml")

    for path in search_paths:
        if path.exists():
            config_path = path
            break

    if not config_path:
        error_msg = (
            "配置文件不存在！\n\n"
            "请执行以下步骤：\n"
            "1. 复制 config.yaml.example 为 config.yaml\n"
            "2. 编辑 config.yaml，填入你的 API Key 和路径\n"
            "3. 将 config.yaml 放在以下任一位置：\n"
        )
        for path in search_paths:
            error_msg += f"   - {path}\n"
        raise FileNotFoundError(error_msg)

    print(f"[INFO] 使用配置文件: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 读取工作模式
    MODE = config.get('mode', None)

    # 向后兼容：如果没有mode但有output配置，使用obsidian模式
    if MODE is None and 'output' in config:
        MODE = 'obsidian'
        print(f"[INFO] 检测到旧配置格式，使用Obsidian模式")
    elif MODE is None:
        MODE = 'obsidian'  # 默认模式

    print(f"[INFO] 工作模式: {MODE}")

    # 根据模式设置路径
    if MODE == 'obsidian':
        # Obsidian模式：关联已有的Obsidian vault
        obsidian_config = config.get('obsidian', config.get('output', {}))  # 兼容旧配置
        VAULT_PATH = Path(obsidian_config.get('vault_path', 'D:/Obsidian/mine'))
        TARGET_FOLDER = obsidian_config.get('target_folder', 'mine')
        print(f"[INFO] Obsidian vault: {VAULT_PATH}")
        print(f"[INFO] Target folder: {TARGET_FOLDER}")
    elif MODE == 'standalone':
        # 独立模式：使用独立的笔记目录
        standalone_config = config.get('standalone', {})
        notes_path = standalone_config.get('notes_path', './notes')
        VAULT_PATH = Path(notes_path)
        TARGET_FOLDER = ''  # 独立模式下不使用子文件夹
        print(f"[INFO] 笔记目录: {VAULT_PATH}")
        # 确保目录存在
        VAULT_PATH.mkdir(parents=True, exist_ok=True)
    else:
        raise ValueError(f"不支持的mode: {MODE}，请设置为 'obsidian' 或 'standalone'")

    # 加载知识图谱（使用配置中的路径）
    graph_path = VAULT_PATH / ".knowflow" / "knowledge_graph.json"
    kg = KnowledgeGraph(storage_path=graph_path)
    print(f"[OK] Knowledge graph loaded: {len(kg.nodes)} concepts")

    # 初始化LLM（从配置读取）
    llm_config = config.get('llm', {})
    llm = LLMClient(
        provider=llm_config.get('provider', 'anthropic'),
        model=llm_config.get('model', 'claude-sonnet-4-6'),
        base_url=llm_config.get('base_url', 'https://api.anthropic.com'),
        temperature=llm_config.get('temperature', 0.7),
        api_key=llm_config.get('api_key', os.getenv('ANTHROPIC_API_KEY'))
    )
    analyzer = KnowledgeAnalyzer(llm)

    # 初始化向量引擎（暂时禁用，避免网络超时阻塞启动）
    vector_engine = None
    print(f"[INFO] Vector engine disabled (network timeout)")
    # try:
    #     vector_engine = VectorEngine(
    #         vault_path="D:/Obsidian/mine",
    #         model_name="BAAI/bge-small-zh-v1.5"
    #     )
    #     print(f"[OK] Vector engine initialized")
    # except Exception as e:
    #     print(f"[WARN] Vector engine init failed: {e}")
    #     vector_engine = None

    # 启动文件监听器（双向同步）
    try:
        watch_path = VAULT_PATH / TARGET_FOLDER
        if watch_path.exists():
            event_handler = NoteFileHandler(kg, VAULT_PATH, TARGET_FOLDER)
            file_observer = Observer()
            file_observer.schedule(event_handler, str(watch_path), recursive=False)
            file_observer.start()
            print(f"[OK] File watcher started: {watch_path}")
        else:
            print(f"[WARN] Watch path does not exist: {watch_path}")
    except Exception as e:
        print(f"[WARN] Failed to start file watcher: {e}")
        file_observer = None


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    global file_observer

    # 停止文件监听器
    if file_observer:
        try:
            file_observer.stop()
            file_observer.join(timeout=5)
            print("[OK] File watcher stopped")
        except Exception as e:
            print(f"[WARN] Error stopping file watcher: {e}")


SETTINGS_PATH = None  # 在startup后初始化

def get_settings_path() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'user_settings.json'
    else:
        return BASE_DIR / 'user_settings.json'

@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "service": "KnowFlow API"}

@app.get("/api/settings")
async def get_settings():
    path = get_settings_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except:
            pass
    return {}

@app.post("/api/settings")
async def save_settings(data: dict):
    path = get_settings_path()
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return {"status": "ok"}


@app.get("/api/graph")
async def get_graph():
    """获取完整知识图谱"""
    nodes = []
    edges = []

    for node_id, node in kg.nodes.items():
        nodes.append({
            "id": node_id,
            "label": node.name,
            "domain": node.domain,
            "depth": node.depth,
            "learned_at": node.learned_at
        })

    # 从graph对象获取边
    if hasattr(kg, 'graph'):
        for source, target, data in kg.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "relation": data.get('relation', 'related')
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_concepts": len(nodes),
            "total_relations": len(edges)
        }
    }


@app.post("/api/explore")
async def explore_concept(request: ExploreRequest):
    """探索概念，推荐子概念"""
    try:
        # 1. 先查索引：模糊匹配概念名（不区分大小写）
        concept_normalized = request.concept.lower().strip().replace(' ', '').replace('-', '').replace('_', '')
        matched_node = None

        for node_id, node in kg.nodes.items():
            # 规范化节点名：转小写、去空格、去下划线
            node_name_normalized = node.name.lower().replace(' ', '').replace('-', '').replace('_', '')
            node_id_normalized = node_id.lower().replace(' ', '').replace('-', '').replace('_', '')

            # 模糊匹配：任意形式包含关系
            if (concept_normalized in node_name_normalized or
                node_name_normalized in concept_normalized or
                concept_normalized == node_id_normalized or
                concept_normalized in node_id_normalized or
                node_id_normalized in concept_normalized):
                matched_node = node
                print(f"[索引命中] {request.concept} -> {node.name} (note_path: {node.note_path})")
                break

        # 2. 如果索引命中且有笔记，直接读取
        if matched_node and matched_node.note_path:
            from pathlib import Path
            note_file = VAULT_PATH / matched_node.note_path
            if note_file.exists():
                content = note_file.read_text(encoding='utf-8')

                # 检查语言是否匹配
                note_lang = 'zh'
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        try:
                            import yaml as _yaml
                            meta = _yaml.safe_load(parts[1]) or {}
                            note_lang = meta.get('language', 'zh')
                        except:
                            pass

                if note_lang != request.language:
                    print(f"[语言不匹配] 缓存={note_lang}, 请求={request.language}, 跳过缓存")
                    matched_node = None  # 跳过，走LLM生成
                else:
                    print(f"[读取笔记] {note_file}")
                    # 去掉frontmatter（--- 之间的内容）
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            content = parts[2].strip()

                    concepts = extract_concepts_from_note(content)

                    return {
                        "success": True,
                        "analysis": content,
                        "concepts": concepts,
                        "parent_suggestion": None,
                        "from_cache": True
                    }

        # 2.5 文件系统查找笔记（不管是否匹配索引）
        from pathlib import Path
        vault_path = VAULT_PATH / TARGET_FOLDER

        if vault_path.exists():
            # 规范化概念名用于匹配（去掉空格、下划线、横杠，转小写）
            def normalize(s):
                return s.lower().replace(' ', '').replace('_', '').replace('-', '')

            concept_normalized = normalize(request.concept)

            note_file = None
            best_match_score = 0

            # 遍历所有md文件，找到最佳匹配
            for md_file in vault_path.glob("*.md"):
                filename = md_file.stem  # 不含扩展名

                # 语言过滤：文件名后缀 _zh / _en，或读frontmatter
                file_lang = 'zh'
                if filename.endswith('_en'):
                    file_lang = 'en'
                elif filename.endswith('_zh'):
                    file_lang = 'zh'
                else:
                    # 旧文件无后缀，读frontmatter
                    try:
                        raw = md_file.read_text(encoding='utf-8')
                        if raw.startswith('---'):
                            _parts = raw.split('---', 2)
                            if len(_parts) >= 3:
                                import yaml as _yaml
                                _meta = _yaml.safe_load(_parts[1]) or {}
                                file_lang = _meta.get('language', 'zh')
                    except:
                        pass

                if file_lang != request.language:
                    continue
                filename = md_file.stem  # 不含扩展名
                # 提取第一个下划线或空格之前的部分作为概念名
                file_concept = filename.split('_')[0].replace(' ', '')
                file_concept_normalized = normalize(file_concept)

                # 计算匹配度
                score = 0
                if file_concept_normalized == concept_normalized:
                    score = 100  # 精确匹配
                elif concept_normalized in file_concept_normalized:
                    score = 80  # 概念包含在文件名中
                elif file_concept_normalized in concept_normalized:
                    score = 60  # 文件名包含在概念中

                # 同时匹配完整文件名（处理 KV_Cache_test 这种情况）
                filename_normalized = normalize(filename.split('_test')[0].split('_探索')[0].split('_理解')[0])
                if filename_normalized == concept_normalized:
                    score = max(score, 90)
                elif concept_normalized in filename_normalized:
                    score = max(score, 70)
                elif filename_normalized in concept_normalized:
                    score = max(score, 50)

                if score > best_match_score:
                    best_match_score = score
                    note_file = md_file

            if note_file and best_match_score >= 50:
                try:
                    print(f"[文件系统查找] 概念'{request.concept}' -> {note_file} (score={best_match_score})")
                    content = note_file.read_text(encoding='utf-8')

                    # 去掉frontmatter
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            content = parts[2].strip()

                    # 从笔记中提取子概念
                    concepts = extract_concepts_from_note(content)

                    return {
                        "success": True,
                        "analysis": content,
                        "concepts": concepts,
                        "parent_suggestion": None,
                        "from_cache": True
                    }
                except Exception as e:
                    print(f"[错误] 读取笔记失败: {e}")

        # 3. 未命中或无笔记，调用LLM生成
        print(f"[LLM生成] {request.concept}")
        result = analyzer.analyze_keywords(
            keywords=request.concept,
            mode="overview",
            explored_concepts=request.existing_roots or [],  # 修复：使用前端传递的已探索概念
            parent_concept=request.parent_concept,
            depth=request.depth,
            language=request.language  # 传递语言参数
        )

        # 从返回的markdown中提取概念列表
        concepts = []
        if result:
            # 调试：输出LLM返回的原始内容
            print("\n" + "="*60)
            print("[DEBUG] LLM返回的原始内容：")
            print(result)
            print("="*60 + "\n")

            lines = result.split('\n')
            current_concept = None

            for line in lines:
                line = line.strip()

                # 匹配 [1] 概念名 | 领域/方向 | 类型 格式
                if line.startswith('[') and ']' in line:
                    # 保存上一个概念
                    if current_concept:
                        print(f"[DEBUG] 保存概念: {current_concept['name'][:50]}... | 描述: {current_concept['description'][:100] if current_concept['description'] else '(空)'}")
                        concepts.append(current_concept)

                    try:
                        # 提取完整的概念信息（保留所有|分隔的内容）
                        parts = line.split(']', 1)[1].strip()
                        current_concept = {
                            "name": parts,  # 保留完整的 "概念 | 领域 | 类型"
                            "description": ""  # 描述在下一行
                        }
                        print(f"[DEBUG] 发现新概念: {parts[:50]}...")
                    except:
                        current_concept = None
                        continue

                # 如果当前有概念且当前行不是新概念，则作为描述
                elif current_concept and line and not line.startswith('['):
                    # 跳过markdown标题行（## 相关概念 等）
                    if line.startswith('#'):
                        continue
                    if current_concept["description"]:
                        current_concept["description"] += " " + line
                    else:
                        current_concept["description"] = line
                    print(f"[DEBUG] 添加描述片段: {line[:80]}...")

            # 添加最后一个概念
            if current_concept:
                print(f"[DEBUG] 保存最后一个概念: {current_concept['name'][:50]}... | 描述: {current_concept['description'][:100] if current_concept['description'] else '(空)'}")
                concepts.append(current_concept)

            print(f"\n[DEBUG] 最终提取到 {len(concepts)} 个概念\n")

        # 判断是否应该归类到已有根节点（双向判断）
        parent_suggestion = None
        children_suggestions = []

        if request.existing_roots and not request.parent_concept and len(request.existing_roots) > 0:
            try:
                # 1. 正向判断：新概念是否属于已有根节点的子概念？
                roots_list = "、".join(request.existing_roots)
                forward_prompt = f"""概念：{request.concept}
已有根节点：{roots_list}

请判断"{request.concept}"是否属于上述某个根节点的子概念或相关概念。

如果属于，返回最合适的父节点名称（只返回节点名，不要有其他文字）。
如果不属于任何一个，返回"NONE"。

判断依据：
- 是否是某个根节点的具体实例、子类、应用场景
- 是否与某个根节点有强相关性
- 优先选择最具体、最相关的父节点

你的判断："""

                forward_result = llm.generate(forward_prompt, system_prompt="你是分类专家，简洁准确。")

                if forward_result:
                    forward_result = forward_result.strip()
                    if forward_result != "NONE" and forward_result in request.existing_roots:
                        parent_suggestion = forward_result
                        print(f"[LLM归类-正向] {request.concept} -> {parent_suggestion}")

                # 2. 反向判断：如果没有找到父节点，判断已有根节点是否应该归类到新概念下
                if not parent_suggestion:
                    reverse_prompt = f"""概念：{request.concept}
已有根节点：{roots_list}

请判断上述根节点中，哪些应该归类为"{request.concept}"的子概念。

判断依据：
- "{request.concept}"是否是一个更宽泛、更上层的概念
- 某个根节点是否是"{request.concept}"的具体实例、子类、应用
- 只选择明确属于"{request.concept}"的根节点

返回格式：如果有，返回节点名，多个用逗号分隔；如果没有，返回"NONE"。
例如："神经网络,深度学习" 或 "NONE"

你的判断："""

                    reverse_result = llm.generate(reverse_prompt, system_prompt="你是分类专家，简洁准确。")

                    if reverse_result:
                        reverse_result = reverse_result.strip()
                        if reverse_result != "NONE":
                            # 解析返回的节点名列表
                            suggested_children = [name.strip() for name in reverse_result.split(',')]
                            # 验证是否都是有效的根节点
                            children_suggestions = [name for name in suggested_children if name in request.existing_roots]
                            if children_suggestions:
                                print(f"[LLM归类-反向] {', '.join(children_suggestions)} -> {request.concept}")

            except Exception as e:
                print(f"LLM判断层级关系失败: {e}")

        return {
            "success": True,
            "analysis": result or "",
            "concepts": concepts,
            "parent_suggestion": parent_suggestion,
            "children_suggestions": children_suggestions
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/question")
async def ask_question(request: QuestionRequest):
    """快速提问 - 苏格拉底式对话"""
    try:
        # 调试：打印收到的请求
        print(f"\n[DEBUG] 收到问题: {request.question}")
        print(f"[DEBUG] 概念: {request.concept}")
        print(f"[DEBUG] 历史记录数: {len(request.history) if request.history else 0}")
        if request.history:
            for i, h in enumerate(request.history):
                print(f"[DEBUG] 历史{i+1} - 问题: {h.get('question', '')[:50]}...")
                print(f"[DEBUG] 历史{i+1} - 回答: {h.get('answer', '')[:50]}...")

        # 检测输入是否为空或非问题
        is_empty_or_not_question = (
            not request.question.strip() or
            len(request.question.strip()) < 2
        )

        # 构建对话历史文本
        history_text = ""
        if request.history and len(request.history) > 0:
            history_text = "\n\n## 对话历史：\n"
            for i, qa in enumerate(request.history, 1):
                history_text += f"\n第{i}轮：\n"
                history_text += f"你的问题：{qa.get('question', '（让用户主动思考）')}\n"
                history_text += f"用户回答：{qa.get('answer', '（无回答）')}\n"

        lang_instruction = "\n\nIMPORTANT: Respond in English only." if request.language == 'en' else ""

        # 构建提示词
        if request.concept:
            # 针对特定概念的问答
            if is_empty_or_not_question:
                # 输入为空或非问题时，AI主动提问
                system_prompt = f"""你是知识探索助手，正在用苏格拉底式对话帮助用户理解"{request.concept}"这个概念。

用户刚刚开始探索这个概念，或者想让你主动引导。请你提出1-2个启发性问题，帮助用户思考。

问题要求：
1. 基于"{request.concept}"的核心概念
2. 由浅入深，从用户的认知出发
3. 开放性问题，引发思考而非简单回答是/否
4. 具体、有针对性

示例：
- "你之前接触过类似的概念吗？有什么印象？"
- "你觉得{request.concept}主要解决什么问题？"
- "从字面意思看，{request.concept}让你联想到什么？"{lang_instruction}
"""
                prompt = f"用户想深入了解'{request.concept}'，请主动提出引导性问题。"
            else:
                # 用户提出了问题或回答，正常回应
                system_prompt = f"""你是知识探索助手，正在用苏格拉底式对话帮助用户理解"{request.concept}"这个概念。

核心原则：
1. 通过提问引导用户思考，而不是直接给答案
2. 根据用户的回答逐步深入
3. 一次只问1-2个关键问题
4. 问题要具体、有针对性

**重要**：如果用户的输入很简短（比如"1"、"是的"、"对"、单个字母/数字等），说明他们在回答你之前提出的问题。你需要：
- 先简要回应他们的回答，表示理解
- 根据他们的回答继续追问，引导更深入的思考
- 不要重新开始提问，而是基于对话历史继续深入

如果用户提出了完整的新问题，则正常引导他们思考。{lang_instruction}
"""
                prompt = request.question
        else:
            system_prompt = f"你是知识探索助手。用苏格拉底式对话引导用户思考，通过提问启发而不是直接给答案。{lang_instruction}"
            prompt = request.question

        # 将对话历史添加到prompt开头
        if history_text:
            prompt = history_text + f"\n\n## 用户当前回复：\n{prompt}"

        # 添加上下文
        if request.context and not is_empty_or_not_question and not history_text:
            prompt = f"{request.context}\n\n用户：{request.question}"

        # 调用LLM
        response = llm.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )

        if response:
            return {
                "success": True,
                "answer": response
            }
        else:
            return {
                "success": False,
                "error": "LLM生成失败"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }




def _find_root_concept(concept: str) -> str:
    """沿 parent 链找到根概念名"""
    concept_id = concept.lower().replace(' ', '_')
    visited = set()
    while concept_id in kg.nodes:
        node = kg.nodes[concept_id]
        if not node.parent or node.parent in visited:
            return node.name
        visited.add(concept_id)
        concept_id = node.parent
    return concept


def _safe_dirname(name: str) -> str:
    for ch in r'/\|:*?"<>':
        name = name.replace(ch, '_')
    return name.strip()


def _index_path() -> Path:
    return VAULT_PATH / "knowflow_index.json"


def _load_index() -> dict:
    p = _index_path()
    if p.exists():
        try:
            import json as _json
            return _json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {"nodes": {}}


def _save_index(index: dict):
    from datetime import datetime
    import json as _json
    index["updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _index_path().write_text(_json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')


@app.post("/api/save")
async def save_note(request: SaveNoteRequest):
    """保存笔记，根据模式决定目录结构"""
    try:
        from datetime import datetime
        from pathlib import Path

        safe_name = _safe_dirname(request.concept)
        lang_suffix = f"_{request.language}" if request.language else "_zh"

        if MODE == 'standalone':
            # 找根概念作为目录名
            root_name = _find_root_concept(request.concept)
            root_dir = _safe_dirname(root_name)
            save_dir = VAULT_PATH / root_dir
            save_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{safe_name}{lang_suffix}.md"
            note_path = save_dir / filename
            relative_path = f"{root_dir}/{filename}"
            # standalone 模式不加 Obsidian 双链
            processed_content = request.content

            # 追加模式：读取旧文件的问答历史合并
            existing_qa = []
            if note_path.exists():
                try:
                    old_content = note_path.read_text(encoding='utf-8')
                    if '## 💬 问答历史' in old_content:
                        qa_section_start = old_content.index('## 💬 问答历史')
                        qa_text = old_content[qa_section_start:]
                        rounds = qa_text.split('### 第')
                        for r in rounds[1:]:
                            lines = r.strip().split('\n')
                            q_text, a_text = '', ''
                            for line in lines:
                                if line.startswith('**Q**:'):
                                    q_text = line[6:].strip()
                                elif line.startswith('**A**:'):
                                    a_text = line[6:].strip()
                            if q_text or a_text:
                                existing_qa.append({'question': q_text, 'answer': a_text})
                except Exception:
                    pass
        else:
            # obsidian 模式：保持原目录逻辑，加双链
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_{timestamp}{lang_suffix}.md"
            vault_path = VAULT_PATH / TARGET_FOLDER
            vault_path.mkdir(parents=True, exist_ok=True)
            note_path = vault_path / filename
            relative_path = f"{TARGET_FOLDER}/{filename}" if TARGET_FOLDER else filename
            processed_content = add_obsidian_links(request.content)

        # 问答历史（standalone 追加旧记录，obsidian 只用当前会话）
        current_qa = request.qa_history or []
        if MODE == 'standalone' and existing_qa:
            # 去重：旧记录里已有的轮次不重复追加
            existing_questions = {qa['question'] for qa in existing_qa}
            new_qa = [qa for qa in current_qa if qa.get('question') not in existing_questions]
            merged_qa = existing_qa + new_qa
        else:
            merged_qa = current_qa

        qa_section = ""
        if merged_qa:
            qa_section = "\n\n## 💬 问答历史\n\n"
            for i, qa in enumerate(merged_qa, 1):
                qa_section += f"### 第{i}轮\n"
                qa_section += f"**Q**: {qa.get('question', '')}\n\n"
                qa_section += f"**A**: {qa.get('answer', '')}\n\n"

        # frontmatter
        frontmatter_lines = [
            "---",
            f"concept: {request.concept}",
            f"language: {request.language}",
        ]
        if request.parent_concept:
            frontmatter_lines.append(f"parent: {request.parent_concept}")
        if request.domain:
            frontmatter_lines.append(f"domain: {request.domain}")
        frontmatter_lines.extend([
            f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "---",
            ""
        ])
        frontmatter = "\n".join(frontmatter_lines)

        note_path.write_text(frontmatter + processed_content + qa_section, encoding='utf-8')
        print(f"[保存笔记] {note_path}")

        # 更新 knowledge_graph 索引
        concept_id = request.concept.lower().replace(' ', '_')
        if concept_id in kg.nodes:
            kg.nodes[concept_id].note_path = relative_path
            print(f"[更新索引] {concept_id} -> {relative_path}")
        else:
            from src.knowledge_graph import KnowledgeNode
            node = KnowledgeNode(
                concept_id=concept_id,
                name=request.concept,
                domain=request.domain or "",
                depth=0,
                learned_at=datetime.now().isoformat()
            )
            node.note_path = relative_path
            kg.add_node(node)
            print(f"[新增索引] {concept_id} -> {relative_path}")

        kg.save()

        # 更新 knowflow_index.json
        try:
            index = _load_index()
            nodes = index.setdefault("nodes", {})
            concept_key = request.concept
            if concept_key not in nodes:
                nodes[concept_key] = {}
            nodes[concept_key].update({
                "file": relative_path,
                "parent": request.parent_concept,
                "created": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "language": request.language,
                "domain": request.domain or ""
            })
            # 维护父子关系
            if request.parent_concept:
                parent_node = nodes.setdefault(request.parent_concept, {})
                kids = parent_node.setdefault("children", [])
                if concept_key not in kids:
                    kids.append(concept_key)
            # 清理自己 children 里可能重复的（避免循环）
            if concept_key in nodes:
                nodes[concept_key].pop("children", None)
                # 重新加（保持最新）
            _save_index(index)
        except Exception as e:
            print(f"[索引更新失败] {e}")

        return {
            "success": True,
            "note_path": str(note_path),
            "relative_path": relative_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/notes")
async def get_saved_notes(language: str = 'zh'):
    """获取已保存的笔记列表（优先读索引，降级扫文件）"""
    try:
        from pathlib import Path
        import json as _json

        vault_path = VAULT_PATH / TARGET_FOLDER
        if not vault_path.exists():
            return {"success": True, "notes": [], "total": 0}

        # 优先从索引读取
        index = _load_index()
        nodes = index.get("nodes", {})
        if nodes:
            notes = []
            for name, info in nodes.items():
                if info.get("language", "zh") != language:
                    continue
                note_id = name.lower().replace(' ', '_').replace('-', '')
                notes.append({
                    "id": note_id,
                    "name": name,
                    "domain": info.get("domain", ""),
                    "depth": 0,
                    "learned_at": info.get("created", ""),
                    "children": [],
                    "parent_name": info.get("parent"),
                    "file_path": info.get("file", ""),
                    "qa_history": []
                })

            # 按 parent 重建树
            note_map = {n['id']: n for n in notes}
            name_to_id = {n['name']: n['id'] for n in notes}
            roots = []
            for note in notes:
                parent_name = note.pop('parent_name', None)
                if parent_name:
                    parent_id = name_to_id.get(parent_name) or parent_name.lower().replace(' ', '_').replace('-', '')
                    if parent_id in note_map:
                        note_map[parent_id]['children'].append(note)
                    else:
                        roots.append(note)
                else:
                    roots.append(note)

            return {"success": True, "notes": roots, "total": len(notes)}

        # 索引为空：降级扫文件并重建索引
        import yaml
        notes = []
        rebuilt_index = {"nodes": {}}

        for note_file in vault_path.glob("*.md"):
            try:
                with open(note_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                metadata = {}
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        try:
                            metadata = yaml.safe_load(parts[1]) or {}
                        except:
                            pass

                note_lang = metadata.get('language', 'zh')
                if note_lang != language:
                    continue

                qa_history = []
                if '## 💬 问答历史' in content:
                    try:
                        qa_section_start = content.index('## 💬 问答历史')
                        qa_section = content[qa_section_start:]
                        rounds = qa_section.split('### 第')
                        for round_text in rounds[1:]:
                            try:
                                if '**Q**:' in round_text and '**A**:' in round_text:
                                    q_start = round_text.index('**Q**:') + 6
                                    a_start = round_text.index('**A**:')
                                    a_content_start = a_start + 6
                                    question = round_text[q_start:a_start].strip()
                                    answer_part = round_text[a_content_start:]
                                    answer = answer_part.split('###')[0].strip()
                                    qa_history.append({'question': question, 'answer': answer})
                            except Exception as e:
                                print(f"[警告] 解析单轮问答失败: {e}")
                                continue
                    except Exception as e:
                        print(f"[警告] 解析问答历史失败: {e}")

                concept_name = None
                if 'concept' in metadata:
                    concept_name = metadata['concept']
                elif 'grepro' in metadata and isinstance(metadata['grepro'], dict):
                    concept_name = metadata['grepro'].get('initial_query')
                elif 'title' in metadata:
                    concept_name = metadata['title'].replace('探索', '').replace('理解', '').strip()

                if concept_name:
                    note_id = concept_name.lower().replace(' ', '_').replace('-', '')
                    if not any(n['id'] == note_id for n in notes):
                        notes.append({
                            "id": note_id,
                            "name": concept_name,
                            "domain": metadata.get('domain', ''),
                            "depth": 0,
                            "learned_at": metadata.get('created', ''),
                            "children": [],
                            "parent_name": metadata.get('parent', None),
                            "file_path": str(note_file.relative_to(vault_path.parent)),
                            "qa_history": qa_history
                        })
                        # 重建索引条目
                        rebuilt_index["nodes"][concept_name] = {
                            "file": str(note_file.relative_to(vault_path.parent)),
                            "parent": metadata.get('parent'),
                            "created": metadata.get('created', ''),
                            "language": note_lang,
                            "domain": metadata.get('domain', '')
                        }
            except Exception as e:
                print(f"[警告] 解析笔记失败 {note_file}: {e}")
                continue

        notes.sort(key=lambda x: x['learned_at'] or '', reverse=True)

        note_map = {n['id']: n for n in notes}
        roots = []
        for note in notes:
            parent_name = note.pop('parent_name', None)
            if parent_name:
                parent_id = parent_name.lower().replace(' ', '_').replace('-', '')
                if parent_id in note_map:
                    note_map[parent_id]['children'].append(note)
                else:
                    roots.append(note)
            else:
                roots.append(note)

        # 重建父子关系进索引
        for name, info in rebuilt_index["nodes"].items():
            parent_name = info.get("parent")
            if parent_name and parent_name in rebuilt_index["nodes"]:
                kids = rebuilt_index["nodes"][parent_name].setdefault("children", [])
                if name not in kids:
                    kids.append(name)

        if rebuilt_index["nodes"]:
            _save_index(rebuilt_index)

        return {"success": True, "notes": roots, "total": len(notes)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    domains = {}
    for node in kg.nodes.values():
        domain = node.domain or "未分类"
        domains[domain] = domains.get(domain, 0) + 1

    return {
        "total_concepts": len(kg.nodes),
        "total_relations": len(kg.edges),
        "domains": domains
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接（用于实时对话）"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "explore":
                # 处理探索请求
                concept = message["concept"]
                response = analyzer.analyze_keywords(
                    keywords=concept,
                    mode="overview"
                )
                await websocket.send_json({
                    "type": "explore_result",
                    "data": response
                })

            elif message["type"] == "question":
                # 处理提问
                question = message["question"]
                answer = llm.generate(
                    prompt=question,
                    system_prompt="你是知识探索助手。"
                )
                await websocket.send_json({
                    "type": "answer",
                    "data": answer or "生成失败"
                })

    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
