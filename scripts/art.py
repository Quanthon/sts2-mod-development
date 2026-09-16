"""Content-addressed PNG sync and optional placeholder/linked-icon generation."""
from __future__ import annotations
import io
import os
import platform
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from common import encode, file_hash, inside, read_json, stamp, transaction
from design import KEY, read_design, linked_card

KINDS = ("cards", "powers", "relics")

def png_bytes(path):
    path = Path(path)
    with Image.open(path) as image:
        if image.format != "PNG":
            raise ValueError(f"Expected PNG: {path}")
        image.verify()
    return path.read_bytes()

def source_for(project, kind, key, row):
    value = project.data.get("asset_roots", {}).get(kind)
    if not value:
        raise ValueError(f"Missing asset_roots.{kind}")
    root = project.path(value)
    names = [key, row.get("名称")]
    old = project.baseline(kind)["entries"].get(key, {})
    if old.get("名称") not in names:
        names.append(old.get("名称"))
    registry = read_json(project.state / "placeholders.json", {}) if kind == "cards" else {}
    files = list(root.rglob("*")) if root.exists() else []
    fallback, seen_names = None, set()
    for name in filter(None, names):
        normalized = str(name).casefold()
        if normalized in seen_names:
            continue
        seen_names.add(normalized)
        matches = [p for p in files if p.is_file() and p.suffix.lower() == ".png" and p.stem.casefold() == normalized]
        regular, placeholders = [], []
        for path in matches:
            source = inside(root, path)
            png_bytes(source)
            relative = source.relative_to(project.root).as_posix()
            registered_hash = registry.get(relative, registry.get(relative.replace("/", "\\")))
            if registered_hash == file_hash(source):
                placeholders.append(source)
            else:
                regular.append(source)
        if len(regular) > 1:
            raise ValueError(f"Ambiguous PNG for {kind}/{key}: {[str(p) for p in regular]}")
        if regular:
            return regular[0]
        if len(placeholders) > 1:
            raise ValueError(f"Ambiguous placeholders for {kind}/{key}: {[str(p) for p in placeholders]}")
        if placeholders and fallback is None:
            fallback = placeholders[0]
    if fallback is not None:
        return fallback
    raise ValueError(f"Missing PNG for {kind}/{key} in {root}")


def sync(project, apply=False, kind=None):
    data, issues = read_design(project)
    manifest = read_json(project.manifest)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("Expected asset manifest schema_version=1")
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Asset manifest entries must be a list")
    report, plans = [], []
    destinations = {}
    for item in entries:
        if kind and item.get("kind") != kind:
            continue
        k, key = item.get("kind"), item.get("key")
        try:
            if k not in KINDS or key not in data[k]:
                raise ValueError(f"Unknown content: {k}/{key}")
            if any(i["kind"] == k and (i.get("key") in (None, key)) for i in issues):
                raise ValueError(f"Invalid design row: {k}/{key}")
            row = data[k][key]
            if row.get("稀有度") == "弃用":
                report.append({"kind": k, "key": key, "status": "skipped_deprecated"})
                continue
            implementation = project.path(item["implementation"])
            if not implementation.is_file():
                raise ValueError(f"Create implementation first: {implementation}")
            target = project.path(item["target"])
            if target.suffix.lower() != ".png":
                raise ValueError("Asset target must be a .png file")
            if target in destinations:
                raise ValueError(f"Duplicate destination: {target}")
            destinations[target] = (k, key)
            for raw_root in project.data.get("asset_roots", {}).values():
                if raw_root and target.is_relative_to(project.path(raw_root)):
                    raise ValueError("Target may not overwrite raw art sources")
            source = source_for(project, k, key, row)
            payload = png_bytes(source)
            plans.append((k, key, source, target, payload))
        except (ValueError, KeyError, OSError) as error:
            report.append({"kind": k, "key": key, "status": "issue", "error": str(error)})
    # Every destination collision is blocked, including the first entry.
    duplicate_targets = set()
    counts = {}
    for item in entries:
        if not kind or item.get("kind") == kind:
            if item.get("target"):
                target = project.path(item["target"])
                counts[target] = counts.get(target, 0) + 1
    duplicate_targets = {p for p, count in counts.items() if count > 1}
    owners = {}
    for k, key, source, target, payload in plans:
        owners.setdefault(source, set()).add((k, key))
    changes = {}
    for k, key, source, target, payload in plans:
        if target in duplicate_targets or len(owners[source]) > 1:
            report.append({"kind": k, "key": key, "status": "issue", "error": "Source or destination is claimed by multiple entries"})
            continue
        equal = target.exists() and target.read_bytes() == payload
        status = "unchanged" if equal else "updated" if apply else "would_update"
        report.append({"kind": k, "key": key, "status": status, "source": str(source), "target": str(target)})
        if not equal:
            changes[target] = payload
    if apply and changes:
        transaction(changes, project.state / "backups" / ("art-" + stamp()))
    return {"entries": report, "needs_export": bool(changes), "applied": apply,
            "issues": [r for r in report if r["status"] == "issue"]}

def font_candidates():
    system = platform.system()
    if system == "Windows":
        root = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        return [root / "msyh.ttc", root / "arial.ttf"]
    if system == "Darwin":
        return [Path("/System/Library/Fonts/PingFang.ttc"),
                Path("/System/Library/Fonts/STHeiti Light.ttc"),
                Path("/System/Library/Fonts/Supplemental/Songti.ttc")]
    return [Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf"),
            Path.home() / ".local/share/fonts/NotoSansCJK-Regular.ttc"]

def font(size, explicit=None):
    if explicit:
        return ImageFont.truetype(str(Path(explicit).expanduser()), size)
    for path in font_candidates():
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def placeholder(project, key, name="", card_type="技能", refresh=False, font_path=None):
    if not KEY.fullmatch(key):
        raise ValueError("Expected PascalCase key")
    root = project.path(project.data["asset_roots"]["cards"])
    target = inside(root, key + ".png")
    registry_path = project.state / "placeholders.json"
    registry = read_json(registry_path, {})
    relative = target.relative_to(project.root).as_posix()
    legacy_relative = relative.replace("/", "\\")
    registered_hash = registry.get(relative, registry.get(legacy_relative))
    if target.exists() and (not refresh or registered_hash != file_hash(target)):
        raise ValueError("Existing artwork preserved; refresh only an unchanged generated placeholder")
    if font_path:
        requested_font = Path(font_path).expanduser()
        font_path = requested_font if requested_font.is_absolute() else project.root / requested_font
    colors = {"攻击": "#ECC7C7", "技能": "#D7E7D0", "能力": "#CCD8F1", "状态": "#D5D5D5", "诅咒": "#CDC3DB"}
    image = Image.new("RGB", (250, 190), colors.get(card_type, "#D5D5D5"))
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 241, 181), outline="#475569", width=2)
    draw.text((18, 18), "TEMP / " + card_type, fill="#334155", font=font(16, font_path))
    label = name or key
    # Fit long labels without altering the identity shown on a second line.
    label_font = font(21, font_path)
    lines, line = [], ""
    for char in label:
        if draw.textlength(line + char, font=label_font) > 210 and line:
            lines.append(line)
            line = ""
        line += char
    lines.append(line)
    for i, value in enumerate(lines[:3]):
        draw.text((18, 55 + i * 26), value, fill="#1F2937", font=label_font)
    key_font = font(12, font_path)
    if draw.textlength(key, font=key_font) <= 214:
        draw.text((18, 154), key, fill="#334155", font=key_font)
    out = io.BytesIO()
    image.save(out, format="PNG")
    import hashlib
    registry.pop(legacy_relative, None)
    registry[relative] = hashlib.sha256(out.getvalue()).hexdigest()
    transaction({target: out.getvalue(), registry_path: encode(registry)},
                project.state / "backups" / ("placeholder-" + stamp()) if target.exists() else None)
    return {"created": str(target), "size": [250, 190]}

def icons(project, apply=False, keys=None, overwrite=False):
    data, issues = read_design(project)
    reports = [{"status": "issue", **i} for i in issues
               if i["kind"] == "powers" and (not keys or i.get("key") is None or i.get("key") in keys)]
    changes = {}
    root = project.path(project.data["asset_roots"]["powers"])
    for key, row in data["powers"].items():
        if keys and key not in keys:
            continue
        try:
            if any(i["kind"] == "powers" and i.get("key") in (None, key) for i in issues):
                raise ValueError("Invalid state design")
            target = inside(root, key + ".png")
            card_key = linked_card(row.get("关联卡牌"), data["cards"])
            if card_key is None:
                reports.append({"key": key, "status": "skipped_unlinked"})
                continue
            if any(i["kind"] == "cards" and i.get("key") in (None, card_key) for i in issues):
                raise ValueError("Invalid linked card design")
            if data["cards"][card_key].get("稀有度") == "弃用":
                reports.append({"key": key, "status": "skipped_deprecated"})
                continue
            if target.exists() and not overwrite:
                reports.append({"key": key, "status": "preserved_existing"})
                continue
            source = source_for(project, "cards", card_key, data["cards"][card_key])
            if target.is_relative_to(project.path(project.data["asset_roots"]["cards"])):
                raise ValueError("State icon output must be separate from raw card art")
            with Image.open(source) as image:
                output = ImageOps.fit(image.convert("RGBA"), (256, 256), method=Image.Resampling.LANCZOS)
                out = io.BytesIO()
                output.save(out, format="PNG")
                changes[target] = out.getvalue()
            reports.append({"key": key, "status": "generated" if apply else "would_generate", "source": str(source), "target": str(target)})
        except (ValueError, KeyError, OSError) as error:
            reports.append({"key": key, "status": "issue", "error": str(error)})
    for key in keys or []:
        if key not in data["powers"]:
            reports.append({"key": key, "status": "issue", "error": "Unknown state key"})
    if apply and changes:
        transaction(changes, project.state / "backups" / ("icons-" + stamp()))
    return {"entries": reports, "applied": apply, "issues": [r for r in reports if r["status"] == "issue"]}

