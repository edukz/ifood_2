"""
Gerenciador principal do banco de dados
"""
import duckdb
import os
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style
from src.utils.logger import get_logger

class DatabaseManager:
    def __init__(self):
        self.logger = get_logger()
        self.db_path = "data/ifood_database.duckdb"
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Garantir que o diretório data existe"""
        Path("data").mkdir(exist_ok=True)
    
    def _get_connection(self):
        """Obter conexão com o banco"""
        return duckdb.connect(self.db_path)
    
    def _format_size(self, size_bytes):
        """Formatar tamanho em bytes para formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def _create_sample_tables(self):
        """Criar tabelas de exemplo se não existirem"""
        conn = self._get_connection()
        try:
            # Tabela de categorias de restaurantes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY,
                    categorias VARCHAR NOT NULL,
                    links VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de restaurantes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS restaurants (
                    id INTEGER PRIMARY KEY,
                    nome VARCHAR NOT NULL,
                    categoria VARCHAR NOT NULL,
                    distancia DECIMAL(10,2),
                    preco_entrega DECIMAL(10,2) DEFAULT 0,
                    link VARCHAR NOT NULL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de pratos
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dishes (
                    id INTEGER PRIMARY KEY,
                    restaurant_id INTEGER,
                    name VARCHAR NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2),
                    category VARCHAR,
                    available BOOLEAN DEFAULT true,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
                )
            """)
            
            # Tabela de promoções
            conn.execute("""
                CREATE TABLE IF NOT EXISTS promotions (
                    id INTEGER PRIMARY KEY,
                    restaurant_id INTEGER,
                    title VARCHAR,
                    description TEXT,
                    discount_percentage INTEGER,
                    valid_until DATE,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
                )
            """)
            
            # Tabela de logs de scraping
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    city VARCHAR,
                    status VARCHAR,
                    restaurants_found INTEGER,
                    dishes_found INTEGER,
                    errors INTEGER,
                    duration_seconds INTEGER
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Erro ao criar tabelas de exemplo: {e}")
            conn.close()
            raise
    
    def show_tables(self):
        """Mostrar tabelas criadas"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║                    TABELAS DO BANCO                      ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        self.logger.info("Listando tabelas do banco")
        
        try:
            # Criar tabelas de exemplo se necessário
            self._create_sample_tables()
            
            conn = self._get_connection()
            
            # Verificar se o banco existe
            if not os.path.exists(self.db_path):
                print(f"\n{Fore.RED}Banco de dados não encontrado!")
                print(f"{Fore.YELLOW}Criando novo banco em: {self.db_path}")
            
            # Obter informações do banco
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            print(f"\n{Fore.CYAN}📊 INFORMAÇÕES DO BANCO:")
            print(f"{Fore.WHITE}   • Arquivo: {self.db_path}")
            print(f"{Fore.WHITE}   • Tamanho: {self._format_size(db_size)}")
            print(f"{Fore.WHITE}   • DuckDB versão: {duckdb.__version__}")
            
            # Listar tabelas
            tables = conn.execute("""
                SELECT 
                    table_name,
                    0 as estimated_size,
                    (SELECT COUNT(*) FROM duckdb_columns() WHERE table_name = t.table_name) as column_count,
                    'BASE TABLE' as table_type
                FROM duckdb_tables() t
                ORDER BY table_name
            """).fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}⚠️  Nenhuma tabela encontrada no banco.")
                print(f"{Fore.WHITE}   Use a opção 'Gerenciamento de Dados' para criar tabelas.")
            else:
                print(f"\n{Fore.CYAN}📋 TABELAS ENCONTRADAS: {len(tables)}")
                print(f"\n{Fore.WHITE}{'Nome da Tabela':<25} {'Colunas':<10} {'Tamanho Estimado':<20} {'Tipo'}")
                print(f"{Fore.WHITE}{'-'*75}")
                
                for table in tables:
                    table_name, size, cols, table_type = table
                    size_formatted = self._format_size(size) if size else "0B"
                    print(f"{Fore.GREEN}{table_name:<25} {Fore.WHITE}{cols:<10} {size_formatted:<20} {table_type}")
                
                # Obter contagem de registros
                print(f"\n{Fore.CYAN}📈 CONTAGEM DE REGISTROS:")
                for table in tables:
                    table_name = table[0]
                    try:
                        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        print(f"{Fore.WHITE}   • {table_name}: {Fore.GREEN}{count:,} registros")
                    except:
                        print(f"{Fore.WHITE}   • {table_name}: {Fore.RED}Erro ao contar")
                
                # Mostrar relacionamentos
                try:
                    # Tentar versão mais nova do DuckDB primeiro
                    fks = conn.execute("""
                        SELECT DISTINCT 
                            constraint_name,
                            constraint_type,
                            constraint_text
                        FROM duckdb_constraints()
                        WHERE constraint_type = 'FOREIGN KEY'
                    """).fetchall()
                except:
                    # Fallback para versões mais antigas
                    fks = []
                
                if fks:
                    print(f"\n{Fore.CYAN}🔗 RELACIONAMENTOS (Foreign Keys):")
                    for fk in fks:
                        constraint_name, constraint_type, constraint_text = fk
                        # Extrair informações do texto da constraint
                        if constraint_text:
                            # Simplificar a exibição do constraint
                            text = constraint_text.replace("FOREIGN KEY", "FK").replace("REFERENCES", "→")
                            print(f"{Fore.WHITE}   • {constraint_name}: {text}")
                        else:
                            print(f"{Fore.WHITE}   • {constraint_name}: {constraint_type}")
            
            # Estatísticas gerais
            print(f"\n{Fore.CYAN}📊 ESTATÍSTICAS GERAIS:")
            
            # Total de tabelas
            total_tables = len(tables)
            
            # Total de colunas
            total_columns = sum(table[2] for table in tables)
            
            # Total de registros (soma de todas as tabelas)
            total_records = 0
            for table in tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                    total_records += count
                except:
                    pass
            
            print(f"{Fore.WHITE}   • Total de tabelas: {total_tables}")
            print(f"{Fore.WHITE}   • Total de colunas: {total_columns}")
            print(f"{Fore.WHITE}   • Total de registros: {total_records:,}")
            print(f"{Fore.WHITE}   • Tamanho do banco: {self._format_size(db_size)}")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao listar tabelas: {e}")
            print(f"\n{Fore.RED}❌ Erro ao acessar banco de dados:")
            print(f"{Fore.YELLOW}   {str(e)}")
            print(f"\n{Fore.CYAN}💡 Dica: Se for um erro de permissão, tente fechar outros programas que possam estar usando o banco.")
        
        # Opção para ver detalhes
        if tables:
            print(f"\n{Fore.YELLOW}Deseja ver detalhes de alguma tabela?")
            choice = input(f"{Fore.WHITE}Digite o nome da tabela (ou ENTER para voltar): {Fore.GREEN}").strip()
            
            if choice:
                self._show_table_details(choice)
        else:
            input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_table_details(self, table_name):
        """Mostrar detalhes de uma tabela específica"""
        try:
            conn = self._get_connection()
            
            print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.YELLOW}║{f'DETALHES DA TABELA: {table_name.upper()}':^58}║")
            print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
            
            # Verificar se a tabela existe
            table_exists = conn.execute(f"""
                SELECT COUNT(*) FROM duckdb_tables() 
                WHERE table_name = '{table_name}'
            """).fetchone()[0]
            
            if not table_exists:
                print(f"\n{Fore.RED}❌ Tabela '{table_name}' não encontrada!")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                conn.close()
                return
            
            # Obter estrutura da tabela
            columns = conn.execute(f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM duckdb_columns()
                WHERE table_name = '{table_name}'
                ORDER BY column_index
            """).fetchall()
            
            print(f"\n{Fore.CYAN}📋 ESTRUTURA DA TABELA:")
            print(f"\n{Fore.WHITE}{'Coluna':<20} {'Tipo':<15} {'Nulo?':<8} {'Padrão'}")
            print(f"{Fore.WHITE}{'-'*65}")
            
            for col in columns:
                col_name, data_type, nullable, default = col
                nullable_str = "Sim" if nullable == "YES" else "Não"
                default_str = str(default) if default else "-"
                if len(default_str) > 15:
                    default_str = default_str[:12] + "..."
                
                print(f"{Fore.GREEN}{col_name:<20} {Fore.WHITE}{data_type:<15} {nullable_str:<8} {default_str}")
            
            # Contagem de registros
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"\n{Fore.CYAN}📊 INFORMAÇÕES:")
            print(f"{Fore.WHITE}   • Total de registros: {count:,}")
            print(f"{Fore.WHITE}   • Total de colunas: {len(columns)}")
            
            # Constraints (chaves primárias, foreign keys, etc.)
            try:
                constraints = conn.execute(f"""
                    SELECT 
                        constraint_name,
                        constraint_type,
                        constraint_text
                    FROM duckdb_constraints()
                    WHERE schema_name = 'main'
                """).fetchall()
                
                # Filtrar constraints que se aplicam à tabela atual
                table_constraints = []
                for constraint in constraints:
                    if constraint[2] and table_name.lower() in constraint[2].lower():
                        table_constraints.append(constraint)
                constraints = table_constraints
                
            except Exception as e:
                # Fallback se houver erro
                constraints = []
            
            if constraints:
                print(f"\n{Fore.CYAN}🔐 CONSTRAINTS:")
                for constraint in constraints:
                    name, type_c, text_c = constraint
                    if text_c:
                        # Simplificar a exibição
                        text = text_c.replace("FOREIGN KEY", "FK").replace("REFERENCES", "→")
                        print(f"{Fore.WHITE}   • {type_c}: {text}")
                    else:
                        print(f"{Fore.WHITE}   • {type_c}: {name}")
            
            # Amostra de dados com opções configuráveis
            if count > 0:
                # Perguntar quantos registros mostrar
                print(f"\n{Fore.YELLOW}Quantos registros mostrar?")
                print(f"{Fore.WHITE}[1] 5 registros   [2] 10 registros   [3] 20 registros   [4] 50 registros   [ENTER] Padrão (10)")
                
                try:
                    opcao = input(f"{Fore.CYAN}➤ ").strip()
                    if opcao == '1':
                        limit = 5
                    elif opcao == '2':
                        limit = 10
                    elif opcao == '3':
                        limit = 20
                    elif opcao == '4':
                        limit = 50
                    else:
                        limit = 10
                except:
                    limit = 10
                
                print(f"\n{Fore.CYAN}👀 AMOSTRA DE DADOS ({limit} registros):")
                sample = conn.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}").fetchall()
                
                if sample:
                    # Cabeçalho melhorado com larguras dinâmicas
                    col_names = [col[0] for col in columns]
                    
                    # Calcular larguras das colunas baseado no conteúdo
                    col_widths = []
                    for i, col_name in enumerate(col_names):
                        max_width = len(col_name)
                        for row in sample:
                            val_width = len(str(row[i])) if row[i] is not None else 4  # "None" = 4
                            max_width = max(max_width, val_width)
                        # Limitar largura máxima para evitar linhas muito longas
                        col_widths.append(min(max_width + 1, 20))
                    
                    # Cabeçalho
                    header = " | ".join(f"{name:<{col_widths[i]}}" for i, name in enumerate(col_names))
                    print(f"\n{Fore.WHITE}{header}")
                    print(f"{Fore.WHITE}{'-' * len(header)}")
                    
                    # Dados com cores alternadas
                    for idx, row in enumerate(sample):
                        color = Fore.GREEN if idx % 2 == 0 else Fore.CYAN
                        row_values = []
                        for i, val in enumerate(row):
                            if val is None:
                                val_str = "None"
                            elif isinstance(val, float):
                                val_str = f"{val:.2f}"
                            else:
                                val_str = str(val)
                            
                            # Truncar se muito longo
                            if len(val_str) > col_widths[i]:
                                val_str = val_str[:col_widths[i]-3] + "..."
                            
                            row_values.append(f"{val_str:<{col_widths[i]}}")
                        
                        row_str = " | ".join(row_values)
                        print(f"{color}{row_str}")
                    
                    print(f"\n{Fore.YELLOW}💡 Mostrando registros mais recentes (ORDER BY id DESC)")
                    
                    # Opção para ver mais dados
                    if count > limit:
                        print(f"\n{Fore.CYAN}📄 Esta tabela tem {count:,} registros no total.")
                        print(f"{Fore.WHITE}Deseja navegar pelos dados? (s/N): ", end="")
                        
                        if input().strip().lower() == 's':
                            self._navegar_dados_paginados(conn, table_name, columns, count)
                else:
                    print(f"{Fore.YELLOW}   Nenhum dado para mostrar")
            else:
                print(f"\n{Fore.YELLOW}📝 Tabela vazia - nenhum registro encontrado")
            
            # Estatísticas por coluna (para colunas numéricas)
            print(f"\n{Fore.CYAN}📈 ESTATÍSTICAS DETALHADAS:")
            
            # Estatísticas gerais da tabela
            print(f"{Fore.WHITE}   📊 Total de registros: {count:,}")
            print(f"{Fore.WHITE}   📊 Colunas na tabela: {len(columns)}")
            
            # Verificar se há registros recentes (últimas 24h)
            try:
                recent = conn.execute(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE scraped_at >= datetime('now', '-1 day')
                """).fetchone()[0]
                if recent > 0:
                    print(f"{Fore.GREEN}   🕒 Registros nas últimas 24h: {recent}")
            except:
                pass
            
            print(f"\n{Fore.CYAN}📊 ESTATÍSTICAS POR COLUNA:")
            for col in columns:
                col_name, data_type, _, _ = col
                if any(t in data_type.upper() for t in ['INTEGER', 'DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE']):
                    try:
                        stats = conn.execute(f"""
                            SELECT 
                                MIN({col_name}) as min_val,
                                MAX({col_name}) as max_val,
                                AVG({col_name}) as avg_val,
                                COUNT(DISTINCT {col_name}) as distinct_count
                            FROM {table_name}
                            WHERE {col_name} IS NOT NULL
                        """).fetchone()
                        
                        if stats and stats[0] is not None:
                            min_val, max_val, avg_val, distinct = stats
                            print(f"{Fore.WHITE}   • {col_name}: Min={min_val}, Max={max_val}, Avg={avg_val:.2f}, Únicos={distinct}")
                    except:
                        pass
                
                elif 'VARCHAR' in data_type.upper() or 'TEXT' in data_type.upper():
                    try:
                        # Estatísticas para colunas de texto
                        text_stats = conn.execute(f"""
                            SELECT 
                                COUNT(DISTINCT {col_name}) as distinct_count,
                                COUNT(*) as total_count,
                                COUNT(CASE WHEN {col_name} IS NULL OR {col_name} = '' THEN 1 END) as null_empty_count
                            FROM {table_name}
                        """).fetchone()
                        
                        if text_stats:
                            distinct, total, null_empty = text_stats
                            non_null = total - null_empty
                            completeness = (non_null / total * 100) if total > 0 else 0
                            
                            print(f"{Fore.WHITE}   • {col_name}: {distinct} únicos, {non_null}/{total} preenchidos ({completeness:.1f}%)")
                            
                            # Mostrar valores mais comuns para algumas colunas específicas
                            if col_name.lower() in ['category', 'categoria', 'city', 'cidade'] and distinct <= 20:
                                common_values = conn.execute(f"""
                                    SELECT {col_name}, COUNT(*) as count 
                                    FROM {table_name} 
                                    WHERE {col_name} IS NOT NULL AND {col_name} != ''
                                    GROUP BY {col_name} 
                                    ORDER BY count DESC 
                                    LIMIT 5
                                """).fetchall()
                                
                                if common_values:
                                    values_str = ", ".join([f"{val[0]}({val[1]})" for val in common_values])
                                    print(f"{Fore.YELLOW}     ↳ Mais comuns: {values_str}")
                    except:
                        # Fallback simples
                        try:
                            distinct_count = conn.execute(f"""
                                SELECT COUNT(DISTINCT {col_name})
                            FROM {table_name}
                            WHERE {col_name} IS NOT NULL
                        """).fetchone()[0]
                            print(f"{Fore.WHITE}   • {col_name}: {distinct_count} valores únicos")
                        except:
                            pass
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar detalhes da tabela {table_name}: {e}")
            print(f"\n{Fore.RED}❌ Erro ao acessar tabela: {e}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _navegar_dados_paginados(self, conn, table_name, columns, total_count):
        """Navegar pelos dados da tabela com paginação"""
        page_size = 20
        current_page = 0
        total_pages = (total_count + page_size - 1) // page_size
        
        col_names = [col[0] for col in columns]
        
        while True:
            offset = current_page * page_size
            
            print(f"\n{Fore.CYAN}📄 PÁGINA {current_page + 1} de {total_pages} ({page_size} registros por página)")
            print(f"{Fore.WHITE}Registros {offset + 1} a {min(offset + page_size, total_count)} de {total_count:,}")
            
            # Buscar dados da página atual
            data = conn.execute(f"""
                SELECT * FROM {table_name} 
                ORDER BY id DESC 
                LIMIT {page_size} OFFSET {offset}
            """).fetchall()
            
            if data:
                # Calcular larguras das colunas
                col_widths = []
                for i, col_name in enumerate(col_names):
                    max_width = len(col_name)
                    for row in data:
                        val_width = len(str(row[i])) if row[i] is not None else 4
                        max_width = max(max_width, val_width)
                    col_widths.append(min(max_width + 1, 25))
                
                # Cabeçalho
                header = " | ".join(f"{name:<{col_widths[i]}}" for i, name in enumerate(col_names))
                print(f"\n{Fore.WHITE}{header}")
                print(f"{Fore.WHITE}{'-' * len(header)}")
                
                # Dados
                for idx, row in enumerate(data):
                    color = Fore.GREEN if idx % 2 == 0 else Fore.CYAN
                    row_values = []
                    for i, val in enumerate(row):
                        if val is None:
                            val_str = "None"
                        elif isinstance(val, float):
                            val_str = f"{val:.2f}"
                        else:
                            val_str = str(val)
                        
                        if len(val_str) > col_widths[i]:
                            val_str = val_str[:col_widths[i]-3] + "..."
                        
                        row_values.append(f"{val_str:<{col_widths[i]}}")
                    
                    row_str = " | ".join(row_values)
                    print(f"{color}{row_str}")
            
            # Menu de navegação
            print(f"\n{Fore.YELLOW}Navegação:")
            options = []
            if current_page > 0:
                options.append("[P] Página anterior")
            if current_page < total_pages - 1:
                options.append("[N] Próxima página")
            options.extend(["[1] Primeira página", "[U] Última página", "[Q] Sair"])
            
            print(f"{Fore.WHITE}" + "   ".join(options))
            
            choice = input(f"\n{Fore.CYAN}➤ ").strip().upper()
            
            if choice == 'Q':
                break
            elif choice == 'P' and current_page > 0:
                current_page -= 1
            elif choice == 'N' and current_page < total_pages - 1:
                current_page += 1
            elif choice == '1':
                current_page = 0
            elif choice == 'U':
                current_page = total_pages - 1
            else:
                print(f"{Fore.RED}Opção inválida!")
                input("Pressione ENTER para continuar...")
                continue
    
    def manage_tables(self):
        """Criar/deletar tabelas"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║                 GERENCIAR TABELAS                        ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        while True:
            # Listar tabelas existentes
            try:
                conn = self._get_connection()
                tables = conn.execute("SELECT table_name FROM duckdb_tables() ORDER BY table_name").fetchall()
                conn.close()
            except:
                tables = []
            
            print(f"\n{Fore.CYAN}📋 TABELAS EXISTENTES: {len(tables)}")
            if tables:
                for i, table in enumerate(tables, 1):
                    print(f"{Fore.WHITE}   {i}. {table[0]}")
            else:
                print(f"{Fore.YELLOW}   Nenhuma tabela encontrada")
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Criar nova tabela")
            print(f"{Fore.WHITE}[2] Deletar tabela existente")
            print(f"{Fore.WHITE}[3] Ver estrutura de uma tabela")
            print(f"{Fore.WHITE}[4] Criar tabela a partir de template")
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._create_table()
            elif choice == "2":
                self._delete_table()
            elif choice == "3":
                self._show_table_structure()
            elif choice == "4":
                self._create_table_from_template()
            elif choice == "0":
                break
            else:
                print(f"{Fore.RED}Opção inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _create_table(self):
        """Criar nova tabela"""
        print(f"\n{Fore.YELLOW}CRIAR NOVA TABELA")
        
        table_name = input(f"{Fore.WHITE}Nome da tabela: {Fore.GREEN}").strip()
        if not table_name:
            print(f"{Fore.RED}Nome da tabela não pode estar vazio!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        # Verificar se já existe
        try:
            conn = self._get_connection()
            exists = conn.execute(f"SELECT COUNT(*) FROM duckdb_tables() WHERE table_name = '{table_name}'").fetchone()[0]
            if exists:
                print(f"{Fore.RED}Tabela '{table_name}' já existe!")
                conn.close()
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
        except Exception as e:
            print(f"{Fore.RED}Erro ao verificar tabela: {e}")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        # Coletar colunas
        columns = []
        print(f"\n{Fore.CYAN}Definir colunas (pressione ENTER sem nome para finalizar):")
        
        while True:
            col_name = input(f"{Fore.WHITE}Nome da coluna: {Fore.GREEN}").strip()
            if not col_name:
                break
            
            print(f"{Fore.CYAN}Tipos disponíveis:")
            print(f"{Fore.WHITE}[1] INTEGER - Número inteiro")
            print(f"{Fore.WHITE}[2] VARCHAR - Texto")
            print(f"{Fore.WHITE}[3] DECIMAL(10,2) - Decimal")
            print(f"{Fore.WHITE}[4] BOOLEAN - Verdadeiro/Falso")
            print(f"{Fore.WHITE}[5] DATE - Data")
            print(f"{Fore.WHITE}[6] TIMESTAMP - Data e hora")
            print(f"{Fore.WHITE}[7] TEXT - Texto longo")
            
            type_choice = input(f"{Fore.WHITE}Escolha o tipo (1-7): {Fore.GREEN}").strip()
            
            type_map = {
                "1": "INTEGER",
                "2": "VARCHAR(255)",
                "3": "DECIMAL(10,2)",
                "4": "BOOLEAN",
                "5": "DATE",
                "6": "TIMESTAMP",
                "7": "TEXT"
            }
            
            if type_choice not in type_map:
                print(f"{Fore.RED}Tipo inválido!")
                continue
            
            col_type = type_map[type_choice]
            
            nullable = input(f"{Fore.WHITE}Pode ser nulo? (S/n): {Fore.GREEN}").strip().lower()
            not_null = " NOT NULL" if nullable == 'n' else ""
            
            primary_key = input(f"{Fore.WHITE}É chave primária? (s/N): {Fore.GREEN}").strip().lower()
            pk = " PRIMARY KEY" if primary_key == 's' else ""
            
            column_def = f"{col_name} {col_type}{not_null}{pk}"
            columns.append(column_def)
            print(f"{Fore.GREEN}✓ Coluna adicionada: {column_def}")
        
        if not columns:
            print(f"{Fore.RED}Nenhuma coluna definida!")
            conn.close()
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        # Criar tabela
        try:
            sql = f"CREATE TABLE {table_name} ({', '.join(columns)})"
            print(f"\n{Fore.CYAN}SQL que será executado:")
            print(f"{Fore.WHITE}{sql}")
            
            confirm = input(f"\n{Fore.YELLOW}Confirmar criação? (S/n): {Fore.GREEN}").strip().lower()
            if confirm == 'n':
                print(f"{Fore.CYAN}Operação cancelada.")
                conn.close()
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            conn.execute(sql)
            conn.commit()
            conn.close()
            
            print(f"{Fore.GREEN}✅ Tabela '{table_name}' criada com sucesso!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao criar tabela: {e}")
            conn.close()
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _delete_table(self):
        """Deletar tabela existente"""
        print(f"\n{Fore.YELLOW}DELETAR TABELA")
        
        try:
            conn = self._get_connection()
            tables = conn.execute("SELECT table_name FROM duckdb_tables() ORDER BY table_name").fetchall()
            
            if not tables:
                print(f"{Fore.YELLOW}Nenhuma tabela para deletar!")
                conn.close()
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            print(f"\n{Fore.WHITE}Tabelas disponíveis:")
            for i, table in enumerate(tables, 1):
                # Mostrar contagem de registros
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                    print(f"{Fore.WHITE}[{i}] {table[0]} ({count:,} registros)")
                except:
                    print(f"{Fore.WHITE}[{i}] {table[0]} (erro ao contar)")
            
            choice = input(f"\n{Fore.WHITE}Número da tabela a deletar (0 para cancelar): {Fore.GREEN}").strip()
            
            try:
                choice_num = int(choice)
                if choice_num == 0:
                    print(f"{Fore.CYAN}Operação cancelada.")
                    conn.close()
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    return
                
                if 1 <= choice_num <= len(tables):
                    table_name = tables[choice_num - 1][0]
                    
                    # Confirmar deleção
                    print(f"\n{Fore.RED}⚠️  ATENÇÃO!")
                    print(f"{Fore.WHITE}Isso deletará permanentemente a tabela '{table_name}' e todos os seus dados!")
                    
                    confirm = input(f"\n{Fore.RED}Digite 'DELETAR' para confirmar: {Fore.WHITE}").strip()
                    
                    if confirm == 'DELETAR':
                        conn.execute(f"DROP TABLE {table_name}")
                        conn.commit()
                        print(f"{Fore.GREEN}✅ Tabela '{table_name}' deletada com sucesso!")
                    else:
                        print(f"{Fore.CYAN}Operação cancelada.")
                else:
                    print(f"{Fore.RED}Número inválido!")
                    
            except ValueError:
                print(f"{Fore.RED}Por favor, digite um número válido!")
            
            conn.close()
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao deletar tabela: {e}")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_table_structure(self):
        """Mostrar estrutura de uma tabela"""
        print(f"\n{Fore.YELLOW}VER ESTRUTURA DA TABELA")
        
        table_name = input(f"{Fore.WHITE}Nome da tabela: {Fore.GREEN}").strip()
        if table_name:
            self._show_table_details(table_name)
    
    def _create_table_from_template(self):
        """Criar tabela a partir de template"""
        print(f"\n{Fore.YELLOW}CRIAR TABELA A PARTIR DE TEMPLATE")
        
        templates = {
            "1": {
                "name": "Produtos",
                "sql": """CREATE TABLE produtos (
                    id INTEGER PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    descricao TEXT,
                    preco DECIMAL(10,2) NOT NULL,
                    categoria VARCHAR(100),
                    disponivel BOOLEAN DEFAULT true,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            },
            "2": {
                "name": "Usuários",
                "sql": """CREATE TABLE usuarios (
                    id INTEGER PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    telefone VARCHAR(20),
                    cidade VARCHAR(100),
                    ativo BOOLEAN DEFAULT true,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            },
            "3": {
                "name": "Pedidos",
                "sql": """CREATE TABLE pedidos (
                    id INTEGER PRIMARY KEY,
                    usuario_id INTEGER,
                    total DECIMAL(10,2) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pendente',
                    endereco_entrega TEXT,
                    data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            },
            "4": {
                "name": "Logs de Sistema",
                "sql": """CREATE TABLE logs_sistema (
                    id INTEGER PRIMARY KEY,
                    nivel VARCHAR(20) NOT NULL,
                    mensagem TEXT NOT NULL,
                    modulo VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            }
        }
        
        print(f"\n{Fore.CYAN}Templates disponíveis:")
        for key, template in templates.items():
            print(f"{Fore.WHITE}[{key}] {template['name']}")
        
        choice = input(f"\n{Fore.WHITE}Escolha um template (1-4): {Fore.GREEN}").strip()
        
        if choice not in templates:
            print(f"{Fore.RED}Template inválido!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        template = templates[choice]
        table_name = input(f"\n{Fore.WHITE}Nome para a nova tabela: {Fore.GREEN}").strip()
        
        if not table_name:
            print(f"{Fore.RED}Nome da tabela não pode estar vazio!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        try:
            conn = self._get_connection()
            
            # Verificar se já existe
            exists = conn.execute(f"SELECT COUNT(*) FROM duckdb_tables() WHERE table_name = '{table_name}'").fetchone()[0]
            if exists:
                print(f"{Fore.RED}Tabela '{table_name}' já existe!")
                conn.close()
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            # Substituir nome da tabela no SQL
            sql = template['sql'].replace(list(templates.values())[int(choice)-1]['sql'].split()[2], table_name)
            
            print(f"\n{Fore.CYAN}SQL que será executado:")
            print(f"{Fore.WHITE}{sql}")
            
            confirm = input(f"\n{Fore.YELLOW}Confirmar criação? (S/n): {Fore.GREEN}").strip().lower()
            if confirm == 'n':
                print(f"{Fore.CYAN}Operação cancelada.")
                conn.close()
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            conn.execute(sql)
            conn.commit()
            conn.close()
            
            print(f"{Fore.GREEN}✅ Tabela '{table_name}' criada com sucesso usando template '{template['name']}'!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao criar tabela: {e}")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def insert_records(self):
        """Inserir registros"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║                   INSERIR REGISTROS                      ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        # Listar tabelas disponíveis
        try:
            conn = self._get_connection()
            tables = conn.execute("SELECT table_name FROM duckdb_tables() ORDER BY table_name").fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}Nenhuma tabela encontrada!")
                print(f"{Fore.WHITE}Crie uma tabela primeiro usando 'Gerenciar Tabelas'.")
                conn.close()
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            print(f"\n{Fore.CYAN}📋 TABELAS DISPONÍVEIS:")
            for i, table in enumerate(tables, 1):
                # Mostrar contagem atual
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                    print(f"{Fore.WHITE}[{i}] {table[0]} ({count:,} registros)")
                except:
                    print(f"{Fore.WHITE}[{i}] {table[0]} (erro ao contar)")
            
            choice = input(f"\n{Fore.WHITE}Escolha a tabela (1-{len(tables)}): {Fore.GREEN}").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(tables):
                    table_name = tables[choice_num - 1][0]
                    self._insert_into_table(table_name)
                else:
                    print(f"{Fore.RED}Número inválido!")
            except ValueError:
                print(f"{Fore.RED}Por favor, digite um número válido!")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao acessar tabelas: {e}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _insert_into_table(self, table_name):
        """Inserir registros em uma tabela específica"""
        print(f"\n{Fore.YELLOW}INSERIR EM: {table_name.upper()}")
        
        try:
            conn = self._get_connection()
            
            # Obter estrutura da tabela
            columns = conn.execute(f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM duckdb_columns()
                WHERE table_name = '{table_name}'
                ORDER BY column_index
            """).fetchall()
            
            print(f"\n{Fore.CYAN}📋 ESTRUTURA DA TABELA:")
            print(f"\n{Fore.WHITE}{'Coluna':<20} {'Tipo':<15} {'Nulo?':<8} {'Padrão'}")
            print(f"{Fore.WHITE}{'-'*55}")
            
            insertable_columns = []
            for col in columns:
                col_name, data_type, nullable, default = col
                nullable_str = "Sim" if nullable == "YES" else "Não"
                default_str = str(default) if default else "-"
                
                # Pular colunas auto-incrementais ou com padrão de timestamp
                if ("PRIMARY KEY" in str(default) or 
                    "CURRENT_TIMESTAMP" in str(default).upper() or
                    col_name.lower() == 'id'):
                    print(f"{Fore.YELLOW}{col_name:<20} {Fore.WHITE}{data_type:<15} {nullable_str:<8} {default_str} (auto)")
                else:
                    print(f"{Fore.GREEN}{col_name:<20} {Fore.WHITE}{data_type:<15} {nullable_str:<8} {default_str}")
                    insertable_columns.append(col)
            
            if not insertable_columns:
                print(f"\n{Fore.YELLOW}Todas as colunas são automáticas!")
                conn.close()
                return
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Inserir um registro")
            print(f"{Fore.WHITE}[2] Inserir múltiplos registros")
            print(f"{Fore.WHITE}[3] Inserir dados de exemplo")
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._insert_single_record(conn, table_name, insertable_columns)
            elif choice == "2":
                self._insert_multiple_records(conn, table_name, insertable_columns)
            elif choice == "3":
                self._insert_sample_data(conn, table_name)
            elif choice == "0":
                pass
            else:
                print(f"{Fore.RED}Opção inválida!")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao preparar inserção: {e}")
    
    def _insert_single_record(self, conn, table_name, columns):
        """Inserir um único registro"""
        print(f"\n{Fore.YELLOW}INSERIR UM REGISTRO")
        
        values = []
        column_names = []
        
        for col in columns:
            col_name, data_type, nullable, default = col
            
            print(f"\n{Fore.CYAN}Coluna: {col_name} ({data_type})")
            if nullable == "YES":
                print(f"{Fore.WHITE}(Opcional - pressione ENTER para deixar vazio)")
            
            while True:
                value = input(f"{Fore.WHITE}Valor: {Fore.GREEN}").strip()
                
                # Se for opcional e vazio
                if not value and nullable == "YES":
                    break
                
                # Se for obrigatório e vazio
                if not value and nullable != "YES":
                    print(f"{Fore.RED}Este campo é obrigatório!")
                    continue
                
                # Validar tipos
                if self._validate_value(value, data_type):
                    values.append(value)
                    column_names.append(col_name)
                    break
                else:
                    print(f"{Fore.RED}Valor inválido para o tipo {data_type}!")
        
        if not values:
            print(f"{Fore.YELLOW}Nenhum valor para inserir!")
            return
        
        try:
            # Construir SQL
            placeholders = ", ".join(["?" for _ in values])
            sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
            
            print(f"\n{Fore.CYAN}SQL: {sql}")
            print(f"{Fore.WHITE}Valores: {values}")
            
            confirm = input(f"\n{Fore.YELLOW}Confirmar inserção? (S/n): {Fore.GREEN}").strip().lower()
            if confirm == 'n':
                print(f"{Fore.CYAN}Operação cancelada.")
                return
            
            conn.execute(sql, values)
            conn.commit()
            
            print(f"{Fore.GREEN}✅ Registro inserido com sucesso!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao inserir: {e}")
    
    def _insert_multiple_records(self, conn, table_name, columns):
        """Inserir múltiplos registros"""
        print(f"\n{Fore.YELLOW}INSERIR MÚLTIPLOS REGISTROS")
        
        records = []
        column_names = [col[0] for col in columns]
        
        print(f"{Fore.CYAN}Digite os valores para cada registro (ENTER vazio para finalizar)")
        
        record_num = 1
        while True:
            print(f"\n{Fore.WHITE}=== REGISTRO {record_num} ===")
            
            values = []
            skip_record = False
            
            for col in columns:
                col_name, data_type, nullable, default = col
                
                value = input(f"{Fore.WHITE}{col_name} ({data_type}): {Fore.GREEN}").strip()
                
                # Verificar se quer parar
                if not value and col == columns[0]:
                    skip_record = True
                    break
                
                # Validar
                if not value and nullable != "YES":
                    print(f"{Fore.RED}Campo obrigatório!")
                    skip_record = True
                    break
                
                if value and not self._validate_value(value, data_type):
                    print(f"{Fore.RED}Valor inválido!")
                    skip_record = True
                    break
                
                values.append(value if value else None)
            
            if skip_record:
                break
            
            records.append(values)
            record_num += 1
            
            print(f"{Fore.GREEN}✓ Registro {record_num-1} adicionado")
        
        if not records:
            print(f"{Fore.YELLOW}Nenhum registro para inserir!")
            return
        
        try:
            placeholders = ", ".join(["?" for _ in column_names])
            sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
            
            print(f"\n{Fore.CYAN}Inserindo {len(records)} registros...")
            
            for values in records:
                conn.execute(sql, values)
            
            conn.commit()
            print(f"{Fore.GREEN}✅ {len(records)} registros inseridos com sucesso!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao inserir: {e}")
    
    def _insert_sample_data(self, conn, table_name):
        """Inserir dados de exemplo"""
        print(f"\n{Fore.YELLOW}INSERIR DADOS DE EXEMPLO")
        
        # Dados de exemplo baseados no nome da tabela
        sample_data = {
            'restaurants': [
                ("Burger King", "Fast Food", 4.2, 25, 5.99, "São Paulo"),
                ("McDonald's", "Fast Food", 4.0, 20, 4.99, "São Paulo"),
                ("Pizza Hut", "Pizza", 4.5, 35, 7.99, "Rio de Janeiro"),
                ("Subway", "Sanduíches", 4.1, 15, 3.99, "São Paulo"),
                ("KFC", "Fast Food", 4.3, 30, 6.99, "Rio de Janeiro")
            ],
            'dishes': [
                (1, "Big King", "Hambúrguer artesanal", 15.99, "Hambúrgueres", True),
                (1, "Batata Frita", "Batata sequinha", 8.99, "Acompanhamentos", True),
                (2, "Big Mac", "Hambúrguer clássico", 16.99, "Hambúrgueres", True),
                (3, "Pizza Pepperoni", "Pizza tradicional", 35.99, "Pizzas", True),
                (4, "Subway Frango", "Sanduíche de frango", 12.99, "Sanduíches", True)
            ],
            'promotions': [
                (1, "Desconto 20%", "20% off em hambúrgueres", 20, "2024-12-31"),
                (2, "Combo Família", "2 Big Mac + batatas", 15, "2024-12-25"),
                (3, "Pizza em Dobro", "Compre 1 leve 2", 50, "2024-12-30")
            ],
            'produtos': [
                ("iPhone 15", "Smartphone Apple", 4999.99, "Eletrônicos", True),
                ("Samsung Galaxy", "Smartphone Samsung", 3499.99, "Eletrônicos", True),
                ("Notebook Dell", "Laptop para trabalho", 2999.99, "Informática", True)
            ],
            'usuarios': [
                ("João Silva", "joao@email.com", "(11)99999-9999", "São Paulo", True),
                ("Maria Santos", "maria@email.com", "(21)88888-8888", "Rio de Janeiro", True),
                ("Pedro Costa", "pedro@email.com", "(11)77777-7777", "São Paulo", True)
            ]
        }
        
        # Verificar se tem dados para a tabela
        table_lower = table_name.lower()
        data = None
        
        for key in sample_data:
            if key in table_lower or table_lower in key:
                data = sample_data[key]
                break
        
        if not data:
            print(f"{Fore.YELLOW}Não há dados de exemplo para a tabela '{table_name}'")
            return
        
        try:
            # Obter colunas não automáticas
            columns = conn.execute(f"""
                SELECT column_name
                FROM duckdb_columns()
                WHERE table_name = '{table_name}'
                AND column_name != 'id'
                AND column_default IS NULL
                ORDER BY column_index
            """).fetchall()
            
            column_names = [col[0] for col in columns]
            
            print(f"{Fore.CYAN}Inserindo {len(data)} registros de exemplo...")
            
            placeholders = ", ".join(["?" for _ in column_names])
            sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
            
            for record in data:
                conn.execute(sql, record)
            
            conn.commit()
            print(f"{Fore.GREEN}✅ {len(data)} registros de exemplo inseridos!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao inserir dados de exemplo: {e}")
    
    def _validate_value(self, value, data_type):
        """Validar valor de acordo com o tipo"""
        try:
            data_type_upper = data_type.upper()
            
            if "INTEGER" in data_type_upper:
                int(value)
            elif "DECIMAL" in data_type_upper or "NUMERIC" in data_type_upper:
                float(value)
            elif "BOOLEAN" in data_type_upper:
                if value.lower() not in ['true', 'false', '1', '0', 'sim', 'não', 's', 'n']:
                    return False
            elif "DATE" in data_type_upper:
                # Aceitar formatos básicos YYYY-MM-DD
                if len(value) != 10 or value.count('-') != 2:
                    return False
            # VARCHAR e TEXT sempre são válidos
            
            return True
            
        except:
            return False
    
    def update_records(self):
        """Atualizar registros"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║                  ATUALIZAR REGISTROS                     ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        # Listar tabelas disponíveis
        try:
            conn = self._get_connection()
            tables = conn.execute("SELECT table_name FROM duckdb_tables() ORDER BY table_name").fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}Nenhuma tabela encontrada!")
                conn.close()
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            print(f"\n{Fore.CYAN}📋 TABELAS DISPONÍVEIS:")
            for i, table in enumerate(tables, 1):
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                    print(f"{Fore.WHITE}[{i}] {table[0]} ({count:,} registros)")
                except:
                    print(f"{Fore.WHITE}[{i}] {table[0]} (erro ao contar)")
            
            choice = input(f"\n{Fore.WHITE}Escolha a tabela (1-{len(tables)}): {Fore.GREEN}").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(tables):
                    table_name = tables[choice_num - 1][0]
                    self._update_table_records(table_name)
                else:
                    print(f"{Fore.RED}Número inválido!")
            except ValueError:
                print(f"{Fore.RED}Por favor, digite um número válido!")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao acessar tabelas: {e}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _update_table_records(self, table_name):
        """Atualizar registros de uma tabela"""
        print(f"\n{Fore.YELLOW}ATUALIZAR REGISTROS EM: {table_name.upper()}")
        
        try:
            conn = self._get_connection()
            
            # Verificar se tem registros
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            if count == 0:
                print(f"\n{Fore.YELLOW}Tabela está vazia! Não há registros para atualizar.")
                conn.close()
                return
            
            # Obter estrutura da tabela
            columns = conn.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM duckdb_columns()
                WHERE table_name = '{table_name}'
                ORDER BY column_index
            """).fetchall()
            
            print(f"\n{Fore.CYAN}📊 Total de registros: {count:,}")
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Atualizar registro específico por ID")
            print(f"{Fore.WHITE}[2] Atualizar registros com filtro")
            print(f"{Fore.WHITE}[3] Atualizar todos os registros")
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._update_by_id(conn, table_name, columns)
            elif choice == "2":
                self._update_with_filter(conn, table_name, columns)
            elif choice == "3":
                self._update_all_records(conn, table_name, columns)
            elif choice == "0":
                pass
            else:
                print(f"{Fore.RED}Opção inválida!")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao preparar atualização: {e}")
    
    def _update_by_id(self, conn, table_name, columns):
        """Atualizar registro específico por ID"""
        print(f"\n{Fore.YELLOW}ATUALIZAR POR ID")
        
        # Verificar se tem coluna ID
        id_column = None
        for col in columns:
            if col[0].lower() == 'id':
                id_column = col[0]
                break
        
        if not id_column:
            print(f"{Fore.RED}Tabela não possui coluna 'id'!")
            return
        
        # Mostrar alguns registros para referência
        try:
            sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 10").fetchall()
            if sample:
                print(f"\n{Fore.CYAN}📋 Registros disponíveis (primeiros 10):")
                col_names = [col[0] for col in columns]
                
                # Cabeçalho
                header = " | ".join(f"{name[:10]:<10}" for name in col_names[:5])  # Primeiras 5 colunas
                print(f"\n{Fore.WHITE}{header}")
                print(f"{Fore.WHITE}{'-' * len(header)}")
                
                # Dados
                for row in sample:
                    row_str = " | ".join(f"{str(val)[:10]:<10}" for val in row[:5])
                    print(f"{Fore.GREEN}{row_str}")
        except:
            pass
        
        record_id = input(f"\n{Fore.WHITE}ID do registro a atualizar: {Fore.GREEN}").strip()
        
        if not record_id:
            print(f"{Fore.RED}ID não pode estar vazio!")
            return
        
        # Verificar se o registro existe
        try:
            existing = conn.execute(f"SELECT * FROM {table_name} WHERE {id_column} = ?", [record_id]).fetchone()
            if not existing:
                print(f"{Fore.RED}Registro com ID {record_id} não encontrado!")
                return
            
            print(f"\n{Fore.CYAN}📄 Registro atual:")
            for i, col in enumerate(columns):
                print(f"{Fore.WHITE}  {col[0]}: {existing[i]}")
            
        except Exception as e:
            print(f"{Fore.RED}Erro ao buscar registro: {e}")
            return
        
        # Coletar novos valores
        updates = {}
        for col in columns:
            col_name, data_type, nullable = col
            
            if col_name.lower() == 'id':
                continue  # Não atualizar ID
            
            current_value = existing[columns.index(col)]
            
            print(f"\n{Fore.CYAN}Campo: {col_name} ({data_type})")
            print(f"{Fore.WHITE}Valor atual: {current_value}")
            
            new_value = input(f"{Fore.WHITE}Novo valor (ENTER para manter): {Fore.GREEN}").strip()
            
            if new_value:
                if self._validate_value(new_value, data_type):
                    updates[col_name] = new_value
                else:
                    print(f"{Fore.RED}Valor inválido! Campo não será atualizado.")
        
        if not updates:
            print(f"\n{Fore.YELLOW}Nenhum campo para atualizar!")
            return
        
        # Executar atualização
        try:
            set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
            values = list(updates.values()) + [record_id]
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ?"
            
            print(f"\n{Fore.CYAN}SQL: {sql}")
            print(f"{Fore.WHITE}Valores: {list(updates.values())}")
            
            confirm = input(f"\n{Fore.YELLOW}Confirmar atualização? (S/n): {Fore.GREEN}").strip().lower()
            if confirm == 'n':
                print(f"{Fore.CYAN}Operação cancelada.")
                return
            
            conn.execute(sql, values)
            conn.commit()
            
            print(f"{Fore.GREEN}✅ Registro ID {record_id} atualizado com sucesso!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao atualizar: {e}")
    
    def _update_with_filter(self, conn, table_name, columns):
        """Atualizar registros com filtro"""
        print(f"\n{Fore.YELLOW}ATUALIZAR COM FILTRO")
        
        # Escolher coluna para filtro
        print(f"\n{Fore.CYAN}Colunas disponíveis para filtro:")
        for i, col in enumerate(columns, 1):
            print(f"{Fore.WHITE}[{i}] {col[0]} ({col[1]})")
        
        choice = input(f"\n{Fore.WHITE}Escolha a coluna para filtro (1-{len(columns)}): {Fore.GREEN}").strip()
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(columns):
                filter_col = columns[choice_num - 1]
                filter_name, filter_type, _ = filter_col
            else:
                print(f"{Fore.RED}Número inválido!")
                return
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
            return
        
        # Valor do filtro
        filter_value = input(f"\n{Fore.WHITE}Valor para filtrar {filter_name}: {Fore.GREEN}").strip()
        
        if not filter_value:
            print(f"{Fore.RED}Valor do filtro não pode estar vazio!")
            return
        
        # Verificar quantos registros serão afetados
        try:
            count_affected = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {filter_name} = ?", [filter_value]).fetchone()[0]
            
            if count_affected == 0:
                print(f"{Fore.YELLOW}Nenhum registro encontrado com {filter_name} = {filter_value}")
                return
            
            print(f"\n{Fore.CYAN}📊 Registros que serão afetados: {count_affected}")
            
            # Mostrar amostra
            sample = conn.execute(f"SELECT * FROM {table_name} WHERE {filter_name} = ? LIMIT 5", [filter_value]).fetchall()
            if sample:
                print(f"\n{Fore.CYAN}📋 Amostra dos registros:")
                col_names = [col[0] for col in columns]
                
                header = " | ".join(f"{name[:10]:<10}" for name in col_names[:4])
                print(f"\n{Fore.WHITE}{header}")
                print(f"{Fore.WHITE}{'-' * len(header)}")
                
                for row in sample:
                    row_str = " | ".join(f"{str(val)[:10]:<10}" for val in row[:4])
                    print(f"{Fore.GREEN}{row_str}")
            
        except Exception as e:
            print(f"{Fore.RED}Erro ao verificar filtro: {e}")
            return
        
        # Coletar campos para atualizar
        updates = {}
        for col in columns:
            col_name, data_type, nullable = col
            
            if col_name.lower() == 'id':
                continue
            
            print(f"\n{Fore.CYAN}Atualizar {col_name} ({data_type})?")
            new_value = input(f"{Fore.WHITE}Novo valor (ENTER para pular): {Fore.GREEN}").strip()
            
            if new_value:
                if self._validate_value(new_value, data_type):
                    updates[col_name] = new_value
                else:
                    print(f"{Fore.RED}Valor inválido! Campo não será atualizado.")
        
        if not updates:
            print(f"\n{Fore.YELLOW}Nenhum campo para atualizar!")
            return
        
        # Executar atualização
        try:
            set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
            values = list(updates.values()) + [filter_value]
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {filter_name} = ?"
            
            print(f"\n{Fore.CYAN}SQL: {sql}")
            print(f"{Fore.WHITE}Valores: {list(updates.values())}")
            print(f"{Fore.YELLOW}⚠️  Isso atualizará {count_affected} registros!")
            
            confirm = input(f"\n{Fore.RED}Confirmar atualização? (digite 'SIM'): {Fore.WHITE}").strip()
            if confirm != 'SIM':
                print(f"{Fore.CYAN}Operação cancelada.")
                return
            
            conn.execute(sql, values)
            conn.commit()
            
            print(f"{Fore.GREEN}✅ {count_affected} registros atualizados com sucesso!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao atualizar: {e}")
    
    def _update_all_records(self, conn, table_name, columns):
        """Atualizar todos os registros"""
        print(f"\n{Fore.YELLOW}ATUALIZAR TODOS OS REGISTROS")
        
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        
        print(f"\n{Fore.RED}⚠️  ATENÇÃO!")
        print(f"{Fore.WHITE}Isso atualizará TODOS os {count:,} registros da tabela!")
        
        confirm = input(f"\n{Fore.RED}Continuar? (digite 'TODOS'): {Fore.WHITE}").strip()
        if confirm != 'TODOS':
            print(f"{Fore.CYAN}Operação cancelada.")
            return
        
        # Coletar campos para atualizar
        updates = {}
        for col in columns:
            col_name, data_type, nullable = col
            
            if col_name.lower() == 'id':
                continue
            
            print(f"\n{Fore.CYAN}Atualizar {col_name} ({data_type})?")
            new_value = input(f"{Fore.WHITE}Novo valor (ENTER para pular): {Fore.GREEN}").strip()
            
            if new_value:
                if self._validate_value(new_value, data_type):
                    updates[col_name] = new_value
                else:
                    print(f"{Fore.RED}Valor inválido! Campo não será atualizado.")
        
        if not updates:
            print(f"\n{Fore.YELLOW}Nenhum campo para atualizar!")
            return
        
        # Executar atualização
        try:
            set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
            values = list(updates.values())
            sql = f"UPDATE {table_name} SET {set_clause}"
            
            print(f"\n{Fore.CYAN}SQL: {sql}")
            print(f"{Fore.WHITE}Valores: {values}")
            
            final_confirm = input(f"\n{Fore.RED}CONFIRMAÇÃO FINAL - Atualizar {count:,} registros? (digite 'CONFIRMO'): {Fore.WHITE}").strip()
            if final_confirm != 'CONFIRMO':
                print(f"{Fore.CYAN}Operação cancelada.")
                return
            
            conn.execute(sql, values)
            conn.commit()
            
            print(f"{Fore.GREEN}✅ Todos os {count:,} registros foram atualizados!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao atualizar: {e}")
    
    def delete_records(self):
        """Deletar registros"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║                   DELETAR REGISTROS                      ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        # Listar tabelas disponíveis
        try:
            conn = self._get_connection()
            tables = conn.execute("SELECT table_name FROM duckdb_tables() ORDER BY table_name").fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}Nenhuma tabela encontrada!")
                conn.close()
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            print(f"\n{Fore.CYAN}📋 TABELAS DISPONÍVEIS:")
            for i, table in enumerate(tables, 1):
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                    print(f"{Fore.WHITE}[{i}] {table[0]} ({count:,} registros)")
                except:
                    print(f"{Fore.WHITE}[{i}] {table[0]} (erro ao contar)")
            
            choice = input(f"\n{Fore.WHITE}Escolha a tabela (1-{len(tables)}): {Fore.GREEN}").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(tables):
                    table_name = tables[choice_num - 1][0]
                    self._delete_table_records(table_name)
                else:
                    print(f"{Fore.RED}Número inválido!")
            except ValueError:
                print(f"{Fore.RED}Por favor, digite um número válido!")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao acessar tabelas: {e}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _delete_table_records(self, table_name):
        """Deletar registros de uma tabela"""
        print(f"\n{Fore.YELLOW}DELETAR REGISTROS DE: {table_name.upper()}")
        
        try:
            conn = self._get_connection()
            
            # Verificar se tem registros
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            if count == 0:
                print(f"\n{Fore.YELLOW}Tabela está vazia! Não há registros para deletar.")
                conn.close()
                return
            
            # Obter estrutura da tabela
            columns = conn.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM duckdb_columns()
                WHERE table_name = '{table_name}'
                ORDER BY column_index
            """).fetchall()
            
            print(f"\n{Fore.CYAN}📊 Total de registros: {count:,}")
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Deletar registro específico por ID")
            print(f"{Fore.WHITE}[2] Deletar registros com filtro")
            print(f"{Fore.WHITE}[3] Deletar todos os registros")
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._delete_by_id(conn, table_name, columns)
            elif choice == "2":
                self._delete_with_filter(conn, table_name, columns)
            elif choice == "3":
                self._delete_all_records(conn, table_name)
            elif choice == "0":
                pass
            else:
                print(f"{Fore.RED}Opção inválida!")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao preparar deleção: {e}")
    
    def _delete_by_id(self, conn, table_name, columns):
        """Deletar registro específico por ID"""
        print(f"\n{Fore.YELLOW}DELETAR POR ID")
        
        # Verificar se tem coluna ID
        id_column = None
        for col in columns:
            if col[0].lower() == 'id':
                id_column = col[0]
                break
        
        if not id_column:
            print(f"{Fore.RED}Tabela não possui coluna 'id'!")
            return
        
        # Mostrar alguns registros para referência
        try:
            sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 15").fetchall()
            if sample:
                print(f"\n{Fore.CYAN}📋 Registros disponíveis (primeiros 15):")
                col_names = [col[0] for col in columns]
                
                # Cabeçalho
                header = " | ".join(f"{name[:12]:<12}" for name in col_names[:4])
                print(f"\n{Fore.WHITE}{header}")
                print(f"{Fore.WHITE}{'-' * len(header)}")
                
                # Dados
                for row in sample:
                    row_str = " | ".join(f"{str(val)[:12]:<12}" for val in row[:4])
                    print(f"{Fore.GREEN}{row_str}")
        except:
            pass
        
        record_id = input(f"\n{Fore.WHITE}ID do registro a deletar: {Fore.GREEN}").strip()
        
        if not record_id:
            print(f"{Fore.RED}ID não pode estar vazio!")
            return
        
        # Verificar se o registro existe
        try:
            existing = conn.execute(f"SELECT * FROM {table_name} WHERE {id_column} = ?", [record_id]).fetchone()
            if not existing:
                print(f"{Fore.RED}Registro com ID {record_id} não encontrado!")
                return
            
            print(f"\n{Fore.CYAN}📄 Registro a ser deletado:")
            for i, col in enumerate(columns):
                print(f"{Fore.WHITE}  {col[0]}: {existing[i]}")
            
            print(f"\n{Fore.RED}⚠️  ATENÇÃO!")
            print(f"{Fore.WHITE}Este registro será deletado permanentemente!")
            
            confirm = input(f"\n{Fore.RED}Confirmar deleção? (digite 'DELETAR'): {Fore.WHITE}").strip()
            if confirm != 'DELETAR':
                print(f"{Fore.CYAN}Operação cancelada.")
                return
            
            # Executar deleção
            sql = f"DELETE FROM {table_name} WHERE {id_column} = ?"
            conn.execute(sql, [record_id])
            conn.commit()
            
            print(f"{Fore.GREEN}✅ Registro ID {record_id} deletado com sucesso!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao deletar: {e}")
    
    def _delete_with_filter(self, conn, table_name, columns):
        """Deletar registros com filtro"""
        print(f"\n{Fore.YELLOW}DELETAR COM FILTRO")
        
        # Escolher coluna para filtro
        print(f"\n{Fore.CYAN}Colunas disponíveis para filtro:")
        for i, col in enumerate(columns, 1):
            print(f"{Fore.WHITE}[{i}] {col[0]} ({col[1]})")
        
        choice = input(f"\n{Fore.WHITE}Escolha a coluna para filtro (1-{len(columns)}): {Fore.GREEN}").strip()
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(columns):
                filter_col = columns[choice_num - 1]
                filter_name, filter_type, _ = filter_col
            else:
                print(f"{Fore.RED}Número inválido!")
                return
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
            return
        
        # Valor do filtro
        filter_value = input(f"\n{Fore.WHITE}Valor para filtrar {filter_name}: {Fore.GREEN}").strip()
        
        if not filter_value:
            print(f"{Fore.RED}Valor do filtro não pode estar vazio!")
            return
        
        # Verificar quantos registros serão afetados
        try:
            count_affected = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {filter_name} = ?", [filter_value]).fetchone()[0]
            
            if count_affected == 0:
                print(f"{Fore.YELLOW}Nenhum registro encontrado com {filter_name} = {filter_value}")
                return
            
            print(f"\n{Fore.CYAN}📊 Registros que serão deletados: {count_affected}")
            
            # Mostrar amostra dos registros que serão deletados
            sample = conn.execute(f"SELECT * FROM {table_name} WHERE {filter_name} = ? LIMIT 10", [filter_value]).fetchall()
            if sample:
                print(f"\n{Fore.CYAN}📋 Amostra dos registros que serão DELETADOS:")
                col_names = [col[0] for col in columns]
                
                header = " | ".join(f"{name[:10]:<10}" for name in col_names[:4])
                print(f"\n{Fore.WHITE}{header}")
                print(f"{Fore.WHITE}{'-' * len(header)}")
                
                for row in sample:
                    row_str = " | ".join(f"{str(val)[:10]:<10}" for val in row[:4])
                    print(f"{Fore.RED}{row_str}")  # Em vermelho para destacar que serão deletados
                
                if count_affected > 10:
                    print(f"\n{Fore.YELLOW}... e mais {count_affected - 10} registros")
            
            print(f"\n{Fore.RED}⚠️  ATENÇÃO!")
            print(f"{Fore.WHITE}Isso deletará permanentemente {count_affected} registros!")
            
            confirm = input(f"\n{Fore.RED}Confirmar deleção? (digite 'DELETAR {count_affected}'): {Fore.WHITE}").strip()
            expected = f'DELETAR {count_affected}'
            
            if confirm != expected:
                print(f"{Fore.CYAN}Operação cancelada.")
                return
            
            # Executar deleção
            sql = f"DELETE FROM {table_name} WHERE {filter_name} = ?"
            conn.execute(sql, [filter_value])
            conn.commit()
            
            print(f"{Fore.GREEN}✅ {count_affected} registros deletados com sucesso!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao deletar: {e}")
    
    def _delete_all_records(self, conn, table_name):
        """Deletar todos os registros"""
        print(f"\n{Fore.YELLOW}DELETAR TODOS OS REGISTROS")
        
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        
        print(f"\n{Fore.RED}⚠️  ATENÇÃO MÁXIMA!")
        print(f"{Fore.WHITE}Isso deletará PERMANENTEMENTE todos os {count:,} registros da tabela!")
        print(f"{Fore.WHITE}A estrutura da tabela será mantida, apenas os dados serão removidos.")
        
        # Mostrar uma amostra do que será perdido
        try:
            sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()
            if sample:
                columns = conn.execute(f"""
                    SELECT column_name FROM duckdb_columns()
                    WHERE table_name = '{table_name}'
                    ORDER BY column_index
                """).fetchall()
                
                print(f"\n{Fore.CYAN}📋 Amostra dos dados que serão PERDIDOS:")
                col_names = [col[0] for col in columns]
                
                header = " | ".join(f"{name[:10]:<10}" for name in col_names[:4])
                print(f"\n{Fore.WHITE}{header}")
                print(f"{Fore.WHITE}{'-' * len(header)}")
                
                for row in sample:
                    row_str = " | ".join(f"{str(val)[:10]:<10}" for val in row[:4])
                    print(f"{Fore.RED}{row_str}")
                
                print(f"\n{Fore.YELLOW}... e mais {count - 5} registros")
        except:
            pass
        
        print(f"\n{Fore.RED}ESTA AÇÃO NÃO PODE SER DESFEITA!")
        
        confirm1 = input(f"\n{Fore.RED}Continuar? (digite 'SIM DELETAR TUDO'): {Fore.WHITE}").strip()
        if confirm1 != 'SIM DELETAR TUDO':
            print(f"{Fore.CYAN}Operação cancelada.")
            return
        
        print(f"\n{Fore.RED}CONFIRMAÇÃO FINAL!")
        print(f"{Fore.WHITE}Última chance para cancelar a operação...")
        
        confirm2 = input(f"\n{Fore.RED}DELETAR {count:,} REGISTROS? (digite 'CONFIRMO DELEÇÃO TOTAL'): {Fore.WHITE}").strip()
        if confirm2 != 'CONFIRMO DELEÇÃO TOTAL':
            print(f"{Fore.CYAN}Operação cancelada.")
            return
        
        # Executar deleção
        try:
            print(f"\n{Fore.YELLOW}Deletando todos os registros...")
            
            sql = f"DELETE FROM {table_name}"
            conn.execute(sql)
            conn.commit()
            
            # Verificar se foi realmente limpa
            new_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            print(f"{Fore.GREEN}✅ Todos os {count:,} registros foram deletados!")
            print(f"{Fore.WHITE}Registros restantes: {new_count}")
            
            if new_count == 0:
                print(f"{Fore.GREEN}Tabela completamente limpa!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao deletar todos os registros: {e}")
    
    def view_data(self):
        """Visualizar dados com paginação"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║              VISUALIZAR DADOS COM PAGINAÇÃO              ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        # Listar tabelas disponíveis
        try:
            conn = self._get_connection()
            tables = conn.execute("SELECT table_name FROM duckdb_tables() ORDER BY table_name").fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}Nenhuma tabela encontrada!")
                conn.close()
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            print(f"\n{Fore.CYAN}Tabelas disponíveis:")
            for i, table in enumerate(tables, 1):
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                    print(f"{Fore.WHITE}[{i}] {table[0]} ({count:,} registros)")
                except:
                    print(f"{Fore.WHITE}[{i}] {table[0]} (erro ao contar)")
            
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma tabela: {Fore.WHITE}").strip()
            
            try:
                choice_num = int(choice)
                if choice_num == 0:
                    conn.close()
                    return
                
                if 1 <= choice_num <= len(tables):
                    table_name = tables[choice_num - 1][0]
                    self._paginate_table_data(conn, table_name)
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
    
    def _paginate_table_data(self, conn, table_name):
        """Paginar dados de uma tabela"""
        try:
            # Obter contagem total e estrutura da tabela
            total_records = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            if total_records == 0:
                print(f"\n{Fore.YELLOW}A tabela '{table_name}' está vazia!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            # Obter informações das colunas
            columns_info = conn.execute(f"DESCRIBE {table_name}").fetchall()
            column_names = [col[0] for col in columns_info]
            
            # Configurações de paginação
            page_size = 20  # registros por página
            total_pages = (total_records + page_size - 1) // page_size
            current_page = 1
            current_filter = ""  # Filtro ativo
            
            while True:
                # Calcular offset
                offset = (current_page - 1) * page_size
                
                # Buscar dados da página atual
                base_sql = f"SELECT * FROM {table_name}"
                if current_filter:
                    sql = f"{base_sql} WHERE {current_filter} LIMIT {page_size} OFFSET {offset}"
                else:
                    sql = f"{base_sql} LIMIT {page_size} OFFSET {offset}"
                records = conn.execute(sql).fetchall()
                
                # Limpar tela e mostrar cabeçalho
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
                print(f"{Fore.CYAN}║           VISUALIZANDO DADOS: {table_name.upper():<27} ║")
                print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
                
                print(f"\n{Fore.WHITE}Página {current_page} de {total_pages} | Total: {total_records:,} registros")
                if current_filter:
                    print(f"{Fore.YELLOW}Filtro ativo: {current_filter}")
                print(f"{Fore.YELLOW}{'─' * 80}")
                
                # Mostrar cabeçalhos das colunas
                header = ""
                for col_name in column_names:
                    header += f"{col_name:<15} | "
                print(f"{Fore.CYAN}{header}")
                print(f"{Fore.YELLOW}{'─' * 80}")
                
                # Mostrar dados
                for record in records:
                    row = ""
                    for value in record:
                        # Formatar valor para exibição
                        if value is None:
                            display_value = "NULL"
                        elif isinstance(value, str) and len(value) > 12:
                            display_value = value[:12] + "..."
                        else:
                            display_value = str(value)
                        
                        row += f"{display_value:<15} | "
                    print(f"{Fore.WHITE}{row}")
                
                print(f"{Fore.YELLOW}{'─' * 80}")
                
                # Menu de navegação
                print(f"\n{Fore.GREEN}NAVEGAÇÃO:")
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
                    "[0] Voltar"
                ])
                
                for option in nav_options:
                    print(f"{Fore.WHITE}{option}")
                
                choice = input(f"\n{Fore.YELLOW}Escolha: {Fore.WHITE}").strip().upper()
                
                if choice == '0':
                    break
                elif choice == 'P' and current_page > 1:
                    current_page -= 1
                elif choice == 'N' and current_page < total_pages:
                    current_page += 1
                elif choice == 'G':
                    try:
                        page = int(input(f"{Fore.WHITE}Ir para página (1-{total_pages}): {Fore.GREEN}"))
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
                        new_size = int(input(f"{Fore.WHITE}Novo tamanho da página (1-100): {Fore.GREEN}"))
                        if 1 <= new_size <= 100:
                            page_size = new_size
                            total_pages = (total_records + page_size - 1) // page_size
                            current_page = 1  # Voltar para primeira página
                        else:
                            print(f"{Fore.RED}Tamanho inválido!")
                            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    except ValueError:
                        print(f"{Fore.RED}Digite um número válido!")
                        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                elif choice == 'E':
                    self._export_current_page(table_name, records, column_names, current_page)
                elif choice == 'F':
                    # Implementar filtro
                    current_filter = self._setup_table_filter(conn, table_name, columns_info)
                    if current_filter:
                        # Recalcular total com filtro
                        try:
                            filtered_count = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {current_filter}").fetchone()[0]
                            total_records = filtered_count
                            total_pages = (total_records + page_size - 1) // page_size
                            current_page = 1
                            print(f"{Fore.GREEN}✅ Filtro aplicado: {filtered_count} registros encontrados")
                        except Exception as e:
                            print(f"{Fore.RED}❌ Erro no filtro: {e}")
                            current_filter = ""
                        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                else:
                    print(f"{Fore.RED}Opção inválida!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao visualizar dados: {e}")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _export_current_page(self, table_name, records, column_names, page_num):
        """Exportar página atual para CSV"""
        try:
            import csv
            from datetime import datetime
            
            # Nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{table_name}_page_{page_num}_{timestamp}.csv"
            filepath = Path("data/exports") / filename
            
            # Criar diretório se não existir
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Escrever CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Cabeçalho
                writer.writerow(column_names)
                
                # Dados
                writer.writerows(records)
            
            print(f"\n{Fore.GREEN}✅ Página exportada para: {filepath}")
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao exportar: {e}")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def search_records(self):
        """Buscar/filtrar registros"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║                 BUSCAR/FILTRAR REGISTROS                 ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        # Listar tabelas disponíveis
        try:
            conn = self._get_connection()
            tables = conn.execute("SELECT table_name FROM duckdb_tables() ORDER BY table_name").fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}Nenhuma tabela encontrada!")
                conn.close()
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            print(f"\n{Fore.CYAN}Tabelas disponíveis:")
            for i, table in enumerate(tables, 1):
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                    print(f"{Fore.WHITE}[{i}] {table[0]} ({count:,} registros)")
                except:
                    print(f"{Fore.WHITE}[{i}] {table[0]} (erro ao contar)")
            
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma tabela: {Fore.WHITE}").strip()
            
            try:
                choice_num = int(choice)
                if choice_num == 0:
                    conn.close()
                    return
                
                if 1 <= choice_num <= len(tables):
                    table_name = tables[choice_num - 1][0]
                    self._search_in_table(conn, table_name)
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
    
    def _search_in_table(self, conn, table_name):
        """Interface de busca em uma tabela específica"""
        while True:
            try:
                # Obter informações das colunas
                columns_info = conn.execute(f"DESCRIBE {table_name}").fetchall()
                column_names = [col[0] for col in columns_info]
                
                print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
                print(f"{Fore.CYAN}║             BUSCA NA TABELA: {table_name.upper():<27} ║")
                print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
                
                print(f"\n{Fore.WHITE}Colunas disponíveis:")
                for i, col_name in enumerate(column_names, 1):
                    col_type = columns_info[i-1][1]  # Tipo da coluna
                    print(f"{Fore.WHITE}[{i}] {col_name} ({col_type})")
                
                print(f"\n{Fore.GREEN}TIPOS DE BUSCA:")
                print(f"{Fore.WHITE}[1] Busca por texto (LIKE)")
                print(f"{Fore.WHITE}[2] Busca exata")
                print(f"{Fore.WHITE}[3] Busca por intervalo numérico")
                print(f"{Fore.WHITE}[4] Busca por data")
                print(f"{Fore.WHITE}[5] Busca personalizada (SQL WHERE)")
                print(f"{Fore.WHITE}[6] Listar registros únicos de uma coluna")
                print(f"{Fore.WHITE}[0] Voltar")
                
                search_type = input(f"\n{Fore.YELLOW}Tipo de busca: {Fore.WHITE}").strip()
                
                if search_type == '0':
                    break
                elif search_type == '1':
                    self._text_search(conn, table_name, column_names)
                elif search_type == '2':
                    self._exact_search(conn, table_name, column_names)
                elif search_type == '3':
                    self._range_search(conn, table_name, column_names)
                elif search_type == '4':
                    self._date_search(conn, table_name, column_names)
                elif search_type == '5':
                    self._custom_search(conn, table_name)
                elif search_type == '6':
                    self._unique_values(conn, table_name, column_names)
                else:
                    print(f"{Fore.RED}Opção inválida!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    
            except Exception as e:
                print(f"{Fore.RED}❌ Erro na busca: {e}")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                break
    
    def _text_search(self, conn, table_name, column_names):
        """Busca por texto usando LIKE"""
        print(f"\n{Fore.YELLOW}BUSCA POR TEXTO")
        
        # Escolher coluna
        print(f"\n{Fore.WHITE}Colunas disponíveis:")
        for i, col_name in enumerate(column_names, 1):
            print(f"{Fore.WHITE}[{i}] {col_name}")
        
        col_choice = input(f"\n{Fore.GREEN}Escolha a coluna: {Fore.WHITE}").strip()
        
        try:
            col_index = int(col_choice) - 1
            if 0 <= col_index < len(column_names):
                column = column_names[col_index]
                
                search_term = input(f"\n{Fore.WHITE}Texto a buscar: {Fore.GREEN}").strip()
                if search_term:
                    sql = f"SELECT * FROM {table_name} WHERE {column} LIKE '%{search_term}%'"
                    self._execute_search(conn, sql, f"texto '{search_term}' na coluna '{column}'")
                else:
                    print(f"{Fore.RED}Termo de busca não pode estar vazio!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            else:
                print(f"{Fore.RED}Coluna inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                
        except ValueError:
            print(f"{Fore.RED}Digite um número válido!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _exact_search(self, conn, table_name, column_names):
        """Busca exata"""
        print(f"\n{Fore.YELLOW}BUSCA EXATA")
        
        # Escolher coluna
        print(f"\n{Fore.WHITE}Colunas disponíveis:")
        for i, col_name in enumerate(column_names, 1):
            print(f"{Fore.WHITE}[{i}] {col_name}")
        
        col_choice = input(f"\n{Fore.GREEN}Escolha a coluna: {Fore.WHITE}").strip()
        
        try:
            col_index = int(col_choice) - 1
            if 0 <= col_index < len(column_names):
                column = column_names[col_index]
                
                search_value = input(f"\n{Fore.WHITE}Valor exato a buscar: {Fore.GREEN}").strip()
                if search_value:
                    # Verificar se é número
                    try:
                        float(search_value)
                        sql = f"SELECT * FROM {table_name} WHERE {column} = {search_value}"
                    except ValueError:
                        sql = f"SELECT * FROM {table_name} WHERE {column} = '{search_value}'"
                    
                    self._execute_search(conn, sql, f"valor '{search_value}' na coluna '{column}'")
                else:
                    print(f"{Fore.RED}Valor não pode estar vazio!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            else:
                print(f"{Fore.RED}Coluna inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                
        except ValueError:
            print(f"{Fore.RED}Digite um número válido!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _range_search(self, conn, table_name, column_names):
        """Busca por intervalo numérico"""
        print(f"\n{Fore.YELLOW}BUSCA POR INTERVALO NUMÉRICO")
        
        # Escolher coluna
        print(f"\n{Fore.WHITE}Colunas disponíveis:")
        for i, col_name in enumerate(column_names, 1):
            print(f"{Fore.WHITE}[{i}] {col_name}")
        
        col_choice = input(f"\n{Fore.GREEN}Escolha a coluna: {Fore.WHITE}").strip()
        
        try:
            col_index = int(col_choice) - 1
            if 0 <= col_index < len(column_names):
                column = column_names[col_index]
                
                min_val = input(f"\n{Fore.WHITE}Valor mínimo (deixe vazio para sem limite): {Fore.GREEN}").strip()
                max_val = input(f"{Fore.WHITE}Valor máximo (deixe vazio para sem limite): {Fore.GREEN}").strip()
                
                conditions = []
                if min_val:
                    try:
                        float(min_val)
                        conditions.append(f"{column} >= {min_val}")
                    except ValueError:
                        print(f"{Fore.RED}Valor mínimo deve ser numérico!")
                        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                        return
                
                if max_val:
                    try:
                        float(max_val)
                        conditions.append(f"{column} <= {max_val}")
                    except ValueError:
                        print(f"{Fore.RED}Valor máximo deve ser numérico!")
                        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                        return
                
                if conditions:
                    where_clause = " AND ".join(conditions)
                    sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
                    self._execute_search(conn, sql, f"intervalo na coluna '{column}'")
                else:
                    print(f"{Fore.RED}Defina pelo menos um limite!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            else:
                print(f"{Fore.RED}Coluna inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                
        except ValueError:
            print(f"{Fore.RED}Digite um número válido!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _date_search(self, conn, table_name, column_names):
        """Busca por data"""
        print(f"\n{Fore.YELLOW}BUSCA POR DATA")
        
        # Escolher coluna
        print(f"\n{Fore.WHITE}Colunas disponíveis:")
        for i, col_name in enumerate(column_names, 1):
            print(f"{Fore.WHITE}[{i}] {col_name}")
        
        col_choice = input(f"\n{Fore.GREEN}Escolha a coluna: {Fore.WHITE}").strip()
        
        try:
            col_index = int(col_choice) - 1
            if 0 <= col_index < len(column_names):
                column = column_names[col_index]
                
                print(f"\n{Fore.CYAN}Formato de data: YYYY-MM-DD (ex: 2024-01-15)")
                date_from = input(f"{Fore.WHITE}Data inicial (deixe vazio para sem limite): {Fore.GREEN}").strip()
                date_to = input(f"{Fore.WHITE}Data final (deixe vazio para sem limite): {Fore.GREEN}").strip()
                
                conditions = []
                if date_from:
                    conditions.append(f"{column} >= '{date_from}'")
                
                if date_to:
                    conditions.append(f"{column} <= '{date_to}'")
                
                if conditions:
                    where_clause = " AND ".join(conditions)
                    sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
                    self._execute_search(conn, sql, f"período na coluna '{column}'")
                else:
                    print(f"{Fore.RED}Defina pelo menos uma data!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            else:
                print(f"{Fore.RED}Coluna inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                
        except ValueError:
            print(f"{Fore.RED}Digite um número válido!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _custom_search(self, conn, table_name):
        """Busca personalizada com SQL WHERE"""
        print(f"\n{Fore.YELLOW}BUSCA PERSONALIZADA (SQL WHERE)")
        print(f"{Fore.CYAN}Digite apenas a condição WHERE (sem a palavra WHERE)")
        print(f"{Fore.CYAN}Exemplo: name LIKE '%João%' AND age > 25")
        
        where_clause = input(f"\n{Fore.WHITE}Condição WHERE: {Fore.GREEN}").strip()
        
        if where_clause:
            sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
            self._execute_search(conn, sql, "condição personalizada")
        else:
            print(f"{Fore.RED}Condição não pode estar vazia!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _unique_values(self, conn, table_name, column_names):
        """Listar valores únicos de uma coluna"""
        print(f"\n{Fore.YELLOW}VALORES ÚNICOS")
        
        # Escolher coluna
        print(f"\n{Fore.WHITE}Colunas disponíveis:")
        for i, col_name in enumerate(column_names, 1):
            print(f"{Fore.WHITE}[{i}] {col_name}")
        
        col_choice = input(f"\n{Fore.GREEN}Escolha a coluna: {Fore.WHITE}").strip()
        
        try:
            col_index = int(col_choice) - 1
            if 0 <= col_index < len(column_names):
                column = column_names[col_index]
                
                sql = f"SELECT DISTINCT {column}, COUNT(*) as quantidade FROM {table_name} GROUP BY {column} ORDER BY quantidade DESC"
                self._execute_search(conn, sql, f"valores únicos da coluna '{column}'")
            else:
                print(f"{Fore.RED}Coluna inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                
        except ValueError:
            print(f"{Fore.RED}Digite um número válido!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _execute_search(self, conn, sql, description):
        """Executar busca e mostrar resultados"""
        try:
            print(f"\n{Fore.CYAN}Executando busca: {description}")
            print(f"{Fore.YELLOW}SQL: {sql}")
            
            results = conn.execute(sql).fetchall()
            
            if not results:
                print(f"\n{Fore.YELLOW}Nenhum registro encontrado!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            # Obter nomes das colunas do resultado
            columns_info = conn.execute(f"DESCRIBE ({sql})").fetchall()
            column_names = [col[0] for col in columns_info]
            
            print(f"\n{Fore.GREEN}✅ {len(results)} registro(s) encontrado(s)")
            print(f"{Fore.YELLOW}{'─' * 80}")
            
            # Mostrar cabeçalhos das colunas
            header = ""
            for col_name in column_names:
                header += f"{col_name:<15} | "
            print(f"{Fore.CYAN}{header}")
            print(f"{Fore.YELLOW}{'─' * 80}")
            
            # Mostrar dados (limitado a 50 registros)
            display_count = min(50, len(results))
            for i, record in enumerate(results[:display_count]):
                row = ""
                for value in record:
                    # Formatar valor para exibição
                    if value is None:
                        display_value = "NULL"
                    elif isinstance(value, str) and len(value) > 12:
                        display_value = value[:12] + "..."
                    else:
                        display_value = str(value)
                    
                    row += f"{display_value:<15} | "
                print(f"{Fore.WHITE}{row}")
            
            if len(results) > 50:
                print(f"\n{Fore.YELLOW}... e mais {len(results) - 50} registros")
                
                export_choice = input(f"\n{Fore.WHITE}Exportar todos os resultados? (s/N): {Fore.GREEN}").strip().lower()
                if export_choice == 's':
                    self._export_search_results(results, column_names, description)
            
            print(f"{Fore.YELLOW}{'─' * 80}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro na busca: {e}")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _export_search_results(self, results, column_names, description):
        """Exportar resultados da busca"""
        try:
            import csv
            from datetime import datetime
            
            # Nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_desc = "".join(c for c in description if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"busca_{safe_desc}_{timestamp}.csv".replace(' ', '_')
            filepath = Path("data/exports") / filename
            
            # Criar diretório se não existir
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Escrever CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Cabeçalho
                writer.writerow(column_names)
                
                # Dados
                writer.writerows(results)
            
            print(f"\n{Fore.GREEN}✅ Resultados exportados para: {filepath}")
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao exportar: {e}")
    
    def _setup_table_filter(self, conn, table_name, columns_info):
        """Configurar filtro para visualização de tabela"""
        print(f"\n{Fore.CYAN}📋 CONFIGURAR FILTRO PARA {table_name.upper()}:")
        print(f"{Fore.WHITE}Colunas disponíveis:")
        
        col_names = [col[0] for col in columns_info]
        for i, col in enumerate(col_names, 1):
            col_type = columns_info[i-1][1]  # Tipo da coluna
            print(f"{Fore.YELLOW}[{i}] {col} ({col_type})")
        
        print(f"{Fore.RED}[0] Remover filtro atual")
        
        try:
            choice = int(input(f"\n{Fore.CYAN}Escolha uma coluna para filtrar: "))
            
            if choice == 0:
                print(f"{Fore.GREEN}✅ Filtro removido")
                return ""
            elif 1 <= choice <= len(col_names):
                col_name = col_names[choice - 1]
                col_type = columns_info[choice - 1][1]
                
                print(f"\n{Fore.CYAN}Tipos de filtro para '{col_name}' ({col_type}):")
                print(f"{Fore.WHITE}[1] Contém texto (LIKE)")
                print(f"{Fore.WHITE}[2] Igual a (=)")
                print(f"{Fore.WHITE}[3] Maior que (>)")
                print(f"{Fore.WHITE}[4] Menor que (<)")
                print(f"{Fore.WHITE}[5] Entre valores (BETWEEN)")
                print(f"{Fore.WHITE}[6] É nulo (IS NULL)")
                print(f"{Fore.WHITE}[7] Não é nulo (IS NOT NULL)")
                
                filter_type = int(input(f"\n{Fore.CYAN}Tipo de filtro: "))
                
                if filter_type == 1:
                    value = input(f"{Fore.WHITE}Texto para buscar: ").strip()
                    if value:
                        return f"{col_name} LIKE '%{value}%'"
                elif filter_type == 2:
                    value = input(f"{Fore.WHITE}Valor exato: ").strip()
                    if value:
                        if 'VARCHAR' in col_type.upper() or 'TEXT' in col_type.upper():
                            return f"{col_name} = '{value}'"
                        else:
                            return f"{col_name} = {value}"
                elif filter_type == 3:
                    value = input(f"{Fore.WHITE}Maior que: ").strip()
                    if value:
                        return f"{col_name} > {value}"
                elif filter_type == 4:
                    value = input(f"{Fore.WHITE}Menor que: ").strip()
                    if value:
                        return f"{col_name} < {value}"
                elif filter_type == 5:
                    min_val = input(f"{Fore.WHITE}Valor mínimo: ").strip()
                    max_val = input(f"{Fore.WHITE}Valor máximo: ").strip()
                    if min_val and max_val:
                        return f"{col_name} BETWEEN {min_val} AND {max_val}"
                elif filter_type == 6:
                    return f"{col_name} IS NULL"
                elif filter_type == 7:
                    return f"{col_name} IS NOT NULL"
            
        except (ValueError, IndexError):
            print(f"{Fore.RED}❌ Opção inválida!")
        
        return ""