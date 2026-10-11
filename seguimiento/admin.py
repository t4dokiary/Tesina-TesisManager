from django.contrib import admin
from .models import (
    PerfilUsuario, TelefonoUsuario, Alumno, Asesor, 
    Coordinador, ProyectoTesis, EntregableVersion, 
    MinutaAsesoria, CompromisoAcuerdo, AlertaRezago
)

class TelefonoInline(admin.TabularInline):
    model = TelefonoUsuario
    extra = 1

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'primer_nombre', 'apellido_paterno', 'tipo_usuario', 'cuenta_activa')
    list_filter = ('tipo_usuario', 'cuenta_activa')
    inlines = [TelefonoInline]

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'matricula')

@admin.register(Asesor)
class AsesorAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'numero_empleado', 'grado_academico')

@admin.register(Coordinador)
class CoordinadorAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'cubiculo_oficina', 'telefono_oficina')

@admin.register(ProyectoTesis)
class ProyectoTesisAdmin(admin.ModelAdmin):
    list_display = ('titulo_tesis', 'alumno', 'asesor', 'fecha_ultimo_avance', 'dias_inactividad', 'tiene_alerta_rezago')
    list_filter = ('estado_proyecto',)

@admin.register(EntregableVersion)
class EntregableVersionAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'numero_version', 'fecha_hora_subida')
    readonly_fields = ('numero_version', 'fecha_hora_subida')

class CompromisoInline(admin.TabularInline):
    model = CompromisoAcuerdo
    extra = 1

@admin.register(MinutaAsesoria)
class MinutaAsesoriaAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'fecha_reunion', 'modalidad')
    inlines = [CompromisoInline]

@admin.register(AlertaRezago)
class AlertaRezagoAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'fecha_deteccion', 'dias_acumulados', 'estado_alerta')