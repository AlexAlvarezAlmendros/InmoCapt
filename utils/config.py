import json
import os
from typing import Dict, Any, Optional
import logging


class ConfigManager:
    """Gestor de configuraciones para el sistema de captación de viviendas"""
    
    def __init__(self, config_dir: str = 'config'):
        self.config_dir = config_dir
        self.default_config_path = os.path.join(config_dir, 'default.json')
        self.user_config_path = os.path.join(config_dir, 'user_settings.json')
        self.logger = logging.getLogger(__name__)
        
        self._ensure_config_dir()
        self._create_default_config()
    
    def _ensure_config_dir(self):
        """Asegurar que el directorio de configuración existe"""
        os.makedirs(self.config_dir, exist_ok=True)
    
    def _create_default_config(self):
        """Crear archivo de configuración por defecto si no existe"""
        if not os.path.exists(self.default_config_path):
            default_config = {
                "search_params": {
                    "operation": "sale",
                    "property_type": "homes",
                    "location": "madrid-madrid",
                    "min_price": 100000,
                    "max_price": 500000,
                    "min_rooms": 1,
                    "max_rooms": 4,
                    "min_surface": 50,
                    "max_pages": 5
                },
                "scraper_settings": {
                    "idealista": {
                        "enabled": True,
                        "delay": 2.0,
                        "max_retries": 3
                    },
                    "fotocasa": {
                        "enabled": True,
                        "delay": 1.5,
                        "max_retries": 3
                    },
                    "habitaclia": {
                        "enabled": True,
                        "delay": 1.0,
                        "max_retries": 3
                    }
                },
                "ui_settings": {
                    "theme": "light",
                    "auto_refresh": False,
                    "notifications": True,
                    "default_tab": "search"
                },
                "file_settings": {
                    "excel_path": "data/viviendas.xlsx",
                    "backup_enabled": True,
                    "backup_frequency": "daily"
                },
                "locations": {
                    "suggested_cities": [
                        "madrid-madrid",
                        "igualada-barcelona",
                        "manresa-barcelona",
                        "barcelona-barcelona",
                        "valencia-valencia",
                        "sevilla-sevilla",
                        "bilbao-vizcaya",
                        "zaragoza-zaragoza",
                        "malaga-malaga",
                        "girona-girona"
                    ],
                    "suggested_comarcas": [
                        "barcelona/anoia",
                        "barcelona/bages",
                        "barcelona/alt-penedes",
                        "barcelona/baix-penedes",
                        "barcelona/valles-occidental",
                        "barcelona/valles-oriental",
                        "girona/alt-emporda",
                        "girona/baix-emporda"
                    ],
                    "suggested_zones": {
                        "Madrid": [
                            "Centro",
                            "Salamanca",
                            "Chamberí",
                            "Retiro",
                            "Chamartín",
                            "Tetuán",
                            "Moncloa",
                            "Fuencarral"
                        ],
                        "Barcelona": [
                            "Eixample",
                            "Gràcia",
                            "Sarrià-Sant Gervasi",
                            "Les Corts",
                            "Sant Martí",
                            "Ciutat Vella"
                        ]
                    }
                }
            }
            
            self._save_config(default_config, self.default_config_path)
            self.logger.info("Archivo de configuración por defecto creado")
    
    def get_default_config(self) -> Dict[str, Any]:
        """Obtener configuración por defecto"""
        return self._load_config(self.default_config_path)
    
    def get_user_config(self) -> Dict[str, Any]:
        """Obtener configuración del usuario, con fallback a la configuración por defecto"""
        if os.path.exists(self.user_config_path):
            user_config = self._load_config(self.user_config_path)
            default_config = self.get_default_config()
            
            # Fusionar configuraciones (user override default)
            merged_config = self._merge_configs(default_config, user_config)
            return merged_config
        else:
            return self.get_default_config()
    
    def save_user_config(self, config: Dict[str, Any]) -> bool:
        """Guardar configuración del usuario"""
        try:
            self._save_config(config, self.user_config_path)
            self.logger.info("Configuración de usuario guardada")
            return True
        except Exception as e:
            self.logger.error(f"Error guardando configuración de usuario: {e}")
            return False
    
    def _load_config(self, file_path: str) -> Dict[str, Any]:
        """Cargar configuración desde archivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error cargando configuración desde {file_path}: {e}")
            return {}
    
    def _save_config(self, config: Dict[str, Any], file_path: str):
        """Guardar configuración a archivo JSON"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Fusionar configuración de usuario con la por defecto"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get_search_params(self) -> Dict[str, Any]:
        """Obtener parámetros de búsqueda actuales"""
        config = self.get_user_config()
        return config.get('search_params', {})
    
    def save_search_params(self, search_params: Dict[str, Any]) -> bool:
        """Guardar parámetros de búsqueda"""
        config = self.get_user_config()
        config['search_params'] = search_params
        return self.save_user_config(config)
    
    def get_scraper_settings(self, portal: Optional[str] = None) -> Dict[str, Any]:
        """Obtener configuración de scrapers"""
        config = self.get_user_config()
        scraper_settings = config.get('scraper_settings', {})
        
        if portal:
            return scraper_settings.get(portal, {})
        return scraper_settings
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """Obtener configuración de interfaz de usuario"""
        config = self.get_user_config()
        return config.get('ui_settings', {})
    
    def get_file_settings(self) -> Dict[str, Any]:
        """Obtener configuración de archivos"""
        config = self.get_user_config()
        return config.get('file_settings', {})
    
    def get_locations(self) -> Dict[str, Any]:
        """Obtener configuración de ubicaciones"""
        config = self.get_user_config()
        return config.get('locations', {})
    
    def get_suggested_cities(self) -> list:
        """Obtener lista de ciudades sugeridas"""
        locations = self.get_locations()
        return locations.get('suggested_cities', [])
    
    def get_suggested_comarcas(self) -> list:
        """Obtener lista de comarcas sugeridas"""
        locations = self.get_locations()
        return locations.get('suggested_comarcas', [])
    
    def get_suggested_zones(self, city: str) -> list:
        """Obtener zonas sugeridas para una ciudad"""
        locations = self.get_locations()
        zones = locations.get('suggested_zones', {})
        return zones.get(city, [])
    
    def add_custom_location(self, city: str, zones: Optional[list] = None) -> bool:
        """Añadir ubicación personalizada"""
        try:
            config = self.get_user_config()
            locations = config.get('locations', {})
            
            # Añadir ciudad si no existe
            suggested_cities = locations.get('suggested_cities', [])
            if city not in suggested_cities:
                suggested_cities.append(city)
                locations['suggested_cities'] = suggested_cities
            
            # Añadir zonas si se proporcionan
            if zones:
                suggested_zones = locations.get('suggested_zones', {})
                suggested_zones[city] = zones
                locations['suggested_zones'] = suggested_zones
            
            config['locations'] = locations
            return self.save_user_config(config)
            
        except Exception as e:
            self.logger.error(f"Error añadiendo ubicación personalizada: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """Resetear configuración a valores por defecto"""
        try:
            if os.path.exists(self.user_config_path):
                os.remove(self.user_config_path)
            self.logger.info("Configuración reseteada a valores por defecto")
            return True
        except Exception as e:
            self.logger.error(f"Error reseteando configuración: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """Exportar configuración actual a archivo"""
        try:
            config = self.get_user_config()
            self._save_config(config, export_path)
            return True
        except Exception as e:
            self.logger.error(f"Error exportando configuración: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Importar configuración desde archivo"""
        try:
            imported_config = self._load_config(import_path)
            if imported_config:
                return self.save_user_config(imported_config)
            return False
        except Exception as e:
            self.logger.error(f"Error importando configuración: {e}")
            return False
