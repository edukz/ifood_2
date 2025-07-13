"""
Menu de Scrapy Paralelo
"""
import os
from colorama import Fore, Back, Style
from src.scrapers.parallel.parallel_restaurants import ParallelRestaurants
from src.scrapers.parallel.parallel_products import ParallelProducts
from src.scrapers.parallel.parallel_extra import ParallelExtra

class ParallelMenu:
    def __init__(self):
        self.parallel_restaurants = ParallelRestaurants()
        self.parallel_products = ParallelProducts()
        self.parallel_extra = ParallelExtra()
    
    def clear_screen(self):
        """Limpar tela"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        """Exibir cabeçalho"""
        self.clear_screen()
        print(f"{Fore.GREEN}{'╔' + '═'*58 + '╗'}")
        print(f"{Fore.GREEN}║{Fore.YELLOW}{'SCRAPY PARALELO':^58}{Fore.GREEN}║")
        print(f"{Fore.GREEN}║{Fore.WHITE}{'Extração em massa com alta performance':^58}{Fore.GREEN}║")
        print(f"{Fore.GREEN}{'╚' + '═'*58 + '╝'}")
        print()
    
    def show_menu(self):
        """Exibir menu de scrapy paralelo"""
        print(f"{Back.GREEN}{Fore.BLACK} OPÇÕES DE SCRAPY PARALELO {Style.RESET_ALL}")
        print()
        print(f"{Fore.CYAN}[1] {Fore.WHITE}Scrapy paralelo de Restaurantes")
        print(f"{Fore.CYAN}[2] {Fore.WHITE}Scrapy paralelo de Produtos")
        print(f"{Fore.CYAN}[3] {Fore.WHITE}Scrapy paralelo de Informações Extras")
        print()
        print(f"{Back.YELLOW}{Fore.BLACK} CONSIDERAÇÕES TÉCNICAS {Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  ▸ {Fore.WHITE}Pool de conexões otimizado para Windows")
        print(f"{Fore.YELLOW}  ▸ {Fore.WHITE}Monitoramento de memória RAM")
        print(f"{Fore.YELLOW}  ▸ {Fore.WHITE}Sistema de retry automático")
        print(f"{Fore.YELLOW}  ▸ {Fore.WHITE}Logs detalhados por thread")
        print(f"{Fore.YELLOW}  ▸ {Fore.WHITE}Checkpoint system")
        print()
        print(f"{Fore.RED}[0] {Fore.WHITE}Voltar ao menu principal")
        print(f"{Fore.GREEN}{'─'*60}")
    
    def run(self):
        """Executar menu de scrapy paralelo"""
        while True:
            self.show_header()
            self.show_menu()
            
            choice = input(f"\n{Fore.YELLOW}➤ {Fore.WHITE}Escolha uma opção: {Fore.CYAN}")
            
            if choice == '0':
                break
            elif choice == '1':
                self.parallel_restaurants.run()
            elif choice == '2':
                self.parallel_products.run()
            elif choice == '3':
                self.parallel_extra.run()
            else:
                print(f"\n{Back.RED}{Fore.WHITE} ERRO {Style.RESET_ALL} {Fore.RED}Opção inválida!")
                input(f"{Fore.YELLOW}Pressione ENTER para continuar...")