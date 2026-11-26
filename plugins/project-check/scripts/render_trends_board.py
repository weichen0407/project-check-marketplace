"""Render verified trend entries and retain previous sources during interrupted refreshes."""

import argparse
from datetime import date
from html import escape
import json
import os
from pathlib import Path
import re
from string import Template
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit

if os.name == "nt":
    from msvcrt import LK_LOCK, locking
else:
    from fcntl import LOCK_EX, flock


TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "trends-board.html"
CHANNELS = {"technology": "技术", "patents": "专利", "news": "资讯"}
STATUSES = {"updated": "已核对", "unchanged": "无确认变化", "failed": "来源核查未完成"}
ENGLISH_CHANNELS = {"technology": "Technology", "patents": "Patents", "news": "News"}
ENGLISH_STATUSES = {"updated": "Checked", "unchanged": "No confirmed changes", "failed": "Source check incomplete"}
SNAPSHOT = re.compile(
    r'<script type="application/json" id="project-check-trends-data">(.*?)</script>',
    re.DOTALL,
)
MAX_FRAGMENT_BYTES = 1024 * 1024


def required_text(value, label, *, language="cn"):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text" if language == "en" else f"{label} 缺少有效文本")
    return value.strip()


def iso_date(value, label, *, language="cn"):
    value = required_text(value, label, language=language)
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError(f"{label} must use YYYY-MM-DD" if language == "en" else f"{label} 须使用 YYYY-MM-DD")
    return date.fromisoformat(value).isoformat()


def source_identity(url, *, language="cn"):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
        or re.search(r"[\s\x00-\x1f\x7f\\]", url)
    ):
        raise ValueError("The source link must be a direct HTTPS URL" if language == "en" else "来源链接须为可直接打开的 HTTPS URL")
    port = parsed.port
    host = parsed.hostname if port in (443, None) else parsed.netloc.lower()
    return host, parsed.path or "/", parsed.query


def read_entries(raw_entries, as_of, *, language="cn"):
    if not isinstance(raw_entries, list):
        raise ValueError("entries must be an array" if language == "en" else "entries 须为数组")
    entries = []
    seen_urls = set()
    seen_keys = set()
    for raw in raw_entries:
        entry = {key: required_text(raw[key], key, language=language) for key in ("title", "summary", "source", "url")}
        identity = source_identity(entry["url"], language=language)
        key = required_text(raw["key"], "key", language=language) if "key" in raw else None
        if raw.get("date"):
            entry["date"] = iso_date(raw["date"], "Entry date" if language == "en" else "条目日期", language=language)
            if entry["date"] > as_of:
                raise ValueError("Entry date is later than the check date" if language == "en" else "条目日期晚于核对日期")
        if identity in seen_urls or key in seen_keys:
            continue
        seen_urls.add(identity)
        if key:
            seen_keys.add(key)
            entry["key"] = key
        entries.append(entry)
    return entries


def merge_snapshot(payload, previous):
    language = payload.get("language", (previous or {}).get("language", "cn"))
    if language not in ("en", "cn"):
        raise ValueError("language must be en or cn")
    english = language == "en"
    product = required_text(payload["product"], "product", language=language)
    market = required_text(payload["market"], "market", language=language)
    as_of = iso_date(payload["as_of"], "as_of", language=language)
    if previous:
        if (product, market) != (previous["product"], previous["market"]):
            raise ValueError("The board belongs to another product or market. Choose a new output path." if english else "既有看板属于其他产品或市场，请选择新的输出路径")
        if as_of < previous["as_of"]:
            raise ValueError("The check date is earlier than the existing board's date." if english else "核对日早于现有版本")

    sources = payload["channels"]
    if set(sources) != set(CHANNELS):
        raise ValueError("channels must contain technology, patents and news" if english else "channels 须包含 technology、patents 和 news")
    channels = {}
    for name in CHANNELS:
        incoming = sources[name]
        old = previous["channels"][name] if previous else {}
        status = incoming["status"]
        if status not in STATUSES:
            raise ValueError(f"Unsupported status for {name}" if english else f"{name} 的 status 不受支持")
        note = required_text(incoming["note"], "note", language=language) if "note" in incoming else ""
        if status == "failed" and not note:
            raise ValueError(f"A failure reason is required for {name}" if english else f"{name} 核查失败时需记录原因")
        if status == "updated":
            entries = read_entries(incoming["entries"], as_of, language=language)
        else:
            if incoming.get("entries"):
                raise ValueError(f"{name} accepts new entries only when updated" if english else f"{name} 只在 updated 时接受新条目")
            entries = old.get("entries", [])
        channels[name] = {
            "status": status,
            "note": note,
            "last_checked": old.get("last_checked") if status == "failed" else as_of,
            "entries": entries,
        }
    return {"product": product, "market": market, "as_of": as_of, "language": language, "channels": channels}


def read_snapshot(path, *, language="cn"):
    source = path.read_text(encoding="utf-8")
    match = SNAPSHOT.search(source)
    if match is None:
        raise ValueError("The file is not a Project Check trends board" if language == "en" else "该文件不是项目检查趋势看板")
    return json.loads(match.group(1))


def render_entry(entry):
    title, summary, source, href = (escape(entry[key]) for key in ("title", "summary", "source", "url"))
    when = entry.get("date")
    metadata = source + (f' · <time datetime="{when}">{when}</time>' if when else "")
    return (
        f'<li><a class="trends-link cursor-interaction" href="{href}" target="_blank" rel="noopener noreferrer">'
        f'<span class="text-small trends-meta">{metadata}</span>'
        f'<span class="trends-title">{title}<span aria-hidden="true">↗</span></span>'
        f'<span class="trends-detail">{summary}</span></a></li>'
    )


def render_board(snapshot):
    english = snapshot.get("language") == "en"
    headings = ENGLISH_CHANNELS if english else CHANNELS
    statuses = ENGLISH_STATUSES if english else STATUSES
    last_checked = "Last successful check" if english else "上次成功"
    empty = "No verified entries" if english else "暂无可核实条目"
    sections = []
    for name, heading in headings.items():
        channel = snapshot["channels"][name]
        status = statuses[channel["status"]]
        if channel["status"] == "failed" and channel["last_checked"]:
            status += f' · {last_checked} {channel["last_checked"]}'
        if channel["note"]:
            status += " · " + channel["note"]
        entries = (
            "<ul>" + "\n".join(map(render_entry, channel["entries"])) + "</ul>"
            if channel["entries"] else f'<p class="trends-status">{empty}</p>'
        )
        sections.append(
            f'<section class="trends-channel" data-category="{name}" aria-labelledby="trends-{name}">'
            f'<h2 id="trends-{name}">{heading}</h2>'
            f'<p class="text-small trends-status">{escape(status)}</p>{entries}</section>'
        )
    data = json.dumps(snapshot, ensure_ascii=False).replace("<", r"\u003c")
    html = Template(TEMPLATE.read_text(encoding="utf-8")).substitute(
        language="en" if english else "zh-CN",
        title=escape(snapshot["product"] + (" Trends Board" if english else " 趋势看板")),
        label=escape(snapshot["market"] + (" · Checked on" if english else " · 本次检查")),
        date=snapshot["as_of"],
        channels="\n".join(sections),
        snapshot=data,
    )
    if len(html.encode("utf-8")) > MAX_FRAGMENT_BYTES:
        raise ValueError("The board exceeds the Codex display limit. Retain fewer entries." if english else "看板超过 Codex 渲染上限，请减少保留条目")
    return html


def update_board(payload, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    # Keep the lock file so overlapping processes always lock the same file.
    lock_path = output.with_name(f".{output.name}.lock")
    with lock_path.open("a+b") as lock:
        if os.name == "nt":
            lock.seek(0)
            locking(lock.fileno(), LK_LOCK, 1)
        else:
            flock(lock.fileno(), LOCK_EX)
        previous = read_snapshot(output, language=payload.get("language", "cn")) if output.exists() else None
        result = merge_snapshot(payload, previous)
        html = render_board(result)
        temporary = None
        try:
            with NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, delete=False) as pending:
                temporary = Path(pending.name)
                pending.write(html)
            temporary.replace(output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    render = commands.add_parser("render", help="Create or update the board")
    render.add_argument("--input", type=Path, required=True)
    render.add_argument("--output", type=Path, required=True)
    snapshot = commands.add_parser("snapshot", help="Read the last structured board snapshot")
    snapshot.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            result = read_snapshot(args.file)
        else:
            output = args.output.expanduser().absolute()
            payload = json.loads(args.input.expanduser().read_text(encoding="utf-8"))
            data = update_board(payload, output)
            result = {"file": str(output), "as_of": data["as_of"], "channels": {
                name: {"status": channel["status"], "count": len(channel["entries"])}
                for name, channel in data["channels"].items()
            }}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.exit(1, f"Trends board: {error}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
