#!/usr/bin/python3
"""Compose Lugali App Store 6.9 screenshots v2 (pt-BR, 1320x2868, RGB, no alpha).

Editorial travel-poster direction: oversized left-aligned SF Pro, mango
highlight, cobalt field, discrete route marks. Reads ./raw, writes ./final-v2
and manifest-v2.json. Does not touch ./final or application source.
"""

from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1320, 2868
BLUE = (11, 87, 240)  # #0B57F0
WHITE = (255, 255, 255)
CREAM = (255, 247, 232)  # #FFF7E8
MANGO = (255, 194, 28)  # #FFC21C from the icon
INK = (28, 28, 30)  # #1C1C1E
SECONDARY = (110, 110, 115)
SF = "/System/Library/Fonts/SFNS.ttf"

DIR = Path(__file__).resolve().parent
REPO = DIR.parents[3]
RAW_DIR = DIR / "raw"
FINAL_V2 = DIR / "final-v2"
ICON = REPO / "InTheCity/Assets.xcassets/AppIcon.appiconset/AppIcon.png"

PAD = 64
PHONE_W = 1200

REJECT = [
    "Simulação",
    "Simulacao",
    "População",
    "Populacao",
    "In The City",
    "CityWatch",
    "a cada 10 minutos",
]

SCREENS = [
    {
        "id": "01",
        "raw": "01-cidade-atual.png",
        "final": "01-cidade-atual.png",
        "title": [("Você chegou.", "mango"), ("O Lugali conta onde.", "white")],
        "highlight": "Você chegou.",
        "subhead": "Cidade, estado e país na tela.",
        "mark": "arrive",
        "overlay": False,
        "title_sizes": (168, 82),
    },
    {
        "id": "02",
        "raw": "02-maps-clean.png",
        "final": "02-aviso-na-rota.png",
        "title": [("A cidade aparece.", "mango"), ("Sua rota continua.", "white")],
        "highlight": "A cidade aparece.",
        "subhead": "Sem sair do mapa.",
        "mark": "route",
        "overlay": True,
        "title_sizes": (128, 82),
    },
    {
        "id": "03",
        "raw": "03-historico.png",
        "final": "03-historico.png",
        "title": [("Sua viagem,", "white"), ("cidade por cidade.", "mango")],
        "highlight": "cidade por cidade.",
        "subhead": "Um histórico simples, salvo no seu iPhone.",
        "mark": "cities",
        "overlay": False,
        "title_sizes": (92, 124),
    },
]


def sf(size: float, weight: float = 400, opsz: float | None = None) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(SF, size)
    if opsz is None:
        opsz = max(17.0, min(96.0, size * 0.42))
    font.set_variation_by_axes([100, opsz, 400, weight])
    return font


def round_mask(size: tuple[int, int], radius: float) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def apply_round(im: Image.Image, radius: float) -> Image.Image:
    im = im.convert("RGBA")
    mask = round_mask(im.size, radius)
    im.putalpha(mask)
    return im


def drop_shadow(
    size: tuple[int, int],
    radius: float,
    blur: int = 42,
    opacity: int = 48,
    extra: int = 72,
    dy: int = 10,
) -> tuple[Image.Image, tuple[int, int]]:
    sw, sh = size[0] + extra * 2, size[1] + extra * 2
    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle(
        (extra, extra + dy, extra + size[0] - 1, extra + size[1] - 1),
        radius=radius,
        fill=(0, 0, 0, opacity),
    )
    return layer.filter(ImageFilter.GaussianBlur(blur)), (-extra, -extra)


def blit(dst: Image.Image, src: Image.Image, xy: tuple[int, int]) -> None:
    dst.alpha_composite(src.convert("RGBA"), xy)


def rounded_icon(path: Path, size: int) -> Image.Image:
    icon = Image.open(path).convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
    return apply_round(icon, radius=size * 0.2237)


def text_size(text: str, font: ImageFont.ImageFont) -> tuple[int, int, int, int]:
    dummy = Image.new("RGB", (8, 8))
    draw = ImageDraw.Draw(dummy)
    x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=font)
    return x0, y0, x1 - x0, y1 - y0


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple,
) -> tuple[int, int]:
    x, y = xy
    x0, y0, w, h = text_size(text, font)
    draw.text((x - x0, y - y0), text, font=font, fill=fill)
    return w, h


def bezier(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], n: int = 48) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(n + 1):
        t = i / n
        u = 1.0 - t
        x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
        y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def polyline_len(pts: list[tuple[float, float]]) -> list[float]:
    acc = [0.0]
    for i in range(1, len(pts)):
        dx = pts[i][0] - pts[i - 1][0]
        dy = pts[i][1] - pts[i - 1][1]
        acc.append(acc[-1] + math.hypot(dx, dy))
    return acc


def draw_dashed(draw: ImageDraw.ImageDraw, pts: list[tuple[float, float]], fill: tuple, width: int, dash: float = 22, gap: float = 14) -> None:
    if len(pts) < 2:
        return
    acc = polyline_len(pts)
    total = acc[-1]
    if total <= 0:
        return
    pos = 0.0
    on = True
    while pos < total:
        end = min(total, pos + (dash if on else gap))
        if on:
            seg: list[tuple[float, float]] = []
            for i, s in enumerate(acc):
                if s >= pos and (not seg or i == 0 or acc[i - 1] < pos):
                    if i > 0 and acc[i - 1] < pos <= s:
                        t = (pos - acc[i - 1]) / (s - acc[i - 1] or 1)
                        x = pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0])
                        y = pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1])
                        seg.append((x, y))
                if pos <= s <= end:
                    seg.append(pts[i])
                if s > end:
                    if i > 0:
                        t = (end - acc[i - 1]) / (s - acc[i - 1] or 1)
                        x = pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0])
                        y = pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1])
                        seg.append((x, y))
                    break
            if len(seg) >= 2:
                draw.line(seg, fill=fill, width=width, joint="curve")
        pos = end
        on = not on


def draw_marks(canvas: Image.Image, kind: str) -> None:
    """Discrete route / pin / map-curve marks. Flat color, no gradient."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cream = CREAM + (42,)
    cream_line = CREAM + (110,)
    mango = MANGO + (255,)

    if kind == "arrive":
        d.arc([760, -120, 1540, 660], start=198, end=430, fill=cream, width=34)
        d.ellipse([1266, 268, 1312, 314], fill=mango)
    elif kind == "route":
        pts = bezier((1288, 90), (980, 260), (1240, 620))
        draw_dashed(d, pts, cream_line, width=7, dash=26, gap=16)
        end = pts[-1]
        r = 11
        d.ellipse([end[0] - r, end[1] - r, end[0] + r, end[1] + r], fill=mango)
        d.ellipse([end[0] - 4, end[1] - 4, end[0] + 4, end[1] + 4], fill=BLUE + (255,))
    elif kind == "cities":
        pts = bezier((70, 430), (240, 560), (90, 720))
        d.line(pts, fill=cream_line, width=5, joint="curve")
        for i, t in enumerate((0.12, 0.5, 0.92)):
            idx = int(t * (len(pts) - 1))
            x, y = pts[idx]
            r = 9 if i < 2 else 12
            d.ellipse([x - r, y - r, x + r, y + r], fill=mango if i == 2 else CREAM + (200,))

    canvas.alpha_composite(layer)


def overlay_notification(maps: Image.Image, icon_path: Path) -> Image.Image:
    """iOS-like banner on the Maps capture. Title and body stay fully visible after scale."""
    base = maps.convert("RGBA")

    name_font = sf(38, weight=610, opsz=17)
    time_font = sf(34, weight=400, opsz=17)
    title_font = sf(54, weight=700, opsz=22)
    body_font = sf(46, weight=450, opsz=20)

    name, time, title, body = "Lugali", "agora", "Foz do Iguaçu", "PR · Brasil"
    pad_x, pad_v = 40, 44
    icon_size, icon_gap = 124, 28
    stack_h = 38 + 10 + 58 + 10 + 50
    card_w, card_h = 1236, pad_v + max(icon_size, stack_h) + pad_v
    card_x, card_y = 42, 168
    radius = 72
    text_x = card_x + pad_x + icon_size + icon_gap
    right = card_x + card_w - 44
    text_max = right - text_x
    if title_font.getlength(title) > text_max:
        raise SystemExit(f"notification title truncated: {title_font.getlength(title):.0f}px in {text_max}px")
    if body_font.getlength(body) > text_max:
        raise SystemExit(f"notification body truncated: {body_font.getlength(body):.0f}px in {text_max}px")

    frost = base.crop((card_x, card_y, card_x + card_w, card_y + card_h)).filter(ImageFilter.GaussianBlur(28))
    white = Image.new("RGB", frost.size, WHITE)
    frost = Image.blend(frost.convert("RGB"), white, 0.9).convert("RGBA")

    shadow, shadow_off = drop_shadow((card_w, card_h), radius, blur=26, opacity=58, extra=56)
    blit(base, shadow, (card_x + shadow_off[0], card_y + shadow_off[1] + 6))
    blit(base, apply_round(frost, radius), (card_x, card_y))

    outline = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    ImageDraw.Draw(outline).rounded_rectangle(
        (0, 0, card_w - 1, card_h - 1),
        radius=radius,
        outline=(0, 0, 0, 30),
        width=2,
    )
    blit(base, outline, (card_x, card_y))

    stack_top = card_y + (card_h - stack_h) // 2
    icon = rounded_icon(icon_path, icon_size)
    blit(base, icon, (card_x + pad_x, card_y + (card_h - icon_size) // 2))

    draw = ImageDraw.Draw(base)
    name_y = stack_top
    draw.text((text_x, name_y), name, font=name_font, fill=SECONDARY)
    tw = time_font.getlength(time)
    draw.text((right - tw, name_y + 2), time, font=time_font, fill=SECONDARY)
    title_y = name_y + 48
    draw.text((text_x, title_y), title, font=title_font, fill=INK)
    body_y = title_y + 64
    draw.text((text_x, body_y), body, font=body_font, fill=INK)
    return base


def measure_header(spec: dict) -> int:
    """Return y where the header block ends (below subtitle)."""
    y = 52
    y += 44  # brand icon
    y += 40  # gap before title
    sizes = spec["title_sizes"]
    for i, (line, _role) in enumerate(spec["title"]):
        size = sizes[i] if i < len(sizes) else sizes[-1]
        font = sf(size, weight=860 if spec["title"][i][1] == "mango" else 780, opsz=96)
        _x0, _y0, _w, h = text_size(line, font)
        y += h
        y += 10 if i == 0 else 0
    y += 28
    s_font = sf(36, weight=510, opsz=28)
    _x0, _y0, _w, sh = text_size(spec["subhead"], s_font)
    y += sh
    return y


def draw_header(canvas: Image.Image, spec: dict, icon_path: Path) -> int:
    draw = ImageDraw.Draw(canvas)
    x = PAD
    y = 52

    icon_size = 44
    icon = rounded_icon(icon_path, icon_size)
    blit(canvas, icon, (x, y))
    brand_font = sf(28, weight=590, opsz=24)
    _w, bh = draw_text(draw, (x + icon_size + 12, y + (icon_size - 28) // 2), "Lugali", brand_font, WHITE)
    y += icon_size + 40

    sizes = spec["title_sizes"]
    for i, (line, role) in enumerate(spec["title"]):
        size = sizes[i] if i < len(sizes) else sizes[-1]
        weight = 860 if role == "mango" else 780
        font = sf(size, weight=weight, opsz=96)
        fill = MANGO if role == "mango" else WHITE
        if font.getlength(line) > W - PAD * 2:
            raise SystemExit(f"title truncated: {line!r} at {size}px")
        _w, h = draw_text(draw, (x, y), line, font, fill)
        y += h + (8 if i == 0 else 0)

    y += 26
    s_font = sf(36, weight=510, opsz=28)
    if s_font.getlength(spec["subhead"]) > W - PAD * 2:
        raise SystemExit(f"subhead truncated: {spec['subhead']!r}")
    _w, sh = draw_text(draw, (x, y), spec["subhead"], s_font, CREAM)
    return y + sh


def compose_frame(screen: Image.Image, spec: dict, icon_path: Path) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), BLUE + (255,))
    draw_marks(canvas, spec["mark"])
    header_end = draw_header(canvas, spec, icon_path)

    scale = PHONE_W / screen.width
    phone_h = int(round(screen.height * scale))
    phone = screen.convert("RGBA").resize((PHONE_W, phone_h), Image.Resampling.LANCZOS)
    radius = 55 * 3 * scale
    phone = apply_round(phone, radius)

    phone_x = (W - PHONE_W) // 2
    phone_y = header_end + 44
    # Phone may extend past the canvas (breaks the top block, occupies more space).
    # Crop only empty lower chrome; keep UI text on-canvas.
    visible_raw = (H - phone_y) / scale
    if spec["id"] == "02":
        min_raw = 2320  # keep 26 min card and notification
    else:
        min_raw = 1680  # keep place rows; bottom is empty white
    if visible_raw < min_raw:
        raise SystemExit(
            f"{spec['id']} would crop UI text: visible raw {visible_raw:.0f}px < {min_raw}"
        )

    shadow, shadow_off = drop_shadow((PHONE_W, phone_h), radius, blur=48, opacity=72, extra=90, dy=18)
    blit(canvas, shadow, (phone_x + shadow_off[0], phone_y + shadow_off[1]))
    blit(canvas, phone, (phone_x, phone_y))

    stroke = Image.new("RGBA", (PHONE_W, phone_h), (0, 0, 0, 0))
    ImageDraw.Draw(stroke).rounded_rectangle(
        (0, 0, PHONE_W - 1, phone_h - 1),
        radius=radius,
        outline=(8, 16, 40, 70),
        width=3,
    )
    blit(canvas, stroke, (phone_x, phone_y))

    return canvas.convert("RGB")


def save_rgb(im: Image.Image, path: Path) -> None:
    rgb = im.convert("RGB")
    if rgb.size != (W, H):
        raise SystemExit(f"{path.name} size {rgb.size}, expected {(W, H)}")
    if rgb.mode != "RGB":
        raise SystemExit(f"{path.name} mode {rgb.mode}")
    if rgb.getbands() != ("R", "G", "B"):
        raise SystemExit(f"{path.name} bands {rgb.getbands()}")
    path.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(path, format="PNG", optimize=False, compress_level=6)


OCR_SWIFT = r"""
import Foundation
import Vision
import AppKit

let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
guard let ns = NSImage(contentsOf: url) else { fputs("no image\n", stderr); exit(2) }
var rect = CGRect(origin: .zero, size: ns.size)
guard let cg = ns.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
    fputs("no cgImage\n", stderr); exit(3)
}
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["pt-BR", "en-US"]
request.usesLanguageCorrection = false
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try handler.perform([request])
for obs in request.results ?? [] {
    if let s = obs.topCandidates(1).first?.string {
        print(s)
    }
}
"""


def compile_ocr(td: Path) -> Path:
    src = td / "ocr.swift"
    src.write_text(OCR_SWIFT, encoding="utf-8")
    bin_path = td / "ocr"
    compile = subprocess.run(
        ["swiftc", "-O", "-o", str(bin_path), str(src)],
        capture_output=True,
        text=True,
    )
    if compile.returncode != 0:
        raise SystemExit(f"swiftc OCR helper failed:\n{compile.stderr}")
    return bin_path


def ocr_image(bin_path: Path, path: Path) -> str:
    run = subprocess.run([str(bin_path), str(path)], capture_output=True, text=True)
    if run.returncode != 0:
        raise SystemExit(f"OCR failed for {path.name}:\n{run.stderr}")
    return run.stdout


def validate(path: Path, spec: dict, text: str) -> None:
    im = Image.open(path)
    if im.size != (W, H):
        raise SystemExit(f"{path.name} size {im.size}")
    if im.mode != "RGB":
        raise SystemExit(f"{path.name} mode {im.mode} (alpha not allowed)")
    if "A" in im.getbands():
        raise SystemExit(f"{path.name} has alpha band")
    folded = text
    low = folded.lower()
    for bad in REJECT:
        if bad.lower() in low:
            raise SystemExit(f"{path.name} OCR contains rejected {bad!r}")
    required = [spec["highlight"], "Lugali"]
    for line, _role in spec["title"]:
        required.append(line)
    required.append(spec["subhead"])
    if spec["overlay"]:
        required.extend(["Foz do Iguaçu", "PR · Brasil", "Lugali"])
    missing = []
    for needle in required:
        if needle not in folded and needle.replace("·", "·") not in folded:
            # OCR may drop accents; require at least the unaccented skeleton for headlines
            missing.append(needle)
    # Accents must be present in the file we drew; OCR is a secondary check.
    # Fail hard if a headline fragment is completely absent.
    soft_missing = []
    for needle in required:
        ok = needle in folded
        if not ok:
            # try without combining-sensitive glyphs
            simplified = (
                needle.replace("ç", "c")
                .replace("á", "a")
                .replace("é", "e")
                .replace("í", "i")
                .replace("ó", "o")
                .replace("ú", "u")
                .replace("ã", "a")
                .replace("ê", "e")
                .replace("ô", "o")
                .replace("·", " ")
            )
            folded_s = (
                folded.replace("ç", "c")
                .replace("Ç", "C")
                .replace("á", "a")
                .replace("é", "e")
                .replace("í", "i")
                .replace("ó", "o")
                .replace("ú", "u")
                .replace("ã", "a")
                .replace("ê", "e")
                .replace("ô", "o")
                .replace("·", " ")
                .replace("•", " ")
            )
            if simplified not in folded_s:
                soft_missing.append(needle)
    if soft_missing:
        raise SystemExit(f"{path.name} OCR missing {soft_missing}:\n{folded}")


def main() -> None:
    if not ICON.is_file():
        raise SystemExit(f"missing icon {ICON}")
    FINAL_V2.mkdir(parents=True, exist_ok=True)

    shots = []
    ocr_cache: dict[str, str] = {}
    for spec in SCREENS:
        raw_path = RAW_DIR / spec["raw"]
        if not raw_path.is_file():
            raise SystemExit(f"missing raw {raw_path}")
        raw = Image.open(raw_path)
        if spec["overlay"]:
            raw = overlay_notification(raw, ICON)
        frame = compose_frame(raw, spec, ICON)
        out = FINAL_V2 / spec["final"]
        save_rgb(frame, out)
        print(f"wrote {out.relative_to(DIR)}")
        shots.append(
            {
                "file": f"final-v2/{spec['final']}",
                "title_lines": [line for line, _ in spec["title"]],
                "highlight": spec["highlight"],
                "subhead": spec["subhead"],
                "origin": f"raw/{spec['raw']}",
                "overlay": (
                    {
                        "kind": "ios-notification-banner",
                        "app": "Lugali",
                        "title": "Foz do Iguaçu",
                        "body": "PR · Brasil",
                        "icon": str(ICON.relative_to(REPO)),
                    }
                    if spec["overlay"]
                    else None
                ),
                "mark": spec["mark"],
            }
        )

    print("OCR…")
    with tempfile.TemporaryDirectory() as td:
        ocr_bin = compile_ocr(Path(td))
        for spec in SCREENS:
            out = FINAL_V2 / spec["final"]
            text = ocr_image(ocr_bin, out)
            ocr_cache[spec["final"]] = text
            validate(out, spec, text)
            print(f"ok {spec['final']}")

    manifest = {
        "locale": "pt-BR",
        "size": "6.9",
        "version": "v2",
        "width": W,
        "height": H,
        "format": "PNG",
        "alpha": False,
        "color_space": "sRGB",
        "background": {
            "lugali_blue": "#0B57F0",
            "mango": "#FFC21C",
            "white": "#FFFFFF",
            "cream": "#FFF7E8",
        },
        "icon": str(ICON.relative_to(REPO)),
        "direction": "editorial travel poster; SF Pro left-aligned; one mango highlight per cover; phone breaks the cobalt field",
        "rejected": REJECT,
        "screenshots": shots,
        "commands": [f"/usr/bin/python3 {DIR / 'compose-v2.py'}"],
        "tool": "Python Pillow (/usr/bin/python3) + SFNS variable font",
        "output_dir": "final-v2",
        "preserves": "final/",
    }
    (DIR / "manifest-v2.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {DIR / 'manifest-v2.json'}")


if __name__ == "__main__":
    main()
