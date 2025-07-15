"""
Menu de Scrapy Unitário
"""
import os
from colorama import Fore, Back, Style
from src.scrapers.categories_scraper import CategoriesScraper
from src.scrapers.restaurants_scraper import RestaurantsScraper
from src.scrapers.products_scraper import ProductsScraper
from src.scrapers.extra_info_scraper import ExtraInfoScraper

class ScrapyMenu:
    def __init__(self):
        self.categories_scraper = CategoriesScraper()
        self.restaurants_scraper = RestaurantsScraper()
        self.products_scraper = ProductsScraper()
        self.extra_info_scraper = ExtraInfoScraper()
    
    def clear_screen(self):
        """Limpar tela"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        """Exibir cabeçalho"""
        self.clear_screen()
        print(f"{Fore.BLUE}{'╔' + '═'*58 + '╗'}")
        print(f"{Fore.BLUE}║{Fore.CYAN}{'SCRAPY UNITÁRIO':^58}{Fore.BLUE}║")
        print(f"{Fore.BLUE}║{Fore.WHITE}{'Extração individual de dados':^58}{Fore.BLUE}║")
        print(f"{Fore.BLUE}{'╚' + '═'*58 + '╝'}")
        print()
    
    def show_menu(self):
        """Exibir menu de scrapy unitário"""
        print(f"{Back.CYAN}{Fore.BLACK} OPÇÕES DE SCRAPY {Style.RESET_ALL}")
        print()
        print(f"{Fore.YELLOW}[1] {Fore.WHITE}Scrapy de Categorias")
        print(f"    {Fore.CYAN}└─ {Fore.WHITE}Extrair metadados e URLs {Fore.MAGENTA}(dados completos)")
        print()
        print(f"{Fore.YELLOW}[2] {Fore.WHITE}Scrapy de Restaurantes")
        print(f"    {Fore.CYAN}└─ {Fore.WHITE}Dados básicos {Fore.MAGENTA}(nome, nota, tempo, taxa)")
        print()
        print(f"{Fore.YELLOW}[3] {Fore.WHITE}Scrapy de Produtos")
        print(f"    {Fore.CYAN}└─ {Fore.WHITE}Cardápio completo com preços")
        print()
        print(f"{Fore.YELLOW}[4] {Fore.WHITE}Scrapy de Informações Extras")
        print()
        print(f"{Fore.RED}[0] {Fore.WHITE}Voltar ao menu principal")
        print(f"{Fore.BLUE}{'─'*60}")
    
    def handle_categories(self):
        """Executar scrapy de categorias completo"""
        self.categories_scraper.extract_complete_data()
    
    def run(self):
        """Executar menu de scrapy unitário"""
        while True:
            self.show_header()
            self.show_menu()
            
            choice = input(f"\n{Fore.YELLOW}➤ {Fore.WHITE}Escolha uma opção: {Fore.CYAN}")
            
            if choice == '0':
                break
            elif choice == '1':
                self.handle_categories()
            elif choice == '2':
                self.restaurants_scraper.extract_restaurants_data()
            elif choice == '3':
                self.products_scraper.scrape_menu()
            elif choice == '4':
                self.extra_info_scraper.scrape_extra()
            else:
                print(f"\n{Back.RED}{Fore.WHITE} ERRO {Style.RESET_ALL} {Fore.RED}Opção inválida!")
                input(f"{Fore.YELLOW}Pressione ENTER para continuar...")