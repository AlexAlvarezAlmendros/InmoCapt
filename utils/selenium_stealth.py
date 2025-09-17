#!/usr/bin/env python3
"""
Selenium Stealth Scraper para casos extremos como Idealista
Usa navegador real con técnicas anti-detección avanzadas
"""

import time
import random
import logging
from typing import Optional, Dict
from bs4 import BeautifulSoup

# Suprimir logs innecesarios de Selenium
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurar logging silencioso para Selenium
logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('webdriver_manager').setLevel(logging.CRITICAL)

class SeleniumStealth:
    """Selenium con técnicas stealth para evadir detección"""
    
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def setup_driver(self, headless: bool = False):  # Cambiar default a False para evitar DataDome
        """Configurar WebDriver con máxima evasión anti-DataDome"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = Options()
            
            # Para DataDome, es mejor NO usar headless
            if headless:
                chrome_options.add_argument("--headless=new")
                self.logger.warning("AVISO: Modo headless activado - DataDome puede detectar esto mas facilmente")
            else:
                self.logger.info("Modo visible activado - mejor para evadir DataDome")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Anti-detección avanzada contra DataDome
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Headers más realistas
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--accept-lang=es-ES,es;q=0.9,en;q=0.8")
            chrome_options.add_argument("--accept-encoding=gzip, deflate, br")
            
            # Deshabilitar características detectables por DataDome
            chrome_options.add_argument("--disable-plugins-discovery")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            
            # Evitar detección de canvas y WebGL - MÁS AGRESIVO
            chrome_options.add_argument("--disable-canvas-aa")
            chrome_options.add_argument("--disable-2d-canvas-clip-aa")
            chrome_options.add_argument("--disable-gl-drawing-for-tests")
            chrome_options.add_argument("--disable-accelerated-2d-canvas")
            chrome_options.add_argument("--disable-accelerated-jpeg-decoding")
            chrome_options.add_argument("--disable-accelerated-mjpeg-decode")
            chrome_options.add_argument("--disable-app-list-dismiss-on-blur")
            chrome_options.add_argument("--disable-accelerated-video-decode")
            
            # Configuración de red más realista
            chrome_options.add_argument("--max_old_space_size=4096")
            chrome_options.add_argument("--dns-prefetch-disable")
            
            # NUEVAS TÉCNICAS ANTI-DATADOME
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--no-zygote")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-field-trial-config")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            
            # Simular navegador normal mejor
            chrome_options.add_argument("--enable-features=NetworkService,NetworkServiceLogging")
            chrome_options.add_argument("--force-color-profile=srgb")
            chrome_options.add_argument("--metrics-recording-only")
            chrome_options.add_argument("--use-mock-keychain")
            
            # Prefs adicionales para evadir detección
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 1,  # Cargar imágenes para parecer más humano
                "profile.default_content_setting_values.media_stream": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-extensions")
            
            # Configuración de memoria y rendimiento
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=4096")
            
            # Suprimir logs del ChromeDriver
            chrome_options.add_argument("--log-level=3")  # Solo errores críticos
            chrome_options.add_argument("--silent")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Crear driver con WebDriver Manager (silencioso)
            import os
            os.environ['WDM_LOG_LEVEL'] = '0'  # Suprimir logs de WebDriver Manager
            service = Service(ChromeDriverManager().install(), log_path=os.devnull)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # JavaScript avanzado para evadir DataDome y otros detectores
            stealth_js = """
            // Ocultar webdriver property
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            
            // Simular propiedades de navegador real
            Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            
            // Evitar detección de canvas fingerprinting
            const getContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
                if (contextType === '2d') {
                    const context = getContext.call(this, contextType, ...args);
                    const originalFillText = context.fillText;
                    context.fillText = function(text, x, y, maxWidth) {
                        return originalFillText.call(this, text, x, y, maxWidth);
                    };
                    return context;
                }
                return getContext.call(this, contextType, ...args);
            };
            
            // Simular timezone y configuración regional
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
                value: function() {
                    return {
                        locale: 'es-ES',
                        timeZone: 'Europe/Madrid',
                        hour12: false
                    };
                }
            });
            
            // Evitar detección por timing de eventos
            const originalAddEventListener = EventTarget.prototype.addEventListener;
            EventTarget.prototype.addEventListener = function(type, listener, options) {
                return originalAddEventListener.call(this, type, listener, options);
            };
            """
            
            self.driver.execute_script(stealth_js)
            
            self.logger.info("OK: Selenium WebDriver configurado con tecnicas stealth anti-DataDome")
            return True
            
        except ImportError:
            self.logger.error("ERROR: Selenium no esta instalado. Ejecuta: pip install selenium webdriver-manager")
            return False
        except Exception as e:
            self.logger.error(f"ERROR: Error configurando WebDriver: {str(e)}")
            return False
    
    def human_navigation(self, url: str, wait_time: tuple = (3, 7)) -> Optional[BeautifulSoup]:
        """Navegación que simula comportamiento humano"""
        
        if not self.driver:
            if not self.setup_driver():
                return None
        
        try:
            self.logger.info(f"Navegacion humana a: {url}")
            
            # Paso 1: Ir a página principal primero
            base_url = '/'.join(url.split('/')[:3])
            self.logger.info(f"Paso 1: Visitando página principal: {base_url}")
            
            self.driver.get(base_url)
            self._random_wait(2, 4)
            
            # Simular scroll y movimiento
            self._simulate_human_behavior()
            
            # Paso 2: Navegar a la URL objetivo
            self.logger.info(f"Paso 2: Navegando a URL objetivo")
            self.driver.get(url)
            self._random_wait(*wait_time)
            
            # Obtener contenido inicial
            page_source = self.driver.page_source
            
            # Verificar si estamos en una página de CAPTCHA de DataDome
            if 'captcha-delivery.com' in page_source or 'DataDome' in page_source:
                self.logger.warning("BLOQUEO: Detectado CAPTCHA de DataDome - intentando evasion adicional")
                
                try:
                    # Técnica adicional: simular comportamiento humano más intenso
                    self._simulate_human_behavior()
                    self._random_wait(8, 15)
                    
                    # Verificar si la conexión sigue activa antes del refresh
                    if not self.driver or not self.driver.session_id:
                        self.logger.error("DESCONEXION: Conexion perdida con DataDome - reintentando con nueva sesion")
                        self.close()
                        if not self.setup_driver(headless=False):
                            return None
                        # Reintentar navegación completa
                        self.driver.get(base_url)
                        self._random_wait(5, 8)
                        self.driver.get(url)
                        self._random_wait(10, 18)
                        page_source = self.driver.page_source
                    else:
                        # Intentar refrescar la página
                        self.driver.refresh()
                        self._random_wait(5, 10)
                        page_source = self.driver.page_source
                    
                except Exception as e:
                    self.logger.error(f"DESCONEXION: DataDome cerro conexion: {e}")
                    # Reiniciar completamente
                    self.close()
                    if not self.setup_driver(headless=False):
                        return None
                    # Intentar navegación más lenta
                    self.logger.info("LENTO: Navegacion ultra-lenta para evitar DataDome")
                    self.driver.get(base_url)
                    self._random_wait(10, 15)
                    self._simulate_human_behavior()
                    self.driver.get(url)
                    self._random_wait(15, 25)
                    page_source = self.driver.page_source
                
                # Si aún tenemos CAPTCHA, intentar navegación diferente
                if 'captcha-delivery.com' in page_source:
                    self.logger.warning("🔄 Segundo intento - navegación alternativa")
                    try:
                        # Volver a la página principal
                        self.driver.get(base_url)
                        self._random_wait(5, 8)
                        self._simulate_human_behavior()
                        
                        # Intentar de nuevo la URL objetivo
                        self.driver.get(url)
                        self._random_wait(10, 18)
                        page_source = self.driver.page_source
                    except Exception as e:
                        self.logger.error(f"FALLO: Segundo intento fallo: {e}")
                        return None
            
            # Simular más comportamiento humano después de cargar
            self._simulate_human_behavior()
            
            # Obtener contenido final
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Verificar si la página se cargó correctamente
            if self._validate_page_content(soup, url):
                self.logger.info("OK: Pagina cargada y validada correctamente")
                return soup
            else:
                self.logger.warning("AVISO: Pagina cargada pero contenido sospechoso")
                return soup
                
        except Exception as e:
            self.logger.error(f"ERROR: Error en navegacion humana: {str(e)}")
            return None
    
    def _simulate_human_behavior(self):
        """Simular comportamiento humano en la página"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # Scroll aleatorio
            scroll_positions = [300, 600, 900, 1200]
            for pos in random.sample(scroll_positions, 2):
                self.driver.execute_script(f"window.scrollTo(0, {pos});")
                self._random_wait(0.5, 1.5)
            
            # Volver arriba
            self.driver.execute_script("window.scrollTo(0, 0);")
            self._random_wait(1, 2)
            
            # Simular movimiento de mouse aleatorio
            actions = ActionChains(self.driver)
            for _ in range(random.randint(1, 3)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                actions.move_by_offset(x, y)
                self._random_wait(0.3, 0.8)
            
            actions.perform()
            
        except Exception as e:
            self.logger.debug(f"Error simulando comportamiento: {e}")
    
    def _random_wait(self, min_time: float, max_time: float):
        """Espera aleatoria"""
        wait_time = random.uniform(min_time, max_time)
        time.sleep(wait_time)
    
    def _validate_page_content(self, soup: BeautifulSoup, url: str) -> bool:
        """Validar que el contenido de la página es real"""
        
        # Verificar título
        title = soup.find('title')
        if not title or 'error' in title.get_text().lower():
            return False
        
        # Para Idealista, verificar elementos específicos
        if 'idealista.com' in url:
            # Buscar indicadores de página real
            indicators = [
                soup.find_all('article'),
                soup.find_all(class_='item-info-container'),
                soup.find_all(class_='listing'),
                soup.find(id='listing-cards'),
                soup.find(class_='listings-container')
            ]
            
            return any(len(indicator) > 0 for indicator in indicators if indicator)
        
        # Validación general - página debe tener contenido sustancial
        return len(soup.get_text()) > 5000
    
    def click_button_and_get_content(self, url: str, button_selector: str, result_selector: str, wait_time: tuple = (3, 7)) -> Optional[str]:
        """Hacer clic en un botón y extraer el contenido resultante"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
            
            # Navegar a la página si es necesario
            if not self.driver or self.driver.current_url != url:
                soup = self.human_navigation(url, wait_time)
                if not soup or not self.driver:
                    return None
            
            # Verificar que el driver está disponible
            if not self.driver:
                self.logger.error("❌ Driver no disponible para interacción")
                return None
            
            # Encontrar y hacer clic en el botón
            try:
                # Esperar a que el botón sea clickeable
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
                )
                
                # Simular comportamiento humano antes del clic
                self._simulate_human_behavior()
                
                # Hacer scroll al botón si es necesario
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(random.uniform(0.5, 1.5))
                
                # Hacer clic
                button.click()
                self.logger.info(f"✅ Clic realizado en botón: {button_selector}")
                
                # Esperar a que aparezca el resultado
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, result_selector))
                )
                
                # Esperar un momento adicional para que se cargue completamente
                time.sleep(random.uniform(1, 3))
                
                # Extraer el contenido del elemento resultado
                result_element = self.driver.find_element(By.CSS_SELECTOR, result_selector)
                content = result_element.text.strip()
                
                self.logger.info(f"📞 Contenido extraído: {content}")
                return content
                
            except TimeoutException:
                self.logger.warning(f"⏰ Timeout esperando botón o resultado: {button_selector}")
                return None
            except ElementNotInteractableException:
                self.logger.warning(f"🚫 Botón no interactuable: {button_selector}")
                return None
            except Exception as e:
                self.logger.error(f"❌ Error durante interacción: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error en click_button_and_get_content: {e}")
            return None
    
    def close(self):
        """Cerrar el driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("🔒 Selenium WebDriver cerrado")
            except Exception as e:
                self.logger.warning(f"Warning cerrando driver: {e}")
    
    def __del__(self):
        """Destructor - asegurar que el driver se cierre"""
        self.close()

# Instancia global para reutilizar
selenium_stealth = SeleniumStealth()
