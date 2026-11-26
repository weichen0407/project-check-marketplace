---
name: trends-board
description: Create or refresh a board of technology, patent, and news trends with links to primary sources. 为当前产品或明确的监测主题生成可在 Codex 中查看的技术、专利和资讯趋势看板，条目可点击跳转原文。用户要求产品趋势看板、最新消息看板或 Scheduled 定时刷新看板时使用。单次新闻 App 选择或纯专利监测沿用对应 Skill。
---

# 产品趋势看板

Follow the [request language rules](../project-check/references/response-language.md). For an English request, use English throughout this workflow.

从当前会话及用户授权的产品资料确定产品、关键技术特征和专利市场。已有范围直接复用。缺少专利市场且无法可靠推断时，询问或标明专利栏待确定。模拟产品继续按模拟方案标注，条目的来源性质单独记录。

## 取证与更新

- **技术**优先厂商技术资料、标准发布方或论文。写清可核查的特征和与本项目的关系。
- **专利**按目标市场和关键结构查询专利局等官方公开来源。公开、授权及其他可核实事件分别注明日期和口径，技术相关性与权利状态分开。来源不可用要注明原因。看板只汇总线索，权利状态以实际可核实的记录为限。
- **资讯**优先直接可打开的报道或发布者公告，使用页面的发布日期或更新时间并注明口径。仅能取得 RSS 时明确标注。技术发现 App 的回执只证明获取数量，按[技术发现](../fetch-latest/SKILL.md)的上下文边界处理，不能用回执推断卡片内容。

选择每栏最贴近产品的少量条目，默认三条。保留可打开的 HTTPS 原文链接，专利优先权项锚点或 PDF 页码。沿用上次成功结果比较。按公开号、事件及规范化 URL 去重。实际核对无变化时用 `unchanged`，来源失败或不足以完成核对时用 `failed` 并说明原因。只更新成功核对的栏，渲染器会保留其余栏的上次条目。

## 云端看板

使用[工作区规则](../project-check/references/workspace.md)找到或创建当前项目的工作区。使用 `triz` 服务。已有看板时先调用 `get_trends_board` 获取各栏上次状态与条目，用户只想查看时直接使用本次 App 结果。新建或更新时调用 `update_trends_board`，传入 `workspace_token`、下方的 `update` 数据和已有的 `board_id`。首次生成后保存返回的 `board_id`，后续刷新沿用这块看板。

输入形状如下。示意只说明字段。正式输入按实际核查结果填写。

```json
{
  "product": "产品名称",
  "market": "已确认的目标市场",
  "language": "cn",
  "as_of": "YYYY-MM-DD",
  "channels": {
    "technology": {"status": "updated", "entries": []},
    "patents": {"status": "unchanged"},
    "news": {"status": "failed", "note": "实际来源错误"}
  }
}
```

`updated` 的每条 `entries` 包含 `title`、`source`、`summary`、`url`，可选 `date`（YYYY-MM-DD）和 `key`（例如公开号或公开号加事件）。`source` 可注明「厂商规格」「授权公告」「RSS 摘录」等口径。更新前可用 `get_trends_board` 读取各栏上次成功日期、条目和状态。`unchanged` 和 `failed` 不传新条目。`failed` 必须提供原因。

For English requests set `"language": "en"` and write all generated entry titles, summaries and notes in English. Preserve source identities and URLs. Include this language in any scheduled refresh prompt.

工具会在对话中打开趋势看板，用户点击条目可查看 HTTPS 原文。返回冲突时先读取现有看板，再按实际核查结果重试。

用户明确要求定时刷新时，按[定时任务流程](../create-scheduled-task/SKILL.md)设置。提示词保存可访问的工作区配置路径、看板标识、范围和来源，写明核查口径、结果语言及失效时保留上次条目的规则。待宿主返回成功后汇报状态。
