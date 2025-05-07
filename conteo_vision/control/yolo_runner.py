# conteo_vision/control/yolo_runner.py
import threading
import time
import cv2
import numpy as np
from datetime import datetime
from ultralytics import YOLO
import os
import django
from django.conf import settings

# Inicializa entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_conteo.settings')
django.setup()

from conteo_api.models import ConteoConfig, ModeloConfig, ConteoPersonas, Poligono, Estado
from conteo_vision.utils.tracker import Tracker

procesos = {}

class ConteoYOLO(threading.Thread):
    def __init__(self, camara_id, rtsp_url, modelo_path):
        super().__init__()
        self.camara_id = camara_id
        self.rtsp_url = rtsp_url
        self.modelo_path = modelo_path
        self._activo = True

    def run(self):
        print(f"[{self.camara_id}] Iniciando conteo con modelo {self.modelo_path}")
        model = YOLO(self.modelo_path)
        tracker = Tracker()
        cap = cv2.VideoCapture(self.rtsp_url)
        if not cap.isOpened():
            print(f"[{self.camara_id}] No se pudo abrir la cámara.")
            return

        # Obtener polígonos (ROI1 y ROI2)
        rois = Poligono.objects.filter(camara_id=self.camara_id).order_by('id')[:2]
        if len(rois) < 2:
            print(f"[{self.camara_id}] Faltan áreas ROI en la base de datos.")
            return

        roi_coords = []
        for roi in rois:
            coords = list(roi.coordenadas.values_list('x', 'y'))
            roi_coords.append(np.array(coords, np.int32).reshape((-1, 1, 2)))

        ROI1_CNT, ROI2_CNT = roi_coords[0], roi_coords[1]

        people_entering = {}
        people_exiting = {}
        entring = set()
        exiting = set()

        estado_activo = Estado.objects.get_or_create(estado='activado')[0]
        poligonos = list(rois)  # asociar ambos

        frame_id = 0
        while self._activo:
            ret, frame = cap.read()
            if not ret:
                break
            frame_id += 1
            if frame_id % 2:
                continue

            frame = cv2.resize(frame, (1020, 500))
            res = model.predict(frame, conf=0.4, iou=0.6, imgsz=640, classes=[0], max_det=60, verbose=False)[0]
            boxes = res.boxes.xyxy.cpu().numpy().astype(int)
            rects = [[x1, y1, x2-x1, y2-y1] for x1,y1,x2,y2 in boxes]
            tracked = tracker.update(rects)

            for x, y, w, h, tid in tracked:
                cx, cy = x + w, y + h
                if cv2.pointPolygonTest(ROI2_CNT, (float(cx), float(cy)), False) >= 0:
                    people_entering[tid] = (cx, cy)
                if tid in people_entering and cv2.pointPolygonTest(ROI1_CNT, (float(cx), float(cy)), False) >= 0:
                    entring.add(tid)
                if cv2.pointPolygonTest(ROI1_CNT, (float(cx), float(cy)), False) >= 0:
                    people_exiting[tid] = (cx, cy)
                if tid in people_exiting and cv2.pointPolygonTest(ROI2_CNT, (float(cx), float(cy)), False) >= 0:
                    exiting.add(tid)

            # Registrar cada 10 segundos
            if frame_id % 60 == 0:
                ahora = datetime.now()
                for poligono in poligonos:
                    ConteoPersonas.objects.create(
                        fecha=ahora.date(),
                        hora=ahora.time(),
                        poligono=poligono,
                        estado=estado_activo,
                        contador_ingreso=len(entring),
                        contador_salida=len(exiting)
                    )
                print(f"[{self.camara_id}] Guardado: Ingresan={len(entring)} | Salen={len(exiting)}")
                entring.clear()
                exiting.clear()

        cap.release()
        print(f"[{self.camara_id}] Conteo detenido.")

    def detener(self):
        self._activo = False


def iniciar_conteo(camara_id, rtsp_url):
    if camara_id in procesos:
        return f"Proceso de cámara {camara_id} ya está en ejecución."

    config = ConteoConfig.objects.filter(camara_id=camara_id, estado__estado='activado').first()
    if not config:
        return f"No hay configuración de conteo activa para cámara {camara_id}."

    modelo_path = config.modelo.url_model
    if not os.path.exists(modelo_path):
        return f"Modelo no encontrado en la ruta: {modelo_path}"

    hilo = ConteoYOLO(camara_id, rtsp_url, modelo_path)
    procesos[camara_id] = hilo
    hilo.start()
    return f"Conteo iniciado para cámara {camara_id} con modelo {modelo_path}"


def detener_conteo(camara_id):
    if camara_id in procesos:
        procesos[camara_id].detener()
        procesos[camara_id].join()
        del procesos[camara_id]
        return f"Conteo detenido para cámara {camara_id}"
    return f"No hay proceso activo para cámara {camara_id}"
