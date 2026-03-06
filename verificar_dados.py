import urllib.request, json
import sys
sys.stdout.reconfigure(encoding='utf-8')

url = (
    "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/"
    "EstatisticasFraudesPix(Database=@Database)"
    "?@Database='202401'&$top=10&$format=json"
)

resp = urllib.request.urlopen(url, timeout=30)
data = json.loads(resp.read().decode("utf-8"))
registros = data.get("value", [])

print(f"Registros retornados : {len(registros)}")
print(f"Campos por registro  : {len(registros[0]) if registros else 0}")
print()

# Mostra o primeiro registro completo
r = registros[0]
print("=" * 60)
print(f"  REGISTRO 1 — Periodo: {r.get('AnoMes')}")
print("=" * 60)
for chave, valor in r.items():
    print(f"  {chave}: {valor}")

# Mostra resumo de todos os 10 registros
print()
print("=" * 60)
print("  RESUMO DOS 10 REGISTROS (AnoMes e QtdePixcontestados)")
print("=" * 60)
for i, r in enumerate(registros, 1):
    print(f"  [{i:02d}] AnoMes={r.get('AnoMes')} | Pix Contestados={r.get('QtdePixcontestados'):,}")
