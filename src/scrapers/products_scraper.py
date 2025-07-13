"""
Scraper de produtos
"""
from colorama import Fore
from src.utils.logger import get_logger

class ProductsScraper:
    def __init__(self):
        self.logger = get_logger()
    
    def scrape_menu(self):
        """Scraping do cardápio completo"""
        print(f"\n{Fore.YELLOW}Extraindo cardápio completo...")
        print(f"{Fore.WHITE}  - Produtos")
        print(f"{Fore.WHITE}  - Preços")
        print(f"{Fore.WHITE}  - Descrições")
        self.logger.info("Iniciando scraping de produtos/cardápio")
        # TODO: Implementar lógica de scraping
        input(f"\n{Fore.GREEN}Funcionalidade em desenvolvimento. ENTER para continuar...")