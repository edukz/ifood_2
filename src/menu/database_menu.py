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
        print(f"{Fore.YELLOW}[7] {Fore.WHITE}📊 Visualizador Avançado de Dados")
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
        self.db_utils.show_advanced_menu()
    
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
            elif choice == '7':
                self.handle_advanced_viewer()
            else:
                input(f"\n{Fore.RED}Opção inválida! ENTER para continuar...")
    
    def handle_advanced_viewer(self):
        """Visualizador avançado de dados"""
        while True:
            self.show_header()
            print(f"{Fore.GREEN}📊 VISUALIZADOR AVANÇADO DE DADOS")
            print(f"{Fore.WHITE}Selecione uma tabela para visualizar:")
            print()
            
            try:
                conn = self.db_manager._get_connection()
                tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name").fetchall()
                
                if not tables:
                    print(f"{Fore.YELLOW}Nenhuma tabela encontrada!")
                    conn.close()
                    input(f"{Fore.GREEN}Pressione ENTER para voltar...")
                    break
                
                for i, table in enumerate(tables, 1):
                    # Contar registros da tabela
                    count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                    print(f"{Fore.CYAN}[{i}] {Fore.WHITE}{table[0]} ({count:,} registros)")
                
                print(f"{Fore.RED}[0] Voltar")
                print(f"{Fore.CYAN}{'─'*60}")
                
                choice = input(f"\n{Fore.YELLOW}➤ Escolha uma tabela: {Style.RESET_ALL}").strip()
                
                if choice == '0':
                    conn.close()
                    break
                    
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(tables):
                        table_name = tables[choice_num - 1][0]
                        self._advanced_table_viewer(conn, table_name)
                    else:
                        print(f"{Fore.RED}Número inválido!")
                        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                        
                except ValueError:
                    print(f"{Fore.RED}Por favor, digite um número válido!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                
                conn.close()
                
            except Exception as e:
                print(f"{Fore.RED}❌ Erro ao listar tabelas: {e}")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                break
    
    def _advanced_table_viewer(self, conn, table_name):
        """Visualizador avançado de uma tabela específica"""
        try:
            # Obter informações da tabela
            columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
            total_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            if total_count == 0:
                print(f"\n{Fore.YELLOW}A tabela '{table_name}' está vazia!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            page_size = 20
            current_page = 1
            total_pages = (total_count + page_size - 1) // page_size
            
            # Configurações de filtro
            current_filter = ""
            order_by = "id DESC"  # Padrão: mais recentes primeiro
            
            while True:
                # Limpar tela e mostrar cabeçalho
                self.clear_screen()
                print(f"{Fore.BLUE}╔══════════════════════════════════════════════════════════╗")
                print(f"{Fore.BLUE}║{f'VISUALIZANDO DADOS: {table_name.upper()}':^58}║")
                print(f"{Fore.BLUE}╚══════════════════════════════════════════════════════════╝")
                print()
                
                # Informações da página
                print(f"{Fore.CYAN}Página {current_page} de {total_pages} | Total: {total_count:,} registros")
                if current_filter:
                    print(f"{Fore.YELLOW}Filtro ativo: {current_filter}")
                
                # Construir query
                offset = (current_page - 1) * page_size
                base_query = f"SELECT * FROM {table_name}"
                
                if current_filter:
                    base_query += f" WHERE {current_filter}"
                
                base_query += f" ORDER BY {order_by} LIMIT {page_size} OFFSET {offset}"
                
                # Executar query
                data = conn.execute(base_query).fetchall()
                
                if data:
                    # Calcular larguras das colunas
                    col_names = [col[0] for col in columns]
                    col_widths = []
                    
                    for i, col_name in enumerate(col_names):
                        max_width = len(col_name)
                        for row in data:
                            val_width = len(str(row[i])) if row[i] is not None else 4
                            max_width = max(max_width, val_width)
                        col_widths.append(min(max_width + 1, 20))
                    
                    # Linha separadora
                    separator = "─" * sum(col_widths) + "─" * (len(col_names) - 1) * 3  # 3 para " | "
                    print(separator)
                    
                    # Cabeçalho
                    header_parts = []
                    for i, name in enumerate(col_names):
                        header_parts.append(f"{name:<{col_widths[i]}}")
                    header = " | ".join(header_parts) + " |"
                    print(f"{Fore.WHITE}{header}")
                    
                    # Linha separadora
                    print(separator)
                    
                    # Dados
                    for row in data:
                        row_parts = []
                        for i, val in enumerate(row):
                            if val is None:
                                val_str = "NULL"
                            elif isinstance(val, float):
                                val_str = f"{val:.2f}"
                            else:
                                val_str = str(val)
                            
                            # Truncar se muito longo
                            if len(val_str) > col_widths[i]:
                                val_str = val_str[:col_widths[i]-3] + "..."
                            
                            row_parts.append(f"{val_str:<{col_widths[i]}}")
                        
                        row_str = " | ".join(row_parts) + " |"
                        print(f"{Fore.GREEN}{row_str}")
                    
                    # Linha separadora final
                    print(separator)
                else:
                    print(f"{Fore.YELLOW}Nenhum registro encontrado com o filtro atual.")
                
                # Menu de navegação
                print(f"\n{Fore.YELLOW}NAVEGAÇÃO:")
                nav_options = []
                
                if current_page > 1:
                    nav_options.append("[P] Página anterior")
                if current_page < total_pages:
                    nav_options.append("[N] Próxima página")
                
                nav_options.extend([
                    "[G] Ir para página específica",
                    "[T] Alterar tamanho da página",
                    "[E] Exportar página atual",
                    "[F] Filtrar dados",
                    "[S] Ordenação",
                    "[0] Voltar"
                ])
                
                for i in range(0, len(nav_options), 3):
                    print(f"{Fore.WHITE}" + "   ".join(nav_options[i:i+3]))
                
                choice = input(f"\n{Fore.CYAN}Escolha: {Style.RESET_ALL}").strip().upper()
                
                if choice == '0':
                    break
                elif choice == 'P' and current_page > 1:
                    current_page -= 1
                elif choice == 'N' and current_page < total_pages:
                    current_page += 1
                elif choice == 'G':
                    try:
                        page = int(input(f"{Fore.WHITE}Ir para página (1-{total_pages}): "))
                        if 1 <= page <= total_pages:
                            current_page = page
                        else:
                            print(f"{Fore.RED}Página inválida!")
                            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    except ValueError:
                        print(f"{Fore.RED}Digite um número válido!")
                        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                elif choice == 'T':
                    try:
                        new_size = int(input(f"{Fore.WHITE}Novo tamanho da página (5-100): "))
                        if 5 <= new_size <= 100:
                            page_size = new_size
                            total_pages = (total_count + page_size - 1) // page_size
                            current_page = 1
                        else:
                            print(f"{Fore.RED}Tamanho inválido!")
                            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    except ValueError:
                        print(f"{Fore.RED}Digite um número válido!")
                        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                elif choice == 'E':
                    self._export_current_page_advanced(table_name, data, [col[0] for col in columns], current_page)
                elif choice == 'F':
                    current_filter = self._setup_filter(conn, table_name, columns)
                    current_page = 1  # Voltar para primeira página após filtrar
                elif choice == 'S':
                    order_by = self._setup_order(columns)
                    current_page = 1  # Voltar para primeira página após reordenar
                else:
                    print(f"{Fore.RED}Opção inválida!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    
        except Exception as e:
            print(f"{Fore.RED}❌ Erro no visualizador: {e}")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _setup_filter(self, conn, table_name, columns):
        """Configurar filtros para a visualização"""
        print(f"\n{Fore.CYAN}📋 CONFIGURAR FILTRO:")
        print(f"{Fore.WHITE}Colunas disponíveis:")
        
        col_names = [col[0] for col in columns]
        for i, col in enumerate(col_names, 1):
            print(f"{Fore.YELLOW}[{i}] {col}")
        
        print(f"{Fore.RED}[0] Remover filtro atual")
        
        try:
            choice = int(input(f"\n{Fore.CYAN}Escolha uma coluna para filtrar: "))
            
            if choice == 0:
                return ""
            elif 1 <= choice <= len(col_names):
                col_name = col_names[choice - 1]
                
                print(f"\n{Fore.CYAN}Tipos de filtro para '{col_name}':")
                print(f"{Fore.WHITE}[1] Contém texto")
                print(f"{Fore.WHITE}[2] Igual a")
                print(f"{Fore.WHITE}[3] Maior que")
                print(f"{Fore.WHITE}[4] Menor que")
                print(f"{Fore.WHITE}[5] Entre valores")
                
                filter_type = int(input(f"\n{Fore.CYAN}Tipo de filtro: "))
                
                if filter_type == 1:
                    value = input(f"{Fore.WHITE}Texto para buscar: ")
                    return f"{col_name} LIKE '%{value}%'"
                elif filter_type == 2:
                    value = input(f"{Fore.WHITE}Valor exato: ")
                    return f"{col_name} = '{value}'"
                elif filter_type == 3:
                    value = input(f"{Fore.WHITE}Maior que: ")
                    return f"{col_name} > {value}"
                elif filter_type == 4:
                    value = input(f"{Fore.WHITE}Menor que: ")
                    return f"{col_name} < {value}"
                elif filter_type == 5:
                    min_val = input(f"{Fore.WHITE}Valor mínimo: ")
                    max_val = input(f"{Fore.WHITE}Valor máximo: ")
                    return f"{col_name} BETWEEN {min_val} AND {max_val}"
            
        except (ValueError, IndexError):
            print(f"{Fore.RED}Opção inválida!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
        
        return ""
    
    def _setup_order(self, columns):
        """Configurar ordenação"""
        print(f"\n{Fore.CYAN}📋 CONFIGURAR ORDENAÇÃO:")
        print(f"{Fore.WHITE}Colunas disponíveis:")
        
        col_names = [col[0] for col in columns]
        for i, col in enumerate(col_names, 1):
            print(f"{Fore.YELLOW}[{i}] {col}")
        
        try:
            choice = int(input(f"\n{Fore.CYAN}Escolha uma coluna: "))
            
            if 1 <= choice <= len(col_names):
                col_name = col_names[choice - 1]
                
                print(f"\n{Fore.CYAN}Direção:")
                print(f"{Fore.WHITE}[1] Crescente (A-Z, 0-9)")
                print(f"{Fore.WHITE}[2] Decrescente (Z-A, 9-0)")
                
                direction = int(input(f"\n{Fore.CYAN}Escolha: "))
                
                if direction == 1:
                    return f"{col_name} ASC"
                elif direction == 2:
                    return f"{col_name} DESC"
            
        except (ValueError, IndexError):
            print(f"{Fore.RED}Opção inválida!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
        
        return "id DESC"  # Padrão
    
    def _export_current_page_advanced(self, table_name, data, col_names, page_num):
        """Exportar página atual para CSV"""
        try:
            import csv
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_page_{page_num}_{timestamp}.csv"
            filepath = f"exports/{filename}"
            
            # Criar diretório se não existir
            import os
            os.makedirs("exports", exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(col_names)  # Cabeçalho
                
                for row in data:
                    writer.writerow(row)
            
            print(f"\n{Fore.GREEN}✅ Página exportada para: {filepath}")
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao exportar: {e}")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")