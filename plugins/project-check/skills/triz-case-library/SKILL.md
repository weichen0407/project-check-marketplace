---
name: triz-case-library
description: Search existing TRIZ examples by technical contradiction, function, technical effect, or scientific effect. 检索已有 TRIZ 技术案例，按技术矛盾、功能描述、技术功效、科学效应或关键词寻找参考。用户要求“找类似技术案例”“跨行业案例”“按科学效应找案例”“TRIZ 案例库”或指定 patsnap-triz-case-library 时使用；生成新方案交给创新机会场景，不用于普通案例写作或侵权判断。
---

# TRIZ 案例库

Follow the [request language rules](../project-check/references/response-language.md). For an English request, use English throughout this workflow.

同时遵循[下一步建议与文档询问](../project-check/references/continuation-and-reporting.md)：
每次调用结束推荐带「【项目检查插件】」的下一步，每轮回答末尾询问是否生成
文档；用户同意时按完整模板映射已有结果，未涉及章节不输出，不为补齐报告重跑。

进入本流程时先遵循[插件调用提示](../project-check/references/call-disclosure.md)：
首条可见回复和本轮最终回复均以加粗的插件／MCP／工具展示名称开头。
本场景的 MCP 展示名称为「TRIZ 案例库」，使用 `triz-case-library` 服务。
该服务没有 `readme`，不调用其他服务的流程说明代替案例检索。

从当前聊天提取技术问题、要改善的性能、不能恶化的性能及已有领域信息。
上下文足够时直接检索；对象不明时才补问。用户只要案例时，不额外运行组件
分析或生成方案。

## 检索与标准词

1. 按实际工具 Schema 调用 `search_triz_case`。至少提供一个非空条件：
   `technical_contradiction`、`svop`、`efficacy`、`oxford_effects` 或 `keyword`；
   `filters` 只能附加过滤，不能单独检索。关键词最多五个，初次通常取十条
   以内，用户有数量要求时依其要求，单次不超过工具上限 200。
2. 不确定标准 TRIZ 参数 ID、SVOP 标准动词或参数时，先用自然语言关键词；
   不凭印象编造编号或标准词。技术矛盾的工程参数 ID 范围为 1–39，发明原理
   ID 为 1–40。使用这些字段时须有可确认的映射。
3. 使用 `efficacy` 或 `oxford_effects` 前，先通过 `list_triz_search_terms`
   查询对应字段；已有本次所需词表时复用。只按返回的原始英文拼写传参，
   不翻译字段值。词表是常用子集，`truncated=true` 不代表完整词库；没有
   合适条目时可改用关键词，不声称该技术功效或科学效应不存在。
4. 不同检索类型之间按 AND 组合；单个技术矛盾或 SVOP 对象内各条件为 AND，
   同类型多个对象为 OR。不要一次堆叠无关条件而误缩检索范围。没有结果时，
   根据用户原意减少条件或换关键词，说明实际修改；无额外要求最多三次检索。
5. 国家／地区、法律状态、申请人和 IPC/CPC 等过滤只在用户要求或有明确
   领域依据时使用。跨行业检索可使用 `ipc_cpc_exclude` 排除已知本领域分类；
   未确认分类号时不要猜测。空结果、失败和词表缺失分别说明。

## 结果与后续

保留真实 `case_id`，展示返回的问题摘要、效果摘要、创新点及适用的 TRIZ
标注，解释对当前问题的启发、差异和验证条件。案例 ID 不是专利公开号；
未返回专利标识、链接、图片或成本数据时，不自行补造成上游证据。

案例库返回的是已有案例，不等于新方案生成、新颖性证明或不侵权结论。
目前没有 UI 资源，使用真实文本和结构化结果，不创建演示页面。后续若返回
HTML，会经共享代理添加 Eureka 导航。

用户要求基于案例继续创新时，转到[创新机会](../innovation-opportunities/SKILL.md)，
把案例摘要、ID 和适用限制作为有来源的背景。案例的 `cases` 不能原样当作
TRIZ 创新工具的 `evidence`；证据字段仅接收其 Schema 认可的结构。
