# Diagnóstico y plan de acción de SocialImage

Fecha de revisión: 4 de noviembre de 2026.

## Dictamen

El proyecto está en fase de prototipo avanzado, previo a un MVP estable. Tiene una estructura coherente de aplicaciones Django (`account`, `images`, `actions`) y buena parte de las pantallas y modelos del producto. Sin embargo, varios recorridos centrales contienen errores que impiden considerarlo listo para una beta pública.

La siguiente entrega debería ser una versión local reproducible que permita registrarse, iniciar sesión, guardar una imagen, verla, reaccionar y seguir a otra persona. Después conviene completar el flujo de actividad y preparar un entorno de pruebas desplegado.

No asigno un porcentaje global: contar pantallas o modelos como funcionalidades terminadas ocultaría los fallos de integración encontrados.

## Alcance y comprobaciones

Se revisaron código, plantillas, configuración, dependencias, migraciones, documentación y estado de Git. Se ejecutaron comprobaciones con el Python del entorno virtual existente. Se hicieron consultas de lectura y pruebas de formularios y backend con objetos simulados, sin guardar usuarios ni descargar imágenes externas.

| Comprobación | Resultado | Interpretación |
| --- | --- | --- |
| Python del entorno virtual | 3.14.0 | El entorno existente ejecuta el proyecto. |
| Django instalado | 6.0.6 | Coincide con `requirements.txt`. |
| Dependencias instaladas frente al archivo | Sin diferencias de versión | El entorno coincide con las versiones fijadas. |
| `manage.py check` | Sin errores | La configuración carga; no garantiza el funcionamiento de los recorridos. |
| `manage.py check --deploy` | 6 advertencias | La configuración examinada es de desarrollo. |
| `manage.py showmigrations` | Migraciones locales aplicadas | Incluye una migración propia dentro de Django instalado, fuera del repositorio. |
| `makemigrations --check --dry-run` | Sin cambios detectados | Resultado condicionado por esa modificación del entorno virtual. |
| `manage.py test` | 0 pruebas | No existe evidencia automatizada de regresión. |
| `pip check` | Sin dependencias incompatibles declaradas | No es una auditoría de vulnerabilidades. |
| Compilación de plantillas HTML | Sin errores de compilación | No comprueba JavaScript ni todos los contextos de renderizado. |
| GET anónimo a login y registro | HTTP 200 | Ambas páginas responden en este entorno. |
| GET a `/` | HTTP 404 | Falta definir una entrada al sitio. |

No se realizó una prueba visual en navegador, un recorrido completo de Google OAuth, entrega real de correos, una instalación limpia ni una auditoría exhaustiva de seguridad de dependencias. Sus resultados siguen pendientes.

## Estado por área

| Área | Estado observado | Pendiente principal |
| --- | --- | --- |
| Arquitectura | Monolito Django pequeño y comprensible | Conservar esta base y ordenar configuración y migraciones. |
| Autenticación y perfiles | Formularios, rutas y edición implementados | Validación de contraseñas, consistencia de perfiles y pruebas de integración. |
| Google OAuth | Backend, credenciales por entorno y pipeline presentes | Validar recorrido real, errores y redirecciones por ambiente. |
| Imágenes y miniaturas | Modelos, formularios y páginas presentes | Corregir almacenamiento, descarga y validación de URL. |
| Me gusta | Relación y endpoint implementados | Reparar JavaScript y mantener consistente el contador. |
| Seguimiento | Modelo, endpoint y páginas en cambios locales | Restricciones de integridad, validación y pruebas. |
| Actividad | Modelo y administración presentes | Registrar eventos y construir el feed. |
| Interfaz | Base HTML/CSS y navegación disponibles | Adaptación móvil, accesibilidad y estados de carga/error. |
| Calidad y operación | Dependencias fijadas y README extenso | Pruebas, CI, instalación reproducible y preparación de despliegue. |

Hay siete archivos versionados modificados y nuevas rutas, migraciones y la aplicación `actions` sin seguimiento en Git. Son trabajo existente del usuario; deben revisarse y conservarse al organizar las siguientes entregas. El README está desfasado: describe como terminados recorridos con errores y no refleja todo el avance de seguimiento y actividad.

## Hallazgos prioritarios

### P0 — Corregir antes de exponer una beta pública

1. **El guardado de imágenes está roto.** En `images/models.py:16`, `image` es un `TextField`, pero `images/forms.py:31` llama a `image.image.save(...)` como si fuera un campo de archivo. Con una respuesta HTTP simulada se reproduce `AttributeError: 'str' object has no attribute 'save'`. Definir `ImageField` con almacenamiento y una migración que conserve las rutas existentes; revisar los archivos reales antes de transformar datos.

2. **La validación de URL rechaza imágenes normales.** `images/forms.py:18` divide desde el primer punto de la URL: `https://example.com/photo.jpg` acaba evaluando `com/photo.jpg` como extensión y resulta inválida. Usar el path de una URL analizada, manejar parámetros y verificar el contenido real con Pillow.

3. **La descarga remota carece de controles suficientes.** `requests.get(image_url)` no tiene timeout, límite de bytes, comprobación de estado, validación de destino ni control de redirecciones. La validación actual admite `https://localhost/photo.jpg`; su descarga se simuló, sin acceder a ese destino. Antes de habilitar la importación, bloquear destinos locales, privados y reservados, comprobar cada salto y limitar tamaño y dimensiones. Es un riesgo de solicitudes desde el servidor hacia recursos internos, además de disponibilidad.

4. **Existe una migración propia dentro del paquete instalado de Django.** `.venv/Lib/site-packages/django/contrib/auth/migrations/0013_user_following.py` agrega la relación definida dinámicamente en `account/models.py:40`. Ese archivo no forma parte del repositorio. Una reinstalación puede perder la equivalencia entre modelos y estado de migraciones. Resolver el seguimiento dentro del código propio, por ejemplo consultando `Contact`, y diseñar la transición considerando las migraciones ya registradas. No borrar registros de migraciones ni editar la base a ciegas.

5. **La configuración y las claves no están preparadas para producción.** `SECRET_KEY` está en el código, `DEBUG=True`, faltan controles HTTPS/cookies y `cert.key` está versionado. Usar secretos propios por entorno, reemplazar la clave Django para despliegue y dejar de distribuir claves privadas. Si esas claves se utilizaron fuera del entorno local, sustituirlas en los entornos afectados. El `.env` y SQLite sí están ignorados por Git.

6. **El registro acepta contraseñas débiles.** La prueba del formulario aceptó la contraseña `1`. `UserRegisterForm` comprueba coincidencia, pero no invoca los validadores de contraseña configurados. Integrar `validate_password` o un formulario basado en `UserCreationForm`. El backend de email también devuelve un usuario inactivo simulado; debe aplicar la política de actividad en autenticación y recuperación de usuario. La vista estándar de login añade su propia comprobación de usuario activo: este hallazgo no demuestra por sí solo que permita ese login.

### P1 — Necesario para un MVP consistente

- **JavaScript de interacciones:** `account/templates/base.html:51` referencia `js-cookied` en lugar de `js-cookie`. El detalle de imagen usa `csrf_token` como variable JavaScript, mientras la base declara `csrftoken`; además tiene el bloque de script anidado en el contenido. Corregir la dependencia, el token y la ubicación del bloque; comprobar los POST con protección CSRF activa.
- **Desplazamiento infinito:** frontend envía `images_only`, backend lee `image_only`; también aparecen `insertAdjacentHTLM` y `False` en JavaScript. Corregir nombres, usar `insertAdjacentHTML` y `false`, y añadir recuperación ante fallos sin saltarse páginas.
- **Contador de me gusta:** `total_likes` existe, pero las vistas solo modifican la relación. Una consulta encontró una imagen cuyo contador difiere del número real de relaciones. Elegir una fuente de verdad: contar relaciones o mantener el agregado de forma consistente y reconstruible.
- **Integridad del seguimiento:** faltan restricciones de pareja única y contra seguirse a sí mismo. El endpoint trata cualquier acción distinta de `follow` como dejar de seguir; también hay que manejar IDs no válidos y usuarios inactivos. Aplicar validación explícita, restricciones en base de datos y respuestas HTTP adecuadas.
- **Feed incompleto:** `Action` está definido, pero no se registra actividad desde las operaciones y el dashboard no la consulta ni presenta. Implementar eventos y feed paginado de personas seguidas.
- **Cuentas y perfiles:** los perfiles se crean en registro y OAuth; otros caminos, como administración, pueden producir usuarios sin perfil. Asegurar la relación y usar transacciones en cambios que afecten varias entidades. Revisar unicidad de email y comparación sin distinción de mayúsculas, incluyendo registros existentes.
- **Restablecimiento de contraseña:** `pasword_reset_complete.html` está mal nombrada. La ruta correcta `/account/reset/done/` devuelve 200 porque usa la plantilla de administración de Django; renombrar la propia para conservar la identidad visual. El correo actual se escribe en consola y no se entrega al usuario.

### P2 — Mejora de producto y mantenimiento

- Definir portada o redirección de `/`, idioma e identidad coherentes entre SocialImage y Social Web.
- Agregar `viewport`, idioma HTML, textos alternativos, foco visible y navegación por teclado; sustituir anchuras y márgenes rígidos por una disposición adaptable.
- Incorporar avatar predeterminado, estados vacíos, indicadores de carga, recuperación de errores y protección contra clics repetidos.
- Corregir enlaces HTML anidados en las tarjetas y evitar `message|safe` cuando no se necesite HTML confiable.
- Paginar personas e imágenes de perfil; medir consultas y aplicar `select_related`/`prefetch_related` donde corresponda.
- Parametrizar el dominio del bookmarklet, hoy fijado a `127.0.0.1:8000`, y documentar las restricciones de CSP y HTTPS de sitios externos. Añadir una alternativa de importación manual por URL.
- Añadir edición y eliminación de imágenes propias con permisos; después evaluar búsqueda, etiquetas y colecciones según uso real.
- Actualizar instalación: el README indica Python 3.11+, pero Django 6.0 requiere Python 3.12 o superior dentro de sus versiones compatibles. El comando global `python` de esta máquina apunta a 3.10; usar explícitamente el entorno virtual.

## Plan de ejecución

Estimaciones orientativas para una persona con dedicación sostenida y familiaridad con Django. Cada fase depende de la anterior; las migraciones y la integración con servicios externos pueden ampliar los plazos.

| Fase | Trabajo concreto | Criterio de aceptación | Esfuerzo orientativo |
| --- | --- | --- | --- |
| 1. Recuperar reproducibilidad | Revisar cambios locales; respaldar SQLite y media; resolver migración en dependencia; crear `.env.example` sin secretos; corregir instrucciones. | Un checkout limpio instala y migra una base vacía sin modificar paquetes; existe una transición ensayada para la base actual. | 2–3 días |
| 2. Estabilizar y proteger el núcleo | Reparar imágenes y URL; proteger descarga; corregir JS, CSRF y paginación; validar contraseñas; ordenar secretos. Añadir pruebas de estos fallos junto con las correcciones. | Registro → login → guardar → ver → like/unlike → segunda página funciona; entradas maliciosas o inválidas se rechazan sin errores 500. | 4–6 días |
| 3. Completar el MVP social | Restricciones y validación de seguimiento; sincronización de likes; eventos y feed; edición/eliminación con permisos; estados de interfaz. | Dos usuarios pueden seguirse y ver actividad pertinente; repetir acciones no duplica relaciones ni altera contadores incorrectamente. | 3–5 días |
| 4. Actualizar y mejorar experiencia | Actualizaciones controladas; diseño móvil; accesibilidad; paginación y consultas; README y roadmap reales. | Suite sin regresiones, recorrido visual en móvil/escritorio y ausencia de errores JavaScript en los flujos principales. | 3–5 días |
| 5. Preparar beta | CI, configuración de producción, servidor WSGI/ASGI, base y almacenamiento persistentes, correo real, logs, copias y restauración. | Despliegue de pruebas repetible; recuperación de contraseña entregada; controles de despliegue revisados; restauración y reversión ensayadas. | 3–5 días |

Total orientativo: 15–24 días de trabajo efectivo. No equivale a una fecha comprometida de lanzamiento.

### Actualización tecnológica

Conservar Django y las plantillas actuales permite concentrar esfuerzo en los problemas encontrados. El alcance observado no justifica una reescritura del frontend ni dividir el backend en servicios.

Primero restablecer la reproducibilidad y las pruebas. Después actualizar al parche vigente de la rama soportada seleccionada y validar OAuth, Pillow, easy-thumbnails y Python Social Auth. La página oficial consultada muestra Django 6.0.10 para la rama 6.0 y 6.1.3 como versión general más reciente; comprobar de nuevo las versiones cuando se ejecute la actualización. El salto a otra rama debe tener su propia validación de compatibilidad.

Separar dependencias de ejecución y herramientas de desarrollo, mantener versiones reproducibles y añadir auditoría de vulnerabilidades. No se realizó esa auditoría en esta revisión.

SQLite sigue siendo útil para desarrollo. Para una beta con escrituras concurrentes, planificar PostgreSQL y ensayar la migración de datos. Añadir caché o colas de trabajo después de medir necesidades; las descargas y miniaturas pueden pasar a tareas si su latencia lo exige.

### Pruebas mínimas y automatización

- Registro con contraseña débil, email duplicado y usuario sin perfil; login por usuario/email y bloqueo de inactivos según la política definida.
- Recuperación de contraseña con backend de correo de pruebas y plantilla propia.
- Importación válida y fallos de destino, redirección, formato, timeout y exceso de tamaño, usando respuestas simuladas.
- Likes y seguimiento repetidos, IDs y acciones inválidos, restricciones y permisos de edición/eliminación.
- Paginación inicial, siguiente página y fin de resultados; feed limitado a la audiencia definida.
- Recorrido en navegador con CSRF activo, imágenes y cookies; revisión de consola y móvil.
- CI desde entorno limpio: instalación, `pip check`, checks Django, coherencia de migraciones y suite. Ejecutar `check --deploy` con ajustes reales de producción.

### Primera entrega recomendada

Una entrega centrada en instalación reproducible, importación segura de imágenes, likes y paginación corregidos, con pruebas de regresión y documentación de arranque. El criterio de cierre es que otra persona pueda clonar y completar ese recorrido sin cambios manuales dentro de `.venv`.

## Referencias oficiales consultadas

- [Compatibilidad de Python con Django 6.0](https://docs.djangoproject.com/en/6.0/releases/6.0/).
- [Versiones y soporte de Django](https://www.djangoproject.com/download/).
- [Validación de contraseñas](https://docs.djangoproject.com/en/6.0/topics/auth/passwords/#password-validation).
- [Lista de preparación para despliegue](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/).
