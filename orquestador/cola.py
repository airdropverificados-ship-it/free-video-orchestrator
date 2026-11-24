#!/usr/bin/env python3
"""Cola de clips reanudable (estado JSON).

Un capítulo es una cola de clips. Cada clip pasa por:

    pendiente -> en-generacion -> hecho
                          |-> fallido (tras agotar los reintentos)

El estado vive en un único archivo JSON (por defecto `cola.json` dentro
de la carpeta de trabajo del capítulo). Se guarda con escritura atómica
(temporal + renombre) para que un corte a mitad no corrompa la cola, y
cualquier corrida puede reanudarse: `reanudar()` devuelve a `pendiente`
los clips que quedaron en `en-generacion` (p. ej. porque la sesión de
Colab/Kaggle murió a mitad).
"""

import json
import os
import tempfile

ESTADOS = ("pendiente", "en-generacion", "hecho", "fallido")

MAX_REINTENTOS = 3


class Cola:
    def __init__(self, ruta, capitulo=""):
        self.ruta = ruta
        self.capitulo = capitulo
        self.items = []  # lista de dicts, en orden de clip

    # -- construcción -------------------------------------------------
    @classmethod
    def desde_jobs(cls, ruta_cola, jobs_ruta, capitulo=""):
        """Crea una cola desde un jobs.json del repo (preparar_jobs.py)."""
        with open(jobs_ruta, encoding="utf-8") as f:
            manifiesto = json.load(f)
        cola = cls(ruta_cola, capitulo or manifiesto.get("capitulo", ""))
        for job in manifiesto["jobs"]:
            cola.items.append({
                "clip_id": job["clip_id"],
                "estado": "pendiente",
                "fuente": None,
                "intentos": 0,
                "error": None,
                "duracion_s": job["duracion_s"],
                "resolucion": job.get("resolucion"),
            })
        return cola

    @classmethod
    def desde_guion(cls, ruta_cola, guion_ruta):
        """Crea una cola directamente desde un guion JSON."""
        with open(guion_ruta, encoding="utf-8") as f:
            guion = json.load(f)
        cola = cls(ruta_cola, guion.get("capitulo", ""))
        for clip in guion["clips"]:
            cola.items.append({
                "clip_id": clip["id"],
                "estado": "pendiente",
                "fuente": None,
                "intentos": 0,
                "error": None,
                "duracion_s": clip["duracion_s"],
                "resolucion": None,
            })
        return cola

    # -- persistencia -------------------------------------------------
    def guardar(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.ruta)),
                    exist_ok=True)
        datos = {"capitulo": self.capitulo, "items": self.items}
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(
            os.path.abspath(self.ruta)), prefix=".cola-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.ruta)
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    @classmethod
    def cargar(cls, ruta):
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        cola = cls(ruta, datos.get("capitulo", ""))
        cola.items = datos["items"]
        return cola

    # -- acceso -------------------------------------------------------
    def buscar(self, clip_id):
        for item in self.items:
            if item["clip_id"] == clip_id:
                return item
        raise KeyError(f"clip no está en la cola: {clip_id}")

    def por_estado(self, estado):
        if estado not in ESTADOS:
            raise ValueError(f"estado desconocido: {estado}")
        return [i for i in self.items if i["estado"] == estado]

    def pendientes(self):
        return self.por_estado("pendiente")

    def resumen(self):
        return {e: len(self.por_estado(e)) for e in ESTADOS}

    def terminado(self):
        """True si no queda ningún clip pendiente ni en generación."""
        return not self.por_estado("pendiente") \
            and not self.por_estado("en-generacion")

    # -- transiciones -------------------------------------------------
    def marcar_en_generacion(self, clip_id, fuente):
        item = self.buscar(clip_id)
        if item["estado"] not in ("pendiente", "fallido"):
            raise ValueError(
                f"{clip_id} está en '{item['estado']}': no se puede "
                "poner en generación")
        item["estado"] = "en-generacion"
        item["fuente"] = fuente
        item["intentos"] += 1
        item["error"] = None

    def marcar_hecho(self, clip_id):
        item = self.buscar(clip_id)
        if item["estado"] != "en-generacion":
            raise ValueError(
                f"{clip_id} está en '{item['estado']}': solo un clip "
                "en generación puede marcarse como hecho")
        item["estado"] = "hecho"
        item["error"] = None

    def marcar_fallido(self, clip_id, error):
        """Marca un fallo. Si quedan reintentos, vuelve a `pendiente`
        para que se reasigne; si no, queda en `fallido`."""
        item = self.buscar(clip_id)
        item["error"] = str(error)
        if item["intentos"] >= MAX_REINTENTOS:
            item["estado"] = "fallido"
        else:
            item["estado"] = "pendiente"
            item["fuente"] = None

    def reanudar(self):
        """Los clips en `en-generacion` vuelven a `pendiente`.

        Se llama al empezar una corrida nueva: una sesión de GPU que
        murió no deja constancia de qué estaba generando, así que esos
        clips se reasignan (la recolecta verifica después si alguno ya
        existe en disco y lo marca hecho sin regenerarlo).
        """
        vueltos = 0
        for item in self.items:
            if item["estado"] == "en-generacion":
                item["estado"] = "pendiente"
                item["fuente"] = None
                vueltos += 1
        return vueltos
