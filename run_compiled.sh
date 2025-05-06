#!/bin/bash

#gestiona cuando vienen parámetros desde la imagen compilada

PARAM1_VAL=""
PARAM2_VAL=""

# Opción 1: Usar argumentos de línea de comandos
if [ "$#" -ge 2 ]; then
  echo "Parámetros recibidos por línea de comandos."
  PARAM1_VAL="$1"
  PARAM2_VAL="$2"
# Opción 2: Usar variables de entorno (puedes darles prioridad si quieres)
elif [ -n "$ENV_PARAM1" ] && [ -n "$ENV_PARAM2" ]; then
  echo "Parámetros recibidos por variables de entorno."
  PARAM1_VAL="$ENV_PARAM1"
  PARAM2_VAL="$ENV_PARAM2"
# Opción 3: Pedir interactivamente si no se proporcionaron
else
  echo "No se proporcionaron parámetros, solicitando interactivamente:"
  read -r -p "Introduce el valor para Parámetro 1: " PARAM1_VAL
  read -r -p "Introduce el valor para Parámetro 2: " PARAM2_VAL
fi

# Validar que los parámetros no estén vacíos (ejemplo básico)
if [ -z "$PARAM1_VAL" ] || [ -z "$PARAM2_VAL" ]; then
  echo "Error: Ambos parámetros son requeridos."
  exit 1
fi

echo "----------------------------------------"
echo "Parámetro 1 recibido: $PARAM1_VAL"
echo "Parámetro 2 recibido: $PARAM2_VAL"
echo "----------------------------------------"

# Aquí va el resto de la lógica de tu script que usa PARAM1_VAL y PARAM2_VAL
echo "Ejecutando acciones con los parámetros..."
# Ejemplo:
# mkdir -p "$PARAM1_VAL"
# echo "$PARAM2_VAL" > "$PARAM1_VAL/info.txt"
sleep 5 # Simula trabajo

echo "Proceso completado."
