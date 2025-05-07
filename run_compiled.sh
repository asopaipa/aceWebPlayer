#!/bin/bash
set -e # Salir si un comando falla

# Argumentos por defecto que esperamos si no se pasa nada más (vienen del CMD del Dockerfile)
DEFAULT_EXEC_ARG1="python"
DEFAULT_EXEC_ARG2="app.py"
APP_FILE="app.py" # Nombre del archivo de la aplicación a modificar

echo "--- run_compiled.sh iniciado ---"
echo "Argumentos recibidos originalmente: $@"
echo "Número de argumentos originales: $#"

# Variables para almacenar los parámetros de setup
SETUP_USUARIO=""
SETUP_CONTRASENYA=""
# Variable para rastrear si se intentó pasar parámetros de configuración
INTENTO_SETUP=false

# Copiamos los argumentos para poder modificarlos (shift) durante el parseo
ARGS_COPY=("$@")

# Primero, verificamos el caso más común: ejecución por defecto sin argumentos en docker run
# Esto sucede si 'docker run mi-imagen' se ejecuta sin argumentos adicionales.
# En este caso, "$1" será "python" y "$2" será "app.py" (del CMD del Dockerfile).
if [ "$#" -eq 2 ] && [ "$1" = "$DEFAULT_EXEC_ARG1" ] && [ "$2" = "$DEFAULT_EXEC_ARG2" ]; then
  echo "MODO: Ejecución por defecto detectada (CMD del Dockerfile sin overrides)."
  echo "No se realizarán tareas de setup adicionales por run_compiled.sh."
  echo "Ejecutando Flask directamente con: $@"
  exec "$@" # Esto ejecutará "python app.py"
fi

# Si no es el caso anterior, entonces los argumentos de CMD fueron reemplazados.
# Intentamos parsear los argumentos para --user y --password.
echo "MODO: Argumentos de CMD reemplazados. Buscando parámetros de setup (--user, --password)..."

# Parsear argumentos con nombre
# Usamos un bucle while para procesar los argumentos
# Es importante guardar los argumentos originales si algunos no son para setup y deben pasarse a la app
# Por ahora, asumimos que si se pasan --user y --password, esos son los únicos relevantes para setup.
# Otros argumentos podrían ser para la app misma, pero este script se enfoca en user/pass para sed.

# Reiniciamos los argumentos posicionales para el bucle de parseo
set -- "${ARGS_COPY[@]}"

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --user)
      if [[ -n "$2" && "$2" != --* ]]; then
        SETUP_USUARIO="$2"
        INTENTO_SETUP=true
        echo "Parámetro --user detectado: '$SETUP_USUARIO'"
        shift # Quitar --user de la lista de argumentos
        shift # Quitar el valor del usuario de la lista de argumentos
      else
        echo "Error: El parámetro --user requiere un valor." >&2
        # Podríamos salir aquí, o dejar que continúe y falle más adelante si es crítico
        # Por ahora, solo marcamos el intento y rompemos el parseo
        INTENTO_SETUP=true
        break 
      fi
      ;;
    --password)
      if [[ -n "$2" && "$2" != --* ]]; then
        SETUP_CONTRASENYA="$2"
        INTENTO_SETUP=true
        echo "Parámetro --password detectado." # No mostramos la contraseña en logs
        shift # Quitar --password
        shift # Quitar el valor de la contraseña
      else
        echo "Error: El parámetro --password requiere un valor." >&2
        INTENTO_SETUP=true
        break
      fi
      ;;
    *)
      # Argumento no reconocido para el setup. Podría ser un error o un argumento para la app.
      # Por ahora, si vemos argumentos que no son --user/--password, asumimos que no es un setup válido
      # y el script intentará la ejecución por defecto más adelante.
      echo "Argumento desconocido para setup: $1. Se detiene el parseo de setup."
      # IMPORTANTE: Si quieres pasar otros argumentos a tu app *además* de --user/--password,
      # esta lógica necesitaría ser más compleja para recolectar esos argumentos.
      # Por ahora, si hay argumentos no reconocidos, se considera que el setup no es el objetivo principal.
      # Esto es para mantener la compatibilidad con la lógica de "fallback" del script original.
      # Si el objetivo es *solo* `setup` o `default_exec`, entonces esto es un error.
      # Dado el script original, se asume que cualquier cosa que no sea `setup` o `default_cmd` debe intentar `default_cmd`.
      INTENTO_SETUP=true # Se intentó, pero algo más vino
      break # Salir del bucle de parseo
      ;;
  esac
done

# Escenario 2: "Versión compilada" con parámetros de setup --user y --password
if [ "$INTENTO_SETUP" = true ] && [ -n "$SETUP_USUARIO" ] && [ -n "$SETUP_CONTRASENYA" ]; then
  echo "MODO: Ejecución 'compilada' con parámetros de setup --user y --password."
  echo "Realizando acciones de setup con Usuario: '$SETUP_USUARIO'..."

  # Asegurarse que el archivo app.py existe y es modificable
  if [ ! -f "$APP_FILE" ]; then
      echo "Error: El archivo '$APP_FILE' no existe en el directorio actual." >&2
      exit 1
  fi
  if [ ! -w "$APP_FILE" ]; then # Chequeo de permisos de escritura
      echo "Error: No se tienen permisos de escritura sobre '$APP_FILE'." >&2
      # Podríamos intentar `ls -l $APP_FILE` para depurar
      exit 1
  fi

  # Usar delimitadores diferentes en sed (ej. |) si la contraseña puede contener /
  sed -i.bak "s|USERNAME = \"\"|USERNAME = \"$SETUP_USUARIO\"|g" "$APP_FILE"
  sed -i.bak "s|PASSWORD = \"\"|PASSWORD = \"$SETUP_CONTRASENYA\"|g" "$APP_FILE"
  rm -f "${APP_FILE}.bak" # Eliminar backup si todo fue bien

  echo "Setup completado."
  echo "Ahora iniciando Flask con los valores por defecto ($DEFAULT_EXEC_ARG1 $DEFAULT_EXEC_ARG2)..."
  exec "$DEFAULT_EXEC_ARG1" "$DEFAULT_EXEC_ARG2"

# Escenario 3: Se intentó un setup (ej. se pasó --user) pero faltaron parámetros, o hubo argumentos extraños.
elif [ "$INTENTO_SETUP" = true ]; then
  echo "MODO: Intento de setup fallido o incompleto (faltan --user o --password, o argumentos no reconocidos)."
  echo "Usuario detectado: '$SETUP_USUARIO'. Contraseña detectada: $(if [ -n "$SETUP_CONTRASENYA" ]; then echo "Sí"; else echo "No"; fi)"
  echo "Por favor, verifica que se pasen '--user <nombre>' y '--password <contraseña>' correctamente."
  echo "Intentando iniciar Flask con valores por defecto de todas formas..."
  exec "$DEFAULT_EXEC_ARG1" "$DEFAULT_EXEC_ARG2"

else
  # Este caso cubre si se pasaron argumentos que no son "python app.py"
  # y tampoco fueron reconocidos como --user o --password (ya que INTENTO_SETUP sería false).
  # Ejemplo: docker run mi-imagen /bin/bash
  # O si el bucle de parseo no encontró nada y INTENTO_SETUP permaneció false.
  echo "MODO: Argumentos no reconocidos como ejecución por defecto ni como parámetros de setup."
  echo "Argumentos recibidos: ${ARGS_COPY[@]}"
  echo "Intentando iniciar Flask con valores por defecto de todas formas..."
  exec "$DEFAULT_EXEC_ARG1" "$DEFAULT_EXEC_ARG2"
fi

echo "--- run_compiled.sh finalizado (no debería verse si 'exec' funcionó) ---"
