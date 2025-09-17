#!/usr/bin/env python3
"""
Script para corregir selectores CSS deprecados
"""

import os
import re

def fix_contains_selectors(directory):
    """Reemplazar :contains por :-soup-contains en archivos Python"""
    
    files_to_fix = [
        'scraper/idealista.py',
        'scraper/fotocasa.py', 
        'scraper/habitaclia.py'
    ]
    
    for file_path in files_to_fix:
        full_path = os.path.join(directory, file_path)
        if os.path.exists(full_path):
            print(f"Corrigiendo {file_path}...")
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Reemplazar :contains por :-soup-contains
            # Buscar patrones como :contains("texto")
            updated_content = re.sub(r':contains\(', ':-soup-contains(', content)
            
            if content != updated_content:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"  ✅ {file_path} actualizado")
            else:
                print(f"  ℹ️  {file_path} no necesita cambios")

if __name__ == "__main__":
    fix_contains_selectors(".")
    print("\n✅ Corrección de selectores CSS completada")
