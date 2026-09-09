#!/usr/bin/python3
"""Compose Lugali App Store 6.9 screenshots (pt-BR, 1320x2868, RGB, no alpha)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1320, 2868
BLUE = (11, 87, 240)  # #0B57F0
WHITE = (255, 255, 255)
INK = (28, 28, 30)  # #1C1C1E
SECONDARY = (110, 110, 115)
SF = "/System/Library/Fonts/SFNS.ttf"

DIR = Path(__file__).resolve().parent
REPO = DIR.parents[3]
RAW_DIR = DIR / "raw"
FINAL_DIR = DIR / "final"
ICON = REPO / "InTheCity/Assets.xcassets/AppIcon.appiconset/AppIcon.png"

SOURCES = {
    "01-cidade-atual.png": Path("/tmp/lugali-appstore/raw2/01-cidade-atual.png"),
    "02-maps-clean.png": Path("/tmp/lugali-appstore/maps-burst/maps-clean.png"),
    "03-historico.png": Path("/tmp/lugali-appstore/raw2/03-historico.png"),
}

SCREENS = [
    {
        "id": "01",
        "raw": "01-cidade-atual.png",
        "final": "01-cidade-atual.png",
        "headline": "Descubra a cidade atual",
        "subhead": "Cidade, estado e país em um só lugar.",
        "overlay": False,
    },
    {
        "id": "02",
        "raw": "02-maps-clean.png",
        "final": "02-aviso-na-rota.png",
        "headline": "Receba o aviso durante a rota",
        "subhead": "Veja a cidade sem sair do mapa.",
        "overlay": True,
    },
    {
        "id": "03",
        "raw": "03-historico.png",
        "final": "03-historico.png",
        "headline": "Relembre o caminho",
        "subhead": "As cidades visitadas ficam salvas no seu iPhone.",
        "overlay": False,
    },
]

REJECT = [
    "Simulação",
    "Simulacao",
    "População",
    "Populacao",
    "In The City",
    "CityWatch",
    "a cada 10 minutos",
]


def sf(size: float, weight: float = 400, opsz: float | None = None) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(SF, size)
    if opsz is None:
        opsz = max(17.0, min(96.0, size * 0.42))
    # Width, Optical Size, GRAD, Weight
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
) -> tuple[Image.Image, tuple[int, int]]:
    sw, sh = size[0] + extra * 2, size[1] + extra * 2
    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle(
        (extra, extra + 10, extra + size[0] - 1, extra + size[1] - 1),
        radius=radius,
        fill=(0, 0, 0, opacity),
    )
    return layer.filter(ImageFilter.GaussianBlur(blur)), (-extra, -extra)


def blit(dst: Image.Image, src: Image.Image, xy: tuple[int, int]) -> None:
    dst.alpha_composite(src.convert("RGBA"), xy)


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    if "\n" in text:
        return text
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = word if not cur else f"{cur} {word}"
        if font.getlength(trial) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def text_block_size(text: str, font: ImageFont.ImageFont, spacing: int) -> tuple[int, int]:
    dummy = Image.new("RGB", (4, 4))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, align="center")
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_centered(
    canvas: Image.Image,
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple,
    cx: int,
    top: int,
    spacing: int = 8,
) -> int:
    draw = ImageDraw.Draw(canvas)
    w, h = text_block_size(text, font, spacing)
    x = int(cx - w / 2)
    draw.multiline_text((x, top), text, font=font, fill=fill, spacing=spacing, align="center")
    return top + h


def rounded_icon(path: Path, size: int) -> Image.Image:
    icon = Image.open(path).convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
    return apply_round(icon, radius=size * 0.2237)


def overlay_notification(maps: Image.Image, icon_path: Path) -> Image.Image:
    """iOS-like banner on the Maps capture. Sized so title and body stay fully visible after scale."""
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

    frost = base.crop((card_x, card_y, card_x + card_w, card_y + card_h)).filter(
        ImageFilter.GaussianBlur(28)
    )
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


def compose_frame(screen: Image.Image, headline: str, subhead: str) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), WHITE + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, W, 560), fill=BLUE + (255,))

    text_width = W - 120
    cx = W // 2

    h_font = sf(70, weight=800, opsz=96)
    wrapped_h = wrap_text(headline, h_font, text_width)
    if wrapped_h.count("\n") >= 1 or h_font.getlength(wrapped_h.replace("\n", " ")) > text_width:
        h_font = sf(64, weight=800, opsz=92)
        wrapped_h = wrap_text(headline, h_font, text_width)
    if headline == "Receba o aviso durante a rota":
        wrapped_h = "Receba o aviso\ndurante a rota"
        h_font = sf(70, weight=800, opsz=96)

    s_font = sf(38, weight=450, opsz=32)
    wrapped_s = wrap_text(subhead, s_font, text_width)

    y = 86
    y = draw_centered(canvas, wrapped_h, h_font, WHITE, cx, y, spacing=4)
    y += 16
    draw_centered(canvas, wrapped_s, s_font, WHITE, cx, y, spacing=6)

    phone_w = 1080
    scale = phone_w / screen.width
    phone_h = int(round(screen.height * scale))
    phone = screen.convert("RGBA").resize((phone_w, phone_h), Image.Resampling.LANCZOS)
    radius = 55 * 3 * scale
    phone = apply_round(phone, radius)

    phone_x = (W - phone_w) // 2
    phone_y = 428

    shadow, shadow_off = drop_shadow((phone_w, phone_h), radius, blur=44, opacity=50, extra=80)
    blit(canvas, shadow, (phone_x + shadow_off[0], phone_y + shadow_off[1]))
    blit(canvas, phone, (phone_x, phone_y))

    stroke = Image.new("RGBA", (phone_w, phone_h), (0, 0, 0, 0))
    ImageDraw.Draw(stroke).rounded_rectangle(
        (0, 0, phone_w - 1, phone_h - 1),
        radius=radius,
        outline=(0, 0, 0, 36),
        width=2,
    )
    blit(canvas, stroke, (phone_x, phone_y))

    return canvas.convert("RGB")


def copy_raws() -> list[str]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    commands = []
    for name, src in SOURCES.items():
        dest = RAW_DIR / name
        shutil.copy2(src, dest)
        commands.append(f"cp {src} {dest}")
    return commands


def save_rgb(im: Image.Image, path: Path) -> None:
    rgb = im.convert("RGB")
    if rgb.size != (W, H):
        raise SystemExit(f"{path.name} size {rgb.size}, expected {(W, H)}")
    if rgb.mode != "RGB":
        raise SystemExit(f"{path.name} mode {rgb.mode}")
    path.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(path, format="PNG", optimize=False, compress_level=6)


def main() -> None:
    commands = copy_raws()
    commands.append(f"/usr/bin/python3 {DIR / 'compose.py'}")

    icon = ICON
    if not icon.is_file():
        raise SystemExit(f"missing icon {icon}")

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    shots = []
    for spec in SCREENS:
        raw_path = RAW_DIR / spec["raw"]
        raw = Image.open(raw_path)
        if spec["overlay"]:
            raw = overlay_notification(raw, icon)
        frame = compose_frame(raw, spec["headline"], spec["subhead"])
        out = FINAL_DIR / spec["final"]
        save_rgb(frame, out)
        shots.append(
            {
                "file": f"final/{spec['final']}",
                "headline": spec["headline"],
                "subhead": spec["subhead"],
                "origin": f"raw/{spec['raw']}",
                "origin_source": str(SOURCES[spec["raw"]]),
                "overlay": (
                    {
                        "kind": "ios-notification-banner",
                        "app": "Lugali",
                        "title": "Foz do Iguaçu",
                        "body": "PR · Brasil",
                        "icon": str(icon.relative_to(REPO)),
                    }
                    if spec["overlay"]
                    else None
                ),
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
        "background": {"white": "#FFFFFF", "lugali_blue": "#0B57F0"},
        "icon": str(icon.relative_to(REPO)),
        "rejected": REJECT,
        "screenshots": shots,
        "commands": commands,
        "tool": "Python Pillow (/usr/bin/python3) + SFNS variable font",
    }
    (DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote 3 screenshots + {DIR / 'manifest.json'}")


if __name__ == "__main__":
    main()
