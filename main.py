"""
Sistema de Scraping iFood
Ponto de entrada principal
"""
import sys
import os
from src.menu.main_menu import MainMenu
from src.utils.logger import setup_logger

def main():
    """Função principal do sistema"""
    # Configurar logger
    logger = setup_logger()
    
    try:
        logger.info("Iniciando sistema de scraping iFood")
        
        # Criar instância do menu principal
        menu = MainMenu()
        
        # Executar menu
        menu.run()
        
    except KeyboardInterrupt:
        logger.info("Sistema interrompido pelo usuário")
        print("\n\nSistema finalizado.")
    except Exception as e:
        logger.error(f"Erro não tratado: {str(e)}")
        print(f"\nErro crítico: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()