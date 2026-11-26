---
name: project-check-report
description: Export existing findings as an English or Chinese report in Markdown, HTML, or Word. 将项目检查工具结果、当前技术方案讨论和用户资料整理成阶段报告，支持单个 MCP、多个 MCP 或长上下文，输出 Markdown、HTML、Word。用户要求“把刚才结果总结成文档”“生成项目检查报告”“按模板导出报告”时使用。
---

# 项目检查报告

Follow the [request language rules](../project-check/references/response-language.md). For an English request, use English throughout this workflow.

先遵循[调用提示](../project-check/references/call-disclosure.md)与
[下一步和文档规则](../project-check/references/continuation-and-reporting.md)。
只整理现有结果时，首行加粗说明启用「项目检查」插件、复用已有结果且本轮
未新调用 MCP 分析工具；不要为了报告标识而额外调用上游。

## 任何阶段都可以总结

- 一个工具或一个 MCP 完成后、两个场景完成后、长对话或资料讨论后，用户
  均可要求报告。没有最低完整度、固定时点、字数上限或总结截止时间。
- 使用当前可见对话、用户提供且实际读取的文档、工具的文本／结构化结果。
  不能声称读取了其他聊天或已经不可见的历史。长上下文先按方案和阶段整理，
  保留用户最新修正、约束、证据和结果版本；不混用不同方案的基线。
- 页面选择或编辑只有已回传、可读取时才能作为最新事实；页面独有且未同步
  的内容不能靠猜测补齐。已有的报告 markdown 可作为来源，但要保留事实与
  模型解释的区别。

## 模板与填充规则

读取 [模板说明](../../templates/README.md) 和对应语言的章节清单。三种格式的
完整模板覆盖项目背景、阶段结论、三个远程 MCP 的全部工具步骤、证据、已知限制、
下一步和实际调用记录。中文模板位于 `templates/`，英文模板位于
`templates/en/`，用户可以直接调整相应格式。

把现有信息写入 UTF-8 JSON：

```json
{
  "language": "cn",
  "sections": {
    "project_context": "当前方案、检查范围和已经明确的约束",
    "triz-case-library.search_triz_case": "实际查到的案例及来源"
  }
}
```

- 所有值均为文本；将实际结果整理成可读段落、列表和证据引用。工具字段 ID
  采用章节清单中的 `MCP 配置名.工具代码名`，不把案例 ID 当专利公开号。
- 只填已有内容。未涉及或缺失字段省略或用空字符串；导出时连同对应章节标题
  一起省略。一个 MCP／方向的全部子章节都没有内容时，也省略该方向标题。
  不填占位结论，不自动写成“无风险”或“不存在机会”。
- `project_context` 只写实际范围；`tool_history` 只写本轮及所采用历史中能确认
  的调用。已知失败写入 `limitations`，不将未知状态补造成成功或失败。
- 用户材料、工具证据和模型分析分别说明。没有成本依据就不补节省率；没有
  专利分析就不补法律判断。允许只填项目背景或一个场景，其余章节不输出。
- 不新增分析来填满报告。若用户同时要求补做分析，先按其范围进入对应场景，
  不将报告生成混同为上游报告工具已执行。

## HTML 模板选择

需要生成 HTML 时，先读取 [HTML 模板目录](../../templates/html-template-catalog.json)。
如果用户尚未指定模板，先用一个简短问题让用户选择；列出与当前内容最相关的
2–4 个布局，把推荐项放在第一位并说明一句栏位和图片区适用原因。用户已指定模板、明确说
“默认即可”或要求直接生成时，不重复询问。

按当前对话内容推荐：

- TRIZ、创新点、概念方案或方案详情：`triz-solution`。
- BOM 成本、价值工程或降本方案：`cost-optimization`。
- 以证据为主、需并列展示来源和图片：`evidence-dossier`。
- 多场景混合或普通阶段总结：`standard`。

用户确认后，在输入 JSON 写入 `"html_template": "模板ID"`。只生成 Markdown
或 Word 时不询问 HTML 模板。英文环境用目录中的英文名称和说明提问。

模板必须体现结构变化，不把只换配色的文件当作新模板。用户要求模仿自己的
偏好时，可以复制最接近的 HTML 布局到自定义模板目录并注册新 ID；保留全部
`data-section` 容器和字段占位符，在不同 `data-region` 之间移动完整章节，调整
图片区、正文、主栏、侧栏、证据区和行动区。不要把一次性偏好写回公共模板。

用户提供图片且选择 HTML 时，把图片写入顶层 `images`：`hero` 是主图，
`secondary` 是辅助图；每项包含 `src`，可选 `alt` 和 `caption`。只使用所选模板
实际声明的 `data-image-slot`。未提供图片时不生成空框；Markdown 和 Word 不使用
这些槽位。图片相对路径按导出 HTML 所在目录解析。

## 输出语言

- 按用户明确指定或当前请求的语言选择 `language`。中文使用 `cn`，英文使用 `en`。
  将标题、正文章节、图注和交付说明写成同一语言。源文本和标识可按引用需要保留。
- 英文环境必须使用英文模板，并把所有实际填写的正文整理为英文。报告标题、
  章节标题、MCP／方向名称、HTML 导航和 Word 内容不得残留中文。
- 渲染器不翻译正文。不能把中文内容放进英文模板后声称报告已完全英文化。

## 导出文件

用户未指定格式时生成 Markdown、HTML、Word 三份；指定格式时只生成所选格式。
在当前项目的可写目录保存输入和报告，不把业务内容写入插件的 `templates/`。

通过可用的本地命令工具执行插件中的
[报告导出脚本](../../scripts/render_project_check_report.py)，无需额外模型 API。
下面路径均相对于本 Skill 文件所在目录解析，执行时使用真实绝对路径，不把
当前工作目录误当成插件目录：

```bash
python3 /插件真实目录/scripts/render_project_check_report.py \
  --input /当前项目/reports/report-input.json \
  --output-dir /当前项目/reports
```

默认导出三种格式。仅指定一种可加 `--formats md`、`--formats html` 或
`--formats docx`；英文环境在输入中设置 `"language": "en"`，或加
`--language en`；HTML 布局可加 `--html-template 模板ID`；使用自定义模板目录
可加 `--template-dir /真实模板目录`。
脚本只使用 Python 标准库，读取模板、校验字段和生成文件，不联网、不触发 MCP。
不会截断文本，也不会覆盖同名旧报告，而是自动使用新的文件名。

执行后确认返回的文件确实存在，检查正文、语言和未涉及章节确已省略，再给用户
真实文件链接。
Word 布局有修改时，使用宿主可用的文档渲染能力检查。若当前宿主没有本地
文件执行能力，可先按 Markdown 模板在聊天中输出，明确没有生成下载文件，
不能把 Markdown 重命名成 docx 冒充 Word。

文档交付后给出带「【项目检查插件】」的后续更新建议；不重复询问是否生成
刚刚已交付的文档。用户继续讨论后，可随时以新增事实再次更新报告。
