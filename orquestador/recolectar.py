#!/usr/bin/env python3
"""Recoge y verifica los clips generados.

Después de una sesión de Colab/Kaggle (o de descargar clips de una API),
`recolectar` comprueba cada clip que la cola espera:

  1. El archivo existe en la carpeta de clips (`<clip_id>.mp4`).
  2. No está vacío ni es un resto (tamaño mínimo 10 KB).
  3. ffprobe lo lee: tiene al menos un stream de vídeo.
  4. Dura lo que el guion pide (± tolerancia, por defecto 1,0 s).

Un clip que pasa queda `hecho`; uno que falla queda marcado con el error
y vuelve a `pendiente` (o a `fallido` si agotó los reintentos), para que
se regenere. Un clip en `en-generacion` que no aparece en disco se deja
como está (puede que la sesión siga corriendo); `marcar_faltantes=True`
lo devuelve a pendiente para reasignarlo.

Requiere ffprobe en el PATH (viene con ffmpeg).
"""

import json
import os
import shutil
import subprocess

TAMANO_MIN_BYTES = 10_000
TOLERANCIA_DURACION_S = 1.0


def ffprobe_disponible():
    return shutil.which("ffprobe") is not None


def inspeccionar_clip(ruta):
    """Inspecciona un clip con ffprobe. Devuelve dict con duración,
    streams y si es legible. Levanta RuntimeError si ffprobe falla."""
    if not os.path.exists(ruta):
        return {"existe": False, "tamano_bytes": 0,
                "legible": False, "duracion_s": None,
                "streams_video": 0, "error": "no existe el archivo"}
    tamano = os.path.getsize(ruta)
    if tamano < TAMANO_MIN_BYTES:
        return {"existe": True, "tamano_bytes": tamano,
                "legible": False, "duracion_s": None,
                "streams_video": 0,
                "error": f"demasiado pequeño ({tamano} bytes, "
                         f"mínimo {TAMANO_MIN_BYTES})"}
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type",
             "-of", "json", ruta],
            capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        raise RuntimeError(
            "ffprobe no está instalado (viene con ffmpeg). "
            "Instala ffmpeg para verificar los clips.")
    if out.returncode != 0:
        return {"existe": True, "tamano_bytes": tamano,
                "legible": False, "duracion_s": None,
                "streams_video": 0,
                "error": f"ffprobe no puede leerlo: "
                         f"{out.stderr.strip()[:200]}"}
    datos = json.loads(out.stdout or "{}")
    dur = None
    try:
        dur = float(datos.get("format", {}).get("duration"))
    except (TypeError, ValueError):
        dur = None
    n_video = sum(1 for s in datos.get("streams", [])
                  if s.get("codec_type") == "video")
    if n_video == 0:
        return {"existe": True, "tamano_bytes": tamano,
                "legible": False, "duracion_s": dur,
                "streams_video": 0,
                "error": "no tiene stream de vídeo"}
    return {"existe": True, "tamano_bytes": tamano,
            "legible": True, "duracion_s": dur,
            "streams_video": n_video, "error": None}


def verificar_clip(ruta, duracion_esperada_s,
                   tolerancia=TOLERANCIA_DURACION_S):
    """Verifica un clip contra su duración esperada.

    Devuelve (ok, info). `ok` es False si no existe, está corrupto o
    dura fuera de la tolerancia.
    """
    info = inspeccionar_clip(ruta)
    if not info["legible"]:
        return False, info
    if info["duracion_s"] is None:
        info["error"] = "ffprobe no devolvió duración"
        return False, info
    diferencia = abs(info["duracion_s"] - duracion_esperada_s)
    if diferencia > tolerancia:
        info["error"] = (f"dura {info['duracion_s']:.2f} s, se esperaban "
                         f"{duracion_esperada_s} s "
                         f"(diferencia {diferencia:.2f} s, "
                         f"tolerancia ±{tolerancia} s)")
        return False, info
    return True, info


def recolectar(cola, clips_dir, marcar_faltantes=False,
               tolerancia=TOLERANCIA_DURACION_S):
    """Verifica los clips de la cola contra `clips_dir`.

    Solo se tocan los clips en `en-generacion` o `hecho` (un `hecho`
    se re-verifica por si el archivo se borró o se corrompió después).
    Devuelve un informe con los clips verificados, los fallidos y los
    que siguen sin aparecer.
    """
    if not ffprobe_disponible():
        raise RuntimeError(
            "ffprobe no está instalado (viene con ffmpeg). "
            "Instala ffmpeg para verificar los clips.")
    informe = {"verificados": [], "fallidos": [], "sin_aparecer": []}
    for item in list(cola.items):
        if item["estado"] not in ("en-generacion", "hecho"):
            continue
        clip_id = item["clip_id"]
        ruta = os.path.join(clips_dir, f"{clip_id}.mp4")
        ok, info = verificar_clip(ruta, item["duracion_s"], tolerancia)
        if ok:
            if item["estado"] == "en-generacion":
                cola.marcar_hecho(clip_id)
            informe["verificados"].append({
                "clip_id": clip_id,
                "fuente": item["fuente"],
                "duracion_s": info["duracion_s"],
                "tamano_bytes": info["tamano_bytes"],
            })
        elif not info["existe"]:
            # Puede que la sesión siga corriendo: no se marca fallo
            # salvo que el usuario lo pida explícitamente.
            if marcar_faltantes and item["estado"] == "en-generacion":
                cola.marcar_fallido(clip_id, "no apareció tras la sesión")
            informe["sin_aparecer"].append({
                "clip_id": clip_id,
                "fuente": item["fuente"],
            })
        else:
            cola.marcar_fallido(clip_id, info["error"])
            informe["fallidos"].append({
                "clip_id": clip_id,
                "fuente": item["fuente"],
                "error": info["error"],
            })
    return informe
