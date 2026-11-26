---
name: project-check-report
description: Turn existing engineering findings into a Markdown or HTML report in Chinese or English. 将项目检查工具结果、当前方案讨论和用户资料按模板整理成 Markdown 或 HTML 阶段报告。
---

# 项目检查报告

Follow the [request language rules](../project-check/references/response-language.md).

先遵循[调用提示](../project-check/references/call-disclosure.md)与[下一步和文档规则](../project-check/references/continuation-and-reporting.md)。只整理现有结果时，首行说明复用已有结果。

使用当前可见对话、实际读取的资料及工具结果。保留用户最新修正、约束、证据和版本。只采用已回传的页面选择与编辑内容。区分事实、工具估算和分析判断。

## 模板与填充

- 中文模板位于 [templates](../../templates/project-check-report.md)，英文模板位于 [templates/en](../../templates/en/project-check-report.md)。按对应的 [中文](../../templates/report-layout.json) 或 [英文](../../templates/en/report-layout.json) 章节清单填充。
- Markdown 使用对应语言的报告模板。HTML 从 [布局目录](../../templates/html-template-catalog.json) 选择，按对应语言的模板目录解析 `file`，沿用所选模板的布局和样式。已指定格式和布局时直接生成。未指定格式时使用 Markdown。
- 用实际项目背景、阶段结论、工具结果、证据、限制、验证建议和调用记录替换占位符。移除空章节及其标题。Markdown 删除模板的 `report-block` 注释。HTML 对正文中的文本进行转义，空图片槽和空章节一起移除。
- 按请求语言撰写报告，保留证据原文、来源链接和标识符。整理现有报告时不重跑分析。

## 交付

用户需要文件时，用宿主的文件编辑能力在项目的可写目录中创建 Markdown 或 HTML 成品。文件名已存在时另存。交付前核对实际文件、正文语言、证据链接及未填充占位符。文件编辑不可用时，在聊天中提供 Markdown。
