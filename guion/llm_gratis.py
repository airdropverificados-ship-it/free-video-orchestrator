#!/usr/bin/env python3
"""Guiones gratis: Pollinations (sin clave, probado) o Groq (opcional).

Fuentes (informe de APIs gratis, 21 nov 2026):

  - Pollinations texto: sin registro ni clave, endpoint compatible con
    OpenAI en https://text.pollinations.ai/openai/v1/chat/completions,
    modelo `openai` (gpt-oss-20b). PROBADO: responde en español en
    ~35 s. Límite: 1 respuesta cada 30-45 s por IP. Este script respeta
    el límite esperando 40 s entre llamadas (con un archivo de estado
    en ~/.cache, para que también se respete entre corridas).
  - Groq (opcional): 1.000 req/día y 200.000 tokens/día por modelo,
    sin tarjeta. Necesita clave en la variable de entorno GROQ_API_KEY
    (nunca en un archivo). Endpoint OpenAI-compatible en
    https://api.groq.com/openai/v1/chat/completions.

El guion generado se valida con `validar_guion.py` del repo antes de
guardarse como válido; si no pasa, se guarda igual (para corregirlo a
mano) pero el script sale con error.

Uso:
    python guion/llm_gratis.py --idea "Fresita descubre que..." \\
        --salida guion.json
    python guion/llm_gratis.py --idea "..." --salida guion.json \\
        --proveedor groq --modelo gpt-oss-20b
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

POLLINATIONS_URL = ("https://text.pollinations.ai/openai/v1/"
                    "chat/completions")
POLLINATIONS_MODELO = "openai"
# Pollinations: 1 respuesta cada 30-45 s por IP. Esperamos 40 s.
POLLINATIONS_ESPERA_S = 40

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELO_DEFECTO = "gpt-oss-20b"

ESTADO_POLL_URL = os.path.join(
    os.path.expanduser("~"), ".cache", "solucion-video-gratis",
    "pollinations-ultima.json")

PLANTILLA_DEFECTO = os.path.join(
    os.path.expanduser("~"), "workspace", "video-generator-repo",
    "guion", "plantillas", "drama-fruti.txt")


def extraer_json(texto):
    """Extrae el primer objeto JSON de la respuesta del modelo."""
    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio < 0 or fin <= inicio:
        return None
    try:
        return json.loads(texto[inicio:fin + 1])
    except json.JSONDecodeError:
        return None


def leer_ultima_pollinations(ruta=ESTADO_POLL_URL):
    """Timestamp (epoch) de la última llamada a Pollinations, o None."""
    try:
        with open(ruta, encoding="utf-8") as f:
            return float(json.load(f)["ultima"])
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError):
        return None


def guardar_ultima_pollinations(ahora=None, ruta=ESTADO_POLL_URL):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"ultima": ahora or time.time()}, f)


def calcular_espera(ultima, ahora, espera_s=POLLINATIONS_ESPERA_S):
    """Segundos que faltan para respetar el rate limit (0 si ya pasó)."""
    if ultima is None:
        return 0.0
    return max(0.0, espera_s - (ahora - ultima))


def esperar_rate_limit_pollinations(ruta=ESTADO_POLL_URL):
    """Duerme lo necesario para respetar 1 req/40 s en Pollinations."""
    espera = calcular_espera(leer_ultima_pollinations(ruta), time.time())
    if espera > 0:
        print(f"Pollinations: esperando {espera:.0f} s para respetar "
              "el límite de 1 respuesta cada 30-45 s…")
        time.sleep(espera)


def llamar_openai_compatible(url, modelo, prompt, api_key=None,
                             timeout=300):
    """Llama a un endpoint compatible con la API de chat de OpenAI."""
    cuerpo = json.dumps({
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
    }).encode("utf-8")
    cabeceras = {"Content-Type": "application/json"}
    if api_key:
        cabeceras["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=cuerpo, headers=cabeceras)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        datos = json.load(resp)
    return datos["choices"][0]["message"]["content"]


def generar_con_pollinations(prompt):
    esperar_rate_limit_pollinations()
    try:
        respuesta = llamar_openai_compatible(
            POLLINATIONS_URL, POLLINATIONS_MODELO, prompt)
    finally:
        # Se registra el intento aunque falle: el límite es por IP.
        guardar_ultima_pollinations()
    return respuesta


def generar_con_groq(prompt, modelo=GROQ_MODELO_DEFECTO):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Groq necesita la clave en la variable de entorno "
            "GROQ_API_KEY (nunca en un archivo). Consíguela gratis en "
            "https://console.groq.com (sin tarjeta) y ejecuta:\n"
            "  export GROQ_API_KEY='tu-clave'\n"
            "O usa --proveedor pollinations, que no necesita clave.")
    return llamar_openai_compatible(GROQ_URL, modelo, prompt,
                                    api_key=api_key)


def validar(guion, repo=None):
    """Valida con validar_guion.py del repo (import, no subprocess)."""
    repo = repo or os.environ.get("VIDEO_GENERATOR_REPO") or \
        os.path.join(os.path.expanduser("~"), "workspace",
                     "video-generator-repo")
    sys.path.insert(0, repo)
    from guion.validar_guion import validar_guion
    return validar_guion(guion)


def generar_guion(idea, proveedor="pollinations", modelo=None,
                  plantilla=None, clips=9, duracion_clip=10, repo=None):
    """Genera y valida un guion. Devuelve (guion, informe_validacion)."""
    plantilla = plantilla or os.environ.get("PLANTILLA_GUION") \
        or PLANTILLA_DEFECTO
    with open(plantilla, encoding="utf-8") as f:
        texto_plantilla = f.read()
    prompt = texto_plantilla.replace("{IDEA}", idea) \
        .replace("{N_CLIPS}", str(clips)) \
        .replace("{DURACION_CLIP}", str(duracion_clip))

    if proveedor == "pollinations":
        print("Generando guion con Pollinations (gratis, sin clave)… "
              "(puede tardar ~1 min)")
        respuesta = generar_con_pollinations(prompt)
    elif proveedor == "groq":
        print(f"Generando guion con Groq ({modelo or GROQ_MODELO_DEFECTO})…")
        respuesta = generar_con_groq(prompt, modelo or GROQ_MODELO_DEFECTO)
    else:
        raise ValueError(f"proveedor desconocido: {proveedor}")

    guion = extraer_json(respuesta)
    if guion is None:
        raise ValueError(
            "el modelo no devolvió un JSON válido. Respuesta recibida:\n"
            + respuesta[:2000])
    informe = validar(guion, repo=repo)
    return guion, informe


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Genera un guion JSON con un LLM gratis "
                    "(Pollinations sin clave, o Groq con clave por env).")
    parser.add_argument("--idea", required=True)
    parser.add_argument("--salida", required=True)
    parser.add_argument("--proveedor", choices=["pollinations", "groq"],
                        default="pollinations")
    parser.add_argument("--modelo", default=None)
    parser.add_argument("--plantilla", default=None)
    parser.add_argument("--clips", type=int, default=9)
    parser.add_argument("--duracion-clip", type=int, default=10)
    parser.add_argument("--repo", default=None)
    args = parser.parse_args(argv)

    try:
        guion, informe = generar_guion(
            args.idea, proveedor=args.proveedor, modelo=args.modelo,
            plantilla=args.plantilla, clips=args.clips,
            duracion_clip=args.duracion_clip, repo=args.repo)
    except urllib.error.URLError as e:
        print(f"❌ No se pudo contactar al proveedor ({args.proveedor}): {e}")
        return 2
    except (RuntimeError, ValueError) as e:
        print(f"❌ {e}")
        return 1

    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(guion, f, ensure_ascii=False, indent=2)
    print(f"Guion guardado en {args.salida}: {informe['clips']} clips, "
          f"{informe['palabras']} palabras, "
          f"{informe['palabras_por_minuto']} pal/min")
    for aviso in informe["avisos"]:
        print(f"  AVISO: {aviso}")
    for error in informe["errores"]:
        print(f"  ERROR: {error}")
    if informe["errores"]:
        print("❌ El guion NO pasó la validación. Corrige los errores "
              "(o genera otro) antes de producirlo.")
        return 1
    print("✅ Guion válido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
