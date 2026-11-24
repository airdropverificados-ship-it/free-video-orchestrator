#!/usr/bin/env python3
"""Narración con Piper TTS (motor PROBADO, ilimitado, local).

Piper TTS se probó el 21 nov 2026 en esta VM: genera voz en español
en CPU, sin internet, sin cuenta y sin límite (ver
~/workspace/apis-gratis-ia/pruebas/piper-test.wav). La voz usada es
`es_ES-sharvard-medium` (76,7 MB, en
~/workspace/apis-gratis-ia/pruebas/piper-voices/).

Genera un WAV por clip desde el guion y recorta el silencio de
cabeza/cola con `voz/recortar_silencios.py` del repo (que además
normaliza a 48 kHz mono, el formato del ensamblaje).

Si piper-tts no está instalado, el script lo dice y explica cómo
instalarlo; no finge que funciona.

Uso:
    python voz/piper_tts.py --guion guion.json --salida wavs/
    python voz/piper_tts.py --guion guion.json --salida wavs/ \\
        --voz es_ES-sharvard-medium --voces-dir /ruta/a/voces/
    python voz/piper_tts.py --guion guion.json --salida wavs/ \\
        --mapa-voces mapa.json   # {"Fresita": "es_ES-sharvard-medium", ...}

Voces en español disponibles (descargar de Hugging Face, ~60-77 MB
cada una): es_ES-sharvard-medium, es_ES-davefx-medium,
es_AR-daniela-high, es_MX-claude-high. Revisar la licencia de cada voz
antes de uso comercial (la mayoría CC-BY/CC0).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

VOZ_DEFECTO = "es_ES-sharvard-medium"
VOCES_DIR_DEFECTO = os.path.join(
    os.path.expanduser("~"), "workspace", "apis-gratis-ia", "pruebas",
    "piper-voices")

URL_VOCES = ("https://huggingface.co/rhasspy/piper-voices/tree/main/"
             "es/es_ES/sharvard/medium")


def mensaje_instalacion():
    return (
        "❌ piper-tts NO está instalado.\n"
        "\n"
        "Para instalarlo (una sola vez):\n"
        "  pip install piper-tts\n"
        "\n"
        "Y descargar una voz en español (una sola vez, ~77 MB):\n"
        "  1. Descarga es_ES-sharvard-medium.onnx y "
        "es_ES-sharvard-medium.onnx.json desde:\n"
        f"     {URL_VOCES}\n"
        "  2. Guárdalos en una carpeta de voces y pasa --voces-dir.\n"
        "\n"
        "Sin piper-tts no se puede generar la narración. Alternativa: "
        "grabar los WAV por otro medio y usar el modo externo de "
        "voz/tts_local.py del repo."
    )


def comprobar_piper():
    """Devuelve (disponible, forma). `forma` es 'modulo' (import piper),
    'cli' (comando piper en PATH) o None."""
    try:
        import piper  # noqa: F401
        return True, "modulo"
    except ImportError:
        pass
    if shutil.which("piper"):
        return True, "cli"
    return False, None


def buscar_modelo(voz, voces_dir):
    """Busca <voz>.onnx (+ su .onnx.json) en la carpeta de voces."""
    onnx = os.path.join(voces_dir, voz + ".onnx")
    if os.path.exists(onnx):
        return onnx
    return None


def sintetizar_cli(texto, modelo_onnx, salida):
    """Sintetiza con el CLI `piper` (o `python -m piper`)."""
    if shutil.which("piper"):
        cmd = ["piper", "--model", modelo_onnx,
               "--output_file", salida]
    else:
        cmd = [sys.executable, "-m", "piper", "--model", modelo_onnx,
               "--output_file", salida]
    proc = subprocess.run(cmd, input=texto, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"piper falló: {proc.stderr.strip()[:300]}")


def sintetizar_modulo(texto, modelo_onnx, salida):
    """Sintetiza con la API Python de piper (sin CLI)."""
    from piper import PiperVoice
    import wave
    voz = PiperVoice.load(modelo_onnx)
    with wave.open(salida, "wb") as wav:
        voz.synthesize_wav(texto, wav)


def recortar_silencio(entrada, salida, repo=None):
    """Recorta el silencio de cabeza/cola con el script del repo.

    Importa `recortar_silencios` si el repo está disponible; si no,
    copia el archivo tal cual y avisa (el ensamblaje recorta de todas
    formas al unir cada segmento).
    """
    repo = repo or os.environ.get("VIDEO_GENERATOR_REPO") or \
        os.path.join(os.path.expanduser("~"), "workspace",
                     "video-generator-repo")
    voz_dir = os.path.join(repo, "voz")
    if os.path.exists(os.path.join(voz_dir, "recortar_silencios.py")):
        sys.path.insert(0, voz_dir)
        from recortar_silencios import recortar
        return recortar(entrada, salida)
    shutil.copy2(entrada, salida)
    print("  (aviso: no se encontró recortar_silencios.py del repo; "
          "el WAV no se recortó, el ensamblaje lo recortará al unir)")
    return None


def duracion_wav(ruta):
    import wave
    with wave.open(ruta, "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def generar_wavs(guion, salida_dir, voz=VOZ_DEFECTO,
                 voces_dir=None, mapa_voces=None, repo=None,
                 sin_recorte=False):
    """Genera un WAV por clip. Devuelve la lista de informes por clip."""
    disponible, forma = comprobar_piper()
    if not disponible:
        raise RuntimeError(mensaje_instalacion())
    voces_dir = voces_dir or os.environ.get("PIPER_VOICES_DIR") \
        or VOCES_DIR_DEFECTO
    os.makedirs(salida_dir, exist_ok=True)

    informes = []
    for clip in guion["clips"]:
        nombre_voz = voz
        if mapa_voces:
            nombre_voz = mapa_voces.get(clip.get("personaje", ""), voz)
        modelo = buscar_modelo(nombre_voz, voces_dir)
        if modelo is None:
            raise FileNotFoundError(
                f"voz '{nombre_voz}' no encontrada en {voces_dir}: "
                f"falta {nombre_voz}.onnx. Descárgala de {URL_VOCES}")
        salida = os.path.join(salida_dir, f"{clip['id']}.wav")
        tmp = os.path.join(salida_dir, f".{clip['id']}-crudo.wav")
        if forma == "modulo":
            sintetizar_modulo(clip["texto"], modelo, tmp)
        else:
            sintetizar_cli(clip["texto"], modelo, tmp)
        if sin_recorte:
            shutil.move(tmp, salida)
            info_recorte = None
        else:
            info_recorte = recortar_silencio(tmp, salida, repo=repo)
            if os.path.exists(tmp):
                os.remove(tmp)
        dur = duracion_wav(salida)
        informes.append({
            "clip_id": clip["id"],
            "voz": nombre_voz,
            "duracion_s": round(dur, 2),
            "duracion_esperada_s": clip["duracion_s"],
            "mas_largo_que_clip": dur > clip["duracion_s"] + 0.5,
            "recorte": info_recorte,
        })
    return informes


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Genera la narración de un guion con Piper TTS.")
    parser.add_argument("--guion", required=True)
    parser.add_argument("--salida", required=True,
                        help="Carpeta donde se guardan los WAV.")
    parser.add_argument("--voz", default=VOZ_DEFECTO)
    parser.add_argument("--voces-dir", default=None,
                        help="Carpeta con los .onnx de Piper "
                        "(o PIPER_VOICES_DIR).")
    parser.add_argument("--mapa-voces", default=None,
                        help="JSON {personaje: voz} para usar una voz "
                        "distinta por personaje.")
    parser.add_argument("--repo", default=None,
                        help="Ruta del repo (para recortar_silencios.py).")
    parser.add_argument("--sin-recorte", action="store_true",
                        help="No recortar el silencio de cabeza/cola.")
    args = parser.parse_args(argv)

    disponible, forma = comprobar_piper()
    if not disponible:
        print(mensaje_instalacion())
        return 2

    with open(args.guion, encoding="utf-8") as f:
        guion = json.load(f)

    mapa = None
    if args.mapa_voces:
        with open(args.mapa_voces, encoding="utf-8") as f:
            mapa = json.load(f)

    try:
        informes = generar_wavs(
            guion, args.salida, voz=args.voz, voces_dir=args.voces_dir,
            mapa_voces=mapa, repo=args.repo,
            sin_recorte=args.sin_recorte)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"❌ {e}")
        return 1

    print(f"Piper ({forma}): {len(informes)} WAV generados en {args.salida}")
    for inf in informes:
        marca = "⚠️" if inf["mas_largo_que_clip"] else "✅"
        extra = (" — la narración dura más que el clip, acorta la línea"
                 if inf["mas_largo_que_clip"] else "")
        print(f"  {marca} {inf['clip_id']}: {inf['duracion_s']} s "
              f"(voz {inf['voz']}){extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
