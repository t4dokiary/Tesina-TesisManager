import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from seguimiento.models import (
    PerfilUsuario, TelefonoUsuario, Alumno, Asesor, Coordinador, 
    ConfiguracionUsuario, ProyectoTesis
)

CLAVE_GENERAL = 'Password123'

# =============================================================================
# 1. CREAR 2 COORDINADORES
# =============================================================================
coordinadores_datos = [
    ('coordinador1@posgrado.buap.mx', 'Roberto', 'Posgrado', 'FCC', 'Cubículo 101', '2221234501'),
    ('coordinador2@posgrado.buap.mx', 'Guadalupe', 'Morales', 'Reyes', 'Cubículo 102', '2221234502'),
]

lista_coordinadores = []
for email, nom, pat, mat, cubiculo, tel in coordinadores_datos:
    u, _ = User.objects.get_or_create(username=email)
    u.email = email
    u.first_name = nom
    u.last_name = pat
    u.is_staff = True
    u.set_password(CLAVE_GENERAL)
    u.save()

    p, _ = PerfilUsuario.objects.get_or_create(user=u)
    p.primer_nombre = nom
    p.apellido_paterno = pat
    p.apellido_materno = mat
    p.tipo_usuario = 'COORDINADOR'
    p.cuenta_activa = True
    p.save()

    ConfiguracionUsuario.objects.get_or_create(perfil=p)
    TelefonoUsuario.objects.get_or_create(perfil=p, numero_telefono=tel)
    coord_obj, _ = Coordinador.objects.get_or_create(
        perfil=p,
        defaults={'cubiculo_oficina': cubiculo, 'telefono_oficina': tel}
    )
    lista_coordinadores.append(coord_obj)

coord_principal = lista_coordinadores[0]


# =============================================================================
# 2. CREAR 5 ASESORES
# =============================================================================
asesores_datos = [
    ('asesor1@posgrado.buap.mx', 'Juan Manuel', 'González', 'Calleros', 'Dr.', 'EMP-1001', '2222001001'),
    ('asesor2@posgrado.buap.mx', 'Carmen', 'Maldonado', 'Pérez', 'Dra.', 'EMP-1002', '2222001002'),
    ('asesor3@posgrado.buap.mx', 'Marco Antonio', 'Sánchez', 'Ramírez', 'Dr.', 'EMP-1003', '2222001003'),
    ('asesor4@posgrado.buap.mx', 'Beatriz', 'López', 'Domínguez', 'Dra.', 'EMP-1004', '2222001004'),
    ('asesor5@posgrado.buap.mx', 'Alejandro', 'Hernández', 'Vargas', 'Dr.', 'EMP-1005', '2222001005'),
]

lista_asesores = []
for email, nom, pat, mat, grado, emp, tel in asesores_datos:
    u, _ = User.objects.get_or_create(username=email)
    u.email = email
    u.first_name = nom
    u.last_name = pat
    u.set_password(CLAVE_GENERAL)
    u.save()

    p, _ = PerfilUsuario.objects.get_or_create(user=u)
    p.primer_nombre = nom
    p.apellido_paterno = pat
    p.apellido_materno = mat
    p.tipo_usuario = 'ASESOR'
    p.cuenta_activa = True
    p.save()

    ConfiguracionUsuario.objects.get_or_create(perfil=p)
    TelefonoUsuario.objects.get_or_create(perfil=p, numero_telefono=tel)
    asesor_obj, _ = Asesor.objects.get_or_create(
        perfil=p,
        defaults={'numero_empleado': emp, 'grado_academico': grado}
    )
    lista_asesores.append(asesor_obj)


# =============================================================================
# 3. CREAR 45 ALUMNOS Y SUS PROYECTOS (9 ALUMNOS POR CADA ASESOR)
# =============================================================================
nombres = [
    "Carlos", "Ana", "Miguel", "Fernanda", "Jorge", "Lucía", "Ricardo", "Elena", "Héctor",
    "Patricia", "Daniel", "Rosa", "Gabriel", "Adriana", "Esteban", "Valeria", "Ignacio", "Gabriela",
    "Javier", "Mariana", "Óscar", "Claudia", "Samuel", "Lorena", "Rodrigo", "Paola", "Eduardo",
    "Silvia", "Ángel", "Teresa", "Manuel", "Mónica", "Raúl", "Karla", "Pablo", "Irma",
    "Víctor", "Natalia", "César", "Alicia", "Mauricio", "Gloria", "Hugo", "Verónica", "Alonso"
]

apellidos_paternos = [
    "García", "Martínez", "López", "González", "Pérez", "Rodríguez", "Sánchez", "Ramírez", "Cruz",
    "Flores", "Gómez", "Morales", "Vázquez", "Jiménez", "Reyes", "Díaz", "Torres", "Gutiérrez",
    "Ruiz", "Mendoza", "Aguilar", "Ortiz", "Moreno", "Castillo", "Romero", "Álvarez", "Méndez",
    "Chávez", "Rivera", "Juárez", "Domínguez", "Herrera", "Medina", "Castro", "Vargas", "Guzmán",
    "Velázquez", "Ramos", "Contreras", "Salazar", "Silva", "Delgado", "Guerrero", "Paredes", "Vega"
]

temas_tesis = [
    "Sistema Web de Visión por Computadora para Clasificación de Imágenes",
    "Procesamiento de Lenguaje Natural para Detección de Temas Médicos",
    "Optimización de Índices en Motores de Bases de Datos NoSQL",
    "Plataforma de Monitoreo IoT para Microclimas Locales",
    "Detección de Intrusos en Redes Basado en Aprendizaje Profundo",
    "Diseño de Interfaces Accesibles para Personas con Discapacidad Visual",
    "Algoritmos Heurísticos para Planificación de Rutas Urbanas",
    "Predicción de Rendimiento Escolar mediante Modelos Estadísticos",
    "Arquitectura Segura para Microservicios en Ambientes Distribuidos"
]

lineas = [
    "Ingeniería de Software y Sistemas Distribuidos",
    "Inteligencia Artificial y Ciencia de Datos",
    "Ciberseguridad y Redes",
    "Sistemas Embebidos e Internet de las Cosas",
    "Interacción Humano-Computadora"
]

# Días de atraso simulados: los primeros están al corriente y los últimos generan alerta (>30 días)
patron_dias_inactividad = [2, 5, 8, 14, 21, 28, 35, 42, 60]

print("Registrando 45 alumnos, 5 asesores y 2 coordinadores...")

contador_alumnos = 0
for idx_asesor, asesor_actual in enumerate(lista_asesores):
    for j in range(9):
        indice_global = (idx_asesor * 9) + j
        
        email = f"alumno{indice_global + 1}@alumno.buap.mx"
        nom = nombres[indice_global]
        pat = apellidos_paternos[indice_global]
        mat = apellidos_paternos[(indice_global + 5) % 45]
        matricula = f"2020{10000 + indice_global}"
        tel = f"2228{100000 + indice_global}"
        
        # 1. Usuario Django
        u, _ = User.objects.get_or_create(username=email)
        u.email = email
        u.first_name = nom
        u.last_name = pat
        u.set_password(CLAVE_GENERAL)
        u.save()

        # 2. Perfil
        p, _ = PerfilUsuario.objects.get_or_create(user=u)
        p.primer_nombre = nom
        p.apellido_paterno = pat
        p.apellido_materno = mat
        p.tipo_usuario = 'ALUMNO'
        p.cuenta_activa = True
        p.save()

        ConfiguracionUsuario.objects.get_or_create(perfil=p)
        TelefonoUsuario.objects.get_or_create(perfil=p, numero_telefono=tel)

        # 3. Alumno
        alu, _ = Alumno.objects.get_or_create(perfil=p, defaults={'matricula': matricula})

        # 4. Proyecto Tesis
        dias_atraso = patron_dias_inactividad[j]
        fecha_avance = date.today() - timedelta(days=dias_atraso)
        titulo = f"{temas_tesis[j]} (Grupo {idx_asesor + 1})"
        linea = lineas[j % len(lineas)]

        ProyectoTesis.objects.get_or_create(
            alumno=alu,
            defaults={
                'asesor': asesor_actual,
                'coordinador': coord_principal,
                'titulo_tesis': titulo,
                'linea_investigacion': linea,
                'fecha_ultimo_avance': fecha_avance,
                'estado_proyecto': 'En desarrollo'
            }
        )
        contador_alumnos += 1

print(f"\nProceso finalizado exitosamente:")
print(f"- 2 Coordinadores registrados.")
print(f"- 5 Asesores registrados.")
print(f"- {contador_alumnos} Alumnos registrados con sus proyectos asignados.")
print(f"- Contraseña común para todas las cuentas de prueba: {CLAVE_GENERAL}")