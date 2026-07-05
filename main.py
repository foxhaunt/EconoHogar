#!/usr/bin/env python3
"""
EconoHogar – Lanzador con comprobación de dependencias
"""
import subprocess
import sys

def check_and_install(package):
    try:
        __import__(package)
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
    if not check_and_install("matplotlib"):
        print("⚠️  No se pudo instalar matplotlib. Los gráficos no estarán disponibles.")
    from gastos import EconoHogar
    app = EconoHogar()
    app.mainloop()
