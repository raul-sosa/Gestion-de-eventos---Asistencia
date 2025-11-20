# Frontend - Sistema de Asistencias

Aplicación web desarrollada con React + Vite para la gestión de asistencias a eventos.

## Características

- 🔐 Autenticación de usuario
- 📅 Gestión de eventos (Listar y Crear)
- 📝 Registro de asistencias en tiempo real
- 📊 Visualización de asistencias por evento
- 🎨 Interfaz moderna y responsiva

## Requisitos Previos

- Node.js 16+ y npm

## Instalación

```bash
npm install
```

## Ejecución en Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en: `http://localhost:3000`

## Construcción para Producción

```bash
npm run build
```

## Credenciales de Prueba

- **Usuario:** organizador
- **Contraseña:** admin123

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/
│   │   ├── Login.jsx              # Componente de autenticación
│   │   ├── EventList.jsx          # Lista de eventos
│   │   ├── EventForm.jsx          # Formulario de creación
│   │   └── AttendanceRegister.jsx # Registro de asistencias
│   ├── App.jsx                    # Componente principal
│   ├── main.jsx                   # Punto de entrada
│   └── index.css                  # Estilos globales
├── index.html
├── vite.config.js
└── package.json
```

## Tecnologías Utilizadas

- React 18
- Vite
- Axios (HTTP Client)
- CSS3 (Estilos personalizados)
