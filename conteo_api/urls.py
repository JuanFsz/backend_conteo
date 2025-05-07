from django.contrib import admin
from django.urls import path, include
from conteo_api.views import *
from rest_framework.routers import DefaultRouter
from . import views 
from django.contrib.auth import views as auth_views
from .views import stream_camara
# Import the viewsets for the models
router = DefaultRouter()
router.register(r'estados', EstadoViewSet)
router.register(r'camaras', CamaraViewSet)
router.register(r'poligonos', PoligonoViewSet)
router.register(r'coordenadas', CoordenadaViewSet)
router.register(r'conteos', ConteoPersonasViewSet)

# This code snippet is defining the URL patterns for the Django application. Here's what it's doing:

# Rutas del proyecto
urlpatterns = [
    path('', include(router.urls)), 
    
    # Vistas HTML
    path('camaras-web/', views.lista_camaras, name='lista_camaras'),
    path('conteos-web/', views.lista_conteos, name='lista_conteos'),
    path('dashboard/', dashboard, name='dashboard'),

    path('login/', auth_views.LoginView.as_view(template_name='conteo_api/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    # configuracion de camara
    path('configurar-camara/', views.configurar_camara, name='configurar_camara'),
    path('editar-camara/<int:pk>/', views.editar_camara, name='editar_camara'),
    path('eliminar-camara/<int:pk>/', views.eliminar_camara, name='eliminar_camara'),
    # configuracion de poligono
    path('roi/snapshot/<int:camara_id>/', views.generar_snapshot, name='generar_snapshot'),
    path('crear-area-roi/', views.crear_area_roi, name='crear_area_roi'),
    path('guardar-roi/', views.guardar_roi, name='guardar_roi'),
    path('snapshot/<int:camara_id>/', views.generar_snapshot, name='generar_snapshot'),
    path('stream/camara/<int:camara_id>/', stream_camara, name='stream_camara'),
    path('roi/stream/<int:camara_id>/', views.stream_camara, name='roi_stream'),    # configuracion de coordenadas
    path('configurar-modelo/', views.configurar_modelo, name='configurar_modelo'),
    path('modelo/editar/<int:pk>/', views.editar_modelo, name='editar_modelo'),
    path('modelo/eliminar/<int:pk>/', views.eliminar_modelo, name='eliminar_modelo'),
    path('roi/guardar/<int:camara_id>/', guardar_roi, name='guardar_roi'),
    path('roi/poligonos/<int:camara_id>/', roi_poligonos, name='roi_poligonos'),

    # eventos
    path('configurar-evento/', views.configurar_evento, name='configurar_evento'),
    # sistema principal
    path('sistema-principal/', views.sistema_principal, name='sistema_principal'),
    path('stream-camara/<int:camara_id>/', views.stream_camara, name='stream_camara'),
    path('stream/<int:camara_id>/', views.stream_camara, name='stream_camara'),


    # iniciar 
    path('api/camaras-activas/', views.api_camaras_activas, name='api_camaras_activas'),
    path('snapshot/<int:camara_id>/', views.snapshot_camara, name='snapshot_camara'),

    path('prueba-stream/', views.prueba_rtsp_directa, name='prueba_rtsp_directa'),










  
]