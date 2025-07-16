"""
Consultas e relatórios do banco
"""
import os
import json
import time
import csv
from datetime import datetime
from colorama import Fore, Style
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager

class DatabaseQueries:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
        self.history_file = "data/query_history.json"
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        """Garantir que o arquivo de histórico existe"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
    
    def _save_to_history(self, query, execution_time, result_count, status="success", error=None):
        """Salvar consulta no histórico"""
        try:
            # Carregar histórico existente
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            
            # Adicionar nova entrada
            entry = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "execution_time": execution_time,
                "result_count": result_count,
                "status": status,
                "error": error
            }
            
            history.append(entry)
            
            # Manter apenas as últimas 100 consultas
            if len(history) > 100:
                history = history[-100:]
            
            # Salvar histórico atualizado
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar no histórico: {str(e)}")
    
    def _format_query_result(self, results, columns):
        """Formatar resultado da consulta em tabela"""
        if not results:
            return "Nenhum resultado encontrado."
        
        # Calcular larguras das colunas
        col_widths = []
        for i, col_name in enumerate(columns):
            max_width = len(col_name)
            for row in results:
                val = str(row[i]) if row[i] is not None else "NULL"
                max_width = max(max_width, len(val))
            col_widths.append(min(max_width + 2, 25))  # Máximo 25 caracteres
        
        # Criar tabela formatada
        output = []
        
        # Linha separadora
        separator = "─" * (sum(col_widths) + len(columns) - 1)
        output.append(separator)
        
        # Cabeçalho
        header_parts = []
        for i, col_name in enumerate(columns):
            header_parts.append(f"{col_name:<{col_widths[i]}}")
        output.append(" ".join(header_parts))
        output.append(separator)
        
        # Dados
        for row in results:
            row_parts = []
            for i, val in enumerate(row):
                val_str = str(val) if val is not None else "NULL"
                if len(val_str) > col_widths[i] - 2:
                    val_str = val_str[:col_widths[i] - 5] + "..."
                row_parts.append(f"{val_str:<{col_widths[i]}}")
            output.append(" ".join(row_parts))
        
        output.append(separator)
        return "\n".join(output)
    
    def execute_custom(self):
        """Executar SQL personalizado"""
        try:
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║               EXECUTAR SQL PERSONALIZADO                 ║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
            
            print(f"\n{Fore.YELLOW}💡 DICAS:")
            print(f"{Fore.WHITE}   • Digite 'exit' para sair")
            print(f"{Fore.WHITE}   • Digite 'help' para ver comandos disponíveis")
            print(f"{Fore.WHITE}   • Digite 'tables' para ver tabelas disponíveis")
            print(f"{Fore.WHITE}   • Use ';' no final das consultas (opcional)")
            
            conn = self.db_manager._get_connection()
            
            while True:
                print(f"\n{Fore.CYAN}{'─'*60}")
                sql = input(f"{Fore.GREEN}SQL> {Style.RESET_ALL}").strip()
                
                if not sql:
                    continue
                
                if sql.lower() == 'exit':
                    break
                elif sql.lower() == 'help':
                    self._show_sql_help()
                    continue
                elif sql.lower() == 'tables':
                    self._show_available_tables(conn)
                    continue
                
                # Executar consulta
                start_time = time.time()
                try:
                    # Remover ';' final se existir
                    sql = sql.rstrip(';')
                    
                    result = conn.execute(sql).fetchall()
                    execution_time = time.time() - start_time
                    
                    if result:
                        # Obter nomes das colunas
                        columns = [desc[0] for desc in conn.description]
                        
                        print(f"\n{Fore.GREEN}✅ Consulta executada com sucesso!")
                        print(f"{Fore.CYAN}⏱️  Tempo de execução: {execution_time:.3f}s")
                        print(f"{Fore.CYAN}📊 Registros retornados: {len(result)}")
                        
                        # Mostrar resultados formatados
                        if len(result) <= 50:
                            print(f"\n{Fore.WHITE}{self._format_query_result(result, columns)}")
                        else:
                            print(f"\n{Fore.YELLOW}⚠️ Muitos resultados ({len(result)}). Mostrando primeiros 50:")
                            print(f"{Fore.WHITE}{self._format_query_result(result[:50], columns)}")
                            
                            export = input(f"\n{Fore.CYAN}Exportar resultados completos para CSV? (s/N): ").strip().lower()
                            if export == 's':
                                self._export_query_results(sql, result, columns)
                    else:
                        print(f"\n{Fore.GREEN}✅ Consulta executada com sucesso!")
                        print(f"{Fore.CYAN}⏱️  Tempo de execução: {execution_time:.3f}s")
                        print(f"{Fore.YELLOW}📊 Nenhum resultado retornado (comando DML ou DDL)")
                    
                    # Salvar no histórico
                    self._save_to_history(sql, execution_time, len(result) if result else 0)
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    error_msg = str(e)
                    
                    print(f"\n{Fore.RED}❌ Erro na consulta:")
                    print(f"{Fore.RED}   {error_msg}")
                    print(f"{Fore.CYAN}⏱️  Tempo até erro: {execution_time:.3f}s")
                    
                    # Salvar erro no histórico
                    self._save_to_history(sql, execution_time, 0, "error", error_msg)
            
            conn.close()
            print(f"\n{Fore.CYAN}👋 Saindo do modo SQL personalizado...")
            
        except Exception as e:
            self.logger.error(f"Erro no SQL personalizado: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_sql_help(self):
        """Mostrar ajuda de comandos SQL"""
        print(f"\n{Fore.CYAN}📚 COMANDOS SQL DISPONÍVEIS:")
        print(f"{Fore.WHITE}   SELECT - Consultar dados")
        print(f"{Fore.WHITE}   INSERT - Inserir dados")
        print(f"{Fore.WHITE}   UPDATE - Atualizar dados")
        print(f"{Fore.WHITE}   DELETE - Deletar dados")
        print(f"{Fore.WHITE}   CREATE - Criar tabelas/índices")
        print(f"{Fore.WHITE}   DROP   - Remover tabelas/índices")
        print(f"{Fore.WHITE}   ALTER  - Alterar estrutura")
        
        print(f"\n{Fore.CYAN}📖 EXEMPLOS:")
        print(f"{Fore.GREEN}   SELECT * FROM restaurants LIMIT 10")
        print(f"{Fore.GREEN}   SELECT category, COUNT(*) FROM restaurants GROUP BY category")
        print(f"{Fore.GREEN}   SELECT name, price FROM products WHERE price > 20")
        print(f"{Fore.GREEN}   UPDATE restaurants SET rating = 4.5 WHERE id = 1")
    
    def _show_available_tables(self, conn):
        """Mostrar tabelas disponíveis"""
        try:
            tables = conn.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'main' ORDER BY table_name
            """).fetchall()
            
            if tables:
                print(f"\n{Fore.CYAN}📋 TABELAS DISPONÍVEIS:")
                for table in tables:
                    table_name = table[0]
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    print(f"{Fore.WHITE}   • {table_name} ({count:,} registros)")
            else:
                print(f"\n{Fore.YELLOW}⚠️ Nenhuma tabela encontrada!")
                
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao listar tabelas: {str(e)}")
    
    def _export_query_results(self, query, results, columns):
        """Exportar resultados da consulta para CSV"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_result_{timestamp}.csv"
            filepath = f"exports/{filename}"
            
            os.makedirs("exports", exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in results:
                    writer.writerow(row)
            
            print(f"\n{Fore.GREEN}✅ Resultados exportados para: {filepath}")
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro ao exportar: {str(e)}")
    
    def predefined_reports(self):
        """Consultas predefinidas (relatórios)"""
        try:
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║               RELATÓRIOS PREDEFINIDOS                   ║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
            
            while True:
                print(f"\n{Fore.YELLOW}📊 RELATÓRIOS DISPONÍVEIS:")
                print(f"{Fore.WHITE}[1] Top 10 restaurantes por rating")
                print(f"{Fore.WHITE}[2] Restaurantes por categoria")
                print(f"{Fore.WHITE}[3] Produtos mais caros")
                print(f"{Fore.WHITE}[4] Estatísticas de delivery")
                print(f"{Fore.WHITE}[5] Análise de preços por categoria")
                print(f"{Fore.WHITE}[6] Restaurantes sem produtos cadastrados")
                print(f"{Fore.WHITE}[7] Resumo geral do banco")
                print(f"{Fore.WHITE}[8] Análise de ratings")
                print(f"{Fore.RED}[0] Voltar")
                
                choice = input(f"\n{Fore.GREEN}Escolha um relatório: {Style.RESET_ALL}").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    self._report_top_restaurants()
                elif choice == '2':
                    self._report_restaurants_by_category()
                elif choice == '3':
                    self._report_expensive_products()
                elif choice == '4':
                    self._report_delivery_stats()
                elif choice == '5':
                    self._report_price_analysis()
                elif choice == '6':
                    self._report_restaurants_without_products()
                elif choice == '7':
                    self._report_general_summary()
                elif choice == '8':
                    self._report_ratings_analysis()
                else:
                    print(f"{Fore.RED}Opção inválida!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    
        except Exception as e:
            self.logger.error(f"Erro nos relatórios: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro: {str(e)}")
            input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _execute_report(self, title, query, description=""):
        """Executar relatório e mostrar resultados"""
        try:
            print(f"\n{Fore.CYAN}📋 {title.upper()}")
            if description:
                print(f"{Fore.WHITE}{description}")
            print(f"{Fore.CYAN}{'─'*60}")
            
            conn = self.db_manager._get_connection()
            start_time = time.time()
            
            result = conn.execute(query).fetchall()
            execution_time = time.time() - start_time
            
            if result:
                columns = [desc[0] for desc in conn.description]
                print(f"\n{self._format_query_result(result, columns)}")
                print(f"\n{Fore.CYAN}📊 {len(result)} resultados em {execution_time:.3f}s")
            else:
                print(f"\n{Fore.YELLOW}📊 Nenhum resultado encontrado")
            
            # Salvar no histórico
            self._save_to_history(query, execution_time, len(result) if result else 0)
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro no relatório: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _report_top_restaurants(self):
        """Relatório: Top 10 restaurantes por rating"""
        query = """
            SELECT name, category, rating, city, delivery_fee
            FROM restaurants 
            WHERE rating IS NOT NULL 
            ORDER BY rating DESC, name 
            LIMIT 10
        """
        self._execute_report(
            "Top 10 Restaurantes por Rating",
            query,
            "Restaurantes com melhor avaliação"
        )
    
    def _report_restaurants_by_category(self):
        """Relatório: Restaurantes por categoria"""
        query = """
            SELECT category, COUNT(*) as total, 
                   AVG(rating) as avg_rating,
                   MIN(delivery_fee) as min_delivery,
                   MAX(delivery_fee) as max_delivery
            FROM restaurants 
            GROUP BY category 
            ORDER BY total DESC
        """
        self._execute_report(
            "Restaurantes por Categoria",
            query,
            "Distribuição e estatísticas por categoria"
        )
    
    def _report_expensive_products(self):
        """Relatório: Produtos mais caros"""
        query = """
            SELECT restaurant_name, name, category, price
            FROM products 
            WHERE price IS NOT NULL 
            ORDER BY price DESC 
            LIMIT 20
        """
        self._execute_report(
            "Top 20 Produtos Mais Caros",
            query,
            "Produtos com maiores preços"
        )
    
    def _report_delivery_stats(self):
        """Relatório: Estatísticas de delivery"""
        query = """
            SELECT 
                COUNT(*) as total_restaurants,
                COUNT(CASE WHEN delivery_fee = 0 THEN 1 END) as free_delivery,
                ROUND(AVG(delivery_fee), 2) as avg_delivery_fee,
                MIN(delivery_fee) as min_fee,
                MAX(delivery_fee) as max_fee
            FROM restaurants 
            WHERE delivery_fee IS NOT NULL
        """
        self._execute_report(
            "Estatísticas de Delivery",
            query,
            "Análise de taxas de entrega"
        )
    
    def _report_price_analysis(self):
        """Relatório: Análise de preços por categoria"""
        query = """
            SELECT category,
                   COUNT(*) as total_products,
                   ROUND(AVG(price), 2) as avg_price,
                   ROUND(MIN(price), 2) as min_price,
                   ROUND(MAX(price), 2) as max_price
            FROM products 
            WHERE price IS NOT NULL 
            GROUP BY category 
            ORDER BY avg_price DESC
        """
        self._execute_report(
            "Análise de Preços por Categoria",
            query,
            "Estatísticas de preços dos produtos"
        )
    
    def _report_restaurants_without_products(self):
        """Relatório: Restaurantes sem produtos"""
        query = """
            SELECT r.name, r.category, r.city, r.rating
            FROM restaurants r
            LEFT JOIN products p ON r.id = p.restaurant_id
            WHERE p.restaurant_id IS NULL
            ORDER BY r.rating DESC
        """
        self._execute_report(
            "Restaurantes sem Produtos Cadastrados",
            query,
            "Restaurantes que ainda não têm cardápio"
        )
    
    def _report_general_summary(self):
        """Relatório: Resumo geral"""
        query = """
            SELECT 
                'Restaurantes' as item,
                COUNT(*) as total
            FROM restaurants
            UNION ALL
            SELECT 
                'Produtos' as item,
                COUNT(*) as total
            FROM products
            UNION ALL
            SELECT 
                'Categorias' as item,
                COUNT(*) as total
            FROM categories
        """
        self._execute_report(
            "Resumo Geral do Banco",
            query,
            "Totais gerais por tabela"
        )
    
    def _report_ratings_analysis(self):
        """Relatório: Análise de ratings"""
        query = """
            SELECT 
                CASE 
                    WHEN rating >= 4.5 THEN 'Excelente (4.5+)'
                    WHEN rating >= 4.0 THEN 'Muito Bom (4.0-4.4)'
                    WHEN rating >= 3.5 THEN 'Bom (3.5-3.9)'
                    WHEN rating >= 3.0 THEN 'Regular (3.0-3.4)'
                    ELSE 'Baixo (<3.0)'
                END as rating_category,
                COUNT(*) as total_restaurants,
                ROUND(AVG(rating), 2) as avg_rating
            FROM restaurants 
            WHERE rating IS NOT NULL
            GROUP BY rating_category
            ORDER BY avg_rating DESC
        """
        self._execute_report(
            "Análise de Ratings",
            query,
            "Distribuição de restaurantes por faixa de rating"
        )
    
    def table_statistics(self):
        """Estatísticas das tabelas"""
        try:
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║               ESTATÍSTICAS DAS TABELAS                   ║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
            
            conn = self.db_manager._get_connection()
            
            # Obter lista de tabelas
            tables = conn.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'main' ORDER BY table_name
            """).fetchall()
            
            if not tables:
                print(f"\n{Fore.YELLOW}⚠️ Nenhuma tabela encontrada!")
                conn.close()
                return
            
            print(f"\n{Fore.WHITE}📊 ESTATÍSTICAS GERAIS:")
            print(f"{Fore.WHITE}{'Tabela':<20} {'Registros':<12} {'Campos':<8} {'Última Atualização'}")
            print(f"{Fore.WHITE}{'-'*20} {'-'*12} {'-'*8} {'-'*20}")
            
            total_records = 0
            
            for table in tables:
                table_name = table[0]
                
                # Contar registros
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                total_records += count
                
                # Contar campos
                columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                field_count = len(columns)
                
                # Simular última atualização (não disponível em DuckDB)
                last_update = "N/A"
                
                print(f"{Fore.CYAN}{table_name:<20} {count:,<12} {field_count:<8} {last_update}")
            
            print(f"\n{Fore.GREEN}📈 TOTAL GERAL: {total_records:,} registros")
            
            # Estatísticas detalhadas por tabela
            print(f"\n{Fore.YELLOW}📋 ESTATÍSTICAS DETALHADAS:")
            
            for table in tables:
                table_name = table[0]
                print(f"\n{Fore.CYAN}🔹 {table_name.upper()}:")
                
                try:
                    # Estrutura da tabela
                    columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                    print(f"{Fore.WHITE}   • Campos: {len(columns)}")
                    
                    # Contagem
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    print(f"{Fore.WHITE}   • Registros: {count:,}")
                    
                    if count > 0:
                        # Estatísticas específicas por tabela
                        if table_name == 'restaurants':
                            # Estatísticas de restaurantes
                            avg_rating = conn.execute("SELECT AVG(rating) FROM restaurants WHERE rating IS NOT NULL").fetchone()[0]
                            cities = conn.execute("SELECT COUNT(DISTINCT city) FROM restaurants").fetchone()[0]
                            categories = conn.execute("SELECT COUNT(DISTINCT category) FROM restaurants").fetchone()[0]
                            
                            if avg_rating:
                                print(f"{Fore.GREEN}   • Rating médio: {avg_rating:.2f}")
                            print(f"{Fore.GREEN}   • Cidades: {cities}")
                            print(f"{Fore.GREEN}   • Categorias: {categories}")
                            
                        elif table_name == 'products':
                            # Estatísticas de produtos
                            avg_price = conn.execute("SELECT AVG(price) FROM products WHERE price IS NOT NULL").fetchone()[0]
                            restaurants_with_products = conn.execute("SELECT COUNT(DISTINCT restaurant_id) FROM products").fetchone()[0]
                            
                            if avg_price:
                                print(f"{Fore.GREEN}   • Preço médio: R$ {avg_price:.2f}")
                            print(f"{Fore.GREEN}   • Restaurantes com produtos: {restaurants_with_products}")
                            
                        elif table_name == 'categories':
                            # Estatísticas de categorias
                            print(f"{Fore.GREEN}   • Total de categorias disponíveis")
                    
                    else:
                        print(f"{Fore.YELLOW}   • Tabela vazia")
                        
                except Exception as e:
                    print(f"{Fore.RED}   • Erro ao analisar: {str(e)}")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro nas estatísticas: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def join_queries(self):
        """Consultas com JOIN entre tabelas"""
        try:
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║                 CONSULTAS COM JOIN                       ║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
            
            while True:
                print(f"\n{Fore.YELLOW}🔗 CONSULTAS DISPONÍVEIS:")
                print(f"{Fore.WHITE}[1] Restaurantes com seus produtos")
                print(f"{Fore.WHITE}[2] Produtos mais caros por restaurante")
                print(f"{Fore.WHITE}[3] Cardápio completo de um restaurante")
                print(f"{Fore.WHITE}[4] Restaurantes por categoria com contagem de produtos")
                print(f"{Fore.WHITE}[5] Análise de preços médios por categoria de restaurante")
                print(f"{Fore.WHITE}[6] Produtos sem descrição por restaurante")
                print(f"{Fore.RED}[0] Voltar")
                
                choice = input(f"\n{Fore.GREEN}Escolha uma consulta: {Style.RESET_ALL}").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    self._join_restaurants_products()
                elif choice == '2':
                    self._join_expensive_products_by_restaurant()
                elif choice == '3':
                    self._join_restaurant_menu()
                elif choice == '4':
                    self._join_category_product_count()
                elif choice == '5':
                    self._join_avg_prices_by_category()
                elif choice == '6':
                    self._join_products_no_description()
                else:
                    print(f"{Fore.RED}Opção inválida!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    
        except Exception as e:
            self.logger.error(f"Erro nas consultas JOIN: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro: {str(e)}")
            input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _join_restaurants_products(self):
        """JOIN: Restaurantes com seus produtos"""
        query = """
            SELECT r.name as restaurant, r.category, r.rating,
                   COUNT(p.id) as total_products,
                   ROUND(AVG(p.price), 2) as avg_product_price
            FROM restaurants r
            LEFT JOIN products p ON r.id = p.restaurant_id
            GROUP BY r.id, r.name, r.category, r.rating
            ORDER BY total_products DESC, r.rating DESC
            LIMIT 20
        """
        self._execute_report(
            "Restaurantes com Produtos",
            query,
            "Restaurantes e resumo de seus cardápios"
        )
    
    def _join_expensive_products_by_restaurant(self):
        """JOIN: Produtos mais caros por restaurante"""
        query = """
            SELECT r.name as restaurant, r.category,
                   p.name as product, p.price, p.description
            FROM restaurants r
            INNER JOIN products p ON r.id = p.restaurant_id
            WHERE p.price IS NOT NULL
            AND p.price = (
                SELECT MAX(price) 
                FROM products p2 
                WHERE p2.restaurant_id = r.id AND p2.price IS NOT NULL
            )
            ORDER BY p.price DESC
            LIMIT 15
        """
        self._execute_report(
            "Produto Mais Caro de Cada Restaurante",
            query,
            "Item mais caro do cardápio por restaurante"
        )
    
    def _join_restaurant_menu(self):
        """JOIN: Cardápio completo de um restaurante"""
        try:
            # Primeiro listar restaurantes disponíveis
            conn = self.db_manager._get_connection()
            restaurants = conn.execute("""
                SELECT r.id, r.name, COUNT(p.id) as product_count
                FROM restaurants r
                LEFT JOIN products p ON r.id = p.restaurant_id
                GROUP BY r.id, r.name
                HAVING product_count > 0
                ORDER BY r.name
                LIMIT 20
            """).fetchall()
            
            if not restaurants:
                print(f"\n{Fore.YELLOW}⚠️ Nenhum restaurante com produtos encontrado!")
                conn.close()
                return
            
            print(f"\n{Fore.CYAN}🍽️ RESTAURANTES COM CARDÁPIO:")
            for i, rest in enumerate(restaurants, 1):
                print(f"{Fore.WHITE}[{i}] {rest[1]} ({rest[2]} produtos)")
            
            try:
                choice = int(input(f"\n{Fore.GREEN}Escolha um restaurante: ")) - 1
                
                if 0 <= choice < len(restaurants):
                    restaurant_id = restaurants[choice][0]
                    restaurant_name = restaurants[choice][1]
                    
                    query = f"""
                        SELECT p.category, p.name, p.description, p.price
                        FROM products p
                        INNER JOIN restaurants r ON r.id = p.restaurant_id
                        WHERE r.id = {restaurant_id}
                        ORDER BY p.category, p.price DESC
                    """
                    
                    self._execute_report(
                        f"Cardápio Completo - {restaurant_name}",
                        query,
                        f"Todos os produtos disponíveis"
                    )
                else:
                    print(f"{Fore.RED}Restaurante inválido!")
                    
            except ValueError:
                print(f"{Fore.RED}Número inválido!")
            
            conn.close()
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro: {str(e)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _join_category_product_count(self):
        """JOIN: Restaurantes por categoria com contagem de produtos"""
        query = """
            SELECT r.category as restaurant_category,
                   COUNT(DISTINCT r.id) as total_restaurants,
                   COUNT(p.id) as total_products,
                   ROUND(AVG(p.price), 2) as avg_product_price,
                   ROUND(AVG(r.rating), 2) as avg_restaurant_rating
            FROM restaurants r
            LEFT JOIN products p ON r.id = p.restaurant_id
            GROUP BY r.category
            ORDER BY total_products DESC
        """
        self._execute_report(
            "Análise por Categoria de Restaurante",
            query,
            "Estatísticas completas por categoria"
        )
    
    def _join_avg_prices_by_category(self):
        """JOIN: Análise de preços médios por categoria"""
        query = """
            SELECT r.category as restaurant_category,
                   p.category as product_category,
                   COUNT(p.id) as product_count,
                   ROUND(MIN(p.price), 2) as min_price,
                   ROUND(AVG(p.price), 2) as avg_price,
                   ROUND(MAX(p.price), 2) as max_price
            FROM restaurants r
            INNER JOIN products p ON r.id = p.restaurant_id
            WHERE p.price IS NOT NULL
            GROUP BY r.category, p.category
            ORDER BY r.category, avg_price DESC
        """
        self._execute_report(
            "Preços por Categoria de Restaurante e Produto",
            query,
            "Análise detalhada de precificação"
        )
    
    def _join_products_no_description(self):
        """JOIN: Produtos sem descrição por restaurante"""
        query = """
            SELECT r.name as restaurant, r.category,
                   COUNT(p.id) as products_without_description
            FROM restaurants r
            INNER JOIN products p ON r.id = p.restaurant_id
            WHERE p.description IS NULL OR p.description = ''
            GROUP BY r.id, r.name, r.category
            ORDER BY products_without_description DESC
            LIMIT 15
        """
        self._execute_report(
            "Produtos sem Descrição",
            query,
            "Restaurantes com produtos que precisam de descrição"
        )
    
    def query_history(self):
        """Histórico de consultas executadas"""
        try:
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║               HISTÓRICO DE CONSULTAS                     ║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
            
            # Carregar histórico
            if not os.path.exists(self.history_file):
                print(f"\n{Fore.YELLOW}📝 Nenhum histórico encontrado!")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            
            if not history:
                print(f"\n{Fore.YELLOW}📝 Histórico vazio!")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            while True:
                print(f"\n{Fore.YELLOW}📋 OPÇÕES DO HISTÓRICO:")
                print(f"{Fore.WHITE}[1] Ver últimas 20 consultas")
                print(f"{Fore.WHITE}[2] Ver consultas com erro")
                print(f"{Fore.WHITE}[3] Ver consultas mais lentas")
                print(f"{Fore.WHITE}[4] Estatísticas do histórico")
                print(f"{Fore.WHITE}[5] Buscar no histórico")
                print(f"{Fore.WHITE}[6] Limpar histórico")
                print(f"{Fore.RED}[0] Voltar")
                
                choice = input(f"\n{Fore.GREEN}Escolha: {Style.RESET_ALL}").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    self._show_recent_queries(history)
                elif choice == '2':
                    self._show_error_queries(history)
                elif choice == '3':
                    self._show_slow_queries(history)
                elif choice == '4':
                    self._show_history_stats(history)
                elif choice == '5':
                    self._search_history(history)
                elif choice == '6':
                    self._clear_history()
                    break
                else:
                    print(f"{Fore.RED}Opção inválida!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    
        except Exception as e:
            self.logger.error(f"Erro no histórico: {str(e)}")
            print(f"\n{Fore.RED}❌ Erro: {str(e)}")
            input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_recent_queries(self, history):
        """Mostrar últimas consultas"""
        recent = history[-20:]  # Últimas 20
        recent.reverse()  # Mais recentes primeiro
        
        print(f"\n{Fore.CYAN}📝 ÚLTIMAS 20 CONSULTAS:")
        print(f"{Fore.WHITE}{'#':<3} {'Data/Hora':<20} {'Status':<8} {'Tempo':<8} {'Resultados':<12} {'Query'}")
        print(f"{Fore.WHITE}{'-'*3} {'-'*20} {'-'*8} {'-'*8} {'-'*12} {'-'*30}")
        
        for i, entry in enumerate(recent, 1):
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%d/%m %H:%M:%S")
            status = "✅" if entry['status'] == 'success' else "❌"
            exec_time = f"{entry['execution_time']:.3f}s"
            result_count = f"{entry['result_count']}"
            
            # Truncar query para exibição
            query = entry['query'].replace('\n', ' ').strip()
            if len(query) > 50:
                query = query[:47] + "..."
            
            color = Fore.GREEN if entry['status'] == 'success' else Fore.RED
            print(f"{color}{i:<3} {timestamp:<20} {status:<8} {exec_time:<8} {result_count:<12} {query}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_error_queries(self, history):
        """Mostrar consultas com erro"""
        errors = [h for h in history if h['status'] == 'error']
        
        if not errors:
            print(f"\n{Fore.GREEN}🎉 Nenhuma consulta com erro encontrada!")
        else:
            print(f"\n{Fore.RED}❌ CONSULTAS COM ERRO ({len(errors)}):")
            
            for i, entry in enumerate(errors[-10:], 1):  # Últimos 10 erros
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%d/%m/%Y %H:%M:%S")
                print(f"\n{Fore.YELLOW}[{i}] {timestamp}")
                print(f"{Fore.WHITE}Query: {entry['query']}")
                print(f"{Fore.RED}Erro: {entry['error']}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_slow_queries(self, history):
        """Mostrar consultas mais lentas"""
        # Ordenar por tempo de execução (decrescente)
        slow_queries = sorted(history, key=lambda x: x['execution_time'], reverse=True)[:10]
        
        print(f"\n{Fore.YELLOW}🐌 TOP 10 CONSULTAS MAIS LENTAS:")
        print(f"{Fore.WHITE}{'#':<3} {'Tempo':<10} {'Status':<8} {'Resultados':<12} {'Query'}")
        print(f"{Fore.WHITE}{'-'*3} {'-'*10} {'-'*8} {'-'*12} {'-'*40}")
        
        for i, entry in enumerate(slow_queries, 1):
            exec_time = f"{entry['execution_time']:.3f}s"
            status = "✅" if entry['status'] == 'success' else "❌"
            result_count = f"{entry['result_count']}"
            
            query = entry['query'].replace('\n', ' ').strip()
            if len(query) > 60:
                query = query[:57] + "..."
            
            color = Fore.RED if entry['execution_time'] > 1.0 else Fore.YELLOW
            print(f"{color}{i:<3} {exec_time:<10} {status:<8} {result_count:<12} {query}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_history_stats(self, history):
        """Mostrar estatísticas do histórico"""
        if not history:
            print(f"\n{Fore.YELLOW}📊 Histórico vazio!")
            return
        
        total_queries = len(history)
        successful = len([h for h in history if h['status'] == 'success'])
        errors = total_queries - successful
        
        times = [h['execution_time'] for h in history]
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\n{Fore.CYAN}📊 ESTATÍSTICAS DO HISTÓRICO:")
        print(f"{Fore.WHITE}   • Total de consultas: {total_queries}")
        print(f"{Fore.GREEN}   • Consultas bem-sucedidas: {successful} ({successful/total_queries*100:.1f}%)")
        print(f"{Fore.RED}   • Consultas com erro: {errors} ({errors/total_queries*100:.1f}%)")
        print(f"{Fore.YELLOW}   • Tempo médio: {avg_time:.3f}s")
        print(f"{Fore.YELLOW}   • Tempo mínimo: {min_time:.3f}s")
        print(f"{Fore.YELLOW}   • Tempo máximo: {max_time:.3f}s")
        
        # Estatísticas por período
        now = datetime.now()
        today = len([h for h in history if datetime.fromisoformat(h['timestamp']).date() == now.date()])
        
        print(f"\n{Fore.CYAN}📅 CONSULTAS POR PERÍODO:")
        print(f"{Fore.WHITE}   • Hoje: {today}")
        print(f"{Fore.WHITE}   • Total histórico: {total_queries}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _search_history(self, history):
        """Buscar no histórico"""
        search_term = input(f"\n{Fore.CYAN}🔍 Digite o termo para buscar: {Style.RESET_ALL}").strip()
        
        if not search_term:
            return
        
        matches = [h for h in history if search_term.lower() in h['query'].lower()]
        
        if not matches:
            print(f"\n{Fore.YELLOW}🔍 Nenhuma consulta encontrada com '{search_term}'")
        else:
            print(f"\n{Fore.GREEN}🔍 {len(matches)} consultas encontradas:")
            
            for i, entry in enumerate(matches[-10:], 1):  # Últimas 10 matches
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%d/%m %H:%M")
                status = "✅" if entry['status'] == 'success' else "❌"
                
                print(f"\n{Fore.CYAN}[{i}] {timestamp} {status}")
                print(f"{Fore.WHITE}{entry['query']}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _clear_history(self):
        """Limpar histórico"""
        confirm = input(f"\n{Fore.RED}⚠️ Confirma limpeza do histórico? (s/N): ").strip().lower()
        
        if confirm == 's':
            with open(self.history_file, 'w') as f:
                json.dump([], f)
            print(f"\n{Fore.GREEN}✅ Histórico limpo com sucesso!")
        else:
            print(f"\n{Fore.CYAN}Operação cancelada.")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")