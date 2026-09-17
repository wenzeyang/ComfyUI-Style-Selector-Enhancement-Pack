# ComfyUI Easy Use 风格选择器增强

基于 [yolain/ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) 的本地增强包，适配已验证的 Easy Use 1.4.1、v2 前端和 ComfyUI 0.36.0。不是独立节点包，也不是完整的 Easy Use 分支。

## 功能

| 模式 | 行为 |
| --- | --- |
| 单选模式 | 只使用一个风格 |
| 多选模式（叠加） | 按原规则合并为一条提示词，旧工作流的默认模式 |
| 多选模式（逐一生成） | 每个风格分别与基础提示词组合，输出一组独立提示词 |
| 全选模式 | 选中当前分类全部风格，逐个输出，仍可移除部分已选项 |

节点内及管理弹窗均显示已选列表，点 × 删除。弹窗支持搜索、缩略图和收藏筛选。收藏按分类与原始名称保存到当前浏览器 localStorage，跨工作流共享，刷新后保留；更换浏览器或清除站点数据不会自动迁移。

## 安装

先安装原版 Easy Use 并停止 ComfyUI。下载本增强包，在命令行执行：

```sh
python install.py "/path/to/ComfyUI/custom_nodes/ComfyUI-Easy-Use"
```

Windows portable 可以使用自带的 `python_embeded/python.exe` 执行同一脚本。脚本会核对节点版本、备份原后端文件，仅替换 `stylesPromptSelector` 类并添加一个前端扩展，不修改风格 JSON 或其他节点。版本不匹配时停止，不覆盖未知代码。

重启 ComfyUI 并刷新浏览器，在原「风格提示词选择器」中设置 `selection_mode`，点击「管理风格 / 收藏夹」。不需要重新连接原有输出。

## 兼容性与执行行为

- 保留原节点名称、风格库 JSON 格式、风格名称和 `select_styles` 的逗号分隔存储。
- 保留前两个正负 STRING 输出的位置；新增可选模式参数，缺省叠加。
- 正负输出现在采用 ComfyUI 列表输出；单选与叠加是单元素列表。主动消费或合并列表的下游节点可能需要调整。
- 逐一模式按列表处理，不保证每张图片保存后才处理下一张，也不主动清理缓存。空选择在逐一模式下输出空列表。
- 全选仅限当前分类，不跨全部风格库。固定种子有助于比较风格差异。
- 上游更新可能覆盖本增强或使版本检查不通过。

## 验证

本地已做 47 个风格库、235 组旧合并结果对照；服务端验证四种模式的提示词输出；浏览器验证十选、移除、单选、全选、收藏刷新持久化及新旧工作流参数恢复。未执行模型出图测试。

```sh
python -m unittest discover -s tests -v
```

## 来源与许可

`src/original_selector.py` 提取自 Easy Use 1.4.1；`src/enhanced_selector.py` 为其修改版本，新增选择模式与列表输出。`src/style_selection_manager.js` 为新增管理界面。保留原项目 GNU GPL v3 许可证，见 [LICENSE](LICENSE)。本包不包含模型、第三方风格库、预览素材、个人工作流或用户数据。
