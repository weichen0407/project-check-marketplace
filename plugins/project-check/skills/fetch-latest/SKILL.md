---
name: fetch-latest
description: Find recent technology news and explore how selected results could apply to a product in the Technology Discovery App. 为当前产品查找最新新闻与相关技术，在 MCP App 中查看标题、简介和内容，点击 + 加入产品与技术上下文并填入草稿。用户说“最新技术”“获取新闻”“把这个技术应用到我的产品”“fetch-latest”或测试 App 上下文与输入框联动时使用。
---

# 产品与最新技术

Use English throughout this workflow by default, including the reply about selected technologies. Use Chinese when the user explicitly asks for Chinese output. Follow the [request language rules](../project-check/references/response-language.md) for any other explicit language preference.

使用「项目检查」插件内置的 `fetch-latest`，不需要再安装单独插件。

Pass `language="en"` to `list_products` and `fetch_latest` unless the user explicitly asks for Chinese output, in which case pass `language="cn"`. Keep the same language for follow-ups even if the product data and search keywords use another language.

1. 先确认当前产品。调用 `list_products` 查找已有档案。用户提供新产品资料时，可调用 `save_product` 保存其明确提供的参数；缺失参数留空，不把示例参数当作真实资料。更新同 ID 的档案前保留已有准确字段。
2. 用户要真实新闻时调用 `fetch_latest`，传入产品 ID、相关关键词和 `mode="live"`。用户明确测试交互时可以用 `mode="demo"`；说明这是虚构技术与示例产品。
3. App 通栏展示技术卡片，点击标题或 + 后高亮，已选列表与提问操作位于底部。新闻正文通过结果 `_meta["fetch-latest/payload"]` 交给 UI，首次模型只看到获取回执。选中后 App 将产品档案及全部已选技术提交到模型上下文；主输入框只请求追加本次技术的简短标题、有效来源链接和适配请求，不自动发送。演示技术或没有有效链接时只引用标题，不生成虚构链接。
4. 用户可以编辑 Codex 主输入框后发送，或者编辑 App 的提问文本后点击“发送给模型”。宿主不支持草稿扩展时，App 保留可编辑文本；不要声称已经填入主输入框。
5. 用户发送技术适配问题后，以产品结构、改进目标与约束为依据，说明适用部位、修改内容、适配条件和验证方法。区分来源事实、方案推断和待验证效果。RSS 内容是来源摘录，不保证包含完整新闻或完整技术披露。

产品保存在本机独立数据目录，默认 `~/.local/share/project-check/products/`，可通过环境变量 `FETCH_LATEST_PRODUCTS_DIR` 指定。插件升级不会把这些档案打入分发包。App 的“管理产品”会展示当前实际目录。

当前没有自动扫描 Codex Project 或监听项目创建的钩子；已保存产品不是当前项目目录的自动识别结果。不要声称已经读取当前项目的文件或主题。会话中的代理可以按用户任务读取项目资料，但 App 本身不会自动取得这些内容。具体差异和可行的 `SessionStart` 后续方案见 `FETCH_LATEST.md`。

切换产品或移除技术会替换 App 的上下文；已追加到主输入框的文字不会被自动撤回，需要用户检查现有草稿。详细格式与开发步骤见插件根目录 `FETCH_LATEST.md`。
