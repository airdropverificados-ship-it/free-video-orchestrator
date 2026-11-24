# Free Video Orchestrator — $0-budget AI video generation

> **In English:** this orchestrator splits a video chapter into short clips and
> distributes them across **free GPU sources** (Google Colab, Kaggle, Lightning AI)
> running open-weight video models, with free video APIs only as a fallback.
> Scripts, voice-over (Piper TTS), assembly and QC run locally. Budget: **$0**
> — no card, no paid credits. The detailed documentation below is in Spanish.

# Orquestador de generación de vídeo gratis — Fruti Novelas

Reparte los clips de un capítulo entre **todas las fuentes gratuitas**
de generación de vídeo, recoge y verifica los clips, y orquesta el
pipeline local del repositorio `video-generator-repo` (validar guion →
voz → ensamblar → QC).

**Presupuesto: $0.** Sin créditos de pago, sin tarjeta, sin
supercomputadora. La laptop hace texto, voz, ensamblaje y QC; el vídeo
se genera en GPU gratis (Colab/Kaggle/Lightning) con modelos abiertos,
y solo como complemento en APIs de vídeo gratis.

**Regla de prioridad:** GPU gratis con modelos abiertos primero (sin
marca de agua, licencia abierta, personajes consistentes). Las APIs de
vídeo gratis solo como complemento, y cada clip asignado allí queda
marcado con marca de agua y sin licencia comercial (o no clara).

---

## Números honestos (preliminares donde se indica)

Un capítulo Fruti ≈ 85 s de vídeo ≈ 17 clips de 5 s (o 9 clips de 10 s;
el coste por clip escala con la duración).

| Recurso | Capacidad | Estado del número |
|---|---|---|
| Guiones (Pollinations / Groq) | Miles al día | Probado (Pollinations) / documentado (Groq) |
| Imágenes de referencia | 10.000+/mes | Documentado |
| Voz (Piper TTS, local) | **Ilimitada** | **Probado** (8 WAV reales, ver abajo) |
| Vídeo GPU libre recurrente (Kaggle 30 h/sem + Colab ~10–20 h/sem) | ~40–50 GPU-h/semana → **2–6 capítulos/semana realistas** | Kaggle **documentado** (30 h/sem); Colab **estimado** (sin cuota publicada, terceros: 15–30 h/sem); coste 10–30 min/clip **estimado, sin medir**; sobrecarga 30–50% estimada |
| Bonos únicos (Lightning ~9 h + Lium ~21 h + Akash 0–6,7 h) | ~30–37 GPU-h **UNA SOLA VEZ** (no semanal) | Lightning **documentado** (5 créditos de registro); Lium **estimado** por terceros (~20,8 h); Akash **en conflicto** (0 h hasta verificar) |
| Vídeo APIs gratis (Dreamina + Kling + PixVerse) | ~57 clips de 5 s/semana ≈ **3 capítulos/semana**, con marca de agua | Documentado (cuotas del informe); Kling usa el peor caso (30 créd/clip, en disputa 10–30) |

**Ritmo realista con $0: 2–6 capítulos/semana sin marca de agua** (Kaggle
30 h/sem verificadas + Colab ~10–20 h/sem estimadas = 40–50 GPU-h/sem;
a 10–30 min por clip de 5 s en T4 y con 30–50% de sobrecarga por
descargas, colas y fallos, eso rinde ~40–200 clips/semana, o sea
~2–6 capítulos de 85 s). Los bonos únicos añaden ~30–37 GPU-h una sola
vez (un impulso inicial, no producción sostenida). Las APIs suman hasta
~3 capítulos/semana extra con marca de agua si se usan todos los días.
**2 capítulos al día NO es alcanzable con $0** a estos tiempos.

> ⚠️ **Primer paso antes de planificar nada: probar el SMS de Kaggle.**
> Kaggle exige verificación por SMS para activar la GPU y el SMS puede
> no llegar a algunos países. Sin Kaggle, el total recurrente cae a
> solo Colab (~10–20 h/semana) y el ritmo a ~1–3 capítulos/semana.

**Calidad:** 480p por defecto (480×832 vertical, la verificada en la T4
gratis). 720p es opción, con fallback automático a 480p si hay falta de
memoria. Los clips de API salen a 540p–720p según el servicio.

## Límites (léelos antes de prometer nada)

1. **Las cuotas cambian sin aviso.** Las de este proyecto son de la
   investigación del 21 nov 2026 (`investigacion/gpu-gratis.md`); antes
   de planificar un mes, verifica la cuota en la cuenta real.
2. **Kaggle exige SMS para la GPU.** El código a algunos números puede
   no llegar; sin él no hay GPU de Kaggle y el total recurrente cae a
   solo Colab. Probar el SMS es el primer paso.
3. **Colab no publica su cuota.** El uso intensivo bloquea la GPU de 1 a
   5 días. El orquestador registra el consumo pero no puede saber el
   límite: cuando Colab diga que no hay GPU, la fuente se pausa a mano.
4. **El tiempo por clip (10–30 min en T4) es una estimación sin medir.**
   La primera corrida real en cada plataforma mide el tiempo y alimenta
   `registro.jsonl`; hasta entonces, todos los "capítulos/semana" son
   preliminares.
5. **Marca de agua y licencia en las APIs de nube.** Kling, PixVerse y
   Hailuo prohíben el uso comercial en sus planes gratis; Dreamina no lo
   aclara. Los vídeos de Fruti se monetizan, así que esos clips no
   cumplen los términos para uso comercial. Las vías sin ese problema
   son los modelos abiertos en GPU gratis (licencia abierta).
6. **Personajes inconsistentes entre proveedores.** Un capítulo mezclado
   entre Wan y las APIs tendrá personajes distintos. Para consistencia,
   un capítulo entero debe salir de la misma fuente (o de Wan en
   Colab+Kaggle, con las mismas referencias).
7. **Wan genera vídeo mudo.** La narración (Piper) y la música se añaden
   en el ensamblaje.
8. **Cuentas pendientes de crear** (ver abajo): Kaggle, Lightning,
   Lium, Akash, ZeroGPU y las APIs. No se creó ninguna cuenta para este
   proyecto.
9. **Cuba:** Google bloquea oficialmente Cuba en Gemini/Flow/AI Studio.
   Colab y Kaggle son de Google y figuran como "sin verificar" para
   Cuba en el informe: pueden funcionar o no desde algunas redes.
   Desde esta VM (salida por EE. UU.) sí son accesibles.

---

## Estructura

```
solucion-video-gratis/
├── fuentes.json                  # registro de fuentes + cuotas de la investigación
├── investigacion/gpu-gratis.md  # investigación de GPU gratis (21 nov 2026)
├── VERIFICACION.md              # verificación independiente (21 nov 2026)
├── orquestador/
│   ├── cola.py                  # cola de clips reanudable (JSON)
│   ├── fuentes.py               # registro + seguimiento de cuotas
│   ├── asignar.py               # reparte clips entre fuentes
│   ├── recolectar.py            # verifica los clips generados (ffprobe)
│   ├── pipeline.py              # flujo local (llama al repo por subprocess)
│   └── cli.py                   # CLI: plan, estado, recolectar, ensamblar
├── voz/piper_tts.py             # narración con Piper TTS (probado)
├── guion/llm_gratis.py          # guiones con Pollinations (sin clave) o Groq
├── plantillas/kaggle-generar-clips.ipynb   # cuaderno de generación para Kaggle
├── tests/test_orquestador.py    # 31 tests, sin GPU ni red
└── README.md                    # este archivo
```

**Sin dependencias de Python** salvo la biblioteca estándar. Requiere
`ffmpeg`/`ffprobe` en el PATH, y opcionalmente `piper-tts` (voz) y
`faster-whisper` (puertas de QC con transcripción). Las claves solo por
variables de entorno (`GROQ_API_KEY`); ningún archivo guarda secretos.

---

## Flujo completo paso a paso

### Paso 0 — Instalar lo local (una sola vez)

```bash
pip install piper-tts        # voz (opcional si usas WAV externos)
# ffmpeg: https://ffmpeg.org/download.html (en la laptop)
# Descargar una voz en español (~77 MB, una sola vez):
#   es_ES-sharvard-medium.onnx + .onnx.json desde
#   https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_ES/sharvard/medium
```

El repo `video-generator-repo` debe estar en
`~/workspace/video-generator-repo` (o pasa `--repo` / define
`VIDEO_GENERATOR_REPO`).

### Paso 1 — Guion (gratis, sin clave)

```bash
python guion/llm_gratis.py --idea "Fresita descubre que Celia le mintió" \
    --salida cap-01/guion.json
# O con Groq (más rápido; necesita GROQ_API_KEY en el entorno):
#   export GROQ_API_KEY='tu-clave'
#   python guion/llm_gratis.py --idea "..." --salida cap-01/guion.json \
#       --proveedor groq
```

Pollinations respeta su límite de 1 respuesta cada 30–45 s (el script
espera 40 s entre llamadas, incluso entre corridas). El guion se valida
con las reglas Fruti (diálogo denso, sin suspiros, gancho en el clip 1)
antes de guardarse como válido. También puedes escribir el guion a mano
copiando `ejemplos/capitulo-ejemplo/guion-ejemplo.json` del repo.

### Paso 2 — Plan: validar, jobs, cola y asignación

```bash
python -m orquestador.cli plan --guion cap-01/guion.json --trabajo cap-01/
```

Valida el guion, prepara `jobs.json`, crea la cola (`cola.json`) y
asigna cada clip a la fuente con cuota disponible, en orden de
prioridad (Colab → Kaggle → Lightning → Dreamina → Kling → PixVerse).
El consumo se reserva al asignar. Si un clip no cabe en ninguna fuente,
el plan lo dice: no se promete lo que no cabe.

Consulta el estado en cualquier momento:

```bash
python -m orquestador.cli estado --trabajo cap-01/
python -m orquestador.cli capacidad   # capacidad semanal estimada
```

### Paso 3 — Generar los clips (externo: GPU gratis o APIs)

**GPU gratis (recomendado, sin marca de agua):**

- **Colab:** sube `jobs.json` + `refs/` a Drive y abre
  `colab/generar-clips.ipynb` del repo (Entorno → GPU).
- **Kaggle:** crea un dataset con `jobs.json` + `refs/`, adjúntalo y
  abre `plantillas/kaggle-generar-clips.ipynb` (Settings → Accelerator
  → GPU). Al terminar: **Save Version → Output** para descargar los
  clips.
- **Lightning:** usa el cuaderno de Kaggle como base (sin adaptación
  propia todavía). Guardar sus 5 créditos para los clips de máxima
  calidad (L4 24 GB, script oficial 720p).
- **Lium:** usa el cuaderno de Kaggle como base (sin adaptación propia
  todavía). Gastar pronto: el bono de $5 expira a los 14 días.

Los cuadernos generan clip por clip, guardan cada uno en cuanto
termina, registran el tiempo real en `registro.jsonl` y se detienen
limpios antes del corte de sesión (~10,5 h). La siguiente sesión
retoma donde quedó.

**APIs gratis (complemento, con marca de agua):** genera los clips
asignados a Dreamina/Kling/PixVerse en sus webs, con el prompt y la
referencia de `jobs.json`, y descárgalos a la carpeta de clips.

### Paso 4 — Recolectar y verificar

```bash
python -m orquestador.cli recolectar --trabajo cap-01/ --clips cap-01/clips/
```

Comprueba cada clip: existe, pesa más de 10 KB, ffprobe lo lee (tiene
stream de vídeo) y dura lo que el guion pide (±1 s). Un clip que falla
vuelve a pendiente para regenerarse (máx. 3 intentos); uno que no
aparece se deja en espera salvo que pases `--marcar-faltantes`.

### Paso 5 — Voz (Piper, ilimitada, local)

```bash
python voz/piper_tts.py --guion cap-01/guion.json --salida cap-01/wavs/
# Una voz distinta por personaje:
#   python voz/piper_tts.py --guion ... --salida ... --mapa-voces mapa.json
```

Genera un WAV por clip y recorta el silencio de cabeza/cola con
`recortar_silencios.py` del repo (normaliza a 48 kHz mono). Si
`piper-tts` no está instalado, el script explica cómo instalarlo y sale
con error claro. Voces en español: `es_ES-sharvard-medium` (probada),
`es_ES-davefx-medium`, `es_AR-daniela-high`, `es_MX-claude-high`.

### Paso 6 — Ensamblar + QC

```bash
python -m orquestador.cli ensamblar --guion cap-01/guion.json \
    --trabajo cap-01/ --clips cap-01/clips/ --wavs cap-01/wavs/ \
    --salida cap-01/capitulo.mp4 --musica musica.mp3
```

Ejecuta el flujo local completo: validar → jobs → voz → (comprueba que
estén todos los clips) → ensamblar → QC. El ensamblaje usa la
corrección anti-desync (concat con re-codificación de audio + conteo de
muestras). **Un capítulo que no pasa el QC NO se publica.** Con
`--sin-whisper` se saltan las puertas de transcripción y el informe lo
marca como NO VERIFICADO (no como aprobado).

### Paso 7 — Publicación

```bash
python publicacion/preparar_post.py --guion cap-01/guion.json \
    --salida cap-01/posts/
```

Prepara caption + primer comentario + hashtags (script del repo). La
programación se hace con las herramientas existentes (CLI de Facebook,
etc.). Regla anti-duplicados: verificar antes de programar que no
existe otro post con el mismo contenido/slot.

---

## Crear las cuentas (pasos exactos, sin crear ninguna aquí)

Ninguna de estas cuentas existe todavía. Todas son gratis y sin
tarjeta. Se crean desde el navegador con tu correo.

| Cuenta | Pasos |
|---|---|
| **Kaggle** | 1. https://www.kaggle.com → Sign Up → con Google. 2. Verificar el correo. 3. **PROBAR PRIMERO el SMS**: en un Notebook, Settings → Accelerator → GPU T4 x2; Kaggle pedirá verificar un número de teléfono para activar la GPU (una sola vez). Si el SMS no llega, Kaggle queda en 0. 4. Crear un Dataset con `jobs.json` + `refs/` y adjuntarlo al cuaderno (Add data → Your Datasets). |
| **Lightning AI** | 1. https://lightning.ai → Sign up con Google o GitHub. 2. Crear un Studio con GPU T4 o L4. Cuota: **5 créditos UNA SOLA VEZ** ≈ 9 h de T4 (o ~6,3 h de L4); los 25 restantes exigen tarjeta. |
| **Lium** | 1. https://lium.io → registro con email y confirmarlo (sin tarjeta). 2. Bono de **$5 UNA SOLA VEZ** (~21 GPU-h estimadas en RTX 3090/4090). **Expira a los 14 días**: gastarlo pronto. |
| **Akash** | 1. https://akash.network → Console, registro con email (sin tarjeta). 2. Bono de **$1 UNA SOLA VEZ** (30 días). **Verificar primero** si la GPU de prueba funciona de verdad (la documentación oficial se contradice: una página dice que la prueba incluye GPU hasta RTX 3090, otra que los créditos de prueba son solo CPU). Hasta verificar, se cuentan 0 h. |
| **Hugging Face (ZeroGPU)** | 1. https://huggingface.co/join → cuenta gratis con correo. 2. Usar Spaces ZeroGPU existentes (p. ej. demos de Wan): 5 min de GPU/día. No hay cuaderno propio: es uso manual por Space. |
| **Dreamina** | 1. https://dreamina.capcut.com → Sign up con Google o correo. 2. 120 créditos/día ≈ 5 clips de 5 s/día. |
| **Kling** | 1. https://kling.ai → Sign up con Google o correo. 2. 66 créditos/día ≈ 2 clips de 5 s/día (peor caso). |
| **PixVerse** | 1. https://pixverse.ai → Sign up con Google o correo. 2. 30 créditos/día (no alcanzan para un clip de 5 s a 720p; sirven para clips de ~3 s o menos). |
| **Groq (opcional, guiones)** | 1. https://console.groq.com → Sign up con Google. 2. API Keys → Create API Key. 3. `export GROQ_API_KEY='la-clave'` (nunca en un archivo). Sin tarjeta. |

---

## Qué está verificado y qué no

Verificado en este proyecto (21 nov 2026; detalle en VERIFICACION.md):

- **31 tests en verde** (`python -m unittest discover -s tests`): cola,
  reanudación, cuotas (reseteo diario/semanal, bonos únicos sin
  reseteo), asignación por prioridad, recolecta con los 8 clips reales
  de la muestra, pipeline (validar + jobs), rate limit de Pollinations,
  Piper (detección y mensaje de instalación).
- **CLI de punta a punta** con el capítulo de ejemplo: plan (8 clips
  asignados a Colab) → recolecta (8/8 verificados) → estado → capacidad
  (GPU libre: 90 clips/semana solo Kaggle, sin contar Colab ni los
  bonos únicos; APIs: 57 clips/semana).
- **Piper TTS de punta a punta:** 8 WAV generados con
  `es_ES-sharvard-medium` (3,0–4,5 s cada uno, 48 kHz mono, silencio
  recortado), todos dentro de sus clips de 5 s.
- **Ensamblaje de punta a punta:** capítulo de 40 s con los clips de la
  muestra + los WAV de Piper (drift 0,13 s, dentro del máx. 0,3 s);
  puertas de QC de duración, silencio y desync en verde (Whisper
  saltado a propósito con `--sin-whisper`).
- **Cuaderno de Kaggle** validado con `nbformat` y con todas sus celdas
  de código parseadas.

NO verificado (pendiente de la primera corrida real):

- **El SMS de Kaggle a Cuba** (primer paso: si no llega, Kaggle = 0).
- Tiempo real por clip en T4 (Colab y Kaggle): 10–30 min es estimación.
- Una generación real en Kaggle (cuenta pendiente de crear).
- Los bonos de Lium (~21 h estimadas) y Akash (GPU de prueba en
  conflicto): sin probar, sin cuenta.
- ZeroGPU: tiempo por clip sin medir; no se asigna solo.
- La cuota real de Colab (no publicada) y si Colab/Kaggle funcionan
  desde Cuba.
- Consistencia del mismo personaje en clips generados en Kaggle.
- Un capítulo completo producido SOLO con este orquestador + GPU gratis
  (la prueba usó los clips de la muestra, ya generados).

## Variables de entorno

| Variable | Para qué |
|---|---|
| `GROQ_API_KEY` | Clave de Groq (guiones). Opcional; sin ella, usa Pollinations. |
| `VIDEO_GENERATOR_REPO` | Ruta del repo (por defecto `~/workspace/video-generator-repo`). |
| `PIPER_VOICES_DIR` | Carpeta con los `.onnx` de Piper (por defecto `~/workspace/apis-gratis-ia/pruebas/piper-voices/`). |
| `PLANTILLA_GUION` | Plantilla de guion (por defecto la del repo). |

## Licencia

MIT. Los modelos usados (Wan 2.2, Apache 2.0; Piper, GPL-3.0; las
voces, según su licencia — revisar antes de uso comercial) mantienen
sus propias licencias.
