from .scraper import extract_specific_article_content
from .network import make_request
from .content_processor import extract_content, analyze_content
from .file_handler import create_folder_from_url, save_content_as_text
from .exceptions import WebScrapingError, NetworkError, ContentExtractionError
from .utils import print_progress

# Puedes definir __all__ para especificar qué se importa con "from package import *"
__all__ = [
    'extract_specific_article_content',
    'make_request',
    'extract_content',
    'analyze_content',
    'create_folder_from_url',
    'save_content_as_text',
    'WebScrapingError',
    'NetworkError',
    'ContentExtractionError',
    'print_progress'
]

__version__ = '1.0.0'
__author__ = 'Tu Nombre'
__description__ = 'Un paquete para web scraping y extracción de contenido'
