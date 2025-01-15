from cryptoLink import decrypt
from urllib.parse import urlparse
import re
import random
import requests
import csv

def generar_m3u_remoto(miHost):

    # Expresión regular para encontrar hashes de 40 caracteres (acestream)
    hash_pattern = re.compile(r'[a-fA-F0-9]{40}')

    input_file_path = "resources/default.m3u"
    output_file_path = "resources/default_remote.m3u"
    numero_aleatorio = random.randint(1, 10000)

    with open(input_file_path, 'r', encoding='utf-8') as infile, \
         open(output_file_path, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            line = line.strip()
            if line.startswith("#"):
                # Copiar las líneas de metadatos (comentarios) sin cambios
                outfile.write(line + "\n")
            else:
                # Buscar un hash en la línea
                match = hash_pattern.search(line)
                if match:
                    # Reemplazar el enlace con el formato nuevo
                    hash_value = match.group()
                    parsed_url = urlparse(f"http://{miHost}")  # Se requiere un esquema para urlparse
                    hostname = parsed_url.hostname
                    new_url = f"http://{hostname}:6878/ace/manifest.m3u8?id={hash_value}&pid={numero_aleatorio}"                    
                    outfile.write(new_url + "\n")
                else:
                    # Si no hay hash, dejar la línea sin cambios
                    outfile.write(line + "\n")

def decode_default_url():
    
    # URL de la que quieres obtener los datos
    url = b'\xb6L\x18\xae#^+\xad@\x02\t\xbf\x8d\xa9V\x8a\x021\xa3\xda>c\xde\x12\xe8::\xbc\xb4\xd2x'
    iv = b'[\xb0E\x9a-\x98.\xd6\xe9>-\x1a$4`}'
    key = b'h\x03\xf5\x0er\xa7\xf7\x8b\xfd\xbaa\x08\r,\x02\x08\x82\n\xcdJ^\xef\xed\xb7\xa88\xca\xcd0\xed\x98l'
    
    # Realizar la solicitud HTTP
    return decrypt(url, key, iv)


def generar_m3u_from_url(miHost, urls):
    # Ruta del diccionario CSV
    csv_file = "resources/dictionary.csv"
    # Archivos de salida
    output_file = "resources/default.m3u"
    output_file_remote = "resources/default_remote.m3u"
    
    # Cargar el diccionario desde el CSV
    diccionario = {}
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            canal, canal_epg, imagen, grupo = row
            diccionario[canal] = {"canal_epg": canal_epg, "imagen": imagen, "grupo": grupo}

    # Lista para almacenar enlaces únicos
    enlaces_unicos = set()

    with open(output_file, "w") as f, open(output_file_remote, "w") as f1:
        for url in urls:
            try:
                # Realizar una solicitud HEAD para comprobar el tipo de contenido
                response_head = requests.head(url, allow_redirects=True, timeout=100)
                content_type = response_head.headers.get("Content-Type", "").lower()
                
                # Si el tipo de contenido indica un M3U
                if "mpegurl" in content_type or "m3u" in content_type:
                    # Descargar el contenido y procesarlo como archivo M3U
                    response = requests.get(url, timeout=100)
                    if response.status_code == 200:
                        m3u_content = response.text
                        canal_actual = None
                        for line in m3u_content.splitlines():
                            line = line.strip()
                            if line.startswith("#EXTINF"):
                                # Extraer el nombre del canal de la línea #EXTINF
                                match = re.search(r',(.+)$', line)
                                if match:
                                    canal_actual = match.group(1).strip()
                            elif line.startswith("http") or line.startswith("acestream:"):  # Enlace de streaming
                                if line not in enlaces_unicos:
                                    enlaces_unicos.add(line)
                                    escribir_m3u(f, f1, line, diccionario, miHost, canal_actual)
                else:
                    # Procesar como una web normal (tu lógica original)
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        content = response.text
                        matches = re.findall(r'{"name": "(.*?)", "url": "acestream://([a-f0-9]{40})"}', content)
                        for canal, acestream_url in matches:
                            if acestream_url not in enlaces_unicos:
                                enlaces_unicos.add(acestream_url)
                                escribir_m3u(f, f1, f"acestream://{acestream_url}", diccionario, miHost, canal)
            except Exception as e:
                print(f"Error procesando URL {url}: {e}")

    print(f"Archivos generados: {output_file}, {output_file_remote}")


def escribir_m3u(f, f1, url, diccionario, miHost, canal=None):
    """
    Escribe una línea en los archivos M3U con los valores del diccionario, si aplica.
    """
    numero_aleatorio = random.randint(1, 10000)

    if canal in diccionario:
        canal_epg = diccionario[canal]["canal_epg"]
        imagen = diccionario[canal]["imagen"]
        grupo = diccionario[canal]["grupo"]
    else:
        canal_epg = ""
        imagen = ""
        grupo = "OTROS"

    # Si no hay nombre del canal, usar la URL como nombre
    canal = canal or url

    # Escribir en el archivo local
    f.write(f'#EXTINF:-1 tvg-id="{canal_epg}" tvg-logo="{imagen}" group-title="{grupo}",{canal}\n')
    f.write(f'{url}\n')

    # Escribir en el archivo remoto (si aplica)
    if url.startswith("acestream://"):
        acestream_id = url.replace("acestream://", "")
        parsed_url = urlparse(f"http://{miHost}")
        hostname = parsed_url.hostname
        f1.write(f'#EXTINF:-1 tvg-id="{canal_epg}" tvg-logo="{imagen}" group-title="{grupo}",{canal}\n')
        f1.write(f'http://{hostname}:6878/ace/manifest.m3u8?id={acestream_id}&pid={numero_aleatorio}\n')
    else:
        f1.write(f'#EXTINF:-1 tvg-id="{canal_epg}" tvg-logo="{imagen}" group-title="{grupo}",{canal}\n')
        f1.write(f'{url}\n')



    
def generar_m3u(miHost):
    
    # URL de la que quieres obtener los datos
    url = b'\xb6L\x18\xae#^+\xad@\x02\t\xbf\x8d\xa9V\x8a\x021\xa3\xda>c\xde\x12\xe8::\xbc\xb4\xd2x'
    iv = b'[\xb0E\x9a-\x98.\xd6\xe9>-\x1a$4`}'
    key = b'h\x03\xf5\x0er\xa7\xf7\x8b\xfd\xbaa\x08\r,\x02\x08\x82\n\xcdJ^\xef\xed\xb7\xa88\xca\xcd0\xed\x98l'
    numero_aleatorio = random.randint(1, 10000)
    
    # Realizar la solicitud HTTP
    response = requests.get(decrypt(url, key, iv))
    if response.status_code == 200:
        content = response.text
    
        # Expresión regular para extraer el nombre y el enlace acestream
        matches = re.findall(r'{"name": "(.*?)", "url": "acestream://([a-f0-9]{40})"}', content)
    
        
        # Cargar el diccionario desde el CSV
        csv_file = "resources/dictionary.csv"  # Sustituye por la ruta a tu CSV
        diccionario = {}
    
        with open(csv_file, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                canal, canal_epg, imagen, grupo = row  # "canal","canal_epg","imagen","grupo" son las columnas del CSV
                diccionario[canal] = {"canal_epg": canal_epg, "imagen": imagen, "grupo": grupo}
    
            # Generar el archivo de salida con el formato especificado
            output_file = "resources/default.m3u"
            output_file_remote = "resources/default_remote.m3u"
    
            with open(output_file, "w") as f, open(output_file_remote, "w") as f1:
                for canal, url in matches:
                    if canal in diccionario:
                        # Extraer valores del diccionario
                        canal_epg = diccionario[canal]["canal_epg"]
                        imagen = diccionario[canal]["imagen"]
                        grupo = diccionario[canal]["grupo"]
                    else:
                        canal_epg = ""
                        imagen = ""
                        grupo = "OTROS"
            
                    # Escribir en el archivo con el formato deseado
                    f.write(f'#EXTINF:-1 tvg-id="{canal_epg}" tvg-logo="{imagen}" group-title="{grupo}",{canal}\n')
                    f.write(f'acestream://{url}\n')


                    parsed_url = urlparse(f"http://{miHost}")  # Se requiere un esquema para urlparse
                    hostname = parsed_url.hostname
                    
                    f1.write(f'#EXTINF:-1 tvg-id="{canal_epg}" tvg-logo="{imagen}" group-title="{grupo}",{canal}\n')
                    f1.write(f'http://{hostname}:6878/ace/manifest.m3u8?id={url}&pid={numero_aleatorio}\n')
            
            print(f"Archivo generado: {output_file}")

