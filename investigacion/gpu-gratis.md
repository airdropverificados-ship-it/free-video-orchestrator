# GPU gratis para video con IA (modelos abiertos) — Investigación verificada

**Fecha:** 21 de noviembre de 2026
**Contexto:** presupuesto $0 absoluto: sin tarjeta, sin depósito, sin pruebas que pidan pago
**Objetivo:** todas las fuentes de GPU gratis, más allá de Google Colab, para generar clips de video con modelos abiertos (Wan 2.2, HunyuanVideo, Mochi 1, LTX-Video, CogVideoX).
**Método:** cada servicio se verificó en su página oficial de precios o documentación (enlace + fecha en cada ficha), o en verificaciones fechadas de terceros que citan la página oficial. No se creó ninguna cuenta. Donde dos fuentes oficiales se contradicen, se marca el conflicto en vez de elegir un bando.
**Reglas:** solo uso legítimo de capas gratis. Nada de cuentas falsas, nada de evadir cuotas, nada de violar términos de servicio. Una sola cuenta por persona y servicio, como exigen sus términos.

Amplía el informe previo: `~/workspace/apis-gratis-ia/informe.md` (§6). **Dos correcciones importantes a ese informe:** (1) Lightning AI ya NO da 15 créditos/mes: ahora son 5 créditos una sola vez al registrarse (los 25 restantes exigen tarjeta). (2) Kaggle retiró el P100 el 15 de septiembre de 2026: ahora solo queda T4 ×2.

## Nota técnica previa: qué necesita Wan 2.2 TI2V-5B de verdad

El encargo decía «~22 GB de pesos». La cifra exacta depende del formato:

- **README oficial de Wan 2.2** (github.com/Wan-Video/Wan2.2, leído 4 nov 2026): el script oficial de TI2V-5B a 720p corre «en una GPU con al menos 24 GB de VRAM (p. ej. RTX 4090)», con `--offload_model True --convert_model_dtype --t5_cpu`. Sin optimización, un video de 5 s a 720p tarda **menos de 9 minutos en una GPU de consumo** (clase RTX 4090).
- **Archivo único BF16** (`wan2.2_ti2v_5B_fp16.safetensors`): ~10,5 GB en disco; el repositorio completo en Hugging Face pesa ~34 GB.
- **ComfyUI** (tutorial oficial): el modelo 5B «debería caber bien en 8 GB de VRAM con el offloading nativo de ComfyUI». La variante **GGUF Q4_K_M** baja a **6 GB de VRAM** y 6,1 GB en disco (480p, 81 fotogramas).
- **T4 (16 GB, Turing SM75): NO tiene BF16 nativo** (los modelos modernos en BF16 se ejecutan emulados, más lentos) pero SÍ tiene tensor cores FP16. En una T4, Wan 2.2 TI2V-5B cabe por la vía ComfyUI-offload o GGUF, no por el script oficial a 720p.
- **Otros modelos (aprox., sin verificar en detalle):** Wan 2.2 A14B exige 80 GB en el script oficial (8 GB con offload en ComfyUI, muy lento); HunyuanVideo original ~45–60 GB, HunyuanVideo-1.5 mínimo 14 GB con offload; Mochi 1 (10B) ~24 GB+; LTX-Video 2.3 destilado (8B) cabe en 16 GB (~20–40 s por clip de 5 s según una fuente); CogVideoX-5B ~20–24 GB. **En la práctica, en T4 de 16 GB los candidatos realistas son Wan 2.2 TI2V-5B (GGUF/offload), LTX destilado y HunyuanVideo-1.5.**

## Tabla resumen

| Servicio | GPU gratis | Cuota gratis | Tarjeta | Teléfono | Cuba | ¿Wan 2.2 5B? | Estado |
|---|---|---|---|---|---|---|---|
| **Kaggle Notebooks** | 2× T4 (16 GB c/u) | **30 GPU-h/semana**, sesiones 12 h | No | **Sí (SMS)** | Sin verificar | Sí, vía GGUF/offload (no script oficial 720p) | ✅ Verificado |
| **Google Colab Free** | T4 (16 GB) | Sin cuota publicada (terceros: ~15–30 h/sem) | No | No | Sin verificar | Sí, vía GGUF/offload | ✅ Verificado |
| **HF ZeroGPU Spaces** | RTX Pro 6000 Blackwell, 48 GB (mitad) | **5 min/día** | No | No | Sin verificar | No práctico (límite por llamada) | ✅ Verificado |
| **Lightning AI** | T4 16 GB / L4 24 GB / A100 / H100… | **5 créditos una sola vez** (≈9 h T4) | No (25 más sí la exigen) | Sin verificar | Sin verificar | Sí (L4 24 GB: script oficial) | ✅ Verificado |
| **Paperspace Gradient** | M4000 (8 GB, Maxwell) | Sin tope de horas publicado, sesiones 6 h | Sin confirmar | No | Sin verificar | No viable (sin tensor cores) | ✅ Verificado |
| **Akash Network** | Hasta RTX 3090 (24 GB) | **$1 una sola vez**, 30 días | No | No | Sin verificar | Sí, si la GPU de prueba funciona | ⚠️ Verificado con conflicto |
| **Lium** | RTX 3090/4090/5090, H100… | **$5 una sola vez**, 14 días | No (email) | No | Sin verificar | Sí (3090/4090: 24 GB) | ✅ Verificado |
| Modal | T4–H100 | $30/mes | **Sí, obligatoria** | — | — | Sí, pero inaccesible | ❌ Excluido (método de pago obligatorio) |
| RunPod | RTX 3090–B300 | Ninguna (bono solo tras cargar $10) | Sí (depósito) | — | — | — | ❌ Excluido |
| Vast.ai | Marketplace | Ninguna (depósito mín. $5) | Sí | — | — | — | ❌ Excluido |
| Hyperbolic | H100/H200/B200 | Ninguna GPU gratis ($1 inferencia con teléfono) | Sí ($5 depósito Pro) | Sí | — | — | ❌ Excluido |
| DeepInfra | H100/B200 | Ninguna | **Sí** | — | — | — | ❌ Excluido |
| Novita AI | RTX 4090/H100 | $100, pero solo CPU/RAM Sandbox | No | No | — | No (crédito no cubre GPU) | ❌ Excluido para GPU |
| Prime Intellect | H100/H200/B300 | Ninguna | Sí | — | — | — | ❌ Excluido |
| Gensyn | Ninguna (tú aportas hardware) | — | No | No | — | No | ❌ Excluido (dirección invertida) |
| Theta EdgeCloud | RTX 3090–H200 | Ninguna publicada | Sin verificar | — | — | — | ❌ Excluido (sin crédito documentado) |
| Oracle Cloud | Ninguna (Always Free es solo CPU) | $300/30 días (trial) | **Sí** | Sí | Sin verificar | No | ❌ Excluido |
| Google Cloud | Ninguna en trial | $300/90 días | **Sí** | — | No (Google bloquea Cuba) | No (trial no admite GPU) | ❌ Excluido |
| Lambda | A10–B200 | Ninguna publicada ($10–$15 citados sin confirmar) | Sí (pre-autorización $10) | — | — | — | ⚠️ Sin verificar |
| SaladCloud | RTX 3060–5090 | Ninguna (FAQ: sin trial) | Sí (prepago) | — | — | — | ❌ Excluido |
| SageMaker Studio Lab | T4 | 4 GPU-h/día | No | Sí | — | Sí, pero cerrado | ❌ Excluido (cerrado a nuevos usuarios 30 jul 2026) |
| Cerebrium | T4–B200 | Ninguna (plan gratis, cómputo de pago) | Sin confirmar | — | — | — | ❌ Excluido |
| Crusoe | Serverless | $5 solo serverless | **Sí** | — | — | No (no GPU cruda) | ❌ Excluido |
| OVHcloud | L4/A100/H100 | $200/1 mes | **Sí (+ autofacturación)** | — | — | — | ❌ Excluido |
| DigitalOcean | GPU Droplets | $200/60 días | **Sí** | — | — | No (GPU excluidas del trial) | ❌ Excluido |
| Azure / AWS | Varias | $200 / $100 | **Sí** | — | — | — | ❌ Excluido |
| Beam | — | Retiró los $30/mes en sep 2026 | — | — | — | — | ❌ Excluido (oferta muerta) |
| Thunder Compute | A6000/L40 | $20 | No | No | — | — | ❌ Excluido (solo estudiantes EE. UU.) |
| Jarvislabs / TensorDock / Spheron | Varias | Ninguna (depósitos $5–$15) | Sí | — | — | — | ❌ Excluido |

---

## Fichas — servicios verificados con GPU gratis real

### 1. Kaggle Notebooks — la mejor fuente recurrente ✅ Verificado

- **Enlace oficial:** https://www.kaggle.com/docs/notebooks · https://www.kaggle.com/docs/efficient-gpu-usage (cuota confirmada en docs de Kaggle y en post del personal de Kaggle, discusión 361104; P100 retirado el 15 sep 2026, anuncio 735239)
- **GPU:** 2× NVIDIA T4 (16 GB cada una), 4 vCPU, 29 GB RAM, 73 GB disco. El P100 (16 GB) se retiró el 15 sep 2026 y los notebooks se migraron a T4 ×2 automáticamente.
- **Cuota gratis:** **30 GPU-horas/semana** (las docs dicen «30 horas o a veces más según la demanda» — 30 es el suelo). **Una hora en T4 ×2 consume UNA hora de cuota, no dos** (confirmado por personal de Kaggle). Sesiones de hasta 12 h; 2 sesiones simultáneas. Reset semanal (las fuentes discrepan: sábado 00:00 UTC o domingo por la noche). Pool aparte: 20 h/semana de TPU v3-8 (inútil para Wan: los modelos de video usan CUDA, no TPU).
- **Tarjeta:** No. **Teléfono: SÍ — verificación por SMS obligatoria para activar GPU/TPU** (una sola vez; un número por cuenta). **Riesgo: el SMS puede no llegar a algunos países** (mismo riesgo ya señalado con Mistral). Sin el SMS no hay GPU.
- **Cuba:** Sin verificar (Kaggle es de Google; Google bloquea Cuba en otros servicios, pero Kaggle no publica bloqueo).
- **Cómo se ejecuta:** notebooks Jupyter en el navegador; ejecución en segundo plano (se puede cerrar el navegador, el notebook sigue hasta 12 h); API oficial `kaggle kernels push/status/output` (uso legítimo documentado, no scraping). Internet activable por notebook.
- **¿Wan 2.2 TI2V-5B?** Sí, con matices: cada T4 tiene 16 GB, así que el script oficial a 720p (24 GB) NO cabe en una sola T4; sí caben la vía ComfyUI con offload (8 GB) y la GGUF Q4_K_M (6 GB, 480p). **Ventaja única: con T4 ×2 se pueden lanzar 2 clips en paralelo (uno por GPU), duplicando el rendimiento por hora de cuota** — plausible, pendiente de probar. T4 sin BF16 nativo: usar FP16 o cuantización.
- **Límites:** disco de salida persistente 20 GB por notebook; la cuota se consume también si el notebook está inactivo (parar limpio al terminar).

### 2. Google Colab Free — segunda fuente recurrente ✅ Verificado

- **Enlace oficial:** https://colab.research.google.com (FAQ y cuaderno de ayuda de Colab; límites revisados nov 2026 en fastero.com/blog/google-colab-limits y freakyjolly.com)
- **GPU:** NVIDIA T4 (16 GB) «sujeto a cuota y disponibilidad». En horas punta puede que solo haya CPU. L4, A100, H100 y G4 (RTX PRO 6000 96 GB) son solo de pago desde agosto 2026.
- **Cuota gratis:** **Google NO publica la cuota.** Usuarios y guías estiman ~15–30 GPU-h/semana; el uso intensivo bloquea la GPU de 1 a 5 días («You cannot currently connect to a GPU due to usage limits»). Sesiones de hasta 12 h; desconexión por inactividad (~90 min); al cerrar el navegador la ejecución se detiene (solo Pro+ sigue hasta 24 h). Las interfaces web (ComfyUI/Gradio por túnel), SSH y escritorios remotos **necesitan saldo de pago desde 2026** — en gratis solo notebooks con código.
- **Tarjeta:** No. **Teléfono:** No.
- **Cuba:** Sin verificar (Google bloquea Cuba oficialmente en Gemini, Flow y AI Studio; Colab no publica bloqueo, pero es servicio de Google).
- **Cómo se ejecuta:** notebook Jupyter en el navegador; ~12 GB de RAM medidos en runtime gratis (2026).
- **¿Wan 2.2 TI2V-5B?** Sí, igual que Kaggle: vía GGUF u offload, no el script oficial 720p. Sin BF16 nativo en T4. Sin interfaz web: hay que correr el modelo por código (diffusers/ComfyUI en modo API sin túnel, o scripts directos).
- **Límites:** cuota opaca y variable; no planificar producción ajustada sobre Colab gratis sin margen.

### 3. Hugging Face ZeroGPU Spaces — GPU potentísima, minutos contados ✅ Verificado

- **Enlace oficial:** https://huggingface.co/docs/hub/spaces-zerogpu (leído 21 nov 2026; confirmado también en https://huggingface.co/docs/hub/spaces-api-endpoints)
- **GPU:** NVIDIA RTX Pro 6000 Blackwell. Tamaño `large` (por defecto): media tarjeta, **48 GB VRAM**, coste de cuota 1×. Tamaño `xlarge`: tarjeta completa, 96 GB, coste 2×.
- **Cuota gratis:** **5 minutos de GPU al día** con cuenta gratis (2 min sin cuenta; PRO 40 min). El reset es 24 h exactas después del primer uso, no a medianoche. Cuentas gratis en buen estado (email verificado, cuenta con más de 30 días) pueden **alojar hasta 2 Spaces ZeroGPU**. Cola compartida con prioridad media para cuentas gratis.
- **Tarjeta:** No. **Teléfono:** No.
- **Cuba:** Sin verificar.
- **Cómo se ejecuta:** solo Spaces Gradio con funciones decoradas `@spaces.GPU` (PyTorch). No es un notebook ni una VM: es GPU bajo demanda por llamada de función. Límite por defecto de 60 s por función GPU según una revisión (sep 2026) — sin confirmar en docs oficiales.
- **¿Wan 2.2 TI2V-5B?** **No práctico para producir clips.** 5 min/día en una GPU de 48 GB suena bien, pero un clip de 5 s tarda varios minutos incluso en GPU rápida, y el modelo de ejecución (funciones Gradio con límite de tiempo por llamada + cola) no está hecho para renders largos. Útil como mucho para 1 micro-prueba al día. **No se cuenta en el total de clips semanales.**
- **Nota:** la antigua Inference API gratuita de HF ya no existe (0 créditos/mes en cuentas gratis, verificado en el informe previo).

### 4. Lightning AI — CORRECCIÓN: ya no es mensual, es un bono único ✅ Verificado

- **Enlace oficial:** https://lightning.ai/pricing (leído 21 nov 2026; FAQ de facturación en la misma página)
- **GPU:** T4 16 GB ($0,55/h), L4 24 GB ($0,79/h), A100 40 GB ($2,19/h), L40S 48 GB ($3,54/h), H200 141 GB ($4,50/h), RTX PRO 6000 96 GB ($4,64/h), H100 80 GB ($5,45/h), B200 180 GB ($9,86/h). Facturación por segundo. Máquinas interrumpibles hasta 80% más baratas.
- **Cuota gratis:** **5 créditos al registrarse (1 crédito = $1), UNA SOLA VEZ, sin tarjeta. Los 25 créditos restantes (hasta 30) exigen añadir una tarjeta.** Los créditos no usados expiran a los 12 meses. **Corrección al informe previo:** el plan ya NO da 15 créditos/mes; el modelo cambió a bono único de registro. 1 Studio CPU gratis con reinicio obligatorio cada 4 h. Sesiones A100/H100/H200 limitadas a 4 h; T4/L4/L40S sin límite de sesión. Hasta 2 GPU simultáneas.
- **Tarjeta:** No para los 5 créditos iniciales. **Teléfono:** sin verificar (una guía de marzo 2026 mencionaba verificación telefónica para horas GPU; no confirmado en la página actual).
- **Cuba:** Sin verificar.
- **Cómo se ejecuta:** Studios en el navegador (VS Code + JupyterLab), entorno persistente (50 GB almacenamiento; primeros 10 GB gratis, luego $0,10/GB/mes — ojo: el almacenamiento por encima de 10 GB consume créditos).
- **¿Wan 2.2 TI2V-5B?** Sí. Con 5 créditos: ~9 h de T4 (vía GGUF/offload) o ~6,3 h de L4 24 GB (el script oficial 720p SÍ cabe en la L4). En interrumpible podría rendir más, sin cuantificar oficialmente para 5 créditos (el «~50 GPU-h» que anuncia Lightning es con los 30 créditos completos, que exigen tarjeta).
- **Valor real:** bono único de ~9 h T4. Útil una vez, no recurrente.

### 5. Paperspace Gradient (DigitalOcean) — gratis pero GPU demasiado vieja ✅ Verificado

- **Enlace oficial:** docs.digitalocean.com (docs de Paperspace; revisado nov 2026 en fastero.com/blog/paperspace-gradient y wheredoirunthis.com/products/paperspace)
- **GPU gratis:** NVIDIA Quadro **M4000 (8 GB, Maxwell, 2015)** + máquina CPU C4. Sesiones de hasta 6 h en máquinas gratis (apagado automático; 1 h por inactividad), 5 GB almacenamiento, notebooks públicos en el plan gratis, cola cuando las máquinas gratis están ocupadas. Un solo notebook a la vez.
- **Cuota gratis:** sin tope de horas publicado — GPU gratis «según disponibilidad». Planes de pago (Pro $8/mes, Growth $39/mes) añaden GPUs gratis mejores (hasta A100 80 GB en Growth), pero son de pago.
- **Tarjeta:** sin confirmar (una fuente la marca «no confirmada»). **Teléfono:** No.
- **Cuba:** Sin verificar.
- **Cómo se ejecuta:** notebooks Jupyter gestionados (Gradient Notebooks).
- **¿Wan 2.2 TI2V-5B?** **No viable.** La M4000 es Maxwell: sin tensor cores, sin FP16/BF16 acelerado, 8 GB. Aunque la GGUF «cabe» en 6 GB en teoría, la velocidad en una Maxwell de 2015 sería inviable y las versiones modernas de PyTorch/CUDA tienen soporte limitado para esa arquitectura. **No se cuenta en el total de clips.**
- **Advertencia:** DigitalOcean (compró Paperspace en 2023) dice en su FAQ que los usuarios existentes mantienen acceso mientras que **los nuevos usuarios deben registrarse en los productos de IA de DigitalOcean**; nada nuevo desde diciembre 2023. El servicio sigue funcionando (nov 2026), pero es una vía en declive.

### 6. Akash Network — $1 de prueba, con conflicto en la documentación ⚠️ Verificado con conflicto

- **Enlace oficial:** https://akash.network/docs/getting-started/quick-start/ (leído directamente 21 nov 2026) y https://akash.network/docs/getting-started/console-onboarding/
- **GPU:** en prueba, «GPUs hasta la RTX 3090» (24 GB) según la guía Quick Start. RTX 4090/5090, A100, H100, H200, B200 requieren cuenta no-trial (con método de pago).
- **Cuota gratis:** **$1 en créditos, una sola vez, ventana de 30 días.** Despliegues de máximo 24 h cada uno (se puede redesplegar dentro de la ventana). Sin tarjeta: solo email o cuenta Google/GitHub.
- **⚠️ CONFLICTO entre dos páginas oficiales:** la Quick Start dice explícitamente que en la prueba hay GPUs hasta la RTX 3090 (con FAQ dedicada). Pero la Guía de Onboarding de la Consola dice «GPU deployments require adding credits first — trial credits are CPU-only» (los créditos de prueba son solo CPU). **No se puede prometer que la GPU de prueba funcione hasta probarlo una vez.** Si funciona: a ~$0,15/h por una RTX 3090 (tarifa rastreada, varía por proveedor), $1 ≈ 6,7 GPU-horas (estimación).
- **Tarjeta:** No (para la prueba). **Teléfono:** No.
- **Cuba:** Sin verificar. La ruta sin permiso (con billetera Keplr, sin KYC) existe pero requiere fondos en ACT/AKT (cripto), fuera del presupuesto $0.
- **Cómo se ejecuta:** consola web con plantillas Docker de un clic (incluye plantilla ComfyUI), o SDL (Stack Definition Language) propio, CLI y API. Los proveedores pujan por alojar el despliegue.
- **¿Wan 2.2 TI2V-5B?** Sí, si la GPU de prueba funciona: una RTX 3090 (24 GB) corre el script oficial 720p. La plantilla ComfyUI de Akash es una vía directa. **Contar 0 h hasta verificar; si funciona, ~6,7 h una sola vez.**

### 7. Lium — $5 nuevos, sin tarjeta (hallazgo nuevo) ✅ Verificado

- **Enlace oficial:** docs.lium.io/pod-users/fingerprint-signup (citado textualmente por fshy.ajam.dev/p/lium/, verificado 22 oct 2026; también listado en gpus.io)
- **GPU:** pods bajo demanda con H100, H200, B200, RTX 4090/5090 y otras. Precios en vivo por GPU; RTX 4090 ~$0,35/h según gpus.io (nov 2026).
- **Cuota gratis:** **$5 en crédito para cuentas nuevas, una sola vez, al confirmar el email** (o al hacer un primer depósito de pago — la vía email no necesita tarjeta). **Expira a los 14 días.** Una sola vez por IP y sujeto a controles anti-abuso («if Lium's abuse checks pass»). El registro puede hacerse con una sola llamada API sin email ni contraseña (fingerprint signup), pero el crédito exige email confirmado.
- **Tarjeta:** No (vía email). **Teléfono:** No.
- **Cuba:** Sin verificar.
- **Cómo se ejecuta:** pods GPU por API/CLI/dashboard, facturación por segundo. Diseñado para que agentes de IA lancen GPUs con una llamada.
- **¿Wan 2.2 TI2V-5B?** Sí: RTX 3090/4090 (24 GB) corren el script oficial 720p. Rendimiento estimado del bono (según análisis de fshy, 22 oct 2026): **~20,8 GPU-horas a la tarifa más barata realmente alquilable** (unas 20 h en RTX 3090, o 1,3–2,5 h en H100). Es una estimación de terceros, no cifra oficial de Lium.
- **Valor real:** bono único de ~20 GPU-horas. El mejor bono único sin tarjeta de toda la lista después de Lightning.

---

## Fichas — excluidos (con motivo)

### 8. Modal — el $30/mes existe, pero exige método de pago ❌ Excluido

- **Enlace oficial:** https://modal.com/pricing (leído directamente 21 nov 2026) y https://modal.com/docs/guide/billing
- **Lo que da:** plan Starter $0 + cómputo, con **$30/mes en créditos** que cubren cómputo (funciones y sandboxes: CPU, memoria y GPU por segundo). GPUs: T4 $0,59/h, L4 $0,80/h, A10 $1,10/h, L40S $1,95/h, A100 40 GB $2,10/h, A100 80 GB $2,50/h, RTX PRO 6000 $3,03/h, H100 $3,95/h, H200 $4,54/h, B200 $6,25/h (tarifas por segundo × 3.600). $30/mes = ~50 h de T4, ~37 h de L4 o ~12 h de A100 80 GB al mes.
- **Por qué queda fuera:** la documentación oficial de facturación dice textualmente: **«Note that you must have a payment method on file in order to use Modal.»** Sin método de pago en archivo no se puede usar Modal en absoluto — confirmado además por una prueba con cuenta nueva (oct 2026): el trabajo se detuvo con «Please add a payment method to use L4 GPU functions». no hay ningún método de pago disponible. Además, desde el 1 sep 2026 los tokens de Model APIs se facturan desde la primera petición, y el uso por encima del crédito se cobra automáticamente a ese método de pago.
- **Nota:** el programa para académicos (hasta $10.000) exige ser estudiante de posgrado, laboratorio o investigador, y tampoco elimina el requisito del método de pago.

### 9. RunPod — sin plan gratis; el «bono» exige cargar $10 ❌ Excluido

- **Enlace oficial:** https://www.runpod.io/pricing (revisado 1 nov 2026 por stork.ai; 30 oct 2026 por blurstudio.ai)
- **Lo que da:** nada gratis. La página de precios **no lista plan gratis ni créditos**. El programa de referidos da un bono aleatorio de $5–$500 (la mayoría recibe $5) **solo después de cargar $10** y con registro por Google. GPUs: RTX A5000 $0,16/h (Community) hasta B300 $8,99/h (Secure); RTX 4090 $0,34/h Community, A100 80 GB $1,39–$1,79/h, H100 SXM $2,69–$3,99/h.
- **Por qué queda fuera:** exige dinero propio antes de recibir nada. Las guías que citan «$5/$10 gratis» describen el bono con depósito o cifras antiguas no publicadas en la página oficial.

### 10. Vast.ai — sin crédito gratis; depósito mínimo $5 ❌ Excluido

- **Enlace oficial:** https://vast.ai/pricing y docs.vast.ai/billing (verificado 21 ago y 2 sep 2026 por buildaicurrent; 24 oct 2026 por askgpu.com)
- **Lo que da:** nada gratis. El «$5» que circula en guías es el **depósito mínimo** («The minimum deposit amount on Vast.ai is $5»), dinero propio, no un regalo. Marketplace con 68+ tipos de GPU (RTX 4090 desde ~$0,47/h, H100 80 GB ~$0,90–$1,90/h según host). Pago por tarjeta (Stripe), BitPay o Crypto.com. Al llegar el saldo a $0 las instancias se paran y los datos pueden borrarse.
- **Por qué queda fuera:** exige depósito con tarjeta o cripto. Sin depósito no hay GPU.

### 11. Hyperbolic — el plan gratis no puede lanzar GPUs ❌ Excluido

- **Enlace oficial:** https://hyperbolic.ai (precios y docs; revisado 9–10 nov 2026 por usagepricing.com y reviewgalore.com)
- **Lo que da:** el plan Free ($0) **no puede lanzar instancias GPU ni crear volúmenes de almacenamiento**; solo puede llamar a la API de inferencia tras verificar el teléfono, lo que añade **$1 de crédito** (solo para inferencia de texto, no para GPU). El plan Pro exige un **depósito único de $5** (créditos prepago 1:1 con el dólar, sin caducidad). GPUs bajo demanda: H100 SXM $3,19/h, H200 $3,99/h, B200 $5,99/h (tarifas revisadas semanalmente).
- **Por qué queda fuera:** cero GPU gratis; la única vía a GPU exige depósito de $5 con tarjeta (Stripe).

### 12. DeepInfra — sin crédito; tarjeta o prepago antes del primer uso ❌ Excluido

- **Enlace oficial:** https://deepinfra.com/pricing (verificado 2 sep 2026 por buildaicurrent; 14 nov 2026 por broadrouter.com; 17 nov 2026 por macrostack.net)
- **Lo que da:** nada gratis. La página oficial dice: **«You have to add a card or pre-pay or you won't be able to use our services.»** El «$5 gratis» que citan guías de terceros no tiene fuente oficial. El programa DeepStart («1.000 millones de tokens gratis») es solo con solicitud y exige ser una empresa fundada hace menos de 2 años que haya levantado entre $250K y $10M. GPUs dedicadas: H100 $2,90/h, B200 $4,89/h, facturación por minuto.
- **Por qué queda fuera:** tarjeta o prepago obligatorio desde el primer token.

### 13. Novita AI — los $100 son solo para CPU/RAM, cero GPU ❌ Excluido para GPU

- **Enlace oficial:** https://docs.novita.ai/guides/sandbox-pricing (modificado 11 nov 2026; verificado 20 nov 2026)
- **Lo que da:** $100 en créditos promocionales de Sandbox para usuarios nuevos que completen una encuesta de registro, **sin tarjeta**, válidos 90 días. Pero los créditos están **limitados oficialmente al uso de Sandbox: CPU y RAM** ($0,0000098/vCPU-s, $0,0000032/GiB-s; plan gratis: 5 sandboxes simultáneos, sesiones de 1 h, 2 vCPU/4 GiB). No hay ninguna declaración oficial de que cubran instancias GPU ni la API de modelos. Las instancias GPU existen (RTX 4090 $0,33/h, H100 SXM $3,39/h) pero se pagan con saldo prepago (recarga mínima >$10, con tarjeta; sin cripto).
- **Por qué queda fuera (para video):** $100 que no pueden comprar ni un minuto de GPU. Podría servir para trabajo CPU (scripts, pre/post-proceso), no para generar video.

### 14. Prime Intellect — sin plan gratis; el programa de grants desapareció ❌ Excluido

- **Enlace oficial:** https://www.primeintellect.ai y docs.primeintellect.ai (revisado 22 oct 2026 por fshy.ajam.dev; sep 2026 por buildaicurrent)
- **Lo que da:** nada gratis. Modelo prepago por minuto («your Prime Intellect credits are deducted every minute while the Pod is active»; si se agotan, los pods se borran automáticamente). El programa Fast Compute Grants ($500–$100.000) **ya no tiene página activa (HTTP 404)**. GPUs: desde ~$0,47/h (H200 en spot según una fuente) hasta $6,64/h (B300); H100 ~$2,43–$3,50/h. Una fuente marca tarjeta requerida.
- **Por qué queda fuera:** sin crédito de registro ni plan gratis; todo es prepago.

### 15. Gensyn — dirección invertida: tú aportas la GPU ❌ Excluido

- **Enlace oficial:** https://docs.gensyn.ai/testnet/rl-swarm/getting-started y https://dashboard.gensyn.ai (revisado 22 oct 2026 por fshy.ajam.dev)
- **Lo que es:** red descentralizada de entrenamiento donde **los participantes aportan su propio hardware** (mínimo 32 GB RAM o GPU NVIDIA 3090/4090/5090/A100/H100) y ganan puntos/recompensas. no hay GPU que aportar. Además, el dashboard oficial decía: **«There are no official swarms running right now.»** Las guías de terceros calculan $65–$300/mes de alquiler de GPU para correr un nodo — gasto, no ingreso.
- **Por qué queda fuera:** no es una fuente de GPU, es un consumidor de GPU. Aparece en guías de «GPU gratis» por un malentendido.

### 16. Theta EdgeCloud — ningún crédito gratis publicado ❌ Excluido

- **Enlace oficial:** https://www.thetaedgecloud.com/ (leído directamente 21 nov 2026)
- **Lo que da:** la página oficial **no menciona ningún crédito gratis ni plan gratuito en absoluto**: «GPUs live in minutes. Pay only for what you use.» Precios: RTX 3090 $0,14/h, RTX 4090 $0,26/h, RTX 5090 $0,49/h, A100 80 GB $1,99/h, H100 $2,29/h, H200 $2,29/h; desde $0,05/h en las tarjetas más baratas. Una comparativa (gpuclouds.fyi) marca «Free credits: Yes» sin cantidad ni enlace; gpus.io marca el crédito de registro como N/A. Sin cantidad publicada ni condiciones, no se puede contar.
- **Por qué queda fuera:** sin crédito gratis documentado; todo es prepago por saldo. Precaución adicional: demanda pendiente (dic 2025) de dos exempleados por presunto fraude y manipulación del token (la empresa lo niega).

### 17. Oracle Cloud Free Tier — exige tarjeta y Always Free NO tiene GPU ❌ Excluido

- **Enlace oficial:** https://www.oracle.com/cloud/free/faq/ (leído 21 nov 2026) y docs de Always Free Resources (revisado 20 nov 2026 por trackvps.com)
- **Lo que da:** Always Free (sin caducidad): 2 OCPU ARM Ampere A1 + 12 GB RAM (1.500 OCPU-h + 9.000 GB-h/mes), 2 micro VMs AMD (1/8 OCPU, 1 GB), 200 GB disco, 10 TB salida/mes. **Ninguna GPU en Always Free.** Trial: $300 por 30 días.
- **Por qué queda fuera (doble motivo):** (1) el registro **exige tarjeta de crédito/débito** para verificación de identidad (no acepta prepago, virtuales ni de un solo uso; con retención temporal de autorización); (2) aunque hubiera tarjeta, **el tier gratis no incluye ninguna GPU** — las GPU solo existen con el crédito trial de $300 (30 días, con tarjeta) o de pago. Sin tarjeta no hay cuenta; sin cuenta no hay nada.

### 18. Google Cloud — exige tarjeta Y el trial no admite GPUs ❌ Excluido

- **Enlace oficial:** https://docs.cloud.google.com/free/docs/free-cloud-features (leído 21 nov 2026)
- **Lo que da:** $300 de crédito de bienvenida por 90 días + Free Tier mensual. **Pero:** «During the sign up, you must provide a credit card or other payment method» y, en las restricciones de la cuenta de prueba: **«You can't add GPUs to your VM instances»** ni pedir aumento de cuota. La única vía a GPU es actualizar primero a una cuenta de facturación de pago (con tarjeta), momento en que el riesgo de cobro es real.
- **Por qué queda fuera (doble motivo):** exige método de pago y, aun con él, el crédito de $300 no se puede gastar en GPU sin convertirse en cuenta de pago. Además Google bloquea oficialmente Cuba en sus servicios de IA.

### 19. Lambda — crédito de registro no confirmado en página oficial ⚠️ Sin verificar

- **Enlace oficial:** https://lambda.ai/cloud (precios; revisado 6–20 nov 2026 por reviewgalore.com y softwr.com)
- **Lo que dicen las fuentes:** varias guías citan un crédito de registro de **$10 (gmicloud, mayo 2026) o $15 (promptquorum, oct 2026)**. Pero las revisiones más recientes (nov 2026) afirman: **«No free plan is listed» / «No free tier or trial»** en la página oficial, y «trial terms are not published». Además, una fuente de tarifas (gpurentalprices.com, oct 2026) registra una **pre-autorización de tarjeta de $10** al registrarse. GPUs: A10G ~$0,60/h, RTX 6000 Ada $0,80/h, A100 80 GB $1,29–$2,79/h, H100 $2,89–$3,99/h, B200 hasta $6,69/h.
- **Por qué no se cuenta:** el crédito no está confirmado en ninguna página oficial actual y hay indicios de que el registro pide tarjeta. **No prometer nada; si algún día se prueba, verificar primero si el registro pide tarjeta.**

### 20. SaladCloud — FAQ oficial: sin prueba gratis ❌ Excluido

- **Enlace oficial:** https://salad.com/pricing/ (FAQ; revisado 5–6 nov 2026 por usagepricing.com, toolin.ai y reviewgalore.com)
- **Lo que da:** nada gratis. La FAQ oficial dice que **no hay prueba gratis ni suscripción mensual**: solo prepago por uso (créditos que expiran a los 12 meses, no reembolsables). GPUs de consumo distribuidas (RTX 3060–5090): desde $0,015/GPU-h en prioridad Lowest; RTX 4090 $0,16/h (Lowest) a $0,44/h (High). Los créditos para startups ($1.000–$10.000) son solo con solicitud, para empresas pre-seed a Serie B con carga de trabajo en contenedores (y el SSAP exige mínimo 10 GPUs de 24 GB simultáneas).
- **Por qué queda fuera:** prepago obligatorio; los programas de créditos no aplican a un usuario individual.

### 21. Amazon SageMaker Studio Lab — cerrado a nuevos usuarios ❌ Excluido

- **Enlace oficial:** https://studiolab.sagemaker.aws (docs de AWS; cierre confirmado por dev.to, spheron.network y gpuperhour.com, sep–nov 2026)
- **Lo que daba:** T4 (16 GB), 4 GPU-h/día (sesiones de hasta 4 h), 15 GB almacenamiento persistente, sin cuenta AWS ni tarjeta (solo verificación por teléfono).
- **Por qué queda fuera:** **AWS cerró el acceso a nuevos clientes el 30 de julio de 2026.** Solo las cuentas existentes siguen funcionando; no hay cuenta disponible. (Varias guías de nov 2026 lo siguen listando como opción sin mencionar el cierre — dato desactualizado.)

### 22. Cerebrium, Crusoe, OVHcloud, DigitalOcean, Azure, AWS, Beam, Thunder Compute, Jarvislabs, TensorDock, Spheron ❌ Excluidos

- **Cerebrium** (cerebrium.ai/pricing, revisado 8 oct 2026): plan Hobby $0/mes + cómputo facturado por segundo (T4 $0,59/h, H100 $3,40/h). **Sin crédito de cómputo gratis**: el plan es gratis, la GPU se paga desde el primer segundo.
- **Crusoe Cloud** (docs.crusoecloud.com, verificado 2 sep 2026): $5 de crédito **solo para inferencia y fine-tuning serverless** (no GPU cruda para correr un modelo propio de video), y **exige método de pago**.
- **OVHcloud** (ovhcloud.com, verificado 2 sep y 15 nov 2026): trial de **$200 por 1 mes** con ejemplos oficiales de GPU (35 h de notebook AI1-1-GPU), pero **exige método de pago válido antes de empezar y factura automáticamente** al agotarse el crédito (sin parada dura en $0). Excluido por tarjeta + riesgo de cobro automático.
- **DigitalOcean** ($200 por 60 días): exige tarjeta y **excluye expresamente las GPU del trial**.
- **Azure** ($200 por 30 días) y **AWS** (~$100 en créditos para cuentas nuevas): ambos exigen tarjeta.
- **Beam:** publicaba $30/mes como Modal, pero **retiró la oferta en septiembre de 2026** (sin rastro en sus páginas oficiales desde el 9 sep 2026).
- **Thunder Compute:** $20 en créditos, pero **solo para estudiantes de EE. UU.** (ámbito A6000/L40). no se cumple el requisito.
- **Jarvislabs** (depósito mínimo $5–$10), **TensorDock** (sin plan gratis; el «$15» citado no aparece en páginas oficiales) y **Spheron** (depósito mínimo $15): prepago obligatorio, sin crédito gratis.

### Programas con solicitud (no son acceso inmediato, no se cuentan)

- **Hugging Face community GPU grants:** becas de GPU para Spaces, con solicitud y aprobación; orientadas a demos de la comunidad.
- **Google TPU Research Cloud, NAIRR Pilot, NSF ACCESS:** programas de investigación con solicitud, revisión y criterios académicos; TPU no sirve para modelos de video CUDA.
- **NVIDIA Inception:** gratis unirse, sin cifra de créditos publicada; orientado a startups.
- Ninguno de estos da GPU inmediata a un usuario individual sin solicitud aprobada. Si algún día se solicita uno, verificar primero que tu país no esté excluido (los programas de EE. UU. suelen excluir países sancionados por OFAC).

---

## Lo que esto cambia

### GPU-horas gratis reales por semana (solo fuentes legítimas verificadas, sin tarjeta)

| Fuente | Tipo | GPU-h/semana | Notas |
|---|---|---|---|
| Kaggle | Recurrente | **30 h** | T4 ×2; 1 h de cuota = 1 h con 2 GPUs. Exige SMS. |
| Google Colab Free | Recurrente | **~10–20 h (estimación)** | Sin cuota publicada; terceros estiman 15–30 h/sem. Se usa el rango bajo por los bloqueos de 1–5 días. |
| HF ZeroGPU | Recurrente | 0,58 h (35 min) | No sirve para clips completos; se excluye del total de clips. |
| Paperspace M4000 | Recurrente | Sin tope publicado | GPU inviable para video; se excluye del total. |
| **Total recurrente útil** | | **~40–50 GPU-h/semana (en T4)** | |
| Lightning AI | Una sola vez | ~9 h T4 | 5 créditos de registro. |
| Lium | Una sola vez | ~20,8 h (estimación) | $5, expira a los 14 días. En GPU 3090/4090. |
| Akash | Una sola vez | 0–6,7 h | $1; 0 hasta verificar si la GPU de prueba funciona. |
| **Total bonos únicos** | | **~30–37 GPU-h (una sola vez)** | |

**Conclusión 1 — la lista real es corta.** De 20+ servicios investigados, solo **2 fuentes recurrentes** sirven para producir video (Kaggle + Colab), más **3 bonos únicos** pequeños (Lightning, Lium, Akash). Todo lo demás exige tarjeta, depósito, o no da GPU gratis. El hallazgo más valioso de esta investigación es negativo: **el $30/mes de Modal — la cifra que más se repite en las guías — es inalcanzable sin método de pago**, y Lightning AI ya no es mensual. El informe previo sobreestimaba Lightning (15 créditos/mes → en realidad 5 créditos una sola vez).

**Conclusión 2 — Kaggle es la columna vertebral.** 30 h/semana publicadas, con ejecución en segundo plano y API oficial, son el 60–75% de todo el total recurrente. El único riesgo es el SMS de verificación: si el código no llega, Kaggle queda en 0 y el total recurrente cae a solo Colab (~10–20 h/semana). **Probar el SMS de Kaggle es el primer paso antes de planificar nada.**

### Cuántos clips de 5 s rinde eso

Rango dado: **10–30 min por clip de 5 s en T4** (vía GGUF/offload; el script oficial 720p no cabe en T4).

**Recurrente (40–50 h T4/semana = 2.400–3.000 min):**

| Ritmo por clip | Clips/semana (en bruto) |
|---|---|
| 10 min/clip (mejor caso) | 240–300 |
| 20 min/clip (medio) | 120–150 |
| 30 min/clip (peor caso) | 80–100 |

**En bruto: 80–300 clips de 5 s por semana.** Pero el bruto no es el neto: cada sesión de Colab/Kaggle pierde tiempo descargando pesos (6–34 GB), instalando dependencias, en colas de GPU, en renders fallidos y en subir/bajar clips. Con una sobrecarga realista del 30–50%, el rendimiento efectivo es **~40–200 clips/semana**. Un capítulo Fruti de ~85 s son ~17 clips de 5 s, así que eso equivale a **~2–12 capítulos/semana en bruto, ~2–6 capítulos/semana realistas** — la misma conclusión del informe previo y del diseño del repo de video. **Esta investigación no cambia el ritmo alcanzable: lo confirma con más fuentes.**

**Bonos únicos (~30–37 GPU-h, una sola vez):** en T4 (Lightning, ~9 h) rinden ~18–54 clips; en RTX 3090/4090 (Lium ~21 h + Akash 0–6,7 h), el README de Wan documenta **menos de 9 min por clip de 5 s a 720p en GPU de consumo** (clase 4090), así que *estimación* (marcada como tal, sin verificar en Lium/Akash): ~140–300 clips adicionales una sola vez si se aprovechan bien los 14 días de Lium y los 30 días de Akash. Son un impulso inicial, no producción sostenida.

**Potencial ×2 en Kaggle (pendiente de probar):** la cuota de Kaggle cobra 1 h por 1 h de pared con **dos** T4. Si se lanzan 2 clips en paralelo (uno por T4), las 30 h/semana rinden como 60 GPU-horas T4. Esto podría elevar el total recurrente a ~70–80 GPU-horas/semana equivalentes. Es plausible pero **no está probado** con Wan 2.2; hay que verificar que dos procesos caben en los 29 GB de RAM del notebook.

### Lo que NO cambia

- **No hay video ilimitado gratis en ningún sitio.** La GPU cuesta electricidad y hardware real; nadie la regala sin límite. La suma de todas las capas gratis legítimas da para 2–6 capítulos/semana, no 2 capítulos/día.
- **La T4 sigue siendo el cuello de botella:** sin BF16 nativo, 16 GB, lenta. Las GPU buenas gratis (ZeroGPU 48 GB, L4 24 GB en Lightning, 3090 en Lium/Akash) llegan en dosis de minutos u horas, no en semanas.
- **El orden de uso recomendado:** (1) probar el SMS de Kaggle; (2) Kaggle como base diaria (30 h/sem); (3) Colab como complemento cuando Kaggle se agota o se bloquea; (4) guardar Lightning (L4 24 GB, script oficial 720p) para los clips que necesiten máxima calidad; (5) gastar Lium ($5, 14 días) y Akash ($1, 30 días) pronto, antes de que expiren, tras verificar que la GPU de prueba de Akash funciona de verdad.

## Límites de esta investigación

- Las cuotas cambian sin aviso: en 2026 ya cambiaron Lightning (de mensual a único), Beam (retiró su oferta), Kaggle (retiró el P100) y Colab (web UIs de pago). Antes de planificar un mes entero, verificar la cuota en la cuenta real.
- «Sin verificar» en Cuba significa que no hay bloqueo publicado ni confirmación de funcionamiento. No significa que funcione seguro. Los servicios de Google (Colab, Kaggle) conllevan riesgo adicional porque Google bloquea Cuba oficialmente en otros productos.
- Los tiempos por clip (10–30 min en T4; <9 min en 4090) son cifras documentadas o estimaciones razonadas, no mediciones propias: ningún clip de Wan 2.2 se ha generado todavía en estas plataformas para este proyecto.
- No se creó ninguna cuenta para este informe. Todo lo «verificado» se leyó en páginas oficiales o en verificaciones fechadas de terceros que citan la página oficial.
- Varias guías de «GPU gratis» repiten cifras muertas o malinterpretadas (el «$5 gratis» de Vast.ai es un depósito; el «$30/mes» de Modal exige tarjeta; Studio Lab cerró en julio). Este informe las marca como excluidas con el motivo exacto.

## Fuentes principales (todas consultadas 21 nov 2026)

- Kaggle docs (notebooks, efficient-gpu-usage) + anuncios de Kaggle (P100 retirado 15 sep 2026; T4 ×2 = 1 h de cuota)
- Google Colab FAQ y guías de límites nov 2026 (fastero.com, freakyjolly.com)
- Hugging Face docs ZeroGPU (huggingface.co/docs/hub/spaces-zerogpu)
- Lightning AI pricing (lightning.ai/pricing) + fastero.com/blog/lightning-ai-studio (12 nov 2026)
- DigitalOcean Paperspace docs + fastero.com/blog/paperspace-gradient (11 nov 2026)
- Akash Network Quick Start + Console Onboarding (akash.network/docs, leídas directamente)
- Lium docs (docs.lium.io/pod-users/fingerprint-signup, citado 22 oct 2026)
- Modal pricing (modal.com/pricing, leída directamente) + Modal billing docs (modal.com/docs/guide/billing)
- Wan 2.2 README (github.com/Wan-Video/Wan2.2) + ComfyUI Wan 2.2 tutorial + cloudgpu.app (4 nov 2026)
- buildaicurrent.com (índice de créditos GPU, verificado ago–sep 2026) — fuente secundaria clave para Modal, DeepInfra, Vast.ai, OVHcloud, Prime Intellect, Novita
- Google Cloud Free Program docs (docs.cloud.google.com/free/docs/free-cloud-features)
- Oracle Cloud Free Tier FAQ (oracle.com/cloud/free/faq/)
- Theta EdgeCloud (thetaedgecloud.com, leída directamente)
- Novita AI Sandbox pricing (docs.novita.ai, 11 nov 2026)
