#!/usr/bin/python3
"""Compose three distinct Lugali 6.9 concept screenshots (pt-BR, 1320x2868, RGB)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))

from compose import (  # noqa: E402
    BLUE,
    H,
    ICON,
    INK,
    RAW_DIR,
    REPO,
    SECONDARY,
    W,
    WHITE,
    apply_round,
    blit,
    overlay_notification,
    rounded_icon,
    save_rgb,
    sf,
    wrap_text,
)

YELLOW = (255, 214, 10)
NAVY_LINE = (180, 210, 255)
CONCEPTS_DIR = DIR / "conceitos"

HEADLINE = "Cada cidade, no momento certo."
SUBHEAD = "O Lugali identifica onde você está e mostra cidade, estado e país."

BANNER_X, BANNER_Y = 42, 168
BANNER_W, BANNER_H = 1236, 254


def font_h(font) -> int:
    bbox = font.getbbox("Áyçú")
    return bbox[3] - bbox[1]


def draw_left(draw: ImageDraw.ImageDraw, text: str, font, fill, x: int, y: int, spacing: int) -> int:
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=spacing, align="left")
    bbox = draw.multiline_textbbox((x, y), text, font=font, spacing=spacing, align="left")
    return bbox[3]


def draw_signature(canvas: Image.Image, icon_path: Path, x: int, y: int, fill, icon_size: int = 56) -> int:
    icon = rounded_icon(icon_path, icon_size)
    blit(canvas, icon, (x, y))
    font = sf(36, weight=700, opsz=28)
    draw = ImageDraw.Draw(canvas)
    ty = y + (icon_size - font_h(font)) // 2 - 2
    draw.text((x + icon_size + 16, ty), "Lugali", font=font, fill=fill)
    return y + icon_size


def crop_ui(im: Image.Image, bottom: int) -> Image.Image:
    return im.crop((0, 0, im.width, min(bottom, im.height)))


def place_phone(canvas: Image.Image, screen: Image.Image, xy: tuple[int, int], width: int, radius: float = 48) -> None:
    scale = width / screen.width
    height = int(round(screen.height * scale))
    phone = screen.convert("RGBA").resize((width, height), Image.Resampling.LANCZOS)
    phone = apply_round(phone, radius)
    stroke = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(stroke).rounded_rectangle(
        (0, 0, width - 1, height - 1),
        radius=radius,
        outline=(0, 0, 0, 40),
        width=3,
    )
    blit(canvas, phone, xy)
    blit(canvas, stroke, xy)


def extract_banner(backdrop: Image.Image, icon_path: Path) -> Image.Image:
    layered = overlay_notification(backdrop.convert("RGB"), icon_path)
    return layered.crop((BANNER_X, BANNER_Y, BANNER_X + BANNER_W, BANNER_Y + BANNER_H))


def cover_map(raw: Image.Image) -> Image.Image:
    crop = raw.crop((0, 0, raw.width, 1480))
    scale = max(W / crop.width, H / crop.height)
    nw, nh = int(round(crop.width * scale)), int(round(crop.height * scale))
    big = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - W) // 2)
    top = max(0, (nh - H) // 2)
    return big.crop((left, top, left + W, top + H)).convert("RGBA")


def draw_pin(draw: ImageDraw.ImageDraw, xy: tuple[int, int], r: int = 28) -> None:
    x, y = xy
    draw.ellipse((x - r, y - r, x + r, y + r), fill=YELLOW)
    draw.ellipse((x - r + 10, y - r + 10, x + r - 10, y + r - 10), fill=BLUE)


def draw_topo(draw: ImageDraw.ImageDraw) -> None:
    cx, cy = 1080, 1980
    for i in range(9):
        rx = 220 + i * 108
        ry = 150 + i * 86
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=NAVY_LINE, width=4)
    cx2, cy2 = 180, 2460
    for i in range(6):
        rx = 160 + i * 120
        ry = 110 + i * 90
        draw.ellipse((cx2 - rx, cy2 - ry, cx2 + rx, cy2 + ry), outline=WHITE, width=4)


def draw_headline_stack(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    font,
    base,
    accent,
    spacing: int,
) -> int:
    lh = font_h(font) + spacing
    draw.text((x, y), "Cada cidade,", font=font, fill=base)
    y += lh
    no = "no "
    draw.text((x, y), no, font=font, fill=base)
    draw.text((x + font.getlength(no), y), "momento", font=font, fill=accent)
    y += lh
    draw.text((x, y), "certo.", font=font, fill=accent)
    return y + font_h(font)


def compose_editorial(cidade: Image.Image, icon_path: Path) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), BLUE + (255,))
    draw = ImageDraw.Draw(canvas)
    draw_topo(draw)

    x = 64
    y = 72
    y = draw_signature(canvas, icon_path, x, y, WHITE, icon_size=56)
    y += 64

    h_font = sf(112, weight=800, opsz=96)
    y = draw_headline_stack(draw, x, y, h_font, WHITE, YELLOW, spacing=18)
    y += 48

    s_font = sf(44, weight=510, opsz=36)
    wrapped = wrap_text(SUBHEAD, s_font, 720)
    y = draw_left(draw, wrapped, s_font, WHITE, x, y, spacing=10)
    y += 56

    route_font = sf(42, weight=700, opsz=36)
    meta_font = sf(36, weight=560, opsz=28)
    p1, p2 = (92, y + 36), (92, y + 292)
    draw.line([p1, p2], fill=YELLOW, width=14)
    draw_pin(draw, p1, 26)
    draw_pin(draw, p2, 26)
    draw.text((136, p1[1] - 48), "Foz do Iguaçu", font=route_font, fill=WHITE)
    draw.text((136, p1[1] + 4), "Brasil", font=meta_font, fill=YELLOW)
    draw.text((136, p2[1] - 48), "Puerto Iguazú", font=route_font, fill=WHITE)
    draw.text((136, p2[1] + 4), "Argentina", font=meta_font, fill=YELLOW)

    phone = crop_ui(cidade, 1680)
    place_phone(canvas, phone, (620, 1180), 860, radius=52)

    banner = extract_banner(Image.new("RGB", (W, H), BLUE), icon_path)
    banner = banner.resize((620, int(BANNER_H * 620 / BANNER_W)), Image.Resampling.LANCZOS)
    blit(canvas, banner.convert("RGBA"), (48, H - banner.height - 56))
    return canvas.convert("RGB")


def compose_immersive(maps: Image.Image, icon_path: Path) -> Image.Image:
    canvas = cover_map(maps)
    canvas = overlay_notification(canvas.convert("RGB"), icon_path).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    p1, p2 = (280, 720), (980, 1280)
    draw.line([p1, p2], fill=YELLOW, width=16)
    draw_pin(draw, p1, 30)
    draw_pin(draw, p2, 30)

    lab = sf(42, weight=700, opsz=36)
    meta = sf(36, weight=560, opsz=28)
    # Solid dark plates only under labels — map stays bright elsewhere.
    plates = [
        (40, 620, 560, 820, "Foz do Iguaçu", "Brasil"),
        (720, 1180, 1276, 1380, "Puerto Iguazú", "Argentina"),
    ]
    for x0, y0, x1, y1, title, country in plates:
        draw.rectangle((x0, y0, x1, y1), fill=(0, 0, 0, 170))
        draw.text((x0 + 28, y0 + 28), title, font=lab, fill=WHITE)
        draw.text((x0 + 28, y0 + 88), country, font=meta, fill=YELLOW)

    panel_top = 1688
    draw.rectangle((0, panel_top, W, H), fill=(0, 0, 0, 160))
    draw.rectangle((40, panel_top + 28, W - 40, H - 40), fill=BLUE + (255,))

    x = 88
    y = panel_top + 64
    y = draw_signature(canvas, icon_path, x, y, WHITE, icon_size=56)
    y += 36
    h_font = sf(84, weight=800, opsz=96)
    y = draw_headline_stack(draw, x, y, h_font, WHITE, YELLOW, spacing=12)
    y += 28
    s_font = sf(42, weight=510, opsz=34)
    wrapped = wrap_text(SUBHEAD, s_font, W - 176)
    draw_left(draw, wrapped, s_font, WHITE, x, y, spacing=8)
    return canvas.convert("RGB")


def city_card(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    size: tuple[int, int],
    title: str,
    subtitle: str,
) -> None:
    x, y = xy
    w, h = size
    draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill=BLUE)
    title_font = sf(42, weight=750, opsz=36)
    sub_font = sf(36, weight=560, opsz=28)
    draw.text((x + 32, y + 28), title, font=title_font, fill=WHITE)
    draw.text((x + 32, y + 84), subtitle, font=sub_font, fill=YELLOW)


def compose_minimal(historico: Image.Image, icon_path: Path) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), WHITE + (255,))
    draw = ImageDraw.Draw(canvas)

    x = 64
    y = 72
    y = draw_signature(canvas, icon_path, x, y, BLUE, icon_size=56)
    y += 56

    h_font = sf(120, weight=800, opsz=96)
    y = draw_headline_stack(draw, x, y, h_font, BLUE, BLUE, spacing=16)
    y += 40

    s_font = sf(44, weight=510, opsz=36)
    wrapped = wrap_text(SUBHEAD, s_font, W - 128)
    y = draw_left(draw, wrapped, s_font, INK, x, y, spacing=10)
    y += 64

    c1 = (64, y)
    c2 = (64, y + 430)
    city_card(draw, c1, (720, 168), "Foz do Iguaçu", "Brasil")
    city_card(draw, c2, (720, 168), "Puerto Iguazú", "Argentina")

    p1 = (c1[0] + 760, c1[1] + 84)
    p2 = (c2[0] + 760, c2[1] + 84)
    draw.line([p1, p2], fill=YELLOW, width=18)
    draw_pin(draw, p1, 30)
    draw_pin(draw, p2, 30)

    axis_font = sf(36, weight=700, opsz=28)
    draw.text((p1[0] + 48, p1[1] - 22), "Brasil", font=axis_font, fill=BLUE)
    draw.text((p2[0] + 48, p2[1] - 22), "Argentina", font=axis_font, fill=BLUE)

    phone = crop_ui(historico, 1620)
    place_phone(canvas, phone, (430, 1688), 720, radius=44)

    banner = extract_banner(Image.new("RGB", (W, H), WHITE), icon_path)
    banner_w = 1180
    banner = banner.resize((banner_w, int(BANNER_H * banner_w / BANNER_W)), Image.Resampling.LANCZOS)
    blit(canvas, banner.convert("RGBA"), ((W - banner_w) // 2, H - banner.height - 48))
    return canvas.convert("RGB")


def main() -> None:
    icon = ICON
    if not icon.is_file():
        raise SystemExit(f"missing icon {icon}")

    cidade = Image.open(RAW_DIR / "01-cidade-atual.png")
    maps = Image.open(RAW_DIR / "02-maps-clean.png")
    historico = Image.open(RAW_DIR / "03-historico.png")

    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    specs = [
        {
            "file": "01-editorial.png",
            "model": "editorial",
            "image": compose_editorial(cidade, icon),
            "origin": "raw/01-cidade-atual.png",
        },
        {
            "file": "02-mapa-imersivo.png",
            "model": "mapa-imersivo",
            "image": compose_immersive(maps, icon),
            "origin": "raw/02-maps-clean.png",
        },
        {
            "file": "03-rota-minimalista.png",
            "model": "rota-minimalista",
            "image": compose_minimal(historico, icon),
            "origin": "raw/03-historico.png",
        },
    ]

    shots = []
    for spec in specs:
        out = CONCEPTS_DIR / spec["file"]
        save_rgb(spec["image"], out)
        shots.append(
            {
                "file": f"conceitos/{spec['file']}",
                "model": spec["model"],
                "headline": HEADLINE,
                "subhead": SUBHEAD,
                "origin": spec["origin"],
                "route": "Brasil–Argentina",
                "cities": ["Foz do Iguaçu", "Puerto Iguazú"],
                "warning": "aviso Lugali",
                "signature": {"icon": str(icon.relative_to(REPO)), "name": "Lugali"},
            }
        )

    manifest = {
        "locale": "pt-BR",
        "size": "6.9",
        "width": W,
        "height": H,
        "format": "PNG",
        "alpha": False,
        "color_space": "sRGB",
        "headline": HEADLINE,
        "subhead": SUBHEAD,
        "backgrounds": {
            "editorial": "#0B57F0",
            "mapa-imersivo": "mapa full bleed + painel #0B57F0",
            "rota-minimalista": "#FFFFFF",
        },
        "accent": "#FFD60A",
        "icon": str(icon.relative_to(REPO)),
        "screenshots": shots,
        "commands": [
            "mkdir -p docs/screenshots-puros",
            "cp -p docs/app-store/pt-BR/6.9/raw/*.png docs/screenshots-puros/",
            f"/usr/bin/python3 {DIR / 'compose-concepts.py'}",
        ],
        "tool": "Python Pillow (/usr/bin/python3) + SFNS variable font",
    }
    (DIR / "manifest-concepts.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote 3 concepts + {DIR / 'manifest-concepts.json'}")


if __name__ == "__main__":
    main()
