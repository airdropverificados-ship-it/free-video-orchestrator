#!/usr/bin/env python3
"""Tests del orquestador — sin GPU ni red obligatoria.

Usan los datos reales del repo video-generator-repo:
  - ejemplos/capitulo-ejemplo/guion-ejemplo.json y jobs-ejemplo.json
  - prueba-muestra/clips/ (8 clips reales de 5 s, 480x832)
  - apis-gratis-ia/pruebas/piper-voices/ (voz es_ES-sharvard-medium)

Ejecutar desde la raíz del proyecto:
    python -m unittest discover -s tests -v
"""

import datetime
import json
import os
import shutil
import sys
import tempfile
import unittest

SOLUCION = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(os.path.expanduser("~"), "workspace",
                    "video-generator-repo")
sys.path.insert(0, SOLUCION)
sys.path.insert(0, os.path.join(SOLUCION, "voz"))
sys.path.insert(0, os.path.join(SOLUCION, "guion"))

from orquestador.asignar import asignar, estimar_capacidad_semanal  # noqa: E402
from orquestador.cola import Cola  # noqa: E402
from orquestador.fuentes import RegistroFuentes, clave_periodo  # noqa: E402
from orquestador import pipeline, recolectar as recolectar_mod  # noqa: E402
import llm_gratis  # noqa: E402
import piper_tts  # noqa: E402

GUION_EJEMPLO = os.path.join(
    REPO, "ejemplos", "capitulo-ejemplo", "guion-ejemplo.json")
JOBS_EJEMPLO = os.path.join(
    REPO, "ejemplos", "capitulo-ejemplo", "jobs-ejemplo.json")
CLIPS_MUESTRA = os.path.join(REPO, "prueba-muestra", "clips")
VOCES_DIR = os.path.join(os.path.expanduser("~"), "workspace",
                         "apis-gratis-ia", "pruebas", "piper-voices")


def requiere_repo(f):
    return unittest.skipUnless(
        os.path.isdir(REPO), "falta el repo video-generator-repo")(f)


class TestCola(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ruta = os.path.join(self.tmp, "cola.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @requiere_repo
    def test_desde_jobs_y_resumen(self):
        cola = Cola.desde_jobs(self.ruta, JOBS_EJEMPLO)
        self.assertEqual(len(cola.items), 8)
        self.assertEqual(cola.capitulo, "La confesión de Celia")
        self.assertEqual(cola.resumen(),
                         {"pendiente": 8, "en-generacion": 0,
                          "hecho": 0, "fallido": 0})
        self.assertFalse(cola.terminado())

    @requiere_repo
    def test_guardar_y_cargar_reanudable(self):
        cola = Cola.desde_jobs(self.ruta, JOBS_EJEMPLO)
        cola.marcar_en_generacion("clip01", "kaggle")
        cola.marcar_hecho("clip01")
        cola.marcar_en_generacion("clip02", "colab")
        cola.guardar()
        otra = Cola.cargar(self.ruta)
        self.assertEqual(otra.resumen(),
                         {"pendiente": 6, "en-generacion": 1,
                          "hecho": 1, "fallido": 0})
        self.assertEqual(otra.buscar("clip01")["fuente"], "kaggle")

    @requiere_repo
    def test_reanudar_devuelve_en_generacion_a_pendiente(self):
        cola = Cola.desde_jobs(self.ruta, JOBS_EJEMPLO)
        cola.marcar_en_generacion("clip01", "kaggle")
        cola.marcar_en_generacion("clip02", "colab")
        vueltos = cola.reanudar()
        self.assertEqual(vueltos, 2)
        self.assertEqual(cola.resumen()["pendiente"], 8)
        self.assertIsNone(cola.buscar("clip01")["fuente"])

    @requiere_repo
    def test_fallido_tras_agotar_reintentos(self):
        cola = Cola.desde_jobs(self.ruta, JOBS_EJEMPLO)
        for _ in range(3):
            cola.marcar_en_generacion("clip01", "kaggle")
            cola.marcar_fallido("clip01", "error de prueba")
        self.assertEqual(cola.buscar("clip01")["estado"], "fallido")
        self.assertEqual(cola.buscar("clip01")["intentos"], 3)

    @requiere_repo
    def test_fallo_con_reintentos_vuelve_a_pendiente(self):
        cola = Cola.desde_jobs(self.ruta, JOBS_EJEMPLO)
        cola.marcar_en_generacion("clip01", "kaggle")
        cola.marcar_fallido("clip01", "error de prueba")
        self.assertEqual(cola.buscar("clip01")["estado"], "pendiente")

    def test_transiciones_invalidas(self):
        cola = Cola(self.ruta)
        cola.items = [{"clip_id": "clip01", "estado": "pendiente",
                       "fuente": None, "intentos": 0, "error": None,
                       "duracion_s": 5, "resolucion": None}]
        with self.assertRaises(ValueError):
            cola.marcar_hecho("clip01")  # pendiente -> hecho, no
        with self.assertRaises(KeyError):
            cola.buscar("clip99")


class TestFuentes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.uso = os.path.join(self.tmp, "uso.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_registro_carga_10_fuentes(self):
        r = RegistroFuentes(uso_ruta=self.uso)
        self.assertEqual(len(r.fuentes), 10)
        # Prioridad: GPU libre primero, APIs después.
        tipos = [f.tipo for f in r.fuentes]
        self.assertEqual(tipos[:5], ["gpu-libre"] * 5)
        self.assertIn("api-video", tipos)

    def test_cuotas_del_informe(self):
        r = RegistroFuentes(uso_ruta=self.uso)
        self.assertEqual(r.fuente("kaggle").cuota_cantidad, 1800)
        self.assertEqual(r.fuente("kaggle").cuota_periodo, "semana")
        # Bonos únicos (corrección 21 nov 2026): Lightning ya no es
        # mensual (5 créditos una sola vez ≈ 9 h T4 = 540 min) y Lium
        # es $5 una sola vez (~20,8 h estimadas = 1.248 min).
        self.assertEqual(r.fuente("lightning").cuota_cantidad, 540)
        self.assertEqual(r.fuente("lightning").cuota_periodo, "una-vez")
        self.assertEqual(r.fuente("lium").cuota_cantidad, 1248)
        self.assertEqual(r.fuente("lium").cuota_periodo, "una-vez")
        # Akash: 0 h hasta verificar si la GPU de prueba funciona
        # (conflicto en su documentación oficial).
        self.assertEqual(r.fuente("akash").cuota_cantidad, 0)
        self.assertEqual(r.fuente("dreamina").cuota_cantidad, 120)
        self.assertEqual(r.fuente("kling").cuota_cantidad, 66)
        self.assertEqual(r.fuente("pixverse").cuota_cantidad, 30)
        self.assertEqual(r.fuente("zerogpu").cuota_cantidad, 5)
        self.assertIsNone(r.fuente("colab").cuota_cantidad)  # no publicada
        self.assertEqual(r.fuente("colab").cuota_estado, "no-publicada")
        self.assertEqual(r.fuente("kling").coste_5s, 30)  # peor caso

    def test_marcas_de_agua_y_licencia(self):
        r = RegistroFuentes(uso_ruta=self.uso)
        for fid in ("colab", "kaggle", "lium", "lightning"):
            self.assertFalse(r.fuente(fid).marca_agua)
            self.assertEqual(r.fuente(fid).uso_comercial, "permitido")
        for fid in ("dreamina", "kling", "pixverse"):
            self.assertTrue(r.fuente(fid).marca_agua)
        self.assertEqual(r.fuente("kling").uso_comercial, "prohibido")

    def test_consumo_y_reseteo_diario(self):
        r = RegistroFuentes(uso_ruta=self.uso)
        lunes = datetime.date(2026, 11, 16)
        martes = datetime.date(2026, 11, 17)
        r.registrar_consumo("dreamina", 44, lunes)
        self.assertEqual(r.consumido("dreamina", lunes), 44)
        self.assertEqual(r.restante("dreamina", lunes), 76)
        # Al día siguiente, la cuota diaria vuelve a estar entera.
        self.assertEqual(r.consumido("dreamina", martes), 0)
        self.assertEqual(r.restante("dreamina", martes), 120)

    def test_reseteo_semanal(self):
        r = RegistroFuentes(uso_ruta=self.uso)
        lunes1 = datetime.date(2026, 11, 16)
        domingo1 = datetime.date(2026, 11, 22)
        lunes2 = datetime.date(2026, 11, 23)
        r.registrar_consumo("kaggle", 500, lunes1)
        self.assertEqual(r.consumido("kaggle", domingo1), 500)
        self.assertEqual(r.consumido("kaggle", lunes2), 0)
        self.assertEqual(clave_periodo("semana", domingo1),
                         clave_periodo("semana", lunes1))

    def test_bono_unico_no_se_resetea(self):
        r = RegistroFuentes(uso_ruta=self.uso)
        # Un bono único no tiene periodo que resetear: el consumo de
        # hoy sigue contado dentro de un mes y dentro de un año.
        hoy = datetime.date(2026, 11, 21)
        dentro_de_un_mes = datetime.date(2026, 12, 21)
        dentro_de_un_ano = datetime.date(2027, 11, 21)
        self.assertEqual(clave_periodo("una-vez", hoy), "una-vez")
        r.registrar_consumo("lightning", 100, hoy)
        self.assertEqual(r.consumido("lightning", hoy), 100)
        self.assertEqual(r.consumido("lightning", dentro_de_un_mes), 100)
        self.assertEqual(r.consumido("lightning", dentro_de_un_ano), 100)
        self.assertEqual(r.restante("lightning", dentro_de_un_ano), 440)
        # Y cuando se agota, no cabe ningún clip más, nunca.
        r.registrar_consumo("lightning", 440, hoy)
        self.assertFalse(r.cabe_clip("lightning", 5, dentro_de_un_ano))

    def test_cabe_clip_y_pausa(self):
        r = RegistroFuentes(uso_ruta=self.uso)
        # PixVerse: 30 créditos/día, un clip de 5 s cuesta 50 -> no cabe.
        self.assertFalse(r.cabe_clip("pixverse", 5))
        # Dreamina: 120 créditos, clip de 5 s = 22 -> cabe.
        self.assertTrue(r.cabe_clip("dreamina", 5))
        r.pausar("dreamina")
        self.assertFalse(r.cabe_clip("dreamina", 5))
        r.reanudar_fuente("dreamina")
        self.assertTrue(r.cabe_clip("dreamina", 5))

    def test_uso_persiste_entre_instancias(self):
        r = RegistroFuentes(uso_ruta=self.uso)
        r.registrar_consumo("kling", 30)
        r2 = RegistroFuentes(uso_ruta=self.uso)
        self.assertEqual(r2.consumido("kling"), 30)


class TestAsignar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ruta_cola = os.path.join(self.tmp, "cola.json")
        self.uso = os.path.join(self.tmp, "uso.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _registro_sin_gpu(self):
        """Registro con la GPU libre pausada: fuerza el uso de APIs."""
        r = RegistroFuentes(uso_ruta=self.uso)
        for fid in ("colab", "kaggle", "lium", "lightning"):
            r.pausar(fid)
        return r

    @requiere_repo
    def test_gpu_libre_primero(self):
        cola = Cola.desde_jobs(self.ruta_cola, JOBS_EJEMPLO)
        r = RegistroFuentes(uso_ruta=self.uso)
        plan = asignar(cola, r)
        self.assertEqual(len(plan["asignados"]), 8)
        self.assertEqual(plan["sin_fuente"], [])
        # Colab no tiene cuota publicada: se lleva todos los clips.
        self.assertTrue(all(a["fuente"] == "colab"
                            for a in plan["asignados"]))
        self.assertTrue(all(not a["marca_agua"]
                            for a in plan["asignados"]))

    @requiere_repo
    def test_apis_solo_como_complemento_y_marcadas(self):
        cola = Cola.desde_jobs(self.ruta_cola, JOBS_EJEMPLO)
        r = self._registro_sin_gpu()
        plan = asignar(cola, r)
        # Dreamina: 120/22 = 5 clips; Kling: 66/30 = 2 clips;
        # PixVerse no da para un clip de 5 s; queda 1 sin fuente.
        fuentes = [a["fuente"] for a in plan["asignados"]]
        self.assertEqual(fuentes.count("dreamina"), 5)
        self.assertEqual(fuentes.count("kling"), 2)
        self.assertEqual(len(plan["sin_fuente"]), 1)
        self.assertTrue(all(a["marca_agua"] for a in plan["asignados"]))
        self.assertTrue(all(a["uso_comercial"] != "permitido"
                            for a in plan["asignados"]))

    @requiere_repo
    def test_sin_cuota_nadie_promete_nada(self):
        cola = Cola.desde_jobs(self.ruta_cola, JOBS_EJEMPLO)
        r = self._registro_sin_gpu()
        # Agotar también las APIs.
        r.registrar_consumo("dreamina", 120)
        r.registrar_consumo("kling", 66)
        plan = asignar(cola, r)
        self.assertEqual(plan["asignados"], [])
        self.assertEqual(len(plan["sin_fuente"]), 8)

    def test_capacidad_semanal_estimada(self):
        r = RegistroFuentes(uso_ruta=self.uso)
        gpu, api, detalle = estimar_capacidad_semanal(r)
        # Solo Kaggle es recurrente con cuota publicada: 1800/20 = 90.
        # Lightning y Lium son bonos únicos: NO suman a la capacidad
        # semanal (corrección 21 nov 2026; antes Lightning contaba
        # 1320/4,33/20 = 15 como si fuera mensual).
        # Dreamina 840/22 = 38; Kling 462/30 = 15; PixVerse 210/50 = 4.
        self.assertEqual(gpu, 90)
        self.assertEqual(api, 57)
        colab = next(d for d in detalle if d["id"] == "colab")
        self.assertIsNone(colab["clips_semana"])  # cuota no publicada
        for fid in ("lightning", "lium"):
            bono = next(d for d in detalle if d["id"] == fid)
            self.assertEqual(bono["clips_semana"], 0)
            self.assertIn("bono único", bono["nota"])


class TestRecolectar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ruta_cola = os.path.join(self.tmp, "cola.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @requiere_repo
    @unittest.skipUnless(recolectar_mod.ffprobe_disponible(),
                         "ffprobe no disponible")
    def test_clips_reales_de_la_muestra_pasan(self):
        cola = Cola.desde_jobs(self.ruta_cola, JOBS_EJEMPLO)
        for item in cola.items:
            cola.marcar_en_generacion(item["clip_id"], "colab")
        informe = recolectar_mod.recolectar(cola, CLIPS_MUESTRA)
        self.assertEqual(len(informe["verificados"]), 8)
        self.assertEqual(informe["fallidos"], [])
        self.assertEqual(informe["sin_aparecer"], [])
        self.assertEqual(cola.resumen()["hecho"], 8)
        for v in informe["verificados"]:
            self.assertAlmostEqual(v["duracion_s"], 5.0, places=1)

    @requiere_repo
    @unittest.skipUnless(recolectar_mod.ffprobe_disponible(),
                         "ffprobe no disponible")
    def test_clip_corrupto_falla_y_vuelve_a_pendiente(self):
        clips = os.path.join(self.tmp, "clips")
        os.makedirs(clips)
        # Copia real de clip01 + un clip02 corrupto (basura).
        shutil.copy2(os.path.join(CLIPS_MUESTRA, "clip01.mp4"),
                     os.path.join(clips, "clip01.mp4"))
        with open(os.path.join(clips, "clip02.mp4"), "wb") as f:
            f.write(b"esto no es un video" * 1000)
        cola = Cola.desde_jobs(self.ruta_cola, JOBS_EJEMPLO)
        cola.marcar_en_generacion("clip01", "colab")
        cola.marcar_en_generacion("clip02", "colab")
        informe = recolectar_mod.recolectar(cola, clips)
        self.assertEqual(len(informe["verificados"]), 1)
        self.assertEqual(len(informe["fallidos"]), 1)
        self.assertEqual(informe["fallidos"][0]["clip_id"], "clip02")
        # Con reintentos disponibles, vuelve a pendiente para regenerar.
        self.assertEqual(cola.buscar("clip02")["estado"], "pendiente")

    @requiere_repo
    @unittest.skipUnless(recolectar_mod.ffprobe_disponible(),
                         "ffprobe no disponible")
    def test_clip_que_no_aparece_no_se_marca_fallo(self):
        cola = Cola.desde_jobs(self.ruta_cola, JOBS_EJEMPLO)
        cola.marcar_en_generacion("clip01", "colab")
        informe = recolectar_mod.recolectar(
            cola, os.path.join(self.tmp, "vacio"))
        self.assertEqual(len(informe["sin_aparecer"]), 1)
        self.assertEqual(cola.buscar("clip01")["estado"], "en-generacion")
        # Con marcar_faltantes=True sí vuelve a pendiente.
        recolectar_mod.recolectar(cola, os.path.join(self.tmp, "vacio"),
                                  marcar_faltantes=True)
        self.assertEqual(cola.buscar("clip01")["estado"], "pendiente")

    @requiere_repo
    @unittest.skipUnless(recolectar_mod.ffprobe_disponible(),
                         "ffprobe no disponible")
    def test_duracion_fuera_de_tolerancia_falla(self):
        ok, info = recolectar_mod.verificar_clip(
            os.path.join(CLIPS_MUESTRA, "clip01.mp4"), 10.0)
        self.assertFalse(ok)
        self.assertIn("5.00", info["error"])
        ok, _ = recolectar_mod.verificar_clip(
            os.path.join(CLIPS_MUESTRA, "clip01.mp4"), 5.0)
        self.assertTrue(ok)


class TestPipeline(unittest.TestCase):
    @requiere_repo
    def test_validar_guion_ejemplo_pasa(self):
        ok, informe = pipeline.validar_guion(REPO, GUION_EJEMPLO)
        self.assertTrue(ok, informe.get("errores"))
        self.assertEqual(informe["clips"], 8)

    @requiere_repo
    def test_preparar_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = os.path.join(tmp, "jobs.json")
            ok, detalle = pipeline.preparar_jobs(REPO, GUION_EJEMPLO, salida)
            self.assertTrue(ok, detalle)
            with open(salida, encoding="utf-8") as f:
                jobs = json.load(f)
            self.assertEqual(len(jobs["jobs"]), 8)
            self.assertEqual(jobs["jobs"][0]["num_frames"], 121)

    def test_resolver_repo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            pipeline.resolver_repo("/ruta/que/no/existe")


class TestLlmGratis(unittest.TestCase):
    def test_extraer_json(self):
        self.assertEqual(
            llm_gratis.extraer_json('texto antes {"a": 1} texto después'),
            {"a": 1})
        self.assertIsNone(llm_gratis.extraer_json("sin json aquí"))

    def test_calcular_espera_pollinations(self):
        # Sin llamada previa: no se espera.
        self.assertEqual(llm_gratis.calcular_espera(None, 1000.0), 0.0)
        # Llamada hace 10 s: faltan 30 s.
        self.assertAlmostEqual(
            llm_gratis.calcular_espera(990.0, 1000.0), 30.0)
        # Llamada hace 50 s: ya se puede llamar.
        self.assertEqual(llm_gratis.calcular_espera(950.0, 1000.0), 0.0)

    def test_groq_sin_clave_falla_con_mensaje_claro(self):
        os.environ.pop("GROQ_API_KEY", None)
        with self.assertRaises(RuntimeError) as ctx:
            llm_gratis.generar_con_groq("hola")
        self.assertIn("GROQ_API_KEY", str(ctx.exception))
        self.assertIn("pollinations", str(ctx.exception).lower())


class TestPiperTts(unittest.TestCase):
    def test_mensaje_instalacion_explica_como_instalar(self):
        msg = piper_tts.mensaje_instalacion()
        self.assertIn("pip install piper-tts", msg)
        self.assertIn("es_ES-sharvard-medium", msg)

    @unittest.skipUnless(
        os.path.isdir(VOCES_DIR), "falta la carpeta de voces de Piper")
    def test_voz_sharvard_existe_en_carpeta_de_pruebas(self):
        modelo = piper_tts.buscar_modelo("es_ES-sharvard-medium", VOCES_DIR)
        self.assertIsNotNone(modelo)
        self.assertTrue(modelo.endswith(".onnx"))
        self.assertGreater(os.path.getsize(modelo), 10_000_000)

    def test_voz_inexistente_no_se_encuentra(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(
                piper_tts.buscar_modelo("es_ES-sharvard-medium", tmp))


if __name__ == "__main__":
    unittest.main()
