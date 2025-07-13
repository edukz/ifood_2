"""
Scraper de informações extras
"""
from colorama import Fore
from src.utils.logger import get_logger

class ExtraInfoScraper:
    def __init__(self):
        self.logger = get_logger()
    
    def scrape_extra(self):
        """Scraping de informações extras"""
        print(f"\n{Fore.YELLOW}Extraindo informações extras...")
        self.logger.info("Iniciando scraping de informações extras")
        # TODO: Implementar lógica de scraping
        input(f"\n{Fore.GREEN}Funcionalidade em desenvolvimento. ENTER para continuar...")