#!/usr/bin/env python3
"""CLI del orquestador.

    python -m orquestador.cli plan --guion guion.json --trabajo cap-01/
    python -m orquestador.cli estado --trabajo cap-01/
    python -m orquestador.cli recolectar --trabajo cap-01/ --clips clips/
    python -m orquestador.cli ensamblar --guion guion.json --trabajo cap-01/ ...

`plan` valida el guion, prepara los jobs, crea la cola y asigna cada
clip a la fuente con cuota disponible. La generación de vídeo en sí es
externa (cuadernos de Colab/Kaggle o APIs); `recolectar` verifica los
clips cuando vuelven, y `ensamblar` une todo y pasa el QC.
"""

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from orquestador.asignar import asignar, estimar_capacidad_semanal  # noqa: E402
from orquestador.cola import Cola  # noqa: E402
from orquestador.fuentes import RegistroFuentes  # noqa: E402
from orquestador import pipeline  # noqa: E402
from orquestador import recolectar as recolectar_mod  # noqa: E402

SOLUCION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rutas_trabajo(trabajo):
    return {
        "cola": os.path.join(trabajo, "cola.json"),
        "jobs": os.path.join(trabajo, "jobs.json"),
        "uso": os.path.join(trabajo, "uso.json"),
        "plan": os.path.join(trabajo, "plan.json"),
    }


def cmd_plan(args):
    repo = pipeline.resolver_repo(args.repo)
    os.makedirs(args.trabajo, exist_ok=True)
    rutas = _rutas_trabajo(args.trabajo)

    ok, val = pipeline.validar_guion(repo, args.guion)
    print(f"Guion: {val.get('clips', '?')} clips, "
          f"{val.get('palabras', '?')} palabras, "
          f"{val.get('palabras_por_minuto', '?')} pal/min")
    for aviso in val.get("avisos", []):
        print(f"  AVISO: {aviso}")
    if not ok:
        for error in val.get("errores", []):
            print(f"  ERROR: {error}")
        print("❌ Guion inválido: corrígelo antes de planificar.")
        return 1

    ok, detalle = pipeline.preparar_jobs(
        repo, args.guion, rutas["jobs"], refs=args.refs, res=args.res)
    if not ok:
        print(f"❌ No se pudieron preparar los jobs: {detalle}")
        return 1
    print(f"✅ Jobs en {rutas['jobs']}")

    cola = Cola.desde_jobs(rutas["cola"], rutas["jobs"])
    registro = RegistroFuentes(uso_ruta=rutas["uso"])
    plan = asignar(cola, registro)
    cola.guardar()
    with open(rutas["plan"], "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(f"\nPlan para «{cola.capitulo}» ({len(cola.items)} clips):")
    for a in plan["asignados"]:
        aviso = ""
        if a["marca_agua"]:
            aviso = " ⚠️ MARCA DE AGUA"
        if a["uso_comercial"] != "permitido":
            aviso += f" ⚠️ uso comercial: {a['uso_comercial']}"
        print(f"  {a['clip_id']} -> {a['fuente_nombre']} "
              f"({a['coste']} {a['coste_unidad']}, "
              f"coste {a['coste_estado']}){aviso}")
    for s in plan["sin_fuente"]:
        print(f"  {s['clip_id']} -> SIN FUENTE: {s['motivo']}")
    if plan["sin_fuente"]:
        print("\n⚠️ Hay clips sin fuente: espera a que se renueve una "
              "cuota diaria o usa una fuente manual.")
    print(f"\nCola guardada en {rutas['cola']}. "
          "Genera los clips y recógelos con `recolectar`.")
    return 0


def cmd_estado(args):
    rutas = _rutas_trabajo(args.trabajo)
    if not os.path.exists(rutas["cola"]):
        print(f"No hay cola en {args.trabajo}. Corre `plan` primero.")
        return 1
    cola = Cola.cargar(rutas["cola"])
    print(f"Capítulo: {cola.capitulo}")
    resumen = cola.resumen()
    print("Cola: " + ", ".join(f"{k}: {v}" for k, v in resumen.items()))
    for item in cola.items:
        extra = ""
        if item["fuente"]:
            extra = f" [{item['fuente']}]"
        if item["error"]:
            extra += f" — {item['error']}"
        print(f"  {item['clip_id']}: {item['estado']}{extra}"
              f" (intentos: {item['intentos']})")

    registro = RegistroFuentes(uso_ruta=rutas["uso"])
    print("\nFuentes:")
    hoy = datetime.date.today()
    for fila in registro.estado(hoy):
        pausa = " ⏸️ PAUSADA" if fila["pausada"] else ""
        restante = (f"{fila['restante']}" if fila["restante"] is not None
                    else "sin límite publicado")
        caben = (f"{fila['clips_5s_que_caben']} clips de 5 s"
                 if fila["clips_5s_que_caben"] is not None else "sin estimar")
        print(f"  {fila['nombre']} ({fila['id']}): cuota "
              f"{fila['cuota']} [{fila['cuota_estado']}], "
              f"consumido {fila['consumido']}, restante {restante}, "
              f"caben {caben}{pausa}")
    return 0


def cmd_recolectar(args):
    rutas = _rutas_trabajo(args.trabajo)
    if not os.path.exists(rutas["cola"]):
        print(f"No hay cola en {args.trabajo}. Corre `plan` primero.")
        return 1
    cola = Cola.cargar(rutas["cola"])
    try:
        informe = recolectar_mod.recolectar(
            cola, args.clips, marcar_faltantes=args.marcar_faltantes)
    except RuntimeError as e:
        print(f"❌ {e}")
        return 1
    cola.guardar()
    for v in informe["verificados"]:
        print(f"  ✅ {v['clip_id']}: {v['duracion_s']:.1f} s "
              f"({v['tamano_bytes'] / 1e6:.1f} MB)")
    for f in informe["fallidos"]:
        print(f"  ❌ {f['clip_id']}: {f['error']}")
    for s in informe["sin_aparecer"]:
        print(f"  ⏳ {s['clip_id']}: aún no aparece en {args.clips}")
    print(f"Verificados: {len(informe['verificados'])}, "
          f"fallidos: {len(informe['fallidos'])}, "
          f"sin aparecer: {len(informe['sin_aparecer'])}")
    return 0


def cmd_ensamblar(args):
    repo = pipeline.resolver_repo(args.repo)
    config = {
        "repo": repo,
        "solucion_dir": SOLUCION_DIR,
        "guion": args.guion,
        "trabajo": args.trabajo,
        "clips": args.clips,
        "wavs": args.wavs,
        "salida": args.salida,
        "musica": args.musica,
        "refs": args.refs,
        "res": args.res,
        "voz": args.voz,
        "voces_dir": args.voces_dir,
        "sin_whisper": args.sin_whisper,
    }
    informe = pipeline.flujo_completo(config)
    for p in informe["pasos"]:
        marca = "✅" if p["ok"] else "❌"
        print(f"{marca} {p['paso']}: {p['detalle'][:500]}")
    if informe["ok"]:
        print(f"✅ Capítulo listo y con QC aprobado: {args.salida}")
        return 0
    print("❌ El flujo no terminó. Revisa el paso que falló arriba.")
    return 1


def cmd_capacidad(args):
    registro = RegistroFuentes()
    gpu, api, detalle = estimar_capacidad_semanal(registro)
    print("Capacidad semanal estimada (clips de 5 s, sin contar Colab — "
          "cuota no publicada):")
    for d in detalle:
        clips = (f"{d['clips_semana']} clips/semana"
                 if d["clips_semana"] is not None else "sin estimar")
        print(f"  {d['id']}: {clips} {d['nota']}")
    print(f"\nGPU libre: ~{gpu} clips/semana "
          f"(≈ {gpu // 17} capítulos de 85 s/semana, estimación)")
    print(f"APIs con marca de agua: ~{api} clips/semana "
          f"(≈ {api // 17} capítulos/semana, estimación)")
    print("Estos números dependen de costes por clip ESTIMADOS (sin medir) "
          "y de cuotas que cambian sin aviso. Verifícalos en la primera "
          "semana real.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Orquestador de generación de vídeo gratis "
                    "(Fruti novelas).")
    parser.add_argument("--repo", default=None,
                        help="Ruta del repo video-generator-repo "
                        "(o VIDEO_GENERATOR_REPO).")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("plan", help="Validar guion, preparar jobs y "
                       "asignar clips a fuentes.")
    p.add_argument("--guion", required=True)
    p.add_argument("--trabajo", required=True,
                   help="Carpeta de trabajo del capítulo.")
    p.add_argument("--refs", default=None)
    p.add_argument("--res", choices=["480", "720"], default="480")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("estado", help="Ver la cola y las cuotas.")
    p.add_argument("--trabajo", required=True)
    p.set_defaults(func=cmd_estado)

    p = sub.add_parser("recolectar", help="Verificar los clips generados.")
    p.add_argument("--trabajo", required=True)
    p.add_argument("--clips", required=True,
                   help="Carpeta con los clips descargados.")
    p.add_argument("--marcar-faltantes", action="store_true",
                   help="Devolver a pendiente los clips que no aparecieron.")
    p.set_defaults(func=cmd_recolectar)

    p = sub.add_parser("ensamblar", help="Flujo local completo: validar, "
                       "voz, ensamblar, QC.")
    p.add_argument("--guion", required=True)
    p.add_argument("--trabajo", required=True)
    p.add_argument("--clips", required=True)
    p.add_argument("--wavs", required=True)
    p.add_argument("--salida", required=True)
    p.add_argument("--musica", default=None)
    p.add_argument("--refs", default=None)
    p.add_argument("--res", choices=["480", "720"], default="480")
    p.add_argument("--voz", default="es_ES-sharvard-medium")
    p.add_argument("--voces-dir", default=None)
    p.add_argument("--sin-whisper", action="store_true")
    p.set_defaults(func=cmd_ensamblar)

    p = sub.add_parser("capacidad", help="Capacidad semanal estimada "
                       "con las cuotas actuales.")
    p.set_defaults(func=cmd_capacidad)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
