#!/bin/bash


DOCKER_COMPOSE_CMD=""

# Verificar si docker compose está disponible
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
elif docker-compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "Ni 'docker compose' ni 'docker-compose' están instalados."
    exit 1
fi


# Pedir el puerto al usuario
read -p "¿En qué puerto quieres que se publique la web? (5001) " PORT

read -p "¿En qué puerto quieres que se publique el Acestream? (6878) " PORTACE

# Preguntar si se quiere permitir el acceso remoto
read -p "¿Quieres permitir el acceso a través de Internet? (sí/NO): " ALLOW_REMOTE_ACCESS

# Exportar la variable de entorno para el puerto
export PORT=$PORT
export PORTACE=$PORTACE

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

if [ -n "$PUERTOACE" ]; then
    sed -i "s/6878/$PUERTOACE/g" ./static/js/main.js
    sed -i "s/6878/$PUERTOACE/g" getLinks.py
fi


docker build -t acestream-player .

# Levantar el contenedor
$DOCKER_COMPOSE_CMD up -d
