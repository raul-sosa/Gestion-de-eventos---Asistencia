# Sistema de Gestión de Asistencias a Eventos

Sistema web completo para la gestión y control de asistencias a eventos académicos, desarrollado con arquitectura de microservicios utilizando FastAPI y React.

## Características Principales

- **Gestión de Eventos**: Crear, editar, eliminar y finalizar eventos con soporte de imágenes
- **Registro de Asistencias**: Escaneo de códigos de barras mediante cámara o entrada manual de matrícula (5 dígitos)
- **Búsqueda Automática de Estudiantes**: El sistema busca y muestra automáticamente el nombre del estudiante al registrar asistencia
- **Pre-registro**: Los estudiantes pueden registrarse anticipadamente a eventos
- **Sistema Multiusuario**: 3 roles diferenciados (Administrador, Encargado, Estudiante)
- **Reportes**: Generación de reportes en PDF y CSV con información detallada de asistentes
- **Importación de Datos**: Carga masiva de estudiantes desde archivos Excel
- **Autenticación Segura**: JWT con encriptación bcrypt
- **Base de Datos SQL**: Almacenamiento persistente con SQLite
- **Validación de Asistencias**: Control de asistencias por parte de encargados
- **Estadísticas**: Dashboard con métricas de pre-registros y asistencias
- **Soporte de Imágenes**: Subida y visualización de imágenes para eventos

## Tecnologías

### Backend

- **FastAPI** - Framework web asíncrono
- **Python 3.x** - Lenguaje de programación
- **SQLite** - Base de datos
- **bcrypt** - Encriptación de contraseñas
- **PyJWT** - Autenticación JWT
- **Pandas** - Procesamiento de datos Excel
- **ReportLab** - Generación de PDFs

### Frontend

- **React 18** - Biblioteca UI
- **Vite** - Build tool
- **React Router** - Navegación
- **Axios** - Cliente HTTP
- **html5-qrcode** - Lectura de códigos de barras

### Arquitectura

**Microservicios con API Gateway**

El sistema utiliza una arquitectura de microservicios donde cada servicio es independiente y se comunica a través de HTTP:

- **API Gateway** (Puerto 8100): Punto de entrada único que enruta las peticiones a los servicios correspondientes
- **Users Service** (Puerto 8101): Gestión de usuarios, autenticación y autorización con JWT
- **Events Service** (Puerto 8102): Gestión de eventos, asistencias, pre-registros y estudiantes
- **Reports Service** (Puerto 8103): Generación de reportes, estadísticas y exportación de datos

**Modelo de Base de Datos**

SQLite con las siguientes tablas:

- `users`: Almacena usuarios del sistema con roles y contraseñas encriptadas
- `events`: Información de eventos (nombre, fecha, ubicación, capacidad, imagen_path, imagen_url)
- `attendances`: Registro de asistencias con validación y referencia al estudiante
- `pre_registros`: Pre-registros de estudiantes a eventos
- `students`: Catálogo de estudiantes importados desde Excel (matrícula de 5 dígitos)

## Instalación

### Requisitos

- Python 3.8+
- Node.js 16+
- npm

### Instalación Automática (Windows)

```bash
INSTALAR_DEPENDENCIAS.bat
```

### Instalación Manual

**Backend:**

```bash
cd backend-microservices/users-service
pip install -r requirements.txt

cd ../events-service
pip install -r requirements.txt

cd ../reports-service
pip install -r requirements.txt

cd ../api-gateway
pip install -r requirements.txt

cd ..
python init_database.py
```

**Frontend:**

```bash
cd frontend-final
npm install
```

## Uso

### Inicio Rápido

```bash
INICIO_RAPIDO.bat
```

Este script inicia automáticamente todos los servicios.

### Inicio Manual

Abrir 5 terminales:

```bash
# Terminal 1 - API Gateway
cd backend-microservices/api-gateway
python app.py

# Terminal 2 - Users Service
cd backend-microservices/users-service
python app.py

# Terminal 3 - Events Service
cd backend-microservices/events-service
python app.py

# Terminal 4 - Reports Service
cd backend-microservices/reports-service
python app.py

# Terminal 5 - Frontend
cd frontend-final
npm run dev
```

### Acceso

Abrir navegador en: `http://localhost:5173`

### Usuarios por Defecto

| Usuario    | Contraseña    | Rol           |
| ---------- | ------------- | ------------- |
| admin      | admin123      | Administrador |
| encargado  | encargado123  | Encargado     |
| estudiante | estudiante123 | Estudiante    |

## Importar Estudiantes

### Automático

```bash
IMPORTAR_ESTUDIANTES.bat
```

### Manual

```bash
cd backend-microservices
pip install pandas openpyxl
python import_students.py
```

El archivo `alumnos.xlsx` debe tener las columnas: Matricula, Nombre, Carrera, Semestre, Email

## Estructura del Proyecto

```
Asistencia-eventos/
├── backend-microservices/
│   ├── api-gateway/          # Puerto 8100
│   ├── users-service/        # Puerto 8101
│   ├── events-service/       # Puerto 8102
│   ├── reports-service/      # Puerto 8103
│   ├── database.py           # Configuración BD
│   ├── init_database.py      # Inicialización BD
│   └── import_students.py    # Importador Excel
├── frontend-final/           # Aplicación React
├── alumnos.xlsx             # Plantilla estudiantes
├── INICIO_RAPIDO.bat        # Inicio automático
├── IMPORTAR_ESTUDIANTES.bat # Importación automática
└── INSTALAR_DEPENDENCIAS.bat # Instalación automática
```

## Funcionalidades por Rol

### Administrador

- Gestión completa de usuarios
- Crear, editar y eliminar cualquier evento
- Finalizar cualquier evento (propio o de otros organizadores)
- Registrar asistencias (incluso en eventos finalizados)
- Acceso a todas las estadísticas y reportes
- Subir y gestionar imágenes de eventos

### Encargado

- Crear y gestionar sus propios eventos
- Finalizar únicamente sus propios eventos
- Registrar asistencias en eventos activos
- Validar asistencias
- Exportar reportes de sus eventos
- Subir imágenes a sus eventos

### Estudiante

- Ver eventos disponibles
- Pre-registrarse a eventos
- Ver sus pre-registros y asistencias

## API Endpoints

### Users Service (8101)

- `POST /api/users/login` - Iniciar sesión
- `POST /api/users/register` - Registrar usuario
- `GET /api/users/me` - Usuario actual

### Events Service (8102)

- `GET /api/events` - Listar eventos
- `POST /api/events` - Crear evento
- `PUT /api/events/{id}` - Actualizar evento
- `DELETE /api/events/{id}` - Eliminar evento (admin o propietario)
- `POST /api/events/{id}/finalize` - Finalizar evento (admin o propietario)
- `POST /api/attendances` - Registrar asistencia
- `GET /api/events/{id}/attendances` - Listar asistencias (incluye datos del estudiante)
- `POST /api/pre-registros` - Pre-registrarse
- `GET /api/students/search/{matricula}` - Buscar estudiante por matrícula
- `POST /api/events/upload-image` - Subir imagen
- `GET /api/uploads/images/{filename}` - Obtener imagen

### Reports Service (8103)

- `GET /api/reports/statistics/global` - Estadísticas globales
- `GET /api/reports/export/event/{id}/pdf` - Exportar PDF
- `GET /api/reports/export/event/{id}/csv` - Exportar CSV

## Base de Datos

### Tablas

- **users** - Usuarios del sistema
- **events** - Eventos creados
- **attendances** - Registro de asistencias
- **pre_registros** - Pre-registros de estudiantes
- **students** - Catálogo de estudiantes

### Inicialización

```bash
cd backend-microservices
python init_database.py
```

## Flujo de Trabajo

### Crear un Evento

1. Login como Admin o Encargado
2. Ir a "Gestión de Eventos"
3. Click en "Crear Evento"
4. Completar formulario (nombre, descripción, fecha, ubicación, capacidad)
5. Opcionalmente subir una imagen del evento
6. Guardar evento

### Pre-registrarse a un Evento

1. Login como Estudiante
2. Ver eventos disponibles en el dashboard
3. Click en "Pre-registrarse" en el evento deseado
4. Ingresar matrícula (5 dígitos numéricos)
5. Confirmar pre-registro

### Registrar Asistencias

1. Login como Admin o Encargado
2. Ir al evento activo
3. Click en "Registrar Asistencias"
4. Escanear código de barras con la cámara o ingresar matrícula manualmente (5 dígitos)
5. El sistema busca automáticamente al estudiante en la base de datos
6. Si el estudiante existe, muestra su nombre, carrera y semestre
7. La asistencia se registra automáticamente
8. En la lista de asistencias registradas, se muestra el nombre del estudiante (o "Desconocido" si no está en la BD)

### Generar Reportes

1. Login como Admin o Encargado
2. Ir al evento deseado
3. Click en "Exportar PDF" o "Exportar CSV"
4. El reporte se descarga automáticamente con:
   - Información del evento
   - Lista de asistentes con matrícula, nombre y carrera
   - Hora de registro

## Desarrollo

### Agregar Funcionalidades

1. Identificar el microservicio correspondiente
2. Agregar endpoint en `app.py`
3. Actualizar frontend si es necesario

### Modificar Base de Datos

1. Editar `backend-microservices/database.py`
2. Ejecutar `python init_database.py`

## Solución de Problemas

**Error: "Servicio no disponible"**

- Verificar que todos los microservicios estén ejecutándose
- Revisar que los puertos no estén ocupados

**Error: "Token inválido"**

- Hacer logout y login nuevamente
- Verificar que Users Service esté activo

**Error 404 al buscar estudiantes**

- Importar estudiantes desde Excel con `IMPORTAR_ESTUDIANTES.bat`
- Verificar que las matrículas tengan exactamente 5 dígitos

**Las imágenes de eventos no se muestran**

- Verificar que el API Gateway esté ejecutándose
- Reiniciar todos los servicios con `INICIO_RAPIDO.bat`
- Las imágenes se sirven a través de `/api/uploads/images/`

**PDF no se puede abrir**

- Reiniciar API Gateway y Reports Service

**Estudiantes aparecen como "Desconocido" en asistencias**

- Verificar que los estudiantes estén importados en la base de datos
- Asegurarse de que las matrículas coincidan exactamente (5 dígitos)
- Reiniciar el Events Service para aplicar cambios

**Error 403 al finalizar evento**

- Solo el organizador del evento o un administrador pueden finalizarlo
- Verificar el rol del usuario en localStorage

## Seguridad

- Contraseñas encriptadas con bcrypt (factor de costo 12)
- Autenticación mediante JWT con expiración configurable
- Validación de permisos por rol en cada endpoint
- Tokens incluyen información de usuario y rol
- Protección CORS configurada en todos los servicios
