"""Proxy configured MCPs with shared navigation and invocation disclosure.

Codex owns the process lifetime. Tools, arguments, tool results and page callback
tools are forwarded by FastMCP. HTML resources, including those embedded in tool
results, receive the same navigation; text, JSON and binary content pass through.
Tool discovery supplies display names and disclosure guidance for the host model.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path

from fastmcp import Client
from fastmcp.resources import ResourceResult
from fastmcp.server import create_proxy
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.tools import ToolResult
from mcp_types import CallToolResult, EmbeddedResource, TextResourceContents

LOGO_ORIGIN = "https://static-eureka.patsnap.com"
NAV_FILE = Path(__file__).resolve().parents[1] / "assets" / "eureka-nav.html"
NAV_ID = 'id="project-check-eureka-nav"'
DISPLAY_NAMES_FILE = NAV_FILE.with_name("tool-display-names.json")
DISCLOSURE_FILE = NAV_FILE.parent.parent / "skills" / "project-check" / "references" / "call-disclosure.md"
CONTINUATION_FILE = DISCLOSURE_FILE.with_name("continuation-and-reporting.md")
LANGUAGE_RULES_FILE = DISCLOSURE_FILE.with_name("response-language.md")
VERSION = "0.9.0"


class NavigationPosition(HTMLParser):
    """Find a document body without mistaking script strings for HTML tags."""

    def __init__(self, html: str):
        super().__init__(convert_charrefs=False)
        self.html = html
        self.lines = html.splitlines(keepends=True)
        self.body = self.head_end = self.html_start = self.doctype_end = None
        self.feed(html)

    def character_position(self):
        line, column = self.getpos()
        return sum(map(len, self.lines[:line - 1])) + column

    def handle_starttag(self, tag, attrs):
        end = self.character_position() + len(self.get_starttag_text())
        if tag == "body" and self.body is None:
            self.body = end
        elif tag == "html" and self.html_start is None:
            self.html_start = end

    def handle_endtag(self, tag):
        if tag == "head" and self.head_end is None:
            self.head_end = self.html.index(">", self.character_position()) + 1

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype") and self.doctype_end is None:
            self.doctype_end = self.html.index(">", self.character_position()) + 1

    def insertion_offset(self):
        # MCP Apps may return either full documents or HTML fragments.
        return next((p for p in (self.body, self.head_end, self.html_start, self.doctype_end) if p is not None), 0)


def is_html(content, mime_type):
    return isinstance(content, str) and (mime_type or "").split(";", 1)[0].strip().lower() == "text/html"


def decorate_html(html, meta, navigation):
    if NAV_ID not in html:
        offset = NavigationPosition(html).insertion_offset()
        html = html[:offset] + navigation + html[offset:]
    meta = deepcopy(meta) if meta else {}
    domains = meta.setdefault("ui", {}).setdefault("csp", {}).setdefault("resourceDomains", [])
    if LOGO_ORIGIN not in domains:
        domains.append(LOGO_ORIGIN)
    return html, meta


def add_navigation(result: ResourceResult, navigation: str) -> ResourceResult:
    """Decorate HTML without changing the upstream result or its CSP entries."""
    decorated = result.model_copy(deep=True)
    for item in decorated.contents:
        if not is_html(item.content, item.mime_type):
            continue
        item.content, item.meta = decorate_html(item.content, item.meta, navigation)
    return decorated


def add_tool_navigation(result: ToolResult, navigation: str) -> ToolResult:
    """Handle embedded HTML resources without changing plain tool results."""
    content = []
    changed = False
    for block in result.content:
        if isinstance(block, EmbeddedResource) and isinstance(block.resource, TextResourceContents) and is_html(block.resource.text, block.resource.mime_type):
            block = block.model_copy(deep=True)
            block.resource.text, block.resource.meta = decorate_html(block.resource.text, block.resource.meta, navigation)
            changed = True
        content.append(block)
    if not changed:
        return result
    wire_result = result.to_mcp_result()
    if isinstance(wire_result, CallToolResult):
        # Preserve the exact upstream wire result, including extension fields.
        return ToolResult.from_mcp_result(wire_result.model_copy(update={"content": content}))
    return ToolResult(content=content, structured_content=result.structured_content, meta=result.meta, is_error=result.is_error)


class EurekaNavigationMiddleware(Middleware):
    def __init__(self, navigation: str):
        self.navigation = navigation

    async def on_read_resource(self, context: MiddlewareContext, call_next) -> ResourceResult:
        result = await call_next(context)
        return add_navigation(result, self.navigation)

    async def on_call_tool(self, context: MiddlewareContext, call_next) -> ToolResult:
        return add_tool_navigation(await call_next(context), self.navigation)


class InvocationDisclosureMiddleware(Middleware):
    """Expose friendly identities and disclosure guidance without renaming tools."""

    def __init__(self, display_name: str, tool_names: dict[str, str], language: str = "en"):
        self.display_name = display_name
        self.tool_names = tool_names
        self.language = language

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        tools = await call_next(context)
        result = []
        for original in tools:
            tool = original.model_copy(deep=True)
            english = self.language == "en"
            title = self.tool_names.get(tool.name) or tool.title or ("Upstream tool" if english else "上游工具")
            tool.title = title
            disclosure = (
                f"Project Check · {self.display_name} · {title}. "
                "Before calling, identify the plugin, service and tool in the user's language. "
                "In the final reply, disclose actual calls and their outcomes. Offer relevant next steps "
                "and, when appropriate, ask whether to export a report. Keep questions, results and follow-ups in the request language."
                if english else
                f"本工具属于「项目检查」插件的「{self.display_name}」MCP，展示名称为「{title}」。\n"
                "调用前第一行用 Markdown 加粗说明插件、MCP 和工具的展示名称，"
                "并标注“准备调用”；本轮最终回复第一行汇总实际调用及成功／失败状态。"
                "未调用时如实说明，不用函数名或变量名代替展示名称。"
                "返回后推荐 1–3 条以“【项目检查插件】”开头的下一步；"
                "本轮回答结束时询问是否按模板生成文档，已交付或用户拒绝时不重复询问。"
            )
            tool.description = disclosure + "\n\n" + (original.description or "")
            tool.meta = deepcopy(original.meta) if original.meta else {}
            # Host support varies; these labels supplement the model's prose.
            if english:
                tool.meta["openai/toolInvocation/invoking"] = f"Project Check · {self.display_name} · Calling {title}"
                tool.meta["openai/toolInvocation/invoked"] = f"Project Check · {self.display_name} · {title} returned"
            else:
                tool.meta["openai/toolInvocation/invoking"] = f"项目检查 · {self.display_name} · 正在调用{title}"
                tool.meta["openai/toolInvocation/invoked"] = f"项目检查 · {self.display_name} · {title}已返回"
            result.append(tool)
        return result


def build_proxy(target, *, navigation: str | None = None, name=None, server: str | None = None, language: str = "en"):
    english = language == "en"
    catalog_path = DISPLAY_NAMES_FILE.with_name("tool-display-names.en.json") if english else DISPLAY_NAMES_FILE
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    service = catalog.get(server, {})
    display_name = service.get("display_name", "Project Check Service" if english else "项目检查服务")
    plugin_name = "Project Check" if english else "项目检查"
    instructions = f"{plugin_name} · {display_name}\n\n" + LANGUAGE_RULES_FILE.read_text(encoding="utf-8")
    if english:
        instructions += (
            "\nBefore a tool call, identify the plugin, service and tool in a bold first line. "
            "In the final reply, disclose actual calls in the first line and distinguish completed, failed and reused results. "
            "Offer one to three relevant next steps and ask if the user wants a report, unless they declined or a report was already delivered. "
            "Use the request language throughout."
        )
    else:
        instructions += "\n\n" + DISCLOSURE_FILE.read_text(encoding="utf-8") + "\n\n" + CONTINUATION_FILE.read_text(encoding="utf-8")
    # Current upstreams implement the handshake-era MCP protocol.
    upstream = Client(target, timeout=600, init_timeout=20, mode="legacy")
    proxy = create_proxy(
        upstream,
        name=name or f"{plugin_name} · {display_name}",
        instructions=instructions,
        version=VERSION,
        provider_error_strategy="raise",
    )
    proxy.add_middleware(EurekaNavigationMiddleware(
        NAV_FILE.read_text(encoding="utf-8") if navigation is None else navigation
    ))
    proxy.add_middleware(InvocationDisclosureMiddleware(display_name, service.get("tools", {}), language))
    return proxy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True)
    parser.add_argument("--upstream-url")
    args = parser.parse_args()
    if args.server == "fetch-latest":
        if __package__:
            from .fetch_latest import build_server
        else:
            from fetch_latest import build_server
        local = build_server()
        local.add_middleware(EurekaNavigationMiddleware(NAV_FILE.read_text(encoding="utf-8")))
        local.run(transport="stdio", show_banner=False, log_level="ERROR")
        return
    if not args.upstream_url:
        parser.error("--upstream-url is required for upstream MCP services")
    build_proxy(args.upstream_url, server=args.server).run(
        transport="stdio", show_banner=False, log_level="ERROR",
    )


if __name__ == "__main__":
    main()
