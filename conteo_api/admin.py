from django.contrib import admin
from .models import Estado, Camara, Poligono, Coordenada, ConteoPersonas

admin.site.register(Estado)
admin.site.register(Camara)
admin.site.register(Poligono)
admin.site.register(Coordenada)
admin.site.register(ConteoPersonas)
