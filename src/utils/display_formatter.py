"""
Formatador visual para outputs do sistema
"""
from colorama import Fore, Back, Style, init

# Inicializar colorama
init(autoreset=True)

class DisplayFormatter:
    """Classe para formatação visual padronizada"""
    
    @staticmethod
    def header(title, subtitle=""):
        """Cabeçalho moderno e limpo"""
        lines = []
        width = 60
        
        lines.append(f"{Fore.CYAN}┌{'─' * (width-2)}┐")
        lines.append(f"{Fore.CYAN}│{Fore.WHITE}{title:^{width-2}}{Fore.CYAN}│")
        
        if subtitle:
            lines.append(f"{Fore.CYAN}│{Fore.LIGHTBLACK_EX}{subtitle:^{width-2}}{Fore.CYAN}│")
        
        lines.append(f"{Fore.CYAN}└{'─' * (width-2)}┘")
        
        return "\n".join(lines)
    
    @staticmethod
    def section(title):
        """Seção com formatação limpa"""
        return f"\n{Fore.YELLOW}▶ {title}"
    
    @staticmethod
    def subsection(title):
        """Subseção com indentação"""
        return f"{Fore.CYAN}  ├─ {title}"
    
    @staticmethod
    def success(message):
        """Mensagem de sucesso"""
        return f"{Fore.GREEN}  ✓ {message}"
    
    @staticmethod
    def info(message):
        """Mensagem informativa"""
        return f"{Fore.CYAN}  ℹ {message}"
    
    @staticmethod
    def warning(message):
        """Mensagem de aviso"""
        return f"{Fore.YELLOW}  ⚠ {message}"
    
    @staticmethod
    def error(message):
        """Mensagem de erro"""
        return f"{Fore.RED}  ✗ {message}"
    
    @staticmethod
    def progress(current, total, message=""):
        """Barra de progresso simples"""
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 20
        filled = int(bar_length * percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        return f"{Fore.CYAN}  ▶ [{bar}] {percentage:.1f}% {message}"
    
    @staticmethod
    def stats_table(data):
        """Tabela de estatísticas"""
        lines = []
        
        lines.append(f"{Fore.CYAN}┌{'─' * 40}┐")
        lines.append(f"{Fore.CYAN}│{Fore.WHITE}{'ESTATÍSTICAS':^40}{Fore.CYAN}│")
        lines.append(f"{Fore.CYAN}├{'─' * 40}┤")
        
        for key, value in data.items():
            lines.append(f"{Fore.CYAN}│ {Fore.WHITE}{key:<18} {Fore.GREEN}{str(value):>18} {Fore.CYAN}│")
        
        lines.append(f"{Fore.CYAN}└{'─' * 40}┘")
        
        return "\n".join(lines)
    
    @staticmethod
    def compact_list(items, title="", max_display=5):
        """Lista compacta com opção de truncar"""
        if not items:
            return f"{Fore.YELLOW}  └─ Nenhum item encontrado"
        
        lines = []
        if title:
            lines.append(f"{Fore.CYAN}  {title}:")
        
        displayed = items[:max_display]
        for i, item in enumerate(displayed, 1):
            lines.append(f"{Fore.WHITE}    {i:2d}. {item}")
        
        if len(items) > max_display:
            remaining = len(items) - max_display
            lines.append(f"{Fore.LIGHTBLACK_EX}    ... e mais {remaining} items")
        
        return "\n".join(lines)
    
    @staticmethod
    def separator(char="─", length=60):
        """Separador visual"""
        return f"{Fore.LIGHTBLACK_EX}{char * length}"
    
    @staticmethod
    def clean_url_display(url, max_length=50):
        """Exibir URL de forma limpa"""
        if len(url) <= max_length:
            return url
        
        # Mostrar início e fim da URL
        start_length = max_length // 2 - 2
        end_length = max_length - start_length - 3
        
        return f"{url[:start_length]}...{url[-end_length:]}"