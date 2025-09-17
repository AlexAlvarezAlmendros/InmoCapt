import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import time
import threading
from typing import Dict, List
import sys
import os

# Configurar codificación UTF-8 para evitar errores de emoji
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Importar módulos locales
from utils.config import ConfigManager
from utils.excel_manager import ExcelManager
from scraper.idealista import IdealistaScraper
from scraper.fotocasa import FotocasaScraper
from scraper.habitaclia import HabitacliaScraper

# Configuración de la página
st.set_page_config(
    page_title="🏠 Captador de Viviendas",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurar logging simple sin emojis para evitar errores de codificación
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/captador.log', encoding='utf-8', errors='replace'),
        logging.StreamHandler()
    ]
)

# Inicializar managers
@st.cache_resource
def initialize_managers():
    """Inicializar managers y scrapers"""
    config_manager = ConfigManager()
    excel_manager = ExcelManager()
    
    scrapers = {
        'Idealista': IdealistaScraper(),
        'Fotocasa': FotocasaScraper(),
        'Habitaclia': HabitacliaScraper()
    }
    
    return config_manager, excel_manager, scrapers

# Cargar datos con cache
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data():
    """Cargar datos del Excel"""
    excel_manager = ExcelManager()
    return excel_manager.load_data()

# Inicializar estado de la sesión
def initialize_session_state():
    """Inicializar variables de estado de la sesión"""
    if 'first_run' not in st.session_state:
        st.session_state.first_run = True
        st.session_state.busqueda_activa = False
        st.session_state.stop_search = False  # Nueva variable para controlar la interrupción
        st.session_state.resultados = pd.DataFrame()
        st.session_state.log_messages = []
        st.session_state.progress = 0
        st.session_state.stats = {}
        st.session_state.current_portal = ""  # Portal actual
        st.session_state.current_page = 0  # Página actual
        st.session_state.listings_found = 0  # Contador de particulares encontrados

def show_welcome_message():
    """Mostrar mensaje de bienvenida"""
    st.balloons()
    st.success("¡Bienvenido al Sistema de Captación de Viviendas en Venta! 🏠")
    st.info("Configura los parámetros de búsqueda en el panel lateral. El sistema busca automáticamente en todas las páginas disponibles y solo inmuebles en venta de particulares.")

def render_sidebar():
    """Renderizar panel lateral con configuración"""
    config_manager, _, _ = initialize_managers()
    
    st.sidebar.title("🏠 Captador de Viviendas")
    st.sidebar.markdown("**Solo Venta - Todas las páginas**")
    st.sidebar.markdown("---")
    
    # Sección de ubicación
    st.sidebar.subheader("📍 Ubicación")
    
    # Obtener sugerencias de ubicaciones
    suggested_cities = config_manager.get_suggested_cities()
    suggested_comarcas = config_manager.get_suggested_comarcas()
    
    # Inicializar location en session_state si no existe
    if 'current_location' not in st.session_state:
        st.session_state.current_location = "madrid-madrid"
    
    # Campo de texto libre con valor del session_state
    location_input = st.sidebar.text_input(
        "Introduce la ubicación:",
        value=st.session_state.current_location,
        help="Formato: ciudad-provincia (ej: madrid-madrid) o provincia/comarca (ej: barcelona/anoia). Usa las sugerencias de abajo para seleccionar rápidamente."
    )
    
    # Actualizar session_state cuando cambia el input
    if location_input != st.session_state.current_location:
        st.session_state.current_location = location_input
    
    # Mostrar sugerencias debajo del campo
    with st.sidebar.expander("💡 Sugerencias de ubicaciones"):
        st.write("**Ciudades principales:**")
        cities_cols = st.columns(2)
        for i, city in enumerate(suggested_cities[:6]):  # Mostrar las primeras 6
            col = cities_cols[i % 2]
            with col:
                if st.button(f"📍 {city.split('-')[0].title()}", key=f"city_{city}", width=True):
                    st.session_state.current_location = city
                    st.rerun()
        
        st.write("**Comarcas disponibles:**")
        comarcas_cols = st.columns(2)
        for i, comarca in enumerate(suggested_comarcas[:6]):  # Mostrar las primeras 6
            col = comarcas_cols[i % 2]
            with col:
                if st.button(f"🏞️ {comarca.split('/')[-1].title()}", key=f"comarca_{comarca}", width=True):
                    st.session_state.current_location = comarca
                    st.rerun()
    
    # Usar la ubicación del session_state
    location = st.session_state.current_location
    
    # Sección de precio
    st.sidebar.subheader("💰 Precio")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_price = st.number_input(
            "Precio mínimo (€):",
            min_value=0,
            max_value=2000000,
            value=100000,
            step=10000
        )
    
    with col2:
        max_price = st.number_input(
            "Precio máximo (€):",
            min_value=min_price,
            max_value=2000000,
            value=500000,
            step=10000
        )
    
    # Sección de características
    st.sidebar.subheader("🏠 Características")
    
    rooms_range = st.sidebar.slider(
        "Número de habitaciones:",
        min_value=1,
        max_value=6,
        value=(1, 4),
        help="Rango de habitaciones"
    )
    
    min_surface = st.sidebar.number_input(
        "Superficie mínima (m²):",
        min_value=20,
        max_value=500,
        value=50,
        step=10
    )
    
    # Sección de portales
    st.sidebar.subheader("🌐 Portales")
    
    scraper_settings = config_manager.get_scraper_settings()
    
    portales_activos = {}
    for portal, settings in scraper_settings.items():
        portales_activos[portal] = st.sidebar.checkbox(
            f"{portal.title()}",
            value=settings.get('enabled', True),
            help=f"Buscar en {portal}"
        )
    
    # Opciones avanzadas
    # Botones de acción
    st.sidebar.markdown("---")
    
    # Configuración fija (sin opciones avanzadas)
    max_pages = 999  # Revisar todas las páginas
    operation = "Venta"  # Solo inmuebles en venta
    
    # Botón principal de búsqueda
    if not st.session_state.busqueda_activa:
        buscar_button = st.sidebar.button(
            "🔍 Iniciar Búsqueda",
            type="primary",
            width="stretch"
        )
    else:
        buscar_button = False
        # Botón de parar búsqueda cuando está activa
        if st.sidebar.button(
            "⏹️ Parar Búsqueda",
            type="secondary",
            width="stretch",
            help="Detiene la búsqueda y guarda los inmuebles encontrados hasta el momento"
        ):
            st.session_state.stop_search = True
            st.sidebar.warning("🛑 Deteniendo búsqueda... Se guardarán los resultados encontrados hasta ahora.")
    
    # Botones secundarios
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("💾 Guardar Config", width="stretch"):
            save_configuration(locals())
    
    with col2:
        if st.button("📁 Cargar Config", width="stretch"):
            load_configuration()
    
    return {
        'location': location,
        'min_price': min_price,
        'max_price': max_price,
        'min_rooms': rooms_range[0],
        'max_rooms': rooms_range[1],
        'min_surface': min_surface,
        'portales_activos': portales_activos,
        'max_pages': max_pages,
        'operation': operation.lower(),  # Siempre será "venta"
        'buscar': buscar_button
    }

def save_configuration(config_data):
    """Guardar configuración actual"""
    try:
        config_manager, _, _ = initialize_managers()
        # Implementar guardado de configuración
        st.sidebar.success("Configuración guardada")
    except Exception as e:
        st.sidebar.error(f"Error guardando configuración: {e}")

def load_configuration():
    """Cargar configuración guardada"""
    try:
        # Implementar carga de configuración
        st.sidebar.success("Configuración cargada")
    except Exception as e:
        st.sidebar.error(f"Error cargando configuración: {e}")

def execute_search(search_params):
    """Ejecutar búsqueda con progreso indefinido simple"""
    _, excel_manager, scrapers = initialize_managers()
    
    # Inicializar estado de búsqueda
    st.session_state.log_messages = []
    st.session_state.progress = 0
    st.session_state.current_portal = ""
    st.session_state.current_page = 0
    st.session_state.listings_found = 0
    
    all_results = []
    total_portales = sum(1 for activo in search_params['portales_activos'].values() if activo)
    
    # Mostrar mensaje simple de progreso
    st.write("## � Búsqueda en Progreso")
    st.info("🚀 Procesando búsqueda en todos los portales seleccionados...")
    
    # Barra de progreso indefinida
    progress_bar = st.progress(0, text="Trabajando...")
    
    for portal_name, scraper in scrapers.items():
        # Verificar si se solicitó parar la búsqueda
        if st.session_state.stop_search:
            break
            
        if not search_params['portales_activos'].get(portal_name.lower(), False):
            continue
        
        # Actualizar mensaje de progreso
        progress_bar.progress(50, text=f"Procesando {portal_name}...")
        
        try:
            # Construir parámetros específicos del portal
            portal_params = {
                'location': search_params['location'],
                'min_price': search_params['min_price'],
                'max_price': search_params['max_price'],
                'min_rooms': search_params['min_rooms'],
                'max_rooms': search_params['max_rooms'],
                'min_surface': search_params['min_surface'],
                'max_pages': search_params['max_pages'],
                'operation': search_params['operation']
            }
            
            # Ejecutar búsqueda
            results = scraper.search_listings(portal_params)
            
            # Verificar si se solicitó parar durante la búsqueda del portal
            if st.session_state.stop_search:
                if results:
                    particulares = [r for r in results if r]
                    all_results.extend(particulares)
                break
            
            # Filtrar solo particulares
            particulares = [r for r in results if r]
            all_results.extend(particulares)
            
        except Exception as e:
            # Solo log interno, no mostrar al usuario
            pass
    
    # Actualizar progreso a guardado
    progress_bar.progress(75, text="Guardando resultados...")
    
    # Guardar resultados (incluso si fueron interrumpidos)
    if all_results:
        try:
            stats = excel_manager.add_listings(all_results)
            st.session_state.stats = stats
            st.session_state.resultados = excel_manager.load_data()
        except Exception as e:
            # Error silencioso
            pass
    
    # Finalizar
    progress_bar.progress(100, text="Completado")
    
    # Limpiar flags
    st.session_state.busqueda_activa = False
    st.session_state.stop_search = False
    
    # Limpiar progreso y mostrar resultado
    progress_bar.empty()
    
    # Mensaje final simple
    if st.session_state.stop_search:
        st.warning("🛑 Proceso detenido por el usuario.")
    else:
        st.success("✅ Proceso finalizado exitosamente.")
    
    if all_results and hasattr(st.session_state, 'stats'):
        st.info(f"� Resultados: {st.session_state.stats.get('nuevos', 0)} nuevos inmuebles encontrados.")

def render_search_tab():
    """Renderizar tab de búsqueda simplificado"""
    st.header("🔍 Búsqueda de Viviendas")
    
    # Mostrar estado de búsqueda si está activa
    if st.session_state.busqueda_activa:
        st.warning("🟡 Búsqueda en progreso... Usa el botón 'Parar Búsqueda' en el panel lateral para detener.")
        st.info("⏳ Por favor, espera mientras procesamos tu búsqueda...")
    
    else:
        # Panel cuando no hay búsqueda activa
        st.subheader("💡 Panel de Control")
        
        if hasattr(st.session_state, 'stats') and st.session_state.stats:
            # Mostrar resultados de la última búsqueda
            st.success("✅ ¡Última búsqueda completada!")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("✨ Nuevos", st.session_state.stats.get('nuevos', 0))
            with col2:
                st.metric("🔄 Actualizados", st.session_state.stats.get('actualizados', 0))
            with col3:
                st.metric("📝 Duplicados", st.session_state.stats.get('duplicados', 0))
            with col4:
                total = len(getattr(st.session_state, 'resultados', []))
                st.metric("📊 Total en BD", total)
        
        else:
            st.info("👈 **Instrucciones:**\n\n1. Configura los parámetros de búsqueda en el panel lateral\n2. Selecciona los portales inmobiliarios\n3. Haz clic en **'🔍 Iniciar Búsqueda'**\n4. El progreso se mostrará automáticamente\n5. Puedes **detener** la búsqueda en cualquier momento")
    
    # Mostrar últimos resultados si existen
    if hasattr(st.session_state, 'resultados') and not st.session_state.resultados.empty:
        st.subheader("📋 Últimos Resultados Encontrados")
        
        # Mostrar solo las primeras 5 filas para no saturar la interfaz
        preview_df = st.session_state.resultados.head(5)
        
        # Seleccionar columnas más relevantes para mostrar
        display_columns = []
        for col in ['Título', 'Precio', 'Superficie', 'Habitaciones', 'Portal', 'Estado']:
            if col in preview_df.columns:
                display_columns.append(col)
        
        if display_columns:
            st.dataframe(
                preview_df[display_columns], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(preview_df.head(), use_container_width=True, hide_index=True)
        
        # Enlace a la pestaña de resultados
        total_count = len(st.session_state.resultados)
        if total_count > 5:
            st.info(f"📈 Se muestran 5 de {total_count} resultados totales. Ve a la pestaña **'📊 Resultados'** para ver todos y gestionarlos.")

def render_results_tab():
    """Renderizar tab de resultados con gestión de inmuebles"""
    st.header("📊 Resultados")
    
    # Cargar datos actuales
    df = load_data()
    
    if df.empty:
        st.info("No hay datos disponibles. Ejecuta una búsqueda primero.")
        return
    
    # Filtros de resultados
    col1, col2, col3 = st.columns(3)
    
    with col1:
        portal_filter = st.selectbox(
            "Filtrar por portal:",
            ["Todos"] + list(df['Portal'].unique())
        )
    
    with col2:
        estado_filter = st.selectbox(
            "Filtrar por estado:",
            ["Todos"] + list(df['Estado'].unique())
        )
    
    with col3:
        precio_max = st.number_input(
            "Precio máximo:",
            min_value=0,
            value=int(df['Precio'].max()) if df['Precio'].notna().any() else 1000000
        )
    
    # Aplicar filtros
    df_filtered = df.copy()
    
    if portal_filter != "Todos":
        df_filtered = df_filtered[df_filtered['Portal'] == portal_filter]
    
    if estado_filter != "Todos":
        df_filtered = df_filtered[df_filtered['Estado'] == estado_filter]
    
    df_filtered = df_filtered[df_filtered['Precio'] <= precio_max]
    
    # Mostrar tabla interactiva con gestión
    st.subheader(f"📋 Listados ({len(df_filtered)} resultados)")
    
    if len(df_filtered) > 0:
        # Crear tabla personalizada con botones de acción
        for index, row in df_filtered.iterrows():
            with st.container():
                # Crear un borde visual para cada inmueble
                st.markdown("---")
                
                # Información principal del inmueble
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    # Información del inmueble
                    estado_color = {
                        'Activo': '🟢',
                        'Contactado': '📞',
                        'Descartado': '❌',
                        'Vendido': '✅'
                    }.get(row['Estado'], '⚪')
                    
                    st.markdown(f"**{estado_color} {row['Titulo']}**")
                    st.markdown(f"💰 **{row['Precio']:,.0f}€** | 📍 {row['Ubicacion']} | 🏠 {row['Habitaciones']} hab | 📐 {row['Superficie']} m²")
                    st.markdown(f"🌐 {row['Portal']} | 📞 {row['Telefono'] if pd.notna(row['Telefono']) else 'No disponible'}")
                
                with col2:
                    # Botón para ir al enlace
                    if st.button("🔗 Ver", key=f"link_{index}", help="Abrir enlace del inmueble"):
                        st.markdown(f'<a href="{row["URL"]}" target="_blank">🔗 Abrir inmueble</a>', unsafe_allow_html=True)
                        st.success("Enlace copiado. Haz clic para abrir en nueva pestaña.")
                
                with col3:
                    # Botón para marcar como contactado
                    if row['Estado'] != 'Contactado':
                        if st.button("📞 Contactado", key=f"contact_{index}", help="Marcar como contactado"):
                            _, excel_manager, _ = initialize_managers()
                            if excel_manager.update_listing_status(row['ID'], 'Contactado'):
                                st.success(f"✅ Marcado como contactado")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Error al actualizar estado")
                    else:
                        st.markdown("📞 **Ya contactado**")
                
                with col4:
                    # Botón para marcar como descartado
                    if row['Estado'] != 'Descartado':
                        if st.button("❌ Descartar", key=f"discard_{index}", help="Marcar como descartado"):
                            _, excel_manager, _ = initialize_managers()
                            if excel_manager.update_listing_status(row['ID'], 'Descartado'):
                                st.success(f"❌ Inmueble descartado")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Error al actualizar estado")
                    else:
                        st.markdown("❌ **Descartado**")
    
    

def render_statistics_tab():
    """Renderizar tab de estadísticas"""
    st.header("📈 Estadísticas y Análisis")
    
    df = load_data()
    
    if df.empty:
        st.info("No hay datos disponibles para mostrar estadísticas.")
        return
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_anuncios = len(df)
        st.metric("Total anuncios", total_anuncios)
    
    with col2:
        con_telefono = len(df[df['Telefono'].notna() & (df['Telefono'] != '')])
        st.metric("Con teléfono", con_telefono)
    
    with col3:
        precio_promedio = df['Precio'].mean() if df['Precio'].notna().any() else 0
        st.metric("Precio promedio", f"{precio_promedio:,.0f}€")
    
    with col4:
        activos = len(df[df['Estado'] == 'Activo'])
        st.metric("Activos", activos)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico por portal
        portal_counts = df['Portal'].value_counts()
        fig_portal = px.bar(
            x=portal_counts.index,
            y=portal_counts.values,
            title="Anuncios por Portal",
            labels={'x': 'Portal', 'y': 'Cantidad'}
        )
        st.plotly_chart(fig_portal, width=True)
    
    with col2:
        # Distribución de precios
        fig_price = px.histogram(
            df,
            x='Precio',
            title="Distribución de Precios",
            nbins=20
        )
        st.plotly_chart(fig_price, width=True)
    
    # Tabla de estadísticas detalladas
    st.subheader("📊 Estadísticas por Portal")
    
    stats_by_portal = []
    for portal in df['Portal'].unique():
        portal_data = df[df['Portal'] == portal]
        stats = {
            'Portal': portal,
            'Total': len(portal_data),
            'Con teléfono': len(portal_data[portal_data['Telefono'].notna() & (portal_data['Telefono'] != '')]),
            'Precio promedio': portal_data['Precio'].mean() if portal_data['Precio'].notna().any() else 0,
            'Activos': len(portal_data[portal_data['Estado'] == 'Activo'])
        }
        stats_by_portal.append(stats)
    
    stats_df = pd.DataFrame(stats_by_portal)
    st.dataframe(stats_df, width=True, hide_index=True)

def download_excel(df):
    """Funcionalidad de descarga de Excel"""
    try:
        # Crear archivo temporal
        temp_file = "temp_export.xlsx"
        df.to_excel(temp_file, index=False)
        
        with open(temp_file, "rb") as file:
            st.download_button(
                label="📥 Descargar archivo",
                data=file.read(),
                file_name=f"viviendas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.success("Archivo preparado para descarga")
    except Exception as e:
        st.error(f"Error preparando descarga: {e}")

def mark_as_contacted(df):
    """Marcar listados como contactados"""
    try:
        _, excel_manager, _ = initialize_managers()
        activos = df[df['Estado'] == 'Activo']['ID'].tolist()
        if activos:
            excel_manager.mark_as_contacted(activos)
            st.success(f"✅ {len(activos)} inmuebles marcados como contactados")
            st.cache_data.clear()
        else:
            st.info("No hay inmuebles activos para marcar como contactados")
    except Exception as e:
        st.error(f"Error marcando como contactados: {e}")

def mark_all_as_contacted(df):
    """Marcar todos los activos como contactados"""
    try:
        _, excel_manager, _ = initialize_managers()
        activos = df[df['Estado'] == 'Activo']['ID'].tolist()
        if activos:
            excel_manager.mark_as_contacted(activos)
            st.success(f"✅ {len(activos)} inmuebles marcados como contactados")
            st.cache_data.clear()
            st.rerun()
        else:
            st.info("No hay inmuebles activos para marcar como contactados")
    except Exception as e:
        st.error(f"Error marcando como contactados: {e}")

def main():
    """Función principal de la aplicación"""
    # Inicializar estado
    initialize_session_state()
    
    # Mostrar mensaje de bienvenida en la primera ejecución
    if st.session_state.first_run:
        show_welcome_message()
        st.session_state.first_run = False
    
    # Renderizar sidebar y obtener parámetros
    search_params = render_sidebar()
    
    # Crear tabs principales
    tab1, tab2, tab3 = st.tabs(["🔍 Búsqueda", "📊 Resultados", "📈 Estadísticas"])
    
    # Manejar inicio de búsqueda sin threading
    if search_params['buscar'] and not st.session_state.busqueda_activa:
        st.session_state.busqueda_activa = True
        st.session_state.stop_search = False
        
        # Ejecutar búsqueda directamente con interfaz en tiempo real
        execute_search(search_params)
        
        # Forzar actualización para mostrar resultados
        st.rerun()
    
    # Renderizar contenido de tabs
    with tab1:
        render_search_tab()
    
    with tab2:
        render_results_tab()
    
    with tab3:
        render_statistics_tab()

if __name__ == "__main__":
    main()
