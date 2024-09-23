class WebScrapingError(Exception):
    """Clase base para excepciones en este módulo."""
    pass

class NetworkError(WebScrapingError):
    """Excepción lanzada por errores de red."""
    pass

class ContentExtractionError(WebScrapingError):
    """Excepción lanzada cuando no se puede extraer el contenido."""
    pass