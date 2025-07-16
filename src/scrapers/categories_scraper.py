"""
Scraper de categorias
"""
import asyncio
import time
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from colorama import Fore, Style
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager
from src.config.config_manager import ConfigManager

class CategoriesScraper:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
        self.config_manager = ConfigManager()
        self.base_url = "https://www.ifood.com.br"
        self.cidade_busca = self.config_manager.get_default_city()
        self.endereco_completo = f"{self.cidade_busca}, SP, Brasil"
        
        # Configurações otimizadas baseadas nos testes de performance + melhorias do teste_localizacao.py
        self.config_otimizado = {
            "campo_endereco": "input[placeholder*='Endereço de entrega']",
            "dropdown_seletor": ".address-search-list",
            "wait_until": "domcontentloaded",  # 0.51s vs 5.42s
            "timeout_campo": 5000,
            "timeout_dropdown": 5000,
            "estrategia_preenchimento": "fill_direto",
            "busca_ampla_habilitada": True,  # Nova: busca ampla por elementos
            "filtro_sp_brasil": True,  # Nova: filtro inteligente por SP + Brasil
            "teclado_prioritario": True  # Nova: priorizar teclado quando necessário
        }
    
    async def preencher_localizacao(self, page):
        """Preencher a localização no modal do iFood - VERSÃO OTIMIZADA"""
        tempo_inicio = time.time()
        
        try:
            self.logger.info("Iniciando preenchimento de localização otimizado")
            print(f"\n{Fore.CYAN}🗺️  Preenchendo localização (otimizado)...")
            
            # Aguardar campo aparecer com configuração otimizada
            campo_endereco = await page.wait_for_selector(
                self.config_otimizado['campo_endereco'], 
                timeout=self.config_otimizado['timeout_campo']
            )
            self.logger.debug(f"Campo encontrado: {self.config_otimizado['campo_endereco']}")
            print(f"{Fore.WHITE}   ✅ Campo de endereço encontrado")
            
            # Preencher com estratégia otimizada
            await campo_endereco.fill(self.cidade_busca)
            self.logger.info(f"Cidade preenchida: {self.cidade_busca}")
            print(f"{Fore.WHITE}   ✅ '{self.cidade_busca}' digitado")
            
            # Aguardar dropdown aparecer com configuração otimizada
            print(f"{Fore.WHITE}   ⏳ Aguardando opções...")
            dropdown = await page.wait_for_selector(
                self.config_otimizado['dropdown_seletor'],
                timeout=self.config_otimizado['timeout_dropdown']
            )
            
            # BUSCA AMPLA por opções (estratégia do teste_localizacao.py)
            opcoes = await page.query_selector_all(f"{self.config_otimizado['dropdown_seletor']} li")
            if not opcoes:
                opcoes = await page.query_selector_all(f"{self.config_otimizado['dropdown_seletor']} .option")
            if not opcoes:
                # Busca ampla por qualquer elemento que contenha a cidade configurada
                print(f"{Fore.WHITE}   🔍 Buscando elementos com '{self.cidade_busca}'...")
                todos_elementos = await page.query_selector_all("*")
                opcoes_cidade = []
                
                for elemento in todos_elementos:
                    try:
                        texto = await elemento.inner_text()
                        if (texto and self.cidade_busca in texto and 
                            await elemento.is_visible() and 
                            len(texto.strip()) < 100):  # Evitar textos muito longos
                            opcoes_cidade.append(elemento)
                            self.logger.debug(f"Elemento {self.cidade_busca} encontrado: {texto.strip()}")
                    except:
                        continue
                
                if opcoes_cidade:
                    opcoes = opcoes_cidade
                    print(f"{Fore.WHITE}   ✅ {len(opcoes_cidade)} elementos com '{self.cidade_busca}' encontrados")
            
            self.logger.info(f"Dropdown encontrado: {len(opcoes)} opções")
            print(f"{Fore.WHITE}   ✅ {len(opcoes)} opções encontradas")
            
            # ESTRATÉGIA OTIMIZADA: Busca inteligente + teclado prioritário
            melhor_opcao_encontrada = False
            
            if opcoes:
                # Buscar opção específica com a cidade configurada, SP e Brasil
                for i, opcao in enumerate(opcoes):
                    try:
                        texto_opcao = await opcao.inner_text()
                        if (self.cidade_busca in texto_opcao and 
                            "SP" in texto_opcao and 
                            ("Brasil" in texto_opcao or "Brazil" in texto_opcao)):
                            await opcao.click()
                            self.logger.debug(f"Opção específica selecionada: {texto_opcao}")
                            print(f"{Fore.WHITE}   ✅ Opção específica selecionada: {texto_opcao}")
                            melhor_opcao_encontrada = True
                            break
                    except:
                        continue
                
                # Se não encontrou opção específica, usar primeira disponível
                if not melhor_opcao_encontrada:
                    await opcoes[0].click()
                    self.logger.debug("Primeira opção selecionada")
                    print(f"{Fore.WHITE}   ✅ Primeira opção selecionada")
                    melhor_opcao_encontrada = True
            
            # Fallback: estratégia de teclado (mais confiável)
            if not melhor_opcao_encontrada:
                print(f"{Fore.WHITE}   🎹 Usando estratégia de teclado...")
                await page.keyboard.press("ArrowDown")
                await asyncio.sleep(0.3)
                await page.keyboard.press("Enter")
                self.logger.debug("Seleção via teclado")
                print(f"{Fore.WHITE}   ✅ Seleção via teclado")
            
            await asyncio.sleep(2)
            
            # Confirmar localização
            try:
                await page.click("button:has-text('Confirmar localização')", timeout=3000)
                print(f"{Fore.WHITE}   ✅ Localização confirmada")
            except:
                try:
                    await page.click("button:has-text('Confirmar')", timeout=3000)
                    print(f"{Fore.WHITE}   ✅ Confirmação alternativa")
                except:
                    self.logger.debug("Botão confirmar não encontrado")
            
            # Salvar endereço se aparecer
            try:
                await page.click("button:has-text('Salvar endereço')", timeout=2000)
                print(f"{Fore.WHITE}   ✅ Endereço salvo")
            except:
                self.logger.debug("Botão salvar não encontrado")
            
            await asyncio.sleep(2)
            
            # ESTRATEGIA OTIMIZADA para navegar para "Restaurantes"
            restaurantes_encontrado = await self.navegar_para_restaurantes_otimizado(page)
            
            if not restaurantes_encontrado:
                self.logger.warning("Falha ao navegar para restaurantes, mas continuando...")
                print(f"{Fore.YELLOW}   ⚠️  Navegação para 'Restaurantes' falhou, continuando...")
            
            tempo_total = time.time() - tempo_inicio
            self.logger.info(f"Localização preenchida com sucesso em {tempo_total:.2f}s")
            print(f"{Fore.GREEN}✅ Localização configurada em {tempo_total:.2f}s (com melhorias aplicadas)!")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao preencher localização: {str(e)}")
            print(f"{Fore.RED}❌ Erro ao preencher localização: {str(e)}")
            
            # Tirar screenshot para debug
            await page.screenshot(path="debug_localizacao.png")
            self.logger.debug("Screenshot salvo: debug_localizacao.png")
            
            return False
    
    async def navegar_para_restaurantes_otimizado(self, page):
        """Navegar para seção Restaurantes com estratégias otimizadas"""
        tempo_inicio = time.time()
        
        try:
            self.logger.info("Iniciando navegação otimizada para Restaurantes")
            print(f"{Fore.WHITE}   🍴 Navegando para 'Restaurantes' (otimizado)...")
            
            # ESTRATEGIA 1: Verificar se já estamos na página correta
            try:
                # Verificar se já existem categorias visíveis (indicando que já estamos na página certa)
                categorias_visiveis = await page.query_selector_all(".small-banner-item, .category-card, [href*='/delivery/']")
                if len(categorias_visiveis) > 5:  # Se já temos muitas categorias visíveis
                    self.logger.debug("Já na página de categorias, pulando navegação")
                    print(f"{Fore.GREEN}   ✅ Já na página correta!")
                    return True
            except:
                pass
            
            # ESTRATEGIA 2: Busca direta e rápida por "Restaurantes"
            seletores_restaurantes = [
                "text='Restaurantes'",
                "a:has-text('Restaurantes')",
                "[href*='/restaurantes']",
                "[data-test*='restaurant']",
                ".category-item:has-text('Restaurantes')",
                "*[role='button']:has-text('Restaurantes')"
            ]
            
            for seletor in seletores_restaurantes:
                try:
                    elemento = await page.wait_for_selector(seletor, state="visible", timeout=1000)
                    if elemento:
                        await elemento.click()
                        self.logger.debug(f"Clicado com seletor: {seletor}")
                        print(f"{Fore.GREEN}   ✅ 'Restaurantes' clicado com seletor direto!")
                        await asyncio.sleep(1)
                        return True
                except:
                    continue
            
            # ESTRATEGIA 3: Navegação rápida do carrossel (se existir)
            try:
                # Verificar se existe carrossel
                carrossel = await page.query_selector(".swiper-wrapper, .carousel, .slider")
                if carrossel:
                    print(f"{Fore.WHITE}   🎠 Carrossel detectado, navegando...")
                    
                    # Navegar no máximo 3 vezes, rápido
                    for i in range(3):
                        # Verificar se "Restaurantes" está visível agora
                        if await page.is_visible("text='Restaurantes'"):
                            await page.click("text='Restaurantes'")
                            self.logger.debug(f"Encontrado após {i} navegações")
                            print(f"{Fore.GREEN}   ✅ 'Restaurantes' encontrado no carrossel!")
                            await asyncio.sleep(1)
                            return True
                        
                        # Navegar para próximo
                        botoes_next = [".swiper-button-next", ".carousel-next", ".slider-next", "[aria-label*='next']"]
                        navegou = False
                        for botao_seletor in botoes_next:
                            try:
                                await page.click(botao_seletor, timeout=500)
                                navegou = True
                                break
                            except:
                                continue
                        
                        if not navegou:
                            break
                        
                        await asyncio.sleep(0.3)  # Pausa rápida
            except:
                pass
            
            # ESTRATEGIA 4: Busca ampla por elementos (last resort)
            try:
                print(f"{Fore.WHITE}   🔍 Busca ampla por 'Restaurantes'...")
                todos_elementos = await page.query_selector_all("*")
                
                for elemento in todos_elementos[:100]:  # Limitar busca aos primeiros 100 elementos
                    try:
                        texto = await elemento.inner_text()
                        if (texto and "Restaurantes" in texto and 
                            len(texto.strip()) < 20 and  # Evitar textos longos
                            await elemento.is_visible()):
                            
                            await elemento.click()
                            self.logger.debug("Clicado via busca ampla")
                            print(f"{Fore.GREEN}   ✅ 'Restaurantes' encontrado por busca ampla!")
                            await asyncio.sleep(1)
                            return True
                    except:
                        continue
            except:
                pass
            
            # ESTRATEGIA 5: Skip - continuar sem clicar
            tempo_total = time.time() - tempo_inicio
            self.logger.info(f"'Restaurantes' não encontrado após {tempo_total:.2f}s, continuando...")
            print(f"{Fore.YELLOW}   ⚠️  'Restaurantes' não encontrado ({tempo_total:.2f}s), mas continuando...")
            return False
            
        except Exception as e:
            tempo_total = time.time() - tempo_inicio
            self.logger.warning(f"Erro na navegação para restaurantes ({tempo_total:.2f}s): {str(e)}")
            print(f"{Fore.YELLOW}   ⚠️  Erro na navegação ({tempo_total:.2f}s), continuando...")
            return False
    
    async def coletar_categorias(self, page):
        """Coletar as categorias disponíveis"""
        try:
            self.logger.info("Iniciando coleta de categorias")
            print(f"\n{Fore.CYAN}📂 Coletando categorias...")
            
            # Aguardar página carregar completamente
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            categorias_coletadas = []
            
            # NOVA ESTRATÉGIA: Procurar especificamente por categorias com seletor correto
            try:
                self.logger.info("Tentando coletar categorias com seletor específico")
                print(f"{Fore.WHITE}   🎯 Procurando por '.small-banner-item__title'...")
                
                # Aguardar elementos de categoria carregarem
                await page.wait_for_selector(".small-banner-item__title", timeout=10000)
                
                # Coletar títulos das categorias
                categorias_info = await page.evaluate("""
                    () => {
                        const elementos = document.querySelectorAll('.small-banner-item__title');
                        const links = document.querySelectorAll('.small-banner-item');
                        
                        const resultados = [];
                        elementos.forEach((elemento, index) => {
                            const titulo = elemento.textContent.trim();
                            let link = '';
                            
                            // Tentar pegar o link do elemento pai ou próximo
                            const linkElement = links[index];
                            if (linkElement) {
                                const anchor = linkElement.querySelector('a') || linkElement.closest('a');
                                if (anchor) {
                                    link = anchor.href;
                                } else if (linkElement.onclick) {
                                    link = linkElement.onclick.toString();
                                }
                            }
                            
                            if (titulo) {
                                resultados.push({
                                    nome: titulo,
                                    link: link || window.location.origin + '/categoria/' + titulo.toLowerCase()
                                });
                            }
                        });
                        
                        return resultados;
                    }
                """)
                
                if categorias_info and len(categorias_info) > 0:
                    categorias_coletadas = categorias_info
                    self.logger.info(f"Coletadas {len(categorias_info)} categorias com seletor específico")
                    print(f"{Fore.GREEN}   ✅ {len(categorias_info)} categorias encontradas!")
                else:
                    self.logger.warning("Seletor específico não retornou resultados")
                    
            except Exception as e:
                self.logger.warning(f"Erro com seletor específico: {str(e)}")
                print(f"{Fore.YELLOW}   ⚠️  Seletor específico falhou, tentando método alternativo...")
            
            # FALLBACK: Se o método específico falhar, usar método anterior
            if not categorias_coletadas:
                self.logger.info("Usando método alternativo de coleta")
                
                # Seletores possíveis para categorias
                seletores_categorias = [
                    ".small-banner-item",  # Novo seletor principal
                    ".category-banner",    # Alternativo
                    "a[href*='/delivery/']",  # Links de categorias
                    ".category-card",  # Cards de categoria
                    "[data-test*='category']",  # Atributos data-test
                    ".restaurant-category",  # Classes de categoria
                    "div[class*='category'] a",  # Links dentro de divs de categoria
                ]
                
                elementos_encontrados = []
                for seletor in seletores_categorias:
                    try:
                        elementos = await page.query_selector_all(seletor)
                        if elementos:
                            self.logger.debug(f"Encontrados {len(elementos)} elementos com seletor: {seletor}")
                            elementos_encontrados.extend(elementos)
                            break
                    except:
                        continue
                
                if elementos_encontrados:
                    # Processar elementos encontrados
                    for elemento in elementos_encontrados:
                        try:
                            # Tentar pegar texto do título
                            texto_elemento = await elemento.query_selector(".small-banner-item__title")
                            if texto_elemento:
                                texto = await texto_elemento.inner_text()
                            else:
                                texto = await elemento.inner_text()
                            
                            # Tentar pegar link
                            href = await elemento.get_attribute("href")
                            if not href:
                                link_child = await elemento.query_selector("a")
                                if link_child:
                                    href = await link_child.get_attribute("href")
                            
                            if texto and texto.strip():
                                categorias_coletadas.append({
                                    "nome": texto.strip(),
                                    "link": href if href and href.startswith("http") else f"{self.base_url}{href if href else '/categoria/' + texto.strip().lower()}"
                                })
                        except:
                            continue
                
                if not categorias_coletadas:
                    self.logger.warning("Nenhuma categoria encontrada com seletores, tentando busca geral")
                    # Método de busca geral como último recurso
                    todos_links = await page.query_selector_all("a[href]")
                    self.logger.debug(f"Total de links encontrados: {len(todos_links)}")
                    
                    for link in todos_links:
                        try:
                            href = await link.get_attribute("href")
                            texto = await link.inner_text()
                            
                            # Filtrar links que parecem ser de categorias
                            if href and "/delivery/" in href and texto and len(texto) > 2:
                                categorias_coletadas.append({
                                    "nome": texto.strip(),
                                    "link": href if href.startswith("http") else f"{self.base_url}{href}"
                                })
                        except:
                            continue
            
            # Filtrar e remover duplicatas
            categorias_filtradas = []
            nomes_vistos = set()
            
            # Palavras que indicam que é restaurante (não categoria)
            palavras_restaurante = [
                "mcdonald", "méqui", "burger", "delivery", "drive", "moo", "house", 
                "kibon", "açaí-", "gourmet", "best", "mccafé", "chickens", "sobremesas",
                "dia todo", "fast food", "macarrão"
            ]
            
            # Categorias válidas (filtrar apenas estas)
            categorias_validas = [
                "pizza", "japonesa", "brasileira", "açaí", "árabe", "doces", "bolos",
                "saudável", "pastel", "italiana", "sorvetes", "carnes", "bebidas",
                "lanches", "mercado", "promoções", "chinesa", "mexicana", "hamburguer",
                "comida", "restaurante", "lanche", "doce"
            ]
            
            for cat in categorias_coletadas:
                nome_lower = cat["nome"].lower()
                
                # Pular se for restaurante específico
                if any(palavra in nome_lower for palavra in palavras_restaurante):
                    self.logger.debug(f"Pulando restaurante: {cat['nome']}")
                    continue
                
                # Aceitar apenas categorias válidas OU palavras curtas (categorias gerais)
                if (any(palavra in nome_lower for palavra in categorias_validas) or 
                    len(cat["nome"]) <= 15):  # Categorias são geralmente nomes curtos
                    
                    if cat["nome"] not in nomes_vistos:
                        nomes_vistos.add(cat["nome"])
                        categorias_filtradas.append(cat)
                        self.logger.debug(f"Categoria aceita: {cat['nome']}")
                else:
                    self.logger.debug(f"Categoria rejeitada: {cat['nome']}")
            
            categorias_unicas = categorias_filtradas
            
            self.logger.info(f"Total de categorias únicas coletadas: {len(categorias_unicas)}")
            print(f"\n{Fore.GREEN}✅ Categorias coletadas: {len(categorias_unicas)}")
            
            # Mostrar categorias coletadas
            for i, cat in enumerate(categorias_unicas, 1):
                print(f"{Fore.WHITE}   [{i}] {cat['nome']}")
                self.logger.debug(f"Categoria {i}: {cat['nome']} - {cat['link']}")
            
            return categorias_unicas
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar categorias: {str(e)}")
            print(f"{Fore.RED}❌ Erro ao coletar categorias: {str(e)}")
            
            # Screenshot para debug
            await page.screenshot(path="debug_categorias.png")
            self.logger.debug("Screenshot salvo: debug_categorias.png")
            
            return []
    
    def _verificar_duplicata_categoria(self, conn, nome_categoria, link_categoria):
        """Verificar se categoria já existe no banco"""
        try:
            # Verificar por nome (critério principal)
            result = conn.execute("""
                SELECT id FROM categories 
                WHERE LOWER(TRIM(categorias)) = LOWER(TRIM(?))
                LIMIT 1
            """, [nome_categoria]).fetchone()
            
            return result is not None
            
        except Exception as e:
            self.logger.debug(f"Erro ao verificar duplicata categoria: {str(e)}")
            return False

    async def salvar_categorias_no_banco(self, categorias):
        """Salvar categorias coletadas no banco de dados (evitando duplicatas)"""
        try:
            self.logger.info("Salvando categorias no banco de dados")
            print(f"\n{Fore.CYAN}💾 Salvando no banco de dados (com verificação anti-duplicatas)...")
            
            conn = self.db_manager._get_connection()
            
            # Criar tabela se não existir (DuckDB syntax - sem AUTOINCREMENT)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY,
                    categorias VARCHAR NOT NULL,
                    links VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            categorias_salvas = 0
            categorias_duplicadas = 0
            categorias_erros = 0
            
            for i, cat in enumerate(categorias):
                try:
                    nome = cat["nome"]
                    link = cat["link"]
                    
                    # NOVO: Verificar se já existe (anti-duplicatas)
                    if self._verificar_duplicata_categoria(conn, nome, link):
                        categorias_duplicadas += 1
                        if categorias_duplicadas <= 3:  # Mostrar apenas os primeiros 3
                            print(f"{Fore.YELLOW}   🔄 Duplicata: {nome} (já existe)")
                        elif categorias_duplicadas == 4:
                            print(f"{Fore.YELLOW}   🔄 ... (mais duplicatas encontradas)")
                        continue
                    
                    # Obter próximo ID disponível
                    result = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM categories").fetchone()
                    next_id = result[0]
                    
                    # Inserir nova categoria
                    conn.execute("""
                        INSERT INTO categories (id, categorias, links, created_at) 
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, [next_id, nome, link])
                    
                    categorias_salvas += 1
                    self.logger.debug(f"Nova categoria salva: {nome}")
                    
                except Exception as e:
                    categorias_erros += 1
                    self.logger.error(f"Erro ao salvar categoria {cat.get('nome', 'N/A')}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            # Relatório final detalhado
            total_processadas = len(categorias)
            print(f"\n{Fore.CYAN}📊 RELATÓRIO FINAL:")
            print(f"{Fore.GREEN}   ✅ Novas categorias salvas: {categorias_salvas}")
            print(f"{Fore.YELLOW}   🔄 Duplicatas ignoradas: {categorias_duplicadas}")
            if categorias_erros > 0:
                print(f"{Fore.RED}   ❌ Erros encontrados: {categorias_erros}")
            print(f"{Fore.WHITE}   📋 Total processadas: {total_processadas}")
            
            eficiencia = (categorias_salvas / total_processadas * 100) if total_processadas > 0 else 0
            print(f"{Fore.CYAN}   📈 Taxa de novos dados: {eficiencia:.1f}%")
            
            self.logger.info(f"Categorias salvas: {categorias_salvas}/{total_processadas} | Duplicatas: {categorias_duplicadas}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar no banco: {str(e)}")
            print(f"{Fore.RED}❌ Erro ao salvar no banco: {str(e)}")
            return False
    
    def extract_complete_data(self):
        """Extrair nomes e URLs das categorias de uma vez - VERSÃO OTIMIZADA + MELHORIAS DO TESTE"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║     SCRAPY DE CATEGORIAS - VERSÃO OTIMIZADA + MELHORIAS  ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        print(f"\n{Fore.CYAN}📊 Iniciando extração otimizada de categorias...")
        print(f"{Fore.YELLOW}📍 Cidade configurada: {self.cidade_busca}")
        self.logger.info("Iniciando extração completa otimizada de dados de categorias")
        
        print(f"\n{Fore.WHITE}Configurações otimizadas + melhorias:")
        print(f"{Fore.WHITE}   🌐 URL: {self.base_url}")
        print(f"{Fore.WHITE}   📍 Cidade: {self.cidade_busca}")
        print(f"{Fore.WHITE}   ⚡ Wait until: {self.config_otimizado['wait_until']}")
        print(f"{Fore.WHITE}   🎯 Campo: {self.config_otimizado['campo_endereco']}")
        print(f"{Fore.WHITE}   📋 Dropdown: {self.config_otimizado['dropdown_seletor']}")
        print(f"{Fore.WHITE}   🔍 Busca ampla: {self.config_otimizado['busca_ampla_habilitada']}")
        print(f"{Fore.WHITE}   🇧🇷 Filtro SP+Brasil: {self.config_otimizado['filtro_sp_brasil']}")
        print(f"{Fore.WHITE}   ⌨️ Teclado prioritário: {self.config_otimizado['teclado_prioritario']}")
        
        # Executar scraping assíncrono
        asyncio.run(self.executar_scraping())
    
    async def executar_scraping(self):
        """Executar o processo de scraping"""
        tempo_inicio = time.time()
        
        async with async_playwright() as p:
            # Configurar navegador
            self.logger.info("Iniciando navegador")
            print(f"\n{Fore.CYAN}🌐 Iniciando navegador...")
            
            browser = await p.chromium.launch(
                headless=False,  # False para ver o processo
                args=[
                    '--no-sandbox', 
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            
            page = await context.new_page()
            
            # Configurar página para evitar detecção
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            try:
                # Acessar iFood com configuração otimizada
                self.logger.info(f"Acessando {self.base_url}")
                print(f"{Fore.CYAN}🔗 Acessando iFood (otimizado)...")
                
                await page.goto(self.base_url, wait_until=self.config_otimizado['wait_until'], timeout=30000)
                self.logger.info("Página carregada com sucesso (otimizado)")
                
                # Aguardar menos tempo (otimizado)
                await asyncio.sleep(2)
                
                # Preencher localização
                if await self.preencher_localizacao(page):
                    # Coletar categorias
                    categorias = await self.coletar_categorias(page)
                    
                    if categorias:
                        # Salvar no banco
                        await self.salvar_categorias_no_banco(categorias)
                        
                        # Estatísticas finais otimizadas
                        tempo_total = time.time() - tempo_inicio
                        performance = len(categorias) / tempo_total if tempo_total > 0 else 0
                        
                        print(f"\n{Fore.YELLOW}📊 RESUMO DA COLETA (OTIMIZADO + MELHORIAS):")
                        print(f"{Fore.WHITE}   ⏱️  Tempo total: {tempo_total:.2f}s")
                        print(f"{Fore.WHITE}   📂 Categorias coletadas: {len(categorias)}")
                        print(f"{Fore.WHITE}   🚀 Performance: {performance:.1f} categorias/segundo")
                        print(f"{Fore.WHITE}   💾 Status: Salvo no banco de dados")
                        print(f"{Fore.WHITE}   ✨ Melhorias aplicadas: Busca ampla + Filtro SP+Brasil + Teclado prioritário")
                        
                        print(f"\n{Fore.CYAN}📋 CATEGORIAS COLETADAS:")
                        for i, cat in enumerate(categorias, 1):
                            print(f"{Fore.WHITE}   [{i:2d}] {cat['nome']}")
                        
                        self.logger.info(f"Scraping concluído (otimizado + melhorias): {len(categorias)} categorias em {tempo_total:.2f}s")
                    else:
                        print(f"\n{Fore.YELLOW}⚠️  Nenhuma categoria foi coletada")
                        self.logger.warning("Nenhuma categoria coletada")
                else:
                    print(f"\n{Fore.RED}❌ Falha ao configurar localização")
                    self.logger.error("Falha ao configurar localização")
                    
            except Exception as e:
                self.logger.error(f"Erro durante scraping: {str(e)}")
                print(f"\n{Fore.RED}❌ Erro durante scraping: {str(e)}")
                
                # Screenshot final para debug
                await page.screenshot(path="debug_erro_final.png")
                self.logger.debug("Screenshot de erro salvo: debug_erro_final.png")
                
            finally:
                await browser.close()
                print(f"\n{Fore.CYAN}🔒 Navegador fechado")
                input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")