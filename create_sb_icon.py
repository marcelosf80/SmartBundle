# create_sb_icon.py
import math
from PIL import Image, ImageDraw

def create_smartbundle_icon(path="app_icon.ico"):
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    
    for size in sizes:
        w, h = size
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Fondo redondeado / Cubo estilizado con degradado azul-violeta a cyan
        margin = max(1, int(w * 0.06))
        rect = [margin, margin, w - margin, h - margin]
        corner_radius = max(2, int(w * 0.18))
        
        # Base oscura con gradiente de borde
        draw.rounded_rectangle(rect, corner_radius, fill=(24, 26, 38, 255), outline=(99, 102, 241, 255), width=max(1, int(w * 0.05)))
        
        # Correas / Capas de compresión (Estilo Archivo / Bundle moderno)
        # Capa superior (cyan)
        l1_top = int(h * 0.22)
        l1_h = int(h * 0.15)
        draw.rounded_rectangle([int(w * 0.18), l1_top, int(w * 0.82), l1_top + l1_h], max(1, int(w * 0.04)), fill=(56, 189, 248, 255))
        
        # Capa media (indigo / violeta)
        l2_top = int(h * 0.42)
        l2_h = int(h * 0.15)
        draw.rounded_rectangle([int(w * 0.18), l2_top, int(w * 0.82), l2_top + l2_h], max(1, int(w * 0.04)), fill=(129, 140, 248, 255))

        # Capa inferior (púrpura)
        l3_top = int(h * 0.62)
        l3_h = int(h * 0.15)
        draw.rounded_rectangle([int(w * 0.18), l3_top, int(w * 0.82), l3_top + l3_h], max(1, int(w * 0.04)), fill=(168, 85, 247, 255))

        # Broche / Hebilla central o Relámpago de velocidad
        # Cinturón vertical central
        belt_w = max(2, int(w * 0.16))
        belt_x1 = int(w * 0.5) - belt_w // 2
        belt_x2 = belt_x1 + belt_w
        draw.rectangle([belt_x1, int(h * 0.18), belt_x2, int(h * 0.82)], fill=(30, 41, 59, 230), outline=(251, 191, 36, 255), width=max(1, int(w * 0.03)))
        
        # Cierre dorado / Hebilla
        buckle_size = max(4, int(w * 0.22))
        bx1 = int(w * 0.5) - buckle_size // 2
        by1 = int(h * 0.5) - buckle_size // 2
        draw.rounded_rectangle([bx1, by1, bx1 + buckle_size, by1 + buckle_size], max(1, int(w * 0.04)), fill=(245, 158, 11, 255), outline=(254, 240, 138, 255), width=max(1, int(w * 0.03)))
        
        images.append(img)
        
    images[0].save(path, format="ICO", sizes=sizes, append_images=images[1:])
    print(f"[OK] Icono generado exitosamente en {path}")

if __name__ == "__main__":
    create_smartbundle_icon("c:/Users/marce/OneDrive/Desktop/SmartBundle/app_icon.ico")
