"""
URL configuration for backend_conteo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.documentation import include_docs_urls
from django.shortcuts import redirect
from conteo_api.views import dashboard
from django.conf import settings
from django.conf.urls.static import static

#urlpatterns = [
#    path('admin/', admin.site.urls),
#    path('', include('conteo_api.urls')),  # No uses 'api/' aquí si tienes vistas HTML
#    path('docs/', include_docs_urls(title='API Documentation')),
#]

# Redirige "/" al login si no ha iniciado sesión
def home_redirect(request):
    return redirect('login')  # o usa 'dashboard' si el login redirige

urlpatterns = [
    path('', home_redirect, name='home'),
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard, name='dashboard'),  # acceso directo
    path('conteo/', include('conteo_api.urls')),
    path('', include('conteo_api.urls')), 
    path('login/', auth_views.LoginView.as_view(template_name='conteo_api/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('docs/', include_docs_urls(title='API Documentation')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
