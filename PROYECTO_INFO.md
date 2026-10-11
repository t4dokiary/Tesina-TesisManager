# Información del proyecto

## 1. Objetivo del proyecto

Este proyecto es una aplicación web para dar seguimiento al avance de trabajos de tesis o tesinas de posgrado. Su propósito es centralizar la relación entre alumnos, asesores y coordinación académica, evitando que los avances, comentarios y acuerdos de asesoría queden dispersos en correos o archivos independientes.

El sistema permite:

- Registrar alumnos y asesores.
- Asociar cada alumno con un proyecto de tesis y un asesor.
- Subir avances de tesis en PDF conservando un historial de versiones.
- Permitir que el asesor revise cada versión y escriba retroalimentación.
- Registrar minutas de reuniones de asesoría y sus compromisos.
- Detectar proyectos sin avances durante más de 30 días.
- Avisar por correo sobre inicios de sesión, comentarios y nuevas minutas, de acuerdo con las preferencias de cada usuario.

Los usuarios se dividen en tres roles:

- **Alumno:** consulta su proyecto, sube avances y revisa las minutas y comentarios.
- **Asesor:** consulta los proyectos que dirige, revisa entregables y registra minutas.
- **Coordinador:** administra asesores y observa el estado general de los proyectos, incluyendo las alertas de rezago.

## 2. Tecnologías utilizadas

- **Lenguaje:** Python.
- **Framework web:** Django 6.1.1.
- **API:** Django REST Framework 3.18.3.
- **Autenticación web:** sistema de usuarios, sesiones y contraseñas de Django.
- **Autenticación de API:** tokens de `rest_framework.authtoken`.
- **Base de datos:** MySQL, configurada para conectarse a `127.0.0.1:3306`, con la base `tesina_db`.
- **Conector de MySQL:** `mysqlclient` 2.3.0.
- **Plantillas:** Django Templates (`.html`), ubicadas dentro de la aplicación `seguimiento`.
- **Archivos multimedia:** PDFs guardados debajo de `media/tesis/`.
- **Correo:** backend de consola de Django. En el estado actual los mensajes se imprimen en la consola en lugar de enviarse mediante un servidor SMTP real.
- **Servidor de desarrollo:** se inicia con `manage.py`, como en cualquier proyecto Django.

La configuración usa idioma `es-mx`, zona horaria `America/Mexico_City` y archivos de medios habilitados en modo `DEBUG`.

## 3. Estructura de carpetas y archivos

### Raíz

- [`manage.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/manage.py): punto de entrada para comandos de Django, como `runserver`, `migrate`, `createsuperuser` y `check`.
- [`pruebas.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/pruebas.py): script de carga de datos de demostración. Crea coordinadores, asesores, alumnos y proyectos de tesis de ejemplo.
- [`main.md`](C:/Users/luism/OneDrive/Escritorio/pruebas/main.md): contiene credenciales de ejemplo para algunos usuarios de prueba.
- [`media/`](C:/Users/luism/OneDrive/Escritorio/pruebas/media/): almacena archivos subidos por los usuarios. Actualmente contiene PDFs de una tesis de ejemplo. Está excluida del control de versiones por `.gitignore`.
- [`venv/`](C:/Users/luism/OneDrive/Escritorio/pruebas/venv/): entorno virtual local con Django, Django REST Framework y el conector de MySQL.

### Configuración del proyecto

- [`config/settings.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/config/settings.py): define aplicaciones instaladas, middleware, conexión a MySQL, idioma, zona horaria, archivos multimedia, autenticación y correo.
- [`config/urls.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/config/urls.py): concentra las rutas web y de la API. También sirve archivos de `media/` cuando `DEBUG` está activo.
- [`config/asgi.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/config/asgi.py): entrada ASGI para servidores compatibles con aplicaciones asíncronas.
- [`config/wsgi.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/config/wsgi.py): entrada WSGI para despliegues tradicionales.

### Aplicación `seguimiento`

- [`seguimiento/models.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/seguimiento/models.py): define las entidades de usuarios, proyectos, entregables, minutas, acuerdos y alertas.
- [`seguimiento/views.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/seguimiento/views.py): contiene la lógica de las páginas web y del endpoint de inicio de sesión por API.
- [`seguimiento/admin.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/seguimiento/admin.py): registra los modelos en el panel administrativo y configura listados e inlines.
- [`seguimiento/apps.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/seguimiento/apps.py): configura la aplicación Django.
- [`seguimiento/migrations/0001_initial.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/seguimiento/migrations/0001_initial.py): crea las tablas iniciales.
- [`seguimiento/migrations/0002_configuracionusuario.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/seguimiento/migrations/0002_configuracionusuario.py): agrega la tabla de preferencias de notificaciones.
- [`seguimiento/tests.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/seguimiento/tests.py): archivo destinado a pruebas automatizadas; actualmente solo contiene la plantilla inicial de Django.
- `seguimiento/templates/seguimiento/`: contiene las pantallas HTML para bienvenida, inicio de sesión, registro, paneles por rol, preferencias, recuperación de contraseña, revisión de borradores y creación de minutas.

## 4. Base de datos y modelos

Django usa el modelo integrado `auth.User` para las credenciales básicas. Cada usuario tiene un `PerfilUsuario` asociado mediante una relación uno a uno.

### Usuarios y roles

- **`PerfilUsuario` (`usuario`):** nombre, apellidos, rol (`ALUMNO`, `ASESOR` o `COORDINADOR`), fecha de registro y estado de la cuenta.
- **`ConfiguracionUsuario` (`configuracion_usuario`):** preferencias de avisos de inicio de sesión, comentarios y minutas. Se crea automáticamente al crear un perfil.
- **`TelefonoUsuario` (`telefono_usuario`):** teléfonos asociados a un perfil.
- **`Alumno` (`alumno`):** datos propios del alumno, principalmente su matrícula.
- **`Asesor` (`asesor`):** número de empleado y grado académico.
- **`Coordinador` (`coordinador`):** cubículo u oficina y teléfono de oficina.

`Alumno`, `Asesor` y `Coordinador` son extensiones separadas de `PerfilUsuario`. Un perfil puede tener solo uno de esos tipos según el valor de `tipo_usuario`.

### Seguimiento académico

- **`ProyectoTesis` (`proyecto_tesis`):** proyecto activo de un alumno, con título, línea de investigación, fecha de inicio, fecha del último avance y estado. Tiene un alumno, un asesor y opcionalmente un coordinador. La relación con el alumno es uno a uno; un asesor y un coordinador pueden estar vinculados con varios proyectos.
- **`EntregableVersion` (`entregable_version`):** versión de un PDF entregado para un proyecto. Guarda archivo, número de versión, fecha de subida, comentario del alumno y retroalimentación del asesor. El número de versión se incrementa automáticamente y las versiones no pueden eliminarse desde el modelo.
- **`MinutaAsesoria` (`minutas_asesoria`):** reunión de asesoría con fecha, modalidad (`PRESENCIAL` o `VIRTUAL`), resumen y fecha de registro.
- **`CompromisoAcuerdo` (`compromiso_acuerdo`):** tarea derivada de una minuta, con descripción, responsable, fecha límite y estado de cumplimiento.
- **`AlertaRezago` (`alerta_rezago`):** alerta asociada a un proyecto cuyo último avance tiene más de 30 días. Registra la fecha de detección, los días acumulados y el estado de la alerta.

Las eliminaciones en cascada hacen que, por ejemplo, los entregables y minutas se eliminen si se elimina su proyecto. Si se elimina un coordinador, el proyecto conserva su registro pero deja vacío ese vínculo (`SET_NULL`).

## 5. Flujos o funciones principales

### Entrada al sistema

1. La ruta raíz muestra la bienvenida si no hay sesión.
2. El usuario inicia sesión con usuario y contraseña desde `/login/`.
3. El sistema valida la cuenta y comprueba que esté activa.
4. Al iniciar sesión se crea o recupera un token de API y se redirige al panel correspondiente al rol.
5. El usuario puede cerrar sesión desde `/logout/`.

También existe `POST /api/login/`, que devuelve un token, el identificador del usuario y su rol para clientes que consuman la API.

### Registro y recuperación de acceso

- Un visitante puede registrar un alumno desde `/alumno/`, incluyendo datos personales, correo, contraseña, matrícula y teléfono.
- Un coordinador autenticado puede registrar asesores desde `/maestro/`.
- El sistema impide repetir correos, matrículas o números de empleado.
- Desde `/recuperar/` un usuario solicita un enlace de cambio de contraseña. El enlace usa el generador de tokens de Django y caduca en una hora.
- Al cambiar la contraseña se renueva el token de API anterior.

### Trabajo del alumno

1. El alumno entra a `/alumno/panel/`.
2. Consulta los datos de su proyecto, sus minutas y sus entregables anteriores.
3. Sube un nuevo avance y un comentario opcional.
4. Solo se aceptan archivos con extensión `.pdf`.
5. El sistema calcula la siguiente versión, guarda el archivo en `media/tesis/proyecto_<id>/` y actualiza la fecha del último avance.
6. El asesor recibe un aviso si tiene habilitada la notificación de comentarios.
7. El alumno puede leer la retroalimentación del asesor y los acuerdos de las minutas.

### Trabajo del asesor

1. El asesor entra a `/asesor/panel/` y ve únicamente los proyectos que dirige.
2. Selecciona un proyecto para acceder a `/asesor/revision/<id>/`.
3. Revisa las versiones PDF y escribe retroalimentación para cada entregable.
4. El alumno recibe un aviso cuando hay nuevos comentarios, si la preferencia está activa.
5. Desde `/asesor/minuta/<id>/` registra una reunión, su modalidad, un resumen y al menos un acuerdo.
6. La minuta crea un compromiso con responsable y fecha límite, actualiza la fecha del último avance y avisa al alumno.

### Trabajo del coordinador

1. El coordinador entra a `/coordinacion/panel/` y consulta todos los proyectos.
2. Puede registrar asesores desde el formulario de maestros.
3. Para cada proyecto se calculan los días desde el último avance.
4. Si pasan más de 30 días, se crea o recupera una `AlertaRezago` con estado `Activa`.
5. El panel muestra la situación de los proyectos para apoyar el seguimiento académico.

### Preferencias y correo

Desde `/preferencias/`, cualquier usuario autenticado con perfil puede activar o desactivar los avisos de inicio de sesión, comentarios y minutas. El envío se centraliza en una función que consulta esas preferencias. En desarrollo, los correos se muestran en la consola por la configuración de `console.EmailBackend`.

## 6. Estado actual

### Ya construido

- Proyecto Django funcional con una aplicación principal llamada `seguimiento`.
- Tres roles de usuario con redirección a paneles separados.
- Registro de alumnos y registro de asesores restringido al coordinador.
- Inicio y cierre de sesión web.
- Inicio de sesión por API con token.
- Recuperación de contraseña con token temporal.
- Control de acceso por rol y bloqueo de cuentas inactivas.
- Modelo de proyectos de tesis con alumno, asesor y coordinador.
- Carga de PDFs con validación de extensión.
- Versionado automático de entregables y conservación de versiones anteriores.
- Revisión de entregables con retroalimentación.
- Registro de minutas y un compromiso por minuta desde la interfaz actual.
- Cálculo y generación de alertas por más de 30 días sin avance.
- Preferencias de notificaciones y avisos de correo.
- Integración con el panel de administración de Django.
- Migraciones iniciales y migración de preferencias.
- Script para poblar datos de demostración: 2 coordinadores, 5 asesores, 45 alumnos y sus proyectos.

### Pendiente o por corregir

- [`seguimiento/tests.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/seguimiento/tests.py) no contiene pruebas automatizadas reales. Falta cubrir autenticación, permisos, registros, carga de PDFs, versionado, minutas y alertas.
- La aplicación depende de un servidor MySQL local y de la base `tesina_db`; si MySQL no está iniciado o la base no existe, los comandos de comprobación y ejecución no pueden conectarse.
- El backend de correo es solo de consola. Para producción falta configurar SMTP u otro proveedor de correo.
- `DEBUG = True`, `ALLOWED_HOSTS` está vacío y la clave secreta está escrita directamente en [`config/settings.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/config/settings.py). Deben configurarse variables de entorno y valores seguros antes de publicar el sistema.
- No hay archivo de dependencias como `requirements.txt` o `pyproject.toml`; la instalación depende actualmente del entorno virtual existente.
- No existe una hoja de estilos o directorio de archivos estáticos propio claramente separado; varias pantallas dependen de estilos incluidos en las plantillas.
- El flujo actual de minutas crea un único compromiso por formulario. La estructura de datos permite varios compromisos, pero la interfaz todavía no los captura en una sola operación.
- La gestión de alertas se ejecuta al abrir el panel del coordinador; no hay una tarea programada que las genere automáticamente en segundo plano.
- No se observa una interfaz para que el alumno o el asesor marque compromisos como cumplidos ni para cambiar formalmente el estado de una alerta.
- El script [`pruebas.py`](C:/Users/luism/OneDrive/Escritorio/pruebas/pruebas.py) contiene credenciales comunes de demostración. Es útil para pruebas locales, pero no debe reutilizarse en un entorno real.

En resumen, el proyecto ya implementa un prototipo funcional de seguimiento de tesis con los principales flujos de los tres roles. Para considerarlo listo para producción todavía requiere pruebas, configuración segura, correo real, documentación de instalación y una estrategia de despliegue.
