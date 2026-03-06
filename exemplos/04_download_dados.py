"""
Exemplo 04 – Baixar dados e salvar localmente
=============================================
Faz o download do primeiro recurso CSV/JSON de um dataset
e salva na pasta 'dados/' do projeto.

Dataset padrão: Taxa de Câmbio – Dólar Americano Venda
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bcb_client import listar_recursos_de_dataset, baixar_recurso_csv

# ─── Configurações ───
DATASET_ID   = "1-taxa-de-cambio---livre---dolar-americano-venda---diario"
PASTA_SAIDA  = os.path.join(os.path.dirname(__file__), '..', 'dados')
# ─────────────────────

os.makedirs(PASTA_SAIDA, exist_ok=True)

print("=" * 60)
print(f"DOWNLOAD: {DATASET_ID}")
print("=" * 60)

recursos = listar_recursos_de_dataset(DATASET_ID)

if not recursos:
    print("Nenhum recurso encontrado neste dataset.")
    sys.exit(1)

# Exibe os recursos disponíveis
print(f"\n{len(recursos)} recurso(s) encontrado(s):\n")
for i, r in enumerate(recursos, 1):
    print(f"  [{i}] {r['nome']} | Formato: {r['formato']}")
    print(f"       URL: {r['url']}\n")

# Baixa o primeiro recurso (geralmente CSV ou JSON)
primeiro = recursos[0]
print(f"Baixando: {primeiro['nome']}...")

conteudo = baixar_recurso_csv(primeiro["url"])

# Salva o arquivo
extensao    = primeiro.get("formato", "txt").lower().replace("text/csv", "csv") or "csv"
nome_arquivo = f"{DATASET_ID[:50]}.{extensao}"
caminho_saida = os.path.join(PASTA_SAIDA, nome_arquivo)

with open(caminho_saida, "w", encoding="utf-8") as f:
    f.write(conteudo)

print(f"\n✅ Arquivo salvo em: {caminho_saida}")
print(f"   Tamanho: {len(conteudo):,} caracteres")
print(f"\n📋 Primeiras linhas do arquivo:")
print("─" * 50)
for linha in conteudo.splitlines()[:5]:
    print(f"  {linha}")
