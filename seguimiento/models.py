import os
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver


def validar_solo_pdf(archivo):
    """Regla obligatoria CU02: Solo archivos PDF."""
    extension = os.path.splitext(archivo.name)[1].lower()
    if extension != '.pdf':
        raise ValidationError('Solo se permiten archivos en formato PDF.')


class PerfilUsuario(models.Model):
    ROLES = [
        ('ALUMNO', 'Alumno'),
        ('ASESOR', 'Asesor'),
        ('COORDINADOR', 'Coordinador'),
    ]
    id_usuario = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    primer_nombre = models.CharField(max_length=50)
    segundo_nombre = models.CharField(max_length=50, blank=True, null=True)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    tipo_usuario = models.CharField(max_length=20, choices=ROLES)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    cuenta_activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return f"{self.primer_nombre} {self.apellido_paterno} ({self.tipo_usuario})"


# Tabla separada de configuración para trabajos futuros
class ConfiguracionUsuario(models.Model):
    id_configuracion = models.AutoField(primary_key=True)
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='configuracion')
    notif_inicio_sesion = models.BooleanField(default=True, verbose_name="Avisar al iniciar sesión")
    notif_comentarios = models.BooleanField(default=True, verbose_name="Avisar avances o comentarios")
    notif_minutas = models.BooleanField(default=True, verbose_name="Avisar registro de minutas")

    class Meta:
        db_table = 'configuracion_usuario'

    def __str__(self):
        return f"Configuración de {self.perfil.primer_nombre}"


@receiver(post_save, sender=PerfilUsuario)
def crear_configuracion_automatica(sender, instance, created, **kwargs):
    if created:
        ConfiguracionUsuario.objects.create(perfil=instance)


class TelefonoUsuario(models.Model):
    id_telefono = models.AutoField(primary_key=True)
    perfil = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, related_name='telefonos')
    numero_telefono = models.CharField(max_length=20)

    class Meta:
        db_table = 'telefono_usuario'

    def __str__(self):
        return self.numero_telefono


class Alumno(models.Model):
    id_alumno = models.AutoField(primary_key=True)
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='datos_alumno')
    matricula = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = 'alumno'

    def __str__(self):
        return f"{self.perfil.primer_nombre} {self.perfil.apellido_paterno} - {self.matricula}"


class Asesor(models.Model):
    id_asesor = models.AutoField(primary_key=True)
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='datos_asesor')
    numero_empleado = models.CharField(max_length=20, unique=True)
    grado_academico = models.CharField(max_length=50)

    class Meta:
        db_table = 'asesor'

    def __str__(self):
        return f"{self.grado_academico} {self.perfil.primer_nombre} {self.perfil.apellido_paterno}"


class Coordinador(models.Model):
    id_coordinador = models.AutoField(primary_key=True)
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='datos_coordinador')
    cubiculo_oficina = models.CharField(max_length=50)
    telefono_oficina = models.CharField(max_length=20)

    class Meta:
        db_table = 'coordinador'

    def __str__(self):
        return f"Coordinador: {self.perfil.primer_nombre} {self.perfil.apellido_paterno}"


class ProyectoTesis(models.Model):
    id_proyecto = models.AutoField(primary_key=True)
    alumno = models.OneToOneField(Alumno, on_delete=models.CASCADE, related_name='proyecto_activo')
    asesor = models.ForeignKey(Asesor, on_delete=models.CASCADE, related_name='proyectos_dirigidos')
    coordinador = models.ForeignKey(Coordinador, on_delete=models.SET_NULL, null=True, blank=True, related_name='proyectos_supervisados')
    
    titulo_tesis = models.CharField(max_length=255)
    linea_investigacion = models.CharField(max_length=255)
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_ultimo_avance = models.DateField(default=date.today)
    estado_proyecto = models.CharField(max_length=50, default='En desarrollo')

    class Meta:
        db_table = 'proyecto_tesis'

    @property
    def dias_inactividad(self):
        return (date.today() - self.fecha_ultimo_avance).days

    @property
    def tiene_alerta_rezago(self):
        return self.dias_inactividad > 30

    def __str__(self):
        return self.titulo_tesis


def ruta_pdf_tesis(instance, filename):
    return f"tesis/proyecto_{instance.proyecto_id}/v{instance.numero_version}_{filename}"


class EntregableVersion(models.Model):
    id_entregable = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(ProyectoTesis, on_delete=models.CASCADE, related_name='entregables')
    numero_version = models.PositiveIntegerField(default=1, editable=False)
    ruta_archivo_pdf = models.FileField(upload_to=ruta_pdf_tesis, validators=[validar_solo_pdf])
    fecha_hora_subida = models.DateTimeField(auto_now_add=True)
    comentario_alumno = models.TextField(blank=True, null=True)
    retroalimentacion_asesor = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'entregable_version'
        ordering = ['-numero_version']

    def save(self, *args, **kwargs):
        if not self.pk:
            ultimo = EntregableVersion.objects.filter(proyecto=self.proyecto).order_by('-numero_version').first()
            self.numero_version = (ultimo.numero_version + 1) if ultimo else 1
            self.proyecto.fecha_ultimo_avance = date.today()
            self.proyecto.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Regla: No está permitido borrar versiones anteriores.")

    def __str__(self):
        return f"{self.proyecto.titulo_tesis} - Versión {self.numero_version}"


class MinutaAsesoria(models.Model):
    MODALIDADES = [
        ('PRESENCIAL', 'Presencial'),
        ('VIRTUAL', 'Virtual'),
    ]
    id_minuta = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(ProyectoTesis, on_delete=models.CASCADE, related_name='minutas')
    fecha_reunion = models.DateField()
    modalidad = models.CharField(max_length=20, choices=MODALIDADES)
    resumen_temas = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'minutas_asesoria'

    def save(self, *args, **kwargs):
        self.proyecto.fecha_ultimo_avance = date.today()
        self.proyecto.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Minuta {self.fecha_reunion} - {self.proyecto.titulo_tesis}"


class CompromisoAcuerdo(models.Model):
    RESPONSABLES = [
        ('ALUMNO', 'Alumno'),
        ('ASESOR', 'Asesor'),
    ]
    id_acuerdo = models.AutoField(primary_key=True)
    minuta = models.ForeignKey(MinutaAsesoria, on_delete=models.CASCADE, related_name='acuerdos')
    numero_acuerdo = models.PositiveIntegerField()
    descripcion_tarea = models.TextField()
    responsable = models.CharField(max_length=10, choices=RESPONSABLES)
    fecha_limite = models.DateField()
    estado_cumplido = models.BooleanField(default=False)

    class Meta:
        db_table = 'compromiso_acuerdo'

    def __str__(self):
        return f"Acuerdo {self.numero_acuerdo} ({self.responsable})"


class AlertaRezago(models.Model):
    id_alerta = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(ProyectoTesis, on_delete=models.CASCADE, related_name='alertas')
    fecha_deteccion = models.DateField(auto_now_add=True)
    dias_acumulados = models.PositiveIntegerField()
    estado_alerta = models.CharField(max_length=50, default='Pendiente')

    class Meta:
        db_table = 'alerta_rezago'

    def __str__(self):
        return f"Alerta {self.proyecto.titulo_tesis} ({self.dias_acumulados} días)"