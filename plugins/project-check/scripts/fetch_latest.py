"""Product knowledge and technology news, bundled in the project-check plugin."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from http.client import HTTPException
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Annotated, Literal
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from fastmcp import FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[1]
UI_URI = "ui://fetch-latest/app.html"
ASSETS = ROOT / "assets" / "fetch-latest"
READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
ProductId = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$")]
Language = Literal["cn", "en"]
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
HAN_TEXT = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]")


class Product(BaseModel):
    id: ProductId
    name: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=5000)
    specifications: dict[str, str] = Field(default_factory=dict)
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    isDemo: bool = False


class NewsItem(BaseModel):
    id: str
    title: str
    summary: str
    content: str
    source: str
    sourceUrl: str | None
    publishedAt: str | None
    contentKind: Literal["excerpt", "demo"]


class NewsPayload(BaseModel):
    schemaVersion: Literal["1.0"] = "1.0"
    fetchedAt: str
    mode: Literal["live", "demo"]
    language: Language
    query: str
    product: Product
    items: list[NewsItem]


class FetchReceipt(BaseModel):
    schemaVersion: Literal["1.0"] = "1.0"
    fetchedAt: str
    mode: Literal["live", "demo"]
    language: Language
    query: str
    productId: str
    count: int


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        elif tag in {"p", "br", "div", "li"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1
        elif tag in {"p", "div", "li"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value):
    parser = PlainText()
    parser.feed(value or "")
    return " ".join("".join(parser.parts).split())


def parse_feed(data: bytes, *, limit: int, language: Language = "en") -> list[NewsItem]:
    invalid_feed = "The news source did not return valid RSS or Atom data." if language == "en" else "新闻源未返回有效的 RSS 或 Atom 数据"
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise ValueError(invalid_feed) from error
    atom = "{http://www.w3.org/2005/Atom}"
    entries = root.findall(".//item") or root.findall(f"{atom}entry")
    feed_language = root.findtext("channel/language") or root.get(XML_LANG) or ""
    feed_title = root.findtext("channel/title") or root.findtext(f"{atom}title") or "RSS"
    items, seen = [], set()
    for entry in entries:
        def value(*names):
            for name in names:
                text = entry.findtext(name)
                if text:
                    return text
            return ""
        title = plain_text(value("title", f"{atom}title"))
        link = value("link")
        if not link:
            links = entry.findall(f"{atom}link")
            link = next((node.get("href", "") for node in links if node.get("rel", "alternate") == "alternate"), "")
        if urlsplit(link).scheme not in {"http", "https"}:
            link = ""
        identity = link or value("guid", f"{atom}id") or title
        if not title or identity in seen:
            continue
        body = plain_text(value("{http://purl.org/rss/1.0/modules/content/}encoded", f"{atom}content", "description", f"{atom}summary")) or title
        source = plain_text(value("source")) or plain_text(feed_title)
        if language == "en":
            declared_language = entry.get(XML_LANG) or value("{http://purl.org/dc/elements/1.1/}language") or feed_language
            if declared_language and declared_language.strip().lower().split("-")[0] != "en":
                continue
            if HAN_TEXT.search(title) or HAN_TEXT.search(body):
                continue
            if HAN_TEXT.search(source):
                source = "RSS"
        seen.add(identity)
        date = value("pubDate", f"{atom}published", f"{atom}updated")
        published = None
        if date:
            try:
                dt = datetime.fromisoformat(date.replace("Z", "+00:00")) if date[:4].isdigit() else parsedate_to_datetime(date)
                published = dt.replace(tzinfo=dt.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            except (ValueError, TypeError, OverflowError):
                pass
        items.append(NewsItem(
            id=sha256(identity.encode()).hexdigest()[:20], title=title,
            summary=body[:240] + ("…" if len(body) > 240 else ""), content=body[:30000],
            source=source, sourceUrl=link or None,
            publishedAt=published, contentKind="excerpt",
        ))
    if not entries and root.tag not in {"rss", f"{atom}feed", "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF"}:
        raise ValueError(invalid_feed)
    return sorted(items, key=lambda item: item.publishedAt or "", reverse=True)[:limit]


def demo_news(limit, language: Language = "en"):
    chinese = [
        ("动态风道调节", "按腔体区域调整气流分配，探索改善受热均匀性的可能性。", "虚构测试技术：通过可调导流叶片改变热风分配。适配时应检查风扇流量、腔体压降、叶片耐温性和清洁空间。预期效果尚未验证，需要布置多点温度测量并与原结构对照。"),
        ("多点温度感知", "利用多个温度测点辅助调整加热与风扇控制。", "虚构测试技术：在腔体不同区域布置温度传感器，根据温差调整加热占空比和风扇转速。需要评估传感器安装空间、耐温等级、控制器接口以及线束成本。"),
        ("可拆卸导流内衬", "通过可替换的内衬形状测试不同热风循环路径。", "虚构测试技术：使用可拆卸内衬形成不同的导流曲面，比较温度均匀性与清洗便利性。需要检查有效容积、食物接触材料要求及零件固定方式。"),
    ]
    english = [
        ("Adjustable air ducts", "Adjust airflow by cooking chamber zone to explore more even heating.", "Fictional test concept. Adjustable vanes redistribute hot air. Check fan flow, chamber pressure drop, heat resistance, and cleaning access. Measure temperatures at multiple points and compare with the original design."),
        ("Multi-point temperature sensing", "Use temperature readings at multiple points to guide heater and fan control.", "Fictional test concept. Sensors at several points guide heater duty cycle and fan speed. Assess mounting space, temperature ratings, controller inputs, and harness costs."),
        ("Removable airflow liner", "Test interchangeable liners to compare hot-air circulation paths.", "Fictional test concept. Compare heating uniformity and cleaning access across liner profiles. Check usable volume, food-contact materials, and how the liner is secured."),
    ]
    examples = english if language == "en" else chinese
    suffix = " (demo)" if language == "en" else "（演示）"
    source = "Fictional demo material" if language == "en" else "虚构演示资料，非真实新闻"
    return [NewsItem(id=f"demo-{index}", title=f"{title}{suffix}", summary=summary,
                     content=body, source=source, sourceUrl=None,
                     publishedAt=None, contentKind="demo")
            for index, (title, summary, body) in enumerate(examples, 1)][:limit]


def products_directory():
    if os.getenv("FETCH_LATEST_PRODUCTS_DIR"):
        return Path(os.environ["FETCH_LATEST_PRODUCTS_DIR"]).expanduser()
    return Path(os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "project-check" / "products"


def read_product(path: Path) -> Product:
    product = Product.model_validate_json(path.read_text(encoding="utf-8"))
    if product.id != path.stem:
        raise ValueError("The product ID does not match the file name.")
    return product


def build_server(*, products_dir: Path | None = None):
    directory = products_dir if products_dir is not None else products_directory()
    demos = {
        language: Product.model_validate_json((ASSETS / name).read_text(encoding="utf-8"))
        for language, name in (("cn", "demo-product.json"), ("en", "demo-product.en.json"))
    }
    server = FastMCP(
        "Project Check · Technology Discovery", version="0.9.0",
        instructions=(
            "Save product profiles, fetch technology news, and select items in the app. "
            "Use English by default. Pass language='cn' only when the user asks for Chinese output. "
            "Keep the selected output language for every follow-up, independently of the search terms and host locale. "
            "The app receives excerpts in UI metadata and attaches selected items to model context. "
            "Demo data is fictional. Live data contains RSS excerpts."
        ),
    )

    def find_product(product_id: str, language: Language) -> Product:
        demo = demos[language]
        path = directory / f"{product_id}.json"
        try:
            return read_product(path)
        except FileNotFoundError:
            if product_id != demo.id:
                message = "Product not found. Call list_products or save_product first." if language == "en" else "找不到指定产品，请先调用 list_products 或 save_product"
                raise ValueError(message) from None
        except (OSError, ValueError):
            if product_id != demo.id:
                message = f"Cannot read product profile: {path.name}" if language == "en" else f"无法读取产品档案：{path.name}"
                raise ValueError(message) from None
        return demo

    @server.tool(annotations=READ_ONLY)
    def list_products(language: Language = "en") -> dict:
        """List local product profiles and unreadable files. Set language to match the user's request for the sample profile."""
        demo = demos[language]
        saved = []
        invalid_files = []
        for path in sorted(directory.glob("*.json")):
            try:
                saved.append(read_product(path))
            except (OSError, ValueError):
                invalid_files.append(path.name)
        if all(item.id != demo.id for item in saved):
            saved.append(demo)
        return {
            "products": [item.model_dump() for item in saved],
            "knowledgeDirectory": str(directory.resolve()),
            "invalidFiles": invalid_files,
        }

    @server.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
    def save_product(product: Product) -> dict:
        """Save a user-provided product profile locally. Saving the same ID updates the profile."""
        directory.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(product.model_dump_json(indent=2) + "\n")
            os.replace(temporary, directory / f"{product.id}.json")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return {"product": product.model_dump()}

    @server.tool(
        title="Find the latest technology",
        description="Find news and technology for a product. English is the default. Pass language='cn' for explicitly requested Chinese output. The app displays RSS excerpts and lets the user select items for model context and a composer draft. Use mode='demo' only for fictional testing.",
        output_schema=FetchReceipt.model_json_schema(),
        annotations={**READ_ONLY, "openWorldHint": True},
        meta={"ui": {"resourceUri": UI_URI}, "openai/ui": {"entrypoints": [{"type": "thread"}]},
              "openai/toolInvocation/invoking": "Finding technology", "openai/toolInvocation/invoked": "Technology results are ready"},
    )
    def fetch_latest(query: str = Field(default="air fryer technology airflow", min_length=1, max_length=200),
                     product_id: ProductId = "air-fryer-demo", mode: Literal["live", "demo"] = "live",
                     limit: int = Field(default=5, ge=1, le=10), language: Language = "en") -> ToolResult:
        product = find_product(product_id, language)
        if mode == "demo":
            items = demo_news(limit, language)
        else:
            url = os.getenv("FETCH_LATEST_FEED_URL") or "https://news.google.com/rss/search?" + urlencode({"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
            headers = {"User-Agent": "project-check-fetch-latest/0.9", "Accept-Language": "en-US" if language == "en" else "zh-CN"}
            try:
                with urlopen(Request(url, headers=headers), timeout=20) as response:
                    data = response.read(4 * 1024 * 1024 + 1)
            except (HTTPException, OSError, ValueError) as error:
                message = "Could not load the news feed. Try again or check the feed URL." if language == "en" else "无法获取新闻源，请重试或检查新闻源地址。"
                raise ValueError(message) from error
            if len(data) > 4 * 1024 * 1024:
                raise ValueError("The RSS response exceeded 4 MiB." if language == "en" else "RSS 响应超过 4 MiB")
            items = parse_feed(data, limit=limit, language=language)
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        payload = NewsPayload(fetchedAt=now, mode=mode, language=language, query=query, product=product, items=items)
        receipt = FetchReceipt(fetchedAt=now, mode=mode, language=language, query=query, productId=product.id, count=len(items))
        if language == "en":
            kind = "fictional demo item" if mode == "demo" else "RSS excerpt"
            plural = "" if len(items) == 1 else "s"
            content = f"Found {len(items)} {kind}{plural}. Click + in the app to select a technology."
        else:
            kind = "虚构演示技术" if mode == "demo" else "RSS 技术新闻摘录"
            content = f"已获取 {len(items)} 条{kind}。请在 App 中点击 + 选择技术。"
        return ToolResult(
            content=content,
            structured_content=receipt.model_dump(), meta={"fetch-latest/payload": payload.model_dump()},
        )

    @server.resource(UI_URI, mime_type="text/html;profile=mcp-app", meta={
        "ui": {"prefersBorder": True, "csp": {"connectDomains": [], "resourceDomains": []}},
        "openai/ui": {"availableDisplayModes": ["inline", "fullscreen"], "preferredDisplayMode": "inline"},
    })
    def app_html() -> str:
        return (ASSETS / "app.html").read_text(encoding="utf-8")

    return server
