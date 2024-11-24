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

3. **Inicia el Servicio de Proxy HTTP**  
   ```bash
   docker compose up -d acestream-http-proxy
   ```

4. **Obtén la Dirección IP del Proxy**  
   Ejecuta el siguiente comando para obtener la dirección IP de `acestream-http-proxy`:
   ```bash
   docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' acestream-http-proxy
   ```

5. **Actualiza la IP Local**  
   Copia la dirección IP que aparece en la consola y pégala en la variable `LOCAL_IP` dentro del archivo `docker-compose.yml`.

6. **Inicia la Configuración Completa**  
   ```bash
   docker compose up -d
   ```

## Solución de Problemas

- Si cualquier comando que comience con `docker compose` da un error, intenta reemplazar `docker compose` con `docker-compose`.
