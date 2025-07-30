import os
import sys
import subprocess
import platform
import threading
import json
import re
import time
from pathlib import Path

import folder_paths
from server import PromptServer
import numpy as np

class ModelDownloader:
    @classmethod
    def INPUT_TYPES(cls):
        # 获取ComfyUI模型目录结构
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
        
        # 将目录列表转换为ComfyUI下拉菜单格式
        model_dir_choices = list(model_dirs.keys())
        
        return {
            "required": {
                "url": ("STRING", {
                    "multiline": True,
                    "default": "https://huggingface.co/..."
                }),
                "model_dir": (["custom"] + model_dir_choices, ),
                "custom_path": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "subfolder": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "use_mirror": (["yes", "no"], ),
                "threads": ("INT", {
                    "default": 16,
                    "min": 1,
                    "max": 32,
                    "step": 1
                }),
            },
            "hidden": {"model_dirs": json.dumps(model_dirs)},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "download_model"
    CATEGORY = "下载"
    
    @classmethod
    def IS_CHANGED(cls):
        # 返回当前时间戳，确保节点状态会更新
        return time.time()

    def download_model(self, url, model_dir, custom_path, subfolder, use_mirror, threads, model_dirs=None):
        # If model_dirs is None, get it from INPUT_TYPES
        if model_dirs is None:
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
            model_dirs = json.dumps(model_dirs)
        # 检查aria2c是否可用
        aria2c_path = ModelDownloader._get_aria2c_path()
        if not aria2c_path:
            return ("错误: 未找到aria2c。请安装aria2c后再试。", )
        
        # 处理URL
        if use_mirror == "yes":
            url = url.replace("huggingface.co", "hf-mirror.com")
        
        # 确定保存路径
        if model_dir == "custom":
            if not custom_path:
                return ("错误: 选择自定义路径时，必须提供有效的路径。", )
            save_path = custom_path
        else:
            model_dirs_dict = json.loads(model_dirs)
            save_path = model_dirs_dict.get(model_dir, "")
            if not save_path:
                return (f"错误: 无法找到模型目录 '{model_dir}'。", )
        
        # 如果提供了子文件夹名称，则在保存路径中添加子文件夹
        if subfolder and subfolder.strip():
            save_path = os.path.join(save_path, subfolder.strip())
        
        # 确保目录存在
        os.makedirs(save_path, exist_ok=True)
        
        # 从URL中提取文件名
        filename = os.path.basename(url)
        if not filename:
            return ("错误: 无法从URL中提取文件名。", )
        
        # 完整的保存路径
        full_save_path = os.path.join(save_path, filename)
        
        # 更新初始状态信息
        status_message = f"开始下载: {url}\n保存到: {full_save_path}\n使用 {threads} 个线程下载中..."
        # 输出日志到控制台
        print(f"下载状态: {status_message}")
        
        # 直接调用下载方法并获取结果
        result = self._download_with_aria2c(aria2c_path, url, save_path, filename, threads, use_mirror)
        
        # 返回下载结果
        return (result, )

    @classmethod
    def _get_aria2c_path(cls):
        """检查aria2c是否已安装并返回路径"""
        try:
            # 在Windows上，我们需要检查aria2c.exe
            if platform.system() == "Windows":
                aria2c_name = "aria2c.exe"
                # 首先检查指定的aria2c目录
                bundled_aria2c_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria2-1.37.0-win-64bit")
                bundled_aria2c_path = os.path.join(bundled_aria2c_dir, aria2c_name)
                if os.path.exists(bundled_aria2c_path):
                    return bundled_aria2c_path
                
                # 然后检查当前目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                aria2c_path = os.path.join(current_dir, aria2c_name)
                if os.path.exists(aria2c_path):
                    return aria2c_path
                
                # 最后检查PATH环境变量中的aria2c
                for path in os.environ["PATH"].split(os.pathsep):
                    exe_path = os.path.join(path, aria2c_name)
                    if os.path.exists(exe_path):
                        return exe_path
                return None
            else:
                # 在Linux/Mac上，使用which命令查找aria2c
                result = subprocess.run(["which", "aria2c"], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE, 
                                        text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
                
                # 如果没找到aria2c，尝试安装
                print("未找到aria2c，尝试自动安装...")
                try:
                    if platform.system() == "Linux":
                        # 尝试使用apt安装
                        print("尝试使用apt安装aria2...")
                        subprocess.run(["sudo", "apt", "update"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
                        result = subprocess.run(["sudo", "apt", "install", "-y", "aria2"], 
                                              stdout=subprocess.PIPE, 
                                              stderr=subprocess.PIPE)
                        if result.returncode == 0:
                            print("aria2c安装成功！")
                            # 再次检查aria2c
                            result = subprocess.run(["which", "aria2c"], 
                                                  stdout=subprocess.PIPE, 
                                                  stderr=subprocess.PIPE, 
                                                  text=True)
                            if result.returncode == 0:
                                return result.stdout.strip()
                    elif platform.system() == "Darwin":  # macOS
                        # 尝试使用brew安装
                        print("尝试使用Homebrew安装aria2...")
                        result = subprocess.run(["brew", "install", "aria2"], 
                                              stdout=subprocess.PIPE, 
                                              stderr=subprocess.PIPE)
                        if result.returncode == 0:
                            print("aria2c安装成功！")
                            # 再次检查aria2c
                            result = subprocess.run(["which", "aria2c"], 
                                                  stdout=subprocess.PIPE, 
                                                  stderr=subprocess.PIPE, 
                                                  text=True)
                            if result.returncode == 0:
                                return result.stdout.strip()
                except Exception as e:
                    print(f"尝试安装aria2c时出错: {str(e)}")
                
                print("无法自动安装aria2c，请手动安装：")
                if platform.system() == "Linux":
                    print("Linux: 使用包管理器安装，如 'sudo apt install aria2'")
                elif platform.system() == "Darwin":
                    print("macOS: 使用Homebrew安装，'brew install aria2'")
                return None
        except Exception as e:
            print(f"检查aria2c时出错: {str(e)}")
            return None

    # 存储下载状态的字典
    download_status = {
        "is_downloading": False,
        "progress": 0,
        "speed": "",
        "eta": "",
        "message": "",
        "url": "",
        "save_path": ""
    }
    
    @classmethod
    def get_download_status(cls):
        """获取当前下载状态"""
        return cls.download_status
    
    @classmethod
    def _download_with_aria2c(cls, aria2c_path, url, save_dir, filename, threads, use_mirror=False):
        """使用aria2c下载文件"""
        try:
            # 初始化下载状态
            cls.download_status["is_downloading"] = True
            cls.download_status["progress"] = 0
            cls.download_status["speed"] = "准备中..."
            cls.download_status["eta"] = "计算中..."
            cls.download_status["url"] = url
            cls.download_status["save_path"] = os.path.join(save_dir, filename)
            cls.download_status["message"] = "" # 添加空的消息字段，以便前端能够正确处理
            
            # 只在控制台输出日志
            print(f"状态: 初始化中")
            print(f"进度: 0%")
            print(f"速度: 准备中...")
            print(f"剩余时间: 计算中...")
            print(f"URL: {url}")
            print(f"保存路径: {os.path.join(save_dir, filename)}")
            
            # 发送初始状态到前端
            PromptServer.instance.send_sync("model_download_status", cls.download_status)
            
            cmd = [
                aria2c_path,
                "-x", str(threads),  # 连接数
                "-s", str(threads),  # 分段数
                "-k", "1M",         # 分段大小
                "--dir", save_dir,   # 保存目录
                "-o", filename,      # 输出文件名
                url                  # 下载URL
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 读取并处理输出
            for line in process.stdout:
                print(line, end='')
                sys.stdout.flush()
                
                # 解析aria2c输出的进度信息
                if "[#" in line:
                    # 提取进度百分比
                    progress = 0  # 默认值
                    progress_match = re.search(r'(\d+)%', line)
                    if progress_match:
                        progress = int(progress_match.group(1))
                        cls.download_status["progress"] = progress
                    
                    # 提取下载速度
                    speed_match = re.search(r'(\d+(\.\d+)?\s*(K|M|G)iB/s)', line)
                    if speed_match:
                        cls.download_status["speed"] = speed_match.group(1)
                    
                    # 提取剩余时间
                    eta_match = re.search(r'ETA:(\s*\d+[smh]\d+[smh]?)', line)
                    if eta_match:
                        cls.download_status["eta"] = eta_match.group(1).strip()
                    
                    # 更新状态
                    cls.download_status["status"] = f"下载中: {progress}%"
                    
                    # 创建简单的文本格式状态信息，使用双反斜杠转义换行符
                    status_text = f"状态: 下载中: {progress}%\\n"
                    status_text += f"进度: {progress}%\\n"
                    status_text += f"速度: {cls.download_status['speed']}\\n"
                    status_text += f"剩余时间: {cls.download_status['eta']}\\n"
                    status_text += f"URL: {url}\\n"
                    status_text += f"保存路径: {os.path.join(save_dir, filename)}"
                    cls.download_status["message"] = status_text
                    
                    # 发送更新到前端
                    PromptServer.instance.send_sync("model_download_status", cls.download_status)
            
            process.wait()
            
            if process.returncode == 0:
                cls.download_status["progress"] = 100
                cls.download_status["speed"] = "完成"
                cls.download_status["eta"] = "0s"
                cls.download_status["status"] = "下载完成"
                # 创建简单的文本格式状态信息，使用双反斜杠转义换行符
                status_text = f"状态: 下载完成\\n"
                status_text += f"进度: 100%\\n"
                status_text += f"速度: 完成\\n"
                status_text += f"剩余时间: 0s\\n"
                status_text += f"URL: {url}\\n"
                status_text += f"保存路径: {os.path.join(save_dir, filename)}"
                cls.download_status["message"] = status_text
                print(f"下载完成: {os.path.join(save_dir, filename)}")
            else:
                cls.download_status["progress"] = 0
                cls.download_status["speed"] = "失败"
                cls.download_status["eta"] = "N/A"
                cls.download_status["status"] = "下载失败"
                cls.download_status["message"] = ""
                # 只在控制台输出日志
                print(f"状态: 下载失败")
                print(f"进度: 0%")
                print(f"速度: 失败")
                print(f"剩余时间: N/A")
                print(f"URL: {url}")
                print(f"保存路径: {os.path.join(save_dir, filename)}")
                print(f"错误: 返回码 {process.returncode}")
                print(f"下载失败，返回码: {process.returncode}")
            
            # 发送最终状态到前端
            cls.download_status["is_downloading"] = False
            PromptServer.instance.send_sync("model_download_status", cls.download_status)
            
            # 返回状态信息
            return cls.download_status["status"]
            
        except Exception as e:
            error_message = f"下载过程中出错: {str(e)}"
            cls.download_status["is_downloading"] = False
            cls.download_status["progress"] = 0
            cls.download_status["speed"] = "失败"
            cls.download_status["eta"] = "N/A"
            cls.download_status["status"] = error_message
            cls.download_status["message"] = ""
            
            # 只在控制台输出日志
            print(f"状态: 下载出错")
            print(f"进度: 0%")
            print(f"速度: 失败")
            print(f"剩余时间: N/A")
            print(f"URL: {url}")
            save_path = os.path.join(save_dir, filename) if save_dir and filename else "未知"
            print(f"保存路径: {save_path}")
            print(f"错误: {str(e)}")
            # 直接输出错误信息
            print(error_message)
            
            # 发送错误状态到前端
            PromptServer.instance.send_sync("model_download_status", cls.download_status)
            
            # 返回错误信息
            return error_message