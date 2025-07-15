"""
Utilitários do banco de dados
"""
import os
from colorama import Fore, Back, Style
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager

class DatabaseUtils:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
    
    def clean_duplicates(self):
        """Limpeza de dados duplicados"""
        print(f"\n{Back.BLUE}{Fore.WHITE} LIMPEZA DE DADOS DUPLICADOS {Style.RESET_ALL}")
        print(f"{Fore.CYAN}┌{'─'*58}┐")
        print(f"{Fore.CYAN}│{'Analisando tabelas para encontrar duplicatas':^56}│")
        print(f"{Fore.CYAN}└{'─'*58}┘")
        
        try:
            conn = self.db_manager._get_connection()
            
            # Obter lista de tabelas
            tables = conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main'
            """).fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}⚠️  Nenhuma tabela encontrada no banco de dados.")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            total_duplicates_removed = 0
            
            print(f"\n{Fore.WHITE}📊 Tabelas encontradas: {len(tables)}")
            print(f"{Fore.CYAN}{'─'*60}")
            
            for table_row in tables:
                table_name = table_row[0]
                print(f"\n{Fore.YELLOW}🔍 Analisando tabela: {table_name}")
                
                try:
                    # Contar total de registros
                    total_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    
                    if total_count == 0:
                        print(f"{Fore.WHITE}   ✅ Tabela vazia - nada para limpar")
                        continue
                    
                    # Obter estrutura da tabela para identificar colunas
                    columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                    column_names = [col[0] for col in columns if col[0] != 'id']
                    
                    if not column_names:
                        print(f"{Fore.WHITE}   ⚠️  Apenas coluna ID encontrada - pulando")
                        continue
                    
                    # Criar query para encontrar duplicatas (ignorando ID)
                    columns_str = ', '.join(column_names)
                    
                    # Contar duplicatas
                    duplicate_query = f"""
                        SELECT {columns_str}, COUNT(*) as count
                        FROM {table_name} 
                        GROUP BY {columns_str} 
                        HAVING COUNT(*) > 1
                    """
                    
                    duplicates = conn.execute(duplicate_query).fetchall()
                    
                    if not duplicates:
                        print(f"{Fore.GREEN}   ✅ Nenhuma duplicata encontrada ({total_count} registros únicos)")
                        continue
                    
                    # Calcular quantos registros serão removidos
                    duplicates_to_remove = sum(row[-1] - 1 for row in duplicates)  # -1 porque mantemos um
                    
                    print(f"{Fore.RED}   🔥 {len(duplicates)} grupos de duplicatas encontrados")
                    print(f"{Fore.RED}   📉 {duplicates_to_remove} registros serão removidos")
                    
                    # Confirmar remoção
                    confirm = input(f"\n{Fore.YELLOW}   ❓ Remover duplicatas da tabela '{table_name}'? (s/N): ").strip().lower()
                    
                    if confirm == 's':
                        # Remover duplicatas mantendo apenas o primeiro registro de cada grupo
                        cleanup_query = f"""
                            DELETE FROM {table_name} 
                            WHERE id NOT IN (
                                SELECT MIN(id) 
                                FROM {table_name} 
                                GROUP BY {columns_str}
                            )
                        """
                        
                        result = conn.execute(cleanup_query)
                        conn.commit()
                        
                        # Verificar resultado
                        new_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        removed = total_count - new_count
                        
                        print(f"{Fore.GREEN}   ✅ Duplicatas removidas: {removed}")
                        print(f"{Fore.GREEN}   📊 Registros restantes: {new_count}")
                        
                        total_duplicates_removed += removed
                    else:
                        print(f"{Fore.YELLOW}   ⏭️  Tabela '{table_name}' ignorada")
                        
                except Exception as e:
                    print(f"{Fore.RED}   ❌ Erro ao processar tabela '{table_name}': {str(e)}")
                    self.logger.error(f"Erro ao limpar duplicatas na tabela {table_name}: {str(e)}")
            
            # Resultado final
            print(f"\n{Fore.CYAN}{'═'*60}")
            print(f"{Back.GREEN}{Fore.BLACK} LIMPEZA CONCLUÍDA {Style.RESET_ALL}")
            print(f"{Fore.WHITE}📈 Total de duplicatas removidas: {total_duplicates_removed}")
            print(f"{Fore.WHITE}📊 Tabelas processadas: {len(tables)}")
            
            if total_duplicates_removed > 0:
                print(f"{Fore.GREEN}✅ Banco de dados otimizado com sucesso!")
            else:
                print(f"{Fore.YELLOW}ℹ️  Nenhuma duplicata encontrada no banco.")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro durante limpeza: {str(e)}")
            self.logger.error(f"Erro na limpeza de duplicatas: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def validate_integrity(self):
        """Validação de integridade dos dados"""
        print(f"\n{Back.MAGENTA}{Fore.WHITE} VALIDAÇÃO DE INTEGRIDADE DOS DADOS {Style.RESET_ALL}")
        print(f"{Fore.CYAN}┌{'─'*58}┐")
        print(f"{Fore.CYAN}│{'Verificando consistência e integridade do banco':^56}│")
        print(f"{Fore.CYAN}└{'─'*58}┘")
        
        try:
            conn = self.db_manager._get_connection()
            
            # Obter lista de tabelas
            tables = conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main'
            """).fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}⚠️  Nenhuma tabela encontrada no banco de dados.")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            print(f"\n{Fore.WHITE}📊 Tabelas a serem validadas: {len(tables)}")
            print(f"{Fore.CYAN}{'─'*60}")
            
            total_issues = 0
            
            for table_row in tables:
                table_name = table_row[0]
                print(f"\n{Fore.YELLOW}🔍 Validando tabela: {table_name}")
                
                table_issues = 0
                
                try:
                    # 1. Verificar registros órfãos/nulos em campos obrigatórios
                    columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                    
                    for col in columns:
                        col_name, col_type, null_allowed = col[0], col[1], col[2]
                        
                        if null_allowed == 'NO':  # Campo obrigatório
                            null_count = conn.execute(f"""
                                SELECT COUNT(*) FROM {table_name} 
                                WHERE {col_name} IS NULL OR {col_name} = ''
                            """).fetchone()[0]
                            
                            if null_count > 0:
                                print(f"{Fore.RED}   ❌ {null_count} valores nulos/vazios em '{col_name}' (campo obrigatório)")
                                table_issues += null_count
                    
                    # 2. Verificar dados inconsistentes específicos por tabela
                    if table_name == 'categories':
                        # Verificar URLs inválidas
                        invalid_urls = conn.execute("""
                            SELECT COUNT(*) FROM categories 
                            WHERE links NOT LIKE 'http%' AND links != ''
                        """).fetchone()[0]
                        
                        if invalid_urls > 0:
                            print(f"{Fore.RED}   ❌ {invalid_urls} URLs inválidas na coluna 'links'")
                            table_issues += invalid_urls
                        
                        # Verificar nomes de categorias muito curtos
                        short_names = conn.execute("""
                            SELECT COUNT(*) FROM categories 
                            WHERE LENGTH(TRIM(categorias)) < 2
                        """).fetchone()[0]
                        
                        if short_names > 0:
                            print(f"{Fore.RED}   ❌ {short_names} nomes de categorias muito curtos")
                            table_issues += short_names
                    
                    elif table_name == 'restaurants':
                        # Verificar notas inválidas (se coluna existir)
                        try:
                            invalid_ratings = conn.execute("""
                                SELECT COUNT(*) FROM restaurants 
                                WHERE rating < 0 OR rating > 5
                            """).fetchone()[0]
                            
                            if invalid_ratings > 0:
                                print(f"{Fore.RED}   ❌ {invalid_ratings} avaliações inválidas (fora do range 0-5)")
                                table_issues += invalid_ratings
                        except:
                            pass  # Coluna pode não existir
                    
                    # 3. Verificar duplicatas (informativo)
                    if table_name in ['categories', 'restaurants', 'products']:
                        # Contar possíveis duplicatas por nome
                        name_columns = {
                            'categories': 'categorias',
                            'restaurants': 'name',
                            'products': 'name'
                        }
                        
                        if name_columns.get(table_name):
                            try:
                                duplicates = conn.execute(f"""
                                    SELECT COUNT(*) FROM (
                                        SELECT {name_columns[table_name]} 
                                        FROM {table_name} 
                                        GROUP BY {name_columns[table_name]} 
                                        HAVING COUNT(*) > 1
                                    )
                                """).fetchone()[0]
                                
                                if duplicates > 0:
                                    print(f"{Fore.YELLOW}   ⚠️  {duplicates} possíveis duplicatas detectadas")
                            except:
                                pass
                    
                    # 4. Verificar timestamps inválidos
                    try:
                        future_dates = conn.execute(f"""
                            SELECT COUNT(*) FROM {table_name} 
                            WHERE created_at > CURRENT_TIMESTAMP
                        """).fetchone()[0]
                        
                        if future_dates > 0:
                            print(f"{Fore.RED}   ❌ {future_dates} registros com datas futuras")
                            table_issues += future_dates
                    except:
                        pass  # Coluna created_at pode não existir
                    
                    # Resultado da tabela
                    if table_issues == 0:
                        print(f"{Fore.GREEN}   ✅ Tabela íntegra - nenhum problema encontrado")
                    else:
                        print(f"{Fore.RED}   🚨 {table_issues} problemas de integridade encontrados")
                        total_issues += table_issues
                    
                except Exception as e:
                    print(f"{Fore.RED}   ❌ Erro ao validar tabela '{table_name}': {str(e)}")
                    self.logger.error(f"Erro ao validar integridade da tabela {table_name}: {str(e)}")
            
            # Resultado final
            print(f"\n{Fore.CYAN}{'═'*60}")
            print(f"{Back.MAGENTA}{Fore.WHITE} VALIDAÇÃO CONCLUÍDA {Style.RESET_ALL}")
            print(f"{Fore.WHITE}📊 Tabelas validadas: {len(tables)}")
            print(f"{Fore.WHITE}🔍 Total de problemas encontrados: {total_issues}")
            
            if total_issues == 0:
                print(f"{Fore.GREEN}✅ Banco de dados íntegro - nenhum problema detectado!")
            else:
                print(f"{Fore.YELLOW}⚠️  {total_issues} problemas de integridade detectados.")
                print(f"{Fore.WHITE}💡 Recomenda-se revisar e corrigir os problemas encontrados.")
            
            # Estatísticas adicionais
            total_records = 0
            for table_row in tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_row[0]}").fetchone()[0]
                    total_records += count
                except:
                    pass
            
            print(f"{Fore.CYAN}📈 Total de registros no banco: {total_records:,}")
            
            # Tamanho do banco
            if os.path.exists(self.db_manager.db_path):
                size = os.path.getsize(self.db_manager.db_path)
                if size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                print(f"{Fore.CYAN}💾 Tamanho do arquivo: {size_str}")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro durante validação: {str(e)}")
            self.logger.error(f"Erro na validação de integridade: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")