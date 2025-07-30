import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def is_windows():
    return platform.system() == "Windows"

def is_linux():
    return platform.system() == "Linux"

def is_macos():
    return platform.system() == "Darwin"

def check_aria2c():
    """检查aria2c是否已安装"""
    try:
        if is_windows():
            aria2c_name = "aria2c.exe"
            # 首先检查指定的aria2c目录
            bundled_aria2c_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria2-1.37.0-win-64bit")
            bundled_aria2c_path = os.path.join(bundled_aria2c_dir, aria2c_name)
            if os.path.exists(bundled_aria2c_path):
                print(f"在捆绑目录找到aria2c: {bundled_aria2c_path}")
                return True
            
            # 然后检查当前目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            aria2c_path = os.path.join(current_dir, aria2c_name)
            if os.path.exists(aria2c_path):
                print(f"在当前目录找到aria2c: {aria2c_path}")
                return True
            
            # 最后检查PATH环境变量
            for path in os.environ["PATH"].split(os.pathsep):
                exe_path = os.path.join(path, aria2c_name)
                if os.path.exists(exe_path):
                    print(f"在PATH中找到aria2c: {exe_path}")
                    return True
            print("未找到aria2c.exe")
            return False
        else:
            # Linux/Mac使用which命令
            result = subprocess.run(["which", "aria2c"], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    text=True)
            if result.returncode == 0:
                print(f"在系统中找到aria2c: {result.stdout.strip()}")
                return True
            print("未在系统中找到aria2c")
            return False
    except Exception as e:
        print(f"检查aria2c时出错: {str(e)}")
        return False

def install_aria2c():
    """安装aria2c"""
    try:
        if is_windows():
            # 检查是否有捆绑的aria2c目录
            bundled_aria2c_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria2-1.37.0-win-64bit")
            bundled_aria2c_path = os.path.join(bundled_aria2c_dir, "aria2c.exe")
            
            # 如果目录存在但aria2c.exe不存在
            if os.path.exists(bundled_aria2c_dir) and not os.path.exists(bundled_aria2c_path):
                print(f"发现aria2c目录 {bundled_aria2c_dir} 但未找到aria2c.exe文件。")
            elif os.path.exists(bundled_aria2c_path):
                print(f"检测到插件已捆绑aria2c，位于 {bundled_aria2c_path}")
                return True
            
            # 尝试解压捆绑的aria2c（如果存在压缩包但尚未解压）
            aria2c_zip = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria2-1.37.0-win-64bit.zip")
            if os.path.exists(aria2c_zip):
                try:
                    import zipfile
                    print(f"找到aria2c压缩包，正在解压...")
                    with zipfile.ZipFile(aria2c_zip, 'r') as zip_ref:
                        zip_ref.extractall(os.path.dirname(os.path.abspath(__file__)))
                    if os.path.exists(bundled_aria2c_path):
                        print(f"解压完成，aria2c已安装到 {bundled_aria2c_path}")
                        return True
                    else:
                        print(f"解压完成，但未找到aria2c.exe，可能压缩包结构不符合预期")
                except Exception as e:
                    print(f"解压aria2c失败: {str(e)}")
            
            # 提供手动安装指导
            print("Windows系统下有两种方式获取aria2c:")
            print("1. 插件已在aria2-1.37.0-win-64bit目录下捆绑了aria2c.exe，无需额外安装。")
            print("2. 如需手动安装，请访问 https://github.com/aria2/aria2/releases 下载最新版本。")
            print("   将aria2c.exe放在以下位置之一:")
            print(f"   - {bundled_aria2c_dir} 目录")
            print(f"   - {os.path.dirname(os.path.abspath(__file__))} 目录")
            print("   - 或添加到系统PATH环境变量中")
            print("   或者使用包管理器如Chocolatey安装: choco install aria2")
            return False
        elif is_linux():
            # 尝试使用apt安装
            print("尝试使用apt安装aria2...")
            result = subprocess.run(["sudo", "apt", "update"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
            if result.returncode == 0:
                result = subprocess.run(["sudo", "apt", "install", "-y", "aria2"], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
                return result.returncode == 0
            return False
        elif is_macos():
            # 尝试使用brew安装
            print("尝试使用Homebrew安装aria2...")
            result = subprocess.run(["brew", "install", "aria2"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
            return result.returncode == 0
        return False
    except Exception as e:
        print(f"安装aria2c时出错: {str(e)}")
        return False

def main():
    print("检查ComfyUI模型下载插件依赖...")
    
    # 检查aria2c
    if not check_aria2c():
        print("未找到aria2c，这是模型下载插件的必要依赖。")
        
        # 检查是否已有捆绑的aria2c目录但可能是空的
        bundled_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria2-1.37.0-win-64bit")
        if os.path.exists(bundled_dir) and not os.path.exists(os.path.join(bundled_dir, "aria2c.exe")):
            print(f"发现aria2c目录 {bundled_dir} 但未找到aria2c.exe文件。")
        
        choice = input("是否尝试安装aria2c? (y/n): ")
        if choice.lower() == 'y':
            if install_aria2c():
                print("aria2c安装成功!")
                print("插件现在可以正常使用。")
            else:
                if is_windows():
                    print("aria2c安装未完成，请按照以下方式手动安装:")
                    print("1. 下载aria2c: 访问 https://github.com/aria2/aria2/releases 下载最新版本")
                    print("2. 解压下载的文件，将aria2c.exe放置在以下任一位置:")
                    print(f"   - {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aria2-1.37.0-win-64bit')} 目录")
                    print(f"   - {os.path.dirname(os.path.abspath(__file__))} 目录")
                    print("   - 或添加到系统PATH环境变量中")
                else:
                    print("aria2c安装失败，请手动安装:")
                    print("Linux: 使用包管理器安装，如 'sudo apt install aria2'")
                    print("macOS: 使用Homebrew安装，'brew install aria2'")
        else:
            print("跳过aria2c安装。注意：没有aria2c，插件将无法正常工作。")
    else:
        print("aria2c已安装，插件可以正常使用。")
    
    print("\n安装完成！")
    print("插件将在ComfyUI中显示为'Model Downloader'节点。")
    print("使用方法: 在ComfyUI中添加'Model Downloader'节点，输入模型URL，选择保存目录，设置线程数，然后点击'下载'按钮。")

if __name__ == "__main__":
    main()