from django.http import HttpResponse
from rest_framework import viewsets
from django.shortcuts import render
from django.db.models import Sum, Count
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime
import cv2
import numpy as np
import os
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from conteo_vision.control.yolo_runner import iniciar_conteo, detener_conteo
from .models import Estado, Camara, Poligono, Coordenada, ConteoPersonas, ModeloConfig, TrackingConfig, ConteoConfig
from django.utils.timezone import now
from .serializers import (
    EstadoSerializer,
    CamaraSerializer,
    PoligonoSerializer,
    CoordenadaSerializer,
    ConteoPersonasSerializer
)
# from django.urls import path, include
@login_required
def lista_camaras(request):
    camaras = Camara.objects.all()
    return render(request, 'conteo_api/lista_camaras.html', {'camaras': camaras})
@login_required
def lista_conteos(request):
    conteos = ConteoPersonas.objects.all().order_by('-fecha', '-hora')
    return render(request, 'conteo_api/lista_conteos.html', {'conteos': conteos})

# This is a sample view function.
class EstadoViewSet(viewsets.ModelViewSet):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer

class CamaraViewSet(viewsets.ModelViewSet):
    queryset = Camara.objects.all()
    serializer_class = CamaraSerializer

class PoligonoViewSet(viewsets.ModelViewSet):
    queryset = Poligono.objects.all()
    serializer_class = PoligonoSerializer

class CoordenadaViewSet(viewsets.ModelViewSet):
    queryset = Coordenada.objects.all()
    serializer_class = CoordenadaSerializer

class ConteoPersonasViewSet(viewsets.ModelViewSet):
    queryset = ConteoPersonas.objects.all()
    serializer_class = ConteoPersonasSerializer
# This is a sample view function.
@login_required
def dashboard(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    camara_id = request.GET.get('camara')

    conteos = ConteoPersonas.objects.select_related('camara')

    if fecha_inicio:
        conteos = conteos.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        conteos = conteos.filter(fecha__lte=fecha_fin)
    if camara_id and camara_id != 'todos':
        conteos = conteos.filter(camara_id=camara_id)

    total_ingresos = conteos.aggregate(total=Sum('contador_ingreso'))['total'] or 0
    total_salidas = conteos.aggregate(total=Sum('contador_salida'))['total'] or 0

    camaras_activas = Camara.objects.filter(estado__estado='Activado')
    camaras = Camara.objects.all()

    return render(request, 'conteo_api/dashboard.html', {
        'conteos': conteos.order_by('-fecha', '-hora'),
        'total_ingresos': total_ingresos,
        'total_salidas': total_salidas,
        'camaras_activas': camaras_activas.count(),
        'camaras': camaras,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'camara_id': camara_id,
    })
#configurar_camara view
@login_required
def configurar_camara(request):
    camaras = Camara.objects.select_related('estado').all()
    estados = Estado.objects.all()
    marcas = ['Hikvision', 'Dahua', 'TP-Link', 'Xiaomi', 'Genérica']

    if request.method == 'POST':
        id_camara = request.POST.get('id')
        data = {
            'nombre': request.POST['nombre'],
            'marca': request.POST['marca'],
            'protocolo': request.POST['protocolo'],
            'usuario': request.POST['usuario'],
            'password': request.POST['password'],
            'direccion_ip': request.POST['direccion_ip'],
            'puerto': request.POST['puerto'],
            'streaming_path': request.POST['streaming_path'],
            'estado_id': request.POST['estado_id'],
            
        }


        if id_camara:  # Editar
            Camara.objects.filter(id=id_camara).update(**data)
        else:  # Crear
            Camara.objects.create(**data)

        return redirect('configurar_camara')

    return render(request, 'conteo_api/configurar_camara.html', {
        'camaras': camaras,
        'estados': estados,
        'marcas': marcas
    })

@login_required
def editar_camara(request, pk):
    camara = get_object_or_404(Camara, pk=pk)
    estados = Estado.objects.all()
    marcas = ['Hikvision', 'Dahua', 'TP-Link', 'Xiaomi', 'Axis', 'Reolink', 'Genérica']

    if request.method == 'POST':
        data = {
            'nombre': request.POST['nombre'],
            'marca': request.POST['marca'],
            'protocolo': request.POST['protocolo'],
            'usuario': request.POST['usuario'],
            'password': request.POST['password'],
            'direccion_ip': request.POST['direccion_ip'],
            'puerto': request.POST['puerto'],
            'streaming_path': request.POST['streaming_path'],
            'estado_id': request.POST['estado_id'],
        }

        # Asignar los valores a la instancia
        for key, value in data.items():
            setattr(camara, key, value)
        camara.save()


        return redirect('configurar_camara')

    return render(request, 'conteo_api/configurar_camara.html', {
        'editar': camara,
        'camaras': Camara.objects.all(),
        'estados': estados,
        'marcas': marcas
    })



@login_required
def eliminar_camara(request, pk):
    camara = get_object_or_404(Camara, pk=pk)
    camara.delete()
    return redirect('configurar_camara')

#---------
#configurar poligono 
def crear_area_roi(request):
    camaras = Camara.objects.all()
    return render(request, 'conteo_api/crear_area_roi.html', {'camaras': camaras})

def guardar_roi(request):
    if request.method == 'POST':
        camara_id = request.POST.get('camara_id')
        tipo = request.POST.get('tipo')  # entrada o salida
        puntos = request.POST.getlist('puntos[]')  # ['x1,y1', 'x2,y2', ...]

        camara = get_object_or_404(Camara, id=camara_id)
        estado = Estado.objects.get(estado='Activado')  # por defecto

        nombre_poligono = f"{tipo}_{camara.id}"
        poligono, creado = Poligono.objects.get_or_create(
            nombre_poligono=nombre_poligono,
            camara=camara,
            defaults={'estado': estado, 'area_interes': tipo}
        )
        if not creado:
            Coordenada.objects.filter(poligono=poligono).delete()

        for punto in puntos:
            x, y = map(int, punto.split(','))
            Coordenada.objects.create(poligono=poligono, x=x, y=y)

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)
# This function generates a snapshot from the camera stream and saves it to the server.
def generar_snapshot(request, camara_id):
    try:
        cam = Camara.objects.get(pk=camara_id)
        rtsp_url = f"rtsp://{cam.usuario}:{cam.password}@{cam.direccion_ip}:{cam.puerto}/{cam.streaming_path}"
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return JsonResponse({'error': 'No se pudo capturar imagen'}, status=500)

        dir_path = os.path.join(settings.MEDIA_ROOT, f"camaras/{camara_id}")
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, "snapshot.jpg")
        cv2.imwrite(path, frame)
        return JsonResponse({'mensaje': 'Snapshot generado correctamente'})

    except Camara.DoesNotExist:
        return JsonResponse({'error': 'Cámara no encontrada'}, status=404)

def generar_rtsp_url(cam):
    return f"rtsp://{cam.usuario}:{cam.password}@{cam.direccion_ip}:{cam.puerto}/{cam.streaming_path}?udp"


def stream_generator(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        print(f"[❌] No se pudo abrir el stream: {rtsp_url}")
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, jpeg = cv2.imencode('.jpg', frame)
        if jpeg is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
    cap.release()

from django.http import StreamingHttpResponse


def generar_frames(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)
    while True:
        success, frame = cap.read()
        if not success:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def stream_camara(request, camara_id):
    try:
        cam = Camara.objects.get(pk=camara_id)
        rtsp_url = generar_rtsp_url(cam)  # asegúrate que esta función funcione bien
        return StreamingHttpResponse(
            stream_generator(rtsp_url),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
    except Camara.DoesNotExist:
        return HttpResponse('Cámara no encontrada', status=404)

from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def guardar_roi(request, camara_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        camara = Camara.objects.get(pk=camara_id)
        estado_activo = Estado.objects.get_or_create(estado='Activado')[0]

        # Borrar ROIs anteriores por cámara
        Poligono.objects.filter(camara=camara).delete()

        for roi_num in (1, 2):
            area_interes = f"ROI{roi_num}"
            nombre = f"{area_interes} - Cámara {camara.id}"
            poligono = Poligono.objects.create(
                nombre_poligono=nombre,
                camara=camara,
                estado=estado_activo,
                area_interes=area_interes
            )
            for x, y in data[str(roi_num)]:
                Coordenada.objects.create(poligono=poligono, x=int(x), y=int(y))

        return JsonResponse({'mensaje': 'Áreas ROI guardadas correctamente.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def roi_poligonos(request, camara_id):
    try:
        camara = Camara.objects.get(pk=camara_id)
        poligonos = Poligono.objects.filter(camara=camara)

        data = []
        for p in poligonos:
            coords = list(p.coordenadas.values_list('x', 'y'))
            data.append({
                'nombre': p.nombre_poligono,
                'area_interes': p.area_interes,
                'coordenadas': coords
            })

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



#configurar_modelo view
modelos_yolo = [
    ('yolo11n.pt', 'YOLOv11 Nano'),
    ('yolo11s.pt', 'YOLOv11 Small'),
    ('yolo11m.pt', 'YOLOv11 Medium'),
    ('yolo11l.pt', 'YOLOv11 Large'),
    ('yolo11x.pt', 'YOLOv11 XLarge'),
]

@login_required
def configurar_modelo(request):
    modelos = ModeloConfig.objects.all()
    camaras = Camara.objects.all()

    if request.method == 'POST':
        modelo = ModeloConfig.objects.create(
            nombre_modelo=request.POST['nombre_modelo'],
            modelo=request.POST['modelo'],
            image_size=request.POST['image_size'],
            stride=request.POST['stride'],
            confidence_threshold=request.POST['confidence_threshold'],
            device=request.POST['device'],
            classes=request.POST['classes'],
            iou=request.POST.get('iou', 0.7),
            max_det=request.POST.get('max_det', 80),
        )

        TrackingConfig.objects.create(
            distance_threshold=request.POST['tracking_distance_threshold'],
            dwell_time_threshold=request.POST['dwell_time_threshold'],
            modelo=modelo
        )

        return redirect('configurar_modelo')

    return render(request, 'conteo_api/configurar_modelo.html', {
        'modelos': modelos,
        'camaras': camaras,
        'modelos_yolo': modelos_yolo
    })

@login_required
def eliminar_modelo(request, pk):
    modelo = get_object_or_404(ModeloConfig, pk=pk)
    modelo.delete()
    return redirect('configurar_modelo')

@login_required
def editar_modelo(request, pk):
    modelo = get_object_or_404(ModeloConfig, pk=pk)
    tracking = modelo.trackingconfig_set.first()

    if request.method == 'POST':
        modelo.nombre_modelo = request.POST['nombre_modelo']
        modelo.modelo = request.POST['modelo']
        modelo.image_size = request.POST['image_size']
        modelo.stride = request.POST['stride']
        modelo.confidence_threshold = request.POST['confidence_threshold']
        modelo.device = request.POST['device']
        modelo.classes = request.POST['classes']
        modelo.iou = request.POST.get('iou', 0.7)
        modelo.max_det = request.POST.get('max_det', 80)
        modelo.save()

        if tracking:
            tracking.distance_threshold = request.POST['tracking_distance_threshold']
            tracking.dwell_time_threshold = request.POST['dwell_time_threshold']
            tracking.save()

        return redirect('configurar_modelo')

    return render(request, 'conteo_api/configurar_modelo.html', {
        'editar': modelo,
        'modelos': ModeloConfig.objects.all(),
        'camaras': Camara.objects.all(),
        'tracking': tracking,
        'modelos_yolo': modelos_yolo
    })


@login_required
def configurar_evento(request):
    eventos = ConteoConfig.objects.select_related('camara', 'modelo').all()
    camaras = Camara.objects.all()
    modelos = ModeloConfig.objects.all()
    estados = Estado.objects.all()

    if request.method == 'POST':
        ConteoConfig.objects.create(
            desde_hora=request.POST['desde_hora'],
            hasta_hora=request.POST['hasta_hora'],
            camara_id=request.POST['camara_id'],
            modelo_id=request.POST['modelo_id'],
            estado_id=request.POST['estado_id']
        )
        return redirect('configurar_evento')

    return render(request, 'conteo_api/configurar_evento.html', {
        'eventos': eventos,
        'camaras': camaras,
        'modelos': modelos,
        'estados': estados
    })



@login_required
def sistema_principal(request):
    camaras = Camara.objects.filter(estado__estado='Activado').exclude(id__isnull=True)[:4]
    return render(request, 'conteo_api/sistema_principal.html', {'camaras': camaras})



def api_camaras_activas(request):
    camaras = Camara.objects.filter(estado__estado__iexact='Activado')
    data = [
        {
            'id': cam.id,
            'nombre': cam.nombre,
            'stream_url': f"/stream-camara/{cam.id}/"
        }
        for cam in camaras
    ]
    return JsonResponse({'camaras': data})

def snapshot_camara(request, camara_id):
    cam = get_object_or_404(Camara, pk=camara_id)
    rtsp_url = generar_rtsp_url(cam)
    cap = cv2.VideoCapture(rtsp_url)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return HttpResponse(status=404)

    _, buffer = cv2.imencode('.jpg', frame)
    return HttpResponse(buffer.tobytes(), content_type='image/jpeg')

#pruebaaa
def prueba_rtsp_directa(request):
    rtsp_url = "rtsp://admin:Camara258@192.168.8.64:554/Streaming/Channels/101"

    def stream_generator():
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            print("[❌] No se pudo abrir el stream en Django.")
            return
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, jpeg = cv2.imencode('.jpg', frame)
            if jpeg is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        cap.release()

    return StreamingHttpResponse(
        stream_generator(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )