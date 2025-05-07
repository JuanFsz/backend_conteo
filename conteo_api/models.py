from django.db import models

# Estado
class Estado(models.Model):
    estado = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.estado

# Cámara
class Camara(models.Model):
    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=50, default='Genérica')
    protocolo = models.CharField(max_length=10, default='rtsp')  # rtsp o rtmps
    usuario = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    direccion_ip = models.CharField(max_length=50)
    puerto = models.IntegerField(default=554)  # Puerto por defecto para RTSP
    streaming_path = models.CharField(max_length=150)
    estado = models.ForeignKey(Estado, on_delete=models.RESTRICT)
    def __str__(self):
        return f"{self.nombre} ({self.direccion_ip})"

    def url_rtsp(self):
        return f"{self.protocolo}://{self.usuario}:{self.password}@{self.direccion_ip}:{self.puerto}{self.streaming_path}"

# Polígono
class Poligono(models.Model):
    nombre_poligono = models.CharField(max_length=100, unique=True)
    area_interes = models.CharField(max_length=50)
    camara = models.ForeignKey(Camara, on_delete=models.CASCADE)
    estado = models.ForeignKey(Estado, on_delete=models.RESTRICT)

    def __str__(self):
        return self.nombre_poligono

# Coordenadas de un polígono
class Coordenada(models.Model):
    poligono = models.ForeignKey(Poligono, on_delete=models.CASCADE, related_name='coordenadas')
    x = models.IntegerField()
    y = models.IntegerField()

    def __str__(self):
        return f"({self.x}, {self.y})"

# Conteo de personas
class ConteoPersonas(models.Model):
    fecha = models.DateField()
    hora = models.TimeField()
    contador_ingreso = models.IntegerField(default=0)
    contador_salida = models.IntegerField(default=0)
    camara = models.ForeignKey(Camara, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.fecha} {self.hora} - Ingresos: {self.contador_ingreso}, Salidas: {self.contador_salida}"

# Configuración del modelo
class ModeloConfig(models.Model):
    YOLO_MODELOS = [
        ('yolo11n.pt', 'YOLOv11 Nano'),
        ('yolo11s.pt', 'YOLOv11 Small'),
        ('yolo11m.pt', 'YOLOv11 Medium'),
        ('yolo11l.pt', 'YOLOv11 Large'),
        ('yolo11x.pt', 'YOLOv11 XLarge'),
    ]

    nombre_modelo = models.CharField(max_length=100)
    modelo = models.CharField(max_length=20, choices=YOLO_MODELOS, default='yolo11s.pt',
                              help_text="Modelo YOLOv11 a utilizar para detección")
    
    image_size = models.IntegerField(default=640, help_text="Tamaño de entrada de la imagen (por ejemplo 640)")
    stride = models.IntegerField(default=1, help_text="Número de frames a saltar")
    device = models.CharField(max_length=20, choices=[('cpu', 'CPU'), ('cuda', 'CUDA')], default='cuda')
    confidence_threshold = models.FloatField(default=0.25, help_text="Umbral de confianza para la detección")
    iou = models.FloatField(default=0.7, help_text="IoU threshold para NMS")
    max_det = models.IntegerField(default=80, help_text="Máximo número de detecciones por imagen")
    
    classes = models.CharField(
        max_length=100,
        default='0',
        help_text="Clases a detectar según COCO.yaml. 0 para personas"
    )

    def __str__(self):
        return f"{self.nombre_modelo} ({self.modelo})"

# Configuración de tracking asociada al modelo
class TrackingConfig(models.Model):
    distance_threshold = models.FloatField(default=35.0, help_text="Distancia máxima para asociar detecciones")
    dwell_time_threshold = models.FloatField(default=5.0, help_text="Tiempo mínimo de permanencia (segundos)")
    modelo = models.ForeignKey(ModeloConfig, on_delete=models.CASCADE)

    def __str__(self):
        return f"Tracking - Modelo: {self.modelo.nombre_modelo}"


# Configuración por horario de conteo
class ConteoConfig(models.Model):
    desde_hora = models.TimeField()
    hasta_hora = models.TimeField()
    estado = models.ForeignKey(Estado, on_delete=models.RESTRICT)
    camara = models.ForeignKey(Camara, on_delete=models.CASCADE)
    modelo = models.ForeignKey(ModeloConfig, on_delete=models.CASCADE)

    def __str__(self):
        return f"Config {self.camara} [{self.desde_hora} - {self.hasta_hora}]"
