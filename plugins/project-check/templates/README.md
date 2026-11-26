# 项目检查报告模板

`project-check-report.md`、`project-check-report.html`、`project-check-report.docx`
分别是 Markdown、HTML 和真正的 Word 模板。`report-layout.json` 记录三种格式
共同的章节和字段，覆盖三个远程 MCP 的全部 29 个工具步骤，以及项目背景、阶段
结论、证据、已知限制、下一步和实际调用记录。

报告可以在任何阶段生成：只有资料、一个 MCP、多个 MCP 或长对话均可。
没有最低调用次数或总结时限。只使用当前可见内容，不为补齐模板新增分析。
完整模板保留全部可用章节；实际导出的报告只显示有内容的章节。一个 MCP／
方向没有任何有内容的子章节时，其方向标题也不显示。

根目录中的模板为中文；`en/` 中是字段 ID 完全一致的英文模板。英文环境应在
输入中设置 `"language": "en"`，此时报告标题、章节名、方向名、HTML 导航和
Word 模板全部使用英文。正文也必须由调用方提供英文内容，渲染器不会擅自翻译。

## HTML 布局模板

`html-template-catalog.json` 是可读取、可扩展的 HTML 布局目录，模板文件位于
当前语言目录的根部和 `html-templates/` 文件夹。模板的主要差异是图片区、
正文、主栏、侧栏、证据区和行动区的位置；颜色只是次要样式。当前包含：

- `standard`：通用长文，题图在标题下方，正文单栏纵向展开。
- `triz-solution`：方案展示，概况和方案图左右分栏，证据与行动并列。
- `cost-optimization`：决策看板，核心分析在主栏，证据、限制和行动在侧栏。
- `evidence-dossier`：证据档案，证据文字与图片并排，分析正文和行动分区。

输入 JSON 可设置 `"html_template": "triz-solution"`；命令行也可用
`--html-template triz-solution` 覆盖。布局模板只影响 HTML，Markdown 和 Word 不受
影响。未指定时使用目录中的 `default`。

自定义布局时，复制最接近的 HTML 到当前语言目录下的 `html-templates/`，再在
目录文件中增加唯一 ID、相对文件路径、中英文名称／说明和推荐场景。必须保留
所有 `data-section` 容器和 `{{字段ID}}` 占位符；可以把完整章节容器移动到新的
`data-region` 区域，增加 `data-image-slot` 图片槽，并调整网格、栏位和阅读顺序。
自定义模板根目录同样使用根级目录文件，英文版本放在 `en/` 下。

图片槽是可选的。模板中的 `<figure data-image-slot="hero">`、
`<figure data-image-slot="secondary">` 决定图片出现的位置；没有提供图片时，
对应元素从成品中删除。`standard` 仅提供 `hero`，其他三个布局提供 `hero` 和
`secondary`。图片不会自动嵌入 Markdown 或 Word。

## 填充方式

输入 JSON 的 `sections` 对象只包含已有内容，例如：

```json
{
  "language": "cn",
  "html_template": "triz-solution",
  "images": {
    "hero": {
      "src": "assets/solution-diagram.svg",
      "alt": "方案结构图",
      "caption": "概念方案和验证路径"
    }
  },
  "sections": {
    "project_context": "当前实际方案和范围",
    "rd-cost.map_component_costs": "已经得到并确认的组件成本基线"
  }
}
```

`language` 支持 `cn` 和 `en`，默认是 `cn`。命令行的 `--language en` 可以覆盖
输入值，适合宿主已经明确识别出英文环境的场景。`html_template` 必须是布局
目录中已注册的 ID。`images` 的键必须对应所选模板的图片槽；`src` 支持
`http://`、`https://` 或相对于导出 HTML 的安全相对路径，`alt` 和 `caption`
可选。不存在的槽位、绝对路径和 `../` 路径会报错，避免图片被静默丢弃或越界。

其他字段省略、空字符串、仅空白字符或 null 时，对应章节及标题不进入成品。
字段值只接受文本，实际工具 JSON 由宿主模型整理为可读内容。未知字段会报错，
避免内容被悄悄丢弃。

```bash
python3 scripts/render_project_check_report.py --input reports/input.json --output-dir reports
```

默认生成 `.md`、`.html`、`.docx` 三份。`--formats` 可选择其中一种或逗号分隔
的多种格式。相同文件名已存在时自动追加序号，不覆盖旧报告。正文没有字数
截断，也不会自动访问上游、补充事实或写入“待补充”等占位结论。

## 修改样式

- Markdown、HTML：修改对应文件的标题、排版和样式，保留 `{{字段ID}}` 占位符。
  Markdown 的 `report-block` 起止注释和 HTML 的 `data-section` 容器用于按内容
  选择章节，也必须保留。HTML 可移动整段 `data-section` 来形成不同布局，不能
  拆开或重复同一章节；`data-image-slot` 用于声明可选图片位置。
- Word：直接编辑 docx 的样式、标题和页边距。填充位置是独立段落里的隐藏
  占位符，且章节标题必须是占位符之前最近的 Heading 1 或 Heading 2 段落；
  在 Word 中显示隐藏文字即可查看。导出时替换有内容的占位符，并删除空章节。
- 三种模板应保留章节清单中的全部字段，未使用的字段及标题不会进入成品。
  可以通过 `--template-dir` 指定自定义模板根目录；英文模板放在该目录的
  `en/` 子目录中。

章节清单的工具字段与插件工具展示名配置一起校验，防止新增 MCP 后漏掉模板。
开发者可以用 `scripts/build_report_templates.py` 重建基础模板，该构建脚本
需要 python-docx；使用模板导出报告的运行脚本只需要 Python 标准库。
