"""
Sistema de gestión de ubicaciones para diferentes portales inmobiliarios
"""

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum


class LocationType(Enum):
    """Tipos de ubicación para Idealista"""
    CITY = "city"           # ciudad-provincia
    COMARCA = "comarca"     # provincia/comarca
    PROVINCE = "province"   # provincia sola


class LocationManager:
    """Gestor de ubicaciones para los diferentes portales"""
    
    def __init__(self):
        # Mapeo de ciudades para Idealista
        self.idealista_cities = {
            # Barcelona provincia
            "igualada": "igualada-barcelona",
            "manresa": "manresa-barcelona", 
            "barcelona": "barcelona-barcelona",
            "sabadell": "sabadell-barcelona",
            "terrassa": "terrassa-barcelona",
            "badalona": "badalona-barcelona",
            "granollers": "granollers-barcelona",
            "vic": "vic-barcelona",
            "vilanova": "vilanova-i-la-geltru-barcelona",
            "abrera": "abrera-barcelona",
            "piera": "piera-barcelona",
            "capellades": "capellades-barcelona",
            
            # Girona provincia
            "girona": "girona-girona",
            "figueres": "figueres-girona",
            "olot": "olot-girona",
            "blanes": "blanes-girona",
            "lloret": "lloret-de-mar-girona",
            
            # Tarragona provincia
            "tarragona": "tarragona-tarragona",
            "reus": "reus-tarragona",
            "tortosa": "tortosa-tarragona",
            
            # Lleida provincia
            "lleida": "lleida-lleida",
            "balaguer": "balaguer-lleida",
            
            # Madrid
            "madrid": "madrid-madrid",
            "alcala": "alcala-de-henares-madrid",
            "getafe": "getafe-madrid",
            "leganes": "leganes-madrid",
            "fuenlabrada": "fuenlabrada-madrid",
            "mostoles": "mostoles-madrid",
            
            # Valencia
            "valencia": "valencia-valencia",
            "alicante": "alicante-alicante",
            "castellon": "castellon-de-la-plana-castellon",
        }
        
        # Mapeo de ciudades para Habitaclia (formato simple)
        self.habitaclia_cities = {
            "igualada": "igualada",
            "manresa": "manresa",
            "barcelona": "barcelona",
            "sabadell": "sabadell",
            "terrassa": "terrassa",
            "badalona": "badalona",
            "granollers": "granollers",
            "vic": "vic",
            "vilanova": "vilanova-i-la-geltru",
            "abrera": "abrera",
            "piera": "piera",
            "capellades": "capellades",
            "girona": "girona",
            "figueres": "figueres",
            "madrid": "madrid",
            "valencia": "valencia",
            "sevilla": "sevilla",
            "bilbao": "bilbao"
        }
        
        self.idealista_comarcas = {
            # Barcelona provincia
            "barcelona": {
                "anoia": "barcelona/anoia",
                "bages": "barcelona/bages", 
                "alt-penedes": "barcelona/alt-penedes",
                "baix-penedes": "barcelona/baix-penedes",
                "garraf": "barcelona/garraf",
                "barcelones": "barcelona/barcelones",
                "valles-occidental": "barcelona/valles-occidental",
                "valles-oriental": "barcelona/valles-oriental",
                "maresme": "barcelona/maresme",
                "osona": "barcelona/osona"
            },
            
            # Girona provincia
            "girona": {
                "alt-emporda": "girona/alt-emporda",
                "baix-emporda": "girona/baix-emporda",
                "garrotxa": "girona/garrotxa",
                "girones": "girona/girones",
                "selva": "girona/selva"
            },
            
            # Tarragona provincia
            "tarragona": {
                "alt-camp": "tarragona/alt-camp",
                "baix-camp": "tarragona/baix-camp",
                "tarragonès": "tarragona/tarragonès"
            },
            
            # Lleida provincia
            "lleida": {
                "segria": "lleida/segria",
                "urgell": "lleida/urgell"
            }
        }
        
        # Mapeo de ciudades para Fotocasa
        self.fotocasa_cities = {
            "igualada": "igualada",
            "manresa": "manresa",
            "barcelona": "barcelona-capital",
            "sabadell": "sabadell",
            "terrassa": "terrassa",
            "badalona": "badalona",
            "granollers": "granollers",
            "vic": "vic",
            "vilanova": "vilanova-i-la-geltru",
            "abrera": "abrera",
            "piera": "piera",
            "capellades": "capellades",
            "girona": "girona",
            "figueres": "figueres",
            "madrid": "madrid-capital",
            "valencia": "valencia-capital",
            "sevilla": "sevilla-capital",
            "bilbao": "bilbao"
        }
        
        # Mapeo de comarcas para Fotocasa (provincia-provincia/comarca)
        self.fotocasa_comarcas = {
            # Barcelona provincia
            "anoia": "barcelona-provincia/anoia",
            "bages": "barcelona-provincia/bages",
            "alt-penedes": "barcelona-provincia/alt-penedes",
            "baix-penedes": "barcelona-provincia/baix-penedes",
            "garraf": "barcelona-provincia/garraf",
            "barcelones": "barcelona-provincia/barcelones",
            "valles-occidental": "barcelona-provincia/valles-occidental",
            "valles-oriental": "barcelona-provincia/valles-oriental",
            "maresme": "barcelona-provincia/maresme",
            "osona": "barcelona-provincia/osona",
            
            # Girona provincia
            "alt-emporda": "girona-provincia/alt-emporda",
            "baix-emporda": "girona-provincia/baix-emporda",
            "garrotxa": "girona-provincia/garrotxa",
            "girones": "girona-provincia/girones",
            "selva": "girona-provincia/selva",
            
            # Tarragona provincia
            "alt-camp": "tarragona-provincia/alt-camp",
            "baix-camp": "tarragona-provincia/baix-camp",
            "tarragonès": "tarragona-provincia/tarragonès",
            
            # Lleida provincia
            "segria": "lleida-provincia/segria",
            "urgell": "lleida-provincia/urgell"
        }
        
        # Mapeo de comarcas para Habitaclia (formato con guión bajo)
        self.habitaclia_comarcas = {
            "anoia": "anoia",
            "bages": "bages",
            "alt-penedes": "alt_penedes", 
            "baix-penedes": "baix_penedes",
            "garraf": "garraf",
            "barcelones": "barcelones",
            "valles-occidental": "valles_occidental",
            "valles-oriental": "valles_oriental",
            "maresme": "maresme",
            "osona": "osona",
            "alt-emporda": "alt_emporda",
            "baix-emporda": "baix_emporda",
            "garrotxa": "garrotxa",
            "girones": "girones",
            "selva": "selva"
        }
    
    def get_idealista_location(self, location: str) -> Tuple[str, LocationType]:
        """
        Convertir ubicación a formato de Idealista
        
        Args:
            location: Ubicación de entrada (puede ser ciudad, comarca o formato ya válido)
            
        Returns:
            Tuple con (location_formatted, location_type)
        """
        location_lower = location.lower().strip()
        
        # Si ya tiene formato ciudad-provincia, verificar si es válido
        if '-' in location_lower and '/' not in location_lower:
            if location_lower in self.idealista_cities.values():
                return location_lower, LocationType.CITY
            # Si no está en la lista pero tiene formato ciudad-provincia, aceptarlo
            if self._is_valid_city_format(location_lower):
                return location_lower, LocationType.CITY
        
        # Si tiene formato provincia/comarca
        if '/' in location_lower:
            parts = location_lower.split('/')
            if len(parts) == 2:
                provincia, comarca = parts
                if provincia in self.idealista_comarcas:
                    if comarca in self.idealista_comarcas[provincia]:
                        return self.idealista_comarcas[provincia][comarca], LocationType.COMARCA
                # Si no está en la lista pero tiene formato correcto, aceptarlo
                if self._is_valid_comarca_format(location_lower):
                    return location_lower, LocationType.COMARCA
        
        # Buscar en ciudades conocidas
        if location_lower in self.idealista_cities:
            return self.idealista_cities[location_lower], LocationType.CITY
        
        # Buscar en comarcas
        for provincia, comarcas in self.idealista_comarcas.items():
            if location_lower in comarcas:
                return comarcas[location_lower], LocationType.COMARCA
        
        # Si no se encuentra, intentar inferir el formato
        # Si contiene palabras que sugieren comarca, intentar formato comarca
        comarca_keywords = ['comarca', 'alt', 'baix', 'valles', 'garraf', 'penedes']
        if any(keyword in location_lower for keyword in comarca_keywords):
            # Asumir que es una comarca de Barcelona por defecto
            formatted = f"barcelona/{location_lower.replace(' ', '-')}"
            return formatted, LocationType.COMARCA
        
        # Por defecto, asumir que es una ciudad
        # Intentar inferir la provincia basándose en patrones comunes
        if any(word in location_lower for word in ['barcelona', 'barna']):
            formatted = f"{location_lower.replace(' ', '-')}-barcelona"
        elif any(word in location_lower for word in ['madrid']):
            formatted = f"{location_lower.replace(' ', '-')}-madrid"
        elif any(word in location_lower for word in ['valencia']):
            formatted = f"{location_lower.replace(' ', '-')}-valencia"
        else:
            # Si no se puede inferir, usar barcelona como provincia por defecto
            formatted = f"{location_lower.replace(' ', '-')}-barcelona"
        
        return formatted, LocationType.CITY
    
    def get_habitaclia_location(self, location: str) -> Tuple[str, LocationType]:
        """
        Convertir ubicación a formato de Habitaclia
        
        Args:
            location: Ubicación de entrada
            
        Returns:
            Tuple con (location_formatted, location_type)
        """
        location_lower = location.lower().strip()
        
        # Normalizar separadores para comarcas
        location_normalized = location_lower.replace('-', '_')
        
        # Buscar en comarcas de Habitaclia primero
        if location_normalized in self.habitaclia_comarcas:
            return self.habitaclia_comarcas[location_normalized], LocationType.COMARCA
        
        # Buscar variaciones de comarcas (con guiones)
        location_with_dash = location_lower.replace('_', '-')
        if location_with_dash in self.habitaclia_comarcas:
            return self.habitaclia_comarcas[location_with_dash], LocationType.COMARCA
        
        # Buscar por nombre base de comarca
        for comarca_key, comarca_formatted in self.habitaclia_comarcas.items():
            if location_lower in comarca_key or comarca_key in location_lower:
                return comarca_formatted, LocationType.COMARCA
        
        # Buscar en ciudades de Habitaclia
        if location_lower in self.habitaclia_cities:
            return self.habitaclia_cities[location_lower], LocationType.CITY
        
        # Buscar variaciones en ciudades
        for city_key, city_formatted in self.habitaclia_cities.items():
            if location_lower in city_key or city_key in location_lower:
                return city_formatted, LocationType.CITY
        
        # Si no se encuentra, intentar inferir el formato
        # Revisar si parece una comarca por palabras clave
        comarca_keywords = ['alt', 'baix', 'valles', 'penedes', 'emporda']
        if any(keyword in location_lower for keyword in comarca_keywords):
            # Formatear como comarca para Habitaclia
            formatted = location_lower.replace('-', '_').replace(' ', '_')
            return formatted, LocationType.COMARCA
        
        # Por defecto, tratar como ciudad
        formatted = location_lower.replace('-', '').replace(' ', '-')
        return formatted, LocationType.CITY
    
    def get_fotocasa_location(self, location: str) -> Tuple[str, LocationType]:
        """
        Convertir ubicación a formato de Fotocasa
        
        Args:
            location: Ubicación de entrada
            
        Returns:
            Tuple con (location_formatted, location_type)
        """
        location_lower = location.lower().strip()
        
        # Buscar en comarcas de Fotocasa primero
        if location_lower in self.fotocasa_comarcas:
            return self.fotocasa_comarcas[location_lower], LocationType.COMARCA
        
        # Buscar variaciones de comarcas
        for comarca_key, comarca_formatted in self.fotocasa_comarcas.items():
            if location_lower in comarca_key or comarca_key in location_lower:
                return comarca_formatted, LocationType.COMARCA
        
        # Buscar en ciudades de Fotocasa
        if location_lower in self.fotocasa_cities:
            return self.fotocasa_cities[location_lower], LocationType.CITY
        
        # Buscar variaciones en ciudades
        for city_key, city_formatted in self.fotocasa_cities.items():
            if location_lower in city_key or city_key in location_lower:
                return city_formatted, LocationType.CITY
        
        # Si no se encuentra, intentar inferir el formato
        # Revisar si parece una comarca por palabras clave
        comarca_keywords = ['alt', 'baix', 'valles', 'penedes', 'emporda']
        if any(keyword in location_lower for keyword in comarca_keywords):
            # Inferir provincia por contexto
            if any(word in location_lower for word in ['girona', 'figueres', 'emporda']):
                provincia = 'girona-provincia'
            elif any(word in location_lower for word in ['tarragona', 'reus']):
                provincia = 'tarragona-provincia'
            elif any(word in location_lower for word in ['lleida']):
                provincia = 'lleida-provincia'
            else:
                provincia = 'barcelona-provincia'  # Por defecto
            
            formatted = f"{provincia}/{location_lower.replace(' ', '-')}"
            return formatted, LocationType.COMARCA
        
        # Por defecto, tratar como ciudad
        # Verificar si es una capital conocida
        capitals = {
            'barcelona': 'barcelona-capital',
            'madrid': 'madrid-capital', 
            'valencia': 'valencia-capital',
            'sevilla': 'sevilla-capital'
        }
        
        if location_lower in capitals:
            return capitals[location_lower], LocationType.CITY
        
        # Para otras ciudades, usar formato simple
        formatted = location_lower.replace(' ', '-')
        return formatted, LocationType.CITY
    
    def _is_valid_city_format(self, location: str) -> bool:
        """Verificar si tiene formato válido ciudad-provincia"""
        pattern = r'^[a-z0-9-]+\-[a-z0-9-]+$'
        return bool(re.match(pattern, location))
    
    def _is_valid_comarca_format(self, location: str) -> bool:
        """Verificar si tiene formato válido provincia/comarca"""
        pattern = r'^[a-z0-9-]+/[a-z0-9-]+$'
        return bool(re.match(pattern, location))
    
    def get_suggested_locations(self, location_type: Optional[LocationType] = None) -> List[str]:
        """Obtener lista de ubicaciones sugeridas"""
        suggestions = []
        
        if location_type is None or location_type == LocationType.CITY:
            suggestions.extend(list(self.idealista_cities.values()))
        
        if location_type is None or location_type == LocationType.COMARCA:
            for provincia_comarcas in self.idealista_comarcas.values():
                suggestions.extend(list(provincia_comarcas.values()))
        
        return sorted(suggestions)
    
    def get_locations_by_province(self, province: str) -> Dict[str, List[str]]:
        """Obtener ubicaciones organizadas por provincia"""
        province_lower = province.lower()
        result = {"cities": [], "comarcas": []}
        
        # Ciudades de la provincia
        for city_key, city_formatted in self.idealista_cities.items():
            if city_formatted.endswith(f"-{province_lower}"):
                result["cities"].append(city_formatted)
        
        # Comarcas de la provincia
        if province_lower in self.idealista_comarcas:
            result["comarcas"] = list(self.idealista_comarcas[province_lower].values())
        
        return result
    
    def search_locations(self, query: str) -> List[Tuple[str, LocationType]]:
        """Buscar ubicaciones que coincidan con la consulta"""
        query_lower = query.lower()
        results = []
        
        # Buscar en ciudades
        for city_key, city_formatted in self.idealista_cities.items():
            if query_lower in city_key or query_lower in city_formatted:
                results.append((city_formatted, LocationType.CITY))
        
        # Buscar en comarcas
        for provincia, comarcas in self.idealista_comarcas.items():
            for comarca_key, comarca_formatted in comarcas.items():
                if query_lower in comarca_key or query_lower in comarca_formatted:
                    results.append((comarca_formatted, LocationType.COMARCA))
        
        return sorted(list(set(results)))


# Instancia global del gestor de ubicaciones
location_manager = LocationManager()
