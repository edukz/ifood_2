"""
Scraper de produtos por restaurante
"""
import asyncio
import time
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from colorama import Fore, Style
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager
from src.config.config_manager import ConfigManager

class ProductsScraper:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
        self.config_manager = ConfigManager()
        self.base_url = "https://www.ifood.com.br"
        
        # Seletores otimizados para produtos (baseados nos testes)
        self.seletores_produtos = {
            # Container principal dos produtos
            "container": "#__next > div:nth-child(1) > main > div.restaurant-container > div > div.restaurant-menu.restaurant-menu--hidden-search > div > div:nth-child(3) > ul > li",
            
            # Elementos dentro de cada produto
            "nome": {
                "principal": ".dish-card__info h3",
                "alternativo": "h3.dish-card__title, .dish-card__description h3",
                "xpath": ".//h3[contains(@class, 'dish-card')]"
            },
            "descricao": {
                "principal": ".dish-card__info span",
                "alternativo": ".dish-card__description, .dish-card__details", 
                "xpath": ".//span[contains(@class, 'dish-card__description')]"
            },
            "preco": {
                "principal": ".dish-card__info span:last-child",
                "alternativo": ".dish-card__price, span.price",
                "xpath": ".//span[contains(text(), 'R$')]"
            }
        }
        
        # Seletores alternativos para diferentes layouts
        self.seletores_alternativos = {
            "menu_container": [
                ".restaurant-menu",
                "[data-test-id='menu-list']",
                ".menu-items-list",
                ".dish-list",
                "ul[role='list']"
            ],
            "produto_item": [
                "li.dish-card",
                "[data-test-id='dish-item']",
                ".menu-item",
                "li[role='listitem']",
                ".dish-card-wrapper"
            ]
        }
    
    def _criar_tabela_produtos(self):
        """Criar tabela de produtos no banco se não existir"""
        try:
            conn = self.db_manager._get_connection()
            
            # Criar tabela products
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    restaurant_id INTEGER,
                    restaurant_name VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    name VARCHAR NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2),
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
                )
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.info("Tabela products criada/verificada com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar tabela products: {str(e)}")
            return False
    
    def obter_restaurantes_por_categoria(self):
        """Obter restaurantes agrupados por categoria"""
        try:
            conn = self.db_manager._get_connection()
            result = conn.execute("""
                SELECT category, name, id, link 
                FROM restaurants 
                ORDER BY category, name
            """).fetchall()
            conn.close()
            
            # Agrupar por categoria
            restaurantes_por_categoria = {}
            for row in result:
                categoria = row[0]
                if categoria not in restaurantes_por_categoria:
                    restaurantes_por_categoria[categoria] = []
                restaurantes_por_categoria[categoria].append({
                    "id": row[2],
                    "nome": row[1],
                    "link": row[3]
                })
            
            return restaurantes_por_categoria
            
        except Exception as e:
            self.logger.error(f"Erro ao obter restaurantes: {str(e)}")
            return {}
    
    def obter_todos_restaurantes(self):
        """Obter todos os restaurantes disponíveis"""
        try:
            conn = self.db_manager._get_connection()
            result = conn.execute("""
                SELECT id, name, category, link 
                FROM restaurants 
                ORDER BY category, name
            """).fetchall()
            conn.close()
            
            return [{"id": row[0], "nome": row[1], "categoria": row[2], "link": row[3]} for row in result]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter todos os restaurantes: {str(e)}")
            return []
    
    async def navegar_para_restaurante(self, page, restaurant_data):
        """Navegar para página de um restaurante específico usando o link salvo"""
        try:
            restaurant_name = restaurant_data.get('nome', 'N/A')
            restaurant_link = restaurant_data.get('link', '')
            
            print(f"{Fore.CYAN}🎯 Navegando para restaurante: {restaurant_name}")
            
            # Estratégia 1: Usar link direto do banco de dados
            if restaurant_link and restaurant_link != "N/A" and restaurant_link.startswith("http"):
                try:
                    print(f"{Fore.WHITE}   🔗 Usando link salvo: {restaurant_link[:50]}...")
                    await page.goto(restaurant_link, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(3)
                    
                    # Verificar se chegou na página do restaurante
                    page_title = await page.title()
                    if restaurant_name.lower() in page_title.lower() or "cardápio" in page_title.lower():
                        print(f"{Fore.GREEN}✅ Navegado diretamente para {restaurant_name}")
                        return True
                    else:
                        print(f"{Fore.YELLOW}⚠️ Link pode estar desatualizado, tentando busca...")
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Erro com link direto: {str(e)}")
            
            # Estratégia 2: Busca no iFood (fallback)
            try:
                print(f"{Fore.WHITE}   🔍 Fazendo busca por: {restaurant_name}")
                await page.goto(self.base_url, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                
                # Buscar pelo restaurante
                search_input = await page.wait_for_selector("input[placeholder*='buscar']", timeout=5000)
                if search_input:
                    await search_input.fill(restaurant_name)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(3)
                    
                    # Clicar no primeiro resultado
                    primeiro_resultado = await page.query_selector("a[href*='delivery']")
                    if primeiro_resultado:
                        await primeiro_resultado.click()
                        await asyncio.sleep(3)
                        print(f"{Fore.GREEN}✅ Encontrado via busca: {restaurant_name}")
                        return True
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Erro na busca: {str(e)}")
            
            # Estratégia 3: Navegação manual
            print(f"{Fore.YELLOW}⚠️ Navegação automática falhou para {restaurant_name}")
            print(f"{Fore.WHITE}   💡 Link esperado: {restaurant_link}")
            resposta = input(f"{Fore.GREEN}Navegue manualmente para o restaurante e pressione ENTER (ou 'skip' para pular): ")
            
            if resposta.lower() == 'skip':
                return False
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao navegar para restaurante: {str(e)}")
            return False
    
    async def coletar_produtos_restaurante(self, page, restaurant_id, restaurant_name, restaurant_category):
        """Coletar produtos de um restaurante específico"""
        try:
            self.logger.info(f"Coletando produtos do restaurante: {restaurant_name}")
            print(f"\n{Fore.CYAN}🍽️ Coletando produtos: {restaurant_name}")
            
            # Aguardar menu aparecer
            await asyncio.sleep(3)
            
            # Estratégia 1: Usar seletores específicos
            produtos = await page.query_selector_all(self.seletores_produtos["container"])
            
            if not produtos:
                # Estratégia 2: Seletores genéricos
                for container_sel in self.seletores_alternativos["menu_container"]:
                    try:
                        container = await page.query_selector(container_sel)
                        if container:
                            for item_sel in self.seletores_alternativos["produto_item"]:
                                produtos = await container.query_selector_all(item_sel)
                                if produtos:
                                    break
                        if produtos:
                            break
                    except:
                        continue
            
            if not produtos:
                # Estratégia 3: Busca ampla
                produtos = await page.query_selector_all("li[class*='dish'], li[class*='menu-item'], li[class*='product']")
            
            if not produtos:
                print(f"{Fore.YELLOW}   ⚠️ Nenhum produto encontrado")
                return []
            
            print(f"{Fore.WHITE}   📦 {len(produtos)} produtos encontrados")
            
            dados_coletados = []
            
            for i, produto in enumerate(produtos):
                try:
                    # Coletar nome
                    nome = "N/A"
                    for seletor in [self.seletores_produtos["nome"]["principal"], 
                                   self.seletores_produtos["nome"]["alternativo"]]:
                        try:
                            nome_elem = await produto.query_selector(seletor)
                            if nome_elem:
                                nome = await nome_elem.inner_text()
                                break
                        except:
                            continue
                    
                    # Se não encontrou nome com seletores específicos, tentar genéricos
                    if nome == "N/A":
                        for nome_sel in ["h3", "h4", "[class*='name']", "[class*='title']"]:
                            try:
                                nome_elem = await produto.query_selector(nome_sel)
                                if nome_elem:
                                    nome = await nome_elem.inner_text()
                                    break
                            except:
                                continue
                    
                    # Coletar descrição
                    descricao = "N/A"
                    for seletor in [self.seletores_produtos["descricao"]["principal"],
                                   self.seletores_produtos["descricao"]["alternativo"]]:
                        try:
                            desc_elem = await produto.query_selector(seletor)
                            if desc_elem:
                                descricao = await desc_elem.inner_text()
                                break
                        except:
                            continue
                    
                    # Se não encontrou descrição, tentar genéricos
                    if descricao == "N/A":
                        for desc_sel in ["[class*='description']", "[class*='details']", "p", "span"]:
                            try:
                                desc_elem = await produto.query_selector(desc_sel)
                                if desc_elem:
                                    texto = await desc_elem.inner_text()
                                    if len(texto) > 10 and not "R$" in texto and texto != nome:
                                        descricao = texto
                                        break
                            except:
                                continue
                    
                    # Coletar preço
                    preco = "N/A"
                    for seletor in [self.seletores_produtos["preco"]["principal"],
                                   self.seletores_produtos["preco"]["alternativo"]]:
                        try:
                            preco_elem = await produto.query_selector(seletor)
                            if preco_elem:
                                preco = await preco_elem.inner_text()
                                break
                        except:
                            continue
                    
                    # Se não encontrou preço, buscar por texto contendo R$
                    if preco == "N/A":
                        try:
                            texto_completo = await produto.inner_text()
                            if "R$" in texto_completo:
                                import re
                                match = re.search(r'R\$\s*(\d+[.,]\d{2})', texto_completo)
                                if match:
                                    preco = match.group(0)
                        except:
                            pass
                    
                    # Só adicionar se tiver pelo menos nome
                    if nome != "N/A" and len(nome) > 2:
                        dados_coletados.append({
                            "restaurant_id": restaurant_id,
                            "restaurant_name": restaurant_name,
                            "category": restaurant_category,
                            "nome": nome,
                            "descricao": descricao if descricao != "N/A" else None,
                            "preco": preco if preco != "N/A" else None
                        })
                        
                        if (i + 1) % 10 == 0:
                            print(f"{Fore.WHITE}   ✅ {i + 1} produtos processados...")
                    
                except Exception as e:
                    self.logger.debug(f"Erro ao processar produto {i+1}: {str(e)}")
                    continue
            
            print(f"{Fore.GREEN}   ✅ {len(dados_coletados)} produtos coletados!")
            return dados_coletados
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar produtos do restaurante {restaurant_name}: {str(e)}")
            print(f"{Fore.RED}❌ Erro no restaurante {restaurant_name}: {str(e)}")
            return []
    
    def _verificar_duplicata_produto(self, conn, nome_produto, restaurant_id, category):
        """Verificar se produto já existe no banco"""
        try:
            # Verificar por nome + restaurant_id + categoria
            result = conn.execute("""
                SELECT id FROM products 
                WHERE LOWER(TRIM(name)) = LOWER(TRIM(?)) 
                AND restaurant_id = ?
                AND LOWER(TRIM(category)) = LOWER(TRIM(?))
                LIMIT 1
            """, [nome_produto, restaurant_id, category]).fetchone()
            
            return result is not None
            
        except Exception as e:
            self.logger.debug(f"Erro ao verificar duplicata produto: {str(e)}")
            return False

    def salvar_produtos_no_banco(self, produtos):
        """Salvar produtos coletados no banco de dados (evitando duplicatas)"""
        try:
            self.logger.info("Salvando produtos no banco de dados")
            print(f"\n{Fore.CYAN}💾 Salvando no banco de dados (com verificação anti-duplicatas)...")
            
            conn = self.db_manager._get_connection()
            produtos_salvos = 0
            produtos_duplicados = 0
            produtos_erros = 0
            
            for i, produto in enumerate(produtos):
                try:
                    nome = produto["nome"]
                    restaurant_id = produto["restaurant_id"]
                    category = produto["category"]
                    
                    # NOVO: Verificar se já existe (anti-duplicatas)
                    if self._verificar_duplicata_produto(conn, nome, restaurant_id, category):
                        produtos_duplicados += 1
                        if produtos_duplicados <= 10:  # Mostrar apenas os primeiros 10
                            print(f"{Fore.YELLOW}   🔄 Duplicata: {nome} ({category}) (já existe)")
                        elif produtos_duplicados == 11:
                            print(f"{Fore.YELLOW}   🔄 ... (mais duplicatas encontradas)")
                        continue
                    
                    # Obter próximo ID
                    result = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM products").fetchone()
                    next_id = result[0]
                    
                    # Processar preço
                    preco_num = None
                    if produto["preco"]:
                        try:
                            # Extrair valor numérico (ex: "15.50" de "R$ 15,50")
                            preco_str = produto["preco"].replace("R$", "").replace(",", ".").strip()
                            preco_num = float(preco_str) if preco_str else None
                        except:
                            preco_num = None
                    
                    # Inserir novo produto
                    conn.execute("""
                        INSERT INTO products (id, restaurant_id, restaurant_name, category, name, description, price, scraped_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, [next_id, restaurant_id, produto["restaurant_name"], 
                          category, nome, produto["descricao"], preco_num])
                    
                    produtos_salvos += 1
                    
                    # Log progresso a cada 100 produtos
                    if produtos_salvos % 100 == 0:
                        print(f"{Fore.GREEN}   ✅ {produtos_salvos} novos produtos salvos...")
                    
                except Exception as e:
                    produtos_erros += 1
                    self.logger.error(f"Erro ao salvar produto {produto.get('nome', 'N/A')}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            # Relatório final detalhado
            total_processados = len(produtos)
            print(f"\n{Fore.CYAN}📊 RELATÓRIO FINAL:")
            print(f"{Fore.GREEN}   ✅ Novos produtos salvos: {produtos_salvos}")
            print(f"{Fore.YELLOW}   🔄 Duplicatas ignoradas: {produtos_duplicados}")
            if produtos_erros > 0:
                print(f"{Fore.RED}   ❌ Erros encontrados: {produtos_erros}")
            print(f"{Fore.WHITE}   📋 Total processados: {total_processados}")
            
            eficiencia = (produtos_salvos / total_processados * 100) if total_processados > 0 else 0
            print(f"{Fore.CYAN}   📈 Taxa de novos dados: {eficiencia:.1f}%")
            
            self.logger.info(f"Produtos salvos: {produtos_salvos}/{total_processados} | Duplicatas: {produtos_duplicados}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar produtos no banco: {str(e)}")
            print(f"{Fore.RED}❌ Erro ao salvar: {str(e)}")
            return False
    
    def exibir_menu_selecao_produtos(self):
        """Exibir menu para seleção de coleta de produtos"""
        restaurantes_por_categoria = self.obter_restaurantes_por_categoria()
        
        if not restaurantes_por_categoria:
            print(f"{Fore.RED}❌ Nenhum restaurante encontrado no banco de dados!")
            print(f"{Fore.YELLOW}💡 Execute primeiro o Scraper de Restaurantes (opção 1 → 2)")
            return None, None
        
        print(f"\n{Fore.CYAN}🍽️ COLETA DE PRODUTOS:")
        print(f"{Fore.MAGENTA}{'─'*60}")
        print(f"{Fore.WHITE}[1] Coletar produtos de um restaurante específico")
        print(f"{Fore.WHITE}[2] Coletar produtos de uma categoria específica")
        print(f"{Fore.WHITE}[3] Coletar produtos de todos os restaurantes")
        print(f"{Fore.RED}[0] Voltar")
        
        while True:
            try:
                escolha = input(f"\n{Fore.YELLOW}➤ Escolha uma opção: ").strip()
                
                if escolha == '0':
                    return None, None
                elif escolha == '1':
                    return self._selecionar_restaurante_especifico()
                elif escolha == '2':
                    return self._selecionar_categoria_especifica(restaurantes_por_categoria)
                elif escolha == '3':
                    todos_restaurantes = self.obter_todos_restaurantes()
                    return todos_restaurantes, "todos"
                else:
                    print(f"{Fore.RED}❌ Opção inválida!")
                    
            except ValueError:
                print(f"{Fore.RED}❌ Digite apenas números!")
    
    def _selecionar_restaurante_especifico(self):
        """Selecionar um restaurante específico"""
        todos_restaurantes = self.obter_todos_restaurantes()
        
        print(f"\n{Fore.CYAN}🍴 RESTAURANTES DISPONÍVEIS:")
        print(f"{Fore.MAGENTA}{'─'*60}")
        
        for i, rest in enumerate(todos_restaurantes, 1):
            print(f"{Fore.WHITE}[{i:2d}] {rest['nome']} ({rest['categoria']})")
        
        print(f"{Fore.RED}[0] Voltar")
        
        while True:
            try:
                escolha = int(input(f"\n{Fore.YELLOW}➤ Escolha um restaurante: "))
                
                if escolha == 0:
                    return None, None
                elif 1 <= escolha <= len(todos_restaurantes):
                    restaurante = todos_restaurantes[escolha - 1]
                    return [restaurante], "especifico"
                else:
                    print(f"{Fore.RED}❌ Número inválido!")
                    
            except ValueError:
                print(f"{Fore.RED}❌ Digite apenas números!")
    
    def _selecionar_categoria_especifica(self, restaurantes_por_categoria):
        """Selecionar uma categoria específica"""
        categorias = list(restaurantes_por_categoria.keys())
        
        print(f"\n{Fore.CYAN}📂 CATEGORIAS DISPONÍVEIS:")
        print(f"{Fore.MAGENTA}{'─'*60}")
        
        for i, categoria in enumerate(categorias, 1):
            count = len(restaurantes_por_categoria[categoria])
            print(f"{Fore.WHITE}[{i:2d}] {categoria} ({count} restaurantes)")
        
        print(f"{Fore.RED}[0] Voltar")
        
        while True:
            try:
                escolha = int(input(f"\n{Fore.YELLOW}➤ Escolha uma categoria: "))
                
                if escolha == 0:
                    return None, None
                elif 1 <= escolha <= len(categorias):
                    categoria_selecionada = categorias[escolha - 1]
                    restaurantes = restaurantes_por_categoria[categoria_selecionada]
                    # Converter para formato padrão
                    restaurantes_formatados = []
                    for rest in restaurantes:
                        restaurantes_formatados.append({
                            "id": rest["id"],
                            "nome": rest["nome"], 
                            "categoria": categoria_selecionada,
                            "link": rest["link"]
                        })
                    return restaurantes_formatados, "categoria"
                else:
                    print(f"{Fore.RED}❌ Número inválido!")
                    
            except ValueError:
                print(f"{Fore.RED}❌ Digite apenas números!")
    
    def extract_products_data(self):
        """Extrair dados de produtos dos restaurantes"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║           SCRAPER DE PRODUTOS DOS RESTAURANTES          ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        # Criar tabela se não existir
        if not self._criar_tabela_produtos():
            print(f"{Fore.RED}❌ Erro ao criar tabela de produtos")
            return
        
        # Menu de seleção
        restaurantes_selecionados, tipo_selecao = self.exibir_menu_selecao_produtos()
        
        if not restaurantes_selecionados:
            return
        
        print(f"\n{Fore.CYAN}📊 Iniciando coleta de produtos...")
        print(f"{Fore.YELLOW}📍 Cidade configurada: {self.config_manager.get_default_city()}")
        
        if tipo_selecao == "todos":
            print(f"{Fore.WHITE}🎯 Coletando produtos de TODOS os {len(restaurantes_selecionados)} restaurantes")
        elif tipo_selecao == "categoria":
            categoria = restaurantes_selecionados[0]['categoria']
            print(f"{Fore.WHITE}🎯 Coletando produtos da categoria: {categoria}")
            print(f"{Fore.WHITE}   Restaurantes: {len(restaurantes_selecionados)}")
        else:
            print(f"{Fore.WHITE}🎯 Coletando produtos do restaurante: {restaurantes_selecionados[0]['nome']}")
        
        # Executar scraping
        asyncio.run(self.executar_scraping_produtos(restaurantes_selecionados))
    
    async def executar_scraping_produtos(self, restaurantes):
        """Executar scraping de produtos"""
        tempo_inicio = time.time()
        todos_produtos = []
        
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
                # ETAPA 1: Coletar produtos de cada restaurante
                for i, restaurante in enumerate(restaurantes, 1):
                    print(f"\n{Fore.MAGENTA}🍴 Restaurante {i}/{len(restaurantes)}: {restaurante['nome']}")
                    
                    # Navegar para restaurante
                    sucesso_navegacao = await self.navegar_para_restaurante(page, restaurante)
                    
                    if not sucesso_navegacao:
                        print(f"{Fore.RED}❌ Falha ao navegar para {restaurante['nome']}")
                        continue
                    
                    # Coletar produtos
                    produtos_restaurante = await self.coletar_produtos_restaurante(
                        page, restaurante['id'], restaurante['nome'], restaurante['categoria']
                    )
                    
                    todos_produtos.extend(produtos_restaurante)
                    
                    print(f"{Fore.GREEN}✅ {len(produtos_restaurante)} produtos coletados")
                    
                    # Pausa entre restaurantes
                    if i < len(restaurantes):
                        await asyncio.sleep(2)
                
                # ETAPA 2: Salvar no banco
                if todos_produtos:
                    self.salvar_produtos_no_banco(todos_produtos)
                    
                    # Relatório final
                    tempo_total = time.time() - tempo_inicio
                    performance = len(todos_produtos) / tempo_total if tempo_total > 0 else 0
                    
                    print(f"\n{Fore.YELLOW}📊 RESUMO DA COLETA:")
                    print(f"{Fore.WHITE}   ⏱️ Tempo total: {tempo_total:.2f}s")
                    print(f"{Fore.WHITE}   🍴 Restaurantes processados: {len(restaurantes)}")
                    print(f"{Fore.WHITE}   🍽️ Produtos coletados: {len(todos_produtos)}")
                    print(f"{Fore.WHITE}   🚀 Performance: {performance:.1f} produtos/segundo")
                    print(f"{Fore.WHITE}   💾 Status: Salvo no banco de dados")
                    
                    # Estatísticas por restaurante
                    print(f"\n{Fore.CYAN}📋 PRODUTOS POR RESTAURANTE:")
                    from collections import Counter
                    contadores = Counter(p['restaurant_name'] for p in todos_produtos)
                    
                    for restaurante, count in contadores.items():
                        print(f"{Fore.WHITE}   • {restaurante}: {count} produtos")
                    
                    self.logger.info(f"Scraping de produtos concluído: {len(todos_produtos)} produtos em {tempo_total:.2f}s")
                else:
                    print(f"\n{Fore.YELLOW}⚠️ Nenhum produto foi coletado")
                
            except Exception as e:
                self.logger.error(f"Erro durante scraping de produtos: {str(e)}")
                print(f"\n{Fore.RED}❌ Erro durante scraping: {str(e)}")
                
            finally:
                await browser.close()
                print(f"\n{Fore.CYAN}🔒 Navegador fechado")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    # Método de compatibilidade com a estrutura existente
    def scrape_menu(self):
        """Método de compatibilidade - chamar extract_products_data"""
        self.extract_products_data()