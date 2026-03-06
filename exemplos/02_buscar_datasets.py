"""
Exemplo 02 – Buscar datasets por palavra-chave
===============================================
Usa o endpoint package_search para encontrar datasets
relacionados a um tema específico (ex: selic, ipca, cambio).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bcb_client import buscar_datasets

# ─── Altere o termo de busca aqui ───
TERMO = "ipca"
# ────────────────────────────────────

print("=" * 60)
print(f"BUSCANDO DATASETS: '{TERMO.upper()}'")
print("=" * 60)

resultados = buscar_datasets(query=TERMO, linhas=10)

print(f"\nEncontrado(s): {len(resultados)} dataset(s)\n")
for ds in resultados:
    print(f"  📦 {ds.get('name')}")
    print(f"     Título:  {ds.get('title', 'N/A')}")
    print(f"     Notas:   {ds.get('notes', 'Sem descrição')[:80]}...")
    print(f"     Recursos: {len(ds.get('resources', []))} arquivo(s)")
    print()
