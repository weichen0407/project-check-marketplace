---
name: fetch-latest
description: Find recent technology news and explore how selected results could apply to a product in the Technology Discovery App. 为当前产品查找最新新闻与相关技术，在 MCP App 中查看并选择技术。用户说“最新技术”“获取新闻”“把这个技术应用到我的产品”或“技术发现”时使用。
---

# 技术发现

按[语言规则](../project-check/references/response-language.md)回复。按请求语言向工具传入 `language="en"` 或 `language="cn"`，后续保留同一语言。

1. 在插件的 `triz` 服务调用 `list_products` 查找产品，产品档案按[工作区规则](../project-check/references/workspace.md)读写。用户明确提供新产品资料并要求保存时调用 `save_product`。更新同 ID 时保留已有准确字段。打开已有工作区中的 App 时向 `fetch_latest` 传入同一 `workspace_token`。
2. 调用 `fetch_latest` 打开技术发现 App，传入实际产品 ID、相关关键词和 `mode="live"`。用户要求体验演示时用 `mode="demo"`，说明产品与技术示例为虚构。真实产品的检索词限于用户允许用于检索的术语，首次搜索时省略保密名称和未公开参数。
3. 用户点击 + 后，App 把产品档案和所选技术提交到模型上下文，并尝试在 Codex 主输入框追加标题、来源链接和适配请求。宿主不支持草稿写入时，App 保留可编辑的提问草稿。用户可以编辑后发送。
4. 回执只记录搜索数量，卡片描述和摘录通过 App 显示。用户选择并发送后，才结合可见资料说明适用部位、改动、约束和验证方法。区分来源事实和适配推断。
