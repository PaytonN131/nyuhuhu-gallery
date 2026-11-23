# Nyuhuhu Gallery

**[Descargar Nyuhuhu Gallery para Windows (ZIP)](https://github.com/PaytonN131/nyuhuhu-gallery/releases/latest/download/NyuhuhuGallery-5.0-Windows.zip)**

Nyuhuhu Gallery es una aplicación de escritorio para organizar y explorar tu colección de novelas visuales. Reúne galerías de imágenes y fichas de personajes y seiyuus, con favoritos, etiquetas y enlaces a The Visual Novel Database (VNDB).

## Cómo empezar

1. Descarga el ZIP y extrae todo su contenido en una carpeta.
2. Abre **NyuhuhuGallery5.0.exe** desde esa carpeta.
3. Conserva la carpeta **_internal** junto al ejecutable.

[Ver versiones en GitHub](https://github.com/PaytonN131/nyuhuhu-gallery/releases)

## Equilibrio de volumen

Desde la versión 5.0.1, el reproductor equilibra automáticamente la sonoridad de los MP3 al reproducirlos. La primera vez que abras una pista en la sesión puede tardar unos segundos. El control de volumen sigue disponible y los MP3 originales se conservan.

## Compilar en Windows

Con Python 3.12, instala las dependencias y crea la distribución:

```powershell
python -m pip install -r requirements.txt
python -m PyInstaller --clean NyuhuhuGallery5.0.spec
```

La aplicación usa el filtro de sonoridad de FFmpeg. La distribución incluye el ejecutable de FFmpeg 7.1 de Gyan que acompaña a imageio-ffmpeg 0.6.0.

- [Código fuente de FFmpeg 7.1](https://ffmpeg.org/releases/ffmpeg-7.1.tar.xz)
- [Distribución y configuración de compilación de Gyan](https://www.gyan.dev/ffmpeg/builds/)
