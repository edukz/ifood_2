# iFood Scraper

Sistema de scraping para extração de dados de restaurantes.

## Estrutura do Projeto

```
ifood_2/
├── main.py              # Ponto de entrada
├── src/
│   ├── menu/           # Sistema de menus
│   ├── scrapers/       # Scrapers unitários e paralelos
│   ├── database/       # Gerenciamento DuckDB
│   ├── config/         # Configurações
│   └── utils/          # Utilitários
├── data/
│   ├── raw/           # Dados brutos
│   └── processed/     # Dados processados
├── logs/              # Arquivos de log
└── tests/             # Testes
```

## Instalação

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

Execute o sistema:
```bash
python main.py
```

## Funcionalidades

1. **Scrapy Unitário**
   - Categorias
   - Restaurantes
   - Produtos
   - Informações extras

2. **Scrapy Paralelo**
   - Otimizado para Windows
   - Monitoramento de recursos
   - Sistema de checkpoint

3. **Banco de Dados (DuckDB)**
   - Gerenciamento completo
   - Import/Export
   - Consultas e relatórios

4. **Sistema**
   - Configurações personalizáveis
   - Logs detalhados