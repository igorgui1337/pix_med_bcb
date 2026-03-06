"""
Exemplo 06 – Estatísticas de Fraudes no Pix (API Olinda/BCB)
=============================================================
Conecta ao serviço Olinda do Banco Central para buscar dados
de fraudes no Pix por período (AnoMes).

API:    https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1
Recurso: EstatisticasFraudesPix

Parâmetro obrigatório:
    Database: período no formato YYYYMM (ex: '202401' = Janeiro/2024)
    ⚠️  A API Olinda exige aspas SIMPLES ao redor do valor.

Campos retornados:
    AnoMes                                          → Período (YYYYMM)
    QtdePixcontestados                              → Qtde Pix contestados
    Qtdecontestacoesaceitas                         → Contestações aceitas
    Qtdecontestacoesrejeitadas                      → Contestações rejeitadas
    Qtdecontestacoesaceitasacada100mil              → Aceitas por 100mil transações
    QtdeUsuarioscommarcacoesdefraude                → Usuários marcados como fraude
    QtdeChavesPixcommarcacoesdefraude               → Chaves Pix com marcação de fraude
    ValorPixcontestadosaceitos                      → Valor total aceito (R$)
    QuantidadedevolvidaintegralmentepormeiodoMED    → Qtde devolvida integralmente (MED)
    ValorPixdevolvidosintegralmente                 → Valor devolvido integralmente (R$)
    QuantidadedevolvidaparcialmentepormeiodoMED     → Qtde devolvida parcialmente (MED)
    ValorPixdevolvidosparcialmente                  → Valor devolvido parcialmente (R$)
    ValorPixresidualnaodevolvido                    → Valor residual não devolvido (R$)
    Quantidadedenaodevolvidossaldoinsuficiente      → Qtde não devolvida (saldo insuf.)
    ValorPixnaodevolvidossaldoinsuficiente          → Valor não devolvido (saldo insuf.)
    Quantidadedenaodevolvidoscontaencerrada         → Qtde não devolvida (conta encerrada)
    Valornaodevolvidoscontaencerrada                → Valor não devolvido (conta encerrada)
    Quantidadedenaodevolvidosmotivosdiversos        → Qtde não devolvida (outros motivos)
    ValorPixnaodevolvidosmotivosdiversos            → Valor não devolvido (outros motivos)
    PercentualdeDevolucao                           → % de devolução
    QtdePixbloqueadoscautelarmenteeliberados        → Pix bloqueados cautelar. e liberados
    ValorPixbloqueadoscautelarmenteeliberados       → Valor bloqueado e liberado (R$)
    QtdePixbloqueadoscautelarmenteedevolvidos       → Pix bloqueados e devolvidos
    ValorPixbloqueadoscautelarmenteedevolvidos      → Valor bloqueado e devolvido (R$)
"""

import urllib.request
import urllib.error
import json
import os
from datetime import datetime


BASE_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/"
    "Pix_DadosAbertos/versao/v1/odata/"
)


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES DE ACESSO À API
# ─────────────────────────────────────────────────────────────────────────────

def buscar_fraudes_pix(anomes: str, top: int = 100) -> list:
    """
    Busca estatísticas de fraudes no Pix para um período específico.

    Args:
        anomes: Período no formato 'YYYYMM' (ex: '202401' = Jan/2024)
        top:    Número máximo de registros (padrão: 100)

    Returns:
        Lista de dicionários com os dados de fraude do período
    """
    # ⚠️ A API Olinda requer aspas SIMPLES ao redor do valor de Database.
    # URL correta: .../EstatisticasFraudesPix(Database=@Database)?@Database='202401'&$top=100&$format=json
    endpoint = "EstatisticasFraudesPix(Database=@Database)"
    url = (
        f"{BASE_URL}{endpoint}"
        f"?@Database='{anomes}'&$top={top}&$format=json"
    )

    try:
        resp = urllib.request.urlopen(url, timeout=30)
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("value", [])
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise ConnectionError(f"Erro HTTP {e.code}: {body[:200]}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Erro de conexão: {e.reason}")


def buscar_fraudes_intervalo(anomes_inicio: str, anomes_fim: str) -> list:
    """
    Busca estatísticas de fraudes para um intervalo de períodos.

    Args:
        anomes_inicio: Período inicial 'YYYYMM' (ex: '202301')
        anomes_fim:    Período final   'YYYYMM' (ex: '202312')

    Returns:
        Lista com todos os registros coletados no intervalo
    """
    inicio = datetime.strptime(anomes_inicio, "%Y%m")
    fim    = datetime.strptime(anomes_fim,    "%Y%m")

    todos = []
    atual = inicio
    while atual <= fim:
        periodo = atual.strftime("%Y%m")
        print(f"  → Buscando {periodo}...", end=" ", flush=True)
        try:
            registros = buscar_fraudes_pix(anomes=periodo)
            todos.extend(registros)
            print(f"✓ {len(registros)} registro(s)")
        except Exception as e:
            print(f"✗ {e}")

        # Avança 1 mês
        mes = atual.month + 1
        ano = atual.year + (1 if mes > 12 else 0)
        mes = 1 if mes > 12 else mes
        atual = datetime(ano, mes, 1)

    return todos


def formatar_brl(valor) -> str:
    """Formata número como moeda brasileira (R$)."""
    if valor is None:
        return "N/A"
    try:
        return f"R$ {float(valor):>15,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return str(valor)


# ─────────────────────────────────────────────────────────────────────────────
# EXECUÇÃO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("  ESTATÍSTICAS DE FRAUDES NO PIX — API OLINDA / BCB")
    print("=" * 65)

    # ─── Configuração ────────────────────────────────────────────
    PERIODO_UNICO  = "202401"   # Janeiro/2024
    PERIODO_INICIO = "202301"   # Início do intervalo
    PERIODO_FIM    = "202306"   # Fim    do intervalo
    # ─────────────────────────────────────────────────────────────

    # ── MODO 1: Período único ─────────────────────────────────────────────────
    print(f"\n[MODO 1] Detalhes do período: {PERIODO_UNICO}\n")

    try:
        registros = buscar_fraudes_pix(anomes=PERIODO_UNICO)
    except ConnectionError as e:
        print(f"  ❌ Erro ao conectar: {e}")
        registros = []

    if not registros:
        print(f"  ⚠️  Nenhum dado para o período {PERIODO_UNICO}.")
    else:
        r = registros[0]  # Normalmente 1 registro por período

        print(f"  {'─'*60}")
        print(f"  Período (AnoMes):                    {r.get('AnoMes', 'N/A')}")
        print(f"  {'─'*60}")
        print(f"\n  [ CONTESTAÇÕES ]")
        print(f"  Pix contestados:                     {r.get('QtdePixcontestados', 0):>15,}")
        print(f"  Contestações aceitas:                {r.get('Qtdecontestacoesaceitas', 0):>15,}")
        print(f"  Contestações rejeitadas:             {r.get('Qtdecontestacoesrejeitadas', 0):>15,}")
        print(f"  Aceitas por 100mil transações:       {r.get('Qtdecontestacoesaceitasacada100mil', 'N/A'):>15}")
        print(f"  Usuários c/ marcação de fraude:      {r.get('QtdeUsuarioscommarcacoesdefraude', 0):>15,}")
        print(f"  Chaves Pix c/ marcação de fraude:    {r.get('QtdeChavesPixcommarcacoesdefraude', 0):>15,}")

        print(f"\n  [ VALORES CONTESTADOS ]")
        print(f"  Valor total aceito:                  {formatar_brl(r.get('ValorPixcontestadosaceitos'))}")

        print(f"\n  [ DEVOLUÇÕES (MED) ]")
        print(f"  Qtde devolvida integralmente:        {r.get('QuantidadedevolvidaintegralmentepormeiodoMED', 0):>15,}")
        print(f"  Valor devolvido integralmente:       {formatar_brl(r.get('ValorPixdevolvidosintegralmente'))}")
        print(f"  Qtde devolvida parcialmente:         {r.get('QuantidadedevolvidaparcialmentepormeiodoMED', 0):>15,}")
        print(f"  Valor devolvido parcialmente:        {formatar_brl(r.get('ValorPixdevolvidosparcialmente'))}")
        print(f"  Valor residual NÃO devolvido:        {formatar_brl(r.get('ValorPixresidualnaodevolvido'))}")
        print(f"  % de devolução:                      {r.get('PercentualdeDevolucao', 'N/A'):>14}%")

        print(f"\n  [ NÃO DEVOLVIDOS — MOTIVOS ]")
        print(f"  Qtde (saldo insuficiente):           {r.get('Quantidadedenaodevolvidossaldoinsuficiente', 0):>15,}")
        print(f"  Valor (saldo insuficiente):          {formatar_brl(r.get('ValorPixnaodevolvidossaldoinsuficiente'))}")
        print(f"  Qtde (conta encerrada):              {r.get('Quantidadedenaodevolvidoscontaencerrada', 0):>15,}")
        print(f"  Valor (conta encerrada):             {formatar_brl(r.get('Valornaodevolvidoscontaencerrada'))}")
        print(f"  Qtde (outros motivos):               {r.get('Quantidadedenaodevolvidosmotivosdiversos', 0):>15,}")
        print(f"  Valor (outros motivos):              {formatar_brl(r.get('ValorPixnaodevolvidosmotivosdiversos'))}")

        print(f"\n  [ BLOQUEIOS CAUTELARES ]")
        print(f"  Pix bloqueados e liberados:          {r.get('QtdePixbloqueadoscautelarmenteeliberados', 0):>15,}")
        print(f"  Valor bloqueado e liberado:          {formatar_brl(r.get('ValorPixbloqueadoscautelarmenteeliberados'))}")
        print(f"  Pix bloqueados e devolvidos:         {r.get('QtdePixbloqueadoscautelarmenteedevolvidos', 0):>15,}")
        print(f"  Valor bloqueado e devolvido:         {formatar_brl(r.get('ValorPixbloqueadoscautelarmenteedevolvidos'))}")

    # ── MODO 2: Intervalo de períodos ─────────────────────────────────────────
    print("\n" + "─" * 65)
    print(f"[MODO 2] Coletando intervalo: {PERIODO_INICIO} → {PERIODO_FIM}\n")

    todos = buscar_fraudes_intervalo(PERIODO_INICIO, PERIODO_FIM)

    print(f"\n{'─' * 65}")
    print(f"Total: {len(todos)} registro(s) coletado(s)\n")

    if todos:
        print(f"  {'Período':<8} {'Pix Contest.':>14} {'% Dev.':>8} {'Vlr. Aceito (R$)':>22}")
        print(f"  {'─'*8} {'─'*14} {'─'*8} {'─'*22}")
        for r in todos:
            periodo = str(r.get("AnoMes", "N/A"))
            contest = r.get("QtdePixcontestados", 0) or 0
            perc    = r.get("PercentualdeDevolucao", 0) or 0
            vlr     = r.get("ValorPixcontestadosaceitos", 0) or 0
            vlr_fmt = f"{float(vlr):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            print(f"  {periodo:<8} {contest:>14,} {perc:>7.2f}% {vlr_fmt:>22}")

    # ── Salvar JSON ──────────────────────────────────────────────────────────
    pasta_dados   = os.path.join(os.path.dirname(__file__), '..', 'dados')
    os.makedirs(pasta_dados, exist_ok=True)
    arquivo_saida = os.path.join(pasta_dados, f"fraudes_pix_{PERIODO_INICIO}_{PERIODO_FIM}.json")

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Dados salvos em: {arquivo_saida}")
