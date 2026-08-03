"""
ÚNICO ARCHIVO QUE DEBES EDITAR.

Cambia tu usuario y el contenido de la tarjeta aquí; los demás scripts leen
de este módulo.
"""

# ---------------------------------------------------------------- identidad
USERNAME = "maikxl0"               # tu usuario EXACTO de GitHub
PROMPT_USER = "maikxl0"            # nombre corto para los prompts falsos
CARD_TITLE = "maikxl0@github"      # cabecera de la tarjeta neofetch

# ------------------------------------------------------- tarjeta "neofetch"
# Cada fila es (etiqueta, valor). El valor puede ser un string o una lista
# de strings (se imprime en varias líneas bajo la misma etiqueta).
#
# Sacado de tus repos públicos. Ajusta lo que no cuadre.
CARD_ROWS = [
    ("Role",    "Full-Stack Developer"),
    ("Doing",   "Showcasing my work and projects here"),
    ("Stack",   ["Web   ·  TypeScript · JavaScript · Node",
                 "ML    ·  Python · YOLO · Computer Vision"]),
    ("Recent",  ["Novahabitat", "Restaurante la Terraza"]),
    ("Open to", "Collaboration and new projects"),
    ("Profile", "github.com/maikxl0"),
]

# Frase corta bajo la cabecera (pon "" para omitirla)
CARD_TAGLINE = "welcome to my repository"

# ------------------------------------------------------------------ retrato
ASCII_COLS = 100                   # ancho del retrato en caracteres
RAMP = " .`:-=+*cs#%@"             # claro (disperso) -> oscuro (denso)

# Recorte final, en fracciones (izq, arriba, der, abajo). None = sin recorte.
# Aquí corta bajo los hombros: si no, el traje oscuro se come medio retrato.
CROP = (0.04, 0.00, 0.96, 0.78)

# Levanta los negros para que la ropa oscura no salga como un bloque sólido.
# 0.0 = sin tocar · 0.20 = lo que usamos · 0.35 = muy lavado
SHADOW_LIFT = 0.06

# ------------------------------------------------------------------ paleta
# Verde estilo GitHub. El nivel 5 es un extremo neón propio (no existe en
# los datos de GitHub, lo derivamos de tus mejores días).
PALETTE = ["#161b22", "#0e4429", "#006d32",
           "#26a641", "#39d353", "#69f0a0"]

BG = "#0d1117"                     # fondo tipo terminal oscura
FG = "#c9d1d9"                     # texto principal
DIM = "#8b949e"                    # texto secundario
ACCENT = "#39d353"                 # acento verde

MONO = "ui-monospace,'SFMono-Regular','JetBrains Mono','Fira Code',Menlo,Consolas,monospace"
