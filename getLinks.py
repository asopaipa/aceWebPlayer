from cryptoLink import decrypt
from scrapperIptv import ScraperManager, RojadirectaScraper, DaddyLiveScraper
from urllib.parse import urlparse, urljoin
import re
import random
import requests
import csv
from bs4 import BeautifulSoup
import logging
import asyncio

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('getLinks')

def normalizar(texto):
    

    # Eliminar todo lo que esté después de " >"
    texto = texto.split(" >")[0]
    # Eliminar todo lo que esté después de " -->"
    texto = texto.split(" -->")[0]

    # Eliminar palabras como "SD", "HD", "FHD", "4K" (independientemente de mayúsculas/minúsculas)
    texto = re.sub(r'\b(SD|HD|FHD|4K)\b', '', texto, flags=re.IGNORECASE)



    return texto.strip().lower()
    
def decode_default_url():
    
    # URL de la que quieres obtener los datos
    url = b'\xb6L\x18\xae#^+\xad@\x02\t\xbf\x8d\xa9V\x8a\x021\xa3\xda>c\xde\x12\xe8::\xbc\xb4\xd2x'
    url2= b'4\xe4L#\x85\x8e\xf5\x0by\xdb\xadV2\xa9n0\x1e\x14)\xab\x16\x90\xb2\xf8\xf65\xb9\xa0\xc0\xd4l\xd9\xc8&[\xfdc\xb1MS\xebZm\xc3\x91I\x8a\xfc'
    iv2 = b'\n]\x95\xc4\x98\xc5\xa5\x01\xca#\x90w\x07\x87\xb3$'
    iv = b'[\xb0E\x9a-\x98.\xd6\xe9>-\x1a$4`}'
    key = b'h\x03\xf5\x0er\xa7\xf7\x8b\xfd\xbaa\x08\r,\x02\x08\x82\n\xcdJ^\xef\xed\xb7\xa88\xca\xcd0\xed\x98l'
    url3 = b'M\xe6\xf9\xdcL\xabA\xde\xc2\xf3x\xc0f\x1c\xb7\xd7\xc6\xa5\x8f\x16\x01\x1a\xb3\xa9\xf8\xf3\x9a%a\x1c\x90E'
    iv3 = b'bU2\xca_)\x16/\xa7B.\xc4\x85x\xba\xb4'

    
    # Realizar la solicitud HTTP
    return decrypt(url, key, iv), decrypt(url2, key, iv2), decrypt(url3, key, iv3)


def generar_m3u_from_url(miHost, urls, tipo, folder):
    # Ruta del diccionario CSV
    csv_file = "resources/dictionary.csv"
    # Archivos de salida
    if tipo == "directos":
        output_file = f"{folder}/acestream_directos.m3u"
        output_file_remote = f"{folder}/web_directos.m3u"
    if tipo == "pelis":
        output_file = f"{folder}/acestream_pelis.m3u"
        output_file_remote = f"{folder}/web_pelis.m3u"
    if tipo == "webs":
        scrapIptv(urls, folder)
        return
    
    # Cargar el diccionario desde el CSV
    diccionario = {}
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            canal, canal_epg, imagen, grupo = row
            canal_normalizado = normalizar(canal)
            diccionario[canal_normalizado] = {"canal_epg": canal_epg, "imagen": imagen, "grupo": grupo}

    # Lista para almacenar enlaces únicos
    enlaces_unicos = set()

    with open(output_file, "w") as f, open(output_file_remote, "w") as f1:
        for url in urls:
            try:
                # Realizar una solicitud HEAD para comprobar el tipo de contenido
                response_head = requests.head(url, allow_redirects=True, timeout=500)
                content_type = response_head.headers.get("Content-Type", "").lower()
                # Descargar el contenido y procesarlo como archivo M3U
                response = requests.get(url, timeout=500)
                html = response.text
                logger.info(f"Contenido: {html[:500]}")
                # Analizamos el HTML en busca de una página de seguridad del zeronet
                soup = BeautifulSoup(html, 'html.parser')
                form = soup.find("form", action="/add/")
                if form:
                    inputs = form.find_all("input", type="hidden")
                    data = {}
                    for input_tag in inputs:
                        name = input_tag.get("name")
                        value = input_tag.get("value")
                        if name and value:
                            data[name] = value
                    
                    # También puedes incluir el valor del botón submit si es necesario
                    submit_input = form.find("input", type="submit")
                    if submit_input and submit_input.get("name"):
                        data[submit_input.get("name")] = submit_input.get("value")
                    # Crear una sesión para mantener las cookies
                    session = requests.Session()
                    
                    # URL a la que se envía el formulario
                    action_url = urljoin(url, form.get("action"))
                    
                    # Enviar el formulario
                    response_post = session.post(action_url, data=data, timeout=500)
                    
                    response_head = requests.head(url, allow_redirects=True, timeout=500)
                    content_type = response_head.headers.get("Content-Type", "").lower()
                    response = requests.get(url, timeout=500)                             
                
                # Si el tipo de contenido indica un M3U
                if "mpegurl" in content_type or "m3u" in content_type:
                    
                    if response.status_code == 200:
                        m3u_content = response.text
                        canal_actual = None
                        grupo_actual = None
                        tvg_id_actual = None
                        logo_actual = None
                        for line in m3u_content.splitlines():
                            line = line.strip()
                            if line.startswith("#EXTINF"):
                                # Extraer el nombre del canal de la línea #EXTINF
                                title_match = re.search(r',([^,]+)$', line)  # Extraer título después de la última coma
                                logo_match = re.search(r'tvg-logo="([^"]*)"', line)  # Extraer logo si está presente
                                group_match = re.search(r'group-title="([^"]*)"', line)  # Extraer grupo si está presente
                                tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)  # Extraer tvg-id si está presente
                                
                                if title_match:
                                    canal_actual = title_match.group(1).strip()
                                grupo_actual = group_match.group(1) if group_match else None
                                tvg_id_actual = tvg_id_match.group(1) if tvg_id_match else None
                                logo_actual = logo_match.group(1) if logo_match else None
                            elif line.startswith("http"):
                                logger.info(f"Analizando enlace: {line}")
                                if line not in enlaces_unicos:
                                    enlaces_unicos.add(line)
                                    escribir_m3u(f, f1, line, diccionario, miHost, canal_actual, tipo, 
                                                 grupo_actual, tvg_id_actual, logo_actual)
                                else:
                                    logger.info(f"El enlace no es único, lo descartamos")
                                    
                            elif line.startswith("acestream:"): 
                                matches = re.findall(r'acestream://([a-f0-9]{40})', line)
                                for acestream_url in matches:
                                    logger.info(f"Analizando enlace: {line}")
                                    if acestream_url not in enlaces_unicos:
                                        logger.info(f"Es único, lo mostraramos")
                                        enlaces_unicos.add(acestream_url)
                                        escribir_m3u(f, f1, f"acestream://{acestream_url}", diccionario, miHost, canal_actual, tipo, 
                                                 grupo_actual, tvg_id_actual, logo_actual)
                             
                                    else:
                                        logger.info(f"El enlace no es único, lo descartamos")
                        
                else:
                   
                    if response.status_code == 200:
                        content = response.text
                        matches = re.findall(r'{\s*"name": "(.*?)", "url": "acestream://([a-f0-9]{40})"\s*}', content)
                        for canal, acestream_url in matches:
                            logger.info(f"Analizando enlace: {acestream_url}")
                            if acestream_url not in enlaces_unicos:
                                logger.info(f"Es único, lo mostraramos")
                                enlaces_unicos.add(acestream_url)
                                escribir_m3u(f, f1, f"acestream://{acestream_url}", diccionario, miHost, canal, tipo, 
                                           None, None, None)
                            else:
                                logger.info(f"El enlace no es único, lo descartamos")
            except Exception as e:
                logger.error(f"Error procesando URL {url}: {e}")

    logger.info(f"Archivos generados: {output_file}, {output_file_remote}")


def escribir_m3u(f, f1, url, diccionario, miHost, canal, tipo, 
                 grupo_orig=None, tvg_id_orig=None, logo_orig=None):
    """
    Escribe una línea en los archivos M3U con los valores del diccionario, si aplica.
    Prioriza los valores originales del M3U si están disponibles.
    """
    if("[pid]" in miHost):
        numero_aleatorio = random.randint(1, 10000)
        miHost=miHost.replace("[pid]", f'{numero_aleatorio}')

    canal_normalizado = normalizar(canal)

    # Primero intentamos con el diccionario
    if canal_normalizado in diccionario:
        canal_epg = diccionario[canal_normalizado]["canal_epg"]
        imagen = diccionario[canal_normalizado]["imagen"]
        grupo = diccionario[canal_normalizado]["grupo"]
    else:
        canal = canal.replace("/", " ").replace("\\", " ").replace("-", " ")
        canal_epg = ""
        imagen = ""
        if tipo == "directos":
            grupo = "OTROS"
        if tipo == "pelis":
            grupo = "PELIS"
        if tipo == "webs":
            grupo = "IPTV"
    
    # Si hay valores originales del M3U, los usamos
    if tvg_id_orig is not None:
        canal_epg = tvg_id_orig
    if logo_orig is not None:
        imagen = logo_orig
    if grupo_orig is not None:
        grupo = grupo_orig

    # Si no hay nombre del canal, usar la URL como nombre
    canal = canal or url

    # Escribir en el archivo local
    f.write(f'#EXTINF:-1 tvg-id="{canal_epg}" tvg-logo="{imagen}" group-title="{grupo}",{canal}\n')
    f.write(f'{url}\n')

    # Escribir en el archivo remoto (si aplica)
    if url.startswith("acestream://"):
        acestream_id = url.replace("acestream://", "")
        if("[acestream_id]" in miHost):
            miHost=miHost.replace("[acestream_id]", f'{acestream_id}')
        f1.write(f'#EXTINF:-1 tvg-id="{canal_epg}" tvg-logo="{imagen}" group-title="{grupo}",{canal}\n')
        f1.write(f'{miHost}\n')
    else:
        f1.write(f'#EXTINF:-1 tvg-id="{canal_epg}" tvg-logo="{imagen}" group-title="{grupo}",{canal}\n')
        f1.write(f'{url}\n')

def scrapIptv(urls, folder):
    # Crear instancia del gestor de scrapers
    manager = ScraperManager()
    
    # Registrar scrapers para diferentes sitios
    manager.register_scraper("rojadirecta", RojadirectaScraper)
    manager.register_scraper("daddylive", DaddyLiveScraper)
    
    
    # Hacer scraping de todas las URLs
    results = manager.scrape_multiple_urls(urls)
    
    # Exportar resultados
    #manager.export_to_json("all_events.json")
    #manager.export_to_csv(f"{folder}/all_events.csv")
    manager.export_to_m3u(f"{folder}/web_iptv.m3u")
    
