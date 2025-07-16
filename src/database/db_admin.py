"""
Administração do banco de dados
"""
import os
import time
from pathlib import Path
from colorama import Fore, Style
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager

class DatabaseAdmin:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
    
    def _format_size(self, size_bytes):
        """Formatar tamanho em bytes para formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def show_structure(self):
        """Ver estrutura das tabelas"""
        try:
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║               ESTRUTURA DAS TABELAS                      ║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
            
            conn = self.db_manager._get_connection()
            
            # Listar todas as tabelas
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main' 
                ORDER BY table_name
            """
            tables = conn.execute(tables_query).fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}⚠️ Nenhuma tabela encontrada no banco de dados!")
                conn.close()
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            print(f"\n{Fore.WHITE}📊 Total de tabelas encontradas: {len(tables)}")
            print(f"{Fore.MAGENTA}{'─'*60}")
            
            for table in tables:
                table_name = table[0]
                print(f"\n{Fore.YELLOW}📋 TABELA: {table_name.upper()}")
                
                # Obter estrutura da tabela
                structure = conn.execute(f"DESCRIBE {table_name}").fetchall()
                
                # Obter contagem de registros
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                
                print(f"{Fore.CYAN}   📊 Registros: {count:,}")
                print(f"{Fore.CYAN}   🏗️  Estrutura:")
                
                # Cabeçalho da tabela de estrutura
                print(f"{Fore.WHITE}      {'Campo':<20} {'Tipo':<15} {'Nulo':<8} {'Chave':<10}")
                print(f"{Fore.WHITE}      {'-'*20} {'-'*15} {'-'*8} {'-'*10}")
                
                for col in structure:
                    col_name = col[0]
                    col_type = col[1]
                    is_null = "Sim" if col[2] else "Não"
                    is_key = "PK" if col[3] else "-"
                    
                    print(f"{Fore.GREEN}      {col_name:<20} {col_type:<15} {is_null:<8} {is_key:<10}")
                
                # Verificar se há índices
                try:
                    indexes_query = f"""
                        SELECT sql FROM sqlite_master 
                        WHERE type = 'index' AND tbl_name = '{table_name}' 
                        AND sql IS NOT NULL
                    """
                    indexes = conn.execute(indexes_query).fetchall()
                    
                    if indexes:
                        print(f"{Fore.YELLOW}   🔍 Índices:")
                        for idx in indexes:
                            idx_sql = idx[0]
                            print(f"{Fore.CYAN}      • {idx_sql}")
                    else:
                        print(f"{Fore.YELLOW}   🔍 Índices: Nenhum índice customizado")
                except:
                    # DuckDB pode não ter sqlite_master
                    print(f"{Fore.YELLOW}   🔍 Índices: Informação não disponível")
                
                print(f"{Fore.MAGENTA}   {'-'*50}")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar estrutura: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro ao obter estrutura das tabelas: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def manage_indexes(self):
        """Criar/alterar índices"""
        try:
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║                  GERENCIAR ÍNDICES                       ║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
            
            while True:
                print(f"\n{Fore.YELLOW}OPÇÕES DE ÍNDICES:")
                print(f"{Fore.WHITE}[1] Criar índices recomendados")
                print(f"{Fore.WHITE}[2] Listar índices existentes")
                print(f"{Fore.WHITE}[3] Criar índice personalizado")
                print(f"{Fore.WHITE}[4] Remover índice")
                print(f"{Fore.RED}[0] Voltar")
                
                choice = input(f"\n{Fore.GREEN}Escolha: {Style.RESET_ALL}").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    self._create_recommended_indexes()
                elif choice == '2':
                    self._list_indexes()
                elif choice == '3':
                    self._create_custom_index()
                elif choice == '4':
                    self._remove_index()
                else:
                    print(f"{Fore.RED}Opção inválida!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    
        except Exception as e:
            self.logger.error(f"Erro no gerenciamento de índices: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro: {str(e)}")
            input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _create_recommended_indexes(self):
        """Criar índices recomendados para performance"""
        try:
            print(f"\n{Fore.CYAN}🔍 CRIANDO ÍNDICES RECOMENDADOS...")
            
            conn = self.db_manager._get_connection()
            
            # Índices recomendados para melhorar performance
            recommended_indexes = [
                ("idx_restaurants_city", "restaurants", "city"),
                ("idx_restaurants_category", "restaurants", "category"),
                ("idx_restaurants_rating", "restaurants", "rating"),
                ("idx_products_restaurant_id", "products", "restaurant_id"),
                ("idx_products_category", "products", "category"),
                ("idx_products_price", "products", "price"),
                ("idx_categories_name", "categories", "categorias"),
                ("idx_restaurants_name", "restaurants", "name")
            ]
            
            created_count = 0
            skipped_count = 0
            
            for idx_name, table_name, column_name in recommended_indexes:
                try:
                    # Verificar se a tabela existe
                    table_exists = conn.execute(f"""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_name = '{table_name}'
                    """).fetchone()[0]
                    
                    if table_exists == 0:
                        print(f"{Fore.YELLOW}   ⚠️ Tabela '{table_name}' não existe - pulando índice {idx_name}")
                        skipped_count += 1
                        continue
                    
                    # Tentar criar índice
                    create_sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name})"
                    conn.execute(create_sql)
                    
                    print(f"{Fore.GREEN}   ✅ Índice criado: {idx_name} em {table_name}({column_name})")
                    created_count += 1
                    
                except Exception as e:
                    print(f"{Fore.RED}   ❌ Erro ao criar {idx_name}: {str(e)}")
                    skipped_count += 1
            
            conn.commit()
            conn.close()
            
            print(f"\n{Fore.CYAN}📊 RESUMO:")
            print(f"{Fore.GREEN}   ✅ Índices criados: {created_count}")
            print(f"{Fore.YELLOW}   ⚠️ Índices pulados: {skipped_count}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao criar índices recomendados: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _list_indexes(self):
        """Listar índices existentes"""
        try:
            print(f"\n{Fore.CYAN}📋 ÍNDICES EXISTENTES:")
            
            conn = self.db_manager._get_connection()
            
            # Tentar listar índices (método pode variar entre bancos)
            try:
                # Para DuckDB/SQLite
                indexes = conn.execute("""
                    SELECT name, sql FROM sqlite_master 
                    WHERE type = 'index' AND sql IS NOT NULL
                    ORDER BY name
                """).fetchall()
                
                if indexes:
                    print(f"{Fore.WHITE}{'Nome do Índice':<30} {'Definição'}")
                    print(f"{Fore.WHITE}{'-'*30} {'-'*40}")
                    
                    for idx in indexes:
                        idx_name = idx[0]
                        idx_sql = idx[1]
                        print(f"{Fore.GREEN}{idx_name:<30} {idx_sql}")
                else:
                    print(f"{Fore.YELLOW}   ⚠️ Nenhum índice personalizado encontrado")
                    
            except:
                # Método alternativo se sqlite_master não estiver disponível
                print(f"{Fore.YELLOW}   ⚠️ Informações de índices não disponíveis para este tipo de banco")
            
            conn.close()
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao listar índices: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _create_custom_index(self):
        """Criar índice personalizado"""
        try:
            print(f"\n{Fore.CYAN}🔧 CRIAR ÍNDICE PERSONALIZADO:")
            
            # Listar tabelas disponíveis
            conn = self.db_manager._get_connection()
            tables = conn.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'main' ORDER BY table_name
            """).fetchall()
            
            if not tables:
                print(f"{Fore.YELLOW}⚠️ Nenhuma tabela encontrada!")
                conn.close()
                return
            
            print(f"{Fore.WHITE}Tabelas disponíveis:")
            for i, table in enumerate(tables, 1):
                print(f"{Fore.YELLOW}[{i}] {table[0]}")
            
            table_choice = int(input(f"\n{Fore.WHITE}Escolha uma tabela: ")) - 1
            
            if 0 <= table_choice < len(tables):
                table_name = tables[table_choice][0]
                
                # Listar colunas da tabela
                columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                
                print(f"\n{Fore.WHITE}Colunas disponíveis em '{table_name}':")
                for i, col in enumerate(columns, 1):
                    print(f"{Fore.YELLOW}[{i}] {col[0]} ({col[1]})")
                
                col_choice = int(input(f"\n{Fore.WHITE}Escolha uma coluna: ")) - 1
                
                if 0 <= col_choice < len(columns):
                    column_name = columns[col_choice][0]
                    
                    idx_name = input(f"\n{Fore.WHITE}Nome do índice (ou ENTER para automático): ").strip()
                    if not idx_name:
                        idx_name = f"idx_{table_name}_{column_name}"
                    
                    # Criar índice
                    create_sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name})"
                    conn.execute(create_sql)
                    conn.commit()
                    
                    print(f"\n{Fore.GREEN}✅ Índice '{idx_name}' criado com sucesso!")
                else:
                    print(f"{Fore.RED}Coluna inválida!")
            else:
                print(f"{Fore.RED}Tabela inválida!")
            
            conn.close()
            
        except (ValueError, IndexError):
            print(f"{Fore.RED}❌ Entrada inválida!")
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao criar índice: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _remove_index(self):
        """Remover índice"""
        try:
            print(f"\n{Fore.CYAN}🗑️ REMOVER ÍNDICE:")
            
            conn = self.db_manager._get_connection()
            
            # Listar índices existentes
            try:
                indexes = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type = 'index' AND sql IS NOT NULL
                    ORDER BY name
                """).fetchall()
                
                if not indexes:
                    print(f"{Fore.YELLOW}⚠️ Nenhum índice personalizado encontrado!")
                    conn.close()
                    return
                
                print(f"{Fore.WHITE}Índices disponíveis:")
                for i, idx in enumerate(indexes, 1):
                    print(f"{Fore.YELLOW}[{i}] {idx[0]}")
                
                idx_choice = int(input(f"\n{Fore.WHITE}Escolha um índice para remover: ")) - 1
                
                if 0 <= idx_choice < len(indexes):
                    idx_name = indexes[idx_choice][0]
                    
                    confirm = input(f"\n{Fore.RED}Confirma remoção do índice '{idx_name}'? (s/N): ").strip().lower()
                    
                    if confirm == 's':
                        conn.execute(f"DROP INDEX IF EXISTS {idx_name}")
                        conn.commit()
                        print(f"\n{Fore.GREEN}✅ Índice '{idx_name}' removido!")
                    else:
                        print(f"\n{Fore.CYAN}Operação cancelada.")
                else:
                    print(f"{Fore.RED}Índice inválido!")
                    
            except:
                print(f"{Fore.YELLOW}⚠️ Não foi possível listar índices")
            
            conn.close()
            
        except (ValueError, IndexError):
            print(f"{Fore.RED}❌ Entrada inválida!")
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao remover índice: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def analyze_performance(self):
        """Analisar performance de consultas"""
        try:
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║                ANÁLISE DE PERFORMANCE                    ║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
            
            conn = self.db_manager._get_connection()
            
            # Análise básica de performance
            print(f"\n{Fore.YELLOW}📊 ESTATÍSTICAS GERAIS:")
            
            # Verificar tamanhos das tabelas
            tables = conn.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'main' ORDER BY table_name
            """).fetchall()
            
            print(f"{Fore.WHITE}{'Tabela':<20} {'Registros':<12} {'Performance'}")
            print(f"{Fore.WHITE}{'-'*20} {'-'*12} {'-'*15}")
            
            total_records = 0
            
            for table in tables:
                table_name = table[0]
                
                # Contar registros com medição de tempo
                start_time = time.time()
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                query_time = time.time() - start_time
                
                total_records += count
                
                # Análise de performance baseada no tempo de consulta
                if query_time < 0.1:
                    perf_status = f"{Fore.GREEN}Excelente"
                elif query_time < 0.5:
                    perf_status = f"{Fore.YELLOW}Boa"
                elif query_time < 1.0:
                    perf_status = f"{Fore.YELLOW}Aceitável"
                else:
                    perf_status = f"{Fore.RED}Lenta"
                
                print(f"{Fore.CYAN}{table_name:<20} {count:,<12} {perf_status} ({query_time:.3f}s)")
            
            print(f"\n{Fore.WHITE}📈 Total de registros: {total_records:,}")
            
            # Teste de consultas complexas
            print(f"\n{Fore.YELLOW}🔍 TESTE DE CONSULTAS COMPLEXAS:")
            
            complex_queries = [
                ("Restaurantes por categoria", "SELECT category, COUNT(*) FROM restaurants GROUP BY category"),
                ("Produtos mais caros", "SELECT restaurant_name, name, price FROM products WHERE price IS NOT NULL ORDER BY price DESC LIMIT 10"),
                ("Estatísticas de rating", "SELECT AVG(rating), MIN(rating), MAX(rating) FROM restaurants WHERE rating IS NOT NULL")
            ]
            
            for query_name, sql in complex_queries:
                try:
                    start_time = time.time()
                    result = conn.execute(sql).fetchall()
                    query_time = time.time() - start_time
                    
                    if query_time < 0.1:
                        perf_icon = f"{Fore.GREEN}⚡"
                    elif query_time < 0.5:
                        perf_icon = f"{Fore.YELLOW}⏱️"
                    else:
                        perf_icon = f"{Fore.RED}🐌"
                    
                    print(f"{perf_icon} {query_name}: {query_time:.3f}s ({len(result)} resultados)")
                    
                except Exception as e:
                    print(f"{Fore.RED}❌ {query_name}: Erro - {str(e)}")
            
            # Recomendações de otimização
            print(f"\n{Fore.YELLOW}💡 RECOMENDAÇÕES DE OTIMIZAÇÃO:")
            
            # Verificar se há tabelas grandes sem índices
            for table in tables:
                table_name = table[0]
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                
                if count > 1000:
                    print(f"{Fore.CYAN}• Tabela '{table_name}' tem {count:,} registros")
                    print(f"{Fore.WHITE}  Recomenda-se criar índices em colunas frequentemente consultadas")
            
            # Verificar fragmentação (simulado)
            if total_records > 10000:
                print(f"{Fore.CYAN}• Banco com {total_records:,} registros")
                print(f"{Fore.WHITE}  Considere executar VACUUM periodicamente")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro na análise de performance: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro na análise: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def check_size(self):
        """Verificar tamanho do banco"""
        try:
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║                 TAMANHO DO BANCO                         ║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
            
            # Verificar tamanho do arquivo do banco
            db_path = self.db_manager.db_path
            
            if os.path.exists(db_path):
                file_size = os.path.getsize(db_path)
                print(f"\n{Fore.WHITE}📁 Arquivo do banco: {db_path}")
                print(f"{Fore.GREEN}📊 Tamanho do arquivo: {self._format_size(file_size)}")
            else:
                print(f"\n{Fore.YELLOW}⚠️ Arquivo do banco não encontrado: {db_path}")
                return
            
            # Análise por tabela
            conn = self.db_manager._get_connection()
            
            print(f"\n{Fore.YELLOW}📋 ANÁLISE POR TABELA:")
            print(f"{Fore.WHITE}{'Tabela':<20} {'Registros':<12} {'Est. Tamanho':<12} {'%':<8}")
            print(f"{Fore.WHITE}{'-'*20} {'-'*12} {'-'*12} {'-'*8}")
            
            tables = conn.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'main' ORDER BY table_name
            """).fetchall()
            
            total_records = 0
            table_sizes = []
            
            for table in tables:
                table_name = table[0]
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                total_records += count
                
                # Estimativa de tamanho baseada no número de registros
                # (estimativa aproximada: ~500 bytes por registro em média)
                estimated_size = count * 500
                table_sizes.append((table_name, count, estimated_size))
            
            # Calcular percentuais
            for table_name, count, estimated_size in table_sizes:
                percentage = (count / total_records * 100) if total_records > 0 else 0
                
                print(f"{Fore.CYAN}{table_name:<20} {count:,<12} {self._format_size(estimated_size):<12} {percentage:.1f}%")
            
            print(f"\n{Fore.WHITE}📈 RESUMO GERAL:")
            print(f"{Fore.GREEN}   • Total de registros: {total_records:,}")
            print(f"{Fore.GREEN}   • Total de tabelas: {len(tables)}")
            print(f"{Fore.GREEN}   • Tamanho do arquivo: {self._format_size(file_size)}")
            
            # Verificar espaço em disco disponível
            try:
                import shutil
                free_space = shutil.disk_usage(os.path.dirname(db_path)).free
                print(f"{Fore.CYAN}   • Espaço livre em disco: {self._format_size(free_space)}")
                
                # Alertas baseados no espaço disponível
                if free_space < file_size * 10:  # Menos que 10x o tamanho do banco
                    print(f"{Fore.YELLOW}   ⚠️ Pouco espaço em disco disponível!")
                
            except:
                print(f"{Fore.YELLOW}   • Espaço em disco: Não foi possível verificar")
            
            # Histórico de crescimento (simulado)
            print(f"\n{Fore.YELLOW}📈 INFORMAÇÕES ADICIONAIS:")
            
            # Verificar quando foi a última modificação
            mod_time = os.path.getmtime(db_path)
            from datetime import datetime
            last_mod = datetime.fromtimestamp(mod_time).strftime("%d/%m/%Y %H:%M:%S")
            print(f"{Fore.CYAN}   • Última modificação: {last_mod}")
            
            # Idade do arquivo
            age_days = (time.time() - mod_time) / (24 * 3600)
            print(f"{Fore.CYAN}   • Idade do banco: {age_days:.1f} dias")
            
            if age_days > 30:
                print(f"{Fore.YELLOW}   💡 Considere fazer backup periódico")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar tamanho: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro ao verificar tamanho: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def vacuum_database(self):
        """Vacuum/otimizar banco"""
        try:
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║               OTIMIZAÇÃO DO BANCO                        ║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
            
            # Verificar tamanho antes
            db_path = self.db_manager.db_path
            if not os.path.exists(db_path):
                print(f"\n{Fore.YELLOW}⚠️ Arquivo do banco não encontrado!")
                return
            
            size_before = os.path.getsize(db_path)
            print(f"\n{Fore.WHITE}📊 Tamanho antes da otimização: {self._format_size(size_before)}")
            
            # Confirmar operação
            print(f"\n{Fore.YELLOW}⚠️ ATENÇÃO:")
            print(f"{Fore.WHITE}A otimização pode demorar alguns minutos dependendo do tamanho do banco.")
            print(f"{Fore.WHITE}Durante o processo, o banco ficará temporariamente bloqueado.")
            
            confirm = input(f"\n{Fore.CYAN}Continuar com a otimização? (s/N): ").strip().lower()
            
            if confirm != 's':
                print(f"\n{Fore.CYAN}Operação cancelada.")
                return
            
            print(f"\n{Fore.CYAN}🔧 Iniciando otimização...")
            
            conn = self.db_manager._get_connection()
            
            start_time = time.time()
            
            # Executar comandos de otimização
            optimization_commands = [
                ("VACUUM", "Desfragmentação do banco"),
                ("ANALYZE", "Atualização de estatísticas"),
            ]
            
            for command, description in optimization_commands:
                try:
                    print(f"{Fore.YELLOW}   🔄 {description}...")
                    conn.execute(command)
                    print(f"{Fore.GREEN}   ✅ {description} concluída")
                except Exception as e:
                    print(f"{Fore.RED}   ❌ Erro em {description}: {str(e)}")
            
            # Recriar estatísticas para tabelas específicas
            try:
                tables = conn.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'main'
                """).fetchall()
                
                print(f"{Fore.YELLOW}   🔄 Atualizando estatísticas das tabelas...")
                for table in tables:
                    try:
                        conn.execute(f"ANALYZE {table[0]}")
                    except:
                        pass  # Nem todos os bancos suportam ANALYZE por tabela
                
                print(f"{Fore.GREEN}   ✅ Estatísticas atualizadas")
                
            except:
                print(f"{Fore.YELLOW}   ⚠️ Atualização de estatísticas não disponível")
            
            conn.close()
            
            # Verificar tamanho depois
            size_after = os.path.getsize(db_path)
            optimization_time = time.time() - start_time
            
            print(f"\n{Fore.GREEN}🎯 OTIMIZAÇÃO CONCLUÍDA!")
            print(f"{Fore.WHITE}⏱️  Tempo de execução: {optimization_time:.2f} segundos")
            print(f"{Fore.WHITE}📊 Tamanho antes: {self._format_size(size_before)}")
            print(f"{Fore.WHITE}📊 Tamanho depois: {self._format_size(size_after)}")
            
            # Calcular economia
            if size_after < size_before:
                saved_space = size_before - size_after
                saved_percent = (saved_space / size_before) * 100
                print(f"{Fore.GREEN}💾 Espaço economizado: {self._format_size(saved_space)} ({saved_percent:.1f}%)")
            elif size_after > size_before:
                print(f"{Fore.YELLOW}📈 Tamanho aumentou (normal após reorganização)")
            else:
                print(f"{Fore.CYAN}📊 Tamanho mantido (banco já estava otimizado)")
            
            print(f"\n{Fore.CYAN}💡 RECOMENDAÇÕES:")
            print(f"{Fore.WHITE}   • Execute VACUUM mensalmente em bancos com alta atividade")
            print(f"{Fore.WHITE}   • Monitore o crescimento do banco regularmente")
            print(f"{Fore.WHITE}   • Considere arquivar dados antigos se necessário")
            
        except Exception as e:
            self.logger.error(f"Erro na otimização: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro durante otimização: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")