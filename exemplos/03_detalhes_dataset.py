"""
Exemplo 03 – Ver detalhes e recursos de um dataset
===================================================
Obtém metadados completos de um dataset e lista os recursos
(arquivos) disponíveis para download.

Dataset padrão: Taxa de Juros SELIC (ID: 11-taxa-de-juros---selic)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bcb_client import obter_dataset, listar_recursos_de_dataset

# ─── Altere o dataset aqui ───
DATASET_ID = "11-taxa-de-juros---selic"
# ─────────────────────────────

print("=" * 60)
print(f"DETALHES DO DATASET: {DATASET_ID}")
print("=" * 60)

dataset = obter_dataset(DATASET_ID)

print(f"\n  Nome:         {dataset.get('name')}")
print(f"  Título:       {dataset.get('title', 'N/A')}")
print(f"  Organização:  {dataset.get('organization', {}).get('title', 'N/A')}")
print(f"  Licença:      {dataset.get('license_title', 'N/A')}")
print(f"  Criado em:    {dataset.get('metadata_created', 'N/A')[:10]}")
print(f"  Atualizado:   {dataset.get('metadata_modified', 'N/A')[:10]}")
print(f"\n  Descrição:\n  {dataset.get('notes', 'Sem descrição')[:200]}")

print("\n" + "─" * 60)
print("RECURSOS DISPONÍVEIS PARA DOWNLOAD")
print("─" * 60)

recursos = listar_recursos_de_dataset(DATASET_ID)
if not recursos:
    print("  Nenhum recurso encontrado.")
else:
    for i, r in enumerate(recursos, 1):
        print(f"\n  [{i}] {r['nome']} ({r['formato']})")
        print(f"      URL: {r['url']}")
