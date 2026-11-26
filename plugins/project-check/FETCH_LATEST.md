# fetch-latest · 插件内置技术发现 App

`fetch-latest` 是现有「项目检查」插件内置的本地服务与 MCP App，通过同一个 `scripts/run_mcp.py --server fetch-latest` 入口启动。安装插件即可使用，无需另装插件或 Node.js；前端页面已构建为 `assets/fetch-latest/app.html`。

用这个 App 可以选择资讯，继续讨论具体技术的产品适配。需要把技术、专利和资讯汇总在同一看板或放进 Scheduled 定期查看时，使用 `$trends-board`。 [产品趋势看板使用指南](TRENDS_BOARD.md)

## 使用

在安装此版本的项目检查插件后，新开聊天，输入：

> 使用 fetch-latest 演示把新技术应用到空气炸锅，打开技术选择 App。

App 提供实时新闻/演示数据切换、产品选择与 JSON 档案编辑、技术选择、可编辑的提问文本和“发送给模型”。技术卡片通栏显示，点击标题或 + 后高亮，再次点击取消。已选技术和发送操作放在列表底部，提问编辑器默认折叠；宿主不支持填草稿或拒绝填入时会展开，方便复制或继续编辑。默认实时数据；演示模式中的产品参数和技术全部明确标为示例/虚构。

点击 + 会按顺序执行：

1. `app.updateModelContext` 提交当前产品和完整已选技术快照。多选提交全部已选内容，避免覆盖丢失。
2. 宿主声明 `openai/message` 扩展时，通过官方 `@openai/mcp-extensions` 的 `message.send` 请求 `_meta["openai/message"]={target:"active",send:false}`，只把本次新增技术的标题、可用的 HTTP(S) 来源链接及一句适配请求追加到当前主输入框草稿，不自动发送，不重复附上之前已选技术。产品参数、技术简介与正文通过上一步的模型上下文提供。演示技术与没有有效来源链接的条目使用标题引用，不生成虚构链接。
3. 用户发送主输入框中的文字，或在 App 内点击“发送给模型”。App 内发送前再次同步完整上下文，再调用 `app.sendMessage`。

宿主没有草稿扩展时不会退化成自动发送，而是保留 App 内的可编辑文本。宿主拒绝请求时展示错误，保留资料。主输入框草稿由宿主维护，移除技术、修改/切换产品后，用户需要检查此前追加的文字。浏览器协议测试验证请求顺序与字段；实际 Codex 客户端能力需加载 App 后确认。

这是普通 Markdown 链接引用，不是宿主原生附件或文件标签。完整已选资料仍会进入模型上下文；缩短主输入框里的文字不等于减少同等数量的模型上下文。

App 内手动编辑过的提问在增减技术、切换或保存产品后会保留；切换产品仍会清空技术选择。需要根据最新选择替换整段提问时，点击“重新生成提问”。新建产品会生成不同 ID，避免重复新建时意外更新上一条产品档案。

“管理产品”中的未保存修改在当前 App 内按产品保留。切换产品时编辑器随之切换，返回原产品可继续编辑。已保存的产品会立即生效，宿主上下文同步失败时会单独提示。

## 产品知识库

真实产品档案默认保存在 `~/.local/share/project-check/products/`。设置 `XDG_DATA_HOME` 时使用其下的 `project-check/products/`；设置 `FETCH_LATEST_PRODUCTS_DIR` 可覆盖完整目录。App 的“管理产品”展示实际目录。

真实资料在插件目录之外，插件升级不覆盖、分发包不包含。可把该目录作为 Codex 本地项目附加文件夹，或通过 `list_products` 工具读取。App 本身通过工具取得产品数据，不依赖读取整段聊天或 Codex Memories。

`list_products` 的 `invalidFiles` 字段列出无法读取或校验的档案文件名，App 也会显示这些文件名。其他档案可以继续使用。

## 产品档案格式

App 从独立的产品档案目录加载产品。你也可以在 Codex 聊天里指定当前项目资料，并明确要求把它整理成产品档案。

单个产品是 `<id>.json`，也可以在 App 中编辑保存：

```json
{
  "id": "my-air-fryer",
  "name": "我的空气炸锅",
  "summary": "请填写真实产品概况",
  "specifications": {},
  "goals": ["改善受热均匀性"],
  "constraints": [],
  "isDemo": false
}
```

`save_product` 会更新同 ID 的档案。随插件提供的 `air-fryer-demo` 是虚构测试档案，位于 `assets/fetch-latest/demo-product.json`。

## 固定输出格式

`fetch_latest` 参数为 `query`（关键词）、`product_id`（默认示例）、`mode`（live/demo）、`limit`（1–10）和 `language`（cn/en）。`list_products` 和 `fetch_latest` 默认返回英文，明确要求中文时传 `language="cn"`。App 沿用所选语言渲染界面并生成草稿。英文模式跳过明确标注为其他语言或标题及摘录中含有中文的新闻条目。用户保存的产品档案和输入的关键词保留原文。

工具的 `structuredContent` 是声明了 `outputSchema` 的获取回执：`schemaVersion/fetchedAt/mode/language/query/productId/count`。完整数据在工具结果 `_meta["fetch-latest/payload"]`，由 Pydantic 和 UI 的 Zod schema 验证：

```json
{
  "schemaVersion": "1.0",
  "fetchedAt": "2026-11-19T06:00:00Z",
  "mode": "demo",
  "language": "cn",
  "query": "air fryer technology airflow",
  "product": { "id": "air-fryer-demo", "name": "示例", "summary": "示例", "specifications": {}, "goals": [], "constraints": [], "isDemo": true },
  "items": [{ "id": "demo-1", "title": "技术标题", "summary": "技术简介", "content": "技术内容", "source": "虚构演示资料", "sourceUrl": null, "publishedAt": null, "contentKind": "demo" }]
}
```

完整技术正文只进入 UI，点击 + 后才提交到模型，便于测试上下文传递。`list_products` 的产品资料对模型可见。模型获得过的资料不能通过后来取消选择来抹除。

实时模式默认获取 Google News RSS 搜索结果，按发布时间排序并去重。可用 `FETCH_LATEST_FEED_URL` 配置自己的 RSS/Atom 源（配置固定源时 query 仅作为界面检索说明，不对该源执行搜索）。`contentKind="excerpt"` 表示来源提供的摘录；不把摘要伪装为新闻全文。网络失败如实报错，不静默切换演示数据。
