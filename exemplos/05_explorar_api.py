"""
Exemplo 05 – Exploração interativa da API do BCB
=================================================
Script de exploração geral: mostra um resumo dos datasets
mais interessantes organizados por tema.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bcb_client import buscar_datasets

TEMAS = {
    "💴 Câmbio":         "cambio",
    "📈 Juros":          "juros selic",
    "📊 IPCA/Inflação":  "ipca",
    "🏦 Crédito":        "credito",
    "🌐 Reservas":       "reservas internacionais",
    "📉 Dívida":         "divida mobiliaria",
}

print("=" * 60)
print("EXPLORAÇÃO DA API CKAN – BANCO CENTRAL DO BRASIL")
print("=" * 60)

for tema, query in TEMAS.items():
    print(f"\n{tema} (busca: '{query}')")
    print("─" * 50)
    resultados = buscar_datasets(query=query, linhas=3)
    if not resultados:
        print("  Nenhum resultado encontrado.")
    else:
        for ds in resultados:
            print(f"  • {ds['name']}")
