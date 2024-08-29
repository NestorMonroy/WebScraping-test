import requests
from bs4 import BeautifulSoup
import re
import json

def extract_headers(soup):
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
    toc = []
    for header in headers:
        toc.append({
            'level': header['level'],
            'text': header['text'],
            'link': f"#{header['id']}" if header['id'] else ''
        })
    return toc

def extract_content(element):
    # Implementa la lógica para extraer el contenido del elemento
    return element.get_text(strip=True)

def analyze_content(content, url):
    # Implementa la lógica para analizar el contenido
    # Por ejemplo, contar palabras, identificar temas principales, etc.
    word_count = len(content.get_text(strip=True).split())
    return {
        'word_count': word_count,
        # Agrega más análisis aquí
    }

def structure_overview(soup):
    # Implementa la lógica para proporcionar una visión general de la estructura de la página
    return {tag.name: len(soup.find_all(tag.name)) for tag in soup.find_all()}

def extract_specific_article_content(url):
    """Extrae el contenido específico de la estructura del artículo dado con mejor manejo de errores."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraer encabezados y crear tabla de contenidos
        headers = extract_headers(soup)
        toc = create_table_of_contents(headers)

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
            return {
                'content': extracted_content,
                'url': url,
                'analysis': analyzed_content,
                'headers': headers,
                'table_of_contents': toc
            }
        else:
            print(f"No se encontró el contenido del artículo en {url}")
            print("Estructura de la página:")
            print(json.dumps(structure_overview(soup), indent=2))
            return None
    except requests.RequestException as e:
        print(f"Error al acceder a {url}: {e}")
        return None

# Ejemplo de uso
if __name__ == "__main__":
    url = "https://blog.csdn.net/qq877507054/article/details/60143099"
    result = extract_specific_article_content(url)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("No se pudo extraer el contenido del artículo.")