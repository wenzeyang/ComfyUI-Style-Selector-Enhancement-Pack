# ComfyUI Style Selector Enhancement Pack

**完整独立插件：下载 ZIP，解压到 `ComfyUI/custom_nodes`，重启即可使用。无需安装 Easy Use，无需运行补丁脚本，无额外 pip 依赖。**

这是从 [yolain/ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) 的风格提示词选择器提取并改造的独立派生版本。来源基线为 Easy Use 1.4.1；采用原项目 GNU GPL v3 许可证。不是上游官方发布，也不是完整 Easy Use 插件集。详见 [上游声明](UPSTREAM.md)。

## 安装

1. 点击 GitHub **Code → Download ZIP**。
2. 解压后将包含 `__init__.py` 的整个文件夹放入 `ComfyUI/custom_nodes/`。
3. 重启 ComfyUI，刷新浏览器。
4. 搜索 **风格选择器增强 / Style Selector**（类别 `Style Selector`）。

正确结构：

```text
ComfyUI/custom_nodes/ComfyUI-Style-Selector-Enhancement-Pack-main/
  __init__.py
  web/style_selection_manager.js
  styles/example.json
```

要求支持 `comfy_api.latest` V3 节点接口的 ComfyUI；开发验证环境为 ComfyUI 0.36.0。不承诺兼容缺少该接口的旧版本。

## 使用

- **单选模式**：只使用一个风格。
- **多选模式（叠加）**：选中风格合并为一条提示词。
- **多选模式（逐一生成）**：每个风格单独与基础提示词组合。
- **全选模式**：当前分类全部逐个输出，仍可删除部分已选项。

点击 **管理风格 / 收藏夹** 选择风格、搜索、收藏；已选框点 × 删除。收藏保存在当前浏览器，不上传服务器；更换浏览器或清除站点数据不会自动迁移。

基础提示词连接 `positive`，正向输出连接 CLIP 编码节点。负向输出可按工作流需要连接负向编码。新增第三个 **文件名前缀** 输出连接 Save Image 的 `filename_prefix` 输入；可右键保存节点相应控件转换为输入。

默认命名 `Krea2-%date:yyyyMMddhhmmss%`，实际文件如 `Krea2-20260101123000_水彩_00001_.png`。日期由选择器展开，风格名附在后面，保存节点追加编号和扩展名。逐一模式下三个输出列表按顺序对应；不要在下游先把所有图合并成单个 batch。若同时使用 Preview Image，资产列表会额外显示临时预览图。

## 风格库与兼容性

包内只有三个新编写的通用示例，安装后即可测试功能。**不包含开发者本地的 Krea 风格库、缩略图或个人素材。**

保留 Easy Use 风格 JSON 格式，将自己有权使用的 JSON 放入本插件 `styles/`，重启后选择分类：

```json
[
  {
    "name": "My Style",
    "name_cn": "我的风格",
    "prompt": "Watercolor, {prompt}",
    "negative_prompt": "text",
    "thumbnail": "samples/my-style.png"
  }
]
```

`name` 为唯一标识，`name_cn`、负向提示词、缩略图可省略。缩略图放入 `styles/` 内，支持 PNG/JPEG/WebP/GIF 的相对路径，不读取任意本地路径或远程图片。选中风格保留逗号分隔存储，名称中不应含逗号。

独立节点 ID 为 `StyleSelectorEnhancement`，可与 Easy Use 共存，不覆盖原节点。已有 `easy stylesSelector` 工作流不会自动迁移：添加新节点、选择相同库和风格后重新连接输出即可。本仓库早期提交是原节点补丁包；当前版本已改为直接安装的独立插件。

逐一模式使用 ComfyUI 列表执行，不保证每张保存后才处理下一张，也不自动清除缓存。插件自身不含模型，需要使用已有生成工作流出图。

## 隐私与许可

发布内容仅为代码、说明、测试、GPL v3 许可证和通用示例风格。无用户收藏、历史任务、模型、图片、截图、工作流、绝对路径、密钥或登录信息。无遥测、外部上传和自动模型下载。

参见 [LICENSE](LICENSE) 和 [UPSTREAM.md](UPSTREAM.md)。
