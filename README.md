# Configuración de AceStream Player con Docker

Esta guía te ayudará a configurar AceStream Player utilizando Docker.

## Prerrequisitos

- Docker instalado en tu sistema
- Docker Compose instalado en tu sistema

## Instrucciones de Configuración

1. **Accede al Directorio del Código**  
   Navega al directorio que contiene el código fuente. Si quieres que el servidor se ejecute desde internet, edita el archivo `docker-compose.yml` y descomenta las líneas indicadas.

2. **Construye la Imagen de Docker**  
   ```bash
   docker build -t acestream-player .
   ```

3. **Inicia el Servicio**  
   ```bash
   docker compose up -d
   ```

4. **Accede**  
   Accede con un navegador por el puerto 5001. La primera vez hay que cargar la lista por defecto.

## Solución de Problemas

- Si cualquier comando que comience con `docker compose` da un error, intenta reemplazar `docker compose` con `docker-compose`.
