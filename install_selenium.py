#!/usr/bin/env python3
"""
Instalador completo para Selenium y ChromeDriver
Para máxima evasión de protecciones anti-bot
"""

import subprocess
import sys
import os
import platform
import requests
import zipfile
from pathlib import Path

def install_selenium():
    """Instalar Selenium"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
        print("✅ Selenium instalado correctamente")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error instalando Selenium")
        return False

def install_webdriver_manager():
    """Instalar WebDriver Manager para manejo automático de drivers"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "webdriver-manager"])
        print("✅ WebDriver Manager instalado correctamente")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error instalando WebDriver Manager")
        return False

def test_selenium_setup():
    """Probar configuración de Selenium"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("🧪 Probando configuración de Selenium...")
        
        # Configurar opciones
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Crear driver con WebDriver Manager
        driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Test básico
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        if "Google" in title:
            print("✅ Selenium configurado y funcionando correctamente")
            print(f"   Título obtenido: {title}")
            return True
        else:
            print("⚠️ Selenium funciona pero respuesta inesperada")
            return False
            
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error probando Selenium: {e}")
        return False

def main():
    """Instalación completa de herramientas anti-bot avanzadas"""
    
    print("🔧 INSTALADOR DE SELENIUM ANTI-BOT")
    print("=" * 60)
    print("Este script instalará:")
    print("   - Selenium WebDriver")
    print("   - WebDriver Manager (manejo automático de ChromeDriver)")
    print("   - Configuración de prueba")
    print()
    
    success_count = 0
    total_steps = 3
    
    # Paso 1: Instalar Selenium
    print("📦 Paso 1: Instalando Selenium...")
    if install_selenium():
        success_count += 1
    
    # Paso 2: Instalar WebDriver Manager
    print("\n📦 Paso 2: Instalando WebDriver Manager...")
    if install_webdriver_manager():
        success_count += 1
    
    # Paso 3: Probar configuración
    print("\n🧪 Paso 3: Probando configuración...")
    if test_selenium_setup():
        success_count += 1
    
    # Resumen
    print("\n" + "=" * 60)
    print(f"✅ Instalación completada: {success_count}/{total_steps} pasos exitosos")
    
    if success_count == total_steps:
        print("🎉 ¡Selenium está listo para evadir anti-bots!")
        print("\n💡 Uso:")
        print("   El sistema usará Selenium automáticamente cuando")
        print("   las técnicas HTTP fallen (como con Idealista)")
        
    elif success_count >= 2:
        print("⚠️ Instalación parcial - puede funcionar")
        print("💡 Si hay problemas, reinstala Chrome y vuelve a ejecutar")
        
    else:
        print("❌ Instalación falló")
        print("💡 Verifica:")
        print("   - Conexión a internet")
        print("   - Google Chrome instalado")
        print("   - Permisos de administrador")

if __name__ == "__main__":
    main()
