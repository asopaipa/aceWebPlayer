**Este repositorio ni aloja ni enlaza ningún contenido ilegal / This repository does not host or link to any illegal content**

# ¿Qué es AceStream Player?

Es un reproductor web que te permite cargar listas con acestreams y reproducirlas en el navegador. De esta forma, puedes ver los vídeos en cualquier dispositivo con navegador sin necesidad de tener instalado Acestream en cada uno de ellos. Tiene soporte tanto para películas como para directos e incopora agenda deportiva.

## Captura

![imatge](https://github.com/user-attachments/assets/1478f233-a5bd-4c45-a1a5-d083dc6333f8)

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

· Si vas a usar Cloudflare, tendrás que usar puertos diferentes a los que están por defecto. Por ejemplo 8080 para la web y 8880 para Acestream. 

· Los navegadores no reproducen de forma nativa todos los codecs de vídeo. Puedes conectar las listas con Kodi, VLC o tu sistema favorito, mediante la exportación de los M3U's 

· La exportación de los strm publica sin contraseña todos los enlaces en la ruta http://IP:PUERTO/output_strm

