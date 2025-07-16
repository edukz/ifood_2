"""
Alternativa: Scraper com interação manual
Permite que o usuário configure a localização manualmente
"""
import asyncio
from playwright.async_api import async_playwright
import time
from colorama import Fore, Style

async def scraper_manual():
    """Scraper com configuração manual da localização"""
    print(f"{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
    print(f"{Fore.YELLOW}║             SCRAPER MANUAL - IFOOD CATEGORIAS            ║")
    print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
    
    print(f"\n{Fore.CYAN}📋 INSTRUÇÕES:")
    print(f"{Fore.WHITE}1. O navegador será aberto")
    print(f"{Fore.WHITE}2. Configure MANUALMENTE sua localização (Birigui)")
    print(f"{Fore.WHITE}3. Aguarde até ver as categorias na tela")
    print(f"{Fore.WHITE}4. Pressione ENTER no terminal quando estiver pronto")
    print(f"{Fore.WHITE}5. O script coletará as categorias automaticamente")
    
    input(f"\n{Fore.GREEN}Pressione ENTER para começar...")
    
    async with async_playwright() as p:
        print(f"\n{Fore.CYAN}🌐 Abrindo navegador...")
        
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            # Acessar iFood
            print(f"{Fore.CYAN}🔗 Acessando iFood...")
            await page.goto("https://www.ifood.com.br")
            
            print(f"\n{Fore.YELLOW}👆 AGORA É SUA VEZ!")
            print(f"{Fore.WHITE}Configure sua localização para: Birigui, SP")
            print(f"{Fore.WHITE}Aguarde as categorias aparecerem na tela")
            
            # Aguardar comando do usuário
            input(f"\n{Fore.GREEN}Pressione ENTER quando estiver pronto para coletar...")
            
            print(f"\n{Fore.CYAN}📂 Coletando categorias...")
            
            # Coletar todas as categorias possíveis
            categorias_encontradas = []
            
            # Múltiplos seletores para tentar encontrar categorias
            seletores = [
                "a[href*='/delivery/']",
                "a[href*='/restaurants/']", 
                "a[href*='/categoria/']",
                "a[href*='/category/']",
                ".category-card",
                ".category-item",
                "[data-test*='category']",
                ".restaurant-category",
                "div[class*='category'] a",
                "div[class*='Category'] a"
            ]
            
            for seletor in seletores:
                try:
                    elementos = await page.query_selector_all(seletor)
                    print(f"{Fore.WHITE}   Testando seletor: {seletor} -> {len(elementos)} encontrados")
                    
                    for elemento in elementos:
                        try:
                            texto = await elemento.inner_text()
                            href = await elemento.get_attribute("href")
                            
                            if texto and href and len(texto.strip()) > 1:
                                categoria = {
                                    "nome": texto.strip(),
                                    "link": href if href.startswith("http") else f"https://www.ifood.com.br{href}"
                                }
                                
                                # Evitar duplicatas
                                if categoria not in categorias_encontradas:
                                    categorias_encontradas.append(categoria)
                                    
                        except:
                            continue
                            
                except:
                    continue
            
            # Se não encontrou nada, tentar uma abordagem mais ampla
            if not categorias_encontradas:
                print(f"{Fore.YELLOW}   Tentando abordagem mais ampla...")
                
                todos_links = await page.query_selector_all("a[href]")
                print(f"{Fore.WHITE}   Total de links na página: {len(todos_links)}")
                
                for link in todos_links:
                    try:
                        texto = await link.inner_text()
                        href = await link.get_attribute("href")
                        
                        # Filtrar por palavras-chave que indicam categorias
                        palavras_categoria = [
                            "pizza", "hamburguer", "japonesa", "brasileira", 
                            "italiana", "chinese", "mexicana", "delivery",
                            "comida", "restaurante", "lanche", "doce"
                        ]
                        
                        if (texto and href and 
                            any(palavra in texto.lower() for palavra in palavras_categoria) and
                            len(texto.strip()) > 2 and len(texto.strip()) < 50):
                            
                            categoria = {
                                "nome": texto.strip(),
                                "link": href if href.startswith("http") else f"https://www.ifood.com.br{href}"
                            }
                            
                            if categoria not in categorias_encontradas:
                                categorias_encontradas.append(categoria)
                                
                    except:
                        continue
            
            # Remover duplicatas por nome
            categorias_unicas = []
            nomes_vistos = set()
            
            for cat in categorias_encontradas:
                if cat["nome"] not in nomes_vistos:
                    nomes_vistos.add(cat["nome"])
                    categorias_unicas.append(cat)
            
            # Mostrar resultados
            print(f"\n{Fore.GREEN}✅ Coleta concluída!")
            print(f"{Fore.WHITE}📊 Total de categorias encontradas: {len(categorias_unicas)}")
            
            if categorias_unicas:
                print(f"\n{Fore.CYAN}📋 CATEGORIAS COLETADAS:")
                for i, cat in enumerate(categorias_unicas, 1):
                    print(f"{Fore.WHITE}   [{i:2d}] {cat['nome']}")
                    print(f"{Fore.CYAN}       -> {cat['link']}")
                
                # Perguntar se quer salvar
                salvar = input(f"\n{Fore.YELLOW}Deseja salvar no banco de dados? (s/N): ").strip().lower()
                
                if salvar == 's':
                    # Importar e salvar
                    try:
                        import sys
                        sys.path.append('.')
                        from src.database.db_manager import DatabaseManager
                        
                        db = DatabaseManager()
                        conn = db._get_connection()
                        
                        # Limpar tabela
                        conn.execute("DELETE FROM categories")
                        
                        # Inserir categorias
                        for cat in categorias_unicas:
                            conn.execute("""
                                INSERT INTO categories (categorias, links) 
                                VALUES (?, ?)
                            """, [cat["nome"], cat["link"]])
                        
                        conn.commit()
                        conn.close()
                        
                        print(f"{Fore.GREEN}✅ Categorias salvas no banco de dados!")
                        
                    except Exception as e:
                        print(f"{Fore.RED}❌ Erro ao salvar: {str(e)}")
                
            else:
                print(f"{Fore.YELLOW}⚠️  Nenhuma categoria foi encontrada")
                
                # Tirar screenshot para análise
                await page.screenshot(path="debug_manual_final.png")
                print(f"{Fore.CYAN}📸 Screenshot salvo: debug_manual_final.png")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro: {str(e)}")
            await page.screenshot(path="debug_manual_error.png")
            
        finally:
            input(f"\n{Fore.GREEN}Pressione ENTER para fechar...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scraper_manual())