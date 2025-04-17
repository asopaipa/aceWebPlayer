import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import json
import importlib
from urllib.parse import urlparse
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import asyncio
from playwright.async_api import async_playwright

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scraper_manager')

class BaseScraper(ABC):
    """Clase base abstracta para todos los scrapers"""
    
    def __init__(self, url: str):
        self.url = url
        self.html_content = None
        self.soup = None


    
    
    def load_from_url(self) -> bool:
        """Cargar HTML desde URL"""
        try:
            response = requests.get(self.url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                self.html_content = response.text
                self.soup = BeautifulSoup(self.html_content, 'html.parser')
                return True
            else:
                logger.error(f"Error al obtener URL {self.url}: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Excepción al cargar URL {self.url}: {str(e)}")
            return False
    
    def load_from_html(self, html_content: str) -> bool:
        """Cargar HTML desde una cadena"""
        try:
            self.html_content = html_content
            self.soup = BeautifulSoup(self.html_content, 'html.parser')
            return True
        except Exception as e:
            logger.error(f"Error al analizar HTML: {str(e)}")
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        """Cargar HTML desde un archivo"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                self.html_content = file.read()
                self.soup = BeautifulSoup(self.html_content, 'html.parser')
                return True
        except Exception as e:
            logger.error(f"Error al cargar archivo {filepath}: {str(e)}")
            return False
    
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """Método abstracto que cada scraper debe implementar"""
        pass

class RojadirectaScraper(BaseScraper):
    """Scraper específico para Rojadirecta"""
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Extraer eventos deportivos de Rojadirecta"""
        if not self.soup:
            logger.error("No se ha cargado el HTML antes de intentar scraping")
            return []
        
        events = []
        
        # Buscar todos los elementos li de la clase menu
        menu_items = self.soup.select("ul.menu > li")
        
        for item in menu_items:
            # Extraer el país/liga (está en la clase del li)
            country_class = item.get('class', [''])[0] if item.get('class') else ''
            
            # Extraer el título del evento y la hora
            event_link = item.find('a')
            if not event_link:
                continue
                
            event_title = event_link.get_text().strip()
            
            # Eliminar la hora del título
            time_match = re.search(r'(.+?)(?:<span class="t">(\d+:\d+)</span>)', str(event_link))
            
            if time_match:
                event_title = time_match.group(1).strip()
                event_time = time_match.group(2)
            else:
                # Si no hay formato de hora en span, intentar extraer de otra manera
                time_span = event_link.find('span', class_='t')
                event_time = time_span.text if time_span else "No especificado"
                # Limpiar el título si la hora está incluida
                event_title = event_title.replace(event_time, '').strip()
                
            event_title = event_title.replace('<a href="#">', '')
            
            # Extraer los canales disponibles
            channels = []
            channel_items = item.find('ul')
            
            if channel_items:
                for channel in channel_items.find_all('li', class_='subitem1'):
                    channel_link = channel.find('a')
                    if channel_link:
                        channel_name = channel_link.text.strip()
                        channel_url = channel_link.get('href', '')
                        channels.append({
                            'name': channel_name,
                            'url': channel_url
                        })
            
            # Crear diccionario con la información del evento
            event_info = {
                'country_league': country_class,
                'title': event_title,
                'time': event_time,
                'channels': channels
            }
            
            events.append(event_info)
        
        return events

class DaddyLiveScraper(BaseScraper):
    """Scraper específico para DaddyLive"""
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Extraer eventos deportivos de DaddyLive"""
        # Implementación específica para DaddyLive (ejemplo)
        if not self.soup:
            return []
        
        # Aquí iría la lógica específica para DaddyLive
        events = []
        # ... código de extracción
        return events


class ScraperManager:
    """Gestor para múltiples scrapers"""

    
    def __init__(self):
        # Mapeo de patrones de URL a clases de scraper
        self.scraper_map = {}
        # Para almacenar resultados de scraping
        self.results = {}
        
    def register_scraper(self, url_pattern: str, scraper_class: type):
        """Registrar un scraper para un patrón de URL"""
        self.scraper_map[url_pattern] = scraper_class
        logger.info(f"Registrado scraper {scraper_class.__name__} para URLs que coincidan con {url_pattern}")
    
    def get_scraper_for_url(self, url: str) -> Optional[type]:
        """Obtener la clase de scraper apropiada para la URL dada"""
        domain = urlparse(url).netloc
        
        for pattern, scraper_class in self.scraper_map.items():
            if pattern in domain:
                return scraper_class
        
        logger.warning(f"No se encontró scraper para la URL: {url}")
        return None
    
    def scrape_url(self, url: str) -> List[Dict[str, Any]]:
        """Hacer scraping de una URL específica"""
        scraper_class = self.get_scraper_for_url(url)
        
        if not scraper_class:
            logger.error(f"No hay scraper disponible para {url}")
            return []
        
        scraper = scraper_class(url)
        if scraper.load_from_url():
            results = scraper.scrape()
            self.results[url] = results
            return results
        else:
            logger.error(f"No se pudo cargar la URL {url}")
            return []
    
    def scrape_from_html(self, html: str, scraper_type: type) -> List[Dict[str, Any]]:
        """Hacer scraping de contenido HTML con un scraper específico"""
        scraper = scraper_type("dummy_url")  # La URL no se usará
        if scraper.load_from_html(html):
            return scraper.scrape()
        return []
    
    def scrape_file(self, filepath: str, scraper_type: type) -> List[Dict[str, Any]]:
        """Hacer scraping de un archivo HTML con un scraper específico"""
        scraper = scraper_type("dummy_url")  # La URL no se usará
        if scraper.load_from_file(filepath):
            results = scraper.scrape()
            self.results[filepath] = results
            return results
        return []
    
    def scrape_multiple_urls(self, urls: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Hacer scraping de múltiples URLs"""
        results = {}
        
        for url in urls:
            results[url] = self.scrape_url(url)
        
        self.results.update(results)
        return results
    
    def export_to_json(self, filepath: str = "scraping_results.json"):
        """Exportar resultados a JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)
        logger.info(f"Resultados exportados a {filepath}")


    def export_to_m3u(self, filepath: str = "directos_web.m3u8"):
        
        """Exportar resultados a M3U8"""
        all_rows = []
        
        for url, events in self.results.items():
            for event in events:
                # Extraer el dominio de la URL
                domain = urlparse(url).netloc
                
                # Para cada canal, crear una fila
                if 'channels' in event:
                    for channel in event.get('channels', []):
                        row = {
                            'source': domain,
                            'url': url
                        }
                        # Añadir todos los campos del evento
                        for key, value in event.items():
                            if key != 'channels':  # No incluir la lista de canales
                                row[key] = value
                        
                        # Añadir información del canal
                        row['channel_name'] = channel.get('name', '')
                        row['channel_url'] = channel.get('url', '')
                        
                        all_rows.append(row)
                else:
                    # Si no hay canales, crear una sola fila para el evento
                    row = {
                        'source': domain,
                        'url': url
                    }
                    # Añadir todos los campos del evento
                    for key, value in event.items():
                        row[key] = value
                    
                    all_rows.append(row)

        #filtered_rows = []
        #if all_rows:   
        #    for row in all_rows:
        #        found_streams = asyncio.run(self.scan_streams(row.get("channel_url", "")))
        #        if found_streams and found_streams[0] and found_streams[0]["url"] and found_streams[0]["headers"]:
        #            row["url_stream"] = found_streams[0]["url"]
        #            row["headers"] = found_streams[0]["headers"]
        #            filtered_rows.append(row)

            
        if all_rows:
            with open(filepath, "w") as f:
                #f.write("#EXTM3U\n")
                for row in all_rows:
                    f.write(f'#EXTINF:-1 tvg-id="" tvg-logo="" group-title="{row.get("source", "")}",{row.get("title", "")} {row.get("channel_name", "")}\n')
                    f.write(f'{row.get("channel_url", "")}\n')
        else:
            logger.warning("No hay datos para exportar")        
    
    def export_to_csv(self, filepath: str = "scraping_results.csv"):
        """Exportar resultados a CSV"""
        all_rows = []
        
        for url, events in self.results.items():
            for event in events:
                # Extraer el dominio de la URL
                domain = urlparse(url).netloc
                
                # Para cada canal, crear una fila
                if 'channels' in event:
                    for channel in event.get('channels', []):
                        row = {
                            'source': domain,
                            'url': url
                        }
                        # Añadir todos los campos del evento
                        for key, value in event.items():
                            if key != 'channels':  # No incluir la lista de canales
                                row[key] = value
                        
                        # Añadir información del canal
                        row['channel_name'] = channel.get('name', '')
                        row['channel_url'] = channel.get('url', '')
                        
                        all_rows.append(row)
                else:
                    # Si no hay canales, crear una sola fila para el evento
                    row = {
                        'source': domain,
                        'url': url
                    }
                    # Añadir todos los campos del evento
                    for key, value in event.items():
                        row[key] = value
                    
                    all_rows.append(row)
        
        if all_rows:
            df = pd.DataFrame(all_rows)
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Resultados exportados a {filepath}")
        else:
            logger.warning("No hay datos para exportar a CSV")

