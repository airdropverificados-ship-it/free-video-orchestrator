#!/usr/bin/env python3
"""Registro de fuentes de generación + seguimiento de cuotas.

Las fuentes se definen en `fuentes.json` (cuotas del informe de APIs
gratis, 21 nov 2026). El consumo se guarda en un archivo JSON aparte
(`uso.json`, dentro de la carpeta de trabajo o en ~/.cache), con una
clave de periodo por fuente:

  - periodo "dia":   la clave es la fecha ISO (2026-11-21)
  - periodo "semana": la clave es el lunes de la semana ISO
  - periodo "mes":   la clave es YYYY-MM
  - periodo "una-vez": la clave es siempre "una-vez": un bono único
    que no se renueva nunca (Lightning 5 créditos, Lium $5, Akash $1).
    El consumo se acumula para siempre y el restante solo baja.

Al cambiar de periodo el consumo vuelve a cero solo. Colab no tiene
cuota publicada: su consumo se registra en minutos-GPU usados, pero el
límite lo pone Colab, no nosotros — la fuente se pausa a mano cuando
Colab dice que no hay GPU (ver `pausar()`).
"""

import datetime
import json
import os

FUENTES_JSON_DEFECTO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fuentes.json")


def clave_periodo(periodo, fecha):
    """Clave del periodo que contiene a `fecha` (datetime.date)."""
    if periodo == "dia":
        return fecha.isoformat()
    if periodo == "semana":
        lunes = fecha - datetime.timedelta(days=fecha.weekday())
        return lunes.isoformat()
    if periodo == "mes":
        return f"{fecha.year:04d}-{fecha.month:02d}"
    if periodo == "una-vez":
        # Bono único: la clave no depende de la fecha, así que el
        # consumo nunca se resetea (el bono solo se gasta una vez).
        return "una-vez"
    raise ValueError(f"periodo desconocido: {periodo}")


class Fuente:
    def __init__(self, definicion):
        self.id = definicion["id"]
        self.nombre = definicion["nombre"]
        self.tipo = definicion["tipo"]  # gpu-libre | api-video | api-video-avatar
        self.prioridad = definicion["prioridad"]
        self.marca_agua = definicion.get("marca_agua", False)
        self.uso_comercial = definicion.get("uso_comercial", "no-claro")
        self.modelo = definicion.get("modelo", "")
        self.resolucion = definicion.get("resolucion", "")
        self.notas = definicion.get("notas", "")
        cuota = definicion.get("cuota") or {}
        self.cuota_cantidad = cuota.get("cantidad")  # None = no publicada
        self.cuota_unidad = cuota.get("unidad")
        self.cuota_periodo = cuota.get("periodo")
        self.cuota_estado = cuota.get("estado")  # documentada|probada|no-publicada
        coste = definicion.get("coste_por_clip_5s")
        if coste is None:
            self.coste_5s = None
            self.coste_estado = "sin-medir"
            self.coste_unidad = None
        else:
            self.coste_5s = coste["cantidad"]
            self.coste_estado = coste.get("estado", "documentada")
            self.coste_unidad = coste.get("unidad")

    @property
    def asignable(self):
        """Una fuente solo se asigna sola si se conoce el coste por clip
        y es una fuente de vídeo de novela (no avatares)."""
        return self.coste_5s is not None and self.tipo in ("gpu-libre", "api-video")

    @property
    def cuota_publicada(self):
        return self.cuota_cantidad is not None

    def coste_clip(self, duracion_s):
        """Coste estimado de un clip de `duracion_s` segundos.

        Se escala linealmente desde el coste de 5 s. Es una estimación:
        el coste real se mide en el registro de cada sesión.
        """
        if self.coste_5s is None:
            return None
        return self.coste_5s * (duracion_s / 5.0)

    def clips_que_caben(self, restante):
        """Cuántos clips de 5 s caben en `restante` unidades de cuota."""
        if self.coste_5s is None or restante is None:
            return None
        return int(restante // self.coste_5s)


class RegistroFuentes:
    def __init__(self, fuentes_json=None, uso_ruta=None):
        ruta = fuentes_json or FUENTES_JSON_DEFECTO
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        self.fuentes = [Fuente(d) for d in datos["fuentes"]]
        self.fuentes.sort(key=lambda f: f.prioridad)
        self.uso_ruta = uso_ruta
        self.uso = {}       # {fuente_id: {clave_periodo: cantidad}}
        self.pausadas = set()
        if uso_ruta and os.path.exists(uso_ruta):
            with open(uso_ruta, encoding="utf-8") as f:
                guardado = json.load(f)
            self.uso = guardado.get("uso", {})
            self.pausadas = set(guardado.get("pausadas", []))

    def guardar_uso(self):
        if not self.uso_ruta:
            return
        os.makedirs(os.path.dirname(os.path.abspath(self.uso_ruta)),
                    exist_ok=True)
        with open(self.uso_ruta, "w", encoding="utf-8") as f:
            json.dump({"uso": self.uso,
                       "pausadas": sorted(self.pausadas)},
                      f, ensure_ascii=False, indent=2)

    def fuente(self, fuente_id):
        for f in self.fuentes:
            if f.id == fuente_id:
                return f
        raise KeyError(f"fuente desconocida: {fuente_id}")

    def consumido(self, fuente_id, fecha=None):
        fecha = fecha or datetime.date.today()
        f = self.fuente(fuente_id)
        clave = clave_periodo(f.cuota_periodo, fecha)
        return self.uso.get(fuente_id, {}).get(clave, 0)

    def restante(self, fuente_id, fecha=None):
        """Unidades de cuota que quedan en el periodo actual.

        None si la cuota no está publicada (Colab): no hay número que
        restar, la fuente se pausa a mano cuando Colab la niega.
        """
        f = self.fuente(fuente_id)
        if f.cuota_cantidad is None:
            return None
        return max(0.0, f.cuota_cantidad - self.consumido(fuente_id, fecha))

    def cabe_clip(self, fuente_id, duracion_s, fecha=None):
        f = self.fuente(fuente_id)
        if fuente_id in self.pausadas:
            return False
        coste = f.coste_clip(duracion_s)
        if coste is None:
            return False
        restante = self.restante(fuente_id, fecha)
        if restante is None:
            return True  # cuota no publicada: cabe hasta que Colab diga no
        return restante >= coste

    def registrar_consumo(self, fuente_id, cantidad, fecha=None):
        fecha = fecha or datetime.date.today()
        f = self.fuente(fuente_id)
        clave = clave_periodo(f.cuota_periodo, fecha)
        self.uso.setdefault(fuente_id, {})
        self.uso[fuente_id][clave] = \
            self.uso[fuente_id].get(clave, 0) + cantidad
        self.guardar_uso()

    def pausar(self, fuente_id, motivo=""):
        """Pausa una fuente a mano (p. ej. Colab sin GPU disponible)."""
        self.fuente(fuente_id)  # valida que existe
        self.pausadas.add(fuente_id)
        self.guardar_uso()

    def reanudar_fuente(self, fuente_id):
        self.pausadas.discard(fuente_id)
        self.guardar_uso()

    def estado(self, fecha=None):
        """Resumen de todas las fuentes para `estado` / informes."""
        fecha = fecha or datetime.date.today()
        filas = []
        for f in self.fuentes:
            restante = self.restante(f.id, fecha)
            filas.append({
                "id": f.id,
                "nombre": f.nombre,
                "tipo": f.tipo,
                "prioridad": f.prioridad,
                "pausada": f.id in self.pausadas,
                "cuota": (f"{f.cuota_cantidad} {f.cuota_unidad}/{f.cuota_periodo}"
                          if f.cuota_publicada
                          else f"no publicada ({f.cuota_unidad})"),
                "cuota_estado": f.cuota_estado,
                "consumido": self.consumido(f.id, fecha),
                "restante": restante,
                "clips_5s_que_caben": (f.clips_que_caben(restante)
                                       if restante is not None else None),
                "coste_5s": f.coste_5s,
                "coste_estado": f.coste_estado,
                "marca_agua": f.marca_agua,
                "uso_comercial": f.uso_comercial,
                "asignable": f.asignable,
            })
        return filas
