# Nyuhuhu Gallery

**[Descargar Nyuhuhu Gallery 5.1.0 para Windows](https://github.com/PaytonN131/nyuhuhu-gallery/releases/download/v5.1.0/NyuhuhuGallery-Windows.zip)** · [Ver todas las versiones](https://github.com/PaytonN131/nyuhuhu-gallery/releases)

Nyuhuhu Gallery es una aplicación de escritorio para organizar una colección de novelas visuales. Reúne portadas, capturas, fichas de personajes, música, clips y voces en una biblioteca local.

## Funciones

- Biblioteca con búsqueda, favoritos, clasificación y temas personalizables.
- **Ficha y guía** con datos de lanzamiento, desarrolladora, enlace a VNDB y un visor integrado para adjuntar y leer tus PDF en una o dos páginas.
- **Openings y Clips** con reproducción de video. Los clips admiten renombrado desde la aplicación.
- **Voces** con tarjetas de retrato, selección de heroína por nombre o foto, reproducción y renombrado de audios.
- Reproductor de música con equilibrio automático de sonoridad de los MP3 mediante FFmpeg.

## Cómo empezar

1. Descarga y extrae el ZIP completo.
2. Ejecuta `NyuhuhuGallery5.0.exe` y conserva la carpeta `_internal` junto al ejecutable.
3. Crea una novela y agrega tu contenido. El ZIP contiene la aplicación y sus dependencias.

## Compilar en Windows

Usa Python 3.12.

```powershell
python -m pip install -r requirements.txt
python -m PyInstaller --clean NyuhuhuGallery5.0.spec
```

La distribución incluye FFmpeg 7.1 Essentials de Gyan Doshi, bajo GPLv3. [Código fuente de FFmpeg](https://ffmpeg.org/releases/ffmpeg-7.1.tar.xz) · [Distribuciones de Gyan](https://www.gyan.dev/ffmpeg/builds/)
