# ComfyUI 模型下载插件

这是一个用于 [ComfyUI](https://github.com/comfyanonymous/ComfyUI) 的插件，提供了一个简单的界面来下载模型文件，使用 aria2c 实现多线程下载，大大提高下载速度。

## 功能特点

- 使用 aria2c 实现多线程下载，显著提高下载速度
- 自动识别 ComfyUI 中的所有模型目录
- 支持自定义保存位置
- 支持使用镜像站点（如 hf-mirror.com）加速下载
- 可调节线程数以优化下载性能
- 支持 Windows、Linux 和 macOS

## 安装方法

### 1. 安装插件

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/yourusername/ComfyUI_Model_Download
cd ComfyUI_Model_Download
python install.py
```

### 2. 安装 aria2c

插件依赖 aria2c 进行多线程下载。

#### Windows

- 方法1：使用 [Chocolatey](https://chocolatey.org/)：`choco install aria2`
- 方法2：从 [aria2 官方网站](https://github.com/aria2/aria2/releases) 下载最新版本

#### Linux

```bash
sudo apt update
sudo apt install aria2
```

#### macOS

```bash
brew install aria2
```

## 使用方法

### 通过 UI 界面下载

1. 在 ComfyUI 顶部菜单中点击"扩展"->"模型下载器"
2. 输入模型的下载 URL（支持 Hugging Face 链接）
3. 选择保存目录或输入自定义路径
4. 选择是否使用镜像站点
5. 设置下载线程数（默认为16）
6. 点击"开始下载"按钮

### 通过工作流节点下载

1. 在 ComfyUI 中添加 "Model Downloader" 节点
2. 输入模型的下载 URL（支持 Hugging Face 链接）
3. 选择保存目录或输入自定义路径
4. 选择是否使用镜像站点
5. 设置下载线程数（默认为16）
6. 点击节点上的"开始下载"按钮

## 注意事项

- 下载大型模型文件时，建议使用16-32个线程以获得最佳性能
- 如果下载速度不稳定，可以尝试减少线程数
- 使用镜像站点可能会提高中国大陆地区的下载速度

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。