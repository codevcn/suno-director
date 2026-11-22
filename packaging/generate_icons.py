"""Generate crisp PNG, multi-size Windows ICO, and Inno Setup BMPs for V1 Baton Pulse (Cyan Pulse)."""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "logos"
BG_DARK = (11, 13, 18, 255)       # #0B0D12
BORDER = (30, 41, 59, 255)        # #1E293B
CYAN_PULSE = (56, 189, 248, 255)  # #38BDF8
CYAN_TIP = (125, 211, 252, 255)   # #7DD3FC


def _draw_round_cap_line(draw: ImageDraw.ImageDraw, p1: tuple[float, float], p2: tuple[float, float], width: float, color: tuple[int, int, int, int]) -> None:
    draw.line([p1, p2], fill=color, width=round(width))
    r = width / 2.0
    for x, y in (p1, p2):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def render_badge(size: int = 1024, *, with_background: bool = True) -> Image.Image:
    scale = 4
    s = size * scale
    k = s / 100.0
    bg = (0, 0, 0, 0)
    img = Image.new("RGBA", (s, s), bg)
    draw = ImageDraw.Draw(img)

    if with_background:
        draw.rounded_rectangle(
            [4 * k, 4 * k, 96 * k, 96 * k],
            radius=22 * k,
            fill=BG_DARK,
            outline=BORDER,
            width=max(1, round(2 * k)),
        )

    bars = [
        ((22 * k, 73 * k), (22 * k, 36 * k)),
        ((36 * k, 66 * k), (36 * k, 27 * k)),
        ((50 * k, 77 * k), (50 * k, 47 * k)),
        ((64 * k, 66 * k), (64 * k, 27 * k)),
        ((78 * k, 73 * k), (78 * k, 39 * k)),
    ]
    for p1, p2 in bars:
        _draw_round_cap_line(draw, p1, p2, 6.5 * k, CYAN_PULSE)

    _draw_round_cap_line(draw, (18 * k, 77 * k), (82 * k, 21 * k), 4.5 * k, CYAN_PULSE)
    r_tip = 5.5 * k
    cx, cy = 82 * k, 21 * k
    draw.ellipse([cx - r_tip, cy - r_tip, cx + r_tip, cy + r_tip], fill=CYAN_TIP)

    return img.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    icon_1024 = render_badge(1024, with_background=True)
    icon_256 = icon_1024.resize((256, 256), Image.Resampling.LANCZOS)

    icon_1024.save(OUT_DIR / "music-director-1024.png", format="PNG")
    icon_256.save(OUT_DIR / "music-director-256.png", format="PNG")
    icon_1024.save(
        OUT_DIR / "music-director.ico",
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)],
    )

    # Inno Setup Wizard BMPs (solid RGB 24-bit BMP)
    wiz_large = Image.new("RGB", (164, 314), (11, 13, 18))
    badge_120 = icon_1024.resize((120, 120), Image.Resampling.LANCZOS)
    wiz_large.paste(badge_120, (22, 97), badge_120)
    wiz_large.save(OUT_DIR / "inno-wizard.bmp", format="BMP")

    wiz_small = Image.new("RGB", (55, 58), (11, 13, 18))
    badge_48 = icon_1024.resize((48, 48), Image.Resampling.LANCZOS)
    wiz_small.paste(badge_48, (3, 5), badge_48)
    wiz_small.save(OUT_DIR / "inno-wizard-small.bmp", format="BMP")
    print("Generated PNG, ICO, and Inno Setup BMPs in", OUT_DIR)


if __name__ == "__main__":
    main()
