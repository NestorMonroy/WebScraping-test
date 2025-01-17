import os, time, random, re, json, requests, html
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

# Lista de User-Agents para rotar
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def add_delay():
    delay = random.uniform(1, 3)  # Delay aleatorio entre 1 y 3 segundos
    time.sleep(delay)

def make_request(url):
    headers = {'User-Agent': get_random_user_agent()}
    add_delay()
    return requests.get(url, headers=headers, timeout=10)

def extract_headers(soup):
    print_progress(1, 7, "Extrayendo encabezados...")
    headers = []
    for header in soup.find_all(re.compile('^h[1-6]$')):
        level = int(header.name[1])
        headers.append({
            'level': level,
            'text': header.get_text(strip=True),
            'id': header.get('id', '')
        })
    return headers

def create_table_of_contents(headers):
    print_progress(2, 7, "Creando tabla de contenidos...")
    toc = []
    for header in headers:
        toc.append({
            'level': header['level'],
            'text': header['text'],
            'link': f"#{header['id']}" if header['id'] else ''
        })
    return toc

def extract_content(content):
    print_progress(3, 7, "Extrayendo contenido principal...")
    return content.get_text()

def analyze_content(content, url):
    print_progress(4, 7, "Analizando contenido...")
    word_count = len(content.get_text(strip=True).split())
    return {
        'word_count': word_count,
        "links": len(content.find_all('a')),
    }

def structure_overview(soup):
    # Implementa la lógica para proporcionar una visión general de la estructura de la página
    # return {tag.name: len(soup.find_all(tag.name)) for tag in soup.find_all()}
    return {
        "title": soup.title.string if soup.title else "No title",
        "meta_tags": len(soup.find_all('meta')),
        # Agrega más información estructural según sea necesario
    }

def create_folder_from_url(url):
    print_progress(5, 7, "Creando carpeta para guardar contenido...")
    domain = urlparse(url).netloc
    folder_name = re.sub(r'[^\w\-_\. ]', '_', domain)
    os.makedirs(folder_name, exist_ok=True)
    img_folder = os.path.join(folder_name, 'img')
    os.makedirs(img_folder, exist_ok=True)
    return folder_name, img_folder


# def download_image(img_url, img_folder, img_count, total_images):
#     try:
#         response = requests.get(img_url, stream=True)
#         response.raise_for_status()
#
#         img = Image.open(BytesIO(response.content))
#         img_name = f"image_{img_count}.jpg"
#         img_path = os.path.join(img_folder, img_name)
#
#         img.convert('RGB').save(img_path, 'JPEG')
#         print_progress(7, 7, f"Descargando imagen {img_count} de {total_images}...")
#         return img_path
#     except Exception as e:
#         print(f"Error al descargar la imagen {img_url}: {e}")
#         return None

# def download_image(img_url, img_folder):
#     try:
#         response = make_request(img_url)
#         if response.status_code == 200:
#             img_name = f"image_{hash(img_url)}.jpg"
#             img_path = os.path.join(img_folder, img_name)
#
#             img = Image.open(BytesIO(response.content))
#             img = img.convert('RGB')
#             img.save(img_path, 'JPEG')
#
#             return img_path
#     except Exception as e:
#         print(f"Error al descargar la imagen {img_url}: {e}")
#     return None

def extract_and_download_images(soup, base_url, img_folder):
    print_progress(7, 7, "Iniciando descarga de imágenes...")
    downloaded_images = []
    images = soup.find_all('img')
    total_images = len(images)
    for i, img in enumerate(images, 1):
        img_url = img.get('src')
        if img_url:
            img_url = urljoin(base_url, img_url)
            downloaded_file = download_image(img_url, img_folder, i, total_images)
            if downloaded_file:
                downloaded_images.append(downloaded_file)
                # Actualizar la ruta de la imagen en el HTML
                img['src'] = os.path.relpath(downloaded_file, os.path.dirname(img_folder))
        report_progress("Descarga de imágenes", i, total_images)
    return downloaded_images


def clean_html_content(content):
    # Decodificar entidades HTML
    content = html.unescape(content)
    # Eliminar scripts y estilos
    soup = BeautifulSoup(content, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()
    return str(soup)

def save_content_as_html(content, folder_name, url):
    print_progress(6, 7, "Guardando contenido como HTML...")
    file_name = re.sub(r'[^\w\-_\. ]', '_', url.split('/')[-1]) + '.html'
    file_path = os.path.join(folder_name, file_name)

    # Limpiar el contenido HTML
    cleaned_content = clean_html_content(content)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Artículo extraído de {url}</title>
    </head>
    <body>
        <h1>Artículo extraído de <a href="{url}">{url}</a></h1>
        <div class="article-content">
            {cleaned_content}
        </div>
    </body>
    </html>
    """

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return file_path


def extract_specific_article_content(url):
    print_progress(0, 7, "Iniciando extracción de contenido...")
    try:
        response = make_request(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        selectors = [
            ('div', 'article_content'),
            ('div', 'htmledit_views'),
            ('article', None),
            ('div', 'post-content'),
            ('div', 'entry-content')
        ]

        content = None
        for tag, class_name in selectors:
            if class_name:
                content = soup.find(tag, class_=class_name)
            else:
                content = soup.find(tag)
            if content:
                break

        if content:
            extracted_content = extract_content(content)
            analyzed_content = analyze_content(content, url)

            folder_name, img_folder = create_folder_from_url(url)

            # Descargar imágenes
            images = content.find_all('img')
            total_images = len(images)
            for i, img in enumerate(images, 1):
                img_url = urljoin(url, img.get('src', ''))
                img_path = download_image(img_url, img_folder)
                if img_path:
                    img['src'] = os.path.relpath(img_path, folder_name)
                report_progress("Descarga de imágenes", i, total_images)
                add_delay()  # Añadir delay entre descargas de imágenes

            file_path = save_content_as_html(str(content), folder_name, url)

            return {
                'content': extracted_content,
                'url': url,
                'analysis': analyzed_content,
                'saved_file_path': file_path
            }
        else:
            print(f"No se encontró el contenido del artículo en {url}")
            print("Estructura de la página:")
            print(json.dumps(structure_overview(soup), indent=2))
            return None
    except requests.RequestException as e:
        print(f"Error al acceder a {url}: {e}")
        return None

def report_progress(message, current, total):
    progress = (current / total) * 100
    print(f"{message}: {progress:.2f}% completado")

def print_progress(step, total_steps, message):
    """Imprime el progreso actual del proceso."""
    print(f"[{step}/{total_steps}] {message}")



# Ejemplo de uso
if __name__ == "__main__":
    url = "https://blog.csdn.net/qq877507054/article/details/60143099"
    result = extract_specific_article_content(url)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("No se pudo extraer el contenido del artículo")