#!/bin/bash

# Pedir el puerto al usuario
read -p "¿En qué puerto quieres que se publique la web? (5001) " PORT

# Preguntar si se quiere permitir el acceso remoto
read -p "¿Quieres permitir el acceso a través de Internet? (sí/NO): " ALLOW_REMOTE_ACCESS

# Exportar la variable de entorno para el puerto
export PORT=$PORT

# Eliminar los comentarios (quitar "#") de las líneas correspondientes si la respuesta es "sí"
if [ "$ALLOW_REMOTE_ACCESS" == "sí" ] || [ "$ALLOW_REMOTE_ACCESS" == "si" ]; then
  # Si la respuesta es sí, descomentar las líneas relacionadas con ALLOW_REMOTE_ACCESS
  echo "Configurando acceso remoto..."

  # Descomentar las líneas relacionadas con environment y ALLOW_REMOTE_ACCESS
  sed -i '/#environment:/s/#//g' docker-compose.yml
  sed -i '/#  - ALLOW_REMOTE_ACCESS=yes/s/#//g' docker-compose.yml
else
  # Si la respuesta es no, no hacer cambios
  echo "No se habilita el acceso remoto."
fi




docker build -t acestream-player .

# Levantar el contenedor con docker-compose
docker-compose up -d
