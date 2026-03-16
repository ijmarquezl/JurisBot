from abc import ABC, abstractmethod
from typing import List

class DocumentInfo:
    def __init__(self, title: str, format: str, url: str):
        self.title = title
        self.format = format
        self.url = url

class BaseScraper(ABC):
    """Clase base para todos los scrapers de documentos legales"""
    
    BASE_URL: str = ""
    
    @abstractmethod
    def scrape(self) -> List[DocumentInfo]:
        """Obtiene una lista de documentos de la fuente"""
        pass
        
class MockScraper(BaseScraper):
    def scrape(self) -> List[DocumentInfo]:
        return [DocumentInfo(title="Ley Mock", format="pdf", url="http://mock")]
