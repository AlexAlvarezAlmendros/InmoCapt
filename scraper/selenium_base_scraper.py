#!/usr/bin/env python3
"""
Scraper base especializado en Selenium para portales con protección anti-bot fuerte
Optimizado para máximo rendimiento y evasión
"""

import time
import random
import logging
import re
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from utils.selenium_stealth import selenium_stealth

# Configurar logging silencioso para librerías de Selenium
logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('webdriver_manager').setLevel(logging.CRITICAL)

class SeleniumBaseScraper(ABC):
    """Clase base para scrapers que usan Selenium como método principal"""
    
    def __init__(self, name: str, delay: float = 5.0, headless: bool = False):  # Cambiar a False para mejor evasión DataDome
        self.name = name
        self.delay = delay
        self.headless = headless
        self.logger = logging.getLogger(f"selenium.{name}")
        self.session_pages = 0  # Contador de páginas por sesión
        self.max_session_pages = 999999  # Desactivar reinicio automático - mantener sesión activa
        
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """Realizar petición usando Selenium como método principal"""
        # Logging más silencioso - solo para URLs importantes
        if "venta-viviendas" in url and "pagina" not in url:
            self.logger.info(f"Selenium: {url}")
        
        # Gestión de sesión - NO reiniciar automáticamente
        # Comentado para mantener sesión activa sin interrupciones
        # if self.session_pages >= self.max_session_pages:
        #     self.logger.info("🔄 Reiniciando sesión Selenium para evitar detección")
        #     selenium_stealth.close()
        #     self.session_pages = 0
        
        # Configurar driver si es necesario
        if not selenium_stealth.driver:
            if not selenium_stealth.setup_driver(headless=self.headless):
                self.logger.error("ERROR: No se pudo configurar Selenium WebDriver")
                return self._fallback_http_request(url)
        
        try:
            # Usar navegación humana optimizada
            soup = selenium_stealth.human_navigation(url, wait_time=(3, 6))
            
            if soup and self._validate_selenium_content(soup, url):
                self.session_pages += 1
                # Solo log cada 10 páginas para reducir ruido
                if self.session_pages % 10 == 0:
                    self.logger.info(f"Progreso: {self.session_pages} paginas procesadas")
                return soup
            else:
                self.logger.warning("AVISO: Contenido Selenium invalido, intentando HTTP fallback")
                return self._fallback_http_request(url)
                
        except Exception as e:
            self.logger.error(f"ERROR: Error Selenium: {str(e)}")
            return self._fallback_http_request(url)
    
    def _validate_selenium_content(self, soup: BeautifulSoup, url: str) -> bool:
        """Validar que el contenido obtenido por Selenium es válido"""
        
        # Validación básica
        if not soup or len(str(soup)) < 1000:
            return False
        
        # Verificar título
        title = soup.find('title')
        if not title:
            return False
        
        title_text = title.get_text().lower()
        
        # Verificar que no es página de error
        error_indicators = ['error', 'blocked', 'access denied', 'forbidden']
        if any(indicator in title_text for indicator in error_indicators):
            return False
        
        # Validación específica por portal
        return self._validate_portal_content(soup, url)
    
    @abstractmethod
    def _validate_portal_content(self, soup: BeautifulSoup, url: str) -> bool:
        """Validación específica del portal - implementar en cada scraper"""
        pass
    
    def _fallback_http_request(self, url: str) -> Optional[BeautifulSoup]:
        """Fallback a HTTP tradicional si Selenium falla"""
        try:
            from utils.antibot import antibot_manager
            
            self.logger.info("🔄 Fallback a HTTP tradicional")
            response = antibot_manager.make_request(url)
            
            if response and response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Fallback HTTP también falló: {str(e)}")
            return None
    
    def search_listings(self, search_params: Dict) -> List[Dict]:
        """Buscar listados usando Selenium como método principal"""
        results = []
        page = 1
        max_pages = 999  # Revisar todas las páginas disponibles
        total_processed = 0
        total_particulares = 0
        
        self.logger.info(f"INICIO: Iniciando busqueda Selenium en {self.name} - Revisando todas las paginas")
        
        while page <= max_pages:
            # Solo mostrar progreso cada 5 páginas
            if page % 5 == 1 or page <= 3:
                self.logger.info(f"Procesando pagina {page} de {self.name}")
            
            # Construir URL de la página actual
            url = self.build_search_url({**search_params, 'page': page})
            soup = self._make_request(url)
            
            if not soup:
                self.logger.error(f"❌ No se pudo obtener la página {page}")
                break
            
            # Extraer enlaces de listados de esta página
            listings = self._extract_listing_links(soup)
            
            if not listings:
                self.logger.info(f"🏁 No se encontraron más listados en página {page}")
                break
            
            self.logger.info(f"🔍 Encontrados {len(listings)} listados en página {page}")
            
            # Procesar cada listado individual
            page_particulares = 0
            for i, listing_url in enumerate(listings, 1):
                progress_msg = f"Procesando listado {i}/{len(listings)} de página {page}"
                self.logger.debug(f"{progress_msg}: {listing_url}")
                
                listing_data = self.scrape_listing(listing_url)
                if listing_data:
                    results.append(listing_data)
                    page_particulares += 1
                    total_particulares += 1
                    self.logger.info(f"✅ Particular encontrado ({total_particulares} total): {listing_data.get('titulo', 'Sin título')}")
                else:
                    self.logger.debug(f"❌ Descartado (no particular): {listing_url}")
                
                total_processed += 1
                
                # Delay entre listados para evitar detección
                time.sleep(random.uniform(1, 3))
            
            self.logger.info(f"📊 Página {page} completada: {page_particulares} particulares de {len(listings)} listados")
            page += 1
            
            # Delay entre páginas
            time.sleep(random.uniform(3, 6))
        
        self.logger.info(f"🎯 Búsqueda completada en {self.name}: {total_particulares} particulares de {total_processed} listados procesados")
        return results
    
    def scrape_listing(self, url: str) -> Optional[Dict]:
        """Scraper listado individual usando Selenium"""
        self.logger.debug(f"🔍 Analizando detalle con Selenium: {url}")
        
        soup = self._make_request(url)
        if not soup:
            self.logger.warning(f"⚠️ No se pudo cargar la página: {url}")
            return None
        
        # Verificar si es particular antes de extraer datos
        if not self._is_particular(soup):
            self.logger.debug(f"❌ No es particular, saltando: {url}")
            return None
        
        # Si es particular, extraer todos los datos
        self.logger.debug(f"✅ Es particular, extrayendo datos: {url}")
        
        try:
            data = self._extract_listing_data(soup)
            data['url'] = url
            data['portal'] = self.name
            data['method'] = 'selenium'  # Marcar como obtenido por Selenium
            
            # Validar que se extrajeron datos mínimos
            if not data.get('titulo') and not data.get('precio'):
                self.logger.warning(f"⚠️ Datos insuficientes extraídos de: {url}")
                return None
            
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo datos de {url}: {str(e)}")
            return None
    
    @abstractmethod
    def build_search_url(self, params: Dict) -> str:
        """Construir URL de búsqueda - implementar en cada scraper"""
        pass
    
    @abstractmethod
    def _extract_listing_links(self, soup: BeautifulSoup) -> List[str]:
        """Extraer enlaces de listados - implementar en cada scraper"""
        pass
    
    @abstractmethod
    def _is_particular(self, soup: BeautifulSoup) -> bool:
        """Verificar si es particular - implementar en cada scraper"""
        pass
    
    @abstractmethod
    def _extract_listing_data(self, soup: BeautifulSoup) -> Dict:
        """Extraer datos del listado - implementar en cada scraper"""
        pass
    
    def close_session(self):
        """Cerrar sesión Selenium"""
        selenium_stealth.close()
        self.session_pages = 0
        self.logger.info("🔒 Sesión Selenium cerrada")
    
    def __del__(self):
        """Destructor - cerrar sesión automáticamente"""
        try:
            self.close_session()
        except:
            pass
    
    # Métodos helper para compatibilidad con scrapers existentes
    def _extract_text(self, element, selector: str, default: str = "") -> str:
        """Extraer texto de un elemento usando selector CSS"""
        try:
            found = element.select_one(selector)
            return found.get_text(strip=True) if found else default
        except Exception:
            return default
    
    def _extract_price(self, price_text: str) -> int:
        """Extraer precio numérico de texto"""
        try:
            # Eliminar todo excepto números
            numbers = re.findall(r'\d+', price_text.replace('.', '').replace(',', ''))
            if numbers:
                return int(''.join(numbers))
            return 0
        except Exception:
            return 0
    
    def _extract_number(self, text: str) -> int:
        """Extraer número de texto"""
        try:
            numbers = re.findall(r'\d+', text)
            return int(numbers[0]) if numbers else 0
        except Exception:
            return 0
