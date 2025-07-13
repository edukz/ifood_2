"""
Gerenciador de configurações
"""
import json
import os
import shutil
from pathlib import Path
from colorama import Fore
from src.utils.logger import get_logger

class ConfigManager:
    def __init__(self):
        self.logger = get_logger()
        self.config_file = os.path.join(os.path.dirname(__file__), 'settings.json')
        self.load_config()
    
    def load_config(self):
        """Carregar configurações"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = self.get_default_config()
            self.save_config()
    
    def save_config(self):
        """Salvar configurações"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def get_default_config(self):
        """Configurações padrão"""
        return {
            "regions": {
                "cities": ["São Paulo", "Rio de Janeiro"],
                "default_city": "São Paulo"
            },
            "scraping": {
                "request_interval": 2,  # segundos
                "timeout": 30,
                "max_retries": 3,
                "user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                ],
                "proxies": {
                    "enabled": False,
                    "list": [],
                    "rotation": "random"  # random, sequential
                }
            },
            "parallel": {
                "max_workers": 5,
                "checkpoint_interval": 100
            },
            "output": {
                "raw_data": "data/raw",
                "processed_data": "data/processed",
                "logs": "logs"
            }
        }
    
    def configure_regions(self):
        """Configurar regiões/cidades"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║            CONFIGURAR REGIÕES E CIDADES                  ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        while True:
            print(f"\n{Fore.CYAN}Cidades atuais:")
            for i, city in enumerate(self.config['regions']['cities'], 1):
                default_mark = " (PADRÃO)" if city == self.config['regions']['default_city'] else ""
                print(f"{Fore.WHITE}[{i}] {city}{default_mark}")
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Adicionar nova cidade")
            print(f"{Fore.WHITE}[2] Remover cidade")
            print(f"{Fore.WHITE}[3] Definir cidade padrão")
            print(f"{Fore.WHITE}[4] Editar cidade existente")
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._add_city()
            elif choice == "2":
                self._remove_city()
            elif choice == "3":
                self._set_default_city()
            elif choice == "4":
                self._edit_city()
            elif choice == "0":
                break
            else:
                print(f"{Fore.RED}Opção inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _add_city(self):
        """Adicionar nova cidade"""
        print(f"\n{Fore.YELLOW}ADICIONAR NOVA CIDADE")
        city = input(f"{Fore.WHITE}Nome da cidade: {Fore.GREEN}").strip()
        
        if not city:
            print(f"{Fore.RED}Nome da cidade não pode estar vazio!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        if city in self.config['regions']['cities']:
            print(f"{Fore.RED}Cidade '{city}' já existe na lista!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        self.config['regions']['cities'].append(city)
        self.save_config()
        print(f"{Fore.GREEN}Cidade '{city}' adicionada com sucesso!")
        
        if len(self.config['regions']['cities']) == 1:
            self.config['regions']['default_city'] = city
            self.save_config()
            print(f"{Fore.CYAN}'{city}' definida como cidade padrão (primeira cidade da lista).")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _remove_city(self):
        """Remover cidade"""
        if len(self.config['regions']['cities']) <= 1:
            print(f"{Fore.RED}Não é possível remover. Pelo menos uma cidade deve permanecer!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        print(f"\n{Fore.YELLOW}REMOVER CIDADE")
        print(f"{Fore.WHITE}Cidades disponíveis:")
        for i, city in enumerate(self.config['regions']['cities'], 1):
            print(f"[{i}] {city}")
        
        try:
            choice = int(input(f"{Fore.WHITE}Número da cidade a remover: {Fore.GREEN}"))
            if 1 <= choice <= len(self.config['regions']['cities']):
                city_to_remove = self.config['regions']['cities'][choice - 1]
                
                # Verificar se é a cidade padrão
                if city_to_remove == self.config['regions']['default_city']:
                    print(f"{Fore.YELLOW}Esta é a cidade padrão. Uma nova cidade padrão será definida automaticamente.")
                
                self.config['regions']['cities'].remove(city_to_remove)
                
                # Se removeu a cidade padrão, definir nova
                if city_to_remove == self.config['regions']['default_city']:
                    self.config['regions']['default_city'] = self.config['regions']['cities'][0]
                    print(f"{Fore.CYAN}Nova cidade padrão: {self.config['regions']['default_city']}")
                
                self.save_config()
                print(f"{Fore.GREEN}Cidade '{city_to_remove}' removida com sucesso!")
            else:
                print(f"{Fore.RED}Número inválido!")
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _set_default_city(self):
        """Definir cidade padrão"""
        print(f"\n{Fore.YELLOW}DEFINIR CIDADE PADRÃO")
        print(f"{Fore.WHITE}Cidades disponíveis:")
        for i, city in enumerate(self.config['regions']['cities'], 1):
            default_mark = " (ATUAL PADRÃO)" if city == self.config['regions']['default_city'] else ""
            print(f"[{i}] {city}{default_mark}")
        
        try:
            choice = int(input(f"{Fore.WHITE}Número da nova cidade padrão: {Fore.GREEN}"))
            if 1 <= choice <= len(self.config['regions']['cities']):
                new_default = self.config['regions']['cities'][choice - 1]
                self.config['regions']['default_city'] = new_default
                self.save_config()
                print(f"{Fore.GREEN}Cidade padrão alterada para: {new_default}")
            else:
                print(f"{Fore.RED}Número inválido!")
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _edit_city(self):
        """Editar cidade existente"""
        print(f"\n{Fore.YELLOW}EDITAR CIDADE")
        print(f"{Fore.WHITE}Cidades disponíveis:")
        for i, city in enumerate(self.config['regions']['cities'], 1):
            print(f"[{i}] {city}")
        
        try:
            choice = int(input(f"{Fore.WHITE}Número da cidade a editar: {Fore.GREEN}"))
            if 1 <= choice <= len(self.config['regions']['cities']):
                old_city = self.config['regions']['cities'][choice - 1]
                new_city = input(f"{Fore.WHITE}Novo nome para '{old_city}': {Fore.GREEN}").strip()
                
                if not new_city:
                    print(f"{Fore.RED}Nome da cidade não pode estar vazio!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    return
                
                if new_city in self.config['regions']['cities']:
                    print(f"{Fore.RED}Cidade '{new_city}' já existe na lista!")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    return
                
                # Atualizar na lista
                self.config['regions']['cities'][choice - 1] = new_city
                
                # Se era a cidade padrão, atualizar também
                if old_city == self.config['regions']['default_city']:
                    self.config['regions']['default_city'] = new_city
                
                self.save_config()
                print(f"{Fore.GREEN}Cidade alterada de '{old_city}' para '{new_city}'!")
            else:
                print(f"{Fore.RED}Número inválido!")
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def configure_intervals(self):
        """Configurar intervalos entre requests"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║           CONFIGURAR INTERVALOS ENTRE REQUESTS          ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        while True:
            current_interval = self.config['scraping']['request_interval']
            
            print(f"\n{Fore.CYAN}CONFIGURAÇÃO ATUAL:")
            print(f"{Fore.WHITE}Intervalo entre requests: {current_interval} segundos")
            
            # Calcular estatísticas úteis
            requests_per_minute = 60 / current_interval if current_interval > 0 else float('inf')
            requests_per_hour = requests_per_minute * 60
            
            print(f"{Fore.CYAN}ESTATÍSTICAS:")
            print(f"{Fore.WHITE}• Requests por minuto: {requests_per_minute:.1f}")
            print(f"{Fore.WHITE}• Requests por hora: {requests_per_hour:.0f}")
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Definir intervalo personalizado")
            print(f"{Fore.WHITE}[2] Usar preset conservador (5s)")
            print(f"{Fore.WHITE}[3] Usar preset moderado (2s)")
            print(f"{Fore.WHITE}[4] Usar preset agressivo (1s)")
            print(f"{Fore.WHITE}[5] Usar preset muito agressivo (0.5s)")
            print(f"{Fore.WHITE}[0] Voltar")
            
            print(f"\n{Fore.RED}⚠️  ATENÇÃO:")
            print(f"{Fore.YELLOW}• Intervalos muito baixos podem sobrecarregar o servidor")
            print(f"{Fore.YELLOW}• Use intervalos maiores para evitar bloqueios")
            print(f"{Fore.YELLOW}• Recomendado: 2-5 segundos para uso seguro")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._set_custom_interval()
            elif choice == "2":
                self._set_preset_interval(5, "conservador")
            elif choice == "3":
                self._set_preset_interval(2, "moderado")
            elif choice == "4":
                self._set_preset_interval(1, "agressivo")
            elif choice == "5":
                self._set_preset_interval(0.5, "muito agressivo")
            elif choice == "0":
                break
            else:
                print(f"{Fore.RED}Opção inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _set_custom_interval(self):
        """Definir intervalo personalizado"""
        print(f"\n{Fore.YELLOW}DEFINIR INTERVALO PERSONALIZADO")
        print(f"{Fore.WHITE}Intervalo atual: {self.config['scraping']['request_interval']}s")
        
        try:
            interval_input = input(f"{Fore.WHITE}Novo intervalo (em segundos): {Fore.GREEN}")
            interval = float(interval_input)
            
            if interval < 0:
                print(f"{Fore.RED}Intervalo não pode ser negativo!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            if interval < 0.1:
                print(f"{Fore.RED}⚠️  ATENÇÃO: Intervalo muito baixo!")
                print(f"{Fore.YELLOW}Intervalos menores que 0.1s podem causar problemas.")
                confirm = input(f"{Fore.WHITE}Continuar mesmo assim? (s/N): {Fore.GREEN}").strip().lower()
                if confirm != 's':
                    print(f"{Fore.CYAN}Operação cancelada.")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    return
            
            elif interval < 1:
                print(f"{Fore.YELLOW}⚠️  Intervalo baixo - use com cuidado para evitar bloqueios.")
                confirm = input(f"{Fore.WHITE}Confirmar intervalo de {interval}s? (s/N): {Fore.GREEN}").strip().lower()
                if confirm != 's':
                    print(f"{Fore.CYAN}Operação cancelada.")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    return
            
            old_interval = self.config['scraping']['request_interval']
            self.config['scraping']['request_interval'] = interval
            self.save_config()
            
            print(f"{Fore.GREEN}✅ Intervalo alterado de {old_interval}s para {interval}s")
            
            # Mostrar nova estatística
            requests_per_minute = 60 / interval if interval > 0 else float('inf')
            print(f"{Fore.CYAN}Nova taxa: {requests_per_minute:.1f} requests/minuto")
            
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _set_preset_interval(self, interval, preset_name):
        """Definir intervalo usando preset"""
        print(f"\n{Fore.YELLOW}APLICAR PRESET {preset_name.upper()}")
        
        old_interval = self.config['scraping']['request_interval']
        
        if interval < 1:
            print(f"{Fore.YELLOW}⚠️  Preset '{preset_name}' usa intervalo baixo ({interval}s)")
            print(f"{Fore.YELLOW}Use com cuidado para evitar bloqueios.")
            confirm = input(f"{Fore.WHITE}Aplicar preset '{preset_name}'? (s/N): {Fore.GREEN}").strip().lower()
            if confirm != 's':
                print(f"{Fore.CYAN}Operação cancelada.")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
        
        self.config['scraping']['request_interval'] = interval
        self.save_config()
        
        print(f"{Fore.GREEN}✅ Preset '{preset_name}' aplicado!")
        print(f"{Fore.WHITE}Intervalo alterado de {old_interval}s para {interval}s")
        
        # Mostrar estatísticas
        requests_per_minute = 60 / interval if interval > 0 else float('inf')
        requests_per_hour = requests_per_minute * 60
        print(f"{Fore.CYAN}Taxa: {requests_per_minute:.1f} requests/minuto ({requests_per_hour:.0f}/hora)")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def configure_proxies(self):
        """Configurar proxies e user agents"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║           CONFIGURAR PROXIES E USER AGENTS              ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        # Verificar se existe a seção proxies, se não, criar
        if "proxies" not in self.config["scraping"]:
            self.config["scraping"]["proxies"] = {
                "enabled": False,
                "list": [],
                "rotation": "random"
            }
            self.save_config()
        
        while True:
            proxies_enabled = self.config["scraping"]["proxies"]["enabled"]
            proxy_count = len(self.config["scraping"]["proxies"]["list"])
            user_agent_count = len(self.config["scraping"]["user_agents"])
            rotation_mode = self.config["scraping"]["proxies"]["rotation"]
            
            print(f"\n{Fore.CYAN}STATUS ATUAL:")
            print(f"{Fore.WHITE}• Proxies: {'ATIVADOS' if proxies_enabled else 'DESATIVADOS'}")
            print(f"{Fore.WHITE}• Proxies cadastrados: {proxy_count}")
            print(f"{Fore.WHITE}• Modo de rotação: {rotation_mode}")
            print(f"{Fore.WHITE}• User agents cadastrados: {user_agent_count}")
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Gerenciar proxies")
            print(f"{Fore.WHITE}[2] Gerenciar user agents")
            print(f"{Fore.WHITE}[3] {'Desativar' if proxies_enabled else 'Ativar'} uso de proxies")
            print(f"{Fore.WHITE}[4] Configurar modo de rotação de proxies")
            print(f"{Fore.WHITE}[5] Testar proxy específico")
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._manage_proxies()
            elif choice == "2":
                self._manage_user_agents()
            elif choice == "3":
                self._toggle_proxies()
            elif choice == "4":
                self._configure_proxy_rotation()
            elif choice == "5":
                self._test_proxy()
            elif choice == "0":
                break
            else:
                print(f"{Fore.RED}Opção inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _manage_proxies(self):
        """Gerenciar lista de proxies"""
        while True:
            proxies = self.config["scraping"]["proxies"]["list"]
            
            print(f"\n{Fore.YELLOW}GERENCIAR PROXIES")
            print(f"\n{Fore.CYAN}Proxies cadastrados ({len(proxies)}):")
            
            if not proxies:
                print(f"{Fore.WHITE}Nenhum proxy cadastrado.")
            else:
                for i, proxy in enumerate(proxies, 1):
                    print(f"{Fore.WHITE}[{i}] {proxy}")
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Adicionar proxy")
            print(f"{Fore.WHITE}[2] Remover proxy")
            print(f"{Fore.WHITE}[3] Limpar todos os proxies")
            print(f"{Fore.WHITE}[4] Importar proxies de arquivo")
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._add_proxy()
            elif choice == "2":
                self._remove_proxy()
            elif choice == "3":
                self._clear_proxies()
            elif choice == "4":
                self._import_proxies()
            elif choice == "0":
                break
            else:
                print(f"{Fore.RED}Opção inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _add_proxy(self):
        """Adicionar novo proxy"""
        print(f"\n{Fore.YELLOW}ADICIONAR PROXY")
        print(f"{Fore.CYAN}Formatos aceitos:")
        print(f"{Fore.WHITE}• http://ip:porta")
        print(f"{Fore.WHITE}• https://ip:porta")
        print(f"{Fore.WHITE}• socks5://ip:porta")
        print(f"{Fore.WHITE}• http://usuario:senha@ip:porta")
        
        proxy = input(f"\n{Fore.WHITE}Digite o proxy: {Fore.GREEN}").strip()
        
        if not proxy:
            print(f"{Fore.RED}Proxy não pode estar vazio!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        if proxy in self.config["scraping"]["proxies"]["list"]:
            print(f"{Fore.RED}Proxy já existe na lista!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        # Validação básica do formato
        if not any(proxy.startswith(protocol) for protocol in ["http://", "https://", "socks5://"]):
            print(f"{Fore.RED}Formato inválido! Use http://, https:// ou socks5://")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        self.config["scraping"]["proxies"]["list"].append(proxy)
        self.save_config()
        print(f"{Fore.GREEN}Proxy adicionado com sucesso!")
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _remove_proxy(self):
        """Remover proxy"""
        proxies = self.config["scraping"]["proxies"]["list"]
        
        if not proxies:
            print(f"\n{Fore.RED}Nenhum proxy para remover!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        print(f"\n{Fore.YELLOW}REMOVER PROXY")
        for i, proxy in enumerate(proxies, 1):
            print(f"{Fore.WHITE}[{i}] {proxy}")
        
        try:
            choice = int(input(f"\n{Fore.WHITE}Número do proxy a remover: {Fore.GREEN}"))
            if 1 <= choice <= len(proxies):
                removed_proxy = proxies.pop(choice - 1)
                self.save_config()
                print(f"{Fore.GREEN}Proxy '{removed_proxy}' removido!")
            else:
                print(f"{Fore.RED}Número inválido!")
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _clear_proxies(self):
        """Limpar todos os proxies"""
        proxies_count = len(self.config["scraping"]["proxies"]["list"])
        
        if proxies_count == 0:
            print(f"\n{Fore.YELLOW}Nenhum proxy para limpar!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        print(f"\n{Fore.YELLOW}LIMPAR TODOS OS PROXIES")
        print(f"{Fore.WHITE}Isso removerá todos os {proxies_count} proxies cadastrados.")
        confirm = input(f"{Fore.RED}Confirma? (s/N): {Fore.GREEN}").strip().lower()
        
        if confirm == 's':
            self.config["scraping"]["proxies"]["list"] = []
            self.save_config()
            print(f"{Fore.GREEN}Todos os proxies foram removidos!")
        else:
            print(f"{Fore.CYAN}Operação cancelada.")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _import_proxies(self):
        """Importar proxies de arquivo"""
        print(f"\n{Fore.YELLOW}IMPORTAR PROXIES DE ARQUIVO")
        print(f"{Fore.WHITE}O arquivo deve conter um proxy por linha.")
        
        filename = input(f"{Fore.WHITE}Nome do arquivo: {Fore.GREEN}").strip()
        
        if not filename:
            print(f"{Fore.RED}Nome do arquivo não pode estar vazio!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            imported = 0
            duplicated = 0
            invalid = 0
            
            for line in lines:
                proxy = line.strip()
                if not proxy or proxy.startswith('#'):
                    continue
                
                if not any(proxy.startswith(protocol) for protocol in ["http://", "https://", "socks5://"]):
                    invalid += 1
                    continue
                
                if proxy in self.config["scraping"]["proxies"]["list"]:
                    duplicated += 1
                    continue
                
                self.config["scraping"]["proxies"]["list"].append(proxy)
                imported += 1
            
            self.save_config()
            
            print(f"{Fore.GREEN}Importação concluída!")
            print(f"{Fore.WHITE}• Importados: {imported}")
            print(f"{Fore.YELLOW}• Duplicados: {duplicated}")
            print(f"{Fore.RED}• Inválidos: {invalid}")
            
        except FileNotFoundError:
            print(f"{Fore.RED}Arquivo '{filename}' não encontrado!")
        except Exception as e:
            print(f"{Fore.RED}Erro ao ler arquivo: {e}")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _manage_user_agents(self):
        """Gerenciar lista de user agents"""
        while True:
            user_agents = self.config["scraping"]["user_agents"]
            
            print(f"\n{Fore.YELLOW}GERENCIAR USER AGENTS")
            print(f"\n{Fore.CYAN}User agents cadastrados ({len(user_agents)}):")
            
            for i, ua in enumerate(user_agents, 1):
                ua_short = ua[:60] + "..." if len(ua) > 60 else ua
                print(f"{Fore.WHITE}[{i}] {ua_short}")
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Adicionar user agent")
            print(f"{Fore.WHITE}[2] Remover user agent")
            print(f"{Fore.WHITE}[3] Ver user agent completo")
            print(f"{Fore.WHITE}[4] Adicionar presets populares")
            print(f"{Fore.WHITE}[5] Limpar todos os user agents")
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._add_user_agent()
            elif choice == "2":
                self._remove_user_agent()
            elif choice == "3":
                self._view_user_agent()
            elif choice == "4":
                self._add_popular_user_agents()
            elif choice == "5":
                self._clear_user_agents()
            elif choice == "0":
                break
            else:
                print(f"{Fore.RED}Opção inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _add_user_agent(self):
        """Adicionar novo user agent"""
        print(f"\n{Fore.YELLOW}ADICIONAR USER AGENT")
        ua = input(f"{Fore.WHITE}Digite o user agent: {Fore.GREEN}").strip()
        
        if not ua:
            print(f"{Fore.RED}User agent não pode estar vazio!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        if ua in self.config["scraping"]["user_agents"]:
            print(f"{Fore.RED}User agent já existe na lista!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        self.config["scraping"]["user_agents"].append(ua)
        self.save_config()
        print(f"{Fore.GREEN}User agent adicionado com sucesso!")
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _remove_user_agent(self):
        """Remover user agent"""
        user_agents = self.config["scraping"]["user_agents"]
        
        if len(user_agents) <= 1:
            print(f"\n{Fore.RED}Não é possível remover. Pelo menos um user agent deve permanecer!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        print(f"\n{Fore.YELLOW}REMOVER USER AGENT")
        for i, ua in enumerate(user_agents, 1):
            ua_short = ua[:60] + "..." if len(ua) > 60 else ua
            print(f"{Fore.WHITE}[{i}] {ua_short}")
        
        try:
            choice = int(input(f"\n{Fore.WHITE}Número do user agent a remover: {Fore.GREEN}"))
            if 1 <= choice <= len(user_agents):
                removed_ua = user_agents.pop(choice - 1)
                self.save_config()
                print(f"{Fore.GREEN}User agent removido!")
            else:
                print(f"{Fore.RED}Número inválido!")
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _view_user_agent(self):
        """Ver user agent completo"""
        user_agents = self.config["scraping"]["user_agents"]
        
        print(f"\n{Fore.YELLOW}VER USER AGENT COMPLETO")
        for i, ua in enumerate(user_agents, 1):
            ua_short = ua[:60] + "..." if len(ua) > 60 else ua
            print(f"{Fore.WHITE}[{i}] {ua_short}")
        
        try:
            choice = int(input(f"\n{Fore.WHITE}Número do user agent: {Fore.GREEN}"))
            if 1 <= choice <= len(user_agents):
                print(f"\n{Fore.CYAN}User Agent completo:")
                print(f"{Fore.WHITE}{user_agents[choice - 1]}")
            else:
                print(f"{Fore.RED}Número inválido!")
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _add_popular_user_agents(self):
        """Adicionar user agents populares"""
        print(f"\n{Fore.YELLOW}ADICIONAR PRESETS POPULARES")
        
        popular_uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        
        added = 0
        for ua in popular_uas:
            if ua not in self.config["scraping"]["user_agents"]:
                self.config["scraping"]["user_agents"].append(ua)
                added += 1
        
        self.save_config()
        print(f"{Fore.GREEN}{added} user agents populares foram adicionados!")
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _clear_user_agents(self):
        """Limpar todos os user agents"""
        ua_count = len(self.config["scraping"]["user_agents"])
        
        print(f"\n{Fore.YELLOW}LIMPAR TODOS OS USER AGENTS")
        print(f"{Fore.WHITE}Isso removerá todos os {ua_count} user agents e adicionará um padrão.")
        confirm = input(f"{Fore.RED}Confirma? (s/N): {Fore.GREEN}").strip().lower()
        
        if confirm == 's':
            self.config["scraping"]["user_agents"] = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            self.save_config()
            print(f"{Fore.GREEN}User agents limpos e um padrão foi adicionado!")
        else:
            print(f"{Fore.CYAN}Operação cancelada.")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _toggle_proxies(self):
        """Ativar/desativar uso de proxies"""
        current_status = self.config["scraping"]["proxies"]["enabled"]
        new_status = not current_status
        
        print(f"\n{Fore.YELLOW}{'DESATIVAR' if current_status else 'ATIVAR'} PROXIES")
        
        if new_status and len(self.config["scraping"]["proxies"]["list"]) == 0:
            print(f"{Fore.RED}Não é possível ativar proxies sem ter proxies cadastrados!")
            print(f"{Fore.YELLOW}Adicione proxies primeiro na opção 'Gerenciar proxies'.")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        self.config["scraping"]["proxies"]["enabled"] = new_status
        self.save_config()
        
        status_text = "ATIVADOS" if new_status else "DESATIVADOS"
        print(f"{Fore.GREEN}Proxies {status_text} com sucesso!")
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _configure_proxy_rotation(self):
        """Configurar modo de rotação de proxies"""
        current_mode = self.config["scraping"]["proxies"]["rotation"]
        
        print(f"\n{Fore.YELLOW}CONFIGURAR ROTAÇÃO DE PROXIES")
        print(f"{Fore.WHITE}Modo atual: {current_mode}")
        
        print(f"\n{Fore.CYAN}Modos disponíveis:")
        print(f"{Fore.WHITE}[1] Random - Seleciona proxy aleatório a cada request")
        print(f"{Fore.WHITE}[2] Sequential - Usa proxies em sequência")
        
        choice = input(f"\n{Fore.GREEN}Escolha o modo (1-2): {Fore.WHITE}").strip()
        
        if choice == "1":
            new_mode = "random"
        elif choice == "2":
            new_mode = "sequential"
        else:
            print(f"{Fore.RED}Opção inválida!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        self.config["scraping"]["proxies"]["rotation"] = new_mode
        self.save_config()
        print(f"{Fore.GREEN}Modo de rotação alterado para: {new_mode}")
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _test_proxy(self):
        """Testar proxy específico"""
        proxies = self.config["scraping"]["proxies"]["list"]
        
        if not proxies:
            print(f"\n{Fore.RED}Nenhum proxy cadastrado para testar!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        print(f"\n{Fore.YELLOW}TESTAR PROXY")
        for i, proxy in enumerate(proxies, 1):
            print(f"{Fore.WHITE}[{i}] {proxy}")
        
        try:
            choice = int(input(f"\n{Fore.WHITE}Número do proxy a testar: {Fore.GREEN}"))
            if 1 <= choice <= len(proxies):
                proxy = proxies[choice - 1]
                print(f"\n{Fore.CYAN}Testando proxy: {proxy}")
                print(f"{Fore.YELLOW}Função de teste não implementada ainda.")
                print(f"{Fore.WHITE}Em uma implementação real, faria uma requisição HTTP de teste.")
            else:
                print(f"{Fore.RED}Número inválido!")
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def configure_timeouts(self):
        """Ajustar timeouts e retries"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║            CONFIGURAR TIMEOUTS E RETRIES                ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        while True:
            current_timeout = self.config['scraping']['timeout']
            current_retries = self.config['scraping']['max_retries']
            
            print(f"\n{Fore.CYAN}CONFIGURAÇÕES ATUAIS:")
            print(f"{Fore.WHITE}• Timeout: {current_timeout} segundos")
            print(f"{Fore.WHITE}• Máximo de tentativas: {current_retries}")
            
            # Calcular tempo total máximo
            max_time_per_request = current_timeout * (current_retries + 1)
            print(f"{Fore.CYAN}• Tempo máximo por request: {max_time_per_request}s")
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Configurar timeout")
            print(f"{Fore.WHITE}[2] Configurar máximo de tentativas")
            print(f"{Fore.WHITE}[3] Usar preset conservador (60s, 5 tentativas)")
            print(f"{Fore.WHITE}[4] Usar preset moderado (30s, 3 tentativas)")
            print(f"{Fore.WHITE}[5] Usar preset agressivo (15s, 2 tentativas)")
            print(f"{Fore.WHITE}[6] Usar preset rápido (10s, 1 tentativa)")
            print(f"{Fore.WHITE}[0] Voltar")
            
            print(f"\n{Fore.CYAN}ℹ️  INFORMAÇÕES:")
            print(f"{Fore.WHITE}• Timeout: tempo limite para cada tentativa")
            print(f"{Fore.WHITE}• Retries: tentativas adicionais após falha")
            print(f"{Fore.WHITE}• Total de tentativas = retries + 1")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._configure_timeout()
            elif choice == "2":
                self._configure_retries()
            elif choice == "3":
                self._set_timeout_preset(60, 5, "conservador")
            elif choice == "4":
                self._set_timeout_preset(30, 3, "moderado")
            elif choice == "5":
                self._set_timeout_preset(15, 2, "agressivo")
            elif choice == "6":
                self._set_timeout_preset(10, 1, "rápido")
            elif choice == "0":
                break
            else:
                print(f"{Fore.RED}Opção inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _configure_timeout(self):
        """Configurar timeout personalizado"""
        print(f"\n{Fore.YELLOW}CONFIGURAR TIMEOUT")
        print(f"{Fore.WHITE}Timeout atual: {self.config['scraping']['timeout']}s")
        
        print(f"\n{Fore.CYAN}RECOMENDAÇÕES:")
        print(f"{Fore.WHITE}• 10-15s: Para conexões rápidas/locais")
        print(f"{Fore.WHITE}• 30s: Valor equilibrado (recomendado)")
        print(f"{Fore.WHITE}• 60s+: Para conexões lentas/instáveis")
        
        try:
            timeout_input = input(f"\n{Fore.WHITE}Novo timeout (em segundos): {Fore.GREEN}")
            timeout = float(timeout_input)
            
            if timeout <= 0:
                print(f"{Fore.RED}Timeout deve ser maior que zero!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            if timeout < 5:
                print(f"{Fore.YELLOW}⚠️  Timeout muito baixo pode causar falhas!")
                confirm = input(f"{Fore.WHITE}Continuar com {timeout}s? (s/N): {Fore.GREEN}").strip().lower()
                if confirm != 's':
                    print(f"{Fore.CYAN}Operação cancelada.")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    return
            
            elif timeout > 120:
                print(f"{Fore.YELLOW}⚠️  Timeout muito alto pode deixar o scraping lento.")
                confirm = input(f"{Fore.WHITE}Continuar com {timeout}s? (s/N): {Fore.GREEN}").strip().lower()
                if confirm != 's':
                    print(f"{Fore.CYAN}Operação cancelada.")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    return
            
            old_timeout = self.config['scraping']['timeout']
            self.config['scraping']['timeout'] = timeout
            self.save_config()
            
            print(f"{Fore.GREEN}✅ Timeout alterado de {old_timeout}s para {timeout}s")
            
            # Mostrar impacto
            retries = self.config['scraping']['max_retries']
            max_time = timeout * (retries + 1)
            print(f"{Fore.CYAN}Tempo máximo por request: {max_time}s")
            
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _configure_retries(self):
        """Configurar número máximo de tentativas"""
        print(f"\n{Fore.YELLOW}CONFIGURAR MÁXIMO DE TENTATIVAS")
        print(f"{Fore.WHITE}Tentativas atuais: {self.config['scraping']['max_retries']}")
        
        print(f"\n{Fore.CYAN}RECOMENDAÇÕES:")
        print(f"{Fore.WHITE}• 0-1: Para testes rápidos")
        print(f"{Fore.WHITE}• 2-3: Valor equilibrado (recomendado)")
        print(f"{Fore.WHITE}• 4-5: Para conexões instáveis")
        print(f"{Fore.WHITE}• 6+: Apenas para casos especiais")
        
        try:
            retries_input = input(f"\n{Fore.WHITE}Novo número de tentativas (0-10): {Fore.GREEN}")
            retries = int(retries_input)
            
            if retries < 0:
                print(f"{Fore.RED}Número de tentativas não pode ser negativo!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            if retries > 10:
                print(f"{Fore.RED}Número muito alto! Máximo permitido: 10")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
            
            if retries == 0:
                print(f"{Fore.YELLOW}⚠️  Com 0 tentativas, falhas não serão recuperadas.")
                confirm = input(f"{Fore.WHITE}Continuar? (s/N): {Fore.GREEN}").strip().lower()
                if confirm != 's':
                    print(f"{Fore.CYAN}Operação cancelada.")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    return
            
            elif retries > 5:
                print(f"{Fore.YELLOW}⚠️  Muitas tentativas podem deixar o scraping lento.")
                confirm = input(f"{Fore.WHITE}Continuar com {retries} tentativas? (s/N): {Fore.GREEN}").strip().lower()
                if confirm != 's':
                    print(f"{Fore.CYAN}Operação cancelada.")
                    input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                    return
            
            old_retries = self.config['scraping']['max_retries']
            self.config['scraping']['max_retries'] = retries
            self.save_config()
            
            print(f"{Fore.GREEN}✅ Tentativas alteradas de {old_retries} para {retries}")
            
            # Mostrar impacto
            timeout = self.config['scraping']['timeout']
            max_time = timeout * (retries + 1)
            total_attempts = retries + 1
            print(f"{Fore.CYAN}Total de tentativas por request: {total_attempts}")
            print(f"{Fore.CYAN}Tempo máximo por request: {max_time}s")
            
        except ValueError:
            print(f"{Fore.RED}Por favor, digite um número válido!")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _set_timeout_preset(self, timeout, retries, preset_name):
        """Aplicar preset de timeout e retries"""
        print(f"\n{Fore.YELLOW}APLICAR PRESET {preset_name.upper()}")
        
        old_timeout = self.config['scraping']['timeout']
        old_retries = self.config['scraping']['max_retries']
        
        max_time = timeout * (retries + 1)
        total_attempts = retries + 1
        
        print(f"{Fore.WHITE}Configurações do preset '{preset_name}':")
        print(f"{Fore.CYAN}• Timeout: {timeout}s")
        print(f"{Fore.CYAN}• Tentativas: {retries}")
        print(f"{Fore.CYAN}• Total de tentativas: {total_attempts}")
        print(f"{Fore.CYAN}• Tempo máximo por request: {max_time}s")
        
        confirm = input(f"\n{Fore.WHITE}Aplicar preset '{preset_name}'? (s/N): {Fore.GREEN}").strip().lower()
        if confirm != 's':
            print(f"{Fore.CYAN}Operação cancelada.")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        self.config['scraping']['timeout'] = timeout
        self.config['scraping']['max_retries'] = retries
        self.save_config()
        
        print(f"{Fore.GREEN}✅ Preset '{preset_name}' aplicado!")
        print(f"{Fore.WHITE}Timeout: {old_timeout}s → {timeout}s")
        print(f"{Fore.WHITE}Tentativas: {old_retries} → {retries}")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def configure_paths(self):
        """Configurar paths de output"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║              CONFIGURAR PATHS DE OUTPUT                 ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        while True:
            raw_path = self.config['output']['raw_data']
            processed_path = self.config['output']['processed_data']
            logs_path = self.config['output']['logs']
            
            print(f"\n{Fore.CYAN}PATHS ATUAIS:")
            print(f"{Fore.WHITE}[1] Dados brutos: {raw_path}")
            self._show_path_status(raw_path)
            
            print(f"\n{Fore.WHITE}[2] Dados processados: {processed_path}")
            self._show_path_status(processed_path)
            
            print(f"\n{Fore.WHITE}[3] Logs: {logs_path}")
            self._show_path_status(logs_path)
            
            print(f"\n{Fore.YELLOW}OPÇÕES:")
            print(f"{Fore.WHITE}[1] Configurar path de dados brutos")
            print(f"{Fore.WHITE}[2] Configurar path de dados processados")
            print(f"{Fore.WHITE}[3] Configurar path de logs")
            print(f"{Fore.WHITE}[4] Criar todos os diretórios")
            print(f"{Fore.WHITE}[5] Ver tamanho dos diretórios")
            print(f"{Fore.WHITE}[6] Limpar diretório específico")
            print(f"{Fore.WHITE}[7] Resetar paths padrão")
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._configure_path("raw_data", "dados brutos")
            elif choice == "2":
                self._configure_path("processed_data", "dados processados")
            elif choice == "3":
                self._configure_path("logs", "logs")
            elif choice == "4":
                self._create_all_directories()
            elif choice == "5":
                self._show_directory_sizes()
            elif choice == "6":
                self._clear_directory()
            elif choice == "7":
                self._reset_paths_to_default()
            elif choice == "0":
                break
            else:
                print(f"{Fore.RED}Opção inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_path_status(self, path):
        """Mostrar status do path"""
        full_path = Path(path)
        if full_path.exists():
            if full_path.is_dir():
                files_count = len(list(full_path.glob("*")))
                size = self._get_directory_size(full_path)
                print(f"{Fore.GREEN}   ✓ Existe ({files_count} arquivos, {self._format_size(size)})")
            else:
                print(f"{Fore.YELLOW}   ⚠ É um arquivo, não diretório")
        else:
            print(f"{Fore.RED}   ✗ Não existe")
    
    def _get_directory_size(self, path):
        """Calcular tamanho total do diretório"""
        total = 0
        try:
            for entry in Path(path).rglob("*"):
                if entry.is_file():
                    total += entry.stat().st_size
        except:
            pass
        return total
    
    def _format_size(self, size):
        """Formatar tamanho em bytes para formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"
    
    def _configure_path(self, path_key, path_name):
        """Configurar um path específico"""
        current_path = self.config['output'][path_key]
        
        print(f"\n{Fore.YELLOW}CONFIGURAR PATH DE {path_name.upper()}")
        print(f"{Fore.WHITE}Path atual: {current_path}")
        
        print(f"\n{Fore.CYAN}DICAS:")
        print(f"{Fore.WHITE}• Use paths relativos para portabilidade")
        print(f"{Fore.WHITE}• Use / como separador (funciona em todos OS)")
        print(f"{Fore.WHITE}• Evite espaços no nome de diretórios")
        
        new_path = input(f"\n{Fore.WHITE}Novo path (vazio para manter atual): {Fore.GREEN}").strip()
        
        if not new_path:
            print(f"{Fore.CYAN}Path mantido sem alterações.")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        # Validar path
        if any(char in new_path for char in ['<', '>', ':', '"', '|', '?', '*']):
            print(f"{Fore.RED}Path contém caracteres inválidos!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        # Verificar se é path absoluto
        if Path(new_path).is_absolute():
            print(f"{Fore.YELLOW}⚠️  Usar path absoluto pode causar problemas de portabilidade.")
            confirm = input(f"{Fore.WHITE}Continuar? (s/N): {Fore.GREEN}").strip().lower()
            if confirm != 's':
                print(f"{Fore.CYAN}Operação cancelada.")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
                return
        
        # Atualizar configuração
        self.config['output'][path_key] = new_path
        self.save_config()
        
        print(f"{Fore.GREEN}✅ Path de {path_name} alterado para: {new_path}")
        
        # Perguntar se deseja criar o diretório
        if not Path(new_path).exists():
            create = input(f"{Fore.YELLOW}Diretório não existe. Criar agora? (S/n): {Fore.GREEN}").strip().lower()
            if create != 'n':
                self._create_directory(new_path)
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _create_directory(self, path):
        """Criar um diretório"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            print(f"{Fore.GREEN}✅ Diretório criado: {path}")
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao criar diretório: {e}")
    
    def _create_all_directories(self):
        """Criar todos os diretórios configurados"""
        print(f"\n{Fore.YELLOW}CRIAR TODOS OS DIRETÓRIOS")
        
        paths = [
            (self.config['output']['raw_data'], "dados brutos"),
            (self.config['output']['processed_data'], "dados processados"),
            (self.config['output']['logs'], "logs")
        ]
        
        created = 0
        existed = 0
        errors = 0
        
        for path, name in paths:
            try:
                if Path(path).exists():
                    print(f"{Fore.CYAN}• {name}: já existe")
                    existed += 1
                else:
                    Path(path).mkdir(parents=True, exist_ok=True)
                    print(f"{Fore.GREEN}• {name}: criado com sucesso")
                    created += 1
            except Exception as e:
                print(f"{Fore.RED}• {name}: erro - {e}")
                errors += 1
        
        print(f"\n{Fore.CYAN}RESUMO:")
        print(f"{Fore.GREEN}• Criados: {created}")
        print(f"{Fore.CYAN}• Já existentes: {existed}")
        if errors > 0:
            print(f"{Fore.RED}• Erros: {errors}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_directory_sizes(self):
        """Mostrar tamanho dos diretórios"""
        print(f"\n{Fore.YELLOW}TAMANHO DOS DIRETÓRIOS")
        
        paths = [
            (self.config['output']['raw_data'], "Dados brutos"),
            (self.config['output']['processed_data'], "Dados processados"),
            (self.config['output']['logs'], "Logs")
        ]
        
        total_size = 0
        
        for path, name in paths:
            if Path(path).exists():
                size = self._get_directory_size(path)
                total_size += size
                files_count = len(list(Path(path).rglob("*")))
                print(f"\n{Fore.WHITE}{name}:")
                print(f"{Fore.CYAN}  Path: {path}")
                print(f"{Fore.CYAN}  Arquivos: {files_count}")
                print(f"{Fore.CYAN}  Tamanho: {self._format_size(size)}")
            else:
                print(f"\n{Fore.WHITE}{name}:")
                print(f"{Fore.RED}  Diretório não existe: {path}")
        
        print(f"\n{Fore.YELLOW}TOTAL: {self._format_size(total_size)}")
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _clear_directory(self):
        """Limpar diretório específico"""
        print(f"\n{Fore.YELLOW}LIMPAR DIRETÓRIO")
        
        print(f"{Fore.WHITE}[1] Dados brutos ({self.config['output']['raw_data']})")
        print(f"{Fore.WHITE}[2] Dados processados ({self.config['output']['processed_data']})")
        print(f"{Fore.WHITE}[3] Logs ({self.config['output']['logs']})")
        print(f"{Fore.WHITE}[0] Cancelar")
        
        choice = input(f"\n{Fore.GREEN}Escolha o diretório: {Fore.WHITE}").strip()
        
        if choice == "0":
            return
        
        path_map = {
            "1": (self.config['output']['raw_data'], "dados brutos"),
            "2": (self.config['output']['processed_data'], "dados processados"),
            "3": (self.config['output']['logs'], "logs")
        }
        
        if choice not in path_map:
            print(f"{Fore.RED}Opção inválida!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        path, name = path_map[choice]
        
        if not Path(path).exists():
            print(f"{Fore.RED}Diretório não existe!")
            input(f"{Fore.GREEN}Pressione ENTER para continuar...")
            return
        
        # Mostrar informações antes de limpar
        size = self._get_directory_size(path)
        files_count = len(list(Path(path).rglob("*")))
        
        print(f"\n{Fore.RED}⚠️  ATENÇÃO!")
        print(f"{Fore.WHITE}Isso removerá todos os arquivos de {name}:")
        print(f"{Fore.CYAN}• {files_count} arquivos")
        print(f"{Fore.CYAN}• {self._format_size(size)} de dados")
        
        confirm = input(f"\n{Fore.RED}Confirmar limpeza? (digite 'sim' para confirmar): {Fore.WHITE}").strip().lower()
        
        if confirm == 'sim':
            try:
                # Remover todos os arquivos dentro do diretório
                for item in Path(path).iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                
                print(f"{Fore.GREEN}✅ Diretório {name} limpo com sucesso!")
            except Exception as e:
                print(f"{Fore.RED}❌ Erro ao limpar diretório: {e}")
        else:
            print(f"{Fore.CYAN}Operação cancelada.")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _reset_paths_to_default(self):
        """Resetar paths para valores padrão"""
        print(f"\n{Fore.YELLOW}RESETAR PATHS PADRÃO")
        
        default_paths = {
            "raw_data": "data/raw",
            "processed_data": "data/processed",
            "logs": "logs"
        }
        
        print(f"{Fore.WHITE}Paths padrão:")
        print(f"{Fore.CYAN}• Dados brutos: {default_paths['raw_data']}")
        print(f"{Fore.CYAN}• Dados processados: {default_paths['processed_data']}")
        print(f"{Fore.CYAN}• Logs: {default_paths['logs']}")
        
        confirm = input(f"\n{Fore.WHITE}Resetar para paths padrão? (s/N): {Fore.GREEN}").strip().lower()
        
        if confirm == 's':
            self.config['output'] = default_paths
            self.save_config()
            print(f"{Fore.GREEN}✅ Paths resetados para valores padrão!")
            
            create = input(f"\n{Fore.YELLOW}Criar diretórios padrão? (S/n): {Fore.GREEN}").strip().lower()
            if create != 'n':
                self._create_all_directories()
        else:
            print(f"{Fore.CYAN}Operação cancelada.")
        
        input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def show_current_config(self):
        """Ver configurações atuais"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║                 CONFIGURAÇÕES ATUAIS                    ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        while True:
            print(f"\n{Fore.CYAN}VISUALIZAÇÃO:")
            print(f"{Fore.WHITE}[1] Resumo formatado (recomendado)")
            print(f"{Fore.WHITE}[2] JSON completo")
            print(f"{Fore.WHITE}[3] Exportar para arquivo")
            print(f"{Fore.WHITE}[0] Voltar")
            
            choice = input(f"\n{Fore.GREEN}Escolha uma opção: {Fore.WHITE}").strip()
            
            if choice == "1":
                self._show_formatted_config()
            elif choice == "2":
                self._show_json_config()
            elif choice == "3":
                self._export_config()
            elif choice == "0":
                break
            else:
                print(f"{Fore.RED}Opção inválida!")
                input(f"{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_formatted_config(self):
        """Mostrar configurações em formato amigável"""
        print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
        print(f"{Fore.YELLOW}║                    RESUMO DAS CONFIGURAÇÕES              ║")
        print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════╝")
        
        # REGIÕES
        print(f"\n{Fore.CYAN}🌍 REGIÕES E CIDADES:")
        cities = self.config['regions']['cities']
        default_city = self.config['regions']['default_city']
        print(f"{Fore.WHITE}   • Cidades cadastradas: {len(cities)}")
        for city in cities:
            if city == default_city:
                print(f"{Fore.GREEN}   • {city} (PADRÃO)")
            else:
                print(f"{Fore.WHITE}   • {city}")
        
        # SCRAPING
        print(f"\n{Fore.CYAN}🔄 CONFIGURAÇÕES DE SCRAPING:")
        scraping = self.config['scraping']
        print(f"{Fore.WHITE}   • Intervalo entre requests: {scraping['request_interval']}s")
        print(f"{Fore.WHITE}   • Timeout: {scraping['timeout']}s")
        print(f"{Fore.WHITE}   • Máximo de tentativas: {scraping['max_retries']}")
        
        # Calcular tempo máximo
        max_time = scraping['timeout'] * (scraping['max_retries'] + 1)
        requests_per_minute = 60 / scraping['request_interval']
        print(f"{Fore.CYAN}   • Tempo máximo por request: {max_time}s")
        print(f"{Fore.CYAN}   • Taxa: {requests_per_minute:.1f} requests/minuto")
        
        # PROXIES
        print(f"\n{Fore.CYAN}🔐 PROXIES:")
        proxies = scraping.get('proxies', {})
        proxies_enabled = proxies.get('enabled', False)
        proxy_count = len(proxies.get('list', []))
        rotation = proxies.get('rotation', 'random')
        
        if proxies_enabled:
            print(f"{Fore.GREEN}   • Status: ATIVADOS")
        else:
            print(f"{Fore.RED}   • Status: DESATIVADOS")
        print(f"{Fore.WHITE}   • Proxies cadastrados: {proxy_count}")
        print(f"{Fore.WHITE}   • Modo de rotação: {rotation}")
        
        # USER AGENTS
        print(f"\n{Fore.CYAN}👤 USER AGENTS:")
        user_agents = scraping['user_agents']
        print(f"{Fore.WHITE}   • Total cadastrados: {len(user_agents)}")
        if user_agents:
            first_ua = user_agents[0][:50] + "..." if len(user_agents[0]) > 50 else user_agents[0]
            print(f"{Fore.WHITE}   • Primeiro: {first_ua}")
        
        # PROCESSAMENTO PARALELO
        print(f"\n{Fore.CYAN}⚡ PROCESSAMENTO PARALELO:")
        parallel = self.config['parallel']
        print(f"{Fore.WHITE}   • Workers máximos: {parallel['max_workers']}")
        print(f"{Fore.WHITE}   • Intervalo de checkpoint: {parallel['checkpoint_interval']} itens")
        
        # PATHS
        print(f"\n{Fore.CYAN}📁 DIRETÓRIOS DE SAÍDA:")
        output = self.config['output']
        for key, path in output.items():
            path_obj = Path(path)
            if path_obj.exists():
                size = self._get_directory_size(path_obj)
                files = len(list(path_obj.glob("*")))
                status = f"{Fore.GREEN}✓ ({files} arquivos, {self._format_size(size)})"
            else:
                status = f"{Fore.RED}✗ (não existe)"
            
            name_map = {
                'raw_data': 'Dados brutos',
                'processed_data': 'Dados processados',
                'logs': 'Logs'
            }
            print(f"{Fore.WHITE}   • {name_map.get(key, key)}: {path} {status}")
        
        # ESTATÍSTICAS GERAIS
        print(f"\n{Fore.CYAN}📊 ESTATÍSTICAS GERAIS:")
        total_settings = sum(len(v) if isinstance(v, dict) else 1 for v in self.config.values())
        print(f"{Fore.WHITE}   • Total de configurações: {total_settings}")
        print(f"{Fore.WHITE}   • Seções principais: {len(self.config)}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _show_json_config(self):
        """Mostrar configurações em formato JSON"""
        print(f"\n{Fore.YELLOW}JSON COMPLETO DAS CONFIGURAÇÕES:")
        print(f"{Fore.WHITE}{'-' * 60}")
        print(json.dumps(self.config, indent=2, ensure_ascii=False))
        print(f"{Fore.WHITE}{'-' * 60}")
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def _export_config(self):
        """Exportar configurações para arquivo"""
        print(f"\n{Fore.YELLOW}EXPORTAR CONFIGURAÇÕES")
        
        default_filename = f"config_backup_{Path(self.config_file).stem}.json"
        filename = input(f"{Fore.WHITE}Nome do arquivo (padrão: {default_filename}): {Fore.GREEN}").strip()
        
        if not filename:
            filename = default_filename
        
        # Adicionar extensão .json se não tiver
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            file_size = Path(filename).stat().st_size
            print(f"{Fore.GREEN}✅ Configurações exportadas com sucesso!")
            print(f"{Fore.WHITE}   • Arquivo: {filename}")
            print(f"{Fore.WHITE}   • Tamanho: {self._format_size(file_size)}")
            
            # Mostrar caminho absoluto
            abs_path = Path(filename).absolute()
            print(f"{Fore.CYAN}   • Caminho completo: {abs_path}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao exportar: {e}")
        
        input(f"\n{Fore.GREEN}Pressione ENTER para continuar...")
    
    def reset_to_default(self):
        """Resetar configurações padrão"""
        print(f"\n{Fore.YELLOW}Resetando para configurações padrão...")
        self.config = self.get_default_config()
        self.save_config()
        print(f"{Fore.GREEN}Configurações resetadas!")
        input("Pressione ENTER para continuar...")