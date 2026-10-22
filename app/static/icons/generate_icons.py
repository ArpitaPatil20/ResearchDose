"""
Generate high-resolution, crisp PWA PNG icons and favicons for ResearchDose.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ICONS_DIR = Path("app/static/icons")
ICONS_DIR.mkdir(parents=True, exist_ok=True)


def draw_icon(size: int, maskable: bool = False, rounded: bool = True) -> Image.Image:
    # Create image with RGBA
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Padding for maskable vs standard
    # Maskable icons need safe zone: center 80%
    pad = int(size * 0.1) if maskable else int(size * 0.04)
    corner_radius = 0 if maskable else int(size * 0.22)

    # Background gradient
    # Deep midnight gradient
    bg_box = [pad, pad, size - pad, size - pad] if not maskable else [0, 0, size, size]
    
    if maskable:
        draw.rectangle([0, 0, size, size], fill=(10, 15, 29, 255))
    else:
        draw.rounded_rectangle(bg_box, radius=corner_radius, fill=(10, 15, 29, 255), outline=(56, 189, 248, 120), width=max(2, int(size * 0.015)))

    # Subtle inner glow circle
    cx, cy = size // 2, int(size * 0.48)
    glow_r = int(size * 0.35)
    draw.ellipse([cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r], fill=(13, 110, 253, 35))

    # Draw Laboratory Flask / Dose Icon
    scale = size / 512.0
    
    # Flask coordinates scaled
    # Top neck
    lip_w = int(50 * scale)
    lip_y = int(120 * scale)
    neck_w = int(32 * scale)
    neck_h = int(60 * scale)
    draw.line([cx - lip_w, lip_y, cx + lip_w, lip_y], fill=(56, 189, 248, 255), width=max(3, int(16 * scale)))
    
    # Neck sides
    draw.line([cx - neck_w, lip_y, cx - neck_w, lip_y + neck_h], fill=(13, 110, 253, 255), width=max(2, int(14 * scale)))
    draw.line([cx + neck_w, lip_y, cx + neck_w, lip_y + neck_h], fill=(13, 110, 253, 255), width=max(2, int(14 * scale)))

    # Flask body (trapezoid)
    base_w = int(140 * scale)
    base_y = int(340 * scale)
    
    flask_points = [
        (cx - neck_w, lip_y + neck_h),
        (cx + neck_w, lip_y + neck_h),
        (cx + base_w, base_y),
        (cx - base_w, base_y)
    ]
    
    # Liquid in flask (green emerald / cyan gradient)
    liquid_y = int(260 * scale)
    liquid_points = [
        (cx - int(95 * scale), liquid_y),
        (cx + int(95 * scale), liquid_y),
        (cx + int(135 * scale), base_y - int(6 * scale)),
        (cx - int(135 * scale), base_y - int(6 * scale))
    ]
    draw.polygon(liquid_points, fill=(16, 185, 129, 210))

    # Flask outline
    draw.line([(cx - neck_w, lip_y + neck_h), (cx - base_w, base_y)], fill=(56, 189, 248, 255), width=max(3, int(14 * scale)))
    draw.line([(cx + neck_w, lip_y + neck_h), (cx + base_w, base_y)], fill=(56, 189, 248, 255), width=max(3, int(14 * scale)))
    draw.line([(cx - base_w, base_y), (cx + base_w, base_y)], fill=(56, 189, 248, 255), width=max(3, int(16 * scale)))

    # Graduation marks
    for offset_y, mark_len in [(180, 24), (215, 32), (250, 24)]:
        y = int(offset_y * scale)
        l = int(mark_len * scale)
        draw.line([cx - int(20 * scale), y, cx - int(20 * scale) + l, y], fill=(255, 255, 255, 220), width=max(2, int(6 * scale)))

    # Bubbles
    bubble_coords = [(cx - int(30 * scale), int(300 * scale), int(10 * scale)),
                     (cx + int(20 * scale), int(285 * scale), int(14 * scale)),
                     (cx + int(45 * scale), int(250 * scale), int(8 * scale))]
    for bx, by, br in bubble_coords:
        draw.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 255, 255, 200))

    # Rx badge at bottom right
    rx_cx = int(350 * scale)
    rx_cy = int(350 * scale)
    rx_r = int(55 * scale)
    draw.ellipse([rx_cx - rx_r, rx_cy - rx_r, rx_cx + rx_r, rx_cy + rx_r], fill=(13, 110, 253, 255), outline=(56, 189, 248, 255), width=max(2, int(6 * scale)))
    
    # Try loading a font or draw simple Rx
    try:
        font = ImageFont.truetype("arial.ttf", int(50 * scale))
        draw.text((rx_cx, rx_cy), "Rx", fill=(255, 255, 255, 255), font=font, anchor="mm")
    except Exception:
        # Fallback simple lines
        draw.text((rx_cx - int(15 * scale), rx_cy - int(20 * scale)), "Rx", fill=(255, 255, 255, 255))

    return img


def main():
    print("Generating PWA icons...")
    
    # 512x512 standard
    img_512 = draw_icon(512, maskable=False)
    img_512.save(ICONS_DIR / "icon-512x512.png", "PNG")
    print("Saved icon-512x512.png")

    # 512x512 maskable (for adaptive Android icons)
    img_maskable = draw_icon(512, maskable=True)
    img_maskable.save(ICONS_DIR / "icon-maskable-512x512.png", "PNG")
    print("Saved icon-maskable-512x512.png")

    # 192x192 standard
    img_192 = draw_icon(192, maskable=False)
    img_192.save(ICONS_DIR / "icon-192x192.png", "PNG")
    print("Saved icon-192x192.png")

    # Apple Touch Icon 180x180
    img_180 = draw_icon(180, maskable=False)
    img_180.save(ICONS_DIR / "apple-touch-icon.png", "PNG")
    print("Saved apple-touch-icon.png")

    # 32x32 favicon
    img_32 = draw_icon(32, maskable=False)
    img_32.save(ICONS_DIR / "favicon-32x32.png", "PNG")
    
    # Favicon.ico (contains 16, 32, 48)
    img_48 = draw_icon(48, maskable=False)
    img_16 = draw_icon(16, maskable=False)
    img_48.save(
        ICONS_DIR / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=[img_32, img_16]
    )
    print("Saved favicon.ico")
    print("All PWA icons successfully generated!")


if __name__ == "__main__":
    main()
