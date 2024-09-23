import os
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from .utils import print_progress


def create_folder_from_url(url):
    domain = urlparse(url).netloc
    folder_name = re.sub(r'[^\w\-_\. ]', '_', domain)
    os.makedirs(folder_name, exist_ok=True)
    return folder_name


def save_content_as_text(content, folder_name, url):
    print_progress(5, 5, "Guardando contenido como texto plano...")
    file_name = re.sub(r'[^\w\-_\. ]', '_', url.split('/')[-1]) + '.txt'
    file_path = os.path.join(folder_name, file_name)

    soup = BeautifulSoup(content, 'html.parser')

    for script in soup(["script", "style"]):
        script.decompose()

    text_content = soup.get_text()

    lines = (line.strip() for line in text_content.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text_content = '\n'.join(chunk for chunk in chunks if chunk)

    text_content = f"Contenido extraído de: {url}\n\n" + text_content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text_content)

    return file_path
