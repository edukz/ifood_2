"""
Menu principal do sistema
"""
import os
import sys
from colorama import init, Fore, Back, Style
from src.menu.scrapy_menu import ScrapyMenu
from src.menu.parallel_menu import ParallelMenu
from src.menu.database_menu import DatabaseMenu
from src.menu.system_menu import SystemMenu

class MainMenu:
    def __init__(self):
        init(autoreset=True)  # Inicializar colorama para Windows
        self.scrapy_menu = ScrapyMenu()
        self.parallel_menu = ParallelMenu()
        self.database_menu = DatabaseMenu()
        self.system_menu = SystemMenu()
    
    def clear_screen(self):
        """Limpar tela - compatível com Windows"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        """Exibir cabeçalho do sistema"""
        self.clear_screen()
        # Banner colorido
        print(f"{Fore.RED}{'╔' + '═'*58 + '╗'}")
        print(f"{Fore.RED}║{Fore.YELLOW}{'':^58}{Fore.RED}║")
        print(f"{Fore.RED}║{Fore.YELLOW}{'SISTEMA DE SCRAPING':^58}{Fore.RED}║")
        print(f"{Fore.RED}║{Fore.WHITE}{'─'*58}{Fore.RED}║")
        print(f"{Fore.RED}║{Fore.MAGENTA}{'i F O O D':^58}{Fore.RED}║")
        print(f"{Fore.RED}║{Fore.YELLOW}{'':^58}{Fore.RED}║")
        print(f"{Fore.RED}{'╚' + '═'*58 + '╝'}")
        print()
    
    def show_menu(self):
        """Exibir opções do menu principal"""
        print(f"{Back.GREEN}{Fore.BLACK} MENU PRINCIPAL {Style.RESET_ALL}")
        print()
        print(f"{Fore.CYAN}[1] {Fore.WHITE}Scrapy Unitário {Fore.YELLOW}➜ {Fore.WHITE}Extração individual")
        print(f"{Fore.CYAN}[2] {Fore.WHITE}Scrapy Paralelo {Fore.YELLOW}➜ {Fore.WHITE}Extração em massa")
        print(f"{Fore.CYAN}[3] {Fore.WHITE}Banco de Dados {Fore.GREEN}(DuckDB) {Fore.YELLOW}➜ {Fore.WHITE}Gerenciar dados")
        print(f"{Fore.CYAN}[4] {Fore.WHITE}Sistema {Fore.YELLOW}➜ {Fore.WHITE}Configurações gerais")
        print()
        print(f"{Fore.RED}[0] {Fore.WHITE}Sair do sistema")
        print(f"{Fore.MAGENTA}{'─'*60}")
    
    def run(self):
        """Executar loop principal do menu"""
        while True:
            try:
                self.show_header()
                self.show_menu()
                
                choice = input(f"\n{Fore.YELLOW}➤ {Fore.WHITE}Escolha uma opção: {Fore.CYAN}")
                
                if choice == '0':
                    self.clear_screen()
                    print(f"{Fore.GREEN}{'─'*60}")
                    print(f"{Fore.YELLOW}{'Obrigado por usar o sistema!':^60}")
                    print(f"{Fore.WHITE}{'Até a próxima!':^60}")
                    print(f"{Fore.GREEN}{'─'*60}\n")
                    sys.exit(0)
                elif choice == '1':
                    self.scrapy_menu.run()
                elif choice == '2':
                    self.parallel_menu.run()
                elif choice == '3':
                    self.database_menu.run()
                elif choice == '4':
                    self.system_menu.run()
                else:
                    print(f"\n{Back.RED}{Fore.WHITE} ERRO {Style.RESET_ALL} {Fore.RED}Opção inválida!")
                    input(f"{Fore.YELLOW}Pressione ENTER para continuar...")
            
            except KeyboardInterrupt:
                print(f"\n\n{Back.YELLOW}{Fore.BLACK} ATENÇÃO {Style.RESET_ALL} {Fore.YELLOW}Operação cancelada!")
                input(f"{Fore.WHITE}Pressione ENTER para continuar...")
            except Exception as e:
                print(f"\n{Back.RED}{Fore.WHITE} ERRO {Style.RESET_ALL} {Fore.RED}{str(e)}")
                input(f"{Fore.YELLOW}Pressione ENTER para continuar...")