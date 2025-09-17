import time
import random
import requests
import logging
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from utils.antibot import antibot_manager


class BaseScraper(ABC):
    """Clase base abstracta para todos los scrapers de portales inmobiliarios"""
    
    def __init__(self, name: str, delay: float = 2.0):
        self.name = name
        self.delay = delay
        self.session = requests.Session()
        self.logger = logging.getLogger(f'{__name__}.{self.name}')
        
        # Headers comunes para simular navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
    
    def _make_request(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Realizar petición HTTP con técnicas anti-bot avanzadas"""
        self.logger.info(f"Realizando petición con anti-bot a: {url}")
        
        # Usar el sistema anti-bot
        response = antibot_manager.make_request(url)
        
        if response and response.status_code == 200:
            self.logger.debug(f"✅ Petición exitosa: {response.status_code}")
            return BeautifulSoup(response.content, 'html.parser')
        elif response:
            self.logger.warning(f"❌ Respuesta con código: {response.status_code}")
            
            # Si es 403, intentar técnicas adicionales
            if response.status_code == 403:
                self.logger.info("🛡️ Detectado bloqueo 403, aplicando técnicas avanzadas...")
                return self._handle_403_block(url)
        else:
            self.logger.error(f"❌ No se pudo obtener respuesta de: {url}")
            
        return None
    
    def _handle_403_block(self, url: str) -> Optional[BeautifulSoup]:
        """Manejar específicamente bloqueos 403 con técnicas adicionales"""
        
        # Técnica 1: Delay más largo y nuevo User-Agent
        self.logger.info("Técnica 1: Delay extendido + nuevo User-Agent")
        time.sleep(random.uniform(5, 10))
        
        response = antibot_manager.make_request(url, headers={
            'User-Agent': antibot_manager.get_random_user_agent(),
            'Referer': 'https://www.google.com/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        if response and response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
        
        # Técnica 2: Simular navegación desde la página principal
        self.logger.info("Técnica 2: Navegación desde página principal")
        base_domain = '/'.join(url.split('/')[:3])
        
        # Visitar primero la página principal
        antibot_manager.make_request(base_domain)
        time.sleep(random.uniform(2, 5))
        
        # Luego intentar la URL objetivo con referer
        response = antibot_manager.make_request(url, headers={
            'Referer': base_domain
        })
        
        if response and response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
        
        # Técnica 3: SELENIUM FALLBACK para casos extremos
        self.logger.info("🤖 Técnica 3: Selenium Stealth Fallback")
        return self._try_selenium_fallback(url)
    
    def _try_selenium_fallback(self, url: str) -> Optional[BeautifulSoup]:
        """Usar Selenium como último recurso para casos extremos"""
        try:
            from utils.selenium_stealth import selenium_stealth
            
            self.logger.info("🚀 Iniciando Selenium Stealth para evadir protección avanzada...")
            
            # Usar navegación humana con Selenium
            soup = selenium_stealth.human_navigation(url, wait_time=(5, 10))
            
            if soup:
                self.logger.info("✅ Selenium Stealth exitoso - página obtenida")
                return soup
            else:
                self.logger.error("❌ Selenium Stealth falló")
                return None
                
        except ImportError:
            self.logger.warning("⚠️ Selenium no disponible. Instala con: pip install selenium")
            self.logger.info("💡 También necesitas ChromeDriver: https://chromedriver.chromium.org/")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error con Selenium: {str(e)}")
            return None
    
    def _extract_text(self, element, selector: str, default: str = "") -> str:
        """Extraer texto de un elemento usando selector CSS"""
        try:
            found = element.select_one(selector)
            return found.get_text(strip=True) if found else default
        except Exception as e:
            self.logger.debug(f"Error extrayendo texto con selector {selector}: {e}")
            return default
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extraer precio numérico del texto"""
        try:
            # Limpiar texto y extraer número
            import re
            price_clean = re.sub(r'[^\d,.]', '', price_text)
            price_clean = price_clean.replace(',', '.')
            return float(price_clean) if price_clean else None
        except ValueError:
            return None
    
    def _is_particular(self, soup: BeautifulSoup) -> bool:
        """Verificar si el anuncio es de un particular"""
        return self._check_particular_indicators(soup)
    
    @abstractmethod
    def _check_particular_indicators(self, soup: BeautifulSoup) -> bool:
        """Método abstracto para verificar indicadores específicos de cada portal"""
        pass
    
    @abstractmethod
    def _extract_listing_data(self, soup: BeautifulSoup) -> Dict:
        """Método abstracto para extraer datos específicos de cada portal"""
        pass
    
    @abstractmethod
    def build_search_url(self, search_params: Dict) -> str:
        """Método abstracto para construir URL de búsqueda específica"""
        pass
    
    def search_listings(self, search_params: Dict) -> List[Dict]:
        """Buscar listados basándose en parámetros de búsqueda"""
        results = []
        page = 1
        max_pages = search_params.get('max_pages', 10)
        total_processed = 0
        total_particulares = 0
        
        self.logger.info(f"Iniciando búsqueda en {self.name} - Máximo {max_pages} páginas")
        
        while page <= max_pages:
            self.logger.info(f"Procesando página {page} de {self.name}")
            
            # Construir URL de la página actual
            url = self.build_search_url({**search_params, 'page': page})
            soup = self._make_request(url)
            
            if not soup:
                self.logger.error(f"No se pudo obtener la página {page}")
                break
            
            # Extraer enlaces de listados de esta página
            listings = self._extract_listing_links(soup)
            
            if not listings:
                self.logger.info(f"No se encontraron más listados en página {page}")
                break
            
            self.logger.info(f"Encontrados {len(listings)} listados en página {page}")
            
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
            
            self.logger.info(f"Página {page} completada: {page_particulares} particulares de {len(listings)} listados")
            page += 1
        
        self.logger.info(f"Búsqueda completada en {self.name}: {total_particulares} particulares de {total_processed} listados procesados")
        return results
    
    @abstractmethod
    def _extract_listing_links(self, soup: BeautifulSoup) -> List[str]:
        """Extraer enlaces de listados de la página de resultados"""
        pass
    
    def scrape_listing(self, url: str) -> Optional[Dict]:
        """
        Analizar página de detalle de vivienda.
        Proceso:
        1. Abrir página de detalle
        2. Verificar si el anunciante es particular
        3. Si es particular: extraer datos y retornar
        4. Si no es particular: retornar None (no se guarda)
        """
        self.logger.debug(f"Analizando detalle: {url}")
        
        soup = self._make_request(url)
        if not soup:
            self.logger.warning(f"No se pudo cargar la página: {url}")
            return None
        
        # PASO 1: Verificar si es particular antes de extraer datos
        if not self._is_particular(soup):
            self.logger.debug(f"❌ No es particular, saltando: {url}")
            return None
        
        # PASO 2: Si es particular, extraer todos los datos
        self.logger.debug(f"✅ Es particular, extrayendo datos: {url}")
        
        try:
            data = self._extract_listing_data(soup)
            data['url'] = url
            data['portal'] = self.name
            
            # Validar que se extrajeron datos mínimos
            if not data.get('titulo') and not data.get('precio'):
                self.logger.warning(f"Datos insuficientes extraídos de: {url}")
                return None
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error extrayendo datos de {url}: {str(e)}")
            return None
        
        return data
