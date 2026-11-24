# Verificación independiente — solución de video gratis

**Fecha:** 21 de noviembre de 2026
**Verificador:** agente independiente (no participó en la investigación ni en la programación)
**Alcance:** reconciliar `investigacion/gpu-gratis.md` con el orquestador y probar
lo que se puede probar sin cuentas nuevas ni pagos. No se creó ninguna cuenta.

## Correcciones aplicadas

### `fuentes.json` (10 fuentes; antes 8)

| Cambio | Antes | Ahora | Base |
|---|---|---|---|
| Lightning AI | 1.320 min/mes (15 créd/mes ≈ 22 h T4) | **540 min, periodo `una-vez`** (5 créditos una sola vez ≈ 9 h T4) | Investigación §4 (lightning.ai/pricing) |
| Lium (nueva) | — | **1.248 min, periodo `una-vez`** ($5 una sola vez, ~20,8 h estimadas en RTX 3090/4090, expira 14 días) | Investigación §7 (hallazgo nuevo) |
| Akash (nueva) | — | **0 min, coste null (no asignable)** — conflicto en la documentación oficial | Investigación §6 |
| Kaggle | "T4/P100", sin advertencia | **"T4 ×2"** + advertencia SMS: el código a Cuba puede no llegar; probar el SMS es el primer paso | Investigación §1 |
| Colab | sin estimación | Notas con el rango de terceros (15–30 h/sem; el repo planifica 10–20) | Investigación §2 |
| Modal | — | **No incluido** (exige método de pago en archivo) | Investigación §8 |

### Código del orquestador (cambio mínimo, obligado por los datos)

El periodo `una-vez` no existía: `clave_periodo()` lanzaba `ValueError` y 2 tests
fallaban con error. Se añadió soporte mínimo:

- `orquestador/fuentes.py`: `clave_periodo("una-vez", ...)` devuelve la clave
  constante `"una-vez"` — el consumo de un bono único nunca se resetea.
- `orquestador/asignar.py`: `estimar_capacidad_semanal()` trata los bonos únicos
  explícitamente: 0 clips/semana con la nota "bono único, no recurrente: no suma
  a la capacidad semanal" (antes caían en un `else` silencioso).

### Tests (31; antes 30)

Actualizados a los números corregidos (el test viejo afirmaba 105 clips/semana
contando Lightning como mensual) y añadido `test_bono_unico_no_se_resetea`.
`_registro_sin_gpu` ahora también pausa Lium. Ver detalle en el test.

### `README.md`

- Tabla de números reescrita: recurrente ~40–50 GPU-h/sem → **2–6 capítulos/semana
  realistas** (antes: "Kaggle + Lightning ≈ 5–6 capítulos/semana"); bonos únicos
  ~30–37 GPU-h una sola vez en fila aparte. Cada número marcado como documentado,
  estimado o en conflicto.
- Aviso destacado: probar el SMS de Kaggle es el primer paso.
- Tabla de cuentas: Lightning corregido (5 créditos una sola vez), Lium y Akash
  añadidos, Kaggle con la advertencia SMS.

## Pruebas realizadas

| Prueba | Resultado |
|---|---|
| `python -m unittest discover -s tests` (31 tests) | ✅ **31/31 en verde** (baseline antes de corregir: 30/30; tras corregir fuentes.json sin tocar código: 2 fallos + 2 errores, todos por los números viejos y el periodo `una-vez` sin soporte) |
| CLI end-to-end con el capítulo ejemplo (`plan` → `recolectar` → `estado` → `capacidad`) | ✅ `plan`: 8/8 clips a Colab; `recolectar`: 8/8 verificados (5,0 s cada uno); `estado`: 8 hecho, fuentes con cuotas corregidas; `capacidad`: GPU libre 90 clips/sem (solo Kaggle) ≈ 5 capítulos, APIs 57 clips/sem ≈ 3 capítulos |
| Pollinations: generación real con la plantilla tal cual (2 intentos, ideas distintas) | ❌ **El modelo rechazó la plantilla 2/2 veces** ("Sorry, I can't comply with that"). El script lo gestionó bien: error claro, salida 1, sin crash, y respetó el rate limit (espera de 35 s entre llamadas) |
| Pollinations: sonda mínima (JSON trivial) | ✅ Endpoint funciona: devolvió `{"saludo": "hola"}` y `extraer_json` lo parseó |
| Pollinations: plantilla con "niña fresa/naranja" → "fresa/naranja joven" | ✅ **JSON válido y validador del repo APROBADO**: 3 clips, 31 palabras, 124 pal/min, 0 errores, 0 avisos |
| Piper TTS: 1 WAV real (`es_ES-sharvard-medium`) | ✅ WAV de 4,81 s / 461 KB dentro del clip de 5 s, con silencio recortado. OJO: `piper-tts` NO estaba instalado en el Python del sistema; se instaló en un venv temporal para la prueba. El mensaje de instalación del script es claro y correcto (verificado en el test) |
| Cuaderno Kaggle (`plantillas/kaggle-generar-clips.ipynb`) | ✅ Válido con nbformat 5.9.1: 15 celdas (7 código, 8 markdown); las 7 celdas de código parsean (omitiendo 2 magias IPython `!`/`%`, válidas en cuaderno); menciona `jobs.json`, `registro.jsonl`, corte a 10,5 h y Wan |
| Secretos (grep de claves/tokens/passwords en todo el repo) | ✅ **Ningún secreto**: solo referencias genéricas a `GROQ_API_KEY` por variable de entorno |

## Hallazgo principal: la plantilla de guion la rechaza Pollinations

El modelo `openai` de Pollinations (gpt-oss-20b) rechaza la plantilla
`drama-fruti.txt` tal cual. La causa casi segura es la palabra **"niña"**
("Fresita (niña fresa…)", "Celia (niña naranja…)"): cambiando solo eso por
"joven", la misma plantilla generó un guion válido que pasó el validador.
**No se modificó la plantilla** (vive en `video-generator-repo`, fuera de este
proyecto, y cambiar la descripción de los personajes es una decisión de
contenido). Acción pendiente para el siguiente paso: cambiar "niña" por
"joven" en la plantilla, o usar Groq (necesita clave; no probado aquí).

Nota: el informe previo decía que Pollinations estaba "probado". El endpoint
sigue funcionando, pero el modelo actual rechaza esta plantilla concreta. Los
modelos gratuitos cambian de comportamiento sin aviso.

## Entorno: `/tmp` casi lleno

`/tmp` es un tmpfs de 512 MB al 91% (50 MB libres, ocupados por trabajo de otros
agentes). Dos pruebas fallaron primero por "No space left on device" (instalar
`piper-tts`, escribir `jobs.json` en `/tmp`). Solución usada: trabajar en
`~/scratch-verif/` y `TMPDIR` apuntando a home. Las pruebas de este documento
usaron esa ruta; el scratch se borró al terminar.

## Qué queda sin probar y por qué

- **SMS de Kaggle**: necesita crear la cuenta y un número de teléfono. Es el
  primer paso real; sin él, Kaggle = 0 y el ritmo cae a solo Colab (~1–3
  capítulos/semana).
- **Tiempo real por clip en T4** (10–30 min, estimación): necesita una corrida
  real en Kaggle o Colab con GPU. Hasta entonces, "2–6 capítulos/semana" es
  una estimación razonada, no una medición.
- **Una generación real de Wan 2.2 en Kaggle/Colab**: necesita cuenta + GPU.
  El cuaderno está validado sintácticamente, no ejecutado.
- **Bonos de Lium (~21 h estimadas) y Akash (GPU de prueba en conflicto)**:
  necesitan cuenta. Lium expira a los 14 días de registrarse.
- **Paralelo ×2 en Kaggle** (2 clips a la vez, uno por T4): plausible pero sin
  probar; podría duplicar el rendimiento de Kaggle.
- **Groq para guiones**: necesita clave (gratis, sin tarjeta); no se creó
  ninguna cuenta.
- **Colab/Kaggle desde Cuba**: sin verificar; Google bloquea Cuba en otros
  servicios.
- **Consistencia del personaje** entre clips generados en Kaggle: sin probar.

## Números finales honestos

| Recurso | Capacidad | Estado |
|---|---|---|
| Recurrente: Kaggle 30 h/sem + Colab ~10–20 h/sem | ~40–50 GPU-h/sem → **2–6 capítulos Fruti/semana realistas** | Kaggle documentado; Colab y coste/clip estimados |
| Bonos únicos: Lightning ~9 h + Lium ~21 h + Akash 0–6,7 h | ~30–37 GPU-h **una sola vez** | Lightning documentado; Lium estimado; Akash en conflicto (0 hasta verificar) |
| APIs gratis (Dreamina + Kling + PixVerse) | ~57 clips/sem ≈ 3 capítulos/sem, con marca de agua | Documentado |
| CLI `capacidad` (solo Kaggle, sin sobrecarga, sin Colab) | 90 clips/sem ≈ 5 capítulos/sem | Estimación; dentro del rango 2–6 |

**2 capítulos al día NO es alcanzable con $0.** El ritmo realista es 2–6
capítulos/semana sin marca de agua, más hasta ~3/semana con marca de agua si se
usan las APIs a diario. Si el SMS de Kaggle falla, el ritmo cae a ~1–3
capítulos/semana solo con Colab.
