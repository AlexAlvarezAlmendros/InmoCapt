import re
from typing import Dict, List
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from utils.locations import location_manager, LocationType


class FotocasaScraper(BaseScraper):
    """Scraper específico para Fotocasa"""
    
    def __init__(self):
        super().__init__(name="Fotocasa", delay=1.5)
        self.base_url = "https://www.fotocasa.es"
    
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
    
    def _extract_listing_links(self, soup: BeautifulSoup) -> List[str]:
        """Extraer enlaces de listados de la página de resultados"""
        links = []
        
        # Selectores para enlaces de anuncios en Fotocasa
        link_selectors = [
            '.re-SearchResult a[href*="/vivienda/"]',
            '.re-SearchResult-item a',
            'article a[href*="/vivienda/"]',
            '.listing-item a'
        ]
        
        for selector in link_selectors:
            for link in soup.select(selector):
                href = link.get('href')
                if href and isinstance(href, str):
                    if href.startswith('/'):
                        href = self.base_url + href
                    if href not in links and '/vivienda/' in href:
                        links.append(href)
        
        return links
