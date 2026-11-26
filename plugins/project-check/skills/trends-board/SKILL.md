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

## 渲染与 Scheduled

使用插件自带的 [render_trends_board.py](../../scripts/render_trends_board.py)，绝对路径按本 Skill 的安装位置解析。把 UTF-8 输入写入可写工作目录，在明确可写的持久路径保存 HTML。优先用宿主提供的会话可视化目录，其次用当前项目可写目录。首次创建选择未使用的路径，之后沿用该看板路径。

```sh
python3 "/插件安装路径/scripts/render_trends_board.py" render --input "/本轮输入/trends.json" --output "/看板路径/product-trends.html"
python3 "/插件安装路径/scripts/render_trends_board.py" snapshot "/看板路径/product-trends.html"
```

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

`updated` 的每条 `entries` 包含 `title`、`source`、`summary`、`url`，可选 `date`（YYYY-MM-DD）和 `key`（例如公开号或公开号加事件）。`source` 可注明「厂商规格」「授权公告」「RSS 摘录」等口径。更新前可用 `snapshot` 读取各栏上次成功日期、条目和状态。`unchanged` 和 `failed` 不传新条目。`failed` 必须提供原因。以脚本返回的绝对文件路径渲染。

For English requests set `"language": "en"` and write all generated entry titles, summaries and notes in English. Preserve source identities and URLs. Include this language in any scheduled refresh prompt.

在支持内嵌可视化的 Codex 回复中单独输出一行引用，路径填入脚本返回值。

```text
visualize{"path":"/绝对路径/product-trends.html","mode":"wide"}
```

先展示首版。明确要求独立 Cron Job 时，按[定时任务流程](../create-scheduled-task/SKILL.md)确定目标项目，并把看板放在该项目的持久可写路径。普通聊天内定期跟进沿用同一聊天。产品、频率、执行时间、时区和通知按本次请求确定。调度提示须包含产品范围、数据来源、既有看板和渲染器的实际绝对路径、比较与失效保留规则，并要求每轮返回同一路径的可视化引用。草案或单次查看只交付当前结果。

只有宿主返回成功才汇报任务已启用。没有内嵌渲染或调度能力时，如实汇报可用产物、失败及未覆盖项。不要把看板来源错误写成没有变化。
