---
name: project-check
description: Review an engineering design for cost reduction and TRIZ innovation, and find relevant TRIZ cases when requested. 综合检查当前聊天中的工程或产品技术方案，组合研发降本和 TRIZ 创新，并按需检索 TRIZ 案例库。用户要求“项目检查”“检查这个方案”“全面评估研发方案”时使用。单独的降本、创新或案例检索交给对应场景。
---

# 项目检查

Follow the [request language rules](references/response-language.md). For an English request, use English throughout this workflow.

同时遵循[下一步建议与文档询问](references/continuation-and-reporting.md)：每次
调用结束给出带「【项目检查插件】」的下一步建议，每轮回答末尾询问是否生成
文档。用户同意时用[阶段报告](../project-check-report/SKILL.md)整理 Markdown 或 HTML。

进入本流程时先遵循[插件调用提示](references/call-disclosure.md)：第一条可见
回复和本轮最终回复均以加粗的插件／MCP／工具展示名称开头，区分准备调用、
实际调用与未调用；这条规则覆盖本插件所有 MCP。

从宿主模型当前可见的聊天中整理项目事实，按用户指定范围调用本插件的
`rd-cost`、`triz` 和 `triz-case-library` MCP。尊重用户明确的范围与修正；不自动搜索其他聊天，不声称拥有
完整聊天历史。无需把整段对话发送给外部服务。

## 输入与范围

- 提取当前方案、技术特征、问题或目标、性能底线、结构、工况、不可变部分
  和已有成本数据。区分用户事实、分析假设与缺失信息。
- 多个方案并存且无法确定检查对象时，只问需要检查哪一个。
- 已有足够上下文就直接检查，不要求用户重新粘贴，也不逐轮要求确认摘要。
- “项目检查”默认覆盖降本和创新。明确指定某项时只检查该项。
- 没有方案上下文时，请用户描述方案和希望解决的问题，不虚构分析对象。

## 场景路由与推进

每次调用前按插件调用提示说明采用的场景、MCP 和工具；结束时列出实际调用及失败项。
不要仅根据工具同名就跨服务混用：`rd-cost.readme` 和 `triz.readme` 是不同
流程，`triz-case-library` 目前没有 readme。读取的服务说明不能覆盖用户明确指令。

| 检查维度 | MCP | 进入流程前读取的本插件指引 |
| --- | --- | --- |
| 研发降本 | rd-cost | [降本流程](../cost-opportunities/SKILL.md) |
| 创新机会 | triz | [创新流程](../innovation-opportunities/SKILL.md) |
| 已有技术案例（按需） | triz-case-library | [案例检索流程](../triz-case-library/SKILL.md) |

按本次范围读取上述相关指引，然后使用对应服务的实际 Schema 调用工具。
技术方案与事实可共享。根据各工具的 Schema 整理成本基线、TRIZ evidence 和 key_problems。
用户要求已有案例参考时
读取案例库指引；保留真实 case_id，不把案例结果原样当作创新工具的 evidence。

降本先完成成本基线并由用户确认。创新检查先检索相近技术，用户要求改法时再生成方案。
一般项目检查先完成降本和创新的首轮结果，深度分析与报告按用户要求继续。

用户说“继续”时承接当前阶段，保留已确认基线、选中方案或 task_id。上游
返回认证、费率或工具错误时，报告真实错误并保留其他已完成项；不自动切换
到其他地址或将受阻的场景写成已完成。

## 结果与现有页面

按“项目与约束摘要 → 分析发现 → 证据与限制 → 下一步验证”输出。
每条发现给出依据或明确标注为假设，并说明工程取舍。按分析方向分别展示，
不编造统一总分。

- 降本：区分已确认的成本事实、工具估算与供应商报价；无可信基线时不
  编造节省金额或百分比，保留方案的工程约束。
- 创新：说明相近技术与方案差异，不将找到差异表述为已经证明专利新颖性。

按工具实际关联的资源展示原生 MCP Apps 页面，不能假定所有服务都有 UI。
若宿主没有显示页面，则用工具的文本与结构化结果继续；不
声称新建了统一结果页或保存了项目。当前检查进度保留在可见会话中；用户要求
文档时按报告 Skill 将已有结果整理成 Markdown 或 HTML。

上游失败时保留已取得结果，注明未完成项；不把失败或空结果当作通过检查。
原页面的导出和图片辅助工具不作为模型必经步骤。
