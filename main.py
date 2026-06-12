#!/usr/bin/env python3
"""
EconoHogar – Lanzador con comprobación de dependencias
"""
import subprocess
import sys
import os

def check_and_install(package, import_name=None):
    import_name = import_name or package
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"📦 Instalando {package}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True, text=True
        )
        return result.returncode == 0

if __name__ == "__main__":
    print("🏠 EconoHogar – Iniciando...")
    
    # Comprobar matplotlib
    if not check_and_install("matplotlib"):
        print("⚠️  No se pudo instalar matplotlib. Los gráficos no estarán disponibles.")
    
    # Lanzar la app
    app_path = os.path.join(os.path.dirname(__file__), "gastos.py")
    os.execv(sys.executable, [sys.executable, app_path])
