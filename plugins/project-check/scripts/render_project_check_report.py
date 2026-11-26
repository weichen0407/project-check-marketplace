"""Fill shared report templates with supplied facts; never run analysis tools."""

import argparse
from collections import Counter
from html import escape
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from xml.dom import Node, minidom
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SLOT = re.compile(r"\{\{([a-zA-Z0-9_.-]+)\}\}")
MARKER = re.compile(r"<!--\s*report-block:([a-zA-Z0-9_.-]+):(start|end)\s*-->")
HTML_SECTION = re.compile(r'<section\b[^>]*\bdata-section="([a-zA-Z0-9_.-]+)"[^>]*>')
HTML_IMAGE_SLOT = re.compile(
    r'<figure\b[^>]*\bdata-image-slot="([a-zA-Z0-9-]+)"[^>]*>.*?</figure>',
    re.DOTALL,
)
WORD = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD}
ET.register_namespace("w", WORD)


def section_definitions(layout):
    return layout["front"] + [item for group in layout["groups"] for item in group["sections"]] + layout["back"]


def block_ids(layout):
    return [item["id"] for item in section_definitions(layout)] + [group["id"] for group in layout["groups"]]


def selected_blocks(values, layout):
    sections = {key for key, value in values.items() if value.strip()}
    groups = {
        group["id"]
        for group in layout["groups"]
        if any(item["id"] in sections for item in group["sections"])
    }
    return sections | groups


def docx_slots(blob, *, document_only=False):
    with zipfile.ZipFile(BytesIO(blob)) as bundle:
        text = "".join(
            "".join(p.itertext())
            for name in bundle.namelist()
            if (name == "word/document.xml" if document_only else name.startswith("word/") and name.endswith(".xml"))
            for p in ET.fromstring(bundle.read(name)).iter(f"{{{WORD}}}p")
        )
    return set(SLOT.findall(text))


def load_html_template_catalog(base):
    path = Path(base) / "html-template-catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or set(catalog) != {"default", "templates"}:
        raise ValueError("HTML template catalog must contain default and templates")
    templates = catalog["templates"]
    if not isinstance(templates, list) or not templates:
        raise ValueError("HTML template catalog must contain at least one template")
    required = {"id", "file", "name", "description", "recommended_for"}
    if any(not isinstance(item, dict) or set(item) != required for item in templates):
        raise ValueError("Each HTML template entry must use the documented catalog fields")
    ids = [item["id"] for item in templates]
    if len(ids) != len(set(ids)) or any(not isinstance(item_id, str) or not re.fullmatch(r"[a-z0-9-]+", item_id) for item_id in ids):
        raise ValueError("HTML template IDs must be unique lowercase identifiers")
    if catalog["default"] not in ids:
        raise ValueError("Default HTML template must reference a registered template")
    for item in templates:
        if not isinstance(item["file"], str) or not item["file"].endswith(".html"):
            raise ValueError("HTML template files must be relative .html paths")
        relative = Path(item["file"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("HTML template files must stay inside the language template directory")
        if (
            not isinstance(item["name"], dict)
            or not isinstance(item["description"], dict)
            or set(item["name"]) != {"cn", "en"}
            or set(item["description"]) != {"cn", "en"}
        ):
            raise ValueError("HTML template names and descriptions must include cn and en")
        if not all(isinstance(item[field][language], str) and item[field][language].strip() for field in ("name", "description") for language in ("cn", "en")):
            raise ValueError("HTML template names and descriptions must be non-empty text")
        if not isinstance(item["recommended_for"], list) or not all(isinstance(value, str) and value for value in item["recommended_for"]):
            raise ValueError("HTML template recommendations must be a list of identifiers")
    return catalog


def validate_templates(root=ROOT, template_dir=None, *, language="cn"):
    if language not in {"cn", "en"}:
        raise ValueError("Report language must be cn or en")
    base = Path(template_dir) if template_dir else Path(root) / "templates"
    folder = base if language == "cn" else base / "en"
    layout = json.loads((folder / "report-layout.json").read_text(encoding="utf-8"))
    definitions = section_definitions(layout)
    keys = [item["id"] for item in definitions]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate report section IDs")
    catalog = json.loads((Path(root) / "assets/tool-display-names.json").read_text(encoding="utf-8"))
    expected_tools = {f"{server}.{tool}" for server, info in catalog.items() for tool in info["tools"]}
    actual_tools = {item["id"] for group in layout["groups"] for item in group["sections"]}
    if expected_tools != actual_tools:
        raise ValueError("Report layout must cover every configured tool; rebuild the report templates")
    expected = set(keys)
    for suffix in ("md", "docx"):
        path = folder / f"project-check-report.{suffix}"
        present = docx_slots(path.read_bytes()) if suffix == "docx" else set(SLOT.findall(path.read_text(encoding="utf-8")))
        if present != expected:
            raise ValueError(f"Template fields differ from report-layout.json: {path.name}")
    markdown = (folder / "project-check-report.md").read_text(encoding="utf-8")
    markers = Counter(MARKER.findall(markdown))
    expected_blocks = set(block_ids(layout))
    if {key for key, state in markers if state == "start"} != expected_blocks or any(
        markers[(key, state)] != 1 for key in expected_blocks for state in ("start", "end")
    ):
        raise ValueError("Markdown template must contain one start/end block for every report section and group")
    html_catalog = load_html_template_catalog(base)
    for item in html_catalog["templates"]:
        path = folder / item["file"]
        html = path.read_text(encoding="utf-8")
        if set(SLOT.findall(html)) != expected:
            raise ValueError(f"HTML template fields differ from report-layout.json: {path.name}")
        if Counter(HTML_SECTION.findall(html)) != Counter(expected_blocks):
            raise ValueError(f"HTML template must contain every report section and group once: {path.name}")
        image_slots = HTML_IMAGE_SLOT.findall(html)
        if len(image_slots) != len(set(image_slots)):
            raise ValueError(f"HTML image slot IDs must be unique: {path.name}")
    docx = (folder / "project-check-report.docx").read_bytes()
    if docx_slots(docx, document_only=True) != expected:
        raise ValueError("Word template report fields must be in the main document body")
    return folder, layout, html_catalog


def supplied_values(payload, layout):
    if not isinstance(payload, dict) or set(payload) - {"sections", "language", "html_template", "images"}:
        raise ValueError("Input must contain sections and optional language, html_template or images")
    sections = payload.get("sections", {})
    if not isinstance(sections, dict):
        raise ValueError("sections must be an object")
    keys = {item["id"] for item in section_definitions(layout)}
    unknown = set(sections) - keys
    if unknown:
        raise ValueError("Unknown report section IDs: " + ", ".join(sorted(unknown)))
    if any(value is not None and not isinstance(value, str) for value in sections.values()):
        raise ValueError("Section values must be text or null")
    if any(re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value or "") for value in sections.values()):
        raise ValueError("Report text contains unsupported XML control characters")
    return {key: sections.get(key) or "" for key in keys}


def supplied_images(payload):
    images = payload.get("images", {})
    if not isinstance(images, dict):
        raise ValueError("images must be an object")
    result = {}
    for slot_id, image in images.items():
        if not isinstance(slot_id, str) or not re.fullmatch(r"[a-z0-9-]+", slot_id):
            raise ValueError("Image slot IDs must be lowercase identifiers")
        if not isinstance(image, dict) or set(image) - {"src", "alt", "caption"} or "src" not in image:
            raise ValueError(f"Image {slot_id} must contain src and optional alt or caption")
        if any(key in image and not isinstance(image[key], str) for key in ("src", "alt", "caption")):
            raise ValueError(f"Image {slot_id} values must be text")
        src = image["src"].strip()
        if not src or re.search(r"[\x00-\x20]", src):
            raise ValueError(f"Image {slot_id} src must be a non-empty URL or relative path without whitespace")
        scheme = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):", src)
        if scheme and scheme.group(1).lower() not in {"http", "https"}:
            raise ValueError(f"Image {slot_id} src uses an unsupported URL scheme")
        if not scheme:
            relative = Path(src)
            if src.startswith(("/", "\\", "//")) or relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Image {slot_id} src must stay relative to the exported HTML")
        result[slot_id] = {
            "src": src,
            "alt": image.get("alt", ""),
            "caption": image.get("caption", ""),
        }
    return result


def supplied_language(payload, override=None):
    if not isinstance(payload, dict):
        raise ValueError("Input must be an object containing sections and optional language")
    language = override or payload.get("language", "cn")
    if language not in {"cn", "en"}:
        raise ValueError("Report language must be cn or en")
    return language


def supplied_html_template(payload, catalog, override=None):
    template_id = override or payload.get("html_template") or catalog["default"]
    if not isinstance(template_id, str):
        raise ValueError("html_template must be a registered template ID")
    templates = {item["id"]: item for item in catalog["templates"]}
    if template_id == "patent-review" and template_id not in templates and "evidence-dossier" in templates:
        template_id = "evidence-dossier"
    if template_id not in templates:
        raise ValueError("Unknown HTML template ID: " + template_id)
    return template_id, templates[template_id]


def fill_text(template, values, *, html=False):
    # Single-pass substitution: content containing braces is never interpreted.
    encode = (lambda value: escape(value, quote=True)) if html else (lambda value: escape(value, quote=False))
    return SLOT.sub(lambda match: encode(values[match.group(1)]), template)


def fill_markdown(template, values, layout):
    selected = selected_blocks(values, layout)
    for block_id in block_ids(layout):
        escaped = re.escape(block_id)
        if block_id in selected:
            template = re.sub(
                rf"(?m)^\s*<!--\s*report-block:{escaped}:(?:start|end)\s*-->\s*\n?",
                "",
                template,
            )
        else:
            template, count = re.subn(
                rf"(?ms)^\s*<!--\s*report-block:{escaped}:start\s*-->\s*\n.*?^\s*<!--\s*report-block:{escaped}:end\s*-->\s*\n?",
                "",
                template,
            )
            if count != 1:
                raise ValueError(f"Markdown template block is missing or duplicated: {block_id}")
    # Normalize only template whitespace before inserting user content.
    template = re.sub(r"\n{3,}", "\n\n", template).rstrip() + "\n"
    return fill_text(template, values)


def fill_html_images(template, images):
    slots = HTML_IMAGE_SLOT.findall(template)
    unknown = set(images) - set(slots)
    if unknown:
        raise ValueError("Selected HTML template has no image slots: " + ", ".join(sorted(unknown)))

    def replace(match):
        slot_id = match.group(1)
        if slot_id not in images:
            return ""
        image = images[slot_id]
        caption = (
            f'<figcaption>{escape(image["caption"], quote=True)}</figcaption>'
            if image["caption"]
            else ""
        )
        return (
            f'<figure class="media-slot media-slot-{slot_id}" data-image-slot="{slot_id}">'
            f'<img src="{escape(image["src"], quote=True)}" '
            f'alt="{escape(image["alt"], quote=True)}" loading="lazy">'
            f"{caption}</figure>"
        )

    return HTML_IMAGE_SLOT.sub(replace, template)


def fill_html(template, values, layout, images=None):
    selected = selected_blocks(values, layout)
    for block_id in block_ids(layout):
        if block_id in selected:
            continue
        template, count = re.subn(
            rf'<section\b[^>]*\bdata-section="{re.escape(block_id)}"[^>]*>.*?</section>\s*',
            "",
            template,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError(f"HTML template section is missing or duplicated: {block_id}")
    template = fill_html_images(template, images or {})
    return fill_text(template, values, html=True)


def paragraph_text(paragraph):
    return "".join(
        child.data
        for node in paragraph.getElementsByTagNameNS(WORD, "t")
        for child in node.childNodes
        if child.nodeType == Node.TEXT_NODE
    )


def heading_level(paragraph):
    styles = paragraph.getElementsByTagNameNS(WORD, "pStyle")
    if not styles:
        return None
    value = styles[0].getAttributeNS(WORD, "val") or styles[0].getAttribute("w:val")
    match = re.fullmatch(r"Heading([12])", value, re.IGNORECASE)
    return int(match.group(1)) if match else None


def write_docx_paragraph(tree, paragraph, text):
    runs = [
        node for node in paragraph.childNodes
        if node.nodeType == Node.ELEMENT_NODE and node.namespaceURI == WORD and node.localName == "r"
    ]
    properties = runs[0].getElementsByTagNameNS(WORD, "rPr") if runs else []
    properties = properties[0].cloneNode(deep=True) if properties else None
    for child in list(paragraph.childNodes):
        if child.nodeType != Node.ELEMENT_NODE or child.localName != "pPr":
            paragraph.removeChild(child)
    prefix = paragraph.prefix or "w"
    element = lambda tag: tree.createElementNS(WORD, f"{prefix}:{tag}")
    run = element("r")
    paragraph.appendChild(run)
    if properties is not None:
        for hidden in list(properties.getElementsByTagNameNS(WORD, "vanish")):
            hidden.parentNode.removeChild(hidden)
        run.appendChild(properties)
    for index, line in enumerate(text.split("\n")):
        if index:
            run.appendChild(element("br"))
        node = element("t")
        node.setAttribute("xml:space", "preserve")
        node.appendChild(tree.createTextNode(line))
        run.appendChild(node)


def fill_docx(blob, values, layout):
    selected = selected_blocks(values, layout)
    output = BytesIO()
    with zipfile.ZipFile(BytesIO(blob)) as source, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            content = source.read(info.filename)
            if info.filename == "word/document.xml":
                # DOM preserves the template's namespace declarations, including
                # prefixes referenced only by mc:Ignorable attributes in OOXML.
                tree = minidom.parseString(content)
                paragraphs = list(tree.getElementsByTagNameNS(WORD, "p"))
                records = {}
                for index, paragraph in enumerate(paragraphs):
                    match = SLOT.fullmatch(paragraph_text(paragraph))
                    if not match:
                        continue
                    heading = next(
                        (candidate for candidate in reversed(paragraphs[:index]) if heading_level(candidate) is not None),
                        None,
                    )
                    if heading is None:
                        raise ValueError(f"Word template field has no preceding heading: {match.group(1)}")
                    records[match.group(1)] = (paragraph, heading, paragraphs.index(heading))
                for group in layout["groups"]:
                    first = records[group["sections"][0]["id"]]
                    group_heading = next(
                        (candidate for candidate in reversed(paragraphs[:first[2]]) if heading_level(candidate) == 1),
                        None,
                    )
                    if group["id"] not in selected and group_heading is not None and group_heading.parentNode is not None:
                        group_heading.parentNode.removeChild(group_heading)
                for key, (paragraph, heading, _) in records.items():
                    if key not in selected:
                        if heading.parentNode is not None:
                            heading.parentNode.removeChild(heading)
                        if paragraph.parentNode is not None:
                            paragraph.parentNode.removeChild(paragraph)
                    else:
                        write_docx_paragraph(tree, paragraph, values[key])
                content = tree.toxml(encoding="utf-8")
            target.writestr(info, content)
    return output.getvalue()


def export_report(
    payload,
    output_dir,
    *,
    formats=("md", "html", "docx"),
    name="project-check-report",
    template_dir=None,
    language=None,
    html_template=None,
    root=ROOT,
):
    language = supplied_language(payload, language)
    folder, layout, html_catalog = validate_templates(root, template_dir, language=language)
    html_template, html_template_entry = supplied_html_template(payload, html_catalog, html_template)
    values = supplied_values(payload, layout)
    images = supplied_images(payload)
    formats = tuple(dict.fromkeys(formats))
    if not formats or set(formats) - {"md", "html", "docx"}:
        raise ValueError("Formats must be md, html or docx")
    if not re.fullmatch(r"[\w-]+", name):
        raise ValueError("Report name must be a filename without paths or extensions")
    selected_html = (folder / html_template_entry["file"]).read_text(encoding="utf-8")
    unknown_image_slots = set(images) - set(HTML_IMAGE_SLOT.findall(selected_html))
    if unknown_image_slots:
        raise ValueError(
            "Selected HTML template has no image slots: " + ", ".join(sorted(unknown_image_slots))
        )
    rendered = {}
    for suffix in formats:
        source = folder / (html_template_entry["file"] if suffix == "html" else f"project-check-report.{suffix}")
        rendered[suffix] = (
            fill_docx(source.read_bytes(), values, layout) if suffix == "docx"
            else (
                fill_html(source.read_text(encoding="utf-8"), values, layout, images)
                if suffix == "html"
                else fill_markdown(source.read_text(encoding="utf-8"), values, layout)
            ).encode("utf-8")
        )
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stem, number = name, 1
    while any((output_dir / f"{stem}.{suffix}").exists() for suffix in formats):
        number += 1
        stem = f"{name}-{number}"
    paths = []
    try:
        for suffix, content in rendered.items():
            path = output_dir / f"{stem}.{suffix}"
            with path.open("xb") as handle:
                paths.append(path)
                handle.write(content)
    except OSError:
        for path in paths:
            path.unlink(missing_ok=True)
        raise
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--formats", default="md,html,docx")
    parser.add_argument("--name", default="project-check-report")
    parser.add_argument("--template-dir", type=Path)
    parser.add_argument("--language", choices=("cn", "en"), help="Override the input language")
    parser.add_argument("--html-template", help="Override the registered HTML template ID")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        paths = export_report(
            payload,
            args.output_dir,
            formats=args.formats.split(","),
            name=args.name,
            template_dir=args.template_dir,
            language=args.language,
            html_template=args.html_template,
        )
    except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile) as error:
        print(f"Unable to export report: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps({"files": [str(path) for path in paths]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
