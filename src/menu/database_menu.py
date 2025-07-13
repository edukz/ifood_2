"""
Menu de Banco de Dados (DuckDB)
"""
import os
from colorama import Fore, Back, Style
from src.database.db_manager import DatabaseManager
from src.database.db_admin import DatabaseAdmin
from src.database.db_queries import DatabaseQueries
from src.database.db_io import DatabaseIO
from src.database.db_utils import DatabaseUtils

class DatabaseMenu:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_admin = DatabaseAdmin()
        self.db_queries = DatabaseQueries()
        self.db_io = DatabaseIO()
        self.db_utils = DatabaseUtils()
    
    def clear_screen(self):
        """Limpar tela"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        """Exibir cabeçalho"""
        self.clear_screen()
        print(f"{Fore.MAGENTA}{'╔' + '═'*58 + '╗'}")
        print(f"{Fore.MAGENTA}║{Fore.CYAN}{'BANCO DE DADOS':^58}{Fore.MAGENTA}║")
        print(f"{Fore.MAGENTA}║{Fore.WHITE}{'DuckDB - Gerenciamento completo':^58}{Fore.MAGENTA}║")
        print(f"{Fore.MAGENTA}{'╚' + '═'*58 + '╝'}")
        print()
    
    def show_menu(self):
        """Exibir menu principal do banco"""
        print(f"{Back.MAGENTA}{Fore.WHITE} OPÇÕES DO BANCO DE DADOS {Style.RESET_ALL}")
        print()
        print(f"{Fore.CYAN}[1] {Fore.WHITE}Mostrar tabelas criadas")
        print(f"{Fore.CYAN}[2] {Fore.WHITE}Gerenciamento de Dados")
        print(f"{Fore.CYAN}[3] {Fore.WHITE}Administração do Banco")
        print(f"{Fore.CYAN}[4] {Fore.WHITE}Consultas e Relatórios")
        print(f"{Fore.CYAN}[5] {Fore.WHITE}Importação/Exportação")
        print(f"{Fore.CYAN}[6] {Fore.WHITE}Utilitários")
        print()
        print(f"{Fore.RED}[0] {Fore.WHITE}Voltar ao menu principal")
        print(f"{Fore.MAGENTA}{'─'*60}")
    
    def handle_data_management(self):
        """Submenu de gerenciamento de dados"""
        while True:
            self.show_header()
            print(f"{Fore.GREEN}GERENCIAMENTO DE DADOS")
            print(f"{Fore.WHITE}1. Criar/deletar tabelas")
            print(f"{Fore.WHITE}2. Inserir registros")
            print(f"{Fore.WHITE}3. Atualizar registros")
            print(f"{Fore.WHITE}4. Deletar registros")
            print(f"{Fore.WHITE}5. Visualizar dados com paginação")
            print(f"{Fore.WHITE}6. Buscar/filtrar registros")
            print(f"{Fore.RED}0. Voltar")
            
            choice = input(f"\n{Fore.YELLOW}Escolha: {Style.RESET_ALL}")
            
            if choice == '0':
                break
            elif choice == '1':
                self.db_manager.manage_tables()
            elif choice == '2':
                self.db_manager.insert_records()
            elif choice == '3':
                self.db_manager.update_records()
            elif choice == '4':
                self.db_manager.delete_records()
            elif choice == '5':
                self.db_manager.view_data()
            elif choice == '6':
                self.db_manager.search_records()
            else:
                input(f"\n{Fore.RED}Opção inválida! ENTER para continuar...")
    
    def handle_admin(self):
        """Submenu de administração"""
        while True:
            self.show_header()
            print(f"{Fore.GREEN}ADMINISTRAÇÃO DO BANCO")
            print(f"{Fore.WHITE}1. Ver estrutura das tabelas")
            print(f"{Fore.WHITE}2. Criar/alterar índices")
            print(f"{Fore.WHITE}3. Analisar performance")
            print(f"{Fore.WHITE}4. Verificar tamanho do banco")
            print(f"{Fore.WHITE}5. Vacuum/otimizar banco")
            print(f"{Fore.RED}0. Voltar")
            
            choice = input(f"\n{Fore.YELLOW}Escolha: {Style.RESET_ALL}")
            
            if choice == '0':
                break
            elif choice == '1':
                self.db_admin.show_structure()
            elif choice == '2':
                self.db_admin.manage_indexes()
            elif choice == '3':
                self.db_admin.analyze_performance()
            elif choice == '4':
                self.db_admin.check_size()
            elif choice == '5':
                self.db_admin.vacuum_database()
            else:
                input(f"\n{Fore.RED}Opção inválida! ENTER para continuar...")
    
    def handle_queries(self):
        """Submenu de consultas"""
        while True:
            self.show_header()
            print(f"{Fore.GREEN}CONSULTAS E RELATÓRIOS")
            print(f"{Fore.WHITE}1. Executar SQL personalizado")
            print(f"{Fore.WHITE}2. Consultas predefinidas")
            print(f"{Fore.WHITE}3. Estatísticas das tabelas")
            print(f"{Fore.WHITE}4. Consultas com JOIN")
            print(f"{Fore.WHITE}5. Histórico de consultas")
            print(f"{Fore.RED}0. Voltar")
            
            choice = input(f"\n{Fore.YELLOW}Escolha: {Style.RESET_ALL}")
            
            if choice == '0':
                break
            elif choice == '1':
                self.db_queries.execute_custom()
            elif choice == '2':
                self.db_queries.predefined_reports()
            elif choice == '3':
                self.db_queries.table_statistics()
            elif choice == '4':
                self.db_queries.join_queries()
            elif choice == '5':
                self.db_queries.query_history()
            else:
                input(f"\n{Fore.RED}Opção inválida! ENTER para continuar...")
    
    def handle_io(self):
        """Submenu de importação/exportação"""
        while True:
            self.show_header()
            print(f"{Fore.GREEN}IMPORTAÇÃO/EXPORTAÇÃO")
            print(f"{Fore.WHITE}1. Importar CSV, JSON, Excel")
            print(f"{Fore.WHITE}2. Exportar dados")
            print(f"{Fore.WHITE}3. Backup completo")
            print(f"{Fore.WHITE}4. Restaurar backup")
            print(f"{Fore.WHITE}5. Sincronizar com outros bancos")
            print(f"{Fore.RED}0. Voltar")
            
            choice = input(f"\n{Fore.YELLOW}Escolha: {Style.RESET_ALL}")
            
            if choice == '0':
                break
            elif choice == '1':
                self.db_io.import_data()
            elif choice == '2':
                self.db_io.export_data()
            elif choice == '3':
                self.db_io.backup_database()
            elif choice == '4':
                self.db_io.restore_backup()
            elif choice == '5':
                self.db_io.sync_databases()
            else:
                input(f"\n{Fore.RED}Opção inválida! ENTER para continuar...")
    
    def handle_utils(self):
        """Submenu de utilitários"""
        while True:
            self.show_header()
            print(f"{Fore.GREEN}UTILITÁRIOS")
            print(f"{Fore.WHITE}1. Limpeza de dados duplicados")
            print(f"{Fore.WHITE}2. Validação de integridade")
            print(f"{Fore.RED}0. Voltar")
            
            choice = input(f"\n{Fore.YELLOW}Escolha: {Style.RESET_ALL}")
            
            if choice == '0':
                break
            elif choice == '1':
                self.db_utils.clean_duplicates()
            elif choice == '2':
                self.db_utils.validate_integrity()
            else:
                input(f"\n{Fore.RED}Opção inválida! ENTER para continuar...")
    
    def run(self):
        """Executar menu do banco de dados"""
        while True:
            self.show_header()
            self.show_menu()
            
            choice = input(f"\n{Fore.YELLOW}Escolha uma opção: {Style.RESET_ALL}")
            
            if choice == '0':
                break
            elif choice == '1':
                self.db_manager.show_tables()
            elif choice == '2':
                self.handle_data_management()
            elif choice == '3':
                self.handle_admin()
            elif choice == '4':
                self.handle_queries()
            elif choice == '5':
                self.handle_io()
            elif choice == '6':
                self.handle_utils()
            else:
                input(f"\n{Fore.RED}Opção inválida! ENTER para continuar...")