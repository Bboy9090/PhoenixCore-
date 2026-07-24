#!/usr/bin/env python3
"""Deterministic renderer and quality audit for Branding V2 SVG masters."""

from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import cairosvg
from PIL import Image, ImageDraw

FORBIDDEN_ELEMENTS = {"image", "foreignObject", "script"}
FORBIDDEN_TEXT_TOKENS = {
    "checkerboard",
    "proof label",
    "filename",
    "screenshot",
    "thunder_core",
}


@dataclass
class AuditResult:
    path: str
    category: str
    valid_xml: bool = False
    expected_viewbox: str = ""
    actual_viewbox: str = ""
    embedded_raster: bool = False
    contains_text_element: bool = False
    forbidden_token: str = ""
    render_pass: bool = False
    small_size_entropy: float | None = None
    small_size_legible: bool | None = None
    errors: list[str] | None = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []

    @property
    def passed(self) -> bool:
        return (
            self.valid_xml
            and self.expected_viewbox == self.actual_viewbox
            and not self.embedded_raster
            and not self.contains_text_element
            and not self.forbidden_token
            and self.render_pass
            and self.small_size_legible is not False
            and not self.errors
        )


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalized_viewbox(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.replace(",", " ").split())


def all_text_and_attributes(root: ET.Element) -> str:
    parts: list[str] = []
    for elem in root.iter():
        if elem.text:
            parts.append(elem.text)
        if elem.tail:
            parts.append(elem.tail)
        parts.extend(str(v) for v in elem.attrib.values())
    return " ".join(parts).lower()


def detect_embedded_raster(root: ET.Element) -> bool:
    for elem in root.iter():
        name = local_name(elem.tag)
        if name in FORBIDDEN_ELEMENTS:
            return True
        for value in elem.attrib.values():
            lowered = str(value).lower()
            if "data:image/" in lowered or lowered.endswith(
                (".png", ".jpg", ".jpeg", ".webp")
            ):
                return True
    return False


def image_entropy(image: Image.Image) -> float:
    gray = image.convert("L")
    histogram = gray.histogram()
    total = sum(histogram)
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in histogram:
        if count:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def render_svg(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=width,
        output_height=height,
    )
    with Image.open(png_path) as rendered:
        if rendered.size != (width, height):
            raise RuntimeError(f"rendered {rendered.size}, expected {(width, height)}")


def audit_svg(
    repo_root: Path,
    svg_path: Path,
    category: str,
    expected_viewbox: str,
    sizes: Iterable[tuple[int, int]],
    output_dir: Path,
) -> AuditResult:
    rel = svg_path.relative_to(repo_root).as_posix()
    result = AuditResult(path=rel, category=category, expected_viewbox=expected_viewbox)

    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        result.valid_xml = True
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"XML parse failed: {exc}")
        return result

    result.actual_viewbox = normalized_viewbox(root.attrib.get("viewBox"))
    if result.actual_viewbox != expected_viewbox:
        result.errors.append(
            f"viewBox mismatch: {result.actual_viewbox!r} != {expected_viewbox!r}"
        )

    result.embedded_raster = detect_embedded_raster(root)
    if result.embedded_raster:
        result.errors.append(
            "embedded raster, script, foreignObject, or external image detected"
        )

    result.contains_text_element = any(
        local_name(elem.tag) == "text" for elem in root.iter()
    )
    if result.contains_text_element:
        result.errors.append(
            "SVG <text> element detected; final masters must not bake labels"
        )

    searchable = all_text_and_attributes(root)
    for token in sorted(FORBIDDEN_TEXT_TOKENS):
        if token in searchable:
            result.forbidden_token = token
            result.errors.append(f"forbidden token detected: {token}")
            break

    try:
        rendered_paths: list[Path] = []
        for width, height in sizes:
            png_path = output_dir / category / f"{svg_path.stem}-{width}x{height}.png"
            render_svg(svg_path, png_path, width, height)
            rendered_paths.append(png_path)
        result.render_pass = True

        if category == "icons":
            smallest = min(rendered_paths, key=lambda p: Image.open(p).size[0])
            with Image.open(smallest) as icon:
                entropy = image_entropy(icon)
                result.small_size_entropy = round(entropy, 4)
                result.small_size_legible = entropy >= 0.75
                if not result.small_size_legible:
                    result.errors.append(
                        f"small-size silhouette likely collapsed; entropy={entropy:.4f}"
                    )
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"render failed: {exc}")

    return result


def make_contact_sheet(
    images: list[Path],
    destination: Path,
    thumb_size: tuple[int, int],
    columns: int,
    label_height: int = 34,
) -> None:
    if not images:
        return
    rows = math.ceil(len(images) / columns)
    cell_w = thumb_size[0] + 24
    cell_h = thumb_size[1] + label_height + 20
    sheet = Image.new("RGB", (cell_w * columns, cell_h * rows), "#071426")
    draw = ImageDraw.Draw(sheet)

    for index, image_path in enumerate(images):
        row, col = divmod(index, columns)
        x = col * cell_w + 12
        y = row * cell_h + 10
        with Image.open(image_path).convert("RGBA") as source:
            source.thumbnail(thumb_size, Image.Resampling.LANCZOS)
            tile = Image.new("RGBA", thumb_size, (0, 0, 0, 0))
            tile.alpha_composite(
                source,
                (
                    (thumb_size[0] - source.width) // 2,
                    (thumb_size[1] - source.height) // 2,
                ),
            )
            sheet.paste(tile.convert("RGB"), (x, y))
        label = image_path.stem[:42]
        draw.text((x, y + thumb_size[1] + 6), label, fill="#E9EDF2")

    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="branding/v2", help="Brand V2 directory")
    parser.add_argument(
        "--output", default="brand-qa-output", help="QA artifact directory"
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    brand_root = repo_root / args.root
    output_dir = repo_root / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    spec_path = brand_root / "EXPORT_SPEC.json"
    if not spec_path.exists():
        print(f"ERROR: missing {spec_path}", file=sys.stderr)
        return 2

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    icon_viewbox = normalized_viewbox(spec["icon_master"]["view_box"])
    wallpaper_viewbox = normalized_viewbox(spec["hero_wallpaper"]["view_box"])
    icon_sizes = [
        (int(size), int(size)) for size in spec["icon_master"]["required_png_exports"]
    ]
    wallpaper_sizes = [
        (int(item["width"]), int(item["height"]))
        for item in spec["hero_wallpaper"]["required_png_exports"]
    ]

    icon_paths = sorted((brand_root / "icons").glob("*.svg"))
    wallpaper_paths = sorted((brand_root / "wallpapers").glob("*.svg"))
    if not icon_paths:
        print("ERROR: no icon SVG masters found", file=sys.stderr)
        return 2
    if not wallpaper_paths:
        print("ERROR: no wallpaper SVG masters found", file=sys.stderr)
        return 2

    results: list[AuditResult] = []
    for path in icon_paths:
        results.append(
            audit_svg(repo_root, path, "icons", icon_viewbox, icon_sizes, output_dir)
        )
    for path in wallpaper_paths:
        results.append(
            audit_svg(
                repo_root,
                path,
                "wallpapers",
                wallpaper_viewbox,
                wallpaper_sizes,
                output_dir,
            )
        )

    small_icons = sorted((output_dir / "icons").glob("*-24x24.png"))
    review_icons = sorted((output_dir / "icons").glob("*-256x256.png"))
    review_wallpapers = sorted((output_dir / "wallpapers").glob("*-1920x1080.png"))
    make_contact_sheet(
        small_icons, output_dir / "icon-contact-sheet-24px.png", (96, 96), 6
    )
    make_contact_sheet(
        review_icons, output_dir / "icon-contact-sheet-256px.png", (256, 256), 4
    )
    make_contact_sheet(
        review_wallpapers,
        output_dir / "wallpaper-contact-sheet-1920x1080.png",
        (480, 270),
        2,
    )

    summary = {
        "schema_version": "1.0.0",
        "icons_audited": len(icon_paths),
        "wallpapers_audited": len(wallpaper_paths),
        "passed": sum(1 for item in results if item.passed),
        "failed": sum(1 for item in results if not item.passed),
        "results": [{**asdict(item), "passed": item.passed} for item in results],
    }
    (output_dir / "audit-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Brand V2 QA Report",
        "",
        f"- Icons audited: {summary['icons_audited']}",
        f"- Wallpapers audited: {summary['wallpapers_audited']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        "",
        "| Asset | Category | Status | Small entropy | Findings |",
        "|---|---|---:|---:|---|",
    ]
    for item in results:
        findings = "; ".join(item.errors or []) or "clean"
        entropy = (
            "" if item.small_size_entropy is None else str(item.small_size_entropy)
        )
        lines.append(
            f"| `{item.path}` | {item.category} | {'PASS' if item.passed else 'FAIL'} | {entropy} | {findings} |"
        )
    (output_dir / "audit-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
