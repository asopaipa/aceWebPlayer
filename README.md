**IMPORTANT: This repository does not host or link to any illegal content**
**IMPORTANTE: Este repositorio ni aloja ni enlaza ningún contenido ilegal**

# Configuración de AceStream Player con Docker

Esta guía te ayudará a configurar AceStream Player utilizando Docker.

## Prerrequisitos

- Docker y Docker Compose instalados en tu sistema

## Instrucciones de Configuración

1. **Accede al Directorio del Código**  
   Navega al directorio que contiene el código fuente. 

2. **Construye la Imagen de Docker**
   
   En Linux:
   ```bash
   chmod +x run_docker.sh
   ./run_docker.sh
   ```
   
   En Windows usando PowerShell:
   ```bash
   run_docker.ps1
   ```
   
4. **Accede**  
   Accede con un navegador por el puerto que hayas indicado, por ejemplo: http://IP:5001
   
   La primera vez se recomienda cargar la lista por defecto. 

## Otras consideraciones

Si vas a usar Cloudflare, tendrás que usar puertos diferentes a los que están por defecto. Por ejemplo 8080 para la web y 8880 para Acestream. 

## Capturas

![imatge](https://github.com/user-attachments/assets/85ce989b-5270-4972-ba04-2a94c0d292c8)

