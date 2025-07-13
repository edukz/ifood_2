"""
Scraper paralelo de restaurantes
"""
from colorama import Fore
from src.utils.logger import get_logger
import psutil
import threading

class ParallelRestaurants:
    def __init__(self):
        self.logger = get_logger()
        self.max_workers = 5
        self.checkpoint_interval = 100
    
    def show_system_info(self):
        """Mostrar informações do sistema"""
        print(f"\n{Fore.CYAN}INFORMAÇÕES DO SISTEMA:")
        print(f"{Fore.WHITE}CPU: {psutil.cpu_percent()}%")
        print(f"{Fore.WHITE}RAM: {psutil.virtual_memory().percent}%")
        print(f"{Fore.WHITE}Workers: {self.max_workers}")
        print(f"{Fore.WHITE}Checkpoint: a cada {self.checkpoint_interval} registros\n")
    
    def run(self):
        """Executar scraping paralelo de restaurantes"""
        print(f"\n{Fore.YELLOW}Iniciando scraping paralelo de restaurantes...")
        self.show_system_info()
        self.logger.info("Iniciando scraping paralelo de restaurantes")
        # TODO: Implementar lógica de scraping paralelo
        input(f"\n{Fore.GREEN}Funcionalidade em desenvolvimento. ENTER para continuar...")