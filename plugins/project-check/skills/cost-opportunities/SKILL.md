---
name: cost-opportunities
description: Find ways to reduce engineering costs while maintaining performance, including material, process, and design changes. 分析当前工程技术方案的降本机会、替代材料、结构简化或工艺改进。用户询问“有没有更便宜的做法”“降低这个方案成本”“成本合理吗”时使用；不用于一般省钱建议、财务预算或没有具体方案的概念问答。
---

# 研发降本

Follow the [request language rules](../project-check/references/response-language.md). For an English request, use English throughout this workflow.

同时遵循[下一步建议与文档询问](../project-check/references/continuation-and-reporting.md)：
每次调用结束推荐带「【项目检查插件】」的下一步，每轮回答末尾询问是否生成
文档；用户同意时按完整模板映射已有结果，未涉及章节不输出，不为补齐报告重跑。

进入本流程时先遵循[插件调用提示](../project-check/references/call-disclosure.md)：
首条可见回复和本轮最终回复均以加粗的插件／MCP／工具展示名称开头。
本场景的 MCP 展示名称为「研发降本」，如实区分准备调用、实际调用与未调用。

使用 `rd-cost` MCP 运行研发降本流程。
从当前可见会话提取产品、成本目标、性能约束与最新修正，不发送无关历史。
调用前说明当前场景、MCP 名称及要调用的工具；结束时汇总实际调用和失败项。

1. 首次使用或缺少研发降本流程说明时，调用 **rd-cost 的** `readme`。
   依据实际工具 Schema 填参；若网关返回错误，报告原始错误与受阻阶段，
   不自动切换其他入口，也不把其他 MCP 的同名 readme 当作成功结果。
2. 明确产品对象、工况、性能底线和成本来源。已有 BOM 时使用
   `standardize_bom`；没有 BOM 时使用 `map_component_costs`。文件仅在用户
   提供时按 `upload_file` 的支持格式处理，不把本地路径冒充下载地址。
3. 展示返回基线中的事实、估算和警告，等待用户确认或修正，再进行下游
   分析。保留完整 `baseline`，用户确认后不要重复生成或混用其他版本。
4. 依用户目标选择方法。未指定方法时优先以 `value_engineering` 做一轮
   初步分析；用户可选 `first_principles` 或 TRIZ 裁剪流程。TRIZ 三阶段为
   `triz_analyze_trimming` → `triz_retrieve_patents` → `triz_generate_solutions`，
   沿用同一基线及对应的完整中间结果。
5. 用户要求完整三维降本时，根据工具目录调用七个 `three_dimensional_*`
   方法，共享已确认基线；部分失败保留成功候选，不声称七种方法均完成。
6. 将实际返回的候选池交给 `evaluate_solutions`；需要最终交付时再调用
   `generate_report`，传入同一基线和对应的完整评估结果。

输出基线、候选方案、证据、收益假设、工程取舍和验证动作。供应商报价、
用户给定成本、工程估算分别标注，工具估算不等于实测节省。未取得可信可比
成本时不给确定的节省比例。仅解释已有结果时不重跑全部方法。

复用研发降本工具实际返回的 MCP Apps 页面。`generate_solution_image`
仅供原页面调用，不作为模型必经步骤。若页面未显示，仍给可读文本。
