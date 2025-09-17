# 🏠 Sistema de Captación Automática de Viviendas

Sistema web desarrollado con Streamlit que automatiza el proceso de web scraping en portales inmobiliarios (Idealista, Fotocasa y Habitaclia) para identificar y recopilar información de viviendas publicadas exclusivamente por particulares.

## 🚀 Características Principales

- **Interfaz Web Moderna**: Aplicación web intuitiva desarrollada con Streamlit
- **Múltiples Portales**: Soporte para Idealista, Fotocasa y Habitaclia  
- **Detección Automática**: Identificación automática de anuncios de particulares
- **Almacenamiento Excel**: Gestión de datos en archivos Excel actualizables
- **Dashboard Interactivo**: Visualizaciones y estadísticas en tiempo real
- **Configuración Flexible**: Sistema de configuración personalizable
- **Progreso en Tiempo Real**: Seguimiento visual del proceso de búsqueda

## 📋 Requisitos del Sistema

- Python 3.8 o superior
- Windows/Mac/Linux
- Conexión a internet
- 4GB RAM recomendados

## 🛠️ Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/InmoCapt.git
cd InmoCapt
```

### 2. Crear Entorno Virtual (Recomendado)
```bash
# Windows
python -m venv venv
venv\\Scripts\\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la Aplicación
```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📁 Estructura del Proyecto

```
InmoCapt/
├── app.py                 # Aplicación principal Streamlit
├── requirements.txt       # Dependencias del proyecto
├── README.md             # Este archivo
├── scraper/              # Módulos de web scraping
│   ├── __init__.py
│   ├── base_scraper.py   # Clase base para scrapers
│   ├── idealista.py      # Scraper específico para Idealista
│   ├── fotocasa.py       # Scraper específico para Fotocasa
│   └── habitaclia.py     # Scraper específico para Habitaclia
├── utils/                # Utilidades del sistema
│   ├── __init__.py
│   ├── excel_manager.py  # Gestión de archivos Excel
│   └── config.py         # Gestión de configuraciones
├── data/                 # Datos generados
│   └── viviendas.xlsx    # Archivo Excel con resultados
├── config/               # Archivos de configuración
│   └── default.json      # Configuración por defecto
├── logs/                 # Archivos de log
├── .streamlit/           # Configuración de Streamlit
│   └── config.toml
└── Documentacion/        # Documentación del proyecto
    └── documentacionFuncional.md
```

## 🎯 Uso de la Aplicación

### 1. Configuración de Búsqueda

En el panel lateral, configura los parámetros de búsqueda:

- **📍 Ubicación**: Selecciona la ciudad y especifica zonas adicionales
- **💰 Precio**: Define el rango de precios (mínimo y máximo)
- **🏠 Características**: Número de habitaciones y superficie mínima
- **🌐 Portales**: Selecciona qué portales incluir en la búsqueda

### 2. Opciones Avanzadas

- **Máximo páginas por portal**: Limita el número de páginas a procesar
- **Tipo de operación**: Venta o Alquiler

### 3. Ejecutar Búsqueda

1. Haz clic en **"🔍 Iniciar Búsqueda"**
2. Observa el progreso en tiempo real
3. Revisa los mensajes de log durante el proceso

### 4. Visualizar Resultados

#### Tab de Resultados
- Tabla interactiva con todos los listados encontrados
- Filtros por portal, estado y precio
- Opciones de descarga y marcado como contactados

#### Tab de Estadísticas
- Métricas principales del dataset
- Gráficos interactivos por portal y precios
- Estadísticas detalladas por portal

## 📊 Estructura de Datos

Los datos se almacenan en Excel con las siguientes columnas:

| Columna | Descripción |
|---------|-------------|
| ID | Identificador único |
| Portal | Portal de origen (Idealista/Fotocasa/Habitaclia) |
| URL | Enlace al anuncio |
| Titulo | Título del anuncio |
| Precio | Precio en euros |
| Ubicacion | Dirección/zona |
| Superficie | Superficie en m² |
| Habitaciones | Número de habitaciones |
| Banos | Número de baños |
| Telefono | Número de contacto |
| Nombre_Contacto | Nombre del contacto |
| Requiere_Formulario | Si requiere formulario para contactar |
| Fecha_Publicacion | Fecha de publicación del anuncio |
| Fecha_Deteccion | Primera vez detectado por el sistema |
| Ultima_Actualizacion | Última actualización del registro |
| Estado | Estado del anuncio (Activo/Contactado) |
| Notas | Campo libre para observaciones |

## ⚙️ Configuración Avanzada

### Personalizar Configuración

La aplicación utiliza archivos JSON para la configuración:

- `config/default.json`: Configuración por defecto
- `config/user_settings.json`: Configuración personalizada (se crea automáticamente)

### Modificar Delays de Scrapers

En `config/default.json`, ajusta los delays para evitar bloqueos:

```json
"scraper_settings": {
    "idealista": {
        "enabled": true,
        "delay": 2.0,
        "max_retries": 3
    }
}
```

### Añadir Nuevas Ubicaciones

Puedes añadir ciudades y zonas personalizadas en la configuración:

```json
"locations": {
    "suggested_cities": [
        "Madrid", "Barcelona", "Tu_Ciudad"
    ],
    "suggested_zones": {
        "Tu_Ciudad": ["Zona1", "Zona2"]
    }
}
```

## 🔧 Mantenimiento

### Logs del Sistema

Los logs se guardan en `logs/captador.log` e incluyen:
- Errores de conexión
- Resultados de búsquedas
- Cambios en configuración
- Estadísticas de uso

### Backup de Datos

Se recomienda hacer backup periódico del archivo `data/viviendas.xlsx`

### Actualización de Selectores

Si los portales cambian su estructura HTML, será necesario actualizar los selectores en los archivos de scraper correspondientes.

## 🚨 Consideraciones Legales y Éticas

### Términos de Uso
- Respecta los términos de servicio de cada portal
- Usa delays apropiados para no sobrecargar los servidores
- No uses la información obtenida para fines comerciales sin autorización

### Rate Limiting
El sistema incluye delays automáticos entre peticiones:
- Idealista: 2 segundos
- Fotocasa: 1.5 segundos  
- Habitaclia: 1 segundo

## 🐛 Solución de Problemas

### Error: Import "streamlit" could not be resolved
**Solución**: Asegúrate de haber instalado las dependencias:
```bash
pip install -r requirements.txt
```

### Error: No se pueden cargar los datos
**Solución**: Verifica que el directorio `data/` existe y tiene permisos de escritura.

### Error: Timeout en las peticiones
**Solución**: Aumenta los delays en la configuración o verifica tu conexión a internet.

### Los scrapers no encuentran datos
**Posibles causas**:
- Los selectores HTML han cambiado
- Los portales han implementado nuevas medidas anti-scraping
- Problemas de conectividad

## 🔄 Actualizaciones y Mantenimiento

### Actualizar Selectores HTML

Si un portal cambia su estructura, edita los archivos correspondientes:

- `scraper/idealista.py`
- `scraper/fotocasa.py`  
- `scraper/habitaclia.py`

Busca los métodos `_check_particular_indicators()` y `_extract_listing_data()` para actualizar los selectores CSS.

### Añadir Nuevos Portales

Para añadir soporte a un nuevo portal:

1. Crea un nuevo archivo en `scraper/nuevo_portal.py`
2. Hereda de `BaseScraper`
3. Implementa los métodos abstractos requeridos
4. Añade la configuración en `config/default.json`
5. Integra en `app.py`

## 📈 Mejoras Futuras

- [ ] Modo automático con programación de búsquedas
- [ ] Notificaciones por email
- [ ] API REST para integración externa
- [ ] Base de datos SQL opcional
- [ ] Análisis de tendencias de precios
- [ ] Detección de duplicados mejorada
- [ ] Soporte para más portales inmobiliarios

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

Desarrollado con ❤️ para automatizar la búsqueda de viviendas de particulares.

## 📞 Soporte

Si tienes problemas o preguntas:

1. Revisa la documentación
2. Consulta los issues existentes en GitHub
3. Abre un nuevo issue con detalles del problema

---

**⚠️ Disclaimer**: Este software es para uso educativo y personal. Respeta siempre los términos de servicio de los portales web y las leyes locales sobre web scraping.
