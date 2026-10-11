from functools import wraps
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.forms import SetPasswordForm

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import (
    PerfilUsuario, TelefonoUsuario, Alumno, Asesor, Coordinador,
    ProyectoTesis, EntregableVersion, MinutaAsesoria, CompromisoAcuerdo,
    AlertaRezago, ConfiguracionUsuario
)


# -------------------------------------------------------------
# CANDADOS DE SEGURIDAD (ANTI-ELEVACIÓN DE PERMISOS)
# -------------------------------------------------------------
def rol_requerido(rol_esperado):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login_web')
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == rol_esperado:
                if not request.user.perfil.cuenta_activa:
                    raise PermissionDenied
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator


def enviar_correo_si_activo(usuario, tipo, asunto, mensaje):
    """Envía correo respetando la tabla de configuración del usuario."""
    if not hasattr(usuario, 'perfil') or not usuario.email:
        return
    config, _ = ConfiguracionUsuario.objects.get_or_create(perfil=usuario.perfil)
    
    enviar = False
    if tipo == 'login' and config.notif_inicio_sesion:
        enviar = True
    elif tipo == 'comentario' and config.notif_comentarios:
        enviar = True
    elif tipo == 'minuta' and config.notif_minutas:
        enviar = True

    if enviar:
        send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [usuario.email], fail_silently=True)


# -------------------------------------------------------------
# RAÍZ Y AUTENTICACIÓN (CU01)
# -------------------------------------------------------------
def index_view(request):
    """Página de bienvenida explicativa en la raíz."""
    if request.user.is_authenticated:
        if request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'COORDINADOR'):
            return redirect('panel_coordinacion')
        elif hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'ASESOR':
            return redirect('panel_asesor')
        elif hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'ALUMNO':
            return redirect('panel_alumno')
    return render(request, 'seguimiento/bienvenida.html')


def login_web_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        usuario = request.POST.get('username')
        clave = request.POST.get('password')
        user = authenticate(request, username=usuario, password=clave)

        if not user:
            return render(request, 'seguimiento/login.html', {'error': 'Usuario o contraseña incorrectos.'})

        if hasattr(user, 'perfil') and not user.perfil.cuenta_activa:
            return render(request, 'seguimiento/login.html', {'error': 'Tu cuenta está inactiva. Acude con coordinación.'})

        login(request, user)
        Token.objects.get_or_create(user=user)

        enviar_correo_si_activo(
            user, 'login',
            'Nuevo inicio de sesión',
            f'Hola {user.first_name}, se inició sesión en tu cuenta.'
        )
        return redirect('inicio')

    return render(request, 'seguimiento/login.html')


def logout_view(request):
    logout(request)
    return redirect('inicio')


class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Credenciales inválidas.'}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(user, 'perfil') and not user.perfil.cuenta_activa:
            return Response({'error': 'Cuenta inactiva.'}, status=status.HTTP_403_FORBIDDEN)
        token, _ = Token.objects.get_or_create(user=user)
        rol = user.perfil.tipo_usuario if hasattr(user, 'perfil') else 'SUPERUSER'
        return Response({'token': token.key, 'user_id': user.id, 'rol': rol}, status=status.HTTP_200_OK)


# -------------------------------------------------------------
# PREFERENCIAS DE CORREO
# -------------------------------------------------------------
@login_required
def preferencias_view(request):
    perfil = request.user.perfil
    config, _ = ConfiguracionUsuario.objects.get_or_create(perfil=perfil)
    if request.method == 'POST':
        config.notif_inicio_sesion = 'notif_inicio_sesion' in request.POST
        config.notif_comentarios = 'notif_comentarios' in request.POST
        config.notif_minutas = 'notif_minutas' in request.POST
        config.save()
        return render(request, 'seguimiento/preferencias.html', {'config': config, 'mensaje': 'Preferencias guardadas.'})
    return render(request, 'seguimiento/preferencias.html', {'config': config})


# -------------------------------------------------------------
# RESTABLECER CONTRASEÑA (1 HORA + ROTACIÓN DE TOKEN)
# -------------------------------------------------------------
def solicitar_recuperacion_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        usuario = User.objects.filter(email=email).first()
        if usuario:
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)
            enlace = request.build_absolute_uri(f'/restablecer/{uid}/{token}/')
            send_mail(
                "Restablecer contraseña - Tesis",
                f"Hola {usuario.first_name}, entra aquí para cambiar tu contraseña (válido por 1 hora):\n{enlace}",
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=False
            )
        return render(request, 'seguimiento/recuperar_enviado.html')
    return render(request, 'seguimiento/recuperar_solicitud.html')


def cambiar_password_token_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        usuario = User.objects.get(pk=uid)
    except Exception:
        usuario = None

    if usuario is None or not default_token_generator.check_token(usuario, token):
        return render(request, 'seguimiento/recuperar_invalido.html')

    if request.method == 'POST':
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            Token.objects.filter(user=usuario).delete()
            Token.objects.create(user=usuario)
            return render(request, 'seguimiento/recuperar_exito.html')
    else:
        form = SetPasswordForm(usuario)

    return render(request, 'seguimiento/recuperar_formulario.html', {'form': form})


# -------------------------------------------------------------
# REGISTROS
# -------------------------------------------------------------
def registrar_alumno_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        p_nom = request.POST.get('primer_nombre')
        s_nom = request.POST.get('segundo_nombre', '')
        paterno = request.POST.get('apellido_paterno')
        materno = request.POST.get('apellido_materno')
        matricula = request.POST.get('matricula')
        tel = request.POST.get('telefono')

        if User.objects.filter(username=email).exists():
            return render(request, 'seguimiento/registrar_alumno.html', {'error': 'El correo ya está registrado.'})
        if Alumno.objects.filter(matricula=matricula).exists():
            return render(request, 'seguimiento/registrar_alumno.html', {'error': 'La matrícula ya existe.'})

        with transaction.atomic():
            user = User.objects.create_user(username=email, email=email, password=password, first_name=p_nom, last_name=paterno)
            perfil = PerfilUsuario.objects.create(
                user=user, primer_nombre=p_nom, segundo_nombre=s_nom,
                apellido_paterno=paterno, apellido_materno=materno,
                tipo_usuario='ALUMNO', cuenta_activa=True
            )
            if tel:
                TelefonoUsuario.objects.create(perfil=perfil, numero_telefono=tel)
            Alumno.objects.create(perfil=perfil, matricula=matricula)

        return render(request, 'seguimiento/registrar_alumno.html', {'mensaje': 'Alumno registrado con éxito. Ya puedes entrar.'})

    return render(request, 'seguimiento/registrar_alumno.html')


@login_required
@rol_requerido('COORDINADOR')
def registrar_maestro_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        p_nom = request.POST.get('primer_nombre')
        s_nom = request.POST.get('segundo_nombre', '')
        paterno = request.POST.get('apellido_paterno')
        materno = request.POST.get('apellido_materno')
        num_emp = request.POST.get('numero_empleado')
        grado = request.POST.get('grado_academico')
        tel = request.POST.get('telefono')

        if User.objects.filter(username=email).exists():
            return render(request, 'seguimiento/registrar_maestro.html', {'error': 'El correo ya existe.'})
        if Asesor.objects.filter(numero_empleado=num_emp).exists():
            return render(request, 'seguimiento/registrar_maestro.html', {'error': 'El número de empleado ya existe.'})

        with transaction.atomic():
            user = User.objects.create_user(username=email, email=email, password=password, first_name=p_nom, last_name=paterno)
            perfil = PerfilUsuario.objects.create(
                user=user, primer_nombre=p_nom, segundo_nombre=s_nom,
                apellido_paterno=paterno, apellido_materno=materno,
                tipo_usuario='ASESOR', cuenta_activa=True
            )
            if tel:
                TelefonoUsuario.objects.create(perfil=perfil, numero_telefono=tel)
            Asesor.objects.create(perfil=perfil, numero_empleado=num_emp, grado_academico=grado)

        return render(request, 'seguimiento/registrar_maestro.html', {'mensaje': 'Asesor registrado con éxito.'})

    return render(request, 'seguimiento/registrar_maestro.html')


# -------------------------------------------------------------
# CU02: PANEL ALUMNO
# -------------------------------------------------------------
@login_required
@rol_requerido('ALUMNO')
def panel_alumno_view(request):
    proyecto = ProyectoTesis.objects.filter(alumno__perfil__user=request.user).first()
    entregables = proyecto.entregables.all() if proyecto else []
    minutas = proyecto.minutas.prefetch_related('acuerdos').all() if proyecto else []

    if request.method == 'POST' and proyecto:
        archivo = request.FILES.get('archivo_pdf')
        comentario = request.POST.get('comentario_alumno')

        if not archivo or not archivo.name.lower().endswith('.pdf'):
            return render(request, 'seguimiento/panel_alumno.html', {
                'proyecto': proyecto, 'entregables': entregables, 'minutas': minutas,
                'error': 'Solo se permiten archivos en formato PDF.'
            })

        EntregableVersion.objects.create(proyecto=proyecto, ruta_archivo_pdf=archivo, comentario_alumno=comentario)
        
        enviar_correo_si_activo(
            proyecto.asesor.perfil.user, 'comentario',
            'Nuevo avance entregado',
            f'El alumno {request.user.first_name} ha subido un nuevo avance en PDF.'
        )
        return redirect('panel_alumno')

    return render(request, 'seguimiento/panel_alumno.html', {
        'proyecto': proyecto,
        'entregables': entregables,
        'minutas': minutas
    })


# -------------------------------------------------------------
# CU02 Y CU03: PANEL ASESOR
# -------------------------------------------------------------
@login_required
@rol_requerido('ASESOR')
def panel_asesor_view(request):
    proyectos = ProyectoTesis.objects.filter(asesor__perfil__user=request.user)
    return render(request, 'seguimiento/panel_asesor.html', {'proyectos': proyectos})


@login_required
@rol_requerido('ASESOR')
def revision_borradores_view(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoTesis, id_proyecto=proyecto_id, asesor__perfil__user=request.user)
    
    if request.method == 'POST':
        entregable_id = request.POST.get('entregable_id')
        feedback = request.POST.get('retroalimentacion')
        entregable = get_object_or_404(EntregableVersion, id_entregable=entregable_id, proyecto=proyecto)
        entregable.retroalimentacion_asesor = feedback
        entregable.save()

        enviar_correo_si_activo(
            proyecto.alumno.perfil.user, 'comentario',
            'Comentarios en tu avance',
            f'Tu asesor ha retroalimentado la versión {entregable.numero_version}.'
        )
        return redirect('revision_borradores', proyecto_id=proyecto.id_proyecto)

    entregables = proyecto.entregables.all()
    return render(request, 'seguimiento/revision_borradores.html', {'proyecto': proyecto, 'entregables': entregables})


@login_required
@rol_requerido('ASESOR')
def crear_minuta_view(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoTesis, id_proyecto=proyecto_id, asesor__perfil__user=request.user)

    if request.method == 'POST':
        fecha = request.POST.get('fecha_reunion')
        modalidad = request.POST.get('modalidad')
        resumen = request.POST.get('resumen_temas')
        desc_tarea = request.POST.get('descripcion_tarea')
        responsable = request.POST.get('responsable')
        fecha_limite = request.POST.get('fecha_limite')

        if not fecha or not resumen or not desc_tarea or not fecha_limite:
            return render(request, 'seguimiento/crear_minuta.html', {
                'proyecto': proyecto,
                'error': 'Fecha, resumen y al menos un acuerdo son obligatorios.'
            })

        with transaction.atomic():
            minuta = MinutaAsesoria.objects.create(
                proyecto=proyecto,
                fecha_reunion=fecha,
                modalidad=modalidad,
                resumen_temas=resumen
            )
            CompromisoAcuerdo.objects.create(
                minuta=minuta,
                numero_acuerdo=1,
                descripcion_tarea=desc_tarea,
                responsable=responsable,
                fecha_limite=fecha_limite
            )

        enviar_correo_si_activo(
            proyecto.alumno.perfil.user, 'minuta',
            'Nueva minuta de asesoría',
            f'Se registraron acuerdos para tu proyecto con fecha {fecha}.'
        )
        return redirect('panel_asesor')

    return render(request, 'seguimiento/crear_minuta.html', {'proyecto': proyecto})


# -------------------------------------------------------------
# CU04: PANEL COORDINACIÓN
# -------------------------------------------------------------
@login_required
@rol_requerido('COORDINADOR')
def panel_coordinacion_view(request):
    proyectos = ProyectoTesis.objects.select_related('alumno__perfil', 'asesor__perfil').all()
    
    for p in proyectos:
        if p.tiene_alerta_rezago:
            AlertaRezago.objects.get_or_create(
                proyecto=p,
                dias_acumulados=p.dias_inactividad,
                estado_alerta='Activa'
            )

    return render(request, 'seguimiento/panel_coordinacion.html', {'proyectos': proyectos})