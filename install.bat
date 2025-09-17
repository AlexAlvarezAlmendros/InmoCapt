@echo off
echo ===================================
echo  Sistema de Captacion de Viviendas
echo ===================================
echo.

echo Instalando dependencias...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Error: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo.
echo Instalacion completada correctamente!
echo.
echo Para ejecutar la aplicacion:
echo   streamlit run app.py
echo.
pause
