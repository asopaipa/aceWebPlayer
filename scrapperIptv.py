import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import asyncio
from playwright.async_api import async_playwright
import cloudscraper25
import base64
import json
import binascii
import string # Para replicar self.def_trans
import urllib.parse
import subprocess


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
        raise NotImplementedError
    
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

    @abstractmethod
    def scan_streams(self, target_url) -> List[Any]:
        """Método abstracto que cada scraper debe implementar"""
        raise NotImplementedError


class RojadirectaScraper(BaseScraper):
    """Scraper específico para Rojadirecta"""


    def load_from_url(self) -> bool:
        """Cargar HTML desde URL"""
        try:
            if not self.url.startswith("http"):
                self.url = "https://" + self.url


            scraper = cloudscraper25.create_scraper()
        

        
            response = scraper.get(self.url)
  

       
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

    async def scan_streams(self, target_url):
        found_streams = []
        event = asyncio.Event()
        
        async with async_playwright() as p:
            # Configuración del navegador
            prefs = {
                "media.autoplay.default": 0,  # 0=Allowed, 1=Blocked, 2=Prompt
                "media.autoplay.blocking_policy": 0, # Deshabilitar política de bloqueo adicional
                "media.autoplay.allow-muted": True, # A menudo necesario incluso con autoplay permitido
                "security.mixed_content.block_active_content": False # ¡PELIGROSO! Solo para diagnóstico
            }
            
            browser = await p.firefox.launch(
                headless=True,
                firefox_user_prefs=prefs
            )
            
            # Configuración del contexto
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                permissions=['geolocation'],
                #user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                ignore_https_errors=True
            )
            
            # Manejo de eventos de red
            async def handle_request(req):
                url = req.url
                if any(x in url for x in [".m3u8",".mp4"]):
                    print(f"Stream encontrado (request): {url}")
                    found_streams.append({
                        "url": url,
                        "headers": dict(req.headers),
                        "source": "request"
                    })
                    event.set()
                    
            async def handle_response(res):
                url = res.url
                if any(x in url for x in [".m3u8",".mp4"]):
                    print(f"Stream encontrado (response): {url}")
                    found_streams.append({
                        "url": url,
                        "headers": dict(res.headers),
                        "source": "response"
                    })
                    event.set()
            
            context.on("request", handle_request)
            context.on("response", handle_response)
            
            # Crear página 
            page = await context.new_page()

                    
            
            try:
                # Navegación inicial
                await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                print("Página cargada inicialmente")
                
                # Esperar carga inicial
                i=0.1
                if not found_streams and i > 8:
                    i=i+0.1
                    await asyncio.sleep(0.1)

                if not found_streams:
                    # Inyectar script para eliminar características restrictivas
                    await page.evaluate("""() => {
                        // Eliminar atributos sandbox
                        document.querySelectorAll('iframe[sandbox]').forEach(iframe => {
                            iframe.removeAttribute('sandbox');
                        });
                        
                        // Modificar reproductor de video para autoplay
                        document.querySelectorAll('video').forEach(video => {
                            video.autoplay = true;
                            video.muted = true;  // Los navegadores permiten autoplay si está silenciado
                            video.play().catch(e => console.log('Error al reproducir:', e));
                        });
                        
                        // Simular interacción de usuario
                        const simulateUserInteraction = () => {
                            document.body.click();
                            document.querySelectorAll('video, [class*="player"], [id*="player"]').forEach(el => {
                                try {
                                    if (el.play) el.play();
                                    el.click();
                                } catch(e) {}
                            });
                        };
                        
                        // Ejecutar ahora y después de un tiempo
                        simulateUserInteraction();
                        setTimeout(simulateUserInteraction, 3000);
                    }""")
                
                # Simular acciones de usuario
                await page.mouse.move(500, 500)
                await page.mouse.down()
                await page.mouse.up()
                
                # Intentar hacer clic en elementos conocidos
                #for selector in ["video", "[class*='play']", "[id*='player']", "iframe"]:
                #    elements = await page.query_selector_all(selector)
                #    for element in elements:
                #        try:
                #            await element.scroll_into_view_if_needed()
                #            await element.click(force=True, timeout=1000)
                #            await asyncio.sleep(2)
                #        except Exception:
                #            pass
                
                # Buscar y procesar iframes
                '''
                if not found_streams:
                    iframe_handles = await page.query_selector_all('iframe')
                    print(f"Encontrados {len(iframe_handles)} iframes")
                    
                    for idx, iframe in enumerate(iframe_handles):
                        try:
                            iframe_src = await iframe.get_attribute('src')
                            if iframe_src:
                                print(f"Procesando iframe {idx+1}: {iframe_src}")
                                
                                # Intentar acceder al contenido del iframe
                                frame = await iframe.content_frame()
                                if frame:
                                    # Intentar reproducir videos dentro del iframe
                                    await frame.evaluate("""() => {
                                        document.querySelectorAll('video').forEach(v => {
                                            v.autoplay = true;
                                            v.muted = true;
                                            v.play().catch(e => {});
                                        });
                                        
                                        // Clic en elementos potenciales
                                        ['video', '[class*="play"]', '[id*="player"]'].forEach(selector => {
                                            document.querySelectorAll(selector).forEach(el => {
                                                try { el.click(); } catch(e) {}
                                            });
                                        });
                                    }""")
                                else:
                                    # Si no podemos acceder al iframe, intenta abrir en nueva pestaña
                                    if iframe_src.startsWith('http'):
                                        try:
                                            iframe_page = await context.new_page()
                                            await iframe_page.goto(iframe_src, timeout=30000)
                                            await asyncio.sleep(5)
                                            await iframe_page.close()
                                        except Exception as e:
                                            print(f"Error al abrir iframe en nueva pestaña: {e}")
                        except Exception as e:
                            print(f"Error procesando iframe {idx+1}: {e}")
                '''
                # Esperar para encontrar streams
                print("Esperando para encontrar streams (60 segundos)...")
                try:
                    await asyncio.wait_for(event.wait(), timeout=60)
                    print("¡Stream encontrado!")
                except asyncio.TimeoutError:
                    print("Timeout sin encontrar streams")
                
                # Capturar screenshot y HTML final
                await page.screenshot(path="screenshot_final.png")
                final_html = await page.content()
                with open("web_iptv_final.html", "w", encoding="utf-8") as f:
                    f.write(final_html)
                    
            except Exception as e:
                print(f"Error durante la ejecución: {e}")
                
            finally:
                print("Manteniendo navegador abierto por 30 segundos para inspección...")
                #await asyncio.sleep(30)
                await browser.close()
        
        return found_streams
    
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
                'channels': channels,
                'clase': 'rojadirecta'
            }
            
            events.append(event_info)
        
        return events

class DaddyLiveScraper(BaseScraper):
    """Scraper específico para DaddyLive"""

    DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'

    
    def load_from_url(self) -> bool:
        """Cargar HTML desde URL"""
        try:
            if not self.url.startswith("http"):
                self.url = "https://" + self.url

            headers = { 'User-Agent': self.DEFAULT_USER_AGENT, 'Referer': self.url }


            url_eventos="schedule/schedule-generated.php"

            if not self.url.endswith("/"):
                url_eventos = "/" + url_eventos

            json_eventos= self.url + url_eventos

            scraper = cloudscraper25.create_scraper()
            #scraper = cloudscraper25.CloudScraper()
            response = scraper.get(json_eventos, headers=headers)
        

            if response.status_code == 200:
                self.html_content = response.text
                
                return True
            else:
                logger.error(f"Error al obtener URL {self.url}: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Excepción al cargar URL {self.url}: {str(e)}")
            return False



    def custom_uncompress(self,encoded_data_str):
        # ======================================================================
        # VALORES OBTENIDOS DEL PLUGIN ORIGINAL
        # ======================================================================
        PLUGIN_DATA_KEY_STR_FROM_CONFIG = 'Wawc9dxf2ivj5lmunpq4hrbsktgyXz01e3Y6o7Z8+/AOEPFQGLIKMCNRJSBTHUDV'

        DEF_TRANS_BYTES_FROM_PLUGIN = ''.join([
            string.ascii_uppercase,
            string.ascii_lowercase,
            string.digits,
            '+/'
        ]).encode('utf-8') # utf-8 es seguro aquí ya que son caracteres ASCII

        PLUGIN_DATA_KEY_BYTES = PLUGIN_DATA_KEY_STR_FROM_CONFIG.encode('utf-8') # Asumir utf-8 para la clave
        TRANSLATION_TABLE = bytes.maketrans(PLUGIN_DATA_KEY_BYTES, DEF_TRANS_BYTES_FROM_PLUGIN)
        if not isinstance(encoded_data_str, str):
            if isinstance(encoded_data_str, bytes):
                try:
                    encoded_data_str = encoded_data_str.decode('utf-8')
                except UnicodeDecodeError:
                    return f"error_input_bytes_not_utf8_{encoded_data_str[:10]}"
            else:
                return f"error_input_type_invalid_{type(encoded_data_str)}"

        if not encoded_data_str or "error_" in encoded_data_str:
            return encoded_data_str

        data_bytes_for_translate = encoded_data_str.encode('utf-8')

        try:
            translated_data_bytes = data_bytes_for_translate.translate(TRANSLATION_TABLE)
        except Exception as e:
            return f"error_translation_failure_{e}"

        try:
            temp_translated_str_for_padding = translated_data_bytes.decode('latin-1')
        except Exception as e:
            return f"error_decode_for_padding_{e}"

        missing_padding = len(temp_translated_str_for_padding) % 4
        if missing_padding:
            temp_translated_str_for_padding += '=' * (4 - missing_padding)
        
        final_b64_bytes_to_decode = temp_translated_str_for_padding.encode('latin-1')

        try:
            decoded_bytes = base64.b64decode(final_b64_bytes_to_decode)
        except (binascii.Error, ValueError) as e:
            return f"error_b64_final_failure_{e}"

        try:
            return decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return decoded_bytes 
        except Exception as e:
            return f"error_final_decode_to_str_{e}"

    def ensure_str_url(self,value, context="URL"):
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value.decode('utf-8', errors='replace')
        if isinstance(value, str) and "error_" in value:
            return value
        return str(value)

    def get_stream_reference_url(self,player_page_url, session):

        PLAYER_REF_URL_REGEX_RAW = {
            1: self.custom_uncompress('gbtIkbC7jY+eXRi6uq2+jY+Vvq2ezN7ozxe='), 
            2: self.custom_uncompress('gbtIkbC7jY+eXRi6uq2+jY+Vvq2ezN7ozxe='),
            3: self.custom_uncompress('gbtIkbC7jY+eXRi6uq2+jY+Vvq2eyZdPtn==')
        }
        PLAYER_REF_URL_REGEX = {}
        for k, v_raw in PLAYER_REF_URL_REGEX_RAW.items():
            if isinstance(v_raw, str) and "error_" in v_raw:
                print(f"ADVERTENCIA: Falló custom_uncompress para PLAYER_REF_URL_REGEX[{k}] ('{v_raw}'), usando fallback regex genérico.")
                PLAYER_REF_URL_REGEX[k] = b'src="([^"]+)"' 
            elif isinstance(v_raw, str): 
                PLAYER_REF_URL_REGEX[k] = v_raw.encode('utf-8')
            else: 
                PLAYER_REF_URL_REGEX[k] = v_raw

        print(f"  [-] Obteniendo página del reproductor: {player_page_url}")
        try:

            
            response = session.get(player_page_url, timeout=10)
            response.raise_for_status()
            
            #scraper = cloudscraper25.create_scraper(session)
            #response = scraper.get(player_page_url)
  
        except requests.exceptions.RequestException as e:
            print(f"  [!] Error en get_stream_reference_url (página reproductor): {e}")
            return None

        content_bytes = response.content
        ref_url_regex_pattern = PLAYER_REF_URL_REGEX.get(1)
        match = None

        if ref_url_regex_pattern and not ("error_" in ref_url_regex_pattern if isinstance(ref_url_regex_pattern, str) else False) :
            if isinstance(ref_url_regex_pattern, str):
                content_text = response.text
                try: match = re.search(ref_url_regex_pattern, content_text)
                except re.error as re_e: print(f"  [!] Error de Regex (str): {re_e} con patrón {ref_url_regex_pattern!r}")
            elif isinstance(ref_url_regex_pattern, bytes):
                try: match = re.search(ref_url_regex_pattern, content_bytes)
                except re.error as re_e: print(f"  [!] Error de Regex (bytes): {re_e} con patrón {ref_url_regex_pattern!r}")
            else:
                print(f"  [!] Tipo de patrón regex no reconocido para PLAYER_REF_URL_REGEX: {type(ref_url_regex_pattern)}")

        if not match:
            print(f"  [!] No se pudo encontrar la URL de referencia en {player_page_url}")
            return None

        ref_url_group = match.group(1)
        if isinstance(ref_url_group, bytes):
            try: ref_url = ref_url_group.decode('utf-8').strip()
            except UnicodeDecodeError: ref_url = ref_url_group.decode('latin-1', errors='replace').strip()
        else:
            ref_url = ref_url_group.strip()

        if ref_url.startswith('//'):
            ref_url = "https:" + ref_url
        elif not ref_url.startswith('http'):
            ref_url = urllib.parse.urljoin(player_page_url, ref_url)

        print(f"  [-] URL de referencia (ch_url) encontrada: {ref_url}")
        return ref_url, player_page_url


    def get_m3u8_url(self, player_page_url, session):
        found_streams = []
        EXT_X_KEY_RE = re.compile(r'#EXT-X-KEY:.*?URI="([^"]+)"')

        M3U8_FINAL_URL_TEMPLATE_RAW = self.custom_uncompress('gfpMXf5BjIUT1sPUjRPUjRPUjNCQyZHFy4lCmW==')
        M3U8_FINAL_URL_TEMPLATE = self.ensure_str_url(M3U8_FINAL_URL_TEMPLATE_RAW, "M3U8_FINAL_URL_TEMPLATE")
        if "error_" in M3U8_FINAL_URL_TEMPLATE or not (isinstance(M3U8_FINAL_URL_TEMPLATE, str) and "{}" in M3U8_FINAL_URL_TEMPLATE and M3U8_FINAL_URL_TEMPLATE.startswith("https://")):
            print(f"ADVERTENCIA: M3U8_FINAL_URL_TEMPLATE no es válida o falló uncompress ('{M3U8_FINAL_URL_TEMPLATE_RAW}'), usando fallback.")
            M3U8_FINAL_URL_TEMPLATE = "https://{}.cdn-host.com/{}/{}.m3u8" # 3 placeholders

        DEFAULT_M3U8_HOST = "new.newkso.ru" 

        SKEY_FROM_JSON_REGEX = re.compile(b'"token":"([^"]*)"')

        DADDYLIVE_BASE_URL_RAW = self.custom_uncompress('gfpMXf5BjIUokbpo0bL/zZhFysWQ=')
        DADDYLIVE_BASE_URL = self.ensure_str_url(DADDYLIVE_BASE_URL_RAW, "DADDYLIVE_BASE_URL")

        SKEY_REQUEST_URL_TEMPLATE_RAW = self.custom_uncompress('gfpMXf5BjIUFtsz7ybi7tfaEksoF0f7BjRl7X8t7X7UEyNUOzsWFXx3GuNl+kbSFtbL1gbnU0RM=')
        SKEY_REQUEST_URL_TEMPLATE = self.ensure_str_url(SKEY_REQUEST_URL_TEMPLATE_RAW, "SKEY_REQUEST_URL_TEMPLATE")
        if "error_" in SKEY_REQUEST_URL_TEMPLATE or not SKEY_REQUEST_URL_TEMPLATE.startswith("http"):
            if "error_" not in SKEY_REQUEST_URL_TEMPLATE and SKEY_REQUEST_URL_TEMPLATE.startswith("/"):
                SKEY_REQUEST_URL_TEMPLATE = DADDYLIVE_BASE_URL.rstrip('/') + SKEY_REQUEST_URL_TEMPLATE
            else:
                print(f"ADVERTENCIA: Falló custom_uncompress o resultado inválido para SKEY_REQUEST_URL_TEMPLATE ('{SKEY_REQUEST_URL_TEMPLATE_RAW}'), usando fallback.")
                SKEY_REQUEST_URL_TEMPLATE = DADDYLIVE_BASE_URL.rstrip('/') + "/req.php?c={}"


        CKEY_EXTRACTION_REGEX_RAW = {
            1: self.custom_uncompress('zZdI2xl+kbSFtbLjtsoeuqWYvdP027MAvn=='), 
            2: self.custom_uncompress('zZdI2xl+kbSFtbLjtsoeuqWYvdP027MAvn=='),
            3: self.custom_uncompress('zZdI2xl+kbSFtbLjtsoeuqWYvdP027MAvn==')
        }
        CKEY_EXTRACTION_REGEX = {}
        for k, v_raw in CKEY_EXTRACTION_REGEX_RAW.items():
            if isinstance(v_raw, str) and "error_" in v_raw:
                print(f"ADVERTENCIA: Falló custom_uncompress para CKEY_EXTRACTION_REGEX[{k}] ('{v_raw}'), usando fallback regex genérico.")
                CKEY_EXTRACTION_REGEX[k] = b"var\\s+tc\\s*=\\s*['\"]([^'\"]+)['\"]" 
            elif isinstance(v_raw, str):
                CKEY_EXTRACTION_REGEX[k] = v_raw.encode('utf-8')
            else:
                CKEY_EXTRACTION_REGEX[k] = v_raw

        ref_data = self.get_stream_reference_url(player_page_url, session)
        if not ref_data:
            return None
        ch_url, player_page_for_referer = ref_data

        headers = { 'User-Agent': self.DEFAULT_USER_AGENT, 'Referer': player_page_for_referer }
        print(f"  [-] Accediendo a URL de referencia ({ch_url}) con Referer: {player_page_for_referer}")
        try:

            #scraper = cloudscraper25.create_scraper(session)
            #response = scraper.get(player_page_url, headers=headers)

           
            response = session.get(ch_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  [!] Error al acceder a la URL de referencia ({ch_url}): {e}")
            return None

        content_bytes_ckey = response.content
        ckey_regex_pattern = CKEY_EXTRACTION_REGEX.get(1)
        match_ckey = None

        if ckey_regex_pattern and not ("error_" in ckey_regex_pattern if isinstance(ckey_regex_pattern, str) else False):
            if isinstance(ckey_regex_pattern, str):
                content_text_ckey = response.text
                try: match_ckey = re.search(ckey_regex_pattern, content_text_ckey)
                except re.error as re_e: print(f"  [!] Error de Regex para cKey (str): {re_e} con patrón {ckey_regex_pattern!r}")
            elif isinstance(ckey_regex_pattern, bytes):
                try: match_ckey = re.search(ckey_regex_pattern, content_bytes_ckey)
                except re.error as re_e: print(f"  [!] Error de Regex para cKey (bytes): {re_e} con patrón {ckey_regex_pattern!r}")
            else:
                print(f"  [!] Tipo de patrón regex no reconocido para CKEY_EXTRACTION_REGEX: {type(ckey_regex_pattern)}")
        else:
            print(f"  [!] Patrón CKEY_EXTRACTION_REGEX[1] no válido o con error: {ckey_regex_pattern!r}")
            print(f"      Contenido para buscar cKey manualmente (primeros 500 bytes): {content_bytes_ckey[:500]!r}")

        if not match_ckey:
            print(f"  [!] No se pudo extraer cKey de {ch_url} . Patrón: {ckey_regex_pattern} . Response: {response.text[:1000]}")
            return None

        cKey_group = match_ckey.group(1)
        if isinstance(cKey_group, bytes):
            try: cKey = cKey_group.decode('utf-8').strip()
            except UnicodeDecodeError: cKey = cKey_group.decode('latin-1', errors='replace').strip()
        else:
            cKey = cKey_group.strip()
        print(f"  [-] cKey extraída: {cKey}")

        skey_req_url = SKEY_REQUEST_URL_TEMPLATE.format(cKey)
        headers_for_skey = { 'User-Agent': self.DEFAULT_USER_AGENT, 'Referer': ch_url }
        print(f"  [-] Solicitando sKey desde: {skey_req_url} con Referer: {ch_url}")
        try:
            response = session.get(skey_req_url, headers=headers_for_skey, timeout=10)
            response.raise_for_status()
            #scraper = cloudscraper25.create_scraper(session)
            #response = scraper.get(skey_req_url, headers_for_skey)
        except requests.exceptions.RequestException as e:
            print(f"  [!] Error al solicitar sKey: {e}")
            return None

        skey_content_bytes = response.content
        skey_match = SKEY_FROM_JSON_REGEX.search(skey_content_bytes)
        if not skey_match:
            skey_match = re.search(b':"([^"]*)', skey_content_bytes)

        if not skey_match:
            print(f"  [!] No se pudo extraer sKey de la respuesta de {skey_req_url}")
            try: print(f"      Respuesta JSON (sKey): {response.json()}")
            except json.JSONDecodeError: print(f"      Respuesta (sKey) no es JSON: {response.text[:200]}...")
            return None

        sKey_bytes = skey_match.group(1)
        try: sKey = sKey_bytes.decode('utf-8').strip()
        except UnicodeDecodeError: sKey = sKey_bytes.decode('latin-1', errors='replace').strip()
        print(f"  [-] sKey extraída: {sKey}")
        

        final_m3u8_url = M3U8_FINAL_URL_TEMPLATE.format(sKey, DEFAULT_M3U8_HOST, sKey, cKey)
        print(f"  [-] URL M3U8 construida: {final_m3u8_url}")

        # Obtener contenido del M3U8 para buscar la clave
        m3u8_content_headers = { 'User-Agent': self.DEFAULT_USER_AGENT, 'Referer': ch_url }
        print(f"  [-] Obteniendo contenido M3U8 desde: {final_m3u8_url} con Referer: {ch_url}")
        try:
            response_m3u8 = session.get(final_m3u8_url, headers=m3u8_content_headers, timeout=10)
            response_m3u8.raise_for_status()
            #scraper = cloudscraper25.create_scraper(session)
            #response_m3u8=response = scraper.get(final_m3u8_url, m3u8_content_headers)


            m3u8_text_content = response_m3u8.text
        except requests.exceptions.RequestException as e:
            print(f"  [!] Error al obtener el contenido del M3U8 ({final_m3u8_url}): {e}")
            return {'m3u8_url': final_m3u8_url, 'key_data': None, 'error_getting_content': str(e)}

        key_match = EXT_X_KEY_RE.search(m3u8_text_content)
        #result_data = {'url': final_m3u8_url, 'headers': None, 'source': 'cabernet'}



        if key_match:
            key_uri_relative = key_match.group(1)
            key_uri_absolute = urllib.parse.urljoin(final_m3u8_url, key_uri_relative)
            
            parsed_ch_url = urllib.parse.urlparse(ch_url)
            origin_for_key = f"{parsed_ch_url.scheme}://{parsed_ch_url.netloc}"

            
            
            #command_list = [
            #    "curl",
            #    key_uri_absolute,
            #    "-H", f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            #    "-H", "Accept: */*",
            #    "-H", "Accept-Language: en-US,en;q=0.5",
            #    "-H", "Accept-Encoding: gzip, deflate, br, zstd", # curl maneja esto
            #    "-H", f"Origin: {origin_for_key}",
            #    "-H", "DNT: 1",
            #    "-H", "Connection: keep-alive", # curl maneja esto
            #    "-H", f"Referer: {origin_for_key}/",
            #    "-H", "Sec-Fetch-Dest: empty",
            #    "-H", "Sec-Fetch-Mode: cors",
            #    "-H", "Sec-Fetch-Site: cross-site",
            #    "-H", "Pragma: no-cache",
            #    "-H", "Cache-Control: no-cache",
                # Puedes añadir otras opciones de curl si las necesitas, por ejemplo:
                # "-s",  # Modo silencioso (no muestra barra de progreso)
                # "-L",  # Seguir redirecciones
            #]
           
           

            #print(f"[*] Ejecutando comando: {' '.join(command_list)}") # Para visualización

            #key=""
            try:

            #    process = subprocess.run(
            #        command_list,
            #        capture_output=True,
            #        check=True,  # Lanza CalledProcessError si el código de retorno no es 0
            #        text=False   # Obtiene stdout y stderr como bytes
            #    )

                # La salida estándar (el contenido de la clave) estará en process.stdout
            #    key_content_bytes = process.stdout

                headers_for_key = { 'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0', 'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.5', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Origin': 'https://alldownplay.xyz', 'DNT': '1', 'Connection': 'keep-alive', 'Referer': 'https://alldownplay.xyz/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'cross-site', 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }
                scraper = cloudscraper25.create_scraper()
                response_m3u8=scraper.get("https://key.keylocking.ru/wmsxx.php?test=true&name=premium326&number=1", headers=headers_for_key)
                key_content_bytes = response_m3u8.content
                    
                print(f"[+] Comando curl ejecutado exitosamente!")
                print(f"[*] Clave obtenida (bytes): {key_content_bytes}")
                print(f"[*] Clave obtenida (hex): {key_content_bytes.hex()}")
                key={key_content_bytes.hex()}
                

            except subprocess.CalledProcessError as e:
                print(f"[-] Error al ejecutar curl. El comando devolvió un código de error: {e.returncode}")
                print(f"    Comando: {' '.join(e.cmd)}")
                if e.stdout:
                    print(f"    Salida estándar (stdout) del error (bytes): {e.stdout}")
                    # Intenta decodificar si crees que es texto útil
                    # print(f"    Salida estándar (stdout) del error (texto): {e.stdout.decode(errors='ignore')}")
                if e.stderr:
                    print(f"    Salida de error (stderr) del error (bytes): {e.stderr}")
                    print(f"    Salida de error (stderr) del error (texto): {e.stderr.decode(errors='ignore')}")
            except FileNotFoundError:
                print("[-] Error: El comando 'curl' no se encontró. Asegúrate de que esté instalado y en el PATH del sistema.")
            except Exception as e:
                print(f"[-] Ocurrió un error inesperado al ejecutar subprocess: {e}")



            headers_for_key = {
                'User-Agent': self.DEFAULT_USER_AGENT,
                'Referer': final_m3u8_url, 
                'Origin': origin_for_key,
                'key_hex': key
            }

            found_streams.append({
                "url": final_m3u8_url,
                "headers": dict(headers_for_key),
                "source": "cabernet"
            })

     
            print(f"  [+] Clave M3U8 encontrada: URI='{key_uri_absolute}'")
            print(f"      Headers para la clave: Origin='{final_m3u8_url}', Referer='{final_m3u8_url}'")
        else:
            found_streams.append({
                "url": final_m3u8_url,
                "headers": None,
                "source": "cabernet"
            })
            print(f"  [-] No se encontró EXT-X-KEY en el contenido del M3U8.")

        print(f"  [+] URL M3U8 y datos de clave (si existen) procesados para {player_page_url}.")
        return found_streams
    
    async def scan_streams(self, target_url):

   

        session = requests.Session()
        session.headers.update({'User-Agent': self.DEFAULT_USER_AGENT})

        


        found_streams = []

        found_streams=self.get_m3u8_url(target_url, session)

        return found_streams

    def scrape_old(self) -> List[Dict[str, Any]]:
        """Extraer eventos deportivos de DaddyLive"""
        if not self.soup:
            logger.error("No se ha cargado el HTML antes de intentar scraping")
            return []
        
        events = []
        channels = []
    
        # Patrón para identificar horas en formato HH:MM
        time_pattern = re.compile(r'\d{2}:\d{2}')
        
        # Buscar todos los elementos <strong>
        strongs = self.soup.find_all('strong')
        
        for strong in strongs:
            # Convertir el contenido del strong a texto
            texto_completo = strong.get_text()
            
            # Verificar si contiene un horario en formato HH:MM
            match = time_pattern.search(texto_completo)
            
            if match:
                # Obtener la hora
                hora = match.group(0)
                
                # Extraer título del evento (todo lo que está entre la hora y el primer enlace)
                titulo_inicio = texto_completo.index(hora) + len(hora)
                titulo_fin = len(texto_completo)
                
                # Buscar los enlaces dentro del strong
                canales = []
                
                for link in strong.find_all('a'):
                    canales.append(link.get_text())
                    channels.append({
                            'name': link.get_text(),
                            'url': link.get('href')
                        })
                
                # Si hay enlaces, ajustar donde termina el título
                if canales:
                    titulo_fin = texto_completo.index(canales[0]) - 1  # -1 para quitar el espacio antes del canal
                
                titulo = texto_completo[titulo_inicio:titulo_fin].strip()

                event_info = {
                    'country_league': "",
                    'title': titulo,
                    'time': hora,
                    'channels': channels,
                    'clase': 'daddylive'
                }
                
                events.append(event_info)
                channels = []
                

        
        return events



    def scrape(self) -> List[Dict[str, Any]]:
        """Extraer eventos deportivos de DaddyLive"""
        if not self.html_content:
            logger.error("No se ha cargado el HTML antes de intentar scraping")
            return []
        
        events = []
        channels = []
    

        # Cargar el JSON string a un diccionario Python
        data = json.loads(self.html_content)

        # Lista para almacenar los eventos procesados
        processed_events = []


        # Iteramos sobre cada par clave-valor en el diccionario principal (cada fecha)
        # 'date_key' será la cadena de la fecha, 'daily_schedule' el diccionario de esa fecha
        for date_key, daily_schedule in data.items():
            # Dentro de cada 'daily_schedule', iteramos sobre sus claves (tipos de evento)
            # 'event_type_key' será "PPV Events", "TV Shows", "Movies", etc.
            # 'events_list' será la lista de objetos de evento para ese tipo
            for event_type_key, events_list in daily_schedule.items():
                # Verificamos que 'events_list' sea realmente una lista (para evitar errores si la estructura es inesperada)
                if not isinstance(events_list, list):
                    # Podrías imprimir un aviso o registrar esto si es necesario
                    # print(f"Advertencia: Se esperaba una lista para {date_key} -> {event_type_key}, pero se encontró {type(events_list)}")
                    continue # Saltar a la siguiente iteración

                # Iteramos sobre cada evento individual dentro de la lista
                for event_item in events_list:
                    # Nos aseguramos de que event_item sea un diccionario
                    if not isinstance(event_item, dict):
                        # print(f"Advertencia: Se esperaba un diccionario para un evento en {date_key} -> {event_type_key}, pero se encontró {type(event_item)}")
                        continue

                    # Extraemos el título y la hora
                    # Usamos .get() para evitar errores si alguna clave no existe y proveer un valor por defecto
                    titulo = event_item.get("event")
                    hora = event_item.get("time")

                    # Procesamos los canales
                    channels_list = []
                    # Usamos .get("channels", []) para que si "channels" no existe, devuelva una lista vacía
                    # y el bucle 'for ch in ...' simplemente no se ejecute, evitando un error.
                    for ch in event_item.get("channels", []):
                        # Nos aseguramos de que 'ch' (cada canal) sea un diccionario
                        if not isinstance(ch, dict):
                            # print(f"Advertencia: Se esperaba un diccionario para un canal en el evento '{titulo}', pero se encontró {type(ch)}")
                            continue

                        channel_name = ch.get("channel_name")
                        channel_url_part = ch.get("channel_id") 

                        url_canal_pre="stream/stream-"
                        url_canal_post=".php"

                        if not self.url.endswith("/"):
                            url_canal_pre = "/" + url_canal_pre


                        channel_url_complete=self.url+url_canal_pre+channel_url_part+url_canal_post
                        
                        channels_list.append({
                            "name": channel_name,
                            "url": channel_url_complete # Guardamos la URL completa
                        })
                    
                    # Creamos el diccionario del evento con el formato deseado
                    processed_event = {
                        'country_league': "",
                        "title": titulo,
                        "time": hora,
                        "channels": channels_list,
                        'clase': 'daddylive'
                    }
                    processed_events.append(processed_event)

             
        
        return processed_events


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
        if not domain:
            domain = url
        
        for pattern, scraper_class in self.scraper_map.items():
            if pattern in domain:
                return scraper_class(domain)
        
        logger.warning(f"No se encontró scraper para la URL: {url}")
        return None
    
    def scrape_url(self, url: str) -> List[Dict[str, Any]]:
        """Hacer scraping de una URL específica"""
        scraper = self.get_scraper_for_url(url)
        
        if not scraper:
            logger.error(f"No hay scraper disponible para {url}")
            return []
        
        #scraper = scraper_class(url)
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

        #if filtered_rows:
        #    with open(filepathdown, "w") as f:
                #f.write("#EXTM3U\n")
        #        for row in all_rows:
        #            f.write(f'#EXTINF:-1 tvg-id="" tvg-logo="" group-title="{row.get("source", "")}",{row.get("title", "")} {row.get("channel_name", "")}\n')
        #            f.write(self.format_url_with_headers(row.get("url_stream", ""), row.get("headers")))
            
        if all_rows:
            with open(filepath, "w") as f:
                #f.write("#EXTM3U\n")
                for row in all_rows:
                    f.write(f'#EXTINF:-1 tvg-id="" tvg-logo="" group-title="{row.get("source", "")}",{row.get("title", "")} {row.get("channel_name", "")}\n')
                    f.write(f'{row.get("clase", "")}/{row.get("channel_url", "")}\n')
        else:
            logger.warning("No hay datos para exportar")     






