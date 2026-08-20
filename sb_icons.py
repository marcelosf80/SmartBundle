# sb_icons.py
import math
from PIL import Image, ImageDraw, ImageTk

def draw_rounded_rect(draw, coords, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = coords
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

def generate_custom_icon(icon_name: str, size: int = 32) -> Image.Image:
    # Renderizamos a 4x para anti-aliasing perfecto
    scale = 4
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    pad = int(4 * scale)
    w = canvas_size - pad * 2
    h = canvas_size - pad * 2
    cx = canvas_size // 2
    cy = canvas_size // 2
    
    cyan = (56, 189, 248, 255)
    purple = (192, 132, 252, 255)
    pink = (244, 114, 182, 255)
    white = (255, 255, 255, 255)
    gold = (251, 191, 36, 255)
    slate = (148, 163, 184, 255)

    if icon_name == "add":
        # Botón '+' con anillo exterior brillante
        draw.ellipse([pad + 4*scale, pad + 4*scale, canvas_size - pad - 4*scale, canvas_size - pad - 4*scale], outline=cyan, width=int(2.5 * scale))
        th = int(2.8 * scale)
        arm = int(7 * scale)
        draw.rectangle([cx - th, cy - arm, cx + th, cy + arm], fill=white)
        draw.rectangle([cx - arm, cy - th, cx + arm, cy + th], fill=white)

    elif icon_name == "compress":
        # Paquete / Caja con cinturón y cierre
        bx1, by1, bx2, by2 = pad + 4*scale, pad + 3*scale, canvas_size - pad - 4*scale, canvas_size - pad - 3*scale
        draw_rounded_rect(draw, [bx1, by1, bx2, by2], int(4 * scale), fill=(30, 27, 75, 255), outline=purple, width=int(2.5 * scale))
        # Cremallera / Cinturón
        bw = int(3 * scale)
        draw.rectangle([cx - bw, by1, cx + bw, by2], fill=cyan)
        draw_rounded_rect(draw, [cx - 5*scale, cy - 4*scale, cx + 5*scale, cy + 4*scale], int(2 * scale), fill=gold, outline=white, width=int(1.5 * scale))

    elif icon_name == "extract":
        # Carpeta abierta con flecha saliente
        fx1, fy1, fx2, fy2 = pad + 3*scale, pad + 7*scale, canvas_size - pad - 3*scale, canvas_size - pad - 3*scale
        draw_rounded_rect(draw, [fx1, fy1, fx2, fy2], int(4 * scale), fill=(24, 28, 50, 255), outline=purple, width=int(2.5 * scale))
        # Pestaña carpeta
        draw_rounded_rect(draw, [fx1, fy1 - 4*scale, fx1 + 10*scale, fy1 + 2*scale], int(2 * scale), fill=purple)
        # Flecha hacia arriba/fuera
        arrow_pts = [(cx, pad + 2*scale), (cx - 6*scale, pad + 9*scale), (cx + 6*scale, pad + 9*scale)]
        draw.polygon(arrow_pts, fill=cyan)
        draw.rectangle([cx - 2.5*scale, pad + 8*scale, cx + 2.5*scale, pad + 15*scale], fill=cyan)

    elif icon_name == "optimize":
        # Sliders / Ecualizador
        for i, offset_x in enumerate([-7*scale, 0, 7*scale]):
            x = cx + offset_x
            draw.line([x, pad + 3*scale, x, canvas_size - pad - 3*scale], fill=(71, 85, 105, 255), width=int(2 * scale))
            slider_y = cy + ((-4 if i == 0 else (4 if i == 1 else -2)) * scale)
            draw_rounded_rect(draw, [x - 3.5*scale, slider_y - 2.5*scale, x + 3.5*scale, slider_y + 2.5*scale], int(1.5 * scale), fill=purple, outline=cyan, width=int(1.2 * scale))

    elif icon_name == "convert":
        # Flechas circulares de sincronización / conversión
        r = int(9 * scale)
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=30, end=150, fill=cyan, width=int(2.5 * scale))
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=210, end=330, fill=purple, width=int(2.5 * scale))
        # Puntas flecha
        draw.polygon([(cx - r + 3*scale, cy + 4*scale), (cx - r - 4*scale, cy + 6*scale), (cx - r + 1*scale, cy - 2*scale)], fill=cyan)
        draw.polygon([(cx + r - 3*scale, cy - 4*scale), (cx + r + 4*scale, cy - 6*scale), (cx + r - 1*scale, cy + 2*scale)], fill=purple)

    elif icon_name == "info":
        # Círculo 'i'
        draw.ellipse([pad + 3*scale, pad + 3*scale, canvas_size - pad - 3*scale, canvas_size - pad - 3*scale], outline=purple, width=int(2.5 * scale))
        # Punto 'i'
        draw.ellipse([cx - 2*scale, pad + 7*scale, cx + 2*scale, pad + 11*scale], fill=cyan)
        # Barra 'i'
        draw_rounded_rect(draw, [cx - 2*scale, pad + 13*scale, cx + 2*scale, canvas_size - pad - 7*scale], int(1.5 * scale), fill=white)

    elif icon_name == "settings":
        # Engranaje
        r_out = int(10 * scale)
        r_in = int(5 * scale)
        for deg in range(0, 360, 45):
            rad = math.radians(deg)
            tx = cx + r_out * math.cos(rad)
            ty = cy + r_out * math.sin(rad)
            draw_rounded_rect(draw, [tx - 2*scale, ty - 2*scale, tx + 2*scale, ty + 2*scale], int(1 * scale), fill=purple)
        draw.ellipse([cx - r_out + 2*scale, cy - r_out + 2*scale, cx + r_out - 2*scale, cy + r_out - 2*scale], fill=(30, 27, 75, 255), outline=purple, width=int(2 * scale))
        draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(18, 21, 38, 255), outline=cyan, width=int(1.5 * scale))

    # Iconos para archivos en la tabla
    elif icon_name == "type_folder":
        # Carpeta dorada
        fx1, fy1, fx2, fy2 = pad + 2*scale, pad + 6*scale, canvas_size - pad - 2*scale, canvas_size - pad - 4*scale
        draw_rounded_rect(draw, [fx1, fy1 - 3*scale, fx1 + 10*scale, fy1 + 2*scale], int(2 * scale), fill=(217, 119, 6, 255))
        draw_rounded_rect(draw, [fx1, fy1, fx2, fy2], int(3 * scale), fill=gold, outline=(254, 243, 199, 255), width=int(1 * scale))

    elif icon_name == "type_archive":
        # Badge púrpura archivador
        bx1, by1, bx2, by2 = pad + 4*scale, pad + 3*scale, canvas_size - pad - 4*scale, canvas_size - pad - 3*scale
        draw_rounded_rect(draw, [bx1, by1, bx2, by2], int(3 * scale), fill=(147, 51, 234, 255), outline=white, width=int(1 * scale))
        draw.rectangle([cx - 2*scale, by1, cx + 2*scale, by2], fill=gold)

    elif icon_name == "type_binary":
        # Badge ejecutable / DLL
        bx1, by1, bx2, by2 = pad + 4*scale, pad + 3*scale, canvas_size - pad - 4*scale, canvas_size - pad - 3*scale
        draw_rounded_rect(draw, [bx1, by1, bx2, by2], int(3 * scale), fill=(37, 99, 235, 255), outline=cyan, width=int(1 * scale))
        draw.polygon([(cx - 3*scale, cy - 4*scale), (cx + 4*scale, cy), (cx - 3*scale, cy + 4*scale)], fill=white)

    elif icon_name == "type_code":
        # Badge código
        bx1, by1, bx2, by2 = pad + 4*scale, pad + 3*scale, canvas_size - pad - 4*scale, canvas_size - pad - 3*scale
        draw_rounded_rect(draw, [bx1, by1, bx2, by2], int(3 * scale), fill=(13, 148, 136, 255), outline=white, width=int(1 * scale))
        # < / >
        draw.line([cx - 5*scale, cy, cx - 2*scale, cy - 4*scale], fill=white, width=int(1.5 * scale))
        draw.line([cx - 5*scale, cy, cx - 2*scale, cy + 4*scale], fill=white, width=int(1.5 * scale))
        draw.line([cx + 5*scale, cy, cx + 2*scale, cy - 4*scale], fill=white, width=int(1.5 * scale))
        draw.line([cx + 5*scale, cy, cx + 2*scale, cy + 4*scale], fill=white, width=int(1.5 * scale))

    else: # type_file
        # Documento estándar
        fx1, fy1, fx2, fy2 = pad + 5*scale, pad + 3*scale, canvas_size - pad - 5*scale, canvas_size - pad - 3*scale
        draw_rounded_rect(draw, [fx1, fy1, fx2, fy2], int(2 * scale), fill=(71, 85, 105, 255), outline=white, width=int(1 * scale))
        # Líneas de texto en documento
        for ly in [cy - 3*scale, cy, cy + 3*scale]:
            draw.line([fx1 + 3*scale, ly, fx2 - 3*scale, ly], fill=(226, 232, 240, 255), width=int(1.2 * scale))

    # Reducir con filtro Lanczos para máxima nitidez
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
