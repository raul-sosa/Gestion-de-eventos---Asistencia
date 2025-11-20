# Sistema de Gestión de Asistencias a Eventos

Sistema web completo para la gestión y control de asistencias a eventos académicos, desarrollado con arquitectura de microservicios. Implementa autenticación segura, control de acceso basado en roles, registro de asistencias mediante lectura de códigos de barras y generación de reportes.

## Características Principales

- **Sistema Multiusuario**: Tres roles diferenciados (Administrador, Encargado, Estudiante)
- **Gestión de Eventos**: Crear, editar, eliminar y finalizar eventos con soporte de imágenes
- **Registro de Asistencias**: Escaneo de códigos de barras mediante cámara o entrada manual
- **Validación de Matrícula**: Control estricto de formato (5 dígitos numéricos)
- **Pre-registro**: Los estudiantes pueden registrarse anticipadamente a eventos
- **Importación de Datos**: Carga masiva de estudiantes desde archivos Excel
- **Reportes**: Generación de reportes en formato PDF y CSV
- **Diseño Responsivo**: Interfaz adaptable para dispositivos móviles
- **Autenticación Segura**: JWT con encriptación bcrypt

## Tecnologías

### Backend

- **FastAPI 0.115.0**: Framework web asíncrono de alto rendimiento
- **Python 3.x**: Lenguaje de programación
- **bcrypt**: Encriptación segura de contraseñas
- **PyJWT 2.9.0**: Autenticación mediante tokens JWT
- **Uvicorn**: Servidor ASGI
- **Pandas 2.2.0**: Procesamiento de datos Excel
- **ReportLab 4.0.7**: Generación de documentos PDF

### Frontend

- **React 18**: Biblioteca para interfaces de usuario
- **Vite 5.4.2**: Herramienta de construcción y servidor de desarrollo
- **React Router DOM 6**: Sistema de navegación
- **Axios 1.7.7**: Cliente HTTP
- **html5-qrcode**: Lectura de códigos de barras mediante cámara
- **CSS3**: Estilos personalizados con diseño responsivo

### Arquitectura

- **Microservicios**: 4 servicios independientes comunicados mediante API REST
- **API Gateway**: Punto de entrada único (puerto 8100)
- **JSON Storage**: Persistencia de datos en archivos JSON
- **Proxy Inverso**: Vite proxy para desarrollo

## Estructura del Proyecto

```
Asistencia-eventos/
├── backend-microservices/
│   ├── api-gateway/          # Puerto 8100
│   ├── users-service/        # Puerto 8101
│   ├── events-service/       # Puerto 8102
│   └── reports-service/      # Puerto 8103
├── frontend-final/           # Puerto 5173
├── INICIO_RAPIDO.bat         # Inicio automático (Windows)
├── instalar.ps1              # Instalación de dependencias
└── README.md
```

## Requisitos Previos

- **Python 3.13** o superior
- **Node.js 18** o superior
- **npm** o **yarn**
- **Windows** (para scripts .bat) o **Linux/Mac** (usar comandos manuales)

## Instalación

### Opción 1: Instalación Automática (Windows)

1. Abre PowerShell en la carpeta del proyecto
2. Ejecuta el script de instalación:

```powershell
.\instalar.ps1
```

Si aparece error de política de ejecución:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\instalar.ps1
```

### Opción 2: Instalación Manual

#### Backend (cada microservicio)

```bash
# Users Service
cd backend-microservices/users-service
pip install -r requirements.txt

# Events Service
cd ../events-service
pip install -r requirements.txt

# Reports Service
cd ../reports-service
pip install -r requirements.txt

# API Gateway
cd ../api-gateway
pip install -r requirements.txt
```

#### Frontend

```bash
cd frontend-final
npm install
```

## Ejecución

### Opción 1: Inicio Automático (Windows)

Simplemente ejecuta:

```bash
INICIO_RAPIDO.bat
```

Esto iniciará automáticamente:

- Users Service (puerto 8101)
- Events Service (puerto 8102)
- Reports Service (puerto 8103)
- API Gateway (puerto 8100)
- Frontend (puerto 5173)

### Opción 2: Inicio Manual

Abre **5 terminales diferentes** y ejecuta en cada una:

#### Terminal 1 - Users Service

```bash
cd backend-microservices/users-service
python app.py
```

#### Terminal 2 - Events Service

```bash
cd backend-microservices/events-service
python app.py
```

#### Terminal 3 - Reports Service

```bash
cd backend-microservices/reports-service
python app.py
```

#### Terminal 4 - API Gateway

```bash
cd backend-microservices/api-gateway
python app.py
```

#### Terminal 5 - Frontend

```bash
cd frontend-final
npm run dev
```

## Acceso al Sistema

Una vez iniciado, accede a:

**URL**: http://localhost:5173

**Credenciales por defecto**:

| Rol           | Usuario      | Contraseña      | Permisos                             |
| ------------- | ------------ | --------------- | ------------------------------------ |
| Administrador | `admin`      | `admin123`      | Acceso completo al sistema           |
| Encargado     | `encargado`  | `encargado123`  | Registro y validación de asistencias |
| Estudiante    | `estudiante` | `estudiante123` | Consulta de eventos y pre-registro   |

## Verificación

### Health Check

Verifica que todos los servicios estén funcionando:

```
http://localhost:8100/health
```

Debe mostrar todos los servicios como "healthy".

### Servicios Individuales

- Users Service: http://localhost:8101/
- Events Service: http://localhost:8102/
- Reports Service: http://localhost:8103/
- API Gateway: http://localhost:8100/
- Frontend: http://localhost:5173/

## Uso del Sistema

### Funcionalidades por Rol

#### Administrador

- Gestión completa de eventos (crear, editar, eliminar, finalizar)
- Agregar imágenes a eventos mediante URL
- Importar base de datos de estudiantes desde Excel
- Generar reportes en PDF y CSV
- Validar asistencias
- Ver estadísticas globales

#### Encargado de Asistencia

- Visualizar eventos activos
- Registrar asistencias mediante:
  - Escaneo de código de barras con cámara
  - Entrada manual de matrícula (5 dígitos)
- Validar asistencias registradas
- Ver estadísticas de asistencia por evento

#### Estudiante

- Consultar eventos disponibles
- Pre-registrarse a eventos
- Ver historial de asistencias
- Dashboard personalizado

### Registro de Asistencias

#### Desde Computadora

1. Login como encargado
2. Seleccionar evento activo
3. Ingresar matrícula (5 dígitos numéricos)
4. El sistema valida y registra automáticamente

#### Desde Dispositivo Móvil

1. Conectarse a la misma red WiFi
2. Acceder a `http://IP_SERVIDOR:5173`
3. Login como encargado
4. Usar botón de cámara para escanear códigos de barras
5. El registro se guarda en el servidor central

### Importación de Estudiantes

1. Preparar archivo Excel con columnas:

   - matricula (5 dígitos)
   - nombre
   - carrera (opcional)
   - semestre (opcional)
   - email (opcional)

2. Colocar archivo `alumnos.xlsx` en la raíz del proyecto

3. Acceder a: `http://localhost:8100/api/students/import-excel`

### Generación de Reportes

- **PDF**: Reporte completo de evento con lista de asistentes
- **CSV**: Exportación de datos para análisis
- **Filtros**: Por evento, fecha, estado de validación

## Arquitectura de Microservicios

### API Gateway (Puerto 8100)

- Punto de entrada único
- Enrutamiento a microservicios
- Manejo de CORS
- Health checks

### Users Service (Puerto 8101)

- Autenticación con JWT
- Gestión de usuarios
- Encriptación con bcrypt
- Verificación de tokens

### Events Service (Puerto 8102)

- CRUD de eventos
- Registro de asistencias
- Control de capacidad
- Validación de asistencias
- Finalización de eventos

### Reports Service (Puerto 8103)

- Estadísticas globales
- Búsqueda de asistencias
- Filtros avanzados
- Exportación a CSV

## Flujo de Datos

```
Frontend (5173)
    ↓
Vite Proxy (/api)
    ↓
API Gateway (8100)
    ↓
┌───────────┬──────────────┬────────────────┐
│           │              │                │
Users       Events         Reports
Service     Service        Service
(8101)      (8102)         (8103)
```

## Seguridad

- **Autenticación**: JWT con expiración de 8 horas
- **Encriptación**: bcrypt para contraseñas
- **Validación**: Tokens en cada request
- **CORS**: Configurado para desarrollo

## Persistencia de Datos

Los datos se almacenan en archivos JSON:

- `users-service/users_db.json`: Usuarios
- `events-service/events_db.json`: Eventos
- `events-service/attendances_db.json`: Asistencias

## Solución de Problemas

### Error: Puerto en uso

```bash
# Verificar puertos ocupados
netstat -ano | findstr "8100 8101 8102 8103 5173"

# Cerrar proceso (Windows)
taskkill /PID [número] /F
```

### Error: Módulo no encontrado

```bash
# Reinstalar dependencias del backend
cd backend-microservices/[servicio]
pip install -r requirements.txt --force-reinstall

# Reinstalar dependencias del frontend
cd frontend-final
npm install
```

### Error: CORS

Asegúrate de que:

1. Todos los servicios estén corriendo
2. El API Gateway esté en puerto 8100
3. El frontend esté usando el proxy de Vite

### Error 503: Service Unavailable

Verifica que todos los microservicios estén corriendo:

```bash
# Windows
netstat -ano | findstr "8101 8102 8103"

# Deben aparecer 3 líneas
```

## Desarrollo

### Agregar Nuevas Funcionalidades

1. **Backend**: Agrega endpoints en el microservicio correspondiente
2. **API Gateway**: Agrega la ruta proxy si es necesario
3. **Frontend**: Crea componentes y páginas según necesites

### Estructura de Código

- **Backend**: Cada servicio es independiente con su propia lógica
- **Frontend**: Componentes reutilizables en `src/components/`
- **Estilos**: CSS modular por componente

## Próximos Pasos

### Mejoras Sugeridas

1. **Base de Datos**: Migrar de JSON a PostgreSQL/MongoDB
2. **Docker**: Containerizar microservicios
3. **Tests**: Agregar pruebas unitarias e integración
4. **CI/CD**: Pipeline de despliegue automatizado
5. **Logs**: Sistema centralizado de logging
6. **Monitoring**: Métricas y alertas

## Acceso desde Red Local

### Configuración para Dispositivos Móviles

1. Obtener IP del servidor:

   ```bash
   ipconfig
   # Buscar: Dirección IPv4 (ej: 192.168.1.100)
   ```

2. El archivo `vite.config.js` ya está configurado con `host: '0.0.0.0'`

3. Desde dispositivo móvil en la misma red WiFi:

   - Acceder a: `http://IP_SERVIDOR:5173`
   - Ejemplo: `http://192.168.1.100:5173`

4. Configurar firewall de Windows si es necesario:
   - Permitir puerto 5173 (Frontend)
   - Permitir puerto 8100 (API Gateway)

## Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Crea un Pull Request

---

**Versión**: 2.0.0  
**Última actualización**: Noviembre 2025  
**Proyecto Académico**: Sistema de Gestión de Asistencias
