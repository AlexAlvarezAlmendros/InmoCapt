@echo off
title InmoCapt - Captador Inmobiliario
cls
echo.
echo ==========================================
echo         INMOCAPT - INICIANDO
echo ==========================================
echo.

REM Cambiar al directorio del proyecto
cd /d "C:\Users\alexc\Documents\GIT\InmoCapt"

echo 🚀 Iniciando InmoCapt desde código fuente...
echo.
echo ⚠️  IMPORTANTE: NO cierres esta ventana
echo    Mantén esta ventana abierta mientras usas la aplicación
echo.

REM Verificar que el entorno virtual existe
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Error: Entorno virtual no encontrado
    echo    Ejecuta primero: python -m venv .venv
    pause
    exit /b 1
)

REM Verificar que app.py existe
if not exist "app.py" (
    echo ❌ Error: app.py no encontrado
    pause
    exit /b 1
)

echo ✅ Entorno virtual encontrado
echo ✅ Archivo app.py encontrado
echo.

REM Crear directorios necesarios
if not exist "logs" mkdir logs
if not exist "data" mkdir data

echo 🌐 Abriendo navegador en: http://localhost:8501
echo.

REM Abrir navegador después de un delay
start "" timeout /t 5 /nobreak >nul ^& start "" "http://localhost:8501"

echo 📊 Cargando interfaz web...
echo    (Esto puede tomar 30-60 segundos la primera vez)
echo.
echo ==========================================

REM Ejecutar con el Python del entorno virtual
.venv\Scripts\python.exe -m streamlit run app.py --server.headless=true --server.port=8501 --server.address=localhost --server.runOnSave=false --browser.gatherUsageStats=false --logger.level=warning

echo.
echo ==========================================
echo ✅ InmoCapt se ha cerrado correctamente
echo.
pause