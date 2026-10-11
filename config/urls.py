"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from seguimiento import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Raíz principal (página de bienvenida)
    path('', views.index_view, name='inicio'),
    
    # CU01: Autenticación y Cierre de Sesión
    path('login/', views.login_web_view, name='login_web'),
    path('logout/', views.logout_view, name='logout'),
    path('api/login/', views.LoginAPIView.as_view(), name='login_token'),
    
    # Registros de usuarios
    path('alumno/', views.registrar_alumno_view, name='registro_alumno'),
    path('maestro/', views.registrar_maestro_view, name='registro_maestro'),
    
    # Preferencias de Correo y Restablecimiento de Contraseña
    path('preferencias/', views.preferencias_view, name='preferencias'),
    path('recuperar/', views.solicitar_recuperacion_view, name='recuperar'),
    path('restablecer/<uidb64>/<token>/', views.cambiar_password_token_view, name='restablecer'),
    
    # CU02: Entregables PDF
    path('alumno/panel/', views.panel_alumno_view, name='panel_alumno'),
    path('asesor/revision/<int:proyecto_id>/', views.revision_borradores_view, name='revision_borradores'),
    
    # CU03: Minutas de Asesoría
    path('asesor/panel/', views.panel_asesor_view, name='panel_asesor'),
    path('asesor/minuta/<int:proyecto_id>/', views.crear_minuta_view, name='crear_minuta'),
    
    # CU04: Alertas de Inactividad (>30 días)
    path('coordinacion/panel/', views.panel_coordinacion_view, name='panel_coordinacion'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)