# sb_icons.py
import math
from PIL import Image, ImageDraw, ImageTk

def draw_rounded_rect(draw, coords, radius, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = coords
    # Asegurar que x0 <= x1 y y0 <= y1
    if x0 > x1: x0, x1 = x1, x0
    if y0 > y1: y0, y1 = y1, y0
    radius = max(1, min(radius, int(abs(x1 - x0) / 2), int(abs(y1 - y0) / 2)))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def generate_custom_icon(icon_name: str, size: int = 32) -> Image.Image:
    scale = 4
    cs = size * scale  # Canvas size
    img = Image.new("RGBA", (cs, cs), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx = cs / 2.0
    cy = cs / 2.0
    
    cyan = (56, 189, 248, 255)
    purple = (192, 132, 252, 255)
    pink = (244, 114, 182, 255)
    white = (255, 255, 255, 255)
    gold = (251, 191, 36, 255)
    dark_bg = (30, 27, 75, 255)
    line_w = max(1, int(1.8 * scale))

    if icon_name == "add":
        # Botón '+' con círculo exterior
        r = cs * 0.38
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=cyan, width=line_w)
        arm = cs * 0.22
        th = max(1.0, 1.8 * scale)
        draw.rectangle([cx - th, cy - arm, cx + th, cy + arm], fill=white)
        draw.rectangle([cx - arm, cy - th, cx + arm, cy + th], fill=white)

    elif icon_name == "compress":
        # Caja con cinturón y hebilla
        x0, y0, x1, y1 = cs * 0.16, cs * 0.18, cs * 0.84, cs * 0.82
        draw_rounded_rect(draw, [x0, y0, x1, y1], int(3 * scale), fill=dark_bg, outline=purple, width=line_w)
        bw = cs * 0.10
        draw.rectangle([cx - bw/2, y0, cx + bw/2, y1], fill=cyan)
        hw = cs * 0.20
        hh = cs * 0.16
        draw_rounded_rect(draw, [cx - hw/2, cy - hh/2, cx + hw/2, cy + hh/2], int(2 * scale), fill=gold, outline=white, width=1)

    elif icon_name == "extract":
        # Carpeta abierta con flecha saliente
        x0, y0, x1, y1 = cs * 0.15, cs * 0.35, cs * 0.85, cs * 0.85
        draw_rounded_rect(draw, [x0, y0, x1, y1], int(3 * scale), fill=dark_bg, outline=purple, width=line_w)
        draw_rounded_rect(draw, [x0, cs * 0.25, x0 + cs * 0.32, y0 + 2], int(2 * scale), fill=purple)
        # Flecha hacia arriba
        arrow_pts = [(cx, cs * 0.10), (cx - cs * 0.22, cs * 0.32), (cx + cs * 0.22, cs * 0.32)]
        draw.polygon(arrow_pts, fill=cyan)
        draw.rectangle([cx - cs * 0.08, cs * 0.28, cx + cs * 0.08, cs * 0.52], fill=cyan)

    elif icon_name == "optimize":
        # Sliders ecualizador
        offsets = [-cs * 0.24, 0, cs * 0.24]
        for i, off in enumerate(offsets):
            x = cx + off
            draw.line([x, cs * 0.18, x, cs * 0.82], fill=(71, 85, 105, 255), width=line_w)
            sy = cy + ((-cs * 0.15 if i == 0 else (cs * 0.15 if i == 1 else -cs * 0.05)))
            kw = cs * 0.18
            kh = cs * 0.12
            draw_rounded_rect(draw, [x - kw/2, sy - kh/2, x + kw/2, sy + kh/2], int(2 * scale), fill=purple, outline=cyan, width=1)

    elif icon_name == "convert":
        # Flechas de sincronización
        r = cs * 0.32
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=30, end=150, fill=cyan, width=line_w)
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=210, end=330, fill=purple, width=line_w)
        # Flechas puntas
        draw.polygon([(cx - r + cs * 0.10, cy + cs * 0.10), (cx - r - cs * 0.12, cy + cs * 0.18), (cx - r + cs * 0.02, cy - cs * 0.08)], fill=cyan)
        draw.polygon([(cx + r - cs * 0.10, cy - cs * 0.10), (cx + r + cs * 0.12, cy - cs * 0.18), (cx + r - cs * 0.02, cy + cs * 0.08)], fill=purple)

    elif icon_name == "info":
        # Círculo información
        r = cs * 0.38
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=purple, width=line_w)
        # Punto 'i'
        pr = cs * 0.07
        draw.ellipse([cx - pr, cy - cs * 0.24 - pr, cx + pr, cy - cs * 0.24 + pr], fill=cyan)
        # Barra 'i'
        draw_rounded_rect(draw, [cx - cs * 0.06, cy - cs * 0.08, cx + cs * 0.06, cy + cs * 0.24], int(1.5 * scale), fill=white)

    elif icon_name == "settings":
        # Engranaje
        r_out = cs * 0.36
        r_in = cs * 0.16
        for deg in range(0, 360, 45):
            rad = math.radians(deg)
            tx = cx + r_out * math.cos(rad)
            ty = cy + r_out * math.sin(rad)
            tw = cs * 0.10
            draw_rounded_rect(draw, [tx - tw/2, ty - tw/2, tx + tw/2, ty + tw/2], int(1.5 * scale), fill=purple)
        draw.ellipse([cx - r_out + cs*0.06, cy - r_out + cs*0.06, cx + r_out - cs*0.06, cy + r_out - cs*0.06], fill=dark_bg, outline=purple, width=line_w)
        draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(18, 21, 38, 255), outline=cyan, width=line_w)

    # Iconos para archivos en la tabla
    elif icon_name == "type_folder":
        # Carpeta dorada
        x0, y0, x1, y1 = cs * 0.12, cs * 0.28, cs * 0.88, cs * 0.82
        draw_rounded_rect(draw, [x0, cs * 0.18, x0 + cs * 0.35, y0 + 2], int(2 * scale), fill=(217, 119, 6, 255))
        draw_rounded_rect(draw, [x0, y0, x1, y1], int(3 * scale), fill=gold, outline=(254, 243, 199, 255), width=1)

    elif icon_name == "type_archive":
        x0, y0, x1, y1 = cs * 0.15, cs * 0.15, cs * 0.85, cs * 0.85
        draw_rounded_rect(draw, [x0, y0, x1, y1], int(3 * scale), fill=(147, 51, 234, 255), outline=white, width=1)
        draw.rectangle([cx - cs * 0.08, y0, cx + cs * 0.08, y1], fill=gold)

    elif icon_name == "type_binary":
        x0, y0, x1, y1 = cs * 0.15, cs * 0.15, cs * 0.85, cs * 0.85
        draw_rounded_rect(draw, [x0, y0, x1, y1], int(3 * scale), fill=(37, 99, 235, 255), outline=cyan, width=1)
        draw.polygon([(cx - cs * 0.12, cy - cs * 0.16), (cx + cs * 0.16, cy), (cx - cs * 0.12, cy + cs * 0.16)], fill=white)

    elif icon_name == "type_code":
        x0, y0, x1, y1 = cs * 0.15, cs * 0.15, cs * 0.85, cs * 0.85
        draw_rounded_rect(draw, [x0, y0, x1, y1], int(3 * scale), fill=(13, 148, 136, 255), outline=white, width=1)
        draw.line([cx - cs * 0.18, cy, cx - cs * 0.06, cy - cs * 0.14], fill=white, width=int(1.5 * scale))
        draw.line([cx - cs * 0.18, cy, cx - cs * 0.06, cy + cs * 0.14], fill=white, width=int(1.5 * scale))
        draw.line([cx + cs * 0.18, cy, cx + cs * 0.06, cy - cs * 0.14], fill=white, width=int(1.5 * scale))
        draw.line([cx + cs * 0.18, cy, cx + cs * 0.06, cy + cs * 0.14], fill=white, width=int(1.5 * scale))

    else: # type_file
        x0, y0, x1, y1 = cs * 0.18, cs * 0.12, cs * 0.82, cs * 0.88
        draw_rounded_rect(draw, [x0, y0, x1, y1], int(2 * scale), fill=(71, 85, 105, 255), outline=white, width=1)
        for ly in [cy - cs * 0.12, cy, cy + cs * 0.12]:
            draw.line([x0 + cs * 0.12, ly, x1 - cs * 0.12, ly], fill=(226, 232, 240, 255), width=int(1.2 * scale))

    return img.resize((size, size), Image.Resampling.LANCZOS)

class IconRegistry:
    _cache = {}

    @classmethod
    def get_tk_icon(cls, name: str, size: int = 24) -> ImageTk.PhotoImage:
        key = f"{name}_{size}"
        if key not in cls._cache:
            img = generate_custom_icon(name, size)
            cls._cache[key] = ImageTk.PhotoImage(img)
        return cls._cache[key]
