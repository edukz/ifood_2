"""
TESTE DE COLETA DE RESTAURANTES - iFood
Objetivo: Testar estratégias para coletar dados de restaurantes por categoria
"""
import asyncio
import time
from datetime import datetime
from playwright.async_api import async_playwright
from colorama import Fore, Style, Back
import sys
import os

# Adicionar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager

class TestadorRestaurantes:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
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
        
        # Seletores para restaurantes
        self.seletores_restaurantes = {
            "container_principal": "#__next > div:nth-child(1) > main > div > section > article > section > div > div",
            "container_alternativo": "[data-test-id='restaurant-list'], .restaurant-list, .merchant-list",
            "nome": {
                "principal": ".merchant-v2__header span",
                "alternativo": "h3 span, .restaurant-name, .merchant-name"
            },
            "info": {
                "principal": ".merchant-v2__info",
                "alternativo": ".restaurant-info, .merchant-info"
            },
            "entrega": {
                "principal": ".merchant-v2__content > div > span:nth-child(2)",
                "alternativo": ".delivery-fee, .merchant-delivery-fee"
            }
        }
        
        self.resultados_teste = {
            "timestamp": datetime.now().isoformat(),
            "estrategias_testadas": [],
            "melhor_estrategia": None,
            "tempo_total": 0,
            "restaurantes_encontrados": 0
        }
    
    def log_teste(self, nome, sucesso, tempo, detalhes="", dados_coletados=0):
        """Registrar resultado de um teste"""
        resultado = {
            "nome": nome,
            "sucesso": sucesso,
            "tempo_segundos": round(tempo, 2),
            "detalhes": detalhes,
            "dados_coletados": dados_coletados,
            "timestamp": datetime.now().isoformat()
        }
        self.resultados_teste["estrategias_testadas"].append(resultado)
        
        # Log visual
        status = f"{Fore.GREEN}✅" if sucesso else f"{Fore.RED}❌"
        print(f"{status} {nome}: {tempo:.2f}s - {dados_coletados} restaurantes - {detalhes}")
    
    async def preencher_localizacao_otimizado(self, page):
        """Preencher localização (herdado do categories_scraper otimizado)"""
        tempo_inicio = time.time()
        
        try:
            print(f"{Fore.CYAN}📍 Preenchendo localização...") 
            
            # Aguardar campo aparecer
            campo_endereco = await page.wait_for_selector(
                self.config_otimizado['campo_endereco'], 
                timeout=self.config_otimizado['timeout_campo']
            )
            
            # Preencher com estratégia otimizada
            await campo_endereco.fill(self.cidade_busca)
            print(f"{Fore.WHITE}   ✅ '{self.cidade_busca}' digitado")
            
            # Aguardar dropdown aparecer
            dropdown = await page.wait_for_selector(
                self.config_otimizado['dropdown_seletor'],
                timeout=self.config_otimizado['timeout_dropdown']
            )
            
            # Verificar opções
            opcoes = await page.query_selector_all(f"{self.config_otimizado['dropdown_seletor']} li")
            if not opcoes:
                opcoes = await page.query_selector_all(f"{self.config_otimizado['dropdown_seletor']} .option")
            
            print(f"{Fore.WHITE}   ✅ {len(opcoes)} opções encontradas")
            
            # Buscar opção específica com "Birigui, SP" e "Brasil"
            melhor_opcao_encontrada = False
            
            if opcoes:
                for opcao in opcoes:
                    try:
                        texto_opcao = await opcao.inner_text()
                        if ("Birigui" in texto_opcao and 
                            "SP" in texto_opcao and 
                            ("Brasil" in texto_opcao or "Brazil" in texto_opcao)):
                            await opcao.click()
                            print(f"{Fore.WHITE}   ✅ Opção específica selecionada: {texto_opcao}")
                            melhor_opcao_encontrada = True
                            break
                    except:
                        continue
                
                if not melhor_opcao_encontrada:
                    await opcoes[0].click()
                    print(f"{Fore.WHITE}   ✅ Primeira opção selecionada")
                    melhor_opcao_encontrada = True
            
            if not melhor_opcao_encontrada:
                await page.keyboard.press("ArrowDown")
                await asyncio.sleep(0.3)
                await page.keyboard.press("Enter")
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
            print(f"{Fore.RED}❌ Erro na localização ({tempo_total:.2f}s): {str(e)}")
            return False
    
    async def navegar_para_categoria(self, page, categoria_url):
        """Navegar para uma categoria específica"""
        try:
            print(f"{Fore.CYAN}🎯 Navegando para categoria...")
            
            # Ir para a URL da categoria
            await page.goto(categoria_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            print(f"{Fore.GREEN}✅ Categoria carregada!")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao navegar para categoria: {str(e)}")
            return False
    
    async def testar_estrategia_container_principal(self, page):
        """Testar estratégia com container principal"""
        tempo_inicio = time.time()
        
        try:
            print(f"{Fore.YELLOW}🧪 TESTE 1: Container Principal")
            
            # Aguardar container de restaurantes
            container = await page.wait_for_selector(
                self.seletores_restaurantes["container_principal"], 
                timeout=10000
            )
            
            if not container:
                raise Exception("Container principal não encontrado")
            
            # Buscar todos os restaurantes dentro do container
            restaurantes = await page.query_selector_all(
                f"{self.seletores_restaurantes['container_principal']} > div"
            )
            
            dados_coletados = []
            
            for i, restaurante in enumerate(restaurantes[:5]):  # Testar apenas primeiros 5
                try:
                    # Coletar nome
                    nome_element = await restaurante.query_selector(self.seletores_restaurantes["nome"]["principal"])
                    nome = await nome_element.inner_text() if nome_element else "N/A"
                    
                    # Coletar info (rating • tipo • km)
                    info_element = await restaurante.query_selector(self.seletores_restaurantes["info"]["principal"])
                    info_text = await info_element.inner_text() if info_element else "N/A"
                    
                    # Separar info por "•"
                    info_parts = [part.strip() for part in info_text.split("•")] if info_text != "N/A" else []
                    rating = info_parts[0] if len(info_parts) > 0 else "N/A"
                    tipo_comida = info_parts[1] if len(info_parts) > 1 else "N/A"
                    distancia = info_parts[2] if len(info_parts) > 2 else "N/A"
                    
                    # Coletar taxa de entrega
                    entrega_element = await restaurante.query_selector(self.seletores_restaurantes["entrega"]["principal"])
                    taxa_entrega = await entrega_element.inner_text() if entrega_element else "N/A"
                    
                    # Processar taxa de entrega
                    if taxa_entrega.lower() == "grátis":
                        taxa_entrega = "0"
                    
                    dados_coletados.append({
                        "nome": nome,
                        "rating": rating,
                        "tipo_comida": tipo_comida,
                        "distancia": distancia,
                        "taxa_entrega": taxa_entrega
                    })
                    
                    print(f"{Fore.WHITE}   [{i+1}] {nome} | {rating} | {tipo_comida} | {distancia} | {taxa_entrega}")
                    
                except Exception as e:
                    print(f"{Fore.YELLOW}   ⚠️ Erro no restaurante {i+1}: {str(e)}")
                    continue
            
            tempo = time.time() - tempo_inicio
            self.log_teste("Container Principal", True, tempo, "Seletor específico funcionou", len(dados_coletados))
            return dados_coletados
            
        except Exception as e:
            tempo = time.time() - tempo_inicio
            self.log_teste("Container Principal", False, tempo, str(e), 0)
            return []
    
    async def testar_estrategia_seletores_alternativos(self, page):
        """Testar estratégias com seletores alternativos"""
        tempo_inicio = time.time()
        
        try:
            print(f"{Fore.YELLOW}🧪 TESTE 2: Seletores Alternativos")
            
            # Tentar diferentes seletores de container
            seletores_container = [
                "[data-test-id='restaurant-list']",
                ".restaurant-list",
                ".merchant-list",
                ".restaurants-grid",
                "[role='main'] section div",
                "main section div"
            ]
            
            container = None
            seletor_usado = None
            
            for seletor in seletores_container:
                try:
                    container = await page.wait_for_selector(seletor, timeout=2000)
                    if container:
                        seletor_usado = seletor
                        print(f"{Fore.GREEN}   ✅ Container encontrado: {seletor}")
                        break
                except:
                    continue
            
            if not container:
                raise Exception("Nenhum container alternativo encontrado")
            
            # Buscar restaurantes
            restaurantes = await page.query_selector_all(f"{seletor_usado} > div, {seletor_usado} article, {seletor_usado} .restaurant-item")
            
            dados_coletados = []
            
            for i, restaurante in enumerate(restaurantes[:5]):
                try:
                    # Tentar diferentes seletores para nome
                    nome = "N/A"
                    for nome_seletor in ["h3 span", ".restaurant-name", ".merchant-name", "h3", "h2"]:
                        try:
                            nome_element = await restaurante.query_selector(nome_seletor)
                            if nome_element:
                                nome = await nome_element.inner_text()
                                break
                        except:
                            continue
                    
                    # Tentar diferentes seletores para info
                    info_text = "N/A"
                    for info_seletor in [".restaurant-info", ".merchant-info", ".info", "[data-test*='info']"]:
                        try:
                            info_element = await restaurante.query_selector(info_seletor)
                            if info_element:
                                info_text = await info_element.inner_text()
                                break
                        except:
                            continue
                    
                    # Processar info
                    info_parts = [part.strip() for part in info_text.split("•")] if info_text != "N/A" else []
                    rating = info_parts[0] if len(info_parts) > 0 else "N/A"
                    tipo_comida = info_parts[1] if len(info_parts) > 1 else "N/A"
                    distancia = info_parts[2] if len(info_parts) > 2 else "N/A"
                    
                    dados_coletados.append({
                        "nome": nome,
                        "rating": rating,
                        "tipo_comida": tipo_comida,
                        "distancia": distancia,
                        "seletor_usado": seletor_usado
                    })
                    
                    print(f"{Fore.WHITE}   [{i+1}] {nome} | {rating}")
                    
                except Exception as e:
                    continue
            
            tempo = time.time() - tempo_inicio
            self.log_teste("Seletores Alternativos", True, tempo, f"Seletor: {seletor_usado}", len(dados_coletados))
            return dados_coletados
            
        except Exception as e:
            tempo = time.time() - tempo_inicio
            self.log_teste("Seletores Alternativos", False, tempo, str(e), 0)
            return []
    
    async def testar_estrategia_busca_ampla(self, page):
        """Testar estratégia de busca ampla por elementos"""
        tempo_inicio = time.time()
        
        try:
            print(f"{Fore.YELLOW}🧪 TESTE 3: Busca Ampla")
            
            # Buscar todos os elementos que podem conter restaurantes
            todos_elementos = await page.query_selector_all("div, article, section")
            
            restaurantes_encontrados = []
            
            for elemento in todos_elementos[:200]:  # Limitar busca
                try:
                    # Verificar se parece ser um restaurante
                    texto = await elemento.inner_text()
                    
                    if (texto and 
                        len(texto) > 10 and len(texto) < 500 and
                        ("km" in texto or "min" in texto or "★" in texto or "•" in texto)):
                        
                        # Tentar extrair dados básicos
                        linhas = texto.split('\n')
                        if len(linhas) >= 2:
                            nome_possivel = linhas[0].strip()
                            info_possivel = linhas[1].strip() if len(linhas) > 1 else ""
                            
                            if (len(nome_possivel) > 3 and len(nome_possivel) < 50 and
                                ("•" in info_possivel or "km" in info_possivel)):
                                
                                restaurantes_encontrados.append({
                                    "nome": nome_possivel,
                                    "info": info_possivel,
                                    "texto_completo": texto[:100] + "..." if len(texto) > 100 else texto
                                })
                                
                                print(f"{Fore.WHITE}   [+] {nome_possivel} | {info_possivel[:30]}...")
                                
                                if len(restaurantes_encontrados) >= 5:
                                    break
                
                except:
                    continue
            
            tempo = time.time() - tempo_inicio
            self.log_teste("Busca Ampla", True, tempo, "Busca por padrões de texto", len(restaurantes_encontrados))
            return restaurantes_encontrados
            
        except Exception as e:
            tempo = time.time() - tempo_inicio
            self.log_teste("Busca Ampla", False, tempo, str(e), 0)
            return []
    
    def gerar_relatorio(self):
        """Gerar relatório final dos testes"""
        tempo_total = sum(teste["tempo_segundos"] for teste in self.resultados_teste["estrategias_testadas"])
        sucessos = [t for t in self.resultados_teste["estrategias_testadas"] if t["sucesso"]]
        
        print(f"\n{Back.GREEN}{Fore.BLACK} RELATÓRIO FINAL - TESTES DE RESTAURANTES {Style.RESET_ALL}")
        print(f"⏱️ Tempo total: {tempo_total:.2f}s")
        print(f"🧪 Testes realizados: {len(self.resultados_teste['estrategias_testadas'])}")
        print(f"✅ Sucessos: {len(sucessos)}")
        
        if sucessos:
            melhor = max(sucessos, key=lambda x: x["dados_coletados"])
            self.resultados_teste["melhor_estrategia"] = melhor
            
            print(f"\n{Fore.YELLOW}🏆 MELHOR ESTRATÉGIA:")
            print(f"   Nome: {melhor['nome']}")
            print(f"   Dados coletados: {melhor['dados_coletados']}")
            print(f"   Tempo: {melhor['tempo_segundos']}s")
            print(f"   Detalhes: {melhor['detalhes']}")
        
        return self.resultados_teste

async def executar_testes_restaurantes():
    """Executar todos os testes de restaurantes"""
    print(f"{Fore.MAGENTA}╔══════════════════════════════════════════════════════════╗")
    print(f"{Fore.MAGENTA}║           TESTES DE COLETA DE RESTAURANTES               ║")
    print(f"{Fore.MAGENTA}║              Análise de Seletores e Estratégias          ║")
    print(f"{Fore.MAGENTA}╚══════════════════════════════════════════════════════════╝")
    
    testador = TestadorRestaurantes()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # ETAPA 1: Acessar iFood
            print(f"\n{Fore.CYAN}🔄 Acessando iFood...")
            await page.goto(testador.base_url, wait_until="domcontentloaded")
            
            # ETAPA 2: Preencher localização
            sucesso_localizacao = await testador.preencher_localizacao_otimizado(page)
            if not sucesso_localizacao:
                print(f"{Fore.RED}❌ TESTE INTERROMPIDO: Falha na localização!")
                return None
            
            # ETAPA 3: Navegar para categoria (Pizza como exemplo)
            categoria_teste = "https://www.ifood.com.br/delivery/birigui-sp/pizza"
            sucesso_categoria = await testador.navegar_para_categoria(page, categoria_teste)
            if not sucesso_categoria:
                print(f"{Fore.RED}❌ TESTE INTERROMPIDO: Falha ao navegar para categoria!")
                return None
            
            # ETAPA 4: Executar testes de coleta
            print(f"\n{Fore.CYAN}🔄 Executando testes de coleta...")
            
            await testador.testar_estrategia_container_principal(page)
            await testador.testar_estrategia_seletores_alternativos(page)
            await testador.testar_estrategia_busca_ampla(page)
            
            print(f"\n{Fore.GREEN}✅ Todos os testes completados!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro durante testes: {e}")
        
        finally:
            await browser.close()
            
            # Gerar relatório
            resultados = testador.gerar_relatorio()
            
            input(f"\n{Fore.GREEN}Pressione ENTER para finalizar...")
            return resultados

if __name__ == "__main__":
    asyncio.run(executar_testes_restaurantes())