#!/usr/bin/env python3
"""
Utilidades para evadir protecciones anti-bot
Incluye rotación de User-Agents, headers realistas, delays aleatorios, etc.
"""

import random
import time
import json
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class AntiBotManager:
    """Gestor de técnicas anti-detección para web scraping"""
    
    def __init__(self):
        self.user_agents = [
            # Chrome en Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            
            # Firefox en Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
            
            # Edge en Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46',
            
            # Chrome en Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        ]
        
        self.accept_languages = [
            'es-ES,es;q=0.9,en;q=0.8',
            'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'es,en-US;q=0.7,en;q=0.3',
            'es-ES,es;q=0.9,ca;q=0.8,en;q=0.7',
        ]
        
        self.session = None
        self.last_request_time = 0
        self.min_delay = 3.0  # Delay más largo para Idealista
        self.max_delay = 8.0  # Delay máximo aumentado
        
    def get_random_user_agent(self) -> str:
        """Obtener un User-Agent aleatorio"""
        return random.choice(self.user_agents)
    
    def get_realistic_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Generar headers realistas que imiten un navegador real"""
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': random.choice(self.accept_languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none' if not referer else 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        if referer:
            headers['Referer'] = referer
            
        return headers
    
    def apply_random_delay(self):
        """Aplicar delay aleatorio entre requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calcular delay necesario
        min_wait = self.min_delay
        if time_since_last < min_wait:
            additional_delay = min_wait - time_since_last
            total_delay = additional_delay + random.uniform(0, self.max_delay - self.min_delay)
            time.sleep(total_delay)
        
        self.last_request_time = time.time()
    
    def create_session(self) -> requests.Session:
        """Crear sesión con configuración optimizada anti-detección"""
        if self.session:
            return self.session
            
        session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers por defecto
        session.headers.update(self.get_realistic_headers())
        
        self.session = session
        return session
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Realizar request con todas las técnicas anti-detección"""
        
        # Aplicar delay
        self.apply_random_delay()
        
        # Crear/obtener sesión
        session = self.create_session()
        
        # Actualizar headers para este request
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        # Merge con headers realistas
        realistic_headers = self.get_realistic_headers()
        realistic_headers.update(kwargs['headers'])
        kwargs['headers'] = realistic_headers
        
        # Configurar timeout
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30
        
        try:
            response = session.request(method, url, **kwargs)
            
            # Verificar si la respuesta indica bloqueo
            if response.status_code == 403:
                # Intentar con cloudscraper si está disponible
                return self._try_cloudscraper(url, method, **kwargs)
            
            return response
            
        except Exception as e:
            print(f"Error en request normal: {e}")
            # Intentar con cloudscraper como fallback
            return self._try_cloudscraper(url, method, **kwargs)
    
    def _try_cloudscraper(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Intentar request con cloudscraper para evadir Cloudflare"""
        try:
            import cloudscraper
            
            # Crear scraper con configuración más agresiva
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                },
                debug=False,
                delay=10,  # Delay más largo
                captcha={
                    'provider': 'return_response'
                }
            )
            
            # Aplicar delay también aquí
            self.apply_random_delay()
            
            # Headers adicionales para cloudscraper
            scraper_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            }
            
            if 'headers' in kwargs:
                scraper_headers.update(kwargs['headers'])
            kwargs['headers'] = scraper_headers
            
            response = scraper.request(method, url, **kwargs)
            print(f"Cloudscraper response: {response.status_code}")
            
            return response
            
        except ImportError:
            print("cloudscraper no está instalado. Instálalo con: pip install cloudscraper")
            return None
        except Exception as e:
            print(f"Error con cloudscraper: {e}")
            # Intentar técnica manual adicional
            return self._try_manual_bypass(url, method, **kwargs)
    
    def _try_manual_bypass(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Técnica manual adicional para evadir bloqueos"""
        try:
            import time
            
            # Crear nueva sesión completamente limpia
            session = requests.Session()
            
            # Headers que imitan completamente un navegador Chrome real
            ultra_realistic_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'keep-alive',
                'DNT': '1',
            }
            
            # Simular comportamiento humano más realista
            base_domain = '/'.join(url.split('/')[:3])
            
            # Paso 1: Visitar página principal con delay realista
            print("🌐 Visitando página principal...")
            session.get(base_domain, headers=ultra_realistic_headers, timeout=30)
            time.sleep(random.uniform(2, 4))
            
            # Paso 2: Simular navegación gradual
            print("🔍 Simulando navegación...")
            ultra_realistic_headers['Referer'] = base_domain
            ultra_realistic_headers['Sec-Fetch-Site'] = 'same-origin'
            
            time.sleep(random.uniform(1, 3))
            
            # Paso 3: Request final con toda la cadena de navegación
            response = session.request(method, url, headers=ultra_realistic_headers, timeout=30)
            print(f"Manual bypass response: {response.status_code}")
            
            return response
            
        except Exception as e:
            print(f"Error en bypass manual: {e}")
            return None

# Instancia global para reutilizar
antibot_manager = AntiBotManager()
