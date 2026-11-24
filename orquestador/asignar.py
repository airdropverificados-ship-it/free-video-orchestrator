#!/usr/bin/env python3
"""Asigna cada clip pendiente a una fuente de generación.

Prioridad (definida en fuentes.json, campo `prioridad`):

  1. GPU gratis con modelos abiertos (Colab, Kaggle, Lightning):
     sin marca de agua, licencia abierta, personajes consistentes.
  2. APIs de vídeo gratis (Dreamina, Kling, PixVerse): SOLO como
     complemento, cuando la GPU gratis no da para más. Cada clip
     asignado aquí queda marcado con marca de agua y sin licencia
     comercial (o no clara), para que el QC y la publicación lo sepan.

Reglas:
  - Un clip solo se asigna a una fuente con cuota suficiente para su
    coste estimado (el coste escala con la duración del clip).
  - El consumo se registra en el momento de asignar (reserva): así dos
    capítulos no se comen la misma cuota.
  - Si ninguna fuente tiene cuota, el clip queda pendiente y el plan lo
    dice en voz alta: no se promete lo que no cabe.
  - ZeroGPU y Vidnoz no se asignan solas (coste sin medir / no es vídeo
    de novela): aparecen en el plan como "uso manual".
"""

from .cola import Cola
from .fuentes import RegistroFuentes


def asignar(cola, registro, fecha=None):
    """Asigna los clips pendientes. Devuelve el plan (dict).

    Modifica la cola (marca en-generación con su fuente) y el registro
    (reserva el consumo). El llamador guarda ambos.
    """
    plan = {"asignados": [], "sin_fuente": [], "manuales": []}
    for item in cola.pendientes():
        clip_id = item["clip_id"]
        dur = item["duracion_s"]
        elegido = None
        for fuente in registro.fuentes:
            if not fuente.asignable:
                continue
            if registro.cabe_clip(fuente.id, dur, fecha):
                elegido = fuente
                break
        if elegido is None:
            plan["sin_fuente"].append({
                "clip_id": clip_id,
                "duracion_s": dur,
                "motivo": "ninguna fuente asignable tiene cuota "
                          "suficiente para este clip",
            })
            continue
        coste = elegido.coste_clip(dur)
        cola.marcar_en_generacion(clip_id, elegido.id)
        registro.registrar_consumo(elegido.id, coste, fecha)
        plan["asignados"].append({
            "clip_id": clip_id,
            "fuente": elegido.id,
            "fuente_nombre": elegido.nombre,
            "tipo": elegido.tipo,
            "coste": round(coste, 2),
            "coste_unidad": elegido.coste_unidad,
            "coste_estado": elegido.coste_estado,
            "marca_agua": elegido.marca_agua,
            "uso_comercial": elegido.uso_comercial,
            "duracion_s": dur,
        })

    # Fuentes no asignables que el usuario puede usar a mano.
    for fuente in registro.fuentes:
        if not fuente.asignable:
            plan["manuales"].append({
                "id": fuente.id,
                "nombre": fuente.nombre,
                "motivo": ("coste por clip sin medir"
                           if fuente.coste_5s is None
                           else "no genera clips de novela"),
                "notas": fuente.notas,
            })
    return plan


def estimar_capacidad_semanal(registro, duracion_clip_s=5.0, fecha=None):
    """Estima cuántos clips de `duracion_clip_s` caben en una semana.

    Suma la cuota semanal de cada fuente asignable (las diarias × 7,
    las mensuales ÷ 4,33). Colab no tiene cuota publicada y NO se
    cuenta: su aporte es desconocido. Los bonos únicos (periodo
    "una-vez": Lightning, Lium, Akash) tampoco se cuentan: se gastan
    una sola vez, no son capacidad semanal. Devuelve (clips_gpu_libre,
    clips_api, detalle) — todo marcado como estimación donde el coste
    por clip es estimado.
    """
    detalle = []
    gpu_libre = 0
    api = 0
    for fuente in registro.fuentes:
        if not fuente.asignable:
            detalle.append({
                "id": fuente.id,
                "clips_semana": None,
                "nota": ("coste por clip sin medir: uso manual"
                         if fuente.coste_5s is None
                         else "no genera clips de novela"),
            })
            continue
        if fuente.cuota_cantidad is None:
            detalle.append({
                "id": fuente.id,
                "clips_semana": None,
                "nota": "cuota no publicada: no se puede estimar",
            })
            continue
        if fuente.cuota_periodo == "una-vez":
            # Bono único (Lightning, Lium, Akash): se gasta una sola
            # vez, no es capacidad semanal. No suma al total.
            detalle.append({
                "id": fuente.id,
                "clips_semana": 0,
                "nota": "bono único, no recurrente: no suma a la "
                        "capacidad semanal",
            })
            continue
        if fuente.cuota_periodo == "dia":
            semanal = fuente.cuota_cantidad * 7
        elif fuente.cuota_periodo == "semana":
            semanal = fuente.cuota_cantidad
        elif fuente.cuota_periodo == "mes":
            semanal = fuente.cuota_cantidad / 4.33
        else:
            semanal = 0
        clips = int(semanal // fuente.coste_clip(duracion_clip_s))
        detalle.append({
            "id": fuente.id,
            "clips_semana": clips,
            "nota": ("coste por clip estimado, sin medir"
                     if fuente.coste_estado == "estimacion" else ""),
        })
        if fuente.tipo == "gpu-libre":
            gpu_libre += clips
        else:
            api += clips
    return gpu_libre, api, detalle
