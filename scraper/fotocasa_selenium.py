#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper de Fotocasa usando Selenium para contenido dinámico
"""

import time
import re
from typing import Dict, List
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .selenium_base_scraper import SeleniumBaseScraper
from utils.locations import location_manager, LocationType


class FotocasaSeleniumScraper(SeleniumBaseScraper):
    """Scraper de Fotocasa usando Selenium para contenido dinámico"""
    
    def __init__(self):
        super().__init__(name="Fotocasa", delay=2.0)
        self.base_url = "https://www.fotocasa.es"
    
    def _wait_for_content_load(self, driver, timeout=20):
        """Esperar a que el contenido se cargue completamente"""
        try:
            # Esperar a que desaparezcan los elementos skeleton
            WebDriverWait(driver, timeout).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".animate-pulse"))
            )
            
            # Esperar a que aparezcan los enlaces reales
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/vivienda/']"))
            )
            
            # Delay adicional para asegurar que todo esté cargado
            time.sleep(3)
            
        except TimeoutException:
            self.logger.warning("Timeout esperando contenido - continuando con lo que está disponible")
    
    def _extract_listing_links_selenium(self, driver) -> List[str]:
        """Extraer enlaces usando Selenium directamente"""
        links = []
        
        try:
            # Esperar a que el contenido se cargue
            self._wait_for_content_load(driver)
            
            # Buscar todos los enlaces que contengan '/vivienda/'
            elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/vivienda/']")
            
            for element in elements:
                try:
                    href = element.get_attribute('href')
                    if href and '/vivienda/' in href:
                        # Filtrar URLs con parámetros de galería
                        if ('multimedia=image' not in href and 
                            'isGalleryOpen=true' not in href and
                            'isZoomGalleryOpen=true' not in href):
                            
                            # Limpiar parámetros de galería si existen
                            clean_href = self._clean_gallery_params(href)
                            
                            if clean_href not in links:
                                links.append(clean_href)
                                
                except Exception as e:
                    self.logger.debug(f"Error procesando enlace: {e}")
                    continue
            
            # Log de depuración
            self.logger.info(f"Encontrados {len(links)} enlaces únicos en la página")
            
            # Mostrar algunos ejemplos para depuración
            for i, link in enumerate(links[:3]):
                self.logger.debug(f"Enlace {i+1}: {link}")
                
        except Exception as e:
            self.logger.error(f"Error extrayendo enlaces con Selenium: {e}")
        
        return links
    
    def _clean_gallery_params(self, url: str) -> str:
        """Limpiar parámetros de galería de la URL"""
        # Patrón para eliminar parámetros de galería
        patterns_to_remove = [
            r'[&?]multimedia=image',
            r'[&?]isGalleryOpen=true',
            r'[&?]isZoomGalleryOpen=true'
        ]
        
        clean_url = url
        for pattern in patterns_to_remove:
            clean_url = re.sub(pattern, '', clean_url)
        
        # Limpiar & duplicados o que queden al final
        clean_url = re.sub(r'[&?]&', '&', clean_url)
        clean_url = re.sub(r'[&?]$', '', clean_url)
        
        return clean_url
    
    def _extract_listing_links(self, soup: BeautifulSoup) -> List[str]:
        """Método heredado - usar la versión Selenium en su lugar"""
        # Este método se mantiene para compatibilidad pero preferimos el método Selenium
        return []
    
    def search_listings(self, search_params: Dict) -> List[Dict]:
        """Buscar listados usando Selenium para manejar contenido dinámico"""
        all_results = []
        
        # Validar parámetros
        location = search_params.get('location', '').strip()
        if not location:
            self.logger.error("❌ Ubicación requerida para la búsqueda")
            return []
        
        max_pages = search_params.get('max_pages', 3)
        
        self.logger.info(f"🔍 Iniciando búsqueda en {self.name}")
        self.logger.info(f"📍 Ubicación: {location}")
        self.logger.info(f"📄 Páginas máximas: {max_pages}")
        
        driver = None
        try:
            # Inicializar driver
            driver = self._init_driver()
            
            for page in range(1, max_pages + 1):
                self.logger.info(f"📄 Procesando página {page}/{max_pages}")
                self._update_current_page(page)
                
                # Construir URL de búsqueda para la página actual
                search_params_page = search_params.copy()
                search_params_page['page'] = page
                search_url = self.build_search_url(search_params_page)
                
                self.logger.info(f"🌐 URL: {search_url}")
                
                try:
                    # Navegar a la página
                    driver.get(search_url)
                    
                    # Extraer enlaces usando Selenium
                    page_links = self._extract_listing_links_selenium(driver)
                    
                    if not page_links:
                        self.logger.warning(f"⚠️ No se encontraron enlaces en página {page}")
                        if page == 1:
                            # Si no hay enlaces ni en la primera página, hay un problema
                            self.logger.error("❌ No se encontraron enlaces en la primera página - posible bloqueo")
                            break
                        else:
                            # Podríamos haber llegado al final
                            break
                    
                    self.logger.info(f"✅ Encontrados {len(page_links)} enlaces en página {page}")
                    
                    # Procesar cada enlace
                    for i, link in enumerate(page_links, 1):
                        try:
                            self.logger.info(f"🏠 Procesando inmueble {i}/{len(page_links)} de página {page}")
                            
                            # Visitar el enlace
                            driver.get(link)
                            time.sleep(2)  # Esperar carga
                            
                            # Obtener HTML y crear BeautifulSoup
                            html = driver.page_source
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Verificar si es de particular
                            if not self._check_particular_indicators(soup):
                                self.logger.info(f"⏭️ Inmueble {i} no es de particular - omitiendo")
                                continue
                            
                            # Extraer datos
                            data = self._extract_listing_data(soup)
                            data['url'] = link
                            data['portal'] = self.name
                            
                            # Validar datos
                            if self._validate_listing_data(data):
                                all_results.append(data)
                                self.logger.info(f"✅ Inmueble {i} añadido: {data.get('titulo', 'Sin título')[:50]}...")
                            else:
                                self.logger.warning(f"⚠️ Inmueble {i} falló validación")
                                
                        except Exception as e:
                            self.logger.error(f"❌ Error procesando inmueble {i}: {e}")
                            continue
                    
                    # Delay entre páginas
                    if page < max_pages:
                        delay = self._calculate_delay()
                        self.logger.info(f"⏳ Esperando {delay:.1f}s antes de la siguiente página...")
                        time.sleep(delay)
                        
                except Exception as e:
                    self.logger.error(f"❌ Error procesando página {page}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        self.logger.info(f"🎯 Búsqueda completada: {len(all_results)} inmuebles encontrados")
        return all_results
    
    def _check_particular_indicators(self, soup: BeautifulSoup) -> bool:
        """Verificar si el anuncio es de un particular en Fotocasa"""
        # Buscar indicadores específicos de Fotocasa para particulares
        particular_indicators = [
            'span.re-FormContactDetailAside-particularLabel:-soup-contains("particular")',
            '.particular-label',
            '.contact-type:-soup-contains("particular")',
            '[data-testid="contact-type"]:-soup-contains("particular")'
        ]
        
        for indicator in particular_indicators:
            if soup.select(indicator):
                return True
        
        # Buscar en el texto del contacto
        contact_sections = soup.select('.contact-info, .contact-section, .advertiser-info')
        for section in contact_sections:
            text = section.get_text().lower()
            if 'particular' in text and ('inmobiliaria' not in text and 'agencia' not in text):
                return True
        
        return False
    
    def _extract_listing_data(self, soup: BeautifulSoup) -> Dict:
        """Extraer datos específicos de Fotocasa"""
        data = {}
        
        try:
            # Título - usando selector específico
            title_element = soup.select_one('h1.re-DetailHeader-propertyTitle')
            if title_element:
                data['titulo'] = title_element.get_text().strip()
            else:
                data['titulo'] = ''
            
            # Precio
            price_text = self._extract_text(soup, '.re-DetailHeader-price', '')
            data['precio'] = self._extract_price(price_text)
            
            # Ubicación
            data['ubicacion'] = self._extract_text(soup, '.re-DetailHeader-locationText', '')
            
            # Características principales - usando re-DetailHeader-features específico
            features_container = soup.select_one('ul.re-DetailHeader-features')
            
            data['superficie'] = 0
            data['habitaciones'] = 0
            data['banos'] = 0
            
            if features_container:
                # Buscar específicamente habitaciones
                rooms_item = features_container.select_one('li.re-DetailHeader-featuresItem.re-DetailHeader-rooms')
                if rooms_item:
                    rooms_span = rooms_item.select_one('span:last-child')
                    if rooms_span:
                        rooms_text = rooms_span.get_text()
                        data['habitaciones'] = self._extract_rooms(rooms_text)
                
                # Buscar superficie
                surface_item = features_container.select_one('li.re-DetailHeader-featuresItem.re-DetailHeader-surface')
                if surface_item:
                    surface_span = surface_item.select_one('span:last-child')
                    if surface_span:
                        surface_text = surface_span.get_text()
                        data['superficie'] = self._extract_surface(surface_text)
                
                # Buscar baños
                bathrooms_item = features_container.select_one('li.re-DetailHeader-featuresItem.re-DetailHeader-bathrooms')
                if bathrooms_item:
                    bathrooms_span = bathrooms_item.select_one('span:last-child')
                    if bathrooms_span:
                        bathrooms_text = bathrooms_span.get_text()
                        data['banos'] = self._extract_bathrooms(bathrooms_text)
            else:
                # Fallback a método anterior
                features = soup.select('.re-DetailFeaturesList-feature')
                
                for feature in features:
                    text = feature.get_text().lower()
                    
                    # Superficie
                    if 'm²' in text or 'metros' in text:
                        data['superficie'] = self._extract_surface(text)
                    
                    # Habitaciones
                    if 'habitacion' in text or 'dormitor' in text:
                        data['habitaciones'] = self._extract_rooms(text)
                    
                    # Baños
                    if 'baño' in text:
                        data['banos'] = self._extract_bathrooms(text)
            
            # Teléfono
            data['telefono'] = self._extract_phone(soup)
            
            # Nombre contacto
            data['nombre_contacto'] = self._extract_text(soup, '.advertiser-name, .contact-name', '')
            
            # Requiere formulario
            data['requiere_formulario'] = self._requires_form(soup)
            
            # Fecha de publicación
            data['fecha_publicacion'] = self._extract_text(soup, '.re-DetailHeader-dates', '')
            
        except Exception as e:
            self.logger.error(f"Error extrayendo datos de Fotocasa: {e}")
        
        return data
    
    def _extract_surface(self, text: str) -> int:
        """Extraer superficie en m²"""
        try:
            match = re.search(r'(\d+)\s*m²', text)
            return int(match.group(1)) if match else 0
        except:
            return 0
    
    def _extract_rooms(self, text: str) -> int:
        """Extraer número de habitaciones"""
        try:
            match = re.search(r'(\d+)\s*(?:habitacion|dormitor)', text)
            return int(match.group(1)) if match else 0
        except:
            return 0
    
    def _extract_bathrooms(self, text: str) -> int:
        """Extraer número de baños"""
        try:
            match = re.search(r'(\d+)\s*baño', text)
            return int(match.group(1)) if match else 0
        except:
            return 0
    
    def _extract_phone(self, soup: BeautifulSoup) -> str:
        """Extraer teléfono de contacto"""
        # Buscar teléfono en diferentes ubicaciones
        phone_selectors = [
            '.contact-phone',
            '.phone-number',
            '[data-testid="phone"]',
            '.re-ContactPhone-number'
        ]
        
        for selector in phone_selectors:
            phone = self._extract_text(soup, selector, '')
            if phone and re.search(r'\d{9}', phone):
                return phone
        
        # Buscar en texto de botones o enlaces de teléfono
        phone_buttons = soup.select('button:-soup-contains("teléfono"), a:-soup-contains("teléfono")')
        for button in phone_buttons:
            text = button.get_text()
            match = re.search(r'(\d{3}\s?\d{3}\s?\d{3})', text)
            if match:
                return match.group(1).replace(' ', '')
        
        return ''
    
    def _requires_form(self, soup: BeautifulSoup) -> bool:
        """Verificar si requiere formulario para ver contacto"""
        form_indicators = [
            '.contact-form',
            'form[data-testid="contact-form"]',
            'button:-soup-contains("Ver teléfono")',
            'button:-soup-contains("Contactar")',
            '.re-ContactForm'
        ]
        
        return any(soup.select(indicator) for indicator in form_indicators)
    
    def build_search_url(self, search_params: Dict) -> str:
        """Construir URL de búsqueda para Fotocasa - Solo venta de viviendas"""
        # Parámetros simplificados
        location = search_params.get('location', 'madrid')
        page = search_params.get('page', 1)
        
        # Configuración fija: siempre comprar viviendas
        operation_str = 'comprar'
        
        # Procesar ubicación usando el gestor de ubicaciones
        location_formatted, location_type = location_manager.get_fotocasa_location(location)
        
        # Construir URL base según el tipo de ubicación
        if location_type == LocationType.COMARCA:
            # Para comarcas: /es/comprar/viviendas/provincia-provincia/comarca/l
            url_base = f"{self.base_url}/es/{operation_str}/viviendas/{location_formatted}/l"
        else:
            # Para ciudades: /es/comprar/viviendas/ciudad/todas-las-zonas/l
            url_base = f"{self.base_url}/es/{operation_str}/viviendas/{location_formatted}/todas-las-zonas/l"
        
        # Añadir parámetros de filtro si es necesario
        params = []
        
        # Precio
        if search_params.get('min_price'):
            params.append(f"precioDesde={search_params['min_price']}")
        
        if search_params.get('max_price'):
            params.append(f"precioHasta={search_params['max_price']}")
        
        # Habitaciones
        if search_params.get('min_rooms'):
            params.append(f"dormitoriosDesde={search_params['min_rooms']}")
        
        if search_params.get('max_rooms'):
            params.append(f"dormitoriosHasta={search_params['max_rooms']}")
        
        # Superficie
        if search_params.get('min_surface'):
            params.append(f"superficieDesde={search_params['min_surface']}")
        
        # Página
        if page > 1:
            params.append(f"pagina={page}")
        
        # Filtro para particulares
        params.append("tipoAnunciante=particular")
        
        # Construir URL final
        if params:
            url = url_base + "?" + "&".join(params)
        else:
            url = url_base
            
        return url
