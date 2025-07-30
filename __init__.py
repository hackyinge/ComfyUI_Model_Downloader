# ComfyUI Model Downloader Plugin
# 基于aria2c实现多线程下载ComfyUI模型

import os
import sys
import subprocess
import platform
import folder_paths
import shutil
import threading
import time
import json
from pathlib import Path

from .model_downloader import ModelDownloader

NODE_CLASS_MAPPINGS = {
    "ModelDownloaderNode": ModelDownloader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ModelDownloaderNode": "Model Downloader"
}

# 获取当前文件所在目录
WEB_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web")

# 注册web目录，使ComfyUI能够加载我们的JavaScript文件
def get_web_directories():
    return [WEB_DIRECTORY]

# API路由处理
from server import PromptServer

@PromptServer.instance.routes.post("/model_downloader/download")
async def api_download_model(request):
    try:
        json_data = await request.json()
        url = json_data.get("url", "")
        model_dir = json_data.get("model_dir", "")
        custom_path = json_data.get("custom_path", "")
        subfolder = json_data.get("subfolder", "")
        use_mirror = json_data.get("use_mirror", "no")
        threads = json_data.get("threads", 16)
        
        if not url:
            return PromptServer.instance.create_response(status=400, content_type="application/json", 
                                                      content=json.dumps({"error": "URL不能为空"}))
        
        # 创建下载器实例
        downloader = ModelDownloader()
        
        # 获取模型目录信息
        model_dirs = {}
        base_path = folder_paths.models_dir
        
        # 遍历models目录下的所有文件夹
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                model_dirs[item] = item_path
        
        # 添加自定义节点中的模型目录
        custom_nodes_path = os.path.join(os.path.dirname(base_path), "custom_nodes")
        if os.path.exists(custom_nodes_path):
            for node_dir in os.listdir(custom_nodes_path):
                node_path = os.path.join(custom_nodes_path, node_dir)
                if os.path.isdir(node_path):
                    node_models_path = os.path.join(node_path, "models")
                    if os.path.exists(node_models_path) and os.path.isdir(node_models_path):
                        model_dirs[f"custom_nodes/{node_dir}/models"] = node_models_path
        
        # 在新线程中启动下载，避免阻塞API响应
        download_thread = threading.Thread(
            target=downloader.download_model,
            args=(url, model_dir, custom_path, subfolder, use_mirror, threads, json.dumps(model_dirs))
        )
        download_thread.daemon = True
        download_thread.start()
        
        return PromptServer.instance.create_response(status=200, content_type="application/json", 
                                                  content=json.dumps({"status": "下载已开始"}))
    except Exception as e:
        return PromptServer.instance.create_response(status=500, content_type="application/json", 
                                                  content=json.dumps({"error": str(e)}))

@PromptServer.instance.routes.get("/model_downloader/status")
async def api_get_download_status(request):
    try:
        status = ModelDownloader.get_download_status()
        return PromptServer.instance.create_response(status=200, content_type="application/json", 
                                                  content=json.dumps(status))
    except Exception as e:
        return PromptServer.instance.create_response(status=500, content_type="application/json", 
                                                  content=json.dumps({"error": str(e)}))

@PromptServer.instance.routes.get("/model_downloader/get_model_dirs")
async def api_get_model_dirs(request):
    try:
        model_dirs = []
        base_path = folder_paths.models_dir
        
        # 遍历models目录下的所有文件夹
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                model_dirs.append(item)
        
        # 添加自定义节点中的模型目录
        custom_nodes_path = os.path.join(os.path.dirname(base_path), "custom_nodes")
        if os.path.exists(custom_nodes_path):
            for node_dir in os.listdir(custom_nodes_path):
                node_path = os.path.join(custom_nodes_path, node_dir)
                if os.path.isdir(node_path):
                    node_models_path = os.path.join(node_path, "models")
                    if os.path.exists(node_models_path) and os.path.isdir(node_models_path):
                        model_dirs.append(f"custom_nodes/{node_dir}/models")
        
        return PromptServer.instance.create_response(status=200, content_type="application/json", 
                                                  content=json.dumps({"model_dirs": model_dirs}))
    except Exception as e:
        return PromptServer.instance.create_response(status=500, content_type="application/json", 
                                                  content=json.dumps({"error": str(e)}))

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'get_web_directories']