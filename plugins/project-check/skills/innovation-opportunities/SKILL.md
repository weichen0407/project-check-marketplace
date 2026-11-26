---
name: innovation-opportunities
description: Check similar technologies, technical differences, and alternative engineering approaches. Use for novelty checks or TRIZ innovation. 检查当前技术方案的相近技术、差异与创新机会，并按需寻找替代技术路线。用户要求“查新”“这个方案有新意吗”“寻找创新点”“还有其他技术路线吗”时使用；不用于商业营销创意、普通头脑风暴或知识概念解释。
---

# 创新机会

Follow the [request language rules](../project-check/references/response-language.md). For an English request, use English throughout this workflow.

同时遵循[下一步建议与文档询问](../project-check/references/continuation-and-reporting.md)：
每次调用结束推荐带「【项目检查插件】」的下一步，每轮回答末尾询问是否生成
文档；用户同意时按完整模板映射已有结果，未涉及章节不输出，不为补齐报告重跑。

进入本流程时先遵循[插件调用提示](../project-check/references/call-disclosure.md)：
首条可见回复和本轮最终回复均以加粗的插件／MCP／工具展示名称开头。
本场景使用「TRIZ 创新」和按需使用「TRIZ 案例库」MCP，如实区分准备调用、
实际调用与未调用。

以当前聊天中可见的方案、技术特征和目标为输入，保留用户已确认的事实与
约束。无法确定要检查哪个方案时才先澄清，不索取已经可见的材料。

使用 `triz` MCP。调用前说明场景、MCP 和工具；结束时汇总实际
调用和失败项。出现网关或工具错误时报告受阻阶段，不自动回退到其他入口。

用户明确要求已有案例、跨行业案例或科学效应参考时，先读取并遵循
[TRIZ 案例库](../triz-case-library/SKILL.md)，使用 `triz-case-library`；仅查案例时
到此结束，不强制生成方案。一般创新分析不必额外检索案例库。需要组合生成
方案时将案例作为带来源的背景，不把案例的 `cases` 冒充 `data.evidence`。

1. 首次使用 `triz` 或当前缺少完整流程说明时，调用 `readme`。
2. 检查已有方案的新颖性线索时，调用 `search_solution_evidence` 检索相近
   技术。以真实专利标识和返回内容对照方案，说明共性、差异及检索边界。
   仅检查已有方案不自动变成生成新方案。
3. 用户要求创新点、替代方案或其他路线时，调用 `generate_concept_solutions`。
   原始问题放入 `user_problem`，当前约束放入 `context_input`。已有适用
   证据时将 `data.evidence` 原样传入 `evidence`，不要塞到背景中。
4. 用户同时要求分析原因与生成方案时，可先调用 `analyze_causal_chain`，
   由用户选定最多三个关键问题再继续；保留完整 `key_problems` 与因果路径。
   单独生成方案不强制增加这一步。
5. 用户选定概念后，使用完整 `solution` 调用 `generate_solution_detail`；
   用户自带的一句话方案可以通过 `solution_description` 展开。

输出相近技术、当前方案差异、创新方向、证据与下一步验证。差异仅代表
当前检索中的线索，不表述为“已经证明新颖性”或“必然可授权”。生成方案
的评分、可行性与图片属于初步结果。

复用上游工具实际返回的证据、概念方案和详情页面；无页面时给文本结果。
“继续”“换一批”尊重已有步骤与仍匹配的证据。无结果或失败应如实说明，
不能将模型假设伪装成工具返回的证据。
