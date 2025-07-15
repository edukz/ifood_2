"""
Scraper de restaurantes por categoria
"""
import asyncio
import time
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from colorama import Fore, Style
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager
from src.config.config_manager import ConfigManager

class RestaurantsScraper:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
        self.config_manager = ConfigManager()
        self.base_url = "https://www.ifood.com.br"
        self.cidade_busca = "Birigui"
        
        # Configurações otimizadas (herdadas do categories_scraper)
        self.config_otimizado = {
            "campo_endereco": "input[placeholder*='Endereço de entrega']",
            "dropdown_seletor": ".address-search-list",
            "wait_until": "domcontentloaded",
            "timeout_campo": 5000,
            "timeout_dropdown": 5000,
            "estrategia_preenchimento": "fill_direto"
        }
        
        # Seletores otimizados para restaurantes (baseados nos testes)
        self.seletores_restaurantes = {
            "container": "#__next > div:nth-child(1) > main > div > section > article > section > div > div",
            "item": "> div",
            "nome": ".merchant-v2__header span",
            "info": ".merchant-v2__info",
            "entrega": ".merchant-v2__content > div > span:nth-child(2)"
        }
        
        # Configurações para carregamento de mais restaurantes
        self.config_scroll = {
            "max_scrolls": 15,  # Máximo de scrolls (aumentado para coletar mais)
            "timeout_scroll": 2,  # Segundos entre scrolls
            "max_tentativas_sem_novos": 3  # Parar após X tentativas sem novos restaurantes
        }
    
    async def preencher_localizacao_otimizado(self, page):
        """Preencher localização (otimizado)"""
        tempo_inicio = time.time()
        
        try:
            self.logger.info("Iniciando preenchimento de localização")
            print(f"\n{Fore.CYAN}📍 Preenchendo localização...")
            
            # Aguardar campo aparecer
            campo_endereco = await page.wait_for_selector(
                self.config_otimizado['campo_endereco'], 
                timeout=self.config_otimizado['timeout_campo']
            )
            
            # Preencher
            await campo_endereco.fill(self.cidade_busca)
            print(f"{Fore.WHITE}   ✅ '{self.cidade_busca}' digitado")
            
            # Aguardar dropdown
            await page.wait_for_selector(
                self.config_otimizado['dropdown_seletor'],
                timeout=self.config_otimizado['timeout_dropdown']
            )
            
            # Buscar e selecionar opção
            opcoes = await page.query_selector_all(f"{self.config_otimizado['dropdown_seletor']} li")
            if not opcoes:
                opcoes = await page.query_selector_all(f"{self.config_otimizado['dropdown_seletor']} .option")
            
            melhor_opcao_encontrada = False
            
            if opcoes:
                for opcao in opcoes:
                    try:
                        texto_opcao = await opcao.inner_text()
                        if ("Birigui" in texto_opcao and "SP" in texto_opcao and 
                            ("Brasil" in texto_opcao or "Brazil" in texto_opcao)):
                            await opcao.click()
                            print(f"{Fore.WHITE}   ✅ Opção específica selecionada")
                            melhor_opcao_encontrada = True
                            break
                    except:
                        continue
                
                if not melhor_opcao_encontrada:
                    await opcoes[0].click()
                    melhor_opcao_encontrada = True
            
            if not melhor_opcao_encontrada:
                await page.keyboard.press("ArrowDown")
                await asyncio.sleep(0.3)
                await page.keyboard.press("Enter")
            
            await asyncio.sleep(2)
            
            # Confirmar localização
            try:
                await page.click("button:has-text('Confirmar localização')", timeout=3000)
            except:
                try:
                    await page.click("button:has-text('Confirmar')", timeout=3000)
                except:
                    pass
            
            # Salvar endereço
            try:
                await page.click("button:has-text('Salvar endereço')", timeout=2000)
                print(f"{Fore.WHITE}   ✅ Endereço salvo")
            except:
                pass
            
            await asyncio.sleep(2)
            
            tempo_total = time.time() - tempo_inicio
            print(f"{Fore.GREEN}✅ Localização configurada em {tempo_total:.2f}s!")
            return True
            
        except Exception as e:
            tempo_total = time.time() - tempo_inicio
            self.logger.error(f"Erro ao preencher localização: {str(e)}")
            print(f"{Fore.RED}❌ Erro na localização ({tempo_total:.2f}s): {str(e)}")
            return False
    
    async def tentar_carregar_mais_conteudo(self, page, scroll_num):
        """Tentar diferentes estratégias para carregar mais conteúdo"""
        try:
            # Estratégia 1: Botão "Ver mais" ou "Carregar mais"
            botoes_carregar = [
                "button:has-text('Ver mais')",
                "button:has-text('Carregar mais')", 
                "button:has-text('Mostrar mais')",
                "[data-test-id='load-more']",
                ".load-more-button",
                "button[aria-label*='mais']"
            ]
            
            for seletor in botoes_carregar:
                try:
                    botao = await page.query_selector(seletor)
                    if botao:
                        await botao.click()
                        print(f"{Fore.CYAN}   🔘 Botão encontrado e clicado: {seletor}")
                        await asyncio.sleep(3)
                        return True
                except:
                    continue
            
            # Estratégia 2: Scroll gradual (a cada 3 scrolls)
            if scroll_num % 3 == 0:
                await page.evaluate("window.scrollBy(0, window.innerHeight / 2)")
                await asyncio.sleep(1)
            
            # Estratégia 3: Simular hover em elementos para trigger lazy loading
            if scroll_num % 5 == 0:
                try:
                    ultimo_restaurante = await page.query_selector(f"{self.seletores_restaurantes['container']} {self.seletores_restaurantes['item']}:last-child")
                    if ultimo_restaurante:
                        await ultimo_restaurante.hover()
                        await asyncio.sleep(0.5)
                except:
                    pass
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Erro nas estratégias de carregamento: {str(e)}")
            return False
    
    async def carregar_mais_restaurantes_com_scroll(self, page):
        """Fazer scroll automático para carregar mais restaurantes"""
        try:
            restaurantes_iniciais = len(await page.query_selector_all(
                f"{self.seletores_restaurantes['container']} {self.seletores_restaurantes['item']}"
            ))
            
            print(f"{Fore.WHITE}   📊 Restaurantes iniciais: {restaurantes_iniciais}")
            
            scrolls_realizados = 0
            max_scrolls = self.config_scroll["max_scrolls"]
            sem_novos_restaurantes = 0
            max_tentativas = self.config_scroll["max_tentativas_sem_novos"]
            
            while scrolls_realizados < max_scrolls and sem_novos_restaurantes < max_tentativas:
                # Fazer scroll para baixo
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(self.config_scroll["timeout_scroll"])
                
                # Verificar se carregaram novos restaurantes
                restaurantes_atuais = len(await page.query_selector_all(
                    f"{self.seletores_restaurantes['container']} {self.seletores_restaurantes['item']}"
                ))
                
                if restaurantes_atuais > restaurantes_iniciais:
                    print(f"{Fore.GREEN}   ✅ +{restaurantes_atuais - restaurantes_iniciais} restaurantes carregados (scroll {scrolls_realizados + 1})")
                    restaurantes_iniciais = restaurantes_atuais
                    sem_novos_restaurantes = 0
                else:
                    sem_novos_restaurantes += 1
                    print(f"{Fore.YELLOW}   ⏳ Aguardando carregamento... ({sem_novos_restaurantes}/3)")
                
                scrolls_realizados += 1
                
                # Estratégias para carregar mais conteúdo
                await self.tentar_carregar_mais_conteudo(page, scrolls_realizados)
            
            restaurantes_finais = len(await page.query_selector_all(
                f"{self.seletores_restaurantes['container']} {self.seletores_restaurantes['item']}"
            ))
            
            print(f"{Fore.GREEN}   🎯 Total carregado: {restaurantes_finais} restaurantes ({scrolls_realizados} scrolls)")
            return restaurantes_finais
            
        except Exception as e:
            self.logger.error(f"Erro no scroll automático: {str(e)}")
            print(f"{Fore.RED}   ❌ Erro no scroll: {str(e)}")
            return 0
    
    async def coletar_restaurantes_categoria(self, page, categoria_nome, categoria_url):
        """Coletar restaurantes de uma categoria específica"""
        try:
            self.logger.info(f"Coletando restaurantes da categoria: {categoria_nome}")
            print(f"\n{Fore.CYAN}🍴 Coletando restaurantes: {categoria_nome}")
            
            # Navegar para categoria
            await page.goto(categoria_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # Aguardar container de restaurantes
            container = await page.wait_for_selector(
                self.seletores_restaurantes["container"], 
                timeout=10000
            )
            
            if not container:
                print(f"{Fore.YELLOW}   ⚠️ Container de restaurantes não encontrado")
                return []
            
            # NOVO: Fazer scroll automático para carregar mais restaurantes
            print(f"{Fore.CYAN}   🔄 Carregando mais restaurantes com scroll...")
            await self.carregar_mais_restaurantes_com_scroll(page)
            
            # Buscar todos os restaurantes após o scroll
            restaurantes = await page.query_selector_all(
                f"{self.seletores_restaurantes['container']} {self.seletores_restaurantes['item']}"
            )
            
            print(f"{Fore.WHITE}   📊 {len(restaurantes)} restaurantes encontrados")
            
            dados_coletados = []
            
            for i, restaurante in enumerate(restaurantes):
                try:
                    # Coletar nome
                    nome_element = await restaurante.query_selector(self.seletores_restaurantes["nome"])
                    nome = await nome_element.inner_text() if nome_element else "N/A"
                    
                    # Coletar info (rating • tipo • km)
                    info_element = await restaurante.query_selector(self.seletores_restaurantes["info"])
                    info_text = await info_element.inner_text() if info_element else "N/A"
                    
                    # Separar info por "•"
                    info_parts = [part.strip() for part in info_text.split("•")] if info_text != "N/A" else []
                    rating = info_parts[0] if len(info_parts) > 0 else "N/A"
                    tipo_comida = info_parts[1] if len(info_parts) > 1 else "N/A"
                    distancia = info_parts[2] if len(info_parts) > 2 else "N/A"
                    
                    # Coletar taxa de entrega
                    entrega_element = await restaurante.query_selector(self.seletores_restaurantes["entrega"])
                    taxa_entrega = await entrega_element.inner_text() if entrega_element else "N/A"
                    
                    # Processar taxa de entrega (grátis = 0)
                    if taxa_entrega.lower() == "grátis":
                        taxa_entrega = "0"
                    
                    dados_coletados.append({
                        "nome": nome,
                        "categoria": categoria_nome,
                        "rating": rating,
                        "tipo_comida": tipo_comida,
                        "distancia": distancia,
                        "taxa_entrega": taxa_entrega,
                        "categoria_url": categoria_url
                    })
                    
                    if (i + 1) % 10 == 0:
                        print(f"{Fore.WHITE}   ✅ {i + 1} restaurantes processados...")
                    
                except Exception as e:
                    self.logger.debug(f"Erro ao processar restaurante {i+1}: {str(e)}")
                    continue
            
            print(f"{Fore.GREEN}   ✅ {len(dados_coletados)} restaurantes coletados!")
            return dados_coletados
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar restaurantes da categoria {categoria_nome}: {str(e)}")
            print(f"{Fore.RED}❌ Erro na categoria {categoria_nome}: {str(e)}")
            return []
    
    def salvar_restaurantes_no_banco(self, restaurantes):
        """Salvar restaurantes coletados no banco de dados"""
        try:
            self.logger.info("Salvando restaurantes no banco de dados")
            print(f"\n{Fore.CYAN}💾 Salvando no banco de dados...")
            
            conn = self.db_manager._get_connection()
            
            # A tabela restaurants já existe, não precisa criar
            
            restaurantes_salvos = 0
            
            for i, rest in enumerate(restaurantes):
                try:
                    # Obter próximo ID
                    result = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM restaurants").fetchone()
                    next_id = result[0] + i
                    
                    # Processar dados para tipos corretos
                    rating_num = None
                    if rest["rating"] != "N/A":
                        try:
                            # Extrair apenas número da rating (ex: "4.5" de "4.5 ★")
                            rating_str = rest["rating"].replace("★", "").strip()
                            rating_num = float(rating_str) if rating_str else None
                        except:
                            rating_num = None
                    
                    delivery_fee_num = None
                    if rest["taxa_entrega"] != "N/A":
                        try:
                            if rest["taxa_entrega"] == "0" or rest["taxa_entrega"].lower() == "grátis":
                                delivery_fee_num = 0.0
                            else:
                                # Extrair valor numérico (ex: "3.50" de "R$ 3,50")
                                fee_str = rest["taxa_entrega"].replace("R$", "").replace(",", ".").strip()
                                delivery_fee_num = float(fee_str) if fee_str else None
                        except:
                            delivery_fee_num = None
                    
                    conn.execute("""
                        INSERT INTO restaurants (id, name, category, rating, delivery_fee, city, scraped_at) 
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, [next_id, rest["nome"], rest["categoria"], rating_num, 
                          delivery_fee_num, "Birigui"])
                    
                    restaurantes_salvos += 1
                    
                except Exception as e:
                    self.logger.error(f"Erro ao salvar restaurante {rest['nome']}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            print(f"{Fore.GREEN}✅ {restaurantes_salvos} restaurantes salvos no banco!")
            self.logger.info(f"Restaurantes salvos: {restaurantes_salvos}/{len(restaurantes)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar no banco: {str(e)}")
            print(f"{Fore.RED}❌ Erro ao salvar: {str(e)}")
            return False
    
    def obter_categorias_disponiveis(self):
        """Obter categorias disponíveis no banco de dados"""
        try:
            conn = self.db_manager._get_connection()
            categorias = conn.execute("SELECT categorias, links FROM categories ORDER BY categorias").fetchall()
            conn.close()
            
            return [{"nome": cat[0], "url": cat[1]} for cat in categorias]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter categorias: {str(e)}")
            return []
    
    def configurar_quantidade_coleta(self):
        """Configurar quantos restaurantes coletar"""
        print(f"\n{Fore.CYAN}⚙️ CONFIGURAÇÃO DE COLETA:")
        print(f"{Fore.WHITE}Atual: máximo {self.config_scroll['max_scrolls']} scrolls")
        print()
        print(f"{Fore.YELLOW}[1] Coleta Rápida   (5 scrolls  - ~50-100 restaurantes)")
        print(f"{Fore.YELLOW}[2] Coleta Média    (15 scrolls - ~150-300 restaurantes)")  
        print(f"{Fore.YELLOW}[3] Coleta Completa (25 scrolls - ~250-500+ restaurantes)")
        print(f"{Fore.YELLOW}[4] Personalizada   (definir quantidade)")
        print(f"{Fore.RED}[0] Manter atual")
        
        while True:
            try:
                escolha = input(f"\n{Fore.YELLOW}➤ Escolha o modo de coleta: ").strip()
                
                if escolha == '0':
                    return
                elif escolha == '1':
                    self.config_scroll["max_scrolls"] = 5
                    print(f"{Fore.GREEN}✅ Configurado para coleta rápida (5 scrolls)")
                    break
                elif escolha == '2':
                    self.config_scroll["max_scrolls"] = 15
                    print(f"{Fore.GREEN}✅ Configurado para coleta média (15 scrolls)")
                    break
                elif escolha == '3':
                    self.config_scroll["max_scrolls"] = 25
                    print(f"{Fore.GREEN}✅ Configurado para coleta completa (25 scrolls)")
                    break
                elif escolha == '4':
                    scrolls = int(input(f"{Fore.CYAN}Digite o número de scrolls (1-50): "))
                    if 1 <= scrolls <= 50:
                        self.config_scroll["max_scrolls"] = scrolls
                        print(f"{Fore.GREEN}✅ Configurado para {scrolls} scrolls")
                        break
                    else:
                        print(f"{Fore.RED}❌ Digite um número entre 1 e 50")
                else:
                    print(f"{Fore.RED}❌ Opção inválida!")
                    
            except ValueError:
                print(f"{Fore.RED}❌ Digite apenas números!")
    
    def exibir_menu_selecao_categorias(self):
        """Exibir menu para seleção de categorias"""
        categorias = self.obter_categorias_disponiveis()
        
        if not categorias:
            print(f"{Fore.RED}❌ Nenhuma categoria encontrada no banco de dados!")
            print(f"{Fore.YELLOW}💡 Execute primeiro o Scraper de Categorias (opção 1 → 1)")
            return None, None
        
        print(f"\n{Fore.CYAN}📂 CATEGORIAS DISPONÍVEIS:")
        print(f"{Fore.MAGENTA}{'─'*60}")
        
        for i, cat in enumerate(categorias, 1):
            print(f"{Fore.WHITE}[{i:2d}] {cat['nome']}")
        
        print(f"{Fore.MAGENTA}{'─'*60}")
        print(f"{Fore.GREEN}[99] Todas as categorias")
        print(f"{Fore.YELLOW}[98] ⚙️ Configurar quantidade de coleta")
        print(f"{Fore.RED}[0 ] Voltar")
        
        while True:
            try:
                escolha = input(f"\n{Fore.YELLOW}➤ Escolha as categorias (ex: 1,3,5 ou 99 para todas): ").strip()
                
                if escolha == '0':
                    return None, None
                elif escolha == '98':
                    self.configurar_quantidade_coleta()
                    continue  # Volta para o menu de categorias
                elif escolha == '99':
                    return categorias, "todas"
                else:
                    indices = [int(x.strip()) for x in escolha.split(',')]
                    categorias_selecionadas = []
                    
                    for idx in indices:
                        if 1 <= idx <= len(categorias):
                            categorias_selecionadas.append(categorias[idx-1])
                    
                    if categorias_selecionadas:
                        return categorias_selecionadas, "selecionadas"
                    else:
                        print(f"{Fore.RED}❌ Números inválidos! Digite números entre 1 e {len(categorias)}")
                        
            except ValueError:
                print(f"{Fore.RED}❌ Formato inválido! Use vírgulas para separar (ex: 1,3,5)")
    
    def extract_restaurants_data(self):
        """Extrair dados de restaurantes por categoria"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║        SCRAPER DE RESTAURANTES POR CATEGORIA            ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        # Menu de seleção
        categorias_selecionadas, tipo_selecao = self.exibir_menu_selecao_categorias()
        
        if not categorias_selecionadas:
            return
        
        print(f"\n{Fore.CYAN}📊 Iniciando coleta de restaurantes...")
        
        if tipo_selecao == "todas":
            print(f"{Fore.WHITE}🎯 Coletando TODAS as {len(categorias_selecionadas)} categorias")
        else:
            print(f"{Fore.WHITE}🎯 Coletando {len(categorias_selecionadas)} categorias selecionadas:")
            for cat in categorias_selecionadas:
                print(f"{Fore.WHITE}   • {cat['nome']}")
        
        # Executar scraping
        asyncio.run(self.executar_scraping_restaurantes(categorias_selecionadas))
    
    async def executar_scraping_restaurantes(self, categorias):
        """Executar scraping de restaurantes"""
        tempo_inicio = time.time()
        todos_restaurantes = []
        
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
                # ETAPA 1: Acessar iFood e configurar localização
                print(f"\n{Fore.CYAN}🌐 Acessando iFood...")
                await page.goto(self.base_url, wait_until="domcontentloaded")
                
                sucesso_localizacao = await self.preencher_localizacao_otimizado(page)
                if not sucesso_localizacao:
                    print(f"{Fore.RED}❌ Falha na configuração de localização")
                    return
                
                # ETAPA 2: Coletar restaurantes de cada categoria
                for i, categoria in enumerate(categorias, 1):
                    print(f"\n{Fore.MAGENTA}📂 Categoria {i}/{len(categorias)}: {categoria['nome']}")
                    
                    restaurantes_categoria = await self.coletar_restaurantes_categoria(
                        page, categoria['nome'], categoria['url']
                    )
                    
                    todos_restaurantes.extend(restaurantes_categoria)
                    
                    print(f"{Fore.GREEN}✅ {len(restaurantes_categoria)} restaurantes coletados")
                    
                    # Pausa entre categorias
                    if i < len(categorias):
                        await asyncio.sleep(2)
                
                # ETAPA 3: Salvar no banco
                if todos_restaurantes:
                    self.salvar_restaurantes_no_banco(todos_restaurantes)
                    
                    # Relatório final
                    tempo_total = time.time() - tempo_inicio
                    performance = len(todos_restaurantes) / tempo_total if tempo_total > 0 else 0
                    
                    print(f"\n{Fore.YELLOW}📊 RESUMO DA COLETA:")
                    print(f"{Fore.WHITE}   ⏱️ Tempo total: {tempo_total:.2f}s")
                    print(f"{Fore.WHITE}   📂 Categorias processadas: {len(categorias)}")
                    print(f"{Fore.WHITE}   🍴 Restaurantes coletados: {len(todos_restaurantes)}")
                    print(f"{Fore.WHITE}   🚀 Performance: {performance:.1f} restaurantes/segundo")
                    print(f"{Fore.WHITE}   💾 Status: Salvo no banco de dados")
                    
                    # Estatísticas por categoria
                    print(f"\n{Fore.CYAN}📋 RESTAURANTES POR CATEGORIA:")
                    from collections import Counter
                    contadores = Counter(r['categoria'] for r in todos_restaurantes)
                    
                    for categoria, count in contadores.items():
                        print(f"{Fore.WHITE}   • {categoria}: {count} restaurantes")
                    
                    self.logger.info(f"Scraping de restaurantes concluído: {len(todos_restaurantes)} restaurantes em {tempo_total:.2f}s")
                else:
                    print(f"\n{Fore.YELLOW}⚠️ Nenhum restaurante foi coletado")
                
            except Exception as e:
                self.logger.error(f"Erro durante scraping de restaurantes: {str(e)}")
                print(f"\n{Fore.RED}❌ Erro durante scraping: {str(e)}")
                
            finally:
                await browser.close()
                print(f"\n{Fore.CYAN}🔒 Navegador fechado")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")