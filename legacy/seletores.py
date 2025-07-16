"""
Teste específico para localização do iFood
"""
import asyncio
from playwright.async_api import async_playwright
from colorama import Fore

async def testar_localizacao():
    """Teste detalhado da seleção de localização"""
    print(f"{Fore.YELLOW}🧪 TESTE DE LOCALIZAÇÃO - IFOOD")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("🔗 Acessando iFood...")
            await page.goto("https://www.ifood.com.br")
            await asyncio.sleep(5)
            
            print("🔍 Procurando campo de endereço...")
            
            # Procurar campo de endereço
            campo_encontrado = False
            seletores = [
                "input[placeholder*='Endereço de entrega']",
                "input[placeholder*='endereço']",
                "input[placeholder*='Digite seu endereço']",
                "input[type='text']"
            ]
            
            for seletor in seletores:
                try:
                    campo = await page.wait_for_selector(seletor, timeout=3000)
                    if campo:
                        print(f"✅ Campo encontrado: {seletor}")
                        
                        # Clicar e digitar
                        await campo.click()
                        await asyncio.sleep(1)
                        await campo.fill("Birigui")
                        print("✅ Digitado: Birigui")
                        
                        campo_encontrado = True
                        break
                except:
                    continue
            
            if not campo_encontrado:
                print("❌ Campo de endereço não encontrado")
                await page.screenshot(path="debug_campo_nao_encontrado.png")
                return
            
            # Aguardar dropdown aparecer
            print("⏱️  Aguardando dropdown aparecer...")
            await asyncio.sleep(3)
            
            # Procurar opções no dropdown
            print("🔍 Procurando opções do dropdown...")
            
            # Tirar screenshot do estado atual
            await page.screenshot(path="debug_dropdown_estado.png")
            print("📸 Screenshot salvo: debug_dropdown_estado.png")
            
            # Listar todos os elementos visíveis que contêm "Birigui"
            elementos_birigui = await page.query_selector_all("*")
            opcoes_encontradas = []
            
            for elemento in elementos_birigui:
                try:
                    texto = await elemento.inner_text()
                    if texto and "Birigui" in texto:
                        # Verificar se é clicável
                        is_visible = await elemento.is_visible()
                        tag_name = await elemento.evaluate("el => el.tagName")
                        
                        if is_visible and len(texto.strip()) < 100:  # Evitar textos muito longos
                            opcoes_encontradas.append({
                                "texto": texto.strip(),
                                "tag": tag_name,
                                "elemento": elemento
                            })
                            print(f"📍 Encontrado: [{tag_name}] '{texto.strip()}'")
                except:
                    continue
            
            if opcoes_encontradas:
                print(f"\n✅ Total de {len(opcoes_encontradas)} opções encontradas!")
                
                # Tentar clicar na primeira opção que pareça mais adequada
                for i, opcao in enumerate(opcoes_encontradas):
                    if "SP" in opcao["texto"] and ("Brasil" in opcao["texto"] or "Brazil" in opcao["texto"]):
                        print(f"🎯 Tentando clicar na opção {i+1}: '{opcao['texto']}'")
                        try:
                            await opcao["elemento"].click()
                            print("✅ Clique realizado!")
                            await asyncio.sleep(2)
                            break
                        except Exception as e:
                            print(f"❌ Erro ao clicar: {e}")
                            continue
                
                # Se não encontrou uma boa opção, tentar a primeira
                if len(opcoes_encontradas) > 0:
                    print("🎯 Tentando primeira opção disponível...")
                    try:
                        await opcoes_encontradas[0]["elemento"].click()
                        print("✅ Primeira opção clicada!")
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"❌ Erro ao clicar na primeira opção: {e}")
            
            else:
                print("❌ Nenhuma opção encontrada no dropdown")
                
                # Tentar estratégia de teclado
                print("🎹 Tentando estratégia de teclado...")
                try:
                    await page.keyboard.press("ArrowDown")
                    await asyncio.sleep(0.5)
                    await page.keyboard.press("Enter")
                    print("✅ Enter pressionado!")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"❌ Erro com teclado: {e}")
            
            # Procurar botão de confirmar
            print("🔍 Procurando botão de confirmar...")
            botoes_confirmar = [
                "button:has-text('Confirmar localização')",
                "button:has-text('Confirmar')",
                "button:has-text('Salvar')",
                "[data-test*='confirm']"
            ]
            
            for seletor in botoes_confirmar:
                try:
                    botao = await page.wait_for_selector(seletor, timeout=3000)
                    if botao:
                        print(f"✅ Botão encontrado: {seletor}")
                        await botao.click()
                        print("✅ Botão clicado!")
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            # Screenshot final
            await page.screenshot(path="debug_final_localizacao.png")
            print("📸 Screenshot final: debug_final_localizacao.png")
            
            print("\n✅ Teste concluído!")
            
        except Exception as e:
            print(f"❌ Erro geral: {e}")
            await page.screenshot(path="debug_erro_localizacao.png")
        
        finally:
            input("\n⏸️  Pressione ENTER para fechar...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(testar_localizacao())