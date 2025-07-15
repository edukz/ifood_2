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
from src.database.db_manager import DatabaseManager
from datetime import datetime

class MainMenu:
    def __init__(self):
        init(autoreset=True)  # Inicializar colorama para Windows
        self.scrapy_menu = ScrapyMenu()
        self.parallel_menu = ParallelMenu()
        self.database_menu = DatabaseMenu()
        self.system_menu = SystemMenu()
        self.db_manager = DatabaseManager()
    
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
        
        # Exibir dashboard com estatísticas
        self.show_dashboard()
    
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
    
    def get_statistics(self):
        """Obter estatísticas do banco de dados"""
        stats = {
            'categorias': 0,
            'restaurantes': 0,
            'produtos': 0,
            'ultima_coleta': 'Nunca',
            'total_registros': 0,
            'tamanho_db': '0 KB'
        }
        
        try:
            conn = self.db_manager._get_connection()
            
            # Contar categorias
            try:
                result = conn.execute("SELECT COUNT(*) FROM categories").fetchone()
                stats['categorias'] = result[0] if result else 0
            except:
                pass
            
            # Contar restaurantes
            try:
                result = conn.execute("SELECT COUNT(*) FROM restaurants").fetchone()
                stats['restaurantes'] = result[0] if result else 0
            except:
                pass
            
            # Contar produtos
            try:
                result = conn.execute("SELECT COUNT(*) FROM products").fetchone()
                stats['produtos'] = result[0] if result else 0
            except:
                pass
            
            # Obter última coleta
            try:
                result = conn.execute("""
                    SELECT MAX(created_at) as ultima_data 
                    FROM (
                        SELECT created_at FROM categories WHERE created_at IS NOT NULL
                        UNION ALL
                        SELECT created_at FROM restaurants WHERE created_at IS NOT NULL
                        UNION ALL  
                        SELECT created_at FROM products WHERE created_at IS NOT NULL
                    )
                """).fetchone()
                
                if result and result[0]:
                    # Formatar data
                    data = datetime.fromisoformat(str(result[0]))
                    stats['ultima_coleta'] = data.strftime('%d/%m/%Y %H:%M')
            except:
                pass
            
            # Total de registros
            stats['total_registros'] = stats['categorias'] + stats['restaurantes'] + stats['produtos']
            
            # Tamanho do banco
            if os.path.exists(self.db_manager.db_path):
                size = os.path.getsize(self.db_manager.db_path)
                if size < 1024:
                    stats['tamanho_db'] = f"{size} B"
                elif size < 1024 * 1024:
                    stats['tamanho_db'] = f"{size / 1024:.1f} KB"
                else:
                    stats['tamanho_db'] = f"{size / (1024 * 1024):.1f} MB"
            
            conn.close()
            
        except Exception as e:
            # Em caso de erro, retornar estatísticas vazias
            pass
        
        return stats
    
    def show_dashboard(self):
        """Exibir dashboard com informações rápidas"""
        stats = self.get_statistics()
        
        # Dashboard com estatísticas - aumentado para 70 chars para acomodar números maiores
        print(f"{Back.BLUE}{Fore.WHITE} DASHBOARD {Style.RESET_ALL}")
        print(f"{Fore.CYAN}┌{'─'*70}┐")
        
        # Linha 1: Contadores principais
        # Total interno: 68 chars (70 - 2 bordas)
        # Divisão: 22 + 22 + 22 = 66 chars + 2 separadores = 68
        cat_text = f"📂 Categorias: {stats['categorias']:>6}"      # Até 999.999
        rest_text = f"🍴 Restaurantes: {stats['restaurantes']:>6}"  # Até 999.999
        prod_text = f"🛒 Produtos: {stats['produtos']:>6}"         # Até 999.999
        
        print(f"{Fore.CYAN}│{Fore.YELLOW}{cat_text:<22}{Fore.CYAN}│{Fore.YELLOW}{rest_text:<22}{Fore.CYAN}│{Fore.YELLOW}{prod_text:<22}{Fore.CYAN}│")
        
        # Linha separadora
        print(f"{Fore.CYAN}├{'─'*70}┤")
        
        # Linha 2: Informações adicionais  
        # Divisão: 34 + 34 = 68 chars + 1 separador = 69, ajustar para 68
        total_text = f"📈 Total de Registros: {stats['total_registros']:>8}"  # Até 99.999.999
        size_text = f"💾 Tamanho do Banco: {stats['tamanho_db']:>10}"         # Até 999.9 GB
        
        print(f"{Fore.CYAN}│{Fore.GREEN}{total_text:<34}{Fore.CYAN}│{Fore.GREEN}{size_text:<33}{Fore.CYAN}│")
        
        # Linha 3: Última coleta (centralizada)
        coleta_text = f"🕒 Última Coleta: {stats['ultima_coleta']}"
        # Centralizar em 68 chars
        espacos_total = 68 - len(coleta_text)
        espacos_antes = espacos_total // 2
        espacos_depois = espacos_total - espacos_antes
        
        print(f"{Fore.CYAN}│{Fore.MAGENTA}{' ' * espacos_antes}{coleta_text}{' ' * espacos_depois}{Fore.CYAN}│")
        
        print(f"{Fore.CYAN}└{'─'*70}┘")
        print()
    
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