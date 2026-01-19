#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para atualizar as URLs das imagens na base de dados
"""

import os
import re
from main import app, db, Vehicle

def parse_image_addresses():
    """Lê o arquivo de endereços e extrai as URLs"""
    addresses_file = "static/images/endereço de imagem"
    image_urls = {}
    
    try:
        with open(addresses_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Procurar por padrões como: marca modelo:https://...
        pattern = r'([^:]+):(https://[^\s]+)'
        matches = re.findall(pattern, content)
        
        for vehicle_name, url in matches:
            # Limpar o nome do veículo
            vehicle_name = vehicle_name.strip().lower()
            image_urls[vehicle_name] = url.strip()
            
        print(f"Encontrados {len(image_urls)} endereços de imagens:")
        for name, url in image_urls.items():
            print(f"  {name}: {url[:50]}...")
            
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        return {}
    
    return image_urls

def update_vehicle_images():
    """Atualiza as URLs das imagens na base de dados"""
    image_urls = parse_image_addresses()
    
    if not image_urls:
        print("Nenhum endereço encontrado!")
        return
    
    with app.app_context():
        vehicles = Vehicle.query.all()
        updated_count = 0
        
        for vehicle in vehicles:
            # Criar chave para busca (marca + modelo)
            search_key = f"{vehicle.brand.lower()} {vehicle.model.lower()}"
            
            # Procurar correspondência
            for url_key, url in image_urls.items():
                if search_key in url_key or url_key in search_key:
                    # Atualizar a URL da imagem
                    old_url = vehicle.image_url
                    vehicle.image_url = url
                    updated_count += 1
                    print(f"✓ {vehicle.brand} {vehicle.model}: {old_url} → {url[:50]}...")
                    break
        
        if updated_count > 0:
            db.session.commit()
            print(f"\n✅ {updated_count} veículos atualizados com sucesso!")
        else:
            print("\n⚠️ Nenhum veículo foi atualizado. Verifique se os nomes coincidem.")

def show_current_images():
    """Mostra as imagens atuais na base de dados"""
    with app.app_context():
        vehicles = Vehicle.query.all()
        print("\n📸 Imagens atuais na base de dados:")
        for vehicle in vehicles:
            print(f"  {vehicle.brand} {vehicle.model}: {vehicle.image_url}")

if __name__ == "__main__":
    print("🔄 Atualizando URLs das imagens...")
    show_current_images()
    print("\n" + "="*50)
    update_vehicle_images()
    print("\n" + "="*50)
    show_current_images()
