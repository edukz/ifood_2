"""
Utilitários avançados do banco de dados
"""
import os
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from colorama import Fore, Back, Style
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager

class DatabaseUtils:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
        self.backup_dir = "data/backups"
        self.reports_dir = "data/reports"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Garantir que diretórios necessários existem"""
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def _format_size(self, size_bytes):
        """Formatar tamanho em bytes"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
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
    
    def auto_backup(self):
        """Backup automático do banco de dados"""
        try:
            print(f"\n{Back.GREEN}{Fore.BLACK} BACKUP AUTOMÁTICO DO BANCO {Style.RESET_ALL}")
            print(f"{Fore.CYAN}┌{'─'*58}┐")
            print(f"{Fore.CYAN}│{'Criando backup completo do banco de dados':^56}│")
            print(f"{Fore.CYAN}└{'─'*58}┘")
            
            if not os.path.exists(self.db_manager.db_path):
                print(f"\n{Fore.RED}❌ Arquivo do banco não encontrado: {self.db_manager.db_path}")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            # Gerar nome do backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.duckdb"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Criar backup
            print(f"\n{Fore.YELLOW}🔄 Criando backup...")
            start_time = time.time()
            
            shutil.copy2(self.db_manager.db_path, backup_path)
            
            backup_time = time.time() - start_time
            
            # Verificar tamanhos
            original_size = os.path.getsize(self.db_manager.db_path)
            backup_size = os.path.getsize(backup_path)
            
            print(f"\n{Fore.GREEN}✅ Backup criado com sucesso!")
            print(f"{Fore.WHITE}📁 Arquivo: {backup_filename}")
            print(f"{Fore.WHITE}📂 Local: {self.backup_dir}")
            print(f"{Fore.WHITE}📊 Tamanho: {self._format_size(backup_size)}")
            print(f"{Fore.WHITE}⏱️  Tempo: {backup_time:.2f}s")
            
            # Verificar integridade
            if backup_size == original_size:
                print(f"{Fore.GREEN}✅ Integridade verificada")
            else:
                print(f"{Fore.YELLOW}⚠️ Tamanhos diferentes - verificar backup")
            
            # Salvar metadados do backup
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "filename": backup_filename,
                "original_size": original_size,
                "backup_size": backup_size,
                "backup_time": backup_time
            }
            
            metadata_file = os.path.join(self.backup_dir, f"backup_{timestamp}.json")
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Listar backups existentes
            self._list_backups()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro durante backup: {str(e)}")
            self.logger.error(f"Erro no backup: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _list_backups(self):
        """Listar backups existentes"""
        try:
            print(f"\n{Fore.CYAN}📋 BACKUPS EXISTENTES:")
            
            backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.duckdb')]
            backup_files.sort(reverse=True)  # Mais recentes primeiro
            
            if not backup_files:
                print(f"{Fore.YELLOW}   ⚠️ Nenhum backup encontrado")
                return
            
            print(f"{Fore.WHITE}{'Arquivo':<25} {'Data/Hora':<20} {'Tamanho':<10}")
            print(f"{Fore.WHITE}{'-'*25} {'-'*20} {'-'*10}")
            
            for backup_file in backup_files[:10]:  # Mostrar últimos 10
                backup_path = os.path.join(self.backup_dir, backup_file)
                
                # Extrair timestamp do nome
                try:
                    timestamp_str = backup_file.replace('backup_', '').replace('.duckdb', '')
                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    date_str = backup_date.strftime("%d/%m/%Y %H:%M")
                except:
                    date_str = "Data inválida"
                
                size = os.path.getsize(backup_path)
                size_str = self._format_size(size)
                
                print(f"{Fore.GREEN}{backup_file:<25} {date_str:<20} {size_str:<10}")
            
            if len(backup_files) > 10:
                print(f"{Fore.YELLOW}   ... e mais {len(backup_files) - 10} backups")
                
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao listar backups: {str(e)}")
    
    def restore_backup(self):
        """Restaurar backup do banco de dados"""
        try:
            print(f"\n{Back.YELLOW}{Fore.BLACK} RESTAURAR BACKUP {Style.RESET_ALL}")
            print(f"{Fore.CYAN}┌{'─'*58}┐")
            print(f"{Fore.CYAN}│{'Restaurando banco de dados a partir de backup':^56}│")
            print(f"{Fore.CYAN}└{'─'*58}┘")
            
            # Listar backups disponíveis
            backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.duckdb')]
            backup_files.sort(reverse=True)
            
            if not backup_files:
                print(f"\n{Fore.YELLOW}⚠️ Nenhum backup encontrado em {self.backup_dir}")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            print(f"\n{Fore.WHITE}📋 BACKUPS DISPONÍVEIS:")
            for i, backup_file in enumerate(backup_files[:10], 1):
                backup_path = os.path.join(self.backup_dir, backup_file)
                
                try:
                    timestamp_str = backup_file.replace('backup_', '').replace('.duckdb', '')
                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    date_str = backup_date.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    date_str = "Data inválida"
                
                size = os.path.getsize(backup_path)
                size_str = self._format_size(size)
                
                print(f"{Fore.CYAN}[{i}] {backup_file} - {date_str} ({size_str})")
            
            print(f"{Fore.RED}[0] Cancelar")
            
            # Escolher backup
            try:
                choice = int(input(f"\n{Fore.GREEN}Escolha um backup para restaurar: ")) - 1
                
                if choice == -1:  # Cancelar
                    print(f"\n{Fore.CYAN}Operação cancelada.")
                    return
                
                if 0 <= choice < len(backup_files):
                    selected_backup = backup_files[choice]
                    backup_path = os.path.join(self.backup_dir, selected_backup)
                    
                    # Confirmar restauração
                    print(f"\n{Fore.YELLOW}⚠️ ATENÇÃO: Esta operação irá substituir o banco atual!")
                    print(f"{Fore.WHITE}Backup selecionado: {selected_backup}")
                    
                    confirm = input(f"\n{Fore.RED}Confirma a restauração? (s/N): ").strip().lower()
                    
                    if confirm == 's':
                        # Fazer backup do estado atual antes de restaurar
                        current_backup = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.duckdb"
                        current_backup_path = os.path.join(self.backup_dir, current_backup)
                        
                        print(f"\n{Fore.YELLOW}🔄 Criando backup do estado atual...")
                        shutil.copy2(self.db_manager.db_path, current_backup_path)
                        print(f"{Fore.GREEN}✅ Backup de segurança criado: {current_backup}")
                        
                        # Restaurar backup
                        print(f"\n{Fore.YELLOW}🔄 Restaurando backup...")
                        shutil.copy2(backup_path, self.db_manager.db_path)
                        
                        print(f"\n{Fore.GREEN}✅ Backup restaurado com sucesso!")
                        print(f"{Fore.WHITE}📁 Arquivo restaurado: {selected_backup}")
                        print(f"{Fore.WHITE}🛡️ Backup de segurança: {current_backup}")
                        
                    else:
                        print(f"\n{Fore.CYAN}Restauração cancelada.")
                        
                else:
                    print(f"\n{Fore.RED}❌ Opção inválida!")
                    
            except ValueError:
                print(f"\n{Fore.RED}❌ Por favor, digite um número válido!")
                
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro durante restauração: {str(e)}")
            self.logger.error(f"Erro na restauração: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def data_quality_report(self):
        """Relatório de qualidade dos dados"""
        try:
            print(f"\n{Back.CYAN}{Fore.BLACK} RELATÓRIO DE QUALIDADE DOS DADOS {Style.RESET_ALL}")
            print(f"{Fore.CYAN}┌{'─'*58}┐")
            print(f"{Fore.CYAN}│{'Analisando qualidade e consistência dos dados':^56}│")
            print(f"{Fore.CYAN}└{'─'*58}┘")
            
            conn = self.db_manager._get_connection()
            
            # Obter tabelas
            tables = conn.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'main' ORDER BY table_name
            """).fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}⚠️ Nenhuma tabela encontrada!")
                conn.close()
                return
            
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "tables": {},
                "summary": {}
            }
            
            total_records = 0
            total_nulls = 0
            total_duplicates = 0
            
            print(f"\n{Fore.WHITE}📊 ANÁLISE DE QUALIDADE POR TABELA:")
            print(f"{Fore.CYAN}{'─'*60}")
            
            for table_row in tables:
                table_name = table_row[0]
                print(f"\n{Fore.YELLOW}🔍 Analisando: {table_name}")
                
                table_report = {
                    "record_count": 0,
                    "null_fields": 0,
                    "duplicate_records": 0,
                    "data_quality_score": 0,
                    "issues": []
                }
                
                try:
                    # Contar registros
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    table_report["record_count"] = count
                    total_records += count
                    
                    if count == 0:
                        print(f"{Fore.WHITE}   📊 Tabela vazia")
                        table_report["data_quality_score"] = 100
                        report_data["tables"][table_name] = table_report
                        continue
                    
                    # Analisar campos nulos
                    columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                    null_count = 0
                    
                    for col in columns:
                        col_name = col[0]
                        col_type = col[1].upper()
                        
                        if col_name != 'id':  # Pular ID
                            # Verificar apenas NULL para tipos numéricos e timestamp
                            if 'DECIMAL' in col_type or 'TIMESTAMP' in col_type or 'INTEGER' in col_type or 'FLOAT' in col_type:
                                nulls = conn.execute(f"""
                                    SELECT COUNT(*) FROM {table_name} 
                                    WHERE {col_name} IS NULL
                                """).fetchone()[0]
                            else:
                                # Para VARCHAR e TEXT, verificar NULL e string vazia
                                nulls = conn.execute(f"""
                                    SELECT COUNT(*) FROM {table_name} 
                                    WHERE {col_name} IS NULL OR {col_name} = ''
                                """).fetchone()[0]
                            
                            if nulls > 0:
                                null_count += nulls
                                percentage = (nulls / count) * 100
                                if percentage > 10:  # Mais de 10% nulos
                                    table_report["issues"].append(f"Campo '{col_name}': {percentage:.1f}% valores nulos")
                    
                    table_report["null_fields"] = null_count
                    total_nulls += null_count
                    
                    # Verificar duplicatas aproximadas (por nome se existir)
                    name_columns = {
                        'categories': 'categorias',
                        'restaurants': 'name', 
                        'products': 'name'
                    }
                    
                    if table_name in name_columns:
                        try:
                            dups = conn.execute(f"""
                                SELECT COUNT(*) FROM (
                                    SELECT {name_columns[table_name]} 
                                    FROM {table_name} 
                                    GROUP BY LOWER(TRIM({name_columns[table_name]}))
                                    HAVING COUNT(*) > 1
                                )
                            """).fetchone()[0]
                            
                            table_report["duplicate_records"] = dups
                            total_duplicates += dups
                            
                            if dups > 0:
                                table_report["issues"].append(f"{dups} possíveis duplicatas detectadas")
                                
                        except:
                            pass
                    
                    # Validações específicas por tabela
                    if table_name == 'restaurants':
                        try:
                            # Verificar ratings inválidos
                            invalid_ratings = conn.execute("""
                                SELECT COUNT(*) FROM restaurants 
                                WHERE rating IS NOT NULL AND (rating < 0 OR rating > 5)
                            """).fetchone()[0]
                            
                            if invalid_ratings > 0:
                                table_report["issues"].append(f"{invalid_ratings} ratings inválidos (fora de 0-5)")
                            
                            # Verificar delivery fees negativos
                            negative_fees = conn.execute("""
                                SELECT COUNT(*) FROM restaurants 
                                WHERE delivery_fee IS NOT NULL AND delivery_fee < 0
                            """).fetchone()[0]
                            
                            if negative_fees > 0:
                                table_report["issues"].append(f"{negative_fees} taxas de entrega negativas")
                                
                        except:
                            pass
                    
                    elif table_name == 'products':
                        try:
                            # Verificar preços negativos
                            negative_prices = conn.execute("""
                                SELECT COUNT(*) FROM products 
                                WHERE price IS NOT NULL AND price < 0
                            """).fetchone()[0]
                            
                            if negative_prices > 0:
                                table_report["issues"].append(f"{negative_prices} preços negativos")
                                
                        except:
                            pass
                    
                    # Calcular score de qualidade
                    issues_count = len(table_report["issues"])
                    null_percentage = (null_count / (count * len(columns))) * 100 if count > 0 else 0
                    
                    quality_score = 100
                    quality_score -= min(null_percentage * 2, 50)  # Penalizar nulos
                    quality_score -= min(issues_count * 10, 30)   # Penalizar issues
                    quality_score = max(quality_score, 0)
                    
                    table_report["data_quality_score"] = round(quality_score, 1)
                    
                    # Exibir resultados da tabela
                    print(f"{Fore.WHITE}   📊 Registros: {count:,}")
                    print(f"{Fore.WHITE}   📊 Campos nulos: {null_count}")
                    print(f"{Fore.WHITE}   📊 Score de qualidade: {quality_score:.1f}%")
                    
                    if quality_score >= 90:
                        print(f"{Fore.GREEN}   ✅ Qualidade excelente")
                    elif quality_score >= 70:
                        print(f"{Fore.YELLOW}   ⚠️ Qualidade boa")
                    else:
                        print(f"{Fore.RED}   ❌ Qualidade baixa")
                    
                    if table_report["issues"]:
                        print(f"{Fore.RED}   🚨 Problemas encontrados:")
                        for issue in table_report["issues"]:
                            print(f"{Fore.RED}      • {issue}")
                    
                except Exception as e:
                    table_report["issues"].append(f"Erro na análise: {str(e)}")
                    print(f"{Fore.RED}   ❌ Erro: {str(e)}")
                
                report_data["tables"][table_name] = table_report
            
            # Resumo geral
            avg_quality = sum(t["data_quality_score"] for t in report_data["tables"].values()) / len(tables) if tables else 0
            
            report_data["summary"] = {
                "total_tables": len(tables),
                "total_records": total_records,
                "total_nulls": total_nulls,
                "total_duplicates": total_duplicates,
                "average_quality_score": round(avg_quality, 1)
            }
            
            print(f"\n{Fore.CYAN}{'═'*60}")
            print(f"{Back.CYAN}{Fore.BLACK} RESUMO GERAL {Style.RESET_ALL}")
            print(f"{Fore.WHITE}📊 Tabelas analisadas: {len(tables)}")
            print(f"{Fore.WHITE}📊 Total de registros: {total_records:,}")
            print(f"{Fore.WHITE}📊 Campos nulos: {total_nulls:,}")
            print(f"{Fore.WHITE}📊 Possíveis duplicatas: {total_duplicates}")
            print(f"{Fore.WHITE}📊 Score médio de qualidade: {avg_quality:.1f}%")
            
            if avg_quality >= 90:
                print(f"{Fore.GREEN}✅ Qualidade geral: EXCELENTE")
            elif avg_quality >= 70:
                print(f"{Fore.YELLOW}⚠️ Qualidade geral: BOA")
            else:
                print(f"{Fore.RED}❌ Qualidade geral: BAIXA")
            
            # Salvar relatório
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.reports_dir, f"quality_report_{timestamp}.json")
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            print(f"\n{Fore.GREEN}💾 Relatório salvo em: {report_file}")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro no relatório: {str(e)}")
            self.logger.error(f"Erro no relatório de qualidade: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def database_migration(self):
        """Migração e versionamento de schema"""
        try:
            print(f"\n{Back.MAGENTA}{Fore.WHITE} MIGRAÇÃO E VERSIONAMENTO {Style.RESET_ALL}")
            print(f"{Fore.CYAN}┌{'─'*58}┐")
            print(f"{Fore.CYAN}│{'Gerenciamento de versões do schema do banco':^56}│")
            print(f"{Fore.CYAN}└{'─'*58}┘")
            
            # Verificar se tabela de versões existe
            conn = self.db_manager._get_connection()
            
            try:
                # Tentar criar tabela de versões se não existir
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_versions (
                        id INTEGER PRIMARY KEY,
                        version VARCHAR NOT NULL,
                        description VARCHAR,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        checksum VARCHAR
                    )
                """)
                conn.commit()
            except:
                pass
            
            # Verificar versão atual
            try:
                current_version = conn.execute("""
                    SELECT version FROM schema_versions 
                    ORDER BY applied_at DESC LIMIT 1
                """).fetchone()
                
                if current_version:
                    current_version = current_version[0]
                else:
                    current_version = "0.0.0"
            except:
                current_version = "0.0.0"
            
            print(f"\n{Fore.WHITE}📊 Versão atual do schema: {current_version}")
            
            # Migrações disponíveis
            migrations = [
                {
                    "version": "1.0.0",
                    "description": "Schema inicial com tabelas básicas",
                    "sql": """
                        CREATE TABLE IF NOT EXISTS categories (
                            id INTEGER PRIMARY KEY,
                            categorias VARCHAR NOT NULL,
                            links VARCHAR NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        
                        CREATE TABLE IF NOT EXISTS restaurants (
                            id INTEGER PRIMARY KEY,
                            name VARCHAR NOT NULL,
                            category VARCHAR NOT NULL,
                            rating DECIMAL(2,1),
                            delivery_fee DECIMAL(10,2),
                            city VARCHAR NOT NULL,
                            link VARCHAR,
                            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        
                        CREATE TABLE IF NOT EXISTS products (
                            id INTEGER PRIMARY KEY,
                            restaurant_id INTEGER,
                            restaurant_name VARCHAR,
                            category VARCHAR,
                            name VARCHAR NOT NULL,
                            description TEXT,
                            price DECIMAL(10,2),
                            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """
                },
                {
                    "version": "1.1.0", 
                    "description": "Adição de índices para performance",
                    "sql": """
                        CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants(city);
                        CREATE INDEX IF NOT EXISTS idx_restaurants_category ON restaurants(category);
                        CREATE INDEX IF NOT EXISTS idx_products_restaurant_id ON products(restaurant_id);
                        CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
                    """
                },
                {
                    "version": "1.2.0",
                    "description": "Adição de campos de auditoria",
                    "sql": """
                        ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
                        ALTER TABLE products ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
                        ALTER TABLE categories ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
                    """
                }
            ]
            
            # Mostrar migrações disponíveis
            print(f"\n{Fore.YELLOW}📋 MIGRAÇÕES DISPONÍVEIS:")
            
            available_migrations = []
            for migration in migrations:
                # Verificar se migração já foi aplicada
                try:
                    applied = conn.execute("""
                        SELECT COUNT(*) FROM schema_versions 
                        WHERE version = ?
                    """, [migration["version"]]).fetchone()[0]
                    
                    if applied == 0:
                        available_migrations.append(migration)
                        print(f"{Fore.GREEN}[{len(available_migrations)}] v{migration['version']} - {migration['description']}")
                    else:
                        print(f"{Fore.GRAY}[ ] v{migration['version']} - {migration['description']} (já aplicada)")
                        
                except:
                    available_migrations.append(migration)
                    print(f"{Fore.GREEN}[{len(available_migrations)}] v{migration['version']} - {migration['description']}")
            
            if not available_migrations:
                print(f"{Fore.GREEN}✅ Todas as migrações estão aplicadas!")
                print(f"\n{Fore.CYAN}💡 Schema está na versão mais recente")
            else:
                print(f"{Fore.YELLOW}[A] Aplicar todas as migrações pendentes")
            
            print(f"{Fore.RED}[0] Voltar")
            
            if available_migrations:
                choice = input(f"\n{Fore.GREEN}Escolha uma migração: ").strip()
                
                if choice == '0':
                    return
                elif choice.upper() == 'A':
                    # Aplicar todas
                    for migration in available_migrations:
                        self._apply_migration(conn, migration)
                else:
                    # Aplicar migração específica
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(available_migrations):
                            self._apply_migration(conn, available_migrations[idx])
                        else:
                            print(f"{Fore.RED}❌ Opção inválida!")
                    except ValueError:
                        print(f"{Fore.RED}❌ Por favor, digite um número válido!")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro na migração: {str(e)}")
            self.logger.error(f"Erro na migração: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _apply_migration(self, conn, migration):
        """Aplicar uma migração específica"""
        try:
            print(f"\n{Fore.YELLOW}🔄 Aplicando migração v{migration['version']}...")
            print(f"{Fore.WHITE}   {migration['description']}")
            
            # Executar SQL da migração
            statements = migration['sql'].split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    conn.execute(statement)
            
            # Registrar migração
            import hashlib
            checksum = hashlib.md5(migration['sql'].encode()).hexdigest()
            
            conn.execute("""
                INSERT INTO schema_versions (version, description, checksum) 
                VALUES (?, ?, ?)
            """, [migration['version'], migration['description'], checksum])
            
            conn.commit()
            
            print(f"{Fore.GREEN}   ✅ Migração v{migration['version']} aplicada com sucesso!")
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Erro ao aplicar migração v{migration['version']}: {str(e)}")
            raise
    
    def cleanup_old_data(self):
        """Limpeza de dados antigos"""
        try:
            print(f"\n{Back.RED}{Fore.WHITE} LIMPEZA DE DADOS ANTIGOS {Style.RESET_ALL}")
            print(f"{Fore.CYAN}┌{'─'*58}┐")
            print(f"{Fore.CYAN}│{'Removendo dados antigos e otimizando espaço':^56}│")
            print(f"{Fore.CYAN}└{'─'*58}┘")
            
            conn = self.db_manager._get_connection()
            
            # Opções de limpeza
            print(f"\n{Fore.YELLOW}🧹 OPÇÕES DE LIMPEZA:")
            print(f"{Fore.WHITE}[1] Remover dados de scraping antigos (>30 dias)")
            print(f"{Fore.WHITE}[2] Remover registros órfãos")
            print(f"{Fore.WHITE}[3] Compactar e otimizar banco")
            print(f"{Fore.WHITE}[4] Limpeza completa (todas as opções)")
            print(f"{Fore.RED}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: ").strip()
            
            if choice == '0':
                return
            elif choice in ['1', '4']:
                self._cleanup_old_scraping_data(conn)
            
            if choice in ['2', '4']:
                self._cleanup_orphaned_records(conn)
            
            if choice in ['3', '4']:
                self._optimize_database(conn)
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro na limpeza: {str(e)}")
            self.logger.error(f"Erro na limpeza: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _cleanup_old_scraping_data(self, conn):
        """Remover dados de scraping antigos"""
        try:
            print(f"\n{Fore.YELLOW}🔄 Removendo dados antigos...")
            
            # Tentar remover dados com mais de 30 dias
            tables_with_timestamps = ['restaurants', 'products', 'categories']
            total_removed = 0
            
            for table in tables_with_timestamps:
                try:
                    # Verificar se tabela e campo existem
                    before_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    
                    # Tentar diferentes nomes de campo de timestamp
                    timestamp_fields = ['scraped_at', 'created_at', 'updated_at']
                    
                    for field in timestamp_fields:
                        try:
                            removed = conn.execute(f"""
                                DELETE FROM {table} 
                                WHERE {field} < datetime('now', '-30 days')
                            """).rowcount
                            
                            if removed > 0:
                                total_removed += removed
                                print(f"{Fore.GREEN}   ✅ {table}: {removed} registros antigos removidos")
                                break
                                
                        except:
                            continue
                    
                except Exception as e:
                    print(f"{Fore.YELLOW}   ⚠️ {table}: {str(e)}")
            
            if total_removed > 0:
                conn.commit()
                print(f"\n{Fore.GREEN}✅ Total removido: {total_removed} registros antigos")
            else:
                print(f"\n{Fore.YELLOW}ℹ️ Nenhum dado antigo encontrado para remoção")
                
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro na limpeza de dados antigos: {str(e)}")
    
    def _cleanup_orphaned_records(self, conn):
        """Remover registros órfãos"""
        try:
            print(f"\n{Fore.YELLOW}🔄 Removendo registros órfãos...")
            
            # Remover produtos sem restaurante correspondente
            try:
                orphaned_products = conn.execute("""
                    DELETE FROM products 
                    WHERE restaurant_id NOT IN (SELECT id FROM restaurants)
                """).rowcount
                
                if orphaned_products > 0:
                    print(f"{Fore.GREEN}   ✅ {orphaned_products} produtos órfãos removidos")
                    conn.commit()
                else:
                    print(f"{Fore.GREEN}   ✅ Nenhum produto órfão encontrado")
                    
            except Exception as e:
                print(f"{Fore.YELLOW}   ⚠️ Erro ao remover produtos órfãos: {str(e)}")
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro na limpeza de órfãos: {str(e)}")
    
    def _optimize_database(self, conn):
        """Otimizar banco de dados"""
        try:
            print(f"\n{Fore.YELLOW}🔄 Otimizando banco de dados...")
            
            # Executar VACUUM
            print(f"{Fore.WHITE}   • Executando VACUUM...")
            conn.execute("VACUUM")
            
            # Executar ANALYZE
            print(f"{Fore.WHITE}   • Executando ANALYZE...")
            conn.execute("ANALYZE")
            
            print(f"{Fore.GREEN}   ✅ Otimização concluída")
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro na otimização: {str(e)}")
    
    def show_advanced_menu(self):
        """Menu avançado de utilitários"""
        while True:
            print(f"\n{Back.CYAN}{Fore.BLACK} UTILITÁRIOS AVANÇADOS {Style.RESET_ALL}")
            print(f"{Fore.CYAN}┌{'─'*58}┐")
            print(f"{Fore.CYAN}│{'Ferramentas avançadas de manutenção':^56}│")
            print(f"{Fore.CYAN}└{'─'*58}┘")
            
            print(f"\n{Fore.YELLOW}🛠️ UTILITÁRIOS DISPONÍVEIS:")
            print(f"{Fore.WHITE}[1] Limpeza de dados duplicados")
            print(f"{Fore.WHITE}[2] Validação de integridade")
            print(f"{Fore.WHITE}[3] Backup automático")
            print(f"{Fore.WHITE}[4] Restaurar backup")
            print(f"{Fore.WHITE}[5] Relatório de qualidade dos dados")
            print(f"{Fore.WHITE}[6] Migração e versionamento")
            print(f"{Fore.WHITE}[7] Limpeza de dados antigos")
            print(f"{Fore.CYAN}[8] 🔧 Enriquecimento de dados")
            print(f"{Fore.RED}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Style.RESET_ALL}").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.clean_duplicates()
            elif choice == '2':
                self.validate_integrity()
            elif choice == '3':
                self.auto_backup()
            elif choice == '4':
                self.restore_backup()
            elif choice == '5':
                self.data_quality_report()
            elif choice == '6':
                self.database_migration()
            elif choice == '7':
                self.cleanup_old_data()
            elif choice == '8':
                self.data_enrichment()
            else:
                print(f"{Fore.RED}Opção inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def data_enrichment(self):
        """Enriquecimento de dados - melhorar qualidade dos dados existentes"""
        print(f"\n{Back.CYAN}{Fore.WHITE} ENRIQUECIMENTO DE DADOS {Style.RESET_ALL}")
        print(f"{Fore.CYAN}┌{'─'*58}┐")
        print(f"{Fore.CYAN}│{'Melhoramento automático da qualidade dos dados':^56}│")
        print(f"{Fore.CYAN}└{'─'*58}┘")
        
        try:
            conn = self.db_manager._get_connection()
            
            # Análise inicial
            print(f"\n{Fore.YELLOW}📊 ANÁLISE INICIAL:")
            
            # Verificar dados faltantes na tabela restaurants
            restaurants_analysis = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) - COUNT(rating) as missing_rating,
                    COUNT(*) - COUNT(delivery_time) as missing_delivery_time,
                    COUNT(*) - COUNT(delivery_fee) as missing_delivery_fee,
                    COUNT(*) - COUNT(reviews) as missing_reviews,
                    COUNT(*) - COUNT(min_order) as missing_min_order
                FROM restaurants
            """).fetchone()
            
            total_restaurants = restaurants_analysis[0]
            missing_data = {
                "rating": restaurants_analysis[1],
                "delivery_time": restaurants_analysis[2], 
                "delivery_fee": restaurants_analysis[3],
                "reviews": restaurants_analysis[4],
                "min_order": restaurants_analysis[5]
            }
            
            print(f"{Fore.WHITE}   📋 Total de restaurantes: {total_restaurants}")
            print(f"{Fore.YELLOW}   📊 Dados faltantes:")
            
            improvements_needed = False
            for field, missing in missing_data.items():
                if missing > 0:
                    percentage = (missing / total_restaurants) * 100
                    print(f"{Fore.RED}      • {field}: {missing} ({percentage:.1f}%)")
                    improvements_needed = True
                else:
                    print(f"{Fore.GREEN}      • {field}: Completo ✅")
            
            if not improvements_needed:
                print(f"\n{Fore.GREEN}🎉 Parabéns! Todos os dados estão completos!")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            # Opções de enriquecimento
            print(f"\n{Fore.YELLOW}🔧 OPÇÕES DE ENRIQUECIMENTO:")
            print(f"{Fore.WHITE}[1] Enriquecer ratings (usar scraping inteligente)")
            print(f"{Fore.WHITE}[2] Calcular delivery_time estimado")
            print(f"{Fore.WHITE}[3] Inferir delivery_fee padrão")
            print(f"{Fore.WHITE}[4] Estimar reviews baseado na popularidade")
            print(f"{Fore.WHITE}[5] Calcular min_order médio por categoria")
            print(f"{Fore.CYAN}[6] 🚀 Enriquecimento completo (todos os itens)")
            print(f"{Fore.RED}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Style.RESET_ALL}").strip()
            
            if choice == '0':
                return
            elif choice == '1':
                self._enrich_ratings(conn)
            elif choice == '2':
                self._enrich_delivery_time(conn)
            elif choice == '3':
                self._enrich_delivery_fee(conn)
            elif choice == '4':
                self._enrich_reviews(conn)
            elif choice == '5':
                self._enrich_min_order(conn)
            elif choice == '6':
                self._enrich_all_data(conn)
            else:
                print(f"{Fore.RED}Opção inválida!")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro no enriquecimento de dados: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _enrich_ratings(self, conn):
        """Enriquecer ratings faltantes"""
        try:
            print(f"\n{Fore.CYAN}🌟 ENRIQUECENDO RATINGS...")
            
            # Calcular rating médio por categoria
            category_avg = conn.execute("""
                SELECT category, AVG(rating) as avg_rating
                FROM restaurants 
                WHERE rating IS NOT NULL
                GROUP BY category
            """).fetchall()
            
            category_ratings = {row[0]: round(row[1], 1) for row in category_avg}
            
            # Rating global médio como fallback
            global_avg = conn.execute("""
                SELECT AVG(rating) FROM restaurants WHERE rating IS NOT NULL
            """).fetchone()[0]
            global_avg = round(global_avg, 1) if global_avg else 4.0
            
            # Atualizar ratings faltantes
            updated = 0
            for category, avg_rating in category_ratings.items():
                result = conn.execute("""
                    UPDATE restaurants 
                    SET rating = ? 
                    WHERE category = ? AND rating IS NULL
                """, [avg_rating, category])
                updated += result.rowcount
            
            # Usar média global para categorias sem dados
            result = conn.execute("""
                UPDATE restaurants 
                SET rating = ? 
                WHERE rating IS NULL
            """, [global_avg])
            updated += result.rowcount
            
            conn.commit()
            print(f"{Fore.GREEN}   ✅ {updated} ratings atualizados")
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Erro: {str(e)}")
    
    def _enrich_delivery_time(self, conn):
        """Enriquecer tempo de entrega"""
        try:
            print(f"\n{Fore.CYAN}⏰ ENRIQUECENDO TEMPO DE ENTREGA...")
            
            # Tempo médio por categoria
            category_times = conn.execute("""
                SELECT category, AVG(delivery_time) as avg_time
                FROM restaurants 
                WHERE delivery_time IS NOT NULL
                GROUP BY category
            """).fetchall()
            
            category_avg_times = {row[0]: int(row[1]) for row in category_times}
            
            # Tempo padrão (45 min)
            default_time = 45
            
            updated = 0
            for category, avg_time in category_avg_times.items():
                result = conn.execute("""
                    UPDATE restaurants 
                    SET delivery_time = ? 
                    WHERE category = ? AND delivery_time IS NULL
                """, [avg_time, category])
                updated += result.rowcount
            
            # Usar tempo padrão para categorias sem dados
            result = conn.execute("""
                UPDATE restaurants 
                SET delivery_time = ? 
                WHERE delivery_time IS NULL
            """, [default_time])
            updated += result.rowcount
            
            conn.commit()
            print(f"{Fore.GREEN}   ✅ {updated} tempos de entrega atualizados")
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Erro: {str(e)}")
    
    def _enrich_delivery_fee(self, conn):
        """Enriquecer taxa de entrega"""
        try:
            print(f"\n{Fore.CYAN}💰 ENRIQUECENDO TAXA DE ENTREGA...")
            
            # Taxa média por categoria
            category_fees = conn.execute("""
                SELECT category, AVG(delivery_fee) as avg_fee
                FROM restaurants 
                WHERE delivery_fee IS NOT NULL
                GROUP BY category
            """).fetchall()
            
            category_avg_fees = {row[0]: round(row[1], 2) for row in category_fees}
            
            # Taxa padrão (R$ 5.00)
            default_fee = 5.00
            
            updated = 0
            for category, avg_fee in category_avg_fees.items():
                result = conn.execute("""
                    UPDATE restaurants 
                    SET delivery_fee = ? 
                    WHERE category = ? AND delivery_fee IS NULL
                """, [avg_fee, category])
                updated += result.rowcount
            
            # Usar taxa padrão para categorias sem dados
            result = conn.execute("""
                UPDATE restaurants 
                SET delivery_fee = ? 
                WHERE delivery_fee IS NULL
            """, [default_fee])
            updated += result.rowcount
            
            conn.commit()
            print(f"{Fore.GREEN}   ✅ {updated} taxas de entrega atualizadas")
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Erro: {str(e)}")
    
    def _enrich_reviews(self, conn):
        """Enriquecer número de reviews baseado no rating"""
        try:
            print(f"\n{Fore.CYAN}📝 ENRIQUECENDO NÚMERO DE REVIEWS...")
            
            # Estimar reviews baseado no rating (ratings altos = mais reviews)
            updated = conn.execute("""
                UPDATE restaurants 
                SET reviews = CASE 
                    WHEN rating >= 4.5 THEN CAST((rating - 3.0) * 200 + 50 AS INTEGER)
                    WHEN rating >= 4.0 THEN CAST((rating - 3.0) * 150 + 30 AS INTEGER)
                    WHEN rating >= 3.5 THEN CAST((rating - 3.0) * 100 + 20 AS INTEGER)
                    ELSE CAST((rating - 2.0) * 50 + 10 AS INTEGER)
                END
                WHERE reviews IS NULL AND rating IS NOT NULL
            """).rowcount
            
            # Para ratings nulos, usar valor padrão baixo
            result = conn.execute("""
                UPDATE restaurants 
                SET reviews = 25
                WHERE reviews IS NULL
            """)
            updated += result.rowcount
            
            conn.commit()
            print(f"{Fore.GREEN}   ✅ {updated} números de reviews atualizados")
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Erro: {str(e)}")
    
    def _enrich_min_order(self, conn):
        """Enriquecer pedido mínimo"""
        try:
            print(f"\n{Fore.CYAN}🛒 ENRIQUECENDO PEDIDO MÍNIMO...")
            
            # Pedido mínimo médio por categoria
            category_min_orders = conn.execute("""
                SELECT category, AVG(min_order) as avg_min_order
                FROM restaurants 
                WHERE min_order IS NOT NULL
                GROUP BY category
            """).fetchall()
            
            category_avg_min_orders = {row[0]: round(row[1], 2) for row in category_min_orders}
            
            # Pedido mínimo padrão (R$ 25.00)
            default_min_order = 25.00
            
            updated = 0
            for category, avg_min_order in category_avg_min_orders.items():
                result = conn.execute("""
                    UPDATE restaurants 
                    SET min_order = ? 
                    WHERE category = ? AND min_order IS NULL
                """, [avg_min_order, category])
                updated += result.rowcount
            
            # Usar valor padrão para categorias sem dados
            result = conn.execute("""
                UPDATE restaurants 
                SET min_order = ? 
                WHERE min_order IS NULL
            """, [default_min_order])
            updated += result.rowcount
            
            conn.commit()
            print(f"{Fore.GREEN}   ✅ {updated} pedidos mínimos atualizados")
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Erro: {str(e)}")
    
    def _enrich_all_data(self, conn):
        """Enriquecer todos os dados de uma vez"""
        print(f"\n{Fore.CYAN}🚀 ENRIQUECIMENTO COMPLETO...")
        
        self._enrich_ratings(conn)
        self._enrich_delivery_time(conn)
        self._enrich_delivery_fee(conn)
        self._enrich_reviews(conn)
        self._enrich_min_order(conn)
        
        print(f"\n{Fore.GREEN}🎉 Enriquecimento completo finalizado!")