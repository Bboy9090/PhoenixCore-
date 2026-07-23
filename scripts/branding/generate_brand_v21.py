#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from xml.sax.saxutils import escape

SIZES = [16, 22, 24, 32, 48, 64, 128, 256, 512]
WALLS = [
    {"width": 1920, "height": 1080},
    {"width": 2560, "height": 1440},
    {"width": 3840, "height": 2160},
]

GLYPHS = {
    "mobile-command": '<rect x="155" y="72" width="202" height="368" rx="48"/><rect x="183" y="116" width="146" height="244" rx="22"/><path d="M202 267c34-92 87-106 109-41-29 3-48 22-55 54-13-27-31-31-54-13Z"/><circle cx="256" cy="400" r="13"/><path d="m332 144 47-8-8 47m-28-9 35-35"/>',
    "desktop-command": '<rect x="64" y="92" width="384" height="266" rx="34"/><rect x="97" y="132" width="318" height="178" rx="17"/><path d="M157 260c45-101 120-121 198-60-54 4-86 31-99 82-20-37-50-45-99-22Z"/><path d="M213 359h86l18 69H195Z"/><path d="M170 430h172"/>',
    "usb-forge": '<path d="M166 108h180v278H166Z"/><path d="M208 58h96v78h-96Z"/><path d="M226 58v78m60-78v78"/><path d="M256 174c-64 77-74 127-36 172 18 22 34 34 36 35 2-1 18-13 36-35 38-45 28-95-36-172Z"/><path d="m256 224 27 50-27 68-27-68Z"/>',
    "diagnosis-scan": '<circle cx="224" cy="221" r="136"/><circle cx="224" cy="221" r="96"/><rect x="176" y="132" width="96" height="176" rx="24"/><path d="m190 240 19-1 17-41 22 77 17-36 25 2"/><path d="m326 326 100 100"/><circle cx="406" cy="406" r="24"/>',
    "compatibility-matrix": '<path d="m104 184 102-60 102 60v114l-102 60-102-60Z"/><path d="m238 273 94-56 94 56v108l-94 56-94-56Z"/><circle cx="206" cy="239" r="30"/><rect x="307" y="300" width="50" height="50" rx="12"/><path d="m350 253 25 25 57-68"/>',
    "planning-route": '<path d="M126 76h232l56 59v302H126Z"/><path d="M358 76v70h56"/><path d="M178 204h130m-130 47h102"/><circle cx="184" cy="348" r="18"/><circle cx="286" cy="318" r="18"/><circle cx="384" cy="367" r="18"/><path d="M184 348c41-79 72 48 102-30 29-73 64 49 98 49"/>',
    "media-stack": '<rect x="96" y="120" width="320" height="72" rx="26"/><rect x="96" y="220" width="320" height="72" rx="26"/><rect x="96" y="320" width="320" height="72" rx="26"/><path d="M256 78v255m-50-46 50 50 50-50"/><path d="m320 382 29 29 61-70"/>',
    "session-orbit": '<circle cx="256" cy="256" r="76"/><circle cx="256" cy="256" r="156"/><circle cx="256" cy="82" r="35"/><circle cx="430" cy="256" r="35"/><circle cx="256" cy="430" r="35"/><circle cx="82" cy="256" r="35"/><path d="M256 117v63m139 76h-63m-76 139v-63M117 256h63"/><path d="m222 258 27 28 54-65"/>',
    "identity-print": '<path d="M256 70 409 134v120c0 96-56 154-153 194-97-40-153-98-153-194V134Z"/><path d="M256 153c-56 0-95 43-95 98 0 80 56 66 56 147m39-210c-36 0-58 28-58 63 0 64 46 53 46 122m12-220c56 0 95 43 95 98 0 80-56 66-56 147m-39-210c36 0 58 28 58 63 0 64-46 53-46 122"/><circle cx="256" cy="255" r="25"/>',
    "deployment-gate": '<rect x="82" y="104" width="156" height="262" rx="28"/><rect x="274" y="104" width="156" height="262" rx="28"/><path d="M126 170h70m-70 48h55"/><path d="m307 233 45 45 84-98"/><path d="M160 407h192"/><path d="M236 242h46m-23-23 23 23-23 23"/>',
    "recovery-vault": '<rect x="70" y="90" width="372" height="336" rx="42"/><circle cx="256" cy="259" r="108"/><circle cx="256" cy="259" r="69"/><circle cx="256" cy="259" r="24"/><path d="M256 151v40m0 136v40M148 259h40m136 0h40"/><path d="m224 261 27 27 57-65"/>',
    "technician-tools": '<rect x="78" y="84" width="356" height="254" rx="32"/><path d="M124 151h212m-212 46h142"/><path d="m170 422 132-132m-165 88 88-88"/><path d="M319 282c35-43 73-54 109-27-36 17-51 45-46 84Z"/><path d="M151 292c-40 5-65-8-77-40 29 2 48-8 59-34l59 59Z"/>',
}


def icon(p):
    c = p["colors"]
    q = GLYPHS[p["motif"]]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><title>{escape(p['name'])}</title><desc>{escape(p['description'])}</desc><defs><linearGradient id="a" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c['primary']}"/><stop offset=".52" stop-color="{c['secondary']}"/><stop offset="1" stop-color="{c['accent']}"/></linearGradient><linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c['background']}"/><stop offset="1" stop-color="#02050A"/></linearGradient><filter id="g"><feGaussianBlur stdDeviation="7" result="x"/><feMerge><feMergeNode in="x"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><rect width="512" height="512" rx="110" fill="url(#b)"/><rect x="16" y="16" width="480" height="480" rx="96" fill="none" stroke="url(#a)" stroke-width="3" opacity=".5"/><circle cx="256" cy="256" r="202" fill="none" stroke="{c['primary']}" stroke-width="2" stroke-dasharray="2 16" opacity=".35"/><g fill="none" stroke="url(#a)" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" filter="url(#g)">{q}</g><path d="M112 447h288" stroke="url(#a)" stroke-width="5" stroke-linecap="round" opacity=".7"/></svg>"""


def wallpaper(p):
    c = p["colors"]
    q = GLYPHS[p["motif"]]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080"><title>{escape(p['name'])}</title><desc>{escape(p['description'])}</desc><defs><linearGradient id="s" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c['background']}"/><stop offset=".48" stop-color="#07182D"/><stop offset="1" stop-color="#02050A"/></linearGradient><linearGradient id="a" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c['primary']}"/><stop offset=".5" stop-color="{c['secondary']}"/><stop offset="1" stop-color="{c['accent']}"/></linearGradient><radialGradient id="n"><stop stop-color="{c['secondary']}" stop-opacity=".35"/><stop offset="1" stop-color="{c['primary']}" stop-opacity="0"/></radialGradient><filter id="g"><feGaussianBlur stdDeviation="10" result="x"/><feMerge><feMergeNode in="x"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><rect width="1920" height="1080" fill="url(#s)"/><ellipse cx="1400" cy="420" rx="650" ry="470" fill="url(#n)"/><path d="M0 920c330-190 650-170 940-35 300 140 620 120 980-80v275H0Z" fill="{c['primary']}" opacity=".16"/><path d="M80 250C430 20 835 31 1130 168c300 139 533 104 710-44" fill="none" stroke="url(#a)" stroke-width="5" opacity=".3"/><path d="M120 860h650" stroke="url(#a)" stroke-width="8" stroke-linecap="round"/><path d="m128 826 28-50 28 50-28 50Z" fill="url(#a)" filter="url(#g)"/><g transform="translate(1120 220) scale(1.28)" fill="none" stroke="url(#a)" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" filter="url(#g)">{q}</g><circle cx="1448" cy="548" r="330" fill="none" stroke="{c['primary']}" stroke-width="3" stroke-dasharray="5 22" opacity=".4"/></svg>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    out = Path(a.output)
    data = json.loads(Path(a.manifest).read_text())
    (out / "icons").mkdir(parents=True, exist_ok=True)
    (out / "wallpapers").mkdir(parents=True, exist_ok=True)
    icons = []
    walls = []
    for p in data["products"]:
        slug = p["slug"]
        (out / "icons" / f"{slug}.svg").write_text(icon(p) + "\n")
        (out / "wallpapers" / f"{slug}-hero.svg").write_text(wallpaper(p) + "\n")
        icons.append(
            {
                "product": p["name"],
                "path": f"{out.as_posix()}/icons/{slug}.svg",
                "role": p["role"],
            }
        )
        walls.append(
            {
                "product": p["name"],
                "path": f"{out.as_posix()}/wallpapers/{slug}-hero.svg",
                "scene": p["scene"],
            }
        )
    spec = {
        "schema_version": "2.1.0",
        "icon_master": {
            "format": "svg",
            "view_box": "0 0 512 512",
            "required_png_exports": SIZES,
            "alpha_required_for_symbol_exports": True,
        },
        "hero_wallpaper": {
            "format": "svg",
            "view_box": "0 0 1920 1080",
            "required_png_exports": WALLS,
        },
        "quality_gates": [
            "valid XML",
            "no embedded raster images",
            "no baked labels or UI fragments",
            "no fake checkerboard backgrounds",
            "one distinct silhouette per application",
            "small-size silhouette remains legible",
        ],
    }
    (out / "EXPORT_SPEC.json").write_text(json.dumps(spec, indent=2) + "\n")
    (out / "ASSET_MANIFEST.json").write_text(
        json.dumps({"schema_version": "2.1.0", "icons": icons}, indent=2) + "\n"
    )
    (out / "WALLPAPER_MANIFEST.json").write_text(
        json.dumps(
            {
                "schema_version": "2.1.0",
                "canvas": {"width": 1920, "height": 1080, "format": "svg"},
                "wallpapers": walls,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "products": len(data["products"]),
                "icons": len(icons),
                "wallpapers": len(walls),
                "output": str(out),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
