"""
VERSÃO FINAL OTIMIZADA - iFood Categories Scraper
Baseada nos resultados dos testes de performance
"""
import asyncio
import time
from datetime import datetime
from playwright.async_api import async_playwright
from colorama import Fore, Style
import sys
import os

# Adicionar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager

class CategoriesScraperFinal:
    def __init__(self):
        self.logger = get_logger()
        self.db_manager = DatabaseManager()
        self.base_url = "https://www.ifood.com.br"
        self.cidade_busca = "Birigui"
        
        # Configurações otimizadas baseadas nos testes
        self.config = {
            "campo_endereco": "input[placeholder*='Endereço de entrega']",
            "dropdown_seletor": ".address-search-list",
            "wait_until": "domcontentloaded",  # 0.51s vs 5.42s
            "timeout_campo": 5000,
            "timeout_dropdown": 5000,
            "estrategia_preenchimento": "fill_direto"
        }
    
    def log_tempo(self, etapa, tempo_inicio):
        """Log de tempo de cada etapa"""
        tempo = time.time() - tempo_inicio
        self.logger.info(f"{etapa}: {tempo:.2f}s")
        print(f"{Fore.CYAN}⏱️  {etapa}: {tempo:.2f}s")
        return tempo
    
    async def executar_scraping_otimizado(self):
        """Executar scraping com configurações otimizadas"""
        tempo_total_inicio = time.time()
        
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║          SCRAPER FINAL OTIMIZADO - CATEGORIAS            ║")
        print(f"{Fore.YELLOW}║           Baseado em testes de performance               ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        print(f"\n{Fore.CYAN}🚀 Configurações otimizadas:")
        print(f"{Fore.WHITE}   • Wait until: {self.config['wait_until']}")
        print(f"{Fore.WHITE}   • Campo: {self.config['campo_endereco']}")
        print(f"{Fore.WHITE}   • Dropdown: {self.config['dropdown_seletor']}")
        print(f"{Fore.WHITE}   • Estratégia: {self.config['estrategia_preenchimento']}")
        
        async with async_playwright() as p:
            # Configurar navegador
            tempo_inicio = time.time()
            browser = await p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            self.log_tempo("Configuração do navegador", tempo_inicio)
            
            try:
                # ETAPA 1: Acessar página (otimizado)
                tempo_inicio = time.time()
                await page.goto(self.base_url, wait_until=self.config['wait_until'])
                self.log_tempo("Acesso à página", tempo_inicio)
                
                # ETAPA 2: Preencher localização (otimizado)
                sucesso_localizacao = await self.preencher_localizacao_otimizado(page)
                if not sucesso_localizacao:
                    print(f"{Fore.RED}❌ Falha na configuração de localização")
                    return False
                
                # ETAPA 3: Navegar para categorias
                tempo_inicio = time.time()
                await self.navegar_para_categorias(page)
                self.log_tempo("Navegação para categorias", tempo_inicio)
                
                # ETAPA 4: Coletar categorias
                tempo_inicio = time.time()
                categorias = await self.coletar_categorias_otimizado(page)
                self.log_tempo("Coleta de categorias", tempo_inicio)
                
                if categorias:
                    # ETAPA 5: Salvar no banco
                    tempo_inicio = time.time()
                    sucesso_salvamento = await self.salvar_categorias_otimizado(categorias)
                    self.log_tempo("Salvamento no banco", tempo_inicio)
                    
                    # Relatório final
                    tempo_total = time.time() - tempo_total_inicio
                    self.gerar_relatorio_final(categorias, tempo_total, sucesso_salvamento)
                    return True
                else:
                    print(f"{Fore.RED}❌ Nenhuma categoria coletada")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Erro durante scraping: {str(e)}")
                print(f"{Fore.RED}❌ Erro: {str(e)}")
                return False
                
            finally:
                await browser.close()
                print(f"{Fore.CYAN}🔒 Navegador fechado")
    
    async def preencher_localizacao_otimizado(self, page):
        """Preencher localização com configurações otimizadas"""
        tempo_inicio = time.time()
        
        try:
            print(f"\n{Fore.CYAN}📍 Preenchendo localização...")
            
            # Aguardar campo aparecer (configuração otimizada)
            campo_endereco = await page.wait_for_selector(
                self.config['campo_endereco'], 
                timeout=self.config['timeout_campo']
            )
            self.logger.debug(f"Campo encontrado: {self.config['campo_endereco']}")
            
            # Preencher com estratégia otimizada
            await campo_endereco.fill(self.cidade_busca)
            self.logger.info(f"Cidade preenchida: {self.cidade_busca}")
            print(f"{Fore.WHITE}   ✅ '{self.cidade_busca}' digitado")
            
            # Aguardar dropdown aparecer (configuração otimizada)
            print(f"{Fore.WHITE}   ⏳ Aguardando opções...")
            dropdown = await page.wait_for_selector(
                self.config['dropdown_seletor'],
                timeout=self.config['timeout_dropdown']
            )
            
            # Verificar opções
            opcoes = await page.query_selector_all(f"{self.config['dropdown_seletor']} li")
            if not opcoes:
                opcoes = await page.query_selector_all(f"{self.config['dropdown_seletor']} .option")
            
            self.logger.info(f"Dropdown encontrado: {len(opcoes)} opções")
            print(f"{Fore.WHITE}   ✅ {len(opcoes)} opções encontradas")
            
            # Selecionar primeira opção (mais rápido e confiável)
            if opcoes:
                await opcoes[0].click()
                self.logger.debug("Primeira opção selecionada")
                print(f"{Fore.WHITE}   ✅ Opção selecionada")
            else:
                # Fallback: usar teclado
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
            
            tempo_total = self.log_tempo("Preenchimento de localização", tempo_inicio)
            print(f"{Fore.GREEN}✅ Localização configurada em {tempo_total:.2f}s!")
            return True
            
        except Exception as e:
            tempo_total = time.time() - tempo_inicio
            self.logger.error(f"Erro ao preencher localização: {str(e)}")
            print(f"{Fore.RED}❌ Erro na localização ({tempo_total:.2f}s): {str(e)}")
            
            # Screenshot para debug
            await page.screenshot(path="debug_localizacao_final.png")
            self.logger.debug("Screenshot salvo: debug_localizacao_final.png")
            
            return False
    
    async def navegar_para_categorias(self, page):
        """Navegar para seção de categorias se necessário"""
        try:
            print(f"\n{Fore.CYAN}🎠 Navegando para categorias...")
            
            # Aguardar página carregar
            await page.wait_for_load_state("networkidle", timeout=10000)
            await asyncio.sleep(2)
            
            # Tentar encontrar "Restaurantes" rapidamente
            if await page.is_visible("text='Restaurantes'"):
                await page.click("text='Restaurantes'")
                print(f"{Fore.WHITE}   ✅ 'Restaurantes' clicado")
                await asyncio.sleep(2)
            else:
                print(f"{Fore.WHITE}   ℹ️  'Restaurantes' não encontrado, continuando...")
            
        except Exception as e:
            self.logger.warning(f"Erro ao navegar para categorias: {str(e)}")
            print(f"{Fore.YELLOW}   ⚠️  Navegação parcial, continuando...")
    
    async def coletar_categorias_otimizado(self, page):
        """Coletar categorias com seletores otimizados"""
        try:
            print(f"\n{Fore.CYAN}📂 Coletando categorias...")
            
            # Aguardar página estabilizar
            await asyncio.sleep(3)
            
            categorias = []
            
            # Estratégia 1: Seletor específico (baseado nos testes)
            try:
                elementos = await page.query_selector_all(".small-banner-item__title")
                if elementos:
                    print(f"{Fore.WHITE}   🎯 Usando seletor específico: {len(elementos)} elementos")
                    
                    for elemento in elementos:
                        try:
                            texto = await elemento.inner_text()
                            if texto and len(texto.strip()) > 0:
                                # Tentar pegar link do elemento pai
                                parent = await elemento.evaluate_handle("el => el.closest('a') || el.closest('[href]')")
                                href = ""
                                try:
                                    href = await parent.get_attribute("href")
                                except:
                                    pass
                                
                                categorias.append({
                                    "nome": texto.strip(),
                                    "link": href if href and href.startswith("http") else f"{self.base_url}/categoria/{texto.strip().lower()}"
                                })
                        except:
                            continue
                
                if categorias:
                    self.logger.info(f"Categorias coletadas com seletor específico: {len(categorias)}")
                    print(f"{Fore.GREEN}   ✅ {len(categorias)} categorias coletadas!")
                    return self.filtrar_categorias(categorias)
            
            except Exception as e:
                self.logger.warning(f"Seletor específico falhou: {str(e)}")
            
            # Estratégia 2: Fallback (seletores alternativos)
            seletores_fallback = [
                ".category-banner",
                ".category-card", 
                "a[href*='/delivery/']"
            ]
            
            for seletor in seletores_fallback:
                try:
                    elementos = await page.query_selector_all(seletor)
                    if elementos:
                        print(f"{Fore.WHITE}   🔄 Fallback: {seletor} ({len(elementos)} elementos)")
                        
                        for elemento in elementos:
                            try:
                                texto = await elemento.inner_text()
                                href = await elemento.get_attribute("href")
                                
                                if texto and len(texto.strip()) > 0:
                                    categorias.append({
                                        "nome": texto.strip(),
                                        "link": href if href and href.startswith("http") else f"{self.base_url}{href if href else '/categoria/' + texto.strip().lower()}"
                                    })
                            except:
                                continue
                        
                        if categorias:
                            self.logger.info(f"Categorias coletadas com fallback: {len(categorias)}")
                            print(f"{Fore.GREEN}   ✅ {len(categorias)} categorias coletadas (fallback)!")
                            return self.filtrar_categorias(categorias)
                
                except Exception as e:
                    self.logger.debug(f"Fallback {seletor} falhou: {str(e)}")
                    continue
            
            print(f"{Fore.RED}   ❌ Nenhuma categoria encontrada")
            return []
            
        except Exception as e:
            self.logger.error(f"Erro na coleta de categorias: {str(e)}")
            print(f"{Fore.RED}❌ Erro na coleta: {str(e)}")
            
            # Screenshot para debug
            await page.screenshot(path="debug_categorias_final.png")
            self.logger.debug("Screenshot salvo: debug_categorias_final.png")
            
            return []
    
    def filtrar_categorias(self, categorias_brutas):
        """Filtrar categorias para remover restaurantes e duplicatas"""
        # Palavras que indicam restaurantes específicos
        palavras_restaurante = [
            "mcdonald", "méqui", "burger", "delivery", "drive", "moo", "house", 
            "kibon", "açaí-", "gourmet", "best", "mccafé", "chickens", "sobremesas"
        ]
        
        categorias_filtradas = []
        nomes_vistos = set()
        
        for cat in categorias_brutas:
            nome_lower = cat["nome"].lower()
            
            # Pular restaurantes específicos
            if any(palavra in nome_lower for palavra in palavras_restaurante):
                continue
            
            # Evitar duplicatas
            if cat["nome"] in nomes_vistos:
                continue
            
            nomes_vistos.add(cat["nome"])
            categorias_filtradas.append(cat)
        
        self.logger.info(f"Categorias após filtro: {len(categorias_filtradas)}")
        return categorias_filtradas
    
    async def salvar_categorias_otimizado(self, categorias):
        """Salvar categorias no banco com otimizações"""
        try:
            print(f"\n{Fore.CYAN}💾 Salvando no banco de dados...")
            
            conn = self.db_manager._get_connection()
            
            # Criar tabela otimizada (DuckDB syntax)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY,
                    categorias VARCHAR NOT NULL,
                    links VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Limpar e inserir
            conn.execute("DELETE FROM categories")
            
            categorias_salvas = 0
            for cat in categorias:
                try:
                    conn.execute("""
                        INSERT INTO categories (categorias, links) 
                        VALUES (?, ?)
                    """, [cat["nome"], cat["link"]])
                    categorias_salvas += 1
                except Exception as e:
                    self.logger.error(f"Erro ao salvar categoria {cat['nome']}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Categorias salvas: {categorias_salvas}/{len(categorias)}")
            print(f"{Fore.GREEN}✅ {categorias_salvas} categorias salvas!")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar no banco: {str(e)}")
            print(f"{Fore.RED}❌ Erro ao salvar: {str(e)}")
            return False
    
    def gerar_relatorio_final(self, categorias, tempo_total, sucesso_salvamento):
        """Gerar relatório final otimizado"""
        print(f"\n{Fore.YELLOW}📊 RELATÓRIO FINAL:")
        print(f"{Fore.WHITE}   ⏱️  Tempo total: {tempo_total:.2f}s")
        print(f"{Fore.WHITE}   📂 Categorias coletadas: {len(categorias)}")
        print(f"{Fore.WHITE}   💾 Salvamento: {'✅ Sucesso' if sucesso_salvamento else '❌ Falha'}")
        print(f"{Fore.WHITE}   🚀 Performance: {len(categorias)/tempo_total:.1f} categorias/segundo")
        
        print(f"\n{Fore.CYAN}📋 CATEGORIAS COLETADAS:")
        for i, cat in enumerate(categorias, 1):
            print(f"{Fore.WHITE}   [{i:2d}] {cat['nome']}")
        
        self.logger.info(f"Scraping concluído: {len(categorias)} categorias em {tempo_total:.2f}s")

async def main():
    """Função principal"""
    scraper = CategoriesScraperFinal()
    sucesso = await scraper.executar_scraping_otimizado()
    
    if sucesso:
        print(f"\n{Fore.GREEN}🎉 Scraping concluído com sucesso!")
    else:
        print(f"\n{Fore.RED}❌ Scraping falhou!")
    
    input(f"\n{Fore.GREEN}Pressione ENTER para finalizar...")

if __name__ == "__main__":
    asyncio.run(main())