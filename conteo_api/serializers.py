from rest_framework import serializers
from .models import Estado, Camara, Poligono, Coordenada, ConteoPersonas

class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = '__all__'

class CamaraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camara
        fields = '__all__'

class PoligonoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poligono
        fields = '__all__'

class CoordenadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coordenada
        fields = '__all__'

class ConteoPersonasSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConteoPersonas
        fields = '__all__'
