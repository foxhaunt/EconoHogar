import os

# ── Intenta importar matplotlib; si falla, avisa ──────────────────────────────
try:
    import matplotlib
    matplotlib.use("TkAgg")
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False

# ── Paleta de colores ──────────────────────────────────────────────────────────
BG_DARK      = "#1A1A2E"
BG_CARD      = "#16213E"
BG_CARD2     = "#0F3460"
ACCENT       = "#E94560"
ACCENT2      = "#533483"
TEXT_WHITE   = "#EAEAEA"
TEXT_MUTED   = "#8B8FA8"
SUCCESS      = "#4CAF50"
WARNING      = "#FF9800"
INFO         = "#2196F3"

CATEGORY_COLORS = [
    "#FF6B6B","#4ECDC4","#45B7D1","#96CEB4","#FFEAA7",
    "#DDA0DD","#98D8C8","#F7DC6F","#BB8FCE","#85C1E9",
    "#F0B27A","#82E0AA","#F1948A","#85C1E9","#D7BDE2",
]

CATEGORY_ICONS = {
    "Comida":       "🍽️",
    "Luz":          "💡",
    "Agua":         "💧",
    "Gas":          "🔥",
    "Internet":     "🌐",
    "Teléfono":     "📱",
    "Hipoteca":     "🏠",
    "Alquiler":     "🏘️",
    "Transporte":   "🚗",
    "Salud":        "🏥",
    "Educación":    "📚",
    "Ocio":         "🎭",
    "Ropa":         "👗",
    "Gimnasio":     "💪",
    "Seguros":      "🛡️",
    "Hogar":        "🛋️",
    "Mascotas":     "🐾",
    "Viajes":       "✈️",
    "Otros":        "📦",
}

ICON_EMOJIS = [
    "🍽️","🍕","🍔","🥗","🍱","☕","🍺","🥤",
    "🏠","🛋️","🪴","🔑","🛁","🧹","💡","🪟",
    "🚗","🚌","🚲","✈️","⛽","🛵","🚇","🚕",
    "💊","🏥","🩺","🏋️","🧘","❤️","🌡️","💆",
    "📱","💻","🖥️","📺","🎮","🎧","📷","🔌",
    "💰","💳","🏦","💸","📈","🪙","💎","🎫",
    "📚","🎓","📝","✏️","📖","🔬","🎨","🖊️",
    "🌿","🌊","🔥","💧","🌞","⚡","🌱","🐾",
    "🛡️","🎭","👗","💪","🛒","🎁","📦","🧺",
]

_BBDD_DIR = os.path.join(os.path.expanduser("~"), "bbdd_econhogar")
os.makedirs(_BBDD_DIR, exist_ok=True)

DATA_FILE = os.path.join(os.path.expanduser("~"), ".econohogar_data.json")  # legacy JSON
DB_FILE   = os.path.join(_BBDD_DIR, "econohogar.db")
