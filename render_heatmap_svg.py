#!/usr/bin/env python3
"""
prep_photo.py — deja una foto lista para convertirla en ASCII.

    python scripts/prep_photo.py source-photo.jpg

Tres pasos, en este orden:
  1. rembg quita el fondo, para que solo quede el sujeto.
  2. CLAHE (OpenCV) sube el contraste LOCAL: una cara plana gana luces y
     sombras reales en vez de convertirse en un borrón oscuro.
  3. Composita sobre blanco puro, para que el fondo caiga en el extremo
     vacío de la rampa ASCII (blanco -> espacios).

Salida: source-prepped.png (escala de grises). Solo hay que ejecutarlo
cuando cambias de foto; la automatización diaria no lo usa.
"""

import sys
import pathlib

import numpy as np
from PIL import Image

import config

OUT = pathlib.Path("source-prepped.png")

# Cuánto sube el contraste local. Súbelo si la cara sale plana, bájalo si
# aparece "ruido" o grano en las mejillas.
CLAHE_CLIP = 2.6
CLAHE_GRID = 8

# Suaviza el gris final: <1.0 aclara, >1.0 oscurece.
GAMMA = 0.95


def remove_background(img: Image.Image) -> Image.Image:
    """Devuelve RGBA con el fondo transparente. Si rembg no está, avisa."""
    try:
        from rembg import remove
    except ImportError:
        print("! rembg no está instalado; sigo sin recortar el fondo.")
        print("  pip install rembg    (o recorta la foto tú mismo)")
        return img.convert("RGBA")
    print("· quitando el fondo con rembg (la primera vez baja el modelo)…")
    return remove(img.convert("RGBA"))


def composite_on_white(img: Image.Image) -> Image.Image:
    """Pega el sujeto sobre blanco puro y pasa a escala de grises."""
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white.alpha_composite(img)
    return white.convert("L")


def boost_local_contrast(gray: Image.Image) -> Image.Image:
    """CLAHE si hay OpenCV; si no, un estirado de histograma decente."""
    arr = np.array(gray)
    try:
        import cv2
        clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP,
                                tileGridSize=(CLAHE_GRID, CLAHE_GRID))
        arr = clahe.apply(arr)
    except ImportError:
        print("! opencv-python no está instalado; uso un estirado simple.")
        lo, hi = np.percentile(arr, (2, 98))
        if hi > lo:
            arr = np.clip((arr - lo) * 255.0 / (hi - lo), 0, 255)
    arr = arr.astype(np.float32) / 255.0
    arr = np.power(arr, GAMMA) * 255.0
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="L")


def lift_shadows(gray: Image.Image) -> Image.Image:
    """
    Sube el suelo de negro SOLO en el sujeto. Sin esto, una chaqueta oscura
    o el pelo se convierten en un bloque macizo de '@' que tapa la cara.
    """
    lift = getattr(config, "SHADOW_LIFT", 0.0)
    if lift <= 0:
        return gray
    arr = np.array(gray, dtype=np.float32) / 255.0
    subject = arr < 0.99                       # el fondo blanco no se toca
    arr[subject] = lift + arr[subject] * (1.0 - lift)
    return Image.fromarray((arr * 255).astype(np.uint8), mode="L")


def crop(img: Image.Image) -> Image.Image:
    """Recorte final en fracciones, definido en config.CROP."""
    box = getattr(config, "CROP", None)
    if not box:
        return img
    l, t, r, b = box
    return img.crop((int(l * img.width), int(t * img.height),
                     int(r * img.width), int(b * img.height)))


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("uso: python scripts/prep_photo.py <foto.jpg>")

    src = pathlib.Path(sys.argv[1])
    if not src.exists():
        sys.exit(f"no encuentro {src}")

    img = Image.open(src)
    # Trabajar grande da mejor detalle al reducir a caracteres después.
    if img.width > 1400:
        img = img.resize((1400, round(img.height * 1400 / img.width)),
                         Image.LANCZOS)

    cut = remove_background(img)
    gray = composite_on_white(cut)
    final = crop(lift_shadows(boost_local_contrast(gray)))

    # El fondo debe quedar blanco del todo: cualquier gris claro residual
    # se fuerza a 255 para que se convierta en espacios, no en puntos.
    arr = np.array(final)
    arr[arr > 244] = 255
    Image.fromarray(arr, mode="L").save(OUT)

    print(f"✓ {OUT}  ({final.width}×{final.height})")
    print("  Ábrelo. Si la cara se ve gris y plana, sube CLAHE_CLIP.")
    print("  Si la ropa sale como un bloque negro, sube SHADOW_LIFT en config.")
    print("  Ahora: python scripts/make_ascii_svg.py")


if __name__ == "__main__":
    main()
