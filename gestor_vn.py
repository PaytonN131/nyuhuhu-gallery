"""
Nyuhuhu Gallery 4.4  -  Biblioteca de capturas de novelas visuales
Requisitos:  python -m pip install PySide6 Pillow
Ejecutar:    python gestor_vn.py
"""
import sys
import os
import re
import random
import zlib
import sqlite3
import hashlib
import shutil
import time
import html
import json
import datetime
import threading
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from math import ceil, sin, cos, pi, log2
from pathlib import Path
from collections import OrderedDict

from PIL import Image
from PySide6.QtCore import (
    Qt, QSize, QRectF, QPointF, QPoint, QRect, Signal, QTimer, QUrl, QVariantAnimation,
    QEasingCurve, QEvent, QPropertyAnimation, QMimeData, QObject, QDate,
    QRunnable, QThreadPool, QEventLoop, QProcess,
    qInstallMessageHandler, QtMsgType
)
from PySide6.QtGui import (
    QPixmap, QImage, QImageReader, QKeySequence, QShortcut, QPainter, QColor,
    QPainterPath, QFont, QIcon, QLinearGradient, QRadialGradient, QBrush,
    QPen, QFontDatabase, QFontMetrics, QPolygonF, QCursor, QDrag, QPalette, QIntValidator, QDesktopServices
)
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFileDialog, QMessageBox, QInputDialog, QComboBox, QFrame, QLineEdit,
    QTabWidget, QSlider, QSplitter, QAbstractItemView, QMenu, QCheckBox,
    QProgressDialog, QFormLayout, QFontComboBox, QSpinBox,
    QStyledItemDelegate, QStyle, QStackedWidget, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QSizePolicy,
    QGraphicsOpacityEffect, QColorDialog, QPlainTextEdit, QGridLayout, QCompleter,
    QDateEdit, QProgressBar, QSplitterHandle, QButtonGroup, QDoubleSpinBox,
    QCalendarWidget, QWidgetAction
)

# =========================================================
# CONFIGURACION
# =========================================================

def recurso(nombre):
    """Ruta de un archivo que viaja con el programa (funciona en .py y dentro del .exe)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / nombre


def _primero_existente(*rutas):
    for r in rutas:
        if Path(r).exists():
            return str(r)
    return str(rutas[0])


# Tu biblioteca de siempre si existe; si no (por ejemplo en el PC de un amigo),
# se crea en «Documentos/NyuhuhuGallery» (si ya tenías «YumeGallery», se sigue usando esa).
_ROOT_PROPIO = Path(r"D:\VN_Extraidos")
_DOC_VIEJO = Path.home() / "Documents" / "YumeGallery"
_DOC_NUEVO = Path.home() / "Documents" / "NyuhuhuGallery"
if _ROOT_PROPIO.exists():
    ROOT = _ROOT_PROPIO
elif _DOC_VIEJO.exists() and not _DOC_NUEVO.exists():
    ROOT = _DOC_VIEJO
else:
    ROOT = _DOC_NUEVO
DB_PATH = ROOT / "biblioteca.db"
ASSETS = ROOT / "_assets"

ICONO_APP = recurso("icono.ico")

TODAS_NOVELAS = "★ Todas las novelas"
CATEGORIAS = ["CG normal", "CG H", "SD", "No-CG"]
CAT_DEFECTO = "CG normal"
EXTENSIONES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
EXT_AUDIO = "*.mp3 *.wav *.ogg *.flac *.m4a"
EXT_VIDEO = "*.mp4 *.mkv *.webm *.mov *.avi *.m4v"
OPENING_VOLUMEN = 25           # volumen inicial del opening (la cuarta parte)
MUSICA_VOLUMEN = 25            # volumen inicial de la música al abrir la aplicación
OPENING_PAUSA_MUSICA = True    # el opening y la música no suenan a la vez
FILTRO_IMG = "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff)"

MINIATURAS = ASSETS / "miniaturas"        # copias reducidas para abrir las pantallas al instante
for _p in (ROOT, ASSETS / "portadas", ASSETS / "heroinas", ASSETS / "ui", MINIATURAS):
    _p.mkdir(parents=True, exist_ok=True)

ACENTOS = {
    "Sakura":  ("#ff9ec7", "#c4a1ff"),
    "Lavanda": ("#c3a6ff", "#8fd3ff"),
    "Menta":   ("#7fe0bb", "#a6c8ff"),
    "Cielo":   ("#8fd0ff", "#ffb3d9"),
    "Durazno": ("#ffb58f", "#ff9ec7"),
    "Limón":   ("#ffe08a", "#ffa6d0"),
}

BASES = {
    "Oscuro": dict(
        bg="#1b1626", panel="rgba(44,36,66,215)", panel_solid="#2c2442",
        input="#251e38", text="#f6efff", muted="#b9acd6",
        border="#52446f", card="#2f2748"),
    "Claro": dict(
        bg="#fff3f9", panel="rgba(255,255,255,220)", panel_solid="#ffffff",
        input="#ffffff", text="#4b3a5e", muted="#8d7aa3",
        border="#f0cde3", card="#ffffff"),
}

TEXTO_SOBRE_ACENTO = "#3b2a4f"


class Tema:
    """Estado visual global, editable desde Ajustes."""
    nombre = "Oscuro"
    acento = "Sakura"
    fuente = "Segoe UI"
    tam = 10
    radio = 14
    anim = False          # MODO LIGERO: sin animaciones (más fluido). Los brillos son estáticos.
    fondo = ""
    fondo_vis = 35
    cabecera = ""
    mascota = ""
    color1 = "#ff9ec7"
    color2 = "#c4a1ff"
    panel_op = 85
    ratio_tarjeta = 138
    titulo = "✿ NYUHUHU GALLERY"
    titulo_biblioteca = "Mi biblioteca"
    particulas = "Pétalos"
    cantidad = 24
    vel = 100
    clic_efecto = True
    alto_cabecera = 60
    acento_portada = True    # dentro de una novela, el color sale de su portada
    acento_juego = None      # (color1, color2) mientras estás dentro de una novela

    @classmethod
    def c(cls, clave):
        return BASES[cls.nombre][clave]

    @classmethod
    def a1(cls):
        if cls.acento_juego:
            return cls.acento_juego[0]
        if cls.acento == "Personalizado":
            return cls.color1
        return ACENTOS[cls.acento][0]

    @classmethod
    def a2(cls):
        if cls.acento_juego:
            return cls.acento_juego[1]
        if cls.acento == "Personalizado":
            return cls.color2
        return ACENTOS[cls.acento][1]


AJUSTES = {
    "titulo_biblioteca": "titulo_biblioteca",
    "tema": "nombre", "acento": "acento", "fuente": "fuente", "tam": "tam",
    "radio": "radio", "anim": "anim", "fondo": "fondo",
    "fondo_vis": "fondo_vis", "cabecera": "cabecera", "mascota": "mascota",
    "color1": "color1", "color2": "color2", "panel_op": "panel_op",
    "ratio_tarjeta": "ratio_tarjeta", "titulo": "titulo",
    "particulas": "particulas", "cantidad": "cantidad", "vel": "vel",
    "clic_efecto": "clic_efecto", "alto_cabecera": "alto_cabecera",
}




def construir_estilo():
    pc = QColor(BASES[Tema.nombre]["panel_solid"])
    panel = f"rgba({pc.red()},{pc.green()},{pc.blue()},{int(Tema.panel_op * 2.55)})"

    def c(k):
        return panel if k == "panel" else Tema.c(k)

    a1, a2 = Tema.a1(), Tema.a2()
    r, s, f = Tema.radio, Tema.tam, Tema.fuente
    rs = max(4, int(r * 0.7))
    _ps = QColor(BASES[Tema.nombre]["panel_solid"])
    bar_a = mezclar(_ps, QColor(a1), 0.16).name()
    bar_b = mezclar(_ps, QColor(a2), 0.16).name()
    return f"""
* {{ color: {c('text')}; }}
QMainWindow, QDialog {{ background: {c('bg')}; }}
QLabel {{ background: transparent; }}
QLabel#logo {{ font-size: {s + 8}pt; font-weight: 800; color: {a1}; }}
QLabel#heading {{ font-size: {s + 6}pt; font-weight: 700; }}
QLabel#muted {{ color: {c('muted')}; }}
QFrame#panel, QFrame#reproductor {{
    background: {c('panel')}; border: 1px solid {c('border')};
    border-radius: {r}px;
}}
QLineEdit, QComboBox, QSpinBox, QFontComboBox, QPlainTextEdit, QDateEdit {{
    background: {c('input')}; border: 1px solid {c('border')};
    border-radius: {rs}px; padding: 7px 10px;
    selection-background-color: {a1}; selection-color: {TEXTO_SOBRE_ACENTO};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{ border: 2px solid {a1}; }}
QDateEdit::drop-down {{ border: none; width: 26px; }}
QCalendarWidget QWidget {{ background: {c('panel_solid')}; }}
QCalendarWidget QAbstractItemView {{
    background: {c('input')}; selection-background-color: {a1};
    selection-color: {TEXTO_SOBRE_ACENTO};
}}
QCalendarWidget QToolButton {{ background: transparent; padding: 4px 8px; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{
    background: {c('panel_solid')}; border: 1px solid {c('border')};
    selection-background-color: {a1}; selection-color: {TEXTO_SOBRE_ACENTO};
}}
QListWidget {{
    background: {c('panel')}; border: 1px solid {c('border')};
    border-radius: {rs}px; outline: 0;
}}
QListWidget#galeria {{ background: transparent; border: none; }}
QFrame#grupo {{
    background: {c('card')}; border: 1px solid {c('border')}; border-radius: {r}px;
}}
QLabel#sec_titulo {{ font-weight: 700; font-size: {s + 1}pt; background: transparent; }}
QLabel#sec_cuenta {{
    color: {TEXTO_SOBRE_ACENTO}; background: {a1}; border-radius: 9px;
    padding: 1px 9px; font-weight: 700; font-size: {max(7, s - 1)}pt;
}}
QListWidget#personajes {{ background: transparent; border: none; outline: 0; }}
QListWidget::item {{ padding: 6px; border-radius: {rs}px; }}
QListWidget::item:selected {{ background: {a1}; color: {TEXTO_SOBRE_ACENTO}; }}
QListWidget::item:hover:!selected {{ background: {c('card')}; }}
QTabWidget::pane {{
    border: 1px solid {c('border')}; border-radius: {r}px;
    background: {c('panel')}; top: -1px;
}}
QFrame#barraBiblioteca {{ background: {c('panel')}; border: 1px solid {c('border')}; border-radius: {r}px; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{
    background: transparent; color: {c('muted')}; padding: 9px 16px;
    margin: 2px 4px 2px 0; border-radius: {rs}px;
}}
QTabBar::tab:selected {{
    background: {a1}; color: {TEXTO_SOBRE_ACENTO}; font-weight: 700;
}}
QTabBar::tab:hover:!selected {{ background: {c('card')}; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar::handle:vertical {{
    background: {a2}; border-radius: 5px; min-height: 36px;
}}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle:horizontal {{
    background: {a2}; border-radius: 5px; min-width: 36px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QSlider::groove:horizontal {{
    height: 6px; background: {c('border')}; border-radius: 3px;
}}
QSlider::sub-page:horizontal {{ background: {a1}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: {a1}; width: 16px; margin: -6px 0; border-radius: 8px;
    border: 2px solid {c('panel_solid')};
}}
QFrame#reproductor {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {bar_a}, stop:1 {bar_b});
    border: 1px solid {c('border')}; border-top: 2px solid {a1};
    border-radius: {r}px;
}}
QFrame#reproductor QLabel#pista_titulo {{ font-size: {s + 3}pt; font-weight: 700; }}
QFrame#reproductor QLabel#pista_sub {{ color: {c('muted')}; font-size: {max(7, s - 1)}pt; }}
QFrame#reproductor QLabel#tiempo {{
    color: {c('muted')}; font-weight: 600; font-size: {max(7, s - 1)}pt;
}}
QFrame#reproductor QSlider::groove:horizontal {{
    height: 5px; background: {c('input')}; border-radius: 2px;
}}
QFrame#reproductor QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {a1}, stop:1 {a2});
    border-radius: 2px;
}}
QFrame#reproductor QSlider::handle:horizontal {{
    background: #ffffff; border: 2px solid {a1};
    width: 9px; margin: -5px 0; border-radius: 6px;
}}
QFrame#reproductor QSlider::handle:horizontal:hover {{
    background: {a1}; border: 2px solid #ffffff;
    width: 11px; margin: -6px 0; border-radius: 7px;
}}
QFrame#reproductor QSlider#volumen::groove:horizontal {{ height: 4px; }}
QFrame#reproductor QSlider#volumen::sub-page:horizontal {{ border-radius: 2px; }}
QFrame#reproductor QSlider#volumen::handle:horizontal {{
    width: 7px; margin: -4px 0; border-radius: 5px;
}}
QCheckBox {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 5px;
    border: 2px solid {c('border')}; background: {c('input')};
}}
QCheckBox::indicator:checked {{ background: {a1}; border-color: {a1}; }}
QMenu {{
    background: {c('panel_solid')}; border: 1px solid {c('border')};
    border-radius: {rs}px; padding: 6px;
}}
QMenu::item {{ padding: 7px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {a1}; color: {TEXTO_SOBRE_ACENTO}; }}
QToolTip {{
    background: {c('panel_solid')}; color: {c('text')};
    border: 1px solid {a1}; padding: 6px;
}}
QLabel#toast {{
    background: {c('panel_solid')}; color: {c('text')};
    border: 2px solid {a1}; border-radius: {r}px;
    padding: 12px 24px; font-weight: 600;
}}
QSplitter::handle {{ background: transparent; width: 10px; }}
QProgressBar {{
    border: 1px solid {c('border')}; border-radius: 6px;
    background: {c('input')}; text-align: center;
}}
QProgressBar::chunk {{ background: {a1}; border-radius: 5px; }}
"""


# =========================================================
# BASE DE DATOS (compatible con versiones anteriores)
# =========================================================

def conectar():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA cache_size = -20000")        # ~20 MB de caché de páginas
    conn.execute("PRAGMA temp_store = MEMORY")
    # (mmap desactivado: mapear la base en memoria puede cerrar el programa de golpe)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS juegos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ficha_novela (
            juego_id INTEGER PRIMARY KEY REFERENCES juegos(id) ON DELETE CASCADE,
            lanzamiento TEXT NOT NULL DEFAULT '',
            vndb TEXT NOT NULL DEFAULT '',
            guia TEXT NOT NULL DEFAULT ''
        )""")
    ficha_columnas = {f[1] for f in conn.execute("PRAGMA table_info(ficha_novela)")}
    for columna in ("lanzamiento_steam", "desarrolladora"):
        if columna not in ficha_columnas:
            conn.execute(f"ALTER TABLE ficha_novela ADD COLUMN {columna} TEXT NOT NULL DEFAULT ''")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juego_id INTEGER NOT NULL REFERENCES juegos(id) ON DELETE CASCADE,
            titulo TEXT NOT NULL,
            ruta TEXT NOT NULL
        )""")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_clips_juego ON clips(juego_id, id)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS voces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juego_id INTEGER NOT NULL REFERENCES juegos(id) ON DELETE CASCADE,
            heroina_id INTEGER REFERENCES heroinas(id) ON DELETE SET NULL,
            titulo TEXT NOT NULL,
            ruta TEXT NOT NULL
        )""")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_voces_juego ON voces(juego_id, id)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS imagenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juego_id INTEGER NOT NULL,
            ruta TEXT NOT NULL,
            hash TEXT NOT NULL UNIQUE,
            categoria TEXT NOT NULL DEFAULT 'CG normal',
            FOREIGN KEY (juego_id) REFERENCES juegos(id)
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS heroinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juego_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            foto TEXT NOT NULL DEFAULT '',
            UNIQUE (juego_id, nombre)
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS musica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juego_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            ruta TEXT NOT NULL
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juego_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            ruta TEXT NOT NULL,
            orden INTEGER NOT NULL DEFAULT 0
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ajustes (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )""")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS seiyuus (
            clave TEXT PRIMARY KEY,
            nombre TEXT NOT NULL DEFAULT '',
            foto TEXT NOT NULL DEFAULT ''
        )""")

    def columnas(tabla):
        return {f[1] for f in conn.execute(f"PRAGMA table_info({tabla})")}

    if "me_gusta" not in columnas("videos"):
        conn.execute("ALTER TABLE videos ADD COLUMN me_gusta INTEGER NOT NULL DEFAULT 0")
    cols = columnas("imagenes")
    if "favorito" not in cols:
        conn.execute("ALTER TABLE imagenes ADD COLUMN favorito INTEGER NOT NULL DEFAULT 0")
    if "etiquetas" not in cols:
        conn.execute("ALTER TABLE imagenes ADD COLUMN etiquetas TEXT NOT NULL DEFAULT ''")
    if "heroina_id" not in cols:
        conn.execute("ALTER TABLE imagenes ADD COLUMN heroina_id INTEGER")
    if "comentario" not in cols:
        conn.execute("ALTER TABLE imagenes ADD COLUMN comentario TEXT NOT NULL DEFAULT ''")
        if "texto" in cols:  # recupera los textos de la versión anterior como comentario
            conn.execute("UPDATE imagenes SET comentario = texto WHERE texto != ''")
    if "nota_titulo" not in cols:
        conn.execute("ALTER TABLE imagenes ADD COLUMN nota_titulo TEXT NOT NULL DEFAULT ''")
    if "portada" not in columnas("juegos"):
        conn.execute("ALTER TABLE juegos ADD COLUMN portada TEXT NOT NULL DEFAULT ''")
    # Encuadre manual de portadas y fotos de heroínas: "zoom,x,y"
    if "portada_enc" not in columnas("juegos"):
        conn.execute("ALTER TABLE juegos ADD COLUMN portada_enc TEXT NOT NULL DEFAULT '1,0,0'")
    if "foto_enc" not in columnas("heroinas"):
        conn.execute("ALTER TABLE heroinas ADD COLUMN foto_enc TEXT NOT NULL DEFAULT '1,0,0'")

    for _col in ("nombre_jp", "cumple", "seiyuu"):
        if _col not in columnas("heroinas"):
            conn.execute(f"ALTER TABLE heroinas ADD COLUMN {_col} TEXT NOT NULL DEFAULT ''")
    for _col in ("altura", "busto", "cintura", "cadera"):   # cm; 0 = sin dato
        if _col not in columnas("heroinas"):
            conn.execute(f"ALTER TABLE heroinas ADD COLUMN {_col} INTEGER NOT NULL DEFAULT 0")
    if "top_pos" not in columnas("heroinas"):
        conn.execute("ALTER TABLE heroinas ADD COLUMN top_pos INTEGER NOT NULL DEFAULT 0")
    if "top_global" not in columnas("heroinas"):      # puesto en «Heroínas de heroínas»
        conn.execute("ALTER TABLE heroinas ADD COLUMN top_global INTEGER NOT NULL DEFAULT 0")
    if "vndb_id" not in columnas("heroinas"):
        conn.execute("ALTER TABLE heroinas ADD COLUMN vndb_id TEXT NOT NULL DEFAULT ''")
    if "tipo" not in columnas("heroinas"):          # 'heroina' · 'sub' (sub-heroína) · 'secundaria' (solo vista)
        conn.execute("ALTER TABLE heroinas ADD COLUMN tipo TEXT NOT NULL DEFAULT 'heroina'")
    if "foto_enc" not in columnas("seiyuus"):       # encuadre de la foto de cada seiyuu
        conn.execute("ALTER TABLE seiyuus ADD COLUMN foto_enc TEXT NOT NULL DEFAULT '1,0,0'")
    for _col in ("alias", "cumple", "redes"):       # datos propios de cada seiyuu
        if _col not in columnas("seiyuus"):
            conn.execute(f"ALTER TABLE seiyuus ADD COLUMN {_col} TEXT NOT NULL DEFAULT ''")
    if "vndb" not in columnas("seiyuus"):           # enlace al perfil de la seiyuu en VNDB
        conn.execute("ALTER TABLE seiyuus ADD COLUMN vndb TEXT NOT NULL DEFAULT ''")
    if "anio" not in columnas("seiyuus"):           # año de nacimiento (0 = sin dato)
        conn.execute("ALTER TABLE seiyuus ADD COLUMN anio INTEGER NOT NULL DEFAULT 0")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clasif_heroinas (
            clave TEXT PRIMARY KEY,
            nombre TEXT NOT NULL DEFAULT '',
            eroge INTEGER NOT NULL DEFAULT 0
        )""")
    if "info" not in columnas("heroinas"):
        conn.execute("ALTER TABLE heroinas ADD COLUMN info TEXT NOT NULL DEFAULT ''")
    for _col in ("roles", "frase", "notas"):        # libreta personal de cada personaje
        if _col not in columnas("heroinas"):
            conn.execute(f"ALTER TABLE heroinas ADD COLUMN {_col} TEXT NOT NULL DEFAULT ''")
    if "carino" not in columnas("heroinas"):         # 0-5 corazones
        conn.execute("ALTER TABLE heroinas ADD COLUMN carino INTEGER NOT NULL DEFAULT 0")
    if "apodos" not in columnas("heroinas"):         # apodo(s) de la heroína, separados por coma
        conn.execute("ALTER TABLE heroinas ADD COLUMN apodos TEXT NOT NULL DEFAULT ''")

    for _col in ("fecha_inicio", "fecha_fin"):        # cuándo empezaste / terminaste la novela
        if _col not in columnas("juegos"):
            conn.execute(f"ALTER TABLE juegos ADD COLUMN {_col} TEXT NOT NULL DEFAULT ''")

    if "horas" not in columnas("juegos"):             # horas jugadas de la novela
        conn.execute("ALTER TABLE juegos ADD COLUMN horas REAL NOT NULL DEFAULT 0")

    for _col in ("excluir_fechas", "excluir_horas"):  # «no recuerdo» las fechas / las horas
        if _col not in columnas("juegos"):
            conn.execute(f"ALTER TABLE juegos ADD COLUMN {_col} INTEGER NOT NULL DEFAULT 0")

    if "nota" not in columnas("juegos"):              # calificación 1-10 de la novela
        conn.execute("ALTER TABLE juegos ADD COLUMN nota REAL NOT NULL DEFAULT 0")

    if "carpeta" not in columnas("juegos"):           # nombre de la CARPETA en disco (el «nombre» es solo para mostrar)
        conn.execute("ALTER TABLE juegos ADD COLUMN carpeta TEXT NOT NULL DEFAULT ''")
    # Las novelas que ya tenías conservan su carpeta actual: no se mueve ni se renombra nada.
    conn.execute("UPDATE juegos SET carpeta = nombre WHERE carpeta = ''")
    conn.commit()

    if "excluir_hall" not in columnas("juegos"):      # novela sin top: no entra a «Heroínas de heroínas»
        conn.execute("ALTER TABLE juegos ADD COLUMN excluir_hall INTEGER NOT NULL DEFAULT 0")
    if "solo_campeona" not in columnas("juegos"):     # de esa novela pasa SOLO la campeona
        conn.execute("ALTER TABLE juegos ADD COLUMN solo_campeona INTEGER NOT NULL DEFAULT 0")

    # Novelas por volúmenes (Nekopara...): cada volumen con sus propias fechas y horas
    conn.execute("""
        CREATE TABLE IF NOT EXISTS volumenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juego_id INTEGER NOT NULL,
            nombre TEXT NOT NULL DEFAULT '',
            fecha_inicio TEXT NOT NULL DEFAULT '',
            fecha_fin TEXT NOT NULL DEFAULT '',
            horas REAL NOT NULL DEFAULT 0,
            excluir_fechas INTEGER NOT NULL DEFAULT 0,
            excluir_horas INTEGER NOT NULL DEFAULT 0,
            orden INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (juego_id) REFERENCES juegos(id) ON DELETE CASCADE
        )""")

    if "duracion" not in columnas("musica"):
        conn.execute("ALTER TABLE musica ADD COLUMN duracion INTEGER NOT NULL DEFAULT 0")

    # Orden manual (arrastrar y soltar)
    for tabla in ("juegos", "heroinas", "imagenes", "musica"):
        if "orden" not in columnas(tabla):
            conn.execute(f"ALTER TABLE {tabla} ADD COLUMN orden INTEGER NOT NULL DEFAULT 0")
    if "orden_fav" not in columnas("imagenes"):
        conn.execute("ALTER TABLE imagenes ADD COLUMN orden_fav INTEGER NOT NULL DEFAULT 0")

    if "top_cap" not in columnas("imagenes"):          # puesto en el Top de capturas favoritas
        conn.execute("ALTER TABLE imagenes ADD COLUMN top_cap INTEGER NOT NULL DEFAULT 0")

    if "estrellas" not in columnas("imagenes"):         # calificación 1-5 de la captura
        conn.execute("ALTER TABLE imagenes ADD COLUMN estrellas INTEGER NOT NULL DEFAULT 0")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orden_vista (
            heroina_id INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            modo TEXT NOT NULL,
            PRIMARY KEY (heroina_id, categoria)
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS duelos_heroinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ganadora_id INTEGER NOT NULL,
            perdedora_id INTEGER NOT NULL,
            ambito TEXT NOT NULL DEFAULT '',
            ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS duelos_criterios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ganadora_id INTEGER NOT NULL,
            perdedora_id INTEGER NOT NULL,
            criterio TEXT NOT NULL,
            ambito TEXT NOT NULL DEFAULT '',
            ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")

    # Versus por etapas (todos contra todos): un resultado por pareja, guardado para no repetirse.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS versus_resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ambito TEXT NOT NULL,
            a_id INTEGER NOT NULL,
            b_id INTEGER NOT NULL,
            ganadora_id INTEGER NOT NULL,
            etapas TEXT NOT NULL DEFAULT '{}',
            ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (ambito, a_id, b_id)
        )""")

    # Torneo por temporadas de «Heroínas de heroínas»: el cuadro completo va en JSON.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS torneos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temporada INTEGER NOT NULL,
            estado TEXT NOT NULL DEFAULT 'curso',
            datos TEXT NOT NULL DEFAULT '{}',
            campeona_id INTEGER NOT NULL DEFAULT 0,
            inicio TEXT NOT NULL DEFAULT '',
            fin TEXT NOT NULL DEFAULT ''
        )""")

    # Índices: las consultas de galería, favoritos y listas dejan de recorrer toda la tabla.
    for nombre_ix, tabla, cols in (
            ("ix_img_galeria", "imagenes", ("juego_id", "heroina_id", "categoria")),
            ("ix_img_heroina", "imagenes", ("heroina_id",)),
            ("ix_img_fav", "imagenes", ("favorito",)),
            ("ix_her_juego", "heroinas", ("juego_id",)),
            ("ix_mus_juego", "musica", ("juego_id",)),
            ("ix_vid_juego", "videos", ("juego_id",))):
        try:
            if all(c in columnas(tabla) for c in cols):
                conn.execute(f"CREATE INDEX IF NOT EXISTS {nombre_ix} ON {tabla}({', '.join(cols)})")
        except sqlite3.Error:
            pass

    # La categoría "Sin clasificar" ya no existe: pasa a "CG normal".
    conn.execute("UPDATE imagenes SET categoria = 'CG normal' WHERE categoria = 'Sin clasificar'")

    limpiar_duelos_antiguos(conn)
    conn.commit()
    return conn


def limpiar_duelos_antiguos(conn):
    """UNA sola vez: borra las victorias/derrotas que venían de duelos anteriores (duelo rápido,
    súper duelo viejo, listas mezcladas) y deja SOLO las de los versus guardados de cada lista.
    Antes de borrar guarda una copia en duelos_heroinas_respaldo / duelos_criterios_respaldo."""
    clave = "limpieza_duelos_v1"
    if conn.execute("SELECT 1 FROM ajustes WHERE clave = ?", (clave,)).fetchone():
        return
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS duelos_heroinas_respaldo AS "
                     "SELECT * FROM duelos_heroinas")
        conn.execute("CREATE TABLE IF NOT EXISTS duelos_criterios_respaldo AS "
                     "SELECT * FROM duelos_criterios")
        conn.execute("DELETE FROM duelos_heroinas")
        conn.execute("DELETE FROM duelos_criterios")
        for amb, g, a, b, et in conn.execute(
                "SELECT ambito, ganadora_id, a_id, b_id, etapas FROM versus_resultados"
        ).fetchall():
            p = b if g == a else a
            conn.execute("INSERT INTO duelos_heroinas (ganadora_id, perdedora_id, ambito) "
                         "VALUES (?, ?, ?)", (g, p, amb))
            try:
                etapas = {k: int(w) for k, w in json.loads(et or "{}").items()}
            except (ValueError, TypeError):
                etapas = {}
            for crit, w in etapas.items():
                if w:
                    conn.execute(
                        "INSERT INTO duelos_criterios (ganadora_id, perdedora_id, criterio, ambito) "
                        "VALUES (?, ?, ?, ?)", (w, p if w == g else g, crit, amb))
        conn.execute("INSERT OR REPLACE INTO ajustes(clave, valor) VALUES (?, '1')", (clave,))
    except sqlite3.Error:
        conn.rollback()


def cargar_ajustes(conn):
    for clave, attr in AJUSTES.items():
        fila = conn.execute("SELECT valor FROM ajustes WHERE clave = ?", (clave,)).fetchone()
        if fila is None:
            continue
        tipo = type(getattr(Tema, attr))
        try:
            if tipo is bool:
                valor = fila[0] == "1"
            elif tipo is int:
                valor = int(fila[0])
            else:
                valor = fila[0]
        except ValueError:
            continue
        setattr(Tema, attr, valor)
    Tema.anim = False          # aunque tu base de datos tenga «anim» activado
    if Tema.titulo.strip().upper() in ("✿ YUME GALLERY", "YUME GALLERY"):
        Tema.titulo = "✿ NYUHUHU GALLERY"
        try:
            conn.execute("INSERT OR REPLACE INTO ajustes(clave, valor) VALUES ('titulo', ?)",
                         (Tema.titulo,))
            conn.commit()
        except sqlite3.Error:
            pass
    # Versión compacta: cabecera más baja (se aplica UNA sola vez; después se respeta tu ajuste)
    if conn.execute("SELECT 1 FROM ajustes WHERE clave = 'ui_compacta'").fetchone() is None:
        try:
            if Tema.alto_cabecera > 60:
                Tema.alto_cabecera = 60
                conn.execute("INSERT OR REPLACE INTO ajustes(clave, valor) VALUES ('alto_cabecera', '60')")
            conn.execute("INSERT OR REPLACE INTO ajustes(clave, valor) VALUES ('ui_compacta', '1')")
            conn.commit()
        except sqlite3.Error:
            pass
    if Tema.nombre not in BASES:
        Tema.nombre = "Oscuro"
    if Tema.acento not in ACENTOS and Tema.acento != "Personalizado":
        Tema.acento = "Sakura"


def guardar_ajuste(conn, clave, valor):
    if isinstance(valor, bool):
        valor = "1" if valor else "0"
    conn.execute(
        "INSERT INTO ajustes(clave, valor) VALUES (?, ?) "
        "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
        (clave, str(valor)))
    conn.commit()


# =========================================================
# UTILIDADES
# =========================================================

def hash_archivo(ruta):
    sha = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(bloque)
    return sha.hexdigest()


def es_captura_steam(ruta):
    return re.fullmatch(r"\d{14}_\d+\.(jpg|jpeg|png)", Path(ruta).name,
                        re.IGNORECASE) is not None


def nombre_seguro(nombre):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", nombre).strip(" .")


def nombre_visible(nombre):
    """Nombre para MOSTRAR: se respeta tal cual (con «:», «?», etc.); solo se limpian espacios."""
    return " ".join((nombre or "").split())


def carpeta_libre(conn, nombre, ignorar_id=None):
    """Nombre de carpeta seguro para Windows y que no choque con otra novela ni con una carpeta
    que ya exista en la biblioteca."""
    base = nombre_seguro(nombre) or "Novela"
    cand, n = base, 2
    while True:
        usada = conn.execute("SELECT 1 FROM juegos WHERE carpeta = ? COLLATE NOCASE AND id IS NOT ?",
                             (cand, ignorar_id)).fetchone()
        if not usada and not (ROOT / cand).exists():
            return cand
        cand = f"{base}_{n}"
        n += 1


def nombre_disponible(carpeta, nombre):
    destino = carpeta / nombre
    n = 2
    while destino.exists():
        destino = carpeta / f"{Path(nombre).stem}_{n}{Path(nombre).suffix}"
        n += 1
    return destino


def carpeta_hc(juego, heroina, categoria):
    return ROOT / juego / heroina / categoria


def preparar_carpetas_heroina(juego, heroina):
    for cat in CATEGORIAS:
        carpeta_hc(juego, heroina, cat).mkdir(parents=True, exist_ok=True)


def copiar_asset(origen, subcarpeta, prefijo):
    """Copia una imagen/audio dentro de la biblioteca y devuelve la nueva ruta."""
    destino_dir = ASSETS / subcarpeta
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = nombre_disponible(destino_dir, f"{prefijo}{Path(origen).suffix.lower()}")
    shutil.copy2(origen, destino)
    return str(destino)


def mezclar(c1, c2, t):
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue() + (c2.blue() - c1.blue()) * t))


def con_alfa(color, alfa):
    c = QColor(color)
    c.setAlpha(alfa)
    return c


def _nivel_miniatura(lado):
    return 480 if lado <= 480 else (1000 if lado <= 1000 else 0)


def _archivos_miniatura(ruta, st, nivel):
    clave = hashlib.md5(
        f"{ruta}|{st.st_mtime_ns}|{st.st_size}|{nivel}".encode("utf-8")).hexdigest()
    return MINIATURAS / f"{clave}.jpg", MINIATURAS / f"{clave}.png"


def _crear_miniatura(ruta, nivel, jpg, png):
    """Lee la imagen original UNA vez, la reduce y la guarda en _assets/miniaturas."""
    lector = QImageReader(ruta)
    lector.setAutoTransform(True)
    tam = lector.size()
    if tam.isValid():
        tam.scale(nivel, nivel, Qt.AspectRatioMode.KeepAspectRatio)
        lector.setScaledSize(tam)
    img = lector.read()
    if img.isNull():
        return QImage()
    destino, formato, calidad = ((png, "PNG", -1) if img.hasAlphaChannel()
                                 else (jpg, "JPEG", 93))
    tmp = destino.with_name(f"{destino.name}.{threading.get_ident()}.tmp")
    try:
        if img.save(str(tmp), formato, calidad):
            os.replace(tmp, destino)
    except OSError:
        pass
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
    return img


def leer_imagen_escalada(ruta, lado, solo_crear=False):
    """QImage con el lado mayor <= `lado`. Las capturas grandes (PNG de pantalla completa)
    tardan en decodificarse cada vez; aquí se reducen una sola vez y se guardan, así las
    pantallas con muchas imágenes se abren al instante. Se invalidan solas si el archivo cambia."""
    ruta = str(ruta)
    try:
        st = os.stat(ruta)
    except OSError:
        return QImage()
    lector = QImageReader(ruta)
    lector.setAutoTransform(True)
    tam = lector.size()
    nivel = _nivel_miniatura(lado)
    if tam.isValid() and nivel and max(tam.width(), tam.height()) > nivel * 1.25:
        jpg, png = _archivos_miniatura(ruta, st, nivel)
        img = QImage()
        for f in (jpg, png):
            if f.exists():
                if solo_crear:
                    return QImage()
                img = QImage(str(f))
                break
        if img.isNull():
            img = _crear_miniatura(ruta, nivel, jpg, png)
            if solo_crear:
                return QImage()
        if not img.isNull():
            if max(img.width(), img.height()) > lado:
                img = img.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
            return img
    if solo_crear:
        return QImage()
    if tam.isValid() and max(tam.width(), tam.height()) > lado:
        tam.scale(lado, lado, Qt.AspectRatioMode.KeepAspectRatio)
        lector.setScaledSize(tam)
    return lector.read()


def precalentar_miniaturas():
    """En segundo plano: prepara las miniaturas empezando por lo que más se ve (fotos de
    heroínas, portadas, favoritas) y siguiendo con el resto de capturas."""
    def trabajo():
        try:
            c = sqlite3.connect(DB_PATH, timeout=20)
            principales, resto, vistas = [], [], set()
            for consulta, destino in (
                    ("SELECT foto FROM heroinas WHERE foto <> ''", principales),
                    ("SELECT portada FROM juegos WHERE portada <> ''", principales),
                    ("SELECT ruta FROM imagenes WHERE favorito = 1", resto),
                    ("SELECT ruta FROM imagenes ORDER BY id DESC", resto)):
                for (r,) in c.execute(consulta):
                    if r and r not in vistas:
                        vistas.add(r)
                        destino.append(r)
            c.close()
        except Exception:
            return
        tareas = [(r, 480) for r in principales] + [(r, 1000) for r in principales] \
            + [(r, 480) for r in resto]
        cola, cerrojo = iter(tareas), threading.Lock()

        def obrero():
            while True:
                with cerrojo:
                    t = next(cola, None)
                if t is None:
                    return
                try:
                    leer_imagen_escalada(t[0], t[1], solo_crear=True)
                except Exception:
                    pass
                time.sleep(0.002)
        for _ in range(2):
            threading.Thread(target=obrero, daemon=True, name="miniaturas").start()
    threading.Thread(target=trabajo, daemon=True, name="miniaturas-lista").start()


class CacheImagenes:
    """Caché LRU de pixmaps: carga perezosa y memoria acotada."""

    def __init__(self, limite, limite_mb=250):
        self.limite = limite
        self.limite_bytes = limite_mb * 1024 * 1024
        self.datos = OrderedDict()
        self._bytes = 0

    def _guardar(self, clave, pm):
        previo = self.datos.pop(clave, None)
        if previo is not None:
            self._bytes -= previo.width() * previo.height() * 4
        self.datos[clave] = pm
        self._bytes += pm.width() * pm.height() * 4
        while len(self.datos) > 1 and (len(self.datos) > self.limite
                                        or self._bytes > self.limite_bytes):
            _, viejo = self.datos.popitem(last=False)
            self._bytes -= viejo.width() * viejo.height() * 4

    def obtener(self, ruta, lado):
        if not ruta:
            return QPixmap()
        clave = (str(ruta), lado)
        if clave in self.datos:
            self.datos.move_to_end(clave)
            return self.datos[clave]

        img = leer_imagen_escalada(ruta, lado)
        pm = QPixmap.fromImage(img) if not img.isNull() else QPixmap()

        self._guardar(clave, pm)
        return pm

    # ---- carga en segundo plano: el dibujo nunca espera al disco
    def obtener_diferido(self, ruta, lado, widget=None):
        """Devuelve el pixmap si ya está en caché; si no, lo carga en otro hilo y devuelve uno
        vacío. Al terminar, repinta `widget` (así la galería no se congela al desplazarse)."""
        if not ruta:
            return QPixmap()
        clave = (str(ruta), lado)
        pm = self.datos.get(clave)
        if pm is not None:
            self.datos.move_to_end(clave)
            return pm
        if not hasattr(self, "_pend"):
            self._pend = {}
            self._espera = set()
            self._senal = _SenalCarga()
            self._senal.listo.connect(self._recibir)
            self._pool = QThreadPool()
            self._pool.setMaxThreadCount(3)
        avisar = self._pend.get(clave)
        if avisar is not None:                      # ya se está cargando
            if widget is not None:
                avisar.add(widget)
            return QPixmap()
        if len(self._pend) >= 32:
            if widget is not None:
                self._espera.add(widget)
            return QPixmap()
        self._pend[clave] = {widget} if widget is not None else set()
        self._pool.start(_TareaCarga(str(ruta), lado, self._senal))
        return QPixmap()

    def _recibir(self, ruta, lado, img):
        clave = (ruta, lado)
        avisar = self._pend.pop(clave, set())
        self._guardar(clave, QPixmap.fromImage(img) if not img.isNull() else QPixmap())
        if self._espera:
            avisar.update(self._espera)
            self._espera.clear()
        for w in avisar:
            try:
                if w.isVisible():
                    w.update()
            except RuntimeError:                    # el widget ya no existe
                pass


class _SenalCarga(QObject):
    listo = Signal(str, int, QImage)


class _TareaCarga(QRunnable):
    def __init__(self, ruta, lado, senal):
        super().__init__()
        self.ruta, self.lado, self.senal = ruta, lado, senal

    def run(self):
        try:
            img = leer_imagen_escalada(self.ruta, self.lado)
        except Exception:
            img = QImage()
        self.senal.listo.emit(self.ruta, self.lado, img)


CACHE_MINI = CacheImagenes(250, 150)
CACHE_GRANDE = CacheImagenes(500, 300)
CACHE_TOP = CacheImagenes(400, 150)       # miniaturas del Top de capturas favoritas (no se pisa con el visor)

_ERRORES_UI_VISTOS = set()


def registrar_error_ui(donde):
    """Anota en error.log (una sola vez por tipo de fallo) un error ocurrido al dibujar o al cargar
    una pantalla, para que NO se repita en cada repintado ni tumbe la ventana."""
    try:
        import traceback
        texto = traceback.format_exc()
        ult = texto.strip().splitlines()[-1] if texto.strip() else ""
        if (donde, ult) in _ERRORES_UI_VISTOS:
            return
        _ERRORES_UI_VISTOS.add((donde, ult))
        with open(ROOT / "error.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- {donde} {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n{texto}")
    except Exception:
        pass


ENC0 = (1.0, 0.0, 0.0)   # encuadre por defecto: (zoom, desplazamiento x, desplazamiento y)


def parse_enc(s):
    """'zoom,x,y' -> (zoom, x, y) con límites seguros."""
    try:
        z, x, y = (float(v) for v in str(s).split(","))
    except (ValueError, TypeError):
        return ENC0
    return (max(1.0, min(4.0, z)), max(-1.0, min(1.0, x)), max(-1.0, min(1.0, y)))


def fmt_enc(enc):
    return "%.4f,%.4f,%.4f" % tuple(enc)


def dibujar_cover(p, rect, pm, radio=12, enc=None):
    """Dibuja la imagen rellenando el rectángulo (recorte tipo 'cover').
    `enc` = (zoom, x, y): zoom >= 1 y desplazamiento -1..1 para encuadrar a mano."""
    p.save()
    camino = QPainterPath()
    camino.addRoundedRect(QRectF(rect), radio, radio)
    p.setClipPath(camino, Qt.ClipOperation.IntersectClip)
    if pm is not None and not pm.isNull():
        z, ox, oy = enc or ENC0
        esc = max(rect.width() / pm.width(), rect.height() / pm.height()) * z
        w, h = pm.width() * esc, pm.height() * esc
        x = rect.x() + (rect.width() - w) / 2 + ox * max(0.0, w - rect.width()) / 2
        y = rect.y() + (rect.height() - h) / 2 + oy * max(0.0, h - rect.height()) / 2
        p.drawPixmap(QRectF(x, y, w, h), pm, QRectF(pm.rect()))
    else:
        g = QLinearGradient(rect.topLeft(), rect.bottomRight())
        g.setColorAt(0, QColor(Tema.a1()))
        g.setColorAt(1, QColor(Tema.a2()))
        p.fillRect(QRectF(rect), QBrush(g))
        p.setPen(QColor(255, 255, 255, 210))
        f = QFont(p.font())
        f.setPixelSize(max(10, int(min(rect.width(), rect.height()) * 0.3)))
        p.setFont(f)
        p.drawText(QRectF(rect), Qt.AlignmentFlag.AlignCenter, "♡")
    p.restore()


_AVATARES = OrderedDict()          # avatares ya dibujados: (ruta, lado, encuadre, fecha) → pixmap
_AVATARES_MAX = 700


def avatar(ruta, lado=52, enc=None):
    """Avatar redondo. Se guarda ya dibujado: pedirlo otra vez no toca el disco ni vuelve a pintar."""
    try:
        mt = os.stat(ruta).st_mtime_ns if ruta else 0
    except OSError:
        mt = 0
    clave = (str(ruta or ""), lado, tuple(enc) if enc else None, mt)
    pm = _AVATARES.get(clave)
    if pm is not None:
        _AVATARES.move_to_end(clave)
        return pm
    pm = _avatar_dibujar(ruta, lado, enc)
    _AVATARES[clave] = pm
    while len(_AVATARES) > _AVATARES_MAX:
        _AVATARES.popitem(last=False)
    return pm


def avatar_listo(ruta, lado, enc, widget):
    """(pixmap, listo). La foto se lee del disco en segundo plano: mientras no esté, devuelve
    (None, False) y, al llegar, repinta `widget`. Así abrir una pantalla nunca se queda esperando."""
    if ruta:
        pm = CACHE_GRANDE.obtener_diferido(ruta, 200, widget)
        if pm.isNull() and (str(ruta), 200) not in CACHE_GRANDE.datos:
            return None, False
    return avatar(ruta, lado, enc), True


def _avatar_dibujar(ruta, lado=52, enc=None):
    pm = QPixmap(lado, lado)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    camino = QPainterPath()
    camino.addEllipse(0, 0, lado, lado)
    p.setClipPath(camino)
    dibujar_cover(p, QRectF(0, 0, lado, lado), CACHE_GRANDE.obtener(ruta, 200), 0, enc)
    p.end()
    return pm


def copiar_imagen_portapapeles(ruta, pm=None):
    """Copia la imagen al portapapeles (como imagen Y como archivo) para pegarla en chats."""
    if pm is not None and not pm.isNull():
        img = pm.toImage()
    else:
        lector = QImageReader(str(ruta))
        lector.setAutoTransform(True)
        img = lector.read()
    if img.isNull():
        return False
    mime = QMimeData()
    mime.setImageData(img)
    if Path(ruta).exists():
        mime.setUrls([QUrl.fromLocalFile(str(ruta))])
    QApplication.clipboard().setMimeData(mime)
    return True


# =========================================================
# WIDGETS DINAMICOS
# =========================================================

def dibujar_icono(p, clave, centro, tam, color, insignia=""):
    """Íconos vectoriales del reproductor (sin emojis): escalan con cualquier tamaño y tema.
    Se definen en coordenadas de -1 a 1 y se dibujan centrados en `centro` con lado `tam`."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(centro)
    p.scale(tam / 2.0, tam / 2.0)
    pincel = QColor(color)
    redondo = dict(cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin)

    def relleno():
        p.setPen(QPen(pincel, 0.14, Qt.PenStyle.SolidLine, redondo["cap"], redondo["join"]))
        p.setBrush(pincel)

    def trazo():
        p.setPen(QPen(pincel, 0.17, Qt.PenStyle.SolidLine, redondo["cap"], redondo["join"]))
        p.setBrush(Qt.BrushStyle.NoBrush)

    def punta(x, y, dx):
        relleno()
        p.drawPolygon(QPolygonF([QPointF(x + 0.5 * dx, y), QPointF(x, y - 0.32),
                                 QPointF(x, y + 0.32)]))

    if clave == "next":
        p.scale(-1, 1)
        clave = "prev"

    if clave == "play":
        relleno()
        p.drawPolygon(QPolygonF([QPointF(-0.45, -0.78), QPointF(0.85, 0.0), QPointF(-0.45, 0.78)]))
    elif clave == "pause":
        relleno()
        p.drawRoundedRect(QRectF(-0.62, -0.72, 0.42, 1.44), 0.12, 0.12)
        p.drawRoundedRect(QRectF(0.20, -0.72, 0.42, 1.44), 0.12, 0.12)
    elif clave == "prev":
        relleno()
        p.drawRoundedRect(QRectF(-0.88, -0.7, 0.2, 1.4), 0.08, 0.08)
        p.drawPolygon(QPolygonF([QPointF(0.82, -0.7), QPointF(-0.45, 0.0), QPointF(0.82, 0.7)]))
    elif clave == "shuffle":
        trazo()
        a = QPainterPath()
        a.moveTo(-0.9, 0.55)
        a.cubicTo(-0.1, 0.55, 0.0, -0.55, 0.5, -0.55)
        p.drawPath(a)
        b = QPainterPath()
        b.moveTo(-0.9, -0.55)
        b.cubicTo(-0.1, -0.55, 0.0, 0.55, 0.5, 0.55)
        p.drawPath(b)
        punta(0.5, -0.55, 1)
        punta(0.5, 0.55, 1)
    elif clave == "repeat":
        for giro in (1, -1):                       # el lazo de abajo es el de arriba girado 180°
            p.save()
            p.scale(giro, giro)
            trazo()
            lazo = QPainterPath()
            lazo.moveTo(-0.9, 0.3)
            lazo.lineTo(-0.9, -0.1)
            lazo.quadTo(-0.9, -0.6, -0.4, -0.6)
            lazo.lineTo(0.45, -0.6)
            p.drawPath(lazo)
            punta(0.45, -0.6, 1)
            p.restore()
    elif clave == "dice":
        trazo()
        p.drawRoundedRect(QRectF(-0.8, -0.8, 1.6, 1.6), 0.38, 0.38)
        relleno()
        for x, y in ((-0.38, -0.38), (0.38, -0.38), (0.0, 0.0), (-0.38, 0.38), (0.38, 0.38)):
            p.drawEllipse(QPointF(x, y), 0.07, 0.07)
    elif clave.startswith("vol"):
        relleno()
        p.drawPolygon(QPolygonF([QPointF(-0.95, -0.3), QPointF(-0.55, -0.3), QPointF(-0.05, -0.75),
                                 QPointF(-0.05, 0.75), QPointF(-0.55, 0.3), QPointF(-0.95, 0.3)]))
        trazo()
        if clave == "vol0":
            p.drawLine(QPointF(0.3, -0.32), QPointF(0.92, 0.32))
            p.drawLine(QPointF(0.92, -0.32), QPointF(0.3, 0.32))
        else:
            p.drawArc(QRectF(-0.3, -0.42, 0.84, 0.84), -45 * 16, 90 * 16)
            if clave == "vol2":
                p.drawArc(QRectF(-0.62, -0.82, 1.64, 1.64), -45 * 16, 90 * 16)
    p.restore()

    if insignia:                                    # número pequeño dentro del ícono (repetir: 1)
        f = QFont(p.font())
        f.setPixelSize(max(7, int(tam * 0.42)))
        f.setBold(True)
        p.save()
        p.setFont(f)
        p.setPen(pincel)
        p.drawText(QRectF(centro.x() - tam / 2, centro.y() - tam / 2, tam, tam),
                   int(Qt.AlignmentFlag.AlignCenter), insignia)
        p.restore()


class BotonAnimado(QPushButton):
    """Botón con animación suave al pasar el ratón; sigue el tema."""

    def __init__(self, texto="", parent=None, primario=False):
        super().__init__(texto, parent)
        self.primario = primario
        self._h = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(170)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._set)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _set(self, v):
        self._h = float(v)
        self.update()

    def _ir(self, fin):
        if Tema.anim:
            self.anim.stop()
            self.anim.setStartValue(self._h)
            self.anim.setEndValue(fin)
            self.anim.start()
        else:
            self._h = fin
            self.update()

    def enterEvent(self, e):
        self._ir(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._ir(0.0)
        super().leaveEvent(e)

    def sizeHint(self):
        fm = self.fontMetrics()
        return QSize(fm.horizontalAdvance(self.text()) + 34, fm.height() + 20)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        if self.isDown():
            r.translate(0, 1.5)

        activo = self.primario or self.isChecked()
        if activo:
            base, alto = QColor(Tema.a1()), QColor(Tema.a2())
            color = mezclar(base, alto, self._h * 0.7)
            txt = QColor(TEXTO_SOBRE_ACENTO)
        else:
            base, alto = QColor(Tema.c("card")), QColor(Tema.a1())
            color = mezclar(base, alto, self._h * 0.30)
            txt = QColor(Tema.c("text"))
        if not self.isEnabled():
            p.setOpacity(0.45)

        radio = min(Tema.radio * 0.8, r.height() / 2)
        if self._h > 0.01 and self.isEnabled():          # resplandor de acento al pasar el ratón
            halo = QColor(Tema.a1())
            p.setBrush(Qt.BrushStyle.NoBrush)
            for i, al in ((2.5, 34), (1.5, 62)):
                halo.setAlpha(al)
                p.setPen(QPen(halo, 1.6))
                p.drawRoundedRect(r.adjusted(-i, -i, i, i), radio + i, radio + i)
        p.setPen(QPen(mezclar(QColor(Tema.c("border")), QColor(Tema.a1()), self._h),
                      1.2 + 0.8 * self._h))
        p.setBrush(color)
        p.drawRoundedRect(r, radio, radio)
        p.setPen(txt)
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.text())


class AccesoBiblioteca(BotonAnimado):
    """Acceso compacto con icono y contorno derivados de la paleta activa."""

    def __init__(self, titulo, simbolo):
        super().__init__(titulo)
        self.simbolo = simbolo

    def sizeHint(self):
        fm = self.fontMetrics()
        return QSize(fm.horizontalAdvance(self.text()) + 38, max(34, fm.height() + 14))

    def paintEvent(self, e):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            r = QRectF(self.rect()).adjusted(1, 2, -1, -2)
            a1 = QColor(Tema.a1())
            base = QColor(Tema.c("input"))
            activo = self.isDown() or self.underMouse() or self.hasFocus()
            color = mezclar(base, a1, 0.19 if self.isDown() else 0.12 if activo else 0.035)
            borde = mezclar(QColor(Tema.c("border")), a1, 0.65 if activo else 0.18)
            p.setPen(QPen(borde, 1.0))
            p.setBrush(color)
            radio = min(Tema.radio, r.height() / 2)
            p.drawRoundedRect(r, radio, radio)

            icono = QFont("Segoe UI Symbol")
            icono.setPixelSize(16)
            p.setFont(icono)
            tinte = mezclar(QColor(Tema.c("text")), a1, 0.72)
            p.setPen(tinte)
            area_icono = QRectF(r.left() + 6, r.top(), 19, r.height())
            p.drawText(area_icono, Qt.AlignmentFlag.AlignCenter, self.simbolo)
            p.setFont(self.font())
            p.setPen(QColor(Tema.c("text")))
            p.drawText(r.adjusted(28, 0, -4, 0),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        finally:
            p.end()


class BotonRedondo(BotonAnimado):
    """Botón circular del reproductor; el principal lleva degradado y halo de acento."""

    def __init__(self, texto="", lado=40, parent=None, primario=False, pt=None, icono=""):
        super().__init__(texto, parent, primario)
        self.lado = lado
        self.pt = pt
        self.icono = icono
        self.insignia = ""
        self.setFixedSize(lado, lado)

    def set_icono(self, clave, insignia=""):
        self.icono = clave
        self.insignia = insignia
        self.update()

    def sizeHint(self):
        return QSize(self.lado, self.lado)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        m = 6 if self.primario else 3
        r = QRectF(self.rect()).adjusted(m, m, -m, -m)
        if Tema.anim:
            g = 1.5 * self._h
            r.adjust(-g, -g, g, g)
        if self.isDown():
            r.adjust(1.5, 1.5, -1.5, -1.5)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        activo = self.primario or self.isChecked()
        if not self.isEnabled():
            p.setOpacity(0.45)
        p.setPen(Qt.PenStyle.NoPen)
        if self.primario:                       # halo suave
            for i in range(6, 0, -2):
                p.setBrush(con_alfa(a1, 14 + int(14 * self._h)))
                p.drawEllipse(r.adjusted(-i, -i, i, i))
        if activo:
            gr = QLinearGradient(r.topLeft(), r.bottomRight())
            gr.setColorAt(0, a1)
            gr.setColorAt(1, a2)
            p.setBrush(QBrush(gr))
            p.setPen(QPen(QColor(255, 255, 255, 110), 1.2))
            txt = QColor(TEXTO_SOBRE_ACENTO)
        else:
            p.setBrush(mezclar(QColor(Tema.c("card")), a1, 0.30 * self._h))
            p.setPen(QPen(mezclar(QColor(Tema.c("border")), a1, self._h), 1.2))
            txt = QColor(Tema.c("text"))
        p.drawEllipse(r)
        if self.icono:
            lado_ic = r.width() * (0.44 if self.primario else 0.5)
            dibujar_icono(p, self.icono, r.center(), lado_ic, txt, self.insignia)
            return
        f = QFont(p.font())
        f.setPointSizeF(self.pt or (Tema.tam + (6 if self.primario else 2)))
        p.setFont(f)
        p.setPen(txt)
        dx = 1.5 if (self.primario and self.text() == "▶") else 0
        p.drawText(r.translated(dx, 0), int(Qt.AlignmentFlag.AlignCenter), self.text())


class CoverWidget(QWidget):
    """Imagen con recorte 'cover'. Si es editable: DOBLE CLIC activa el modo encuadre
    (arrastrar = mover, rueda = ampliar); doble clic otra vez (o sacar el ratón) lo desactiva.
    Así un roce accidental del ratón no desenfoca la foto. El encuadre se guarda como
    (zoom, x, y) normalizado, y se ve bien en tarjetas, paneles y avatares de cualquier tamaño."""
    encuadre_cambiado = Signal(object)

    def __init__(self, texto="", min_h=200, parent=None, editable=False, pista=False):
        super().__init__(parent)
        self.ruta = ""
        self.texto = texto
        self.enc = ENC0
        self.editable = editable
        self.pista = pista
        self.modo_edicion = False
        self._arrastre = None
        self.setMinimumHeight(min_h)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def poner(self, ruta, texto=None, enc=None):
        self.ruta = ruta or ""
        if texto is not None:
            self.texto = texto
        self.enc = tuple(enc) if enc else ENC0
        self._salir_edicion()
        self.update()

    # --- modo encuadre
    def _entrar_edicion(self):
        self.modo_edicion = True
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("")
        self.update()

    def _salir_edicion(self):
        if not self.modo_edicion:
            return
        self.modo_edicion = False
        self._arrastre = None
        self.unsetCursor()
        self.update()

    def _desborde(self):
        pm = CACHE_GRANDE.obtener(self.ruta, 1000)
        if pm.isNull():
            return 0.0, 0.0
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        esc = max(r.width() / pm.width(), r.height() / pm.height()) * self.enc[0]
        return (max(0.0, pm.width() * esc - r.width()),
                max(0.0, pm.height() * esc - r.height()))

    def mouseDoubleClickEvent(self, e):
        if self.editable and self.ruta and e.button() == Qt.MouseButton.LeftButton:
            if self.modo_edicion:
                self._salir_edicion()
            else:
                self._entrar_edicion()
        else:
            super().mouseDoubleClickEvent(e)

    def mousePressEvent(self, e):
        if self.modo_edicion and e.button() == Qt.MouseButton.LeftButton:
            self._arrastre = (e.position(), self.enc)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._arrastre is None:
            return
        p0, enc0 = self._arrastre
        ow, oh = self._desborde()
        d = e.position() - p0
        ox = enc0[1] + (d.x() / (ow / 2) if ow > 1 else 0.0)
        oy = enc0[2] + (d.y() / (oh / 2) if oh > 1 else 0.0)
        self.enc = (enc0[0], max(-1.0, min(1.0, ox)), max(-1.0, min(1.0, oy)))
        self.update()

    def mouseReleaseEvent(self, e):
        if self._arrastre is not None:
            self._arrastre = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.encuadre_cambiado.emit(self.enc)
        else:
            super().mouseReleaseEvent(e)

    def wheelEvent(self, e):
        if not self.modo_edicion:
            e.ignore()
            return
        z = self.enc[0] * (1.1 if e.angleDelta().y() > 0 else 1 / 1.1)
        self.enc = (max(1.0, min(4.0, z)), self.enc[1], self.enc[2])
        self.update()
        self.encuadre_cambiado.emit(self.enc)
        e.accept()

    def leaveEvent(self, e):
        if self._arrastre is None:
            self._salir_edicion()
        super().leaveEvent(e)

    def contextMenuEvent(self, e):
        if not (self.editable and self.ruta):
            return
        m = QMenu(self)
        a_enc = m.addAction("✥ Terminar de encuadrar" if self.modo_edicion
                            else "✥ Encuadrar imagen")
        a_rst = m.addAction("↺ Restablecer encuadre")
        acc = m.exec(e.globalPos())
        if acc == a_enc:
            self._salir_edicion() if self.modo_edicion else self._entrar_edicion()
        elif acc == a_rst:
            self.enc = ENC0
            self.update()
            self.encuadre_cambiado.emit(self.enc)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        radio = Tema.radio + 2
        dibujar_cover(p, r, CACHE_GRANDE.obtener_diferido(self.ruta, 1000, self), radio, self.enc)
        camino = QPainterPath()
        camino.addRoundedRect(r, radio, radio)
        if self.texto and not self.modo_edicion:
            p.save()
            p.setClipPath(camino)
            g = QLinearGradient(r.left(), r.bottom() - 90, r.left(), r.bottom())
            g.setColorAt(0, QColor(0, 0, 0, 0))
            g.setColorAt(1, QColor(20, 10, 30, 200))
            p.fillRect(r, QBrush(g))
            p.restore()
            f = QFont(p.font())
            f.setBold(True)
            f.setPointSize(Tema.tam + 4)
            p.setFont(f)
            p.setPen(QColor("#ffffff"))
            p.drawText(r.adjusted(14, 0, -14, -12),
                       Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
                       self.texto)
        p.setBrush(Qt.BrushStyle.NoBrush)
        if self.modo_edicion:
            p.setPen(QPen(QColor(Tema.a2()), 3, Qt.PenStyle.DashLine))
        else:
            p.setPen(QPen(QColor(Tema.a1()), 2))
        p.drawRoundedRect(r, radio, radio)


class TarjetaJuego(QWidget):
    """Tarjeta tipo carta con portada, zoom y elevación al pasar el ratón.
    Se puede arrastrar para reordenarla (lo gestiona GridTarjetas)."""
    clic = Signal(int)
    menu = Signal(int, object)
    arrastre = Signal(object, object)   # (tarjeta, posición global)
    soltado = Signal(object, object)

    def __init__(self, juego_id=-1, nombre="", portada="", cantidad=0, nueva=False, enc=None):
        super().__init__()
        self.enc = tuple(enc) if enc else ENC0
        self.juego_id, self.nombre = juego_id, nombre
        self.portada, self.cantidad, self.nueva = portada, cantidad, nueva
        self._mx = self._my = 0.0
        self._h = 0.0
        self._press = None
        self._arrastrando = False
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._set)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def _set(self, v):
        self._h = float(v)
        self.update()

    def _ir(self, fin):
        if Tema.anim:
            self.anim.stop()
            self.anim.setStartValue(self._h)
            self.anim.setEndValue(fin)
            self.anim.start()
        else:
            self._h = fin
            self.update()

    def enterEvent(self, e):
        self._ir(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        if not self._arrastrando:
            self._ir(0.0)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self._arrastrando = False
        self._press = (e.position().toPoint()
                       if e.button() == Qt.MouseButton.LeftButton and not self.nueva else None)
        e.accept()          # así la tarjeta recibe el movimiento aunque el cursor salga de ella

    def mouseMoveEvent(self, e):
        if self._press is not None and (e.buttons() & Qt.MouseButton.LeftButton):
            if self._arrastrando or (e.position().toPoint() - self._press).manhattanLength() \
                    >= QApplication.startDragDistance():
                self._arrastrando = True
                self.arrastre.emit(self, e.globalPosition().toPoint())
                return
        pt = e.position()
        self._mx = pt.x() / max(1, self.width()) - 0.5
        self._my = pt.y() / max(1, self.height()) - 0.5
        if Tema.anim:
            self.update()

    def mouseReleaseEvent(self, e):
        if self._arrastrando:
            self._arrastrando = False
            self._press = None
            self.soltado.emit(self, e.globalPosition().toPoint())
            return
        self._press = None
        if e.button() == Qt.MouseButton.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clic.emit(self.juego_id)
        elif e.button() == Qt.MouseButton.RightButton and not self.nueva:
            self.menu.emit(self.juego_id, e.globalPosition().toPoint())

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        h = self._h                       # 0 o 1 al instante (sin animación)
        r = QRectF(self.rect()).adjusted(7, 9, -7, -7)
        radio = Tema.radio + 4
        camino = QPainterPath()
        camino.addRoundedRect(r, radio, radio)
        if h > 0.02:                      # resplandor de acento en lugar de «levantar» la tarjeta
            halo = QColor(Tema.a1())
            p.setBrush(Qt.BrushStyle.NoBrush)
            for i, al in ((6, 24), (4, 46), (2, 84)):
                halo.setAlpha(al)
                p.setPen(QPen(halo, 2.2))
                p.drawRoundedRect(r.adjusted(-i, -i, i, i), radio + i, radio + i)

        if self.nueva:
            p.setBrush(mezclar(QColor(Tema.c("card")), QColor(Tema.a1()), 0.18 * self._h))
            pen = QPen(QColor(Tema.a1()), 2.5, Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.drawPath(camino)
            p.setPen(QColor(Tema.a1()))
            f = QFont(p.font())
            f.setPixelSize(int(r.height() * 0.25))
            f.setBold(True)
            p.setFont(f)
            p.drawText(r.adjusted(0, 0, 0, -r.height() * 0.15),
                       Qt.AlignmentFlag.AlignCenter, "＋")
            f.setPixelSize(max(12, int(r.width() * 0.08)))
            p.setFont(f)
            p.setPen(QColor(Tema.c("text")))
            p.drawText(r.adjusted(0, r.height() * 0.45, 0, 0),
                       Qt.AlignmentFlag.AlignCenter, "Nueva novela")
            return

        p.save()
        p.setClipPath(camino)
        pm = CACHE_GRANDE.obtener_diferido(self.portada, 700, self)
        dibujar_cover(p, r, pm, 0, self.enc)
        g = QLinearGradient(r.left(), r.top() + r.height() * 0.55, r.left(), r.bottom())
        g.setColorAt(0, QColor(25, 12, 40, 0))
        g.setColorAt(1, QColor(25, 12, 40, 225))
        p.fillRect(r, QBrush(g))
        if h > 0.02:                      # luz suave fija en la esquina superior
            cx = r.left() + r.width() * 0.30
            cy = r.top() + r.height() * 0.18
            brillo = QRadialGradient(QPointF(cx, cy), r.width() * 0.9)
            brillo.setColorAt(0, QColor(255, 255, 255, int(60 * h)))
            brillo.setColorAt(1, QColor(255, 255, 255, 0))
            p.fillRect(r, QBrush(brillo))
        p.restore()

        f = QFont(p.font())
        f.setBold(True)
        f.setPointSizeF(Tema.tam + 1.5)
        p.setFont(f)
        p.setPen(QColor("#ffffff"))
        titulo = p.fontMetrics().elidedText(
            self.nombre, Qt.TextElideMode.ElideRight, int(r.width() - 24))
        p.drawText(QRectF(r.left() + 12, r.bottom() - 54, r.width() - 24, 26),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, titulo)
        f.setBold(False)
        f.setPointSizeF(Tema.tam - 1)
        p.setFont(f)
        p.setPen(QColor(Tema.a1()))
        p.drawText(QRectF(r.left() + 12, r.bottom() - 30, r.width() - 24, 20),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   f"♡ {self.cantidad} capturas")

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(mezclar(QColor(Tema.c("border")), QColor(Tema.a1()), h), 1.5 + 2 * h))
        p.drawPath(camino)


ORDENES_BIB = ("Orden manual", "Nombre A-Z", "Nombre Z-A", "Recién agregadas",
               "Más capturas", "Más horas jugadas", "Más recientes")
# nombres antiguos de ajustes ya guardados -> nombre nuevo
ORDENES_BIB_ANTIGUOS = {"Terminadas recientemente": "Más recientes"}
FILTROS_BIB = ("Todas", "En curso", "Terminadas", "Sin empezar", "Sin portada")


def clave_alfabetica(nombre):
    """Orden de diccionario: sin tildes ni mayúsculas (Álvaro va junto a Alvaro)."""
    import unicodedata
    t = unicodedata.normalize("NFKD", nombre or "")
    return "".join(c for c in t if not unicodedata.combining(c)).casefold()


class GridTarjetas(QWidget):
    """Rejilla que reorganiza sus tarjetas y permite reordenarlas arrastrando."""
    reordenado = Signal(list)   # ids de novelas en el nuevo orden

    def __init__(self, ratio=1.38):
        super().__init__()
        self.ratio = ratio
        self.min_w = 220
        self.items = []
        self.scroll = None          # el QScrollArea que la contiene (para el auto-scroll)
        self._geo = (1, 220, 300, 14)
        self._arr = None
        self._ins = None
        self._off = QPoint()

    def poner(self, widgets):
        if self.items == widgets:
            return
        self._arr = None
        self._ins = None
        for w in set(self.items) - set(widgets):
            w.hide()
        self.items = widgets
        for w in widgets:
            nuevo = w.parent() is not self
            if nuevo:
                w.setParent(self)
            if nuevo and hasattr(w, "arrastre"):
                w.arrastre.connect(self._al_arrastrar)
                w.soltado.connect(self._al_soltar)
            w.show()
        self.relayout()

    def relayout(self):
        if not self.items:
            self.setMinimumHeight(0)
            return
        esp = 14
        ancho = max(self.width(), self.min_w)
        cols = max(1, (ancho + esp) // (self.min_w + esp))
        w = (ancho - esp * (cols - 1)) // cols
        h = int(w * self.ratio)
        self._geo = (cols, w, h, esp)
        for i, wd in enumerate(self.items):
            wd.setFixedSize(w, h)
            if wd is self._arr:
                continue
            wd.move((i % cols) * (w + esp), (i // cols) * (h + esp))
        self.setMinimumHeight(ceil(len(self.items) / cols) * (h + esp))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.relayout()

    # --- reordenar arrastrando tarjetas
    def _slot(self, i):
        cols, w, h, esp = self._geo
        return QRect((i % cols) * (w + esp), (i // cols) * (h + esp), w, h)

    def _ins_para(self, pt):
        """Hueco (0..n) entre las novelas reales (la tarjeta «Nueva novela» no cuenta)."""
        n = len(self.items)
        if n < 2:
            return 0
        mejor, dmin = 1, None
        for i in range(1, n):
            r = self._slot(i)
            dx = max(r.left() - pt.x(), 0, pt.x() - r.right())
            dy = max(r.top() - pt.y(), 0, pt.y() - r.bottom())
            d = dx * dx + dy * dy
            if dmin is None or d < dmin:
                mejor, dmin = i, d
        return (mejor - 1) if pt.x() < self._slot(mejor).center().x() else mejor

    def _al_arrastrar(self, card, gpos):
        pt = self.mapFromGlobal(gpos)
        if self._arr is not card:
            self._arr = card
            self._off = QPoint(card.width() // 2, card.height() // 2)
            card.raise_()
            card.setCursor(Qt.CursorShape.ClosedHandCursor)
        card.move(pt - self._off)
        self._ins = self._ins_para(pt)
        self.update()
        if self.scroll is not None:
            vp = self.scroll.viewport()
            y = vp.mapFromGlobal(gpos).y()
            barra = self.scroll.verticalScrollBar()
            if y < 40:
                barra.setValue(barra.value() - 22)
            elif y > vp.height() - 40:
                barra.setValue(barra.value() + 22)

    def _al_soltar(self, card, gpos):
        ins = self._ins_para(self.mapFromGlobal(gpos))
        self._arr = None
        self._ins = None
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        reales = [w for w in self.items if not w.nueva]
        ids = [w.juego_id for w in reales]
        nuevo = list(ids)
        if card in reales:
            k = reales.index(card)
            nuevo.pop(k)
            nuevo.insert(ins - 1 if k < ins else ins, card.juego_id)
        self.relayout()
        self.update()
        if nuevo != ids:
            self.reordenado.emit(nuevo)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._arr is None or self._ins is None or len(self.items) < 2:
            return
        esp = self._geo[3]
        reales = len(self.items) - 1
        if self._ins < reales:
            r = self._slot(self._ins + 1)
            x = r.left() - esp / 2
        else:
            r = self._slot(len(self.items) - 1)
            x = r.right() + esp / 2
        x = max(3.0, min(self.width() - 3.0, x))
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QLinearGradient(x, r.top(), x, r.bottom())
        g.setColorAt(0, QColor(Tema.a1()))
        g.setColorAt(1, QColor(Tema.a2()))
        pen = QPen(QBrush(g), 5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(x, r.top() + 10), QPointF(x, r.bottom() - 10))
        p.end()


class Ecualizador(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(46, 30)
        self.v = [0.2] * 5
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def activar(self, on):
        if on:                                   # se anima SOLO mientras suena la música
            self.timer.start(95)
        else:
            self.timer.stop()
            self.v = [0.2] * 5
            self.update()

    def _tick(self):
        self.v = [random.uniform(0.2, 1.0) for _ in self.v]
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        for i, v in enumerate(self.v):
            alto = max(4, int(self.height() * v))
            p.setBrush(QColor(Tema.a1() if i % 2 == 0 else Tema.a2()))
            p.drawRoundedRect(QRectF(i * 9, self.height() - alto, 6, alto), 3, 3)


class IconoVolumen(QWidget):
    """Altavoz dibujado a mano que refleja el volumen; un clic silencia / reactiva."""
    clic = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(28, 28)
        self.nivel = MUSICA_VOLUMEN
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def poner(self, nivel):
        self.nivel = nivel
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clic.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        clave = "vol0" if self.nivel == 0 else ("vol1" if self.nivel < 50 else "vol2")
        color = QColor(Tema.c("muted") if self.nivel == 0 else Tema.c("text"))
        dibujar_icono(p, clave, QPointF(self.width() / 2, self.height() / 2), 18, color)


class Disco(QWidget):
    """Disco giratorio con la portada de la novela que está sonando."""
    LADO = 52

    def __init__(self):
        super().__init__()
        self.setFixedSize(self.LADO, self.LADO)
        self.pm = avatar("", self.LADO - 10)
        self.ang = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def poner(self, portada):
        self.pm = avatar(portada, self.LADO - 10)
        self.update()

    def activar(self, on):
        if on:                                   # gira SOLO mientras suena la música
            self.timer.start(66)
        else:
            self.timer.stop()

    def _tick(self):
        self.ang = (self.ang + 5) % 360
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        L = self.LADO
        c = L / 2
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        # halo
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(5, 0, -1):
            p.setBrush(con_alfa(a1, 10))
            p.drawEllipse(QRectF(2 - i * 0.6, 2 - i * 0.6, L - 4 + i * 1.2, L - 4 + i * 1.2))
        # portada girando
        p.save()
        p.translate(c, c)
        p.rotate(self.ang)
        lado = self.pm.width() / max(1.0, self.pm.devicePixelRatio())
        p.drawPixmap(QPointF(-lado / 2, -lado / 2), self.pm)
        p.restore()
        # surcos y anillo degradado
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        for rad in (c - 12, c - 18):
            p.drawEllipse(QPointF(c, c), rad, rad)
        gr = QLinearGradient(0, 0, L, L)
        gr.setColorAt(0, a1)
        gr.setColorAt(1, a2)
        p.setPen(QPen(QBrush(gr), 3))
        p.drawEllipse(QRectF(3, 3, L - 6, L - 6))
        # centro
        p.setPen(QPen(QColor(255, 255, 255, 140), 1))
        p.setBrush(QColor(Tema.c("panel_solid")))
        p.drawEllipse(QPointF(c, c), 6, 6)


class Toast(QLabel):
    """Aviso flotante que aparece y se desvanece."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.ef = QGraphicsOpacityEffect(self)
        self.ef.setOpacity(0.0)
        self.setGraphicsEffect(self.ef)
        self.an = QPropertyAnimation(self.ef, b"opacity", self)
        self.an.finished.connect(self._fin)
        self.salida = False
        self.espera = QTimer(self)
        self.espera.setSingleShot(True)
        self.espera.timeout.connect(self._ocultar)
        self.hide()

    def mostrar(self, texto, ms=3400):
        self.salida = False
        self.setText(texto)
        self.adjustSize()
        pw, ph = self.parent().width(), self.parent().height()
        self.move(max(10, (pw - self.width()) // 2), ph - self.height() - 120)
        self.show()
        self.raise_()
        self.an.stop()
        self.an.setDuration(260 if Tema.anim else 1)
        self.an.setStartValue(self.ef.opacity())
        self.an.setEndValue(1.0)
        self.an.start()
        self.espera.start(ms)

    def _ocultar(self):
        self.salida = True
        self.an.stop()
        self.an.setDuration(420 if Tema.anim else 1)
        self.an.setStartValue(self.ef.opacity())
        self.an.setEndValue(0.0)
        self.an.start()

    def _fin(self):
        if self.salida:
            self.hide()


class EfectoClic(QWidget):
    """Capa transparente que dibuja chispas al hacer clic."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.chispas = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def burst(self, pos):
        for _ in range(14):
            ang = random.uniform(0, 2 * pi)
            v = random.uniform(2, 6)
            self.chispas.append([pos.x(), pos.y(), cos(ang) * v, sin(ang) * v,
                                 1.0, random.choice([0, 1]), random.uniform(6, 11)])
        if not self.timer.isActive():
            self.timer.start(16)

    def _tick(self):
        for c in self.chispas:
            c[0] += c[2]
            c[1] += c[3]
            c[3] += 0.15
            c[2] *= 0.97
            c[4] -= 0.035
        self.chispas = [c for c in self.chispas if c[4] > 0]
        if not self.chispas:
            self.timer.stop()
        self.update()

    def paintEvent(self, e):
        if not self.chispas:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for x, y, _vx, _vy, vida, col, tam in self.chispas:
            color = QColor(Tema.a1() if col == 0 else Tema.a2())
            color.setAlpha(int(255 * max(0.0, vida)))
            p.setPen(color)
            f = QFont(p.font())
            f.setPixelSize(max(6, int(tam * 2 * vida + 4)))
            p.setFont(f)
            p.drawText(QRectF(x - 20, y - 20, 40, 40), Qt.AlignmentFlag.AlignCenter, "✦")


class Particula:
    __slots__ = ("x", "y", "vx", "vy", "t", "rot", "vrot", "fase", "col")


class FondoWidget(QWidget):
    """Contenedor principal: fondo personalizable, decoración estática y personaje.
    Todo se dibuja UNA sola vez en una caché (sin temporizadores): no consume nada al usar la app."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self._fondo_pm = None
        self._fondo_clave = None
        self.timer = QTimer(self)          # ya no se usa; se conserva por compatibilidad
        self.overlay = EfectoClic(self)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.overlay.setGeometry(self.rect())

    def reiniciar_particulas(self):
        self.update()                      # la decoración cambia sola: su configuración está en la clave

    def _decoracion(self, p, W, H):
        """Pétalos / estrellas / corazones / burbujas repartidos de forma fija (misma semilla)."""
        tipo, n = Tema.particulas, Tema.cantidad
        if tipo == "Ninguno" or n <= 0:
            return
        rng = random.Random(20240)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for _ in range(n):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            t = rng.uniform(6, 15)
            rot = rng.uniform(0, 360)
            col = a1 if rng.random() < 0.5 else a2
            alfa = rng.randint(40, 130)
            p.save()
            p.translate(x, y)
            p.rotate(rot)
            if tipo == "Pétalos":
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(con_alfa(col, alfa))
                p.drawEllipse(QRectF(-t, -t * 0.5, t * 2, t))
            elif tipo == "Burbujas":
                p.setPen(QPen(con_alfa(col, alfa), 1.5))
                p.setBrush(con_alfa(col, 28))
                p.drawEllipse(QRectF(-t, -t, t * 2, t * 2))
                p.setPen(Qt.PenStyle.NoPen)                  # reflejo
                p.setBrush(QColor(255, 255, 255, 70))
                p.drawEllipse(QRectF(-t * 0.55, -t * 0.6, t * 0.5, t * 0.35))
            else:
                p.setPen(con_alfa(col, alfa + 40))
                f = QFont(p.font())
                f.setPixelSize(int(t * 2))
                p.setFont(f)
                p.drawText(QRectF(-t * 2, -t * 2, t * 4, t * 4),
                           int(Qt.AlignmentFlag.AlignCenter), "✦" if tipo == "Estrellas" else "♥")
            p.restore()
        p.restore()

    def _fondo_estatico(self):
        """Color de fondo, imagen o degradados, decoración y mascota: se redibujan solo si algo cambia."""
        W, H = max(1, self.width()), max(1, self.height())
        dpr = self.devicePixelRatioF()
        clave = (W, H, dpr, Tema.nombre, Tema.a1(), Tema.a2(), Tema.fondo, Tema.fondo_vis,
                 Tema.mascota, Tema.particulas, Tema.cantidad)
        if clave == self._fondo_clave and self._fondo_pm is not None:
            return self._fondo_pm
        lienzo = QPixmap(int(W * dpr), int(H * dpr))
        lienzo.setDevicePixelRatio(dpr)
        p = QPainter(lienzo)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(QRectF(0, 0, W, H), QColor(Tema.c("bg")))
        if Tema.fondo and Path(Tema.fondo).exists():
            pm = CACHE_GRANDE.obtener(Tema.fondo, 2200)
            if not pm.isNull():
                p.setOpacity(Tema.fondo_vis / 100)
                dibujar_cover(p, QRectF(0, 0, W, H), pm, 0)
                p.setOpacity(1)
        else:
            for (x, y, rad, col, al) in (
                (0.1, 0.1, 0.55, Tema.a1(), 70),
                (0.95, 0.85, 0.6, Tema.a2(), 60),
                (0.7, 0.05, 0.35, Tema.a2(), 35),
                (0.35, 0.95, 0.40, Tema.a1(), 28),
            ):
                g = QRadialGradient(QPointF(W * x, H * y), max(W, H) * rad)
                g.setColorAt(0, con_alfa(col, al))
                g.setColorAt(1, con_alfa(col, 0))
                p.fillRect(QRectF(0, 0, W, H), QBrush(g))

        self._decoracion(p, W, H)

        if Tema.mascota and Path(Tema.mascota).exists():
            pm = CACHE_GRANDE.obtener(Tema.mascota, 1200)
            if not pm.isNull():
                alto = min(int(H * 0.6), pm.height())
                pm = pm.scaledToHeight(alto, Qt.TransformationMode.SmoothTransformation)
                p.drawPixmap(W - pm.width() - 20, H - pm.height() - 20, pm)
        p.end()
        self._fondo_pm, self._fondo_clave = lienzo, clave
        return lienzo

    def paintEvent(self, e):
        p = QPainter(self)
        p.drawPixmap(0, 0, self._fondo_estatico())


class Cabecera(QFrame):
    """Fondo temático de la barra de la biblioteca."""

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radio = Tema.radio + 6
        camino = QPainterPath()
        camino.addRoundedRect(r, radio, radio)
        p.save()
        p.setClipPath(camino)
        g = QLinearGradient(r.topLeft(), r.topRight())
        g.setColorAt(0, con_alfa(Tema.a1(), 120))
        g.setColorAt(1, con_alfa(Tema.a2(), 120))
        p.fillRect(r, QBrush(g))
        if Tema.cabecera:
            banner = CACHE_GRANDE.obtener_diferido(Tema.cabecera, 1500, self)
            if not banner.isNull():
                dibujar_cover(p, r, banner, 0)
        vel = QLinearGradient(r.topLeft(), r.topRight())
        vel.setColorAt(0, con_alfa(Tema.c("bg"), 235))
        vel.setColorAt(0.55, con_alfa(Tema.c("bg"), 110))
        vel.setColorAt(1, con_alfa(Tema.c("bg"), 30))
        p.fillRect(r, QBrush(vel))
        p.restore()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(Tema.c("border")), 1.2))
        p.drawPath(camino)
        p.end()


# =========================================================
# GALERIA (lista + delegado con miniaturas adaptables)
# =========================================================

def par_galeria(clave):
    """Pareja de colores pastel estable para cada captura (según su ruta)."""
    pares = list(ACENTOS.values())
    a, b = pares[sum(map(ord, str(clave))) % len(pares)]
    return QColor(a), QColor(b)


class DelegadoMiniatura(QStyledItemDelegate):
    """Tarjeta de captura: sombra, borde degradado, brillo y elevación al pasar el ratón,
    y aparición escalonada al cargar. Las animaciones las lleva ListaGaleria."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tam = QSize(260, 200)

    def sizeHint(self, option, index):
        return self.tam

    def paint(self, p, option, index):
        datos = index.data(Qt.ItemDataRole.UserRole)
        if not datos:
            return
        vista = option.widget
        fila = index.row()
        h = vista.progreso_hover(fila) if hasattr(vista, "progreso_hover") else 0.0
        ent = vista.progreso_entrada(fila) if hasattr(vista, "progreso_entrada") else 1.0
        if ent <= 0.0:
            return
        ease = 1 - (1 - ent) ** 3
        sel = bool(option.state & QStyle.StateFlag.State_Selected)
        radio = Tema.radio
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        borde = QColor(Tema.c("border"))
        card = QColor(Tema.c("card"))
        ca, cb = par_galeria(datos["ruta"])

        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setOpacity(ease)
        r = QRectF(option.rect).adjusted(9, 9, -9, -9)
        r.translate(0, (1 - ease) * 16)
        camino = QPainterPath()
        camino.addRoundedRect(r, radio, radio)

        # sombra suave + resplandor de acento
        for i in (5, 2):
            sh = QPainterPath()
            sh.addRoundedRect(r.adjusted(-i, -i + 4, i, i + 4), radio + i, radio + i)
            p.fillPath(sh, QColor(0, 0, 0, int(8 + 5 * h)))
        brillo = max(h, 0.7 if sel else 0.0)
        if brillo > 0.02:
            for i in (6, 3):
                gl = QPainterPath()
                gl.addRoundedRect(r.adjusted(-i, -i, i, i), radio + i, radio + i)
                col = QColor(ca)
                col.setAlpha(int(16 * brillo * (11 - i) / 10))
                p.fillPath(gl, col)

        # fondo de la tarjeta
        fondo = QLinearGradient(r.topLeft(), r.bottomRight())
        fondo.setColorAt(0, mezclar(card, ca, 0.22 + 0.08 * h))
        fondo.setColorAt(1, mezclar(card, cb, 0.36 + 0.10 * h))
        p.fillPath(camino, QBrush(fondo))

        # imagen (contenida, con ligero zoom al pasar el ratón)
        zona = r.adjusted(10, 10, -10, -10)
        pm = CACHE_MINI.obtener_diferido(
            datos["ruta"], 480, option.widget.viewport() if option.widget else None)
        if not pm.isNull():
            esc = min(zona.width() / pm.width(), zona.height() / pm.height())
            w, hh = pm.width() * esc, pm.height() * esc
            dest = QRectF(zona.x() + (zona.width() - w) / 2,
                          zona.y() + (zona.height() - hh) / 2, w, hh)
            p.save()
            ruta_img = QPainterPath()
            ruta_img.addRoundedRect(dest, radio * 0.6, radio * 0.6)
            p.setClipPath(ruta_img)
            p.drawPixmap(dest, pm, QRectF(pm.rect()))
            if h > 0.02:                           # velo de luz suave al pasar el ratón (estático)
                g = QLinearGradient(dest.topLeft(), dest.bottomRight())
                g.setColorAt(0, QColor(255, 255, 255, int(46 * h)))
                g.setColorAt(0.55, QColor(255, 255, 255, 0))
                p.fillRect(dest, QBrush(g))
            if Tema.anim and 0.03 < h < 0.97:      # destello que cruza la imagen
                bx = dest.left() - dest.width() * 0.3 + dest.width() * 1.6 * h
                g = QLinearGradient(bx - 40, dest.top(), bx + 40, dest.bottom())
                g.setColorAt(0, QColor(255, 255, 255, 0))
                g.setColorAt(0.5, QColor(255, 255, 255, int(70 * sin(pi * h))))
                g.setColorAt(1, QColor(255, 255, 255, 0))
                p.fillRect(dest, QBrush(g))
            pie = datos.get("pie")
            if pie:                                 # «Novela · Heroína» (sección Favoritos)
                franja = QRectF(dest.left(), dest.bottom() - 28, dest.width(), 28)
                g = QLinearGradient(franja.topLeft(), franja.bottomLeft())
                g.setColorAt(0, QColor(15, 8, 25, 0))
                g.setColorAt(1, QColor(15, 8, 25, 215))
                p.fillRect(franja, QBrush(g))
                f = QFont(p.font())
                f.setPointSizeF(max(7.5, Tema.tam - 1.5))
                f.setBold(True)
                p.setFont(f)
                p.setPen(QColor("#ffffff"))
                txt = QFontMetrics(f).elidedText(
                    pie, Qt.TextElideMode.ElideRight, int(franja.width() - 16))
                p.drawText(franja.adjusted(8, 0, -8, -4),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, txt)
            p.restore()

        if sel:
            p.fillPath(camino, QColor(a1.red(), a1.green(), a1.blue(), 26))

        # borde degradado + filete interior
        fuerza = max(h, 1.0 if sel else 0.0)
        bord = QLinearGradient(r.topLeft(), r.bottomRight())
        fuerza_c = max(fuerza, 0.65)
        bord.setColorAt(0, mezclar(borde, ca, fuerza_c))
        bord.setColorAt(1, mezclar(borde, cb, fuerza_c))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QBrush(bord), 3.2 if sel else 1.4 + 1.2 * h))
        p.drawPath(camino)
        inner = QPainterPath()
        inner.addRoundedRect(r.adjusted(4, 4, -4, -4), max(2, radio - 4), max(2, radio - 4))
        p.setPen(QPen(QColor(255, 255, 255, 30 + int(60 * h)), 1))
        p.drawPath(inner)

        # insignias: favorito (★) y seleccionada (✓)
        if datos.get("favorito"):
            c = QRectF(r.right() - 38, r.top() + 10, 27, 27)
            g = QLinearGradient(c.topLeft(), c.bottomRight())
            g.setColorAt(0, a1)
            g.setColorAt(1, a2)
            p.setPen(QPen(QColor(255, 255, 255, 220), 1.5))
            p.setBrush(QBrush(g))
            p.drawEllipse(c)
            p.setPen(QColor(TEXTO_SOBRE_ACENTO))
            p.drawText(c, Qt.AlignmentFlag.AlignCenter, "★")
        if sel:
            c = QRectF(r.left() + 11, r.top() + 10, 25, 25)
            p.setPen(QPen(QColor(255, 255, 255, 230), 1.5))
            p.setBrush(a1)
            p.drawEllipse(c)
            p.setPen(QColor(TEXTO_SOBRE_ACENTO))
            p.drawText(c, Qt.AlignmentFlag.AlignCenter, "✓")
        p.restore()


class ListaGaleria(QListWidget):
    archivos_arrastrados = Signal(list)
    redimensionada = Signal()
    orden_cambiado = Signal(list)   # ids en el nuevo orden

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("galeria")
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)
        self.setWrapping(True)
        self.setSpacing(0)
        self.setUniformItemSizes(True)
        self.setLayoutMode(QListWidget.LayoutMode.Batched)
        self.setBatchSize(100)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # Qt solo recibe archivos soltados desde fuera; el reordenado es propio.
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setAcceptDrops(True)
        self._press_pos = None
        self._reordenando = False
        self._cur = QPoint()
        self._ghost = QPixmap()
        self._ins = None
        self._arrastre_ids = set()
        self._t_scroll = QTimer(self)
        self._t_scroll.setInterval(30)
        self._t_scroll.timeout.connect(self._auto_scroll)
        # --- animaciones de las tarjetas (hover suave + entrada escalonada)
        self._hover_fila = -1
        self._hover = {}
        self._entrada_t0 = 0.0
        self._entrada_activa = False
        self._anim = QTimer(self)
        self._anim.setInterval(16)
        self._anim.timeout.connect(self._tick)

    def progreso_hover(self, fila):
        return self._hover.get(fila, 0.0)

    def progreso_entrada(self, fila):
        if not self._entrada_activa or not Tema.anim:
            return 1.0
        t = (time.monotonic() - self._entrada_t0) * 1000 - min(fila, 14) * 35
        return max(0.0, min(1.0, t / 320))

    def iniciar_entrada(self):
        """Las tarjetas aparecen una tras otra, subiendo y desvaneciéndose."""
        self._hover.clear()
        self._hover_fila = -1
        if Tema.anim:
            self._entrada_t0 = time.monotonic()
            self._entrada_activa = True
            self._anim.start()
        else:
            self._entrada_activa = False
        self.viewport().update()

    # ---------- reordenar arrastrando (con el ratón, sin QDrag) ----------
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            pt = e.position().toPoint()
            self._press_pos = pt if self.indexAt(pt).isValid() else None
        else:
            self._press_pos = None

    def mouseReleaseEvent(self, e):
        if self._reordenando:
            self._terminar_reorden(e.position().toPoint())
            return
        self._press_pos = None
        super().mouseReleaseEvent(e)

    def mouseMoveEvent(self, e):
        pt = e.position().toPoint()
        if self._reordenando:
            self._cur = pt
            self._ins = self._pos_insercion(pt)
            self.viewport().update()
            return
        con_press = (self._press_pos is not None
                     and bool(e.buttons() & Qt.MouseButton.LeftButton))
        if not con_press:
            super().mouseMoveEvent(e)
        idx = self.indexAt(pt)
        fila = idx.row() if idx.isValid() else -1
        if fila != self._hover_fila:
            self._hover_fila = fila
            self._anim.start()
        if con_press and (pt - self._press_pos).manhattanLength() >= QApplication.startDragDistance():
            self._iniciar_reorden()

    def _iniciar_reorden(self):
        pos, self._press_pos = self._press_pos, None
        idx = self.indexAt(pos)
        if not idx.isValid() or not self.item(idx.row()).isSelected():
            return
        rol = Qt.ItemDataRole.UserRole
        self._arrastre_ids = {it.data(rol)["id"] for it in self.selectedItems()}
        datos = self.item(idx.row()).data(rol)
        pm = CACHE_MINI.obtener(datos["ruta"], 220)
        self._ghost = (pm.scaledToWidth(130, Qt.TransformationMode.SmoothTransformation)
                       if not pm.isNull() else QPixmap())
        self._cur = pos
        self._ins = self._pos_insercion(pos)
        self._reordenando = True
        self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
        self._t_scroll.start()
        self.viewport().update()

    def _terminar_reorden(self, pt):
        dentro = self.viewport().rect().contains(pt)
        ins = self._pos_insercion(pt)
        self._reordenando = False
        self._t_scroll.stop()
        self.viewport().unsetCursor()
        self._ghost = QPixmap()
        self._ins = None
        try:   # el release no llegó a Qt: evita que se quede en modo "selección arrastrada"
            self.setState(QAbstractItemView.State.NoState)
        except Exception:
            pass
        sel = set(self._arrastre_ids)
        self._arrastre_ids = set()
        self.viewport().update()
        if not dentro:
            return
        rol = Qt.ItemDataRole.UserRole
        ids = [self.item(i).data(rol)["id"] for i in range(self.count())]
        mover = [i for i in ids if i in sel]
        resto = [i for i in ids if i not in sel]
        k = sum(1 for i in ids[:ins] if i not in sel)
        resto[k:k] = mover
        if mover and resto != ids:
            QTimer.singleShot(0, lambda: self.orden_cambiado.emit(resto))

    def _pos_insercion(self, pt):
        """Hueco (0..count): tarjeta más cercana al cursor; mitad izquierda = antes, derecha = después."""
        n = self.count()
        if n == 0:
            return 0
        mejor, dmin = 0, None
        for i in range(n):
            r = self.visualRect(self.model().index(i, 0))
            dx = max(r.left() - pt.x(), 0, pt.x() - r.right())
            dy = max(r.top() - pt.y(), 0, pt.y() - r.bottom())
            d = dx * dx + dy * dy
            if dmin is None or d < dmin:
                mejor, dmin = i, d
        r = self.visualRect(self.model().index(mejor, 0))
        return mejor if pt.x() < r.center().x() else mejor + 1

    def _auto_scroll(self):
        pt = self.viewport().mapFromGlobal(QCursor.pos())
        if not self.viewport().rect().contains(pt):
            if self._ins is not None:
                self._ins = None
                self.viewport().update()
            return
        h, m = self.viewport().height(), 50
        barra = self.verticalScrollBar()
        if pt.y() < m:
            barra.setValue(barra.value() - 22)
        elif pt.y() > h - m:
            barra.setValue(barra.value() + 22)
        self._cur = pt
        self._ins = self._pos_insercion(pt)
        self.viewport().update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if not self._reordenando or self.count() == 0:
            return
        p = QPainter(self.viewport())
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._ins is not None:
            n = self.count()
            if self._ins < n:
                r = self.visualRect(self.model().index(self._ins, 0))
                x = r.left() + 4
            else:
                r = self.visualRect(self.model().index(n - 1, 0))
                x = r.right() - 4
            g = QLinearGradient(x, r.top(), x, r.bottom())
            g.setColorAt(0, QColor(Tema.a1()))
            g.setColorAt(1, QColor(Tema.a2()))
            pen = QPen(QBrush(g), 5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(x, r.top() + 12), QPointF(x, r.bottom() - 12))
        if not self._ghost.isNull():
            p.setOpacity(0.8)
            p.drawPixmap(self._cur - QPoint(self._ghost.width() // 2,
                                            self._ghost.height() // 2), self._ghost)
        p.end()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._hover_fila = -1
        self._anim.start()

    def _tick(self):
        activo = False
        filas = set(self._hover)
        if self._hover_fila >= 0:
            filas.add(self._hover_fila)
        for f in filas:
            v = self._hover.get(f, 0.0)
            objetivo = 1.0 if f == self._hover_fila else 0.0
            if Tema.anim:
                nv = v + (objetivo - v) * 0.28
                if abs(nv - objetivo) < 0.01:
                    nv = objetivo
            else:
                nv = objetivo
            if nv <= 0.0:
                self._hover.pop(f, None)
            else:
                self._hover[f] = nv
            if nv != objetivo:
                activo = True
        if self._entrada_activa:
            if (time.monotonic() - self._entrada_t0) * 1000 > 320 + 14 * 35 + 60:
                self._entrada_activa = False
            else:
                activo = True
        if self._entrada_activa:
            self.viewport().update()
        else:
            for fila in filas:
                indice = self.model().index(fila, 0)
                if indice.isValid():
                    self.viewport().update(self.visualRect(indice))
        if not activo:
            self._anim.stop()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.redimensionada.emit()

    # ---------- archivos soltados desde el Explorador ----------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            rutas = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
            self.archivos_arrastrados.emit(rutas)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


# =========================================================
# VISOR CON ZOOM (rueda, arrastre, ajuste automático)
# =========================================================

class VistaZoom(QGraphicsView):
    zoom_cambiado = Signal(float)
    redimensionada = Signal()

    def __init__(self):
        super().__init__()
        self.escena = QGraphicsScene(self)
        self.setScene(self.escena)
        self.item = QGraphicsPixmapItem()
        self.item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.escena.addItem(self.item)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHints(QPainter.RenderHint.SmoothPixmapTransform
                            | QPainter.RenderHint.Antialiasing)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setBackgroundBrush(QColor(Tema.c("bg")))
        self.modo_ajuste = True

    def escala(self):
        return self.transform().m11()

    def poner(self, pm):
        self.item.setPixmap(pm)
        self.escena.setSceneRect(self.item.boundingRect())
        self.ajustar()

    def ajustar(self):
        self.modo_ajuste = True
        self.resetTransform()
        if not self.item.pixmap().isNull():
            self.fitInView(self.item, Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_cambiado.emit(self.escala())

    def cien(self):
        self.modo_ajuste = False
        self.resetTransform()
        self.zoom_cambiado.emit(self.escala())

    def zoom(self, factor):
        self.modo_ajuste = False
        nuevo = max(0.05, min(16.0, self.escala() * factor))
        self.scale(nuevo / self.escala(), nuevo / self.escala())
        self.zoom_cambiado.emit(self.escala())

    def wheelEvent(self, e):
        self.zoom(1.15 if e.angleDelta().y() > 0 else 1 / 1.15)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.modo_ajuste:
            self.ajustar()
        self.redimensionada.emit()

    def mouseDoubleClickEvent(self, e):
        self.cien() if self.modo_ajuste else self.ajustar()


# =========================================================
# TOP HEROÍNAS (podio con trofeos; se reordena arrastrando)
# =========================================================

MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

PODIO = {
    1: ("#ffd54a", "#f08a00", "CAMPEONA"),
    2: ("#e6ecf5", "#8794ab", "SUBCAMPEONA"),
    3: ("#eba570", "#a35a28", "TERCER LUGAR"),
}


CAT_COLOR = {"CG normal": "#6ea8fe", "CG H": "#ff6fa5", "SD": "#ffc857", "No-CG": "#7bd88f"}
ABREV_CAT = {"CG normal": "CG", "CG H": "H", "SD": "SD", "No-CG": "No-CG"}


def fmt_fecha(iso):
    """'2026-10-05' -> '05 oct 2026' (vacío si no hay fecha válida)."""
    try:
        d = datetime.date.fromisoformat(str(iso))
    except (TypeError, ValueError):
        return ""
    return f"{d.day:02d} {MESES_ES[d.month - 1][:3]} {d.year}"


def calcular_dias(inicio, fin):
    """(días, en_curso). Cuenta el día de inicio y el de fin (empezar y terminar el mismo día
    = 1 día). Sin fecha de fin cuenta hasta hoy. (None, _) si no se puede calcular."""
    try:
        d1 = datetime.date.fromisoformat(str(inicio))
    except (TypeError, ValueError):
        return None, False
    d2 = None
    if fin:
        try:
            d2 = datetime.date.fromisoformat(str(fin))
        except (TypeError, ValueError):
            return None, False
    en_curso = d2 is None
    if en_curso:
        d2 = datetime.date.today()
    dias = (d2 - d1).days + 1
    return (dias, en_curso) if dias >= 1 else (None, en_curso)


def fmt_horas(h):
    """42 -> '42 h' · 42.5 -> '42,5 h' (vacío si no hay horas anotadas)."""
    try:
        h = float(h)
    except (TypeError, ValueError):
        return ""
    if h <= 0:
        return ""
    return f"{int(round(h))} h" if abs(h - round(h)) < 0.05 else f"{h:.1f} h".replace(".", ",")


class CronologiaVista(QWidget):
    """Panel «Cronología»: tus novelas sobre una línea de tiempo según las fechas de inicio y fin
    que anotaste, con horas jugadas, ritmo mensual y récords. Es estático (sin temporizadores)."""
    abrir = Signal(int)
    FILA = 50
    ETQ = 250
    TARJ = 92

    def __init__(self):
        super().__init__()
        self.items, self.records, self.mensual, self.stats = [], [], [], {}
        self._rects = []
        self._hover = -1
        self.setMouseTracking(True)
        self.poner([])

    # ---------------- datos
    def poner(self, filas):
        """filas: (id, nombre, portada, portada_enc, horas, fecha_inicio, fecha_fin, capturas,
        excluir_fechas, excluir_horas, nota)"""
        hoy = datetime.date.today()
        un_dia = datetime.timedelta(days=1)
        items = []
        ids_omit, ids_inc = set(), set()
        for jid, nombre, portada, enc, horas, ini, fin, caps, ex_f, ex_h, nota in filas:
            if ex_f:                                   # «no recuerdo las fechas»
                ids_omit.add(jid)
                continue
            try:
                d1 = datetime.date.fromisoformat(str(ini))
            except (TypeError, ValueError):
                continue
            try:
                d2 = datetime.date.fromisoformat(str(fin)) if fin else None
            except (TypeError, ValueError):
                d2 = None
            curso = False
            if d2 is None:                             # novela actual: dura hasta hoy
                curso = True
                d2 = max(hoy, d1)
            elif d2 < d1:                              # fechas incoherentes: no se puede dibujar
                ids_inc.add(jid)
                continue
            dias = (d2 - d1).days + 1
            h = 0.0 if ex_h else float(horas or 0)
            items.append(dict(id=jid, nombre=nombre, portada=portada, enc=parse_enc(enc), h=h,
                              d1=d1, d2=d2, dias=dias, curso=curso, caps=int(caps or 0),
                              nota=float(nota or 0),
                              hpd=(h / dias if h > 0 else 0.0)))
        items.sort(key=lambda i: (i["d1"], i["d2"], clave_alfabetica(i["nombre"])))
        self.items = items
        # una novela por volúmenes cuenta como UNA novela en las estadísticas
        ids_con = {i["id"] for i in items}
        omitidas = len(ids_omit - ids_con)
        incompletas = len(ids_inc - ids_con - ids_omit)
        n_novelas = len({f[0] for f in filas})

        # días con alguna novela en marcha y la pausa más larga entre novelas
        fusion, pausa, pausa_ent = [], 0, ("", "")
        for it in items:
            if fusion and it["d1"] <= fusion[-1][1] + un_dia:
                if it["d2"] > fusion[-1][1]:
                    fusion[-1][1], fusion[-1][2] = it["d2"], it["nombre"]
            else:
                if fusion:
                    hueco = (it["d1"] - fusion[-1][1]).days - 1
                    if hueco > pausa:
                        pausa, pausa_ent = hueco, (fusion[-1][2], it["nombre"])
                fusion.append([it["d1"], it["d2"], it["nombre"]])
        dias_activos = sum((b - a).days + 1 for a, b, _ in fusion)

        # novelas jugadas a la vez (máximo)
        ev = []
        for it in items:
            ev.append((it["d1"], 1))
            ev.append((it["d2"] + un_dia, -1))
        ev.sort()
        act = simult = 0
        for _, delta in ev:
            act += delta
            simult = max(simult, act)

        # horas por mes (las horas de cada novela se reparten entre sus días)
        meses = {}
        for it in items:
            if it["h"] <= 0:
                continue
            por_dia = it["h"] / it["dias"]
            d = it["d1"]
            while d <= it["d2"]:
                k = (d.year, d.month)
                meses[k] = meses.get(k, 0.0) + por_dia
                d += un_dia
        self.mensual = []
        if meses:
            y, m = min(meses)
            y2, m2 = max(meses)
            while (y, m) <= (y2, m2):
                self.mensual.append((y, m, meses.get((y, m), 0.0)))
                m += 1
                if m > 12:
                    y, m = y + 1, 1
            self.mensual = self.mensual[-24:]

        horas_fechas = sum(i["h"] for i in items)
        self.stats = dict(
            total=n_novelas - omitidas, con_fechas=len(ids_con),
            omitidas=omitidas, incompletas=incompletas,
            terminadas=len({i["id"] for i in items if not i["curso"]}),
            curso=len({i["id"] for i in items if i["curso"]}),
            horas=sum(float(f[4] or 0) for f in filas if not f[9]),
            sin_horas=len({f[0] for f in filas if not f[9] and not (f[4] or 0)}),
            dias=dias_activos, simult=simult,
            ritmo=(horas_fechas / dias_activos if dias_activos and horas_fechas else 0.0),
            desde=(min(i["d1"] for i in items) if items else None),
            hasta=(max(i["d2"] for i in items) if items else None))

        # récords
        def coma(x, dec=1):
            return f"{x:.{dec}f}".replace(".", ",")
        rec = []
        con_h = [i for i in items if i["h"] > 0]
        if con_h:
            i = max(con_h, key=lambda i: i["h"])
            rec.append(("🏆", "La que más horas llevó", fmt_horas(i["h"]), i["nombre"], i["id"]))
            i = max(con_h, key=lambda i: i["hpd"])
            rec.append(("🔥", "Tu maratón más intensa", f"{coma(i['hpd'])} h/día", i["nombre"], i["id"]))
        if items:
            i = max(items, key=lambda i: i["dias"])
            rec.append(("🐢", "La más larga en días", f"{i['dias']} días", i["nombre"], i["id"]))
        ter = [i for i in items if not i["curso"]]
        if ter:
            i = min(ter, key=lambda i: i["dias"])
            rec.append(("⚡", "Terminada más rápido", f"{i['dias']} {'día' if i['dias'] == 1 else 'días'}",
                        i["nombre"], i["id"]))
        cc = [i for i in con_h if i["caps"] > 0]
        if cc:
            i = max(cc, key=lambda i: i["caps"] / i["h"])
            rec.append(("📸", "Más capturas por hora", f"{coma(i['caps'] / i['h'])} capt./h",
                        i["nombre"], i["id"]))
        if pausa > 0:
            rec.append(("🌙", "Mayor pausa entre novelas", f"{pausa} días",
                        f"{pausa_ent[0]} → {pausa_ent[1]}", -1))
        self.records = rec
        self._hover = -1
        self._ajustar()
        self.update()

    # ---------------- geometría
    def _calc(self, W):
        PAD = 6
        cols_s = max(1, min(5, (W - 2 * PAD + 12) // 180))
        L = {"PAD": PAD, "cols_s": cols_s}
        y = 4
        L["gantt_t"] = y
        y += 36
        L["gantt"] = y
        y += (34 + len(self.items) * self.FILA + 10) if self.items else 90
        y += 14
        L["mes_t"] = y
        y += 36
        L["mes"] = y
        y += 190
        L["alto"] = y + 16
        return L

    def _ajustar(self):
        h = self._calc(max(self.width(), 600))["alto"]
        if self.minimumHeight() != h:
            self.setMinimumHeight(h)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._ajustar()

    # ---------------- utilidades de dibujo
    def _texto(self, p, rect, txt, pt, color, bold=False, alin=Qt.AlignmentFlag.AlignLeft):
        f = QFont(Tema.fuente)
        f.setPointSizeF(pt)
        f.setBold(bold)
        p.setFont(f)
        p.setPen(color)
        txt = QFontMetrics(f).elidedText(txt, Qt.TextElideMode.ElideRight, int(rect.width()))
        p.drawText(rect, int(alin | Qt.AlignmentFlag.AlignVCenter), txt)

    def _titulo(self, p, y, txt, der=""):
        W = self.width()
        a1 = QColor(Tema.a1())
        self._texto(p, QRectF(10, y, W - 20, 28), txt, Tema.tam + 3, QColor(Tema.c("text")), True)
        p.setPen(QPen(a1, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(12, y + 31), QPointF(54, y + 31))
        if der:
            self._texto(p, QRectF(W * 0.35, y, W * 0.65 - 12, 28), der, Tema.tam - 0.5,
                        QColor(Tema.c("muted")), False, Qt.AlignmentFlag.AlignRight)

    def _tarjeta(self, p, r, emoji, titulo, valor, sub, a1, a2):
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        mu = QColor(Tema.c("muted"))
        cam = QPainterPath()
        cam.addRoundedRect(r, Tema.radio, Tema.radio)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, mezclar(card, a1, 0.16))
        g.setColorAt(1, mezclar(card, a2, 0.16))
        p.fillPath(cam, QBrush(g))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(mezclar(borde, a1, 0.35), 1.3))
        p.drawPath(cam)
        d = r.adjusted(16, 8, -12, -8)
        self._texto(p, QRectF(d.left(), d.top(), d.width(), 20), f"{emoji}  {titulo}", Tema.tam - 1, mu)
        self._texto(p, QRectF(d.left(), d.top() + 20, d.width(), 34), valor, Tema.tam + 9, a1, True)
        self._texto(p, QRectF(d.left(), d.top() + 54, d.width(), 18), sub, Tema.tam - 1.5, mu)

    # ---------------- dibujo
    def paintEvent(self, e):
        W = self.width()
        L = self._calc(W)
        PAD = L["PAD"]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        borde = QColor(Tema.c("border"))
        st = self.stats
        self._rects = []

        def coma(x, dec=1):
            return f"{x:.{dec}f}".replace(".", ",")

        # ---- 2) línea de tiempo
        self._titulo(p, L["gantt_t"], "⏳ Línea de tiempo",
                     "clic en una novela para abrirla" if self.items else "")
        gy = L["gantt"]
        if not self.items:
            self._texto(p, QRectF(0, gy, W, 70),
                        "Aún no hay fechas. Abre una novela y pulsa 📅 para anotar cuándo empezaste, "
                        "terminaste y cuántas horas jugaste.",
                        Tema.tam, mu, False, Qt.AlignmentFlag.AlignHCenter)
        else:
            un_dia = datetime.timedelta(days=1)
            hoy = datetime.date.today()
            d_min = min(i["d1"] for i in self.items) - datetime.timedelta(days=5)
            d_max = max(i["d2"] for i in self.items) + datetime.timedelta(days=6)
            span = max(30, (d_max - d_min).days)
            x0, x1 = PAD + self.ETQ, W - PAD - 14
            ancho = max(60.0, x1 - x0)

            def X(d):
                return x0 + (d - d_min).days / span * ancho

            alto_filas = len(self.items) * self.FILA
            base = gy + 34
            # fondo del panel
            panel = QRectF(PAD, gy, W - 2 * PAD, 34 + alto_filas + 6)
            cam = QPainterPath()
            cam.addRoundedRect(panel, Tema.radio, Tema.radio)
            p.fillPath(cam, con_alfa(Tema.c("card"), 150))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(borde, 1.2))
            p.drawPath(cam)
            # meses
            px_mes = ancho * 30.4 / span
            paso = max(1, int(ceil(48 / max(1.0, px_mes))))
            yy, mm, n = d_min.year, d_min.month, 0
            while True:
                d = datetime.date(yy, mm, 1)
                if d > d_max:
                    break
                if d >= d_min:
                    xx = X(d)
                    p.setPen(QPen(con_alfa(borde, 150), 1))
                    p.drawLine(QPointF(xx, gy + 30), QPointF(xx, base + alto_filas))
                    if n % paso == 0:
                        self._texto(p, QRectF(xx + 3, gy + 2, 60, 15), MESES_ES[mm - 1][:3],
                                    Tema.tam - 1.5, mu)
                        if mm == 1 or n == 0:
                            self._texto(p, QRectF(xx + 3, gy + 15, 60, 14), str(yy),
                                        Tema.tam - 1.5, a1, True)
                    n += 1
                mm += 1
                if mm > 12:
                    yy, mm = yy + 1, 1
            # filas
            f_nom = QFont(Tema.fuente)
            for k, it in enumerate(self.items):
                y = base + k * self.FILA
                fila = QRectF(PAD + 2, y, W - 2 * PAD - 4, self.FILA)
                self._rects.append((fila, it["id"], k))
                if k == self._hover:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(con_alfa(a1, 34))
                    p.drawRoundedRect(fila, 10, 10)
                elif k % 2 == 0:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(con_alfa(a1, 10))
                    p.drawRoundedRect(fila, 10, 10)
                pm = CACHE_GRANDE.obtener_diferido(it["portada"], 200, self)
                portada = QRectF(PAD + 10, y + (self.FILA - 36) / 2, 36, 36)
                dibujar_cover(p, portada, pm, 9, it["enc"])
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(con_alfa(a1, 160 if k == self._hover else 80), 1.4))
                p.drawRoundedRect(portada, 9, 9)
                self._texto(p, QRectF(PAD + 54, y + 5, self.ETQ - 62, 22), it["nombre"],
                            Tema.tam, txt, True)
                fin_txt = "en curso" if it["curso"] else fmt_fecha(it["d2"])
                self._texto(p, QRectF(PAD + 54, y + 25, self.ETQ - 62, 18),
                            f"{fmt_fecha(it['d1'])} → {fin_txt}"
                            + (f"   ★ {fmt_nota(it['nota'])}" if it.get("nota") else ""),
                            Tema.tam - 2, mu)
                # barra
                ca, cb = par_galeria(it["nombre"])
                bx0, bx1 = X(it["d1"]), X(it["d2"] + un_dia)
                bw = max(12.0, bx1 - bx0)
                barra = QRectF(bx0, y + 11, bw, self.FILA - 22)
                g = QLinearGradient(barra.topLeft(), barra.topRight())
                g.setColorAt(0, ca)
                g.setColorAt(1, con_alfa(cb, 70) if it["curso"] else cb)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(g))
                p.drawRoundedRect(barra, 9, 9)
                if it["curso"]:
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.setPen(QPen(cb, 1.4, Qt.PenStyle.DashLine))
                    p.drawRoundedRect(barra, 9, 9)
                h_txt = fmt_horas(it["h"])
                variantes = []
                if h_txt:
                    variantes.append(f"⏱ {h_txt} · {it['dias']} d" + ("  ▶" if it["curso"] else ""))
                    variantes.append(f"⏱ {h_txt}")
                variantes.append(f"{it['dias']} d")
                f_nom.setPointSizeF(Tema.tam - 1)
                f_nom.setBold(True)
                fm = QFontMetrics(f_nom)
                puesto = False
                for v_ in variantes:
                    if fm.horizontalAdvance(v_) + 18 <= bw:
                        self._texto(p, barra.adjusted(9, 0, -6, 0), v_, Tema.tam - 1,
                                    QColor(TEXTO_SOBRE_ACENTO), True)
                        puesto = True
                        break
                if not puesto:
                    v_ = variantes[0]
                    tw = fm.horizontalAdvance(v_) + 12
                    if bx0 + bw + 6 + tw < W - 4:
                        self._texto(p, QRectF(bx0 + bw + 6, y + 11, tw, self.FILA - 22), v_,
                                    Tema.tam - 1, txt, True)
                    else:
                        self._texto(p, QRectF(bx0 - tw - 4, y + 11, tw, self.FILA - 22), v_,
                                    Tema.tam - 1, txt, True, Qt.AlignmentFlag.AlignRight)
            # marca de «hoy»
            if d_min <= hoy <= d_max:
                xh = X(hoy)
                p.setPen(QPen(con_alfa(a1, 200), 1.6, Qt.PenStyle.DashLine))
                p.drawLine(QPointF(xh, gy + 28), QPointF(xh, base + alto_filas))
                self._texto(p, QRectF(xh - 30, gy + 14, 60, 14), "hoy", Tema.tam - 2, a1, True,
                            Qt.AlignmentFlag.AlignHCenter)

        # ---- 3) ritmo mensual
        mejor = ""
        if self.mensual and max(m[2] for m in self.mensual) > 0:
            y_, m_, h_ = max(self.mensual, key=lambda m: m[2])
            mejor = f"mejor mes: {MESES_ES[m_ - 1]} {y_} · {fmt_horas(h_)}"
        self._titulo(p, L["mes_t"], "📈 Ritmo mensual (horas)", mejor)
        my = L["mes"]
        marco = QRectF(PAD, my, W - 2 * PAD, 190)
        cam = QPainterPath()
        cam.addRoundedRect(marco, Tema.radio, Tema.radio)
        p.fillPath(cam, con_alfa(Tema.c("card"), 150))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(borde, 1.2))
        p.drawPath(cam)
        if not self.mensual or max(m[2] for m in self.mensual) <= 0:
            self._texto(p, marco, "Anota las horas jugadas de tus novelas (botón 📅 dentro de cada una) "
                        "y aquí verás cuánto jugaste cada mes.", Tema.tam, mu, False,
                        Qt.AlignmentFlag.AlignHCenter)
        else:
            area = QRectF(marco.left() + 14, marco.top() + 26, marco.width() - 28, 190 - 26 - 42)
            mx = max(m[2] for m in self.mensual)
            n = len(self.mensual)
            slot = area.width() / n
            bw = min(52.0, slot * 0.68)
            p.setPen(QPen(con_alfa(borde, 200), 1.2))
            p.drawLine(QPointF(area.left(), area.bottom()), QPointF(area.right(), area.bottom()))
            for k, (y_, m_, h_) in enumerate(self.mensual):
                cx = area.left() + slot * (k + 0.5)
                if h_ > 0:
                    alto = max(4.0, area.height() * h_ / mx)
                    r = QRectF(cx - bw / 2, area.bottom() - alto, bw, alto)
                    g = QLinearGradient(r.topLeft(), r.bottomLeft())
                    g.setColorAt(0, a1)
                    g.setColorAt(1, a2)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QBrush(g))
                    p.drawRoundedRect(r, 6, 6)
                    if slot >= 24:
                        self._texto(p, QRectF(cx - 30, r.top() - 17, 60, 16), str(int(round(h_))),
                                    Tema.tam - 1.5, txt, True, Qt.AlignmentFlag.AlignHCenter)
                nombre_mes = MESES_ES[m_ - 1][:3] if slot >= 30 else MESES_ES[m_ - 1][0].upper()
                self._texto(p, QRectF(cx - 30, area.bottom() + 3, 60, 15), nombre_mes,
                            Tema.tam - 1.5, mu, False, Qt.AlignmentFlag.AlignHCenter)
                if m_ == 1 or k == 0:
                    self._texto(p, QRectF(cx - 30, area.bottom() + 18, 60, 15), str(y_),
                                Tema.tam - 1.5, a1, True, Qt.AlignmentFlag.AlignHCenter)

        p.end()

    # ---------------- ratón
    def mouseMoveEvent(self, e):
        pt = e.position()
        hover, clic = -1, False
        for r, jid, idx in self._rects:
            if r.contains(pt):
                hover, clic = idx, True
                break
        if hover != self._hover:
            self._hover = hover
            self.setCursor(Qt.CursorShape.PointingHandCursor if clic
                           else Qt.CursorShape.ArrowCursor)
            tip = ""
            if 0 <= hover < len(self.items):
                it = self.items[hover]
                fin = "en curso" if it["curso"] else fmt_fecha(it["d2"])
                tip = (f"{it['nombre']}\n📅 {fmt_fecha(it['d1'])} → {fin}  ({it['dias']} días)\n"
                       f"⏱ {fmt_horas(it['h']) or 'sin horas anotadas'}")
                if it["hpd"]:
                    tip += f" ≈ {it['hpd']:.1f} h por día".replace(".", ",")
            self.setToolTip(tip)
            self.update()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        if self._hover != -1:
            self._hover = -1
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        pt = e.position()
        for r, jid, _idx in self._rects:
            if r.contains(pt):
                self.abrir.emit(jid)
                return


class DatosNovelasVista(QWidget):
    """Pestaña «Datos» de la cronología: resumen, tus notas (1-10), horas por novela, resumen por
    año y récords. Se alimenta de la propia CronologiaVista (así ambas cuadran siempre)."""
    abrir = Signal(int)
    TARJ = 92
    _texto = CronologiaVista._texto
    _titulo = CronologiaVista._titulo
    _tarjeta = CronologiaVista._tarjeta

    def __init__(self):
        super().__init__()
        self.nov, self.crono = [], None
        self.hist, self.top, self.por_horas, self.anios, self.media, self.n_cal = [0] * 10, [], [], [], 0.0, 0
        self._rects = []
        self._hover = -1
        self.setMouseTracking(True)

    # ---------------- datos
    def poner(self, novelas, crono):
        self.nov, self.crono = novelas, crono
        cal = [n for n in novelas if n["nota"] > 0]
        self.n_cal = len(cal)
        self.media = (sum(n["nota"] for n in cal) / len(cal)) if cal else 0.0
        self.hist = [0] * 10
        for n in cal:
            self.hist[min(9, max(0, int(ceil(n["nota"])) - 1))] += 1
        self.top = sorted(cal, key=lambda n: (-n["nota"], -n["horas"],
                                              clave_alfabetica(n["nombre"])))[:5]
        self.por_horas = sorted([n for n in novelas if n["horas"] > 0],
                                key=lambda n: -n["horas"])[:8]
        por_anio = {}
        for it in crono.items:
            a = por_anio.setdefault(it["d2"].year, [set(), 0.0])
            a[0].add(it["id"])
            a[1] += it["h"]
        self.anios = [(y, len(v[0]), v[1]) for y, v in sorted(por_anio.items())]
        self._ajustar()
        self.update()

    # ---------------- geometría
    def _calc(self, W):
        PAD = 6
        L = {"PAD": PAD}
        cols = max(1, min(4, (W - 2 * PAD + 12) // 200))
        L["cols"] = cols
        y = 4
        L["res_t"] = y
        y += 36
        L["res"] = y
        y += ceil(7 / cols) * (self.TARJ + 12) + 8
        L["nota_t"] = y
        y += 36
        L["nota"] = y
        L["dos"] = W >= 820
        alto_h, alto_t = 210, 5 * 56 + 20
        y += (max(alto_h, alto_t) if L["dos"] else alto_h + 12 + alto_t) + 16
        L["hor_t"] = y
        y += 36
        L["hor"] = y
        y += max(1, len(self.por_horas)) * 40 + 18 + 14
        L["anio_t"] = y
        y += 36
        L["anio"] = y
        y += max(1, len(self.anios)) * 36 + 18 + 14
        L["rec_t"] = y
        y += 36
        L["rec"] = y
        L["cols_r"] = max(1, min(3, (W - 2 * PAD) // 300))
        recs = self.crono.records if self.crono else []
        y += ceil(max(1, len(recs)) / L["cols_r"]) * (self.TARJ + 12)
        L["alto"] = y + 16
        return L

    def _ajustar(self):
        h = self._calc(max(self.width(), 600))["alto"]
        if self.minimumHeight() != h:
            self.setMinimumHeight(h)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._ajustar()

    # ---------------- dibujo
    def _marco(self, p, r, borde):
        cam = QPainterPath()
        cam.addRoundedRect(r, Tema.radio, Tema.radio)
        p.fillPath(cam, con_alfa(Tema.c("card"), 150))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(borde, 1.2))
        p.drawPath(cam)

    def _portada(self, p, rect, n, a1, activo=False):
        pm = CACHE_GRANDE.obtener_diferido(n["portada"], 200, self)
        dibujar_cover(p, rect, pm, 8, n["enc"])
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(con_alfa(a1, 170 if activo else 80), 1.3))
        p.drawRoundedRect(rect, 8, 8)

    def paintEvent(self, e):
        if self.crono is None:
            return
        W = self.width()
        L = self._calc(W)
        PAD = L["PAD"]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        borde = QColor(Tema.c("border"))
        st = self.crono.stats
        self._rects = []

        def coma(x, dec=1):
            return f"{x:.{dec}f}".replace(".", ",")

        # ---- 1) resumen
        self._titulo(p, L["res_t"], "📊 Resumen general")
        horas = st["horas"]
        mejor = self.top[0] if self.top else None
        tarjetas = [
            ("📚", "Novelas", str(len(self.nov)),
             f"{st['con_fechas']} con fechas" + (f" · {st['incompletas']} sin fin"
                                                   if st["incompletas"] else "")),
            ("⏱", "Horas jugadas", fmt_horas(horas) or "—",
             f"{st['sin_horas']} sin horas anotadas" if st["sin_horas"]
             else (f"≈ {coma(horas / 24)} días sin parar" if horas else "anota horas en cada novela")),
            ("📅", "Días de juego", str(st["dias"]),
             f"desde {fmt_fecha(st['desde'])}" if st["desde"] else "añade fechas a tus novelas"),
            ("⚡", "Ritmo medio", f"{coma(st['ritmo'])} h/día" if st["ritmo"] else "—",
             "horas por día de juego"),
            ("🎭", "A la vez", str(st["simult"]), "máx. novelas en paralelo"),
            ("⭐", "Nota media", f"{coma(self.media)}/10" if self.n_cal else "—",
             f"{self.n_cal} calificadas · {len(self.nov) - self.n_cal} sin nota"),
            ("🏆", "Tu favorita", f"{fmt_nota(mejor['nota'])}/10" if mejor else "—",
             mejor["nombre"] if mejor else "califica tus novelas"),
        ]
        cols = L["cols"]
        cw = (W - 2 * PAD - (cols - 1) * 12) / cols
        for k, (emo, tit, val, sub) in enumerate(tarjetas):
            r = QRectF(PAD + (k % cols) * (cw + 12), L["res"] + (k // cols) * (self.TARJ + 12),
                       cw, self.TARJ)
            self._tarjeta(p, r, emo, tit, val, sub, a1, a2)
            if k == 6 and mejor:
                self._rects.append((r, mejor["id"], 900))

        # ---- 2) notas: histograma + mejor calificadas
        self._titulo(p, L["nota_t"], "⭐ Tus notas",
                     f"media {coma(self.media)}/10" if self.n_cal else "")
        ny = L["nota"]
        if L["dos"]:
            ancho = (W - 2 * PAD - 12) / 2.0
            r_h = QRectF(PAD, ny, ancho, 210)
            r_t = QRectF(PAD + ancho + 12, ny, ancho, 5 * 56 + 20)
        else:
            r_h = QRectF(PAD, ny, W - 2 * PAD, 210)
            r_t = QRectF(PAD, ny + 222, W - 2 * PAD, 5 * 56 + 20)
        self._marco(p, r_h, borde)
        if not self.n_cal:
            self._texto(p, r_h, "Califica tus novelas (botón ☆ dentro de cada una) y aquí verás "
                        "cómo se reparten tus notas.", Tema.tam, mu, False,
                        Qt.AlignmentFlag.AlignHCenter)
        else:
            area = QRectF(r_h.left() + 16, r_h.top() + 30, r_h.width() - 32, r_h.height() - 66)
            mx = max(self.hist)
            slot = area.width() / 10.0
            bw = min(40.0, slot * 0.66)
            p.setPen(QPen(con_alfa(borde, 200), 1.2))
            p.drawLine(QPointF(area.left(), area.bottom()), QPointF(area.right(), area.bottom()))
            for k, c in enumerate(self.hist):
                cx = area.left() + slot * (k + 0.5)
                if c:
                    alto = max(5.0, area.height() * c / mx)
                    r = QRectF(cx - bw / 2, area.bottom() - alto, bw, alto)
                    g = QLinearGradient(r.topLeft(), r.bottomLeft())
                    g.setColorAt(0, a1)
                    g.setColorAt(1, a2)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QBrush(g))
                    p.drawRoundedRect(r, 6, 6)
                    self._texto(p, QRectF(cx - 24, r.top() - 18, 48, 16), str(c), Tema.tam - 1,
                                txt, True, Qt.AlignmentFlag.AlignHCenter)
                self._texto(p, QRectF(cx - 24, area.bottom() + 4, 48, 18), str(k + 1),
                            Tema.tam - 0.5, mu, False, Qt.AlignmentFlag.AlignHCenter)
        self._marco(p, r_t, borde)
        self._texto(p, QRectF(r_t.left() + 16, r_t.top() + 4, r_t.width() - 32, 24),
                    "Mejor calificadas", Tema.tam, mu, True)
        for k, n in enumerate(self.top):
            fila = QRectF(r_t.left() + 8, r_t.top() + 30 + k * 56, r_t.width() - 16, 52)
            idx = 800 + k
            if idx == self._hover:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(con_alfa(a1, 34))
                p.drawRoundedRect(fila, 10, 10)
            self._rects.append((fila, n["id"], idx))
            self._texto(p, QRectF(fila.left() + 4, fila.top(), 26, fila.height()), str(k + 1),
                        Tema.tam + 3, a1, True, Qt.AlignmentFlag.AlignHCenter)
            self._portada(p, QRectF(fila.left() + 34, fila.top() + 5, 42, 42), n, a1,
                          idx == self._hover)
            self._texto(p, QRectF(fila.left() + 86, fila.top() + 5, fila.width() - 170, 22),
                        n["nombre"], Tema.tam, txt, True)
            self._texto(p, QRectF(fila.left() + 86, fila.top() + 27, fila.width() - 170, 18),
                        fmt_horas(n["horas"]) or "sin horas anotadas", Tema.tam - 1.5, mu)
            self._texto(p, QRectF(fila.right() - 82, fila.top(), 76, fila.height()),
                        f"★ {fmt_nota(n['nota'])}", Tema.tam + 3, a1, True,
                        Qt.AlignmentFlag.AlignRight)

        # ---- 3) horas por novela
        self._titulo(p, L["hor_t"], "⏱ Horas por novela",
                     "tus más largas" if self.por_horas else "")
        marco = QRectF(PAD, L["hor"], W - 2 * PAD, max(1, len(self.por_horas)) * 40 + 18)
        self._marco(p, marco, borde)
        if not self.por_horas:
            self._texto(p, marco, "Anota las horas jugadas de tus novelas para compararlas aquí.",
                        Tema.tam, mu, False, Qt.AlignmentFlag.AlignHCenter)
        else:
            mxh = self.por_horas[0]["horas"]
            for k, n in enumerate(self.por_horas):
                y = marco.top() + 9 + k * 40
                fila = QRectF(marco.left() + 6, y, marco.width() - 12, 38)
                idx = 700 + k
                if idx == self._hover:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(con_alfa(a1, 34))
                    p.drawRoundedRect(fila, 9, 9)
                self._rects.append((fila, n["id"], idx))
                self._portada(p, QRectF(fila.left() + 6, y + 3, 32, 32), n, a1, idx == self._hover)
                nom_w = min(230.0, fila.width() * 0.32)
                self._texto(p, QRectF(fila.left() + 46, y, nom_w, 38), n["nombre"], Tema.tam, txt,
                            True)
                bx = fila.left() + 46 + nom_w + 8
                bmax = max(40.0, fila.right() - bx - 150)
                bw = max(8.0, bmax * n["horas"] / mxh)
                g = QLinearGradient(bx, 0, bx + bw, 0)
                g.setColorAt(0, a1)
                g.setColorAt(1, a2)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(g))
                p.drawRoundedRect(QRectF(bx, y + 11, bw, 16), 8, 8)
                self._texto(p, QRectF(bx + bw + 8, y, 80, 38), fmt_horas(n["horas"]), Tema.tam - 0.5,
                            txt, True)
                if n["nota"]:
                    self._texto(p, QRectF(fila.right() - 66, y, 60, 38), f"★ {fmt_nota(n['nota'])}",
                                Tema.tam, a1, True, Qt.AlignmentFlag.AlignRight)

        # ---- 4) por año
        self._titulo(p, L["anio_t"], "🗓 Por año", "según el año en que terminaste")
        marco = QRectF(PAD, L["anio"], W - 2 * PAD, max(1, len(self.anios)) * 36 + 18)
        self._marco(p, marco, borde)
        if not self.anios:
            self._texto(p, marco, "Aún no hay novelas con fechas.", Tema.tam, mu, False,
                        Qt.AlignmentFlag.AlignHCenter)
        else:
            mxa = max(max(a[2] for a in self.anios), 0.1)
            for k, (anio, cuenta, h) in enumerate(self.anios):
                y = marco.top() + 9 + k * 36
                self._texto(p, QRectF(marco.left() + 18, y, 60, 34), str(anio), Tema.tam + 1, a1,
                            True)
                bx = marco.left() + 84
                bmax = max(40.0, marco.right() - bx - 230)
                bw = max(8.0, bmax * h / mxa) if h > 0 else 8.0
                g = QLinearGradient(bx, 0, bx + bw, 0)
                g.setColorAt(0, a1)
                g.setColorAt(1, a2)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(g))
                p.drawRoundedRect(QRectF(bx, y + 9, bw, 16), 8, 8)
                self._texto(p, QRectF(bx + bw + 10, y, marco.right() - bx - bw - 20, 34),
                            f"{cuenta} {'novela' if cuenta == 1 else 'novelas'}"
                            + (f" · {fmt_horas(h)}" if h > 0 else ""), Tema.tam - 0.5, txt, True)

        # ---- 5) récords
        recs = self.crono.records
        self._titulo(p, L["rec_t"], "🏅 Récords de tu historial")
        if not recs:
            self._texto(p, QRectF(0, L["rec"], W, 50),
                        "Los récords aparecen en cuanto anotes fechas y horas en tus novelas.",
                        Tema.tam, mu, False, Qt.AlignmentFlag.AlignHCenter)
        else:
            cr = L["cols_r"]
            cw = (W - 2 * PAD - (cr - 1) * 12) / cr
            for k, (emo, tit, val, nom, jid) in enumerate(recs):
                r = QRectF(PAD + (k % cr) * (cw + 12), L["rec"] + (k // cr) * (self.TARJ + 12),
                           cw, self.TARJ)
                self._tarjeta(p, r, emo, tit, val, nom, a1, a2)
                if jid >= 0:
                    self._rects.append((r, jid, 500 + k))
        p.end()

    # ---------------- ratón
    def mouseMoveEvent(self, e):
        pt = e.position()
        hover = -1
        for r, jid, idx in self._rects:
            if r.contains(pt):
                hover = idx
                break
        if hover != self._hover:
            self._hover = hover
            self.setCursor(Qt.CursorShape.PointingHandCursor if hover >= 0
                           else Qt.CursorShape.ArrowCursor)
            self.update()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        if self._hover != -1:
            self._hover = -1
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        for r, jid, _idx in self._rects:
            if r.contains(e.position()):
                self.abrir.emit(jid)
                return


def medidas_completas(busto, cintura, cadera):
    return bool(busto and cintura and cadera)


def texto_cuerpo(alt, bus, cin, cad):
    """'Altura: 158 cm. Medidas de busto, cintura y caderas: 90-59-88 cm.'"""
    partes = []
    if alt:
        partes.append(f"Altura: {alt} cm.")
    if medidas_completas(bus, cin, cad):
        partes.append(f"Medidas de busto, cintura y caderas: {bus}-{cin}-{cad} cm.")
    return " ".join(partes)


def cuerpo_corto(alt, bus, cin, cad):
    """'158 cm · 90-59-88' (para tarjetas y listas)."""
    partes = []
    if alt:
        partes.append(f"{alt} cm")
    if medidas_completas(bus, cin, cad):
        partes.append(f"{bus}-{cin}-{cad}")
    return " · ".join(partes)


def parsear_cuerpo(texto):
    """Entiende textos como «Altura: 158 cm. Medidas de busto, cintura y caderas: 90-59-88 cm.»
    (también «B90 W59 H88», «1,58 m», «90/59/88»...). Devuelve (altura, busto, cintura, cadera);
    0 = no encontrado."""
    t = (texto or "").replace("\u2013", "-").replace("\u2014", "-")
    alt = bus = cin = cad = 0
    m = re.search(r"(\d)[.,](\d{2})\s*m\b", t)
    if m:
        alt = int(m.group(1)) * 100 + int(m.group(2))
    else:
        m = (re.search(r"(?:altura|estatura|height)\D{0,12}(\d{2,3})", t, re.I)
             or re.search(r"\b(\d{3})\s*cm\b", t, re.I))
        if m:
            alt = int(m.group(1))
    m = re.search(r"B\s*[:=]?\s*(\d{2,3})\D{1,8}W\s*[:=]?\s*(\d{2,3})\D{1,8}H\s*[:=]?\s*(\d{2,3})", t)
    if not m:
        m = re.search(r"(\d{2,3})\s*[-/x×,·]\s*(\d{2,3})\s*[-/x×,·]\s*(\d{2,3})", t)
    if m:
        bus, cin, cad = (int(v) for v in m.groups())
    if not 80 <= alt <= 250:
        alt = 0
    if not all(40 <= v <= 200 for v in (bus, cin, cad)):
        bus = cin = cad = 0
    return alt, bus, cin, cad


def puntaje_reloj(bus, cin, cad):
    """0-100: qué tan «reloj de arena» es la silueta (busto y cadera parecidos y cintura
    marcada, cintura/cadera cercana a 0,70)."""
    if not medidas_completas(bus, cin, cad):
        return 0
    equilibrio = max(0.0, 1 - (abs(bus - cad) / max(bus, cad)) / 0.15)
    marcada = max(0.0, 1 - abs(cin / cad - 0.70) / 0.20)
    return int(round(100 * (0.5 * equilibrio + 0.5 * marcada)))


def lista_apodos(texto):
    """'Nana, Nanako ; Nana-chan' -> ['Nana', 'Nanako', 'Nana-chan'] (sin repetidos)."""
    vistos, res = set(), []
    for a in re.split(r"[,;|\n]+", texto or ""):
        a = " ".join(a.split())
        if a and a.casefold() not in vistos:
            vistos.add(a.casefold())
            res.append(a)
    return res


def texto_apodos(texto):
    return ", ".join(lista_apodos(texto))


MODOS_MEDIDAS = (
    ("alta", "Más alta"), ("baja", "Más baja"),
    ("reloj", "Figura reloj de arena"), ("cintura", "Cintura más estrecha"),
    ("busto", "Mayor busto"), ("coqueta", "Menor busto"),
    ("cadera", "Mayor cadera"), ("cadera_min", "Menor cadera"),
    ("violin", "Curva cintura-cadera"), ("voluptuosa", "Mayor suma de medidas"),
    ("delicada", "Menor suma de medidas"), ("simetria", "Busto y cadera parejos"),
)
ETIQUETA_MEDIDAS = {k: t.upper() for k, t in MODOS_MEDIDAS}
DESCRIPCION_MEDIDAS = {
    "alta": "Estatura: gana la heroína más alta (en cm).",
    "baja": "Estatura: gana la heroína más baja (en cm).",
    "reloj": "Qué tan cerca está de una silueta de reloj de arena: busto y cadera parecidos y "
             "cintura marcada. Puntaje de 0 a 100; más alto = más reloj de arena.",
    "cintura": "Medida de cintura: gana la que tiene la cintura más estrecha (en cm).",
    "busto": "Medida de busto: gana la que tiene el mayor contorno de busto (en cm).",
    "coqueta": "Medida de busto: gana la que tiene el menor contorno de busto (en cm).",
    "cadera": "Medida de cadera: gana la que tiene el mayor contorno de cadera (en cm).",
    "cadera_min": "Medida de cadera: gana la que tiene el menor contorno de cadera (en cm).",
    "violin": "Cadera menos cintura, en cm. Cuanto mayor es la diferencia, más marcada es la "
              "curva entre cintura y cadera.",
    "voluptuosa": "Busto + cintura + cadera sumados, en cm: gana la de mayor total.",
    "delicada": "Busto + cintura + cadera sumados, en cm: gana la de menor total.",
    "simetria": "Diferencia entre busto y cadera, en cm. Cuanto menor, más parejos son; "
                "gana la de menor diferencia.",
    "campeonas": "La número 1 de cada apartado. Si hay empate, todas las empatadas aparecen.",
}


def dias_para_cumple(cumple):
    """Días que faltan para el próximo cumpleaños ('12 de marzo'); None si no se entiende."""
    import datetime
    m = re.match(r"\s*(\d{1,2}) de (\w+)", cumple or "")
    if not m or m.group(2).lower() not in MESES_ES:
        return None
    mes, dia = MESES_ES.index(m.group(2).lower()) + 1, int(m.group(1))
    hoy = datetime.date.today()
    for anio in (hoy.year, hoy.year + 1):
        try:
            f = datetime.date(anio, mes, dia)
        except ValueError:                       # 29 de febrero en año no bisiesto
            f = datetime.date(anio, mes, 28)
        if f >= hoy:
            return (f - hoy).days
    return None


def edad_actual(cumple, anio):
    """Edad en años cumplidos hoy. Con día y mes es exacta; solo con el mes o sin ellos,
    se calcula con el año (puede variar en 1). None si no hay año de nacimiento."""
    import datetime
    try:
        anio = int(anio or 0)
    except (TypeError, ValueError):
        return None
    if anio <= 0:
        return None
    hoy = datetime.date.today()
    edad = hoy.year - anio
    m = re.match(r"\s*(\d{1,2}) de (\w+)", cumple or "")
    if m and m.group(2).lower() in MESES_ES:
        mes, dia = MESES_ES.index(m.group(2).lower()) + 1, int(m.group(1))
        if (hoy.month, hoy.day) < (mes, dia):
            edad -= 1
    elif (cumple or "").strip().lower() in MESES_ES:
        if hoy.month < MESES_ES.index(cumple.strip().lower()) + 1:
            edad -= 1
    return edad if edad >= 0 else None


def texto_cumple_seiyuu(cumple, anio):
    """'12 de marzo de 1990 · 36 años' (o lo que se sepa)."""
    partes = cumple or ""
    try:
        anio = int(anio or 0)
    except (TypeError, ValueError):
        anio = 0
    if anio > 0:
        partes = (partes + " de " if partes and re.match(r"\s*\d", partes) else
                  (partes + " " if partes else "")) + str(anio)
    edad = edad_actual(cumple, anio)
    if edad is not None:
        partes += f"  ·  {edad} {'año' if edad == 1 else 'años'}"
    return partes


def dibujar_trofeo(p, centro, tam, c1, c2):
    """Copa vectorial con degradado, asas, brillo y estrella. c1/c2: colores claro y oscuro."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(centro)
    p.scale(tam / 2.0, tam / 2.0)
    a, b = QColor(c1), QColor(c2)
    g = QLinearGradient(-0.6, -0.85, 0.6, 0.85)
    g.setColorAt(0, a)
    g.setColorAt(1, b)
    p.setPen(QPen(b, 0.13, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                  Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for s in (-1, 1):                                    # asas
        asa = QPainterPath()
        asa.moveTo(s * 0.52, -0.62)
        asa.cubicTo(s * 1.0, -0.7, s * 0.98, -0.08, s * 0.42, -0.02)
        p.drawPath(asa)
    copa = QPainterPath()                                # copa
    copa.moveTo(-0.58, -0.85)
    copa.lineTo(0.58, -0.85)
    copa.cubicTo(0.58, -0.1, 0.36, 0.34, 0.0, 0.38)
    copa.cubicTo(-0.36, 0.34, -0.58, -0.1, -0.58, -0.85)
    copa.closeSubpath()
    p.setPen(QPen(b.darker(130), 0.05))
    p.setBrush(QBrush(g))
    p.drawPath(copa)
    p.drawRect(QRectF(-0.09, 0.36, 0.18, 0.3))           # tallo
    p.drawRoundedRect(QRectF(-0.4, 0.64, 0.8, 0.2), 0.07, 0.07)   # base
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 110))               # brillo
    p.drawEllipse(QRectF(-0.44, -0.72, 0.16, 0.5))
    pts = []                                             # estrella
    for k in range(10):
        r = 0.26 if k % 2 == 0 else 0.11
        ang = -pi / 2 + k * pi / 5
        pts.append(QPointF(cos(ang) * r, -0.38 + sin(ang) * r))
    p.setBrush(QColor(255, 255, 255, 210))
    p.drawPolygon(QPolygonF(pts))
    p.restore()


def dibujar_medalla(p, centro, rad, n, destacada=False):
    """Medalla redonda con el número del puesto (las destacadas llevan cintas y anillo)."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
    p.setPen(Qt.PenStyle.NoPen)
    if destacada:
        p.setBrush(a2)
        for s in (-1, 1):
            p.drawPolygon(QPolygonF([
                QPointF(centro.x() + s * rad * 0.25, centro.y()),
                QPointF(centro.x() + s * rad * 0.85, centro.y()),
                QPointF(centro.x() + s * rad * 0.55, centro.y() + rad * 1.3)]))
    g = QLinearGradient(centro.x() - rad, centro.y() - rad, centro.x() + rad, centro.y() + rad)
    g.setColorAt(0, a1)
    g.setColorAt(1, a2)
    p.setPen(QPen(QColor(255, 255, 255, 170), 1.5))
    p.setBrush(QBrush(g))
    p.drawEllipse(centro, rad, rad)
    if destacada:
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 120), 1))
        p.drawEllipse(centro, rad - 4, rad - 4)
    f = QFont(Tema.fuente)
    f.setPixelSize(max(9, int(rad * (0.95 if n < 10 else 0.8))))
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor(TEXTO_SOBRE_ACENTO))
    p.drawText(QRectF(centro.x() - rad, centro.y() - rad, rad * 2, rad * 2),
               int(Qt.AlignmentFlag.AlignCenter), str(n))
    p.restore()


class FichaHeroina(QWidget):
    """Ficha de la heroína (cumpleaños, seiyuu, altura y medidas). Cada dato va en una
    fila de altura fija con icono, etiqueta y valor alineados. Se ajusta sola a su
    contenido, así que nunca necesita barra de desplazamiento."""
    ALTO_FILA = 54

    def __init__(self):
        super().__init__()
        self.filas = []
        self.hint = ""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.poner(None)

    def poner(self, d):
        self.filas = []
        self.hint = ""
        self.setToolTip("")
        if d:
            cu, cv = d.get("cumple", ""), d.get("seiyuu", "")
            apodos = lista_apodos(d.get("apodos", ""))
            if apodos:
                self.filas.append(("🏷", "APODO" if len(apodos) == 1 else "APODOS",
                                   apodos, "", False))
                self.setToolTip("Apodos: " + ", ".join(apodos))
            if cu:
                dias = dias_para_cumple(cu)
                pill = ("¡es hoy! 🎉" if dias == 0 else
                        "falta 1 día" if dias == 1 else
                        f"faltan {dias} días" if dias is not None else "")
                self.filas.append(("🎂", "CUMPLEAÑOS", cu, pill, False))
            if cv:
                self.filas.append(("🎙", "SEIYUU", cv, "", False))
            cuerpo = cuerpo_corto(d.get("altura", 0), d.get("busto", 0),
                                  d.get("cintura", 0), d.get("cadera", 0))
            if cuerpo:
                self.filas.append(("📏", "ALTURA · BUSTO-CINTURA-CADERA", cuerpo, "", False))
            if not self.filas:
                self.hint = ""
        self.setFixedHeight(14 + len(self.filas) * self.ALTO_FILA if self.filas else 0)
        self.update()

    @staticmethod
    def _chips(p, nombres, x, y, w, a1, txt):
        """Apodos como etiquetas; si no caben todos, el resto se resume en «+N»."""
        f = QFont(Tema.fuente)
        f.setPixelSize(12)
        f.setBold(True)
        fm = QFontMetrics(f)
        p.setFont(f)
        cx, fin = x, x + w
        for i, n in enumerate(nombres):
            tw = fm.horizontalAdvance(n) + 18
            resto = len(nombres) - i - 1
            reserva = (fm.horizontalAdvance(f"+{resto}") + 24) if resto else 0
            if i > 0 and cx + tw + reserva > fin:
                mas = f"+{len(nombres) - i}"
                mw = fm.horizontalAdvance(mas) + 18
                caja = QRectF(cx, y, mw, 24)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(con_alfa(a1, 90))
                p.drawRoundedRect(caja, 12, 12)
                p.setPen(txt)
                p.drawText(caja, int(Qt.AlignmentFlag.AlignCenter), mas)
                break
            tw = min(tw, fin - cx)
            caja = QRectF(cx, y, tw, 24)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(con_alfa(a1, 52))
            p.drawRoundedRect(caja, 12, 12)
            p.setPen(txt)
            p.drawText(caja, int(Qt.AlignmentFlag.AlignCenter),
                       fm.elidedText(n, Qt.TextElideMode.ElideRight, int(tw - 14)))
            cx += tw + 6

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio, Tema.radio)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, mezclar(card, a1, 0.10))
        g.setColorAt(1, mezclar(card, a2, 0.04))
        p.fillPath(camino, QBrush(g))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(borde, 1.2))
        p.drawPath(camino)
        if self.hint:
            f = QFont(Tema.fuente)
            f.setPointSizeF(max(8.0, Tema.tam - 1))
            p.setFont(f)
            p.setPen(mu)
            p.drawText(r.adjusted(14, 8, -14, -8),
                       int(Qt.AlignmentFlag.AlignCenter.value | Qt.TextFlag.TextWordWrap.value), self.hint)
            return
        y = r.top() + 7
        for i, (icono, etiqueta, valor, pill, grande) in enumerate(self.filas):
            fila = QRectF(r.left() + 12, y, r.width() - 24, self.ALTO_FILA)
            if i:
                p.setPen(QPen(con_alfa(borde, 170), 1))
                p.drawLine(QPointF(fila.left(), y), QPointF(fila.right(), y))
            d = 36.0                                           # icono en círculo
            ic = QRectF(fila.left(), fila.center().y() - d / 2, d, d)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(con_alfa(a1, 46))
            p.drawEllipse(ic)
            f = QFont(Tema.fuente)
            f.setPixelSize(17)
            f.setBold(True)
            p.setFont(f)
            p.setPen(a1)
            p.drawText(ic, int(Qt.AlignmentFlag.AlignCenter), icono)
            x = ic.right() + 12
            w = fila.right() - x
            f = QFont(Tema.fuente)                             # etiqueta
            f.setPixelSize(10)
            f.setBold(True)
            f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
            p.setFont(f)
            p.setPen(a1)
            p.drawText(QRectF(x, y + 7, w, 16), int(Qt.AlignmentFlag.AlignLeft
                                                    | Qt.AlignmentFlag.AlignVCenter), etiqueta)
            if pill:                                           # «faltan N días»
                fp = QFont(Tema.fuente)
                fp.setPixelSize(10)
                fp.setBold(True)
                p.setFont(fp)
                pw = QFontMetrics(fp).horizontalAdvance(pill) + 14
                pr = QRectF(fila.right() - pw, y + 7, pw, 17)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(con_alfa(a1, 40))
                p.drawRoundedRect(pr, 8.5, 8.5)
                p.setPen(a1)
                p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter), pill)
            if isinstance(valor, list):                        # apodos: una etiqueta por apodo
                self._chips(p, valor, x, y + 24, w, a1, txt)
                y += self.ALTO_FILA
                continue
            f = QFont(Tema.fuente)                             # valor
            f.setPointSizeF(Tema.tam + (4 if grande else 1))
            f.setBold(True)
            p.setFont(f)
            p.setPen(txt)
            p.drawText(QRectF(x, y + 23, w, 26),
                       int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                       QFontMetrics(f).elidedText(valor, Qt.TextElideMode.ElideRight, int(w)))
            y += self.ALTO_FILA
        p.end()


class TopHeroinas(QWidget):
    """Podio de heroínas: 1.º, 2.º y 3.º con trofeo sobre un pedestal; el resto, en filas
    con medalla (en dos columnas si la ventana es ancha). Se reordena arrastrando una
    tarjeta (las demás se apartan y se deslizan solas). Doble clic: ir a su galería.
    Con suprema=True es el ranking global («Heroína de heroínas»)."""
    orden_cambiado = Signal(list)       # ids de heroínas en el nuevo orden
    abrir = Signal(int)

    ALTO_PODIO = 470
    ALTO_FILA = 78
    ESP = 10
    PED = {1: 232, 2: 208, 3: 192}

    def __init__(self, suprema=False):
        super().__init__()
        self.suprema = suprema
        self.vacio = "🏆\n\nAún no hay heroínas."
        self.items = {}
        self.orden = []
        self.av = {}
        self.scroll = None
        self._max = 1
        self._total = 1
        self._cumples = []
        self._activas = []
        self._duelistas = []
        self.stats_duelos = {}              # {id: (victorias, derrotas)} de los duelos
        self._zonas = []                    # (id, centro, radio): avatares clicables de los paneles
        self._zona = None                   # avatar de panel bajo el cursor
        self._vis_actual = []
        self.terceras = [[], []]            # terceros puestos sorteados: panel izq. / der.
        self.av3 = {}
        self._cur = {}
        self._arr = None
        self._cursor = QPointF()
        self._press = None
        self._hover = None
        self._prev = None
        self._t0 = time.monotonic()
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._tick)
        self.setMouseTracking(True)
        self.setMinimumHeight(self.ALTO_PODIO)

    # ---------- datos
    def poner(self, items):
        self.items = {i["id"]: i for i in items}
        self.orden = [i["id"] for i in items]
        self.av = {}
        self._max = max([i["capturas"] for i in items] + [1])
        self._total = max(sum(i["capturas"] for i in items), 1)
        for i in items:
            i["dias"] = dias_para_cumple(i.get("cumple", ""))
        self._cumples = sorted((i for i in items if i["dias"] is not None),
                               key=lambda i: i["dias"])[:5]
        self._activas = sorted(items, key=lambda i: -i["capturas"])[:5]
        duel = []
        for i in items:
            v_, d_ = self.stats_duelos.get(i["id"], (0, 0))
            i["duelos_v"], i["duelos_d"] = v_, d_
            if v_ + d_:
                duel.append(i)
        self._duelistas = sorted(
            duel, key=lambda i: (-i["duelos_v"], str(i.get("nombre", "")).casefold()))[:5]
        self._arr = self._prev = self._press = self._hover = None
        self._cur = {k: v for k, v in self._cur.items() if k in self.items}
        self.setMinimumHeight(self._alto(len(items)))
        self.update()

    def _cols(self):
        return 2 if self.width() >= 1180 else 1

    def _alto(self, n):
        if n <= 3:
            return self.ALTO_PODIO
        filas = ceil((n - 3) / self._cols())
        return self.ALTO_PODIO + filas * (self.ALTO_FILA + self.ESP) + 24

    def resizeEvent(self, e):
        super().resizeEvent(e)
        h = self._alto(len(self.orden))
        if self.minimumHeight() != h:
            self.setMinimumHeight(h)

    def showEvent(self, e):
        super().showEvent(e)
        self.timer.start(30 if Tema.anim else 100)

    def hideEvent(self, e):
        super().hideEvent(e)
        self.timer.stop()

    # ---------- geometría
    def _destinos(self, orden):
        """Rectángulo de cada puesto (los 3 primeros: columnas del podio; el resto: filas)."""
        W = max(self.width(), 480)
        n = len(orden)
        pw = min(310.0, (W - 80) / 3.0)
        cx = W / 2
        top, base = 12.0, float(self.ALTO_PODIO - 28)
        if n == 1:
            xs = [cx - pw / 2]
        elif n == 2:
            xs = [cx - pw - 9, cx + 9]
        else:
            xs = [cx - pw / 2, cx - pw * 1.5 - 18, cx + pw / 2 + 18]
        cols = self._cols()
        gap = 14.0
        total = min(W - 40.0, 1320.0 if cols == 2 else 860.0)
        fw = (total - gap * (cols - 1)) / cols
        x0 = (W - total) / 2
        out = {}
        for i, hid in enumerate(orden):
            if i < 3:
                out[hid] = QRectF(xs[i], top, pw, base - top)
            else:
                j = i - 3
                out[hid] = QRectF(x0 + (j % cols) * (fw + gap),
                                  self.ALTO_PODIO + (j // cols) * (self.ALTO_FILA + self.ESP),
                                  fw, self.ALTO_FILA)
        return out

    def _rect(self, hid, dest):
        origen = self._cur.get(hid)
        if origen is None:
            origen = dest[hid].topLeft()
        return QRectF(origen, dest[hid].size())

    def _tick(self):
        if not self.orden:
            return
        dest = self._destinos(self._prev or self.orden)
        movido = False
        for hid, r in dest.items():
            tgt = r.topLeft()
            cur = self._cur.get(hid, tgt)
            if Tema.anim:
                nx = cur.x() + (tgt.x() - cur.x()) * 0.3
                ny = cur.y() + (tgt.y() - cur.y()) * 0.3
                if abs(tgt.x() - nx) < 0.5 and abs(tgt.y() - ny) < 0.5:
                    nx, ny = tgt.x(), tgt.y()
            else:
                nx, ny = tgt.x(), tgt.y()
            nuevo = QPointF(nx, ny)
            if nuevo != cur:
                movido = True
            self._cur[hid] = nuevo
        if movido or Tema.anim:
            self.update()

    # ---------- ratón
    def _en(self, pos):
        dest = self._destinos(self.orden)
        for hid in self.orden:
            if self._rect(hid, dest).contains(pos):
                return hid
        return None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            hid = self._en(e.position())
            self._press = (hid, e.position()) if hid is not None else None
        e.accept()

    def _actualizar_prev(self, pos):
        n = len(self.orden)
        slots = self._destinos(list(range(n)))
        mejor, dmin = 0, None
        for i in range(n):
            r = slots[i]
            dx = max(r.left() - pos.x(), 0, pos.x() - r.right())
            dy = max(r.top() - pos.y(), 0, pos.y() - r.bottom())
            d = dx * dx + dy * dy
            if dmin is None or d < dmin:
                mejor, dmin = i, d
        resto = [h for h in self.orden if h != self._arr]
        resto.insert(mejor, self._arr)
        self._prev = resto

    def _auto_scroll(self, g):
        if self.scroll is None:
            return
        vp = self.scroll.viewport()
        y = vp.mapFromGlobal(g).y()
        barra = self.scroll.verticalScrollBar()
        if y < 40:
            barra.setValue(barra.value() - 20)
        elif y > vp.height() - 40:
            barra.setValue(barra.value() + 20)

    def mouseMoveEvent(self, e):
        pos = e.position()
        if (self._arr is None and self._press and (e.buttons() & Qt.MouseButton.LeftButton)
                and (pos - self._press[1]).toPoint().manhattanLength()
                >= QApplication.startDragDistance()):
            self._arr = self._press[0]
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        if self._arr is not None:
            self._cursor = pos
            self._actualizar_prev(pos)
            self._tick()
            self._auto_scroll(e.globalPosition().toPoint())
            self.update()
            return
        hid = self._en(pos)
        zona = self._en_zona(pos) if hid is None else None
        if hid != self._hover or zona != self._zona:
            self._hover, self._zona = hid, zona
            self.setCursor(Qt.CursorShape.PointingHandCursor
                           if (hid is not None or zona is not None)
                           else Qt.CursorShape.ArrowCursor)
            self.update()

    def mouseReleaseEvent(self, e):
        if self._arr is not None:
            arr = self._arr
            nuevo = list(self._prev or self.orden)
            cambio = nuevo != self.orden
            self.orden = nuevo
            self._arr = self._prev = self._press = None
            idx = nuevo.index(arr)
            if idx >= 3:                       # la fila «aterriza» deslizándose desde el cursor
                r = self._destinos(nuevo)[arr]
                self._cur[arr] = QPointF(self._cursor.x() - r.width() / 2,
                                         self._cursor.y() - r.height() / 2)
            self.unsetCursor()
            self.update()
            if cambio:
                self.orden_cambiado.emit(list(self.orden))
            return
        self._press = None

    def mouseDoubleClickEvent(self, e):
        hid = self._en(e.position())
        if hid is None:
            hid = self._en_zona(e.position())
        if hid is not None:
            self.abrir.emit(hid)

    def leaveEvent(self, e):
        super().leaveEvent(e)
        if self._arr is None and self._hover is not None:
            self._hover = None
            self.update()

    # ---------- utilidades de dibujo
    def _f(self, pt=None, px=None, bold=False, esp=0.0):
        f = QFont(Tema.fuente)
        if px is not None:
            f.setPixelSize(int(px))
        else:
            f.setPointSizeF(pt if pt is not None else Tema.tam)
        f.setBold(bold)
        if esp:
            f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, esp)
        return f

    def _txt(self, p, x, y, w, h, texto, f, color, alin=Qt.AlignmentFlag.AlignLeft):
        p.setFont(f)
        p.setPen(color)
        p.drawText(QRectF(x, y, w, h), int(alin | Qt.AlignmentFlag.AlignVCenter),
                   QFontMetrics(f).elidedText(texto, Qt.TextElideMode.ElideRight,
                                              int(max(10.0, w))))

    @staticmethod
    def _detalle(it):
        if "rol" in it:                      # ranking global: campeona / subcampeona de su novela
            return it["rol"]
        partes = []
        if it.get("cumple"):
            partes.append("🎂 " + it["cumple"])
        if it.get("seiyuu"):
            partes.append("CV: " + it["seiyuu"])
        cuerpo = cuerpo_corto(it.get("altura", 0), it.get("busto", 0),
                              it.get("cintura", 0), it.get("cadera", 0))
        if cuerpo:
            partes.append("📏 " + cuerpo)
        return " · ".join(partes)

    def _barra(self, p, x, y, w, h, frac, a1, a2):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(Tema.c("border")))
        p.drawRoundedRect(QRectF(x, y, w, h), h / 2, h / 2)
        if frac > 0:
            gb = QLinearGradient(x, 0, x + w, 0)
            gb.setColorAt(0, a1)
            gb.setColorAt(1, a2)
            p.setBrush(QBrush(gb))
            p.drawRoundedRect(QRectF(x, y, max(h, w * frac), h), h / 2, h / 2)

    # ---------- dibujo
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        W = self.width()
        n = len(self.orden)
        if n == 0:
            p.setFont(self._f(Tema.tam + 3))
            p.setPen(QColor(Tema.c("muted")))
            p.drawText(QRectF(self.rect()), int(Qt.AlignmentFlag.AlignCenter), self.vacio)
            return
        t = time.monotonic() - self._t0
        vis = self._prev or self.orden
        self._vis_actual = vis
        self._zonas = []
        dest = self._destinos(vis)
        r1 = self._rect(vis[0], dest)

        halo = QRadialGradient(QPointF(r1.center().x(), 170), 400)      # resplandor dorado
        halo.setColorAt(0, con_alfa(PODIO[1][0], 55))
        halo.setColorAt(1, con_alfa(PODIO[1][0], 0))
        p.fillRect(QRectF(0, 0, W, self.ALTO_PODIO), QBrush(halo))

        base_y = dest[vis[0]].bottom() + 4                                # suelo del podio
        suelo = QLinearGradient(W * 0.04, 0, W * 0.96, 0)
        suelo.setColorAt(0, con_alfa(Tema.a1(), 0))
        suelo.setColorAt(0.5, QColor(Tema.a1()))
        suelo.setColorAt(1, con_alfa(Tema.a2(), 0))
        p.setPen(QPen(QBrush(suelo), 3))
        p.drawLine(QPointF(W * 0.04, base_y), QPointF(W * 0.96, base_y))

        if n > 3:                                                         # separador
            f = self._f(px=12, bold=True, esp=2)
            txt = "SIGUIENTES PUESTOS"
            tw = QFontMetrics(f).horizontalAdvance(txt) + 26
            self._txt(p, (W - tw) / 2, base_y + 8, tw, 22, txt, f,
                      QColor(Tema.c("muted")), Qt.AlignmentFlag.AlignCenter)
            p.setPen(QPen(con_alfa(Tema.c("border"), 200), 1.5))
            p.drawLine(QPointF(W * 0.04, base_y + 19), QPointF((W - tw) / 2, base_y + 19))
            p.drawLine(QPointF((W + tw) / 2, base_y + 19), QPointF(W * 0.96, base_y + 19))

        if W >= 820:                                                      # leyenda de colores
            self._leyenda(p, [(CAT_COLOR[c], c) for c in CATEGORIAS], W * 0.96, base_y + 11,
                          "der")
        self._paneles_laterales(p, vis, dest)

        for rank, hid in enumerate(vis, 1):
            if hid == self._arr:
                continue
            r = self._rect(hid, dest)
            hover = hid == self._hover and self._arr is None
            if hover and Tema.anim:
                r = r.translated(0, -4)
            if rank <= 3:
                self._podio(p, rank, self.items[hid], r, t, hover)
            else:
                self._fila(p, rank, self.items[hid], r, hover)

        if self._arr is not None:
            hueco = dest[self._arr].adjusted(4, 4, -4, -4)
            p.setBrush(con_alfa(Tema.a1(), 28))
            p.setPen(QPen(QColor(Tema.a1()), 2, Qt.PenStyle.DashLine))
            p.drawRoundedRect(hueco, 16, 16)
            self._fantasma(p, vis.index(self._arr) + 1, self.items[self._arr])
        p.end()

    def _avatar(self, p, hid, centro, rad):
        pm = self.av.get(hid)
        if pm is None and hid in self.items:
            datos = self.items[hid]
            pm, listo = avatar_listo(datos["foto"], 128, datos["enc"], self)
            if listo:
                self.av[hid] = pm
        if pm is not None and not pm.isNull():
            p.drawPixmap(QRectF(centro.x() - rad, centro.y() - rad, rad * 2, rad * 2),
                         pm, QRectF(pm.rect()))

    def _barra_cats(self, p, x, y, w, h, it, a1, a2):
        """Barra de actividad dividida por colores según la categoría de sus capturas."""
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(Tema.c("border")))
        p.drawRoundedRect(QRectF(x, y, w, h), h / 2, h / 2)
        tot = it["capturas"]
        if tot <= 0 or not self._max:
            return
        ancho = max(h, w * tot / self._max)
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(x, y, ancho, h), h / 2, h / 2)
        p.setClipPath(clip)
        cats = it.get("cats") or {}
        suma = sum(cats.get(c, 0) for c in CATEGORIAS)
        if suma <= 0:
            gb = QLinearGradient(x, 0, x + ancho, 0)
            gb.setColorAt(0, a1)
            gb.setColorAt(1, a2)
            p.fillRect(QRectF(x, y, ancho, h), QBrush(gb))
        else:
            cx = x
            for c in CATEGORIAS:
                n = cats.get(c, 0)
                if n:
                    sw = ancho * n / suma
                    p.fillRect(QRectF(cx, y, sw + 0.5, h), QColor(CAT_COLOR[c]))
                    cx += sw
        p.restore()

    def _leyenda(self, p, partes, x, y, alin="centro"):
        """partes: [(color, texto)] → puntos de color con su texto, en una sola línea."""
        f = self._f(px=10, bold=True)
        fm = QFontMetrics(f)
        anchos = [fm.horizontalAdvance(t) + 20 for _, t in partes]
        tot = sum(anchos) - 8
        x0 = x - tot / 2 if alin == "centro" else (x - tot if alin == "der" else x)
        p.setFont(f)
        for (col, t), a in zip(partes, anchos):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(col))
            p.drawEllipse(QPointF(x0 + 4, y + 8), 3.5, 3.5)
            p.setPen(QColor(Tema.c("muted")))
            p.drawText(QRectF(x0 + 11, y, a, 16),
                       int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), t)
            x0 += a

    def _miniaturas(self, p, rutas, x, y, w, h, n, gap=6.0, etiqueta=True):
        """rutas: lista de (ruta, categoría). Pone una pequeña etiqueta CG / H en cada una."""
        for k, t in enumerate(rutas[:n]):
            ruta, cat = t if isinstance(t, tuple) else (t, "")
            r = QRectF(x + k * (w + gap), y, w, h)
            dibujar_cover(p, r, CACHE_MINI.obtener_diferido(ruta, 240, self), 8)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(con_alfa(Tema.c("border"), 230), 1))
            p.drawRoundedRect(r, 8, 8)
            if cat and etiqueta and h >= 30:
                ft = self._f(px=9, bold=True)
                tx = ABREV_CAT.get(cat, cat)
                cw = QFontMetrics(ft).horizontalAdvance(tx) + 10
                chip = QRectF(r.left() + 4, r.bottom() - 17, cw, 13)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(con_alfa(CAT_COLOR.get(cat, Tema.a1()), 235))
                p.drawRoundedRect(chip, 6.5, 6.5)
                p.setFont(ft)
                p.setPen(QColor(TEXTO_SOBRE_ACENTO))
                p.drawText(chip, int(Qt.AlignmentFlag.AlignCenter), tx)

    def _paneles_laterales(self, p, vis, dest):
        """Paneles a los lados del podio (solo si sobra sitio). Ranking global: galaxia de
        heroínas y reinas por categoría; ranking de una novela: cumpleaños y actividad."""
        W = self.width()
        izq = min(dest[h].left() for h in vis[:3])
        der = max(dest[h].right() for h in vis[:3])
        wi = min(340.0, izq - 36.0)
        if wi >= 220:
            if self.suprema:
                self._panel_terceras(p, QRectF(izq - 20 - wi, 30, wi, 312), 0)
            else:
                self._panel(p, QRectF(izq - 20 - wi, 30, wi, 312), "🎂  PRÓXIMOS CUMPLEAÑOS",
                            self._cumples, "cumple")
        wd = min(340.0, W - 16.0 - (der + 20.0))
        if wd >= 220:
            if self.suprema:
                self._panel_terceras(p, QRectF(der + 20, 30, wd, 312), 1)
            else:
                self._panel(p, QRectF(der + 20, 30, wd, 312), "📈  MÁS ACTIVAS",
                            self._activas, "activa")

    def _marco_panel(self, p, r, titulo):
        a1 = QColor(Tema.a1())
        card = QColor(Tema.c("card"))
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio, Tema.radio)
        p.fillPath(camino, QBrush(mezclar(card, a1, 0.06)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(Tema.c("border")), 1.2))
        p.drawPath(camino)
        self._txt(p, r.left() + 16, r.top() + 8, r.width() - 32, 24, titulo,
                  self._f(px=11, bold=True, esp=1.4), a1)
        p.setPen(QPen(con_alfa(Tema.c("border"), 200), 1))
        p.drawLine(QPointF(r.left() + 14, r.top() + 38), QPointF(r.right() - 14, r.top() + 38))

    def _en_zona(self, pos):
        for hid, rect in reversed(self._zonas):
            if rect.contains(pos):
                return hid
        return None

    def poner_terceras(self, izq, der):
        """Terceros puestos (de cada novela) que no llegaron al ranking global."""
        self.terceras = [list(izq), list(der)]
        self.av3 = {i["id"]: avatar(i["foto"], 128, i["enc"]) for i in list(izq) + list(der)}
        self.update()

    def _panel_terceras(self, p, r, lado):
        """4 terceros puestos al azar por panel. Se sortean de nuevo cada vez que entras a
        «Heroínas de heroínas». Doble clic en una fila: ir a su galería."""
        self._marco_panel(p, r, "🥉  TERCEROS PUESTOS")
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        bronce = QColor(PODIO[3][0])
        lista = self.terceras[lado]
        if not lista:
            msg = ("Aún no hay terceros puestos libres.\nAparecen cuando una novela tiene 3 o "
                   "más heroínas." if lado == 0 or not self.terceras[0]
                   else "Ya salieron todos los terceros puestos en el otro panel.")
            p.setFont(self._f(max(8.0, Tema.tam - 1)))
            p.setPen(mu)
            p.drawText(r.adjusted(16, 46, -16, -12),
                       int(Qt.AlignmentFlag.AlignCenter.value | Qt.TextFlag.TextWordWrap.value),
                       msg)
            return
        for k, it in enumerate(lista[:4]):
            y = r.top() + 46 + k * 64
            fila = QRectF(r.left() + 10, y + 2, r.width() - 20, 58)
            if it["id"] == self._zona:                           # resalta la fila señalada
                camino = QPainterPath()
                camino.addRoundedRect(fila, 12, 12)
                p.fillPath(camino, con_alfa(bronce, 36))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(bronce, 1.4))
                p.drawPath(camino)
            ac = QPointF(fila.left() + 12 + 22, fila.center().y())
            pm = self.av3.get(it["id"])
            if pm is not None and not pm.isNull():
                p.drawPixmap(QRectF(ac.x() - 22, ac.y() - 22, 44, 44), pm, QRectF(pm.rect()))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(bronce, 2.4))
            p.drawEllipse(ac, 23, 23)
            xt = ac.x() + 32
            wr = fila.right() - 10 - xt
            self._txt(p, xt, fila.top() + 9, wr, 20, it["nombre"],
                      self._f(Tema.tam, bold=True), txt)
            self._txt(p, xt, fila.top() + 31, wr, 18, f"🥉 3.º de {it['juego']}",
                      self._f(max(7.5, Tema.tam - 1)),
                      bronce if Tema.nombre == "Oscuro" else bronce.darker(130))
            self._zonas.append((it["id"], fila))

    def _perfil(self, it):
        """Etiquetas de personalidad según cómo es su colección (solo con sus números)."""
        cats = it.get("cats") or {}
        tot = sum(cats.get(c, 0) for c in CATEGORIAS)
        a2 = QColor(Tema.a2())
        if tot <= 0:
            return [("🌱", "Sin capturas aún", QColor(Tema.c("muted")))]
        tags = []
        dom = max(CATEGORIAS, key=lambda c: cats.get(c, 0))
        if cats[dom] / tot >= 0.6:
            ico, nom = {"CG H": ("🔥", "Reina H"), "CG normal": ("🌸", "Musa del CG"),
                        "SD": ("🎀", "Chibi lover"), "No-CG": ("🧩", "Misteriosa")}[dom]
            tags.append((ico, nom, QColor(CAT_COLOR[dom])))
        else:
            tags.append(("🌈", "Variada", a2))
        if it["capturas"] >= 3 and it["favs"] / it["capturas"] >= 0.25:
            tags.append(("⭐", "Adorada", QColor(PODIO[1][0])))
        if self._max and it["capturas"] == self._max:
            tags.append(("📸", "La más fotografiada", QColor(Tema.a1())))
        return tags

    def _fila_suprema(self, p, rank, it, x, y0, ancho):
        """Fila del ranking global: «Campeona / Subcampeona de la novela» y, debajo, el
        perfil de su colección. Sin repetir la lista de novelas."""
        txt = QColor(Tema.c("text"))
        rol = it.get("rol") or ""
        if rol:
            self._txt(p, x, y0 + 38, ancho, 18, rol, self._f(max(7.5, Tema.tam - 1.5), bold=True),
                      _legible(QColor(Tema.a1())))

    def _panel(self, p, r, titulo, lista, modo):
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card = QColor(Tema.c("card"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio, Tema.radio)
        p.fillPath(camino, QBrush(mezclar(card, a1, 0.06)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(Tema.c("border")), 1.2))
        p.drawPath(camino)
        self._txt(p, r.left() + 16, r.top() + 8, r.width() - 32, 24, titulo,
                  self._f(px=11, bold=True, esp=1.4), a1)
        p.setPen(QPen(con_alfa(Tema.c("border"), 200), 1))
        p.drawLine(QPointF(r.left() + 14, r.top() + 38), QPointF(r.right() - 14, r.top() + 38))
        if not lista:
            p.setFont(self._f(max(8.0, Tema.tam - 1)))
            p.setPen(mu)
            msg = {"cumple": "Aún sin cumpleaños.", "duelos": "Aún sin duelos."
                   }.get(modo, "Todavía no hay capturas.")
            p.drawText(r.adjusted(16, 46, -16, -12),
                       int(Qt.AlignmentFlag.AlignCenter.value | Qt.TextFlag.TextWordWrap.value),
                       msg)
            return
        for i, it in enumerate(lista[:5]):
            y = r.top() + 46 + i * 52
            cx, cy = r.left() + 16 + 18, y + 22
            self._avatar(p, it["id"], QPointF(cx, cy), 18)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(a1, 1.6))
            p.drawEllipse(QPointF(cx, cy), 18, 18)
            xt = cx + 28
            wr = r.right() - 16 - xt
            if modo == "cumple":
                dias = it["dias"]
                pill = "¡HOY! 🎉" if dias == 0 else f"en {dias} d"
                fp = self._f(px=10, bold=True)
                pw = QFontMetrics(fp).horizontalAdvance(pill) + 16
                pr = QRectF(r.right() - 16 - pw, y + 5, pw, 18)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(con_alfa(a1, 46))
                p.drawRoundedRect(pr, 9, 9)
                p.setFont(fp)
                p.setPen(a1)
                p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter), pill)
                self._txt(p, xt, y + 2, wr - pw - 8, 22, it["nombre"],
                          self._f(Tema.tam, bold=True), txt)
                self._txt(p, xt, y + 24, wr, 18, it.get("cumple") or "",
                          self._f(max(7.5, Tema.tam - 1.5)), mu)
            elif modo == "duelos":
                v_, d_ = it["duelos_v"], it["duelos_d"]
                pct = v_ / (v_ + d_)
                fuego = "🔥 " if pct == 1 and v_ + d_ >= 3 else ""
                self._txt(p, xt, y + 2, wr - 70, 22, fuego + it["nombre"],
                          self._f(Tema.tam, bold=True), txt)
                self._txt(p, r.right() - 16 - 70, y + 2, 70, 22, f"{v_}V · {d_}D",
                          self._f(px=11, bold=True), txt, Qt.AlignmentFlag.AlignRight)
                self._barra(p, xt, y + 29, wr - 42, 7, pct, a1, a2)
                self._txt(p, r.right() - 16 - 38, y + 24, 38, 18, f"{round(pct * 100)}%",
                          self._f(px=10, bold=True), mu, Qt.AlignmentFlag.AlignRight)
            else:
                self._txt(p, xt, y + 2, wr - 56, 22, it["nombre"],
                          self._f(Tema.tam, bold=True), txt)
                self._txt(p, r.right() - 16 - 56, y + 2, 56, 22, f"🖼 {it['capturas']}",
                          self._f(Tema.tam, bold=True), txt, Qt.AlignmentFlag.AlignRight)
                self._barra_cats(p, xt, y + 28, wr, 7, it, a1, a2)

    def _podio(self, p, rank, it, r, t, hover):
        c1, c2, titulo = PODIO[rank]
        if self.suprema and rank == 1:
            titulo = "HEROÍNA SUPREMA"
        a, b = QColor(c1), QColor(c2)
        card = QColor(Tema.c("card"))
        ph = self.PED[rank]
        ped = QRectF(r.left(), r.bottom() - ph, r.width(), ph)
        camino = QPainterPath()
        camino.addRoundedRect(ped, 14, 14)
        for i in range(5, 0, -1):
            p.fillPath(camino.translated(0, i * 1.5), QColor(0, 0, 0, 12 - 2 * i))
        g = QLinearGradient(ped.topLeft(), ped.bottomLeft())
        g.setColorAt(0, mezclar(card, a, 0.5))
        g.setColorAt(1, mezclar(card, b, 0.2))
        p.fillPath(camino, QBrush(g))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a if hover else mezclar(QColor(Tema.c("border")), a, 0.7),
                      2.6 if hover else 1.8))
        p.drawPath(camino)

        p.setFont(self._f(px=int(ph * 0.5), bold=True))           # número de fondo
        p.setPen(con_alfa(c1, 36))
        p.drawText(ped.adjusted(0, 4, 0, 0), int(Qt.AlignmentFlag.AlignCenter), str(rank))

        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        w = ped.width() - 24
        x = ped.left() + 12
        self._txt(p, x, ped.top() + 10, w, 26, it["nombre"], self._f(Tema.tam + 3, bold=True),
                  txt, Qt.AlignmentFlag.AlignHCenter)
        self._txt(p, x, ped.top() + 37, w, 18, titulo, self._f(px=11, bold=True, esp=1.5),
                  a if Tema.nombre == "Oscuro" else b.darker(115),
                  Qt.AlignmentFlag.AlignHCenter)
        if self.suprema:
            sub = it.get("rol") or (("📖 " + it["juego"]) if it.get("juego") else "")
        else:
            sub = self._detalle(it)
        if sub:
            self._txt(p, x, ped.top() + 57, w, 18, sub,
                      self._f(max(7.5, Tema.tam - 1.5)), mu, Qt.AlignmentFlag.AlignHCenter)
        self._txt(p, x, ped.top() + 77, w, 18, f"🖼 {it['capturas']} capturas · ★ {it['favs']}",
                  self._f(max(7.5, Tema.tam - 1.5), bold=True), txt,
                  Qt.AlignmentFlag.AlignHCenter)
        self._barra_cats(p, ped.left() + 20, ped.top() + 101, ped.width() - 40, 8, it, a, b)
        cats = it.get("cats") or {}
        partes = [(CAT_COLOR[c], f"{ABREV_CAT[c]} {cats[c]}") for c in CATEGORIAS if cats.get(c)]
        if partes:
            self._leyenda(p, partes, ped.center().x(), ped.top() + 113)
        th = it.get("thumbs") or []                              # miniaturas de sus capturas
        y0 = ped.top() + 136
        disp = ped.bottom() - 12 - y0
        k = min(3, len(th))
        if k and disp >= 28:
            gap = 6.0
            tw = min(120.0, (ped.width() - 24 - gap * (k - 1)) / k)
            tot = tw * k + gap * (k - 1)
            thh = min(disp, tw * 0.64)
            self._miniaturas(p, th, ped.center().x() - tot / 2, y0 + (disp - thh) / 2,
                             tw, thh, k, gap)

        ar = 56 if rank == 1 else 46                             # avatar con resplandor
        acx, acy = r.center().x(), ped.top() - ar - 8
        pulso = 0.5 + 0.5 * sin(t * 2.2 + rank) if Tema.anim else 0.5
        brillo = QRadialGradient(QPointF(acx, acy), ar * 1.9)
        brillo.setColorAt(0, con_alfa(c1, int((60 if rank == 1 else 38) + 50 * pulso)))
        brillo.setColorAt(1, con_alfa(c1, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(brillo))
        p.drawEllipse(QPointF(acx, acy), ar * 1.9, ar * 1.9)
        self._avatar(p, it["id"], QPointF(acx, acy), ar)
        aro = QLinearGradient(acx - ar, acy - ar, acx + ar, acy + ar)
        aro.setColorAt(0, a)
        aro.setColorAt(1, b)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QBrush(aro), 4))
        p.drawEllipse(QPointF(acx, acy), ar + 1, ar + 1)

        tam = 70 if rank == 1 else 56                            # trofeo flotando
        bob = 3 * sin(t * 2 + rank) if Tema.anim else 0
        cy_t = acy - ar - tam * 0.5 - 4 + bob
        dibujar_trofeo(p, QPointF(acx, cy_t), tam, c1, c2)
        if rank == 1:                                            # destellos fijos alrededor del trofeo
            f = QFont(Tema.fuente)
            for k in range(7):
                ang = 0.5 + k * 2 * pi / 7
                rx = 62 + 6 * sin(k * 1.9)
                px, py = acx + cos(ang) * rx, cy_t + sin(ang) * rx * 0.55
                f.setPixelSize(int(11 + 5 * (0.5 + 0.5 * sin(k * 2.3))))
                p.setFont(f)
                p.setPen(con_alfa("#fff2a8", int(170 + 70 * sin(k * 1.7))))
                p.drawText(QRectF(px - 12, py - 12, 24, 24),
                           int(Qt.AlignmentFlag.AlignCenter), "✦")

    def _fila(self, p, rank, it, r, hover):
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card = QColor(Tema.c("card"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio, Tema.radio)
        base = mezclar(card, a1, 0.16 if hover else 0.05)
        g = QLinearGradient(r.topLeft(), r.topRight())
        g.setColorAt(0, base)
        g.setColorAt(1, mezclar(base, a2, 0.14))
        p.fillPath(camino, QBrush(g))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a1 if hover else QColor(Tema.c("border")), 2 if hover else 1.2))
        p.drawPath(camino)
        franja = QPainterPath()                                  # franja de acento
        franja.addRoundedRect(QRectF(r.left() + 1, r.top() + 12, 4, r.height() - 24), 2, 2)
        p.fillPath(franja, a1 if rank <= 5 else mezclar(card, a1, 0.45))

        cy = r.center().y()
        dibujar_medalla(p, QPointF(r.left() + 36, cy), 21, rank, rank <= 5)
        ar, ax = 29, r.left() + 70
        self._avatar(p, it["id"], QPointF(ax + ar, cy), ar)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a1, 2))
        p.drawEllipse(QPointF(ax + ar, cy), ar, ar)

        bw = 132.0
        x_txt = ax + ar * 2 + 14
        resto = r.width() - (x_txt - r.left()) - bw - 36
        th = it.get("thumb_fila") or []                          # 1 captura H al azar
        tw, thh = 98.0, 60.0
        k = min(len(th), 4, max(0, int((resto - 190) // (tw + 6))))
        ancho = max(40.0, resto - k * (tw + 6))
        self._txt(p, x_txt, r.top() + 7, ancho, 26, it["nombre"],
                  self._f(Tema.tam + 2, bold=True), txt)
        if self.suprema:
            self._fila_suprema(p, rank, it, x_txt, r.top(), ancho)
        else:
            l2 = ("📖 " + it["juego"]) if it.get("juego") else ""
            if l2:
                self._txt(p, x_txt, r.top() + 31, ancho, 18, l2,
                          self._f(max(7.5, Tema.tam - 1.5)), a1)
            self._txt(p, x_txt, r.top() + 51, ancho, 18, self._detalle(it) or "Sin más datos",
                      self._f(max(7.5, Tema.tam - 1.5)), mu)
        if k:
            self._miniaturas(p, th, x_txt + ancho + 6, cy - thh / 2, tw, thh, k, 6.0)

        bx = r.right() - bw - 18                                 # bloque de estadísticas
        self._txt(p, bx, r.top() + 9, bw, 20, f"🖼 {it['capturas']}   ★ {it['favs']}",
                  self._f(Tema.tam, bold=True), txt, Qt.AlignmentFlag.AlignRight)
        self._barra_cats(p, bx, cy + 2, bw, 8, it, a1, a2)
        pct = round(100 * it["capturas"] / self._total)
        self._txt(p, bx, r.bottom() - 26, bw, 18, f"{pct} % de las capturas",
                  self._f(px=11), mu, Qt.AlignmentFlag.AlignRight)

    def _fantasma(self, p, rank, it):
        c = self._cursor
        w, h = 250.0, 66.0
        r = QRectF(c.x() - w / 2, c.y() - h / 2, w, h)
        p.save()
        p.setOpacity(0.93)
        camino = QPainterPath()
        camino.addRoundedRect(r, 18, 18)
        for i in range(6, 0, -1):
            p.fillPath(camino.translated(0, i * 2), QColor(0, 0, 0, 14 - 2 * i))
        g = QLinearGradient(r.topLeft(), r.topRight())
        g.setColorAt(0, QColor(Tema.a1()))
        g.setColorAt(1, QColor(Tema.a2()))
        p.fillPath(camino, QBrush(g))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 230), 2))
        p.drawPath(camino)
        self._avatar(p, it["id"], QPointF(r.left() + 36, r.center().y()), 24)
        p.setPen(QPen(QColor(255, 255, 255, 230), 2))
        p.drawEllipse(QPointF(r.left() + 36, r.center().y()), 24, 24)
        f = QFont(Tema.fuente)
        f.setPointSize(Tema.tam + 1)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(TEXTO_SOBRE_ACENTO))
        x = r.left() + 70
        p.drawText(QRectF(x, r.top() + 8, w - 80, 24),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   QFontMetrics(f).elidedText(it["nombre"], Qt.TextElideMode.ElideRight,
                                              int(w - 80)))
        medalla = {1: "🥇 ", 2: "🥈 ", 3: "🥉 "}.get(rank, "")
        f.setBold(False)
        f.setPointSizeF(max(7.5, Tema.tam - 1))
        p.setFont(f)
        p.drawText(QRectF(x, r.top() + 34, w - 80, 22),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   f"{medalla}Puesto {rank}")
        p.restore()


class TopCapturas(QWidget):
    """Ranking de capturas favoritas SIN trofeos: tarjetas grandes para ver bien cada imagen.
    1.º ancho completo, 2.º y 3.º a mitad, el resto en rejilla. Arrastra una tarjeta para
    cambiar su puesto (las demás se apartan y se deslizan). Doble clic: ver en grande."""
    orden_cambiado = Signal(list)       # ids de capturas en el nuevo orden
    abrir = Signal(int)
    menu_pedido = Signal(int, QPoint)
    GAP = 12.0

    def __init__(self):
        super().__init__()
        self.cat = ""
        self.vacio = "Aún no hay capturas favoritas aquí."
        self.items = {}
        self.orden = []
        self.scroll = None
        self._cur = {}
        self._arr = None
        self._cursor = QPointF()
        self._press = None
        self._hover = None
        self._prev = None
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._tick)
        self.setMouseTracking(True)
        self.setMinimumHeight(220)

    # ---------- datos
    def poner(self, items):
        self.items = {i["id"]: i for i in items}
        self.orden = [i["id"] for i in items]
        self._arr = self._prev = self._press = self._hover = None
        self._cur = {k: v for k, v in self._cur.items() if k in self.items}
        self.setMinimumHeight(self._alto(len(items)))
        self.update()

    def showEvent(self, e):
        super().showEvent(e)
        self.timer.start(30 if Tema.anim else 100)

    def hideEvent(self, e):
        super().hideEvent(e)
        self.timer.stop()

    # ---------- geometría
    def _medidas(self):
        W, g = float(max(self.width(), 300)), self.GAP
        c = max(2, int((W + g) // (270 + g)))
        wr = (W - g * (c - 1)) / c
        return W, g, c, wr, wr * 0.5625

    def _bloque_top(self, n):
        """(ancho del 1.º, alto del 1.º, alto del bloque superior, modo ancho).
        En pantallas anchas el 1.º va a la izquierda en 16:9 y el 2.º y 3.º se apilan a su
        derecha; en estrechas se mantiene el 1.º arriba y los otros dos debajo."""
        W, g = float(max(self.width(), 300)), self.GAP
        if W >= 820:
            wh = (W - g) * 0.64
            hh = min(wh * 0.5625, 520.0)
            return hh / 0.5625, hh, hh, True
        h1 = min(W * 0.56, 440.0)
        h2 = ((W - g) / 2) * 0.5625
        return W, h1, h1 + (g + h2 if n > 1 else 0.0), False

    def _alto(self, n):
        if n == 0:
            return 220
        W, g, c, wr, hr = self._medidas()
        wh, hh, alto_top, ancho = self._bloque_top(n)
        y = alto_top
        if n > 3:
            y = alto_top + g + ceil((n - 3) / c) * (hr + g) - g
        return int(y + 16)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        h = self._alto(len(self.orden))
        if self.minimumHeight() != h:
            self.setMinimumHeight(h)

    def _destinos(self, orden):
        n = len(orden)
        W, g, c, wr, hr = self._medidas()
        wh, hh, alto_top, ancho = self._bloque_top(n)
        out = {}
        for i, cid in enumerate(orden):
            if i >= 3:
                j = i - 3
                out[cid] = QRectF((j % c) * (wr + g), alto_top + g + (j // c) * (hr + g), wr, hr)
            elif ancho:
                wR = W - g - wh
                if i == 0:
                    out[cid] = QRectF(0 if n > 1 else (W - wh) / 2, 0, wh, hh)
                elif min(n - 1, 2) == 1:
                    out[cid] = QRectF(wh + g, 0, wR, hh)
                else:
                    h23 = (hh - g) / 2
                    out[cid] = QRectF(wh + g, (i - 1) * (h23 + g), wR, h23)
            else:
                w2 = (W - g) / 2
                h2 = w2 * 0.5625
                out[cid] = (QRectF(0, 0, W, hh) if i == 0
                            else QRectF((i - 1) * (w2 + g), hh + g, w2, h2))
        return out

    def _rect(self, cid, dest):
        return self._cur.get(cid, dest[cid])

    def _tick(self):
        if not self.orden:
            return
        dest = self._destinos(self._prev or self.orden)
        movido = False
        for cid, tgt in dest.items():
            cur = self._cur.get(cid, tgt)
            if Tema.anim:
                v = [cur.x() + (tgt.x() - cur.x()) * 0.3, cur.y() + (tgt.y() - cur.y()) * 0.3,
                     cur.width() + (tgt.width() - cur.width()) * 0.3,
                     cur.height() + (tgt.height() - cur.height()) * 0.3]
                fin = [tgt.x(), tgt.y(), tgt.width(), tgt.height()]
                if all(abs(a - b) < 0.6 for a, b in zip(v, fin)):
                    v = fin
                nuevo = QRectF(*v)
            else:
                nuevo = QRectF(tgt)
            if nuevo != cur:
                movido = True
            self._cur[cid] = nuevo
        if movido:
            self.update()

    # ---------- ratón
    def _en(self, pos):
        dest = self._destinos(self.orden)
        for cid in self.orden:
            if self._rect(cid, dest).contains(pos):
                return cid
        return None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            cid = self._en(e.position())
            self._press = (cid, e.position()) if cid is not None else None
        e.accept()

    def _actualizar_prev(self, pos):
        n = len(self.orden)
        slots = self._destinos(list(range(n)))
        mejor, dmin = 0, None
        for i in range(n):
            r = slots[i]
            dx = max(r.left() - pos.x(), 0, pos.x() - r.right())
            dy = max(r.top() - pos.y(), 0, pos.y() - r.bottom())
            d = dx * dx + dy * dy
            if dmin is None or d < dmin:
                mejor, dmin = i, d
        resto = [h for h in self.orden if h != self._arr]
        resto.insert(mejor, self._arr)
        self._prev = resto

    def _auto_scroll(self, g):
        if self.scroll is None:
            return
        vp = self.scroll.viewport()
        y = vp.mapFromGlobal(g).y()
        barra = self.scroll.verticalScrollBar()
        if y < 50:
            barra.setValue(barra.value() - 22)
        elif y > vp.height() - 50:
            barra.setValue(barra.value() + 22)

    def mouseMoveEvent(self, e):
        pos = e.position()
        if (self._arr is None and self._press and (e.buttons() & Qt.MouseButton.LeftButton)
                and (pos - self._press[1]).toPoint().manhattanLength()
                >= QApplication.startDragDistance()):
            self._arr = self._press[0]
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        if self._arr is not None:
            self._cursor = pos
            self._actualizar_prev(pos)
            self._tick()
            self._auto_scroll(e.globalPosition().toPoint())
            self.update()
            return
        cid = self._en(pos)
        if cid != self._hover:
            self._hover = cid
            self.setCursor(Qt.CursorShape.PointingHandCursor if cid is not None
                           else Qt.CursorShape.ArrowCursor)
            self.update()

    def mouseReleaseEvent(self, e):
        if self._arr is not None:
            arr = self._arr
            nuevo = list(self._prev or self.orden)
            cambio = nuevo != self.orden
            self.orden = nuevo
            self._arr = self._prev = self._press = None
            c = self._cursor                      # aterriza deslizándose desde el cursor
            self._cur[arr] = QRectF(c.x() - 120, c.y() - 67, 240, 135)
            self.unsetCursor()
            self.update()
            if cambio:
                self.orden_cambiado.emit(list(self.orden))
            return
        self._press = None

    def mouseDoubleClickEvent(self, e):
        cid = self._en(e.position())
        if cid is not None:
            self.abrir.emit(cid)

    def contextMenuEvent(self, e):
        cid = self._en(QPointF(e.pos()))
        if cid is not None:
            self.menu_pedido.emit(cid, e.globalPos())

    def leaveEvent(self, e):
        super().leaveEvent(e)
        if self._arr is None and self._hover is not None:
            self._hover = None
            self.update()

    # ---------- dibujo
    def _insignia(self, p, rank, centro):
        rad = 22 if rank == 1 else 19 if rank <= 3 else 14
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if rank <= 3:
            a, b = QColor(PODIO[rank][0]), QColor(PODIO[rank][1])
        else:
            a, b = QColor(Tema.a1()), QColor(Tema.a2())
        g = QLinearGradient(centro.x() - rad, centro.y() - rad,
                            centro.x() + rad, centro.y() + rad)
        g.setColorAt(0, a)
        g.setColorAt(1, b)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 80))
        p.drawEllipse(centro + QPointF(0, 2), rad, rad)
        p.setPen(QPen(QColor(255, 255, 255, 230), 2))
        p.setBrush(QBrush(g))
        p.drawEllipse(centro, rad, rad)
        f = QFont(Tema.fuente)
        f.setBold(True)
        f.setPixelSize(int(rad * (1.0 if rank < 10 else 0.82)))
        p.setFont(f)
        p.setPen(QColor(TEXTO_SOBRE_ACENTO))
        p.drawText(QRectF(centro.x() - rad, centro.y() - rad, rad * 2, rad * 2),
                   int(Qt.AlignmentFlag.AlignCenter), str(rank))
        p.restore()

    def _tarjeta(self, p, rank, it, r, hover):
        radio = 14
        camino = QPainterPath()
        camino.addRoundedRect(r, radio, radio)
        for i in range(4, 0, -1):
            p.fillPath(camino.translated(0, i * 1.6), QColor(0, 0, 0, 16 - 3 * i))
        lado = 1100 if rank == 1 else 720 if rank <= 3 else 480
        dibujar_cover(p, r, CACHE_GRANDE.obtener_diferido(it["ruta"], lado, self), radio)
        alto_g = min(r.height() * 0.5, 86.0)
        p.save()
        p.setClipPath(camino)
        gr = QLinearGradient(r.left(), r.bottom() - alto_g, r.left(), r.bottom())
        gr.setColorAt(0, QColor(0, 0, 0, 0))
        gr.setColorAt(1, QColor(15, 8, 25, 220))
        p.fillRect(QRectF(r.left(), r.bottom() - alto_g, r.width(), alto_g), QBrush(gr))
        p.restore()
        ft = QFont(Tema.fuente)
        ft.setBold(True)
        ft.setPointSizeF(Tema.tam + 5 if rank == 1 else Tema.tam + 2 if rank <= 3
                         else max(8.0, Tema.tam - 0.5))
        p.setFont(ft)
        p.setPen(QColor("#ffffff"))
        w = r.width() - 28
        p.drawText(QRectF(r.left() + 14, r.bottom() - 52, w, 26),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   QFontMetrics(ft).elidedText(it["titulo"], Qt.TextElideMode.ElideRight, int(w)))
        fs = QFont(Tema.fuente)
        fs.setPointSizeF(max(7.5, Tema.tam - 1.5))
        p.setFont(fs)
        p.setPen(QColor(255, 255, 255, 205))
        p.drawText(QRectF(r.left() + 14, r.bottom() - 28, w, 20),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   QFontMetrics(fs).elidedText(it["sub"], Qt.TextElideMode.ElideRight, int(w)))
        self._insignia(p, rank, QPointF(r.left() + 16 + (22 if rank == 1 else 19 if rank <= 3
                                                            else 14), r.top() + 16 + (
            22 if rank == 1 else 19 if rank <= 3 else 14)))
        if hover and self._arr is None:                           # lupa al pasar el ratón
            c = QPointF(r.right() - 24, r.top() + 24)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(15, 8, 25, 170))
            p.drawEllipse(c, 15, 15)
            fl = QFont(Tema.fuente)
            fl.setPixelSize(15)
            p.setFont(fl)
            p.setPen(QColor("#ffffff"))
            p.drawText(QRectF(c.x() - 15, c.y() - 15, 30, 30),
                       int(Qt.AlignmentFlag.AlignCenter), "🔍")
        p.setBrush(Qt.BrushStyle.NoBrush)
        if hover:
            p.setPen(QPen(QColor(Tema.a1()), 3))
        elif rank <= 3:
            p.setPen(QPen(QColor(PODIO[rank][0]), 4 if rank == 1 else 3))
        else:
            p.setPen(QPen(QColor(Tema.c("border")), 1.5))
        p.drawRoundedRect(r, radio, radio)

    def _fantasma(self, p, it):
        c = self._cursor
        r = QRectF(c.x() - 120, c.y() - 67, 240, 135)
        p.save()
        p.setOpacity(0.92)
        camino = QPainterPath()
        camino.addRoundedRect(r, 12, 12)
        for i in range(6, 0, -1):
            p.fillPath(camino.translated(0, i * 2), QColor(0, 0, 0, 14 - 2 * i))
        dibujar_cover(p, r, CACHE_GRANDE.obtener_diferido(it["ruta"], 480, self), 12)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(Tema.a1()), 3))
        p.drawRoundedRect(r, 12, 12)
        p.restore()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        if not self.orden:
            f = QFont(Tema.fuente)
            f.setPointSize(Tema.tam + 1)
            p.setFont(f)
            p.setPen(QColor(Tema.c("muted")))
            p.drawText(QRectF(self.rect()), int(Qt.AlignmentFlag.AlignCenter),
                       "🖼\n\n" + self.vacio)
            return
        vis = self._prev or self.orden
        dest = self._destinos(vis)
        zona = QRectF(e.rect()).adjusted(-40, -40, 40, 40)      # solo lo que está a la vista
        for rank, cid in enumerate(vis, 1):
            if cid == self._arr:
                continue
            r = self._rect(cid, dest)
            if not r.intersects(zona):
                continue
            hover = cid == self._hover and self._arr is None
            if hover and Tema.anim:
                r = r.translated(0, -3)
            try:
                self._tarjeta(p, rank, self.items[cid], r, hover)
            except Exception:
                registrar_error_ui("TopCapturas._tarjeta")
        if self._arr is not None:
            p.setBrush(con_alfa(Tema.a1(), 28))
            p.setPen(QPen(QColor(Tema.a1()), 2, Qt.PenStyle.DashLine))
            p.drawRoundedRect(dest[self._arr].adjusted(3, 3, -3, -3), 14, 14)
            self._fantasma(p, self.items[self._arr])
        p.end()


class TopCapturasMini(TopCapturas):
    """Las mismas 4 partes del top, pero en MINIATURAS (rejilla compacta) para ordenar
    arrastrando. Un clic elige la captura (se ve grande a la derecha)."""
    elegida = Signal(int)               # id de la captura elegida (-1 = ninguna)
    GAP = 10.0
    TILE = 150.0

    def __init__(self):
        super().__init__()
        self.sel = None

    # ---------- geometría: rejilla uniforme
    def _grid(self):
        W, g = float(max(self.width(), 150)), self.GAP
        c = max(1, int((W + g) // (self.TILE + g)))
        wr = (W - g * (c - 1)) / c
        return W, g, c, wr, wr * 0.62

    def _alto(self, n):
        if n == 0:
            return 220
        W, g, c, wr, hr = self._grid()
        return int(ceil(n / c) * (hr + g) + 8)

    def _destinos(self, orden):
        W, g, c, wr, hr = self._grid()
        return {cid: QRectF((i % c) * (wr + g), (i // c) * (hr + g), wr, hr)
                for i, cid in enumerate(orden)}

    # ---------- datos y selección
    def poner(self, items):
        previo = self.sel
        super().poner(items)
        if previo not in self.items:
            previo = self.orden[0] if self.orden else None
        self.sel = previo
        self.elegida.emit(-1 if previo is None else previo)

    def seleccionar(self, cid):
        if cid != self.sel:
            self.sel = cid
            self.update()
        self.elegida.emit(cid)

    def mouseReleaseEvent(self, e):
        arrastre = self._arr is not None
        press = self._press
        super().mouseReleaseEvent(e)
        if (not arrastre and press and press[0] is not None
                and e.button() == Qt.MouseButton.LeftButton):
            self.seleccionar(press[0])

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        it = self.items.get(self._hover) if self._arr is None else None
        if it:
            self.setToolTip(f"#{self.orden.index(it['id']) + 1} · {it['titulo']}\n{it['sub']}")
        else:
            self.setToolTip("")

    # ---------- dibujo
    def _tarjeta(self, p, rank, it, r, hover):
        radio = 10
        sel = it["id"] == self.sel
        a1 = QColor(Tema.a1())
        camino = QPainterPath()
        camino.addRoundedRect(r, radio, radio)
        for i in range(3, 0, -1):
            p.fillPath(camino.translated(0, i * 1.4), QColor(0, 0, 0, 16 - 4 * i))
        dibujar_cover(p, r, CACHE_TOP.obtener_diferido(it["ruta"], 380, self), radio)
        if sel:                                              # resplandor de la elegida
            for i in range(1, 4):
                gl = QPainterPath()
                gl.addRoundedRect(r.adjusted(-i, -i, i, i), radio + i, radio + i)
                p.fillPath(gl, con_alfa(a1, int(70 * (1 - i / 4))))
            p.fillPath(camino, con_alfa(a1, 26))
        # insignia de puesto
        rad = 11.0
        c = QPointF(r.left() + 6 + rad, r.top() + 6 + rad)
        if rank <= 3:
            ca, cb = QColor(PODIO[rank][0]), QColor(PODIO[rank][1])
        else:
            ca, cb = a1, QColor(Tema.a2())
        g = QLinearGradient(c.x() - rad, c.y() - rad, c.x() + rad, c.y() + rad)
        g.setColorAt(0, ca)
        g.setColorAt(1, cb)
        p.setPen(QPen(QColor(255, 255, 255, 225), 1.6))
        p.setBrush(QBrush(g))
        p.drawEllipse(c, rad, rad)
        p.setFont(fnt(px=int(rad * (1.0 if rank < 10 else 0.8)), bold=True))
        p.setPen(QColor(TEXTO_SOBRE_ACENTO))
        p.drawText(QRectF(c.x() - rad, c.y() - rad, rad * 2, rad * 2),
                   int(Qt.AlignmentFlag.AlignCenter), str(rank))
        if it.get("estrellas"):                              # estrellas de la captura
            tx = f"★{it['estrellas']}"
            fe = fnt(px=11, bold=True)
            cw = QFontMetrics(fe).horizontalAdvance(tx) + 12
            chip = QRectF(r.right() - cw - 5, r.bottom() - 21, cw, 16)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(15, 8, 25, 200))
            p.drawRoundedRect(chip, 8, 8)
            p.setFont(fe)
            p.setPen(QColor("#ffd45e"))
            p.drawText(chip, int(Qt.AlignmentFlag.AlignCenter), tx)
        # borde
        p.setBrush(Qt.BrushStyle.NoBrush)
        if sel:
            p.setPen(QPen(a1, 3.4))
        elif hover:
            p.setPen(QPen(a1, 2.4))
        elif rank <= 3:
            p.setPen(QPen(QColor(PODIO[rank][0]), 2.2))
        else:
            p.setPen(QPen(QColor(Tema.c("border")), 1.2))
        p.drawRoundedRect(r, radio, radio)


class VisorGrande(QWidget):
    """Captura elegida en grande, con su título y puesto. Clic: abrir a pantalla completa."""
    clic = Signal()

    def __init__(self):
        super().__init__()
        self.ruta, self.titulo, self.sub, self.rank = "", "", "", 0
        self._t = 1.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(300)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._paso)
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _paso(self, v):
        self._t = float(v)
        self.update()

    def poner(self, ruta, titulo="", sub="", rank=0):
        cambia = ruta != self.ruta
        self.ruta, self.titulo, self.sub, self.rank = ruta, titulo, sub, rank
        if cambia and ruta and Tema.anim:
            self._anim.stop()
            self._anim.start()
        else:
            self._t = 1.0
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.ruta:
            self.clic.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        radio = Tema.radio + 2
        marco = QPainterPath()
        marco.addRoundedRect(r, radio, radio)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, mezclar(card, a1, 0.10))
        g.setColorAt(1, mezclar(card, a2, 0.05))
        p.fillPath(marco, QBrush(g))
        pm = CACHE_GRANDE.obtener_diferido(self.ruta, 1400, self) if self.ruta else QPixmap()
        if pm.isNull():
            p.setFont(fnt(Tema.tam + 1))
            p.setPen(QColor(Tema.c("muted")))
            p.drawText(r, int(Qt.AlignmentFlag.AlignCenter),
                       "🖼")
        else:
            zona = r.adjusted(5, 5, -5, -5)
            esc = min(zona.width() / pm.width(), zona.height() / pm.height())
            w, h = pm.width() * esc, pm.height() * esc
            dest = QRectF(zona.center().x() - w / 2, zona.center().y() - h / 2, w, h)
            ri = 12.0
            ruta_img = QPainterPath()
            ruta_img.addRoundedRect(dest, ri, ri)
            p.save()
            p.setOpacity(self._t)
            p.setClipPath(ruta_img)
            p.drawPixmap(dest, pm, QRectF(pm.rect()))
            p.restore()
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(con_alfa(a1, 170), 2))
            p.drawRoundedRect(dest, ri, ri)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(borde, 1.3))
        p.drawPath(marco)
        p.end()


class InfoHeroinaCaptura(QWidget):
    """Franja elegante bajo la captura grande: solo la foto de la heroína y la novela a la que
    pertenece (el nombre de la heroína ya sale escrito sobre la propia captura)."""
    ALTO = 64

    def __init__(self):
        super().__init__()
        self.d = None
        self.setFixedHeight(self.ALTO)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def poner(self, d):
        """d: None (nada elegido) · {'general': True, 'juego': ...} · datos de la heroína."""
        self.d = d or None
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radio = min(r.height() / 2, Tema.radio + 8)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, mezclar(card, a1, 0.14))
        g.setColorAt(1, mezclar(card, a2, 0.08))
        p.setBrush(QBrush(g))
        p.setPen(QPen(mezclar(borde, a1, 0.35), 1.3))
        p.drawRoundedRect(r, radio, radio)

        d = self.d
        lado = r.height() - 14
        foto = QRectF(r.left() + 8, r.top() + 7, lado, lado)
        if not d:
            p.setFont(fnt(Tema.tam - 0.5))
            p.setPen(QColor(Tema.c("muted")))
            p.drawText(r, int(Qt.AlignmentFlag.AlignCenter),
                       "Elige una captura para ver a qué novela pertenece")
            p.end()
            return
        general = bool(d.get("general"))
        pm = avatar("" if general else d.get("foto", ""), int(lado * 2),
                    None if general else d.get("enc"))
        glow = QColor(a1)
        glow.setAlpha(60)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(glow)
        p.drawEllipse(foto.adjusted(-3, -3, 3, 3))
        p.drawPixmap(foto, pm, QRectF(pm.rect()))
        ar = QLinearGradient(foto.topLeft(), foto.bottomRight())
        ar.setColorAt(0, a1)
        ar.setColorAt(1, a2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QBrush(ar), 2.4))
        p.drawEllipse(foto)

        x = foto.right() + 14
        w = r.right() - x - 16
        nombre = "Sin heroína" if general else d.get("nombre", "")
        texto_el(p, x, r.top() + 9, w, 24, nombre, fnt(Tema.tam + 2.5, bold=True),
                 QColor(Tema.c("text")))
        texto_el(p, x, r.top() + 34, w, 20, f"📖 {d.get('juego', '')}",
                 fnt(max(8.0, Tema.tam - 1)), QColor(Tema.c("muted")))
        p.end()


class PanelCaptura(QWidget):
    """Lado derecho de «Capturas Favoritas»: captura grande + información de su heroína."""
    abrir = Signal()

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        self.visor = VisorGrande()
        self.visor.clic.connect(self.abrir)
        self.info = InfoHeroinaCaptura()
        v.addWidget(self.visor, 1)
        v.addWidget(self.info)


def fnt(pt=None, px=None, bold=False, esp=0.0):
    f = QFont(Tema.fuente)
    if px is not None:
        f.setPixelSize(int(px))
    else:
        f.setPointSizeF(pt if pt is not None else Tema.tam)
    f.setBold(bold)
    if esp:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, esp)
    return f


def texto_el(p, x, y, w, h, texto, f, color, alin=Qt.AlignmentFlag.AlignLeft):
    p.setFont(f)
    p.setPen(color)
    p.drawText(QRectF(x, y, w, h), int(alin | Qt.AlignmentFlag.AlignVCenter),
               QFontMetrics(f).elidedText(texto, Qt.TextElideMode.ElideRight,
                                          int(max(10.0, w))))


def clave_heroina(nombre):
    """Misma heroína aunque cambien mayúsculas o espacios (para no repetirla si sale en
    varias novelas o secuelas)."""
    return " ".join((nombre or "").split()).casefold()


ROSA_H = "#ff5fa2"          # color de las heroínas con escenas H (eroge)


def lista_json(txt):
    """Lista de textos guardada como JSON (alias, redes sociales). Sin límite de elementos."""
    try:
        v = json.loads(txt or "[]")
    except ValueError:
        return []
    if not isinstance(v, list):
        return []
    return [" ".join(str(x).split()) for x in v if str(x).strip()]


_REDES = (("twitter.com", "X"), ("x.com", "X"), ("instagram.com", "Instagram"),
          ("youtube.com", "YouTube"), ("youtu.be", "YouTube"), ("tiktok.com", "TikTok"),
          ("twitch.tv", "Twitch"), ("facebook.com", "Facebook"), ("ameblo.jp", "Blog"),
          ("lineblog.me", "Blog"), ("note.com", "note"), ("pixiv.net", "pixiv"))


def red_social(texto):
    """(texto corto para mostrar, enlace o None) de una red social escrita como enlace o @usuario."""
    t = " ".join((texto or "").split())
    bajo = t.lower()
    url = None
    if re.match(r"https?://", bajo):
        url = t
    elif re.match(r"(www\.)?[\w-]+(\.[\w-]+)+(/|$)", bajo):
        url = "https://" + t
    if not url:
        return t, None
    pu = urllib.parse.urlparse(url)
    host = pu.netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    partes = [x for x in pu.path.split("/") if x]
    if partes and partes[0].lower() in ("channel", "c", "user", "users") and len(partes) > 1:
        partes = partes[1:]
    usuario = partes[0].lstrip("@") if partes else ""
    for dom, etiqueta in _REDES:
        if host == dom or host.endswith("." + dom):
            return (f"{etiqueta} · @{usuario}" if usuario else etiqueta), url
    return host or t, url


def normalizar_vndb(texto):
    """'s1234', 'vndb.org/s1234' o el enlace completo → 'https://vndb.org/s1234'."""
    t = " ".join((texto or "").split())
    if re.fullmatch(r"[sS]\d+", t):
        return "https://vndb.org/" + t.lower()
    if t and not re.match(r"https?://", t, re.I) and "vndb.org" in t.lower():
        return "https://" + t.lstrip("/")
    return t


_TIPOS_RED = (("facebook.com", "fb"), ("fb.com", "fb"), ("fb.me", "fb"),
              ("instagram.com", "ig"), ("x.com", "x"), ("twitter.com", "x"),
              ("vndb.org", "vndb"), ("youtube.com", "yt"), ("youtu.be", "yt"))


def red_social_item(texto):
    """(texto corto, enlace o None, tipo de icono o None) de una red social."""
    t0 = " ".join((texto or "").split())
    if re.fullmatch(r"@?UC[\w-]{20,}", t0):               # solo el id del canal de YouTube
        texto = "https://www.youtube.com/channel/" + t0.lstrip("@")
    corto, url = red_social(texto)
    if not url:
        return corto, None, None
    pu = urllib.parse.urlparse(url)
    host = pu.netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    tipo = next((tp for dom, tp in _TIPOS_RED if host == dom or host.endswith("." + dom)), None)
    if tipo is None:
        return corto, url, None
    partes = [x for x in pu.path.split("/") if x]
    if tipo == "vndb":
        corto = partes[0] if partes else "VNDB"
    elif " · " in corto:
        corto = urllib.parse.unquote(corto.split(" · ", 1)[1])      # solo «@usuario»
        if tipo == "yt" and re.fullmatch(r"@?UC[\w-]{10,}", corto):
            corto = "YouTube"                       # id de canal: no se muestra el código
    if tipo == "yt" and re.fullmatch(r"@?UC[\w-]{10,}", corto):
        corto = "YouTube"
    return corto, url, tipo


_ICONOS_EXT = {}


def _icono_externo(tipo):
    """Logo oficial puesto por ti: guarda `vndb.png` (o icono_vndb.png / .webp / .jpg / .ico /
    .svg) junto al programa o en la carpeta de assets y se usa en lugar del dibujado."""
    if tipo not in _ICONOS_EXT:
        pm = None
        for carpeta in (ROOT, ASSETS):
            for nombre in (f"icono_{tipo}", tipo):
                for ext in (".png", ".webp", ".jpg", ".jpeg", ".ico", ".svg"):
                    f = carpeta / (nombre + ext)
                    if pm is None and f.exists():
                        q = QPixmap(str(f))
                        if not q.isNull():
                            pm = q
        _ICONOS_EXT[tipo] = pm
    return _ICONOS_EXT[tipo]


def dibujar_icono_red(p, r, tipo):
    """Icono vectorial de marca (Facebook, Instagram, X, VNDB, YouTube) dentro del cuadrado r."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s_ = r.width()
    u = s_ / 24.0

    def P(x, y):
        return QPointF(r.x() + x * u, r.y() + y * u)

    def trazo(color, ancho):
        return QPen(QColor(color), ancho * u, Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

    fondo = QPainterPath()
    fondo.addRoundedRect(r, s_ * 0.30, s_ * 0.30)
    p.setPen(Qt.PenStyle.NoPen)
    if tipo == "fb":
        p.fillPath(fondo, QColor("#1877F2"))
        p.setPen(trazo("#ffffff", 2.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        f = QPainterPath(P(13.4, 21))
        f.lineTo(P(13.4, 9.6))
        f.cubicTo(P(13.4, 7.0), P(14.6, 5.4), P(17.2, 5.4))
        f.moveTo(P(9.6, 11.6))
        f.lineTo(P(17.0, 11.6))
        p.drawPath(f)
    elif tipo == "ig":
        g = QLinearGradient(P(1, 23), P(23, 1))
        for pos, col in ((0.0, "#FEDA75"), (0.30, "#FA7E1E"), (0.55, "#D62976"),
                         (0.78, "#962FBF"), (1.0, "#4F5BD5")):
            g.setColorAt(pos, QColor(col))
        p.fillPath(fondo, QBrush(g))
        p.setPen(trazo("#ffffff", 1.9))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(P(5.6, 5.6), P(18.4, 18.4)), 4.6 * u, 4.6 * u)
        p.drawEllipse(P(12, 12), 3.2 * u, 3.2 * u)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(P(16.5, 7.5), 1.05 * u, 1.05 * u)
    elif tipo == "x":
        p.fillPath(fondo, QColor("#0d0d10"))
        p.setPen(QPen(QColor(255, 255, 255, 60), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(fondo)
        p.setPen(trazo("#ffffff", 2.7))
        p.drawLine(P(6.4, 5.6), P(17.6, 18.4))
        p.setPen(trazo("#ffffff", 1.5))
        p.drawLine(P(17.6, 5.6), P(6.4, 18.4))
    elif tipo == "vndb" and _icono_externo("vndb") is not None:
        ext = _icono_externo("vndb")
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setClipPath(fondo)
        p.fillPath(fondo, QColor("#0f2745"))
        k = min(r.width() / ext.width(), r.height() / ext.height())
        w, h = ext.width() * k, ext.height() * k
        p.drawPixmap(QRectF(r.x() + (r.width() - w) / 2, r.y() + (r.height() - h) / 2, w, h),
                     ext, QRectF(ext.rect()))
    elif tipo == "vndb":
        g = QLinearGradient(P(0, 0), P(24, 24))
        g.setColorAt(0, QColor("#2f7fd1"))
        g.setColorAt(1, QColor("#12365f"))
        p.fillPath(fondo, QBrush(g))
        p.setFont(fnt(px=max(6, int(s_ * 0.44)), bold=True))
        p.setPen(QColor("#ffffff"))
        p.drawText(r, int(Qt.AlignmentFlag.AlignCenter), "VN")
    elif tipo == "yt":
        p.fillPath(fondo, QColor("#ff0033"))
        p.setBrush(QColor("#ffffff"))
        p.drawPolygon(QPolygonF([P(9.6, 7.8), P(9.6, 16.2), P(16.8, 12.0)]))
    p.restore()


def pixmap_icono_red(tipo, tam=24):
    dpr = 2
    pm = QPixmap(tam * dpr, tam * dpr)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.GlobalColor.transparent)
    q = QPainter(pm)
    dibujar_icono_red(q, QRectF(0, 0, tam, tam), tipo)
    q.end()
    return pm


def clave_seiyuu(nombre):
    """Misma seiyuu aunque cambien mayúsculas o espacios."""
    return " ".join((nombre or "").split()).casefold()


def _legible(color):
    """Acento oscurecido en el modo claro para que el texto pequeño se lea bien."""
    c = QColor(color)
    return mezclar(c, QColor(0, 0, 0), 0.38) if Tema.nombre == "Claro" else c


DESC_CAT = {"CG H": "Tus escenas H favoritas", "CG normal": "Tus ilustraciones favoritas",
            "SD": "Tus chibis favoritos", "No-CG": "Tus otras imágenes favoritas"}


class CabeceraTop(QWidget):
    """Encabezado elegante de cada parte del Top de capturas (color propio por categoría)."""

    def __init__(self, parte, cat):
        super().__init__()
        self.parte, self.cat = parte, cat
        self.n = self.novelas = self.heroinas = 0
        self.setFixedHeight(92)

    def poner(self, n, novelas, heroinas):
        self.n, self.novelas, self.heroinas = n, novelas, heroinas
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        col = QColor(CAT_COLOR.get(self.cat, Tema.a1()))
        a2 = QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio + 2, Tema.radio + 2)
        g = QLinearGradient(r.topLeft(), r.topRight())
        g.setColorAt(0, mezclar(card, col, 0.30))
        g.setColorAt(0.55, mezclar(card, col, 0.08))
        g.setColorAt(1, mezclar(card, a2, 0.12))
        p.fillPath(camino, QBrush(g))
        p.save()                                              # estrella decorativa de fondo
        p.setClipPath(camino)
        p.setFont(fnt(px=130, bold=True))
        p.setPen(con_alfa(col, 28))
        p.drawText(QRectF(r.right() - 200, r.top() - 16, 210, r.height() + 32),
                   int(Qt.AlignmentFlag.AlignCenter), "✦")
        p.restore()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(mezclar(borde, col, 0.55), 1.4))
        p.drawPath(camino)

        c = QPointF(r.left() + 52, r.center().y())            # medalla con el número de parte
        rad = 30.0
        gm = QLinearGradient(c.x() - rad, c.y() - rad, c.x() + rad, c.y() + rad)
        gm.setColorAt(0, col.lighter(118))
        gm.setColorAt(1, col.darker(125))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 60))
        p.drawEllipse(c + QPointF(0, 2), rad, rad)
        p.setPen(QPen(QColor(255, 255, 255, 220), 2.5))
        p.setBrush(QBrush(gm))
        p.drawEllipse(c, rad, rad)
        p.setFont(fnt(px=30, bold=True))
        p.setPen(QColor(TEXTO_SOBRE_ACENTO))
        p.drawText(QRectF(c.x() - rad, c.y() - rad, rad * 2, rad * 2),
                   int(Qt.AlignmentFlag.AlignCenter), str(self.parte))

        x, w = r.left() + 100, r.width() - 116
        texto_el(p, x, r.top() + 11, w, 18, f"PARTE {self.parte} DE 4",
                 fnt(px=11, bold=True, esp=2.0), _legible(col))
        texto_el(p, x, r.top() + 29, w, 32, f"Top {self.cat}", fnt(Tema.tam + 8, bold=True), txt)
        texto_el(p, x, r.top() + 62, w, 20, DESC_CAT.get(self.cat, ""),
                 fnt(max(8.0, Tema.tam - 1)), mu)

        chips = [f"🖼 {self.n} {'captura' if self.n == 1 else 'capturas'}"]
        if self.novelas:
            chips.append(f"📖 {self.novelas} {'novela' if self.novelas == 1 else 'novelas'}")
        if self.heroinas:
            chips.append(f"💗 {self.heroinas} {'heroína' if self.heroinas == 1 else 'heroínas'}")
        fc = fnt(px=12, bold=True)
        fm = QFontMetrics(fc)
        visibles, tot = [], 0.0
        for t in chips:
            a = fm.horizontalAdvance(t) + 24
            if not visibles or tot + a + 8 <= r.width() - 430:
                visibles.append((t, a))
                tot += a + 8
        x0 = r.right() - 18 - tot + 8
        for t, a in visibles:
            pr = QRectF(x0, r.center().y() - 14, a, 28)
            p.setPen(QPen(con_alfa(col, 150), 1.2))
            p.setBrush(con_alfa(col, 48))
            p.drawRoundedRect(pr, 14, 14)
            p.setFont(fc)
            p.setPen(txt)
            p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter), t)
            x0 += a + 8
        p.end()


class FilaInfo(QWidget):
    """Tarjeta pintada: medalla de puesto + avatar + título + dos líneas + etiqueta."""
    clic = Signal()

    def __init__(self, pm, titulo, sub="", sub2="", pill="", rank=0, destacada=False,
                 etiqueta=""):
        super().__init__()
        self.pm, self.titulo, self.sub, self.sub2 = pm, titulo, sub, sub2
        self.pill, self.rank, self.destacada, self.etiqueta = pill, rank, destacada, etiqueta
        self._hover = False
        self.setFixedHeight(108 if destacada else 76)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def mouseDoubleClickEvent(self, e):
        self.clic.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio, Tema.radio)
        base = mezclar(card, a1, 0.24 if self.destacada else (0.15 if self._hover else 0.05))
        g = QLinearGradient(r.topLeft(), r.topRight())
        g.setColorAt(0, base)
        g.setColorAt(1, mezclar(base, a2, 0.16))
        p.fillPath(camino, QBrush(g))
        resalta = self._hover or self.destacada
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a1 if resalta else borde, 2 if resalta else 1.2))
        p.drawPath(camino)

        cy = r.center().y()
        if self.rank:
            dibujar_medalla(p, QPointF(r.left() + 34, cy), 22 if self.destacada else 18,
                            self.rank, self.destacada)
        ar = 36.0 if self.destacada else 26.0
        ax = r.left() + 72
        if self.pm is not None and not self.pm.isNull():
            p.drawPixmap(QRectF(ax, cy - ar, ar * 2, ar * 2), self.pm, QRectF(self.pm.rect()))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a1, 2.2))
        p.drawEllipse(QPointF(ax + ar, cy), ar, ar)

        x = ax + ar * 2 + 16
        w = r.right() - x - 14
        pw = 0.0
        if self.pill:
            fp = fnt(px=12, bold=True)
            pw = QFontMetrics(fp).horizontalAdvance(self.pill) + 22
            pr = QRectF(r.right() - 14 - pw, cy - 13, pw, 26)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(con_alfa(a1, 72 if self.destacada else 46))
            p.drawRoundedRect(pr, 13, 13)
            p.setFont(fp)
            p.setPen(_legible(a1))
            p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter), self.pill)
            pw += 10
        wt = w - pw
        chico = fnt(max(8.0, Tema.tam - 1.5))
        if self.destacada:
            texto_el(p, x, r.top() + 10, wt, 16, self.etiqueta,
                     fnt(px=10, bold=True, esp=1.6), _legible(a1))
            texto_el(p, x, r.top() + 26, wt, 30, self.titulo, fnt(Tema.tam + 4, bold=True), txt)
            texto_el(p, x, r.top() + 58, wt, 18, self.sub, chico, _legible(a1))
            texto_el(p, x, r.top() + 78, wt, 18, self.sub2, chico, mu)
        else:
            texto_el(p, x, r.top() + 8, wt, 24, self.titulo, fnt(Tema.tam + 1, bold=True), txt)
            texto_el(p, x, r.top() + 32, wt, 18, self.sub, chico, _legible(a1))
            texto_el(p, x, r.top() + 50, wt, 18, self.sub2, chico, mu)
        p.end()


class FilaMedidas(QWidget):
    """Fila del top de medidas: medalla (o icono), foto, nombre, lo que ganó, su cifra y la
    silueta / medidor. Entra deslizándose, la cifra cuenta hasta su valor, una barrita se
    llena según lo cerca que está de la primera y la campeona lleva un brillo que la recorre."""
    clic = Signal()

    def __init__(self, pm, h, rank, destacada, etiqueta, valor, sufijo, modo, ctx,
                 frac=1.0, campeona=False, retraso=0):
        super().__init__()
        self.pm, self.h, self.rank, self.destacada = pm, h, rank, destacada
        self.etiqueta, self.valor, self.sufijo = etiqueta, valor, sufijo
        self.modo, self.ctx, self.frac, self.campeona = modo, ctx, frac, campeona
        self.novelas = " · ".join(h.get("novelas") or [])
        self._hover = False
        self._t = 1.0                  # progreso de la entrada (0 → 1)
        self._brillo = 2.0             # posición del brillo (0 → 1 = recorre la tarjeta)
        self.setFixedHeight(96 if destacada else 70)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if Tema.anim:
            self._t = 0.0
            self._anim = QVariantAnimation(self)
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.setDuration(700)
            self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._anim.valueChanged.connect(self._entrada)
            self._arranque = QTimer(self)
            self._arranque.setSingleShot(True)
            self._arranque.timeout.connect(self._anim.start)
            self._arranque.start(max(0, int(retraso)))
            if destacada:
                self._brillo = 1.2
                self._reloj = QTimer(self)
                self._reloj.setInterval(33)
                self._reloj.timeout.connect(self._tic)
                self._reloj.start()

    def _entrada(self, v):
        self._t = float(v)
        self.update()

    def _tic(self):
        if not self.isVisible():
            return
        self._brillo += 0.018
        if self._brillo > 2.6:         # tras el barrido, una pausa antes del siguiente
            self._brillo = 0.0
        if self._brillo <= 1.0:
            self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def mouseDoubleClickEvent(self, e):
        self.clic.emit()

    # ---------- dibujo de la figura
    def _silueta(self, p, box, a1, a2):
        h, ctx = self.h, self.ctx
        ref = float(ctx.get("ref_med") or max(h["busto"], h["cadera"]))
        cx, top, bot = box.center().x(), box.top() + 2, box.bottom() - 2
        alto = bot - top
        ymid = top + alto * 0.42

        def mitad(v):
            return max(4.0, box.width() * (v / ref) / 2.0)
        wb, wc, wh = mitad(h["busto"]), mitad(h["cintura"]), mitad(h["cadera"])
        k = alto * 0.22
        path = QPainterPath()
        path.moveTo(cx - wb, top)
        path.cubicTo(cx - wb, top + k, cx - wc, ymid - k, cx - wc, ymid)
        path.cubicTo(cx - wc, ymid + k, cx - wh, bot - k, cx - wh, bot)
        path.lineTo(cx + wh, bot)
        path.cubicTo(cx + wh, bot - k, cx + wc, ymid + k, cx + wc, ymid)
        path.cubicTo(cx + wc, ymid - k, cx + wb, top + k, cx + wb, top)
        path.closeSubpath()
        g = QLinearGradient(box.topLeft(), box.bottomLeft())
        g.setColorAt(0, con_alfa(a1, 150))
        g.setColorAt(1, con_alfa(a2, 150))
        p.setBrush(QBrush(g))
        p.setPen(QPen(a1, 1.6))
        p.drawPath(path)
        nivel = {"busto": (top, wb), "cintura": (ymid, wc), "cadera": (bot, wh)}.get(self.modo)
        if nivel:                                  # marca la medida que se está comparando
            y, w = nivel
            p.setPen(QPen(QColor(Tema.c("text")), 2.2, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(cx - w - 4, y), QPointF(cx + w + 4, y))

    def _medidor(self, p, box, a1, a2):
        lo, hi = self.ctx.get("min_alt", 140), self.ctx.get("max_alt", 180)
        frac = 0.5 if hi <= lo else (self.h["altura"] - lo) / float(hi - lo)
        frac = max(0.1, min(1.0, 0.1 + 0.9 * frac))
        pista = QRectF(box.center().x() - 8, box.top(), 16, box.height())
        p.setPen(QPen(QColor(Tema.c("border")), 1.2))
        p.setBrush(QColor(Tema.c("card")))
        p.drawRoundedRect(pista, 8, 8)
        alto = max(6.0, pista.height() * frac * self._t)
        lleno = QRectF(pista.left(), pista.bottom() - alto, pista.width(), alto)
        g = QLinearGradient(lleno.topLeft(), lleno.bottomLeft())
        g.setColorAt(0, a1)
        g.setColorAt(1, a2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawRoundedRect(lleno, 8, 8)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        t = self._t
        p.setOpacity(min(1.0, t * 2.0))
        p.translate(-(1.0 - t) * 48, 0)          # entra deslizándose desde la izquierda
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt = QColor(Tema.c("text"))
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio, Tema.radio)
        base = mezclar(card, a1, 0.24 if self.destacada else (0.15 if self._hover else 0.05))
        g = QLinearGradient(r.topLeft(), r.topRight())
        g.setColorAt(0, base)
        g.setColorAt(1, mezclar(base, a2, 0.16))
        p.fillPath(camino, QBrush(g))
        if self.destacada and 0.0 <= self._brillo <= 1.0:      # brillo que recorre la tarjeta
            p.save()
            p.setClipPath(camino)
            bw = 90.0
            x0 = r.left() - bw + self._brillo * (r.width() + bw * 2)
            gb = QLinearGradient(x0, 0, x0 + bw, 0)
            gb.setColorAt(0, QColor(255, 255, 255, 0))
            gb.setColorAt(0.5, QColor(255, 255, 255, 60))
            gb.setColorAt(1, QColor(255, 255, 255, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(gb))
            p.drawRect(QRectF(x0, r.top(), bw, r.height()))
            p.restore()
        resalta = self._hover or self.destacada
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a1 if resalta else borde, 2 if resalta else 1.2))
        p.drawPath(camino)

        if not self.campeona:                                    # barrita «de carrera»
            bx, by, bt = r.left() + 16, r.bottom() - 10, r.width() - 32
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(con_alfa(a1, 30))
            p.drawRoundedRect(QRectF(bx, by, bt, 4), 2, 2)
            gb = QLinearGradient(bx, 0, bx + bt, 0)
            gb.setColorAt(0, a1)
            gb.setColorAt(1, a2)
            p.setBrush(QBrush(gb))
            p.drawRoundedRect(QRectF(bx, by, max(6.0, bt * max(0.02, min(1.0, self.frac)) * t),
                                     4), 2, 2)
        cy = r.top() + (r.height() - (0 if self.campeona else 8)) / 2.0

        if self.campeona:                                        # campeona: franja de color
            gf = QLinearGradient(0, r.top(), 0, r.bottom())
            gf.setColorAt(0, a1)
            gf.setColorAt(1, a2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(gf))
            p.drawRoundedRect(QRectF(r.left() + 9, r.top() + 14, 5, r.height() - 28), 2.5, 2.5)
        else:
            dibujar_medalla(p, QPointF(r.left() + 34, cy), 22 if self.destacada else 17,
                            self.rank, self.destacada)
        ar = 32.0 if self.destacada else 24.0
        ax = r.left() + (30 if self.campeona else 72)
        if self.pm is not None and not self.pm.isNull():
            p.drawPixmap(QRectF(ax, cy - ar, ar * 2, ar * 2), self.pm, QRectF(self.pm.rect()))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a1, 2.2))
        p.drawEllipse(QPointF(ax + ar, cy), ar, ar)

        # figura a la derecha
        figura = QRectF(r.right() - 14 - 56, r.top() + 10, 56,
                        r.height() - 20 - (0 if self.campeona else 8))
        if self.modo in ("alta", "baja"):
            self._medidor(p, figura.adjusted(18, 0, -18, 0), a1, a2)
        else:
            self._silueta(p, figura, a1, a2)

        # cifra (cuenta hasta su valor)
        x = ax + ar * 2 + 16
        fp = fnt(px=15 if self.destacada else 13, bold=True)
        fm = QFontMetrics(fp)
        pw = fm.horizontalAdvance(f"{self.valor}{self.sufijo}") + 26
        zona_der = figura.left() - 12
        pr = QRectF(zona_der - pw, cy - 14, pw, 28)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(con_alfa(a1, 72 if self.destacada else 46))
        p.drawRoundedRect(pr, 14, 14)
        p.setFont(fp)
        p.setPen(_legible(a1))
        p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter),
                   f"{int(round(self.valor * t))}{self.sufijo}")

        # lo que ganó (solo la primera), nombre y novela
        wt = pr.left() - x - 8
        mu = QColor(Tema.c("muted"))
        chico = fnt(max(8.0, Tema.tam - 1.5))
        if self.etiqueta:
            texto_el(p, x, cy - 36, wt, 16, self.etiqueta,
                     fnt(px=10, bold=True, esp=1.6), _legible(a1))
            texto_el(p, x, cy - 19, wt, 28, self.h["nombre"],
                     fnt(Tema.tam + 3, bold=True), txt)
            texto_el(p, x, cy + 10, wt, 18, self.novelas, chico, mu)
        else:
            texto_el(p, x, cy - 19, wt, 26, self.h["nombre"],
                     fnt(Tema.tam + 1, bold=True), txt)
            texto_el(p, x, cy + 6, wt, 18, self.novelas, chico, mu)
        p.end()


COLOR_PLATA, COLOR_BRONCE = "#c9d1dc", "#d08a4a"


class PodioMedidas(QWidget):
    """Podio de las 3 primeras: foto grande sobre un pedestal con su nombre y su cifra. El
    pedestal «sube» al entrar y la cifra cuenta hasta su valor; la primera lleva corona."""
    abrir = Signal(int)
    PH = (150, 130, 114)                 # alto del pedestal: 1.º, 2.º, 3.º
    RAD = (66, 56, 52)                   # radio de la foto

    def __init__(self, entradas, modo, titulo, ctx):
        super().__init__()
        self.e, self.modo, self.titulo, self.ctx = entradas, modo, titulo, ctx
        self._hover, self._t = -1, 1.0
        self.setFixedHeight(352)
        self.setMouseTracking(True)
        if Tema.anim:
            self._t = 0.0
            self._anim = QVariantAnimation(self)
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.setDuration(950)
            self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._anim.valueChanged.connect(self._paso)
            self._anim.start()

    def _paso(self, v):
        self._t = float(v)
        self.update()

    def _columnas(self):
        n = len(self.e)
        orden = [0] if n == 1 else [1, 0] if n == 2 else [1, 0, 2]
        W = self.width()
        cw = min(330.0, (W - 20) / max(1, len(orden)))
        x0 = (W - cw * len(orden)) / 2.0
        return [(i, x0 + cw * (k + 0.5), cw) for k, i in enumerate(orden)]

    def _geom(self, i, cx, cw):
        H = self.height()
        ph = self.PH[i] * self._t
        ped = QRectF(cx - cw / 2 + 8, H - ph, cw - 16, ph)
        r = self.RAD[i]
        return ped, QPointF(cx, ped.top() - r - 8), r

    def _en(self, pos):
        for i, cx, cw in self._columnas():
            ped, c, r = self._geom(i, cx, cw)
            if ped.contains(pos) or (pos.x() - c.x()) ** 2 + (pos.y() - c.y()) ** 2 <= r * r:
                return i
        return -1

    def mouseMoveEvent(self, e):
        i = self._en(e.position())
        self.setCursor(Qt.CursorShape.PointingHandCursor if i >= 0
                       else Qt.CursorShape.ArrowCursor)
        if i != self._hover:
            self._hover = i
            self.update()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._hover = -1
        self.update()

    def mouseDoubleClickEvent(self, e):
        i = self._en(e.position())
        if i >= 0:
            self.abrir.emit(self.e[i]["h"]["id"])

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        texto_el(p, 6, 0, self.width() - 12, 26, self.titulo,
                 fnt(px=13, bold=True, esp=2.0), _legible(a1))
        metales = (QColor(ORO), QColor(COLOR_PLATA), QColor(COLOR_BRONCE))
        for i, cx, cw in self._columnas():
            d = self.e[i]
            ped, c, r = self._geom(i, cx, cw)
            metal = metales[i]
            hov = i == self._hover
            camino = QPainterPath()
            camino.addRoundedRect(ped, 16, 16)
            g = QLinearGradient(ped.topLeft(), ped.bottomLeft())
            g.setColorAt(0, mezclar(card, metal, 0.42 if hov else 0.30))
            g.setColorAt(1, mezclar(card, a2, 0.10))
            p.fillPath(camino, QBrush(g))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(metal, 2.2 if hov else 1.6))
            p.drawPath(camino)
            # numeral grande, tenue, detrás del texto
            p.setFont(fnt(px=92, bold=True))
            p.setPen(con_alfa(metal, 46))
            p.drawText(QRectF(ped.right() - 92, ped.top() - 4, 84, ped.height()),
                       int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                       str(d["rank"]))
            # foto con aro del color de su medalla
            halo = QRadialGradient(c, r + 26)
            halo.setColorAt(0.55, con_alfa(metal, 120 if i == 0 else 70))
            halo.setColorAt(1, con_alfa(metal, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(halo))
            p.drawEllipse(c, r + 26, r + 26)
            pm = d["pm"]
            if pm is not None and not pm.isNull():
                p.drawPixmap(QRectF(c.x() - r, c.y() - r, r * 2, r * 2), pm, QRectF(pm.rect()))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(metal, 5 if i == 0 else 4))
            p.drawEllipse(c, r + 1, r + 1)
            if i == 0:
                p.setFont(fnt(px=30))
                p.setPen(QColor(ORO))
                p.drawText(QRectF(c.x() - 30, c.y() - r - 40, 60, 36),
                           int(Qt.AlignmentFlag.AlignCenter), "👑")
            # nombre, novela y cifra dentro del pedestal
            tx, tw = ped.left() + 14, ped.width() - 28
            if self._t > 0.85:
                texto_el(p, tx, ped.top() + 10, tw, 26, d["h"]["nombre"],
                         fnt(Tema.tam + (3 if i == 0 else 1), bold=True), txt,
                         Qt.AlignmentFlag.AlignLeft)
                texto_el(p, tx, ped.top() + 36, tw, 18,
                         " · ".join(d["h"].get("novelas") or []),
                         fnt(max(8.0, Tema.tam - 1.5)), mu)
            fp = fnt(px=15 if i == 0 else 13, bold=True)
            cifra = f"{int(round(d['valor'] * self._t))}{d['suf']}"
            pw = QFontMetrics(fp).horizontalAdvance(cifra) + 26
            pr = QRectF(tx, ped.bottom() - 36, pw, 28)
            if pr.top() > ped.top() + 56:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(con_alfa(metal, 90))
                p.drawRoundedRect(pr, 14, 14)
                p.setFont(fp)
                p.setPen(txt)
                p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter), cifra)
        p.end()


class TileMedidas(QWidget):
    """Tarjeta del top (puesto 4 en adelante) o de «Las reinas»: foto vertical con la medalla
    en la esquina, nombre, novela, cifra, barra de «qué tan cerca está de la primera» y su
    silueta (o medidor de altura). Entra con un fundido y la cifra cuenta hasta su valor."""
    clic = Signal()

    def __init__(self, pm_ruta, enc, h, rank, etiqueta, valor, sufijo, modo, ctx, frac=1.0,
                 retraso=0):
        super().__init__()
        self.ruta, self.enc, self.h, self.rank = pm_ruta, enc, h, rank
        self.etiqueta, self.valor, self.sufijo = etiqueta, valor, sufijo
        self.modo, self.ctx, self.frac = modo, ctx, frac
        self.novelas = " · ".join(h.get("novelas") or [])
        self._hover, self._t = False, 1.0
        self.setFixedHeight(112 if etiqueta else 92)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if Tema.anim:
            self._t = 0.0
            self._anim = QVariantAnimation(self)
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.setDuration(650)
            self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._anim.valueChanged.connect(self._paso)
            self._arranque = QTimer(self)
            self._arranque.setSingleShot(True)
            self._arranque.timeout.connect(self._anim.start)
            self._arranque.start(max(0, int(retraso)))

    def _paso(self, v):
        self._t = float(v)
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def mouseDoubleClickEvent(self, e):
        self.clic.emit()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        t = self._t
        p.setOpacity(min(1.0, t * 2.0))
        p.translate(0, (1.0 - t) * 14)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio + 2, Tema.radio + 2)
        base = mezclar(card, a1, 0.18 if self._hover else (0.12 if self.etiqueta else 0.05))
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, base)
        g.setColorAt(1, mezclar(base, a2, 0.14))
        p.fillPath(camino, QBrush(g))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a1 if (self._hover or self.etiqueta) else borde,
                      2 if self._hover else 1.2))
        p.drawPath(camino)

        # foto vertical + medalla
        ph = r.height() - 22
        foto = QRectF(r.left() + 12, r.top() + 9, 66, ph - (0 if self.etiqueta else 4))
        dibujar_cover(p, foto, CACHE_GRANDE.obtener(self.h["foto"], 200), 12, self.enc)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a1, 2))
        p.drawRoundedRect(foto, 12, 12)
        dibujar_medalla(p, QPointF(foto.left() + 2, foto.top() + 2), 12, self.rank, False)

        # figura a la derecha
        figura = QRectF(r.right() - 14 - 40, r.top() + 10, 40, r.height() - 30)
        if self.modo in ("alta", "baja"):
            FilaMedidas._medidor(self, p, figura.adjusted(12, 0, -12, 0), a1, a2)
        else:
            FilaMedidas._silueta(self, p, figura, a1, a2)

        # cifra
        x = foto.right() + 14
        fp = fnt(px=14 if self.etiqueta else 13, bold=True)
        cifra = f"{int(round(self.valor * t))}{self.sufijo}"
        pw = QFontMetrics(fp).horizontalAdvance(cifra) + 24
        cy = r.top() + (36 if self.etiqueta else 28)
        pr = QRectF(figura.left() - 10 - pw, cy - 13, pw, 26)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(con_alfa(a1, 60))
        p.drawRoundedRect(pr, 13, 13)
        p.setFont(fp)
        p.setPen(_legible(a1))
        p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter), cifra)

        wt = pr.left() - x - 8
        y0 = r.top() + 8
        if self.etiqueta:
            texto_el(p, x, y0, figura.left() - x - 8, 18, self.etiqueta,
                     fnt(px=10, bold=True, esp=1.4), _legible(a1))
            y0 += 20
        texto_el(p, x, y0 + 4, wt, 26, self.h["nombre"], fnt(Tema.tam + 1, bold=True), txt)
        texto_el(p, x, y0 + 30, figura.left() - x - 8, 18, self.novelas,
                 fnt(max(8.0, Tema.tam - 1.5)), mu)

        # barra «qué cerca está de la primera»
        bx, by, bt = x, r.bottom() - 13, figura.left() - x - 10
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(con_alfa(a1, 30))
        p.drawRoundedRect(QRectF(bx, by, bt, 4), 2, 2)
        gb = QLinearGradient(bx, 0, bx + bt, 0)
        gb.setColorAt(0, a1)
        gb.setColorAt(1, a2)
        p.setBrush(QBrush(gb))
        p.drawRoundedRect(QRectF(bx, by, max(6.0, bt * max(0.02, min(1.0, self.frac)) * t), 4),
                          2, 2)
        p.end()


class RejillaTiles(QWidget):
    """Tarjetas en 1, 2 o 3 columnas según el ancho disponible."""

    def __init__(self, tiles, ancho_min=430):
        super().__init__()
        self.tiles, self.ancho_min, self.cols = tiles, ancho_min, 0
        self.g = QGridLayout(self)
        self.g.setContentsMargins(0, 0, 0, 0)
        self.g.setSpacing(10)
        self._reflow(2)

    def _reflow(self, cols):
        self.cols = cols
        for t in self.tiles:
            self.g.removeWidget(t)
        for i, t in enumerate(self.tiles):
            self.g.addWidget(t, i // cols, i % cols)
        for c in range(4):
            self.g.setColumnStretch(c, 1 if c < cols else 0)
        self.updateGeometry()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        cols = max(1, min(3, int((self.width() + 10) // (self.ancho_min + 10))))
        if cols != self.cols:
            self._reflow(cols)


class TarjetaSeiyuu(QWidget):
    """Seiyuu con su foto GRANDE, sus datos (cumpleaños y redes) y todas las heroínas a
    las que da voz. Las heroínas con escenas H (eroge) van en rosado con una «H» al costado."""
    abrir = Signal(int)                 # id de heroína (doble clic)
    cambiar_foto = Signal(str)          # clave de la seiyuu (doble clic en su foto)
    editar = Signal(str)                # clave de la seiyuu (botón «Datos»)
    menu = Signal(str, QPoint)
    CH, G, CAB_MIN = 72, 10, 170

    def __init__(self, d):
        super().__init__()
        self.d = d
        self.av = None
        self.avs = [None] * len(d["heroinas"])
        self._listo = False                  # las fotos se preparan al pintar, no al crear
        self._hover = -1
        self._hover_red = None
        self._hover_edit = False
        self._geo = (None, None)
        self.setMouseTracking(True)
        self.setFixedHeight(self._alto(820))

    def recargar_foto(self, repintar=True):
        self._listo = False
        if repintar:
            self.update()

    def _preparar(self):
        """Dibuja las fotos redondas la primera vez que la tarjeta se ve (y solo si ya cargaron)."""
        if self._listo:
            return
        d = self.d
        todo = True
        ruta = d["foto"] if d["foto"] and Path(d["foto"]).exists() else ""
        if ruta:
            self.av, ok = avatar_listo(ruta, 248, d.get("enc"), self)
            todo = todo and ok
        else:
            self.av = None
        avs = []
        for h in d["heroinas"]:
            pm, ok = avatar_listo(h["foto"], 112, h["enc"], self)
            avs.append(pm)
            todo = todo and ok
        self.avs = avs
        self._listo = todo

    def recargar_datos(self):
        """Tras editar cumpleaños / redes: recalcula la cabecera y la altura."""
        self._geo = (None, None)
        self.setFixedHeight(self._alto(self.width() or 820))
        self.update()

    # ---- cabecera: cumpleaños → redes sociales (en ese orden)
    def _cabecera(self, W):
        d = self.d
        clave = (W, d.get("cumple") or "",
                 d.get("anio") or 0, d.get("vndb") or "", tuple(d.get("redes") or ()))
        if self._geo[0] == clave:
            return self._geo[1]
        fm = QFontMetrics(fnt(max(8.5, Tema.tam - 1), bold=True))
        x0 = 20 + 124 + 22
        et_w = 74.0
        ancho = max(160.0, W - x0 - 20)
        grupos = []
        if d.get("cumple") or d.get("anio"):
            grupos.append(("CUMPLE", [("🎂 " + texto_cumple_seiyuu(d.get("cumple"),
                                                                     d.get("anio")), None, None)]))
        enlaces = ([normalizar_vndb(d["vndb"])] if d.get("vndb") else []) + list(d.get("redes") or ())
        if enlaces:
            grupos.append(("REDES", [red_social_item(r) for r in enlaces]))
        filas, y = [], 68.0
        for etiqueta, items in grupos:
            x, y0, chips = x0 + et_w, y, []
            for texto, enlace, tipo in items:
                w = min(fm.horizontalAdvance(texto) + (24.0 + 26.0 if tipo else 24.0),
                        ancho - et_w)
                if x + w > x0 + ancho and x > x0 + et_w:
                    x = x0 + et_w
                    y += 30
                chips.append((QRectF(x, y, w, 24), texto, enlace, tipo))
                x += w + 6
            filas.append((etiqueta, y0, chips))
            y += 32
        cab = max(self.CAB_MIN, int(y + 10)) if filas else self.CAB_MIN
        res = (filas, cab, x0)
        self._geo = (clave, res)
        return res

    def _cols(self, W):
        return max(1, int((W - 40 + self.G) // (290 + self.G)))

    def _alto(self, W):
        filas = ceil(len(self.d["heroinas"]) / self._cols(W))
        return int(self._cabecera(W)[1] + filas * (self.CH + self.G) + 10)

    def _chip(self, i):
        W = self.width()
        c = self._cols(W)
        cw = (W - 40 - self.G * (c - 1)) / c
        return QRectF(20 + (i % c) * (cw + self.G),
                      self._cabecera(W)[1] + (i // c) * (self.CH + self.G), cw, self.CH)

    @staticmethod
    def _foto():
        return QRectF(20, 20, 124, 124)

    def _boton_datos(self):
        return QRectF(self.width() - 20 - 92, 22, 92, 30)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        h = self._alto(self.width())
        if self.height() != h:
            self.setFixedHeight(h)

    def _en_chip(self, pos):
        for i in range(len(self.d["heroinas"])):
            if self._chip(i).contains(pos):
                return i
        return -1

    def _red_en(self, pos):
        for _et, _y, chips in self._cabecera(self.width())[0]:
            for rect, texto, enlace, _tipo in chips:
                if enlace and rect.contains(pos):
                    return enlace
        return None

    def mouseMoveEvent(self, e):
        pos = e.position()
        i = self._en_chip(pos)
        red = self._red_en(pos)
        edit = self._boton_datos().contains(pos)
        if self.toolTip() != (red or ""):
            self.setToolTip(red or "")
        activo = i >= 0 or edit or red or self._foto().contains(pos)
        self.setCursor(Qt.CursorShape.PointingHandCursor if activo
                       else Qt.CursorShape.ArrowCursor)
        if (i, red, edit) != (self._hover, self._hover_red, self._hover_edit):
            self._hover, self._hover_red, self._hover_edit = i, red, edit
            self.update()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        if self._hover != -1 or self._hover_red or self._hover_edit:
            self._hover, self._hover_red, self._hover_edit = -1, None, False
            self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            pos = e.position()
            if self._boton_datos().contains(pos):
                self.editar.emit(self.d["clave"])
                return
            red = self._red_en(pos)
            if red:
                from PySide6.QtGui import QDesktopServices
                QDesktopServices.openUrl(QUrl(red))
                return
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        i = self._en_chip(e.position())
        if i >= 0:
            self.abrir.emit(self.d["heroinas"][i]["id"])
        elif self._foto().contains(e.position()):
            self.cambiar_foto.emit(self.d["clave"])

    def contextMenuEvent(self, e):
        if e.pos().y() < self._cabecera(self.width())[1]:
            self.menu.emit(self.d["clave"], e.globalPos())

    def paintEvent(self, e):
        self._preparar()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        rosa = QColor(ROSA_H)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        filas_cab, cab, x0 = self._cabecera(self.width())
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio + 4, Tema.radio + 4)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, mezclar(card, a2, 0.16))
        g.setColorAt(1, mezclar(card, a1, 0.05))
        p.fillPath(camino, QBrush(g))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(mezclar(borde, a2, 0.5), 1.6))
        p.drawPath(camino)

        fr = self._foto()                                       # foto de la seiyuu
        halo = QRadialGradient(fr.center(), 90)
        halo.setColorAt(0, con_alfa(a2, 90))
        halo.setColorAt(1, con_alfa(a2, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(fr.center(), 90, 90)
        if self.av is not None:
            p.drawPixmap(fr, self.av, QRectF(self.av.rect()))
        else:
            gp = QLinearGradient(fr.topLeft(), fr.bottomRight())
            gp.setColorAt(0, a2)
            gp.setColorAt(1, a1)
            p.setBrush(QBrush(gp))
            p.drawEllipse(fr)
            p.setFont(fnt(px=50))
            p.setPen(QColor(255, 255, 255, 235))
            p.drawText(fr, int(Qt.AlignmentFlag.AlignCenter), "🎙")
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a2, 4))
        p.drawEllipse(fr.adjusted(-2, -2, 2, 2))

        hs = self.d["heroinas"]
        x = fr.right() + 22
        # botón «Datos» (arriba a la derecha) y, a su izquierda, la corona de «más versátil»
        br = self._boton_datos()
        p.setPen(QPen(a1 if self._hover_edit else borde, 1.6 if self._hover_edit else 1.2))
        p.setBrush(mezclar(card, a1, 0.22 if self._hover_edit else 0.08))
        p.drawRoundedRect(br, 15, 15)
        p.setFont(fnt(px=13, bold=True))
        p.setPen(_legible(a1))
        p.drawText(br, int(Qt.AlignmentFlag.AlignCenter), "✎ Datos")
        limite = br.left() - 12
        if self.d.get("corona"):
            lab = "MÁS VERSÁTIL"
            fp = fnt(px=12, bold=True, esp=1.2)
            pw = QFontMetrics(fp).horizontalAdvance(lab) + 26
            pr = QRectF(br.left() - 12 - pw, 24, pw, 26)
            p.setPen(QPen(QColor(ORO), 1.3))
            p.setBrush(QColor(255, 213, 74, 60))
            p.drawRoundedRect(pr, 13, 13)
            p.setFont(fp)
            p.setPen(_legible(QColor("#d99a00")))
            p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter), lab)
            limite = pr.left() - 12
        texto_el(p, x, 20, max(60.0, limite - x), 40, self.d["nombre"],
                 fnt(Tema.tam + 8, bold=True), txt)

        if not filas_cab:
            texto_el(p, x, 68, r.right() - x - 20, 24,
                     "Sin datos aún · pulsa «✎ Datos» para añadir cumpleaños, VNDB y redes",
                     fnt(max(8.5, Tema.tam - 1)), mu)
        fc = fnt(max(8.5, Tema.tam - 1), bold=True)
        for etiqueta, y0, chips in filas_cab:
            texto_el(p, x0, y0, 70, 24, etiqueta, fnt(px=11, bold=True, esp=1.4), mu)
            for rect, texto, enlace, tipo in chips:
                hov = bool(enlace) and enlace == self._hover_red
                color = a1 if enlace else (rosa if etiqueta == "CUMPLE" else a2)
                p.setPen(QPen(con_alfa(color, 230 if hov else 150), 1.2))
                p.setBrush(mezclar(card, color, 0.30 if hov else 0.14))
                p.drawRoundedRect(rect, 12, 12)
                if tipo:                                  # icono de marca + @usuario
                    dibujar_icono_red(p, QRectF(rect.x() + 3, rect.y() + 2, 20, 20), tipo)
                    texto_el(p, rect.x() + 30, rect.y(), rect.width() - 38, rect.height(),
                             texto, fc, txt)
                else:
                    texto_el(p, rect.x() + 11, rect.y(), rect.width() - 22, rect.height(),
                             texto, fc, txt)

        p.setPen(QPen(con_alfa(borde, 200), 1))
        p.drawLine(QPointF(20, cab - 14), QPointF(r.right() - 20, cab - 14))
        for i, h in enumerate(hs):
            cr = self._chip(i)
            eroge = bool(h.get("eroge"))
            cam = QPainterPath()
            cam.addRoundedRect(cr, 16, 16)
            hover = i == self._hover
            if eroge:                                           # recuadro rosado + «H»
                gr = QLinearGradient(cr.topLeft(), cr.topRight())
                gr.setColorAt(0, mezclar(card, rosa, 0.34 if hover else 0.24))
                gr.setColorAt(1, mezclar(card, rosa, 0.14 if hover else 0.08))
                p.fillPath(cam, QBrush(gr))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(rosa, 2.6 if hover else 1.9))
            else:
                p.fillPath(cam, QBrush(mezclar(card, a1, 0.18 if hover else 0.07)))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(a1 if hover else borde, 2 if hover else 1.2))
            p.drawPath(cam)
            ar = 27.0
            pm = self.avs[i] if i < len(self.avs) else None
            ac = QPointF(cr.left() + 12 + ar, cr.center().y())
            if pm is not None:
                p.drawPixmap(QRectF(ac.x() - ar, ac.y() - ar, ar * 2, ar * 2), pm,
                             QRectF(pm.rect()))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(rosa if eroge else a1, 2.5))
            p.drawEllipse(ac, ar, ar)
            tx = ac.x() + ar + 14
            tw = cr.right() - tx - (56 if eroge else 14)
            texto_el(p, tx, cr.center().y() - 25, tw, 26, h["nombre"],
                     fnt(Tema.tam + 1, bold=True), txt)
            texto_el(p, tx, cr.center().y() + 2, tw, 22, "📖 " + h["juego"],
                     fnt(max(8.5, Tema.tam - 1)), mu)
            if eroge:
                bc = QPointF(cr.right() - 28, cr.center().y())
                halo_h = QRadialGradient(bc, 26)
                halo_h.setColorAt(0, con_alfa(rosa, 120))
                halo_h.setColorAt(1, con_alfa(rosa, 0))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(halo_h))
                p.drawEllipse(bc, 26, 26)
                gb = QLinearGradient(bc.x(), bc.y() - 16, bc.x(), bc.y() + 16)
                gb.setColorAt(0, QColor("#ff9cc9"))
                gb.setColorAt(1, QColor("#ff3d8b"))
                p.setBrush(QBrush(gb))
                p.setPen(QPen(QColor(255, 255, 255, 235), 2))
                p.drawEllipse(bc, 16, 16)
                p.setFont(fnt(px=18, bold=True))
                p.setPen(QColor(255, 255, 255))
                p.drawText(QRectF(bc.x() - 16, bc.y() - 16, 32, 32),
                           int(Qt.AlignmentFlag.AlignCenter), "H")
        p.end()


class ContenedorFilas(QScrollArea):
    """Columna con scroll para apilar tarjetas; muestra un mensaje si está vacía."""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.cuerpo = QWidget()
        self.lay = QVBoxLayout(self.cuerpo)
        self.lay.setContentsMargins(0, 0, 8, 0)
        self.lay.setSpacing(10)
        self.lay.addStretch()
        self.setWidget(self.cuerpo)
        self.viewport().setAutoFillBackground(False)
        self.cuerpo.setAutoFillBackground(False)

    def _vaciar(self):
        while self.lay.count() > 1:
            w = self.lay.takeAt(0).widget()
            if w is not None:
                w.hide()
                w.deleteLater()

    def poner_por_partes(self, fabricas, vacio="", tam=4):
        """Como poner(), pero recibe funciones que CREAN cada tarjeta y las va creando de a
        pocas: la pantalla se abre al instante en vez de congelarse con cientos de tarjetas."""
        self._gen = getattr(self, "_gen", 0) + 1
        gen = self._gen
        self._vaciar()
        if not fabricas:
            self.poner([], vacio)
            return
        pendientes = list(fabricas)[::-1]

        def paso():
            if gen != self._gen:                    # llegó una carga más nueva: esta se cancela
                return
            try:
                self.cuerpo.setUpdatesEnabled(False)
                for _ in range(tam):
                    if not pendientes:
                        break
                    try:
                        w = pendientes.pop()()
                    except Exception:
                        registrar_error_ui("ContenedorFilas.poner_por_partes")
                        continue
                    self.lay.insertWidget(self.lay.count() - 1, w)
                self.cuerpo.setUpdatesEnabled(True)
            except RuntimeError:                    # la pantalla ya no existe
                return
            if pendientes:
                QTimer.singleShot(1, paso)
        paso()

    def poner(self, widgets, vacio=""):
        self._gen = getattr(self, "_gen", 0) + 1    # cancela cualquier carga por partes pendiente
        self._vaciar()
        if not widgets:
            msg = QLabel(vacio)
            msg.setObjectName("muted")
            msg.setWordWrap(True)
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            widgets = [msg]
        for w in widgets:
            self.lay.insertWidget(self.lay.count() - 1, w)


# =========================================================
# INFO HEROÍNAS: widgets propios de las pestañas Cumpleaños y Seiyuus
# =========================================================

FRASES_CUMPLE = (
    "Que todos sus finales sean felices ✨",
    "Hoy toca pastel, velitas y mucho cariño 🍰",
    "Un día para consentirla como se merece 💖",
    "Pide un deseo… seguro se cumple 🌠",
    "La protagonista de su propia historia 📖",
    "Hoy brilla más que cualquier CG ✦",
    "Un año más de ser inolvidable 🌸",
    "¡Que no falten los pétalos ni los abrazos! 🌷",
)
ORO = "#ffd54a"


class ContenedorCuadricula(QScrollArea):
    """Tarjetas en columnas que se adaptan al ancho de la ventana (1, 2, 3…), con carga por
    partes: la pantalla se abre al instante y las tarjetas van entrando de a pocas."""

    def __init__(self, ancho_min=440, sep=12):
        super().__init__()
        self.ancho_min, self.sep = ancho_min, sep
        self.items, self.cols, self._gen, self._msg = [], 1, 0, None
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.cuerpo = QWidget()
        ext = QVBoxLayout(self.cuerpo)
        ext.setContentsMargins(0, 0, 8, 0)
        self.grid = QGridLayout()
        self.grid.setSpacing(sep)
        ext.addLayout(self.grid)
        ext.addStretch(1)
        self.setWidget(self.cuerpo)
        self.viewport().setAutoFillBackground(False)
        self.cuerpo.setAutoFillBackground(False)

    def _columnas(self):
        ancho = self.width() - self.verticalScrollBar().sizeHint().width() - 16
        return max(1, int((ancho + self.sep) // (self.ancho_min + self.sep)))

    def _vaciar(self):
        for w in self.items:
            self.grid.removeWidget(w)
            w.hide()
            w.deleteLater()
        self.items = []
        if self._msg is not None:
            self.grid.removeWidget(self._msg)
            self._msg.hide()
            self._msg.deleteLater()
            self._msg = None

    def _estirar(self):
        for c in range(max(self.cols, self.grid.columnCount())):
            self.grid.setColumnStretch(c, 1 if c < self.cols else 0)

    def _colocar(self, w, i):
        self.grid.addWidget(w, i // self.cols, i % self.cols, Qt.AlignmentFlag.AlignTop)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        cols = self._columnas()
        if cols == self.cols:
            return
        self.cols = cols
        for w in self.items:
            self.grid.removeWidget(w)
        for i, w in enumerate(self.items):
            self._colocar(w, i)
        self._estirar()

    def poner_por_partes(self, fabricas, vacio="", tam=4):
        self._gen += 1
        gen = self._gen
        self._vaciar()
        self.cols = self._columnas()
        self._estirar()
        if not fabricas:
            m = QLabel(vacio)
            m.setObjectName("muted")
            m.setWordWrap(True)
            m.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._msg = m
            self.grid.addWidget(m, 0, 0, 1, self.cols)
            return
        pendientes = list(fabricas)[::-1]

        def paso():
            if gen != self._gen:                    # llegó una carga más nueva: esta se cancela
                return
            try:
                self.cuerpo.setUpdatesEnabled(False)
                for _ in range(tam):
                    if not pendientes:
                        break
                    try:
                        w = pendientes.pop()()
                    except Exception:
                        registrar_error_ui("ContenedorCuadricula.poner_por_partes")
                        continue
                    self._colocar(w, len(self.items))
                    self.items.append(w)
                self.cuerpo.setUpdatesEnabled(True)
            except RuntimeError:                    # la pantalla ya no existe
                return
            if pendientes:
                QTimer.singleShot(1, paso)
        paso()


class TarjetaCumple(QWidget):
    """Tarjeta grande de cumpleaños: foto redonda, nombre, novela, fecha con signo y etiqueta
    de cuánto falta. La de HOY va dorada."""
    clic = Signal()
    ALTO = 128

    def __init__(self, pm, g, pill, extra=""):
        super().__init__()
        self.pm, self.g, self.pill, self.extra = pm, g, pill, extra
        self.hoy = g["dias"] == 0
        self._hover = False
        self.setFixedHeight(self.ALTO)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def mouseDoubleClickEvent(self, e):
        self.clic.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        oro = QColor(ORO)
        g = self.g
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio + 2, Tema.radio + 2)
        base = mezclar(card, oro, 0.26) if self.hoy else mezclar(
            card, a1, 0.16 if self._hover else 0.06)
        gr = QLinearGradient(r.topLeft(), r.topRight())
        gr.setColorAt(0, base)
        gr.setColorAt(1, mezclar(base, a2, 0.14))
        p.fillPath(camino, QBrush(gr))
        resalta = self.hoy or self._hover
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(oro if self.hoy else (a1 if self._hover else borde),
                      2.4 if resalta else 1.2))
        p.drawPath(camino)

        cy, ar = r.center().y(), 48.0
        ax = r.left() + 18
        if self.pm is not None and not self.pm.isNull():
            p.drawPixmap(QRectF(ax, cy - ar, ar * 2, ar * 2), self.pm, QRectF(self.pm.rect()))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(oro if self.hoy else a1, 3))
        p.drawEllipse(QPointF(ax + ar, cy), ar, ar)
        dibujar_medalla(p, QPointF(ax + 9, cy - ar + 9), 14, g["rank"], False)

        x = ax + ar * 2 + 18
        fp = fnt(px=13, bold=True)
        pw = QFontMetrics(fp).horizontalAdvance(self.pill) + 26
        pr = QRectF(r.right() - 16 - pw, r.top() + 14, pw, 28)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(con_alfa(oro if self.hoy else a1, 90 if self.hoy else 56))
        p.drawRoundedRect(pr, 14, 14)
        p.setFont(fp)
        p.setPen(_legible(QColor("#d99a00") if self.hoy else a1))
        p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter), self.pill)

        w = r.right() - x - 16
        texto_el(p, x, r.top() + 12, w - pw - 10, 32, g["nombre"],
                 fnt(Tema.tam + 5, bold=True), txt)
        texto_el(p, x, r.top() + 46, w, 22, "📖 " + " · ".join(g["novelas"]),
                 fnt(Tema.tam - 0.5), _legible(a1))
        fecha = "🎂 " + g["cumple"] + (f"  ·  {g['zodiaco']}" if g["zodiaco"] else "")
        texto_el(p, x, r.top() + 70, w, 24, fecha, fnt(Tema.tam + 1, bold=True), txt)
        if self.extra:
            texto_el(p, x, r.top() + 96, w, 20, self.extra,
                     fnt(max(8.5, Tema.tam - 1.5)), mu)
        p.end()


class BarraChips(QWidget):
    """Fila de «pastillas» con datos curiosos. Se pinta sola: cero widgets por dato."""

    def __init__(self):
        super().__init__()
        self.chips = []
        self.setFixedHeight(40)

    def poner(self, chips):
        self.chips = [c for c in chips if c]
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        txt = QColor(Tema.c("text"))
        f = fnt(px=13, bold=True)
        fm = QFontMetrics(f)
        x = 2.0
        for i, t in enumerate(self.chips):
            w = fm.horizontalAdvance(t) + 28
            if x + w > self.width():
                break
            col = a1 if i % 2 == 0 else a2
            r = QRectF(x, 5, w, 30)
            p.setPen(QPen(con_alfa(col, 150), 1.2))
            p.setBrush(con_alfa(col, 44))
            p.drawRoundedRect(r, 15, 15)
            p.setFont(f)
            p.setPen(txt)
            p.drawText(r, int(Qt.AlignmentFlag.AlignCenter), t)
            x += w + 8
        p.end()


class BannerCumple(QWidget):
    """Tarjeta grande de arriba. Normalmente: el próximo cumpleaños con cuenta atrás. Si HOY es
    el día de una heroína se convierte en una fiesta: corona, confeti, un regalo (una de sus
    capturas favoritas) y un botón para celebrar con una lluvia de confeti."""
    abrir = Signal(int)

    def __init__(self):
        super().__init__()
        self.items, self.idx = [], 0
        self._t = 0.0
        self._celebrando = False
        self._reloj = QTimer(self)
        self._reloj.setInterval(33)
        self._reloj.timeout.connect(self._tic)
        rnd = random.Random(11)
        self._conf = [(rnd.random(), rnd.random(), rnd.uniform(6, 11), rnd.uniform(0, 360),
                       rnd.randrange(6), rnd.uniform(0.25, 0.9), rnd.uniform(0, 6.28))
                      for _ in range(64)]
        self.setFixedHeight(176)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def poner(self, items):
        self.items, self.idx = items, 0
        self._celebrando = False
        self._reloj.stop()
        self._t = 0.0
        self.update()

    def actual(self):
        return self.items[self.idx] if self.items else None

    def hoy(self):
        a = self.actual()
        return bool(a and a["dias"] == 0)

    def siguiente(self):
        if self.items:
            self.idx = (self.idx + 1) % len(self.items)
            self.update()

    def celebrar(self):
        self._celebrando = True
        self._t = 0.0
        self._reloj.start()

    def _tic(self):
        self._t += 0.033
        if self._t > 3.4:
            self._celebrando = False
            self._reloj.stop()
            self._t = 0.0
        self.update()

    def mouseDoubleClickEvent(self, e):
        a = self.actual()
        if a:
            self.abrir.emit(a["id"])

    def _confeti(self, p, r, alfa, animado):
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        paleta = (a1, a2, QColor(ORO), QColor("#7fe0bb"), QColor("#8fd0ff"), QColor("#ff9ec7"))
        p.save()
        p.setClipRect(r)
        p.setPen(Qt.PenStyle.NoPen)
        for xf, yf, tam, ang, ci, vel, fase in self._conf:
            if animado:
                y = r.top() + ((yf + self._t * vel) % 1.15 - 0.08) * r.height()
                x = r.left() + xf * r.width() + sin(self._t * 3 + fase) * 14
                giro = ang + self._t * 200 * vel
            else:
                y = r.top() + yf * r.height() * 0.9
                x = r.left() + xf * r.width()
                giro = ang
            c = QColor(paleta[ci])
            c.setAlpha(alfa)
            p.setBrush(c)
            p.save()
            p.translate(x, y)
            p.rotate(giro)
            p.drawRoundedRect(QRectF(-tam / 2, -tam / 4, tam, tam / 2), 1.5, 1.5)
            p.restore()
        p.restore()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        oro = QColor(ORO)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio + 4, Tema.radio + 4)
        d = self.actual()
        if d is None:
            p.fillPath(camino, QBrush(mezclar(card, a1, 0.10)))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(borde, 1.4))
            p.drawPath(camino)
            p.setFont(fnt(Tema.tam + 1))
            p.setPen(mu)
            p.drawText(r, int(Qt.AlignmentFlag.AlignCenter),
                       "Aún no hay cumpleaños.\nAñádelos con «✎ Editar información» en la galería "
                       "de cada heroína (día y mes).")
            p.end()
            return
        hoy = d["dias"] == 0
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, mezclar(card, oro if hoy else a1, 0.30 if hoy else 0.22))
        g.setColorAt(1, mezclar(card, a2, 0.14))
        p.fillPath(camino, QBrush(g))
        p.save()
        p.setClipPath(camino)
        p.setFont(fnt(px=190, bold=True))
        p.setPen(con_alfa(oro if hoy else a1, 24))
        p.drawText(QRectF(r.center().x() - 60, r.top() - 40, 300, r.height() + 80),
                   int(Qt.AlignmentFlag.AlignCenter), "✦")
        p.restore()
        if hoy or self._celebrando:
            self._confeti(p, r, 230 if self._celebrando else 120, self._celebrando)
            dibujar_destello(p, r.left() + 20, r.top() + 26, 8, oro)
            dibujar_destello(p, r.center().x() + 40, r.bottom() - 26, 6, a1)
            dibujar_destello(p, r.right() - 28, r.top() + 30, 9, oro)

        lado = 124.0
        ring = lado / 2 + 9
        c = QPointF(r.left() + 34 + ring, r.center().y())
        if hoy:
            halo = QRadialGradient(c, ring + 26)
            halo.setColorAt(0, con_alfa(oro, 130))
            halo.setColorAt(1, con_alfa(oro, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(halo))
            p.drawEllipse(c, ring + 26, ring + 26)
        else:                                  # anillo que se llena según se acerca su día
            frac = max(0.0, min(1.0, 1 - d["dias"] / 365.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(con_alfa(borde, 220), 6))
            p.drawEllipse(c, ring, ring)
            lapiz = QPen(a1, 6)
            lapiz.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(lapiz)
            p.drawArc(QRectF(c.x() - ring, c.y() - ring, ring * 2, ring * 2),
                      90 * 16, -int(frac * 360 * 16))
        pm = d["pm"]
        if pm is not None and not pm.isNull():
            p.drawPixmap(QRectF(c.x() - lado / 2, c.y() - lado / 2, lado, lado), pm,
                         QRectF(pm.rect()))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(oro if hoy else a1, 3.5))
        p.drawEllipse(c, lado / 2 + 1, lado / 2 + 1)
        if hoy:
            p.setFont(fnt(px=40))
            p.setPen(txt)
            p.drawText(QRectF(c.x() - 28, c.y() - lado / 2 - 20, 56, 44),
                       int(Qt.AlignmentFlag.AlignCenter), "👑")

        x = c.x() + ring + 26
        w = r.right() - x - 206
        mas = f"   ·   {self.idx + 1} de {len(self.items)}" if len(self.items) > 1 else ""
        texto_el(p, x, r.top() + 20, w, 18,
                 ("🎉  ¡HOY ES SU CUMPLEAÑOS!" if hoy else "PRÓXIMO CUMPLEAÑOS") + mas,
                 fnt(px=12, bold=True, esp=2.0), _legible(oro if hoy else a1))
        texto_el(p, x, r.top() + 40, w, 40, d["nombre"], fnt(Tema.tam + 11, bold=True), txt)
        fecha = "🎂 " + d["cumple"] + (f"  ·  {d['zodiaco']}" if d["zodiaco"] else "")
        texto_el(p, x, r.top() + 84, w, 22, fecha, fnt(Tema.tam + 1, bold=True), _legible(a1))
        chico = fnt(max(8.5, Tema.tam - 1))
        texto_el(p, x, r.top() + 110, w, 20, d["frase"] if hoy else "📖 " + d["novelas"],
                 chico, mu)
        extra = []
        if d.get("seiyuu"):
            extra.append("🎙 " + d["seiyuu"])
        if d.get("caps"):
            extra.append(f"🖼 {d['caps']} capturas · ★ {d['favs']}")
        if extra:
            texto_el(p, x, r.top() + 133, w, 20, "   ·   ".join(extra), chico, mu)

        xr = r.right() - 192
        if not hoy:
            n = d["dias"]
            p.setFont(fnt(px=64 if n != 1 else 40, bold=True))
            p.setPen(_legible(a1))
            p.drawText(QRectF(xr, r.top() + 30, 170, 80), int(Qt.AlignmentFlag.AlignCenter),
                       "mañana" if n == 1 else str(n))
            if n != 1:
                texto_el(p, xr, r.top() + 112, 170, 20, "días para su cumple",
                         fnt(Tema.tam, bold=True), mu, Qt.AlignmentFlag.AlignHCenter)
            if n <= 7:
                pr = QRectF(xr + 25, r.top() + 140, 120, 24)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(con_alfa(a1, 60))
                p.drawRoundedRect(pr, 12, 12)
                p.setFont(fnt(px=12, bold=True))
                p.setPen(_legible(a1))
                p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter), "¡esta semana!")
        else:                                  # su regalo: una de sus capturas favoritas
            p.save()
            p.translate(xr + 85, r.top() + 88)
            p.rotate(-4)
            rl = QRectF(-72, -54, 144, 108)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 50))
            p.drawRoundedRect(rl.translated(3, 5), 14, 14)
            reg = d.get("regalo")
            if reg is not None and not reg.isNull():
                dibujar_cover(p, rl, reg, 14)
            else:
                gg = QLinearGradient(rl.topLeft(), rl.bottomRight())
                gg.setColorAt(0, oro)
                gg.setColorAt(1, a1)
                p.setBrush(QBrush(gg))
                p.drawRoundedRect(rl, 14, 14)
                p.setFont(fnt(px=52))
                p.setPen(txt)
                p.drawText(rl, int(Qt.AlignmentFlag.AlignCenter), "🎁")
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(con_alfa(a1, 150))
            p.drawRect(QRectF(-7, rl.top(), 14, rl.height()))
            p.drawRect(QRectF(rl.left(), -7, rl.width(), 14))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(oro, 3))
            p.drawRoundedRect(rl, 14, 14)
            p.setFont(fnt(px=30))
            p.setPen(txt)
            p.drawText(QRectF(-20, rl.top() - 22, 40, 36), int(Qt.AlignmentFlag.AlignCenter), "🎀")
            p.restore()
            texto_el(p, xr, r.top() + 150, 170, 20, "🎁 Su regalo de hoy",
                     fnt(px=12, bold=True), _legible(a1), Qt.AlignmentFlag.AlignHCenter)

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(oro if hoy else mezclar(borde, a1, 0.5), 1.8 if hoy else 1.4))
        p.drawPath(camino)
        p.end()


class BarraProgreso(QWidget):
    """Barra fina que se llena hasta la siguiente captura (modo presentación)."""

    def __init__(self):
        super().__init__()
        self.valor = 0.0
        self.setFixedHeight(6)

    def poner(self, v):
        self.valor = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(Tema.c("border")))
        p.drawRoundedRect(r, 3, 3)
        if self.valor > 0:
            g = QLinearGradient(r.topLeft(), r.topRight())
            g.setColorAt(0, QColor(Tema.a1()))
            g.setColorAt(1, QColor(Tema.a2()))
            p.setBrush(QBrush(g))
            p.drawRoundedRect(QRectF(r.left(), r.top(), r.width() * self.valor, r.height()), 3, 3)


class PopFavorito(QWidget):
    """Estrella que «salta» sobre la imagen al marcar/desmarcar un favorito."""

    def __init__(self, vista):
        super().__init__(vista)
        self.vista = vista
        self.t = 0.0
        self.marcado = True
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(800)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._set)
        self.anim.finished.connect(self.hide)
        self.hide()

    def _set(self, v):
        self.t = float(v)
        self.update()

    def disparar(self, marcado):
        self.marcado = marcado
        self.setGeometry(self.vista.rect())
        self.show()
        self.raise_()
        self.anim.stop()
        self.anim.start()

    def paintEvent(self, e):
        t = self.t
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QPointF(self.width() / 2, self.height() / 2)
        alfa = 1.0 if t < 0.55 else max(0.0, 1 - (t - 0.55) / 0.45)
        salto = 1 - (1 - min(1.0, t * 2.2)) ** 3
        esc = 0.35 + 0.85 * salto
        col = QColor(Tema.a1()) if self.marcado else QColor(190, 190, 205)
        if self.marcado:
            for i in range(10):                      # chispas que salen disparadas
                ang = i * 2 * pi / 10
                d = 50 + 110 * salto
                q = QColor(Tema.a1() if i % 2 else Tema.a2())
                q.setAlphaF(alfa * 0.9)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(q)
                rad = 7 * (1 - t) + 2
                p.drawEllipse(QPointF(c.x() + cos(ang) * d, c.y() + sin(ang) * d), rad, rad)
        halo = QColor(col)
        halo.setAlphaF(alfa * 0.25)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(halo)
        p.drawEllipse(c, 80 * esc, 80 * esc)
        f = QFont(Tema.fuente)
        f.setPixelSize(max(10, int(120 * esc)))
        p.setFont(f)
        col.setAlphaF(alfa)
        p.setPen(col)
        p.drawText(QRectF(c.x() - 120, c.y() - 120, 240, 240),
                   int(Qt.AlignmentFlag.AlignCenter), "★" if self.marcado else "☆")


try:                                  # opcional: lee la duración al instante (pip install mutagen)
    import mutagen
except ImportError:
    mutagen = None


def fmt_dur(ms):
    if not ms or ms <= 0:
        return "--:--"
    s = int(ms // 1000)
    h, m, s = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def fmt_peso(b):
    if not b or b <= 0:
        return "—"
    for unidad in ("B", "KB", "MB", "GB"):
        if b < 1024 or unidad == "GB":
            return f"{b:.0f} {unidad}" if unidad == "B" else f"{b:.1f} {unidad}"
        b /= 1024


def duracion_mutagen(ruta):
    if mutagen is None:
        return 0
    try:
        f = mutagen.File(ruta)
        if f is not None and f.info is not None:
            return int(f.info.length * 1000)
    except Exception:
        pass
    return 0


_BR_MPEG1 = (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0)
_BR_MPEG2 = (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0)
_SR_MPEG = {3: (44100, 48000, 32000), 2: (22050, 24000, 16000), 0: (11025, 12000, 8000)}


def duracion_mp3(ruta):
    """Duración de un MP3 leyendo sus cabeceras (sin librerías ni reproductor)."""
    try:
        tam = os.path.getsize(ruta)
        with open(ruta, "rb") as f:
            cab = f.read(10)
            ini = 0
            if cab[:3] == b"ID3" and len(cab) == 10:
                ini = 10 + (((cab[6] & 0x7F) << 21) | ((cab[7] & 0x7F) << 14)
                            | ((cab[8] & 0x7F) << 7) | (cab[9] & 0x7F))
            f.seek(ini)
            buf = f.read(131072)
        i, n = 0, len(buf)
        while i + 4 <= n:
            if buf[i] == 0xFF and (buf[i + 1] & 0xE0) == 0xE0:
                ver, capa = (buf[i + 1] >> 3) & 3, (buf[i + 1] >> 1) & 3
                bi, si = (buf[i + 2] >> 4) & 15, (buf[i + 2] >> 2) & 3
                if ver != 1 and capa == 1 and bi not in (0, 15) and si != 3:
                    break
            i += 1
        else:
            return 0
        mpeg1 = ver == 3
        br = (_BR_MPEG1 if mpeg1 else _BR_MPEG2)[bi] * 1000
        sr = _SR_MPEG[ver][si]
        muestras = 1152 if mpeg1 else 576
        mono = (buf[i + 3] >> 6) == 3
        x = i + 4 + ((17 if mono else 32) if mpeg1 else (9 if mono else 17))
        if (buf[i + 1] & 1) == 0:
            x += 2
        if buf[x:x + 4] in (b"Xing", b"Info"):
            if int.from_bytes(buf[x + 4:x + 8], "big") & 1:
                frames = int.from_bytes(buf[x + 8:x + 12], "big")
                if frames > 0:
                    return int(frames * muestras / sr * 1000)
        if buf[i + 36:i + 40] == b"VBRI":
            frames = int.from_bytes(buf[i + 50:i + 54], "big")
            if frames > 0:
                return int(frames * muestras / sr * 1000)
        datos = tam - ini - i
        return int(datos * 8 / br * 1000) if br and datos > 0 else 0
    except Exception:
        return 0


def duracion_wav(ruta):
    try:
        import wave
        with wave.open(str(ruta), "rb") as w:
            return int(w.getnframes() / w.getframerate() * 1000)
    except Exception:
        return 0


def duracion_rapida(ruta):
    """mutagen si está instalado; si no, lector propio de MP3/WAV. 0 si no se sabe."""
    d = duracion_mutagen(ruta)
    if d > 0:
        return d
    ext = Path(ruta).suffix.lower()
    if ext == ".mp3":
        return duracion_mp3(ruta)
    if ext == ".wav":
        return duracion_wav(ruta)
    return 0


class SondaDuracion(QObject):
    """Último recurso (ogg/flac/m4a sin mutagen): averigua la duración con Qt, de una en una.
    El reproductor se crea solo si hace falta y los cambios de pista se difieren al siguiente
    ciclo de eventos para no reentrar dentro de las señales de QMediaPlayer."""
    lista = Signal(int, int)          # id de pista, duración en ms

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cola = []
        self.actual = None
        self.player = None
        self.limite = QTimer(self)
        self.limite.setSingleShot(True)
        self.limite.timeout.connect(self._siguiente_diferido)

    def _asegurar_player(self):
        if self.player is None:
            self.player = QMediaPlayer(self)
            self.player.durationChanged.connect(self._dur)
            self.player.errorOccurred.connect(lambda *a: self._siguiente_diferido())

    def pedir(self, mid, ruta):
        if self.actual and self.actual[0] == mid or any(c[0] == mid for c in self.cola):
            return
        self.cola.append((mid, ruta))
        if self.actual is None:
            self._siguiente_diferido()

    def _siguiente_diferido(self):
        QTimer.singleShot(0, self._siguiente)

    def _siguiente(self):
        self.limite.stop()
        if not self.cola:
            self.actual = None
            if self.player is not None:
                self.player.stop()
            return
        self.actual = self.cola.pop(0)
        try:
            self._asegurar_player()
            self.player.setSource(QUrl.fromLocalFile(self.actual[1]))
            self.limite.start(4000)
        except Exception:
            self._siguiente_diferido()

    def _dur(self, ms):
        if ms > 0 and self.actual:
            self.lista.emit(self.actual[0], int(ms))
            self.actual = None
            self._siguiente_diferido()


def columnas_pista(ancho):
    """Posición de las columnas de la lista de pistas (la comparten cabecera y filas)."""
    x_kbps = ancho - 96
    x_peso = x_kbps - 86
    x_dur = x_peso - 78
    x_fmt = x_dur - 74
    return dict(num=(16, 34), titulo=(58, max(60, x_fmt - 70)),
                fmt=(x_fmt, 62), dur=(x_dur, 66), peso=(x_peso, 76), kbps=(x_kbps, 84))


class CabeceraPistas(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(28)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        f = QFont(p.font())
        f.setPointSizeF(max(8, Tema.tam - 1.5))
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(Tema.c("muted")))
        c = columnas_pista(self.width())
        nombres = dict(num="#", titulo="TÍTULO", fmt="FORMATO", dur="DURACIÓN",
                       peso="PESO", kbps="BITRATE")
        for clave, (x, w) in c.items():
            alin = (Qt.AlignmentFlag.AlignLeft if clave in ("num", "titulo")
                    else Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter
            p.drawText(QRectF(x, 0, w, self.height()), int(alin), nombres[clave])
        p.setPen(QPen(QColor(Tema.c("border")), 1))
        p.drawLine(8, self.height() - 1, self.width() - 8, self.height() - 1)


class DelegadoPista(QStyledItemDelegate):
    """Fila de pista: número, título, formato, duración, peso y bitrate.
    La pista que suena se resalta y muestra un ecualizador animado."""

    def sizeHint(self, option, index):
        return QSize(100, 54)

    def paint(self, p, option, index):
        d = index.data(Qt.ItemDataRole.UserRole + 1)
        if not d:
            return
        vista = option.widget
        sel = bool(option.state & QStyle.StateFlag.State_Selected)
        hover = bool(option.state & QStyle.StateFlag.State_MouseOver)
        actual = getattr(vista, "ruta_sonando_n", "")
        es_actual = bool(actual) and actual == d.get("rn")
        sonando = es_actual and getattr(vista, "sonando", False)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card = QColor(Tema.c("card"))
        radio = Tema.radio

        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        r = QRectF(option.rect).adjusted(4, 3, -4, -3)
        camino = QPainterPath()
        camino.addRoundedRect(r, radio * 0.8, radio * 0.8)
        fondo = QLinearGradient(r.topLeft(), r.topRight())
        base = mezclar(card, a1, 0.22 if es_actual else (0.10 if hover or sel else 0.0))
        fondo.setColorAt(0, base)
        fondo.setColorAt(1, mezclar(base, a2, 0.16 if (es_actual or sel) else 0.04))
        p.fillPath(camino, QBrush(fondo))
        if sel or es_actual or hover:
            bord = QLinearGradient(r.topLeft(), r.topRight())
            bord.setColorAt(0, a1)
            bord.setColorAt(1, a2)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QBrush(bord), 2.2 if sel else 1.4))
            p.drawPath(camino)
        else:
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(Tema.c("border")), 1))
            p.drawPath(camino)

        c = columnas_pista(option.rect.width())
        ox, oy = option.rect.x(), r.top()
        alto = r.height()

        def celda(clave):
            x, w = c[clave]
            return QRectF(ox + x, oy, w, alto)

        # número / ecualizador
        rn = celda("num")
        if es_actual:
            p.setPen(Qt.PenStyle.NoPen)
            for i in range(3):
                if sonando:
                    v = 0.35 + 0.65 * abs(sin(time.monotonic() * (4.5 + i * 1.7) + i * 1.3))
                else:
                    v = 0.5
                h = max(4.0, 20 * v)
                p.setBrush(a1 if i != 1 else a2)
                p.drawRoundedRect(QRectF(rn.left() + i * 8, rn.center().y() + 10 - h, 5, h), 2, 2)
        else:
            f = QFont(p.font())
            f.setPointSizeF(max(8, Tema.tam))
            p.setFont(f)
            p.setPen(QColor(Tema.c("muted")))
            p.drawText(rn, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                       f"{d['n']:02d}")

        # título
        f = QFont(p.font())
        f.setPointSizeF(Tema.tam + 1)
        f.setBold(True)
        p.setFont(f)
        rt = celda("titulo")
        if not d["existe"]:
            p.setPen(QColor("#e57373"))
            txt = d["titulo"] + "  (archivo no encontrado)"
        else:
            p.setPen(a1 if es_actual else QColor(Tema.c("text")))
            txt = d["titulo"]
        txt = QFontMetrics(f).elidedText(txt, Qt.TextElideMode.ElideRight, int(rt.width()))
        p.drawText(rt, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), txt)

        # formato (pastilla)
        rf = celda("fmt")
        pill = QRectF(rf.left() + 4, rf.center().y() - 11, rf.width() - 8, 22)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(mezclar(card, a2, 0.35))
        p.drawRoundedRect(pill, 11, 11)
        f2 = QFont(p.font())
        f2.setPointSizeF(max(7.5, Tema.tam - 2))
        f2.setBold(True)
        p.setFont(f2)
        p.setPen(QColor(Tema.c("text")))
        p.drawText(pill, int(Qt.AlignmentFlag.AlignCenter), d["fmt"] or "—")

        # duración, peso, bitrate
        f3 = QFont(p.font())
        f3.setPointSizeF(Tema.tam)
        f3.setBold(False)
        p.setFont(f3)
        p.setPen(QColor(Tema.c("text")))
        p.drawText(celda("dur"), int(Qt.AlignmentFlag.AlignCenter), fmt_dur(d["dur"]))
        p.setPen(QColor(Tema.c("muted")))
        p.drawText(celda("peso"), int(Qt.AlignmentFlag.AlignCenter), fmt_peso(d["peso"]))
        kb = f"{int(d['peso'] * 8 / (d['dur'] / 1000) / 1000)} kbps" \
            if d["dur"] > 0 and d["peso"] > 0 else "—"
        p.drawText(celda("kbps"), int(Qt.AlignmentFlag.AlignCenter), kb)
        p.restore()


INTERVALOS_PRES = (3, 5, 8, 12, 20)


class VisorImagen(QDialog):
    """items: lista de rutas de imagen. Si la ventana padre tiene `conn` (base de datos),
    el visor puede marcar favoritos."""

    def __init__(self, items, indice=0, parent=None):
        super().__init__(parent)
        self.items, self.indice = items, indice
        self.db = getattr(parent, "conn", None)
        self.cambios = False            # ¿se tocó algún favorito? (para refrescar la galería)
        self.pres_activa = False
        self._pres_ms = 0
        self._pres_cg = False
        self._cg = False
        self._an = None
        self._ef = None
        self.setWindowTitle("NyuhuhuGallery · Visor")
        pantalla = QApplication.primaryScreen().availableGeometry()
        self.resize(int(pantalla.width() * 0.9), int(pantalla.height() * 0.9))

        lay = QVBoxLayout(self)
        self.barra_sup = QWidget()
        barra = QHBoxLayout(self.barra_sup)
        barra.setContentsMargins(0, 0, 0, 0)
        self.titulo = QLabel()
        self.titulo.setObjectName("heading")
        barra.addWidget(self.titulo, 1)
        b_aj = BotonAnimado("Ajustar")
        b_100 = BotonAnimado("100 %")
        b_menos = BotonAnimado("−")
        b_mas = BotonAnimado("+")
        self.b_fav = BotonAnimado("☆ Favorito")
        self.b_fav.setCheckable(True)
        b_copiar = BotonAnimado("📋 Copiar")
        self.b_pres = BotonAnimado("▶ Presentación")
        self.b_pres.setCheckable(True)
        self.c_int = QComboBox()
        for s in INTERVALOS_PRES:
            self.c_int.addItem(f"{s} s", s)
        self.c_int.setCurrentIndex(1)
        b_full = BotonAnimado("⛶ Pantalla completa")
        self.lbl_zoom = QLabel("100 %")
        for b in (b_aj, b_100, b_menos):
            barra.addWidget(b)
        barra.addWidget(self.lbl_zoom)
        for w in (b_mas, self.b_fav, b_copiar, self.c_int, self.b_pres, b_full):
            barra.addWidget(w)
        lay.addWidget(self.barra_sup)

        self.vista = VistaZoom()
        self.vista.zoom_cambiado.connect(
            lambda z: self.lbl_zoom.setText(f"{int(z * 100)} %"))
        self.vista.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vista.customContextMenuRequested.connect(self.menu_visor)
        lay.addWidget(self.vista, 1)

        self.progreso = BarraProgreso()
        self.progreso.hide()
        lay.addWidget(self.progreso)

        self.pop = PopFavorito(self.vista)
        self.toast_v = Toast(self)

        self.barra_inf = QWidget()
        nav = QHBoxLayout(self.barra_inf)
        nav.setContentsMargins(0, 0, 0, 0)
        ant = BotonAnimado("← Anterior")
        sig = BotonAnimado("Siguiente →")
        nav.addWidget(ant)
        nav.addStretch()
        nav.addStretch()
        nav.addWidget(sig)
        lay.addWidget(self.barra_inf)

        # Los botones no roban el foco: así Espacio / flechas siempre llegan a los atajos.
        for w in self.findChildren(QPushButton) + [self.c_int, self.vista]:
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._margenes = (lay.contentsMargins(), lay.spacing())
        self.t_pres = QTimer(self)
        self.t_pres.setInterval(40)
        self.t_pres.timeout.connect(self._tick_pres)
        self.b_pres.toggled.connect(self.alternar_presentacion)
        self.c_int.currentIndexChanged.connect(lambda _i: setattr(self, "_pres_ms", 0))
        self.b_fav.clicked.connect(self.alternar_fav)
        b_copiar.clicked.connect(self.copiar_imagen)

        b_aj.clicked.connect(self.vista.ajustar)
        b_100.clicked.connect(self.vista.cien)
        b_menos.clicked.connect(lambda: self.vista.zoom(0.8))
        b_mas.clicked.connect(lambda: self.vista.zoom(1.25))
        b_full.clicked.connect(self.pantalla_completa)
        ant.clicked.connect(lambda: self.navegar(-1))
        sig.clicked.connect(lambda: self.navegar(1))

        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=lambda: self.navegar(-1))
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=lambda: self.navegar(1))
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, activated=self.b_pres.toggle)
        QShortcut(QKeySequence(Qt.Key.Key_F), self, activated=self.alternar_fav)
        QShortcut(QKeySequence("Ctrl+C"), self, activated=self.copiar_imagen)
        QShortcut(QKeySequence(Qt.Key.Key_F11), self, activated=self.pantalla_completa)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self.salir)
        self.cargar()

    # --- pantalla completa: SOLO la CG, sin barras, sin Euracia, sin nada
    def pantalla_completa(self):
        if self.pres_activa:
            self.b_pres.setChecked(False)
        elif self._cg:
            self.salir_cg()
        else:
            self.entrar_cg()

    def entrar_cg(self):
        if self._cg:
            return
        self._cg = True
        lay = self.layout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.barra_sup.hide()
        self.barra_inf.hide()
        self.progreso.hide()
        self.vista.setBackgroundBrush(QColor(0, 0, 0))
        self.showFullScreen()

    def salir_cg(self):
        if not self._cg:
            return
        self._cg = False
        lay = self.layout()
        m, sp = self._margenes
        lay.setContentsMargins(m)
        lay.setSpacing(sp)
        self.barra_sup.show()
        self.barra_inf.show()
        self.vista.setBackgroundBrush(QColor(Tema.c("bg")))
        self.showNormal()

    def salir(self):
        if self.pres_activa:
            self.b_pres.setChecked(False)
        elif self._cg:
            self.salir_cg()
        elif self.isFullScreen():
            self.showNormal()
        else:
            self.close()

    # --- presentación
    def alternar_presentacion(self, activo):
        if activo:
            if len(self.items) < 2:
                self.b_pres.blockSignals(True)
                self.b_pres.setChecked(False)
                self.b_pres.blockSignals(False)
                self.toast_v.mostrar("Necesitas al menos 2 capturas para la presentación", 2600)
                return
            self.pres_activa = True
            self._pres_ms = 0
            self._pres_cg = not self._cg
            if self._pres_cg:
                self.entrar_cg()
            self.progreso.poner(0)
            self.progreso.show()
            self.b_pres.setText("⏸ Detener")
            self.t_pres.start()
            self.toast_v.mostrar("▶ Presentación  ·  Espacio o Esc: salir  ·  ← →: cambiar", 3200)
        else:
            self.pres_activa = False
            self.t_pres.stop()
            self.progreso.hide()
            self.b_pres.setText("▶ Presentación")
            if self._pres_cg:
                self.salir_cg()
                self._pres_cg = False

    def intervalo_ms(self):
        return int(self.c_int.currentData() or 5) * 1000

    def _tick_pres(self):
        self._pres_ms += self.t_pres.interval()
        self.progreso.poner(self._pres_ms / self.intervalo_ms())
        if self._pres_ms >= self.intervalo_ms():
            self.avanzar_pres()

    def avanzar_pres(self):
        self.ir_a((self.indice + 1) % len(self.items))

    # --- transición suave entre capturas
    def ir_a(self, nuevo):
        self.indice = nuevo
        self._pres_ms = 0
        self.progreso.poner(0)
        if not Tema.anim:
            self.cargar()
            return
        if self._an is not None:
            self._an.stop()
        self._ef = QGraphicsOpacityEffect(self.vista)
        self._ef.setOpacity(1.0)
        self.vista.setGraphicsEffect(self._ef)
        salida = QPropertyAnimation(self._ef, b"opacity", self)
        salida.setDuration(170)
        salida.setStartValue(1.0)
        salida.setEndValue(0.0)

        def al_salir():
            self.cargar()
            entrada = QPropertyAnimation(self._ef, b"opacity", self)
            entrada.setDuration(260)
            entrada.setStartValue(0.0)
            entrada.setEndValue(1.0)
            entrada.setEasingCurve(QEasingCurve.Type.OutCubic)
            entrada.finished.connect(lambda: self.vista.setGraphicsEffect(None))
            self._an = entrada
            entrada.start()

        salida.finished.connect(al_salir)
        self._an = salida
        salida.start()

    # --- favoritos
    def _registro(self):
        if self.db is None:
            return None
        return self.db.execute("SELECT id, favorito FROM imagenes WHERE ruta = ?",
                               (str(self.items[self.indice]),)).fetchone()

    def actualizar_fav(self):
        r = self._registro()
        on = bool(r and r[1])
        self.b_fav.setEnabled(r is not None)
        self.b_fav.setChecked(on)
        self.b_fav.setText("★ Favorito" if on else "☆ Favorito")

    def alternar_fav(self):
        r = self._registro()
        if not r:
            return
        nuevo = 0 if r[1] else 1
        self.db.execute("UPDATE imagenes SET favorito = ? WHERE id = ?", (nuevo, r[0]))
        self.db.commit()
        self.cambios = True
        self.actualizar_fav()
        if Tema.anim:
            self.pop.disparar(bool(nuevo))
        self.toast_v.mostrar("★ Añadida a Favoritos" if nuevo else "Quitada de Favoritos", 1800)

    # --- copiar / compartir
    def copiar_imagen(self):
        ruta = str(self.items[self.indice])
        if copiar_imagen_portapapeles(ruta, self.vista.item.pixmap()):
            self.toast_v.mostrar("📋 Imagen copiada", 2600)
        else:
            self.toast_v.mostrar("No se pudo copiar la imagen", 2400)

    def menu_visor(self, punto):
        ruta = str(self.items[self.indice])
        r = self._registro()
        m = QMenu(self)
        a_copia = m.addAction("📋  Copiar imagen")
        a_guardar = m.addAction("💾  Guardar una copia…")
        m.addSeparator()
        a_fav = None
        if r:
            a_fav = m.addAction("★  Quitar de favoritos" if r[1] else "☆  Añadir a favoritos")
        a_ubi = m.addAction("📂  Abrir ubicación del archivo")
        m.addSeparator()
        a_full = m.addAction("⛶  Salir de pantalla completa" if self._cg
                             else "⛶  Pantalla completa (solo la imagen)")
        a_aj = m.addAction("Ajustar a la ventana")
        a_100 = m.addAction("Tamaño real (100 %)")
        accion = m.exec(QCursor.pos())
        if accion is None:
            return
        if accion == a_copia:
            self.copiar_imagen()
        elif accion == a_guardar:
            destino, _ = QFileDialog.getSaveFileName(
                self, "Guardar una copia", str(Path.home() / Path(ruta).name), FILTRO_IMG)
            if destino:
                try:
                    shutil.copy2(ruta, destino)
                    self.toast_v.mostrar("💾 Copia guardada", 2200)
                except OSError as err:
                    QMessageBox.warning(self, "No se pudo guardar", str(err))
        elif a_fav is not None and accion == a_fav:
            self.alternar_fav()
        elif accion == a_ubi:
            if Path(ruta).exists():
                os.startfile(str(Path(ruta).parent))
        elif accion == a_full:
            self.pantalla_completa()
        elif accion == a_aj:
            self.vista.ajustar()
        elif accion == a_100:
            self.vista.cien()

    def cargar(self):
        ruta = self.items[self.indice]
        self.actualizar_fav()
        if not Path(ruta).exists():
            self.titulo.setText("Archivo no encontrado")
            return
        lector = QImageReader(ruta)
        lector.setAutoTransform(True)
        img = lector.read()
        if img.isNull():
            self.titulo.setText("No se pudo cargar la imagen")
            return
        pm = QPixmap.fromImage(img)
        self.titulo.setText(
            f"{pm.width()} × {pm.height()}  ·  {self.indice + 1}/{len(self.items)}")
        self.vista.poner(pm)

    def navegar(self, d):
        nuevo = self.indice + d
        if 0 <= nuevo < len(self.items):
            self.ir_a(nuevo)


# =========================================================
# DIALOGOS
# =========================================================

class BotonFechas(QWidget):
    """Pastilla del encabezado de la novela: cuándo empezaste, cuándo terminaste y cuántos días.
    Un clic la abre para editarla."""
    clic = Signal()

    def __init__(self):
        super().__init__()
        self.ini = self.fin = ""
        self.horas = 0.0
        self.vols = 0
        self.sin_f = self.sin_h = False
        self._h = 0.0
        self._an = QVariantAnimation(self)
        self._an.setDuration(160)
        self._an.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._an.valueChanged.connect(self._set)
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def _set(self, v):
        self._h = float(v)
        self.update()

    def _ir(self, fin):
        if Tema.anim:
            self._an.stop()
            self._an.setStartValue(self._h)
            self._an.setEndValue(fin)
            self._an.start()
        else:
            self._h = fin
            self.update()

    def enterEvent(self, e):
        self._ir(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._ir(0.0)
        super().leaveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clic.emit()

    def poner(self, ini, fin, horas=0.0, sin_f=0, sin_h=0, vols=0):
        self.ini, self.fin = ini or "", fin or ""
        self.horas = float(horas or 0)
        self.vols = int(vols or 0)
        self.sin_f, self.sin_h = bool(sin_f), bool(sin_h)
        dias, _ = calcular_dias(self.ini, self.fin) if self.ini else (None, False)
        if self.vols > 1:
            self.setToolTip("Esta novela tiene varios volúmenes, cada uno con sus fechas y horas "
                            "(clic para editar)")
        elif self.horas and dias:
            self.setToolTip(f"{fmt_horas(self.horas)} en {dias} {'día' if dias == 1 else 'días'}"
                            f" ≈ {self.horas / dias:.1f} h por día".replace(".", ","))
        else:
            self.setToolTip("Fechas y horas de juego de esta novela (clic para editar)")
        self.updateGeometry()
        self.update()

    def _partes(self):
        texto, chip = self._partes_base()
        if self.vols > 1:                    # varios volúmenes: el total de días no tiene sentido
            texto, chip = f"📚 {self.vols} vol.   ·   " + texto, ""
        return texto, chip

    def _partes_base(self):
        extra = (f"⏱ {fmt_horas(self.horas)}" if self.horas
                 else ("🤷 horas omitidas" if self.sin_h else ""))
        if self.sin_f:
            return "🤷 Fechas omitidas" + (f"   ·   {extra}" if extra else ""), ""
        if not self.ini:
            return (extra or "📅  Añadir fechas y horas de juego"), ""
        fin = f"🏁 {fmt_fecha(self.fin)}" if self.fin else "📖 novela actual"
        dias, _ = calcular_dias(self.ini, self.fin)
        chip = "" if (dias is None or not self.fin) else f"{dias} {'día' if dias == 1 else 'días'}"
        texto = f"📅 {fmt_fecha(self.ini)}   →   {fin}"
        if extra:
            texto += f"   ·   {extra}"
        return texto, chip

    def sizeHint(self):
        texto, chip = self._partes()
        w = 34 + QFontMetrics(fnt(Tema.tam - 0.5)).horizontalAdvance(texto)
        if chip:
            w += QFontMetrics(fnt(Tema.tam - 1, bold=True)).horizontalAdvance(chip) + 30
        return QSize(int(w), 38)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        h = self._h
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        rad = r.height() / 2
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, mezclar(card, a1, 0.10 + 0.14 * h))
        g.setColorAt(1, mezclar(card, a2, 0.06 + 0.12 * h))
        p.setBrush(QBrush(g))
        estilo = Qt.PenStyle.SolidLine if (self.ini or self.sin_f) else Qt.PenStyle.DashLine
        p.setPen(QPen(mezclar(borde, a1, 0.35 + 0.65 * h), 1.4, estilo))
        p.drawRoundedRect(r, rad, rad)
        texto, chip = self._partes()
        ancho_chip = 0.0
        if chip:
            fb = fnt(Tema.tam - 1, bold=True)
            ancho_chip = QFontMetrics(fb).horizontalAdvance(chip) + 22
            c = QRectF(r.right() - ancho_chip - 5, r.top() + 5, ancho_chip, r.height() - 10)
            gc = QLinearGradient(c.topLeft(), c.topRight())
            gc.setColorAt(0, a1)
            gc.setColorAt(1, a2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(gc))
            p.drawRoundedRect(c, c.height() / 2, c.height() / 2)
            p.setFont(fb)
            p.setPen(QColor(TEXTO_SOBRE_ACENTO))
            p.drawText(c, int(Qt.AlignmentFlag.AlignCenter), chip)
        texto_el(p, r.left() + 16, r.top(), r.width() - 24 - (ancho_chip + 8 if chip else 0),
                 r.height(), texto, fnt(Tema.tam - 0.5),
                 QColor(Tema.c("text") if self.ini else Tema.c("muted")))
        p.end()


# ====================================================================
# Fechas, horas y notas fáciles de escribir
# ====================================================================
_ALIAS_MES = {m[:3]: i + 1 for i, m in enumerate(MESES_ES)}
_ALIAS_MES.update({"set": 9, "sep": 9})


def parsear_horas(txt):
    """'34.4' · '34,4' · '34h 24m' · '34:24' · '34 h' · '45 min' -> horas (float); None si no se
    entiende; 0.0 si está vacío."""
    t = (txt or "").strip().lower().replace(",", ".")
    if not t:
        return 0.0
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hora|horas)?", t)
    if m:
        return float(m.group(1))
    m = re.fullmatch(r"(\d+)\s*(?:h|hr|hrs|horas?|:)\s*(\d{1,2})\s*(?:m|min|mins|minutos?)?", t)
    if m and int(m.group(2)) < 60:
        return int(m.group(1)) + int(m.group(2)) / 60.0
    m = re.fullmatch(r"(\d+)\s*(?:m|min|mins|minutos?)", t)
    if m:
        return int(m.group(1)) / 60.0
    return None


def parsear_fecha(txt, ref=None, hoy=None):
    """Entiende 'hoy', 'ayer', '5', '5/10', '5/10/26', '05-10-2026', '5 oct', '5 de octubre 2026'
    y '2026-10-05'. Con `ref` (la fecha de inicio) lo que falta se toma de ella y nunca queda
    antes del inicio. Devuelve datetime.date o None."""
    hoy = hoy or datetime.date.today()
    t = " ".join((txt or "").lower().replace(",", " ").split())
    if not t:
        return None
    rel = {"hoy": 0, "ayer": -1, "anteayer": -2, "antier": -2, "mañana": 1, "manana": 1}
    if t in rel:
        return hoy + datetime.timedelta(days=rel[t])
    base = ref or hoy
    d = m = y = None
    solo_dia = False
    r = re.fullmatch(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", t)
    if r:
        y, m, d = int(r.group(1)), int(r.group(2)), int(r.group(3))
    else:
        r = re.fullmatch(r"(\d{1,2})\s*[/\-. ]\s*(\d{1,2})(?:\s*[/\-. ]\s*(\d{2}|\d{4}))?", t)
        if r:
            d, m = int(r.group(1)), int(r.group(2))
            y = int(r.group(3)) if r.group(3) else None
        else:
            r = re.fullmatch(r"(\d{1,2})\s*(?:de\s+)?([a-záéíóúñ]{3,})\.?"
                             r"(?:\s*(?:de\s+)?(\d{2}|\d{4}))?", t)
            if r and r.group(2)[:3] in _ALIAS_MES:
                d, m = int(r.group(1)), _ALIAS_MES[r.group(2)[:3]]
                y = int(r.group(3)) if r.group(3) else None
            else:
                r = re.fullmatch(r"(\d{1,2})", t)
                if not r:
                    return None
                d, m, y, solo_dia = int(r.group(1)), base.month, None, True
    if y is not None and y < 100:
        y += 2000
    sin_anio = y is None
    try:
        f = datetime.date(y if y else base.year, m, d)
    except ValueError:
        return None
    if ref and sin_anio and f < ref:                 # la fecha de fin no puede ser anterior
        try:
            if solo_dia:
                mm, yy = (ref.month % 12) + 1, ref.year + (1 if ref.month == 12 else 0)
                f = datetime.date(yy, mm, d)
            else:
                f = datetime.date(base.year + 1, m, d)
        except ValueError:
            return None
    return f


def fmt_nota(n):
    """8 -> '8' · 8.5 -> '8,5' (vacío si no hay nota)."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return ""
    if n <= 0:
        return ""
    return f"{int(n)}" if abs(n - round(n)) < 0.01 else f"{n:.1f}".replace(".", ",")


ETIQUETAS_NOTA = {10: "Obra maestra", 9: "Excelente", 8: "Muy buena", 7: "Buena",
                  6: "Entretenida", 5: "Regular", 4: "Floja", 3: "Mala", 2: "Muy mala",
                  1: "Para olvidar"}


def colores_de_portada(ruta):
    """Dos colores (hex) que representan la portada: los tonos más vivos y frecuentes, ya
    ajustados para que el texto oscuro sobre ellos se lea bien. None si la portada es gris."""
    try:
        pm = CACHE_GRANDE.obtener(ruta, 120)
        if pm.isNull():
            return None
        img = pm.toImage().scaled(48, 48, Qt.AspectRatioMode.IgnoreAspectRatio,
                                  Qt.TransformationMode.FastTransformation
                                  ).convertToFormat(QImage.Format.Format_RGB32)
    except Exception:
        return None
    bins = {}
    for y in range(48):
        for x in range(48):
            h, s, l, _a = QColor(img.pixel(x, y)).getHslF()
            if h < 0 or s < 0.22 or l < 0.14 or l > 0.92:
                continue
            peso = s * (1.0 - abs(l - 0.5) * 1.1)
            b = bins.setdefault(int(h * 24) % 24, [0.0, 0.0, 0.0])
            b[0] += peso
            b[1] += peso * s
            b[2] += peso * l
    if not bins:
        return None
    orden = sorted(bins.items(), key=lambda kv: -kv[1][0])

    def tono(k, v):
        return QColor.fromHslF((k + 0.5) / 24.0, min(0.9, max(0.58, v[1] / v[0])),
                               min(0.70, max(0.58, v[2] / v[0])))
    k0, v0 = orden[0]
    c1 = tono(k0, v0)
    c2 = None
    for k, v in orden[1:]:
        dist = min(abs(k - k0), 24 - abs(k - k0))
        if dist >= 3 and v[0] >= v0[0] * 0.2:
            c2 = tono(k, v)
            break
    if c2 is None:
        c2 = QColor.fromHslF(((k0 + 0.5) / 24.0 + 0.08) % 1.0, c1.hslSaturationF(),
                             min(0.78, c1.lightnessF() + 0.08))
    return c1.name(), c2.name()


class _LineaSinEnter(QLineEdit):
    """Enter pasa al siguiente campo en vez de cerrar el diálogo entero."""

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.focusNextChild()
            e.accept()
            return
        super().keyPressEvent(e)


class CampoFecha(QWidget):
    """Fecha escrita a mano y flexible (5 · 5/10 · 5 oct · ayer · hoy…) con calendario. Si le das
    una fecha de referencia (el inicio), lo que no escribas se toma de ella."""
    dateChanged = Signal(QDate)
    DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")

    def __init__(self, fecha, ref=None):
        super().__init__()
        self._fecha, self._ref = fecha, ref
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self.e = _LineaSinEnter()
        self.e.setPlaceholderText("5 · 5/10 · 5 oct · ayer")
        self.e.setMinimumWidth(130)
        self.e.editingFinished.connect(self._terminar)
        self.b = BotonAnimado("📅")
        self.b.setAutoDefault(False)
        self.b.setFixedSize(44, 32)
        self.b.setToolTip("Elegir en el calendario")
        self.b.clicked.connect(self._calendario)
        lay.addWidget(self.e, 1)
        lay.addWidget(self.b)
        self._mostrar()

    @staticmethod
    def _py(q):
        return datetime.date(q.year(), q.month(), q.day())

    def date(self):
        return self._fecha

    def setDate(self, q):
        cambio = q != self._fecha
        self._fecha = q
        self._mostrar()
        if cambio:
            self.dateChanged.emit(q)

    def _mostrar(self):
        q = self._fecha
        self.e.setText(f"{q.day():02d}/{q.month():02d}/{q.year()}")
        d = self._py(q)
        self.e.setToolTip(f"{self.DIAS[d.weekday()]} {d.day} de {MESES_ES[d.month - 1]} de {d.year}")

    def _terminar(self):
        ref = self._py(self._ref.date()) if self._ref is not None else None
        f = parsear_fecha(self.e.text(), ref)
        if f is None:
            self.e.setStyleSheet("border: 2px solid #ff6b6b;")
            QTimer.singleShot(900, lambda: self.e.setStyleSheet(""))
            self._mostrar()
            return
        self.setDate(QDate(f.year, f.month, f.day))

    def _calendario(self):
        m = QMenu(self)
        cal = QCalendarWidget()
        cal.setSelectedDate(self._fecha)
        wa = QWidgetAction(m)
        wa.setDefaultWidget(cal)
        m.addAction(wa)
        cal.clicked.connect(lambda q: (self.setDate(q), m.close()))
        m.exec(self.b.mapToGlobal(QPoint(0, self.b.height())))


class CampoHoras(QWidget):
    """Horas jugadas: escribe 34.4, 34,4, 34h 24m o 34:24; todo vale."""
    valueChanged = Signal(float)

    def __init__(self):
        super().__init__()
        self._v = 0.0
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.e = _LineaSinEnter()
        self.e.setPlaceholderText("ej. 34.4 · 34h 24m")
        self.e.setMinimumWidth(130)
        self.e.setMaximumWidth(190)
        self.e.textEdited.connect(self._escrito)
        self.e.editingFinished.connect(self._terminar)
        self.lbl = QLabel("")
        self.lbl.setObjectName("muted")
        lay.addWidget(self.e)
        lay.addWidget(self.lbl)
        lay.addStretch()

    def value(self):
        return self._v

    def setValue(self, v):
        v = max(0.0, min(9999.0, float(v or 0)))
        cambio = abs(v - self._v) > 1e-9
        self._v = v
        self._texto()
        if cambio:
            self.valueChanged.emit(v)

    def _texto(self):
        v = self._v
        self.e.setText("" if v <= 0 else (f"{round(v, 2):g}").replace(".", ","))
        self._pista()

    def _pista(self):
        v = self._v
        h, mi = int(v), int(round((v - int(v)) * 60))
        self.lbl.setText(f"= {h} h {mi} min" if v > 0 and mi else (f"= {h} h" if v > 0 else ""))

    def _escrito(self, txt):
        v = parsear_horas(txt)
        if v is None:
            return
        self._v = min(9999.0, v)
        self._pista()
        self.valueChanged.emit(self._v)

    def _terminar(self):
        v = parsear_horas(self.e.text())
        if v is None:
            self.e.setStyleSheet("border: 2px solid #ff6b6b;")
            QTimer.singleShot(900, lambda: self.e.setStyleSheet(""))
        else:
            self._v = min(9999.0, v)
        self._texto()


def _estrella(cx, cy, r):
    pol = QPolygonF()
    for k in range(10):
        ang = -pi / 2 + k * pi / 5
        rr = r if k % 2 == 0 else r * 0.46
        pol.append(QPointF(cx + rr * cos(ang), cy + rr * sin(ang)))
    return pol


class EstrellasNota(QWidget):
    """Diez estrellas: pasa el ratón y haz clic (mitad izquierda = media estrella)."""
    elegida = Signal(float)

    def __init__(self, valor):
        super().__init__()
        self.valor, self._hover = float(valor or 0), 0.0
        self.setFixedSize(344, 96)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _en(self, x):
        return max(0.5, min(10.0, ceil((x - 12) / 16.0) / 2.0))

    def mouseMoveEvent(self, e):
        self._hover = self._en(e.position().x())
        self.update()

    def leaveEvent(self, e):
        self._hover = 0.0
        self.update()
        super().leaveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.elegida.emit(self._en(e.position().x()))

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        v = self._hover or self.valor
        etq = ETIQUETAS_NOTA.get(int(ceil(v)), "") if v else "Sin calificar"
        txt = f"{fmt_nota(v)} / 10  ·  {etq}" if v else etq
        p.setFont(fnt(Tema.tam + 1, bold=True))
        p.setPen(QColor(Tema.c("text")))
        p.drawText(QRectF(0, 6, self.width(), 26), int(Qt.AlignmentFlag.AlignCenter), txt)
        for i in range(10):
            cx, cy = 12 + i * 32 + 16, 62
            cam = QPainterPath()
            cam.addPolygon(_estrella(cx, cy, 15))
            p.setPen(QPen(QColor(Tema.c("border")), 1.4))
            p.setBrush(con_alfa(a1, 24))
            p.drawPath(cam)
            frac = max(0.0, min(1.0, v - i))
            if frac > 0:
                p.save()
                p.setClipRect(QRectF(cx - 16, cy - 16, 32 * frac, 32))
                g = QLinearGradient(cx - 16, cy - 16, cx + 16, cy + 16)
                g.setColorAt(0, a1)
                g.setColorAt(1, a2)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(g))
                p.drawPath(cam)
                p.restore()
        p.end()


class TarjetaVolumen(QFrame):
    """Una parte de la novela: cuándo la empezaste, cuándo la terminaste y cuántas horas jugaste.
    Una novela normal tiene una sola; una por volúmenes (Nekopara...) tiene una por volumen."""
    cambio = Signal()
    quitar = Signal(object)
    tras_anterior = Signal(object)

    def __init__(self, datos, hoy):
        super().__init__()
        self.setObjectName("panel")
        self._sync = False
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(8)

        # ---- nombre del volumen (solo si hay varios)
        self.cab = QWidget()
        top = QHBoxLayout(self.cab)
        top.setContentsMargins(0, 0, 0, 0)
        self.e_nombre = QLineEdit(datos.get("nombre", ""))
        self.e_nombre.setPlaceholderText("Nombre del volumen (ej. Vol. 2)")
        self.b_quitar = BotonAnimado("✕")
        self.b_quitar.setAutoDefault(False)
        self.b_quitar.setFixedWidth(42)
        self.b_quitar.setToolTip("Quitar este volumen")
        self.b_quitar.clicked.connect(lambda: self.quitar.emit(self))
        top.addWidget(self.e_nombre, 1)
        top.addWidget(self.b_quitar)
        v.addWidget(self.cab)

        # ---- fechas: se escriben (5 · 5/10 · 5 oct · ayer) o se eligen en el calendario
        ini_q = self._a_qdate(datos.get("ini"), hoy)
        fin_q = self._a_qdate(datos.get("fin"), ini_q)
        if fin_q < ini_q:
            fin_q = ini_q
        self.f_ini = CampoFecha(ini_q)
        self.f_fin = CampoFecha(fin_q, ref=self.f_ini)
        self.s_dias = QSpinBox()
        self.s_dias.setRange(1, 9999)
        self.s_dias.setSuffix(" días")
        self.s_horas = CampoHoras()
        self.s_horas.setValue(float(datos.get("horas") or 0))

        def chips(*items):
            c = QWidget()
            lay = QHBoxLayout(c)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(4)
            for texto, fn in items:
                b = BotonAnimado(texto)
                b.setAutoDefault(False)
                b.setFixedHeight(32)
                b.clicked.connect(lambda _=False, fn=fn: fn())
                lay.addWidget(b)
            lay.addStretch()
            return c

        hoy_f = QDate.currentDate
        self.caja_f = QWidget()
        g = QGridLayout(self.caja_f)
        g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(8)
        g.setVerticalSpacing(8)
        g.addWidget(QLabel("🚀 Empecé"), 0, 0)
        g.addWidget(self.f_ini, 0, 1)
        c_ini = chips(("Hoy", lambda: self.f_ini.setDate(hoy_f())),
                      ("Ayer", lambda: self.f_ini.setDate(hoy_f().addDays(-1))),
                      ("Hace 1 sem", lambda: self.f_ini.setDate(hoy_f().addDays(-7))))
        self.b_tras = BotonAnimado("↳ Tras el anterior")
        self.b_tras.setAutoDefault(False)
        self.b_tras.setFixedHeight(32)
        self.b_tras.setToolTip("Empieza el día después de que terminó el volumen anterior")
        self.b_tras.clicked.connect(lambda: self.tras_anterior.emit(self))
        c_ini.layout().insertWidget(c_ini.layout().count() - 1, self.b_tras)
        self.b_tras.setVisible(False)
        g.addWidget(c_ini, 0, 2)
        g.addWidget(QLabel("🏁 Terminé"), 1, 0)
        g.addWidget(self.f_fin, 1, 1)
        g.addWidget(chips(("Hoy", lambda: self.f_fin.setDate(hoy_f())),
                          ("Ayer", lambda: self.f_fin.setDate(hoy_f().addDays(-1))),
                          ("Mismo día", lambda: self.f_fin.setDate(self.f_ini.date())),
                          ("1 sem", lambda: self.f_fin.setDate(self.f_ini.date().addDays(6))),
                          ("2 sem", lambda: self.f_fin.setDate(self.f_ini.date().addDays(13))),
                          ("1 mes", lambda: self.f_fin.setDate(
                              self.f_ini.date().addMonths(1).addDays(-1))),
                          ("3 meses", lambda: self.f_fin.setDate(
                              self.f_ini.date().addMonths(3).addDays(-1)))), 1, 2)
        g.addWidget(QLabel("⏳ Duró"), 2, 0)
        g.addWidget(self.s_dias, 2, 1)
        g.setColumnStretch(1, 1)
        v.addWidget(self.caja_f)

        # ---- horas: 34.4 · 34,4 · 34h 24m · 34:24
        self.caja_h = QWidget()
        h = QHBoxLayout(self.caja_h)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        h.addWidget(QLabel("⏱ Horas"))
        h.addWidget(self.s_horas, 1)
        for texto, delta in (("−5", -5), ("−1", -1), ("+½ h", 0.5), ("+1", 1), ("+5", 5),
                             ("+10", 10)):
            b = BotonAnimado(texto)
            b.setAutoDefault(False)
            b.setFixedHeight(32)
            b.clicked.connect(lambda _=False, d=delta: self.s_horas.setValue(
                self.s_horas.value() + d))
            h.addWidget(b)
        b = BotonAnimado("✕")
        b.setAutoDefault(False)
        b.setFixedHeight(32)
        b.setToolTip("Borrar las horas")
        b.clicked.connect(lambda: self.s_horas.setValue(0))
        h.addWidget(b)
        v.addWidget(self.caja_h)

        # ---- «no recuerdo» y resumen
        pie = QHBoxLayout()
        self.k_actual = QCheckBox("📖 Novela actual (aún no la termino)")
        self.k_actual.setToolTip("Solo pide la fecha de inicio. Cuando termines, desmarca esta "
                                 "casilla y pon la fecha de fin.")
        self.k_actual.setChecked(bool(datos.get("ini")) and not datos.get("fin")
                                 and not datos.get("sin_f"))
        pie.addWidget(self.k_actual)
        self.b_termine = BotonAnimado("🏁 La terminé hoy")
        self.b_termine.setAutoDefault(False)
        self.b_termine.setFixedHeight(32)
        self.b_termine.setToolTip("Quita «novela actual» y pone hoy como fecha de fin")
        self.b_termine.clicked.connect(self._terminar_hoy)
        pie.addWidget(self.b_termine)
        pie.addStretch()
        v.addLayout(pie)
        pie2 = QHBoxLayout()
        self.k_sin_f = QCheckBox("🤷 No recuerdo las fechas")
        self.k_sin_f.setChecked(bool(datos.get("sin_f")))
        self.k_sin_h = QCheckBox("🤷 No recuerdo las horas")
        self.k_sin_h.setChecked(bool(datos.get("sin_h")))
        pie2.addWidget(self.k_sin_f)
        pie2.addSpacing(18)
        pie2.addWidget(self.k_sin_h)
        pie2.addStretch()
        v.addLayout(pie2)
        self.lbl = QLabel("")
        self.lbl.setObjectName("muted")
        self.lbl.setWordWrap(True)
        v.addWidget(self.lbl)

        self.f_ini.dateChanged.connect(self._ini_cambio)
        self.f_fin.dateChanged.connect(self._fin_cambio)
        self.s_dias.valueChanged.connect(self._cambio_dias)
        self.s_horas.valueChanged.connect(self._refrescar)
        self.k_actual.toggled.connect(self._refrescar)
        self.k_sin_f.toggled.connect(self._refrescar)
        self.k_sin_h.toggled.connect(self._refrescar)
        self._fin_cambio()

    @staticmethod
    def _a_qdate(iso, defecto):
        try:
            d = datetime.date.fromisoformat(str(iso))
            return QDate(d.year, d.month, d.day)
        except (TypeError, ValueError):
            return defecto

    def _ini_cambio(self, *_):
        """Al cambiar el inicio, el fin se mueve con él (se conserva la duración)."""
        if self._sync:
            return
        self._sync = True
        self.f_fin.setDate(self.f_ini.date().addDays(self.s_dias.value() - 1))
        self._sync = False
        self._refrescar()

    def _fin_cambio(self, *_):
        if self._sync:
            return
        self._sync = True
        if self.f_fin.date() < self.f_ini.date():
            self.f_fin.setDate(self.f_ini.date())
        self.s_dias.setValue(self.f_ini.date().daysTo(self.f_fin.date()) + 1)
        self._sync = False
        self._refrescar()

    def _cambio_dias(self, n):
        if self._sync:
            return
        self._sync = True
        self.f_fin.setDate(self.f_ini.date().addDays(n - 1))
        self._sync = False
        self._refrescar()

    def _refrescar(self, *_):
        sin_f, sin_h = self.k_sin_f.isChecked(), self.k_sin_h.isChecked()
        actual = self.k_actual.isChecked() and not sin_f
        self.caja_f.setEnabled(not sin_f)
        self.f_fin.setEnabled(not actual)
        self.s_dias.setEnabled(not actual)
        self.caja_h.setEnabled(not sin_h)
        self.b_termine.setVisible(actual)
        hoy = QDate.currentDate()
        if actual:
            dias = max(1, self.f_ini.date().daysTo(hoy) + 1)
        else:
            dias = self.s_dias.value()
        partes = []
        if sin_f:
            partes.append("Sin fechas: no saldrá en la línea de tiempo")
        elif actual:
            partes.append(f"📖 En curso · {dias} {'día' if dias == 1 else 'días'} hasta hoy")
        else:
            partes.append(f"{dias} {'día' if dias == 1 else 'días'}")
        if not sin_h and self.s_horas.value() > 0:
            hh = self.s_horas.value()
            partes.append(fmt_horas(hh))
            if not sin_f:
                hpd = hh / dias
                partes.append(f"≈ {hpd:.1f} h por día".replace(".", ","))
                if dias >= 7:
                    partes.append(f"≈ {hpd * 7:.0f} h por semana")
                partes.append(self._ritmo(hpd))
        avisos = []
        if not sin_f:
            if self.f_ini.date() > hoy:
                avisos.append("⚠ la fecha de inicio es futura")
            elif not actual and self.f_fin.date() > hoy:
                avisos.append("⚠ la fecha de fin es futura")
        txt = "  ·  ".join(partes)
        if avisos:
            txt += "\n" + "  ·  ".join(avisos)
        self.lbl.setText(txt)
        self.cambio.emit()

    @staticmethod
    def _ritmo(hpd):
        """Etiqueta de ritmo según las horas jugadas por día."""
        if hpd < 1:
            return "🌿 ritmo tranquilo"
        if hpd < 3:
            return "📘 ritmo constante"
        if hpd < 6:
            return "🔥 ritmo intenso"
        return "🚀 maratón"

    def _terminar_hoy(self):
        """Pasa de «novela actual» a terminada, con hoy como fecha de fin."""
        self.k_actual.setChecked(False)
        hoy = QDate.currentDate()
        self.f_fin.setDate(hoy if hoy >= self.f_ini.date() else self.f_ini.date())
        self._fin_cambio()

    def poner_modo(self, varios):
        self.cab.setVisible(varios)
        self.b_tras.setVisible(varios)

    def datos(self, defecto_nombre=""):
        sin_f, sin_h = self.k_sin_f.isChecked(), self.k_sin_h.isChecked()
        actual = self.k_actual.isChecked()
        return dict(
            nombre=self.e_nombre.text().strip() or defecto_nombre,
            ini="" if sin_f else self.f_ini.date().toString("yyyy-MM-dd"),
            fin="" if (sin_f or actual) else self.f_fin.date().toString("yyyy-MM-dd"),
            horas=0.0 if sin_h else round(self.s_horas.value(), 1),
            sin_f=sin_f, sin_h=sin_h)


class DialogoFechasNovela(QDialog):
    """Fechas y horas de juego de una novela. Una novela normal tiene una sola parte; si la
    jugaste por volúmenes (Nekopara...) añade uno por cada parte, cada uno con sus propias
    fechas y horas. Si no recuerdas las fechas o las horas, puedes omitirlas."""

    def __init__(self, parent, nombre, partes=None):
        super().__init__(parent)
        self.setWindowTitle("Fechas y horas de juego")
        self.setMinimumSize(820, 640)
        self.resize(900, 820)
        self.vaciado = False
        self.tarjetas = []
        v = QVBoxLayout(self)
        v.setSpacing(10)
        cab = QLabel(f"📅 {nombre}")
        cab.setObjectName("heading")
        cab.setWordWrap(True)
        v.addWidget(cab)
        ayuda = QLabel("Anota cuándo la empezaste, cuándo la terminaste y cuántas horas jugaste. "
                       "¿La jugaste por partes, como Nekopara? Pulsa «Añadir otro volumen» y pon "
                       "las fechas de cada uno por separado.")
        ayuda.setObjectName("muted")
        ayuda.setWordWrap(True)
        v.addWidget(ayuda)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        interior = QWidget()
        interior.setAutoFillBackground(False)
        self.scroll.viewport().setAutoFillBackground(False)
        self.lista = QVBoxLayout(interior)
        self.lista.setContentsMargins(0, 0, 6, 0)
        self.lista.setSpacing(10)
        self.lista.addStretch()
        self.scroll.setWidget(interior)
        v.addWidget(self.scroll, 1)

        self.b_add = BotonAnimado("➕  Añadir otro volumen")
        self.b_add.setAutoDefault(False)
        self.b_add.clicked.connect(self._anadir)
        v.addWidget(self.b_add)

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setObjectName("heading")
        self.lbl_resumen.setWordWrap(True)
        v.addWidget(self.lbl_resumen)
        self.lbl_extra = QLabel("")
        self.lbl_extra.setObjectName("muted")
        self.lbl_extra.setWordWrap(True)
        v.addWidget(self.lbl_extra)

        botones = QHBoxLayout()
        b_borrar = BotonAnimado("Borrar todo")
        b_borrar.setAutoDefault(False)
        b_borrar.clicked.connect(self._borrar)
        b_c = BotonAnimado("Cancelar")
        b_c.setAutoDefault(False)
        b_c.clicked.connect(self.reject)
        b_g = BotonAnimado("Guardar", primario=True)
        b_g.clicked.connect(self.accept)
        botones.addWidget(b_borrar)
        botones.addStretch()
        botones.addWidget(b_c)
        botones.addWidget(b_g)
        v.addLayout(botones)

        for d in (partes or [{}]):
            self._nueva(d)
        self._modo()

    def _nueva(self, datos):
        t = TarjetaVolumen(datos, QDate.currentDate())
        t.cambio.connect(self._resumen)
        t.quitar.connect(self._quitar)
        t.tras_anterior.connect(self._tras_anterior)
        self.lista.insertWidget(self.lista.count() - 1, t)
        self.tarjetas.append(t)
        return t

    def _anadir(self):
        if len(self.tarjetas) == 1 and not self.tarjetas[0].e_nombre.text().strip():
            self.tarjetas[0].e_nombre.setText("Vol. 1")
        t = self._nueva({"nombre": f"Vol. {len(self.tarjetas) + 1}"})
        self._modo()
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))
        t.e_nombre.setFocus()
        t.e_nombre.selectAll()

    def _tras_anterior(self, t):
        """El volumen empieza el día después de que terminó el anterior."""
        i = self.tarjetas.index(t)
        if i == 0:
            return
        prev = self.tarjetas[i - 1]
        if prev.k_sin_f.isChecked():
            return
        hoy = QDate.currentDate()
        if prev.k_actual.isChecked():
            t.f_ini.setDate(hoy)
        else:
            t.f_ini.setDate(prev.f_fin.date().addDays(1))

    def _quitar(self, t):
        if len(self.tarjetas) <= 1:
            return
        self.tarjetas.remove(t)
        t.setParent(None)
        t.deleteLater()
        self._modo()

    def _modo(self):
        varios = len(self.tarjetas) > 1
        for t in self.tarjetas:
            t.poner_modo(varios)
            t.b_quitar.setEnabled(varios)
        self.b_add.setText("➕  Añadir otro volumen" if varios else "➕  La jugué por volúmenes: añadir otro")
        self._resumen()

    def _resumen(self, *_):
        ps = [t.datos() for t in self.tarjetas]
        horas = sum(p["horas"] for p in ps)
        con_f = [p for p in ps if p["ini"]]
        txt = []
        if len(ps) > 1:
            txt.append(f"📚 {len(ps)} volúmenes")
        if con_f:
            a = min(p["ini"] for p in con_f)
            b = "" if any(not p["fin"] for p in con_f) else max(p["fin"] for p in con_f)
            txt.append(f"📅 {fmt_fecha(a)} → {fmt_fecha(b) if b else 'en curso'}")
        if horas > 0:
            txt.append(f"⏱ {fmt_horas(horas)} en total")
        self.lbl_resumen.setText("   ·   ".join(txt))
        # ---- detalles: días totales, ritmo medio, volúmenes terminados y avisos
        extra = []
        try:
            hoy = datetime.date.today()
            d_ini = datetime.date.fromisoformat(min(p["ini"] for p in con_f)) if con_f else None
            if d_ini:
                fines = [datetime.date.fromisoformat(p["fin"]) if p["fin"] else hoy
                         for p in con_f]
                dias_tot = max(1, (max(fines) - d_ini).days + 1)
                extra.append(f"🗓 {dias_tot} {'día' if dias_tot == 1 else 'días'} desde el primer "
                             "inicio" + (" hasta hoy" if any(not p["fin"] for p in con_f) else
                                         " hasta el último fin"))
                if horas > 0:
                    extra.append(f"≈ {horas / dias_tot:.1f} h por día".replace(".", ","))
            if len(ps) > 1:
                n_ok = sum(1 for p in con_f if p["fin"])
                extra.append(f"✅ {n_ok} de {len(ps)} volúmenes terminados")
                tramos = sorted((p["ini"], p["fin"] or hoy.isoformat(), p["nombre"])
                                for p in con_f)
                for a, b in zip(tramos, tramos[1:]):
                    if b[0] <= a[1]:
                        extra.append(f"ℹ «{a[2] or 'Vol.'}» y «{b[2] or 'Vol.'}» se solapan "
                                     "en fechas")
                        break
        except (ValueError, TypeError):
            pass
        self.lbl_extra.setText("   ·   ".join(extra))

    def _borrar(self):
        self.vaciado = True
        self.accept()

    def partes(self):
        """Lista de dicts (nombre, ini, fin, horas, sin_f, sin_h); vacía si pulsó «Borrar todo»."""
        if self.vaciado:
            return []
        if len(self.tarjetas) == 1:
            return [{**self.tarjetas[0].datos(), "nombre": ""}]
        return [t.datos(f"Vol. {i + 1}") for i, t in enumerate(self.tarjetas)]


class DialogoRankear(QDialog):
    """Ranking sin arrastrar miniaturas:
    · ⭐ Puntuar rápido: ves cada captura y pulsas 1-5 (sube las mejores solas).
    · ⚔ Duelos: te muestro 2 y eliges la mejor (inserción binaria: muchos menos duelos que
      comparar todas con todas). Puedes meter solo las últimas que añadiste a tu top."""

    def __init__(self, parent, cat, items, modo, ultimas=0):
        super().__init__(parent)
        self.calificar = modo == "calificar"      # igual que puntuar, pero guarda estrellas
        if self.calificar:
            modo = "puntuar"
        self.log = []                             # duelos decididos: (ganador, perdedor)
        self.items = items
        self.por_id = {i["id"]: i for i in items}
        self.modo = modo
        self.cat = cat
        self.resultado = [i["id"] for i in items]
        self.setWindowTitle(f"{'Calificar' if self.calificar else 'Rankear fácil'} · {cat}")
        self.resize(*((900, 680) if self.calificar else (1120, 740)))
        v = QVBoxLayout(self)
        v.setSpacing(8)
        titulo = QLabel(("⭐ Calificar capturas" if self.calificar else "⭐ Puntuar rápido")
                        if modo == "puntuar" else "⚔ Duelos")
        titulo.setObjectName("heading")
        v.addWidget(titulo)
        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        self.barra.setFixedHeight(10)
        v.addWidget(self.barra)
        self.lbl_prog = QLabel("")
        self.lbl_prog.setObjectName("muted")
        v.addWidget(self.lbl_prog)

        zona = QHBoxLayout()
        zona.setSpacing(12)
        self.vis, self.cap = [], []
        for _ in range(1 if modo == "puntuar" else 2):
            col = QVBoxLayout()
            vi = VisorGrande()
            vi.setMinimumHeight(300)
            vi.setToolTip("")
            col.addWidget(vi, 1)
            lb = QLabel("")
            lb.setObjectName("muted")
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lb)
            zona.addLayout(col, 1)
            self.vis.append(vi)
            self.cap.append(lb)
        v.addLayout(zona, 1)

        botones = QHBoxLayout()
        botones.setSpacing(8)
        self._bots = []

        def boton(texto, fn, primario=False):
            b = BotonAnimado(texto, primario=primario)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.clicked.connect(fn)
            botones.addWidget(b)
            return b

        if modo == "puntuar":
            botones.addStretch()
            for k in range(1, 6):
                self._bots.append(boton("★" * k + f"  {k}", lambda _=False, k=k: self._punto(k)))
            botones.addStretch()
        else:
            botones.addStretch()
            self._bots.append(boton("◀  Gana esta", lambda: self._elegir(True)))
            self._bots.append(boton("No sé", lambda: self._elegir(None)))
            self._bots.append(boton("Gana esta  ▶", lambda: self._elegir(False)))
            botones.addStretch()
        v.addLayout(botones)

        pie = QHBoxLayout()
        self.b_atras = boton("↩ Atrás", self._atras)
        pie.addWidget(self.b_atras)
        botones.removeWidget(self.b_atras)
        pie.addStretch()
        b_c = BotonAnimado("Cancelar")
        b_c.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        b_c.clicked.connect(self.reject)
        b_ok = BotonAnimado("Guardar calificaciones" if self.calificar else "Aplicar ranking",
                            primario=True)
        b_ok.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        b_ok.clicked.connect(self._aplicar)
        pie.addWidget(b_c)
        pie.addWidget(b_ok)
        v.addLayout(pie)

        n = len(items)
        if modo == "puntuar":
            self.i = 0
            self.notas = ({i["id"]: i["estrellas"] for i in items if i.get("estrellas")}
                          if self.calificar else {})
            self.barra.setRange(0, max(1, n))
            self._mostrar_punt()
        else:
            ids = [it["id"] for it in items]
            self.base = ids[:-ultimas] if ultimas else []
            self.pend = ids[-ultimas:] if ultimas else ids[:]
            random.shuffle(self.pend)
            if not self.base and self.pend:
                self.base = [self.pend.pop(0)]
            self.x = None
            self.lo = self.hi = self.hechos = 0
            self.hist = []
            tot, tam = 0, len(self.base)
            for _ in self.pend:                    # duelos estimados (peor caso)
                tot += ceil(log2(tam + 1)) if tam else 0
                tam += 1
            self.total = tot
            self.barra.setRange(0, max(1, tot))
            self._nuevo_x()

    # ---------------- puntuar
    def _mostrar_punt(self):
        n = len(self.items)
        self.barra.setValue(min(self.i, n))
        if self.i >= n:
            self.vis[0].poner("")
            self.cap[0].setText("")
            self.lbl_prog.setText("¡Listo!")
            for b in self._bots:
                b.setEnabled(False)
            return
        it = self.items[self.i]
        self.vis[0].poner(it["ruta"])
        self.cap[0].setText(it["sub"])
        nota = self.notas.get(it["id"])
        self.lbl_prog.setText(f"Captura {self.i + 1} de {n}"
                              + (f"  ·  tu nota: {'★' * nota}" if nota else ""))
        for b in self._bots:
            b.setEnabled(True)

    def _punto(self, k):
        if self.i < len(self.items):
            self.notas[self.items[self.i]["id"]] = k
            self.i += 1
            self._mostrar_punt()

    # ---------------- duelos
    def _nuevo_x(self):
        if not self.pend:
            self.x = None
            self._fin_duelos()
            return
        self.x = self.pend.pop(0)
        self.lo, self.hi = 0, len(self.base)
        if self.lo >= self.hi:
            self.base.insert(0, self.x)
            self._nuevo_x()
            return
        self._mostrar_duelo()

    def _mostrar_duelo(self):
        mid = (self.lo + self.hi) // 2
        self._x_izq = random.random() < 0.5
        a, b = self.x, self.base[mid]
        izq, der = (a, b) if self._x_izq else (b, a)
        for vi, lb, cid in ((self.vis[0], self.cap[0], izq), (self.vis[1], self.cap[1], der)):
            it = self.por_id[cid]
            vi.poner(it["ruta"])
            lb.setText(it["sub"])
        self.barra.setValue(min(self.hechos, self.total))
        restan = len(self.pend)
        self.lbl_prog.setText(f"Duelo {self.hechos + 1}  ·  {restan} captura"
                              f"{'' if restan == 1 else 's'} más por colocar después de esta")
        for b in self._bots:
            b.setEnabled(True)

    def _fin_duelos(self):
        for vi in self.vis:
            vi.poner("")
        for lb in self.cap:
            lb.setText("")
        self.barra.setValue(self.barra.maximum())
        self.lbl_prog.setText("¡Listo!")
        for b in self._bots:
            b.setEnabled(False)

    def _elegir(self, izquierda):
        """izquierda: True = gana la de la izquierda · False = la de la derecha · None = no sé."""
        if self.x is None:
            return
        self.hist.append((list(self.base), list(self.pend), self.x, self.lo, self.hi,
                          self.hechos, len(self.log)))
        mid = (self.lo + self.hi) // 2
        gana_x = None if izquierda is None else (izquierda == self._x_izq)
        if gana_x is not None:
            rival = self.base[mid]
            self.log.append((self.x, rival) if gana_x else (rival, self.x))
        if gana_x:
            self.hi = mid
        else:
            self.lo = mid + 1
        self.hechos += 1
        if self.lo >= self.hi:
            self.base.insert(self.lo, self.x)
            self._nuevo_x()
        else:
            self._mostrar_duelo()

    # ---------------- común
    def _atras(self):
        if self.modo == "puntuar":
            if self.i > 0:
                self.i -= 1
                self._mostrar_punt()
            return
        if self.hist:
            (self.base, self.pend, self.x, self.lo, self.hi,
             self.hechos, nlog) = self.hist.pop()
            del self.log[nlog:]
            self.base, self.pend = list(self.base), list(self.pend)
            self._mostrar_duelo()

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key.Key_Backspace:
            self._atras()
        elif self.modo == "puntuar":
            if Qt.Key.Key_1 <= k <= Qt.Key.Key_5:
                self._punto(k - Qt.Key.Key_0)
            elif k in (Qt.Key.Key_Space, Qt.Key.Key_Right):
                if self.i < len(self.items):
                    self.i += 1
                    self._mostrar_punt()
            elif k == Qt.Key.Key_Left:
                self._atras()
            else:
                super().keyPressEvent(e)
        else:
            if k == Qt.Key.Key_Left:
                self._elegir(True)
            elif k == Qt.Key.Key_Right:
                self._elegir(False)
            elif k == Qt.Key.Key_Down:
                self._elegir(None)
            else:
                super().keyPressEvent(e)

    def _aplicar(self):
        if self.modo == "puntuar" and self.calificar:
            self.resultado = [i["id"] for i in self.items]
        elif self.modo == "puntuar":
            orden = sorted(range(len(self.items)),
                           key=lambda ix: (-self.notas.get(self.items[ix]["id"], 3), ix))
            self.resultado = [self.items[ix]["id"] for ix in orden]
        else:
            b = list(self.base)
            if self.x is not None:                  # duelo a medias: se queda donde va
                b.insert(self.lo, self.x)
            self.resultado = b + list(self.pend)
        self.accept()


# ======================================================================
# SÚPER DUELO de heroínas: criterios + CGs al azar + avisos en rojo
# ======================================================================

CRITERIOS_DUELO = (
    ("historia", "📖", "Mejor historia"), ("final", "🏁", "Mejor final"),
    ("personalidad", "💖", "Mejor personalidad"), ("diseno", "🎨", "Mejor diseño"),
    ("voz", "🎙", "Mejor voz"), ("romance", "💞", "Mejor romance"),
)

# Etapas del versus: (clave, icono, nombre, pregunta). Primero los CGs, luego los criterios.
ETAPAS_VERSUS = (
    ("cg_fav", "⭐", "CG favoritos", "¿Quién tiene los mejores CG favoritos?"),
    ("cg_normal", "🖼", "CG normal", "¿Quién tiene el mejor CG normal?"),
    ("cg_h", "🔞", "CG H", "¿Quién tiene el mejor CG H?"),
    ("historia", "📖", "Mejor historia", "¿Quién tiene la mejor historia?"),
    ("final", "🏁", "Mejor final", "¿Quién tiene el mejor final?"),
    ("personalidad", "💖", "Mejor personalidad", "¿Quién tiene la mejor personalidad?"),
    ("diseno", "🎨", "Mejor diseño", "¿Quién tiene el mejor diseño?"),
    ("voz", "🎙", "Mejor voz", "¿Quién tiene la mejor voz?"),
    ("romance", "💞", "Mejor romance", "¿Quién tiene el mejor romance?"),
)
DESEMPATE = ("desempate", "⚖", "Desempate", "Van empatadas: ¿quién gana el versus?")
ETAPA_COLOR = {"cg_fav": "#ffc857", "cg_normal": "#4fc3f7", "cg_h": "#ff6b8b",
               "historia": "#7aa2ff", "final": "#ff9a62", "personalidad": "#ff7eb6",
               "diseno": "#b388ff", "voz": "#4dd0e1", "romance": "#ff5d8f"}
CG_ETAPA = {"cg_fav": ("fav", "⭐", "CG favoritos", "#ffc857"),
            "cg_normal": ("normal", "🖼", "CG normal", CAT_COLOR["CG normal"]),
            "cg_h": ("h", "🔞", "CG H", CAT_COLOR["CG H"])}


def generar_pares(ids, hechos, solo_con=None):
    """Todos contra todos: cada pareja UNA sola vez, sin repetir las ya jugadas, y ordenadas para
    que la misma heroína no pelee dos veces seguidas. solo_con: limita a las parejas donde
    participa alguna de esas heroínas (para meter solo las nuevas)."""
    hechos = {frozenset(h) for h in hechos}
    sc = set(solo_con) if solo_con else None
    pend = [(a, b) for i, a in enumerate(ids) for b in ids[i + 1:]
            if frozenset((a, b)) not in hechos and (sc is None or a in sc or b in sc)]
    random.shuffle(pend)
    orden, ultimo = [], set()
    while pend:
        k = next((i for i, par in enumerate(pend) if not (ultimo & set(par))), 0)
        par = pend.pop(k)
        orden.append(par)
        ultimo = set(par)
    return orden


def combates_por_heroina(n):
    """Cuántos combates juega cada heroína en el torneo de «heroínas de heroínas», en vez de
    pelear contra todas: pocas heroínas = todas contra todas; con muchas, ~log2(n)+1."""
    if n <= 6:
        return max(1, n - 1)
    return min(n - 1, ceil(log2(n)) + 1)


def generar_ronda_suiza(ids, resultados, objetivo, solo_con=None):
    """Una ronda de torneo SUIZO: cada heroína pelea a lo sumo una vez, contra alguien con
    victorias parecidas y a quien aún no se haya enfrentado. Se repite hasta que todas llegan a
    `objetivo` combates. Con n heroínas hace ~n·objetivo/2 combates (todos contra todos haría
    n·(n-1)/2). solo_con: solo las nuevas buscan combates (pueden pelear contra cualquiera).
    Devuelve [(a, b), ...]; vacío cuando ya no hay rivales nuevos o todas llegaron al objetivo."""
    juegos = {i: 0 for i in ids}
    vict = dict(juegos)
    vistas = set()
    for g, p, _et in resultados:
        vistas.add(frozenset((g, p)))
        if g in juegos:
            juegos[g] += 1
            vict[g] += 1
        if p in juegos:
            juegos[p] += 1
    sc = set(solo_con) if solo_con else None
    quieren = [i for i in ids if juegos[i] < objetivo and (sc is None or i in sc)]
    rivales = list(ids) if sc is not None else quieren
    usados, pares = set(), []
    # los que menos han jugado eligen primero: así nadie se queda sin rival
    for a in sorted(quieren, key=lambda i: (juegos[i], random.random())):
        if a in usados:
            continue
        cand = [b for b in rivales if b != a and b not in usados
                and frozenset((a, b)) not in vistas]
        if not cand:
            continue
        b = min(cand, key=lambda b: (abs(vict[a] - vict[b]), abs(juegos[a] - juegos[b]),
                                     random.random()))
        usados.update((a, b))
        pares.append((a, b))
    random.shuffle(pares)
    return pares


def clasificar(ids, resultados):
    """resultados: [(ganadora, perdedora, {etapa: id_ganadora_o_0})].
    El orden lo decide SOLO la victoria total: cada versus ganado vale 1 victoria (da igual que
    se gane 5-2 o 6-3 en etapas). Con las mismas victorias se respeta el orden que ya tenías.
    Devuelve (orden, victorias, derrotas, etapas_ganadas); las etapas solo se informan."""
    v = {i: 0 for i in ids}
    d = dict(v)
    e = dict(v)
    for g, p, et in resultados:
        if g in v:
            v[g] += 1
        if p in d:
            d[p] += 1
        for w in (et or {}).values():
            if w in e:
                e[w] += 1
    pos = {i: k for k, i in enumerate(ids)}
    return sorted(ids, key=lambda i: (-v[i], pos[i])), v, d, e

# ======================================================================
# TORNEO DE «HEROÍNAS DE HEROÍNAS» (por temporadas, eliminación directa)
# ======================================================================

def _tamanos_llaves(n, sin_trios=False):
    """Tamaño de cada llave de una ronda con n participantes: duelos de 2 y, si n es impar,
    UNA llave de 3 (1 vs 1 vs 1) en un lugar al azar.
    sin_trios (modo 3 vs 3): si n es impar, en vez del trío un equipo pasa directo (llave de 1)."""
    if sin_trios:
        if n == 1:
            return [1]
        tam = [2] * (n // 2)
        if n % 2:
            tam.insert(random.randint(0, len(tam)), 1)
        return tam
    if n == 3:
        return [3]
    if n % 2 == 0:
        return [2] * (n // 2)
    tam = [2] * ((n - 3) // 2)
    tam.insert(random.randint(0, len(tam)), 3)
    return tam


def _llave_nueva(ids, src):
    return {"ids": list(ids), "src": list(src), "gan": 0, "orden": [], "pts": {}, "etapas": {}}


def crear_cuadro(ids, sin_trios=False):
    """Sorteo completo del torneo. Devuelve las rondas: cada ronda es una lista de llaves
    {ids, src, gan, orden, pts, etapas}. En la ronda 1 las heroínas ya están emparejadas al
    azar; en las siguientes los huecos (id 0) se llenan con las ganadoras de las llaves `src`."""
    ids = list(ids)
    random.shuffle(ids)
    rondas, pos, r1 = [], 0, []
    for t in _tamanos_llaves(len(ids), sin_trios):
        r1.append(_llave_nueva(ids[pos:pos + t], []))
        pos += t
    rondas.append(r1)
    while len(rondas[-1]) > 1:
        m, pos, nueva = len(rondas[-1]), 0, []
        for t in _tamanos_llaves(m, sin_trios):
            nueva.append(_llave_nueva([0] * t, range(pos, pos + t)))
            pos += t
        rondas.append(nueva)
    for k, ll in enumerate(rondas[0]):                 # pase directo de la 1.ª ronda
        if len(ll["ids"]) == 1:
            registrar_llave(rondas, 0, k, ll["ids"][0], ll["ids"], {}, {})
    return rondas


def nombre_ronda(i, rondas, corto=False):
    """Nombre de la ronda i (0 = primera) según cuántos duelos tiene."""
    m = len(rondas[i])
    if m == 1:
        return "Final"
    if m == 2:
        return "Semis" if corto else "Semifinales"
    if m <= 4:
        return "Cuartos" if corto else "Cuartos de final"
    if m <= 8:
        return "Octavos" if corto else "Octavos de final"
    if m <= 16:
        return "16avos" if corto else "Dieciseisavos de final"
    return f"Ronda {i + 1}"


def llave_jugable(ll):
    return not ll["gan"] and all(ll["ids"])


def llaves_pendientes(rondas):
    """[(ronda, llave)] listas para jugarse, en orden."""
    return [(r, k) for r, ronda in enumerate(rondas) for k, ll in enumerate(ronda)
            if llave_jugable(ll)]


def registrar_llave(rondas, r, k, gan, orden, pts, etapas):
    """Guarda el resultado de una llave y mete a la ganadora en la ronda siguiente."""
    ll = rondas[r][k]
    ll["gan"], ll["orden"], ll["pts"], ll["etapas"] = gan, list(orden), dict(pts), dict(etapas)
    if r + 1 < len(rondas):
        for k2, sig in enumerate(rondas[r + 1]):
            if k in sig["src"]:
                sig["ids"][sig["src"].index(k)] = gan
                if len(sig["ids"]) == 1 and not sig["gan"]:      # pase directo: avanza sola
                    registrar_llave(rondas, r + 1, k2, gan, [gan], {}, {})


def torneo_terminado(rondas):
    return bool(rondas and rondas[-1][0]["gan"])


def jugadas_y_total(rondas):
    tot = sum(1 for r in rondas for ll in r if len(ll["ids"]) > 1)      # sin pases directos
    return sum(1 for r in rondas for ll in r if ll["gan"] and len(ll["ids"]) > 1), tot


def ronda_actual(rondas):
    """Índice de la primera ronda con llaves sin jugar (o la última si ya terminó)."""
    for r, ronda in enumerate(rondas):
        if any(not ll["gan"] for ll in ronda):
            return r
    return len(rondas) - 1


def eliminadas(rondas):
    """{id: (índice_de_ronda, id_de_la_ganadora_de_esa_llave)} de quienes ya cayeron."""
    out = {}
    for r, ronda in enumerate(rondas):
        for ll in ronda:
            if ll["gan"]:
                for i in ll["ids"]:
                    if i != ll["gan"]:
                        out[i] = (r, ll["gan"])
    return out


def rondas_ganadas(rondas):
    """{id: [índices de ronda que ganó]}"""
    out = {}
    for r, ronda in enumerate(rondas):
        for ll in ronda:
            if ll["gan"]:
                out.setdefault(ll["gan"], []).append(r)
    return out


def podio(rondas):
    """{1: [ids], 2: [ids], 3: [ids]} o None si el torneo no ha terminado.
    1.º = campeona; 2.º = a quien venció en la final (si la final es de 3, la 2.ª por puntos);
    3.º = 3.ª de la final (llave de 3) o las que cayeron en semifinales (puesto compartido)."""
    if not torneo_terminado(rondas):
        return None
    final = rondas[-1][0]
    orden = [final["gan"]] + [i for i in final.get("orden", []) if i != final["gan"]]
    orden += [i for i in final["ids"] if i not in orden]
    if len(final["ids"]) == 3:
        return {1: [orden[0]], 2: [orden[1]], 3: [orden[2]]}
    bronce = []
    if len(rondas) >= 2:
        for ll in rondas[-2]:
            bronce += [i for i in ll["ids"] if i != ll["gan"]]
    return {1: [orden[0]], 2: [orden[1]], 3: bronce}


def orden_final(rondas, nombres=None):
    """Todas las participantes de mejor a peor: campeona, subcampeona, y después por la
    ronda a la que llegaron y los puntos (etapas) ganados."""
    nombres = nombres or {}
    elim, pts = eliminadas(rondas), {}
    for ronda in rondas:
        for ll in ronda:
            for i, p in (ll.get("pts") or {}).items():
                pts[int(i)] = pts.get(int(i), 0) + p
    todas = [i for ll in rondas[0] for i in ll["ids"]]
    pod = podio(rondas)
    fijas = []
    if pod:
        fijas = [i for k in (1, 2) for i in pod[k]]
    resto = [i for i in todas if i not in fijas]
    resto.sort(key=lambda i: (-(elim[i][0] if i in elim else 99), -pts.get(i, 0),
                              str(nombres.get(i, "")).casefold()))
    return fijas + resto



# ======================================================================
# MODALIDAD 3 VS 3 (equipos de 3 heroínas; el cuadro usa «equipos» con id negativo)
# ======================================================================
VIDAS_CAPITANA, VIDAS_NORMAL = 10, 9


def es_equipos(jug):
    """True si la temporada es 3 vs 3 (sus participantes del cuadro son equipos)."""
    return any(isinstance(v, dict) and v.get("miembros") for v in (jug or {}).values())


def b3_crear(eq, jug, previas=None):
    """Estado de un enfrentamiento entre dos equipos. Orden de batalla al azar; la capitana de
    cada equipo (ya sorteada al formar el equipo) empieza con 10 corazones y las demás con 9.
    previas {str(heroína): corazones}: lo que traen de la ronda anterior. Las que tienen 0 están
    fuera (no pelean) y las demás conservan sus corazones."""
    previas = previas or {}
    orden, vidas, caps, miem = {}, {}, {}, {}
    for t in eq:
        e = jug[str(t)]
        miem[str(t)], caps[str(t)] = list(e["miembros"]), e.get("cap")
        m = [h for h in e["miembros"] if previas.get(str(h), 1) > 0]
        random.shuffle(m)
        orden[str(t)] = m
        for h in m:
            vidas[str(h)] = previas.get(str(h)) or (
                VIDAS_CAPITANA if h == e.get("cap") else VIDAS_NORMAL)
    return {"eq": list(eq), "orden": orden, "vidas": vidas, "usados": [], "hist": [], "fin": 0,
            "caps": caps, "miembros": miem, "sig": {}, "recupera": 0,
            "actual": [orden[str(eq[0])][0], orden[str(eq[1])][0]]}


def b3_cierre(b3, g):
    """El equipo g ganó el duelo entero: sus vivas conservan sus corazones, las caídas siguen
    fuera y UNA de las vivas (al azar) recupera todos sus corazones para la ronda siguiente.
    Si de las 3 solo queda una viva, esa última heroína NO se cura (b3['sola'])."""
    b3["fin"], b3["actual"] = g, None
    sig = {str(h): b3["vidas"].get(str(h), 0)
           for h in (b3.get("miembros") or {}).get(str(g), b3["orden"][str(g)])}
    vivas = b3_vivas(b3, g)
    b3["sola"] = 0
    if len(vivas) >= 2:          # quedan 2 o 3 vivas: una al azar recupera todos sus corazones
        h = random.choice(vivas)
        cap = (b3.get("caps") or {}).get(str(g))
        sig[str(h)] = VIDAS_CAPITANA if h == cap else VIDAS_NORMAL
    elif len(vivas) == 1:        # solo queda UNA de las 3: ya no puede curarse
        h, b3["sola"] = 0, vivas[0]
    else:                        # ganó por desempate con todas caídas: la última en caer sigue con 1 ❤
        ult = b3["hist"][-1]
        h = ult["a"] if ult["a"] in b3["orden"][str(g)] else ult["b"]
        sig[str(h)], b3["sola"] = 1, h
        h = 0
    b3["sig"], b3["recupera"] = sig, h
    return b3


def b3_vivas(b3, t):
    return [h for h in b3["orden"][str(t)] if b3["vidas"][str(h)] > 0]


def b3_equipo_de(b3, h):
    return next(t for t in b3["eq"] if h in b3["orden"][str(t)])


def b3_aplicar(b3, res):
    """Aplica un versus terminado. res = {a, b, vidas:[va, vb], etapas}. Quien llega a 0 muere y
    entra la siguiente de su equipo contra la que sigue viva (conserva sus corazones). Si nadie
    muere, se sortea otro versus entre las vivas SIN repetir parejas. Si un equipo se queda sin
    heroínas vivas, el otro gana."""
    a, b = res["a"], res["b"]
    b3["vidas"][str(a)], b3["vidas"][str(b)] = int(res["vidas"][0]), int(res["vidas"][1])
    b3["usados"].append(sorted([a, b]))
    b3["hist"].append({"a": a, "b": b, "vidas": [int(x) for x in res["vidas"]],
                       "etapas": dict(res.get("etapas") or {}),
                       "evento": res.get("evento") or None,
                       "v0": [int(x) for x in res["v0"]] if res.get("v0") else None})
    ta, tb = b3["eq"]
    va, vb = b3_vivas(b3, ta), b3_vivas(b3, tb)
    if not va or not vb:
        if va:
            g = ta
        elif vb:
            g = tb
        else:                    # las últimas de ambos equipos caen a la vez: más etapas ganadas
            cuenta = {ta: 0, tb: 0}
            for h in b3["hist"]:
                for w in h["etapas"].values():
                    if w:
                        cuenta[b3_equipo_de(b3, w)] += 1
            g = ta if cuenta[ta] > cuenta[tb] else tb if cuenta[tb] > cuenta[ta] else random.choice((ta, tb))
        return b3_cierre(b3, g)
    vistas = {x for h in b3["hist"] for x in (h["a"], h["b"])}

    def reemplazo(lista):          # la siguiente del grupo que aún no ha peleado (si no, la 1.ª viva)
        return ([x for x in lista if x not in vistas] or lista)[0]
    muerta_a, muerta_b = b3["vidas"][str(a)] <= 0, b3["vidas"][str(b)] <= 0
    if muerta_a or muerta_b:
        na = reemplazo(va) if muerta_a else a
        nb = reemplazo(vb) if muerta_b else b
    else:
        usados = {tuple(p) for p in b3["usados"]}
        cand = [(x, y) for x in va for y in vb if tuple(sorted([x, y])) not in usados]
        if not cand:               # ya se jugaron todas las parejas posibles: se vuelven a permitir
            b3["usados"] = []
            cand = [(x, y) for x in va for y in vb]
        na, nb = random.choice(cand)
    b3["actual"] = [na, nb]
    return b3


# ----------------------------------------------------------------------
# EVENTOS ALEATORIOS DEL 3 VS 3
# En cada versus hay un PROB_EVENTO_3V3 de que ocurra UN evento (los demás versus son normales).
# "lado": True = el evento beneficia/castiga a una de las dos peleadoras (se sortea cuál; en el
# texto {h} es su nombre y {o} la rival). "azar": (min, max) = el evento sortea un número {x}.
#
# Cada evento es una tabla de REGLAS que entiende b3_vidas_versus (todas opcionales):
#  AL EMPEZAR  fijar_ambos / fijar_lado / fijar_otro (cambia los ❤ a ese valor; "x" = el sorteado)
#              ini_ambos / ini_lado / ini_otro (suma o resta ❤; "x" / "-x" = sorteado)
#              intercambio · nivelar · transferir=n · robo=n · regalo=n · mitad_lado · doble_lado
#  POR ETAPA   dano · dano_empate · dano_lado_gana/_pierde · dano_otro_gana/_pierde
#              cura_gana · cura_lado_gana · cura_empate · vampiro_total · rebote · rebote_lado
#              invertido · escudo_lado=n · escudo_ambos=n · racha · remontada · lider_pierde_mas
#              mult=(desde, hasta, x) · empate_swap · piso_lado · piso_ambos · inmortal_hasta
#              swap_cada=n · tras=[(n_etapas, accion, valor)]  con accion: swap, nivelar,
#              fijar_lado, suma_lado, suma_otro, suma_ambos
# Para añadir un evento nuevo basta una línea más con _ev(...).
# ----------------------------------------------------------------------
PROB_EVENTO_3V3 = 0.30
EVENTOS_3V3 = {}


def _ev(clave, ico, nombre, color, desc, lado=False, **regla):
    EVENTOS_3V3[clave] = dict(ico=ico, nombre=nombre, lado=lado, color=color, desc=desc, **regla)


# --- los clásicos
_ev("tormenta", "⛈", "Tormenta", "#6ea8fe",
    "Cada etapa perdida resta 3 ❤ (en vez de 1) y los empates también restan 3.",
    dano=3, dano_empate=3)
_ev("angel", "😇", "Ángel guardián", "#ffe08a",
    "{h} está protegida: aunque pierda todos sus corazones, se queda con 1 ❤.",
    lado=True, piso_lado=1)
_ev("vampiro", "🦇", "Sed de sangre", "#d46bff",
    "Quien gana una etapa recupera 1 ❤ (hasta un máximo de 10).", cura_gana=1)
_ev("furia", "🔥", "Furia", "#ff7a4d",
    "{h} está furiosa: cada etapa que gana quita 2 ❤ en vez de 1.",
    lado=True, dano_lado_gana=2)
_ev("escudo", "🛡", "Escudo", "#7bd88f",
    "{h} lleva escudo: la primera etapa que pierda no le quita ningún ❤.",
    lado=True, escudo_lado=1)
_ev("maldicion", "💀", "Maldición", "#a06bff",
    "{h} empieza este versus maldita: −3 ❤ (le queda al menos 1).", lado=True, ini_lado=-3)
_ev("bendicion", "✨", "Bendición", "#ffd45e",
    "{h} empieza este versus bendecida: +3 ❤.", lado=True, ini_lado=3)
_ev("tregua", "🕊", "Tregua", "#8be0ff",
    "Los empates no restan ningún ❤ a nadie.", dano_empate=0)
_ev("doble", "🎲", "Doble o nada", "#ff6b8b",
    "Cada etapa perdida resta 2 ❤ en vez de 1.", dano=2)

# --- CAMBIO E INTERCAMBIO DE VIDA
_ev("intercambio", "🔄", "Intercambio de vidas", "#4dd0e1",
    "Las dos se cambian los corazones al empezar.", intercambio=True)
_ev("trueque_tarde", "⏳", "Trueque tardío", "#26c6da",
    "Tras 3 etapas, las dos intercambian sus ❤.", tras=[(3, "swap", 0)])
_ev("torbellino", "🌀", "Torbellino", "#5c9dff",
    "Cada 2 etapas, las dos intercambian sus ❤.", swap_cada=2)
_ev("balanza", "⚖", "Balanza", "#b0bec5",
    "Las dos igualan sus ❤ (promedio) al empezar.", nivelar=True)
_ev("balanza_tarde", "🎚", "Balanza tardía", "#90a4ae",
    "Tras 4 etapas, las dos igualan sus ❤.", tras=[(4, "nivelar", 0)])
_ev("ruleta", "🎰", "Ruleta de vidas", "#ff8a65",
    "{h} gira la ruleta: sus ❤ pasan a ser {x}.", lado=True, azar=(1, 10), fijar_lado="x")
_ev("loteria", "🎟", "Lotería", "#ffb74d",
    "{o} queda con {x} ❤ por sorteo.", lado=True, azar=(3, 8), fijar_otro="x")
_ev("ladron", "🥷", "Ladrona de vidas", "#78909c",
    "{h} le roba 2 ❤ a {o}.", lado=True, robo=2)
_ev("saqueo", "🏴‍☠️", "Saqueo", "#8d6e63",
    "{h} le roba 3 ❤ a {o} (le deja al menos 1).", lado=True, robo=3)
_ev("generosa", "🎁", "Generosa", "#f48fb1",
    "{h} le regala 2 ❤ a {o}.", lado=True, regalo=2)
_ev("robin", "🏹", "Robin Hood", "#66bb6a",
    "La que tiene más ❤ le pasa 2 a la que tiene menos.", transferir=2)
_ev("mitad", "✂", "Cortada a la mitad", "#ef9a9a",
    "{h} pierde la mitad de sus ❤ (mín. 1).", lado=True, mitad_lado=True)
_ev("doblar", "💰", "Corazones dobles", "#ffd54f",
    "{h} duplica sus ❤ (hasta 12).", lado=True, doble_lado=True)
_ev("reinicio5", "🎯", "Reinicio a 5", "#9fa8da",
    "Las dos empiezan con 5 ❤.", fijar_ambos=5)
_ev("muerte_subita", "☠", "Muerte súbita", "#e53935",
    "Las dos empiezan con 1 ❤: un error y caes.", fijar_ambos=1)
_ev("vida_llena", "💖", "Vida llena", "#ff80ab",
    "Las dos empiezan con 10 ❤.", fijar_ambos=10)
_ev("ultimo_aliento", "🩸", "Último aliento", "#c62828",
    "{h} se queda con solo 1 ❤.", lado=True, fijar_lado=1)
_ev("renacer", "🌅", "Renacer", "#ffca28",
    "{h} queda con 10 ❤ exactos.", lado=True, fijar_lado=10)
_ev("dado_bueno", "🎲", "Dado de la suerte", "#81c784",
    "{h} gana {x} ❤ por el dado.", lado=True, azar=(1, 4), ini_lado="x")
_ev("dado_malo", "🎲", "Dado maldito", "#b39ddb",
    "{h} pierde {x} ❤ (mín. 1).", lado=True, azar=(1, 4), ini_lado="-x")
_ev("lluvia", "🌧", "Lluvia de corazones", "#80deea",
    "Las dos ganan +2 ❤.", ini_ambos=2)
_ev("plaga", "☣", "Plaga", "#9ccc65",
    "Las dos pierden 2 ❤ (mín. 1).", ini_ambos=-2)
_ev("mal_de_ojo", "🧿", "Mal de ojo", "#5c6bc0",
    "{o} empieza con −2 ❤ (mín. 1).", lado=True, ini_otro=-2)
_ev("giro", "🎭", "Giro del destino", "#ba68c8",
    "Tras 4 etapas, {h} queda con 5 ❤ (si sigue viva).", lado=True, tras=[(4, "fijar_lado", 5)])
_ev("gota_final", "💧", "Gota final", "#4fc3f7",
    "Tras 5 etapas, {h} gana 3 ❤.", lado=True, tras=[(5, "suma_lado", 3)])
_ev("meteorito", "☄", "Meteorito", "#ff7043",
    "Tras 4 etapas, las dos pierden 2 ❤ (mín. 1).", tras=[(4, "suma_ambos", -2)])
_ev("eclipse", "🌑", "Eclipse", "#7e57c2",
    "Tras 5 etapas, {h} pierde 2 ❤ (mín. 1).", lado=True, tras=[(5, "suma_lado", -2)])
_ev("estrellas", "🌠", "Lluvia de estrellas", "#ffee58",
    "Tras 3 etapas, las dos ganan 2 ❤.", tras=[(3, "suma_ambos", 2)])

# --- REGLAS DE DAÑO Y CURACIÓN
_ev("criticos", "💥", "Golpes críticos", "#ff5252",
    "Las 3 primeras etapas quitan el doble de ❤.", mult=(0, 3, 2))
_ev("final_explosiva", "🏁", "Final explosiva", "#ff9a62",
    "Desde la etapa 7, todo quita el doble de ❤.", mult=(6, 99, 2))
_ev("calma", "🍃", "Calma inicial", "#a5d6a7",
    "Las 3 primeras etapas no quitan ❤.", mult=(0, 3, 0))
_ev("fragil", "🥀", "Frágil", "#f06292",
    "{h} pierde 2 ❤ por cada etapa perdida.", lado=True, dano_lado_pierde=2)
_ev("armadura", "🧱", "Armadura", "#a1887f",
    "{h} ignora sus 2 primeras etapas perdidas.", lado=True, escudo_lado=2)
_ev("escudos_dobles", "🛡", "Escudos para todas", "#69f0ae",
    "Cada una ignora su primera etapa perdida.", escudo_ambos=1)
_ev("golpe_bajo", "🥊", "Golpe bajo", "#ef5350",
    "{o} pierde 2 ❤ por cada etapa perdida.", lado=True, dano_otro_pierde=2)
_ev("doble_filo", "⚔", "Doble filo", "#cfd8dc",
    "Quien gana una etapa también pierde 1 ❤ (mín. 1).", rebote=1)
_ev("mundo_reves", "🙃", "Mundo al revés", "#ce93d8",
    "Ganar una etapa cuesta 1 ❤ y perderla no cuesta nada.", invertido=True)
_ev("vampiresa", "🧛", "Vampiresa", "#ab47bc",
    "Quien gana una etapa recupera tantos ❤ como quita.", vampiro_total=True)
_ev("racha", "🔥", "Racha ganadora", "#ff8f00",
    "Ganar 2 etapas seguidas quita +1 ❤ extra.", racha=1)
_ev("remontada", "🚀", "Remontada", "#42a5f5",
    "La que va con menos ❤ pega +1 extra al ganar una etapa.", remontada=1)
_ev("peso_corona", "👑", "Peso de la corona", "#ffc857",
    "La que va con más ❤ pierde +1 extra al perder una etapa.", lider_pierde_mas=1)
_ev("empate_dulce", "💞", "Empate dulce", "#f8bbd0",
    "Los empates curan 1 ❤ a las dos (en vez de restar).", dano_empate=0, cura_empate=1)
_ev("empate_cosmico", "♾", "Empate cósmico", "#7986cb",
    "En un empate las dos intercambian sus ❤ (sin daño).", dano_empate=0, empate_swap=True)
_ev("empate_letal", "🪦", "Empate letal", "#b71c1c",
    "Los empates restan 4 ❤ a las dos.", dano_empate=4)
_ev("velas", "🕯", "Velas encendidas", "#ffe082",
    "Nadie puede morir en las 4 primeras etapas.", inmortal_hasta=4)
_ev("santuario", "⛪", "Santuario", "#fff9c4",
    "Nadie puede morir en este versus (mín. 1 ❤).", piso_ambos=1)
_ev("viento", "🌬", "Viento a favor", "#b3e5fc",
    "{h} recupera 1 ❤ por cada etapa que gana.", lado=True, cura_lado_gana=1)
_ev("berserker", "🪓", "Berserker", "#d84315",
    "{h} quita 3 ❤ al ganar una etapa, pero se hiere 1.", lado=True,
    dano_lado_gana=3, rebote_lado=1)
_ev("pacifista", "🌸", "Pacifista", "#f48fb1",
    "Las etapas que gana {h} no quitan ❤ y le curan 1.", lado=True,
    dano_lado_gana=0, cura_lado_gana=1)
_ev("kamikaze", "💣", "Kamikaze", "#ff6f00",
    "{h} pierde 3 ❤ por etapa perdida, pero quita 2 al ganar.", lado=True,
    dano_lado_pierde=3, dano_lado_gana=2)
_ev("adrenalina", "💉", "Adrenalina", "#26a69a",
    "{h} no puede bajar de 2 ❤ en este versus.", lado=True, piso_lado=2)
_ev("favorita", "📣", "Favorita del público", "#ffa726",
    "{h} empieza con +2 ❤ y quita 2 al ganar una etapa.", lado=True,
    ini_lado=2, dano_lado_gana=2)
_ev("gafe", "🐈‍⬛", "Gafe", "#757575",
    "{h} empieza con −1 ❤ y pierde 2 por etapa perdida.", lado=True,
    ini_lado=-1, dano_lado_pierde=2)
_ev("fuente", "⛲", "Fuente curativa", "#4dd0e1",
    "Quien gana una etapa recupera 2 ❤.", cura_gana=2)


def b3_sortear_evento(a, b):
    """Con probabilidad PROB_EVENTO_3V3 devuelve {'k': clave, 'h': heroína afectada o 0, 'x': número
    sorteado (solo si el evento lo usa)}; si no, None."""
    if random.random() >= PROB_EVENTO_3V3:
        return None
    k = random.choice(list(EVENTOS_3V3))
    ev = {"k": k, "h": random.choice((a, b)) if EVENTOS_3V3[k]["lado"] else 0}
    if EVENTOS_3V3[k].get("azar"):
        ev["x"] = random.randint(*EVENTOS_3V3[k]["azar"])
    return ev


def b3_dano_empate(k=None):
    """❤ que pierde CADA peleadora cuando una etapa termina en empate."""
    return (EVENTOS_3V3.get(k) or {}).get("dano_empate", 2)


def _b3_num(p, x, ev):
    """Valor de una regla: número fijo o el sorteado ('x' / '-x')."""
    if p in ("x", "-x"):
        if x is None:
            x = (ev.get("azar") or (1, 1))[0]
        return x if p == "x" else -x
    return p


def b3_vidas_versus(v0, votos, k=None, lado=None, x=None):
    """Corazones de las dos peleadoras tras las etapas votadas (en orden).
    v0: [va, vb] al empezar · votos: [-1 empate | 0 gana A | 1 gana B] · k: evento · lado: 0/1
    · x: número sorteado del evento (si lo usa)."""
    v = [int(n) for n in v0]
    ev = EVENTOS_3V3.get(k) or {}
    if ev.get("lado") and lado not in (0, 1):
        ev = {}
    L = lado if ev.get("lado") else None          # peleadora afectada (0/1) o None
    O = None if L is None else 1 - L              # su rival
    R = ev.get

    def num(clave):
        return _b3_num(R(clave), x, ev)

    def suma(i, d):                               # sumar; al restar siempre queda al menos 1
        v[i] = max(1, v[i] + d) if d < 0 else v[i] + d

    def cambiar():                                # intercambio de corazones (solo si las dos viven)
        if v[0] > 0 and v[1] > 0:
            v[0], v[1] = v[1], v[0]

    # ---------- al empezar el versus
    for clave, quienes in (("fijar_ambos", (0, 1)), ("fijar_lado", (L,)), ("fijar_otro", (O,))):
        if R(clave) is not None:
            for i in quienes:
                if i is not None:
                    v[i] = max(1, int(num(clave)))
    if R("intercambio"):
        cambiar()
    if R("nivelar"):
        m = -(-(v[0] + v[1]) // 2)
        v = [m, m]
    if R("transferir") and v[0] != v[1]:
        rico, pobre = (0, 1) if v[0] > v[1] else (1, 0)
        t = min(R("transferir"), (v[rico] - v[pobre]) // 2, v[rico] - 1)
        if t > 0:
            v[rico] -= t
            v[pobre] += t
    if L is not None:
        if R("robo"):
            t = max(0, min(R("robo"), v[O] - 1))
            v[O] -= t
            v[L] += t
        if R("regalo"):
            t = max(0, min(R("regalo"), v[L] - 1))
            v[L] -= t
            v[O] += t
        if R("mitad_lado"):
            v[L] = max(1, -(-v[L] // 2))
        if R("doble_lado"):
            v[L] = max(v[L], min(v[L] * 2, 12))
    if R("ini_ambos"):
        suma(0, num("ini_ambos"))
        suma(1, num("ini_ambos"))
    if L is not None and R("ini_lado"):
        suma(L, num("ini_lado"))
    if L is not None and R("ini_otro"):
        suma(O, num("ini_otro"))

    # ---------- etapa por etapa
    tope = [max(VIDAS_CAPITANA, n) for n in v]
    cupo = [R("escudo_ambos") or 0] * 2           # escudos disponibles de cada una
    if L is not None:
        cupo[L] += R("escudo_lado") or 0
    gastados = [0, 0]
    racha = [0, 0]
    for i, g in enumerate(votos):
        mu = R("mult")
        mult = mu[2] if mu and mu[0] <= i < mu[1] else 1
        if g < 0:                                 # empate
            d = R("dano_empate", 2) * mult
            if R("empate_swap"):
                cambiar()
            for j in (0, 1):
                v[j] = max(0, v[j] - d)
                c = R("cura_empate", 0)
                if c and v[j] > 0:
                    v[j] = max(v[j], min(tope[j], v[j] + c))
            racha = [0, 0]
        else:
            p = 1 - g
            d = R("dano", 1)
            for cond, clave in ((g == L, "dano_lado_gana"), (p == L, "dano_lado_pierde"),
                                (g == O, "dano_otro_gana"), (p == O, "dano_otro_pierde")):
                if cond and R(clave) is not None:
                    d = R(clave)
                    break
            if R("remontada") and v[g] < v[p]:
                d += R("remontada")
            if R("lider_pierde_mas") and v[p] > v[g]:
                d += R("lider_pierde_mas")
            racha[g] += 1
            racha[p] = 0
            if R("racha") and racha[g] >= 2:
                d += R("racha")
            d *= mult
            t = g if R("invertido") else p        # quién recibe el daño
            if d > 0 and gastados[t] < cupo[t]:
                d, gastados[t] = 0, gastados[t] + 1
            cura = (R("cura_gana", 0) + (R("cura_lado_gana", 0) if g == L else 0)
                    + (d if R("vampiro_total") else 0))
            if cura:
                v[g] = max(v[g], min(tope[g], v[g] + cura))
            v[t] = max(0, v[t] - d)
            rb = R("rebote", 0) + (R("rebote_lado", 0) if g == L else 0)
            if rb and not R("invertido") and v[g] > 0:
                v[g] = max(1, v[g] - rb)
        # suelos: nadie baja de cierto número de ❤ (ángel, santuario, velas…)
        suelo = [R("piso_ambos") or 0] * 2
        if i < R("inmortal_hasta", 0):
            suelo = [max(s, 1) for s in suelo]
        if L is not None and R("piso_lado"):
            suelo[L] = max(suelo[L], R("piso_lado"))
        for j in (0, 1):
            if suelo[j]:
                v[j] = max(suelo[j], v[j])
        # cambios de vida a mitad del versus
        for n, accion, val in R("tras", ()):
            if i + 1 == n and v[0] > 0 and v[1] > 0:
                if accion == "swap":
                    cambiar()
                elif accion == "nivelar":
                    m = -(-(v[0] + v[1]) // 2)
                    v = [m, m]
                elif accion == "fijar_lado" and L is not None:
                    v[L] = max(1, val)
                elif accion == "suma_lado" and L is not None:
                    suma(L, val)
                elif accion == "suma_otro" and L is not None:
                    suma(O, val)
                elif accion == "suma_ambos":
                    suma(0, val)
                    suma(1, val)
        if R("swap_cada") and (i + 1) % R("swap_cada") == 0:
            cambiar()
    return v


def b3_resultado(b3):
    """(equipo ganador, [ganador, perdedor], {str(equipo): corazones que le quedan en total})."""
    g = b3["fin"]
    p = next(t for t in b3["eq"] if t != g)
    pts = {str(t): sum(b3["vidas"][str(h)] for h in b3["orden"][str(t)]) for t in b3["eq"]}
    return g, [g, p], pts


def b3_previas(rondas, r, ids):
    """Corazones con que llegan a la ronda r los equipos `ids`: los que dejó su último duelo
    ganado (ya con la recuperación de una heroína). Un pase directo no cambia nada."""
    out = {}
    for t in ids:
        for rr in range(r - 1, -1, -1):
            hit = next((l for l in rondas[rr] if t in l["ids"] and (l.get("b3") or {}).get("fin") == t),
                       None)
            if hit:
                out.update(hit["b3"].get("sig") or {})
                break
    return out


def b3_estadisticas(rondas):
    """{heroína: {ko, vs, etapas: {clave: n}}} sumando todos los versus 3 vs 3 de la temporada.
    ko = rivales que dejó en 0 corazones · vs = versus ganados (por K.O. o, si nadie cayó, por
    más etapas)."""
    st = {}

    def ficha(h):
        return st.setdefault(h, {"ko": 0, "vs": 0, "etapas": {}})
    for ronda in rondas:
        for ll in ronda:
            for h in (ll.get("b3") or {}).get("hist", []):
                a, b = h["a"], h["b"]
                va, vb = h["vidas"]
                cnt = {a: 0, b: 0}
                for c, w in (h.get("etapas") or {}).items():
                    if w in cnt:
                        cnt[w] += 1
                        f = ficha(w)
                        f["etapas"][c] = f["etapas"].get(c, 0) + 1
                ficha(a), ficha(b)
                if vb <= 0 < va:
                    st[a]["ko"] += 1
                    st[a]["vs"] += 1
                elif va <= 0 < vb:
                    st[b]["ko"] += 1
                    st[b]["vs"] += 1
                elif va > 0 and vb > 0 and cnt[a] != cnt[b]:
                    st[a if cnt[a] > cnt[b] else b]["vs"] += 1
    return st


def b3_mvp_duelo(b3):
    """Aporte de cada integrante del equipo ganador en ESTE duelo 3 vs 3 y quién(es) fueron MVP.
    Devuelve ([(heroína, {ko, vs, etapas, vidas})...], [ids MVP]). Puntos = 3 por K.O. + 1 por
    etapa ganada; si hay empate decide más versus ganados y luego más corazones."""
    g = b3["fin"]
    st = b3_estadisticas([[{"b3": b3}]])
    miembros = (b3.get("miembros") or {}).get(str(g)) or b3["orden"][str(g)]
    filas = []
    for h in miembros:
        f = st.get(h, {"ko": 0, "vs": 0, "etapas": {}})
        filas.append((h, {"ko": f["ko"], "vs": f["vs"], "etapas": sum(f["etapas"].values()),
                          "vidas": b3["vidas"].get(str(h), 0)}))
    clave = lambda x: (3 * x[1]["ko"] + x[1]["etapas"], x[1]["vs"], x[1]["vidas"])
    mejor = max((clave(x) for x in filas), default=None)
    mvps = [h for h, d in filas if mejor is not None and clave((h, d)) == mejor]
    return filas, mvps


HONORES_ETAPA = {
    "cg_h": ("🔞", "CG Hentai Master"), "cg_normal": ("🖼", "Reina del CG"),
    "cg_fav": ("⭐", "Maestra de los favoritos"), "historia": ("📖", "Narradora legendaria"),
    "final": ("🏁", "Final perfecto"), "personalidad": ("💖", "Corazón de oro"),
    "diseno": ("🎨", "Diseño de ensueño"), "voz": ("🎙", "Voz de ángel"),
    "romance": ("💞", "Reina del romance"),
}


def honores_equipo(rondas, jug):
    """Menciones honoríficas de las integrantes del equipo campeón:
    [(heroína, [(icono, título, detalle), ...]), ...]. Cada mención va para quien más tiene
    (si hay empate, para todas las empatadas); solo se da si tiene al menos 1."""
    if not torneo_terminado(rondas):
        return []
    camp = rondas[-1][0]["gan"]
    miembros = (jug.get(str(camp)) or {}).get("miembros") or []
    st = b3_estadisticas(rondas)
    vacio = {"ko": 0, "vs": 0, "etapas": {}}
    g = lambda h: st.get(h, vacio)
    tot = lambda h: sum(g(h)["etapas"].values())
    cats = [("⚔", "Batallas más ganadas", lambda h: g(h)["vs"], "{} versus ganados"),
            ("🌟", "MVP", lambda h: 3 * g(h)["ko"] + tot(h), "{} pts (3 por K.O. + 1 por etapa)"),
            ("💀", "Verdugo", lambda h: g(h)["ko"], "{} K.O."),
            ("🏅", "Etapas ganadas", tot, "{} etapas")]
    for clave, (ico, nombre) in HONORES_ETAPA.items():
        cats.append((ico, nombre, lambda h, c=clave: g(h)["etapas"].get(c, 0), "{} etapas"))
    res = {h: [] for h in miembros}
    for ico, nombre, fn, fmt in cats:
        mejor = max((fn(h) for h in miembros), default=0)
        if mejor <= 0:
            continue
        for h in miembros:
            if fn(h) == mejor:
                res[h].append((ico, nombre, fmt.format(mejor)))
    cap = (jug.get(str(camp)) or {}).get("cap")
    return [(h, res[h]) for h in sorted(miembros, key=lambda h: (-len(res[h]), h != cap))]


# ----------------------------------------------------------------------
# ESTADÍSTICAS DETALLADAS Y COMENTARIOS DEL RANKING 3 VS 3
# ----------------------------------------------------------------------
def b3_stats_det(rondas):
    """{heroína: ficha} con TODO lo que hizo en la temporada 3 vs 3 (para los comentarios del
    ranking). Reconstruye cada versus etapa por etapa para saber cuántos ❤ quitó y recibió."""
    st = {}

    def ficha(h):
        return st.setdefault(h, dict(
            vs=0, vg=0, vp=0, ko=0, caidas=0, ronda_caida=None, etapas_g=0, etapas_p=0,
            empates=0, dano=0, recibido=0, eventos=0, ev_propios=[], cats_g={}, cats_p={},
            rachas_g=0, rachas_p=0, perfectos=0, palizas=0, doble_ko=0, ko_caps=0, curadas=0,
            sola=0, vida_final=None, rondas=set(), etapas_final=0, gano_con_1=0, cap_primera=False,
            cur_g=0, cur_p=0))
    caidos_eq = {}
    for r, ronda in enumerate(rondas):
        final = r == len(rondas) - 1
        for ll in ronda:
            b3 = ll.get("b3") or {}
            caps = b3.get("caps") or {}
            if b3.get("fin"):
                if b3.get("recupera"):
                    ficha(b3["recupera"])["curadas"] += 1
                if b3.get("sola"):
                    ficha(b3["sola"])["sola"] += 1
            for e in b3.get("hist", []):
                a, b = e["a"], e["b"]
                va, vb = e["vidas"]
                et = e.get("etapas") or {}
                ev = e.get("evento") or {}
                fa, fb = ficha(a), ficha(b)
                fa["rondas"].add(r)
                fb["rondas"].add(r)
                cnt = {a: 0, b: 0}
                votos = []
                for c, w in et.items():
                    if w in cnt:
                        cnt[w] += 1
                        otro = b if w == a else a
                        votos.append(0 if w == a else 1)
                        for quien, rival in ((w, otro),):
                            F, G = ficha(quien), ficha(rival)
                            F["etapas_g"] += 1
                            F["cats_g"][c] = F["cats_g"].get(c, 0) + 1
                            G["etapas_p"] += 1
                            G["cats_p"][c] = G["cats_p"].get(c, 0) + 1
                            F["cur_g"] += 1
                            G["cur_g"] = 0
                            F["cur_p"] = 0
                            G["cur_p"] += 1
                            F["rachas_g"] = max(F["rachas_g"], F["cur_g"])
                            G["rachas_p"] = max(G["rachas_p"], G["cur_p"])
                        if final:
                            ficha(w)["etapas_final"] += 1
                    else:
                        votos.append(-1)
                        fa["empates"] += 1
                        fb["empates"] += 1
                        for F in (fa, fb):
                            F["cur_g"] = F["cur_p"] = 0
                # ❤ quitados y recibidos (se reconstruye con las reglas del evento)
                v0 = e.get("v0")
                if v0 is not None and votos:
                    k = ev.get("k")
                    lado = (0 if ev.get("h") == a else 1 if ev.get("h") == b else None)
                    prev = b3_vidas_versus(v0, [], k, lado, ev.get("x"))
                    for n, w in enumerate(votos):
                        cur = b3_vidas_versus(v0, votos[:n + 1], k, lado, ev.get("x"))
                        if w >= 0:
                            ficha((a, b)[w])["dano"] += max(0, prev[1 - w] - cur[1 - w])
                        for j, F in enumerate((fa, fb)):
                            F["recibido"] += max(0, prev[j] - cur[j])
                        prev = cur
                else:                                    # partidas viejas: 1 ❤ por etapa ganada
                    fa["dano"] += cnt[a]
                    fb["dano"] += cnt[b]
                    fa["recibido"] += cnt[b]
                    fb["recibido"] += cnt[a]
                if ev.get("k"):
                    fa["eventos"] += 1
                    fb["eventos"] += 1
                    if ev.get("h") in (a, b):
                        ficha(ev["h"])["ev_propios"].append(ev["k"])
                fa["vs"] += 1
                fb["vs"] += 1
                fa["vida_final"], fb["vida_final"] = va, vb
                # quién ganó / perdió el versus
                gan = per = None
                if vb <= 0 < va:
                    gan, per = a, b
                elif va <= 0 < vb:
                    gan, per = b, a
                elif va > 0 and vb > 0 and cnt[a] != cnt[b]:
                    gan, per = (a, b) if cnt[a] > cnt[b] else (b, a)
                elif va <= 0 and vb <= 0:
                    fa["doble_ko"] += 1
                    fb["doble_ko"] += 1
                if gan:
                    ficha(gan)["vg"] += 1
                    ficha(per)["vp"] += 1
                    tot = cnt[a] + cnt[b]
                    if cnt[per] == 0 and cnt[gan] >= 3:
                        ficha(gan)["perfectos"] += 1
                    if cnt[gan] == 0 and tot >= 3:
                        ficha(per)["palizas"] += 1
                if vb <= 0 < va or va <= 0 < vb:
                    k_, muerta = (a, b) if vb <= 0 < va else (b, a)
                    ficha(k_)["ko"] += 1
                    if (va if k_ == a else vb) == 1:
                        ficha(k_)["gano_con_1"] += 1
                    eq_m = b3_equipo_de(b3, muerta)
                    if caps.get(str(eq_m)) == muerta:
                        ficha(k_)["ko_caps"] += 1
                for h_, vv in ((a, va), (b, vb)):
                    if vv <= 0:
                        F = ficha(h_)
                        F["caidas"] += 1
                        F["ronda_caida"] = r
                        eq_h = b3_equipo_de(b3, h_)
                        lista = caidos_eq.setdefault(eq_h, [])
                        if not lista and caps.get(str(eq_h)) == h_:
                            F["cap_primera"] = True
                        lista.append(h_)
    return st


def _pct(a, b):
    return int(round(100.0 * a / b)) if b else 0


def _com_cat(s, clave, ganar=True):
    d = s["cats_g"] if ganar else s["cats_p"]
    return d.get(clave, 0)


FRASE_CAT = {
    "cg_fav": ("⭐", "Sus CG favoritos mandan"), "cg_normal": ("🖼", "Reina del CG normal"),
    "cg_h": ("🔞", "Dominó el CG H"), "historia": ("📖", "Su historia es la mejor"),
    "final": ("🏁", "Sus finales enamoran"), "personalidad": ("💖", "Personalidad ganadora"),
    "diseno": ("🎨", "Diseño que arrasa"), "voz": ("🎙", "Voz de ángel"),
    "romance": ("💞", "Romance puro"),
}
FRASE_DEBIL = {
    "cg_fav": "sus CG favoritos no convencen", "cg_normal": "su CG normal flojea",
    "cg_h": "su CG H se quedó corto", "historia": "su historia no despegó",
    "final": "sus finales no enamoran", "personalidad": "su personalidad no ganó",
    "diseno": "su diseño no alcanzó", "voz": "ni una etapa de voz ganada",
    "romance": "su romance no cuajó",
}
FRASE_EV = {          # comentario especial para eventos concretos (el resto usa uno genérico)
    "angel": "😇 Un ángel guardián la salvó", "maldicion": "💀 La maldijeron… y sobrevivió",
    "bendicion": "✨ La bendijo el destino", "furia": "🔥 Peleó con furia",
    "escudo": "🛡 Se cubrió con un escudo", "ruleta": "🎰 Giró la ruleta de vidas",
    "ladron": "🥷 Robó corazones a su rival", "saqueo": "🏴‍☠️ Saqueó a su rival",
    "generosa": "🎁 Regaló corazones a su rival", "mitad": "✂ Perdió la mitad de sus ❤",
    "doblar": "💰 Duplicó sus corazones", "ultimo_aliento": "🩸 Peleó con 1 ❤ de vida",
    "renacer": "🌅 Renació con 10 ❤", "mal_de_ojo": "🧿 Le echaron mal de ojo",
    "berserker": "🪓 Peleó como berserker", "kamikaze": "💣 Fue kamikaze",
    "pacifista": "🌸 Fue pacifista por un versus", "gafe": "🐈‍⬛ Le tocó el gafe",
}


def _comentarios_def():
    """Reglas de comentario: (prioridad, función(s, c) -> texto o None). `s` = ficha de la
    heroína (b3_stats_det) y `c` = contexto (equipo, ranking, menciones…). Hay más de 50."""
    R = []

    def add(prio, fn):
        R.append((prio, fn))

    jug = lambda s: s["vs"] > 0
    # ---- daño y etapas
    add(9, lambda s, c: "😴 No hizo nada de daño" if jug(s) and s["dano"] == 0 else None)
    add(8, lambda s, c: "🫥 0 etapas ganadas" if jug(s) and s["etapas_g"] == 0 and s["dano"] > 0 else None)
    add(5, lambda s, c: f"☝ Una sola etapa ganada" if s["etapas_g"] == 1 else None)
    add(6, lambda s, c: f"🏅 {s['etapas_g']} etapas ganadas" if s["etapas_g"] >= 6 else None)
    add(7, lambda s, c: f"💥 Quitó {s['dano']} ❤ en total" if s["dano"] >= 12 else None)
    add(4, lambda s, c: f"🗡 Quitó {s['dano']} ❤ a sus rivales" if 4 <= s["dano"] < 12 else None)
    add(6, lambda s, c: f"🩹 Aguantó {s['recibido']} ❤ de daño" if s["recibido"] >= 12 else None)
    add(5, lambda s, c: f"🧊 Casi ni la rozaron: {s['recibido']} ❤"
        if jug(s) and s["recibido"] <= 1 and s["vs"] >= 2 else None)
    add(4, lambda s, c: f"📊 Ganó {s['etapas_g']} de {s['etapas_g'] + s['etapas_p']} etapas"
        if s["etapas_g"] + s["etapas_p"] >= 5 else None)
    add(8, lambda s, c: f"🎯 {_pct(s['etapas_g'], s['etapas_g'] + s['etapas_p'])}% de etapas ganadas"
        if s["etapas_g"] + s["etapas_p"] >= 5
        and _pct(s["etapas_g"], s["etapas_g"] + s["etapas_p"]) >= 75 else None)
    add(7, lambda s, c: f"📉 Solo {_pct(s['etapas_g'], s['etapas_g'] + s['etapas_p'])}% de etapas ganadas"
        if s["etapas_g"] + s["etapas_p"] >= 5
        and _pct(s["etapas_g"], s["etapas_g"] + s["etapas_p"]) <= 25 else None)
    add(7, lambda s, c: f"🚀 Racha de {s['rachas_g']} etapas seguidas" if s["rachas_g"] >= 4 else None)
    add(6, lambda s, c: f"🥶 {s['rachas_p']} etapas perdidas seguidas" if s["rachas_p"] >= 4 else None)
    add(5, lambda s, c: f"🤝 {s['empates']} empates: nunca se decide" if s["empates"] >= 3 else None)
    add(6, lambda s, c: "🤝 Solo sabe empatar"
        if s["etapas_g"] == 0 and s["empates"] >= 2 else None)
    add(6, lambda s, c: f"🧸 Ganó {s['etapas_g']} y perdió {s['etapas_p']} etapas"
        if s["etapas_g"] in (1, 2) and s["etapas_p"] >= 5 else None)
    # ---- K.O., versus y supervivencia
    add(8, lambda s, c: f"💀 {s['ko']} K.O. a rivales" if s["ko"] >= 2 else None)
    add(6, lambda s, c: "💀 1 K.O. en su cuenta" if s["ko"] == 1 else None)
    add(5, lambda s, c: "🕊 Cero K.O.: pura paz" if s["vs"] >= 2 and s["ko"] == 0 else None)
    add(8, lambda s, c: ("👑 Derribó a una capitana rival" if s["ko_caps"] == 1
                          else f"👑 Derribó a {s['ko_caps']} capitanas rivales") if s["ko_caps"] else None)
    add(9, lambda s, c: f"🔥 Invicta: {s['vg']} de {s['vs']} versus ganados"
        if s["vs"] >= 2 and s["vg"] == s["vs"] else None)
    add(8, lambda s, c: f"🧊 Sin victorias en {s['vs']} versus"
        if s["vs"] >= 2 and s["vg"] == 0 else None)
    add(6, lambda s, c: f"⚔ {s['vs']} versus: infatigable" if s["vs"] >= 5 else None)
    add(7, lambda s, c: f"✨ {s['perfectos']} versus sin perder una etapa" if s["perfectos"] else None)
    add(7, lambda s, c: "🥶 Recibió una paliza: 0 etapas en un versus" if s["palizas"] else None)
    add(6, lambda s, c: "💥 Doble K.O.: cayó junto a su rival" if s["doble_ko"] else None)
    add(6, lambda s, c: f"😰 Ganó un versus con solo 1 ❤" if s["gano_con_1"] else None)
    add(7, lambda s, c: "🛡 Nunca cayó en combate" if s["vs"] >= 2 and not s["caidas"] else None)
    add(7, lambda s, c: f"☠ Cayó en {c['ronda_caida']}" if s["caidas"] and c.get("ronda_caida") else None)
    add(6, lambda s, c: "🧍 Última en pie de su equipo" if s["sola"] else None)
    add(6, lambda s, c: f"💊 Se curó entre rondas ({s['curadas']}×)" if s["curadas"] else None)
    add(5, lambda s, c: f"🥵 Terminó con solo {s['vida_final']} ❤"
        if s["vida_final"] is not None and 1 <= s["vida_final"] <= 2 else None)
    add(5, lambda s, c: f"💖 {s['vida_final']} ❤: casi intacta"
        if s["vida_final"] is not None and s["vida_final"] >= 9 and s["vs"] >= 1 else None)
    add(9, lambda s, c: "🪑 Calentó la banca: no peleó" if s["vs"] == 0 and c["equipo_jugo"] else None)
    # ---- categorías de etapa (lo que mejor y peor hace)
    for clave, (ico, frase) in FRASE_CAT.items():
        add(6, lambda s, c, k=clave, i=ico, f=frase:
            f"{i} {f}: {_com_cat(s, k)} etapas"
            if _com_cat(s, k) >= 2 and _com_cat(s, k) == max(s["cats_g"].values()) else None)
        add(5, lambda s, c, k=clave, f=FRASE_DEBIL[clave]:
            f"📉 {f[0].upper() + f[1:]}"
            if _com_cat(s, k, False) >= 2 and _com_cat(s, k) == 0 else None)
    # ---- equipo, capitana y ranking
    add(8, lambda s, c: "👑 Capitana y MVP de su equipo" if c["es_cap"] and c["mejor_equipo"] else None)
    add(6, lambda s, c: "👑 Capitana campeona" if c["es_cap"] and c["campeon"] else None)
    add(6, lambda s, c: "👑 La capitana cayó primero" if s["cap_primera"] else None)
    add(5, lambda s, c: "👑 Capitana: cayó en la 1.ª ronda"
        if c["es_cap"] and c["primera_ronda"] else None)
    add(8, lambda s, c: "🌟 La mejor de toda la temporada" if c["rank_ind"] == 1 and c["n_ind"] > 3 else None)
    add(6, lambda s, c: f"🌟 Top 3 individual (#{c['rank_ind']})"
        if 2 <= c["rank_ind"] <= 3 and c["n_ind"] > 3 else None)
    add(5, lambda s, c: "⭐ La mejor de su equipo" if c["mejor_equipo"] and not c["es_cap"] else None)
    add(6, lambda s, c: "🐢 La que menos aportó de su equipo" if c["peor_equipo"] else None)
    add(6, lambda s, c: f"🏋 Cargó al equipo: {c['aporte']}% de sus etapas" if c["aporte"] >= 55 else None)
    add(6, lambda s, c: f"🎒 De paseo: solo {c['aporte']}% de las etapas del equipo"
        if c["aporte"] <= 12 and c["equipo_etapas"] >= 6 and s["vs"] > 0 else None)
    add(7, lambda s, c: f"🏆 Brilló en la final: {s['etapas_final']} etapas"
        if s["etapas_final"] >= 3 else None)
    add(6, lambda s, c: "🎖 " + " · ".join(t for _i, t, _d in c["honores"][:2]) if c["honores"] else None)
    add(4, lambda s, c: "⚰ Último puesto individual" if c["rank_ind"] == c["n_ind"] and c["n_ind"] > 3 else None)
    # ---- eventos
    add(6, lambda s, c: FRASE_EV[s["ev_propios"][-1]] if s["ev_propios"] and s["ev_propios"][-1] in FRASE_EV else None)
    add(5, lambda s, c: (lambda e: f"{e['ico']} Le tocó «{e['nombre']}»")(EVENTOS_3V3[s["ev_propios"][-1]])
        if s["ev_propios"] and s["ev_propios"][-1] in EVENTOS_3V3
        and s["ev_propios"][-1] not in FRASE_EV else None)
    add(5, lambda s, c: f"⚡ Vivió {s['eventos']} eventos aleatorios" if s["eventos"] >= 3 else None)
    return R


COMENTARIOS_3V3 = _comentarios_def()


def b3_comentarios(s, c, semilla, n=3):
    """Hasta n comentarios cortos de una heroína, los más llamativos primero. El orden entre
    los de igual interés es fijo para cada temporada (no cambia cada vez que abres el ranking)."""
    rnd = random.Random(semilla)
    cand = []
    for prio, fn in COMENTARIOS_3V3:
        try:
            t = fn(s, c)
        except Exception:
            t = None
        if t:
            cand.append((-prio, rnd.random(), t))
    cand.sort()
    return [t for _p, _r, t in cand[:n]]


def b3_ficha_vacia():
    return dict(vs=0, vg=0, vp=0, ko=0, caidas=0, ronda_caida=None, etapas_g=0, etapas_p=0,
                empates=0, dano=0, recibido=0, eventos=0, ev_propios=[], cats_g={}, cats_p={},
                rachas_g=0, rachas_p=0, perfectos=0, palizas=0, doble_ko=0, ko_caps=0, curadas=0,
                sola=0, vida_final=None, rondas=set(), etapas_final=0, gano_con_1=0,
                cap_primera=False, cur_g=0, cur_p=0)


ROJO_PELIGRO = "#ff4d5e"
VERDE_VENTAJA = "#6be19b"


def muestra_cg(rutas, n=3):
    """Hasta n capturas AL AZAR (distintas en cada duelo) que existan en el disco."""
    out = []
    for r in random.sample(rutas, min(len(rutas), n + 7)) if rutas else []:
        if Path(r).exists():
            out.append(r)
            if len(out) >= n:
                break
    return out


class CabeceraDuelista(QWidget):
    """Tarjeta de una heroína en el duelo: foto, nombre, subtítulo y chips (rojos = desventaja)."""

    def __init__(self):
        super().__init__()
        self.it, self.av, self.chips = None, None, []
        self.setFixedHeight(108)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def poner(self, it, pm, chips):
        self.it, self.av, self.chips = it, pm, chips
        self.update()

    def paintEvent(self, e):
        if not self.it:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio + 2, Tema.radio + 2)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, mezclar(card, a1, 0.16))
        g.setColorAt(1, mezclar(card, a2, 0.05))
        p.fillPath(camino, QBrush(g))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(mezclar(borde, a1, 0.6), 1.6))
        p.drawPath(camino)
        ar = 38.0
        c = QPointF(r.left() + 16 + ar, r.center().y())
        if self.av is not None and not self.av.isNull():
            p.drawPixmap(QRectF(c.x() - ar, c.y() - ar, ar * 2, ar * 2), self.av,
                         QRectF(self.av.rect()))
        p.setPen(QPen(a1, 3))
        p.drawEllipse(c, ar, ar)
        x = c.x() + ar + 14
        w = r.right() - 12 - x
        texto_el(p, x, r.top() + 10, w, 28, self.it["nombre"], fnt(Tema.tam + 4, bold=True), txt)
        texto_el(p, x, r.top() + 39, w, 18, self.it.get("sub2") or "",
                 fnt(max(8.0, Tema.tam - 1.5)), mu)
        fc = fnt(px=11, bold=True)
        fm = QFontMetrics(fc)
        xx, y = x, r.top() + 64
        for texto, color in self.chips:
            col = QColor(color)
            a = fm.horizontalAdvance(texto) + 20
            if xx + a > r.right() - 10:
                break
            pr = QRectF(xx, y, a, 24)
            p.setPen(QPen(con_alfa(col, 200), 1.3))
            p.setBrush(con_alfa(col, 52))
            p.drawRoundedRect(pr, 12, 12)
            p.setFont(fc)
            p.setPen(col if col.lightness() > 110 else txt)
            p.drawText(pr, int(Qt.AlignmentFlag.AlignCenter), texto)
            xx += a + 6
        p.end()


class Marcador(QWidget):
    """El «L : R» de los criterios ganados en el duelo actual."""

    def __init__(self):
        super().__init__()
        self.l = self.r = 0
        self.setFixedWidth(128)
        self.setFixedHeight(108)

    def poner(self, l, r):
        self.l, self.r = l, r
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1 = QColor(Tema.a1())
        mu, txt = QColor(Tema.c("muted")), QColor(Tema.c("text"))
        W = self.width()
        texto_el(p, 0, 6, W, 26, "VS", fnt(px=22, bold=True, esp=2), a1, Qt.AlignmentFlag.AlignHCenter)
        fb = fnt(px=30, bold=True)
        for val, otro, x in ((self.l, self.r, 6), (self.r, self.l, W - 50)):
            texto_el(p, x, 36, 44, 38, str(val), fb,
                     a1 if val > otro else txt, Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, W / 2 - 8, 36, 16, 38, ":", fb, mu, Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, 0, 80, W, 18, getattr(self, "etiqueta", "CRITERIOS"),
                 fnt(px=10, bold=True, esp=1.6), mu,
                 Qt.AlignmentFlag.AlignHCenter)
        p.end()


class FilaGalerias(QWidget):
    """Un «duelo de CGs»: hasta 3 al azar de cada heroína, una frente a otra. Si a una le falta
    ese tipo de CG sale en rojo como desventaja. Clic en una miniatura: verla en grande."""
    ver = Signal(str)
    CENTRO = 176

    def __init__(self, nombre, icono, color):
        super().__init__()
        self.nombre, self.icono, self.color = nombre, icono, color
        self.L = self.R = {"n": 0, "rutas": []}
        self._zonas = []
        self.setFixedHeight(126)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def poner(self, L, R):
        self.L, self.R = L, R
        self.update()

    def mouseMoveEvent(self, e):
        sobre = any(z.contains(e.position()) for z, _ in self._zonas)
        self.setCursor(Qt.CursorShape.PointingHandCursor if sobre else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            for z, ruta in self._zonas:
                if z.contains(e.position()):
                    self.ver.emit(ruta)
                    return

    def _lado(self, p, r, d):
        rojo = QColor(ROJO_PELIGRO)
        if not d["rutas"]:                                   # desventaja
            caja = r.adjusted(2, 6, -2, -6)
            p.setBrush(con_alfa(rojo, 36))
            p.setPen(QPen(rojo, 2, Qt.PenStyle.DashLine))
            p.drawRoundedRect(caja, 12, 12)
            texto_el(p, caja.left(), caja.top() + caja.height() / 2 - 24, caja.width(), 24,
                     f"⚠  Sin {self.nombre}", fnt(Tema.tam + 1, bold=True), rojo,
                     Qt.AlignmentFlag.AlignHCenter)
            texto_el(p, caja.left(), caja.top() + caja.height() / 2 + 2, caja.width(), 20,
                     "DESVENTAJA", fnt(px=11, bold=True, esp=2), rojo,
                     Qt.AlignmentFlag.AlignHCenter)
            return
        gap = 8.0
        sw = (r.width() - 2 * gap) / 3
        col = QColor(self.color)
        for i in range(3):
            rr = QRectF(r.left() + i * (sw + gap), r.top() + 6, sw, r.height() - 12)
            if i < len(d["rutas"]):
                ruta_i = d["rutas"][i]
                pm_i = CACHE_MINI.obtener_diferido(ruta_i, 360, self)     # sin congelar la ventana
                if pm_i.isNull() and (str(ruta_i), 360) not in CACHE_MINI.datos:
                    cam_i = QPainterPath()                                 # aún cargando
                    cam_i.addRoundedRect(rr, 10, 10)
                    p.fillPath(cam_i, QBrush(mezclar(QColor(Tema.c("card")), col, 0.14)))
                    texto_el(p, rr.left(), rr.center().y() - 11, rr.width(), 22, "⏳",
                             fnt(px=15), QColor(Tema.c("muted")), Qt.AlignmentFlag.AlignHCenter)
                else:
                    dibujar_cover(p, rr, pm_i, 10)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(con_alfa(col, 210), 1.8))
                p.drawRoundedRect(rr, 10, 10)
                self._zonas.append((rr, d["rutas"][i]))
            else:                                            # hueco: mantiene la fila ordenada
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(con_alfa(Tema.c("border"), 200), 1.2, Qt.PenStyle.DashLine))
                p.drawRoundedRect(rr, 10, 10)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._zonas = []
        W, H = self.width(), self.height()
        lw = (W - self.CENTRO - 16) / 2
        self._lado(p, QRectF(0, 0, lw, H), self.L)
        self._lado(p, QRectF(W - lw, 0, lw, H), self.R)
        cen = QRectF(lw + 8, 0, self.CENTRO, H).adjusted(4, 8, -4, -8)
        card, txt, mu = QColor(Tema.c("card")), QColor(Tema.c("text")), QColor(Tema.c("muted"))
        col = QColor(self.color)
        camino = QPainterPath()
        camino.addRoundedRect(cen, 16, 16)
        p.fillPath(camino, QBrush(mezclar(card, col, 0.16)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(con_alfa(col, 170), 1.4))
        p.drawPath(camino)
        texto_el(p, cen.left() + 6, cen.top() + 8, cen.width() - 12, 22,
                 f"{self.icono}  {self.nombre}", fnt(Tema.tam, bold=True), txt,
                 Qt.AlignmentFlag.AlignHCenter)
        nl, nr = self.L["n"], self.R["n"]

        def color_n(n, otro):
            return (QColor(ROJO_PELIGRO) if n == 0 else
                    QColor(VERDE_VENTAJA) if n > otro else txt)
        fb = fnt(px=26, bold=True)
        mitad = (cen.width() - 36) / 2
        texto_el(p, cen.left() + 6, cen.top() + 36, mitad, 34, str(nl), fb,
                 color_n(nl, nr), Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, cen.center().x() - 12, cen.top() + 36, 24, 34, "vs", fnt(px=12, bold=True),
                 mu, Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, cen.right() - 6 - mitad, cen.top() + 36, mitad, 34, str(nr), fb,
                 color_n(nr, nl), Qt.AlignmentFlag.AlignHCenter)
        if nl == nr:
            veredicto, vc = "igualadas", mu
        else:
            veredicto, vc = ("◀  más CGs" if nl > nr else "más CGs  ▶"), QColor(VERDE_VENTAJA)
        texto_el(p, cen.left() + 6, cen.bottom() - 28, cen.width() - 12, 20, veredicto,
                 fnt(px=11, bold=True), vc, Qt.AlignmentFlag.AlignHCenter)
        p.end()


class PanelCriterios(QWidget):
    """Rejilla de criterios: clic en la mitad izquierda o derecha de cada celda para dar el punto
    a esa heroína (otro clic en la misma mitad lo quita)."""
    cambio = Signal()
    FILA, GAP, COLS, TOPE = 44, 8, 2, 26

    def __init__(self):
        super().__init__()
        self.votos = {c[0]: 0 for c in CRITERIOS_DUELO}
        self._hover = None
        self.setMouseTracking(True)
        filas = ceil(len(CRITERIOS_DUELO) / self.COLS)
        self.setFixedHeight(self.TOPE + filas * (self.FILA + self.GAP))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def reset(self):
        for k in self.votos:
            self.votos[k] = 0
        self.update()
        self.cambio.emit()

    def puntos(self):
        v = list(self.votos.values())
        return v.count(-1), v.count(1)

    def _celda(self, i):
        cw = (self.width() - self.GAP * (self.COLS - 1)) / self.COLS
        c, f = i % self.COLS, i // self.COLS
        return QRectF(c * (cw + self.GAP), self.TOPE + f * (self.FILA + self.GAP), cw, self.FILA)

    def _en(self, pos):
        for i in range(len(CRITERIOS_DUELO)):
            r = self._celda(i)
            if r.contains(pos):
                return i, (-1 if pos.x() < r.center().x() else 1)
        return None

    def mouseMoveEvent(self, e):
        h = self._en(e.position())
        if h != self._hover:
            self._hover = h
            self.setCursor(Qt.CursorShape.PointingHandCursor if h else Qt.CursorShape.ArrowCursor)
            self.update()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._hover = None
        self.update()

    def mouseReleaseEvent(self, e):
        h = self._en(e.position())
        if e.button() == Qt.MouseButton.LeftButton and h:
            clave = CRITERIOS_DUELO[h[0]][0]
            self.votos[clave] = 0 if self.votos[clave] == h[1] else h[1]
            self.update()
            self.cambio.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        texto_el(p, 4, 0, self.width() - 8, 22,
                 "CRITERIOS  ·  toca el lado de la heroína que gana en cada uno",
                 fnt(px=11, bold=True, esp=1.2), mu)
        for i, (clave, icono, nombre) in enumerate(CRITERIOS_DUELO):
            r = self._celda(i)
            voto = self.votos[clave]
            camino = QPainterPath()
            camino.addRoundedRect(r, 12, 12)
            p.fillPath(camino, QBrush(mezclar(card, a1, 0.05)))
            p.save()
            p.setClipPath(camino)
            for lado in (-1, 1):
                mitad = QRectF(r.left() if lado < 0 else r.center().x(), r.top(),
                               r.width() / 2, r.height())
                if voto == lado:
                    g = QLinearGradient(mitad.topLeft(), mitad.bottomRight())
                    g.setColorAt(0, a1)
                    g.setColorAt(1, a2)
                    p.fillRect(mitad, QBrush(g))
                elif self._hover == (i, lado):
                    p.fillRect(mitad, con_alfa(a1, 46))
            p.restore()
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(a1 if voto else borde, 1.6 if voto else 1.2))
            p.drawPath(camino)
            for lado, flecha in ((-1, "◀"), (1, "▶")):
                x = r.left() + 12 if lado < 0 else r.right() - 30
                texto_el(p, x, r.top(), 18, r.height(), flecha, fnt(px=13, bold=True),
                         QColor(TEXTO_SOBRE_ACENTO) if voto == lado else mu,
                         Qt.AlignmentFlag.AlignHCenter)
            texto_el(p, r.left() + 38, r.top(), r.width() - 76, r.height(), f"{icono}  {nombre}",
                     fnt(Tema.tam, bold=True), txt, Qt.AlignmentFlag.AlignHCenter)
        p.end()


class BannerEtapas(QWidget):
    """Tira con las etapas del versus: las ya decididas (color de la heroína que ganó cada una),
    la actual resaltada y las que faltan."""

    def __init__(self):
        super().__init__()
        self.etapas, self.res, self.actual = [], {}, 0
        self.colores = None
        self.setFixedHeight(66)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def poner(self, etapas, res, actual, colores=None):
        """colores: un color por participante; en ese modo res[etapa] = nº de participante (1, 2, 3)
        y 0 = sin punto. Sin colores: -1 izquierda / 1 derecha (modo original)."""
        self.etapas, self.res, self.actual = list(etapas), dict(res), actual
        self.colores = colores
        self.update()

    def paintEvent(self, e):
        n = len(self.etapas)
        if not n:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        gap = 8.0
        w = (self.width() - gap * (n - 1)) / n
        for i, (clave, icono, nombre, _q) in enumerate(self.etapas):
            r = QRectF(i * (w + gap), 4, w, self.height() - 8)
            voto = self.res.get(clave)
            cam = QPainterPath()
            cam.addRoundedRect(r, 12, 12)
            if voto is None:
                relleno = mezclar(card, a1, 0.14 if i == self.actual else 0.04)
            elif voto == 0:
                relleno = mezclar(card, QColor(Tema.c("muted")), 0.18)
            else:
                if self.colores:
                    col_v = self.colores[(voto - 1) % len(self.colores)]
                else:
                    col_v = a1 if voto < 0 else a2
                relleno = mezclar(card, col_v, 0.55)
            p.fillPath(cam, QBrush(relleno))
            p.setBrush(Qt.BrushStyle.NoBrush)
            if i == self.actual:
                p.setPen(QPen(con_alfa(a1, 90), 6))
                p.drawPath(cam)
                p.setPen(QPen(a1, 2.2))
            else:
                p.setPen(QPen(borde, 1.2))
            p.drawPath(cam)
            texto_el(p, r.left(), r.top() + 3, r.width(), 26, icono, fnt(px=18), txt,
                     Qt.AlignmentFlag.AlignHCenter)
            lado = ""
            if voto and not self.colores:
                lado = "◀ " if voto < 0 else " ▶"
            texto_el(p, r.left() + 3, r.top() + 30, r.width() - 6, 16, lado[:2] + nombre + lado[2:],
                     fnt(px=10, bold=(i == self.actual)), txt if (i == self.actual or voto) else mu,
                     Qt.AlignmentFlag.AlignHCenter)
        p.end()


class RetratosVersus(QWidget):
    """Las dos heroínas en grande para las etapas sin CGs (historia, final, voz…).
    Clic en una para darle el punto."""
    elegir = Signal(int)                     # -1 izquierda · +1 derecha

    def __init__(self):
        super().__init__()
        self.L = self.R = None
        self.pmL = self.pmR = None
        self.icono, self.nombre = "", ""
        self._hover = 0
        self.setMouseTracking(True)
        self.setMinimumHeight(250)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def poner(self, L, pmL, R, pmR, icono, nombre):
        self.L, self.pmL, self.R, self.pmR = L, pmL, R, pmR
        self.icono, self.nombre = icono, nombre
        self.update()

    def _lado_en(self, pos):
        if pos.x() < self.width() * 0.4:
            return -1
        if pos.x() > self.width() * 0.6:
            return 1
        return 0

    def mouseMoveEvent(self, e):
        h = self._lado_en(e.position())
        if h != self._hover:
            self._hover = h
            self.setCursor(Qt.CursorShape.PointingHandCursor if h else Qt.CursorShape.ArrowCursor)
            self.update()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._hover = 0
        self.update()

    def mouseReleaseEvent(self, e):
        h = self._lado_en(e.position())
        if e.button() == Qt.MouseButton.LeftButton and h:
            self.elegir.emit(h)

    def paintEvent(self, e):
        if not self.L:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        W, H = self.width(), self.height()
        rad = max(50.0, min(H * 0.34, W * 0.13, 130.0))
        for lado, it, pm, cx in ((-1, self.L, self.pmL, W * 0.2), (1, self.R, self.pmR, W * 0.8)):
            col = a1 if lado < 0 else a2
            cy = H * 0.42
            r = rad * (1.05 if self._hover == lado else 1.0)
            if self._hover == lado:
                for k in range(5, 0, -1):
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(con_alfa(col, 16))
                    p.drawEllipse(QPointF(cx, cy), r + k * 7, r + k * 7)
            if pm is not None and not pm.isNull():
                p.drawPixmap(QRectF(cx - r, cy - r, 2 * r, 2 * r), pm, QRectF(pm.rect()))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(col, 5 if self._hover == lado else 3.5))
            p.drawEllipse(QPointF(cx, cy), r, r)
            texto_el(p, cx - W * 0.19, cy + r + 12, W * 0.38, 34, it["nombre"],
                     fnt(Tema.tam + 7, bold=True), txt, Qt.AlignmentFlag.AlignHCenter)
            texto_el(p, cx - W * 0.19, cy + r + 46, W * 0.38, 22, it.get("sub2") or "",
                     fnt(max(8.0, Tema.tam - 1)), mu, Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, W * 0.4, H * 0.42 - 52, W * 0.2, 70, self.icono, fnt(px=58), txt,
                 Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, W * 0.4, H * 0.42 + 18, W * 0.2, 28, self.nombre,
                 fnt(Tema.tam + 3, bold=True), a1, Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, W * 0.4, H * 0.42 + 48, W * 0.2, 20, "toca a la que gana",
                 fnt(max(8.0, Tema.tam - 2)), mu, Qt.AlignmentFlag.AlignHCenter)
        p.end()


def _estrella_v(p, cx, cy, r, color):
    pts = []
    for k in range(8):
        ang = -pi / 2 + k * pi / 4
        rad = r if k % 2 == 0 else r * 0.28
        pts.append(QPointF(cx + cos(ang) * rad, cy + sin(ang) * rad))
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawPolygon(QPolygonF(pts))
    p.restore()


class PantallaVictoria(QWidget):
    """Pantalla a pantalla completa con la ganadora del versus: rayos, trofeo, confeti y resumen
    de las etapas. «Aceptar» pasa al siguiente combate."""
    aceptar = Signal()

    ORO1, ORO2 = QColor(255, 236, 140), QColor(238, 164, 34)

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.g = self.pm = self.perd = None
        self.gana = self.pierde = 0
        self.tally = []
        self.texto = self.titulo = None
        self.t0 = 0.0
        self._tprev = 0.0
        self.conf = []
        # Inicializar el timer ANTES de ocultar el widget:
        # hide() puede disparar hideEvent(), que detiene self.timer.
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.update)
        self.hide()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 34)
        lay.addStretch()
        self.btn = BotonAnimado("Aceptar  ▶  siguiente combate", primario=True)
        self.btn.setFixedSize(380, 54)
        self.btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn.clicked.connect(self._clic)
        lay.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignHCenter)

    def listo(self):
        return self.isVisible() and time.monotonic() - self.t0 > 0.7

    def _clic(self):
        if self.listo():
            self.aceptar.emit()

    def mostrar(self, g, pm, perd, gana, pierde, tally, ultimo, texto=None, titulo=None,
                boton=None):
        self.g, self.pm, self.perd = g, pm, perd
        self.gana, self.pierde, self.tally = gana, pierde, tally
        self.texto, self.titulo = texto, titulo
        self.btn.setText(boton or ("Aceptar  ▶  ver la clasificación" if ultimo
                                   else "Aceptar  ▶  siguiente combate"))
        self.setGeometry(self.parentWidget().rect())
        self.t0 = self._tprev = time.monotonic()
        W = max(400, self.width())
        cols = (self.ORO1, QColor(Tema.a1()), QColor(Tema.a2()), QColor(255, 255, 255),
                QColor(140, 230, 200))
        self.conf = [[random.uniform(0, W), random.uniform(-400, -10), random.uniform(-1.2, 1.2),
                      random.uniform(90, 230), random.uniform(0, 360), random.uniform(-260, 260),
                      cols[random.randrange(len(cols))], random.uniform(6, 12)]
                     for _ in range(110)]
        self.raise_()
        self.show()
        self.timer.start()

    def hideEvent(self, e):
        self.timer.stop()
        super().hideEvent(e)

    def paintEvent(self, e):
        if self.g is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        ahora = time.monotonic()
        t, dt = ahora - self.t0, min(0.1, ahora - self._tprev)
        self._tprev = ahora
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        W, H = self.width(), self.height()
        fondo = QColor(14, 9, 26)
        p.fillRect(self.rect(), fondo)
        cx, cy = W / 2, H * 0.36
        ent = min(1.0, t / 0.7)
        glow = QRadialGradient(QPointF(cx, cy), max(W, H) * 0.75)
        glow.setColorAt(0, mezclar(fondo, a1, 0.55 * ent))
        glow.setColorAt(1, fondo)
        p.fillRect(self.rect(), QBrush(glow))

        # rayos giratorios (efecto anime)
        p.save()
        p.translate(cx, cy)
        p.rotate(t * 9)
        R = max(W, H)
        for k in range(18):
            a0 = k * 20.0
            cam = QPainterPath()
            cam.moveTo(0, 0)
            cam.lineTo(R * cos(a0 * pi / 180), R * sin(a0 * pi / 180))
            cam.lineTo(R * cos((a0 + 10) * pi / 180), R * sin((a0 + 10) * pi / 180))
            cam.closeSubpath()
            p.fillPath(cam, con_alfa(self.ORO1 if k % 2 == 0 else a1, int(34 * ent)))
        p.restore()

        # retrato de la ganadora (entra con rebote)
        def rebote(x):
            c1 = 1.70158
            return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2
        d = min(270.0, H * 0.36) * rebote(ent)
        r = d / 2
        for k in range(6, 0, -1):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(con_alfa(self.ORO2, 14))
            p.drawEllipse(QPointF(cx, cy), r + k * 9, r + k * 9)
        if self.pm is not None and not self.pm.isNull() and r > 1:
            p.drawPixmap(QRectF(cx - r, cy - r, d, d), self.pm, QRectF(self.pm.rect()))
        ar = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
        ar.setColorAt(0, self.ORO1)
        ar.setColorAt(1, self.ORO2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QBrush(ar), 9))
        p.drawEllipse(QPointF(cx, cy), r, r)
        dibujar_trofeo(p, QPointF(cx, cy - r - 30 + sin(t * 3) * 4), 96 * ent, self.ORO1, self.ORO2)
        for k in range(8):                                    # estrellitas que titilan
            ang = k * pi / 4 + t * 0.5
            rr = r + 44 + 10 * sin(t * 2 + k)
            tw = max(0.0, sin(pi * ((t * 0.9 + k * 0.37) % 1.0)))
            if tw > 0.03:
                _estrella_v(p, cx + cos(ang) * rr, cy + sin(ang) * rr * 0.9, 12 * tw,
                            QColor(255, 244, 190, int(240 * tw)))

        # texto
        a = max(0.0, min(1.0, (t - 0.45) / 0.45))
        y0 = cy + r + 22 + (1 - a) * 30
        p.setOpacity(a)
        f = fnt(px=62, bold=True, esp=7)
        texto = self.titulo or "¡VICTORIA!"
        ancho = QFontMetrics(f).horizontalAdvance(texto)
        ruta = QPainterPath()
        ruta.addText(cx - ancho / 2, y0 + 58, f, texto)
        gt = QLinearGradient(cx - ancho / 2, y0, cx + ancho / 2, y0 + 60)
        gt.setColorAt(0, self.ORO1)
        gt.setColorAt(0.5, QColor(255, 255, 255))
        gt.setColorAt(1, self.ORO2)
        p.setPen(QPen(QColor(60, 20, 10, 200), 4))
        p.setBrush(QBrush(gt))
        p.drawPath(ruta)
        texto_el(p, 0, y0 + 68, W, 44, self.g["nombre"], fnt(px=36, bold=True),
                 QColor(255, 255, 255), Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, 0, y0 + 112, W, 30,
                 self.texto or f"gana el versus  {self.gana} – {self.pierde}  a {self.perd['nombre']}",
                 fnt(px=19, bold=True), self.ORO1, Qt.AlignmentFlag.AlignHCenter)
        # etapas: ✔ las que ganó ella · apagadas las de la rival
        n = len(self.tally)
        if n:
            paso = 52.0
            x0 = cx - paso * (n - 1) / 2
            for i, (ico, quien) in enumerate(self.tally):
                c = QPointF(x0 + i * paso, y0 + 176)
                if quien == "g":
                    gg = QLinearGradient(c.x() - 20, c.y() - 20, c.x() + 20, c.y() + 20)
                    gg.setColorAt(0, self.ORO1)
                    gg.setColorAt(1, self.ORO2)
                    p.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
                    p.setBrush(QBrush(gg))
                elif quien == "p":
                    p.setPen(QPen(QColor(255, 255, 255, 50), 1.3))
                    p.setBrush(QColor(255, 255, 255, 14))
                else:
                    p.setPen(QPen(QColor(255, 255, 255, 60), 1.3, Qt.PenStyle.DashLine))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(c, 21, 21)
                p.setOpacity(a * (1.0 if quien == "g" else 0.45))
                texto_el(p, c.x() - 21, c.y() - 15, 42, 30, ico, fnt(px=18),
                         QColor(40, 20, 10) if quien == "g" else QColor(255, 255, 255),
                         Qt.AlignmentFlag.AlignHCenter)
                p.setOpacity(a)
        p.setOpacity(1.0)

        # confeti
        for c in self.conf:
            c[0] += c[2] * 60 * dt
            c[1] += c[3] * dt
            c[4] += c[5] * dt
            if c[1] > H + 20:
                c[0], c[1] = random.uniform(0, W), random.uniform(-60, -10)
            p.save()
            p.translate(c[0], c[1])
            p.rotate(c[4])
            p.fillRect(QRectF(-c[7] / 2, -c[7] / 3, c[7], c[7] * 0.66), c[6])
            p.restore()
        p.end()


def _suave(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


class DialogoVersus(QDialog):
    """Todos contra todos, por etapas. Cada combate enfrenta a 2 heroínas: primero sus CG favoritos,
    CG normal y CG H (hasta 3 de cada una) y después historia, final, personalidad, diseño, voz y
    romance. Al terminar se anuncia la ganadora y, con «Aceptar», se pasa a otro combate.
    Cada combate se guarda al aceptarlo: esa pareja no vuelve a salir."""

    def __init__(self, parent, titulo, items, datos, hechos, solo_con, guardar, rondas=None):
        super().__init__(parent)
        self.items = items
        self.por_id = {i["id"]: i for i in items}
        self.ids = [i["id"] for i in items]
        self.datos = datos
        self.guardar = guardar
        self.resultados = list(hechos)               # (ganadora, perdedora, etapas) de siempre
        self.ya = len(hechos)
        self.rondas, self.solo_con = rondas, solo_con      # rondas: torneo suizo (None = todos)
        if rondas:
            self.pares = generar_ronda_suiza(self.ids, self.resultados, rondas, solo_con)
        else:
            self.pares = generar_pares(self.ids, [(g, p) for g, p, _ in hechos], solo_con)
        self.total = len(self.pares)
        self.idx = 0
        self.hubo = False
        self.aplicar = False
        self.resultado = list(self.ids)
        self._av, self._avg = {}, {}
        self._izq = self._der = None
        self.etapas, self.votos, self.e = list(ETAPAS_VERSUS), {}, 0
        self._ganadora = self._perdedora = None
        self._guardado = -1                          # índice del último combate ya guardado
        self.setWindowTitle(f"Versus · {titulo}")
        self.resize(1240, 920)
        self.setMinimumSize(1000, 720)

        v = QVBoxLayout(self)
        v.setSpacing(8)
        cab = QHBoxLayout()
        t = QLabel("⚔ Versus")
        t.setObjectName("heading")
        cab.addWidget(t)
        cab.addStretch()
        self.lbl_prog = QLabel("")
        self.lbl_prog.setObjectName("muted")
        cab.addWidget(self.lbl_prog)
        self.b_clas = BotonAnimado("📊 Clasificación")
        self.b_clas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.b_clas.clicked.connect(self._alternar_clasificacion)
        cab.addWidget(self.b_clas)
        v.addLayout(cab)
        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        self.barra.setFixedHeight(10)
        v.addWidget(self.barra)

        self.pila = QStackedWidget()
        v.addWidget(self.pila, 1)

        # ---- página 0: el combate
        pg = QWidget()
        pv = QVBoxLayout(pg)
        pv.setContentsMargins(0, 0, 0, 0)
        pv.setSpacing(8)
        fila = QHBoxLayout()
        fila.setSpacing(10)
        self.cab_i, self.marcador, self.cab_d = CabeceraDuelista(), Marcador(), CabeceraDuelista()
        self.marcador.etiqueta = "ETAPAS"
        fila.addWidget(self.cab_i, 1)
        fila.addWidget(self.marcador)
        fila.addWidget(self.cab_d, 1)
        pv.addLayout(fila)
        self.banner = BannerEtapas()
        pv.addWidget(self.banner)
        self.lbl_preg = QLabel("")
        self.lbl_preg.setObjectName("heading")
        self.lbl_preg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pv.addWidget(self.lbl_preg)
        self.stack_etapa = QStackedWidget()
        self.fila_cg = FilaGalerias("CG favoritos", "⭐", "#ffc857")
        self.fila_cg.setFixedHeight(200)
        self.fila_cg.ver.connect(self._ver_grande)
        cont_cg = QWidget()
        cl = QVBoxLayout(cont_cg)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addStretch()
        cl.addWidget(self.fila_cg)
        cl.addWidget(QLabel("<span style='opacity:0.6'>Clic en un CG para verlo en grande</span>"),
                     0, Qt.AlignmentFlag.AlignHCenter)
        cl.addStretch()
        self.retratos = RetratosVersus()
        self.retratos.elegir.connect(self._votar)
        self.stack_etapa.addWidget(cont_cg)
        self.stack_etapa.addWidget(self.retratos)
        pv.addWidget(self.stack_etapa, 1)

        botones = QHBoxLayout()
        botones.setSpacing(8)

        def boton(texto, fn, primario=False):
            b = BotonAnimado(texto, primario=primario)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.clicked.connect(fn)
            return b
        self.b_izq = boton("◀", lambda: self._votar(-1), True)
        self.b_emp = boton("🤝 Empate / no sé", lambda: self._votar(0))
        self.b_der = boton("▶", lambda: self._votar(1), True)
        botones.addStretch()
        for b in (self.b_izq, self.b_emp, self.b_der):
            botones.addWidget(b)
        botones.addStretch()
        pv.addLayout(botones)
        self.pila.addWidget(pg)

        # ---- página 1: clasificación
        pc = QWidget()
        cv = QVBoxLayout(pc)
        cv.setContentsMargins(0, 0, 0, 0)
        self.lbl_clas = QLabel("")
        self.lbl_clas.setObjectName("muted")
        self.lbl_clas.setWordWrap(True)
        cv.addWidget(self.lbl_clas)
        self.lista_clas = QListWidget()
        self.lista_clas.setIconSize(QSize(52, 52))
        cv.addWidget(self.lista_clas, 1)
        self.pila.addWidget(pc)

        pie = QHBoxLayout()
        self.b_atras = boton("↩ Atrás", self._atras)
        self.b_salta = boton("⏭ Saltar combate", self._saltar)
        pie.addWidget(self.b_atras)
        pie.addWidget(self.b_salta)
        pie.addStretch()
        pie.addWidget(boton("Salir (se guarda y reordena)", self.reject))
        pie.addWidget(boton("✔ Aplicar ranking", self._aplicar, True))
        v.addLayout(pie)

        self.victoria = PantallaVictoria(self)
        self.victoria.aceptar.connect(self._aceptar_victoria)

        if self.pares:
            self._cargar_combate()
        else:
            self._fin_total()

    # ---------- utilidades
    def _avatar(self, cid):
        if cid not in self._av:
            it = self.por_id[cid]
            self._av[cid] = avatar(it.get("foto") or "", 160, it.get("enc"))
        return self._av[cid]

    def _avatar_grande(self, cid):
        if cid not in self._avg:
            it = self.por_id[cid]
            self._avg[cid] = avatar(it.get("foto") or "", 320, it.get("enc"))
        return self._avg[cid]

    def _chips(self, cid):
        it, d = self.por_id[cid], self.datos.get(cid, {})
        n = len(d.get("fav", []))
        chips = [(f"★ {n} {'CG favorito' if n == 1 else 'CG favoritos'}", "#ffc857")
                 if n else ("⚠ Sin CG favoritos", ROJO_PELIGRO)]
        _o, gan, per, _e = clasificar(self.ids, self.resultados)   # solo versus de esta lista
        if gan.get(cid, 0) + per.get(cid, 0):
            chips.append((f"⚔ {gan[cid]}V · {per[cid]}D", Tema.a1()))
        return chips

    def _datos_lado(self, cid, clave):
        lista = self.datos.get(cid, {}).get(clave, [])
        return {"n": len(lista), "rutas": muestra_cg(lista)}

    def _corto(self, cid):
        return QFontMetrics(fnt(Tema.tam)).elidedText(
            self.por_id[cid]["nombre"], Qt.TextElideMode.ElideRight, 230)

    def _puntos(self):
        v = list(self.votos.values())
        return v.count(-1), v.count(1)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.victoria.isVisible():
            self.victoria.setGeometry(self.rect())

    def _ver_grande(self, ruta):
        d = QDialog(self)
        d.setWindowTitle("Captura")
        d.resize(1000, 640)
        lay = QVBoxLayout(d)
        lay.setContentsMargins(8, 8, 8, 8)
        vg = VisorGrande()
        vg.poner(ruta)
        vg.clic.connect(d.accept)
        lay.addWidget(vg)
        d.exec()

    def _total_estimado(self):
        """Combates de la sesión: los de la cola + una estimación de las rondas que faltan."""
        if not self.rondas:
            return len(self.pares)
        juegos = {i: 0 for i in self.ids}
        for g, p, _e in self.resultados:
            if g in juegos:
                juegos[g] += 1
            if p in juegos:
                juegos[p] += 1
        for a, b in self.pares[self.idx:]:
            juegos[a] += 1
            juegos[b] += 1
        quieren = self.ids if not self.solo_con else [i for i in self.ids if i in self.solo_con]
        faltan = sum(max(0, self.rondas - juegos[i]) for i in quieren)
        return len(self.pares) + (faltan + 1) // 2

    # ---------- combate y etapas
    def _cargar_combate(self):
        a, b = self.pares[self.idx]
        if random.random() < 0.5:
            a, b = b, a
        self._izq, self._der = a, b
        self.etapas, self.votos, self.e = list(ETAPAS_VERSUS), {}, 0
        for cab, cid in ((self.cab_i, a), (self.cab_d, b)):
            cab.poner(self.por_id[cid], self._avatar(cid), self._chips(cid))
        self.total = self._total_estimado()
        falta = max(0, self.total - self.idx - 1)
        aprox = "~" if self.rondas else ""
        self.lbl_prog.setText(f"Combate {self.idx + 1} de {aprox}{self.total}  ·  "
                              f"{aprox}{falta} por jugar  ·  {self.ya + self.idx} ya guardados")
        self.barra.setRange(0, max(1, self.total))
        self.barra.setValue(self.idx)
        self.pila.setCurrentIndex(0)
        self.b_clas.setText("📊 Clasificación")
        self._mostrar_etapa()

    def _mostrar_etapa(self):
        clave, icono, nombre, pregunta = self.etapas[self.e]
        l, r = self._puntos()
        self.marcador.poner(l, r)
        self.banner.poner(self.etapas, self.votos, self.e)
        self.lbl_preg.setText(f"{icono}  {pregunta}")
        cg = CG_ETAPA.get(clave)
        if cg:
            k, ic, nom, col = cg
            f = self.fila_cg
            f.nombre, f.icono, f.color = nom, ic, col
            f.poner(self._datos_lado(self._izq, k), self._datos_lado(self._der, k))
            self.stack_etapa.setCurrentIndex(0)
        else:
            self.retratos.poner(self.por_id[self._izq], self._avatar_grande(self._izq),
                                self.por_id[self._der], self._avatar_grande(self._der),
                                icono, nombre)
            self.stack_etapa.setCurrentIndex(1)
        self.b_izq.setText(f"◀  Gana {self._corto(self._izq)}")
        self.b_der.setText(f"Gana {self._corto(self._der)}  ▶")
        self.b_emp.setEnabled(clave != "desempate")
        for b in (self.b_izq, self.b_der):
            b.setEnabled(True)

    def _votar(self, lado):
        """lado: -1 gana la izquierda · 1 la derecha · 0 empate / no sé."""
        if self._izq is None or self.victoria.isVisible() or self.e >= len(self.etapas):
            return
        clave = self.etapas[self.e][0]
        if clave == "desempate" and lado == 0:
            return
        self.votos[clave] = lado
        self.e += 1
        if self.e >= len(self.etapas):
            self._fin_combate()
        else:
            self._mostrar_etapa()

    def _fin_combate(self):
        l, r = self._puntos()
        self.marcador.poner(l, r)
        if l == r:                                   # empate: etapa extra para desempatar
            self.etapas.append(DESEMPATE)
            self._mostrar_etapa()
            return
        gana_izq = l > r
        g, p = (self._izq, self._der) if gana_izq else (self._der, self._izq)
        self._ganadora, self._perdedora = g, p
        tally = []
        for clave, icono, _n, _q in self.etapas:
            voto = self.votos.get(clave, 0)
            if voto == 0:
                tally.append((icono, "0"))
            else:
                lado = self._izq if voto < 0 else self._der
                tally.append((icono, "g" if lado == g else "p"))
        self.banner.poner(self.etapas, self.votos, len(self.etapas))
        self.victoria.mostrar(self.por_id[g], self._avatar_grande(g), self.por_id[p],
                              max(l, r), min(l, r), tally, self.idx + 1 >= len(self.pares))

    def _guardar_decidido(self):
        """Guarda el combate ya decidido (una sola vez). Si falla, lo MUESTRA en pantalla."""
        g, p = self._ganadora, self._perdedora
        if g is None or p is None or self._guardado == self.idx:
            return True
        etapas = {c: (self._izq if v < 0 else self._der if v > 0 else 0)
                  for c, v in self.votos.items()}
        try:
            self.guardar(g, p, etapas)               # queda guardado: esta pareja no se repite
        except Exception:
            import traceback
            texto = traceback.format_exc()
            try:
                with open(ROOT / "error.log", "a", encoding="utf-8") as f:
                    f.write(f"\n--- versus {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n{texto}")
            except Exception:
                pass
            QMessageBox.critical(self, "No se pudo guardar el combate", texto[-1800:])
            return False
        self._guardado = self.idx
        self.resultados.append((g, p, etapas))
        self.hubo = True
        return True

    def reject(self):
        # Si cierras la ventana con la pantalla de victoria a la vista, el combate YA está
        # decidido: se guarda igualmente (antes solo se guardaba al pulsar «Aceptar»).
        if self.victoria.isVisible():
            self._guardar_decidido()
        super().reject()

    def _aceptar_victoria(self):
        self._guardar_decidido()
        self.victoria.hide()
        self.idx += 1
        if self.idx >= len(self.pares) and self.rondas:          # torneo suizo: otra ronda
            self.pares.extend(generar_ronda_suiza(self.ids, self.resultados, self.rondas,
                                                  self.solo_con))
        if self.idx >= len(self.pares):
            self._fin_total()
        else:
            self._cargar_combate()

    def _atras(self):
        if self.victoria.isVisible():
            self.victoria.hide()
        if self.pila.currentIndex() == 1 and self.idx < len(self.pares):
            self.pila.setCurrentIndex(0)
            self.b_clas.setText("📊 Clasificación")
            return
        if self._izq is None or self.e <= 0 or self.idx >= len(self.pares):
            return
        self.e = min(self.e, len(self.etapas)) - 1
        clave = self.etapas[self.e][0]
        self.votos.pop(clave, None)
        if clave == "desempate":
            self.etapas.pop()
        self._mostrar_etapa()

    def _saltar(self):
        if self.idx >= len(self.pares) or self.victoria.isVisible():
            return
        if len(self.pares) - self.idx <= 1:
            self.lbl_prog.setText("Es el último combate: no hay otro al que saltar")
            return
        self.pares.append(self.pares.pop(self.idx))
        self._cargar_combate()

    # ---------- clasificación
    def _llenar_clasificacion(self):
        orden, v, d, e = clasificar(self.ids, self.resultados)
        self.lista_clas.clear()
        medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
        for k, cid in enumerate(orden, 1):
            it = self.por_id[cid]
            n = v[cid] + d[cid]
            txt = (f"{medallas.get(k, f'{k}.º')}   {it['nombre']}\n"
                   f"{v[cid]} ganados · {d[cid]} perdidos"
                   f"{f'   ·   {e[cid]} etapas ganadas' if n else '   ·   sin combates todavía'}")
            li = QListWidgetItem(QIcon(self._avatar(cid)), txt)
            li.setSizeHint(QSize(100, 62))
            self.lista_clas.addItem(li)
        self.resultado = orden
        hechos = len(self.resultados)
        todos = len(self.ids) * (len(self.ids) - 1) // 2
        if self.rondas:
            self.lbl_clas.setText(
                f"{hechos} combates jugados · torneo suizo de ~{self.rondas} combates por heroína "
                f"(no hace falta que todas peleen con todas: serían {todos}). El orden lo decide "
                f"SOLO el total de victorias; con las mismas victorias se respeta tu orden actual.")
        else:
            self.lbl_clas.setText(
                f"{hechos} de {todos} combates jugados. El orden lo decide SOLO el total de "
                f"victorias (cada versus ganado vale 1, sin importar el marcador de etapas); con "
                f"las mismas victorias se respeta tu orden actual.")

    def _alternar_clasificacion(self):
        if self.pila.currentIndex() == 0:
            self._llenar_clasificacion()
            self.pila.setCurrentIndex(1)
            self.b_clas.setText("⚔ Volver al combate" if self.idx < len(self.pares)
                                else "📊 Clasificación")
        elif self.idx < len(self.pares):
            self.pila.setCurrentIndex(0)
            self.b_clas.setText("📊 Clasificación")

    def _fin_total(self):
        self._izq = None
        self._llenar_clasificacion()
        self.pila.setCurrentIndex(1)
        self.barra.setRange(0, 1)
        self.barra.setValue(1)
        if self.rondas:
            self.lbl_prog.setText("¡Torneo completo!" if self.total
                                  else "Ya no quedan rivales nuevos para nadie")
        else:
            self.lbl_prog.setText("¡Todos contra todos completo!" if self.total
                                  else "Todas las parejas ya se enfrentaron antes")
        for b in (self.b_izq, self.b_der, self.b_emp, self.b_salta):
            b.setEnabled(False)

    def _aplicar(self):
        self._llenar_clasificacion()                 # deja el orden final en self.resultado
        self.aplicar = True
        self.accept()

    def keyPressEvent(self, e):
        k = e.key()
        if self.victoria.isVisible():
            if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space) and self.victoria.listo():
                self._aceptar_victoria()
            elif k == Qt.Key.Key_Backspace:
                self._atras()
            return
        if k == Qt.Key.Key_Backspace:
            self._atras()
        elif k == Qt.Key.Key_Left:
            self._votar(-1)
        elif k == Qt.Key.Key_Right:
            self._votar(1)
        elif k == Qt.Key.Key_Down:
            self._votar(0)
        else:
            super().keyPressEvent(e)


TRIO_COLOR = "#4dd0e1"


def colores_duelo():
    """Un color por participante del duelo (el tercero solo existe en las llaves 1 vs 1 vs 1)."""
    return [QColor(Tema.a1()), QColor(Tema.a2()), QColor(TRIO_COLOR)]


class FilaGaleriasN(FilaGalerias):
    """Duelo de CGs entre 3 heroínas (llave 1 vs 1 vs 1): una columna por heroína con hasta 3 CGs
    al azar. La que no tiene de ese tipo sale en rojo como desventaja."""

    def __init__(self, nombre, icono, color):
        super().__init__(nombre, icono, color)
        self.lados = []
        self.setFixedHeight(214)

    def poner_n(self, lados):
        self.lados = list(lados)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._zonas = []
        n = len(self.lados)
        if not n:
            p.end()
            return
        W, H = self.width(), self.height()
        gap = 12.0
        cw = (W - gap * (n - 1)) / n
        txt = QColor(Tema.c("text"))
        cantidades = [d["n"] for d in self.lados]
        mayor = max(cantidades)
        for i, d in enumerate(self.lados):
            x = i * (cw + gap)
            c = d["n"]
            if c == 0:
                col = QColor(ROJO_PELIGRO)
            elif c == mayor and cantidades.count(mayor) == 1:
                col = QColor(VERDE_VENTAJA)
            else:
                col = txt
            texto_el(p, x, 0, cw, 28, f"{self.icono}  {c}  ·  {self.nombre}",
                     fnt(Tema.tam, bold=True), col, Qt.AlignmentFlag.AlignHCenter)
            self._lado(p, QRectF(x, 30, cw, H - 30), d)
        p.end()


class RetratosN(QWidget):
    """Las 2 o 3 heroínas en grande para las etapas sin CGs (historia, final, voz…) y para los
    desempates de la llave 1 vs 1 vs 1. Clic en una para darle el punto."""
    elegir = Signal(int)                     # posición (0, 1, 2) dentro de las que se muestran

    def __init__(self):
        super().__init__()
        self.cands, self.cols = [], []
        self.icono, self.nombre = "", ""
        self._hover = -1
        self.setMouseTracking(True)
        self.setMinimumHeight(250)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def poner(self, cands, icono, nombre, colores):
        """cands: [(item, pixmap)] · colores: un color por cada una."""
        self.cands, self.cols = list(cands), list(colores)
        self.icono, self.nombre = icono, nombre
        self._hover = -1
        self.update()

    def _en(self, pos):
        n = len(self.cands)
        if not n:
            return -1
        return max(0, min(n - 1, int(pos.x() / (self.width() / n))))

    def mouseMoveEvent(self, e):
        h = self._en(e.position())
        if h != self._hover:
            self._hover = h
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.update()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._hover = -1
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.cands:
            self.elegir.emit(self._en(e.position()))

    def paintEvent(self, e):
        n = len(self.cands)
        if not n:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        a1 = QColor(Tema.a1())
        W, H = self.width(), self.height()
        cw = W / n
        texto_el(p, 0, 0, W, 40, f"{self.icono}  {self.nombre}", fnt(Tema.tam + 5, bold=True),
                 a1, Qt.AlignmentFlag.AlignHCenter)
        rad = max(46.0, min((H - 40) * 0.30, cw * 0.36, 118.0))
        cy = 40 + (H - 40) * 0.40
        for i, (it, pm) in enumerate(self.cands):
            col = self.cols[i % len(self.cols)]
            cx = cw * (i + 0.5)
            r = rad * (1.05 if self._hover == i else 1.0)
            if self._hover == i:
                for k in range(5, 0, -1):
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(con_alfa(col, 16))
                    p.drawEllipse(QPointF(cx, cy), r + k * 7, r + k * 7)
            if pm is not None and not pm.isNull():
                p.drawPixmap(QRectF(cx - r, cy - r, 2 * r, 2 * r), pm, QRectF(pm.rect()))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(col, 5 if self._hover == i else 3.5))
            p.drawEllipse(QPointF(cx, cy), r, r)
            texto_el(p, cx - cw * 0.46, cy + r + 10, cw * 0.92, 32, it["nombre"],
                     fnt(Tema.tam + 5, bold=True), txt, Qt.AlignmentFlag.AlignHCenter)
            texto_el(p, cx - cw * 0.46, cy + r + 42, cw * 0.92, 20, it.get("sub2") or "",
                     fnt(max(8.0, Tema.tam - 1)), mu, Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, 0, H - 24, W, 20, "toca a la que gana", fnt(max(8.0, Tema.tam - 2)), mu,
                 Qt.AlignmentFlag.AlignHCenter)
        p.end()


class DialogoDuelo(QDialog):
    """UN duelo del torneo, por etapas (CG favoritos, CG normal, CG H, historia, final,
    personalidad, diseño, voz y romance). Juegan 2 heroínas (1 vs 1) o 3 (llave 1 vs 1 vs 1);
    gana quien consiga más etapas y, si hay empate, se juega un desempate.
    Al aceptar la victoria se guarda el resultado (callback `guardar`)."""
    SOLO_FOTO = False             # True: duelo 1 vs 1 solo con fotos (sin etapas ni CG)

    def _etapas_iniciales(self):
        return list(ETAPAS_VERSUS)

    def __init__(self, parent, titulo, info, items, datos, guardar, es_final=False):
        super().__init__(parent)
        self.items = list(items)
        self.n = len(self.items)
        self.ids = [i["id"] for i in self.items]
        self.datos, self.guardar = datos, guardar
        self.es_final = es_final
        self.colores = colores_duelo()[:self.n]
        self.hecho = False            # el resultado ya quedó guardado
        self.seguir = False           # pulsó «Aceptar» (pasar al siguiente duelo)
        self._res = None
        self._av, self._avg = {}, {}
        self.etapas, self.votos, self.e = self._etapas_iniciales(), {}, 0
        self._cand_de = {}            # etapa de desempate -> quiénes siguen empatadas
        self._muestras = {}           # CG elegidos al azar (fijos durante el duelo)
        self.setWindowTitle(f"Torneo · {titulo}")
        self.resize(1240, 900)
        self.setMinimumSize(1000, 700)

        v = QVBoxLayout(self)
        v.setSpacing(8)
        cab = QHBoxLayout()
        t = QLabel(f"🏆 {titulo}")
        t.setObjectName("heading")
        cab.addWidget(t)
        cab.addStretch()
        lbl_info = QLabel(info)
        lbl_info.setObjectName("muted")
        cab.addWidget(lbl_info)
        v.addLayout(cab)
        if self.n == 3:
            aviso = QLabel("⚔ Llave especial 1 vs 1 vs 1: elige a la ganadora y solo "
                           "ella pasa a la siguiente ronda; las otras dos quedan eliminadas."
                           if self.SOLO_FOTO else
                           "⚔ Llave especial 1 vs 1 vs 1: gana quien consiga más etapas y solo "
                           "ella pasa a la siguiente ronda; las otras dos quedan eliminadas.")
            aviso.setObjectName("muted")
            aviso.setWordWrap(True)
            v.addWidget(aviso)

        fila = QHBoxLayout()
        fila.setSpacing(12 if self.n == 3 else 10)
        self.cabs = [CabeceraDuelista() for _ in range(self.n)]
        if self.n == 2:
            self.marcador = Marcador()
            self.marcador.etiqueta = "ETAPAS"
            fila.addWidget(self.cabs[0], 1)
            fila.addWidget(self.marcador)
            fila.addWidget(self.cabs[1], 1)
        else:
            self.marcador = None
            for c in self.cabs:
                fila.addWidget(c, 1)
        v.addLayout(fila)
        self.banner = BannerEtapas()
        v.addWidget(self.banner)
        self.lbl_preg = QLabel("")
        self.lbl_preg.setObjectName("heading")
        self.lbl_preg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.lbl_preg)

        # páginas de la etapa: 0 CG (2) · 1 retratos (2) · 2 CG (3) · 3 retratos (3)
        self.stack_etapa = QStackedWidget()
        self.fila_cg = FilaGalerias("CG favoritos", "⭐", "#ffc857")
        self.fila_cg.setFixedHeight(200)
        self.fila_cg.ver.connect(self._ver_grande)
        self.retratos2 = RetratosVersus()
        self.retratos2.elegir.connect(lambda lado: self._votar_pos(0 if lado < 0 else 1))
        self.fila_cg3 = FilaGaleriasN("CG favoritos", "⭐", "#ffc857")
        self.fila_cg3.ver.connect(self._ver_grande)
        self.retratos3 = RetratosN()
        self.retratos3.elegir.connect(self._votar_pos)
        for fila_cg in (self.fila_cg, self.fila_cg3):
            cont = QWidget()
            cl = QVBoxLayout(cont)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.addStretch()
            cl.addWidget(fila_cg)
            cl.addWidget(QLabel("<span style='opacity:0.6'>Clic en un CG para verlo en grande</span>"),
                         0, Qt.AlignmentFlag.AlignHCenter)
            cl.addStretch()
            self.stack_etapa.addWidget(cont)
            if fila_cg is self.fila_cg:
                self.stack_etapa.addWidget(self.retratos2)
        self.stack_etapa.addWidget(self.retratos3)
        v.addWidget(self.stack_etapa, 1)

        botones = QHBoxLayout()
        botones.setSpacing(8)

        def boton(texto, fn, primario=False):
            b = BotonAnimado(texto, primario=primario)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.clicked.connect(fn)
            return b
        self.b_v = [boton("", lambda _=False, i=i: self._votar_pos(i), True)
                    for i in range(self.n)]
        self.b_emp = boton("🤝 Empate / no sé", lambda _=False: self._votar_pos(-1))
        botones.addStretch()
        orden_b = ([self.b_v[0], self.b_emp, self.b_v[1]] if self.n == 2
                   else self.b_v + [self.b_emp])
        for b in orden_b:
            botones.addWidget(b)
        botones.addStretch()
        v.addLayout(botones)

        pie = QHBoxLayout()
        self.b_atras = boton("↩ Atrás", self._atras)
        pie.addWidget(self.b_atras)
        pie.addStretch()
        pie.addWidget(boton("Salir (este duelo no se guarda)", self.reject))
        v.addLayout(pie)

        self.victoria = PantallaVictoria(self)
        self.victoria.aceptar.connect(self._aceptar_victoria)
        self._precargar_cg()
        self._mostrar_etapa()

    # ---------- utilidades
    def _avatar(self, i):
        if i not in self._av:
            it = self.items[i]
            self._av[i] = avatar(it.get("foto") or "", 160, it.get("enc"))
        return self._av[i]

    def _avatar_grande(self, i):
        if i not in self._avg:
            it = self.items[i]
            self._avg[i] = avatar(it.get("foto") or "", 320, it.get("enc"))
        return self._avg[i]

    def _chips(self, i):
        d = self.datos.get(self.ids[i], {})
        n = len(d.get("fav", []))
        chips = [(f"★ {n} {'CG favorito' if n == 1 else 'CG favoritos'}", "#ffc857")
                 if n else ("⚠ Sin CG favoritos", ROJO_PELIGRO)]
        if self.n == 3:
            pts = self._pts()[i]
            chips.append((f"🏅 {pts} {'etapa' if pts == 1 else 'etapas'}", Tema.a1()))
        return chips

    def _datos_lado(self, i, clave):
        k = (self.ids[i], clave)
        if k not in self._muestras:          # se sortean una vez: «Atrás» muestra los mismos
            lista = self.datos.get(self.ids[i], {}).get(clave, [])
            self._muestras[k] = {"n": len(lista), "rutas": muestra_cg(lista)}
        return self._muestras[k]

    def _precargar_cg(self):
        """Empieza a cargar en segundo plano los CG de las etapas CG favoritos, normal y H,
        para que estén listos cuando toque cada una (la ventana no se congela)."""
        for clave in ("cg_fav", "cg_normal", "cg_h"):
            k = CG_ETAPA[clave][0]
            for i in range(self.n):
                for ruta in self._datos_lado(i, k)["rutas"]:
                    CACHE_MINI.obtener_diferido(ruta, 360)

    def _corto(self, i):
        return QFontMetrics(fnt(Tema.tam)).elidedText(
            self.items[i]["nombre"], Qt.TextElideMode.ElideRight, 230)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.victoria.isVisible():
            self.victoria.setGeometry(self.rect())

    def _ver_grande(self, ruta):
        d = QDialog(self)
        d.setWindowTitle("Captura")
        d.resize(1000, 640)
        lay = QVBoxLayout(d)
        lay.setContentsMargins(8, 8, 8, 8)
        vg = VisorGrande()
        vg.poner(ruta)
        vg.clic.connect(d.accept)
        lay.addWidget(vg)
        d.exec()

    # ---------- puntos y desempates
    def _pts(self):
        """Etapas ganadas por cada participante (los desempates no cuentan aquí)."""
        pts = [0] * self.n
        for clave, v in self.votos.items():
            if v >= 0 and not clave.startswith("desempate"):
                pts[v] += 1
        return pts

    def _pts_f(self):
        """Etapas + un pequeño bono por cada desempate ganado (solo para ordenar)."""
        pts = [float(x) for x in self._pts()]
        k = 0
        for clave, _i, _n, _q in self.etapas:
            if clave.startswith("desempate"):
                v = self.votos.get(clave, -1)
                if v >= 0:
                    pts[v] += 0.5 / (2 ** k)
                k += 1
        return pts

    def _grupo_empatado(self):
        """Quiénes siguen empatadas en un puesto que importa (o None si ya hay resultado).
        Siempre importa el 1.º; en la final de 3 importan también el 2.º y el 3.º."""
        pts = self._pts_f()
        necesarios = 3 if (self.es_final and self.n == 3) else 1
        orden = sorted(range(self.n), key=lambda i: -pts[i])
        i = 0
        while i < self.n and i < necesarios:
            j = i
            while j + 1 < self.n and pts[orden[j + 1]] == pts[orden[i]]:
                j += 1
            if j > i:
                return orden[i:j + 1]
            i = j + 1
        return None

    def _cand_actual(self):
        return self._cand_de.get(self.etapas[self.e][0], list(range(self.n)))

    # ---------- etapas
    def _mostrar_etapa(self):
        clave, icono, nombre, pregunta = self.etapas[self.e]
        cand = self._cand_actual()
        pts = self._pts()
        for i in range(self.n):
            self.cabs[i].poner(self.items[i], self._avatar(i), self._chips(i))
        if self.marcador is not None:
            self.marcador.poner(pts[0], pts[1])
        res = {c: (v + 1 if v >= 0 else 0) for c, v in self.votos.items()}
        self.banner.poner(self.etapas, res, self.e, self.colores)
        self.lbl_preg.setText(f"{icono}  {pregunta}")
        cg = CG_ETAPA.get(clave)
        if cg:
            k, ic, nom, col = cg
            f = self.fila_cg if self.n == 2 else self.fila_cg3
            f.nombre, f.icono, f.color = nom, ic, col
            if self.n == 2:
                f.poner(self._datos_lado(0, k), self._datos_lado(1, k))
                self.stack_etapa.setCurrentIndex(0)
            else:
                f.poner_n([self._datos_lado(i, k) for i in range(3)])
                self.stack_etapa.setCurrentIndex(2)
        elif len(cand) == 2:
            a, b = cand
            self.retratos2.poner(self.items[a], self._avatar_grande(a),
                                 self.items[b], self._avatar_grande(b), icono, nombre)
            self.stack_etapa.setCurrentIndex(1)
        else:
            self.retratos3.poner([(self.items[i], self._avatar_grande(i)) for i in cand],
                                 icono, nombre, [self.colores[i] for i in cand])
            self.stack_etapa.setCurrentIndex(3)
        for pos, b in enumerate(self.b_v):
            if pos < len(cand):
                nom_c = self._corto(cand[pos])
                if self.n == 2:
                    b.setText(f"◀  Gana {nom_c}" if pos == 0 else f"Gana {nom_c}  ▶")
                else:
                    b.setText(f"{pos + 1}  ·  Gana {nom_c}")
                b.setVisible(True)
                b.setEnabled(True)
            else:
                b.setVisible(False)
        self.b_emp.setEnabled(not clave.startswith("desempate"))
        self.b_atras.setEnabled(self.e > 0)

    def _votar_pos(self, pos):
        """pos: posición entre las que se muestran (0, 1, 2) · -1 empate / no sé."""
        if self.victoria.isVisible() or self.e >= len(self.etapas):
            return
        cand = self._cand_actual()
        if pos < 0:
            v = -1
        elif pos < len(cand):
            v = cand[pos]
        else:
            return
        clave = self.etapas[self.e][0]
        if clave.startswith("desempate") and v < 0:
            return
        self.votos[clave] = v
        self.e += 1
        if self.e >= len(self.etapas):
            self._fin_duelo()
        else:
            self._mostrar_etapa()

    def _fin_duelo(self):
        tie = self._grupo_empatado()
        if tie:                                      # empate en un puesto que importa
            k = sum(1 for et in self.etapas if et[0].startswith("desempate")) + 1
            clave = "desempate" if k == 1 else f"desempate{k}"
            self.etapas.append((clave, "⚖", "Desempate",
                                "Hay empate: ¿quién gana el duelo?"))
            self._cand_de[clave] = tie
            self._mostrar_etapa()
            return
        pts_f, pts = self._pts_f(), self._pts()
        orden = sorted(range(self.n), key=lambda i: (-pts_f[i], i))
        g = orden[0]
        self._res = {
            "gan": self.ids[g],
            "orden": [self.ids[i] for i in orden],
            "pts": {str(self.ids[i]): pts[i] for i in range(self.n)},
            "etapas": {c: (self.ids[v] if v >= 0 else 0) for c, v in self.votos.items()},
        }
        tally = []
        for clave, icono, _n, _q in self.etapas:
            v = self.votos.get(clave, -1)
            tally.append((icono, "0" if v < 0 else ("g" if v == g else "p")))
        otros = [i for i in orden if i != g]
        if self.SOLO_FOTO:
            tally = []
            texto = "gana el duelo a " + " y ".join(self.items[i]["nombre"] for i in otros)
        elif self.n == 2:
            texto = f"gana a {self.items[otros[0]]['nombre']}  ·  {pts[g]} – {pts[otros[0]]} en etapas"
        else:
            texto = ("gana la llave 1 vs 1 vs 1  ·  "
                     + " – ".join(str(pts[i]) for i in orden) + " en etapas")
        if self.es_final:
            titulo, boton = "¡CAMPEONA!", "Aceptar  ▶  ver el cuadro final"
        else:
            titulo, boton = None, "Aceptar  ▶  siguiente duelo"
        perd = {"nombre": " y ".join(self.items[i]["nombre"] for i in otros)}
        self.victoria.mostrar(self.items[g], self._avatar_grande(g), perd, pts[g],
                              max(pts[i] for i in otros), tally, False,
                              texto=texto, titulo=titulo, boton=boton)

    def _guardar_decidido(self):
        """Guarda el duelo ya decidido (una sola vez). Si falla, lo MUESTRA en pantalla."""
        if self.hecho:
            return True
        if not self._res:
            return False
        try:
            self.guardar(self._res)
        except Exception:
            import traceback
            texto = traceback.format_exc()
            try:
                with open(ROOT / "error.log", "a", encoding="utf-8") as f:
                    f.write(f"\n--- torneo {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n{texto}")
            except Exception:
                pass
            QMessageBox.critical(self, "No se pudo guardar el duelo", texto[-1800:])
            return False
        self.hecho = True
        return True

    def reject(self):
        # Si cierras con la pantalla de victoria a la vista, el duelo YA está decidido: se guarda.
        if self.victoria.isVisible():
            self._guardar_decidido()
        super().reject()

    def _aceptar_victoria(self):
        if self._guardar_decidido():
            self.victoria.hide()
            self.seguir = True
            self.accept()

    def _atras(self):
        if self.hecho:
            return
        if self.victoria.isVisible():
            self.victoria.hide()
            self._res = None
            self.e = len(self.etapas) - 1             # vuelve a la última etapa
            self.votos.pop(self.etapas[self.e][0], None)
            self._mostrar_etapa()
            return
        if self.e <= 0:
            return
        clave = self.etapas[self.e][0]
        if clave.startswith("desempate"):             # un desempate sin votar se descarta
            self.etapas.pop()
            self._cand_de.pop(clave, None)
        self.e -= 1
        self.votos.pop(self.etapas[self.e][0], None)
        self._mostrar_etapa()

    def keyPressEvent(self, e):
        k = e.key()
        if self.victoria.isVisible():
            if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space) and self.victoria.listo():
                self._aceptar_victoria()
            elif k == Qt.Key.Key_Backspace:
                self._atras()
            return
        if k == Qt.Key.Key_Backspace:
            self._atras()
        elif k == Qt.Key.Key_Left or k == Qt.Key.Key_1:
            self._votar_pos(0)
        elif k == Qt.Key.Key_Right:
            self._votar_pos(len(self._cand_actual()) - 1)
        elif k == Qt.Key.Key_2:
            self._votar_pos(1)
        elif k == Qt.Key.Key_3:
            self._votar_pos(2)
        elif k == Qt.Key.Key_Down:
            self._votar_pos(-1)
        else:
            super().keyPressEvent(e)


ETAPA_FOTO = ("foto", "📸", "Elige a tu favorita", "¿Quién gana este duelo?")


class DialogoDuelo1v1(DialogoDuelo):
    """Duelo 1 vs 1 (o llave 1 vs 1 vs 1) del torneo SOLO con fotos: se ven las heroínas en grande y
    haces clic en la que gana. Sin etapas, sin CG y sin consultar la base de datos de capturas,
    así no se vuelve pesado cuando agregas más heroínas."""
    SOLO_FOTO = True

    def __init__(self, parent, titulo, info, items, guardar, es_final=False):
        super().__init__(parent, titulo, info, items, {}, guardar, es_final)
        self.b_emp.setVisible(False)
        self.banner.setVisible(False)
        if self.marcador is not None:
            self.marcador.setVisible(False)

    def _etapas_iniciales(self):
        return [ETAPA_FOTO]

    def _precargar_cg(self):          # sin CG: no hay nada que precargar
        pass

    def _chips(self, i):
        return []

    def _votar_pos(self, pos):
        if pos < 0:                   # aquí no hay empate: se elige a una
            return
        super()._votar_pos(pos)


class DialogoDuelo3v3(DialogoDuelo):
    """Un versus dentro de un 3 vs 3: 2 heroínas pelean por etapas (en orden AL AZAR en cada
    versus) y cada etapa perdida le quita 1 corazón a quien la pierde; si la etapa es empate, las
    dos pierden 2. Quien llega a 0 corazones muere y el versus termina ahí. Si pasan todas las
    etapas y nadie muere, el versus termina igualmente y el torneo sortea otro. Los corazones que
    quedan se guardan. Con un 30 % de probabilidad el versus trae un EVENTO aleatorio
    (tormenta, ángel guardián…) que cambia las reglas de los corazones."""

    def __init__(self, parent, titulo, info, items, datos, vidas, caps, guardar, evento=None):
        self.vidas0 = [int(v) for v in vidas]
        self.caps = list(caps)
        self.evento = evento if evento and evento.get("k") in EVENTOS_3V3 else None
        super().__init__(parent, titulo, info, items, datos, guardar, es_final=False)
        self.marcador.etiqueta = "VIDAS"
        d = b3_dano_empate(self.evento["k"] if self.evento else None)
        cura = (EVENTOS_3V3.get(self.evento["k"]) or {}).get("cura_empate", 0) if self.evento else 0
        self.b_emp.setText(f"🤝 Empate (las dos +{cura} ❤)" if cura and not d else
                           f"🤝 Empate (las dos −{d} ❤)" if d else "🤝 Empate (sin daño)")
        if self.evento:
            self._poner_banner_evento()
        self._mostrar_etapa()

    def _etapas_iniciales(self):
        et = list(ETAPAS_VERSUS)
        random.shuffle(et)            # etapas en orden aleatorio en cada versus
        return et

    # ---------- evento
    def _lado_evento(self):
        h = (self.evento or {}).get("h")
        return self.ids.index(h) if h in self.ids else None

    def _poner_banner_evento(self):
        info = EVENTOS_3V3[self.evento["k"]]
        lado = self._lado_evento()
        quien = self.items[lado]["nombre"] if lado is not None else ""
        otra = self.items[1 - lado]["nombre"] if lado is not None else ""
        desc = (info["desc"].replace("{h}", quien).replace("{o}", otra)
                .replace("{x}", str((self.evento or {}).get("x", ""))))
        lbl = QLabel(f"⚡ EVENTO ALEATORIO  ·  {info['ico']} {info['nombre']}\n" + desc)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"background: rgba(255,255,255,0.07); border: 2px solid {info['color']};"
                          "border-radius: 12px; padding: 8px 14px; font-weight: 700;")
        self.layout().insertWidget(1, lbl)

    # ---------- corazones
    def _vidas_ahora(self):
        votos = [self.votos[c] for c, _i, _n, _q in self.etapas if c in self.votos]
        k = self.evento["k"] if self.evento else None
        return b3_vidas_versus(self.vidas0, votos, k, self._lado_evento(),
                               (self.evento or {}).get("x"))

    def _chips(self, i):
        v = self._vidas_ahora()[i]
        chips = [(f"❤ {v}", ROJO_PELIGRO if v <= 3 else "#ff6b8b")]
        if self.caps[i]:
            chips.append(("👑 Capitana", "#ffc857"))
        if self.evento and self._lado_evento() == i:
            info = EVENTOS_3V3[self.evento["k"]]
            chips.append((f"{info['ico']} {info['nombre']}", info["color"]))
        n = len(self.datos.get(self.ids[i], {}).get("fav", []))
        chips.append((f"★ {n} CG fav." if n else "⚠ Sin CG fav.",
                      "#ffc857" if n else ROJO_PELIGRO))
        return chips

    def _mostrar_etapa(self):
        super()._mostrar_etapa()
        self.marcador.poner(*self._vidas_ahora())

    def _votar_pos(self, pos):
        if self.victoria.isVisible() or self.e >= len(self.etapas) or pos >= 2:
            return
        self.votos[self.etapas[self.e][0]] = -1 if pos < 0 else pos
        self.e += 1
        if self.e >= len(self.etapas) or min(self._vidas_ahora()) <= 0:
            self._fin_duelo()
        else:
            self._mostrar_etapa()

    def _fin_duelo(self):
        v = self._vidas_ahora()
        pts = self._pts()
        muertos = [i for i in range(2) if v[i] <= 0]
        self._res = {"a": self.ids[0], "b": self.ids[1], "vidas": v, "pts": pts,
                     "etapas": {c: (self.ids[x] if x >= 0 else 0) for c, x in self.votos.items()},
                     "evento": dict(self.evento) if self.evento else None,
                     "v0": list(self.vidas0)}
        if len(muertos) == 1:
            g = 1 - muertos[0]
            titulo = "¡K.O.!"
            texto = (f"deja fuera a {self.items[muertos[0]]['nombre']}  ·  "
                     f"le quedan {v[g]} ❤")
        elif len(muertos) == 2:
            g = 0 if pts[0] >= pts[1] else 1
            titulo, texto = "¡DOBLE K.O.!", "las dos caen en la misma etapa"
        else:
            g = 0 if (v[0], pts[0]) >= (v[1], pts[1]) else 1
            titulo = "¡SOBREVIVEN LAS DOS!"
            texto = f"nadie cae  ·  {v[0]} ❤  vs  {v[1]} ❤  ·  habrá otro versus"
        tally = [(ico, "0" if self.votos[c] < 0 else ("g" if self.votos[c] == g else "p"))
                 for c, ico, _n, _q in self.etapas if c in self.votos]
        self.victoria.mostrar(self.items[g], self._avatar_grande(g),
                              {"nombre": self.items[1 - g]["nombre"]}, pts[g], pts[1 - g],
                              tally, False, texto=texto, titulo=titulo,
                              boton="Aceptar  ▶  continuar el 3 vs 3")

    def _atras(self):
        if self.hecho:
            return
        if self.victoria.isVisible():
            self.victoria.hide()
            self._res = None
            ult = max(i for i, et in enumerate(self.etapas) if et[0] in self.votos)
            self.votos.pop(self.etapas[ult][0], None)
            self.e = ult
            self._mostrar_etapa()
            return
        if self.e <= 0:
            return
        self.e -= 1
        self.votos.pop(self.etapas[self.e][0], None)
        self._mostrar_etapa()


class DialogoVictoriaEquipo(QDialog):
    """Tras ganar un duelo 3 vs 3: las 3 integrantes del equipo como victoriosas, la MVP del
    duelo y a qué ronda pasan (o la corona si fue la final)."""

    def __init__(self, parent, titulo, subtitulo, miembros, caps, mvps, jug, extra=""):
        super().__init__(parent)
        self.setWindowTitle("Victoria del equipo")
        self.resize(980, 560)
        v = QVBoxLayout(self)
        v.setSpacing(10)
        t = QLabel(titulo)
        t.setObjectName("heading")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size: 26px; font-weight: 800;")
        v.addWidget(t)
        sb = QLabel(subtitulo)
        sb.setObjectName("muted")
        sb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb.setWordWrap(True)
        v.addWidget(sb)
        fila = QHBoxLayout()
        fila.setSpacing(14)
        for h, d in miembros:
            j = info_jug(jug, h)
            card = QFrame()
            card.setObjectName("panel")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 14, 14, 14)
            cl.setSpacing(6)
            es_mvp = h in mvps
            av = QLabel()
            av.setPixmap(avatar(j.get("foto") or "", 150, parse_enc(j.get("enc"))))
            av.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(av)
            nom = QLabel((" 👑" if h in caps else "") + (j.get("nombre") or "¿?"))
            nom.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nom.setWordWrap(True)
            nom.setStyleSheet("font-size: 16px; font-weight: 700;")
            cl.addWidget(nom)
            cab = QLabel("🌟 MVP del duelo" if es_mvp else "🏆 Victoriosa")
            cab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cab.setStyleSheet("font-weight: 700; color: " + ("#eea422" if es_mvp else VERDE_GANA) + ";")
            cl.addWidget(cab)
            est = QLabel((f"❤ {d['vidas']} corazones" if d["vidas"] > 0 else "✖ cayó en este duelo")
                         + f"\n⚔ {d['ko']} K.O.  ·  {d['vs']} versus ganados"
                         + f"\n🏅 {d['etapas']} etapas ganadas")
            est.setAlignment(Qt.AlignmentFlag.AlignCenter)
            est.setObjectName("muted")
            cl.addWidget(est)
            cl.addStretch()
            if es_mvp:
                card.setStyleSheet("QFrame#panel { border: 2px solid #eea422; border-radius: 14px; }")
            fila.addWidget(card, 1)
        v.addLayout(fila, 1)
        if extra:
            ex = QLabel(extra)
            ex.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ex.setWordWrap(True)
            v.addWidget(ex)
        ok = BotonAnimado("Continuar  ▶", primario=True)
        ok.clicked.connect(self.accept)
        v.addWidget(ok, 0, Qt.AlignmentFlag.AlignHCenter)


ORO_T1, ORO_T2 = QColor(255, 236, 140), QColor(238, 164, 34)
VERDE_GANA = "#6be19b"


def info_jug(jug, hid):
    """Datos guardados de una heroína del torneo (nombre, novela, foto, encuadre)."""
    return jug.get(str(hid)) or {"nombre": "¿?", "juego": "", "foto": "", "enc": ""}


class BracketWidget(QWidget):
    """El cuadro del torneo: una columna por ronda, llaves unidas con líneas hasta la campeona.
    Cada heroína muestra en qué ronda ganó o en cuál quedó eliminada. Clic en una llave lista
    para jugarse → jugarla · clic en una ya jugada → ver el detalle por etapas."""
    jugar = Signal(int, int)
    detalle = Signal(int, int)

    CW, GAPX, MX, MY, HEAD = 268, 78, 28, 16, 66
    RH, TAG, PAD, GAPY, CH_W = 50, 24, 8, 22, 240

    def __init__(self):
        super().__init__()
        self.rondas, self.jug = [], {}
        self.activo = True
        self._pos, self._pm, self._hover = [], {}, None
        self._elim, self._pod = {}, None
        self.setMouseTracking(True)

    # ---------- datos y geometría
    def poner(self, rondas, jug, activo=True):
        self.rondas, self.jug, self.activo = rondas, jug, activo
        self._elim, self._pod = eliminadas(rondas), podio(rondas)
        self._calcular()
        self.update()

    def _alto_llave(self, n):
        return self.TAG + n * self.RH + self.PAD

    def _calcular(self):
        self._pos = []
        for r, ronda in enumerate(self.rondas):
            x = self.MX + r * (self.CW + self.GAPX)
            fila, y = [], self.MY + self.HEAD
            for ll in ronda:
                h = self._alto_llave(len(ll["ids"]))
                if r == 0:
                    rect = QRectF(x, y, self.CW, h)
                    y += h + self.GAPY
                else:
                    cs = [self._pos[r - 1][s].center().y() for s in ll["src"]]
                    cy = sum(cs) / len(cs)
                    rect = QRectF(x, cy - h / 2, self.CW, h)
                fila.append(rect)
            self._pos.append(fila)
        R = len(self.rondas)
        base = max((rc.bottom() for f in self._pos for rc in f), default=0)
        self.setMinimumSize(int(self.MX * 2 + R * (self.CW + self.GAPX) + self.CH_W),
                            int(base + self.MY + 10))

    def rect_llave(self, r, k):
        return self._pos[r][k]

    def _llave_en(self, pos):
        for r, fila in enumerate(self._pos):
            for k, rc in enumerate(fila):
                if rc.contains(pos):
                    return (r, k)
        return None

    def _pm_de(self, hid):
        if hid not in self._pm:
            j = info_jug(self.jug, hid)
            self._pm[hid] = avatar(j.get("foto") or "", 80, parse_enc(j.get("enc")))
        return self._pm[hid]

    # ---------- ratón
    def _accion(self, h):
        if h is None:
            return None
        ll = self.rondas[h[0]][h[1]]
        if llave_jugable(ll) and self.activo:
            return "jugar"
        return "detalle" if ll["gan"] else None

    def mouseMoveEvent(self, e):
        h = self._llave_en(e.position())
        h = h if self._accion(h) else None
        if h != self._hover:
            self._hover = h
            self.setCursor(Qt.CursorShape.PointingHandCursor if h else Qt.CursorShape.ArrowCursor)
            self.update()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._hover = None
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        h = self._llave_en(e.position())
        acc = self._accion(h)
        if acc == "jugar":
            self.jugar.emit(*h)
        elif acc == "detalle":
            self.detalle.emit(*h)

    # ---------- dibujo
    def _subtitulo(self, r, ll, hid):
        """(texto, color) de debajo del nombre: en qué ronda ganó o quedó eliminada."""
        mu = QColor(Tema.c("muted"))
        R = len(self.rondas)
        corto = nombre_ronda(r, self.rondas, True)
        if not ll["gan"]:
            juego = info_jug(self.jug, hid).get("juego") or ""
            return (f"📖 {juego}" if juego else "En espera"), mu
        if len(ll["ids"]) == 1 and r < R - 1:
            return "⏭ Pasa directo", QColor(VERDE_GANA)
        if hid == ll["gan"]:
            if r == R - 1:
                return "🏆 ¡Campeona!", ORO_T2
            return f"✔ Ganó en {corto}", QColor(VERDE_GANA)
        if r == R - 1 and self._pod:
            if hid in self._pod[2]:
                return "🥈 Subcampeona · perdió la Final", QColor("#c9d3e6")
            return "🥉 Tercer lugar", QColor("#eba570")
        return f"✖ Eliminada en {corto}", QColor(ROJO_PELIGRO)

    def _fila(self, p, rc, r, k, ll, i, hid, a1, a2, card, borde, txt, mu):
        y = rc.top() + self.TAG + i * self.RH
        fr = QRectF(rc.left() + 4, y, rc.width() - 8, self.RH)
        if i > 0:
            p.setPen(QPen(con_alfa(borde, 140), 1))
            p.drawLine(QPointF(rc.left() + 12, y), QPointF(rc.right() - 12, y))
        if not hid:                                   # todavía no se sabe quién llega
            p.setPen(QPen(con_alfa(borde, 220), 1.4, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            c = QPointF(fr.left() + 8 + 17, fr.center().y())
            p.drawEllipse(c, 17, 17)
            texto_el(p, c.x() - 17, c.y() - 12, 34, 24, "?", fnt(px=16, bold=True), mu,
                     Qt.AlignmentFlag.AlignHCenter)
            src = ll["src"][i] + 1 if i < len(ll["src"]) else 0
            etq = f"Ganadora del duelo {src}" if src else "Por definir"
            texto_el(p, fr.left() + 54, fr.center().y() - 11, fr.width() - 60, 22, etq,
                     fnt(px=12), mu)
            return
        j = info_jug(self.jug, hid)
        hecha = bool(ll["gan"])
        gana = hecha and ll["gan"] == hid
        pierde = hecha and not gana
        p.save()
        if pierde:
            p.setOpacity(0.55)
        if gana:
            cam = QPainterPath()
            cam.addRoundedRect(fr, 9, 9)
            g = QLinearGradient(fr.topLeft(), fr.topRight())
            g.setColorAt(0, con_alfa(ORO_T1 if r == len(self.rondas) - 1 else a1, 70))
            g.setColorAt(1, con_alfa(a2, 0))
            p.fillPath(cam, QBrush(g))
        c = QPointF(fr.left() + 8 + 17, fr.center().y())
        pm = self._pm_de(hid)
        if pm is not None and not pm.isNull():
            p.drawPixmap(QRectF(c.x() - 17, c.y() - 17, 34, 34), pm, QRectF(pm.rect()))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(ORO_T2 if gana else (QColor(ROJO_PELIGRO) if pierde else a1), 2.4 if gana else 1.8))
        p.drawEllipse(c, 17, 17)
        tx = fr.left() + 54
        tw = fr.width() - 54 - 44
        texto_el(p, tx, fr.top() + 5, tw, 22, j.get("nombre") or "¿?",
                 fnt(px=13, bold=gana), txt)
        sub, col = self._subtitulo(r, ll, hid)
        texto_el(p, tx, fr.top() + 26, tw + 36, 18, sub, fnt(px=11, bold=hecha), col)
        if hecha and len(ll["ids"]) > 1:              # etapas ganadas en este duelo
            pts = (ll.get("pts") or {}).get(str(hid), 0)
            bx = QRectF(fr.right() - 36, fr.center().y() - 13, 30, 26)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(ORO_T2 if gana else con_alfa(mu, 60))
            p.drawRoundedRect(bx, 8, 8)
            texto_el(p, bx.left(), bx.top(), bx.width(), bx.height(), str(pts),
                     fnt(px=13, bold=True), QColor(TEXTO_SOBRE_ACENTO) if gana else txt,
                     Qt.AlignmentFlag.AlignHCenter)
        p.restore()

    def _tarjeta(self, p, r, k, a1, a2, card, borde, txt, mu):
        rc = self._pos[r][k]
        ll = self.rondas[r][k]
        n = len(ll["ids"])
        listo = llave_jugable(ll) and self.activo
        hecha = bool(ll["gan"])
        hover = self._hover == (r, k)
        cam = QPainterPath()
        cam.addRoundedRect(rc, 14, 14)
        p.fillPath(cam, QBrush(mezclar(card, a1, 0.16 if listo else 0.05)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        if listo:
            p.setPen(QPen(con_alfa(a1, 80 if not hover else 130), 7))
            p.drawPath(cam)
            p.setPen(QPen(a1, 2.2))
        elif hecha:
            p.setPen(QPen(mezclar(borde, a1, 0.55 if hover else 0.35), 1.6))
        else:
            p.setPen(QPen(con_alfa(borde, 230), 1.3, Qt.PenStyle.DashLine))
        p.drawPath(cam)
        etq = f"DUELO {k + 1}"
        if n == 3:
            etq += "  ·  1 VS 1 VS 1"
        elif n == 1:
            etq += "  ·  PASE DIRECTO"
        texto_el(p, rc.left() + 14, rc.top() + 2, rc.width() - 100, self.TAG, etq,
                 fnt(px=10, bold=True, esp=1.2), QColor(TRIO_COLOR) if n == 3 else mu)
        if listo:
            f = fnt(px=10, bold=True, esp=1)
            w = QFontMetrics(f).horizontalAdvance("▶ JUGAR") + 18
            chip = QRectF(rc.right() - w - 10, rc.top() + 4, w, self.TAG - 6)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(a1)
            p.drawRoundedRect(chip, 8, 8)
            texto_el(p, chip.left(), chip.top(), chip.width(), chip.height(), "▶ JUGAR", f,
                     QColor(TEXTO_SOBRE_ACENTO), Qt.AlignmentFlag.AlignHCenter)
        elif hecha:
            texto_el(p, rc.right() - 110, rc.top() + 2, 98, self.TAG, "ver detalle  ›",
                     fnt(px=10), mu, Qt.AlignmentFlag.AlignRight)
        for i, hid in enumerate(ll["ids"]):
            self._fila(p, rc, r, k, ll, i, hid, a1, a2, card, borde, txt, mu)

    def _campeona(self, p, a1, a2, card, borde, txt, mu):
        R = len(self.rondas)
        final = self._pos[R - 1][0]
        x = self.MX + R * (self.CW + self.GAPX)
        h = 236.0
        rc = QRectF(x, final.center().y() - h / 2, self.CH_W, h)
        ll = self.rondas[-1][0]
        cam = QPainterPath()
        cam.addRoundedRect(rc, 18, 18)
        if ll["gan"]:
            g = QLinearGradient(rc.topLeft(), rc.bottomRight())
            g.setColorAt(0, mezclar(card, ORO_T1, 0.30))
            g.setColorAt(1, mezclar(card, ORO_T2, 0.18))
            p.fillPath(cam, QBrush(g))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(ORO_T2, 2.4))
        else:
            p.fillPath(cam, QBrush(mezclar(card, a1, 0.04)))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(con_alfa(borde, 230), 1.3, Qt.PenStyle.DashLine))
        p.drawPath(cam)
        cx = rc.center().x()
        p.save()
        if not ll["gan"]:
            p.setOpacity(0.35)
        dibujar_trofeo(p, QPointF(cx, rc.top() + 36), 52, ORO_T1, ORO_T2)
        p.restore()
        if ll["gan"]:
            j = info_jug(self.jug, ll["gan"])
            pm = self._pm_de(ll["gan"])
            rad = 42.0
            cy = rc.top() + 36 + 26 + rad + 6
            if pm is not None and not pm.isNull():
                p.drawPixmap(QRectF(cx - rad, cy - rad, rad * 2, rad * 2), pm, QRectF(pm.rect()))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(ORO_T2, 4))
            p.drawEllipse(QPointF(cx, cy), rad, rad)
            texto_el(p, rc.left() + 8, cy + rad + 6, rc.width() - 16, 26, j.get("nombre") or "",
                     fnt(px=16, bold=True), txt, Qt.AlignmentFlag.AlignHCenter)
            texto_el(p, rc.left() + 8, cy + rad + 32, rc.width() - 16, 18,
                     j.get("juego") or "", fnt(px=11), mu, Qt.AlignmentFlag.AlignHCenter)
            texto_el(p, rc.left(), rc.bottom() - 24, rc.width(), 18, "CAMPEONA",
                     fnt(px=11, bold=True, esp=2.5), ORO_T2, Qt.AlignmentFlag.AlignHCenter)
        else:
            texto_el(p, rc.left(), rc.center().y() - 6, rc.width(), 26, "Campeona",
                     fnt(px=17, bold=True), mu, Qt.AlignmentFlag.AlignHCenter)
            texto_el(p, rc.left(), rc.center().y() + 20, rc.width(), 20, "por definir",
                     fnt(px=12), mu, Qt.AlignmentFlag.AlignHCenter)
        # línea desde la final
        hecho = bool(ll["gan"])
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(ORO_T2 if hecho else borde, 2.4 if hecho else 1.4, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(final.right(), final.center().y()), QPointF(rc.left(), final.center().y()))

    def paintEvent(self, e):
        if not self.rondas:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        R = len(self.rondas)
        # cabeceras de cada ronda
        for r, ronda in enumerate(self.rondas):
            x = self.MX + r * (self.CW + self.GAPX)
            rc = QRectF(x, self.MY, self.CW, 46)
            final = r == R - 1
            cam = QPainterPath()
            cam.addRoundedRect(rc, 14, 14)
            g = QLinearGradient(rc.topLeft(), rc.bottomRight())
            if final:
                g.setColorAt(0, mezclar(card, ORO_T1, 0.45))
                g.setColorAt(1, mezclar(card, ORO_T2, 0.30))
            else:
                g.setColorAt(0, mezclar(card, a1, 0.30))
                g.setColorAt(1, mezclar(card, a2, 0.16))
            p.fillPath(cam, QBrush(g))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(ORO_T2 if final else a1, 1.6))
            p.drawPath(cam)
            hechas = sum(1 for ll in ronda if ll["gan"])
            texto_el(p, rc.left(), rc.top() + 3, rc.width(), 24,
                     ("🏆  " if final else "") + nombre_ronda(r, self.rondas),
                     fnt(px=15, bold=True), txt, Qt.AlignmentFlag.AlignHCenter)
            texto_el(p, rc.left(), rc.top() + 26, rc.width(), 16,
                     f"{hechas} de {len(ronda)} {'duelo' if len(ronda) == 1 else 'duelos'}",
                     fnt(px=11), mu, Qt.AlignmentFlag.AlignHCenter)
        # líneas que unen las llaves
        p.setBrush(Qt.BrushStyle.NoBrush)
        for r in range(1, R):
            for k, ll in enumerate(self.rondas[r]):
                dest = self._pos[r][k]
                xm = dest.left() - self.GAPX / 2
                for s in ll["src"]:
                    src = self._pos[r - 1][s]
                    hecho = bool(self.rondas[r - 1][s]["gan"])
                    p.setPen(QPen(a1 if hecho else borde, 2.4 if hecho else 1.4,
                                  Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                  Qt.PenJoinStyle.RoundJoin))
                    ruta = QPainterPath()
                    ruta.moveTo(src.right(), src.center().y())
                    ruta.lineTo(xm, src.center().y())
                    ruta.lineTo(xm, dest.center().y())
                    ruta.lineTo(dest.left(), dest.center().y())
                    p.drawPath(ruta)
        for r, ronda in enumerate(self.rondas):
            for k in range(len(ronda)):
                self._tarjeta(p, r, k, a1, a2, card, borde, txt, mu)
        self._campeona(p, a1, a2, card, borde, txt, mu)
        p.end()


class DialogoTorneo(QDialog):
    """Ventana del torneo de una temporada: el cuadro completo, quién va ganando y quién cayó,
    y el botón para jugar los duelos que faltan (uno tras otro)."""

    def __init__(self, app, tid):
        super().__init__(app)
        self.app, self.tid = app, tid
        d = app.cargar_torneo(tid)
        self.temporada = d["temporada"]
        self.jug, self.rondas = d["jug"], d["rondas"]
        self._preguntado = False
        self.setWindowTitle(f"Torneo · Temporada {self.temporada}")
        self.resize(1360, 900)
        self.setMinimumSize(980, 640)

        v = QVBoxLayout(self)
        v.setSpacing(8)
        cab = QHBoxLayout()
        col = QVBoxLayout()
        self.lbl_t = QLabel(f"🏆 Temporada {self.temporada}")
        self.lbl_t.setObjectName("heading")
        self.lbl_s = QLabel("")
        self.lbl_s.setObjectName("muted")
        self.lbl_s.setWordWrap(True)
        col.addWidget(self.lbl_t)
        col.addWidget(self.lbl_s)
        cab.addLayout(col, 1)
        self.b_rank = BotonAnimado("👑 Aplicar al ranking")
        self.b_rank.clicked.connect(self._aplicar_ranking)
        self.b_jugar = BotonAnimado("▶ Jugar siguiente duelo", primario=True)
        self.b_jugar.clicked.connect(lambda: self._jugar())
        cab.addWidget(self.b_rank)
        cab.addWidget(self.b_jugar)
        v.addLayout(cab)

        self.tabs = QTabWidget()
        self.bracket = BracketWidget()
        self.bracket.jugar.connect(self._jugar)
        self.bracket.detalle.connect(self._ver_detalle)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidget(self.bracket)
        self.tabs.addTab(self.scroll, "🏟  Cuadro del torneo")
        self.lista = QListWidget()
        self.lista.setIconSize(QSize(52, 52))
        self.tabs.addTab(self.lista, "📋  Recorrido de cada heroína")
        self.lista_hon = QListWidget()
        self.lista_hon.setIconSize(QSize(52, 52))
        self._tab_hon = self.tabs.addTab(self.lista_hon, "🎖  Menciones")
        self.tabs.setTabVisible(self._tab_hon, False)
        v.addWidget(self.tabs, 1)
        pie = QHBoxLayout()
        pie.addStretch()
        b_c = BotonAnimado("Cerrar", primario=False)
        b_c.clicked.connect(self.accept)
        pie.addWidget(b_c)
        v.addLayout(pie)
        self._refrescar()

    # ---------- estado
    def _nombre(self, hid):
        return info_jug(self.jug, hid).get("nombre") or "¿?"

    def _refrescar(self):
        hechas, total = jugadas_y_total(self.rondas)
        fin = torneo_terminado(self.rondas)
        n = sum(len(ll["ids"]) for ll in self.rondas[0])
        trio = any(len(ll["ids"]) == 3 for ronda in self.rondas for ll in ronda)
        extra = "  ·  incluye una llave 1 vs 1 vs 1" if trio else ""
        unidad = "equipos 3 vs 3" if es_equipos(self.jug) else "heroínas"
        if any(len(ll["ids"]) == 1 for ronda in self.rondas for ll in ronda):
            extra += "  ·  hay pases directos"
        if fin:
            camp = self._nombre(self.rondas[-1][0]["gan"])
            self.lbl_t.setText(f"🏆 Temporada {self.temporada} · terminada")
            self.lbl_s.setText(f"🥇 Campeona: {camp}  ·  {n} {unidad}  ·  {total} duelos{extra}")
        else:
            act = nombre_ronda(ronda_actual(self.rondas), self.rondas)
            self.lbl_t.setText(f"🏆 Temporada {self.temporada}")
            self.lbl_s.setText(f"{n} {unidad}  ·  ronda actual: {act}  ·  "
                               f"{hechas} de {total} duelos jugados{extra}.  "
                               f"Toca una llave marcada «▶ JUGAR» o usa el botón.")
        self.bracket.poner(self.rondas, self.jug, activo=not fin)
        self.b_jugar.setVisible(not fin)
        self.b_rank.setVisible(fin and not es_equipos(self.jug))
        self._llenar_lista()
        self._llenar_menciones()

    def _llenar_menciones(self):
        """Pestaña «Menciones»: honores del equipo campeón del 3 vs 3 (MVP, batallas más
        ganadas, CG Hentai Master…)."""
        visible = es_equipos(self.jug) and torneo_terminado(self.rondas)
        self.tabs.setTabVisible(self._tab_hon, bool(visible))
        self.lista_hon.clear()
        if not visible:
            return
        for hid, lista in honores_equipo(self.rondas, self.jug):
            j = info_jug(self.jug, hid)
            pm = avatar(j.get("foto") or "", 104, parse_enc(j.get("enc")))
            cap = " 👑" if info_jug(self.jug, self.rondas[-1][0]["gan"]).get("cap") == hid else ""
            cuerpo = ("\n".join(f"{ico} {tit}  ·  {det}" for ico, tit, det in lista)
                      if lista else "Sin menciones esta vez")
            it = QListWidgetItem(QIcon(pm), f"{self._nombre(hid)}{cap}\n{cuerpo}")
            it.setSizeHint(QSize(100, 40 + 20 * max(1, len(lista))))
            self.lista_hon.addItem(it)

    def _ir_a_pendiente(self):
        pend = llaves_pendientes(self.rondas)
        if pend:
            rc = self.bracket.rect_llave(*pend[0])
            self.scroll.ensureVisible(int(rc.center().x()), int(rc.center().y()), 260, 200)

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self._ir_a_pendiente)

    def _llenar_lista(self):
        self.lista.clear()
        elim = eliminadas(self.rondas)
        ganadas = rondas_ganadas(self.rondas)
        pod = podio(self.rondas)
        nombres = {int(k): v.get("nombre", "") for k, v in self.jug.items()}
        participantes = [i for ll in self.rondas[0] for i in ll["ids"]]
        if pod:
            orden = orden_final(self.rondas, nombres)
        else:                           # en curso: primero las que siguen, luego por ronda alcanzada
            orden = sorted(participantes, key=lambda i: (
                i in elim, -(elim[i][0] if i in elim else 0), str(nombres.get(i, "")).casefold()))
        R = len(self.rondas)
        for hid in orden:
            if pod and hid in pod[1]:
                cab = "🥇 Campeona"
            elif pod and hid in pod[2]:
                cab = "🥈 Subcampeona · perdió la Final"
            elif pod and hid in pod[3]:
                r = elim[hid][0]
                cab = ("🥉 Tercer lugar" if r == R - 1
                       else f"🥉 Tercer lugar · eliminada en {nombre_ronda(r, self.rondas)}")
            elif hid in elim:
                r, ante = elim[hid]
                cab = (f"✖ Eliminada en {nombre_ronda(r, self.rondas)}"
                       f"  (cayó ante {self._nombre(ante)})")
            else:
                cab = "⏳ Sigue en el torneo"
            g = ganadas.get(hid, [])
            det = ("✔ Ganó en: " + " · ".join(nombre_ronda(r, self.rondas, True) for r in g)
                   if g else "✔ Aún no ha ganado ningún duelo")
            if hid in elim and not g:
                det = "Perdió su primer duelo"
            j = info_jug(self.jug, hid)
            pm = avatar(j.get("foto") or "", 104, parse_enc(j.get("enc")))
            it = QListWidgetItem(QIcon(pm), f"{self._nombre(hid)}   ·   {cab}\n{det}")
            it.setSizeHint(QSize(100, 64))
            self.lista.addItem(it)

    # ---------- jugar
    def _guardar_resultado(self, r, k, res):
        rondas = json.loads(json.dumps(self.rondas))     # copia: si falla, no se toca nada
        registrar_llave(rondas, r, k, res["gan"], res["orden"], res["pts"], res["etapas"])
        self.app.guardar_torneo(self.tid, self.jug, rondas, torneo_terminado(rondas))
        self.rondas = rondas

    def _items(self, ids):
        out = []
        for hid in ids:
            j = info_jug(self.jug, hid)
            out.append({"id": hid, "nombre": j.get("nombre") or "¿?",
                        "sub2": ("📖 " + j["juego"]) if j.get("juego") else "",
                        "foto": j.get("foto") or "", "enc": parse_enc(j.get("enc")),
                        "ids": j.get("ids") or [hid]})
        return out

    def _jugar(self, r=None, k=None):
        pend = llaves_pendientes(self.rondas)
        if not pend:
            return
        if r is None or (r, k) not in pend:
            r, k = pend[0]
        while True:
            ll = self.rondas[r][k]
            if es_equipos(self.jug):                      # modalidad 3 vs 3
                fin_ll, seguir = self._jugar_equipos(r, k)
                self._refrescar()
                if torneo_terminado(self.rondas):
                    self._al_terminar()
                    break
                if not fin_ll or not seguir:
                    break
                pend = llaves_pendientes(self.rondas)
                if not pend:
                    break
                r, k = pend[0]
                continue
            items = self._items(ll["ids"])
            hechas, total = jugadas_y_total(self.rondas)
            es_final = r == len(self.rondas) - 1
            dlg = DialogoDuelo1v1(          # 1 vs 1: solo fotos, sin etapas
                self, f"Temporada {self.temporada} · {nombre_ronda(r, self.rondas)}",
                f"Duelo {k + 1} de {len(self.rondas[r])}  ·  {hechas} de {total} jugados",
                items, lambda res, r=r, k=k: self._guardar_resultado(r, k, res),
                es_final=es_final)
            dlg.exec()
            if not dlg.hecho:
                break
            self._refrescar()
            if torneo_terminado(self.rondas):
                self._al_terminar()
                break
            if not dlg.seguir:
                break
            pend = llaves_pendientes(self.rondas)
            if not pend:
                break
            r, k = pend[0]
        self._ir_a_pendiente()

    def _jugar_equipos(self, r, k):
        """Juega (o continúa) el 3 vs 3 de una llave: una serie de versus 1 vs 1 por etapas.
        Cada versus terminado se guarda, así que se puede cerrar y seguir después.
        Devuelve (llave_terminada, pulsó_aceptar)."""
        ll = self.rondas[r][k]
        ta, tb = ll["ids"]
        est = [json.loads(json.dumps(ll["b3"])) if ll.get("b3") else
               b3_crear(ll["ids"], self.jug, b3_previas(self.rondas, r, ll["ids"]))]
        nom_ronda = nombre_ronda(r, self.rondas)

        def guardar(res):
            nuevo = b3_aplicar(json.loads(json.dumps(est[0])), res)
            rondas = json.loads(json.dumps(self.rondas))     # copia: si falla, no se toca nada
            rondas[r][k]["b3"] = nuevo
            if nuevo["fin"]:
                gan, orden, pts = b3_resultado(nuevo)
                registrar_llave(rondas, r, k, gan, orden, pts, {})
            self.app.guardar_torneo(self.tid, self.jug, rondas, torneo_terminado(rondas))
            self.rondas = rondas
            est[0] = nuevo

        while True:
            b3 = est[0]
            a, b = b3["actual"]
            ev = b3.get("ev")           # evento de ESTE versus: se sortea una vez y queda guardado
            if not ev or ev.get("n") != len(b3["hist"]) or sorted(ev.get("par") or []) != sorted([a, b]):
                ev = {"n": len(b3["hist"]), "par": [a, b], "e": b3_sortear_evento(a, b)}
                b3["ev"] = ev
                self._guardar_estado_b3(r, k, b3)
            items = self._items([a, b])
            datos = self.app.datos_super_duelo([(i["id"], i["ids"]) for i in items])
            vidas = [b3["vidas"][str(a)], b3["vidas"][str(b)]]
            caps = [self.jug[str(ta)].get("cap") == a, self.jug[str(tb)].get("cap") == b]
            info = (f"{self._nombre(ta)} vs {self._nombre(tb)}  ·  versus {len(b3['hist']) + 1}  ·  "
                    f"duelo {k + 1} de {len(self.rondas[r])}")
            dlg = DialogoDuelo3v3(self, f"Temporada {self.temporada} · {nom_ronda} · 3 vs 3",
                                  info, items, datos, vidas, caps, guardar, ev.get("e"))
            dlg.exec()
            if not dlg.hecho:
                return False, False
            if est[0]["fin"]:
                self._victoria_equipo(r, est[0])
                return True, dlg.seguir
            if not dlg.seguir:
                return False, False

    def _guardar_estado_b3(self, r, k, b3):
        """Guarda el estado a medias de un 3 vs 3 (para que el evento sorteado no cambie si cierras)."""
        try:
            rondas = json.loads(json.dumps(self.rondas))
            rondas[r][k]["b3"] = json.loads(json.dumps(b3))
            self.app.guardar_torneo(self.tid, self.jug, rondas, torneo_terminado(rondas))
            self.rondas = rondas
        except Exception:
            pass

    def _victoria_equipo(self, r, b3):
        """Las 3 del equipo ganador como victoriosas, sus aportes y la MVP; pasan a la ronda
        siguiente (o son las campeonas si era la final)."""
        g = b3["fin"]
        filas, mvps = b3_mvp_duelo(b3)
        final = r == len(self.rondas) - 1
        cap = (b3.get("caps") or {}).get(str(g))
        if final:
            titulo = f"🏆 ¡{self._nombre(g)} es CAMPEONA!"
            sub = "Las 3 se coronan en la final de la temporada."
        else:
            titulo = f"🎉 ¡{self._nombre(g)} gana el duelo!"
            sub = f"Las 3 pasan a la siguiente ronda: {nombre_ronda(r + 1, self.rondas)}."
        extra = ""
        if not final and b3.get("recupera"):
            extra = (f"💊 {self._nombre(b3['recupera'])} recupera todos sus corazones para la "
                     "siguiente ronda.")
        elif not final and b3.get("sola"):
            extra = (f"🧍 Solo queda {self._nombre(b3['sola'])}: al ser la última en pie "
                     "ya no puede curarse.")
        mv = " y ".join(self._nombre(h) for h in mvps)
        if mv:
            extra = (f"🌟 MVP del duelo: {mv}" + ("\n" + extra if extra else ""))
        DialogoVictoriaEquipo(self, titulo, sub, filas, {cap}, set(mvps), self.jug, extra).exec()

    def _detalle_equipos(self, r, k):
        ll = self.rondas[r][k]
        esc = html.escape
        b3 = ll.get("b3") or {}
        cuerpo = [f"<h3>{esc(nombre_ronda(r, self.rondas))} · Duelo {k + 1} · 3 vs 3</h3>"]
        for t in ll["ids"]:
            e = self.jug.get(str(t), {})
            marca = "🏆 " if t == ll["gan"] else ""
            cuerpo.append(f"<p>{marca}<b>{esc(self._nombre(t))}</b></p><ul>")
            for h in e.get("miembros", []):
                v = (b3.get("vidas") or {}).get(str(h))
                cap = " 👑" if e.get("cap") == h else ""
                est = (" · ✖ ya estaba fuera" if v is None and b3 else
                       "" if v is None else (f" · ❤ {v}" if v > 0 else " · ✖ cayó"))
                cuerpo.append(f"<li>{esc(self._nombre(h))}{cap}{est}</li>")
            cuerpo.append("</ul>")
            if t == ll["gan"] and b3.get("recupera"):
                cuerpo.append(f"<p>💊 Recuperó todos sus ❤ para la siguiente ronda: "
                              f"<b>{esc(self._nombre(b3['recupera']))}</b></p>")
            elif t == ll["gan"] and b3.get("sola"):
                cuerpo.append(f"<p>🧍 Última en pie, sin curarse: "
                              f"<b>{esc(self._nombre(b3['sola']))}</b></p>")
        filas = []
        for n, h in enumerate(b3.get("hist", []), 1):
            va, vb = h["vidas"]
            ev = h.get("evento") or {}
            inf = EVENTOS_3V3.get(ev.get("k"))
            ev_txt = f"{inf['ico']} {esc(inf['nombre'])}" if inf else ""
            filas.append(f"<tr><td>{n}.</td><td>{esc(self._nombre(h['a']))} <b>❤{va}</b></td>"
                         f"<td>vs</td><td>{esc(self._nombre(h['b']))} <b>❤{vb}</b></td>"
                         f"<td>{ev_txt}</td></tr>")
        if filas:
            cuerpo.append("<p>Versus jugados (corazones al terminar):</p>"
                          "<table cellspacing='6'>" + "".join(filas) + "</table>")
        d = QDialog(self)
        d.setWindowTitle("Detalle del 3 vs 3")
        d.resize(560, 620)
        lay = QVBoxLayout(d)
        lbl = QLabel("".join(cuerpo))
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setWidget(lbl)
        lay.addWidget(sc, 1)
        ok = BotonAnimado("Cerrar", primario=True)
        ok.clicked.connect(d.accept)
        lay.addWidget(ok, 0, Qt.AlignmentFlag.AlignRight)
        d.exec()

    def _al_terminar(self):
        self.tabs.setCurrentIndex(0)
        if self._preguntado:
            return
        self._preguntado = True
        camp = self._nombre(self.rondas[-1][0]["gan"])
        if es_equipos(self.jug):        # el 3 vs 3 tiene su propio ranking por equipos
            QMessageBox.information(
                self, "¡Temporada terminada!",
                f"🥇 {camp} es el equipo campeón de la temporada {self.temporada}.\n\n"
                "Su resultado queda en el ranking por equipos (pestaña «3 vs 3 · equipos» de "
                "«Heroínas de heroínas»); no cambia el ranking individual 1 vs 1.")
            return
        if QMessageBox.question(
                self, "¡Temporada terminada!",
                f"🥇 {camp} es la campeona de la temporada {self.temporada}.\n\n"
                "¿Quieres aplicar este resultado al ranking de «Heroínas de heroínas»?\n"
                "(la campeona queda #1, la subcampeona #2 y las demás según hasta qué ronda "
                "llegaron)") == QMessageBox.StandardButton.Yes:
            self._aplicar_ranking()

    def _aplicar_ranking(self):
        if self.app.aplicar_torneo_a_ranking(self.tid):
            QMessageBox.information(self, "Ranking actualizado",
                                    "Listo: el ranking de «Heroínas de heroínas» ya refleja "
                                    f"la temporada {self.temporada}.")

    def _ver_detalle(self, r, k):
        ll = self.rondas[r][k]
        if len(ll["ids"]) == 1:
            QMessageBox.information(self, "Pase directo",
                                    f"{self._nombre(ll['ids'][0])} pasa directo a la siguiente "
                                    "ronda (había un número impar de participantes).")
            return
        if ll.get("b3"):
            self._detalle_equipos(r, k)
            return
        esc = html.escape
        filas = []
        claves = ["foto"] + [e[0] for e in ETAPAS_VERSUS] + sorted(
            c for c in (ll.get("etapas") or {}) if c.startswith("desempate"))
        info = {e[0]: (e[1], e[2]) for e in ETAPAS_VERSUS}
        info["foto"] = ("📸", "Foto")
        for c in claves:
            if c not in (ll.get("etapas") or {}):
                continue
            ico, nom = info.get(c, ("⚖", "Desempate"))
            w = ll["etapas"][c]
            quien = esc(self._nombre(w)) if w else "<i>empate / sin punto</i>"
            filas.append(f"<tr><td>{ico}</td><td>{esc(nom)}</td><td><b>{quien}</b></td></tr>")
        cuerpo = (f"<h3>{esc(nombre_ronda(r, self.rondas))} · Duelo {k + 1}</h3>"
                  f"<p>{' vs '.join(esc(self._nombre(i)) for i in ll['ids'])}</p>"
                  f"<p>🏆 Ganó: <b>{esc(self._nombre(ll['gan']))}</b></p>"
                  + ("" if "foto" in (ll.get("etapas") or {}) else "<p>Etapas ganadas: "
                     + " · ".join(f"{esc(self._nombre(i))} <b>{(ll.get('pts') or {}).get(str(i), 0)}</b>"
                                  for i in ll["ids"]) + "</p>")
                  + "<table cellspacing='6'>" + "".join(filas) + "</table>")
        d = QDialog(self)
        d.setWindowTitle("Detalle del duelo")
        d.resize(520, 560)
        lay = QVBoxLayout(d)
        lbl = QLabel(cuerpo)
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(lbl, 1)
        ok = BotonAnimado("Cerrar", primario=True)
        ok.clicked.connect(d.accept)
        lay.addWidget(ok, 0, Qt.AlignmentFlag.AlignRight)
        d.exec()


class PodioTemporada(QWidget):
    """Podio de UNA temporada: campeona al centro, subcampeona a la izquierda y tercer lugar a la
    derecha (si hubo semifinalistas, comparten el tercer lugar)."""
    ALTO = 372
    PED = {1: 140, 2: 108, 3: 84}

    def __init__(self):
        super().__init__()
        self.pod, self.jug, self._pm = {}, {}, {}
        self.setFixedHeight(self.ALTO)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def poner(self, pod, jug):
        self.pod, self.jug, self._pm = pod or {}, jug or {}, {}
        self.update()

    def _pm_de(self, hid):
        if hid not in self._pm:
            j = info_jug(self.jug, hid)
            self._pm[hid] = avatar(j.get("foto") or "", 160, parse_enc(j.get("enc")))
        return self._pm[hid]

    def _avatar(self, p, hid, cx, cy, rad, c1, c2, ancho_pen):
        pm = self._pm_de(hid)
        if pm is not None and not pm.isNull():
            p.drawPixmap(QRectF(cx - rad, cy - rad, rad * 2, rad * 2), pm, QRectF(pm.rect()))
        g = QLinearGradient(cx - rad, cy - rad, cx + rad, cy + rad)
        g.setColorAt(0, QColor(c1))
        g.setColorAt(1, QColor(c2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QBrush(g), ancho_pen))
        p.drawEllipse(QPointF(cx, cy), rad, rad)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        W, H = self.width(), self.height()
        ped_w = max(130.0, min(250.0, W * 0.26))
        mid = W / 2
        centros = {1: mid, 2: mid - ped_w - 14, 3: mid + ped_w + 14}
        sobre = QColor(TEXTO_SOBRE_ACENTO)
        for rank in (2, 1, 3):
            lista = self.pod.get(rank) or []
            c1, c2, titulo = PODIO[rank]
            ph = self.PED[rank]
            cx = centros[rank]
            ped = QRectF(cx - ped_w / 2, H - 8 - ph, ped_w, ph)
            cam = QPainterPath()
            cam.addRoundedRect(ped, 14, 14)
            g = QLinearGradient(ped.topLeft(), ped.bottomLeft())
            g.setColorAt(0, QColor(c1))
            g.setColorAt(1, QColor(c2))
            p.fillPath(cam, QBrush(g))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(255, 255, 255, 130), 1.5))
            p.drawPath(cam)
            texto_el(p, ped.left(), ped.top() + 4, ped_w, ph * 0.58, str(rank),
                     fnt(px=int(ph * 0.5), bold=True), con_alfa(sobre, 200),
                     Qt.AlignmentFlag.AlignHCenter)
            texto_el(p, ped.left(), ped.bottom() - 28, ped_w, 22, titulo,
                     fnt(px=11, bold=True, esp=1.6), sobre, Qt.AlignmentFlag.AlignHCenter)
            if not lista:
                continue
            franja = 26.0
            nombre_top = ped.top() - 4 - franja
            n = len(lista)
            if n == 1:
                rad = {1: 58.0, 2: 46.0, 3: 40.0}[rank]
                cy = nombre_top - 6 - rad
                if rank == 1:
                    for k in range(6, 0, -1):
                        p.setPen(Qt.PenStyle.NoPen)
                        p.setBrush(con_alfa(ORO_T2, 14))
                        p.drawEllipse(QPointF(cx, cy), rad + k * 8, rad + k * 8)
                    dibujar_trofeo(p, QPointF(cx, cy - rad - 28), 56, ORO_T1, ORO_T2)
                self._avatar(p, lista[0], cx, cy, rad, c1, c2, 5 if rank == 1 else 4)
                texto_el(p, cx - ped_w / 2 - 24, nombre_top, ped_w + 48, franja,
                         info_jug(self.jug, lista[0]).get("nombre") or "",
                         fnt(Tema.tam + 1, bold=True), txt, Qt.AlignmentFlag.AlignHCenter)
            else:                                    # puesto compartido (semifinalistas)
                slot = ped_w * 1.15 / n * (1.0 if n == 2 else 1.1)
                x0 = cx - slot * n / 2
                rad = min(34.0, slot * 0.4)
                cy = nombre_top - 6 - rad
                for i, hid in enumerate(lista):
                    scx = x0 + slot * (i + 0.5)
                    self._avatar(p, hid, scx, cy, rad, c1, c2, 3)
                    texto_el(p, scx - slot / 2, nombre_top, slot, franja,
                             info_jug(self.jug, hid).get("nombre") or "",
                             fnt(px=11, bold=True), txt, Qt.AlignmentFlag.AlignHCenter)
        p.end()


class PodioEquipo(PodioTemporada):
    """Podio de una temporada 3 vs 3: solo el equipo campeón completo (sus 3 integrantes)."""
    ALTO = 340

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        sobre = QColor(TEXTO_SOBRE_ACENTO)
        W, H = self.width(), self.height()
        tid = (self.pod.get(1) or [0])[0]
        eq = info_jug(self.jug, tid)
        miembros = eq.get("miembros") or []
        if not tid or not miembros:
            p.end()
            return
        c1, c2, _t = PODIO[1]
        mid = W / 2
        pw, ph = max(260.0, min(620.0, W * 0.7)), 68.0
        ped = QRectF(mid - pw / 2, H - 8 - ph, pw, ph)
        cam = QPainterPath()
        cam.addRoundedRect(ped, 14, 14)
        g = QLinearGradient(ped.topLeft(), ped.bottomLeft())
        g.setColorAt(0, QColor(c1))
        g.setColorAt(1, QColor(c2))
        p.fillPath(cam, QBrush(g))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 130), 1.5))
        p.drawPath(cam)
        texto_el(p, ped.left(), ped.top() + 8, pw, 28, eq.get("nombre") or "Equipo",
                 fnt(Tema.tam + 3, bold=True), sobre, Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, ped.left(), ped.bottom() - 28, pw, 22, "EQUIPO CAMPEÓN",
                 fnt(px=11, bold=True, esp=2.0), sobre, Qt.AlignmentFlag.AlignHCenter)
        franja = 26.0
        nombre_top = ped.top() - 4 - franja
        n = len(miembros)
        slot = min(pw / n, 210.0)
        x0 = mid - slot * n / 2
        rad = min(52.0, slot * 0.34)
        cy = nombre_top - 6 - rad
        for k in range(6, 0, -1):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(con_alfa(ORO_T2, 12))
            p.drawEllipse(QPointF(mid, cy), slot * n / 2 * 0.9 + k * 6, rad + k * 7)
        dibujar_trofeo(p, QPointF(mid, cy - rad - 34), 52, ORO_T1, ORO_T2)
        for i, hid in enumerate(miembros):
            scx = x0 + slot * (i + 0.5)
            self._avatar(p, hid, scx, cy, rad, c1, c2, 5)
            nom = (info_jug(self.jug, hid).get("nombre") or "")
            if hid == eq.get("cap"):
                nom = "👑 " + nom
            texto_el(p, scx - slot / 2, nombre_top, slot, franja, nom,
                     fnt(Tema.tam + 1, bold=True), txt, Qt.AlignmentFlag.AlignHCenter)
        p.end()


class DialogoSuperDuelo(QDialog):
    """Duelo entre dos heroínas con todo lo que ayuda a decidir: criterios (historia, H, final…),
    cantidad de CGs favoritos, y un duelo de CG normal y otro de CG H (3 al azar de cada una; en
    rojo si a una le falta). Mismo ranking por inserción binaria que el duelo rápido."""

    def __init__(self, parent, titulo, items, datos, ultimas=0):
        super().__init__(parent)
        self.items = items
        self.por_id = {i["id"]: i for i in items}
        self.datos = datos
        self.log = []                  # duelos decididos: (ganadora, perdedora)
        self.log_crit = []             # puntos por criterio: (ganadora, perdedora, criterio)
        self.resultado = [i["id"] for i in items]
        self._av = {}
        self.setWindowTitle(f"Súper duelo · {titulo}")
        self.resize(1200, 900)
        self.setMinimumSize(980, 660)
        v = QVBoxLayout(self)
        v.setSpacing(8)
        cab = QHBoxLayout()
        t = QLabel("⚔ Súper duelo")
        t.setObjectName("heading")
        cab.addWidget(t)
        cab.addStretch()
        self.lbl_prog = QLabel("")
        self.lbl_prog.setObjectName("muted")
        cab.addWidget(self.lbl_prog)
        v.addLayout(cab)
        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        self.barra.setFixedHeight(10)
        v.addWidget(self.barra)

        cont = QWidget()
        cv = QVBoxLayout(cont)
        cv.setContentsMargins(0, 0, 6, 0)
        cv.setSpacing(8)
        fila = QHBoxLayout()
        fila.setSpacing(10)
        self.cab_i, self.marcador, self.cab_d = CabeceraDuelista(), Marcador(), CabeceraDuelista()
        fila.addWidget(self.cab_i, 1)
        fila.addWidget(self.marcador)
        fila.addWidget(self.cab_d, 1)
        cv.addLayout(fila)
        self.filas = {}
        for clave, icono, nombre, color in (("fav", "⭐", "CG favoritos", "#ffc857"),
                                            ("normal", "🖼", "CG normal", CAT_COLOR["CG normal"]),
                                            ("h", "🔞", "CG H", CAT_COLOR["CG H"])):
            f = FilaGalerias(nombre, icono, color)
            f.ver.connect(self._ver_grande)
            cv.addWidget(f)
            self.filas[clave] = f
        self.criterios = PanelCriterios()
        self.criterios.cambio.connect(self._actualizar_marcador)
        cv.addWidget(self.criterios)
        cv.addStretch()
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setWidget(cont)
        v.addWidget(sc, 1)

        botones = QHBoxLayout()
        botones.setSpacing(8)

        def boton(texto, fn, primario=False):
            b = BotonAnimado(texto, primario=primario)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.clicked.connect(fn)
            return b
        self.b_izq = boton("◀  Gana la de la izquierda", lambda: self._elegir(True))
        self.b_ok = boton("✔ Confirmar según criterios", self._confirmar, True)
        self.b_no = boton("No sé", lambda: self._elegir(None))
        self.b_der = boton("Gana la de la derecha  ▶", lambda: self._elegir(False))
        botones.addStretch()
        for b in (self.b_izq, self.b_ok, self.b_no, self.b_der):
            botones.addWidget(b)
        botones.addStretch()
        v.addLayout(botones)
        pie = QHBoxLayout()
        self.b_atras = boton("↩ Atrás", self._atras)
        pie.addWidget(self.b_atras)
        pie.addStretch()
        pie.addWidget(boton("Cancelar", self.reject))
        pie.addWidget(boton("Aplicar ranking", self._aplicar, True))
        v.addLayout(pie)

        ids = [it["id"] for it in items]
        self.base = ids[:-ultimas] if ultimas else []
        self.pend = ids[-ultimas:] if ultimas else ids[:]
        random.shuffle(self.pend)
        if not self.base and self.pend:
            self.base = [self.pend.pop(0)]
        self.x = None
        self.lo = self.hi = self.hechos = 0
        self.hist = []
        tot, tam = 0, len(self.base)
        for _ in self.pend:
            tot += ceil(log2(tam + 1)) if tam else 0
            tam += 1
        self.total = tot
        self.barra.setRange(0, max(1, tot))
        self._nuevo_x()

    # ---------- presentación
    def _ver_grande(self, ruta):
        d = QDialog(self)
        d.setWindowTitle("Captura")
        d.resize(1000, 640)
        lay = QVBoxLayout(d)
        lay.setContentsMargins(8, 8, 8, 8)
        vg = VisorGrande()
        vg.poner(ruta)
        vg.clic.connect(d.accept)
        lay.addWidget(vg)
        d.exec()

    def _avatar(self, cid):
        if cid not in self._av:
            it = self.por_id[cid]
            self._av[cid] = avatar(it.get("foto") or "", 160, it.get("enc"))
        return self._av[cid]

    def _chips(self, cid):
        it, d = self.por_id[cid], self.datos.get(cid, {})
        n = len(d.get("fav", []))
        chips = [(f"★ {n} {'CG favorito' if n == 1 else 'CG favoritos'}", "#ffc857")
                 if n else ("⚠ Sin CG favoritos", ROJO_PELIGRO)]
        if it.get("v", 0) + it.get("d", 0):
            chips.append((f"⚔ {it['v']}V · {it['d']}D", Tema.a1()))
        return chips

    def _datos_lado(self, cid, clave):
        lista = self.datos.get(cid, {}).get(clave, [])
        return {"n": len(lista), "rutas": muestra_cg(lista)}

    def _mostrar_duelo(self):
        mid = (self.lo + self.hi) // 2
        self._x_izq = random.random() < 0.5
        a, b = self.x, self.base[mid]
        self._izq, self._der = (a, b) if self._x_izq else (b, a)
        for cab, cid in ((self.cab_i, self._izq), (self.cab_d, self._der)):
            cab.poner(self.por_id[cid], self._avatar(cid), self._chips(cid))
        for clave, fila in self.filas.items():              # CGs al azar, distintos en cada duelo
            fila.poner(self._datos_lado(self._izq, clave), self._datos_lado(self._der, clave))
        self.criterios.reset()
        self.barra.setValue(min(self.hechos, self.total))
        restan = len(self.pend)
        self.lbl_prog.setText(f"Duelo {self.hechos + 1}  ·  {restan} heroína"
                              f"{'' if restan == 1 else 's'} más por colocar después de esta")
        for b_ in (self.b_izq, self.b_no, self.b_der):
            b_.setEnabled(True)
        self._actualizar_marcador()

    def _actualizar_marcador(self):
        l, r = self.criterios.puntos()
        self.marcador.poner(l, r)
        if self.x is None:
            return
        if l == r:
            self.b_ok.setText("Empate: usa un desempate")
            self.b_ok.setEnabled(False)
        else:
            self.b_ok.setText(f"✔ Confirmar: gana {'la izquierda' if l > r else 'la derecha'}"
                              f"  ({max(l, r)}–{min(l, r)})")
            self.b_ok.setEnabled(True)
        self.b_ok.updateGeometry()

    def _fin(self):
        self.x = None
        for cab in (self.cab_i, self.cab_d):
            cab.poner(None, None, [])
        for f in self.filas.values():
            f.poner({"n": 0, "rutas": []}, {"n": 0, "rutas": []})
        self.barra.setValue(self.barra.maximum())
        self.lbl_prog.setText("¡Listo! Pulsa «Aplicar ranking»")
        for b_ in (self.b_izq, self.b_ok, self.b_no, self.b_der):
            b_.setEnabled(False)

    # ---------- inserción binaria
    def _nuevo_x(self):
        if not self.pend:
            self._fin()
            return
        self.x = self.pend.pop(0)
        self.lo, self.hi = 0, len(self.base)
        if self.lo >= self.hi:
            self.base.insert(0, self.x)
            self._nuevo_x()
            return
        self._mostrar_duelo()

    def _confirmar(self):
        l, r = self.criterios.puntos()
        if l != r:
            self._elegir(l > r)

    def _elegir(self, izquierda):
        """True = gana la izquierda · False = la derecha · None = no sé (no cuenta)."""
        if self.x is None:
            return
        self.hist.append((list(self.base), list(self.pend), self.x, self.lo, self.hi,
                          self.hechos, len(self.log), len(self.log_crit)))
        mid = (self.lo + self.hi) // 2
        gana_x = None if izquierda is None else (izquierda == self._x_izq)
        if gana_x is not None:
            rival = self.base[mid]
            self.log.append((self.x, rival) if gana_x else (rival, self.x))
            for clave, voto in self.criterios.votos.items():   # los puntos por criterio se guardan
                if voto:
                    g, pe = (self._izq, self._der) if voto < 0 else (self._der, self._izq)
                    self.log_crit.append((g, pe, clave))
        if gana_x:
            self.hi = mid
        else:
            self.lo = mid + 1
        self.hechos += 1
        if self.lo >= self.hi:
            self.base.insert(self.lo, self.x)
            self._nuevo_x()
        else:
            self._mostrar_duelo()

    def _atras(self):
        if self.hist:
            (self.base, self.pend, self.x, self.lo, self.hi,
             self.hechos, nlog, ncrit) = self.hist.pop()
            del self.log[nlog:]
            del self.log_crit[ncrit:]
            self.base, self.pend = list(self.base), list(self.pend)
            self._mostrar_duelo()

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key.Key_Backspace:
            self._atras()
        elif k == Qt.Key.Key_Left:
            self._elegir(True)
        elif k == Qt.Key.Key_Right:
            self._elegir(False)
        elif k == Qt.Key.Key_Down:
            self._elegir(None)
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirmar()
        else:
            super().keyPressEvent(e)

    def _aplicar(self):
        b = list(self.base)
        if self.x is not None:                  # duelo a medias: se queda donde va
            b.insert(self.lo, self.x)
        self.resultado = b + list(self.pend)
        self.accept()


class DialogoTarjeta(QDialog):
    """Nombre + imagen con vista previa (novelas y heroínas)."""

    def __init__(self, parent, titulo, etiqueta, nombre="", imagen="",
                 nombre_editable=True, mostrar_general=False, info="", enc=None,
                 invertir=False, sanear=True):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.resize(680, 440)
        self._inv_orig = self._inv_res = None
        self._sanear = sanear
        self.imagen = imagen
        self.cambio_imagen = False

        raiz = QHBoxLayout(self)
        raiz.setSpacing(18)
        self.preview = CoverWidget("", 280, editable=True, pista=True)
        self.preview.setMinimumWidth(240)
        self.preview.poner(imagen, None, enc)
        raiz.addWidget(self.preview, 2)

        der = QVBoxLayout()
        cab = QLabel(titulo)
        cab.setObjectName("heading")
        der.addWidget(cab)
        der.addSpacing(8)
        der.addWidget(QLabel(etiqueta))
        self.edit = QLineEdit(nombre)
        self.edit.setEnabled(nombre_editable)
        if invertir:        # solo al poner el nombre de una heroína: ⇄ apellido / nombre
            fila_n = QHBoxLayout()
            fila_n.setSpacing(8)
            fila_n.addWidget(self.edit, 1)
            b_inv = BotonAnimado("⇄ Invertir")
            b_inv.setAutoDefault(False)
            b_inv.clicked.connect(self.invertir_nombre)
            fila_n.addWidget(b_inv)
            der.addLayout(fila_n)
        else:
            der.addWidget(self.edit)
        der.addSpacing(8)

        b_img = BotonAnimado("🖼  Elegir imagen")
        b_img.clicked.connect(self.elegir)
        der.addWidget(b_img)
        b_quitar = BotonAnimado("Quitar imagen")
        b_quitar.clicked.connect(self.quitar)
        der.addWidget(b_quitar)
        if mostrar_general:
            b_gen = BotonAnimado("Usar «General» (sin heroína)")
            b_gen.clicked.connect(lambda: self.edit.setText("General"))
            der.addWidget(b_gen)
        der.addStretch()

        fila = QHBoxLayout()
        fila.addStretch()
        b_c = BotonAnimado("Cancelar")
        b_c.clicked.connect(self.reject)
        b_g = BotonAnimado("Guardar", primario=True)
        b_g.clicked.connect(self.guardar)
        fila.addWidget(b_c)
        fila.addWidget(b_g)
        der.addLayout(fila)
        raiz.addLayout(der, 3)

    def elegir(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Elegir imagen", str(Path.home()), FILTRO_IMG)
        if ruta:
            self.imagen = ruta
            self.cambio_imagen = True
            self.preview.poner(ruta, None, ENC0)

    def quitar(self):
        self.imagen = ""
        self.cambio_imagen = True
        self.preview.poner("", None, ENC0)

    def invertir_nombre(self):
        """'Apellido Nombre' <-> 'Nombre Apellido'. Con 3 o más palabras pasa la primera al
        final. Pulsarlo otra vez devuelve el nombre tal como estaba."""
        txt = " ".join(self.edit.text().split())
        if not txt:
            return
        if self._inv_res is not None and txt == self._inv_res:
            nuevo = self._inv_orig
        else:
            pal = txt.split(" ")
            if len(pal) < 2:
                return
            nuevo = " ".join(pal[1:] + pal[:1])
            self._inv_orig, self._inv_res = txt, nuevo
        self.edit.setText(nuevo)
        self.edit.setFocus()

    def guardar(self):
        if not self.nombre():
            QMessageBox.information(self, "Nombre", "Escribe un nombre.")
            return
        self.accept()

    def nombre(self):
        txt = self.edit.text().strip()
        return nombre_seguro(txt) if self._sanear else nombre_visible(txt)

    @property
    def encuadre(self):
        return self.preview.enc


class DialogoInfoHeroina(QDialog):
    """Apodo(s), cumpleaños, seiyuu, altura y medidas (busto, cintura, caderas) de una heroína."""

    def __init__(self, parent, nombre, cumple="", seiyuu="", sugerencias=(),
                 altura=0, busto=0, cintura=0, cadera=0, apodos=""):
        super().__init__(parent)
        self.setWindowTitle(f"Información de {nombre}")
        self.resize(560, 560)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        cab = QLabel(f"✎ {nombre}")
        cab.setObjectName("heading")
        lay.addWidget(cab)
        form = QFormLayout()
        form.setVerticalSpacing(14)

        fila = QHBoxLayout()
        self.s_dia = QComboBox()                 # desplegable: eliges el día con un clic
        self.s_dia.addItem("—")
        self.s_dia.addItems([str(i) for i in range(1, 32)])
        self.s_dia.setMaxVisibleItems(12)
        self.c_mes = QComboBox()
        self.c_mes.addItem("—")
        self.c_mes.addItems([m.capitalize() for m in MESES_ES])
        m = re.match(r"\s*(\d{1,2}) de (\w+)", cumple or "")
        if m and m.group(2).lower() in MESES_ES:
            self.s_dia.setCurrentIndex(min(31, max(0, int(m.group(1)))))
            self.c_mes.setCurrentIndex(MESES_ES.index(m.group(2).lower()) + 1)
        elif (cumple or "").lower() in MESES_ES:
            self.c_mes.setCurrentIndex(MESES_ES.index(cumple.lower()) + 1)
        fila.addWidget(self.s_dia)
        fila.addWidget(QLabel("de"))
        fila.addWidget(self.c_mes, 1)
        form.addRow("Cumpleaños:", fila)
        self.e_apodos = QLineEdit(texto_apodos(apodos))
        self.e_apodos.setPlaceholderText("Ej.: Nana, Nanako, Nana-chan  (sepáralos con comas)")
        form.addRow("Apodo(s):", self.e_apodos)
        # Menos clics: al elegir el día se abre solo la lista de meses (si aún no hay mes)
        self.s_dia.activated.connect(
            lambda _i: QTimer.singleShot(0, self.c_mes.showPopup)
            if self.c_mes.currentIndex() == 0 else None)
        self.c_mes.currentIndexChanged.connect(self._ajustar_dia)

        self.e_cv = QLineEdit(seiyuu)
        self.e_cv.setPlaceholderText("Ej.: Hanazawa Kana")
        if sugerencias:                       # mismo nombre = misma seiyuu en «Info heroínas»
            comp = QCompleter(list(sugerencias), self.e_cv)
            comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            comp.setFilterMode(Qt.MatchFlag.MatchContains)
            self.e_cv.setCompleter(comp)
        form.addRow("Seiyuu (actriz de voz):", self.e_cv)
        lay.addLayout(form)

        # ---- altura y medidas: escribir cada número o pegar el texto de VNDB / wiki
        caja = QFrame()
        caja.setObjectName("panel")
        cl = QVBoxLayout(caja)
        cl.setContentsMargins(14, 12, 14, 14)
        cl.setSpacing(10)
        t = QLabel("📏 Altura y medidas")
        t.setObjectName("heading")
        cl.addWidget(t)
        pega = QHBoxLayout()
        self.e_pegar = QLineEdit()
        self.e_pegar.setPlaceholderText(
            "Pega aquí: Altura: 158 cm. Medidas de busto, cintura y caderas: 90-59-88 cm.")
        self.e_pegar.textChanged.connect(self._leer_texto)
        b_pegar = BotonAnimado("📋 Pegar")
        b_pegar.setAutoDefault(False)
        b_pegar.setToolTip("Pega el texto copiado y se rellenan solos los cuatro números")
        b_pegar.clicked.connect(self._pegar)
        pega.addWidget(self.e_pegar, 1)
        pega.addWidget(b_pegar)
        cl.addLayout(pega)
        cifras = QHBoxLayout()
        cifras.setSpacing(10)
        self.s_alt = self._spin(altura, 250)
        self.s_bus = self._spin(busto, 200)
        self.s_cin = self._spin(cintura, 200)
        self.s_cad = self._spin(cadera, 200)
        for etiqueta, spin in (("Altura", self.s_alt), ("Busto", self.s_bus),
                               ("Cintura", self.s_cin), ("Cadera", self.s_cad)):
            col = QVBoxLayout()
            col.setSpacing(4)
            lb = QLabel(etiqueta)
            lb.setObjectName("muted")
            col.addWidget(lb)
            col.addWidget(spin)
            cifras.addLayout(col, 1)
        cl.addLayout(cifras)
        self.lbl_prev = QLabel("")
        self.lbl_prev.setWordWrap(True)
        cl.addWidget(self.lbl_prev)
        self.lbl_extra = QLabel("")
        self.lbl_extra.setObjectName("muted")
        self.lbl_extra.setWordWrap(True)
        cl.addWidget(self.lbl_extra)
        lay.addWidget(caja)
        lay.addStretch()

        botones = QHBoxLayout()
        b_borrar = BotonAnimado("Vaciar todo")
        b_borrar.setAutoDefault(False)
        b_borrar.clicked.connect(self.vaciar)
        b_c = BotonAnimado("Cancelar")
        b_c.setAutoDefault(False)
        b_c.clicked.connect(self.reject)
        b_g = BotonAnimado("Guardar", primario=True)
        b_g.setDefault(True)
        b_g.clicked.connect(self.guardar)
        botones.addWidget(b_borrar)
        botones.addStretch()
        botones.addWidget(b_c)
        botones.addWidget(b_g)
        lay.addLayout(botones)
        self._actualizar()

    def _spin(self, valor, tope):
        s = QSpinBox()
        s.setRange(0, tope)
        s.setSuffix(" cm")
        s.setSpecialValueText("—")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.setValue(int(valor or 0))
        s.valueChanged.connect(self._actualizar)
        return s

    def _pegar(self):
        self.e_pegar.setText(QApplication.clipboard().text().strip())

    def _leer_texto(self, texto):
        """Rellena las casillas con lo que entienda del texto pegado."""
        alt, bus, cin, cad = parsear_cuerpo(texto)
        if alt:
            self.s_alt.setValue(alt)
        if bus:
            self.s_bus.setValue(bus)
            self.s_cin.setValue(cin)
            self.s_cad.setValue(cad)

    def _actualizar(self, *_):
        a, b, c, h = (self.s_alt.value(), self.s_bus.value(),
                      self.s_cin.value(), self.s_cad.value())
        self.lbl_prev.setText(texto_cuerpo(a, b, c, h) or
                              "Escribe la altura y las medidas, o pega el texto de arriba.")
        if medidas_completas(b, c, h):
            self.lbl_extra.setText(f"Cintura/cadera: {c / h:.2f}  ·  silueta «reloj de arena»: "
                                   f"{puntaje_reloj(b, c, h)}/100")
        else:
            self.lbl_extra.setText("Para las medidas hacen falta las tres: busto, cintura y cadera.")

    def _ajustar_dia(self, *_):
        """No deja un 31 de abril ni un 30 de febrero."""
        mes = self.c_mes.currentIndex()
        tope = {2: 29, 4: 30, 6: 30, 9: 30, 11: 30}.get(mes, 31)
        if self.s_dia.currentIndex() > tope:
            self.s_dia.setCurrentIndex(tope)

    def vaciar(self):
        self.e_pegar.clear()
        self.e_apodos.clear()
        self.e_cv.clear()
        self.s_dia.setCurrentIndex(0)
        self.c_mes.setCurrentIndex(0)
        for s in (self.s_alt, self.s_bus, self.s_cin, self.s_cad):
            s.setValue(0)

    def guardar(self):
        a, med = self.s_alt.value(), (self.s_bus.value(), self.s_cin.value(), self.s_cad.value())
        if 0 < a < 80:
            QMessageBox.information(self, "Altura", "La altura parece muy baja: escríbela en cm "
                                                    "(por ejemplo 158).")
            return
        if any(0 < v < 40 for v in med):
            QMessageBox.information(self, "Medidas", "Alguna medida parece muy baja: escríbelas "
                                                     "en cm (por ejemplo 90, 59 y 88).")
            return
        if any(med) and not all(med):
            QMessageBox.information(self, "Medidas", "Para guardar las medidas hacen falta las "
                                                     "tres: busto, cintura y cadera.")
            return
        self.accept()

    def valores(self):
        dia, mes = self.s_dia.currentIndex(), self.c_mes.currentIndex()
        if mes and dia:
            cumple = f"{dia} de {MESES_ES[mes - 1]}"
        elif mes:
            cumple = MESES_ES[mes - 1]
        else:
            cumple = ""
        return (cumple, self.e_cv.text().strip(), self.s_alt.value(),
                self.s_bus.value(), self.s_cin.value(), self.s_cad.value(),
                texto_apodos(self.e_apodos.text()))


class FilasTexto(QWidget):
    """Lista de casillas de texto SIN límite: «＋ Añadir» agrega otra y «✕» quita la fila."""

    def __init__(self, valores=(), pista="", etiqueta_add="＋ Añadir"):
        super().__init__()
        self._pista = pista
        self.col = QVBoxLayout(self)
        self.col.setContentsMargins(0, 0, 0, 0)
        self.col.setSpacing(6)
        self.caja = QVBoxLayout()
        self.caja.setSpacing(6)
        self.col.addLayout(self.caja)
        self.filas = []
        for v in valores:
            self.agregar(v)
        if not self.filas:
            self.agregar("")
        b = BotonAnimado(etiqueta_add)
        b.setAutoDefault(False)
        b.clicked.connect(lambda *_: self.agregar("", foco=True))
        fila = QHBoxLayout()
        fila.addWidget(b)
        fila.addStretch()
        self.col.addLayout(fila)

    def agregar(self, texto="", foco=False):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        e = QLineEdit(texto)
        e.setPlaceholderText(self._pista)
        q = BotonAnimado("✕")
        q.setAutoDefault(False)
        q.setFixedWidth(40)
        q.setToolTip("Quitar")
        q.clicked.connect(lambda *_: self._quitar(w))
        h.addWidget(e, 1)
        h.addWidget(q)
        self.caja.addWidget(w)
        self.filas.append((w, e))
        if foco:
            e.setFocus()

    def _quitar(self, w):
        self.filas = [(x, e) for x, e in self.filas if x is not w]
        self.caja.removeWidget(w)
        w.hide()
        w.deleteLater()

    def valores(self):
        vistos, res = set(), []
        for _w, e in self.filas:
            t = " ".join(e.text().split())
            if t and t.casefold() not in vistos:
                vistos.add(t.casefold())
                res.append(t)
        return res


class DialogoDatosSeiyuu(QDialog):
    """Cumpleaños (con año y edad), enlace de VNDB y redes sociales de una seiyuu."""

    def __init__(self, parent, nombre, cumple="", redes=(), anio=0, vndb=""):
        super().__init__(parent)
        self.setWindowTitle(f"Datos de {nombre}")
        self.resize(580, 640)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        cab = QLabel(f"🎙 {nombre}")
        cab.setObjectName("heading")
        lay.addWidget(cab)

        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        cuerpo = QWidget()
        v = QVBoxLayout(cuerpo)
        v.setContentsMargins(0, 0, 8, 0)
        v.setSpacing(8)

        v.addWidget(self._titulo("1 · Cumpleaños  (si no se sabe, déjalo en —)"))
        fila = QHBoxLayout()
        self.s_dia = QComboBox()
        self.s_dia.addItem("—")
        self.s_dia.addItems([str(i) for i in range(1, 32)])
        self.s_dia.setMaxVisibleItems(12)
        self.c_mes = QComboBox()
        self.c_mes.addItem("—")
        self.c_mes.addItems([m.capitalize() for m in MESES_ES])
        m = re.match(r"\s*(\d{1,2}) de (\w+)", cumple or "")
        if m and m.group(2).lower() in MESES_ES:
            self.s_dia.setCurrentIndex(min(31, max(0, int(m.group(1)))))
            self.c_mes.setCurrentIndex(MESES_ES.index(m.group(2).lower()) + 1)
        elif (cumple or "").lower() in MESES_ES:
            self.c_mes.setCurrentIndex(MESES_ES.index(cumple.lower()) + 1)
        fila.addWidget(self.s_dia)
        fila.addWidget(QLabel("de"))
        fila.addWidget(self.c_mes, 1)
        self.e_anio = QLineEdit()                       # año de nacimiento (opcional)
        self.e_anio.setPlaceholderText("Año")
        self.e_anio.setMaxLength(4)
        self.e_anio.setFixedWidth(70)
        self.e_anio.setValidator(QIntValidator(1, 9999, self))
        if anio:
            self.e_anio.setText(str(int(anio)))
        fila.addWidget(QLabel("de"))
        fila.addWidget(self.e_anio)
        v.addLayout(fila)
        self.lbl_edad = QLabel("")
        self.lbl_edad.setObjectName("muted")
        v.addWidget(self.lbl_edad)
        self.s_dia.activated.connect(
            lambda _i: QTimer.singleShot(0, self.c_mes.showPopup)
            if self.c_mes.currentIndex() == 0 else None)
        self.c_mes.currentIndexChanged.connect(self._ajustar_dia)
        for _w in (self.s_dia, self.c_mes):
            _w.currentIndexChanged.connect(self._actualizar_edad)
        self.e_anio.textChanged.connect(self._actualizar_edad)
        self._actualizar_edad()

        v.addSpacing(8)
        v.addWidget(self._titulo("2 · VNDB  (The Visual Novel Database)"))
        fv = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(pixmap_icono_red("vndb", 26))
        ic.setFixedSize(28, 28)
        fv.addWidget(ic)
        self.e_vndb = QLineEdit(vndb or "")
        self.e_vndb.setPlaceholderText("https://vndb.org/s1234   (o solo  s1234)")
        fv.addWidget(self.e_vndb, 1)
        v.addLayout(fv)

        v.addSpacing(8)
        v.addWidget(self._titulo("3 · Redes sociales  (Facebook, Instagram, X…)"))
        self.f_redes = FilasTexto(redes, "Enlace  (ej.: https://x.com/usuario)",
                                  "＋ Añadir red social")
        v.addWidget(self.f_redes)
        v.addStretch()
        sc.setWidget(cuerpo)
        lay.addWidget(sc, 1)

        botones = QHBoxLayout()
        botones.addStretch()
        b_c = BotonAnimado("Cancelar")
        b_c.setAutoDefault(False)
        b_c.clicked.connect(self.reject)
        b_g = BotonAnimado("Guardar", primario=True)
        b_g.setDefault(True)
        b_g.clicked.connect(self.accept)
        botones.addWidget(b_c)
        botones.addWidget(b_g)
        lay.addLayout(botones)

    @staticmethod
    def _titulo(texto):
        t = QLabel(texto)
        t.setObjectName("heading")
        return t

    def _ajustar_dia(self, *_):
        mes = self.c_mes.currentIndex()
        tope = {2: 29, 4: 30, 6: 30, 9: 30, 11: 30}.get(mes, 31)
        if self.s_dia.currentIndex() > tope:
            self.s_dia.setCurrentIndex(tope)

    def _cumple_texto(self):
        dia, mes = self.s_dia.currentIndex(), self.c_mes.currentIndex()
        if mes and dia:
            return f"{dia} de {MESES_ES[mes - 1]}"
        return MESES_ES[mes - 1] if mes else ""

    def _anio(self):
        t = self.e_anio.text().strip()
        return int(t) if t.isdigit() and 1 <= int(t) <= 9999 else 0

    def _actualizar_edad(self, *_):
        edad = edad_actual(self._cumple_texto(), self._anio())
        if edad is None:
            self.lbl_edad.setText("Escribe el año de nacimiento para ver su edad actual.")
        else:
            self.lbl_edad.setText(f"🎂 Tiene {edad} {'año' if edad == 1 else 'años'} actualmente")

    def valores(self):
        return (self._cumple_texto(), self.f_redes.valores(), self._anio(),
                normalizar_vndb(self.e_vndb.text()))


class FotoClasif(QWidget):
    """Foto grande de la heroína que se está clasificando."""

    def __init__(self):
        super().__init__()
        self.ruta, self.enc = "", ENC0
        self.setMinimumSize(300, 380)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def poner(self, ruta, enc):
        self.ruta, self.enc = ruta or "", enc or ENC0
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        pm = (CACHE_GRANDE.obtener_diferido(self.ruta, 760, self)
              if self.ruta and Path(self.ruta).exists() else None)
        dibujar_cover(p, r, pm, 22, self.enc)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(ROSA_H), 3))
        p.drawRoundedRect(r, 22, 22)
        p.end()


class DialogoClasificarH(QDialog):
    """Pasa por las fotos de las heroínas aún sin clasificar: ¿tiene escenas H (eroge)? Sí / No.
    Cada respuesta se guarda al instante, así que se puede salir cuando se quiera."""

    def __init__(self, parent, items, guardar, borrar):
        super().__init__(parent)
        self.setWindowTitle("Clasificación de heroínas")
        self.resize(560, 760)
        self.items, self.guardar, self.borrar = items, guardar, borrar
        self.i = 0
        self.hist = []                      # (clave, valor) en orden, para deshacer
        self.n_si = self.n_no = 0

        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        cab = QLabel("💗 Clasificación de heroínas")
        cab.setObjectName("heading")
        lay.addWidget(cab)
        self.lbl_prog = QLabel("")
        self.lbl_prog.setObjectName("muted")
        lay.addWidget(self.lbl_prog)
        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        self.barra.setFixedHeight(8)
        self.barra.setRange(0, len(items))
        lay.addWidget(self.barra)

        self.foto = FotoClasif()
        lay.addWidget(self.foto, 1)
        self.lbl_nombre = QLabel("")
        self.lbl_nombre.setObjectName("heading")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setWordWrap(True)
        lay.addWidget(self.lbl_nombre)
        self.lbl_juego = QLabel("")
        self.lbl_juego.setObjectName("muted")
        self.lbl_juego.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_juego.setWordWrap(True)
        lay.addWidget(self.lbl_juego)
        preg = QLabel("¿Tiene escenas H (eroge)?")
        preg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(preg)

        fila = QHBoxLayout()
        fila.setSpacing(10)
        self.b_no = BotonAnimado("✕  No   (N)")
        self.b_si = BotonAnimado("💗  Sí, tiene H   (S)", primario=True)
        for b in (self.b_no, self.b_si):
            b.setAutoDefault(False)
            b.setMinimumHeight(48)
            fila.addWidget(b, 1)
        self.b_no.clicked.connect(lambda *_: self.responder(0))
        self.b_si.clicked.connect(lambda *_: self.responder(1))
        lay.addLayout(fila)

        fila2 = QHBoxLayout()
        self.b_atras = BotonAnimado("↶ Deshacer   (Z)")
        self.b_atras.setAutoDefault(False)
        self.b_atras.clicked.connect(self.deshacer)
        b_salir = BotonAnimado("Salir")
        b_salir.setAutoDefault(False)
        b_salir.clicked.connect(self.accept)
        fila2.addWidget(self.b_atras)
        fila2.addStretch()
        fila2.addWidget(b_salir)
        lay.addLayout(fila2)

        for tecla, val in (("S", 1), ("N", 0)):
            QShortcut(QKeySequence(tecla), self, activated=lambda v=val: self.responder(v))
        QShortcut(QKeySequence("Z"), self, activated=self.deshacer)
        self.mostrar()

    @property
    def hechas(self):
        return len(self.hist)

    def mostrar(self):
        n = len(self.items)
        if self.i >= n:
            self.accept()
            return
        it = self.items[self.i]
        self.foto.poner(it["foto"], it["enc"])
        self.lbl_nombre.setText(it["nombre"])
        self.lbl_juego.setText("📖 " + it["juego"])
        self.lbl_prog.setText(f"{self.i + 1} de {n}  ·  💗 {self.n_si} con H  ·  {self.n_no} sin H")
        self.barra.setValue(self.i)
        self.b_atras.setEnabled(bool(self.hist))
        if self.i + 1 < n:                                  # precarga la siguiente foto
            sig = self.items[self.i + 1]["foto"]
            if sig and Path(sig).exists():
                CACHE_GRANDE.obtener_diferido(sig, 760, None)

    def responder(self, valor):
        if self.i >= len(self.items):
            return
        it = self.items[self.i]
        self.guardar(it["clave"], it["nombre"], valor)
        self.hist.append((it["clave"], valor))
        if valor:
            self.n_si += 1
        else:
            self.n_no += 1
        self.i += 1
        self.mostrar()

    def deshacer(self):
        if not self.hist:
            return
        clave, valor = self.hist.pop()
        self.borrar(clave)
        if valor:
            self.n_si -= 1
        else:
            self.n_no -= 1
        self.i -= 1
        self.mostrar()


class DialogoCorregirH(QDialog):
    """Corrige el sí/no de H de UNA heroína: escribe su nombre, elige y cambia. Compacto."""

    def __init__(self, parent, heroinas, estado, guardar):
        super().__init__(parent)
        self.setWindowTitle("Corregir H de una heroína")
        self.setMinimumWidth(380)
        self.heroinas = heroinas            # {clave: nombre}
        self.estado = estado                # {clave: 0/1}
        self.guardar = guardar
        self.clave = None
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        self.e_nombre = QLineEdit()
        self.e_nombre.setPlaceholderText("Escribe el nombre de la heroína…")
        comp = QCompleter(sorted(set(heroinas.values()), key=str.casefold), self)
        comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp.setFilterMode(Qt.MatchFlag.MatchContains)
        self.e_nombre.setCompleter(comp)
        lay.addWidget(self.e_nombre)
        self.lbl = QLabel("")
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        fila = QHBoxLayout()
        self.b_no = BotonAnimado("✕  Sin H")
        self.b_si = BotonAnimado("💗  Con H", primario=True)
        for b in (self.b_no, self.b_si):
            b.setAutoDefault(False)
            b.setEnabled(False)
            fila.addWidget(b, 1)
        self.b_no.clicked.connect(lambda *_: self._poner(0))
        self.b_si.clicked.connect(lambda *_: self._poner(1))
        lay.addLayout(fila)
        b_cerrar = BotonAnimado("Cerrar")
        b_cerrar.setAutoDefault(False)
        b_cerrar.clicked.connect(self.accept)
        lay.addWidget(b_cerrar, 0, Qt.AlignmentFlag.AlignRight)
        self.e_nombre.textChanged.connect(self._buscar)
        self.e_nombre.setFocus()
        self._buscar("")

    def _buscar(self, texto):
        clave = clave_heroina(texto) if texto.strip() else None
        self.clave = clave if clave in self.heroinas else None
        for b in (self.b_no, self.b_si):
            b.setEnabled(self.clave is not None)
        if not texto.strip():
            self.lbl.setText("Elige una heroína para ver y cambiar su clasificación.")
        elif self.clave is None:
            self.lbl.setText("No hay ninguna heroína con ese nombre exacto.")
        else:
            self._mostrar()

    def _mostrar(self):
        v = self.estado.get(self.clave)
        txt = ("💗 Está marcada CON escenas H" if v == 1 else
               "✕ Está marcada SIN escenas H" if v == 0 else
               "Aún sin clasificar")
        self.lbl.setText(f"{self.heroinas[self.clave]}: {txt}")

    def _poner(self, valor):
        if self.clave is None:
            return
        self.guardar(self.clave, self.heroinas[self.clave], valor)
        self.estado[self.clave] = valor
        self._mostrar()


class DialogoImportarHeroina(QDialog):
    """Elige heroínas de OTRAS novelas para copiarlas (foto y datos) a la novela actual."""

    def __init__(self, parent, candidatas, novela):
        super().__init__(parent)
        self.setWindowTitle("Importar heroína de otra novela")
        self.resize(560, 620)
        lay = QVBoxLayout(self)
        t = QLabel(f"⇩ Importar a «{novela}»")
        t.setObjectName("heading")
        lay.addWidget(t)
        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("⌕  Buscar heroína o novela...")
        self.buscar.textChanged.connect(self._filtrar)
        lay.addWidget(self.buscar)
        self.lista = QListWidget()
        self.lista.setIconSize(QSize(52, 52))
        self.lista.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.lista.itemSelectionChanged.connect(self._contar)
        for g in candidatas:
            it = QListWidgetItem(QIcon(avatar(g["foto"], 52, parse_enc(g["enc"]))),
                                 f"{g['nombre']}\n📖 {' · '.join(g['novelas'])}")
            it.setData(Qt.ItemDataRole.UserRole, g)
            it.setSizeHint(QSize(100, 64))
            self.lista.addItem(it)
        lay.addWidget(self.lista, 1)
        fila = QHBoxLayout()
        self.lbl = QLabel("0 elegidas")
        self.lbl.setObjectName("muted")
        fila.addWidget(self.lbl, 1)
        b_c = BotonAnimado("Cancelar")
        b_c.clicked.connect(self.reject)
        self.b_ok = BotonAnimado("Importar", primario=True)
        self.b_ok.clicked.connect(self.accept)
        fila.addWidget(b_c)
        fila.addWidget(self.b_ok)
        lay.addLayout(fila)

    def _filtrar(self, texto):
        q = texto.casefold().strip()
        for i in range(self.lista.count()):
            it = self.lista.item(i)
            it.setHidden(bool(q) and q not in it.text().casefold())

    def _contar(self):
        n = len(self.lista.selectedItems())
        self.lbl.setText(f"{n} {'elegida' if n == 1 else 'elegidas'}")

    def elegidas(self):
        return [it.data(Qt.ItemDataRole.UserRole) for it in self.lista.selectedItems()]


class DialogoMover(QDialog):
    """Mover RÁPIDO: eliges la categoría (botones o teclas 1-4) y tocas a la heroína:
    se mueve al instante, sin pulsar «Aceptar».  Enter en el buscador = primera heroína."""

    def __init__(self, parent, heroinas, cat_actual, heroina_actual, ultimo=None):
        super().__init__(parent)
        self.setWindowTitle("Mover selección")
        self.resize(560, 520)
        self.resultado = None            # (categoria, heroina_id, heroina_nombre)
        self.cat = cat_actual if cat_actual in CATEGORIAS else CAT_DEFECTO
        self._botones_her = []

        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        cab = QLabel("⇄ Mover a…")
        cab.setObjectName("heading")
        lay.addWidget(cab)

        # --- repetir el último destino (ideal para mover varias tandas al mismo sitio)
        nombres = {hid: n for hid, n in heroinas}
        if ultimo and ultimo[1] in nombres:
            b_ult = BotonAnimado(f"⚡ Repetir último:  {ultimo[0]}  →  {nombres[ultimo[1]]}",
                                 primario=True)
            b_ult.clicked.connect(
                lambda: self.elegir(ultimo[0], ultimo[1], nombres[ultimo[1]]))
            lay.addWidget(b_ult)

        # --- 1) categoría
        t1 = QLabel("1) Categoría   (teclas 1 - 4)")
        t1.setObjectName("muted")
        lay.addWidget(t1)
        fila_cat = QHBoxLayout()
        self.b_cats = {}
        for i, c in enumerate(CATEGORIAS, 1):
            b = BotonAnimado(f"{i}  {c}")
            b.setCheckable(True)
            b.setChecked(c == self.cat)
            b.clicked.connect(lambda _=False, c=c: self.poner_cat(c))
            self.b_cats[c] = b
            fila_cat.addWidget(b)
        lay.addLayout(fila_cat)

        # --- 2) heroína
        t2 = QLabel("2) Toca a la heroína: se mueve al instante")
        t2.setObjectName("muted")
        lay.addWidget(t2)
        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Filtrar heroína…  (Enter = la primera de la lista)")
        self.buscar.setClearButtonEnabled(True)
        self.buscar.textChanged.connect(self.filtrar)
        self.buscar.returnPressed.connect(self.primera)
        lay.addWidget(self.buscar)

        self.zona = QWidget()
        self.rejilla = QGridLayout(self.zona)
        self.rejilla.setSpacing(8)
        self.rejilla.setContentsMargins(2, 2, 2, 2)
        for hid, nombre in heroinas:
            texto = nombre + ("   ● actual" if hid == heroina_actual else "")
            b = BotonAnimado(texto, primario=(hid == heroina_actual))
            b.clicked.connect(lambda _=False, h=hid, n=nombre: self.elegir(self.cat, h, n))
            self._botones_her.append((nombre, b))
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidget(self.zona)
        lay.addWidget(self.scroll, 1)
        self.filtrar()

        fila = QHBoxLayout()
        fila.addStretch()
        b_c = BotonAnimado("Cancelar")
        b_c.clicked.connect(self.reject)
        fila.addWidget(b_c)
        lay.addLayout(fila)
        self.setFocus()

    def poner_cat(self, cat):
        self.cat = cat
        for c, b in self.b_cats.items():
            b.setChecked(c == cat)

    def filtrar(self, *_):
        texto = self.buscar.text().casefold().strip()
        while self.rejilla.count():
            self.rejilla.takeAt(0)
        for fila_i in range(self.rejilla.rowCount()):
            self.rejilla.setRowStretch(fila_i, 0)
        pos = 0
        for nombre, b in self._botones_her:
            visible = texto in nombre.casefold()
            b.setVisible(visible)
            if visible:
                self.rejilla.addWidget(b, pos // 2, pos % 2)
                pos += 1
        self.rejilla.setRowStretch(pos // 2 + 1, 1)

    def primera(self):
        for nombre, b in self._botones_her:
            if b.isVisible():
                b.click()
                return

    def elegir(self, cat, hid, nombre):
        self.resultado = (cat, hid, nombre)
        self.accept()

    def keyPressEvent(self, e):
        # 1-4 eligen categoría (solo si no estás escribiendo en el buscador)
        k = int(e.key())
        if 0x31 <= k <= 0x34 and not self.buscar.hasFocus():      # teclas 1..4
            self.poner_cat(CATEGORIAS[k - 0x31])
            return
        super().keyPressEvent(e)


class DialogoAjustes(QDialog):
    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.setWindowTitle("Personalizar NyuhuhuGallery")
        self.resize(640, 600)
        raiz = QVBoxLayout(self)
        self.tabs = QTabWidget()
        raiz.addWidget(self.tabs, 1)

        def pagina(titulo):
            w = QWidget()
            f = QFormLayout(w)
            f.setVerticalSpacing(14)
            f.setContentsMargins(16, 16, 16, 16)
            self.tabs.addTab(w, titulo)
            return f

        def slider(rango, valor, clave):
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(*rango)
            sl.setValue(valor)
            sl.valueChanged.connect(lambda v: main.cambiar_ajuste(clave, v))
            return sl

        def combo(opciones, actual, clave):
            c = QComboBox()
            c.addItems(opciones)
            c.setCurrentText(actual)
            c.currentTextChanged.connect(lambda v: main.cambiar_ajuste(clave, v))
            return c

        def check(texto, valor, clave):
            k = QCheckBox(texto)
            k.setChecked(valor)
            k.toggled.connect(lambda v: main.cambiar_ajuste(clave, v))
            return k

        # --- colores
        f = pagina("🎨 Colores")
        f.addRow("Modo:", combo(list(BASES), Tema.nombre, "tema"))
        self.c_acento = combo(list(ACENTOS) + ["Personalizado"], Tema.acento, "acento")
        f.addRow("Paleta pastel:", self.c_acento)
        fila = QHBoxLayout()
        b1 = BotonAnimado("Color principal")
        b2 = BotonAnimado("Color secundario")
        b1.clicked.connect(lambda: self.elegir_color("color1"))
        b2.clicked.connect(lambda: self.elegir_color("color2"))
        fila.addWidget(b1)
        fila.addWidget(b2)
        f.addRow("Colores propios:", fila)
        f.addRow("Opacidad de paneles:", slider((30, 100), Tema.panel_op, "panel_op"))
        f.addRow("Redondeo de esquinas:", slider((4, 30), Tema.radio, "radio"))

        # --- fuente
        f = pagina("🔤 Fuente")
        self.c_fuente = QFontComboBox()
        self.c_fuente.setCurrentFont(QFont(Tema.fuente))
        self.c_fuente.currentFontChanged.connect(self.cambiar_fuente)
        f.addRow("Fuente (lista desplegable):", self.c_fuente)
        sp = QSpinBox()
        sp.setRange(8, 18)
        sp.setValue(Tema.tam)
        sp.valueChanged.connect(lambda v: main.cambiar_ajuste("tam", v))
        f.addRow("Tamaño de letra:", sp)
        self.vista = QLabel("Así se verá tu texto ♡ あいうえお 123")
        self.vista.setWordWrap(True)
        self.vista.setFont(QFont(Tema.fuente, 18))
        f.addRow("Vista previa:", self.vista)

        # --- imágenes
        f = pagina("🖼 Imágenes")
        f.addRow(self._fila_imagen("Imagen de fondo", "fondo"))
        f.addRow("Visibilidad del fondo:", slider((0, 100), Tema.fondo_vis, "fondo_vis"))
        f.addRow(self._fila_imagen("Banner superior", "cabecera"))
        f.addRow(self._fila_imagen("Personaje decorativo", "mascota"))

        # --- interfaz
        f = pagina("🧩 Interfaz")
        titulo = QLineEdit(Tema.titulo_biblioteca)
        titulo.setMaxLength(65)
        titulo.setPlaceholderText("Mi biblioteca")
        titulo.editingFinished.connect(
            lambda: main.cambiar_ajuste("titulo_biblioteca", titulo.text().strip() or "Mi biblioteca"))
        f.addRow("Título de la biblioteca", titulo)
        carpeta = BotonAnimado("📁 Abrir carpeta de la biblioteca")
        carpeta.clicked.connect(lambda: os.startfile(str(ROOT)))
        f.addRow(carpeta)
        f.addRow("Forma de las tarjetas:", slider((100, 190), Tema.ratio_tarjeta, "ratio_tarjeta"))

        # --- efectos
        f = pagina("✨ Efectos")
        f.addRow("Decoración de fondo:",
                 combo(["Pétalos", "Estrellas", "Corazones", "Burbujas", "Ninguno"],
                       Tema.particulas, "particulas"))
        f.addRow("Cantidad:", slider((0, 80), Tema.cantidad, "cantidad"))
        nota = QLabel("Modo ligero: sin animaciones, para que la app vaya fluida.\n"
                      "La decoración y los brillos al pasar el ratón son estáticos.")
        nota.setObjectName("muted")
        nota.setWordWrap(True)
        f.addRow("", nota)

        cerrar = BotonAnimado("Listo", primario=True)
        cerrar.clicked.connect(self.accept)
        raiz.addWidget(cerrar)

    def cambiar_fuente(self, fnt):
        self.main.cambiar_ajuste("fuente", fnt.family())
        self.vista.setFont(QFont(fnt.family(), 18))

    def elegir_color(self, clave):
        if Tema.acento != "Personalizado":
            self.main.cambiar_ajuste("color1", Tema.a1())
            self.main.cambiar_ajuste("color2", Tema.a2())
        col = QColorDialog.getColor(QColor(getattr(Tema, clave)), self, "Elegir color")
        if col.isValid():
            self.main.cambiar_ajuste(clave, col.name())
            self.main.cambiar_ajuste("acento", "Personalizado")
            self.c_acento.setCurrentText("Personalizado")

    def _fila_imagen(self, etiqueta, clave):
        cont = QWidget()
        h = QHBoxLayout(cont)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(QLabel(etiqueta), 1)
        b1 = BotonAnimado("Elegir")
        b2 = BotonAnimado("Quitar")
        b1.clicked.connect(lambda: self.elegir(clave))
        b2.clicked.connect(lambda: self.main.cambiar_ajuste(clave, ""))
        h.addWidget(b1)
        h.addWidget(b2)
        return cont

    def elegir(self, clave):
        ruta, _ = QFileDialog.getOpenFileName(self, "Elegir imagen", str(Path.home()), FILTRO_IMG)
        if ruta:
            self.main.cambiar_ajuste(clave, copiar_asset(ruta, "ui", clave))
            self.actualizar_prev(clave)

    def _poner_imagen(self, clave, ruta):
        self.main.cambiar_ajuste(clave, ruta)
        self.actualizar_prev(clave)

    def actualizar_prev(self, clave):
        prev = getattr(self, "prevs", {}).get(clave)
        if prev is None:
            return
        ruta = getattr(Tema, clave)
        pm = QPixmap(ruta) if ruta and Path(ruta).exists() else QPixmap()
        if pm.isNull():
            prev.setPixmap(QPixmap())
            prev.setText("(sin imagen: no se encontró el archivo)" if ruta else "(sin imagen)")
        else:
            prev.setText("")
            prev.setPixmap(pm.scaledToHeight(104, Qt.TransformationMode.SmoothTransformation))


# =========================================================
# APLICACION PRINCIPAL
# =========================================================

MIME_PERSONAJE = "application/x-vn-personaje"


class DelegadoPersonaje(QStyledItemDelegate):
    """Fila de personaje: tarjeta redondeada con su foto en círculo y el nombre."""
    ALTO = 70

    def sizeHint(self, option, index):
        return QSize(100, self.ALTO)

    def paint(self, p, option, index):
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(option.rect).adjusted(2, 5, -2, -5)
        sel = bool(option.state & QStyle.StateFlag.State_Selected)
        hov = bool(option.state & QStyle.StateFlag.State_MouseOver)
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        camino = QPainterPath()
        camino.addRoundedRect(r, Tema.radio, Tema.radio)
        if sel:
            g = QLinearGradient(r.topLeft(), r.topRight())
            g.setColorAt(0, a1)
            g.setColorAt(1, a2)
            p.fillPath(camino, QBrush(g))
            txt = QColor(TEXTO_SOBRE_ACENTO)
        else:
            p.fillPath(camino, mezclar(QColor(Tema.c("input")), a1, 0.24 if hov else 0.05))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(mezclar(QColor(Tema.c("border")), a1, 0.75 if hov else 0.0), 1.2))
            p.drawPath(camino)
            txt = QColor(Tema.c("text"))
        lado = r.height() - 14
        av = QRectF(r.left() + 10, r.top() + 7, lado, lado)
        datos = index.data(Qt.ItemDataRole.UserRole) or {}
        pm, _ = avatar_listo(datos.get("foto"), 52, datos.get("enc"), option.widget.viewport())
        if pm is not None and not pm.isNull():
            p.drawPixmap(av, pm, QRectF(pm.rect()))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 215) if sel else con_alfa(a1, 200), 2))
        p.drawEllipse(av)
        f = QFont(option.font)
        f.setBold(True)
        f.setPointSizeF(Tema.tam + 0.5)
        p.setFont(f)
        p.setPen(txt)
        zona = QRectF(av.right() + 12, r.top(), r.right() - av.right() - 22, r.height())
        nombre = QFontMetrics(f).elidedText(str(index.data(Qt.ItemDataRole.DisplayRole) or ""),
                                            Qt.TextElideMode.ElideRight, int(zona.width()))
        p.drawText(zona, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, nombre)
        p.restore()


class ListaPersonajes(QListWidget):
    """Lista de heroínas, sub-heroínas o personajes secundarios.
    Se reordena arrastrando dentro de la lista y, si arrastras un icono a OTRA lista, el
    personaje cambia de tipo (el movimiento lo resuelve la ventana principal)."""
    personaje_soltado = Signal(int, str, int)       # id del personaje, tipo de ESTA lista, fila
    arrastre_iniciado = Signal()
    arrastre_terminado = Signal()

    def __init__(self, tipo):
        super().__init__()
        self.tipo = tipo
        self.setMouseTracking(True)
        self.setSpacing(0)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setIconSize(QSize(52, 52))
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.count() == 0:                   # hueco punteado: también sirve para soltar un icono
            p = QPainter(self.viewport())
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            c = QColor(Tema.a1())
            c.setAlpha(120)
            p.setPen(QPen(c, 1.6, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(self.viewport().rect()).adjusted(2, 3, -2, -3),
                              Tema.radio, Tema.radio)


    def startDrag(self, acciones):
        """Mientras arrastras, los paneles vacíos se despliegan para poder soltar en ellos."""
        self.arrastre_iniciado.emit()
        try:
            super().startDrag(acciones)
        finally:
            self.arrastre_terminado.emit()

    def mimeData(self, items):
        md = super().mimeData(items)
        if items:
            d = items[0].data(Qt.ItemDataRole.UserRole) or {}
            md.setData(MIME_PERSONAJE, str(d.get("id", 0)).encode())
        return md

    def _ajeno(self, e):
        return e.source() is not self and isinstance(e.source(), ListaPersonajes)

    def _resaltar(self, si):
        if si:
            c = QColor(Tema.a1())
            self.viewport().setStyleSheet(f"background: rgba({c.red()},{c.green()},{c.blue()},45);")
        else:
            self.viewport().setStyleSheet("")

    def dragEnterEvent(self, e):
        if self._ajeno(e):
            self._resaltar(True)
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if self._ajeno(e):
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dragLeaveEvent(self, e):
        self._resaltar(False)
        super().dragLeaveEvent(e)

    def dropEvent(self, e):
        self._resaltar(False)
        if e.source() is self:                       # reordenar dentro de la misma lista
            super().dropEvent(e)
            return
        if self._ajeno(e) and e.mimeData().hasFormat(MIME_PERSONAJE):
            try:
                pid = int(bytes(e.mimeData().data(MIME_PERSONAJE)).decode())
            except ValueError:
                e.ignore()
                return
            fila = self.indexAt(e.position().toPoint()).row()
            e.setDropAction(Qt.DropAction.CopyAction)    # la ventana recarga las listas
            e.accept()
            self.personaje_soltado.emit(pid, self.tipo, fila if fila >= 0 else self.count())
            return
        e.ignore()


SIGNOS = ((1, 20, "♑", "Capricornio"), (2, 19, "♒", "Acuario"), (3, 21, "♓", "Piscis"),
          (4, 20, "♈", "Aries"), (5, 21, "♉", "Tauro"), (6, 21, "♊", "Géminis"),
          (7, 23, "♋", "Cáncer"), (8, 23, "♌", "Leo"), (9, 23, "♍", "Virgo"),
          (10, 23, "♎", "Libra"), (11, 22, "♏", "Escorpio"), (12, 22, "♐", "Sagitario"))


def signo_zodiaco(cumple):
    """'12 de marzo' -> '♓ Piscis'; '' si no se entiende la fecha."""
    m = re.match(r"\s*(\d{1,2}) de (\w+)", cumple or "")
    if not m or m.group(2).lower() not in MESES_ES:
        return ""
    mes, dia = MESES_ES.index(m.group(2).lower()) + 1, int(m.group(1))
    for mf, df, simbolo, nombre in SIGNOS:
        if (mes, dia) < (mf, df):
            return f"{simbolo} {nombre}"
    return "♑ Capricornio"


def _camino_estrella4():
    c = QPainterPath()
    c.moveTo(0, -1)
    c.cubicTo(0.12, -0.28, 0.28, -0.12, 1, 0)
    c.cubicTo(0.28, 0.12, 0.12, 0.28, 0, 1)
    c.cubicTo(-0.12, 0.28, -0.28, 0.12, -1, 0)
    c.cubicTo(-0.28, -0.12, -0.12, -0.28, 0, -1)
    c.closeSubpath()
    return c


ESTRELLA4 = _camino_estrella4()


def dibujar_destello(p, x, y, r, color):
    """Destello de 4 puntas (el clásico «kirakira» del anime)."""
    p.save()
    p.translate(x, y)
    p.scale(r, r)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawPath(ESTRELLA4)
    p.restore()


class _LienzoPerfil(QWidget):
    """Dibuja el perfil: retrato grande con sus datos, el reparto de su novela y las otras
    novelas donde aparece. Todo sale solo de lo que ya existe: no hay nada que escribir."""
    BH, M, G = 270, 6, 12
    CELDA, CELDA_H = 96, 100          # reparto: avatar + nombre
    PW, PH = 110, 148                 # otras novelas: portada + título

    def __init__(self):
        super().__init__()
        self.d = None

    def poner(self, d):
        self.d = d
        self._ajustar()
        self.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._ajustar()

    def _cols(self, W, celda):
        return max(1, int((W - 2 * self.M - 40 + self.G) // (celda + self.G)))

    def _alto_reparto(self, W):
        filas = ceil(len(self.d["reparto"]) / self._cols(W, self.CELDA))
        return 58 + filas * (self.CELDA_H + 8) + 12

    def _alto_otras(self, W):
        filas = ceil(len(self.d["otras"]) / self._cols(W, self.PW))
        return 58 + filas * (self.PH + 8) + 12

    def _alto(self, W):
        if not self.d:
            return 200
        h = self.M + self.BH + 16 + self._alto_reparto(W)
        if self.d["otras"]:
            h += 16 + self._alto_otras(W)
        return int(h + self.M)

    def _ajustar(self):
        if self.d:
            self.setMinimumHeight(self._alto(max(300, self.width())))

    def _seccion(self, p, rect, titulo, derecha=""):
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card, borde = QColor(Tema.c("card")), QColor(Tema.c("border"))
        cam = QPainterPath()
        cam.addRoundedRect(rect, Tema.radio + 4, Tema.radio + 4)
        p.fillPath(cam, mezclar(card, a1, 0.06))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(borde, 1.2))
        p.drawPath(cam)
        texto_el(p, rect.left() + 20, rect.top() + 10, rect.width() - 190, 30, titulo,
                 fnt(Tema.tam + 1, bold=True), QColor(Tema.c("text")))
        if derecha:
            texto_el(p, rect.right() - 170, rect.top() + 10, 150, 30, derecha,
                     fnt(Tema.tam - 1), QColor(Tema.c("muted")), Qt.AlignmentFlag.AlignRight)
        g = QLinearGradient(rect.left() + 20, 0, rect.right() - 20, 0)
        g.setColorAt(0, con_alfa(a1, 190))
        g.setColorAt(1, con_alfa(a2, 0))
        p.setPen(QPen(QBrush(g), 1.6))
        p.drawLine(QPointF(rect.left() + 20, rect.top() + 46), QPointF(rect.right() - 20,
                                                                      rect.top() + 46))

    def paintEvent(self, e):
        d = self.d
        if not d:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        W, M = self.width(), self.M
        a1, a2 = QColor(Tema.a1()), QColor(Tema.a2())
        card = QColor(Tema.c("card"))
        txt, mu = QColor(Tema.c("text")), QColor(Tema.c("muted"))
        blanco = QColor(255, 255, 255)

        # ---------- banner
        r = QRectF(M, M, W - 2 * M, self.BH)
        rad = Tema.radio + 8
        cam = QPainterPath()
        cam.addRoundedRect(r, rad, rad)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, mezclar(card, a1, 0.22))
        g.setColorAt(1, mezclar(card, a2, 0.30))
        p.fillPath(cam, QBrush(g))
        p.save()
        p.setClipPath(cam)
        dibujar_destello(p, r.right() - 70, r.top() + 80, 130, con_alfa(a1, 28))
        dibujar_destello(p, r.right() - 210, r.bottom() - 46, 46, con_alfa(a2, 40))
        for fx, fy, rr, al in ((0.46, 0.12, 9, 170), (0.93, 0.50, 7, 150),
                               (0.60, 0.88, 6, 140), (0.30, 0.93, 8, 120)):
            dibujar_destello(p, r.left() + r.width() * fx, r.top() + r.height() * fy, rr,
                             con_alfa(mezclar(a1, blanco, 0.5), al))
        p.restore()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(a1, 2))
        p.drawPath(cam)

        # retrato
        pr = QRectF(r.left() + 24, r.top() + 20, 170, r.height() - 40)
        for i in (8, 5, 2):
            sh = QPainterPath()
            sh.addRoundedRect(pr.adjusted(-i, -i + 4, i, i + 4), 20 + i, 20 + i)
            p.fillPath(sh, QColor(0, 0, 0, 18))
        pm = CACHE_GRANDE.obtener(d["foto"], 700) if d["foto"] else QPixmap()
        dibujar_cover(p, pr, pm, 20, d["enc"])
        gb = QLinearGradient(pr.topLeft(), pr.bottomRight())
        gb.setColorAt(0, a1)
        gb.setColorAt(1, a2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QBrush(gb), 3))
        p.drawRoundedRect(pr, 20, 20)

        # etiqueta + nombre + datos
        x0 = pr.right() + 28
        wt = r.right() - x0 - 26
        etiqueta = "☆  PERSONAJE SECUNDARIO"
        f = fnt(px=11, bold=True, esp=1.4)
        pill = QRectF(x0, r.top() + 26, min(QFontMetrics(f).horizontalAdvance(etiqueta) + 30, wt), 24)
        gp = QLinearGradient(pill.topLeft(), pill.topRight())
        gp.setColorAt(0, a1)
        gp.setColorAt(1, a2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(gp))
        p.drawRoundedRect(pill, 12, 12)
        texto_el(p, pill.left(), pill.top(), pill.width(), pill.height(), etiqueta, f,
                 QColor(TEXTO_SOBRE_ACENTO), Qt.AlignmentFlag.AlignHCenter)
        texto_el(p, x0, r.top() + 58, wt, 46, d["nombre"], fnt(Tema.tam + 14, bold=True), txt)
        y = r.top() + 106
        if d["apodos"]:
            texto_el(p, x0, y, wt, 22, "también: " + ", ".join(d["apodos"]),
                     fnt(Tema.tam - 0.5), mu)
        texto_el(p, x0, y + 24, wt, 22, "✦  " + d["novela"], fnt(Tema.tam, bold=True), _legible(a1))

        chips = []
        if d["cumple"]:
            chips.append(("🎂  " + d["cumple"], False))
            if d["signo"]:
                chips.append((d["signo"], False))
            dc = d["dias_cumple"]
            if dc is not None:
                chips.append(("¡es hoy! 🎉" if dc == 0 else "falta 1 día" if dc == 1
                              else f"faltan {dc} días", True))
        if d["seiyuu"]:
            chips.append(("🎙  " + d["seiyuu"], False))
        if d["altura"]:
            chips.append((f"📏  {d['altura']} cm", False))
        fc = fnt(Tema.tam - 0.5, bold=True)
        fmc = QFontMetrics(fc)
        cx, cy = x0, r.top() + 164
        for texto, acento in chips:
            w = min(wt, fmc.horizontalAdvance(texto) + 28)
            if cx + w > x0 + wt and cx > x0:
                cx, cy = x0, cy + 38
            chip = QRectF(cx, cy, w, 30)
            if acento:
                gc = QLinearGradient(chip.topLeft(), chip.topRight())
                gc.setColorAt(0, a1)
                gc.setColorAt(1, a2)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(gc))
            else:
                p.setPen(QPen(con_alfa(a1, 160), 1.2))
                p.setBrush(con_alfa(a1, 44))
            p.drawRoundedRect(chip, 15, 15)
            texto_el(p, chip.left() + 14, chip.top(), chip.width() - 28, chip.height(), texto, fc,
                     QColor(TEXTO_SOBRE_ACENTO) if acento else txt)
            cx += w + 8

        # ---------- reparto de su novela
        y = r.bottom() + 16
        cr = QRectF(M, y, W - 2 * M, self._alto_reparto(W))
        n = len(d["reparto"])
        self._seccion(p, cr, f"✧  Reparto de «{d['novela']}»",
                      f"{n} {'personaje' if n == 1 else 'personajes'}")
        cols = self._cols(W, self.CELDA)
        simbolos = {"heroina": "♡", "sub": "✧", "secundaria": "☆"}
        for i, c in enumerate(d["reparto"]):
            col, fila = i % cols, i // cols
            cx = cr.left() + 20 + col * (self.CELDA + self.G) + self.CELDA / 2
            cy = cr.top() + 58 + fila * (self.CELDA_H + 8) + 34
            actual = c["id"] == d["id"]
            p.setPen(Qt.PenStyle.NoPen)
            if actual:                                   # él/ella: aura y aro de color
                for k, al in ((12, 26), (8, 40), (4, 60)):
                    p.setBrush(con_alfa(a1, al))
                    p.drawEllipse(QPointF(cx, cy), 34 + k, 34 + k)
            pmv = avatar(c["foto"], 96, c["enc"])
            p.drawPixmap(QRectF(cx - 34, cy - 34, 68, 68), pmv, QRectF(pmv.rect()))
            p.setBrush(Qt.BrushStyle.NoBrush)
            if actual:
                ga = QLinearGradient(cx - 36, cy - 36, cx + 36, cy + 36)
                ga.setColorAt(0, a1)
                ga.setColorAt(1, a2)
                p.setPen(QPen(QBrush(ga), 3.6))
            else:
                p.setPen(QPen(con_alfa(a1, 150), 1.6))
            p.drawEllipse(QPointF(cx, cy), 35, 35)
            gi = QLinearGradient(cx + 14, cy + 14, cx + 36, cy + 36)
            gi.setColorAt(0, a1)
            gi.setColorAt(1, a2)
            p.setPen(QPen(card, 2))
            p.setBrush(QBrush(gi))
            p.drawEllipse(QPointF(cx + 25, cy + 25), 11, 11)
            texto_el(p, cx + 14, cy + 14, 22, 22, simbolos.get(c["tipo"], "♡"),
                     fnt(px=12, bold=True), QColor(TEXTO_SOBRE_ACENTO), Qt.AlignmentFlag.AlignHCenter)
            texto_el(p, cx - 48, cy + 38, 96, 20, c["nombre"], fnt(px=12, bold=actual),
                     txt if actual else mu, Qt.AlignmentFlag.AlignHCenter)

        # ---------- otras novelas donde aparece
        if d["otras"]:
            y = cr.bottom() + 16
            cr = QRectF(M, y, W - 2 * M, self._alto_otras(W))
            n = len(d["otras"])
            self._seccion(p, cr, "✦  También aparece en",
                          f"{n} {'novela' if n == 1 else 'novelas'}")
            cols = self._cols(W, self.PW)
            for i, o in enumerate(d["otras"]):
                col, fila = i % cols, i // cols
                cx = cr.left() + 20 + col * (self.PW + self.G) + self.PW / 2
                top = cr.top() + 58 + fila * (self.PH + 8)
                portada = QRectF(cx - 42, top, 84, 112)
                for k in (6, 3):
                    sh = QPainterPath()
                    sh.addRoundedRect(portada.adjusted(-k, -k + 3, k, k + 3), 12 + k, 12 + k)
                    p.fillPath(sh, QColor(0, 0, 0, 20))
                pmn = CACHE_GRANDE.obtener(o["portada"], 320) if o["portada"] else QPixmap()
                dibujar_cover(p, portada, pmn, 12, o["enc"])
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(con_alfa(a1, 170), 1.6))
                p.drawRoundedRect(portada, 12, 12)
                p.save()
                zona = QRectF(cx - 54, top + 116, 108, 30)
                p.setClipRect(zona)
                p.setFont(fnt(px=11))
                p.setPen(mu)
                p.drawText(zona, int(Qt.AlignmentFlag.AlignHCenter.value
                                     | Qt.AlignmentFlag.AlignTop.value
                                     | Qt.TextFlag.TextWordWrap.value), o["nombre"])
                p.restore()


class PerfilPersonaje(QScrollArea):
    """Lo que se ve en lugar de las pestañas de capturas cuando eliges un personaje secundario
    (no tiene CG). Es solo para mirar: se arma solo con sus datos, el reparto de su novela y las
    demás novelas donde aparece."""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport().setAutoFillBackground(False)
        self.lienzo = _LienzoPerfil()
        self.lienzo.setAutoFillBackground(False)
        self.setWidget(self.lienzo)

    def poner(self, d):
        self.lienzo.poner(d)
        self.verticalScrollBar().setValue(0)


class AsaDivisorPaneles(QSplitterHandle):
    """Asa entre paneles: tres puntitos. Arrastrar = estirar; doble clic = repartir solo."""

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(Tema.a1())
        c.setAlpha(190 if self.underMouse() else 80)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        cx, cy = self.width() / 2, self.height() / 2
        for dx in (-10, 0, 10):
            p.drawEllipse(QPointF(cx + dx, cy), 2.2, 2.2)

    def enterEvent(self, e):
        super().enterEvent(e)
        self.update()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.update()

    def mouseDoubleClickEvent(self, e):
        self.splitter().restablecer.emit()
        e.accept()


class DivisorPaneles(QSplitter):
    """Divisor vertical de los paneles Heroínas / Sub-heroínas / Secundarios."""
    restablecer = Signal()

    def __init__(self):
        super().__init__(Qt.Orientation.Vertical)
        self.pendiente = False
        self.alto_ok = None             # función que reparte los paneles
        self._alto_prev = 0
        self.setChildrenCollapsible(False)
        self.setHandleWidth(14)

    def createHandle(self):
        h = AsaDivisorPaneles(self.orientation(), self)
        h.setToolTip("Arrastra para estirar · doble clic: repartir automáticamente")
        return h

    def _reintentar(self):
        if self.pendiente and self.height() >= 120 and self.alto_ok:
            self.alto_ok()

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self._reintentar)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if abs(self.height() - self._alto_prev) >= 2:
            self._alto_prev = self.height()
            self.pendiente = True
            self._reintentar()


class DivisorProporcional(QSplitter):
    """QSplitter que recuerda la PROPORCIÓN que le das (se guarda y se reaplica al abrir,
    al mostrarse y al cambiar el tamaño de la ventana)."""
    proporcion_cambiada = Signal(float)

    def __init__(self, orientacion, proporcion=None):
        super().__init__(orientacion)
        self.prop = proporcion
        self._aplicando = False
        self.splitterMoved.connect(self._movido)

    def _movido(self, *_):
        s = self.sizes()
        tot = sum(s)
        if tot > 0 and len(s) >= 2:
            self.prop = s[0] / tot
            self.proporcion_cambiada.emit(self.prop)

    def poner_proporcion(self, r):
        self.prop = r
        self._aplicar()

    def _aplicar(self):
        if self.prop is None or self._aplicando or not self.isVisible():
            return
        tot = self.width() - self.handleWidth()
        if tot < 100:
            return
        a = int(tot * self.prop)
        self._aplicando = True
        try:
            self.setSizes([a, tot - a])
        finally:
            self._aplicando = False

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self._aplicar)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.prop is not None:
            self._aplicar()


VELOCIDADES = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
SALTO_CORTO_S = 5              # ← / → y los botones -5 / +5
SALTO_LARGO_S = 10             # J / L
OCULTAR_CONTROLES_MS = 2600    # en pantalla completa, los controles se esconden si no mueves el mouse


class SliderSalto(QSlider):
    """Barra de posición del video: un clic salta directo a ese punto; al arrastrar solo se
    actualiza el tiempo y el video se mueve al soltar (así no se traba)."""
    arrastrando = Signal(int)
    soltado = Signal(int)

    def __init__(self):
        super().__init__(Qt.Orientation.Horizontal)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def _valor(self, e):
        return QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), int(e.position().x()), max(1, self.width()))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.maximum() > 0:
            self.setSliderDown(True)
            v = self._valor(e)
            self.setValue(v)
            self.arrastrando.emit(v)
            e.accept()
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self.isSliderDown():
            v = self._valor(e)
            self.setValue(v)
            self.arrastrando.emit(v)
            e.accept()
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self.isSliderDown() and e.button() == Qt.MouseButton.LeftButton:
            self.setSliderDown(False)
            self.soltado.emit(self.value())
            e.accept()
        else:
            super().mouseReleaseEvent(e)


class VideoPantalla(QVideoWidget):
    """Superficie del video.  Clic: pausa / play · doble clic: pantalla completa (agranda el
    mismo recuadro, no abre ninguna ventana) · rueda: volumen.  El teclado lo atiende el
    reproductor que lo contiene."""
    alternar_play = Signal()
    pantalla_completa = Signal()
    cambio_vol = Signal(int)
    movido = Signal()

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.setMinimumSize(160, 90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        # opaco: Qt no repinta todo lo que hay detrás del video en cada fotograma
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self._t_clic = QTimer(self)                   # un clic espera por si viene el doble clic
        self._t_clic.setSingleShot(True)
        self._t_clic.setInterval(260)
        self._t_clic.timeout.connect(self.alternar_play.emit)
        self._tras_doble = False

    def mousePressEvent(self, e):
        self.setFocus()
        e.accept()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            if self._tras_doble:
                self._tras_doble = False
            else:
                self._t_clic.start()
        e.accept()

    def mouseDoubleClickEvent(self, e):
        self._t_clic.stop()
        self._tras_doble = True
        self.pantalla_completa.emit()
        e.accept()

    def mouseMoveEvent(self, e):
        self.movido.emit()
        super().mouseMoveEvent(e)

    def wheelEvent(self, e):
        self.cambio_vol.emit(5 if e.angleDelta().y() > 0 else -5)
        e.accept()

    def keyPressEvent(self, e):
        e.ignore()                                    # lo atiende ReproductorOpening


TXT_REPOSO = "🎬\n\nHaz clic para reproducir"


class PantallaReposo(QLabel):
    """Pantalla apagada: no carga ni decodifica nada hasta que pulsas ▶ (o haces clic aquí)."""
    clic = Signal()

    def __init__(self):
        super().__init__(TXT_REPOSO)
        self.setObjectName("panel")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(320, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("font-size: 15pt;")

    def mousePressEvent(self, e):
        self.clic.emit()
        e.accept()


class _CapaCompleta(QWidget):
    """Capa negra que cubre TODA la ventana principal. El mismo reproductor se pasa aquí para
    verse grande: no se crea ninguna ventana ni pestaña nueva."""

    def __init__(self, ventana):
        super().__init__(ventana)
        self._v = ventana
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.setPalette(pal)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.setGeometry(ventana.rect())
        ventana.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is self._v and ev.type() == QEvent.Type.Resize:
            self.setGeometry(self._v.rect())
        return False


def _fmt_tiempo(ms):
    s = max(0, int(ms) // 1000)
    h, r = divmod(s, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class ReproductorOpening(QWidget):
    """Pantalla de openings. Empieza APAGADA (no abre ni decodifica ningún video) hasta que
    pulsas ▶. Reproduce la lista en orden y vuelve a empezar (bucle) hasta que la pares.

    Controles: ▶/⏸ · anterior / siguiente · -5 s / +5 s · barra de posición (clic o arrastre) ·
    velocidad · volumen · pantalla completa (agranda este mismo recuadro).
    Teclas: Espacio/K pausa · ← → ∓5 s · J L ∓10 s · Ctrl+← → (o P / N) anterior / siguiente ·
    ↑ ↓ volumen · M silencio · F pantalla completa · Esc salir · 0-9 saltar al 0-90 % ·
    < > velocidad."""
    volumen_cambiado = Signal(int)     # solo cuando TÚ lo cambias (para guardarlo)
    empezo = Signal()                  # empezó a sonar (para pausar la música)
    indice_cambiado = Signal(int)      # qué opening de la lista está activo

    def __init__(self, volumen=OPENING_VOLUMEN):
        super().__init__()
        self._rutas, self._titulos, self._idx, self._fallos = [], [], 0, 0
        self._vol_previo = 0
        self._silenciando = False
        self._reanudar = False
        self._tok = 0
        self._vel = 1.0
        self._dur = 0
        self._seg_mostrado = -1
        # pantalla completa dentro de la misma ventana
        self._completa = False
        self._capa = None
        self._marco = None
        self._ph = None
        self._tamanos = None
        self._ventana_full_previa = False
        self._ventana_max = False
        self._ult_pos = QPoint()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.pantalla = QStackedWidget()
        self.reposo = PantallaReposo()
        self.reposo.clic.connect(self.alternar_play)
        self.video = VideoPantalla()
        self.video.alternar_play.connect(self.alternar_play)
        self.video.pantalla_completa.connect(self.alternar_completa)
        self.video.cambio_vol.connect(lambda d: self.sl_vol.setValue(self.sl_vol.value() + d))
        self.video.movido.connect(self._mostrar_controles)
        self.pantalla.addWidget(self.reposo)          # 0: apagada (no cuesta nada)
        self.pantalla.addWidget(self.video)           # 1: video
        lay.addWidget(self.pantalla, 1)

        self.barra = QFrame()
        self.barra.setObjectName("reproductor")
        col = QVBoxLayout(self.barra)
        col.setContentsMargins(8, 4, 8, 4)
        col.setSpacing(2)

        # --- fila de tiempo: 0:00 ────●──── 3:42
        ft = QHBoxLayout()
        ft.setSpacing(8)
        self.lbl_pos = QLabel("0:00")
        self.lbl_pos.setObjectName("tiempo")
        self.lbl_pos.setMinimumWidth(40)
        self.sl_pos = SliderSalto()
        self.sl_pos.setRange(0, 0)
        self.sl_pos.arrastrando.connect(lambda v: self.lbl_pos.setText(_fmt_tiempo(v)))
        self.sl_pos.soltado.connect(self._ir_a_posicion)
        self.lbl_dur = QLabel("0:00")
        self.lbl_dur.setObjectName("tiempo")
        self.lbl_dur.setMinimumWidth(40)
        self.lbl_dur.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ft.addWidget(self.lbl_pos)
        ft.addWidget(self.sl_pos, 1)
        ft.addWidget(self.lbl_dur)
        col.addLayout(ft)

        # --- fila de botones
        b = QHBoxLayout()
        b.setSpacing(4)
        self.b_ant = BotonRedondo("", 28, icono="prev")
        self.b_ant.setToolTip("Opening anterior (Ctrl+←)")
        self.b_ant.clicked.connect(lambda: self.saltar(-1, manual=True))
        self.b_atr = BotonRedondo(f"-{SALTO_CORTO_S}", 32, pt=8)
        self.b_atr.setToolTip(f"Retroceder {SALTO_CORTO_S} segundos (←)")
        self.b_atr.clicked.connect(lambda: self.mover_segundos(-SALTO_CORTO_S))
        self.b_play = BotonRedondo("", 34, primario=True, icono="play")
        self.b_play.setToolTip("Reproducir / pausa (Espacio)")
        self.b_play.clicked.connect(self.alternar_play)
        self.b_ade = BotonRedondo(f"+{SALTO_CORTO_S}", 32, pt=8)
        self.b_ade.setToolTip(f"Adelantar {SALTO_CORTO_S} segundos (→)")
        self.b_ade.clicked.connect(lambda: self.mover_segundos(SALTO_CORTO_S))
        self.b_sig = BotonRedondo("", 28, icono="next")
        self.b_sig.setToolTip("Opening siguiente (Ctrl+→)")
        self.b_sig.clicked.connect(lambda: self.saltar(1, manual=True))
        self.lbl_n = QLabel("")
        self.lbl_n.setObjectName("tiempo")
        for w in (self.b_ant, self.b_atr, self.b_play, self.b_ade, self.b_sig, self.lbl_n):
            b.addWidget(w)
        self.lbl_t = QLabel("")
        self.lbl_t.setObjectName("muted")
        self.lbl_t.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.lbl_t.setMinimumWidth(0)
        b.addWidget(self.lbl_t, 1)
        self.b_vel = BotonRedondo("1×", 40, pt=7)
        self.b_vel.setToolTip("Velocidad de reproducción")
        self.b_vel.clicked.connect(self._menu_velocidad)
        b.addWidget(self.b_vel)
        self.ic_vol = IconoVolumen()
        self.ic_vol.clic.connect(self.alternar_silencio)
        b.addWidget(self.ic_vol)
        self.sl_vol = QSlider(Qt.Orientation.Horizontal)
        self.sl_vol.setObjectName("volumen")
        self.sl_vol.setRange(0, 100)
        self.sl_vol.setFixedWidth(90)
        self.sl_vol.setCursor(Qt.CursorShape.PointingHandCursor)
        b.addWidget(self.sl_vol)
        self.b_full = BotonRedondo("⛶", 28, pt=max(8, Tema.tam))
        self.b_full.setToolTip("Pantalla completa (F)")
        self.b_full.clicked.connect(self.alternar_completa)
        b.addWidget(self.b_full)
        col.addLayout(b)
        lay.addWidget(self.barra)

        # ningún control de la barra se queda con el teclado: Espacio, flechas, etc. siempre
        # llegan al reproductor
        for w in (self.b_ant, self.b_atr, self.b_play, self.b_ade, self.b_sig, self.b_vel,
                  self.b_full, self.sl_vol):
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._t_ocultar = QTimer(self)
        self._t_ocultar.setSingleShot(True)
        self._t_ocultar.setInterval(OCULTAR_CONTROLES_MS)
        self._t_ocultar.timeout.connect(self._ocultar_controles)

        self.audio = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.player.mediaStatusChanged.connect(self._al_status)
        self.player.playbackStateChanged.connect(self._al_estado)
        self.player.errorOccurred.connect(self._al_error)
        self.player.positionChanged.connect(self._al_posicion)
        self.player.durationChanged.connect(self._al_duracion)

        vol = max(0, min(100, int(volumen)))
        self.audio.setVolume(vol / 100)
        self.ic_vol.poner(vol)
        self.sl_vol.setValue(vol)
        self.sl_vol.valueChanged.connect(self._cambio_volumen)
        self._etiquetar()

    # ---- pantalla completa: el MISMO recuadro se agranda hasta cubrir la ventana
    def en_completa(self):
        return self._completa

    def alternar_completa(self):
        if self._completa:
            self.salir_completa()
        elif self.pantalla.currentIndex() == 1:
            self._entrar_completa()

    def _entrar_completa(self):
        ventana = self.window()
        padre = self.parentWidget()
        if ventana is self or padre is None:
            return
        ph = QWidget()                                # ocupa el hueco mientras el video está grande
        if isinstance(padre, QSplitter):
            i = padre.indexOf(self)
            if i < 0:
                return
            self._tamanos = padre.sizes()
            padre.replaceWidget(i, ph)
            self._marco = ("splitter", padre)
        elif padre.layout() is not None:
            padre.layout().replaceWidget(self, ph)
            self._marco = ("layout", padre.layout())
        else:
            return
        self._ph = ph
        self._capa = _CapaCompleta(ventana)
        self._capa.layout().addWidget(self)
        self._completa = True
        self._ventana_full_previa = ventana.isFullScreen()
        self._ventana_max = ventana.isMaximized()
        if not self._ventana_full_previa:
            ventana.showFullScreen()
        self._capa.setGeometry(ventana.rect())
        self._capa.show()
        self._capa.raise_()
        self.show()
        self.b_full.setToolTip("Salir de pantalla completa (Esc)")
        self.video.setFocus()
        self._mostrar_controles(True)

    def salir_completa(self):
        if not self._completa:
            return
        self._completa = False
        self._t_ocultar.stop()
        self.barra.setVisible(True)
        self.video.unsetCursor()
        capa, ph, ventana = self._capa, self._ph, self._capa.parentWidget()
        capa.layout().removeWidget(self)
        tipo, cont = self._marco
        if tipo == "splitter":
            i = cont.indexOf(ph)
            if i >= 0:
                cont.replaceWidget(i, self)
            if self._tamanos:
                cont.setSizes(self._tamanos)
        else:
            cont.replaceWidget(ph, self)
        self.show()
        ph.hide()
        ph.deleteLater()
        capa.hide()
        capa.deleteLater()
        self._capa = self._ph = self._marco = None
        self.b_full.setToolTip("Pantalla completa (F)")
        if not self._ventana_full_previa and ventana is not None:
            if self._ventana_max:
                ventana.showMaximized()
            else:
                ventana.showNormal()

    def _mostrar_controles(self, forzar=False):
        if not self._completa:
            return
        if not forzar:                                # ignora «movimientos» sin mover el mouse
            p = QCursor.pos()
            if (p - self._ult_pos).manhattanLength() < 4:
                return
            self._ult_pos = p
        else:
            self._ult_pos = QCursor.pos()
        if not self.barra.isVisible():
            self.barra.setVisible(True)
        self.video.unsetCursor()
        self._t_ocultar.start()

    def _ocultar_controles(self):
        if not self._completa:
            return
        if self.sonando() and not self.barra.underMouse() and not self.sl_pos.isSliderDown():
            self.barra.setVisible(False)
            self.video.setCursor(Qt.CursorShape.BlankCursor)
        else:
            self._t_ocultar.start()

    # ---- teclado
    def keyPressEvent(self, e):
        k = e.key()
        ctrl = bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)
        txt = e.text()
        if k == Qt.Key.Key_Escape and self._completa:
            self.salir_completa()
        elif k in (Qt.Key.Key_F, Qt.Key.Key_F11):
            self.alternar_completa()
        elif k in (Qt.Key.Key_Space, Qt.Key.Key_K):
            self.alternar_play()
        elif k == Qt.Key.Key_Left:
            if ctrl:
                self.saltar(-1, manual=True)
            else:
                self.mover_segundos(-SALTO_CORTO_S)
        elif k == Qt.Key.Key_Right:
            if ctrl:
                self.saltar(1, manual=True)
            else:
                self.mover_segundos(SALTO_CORTO_S)
        elif k == Qt.Key.Key_J:
            self.mover_segundos(-SALTO_LARGO_S)
        elif k == Qt.Key.Key_L:
            self.mover_segundos(SALTO_LARGO_S)
        elif k in (Qt.Key.Key_PageUp, Qt.Key.Key_P):
            self.saltar(-1, manual=True)
        elif k in (Qt.Key.Key_PageDown, Qt.Key.Key_N):
            self.saltar(1, manual=True)
        elif k == Qt.Key.Key_Up:
            self.sl_vol.setValue(self.sl_vol.value() + 5)
        elif k == Qt.Key.Key_Down:
            self.sl_vol.setValue(self.sl_vol.value() - 5)
        elif k == Qt.Key.Key_M:
            self.alternar_silencio()
        elif k == Qt.Key.Key_Home:
            self._ir_a_posicion(0)
        elif Qt.Key.Key_0.value <= int(k) <= Qt.Key.Key_9.value:
            self._ir_a_posicion(int(self._dur * (int(k) - Qt.Key.Key_0.value) / 10))
        elif txt in ("<", ">"):
            i = min(range(len(VELOCIDADES)), key=lambda j: abs(VELOCIDADES[j] - self._vel))
            i = max(0, min(len(VELOCIDADES) - 1, i + (1 if txt == ">" else -1)))
            self.poner_velocidad(VELOCIDADES[i])
        else:
            super().keyPressEvent(e)
            return
        self._mostrar_controles(True)
        e.accept()

    # ---- posición, saltos y velocidad
    def _al_duracion(self, dur):
        self._dur = max(0, int(dur))
        self.sl_pos.setRange(0, self._dur)
        self.lbl_dur.setText(_fmt_tiempo(self._dur))

    def _al_posicion(self, pos):
        if self.sl_pos.isSliderDown():
            return
        self.sl_pos.setValue(int(pos))
        seg = int(pos) // 1000
        if seg != self._seg_mostrado:                 # el texto solo cambia una vez por segundo
            self._seg_mostrado = seg
            self.lbl_pos.setText(_fmt_tiempo(pos))

    def _ir_a_posicion(self, ms):
        if self.player.source().isEmpty():
            return
        self.player.setPosition(max(0, min(int(ms), self._dur or int(ms))))

    def mover_segundos(self, s):
        """Retrocede (s < 0) o adelanta (s > 0) esos segundos en el opening actual."""
        if not self._rutas or self.player.source().isEmpty():
            return
        dur = self._dur or self.player.duration()
        nueva = self.player.position() + int(s * 1000)
        self.player.setPosition(max(0, min(nueva, max(0, dur - 300))))

    def _menu_velocidad(self):
        m = QMenu(self)
        for r in VELOCIDADES:
            a = m.addAction(f"{r:g}×" + ("  (normal)" if r == 1.0 else ""))
            a.setCheckable(True)
            a.setChecked(abs(r - self._vel) < 0.01)
            a.triggered.connect(lambda _=False, r=r: self.poner_velocidad(r))
        pos = self.b_vel.mapToGlobal(QPoint(0, 0))
        pos.setY(pos.y() - m.sizeHint().height())
        m.exec(pos)

    def poner_velocidad(self, r):
        self._vel = float(r)
        self.player.setPlaybackRate(self._vel)
        self.b_vel.setText(f"{self._vel:g}×")

    # ---- volumen
    def _cambio_volumen(self, v):
        self.audio.setVolume(v / 100)
        self.ic_vol.poner(v)
        if not self._silenciando:
            self.volumen_cambiado.emit(v)

    def alternar_silencio(self):
        self._silenciando = True              # silenciar con el altavoz no cambia el volumen guardado
        try:
            if self.sl_vol.value() > 0:
                self._vol_previo = self.sl_vol.value()
                self.sl_vol.setValue(0)
            else:
                self.sl_vol.setValue(self._vol_previo or OPENING_VOLUMEN)
        finally:
            self._silenciando = False

    # ---- lista y reproducción
    def sonando(self):
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _etiquetar(self):
        n = len(self._rutas)
        varios = n > 1
        self.b_ant.setVisible(varios)
        self.b_sig.setVisible(varios)
        self.lbl_n.setVisible(varios)
        if varios:
            self.lbl_n.setText(f"{self._idx + 1}/{n}")
        t = self._titulos[self._idx] if 0 <= self._idx < len(self._titulos) else ""
        self.lbl_t.setText(t)
        self.lbl_t.setToolTip(t)
        for w in (self.b_play, self.b_full, self.b_atr, self.b_ade, self.b_vel, self.sl_pos):
            w.setEnabled(n > 0)

    def cargar(self, rutas, autoplay=False, forzar=False, titulos=None, inicio=0):
        pares = [(r, titulos[i] if titulos and i < len(titulos) else Path(r).stem)
                 for i, r in enumerate(rutas) if Path(r).exists()]
        if not pares:
            self.detener()
            return
        rutas = [p[0] for p in pares]
        titulos = [p[1] for p in pares]
        actual = self._rutas[self._idx] if 0 <= self._idx < len(self._rutas) else None
        if not forzar and actual in rutas:            # misma lista: no reinicia el video
            self._rutas, self._titulos = rutas, titulos
            self._idx = rutas.index(actual)
            self._etiquetar()
            self.indice_cambiado.emit(self._idx)
            return
        sonaba = self.sonando()
        inicio = max(0, min(int(inicio), len(rutas) - 1))
        self._rutas, self._titulos, self._idx, self._fallos = rutas, titulos, inicio, 0
        if autoplay or sonaba:
            self._abrir(inicio, True, diferido=True)
        else:
            self._apagar()                            # lista lista, pero la pantalla sigue apagada
            self._etiquetar()
            self.indice_cambiado.emit(inicio)

    def _apagar(self):
        self._tok += 1
        self.player.stop()
        if not self.player.source().isEmpty():
            self.player.setSource(QUrl())
        self.reposo.setText(TXT_REPOSO)
        self.pantalla.setCurrentIndex(0)
        self._al_duracion(0)
        self.sl_pos.setValue(0)
        self.lbl_pos.setText("0:00")
        self._seg_mostrado = -1

    def _abrir(self, idx, reproducir, diferido=False):
        self._idx = idx
        self._tok += 1
        self._etiquetar()
        self.indice_cambiado.emit(idx)
        self.reposo.setText(TXT_REPOSO)
        self.pantalla.setCurrentIndex(1)
        self.player.setSource(QUrl.fromLocalFile(self._rutas[idx]))
        self.player.setPlaybackRate(self._vel)        # la velocidad elegida se mantiene
        if reproducir and diferido:
            tok = self._tok                           # arranca cuando la pantalla ya se dibujó
            QTimer.singleShot(350, lambda: self._arrancar(tok))
        elif reproducir:
            self.player.play()
        else:
            self.player.pause()

    def _arrancar(self, tok):
        if tok == self._tok and self._rutas and self.isVisible():
            self.player.play()

    def saltar(self, d, manual=False):
        if not self._rutas:
            return
        if len(self._rutas) == 1:
            if self.player.source().isEmpty():
                self._abrir(0, True)
            else:
                self.player.setPosition(0)
                self.player.play()
            return
        self._abrir((self._idx + d) % len(self._rutas), True)

    def reproducir_indice(self, i):
        if 0 <= i < len(self._rutas):
            self._abrir(i, True)

    def reproducir_ruta(self, ruta):
        if ruta in self._rutas:
            self._abrir(self._rutas.index(ruta), True)

    def alternar_play(self):
        if not self._rutas:
            return
        if self.sonando():
            self.player.pause()
        elif self.player.source().isEmpty():
            self._abrir(self._idx, True)
        else:
            self.player.play()

    def iniciar(self):
        if self._rutas and not self.sonando():
            self.alternar_play()

    def pausar(self):
        if self.sonando():
            self.player.pause()

    def pausar_por_pestana(self):
        if self.sonando():                            # solo recuerda si de verdad sonaba
            self._reanudar = True
            self.player.pause()

    def reanudar(self):
        if self._reanudar:
            self._reanudar = False
            self.player.play()

    def soltar(self):
        """Suelta el archivo (Windows no deja borrarlo ni renombrarlo mientras está en uso)
        pero conserva la lista: al pulsar ▶ vuelve a abrirse."""
        self._reanudar = False
        if self._completa:
            self.salir_completa()
        self._apagar()

    def liberar(self):
        self.soltar()
        self._rutas, self._titulos, self._idx = [], [], 0

    def detener(self):
        self.liberar()
        self._etiquetar()

    # ---- eventos del motor
    def _al_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            QTimer.singleShot(0, self._fin_de_video)

    def _fin_de_video(self):
        try:
            if self.player.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia:
                self.saltar(1)                        # siguiente; tras el último vuelve al primero
        except RuntimeError:
            pass

    def _al_estado(self, estado):
        sonando = estado == QMediaPlayer.PlaybackState.PlayingState
        self.b_play.set_icono("pause" if sonando else "play")
        if sonando:
            self._fallos = 0
            self.pantalla.setCurrentIndex(1)
            self.empezo.emit()
        else:
            self._mostrar_controles(True)             # en pausa, los controles siempre se ven

    def _al_error(self, *_):
        self._fallos += 1                             # un video roto se salta, sin bucles infinitos
        if len(self._rutas) > 1 and self._fallos < len(self._rutas):
            QTimer.singleShot(0, lambda: self.saltar(1))
        else:
            self.reposo.setText("⚠ No se pudo reproducir este video")
            self.pantalla.setCurrentIndex(0)


class DelegadoCatalogoOpening(QStyledItemDelegate):
    def sizeHint(self, opcion, indice):
        return QSize(180, max(75, opcion.fontMetrics.height() * 2 + 18))

    def paint(self, p, opcion, indice):
        datos = indice.data(Qt.ItemDataRole.UserRole + 1)
        if not datos:
            return
        p.save()
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            r = QRectF(opcion.rect).adjusted(3, 3, -3, -2)
            sel = bool(opcion.state & QStyle.StateFlag.State_Selected)
            a1 = QColor(Tema.a1())
            fondo = QColor(Tema.c("input"))
            p.setBrush(mezclar(fondo, a1, 0.21 if sel else 0.03))
            p.setPen(QPen(mezclar(QColor(Tema.c("border")), a1, 0.62 if sel else 0.1), 1))
            p.drawRoundedRect(r, 9, 9)
            poster = QRectF(r.x() + 6, r.y() + 5, 43, r.height() - 10)
            vista = opcion.widget.viewport() if opcion.widget is not None else None
            portada = CACHE_GRANDE.obtener_diferido(datos.get("portada"), 160, vista)
            if portada.isNull():
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(mezclar(fondo, a1, 0.19))
                p.drawRoundedRect(poster, 6, 6)
                p.setPen(QColor(Tema.c("muted")))
                p.drawText(poster, Qt.AlignmentFlag.AlignCenter, "▷")
            else:
                p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                dibujar_cover(p, poster, portada, 6, datos.get("enc"))
            titulo = QFont(opcion.font)
            titulo.setBold(True)
            alto = r.height() / 2
            x = poster.right() + 10
            ancho = max(0, r.right() - x - 28)
            texto_el(p, x, r.y() + 2, ancho, alto, datos["titulo"],
                     titulo, QColor(Tema.c("text")))
            texto_el(p, x, r.center().y(), ancho, alto - 2, datos["novela"],
                     opcion.font, QColor(Tema.c("muted")))
            p.setPen(a1)
            p.drawText(r.adjusted(0, 0, -10, 0),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       "♥" if datos["favorito"] else "▷")
        finally:
            p.restore()


class NyuhuhuGallery(QMainWindow):
    IDX_OPENINGS = 2          # pestañas de una novela: Galería · Música · Openings · Top
    IDX_TOP = 3
    IDX_FICHA = 4
    IDX_CLIPS = 5
    IDX_VOCES = 6
    PAG_OPENINGS = 6          # página «Openings» del panel principal

    def __init__(self):
        super().__init__()
        self.conn = conectar()
        cargar_ajustes(self.conn)
        self.sonda = SondaDuracion(self)
        self.sonda.lista.connect(self.al_duracion_pista)

        self.juego_id = self.juego_nombre = self.juego_carpeta = None
        self.heroina_id = self.heroina_nombre = None
        self.tamano = 260
        self.cargando = False
        self._galeria_id = None
        self.clips_reproductor = None
        self.voces_player = None
        self.cola, self.cola_idx, self.repetir = [], -1, 0
        self._pendientes = {}
        self._estilo_cache = None
        self._ultimo_clic = None
        self._atras_pila, self._adelante_pila = [], []     # historial de navegación
        self._nav_actual, self._navegando, self._nav_pend = None, False, False
        self._nav_tragar = None
        self._id_salida = b""
        self._timer_guardar = QTimer(self)
        self._timer_guardar.setSingleShot(True)
        self._timer_guardar.timeout.connect(self.guardar_pendientes)

        self.setWindowTitle("NyuhuhuGallery · Biblioteca VN")
        pant = QApplication.primaryScreen().availableGeometry()
        self.resize(min(1920, pant.width()), min(1080, pant.height()))
        self.setMinimumSize(1000, 680)

        self.crear_motor_audio()
        self.crear_interfaz()
        self.aplicar_tema()
        self.cargar_biblioteca()
        QApplication.instance().installEventFilter(self)
        self._iniciar_nav()
        self._iniciar_vigilante_audio()
        self._encolar_biblioteca_mp3()
        self._timer_mp3.start(1200)

    # -----------------------------------------------------
    # TEMA Y AJUSTES
    # -----------------------------------------------------

    def aplicar_tema(self):
        app = QApplication.instance()
        app.setFont(QFont(Tema.fuente, Tema.tam))
        estilo = construir_estilo()
        if estilo != self._estilo_cache:
            self._estilo_cache = estilo
            app.setStyleSheet(estilo)
        self.titulo_bib.setText(Tema.titulo_biblioteca or "Mi biblioteca")
        self.titulo_bib.setToolTip(self.titulo_bib.text())
        self.grid_juegos.ratio = Tema.ratio_tarjeta / 100
        self.grid_juegos.relayout()
        for b in self.findChildren(BotonAnimado):
            b.updateGeometry()
        self.fondo.reiniciar_particulas()
        for w in self.findChildren(QWidget):
            w.update()
        self.ajustar_rejilla()
        self.refrescar_info_heroina(self.heroina_actual_datos())

    def cambiar_ajuste(self, clave, valor):
        if clave == "titulo_biblioteca":
            Tema.titulo_biblioteca = valor
            self.titulo_bib.setText(valor)
            self.titulo_bib.setToolTip(valor)
            guardar_ajuste(self.conn, clave, valor)
            return
        if clave == "anim":
            valor = False
        setattr(Tema, AJUSTES[clave], valor)
        self._pendientes[clave] = valor
        self._timer_guardar.start(500)
        self.aplicar_tema()

    def guardar_pendientes(self):
        for clave, valor in self._pendientes.items():
            guardar_ajuste(self.conn, clave, valor)
        self._pendientes.clear()

    def alternar_tema(self):
        self.cambiar_ajuste("tema", "Claro" if Tema.nombre == "Oscuro" else "Oscuro")

    def abrir_ajustes(self, pestana=0):
        dlg = DialogoAjustes(self)
        dlg.tabs.setCurrentIndex(pestana)
        dlg.exec()

    def toast(self, texto, ms=3400):
        self.toast_w.mostrar(texto, ms)

    def alternar_pantalla_completa(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def changeEvent(self, e):
        super().changeEvent(e)
        if e.type() == QEvent.Type.WindowStateChange and hasattr(self, "opening"):
            if self.isMinimized():
                self.opening.pausar_por_pestana()
                if hasattr(self, "opening_global"):
                    self.opening_global.pausar_por_pestana()
            elif self.pila.currentIndex() == 1 and \
                    self.tabs_juego.currentIndex() == self.IDX_OPENINGS:
                self.opening.reanudar()
            elif self.pila.currentIndex() == self.PAG_OPENINGS:
                self.opening_global.reanudar()

    def _al_cambiar_pagina(self, i):
        """Dentro de una novela (página 1) la cabecera se esconde para dar espacio al opening;
        al salir, el video se detiene."""
        if i != 1:
            self.guia_pdf.close()
            self._detener_clips()
            self._detener_voces()
        if i != 1 and hasattr(self, "opening"):
            self.opening.detener()
        if i != self.PAG_OPENINGS and hasattr(self, "opening_global"):
            self.opening_global.detener()

    def ir_a_pagina(self, i):
        if i != 1 and Tema.acento_juego:                 # fuera de la novela vuelve tu color
            Tema.acento_juego = None
            QTimer.singleShot(0, self._restilizar_acento)
        if self.pila.currentIndex() == i:
            return
        self.pila.setCurrentIndex(i)
        if not Tema.anim or i == self.PAG_OPENINGS:      # el video no se mezcla con fundidos
            return
        w = self.pila.currentWidget()
        ef = QGraphicsOpacityEffect(w)
        w.setGraphicsEffect(ef)
        an = QPropertyAnimation(ef, b"opacity", w)
        an.setDuration(340)
        an.setStartValue(0.0)
        an.setEndValue(1.0)
        an.setEasingCurve(QEasingCurve.Type.OutCubic)
        an.finished.connect(lambda: w.setGraphicsEffect(None))
        an.start()
        self._an_pagina = an

    def eventFilter(self, obj, ev):
        t = ev.type()
        if (t in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress)
                and ev.key() == Qt.Key.Key_Escape
                and isinstance(obj, QWidget) and obj.window() is self
                and QApplication.activeModalWidget() is None
                and QApplication.activePopupWidget() is None
                and self._opening_activo() is not None):
            ev.accept()
            if t == QEvent.Type.KeyPress and not ev.isAutoRepeat():
                self._salir_del_opening()
            return True
        if t == QEvent.Type.MouseButtonPress or t == QEvent.Type.MouseButtonRelease:
            try:
                b = ev.button()
                if b == Qt.MouseButton.BackButton or b == Qt.MouseButton.ForwardButton:
                    if t == QEvent.Type.MouseButtonPress:
                        if self._nav_con_raton(b):
                            self._nav_tragar = b
                            return True
                    elif self._nav_tragar == b:
                        self._nav_tragar = None
                        return True
            except Exception:
                pass
        if (ev.type() == QEvent.Type.MouseButtonPress and Tema.clic_efecto
                and Tema.anim and QApplication.activeWindow() is self):
            try:
                marca = ev.timestamp()
                if marca != self._ultimo_clic:
                    self._ultimo_clic = marca
                    glob = ev.globalPosition().toPoint()          # copia: el evento puede morir
                    QTimer.singleShot(0, lambda g=glob: self._explosion_clic(g))
            except Exception:
                pass
        return False

    def _opening_activo(self):
        if self.pila.currentIndex() == self.PAG_OPENINGS:
            return self.opening_global
        if self.pila.currentIndex() == 1:
            pestaña = self.tabs_juego.currentIndex()
            if pestaña == self.IDX_OPENINGS:
                return self.opening
            if pestaña == self.IDX_CLIPS:
                return self.clips_reproductor
        return None

    def _salir_del_opening(self):
        reproductor = self._opening_activo()
        if reproductor is None:
            return
        if reproductor.en_completa():
            reproductor.salir_completa()
            reproductor.video.setFocus()
        elif not reproductor.player.source().isEmpty():
            reproductor.soltar()
            if reproductor is self.opening_global:
                self.lista_op_todos.setFocus()
            elif reproductor is self.clips_reproductor:
                self.lista_clips.setFocus()
            else:
                self.lista_openings.setFocus()
        elif reproductor is self.opening_global:
            self.volver_biblioteca()
        else:
            self.tabs_juego.setCurrentIndex(0)

    def _explosion_clic(self, glob):
        try:
            self.fondo.overlay.burst(self.fondo.mapFromGlobal(glob))
        except Exception:
            pass

    # -----------------------------------------------------
    # NAVEGACION (botones laterales del mouse · Alt+← / Alt+→)
    # -----------------------------------------------------

    def _iniciar_nav(self):
        self.pila.currentChanged.connect(lambda *_: self._nav_diferido())
        self.tabs_juego.currentChanged.connect(lambda *_: self._nav_diferido())
        self._nav_actual = self._estado_nav()
        QShortcut(QKeySequence("Alt+Left"), self, activated=self.nav_atras)
        QShortcut(QKeySequence("Alt+Right"), self, activated=self.nav_adelante)

    def _estado_nav(self):
        p = self.pila.currentIndex()
        if p == 1:                                    # dentro de una novela: cuál y qué pestaña
            return (1, self.juego_id, self.tabs_juego.currentIndex())
        return (p, None, None)

    def _nav_diferido(self):
        """Agrupa los cambios de un mismo movimiento (p. ej. entrar a una novela cambia de
        página y de pestaña) para que cuenten como UN solo paso del historial."""
        if self._nav_pend or self._navegando:
            return
        self._nav_pend = True
        QTimer.singleShot(0, self._registrar_nav)

    def _registrar_nav(self):
        self._nav_pend = False
        if self._navegando:
            return
        est = self._estado_nav()
        if est == self._nav_actual:
            return
        if self._nav_actual is not None:
            self._atras_pila.append(self._nav_actual)
            del self._atras_pila[:-80]
        self._adelante_pila.clear()
        self._nav_actual = est

    def _ir_nav(self, est):
        self._navegando = True
        try:
            p, jid, tab = est
            if p == 1:
                if jid is None:
                    return
                if self.pila.currentIndex() != 1 or self.juego_id != jid:
                    self.entrar_juego(jid)
                self.tabs_juego.setCurrentIndex(tab or 0)
            elif p == 0:
                self.volver_biblioteca()
            elif p == 2:
                self.abrir_favoritos()
            elif p == 3:
                self.abrir_hall()
            elif p == 4:
                self.abrir_info_heroinas()
            elif p == 5:
                self.abrir_cronologia()
            elif p == 6:
                self.abrir_openings()
            else:
                self.ir_a_pagina(p)
        except Exception:
            registrar_error_ui("navegación")
        finally:
            self._navegando = False
            self._nav_actual = self._estado_nav()

    def nav_atras(self):
        if not self._atras_pila:
            return
        destino = self._atras_pila.pop()
        if self._nav_actual is not None:
            self._adelante_pila.append(self._nav_actual)
        self._ir_nav(destino)

    def nav_adelante(self):
        if not self._adelante_pila:
            return
        destino = self._adelante_pila.pop()
        if self._nav_actual is not None:
            self._atras_pila.append(self._nav_actual)
        self._ir_nav(destino)

    def _nav_con_raton(self, boton):
        """Botón lateral del mouse. Devuelve True si lo atendió (entonces el clic no sigue).
        · Video en pantalla completa: «atrás» sale de ella.
        · Visor de capturas: atrás / adelante = captura anterior / siguiente.
        · Duelos y rankings: «atrás» deshace el último paso (igual que Retroceso).
        · Ventana principal: va por el historial (páginas, novelas y pestañas)."""
        atras = boton == Qt.MouseButton.BackButton
        if QApplication.activePopupWidget() is not None:
            return False
        activa = QApplication.activeModalWidget() or QApplication.activeWindow()
        if activa is not None and activa is not self:
            if isinstance(activa, VisorImagen):
                QTimer.singleShot(0, lambda: activa.navegar(-1 if atras else 1))
                return True
            f = getattr(activa, "_atras", None)
            if atras and callable(f):
                QTimer.singleShot(0, f)
                return True
            return False
        for rp in (getattr(self, "opening", None), getattr(self, "opening_global", None),
                       self.clips_reproductor):
            if rp is not None and rp.en_completa():
                if atras:
                    QTimer.singleShot(0, rp.salir_completa)
                return True
        if atras and self._atras_pila:
            QTimer.singleShot(0, self.nav_atras)
            return True
        if not atras and self._adelante_pila:
            QTimer.singleShot(0, self.nav_adelante)
            return True
        return False

    # -----------------------------------------------------
    # SALIDA DE AUDIO (parlantes <-> auriculares)
    # -----------------------------------------------------

    def _iniciar_vigilante_audio(self):
        """Qt deja cada QAudioOutput pegado al dispositivo con el que nació. Aquí se vigila la
        salida predeterminada de Windows y, cuando cambia, se pasa a ella la música y los
        openings (sin que tengas que reiniciar el programa)."""
        self._dispositivos = QMediaDevices(self)      # hay que conservarlo vivo
        self._id_salida = self._id_salida_actual()
        self._t_audio = QTimer(self)                  # junta varios avisos seguidos en uno
        self._t_audio.setSingleShot(True)
        self._t_audio.setInterval(350)
        self._t_audio.timeout.connect(self._reajustar_audio)
        self._dispositivos.audioOutputsChanged.connect(self._t_audio.start)
        self._t_vigia = QTimer(self)                  # respaldo: algunos controladores no avisan
        self._t_vigia.setInterval(2500)
        self._t_vigia.timeout.connect(self._vigilar_audio)
        self._t_vigia.start()

    @staticmethod
    def _id_salida_actual():
        try:
            return bytes(QMediaDevices.defaultAudioOutput().id())
        except Exception:
            return b""

    def _vigilar_audio(self):
        if self._id_salida_actual() != self._id_salida:
            self._reajustar_audio()

    def _reajustar_audio(self):
        try:
            dev = QMediaDevices.defaultAudioOutput()
            ident = bytes(dev.id())
            if ident == self._id_salida:
                return
            self._id_salida = ident
            if dev.isNull():
                return
            motores = [(self.audio, self.player)]
            if self.voces_player is not None:
                motores.append((self.voces_audio, self.voces_player))
            for rp in (getattr(self, "opening", None), getattr(self, "opening_global", None),
                       self.clips_reproductor):
                if rp is not None:
                    motores.append((rp.audio, rp.player))
            for audio, player in motores:
                sonaba = player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
                pos = player.position()
                audio.setDevice(dev)
                if sonaba:                            # reengancha el sonido en el mismo punto
                    QTimer.singleShot(150, lambda p=player, x=pos: self._reenganchar(p, x))
            self.toast(f"🔊 Salida de audio: {dev.description()}")
        except Exception:
            registrar_error_ui("cambio de salida de audio")

    @staticmethod
    def _reenganchar(player, pos):
        try:
            if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                player.pause()
                player.setPosition(pos)
                player.play()
        except RuntimeError:
            pass

    # -----------------------------------------------------
    # CONSTRUCCION DE LA INTERFAZ
    # -----------------------------------------------------

    def crear_interfaz(self):
        self.fondo = FondoWidget()
        self.setCentralWidget(self.fondo)
        raiz = QVBoxLayout(self.fondo)
        raiz.setContentsMargins(14, 8, 14, 8)
        raiz.setSpacing(8)

        self.pila = QStackedWidget()
        self.pila.addWidget(self.construir_biblioteca())
        self.pila.addWidget(self.construir_juego())
        self.pila.addWidget(self.construir_favoritos())
        self.pila.addWidget(self.construir_hall())
        self.pila.addWidget(self.construir_info_heroinas())
        self.pila.addWidget(self.construir_cronologia())
        self.pila.addWidget(self.construir_openings_global())       # página 6
        raiz.addWidget(self.pila, 1)
        self.pila.currentChanged.connect(self._al_cambiar_pagina)
        raiz.addWidget(self.construir_barra_player())
        self.fondo.overlay.raise_()
        self.toast_w = Toast(self.fondo)

        QShortcut(QKeySequence("F11"), self, activated=self.alternar_pantalla_completa)
        QShortcut(QKeySequence("Ctrl+I"), self, activated=self.importar_archivos)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.enfocar_busqueda)
        QShortcut(QKeySequence("Ctrl+A"), self, activated=self.seleccionar_todas)
        QShortcut(QKeySequence("Escape"), self, activated=self.limpiar_seleccion)
        QShortcut(QKeySequence("Ctrl+T"), self, activated=self.alternar_tema)
        QShortcut(QKeySequence("Ctrl+Space"), self, activated=self.alternar_play)
        QShortcut(QKeySequence("Ctrl+M"), self, activated=self.reproducir_aleatorio_global)
        QShortcut(QKeySequence("M"), self, activated=self.atajo_mover)

    def construir_biblioteca(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)
        panel = Cabecera()
        barra = QVBoxLayout(panel)
        barra.setContentsMargins(12, 7, 12, 7)
        barra.setSpacing(6)
        fila = QHBoxLayout()
        herramientas = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(0)
        self.titulo_bib = QLabel()
        self.titulo_bib.setObjectName("heading")
        self.titulo_bib.setWordWrap(True)
        self.titulo_bib.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.lbl_bib = QLabel("")
        self.lbl_bib.setObjectName("muted")
        col.addWidget(self.titulo_bib)
        col.addWidget(self.lbl_bib)
        fila.addLayout(col, 1)
        accesos = QHBoxLayout()
        accesos.setSpacing(5)
        for titulo, simbolo, accion in (
            ("Favoritas", "♡", self.abrir_favoritos),
            ("Ranking", "♕", self.abrir_hall),
            ("Personajes", "♙", self.abrir_info_heroinas),
            ("Cronología", "▤", self.abrir_cronologia),
            ("Openings", "▷", self.abrir_openings),
            ("Personalizar", "✎", self.abrir_ajustes),
        ):
            boton = AccesoBiblioteca(titulo, simbolo)
            boton.clicked.connect(accion)
            accesos.addWidget(boton)
        fila.addLayout(accesos)
        self.orden_bib = QComboBox()
        self.orden_bib.addItems(ORDENES_BIB)
        self.orden_bib.setToolTip("Ordenar las novelas")
        self.filtro_bib = QComboBox()
        self.filtro_bib.addItems(FILTROS_BIB)
        self.filtro_bib.setToolTip("Mostrar solo algunas novelas")
        for combo, clave in ((self.orden_bib, "orden_bib"), (self.filtro_bib, "filtro_bib")):
            try:
                f = self.conn.execute("SELECT valor FROM ajustes WHERE clave = ?",
                                      (clave,)).fetchone()
            except sqlite3.Error:
                f = None
            if f and clave == "orden_bib":
                f = (ORDENES_BIB_ANTIGUOS.get(f[0], f[0]),)
            if f and combo.findText(f[0]) >= 0:
                combo.setCurrentText(f[0])
            combo.currentTextChanged.connect(
                lambda txt, c=clave: (guardar_ajuste(self.conn, c, txt), self.cargar_biblioteca()))
        b_azar = BotonAnimado("🎲 Al azar")
        b_azar.setToolTip("Abre una novela cualquiera de las que se ven ahora")
        b_azar.clicked.connect(self.novela_al_azar)
        herramientas.addWidget(b_azar)
        herramientas.addWidget(self.orden_bib)
        herramientas.addWidget(self.filtro_bib)
        self.buscar_juego = QLineEdit()
        self.buscar_juego.setPlaceholderText("⌕  Buscar novela...")
        self.buscar_juego.setMinimumWidth(170)
        self._t_busq_bib = QTimer(self)
        self._t_busq_bib.setSingleShot(True)
        self._t_busq_bib.setInterval(180)
        self._t_busq_bib.timeout.connect(self.cargar_biblioteca)
        self.buscar_juego.textChanged.connect(lambda *_: self._t_busq_bib.start())
        herramientas.insertWidget(0, self.buscar_juego, 1)
        herramientas.addWidget(QLabel("Tarjetas"))
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(150, 380)
        sl.setValue(220)
        sl.setMaximumWidth(96)
        sl.valueChanged.connect(self.cambiar_tamano_tarjetas)
        herramientas.addWidget(sl)
        barra.addLayout(fila)
        barra.addLayout(herramientas)
        v.addWidget(panel)

        self.scroll_bib = QScrollArea()
        self.scroll_bib.setWidgetResizable(True)
        self.grid_juegos = GridTarjetas()
        self.grid_juegos.scroll = self.scroll_bib
        self.grid_juegos.reordenado.connect(self.guardar_orden_juegos)
        self.scroll_bib.setWidget(self.grid_juegos)
        self.scroll_bib.viewport().setAutoFillBackground(False)
        self.grid_juegos.setAutoFillBackground(False)
        v.addWidget(self.scroll_bib, 1)
        return w

    def construir_juego(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)

        fila = QHBoxLayout()
        volver = BotonAnimado("← Biblioteca")
        volver.clicked.connect(self.volver_biblioteca)
        fila.addWidget(volver)
        self.lbl_juego = QLabel("")
        self.lbl_juego.setObjectName("heading")
        fila.addWidget(self.lbl_juego, 1)
        self.btn_fechas = BotonFechas()          # fechas de inicio / fin y días jugados
        self.btn_fechas.clic.connect(self.editar_fechas_novela)
        fila.addWidget(self.btn_fechas)
        self.btn_nota = BotonAnimado("☆ Calificar")      # nota 1-10 de la novela
        self.btn_nota.setAutoDefault(False)
        self.btn_nota.setFixedHeight(38)
        self.btn_nota.setToolTip("Califica esta novela del 1 al 10")
        self.btn_nota.clicked.connect(self.elegir_nota_novela)
        fila.addWidget(self.btn_nota)
        self.orden = QComboBox()
        self.orden.addItems(["Orden manual", "Más recientes", "Nombre A-Z",
                             "Nombre Z-A", "Favoritos primero"])
        self.orden.currentTextChanged.connect(self.al_cambiar_orden)
        fila.addWidget(self.orden)
        v.addLayout(fila)

        self.tabs_juego = QTabWidget()
        self.tabs_juego.addTab(self.construir_galeria(), "🖼  Galería")
        self.tabs_juego.addTab(self.construir_musica(), "♪  Música")
        self.tabs_juego.addTab(self.construir_openings_novela(), "🎬  Openings")
        self.tabs_juego.addTab(self.construir_top(), "🏆  Top Heroínas")
        self.tabs_juego.addTab(self.construir_ficha_novela(), "📖 Ficha y guía")
        self.tabs_juego.addTab(self.construir_clips(), "🎞 Clips")
        self.tabs_juego.addTab(self.construir_voces(), "🎙 Voces")
        self.tabs_juego.currentChanged.connect(self._al_cambiar_pestana_juego)
        v.addWidget(self.tabs_juego, 1)
        return w

    def construir_ficha_novela(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 4, 4, 4)
        v.setSpacing(4)
        ficha = QDialog(w)
        ficha.setWindowTitle("Editar datos de la novela")
        ficha.setMinimumWidth(610)
        self.editor_ficha = ficha
        datos = QGridLayout(ficha)
        datos.setContentsMargins(12, 8, 12, 8)
        datos.setHorizontalSpacing(10)
        self.ficha_lanzamiento = QLineEdit()
        self.ficha_lanzamiento.setPlaceholderText("AAAA, AAAA-MM o AAAA-MM-DD")
        self.ficha_steam = QLineEdit()
        self.ficha_steam.setPlaceholderText("AAAA-MM-DD")
        self.ficha_desarrolladora = QLineEdit()
        self.ficha_desarrolladora.setPlaceholderText("Estudio de desarrollo")
        self.ficha_vndb = QLineEdit()
        self.ficha_vndb.setPlaceholderText("https://vndb.org/v1234")
        for fila, campos in enumerate((
            (("Lanzamiento original", self.ficha_lanzamiento), ("Lanzamiento en Steam", self.ficha_steam)),
            (("Desarrolladora", self.ficha_desarrolladora), ("VNDB", self.ficha_vndb)),
        )):
            for i, (texto, control) in enumerate(campos):
                datos.addWidget(QLabel(texto), fila, i * 2)
                datos.addWidget(control, fila, i * 2 + 1)
        datos.setColumnStretch(1, 1)
        datos.setColumnStretch(3, 1)
        guardar = BotonAnimado("Guardar datos")
        guardar.clicked.connect(self.guardar_ficha_novela)
        datos.addWidget(guardar, 0, 4)
        abrir = BotonAnimado("Abrir VNDB")
        abrir.clicked.connect(self.abrir_vndb_novela)
        datos.addWidget(abrir, 1, 4)
        cancelar = BotonAnimado("Cancelar")
        cancelar.clicked.connect(ficha.reject)
        datos.addWidget(cancelar, 2, 4)

        barra = QHBoxLayout()
        self.guia_estado = QLabel("Sin guía PDF")
        barra.addWidget(self.guia_estado, 1)
        self.btn_editar_datos = BotonAnimado("✎ Editar datos")
        self.btn_editar_datos.clicked.connect(self.editar_datos_novela)
        barra.addWidget(self.btn_editar_datos)
        adjuntar = BotonAnimado("Adjuntar o reemplazar PDF")
        adjuntar.clicked.connect(self.adjuntar_guia)
        barra.addWidget(adjuntar)
        self.guia_doble = BotonAnimado("Dos páginas")
        self.guia_doble.setCheckable(True)
        barra.addWidget(self.guia_doble)
        anterior = BotonAnimado("‹")
        anterior.setToolTip("Página anterior")
        anterior.clicked.connect(lambda: self._saltar_guia(-1))
        barra.addWidget(anterior)
        self.guia_pagina = QSpinBox()
        self.guia_pagina.setMinimum(1)
        barra.addWidget(self.guia_pagina)
        siguiente = BotonAnimado("›")
        siguiente.setToolTip("Página siguiente")
        siguiente.clicked.connect(lambda: self._saltar_guia(1))
        barra.addWidget(siguiente)
        self.guia_zoom = QComboBox()
        self.guia_zoom.addItems(["Ajustar al ancho", "Página completa", "100 %", "150 %", "200 %"])
        barra.addWidget(self.guia_zoom)
        v.addLayout(barra)

        self.guia_pdf = QPdfDocument(w)
        self.guia_visor = QPdfView(w)
        self.guia_visor.setDocument(self.guia_pdf)
        self.guia_visor_sec = QPdfView(w)
        self.guia_visor_sec.setDocument(self.guia_pdf)
        self.guia_visor_sec.setPageMode(QPdfView.PageMode.SinglePage)
        self.guia_divisor = QFrame()
        self.guia_divisor.setFrameShape(QFrame.Shape.VLine)
        self.guia_divisor.setFixedWidth(2)
        self.guia_fin = QLabel("Última página")
        self.guia_fin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.guia_fin.setObjectName("muted")
        self.guia_pareja = QStackedWidget()
        self.guia_pareja.addWidget(self.guia_visor_sec)
        self.guia_pareja.addWidget(self.guia_fin)
        self._zoom_guia_individual = 3
        self._zoom_guia_doble = 0
        self.guia_visor.setPageMode(QPdfView.PageMode.MultiPage)
        self.guia_visor.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        navegador = self.guia_visor.pageNavigator()
        navegador.currentPageChanged.connect(self._al_pagina_guia)
        self.guia_pagina.valueChanged.connect(self._ir_pagina_guia)
        self.guia_zoom.currentIndexChanged.connect(self._zoom_guia)
        self.guia_zoom.setCurrentIndex(3)
        lectura = QHBoxLayout()
        lectura.setSpacing(12)
        lectura.addWidget(self.guia_visor, 1)
        lectura.addWidget(self.guia_divisor)
        lectura.addWidget(self.guia_pareja, 1)
        self.guia_divisor.hide()
        self.guia_pareja.hide()
        self.guia_doble.toggled.connect(self._modo_guia)
        v.addLayout(lectura, 1)
        return w

    def editar_datos_novela(self):
        if self.juego_id is None:
            return
        fila = self.conn.execute("""
            SELECT lanzamiento, lanzamiento_steam, desarrolladora, vndb
            FROM ficha_novela WHERE juego_id = ?
        """, (self.juego_id,)).fetchone()
        controles = (self.ficha_lanzamiento, self.ficha_steam,
                     self.ficha_desarrolladora, self.ficha_vndb)
        for campo, valor in zip(controles, fila or ("", "", "", "")):
            campo.setText(valor or "")
        self.editor_ficha.exec()

    def _saltar_guia(self, direccion):
        pasos = 2 if self.guia_doble.isChecked() else 1
        self.guia_pagina.setValue(self.guia_pagina.value() + direccion * pasos)

    def _modo_guia(self, doble):
        pagina = self.guia_pagina.value()
        if doble:
            self._zoom_guia_individual = self.guia_zoom.currentIndex()
            zoom = self._zoom_guia_doble
        else:
            self._zoom_guia_doble = self.guia_zoom.currentIndex()
            zoom = self._zoom_guia_individual
        modo = QPdfView.PageMode.SinglePage if doble else QPdfView.PageMode.MultiPage
        bloqueado = self.guia_pagina.blockSignals(True)
        self.guia_visor.setPageMode(modo)
        self.guia_pagina.setValue(pagina)
        self.guia_pagina.blockSignals(bloqueado)
        self.guia_zoom.setCurrentIndex(zoom)
        self.guia_divisor.setVisible(doble)
        self.guia_pareja.setVisible(doble)
        self._ir_pagina_guia(pagina)

    def _pagina_derecha_guia(self, pagina):
        if self.guia_doble.isChecked():
            hay_siguiente = pagina + 1 < self.guia_pdf.pageCount()
            self.guia_pareja.setCurrentIndex(0 if hay_siguiente else 1)
            if hay_siguiente:
                self.guia_visor_sec.pageNavigator().jump(pagina + 1, QPointF())

    def _al_pagina_guia(self, pagina):
        previo = self.guia_pagina.blockSignals(True)
        self.guia_pagina.setValue(pagina + 1)
        self.guia_pagina.blockSignals(previo)
        self._pagina_derecha_guia(pagina)

    def _ir_pagina_guia(self, numero):
        if self.guia_pdf.status() == QPdfDocument.Status.Ready:
            self.guia_visor.pageNavigator().jump(numero - 1, QPointF())
            self._pagina_derecha_guia(numero - 1)

    def _zoom_guia(self, modo):
        for visor in (self.guia_visor, self.guia_visor_sec):
            if modo < 2:
                visor.setZoomMode(
                    QPdfView.ZoomMode.FitToWidth if modo == 0 else QPdfView.ZoomMode.FitInView)
            else:
                visor.setZoomMode(QPdfView.ZoomMode.Custom)
                visor.setZoomFactor((1.0, 1.5, 2.0)[modo - 2])

    @staticmethod
    def _vndb_novela(texto):
        enlace = re.fullmatch(
            r"(?:https?://(?:www\.)?vndb\.org/)?(v[0-9]+)/?", texto, re.IGNORECASE)
        return "https://vndb.org/" + enlace[1].lower() if enlace else ""

    def abrir_vndb_novela(self):
        enlace = self._vndb_novela(self.ficha_vndb.text().strip())
        if enlace:
            QDesktopServices.openUrl(QUrl(enlace))
        else:
            self.toast("Escribe un enlace de novela de VNDB, por ejemplo v1234.")

    def guardar_ficha_novela(self):
        if self.juego_id is None:
            return
        fecha = self.ficha_lanzamiento.text().strip()
        steam = self.ficha_steam.text().strip()
        estudio = self.ficha_desarrolladora.text().strip()
        for valor in (fecha, steam):
            if valor:
                try:
                    if not re.fullmatch(r"[0-9]{4}(?:-[0-9]{2}(?:-[0-9]{2})?)?", valor):
                        raise ValueError
                    datetime.date.fromisoformat(valor + {4: "-01-01", 7: "-01", 10: ""}[len(valor)])
                except ValueError:
                    QMessageBox.information(self.editor_ficha, "Fecha inválida", "Usa AAAA, AAAA-MM o AAAA-MM-DD.")
                    return
        texto = self.ficha_vndb.text().strip()
        enlace = self._vndb_novela(texto)
        if texto and not enlace:
            QMessageBox.information(self.editor_ficha, "Enlace inválido", "Usa un enlace como https://vndb.org/v1234.")
            return
        self.conn.execute("""
            INSERT INTO ficha_novela(juego_id, lanzamiento, vndb, lanzamiento_steam, desarrolladora)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(juego_id) DO UPDATE SET lanzamiento=excluded.lanzamiento,
                vndb=excluded.vndb, lanzamiento_steam=excluded.lanzamiento_steam,
                desarrolladora=excluded.desarrolladora
        """, (self.juego_id, fecha, enlace, steam, estudio))
        self.conn.commit()
        self.ficha_vndb.setText(enlace)
        self.editor_ficha.accept()
        self.toast("Datos de la novela guardados.")

    def _ruta_guia_adjunta(self):
        fila = self.conn.execute(
            "SELECT guia FROM ficha_novela WHERE juego_id=?", (self.juego_id,)
        ).fetchone()
        nombre = fila[0] if fila else ""
        return ASSETS / "guias" / nombre if re.fullmatch(
            rf"novela_{self.juego_id}_[a-z0-9_]+\.pdf", nombre) else None

    def _ruta_guia(self):
        adjunta = self._ruta_guia_adjunta()
        if adjunta is not None and adjunta.is_file():
            return adjunta
        carpeta = (ROOT / self.juego_carpeta).resolve()
        if carpeta.is_relative_to(ROOT.resolve()):
            return carpeta / "Guía de rutas - Nyuhuhu.pdf"
        return None

    def cargar_ficha_novela(self):
        if self.juego_id is None:
            return
        ficha = self.conn.execute(
            "SELECT lanzamiento, vndb, lanzamiento_steam, desarrolladora "
            "FROM ficha_novela WHERE juego_id=?", (self.juego_id,)
        ).fetchone() or ("", "", "", "")
        self.ficha_lanzamiento.setText(ficha[0])
        self.ficha_vndb.setText(ficha[1])
        self.ficha_steam.setText(ficha[2])
        self.ficha_desarrolladora.setText(ficha[3])
        self._cargar_guia()

    def _cargar_guia(self):
        self.guia_pdf.close()
        ruta = self._ruta_guia()
        paginas = 0
        if ruta is not None and ruta.is_file():
            if self.guia_pdf.load(str(ruta)) == QPdfDocument.Error.None_:
                paginas = self.guia_pdf.pageCount()
            self.guia_estado.setText(
                f"Guía PDF · {paginas} páginas" if paginas else "No se pudo leer la guía PDF")
        else:
            self.guia_estado.setText("Sin guía PDF")
        previo = self.guia_pagina.blockSignals(True)
        self.guia_pagina.setRange(1, max(1, paginas))
        self.guia_pagina.setValue(1)
        self.guia_pagina.blockSignals(previo)
        self.guia_pagina.setEnabled(bool(paginas))
        self.guia_zoom.setEnabled(bool(paginas))
        self.guia_doble.setEnabled(bool(paginas))
        self.guia_visor.setVisible(bool(paginas))
        self.guia_divisor.setVisible(bool(paginas) and self.guia_doble.isChecked())
        self.guia_pareja.setVisible(bool(paginas) and self.guia_doble.isChecked())
        if paginas:
            self._ir_pagina_guia(1)

    def adjuntar_guia(self):
        if self.juego_id is None:
            return
        origen, _ = QFileDialog.getOpenFileName(self, "Guía de la novela", str(Path.home()), "PDF (*.pdf)")
        if not origen:
            return
        anterior = self._ruta_guia_adjunta()
        carpeta = ASSETS / "guias"
        temporal = None
        guardado = False
        verificador = QPdfDocument(self)
        try:
            error = verificador.load(origen)
            valido = error == QPdfDocument.Error.None_ and verificador.pageCount() > 0
            verificador.close()
            if not valido:
                self.toast("El archivo no es un PDF legible o está protegido con contraseña.")
                return
            carpeta.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                    dir=carpeta, prefix=f"novela_{self.juego_id}_", suffix=".pdf", delete=False
            ) as salida:
                temporal = Path(salida.name)
            shutil.copyfile(origen, temporal)
            with self.conn:
                self.conn.execute("""
                    INSERT INTO ficha_novela(juego_id, guia) VALUES (?, ?)
                    ON CONFLICT(juego_id) DO UPDATE SET guia=excluded.guia
                """, (self.juego_id, temporal.name))
            guardado = True
            self._cargar_guia()
            if anterior is not None:
                QTimer.singleShot(500, lambda: self._borrar_archivo_temporal(anterior))
        except (OSError, sqlite3.Error):
            self.toast("No se pudo guardar el PDF.")
        finally:
            verificador.deleteLater()
            if temporal is not None and not guardado:
                self._borrar_archivo_temporal(temporal)

    def construir_galeria(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---- panel izquierdo: foto de la heroína + INFORMACIÓN VITAL (VNDB) ----
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(320)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(12, 12, 12, 12)
        self.cover_heroina = CoverWidget("", 200, editable=True)
        self.cover_heroina.encuadre_cambiado.connect(self.encuadre_heroina_cambiado)
        self._enc_pend = None
        self._t_enc = QTimer(self)
        self._t_enc.setSingleShot(True)
        self._t_enc.timeout.connect(self._guardar_encuadre_heroina)
        pl.addWidget(self.cover_heroina, 1)
        self.lbl_heroina = QLabel("—")       # el nombre ya se dibuja sobre la foto
        self.lbl_heroina.setObjectName("heading")
        self.lbl_heroina.setVisible(False)
        pl.addWidget(self.lbl_heroina)
        self.lbl_stats = QLabel("")
        self.lbl_stats.setObjectName("muted")
        self.lbl_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pl.addWidget(self.lbl_stats)
        self.ficha = FichaHeroina()           # cumpleaños / seiyuu / altura y medidas, sin scroll
        pl.addWidget(self.ficha)
        fila_b = QHBoxLayout()
        b_foto = BotonAnimado("📷 Foto")
        b_foto.clicked.connect(self.cambiar_foto_heroina)
        fila_b.addWidget(b_foto)
        self.b_info = BotonAnimado("✎ Editar información", primario=True)
        self.b_info.clicked.connect(self.editar_info_heroina)
        fila_b.addWidget(self.b_info)
        pl.addLayout(fila_b)
        splitter.addWidget(panel)

        # ---- centro: galería ----
        der = QWidget()
        der_lay = QVBoxLayout(der)
        der_lay.setContentsMargins(0, 0, 0, 0)
        self.pila_gal = QStackedWidget()
        gal_w = QWidget()                      # página 0: la galería de capturas
        dl = QVBoxLayout(gal_w)
        dl.setContentsMargins(0, 0, 0, 0)
        herr = QHBoxLayout()
        herr.addWidget(QLabel("Miniaturas"))
        self.slider_tamano = QSlider(Qt.Orientation.Horizontal)
        self.slider_tamano.setRange(140, 480)
        self.slider_tamano.setValue(self.tamano)
        self.slider_tamano.setMaximumWidth(180)
        self.slider_tamano.valueChanged.connect(self.cambiar_tamano)
        herr.addWidget(self.slider_tamano)
        self.lbl_tamano = QLabel(f"{self.tamano} px")
        herr.addWidget(self.lbl_tamano)
        herr.addStretch()
        for texto, fn in (("＋ Importar", self.importar_archivos),
                          ("📂 Carpeta", self.importar_carpeta),
                          ("🎲 Al azar", self.imagen_al_azar)):
            b = BotonAnimado(texto)
            b.clicked.connect(fn)
            herr.addWidget(b)
        dl.addLayout(herr)

        herr2 = QHBoxLayout()
        for texto, fn in (("★ Favorito", self.alternar_favoritos),
                          ("✎ Etiquetas", self.editar_etiquetas),
                          ("⇄ Mover  (M)", self.mover_seleccion),
                          ("⚡ Repetir mover", self.repetir_movimiento),
                          ("🗑 Eliminar", self.eliminar_imagenes)):
            b = BotonAnimado(texto)
            b.clicked.connect(fn)
            herr2.addWidget(b)
        herr2.addStretch()
        dl.addLayout(herr2)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.currentChanged.connect(self.actualizar_galeria)
        self.listas = []
        self.delegado = DelegadoMiniatura(self)
        for cat in CATEGORIAS:
            lista = ListaGaleria()
            lista.setItemDelegate(self.delegado)
            lista.archivos_arrastrados.connect(self.importar_rutas_arrastradas)
            lista.itemDoubleClicked.connect(self.abrir_imagen_seleccionada)
            lista.itemSelectionChanged.connect(self.actualizar_seleccion_info)
            lista.orden_cambiado.connect(self.guardar_orden_galeria)
            lista.redimensionada.connect(self.ajustar_rejilla)
            lista.customContextMenuRequested.connect(
                lambda punto, l=lista: self.menu_contextual(l, punto))
            self.tabs.addTab(lista, cat)
            self.listas.append(lista)
        dl.addWidget(self.tabs, 1)

        pie = QHBoxLayout()
        self.estadisticas = QLabel("")
        self.estadisticas.setObjectName("muted")
        pie.addWidget(self.estadisticas, 1)
        self.seleccion_info = QLabel("0 seleccionadas")
        self.seleccion_info.setObjectName("muted")
        pie.addWidget(self.seleccion_info)
        dl.addLayout(pie)
        self.perfil_sec = PerfilPersonaje()    # página 1: perfil automático del personaje secundario
        self.pila_gal.addWidget(gal_w)
        self.pila_gal.addWidget(self.perfil_sec)
        der_lay.addWidget(self.pila_gal, 1)

        # ---- panel derecho: HEROÍNAS (tres tarjetas separadas; las vacías se encogen) ----
        panel_her = QFrame()
        panel_her.setObjectName("panel")
        panel_her.setFixedWidth(320)
        hl2 = QVBoxLayout(panel_her)
        hl2.setContentsMargins(14, 14, 14, 14)
        hl2.setSpacing(10)
        self._flechas = {}

        def grupo(titulo, simbolo, tipo, minimo=0):
            caja = QFrame()
            caja.setObjectName("grupo")
            lay = QVBoxLayout(caja)
            lay.setContentsMargins(14, 12, 14, 14)
            lay.setSpacing(10)
            cab = QHBoxLayout()
            cab.setSpacing(8)
            lb = QLabel(f"{simbolo}  {titulo}")
            lb.setObjectName("sec_titulo")
            cab.addWidget(lb)
            cuenta = QLabel("0")
            cuenta.setObjectName("sec_cuenta")
            cab.addWidget(cuenta)
            for simbolo_f, paso in (("▲", -1), ("▼", 1)):      # subir / bajar el panel
                bf = BotonRedondo(simbolo_f, 24, pt=max(6, Tema.tam - 3))
                bf.setToolTip("Subir este panel" if paso < 0 else "Bajar este panel")
                bf.clicked.connect(lambda _=False, t=tipo, d=paso: self.mover_grupo(t, d))
                cab.addWidget(bf)
                self._flechas.setdefault(tipo, []).append(bf)
            cab.addStretch()
            lay.addLayout(cab)
            lista = ListaPersonajes(tipo)
            lista.setObjectName("personajes")
            lista.setItemDelegate(DelegadoPersonaje(lista))
            if minimo:
                lista.setMinimumHeight(minimo)
            lista.model().rowsMoved.connect(
                lambda *a, l=lista: QTimer.singleShot(0, lambda: self.guardar_orden_heroinas(l)))
            lista.customContextMenuRequested.connect(
                lambda punto, l=lista: self.menu_heroina(punto, l))
            lista.currentItemChanged.connect(
                lambda act, ant, l=lista: self.al_seleccionar_personaje(l, act))
            lista.personaje_soltado.connect(self.mover_personaje)
            lista.arrastre_iniciado.connect(lambda: self.ajustar_listas_pers(True))
            lista.arrastre_terminado.connect(lambda: self.ajustar_listas_pers(False))
            lay.addWidget(lista, 1)
            return caja, cab, lista, cuenta

        def boton(cab, texto, fn, lado=30, primario=False):
            b = BotonRedondo(texto, lado, primario=primario, pt=Tema.tam + 1)
            b.clicked.connect(fn)
            cab.addWidget(b)
            return b

        caja_h, cab_h, self.lista_heroinas, cnt_h = grupo("Heroínas", "♡", "heroina", 150)
        boton(cab_h, "⇩", self.importar_heroina)
        boton(cab_h, "＋", lambda: self.nueva_heroina("heroina"), 34, True)

        caja_s, cab_s, self.lista_subs, cnt_s = grupo("Sub-heroínas", "✧", "sub")
        boton(cab_s, "＋", lambda: self.nueva_heroina("sub"))

        caja_p, cab_p, self.lista_secundarias, cnt_p = grupo("Secundarios", "☆", "secundaria")
        boton(cab_p, "＋", lambda: self.nueva_heroina("secundaria"))

        self._cuentas = [(self.lista_heroinas, cnt_h), (self.lista_subs, cnt_s),
                         (self.lista_secundarias, cnt_p)]
        self.listas_pers = [self.lista_heroinas, self.lista_subs, self.lista_secundarias]
        self._lista_pers = self.lista_heroinas
        self._pers_id = None
        self._sel_secundaria = False
        self._cajas_pers = {"heroina": caja_h, "sub": caja_s, "secundaria": caja_p}
        self._orden_paneles = self._leer_orden_paneles()
        self._split_pers = DivisorPaneles()
        self._split_pers.alto_ok = self.repartir_paneles
        for t in self._orden_paneles:
            self._split_pers.addWidget(self._cajas_pers[t])
        self._relleno_pers = QWidget()          # absorbe el espacio que sobre
        self._relleno_pers.setMinimumHeight(0)
        self._split_pers.addWidget(self._relleno_pers)
        hl2.addWidget(self._split_pers, 1)
        self._t_pan = QTimer(self)
        self._t_pan.setSingleShot(True)
        self._t_pan.timeout.connect(self.guardar_reparto_paneles)
        self._split_pers.splitterMoved.connect(lambda *a: self._t_pan.start(400))
        self._split_pers.restablecer.connect(self.restablecer_reparto_paneles)
        self.ajustar_listas_pers()
        self._actualizar_flechas()

        ext = QWidget()
        hl = QHBoxLayout(ext)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(10)
        hl.addWidget(der, 1)
        hl.addWidget(panel_her)
        splitter.addWidget(ext)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([400, 1100])
        return splitter

    # -----------------------------------------------------
    # FAVORITOS (todas las novelas en un solo apartado)
    # -----------------------------------------------------

    def construir_favoritos(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        fila = QHBoxLayout()
        volver = BotonAnimado("← Biblioteca")
        volver.clicked.connect(self.volver_biblioteca)
        fila.addWidget(volver)
        col = QVBoxLayout()
        t = QLabel("★ Capturas Favoritas")
        t.setObjectName("heading")
        self.lbl_fav = QLabel("")
        self.lbl_fav.setObjectName("muted")
        col.addWidget(t)
        col.addWidget(self.lbl_fav)
        fila.addLayout(col, 1)
        v.addLayout(fila)
        v.addWidget(self.construir_top_caps(), 1)
        return w

    # ---------- capturas favoritas: miniaturas a la izquierda, grande a la derecha ----------

    def construir_top_caps(self):
        self.divisores_top = []
        fila_p = self.conn.execute("SELECT valor FROM ajustes WHERE clave = 'top_split'").fetchone()
        try:
            self._prop_top = min(0.85, max(0.15, float(fila_p[0]))) if fila_p else None
        except ValueError:
            self._prop_top = None
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(8)
        self.tabs_caps = QTabWidget()
        self.tabs_caps.setDocumentMode(True)
        self.top_caps, self.cab_caps, self.panel_caps = {}, {}, {}
        for n, cat in enumerate(("CG H", "CG normal", "SD", "No-CG"), 1):
            pag = QWidget()
            pl = QVBoxLayout(pag)
            pl.setContentsMargins(6, 12, 6, 6)
            pl.setSpacing(12)
            cab = CabeceraTop(n, cat)
            pl.addWidget(cab)
            wid = TopCapturasMini()
            wid.cat = cat
            wid.vacio = f"Aún no hay favoritas en {cat}."
            sc = QScrollArea()
            sc.setWidgetResizable(True)
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            sc.setFrameShape(QFrame.Shape.NoFrame)
            sc.setWidget(wid)
            sc.setMinimumWidth(340)
            sc.viewport().setAutoFillBackground(False)
            wid.setAutoFillBackground(False)
            wid.scroll = sc
            panel = PanelCaptura()
            sp = DivisorProporcional(Qt.Orientation.Horizontal, self._prop_top)
            sp.setChildrenCollapsible(False)
            sp.addWidget(sc)
            sp.addWidget(panel)
            sp.setStretchFactor(0, 0)
            sp.setStretchFactor(1, 1)
            sp.setSizes([420, 1100])
            sp.proporcion_cambiada.connect(self._guardar_prop_top)
            self.divisores_top.append(sp)
            pl.addWidget(sp, 1)
            wid.orden_cambiado.connect(lambda ids, c=cat: self.guardar_top_caps(c, ids))
            wid.abrir.connect(lambda iid, c=cat: self.abrir_top_cap(c, iid))
            wid.menu_pedido.connect(lambda iid, pt, c=cat: self.menu_top_cap(c, iid, pt))
            wid.elegida.connect(lambda iid, c=cat: self.mostrar_captura(c, iid))
            panel.abrir.connect(lambda c=cat: self.abrir_top_cap(c, self.top_caps[c].sel))
            self.tabs_caps.addTab(pag, f"Parte {n} · {cat}")
            self.top_caps[cat] = wid
            self.cab_caps[cat] = cab
            self.panel_caps[cat] = panel
        self.btn_rank = BotonAnimado("⭐ Calificar y rankear  ▾", primario=True)
        self.btn_rank.clicked.connect(self.menu_rankear)
        self.tabs_caps.setCornerWidget(self.btn_rank, Qt.Corner.TopRightCorner)
        v.addWidget(self.tabs_caps, 1)
        return w

    CATS_TOP = ("CG H", "CG normal", "SD", "No-CG")

    def _guardar_prop_top(self, r):
        """Lo que estires en una parte del Top se aplica a las cuatro y se guarda para la próxima vez."""
        self._prop_top = r
        for d in self.divisores_top:
            if d is not self.sender():
                d.poner_proporcion(r)
        self._pendientes["top_split"] = f"{r:.4f}"
        self._timer_guardar.start(500)

    def menu_rankear(self):
        m = QMenu(self)
        a_cal = m.addAction("⭐ Calificar capturas  (1 a 5 estrellas)")
        m.addSeparator()
        a_ran = m.addAction("⚔ Rankear por estrellas  (duelos dentro de cada nivel)")
        a_ult = m.addAction("⚔ Meter solo las últimas de un nivel…")
        acc = m.exec(self.btn_rank.mapToGlobal(self.btn_rank.rect().bottomLeft()))
        if acc == a_cal:
            self.calificar_capturas()
        elif acc == a_ran:
            self.rankear_por_estrellas()
        elif acc == a_ult:
            self.rankear_por_estrellas(solo_ultimas=True)

    def calificar_capturas(self):
        cat = self.CATS_TOP[self.tabs_caps.currentIndex()]
        w = self.top_caps[cat]
        items = [w.items[i] for i in w.orden]
        if not items:
            self.toast(f"No hay favoritas en {cat} para calificar")
            return
        sin = [i for i in items if not i.get("estrellas")]
        if sin:
            lista = sin                                  # primero las que aún no tienen estrellas
        else:
            r = QMessageBox.question(
                self, "Calificar", f"Todas las capturas de {cat} ya tienen estrellas.\n"
                "¿Quieres revisarlas de nuevo?")
            if r != QMessageBox.StandardButton.Yes:
                return
            lista = items
        dlg = DialogoRankear(self, cat, lista, "calificar")
        if dlg.exec():
            self.poner_estrellas(dlg.notas)

    def poner_estrellas(self, notas):
        """notas: {id_captura: 1..5}. Una captura que cambia de nivel entra al FINAL de su
        nuevo nivel (después puedes meterla en su sitio con duelos)."""
        previas = {}
        for w in self.top_caps.values():
            previas.update({i: it.get("estrellas", 0) for i, it in w.items.items()})
        cambios = 0
        for iid, n in notas.items():
            if previas.get(iid, 0) != n:
                self.conn.execute("UPDATE imagenes SET estrellas = ?, top_cap = 1000000 "
                                  "WHERE id = ?", (n, iid))
                cambios += 1
        self.conn.commit()
        self.cargar_top_caps()
        self.toast(f"⭐ {cambios} calificaciones guardadas · el top se acomodó por estrellas"
                   if cambios else "Las calificaciones no cambiaron")

    def rankear_por_estrellas(self, solo_ultimas=False):
        """Cada nivel (5★, 4★…) hace duelos solo contra sí mismo. El resultado final deja
        todos los 5★ arriba, luego los 4★ (su mejor queda justo debajo de la última 5★)…"""
        cat = self.CATS_TOP[self.tabs_caps.currentIndex()]
        w = self.top_caps[cat]
        items = [w.items[i] for i in w.orden]
        niveles = {s: [i for i in items if i.get("estrellas") == s] for s in (5, 4, 3, 2, 1)}
        if not any(niveles.values()):
            self.toast("Primero califica tus capturas con «⭐ Calificar capturas»")
            return
        minimo = 3 if solo_ultimas else 2
        posibles = [s for s in (5, 4, 3, 2, 1) if len(niveles[s]) >= minimo]
        if not posibles:
            self.toast("Ningún nivel tiene suficientes capturas para enfrentarlas")
            return
        etiquetas = [f"{'★' * s}   ({len(niveles[s])} capturas)" for s in posibles]
        opciones = etiquetas if solo_ultimas else ["Todos los niveles, de 5★ a 1★"] + etiquetas
        txt, ok = QInputDialog.getItem(
            self, "Rankear por estrellas",
            "¿Qué nivel quieres rankear?\nCada nivel compite solo contra sí mismo: los 5★ "
            "siempre quedan sobre los 4★ y así.", opciones, 0, False)
        if not ok:
            return
        k = opciones.index(txt)
        if solo_ultimas:
            s = posibles[k]
            n, ok = QInputDialog.getInt(
                self, "Duelos", f"¿Cuántas de las ÚLTIMAS de {'★' * s} quieres meter en el "
                "ranking?\n(las que acabas de calificar van al final del nivel; el resto de "
                "tu orden no se toca)", min(10, len(niveles[s]) - 1), 1, len(niveles[s]) - 1)
            if not ok:
                return
            plan = [(s, n)]
        elif k == 0:
            plan = [(s, 0) for s in posibles]
        else:
            plan = [(posibles[k - 1], 0)]
        sin_estrellas = [i["id"] for i in items if not i.get("estrellas")]
        hechos = 0
        for s, ultimas in plan:
            dlg = DialogoRankear(self, f"{cat} · {'★' * s}", niveles[s], "duelos", ultimas)
            if not dlg.exec():
                break
            hechos += 1
            niveles[s] = [w.items[i] for i in dlg.resultado]
            ids = [i["id"] for t in (5, 4, 3, 2, 1) for i in niveles[t]] + sin_estrellas
            for pos, iid in enumerate(ids, 1):           # se guarda nivel por nivel
                self.conn.execute("UPDATE imagenes SET top_cap = ? WHERE id = ?", (pos, iid))
            self.conn.commit()
        self.cargar_top_caps()
        if hechos:
            self.toast(f"⚔ {hechos} {'nivel rankeado' if hechos == 1 else 'niveles rankeados'}"
                       f" en {cat}")

    def datos_heroina_captura(self, it):
        """Foto de la heroína de una captura favorita y su novela (franja bajo la captura)."""
        hid = it.get("heroina_id")
        if not hid:
            return {"general": True, "juego": it["juego"]}
        f = self.conn.execute("SELECT nombre, foto, foto_enc FROM heroinas WHERE id = ?",
                              (hid,)).fetchone()
        if not f or f[0] == "General":
            return {"general": True, "juego": it["juego"]}
        return {"nombre": f[0], "foto": f[1], "enc": parse_enc(f[2]), "juego": it["juego"]}

    def mostrar_captura(self, cat, iid):
        w, panel = self.top_caps[cat], self.panel_caps[cat]
        it = w.items.get(iid)
        if not it:
            panel.visor.poner("")
            panel.info.poner(None)
            return
        est = it.get("estrellas", 0)
        panel.visor.poner(it["ruta"], it["titulo"],
                          it["sub"] + (f"  ·  {'★' * est}" if est else ""),
                          w.orden.index(iid) + 1)
        panel.info.poner(self.datos_heroina_captura(it))

    def cargar_top_caps(self):
        if not hasattr(self, "top_caps"):
            return
        c = self.conn
        c.execute("UPDATE imagenes SET top_cap = 0 WHERE favorito = 0 AND top_cap <> 0")
        for cat in CATEGORIAS:
            try:
                filas = c.execute("""
                    SELECT i.id, i.ruta, i.nota_titulo, i.top_cap, j.nombre,
                           COALESCE(h.nombre, 'General'), i.juego_id, i.heroina_id, i.estrellas
                    FROM imagenes i
                    JOIN juegos j ON j.id = i.juego_id
                    LEFT JOIN heroinas h ON h.id = i.heroina_id
                    WHERE i.favorito = 1 AND i.categoria = ?
                    ORDER BY i.estrellas DESC, CASE WHEN i.top_cap = 0 THEN 1 ELSE 0 END,
                             i.top_cap, i.orden_fav, i.id
                """, (cat,)).fetchall()
                filas = [f for f in filas if Path(f[1]).exists()]
                for pos, f in enumerate(filas, 1):          # puestos 1..n sin huecos
                    if f[3] != pos:
                        c.execute("UPDATE imagenes SET top_cap = ? WHERE id = ?", (pos, f[0]))
                items = [dict(id=i, ruta=r, titulo=nt or Path(r).stem, sub=f"{jn} · {hn}",
                              juego=jn, heroina=hn, cat=cat, juego_id=ji, heroina_id=hi,
                              estrellas=es)
                         for i, r, nt, tc, jn, hn, ji, hi, es in filas]
                self.top_caps[cat].poner(items)
                self.cab_caps[cat].poner(
                    len(items), len({i["juego"] for i in items}),
                    len({clave_heroina(i["heroina"]) for i in items if i["heroina"] != "General"}))
            except Exception:
                registrar_error_ui(f"cargar_top_caps · {cat}")
        c.commit()

    def guardar_top_caps(self, cat, ids):
        for pos, iid in enumerate(ids, 1):
            self.conn.execute("UPDATE imagenes SET top_cap = ? WHERE id = ?", (pos, iid))
        self.conn.commit()
        w = self.top_caps[cat]
        niv = [w.items[i].get("estrellas", 0) for i in ids if i in w.items]
        if niv != sorted(niv, reverse=True):         # se soltó fuera de su nivel de estrellas
            self.cargar_top_caps()
            self.toast("Solo puedes mover una captura dentro de su mismo nivel de ⭐")
            return
        it = w.items.get(ids[0])
        self.mostrar_captura(cat, w.sel)             # el puesto cambió
        self.toast(f"🏅 Top {cat} guardado · #1: {it['sub']}" if it
                   else f"🏅 Top {cat} guardado")

    def abrir_top_cap(self, cat, iid):
        if iid is None:
            return
        w = self.top_caps[cat]
        rutas = [w.items[i]["ruta"] for i in w.orden]
        if iid in w.orden:
            self.abrir_visor(rutas, w.orden.index(iid))

    def menu_top_cap(self, cat, iid, punto):
        w = self.top_caps[cat]
        it = w.items.get(iid)
        if not it:
            return
        m = QMenu(self)
        a_ver = m.addAction("Abrir imagen")
        a_copia = m.addAction("📋 Copiar imagen")
        a_ir = m.addAction("Ir a la novela y heroína")
        a_ubi = m.addAction("Abrir ubicación del archivo")
        m_est = m.addMenu("⭐ Calificar")
        acts_est = {m_est.addAction("★" * k + f"   ({k})"): k for k in (5, 4, 3, 2, 1)}
        m.addSeparator()
        a_quitar = m.addAction("☆ Quitar de favoritos")
        acc = m.exec(punto)
        if acc == a_ver:
            self.abrir_top_cap(cat, iid)
        elif acc == a_copia:
            if copiar_imagen_portapapeles(it["ruta"]):
                self.toast("📋 Imagen copiada")
        elif acc == a_ir:
            f = self.conn.execute(
                "SELECT juego_id, heroina_id, categoria FROM imagenes WHERE id = ?",
                (iid,)).fetchone()
            if f:
                self.ir_a_captura({"juego_id": f[0], "heroina_id": f[1], "categoria": f[2]})
        elif acc == a_ubi:
            if Path(it["ruta"]).exists():
                os.startfile(str(Path(it["ruta"]).parent))
        elif acc in acts_est:
            self.poner_estrellas({iid: acts_est[acc]})
        elif acc == a_quitar:
            self.conn.execute("UPDATE imagenes SET favorito = 0, top_cap = 0 WHERE id = ?",
                              (iid,))
            self.conn.commit()
            self.cargar_top_caps()
            self.cargar_favoritos()

    def extras_heroinas(self, ids):
        """Capturas por categoría y muestras AL AZAR de cada heroína (se sortean en cada carga):
          · podio: 1 captura CG normal + 2 CG H (si falta de un tipo se completa con el otro)
          · fila (4.º puesto en adelante): 1 sola captura CG H
        Devuelve (cats, podio, fila); las muestras son listas de (ruta, categoría)."""
        cats = {i: {} for i in ids}
        podio = {i: [] for i in ids}
        fila = {i: [] for i in ids}
        if not ids:
            return cats, podio, fila
        q = ",".join("?" * len(ids))
        for hid, cat, n in self.conn.execute(
                f"SELECT heroina_id, categoria, COUNT(*) FROM imagenes "
                f"WHERE heroina_id IN ({q}) GROUP BY heroina_id, categoria", ids):
            cats[hid][cat] = n
        pool = {i: {"CG normal": [], "CG H": []} for i in ids}
        for hid, cat, ruta in self.conn.execute(
                f"SELECT heroina_id, categoria, ruta FROM imagenes "
                f"WHERE heroina_id IN ({q}) AND categoria IN ('CG normal', 'CG H')", ids):
            pool[hid][cat].append(ruta)

        def toma(lista, n):                     # primeras n que existen en el disco
            out = []
            for ruta in lista:
                if len(out) >= n:
                    break
                if Path(ruta).exists():
                    out.append(ruta)
            return out

        for hid in ids:
            normales, hs = pool[hid]["CG normal"], pool[hid]["CG H"]
            random.shuffle(normales)
            random.shuffle(hs)
            cg, hh = toma(normales, 1), toma(hs, 2)
            if not cg:                          # sin CG normal: se completa con H
                hh = toma(hs, 3)
            elif len(hh) < 2:                   # pocas H: se completa con CG normal
                cg = toma(normales, 3 - len(hh))
            podio[hid] = [(r, "CG normal") for r in cg] + [(r, "CG H") for r in hh]
            fila[hid] = ([(r, "CG H") for r in toma(hs, 1)]
                         or [(r, "CG normal") for r in toma(normales, 1)])   # sin H: CG normal
        return cats, podio, fila

    def abrir_favoritos(self):
        self.cargar_favoritos()
        self.pila.setCurrentIndex(2)          # sin fundido: esta página es pesada

    def contar_favoritos(self):
        return self.conn.execute(
            "SELECT COUNT(*) FROM imagenes WHERE favorito = 1").fetchone()[0]

    def actualizar_contador_favoritos(self):
        n = self.contar_favoritos()
        if hasattr(self, "lbl_fav"):
            self.lbl_fav.setText(
                f"{n} {'captura favorita' if n == 1 else 'capturas favoritas'} de todas tus novelas"
                if n else "Aún no tienes favoritas.")

    def cargar_favoritos(self, *args):
        """Recarga las secciones de capturas favoritas."""
        self.cargar_top_caps()
        self.actualizar_contador_favoritos()

    def ir_a_captura(self, d):
        self.entrar_juego(d["juego_id"])
        if d.get("heroina_id"):
            self.cargar_heroinas(d["heroina_id"])
        if d["categoria"] in CATEGORIAS:
            self.tabs.setCurrentIndex(CATEGORIAS.index(d["categoria"]))

    def abrir_visor(self, items, indice):
        """Abre el visor; al cerrarlo, refresca galería y favoritos si cambió algo."""
        visor = VisorImagen(items, indice, self)
        visor.exec()
        if visor.cambios:
            barras = {l: l.verticalScrollBar().value() for l in self.listas}
            self.actualizar_galeria()
            if self.pila.currentIndex() == 2:
                self.cargar_favoritos()
            self.actualizar_contador_favoritos()
            for l, valor in barras.items():
                QTimer.singleShot(0, lambda l=l, valor=valor:
                                  l.verticalScrollBar().setValue(valor))

    # -----------------------------------------------------
    # ENCUADRE DE LA FOTO DE LA HEROINA (arrastrar / ampliar)
    # -----------------------------------------------------

    def encuadre_heroina_cambiado(self, enc):
        if self._pers_id is None:
            return
        self._enc_pend = (self._pers_id, enc)
        self._t_enc.start(450)

    def _guardar_encuadre_heroina(self):
        if not self._enc_pend:
            return
        hid, enc = self._enc_pend
        self._enc_pend = None
        self.conn.execute("UPDATE heroinas SET foto_enc = ? WHERE id = ?", (fmt_enc(enc), hid))
        self.conn.commit()
        for lista in self.listas_pers:
            for i in range(lista.count()):
                it = lista.item(i)
                d = it.data(Qt.ItemDataRole.UserRole)
                if d["id"] == hid:
                    d["enc"] = tuple(enc)
                    it.setData(Qt.ItemDataRole.UserRole, d)
                    it.setIcon(QIcon(avatar(d["foto"], 52, d["enc"])))
                    break

    def construir_musica(self):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setSpacing(16)

        # ---- columna izquierda: portada + resumen + acciones principales
        izq = QFrame()
        izq.setObjectName("panel")
        izq.setFixedWidth(330)
        il = QVBoxLayout(izq)
        il.setContentsMargins(12, 12, 12, 12)
        self.cover_musica = CoverWidget("", 260)
        il.addWidget(self.cover_musica, 1)
        self.lbl_mus_resumen = QLabel("")
        self.lbl_mus_resumen.setObjectName("heading")
        self.lbl_mus_resumen.setWordWrap(True)
        il.addWidget(self.lbl_mus_resumen)
        self.lbl_mus_total = QLabel("")
        self.lbl_mus_total.setObjectName("muted")
        self.lbl_mus_total.setWordWrap(True)
        il.addWidget(self.lbl_mus_total)
        b_play = BotonAnimado("▶ Reproducir todo", primario=True)
        b_play.clicked.connect(lambda: self.reproducir_todo(0))
        b_add = BotonAnimado("＋ Añadir MP3")
        b_add.clicked.connect(self.anadir_musica)
        b_rand = BotonAnimado("🎲 Aleatorio global")
        b_rand.clicked.connect(self.reproducir_aleatorio_global)
        for b in (b_play, b_add, b_rand):
            il.addWidget(b)
        h.addWidget(izq)

        # ---- columna derecha: lista de pistas con detalles
        col = QVBoxLayout()
        fila = QHBoxLayout()
        t = QLabel("♪ Banda sonora")
        t.setObjectName("heading")
        fila.addWidget(t, 1)
        self.buscar_pista = QLineEdit()
        self.buscar_pista.setPlaceholderText("⌕  Buscar pista...")
        self.buscar_pista.setMinimumWidth(220)
        self._t_busq_pista = QTimer(self)
        self._t_busq_pista.setSingleShot(True)
        self._t_busq_pista.setInterval(220)
        self._t_busq_pista.timeout.connect(self.cargar_musica)
        self.buscar_pista.textChanged.connect(lambda *_: self._t_busq_pista.start())
        fila.addWidget(self.buscar_pista)
        col.addLayout(fila)

        cab = CabeceraPistas()
        self.lista_musica = QListWidget()
        self.lista_musica.setObjectName("galeria")
        self.lista_musica.setItemDelegate(DelegadoPista(self.lista_musica))
        self.lista_musica.setMouseTracking(True)
        self.lista_musica.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.lista_musica.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.lista_musica.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lista_musica.ruta_sonando = ""
        self.lista_musica.ruta_sonando_n = ""
        self.lista_musica.sonando = False
        self.lista_musica.itemDoubleClicked.connect(self.reproducir_desde_lista)
        self.lista_musica.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lista_musica.customContextMenuRequested.connect(self.menu_musica)
        self.lista_musica.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.lista_musica.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.lista_musica.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.lista_musica.model().rowsMoved.connect(
            lambda *a: QTimer.singleShot(0, self.guardar_orden_musica))
        self.lista_musica.itemSelectionChanged.connect(self.actualizar_detalle_pista)
        cab.setContentsMargins(0, 0, 0, 0)
        # la cabecera deja el hueco de la barra de desplazamiento para alinear columnas
        cab_fila = QHBoxLayout()
        cab_fila.setContentsMargins(0, 0, self.lista_musica.verticalScrollBar().sizeHint().width() + 4, 0)
        cab_fila.addWidget(cab)
        col.addLayout(cab_fila)
        col.addWidget(self.lista_musica, 1)

        self.detalle_pista = QLabel("")
        self.detalle_pista.setObjectName("panel")
        self.detalle_pista.setWordWrap(True)
        self.detalle_pista.setTextFormat(Qt.TextFormat.RichText)
        self.detalle_pista.setMargin(12)
        self.detalle_pista.setMinimumHeight(96)
        self.detalle_pista.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        col.addWidget(self.detalle_pista)

        fila = QHBoxLayout()
        b_ren = BotonAnimado("✎ Renombrar")
        b_ren.clicked.connect(self.renombrar_musica)
        b_ubi = BotonAnimado("📂 Ubicación")
        b_ubi.clicked.connect(self.abrir_ubicacion_pista)
        b_del = BotonAnimado("🗑 Eliminar")
        b_del.clicked.connect(self.eliminar_musica)
        for b in (b_ren, b_ubi, b_del):
            fila.addWidget(b)
        fila.addStretch()
        col.addLayout(fila)
        h.addLayout(col, 1)

        self._t_eq_lista = QTimer(self)
        self._t_eq_lista.setInterval(120)
        self._t_eq_lista.timeout.connect(self._repintar_pista_sonando)
        self.actualizar_detalle_pista()
        return w

    def _repintar_pista_sonando(self):
        lista = self.lista_musica
        actual = getattr(lista, "ruta_sonando_n", "")
        if not actual:
            return
        vp = lista.viewport()
        for i in range(lista.count()):
            it = lista.item(i)
            d = it.data(Qt.ItemDataRole.UserRole + 1)
            if d and d.get("rn") == actual:
                vp.update(lista.visualItemRect(it))
                return

    def cargar_musica(self, *args):
        if not hasattr(self, "lista_musica"):
            return
        filtro = self.buscar_pista.text().casefold().strip()
        self.lista_musica.clear()
        self._info_pistas = {}
        filas = self.conn.execute(
            "SELECT id, titulo, ruta, duracion FROM musica WHERE juego_id = ? ORDER BY orden, id",
            (self.juego_id,)).fetchall()
        for i, (mid, titulo, ruta, dur) in enumerate(filas):
            p = Path(ruta)
            try:
                st = p.stat()
                peso, fecha, existe = st.st_size, st.st_mtime, True
            except OSError:
                peso, fecha, existe = 0, 0.0, False
            if dur <= 0 and existe:
                dur = duracion_rapida(ruta)
                if dur > 0:
                    self.conn.execute("UPDATE musica SET duracion = ? WHERE id = ?", (dur, mid))
                else:
                    self.sonda.pedir(mid, ruta)
            info = dict(id=mid, n=i + 1, titulo=titulo, ruta=ruta, dur=dur, peso=peso,
                        fecha=fecha, existe=existe, fmt=p.suffix.lstrip(".").upper(),
                        rn=os.path.normcase(os.path.normpath(ruta)))
            self._info_pistas[mid] = info
            if filtro and filtro not in titulo.casefold():
                continue
            it = QListWidgetItem()
            it.setData(Qt.ItemDataRole.UserRole, mid)
            it.setData(Qt.ItemDataRole.UserRole + 1, info)
            it.setSizeHint(QSize(100, 54))
            self.lista_musica.addItem(it)
        self.conn.commit()
        self.actualizar_resumen_musica()
        self.actualizar_detalle_pista()

    def guardar_orden_musica(self):
        if self.buscar_pista.text().strip():
            self.toast("Borra la búsqueda para ordenar las pistas")
            self.cargar_musica()
            return
        for pos in range(self.lista_musica.count()):
            mid = self.lista_musica.item(pos).data(Qt.ItemDataRole.UserRole)
            self.conn.execute("UPDATE musica SET orden = ? WHERE id = ?", (pos + 1, mid))
        self.conn.commit()
        self.cargar_musica()

    def actualizar_resumen_musica(self):
        infos = list(getattr(self, "_info_pistas", {}).values())
        n = len(infos)
        dur = sum(i["dur"] for i in infos)
        peso = sum(i["peso"] for i in infos)
        self.lbl_mus_resumen.setText(f"{n} pista{'s' if n != 1 else ''}" if n else "Sin pistas aún")
        self.lbl_mus_total.setText(
            f"⏱ {fmt_dur(dur) if dur else '—'} en total   ·   💾 {fmt_peso(peso)}" if n
            else "Añade MP3 con «＋ Añadir MP3».")

    def al_duracion_pista(self, mid, ms):
        self.conn.execute("UPDATE musica SET duracion = ? WHERE id = ?", (ms, mid))
        self.conn.commit()
        info = getattr(self, "_info_pistas", {}).get(mid)
        if info is None:
            return
        info["dur"] = ms
        for i in range(self.lista_musica.count()):
            it = self.lista_musica.item(i)
            if it.data(Qt.ItemDataRole.UserRole) == mid:
                it.setData(Qt.ItemDataRole.UserRole + 1, info)
        self.actualizar_resumen_musica()
        self.lista_musica.viewport().update()
        self.actualizar_detalle_pista()

    def actualizar_detalle_pista(self):
        if not hasattr(self, "detalle_pista"):
            return
        infos = [it.data(Qt.ItemDataRole.UserRole + 1) for it in self.lista_musica.selectedItems()]
        if not infos:
            self.detalle_pista.setText("")
            return
        if len(infos) > 1:
            dur = sum(i["dur"] for i in infos)
            peso = sum(i["peso"] for i in infos)
            self.detalle_pista.setText(
                f"<b>{len(infos)} pistas seleccionadas</b><br>"
                f"Duración total: {fmt_dur(dur) if dur else '—'} &nbsp;·&nbsp; "
                f"Peso total: {fmt_peso(peso)}")
            return
        i = infos[0]
        kb = (f"{int(i['peso'] * 8 / (i['dur'] / 1000) / 1000)} kbps (medio)"
              if i["dur"] > 0 and i["peso"] > 0 else "—")
        fecha = time.strftime("%d/%m/%Y %H:%M", time.localtime(i["fecha"])) if i["fecha"] else "—"
        esc = html.escape
        self.detalle_pista.setText(
            f"<b style='font-size:{Tema.tam + 3}pt'>{esc(i['titulo'])}</b><br>"
            f"<b>Formato:</b> {esc(i['fmt'] or '—')} &nbsp;·&nbsp; "
            f"<b>Duración:</b> {fmt_dur(i['dur'])} &nbsp;·&nbsp; "
            f"<b>Peso:</b> {fmt_peso(i['peso'])} &nbsp;·&nbsp; <b>Bitrate:</b> {kb}<br>"
            f"<b>Archivo:</b> {esc(Path(i['ruta']).name)} &nbsp;·&nbsp; "
            f"<b>Fecha del archivo:</b> {fecha}<br>"
            f"<b>Carpeta:</b> {esc(str(Path(i['ruta']).parent))}")

    def abrir_ubicacion_pista(self):
        infos = [it.data(Qt.ItemDataRole.UserRole + 1) for it in self.lista_musica.selectedItems()]
        if not infos:
            self.toast("Selecciona una pista")
            return
        ruta = Path(infos[0]["ruta"])
        if ruta.exists():
            os.startfile(str(ruta.parent))
        else:
            self.toast("El archivo ya no existe en el disco")

    def construir_barra_player(self):
        f = QFrame()
        f.setObjectName("reproductor")
        h = QHBoxLayout(f)
        h.setContentsMargins(16, 4, 16, 4)
        h.setSpacing(12)

        # --- izquierda: disco + título + novela
        self.disco = Disco()
        h.addWidget(self.disco)
        info = QVBoxLayout()
        info.setSpacing(2)
        info.addStretch()
        self.lbl_pista = QLabel("Sin música")
        self.lbl_pista.setObjectName("pista_titulo")
        self.lbl_sub = QLabel("Añade MP3 en la pestaña Música de una novela")
        self.lbl_sub.setObjectName("pista_sub")
        for lb in (self.lbl_pista, self.lbl_sub):
            lb.setMinimumWidth(170)
            lb.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            info.addWidget(lb)
        info.addStretch()
        h.addLayout(info, 3)

        # --- centro: controles arriba, barra de progreso debajo
        centro = QVBoxLayout()
        centro.setSpacing(0)
        ctr = QHBoxLayout()
        ctr.setSpacing(6)
        ctr.addStretch()

        def btn(icono, fn, checkable=False, lado=40, primario=False):
            b = BotonRedondo("", lado, primario=primario, icono=icono)
            b.setCheckable(checkable)
            b.clicked.connect(fn)
            ctr.addWidget(b)
            return b

        self.btn_shuffle = btn("shuffle", lambda: None, True, lado=30)
        b_ant = btn("prev", lambda: self.siguiente(-1), lado=34)
        self.btn_play = btn("play", self.alternar_play, lado=46, primario=True)
        b_sig = btn("next", lambda: self.siguiente(1), lado=34)
        self.btn_rep = btn("repeat", self.ciclar_repetir, lado=30)
        ctr.addSpacing(8)
        self.btn_rand = btn("dice", self.reproducir_aleatorio_global, lado=30)
        ctr.addStretch()
        centro.addLayout(ctr)

        prog = QHBoxLayout()
        prog.setSpacing(10)
        self.lbl_t1 = QLabel("0:00")
        self.lbl_t1.setObjectName("tiempo")
        self.lbl_t1.setFixedWidth(42)
        self.lbl_t1.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        prog.addWidget(self.lbl_t1)
        self.sl_pos = QSlider(Qt.Orientation.Horizontal)
        self.sl_pos.setMinimumWidth(200)
        self.sl_pos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sl_pos.sliderMoved.connect(self.player.setPosition)
        prog.addWidget(self.sl_pos, 1)
        self.lbl_t2 = QLabel("0:00")
        self.lbl_t2.setObjectName("tiempo")
        self.lbl_t2.setFixedWidth(42)
        prog.addWidget(self.lbl_t2)
        centro.addLayout(prog)
        h.addLayout(centro, 6)

        # --- derecha: ecualizador + volumen
        der = QVBoxLayout()
        der.setSpacing(6)
        der.addStretch()
        self.eq = Ecualizador()
        der.addWidget(self.eq, 0, Qt.AlignmentFlag.AlignRight)
        vol = QHBoxLayout()
        vol.setSpacing(6)
        self.ic_vol = IconoVolumen()
        self.ic_vol.clic.connect(self.alternar_silencio)
        vol.addWidget(self.ic_vol)
        self.sl_vol = QSlider(Qt.Orientation.Horizontal)
        self.sl_vol.setObjectName("volumen")
        self.sl_vol.setRange(0, 100)
        self.sl_vol.setValue(MUSICA_VOLUMEN)
        self.sl_vol.setFixedWidth(110)
        self.sl_vol.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sl_vol.valueChanged.connect(self.cambiar_volumen)
        vol.addWidget(self.sl_vol)
        der.addLayout(vol)
        der.addStretch()
        h.addLayout(der, 0)
        return f

    # -----------------------------------------------------
    # REPRODUCTOR
    # -----------------------------------------------------

    def crear_motor_audio(self):
        self._ruta_musica = None
        self._normalizando = None
        self._cache_musica = ASSETS / "audio_equilibrado"
        self._cola_mp3 = {}
        self._pedido_mp3 = None
        self._trabajo_mp3 = None
        self._timer_mp3 = QTimer(self)
        self._timer_mp3.setSingleShot(True)
        self._timer_mp3.timeout.connect(self._siguiente_mp3)
        self._ffmpeg = recurso("ffmpeg.exe")
        if not self._ffmpeg.is_file():
            try:
                from imageio_ffmpeg import get_ffmpeg_exe
                self._ffmpeg = get_ffmpeg_exe()
            except (ImportError, RuntimeError):
                self._ffmpeg = shutil.which("ffmpeg")
        self.audio = QAudioOutput()
        self.audio.setVolume(MUSICA_VOLUMEN / 100)
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio)
        self.player.positionChanged.connect(self.al_posicion)
        self.player.durationChanged.connect(self.al_duracion)
        self.player.playbackStateChanged.connect(self.al_estado)
        self.player.mediaStatusChanged.connect(self.al_status)
        self.player.errorOccurred.connect(
            lambda *a: self.lbl_pista.setText("No se pudo reproducir esta pista"))

    def cambiar_volumen(self, v):
        self.audio.setVolume(v / 100)
        self.ic_vol.poner(v)

    def alternar_silencio(self):
        if self.sl_vol.value() > 0:
            self._vol_previo = self.sl_vol.value()
            self.sl_vol.setValue(0)
        else:
            self.sl_vol.setValue(getattr(self, "_vol_previo", MUSICA_VOLUMEN) or MUSICA_VOLUMEN)

    @staticmethod
    def formato_tiempo(ms):
        s = max(0, ms // 1000)
        return f"{s // 60}:{s % 60:02d}"

    def al_posicion(self, pos):
        if not self.sl_pos.isSliderDown():
            self.sl_pos.setValue(pos)
        self.lbl_t1.setText(self.formato_tiempo(pos))

    def al_duracion(self, dur):
        self.sl_pos.setRange(0, dur)
        self.lbl_t2.setText(self.formato_tiempo(dur))

    def al_estado(self, estado):
        sonando = estado == QMediaPlayer.PlaybackState.PlayingState
        self.btn_play.set_icono("pause" if sonando else "play")
        self.eq.activar(sonando)
        self.disco.activar(sonando)
        if sonando and self.voces_player is not None:
            self.voces_player.pause()
        if sonando and OPENING_PAUSA_MUSICA:
            for rp in (getattr(self, "opening", None), getattr(self, "opening_global", None),
                       self.clips_reproductor):
                if rp is not None:
                    rp.pausar()
        if hasattr(self, "lista_musica"):
            self.lista_musica.sonando = sonando
            if sonando:
                self._t_eq_lista.start()
            else:
                self._t_eq_lista.stop()
            self.lista_musica.viewport().update()

    def al_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            QTimer.singleShot(0, self._fin_de_pista)      # fuera de la señal de Qt

    def _fin_de_pista(self):
        try:
            if self.player.mediaStatus() != QMediaPlayer.MediaStatus.EndOfMedia:
                return
            if self.repetir == 2:
                self.player.setPosition(0)
                self.player.play()
            else:
                self.siguiente(1, auto=True)
        except RuntimeError:
            pass

    def reproducir_cola(self, pistas, indice):
        self.cola = list(pistas)
        self.cola_idx = indice
        self.reproducir_actual()

    def reproducir_actual(self):
        if not (0 <= self.cola_idx < len(self.cola)):
            return
        titulo, ruta, juego, portada = self.cola[self.cola_idx]
        if not Path(ruta).exists():
            self.lbl_pista.setText(f"Archivo no encontrado: {titulo}")
            return
        self._detener_musica()
        self._ruta_musica = ruta
        self.lbl_pista.setText(titulo)
        self.lbl_sub.setText(f"{juego}   ·   {self.cola_idx + 1} / {len(self.cola)}")
        self.disco.poner(portada)
        if hasattr(self, "lista_musica"):
            self.lista_musica.ruta_sonando = ruta
            self.lista_musica.ruta_sonando_n = os.path.normcase(os.path.normpath(ruta))
            self.lista_musica.viewport().update()
        self._preparar_mp3(Path(ruta), titulo)

    def _archivo_equilibrado(self, ruta):
        if ruta.suffix.lower() != ".mp3" or not self._ffmpeg:
            return None
        try:
            estado = ruta.stat()
        except OSError:
            return None
        ruta_id = hashlib.sha256(os.fsencode(os.path.normcase(str(ruta.absolute())))).hexdigest()
        return self._cache_musica / f"{ruta_id}-{estado.st_size}-{estado.st_mtime_ns}.m4a"

    def _encolar_biblioteca_mp3(self):
        for (ruta,) in self.conn.execute(
                "SELECT DISTINCT ruta FROM musica WHERE lower(ruta) LIKE '%.mp3'"):
            self._cola_mp3[Path(ruta)] = None
        self._timer_mp3.start(100)

    def _siguiente_mp3(self):
        if self._normalizando is not None or not self._cola_mp3:
            return
        ruta = next(iter(self._cola_mp3))
        del self._cola_mp3[ruta]
        salida = self._archivo_equilibrado(ruta)
        if salida is None or salida.is_file():
            self._timer_mp3.start(0)
        else:
            self._normalizar_mp3(ruta, salida)

    def _preparar_mp3(self, ruta, titulo):
        salida = self._archivo_equilibrado(ruta)
        if salida is None or salida.is_file():
            self._abrir_musica(salida or ruta)
            return
        self._pedido_mp3 = (ruta, titulo)
        self.lbl_pista.setText(f"Preparando por primera vez: {titulo}")
        if self._trabajo_mp3 and self._trabajo_mp3[0] == ruta:
            return
        if self._trabajo_mp3:
            self._cola_mp3[self._trabajo_mp3[0]] = None
            self._cancelar_normalizacion()
        self._cola_mp3.pop(ruta, None)
        self._normalizar_mp3(ruta, salida)

    def _normalizar_mp3(self, ruta, salida):
        try:
            self._cache_musica.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self._cache_musica, suffix=".part",
                                             delete=False) as archivo:
                temporal = Path(archivo.name)
        except OSError:
            self._terminar_pedido_mp3(ruta, ruta)
            self._timer_mp3.start(0)
            return
        proceso = QProcess(self)
        self._normalizando = proceso
        self._trabajo_mp3 = (ruta, temporal)
        proceso.setStandardOutputFile(QProcess.nullDevice())
        proceso.setStandardErrorFile(QProcess.nullDevice())

        def terminar(exito):
            if self._normalizando is not proceso:
                return
            self._normalizando = None
            self._trabajo_mp3 = None
            proceso.deleteLater()
            resultado = ruta
            try:
                if exito and temporal.stat().st_size > 0 and self._archivo_equilibrado(ruta) == salida:
                    temporal.replace(salida)
                    resultado = salida
                    for anterior in salida.parent.glob(salida.name.split("-", 1)[0] + "-*.m4a"):
                        if anterior != salida:
                            anterior.unlink(missing_ok=True)
            except OSError:
                pass
            finally:
                self._borrar_archivo_temporal(temporal)
            self._terminar_pedido_mp3(ruta, resultado)
            self._timer_mp3.start(50)

        proceso.finished.connect(
            lambda codigo, estado: terminar(codigo == 0 and estado == QProcess.ExitStatus.NormalExit)
        )
        proceso.errorOccurred.connect(
            lambda error: terminar(False) if error == QProcess.ProcessError.FailedToStart else None
        )
        proceso.start(str(self._ffmpeg), [
            "-nostdin", "-v", "error", "-y", "-i", str(ruta.absolute()),
            "-map", "0:a:0", "-map_metadata", "-1", "-filter_threads", "1",
            "-af", "loudnorm=I=-16:TP=-2:LRA=11", "-ar", "48000",
            "-c:a", "aac", "-b:a", "192k", "-threads", "1", "-f", "ipod", str(temporal),
        ])

    def _terminar_pedido_mp3(self, ruta, resultado):
        if self._pedido_mp3 and self._pedido_mp3[0] == ruta:
            _ruta, titulo = self._pedido_mp3
            self._pedido_mp3 = None
            self.lbl_pista.setText(titulo)
            self._abrir_musica(resultado)

    @staticmethod
    def _borrar_archivo_temporal(temporal):
        try:
            temporal.unlink(missing_ok=True)
        except OSError:
            pass

    def _cancelar_normalizacion(self):
        proceso = self._normalizando
        if proceso is not None:
            _ruta, temporal = self._trabajo_mp3
            self._normalizando = self._trabajo_mp3 = None
            proceso.kill()
            proceso.waitForFinished(200)
            proceso.deleteLater()
            self._borrar_archivo_temporal(temporal)

    def _abrir_musica(self, ruta):
        self.player.setSource(QUrl.fromLocalFile(str(ruta)))
        self.player.play()

    def _detener_musica(self):
        self._pedido_mp3 = None
        self.player.stop()
        self.player.setSource(QUrl())
        self._ruta_musica = None

    def _cerrar_audio(self):
        self._timer_mp3.stop()
        self._detener_musica()
        self._cancelar_normalizacion()

    def alternar_play(self):
        if self._pedido_mp3 is not None:
            self._detener_musica()
            if 0 <= self.cola_idx < len(self.cola):
                self.lbl_pista.setText(self.cola[self.cola_idx][0])
        elif self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.player.source().isEmpty():
            if self.cola:
                self.cola_idx = max(0, self.cola_idx)
                self.reproducir_actual()
        else:
            self.player.play()

    def siguiente(self, direccion, auto=False):
        if not self.cola:
            return
        if self.btn_shuffle.isChecked() and len(self.cola) > 1:
            nuevo = random.choice([i for i in range(len(self.cola)) if i != self.cola_idx])
        else:
            nuevo = self.cola_idx + direccion
            if nuevo >= len(self.cola):
                if self.repetir == 1:
                    nuevo = 0
                elif auto:
                    self.player.stop()
                    return
                else:
                    nuevo = len(self.cola) - 1
            elif nuevo < 0:
                nuevo = 0
        self.cola_idx = nuevo
        self.reproducir_actual()

    def ciclar_repetir(self):
        self.repetir = (self.repetir + 1) % 3
        self.aplicar_repetir()

    def aplicar_repetir(self):
        self.btn_rep.set_icono("repeat", "1" if self.repetir == 2 else "")
        self.btn_rep.setChecked(self.repetir != 0)

    # -----------------------------------------------------
    # MUSICA POR NOVELA
    # -----------------------------------------------------

    def pistas(self, juego_id=None):
        sql = ("SELECT m.titulo, m.ruta, j.nombre, j.portada FROM musica m "
               "JOIN juegos j ON j.id = m.juego_id")
        params = ()
        if juego_id is not None:
            sql += " WHERE m.juego_id = ?"
            params = (juego_id,)
        sql += " ORDER BY m.orden, m.id"
        return [tuple(r) for r in self.conn.execute(sql, params)]

    def anadir_musica(self):
        if self.juego_id is None:
            return
        archivos, _ = QFileDialog.getOpenFileNames(
            self, "Añadir música", str(Path.home()), f"Audio ({EXT_AUDIO})")
        if not archivos:
            return
        carpeta = ROOT / self.juego_carpeta / "Música"
        carpeta.mkdir(parents=True, exist_ok=True)
        for a in archivos:
            destino = nombre_disponible(carpeta, Path(a).name)
            shutil.copy2(a, destino)
            self.conn.execute(
                "INSERT INTO musica(juego_id, titulo, ruta) VALUES (?, ?, ?)",
                (self.juego_id, Path(a).stem, str(destino)))
        self.conn.commit()
        self.cargar_musica()
        self._encolar_biblioteca_mp3()
        self.toast(f"♪ {len(archivos)} pista(s) añadidas")

    def renombrar_musica(self):
        items = self.lista_musica.selectedItems()
        if len(items) != 1:
            self.toast("Selecciona una sola pista para renombrar")
            return
        mid = items[0].data(Qt.ItemDataRole.UserRole)
        titulo, ruta = self.conn.execute(
            "SELECT titulo, ruta FROM musica WHERE id = ?", (mid,)).fetchone()
        nuevo, ok = QInputDialog.getText(self, "Renombrar pista", "Nuevo nombre:", text=titulo)
        nuevo = nombre_seguro(nuevo.strip()) if ok else ""
        if not nuevo or nuevo == titulo:
            return

        ruta_p = Path(ruta)
        destino = ruta_p.with_name(nuevo + ruta_p.suffix)
        nueva_ruta, aviso = ruta, ""
        try:
            if destino.exists():
                raise FileExistsError
            if self._ruta_musica and Path(self._ruta_musica) == ruta_p:
                self._detener_musica()
            if self._trabajo_mp3 and self._trabajo_mp3[0] == ruta_p:
                self._cancelar_normalizacion()
                self._timer_mp3.start(50)
            ruta_p.rename(destino)
            nueva_ruta = str(destino)
        except Exception:
            aviso = " (el archivo no pudo renombrarse en el disco)"
        self.conn.execute("UPDATE musica SET titulo = ?, ruta = ? WHERE id = ?",
                          (nuevo, nueva_ruta, mid))
        self.conn.commit()
        self.cola = [(nuevo, nueva_ruta, j, p) if r == ruta else (t, r, j, p)
                     for (t, r, j, p) in self.cola]
        self.cargar_musica()
        self.toast(f"✎ Renombrada a «{nuevo}»{aviso}")

    def eliminar_musica(self):
        items = self.lista_musica.selectedItems()
        if not items:
            self.toast("Selecciona las pistas que quieras eliminar")
            return
        if QMessageBox.question(
                self, "Eliminar permanentemente",
                f"¿Eliminar PERMANENTEMENTE {len(items)} pista(s)?\n\n"
                "Los archivos de audio se borrarán del disco y no se podrán recuperar.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        filas = []
        for it in items:
            mid = it.data(Qt.ItemDataRole.UserRole)
            fila = self.conn.execute("SELECT ruta FROM musica WHERE id = ?", (mid,)).fetchone()
            if fila:
                filas.append((mid, fila[0]))
        actual = self._ruta_musica
        if actual and any(Path(r) == Path(actual) for _m, r in filas):
            self._detener_musica()
            self.lbl_pista.setText("Sin música")
            self.lbl_sub.setText("")
        borradas, fallos = [], 0
        for mid, ruta in filas:
            try:
                if self._trabajo_mp3 and self._trabajo_mp3[0] == Path(ruta):
                    self._cancelar_normalizacion()
                    self._timer_mp3.start(50)
                Path(ruta).unlink(missing_ok=True)
                self.conn.execute("DELETE FROM musica WHERE id = ?", (mid,))
                borradas.append(ruta)
            except OSError:
                fallos += 1
        self.conn.commit()
        if borradas:
            self.cola = [t for t in self.cola if t[1] not in borradas]
            self.cola_idx = -1
        self.cargar_musica()
        self.toast(f"🗑 {len(borradas)} pista(s) eliminadas"
                   + (f" · {fallos} con error" if fallos else ""))

    # -----------------------------------------------------
    # OPENINGS (video de la novela)
    # -----------------------------------------------------

    def cargar_openings(self, autoplay=False, forzar=False):
        if self.juego_id is None:
            return
        filas = self.conn.execute("""
            SELECT v.id, v.titulo, v.ruta, v.me_gusta, j.nombre, j.portada, j.portada_enc
            FROM videos v JOIN juegos j ON j.id = v.juego_id
            WHERE j.id = ? ORDER BY v.orden, v.id
        """, (self.juego_id,)).fetchall()
        lista = self.lista_openings
        elegido = lista.currentItem()
        elegido = elegido.data(Qt.ItemDataRole.UserRole) if elegido else None
        lista.setUpdatesEnabled(False)
        lista.clear()
        for vid, titulo, ruta, favorito, novela, portada, enc in filas:
            item = QListWidgetItem(titulo)
            item.setData(Qt.ItemDataRole.UserRole, vid)
            item.setData(Qt.ItemDataRole.UserRole + 1,
                         dict(titulo=titulo, ruta=ruta, favorito=bool(favorito),
                              novela=novela, portada=portada, enc=parse_enc(enc)))
            item.setToolTip(titulo)
            lista.addItem(item)
            if elegido == vid:
                lista.setCurrentItem(item)
        lista.setUpdatesEnabled(True)
        if lista.currentRow() < 0 and lista.count():
            lista.setCurrentRow(0)
        self.lbl_op_resumen.setText(
            "Openings de la novela" if filas else "Adjunta un video para empezar")
        self.opening.cargar([fila[2] for fila in filas], autoplay, forzar,
                            [fila[1] for fila in filas])

    def _guardar_volumen_opening(self, v):
        self._pendientes["opening_volumen"] = v
        self._timer_guardar.start(500)

    def _opening_empezo(self, rp=None):
        if self.voces_player is not None:
            self.voces_player.pause()
        if OPENING_PAUSA_MUSICA:
            if self._pedido_mp3 is not None:
                self.alternar_play()
            elif self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.pause()
        for otro in (getattr(self, "opening", None), getattr(self, "opening_global", None),
                     self.clips_reproductor):
            if otro is not None and otro is not rp:
                otro.pausar()

    def _copiar_con_progreso(self, origen, destino, titulo="Añadiendo opening"):
        total = max(1, Path(origen).stat().st_size)
        dlg = QProgressDialog(f"Copiando «{Path(origen).name}»…", "Cancelar", 0, 100, self)
        dlg.setWindowTitle(titulo)
        dlg.setWindowModality(Qt.WindowModality.WindowModal)
        dlg.setMinimumDuration(400)
        dlg.setValue(0)
        hecho = 0
        try:
            with open(origen, "rb") as fi, open(destino, "wb") as fo:
                while True:
                    bloque = fi.read(4 * 1024 * 1024)
                    if not bloque:
                        break
                    fo.write(bloque)
                    hecho += len(bloque)
                    dlg.setValue(min(99, int(hecho * 100 / total)))
                    QApplication.processEvents()
                    if dlg.wasCanceled():
                        raise InterruptedError
        except (OSError, InterruptedError):
            Path(destino).unlink(missing_ok=True)
            return False
        finally:
            dlg.close()
        return True

    def anadir_opening(self):
        if self.juego_id is None:
            return
        archivos, _ = QFileDialog.getOpenFileNames(
            self, "Añadir opening", str(Path.home()), f"Video ({EXT_VIDEO})")
        if not archivos:
            return
        carpeta = ROOT / self.juego_carpeta / "Openings"
        carpeta.mkdir(parents=True, exist_ok=True)
        orden = self.conn.execute("SELECT COALESCE(MAX(orden), 0) FROM videos WHERE juego_id = ?",
                                  (self.juego_id,)).fetchone()[0]
        puestos = 0
        for a in archivos:
            destino = nombre_disponible(carpeta, Path(a).name)
            if not self._copiar_con_progreso(a, destino):
                break
            orden += 1
            self.conn.execute(
                "INSERT INTO videos(juego_id, titulo, ruta, orden) VALUES (?, ?, ?, ?)",
                (self.juego_id, Path(a).stem, str(destino), orden))
            puestos += 1
        self.conn.commit()
        self.cargar_openings()
        if puestos:
            self.toast(f"🎬 {puestos} opening(s) añadidos")

    def reproducir_opening(self, item):
        self.tabs_juego.setCurrentIndex(self.IDX_OPENINGS)
        ruta = item.data(Qt.ItemDataRole.UserRole + 1)["ruta"]
        if ruta in self.opening._rutas:
            self.opening.reproducir_ruta(ruta)
        else:
            self.toast("El archivo de video ya no está en el disco.")

    def menu_openings(self, punto):
        it = self.lista_openings.itemAt(punto)
        if it is None:
            return
        vid = it.data(Qt.ItemDataRole.UserRole)
        m = QMenu(self)
        a_ver = m.addAction("▶ Ver este opening")
        a_ren = m.addAction("✎ Renombrar")
        a_ubi = m.addAction("📂 Abrir ubicación del archivo")
        m.addSeparator()
        a_del = m.addAction("🗑 Eliminar permanentemente")
        eleg = m.exec(self.lista_openings.viewport().mapToGlobal(punto))
        if eleg == a_ver:
            self.reproducir_opening(it)
        elif eleg == a_ren:
            self.renombrar_opening(vid)
        elif eleg == a_ubi:
            self.ubicacion_opening(vid)
        elif eleg == a_del:
            self.eliminar_opening(vid)
    def eliminar_opening(self, vid):
        fila = self.conn.execute("SELECT titulo, ruta FROM videos WHERE id = ?", (vid,)).fetchone()
        if not fila:
            return
        if QMessageBox.question(
                self, "Eliminar opening",
                f"¿Eliminar PERMANENTEMENTE «{fila[0]}»?\n\n"
                "El archivo de video se borrará del disco y no se podrá recuperar.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self._soltar_openings()
        try:
            Path(fila[1]).unlink(missing_ok=True)
        except OSError:
            self.toast("No se pudo borrar el archivo del disco (¿está abierto en otro programa?)")
        self.conn.execute("DELETE FROM videos WHERE id = ?", (vid,))
        self.conn.commit()
        self.refrescar_openings()

    def _soltar_openings(self, procesar=True):
        """Suelta los archivos de video de las dos pantallas (conservan su lista)."""
        for rp in (getattr(self, "opening", None), getattr(self, "opening_global", None),
                       self.clips_reproductor):
            if rp is not None:
                rp.soltar()
        if procesar:
            QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

    def refrescar_openings(self):
        if self.juego_id is not None and hasattr(self, "lista_openings"):
            self.cargar_openings()
        if self.pila.currentIndex() == self.PAG_OPENINGS:
            self.cargar_openings_global()

    def renombrar_opening(self, vid):
        fila = self.conn.execute("SELECT titulo, ruta FROM videos WHERE id = ?", (vid,)).fetchone()
        if not fila:
            return
        titulo, ruta = fila
        nuevo, ok = QInputDialog.getText(self, "Renombrar opening", "Nuevo nombre:", text=titulo)
        nuevo = nombre_seguro(nuevo.strip()) if ok else ""
        if not nuevo or nuevo == titulo:
            return
        self._soltar_openings()
        ruta_p = Path(ruta)
        destino = ruta_p.with_name(nuevo + ruta_p.suffix)
        nueva_ruta, aviso = ruta, ""
        try:
            if destino.exists():
                raise FileExistsError
            ruta_p.rename(destino)
            nueva_ruta = str(destino)
        except Exception:
            aviso = " (el archivo no pudo renombrarse en el disco)"
        self.conn.execute("UPDATE videos SET titulo = ?, ruta = ? WHERE id = ?",
                          (nuevo, nueva_ruta, vid))
        self.conn.commit()
        self.refrescar_openings()
        self.toast(f"✎ Opening renombrado a «{nuevo}»{aviso}")

    def ubicacion_opening(self, vid):
        fila = self.conn.execute("SELECT ruta FROM videos WHERE id = ?", (vid,)).fetchone()
        if fila and Path(fila[0]).exists():
            os.startfile(str(Path(fila[0]).parent))
        else:
            self.toast("El archivo ya no existe en el disco")

    # -----------------------------------------------------
    # PESTAÑA «OPENINGS» DE LA NOVELA
    # -----------------------------------------------------

    def _nuevo_reproductor_opening(self):
        try:
            f = self.conn.execute(
                "SELECT valor FROM ajustes WHERE clave = 'opening_volumen'").fetchone()
            vol = int(f[0]) if f else OPENING_VOLUMEN
        except (sqlite3.Error, ValueError):
            vol = OPENING_VOLUMEN
        rp = ReproductorOpening(vol)
        rp.volumen_cambiado.connect(self._guardar_volumen_opening)
        rp.empezo.connect(lambda r=rp: self._opening_empezo(r))
        return rp

    def _marcar_fila(self, lista, i):
        if 0 <= i < lista.count():
            lista.blockSignals(True)
            lista.setCurrentRow(i)
            lista.blockSignals(False)

    def construir_openings_novela(self):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(8, 8, 8, 8)
        h.setSpacing(10)
        self.opening = self._nuevo_reproductor_opening()
        h.addWidget(self.opening, 1)

        catalogo = QFrame()
        catalogo.setObjectName("panel")
        catalogo.setMinimumWidth(250)
        catalogo.setMaximumWidth(345)
        layout = QVBoxLayout(catalogo)
        layout.setContentsMargins(10, 12, 10, 12)
        self.lbl_op_resumen = QLabel("Openings de la novela")
        self.lbl_op_resumen.setObjectName("heading")
        self.lbl_op_resumen.setWordWrap(True)
        layout.addWidget(self.lbl_op_resumen)

        self.lista_openings = QListWidget()
        self.lista_openings.setItemDelegate(DelegadoCatalogoOpening(self.lista_openings))
        self.lista_openings.setUniformItemSizes(True)
        self.lista_openings.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.lista_openings.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lista_openings.customContextMenuRequested.connect(self.menu_openings)
        self.lista_openings.itemActivated.connect(self.reproducir_opening)
        self.lista_openings.setToolTip("Doble clic o Enter para ver. Esc para salir del video.")
        self.opening.indice_cambiado.connect(lambda _: self._seleccionar_opening_en_video())
        self.opening.reposo.clic.disconnect(self.opening.alternar_play)
        self.opening.reposo.clic.connect(
            lambda: self._accion_opening_novela(self.reproducir_opening))
        layout.addWidget(self.lista_openings, 1)
        acciones = QHBoxLayout()
        ver = BotonAnimado("▶ Ver", primario=True)
        ver.clicked.connect(lambda: self._accion_opening_novela(self.reproducir_opening))
        corazon = BotonAnimado("♡ Favorito")
        corazon.clicked.connect(lambda: self._accion_opening_novela(self._favorito_opening_novela))
        acciones.addWidget(ver)
        acciones.addWidget(corazon)
        layout.addLayout(acciones)
        adjuntar = BotonAnimado("＋ Adjuntar video")
        adjuntar.clicked.connect(self.anadir_opening)
        layout.addWidget(adjuntar)
        layout.addWidget(self._boton_cerrar_video(self.opening))
        h.addWidget(catalogo)
        return w

    def _boton_cerrar_video(self, reproductor):
        cerrar = BotonAnimado("Cerrar video")
        cerrar.setToolTip("Cerrar el video y regresar al catálogo (Esc)")
        cerrar.clicked.connect(self._salir_del_opening)
        cerrar.hide()
        reproductor.player.sourceChanged.connect(
            lambda url: cerrar.setVisible(not url.isEmpty()))
        return cerrar

    def _accion_opening_novela(self, accion):
        item = self.lista_openings.currentItem()
        if item is not None:
            accion(item)

    def _favorito_opening_novela(self, item):
        self._marcar_opening_favorito(item.data(Qt.ItemDataRole.UserRole))
        self.cargar_openings()

    def _seleccionar_opening_en_video(self):
        ruta = self._ruta_opening_actual(self.opening)
        for fila in range(self.lista_openings.count()):
            item = self.lista_openings.item(fila)
            if item.data(Qt.ItemDataRole.UserRole + 1)["ruta"] == ruta:
                self._marcar_fila(self.lista_openings, fila)
                return

    def construir_clips(self):
        vista = QWidget()
        cuerpo = QHBoxLayout(vista)
        cuerpo.setContentsMargins(8, 8, 8, 8)
        self.escenario_clips = QVBoxLayout()
        cuerpo.addLayout(self.escenario_clips, 1)

        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(235)
        panel.setMaximumWidth(360)
        lado = QVBoxLayout(panel)
        titulo = QLabel("Clips de la novela")
        titulo.setObjectName("heading")
        lado.addWidget(titulo)
        self.lista_clips = QListWidget()
        self.lista_clips.setUniformItemSizes(True)
        self.lista_clips.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.lista_clips.itemActivated.connect(self.reproducir_clip)
        lado.addWidget(self.lista_clips, 1)

        acciones = QHBoxLayout()
        ver = BotonAnimado("▶ Reproducir", primario=True)
        ver.clicked.connect(lambda: self.reproducir_clip(self.lista_clips.currentItem()))
        acciones.addWidget(ver)
        agregar = BotonAnimado("＋ Adjuntar")
        agregar.clicked.connect(self.adjuntar_clips)
        acciones.addWidget(agregar)
        lado.addLayout(acciones)
        renombrar = BotonAnimado("✎ Renombrar archivo")
        renombrar.clicked.connect(lambda: self._renombrar_adjunto("clips"))
        lado.addWidget(renombrar)
        cuerpo.addWidget(panel)
        return vista

    def cargar_clips(self, seleccion=None):
        if self.juego_id is None:
            return
        if self.clips_reproductor is None:
            self.clips_reproductor = self._nuevo_reproductor_opening()
            reproductor = self.clips_reproductor
            reproductor.reposo.clic.disconnect(reproductor.alternar_play)
            reproductor.reposo.clic.connect(
                lambda: self.reproducir_clip(self.lista_clips.currentItem()))
            self.escenario_clips.addWidget(reproductor, 1)
            self.escenario_clips.addWidget(self._boton_cerrar_video(reproductor))
        registros = self.conn.execute(
            "SELECT id, titulo, ruta FROM clips WHERE juego_id=? ORDER BY id", (self.juego_id,)
        ).fetchall()
        self.lista_clips.clear()
        for id_clip, titulo, ruta in registros:
            item = QListWidgetItem(titulo)
            item.setData(Qt.ItemDataRole.UserRole, ruta)
            item.setData(Qt.ItemDataRole.UserRole + 1, id_clip)
            item.setToolTip(Path(ruta).name)
            item.setSizeHint(QSize(0, 38))
            self.lista_clips.addItem(item)
        if registros:
            fila = next((i for i, r in enumerate(registros) if r[0] == seleccion), 0)
            self.lista_clips.setCurrentRow(fila)
        self.clips_reproductor.cargar([r[2] for r in registros], titulos=[r[1] for r in registros])
        if not registros:
            self.clips_reproductor.reposo.setText("Adjunta un clip para empezar")

    def reproducir_clip(self, item):
        if item is None or self.clips_reproductor is None:
            return
        ruta = item.data(Qt.ItemDataRole.UserRole)
        if ruta in self.clips_reproductor._rutas:
            self.clips_reproductor.reproducir_ruta(ruta)
        else:
            self.toast("El archivo del clip ya no está en el disco.")

    def adjuntar_clips(self):
        if self.juego_id is None:
            return
        archivos, _ = QFileDialog.getOpenFileNames(
            self, "Adjuntar clips a la novela", str(ROOT), f"Videos ({EXT_VIDEO})")
        if not archivos:
            return
        carpeta = (ROOT / self.juego_carpeta / "Clips").resolve()
        if not carpeta.is_relative_to(ROOT.resolve()):
            self.toast("La carpeta de clips debe estar dentro de la biblioteca.")
            return
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.toast("No se pudo crear la carpeta de clips.")
            return
        jid = self.juego_id
        cantidad = 0
        for archivo in archivos:
            origen = Path(archivo)
            destino = nombre_disponible(carpeta, origen.name)
            if not self._copiar_con_progreso(archivo, destino, "Adjuntando clip"):
                break
            with self.conn:
                self.conn.execute("INSERT INTO clips(juego_id,titulo,ruta) VALUES (?,?,?)",
                                  (jid, origen.stem, str(destino)))
            cantidad += 1
        if cantidad:
            self.cargar_clips()
            self.toast(f"{cantidad} {'clip adjuntado' if cantidad == 1 else 'clips adjuntados'}.")

    def _detener_clips(self):
        if self.clips_reproductor is not None:
            self.clips_reproductor.detener()

    def construir_voces(self):
        vista = QWidget()
        cuerpo = QVBoxLayout(vista)
        cuerpo.setContentsMargins(8, 8, 8, 8)
        panel = QFrame()
        panel.setObjectName("panel")
        contenido = QVBoxLayout(panel)
        cabecera = QHBoxLayout()
        titulo = QLabel("Voces de la novela")
        titulo.setObjectName("heading")
        cabecera.addWidget(titulo)
        cabecera.addStretch(1)
        adjuntar = BotonAnimado("＋ Adjuntar audio", primario=True)
        adjuntar.clicked.connect(self.adjuntar_voz)
        cabecera.addWidget(adjuntar)
        renombrar = BotonAnimado("✎ Renombrar archivo")
        renombrar.clicked.connect(lambda: self._renombrar_adjunto("voces"))
        cabecera.addWidget(renombrar)
        contenido.addLayout(cabecera)

        self.lista_voces = QListWidget()
        self._configurar_tarjetas_voces(self.lista_voces)
        self.lista_voces.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.lista_voces.itemActivated.connect(self.reproducir_voz)
        contenido.addWidget(self.lista_voces, 1)
        self.estado_voces = QLabel()
        contenido.addWidget(self.estado_voces)

        controles = QHBoxLayout()
        self.btn_voz = BotonAnimado("▶ Reproducir")
        self.btn_voz.clicked.connect(self._alternar_voz)
        controles.addWidget(self.btn_voz)
        detener = BotonAnimado("■ Detener")
        detener.clicked.connect(self._detener_voces)
        controles.addWidget(detener)
        self.posicion_voces = QSlider(Qt.Orientation.Horizontal)
        self.posicion_voces.setAccessibleName("Posición de la voz")
        self.posicion_voces.setRange(0, 0)
        self.posicion_voces.sliderMoved.connect(
            lambda posicion: self.voces_player.setPosition(posicion) if self.voces_player else None)
        controles.addWidget(self.posicion_voces, 1)
        self.tiempo_voces = QLabel("0:00 / 0:00")
        controles.addWidget(self.tiempo_voces)
        controles.addWidget(QLabel("Volumen"))
        self.volumen_voces = QSlider(Qt.Orientation.Horizontal)
        self.volumen_voces.setAccessibleName("Volumen de voces")
        self.volumen_voces.setRange(0, 100)
        self.volumen_voces.setValue(85)
        self.volumen_voces.setFixedWidth(105)
        self.volumen_voces.valueChanged.connect(
            lambda valor: self.voces_audio.setVolume(valor / 100) if self.voces_player else None)
        controles.addWidget(self.volumen_voces)
        contenido.addLayout(controles)
        cuerpo.addWidget(panel, 1)
        return vista

    @staticmethod
    def _configurar_tarjetas_voces(lista):
        lista.setViewMode(QListWidget.ViewMode.IconMode)
        lista.setMovement(QListWidget.Movement.Static)
        lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        lista.setIconSize(QSize(164, 164))
        lista.setGridSize(QSize(220, 230))
        lista.setSpacing(8)
        lista.setWordWrap(True)
        lista.setUniformItemSizes(True)
        lista.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

    @staticmethod
    def _icono_voz(foto, encuadre):
        return QIcon(avatar(foto or "", 164, parse_enc(encuadre)))

    def _elegir_heroina_voz(self, heroinas, archivo):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Asignar audio a una heroína")
        dialogo.resize(930, 640)
        contenido = QVBoxLayout(dialogo)
        texto = QLabel(f"¿De quién es «{archivo}»?")
        texto.setWordWrap(True)
        contenido.addWidget(texto)
        buscar = QLineEdit()
        buscar.setPlaceholderText("Buscar por nombre…")
        contenido.addWidget(buscar)
        lista = QListWidget()
        self._configurar_tarjetas_voces(lista)
        contenido.addWidget(lista, 1)
        for hid, nombre, foto, encuadre in heroinas:
            item = QListWidgetItem(self._icono_voz(foto, encuadre), nombre)
            item.setData(Qt.ItemDataRole.UserRole, hid)
            item.setToolTip(nombre)
            lista.addItem(item)
        def filtrar(texto):
            aguja = texto.strip().casefold()
            for i in range(lista.count()):
                item = lista.item(i)
                item.setHidden(aguja not in item.text().casefold())
            actual = lista.currentItem()
            if actual is None or actual.isHidden():
                lista.setCurrentItem(next((lista.item(i) for i in range(lista.count())
                                           if not lista.item(i).isHidden()), None))
        buscar.textChanged.connect(filtrar)
        acciones = QHBoxLayout()
        acciones.addStretch(1)
        cancelar = BotonAnimado("Cancelar")
        cancelar.clicked.connect(dialogo.reject)
        elegir = BotonAnimado("Asignar audio", primario=True)
        def aceptar():
            if lista.currentItem() is not None and not lista.currentItem().isHidden():
                dialogo.accept()
        elegir.clicked.connect(aceptar)
        lista.itemActivated.connect(aceptar)
        acciones.addWidget(cancelar)
        acciones.addWidget(elegir)
        contenido.addLayout(acciones)
        lista.setCurrentRow(0)
        buscar.setFocus()
        return (lista.currentItem().data(Qt.ItemDataRole.UserRole)
                if dialogo.exec() == QDialog.DialogCode.Accepted else None)

    def cargar_voces(self, seleccion=None):
        if self.juego_id is None:
            return
        filas = self.conn.execute("""
            SELECT v.id, v.titulo, v.ruta, h.nombre, h.foto, h.foto_enc
            FROM voces v LEFT JOIN heroinas h ON h.id = v.heroina_id
            WHERE v.juego_id = ? ORDER BY h.orden, h.nombre COLLATE NOCASE, v.id
        """, (self.juego_id,)).fetchall()
        self.lista_voces.clear()
        indice = 0
        for i, (vid, titulo, ruta, heroina, foto, encuadre) in enumerate(filas):
            nombre = heroina or "Heroína eliminada"
            item = QListWidgetItem(self._icono_voz(foto, encuadre), f"{titulo}\n{nombre}")
            item.setData(Qt.ItemDataRole.UserRole, ruta)
            item.setData(Qt.ItemDataRole.UserRole + 1, vid)
            item.setToolTip(f"{Path(ruta).name}\n{nombre}")
            self.lista_voces.addItem(item)
            if vid == seleccion:
                indice = i
        if filas:
            self.lista_voces.setCurrentRow(indice)
        self.estado_voces.setText("" if filas else "Adjunta un audio y selecciona a su heroína.")

    def adjuntar_voz(self):
        jid = self.juego_id
        if jid is None:
            return
        heroinas = self.conn.execute("""
            SELECT id, nombre, foto, foto_enc FROM heroinas
            WHERE juego_id = ? AND nombre <> 'General'
            ORDER BY orden, nombre
        """, (jid,)).fetchall()
        if not heroinas:
            self.toast("Añade una heroína a la novela antes de adjuntar voces.")
            return
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Adjuntar audio de una heroína", str(ROOT), f"Audio ({EXT_AUDIO} *.aac *.opus)")
        if not archivo or jid != self.juego_id:
            return
        origen = Path(archivo)
        if origen.suffix.lower() not in {pat[1:] for pat in (EXT_AUDIO + " *.aac *.opus").split()}:
            self.toast("Selecciona un archivo de audio compatible.")
            return
        elegida = self._elegir_heroina_voz(heroinas, origen.name)
        if elegida is None or jid != self.juego_id:
            return
        carpeta = (ROOT / self.juego_carpeta / "Voces").resolve()
        if not carpeta.is_relative_to(ROOT.resolve()):
            self.toast("La carpeta de voces debe estar dentro de la biblioteca.")
            return
        destino = None
        copiado = False
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
            destino = nombre_disponible(carpeta, origen.name)
            copiado = self._copiar_con_progreso(origen, destino, "Adjuntando voz")
            if not copiado:
                return
            with self.conn:
                cursor = self.conn.execute(
                    "INSERT INTO voces(juego_id, heroina_id, titulo, ruta) VALUES (?,?,?,?)",
                    (jid, elegida, destino.stem, str(destino)))
        except (OSError, sqlite3.Error):
            if copiado:
                destino.unlink(missing_ok=True)
            self.toast("No se pudo adjuntar el audio.")
            return
        if jid == self.juego_id:
            self.cargar_voces(cursor.lastrowid)
        self.toast("Audio adjuntado.")

    def _iniciar_reproductor_voces(self):
        self.voces_player = QMediaPlayer(self)
        self.voces_audio = QAudioOutput(self)
        self.voces_audio.setVolume(self.volumen_voces.value() / 100)
        self.voces_player.setAudioOutput(self.voces_audio)
        self.voces_player.durationChanged.connect(self._progreso_voz)
        self.voces_player.positionChanged.connect(self._progreso_voz)
        self.voces_player.playbackStateChanged.connect(self._estado_reproductor_voz)
        self.voces_player.errorOccurred.connect(
            lambda *_: self.toast("No se pudo reproducir el archivo de audio."))

    def reproducir_voz(self, item):
        if item is None:
            return
        ruta = Path(item.data(Qt.ItemDataRole.UserRole))
        if not ruta.is_file():
            self.toast("El audio ya no está en el disco.")
            return
        if self.voces_player is None:
            self._iniciar_reproductor_voces()
        fuente = QUrl.fromLocalFile(str(ruta))
        if self.voces_player.source() != fuente:
            self.voces_player.setSource(fuente)
        elif self.voces_player.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia:
            self.voces_player.setPosition(0)
        self._opening_empezo()
        self.player.pause()
        self.voces_player.play()
        self.estado_voces.setText(item.text().replace('\n', ' · '))

    def _alternar_voz(self):
        item = self.lista_voces.currentItem()
        if item and self.voces_player is not None:
            fuente = QUrl.fromLocalFile(item.data(Qt.ItemDataRole.UserRole))
            if (self.voces_player.source() == fuente and
                    self.voces_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState):
                self.voces_player.pause()
                return
        self.reproducir_voz(item)

    def _estado_reproductor_voz(self, estado):
        sonando = estado == QMediaPlayer.PlaybackState.PlayingState
        self.btn_voz.setText("⏸ Pausar" if sonando else "▶ Reproducir")

    def _progreso_voz(self, _):
        pos = self.voces_player.position()
        dur = self.voces_player.duration()
        self.posicion_voces.setMaximum(dur)
        if not self.posicion_voces.isSliderDown():
            self.posicion_voces.setValue(pos)
        self.tiempo_voces.setText(f"{self.formato_tiempo(pos)} / {self.formato_tiempo(dur)}")

    def _detener_voces(self):
        if self.voces_player is not None:
            self.voces_player.stop()
            self.voces_player.setSource(QUrl())
            self.estado_voces.clear()

    def _renombrar_adjunto(self, tabla):
        es_clip = tabla == "clips"
        lista = self.lista_clips if es_clip else self.lista_voces
        item = lista.currentItem()
        if item is None:
            self.toast("Selecciona el archivo que quieres renombrar.")
            return
        jid = self.juego_id
        vid = item.data(Qt.ItemDataRole.UserRole + 1)
        fila = self.conn.execute(
            f"SELECT ruta FROM {tabla} WHERE id=? AND juego_id=?", (vid, jid)).fetchone()
        if not fila:
            return
        ruta = Path(fila[0])
        nombre, ok = QInputDialog.getText(
            self, "Renombrar archivo", "Nuevo nombre sin la extensión", text=ruta.stem)
        if not ok or jid != self.juego_id:
            return
        nombre = nombre.strip().rstrip(". ")
        if nombre.lower().endswith(ruta.suffix.lower()):
            nombre = nombre[:-len(ruta.suffix)].rstrip(". ")
        if not nombre or nombre != nombre_seguro(nombre) or Path(nombre).is_reserved():
            self.toast("Escribe un nombre de archivo válido.")
            return
        destino = ruta.with_name(nombre + ruta.suffix)
        if destino.name == ruta.name:
            return
        carpeta = (ROOT / self.juego_carpeta / ("Clips" if es_clip else "Voces")).resolve()
        if not carpeta.is_relative_to(ROOT.resolve()) or ruta.resolve().parent != carpeta or not ruta.is_file():
            self.toast("El archivo no está en la carpeta de la novela.")
            return
        if destino.exists() and destino != ruta:
            self.toast("Ya existe un archivo con ese nombre.")
            return
        if es_clip and self.clips_reproductor is not None:
            self.clips_reproductor.soltar()
        elif not es_clip:
            self._detener_voces()
        cambio = False
        try:
            with self.conn:
                ruta.rename(destino)
                cambio = True
                self.conn.execute(f"UPDATE {tabla} SET titulo=?, ruta=? WHERE id=? AND juego_id=?",
                                  (nombre, str(destino), vid, jid))
        except (OSError, sqlite3.Error):
            if cambio:
                destino.rename(ruta)
            self.toast("No se pudo renombrar el archivo.")
            return
        cargar = self.cargar_clips if es_clip else self.cargar_voces
        cargar(vid)
        self.toast(f"Archivo renombrado a «{destino.name}».")

    def _al_cambiar_pestana_juego(self, i):
        if i == self.IDX_VOCES:
            self.cargar_voces()
        else:
            self._detener_voces()
        if i == self.IDX_CLIPS:
            self.cargar_clips()
        else:
            self._detener_clips()
        if i == 1:
            self.cargar_musica()
        if i == self.IDX_FICHA:
            self.cargar_ficha_novela()
        elif self.guia_pdf.status() != QPdfDocument.Status.Null:
            self.guia_pdf.close()
        if i == self.IDX_TOP:
            self.cargar_top()
        if i == self.IDX_OPENINGS:
            self.cargar_openings()
            self.opening.reanudar()
        else:
            self.opening.pausar_por_pestana()

    # -----------------------------------------------------
    # PÁGINA «OPENINGS» DEL PANEL PRINCIPAL
    # -----------------------------------------------------

    def abrir_openings(self):
        self.cargar_openings_global()
        self.ir_a_pagina(self.PAG_OPENINGS)

    def construir_openings_global(self):
        self._ops = {}
        self._ops_rutas = {}
        self._ultimos_openings = []
        self._seleccion_openings = []
        self._opening_en_pantalla = None
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        fila = QHBoxLayout()
        volver = BotonAnimado("← Biblioteca")
        volver.clicked.connect(self.volver_biblioteca)
        fila.addWidget(volver)
        titulo = QLabel("Sala de openings")
        titulo.setObjectName("heading")
        fila.addWidget(titulo, 1)
        v.addLayout(fila)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(10)
        escenario = QFrame()
        escenario.setObjectName("panel")
        zona = QVBoxLayout(escenario)
        zona.setContentsMargins(10, 8, 10, 8)
        self.opening_global = self._nuevo_reproductor_opening()
        self.opening_global.empezo.connect(self._registrar_opening_visto)
        zona.addWidget(self.opening_global, 1)
        self.lbl_op_actual = QLabel("Elige un opening del catálogo")
        self.lbl_op_actual.setObjectName("heading")
        self.lbl_op_actual.setWordWrap(True)
        self.lbl_op_novela = QLabel("")
        self.lbl_op_novela.setObjectName("muted")
        descripcion = QHBoxLayout()
        textos = QVBoxLayout()
        textos.setSpacing(2)
        textos.addWidget(self.lbl_op_actual)
        textos.addWidget(self.lbl_op_novela)
        descripcion.addLayout(textos, 1)
        salir = self._boton_cerrar_video(self.opening_global)
        descripcion.addWidget(salir)
        zona.addLayout(descripcion)
        cuerpo.addWidget(escenario, 1)

        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(395)
        catalogo = QVBoxLayout(panel)
        catalogo.setContentsMargins(10, 10, 10, 10)
        self.buscar_op = QLineEdit()
        self.buscar_op.setPlaceholderText("Buscar por opening o novela")
        catalogo.addWidget(self.buscar_op)
        self.filtro_op = QComboBox()
        self.filtro_op.addItems(["Todos los openings", "Favoritos", "Vistos recientemente",
                                 "Selección guardada"])
        catalogo.addWidget(self.filtro_op)
        self.lista_op_todos = QListWidget()
        self.lista_op_todos.setItemDelegate(DelegadoCatalogoOpening(self.lista_op_todos))
        self.lista_op_todos.setUniformItemSizes(True)
        self.lista_op_todos.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.lista_op_todos.itemActivated.connect(self._op_doble_clic)
        self.lista_op_todos.setToolTip("Doble clic o Enter para ver. Esc para salir del video.")
        catalogo.addWidget(self.lista_op_todos, 1)
        self.lbl_op_global = QLabel("")
        self.lbl_op_global.setObjectName("muted")
        self.lbl_op_global.setWordWrap(True)
        catalogo.addWidget(self.lbl_op_global)
        acciones = QHBoxLayout()
        self.btn_ver_op = BotonAnimado("▶ Reproducir", primario=True)
        self.btn_ver_op.clicked.connect(self._op_ver_seleccionado)
        self.btn_ver_op.setToolTip("Reproducir el opening seleccionado (Enter)")
        self.btn_fav_op = BotonAnimado("♡ Favorito")
        self.btn_fav_op.clicked.connect(self._op_favorito_seleccionado)
        acciones.addWidget(self.btn_ver_op, 1)
        acciones.addWidget(self.btn_fav_op)
        catalogo.addLayout(acciones)
        cuerpo.addWidget(panel)
        v.addLayout(cuerpo, 1)
        self.lista_op_todos.currentItemChanged.connect(self._actualizar_acciones_opening)
        self.opening_global.reposo.clic.disconnect(self.opening_global.alternar_play)
        self.opening_global.reposo.clic.connect(self._op_ver_seleccionado)
        self.opening_global.player.sourceChanged.connect(self._actualizar_acciones_opening)
        self.buscar_op.textChanged.connect(self._pintar_lista_ops)
        self.filtro_op.currentIndexChanged.connect(self._pintar_lista_ops)
        self._actualizar_acciones_opening()
        return w

    def _ids_openings_guardados(self, clave):
        fila = self.conn.execute("SELECT valor FROM ajustes WHERE clave=?", (clave,)).fetchone()
        try:
            ids = json.loads(fila[0]) if fila else []
        except (ValueError, TypeError):
            return []
        return list(dict.fromkeys(i for i in ids if type(i) is int and i in self._ops)) \
            if isinstance(ids, list) else []

    def cargar_openings_global(self):
        filas = self.conn.execute("""
            SELECT v.id, v.titulo, v.ruta, j.nombre, v.me_gusta, j.portada, j.portada_enc
            FROM videos v JOIN juegos j ON j.id = v.juego_id
            ORDER BY j.orden, j.nombre COLLATE NOCASE, v.orden, v.id""").fetchall()
        self._ops = {i: dict(titulo=titulo, ruta=ruta, novela=novela, favorito=bool(fav),
                             portada=portada, enc=parse_enc(enc))
                     for i, titulo, ruta, novela, fav, portada, enc in filas}
        self._ops_rutas = {d["ruta"]: i for i, d in self._ops.items()}
        self._ultimos_openings = self._ids_openings_guardados("openings_recientes")
        self._seleccion_openings = self._ids_openings_guardados("openings_lista")
        self._pintar_lista_ops()

    def _pintar_lista_ops(self, *_):
        filtro = self.buscar_op.text().strip().casefold()
        modo = self.filtro_op.currentIndex()
        ids = self._ops
        if modo == 1:
            ids = [i for i, datos in self._ops.items() if datos["favorito"]]
        elif modo == 2:
            ids = self._ultimos_openings
        elif modo == 3:
            ids = self._seleccion_openings

        lista = self.lista_op_todos
        anterior = lista.currentItem()
        elegir = anterior.data(Qt.ItemDataRole.UserRole) if anterior else self._opening_en_pantalla
        previo = lista.blockSignals(True)
        lista.setUpdatesEnabled(False)
        lista.clear()
        for i in ids:
            datos = self._ops[i]
            if filtro and filtro not in (datos["titulo"] + " " + datos["novela"]).casefold():
                continue
            it = QListWidgetItem(datos["titulo"])
            it.setData(Qt.ItemDataRole.UserRole, i)
            it.setData(Qt.ItemDataRole.UserRole + 1, datos)
            it.setToolTip(f"{datos['titulo']} · {datos['novela']}")
            lista.addItem(it)
            if i == elegir:
                lista.setCurrentItem(it)
        if lista.currentRow() < 0 and lista.count():
            lista.setCurrentRow(0)
        lista.setUpdatesEnabled(True)
        lista.blockSignals(previo)
        self.lbl_op_global.setText(
            "Sin resultados" if not lista.count() and (filtro or modo)
            else "Adjunta videos desde la pestaña Openings de una novela" if not lista.count()
            else "")
        self._actualizar_acciones_opening()

    def _actualizar_acciones_opening(self, *_):
        item = self.lista_op_todos.currentItem()
        datos = self._ops.get(item.data(Qt.ItemDataRole.UserRole)) if item else None
        if self.opening_global.player.source().isEmpty():
            self.lbl_op_actual.setText(datos["titulo"] if datos else "Elige un opening del catálogo")
            self.lbl_op_novela.setText(datos["novela"] if datos else "")
        self.btn_ver_op.setEnabled(datos is not None)
        self.btn_fav_op.setEnabled(datos is not None)
        self.btn_fav_op.setText("♥ Favorito" if datos and datos["favorito"] else "♡ Favorito")

    def _op_ver_seleccionado(self):
        item = self.lista_op_todos.currentItem()
        if item is not None:
            self._op_doble_clic(item)

    def _op_doble_clic(self, item):
        vid = item.data(Qt.ItemDataRole.UserRole)
        datos = self._ops[vid]
        if not Path(datos["ruta"]).is_file():
            self.toast("El archivo de video ya no está en el disco.")
            return
        ids = [self.lista_op_todos.item(i).data(Qt.ItemDataRole.UserRole)
               for i in range(self.lista_op_todos.count())]
        disponibles = [i for i in ids if i == vid or Path(self._ops[i]["ruta"]).is_file()]
        self.opening_global.cargar(
            [self._ops[i]["ruta"] for i in disponibles], True, True,
            [self._ops[i]["titulo"] for i in disponibles], disponibles.index(vid)
        )

    @staticmethod
    def _ruta_opening_actual(reproductor):
        if 0 <= reproductor._idx < len(reproductor._rutas):
            return reproductor._rutas[reproductor._idx]
        return ""

    def _registrar_opening_visto(self):
        vid = self._ops_rutas.get(self._ruta_opening_actual(self.opening_global))
        if vid is None:
            return
        info = self._ops[vid]
        self._opening_en_pantalla = vid
        self.lbl_op_actual.setText(info["titulo"])
        self.lbl_op_novela.setText(info["novela"])
        if self._ultimos_openings[:1] != [vid]:
            anteriores = [i for i in self._ultimos_openings if i != vid]
            self._ultimos_openings = [vid] + anteriores[:29]
            guardar_ajuste(self.conn, "openings_recientes", json.dumps(self._ultimos_openings))
            if self.filtro_op.currentIndex() == 2:
                self._pintar_lista_ops()
        for fila in range(self.lista_op_todos.count()):
            if self.lista_op_todos.item(fila).data(Qt.ItemDataRole.UserRole) == vid:
                self.lista_op_todos.setCurrentRow(fila)
                break

    def _marcar_opening_favorito(self, vid):
        self.conn.execute(
            "UPDATE videos SET me_gusta = 1 - COALESCE(me_gusta, 0) WHERE id=?", (vid,))
        self.conn.commit()

    def _op_favorito_seleccionado(self):
        item = self.lista_op_todos.currentItem()
        if item is not None:
            self._marcar_opening_favorito(item.data(Qt.ItemDataRole.UserRole))
            self.cargar_openings_global()

    def menu_musica(self, punto):
        it = self.lista_musica.itemAt(punto)
        if not it:
            return
        if not it.isSelected():
            self.lista_musica.clearSelection()
            it.setSelected(True)
        m = QMenu(self)
        a_play = m.addAction("▶ Reproducir desde aquí")
        a_ren = m.addAction("✎ Renombrar")
        a_ubi = m.addAction("📂 Abrir ubicación del archivo")
        m.addSeparator()
        a_del = m.addAction("🗑 Eliminar permanentemente")
        acc = m.exec(self.lista_musica.mapToGlobal(punto))
        if acc == a_play:
            self.reproducir_desde_lista(it)
        elif acc == a_ubi:
            self.abrir_ubicacion_pista()
        elif acc == a_ren:
            self.renombrar_musica()
        elif acc == a_del:
            self.eliminar_musica()

    def reproducir_desde_lista(self, item):
        info = item.data(Qt.ItemDataRole.UserRole + 1)
        self.reproducir_todo(info["n"] - 1 if info else self.lista_musica.row(item))

    def reproducir_todo(self, indice):
        pistas = self.pistas(self.juego_id)
        if pistas:
            self.reproducir_cola(pistas, indice)

    def reproducir_aleatorio_global(self):
        pistas = self.pistas()
        if not pistas:
            self.toast("Aún no hay música: añade MP3 en la pestaña Música de una novela")
            return
        self.btn_shuffle.setChecked(True)
        self.repetir = 1
        self.aplicar_repetir()
        self.reproducir_cola(pistas, random.randrange(len(pistas)))
        self.toast(f"Aleatorio global · {len(pistas)} pistas de todas tus novelas")

    # -----------------------------------------------------
    # BIBLIOTECA DE NOVELAS (tarjetas)
    # -----------------------------------------------------

    def cambiar_tamano_tarjetas(self, v):
        self.grid_juegos.min_w = v
        self.grid_juegos.relayout()

    def cargar_biblioteca(self, *args):
        filtro = self.buscar_juego.text().casefold().strip()
        todas = self.conn.execute("""
            SELECT j.id, j.nombre, j.portada,
                   (SELECT COUNT(*) FROM imagenes i WHERE i.juego_id = j.id),
                   j.portada_enc,
                   (SELECT COUNT(*) FROM heroinas h WHERE h.juego_id = j.id
                        AND h.nombre <> 'General' AND h.tipo = 'heroina'),
                   j.horas, j.fecha_inicio, j.fecha_fin
            FROM juegos j ORDER BY j.orden, j.nombre COLLATE NOCASE
        """).fetchall()
        # ---- filtro por estado
        est = self.filtro_bib.currentText()
        if est == "En curso":
            filas = [f for f in todas if f[7] and not f[8]]
        elif est == "Terminadas":
            filas = [f for f in todas if f[8]]
        elif est == "Sin empezar":
            filas = [f for f in todas if not f[7] and not f[8]]
        elif est == "Sin portada":
            filas = [f for f in todas if not (f[2] and Path(f[2]).exists())]
        else:
            filas = list(todas)
        # ---- orden (el manual es el que se cambia arrastrando)
        modo = self.orden_bib.currentText()
        nom = lambda f: clave_alfabetica(f[1])
        if modo == "Nombre A-Z":
            filas.sort(key=nom)
        elif modo == "Nombre Z-A":
            filas.sort(key=nom, reverse=True)
        elif modo == "Recién agregadas":
            filas.sort(key=lambda f: f[0], reverse=True)
        elif modo == "Más capturas":
            filas.sort(key=lambda f: (-f[3], nom(f)))
        elif modo == "Más horas jugadas":
            filas.sort(key=lambda f: (-(f[6] or 0), nom(f)))
        elif modo == "Más recientes":
            # 1.º la novela actual (empezada y aún sin terminar; la que empezaste más tarde
            # primero), 2.º las terminadas por fecha de fin (la más reciente primero) y
            # 3.º las que no tienen fechas.
            actuales = sorted((f for f in filas if f[7] and not f[8]),
                              key=lambda f: str(f[7]), reverse=True)
            terminadas = sorted((f for f in filas if f[8]),
                                key=lambda f: (str(f[8]), str(f[7] or "")), reverse=True)
            resto = [f for f in filas if not f[7] and not f[8]]
            filas = actuales + terminadas + resto
        self._filas_bib = filas
        cache = self.__dict__.setdefault("_tarjetas_bib", {})
        vigentes = {f[0] for f in todas} | {-1}
        for fuera in cache.keys() - vigentes:
            cache.pop(fuera).deleteLater()
        if -1 not in cache:
            nueva = cache[-1] = TarjetaJuego(nueva=True)
            nueva.clic.connect(lambda _id: self.anadir_juego())
        tarjetas = [cache[-1]]
        for jid, nombre, portada, n, enc, _nh, _hr, _fi, _ff in filas:
            if filtro and filtro not in nombre.casefold():
                continue
            encuadre = parse_enc(enc)
            t = cache.get(jid)
            if t is None:
                t = cache[jid] = TarjetaJuego(jid, nombre, portada, n, enc=encuadre)
                t.clic.connect(self.entrar_juego)
                t.menu.connect(self.menu_juego)
            elif (t.nombre, t.portada, t.cantidad, t.enc) != (nombre, portada, n, encuadre):
                t.nombre, t.portada, t.cantidad, t.enc = nombre, portada, n, encuadre
                t.update()
            tarjetas.append(t)
        self.grid_juegos.poner(tarjetas)
        self.lbl_bib.setText(
            f"{len(todas)} novelas registradas" if len(filas) == len(todas)
            else f"{len(filas)} de {len(todas)} novelas · filtro: {est}")
        self.actualizar_contador_favoritos()

    def novela_al_azar(self):
        filas = [f for f in getattr(self, "_filas_bib", [])
                 if not self.buscar_juego.text().strip()
                 or self.buscar_juego.text().casefold().strip() in f[1].casefold()]
        if not filas:
            self.toast("No hay novelas que mostrar")
            return
        self.entrar_juego(random.choice(filas)[0])

    def guardar_orden_juegos(self, ids):
        if self.buscar_juego.text().strip():
            self.toast("Borra la búsqueda para ordenar las novelas")
            QTimer.singleShot(0, self.cargar_biblioteca)
            return
        if self.orden_bib.currentText() != "Orden manual" \
                or self.filtro_bib.currentText() != "Todas":
            self.toast("Para arrastrar, elige «Orden manual» y el filtro «Todas»")
            QTimer.singleShot(0, self.cargar_biblioteca)
            return
        barra = self.scroll_bib.verticalScrollBar().value()
        for pos, jid in enumerate(ids, 1):
            self.conn.execute("UPDATE juegos SET orden = ? WHERE id = ?", (pos, jid))
        self.conn.commit()

        def recargar():
            self.cargar_biblioteca()
            QTimer.singleShot(0, lambda: self.scroll_bib.verticalScrollBar().setValue(barra))
        QTimer.singleShot(0, recargar)

    def anadir_juego(self):
        dlg = DialogoTarjeta(self, "Nueva novela visual", "Nombre de la novela:",
                             info="Escribe el nombre tal como quieres verlo (puede llevar «:», «?», etc.). "
                                  "La carpeta del disco usa una versión segura del nombre.",
                             sanear=False)
        if not dlg.exec():
            return
        nombre = dlg.nombre()
        carpeta_nom = carpeta_libre(self.conn, nombre)
        try:
            cur = self.conn.execute("INSERT INTO juegos(nombre, carpeta) VALUES (?, ?)",
                                    (nombre, carpeta_nom))
            jid = cur.lastrowid
            self.conn.commit()
        except sqlite3.IntegrityError:
            QMessageBox.information(self, "Ya existe", "Esa novela ya está registrada.")
            return
        (ROOT / carpeta_nom).mkdir(parents=True, exist_ok=True)
        if dlg.imagen:
            ruta = copiar_asset(dlg.imagen, "portadas", f"juego_{jid}")
            self.conn.execute("UPDATE juegos SET portada = ?, portada_enc = ? WHERE id = ?",
                              (ruta, fmt_enc(dlg.encuadre), jid))
            self.conn.commit()
        self.cargar_biblioteca()

    def menu_juego(self, jid, pos):
        m = QMenu(self)
        a_abrir = m.addAction("Abrir")
        a_cover = m.addAction("✎ Editar nombre / portada")
        a_antes = m.addAction("⬅ Mover antes")
        a_despues = m.addAction("➡ Mover después")
        fe = self.conn.execute("SELECT excluir_hall FROM juegos WHERE id = ?", (jid,)).fetchone()
        excluida = bool(fe and fe[0])
        a_hall = m.addAction("👑 Incluir en Heroínas de heroínas" if excluida
                             else "🚫 Excluir de Heroínas de heroínas")
        fs = self.conn.execute("SELECT solo_campeona FROM juegos WHERE id = ?", (jid,)).fetchone()
        solo = bool(fs and fs[0])
        a_solo = m.addAction("🥇🥈 Que pasen campeona y subcampeona" if solo
                             else "🥇 Que pase solo la campeona")
        m.addSeparator()
        a_quitar = m.addAction("Quitar novela (conserva archivos)")
        a_borrar = m.addAction("🗑 Eliminar novela PERMANENTEMENTE (borra archivos)")
        accion = m.exec(pos)
        if accion == a_abrir:
            self.entrar_juego(jid)
        elif accion == a_antes:
            self.mover_juego(jid, -1)
        elif accion == a_despues:
            self.mover_juego(jid, 1)
        elif accion == a_hall:
            self.fijar_participacion_hall(jid, excluida)
        elif accion == a_solo:
            self.fijar_solo_campeona(jid, not solo)
        elif accion == a_cover:
            fila = self.conn.execute(
                "SELECT nombre, portada, portada_enc, carpeta FROM juegos WHERE id = ?",
                (jid,)).fetchone()
            dlg = DialogoTarjeta(self, "Editar novela", "Nombre de la novela:", nombre=fila[0],
                                 imagen=fila[1], enc=parse_enc(fila[2]), nombre_editable=True,
                                 info=f"Cambiar el nombre NO toca la carpeta del disco "
                                      f"(«{fila[3]}»): tus archivos y datos quedan intactos.",
                                 sanear=False)
            if dlg.exec():
                nuevo = dlg.nombre()
                if nuevo and nuevo != fila[0]:
                    if not self.renombrar_juego(jid, fila[0], nuevo):
                        return
                portada = fila[1]
                if dlg.cambio_imagen:
                    portada = copiar_asset(dlg.imagen, "portadas", f"juego_{jid}") \
                        if dlg.imagen else ""
                self.conn.execute("UPDATE juegos SET portada = ?, portada_enc = ? WHERE id = ?",
                                  (portada, fmt_enc(dlg.encuadre), jid))
                self.conn.commit()
                self.cargar_biblioteca()
        elif accion == a_quitar:
            if QMessageBox.question(
                    self, "Quitar novela",
                    "Se quitarán del catálogo la novela, sus heroínas, imágenes y música.\n"
                    "Los archivos del disco NO se borran. ¿Continuar?"
            ) == QMessageBox.StandardButton.Yes:
                for tabla in ("musica", "videos", "imagenes", "heroinas"):
                    self.conn.execute(f"DELETE FROM {tabla} WHERE juego_id = ?", (jid,))
                self.conn.execute("DELETE FROM juegos WHERE id = ?", (jid,))
                self.conn.commit()
                self.cargar_biblioteca()
        elif accion == a_borrar:
            self.eliminar_novela_total(jid)

    def _soltar_audio(self):
        """Libera los archivos de música (Windows no deja renombrar/borrar archivos en uso)."""
        self._detener_musica()
        self._cancelar_normalizacion()
        self._timer_mp3.start(50)
        self._soltar_openings(procesar=False)
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

    def renombrar_juego(self, jid, viejo, nuevo):
        """Cambia SOLO el nombre que se muestra. La carpeta y las rutas guardadas no se tocan."""
        if self.conn.execute("SELECT 1 FROM juegos WHERE nombre = ? AND id <> ?",
                             (nuevo, jid)).fetchone():
            QMessageBox.information(self, "Ya existe", "Ya hay una novela con ese nombre.")
            return False
        self.conn.execute("UPDATE juegos SET nombre = ? WHERE id = ?", (nuevo, jid))
        self.conn.commit()
        return True

    def eliminar_novela_total(self, jid):
        """Borra la novela ENTERA: base de datos + carpeta del disco + portada y fotos."""
        fila = self.conn.execute("SELECT nombre, portada, carpeta FROM juegos WHERE id = ?",
                                 (jid,)).fetchone()
        if not fila:
            return
        nombre, portada, carpeta_nom = fila
        n_img = self.conn.execute("SELECT COUNT(*) FROM imagenes WHERE juego_id = ?",
                                  (jid,)).fetchone()[0]
        n_mus = self.conn.execute("SELECT COUNT(*) FROM musica WHERE juego_id = ?",
                                  (jid,)).fetchone()[0]
        n_her = self.conn.execute("SELECT COUNT(*) FROM heroinas WHERE juego_id = ?",
                                  (jid,)).fetchone()[0]
        carpeta = ROOT / (carpeta_nom or nombre_seguro(nombre))
        if QMessageBox.warning(
                self, "Eliminar novela PERMANENTEMENTE",
                f"Vas a ELIMINAR «{nombre}» por completo:\n\n"
                f"•  {n_img} imágenes\n•  {n_mus} pistas de música\n•  {n_her} heroínas\n"
                f"•  su portada y la carpeta del disco:\n   {carpeta}\n\n"
                "Los archivos se borrarán del disco y NO se podrán recuperar.\n¿Continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        escrito, ok = QInputDialog.getText(
            self, "Confirmar eliminación",
            f"Para confirmar, escribe el nombre exacto de la novela:\n\n{nombre}")
        if not ok or escrito.strip() != nombre:
            self.toast("Eliminación cancelada: el nombre no coincidía")
            return

        self._soltar_audio()
        self.cola, self.cola_idx = [], -1
        fallos = []

        def borrar_archivo(ruta):
            try:
                Path(ruta).unlink(missing_ok=True)
            except OSError:
                fallos.append(str(ruta))

        # 1) archivos registrados (por si alguno está fuera de la carpeta de la novela)
        for tabla in ("imagenes", "musica", "videos"):
            for (ruta,) in self.conn.execute(
                    f"SELECT ruta FROM {tabla} WHERE juego_id = ?", (jid,)).fetchall():
                borrar_archivo(ruta)
        # 2) portada y fotos de heroínas (viven en _assets)
        extras = [portada] + [f[0] for f in self.conn.execute(
            "SELECT foto FROM heroinas WHERE juego_id = ?", (jid,)).fetchall()]
        for a in extras:
            if a:
                try:
                    Path(a).resolve().relative_to(ASSETS.resolve())
                except ValueError:
                    continue                      # nunca borra nada fuera de _assets
                borrar_archivo(a)
        # 3) la carpeta completa de la novela (solo si está DENTRO de la biblioteca)
        try:
            if carpeta.exists() and carpeta.resolve() != ROOT.resolve():
                carpeta.resolve().relative_to(ROOT.resolve())
                shutil.rmtree(carpeta, ignore_errors=True)
                if carpeta.exists():
                    fallos.append(str(carpeta))
        except ValueError:
            fallos.append(str(carpeta))

        for tabla in ("musica", "videos", "imagenes", "heroinas"):
            self.conn.execute(f"DELETE FROM {tabla} WHERE juego_id = ?", (jid,))
        self.conn.execute("DELETE FROM juegos WHERE id = ?", (jid,))
        self.conn.commit()
        self.cargar_biblioteca()
        if fallos:
            QMessageBox.warning(
                self, "Eliminada, pero quedaron archivos",
                f"«{nombre}» se quitó de la biblioteca, pero {len(fallos)} archivo(s)/carpeta(s) "
                "no se pudieron borrar (¿abiertos en otro programa?). Bórralos a mano:\n\n"
                + "\n".join(fallos[:6]))
        else:
            self.toast(f"🗑 «{nombre}» eliminada por completo")

    def mover_juego(self, jid, d):
        ids = [r[0] for r in self.conn.execute(
            "SELECT id FROM juegos ORDER BY orden, nombre COLLATE NOCASE")]
        i = ids.index(jid)
        j = i + d
        if not 0 <= j < len(ids):
            return
        ids[i], ids[j] = ids[j], ids[i]
        for pos, x in enumerate(ids, 1):
            self.conn.execute("UPDATE juegos SET orden = ? WHERE id = ?", (pos, x))
        self.conn.commit()
        self.cargar_biblioteca()

    def volver_biblioteca(self):
        self.ir_a_pagina(0)
        self.cargar_biblioteca()

    # -----------------------------------------------------
    # ENTRAR A UNA NOVELA Y HEROINAS
    # -----------------------------------------------------

    def entrar_juego(self, jid):
        fila = self.conn.execute(
            "SELECT nombre, portada, portada_enc, carpeta FROM juegos WHERE id = ?",
            (jid,)).fetchone()
        if not fila:
            return
        self.juego_id, self.juego_nombre = jid, fila[0]
        self.juego_carpeta = fila[3] or nombre_seguro(fila[0])
        self.lbl_juego.setText(fila[0])
        self._aplicar_acento_portada(jid, fila[1])
        self.refrescar_fechas_novela()
        self.refrescar_nota_novela()
        self.cover_musica.poner(fila[1], fila[0], parse_enc(fila[2]))
        self.buscar_pista.clear()

        huerfanas = self.conn.execute(
            "SELECT COUNT(*) FROM imagenes WHERE juego_id = ? AND heroina_id IS NULL",
            (jid,)).fetchone()[0]
        if huerfanas:
            self.asegurar_general()
        else:
            g = self.conn.execute(
                "SELECT id FROM heroinas WHERE juego_id = ? AND nombre = 'General'",
                (jid,)).fetchone()
            if g:
                self.foto_general_desde_portada(g[0])

        self.ir_a_pagina(1)
        self.tabs_juego.setCurrentIndex(0)
        self.cargar_heroinas()
        self._nav_diferido()

        if self.total_personajes() == 0:
            self.pedir_primera_heroina()

    # ---------- color de la interfaz según la portada y nota de la novela

    def _aplicar_acento_portada(self, jid, portada):
        nuevo = None
        if Tema.acento_portada and portada:
            cache = self.__dict__.setdefault("_acentos_cache", {})
            clave = (jid, str(portada))
            if clave not in cache:
                cache[clave] = colores_de_portada(portada)
            nuevo = cache[clave]
        if Tema.acento_juego != nuevo:
            Tema.acento_juego = nuevo
            QTimer.singleShot(0, self._restilizar_acento)

    def _restilizar_acento(self):
        estilo = construir_estilo()
        if estilo != self._estilo_cache:
            self._estilo_cache = estilo
            QApplication.instance().setStyleSheet(estilo)
        for w in self.findChildren(QWidget):
            w.update()

    def refrescar_nota_novela(self):
        f = self.conn.execute("SELECT nota FROM juegos WHERE id = ?", (self.juego_id,)).fetchone()
        n = float(f[0] or 0) if f else 0.0
        self.btn_nota.setText(f"★ {fmt_nota(n)}/10" if n > 0 else "☆ Calificar")

    def elegir_nota_novela(self):
        if self.juego_id is None:
            return
        f = self.conn.execute("SELECT nota FROM juegos WHERE id = ?", (self.juego_id,)).fetchone()
        actual = float(f[0] or 0) if f else 0.0
        m = QMenu(self)
        est = EstrellasNota(actual)
        wa = QWidgetAction(m)
        wa.setDefaultWidget(est)
        m.addAction(wa)
        a_quitar = m.addAction("Quitar nota") if actual > 0 else None
        est.elegida.connect(lambda v: (self.guardar_nota_novela(v), m.close()))
        accion = m.exec(self.btn_nota.mapToGlobal(QPoint(0, self.btn_nota.height())))
        if a_quitar is not None and accion == a_quitar:
            self.guardar_nota_novela(0)

    def guardar_nota_novela(self, nota):
        self.conn.execute("UPDATE juegos SET nota = ? WHERE id = ?", (float(nota), self.juego_id))
        self.conn.commit()
        self.refrescar_nota_novela()
        self.toast(f"⭐ {self.juego_nombre}: {fmt_nota(nota)}/10" if nota > 0
                   else "Nota quitada")

    def refrescar_fechas_novela(self):
        f = self.conn.execute(
            "SELECT fecha_inicio, fecha_fin, horas, excluir_fechas, excluir_horas "
            "FROM juegos WHERE id = ?", (self.juego_id,)).fetchone()
        n_vols = self.conn.execute(
            "SELECT COUNT(*) FROM volumenes WHERE juego_id = ?", (self.juego_id,)).fetchone()[0]
        self.btn_fechas.poner(*(f or ("", "", 0, 0, 0)), vols=n_vols)

    def _partes_de_novela(self, jid):
        """Partes (volúmenes) guardadas de la novela; si no tiene, la parte única de siempre."""
        vols = self.conn.execute(
            "SELECT nombre, fecha_inicio, fecha_fin, horas, excluir_fechas, excluir_horas "
            "FROM volumenes WHERE juego_id = ? ORDER BY orden, id", (jid,)).fetchall()
        if vols:
            return [dict(nombre=n, ini=i, fin=f, horas=h, sin_f=bool(xf), sin_h=bool(xh))
                    for n, i, f, h, xf, xh in vols]
        f = self.conn.execute(
            "SELECT fecha_inicio, fecha_fin, horas, excluir_fechas, excluir_horas "
            "FROM juegos WHERE id = ?", (jid,)).fetchone()
        if f and (f[0] or f[1] or f[2] or f[3] or f[4]):
            return [dict(nombre="", ini=f[0], fin=f[1], horas=f[2], sin_f=bool(f[3]),
                         sin_h=bool(f[4]))]
        return []

    def _guardar_partes_novela(self, jid, partes):
        """Guarda las partes. En la novela se deja un resumen (primera fecha de inicio, última de
        fin y suma de horas) para que filtros y ordenes de la biblioteca sigan funcionando."""
        self.conn.execute("DELETE FROM volumenes WHERE juego_id = ?", (jid,))
        if len(partes) > 1:
            for orden, p in enumerate(partes):
                self.conn.execute(
                    "INSERT INTO volumenes(juego_id, nombre, fecha_inicio, fecha_fin, horas, "
                    "excluir_fechas, excluir_horas, orden) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (jid, p["nombre"], p["ini"], p["fin"], p["horas"],
                     int(p["sin_f"]), int(p["sin_h"]), orden))
        con_f = [p for p in partes if p["ini"] and not p["sin_f"]]
        ini = min((p["ini"] for p in con_f), default="")
        fin = "" if any(not p["fin"] for p in con_f) else max((p["fin"] for p in con_f), default="")
        horas = round(sum(p["horas"] for p in partes if not p["sin_h"]), 1)
        sin_f = bool(partes) and all(p["sin_f"] for p in partes)
        sin_h = bool(partes) and all(p["sin_h"] for p in partes)
        self.conn.execute(
            "UPDATE juegos SET fecha_inicio = ?, fecha_fin = ?, horas = ?, "
            "excluir_fechas = ?, excluir_horas = ? WHERE id = ?",
            (ini, fin, horas, int(sin_f), int(sin_h), jid))
        self.conn.commit()

    def editar_fechas_novela(self):
        if self.juego_id is None:
            return
        dlg = DialogoFechasNovela(self, self.juego_nombre, self._partes_de_novela(self.juego_id))
        if dlg.exec():
            self._guardar_partes_novela(self.juego_id, dlg.partes())
            self.refrescar_fechas_novela()
            self.toast("📅 Fechas y horas guardadas")

    def foto_general_desde_portada(self, hid):
        """La foto de «General» es la portada de la novela (con su mismo encuadre).
        Solo se aplica si «General» aún no tiene foto: nunca pisa una foto que tú hayas puesto."""
        fila = self.conn.execute("SELECT foto FROM heroinas WHERE id = ?", (hid,)).fetchone()
        if fila and fila[0] and Path(fila[0]).exists():
            return
        j = self.conn.execute(
            "SELECT portada, portada_enc FROM juegos WHERE id = ?", (self.juego_id,)).fetchone()
        if not j or not j[0] or not Path(j[0]).exists():
            return
        try:
            ruta = copiar_asset(j[0], "heroinas", f"h_{hid}")
        except OSError:
            return
        self.conn.execute("UPDATE heroinas SET foto = ?, foto_enc = ? WHERE id = ?",
                          (ruta, j[1] or "1,0,0", hid))
        self.conn.commit()

    def asegurar_general(self):
        fila = self.conn.execute(
            "SELECT id FROM heroinas WHERE juego_id = ? AND nombre = 'General'",
            (self.juego_id,)).fetchone()
        if fila:
            hid = fila[0]
        else:
            hid = self.conn.execute(
                "INSERT INTO heroinas(juego_id, nombre) VALUES (?, 'General')",
                (self.juego_id,)).lastrowid
        self.conn.execute(
            "UPDATE imagenes SET heroina_id = ? WHERE juego_id = ? AND heroina_id IS NULL",
            (hid, self.juego_id))
        self.conn.commit()
        preparar_carpetas_heroina(self.juego_carpeta, "General")
        self.foto_general_desde_portada(hid)
        return hid

    def importar_heroina(self):
        """Copia heroínas (foto, cumpleaños, seiyuu, altura y medidas...) de otras novelas."""
        if self.juego_id is None:
            return
        filas = self.conn.execute("""
            SELECT h.nombre, h.foto, h.foto_enc, h.altura, h.cumple, h.seiyuu,
                   h.vndb_id, h.info, j.nombre, h.tipo, h.busto, h.cintura, h.cadera, h.apodos
            FROM heroinas h JOIN juegos j ON j.id = h.juego_id
            WHERE h.juego_id <> ? AND h.nombre <> 'General'
            ORDER BY j.orden, j.nombre COLLATE NOCASE, h.orden, h.id
        """, (self.juego_id,)).fetchall()
        ya = {clave_heroina(r[0]) for r in self.conn.execute(
            "SELECT nombre FROM heroinas WHERE juego_id = ?", (self.juego_id,))}
        grupos = {}
        for n, fo, e, alt, cu, cv, vid, info, jn, tp, bu, ci, ca, ap in filas:
            k = clave_heroina(n)
            if k in ya:
                continue
            g = grupos.get(k)
            if g is None:
                grupos[k] = dict(nombre=n, foto=fo, enc=e, altura=alt, busto=bu, cintura=ci,
                                 cadera=ca, cumple=cu, seiyuu=cv, vndb=vid, info=info,
                                 novelas=[jn], tipo=tp or "heroina", apodos=ap or "")
                continue
            # si la heroína está en varias novelas, se completa con lo que falte
            for campo, val in (("foto", fo), ("altura", alt), ("cumple", cu), ("seiyuu", cv),
                               ("vndb", vid), ("info", info), ("apodos", ap)):
                if not g[campo] and val:
                    g[campo] = val
                    if campo == "foto":
                        g["enc"] = e
            if not medidas_completas(g["busto"], g["cintura"], g["cadera"]) \
                    and medidas_completas(bu, ci, ca):
                g["busto"], g["cintura"], g["cadera"] = bu, ci, ca
            if jn not in g["novelas"]:
                g["novelas"].append(jn)
        if not grupos:
            QMessageBox.information(
                self, "Importar heroína",
                "No hay heroínas de otras novelas que puedas importar "
                "(o ya tienes todas en esta novela).")
            return
        cand = sorted(grupos.values(), key=lambda g: g["nombre"].casefold())
        dlg = DialogoImportarHeroina(self, cand, self.juego_nombre)
        if not dlg.exec():
            return
        elegidas = dlg.elegidas()
        if not elegidas:
            return
        creadas, ultimo = 0, None
        for g in elegidas:
            try:
                hid = self.conn.execute(
                    "INSERT INTO heroinas(juego_id, nombre, altura, busto, cintura, cadera, "
                    "cumple, seiyuu, vndb_id, info, tipo, apodos) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.juego_id, g["nombre"], g["altura"] or 0, g["busto"] or 0,
                     g["cintura"] or 0, g["cadera"] or 0, g["cumple"] or "",
                     g["seiyuu"] or "", g["vndb"] or "", g["info"] or "",
                     g["tipo"], g["apodos"] or "")).lastrowid
            except sqlite3.IntegrityError:
                continue
            self.conn.execute(
                "UPDATE heroinas SET orden = (SELECT COALESCE(MAX(orden), 0) + 1 "
                "FROM heroinas WHERE juego_id = ?) WHERE id = ?", (self.juego_id, hid))
            if g["foto"] and Path(g["foto"]).exists():
                ruta = copiar_asset(g["foto"], "heroinas", f"h_{hid}")
                self.conn.execute("UPDATE heroinas SET foto = ?, foto_enc = ? WHERE id = ?",
                                  (ruta, g["enc"] or "1,0,0", hid))
            if g["tipo"] != "secundaria":
                preparar_carpetas_heroina(self.juego_carpeta, g["nombre"])
            creadas += 1
            ultimo = hid
        self.conn.commit()
        self.cargar_heroinas(ultimo)
        self.toast(f"⇩ {creadas} {'heroína importada' if creadas == 1 else 'heroínas importadas'}")

    def pedir_primera_heroina(self):
        hay_otras = self.conn.execute(
            "SELECT 1 FROM heroinas WHERE juego_id <> ? AND nombre <> 'General' LIMIT 1",
            (self.juego_id,)).fetchone()
        if hay_otras and QMessageBox.question(
                self, "Heroínas",
                "Esta novela aún no tiene heroínas.\n\n¿Es una secuela o comparte heroínas con "
                "otra novela? Puedes importarlas sin escribir sus datos otra vez."
        ) == QMessageBox.StandardButton.Yes:
            self.importar_heroina()
            if self.total_personajes():
                return
        dlg = DialogoTarjeta(
            self, "¿Quién es la heroína?", "Nombre de la heroína:",
            mostrar_general=True, invertir=True,
            info="Pon el nombre y su foto. Si la novela no tiene heroínas, "
                 "usa «General» y una imagen cualquiera.")
        if dlg.exec():
            hid = self.crear_heroina(dlg.nombre(), dlg.imagen, dlg.encuadre)
        else:
            hid = self.crear_heroina("General", "")
        self.cargar_heroinas(hid)

    def crear_heroina(self, nombre, foto, enc=None, tipo="heroina"):
        try:
            hid = self.conn.execute(
                "INSERT INTO heroinas(juego_id, nombre, tipo) VALUES (?, ?, ?)",
                (self.juego_id, nombre, tipo)).lastrowid
        except sqlite3.IntegrityError:
            QMessageBox.information(self, "Ya existe", "Esa heroína ya existe en esta novela.")
            return self.conn.execute(
                "SELECT id FROM heroinas WHERE juego_id = ? AND nombre = ?",
                (self.juego_id, nombre)).fetchone()[0]
        self.conn.execute(
            "UPDATE heroinas SET orden = (SELECT COALESCE(MAX(orden), 0) + 1 "
            "FROM heroinas WHERE juego_id = ?) WHERE id = ?", (self.juego_id, hid))
        if foto:
            ruta = copiar_asset(foto, "heroinas", f"h_{hid}")
            self.conn.execute("UPDATE heroinas SET foto = ?, foto_enc = ? WHERE id = ?",
                              (ruta, fmt_enc(enc or ENC0), hid))
        if nombre == "General":
            self.conn.execute(
                "UPDATE imagenes SET heroina_id = ? WHERE juego_id = ? AND heroina_id IS NULL",
                (hid, self.juego_id))
        self.conn.commit()
        if nombre == "General":
            self.foto_general_desde_portada(hid)
        if tipo != "secundaria":                    # los secundarios no tienen capturas
            preparar_carpetas_heroina(self.juego_carpeta, nombre)
        return hid

    def nueva_heroina(self, tipo="heroina"):
        if self.juego_id is None:
            return
        titulo, etiqueta = {
            "heroina": ("Nueva heroína", "Nombre de la heroína:"),
            "sub": ("Nueva sub-heroína", "Nombre de la sub-heroína:"),
            "secundaria": ("Nuevo personaje secundario", "Nombre del personaje:"),
        }[tipo]
        info = {"sub": "Una sub-heroína funciona como una heroína (tiene sus capturas) pero va "
                       "en su propia lista.",
                "secundaria": "Los personajes secundarios son solo para la vista: no tienen "
                              "capturas. Su cumpleaños y seiyuu los puedes guardar después con «Editar información»."
                }.get(tipo, "")
        dlg = DialogoTarjeta(self, titulo, etiqueta, mostrar_general=(tipo == "heroina"),
                             invertir=True, info=info)
        if dlg.exec():
            hid = self.crear_heroina(dlg.nombre(), dlg.imagen, dlg.encuadre, tipo)
            dlg.deleteLater()
            # se recarga cuando ya terminó el clic del botón: así no se borran las listas
            # (ni sus elementos) mientras Qt todavía está dentro de ese mismo clic
            QTimer.singleShot(0, lambda h=hid: self.cargar_heroinas(h))

    def total_personajes(self):
        return sum(l.count() for l in self.listas_pers)

    def cargar_heroinas(self, seleccionar=None):
        previo = seleccionar or self.heroina_id or self._pers_id
        destino = {"heroina": self.lista_heroinas, "sub": self.lista_subs,
                   "secundaria": self.lista_secundarias}
        for l in self.listas_pers:
            l.blockSignals(True)
            l.clear()
        filas = self.conn.execute(
            "SELECT id, nombre, foto, foto_enc, altura, cumple, seiyuu, tipo, busto, cintura, "
            "cadera, apodos FROM heroinas "
            "WHERE juego_id = ? ORDER BY orden, nombre COLLATE NOCASE",
            (self.juego_id,)).fetchall()
        elegido = None
        for hid, nombre, foto, enc_txt, alt, cumple, seiyuu, tipo, bus, cin, cad, apodos in filas:
            lista = destino.get(tipo, self.lista_heroinas)
            enc = parse_enc(enc_txt)
            it = QListWidgetItem(nombre)
            it.setData(Qt.ItemDataRole.UserRole,
                       {"id": hid, "nombre": nombre, "foto": foto, "enc": enc,
                        "altura": alt or 0, "busto": bus or 0, "cintura": cin or 0,
                        "cadera": cad or 0, "cumple": cumple or "", "seiyuu": seiyuu or "",
                        "tipo": tipo or "heroina", "apodos": apodos or ""})
            it.setSizeHint(QSize(100, 64))
            lista.addItem(it)
            if hid == previo:
                elegido = (lista, it)
        if elegido is None:
            for l in self.listas_pers:
                if l.count():
                    elegido = (l, l.item(0))
                    break
        for l in self.listas_pers:
            l.setCurrentRow(-1)
        if elegido:
            elegido[0].setCurrentItem(elegido[1])
            self._lista_pers = elegido[0]
        for l in self.listas_pers:
            l.blockSignals(False)
        for lista_p, etq in self._cuentas:
            etq.setText(str(lista_p.count()))
        self.ajustar_listas_pers()
        self.al_cambiar_heroina(elegido[1] if elegido else None)
        if self.tabs_juego.currentIndex() == self.IDX_TOP:
            self.cargar_top()

    def _leer_orden_paneles(self):
        base = ["heroina", "sub", "secundaria"]
        try:
            f = self.conn.execute(
                "SELECT valor FROM ajustes WHERE clave = 'orden_paneles'").fetchone()
            orden = f[0].split(",") if f else []
        except Exception:
            orden = []
        return orden if sorted(orden) == sorted(base) else base

    def _actualizar_flechas(self):
        o = self._orden_paneles
        for t, (arriba, abajo) in self._flechas.items():
            arriba.setEnabled(o.index(t) > 0)
            abajo.setEnabled(o.index(t) < len(o) - 1)

    COLAPSADO = 46      # altura de un panel vacío (solo título y botones)

    def _lista_de(self, tipo):
        return {"heroina": self.lista_heroinas, "sub": self.lista_subs,
                "secundaria": self.lista_secundarias}[tipo]

    def mover_grupo(self, tipo, paso):
        """Sube o baja el panel de Heroínas / Sub-heroínas / Secundarios (se recuerda)."""
        o = self._orden_paneles
        i = o.index(tipo)
        j = i + paso
        if not 0 <= j < len(o):
            return
        o[i], o[j] = o[j], o[i]
        for k, t in enumerate(o):
            self._split_pers.insertWidget(k, self._cajas_pers[t])
        guardar_ajuste(self.conn, "orden_paneles", ",".join(o))
        self._actualizar_flechas()
        self.repartir_paneles()

    def ajustar_listas_pers(self, arrastrando=False):
        """Un panel vacío se pliega a una franja mínima (solo título y botones). Mientras
        arrastras un personaje se despliegan todos para poder soltarlo en cualquiera."""
        alto = DelegadoPersonaje.ALTO
        for tipo in self._orden_paneles:
            lista, caja = self._lista_de(tipo), self._cajas_pers[tipo]
            n = lista.count()
            vacio = n == 0 and not arrastrando
            lay = caja.layout()
            lista.setVisible(not vacio)
            if vacio:
                lay.setContentsMargins(14, 5, 14, 5)
                lay.setSpacing(0)
                caja.setFixedHeight(self.COLAPSADO)
            else:
                lay.setContentsMargins(14, 12, 14, 14)
                lay.setSpacing(10)
                lista.setMinimumHeight(alto + 6 if n else 44)
                lista.setMaximumHeight(16777215)
                caja.setMinimumHeight(0)
                caja.setMaximumHeight(16777215)
        self.repartir_paneles(arrastrando)

    @staticmethod
    def _reparto_auto(deseos, disponible):
        """Cada panel recibe lo que necesita; si no alcanza, el espacio se reparte parejo
        y lo que un panel no usa pasa a los demás (los que tienen más personajes)."""
        res, pend, resto = {}, dict(deseos), float(disponible)
        while pend:
            parte = resto / len(pend)
            listos = [t for t, d in pend.items() if d <= parte]
            if not listos:
                for t in pend:
                    res[t] = parte
                break
            for t in listos:
                res[t] = pend.pop(t)
                resto -= res[t]
        return res

    def _leer_reparto_paneles(self):
        if self.juego_id is None:
            return {}
        f = self.conn.execute("SELECT valor FROM ajustes WHERE clave = ?",
                              (f"paneles_{self.juego_id}",)).fetchone()
        out = {}
        for par in (f[0].split(",") if f and f[0] else []):
            try:
                k, v = par.split(":")
                out[k] = float(v)
            except ValueError:
                continue
        return out

    def repartir_paneles(self, arrastrando=False):
        """Reparte la altura entre los paneles: usa el tamaño que estiraste en ESTA novela
        o, si nunca lo tocaste, se adapta solo a la cantidad de personajes de cada uno."""
        sp = self._split_pers
        alto_total = sp.height()
        if alto_total < 120:
            sp.pendiente = True             # se reintenta cuando el panel ya tiene tamaño
            return
        sp.pendiente = False
        alto, cab = DelegadoPersonaje.ALTO, 72
        fijo, deseos = 0, {}
        for t in self._orden_paneles:
            n = self._lista_de(t).count()
            if n == 0 and not arrastrando:
                fijo += self.COLAPSADO
            else:
                deseos[t] = cab + (n * alto if n else 44) + 6
        manijas = sp.handleWidth() * (sp.count() - 1)
        libre = max(0, alto_total - fijo - manijas)
        guardado = {} if arrastrando else self._leer_reparto_paneles()
        if deseos and all(t in guardado for t in deseos):
            tam = {t: max(cab + alto + 6, guardado[t] * alto_total) for t in deseos}
            tot = sum(tam.values())
            if tot > libre:
                tam = {t: v * libre / tot for t, v in tam.items()}
        else:
            tam = self._reparto_auto(deseos, libre)
        sizes = [tam.get(t, self.COLAPSADO) for t in self._orden_paneles]
        sizes.append(max(0, alto_total - manijas - sum(sizes)))
        sp.setSizes([int(s) for s in sizes])

    def guardar_reparto_paneles(self):
        """Guarda lo que estiraste (por novela)."""
        sp = self._split_pers
        if self.juego_id is None or sp.height() < 120:
            return
        sizes = sp.sizes()
        pares = [f"{t}:{sizes[k] / sp.height():.4f}"
                 for k, t in enumerate(self._orden_paneles) if self._lista_de(t).count() > 0]
        guardar_ajuste(self.conn, f"paneles_{self.juego_id}", ",".join(pares))

    def restablecer_reparto_paneles(self):
        """Doble clic en un asa: olvida lo estirado y vuelve al reparto automático."""
        if self.juego_id is not None:
            guardar_ajuste(self.conn, f"paneles_{self.juego_id}", "")
        self.repartir_paneles()
        self.toast("↕ Paneles repartidos automáticamente")

    def al_seleccionar_personaje(self, lista, actual):
        """Se eligió alguien en una de las tres listas: las otras dejan de tener selección."""
        if actual is None:
            return
        for l in self.listas_pers:
            if l is not lista and l.currentRow() >= 0:
                l.blockSignals(True)
                l.clearSelection()
                l.setCurrentRow(-1)
                l.blockSignals(False)
        self._lista_pers = lista
        self.al_cambiar_heroina(actual)

    def mover_personaje(self, pid, tipo_destino, fila):
        """Arrastraste un icono de una lista a otra: cambia su tipo."""
        f = self.conn.execute("SELECT nombre, tipo, juego_id FROM heroinas WHERE id = ?",
                              (pid,)).fetchone()
        if not f:
            return
        nombre, tipo_old, jid = f
        if nombre == "General":
            self.toast("«General» no se puede mover de lista")
            return
        if tipo_old == tipo_destino:
            return
        if tipo_destino == "secundaria":
            n = self.conn.execute("SELECT COUNT(*) FROM imagenes WHERE heroina_id = ?",
                                  (pid,)).fetchone()[0]
            if n:
                QMessageBox.information(
                    self, "Tiene capturas",
                    f"{nombre} tiene {n} {'captura' if n == 1 else 'capturas'}. Los personajes "
                    "secundarios son solo de vista (sin capturas).\n\nMueve primero sus capturas "
                    "a otra heroína, o déjala como sub-heroína.")
                return
        self.conn.execute("UPDATE heroinas SET tipo = ? WHERE id = ?", (tipo_destino, pid))
        ids = [r[0] for r in self.conn.execute(
            "SELECT id FROM heroinas WHERE juego_id = ? AND tipo = ? AND id <> ? "
            "ORDER BY orden, nombre COLLATE NOCASE", (jid, tipo_destino, pid))]
        ids.insert(max(0, min(fila, len(ids))), pid)
        for pos, h in enumerate(ids, 1):
            self.conn.execute("UPDATE heroinas SET orden = ? WHERE id = ?", (pos, h))
        self.conn.commit()
        etiqueta = {"heroina": "heroína", "sub": "sub-heroína",
                    "secundaria": "personaje secundario"}[tipo_destino]

        def terminar():
            self.cargar_heroinas(pid)
            self.toast(f"↔ {nombre} ahora es {etiqueta}")
        QTimer.singleShot(150, terminar)        # tras terminar el arrastre

    # -----------------------------------------------------
    # INFORMACIÓN DE LA HEROÍNA (cumpleaños, seiyuu, altura y medidas)
    # -----------------------------------------------------

    def refrescar_info_heroina(self, d):
        if not hasattr(self, "ficha"):
            return
        es_heroina = bool(d) and d["nombre"] != "General"
        self.b_info.setVisible(es_heroina)
        self.ficha.setVisible(es_heroina)
        if es_heroina:                  # «General» no es una heroína: no se muestra nada
            self.ficha.poner(d)

    def editar_info_heroina(self, *_):
        d = self.heroina_actual_datos()
        if not d:
            self.toast("Selecciona una heroína primero")
            return
        if d["nombre"] == "General":
            self.toast("«General» no es una heroína: no tiene ficha")
            return
        sugerencias = sorted({r[0] for r in self.conn.execute(
            "SELECT DISTINCT seiyuu FROM heroinas WHERE TRIM(seiyuu) <> ''")},
            key=str.casefold)
        dlg = DialogoInfoHeroina(self, d["nombre"], d.get("cumple", ""), d.get("seiyuu", ""),
                                 sugerencias, d.get("altura", 0), d.get("busto", 0),
                                 d.get("cintura", 0), d.get("cadera", 0), d.get("apodos", ""))
        if not dlg.exec():
            return
        cumple, cv, alt, bus, cin, cad, apodos = dlg.valores()
        self.conn.execute(
            "UPDATE heroinas SET cumple = ?, seiyuu = ?, altura = ?, busto = ?, cintura = ?, "
            "cadera = ?, apodos = ? WHERE id = ?", (cumple, cv, alt, bus, cin, cad, apodos, d["id"]))
        self.conn.commit()
        self.cargar_heroinas(d["id"])
        self.toast(f"✿ Información de «{d['nombre']}» guardada")

    # -----------------------------------------------------
    # TOP HEROÍNAS
    # -----------------------------------------------------

    def _tarjeta_dato(self, icono, titulo):
        f = QFrame()
        f.setObjectName("panel")
        l = QVBoxLayout(f)
        l.setContentsMargins(14, 8, 14, 8)
        l.setSpacing(0)
        cap = QLabel(f"{icono}  {titulo}")
        cap.setObjectName("muted")
        val = QLabel("—")
        val.setObjectName("heading")
        l.addWidget(cap)
        l.addWidget(val)
        return f, val

    def _fila_datos(self, definiciones):
        fila = QHBoxLayout()
        fila.setSpacing(10)
        labels = []
        for icono, titulo in definiciones:
            f, val = self._tarjeta_dato(icono, titulo)
            fila.addWidget(f, 1)
            labels.append(val)
        return fila, labels

    @staticmethod
    def _poner_datos(labels, items):
        lider = items[0]["nombre"] if items else "—"
        labels[0].setText(str(len(items)))
        labels[1].setText(str(sum(i["capturas"] for i in items)))
        labels[2].setText(str(sum(i["favs"] for i in items)))
        labels[3].setText(lider if len(lider) <= 22 else lider[:21] + "…")
        labels[3].setToolTip(lider)
        if len(labels) > 5:
            def corto(t, n=24):
                return t if len(t) <= n else t[:n - 1] + "…"
            cum = sorted((i for i in items if i.get("dias") is not None),
                         key=lambda i: i["dias"])
            if cum:
                c = cum[0]
                labels[4].setText(corto("¡Hoy! " + c["nombre"] if c["dias"] == 0
                                        else f"{c['nombre']} · {c['dias']} d"))
            else:
                labels[4].setText("—")
            act = max(items, key=lambda i: i["capturas"], default=None)
            labels[5].setText(corto(f"{act['nombre']} · {act['capturas']}") if act else "—")

    def normalizar_tops(self):
        """Da un puesto fijo a las heroínas que aún no lo tienen (las nuevas van al final).
        Se hace UNA vez con la foto actual; después el top ya no depende del orden de la
        galería: solo cambia cuando tú lo arrastras."""
        c = self.conn
        for (jid,) in c.execute("SELECT DISTINCT juego_id FROM heroinas "
                                "WHERE nombre <> 'General' AND top_pos = 0").fetchall():
            mx = c.execute("SELECT COALESCE(MAX(top_pos), 0) FROM heroinas "
                           "WHERE juego_id = ? AND nombre <> 'General'", (jid,)).fetchone()[0]
            for (hid,) in c.execute(
                    "SELECT id FROM heroinas WHERE juego_id = ? AND nombre <> 'General' "
                    "AND top_pos = 0 ORDER BY CASE tipo WHEN 'heroina' THEN 0 "
                    "WHEN 'sub' THEN 1 ELSE 2 END, orden, id", (jid,)).fetchall():
                mx += 1
                c.execute("UPDATE heroinas SET top_pos = ? WHERE id = ?", (mx, hid))
        mx = c.execute("SELECT COALESCE(MAX(top_global), 0) FROM heroinas "
                       "WHERE nombre <> 'General'").fetchone()[0]
        for (hid,) in c.execute(
                "SELECT h.id FROM heroinas h JOIN juegos j ON j.id = h.juego_id "
                "WHERE h.nombre <> 'General' AND h.tipo = 'heroina' AND h.top_global = 0 "
                "ORDER BY h.top_pos, j.orden, h.id").fetchall():
            mx += 1
            c.execute("UPDATE heroinas SET top_global = ? WHERE id = ?", (mx, hid))
        c.commit()

    # ---------- top de una novela

    def construir_top(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(10)
        cab = QHBoxLayout()
        self.lbl_top = QLabel("🏆 Top Heroínas")
        self.lbl_top.setObjectName("heading")
        cab.addWidget(self.lbl_top, 1)
        self.btn_duelos_top = BotonAnimado("⚔ Duelos de heroínas  ▾", primario=True)
        self.btn_duelos_top.clicked.connect(lambda: self.menu_duelos_heroinas("novela"))
        self.chk_hall = QCheckBox("👑 Participa en Heroínas de heroínas")
        self.chk_hall.toggled.connect(
            lambda marcado: self.fijar_participacion_hall(self.juego_id, marcado))
        self.chk_solo_camp = QCheckBox("🥇 Solo la campeona pasa")
        self.chk_solo_camp.setToolTip(
            "Marcado: de esta novela solo la campeona (1.º del top) entra a «Heroínas de "
            "heroínas».\nDesmarcado: pasan la campeona y la subcampeona.")
        self.chk_solo_camp.toggled.connect(
            lambda marcado: self.fijar_solo_campeona(self.juego_id, marcado))
        cab.addWidget(self.chk_solo_camp)
        cab.addWidget(self.chk_hall)
        cab.addWidget(self.btn_duelos_top)
        v.addLayout(cab)
        self.lbl_top_sub = QLabel("")
        self.lbl_top_sub.setObjectName("muted")
        self.lbl_top_sub.setWordWrap(True)
        v.addWidget(self.lbl_top_sub)
        fila, self.datos_top = self._fila_datos(
            (("💗", "Heroínas"), ("🖼", "Capturas"), ("★", "Favoritas"), ("👑", "Líder"),
             ("🎂", "Próximo cumple"), ("📈", "Más activa")))
        v.addLayout(fila)
        self.top = TopHeroinas()
        self.scroll_top = QScrollArea()
        self.scroll_top.setWidgetResizable(True)
        self.scroll_top.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_top.setWidget(self.top)
        self.top.scroll = self.scroll_top
        self.top.orden_cambiado.connect(self.guardar_top)
        self.top.abrir.connect(self.abrir_heroina_desde_top)
        v.addWidget(self.scroll_top, 1)
        return w

    def cargar_top(self):
        if not hasattr(self, "top") or self.juego_id is None:
            return
        self.normalizar_tops()
        filas = self.conn.execute("""
            SELECT h.id, h.nombre, h.foto, h.foto_enc, h.seiyuu, h.altura, h.cumple,
                   (SELECT COUNT(*) FROM imagenes i WHERE i.heroina_id = h.id),
                   (SELECT COUNT(*) FROM imagenes i
                     WHERE i.heroina_id = h.id AND i.favorito = 1),
                   h.tipo, h.busto, h.cintura, h.cadera
            FROM heroinas h
            WHERE h.juego_id = ? AND h.nombre <> 'General'
            ORDER BY h.top_pos, h.id
        """, (self.juego_id,)).fetchall()
        cats, thumbs, thumbs_fila = self.extras_heroinas([f[0] for f in filas])
        marca = {"sub": "✧ ", "secundaria": "☆ "}        # mismo símbolo que su panel
        items = [dict(id=i, nombre=marca.get(tp, "") + n, foto=f, enc=parse_enc(e),
                      seiyuu=s or "", altura=alt or 0, busto=bu or 0, cintura=ci or 0,
                      cadera=ca or 0, cumple=cu or "", capturas=c, favs=fv,
                      cats=cats[i], thumbs=thumbs[i], thumb_fila=thumbs_fila[i], tipo=tp)
                 for i, n, f, e, s, alt, cu, c, fv, tp, bu, ci, ca in filas]
        self.top.poner(items)
        self._poner_datos(self.datos_top, items)
        n = len(items)
        self.lbl_top.setText(f"🏆 Top Heroínas · {self.juego_nombre}")
        ex = self.conn.execute("SELECT excluir_hall FROM juegos WHERE id = ?",
                               (self.juego_id,)).fetchone()
        self.chk_hall.blockSignals(True)
        self.chk_hall.setChecked(not (ex and ex[0]))
        self.chk_hall.blockSignals(False)
        sc = self.conn.execute("SELECT solo_campeona FROM juegos WHERE id = ?",
                               (self.juego_id,)).fetchone()
        self.chk_solo_camp.blockSignals(True)
        self.chk_solo_camp.setChecked(bool(sc and sc[0]))
        self.chk_solo_camp.blockSignals(False)
        cuenta = {t: sum(1 for i in items if i["tipo"] == t)
                  for t in ("heroina", "sub", "secundaria")}
        partes = [f"{cuenta['heroina']} {'heroína' if cuenta['heroina'] == 1 else 'heroínas'}"
                  if cuenta["heroina"] else "",
                  f"{cuenta['sub']} {'sub-heroína' if cuenta['sub'] == 1 else 'sub-heroínas'}"
                  if cuenta["sub"] else "",
                  f"{cuenta['secundaria']} "
                  f"{'secundario' if cuenta['secundaria'] == 1 else 'secundarios'}"
                  if cuenta["secundaria"] else ""]
        txt = (f"{n} personajes compiten por el podio · " + " · ".join(p for p in partes if p)
               ) if n else ""
        self.lbl_top_sub.setText(txt)

    def guardar_top(self, ids):
        for pos, hid in enumerate(ids, 1):
            self.conn.execute("UPDATE heroinas SET top_pos = ? WHERE id = ?", (pos, hid))
        self.conn.commit()
        fila = self.conn.execute("SELECT nombre FROM heroinas WHERE id = ?",
                                 (ids[0],)).fetchone()
        self._poner_datos(self.datos_top, [self.top.items[i] for i in ids])
        self.toast(f"🏆 Top guardado · 👑 {fila[0]} lidera el podio" if fila
                   else "🏆 Top guardado")

    # -----------------------------------------------------
    # INFO HEROÍNAS: cumpleaños globales y seiyuus compartidas
    # -----------------------------------------------------

    def construir_info_heroinas(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)
        fila = QHBoxLayout()
        volver = BotonAnimado("← Biblioteca")
        volver.clicked.connect(self.volver_biblioteca)
        fila.addWidget(volver)
        col = QVBoxLayout()
        t = QLabel("🎂 Información de heroínas")
        t.setObjectName("heading")
        self.lbl_info_h = QLabel("")
        self.lbl_info_h.setObjectName("muted")
        self.lbl_info_h.setWordWrap(True)
        col.addWidget(t)
        col.addWidget(self.lbl_info_h)
        fila.addLayout(col, 1)
        self.b_clasif_h = BotonAnimado("💗 Clasificar H")
        self.b_clasif_h.setAutoDefault(False)
        self.b_clasif_h.setToolTip(
            "Pasa por las fotos de las heroínas que aún no clasificaste: ¿tiene escenas H "
            "(eroge)? Sí / No. Las ya clasificadas no vuelven a salir.")
        self.b_clasif_h.clicked.connect(self.clasificar_heroinas_h)
        fila.addWidget(self.b_clasif_h)
        self.b_corregir_h = BotonAnimado("✎ Corregir H")
        self.b_corregir_h.setAutoDefault(False)
        self.b_corregir_h.setToolTip(
            "Escribe el nombre de una heroína y cambia si tiene escenas H o no.")
        self.b_corregir_h.clicked.connect(self.corregir_heroina_h)
        fila.addWidget(self.b_corregir_h)
        v.addLayout(fila)

        self._nombres_seiyuu = {}
        self._azar_seiyuus = {}
        self._info_cargada = set()            # pestañas ya cargadas: cada una se carga SOLO al abrirla
        self._lista_cumples, self._comparten, self._sin_dia_cumples = [], {}, 0
        self._mes_cumple = 0
        self._grupos_seiyuu = []
        self.modo_seiyuu = "azar"
        self.tabs_info = QTabWidget()
        self.tabs_info.setDocumentMode(True)
        self.tabs_info.addTab(self.construir_pagina_cumples(), "🎂 Cumpleaños")
        self.tabs_info.addTab(self.construir_pagina_seiyuus(), "🎙 Seiyuus")
        self.tabs_info.addTab(self.construir_medidas(), "📏 Altura y medidas")
        self.tabs_info.currentChanged.connect(self._info_tab_cambiada)
        v.addWidget(self.tabs_info, 1)
        return w

    # ---------- pestaña «Cumpleaños»

    def construir_pagina_cumples(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(10)
        self.banner_cumple = BannerCumple()
        self.banner_cumple.abrir.connect(self.abrir_heroina_desde_hall)
        v.addWidget(self.banner_cumple)

        self.fila_fiesta = QWidget()               # solo aparece cuando HOY es un cumpleaños
        h = QHBoxLayout(self.fila_fiesta)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        self.b_celebrar = BotonAnimado("🎉 ¡Celebrar!", primario=True)
        self.b_regalo = BotonAnimado("🎁 Otro regalo")
        self.b_ver_cumple = BotonAnimado("🖼 Ver su galería")
        self.b_sig_cumple = BotonAnimado("💞 Siguiente cumpleañera")
        for b in (self.b_celebrar, self.b_regalo, self.b_ver_cumple, self.b_sig_cumple):
            b.setAutoDefault(False)
            h.addWidget(b)
        h.addStretch()
        self.b_celebrar.clicked.connect(self.banner_cumple.celebrar)
        self.b_regalo.clicked.connect(self._otro_regalo)
        self.b_ver_cumple.clicked.connect(self._ver_cumpleanera)
        self.b_sig_cumple.clicked.connect(self._siguiente_cumpleanera)
        self.fila_fiesta.hide()
        v.addWidget(self.fila_fiesta)


        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.c_mes_cumple = QComboBox()                # desplegable de meses (ocupa casi nada)
        self.c_mes_cumple.setMinimumWidth(240)
        self.c_mes_cumple.addItem("📅  Todos los meses")
        self.c_mes_cumple.currentIndexChanged.connect(self._filtrar_cumples_mes)
        fila.addWidget(self.c_mes_cumple)
        self.b_faltan_cumple = BotonAnimado("🎯 Solo las que faltan este año")
        self.b_faltan_cumple.setCheckable(True)
        self.b_faltan_cumple.setAutoDefault(False)
        self.b_faltan_cumple.setToolTip(
            "Oculta a las que ya cumplieron años este año. Con un mes elegido, muestra las "
            "que todavía no cumplen en ese mes.")
        self.b_faltan_cumple.toggled.connect(lambda *_: self._pintar_cumples())
        fila.addWidget(self.b_faltan_cumple)
        self.e_buscar_cumple = QLineEdit()
        self.e_buscar_cumple.setPlaceholderText("🔍  Buscar heroína o novela…")
        self.e_buscar_cumple.setClearButtonEnabled(True)
        self._t_busq_cumple = QTimer(self)
        self._t_busq_cumple.setSingleShot(True)
        self._t_busq_cumple.setInterval(220)
        self._t_busq_cumple.timeout.connect(self._pintar_cumples)
        self.e_buscar_cumple.textChanged.connect(lambda *_: self._t_busq_cumple.start())
        fila.addWidget(self.e_buscar_cumple, 1)
        self.lbl_cumples = QLabel("")
        self.lbl_cumples.setObjectName("muted")
        fila.addWidget(self.lbl_cumples)
        v.addLayout(fila)
        self.cont_cumples = ContenedorCuadricula(470)
        v.addWidget(self.cont_cumples, 1)
        return w

    def _datos_cumples(self):
        """Una entrada por heroína (aunque salga en varias novelas), con su próximo cumpleaños."""
        filas = self.conn.execute("""
            SELECT h.id, h.nombre, h.foto, h.foto_enc, h.cumple, j.nombre, h.seiyuu
            FROM heroinas h JOIN juegos j ON j.id = h.juego_id
            WHERE h.nombre <> 'General'
            ORDER BY j.orden, j.nombre COLLATE NOCASE, h.top_pos, h.id
        """).fetchall()
        grupos = {}
        for hid, n, fo, e, cu, jn, cv in filas:
            k = clave_heroina(n)
            g = grupos.get(k)
            if g is None:
                g = grupos[k] = dict(ids=[], id=hid, nombre=n, foto="", enc="", cumple="",
                                     dias=None, novelas=[], seiyuu="", con_texto=False)
            g["ids"].append(hid)
            if jn not in g["novelas"]:
                g["novelas"].append(jn)
            if not g["foto"] and fo:
                g["foto"], g["enc"] = fo, e
            if cv and cv.strip() and not g["seiyuu"]:
                g["seiyuu"] = " ".join(cv.split())
            if (cu or "").strip():
                g["con_texto"] = True
                if g["dias"] is None:
                    d = dias_para_cumple(cu)
                    if d is not None:
                        g["dias"], g["cumple"], g["id"] = d, cu.strip(), hid
        lista = [g for g in grupos.values() if g["dias"] is not None]
        sin_dia = sum(1 for g in grupos.values() if g["dias"] is None and g["con_texto"])
        lista.sort(key=lambda g: (g["dias"], g["nombre"].casefold()))
        comparten = {}
        for k, g in enumerate(lista, 1):
            m = re.match(r"\s*(\d{1,2}) de (\w+)", g["cumple"])
            g["dia_n"], g["mes"] = int(m.group(1)), MESES_ES.index(m.group(2).lower()) + 1
            g["zodiaco"] = signo_zodiaco(g["cumple"])
            g["rank"] = k
            comparten.setdefault((g["mes"], g["dia_n"]), []).append(g["nombre"])
        return lista, comparten, sin_dia

    def _regalo(self, ids, evitar=""):
        """Una captura (mejor si es favorita) de la heroína, como regalo de su cumpleaños."""
        q = ",".join("?" * len(ids))
        filas = self.conn.execute(
            f"SELECT ruta FROM imagenes WHERE heroina_id IN ({q}) "
            "ORDER BY favorito DESC, RANDOM() LIMIT 15", list(ids)).fetchall()
        rutas = [r[0] for r in filas if r[0] and Path(r[0]).exists()]
        if evitar and len(rutas) > 1:
            rutas = [r for r in rutas if r != evitar] or rutas
        for r in rutas[:1]:
            pm = CACHE_MINI.obtener(r, 360)
            if not pm.isNull():
                return pm, r
        return None, ""

    def _item_banner(self, g):
        q = ",".join("?" * len(g["ids"]))
        caps, favs = self.conn.execute(
            f"SELECT COUNT(*), COALESCE(SUM(favorito), 0) FROM imagenes "
            f"WHERE heroina_id IN ({q})", g["ids"]).fetchone()
        item = dict(id=g["id"], ids=g["ids"], nombre=g["nombre"],
                    pm=avatar(g["foto"], 280, parse_enc(g["enc"])), dias=g["dias"],
                    cumple=g["cumple"], zodiaco=g["zodiaco"], novelas=" · ".join(g["novelas"]),
                    caps=caps, favs=int(favs or 0), seiyuu=g["seiyuu"], regalo=None,
                    regalo_ruta="",
                    frase=FRASES_CUMPLE[(datetime.date.today().toordinal() + g["id"])
                                        % len(FRASES_CUMPLE)])
        if g["dias"] == 0:
            item["regalo"], item["regalo_ruta"] = self._regalo(g["ids"])
        return item

    def _cargar_cumples(self):
        lista, self._comparten, self._sin_dia_cumples = self._datos_cumples()
        self._lista_cumples = lista
        hoy = [g for g in lista if g["dias"] == 0]
        if hoy:
            elegidos = hoy
        elif lista:
            elegidos = [g for g in lista if g["dias"] == lista[0]["dias"]]
        else:
            elegidos = []
        self.banner_cumple.poner([self._item_banner(g) for g in elegidos[:6]])
        self._actualizar_fiesta()

        mes_hoy = datetime.date.today().month
        cuentas = [0] * 12
        for g in lista:
            cuentas[g["mes"] - 1] += 1
        signos = {}
        for g in lista:
            if g["zodiaco"]:
                signos[g["zodiaco"]] = signos.get(g["zodiaco"], 0) + 1
        top_signo = max(signos.items(), key=lambda kv: kv[1]) if signos else None
        gemelas = [ns for ns in self._comparten.values() if len(ns) > 1]
        self._llenar_meses(cuentas)
        self._pintar_cumples()

    def _fila_cumple(self, g):
        d = g["dias"]
        pill = ("¡HOY! 🎉" if d == 0 else "mañana" if d == 1 else f"en {d} días" if d < 100
                else f"en {round(d / 30.4)} meses")
        extra = []
        otros = [n for n in self._comparten.get((g["mes"], g["dia_n"]), []) if n != g["nombre"]]
        if otros:
            extra.append("💞 mismo día que " + ", ".join(otros[:2]))
        if g["seiyuu"]:
            extra.append("🎙 " + g["seiyuu"])
        t = TarjetaCumple(avatar(g["foto"], 200, parse_enc(g["enc"])), g, pill,
                          "  ·  ".join(extra))
        t.clic.connect(lambda hid=g["id"]: self.abrir_heroina_desde_hall(hid))
        return t

    def _pintar_cumples(self):
        if not hasattr(self, "cont_cumples"):
            return
        mes = self._mes_cumple
        filtro = self.e_buscar_cumple.text().casefold().strip()
        sel = []
        faltan = self.b_faltan_cumple.isChecked()
        hoy = datetime.date.today()
        for g in self._lista_cumples:
            if mes and g["mes"] != mes:
                continue
            if faltan and (hoy + datetime.timedelta(days=g["dias"])).year != hoy.year:
                continue                      # su próximo cumpleaños ya es el del año que viene
            if filtro and filtro not in g["nombre"].casefold() \
                    and not any(filtro in nv.casefold() for nv in g["novelas"]):
                continue
            sel.append(g)
        vacio = ("Ya cumplieron todas las de este filtro 🎂" if faltan
                 else "Nadie cumple años en ese filtro." if (mes or filtro)
                 else "Aún no hay cumpleaños.\nAñádelos con «✎ Editar información» en la "
                      "galería de cada heroína (día y mes).")
        self.cont_cumples.poner_por_partes(
            [(lambda g=g: self._fila_cumple(g)) for g in sel], vacio, 5)
        nombre_mes = MESES_ES[mes - 1] if mes else ""
        self.lbl_cumples.setText(
            f"{len(sel)} de {len(self._lista_cumples)}" + (f" · en {nombre_mes}" if mes else "")
            + (" · faltan por cumplir" if faltan else "")
            + "  ·  doble clic para abrir su galería")

    def _llenar_meses(self, cuentas):
        c = self.c_mes_cumple
        c.blockSignals(True)
        c.clear()
        c.addItem(f"📅  Todos los meses  ({sum(cuentas)})")
        hoy = datetime.date.today().month
        for i, nombre in enumerate(MESES_ES):
            c.addItem(f"{nombre.capitalize()}  ({cuentas[i]})"
                      + ("   ★ este mes" if i + 1 == hoy else ""))
        c.setCurrentIndex(self._mes_cumple)
        c.blockSignals(False)

    def _filtrar_cumples_mes(self, mes):
        self._mes_cumple = mes
        self._pintar_cumples()

    def _actualizar_fiesta(self):
        b = self.banner_cumple
        self.fila_fiesta.setVisible(b.hoy())
        self.b_sig_cumple.setVisible(len(b.items) > 1)
        self.b_regalo.setVisible(b.hoy())

    def _otro_regalo(self):
        a = self.banner_cumple.actual()
        if a and a["dias"] == 0:
            a["regalo"], a["regalo_ruta"] = self._regalo(a["ids"], a["regalo_ruta"])
            self.banner_cumple.update()

    def _siguiente_cumpleanera(self):
        self.banner_cumple.siguiente()

    def _ver_cumpleanera(self):
        a = self.banner_cumple.actual()
        if a:
            self.abrir_heroina_desde_hall(a["id"])

    # ---------- pestaña «Seiyuus»

    def construir_pagina_seiyuus(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(10)
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.e_buscar_seiyuu = QLineEdit()
        self.e_buscar_seiyuu.setPlaceholderText("🔍  Buscar seiyuu, heroína o novela…")
        self.e_buscar_seiyuu.setClearButtonEnabled(True)
        self._t_busq_seiyuu = QTimer(self)
        self._t_busq_seiyuu.setSingleShot(True)
        self._t_busq_seiyuu.setInterval(220)
        self._t_busq_seiyuu.timeout.connect(self._pintar_seiyuus)
        self.e_buscar_seiyuu.textChanged.connect(lambda *_: self._t_busq_seiyuu.start())
        fila.addWidget(self.e_buscar_seiyuu, 1)
        self.b_az_seiyuu = BotonAnimado("🔤 A-Z")
        self.b_az_seiyuu.setCheckable(True)
        self.b_az_seiyuu.setAutoDefault(False)
        self.b_az_seiyuu.toggled.connect(
            lambda on: self._orden_seiyuus("az" if on else "azar"))
        fila.addWidget(self.b_az_seiyuu)
        v.addLayout(fila)

        fila2 = QHBoxLayout()
        self.chk_seiyuu_todas = QCheckBox("Incluir también seiyuus con una sola heroína")
        self.chk_seiyuu_todas.toggled.connect(self._pintar_seiyuus)
        fila2.addWidget(self.chk_seiyuu_todas)
        fila2.addStretch()
        self.lbl_seiyuus = QLabel("")
        self.lbl_seiyuus.setObjectName("muted")
        fila2.addWidget(self.lbl_seiyuus)
        v.addLayout(fila2)
        self.cont_seiyuus = ContenedorCuadricula(780)
        v.addWidget(self.cont_seiyuus, 1)
        return w

    def _cargar_seiyuus(self):
        c = self.conn
        filas = c.execute("""
            SELECT h.id, h.nombre, h.foto, h.foto_enc, h.seiyuu, j.nombre,
                   h.altura, h.busto, h.cintura, h.cadera, h.cumple
            FROM heroinas h JOIN juegos j ON j.id = h.juego_id
            WHERE h.nombre <> 'General' AND TRIM(h.seiyuu) <> ''
            ORDER BY j.orden, j.nombre COLLATE NOCASE, h.top_pos, h.id
        """).fetchall()
        fotos = {r[0]: (r[1], r[2]) for r in c.execute(
            "SELECT clave, foto, foto_enc FROM seiyuus")}
        datos_s = {r[0]: (r[1] or "", lista_json(r[2]), r[3] or 0, r[4] or "")
                   for r in c.execute("SELECT clave, cumple, redes, anio, vndb FROM seiyuus")}
        h_clasif = {r[0]: r[1] for r in c.execute("SELECT clave, eroge FROM clasif_heroinas")}
        cuenta = dict(c.execute(
            "SELECT heroina_id, COUNT(*) FROM imagenes GROUP BY heroina_id").fetchall())
        grupos, vistas = {}, {}
        for hid, n, fo, e, cv, jn, alt, bu, ci, ca, cu in filas:
            clave = clave_seiyuu(cv)
            foto_s, enc_s = fotos.get(clave, ("", ""))
            cu_s, rd, an_s, vn_s = datos_s.get(clave, ("", [], 0, ""))
            g = grupos.setdefault(clave, dict(clave=clave, nombre=" ".join(cv.split()),
                                              foto=foto_s, enc=parse_enc(enc_s), heroinas=[],
                                              caps=0, corona=False, cumple=cu_s,
                                              anio=an_s, redes=rd, vndb=vn_s))
            previa = vistas.get((clave, clave_heroina(n)))
            if previa is None:
                previa = dict(id=hid, nombre=n, foto=fo, enc=parse_enc(e), juego="", _js=[jn],
                              caps=cuenta.get(hid, 0), altura=alt or 0, busto=bu or 0,
                              cintura=ci or 0, cadera=ca or 0, cumple=cu or "",
                              eroge=bool(h_clasif.get(clave_heroina(n))))
                vistas[(clave, clave_heroina(n))] = previa
                g["heroinas"].append(previa)
            else:
                previa["caps"] += cuenta.get(hid, 0)
                if not previa["foto"] and fo:
                    previa["foto"], previa["enc"] = fo, parse_enc(e)
                for campo, val in (("altura", alt), ("busto", bu), ("cintura", ci),
                                   ("cadera", ca), ("cumple", cu)):
                    if val and not previa[campo]:
                        previa[campo] = val
                if jn not in previa["_js"]:
                    previa["_js"].append(jn)
        for g in grupos.values():
            for h in g["heroinas"]:
                h["juego"] = " · ".join(h.pop("_js"))
            g["caps"] = sum(h["caps"] for h in g["heroinas"])
        varias = [g for g in grupos.values() if len(g["heroinas"]) >= 2]
        top = max(varias, key=lambda g: (len(g["heroinas"]), g["caps"])) if varias else None
        if top:
            top["corona"] = True
        self._grupos_seiyuu = list(grupos.values())
        self._nombres_seiyuu = {g["clave"]: g["nombre"] for g in grupos.values()}
        total_h = sum(len(g["heroinas"]) for g in grupos.values())
        self._pintar_seiyuus()

    def _orden_seiyuus(self, modo):
        self.modo_seiyuu = modo
        self._pintar_seiyuus()

    def _pintar_seiyuus(self, *_):
        if not hasattr(self, "cont_seiyuus"):
            return
        todas = self.chk_seiyuu_todas.isChecked()
        filtro = self.e_buscar_seiyuu.text().casefold().strip()
        elegidas = []
        for g in self._grupos_seiyuu:
            if not todas and len(g["heroinas"]) < 2:
                continue
            if filtro and filtro not in g["nombre"].casefold() and not any(
                    filtro in h["nombre"].casefold() or filtro in h["juego"].casefold()
                    for h in g["heroinas"]):
                continue
            elegidas.append(g)
        if self.modo_seiyuu == "az":
            elegidas.sort(key=lambda g: g["nombre"].casefold())
        else:
            for g in elegidas:                 # sorteo UNA vez al entrar a «Info heroínas»
                self._azar_seiyuus.setdefault(g["clave"], random.random())
            elegidas.sort(key=lambda g: self._azar_seiyuus[g["clave"]])

        def fabrica(g):
            def hacer():
                t = TarjetaSeiyuu(g)
                t.abrir.connect(self.abrir_heroina_desde_hall)
                t.cambiar_foto.connect(self.cambiar_foto_seiyuu)
                t.editar.connect(self.editar_datos_seiyuu)
                t.menu.connect(self.menu_seiyuu)
                return t
            return hacer
        self.cont_seiyuus.poner_por_partes(
            [fabrica(g) for g in elegidas],
            "Nada que mostrar con ese filtro." if filtro else
            "Aún no hay seiyuus que den voz a varias heroínas.", 8)
        self.lbl_seiyuus.setText(
            f"{len(elegidas)} mostradas · doble clic en una heroína abre su galería · "
            "doble clic en la foto la cambia · rosado con H = tiene escenas H")

    # ---------- carga por pestañas (cada una SOLO cuando se abre)

    def _info_tab_cambiada(self, i):
        if i not in self._info_cargada:
            QTimer.singleShot(0, lambda i=i: self._cargar_pestana_info(i))

    def _cargar_pestana_info(self, i):
        if i in self._info_cargada or self.pila.currentIndex() != 4:
            return
        self._info_cargada.add(i)
        try:
            if i == 0:
                self._cargar_cumples()
            elif i == 1:
                self._cargar_seiyuus()
            else:
                self.cargar_medidas()
        except Exception:
            registrar_error_ui(f"info_heroinas · pestaña {i}")
        self.lbl_info_h.setText("")

    def aviso_cumple_hoy(self):
        """Al abrir el programa: si hoy cumple años alguna heroína, un aviso con cariño."""
        try:
            hoy = {}
            for n, cu in self.conn.execute(
                    "SELECT nombre, cumple FROM heroinas "
                    "WHERE nombre <> 'General' AND TRIM(cumple) <> ''"):
                if dias_para_cumple(cu) == 0:
                    hoy.setdefault(clave_heroina(n), n)
            if hoy:
                nombres = list(hoy.values())
                quien = ", ".join(nombres[:3]) + (f" y {len(nombres) - 3} más"
                                                  if len(nombres) > 3 else "")
                self.toast(f"🎂🎉 ¡Hoy es el cumpleaños de {quien}!  Pásate por «Info heroínas»",
                           6500)
        except Exception:
            pass

    def construir_cronologia(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        fila = QHBoxLayout()
        volver = BotonAnimado("← Biblioteca")
        volver.clicked.connect(self.volver_biblioteca)
        fila.addWidget(volver)
        col = QVBoxLayout()
        t = QLabel("⏳ Cronología de mis novelas")
        t.setObjectName("heading")
        self.lbl_crono = QLabel("")
        self.lbl_crono.setObjectName("muted")
        col.addWidget(t)
        col.addWidget(self.lbl_crono)
        fila.addLayout(col, 1)
        v.addLayout(fila)
        def con_scroll(vista):
            sc = QScrollArea()
            sc.setWidgetResizable(True)
            sc.setFrameShape(QFrame.Shape.NoFrame)
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            sc.setWidget(vista)
            sc.viewport().setAutoFillBackground(False)
            vista.setAutoFillBackground(False)
            return sc
        self.vista_crono = CronologiaVista()
        self.vista_crono.abrir.connect(self.entrar_juego)
        self.vista_datos = DatosNovelasVista()
        self.vista_datos.abrir.connect(self.entrar_juego)
        self.tabs_crono = QTabWidget()
        self.tabs_crono.addTab(con_scroll(self.vista_crono), "⏳ Cronología")
        self.tabs_crono.addTab(con_scroll(self.vista_datos), "📊 Datos")
        v.addWidget(self.tabs_crono, 1)
        return w

    def abrir_cronologia(self):
        self.cargar_cronologia()
        self.ir_a_pagina(5)

    def cargar_cronologia(self, *_):
        if not hasattr(self, "vista_crono"):
            return
        base = self.conn.execute("""
            SELECT j.id, j.nombre, j.portada, j.portada_enc, j.horas, j.fecha_inicio, j.fecha_fin,
                   (SELECT COUNT(*) FROM imagenes i WHERE i.juego_id = j.id),
                   j.excluir_fechas, j.excluir_horas, j.nota
            FROM juegos j ORDER BY j.fecha_inicio, j.nombre COLLATE NOCASE
        """).fetchall()
        # Las novelas por volúmenes salen en la línea de tiempo una vez por volumen
        vols = {}
        for jv, vn, vi, vf, vh, vxf, vxh in self.conn.execute(
                "SELECT juego_id, nombre, fecha_inicio, fecha_fin, horas, excluir_fechas, "
                "excluir_horas FROM volumenes ORDER BY juego_id, orden, id"):
            vols.setdefault(jv, []).append((vn, vi, vf, vh, vxf, vxh))
        filas = []
        for f in base:
            if f[0] in vols:
                for vn, vi, vf, vh, vxf, vxh in vols[f[0]]:
                    filas.append((f[0], f"{f[1]} · {vn}" if vn else f[1], f[2], f[3],
                                  vh, vi, vf, 0, vxf, vxh, f[10]))
            else:
                filas.append(f)
        self.vista_crono.poner(filas)
        novelas = [dict(id=f[0], nombre=f[1], portada=f[2], enc=parse_enc(f[3]),
                        horas=0.0 if f[9] else float(f[4] or 0), nota=float(f[10] or 0),
                        caps=int(f[7] or 0)) for f in base]
        self.vista_datos.poner(novelas, self.vista_crono)
        st = self.vista_crono.stats
        partes = [f"{st['con_fechas']} de {st['total']} novelas con fechas"]
        if st["omitidas"]:
            partes.append(f"{st['omitidas']} omitidas")
        if st["curso"]:
            partes.append(f"📖 {st['curso']} en curso")
        if st["incompletas"]:
            partes.append(f"{st['incompletas']} con fechas incoherentes")
        if st["horas"]:
            partes.append(f"{fmt_horas(st['horas'])} jugadas en total")
        self.lbl_crono.setText("  ·  ".join(partes))

    def _pendientes_clasif_h(self):
        """Heroínas (una por nombre, de todas las novelas) que aún no tienen sí/no de H."""
        hechas = {r[0] for r in self.conn.execute("SELECT clave FROM clasif_heroinas")}
        pend = {}
        for hid, n, fo, e, jn in self.conn.execute("""
                SELECT h.id, h.nombre, h.foto, h.foto_enc, j.nombre
                FROM heroinas h JOIN juegos j ON j.id = h.juego_id
                WHERE h.nombre <> 'General' AND TRIM(h.nombre) <> ''
                ORDER BY j.orden, j.nombre COLLATE NOCASE, h.top_pos, h.id"""):
            clave = clave_heroina(n)
            if clave in hechas:
                continue
            it = pend.get(clave)
            if it is None:
                pend[clave] = dict(clave=clave, nombre=n, foto=fo or "", enc=parse_enc(e),
                                   juego=jn, _js=[jn])
            else:
                if jn not in it["_js"]:
                    it["_js"].append(jn)
                if (not it["foto"] or not Path(it["foto"]).exists()) and fo:
                    it["foto"], it["enc"] = fo, parse_enc(e)
        for it in pend.values():
            it["juego"] = " · ".join(it.pop("_js"))
        return list(pend.values())

    def _actualizar_boton_clasif(self):
        try:
            n = len(self._pendientes_clasif_h())
        except Exception:
            return
        self.b_clasif_h.setText(f"💗 Clasificar H · {n} nuevas" if n else "💗 Clasificar H ✓")

    def corregir_heroina_h(self):
        """Cambia el sí/no de H de una heroína concreta, buscándola por su nombre."""
        nombres = {}
        for (n,) in self.conn.execute(
                "SELECT nombre FROM heroinas WHERE nombre <> 'General' AND TRIM(nombre) <> '' "
                "ORDER BY id"):
            nombres.setdefault(clave_heroina(n), n)
        estado = {r[0]: r[1] for r in self.conn.execute(
            "SELECT clave, eroge FROM clasif_heroinas")}

        def guardar(clave, nombre, valor):
            self.conn.execute(
                "INSERT INTO clasif_heroinas(clave, nombre, eroge) VALUES (?, ?, ?) "
                "ON CONFLICT(clave) DO UPDATE SET nombre = excluded.nombre, "
                "eroge = excluded.eroge", (clave, nombre, int(valor)))
            self.conn.commit()

        dlg = DialogoCorregirH(self, nombres, estado, guardar)
        dlg.exec()
        if 1 in self._info_cargada:
            self._cargar_seiyuus()
        self._actualizar_boton_clasif()

    def clasificar_heroinas_h(self):
        """Botón global: solo muestra las heroínas aún no registradas y guarda sí/no."""
        pend = self._pendientes_clasif_h()
        if not pend:
            self.toast("💗 Todas las heroínas ya están clasificadas")
            return

        def guardar(clave, nombre, valor):
            self.conn.execute(
                "INSERT INTO clasif_heroinas(clave, nombre, eroge) VALUES (?, ?, ?) "
                "ON CONFLICT(clave) DO UPDATE SET nombre = excluded.nombre, "
                "eroge = excluded.eroge", (clave, nombre, int(valor)))
            self.conn.commit()

        def borrar(clave):
            self.conn.execute("DELETE FROM clasif_heroinas WHERE clave = ?", (clave,))
            self.conn.commit()

        dlg = DialogoClasificarH(self, pend, guardar, borrar)
        dlg.exec()
        if dlg.hechas:
            self.toast(f"💗 {dlg.hechas} clasificadas · {dlg.n_si} con escenas H")
            if 1 in self._info_cargada:
                self._cargar_seiyuus()
        self._actualizar_boton_clasif()

    def abrir_info_heroinas(self):
        self._actualizar_boton_clasif()
        self._azar_seiyuus = {}             # nuevo sorteo cada vez que entras
        self._info_cargada = set()          # se vuelve a cargar, pero solo la pestaña visible
        self.ir_a_pagina(4)
        QTimer.singleShot(0, lambda: self._cargar_pestana_info(self.tabs_info.currentIndex()))

    def cargar_info_heroinas(self, *_):
        """Refresca la pestaña que se está viendo (las demás se cargan al abrirlas)."""
        if not hasattr(self, "tabs_info"):
            return
        self._info_cargada = set()
        self._cargar_pestana_info(self.tabs_info.currentIndex())

    # ---------- pestaña «Altura y medidas»: campeonas y tops (solo lo que ganó cada una)

    def construir_medidas(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 12, 0, 0)
        v.setSpacing(10)
        self.lbl_medidas = QLabel("")
        self.lbl_medidas.setObjectName("muted")
        self.lbl_medidas.setWordWrap(True)
        v.addWidget(self.lbl_medidas)
        chips = QGridLayout()
        chips.setSpacing(8)
        self.grupo_medidas = QButtonGroup(self)
        self.grupo_medidas.setExclusive(True)
        self.chips_medidas = {}
        for k, (clave, texto) in enumerate(MODOS_MEDIDAS + (("campeonas", "👑 Las campeonas"),)):
            b = BotonAnimado(texto)
            b.setToolTip(DESCRIPCION_MEDIDAS.get(clave, ""))
            b.setCheckable(True)
            b.setAutoDefault(False)
            b.clicked.connect(lambda _=False, c=clave: self.elegir_modo_medidas(c))
            self.grupo_medidas.addButton(b)
            self.chips_medidas[clave] = b
            chips.addWidget(b, k // 7, k % 7)
        chips.setColumnStretch(7, 1)
        v.addLayout(chips)
        self.lbl_desc_medidas = QLabel("")          # qué significa el apartado elegido
        self.lbl_desc_medidas.setWordWrap(True)
        self.lbl_desc_medidas.setObjectName("muted")
        v.addWidget(self.lbl_desc_medidas)
        self.cont_medidas = ContenedorFilas()
        v.addWidget(self.cont_medidas, 1)
        self.modo_medidas = "alta"
        self.chips_medidas["alta"].setChecked(True)
        self._datos_medidas = []
        return w

    def datos_medidas(self):
        """Heroínas con altura o medidas, una sola vez aunque salgan en varias novelas."""
        filas = self.conn.execute("""
            SELECT h.id, h.nombre, h.foto, h.foto_enc, h.altura, h.busto, h.cintura, h.cadera,
                   j.nombre
            FROM heroinas h JOIN juegos j ON j.id = h.juego_id
            WHERE h.nombre <> 'General'
            ORDER BY j.orden, j.nombre COLLATE NOCASE, h.top_pos, h.id
        """).fetchall()
        grupos = {}
        for hid, n, fo, e, alt, bu, ci, ca, jn in filas:
            k = clave_heroina(n)
            g = grupos.get(k)
            if g is None:
                grupos[k] = dict(id=hid, nombre=n, foto=fo, enc=e, altura=alt or 0,
                                 busto=bu or 0, cintura=ci or 0, cadera=ca or 0, novelas=[jn])
                continue
            if not g["altura"] and alt:
                g["altura"] = alt
            if not medidas_completas(g["busto"], g["cintura"], g["cadera"]) \
                    and medidas_completas(bu, ci, ca):
                g["busto"], g["cintura"], g["cadera"] = bu, ci, ca
            if not g["foto"] and fo:
                g["foto"], g["enc"] = fo, e
            if jn not in g["novelas"]:
                g["novelas"].append(jn)
        return [g for g in grupos.values()
                if g["altura"] or medidas_completas(g["busto"], g["cintura"], g["cadera"])]

    def cargar_medidas(self):
        if not hasattr(self, "cont_medidas"):
            return
        self._datos_medidas = self.datos_medidas()
        self.pintar_medidas()

    def elegir_modo_medidas(self, modo):
        self.modo_medidas = modo
        self.pintar_medidas()

    @staticmethod
    def _ranking_medidas(modo, con_alt, con_med):
        """(heroínas ordenadas, función de valor, ¿gana el mayor?) para cada prueba."""
        if modo in ("alta", "baja"):
            base, valor, mayor = con_alt, (lambda h: h["altura"]), modo == "alta"
        elif modo == "reloj":
            base, mayor = con_med, True
            valor = lambda h: puntaje_reloj(h["busto"], h["cintura"], h["cadera"])
        else:
            base = con_med
            valor, mayor = {
                "cintura": (lambda h: h["cintura"], False),
                "busto": (lambda h: h["busto"], True),
                "cadera": (lambda h: h["cadera"], True),
                "violin": (lambda h: h["cadera"] - h["cintura"], True),
                "cadera_min": (lambda h: h["cadera"], False),
                "coqueta": (lambda h: h["busto"], False),
                "voluptuosa": (lambda h: h["busto"] + h["cintura"] + h["cadera"], True),
                "delicada": (lambda h: h["busto"] + h["cintura"] + h["cadera"], False),
                "simetria": (lambda h: abs(h["busto"] - h["cadera"]), False),
            }[modo]
        orden = sorted(base, key=lambda h: (-valor(h) if mayor else valor(h),
                                            h["nombre"].casefold()))
        return orden, valor, mayor

    @staticmethod
    def _puestos(orden, valor):
        """Puesto de cada heroína (ya ordenadas): las que empatan comparten puesto y la
        siguiente salta (1, 1, 3, 4…)."""
        puestos = []
        for i, h in enumerate(orden):
            puestos.append(puestos[-1] if i and valor(h) == valor(orden[i - 1]) else i + 1)
        return puestos

    def _tile_medidas(self, h, rank, clave, v, frac, ctx, retraso, etiqueta=""):
        t = TileMedidas(h["foto"], parse_enc(h["enc"]), h, rank, etiqueta, v,
                        "/100" if clave == "reloj" else " cm", clave, ctx, frac, retraso)
        t.clic.connect(lambda hid=h["id"]: self.abrir_heroina_desde_hall(hid))
        return t

    def pintar_medidas(self):
        datos = self._datos_medidas
        con_alt = [h for h in datos if h["altura"]]
        con_med = [h for h in datos if medidas_completas(h["busto"], h["cintura"], h["cadera"])]
        ctx = {}
        if con_alt:
            ctx["min_alt"] = min(h["altura"] for h in con_alt)
            ctx["max_alt"] = max(h["altura"] for h in con_alt)
        if con_med:
            ctx["ref_med"] = max(max(h["busto"], h["cadera"]) for h in con_med)
        self.lbl_medidas.setText(
            f"{len(datos)} {'heroína' if len(datos) == 1 else 'heroínas'} con datos "
            "(ranking global de todas tus novelas)  ·  doble clic para abrir su galería")

        modo = self.modo_medidas
        titulo_modo = "Las campeonas" if modo == "campeonas" else dict(MODOS_MEDIDAS).get(modo, "")
        self.lbl_desc_medidas.setText(f"<b>{titulo_modo}:</b> {DESCRIPCION_MEDIDAS.get(modo, '')}")
        if modo == "campeonas":                  # una tarjeta por categoría: quién reina
            tiles = []
            for clave, _txt in MODOS_MEDIDAS:
                orden, valor, _m = self._ranking_medidas(clave, con_alt, con_med)
                if not orden:
                    continue
                puestos = self._puestos(orden, valor)
                primeras = [h for h, rk in zip(orden, puestos) if rk == 1]
                for h in primeras:                      # si empatan, todas reinan
                    et = ETIQUETA_MEDIDAS[clave] + ("  ·  EMPATE" if len(primeras) > 1 else "")
                    tiles.append(self._tile_medidas(h, 1, clave, valor(h), 1.0, ctx,
                                                    len(tiles) * 60, et))
            self.cont_medidas.poner(
                [RejillaTiles(tiles, 470)] if tiles else [],
                "Aún no hay heroínas con altura o medidas.")
            return

        orden, valor, mayor = self._ranking_medidas(modo, con_alt, con_med)
        falta = "altura" if modo in ("alta", "baja") else "medidas completas"
        if not orden:
            self.cont_medidas.poner([], f"Aún no hay heroínas con {falta}.")
            return
        lider = valor(orden[0])
        puestos = self._puestos(orden, valor)
        suf = "/100" if modo == "reloj" else " cm"
        podio, tiles = [], []
        for k, (h, rk) in enumerate(zip(orden, puestos)):
            v = valor(h)
            if k < 3:
                podio.append(dict(h=h, rank=rk, valor=v, suf=suf,
                                  pm=avatar(h["foto"], 280, parse_enc(h["enc"]))))
            else:                                    # del 4.º en adelante: ranking global completo
                if mayor:
                    frac = (v / float(lider)) if lider else 1.0
                else:
                    frac = (lider + 1.0) / (v + 1.0)
                tiles.append(self._tile_medidas(h, rk, modo, v, frac, ctx,
                                                min((k - 3) * 45, 900)))
        pod = PodioMedidas(podio, modo, ETIQUETA_MEDIDAS[modo], ctx)
        pod.abrir.connect(self.abrir_heroina_desde_hall)
        self.cont_medidas.poner([pod] + ([RejillaTiles(tiles, 430)] if tiles else []))

    def cambiar_foto_seiyuu(self, clave):
        """Elegir o cambiar la foto de la seiyuu y encuadrarla (arrastrar = mover, rueda = ampliar)."""
        f = self.conn.execute("SELECT foto, foto_enc FROM seiyuus WHERE clave = ?",
                              (clave,)).fetchone()
        previa, enc_txt = (f[0], f[1]) if f else ("", "1,0,0")
        nombre = self._nombres_seiyuu.get(clave, clave)
        dlg = DialogoTarjeta(
            self, "Foto de la seiyuu", "Seiyuu:", nombre=nombre,
            imagen=previa if previa and Path(previa).exists() else "",
            nombre_editable=False, enc=parse_enc(enc_txt),
            info="Elige su foto y déjala bien encuadrada.")
        if not dlg.exec():
            return
        enc = fmt_enc(dlg.encuadre)
        if dlg.cambio_imagen:
            nueva = (copiar_asset(dlg.imagen, "seiyuus",
                                  f"s_{zlib.crc32(clave.encode('utf-8')):08x}")
                     if dlg.imagen else "")
        else:
            nueva = previa
        self.conn.execute(
            "INSERT INTO seiyuus(clave, nombre, foto, foto_enc) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET foto = excluded.foto, nombre = excluded.nombre, "
            "foto_enc = excluded.foto_enc", (clave, nombre, nueva, enc))
        self.conn.commit()
        if previa and previa != nueva:
            try:
                if (ASSETS / "seiyuus") in Path(previa).parents:
                    Path(previa).unlink(missing_ok=True)
            except OSError:
                pass
        self._refrescar_foto_seiyuu(clave)
        self.toast("📷 Foto de la seiyuu guardada")

    def editar_datos_seiyuu(self, clave):
        """Cumpleaños (con año y edad) y redes sociales de la seiyuu."""
        g = next((x for x in self._grupos_seiyuu if x["clave"] == clave), None)
        if g is None:
            return
        dlg = DialogoDatosSeiyuu(self, g["nombre"], g.get("cumple", ""),
                                 g.get("redes", []), g.get("anio", 0), g.get("vndb", ""))
        if not dlg.exec():
            return
        cumple, redes, anio, vndb = dlg.valores()
        self.conn.execute(
            "INSERT INTO seiyuus(clave, nombre, cumple, redes, anio, vndb) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET cumple = excluded.cumple, "
            "redes = excluded.redes, anio = excluded.anio, vndb = excluded.vndb",
            (clave, g["nombre"], cumple, json.dumps(redes, ensure_ascii=False), anio, vndb))
        self.conn.commit()
        g["cumple"], g["redes"], g["anio"], g["vndb"] = cumple, redes, anio, vndb
        for t in self.cont_seiyuus.items:
            if getattr(t, "d", None) is g:
                t.recargar_datos()
        self.toast("🎙 Datos de la seiyuu guardados")

    def menu_seiyuu(self, clave, punto):
        m = QMenu(self)
        a_datos = m.addAction("✎ Cumpleaños, VNDB y redes")
        a_foto = m.addAction("📷 Cambiar / encuadrar foto")
        a_quitar = m.addAction("✕ Quitar foto")
        acc = m.exec(punto)
        if acc == a_datos:
            self.editar_datos_seiyuu(clave)
        elif acc == a_foto:
            self.cambiar_foto_seiyuu(clave)
        elif acc == a_quitar:
            self.conn.execute("UPDATE seiyuus SET foto = '' WHERE clave = ?", (clave,))
            self.conn.commit()
            self._refrescar_foto_seiyuu(clave)

    def _refrescar_foto_seiyuu(self, clave):
        """Cambia la foto de UNA tarjeta en su sitio: sin reordenar ni repintar el resto."""
        f = self.conn.execute("SELECT foto, foto_enc FROM seiyuus WHERE clave = ?",
                              (clave,)).fetchone()
        foto, enc = (f[0] or "", parse_enc(f[1])) if f else ("", parse_enc(""))
        for g in self._grupos_seiyuu:
            if g["clave"] == clave:
                g["foto"], g["enc"] = foto, enc
        for t in self.cont_seiyuus.items:
            if getattr(t, "d", None) and t.d.get("clave") == clave:
                t.recargar_foto()

    # ---------- «Heroínas de heroínas»: ranking global de todas las novelas

    def construir_hall(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)
        fila = QHBoxLayout()
        volver = BotonAnimado("← Biblioteca")
        volver.clicked.connect(self.volver_biblioteca)
        fila.addWidget(volver)
        col = QVBoxLayout()
        t = QLabel("👑 Heroínas de heroínas")
        t.setObjectName("heading")
        self.lbl_hall = QLabel("")
        self.lbl_hall.setObjectName("muted")
        self.lbl_hall.setWordWrap(True)
        col.addWidget(t)
        col.addWidget(self.lbl_hall)
        fila.addLayout(col, 1)
        self.btn_duelos_hall = BotonAnimado("🏆 Torneo  ▾", primario=True)
        self.btn_duelos_hall.clicked.connect(lambda: self.menu_duelos_heroinas("hall"))
        self.btn_novelas_hall = BotonAnimado("🗂 Novelas…")
        self.btn_novelas_hall.clicked.connect(self.elegir_novelas_hall)
        fila.addWidget(self.btn_novelas_hall)
        fila.addWidget(self.btn_duelos_hall)
        v.addLayout(fila)
        self.hall = TopHeroinas(suprema=True)
        self.hall.vacio = "👑\n\nAún no hay heroínas."
        self.scroll_hall = QScrollArea()
        self.scroll_hall.setWidgetResizable(True)
        self.scroll_hall.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_hall.setWidget(self.hall)
        self.hall.scroll = self.scroll_hall
        self.hall.orden_cambiado.connect(self.guardar_hall)
        self.hall.abrir.connect(self.abrir_heroina_desde_hall)
        self.scroll_camp_hall = QScrollArea()
        self.scroll_camp_hall.setWidgetResizable(True)
        self.scroll_camp_hall.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_camp_hall.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # ----- Ranking 1 vs 1: el top individual de siempre, o el resultado de una temporada
        self.cmb_temp_1v1 = QComboBox()
        self.cmb_temp_1v1.currentIndexChanged.connect(self._al_elegir_temp_1v1)
        self.scroll_rank_1v1 = self._scroll_ranking()
        self.pila_rank_1v1 = QStackedWidget()
        self.pila_rank_1v1.addWidget(self.scroll_hall)
        self.pila_rank_1v1.addWidget(self.scroll_rank_1v1)
        # ----- Ranking 3 vs 3: SOLO por equipos, según la temporada elegida
        self.cmb_temp_3v3 = QComboBox()
        self.cmb_temp_3v3.currentIndexChanged.connect(self._al_elegir_temp_3v3)
        self.scroll_rank_3v3 = self._scroll_ranking()
        self.tabs_hall = QTabWidget()
        self.tabs_hall.addTab(self._pagina_ranking(self.cmb_temp_1v1, self.pila_rank_1v1),
                              "👑  Ranking 1 vs 1")
        self.tabs_hall.addTab(self._pagina_ranking(self.cmb_temp_3v3, self.scroll_rank_3v3),
                              "🛡  Ranking 3 vs 3 · equipos")
        self.tabs_hall.addTab(self.scroll_camp_hall, "🏅  Podios por temporada")
        self.tabs_hall.currentChanged.connect(self._al_cambiar_pestana_hall)
        v.addWidget(self.tabs_hall, 1)
        return w

    @staticmethod
    def _scroll_ranking():
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return sc

    @staticmethod
    def _pagina_ranking(combo, contenido):
        """Página de una pestaña de ranking: desplegable de temporada arriba y el contenido debajo."""
        pag = QWidget()
        pv = QVBoxLayout(pag)
        pv.setContentsMargins(0, 8, 0, 0)
        pv.setSpacing(8)
        fila = QHBoxLayout()
        fila.addWidget(QLabel("Temporada:"))
        combo.setMinimumWidth(380)
        fila.addWidget(combo)
        fila.addStretch(1)
        pv.addLayout(fila)
        pv.addWidget(contenido, 1)
        return pag

    def _al_cambiar_pestana_hall(self, i):
        if i == 0:
            self._al_elegir_temp_1v1()
        elif i == 1:
            self._al_elegir_temp_3v3()
        elif i == 2:
            self.refrescar_podios_hall()

    def _temporadas_por_modo(self):
        """{'1v1': [(id, temporada, estado, nombre de la campeona)], '3v3': [...]}, la más reciente
        primero."""
        out = {"1v1": [], "3v3": []}
        for tid, temp, estado, datos in self.conn.execute(
                "SELECT id, temporada, estado, datos FROM torneos ORDER BY temporada DESC"):
            try:
                d = json.loads(datos or "{}")
            except ValueError:
                continue
            jug, rondas = d.get("jug", {}), d.get("rondas", [])
            if not rondas:
                continue
            camp = ""
            if estado == "final" and torneo_terminado(rondas):
                camp = info_jug(jug, rondas[-1][0]["gan"]).get("nombre", "")
            out["3v3" if es_equipos(jug) else "1v1"].append((tid, temp, estado, camp))
        return out

    def refrescar_rankings_temporada(self):
        """Rellena los desplegables de temporada (conservando la elegida) y redibuja la pestaña visible."""
        if not hasattr(self, "cmb_temp_1v1"):
            return
        por = self._temporadas_por_modo()
        for modo, cmb in (("1v1", self.cmb_temp_1v1), ("3v3", self.cmb_temp_3v3)):
            previa = cmb.currentData()
            cmb.blockSignals(True)
            cmb.clear()
            if modo == "1v1":
                cmb.addItem("👑 Ranking general (top de heroínas)", None)
            elif not por[modo]:
                cmb.addItem("Aún no hay temporadas 3 vs 3", None)
            for tid, temp, estado, camp in por[modo]:
                cmb.addItem(f"Temporada {temp}  ·  " + (f"🥇 {camp}" if camp else "en curso"), tid)
            k = cmb.findData(previa) if previa is not None else 0
            cmb.setCurrentIndex(k if k >= 0 else 0)
            cmb.blockSignals(False)
        i = self.tabs_hall.currentIndex()
        if i == 0:
            self._al_elegir_temp_1v1()
        elif i == 1:
            self._al_elegir_temp_3v3()

    def _al_elegir_temp_1v1(self, *_):
        tid = self.cmb_temp_1v1.currentData()
        if tid is None:                      # ranking general: el top individual de siempre
            self.pila_rank_1v1.setCurrentIndex(0)
            return
        self.scroll_rank_1v1.setWidget(self._widget_ranking_temporada(tid))
        self.pila_rank_1v1.setCurrentIndex(1)

    def _al_elegir_temp_3v3(self, *_):
        tid = self.cmb_temp_3v3.currentData()
        if tid is None:
            vacio = QLabel("🛡\n\nAún no hay temporadas 3 vs 3.\n"
                           "Empieza una desde el botón «Torneo».")
            vacio.setObjectName("muted")
            vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_rank_3v3.setWidget(vacio)
            return
        self.scroll_rank_3v3.setWidget(self._widget_ranking_temporada(tid))

    def _widget_ranking_temporada(self, tid):
        """Resultado de UNA temporada: podio (si ya terminó) y clasificación completa. En 3 vs 3 las
        filas son equipos; en 1 vs 1, heroínas."""
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)
        d = self.cargar_torneo(tid)
        if not d or not d["rondas"]:
            lay.addWidget(QLabel("Esta temporada no tiene datos."))
            lay.addStretch(1)
            return cont
        rondas, jug = d["rondas"], d["jug"]
        equipos = es_equipos(jug)
        fin = torneo_terminado(rondas)
        hechas, total = jugadas_y_total(rondas)
        n = sum(len(ll["ids"]) for ll in rondas[0])
        unidad = "equipos" if equipos else "heroínas"
        if fin:
            sub = f"Terminada  ·  {n} {unidad}  ·  {total} duelos"
            if d.get("fin"):
                sub += f"  ·  {fmt_fecha(d['fin']) or d['fin']}"
        else:
            sub = (f"EN CURSO  ·  ronda: {nombre_ronda(ronda_actual(rondas), rondas)}  ·  "
                   f"{hechas} de {total} duelos jugados")
        t = QLabel(f"🏆 Temporada {d['temporada']}  ·  "
                   + ("3 vs 3 por equipos" if equipos else "1 vs 1"))
        t.setObjectName("heading")
        st = QLabel(sub)
        st.setObjectName("muted")
        lay.addWidget(t)
        lay.addWidget(st)
        pod = podio(rondas) if fin else None
        if pod:
            pw = PodioEquipo() if equipos else PodioTemporada()
            pw.poner(pod, jug)
            lay.addWidget(pw)
        nombres = {int(k): v.get("nombre", "") for k, v in jug.items()}
        elim, ganadas = eliminadas(rondas), rondas_ganadas(rondas)
        participantes = [i for ll in rondas[0] for i in ll["ids"]]
        if pod:
            orden = orden_final(rondas, nombres)
        else:                                # en curso: primero las que siguen, luego por ronda
            orden = sorted(participantes, key=lambda i: (
                i in elim, -(elim[i][0] if i in elim else 0), str(nombres.get(i, "")).casefold()))
        R = len(rondas)
        camp_t, sub_t = ("Campeón", "Subcampeón") if equipos else ("Campeona", "Subcampeona")
        if equipos:                          # 3 vs 3: tarjetas con las 3 heroínas de cada equipo
            lay.addWidget(self._tarjetas_equipos(tid, rondas, jug, orden, pod, elim, ganadas))
            lay.addStretch(1)
            return cont
        lista = QListWidget()
        lista.setIconSize(QSize(52, 52))
        lista.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        lista.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        alto = 84 if equipos else 64
        for pos, hid in enumerate(orden, 1):
            if pod and hid in pod[1]:
                est = f"🥇 {camp_t}"
            elif pod and hid in pod[2]:
                est = f"🥈 {sub_t} · perdió la Final"
            elif pod and hid in pod[3]:
                r = elim[hid][0]
                est = "🥉 Tercer lugar" + ("" if r == R - 1 else f" · eliminado en {nombre_ronda(r, rondas)}")
            elif hid in elim:
                r, ante = elim[hid]
                est = (f"✖ Eliminado en {nombre_ronda(r, rondas)}"
                       f"  (cayó ante {info_jug(jug, ante).get('nombre') or '¿?'})")
            else:
                est = "⏳ Sigue en el torneo"
            g = ganadas.get(hid, [])
            det = ("✔ Ganó en: " + " · ".join(nombre_ronda(r, rondas, True) for r in g)
                   if g else "✔ Aún no ha ganado ningún duelo")
            if hid in elim and not g:
                det = "Perdió su primer duelo"
            j = info_jug(jug, hid)
            pm = avatar(j.get("foto") or "", 104, parse_enc(j.get("enc")))
            lineas = [f"#{pos}   {j.get('nombre') or '¿?'}   ·   {est}"]
            if equipos:
                lineas.append(" · ".join(
                    (info_jug(jug, h).get("nombre") or "¿?") + (" 👑" if h == j.get("cap") else "")
                    for h in (j.get("miembros") or [])))
            lineas.append(det)
            it = QListWidgetItem(QIcon(pm), "\n".join(lineas))
            it.setSizeHint(QSize(100, alto))
            lista.addItem(it)
        lista.setFixedHeight(len(orden) * alto + 10)
        lay.addWidget(lista)
        lay.addStretch(1)
        return cont

    def _tarjetas_equipos(self, tid, rondas, jug, orden, pod, elim, ganadas):
        """Ranking 3 vs 3: una tarjeta por equipo con su lugar y, en tamaño mediano, sus 3
        heroínas, cada una con su puesto individual y comentarios cortos sobre su temporada."""
        R = len(rondas)
        esc = html.escape
        st = b3_stats_det(rondas)
        # puesto individual: 3 pts por K.O. + 1 por etapa ganada; luego versus ganados y ❤ finales
        todas = [h for t in orden for h in (info_jug(jug, t).get("miembros") or [])]
        puntos = lambda h: (3 * st.get(h, {}).get("ko", 0) + st.get(h, {}).get("etapas_g", 0),
                            st.get(h, {}).get("vg", 0), st.get(h, {}).get("vida_final") or 0)
        ranking_ind = {h: i for i, h in enumerate(sorted(todas, key=puntos, reverse=True), 1)}
        camp = pod[1][0] if pod else None
        honores = {h: l for h, l in honores_equipo(rondas, jug)} if pod else {}
        etapas_eq = {}
        for t in orden:
            etapas_eq[t] = sum(st.get(h, {}).get("etapas_g", 0)
                               for h in (info_jug(jug, t).get("miembros") or []))
        duelos_jugados = {t: sum(1 for ronda in rondas for ll in ronda
                                 if t in ll["ids"] and (ll.get("b3") or {}).get("hist")) for t in orden}
        borde = {1: "#eea422", 2: "#c3c9d4", 3: "#d08a54"}
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        for pos, t in enumerate(orden, 1):
            e = info_jug(jug, t)
            miembros = list(e.get("miembros") or [])
            cap = e.get("cap")
            if pod and t in pod[1]:
                medalla, est, nivel = "🥇", "Campeón", 1
            elif pod and t in pod[2]:
                medalla, est, nivel = "🥈", "Subcampeón · perdió la Final", 2
            elif pod and t in pod[3]:
                r = elim[t][0]
                medalla, nivel = "🥉", 3
                est = "Tercer lugar" + ("" if r == R - 1 else f" · eliminado en {nombre_ronda(r, rondas)}")
            elif t in elim:
                r, ante = elim[t]
                medalla, nivel = "✖", 0
                est = (f"Eliminado en {nombre_ronda(r, rondas)} "
                       f"(cayó ante {info_jug(jug, ante).get('nombre') or '¿?'})")
            else:
                medalla, nivel, est = "⏳", 0, "Sigue en el torneo"
            g = ganadas.get(t, [])
            gana_txt = (f"🏆 {len(g)} duelo{'s' if len(g) != 1 else ''} ganado{'s' if len(g) != 1 else ''}"
                        if g else "🏆 Sin duelos ganados")
            card = QFrame()
            card.setObjectName("panel")
            if nivel:
                card.setStyleSheet(f"QFrame#panel {{ border: 2px solid {borde[nivel]}; "
                                   "border-radius: 14px; }")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 10, 14, 12)
            cl.setSpacing(8)
            cab = QHBoxLayout()
            tit = QLabel(f"<span style='font-size:19px; font-weight:800;'>{medalla} #{pos}  "
                         f"{esc(e.get('nombre') or '¿?')}</span>"
                         f"  <span style='color:{Tema.c('muted')};'>{esc(est)}</span>")
            tit.setTextFormat(Qt.TextFormat.RichText)
            cab.addWidget(tit, 1)
            der = QLabel(f"{gana_txt}  ·  🏅 {etapas_eq.get(t, 0)} etapas  ·  "
                         f"⚔ {duelos_jugados.get(t, 0)} duelos")
            der.setObjectName("muted")
            cab.addWidget(der, 0, Qt.AlignmentFlag.AlignRight)
            cl.addLayout(cab)
            fila = QHBoxLayout()
            fila.setSpacing(10)
            hay_dif = len(set(map(puntos, miembros))) > 1
            mejor = max(miembros, key=puntos) if miembros and hay_dif else None
            peor = min(miembros, key=puntos) if miembros else None
            tot_eq = max(1, etapas_eq.get(t, 0))
            for h in miembros:
                s = st.get(h) or b3_ficha_vacia()
                j = info_jug(jug, h)
                ctx = dict(
                    es_cap=(h == cap), campeon=(t == camp), mejor_equipo=(h == mejor),
                    peor_equipo=(h == peor and len(set(map(puntos, miembros))) > 1),
                    primera_ronda=(t in elim and elim[t][0] == 0),
                    rank_ind=ranking_ind.get(h, 0), n_ind=len(todas),
                    aporte=_pct(s["etapas_g"], tot_eq), equipo_etapas=etapas_eq.get(t, 0),
                    honores=honores.get(h, []), equipo_jugo=duelos_jugados.get(t, 0) > 0,
                    ronda_caida=(nombre_ronda(s["ronda_caida"], rondas)
                                 if s.get("ronda_caida") is not None else ""))
                coment = b3_comentarios(s, ctx, f"{tid}-{h}", 3)
                sub = QFrame()
                sub.setObjectName("card")
                sub.setStyleSheet(f"QFrame#card {{ border: 1px solid {Tema.c('border')}; "
                                  "border-radius: 12px; }")
                sl = QHBoxLayout(sub)
                sl.setContentsMargins(10, 8, 10, 8)
                sl.setSpacing(10)
                av = QLabel()
                av.setPixmap(avatar(j.get("foto") or "", 84, parse_enc(j.get("enc"))))
                av.setFixedSize(84, 84)
                sl.addWidget(av, 0, Qt.AlignmentFlag.AlignTop)
                col = QVBoxLayout()
                col.setSpacing(3)
                nom = QLabel(("👑 " if h == cap else "") + (j.get("nombre") or "¿?"))
                nom.setWordWrap(True)
                nom.setStyleSheet("font-size: 14px; font-weight: 800;")
                col.addWidget(nom)
                vida = s["vida_final"]
                vida_txt = ("—" if vida is None else "✖ cayó" if vida <= 0 else f"❤ {vida}")
                if s["vs"] == 0:
                    vida_txt = "sin pelear"
                resumen = QLabel(f"#{ranking_ind.get(h, 0)} de {len(todas)}  ·  ⚔ {s['vs']}  ·  "
                                 f"🏅 {s['etapas_g']}  ·  💀 {s['ko']}  ·  {vida_txt}")
                resumen.setObjectName("muted")
                resumen.setStyleSheet("font-size: 11px;")
                col.addWidget(resumen)
                for txt in coment:
                    lb = QLabel(txt)
                    lb.setWordWrap(True)
                    lb.setStyleSheet("font-size: 12px;")
                    col.addWidget(lb)
                col.addStretch(1)
                sl.addLayout(col, 1)
                fila.addWidget(sub, 1)
            cl.addLayout(fila)
            lay.addWidget(card)
        return cont

    def abrir_hall(self):
        self.cargar_hall()
        self.ir_a_pagina(3)

    @staticmethod
    def _juntar_muestras(ids, podio, fila):
        """Une las muestras al azar de varias copias de la misma heroína."""
        normales = [t for i in ids for t in podio[i] if t[1] == "CG normal"]
        hs = [t for i in ids for t in podio[i] if t[1] == "CG H"]
        random.shuffle(normales)
        random.shuffle(hs)
        cg, hh = normales[:1], hs[:2]
        if not cg:
            hh = hs[:3]
        elif len(hh) < 2:
            cg = normales[:3 - len(hh)]
        filas_h = [t for i in ids for t in fila[i]]
        con_h = [t for t in filas_h if t[1] == "CG H"]       # prefiere H; si no hay, CG normal
        elegibles = con_h or filas_h
        random.shuffle(elegibles)
        return cg + hh, elegibles[:1]

    def cargar_hall(self, *_):
        if not hasattr(self, "hall"):
            return
        self.normalizar_tops()
        filas = self.conn.execute("""
            SELECT h.id, h.nombre, h.foto, h.foto_enc, h.seiyuu, h.altura, h.cumple,
                   h.juego_id, j.nombre, h.top_pos,
                   (SELECT COUNT(*) FROM imagenes i WHERE i.heroina_id = h.id),
                   (SELECT COUNT(*) FROM imagenes i
                     WHERE i.heroina_id = h.id AND i.favorito = 1),
                   h.busto, h.cintura, h.cadera
            FROM heroinas h JOIN juegos j ON j.id = h.juego_id
            WHERE h.nombre <> 'General' AND h.tipo = 'heroina' AND j.excluir_hall = 0
            ORDER BY h.top_global, h.id
        """).fetchall()
        por_juego = {}
        for f in filas:                       # lista de heroínas (para los terceros puestos)
            por_juego.setdefault(f[7], []).append((f[9], f[0]))
        solo_camp = {r[0] for r in self.conn.execute(
            "SELECT id FROM juegos WHERE solo_campeona = 1").fetchall()}
        # El puesto se toma del top COMPLETO de la novela (con sub-heroínas y secundarios),
        # igual que lo ves dentro de ella: si la 1.ª del top es una sub-heroína, la
        # «campeona» NO es la siguiente heroína, y no se le puede dar ese título.
        top_real = {}
        for jid_, hid, tp_ in self.conn.execute(
                "SELECT juego_id, id, tipo FROM heroinas WHERE nombre <> 'General' "
                "ORDER BY juego_id, top_pos, id"):
            top_real.setdefault(jid_, []).append((hid, tp_))
        pasan = set()
        rango = {}                            # 1 = campeona, 2 = subcampeona de su novela
        for jid_, lista in top_real.items():
            cupos = 1 if jid_ in solo_camp else 2          # «solo la campeona» → 1 plaza
            for k, (hid, tp_) in enumerate(lista[:cupos], 1):
                if tp_ == "heroina":
                    pasan.add(hid)
                    rango[hid] = k

        # Una sola entrada por heroína aunque salga en varias novelas o secuelas:
        # se cuenta una vez y sus capturas/favoritas se suman.
        pos = {f[0]: k for k, f in enumerate(filas)}
        grupos = {}
        for f in filas:
            grupos.setdefault(clave_heroina(f[1]), []).append(f)
        elegidas = []
        for miembros in grupos.values():
            clasifican = [m for m in miembros if m[0] in pasan]
            if clasifican:
                elegidas.append((clasifican[0], miembros))
        elegidas.sort(key=lambda t: pos[t[0][0]])

        todos_ids = [m[0] for _, miembros in elegidas for m in miembros]
        cats, thumbs, thumbs_fila = self.extras_heroinas(todos_ids)
        items = []
        for rep, miembros in elegidas:
            i, n, fo, e, s, alt, cu = rep[:7]
            bus, cin, cad = rep[12:15]
            for m in miembros:                # completa datos que falten con otra copia
                if not fo and m[2]:
                    fo, e = m[2], m[3]
                s, alt, cu = s or m[4], alt or m[5], cu or m[6]
                if not medidas_completas(bus, cin, cad) and medidas_completas(*m[12:15]):
                    bus, cin, cad = m[12:15]
            ids = [m[0] for m in miembros]
            cats_h = {}
            for hid in ids:
                for cat, k in cats[hid].items():
                    cats_h[cat] = cats_h.get(cat, 0) + k
            if len(ids) == 1:
                th, thf = thumbs[i], thumbs_fila[i]
            else:
                th, thf = self._juntar_muestras(ids, thumbs, thumbs_fila)
            nombres = []
            for m in miembros:
                if m[8] not in nombres:
                    nombres.append(m[8])
            roles = [("🥇 Campeona de " if rango[m[0]] == 1 else "🥈 Subcampeona de ") + m[8]
                     for m in miembros if m[0] in rango]
            items.append(dict(
                id=i, nombre=n, foto=fo, enc=parse_enc(e), seiyuu=s or "", altura=alt or 0,
                busto=bus or 0, cintura=cin or 0, cadera=cad or 0, cumple=cu or "", juego_id=rep[7], juego=" · ".join(nombres),
                juegos_ids={m[7] for m in miembros}, ids=ids,
                rol=" · ".join(roles),
                capturas=sum(m[10] for m in miembros), favs=sum(m[11] for m in miembros),
                cats=cats_h, thumbs=th, thumb_fila=thf))
        self.hall.stats_duelos = self.stats_torneos(items)
        self.hall.poner(items)
        # Terceros puestos de cada novela (no entran al ranking global): 4 al azar por panel,
        # distintos cada vez que se abre esta sección.
        por_id = {f[0]: f for f in filas}
        en_ranking = {clave_heroina(i["nombre"]) for i in items}
        cands = {}
        for lista_j in top_real.values():
            if len(lista_j) < 3 or lista_j[2][1] != "heroina" or lista_j[2][0] not in por_id:
                continue                         # el 3.º real del top debe ser heroína y participar
            f3 = por_id[lista_j[2][0]]
            clave = clave_heroina(f3[1])
            if clave in en_ranking:
                continue
            if clave in cands:                       # misma heroína en varias novelas
                if f3[8] not in cands[clave]["juego"].split(" · "):
                    cands[clave]["juego"] += " · " + f3[8]
                cands[clave]["capturas"] += f3[10]
                cands[clave]["favs"] += f3[11]
            else:
                cands[clave] = dict(id=f3[0], nombre=f3[1], foto=f3[2], enc=parse_enc(f3[3]),
                                    juego=f3[8], capturas=f3[10], favs=f3[11])
        pool = list(cands.values())
        random.shuffle(pool)
        self.hall.poner_terceras(pool[:4], pool[4:8])
        novelas = len(set().union(*[i["juegos_ids"] for i in items])) if items else 0
        if not items:
            txt = "Todavía no hay heroínas en tus novelas."
        else:
            txt = f"{len(items)} heroínas de {novelas} {'novela' if novelas == 1 else 'novelas'}"
        exc = self.conn.execute("SELECT COUNT(*) FROM juegos WHERE excluir_hall = 1").fetchone()[0]
        if exc:
            txt += f" · {exc} {'novela excluida' if exc == 1 else 'novelas excluidas'}"
        self.lbl_hall.setText(txt)
        if hasattr(self, "tabs_hall"):
            self.refrescar_rankings_temporada()
            if self.tabs_hall.currentIndex() == 2:
                self.refrescar_podios_hall()

    def guardar_hall(self, ids):
        c = self.conn
        todos = [r[0] for r in c.execute(
            "SELECT id FROM heroinas WHERE nombre <> 'General' AND tipo = 'heroina' "
            "ORDER BY top_global, id").fetchall()]
        mostradas = set(ids)
        huecos = [k for k, h in enumerate(todos) if h in mostradas]   # puestos que ocupaban
        for k, h in zip(huecos, ids):
            todos[k] = h
        for pos, hid in enumerate(todos, 1):
            c.execute("UPDATE heroinas SET top_global = ? WHERE id = ?", (pos, hid))
        c.commit()
        it = self.hall.items.get(ids[0])
        self.toast(f"👑 {it['nombre']} ({it['juego']}) es la heroína suprema" if it
                   else "👑 Ranking guardado")

    def fijar_participacion_hall(self, jid, participa):
        """participa=False: las heroínas de esa novela no entran a «Heroínas de heroínas»."""
        if jid is None:
            return
        self.conn.execute("UPDATE juegos SET excluir_hall = ? WHERE id = ?",
                          (0 if participa else 1, jid))
        self.conn.commit()
        nombre = self.conn.execute("SELECT nombre FROM juegos WHERE id = ?", (jid,)).fetchone()
        if hasattr(self, "chk_hall") and jid == self.juego_id:
            self.chk_hall.blockSignals(True)
            self.chk_hall.setChecked(participa)
            self.chk_hall.blockSignals(False)
        self.toast((f"👑 «{nombre[0]}» participa en Heroínas de heroínas" if participa
                    else f"🚫 «{nombre[0]}» ya no participa en Heroínas de heroínas")
                   if nombre else "Listo")

    def fijar_solo_campeona(self, jid, solo):
        """solo=True: de esa novela solo la campeona pasa a «Heroínas de heroínas»."""
        if jid is None:
            return
        self.conn.execute("UPDATE juegos SET solo_campeona = ? WHERE id = ?",
                          (1 if solo else 0, jid))
        self.conn.commit()
        nombre = self.conn.execute("SELECT nombre FROM juegos WHERE id = ?", (jid,)).fetchone()
        if hasattr(self, "chk_solo_camp") and jid == self.juego_id:
            self.chk_solo_camp.blockSignals(True)
            self.chk_solo_camp.setChecked(bool(solo))
            self.chk_solo_camp.blockSignals(False)
        self.toast((f"🥇 De «{nombre[0]}» pasa solo la campeona" if solo
                    else f"🥇🥈 De «{nombre[0]}» pasan la campeona y la subcampeona")
                   if nombre else "Listo")

    def elegir_novelas_hall(self):
        filas = self.conn.execute(
            "SELECT id, nombre, excluir_hall FROM juegos ORDER BY orden, id").fetchall()
        if not filas:
            self.toast("Aún no tienes novelas")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Novelas en «Heroínas de heroínas»")
        dlg.resize(460, 520)
        v = QVBoxLayout(dlg)
        lista = QListWidget()
        for jid, nombre, ex in filas:
            it = QListWidgetItem(nombre)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Unchecked if ex else Qt.CheckState.Checked)
            it.setData(Qt.ItemDataRole.UserRole, jid)
            lista.addItem(it)
        v.addWidget(lista, 1)
        pie = QHBoxLayout()
        pie.addStretch()
        b_c = BotonAnimado("Cancelar")
        b_c.clicked.connect(dlg.reject)
        b_ok = BotonAnimado("Guardar", primario=True)
        b_ok.clicked.connect(dlg.accept)
        pie.addWidget(b_c)
        pie.addWidget(b_ok)
        v.addLayout(pie)
        if dlg.exec():
            for i in range(lista.count()):
                it = lista.item(i)
                self.conn.execute(
                    "UPDATE juegos SET excluir_hall = ? WHERE id = ?",
                    (0 if it.checkState() == Qt.CheckState.Checked else 1,
                     it.data(Qt.ItemDataRole.UserRole)))
            self.conn.commit()
            self.cargar_hall()

    # ---------- duelos de heroínas (eliges la mejor de 2) ----------

    def registrar_duelos(self, log, ambito):
        self.conn.executemany(
            "INSERT INTO duelos_heroinas (ganadora_id, perdedora_id, ambito) VALUES (?, ?, ?)",
            [(g, p, ambito) for g, p in log])
        self.conn.commit()

    def stats_duelos(self, items, ambito):
        """{id: (victorias, derrotas)} SOLO de esa lista («hall» o «novela:ID»), sumando todas
        las copias de cada heroína."""
        gan = dict(self.conn.execute(
            "SELECT ganadora_id, COUNT(*) FROM duelos_heroinas WHERE ambito = ? "
            "GROUP BY ganadora_id", (ambito,)))
        per = dict(self.conn.execute(
            "SELECT perdedora_id, COUNT(*) FROM duelos_heroinas WHERE ambito = ? "
            "GROUP BY perdedora_id", (ambito,)))
        out = {}
        for it in items:
            ids = it.get("ids") or [it["id"]]
            out[it["id"]] = (sum(gan.get(h, 0) for h in ids), sum(per.get(h, 0) for h in ids))
        return out

    def cargar_versus(self, ambito, ids):
        """Combates ya guardados entre las heroínas de la lista: [(ganadora, perdedora, etapas)]."""
        s, out = set(ids), []
        for a, b, g, et in self.conn.execute(
                "SELECT a_id, b_id, ganadora_id, etapas FROM versus_resultados WHERE ambito = ?",
                (ambito,)).fetchall():
            if a in s and b in s:
                try:
                    e = {k: int(v) for k, v in json.loads(et or "{}").items()}
                except (ValueError, TypeError):
                    e = {}
                out.append((g, b if g == a else a, e))
        return out

    def guardar_versus(self, ambito, g, p, etapas):
        """Guarda un combate terminado (y sus puntos para victorias/derrotas y campeonas)."""
        a, b = sorted((g, p))
        c = self.conn
        c.execute(
            "INSERT INTO versus_resultados (ambito, a_id, b_id, ganadora_id, etapas) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(ambito, a_id, b_id) DO UPDATE SET "
            "ganadora_id = excluded.ganadora_id, etapas = excluded.etapas, ts = CURRENT_TIMESTAMP",
            (ambito, a, b, g, json.dumps(etapas)))
        c.execute("INSERT INTO duelos_heroinas (ganadora_id, perdedora_id, ambito) VALUES (?, ?, ?)",
                  (g, p, ambito))
        c.executemany(
            "INSERT INTO duelos_criterios (ganadora_id, perdedora_id, criterio, ambito) "
            "VALUES (?, ?, ?, ?)",
            [(w, p if w == g else g, clave, ambito) for clave, w in etapas.items() if w])
        c.commit()

    def reiniciar_versus(self, ambito):
        c = self.conn
        for tabla in ("versus_resultados", "duelos_heroinas", "duelos_criterios"):
            c.execute(f"DELETE FROM {tabla} WHERE ambito = ?", (ambito,))
        c.commit()

    def versus_heroinas(self, amb, hall, w, items, titulo, ultimas):
        ids = [i["id"] for i in items]
        hechos = self.cargar_versus(amb, ids)
        solo = ids[-ultimas:] if ultimas else None
        datos = self.datos_super_duelo([(i["id"], i["ids"]) for i in items])
        dlg = DialogoVersus(self, titulo, items, datos, hechos, solo,
                            lambda g, p, et: self.guardar_versus(amb, g, p, et),
                            rondas=self.rondas_hall(len(ids)) if hall else None)
        dlg.exec()
        if dlg.hubo or dlg.aplicar:
            # El orden sale de TODOS los combates guardados y lo decide SOLO la victoria total
            # (cada versus ganado = 1); con las mismas victorias se respeta el orden que ya tenías.
            orden = clasificar(dlg.ids, dlg.resultados)[0]
            if orden != list(w.orden):
                (self.guardar_hall if hall else self.guardar_top)(orden)
            else:
                self.toast("⚔ Combates guardados · el orden no cambió")
        (self.cargar_hall if hall else self.cargar_top)()

    def rondas_hall(self, n):
        """Combates por heroína en el torneo de «heroínas de heroínas» (se cambia en el menú)."""
        fila = self.conn.execute(
            "SELECT valor FROM ajustes WHERE clave = 'hall_rondas'").fetchone()
        try:
            pedido = int(fila[0]) if fila else 0
        except (TypeError, ValueError):
            pedido = 0
        return max(1, min(n - 1, pedido)) if pedido > 0 else combates_por_heroina(n)

    def pedir_rondas_hall(self):
        n = len(self.hall.orden)
        if n < 3:
            self.toast("Necesitas al menos 3 heroínas")
            return
        r, ok = QInputDialog.getInt(
            self, "Combates por heroína",
            f"Cada heroína peleará este número de veces (torneo suizo).\n"
            f"Todos contra todos serían {n - 1} combates por heroína ({n * (n - 1) // 2} en "
            f"total); lo recomendado para {n} heroínas es {combates_por_heroina(n)} "
            f"(~{n * combates_por_heroina(n) // 2} en total).",
            self.rondas_hall(n), 1, n - 1)
        if ok:
            self.conn.execute(
                "INSERT OR REPLACE INTO ajustes(clave, valor) VALUES ('hall_rondas', ?)", (str(r),))
            self.conn.commit()
            self.toast(f"⚙ {r} combates por heroína (~{n * r // 2} combates en total)")

    def registrar_criterios(self, log, ambito):
        if not log:
            return
        self.conn.executemany(
            "INSERT INTO duelos_criterios (ganadora_id, perdedora_id, criterio, ambito) "
            "VALUES (?, ?, ?, ?)", [(g, p, c, ambito) for g, p, c in log])
        self.conn.commit()

    def datos_super_duelo(self, pares):
        """pares: [(id_item, [ids de heroína])] → {id_item: {'fav': [...], 'normal': [...],
        'h': [...]}} con las rutas de sus CG favoritos / CG normal / CG H."""
        todos = sorted({h for _, ids in pares for h in ids})
        por = {h: {"fav": [], "normal": [], "h": []} for h in todos}
        if todos:
            q = ",".join("?" * len(todos))
            for hid, cat, fav, ruta in self.conn.execute(
                    f"SELECT heroina_id, categoria, favorito, ruta FROM imagenes "
                    f"WHERE heroina_id IN ({q}) AND categoria IN ('CG normal', 'CG H')", todos):
                d = por[hid]
                d["normal" if cat == "CG normal" else "h"].append(ruta)
                if fav:
                    d["fav"].append(ruta)
        out = {}
        for iid, ids in pares:
            agg = {"fav": [], "normal": [], "h": []}
            for h in ids:
                for k in agg:
                    agg[k] += por.get(h, {}).get(k, [])
            out[iid] = agg
        return out

    def menu_duelos_heroinas(self, ambito):
        if ambito == "hall":                  # «Heroínas de heroínas» ya no usa duelos sueltos
            self.menu_torneo_hall()
            return
        w = self.hall if ambito == "hall" else self.top
        btn = self.btn_duelos_hall if ambito == "hall" else self.btn_duelos_top
        m = QMenu(self)
        a_todas = m.addAction(
            "⚔ Versus: torneo suizo  (pocos combates, por etapas)" if ambito == "hall"
            else "⚔ Versus: todos contra todos  (por etapas)")
        a_ult = m.addAction("⚔ Versus: solo las últimas que añadí…")
        a_rap = m.addAction("⚡ Duelo rápido: solo la foto")
        a_rondas = m.addAction("⚙ Combates por heroína…") if ambito == "hall" else None
        m.addSeparator()
        a_rank = m.addAction("🏆 Ranking de duelos…")
        a_camp = m.addAction("🏅 Campeonas por etapa…")
        a_reset = m.addAction("🔁 Reiniciar los versus de esta lista…")
        acc = m.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        if acc is None:
            return
        if a_rondas is not None and acc == a_rondas:
            self.pedir_rondas_hall()
            return
        if acc == a_rank:
            self.ver_ranking_duelos(ambito)
            return
        if acc == a_camp:
            self.ver_campeonas_criterios(ambito)
            return
        if acc == a_reset:
            amb = "hall" if ambito == "hall" else f"novela:{self.juego_id}"
            if QMessageBox.question(
                    self, "Reiniciar versus",
                    "Se borran los combates guardados de esta lista (y sus victorias, derrotas y "
                    "puntos por etapa) para volver a enfrentarlas desde cero.\n\n¿Seguro?"
            ) == QMessageBox.StandardButton.Yes:
                self.reiniciar_versus(amb)
                (self.cargar_hall if ambito == "hall" else self.cargar_top)()
                self.toast("🔁 Versus reiniciados")
            return
        if len(w.orden) < 2:
            self.toast("Necesitas al menos 2 heroínas para hacer duelos")
            return
        ultimas = 0
        if acc == a_ult:
            if len(w.orden) < 3:
                self.toast("Con 2 heroínas usa «ordenar todas»")
                return
            ultimas, ok = QInputDialog.getInt(
                self, "Duelos", "¿Cuántas de las ÚLTIMAS de tu lista quieres meter en el ranking?\n"
                "(las heroínas nuevas se agregan al final; el resto de tu orden no se toca)",
                min(3, len(w.orden) - 1), 1, len(w.orden) - 1)
            if not ok:
                return
        self.duelos_heroinas(ambito, ultimas, rapido=(acc == a_rap))

    def duelos_heroinas(self, ambito, ultimas=0, rapido=False):
        hall = ambito == "hall"
        w = self.hall if hall else self.top
        items = []
        for hid in w.orden:
            it = w.items[hid]
            ruta = it.get("foto") or ""
            if not ruta or not Path(ruta).exists():
                ruta = next((t[0] for t in (it.get("thumbs") or []) if Path(t[0]).exists()), "")
            if hall:
                sub2 = it.get("rol") or (("📖 " + it["juego"]) if it.get("juego") else "")
            else:
                sub2 = (f"🎙 {it['seiyuu']}" if it.get("seiyuu") else (it.get("jp") or ""))
            items.append({"id": hid, "ruta": ruta, "nombre": it["nombre"],
                          "sub": it["nombre"] + (f" · {it['juego']}" if hall and it.get("juego")
                                                 else ""),
                          "foto": it.get("foto") or "", "enc": it.get("enc"), "sub2": sub2,
                          "v": it.get("duelos_v", 0), "d": it.get("duelos_d", 0),
                          "ids": it.get("ids") or [hid]})
        titulo = "Heroínas de heroínas" if hall else f"Heroínas · {self.juego_nombre}"
        amb = "hall" if hall else f"novela:{self.juego_id}"
        if not rapido:
            self.versus_heroinas(amb, hall, w, items, titulo, ultimas)
            return
        dlg = DialogoRankear(self, titulo, items, "duelos", ultimas)
        if not dlg.exec():
            return
        if dlg.log:
            self.registrar_duelos(dlg.log, amb)
        self.registrar_criterios(getattr(dlg, "log_crit", []), amb)
        ids = dlg.resultado
        if ids != list(w.orden):
            (self.guardar_hall if hall else self.guardar_top)(ids)
        else:
            self.toast("El orden no cambió")
        (self.cargar_hall if hall else self.cargar_top)()

    # ---------- ranking y campeonas de los duelos (cada lista por separado)

    def _participantes_duelos(self, ambito):
        """Quiénes participan AHORA en una lista de duelos y cómo se guardan sus combates.
        Devuelve (amb, titulo, miembros):
          · amb: valor de la columna «ambito» de las tablas de duelos («hall» o «novela:ID»).
          · miembros: {id_guardado: (clave, nombre, novela, foto, enc)}. En heroínas de heroínas
            cada heroína agrupa todas sus copias (la misma heroína en varias novelas)."""
        miembros = {}
        if ambito == "hall":
            amb, titulo = "hall", "Heroínas de heroínas"
            for hid, it in self.hall.items.items():
                datos = (hid, it["nombre"], it.get("juego") or "", it.get("foto") or "",
                         it.get("enc"))
                for i in set(it.get("ids") or []) | {hid}:
                    miembros[i] = datos
        else:
            amb, titulo = f"novela:{self.juego_id}", f"Heroínas · {self.juego_nombre}"
            for hid, it in self.top.items.items():
                miembros[hid] = (hid, it["nombre"], self.juego_nombre or "",
                                 it.get("foto") or "", it.get("enc"))
        return amb, titulo, miembros

    def _tabla_ranking_duelos(self, amb, miembros):
        """[(nombre, novela, foto, victorias, derrotas)] solo de quienes participan en la lista:
        primero las que más victorias tienen (solo cuenta la victoria total); al final las que
        aún no tienen duelos."""
        gan = dict(self.conn.execute(
            "SELECT ganadora_id, COUNT(*) FROM duelos_heroinas WHERE ambito = ? "
            "GROUP BY ganadora_id", (amb,)))
        per = dict(self.conn.execute(
            "SELECT perdedora_id, COUNT(*) FROM duelos_heroinas WHERE ambito = ? "
            "GROUP BY perdedora_id", (amb,)))
        acum = {}
        for i, (clave, nombre, novela, foto, _enc) in miembros.items():
            fila = acum.setdefault(clave, [nombre, novela, foto, 0, 0])
            fila[3] += gan.get(i, 0)
            fila[4] += per.get(i, 0)
        filas = list(acum.values())
        jugadas = sorted((f for f in filas if f[3] + f[4]),
                         key=lambda f: (-f[3], str(f[0]).casefold()))
        sin = sorted((f for f in filas if not (f[3] + f[4])),
                     key=lambda f: str(f[0]).casefold())
        return [tuple(f) for f in jugadas + sin]

    def _puntos_etapa_duelos(self, amb, miembros):
        """Puntos por etapa SOLO entre las participantes de la lista.
        Devuelve (v, d, quien): v[(etapa, clave)] puntos ganados, d[(etapa, clave)] perdidos,
        quien[clave] = (nombre, novela, foto, enc)."""
        gan = self.conn.execute(
            "SELECT criterio, ganadora_id, COUNT(*) FROM duelos_criterios WHERE ambito = ? "
            "GROUP BY criterio, ganadora_id", (amb,)).fetchall()
        per = self.conn.execute(
            "SELECT criterio, perdedora_id, COUNT(*) FROM duelos_criterios WHERE ambito = ? "
            "GROUP BY criterio, perdedora_id", (amb,)).fetchall()
        v, d, quien = {}, {}, {}
        for tabla, filas in ((v, gan), (d, per)):
            for crit, hid, n in filas:
                if hid not in miembros:
                    continue
                clave, nombre, novela, foto, enc = miembros[hid]
                k = (crit, clave)
                tabla[k] = tabla.get(k, 0) + n
                quien.setdefault(clave, (nombre, novela, foto, enc))
        return v, d, quien

    def ver_ranking_duelos(self, ambito="novela"):
        """Top de la lista según los duelos: la de mejor resultado es la #1 y así sucesivamente.
        En una novela solo cuentan sus heroínas; en heroínas de heroínas, todas las participantes."""
        from html import escape
        amb, titulo_lista, miembros = self._participantes_duelos(ambito)
        filas = self._tabla_ranking_duelos(amb, miembros)
        if not any(f[3] + f[4] for f in filas):
            self.toast("Aún no hay duelos guardados en esta lista")
            return
        es_hall = ambito == "hall"

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Ranking de duelos · {titulo_lista}")
        dlg.resize(700, 760)
        dlg.setMinimumSize(540, 480)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        titulo = QLabel("🏆 Ranking de duelos")
        titulo.setObjectName("heading")
        lay.addWidget(titulo)

        subtitulo = QLabel(
            ("Todas las heroínas que participan en Heroínas de heroínas. "
             if es_hall else f"Solo las heroínas de {escape(str(self.juego_nombre))}. ")
            + "El puesto lo decide SOLO el total de victorias (cada versus ganado vale 1, sin "
              "importar el marcador de etapas); con las mismas victorias comparten puesto.")
        subtitulo.setObjectName("muted")
        subtitulo.setWordWrap(True)
        lay.addWidget(subtitulo)

        contenido = QWidget()
        col = QVBoxLayout(contenido)
        col.setContentsMargins(2, 2, 2, 2)
        col.setSpacing(8)

        puesto = 0
        anterior = None
        for indice, (nombre, novela, foto, victorias, derrotas) in enumerate(filas, 1):
            total = victorias + derrotas
            if total:
                if victorias != anterior:
                    puesto = indice
                    anterior = victorias
                texto_puesto = f"#{puesto}"
            else:
                texto_puesto = "—"

            tarjeta = QFrame()
            tarjeta.setObjectName("panel")
            tarjeta.setFrameShape(QFrame.Shape.StyledPanel)
            fila = QHBoxLayout(tarjeta)
            fila.setContentsMargins(10, 9, 12, 9)
            fila.setSpacing(12)

            lbl_puesto = QLabel(texto_puesto)
            lbl_puesto.setMinimumWidth(48)
            lbl_puesto.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_puesto.setStyleSheet("font-size: 19px; font-weight: 700;")
            fila.addWidget(lbl_puesto, 0, Qt.AlignmentFlag.AlignVCenter)

            lbl_foto = QLabel()
            lbl_foto.setFixedSize(76, 76)
            lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_foto.setStyleSheet("border-radius: 8px; background: rgba(127,127,127,35);")
            ruta = Path(foto) if foto else None
            if ruta and ruta.is_file():
                pm = QPixmap(str(ruta))
                if not pm.isNull():
                    pm = pm.scaled(lbl_foto.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
                    lbl_foto.setPixmap(pm)
            fila.addWidget(lbl_foto, 0, Qt.AlignmentFlag.AlignVCenter)

            datos = QVBoxLayout()
            datos.setSpacing(4)
            lbl_nombre = QLabel(escape(str(nombre)))
            lbl_nombre.setStyleSheet("font-size: 15px; font-weight: 700;")
            lbl_nombre.setWordWrap(True)
            datos.addWidget(lbl_nombre)
            if es_hall and novela:
                lbl_novela = QLabel(escape(str(novela)))
                lbl_novela.setObjectName("muted")
                lbl_novela.setWordWrap(True)
                datos.addWidget(lbl_novela)
            lbl_stats = QLabel(f"<b>{victorias}</b> victorias  -  <b>{derrotas}</b> derrotas")
            lbl_stats.setTextFormat(Qt.TextFormat.RichText)
            datos.addWidget(lbl_stats)
            pct = (victorias / total * 100) if total else 0
            lbl_pct = QLabel(f"Porcentaje de victorias: {pct:.1f}% · {total} duelos"
                             if total else "Aún sin duelos")
            lbl_pct.setObjectName("muted")
            datos.addWidget(lbl_pct)
            datos.addStretch(1)
            fila.addLayout(datos, 1)
            col.addWidget(tarjeta)

        col.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(contenido)
        lay.addWidget(scroll, 1)

        cerrar = BotonAnimado("Cerrar", primario=True)
        cerrar.clicked.connect(dlg.accept)
        lay.addWidget(cerrar, 0, Qt.AlignmentFlag.AlignRight)
        dlg.exec()

    def _widget_campeonas(self, ambito):
        """Una tarjeta por etapa con la CAMPEONA (foto, nombre y victorias), solo entre las
        participantes de esa lista. Devuelve (widget, hay_datos)."""
        amb, _titulo, miembros = self._participantes_duelos(ambito)
        v, d, quien = self._puntos_etapa_duelos(amb, miembros)
        es_hall = ambito == "hall"
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setContentsMargins(6, 6, 6, 6)
        campeonas = []
        for clave, icono, nombre, _q in ETAPAS_VERSUS:
            claves = {k[1] for k in list(v) + list(d) if k[0] == clave}
            if not claves:
                continue
            vv, dd, k = sorted(((v.get((clave, c), 0), d.get((clave, c), 0), c) for c in claves),
                               key=lambda x: (-x[0], x[1], str(quien[x[2]][0]).casefold()))[0]
            corto = nombre.replace("Mejor ", "")
            campeonas.append((icono, corto[:1].upper() + corto[1:], vv, dd, quien[k]))
        if not campeonas:
            vacio = QLabel("🏅\n\nAún no hay campeonas:\njuega un versus")
            vacio.setObjectName("muted")
            vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(vacio, 1)
            return cont, False
        grid = QGridLayout()
        grid.setSpacing(12)
        columnas = 3
        for n, (icono, etapa, vv, dd, (nom, nov, foto, enc)) in enumerate(campeonas):
            tarjeta = QFrame()
            tarjeta.setObjectName("panel")
            tv = QVBoxLayout(tarjeta)
            tv.setContentsMargins(12, 12, 12, 12)
            tv.setSpacing(6)
            lbl_etapa = QLabel(f"{icono}  {etapa}")
            lbl_etapa.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_etapa.setStyleSheet("font-size: 14px; font-weight: 700;")
            tv.addWidget(lbl_etapa)
            lbl_foto = QLabel()
            lbl_foto.setFixedSize(116, 116)
            lbl_foto.setPixmap(avatar(foto or "", 116, enc))
            tv.addWidget(lbl_foto, 0, Qt.AlignmentFlag.AlignHCenter)
            lbl_nom = QLabel(str(nom))
            lbl_nom.setTextFormat(Qt.TextFormat.PlainText)
            lbl_nom.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_nom.setWordWrap(True)
            lbl_nom.setStyleSheet("font-size: 15px; font-weight: 700;")
            tv.addWidget(lbl_nom)
            pct = round(100 * vv / (vv + dd)) if vv + dd else 0
            lbl_v = QLabel(f"🏅 {vv} V · {pct}%")
            lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tv.addWidget(lbl_v)
            if es_hall and nov:
                lbl_nov = QLabel(str(nov))
                lbl_nov.setTextFormat(Qt.TextFormat.PlainText)
                lbl_nov.setObjectName("muted")
                lbl_nov.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_nov.setWordWrap(True)
                tv.addWidget(lbl_nov)
            tv.addStretch(1)
            grid.addWidget(tarjeta, n // columnas, n % columnas)
        for c in range(columnas):
            grid.setColumnStretch(c, 1)
        lay.addLayout(grid)
        lay.addStretch(1)
        return cont, True

    # ---------- Torneo por temporadas de «Heroínas de heroínas»

    def torneo_en_curso(self):
        """id de la temporada que aún no termina (o None)."""
        fila = self.conn.execute(
            "SELECT id FROM torneos WHERE estado = 'curso' ORDER BY id DESC LIMIT 1").fetchone()
        return fila[0] if fila else None

    def cargar_torneo(self, tid):
        fila = self.conn.execute(
            "SELECT id, temporada, estado, datos, campeona_id, inicio, fin FROM torneos "
            "WHERE id = ?", (tid,)).fetchone()
        if not fila:
            return None
        try:
            datos = json.loads(fila[3] or "{}")
        except ValueError:
            datos = {}
        return dict(id=fila[0], temporada=fila[1], estado=fila[2], jug=datos.get("jug", {}),
                    rondas=datos.get("rondas", []), campeona_id=fila[4], inicio=fila[5],
                    fin=fila[6])

    def guardar_torneo(self, tid, jug, rondas, terminado):
        camp = rondas[-1][0]["gan"] if terminado else 0
        self.conn.execute(
            "UPDATE torneos SET datos = ?, estado = ?, campeona_id = ?, fin = ? WHERE id = ?",
            (json.dumps({"jug": jug, "rondas": rondas}), "final" if terminado else "curso",
             camp, time.strftime("%Y-%m-%d") if terminado else "", tid))
        self.conn.commit()

    def nueva_temporada(self, modo=None):
        if modo is None:
            cuadro = QMessageBox(self)
            cuadro.setWindowTitle("Nueva temporada")
            cuadro.setText("¿Qué modalidad quieres para esta temporada?")
            b1 = cuadro.addButton("⚔ 1 vs 1 (clásico)", QMessageBox.ButtonRole.AcceptRole)
            b3 = cuadro.addButton("🛡 3 vs 3 por equipos", QMessageBox.ButtonRole.AcceptRole)
            cuadro.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            cuadro.exec()
            pulsado = cuadro.clickedButton()
            if pulsado is b3:
                modo = "3v3"
            elif pulsado is b1:
                modo = "1v1"
            else:
                return
        if modo == "3v3":
            self._nueva_temporada_equipos()
            return
        w = self.hall
        ids = list(w.orden)
        if len(ids) < 2:
            self.toast("Necesitas al menos 2 heroínas en «Heroínas de heroínas»")
            return
        if self.torneo_en_curso() is not None:
            self.toast("Ya hay una temporada en curso: termínala o cancélala primero")
            return
        n = len(ids)
        rondas = crear_cuadro(ids)
        duelos = sum(len(r) for r in rondas)
        texto = (f"Van a competir {n} heroínas de todas tus novelas.\n\n"
                 f"Se sortean los emparejamientos al azar: {len(rondas)} rondas y {duelos} duelos. "
                 "La que gana pasa a la siguiente ronda y la que pierde queda eliminada, hasta "
                 "que quede la campeona.\n")
        if n % 2:
            texto += ("\nComo son un número impar, habrá una llave especial 1 vs 1 vs 1 "
                      "(en un lugar al azar); solo una de las tres pasa.\n")
        texto += "\nCada duelo se juega solo con fotos: eliges a tu favorita.\n\n¿Empezar?"
        if QMessageBox.question(self, "Nueva temporada", texto) != QMessageBox.StandardButton.Yes:
            return
        jug = {}
        for hid in ids:
            it = w.items[hid]
            ruta = it.get("foto") or ""
            if not ruta or not Path(ruta).exists():
                ruta = next((t[0] for t in (it.get("thumbs") or []) if Path(t[0]).exists()), "")
            jug[str(hid)] = {"nombre": it["nombre"], "juego": it.get("juego") or "",
                             "foto": ruta, "enc": fmt_enc(it.get("enc") or ENC0),
                             "ids": list(it.get("ids") or [hid])}
        num = (self.conn.execute("SELECT COALESCE(MAX(temporada), 0) FROM torneos").fetchone()[0]
               or 0) + 1
        cur = self.conn.execute(
            "INSERT INTO torneos (temporada, estado, datos, inicio) VALUES (?, 'curso', ?, ?)",
            (num, json.dumps({"jug": jug, "rondas": rondas}), time.strftime("%Y-%m-%d")))
        self.conn.commit()
        self.abrir_torneo(cur.lastrowid)

    def _nueva_temporada_equipos(self):
        """Temporada 3 vs 3: las heroínas se reparten al azar en equipos de 3, cada equipo sortea
        su capitana y el cuadro de eliminación directa se juega entre equipos."""
        w = self.hall
        ids = list(w.orden)
        if len(ids) < 6:
            self.toast("Para un 3 vs 3 necesitas al menos 6 heroínas en «Heroínas de heroínas»")
            return
        if self.torneo_en_curso() is not None:
            self.toast("Ya hay una temporada en curso: termínala o cancélala primero")
            return
        random.shuffle(ids)
        n_eq = len(ids) // 3
        part, sobran = ids[:n_eq * 3], ids[n_eq * 3:]
        jug = {}
        for hid in part:
            it = w.items[hid]
            ruta = it.get("foto") or ""
            if not ruta or not Path(ruta).exists():
                ruta = next((t[0] for t in (it.get("thumbs") or []) if Path(t[0]).exists()), "")
            jug[str(hid)] = {"nombre": it["nombre"], "juego": it.get("juego") or "",
                             "foto": ruta, "enc": fmt_enc(it.get("enc") or ENC0),
                             "ids": list(it.get("ids") or [hid])}
        eq_ids, lineas = [], []
        for e in range(n_eq):
            miembros = part[e * 3:e * 3 + 3]
            cap = random.choice(miembros)
            tid = -(e + 1)
            cf = jug[str(cap)]
            jug[str(tid)] = {"nombre": f"Equipo {cf['nombre']}",
                             "juego": " · ".join(jug[str(h)]["nombre"] for h in miembros),
                             "foto": cf["foto"], "enc": cf["enc"], "ids": [tid],
                             "miembros": miembros, "cap": cap}
            eq_ids.append(tid)
            lineas.append(f"• Equipo {cf['nombre']}: " + ", ".join(
                jug[str(h)]["nombre"] + (" 👑" if h == cap else "") for h in miembros))
        rondas = crear_cuadro(eq_ids, sin_trios=True)
        duelos = sum(1 for r in rondas for ll in r if len(ll["ids"]) > 1)
        texto = (f"{len(part)} heroínas en {n_eq} equipos de 3 (sorteados al azar).\n"
                 f"Cada equipo tiene una capitana 👑 con {VIDAS_CAPITANA} corazones; las demás "
                 f"tienen {VIDAS_NORMAL}.\n\n"
                 "En cada duelo el orden de batalla es al azar. Cada etapa perdida resta 1 ❤ "
                 "(si hay empate, las dos pierden 2 ❤). Quien llega a 0 muere y entra la "
                 "siguiente de su equipo contra la que sigue viva, conservando sus corazones. "
                 "Si nadie muere, se sortea otro versus sin repetir parejas. Gana el equipo "
                 "que deja sin heroínas al otro.\n"
                 "Entre rondas, las ganadoras conservan sus corazones, las caídas quedan fuera "
                 "y una viva al azar de cada equipo ganador recupera todos los suyos "
                 "(salvo que de las 3 solo quede una: esa última ya no puede curarse).\n"
                 "Al final, el equipo campeón recibe menciones (MVP, batallas más ganadas, "
                 "CG Hentai Master…).\n"
                 "Las etapas salen en orden aleatorio en cada versus y, con un "
                 f"{int(PROB_EVENTO_3V3 * 100)} % de probabilidad, ocurre un evento aleatorio "
                 "(tormenta, ángel guardián, maldición, intercambio de vidas… ¡más de 60 distintos!).\n\n"
                 f"{len(rondas)} rondas · {duelos} duelos entre equipos.\n")
        if n_eq % 2:
            texto += "Son un número impar de equipos: alguno pasará directo en una ronda.\n"
        if sobran:
            texto += ("\nQuedan fuera de esta temporada (por sorteo, no completan equipo): "
                      + ", ".join(w.items[h]["nombre"] for h in sobran) + ".\n")
        texto += "\n" + "\n".join(lineas[:10]) + ("\n…" if len(lineas) > 10 else "")
        texto += "\n\n¿Empezar?"
        if QMessageBox.question(self, "Nueva temporada · 3 vs 3", texto) != QMessageBox.StandardButton.Yes:
            return
        num = (self.conn.execute("SELECT COALESCE(MAX(temporada), 0) FROM torneos").fetchone()[0]
               or 0) + 1
        cur = self.conn.execute(
            "INSERT INTO torneos (temporada, estado, datos, inicio) VALUES (?, 'curso', ?, ?)",
            (num, json.dumps({"jug": jug, "rondas": rondas}), time.strftime("%Y-%m-%d")))
        self.conn.commit()
        self.abrir_torneo(cur.lastrowid)

    def abrir_torneo(self, tid=None):
        if tid is None:
            tid = self.torneo_en_curso()
        if tid is None:
            self.nueva_temporada()
            return
        if not self.cargar_torneo(tid):
            self.toast("No se encontró esa temporada")
            return
        DialogoTorneo(self, tid).exec()
        self.cargar_hall()

    def cancelar_temporada(self):
        tid = self.torneo_en_curso()
        if tid is None:
            return
        if QMessageBox.question(
                self, "Cancelar temporada",
                "Se borra la temporada en curso con todos sus duelos jugados. "
                "Las temporadas ya terminadas no se tocan.\n\n¿Seguro?"
        ) == QMessageBox.StandardButton.Yes:
            self.conn.execute("DELETE FROM torneos WHERE id = ?", (tid,))
            self.conn.commit()
            self.cargar_hall()
            self.toast("🗑 Temporada cancelada")

    def menu_torneo_hall(self):
        m = QMenu(self)
        en_curso = self.torneo_en_curso()
        a_jugar = a_nueva = a_nueva3 = a_cancel = None
        if en_curso is not None:
            a_jugar = m.addAction("▶ Continuar la temporada en curso")
        else:
            a_nueva = m.addAction("🆕 Nueva temporada · 1 vs 1")
            a_nueva3 = m.addAction("🛡 Nueva temporada · 3 vs 3 por equipos")
        a_podios = m.addAction("🏅 Ver los podios de las temporadas")
        if en_curso is not None:
            m.addSeparator()
            a_cancel = m.addAction("🗑 Cancelar la temporada en curso…")
        acc = m.exec(self.btn_duelos_hall.mapToGlobal(self.btn_duelos_hall.rect().bottomLeft()))
        if acc is None:
            return
        if acc == a_podios:
            self.tabs_hall.setCurrentIndex(2)
            self.refrescar_podios_hall()
        elif acc == a_jugar:
            self.abrir_torneo(en_curso)
        elif acc == a_nueva:
            self.nueva_temporada("1v1")
        elif acc == a_nueva3 and a_nueva3 is not None:
            self.nueva_temporada("3v3")
        elif acc == a_cancel:
            self.cancelar_temporada()

    def aplicar_torneo_a_ranking(self, tid):
        """Campeona #1, subcampeona #2 y las demás según hasta qué ronda llegaron."""
        d = self.cargar_torneo(tid)
        if not d or not torneo_terminado(d["rondas"]):
            return False
        if es_equipos(d["jug"]):               # el 3 vs 3 tiene su propio ranking por equipos
            return False
        nombres = {int(k): v.get("nombre", "") for k, v in d["jug"].items()}
        orden_t = orden_final(d["rondas"], nombres)
        actual = list(self.hall.orden)
        presentes = set(actual)
        cabeza = [i for i in orden_t if i in presentes]
        resto = [i for i in actual if i not in set(cabeza)]
        nuevo = cabeza + resto
        if nuevo != actual:
            self.guardar_hall(nuevo)
        self.cargar_hall()
        return True

    def stats_torneos(self, items):
        """{id: (duelos ganados, duelos perdidos)} sumando las temporadas 1 vs 1."""
        gan, per = {}, {}
        for (datos,) in self.conn.execute("SELECT datos FROM torneos").fetchall():
            try:
                dd = json.loads(datos or "{}")
            except ValueError:
                continue
            rondas, jug_t = dd.get("rondas", []), dd.get("jug", {})
            if es_equipos(jug_t):             # el ranking individual es solo de las temporadas 1 vs 1
                continue

            def integrantes(i, jug_t=jug_t):      # en 3 vs 3 el resultado cuenta para cada integrante
                return (jug_t.get(str(i)) or {}).get("miembros") or [i]
            for ronda in rondas:
                for ll in ronda:
                    if not ll.get("gan") or len(ll["ids"]) < 2:
                        continue
                    for h in integrantes(ll["gan"]):
                        gan[h] = gan.get(h, 0) + 1
                    for i in ll["ids"]:
                        if i != ll["gan"]:
                            for h in integrantes(i):
                                per[h] = per.get(h, 0) + 1
        out = {}
        for it in items:
            ids = it.get("ids") or [it["id"]]
            out[it["id"]] = (sum(gan.get(h, 0) for h in ids), sum(per.get(h, 0) for h in ids))
        return out

    def _widget_podios(self):
        """Pestaña «Podios»: el podio de cada temporada terminada (la más reciente arriba) y,
        si hay una en curso, su avance. Cada una con su botón «Ver cuadro»."""
        esc = html.escape
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(12)
        filas = self.conn.execute(
            "SELECT id, temporada, estado, datos, inicio, fin FROM torneos "
            "ORDER BY temporada DESC").fetchall()
        if not filas:
            vacio = QLabel("🏆\n\nAún no hay temporadas.\nEmpieza un torneo desde el botón «Torneo».")
            vacio.setObjectName("muted")
            vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(vacio, 1)
            return cont
        en_curso = self.torneo_en_curso()
        barra = QHBoxLayout()
        info = QLabel("Cada temporada es un torneo de eliminación directa: la que gana pasa, la que "
                      "pierde queda fuera. Aquí está el podio de cada una.")
        info.setObjectName("muted")
        info.setWordWrap(True)
        barra.addWidget(info, 1)
        b_nueva = BotonAnimado("▶ Continuar la temporada" if en_curso is not None
                               else "🆕 Nueva temporada", primario=True)
        b_nueva.clicked.connect(lambda: self.abrir_torneo(en_curso))
        barra.addWidget(b_nueva)
        lay.addLayout(barra)

        # medallero: cuántas veces subió cada heroína al podio
        medallas = {}
        bloques = []
        for tid, temp, estado, datos, inicio, fin in filas:
            try:
                d = json.loads(datos or "{}")
            except ValueError:
                d = {}
            rondas, jug = d.get("rondas", []), d.get("jug", {})
            if not rondas:
                continue
            pod = podio(rondas) if estado == "final" else None
            bloques.append((tid, temp, estado, rondas, jug, pod, inicio, fin))
            if pod:
                for rank in ((1,) if es_equipos(jug) else (1, 2, 3)):
                    for hid in pod[rank]:
                        for h2 in (info_jug(jug, hid).get("miembros") or [hid]):
                            nom = info_jug(jug, h2).get("nombre") or "¿?"
                            medallas.setdefault(clave_heroina(nom), [nom, 0, 0, 0])[rank] += 1
        if medallas:
            top = sorted(medallas.values(), key=lambda m: (-m[1], -m[2], -m[3], m[0].casefold()))[:8]
            txt = "  ·  ".join(f"<b>{esc(m[0])}</b> 🥇{m[1]} 🥈{m[2]} 🥉{m[3]}" for m in top)
            lbl = QLabel(f"🏅 Medallero: {txt}")
            lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setWordWrap(True)
            lay.addWidget(lbl)

        for tid, temp, estado, rondas, jug, pod, inicio, fin in bloques:
            tarjeta = QFrame()
            tarjeta.setObjectName("panel")
            tv = QVBoxLayout(tarjeta)
            tv.setContentsMargins(14, 12, 14, 12)
            tv.setSpacing(6)
            cab = QHBoxLayout()
            n = sum(len(ll["ids"]) for ll in rondas[0])
            t = QLabel(f"🏆 Temporada {temp}  ·  " + ("3 vs 3" if es_equipos(jug) else "1 vs 1"))
            t.setStyleSheet("font-size: 17px; font-weight: 700;")
            cab.addWidget(t)
            if estado == "final":
                sub = f"{n} heroínas · {sum(len(r) for r in rondas)} duelos"
                if fin:
                    sub += f" · {fmt_fecha(fin) or fin}"
            else:
                hechas, total = jugadas_y_total(rondas)
                sub = (f"EN CURSO · ronda: {nombre_ronda(ronda_actual(rondas), rondas)} · "
                       f"{hechas} de {total} duelos jugados")
            s = QLabel(sub)
            s.setObjectName("muted")
            cab.addWidget(s)
            cab.addStretch()
            b = BotonAnimado("📋 Ver cuadro" if estado == "final" else "▶ Continuar")
            b.clicked.connect(lambda _=False, i=tid: self.abrir_torneo(i))
            cab.addWidget(b)
            tv.addLayout(cab)
            if pod:
                podio_w = PodioEquipo() if es_equipos(jug) else PodioTemporada()
                podio_w.poner(pod, jug)
                tv.addWidget(podio_w)
            lay.addWidget(tarjeta)
        lay.addStretch(1)
        return cont

    def refrescar_podios_hall(self):
        """Rellena la pestaña «Podios» de heroínas de heroínas."""
        if not hasattr(self, "scroll_camp_hall"):
            return
        self.scroll_camp_hall.setWidget(self._widget_podios())

    def ver_campeonas_criterios(self, ambito="novela"):
        """Campeonas por etapa. En heroínas de heroínas es una pestaña (entre todas las
        participantes); en una novela, una ventana con solo las heroínas de esa novela."""
        if ambito == "hall":
            self.tabs_hall.setCurrentIndex(2)
            self.refrescar_podios_hall()
            return
        cont, hay = self._widget_campeonas(ambito)
        if not hay:
            self.toast("Aún no hay campeonas en esta novela: juega un versus primero")
            cont.deleteLater()
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"🏅 Campeonas por etapa · {self.juego_nombre}")
        dlg.resize(760, 620)
        lay = QVBoxLayout(dlg)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setWidget(cont)
        lay.addWidget(sc, 1)
        b_ok = BotonAnimado("Cerrar", primario=True)
        b_ok.clicked.connect(dlg.accept)
        lay.addWidget(b_ok, 0, Qt.AlignmentFlag.AlignRight)
        dlg.exec()

    def abrir_heroina_desde_hall(self, hid):
        fila = self.conn.execute("SELECT juego_id FROM heroinas WHERE id = ?",
                                 (hid,)).fetchone()
        if not fila:
            return
        self.entrar_juego(fila[0])
        self.tabs_juego.setCurrentIndex(0)
        self.cargar_heroinas(hid)

    def abrir_heroina_desde_top(self, hid):
        self.tabs_juego.setCurrentIndex(0)
        self.cargar_heroinas(hid)

    def guardar_orden_heroinas(self, lista=None):
        lista = lista or self.lista_heroinas
        for pos in range(lista.count()):
            hid = lista.item(pos).data(Qt.ItemDataRole.UserRole)["id"]
            self.conn.execute("UPDATE heroinas SET orden = ? WHERE id = ?", (pos + 1, hid))
        self.conn.commit()

    def al_cambiar_heroina(self, actual, anterior=None):
        self._sel_secundaria = False
        if actual is None:
            self.heroina_id = self.heroina_nombre = self._pers_id = None
            self.cover_heroina.poner("", "")
            self.lbl_heroina.setText("—")
            self.pila_gal.setCurrentIndex(0)
            self.refrescar_info_heroina(None)
            self.actualizar_galeria()
            return
        d = actual.data(Qt.ItemDataRole.UserRole)
        tipo = d.get("tipo", "heroina")
        self._pers_id = d["id"]
        if tipo == "secundaria":                    # solo vista: no hay capturas que mostrar
            self.heroina_id = self.heroina_nombre = None
            self._sel_secundaria = True
        else:
            self.heroina_id, self.heroina_nombre = d["id"], d["nombre"]
        self.cover_heroina.poner(d["foto"], d["nombre"], d["enc"])
        self.lbl_heroina.setText(
            d["nombre"] + {"sub": " · sub-heroína",
                           "secundaria": " · personaje secundario"}.get(tipo, ""))
        self.refrescar_info_heroina(d)
        if tipo == "secundaria":                    # sin CG: en vez de pestañas vacías, su perfil
            try:
                clave = clave_heroina(d["nombre"])
                otras, vistas = [], set()
                for jn, hn, jp, je in self.conn.execute(
                        "SELECT j.nombre, h.nombre, j.portada, j.portada_enc FROM heroinas h "
                        "JOIN juegos j ON j.id = h.juego_id "
                        "WHERE h.juego_id <> ? AND h.id <> ? ORDER BY j.orden, j.nombre COLLATE NOCASE",
                        (self.juego_id, d["id"])):
                    if clave_heroina(hn) == clave and jn not in vistas:
                        vistas.add(jn)
                        otras.append({"nombre": jn, "portada": jp or "", "enc": parse_enc(je)})
                reparto = [{"id": i, "nombre": n, "foto": f or "", "enc": parse_enc(e),
                            "tipo": t or "heroina"}
                           for i, n, f, e, t in self.conn.execute(
                               "SELECT id, nombre, foto, foto_enc, tipo FROM heroinas "
                               "WHERE juego_id = ? AND nombre <> 'General' "
                               "ORDER BY CASE tipo WHEN 'sub' THEN 1 WHEN 'secundaria' THEN 2 ELSE 0 END, "
                               "orden, nombre COLLATE NOCASE", (self.juego_id,))]
                self.perfil_sec.poner({
                    "id": d["id"], "nombre": d["nombre"], "foto": d["foto"] or "", "enc": d["enc"],
                    "novela": self.juego_nombre or "", "apodos": lista_apodos(d.get("apodos", "")),
                    "cumple": d["cumple"], "signo": signo_zodiaco(d["cumple"]),
                    "dias_cumple": dias_para_cumple(d["cumple"]), "seiyuu": d["seiyuu"],
                    "altura": d["altura"], "reparto": reparto, "otras": otras})
                self.pila_gal.setCurrentIndex(1)
            except Exception:                       # un perfil con datos raros nunca debe cerrar el programa
                registrar_error_ui("perfil de personaje secundario")
                self.pila_gal.setCurrentIndex(0)
        else:
            self.pila_gal.setCurrentIndex(0)
        self.actualizar_galeria()

    def heroina_actual_datos(self):
        lista = self._lista_pers or self.lista_heroinas
        it = lista.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def cambiar_foto_heroina(self, foto_origen=None):
        d = self.heroina_actual_datos()
        if not d:
            return
        if not foto_origen:
            foto_origen, _ = QFileDialog.getOpenFileName(
                self, "Foto de la heroína", str(Path.home()), FILTRO_IMG)
        if not foto_origen:
            return
        ruta = copiar_asset(foto_origen, "heroinas", f"h_{d['id']}")
        self.conn.execute("UPDATE heroinas SET foto = ?, foto_enc = '1,0,0' WHERE id = ?",
                          (ruta, d["id"]))
        self.conn.commit()
        QTimer.singleShot(0, lambda h=d["id"]: self.cargar_heroinas(h))

    def menu_heroina(self, punto, lista=None):
        lista = lista or self.lista_heroinas
        it = lista.itemAt(punto)
        if not it:
            return
        lista.setCurrentItem(it)
        d = it.data(Qt.ItemDataRole.UserRole)
        m = QMenu(self)
        a_foto = m.addAction("Cambiar foto")
        a_ren = m.addAction("Renombrar")
        a_info = m.addAction("✎ Editar información")
        destinos = {}
        if d["nombre"] != "General":
            sub = m.addMenu("↔ Mover a…")
            for tipo, txt in (("heroina", "Heroínas"), ("sub", "Sub-heroínas"),
                              ("secundaria", "Personajes secundarios")):
                if tipo != d.get("tipo", "heroina"):
                    destinos[sub.addAction(txt)] = tipo
        m.addSeparator()
        a_del = m.addAction("Quitar (sus imágenes pasan a «General»)")
        accion = m.exec(lista.mapToGlobal(punto))
        if accion is None:
            return
        if accion in destinos:
            self.mover_personaje(d["id"], destinos[accion], 10 ** 6)
        elif accion == a_foto:
            self.cambiar_foto_heroina()
        elif accion == a_ren:
            nombre, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=d["nombre"])
            nombre = nombre_seguro(nombre.strip()) if ok else ""
            if nombre:
                try:
                    self.conn.execute("UPDATE heroinas SET nombre = ? WHERE id = ?",
                                      (nombre, d["id"]))
                    self.conn.commit()
                    if d.get("tipo") != "secundaria":
                        preparar_carpetas_heroina(self.juego_carpeta, nombre)
                except sqlite3.IntegrityError:
                    QMessageBox.information(self, "Ya existe", "Ya hay un personaje con ese nombre.")
                self.cargar_heroinas(d["id"])
        elif accion == a_info:
            self.editar_info_heroina()
        elif accion == a_del:
            self.quitar_heroina(d)

    def quitar_heroina(self, d):
        total = self.conn.execute(
            "SELECT COUNT(*) FROM imagenes WHERE heroina_id = ?", (d["id"],)).fetchone()[0]
        if d["nombre"] == "General" and total:
            QMessageBox.information(
                self, "No se puede",
                "«General» contiene imágenes. Muévelas a otra heroína primero.")
            return
        if QMessageBox.question(
                self, "Quitar heroína",
                f"¿Quitar a {d['nombre']}? Sus {total} imágenes pasarán a «General».\n"
                "Los archivos no se borran."
        ) != QMessageBox.StandardButton.Yes:
            return
        if total:
            fila = self.conn.execute(
                "SELECT id FROM heroinas WHERE juego_id = ? AND nombre = 'General'",
                (self.juego_id,)).fetchone()
            gid = fila[0] if fila else self.conn.execute(
                "INSERT INTO heroinas(juego_id, nombre) VALUES (?, 'General')",
                (self.juego_id,)).lastrowid
            self.conn.execute("UPDATE imagenes SET heroina_id = ? WHERE heroina_id = ?",
                              (gid, d["id"]))
            self.conn.commit()
            self.foto_general_desde_portada(gid)
        self.conn.execute("DELETE FROM heroinas WHERE id = ?", (d["id"],))
        self.conn.commit()
        self.heroina_id = None
        self._pers_id = None
        self.cargar_heroinas()
        if self.total_personajes() == 0:
            self.pedir_primera_heroina()

    # -----------------------------------------------------
    # IMPORTACION
    # -----------------------------------------------------

    def exigir_heroina(self):
        if self.juego_id is None or self.heroina_id is None:
            QMessageBox.information(
                self, "Selecciona una heroína",
                "Entra a una novela y selecciona una heroína (o «General»).")
            return False
        return True

    def importar_carpeta(self):
        if not self.exigir_heroina():
            return
        ruta = QFileDialog.getExistingDirectory(self, "Selecciona una carpeta de imágenes")
        if ruta:
            self.importar_rutas([p for p in Path(ruta).rglob("*")
                                 if p.is_file() and p.suffix.lower() in EXTENSIONES])

    def importar_archivos(self):
        if self.pila.currentIndex() != 1 or not self.exigir_heroina():
            return
        archivos, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imágenes", str(Path.home()), FILTRO_IMG)
        if archivos:
            self.importar_rutas([Path(p) for p in archivos])

    def importar_rutas_arrastradas(self, rutas):
        if not self.exigir_heroina():
            return
        archivos = []
        for r in rutas:
            if r.is_dir():
                archivos.extend(p for p in r.rglob("*")
                                if p.is_file() and p.suffix.lower() in EXTENSIONES)
            elif r.is_file() and r.suffix.lower() in EXTENSIONES:
                archivos.append(r)
        self.importar_rutas(archivos)

    def importar_rutas(self, archivos):
        if not self.exigir_heroina():
            return
        preparar_carpetas_heroina(self.juego_carpeta, self.heroina_nombre)
        base = carpeta_hc(self.juego_carpeta, self.heroina_nombre, CAT_DEFECTO)
        copiadas = duplicadas = errores = steam = 0

        progreso = QProgressDialog("Importando imágenes...", "Cancelar", 0, len(archivos), self)
        progreso.setWindowTitle("Importación")
        progreso.setWindowModality(Qt.WindowModality.WindowModal)
        progreso.show()

        for i, origen in enumerate(archivos):
            progreso.setValue(i)
            QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            if progreso.wasCanceled():
                break
            try:
                origen = Path(origen)
                if not origen.is_file():
                    continue
                with Image.open(origen) as img:
                    img.verify()
                huella = hash_archivo(origen)
                if self.conn.execute("SELECT id FROM imagenes WHERE hash = ?",
                                     (huella,)).fetchone():
                    duplicadas += 1
                    continue
                destino = nombre_disponible(base, origen.name)
                shutil.copy2(origen, destino)
                self.conn.execute(
                    "INSERT INTO imagenes (juego_id, heroina_id, ruta, hash, categoria) "
                    "VALUES (?, ?, ?, ?, 'CG normal')",
                    (self.juego_id, self.heroina_id, str(destino), huella))
                copiadas += 1
                if copiadas % 25 == 0:
                    self.conn.commit()
                if es_captura_steam(origen):
                    steam += 1
            except Exception:
                errores += 1

        self.conn.commit()
        progreso.setValue(len(archivos))
        self.actualizar_galeria()
        self.toast(f"✿ Importadas {copiadas} · duplicadas {duplicadas} · errores {errores}")

    # -----------------------------------------------------
    # GALERIA
    # -----------------------------------------------------

    def categoria_actual(self):
        return CATEGORIAS[self.tabs.currentIndex()]

    def lista_actual(self):
        return self.listas[self.tabs.currentIndex()]

    def cambiar_tamano(self, v):
        self.tamano = v
        self.lbl_tamano.setText(f"{v} px")
        self.ajustar_rejilla()

    def _ajustar_lista(self, lista, delegado):
        """Las miniaturas se estiran para llenar siempre todo el ancho."""
        ancho = lista.viewport().width() - 2
        if ancho < 80:
            return
        cols = max(1, ancho // (self.tamano + 10))
        tw = ancho // cols
        th = int(tw * 0.64) + 40
        tam = QSize(tw, th)
        if delegado.tam == tam and lista.gridSize() == tam:
            return
        delegado.tam = tam
        lista.setGridSize(tam)
        for i in range(lista.count()):
            lista.item(i).setSizeHint(tam)
        lista.viewport().update()

    def ajustar_rejilla(self, *a):
        if not hasattr(self, "listas"):
            return
        self._ajustar_lista(self.lista_actual(), self.delegado)

    def actualizar_titulos_tabs(self):
        conteo = {}
        if self.juego_id is not None and self.heroina_id is not None:
            conteo = dict(self.conn.execute(
                "SELECT categoria, COUNT(*) FROM imagenes "
                "WHERE juego_id = ? AND heroina_id = ? GROUP BY categoria",
                (self.juego_id, self.heroina_id)).fetchall())
        for i, cat in enumerate(CATEGORIAS):
            self.tabs.setTabText(i, f"{cat}  ({conteo.get(cat, 0)})")

    def actualizar_galeria(self, *args):
        if self.cargando or not hasattr(self, "listas") or not hasattr(self, "estadisticas") \
                or not hasattr(self, "seleccion_info") or len(self.listas) < len(CATEGORIAS):
            return                      # la galería todavía se está construyendo
        self.cargando = True
        try:
            self.actualizar_titulos_tabs()
            lista = self.lista_actual()
            if self._galeria_id != self.heroina_id:
                for l in self.listas:
                    l.clear()
                self._galeria_id = self.heroina_id
            else:
                lista.clear()
            if self.juego_id is None or self.heroina_id is None:
                self.estadisticas.setText(
                    "Los personajes secundarios son solo de vista: no tienen capturas."
                    if self._sel_secundaria else "Selecciona una heroína para ver sus capturas.")
                return

            categoria = self.categoria_actual()
            orden = self.modo_orden_vista()          # el orden de ESTA heroína + categoría
            if self.orden.currentText() != orden:
                self.orden.blockSignals(True)
                self.orden.setCurrentText(orden)
                self.orden.blockSignals(False)
            consulta = ("SELECT id, ruta, categoria, favorito, etiquetas, comentario, nota_titulo "
                        "FROM imagenes "
                        "WHERE juego_id = ? AND heroina_id = ? AND categoria = ?")
            if orden == "Orden manual":
                consulta += " ORDER BY orden ASC, id DESC"
            elif orden == "Nombre A-Z":
                consulta += " ORDER BY ruta COLLATE NOCASE ASC"
            elif orden == "Nombre Z-A":
                consulta += " ORDER BY ruta COLLATE NOCASE DESC"
            elif orden == "Favoritos primero":
                consulta += " ORDER BY favorito DESC, id DESC"
            else:
                consulta += " ORDER BY id DESC"
            filas = self.conn.execute(
                consulta, (self.juego_id, self.heroina_id, categoria)).fetchall()

            self.delegado.tam = QSize(0, 0)  # fuerza recalcular rejilla
            lista.setGridSize(QSize(0, 0))
            visibles = 0
            for imagen_id, ruta, cat, fav, etiquetas, coment, ntit in filas:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, {
                    "id": imagen_id, "ruta": ruta, "categoria": cat,
                    "favorito": fav, "etiquetas": etiquetas or "",
                    "comentario": coment or "", "nota_titulo": ntit or ""})
                tip = f"Categoría: {cat}\nFavorito: {'Sí' if fav else 'No'}"
                if etiquetas:
                    tip += f"\nEtiquetas: {etiquetas}"
                item.setToolTip(tip)
                lista.addItem(item)
                visibles += 1
            self.ajustar_rejilla()
            lista.iniciar_entrada()

            total, favs = self.conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(favorito), 0) FROM imagenes "
                "WHERE juego_id = ? AND heroina_id = ?",
                (self.juego_id, self.heroina_id)).fetchone()
            self.lbl_stats.setText(f"{total} capturas  ·  {favs} favoritas")
            self.estadisticas.setText(
                f"{visibles} mostradas en «{categoria}»  ·  {total} de {self.heroina_nombre}")
            self.actualizar_seleccion_info()
        finally:
            self.cargando = False

    def modo_orden_vista(self):
        """Orden de ESTA sección (heroína + categoría): cada una recuerda el suyo."""
        if self.heroina_id is None:
            return "Orden manual"
        f = self.conn.execute("SELECT modo FROM orden_vista WHERE heroina_id = ? AND categoria = ?",
                              (self.heroina_id, self.categoria_actual())).fetchone()
        return f[0] if f and self.orden.findText(f[0]) >= 0 else "Orden manual"

    def guardar_modo_orden(self, modo):
        if self.heroina_id is None:
            return
        cat = self.categoria_actual()
        if modo == "Orden manual":                      # es el predeterminado: no hace falta fila
            self.conn.execute("DELETE FROM orden_vista WHERE heroina_id = ? AND categoria = ?",
                              (self.heroina_id, cat))
        else:
            self.conn.execute("INSERT OR REPLACE INTO orden_vista (heroina_id, categoria, modo) "
                              "VALUES (?, ?, ?)", (self.heroina_id, cat, modo))
        self.conn.commit()

    def al_cambiar_orden(self, *_):
        if self.cargando:
            return
        self.guardar_modo_orden(self.orden.currentText())
        self.actualizar_galeria()

    def guardar_orden_galeria(self, ids):
        for pos, iid in enumerate(ids, 1):
            self.conn.execute("UPDATE imagenes SET orden = ? WHERE id = ?", (pos, iid))
        self.conn.commit()
        self.guardar_modo_orden("Orden manual")
        lista = self.lista_actual()
        barra = lista.verticalScrollBar().value()
        self.actualizar_galeria()
        QTimer.singleShot(0, lambda: lista.verticalScrollBar().setValue(barra))

    def seleccion_registros(self):
        return [it.data(Qt.ItemDataRole.UserRole)
                for it in self.lista_actual().selectedItems()
                if it.data(Qt.ItemDataRole.UserRole)]

    def actualizar_seleccion_info(self):
        self.seleccion_info.setText(f"{len(self.seleccion_registros())} seleccionadas")

    # -----------------------------------------------------
    # VISOR, FAVORITOS, ETIQUETAS
    # -----------------------------------------------------

    def items_visor(self):
        lista = self.lista_actual()
        out = []
        for i in range(lista.count()):
            d = lista.item(i).data(Qt.ItemDataRole.UserRole)
            out.append(d["ruta"])
        return out

    def abrir_imagen_seleccionada(self, item):
        """Doble clic abre la captura grande (un clic solo selecciona)."""
        items = self.items_visor()
        datos = item.data(Qt.ItemDataRole.UserRole)
        if datos and datos["ruta"] in items:
            self.abrir_visor(items, items.index(datos["ruta"]))

    def imagen_al_azar(self):
        items = self.items_visor()
        if not items:
            self.toast("No hay imágenes en esta pestaña")
            return
        self.abrir_visor(items, random.randrange(len(items)))

    def exigir_seleccion(self, texto):
        regs = self.seleccion_registros()
        if not regs:
            QMessageBox.information(self, "Selecciona imágenes", texto)
        return regs

    def alternar_favoritos(self):
        regs = self.exigir_seleccion("Selecciona una o más imágenes primero.")
        if not regs:
            return
        nuevo = 0 if all(r["favorito"] for r in regs) else 1
        for r in regs:
            self.conn.execute("UPDATE imagenes SET favorito = ? WHERE id = ?", (nuevo, r["id"]))
        self.conn.commit()
        self.actualizar_galeria()

    def editar_etiquetas(self):
        regs = self.exigir_seleccion("Selecciona imágenes para editar sus etiquetas.")
        if not regs:
            return
        texto, ok = QInputDialog.getText(
            self, "Etiquetas personalizadas", "Etiquetas separadas por comas:",
            text=regs[0]["etiquetas"])
        if not ok:
            return
        for r in regs:
            self.conn.execute("UPDATE imagenes SET etiquetas = ? WHERE id = ?",
                              (texto.strip(), r["id"]))
        self.conn.commit()
        self.actualizar_galeria()

    # -----------------------------------------------------
    # MOVER / QUITAR / MENU
    # -----------------------------------------------------

    def mover_seleccion(self):
        regs = self.exigir_seleccion("Selecciona una o más imágenes para mover.")
        if not regs:
            return
        heroinas = self.conn.execute(
            "SELECT id, nombre FROM heroinas WHERE juego_id = ? AND tipo <> 'secundaria' "
            "ORDER BY orden, nombre COLLATE NOCASE",
            (self.juego_id,)).fetchall()
        dlg = DialogoMover(self, heroinas, self.categoria_actual(), self.heroina_id,
                           getattr(self, "ultimo_destino", None))
        if not dlg.exec() or not dlg.resultado:
            return
        cat, hid, hnombre = dlg.resultado
        self.ejecutar_movimiento(regs, cat, hid, hnombre)

    def atajo_mover(self):
        """Tecla M: abre el panel de Mover para lo seleccionado (sin pasar por el clic derecho)."""
        if self.pila.currentIndex() != 1:
            return
        if isinstance(QApplication.focusWidget(), (QLineEdit, QPlainTextEdit, QSpinBox)):
            return                                   # estás escribiendo: la M es una letra más
        if not self.seleccion_registros():
            self.toast("Selecciona una o más imágenes")
            return
        self.mover_seleccion()

    def repetir_movimiento(self):
        """⚡ Manda la selección al mismo destino de la última vez, sin preguntar nada."""
        regs = self.exigir_seleccion("Selecciona una o más imágenes para mover.")
        if not regs:
            return
        ult = getattr(self, "ultimo_destino", None)
        fila = None
        if ult:
            fila = self.conn.execute(
                "SELECT nombre FROM heroinas WHERE id = ? AND juego_id = ?",
                (ult[1], self.juego_id)).fetchone()
        if not fila:
            self.toast("⚡ Aún no hay un último destino en esta novela: usa Mover (M) primero")
            return
        self.ejecutar_movimiento(regs, ult[0], ult[1], fila[0])

    def ejecutar_movimiento(self, regs, cat, hid, hnombre):
        self.ultimo_destino = (cat, hid, hnombre)
        carpeta = carpeta_hc(self.juego_carpeta, hnombre, cat)
        carpeta.mkdir(parents=True, exist_ok=True)

        movidas = errores = 0
        for r in regs:
            origen = Path(r["ruta"])
            try:
                if not origen.exists():
                    errores += 1
                    continue
                if cat == r["categoria"] and hid == self.heroina_id:
                    continue
                nueva = nombre_disponible(carpeta, origen.name)
                shutil.move(str(origen), str(nueva))
                self.conn.execute(
                    "UPDATE imagenes SET ruta = ?, categoria = ?, heroina_id = ? WHERE id = ?",
                    (str(nueva), cat, hid, r["id"]))
                movidas += 1
            except Exception:
                errores += 1
        self.conn.commit()
        self.actualizar_galeria()
        if movidas:
            self.toast(f"⇄ {movidas} movida(s) → {cat} · {hnombre}")
        if errores:
            QMessageBox.warning(self, "Movimiento parcial",
                                f"No se pudieron mover {errores} imágenes.")

    def eliminar_imagenes(self):
        regs = self.exigir_seleccion("Selecciona las imágenes que quieras eliminar.")
        if not regs:
            return
        if QMessageBox.question(
                self, "Eliminar permanentemente",
                f"¿Eliminar PERMANENTEMENTE {len(regs)} imagen(es)?\n\n"
                "Los archivos se borrarán del disco y no se podrán recuperar.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        borradas = fallos = 0
        for r in regs:
            try:
                Path(r["ruta"]).unlink(missing_ok=True)
                self.conn.execute("DELETE FROM imagenes WHERE id = ?", (r["id"],))
                borradas += 1
            except OSError:
                fallos += 1
        self.conn.commit()
        self.actualizar_galeria()
        self.toast(f"🗑 {borradas} imagen(es) eliminadas"
                   + (f" · {fallos} con error" if fallos else ""))

    def menu_contextual(self, lista, punto):
        item = lista.itemAt(punto)
        if not item:
            return
        if not item.isSelected():
            lista.clearSelection()
            item.setSelected(True)
        m = QMenu(self)
        a_ver = m.addAction("Abrir imagen")
        a_copia = m.addAction("📋 Copiar imagen")
        a_fav = m.addAction("Alternar favorito")
        a_eti = m.addAction("Editar etiquetas")
        a_mov = m.addAction("Mover…   (tecla M)")
        a_foto = m.addAction("Usar como foto de la heroína")
        a_ubi = m.addAction("Abrir ubicación del archivo")
        m.addSeparator()
        a_del = m.addAction("🗑 Eliminar permanentemente")
        accion = m.exec(lista.mapToGlobal(punto))
        datos = item.data(Qt.ItemDataRole.UserRole)
        if accion == a_ver:
            self.abrir_imagen_seleccionada(item)
        elif accion == a_copia:
            if datos and copiar_imagen_portapapeles(datos["ruta"]):
                self.toast("📋 Imagen copiada")
        elif accion == a_fav:
            self.alternar_favoritos()
        elif accion == a_eti:
            self.editar_etiquetas()
        elif accion == a_mov:
            self.mover_seleccion()
        elif accion == a_foto:
            self.cambiar_foto_heroina(datos["ruta"])
        elif accion == a_ubi:
            if datos and Path(datos["ruta"]).exists():
                os.startfile(str(Path(datos["ruta"]).parent))
        elif accion == a_del:
            self.eliminar_imagenes()

    # -----------------------------------------------------
    # ATAJOS
    # -----------------------------------------------------

    def enfocar_busqueda(self):
        if self.pila.currentIndex() == 0:
            self.buscar_juego.setFocus()
            self.buscar_juego.selectAll()

    def seleccionar_todas(self):
        if self.pila.currentIndex() == 1:
            self.lista_actual().selectAll()

    def limpiar_seleccion(self):
        if self.pila.currentIndex() == 1:
            self.lista_actual().clearSelection()

    def closeEvent(self, event):
        for paso in (self._cerrar_audio, self.guia_pdf.close, self._detener_clips, self._detener_voces, self.opening.detener, self.opening_global.detener,
                     self.guardar_pendientes,
                     self.conn.close):
            try:
                paso()
            except Exception:
                pass
        event.accept()


# =========================================================
# INICIO
# =========================================================

if __name__ == "__main__":
    if sys.platform == "win32":          # para que la barra de tareas muestre TU icono
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("NyuhuhuGallery.App")
        except Exception:
            pass
    import faulthandler
    import traceback
    _LOG_ERR = open(ROOT / "error.log", "a", encoding="utf-8", buffering=1)
    faulthandler.enable(file=_LOG_ERR)          # si Qt se cae de golpe, queda constancia aquí

    def _registrar_error(tipo, valor, tb):
        texto = "".join(traceback.format_exception(tipo, valor, tb))
        try:
            _LOG_ERR.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n{texto}")
        except Exception:
            pass
        if sys.stderr:
            sys.stderr.write(texto)

    sys.excepthook = _registrar_error
    threading.excepthook = lambda a: _registrar_error(a.exc_type, a.exc_value, a.exc_traceback)

    _avisos_qt = {"n": 0}

    def _mensaje_qt(tipo, ctx, msg):
        """Anota en error.log los avisos de Qt (sirven para saber qué pasó antes de un cierre)."""
        if tipo == QtMsgType.QtDebugMsg or _avisos_qt["n"] > 300:
            return
        _avisos_qt["n"] += 1
        try:
            _LOG_ERR.write(f"[Qt {time.strftime('%H:%M:%S')}] {msg}\n")
        except Exception:
            pass
    qInstallMessageHandler(_mensaje_qt)

    def _blindar_dibujado():
        """Si un paintEvent/paint falla, se anota y se sigue: antes un error al dibujar podía
        dejar un QPainter abierto y cerrar el programa entero."""
        import functools
        import inspect
        for nombre, cls in list(globals().items()):
            if not inspect.isclass(cls) or cls.__module__ != "__main__":
                continue
            for met in ("paintEvent", "paint"):
                f = cls.__dict__.get(met)
                if f is None or not callable(f) or getattr(f, "_blindado", False):
                    continue

                def envolver(f, donde):
                    @functools.wraps(f)
                    def seguro(*a, **k):
                        try:
                            return f(*a, **k)
                        except Exception:
                            registrar_error_ui(donde)
                    seguro._blindado = True
                    return seguro
                setattr(cls, met, envolver(f, f"{nombre}.{met}"))
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    if ICONO_APP.exists():
        app.setWindowIcon(QIcon(str(ICONO_APP)))

    # ---- Diagnóstico de rendimiento: escribe «rendimiento.log» junto a tu biblioteca.
    # Anota cuánto tarda cada pantalla y, si la ventana se queda congelada, EN QUÉ línea del
    # programa estaba. Para desactivarlo, borra este bloque o el archivo rendimiento.log.
    _LOG_RENDIMIENTO = ROOT / "rendimiento.log"
    _hilo_principal = threading.get_ident()
    _latido = {"t": time.perf_counter(), "ep": None, "n": 0, "ult": 0.0}

    def _anotar(texto):
        try:
            with open(_LOG_RENDIMIENTO, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {texto}\n")
        except OSError:
            pass

    def _vigilante():
        while True:
            time.sleep(0.2)
            ahora, t = time.perf_counter(), _latido["t"]
            if _latido["ep"] != t:                      # la ventana respondió: episodio nuevo
                _latido["ep"], _latido["n"] = t, 0
            if ahora - t > 0.7 and _latido["n"] < 4 and ahora - _latido["ult"] > 0.5:
                _latido["n"] += 1
                _latido["ult"] = ahora
                marco = sys._current_frames().get(_hilo_principal)
                if marco is not None:
                    pila = "".join(traceback.format_stack(marco)[-9:])
                    _anotar(f"CONGELADA {ahora - t:.1f} s. Estaba en:\n{pila}")

    _timer_latido = QTimer()
    _timer_latido.timeout.connect(lambda: _latido.__setitem__("t", time.perf_counter()))
    _timer_latido.start(50)
    threading.Thread(target=_vigilante, daemon=True, name="vigilante").start()

    def _medir(nombre):
        original = getattr(NyuhuhuGallery, nombre)

        def envoltorio(self, *a, **k):
            t0 = time.perf_counter()
            try:
                return original(self, *a, **k)
            finally:
                dt = time.perf_counter() - t0
                if dt > 0.25:
                    _anotar(f"{nombre} tardó {dt:.2f} s")
        setattr(NyuhuhuGallery, nombre, envoltorio)

    for _n in ("abrir_hall", "abrir_favoritos", "abrir_info_heroinas", "entrar_juego",
               "cargar_heroinas", "actualizar_galeria", "cargar_top", "cargar_medidas",
               "cargar_hall", "cargar_favoritos", "cargar_info_heroinas", "cargar_biblioteca"):
        if hasattr(NyuhuhuGallery, _n):
            _medir(_n)
    _anotar("--- programa iniciado ---")

    _blindar_dibujado()
    ventana = NyuhuhuGallery()
    ventana.showMaximized()
    QTimer.singleShot(1500, ventana.aviso_cumple_hoy)          # ocupa toda la pantalla; minimizar/maximizar/cerrar siguen disponibles
    QTimer.singleShot(400, precalentar_miniaturas)
    sys.exit(app.exec())
