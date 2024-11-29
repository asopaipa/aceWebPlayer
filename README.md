# Configuración de AceStream Player con Docker

Esta guía te ayudará a configurar AceStream Player utilizando Docker.

## Prerrequisitos

- Docker instalado en tu sistema
- Docker Compose instalado en tu sistema

## Instrucciones de Configuración

1. **Accede al Directorio del Código**  
   Navega al directorio que contiene el código fuente. 

2. **Construye la Imagen de Docker**  
   ```bash
   chmod +x run_docker.sh
   ./run_docker.sh
   ```
   
3. **Accede**  
   Accede con un navegador por el puerto que hayas indicado. La primera vez se recomienda cargar la lista por defecto. Por ejemplo: http://IP:5001

## Solución de Problemas

- Si cualquier comando que comience con `docker compose` da un error, intenta reemplazar `docker compose` con `docker-compose`. 
