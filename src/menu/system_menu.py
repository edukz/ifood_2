"""
Menu de Sistema
"""
import os
from colorama import Fore, Back, Style
from src.config.config_manager import ConfigManager

class SystemMenu:
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def clear_screen(self):
        """Limpar tela"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        """Exibir cabeçalho"""
        self.clear_screen()
        print(f"{Fore.YELLOW}{'╔' + '═'*58 + '╗'}")
        print(f"{Fore.YELLOW}║{Fore.WHITE}{'CONFIGURAÇÕES DO SISTEMA':^58}{Fore.YELLOW}║")
        print(f"{Fore.YELLOW}║{Fore.CYAN}{'Personalização e ajustes gerais':^58}{Fore.YELLOW}║")
        print(f"{Fore.YELLOW}{'╚' + '═'*58 + '╝'}")
        print()
    
    def show_menu(self):
        """Exibir menu de sistema"""
        print(f"{Back.YELLOW}{Fore.BLACK} CONFIGURAÇÕES GERAIS {Style.RESET_ALL}")
        print()
        print(f"{Fore.CYAN}[1] {Fore.WHITE}Configurar regiões/cidades para scrap")
        print(f"{Fore.CYAN}[2] {Fore.WHITE}Definir intervalos entre requests")
        print(f"{Fore.CYAN}[3] {Fore.WHITE}Configurar proxies e user agents")
        print(f"{Fore.CYAN}[4] {Fore.WHITE}Ajustar timeouts e retries")
        print(f"{Fore.CYAN}[5] {Fore.WHITE}Configurar paths de output")
        print(f"{Fore.CYAN}[6] {Fore.WHITE}Ver configurações atuais")
        print(f"{Fore.CYAN}[7] {Fore.WHITE}Resetar configurações padrão")
        print()
        print(f"{Fore.RED}[0] {Fore.WHITE}Voltar ao menu principal")
        print(f"{Fore.YELLOW}{'─'*60}")
    
    def run(self):
        """Executar menu de sistema"""
        while True:
            self.show_header()
            self.show_menu()
            
            choice = input(f"\n{Fore.YELLOW}Escolha uma opção: {Style.RESET_ALL}")
            
            if choice == '0':
                break
            elif choice == '1':
                self.config_manager.configure_regions()
            elif choice == '2':
                self.config_manager.configure_intervals()
            elif choice == '3':
                self.config_manager.configure_proxies()
            elif choice == '4':
                self.config_manager.configure_timeouts()
            elif choice == '5':
                self.config_manager.configure_paths()
            elif choice == '6':
                self.config_manager.show_current_config()
            elif choice == '7':
                self.config_manager.reset_to_default()
            else:
                input(f"\n{Fore.RED}Opção inválida! ENTER para continuar...")