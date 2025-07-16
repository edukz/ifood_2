"""
Scraper de informações extras (avaliações e pedido mínimo)
"""
import asyncio
import time
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from colorama import Fore, Style
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager

class ExtraInfoScraper:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
        self.base_url = "https://www.ifood.com.br"
        
        # Seletores para informações extras
        self.seletores = {
            # Botão de avaliações
            "botao_rating": {
                "principal": "#__next > div:nth-child(1) > main > div.restaurant-container > div > header.merchant-info > div.merchant-info__content-container > div > div.merchant-info__title-container > div > a > button",
                "alternativo": "[data-test-id='restaurant-rating__evaluation']",
                "classe": ".restaurant-rating__button"
            },
            # Contador de avaliações
            "reviews_count": {
                "principal": "body > div.drawer > div > div > div > section > div.rating-counter > h3",
                "alternativo": ".rating-counter h3",
                "texto": "div.rating-counter"
            },
            # Botão fechar drawer
            "fechar_drawer": {
                "principal": "body > div.drawer > div > div > button",
                "alternativo": ".drawer button[aria-label*='fechar']",
                "svg": "button > span > svg"
            },
            # Pedido mínimo
            "pedido_minimo": {
                "principal": "#__next > div:nth-child(1) > main > div.restaurant-container > div > header.merchant-info > div.merchant-info__content-container > div > div.merchant-info__detail-container > div.merchant-info__minimum-order",
                "alternativo": ".merchant-info__minimum-order",
                "texto": "[class*='minimum-order']"
            }
        }
    
    def _verificar_colunas_extras(self):
        """Verificar e adicionar colunas reviews e min_order se necessário"""
        try:
            conn = self.db_manager._get_connection()
            
            # Verificar e adicionar coluna reviews
            try:
                conn.execute("SELECT reviews FROM restaurants LIMIT 1")
                # Coluna existe, continuar silenciosamente
            except:
                print(f"{Fore.YELLOW}⚠️ Adicionando coluna 'reviews' à tabela...")
                try:
                    conn.execute("ALTER TABLE restaurants ADD COLUMN reviews INTEGER")
                    print(f"{Fore.GREEN}✅ Coluna 'reviews' adicionada!")
                except Exception as e:
                    print(f"{Fore.RED}❌ Erro ao adicionar coluna reviews: {e}")
            
            # Verificar e adicionar coluna min_order
            try:
                conn.execute("SELECT min_order FROM restaurants LIMIT 1")
                # Coluna existe, continuar silenciosamente
            except:
                print(f"{Fore.YELLOW}⚠️ Adicionando coluna 'min_order' à tabela...")
                try:
                    conn.execute("ALTER TABLE restaurants ADD COLUMN min_order DECIMAL(10,2)")
                    print(f"{Fore.GREEN}✅ Coluna 'min_order' adicionada!")
                except Exception as e:
                    print(f"{Fore.RED}❌ Erro ao adicionar coluna min_order: {e}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar/criar colunas extras: {str(e)}")
            return False
    
    def obter_restaurantes_para_atualizar(self):
        """Obter restaurantes que ainda não têm informações extras"""
        try:
            conn = self.db_manager._get_connection()
            
            # Buscar restaurantes sem reviews ou min_order
            result = conn.execute("""
                SELECT id, name, category, link 
                FROM restaurants 
                WHERE (reviews IS NULL OR min_order IS NULL)
                AND link IS NOT NULL 
                AND link != 'N/A'
                ORDER BY category, name
            """).fetchall()
            
            conn.close()
            
            return [{"id": row[0], "nome": row[1], "categoria": row[2], "link": row[3]} for row in result]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter restaurantes: {str(e)}")
            return []
    
    def obter_todos_restaurantes(self):
        """Obter todos os restaurantes para atualização"""
        try:
            conn = self.db_manager._get_connection()
            
            result = conn.execute("""
                SELECT id, name, category, link 
                FROM restaurants 
                WHERE link IS NOT NULL AND link != 'N/A'
                ORDER BY category, name
            """).fetchall()
            
            conn.close()
            
            return [{"id": row[0], "nome": row[1], "categoria": row[2], "link": row[3]} for row in result]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter todos os restaurantes: {str(e)}")
            return []
    
    async def coletar_avaliacoes(self, page):
        """Coletar número de avaliações do restaurante"""
        try:
            print(f"{Fore.CYAN}   📊 Coletando avaliações...")
            
            # Estratégia 1: Clicar no botão de rating
            botao_clicado = False
            for seletor in [self.seletores["botao_rating"]["principal"], 
                           self.seletores["botao_rating"]["alternativo"],
                           self.seletores["botao_rating"]["classe"]]:
                try:
                    botao = await page.wait_for_selector(seletor, timeout=5000)
                    if botao:
                        await botao.click()
                        await asyncio.sleep(2)  # Aguardar drawer abrir
                        botao_clicado = True
                        print(f"{Fore.GREEN}   ✅ Drawer de avaliações aberto")
                        break
                except:
                    continue
            
            if not botao_clicado:
                print(f"{Fore.YELLOW}   ⚠️ Não foi possível abrir drawer de avaliações")
                return None
            
            # Coletar quantidade de avaliações
            reviews_count = None
            for seletor in [self.seletores["reviews_count"]["principal"],
                           self.seletores["reviews_count"]["alternativo"],
                           self.seletores["reviews_count"]["texto"]]:
                try:
                    elemento = await page.wait_for_selector(seletor, timeout=3000)
                    if elemento:
                        texto = await elemento.inner_text()
                        # Extrair número do texto (ex: "1.234 avaliações" -> 1234)
                        import re
                        numeros = re.findall(r'\d+', texto.replace('.', '').replace(',', ''))
                        if numeros:
                            reviews_count = int(numeros[0])
                            print(f"{Fore.GREEN}   ✅ Avaliações encontradas: {reviews_count}")
                            break
                except:
                    continue
            
            # Fechar drawer
            for seletor in [self.seletores["fechar_drawer"]["principal"],
                           self.seletores["fechar_drawer"]["alternativo"]]:
                try:
                    botao_fechar = await page.query_selector(seletor)
                    if botao_fechar:
                        await botao_fechar.click()
                        await asyncio.sleep(1)
                        print(f"{Fore.GREEN}   ✅ Drawer fechado")
                        break
                except:
                    continue
            
            return reviews_count
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Erro ao coletar avaliações: {str(e)}")
            return None
    
    async def coletar_pedido_minimo(self, page):
        """Coletar valor do pedido mínimo"""
        try:
            print(f"{Fore.CYAN}   💰 Coletando pedido mínimo...")
            
            pedido_minimo = None
            
            for seletor in [self.seletores["pedido_minimo"]["principal"],
                           self.seletores["pedido_minimo"]["alternativo"],
                           self.seletores["pedido_minimo"]["texto"]]:
                try:
                    elemento = await page.query_selector(seletor)
                    if elemento:
                        texto = await elemento.inner_text()
                        # Extrair valor do texto (ex: "Pedido mínimo R$ 20,00" -> 20.00)
                        import re
                        match = re.search(r'R\$\s*([\d,]+)', texto)
                        if match:
                            valor_str = match.group(1).replace(',', '.')
                            pedido_minimo = float(valor_str)
                            print(f"{Fore.GREEN}   ✅ Pedido mínimo: R$ {pedido_minimo:.2f}")
                            break
                except:
                    continue
            
            if pedido_minimo is None:
                print(f"{Fore.YELLOW}   ⚠️ Pedido mínimo não encontrado")
            
            return pedido_minimo
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Erro ao coletar pedido mínimo: {str(e)}")
            return None
    
    async def coletar_info_extra_restaurante(self, page, restaurant_data):
        """Coletar informações extras de um restaurante específico"""
        try:
            restaurant_name = restaurant_data['nome']
            restaurant_link = restaurant_data['link']
            
            print(f"\n{Fore.MAGENTA}🍴 Coletando info extra: {restaurant_name}")
            
            # Navegar para o restaurante
            if restaurant_link and restaurant_link != "N/A":
                print(f"{Fore.CYAN}   🔗 Navegando para: {restaurant_link[:50]}...")
                await page.goto(restaurant_link, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
            else:
                print(f"{Fore.RED}   ❌ Link inválido para {restaurant_name}")
                return None, None
            
            # Coletar pedido mínimo primeiro (já está visível)
            pedido_minimo = await self.coletar_pedido_minimo(page)
            
            # Coletar avaliações (precisa abrir drawer)
            reviews = await self.coletar_avaliacoes(page)
            
            return reviews, pedido_minimo
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao coletar info extra de {restaurant_data['nome']}: {str(e)}")
            return None, None
    
    def atualizar_info_extra_banco(self, restaurant_id, reviews, min_order):
        """Atualizar informações extras no banco de dados"""
        try:
            conn = self.db_manager._get_connection()
            
            # Preparar query de update
            updates = []
            params = []
            
            if reviews is not None:
                updates.append("reviews = ?")
                params.append(reviews)
            
            if min_order is not None:
                updates.append("min_order = ?")
                params.append(min_order)
            
            if updates:
                params.append(restaurant_id)
                query = f"UPDATE restaurants SET {', '.join(updates)} WHERE id = ?"
                conn.execute(query, params)
                conn.commit()
                
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar info extra: {str(e)}")
            return False
    
    def exibir_menu_selecao(self):
        """Exibir menu para seleção de restaurantes"""
        print(f"\n{Fore.CYAN}🔍 COLETA DE INFORMAÇÕES EXTRAS:")
        print(f"{Fore.MAGENTA}{'─'*60}")
        print(f"{Fore.WHITE}[1] Coletar info extra de um restaurante específico")
        print(f"{Fore.WHITE}[2] Coletar info extra de uma categoria específica")
        print(f"{Fore.WHITE}[3] Coletar info extra de todos os restaurantes")
        print(f"{Fore.RED}[0] Voltar")
        
        while True:
            try:
                escolha = input(f"\n{Fore.YELLOW}➤ Escolha uma opção: ").strip()
                
                if escolha == '0':
                    return None
                elif escolha == '1':
                    return self._selecionar_restaurante_especifico()
                elif escolha == '2':
                    return self._selecionar_categoria_especifica()
                elif escolha == '3':
                    return self.obter_todos_restaurantes()
                else:
                    print(f"{Fore.RED}❌ Opção inválida!")
                    
            except ValueError:
                print(f"{Fore.RED}❌ Digite apenas números!")
    
    def _selecionar_restaurante_especifico(self):
        """Selecionar um restaurante específico"""
        restaurantes = self.obter_todos_restaurantes()
        
        if not restaurantes:
            print(f"{Fore.RED}❌ Nenhum restaurante encontrado!")
            return None
        
        print(f"\n{Fore.CYAN}🍴 RESTAURANTES DISPONÍVEIS:")
        print(f"{Fore.MAGENTA}{'─'*60}")
        
        for i, rest in enumerate(restaurantes, 1):
            print(f"{Fore.WHITE}[{i:2d}] {rest['nome']} ({rest['categoria']})")
        
        print(f"{Fore.RED}[0] Voltar")
        
        while True:
            try:
                escolha = int(input(f"\n{Fore.YELLOW}➤ Escolha um restaurante: "))
                
                if escolha == 0:
                    return None
                elif 1 <= escolha <= len(restaurantes):
                    return [restaurantes[escolha - 1]]
                else:
                    print(f"{Fore.RED}❌ Número inválido!")
                    
            except ValueError:
                print(f"{Fore.RED}❌ Digite apenas números!")
    
    def _selecionar_categoria_especifica(self):
        """Selecionar uma categoria específica"""
        try:
            conn = self.db_manager._get_connection()
            
            # Obter categorias disponíveis
            categorias = conn.execute("""
                SELECT DISTINCT category, COUNT(*) as count 
                FROM restaurants 
                WHERE link IS NOT NULL AND link != 'N/A'
                GROUP BY category 
                ORDER BY category
            """).fetchall()
            
            conn.close()
            
            if not categorias:
                print(f"{Fore.RED}❌ Nenhuma categoria encontrada!")
                return None
            
            print(f"\n{Fore.CYAN}📂 CATEGORIAS DISPONÍVEIS:")
            print(f"{Fore.MAGENTA}{'─'*60}")
            
            categoria_lista = []
            for i, (categoria, count) in enumerate(categorias, 1):
                print(f"{Fore.WHITE}[{i:2d}] {categoria} ({count} restaurantes)")
                categoria_lista.append(categoria)
            
            print(f"{Fore.RED}[0] Voltar")
            
            while True:
                try:
                    escolha = int(input(f"\n{Fore.YELLOW}➤ Escolha uma categoria: "))
                    
                    if escolha == 0:
                        return None
                    elif 1 <= escolha <= len(categoria_lista):
                        categoria_selecionada = categoria_lista[escolha - 1]
                        # Obter restaurantes da categoria
                        conn = self.db_manager._get_connection()
                        result = conn.execute("""
                            SELECT id, name, category, link 
                            FROM restaurants 
                            WHERE category = ? AND link IS NOT NULL AND link != 'N/A'
                            ORDER BY name
                        """, [categoria_selecionada]).fetchall()
                        conn.close()
                        
                        return [{
                            "id": row[0], 
                            "nome": row[1], 
                            "categoria": row[2], 
                            "link": row[3]
                        } for row in result]
                    else:
                        print(f"{Fore.RED}❌ Número inválido!")
                        
                except ValueError:
                    print(f"{Fore.RED}❌ Digite apenas números!")
                    
        except Exception as e:
            self.logger.error(f"Erro ao selecionar categoria: {str(e)}")
            return None
    
    async def executar_coleta_info_extra(self, restaurantes):
        """Executar coleta de informações extras"""
        tempo_inicio = time.time()
        sucesso_count = 0
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            try:
                print(f"\n{Fore.CYAN}📊 Iniciando coleta de {len(restaurantes)} restaurantes...")
                
                for i, restaurante in enumerate(restaurantes, 1):
                    print(f"\n{Fore.BLUE}[{i}/{len(restaurantes)}]", end="")
                    
                    # Coletar informações extras
                    reviews, min_order = await self.coletar_info_extra_restaurante(page, restaurante)
                    
                    # Atualizar no banco
                    if reviews is not None or min_order is not None:
                        sucesso = self.atualizar_info_extra_banco(
                            restaurante['id'], reviews, min_order
                        )
                        if sucesso:
                            sucesso_count += 1
                            print(f"{Fore.GREEN}   ✅ Info extra salva no banco!")
                        else:
                            print(f"{Fore.RED}   ❌ Erro ao salvar no banco")
                    else:
                        print(f"{Fore.YELLOW}   ⚠️ Nenhuma info extra coletada")
                    
                    # Pausa entre restaurantes
                    if i < len(restaurantes):
                        await asyncio.sleep(2)
                
                # Relatório final
                tempo_total = time.time() - tempo_inicio
                print(f"\n{Fore.YELLOW}📊 RESUMO DA COLETA:")
                print(f"{Fore.WHITE}   ⏱️ Tempo total: {tempo_total:.2f}s")
                print(f"{Fore.WHITE}   🍴 Restaurantes processados: {len(restaurantes)}")
                print(f"{Fore.WHITE}   ✅ Atualizações bem-sucedidas: {sucesso_count}")
                print(f"{Fore.WHITE}   🚀 Performance: {tempo_total/len(restaurantes):.1f}s por restaurante")
                
                self.logger.info(f"Coleta de info extra concluída: {sucesso_count}/{len(restaurantes)} em {tempo_total:.2f}s")
                
            except Exception as e:
                self.logger.error(f"Erro durante coleta de info extra: {str(e)}")
                print(f"\n{Fore.RED}❌ Erro durante coleta: {str(e)}")
                
            finally:
                await browser.close()
                print(f"\n{Fore.CYAN}🔒 Navegador fechado")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def scrape_extra(self):
        """Método principal - interface do menu"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║          SCRAPER DE INFORMAÇÕES EXTRAS                   ║")
        print(f"{Fore.YELLOW}║        (Avaliações e Pedido Mínimo)                     ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        # Verificar/criar colunas extras
        if not self._verificar_colunas_extras():
            print(f"{Fore.RED}❌ Erro ao preparar banco de dados")
            return
        
        # Menu de seleção
        restaurantes_selecionados = self.exibir_menu_selecao()
        
        if not restaurantes_selecionados:
            return
        
        # Mensagem personalizada baseada na seleção
        print(f"\n{Fore.YELLOW}📍 Cidade configurada: {self.db_manager.config_manager.get_default_city()}")
        
        if len(restaurantes_selecionados) == 1:
            print(f"\n{Fore.CYAN}🎯 Coletando info extra do restaurante: {restaurantes_selecionados[0]['nome']}")
        elif len(restaurantes_selecionados) > 1 and len(restaurantes_selecionados) < 50:
            categoria = restaurantes_selecionados[0]['categoria']
            print(f"\n{Fore.CYAN}🎯 Coletando info extra da categoria: {categoria}")
            print(f"{Fore.WHITE}   Restaurantes: {len(restaurantes_selecionados)}")
        else:
            print(f"\n{Fore.CYAN}🎯 Coletando info extra de TODOS os {len(restaurantes_selecionados)} restaurantes")
        
        # Executar coleta
        asyncio.run(self.executar_coleta_info_extra(restaurantes_selecionados))