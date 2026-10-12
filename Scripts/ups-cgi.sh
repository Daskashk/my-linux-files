#!/bin/bash

# 1. Definir rutas
PYTHON_SCRIPT="/home/nab/.local/bin/servidor_nut.py"
URL="http://localhost:8000"

# Verificar si el script de python existe
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: No encuentro el servidor en $PYTHON_SCRIPT"
    read -p "Presiona Enter para salir..."
    exit 1
fi

# Verificar si electron está instalado
if ! command -v electron &> /dev/null; then
    echo "Error: El comando 'electron' no está disponible."
    echo "Asegúrate de tenerlo instalado globalmente (npm install -g electron) o usa la ruta completa."
    read -p "Presiona Enter para salir..."
    exit 1
fi

# Función para limpiar todo al cerrar
cleanup() {
    echo "Cerrando aplicación y servidor..."
    # Matar el proceso del servidor usando el PID guardado
    if kill -0 $SERVER_PID 2>/dev/null; then
        kill $SERVER_PID
    fi
    exit 0
}

# Capturar cuando se cierra la ventana (señal EXIT)
trap cleanup EXIT

# 2. Iniciar el servidor Python en segundo plano
echo "Iniciando servidor en $URL..."
python3 "$PYTHON_SCRIPT" &
SERVER_PID=$!

# Esperar un segundo para asegurar que el servidor esté listo
sleep 2

# 3. Abrir Electron (el script se queda "esperando" aquí hasta que cierres la ventana)
# Agregué --disable-gpu-sandbox a veces ayuda en Linux con Electron puro
electron "$URL" --disable-gpu-sandbox

# Cuando el usuario cierra Electron, el script continúa y ejecuta 'cleanup' (gracias al trap)
