#!/bin/bash

# --- CORRECCIÓN: Asegurar que los binarios de usuario sean visibles ---
export PATH="$HOME/.local/bin:$PATH"

echo "========================================"
echo "  Verificando JupyterLab / Notebook"
echo "========================================"

# Función para instalar paquete Python solo si no está presente
install_if_missing() {
    PACKAGE=$1
    # Verificamos si podemos importar el paquete
    if ! python3 -c "import $PACKAGE" &> /dev/null; then
        echo "Paquete '$PACKAGE' no encontrado. Instalando..."
        # Actualizamos pip primero para evitar advertencias y errores
        python3 -m pip install --user $PACKAGE
    else
        echo "Paquete '$PACKAGE' ya instalado."
    fi
}

# Instala JupyterLab y notebook solo si faltan
install_if_missing jupyterlab
install_if_missing notebook

echo "========================================"
echo "  Configurando Jupyter Notebook Server"
echo "========================================"

# Usar carpeta de usuario actual
JUPYTER_CONFIG_DIR="$HOME/.jupyter"
mkdir -p "$JUPYTER_CONFIG_DIR"

CONFIG_FILE="$JUPYTER_CONFIG_DIR/jupyter_notebook_config.py"

# Generar configuración solo si no existe
if [ ! -f "$CONFIG_FILE" ]; then
    # Usamos python3 -m jupyter en lugar de notebook directo por compatibilidad
    python3 -m jupyter notebook --generate-config
fi

# Añadir configuración para acceso externo si no está
if ! grep -q "c.ServerApp.ip = '0.0.0.0'" "$CONFIG_FILE"; then
cat >> "$CONFIG_FILE" <<EOF
c = get_config()
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.open_browser = False
c.ServerApp.allow_root = True
c.ServerApp.token = ''
c.ServerApp.password = ''
EOF
fi

echo "========================================"
echo "  Iniciando JupyterLab en http://localhost:8888"
echo "========================================"

# Arrancar JupyterLab
# Usamos 'jupyter lab' directamente ahora que el PATH está corregido
exec jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''
