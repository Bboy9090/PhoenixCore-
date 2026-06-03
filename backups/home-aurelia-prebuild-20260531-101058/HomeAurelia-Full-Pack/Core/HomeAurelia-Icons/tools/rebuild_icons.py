#!/usr/bin/env python3
"""Rebuild Home Aurelia Core icon pack exports.

This is intentionally self-contained: it generates deterministic SVG sources that
match the Home Aurelia icon-board direction (gold medallion + electric-blue line
symbols), then renders PNGs for all required sizes.

It also syncs the generated assets into:
  - HomeAurelia-Full-Pack/Core/HomeAurelia-Icons
  - HomeAurelia-Theme-Pack/09-Icons
  - os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/home-aurelia

Rules:
  - No network access.
  - No external downloads.
  - Shared Core icon pack only (v1).
"""

from __future__ import annotations

import shutil
import subprocess
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

def _repo_root(start: Path) -> Path:
    p = start
    while p.parent != p:
        if (p / ".git").exists() or (p / "AGENTS.md").exists():
            return p
        p = p.parent
    return start


REPO_ROOT = _repo_root(Path(__file__).resolve())
CORE_DIR = REPO_ROOT / "HomeAurelia-Full-Pack" / "Core" / "HomeAurelia-Icons"
THEME_PACK_DIR = REPO_ROOT / "HomeAurelia-Theme-Pack" / "09-Icons"
LIVE_BUILD_ICON_DIR = (
    REPO_ROOT
    / "os"
    / "phoenix-os"
    / "live-build"
    / "config"
    / "includes.chroot"
    / "usr"
    / "share"
    / "icons"
    / "home-aurelia"
)

SIZES = [16, 22, 24, 32, 48, 64, 128, 256, 512]
CONTEXTS = [
    "apps",
    "places",
    "actions",
    "devices",
    "status",
    "mimetypes",
    "categories",
    "emblems",
]


@dataclass(frozen=True)
class IconDef:
    name: str
    symbol: str


# Core icon set (shared across editions for v1)
ICONS: list[IconDef] = [
    IconDef("folder", "folder"),
    IconDef("folder-home", "home"),
    IconDef("folder-documents", "document"),
    IconDef("folder-downloads", "download"),
    IconDef("folder-music", "music"),
    IconDef("folder-pictures", "photo"),
    IconDef("folder-videos", "video"),
    IconDef("user-trash", "trash"),
    IconDef("user-trash-full", "trash_full"),
    IconDef("preferences-system", "gear"),
    IconDef("system-settings", "gear"),
    IconDef("utilities-terminal", "terminal"),
    IconDef("internet-web-browser", "globe"),
    IconDef("internet-mail", "mail"),
    IconDef("office-calendar", "calendar"),
    IconDef("network-wireless", "wifi"),
    IconDef("network-workgroup", "network"),
    IconDef("bluetooth", "bluetooth"),
    IconDef("user", "user"),
    IconDef("system-shutdown", "power"),
    IconDef("system-reboot", "reboot"),
    IconDef("system-software-install", "download"),
    IconDef("dialog-question", "question"),
    IconDef("drive-harddisk", "drive"),
    IconDef("drive-removable-media", "usb"),
    IconDef("computer", "computer"),
    IconDef("network-firewall", "shield"),
    IconDef("accessories-calculator", "calculator"),
    IconDef("accessories-text-editor", "edit"),
    IconDef("text-x-generic", "document"),
    IconDef("audio-x-generic", "music"),
    IconDef("image-x-generic", "photo"),
    IconDef("video-x-generic", "video"),
    IconDef("start-here-kde", "phoenix"),
]


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _ensure_tooling() -> None:
    if shutil.which("qlmanage") is None:
        raise SystemExit("macOS 'qlmanage' not found in PATH (required for gradient SVG rendering).")


def _svg_template(inner: str) -> str:
    # Circular medallion with gold trim + electric-blue inner symbol.
    # Keep it readable at small sizes: thick strokes, simple geometry.
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"512\" height=\"512\" viewBox=\"0 0 512 512\" version=\"1.1\">
  <defs>
    <radialGradient id=\"bg\" cx=\"50%\" cy=\"40%\" r=\"70%\">
      <stop offset=\"0%\" stop-color=\"#0F1730\"/>
      <stop offset=\"55%\" stop-color=\"#060A14\"/>
      <stop offset=\"100%\" stop-color=\"#020306\"/>
    </radialGradient>
    <linearGradient id=\"gold\" x1=\"0%\" y1=\"0%\" x2=\"100%\" y2=\"100%\">
      <stop offset=\"0%\" stop-color=\"#FFC857\"/>
      <stop offset=\"45%\" stop-color=\"#D4AF37\"/>
      <stop offset=\"100%\" stop-color=\"#8A6600\"/>
    </linearGradient>
    <linearGradient id=\"gold2\" x1=\"0%\" y1=\"0%\" x2=\"100%\" y2=\"0%\">
      <stop offset=\"0%\" stop-color=\"#D4AF37\"/>
      <stop offset=\"50%\" stop-color=\"#FFE29A\"/>
      <stop offset=\"100%\" stop-color=\"#D4AF37\"/>
    </linearGradient>
    <linearGradient id=\"blue\" x1=\"0%\" y1=\"0%\" x2=\"0%\" y2=\"100%\">
      <stop offset=\"0%\" stop-color=\"#1E6BFF\"/>
      <stop offset=\"100%\" stop-color=\"#00C3FF\"/>
    </linearGradient>
    <filter id=\"glow\" x=\"-40%\" y=\"-40%\" width=\"180%\" height=\"180%\">
      <feGaussianBlur stdDeviation=\"6\" result=\"b\"/>
      <feMerge>
        <feMergeNode in=\"b\"/>
        <feMergeNode in=\"SourceGraphic\"/>
      </feMerge>
    </filter>
  </defs>

  <circle cx=\"256\" cy=\"256\" r=\"228\" fill=\"url(#bg)\"/>
  <circle cx=\"256\" cy=\"256\" r=\"228\" fill=\"none\" stroke=\"url(#gold)\" stroke-width=\"14\"/>
  <circle cx=\"256\" cy=\"256\" r=\"206\" fill=\"none\" stroke=\"url(#gold2)\" stroke-width=\"6\" opacity=\"0.9\"/>
  <circle cx=\"256\" cy=\"256\" r=\"190\" fill=\"none\" stroke=\"#00C3FF\" stroke-opacity=\"0.18\" stroke-width=\"4\"/>

  <g filter=\"url(#glow)\" stroke-linecap=\"round\" stroke-linejoin=\"round\">
    {inner}
  </g>
</svg>
"""


def _inner_symbol(sym: str) -> str:
    # Use thick electric-blue strokes and minimal fills to match the reference board.
    stroke = 'stroke="url(#blue)" stroke-width="18" fill="none"'
    stroke2 = 'stroke="#00C3FF" stroke-width="12" fill="none"'
    fill = 'fill="url(#blue)"'

    if sym == "folder":
        return (
            f'<path d="M 158 230 H 242 L 268 258 H 354 C 372 258 386 272 386 290 V 338 C 386 356 372 370 354 370 H 158 C 140 370 126 356 126 338 V 262 C 126 244 140 230 158 230 Z" {stroke}/>'
            f'<path d="M 126 280 H 386" {stroke2} opacity="0.25"/>'
        )
    if sym == "home":
        return (
            f'<path d="M 168 294 L 256 214 L 344 294" {stroke}/>'
            f'<path d="M 202 294 V 356 H 242 V 320 H 270 V 356 H 310 V 294" {stroke}/>'
        )
    if sym == "document":
        return (
            f'<path d="M 202 200 H 302 L 336 234 V 362 H 202 Z" {stroke}/>'
            f'<path d="M 302 200 V 234 H 336" {stroke}/>'
            f'<path d="M 224 270 H 314" {stroke2}/>'
            f'<path d="M 224 304 H 314" {stroke2}/>'
            f'<path d="M 224 338 H 286" {stroke2}/>'
        )
    if sym == "download":
        return (
            f'<path d="M 256 206 V 314" {stroke}/>'
            f'<path d="M 210 276 L 256 322 L 302 276" {stroke}/>'
            f'<path d="M 204 350 H 308" {stroke}/>'
        )
    if sym == "music":
        return (
            f'<path d="M 300 214 V 334" {stroke}/>'
            f'<path d="M 300 214 C 270 222 246 230 214 238 V 268" {stroke}/>'
            f'<circle cx="214" cy="334" r="26" {fill} opacity="0.15"/>'
            f'<circle cx="214" cy="334" r="26" {stroke}/>'
            f'<circle cx="292" cy="350" r="26" {fill} opacity="0.15"/>'
            f'<circle cx="292" cy="350" r="26" {stroke}/>'
        )
    if sym == "photo":
        return (
            f'<rect x="188" y="224" width="136" height="120" rx="18" {stroke}/>'
            f'<circle cx="232" cy="262" r="16" {stroke}/>'
            f'<path d="M 202 332 L 238 296 L 266 324 L 292 304 L 316 332" {stroke2}/>'
        )
    if sym == "video":
        return (
            f'<rect x="182" y="226" width="148" height="116" rx="18" {stroke}/>'
            f'<path d="M 242 256 L 304 284 L 242 312 Z" {stroke}/>'
        )
    if sym in ("trash", "trash_full"):
        lid = '<path d="M 206 226 H 306" ' + stroke + '/>'
        can = '<path d="M 216 242 H 296 L 288 362 H 224 Z" ' + stroke + '/>'
        lines = (
            f'<path d="M 240 264 V 340" {stroke2}/>'
            f'<path d="M 272 264 V 340" {stroke2}/>'
        )
        fillbin = ''
        if sym == "trash_full":
            fillbin = '<path d="M 224 250 H 288 L 282 356 H 230 Z" fill="url(#blue)" opacity="0.18"/>'
        return lid + fillbin + can + lines
    if sym == "terminal":
        return (
            f'<rect x="168" y="222" width="176" height="128" rx="18" {stroke}/>'
            f'<path d="M 200 262 L 232 286 L 200 310" {stroke}/>'
            f'<path d="M 250 312 H 312" {stroke}/>'
        )
    if sym == "gear":
        # Simple readable gear: outer ring + 8 teeth + inner hub.
        return (
            f'<circle cx="256" cy="286" r="64" {stroke}/>'
            f'<circle cx="256" cy="286" r="24" {stroke2}/>'
            f'<path d="M 256 202 V 228" {stroke2}/>'
            f'<path d="M 256 344 V 370" {stroke2}/>'
            f'<path d="M 172 286 H 198" {stroke2}/>'
            f'<path d="M 314 286 H 340" {stroke2}/>'
            f'<path d="M 196 226 L 214 244" {stroke2}/>'
            f'<path d="M 316 346 L 298 328" {stroke2}/>'
            f'<path d="M 316 226 L 298 244" {stroke2}/>'
            f'<path d="M 196 346 L 214 328" {stroke2}/>'
        )
    if sym == "globe":
        return (
            f'<circle cx="256" cy="286" r="90" {stroke}/>'
            f'<path d="M 166 286 H 346" {stroke2}/>'
            f'<path d="M 256 196 C 228 228 216 256 216 286 C 216 316 228 344 256 376" {stroke2}/>'
            f'<path d="M 256 196 C 284 228 296 256 296 286 C 296 316 284 344 256 376" {stroke2}/>'
        )
    if sym == "mail":
        return (
            f'<rect x="178" y="232" width="156" height="112" rx="18" {stroke}/>'
            f'<path d="M 190 244 L 256 294 L 322 244" {stroke2}/>'
        )
    if sym == "calendar":
        return (
            f'<rect x="186" y="214" width="140" height="168" rx="22" {stroke}/>'
            f'<path d="M 186 252 H 326" {stroke2}/>'
            f'<path d="M 218 204 V 252" {stroke2}/>'
            f'<path d="M 294 204 V 252" {stroke2}/>'
        )
    if sym == "wifi":
        return (
            f'<path d="M 176 308 C 220 264 292 264 336 308" {stroke}/>'
            f'<path d="M 206 338 C 236 308 276 308 306 338" {stroke2}/>'
            f'<path d="M 234 366 C 246 354 266 354 278 366" {stroke2}/>'
            f'<circle cx="256" cy="386" r="16" fill="url(#blue)" opacity="0.22"/>'
            f'<circle cx="256" cy="386" r="16" {stroke2}/>'
        )
    if sym == "network":
        return (
            f'<circle cx="206" cy="296" r="26" {stroke}/>'
            f'<circle cx="318" cy="246" r="26" {stroke}/>'
            f'<circle cx="318" cy="346" r="26" {stroke}/>'
            f'<path d="M 232 284 L 292 262" {stroke2}/>'
            f'<path d="M 232 308 L 292 330" {stroke2}/>'
            f'<path d="M 318 272 V 320" {stroke2}/>'
        )
    if sym == "bluetooth":
        return (
            f'<path d="M 256 206 V 382" {stroke}/>'
            f'<path d="M 256 206 L 314 256 L 256 304 L 314 354 L 256 382" {stroke2}/>'
            f'<path d="M 198 252 L 256 304 L 198 356" {stroke2}/>'
        )
    if sym == "user":
        return (
            f'<circle cx="256" cy="262" r="40" {stroke}/>'
            f'<path d="M 184 378 C 198 338 228 320 256 320 C 284 320 314 338 328 378" {stroke2}/>'
        )
    if sym == "power":
        return (
            f'<path d="M 256 206 V 278" {stroke}/>'
            f'<path d="M 210 228 C 188 252 176 284 176 320 C 176 366 214 404 256 404 C 298 404 336 366 336 320 C 336 284 324 252 302 228" {stroke}/>'
        )
    if sym == "reboot":
        return (
            f'<path d="M 322 268 C 304 232 268 212 232 222 C 198 232 176 266 176 304 C 176 350 214 388 260 388 C 296 388 328 364 340 332" {stroke}/>'
            f'<path d="M 342 246 V 206 H 302" {stroke2}/>'
        )
    if sym == "question":
        return (
            f'<path d="M 214 266 C 216 236 238 220 262 220 C 286 220 306 234 306 258 C 306 292 256 288 256 324" {stroke}/>'
            f'<circle cx="256" cy="364" r="10" fill="url(#blue)"/>'
        )
    if sym == "drive":
        return (
            f'<rect x="186" y="252" width="140" height="112" rx="18" {stroke}/>'
            f'<circle cx="300" cy="340" r="10" fill="url(#blue)" opacity="0.25"/>'
            f'<circle cx="300" cy="340" r="10" {stroke2}/>'
            f'<circle cx="330" cy="340" r="10" fill="url(#blue)" opacity="0.25"/>'
            f'<circle cx="330" cy="340" r="10" {stroke2}/>'
        )
    if sym == "usb":
        return (
            f'<path d="M 256 198 V 328" {stroke}/>'
            f'<path d="M 256 198 L 238 216" {stroke2}/>'
            f'<path d="M 256 198 L 274 216" {stroke2}/>'
            f'<circle cx="256" cy="352" r="22" {stroke}/>'
        )
    if sym == "computer":
        return (
            f'<rect x="176" y="224" width="160" height="108" rx="16" {stroke}/>'
            f'<path d="M 224 352 H 288" {stroke2}/>'
            f'<path d="M 246 332 V 352" {stroke2}/>'
        )
    if sym == "shield":
        return (
            f'<path d="M 256 214 C 288 238 318 248 334 262 V 318 C 334 352 306 378 256 394 C 206 378 178 352 178 318 V 262 C 194 248 224 238 256 214 Z" {stroke}/>'
            f'<path d="M 256 238 V 382" {stroke2}/>'
        )
    if sym == "calculator":
        return (
            f'<rect x="206" y="206" width="100" height="188" rx="16" {stroke}/>'
            f'<path d="M 222 234 H 290" {stroke2}/>'
            f'<path d="M 226 276 H 242" {stroke2}/>'
            f'<path d="M 262 276 H 278" {stroke2}/>'
            f'<path d="M 226 316 H 242" {stroke2}/>'
            f'<path d="M 262 316 H 278" {stroke2}/>'
            f'<path d="M 226 356 H 242" {stroke2}/>'
            f'<path d="M 262 356 H 278" {stroke2}/>'
        )
    if sym == "edit":
        return (
            f'<path d="M 204 352 L 232 324 L 318 238 L 346 266 L 260 352 Z" {stroke}/>'
            f'<path d="M 198 358 L 226 358" {stroke2}/>'
        )
    if sym == "phoenix":
        # abstract crest
        return (
            f'<path d="M 256 214 C 232 226 218 250 218 276 C 218 302 232 322 256 334 C 280 322 294 302 294 276 C 294 250 280 226 256 214 Z" {stroke}/>'
            f'<path d="M 256 334 V 394" {stroke2}/>'
        )

    # fallback
    return f'<circle cx="256" cy="292" r="80" {stroke}/>'


def write_svg_sources(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for icon in ICONS:
        (out_dir / f"{icon.name}.svg").write_text(
            _svg_template(_inner_symbol(icon.symbol)), encoding="utf-8"
        )


def render_pngs(svg_dir: Path, out_dir: Path) -> None:
    """
    Render SVG -> PNG.

    Notes:
      - The local ImageMagick SVG renderer does not correctly render SVG gradients
        when the rsvg delegate is missing (outputs black/blank icons).
      - QuickLook (qlmanage) renders gradients correctly, but outputs opaque PNGs
        with a white background. We post-process by applying a circular alpha
        mask so icon corners are transparent.
      - We render once at 1024px then downsample to all required sizes.
    """

    for sz in SIZES:
        (out_dir / f"{sz}x{sz}").mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="home-aurelia-icon-render-") as td:
        tmp = Path(td)
        for icon in ICONS:
            svg = svg_dir / f"{icon.name}.svg"

            _run(["qlmanage", "-t", "-s", "1024", "-o", str(tmp), str(svg)])
            matches = sorted(tmp.glob(svg.name + "*.png"))
            if not matches:
                raise RuntimeError(f"qlmanage did not produce thumbnail for {svg}")
            thumb = matches[0]

            base = Image.open(thumb).convert("RGBA")
            w, h = base.size
            side = min(w, h)
            x0 = (w - side) // 2
            y0 = (h - side) // 2
            base = base.crop((x0, y0, x0 + side, y0 + side))

            # Apply circular alpha mask to remove QL's opaque white corners.
            cx = cy = side / 2.0
            r = side * 0.495
            px = base.load()
            for y in range(side):
                dy = y - cy
                for x in range(side):
                    dx = x - cx
                    d = math.sqrt(dx * dx + dy * dy)
                    if d <= r:
                        continue
                    rr, gg, bb, aa = px[x, y]
                    if d < r + 2.0:
                        na = int(aa * max(0.0, 1.0 - (d - r) / 2.0))
                        px[x, y] = (rr, gg, bb, na)
                    else:
                        px[x, y] = (rr, gg, bb, 0)

            for sz in SIZES:
                out = out_dir / f"{sz}x{sz}" / f"{icon.name}.png"
                im = base.resize((sz, sz), resample=Image.Resampling.LANCZOS)
                im.save(out)


def sync_theme_tree(dest_root: Path, svg_dir: Path, png_dir: Path) -> None:
    dest_root.mkdir(parents=True, exist_ok=True)

    # Preserve existing index.theme if present, otherwise seed it from CORE.
    if not (dest_root / "index.theme").exists() and (CORE_DIR / "index.theme").exists():
        shutil.copy2(CORE_DIR / "index.theme", dest_root / "index.theme")

    for ctx in CONTEXTS:
        (dest_root / "scalable" / ctx).mkdir(parents=True, exist_ok=True)
        for sz in SIZES:
            (dest_root / f"{sz}x{sz}" / ctx).mkdir(parents=True, exist_ok=True)

    # Copy each icon into every context directory (MaxCompat style).
    for icon in ICONS:
        src_svg = svg_dir / f"{icon.name}.svg"
        for ctx in CONTEXTS:
            shutil.copy2(src_svg, dest_root / "scalable" / ctx / f"{icon.name}.svg")
        for sz in SIZES:
            src_png = png_dir / f"{sz}x{sz}" / f"{icon.name}.png"
            for ctx in CONTEXTS:
                shutil.copy2(src_png, dest_root / f"{sz}x{sz}" / ctx / f"{icon.name}.png")


def main() -> None:
    _ensure_tooling()

    build_dir = CORE_DIR / "_rebuild_work"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    svg_dir = build_dir / "svg"
    png_dir = build_dir / "png"

    write_svg_sources(svg_dir)
    render_pngs(svg_dir, png_dir)

    sync_theme_tree(CORE_DIR, svg_dir, png_dir)
    sync_theme_tree(THEME_PACK_DIR, svg_dir, png_dir)
    sync_theme_tree(LIVE_BUILD_ICON_DIR, svg_dir, png_dir)

    print("OK: rebuilt Home Aurelia core icons")


if __name__ == "__main__":
    main()
