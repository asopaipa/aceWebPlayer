import re
import requests
import csv

def generar_m3u():
    
    # URL de la que quieres obtener los datos
    url = 'https://ipfs.io/ipns/elcano.top'
    
    # Realizar la solicitud HTTP
    response = requests.get(url)
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
    
            with open(output_file, "w") as f:
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
            
            print(f"Archivo generado: {output_file}")

