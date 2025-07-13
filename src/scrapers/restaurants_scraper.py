"""
Scraper de restaurantes
"""
from colorama import Fore
from src.utils.logger import get_logger

class RestaurantsScraper:
    def __init__(self):
        self.logger = get_logger()
    
    def scrape_basic_data(self):
        """Scraping de dados básicos dos restaurantes"""
        print(f"\n{Fore.YELLOW}Extraindo dados básicos de restaurantes...")
        print(f"{Fore.WHITE}  - Nome")
        print(f"{Fore.WHITE}  - Nota")
        print(f"{Fore.WHITE}  - Tempo de entrega")
        print(f"{Fore.WHITE}  - Taxa de entrega")
        self.logger.info("Iniciando scraping de dados básicos de restaurantes")
        # TODO: Implementar lógica de scraping
        input(f"\n{Fore.GREEN}Funcionalidade em desenvolvimento. ENTER para continuar...")