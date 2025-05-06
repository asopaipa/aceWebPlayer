#!/bin/bash
set -e # Salir si un comando falla

# Argumentos por defecto que esperamos si no se pasa nada más (vienen del CMD del Dockerfile)
DEFAULT_EXEC_ARG1="python"
DEFAULT_EXEC_ARG2="app.py"

echo "--- run_compiled.sh iniciado ---"
echo "Argumentos recibidos: $@"
echo "Número de argumentos: $#"

# Escenario 1: "Versión sin compilar" o ejecución por defecto de la "compilada"
# Esto sucede si 'docker run mi-imagen' se ejecuta sin argumentos adicionales.
# En este caso, "$1" será "python" y "$2" será "app.py" (del CMD del Dockerfile).
# O si el run_docker.sh externo simplemente hace 'docker-compose up' y el compose
# no pasa argumentos al entrypoint.
if [ "$#" -eq 2 ] && [ "$1" = "$DEFAULT_EXEC_ARG1" ] && [ "$2" = "$DEFAULT_EXEC_ARG2" ]; then
  echo "MODO: Ejecución por defecto detectada (probablemente 'sin compilar' o 'compilada' sin params de setup)."
  echo "No se realizarán tareas de setup adicionales por run_compiled.sh."
  echo "Ejecutando Flask directamente con: $@"
  exec "$@" # Esto ejecutará "python app.py"

# Escenario 2: "Versión compilada" con parámetros de setup pasados en `docker run`
# Esto sucede si 'docker run mi-imagen param1 param2 ...' se ejecuta.
# Los argumentos "python" y "app.py" del CMD del Dockerfile son REEMPLAZADOS.
elif [ "$#" -eq 2 ]; then
  echo "MODO: Ejecución 'compilada' con parámetros de setup detectada."
  PARAMETROS_SETUP=("$@") # Guardamos todos los parámetros de setup

  echo "Parámetros de setup recibidos: ${PARAMETROS_SETUP[@]}"
  echo "Realizando acciones de setup con estos parámetros..."

  USUARIO="${PARAMETROS_SETUP[0]}"
  CONTRASENYA="${PARAMETROS_SETUP[1]}"


  sed -i "s/USERNAME = \"\"/USERNAME = \"$USUARIO\"/g" app.py
  sed -i "s/PASSWORD = \"\"/PASSWORD = \"$CONTRASENYA\"/g" app.py

  echo "Setup completado."
  echo "Ahora iniciando Flask con los valores por defecto ($DEFAULT_EXEC_ARG1 $DEFAULT_EXEC_ARG2)..."
  # Después del setup, ejecutamos Flask.
  # Usamos 'exec' para que Flask se convierta en el proceso principal (PID 1 idealmente)
  exec "$DEFAULT_EXEC_ARG1" "$DEFAULT_EXEC_ARG2"

else
  # Este caso es menos probable si tienes un CMD por defecto, pero es bueno tenerlo.
  echo "MODO: No se recibieron 2 argumentos (usuario y contrasenya)."
  echo "Por favor, verifica la configuración o pasa los argumentos necesarios."
  echo "Intentando iniciar Flask con valores por defecto de todas formas..."
  exec "$DEFAULT_EXEC_ARG1" "$DEFAULT_EXEC_ARG2"
fi

echo "--- run_compiled.sh finalizado (no debería verse si 'exec' funcionó) ---"
