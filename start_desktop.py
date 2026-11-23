# -*- coding: utf-8 -*-
"""
KnowFlow 桌面应用启动器
双击运行即可打开桌面应用
"""
import webview
import threading
import uvicorn
import time
import sys
import os
import requests
from pathlib import Path

# 获取资源路径（支持打包后的环境）
def get_resource_path(relative_path):
    """获取资源文件的绝对路径（兼容打包后的环境）"""
    if getattr(sys, 'frozen', False):
        # 运行在打包后的exe中
        base_path = sys._MEIPASS
    else:
        # 运行在开发环境
        base_path = Path(__file__).parent
    return os.path.join(base_path, relative_path)

def check_and_create_config():
    """检查config.yaml是否存在，不存在则从模板创建"""
    if getattr(sys, 'frozen', False):
        # 打包环境：config.yaml应该在exe同目录
        config_path = Path(sys.executable).parent / 'config.yaml'
        example_path = Path(get_resource_path('config.yaml.example'))
    else:
        # 开发环境
        config_path = Path(__file__).parent / 'config.yaml'
        example_path = Path(__file__).parent / 'config.yaml.example'

    if not config_path.exists():
        try:
            if example_path.exists():
                import shutil
                shutil.copy(example_path, config_path)

                # 使用GUI对话框显示提示
                if getattr(sys, 'frozen', False):
                    msg = (
                        "首次运行检测\n\n"
                        f"已创建配置文件:\n{config_path}\n\n"
                        "请按以下步骤配置:\n"
                        "1. 用文本编辑器打开 config.yaml\n"
                        "2. 将 'your-api-key-here' 替换为你的真实API Key\n"
                        "3. 根据需要修改其他配置\n"
                        "4. 保存后重新启动程序"
                    )
                    try:
                        import webview
                        # 创建临时窗口显示消息
                        webview.create_window('KnowFlow - 首次配置', html=f'<html><body style="font-family: Arial; padding: 20px;"><pre>{msg}</pre></body></html>', width=600, height=400)
                        webview.start()
                    except:
                        # 如果webview失败，创建文本文件
                        readme_path = Path(sys.executable).parent / 'README_CONFIG.txt'
                        with open(readme_path, 'w', encoding='utf-8') as f:
                            f.write(msg)
                return False
            else:
                if getattr(sys, 'frozen', False):
                    try:
                        import webview
                        webview.create_window('KnowFlow - 错误', html='<html><body><h3>错误</h3><p>找不到配置模板文件</p></body></html>', width=400, height=200)
                        webview.start()
                    except:
                        pass
                return False
        except Exception as e:
            if getattr(sys, 'frozen', False):
                try:
                    import webview
                    webview.create_window('KnowFlow - 错误', html=f'<html><body><h3>创建配置文件失败</h3><p>{e}</p></body></html>', width=400, height=200)
                    webview.start()
                except:
                    pass
            return False

    # 检查配置文件是否包含占位符（未配置）
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'your-api-key-here' in content:
                if getattr(sys, 'frozen', False):
                    msg = (
                        "配置未完成\n\n"
                        f"请编辑配置文件:\n{config_path}\n\n"
                        "将 'your-api-key-here' 替换为你的真实API Key"
                    )
                    try:
                        import webview
                        webview.create_window('KnowFlow - 配置提示', html=f'<html><body style="font-family: Arial; padding: 20px;"><pre>{msg}</pre></body></html>', width=500, height=300)
                        webview.start()
                    except:
                        pass
                return False
    except Exception as e:
        pass

    return True

# 添加src到路径
src_path = get_resource_path('src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 切换工作目录到资源目录（让api_server能找到web目录）
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

def start_server():
    """后台启动FastAPI服务器"""
    log_file = Path("server_error.log")
    try:
        # 记录启动尝试
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] 开始启动服务器...\n")

        from api_server import app

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] api_server导入成功\n")

        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")
    except Exception as e:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] 服务器启动失败: {e}\n")
            import traceback
            f.write(traceback.format_exc())

def wait_for_server(url, timeout=15):
    """等待服务器启动"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return True
        except:
            time.sleep(0.5)
    return False

if __name__ == '__main__':
    # 检查并创建配置文件
    if not check_and_create_config():
        sys.exit(0)

    print("=" * 60)
    print("KnowFlow - 知识探索系统")
    print("=" * 60)
    print("\n正在启动服务器...")

    # 启动服务器线程
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等待服务器就绪
    if wait_for_server('http://127.0.0.1:8001'):
        print("[OK] 服务器启动成功")
        print("[OK] 正在打开窗口...\n")

        # 创建桌面窗口
        window = webview.create_window(
            'KnowFlow - 知识探索系统',
            'http://127.0.0.1:8001/web/index_cmd_style.html',
            width=1400,
            height=900,
            resizable=True,
            min_size=(1000, 600)
        )

        webview.start()
        print("\n应用已关闭")
    else:
        print("[ERROR] 服务器启动失败！")
        print("\n可能的原因：")
        print("  1. 端口8001被占用")
        print("  2. config.yaml不存在或配置错误")
        print("  3. API Key配置错误")
        # 打包后的环境中可能没有stdin，不要使用input()
        if not getattr(sys, 'frozen', False):
            input("\n按Enter键退出...")
        else:
            time.sleep(5)  # 延迟5秒让用户看到错误信息
