import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from .selenium_base_scraper import SeleniumBaseScraper
from utils.locations import location_manager, LocationType


class IdealistaScraper(SeleniumBaseScraper):
    """Scraper específico para Idealista usando Selenium como método principal"""
    
    def __init__(self):
        super().__init__(name="Idealista", delay=5.0, headless=False)  # Modo visible para evadir DataDome
        self.base_url = "https://www.idealista.com"
        
        self.logger.info("IdealistaScraper inicializado con Selenium como metodo principal")
        self.logger.info("Modo visible activado - mejor para evadir DataDome")
    
    def _validate_portal_content(self, soup: BeautifulSoup, url: str) -> bool:
        """Validación específica para Idealista con detección de DataDome y redirecciones"""
        try:
            # Detectar bloqueo de DataDome
            title_elem = soup.find('title')
            has_interstitial_title = title_elem and 'interstitial' in title_elem.get_text().lower()
            
            datadome_indicators = [
                has_interstitial_title,
                'datadome.co' in str(soup).lower(),
                'datadome' in str(soup).lower(),
                len(str(soup)) < 5000 and 'blocked' in str(soup).lower(),
                len(str(soup)) < 3000  # Páginas de CAPTCHA suelen ser muy pequeñas
            ]
            
            if any(datadome_indicators):
                self.logger.warning("BLOQUEO: DataDome detectado - se requiere evasion avanzada")
                return False
            
            # Detectar redirección a primera página (fin de resultados)
            if self._is_redirected_to_first_page(soup, url):
                self.logger.info("FIN: Detectada redireccion a primera pagina - no hay mas resultados")
                return False
            
            # Verificar elementos característicos de Idealista
            title = soup.find('title')
            has_idealista_title = title and 'idealista' in title.get_text().lower()
            
            idealista_indicators = [
                has_idealista_title,
                soup.find(class_='main-info__title-main'),
                soup.find(class_='item-info-container'),
                soup.find('article'),
                soup.select('[data-element-id]'),
                'idealista.com' in str(soup),
                soup.find('div', {'id': 'wrapper'}),
                soup.find('div', class_='listing-items')
            ]
            
            valid_content = any(idealista_indicators)
            
            if valid_content:
                content_length = len(str(soup))
                self.logger.info(f"OK: Contenido de Idealista validado - {content_length} caracteres")
            else:
                self.logger.warning("AVISO: Contenido no valido de Idealista detectado")
                
            return valid_content
            
        except Exception as e:
            self.logger.error(f"Error en validación de contenido: {e}")
            return False
    
    def _is_redirected_to_first_page(self, soup: BeautifulSoup, url: str) -> bool:
        """Detectar si Idealista ha redirigido a la primera página por falta de resultados"""
        try:
            # Extraer número de página de la URL solicitada
            if 'pagina-' not in url:
                return False  # Es la primera página (sin sufijo /pagina-X.htm)
                
            page_part = url.split('pagina-')[1].split('.htm')[0]
            try:
                page_num = int(page_part)
                if page_num <= 1:
                    return False  # Es la primera página, no hay redirección
            except ValueError:
                return False
            
            # Verificar contenido del HTML para detectar redirección a página 1
            html_content = str(soup)
            
            # Si la URL actual aparece en el contenido, probablemente no hubo redirección
            if f'pagina-{page_num}.htm' in html_content:
                return False
                
            # CLAVE: Verificar si estamos en la URL base (página 1) cuando solicitamos página > 1
            # La página 1 NO tiene /pagina-1.htm, así que si solicitamos página 2+ pero la URL actual
            # no contiene pagina-X.htm, entonces fuimos redirigidos a página 1
            current_url = str(soup.find('link', {'rel': 'canonical'}))
            if current_url and 'pagina-' not in current_url and page_num > 1:
                self.logger.warning(f"REDIRECCION DETECTADA: URL solicitada página {page_num} pero URL actual es página 1 (sin pagina-X.htm)")
                return True
            
            # Si aparecen indicadores de página 1 pero solicitamos página mayor
            page_1_indicators = [
                # NO buscar 'pagina-1.htm' porque la página 1 no lo tiene
                '"current">1<' in html_content,
                'pagination-current">1<' in html_content,
                'class="current">1' in html_content,
                '>1</span>' in html_content and 'current' in html_content,
                # Buscar que el primer enlace de paginación sea página 2
                'pagina-2.htm' in html_content and not any([
                    f'pagina-{i}.htm' in html_content for i in range(page_num-1, page_num+2) if i > 2
                ])
            ]
            
            if any(page_1_indicators) and page_num > 1:
                self.logger.warning(f"REDIRECCION DETECTADA: Indicadores de página 1 para URL solicitada página {page_num}")
                return True
            
            # Verificar si no existe paginación para la página solicitada
            if page_num > 5:  # Para páginas altas, verificar existencia
                # Buscar enlaces de páginas cercanas
                has_nearby_pages = any([
                    f'pagina-{page_num-2}.htm' in html_content,
                    f'pagina-{page_num-1}.htm' in html_content,
                    f'pagina-{page_num}.htm' in html_content,
                    f'>{page_num}<' in html_content,
                    f'>{page_num-1}<' in html_content
                ])
                
                if not has_nearby_pages:
                    self.logger.warning(f"REDIRECCION DETECTADA: No existen páginas cercanas a {page_num}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error detectando redirección: {e}")
            return False
    
    def _is_particular(self, soup: BeautifulSoup) -> bool:
        """Verificar si el anuncio es de un particular en Idealista"""
        return self._check_particular_indicators(soup)
    
    def _check_particular_indicators(self, soup: BeautifulSoup) -> bool:
        """Verificar si el anuncio es de un particular en Idealista"""
        # Buscar indicadores de "Particular"
        particular_indicators = [
            'div.name:-soup-contains("Particular")',
            'span.particular',
            '.professional-name:-soup-contains("Particular")',
            '[data-test="contact-name"]:-soup-contains("Particular")'
        ]
        
        for indicator in particular_indicators:
            if soup.select(indicator):
                return True
        
        # Buscar en texto completo si no encuentra selectores específicos
        text_content = soup.get_text().lower()
        if 'particular' in text_content and 'profesional' not in text_content:
            return True
            
        return False
    
    def _extract_listing_data(self, soup: BeautifulSoup) -> Dict:
        """Extraer datos específicos de Idealista"""
        data = {}
        
        try:
            # Título - usando el selector específico proporcionado
            title_element = soup.select_one('.shortAdDescription p.ellipsis')
            if title_element:
                data['titulo'] = title_element.get_text().strip()
            else:
                # Fallback al selector anterior
                data['titulo'] = self._extract_text(soup, 'h1.main-info__title-main', '')
            
            # Precio
            price_text = self._extract_text(soup, '.info-data-price span', '')
            data['precio'] = self._extract_price(price_text)
            
            # Ubicación
            data['ubicacion'] = self._extract_text(soup, '.main-info__title-minor', '')
            
            # Superficie y habitaciones - usando info-features específico
            info_features = soup.select_one('.info-features')
            if info_features:
                # Extraer superficie (m²)
                surface_spans = info_features.find_all('span')
                for span in surface_spans:
                    text = span.get_text().strip()
                    if 'm²' in text:
                        data['superficie'] = self._extract_surface(text)
                        break
                else:
                    data['superficie'] = 0
                
                # Extraer habitaciones
                for span in surface_spans:
                    text = span.get_text().strip()
                    if 'hab.' in text:
                        data['habitaciones'] = self._extract_rooms(text)
                        break
                else:
                    data['habitaciones'] = 0
            else:
                # Fallback a selectores anteriores
                surface_text = self._extract_text(soup, '.info-features li:-soup-contains("m²")', '')
                data['superficie'] = self._extract_surface(surface_text)
                
                rooms_text = self._extract_text(soup, '.info-features li:-soup-contains("hab")', '')
                data['habitaciones'] = self._extract_rooms(rooms_text)
            
            # Baños
            bathrooms_text = self._extract_text(soup, '.info-features li:-soup-contains("baño")', '')
            data['banos'] = self._extract_bathrooms(bathrooms_text)
            
            # Teléfono
            telefono_extraido = self._extract_phone(soup)
            data['telefono'] = telefono_extraido
            self.logger.info(f"📞 DEBUG: Teléfono extraído = '{telefono_extraido}' (tipo: {type(telefono_extraido)})")
            
            # Debug adicional para verificar el contenido del diccionario de datos
            self.logger.info(f"📊 DEBUG: data['telefono'] final = '{data.get('telefono', 'NO_SET')}'")
            
            # Nombre contacto
            data['nombre_contacto'] = self._extract_text(soup, '.professional-name', '')
            
            # Requiere formulario
            data['requiere_formulario'] = self._requires_form(soup)
            
            # Fecha de publicación
            data['fecha_publicacion'] = self._extract_text(soup, '.stats-text', '')
            
        except Exception as e:
            self.logger.error(f"Error extrayendo datos de Idealista: {e}")
        
        return data
    
    def scrape_listing(self, url: str) -> Optional[Dict]:
        """
        Sobrescribir método para almacenar URL actual (necesaria para Selenium)
        """
        # Almacenar URL actual para uso en _extract_phone
        self._current_url = url
        
        # Llamar al método padre
        result = super().scrape_listing(url)
        
        # Limpiar URL tras el procesamiento
        self._current_url = ''
        
        return result
    
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
            match = re.search(r'(\d+)\s*hab', text)
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
        """Extraer teléfono de contacto - con clic en botón si es necesario"""
        try:
            self.logger.info("🔍 DEBUG: Iniciando extracción de teléfono")
            
            # Primero verificar si ya hay un teléfono visible
            visible_phone_selectors = [
                '.hidden-contact-phones_text',
                '.contact-phones span',
                '.phone-number',
                '[data-phone]',
                '.contact-info-phone'
            ]
            
            for selector in visible_phone_selectors:
                phone_element = soup.select_one(selector)
                if phone_element:
                    phone_text = phone_element.get_text().strip()
                    self.logger.info(f"🔍 DEBUG: Elemento encontrado con selector '{selector}': '{phone_text}'")
                    if phone_text and 'Ver teléfono' not in phone_text:
                        # Verificar si tiene suficientes dígitos
                        phone_digits = re.sub(r'\D', '', phone_text)
                        if len(phone_digits) >= 9:
                            self.logger.info(f"📞 Teléfono encontrado directamente: {phone_text}")
                            return phone_text
            
            # Si no hay teléfono visible, verificar si hay botón "Ver teléfono"
            button_selector = 'a.see-phones-btn.icon-phone-outline.hidden-contact-phones_link'
            button_element = soup.select_one(button_selector)
            
            if button_element:
                self.logger.info("🔘 Botón 'Ver teléfono' encontrado - usando Selenium para hacer clic")
                
                # Usar Selenium para hacer clic en el botón
                try:
                    from utils.selenium_stealth import selenium_stealth
                    
                    # Obtener la URL actual (necesaria para la navegación)
                    current_url = getattr(self, '_current_url', '')
                    self.logger.info(f"🔍 DEBUG: URL actual para Selenium: '{current_url}'")
                    if not current_url:
                        self.logger.warning("⚠️ URL actual no disponible para interacción con Selenium")
                        return ''
                    
                    # Selectores para el botón y el resultado
                    result_selector = 'a.icon-phone-outline.hidden-contact-phones_formatted-phone._mobilePhone .hidden-contact-phones_text'
                    
                    # Hacer clic y obtener el teléfono
                    self.logger.info("🔍 DEBUG: Llamando a selenium_stealth.click_button_and_get_content")
                    phone_text = selenium_stealth.click_button_and_get_content(
                        url=current_url,
                        button_selector=button_selector,
                        result_selector=result_selector,
                        wait_time=(2, 4)
                    )
                    
                    self.logger.info(f"🔍 DEBUG: Resultado de Selenium: '{phone_text}' (tipo: {type(phone_text)})")
                    if phone_text:
                        # Limpiar espacios y verificar si tiene al menos 9 dígitos
                        phone_digits = re.sub(r'\D', '', phone_text)  # Quitar todo lo que no sea dígito
                        if len(phone_digits) >= 9:
                            self.logger.info(f"📞 Teléfono obtenido tras clic: {phone_text}")
                            self.logger.info(f"🔍 DEBUG: Retornando teléfono: '{phone_text}'")
                            return phone_text
                        else:
                            self.logger.warning(f"⚠️ Teléfono muy corto ({len(phone_digits)} dígitos): '{phone_text}'")
                    else:
                        self.logger.warning(f"⚠️ No se pudo obtener teléfono tras hacer clic. Contenido: '{phone_text}'")
                        
                except ImportError:
                    self.logger.warning("⚠️ Selenium no disponible para hacer clic en botón de teléfono")
                except Exception as e:
                    self.logger.error(f"❌ Error usando Selenium para teléfono: {e}")
            else:
                self.logger.info("🔍 DEBUG: No se encontró botón 'Ver teléfono'")
            
            self.logger.info("ℹ️ No se encontró teléfono disponible - retornando cadena vacía")
            return ''
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo teléfono: {e}")
            return ''
    
    def _requires_form(self, soup: BeautifulSoup) -> bool:
        """Verificar si requiere formulario para ver contacto"""
        form_indicators = [
            'form[data-test="contact-form"]',
            '.contact-form',
            'button:-soup-contains("Ver teléfono")',
            'button:-soup-contains("Mostrar teléfono")'
        ]
        
        return any(soup.select(indicator) for indicator in form_indicators)
    
    def build_search_url(self, params: Dict) -> str:
        """Construir URL de búsqueda para Idealista - Solo venta de viviendas"""
        # Parámetros simplificados
        location = params.get('location', 'madrid')
        page = params.get('page', 1)
        
        # Configuración fija: siempre venta de viviendas
        operation_str = 'venta'
        property_type_str = 'viviendas'
        
        # Procesar ubicación usando el gestor de ubicaciones
        location_formatted, location_type = location_manager.get_idealista_location(location)
        
        # Construir URL base según el tipo de ubicación
        if location_type == LocationType.COMARCA:
            # Para comarcas: /venta-viviendas/provincia/comarca/
            url_base = f"{self.base_url}/{operation_str}-{property_type_str}/{location_formatted}/"
        else:
            # Para ciudades: /venta-viviendas/ciudad-provincia/
            url_base = f"{self.base_url}/{operation_str}-{property_type_str}/{location_formatted}/"
        
        # Construir filtros
        filters = []
        
        # Precio
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        
        if max_price:
            filters.append(f"precio-hasta_{max_price}")
        if min_price:
            filters.append(f"precio-desde_{min_price}")
        
        # Superficie
        min_surface = params.get('min_surface')
        max_surface = params.get('max_surface')
        
        if min_surface:
            filters.append(f"metros-cuadrados-mas-de_{min_surface}")
        if max_surface:
            filters.append(f"metros-cuadrados-menos-de_{max_surface}")
        
        # Habitaciones - Idealista usa rangos específicos
        min_rooms = params.get('min_rooms', 1)
        max_rooms = params.get('max_rooms', 4)
        
        room_filters = []
        for rooms in range(min_rooms, max_rooms + 1):
            if rooms == 1:
                room_filters.append("de-un-dormitorio")
            elif rooms == 2:
                room_filters.append("de-dos-dormitorios")
            elif rooms == 3:
                room_filters.append("de-tres-dormitorios")
            elif rooms >= 4:
                if "de-cuatro-cinco-habitaciones-o-mas" not in room_filters:
                    room_filters.append("de-cuatro-cinco-habitaciones-o-mas")
        
        filters.extend(room_filters)
        
        # Construir URL final
        if filters:
            url = url_base + "con-" + ",".join(filters) + "/"
        else:
            url = url_base
        
        # Agregar página si es mayor a 1 - Formato correcto: /pagina-{num}.htm
        if page > 1:
            url += f"pagina-{page}.htm"
            
        return url
    
    def _extract_listing_links(self, soup: BeautifulSoup) -> List[str]:
        """Extraer enlaces de listados de la página de resultados de Idealista"""
        links = []
        
        try:
            # DEBUG: Guardar HTML para inspección manual
            import os
            debug_file = "debug_idealista_page.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            self.logger.info(f"📁 HTML guardado en {debug_file} para inspección")
            
            # DEBUG: Verificar qué contenido tenemos realmente
            page_title = soup.find('title')
            self.logger.info(f"🔍 Título de página: {page_title.text if page_title else 'No encontrado'}")
            
            # DEBUG: Verificar si hay contenido HTML básico
            body = soup.find('body')
            if body:
                body_text = body.get_text()[:500]  # Primeros 500 caracteres
                self.logger.info(f"📄 Contenido parcial del body: {body_text}")
            else:
                self.logger.warning("⚠️ No se encontró elemento body en la página")
            
            # DEBUG: Buscar diferentes tipos de artículos
            all_articles = soup.find_all('article')
            self.logger.info(f"📋 Total artículos encontrados: {len(all_articles)}")
            
            # Buscar artículos con data-element-id (estructura principal de Idealista)
            articles = soup.select('article[data-element-id]')
            self.logger.info(f"🎯 Artículos con data-element-id: {len(articles)}")
            
            # DEBUG: Si no hay artículos con data-element-id, mostrar estructura
            if not articles and all_articles:
                self.logger.info("🔍 Ejemplos de artículos encontrados:")
                for i, article in enumerate(all_articles[:3]):  # Solo los primeros 3
                    article_str = str(article)[:200]  # Primeros 200 caracteres
                    self.logger.info(f"  Artículo {i+1}: {article_str}")
            
            # DEBUG: Buscar también divs que podrían contener listados
            divs_with_item = soup.select('div.item, div[class*="item"]')
            self.logger.info(f"📦 Divs con 'item' en clase: {len(divs_with_item)}")
            
            # DEBUG: Buscar enlaces con /inmueble/ directamente
            direct_property_links = soup.select('a[href*="/inmueble/"]')
            self.logger.info(f"🔗 Enlaces directos a inmuebles: {len(direct_property_links)}")
            
            for article in articles:
                # Buscar el enlace principal dentro del artículo
                link_elements = article.select('a.item-link')
                
                if link_elements:
                    link_element = link_elements[0]
                    href = link_element.get('href')
                    
                    if href:
                        href_str = str(href)
                        # Construir URL completa si es relativa
                        if href_str.startswith('/'):
                            full_url = self.base_url + href_str
                        else:
                            full_url = href_str
                        
                        links.append(full_url)
                        self.logger.debug(f"Enlace extraído: {full_url}")
                else:
                    # Fallback: buscar cualquier enlace que contenga /inmueble/
                    fallback_links = article.select('a')
                    for fallback_link in fallback_links:
                        href = fallback_link.get('href')
                        if href and '/inmueble/' in str(href):
                            href_str = str(href)
                            full_url = self.base_url + href_str if href_str.startswith('/') else href_str
                            links.append(full_url)
                            self.logger.debug(f"Enlace fallback extraído: {full_url}")
                            break
            
            # Si no encontramos artículos, intentar métodos alternativos
            if not links:
                self.logger.warning("No se encontraron artículos con data-element-id, intentando métodos alternativos")
                
                # Método alternativo: buscar directamente enlaces a inmuebles (CSS corregido)
                direct_links = soup.select('a[href*="/inmueble/"]')  # Añadir comillas
                for link in direct_links:
                    href = link.get('href')
                    if href:
                        href_str = str(href)
                        if href_str not in [l.replace(self.base_url, '') for l in links]:
                            full_url = self.base_url + href_str if href_str.startswith('/') else href_str
                            links.append(full_url)
            
            self.logger.info(f"Total de enlaces extraídos: {len(links)}")
            return links
            
        except Exception as e:
            self.logger.error(f"Error extrayendo enlaces de listados: {str(e)}")
            return []
