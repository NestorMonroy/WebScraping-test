from bs4 import BeautifulSoup
from .network import make_request
from .content_processor import extract_content, analyze_content
from .file_handler import create_folder_from_url, save_content_as_text
from .exceptions import ContentExtractionError, NetworkError
from .utils import print_progress


def extract_specific_article_content(url):
    print_progress(0, 5, "Iniciando extracción de contenido...")
    try:
        response = make_request(url)
        if response is None:
            raise NetworkError("No se pudo obtener respuesta del servidor")

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

        if not content:
            raise ContentExtractionError(f"No se encontró el contenido del artículo en {url}")

        extracted_content = extract_content(content)
        if not extracted_content:
            raise ContentExtractionError("No se pudo extraer el contenido del artículo")

        if not callable(analyze_content):
            raise TypeError("analyze_content no es una función válida")

        analyzed_content = analyze_content(content)
        if analyzed_content is None:
            raise ContentExtractionError("No se pudo analizar el contenido del artículo")

        folder_name = create_folder_from_url(url)
        file_path = save_content_as_text(str(content), folder_name, url)

        return {
            'content': extracted_content,
            'url': url,
            'analysis': analyzed_content,
            'saved_file_path': file_path
        }
    except NetworkError as e:
        print(f"Error de red: {e}")
    except ContentExtractionError as e:
        print(f"Error de extracción de contenido: {e}")
    except TypeError as e:
        print(f"Error de tipo: {e}")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

    return None