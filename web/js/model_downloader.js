
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// 监听下载状态更新
api.addEventListener("model_download_status", function(status) {
    const dialog = document.getElementById("model-downloader-dialog");
    if (!dialog) return;
    
    const statusGroup = dialog.querySelector("div:nth-child(7)"); // 状态显示区域
    const statusText = statusGroup.querySelector("pre");
    
    // 显示状态区域
    statusGroup.style.display = "block";
    
    // 更新状态信息
    let statusMessage = `状态: ${status.message}\n`;
    if (status.is_downloading) {
        statusMessage += `进度: ${status.progress}%\n`;
        statusMessage += `速度: ${status.speed}\n`;
        statusMessage += `预计剩余时间: ${status.eta}\n`;
    }
    statusMessage += `URL: ${status.url}\n`;
    statusMessage += `保存路径: ${status.save_path}`;
    
    statusText.textContent = statusMessage;
    
    // 更新ComfyUI节点输出显示
    updateNodeOutputs(status);
});

// 更新ComfyUI节点状态
function updateNodeOutputs(status) {
    // 查找所有ModelDownloader节点
    const nodes = app.graph._nodes;
    if (!nodes) return;
    
    for (const node of nodes) {
        if (node.type === "ModelDownloaderNode") {
            // 添加调试信息
            console.log("下载状态更新:", status);
            
            // 触发节点更新
            node.setDirtyCanvas(true, true);
            
            // 强制节点重新绘制
            if (node.onDrawBackground) {
                node.onDrawBackground();
            }
                
                // 强制整个画布更新
                app.graph.setDirtyCanvas(true, true);
                
                // 通知连接的节点更新
                if (node.outputs && node.outputs[0] && node.outputs[0].links) {
                    for (const linkId of node.outputs[0].links) {
                        const link = app.graph.links[linkId];
                        if (link) {
                            const targetNode = app.graph.getNodeById(link.target_id);
                            if (targetNode) {
                                targetNode.onExecuted && targetNode.onExecuted();
                                targetNode.setDirtyCanvas(true, true);
                            }
                        }
                    }
                }
                
                // 延迟再次更新，确保显示正确
                setTimeout(() => {
                    node.setDirtyCanvas(true, true);
                    app.graph.setDirtyCanvas(true, true);
                }, 100);
            }
        }
    }
}

app.registerExtension({
    name: "ComfyUI.ModelDownloader",
    async setup() {
        // 创建下载对话框
        function createDownloadDialog() {
            // 创建对话框容器
            const dialog = document.createElement("div");
            dialog.id = "model-downloader-dialog";
            dialog.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: #1a1a1a;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 20px;
                z-index: 10000;
                width: 500px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
                display: none;
            `;

            // 创建对话框标题
            const title = document.createElement("h2");
            title.textContent = "模型下载器";
            title.style.cssText = `
                margin-top: 0;
                margin-bottom: 20px;
                color: #fff;
                font-size: 18px;
                border-bottom: 1px solid #444;
                padding-bottom: 10px;
            `;
            dialog.appendChild(title);

            // 创建表单容器
            const form = document.createElement("div");
            form.style.cssText = `
                display: flex;
                flex-direction: column;
                gap: 15px;
            `;
            dialog.appendChild(form);

            // URL输入
            const urlGroup = document.createElement("div");
            const urlLabel = document.createElement("label");
            urlLabel.textContent = "下载URL:";
            urlLabel.style.cssText = `
                display: block;
                margin-bottom: 5px;
                color: #ddd;
            `;
            const urlInput = document.createElement("input");
            urlInput.type = "text";
            urlInput.placeholder = "https://huggingface.co/...";
            urlInput.style.cssText = `
                width: 100%;
                padding: 8px;
                background-color: #333;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
                box-sizing: border-box;
            `;
            urlGroup.appendChild(urlLabel);
            urlGroup.appendChild(urlInput);
            form.appendChild(urlGroup);

            // 模型目录选择
            const dirGroup = document.createElement("div");
            const dirLabel = document.createElement("label");
            dirLabel.textContent = "保存目录:";
            dirLabel.style.cssText = `
                display: block;
                margin-bottom: 5px;
                color: #ddd;
            `;
            const dirSelect = document.createElement("select");
            dirSelect.style.cssText = `
                width: 100%;
                padding: 8px;
                background-color: #333;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
                box-sizing: border-box;
            `;
            dirGroup.appendChild(dirLabel);
            dirGroup.appendChild(dirSelect);
            form.appendChild(dirGroup);

            // 自定义路径输入（当选择custom时显示）
            const customPathGroup = document.createElement("div");
            customPathGroup.style.display = "none";
            const customPathLabel = document.createElement("label");
            customPathLabel.textContent = "自定义路径:";
            customPathLabel.style.cssText = `
                display: block;
                margin-bottom: 5px;
                color: #ddd;
            `;
            const customPathInput = document.createElement("input");
            customPathInput.type = "text";
            customPathInput.placeholder = "输入完整路径...";
            customPathInput.style.cssText = `
                width: 100%;
                padding: 8px;
                background-color: #333;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
                box-sizing: border-box;
            `;
            customPathGroup.appendChild(customPathLabel);
            customPathGroup.appendChild(customPathInput);
            form.appendChild(customPathGroup);
            
            // 子文件夹输入
            const subfolderGroup = document.createElement("div");
            const subfolderLabel = document.createElement("label");
            subfolderLabel.textContent = "子文件夹名称:";
            subfolderLabel.style.cssText = `
                display: block;
                margin-bottom: 5px;
                color: #ddd;
            `;
            const subfolderInput = document.createElement("input");
            subfolderInput.type = "text";
            subfolderInput.placeholder = "输入子文件夹名称...";
            subfolderInput.style.cssText = `
                width: 100%;
                padding: 8px;
                background-color: #333;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
                box-sizing: border-box;
            `;
            subfolderGroup.appendChild(subfolderLabel);
            subfolderGroup.appendChild(subfolderInput);
            form.appendChild(subfolderGroup);

            // 使用镜像选项
            const mirrorGroup = document.createElement("div");
            const mirrorLabel = document.createElement("label");
            mirrorLabel.style.cssText = `
                color: #ddd;
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
            `;
            const mirrorCheckbox = document.createElement("input");
            mirrorCheckbox.type = "checkbox";
            mirrorCheckbox.checked = true;
            mirrorLabel.appendChild(mirrorCheckbox);
            mirrorLabel.appendChild(document.createTextNode("使用镜像站点 (hf-mirror.com)"));
            mirrorGroup.appendChild(mirrorLabel);
            form.appendChild(mirrorGroup);

            // 线程数选择
            const threadsGroup = document.createElement("div");
            const threadsLabel = document.createElement("label");
            threadsLabel.textContent = "下载线程数:";
            threadsLabel.style.cssText = `
                display: block;
                margin-bottom: 5px;
                color: #ddd;
            `;
            const threadsInput = document.createElement("input");
            threadsInput.type = "number";
            threadsInput.min = "1";
            threadsInput.max = "32";
            threadsInput.value = "16";
            threadsInput.style.cssText = `
                width: 100%;
                padding: 8px;
                background-color: #333;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
                box-sizing: border-box;
            `;
            threadsGroup.appendChild(threadsLabel);
            threadsGroup.appendChild(threadsInput);
            form.appendChild(threadsGroup);

            // 状态显示区域
            const statusGroup = document.createElement("div");
            statusGroup.style.cssText = `
                margin-top: 10px;
                padding: 10px;
                background-color: #222;
                border-radius: 4px;
                color: #aaa;
                max-height: 150px;
                overflow-y: auto;
                display: none;
            `;
            const statusText = document.createElement("pre");
            statusText.style.cssText = `
                margin: 0;
                white-space: pre-wrap;
                word-break: break-all;
                font-family: monospace;
                font-size: 12px;
            `;
            statusGroup.appendChild(statusText);
            form.appendChild(statusGroup);

            // 按钮组
            const buttonGroup = document.createElement("div");
            buttonGroup.style.cssText = `
                display: flex;
                justify-content: flex-end;
                gap: 10px;
                margin-top: 20px;
            `;

            // 下载按钮
            const downloadButton = document.createElement("button");
            downloadButton.textContent = "开始下载";
            downloadButton.style.cssText = `
                padding: 8px 16px;
                background-color: #2a6496;
                border: none;
                border-radius: 4px;
                color: white;
                cursor: pointer;
            `;
            downloadButton.addEventListener("mouseover", () => {
                downloadButton.style.backgroundColor = "#3a74a6";
            });
            downloadButton.addEventListener("mouseout", () => {
                downloadButton.style.backgroundColor = "#2a6496";
            });

            // 关闭按钮
            const closeButton = document.createElement("button");
            closeButton.textContent = "关闭";
            closeButton.style.cssText = `
                padding: 8px 16px;
                background-color: #555;
                border: none;
                border-radius: 4px;
                color: white;
                cursor: pointer;
            `;
            closeButton.addEventListener("mouseover", () => {
                closeButton.style.backgroundColor = "#666";
            });
            closeButton.addEventListener("mouseout", () => {
                closeButton.style.backgroundColor = "#555";
            });

            buttonGroup.appendChild(closeButton);
            buttonGroup.appendChild(downloadButton);
            form.appendChild(buttonGroup);

            // 添加事件监听器
            dirSelect.addEventListener("change", () => {
                if (dirSelect.value === "custom") {
                    customPathGroup.style.display = "block";
                } else {
                    customPathGroup.style.display = "none";
                }
            });

            closeButton.addEventListener("click", () => {
                dialog.style.display = "none";
            });

            downloadButton.addEventListener("click", async () => {
                const url = urlInput.value.trim();
                if (!url) {
                    alert("请输入有效的下载URL");
                    return;
                }

                const modelDir = dirSelect.value;
                const customPath = customPathInput.value.trim();
                const subfolder = subfolderInput.value.trim();
                const useMirror = mirrorCheckbox.checked ? "yes" : "no";
                const threads = parseInt(threadsInput.value) || 16;

                if (modelDir === "custom" && !customPath) {
                    alert("选择自定义路径时，必须提供有效的路径");
                    return;
                }

                // 显示状态区域
                statusGroup.style.display = "block";
                statusText.textContent = "正在准备下载...";

                try {
                    // 通过API调用后端下载功能
                    const response = await api.fetchApi('/model_downloader/download', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            url: url,
                            model_dir: modelDir,
                            custom_path: customPath,
                            subfolder: subfolder,
                            use_mirror: useMirror,
                            threads: threads
                        })
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || '下载请求失败');
                    }

                    // 下载已开始，状态更新将通过WebSocket事件接收
                    console.log('下载请求已发送');
                } catch (error) {
                    statusText.textContent = `错误: ${error.message}`;
                    console.error("下载出错:", error);
                }
            });

            // 获取模型目录列表
            async function fetchModelDirs() {
                try {
                    // 通过API获取模型目录列表
                    const response = await api.fetchApi('/model_downloader/get_model_dirs', {
                        method: 'GET'
                    });
                    
                    if (!response.ok) {
                        throw new Error('获取模型目录失败');
                    }
                    
                    const data = await response.json();
                    const modelDirs = data.model_dirs || [];
                    
                    // 填充下拉菜单
                    dirSelect.innerHTML = "";
                    
                    // 添加custom选项
                    const customOption = document.createElement("option");
                    customOption.value = "custom";
                    customOption.textContent = "custom";
                    dirSelect.appendChild(customOption);
                    
                    // 添加其他目录选项
                    modelDirs.forEach(option => {
                        const optionElement = document.createElement("option");
                        optionElement.value = option;
                        optionElement.textContent = option;
                        dirSelect.appendChild(optionElement);
                    });
                } catch (error) {
                    console.error("获取模型目录失败:", error);
                }
            }

            // 初始化时获取目录列表
            fetchModelDirs();

            return dialog;
        }

        // 创建并添加对话框到DOM
        const dialog = createDownloadDialog();
        document.body.appendChild(dialog);

        // 注册菜单项
        app.ui.menuContainer.appendChild(
            app.ui.createButton({
                id: "model-downloader-button",
                content: "模型下载器",
                onClick: () => {
                    const dialog = document.getElementById("model-downloader-dialog");
                    if (dialog) {
                        dialog.style.display = "block";
                    }
                }
            })
        );

        // 注册顶部菜单项
        app.registerExtension({
            name: "ComfyUI.ModelDownloader.Menu",
            async setup() {
                const modelDownloaderMenu = {
                    id: "model-downloader",
                    label: "模型下载器",
                    function: () => {
                        const dialog = document.getElementById("model-downloader-dialog");
                        if (dialog) {
                            dialog.style.display = "block";
                        }
                    }
                };

                // 添加到顶部菜单
                app.ui.menu.addItem({
                    path: "扩展",
                    item: modelDownloaderMenu
                });
            }
        });
    }
});