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



# Preguntar si se quiere permitir el acceso remoto
read -p "Si quieres proteger la web con usuario y contraseña, introduce el usuario: " USUARIO

if [ -n "$USUARIO" ]; then
    read -p "Introduce la contraseña: " CONTRASENYA
fi

# Exportar la variable de entorno para el puerto
export PORT=$PORT


if [ -n "$USUARIO" ]; then
    sed -i "s/USERNAME = \"\"/USERNAME = \"$USUARIO\"/g" app.py
    sed -i "s/PASSWORD = \"\"/PASSWORD = \"$CONTRASENYA\"/g" app.py
fi


docker build -t acestream-player .

# Levantar el contenedor
$DOCKER_COMPOSE_CMD up -d
