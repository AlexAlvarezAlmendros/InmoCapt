#!/usr/bin/env python3
"""
Script para instalar dependencias anti-bot
"""

import subprocess
import sys

def install_package(package):
    """Instalar un paquete usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} instalado correctamente")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Error instalando {package}")
        return False

def main():
    """Instalar todas las dependencias anti-bot"""
    
    packages = [
        "cloudscraper",  # Para evadir Cloudflare
        "fake-useragent",  # Para User-Agents realistas adicionales
        "requests[socks]",  # Para soporte de proxies SOCKS
    ]
    
    print("🔧 Instalando dependencias anti-bot...")
    print("=" * 50)
    
    success_count = 0
    for package in packages:
        print(f"\n📦 Instalando {package}...")
        if install_package(package):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Instalación completada: {success_count}/{len(packages)} paquetes")
    
    if success_count == len(packages):
        print("🎉 Todas las dependencias anti-bot están listas!")
    else:
        print("⚠️ Algunas dependencias fallaron. El sistema básico seguirá funcionando.")

if __name__ == "__main__":
    main()
