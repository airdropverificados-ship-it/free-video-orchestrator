#!/usr/bin/env python3
"""Pipeline completo: llama a los scripts del repo por subprocess.

Flujo (los scripts del repo hacen el trabajo real; aquí solo se
orquestan, en orden, con un informe por paso):

    validar guion -> preparar jobs -> voz (Piper) -> ensamblar -> QC

La generación de vídeo en sí NO corre aquí: corre en Colab/Kaggle
(cuadernos) o en las APIs de nube. El pipeline se detiene antes de
ensamblar si faltan clips, y la recolecta (`recolectar.py`) es el paso
que marca los clips como hechos.

La ruta del repo se resuelve así: argumento --repo, variable de entorno
VIDEO_GENERATOR_REPO, o ~/workspace/video-generator-repo.
"""

import json
import os
import subprocess
import sys

REPO_DEFECTO = os.path.join(os.path.expanduser("~"), "workspace",
                            "video-generator-repo")


def resolver_repo(repo=None):
    ruta = repo or os.environ.get("VIDEO_GENERATOR_REPO") or REPO_DEFECTO
    if not os.path.isdir(ruta):
        raise FileNotFoundError(
            f"no existe el repositorio de vídeo en {ruta}. "
            "Pasa --repo o define VIDEO_GENERATOR_REPO.")
    return ruta


def ejecutar(cmd, descripcion):
    """Ejecuta un comando y devuelve (codigo, salida). No levanta
    excepción por código distinto de cero: el llamador decide."""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    salida = (proc.stdout + proc.stderr).strip()
    return proc.returncode, salida


def validar_guion(repo, guion):
    cmd = [sys.executable,
           os.path.join(repo, "guion", "validar_guion.py"),
           "--guion", guion, "--json"]
    codigo, salida = ejecutar(cmd, "validar guion")
    try:
        informe = json.loads(salida)
    except json.JSONDecodeError:
        informe = {"errores": [f"el validador no devolvió JSON: {salida[:300]}"],
                   "avisos": []}
    return codigo == 0, informe


def preparar_jobs(repo, guion, salida, refs=None, res="480"):
    cmd = [sys.executable,
           os.path.join(repo, "storyboard", "preparar_jobs.py"),
           "--guion", guion, "--salida", salida, "--res", res]
    if refs:
        cmd += ["--refs", refs]
    codigo, salida_txt = ejecutar(cmd, "preparar jobs")
    return codigo == 0, salida_txt


def generar_voz(solucion_dir, guion, salida, voz="es_ES-sharvard-medium",
                voces_dir=None, mapa_voces=None):
    """Genera los WAV con Piper (voz/piper_tts.py de este proyecto)."""
    cmd = [sys.executable,
           os.path.join(solucion_dir, "voz", "piper_tts.py"),
           "--guion", guion, "--salida", salida, "--voz", voz]
    if voces_dir:
        cmd += ["--voces-dir", voces_dir]
    if mapa_voces:
        cmd += ["--mapa-voces", mapa_voces]
    codigo, salida_txt = ejecutar(cmd, "generar voz")
    return codigo == 0, salida_txt


def ensamblar(repo, guion, clips, wavs, salida, musica=None, trabajo=None):
    cmd = [sys.executable,
           os.path.join(repo, "ensamblaje", "ensamblar.py"),
           "--guion", guion, "--clips", clips, "--wavs", wavs,
           "--salida", salida]
    if musica:
        cmd += ["--musica", musica]
    if trabajo:
        cmd += ["--trabajo", trabajo]
    codigo, salida_txt = ejecutar(cmd, "ensamblar")
    return codigo == 0, salida_txt


def qc(repo, video, guion, sin_whisper=False, salida_qc=None):
    cmd = [sys.executable,
           os.path.join(repo, "qc", "qc_capitulo.py"),
           "--video", video, "--guion", guion]
    if sin_whisper:
        cmd += ["--sin-whisper"]
    if salida_qc:
        cmd += ["--salida-qc", salida_qc]
    codigo, salida_txt = ejecutar(cmd, "QC")
    return codigo == 0, salida_txt


def flujo_completo(config):
    """Ejecuta el flujo local completo hasta donde se pueda.

    `config` es un dict con: repo, solucion_dir, guion, trabajo,
    clips, wavs, salida, musica (opcional), res ("480"/"720"),
    sin_whisper (bool). Devuelve un informe con un paso por fase y
    `ok` global. Se detiene en el primer paso que falla (salvo que
    falten clips: eso no es un fallo, es "esperando generación").
    """
    repo = resolver_repo(config.get("repo"))
    solucion_dir = config.get("solucion_dir") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    trabajo = config["trabajo"]
    os.makedirs(trabajo, exist_ok=True)
    guion = config["guion"]
    informe = {"pasos": [], "ok": False}

    def paso(nombre, ok, detalle):
        informe["pasos"].append({"paso": nombre, "ok": ok,
                                 "detalle": detalle})
        return ok

    ok, val = validar_guion(repo, guion)
    if not paso("validar-guion", ok,
                f"{val.get('clips', '?')} clips, "
                f"{val.get('palabras_por_minuto', '?')} pal/min; "
                f"errores: {val.get('errores', [])}"):
        return informe

    jobs = os.path.join(trabajo, "jobs.json")
    ok, detalle = preparar_jobs(repo, guion, jobs,
                                refs=config.get("refs"),
                                res=config.get("res", "480"))
    if not paso("preparar-jobs", ok, detalle):
        return informe

    ok, detalle = generar_voz(
        solucion_dir, guion, config["wavs"],
        voz=config.get("voz", "es_ES-sharvard-medium"),
        voces_dir=config.get("voces_dir"),
        mapa_voces=config.get("mapa_voces"))
    if not paso("voz-piper", ok, detalle):
        return informe

    # ¿Están todos los clips? Si no, el flujo se detiene aquí: la
    # generación de vídeo es externa (Colab/Kaggle/APIs).
    with open(guion, encoding="utf-8") as f:
        clips_guion = json.load(f)["clips"]
    faltan = [c["id"] for c in clips_guion
              if not os.path.exists(
                  os.path.join(config["clips"], c["id"] + ".mp4"))]
    if faltan:
        paso("clips-listos", False,
             f"faltan {len(faltan)}/{len(clips_guion)} clips: "
             f"{', '.join(faltan)}. Genera los clips (Colab/Kaggle/APIs), "
             "recógelos con `recolectar` y vuelve a correr `ensamblar`.")
        return informe
    paso("clips-listos", True,
         f"{len(clips_guion)}/{len(clips_guion)} clips en disco")

    ok, detalle = ensamblar(repo, guion, config["clips"], config["wavs"],
                            config["salida"], musica=config.get("musica"),
                            trabajo=os.path.join(trabajo, "ensamblaje"))
    if not paso("ensamblar", ok, detalle):
        return informe

    ok, detalle = qc(repo, config["salida"], guion,
                     sin_whisper=config.get("sin_whisper", False),
                     salida_qc=os.path.join(trabajo, "qc"))
    paso("qc", ok, detalle)
    informe["ok"] = ok
    return informe
