# Free Video Orchestrator — $0-budget AI video generation

> Split a video chapter into short clips and distribute them across **free
> GPU sources** (Google Colab, Kaggle, Lightning AI) running open-weight
> video models, with free video APIs only as a fallback. Scripts, voice-over
> (Piper TTS), assembly and QC run locally. Budget: **$0** — no card, no paid
> credits.

## Honest numbers (marked preliminary where they are)

One Fruti chapter ≈ 85 s of video ≈ 17 clips of 5 s (or 9 clips of 10 s;
cost per clip scales with duration).

| Resource | Capacity | Status of the number |
|---|---|---|
| Scripts (Pollinations / Groq) | Thousands per day | Tested (Pollinations) / documented (Groq) |
| Reference images | 10,000+/month | Documented |
| Voice (Piper TTS, local) | **Unlimited** | **Tested** (8 real WAVs, see below) |
| Recurring free GPU (Kaggle 30 h/week + Colab ~10–20 h/week) | ~40–50 GPU-h/week → **2–6 chapters/week realistic** | Kaggle **documented** (30 h/week); Colab **estimated** (no published quota; third parties: 15–30 h/week); cost 10–30 min/clip **estimated, unmeasured**; overhead 30–50% estimated |
| One-time bonuses (Lightning ~9 h + Lium ~21 h + Akash 0–6.7 h) | ~30–37 GPU-h **ONE TIME ONLY** (not weekly) | Lightning **documented** (5 signup credits); Lium **estimated** by third parties (~20.8 h); Akash **in conflict** (0 h until verified) |
| Free video APIs (Dreamina + Kling + PixVerse) | ~57 clips of 5 s/week ≈ **3 chapters/week**, watermarked | Documented (quotas from the research); Kling uses the worst case (30 credits/clip, disputed 10–30) |

**Realistic pace at $0: 2–6 chapters/week without a watermark** (Kaggle
30 h/week verified + Colab ~10–20 h/week estimated = 40–50 GPU-h/week;
at 10–30 min per 5 s clip on a T4 with 30–50% overhead for downloads,
queues and failures, that yields ~40–200 clips/week, i.e. ~2–6 chapters
of 85 s). One-time bonuses add ~30–37 GPU-h once (an initial boost, not
sustained production). The APIs add up to ~3 chapters/week extra with a
watermark if used every day. **2 chapters a day is NOT achievable at $0**
at these speeds.

> ⚠️ **First step before planning anything: test the Kaggle SMS.**
> Kaggle requires SMS verification to enable the GPU, and the SMS may not
> reach some countries. Without Kaggle, recurring total drops to Colab
> only (~10–20 h/week) and the pace to ~1–3 chapters/week.

**Quality:** 480p by default (480×832 vertical, the one verified on a free
T4). 720p is an option, with automatic fallback to 480p on out-of-memory.
API clips come out at 540p–720p depending on the service.

## Limits (read before promising anything)

1. **Quotas change without notice.** The ones in this project are from the
   research of 21 Nov 2026 (`investigacion/gpu-gratis.md`); before planning
   a month, check the quota in the real account.
2. **Kaggle requires SMS for the GPU.** The code may not reach some phone
   numbers; without it there is no Kaggle GPU and the recurring total drops
   to Colab only. Testing the SMS is the first step.
3. **Colab publishes no quota.** Heavy use blocks the GPU for 1–5 days.
   The orchestrator records usage but cannot know the limit: when Colab
   says there is no GPU, the source is paused by hand.
4. **Time per clip (10–30 min on a T4) is an unmeasured estimate.** The
   first real run on each platform measures the time and feeds
   `registro.jsonl`; until then, all "chapters/week" figures are
   preliminary.
5. **Watermark and licence on cloud APIs.** Kling, PixVerse and Hailuo
   forbid commercial use on their free plans; Dreamina does not clarify.
   Fruti videos are monetised, so those clips do not meet the terms for
   commercial use. The routes without that problem are open models on
   free GPU (open licence).
6. **Inconsistent characters across providers.** A chapter mixed between
   Wan and the APIs will have different characters. For consistency, a
   whole chapter must come from one source (or from Wan on Colab+Kaggle,
   with the same references).
7. **Wan generates silent video.** Narration (Piper) and music are added
   at assembly.
8. **Accounts not yet created** (see below): Kaggle, Lightning, Lium,
   Akash, ZeroGPU and the APIs. No account was created for this project.
9. **Google officially blocks Cuba in Gemini/Flow/AI Studio.** Colab and
   Kaggle are Google services and are listed as "unverified" for Cuba in
   the report: they may or may not work from some networks. From this VM
   (egress via the US) they are reachable.

## Layout

```
.
├── fuentes.json                  # source registry + quotas from the research
├── investigacion/gpu-gratis.md  # free-GPU research (21 Nov 2026, Spanish)
├── VERIFICACION.md              # independent verification (21 Nov 2026, Spanish)
├── orquestador/
│   ├── cola.py                  # resumable clip queue (JSON)
│   ├── fuentes.py               # registry + quota tracking
│   ├── asignar.py               # splits clips across sources
│   ├── recolectar.py            # verifies generated clips (ffprobe)
│   ├── pipeline.py              # local flow (calls the companion repo)
│   └── cli.py                   # CLI: plan, estado, recolectar, ensamblar
├── voz/piper_tts.py             # narration with Piper TTS (tested)
├── guion/llm_gratis.py          # scripts with Pollinations (no key) or Groq
├── plantillas/kaggle-generar-clips.ipynb   # generation notebook for Kaggle
├── tests/test_orquestador.py    # 31 tests, no GPU or network
└── README.md                    # this file
```

**No Python dependencies** beyond the standard library. Requires
`ffmpeg`/`ffprobe` on the PATH, and optionally `piper-tts` (voice) and
`faster-whisper` (transcription QC gates). Keys only via environment
variables (`GROQ_API_KEY`); no file stores secrets.

> **Note:** assembly (`ensamblar`) calls scripts from the separate
> `video-generator-repo` companion repository (validation, assembly, QC),
> which is **not included here**. Point to it with `--repo` or
> `VIDEO_GENERATOR_REPO` (default `~/workspace/video-generator-repo`).
> Planning, quota tracking, clip collection and voice work fully here.

## Full flow, step by step

### Step 0 — Install the local bits (once)

```bash
pip install piper-tts        # voice (optional if you use external WAVs)
# ffmpeg: https://ffmpeg.org/download.html
# Download one Spanish voice (~77 MB, once):
#   es_ES-sharvard-medium.onnx + .onnx.json from
#   https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_ES/sharvard/medium
```

### Step 1 — Script (free, no key)

```bash
python guion/llm_gratis.py --idea "Fresita discovers Celia lied to her" \
    --salida cap-01/guion.json
# Or with Groq (faster; needs GROQ_API_KEY in the environment):
#   export GROQ_API_KEY='your-key'
#   python guion/llm_gratis.py --idea "..." --salida cap-01/guion.json \
#       --proveedor groq
```

Pollinations enforces a limit of 1 response every 30–45 s (the script
waits 40 s between calls, even across runs). The script is validated
against the Fruti rules (dense dialogue, no sighs, hook in clip 1)
before it is saved as valid. You can also write the script by hand in
the same JSON format.

### Step 2 — Plan: validate, jobs, queue and assignment

```bash
python -m orquestador.cli plan --guion cap-01/guion.json --trabajo cap-01/
```

Validates the script, prepares `jobs.json`, creates the queue
(`cola.json`) and assigns each clip to the source with available quota,
in priority order (Colab → Kaggle → Lightning → Dreamina → Kling →
PixVerse). Usage is reserved at assignment. If a clip fits no source,
the plan says so: nothing is promised that does not fit.

Check the status at any time:

```bash
python -m orquestador.cli estado --trabajo cap-01/
python -m orquestador.cli capacidad   # estimated weekly capacity
```

### Step 3 — Generate the clips (external: free GPU or APIs)

**Free GPU (recommended, no watermark):**

- **Colab:** upload `jobs.json` + `refs/` to Drive and open a
  generation notebook (Runtime → GPU). No Colab notebook is included in
  this repo yet — use the Kaggle notebook below as the base.
- **Kaggle:** create a dataset with `jobs.json` + `refs/`, attach it and
  open `plantillas/kaggle-generar-clips.ipynb` (Settings → Accelerator
  → GPU). When done: **Save Version → Output** to download the clips.
- **Lightning:** use the Kaggle notebook as a base (no dedicated
  adaptation yet). Save its 5 credits for the highest-quality clips
  (L4 24 GB, official 720p script).
- **Lium:** use the Kaggle notebook as a base (no dedicated adaptation
  yet). Spend soon: the $5 bonus expires after 14 days.

The notebooks generate clip by clip, save each one as soon as it
finishes, record the real time in `registro.jsonl` and stop cleanly
before the session cut (~10.5 h). The next session resumes where it
left off.

**Free APIs (supplement, watermarked):** generate the clips assigned to
Dreamina/Kling/PixVerse on their websites, with the prompt and
reference from `jobs.json`, and download them into the clips folder.

### Step 4 — Collect and verify

```bash
python -m orquestador.cli recolectar --trabajo cap-01/ --clips cap-01/clips/
```

Checks every clip: it exists, is over 10 KB, ffprobe reads it (it has a
video stream) and lasts what the script asks (±1 s). A failing clip goes
back to pending for regeneration (max 3 attempts); a missing one stays
on hold unless you pass `--marcar-faltantes`.

### Step 5 — Voice (Piper, unlimited, local)

```bash
python voz/piper_tts.py --guion cap-01/guion.json --salida cap-01/wavs/
# A different voice per character:
#   python voz/piper_tts.py --guion ... --salida ... --mapa-voces mapa.json
```

Generates one WAV per clip. Head/tail silence is trimmed when the
companion `video-generator-repo` is available (its
`recortar_silencios.py`); otherwise the script warns and keeps the
audio untrimmed. Output is normalised to 48 kHz mono. If `piper-tts`
is not installed, the script explains how to install it and exits with
a clear error. Spanish voices: `es_ES-sharvard-medium` (tested),
`es_ES-davefx-medium`, `es_AR-daniela-high`, `es_MX-claude-high`.

### Step 6 — Assemble + QC

```bash
python -m orquestador.cli ensamblar --guion cap-01/guion.json \
    --trabajo cap-01/ --clips cap-01/clips/ --wavs cap-01/wavs/ \
    --salida cap-01/capitulo.mp4 --musica musica.mp3
```

Runs the full local flow: validate → jobs → voice → (checks all clips
are present) → assemble → QC, using the companion
`video-generator-repo`. Assembly uses the anti-desync fix (concat with
re-encoded audio + sample counting). **A chapter that fails QC is NOT
published.** With `--sin-whisper` the transcription gates are skipped
and the report marks the result NOT VERIFIED (not approved).

### Step 7 — Publishing

Captions, first comments and hashtags are prepared with your existing
publishing tools (no publishing script is included in this repo). Before
scheduling, verify no other post with the same content/slot exists, to
avoid duplicates.

## Creating the accounts (exact steps; none created here)

None of these accounts exists yet. All are free and card-free. Create
them from the browser with your email.

| Account | Steps |
|---|---|
| **Kaggle** | 1. https://www.kaggle.com → Sign Up → with Google. 2. Verify the email. 3. **Test the SMS FIRST**: in a Notebook, Settings → Accelerator → GPU T4 x2; Kaggle will ask to verify a phone number to enable the GPU (once). If the SMS never arrives, Kaggle is 0. 4. Create a Dataset with `jobs.json` + `refs/` and attach it to the notebook (Add data → Your Datasets). |
| **Lightning AI** | 1. https://lightning.ai → Sign up with Google or GitHub. 2. Create a Studio with a T4 or L4 GPU. Quota: **5 credits ONE TIME ONLY** ≈ 9 h of T4 (or ~6.3 h of L4); the other 25 require a card. |
| **Lium** | 1. https://lium.io → sign up with email and confirm it (no card). 2. **$5 bonus ONE TIME ONLY** (~21 estimated GPU-h on RTX 3090/4090). **Expires after 14 days**: spend it soon. |
| **Akash** | 1. https://akash.network → Console, sign up with email (no card). 2. **$1 bonus ONE TIME ONLY** (30 days). **Verify first** whether the trial GPU really works (the official docs contradict each other: one page says the trial includes GPUs up to RTX 3090, another that trial credits are CPU-only). Until verified, count 0 h. |
| **Hugging Face (ZeroGPU)** | 1. https://huggingface.co/join → free account with email. 2. Use existing ZeroGPU Spaces (e.g. Wan demos): 5 min of GPU/day. No dedicated notebook: manual use per Space. |
| **Dreamina** | 1. https://dreamina.capcut.com → Sign up with Google or email. 2. 120 credits/day ≈ 5 clips of 5 s/day. |
| **Kling** | 1. https://kling.ai → Sign up with Google or email. 2. 66 credits/day ≈ 2 clips of 5 s/day (worst case). |
| **PixVerse** | 1. https://pixverse.ai → Sign up with Google or email. 2. 30 credits/day (not enough for one 5 s clip at 720p; enough for ~3 s clips or less). |
| **Groq (optional, scripts)** | 1. https://console.groq.com → Sign up with Google. 2. API Keys → Create API Key. 3. `export GROQ_API_KEY='your-key'` (never in a file). No card. |

## What is verified and what is not

Verified in this project (21 Nov 2026; detail in VERIFICACION.md, in
Spanish):

- **31 tests green** (`python -m pytest tests/` or `python -m unittest
  discover -s tests`): queue, resume, quotas (daily/weekly reset, one-time
  bonuses without reset), priority assignment, collection with the 8 real
  sample clips, pipeline (validate + jobs), Pollinations rate limit,
  Piper (detection and install message).
- **CLI end to end** with the sample chapter: plan (8 clips assigned to
  Colab) → collect (8/8 verified) → status → capacity (free GPU: 90
  clips/week Kaggle alone, not counting Colab or the one-time bonuses;
  APIs: 57 clips/week).
- **Piper TTS end to end:** 8 WAVs generated with
  `es_ES-sharvard-medium` (3.0–4.5 s each, 48 kHz mono, silence
  trimmed), all inside their 5 s clips.
- **Assembly end to end:** a 40 s chapter with the sample clips + the
  Piper WAVs (drift 0.13 s, within the 0.3 s max); duration, silence
  and desync QC gates green (Whisper deliberately skipped with
  `--sin-whisper`).
- **Kaggle notebook** validated with `nbformat`, all code cells parsed.

NOT verified (pending the first real run):

- **The Kaggle SMS** (first step: if it never arrives, Kaggle = 0).
- Real time per clip on a T4 (Colab and Kaggle): 10–30 min is an estimate.
- A real generation on Kaggle (account not yet created).
- The Lium (~21 h estimated) and Akash (trial GPU in conflict) bonuses:
  untested, no account.
- ZeroGPU: time per clip unmeasured; never assigned alone.
- The real Colab quota (unpublished) and whether Colab/Kaggle work from
  every network.
- Same-character consistency in clips generated on Kaggle.
- A full chapter produced ONLY with this orchestrator + free GPU (the test
  used the sample clips, already generated).

## Environment variables

| Variable | What for |
|---|---|
| `GROQ_API_KEY` | Groq key (scripts). Optional; without it, uses Pollinations. |
| `VIDEO_GENERATOR_REPO` | Path of the companion repo (default `~/workspace/video-generator-repo`). |
| `PIPER_VOICES_DIR` | Folder with the Piper `.onnx` voices (default `~/workspace/apis-gratis-ia/pruebas/piper-voices/`). |
| `PLANTILLA_GUION` | Script template (default: the one in the repo). |

## License

MIT. The models used (Wan 2.2, Apache 2.0; Piper, GPL-3.0; the voices,
per their own licence — check before commercial use) keep their own
licences.
