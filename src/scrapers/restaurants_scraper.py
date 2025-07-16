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
from src.utils.display_formatter import DisplayFormatter

class RestaurantsScraper:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
        self.config_manager = ConfigManager()
        self.base_url = "https://www.ifood.com.br"
        self.cidade_busca = self.config_manager.get_default_city()
        
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
            "entrega": ".merchant-v2__content > div > span:nth-child(2)",
            "link": "a",  # Link principal do restaurante
            
            # Seletores avançados para mais dados
            "rating_detalhado": ".merchant-v2__info span:first-child",
            "tempo_entrega": ".merchant-v2__content > div > span:first-child",
            "reviews_count": ".merchant-v2__info span:last-child",
            "promocoes": ".merchant-v2__promotion, .merchant-v2__badge",
            "min_order_info": ".merchant-v2__min-order, .min-order",
            
            # Seletores alternativos
            "alt_rating": "[data-testid='rating'], .rating-value, .star-rating",
            "alt_delivery_time": "[data-testid='delivery-time'], .delivery-time, .time-info",
            "alt_reviews": "[data-testid='reviews'], .reviews-count, .review-number",
            "alt_min_order": "[data-testid='min-order'], .minimum-order, .pedido-minimo"
        }
        
        # Configurações para carregamento de mais restaurantes
        # Buscar configuração de scrolls do ConfigManager
        max_scrolls_config = self.config_manager.get_max_scrolls()
        
        self.config_scroll = {
            "max_scrolls": max_scrolls_config,  # Máximo de scrolls do ConfigManager
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
                        if (self.cidade_busca in texto_opcao and "SP" in texto_opcao and 
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
    
    async def verificar_necessidade_scroll(self, page):
        """Verificar se há mais conteúdo para carregar"""
        try:
            # Verificar se há botão "Ver mais" ou similar
            botoes_mais = [
                "button:has-text('Ver mais')",
                "button:has-text('Carregar mais')",
                "button:has-text('Mostrar mais')",
                "[data-test-id='load-more']",
                ".load-more-button"
            ]
            
            for seletor in botoes_mais:
                botao = await page.query_selector(seletor)
                if botao:
                    is_visible = await botao.is_visible()
                    if is_visible:
                        print(f"{Fore.CYAN}   🔍 Botão 'Ver mais' detectado - scroll necessário")
                        return True
            
            # Verificar se página está no final
            scroll_info = await page.evaluate("""
                () => {
                    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    const scrollHeight = document.documentElement.scrollHeight;
                    const clientHeight = document.documentElement.clientHeight;
                    const scrollPercentage = (scrollTop / (scrollHeight - clientHeight)) * 100;
                    
                    return {
                        scrollTop,
                        scrollHeight,
                        clientHeight,
                        scrollPercentage,
                        isAtBottom: scrollTop + clientHeight >= scrollHeight - 100
                    };
                }
            """)
            
            if scroll_info['isAtBottom']:
                print(f"{Fore.GREEN}   ✅ Página já está no final - scroll desnecessário")
                return False
            
            # Verificar se há conteúdo lazy-loading
            lazy_indicators = []
            for selector in [".loading", ".spinner", "[data-loading]", ".skeleton"]:
                elements = await page.query_selector_all(selector)
                lazy_indicators.extend(elements)
            
            if lazy_indicators:
                print(f"{Fore.CYAN}   🔄 Indicadores de loading detectados - scroll pode ser necessário")
                return True
            
            # Por padrão, assumir que scroll pode ser necessário se não estiver no final
            print(f"{Fore.YELLOW}   📏 Scroll pode ser necessário (página {scroll_info['scrollPercentage']:.1f}% completa)")
            return scroll_info['scrollPercentage'] < 90
            
        except Exception as e:
            print(f"{Fore.YELLOW}   ⚠️ Erro ao verificar necessidade de scroll: {e}")
            return True  # Por segurança, assumir que scroll é necessário

    async def detectar_elementos_duplicados(self, page):
        """Detectar se há elementos duplicados (indica que não há mais conteúdo novo)"""
        try:
            restaurantes = await page.query_selector_all(
                f"{self.seletores_restaurantes['container']} {self.seletores_restaurantes['item']}"
            )
            
            # Coletar nomes dos últimos 10 restaurantes
            nomes_restaurantes = []
            for restaurante in restaurantes[-10:]:
                try:
                    nome_element = await restaurante.query_selector(self.seletores_restaurantes["nome"])
                    if nome_element:
                        nome = await nome_element.inner_text()
                        nomes_restaurantes.append(nome.strip())
                except:
                    continue
            
            # Verificar se há duplicatas nos últimos elementos
            if len(nomes_restaurantes) > 5:
                duplicatas = len(nomes_restaurantes) - len(set(nomes_restaurantes))
                if duplicatas >= 3:  # Se 3+ duplicatas nos últimos 10
                    print(f"{Fore.YELLOW}   🔁 Detectadas {duplicatas} duplicatas - possível fim do conteúdo")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Erro ao detectar duplicatas: {str(e)}")
            return False

    async def verificar_carregamento_completo(self, page):
        """Verificar múltiplas condições para determinar se o carregamento está completo"""
        try:
            # 1. Verificar se há indicadores de loading
            loading_selectors = [
                ".loading", ".spinner", "[data-loading]", ".skeleton",
                ".loading-more", ".load-more-spinner", "[aria-busy='true']"
            ]
            
            for selector in loading_selectors:
                loading_elements = await page.query_selector_all(f"{selector}:visible")
                if loading_elements:
                    print(f"{Fore.CYAN}   🔄 Loading detectado - aguardando...")
                    return False
            
            # 2. Verificar posição do scroll
            scroll_info = await page.evaluate("""
                () => {
                    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    const scrollHeight = document.documentElement.scrollHeight;
                    const clientHeight = document.documentElement.clientHeight;
                    const scrollPercentage = (scrollTop / (scrollHeight - clientHeight)) * 100;
                    
                    return {
                        scrollPercentage,
                        isAtBottom: scrollTop + clientHeight >= scrollHeight - 50,
                        documentHeight: scrollHeight
                    };
                }
            """)
            
            # 3. Verificar se há botões de "carregar mais" visíveis
            load_more_buttons = [
                "button:has-text('Ver mais'):visible",
                "button:has-text('Carregar mais'):visible", 
                "button:has-text('Mostrar mais'):visible",
                "[data-test-id='load-more']:visible"
            ]
            
            for selector in load_more_buttons:
                button = await page.query_selector(selector)
                if button:
                    print(f"{Fore.CYAN}   🔘 Botão 'Carregar mais' ainda visível")
                    return False
            
            # 4. Verificar duplicatas
            tem_duplicatas = await self.detectar_elementos_duplicados(page)
            
            # Condições para considerar carregamento completo:
            condicoes_fim = [
                scroll_info['isAtBottom'],  # Está no final da página
                scroll_info['scrollPercentage'] > 95,  # Scroll > 95%
                tem_duplicatas  # Tem elementos duplicados
            ]
            
            condicoes_atendidas = sum(condicoes_fim)
            
            if condicoes_atendidas >= 2:  # Se 2+ condições são atendidas
                print(f"{Fore.GREEN}   ✅ Carregamento completo detectado ({condicoes_atendidas}/3 condições)")
                return True
            
            print(f"{Fore.CYAN}   📊 Progresso: {scroll_info['scrollPercentage']:.1f}% | Condições: {condicoes_atendidas}/3")
            return False
            
        except Exception as e:
            self.logger.debug(f"Erro ao verificar carregamento: {str(e)}")
            return False

    async def carregar_mais_restaurantes_com_scroll(self, page):
        """Fazer scroll automático inteligente para carregar mais restaurantes"""
        try:
            restaurantes_iniciais = len(await page.query_selector_all(
                f"{self.seletores_restaurantes['container']} {self.seletores_restaurantes['item']}"
            ))
            
            print(f"{Fore.WHITE}   📊 Restaurantes iniciais: {restaurantes_iniciais}")
            
            # Verificar se scroll é necessário
            precisa_scroll = await self.verificar_necessidade_scroll(page)
            
            if not precisa_scroll:
                print(f"{Fore.GREEN}   ⚡ Scroll desnecessário - usando {restaurantes_iniciais} restaurantes existentes")
                return restaurantes_iniciais
            
            print(f"{Fore.CYAN}   🔄 Iniciando scroll inteligente...")
            
            scrolls_realizados = 0
            max_scrolls = self.config_scroll["max_scrolls"]
            sem_novos_restaurantes = 0
            max_tentativas = self.config_scroll["max_tentativas_sem_novos"]
            restaurantes_antes_scroll = restaurantes_iniciais
            altura_pagina_anterior = 0
            
            while scrolls_realizados < max_scrolls and sem_novos_restaurantes < max_tentativas:
                # Verificar se carregamento está completo (múltiplas condições)
                carregamento_completo = await self.verificar_carregamento_completo(page)
                if carregamento_completo:
                    print(f"{Fore.GREEN}   🎯 Sistema inteligente detectou fim do conteúdo - parando scroll")
                    break
                
                # Verificar se altura da página mudou (indicador de novo conteúdo)
                altura_atual = await page.evaluate("document.documentElement.scrollHeight")
                if altura_atual == altura_pagina_anterior and scrolls_realizados > 2:
                    print(f"{Fore.YELLOW}   📏 Altura da página não mudou - possível fim do conteúdo")
                    sem_novos_restaurantes += 1
                else:
                    altura_pagina_anterior = altura_atual
                
                # Fazer scroll para baixo
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(self.config_scroll["timeout_scroll"])
                
                # Aguardar carregamento adicional após scroll
                await asyncio.sleep(1)
                
                # Verificar se carregaram novos restaurantes
                restaurantes_atuais = len(await page.query_selector_all(
                    f"{self.seletores_restaurantes['container']} {self.seletores_restaurantes['item']}"
                ))
                
                if restaurantes_atuais > restaurantes_antes_scroll:
                    novos_restaurantes = restaurantes_atuais - restaurantes_antes_scroll
                    print(f"{Fore.GREEN}   ✅ +{novos_restaurantes} restaurantes carregados (scroll {scrolls_realizados + 1})")
                    restaurantes_antes_scroll = restaurantes_atuais
                    sem_novos_restaurantes = 0
                else:
                    sem_novos_restaurantes += 1
                    print(f"{Fore.YELLOW}   ⏳ Aguardando carregamento... ({sem_novos_restaurantes}/{max_tentativas})")
                
                scrolls_realizados += 1
                
                # Estratégias para carregar mais conteúdo
                await self.tentar_carregar_mais_conteudo(page, scrolls_realizados)
                
                # Parada inteligente: se muitos scrolls sem resultado, verificar fim
                if sem_novos_restaurantes >= 2:
                    fim_detectado = await self.verificar_carregamento_completo(page)
                    if fim_detectado:
                        print(f"{Fore.GREEN}   🧠 Parada inteligente ativada - fim do conteúdo confirmado")
                        break
            
            restaurantes_finais = len(await page.query_selector_all(
                f"{self.seletores_restaurantes['container']} {self.seletores_restaurantes['item']}"
            ))
            
            total_carregados = restaurantes_finais - restaurantes_iniciais
            eficiencia_msg = "otimizado" if scrolls_realizados < max_scrolls else "máximo atingido"
            economia_scrolls = max_scrolls - scrolls_realizados
            
            if economia_scrolls > 0:
                print(f"{Fore.GREEN}   🎯 Total: {restaurantes_finais} restaurantes (+{total_carregados}) | {scrolls_realizados} scrolls ({eficiencia_msg}) | 💡 {economia_scrolls} scrolls economizados!")
            else:
                print(f"{Fore.GREEN}   🎯 Total: {restaurantes_finais} restaurantes (+{total_carregados}) | {scrolls_realizados} scrolls ({eficiencia_msg})")
                
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
            print(DisplayFormatter.subsection("Carregando restaurantes com scroll inteligente"))
            await self.carregar_mais_restaurantes_com_scroll(page)
            
            # Buscar todos os restaurantes após o scroll
            restaurantes = await page.query_selector_all(
                f"{self.seletores_restaurantes['container']} {self.seletores_restaurantes['item']}"
            )
            
            print(DisplayFormatter.success(f"{len(restaurantes)} restaurantes encontrados"))
            
            dados_coletados = []
            
            for i, restaurante in enumerate(restaurantes):
                try:
                    # Coletar nome
                    nome_element = await restaurante.query_selector(self.seletores_restaurantes["nome"])
                    nome = await nome_element.inner_text() if nome_element else "N/A"
                    
                    # Coletar link do restaurante (estratégias múltiplas)
                    link_restaurante = "N/A"
                    
                    # Estratégia 1: Seletor específico fornecido
                    try:
                        link_element = await restaurante.query_selector("a")
                        if link_element:
                            href = await link_element.get_attribute("href")
                            if href:
                                # Se for link relativo, completar com base_url
                                if href.startswith("/"):
                                    link_restaurante = f"{self.base_url}{href}"
                                else:
                                    link_restaurante = href
                                # Link coletado silenciosamente
                    except:
                        pass
                    
                    # Estratégia 2: Se não encontrou, tentar seletor mais específico
                    if link_restaurante == "N/A":
                        try:
                            # Usando o seletor específico que você forneceu
                            link_element = await page.query_selector(f"{self.seletores_restaurantes['container']} > div:nth-child({i+1}) > a")
                            if link_element:
                                href = await link_element.get_attribute("href")
                                if href:
                                    if href.startswith("/"):
                                        link_restaurante = f"{self.base_url}{href}"
                                    else:
                                        link_restaurante = href
                                    # Link coletado silenciosamente
                        except:
                            pass
                    
                    # Coletar info (rating • tipo • km)
                    info_element = await restaurante.query_selector(self.seletores_restaurantes["info"])
                    info_text = await info_element.inner_text() if info_element else "N/A"
                    
                    # Separar info por "•"
                    info_parts = [part.strip() for part in info_text.split("•")] if info_text != "N/A" else []
                    rating = info_parts[0] if len(info_parts) > 0 else "N/A"
                    tipo_comida = info_parts[1] if len(info_parts) > 1 else "N/A"
                    distancia = info_parts[2] if len(info_parts) > 2 else "N/A"
                    
                    # MELHORADO: Coletar dados avançados
                    dados_avancados = await self._coletar_dados_avancados(restaurante)
                    
                    # Usar dados melhorados se disponíveis
                    if dados_avancados["rating"] != "N/A":
                        rating = dados_avancados["rating"]
                    
                    # Coletar taxa de entrega
                    entrega_element = await restaurante.query_selector(self.seletores_restaurantes["entrega"])
                    taxa_entrega = await entrega_element.inner_text() if entrega_element else "N/A"
                    
                    # Usar delivery_time melhorado se disponível
                    delivery_time = dados_avancados["delivery_time"]
                    if delivery_time == "N/A" and taxa_entrega != "N/A":
                        # Tentar extrair tempo da string de entrega
                        import re
                        time_match = re.search(r'(\d+)-(\d+)\s*min', taxa_entrega)
                        if time_match:
                            # Usar tempo médio
                            min_time = int(time_match.group(1))
                            max_time = int(time_match.group(2))
                            delivery_time = (min_time + max_time) // 2
                    
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
                        "delivery_time": delivery_time,
                        "reviews": dados_avancados["reviews"],
                        "min_order": dados_avancados["min_order"],
                        "link_restaurante": link_restaurante,
                        "categoria_url": categoria_url
                    })
                    
                    if (i + 1) % 20 == 0:
                        progress_msg = DisplayFormatter.progress(i + 1, len(restaurantes), "processados")
                        print(progress_msg)
                    
                except Exception as e:
                    self.logger.debug(f"Erro ao processar restaurante {i+1}: {str(e)}")
                    continue
            
            print(DisplayFormatter.success(f"{len(dados_coletados)} restaurantes coletados"))
            return dados_coletados
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar restaurantes da categoria {categoria_nome}: {str(e)}")
            print(f"{Fore.RED}❌ Erro na categoria {categoria_nome}: {str(e)}")
            return []
    
    async def _coletar_dados_avancados(self, restaurante_element):
        """Coletar dados avançados do restaurante (delivery_time, reviews, min_order)"""
        dados = {
            "rating": "N/A",
            "delivery_time": "N/A", 
            "reviews": "N/A",
            "min_order": "N/A"
        }
        
        try:
            # 1. RATING detalhado
            for seletor in [self.seletores_restaurantes["rating_detalhado"], 
                           self.seletores_restaurantes["alt_rating"]]:
                try:
                    rating_elem = await restaurante_element.query_selector(seletor)
                    if rating_elem:
                        rating_text = await rating_elem.inner_text()
                        # Extrair apenas número (ex: "4.5" de "4.5 ★" ou "★ 4.5")
                        import re
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            dados["rating"] = rating_match.group(1)
                            break
                except:
                    continue
            
            # 2. DELIVERY TIME
            for seletor in [self.seletores_restaurantes["tempo_entrega"],
                           self.seletores_restaurantes["alt_delivery_time"]]:
                try:
                    time_elem = await restaurante_element.query_selector(seletor)
                    if time_elem:
                        time_text = await time_elem.inner_text()
                        # Extrair tempo em minutos (ex: "30-45 min" → 37)
                        import re
                        time_match = re.search(r'(\d+)-(\d+)\s*min', time_text)
                        if time_match:
                            min_time = int(time_match.group(1))
                            max_time = int(time_match.group(2))
                            dados["delivery_time"] = (min_time + max_time) // 2
                            break
                        # Tempo único (ex: "30 min")
                        single_time = re.search(r'(\d+)\s*min', time_text)
                        if single_time:
                            dados["delivery_time"] = int(single_time.group(1))
                            break
                except:
                    continue
            
            # 3. REVIEWS COUNT
            for seletor in [self.seletores_restaurantes["reviews_count"],
                           self.seletores_restaurantes["alt_reviews"]]:
                try:
                    reviews_elem = await restaurante_element.query_selector(seletor)
                    if reviews_elem:
                        reviews_text = await reviews_elem.inner_text()
                        # Extrair número de reviews (ex: "(234)" ou "234 avaliações")
                        import re
                        reviews_match = re.search(r'(\d+)', reviews_text)
                        if reviews_match:
                            dados["reviews"] = int(reviews_match.group(1))
                            break
                except:
                    continue
            
            # 4. MIN ORDER
            for seletor in [self.seletores_restaurantes["min_order_info"],
                           self.seletores_restaurantes["alt_min_order"]]:
                try:
                    min_order_elem = await restaurante_element.query_selector(seletor)
                    if min_order_elem:
                        min_order_text = await min_order_elem.inner_text()
                        # Extrair valor mínimo (ex: "R$ 25,00" ou "Mínimo R$25")
                        import re
                        min_order_match = re.search(r'R\$\s*(\d+[.,]?\d*)', min_order_text)
                        if min_order_match:
                            valor_str = min_order_match.group(1).replace(',', '.')
                            dados["min_order"] = float(valor_str)
                            break
                except:
                    continue
            
            # 5. Busca adicional no texto completo do elemento (fallback)
            try:
                texto_completo = await restaurante_element.inner_text()
                
                # Buscar reviews no texto completo
                if dados["reviews"] == "N/A":
                    import re
                    # Padrões: "(123)", "123 avaliações", "123 reviews"
                    reviews_patterns = [r'\((\d+)\)', r'(\d+)\s*avalia', r'(\d+)\s*review']
                    for pattern in reviews_patterns:
                        match = re.search(pattern, texto_completo, re.IGNORECASE)
                        if match:
                            dados["reviews"] = int(match.group(1))
                            break
                
                # Buscar min_order no texto completo
                if dados["min_order"] == "N/A":
                    min_patterns = [r'mínimo.*?R\$\s*(\d+[.,]?\d*)', r'pedido.*?R\$\s*(\d+[.,]?\d*)']
                    for pattern in min_patterns:
                        match = re.search(pattern, texto_completo, re.IGNORECASE)
                        if match:
                            valor_str = match.group(1).replace(',', '.')
                            dados["min_order"] = float(valor_str)
                            break
                            
            except:
                pass
        
        except Exception as e:
            # Log silencioso de erros
            pass
        
        return dados
    
    def _verificar_estrutura_tabela_restaurants(self, conn):
        """Verificar e adicionar coluna link se necessário"""
        try:
            # Verificar se coluna 'link' existe
            try:
                conn.execute("SELECT link FROM restaurants LIMIT 1")
                # Coluna existe, continuar silenciosamente
            except:
                print(f"{Fore.YELLOW}⚠️ Adicionando coluna 'link' à tabela restaurants...")
                try:
                    conn.execute("ALTER TABLE restaurants ADD COLUMN link VARCHAR")
                    conn.commit()
                    print(f"{Fore.GREEN}✅ Coluna 'link' adicionada com sucesso!")
                except Exception as alter_error:
                    print(f"{Fore.RED}❌ Erro ao adicionar coluna link: {alter_error}")
                    
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao verificar tabela: {e}")
    
    def _verificar_duplicata_restaurante(self, conn, nome, cidade, categoria):
        """Verificar se restaurante já existe no banco"""
        try:
            # Verificar por nome + cidade (critério principal)
            result = conn.execute("""
                SELECT id FROM restaurants 
                WHERE LOWER(TRIM(name)) = LOWER(TRIM(?)) 
                AND LOWER(TRIM(city)) = LOWER(TRIM(?))
                LIMIT 1
            """, [nome, cidade]).fetchone()
            
            return result is not None
            
        except Exception as e:
            self.logger.debug(f"Erro ao verificar duplicata: {str(e)}")
            return False

    def salvar_restaurantes_no_banco(self, restaurantes):
        """Salvar restaurantes coletados no banco de dados (evitando duplicatas)"""
        try:
            self.logger.info("Salvando restaurantes no banco de dados")
            print(f"\n{Fore.CYAN}💾 Salvando no banco de dados (com verificação anti-duplicatas)...")
            
            conn = self.db_manager._get_connection()
            
            # Verificar/corrigir estrutura da tabela
            self._verificar_estrutura_tabela_restaurants(conn)
            
            restaurantes_salvos = 0
            restaurantes_duplicados = 0
            restaurantes_erros = 0
            
            for i, rest in enumerate(restaurantes):
                try:
                    nome = rest["nome"]
                    categoria = rest["categoria"]
                    
                    # NOVO: Verificar se já existe (anti-duplicatas)
                    if self._verificar_duplicata_restaurante(conn, nome, self.cidade_busca, categoria):
                        restaurantes_duplicados += 1
                        if restaurantes_duplicados <= 5:  # Mostrar apenas os primeiros 5
                            print(f"{Fore.YELLOW}   🔄 Duplicata: {nome} (já existe)")
                        elif restaurantes_duplicados == 6:
                            print(f"{Fore.YELLOW}   🔄 ... (mais duplicatas encontradas)")
                        continue
                    
                    # Obter próximo ID
                    result = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM restaurants").fetchone()
                    next_id = result[0]
                    
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
                    
                    # Processar link do restaurante
                    link_rest = rest.get("link_restaurante", "N/A")
                    if link_rest == "N/A":
                        # Gerar link baseado na cidade configurada
                        cidade_url = self.cidade_busca.lower().replace(' ', '-')
                        link_rest = f"{self.base_url}/delivery/{cidade_url}-sp/{nome.lower().replace(' ', '-')}"
                    
                    # Processar dados avançados
                    delivery_time_num = None
                    if rest.get("delivery_time", "N/A") != "N/A":
                        try:
                            delivery_time_num = int(rest["delivery_time"])
                        except:
                            delivery_time_num = None
                    
                    reviews_num = None
                    if rest.get("reviews", "N/A") != "N/A":
                        try:
                            reviews_num = int(rest["reviews"])
                        except:
                            reviews_num = None
                    
                    min_order_num = None
                    if rest.get("min_order", "N/A") != "N/A":
                        try:
                            min_order_num = float(rest["min_order"])
                        except:
                            min_order_num = None
                    
                    # Inserir novo restaurante com todos os campos
                    conn.execute("""
                        INSERT INTO restaurants (id, name, category, rating, delivery_time, delivery_fee, 
                                               city, link, reviews, min_order, scraped_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, [next_id, nome, categoria, rating_num, delivery_time_num, 
                          delivery_fee_num, self.cidade_busca, link_rest, reviews_num, min_order_num])
                    
                    restaurantes_salvos += 1
                    
                    # Log progresso a cada 50 restaurantes
                    if restaurantes_salvos % 50 == 0:
                        print(f"{Fore.GREEN}   ✅ {restaurantes_salvos} novos restaurantes salvos...")
                    
                except Exception as e:
                    restaurantes_erros += 1
                    self.logger.error(f"Erro ao salvar restaurante {rest.get('nome', 'N/A')}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            # Relatório final detalhado
            total_processados = len(restaurantes)
            print(f"\n{Fore.CYAN}📊 RELATÓRIO FINAL:")
            print(f"{Fore.GREEN}   ✅ Novos restaurantes salvos: {restaurantes_salvos}")
            print(f"{Fore.YELLOW}   🔄 Duplicatas ignoradas: {restaurantes_duplicados}")
            if restaurantes_erros > 0:
                print(f"{Fore.RED}   ❌ Erros encontrados: {restaurantes_erros}")
            print(f"{Fore.WHITE}   📋 Total processados: {total_processados}")
            
            eficiencia = (restaurantes_salvos / total_processados * 100) if total_processados > 0 else 0
            print(f"{Fore.CYAN}   📈 Taxa de novos dados: {eficiencia:.1f}%")
            
            self.logger.info(f"Restaurantes salvos: {restaurantes_salvos}/{total_processados} | Duplicatas: {restaurantes_duplicados}")
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
        print(f"{Fore.RED}[0 ] Voltar")
        
        while True:
            try:
                escolha = input(f"\n{Fore.YELLOW}➤ Escolha as categorias (ex: 1,3,5 ou 99 para todas): ").strip()
                
                if escolha == '0':
                    return None, None
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
        print(f"\n{DisplayFormatter.header('SCRAPER DE RESTAURANTES POR CATEGORIA')}")
        
        # Menu de seleção
        categorias_selecionadas, tipo_selecao = self.exibir_menu_selecao_categorias()
        
        if not categorias_selecionadas:
            return
        
        print(f"\n{DisplayFormatter.section('Iniciando coleta de restaurantes')}")
        print(f"{DisplayFormatter.info(f'Cidade configurada: {self.cidade_busca}')}")
        
        if tipo_selecao == "todas":
            print(f"{DisplayFormatter.info(f'Coletando TODAS as {len(categorias_selecionadas)} categorias')}")
        else:
            categoria_nomes = [cat['nome'] for cat in categorias_selecionadas]
            print(f"{DisplayFormatter.compact_list(categoria_nomes, f'Coletando {len(categorias_selecionadas)} categorias selecionadas')}")
        
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
                    
                    # Criar dados de estatísticas
                    stats_data = {
                        "Tempo total": f"{tempo_total:.2f}s",
                        "Categorias": len(categorias),
                        "Restaurantes": len(todos_restaurantes),
                        "Performance": f"{performance:.1f}/s",
                        "Status": "✓ Salvo no BD"
                    }
                    
                    print(f"\n{DisplayFormatter.stats_table(stats_data)}")
                    
                    # Estatísticas por categoria
                    from collections import Counter
                    contadores = Counter(r['categoria'] for r in todos_restaurantes)
                    
                    categoria_list = [f"{categoria}: {count} restaurantes" for categoria, count in contadores.items()]
                    print(f"\n{DisplayFormatter.compact_list(categoria_list, 'RESTAURANTES POR CATEGORIA')}")
                    
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