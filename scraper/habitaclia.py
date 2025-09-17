import re
from typing import Dict, List
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from utils.locations import location_manager, LocationType


class HabitacliaScraper(BaseScraper):
    """Scraper específico para Habitaclia"""
    
    def __init__(self):
        super().__init__(name="Habitaclia", delay=1.0)
        self.base_url = "https://www.habitaclia.com"
    
    def _check_particular_indicators(self, soup: BeautifulSoup) -> bool:
        """Verificar si el anuncio es de un particular en Habitaclia"""
        # Buscar indicadores específicos de Habitaclia para particulares
        particular_indicators = [
            'span.title:-soup-contains("Particular")',
            '.advertiser-type:-soup-contains("Particular")',
            '.contact-info .particular',
            '[data-qa="contact-type"]:-soup-contains("Particular")'
        ]
        
        for indicator in particular_indicators:
            if soup.select(indicator):
                return True
        
        # Buscar en las secciones de contacto
        contact_sections = soup.select('.contact-section, .advertiser-info, .contact-details')
        for section in contact_sections:
            text = section.get_text().lower()
            if 'particular' in text and ('inmobiliaria' not in text and 'profesional' not in text):
                return True
        
        # Verificar en badges o etiquetas
        badges = soup.select('.badge, .tag, .label')
        for badge in badges:
            if 'particular' in badge.get_text().lower():
                return True
        
        return False
    
    def _extract_listing_data(self, soup: BeautifulSoup) -> Dict:
        """Extraer datos específicos de Habitaclia"""
        data = {}
        
        try:
            # Título - usando selector específico de Habitaclia
            title_element = soup.select_one('h1')
            if title_element:
                data['titulo'] = title_element.get_text().strip()
            else:
                # Fallback a selectores anteriores
                title_selectors = ['h1.property-title', '.listing-title', '.ad-title h1']
                data['titulo'] = ''
                for selector in title_selectors:
                    title = self._extract_text(soup, selector, '')
                    if title:
                        data['titulo'] = title
                        break
            
            # Precio
            price_selectors = ['.price-amount', '.listing-price', '.property-price .amount']
            price_text = ''
            for selector in price_selectors:
                price_text = self._extract_text(soup, selector, '')
                if price_text:
                    break
            data['precio'] = self._extract_price(price_text)
            
            # Ubicación
            location_selectors = ['.property-location', '.listing-location', '.address']
            data['ubicacion'] = ''
            for selector in location_selectors:
                location = self._extract_text(soup, selector, '')
                if location:
                    data['ubicacion'] = location
                    break
            
            # Características - usando estructura específica de Habitaclia
            data['superficie'] = 0
            data['habitaciones'] = 0
            data['banos'] = 0
            
            # Buscar en feature-container específico
            features_container = soup.select_one('ul.feature-container')
            if features_container:
                feature_items = features_container.select('li.feature')
                
                for feature in feature_items:
                    text = feature.get_text().strip()
                    
                    # Superficie (ej: "62 m²")
                    if 'm²' in text or 'm<sup>2</sup>' in str(feature):
                        data['superficie'] = self._extract_surface(text)
                    
                    # Habitaciones (ej: "2 hab.")
                    elif 'hab.' in text:
                        data['habitaciones'] = self._extract_rooms(text)
                    
                    # Baños (ej: "1 baño")
                    elif 'baño' in text:
                        data['banos'] = self._extract_bathrooms(text)
            else:
                # Fallback: Método anterior - Lista de características
                features = soup.select('.features-list li, .property-features li, .characteristics li')
                for feature in features:
                    text = feature.get_text().lower()
                    
                    if 'm²' in text or 'metros' in text:
                        data['superficie'] = self._extract_surface(text)
                    
                    if 'habitacion' in text or 'dormitor' in text:
                        data['habitaciones'] = self._extract_rooms(text)
                    
                    if 'baño' in text:
                        data['banos'] = self._extract_bathrooms(text)
                
                # Método 2: Iconos con texto
                icon_features = soup.select('.feature-item, .property-feature, .icon-feature')
                for feature in icon_features:
                    text = feature.get_text().lower()
                    
                    if 'm²' in text and data['superficie'] == 0:
                        data['superficie'] = self._extract_surface(text)
                    
                    if ('hab' in text or 'dorm' in text) and data['habitaciones'] == 0:
                        data['habitaciones'] = self._extract_rooms(text)
                    
                    if 'baño' in text and data['banos'] == 0:
                        data['banos'] = self._extract_bathrooms(text)
            
            # Teléfono
            data['telefono'] = self._extract_phone(soup)
            
            # Nombre contacto
            contact_selectors = ['.advertiser-name', '.contact-name', '.seller-name']
            data['nombre_contacto'] = ''
            for selector in contact_selectors:
                name = self._extract_text(soup, selector, '')
                if name:
                    data['nombre_contacto'] = name
                    break
            
            # Requiere formulario
            data['requiere_formulario'] = self._requires_form(soup)
            
            # Fecha de publicación
            date_selectors = ['.publication-date', '.listing-date', '.ad-date']
            data['fecha_publicacion'] = ''
            for selector in date_selectors:
                date = self._extract_text(soup, selector, '')
                if date:
                    data['fecha_publicacion'] = date
                    break
            
        except Exception as e:
            self.logger.error(f"Error extrayendo datos de Habitaclia: {e}")
        
        return data
    
    def _extract_surface(self, text: str) -> int:
        """Extraer superficie en m²"""
        try:
            # Buscar patrones como "85 m²", "85m²", "85 metros"
            patterns = [r'(\d+)\s*m²', r'(\d+)\s*metros']
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return int(match.group(1))
            return 0
        except:
            return 0
    
    def _extract_rooms(self, text: str) -> int:
        """Extraer número de habitaciones"""
        try:
            patterns = [r'(\d+)\s*habitacion', r'(\d+)\s*dormitor', r'(\d+)\s*hab', r'(\d+)\s*dorm']
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return int(match.group(1))
            return 0
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
            '.advertiser-phone',
            '[data-qa="phone"]',
            '.contact-info .phone'
        ]
        
        for selector in phone_selectors:
            phone = self._extract_text(soup, selector, '')
            if phone and re.search(r'\d{9}', phone):
                return phone
        
        # Buscar en botones o enlaces de teléfono
        phone_elements = soup.select('button:-soup-contains("teléfono"), a:-soup-contains("teléfono"), .phone-button')
        for element in phone_elements:
            text = element.get_text()
            match = re.search(r'(\d{3}\s?\d{3}\s?\d{3})', text)
            if match:
                return match.group(1).replace(' ', '')
        
        return ''
    
    def _requires_form(self, soup: BeautifulSoup) -> bool:
        """Verificar si requiere formulario para ver contacto"""
        form_indicators = [
            '.contact-form',
            'form[data-qa="contact-form"]',
            'button:-soup-contains("Ver teléfono")',
            'button:-soup-contains("Contactar")',
            '.contact-form-container',
            '.show-phone-form'
        ]
        
        return any(soup.select(indicator) for indicator in form_indicators)
    
    def build_search_url(self, search_params: Dict) -> str:
        """Construir URL de búsqueda para Habitaclia usando el formato específico del portal"""
        # Parámetros base
        location = search_params.get('location', 'madrid')
        page = search_params.get('page', 1)
        
        # Procesar ubicación usando el gestor de ubicaciones
        location_formatted, location_type = location_manager.get_habitaclia_location(location)
        
        # Construir URL base según el tipo de ubicación
        if location_type == LocationType.COMARCA:
            # Para comarcas: /viviendas-en-comarca.htm
            url_base = f"{self.base_url}/viviendas-en-{location_formatted}.htm"
        else:
            # Para ciudades: /viviendas-ciudad.htm
            url_base = f"{self.base_url}/viviendas-{location_formatted}.htm"
        
        # Añadir filtros como parámetros de query si es necesario
        params = []
        
        # Precio
        if search_params.get('min_price'):
            params.append(f"precio_min={search_params['min_price']}")
        
        if search_params.get('max_price'):
            params.append(f"precio_max={search_params['max_price']}")
        
        # Habitaciones
        if search_params.get('min_rooms'):
            params.append(f"habitaciones_min={search_params['min_rooms']}")
        
        if search_params.get('max_rooms'):
            params.append(f"habitaciones_max={search_params['max_rooms']}")
        
        # Superficie
        if search_params.get('min_surface'):
            params.append(f"superficie_min={search_params['min_surface']}")
        
        # Página
        if page > 1:
            params.append(f"page={page}")
        
        # Configuración fija: solo venta (sin parámetro adicional)
        # Habitaclia por defecto muestra venta
        
        # Filtro para particulares
        params.append("anunciante=particular")
        
        # Construir URL final
        if params:
            url = url_base + "?" + "&".join(params)
        else:
            url = url_base
            
        return url
    
    def _extract_listing_links(self, soup: BeautifulSoup) -> List[str]:
        """Extraer enlaces de listados de la página de resultados"""
        links = []
        
        # Selectores para enlaces de anuncios en Habitaclia
        link_selectors = [
            '.listing-item a[href*="/vivienda/"]',
            '.property-card a',
            'article a[href*="/vivienda/"]',
            '.ad-item a[href*="/venta/"], .ad-item a[href*="/alquiler/"]'
        ]
        
        for selector in link_selectors:
            for link in soup.select(selector):
                href = link.get('href')
                if href and isinstance(href, str):
                    if href.startswith('/'):
                        href = self.base_url + href
                    if href not in links and ('/venta/' in href or '/alquiler/' in href):
                        links.append(href)
        
        return links
