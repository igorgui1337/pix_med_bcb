# BC_DATA — Exploração da API do Banco Central do Brasil

Projeto de estudo para acessar a API CKAN de dados abertos do Banco Central do Brasil (BCB).

**URL da API:** `https://dadosabertos.bcb.gov.br/api/3/action/`

---

## 📁 Estrutura do Projeto

```
BC_DATA/
├── src/
│   └── bcb_client.py       # Cliente Python reutilizável para a API CKAN do BCB
├── exemplos/
│   ├── 01_listar_datasets.py    # Lista todos os datasets disponíveis
│   ├── 02_buscar_datasets.py    # Busca datasets por palavra-chave
│   ├── 03_detalhes_dataset.py   # Detalhes e recursos de um dataset específico
│   ├── 04_download_dados.py     # Baixa e salva dados localmente (CSV)
│   └── 05_explorar_api.py       # Exploração temática (câmbio, juros, IPCA...)
├── dados/                       # Pasta onde os arquivos baixados são salvos
├── requirements.txt
└── README.md
```

---

## 🚀 Como Começar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Executar os exemplos
```bash
# Listar datasets
python exemplos/01_listar_datasets.py

# Buscar por tema (edite o TERMO dentro do arquivo)
python exemplos/02_buscar_datasets.py

# Ver detalhes da SELIC
python exemplos/03_detalhes_dataset.py

# Baixar dados do Dólar
python exemplos/04_download_dados.py

# Explorar por tema (câmbio, juros, IPCA, crédito...)
python exemplos/05_explorar_api.py
```

---

## 📦 Principais Funções (`bcb_client.py`)

| Função | Descrição |
|---|---|
| `listar_datasets(limite, offset)` | Lista todos os datasets (com paginação) |
| `buscar_datasets(query, linhas)` | Busca por palavra-chave |
| `obter_dataset(nome_ou_id)` | Detalhes completos de um dataset |
| `listar_recursos_de_dataset(nome_ou_id)` | Lista arquivos disponíveis para download |
| `baixar_recurso_csv(url)` | Baixa o conteúdo de um recurso |
| `listar_grupos()` | Lista os grupos temáticos |
| `obter_grupo(nome_grupo)` | Detalhes de um grupo |

---

## 🗂️ Datasets Interessantes para Estudo

| Dataset ID | Descrição |
|---|---|
| `11-taxa-de-juros---selic` | Taxa SELIC |
| `1-taxa-de-cambio---livre---dolar-americano-venda---diario` | Dólar (venda, diário) |
| `10813-taxa-de-cambio---livre---dolar-americano-compra` | Dólar (compra, diário) |
| `21082-inadimplencia-da-carteira-de-credito---total` | Inadimplência total |
| `24363-indice-de-atividade-economica-do-banco-central---ibc-br` | IBC-Br (PIB mensal) |
| `195-depositos-de-poupanca-a-partir-de-04052012---rentabilidade-no-periodo` | Rendimento poupança |

---

## 📚 Referências

- [Dados Abertos BCB](https://dadosabertos.bcb.gov.br)
- [Documentação CKAN API](https://docs.ckan.org/en/latest/api/index.html)
- [SGS — Sistema Gerenciador de Séries Temporais do BCB](https://www3.bcb.gov.br/sgspub/)
