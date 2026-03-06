"""
Exemplo 01 – Listar todos os datasets disponíveis no portal BCB
===============================================================
Demonstra como paginar os resultados da API CKAN para obter
a lista completa de datasets do Banco Central.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bcb_client import listar_datasets

print("=" * 60)
print("LISTANDO DATASETS DO BANCO CENTRAL DO BRASIL")
print("=" * 60)

# Busca os 20 primeiros datasets
datasets = listar_datasets(limite=20, offset=0)

print(f"\nTotal retornado nesta página: {len(datasets)}\n")
for i, nome in enumerate(datasets, 1):
    print(f"  {i:02d}. {nome}")

print("\n📌 Dica: use listar_datasets(offset=20) para ver a próxima página.")
