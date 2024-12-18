import os
import time
import json
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

# Configuración
TAGS = ["bondage", "anal", "bdsm", "milf", "futanaria", "anal-sex", "big-tits", "busty-milf", "big-cock"]  # Lista de tags para recorrer
BASE_URL = "https://www.xvideos.com/tags/{}/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
OUTPUT_FOLDER = "images"
JSON_FILE = "metadata.json"
MAX_PAGES = 15  # Limitar el scraping a 15 páginas

# Crear carpeta para guardar imágenes
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Función para descargar imágenes
def download_image(url, save_path):
    try:
        response = requests.get(url, headers=HEADERS, stream=True)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            image.save(save_path)
            print(f"Imagen guardada: {save_path}")
        else:
            print(f"Error al descargar la imagen: {url}")
    except Exception as e:
        print(f"Error al guardar la imagen: {e}")

# Función para extraer etiquetas desde la página del video
def get_video_tags(video_url):
    try:
        response = requests.get(video_url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Error al acceder a la URL del video: {video_url}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Buscar las etiquetas (tags) en la página del video
        tag_elements = soup.find_all("a", class_="is-keyword")
        tags = [tag.text.strip() for tag in tag_elements]

        # Devolver solo los nombres de los tags, sin las URLs
        return tags
    except Exception as e:
        print(f"Error al extraer etiquetas: {e}")
        return []

# Función para leer los metadatos existentes
def read_existing_metadata():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Función para guardar metadatos en el archivo JSON
def save_metadata(metadata):
    with open(JSON_FILE, "w", encoding="utf-8") as json_file:
        json.dump(metadata, json_file, ensure_ascii=False, indent=4)
        print(f"Metadatos guardados en {JSON_FILE}")

# Función principal para hacer scraping
def scrape_videos(tag, page_number=1):
    if page_number > MAX_PAGES:
        print(f"Llegamos al límite de {MAX_PAGES} páginas, cambiando de tag.")
        return

    current_url = BASE_URL.format(tag) + str(page_number)
    print(f"Scrapeando página {page_number} de {tag}: {current_url}")

    response = requests.get(current_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error al acceder a la página. Código: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    videos = soup.find_all("div", class_="thumb-block")

    # Leer metadatos existentes
    existing_metadata = read_existing_metadata()

    for video in videos:
        try:
            # Extraer título
            title_tag = video.find("p", class_="title")
            if not title_tag:
                continue
            title = title_tag.text.strip()
            sanitized_title = "".join(c for c in title if c.isalnum() or c in " _-").rstrip()

            # Extraer URL del thumbnail
            thumbnail = video.find("img")
            if not thumbnail or "data-src" not in thumbnail.attrs:
                continue
            thumbnail_url = thumbnail["data-src"]

            # Extraer URL del video
            link = video.find("a", href=True)
            if not link:
                continue
            video_url = f"https://www.xvideos.com{link['href']}"

            # Descargar la imagen
            image_path = os.path.join(OUTPUT_FOLDER, f"{sanitized_title}.jpg")
            download_image(thumbnail_url, image_path)

            # Extraer etiquetas desde la página del video
            tags = get_video_tags(video_url)

            # Agregar nuevo metadato
            existing_metadata.append({
                "file_name": f"{sanitized_title}.jpg",
                "title": title,
                "tags": tags,
                "video_url": video_url
            })

            # Espera fija de 5 milisegundos
            wait_time = 0.005
            print(f"Esperando {wait_time * 1000:.0f} milisegundos...")
            time.sleep(wait_time)

        except Exception as e:
            print(f"Error al procesar un video: {e}")

    # Guardar los metadatos actualizados
    save_metadata(existing_metadata)

    # Pasar a la siguiente página
    scrape_videos(tag, page_number + 1)

# Ejecutar el script
if __name__ == "__main__":
    for tag in TAGS:
        scrape_videos(tag)
