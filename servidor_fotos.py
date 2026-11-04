#!/usr/bin/env python3
# Servidor local para Trazabilidad: publica el HTML e indexa imágenes de la carpeta.
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlsplit
import json
import os

ROOT = Path(__file__).resolve().parent
IMAGE_EXTS = {".jpg", ".jpeg", ".jfif", ".png", ".webp", ".gif", ".bmp",
              ".tif", ".tiff", ".avif", ".heic", ".heif"}
CACHE = ROOT / ".cache_fotos"
CACHE.mkdir(exist_ok=True)

try:
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_OK = True
except Exception:
    Image = None
    HEIF_OK = False

def public_image(file: Path):
    # Los navegadores no siempre muestran HEIC/HEIF. Si están instaladas las
    # dependencias opcionales, genera una copia JPEG cacheada.
    if file.suffix.lower() in {".heic", ".heif"}:
        if not HEIF_OK or Image is None:
            return None
        target = CACHE / (file.stem + "_" + str(int(file.stat().st_mtime)) + ".jpg")
        if not target.exists():
            with Image.open(file) as im:
                im.convert("RGB").save(target, "JPEG", quality=92)
        return target
    return file

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if urlsplit(self.path).path == "/api/fotos":
            items, seen = [], set()
            scan_roots = [ROOT]
            for folder in ("Fotos_Otras", "Fotos", "fotos", "imagenes", "imagenes_af"):
                p = ROOT / folder
                if p.is_dir():
                    scan_roots.append(p)
            for scan_root in scan_roots:
                try:
                    candidates = scan_root.rglob("*") if scan_root != ROOT else scan_root.iterdir()
                    for file in candidates:
                        if not file.is_file() or file.suffix.lower() not in IMAGE_EXTS:
                            continue
                        rel = file.relative_to(ROOT).as_posix()
                        if rel in seen or any(part.startswith(".") for part in Path(rel).parts):
                            continue
                        seen.add(rel)
                        served = public_image(file)
                        if served is None:
                            continue
                        served_rel = served.relative_to(ROOT).as_posix()
                        st = file.stat()
                        items.append({
                            "name": file.name,
                            "path": served_rel,
                            "url": "/" + quote(served_rel, safe="/"),
                            "mtime": st.st_mtime
                        })
                except OSError:
                    continue
            items.sort(key=lambda x: x["mtime"], reverse=True)
            body = json.dumps(items, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

if __name__ == "__main__":
    os.chdir(ROOT)
    if not HEIF_OK:
        print("Aviso: HEIC/HEIF requiere: pip install -r requirements_fotos.txt")
    host, port = "127.0.0.1", 8765
    print(f"Proyecto listo: http://{host}:{port}/Trazabilidad.html")
    print("Copiá fotos en la raíz o en Fotos_Otras; se detectan al tocar la cámara.")
    print("Para detener: Ctrl+C")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
