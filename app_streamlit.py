"""
Painel BCB - Estatísticas Pix
Versão Streamlit — mantém as 3 abas do app Dash original
e adiciona a Aba 4: Transações por Município.
"""

import os
import glob
import json
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from prophet import Prophet
from plotly.subplots import make_subplots
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Painel BCB — Estatísticas Pix",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS GLOBAL (tema dark glassmorphism)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    -webkit-font-smoothing: antialiased;
    letter-spacing: -0.01em;
}

/* Fundo geral: Slate 900 to Slate 950 gradient */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #020617 100%);
    color: #e2e8f0; /* Slate 200 */
}

/* Tipografia Escalonada */
h1, h2, h3, h4, h5, h6 { 
    color: #f8fafc; /* Slate 50 */
    font-weight: 600;
    letter-spacing: -0.02em;
}
p, span, div {
    line-height: 1.6;
}

/* Sidebar - glassmorphism */
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.75); /* Slate 900 com opacidade */
    border-right: 1px solid rgba(148, 163, 184, 0.05); /* Slate 400 a 5% */
    backdrop-filter: blur(16px);
}
[data-testid="stSidebar"] hr {
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #38bdf8; /* Sky 400 */
    font-weight: 500;
}

/* Cards de métricas premium */
[data-testid="metric-container"] {
    background: rgba(30, 41, 59, 0.4); /* Slate 800 */
    border: 1px solid rgba(148, 163, 184, 0.08); /* Bordas ultra-finas */
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.2); /* Brilho sutil Sky no hover */
}
[data-testid="metric-container"] label {
    color: #94a3b8 !important; /* Slate 400 */
    font-size: 0.9rem;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f8fafc; /* Slate 50 */
    font-weight: 700;
    font-size: 2rem;
    margin-top: 8px;
    letter-spacing: -0.03em;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.85rem;
    font-weight: 500;
    margin-top: 4px;
}
/* Cores semânticas do Delta - Emerald e Rose */
[data-testid="stMetricDelta"] svg[title="up"] + div { color: #34d399 !important; } /* Emerald 400 */
[data-testid="stMetricDelta"] svg[title="down"] + div { color: #fb7185 !important; } /* Rose 400 */

/* Abas refinadas */
[data-testid="stTabs"] [data-baseweb="tab"] {
    color: #64748b; /* Slate 500 */
    font-weight: 500;
    padding: 12px 16px;
    font-size: 1.05rem;
    transition: color 0.2s;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #f8fafc !important; /* Slate 50 */
    font-weight: 600;
    border-bottom: 2px solid #38bdf8 !important; /* Sky 400 */
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: #cbd5e1; /* Slate 300 */
}

/* Divisores sutis */
hr {
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
    margin: 32px 0;
}

/* Inputs e selects modernizados */
[data-baseweb="select"] div, [data-baseweb="input"] input {
    background: rgba(15, 23, 42, 0.6) !important; /* Slate 900 */
    border-color: rgba(148, 163, 184, 0.15) !important;
    color: #f8fafc !important;
    border-radius: 8px !important;
    transition: all 0.2s;
}
[data-baseweb="select"] div:hover, [data-baseweb="input"] input:hover {
    border-color: rgba(56, 189, 248, 0.4) !important;
}

/* Botões primários (Indigo to Sky gradient) */
.stButton > button {
    background: linear-gradient(135deg, #4f46e5 0%, #0ea5e9 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    padding: 10px 24px;
    letter-spacing: 0.02em;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
    color: white;
}
.stButton > button:active {
    transform: translateY(0);
}

/* Gráficos Plotly — fundo transparente */
.js-plotly-plot .plotly .bg {
    fill: transparent !important;
}

/* Alertas estilo Tailwind */
.stAlert {
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.1);
    background: rgba(30, 41, 59, 0.5);
    backdrop-filter: blur(8px);
}

/* Info boxes personalizadas */
.info-box {
    background: rgba(56, 189, 248, 0.05); /* Sky a 5% */
    border-left: 3px solid #38bdf8; /* Sky 400 */
    border-radius: 0 8px 8px 0;
    padding: 16px 20px;
    color: #cbd5e1; /* Slate 300 */
    font-size: 0.95rem;
    margin-bottom: 24px;
    line-height: 1.6;
}

/* Expander (Sanfona) */
[data-testid="stExpander"] {
    background: rgba(30, 41, 59, 0.3);
    border: 1px solid rgba(148, 163, 184, 0.08);
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE PLOTLY (tema dark reutilizável / Claude Frontend Aesthetics)
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_DARK = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#f8fafc", # Slate 50
    font_family="Outfit",
    title_font_family="Outfit",
    title_font_size=20,
    hovermode="x unified",
    margin=dict(t=65, l=20, r=20, b=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=13, color="#94a3b8")),
)

# ─────────────────────────────────────────────────────────────────────────────
# CARREGAMENTO DE DADOS
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados")


@st.cache_data(show_spinner="Carregando dados de fraudes...")
def load_dados_fraudes():
    import glob, os
    padrao1 = os.path.join(DADOS_DIR, "fraudes_pix_*.json")
    padrao2 = os.path.join(DADOS_DIR, "Fraudes_Pix_*.json")
    arquivos = sorted(glob.glob(padrao1) + glob.glob(padrao2))
    
    if not arquivos:
        st.error(f"Erro: Arquivos 'fraudes' não encontrados no diretório:\n\n`{DADOS_DIR}`\n\nLista de arquivos na pasta atual: {os.listdir(DADOS_DIR) if os.path.exists(DADOS_DIR) else 'pasta inexistente'}")
        return pd.DataFrame()
    df = pd.read_json(arquivos[-1])
    if not df.empty and "AnoMes" in df.columns:
        df = df.sort_values("AnoMes")
        # --- LIMPEZA DE DADOS: Fraudes ---
        df = df.dropna(subset=["QtdePixcontestados", "AnoMes"])          # remove linhas críticas nulas
        df = df[df["QtdePixcontestados"] >= 0]                           # remove valores negativos impossíveis
        df = df.drop_duplicates(subset=["AnoMes"])                       # remove meses duplicados
        if "PercentualdeDevolucao" in df.columns:
            df["PercentualdeDevolucao"] = df["PercentualdeDevolucao"].clip(0, 100)  # % não pode passar de 100
        # ---------------------------------
        df["MesesFormatados"] = (
            df["AnoMes"].astype(str).str[:4] + "-" + df["AnoMes"].astype(str).str[4:]
        )
    return df


@st.cache_data(show_spinner="Carregando estatísticas de transações...")
def load_dados_transacoes():
    arquivos = sorted(glob.glob(os.path.join(DADOS_DIR, "estatisticas_transacoes_*.json")))
    if not arquivos:
        st.error(f"Erro: Arquivos 'transações' não encontrados no diretório:\n\n`{DADOS_DIR}`")
        return pd.DataFrame()
    try:
        return pd.read_json(arquivos[-1])
    except Exception as e:
        st.warning(f"Erro lendo transações: {e}")
        return pd.DataFrame()


def _process_estados(df):
    if df.empty or "Estado" not in df.columns:
        return df
    
    # Se já estiver com 2 caracteres, assume que já são siglas
    if df["Estado"].str.strip().str.len().max() == 2:
        return df
        
    mapa_uf = {
        "ACRE": "AC", "ALAGOAS": "AL", "AMAPÁ": "AP", "AMAZONAS": "AM",
        "BAHIA": "BA", "CEARÁ": "CE", "DISTRITO FEDERAL": "DF",
        "ESPÍRITO SANTO": "ES", "GOIÁS": "GO", "MARANHÃO": "MA",
        "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS", "MINAS GERAIS": "MG",
        "PARÁ": "PA", "PARAÍBA": "PB", "PARANÁ": "PR", "PERNAMBUCO": "PE",
        "PIAUÍ": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
        "RIO GRANDE DO SUL": "RS", "RONDÔNIA": "RO", "RORAIMA": "RR",
        "SANTA CATARINA": "SC", "SÃO PAULO": "SP", "SERGIPE": "SE", "TOCANTINS": "TO"
    }
    
    # Tenta usar o mapa
    df["Estado"] = df["Estado"].str.strip().str.upper().map(mapa_uf).fillna(df["Estado"])
    return df


@st.cache_data(show_spinner="Carregando dados municipais (cache)...")
def load_dados_municipios():
    """Lê cache local ou busca da API Olinda BCB."""
    cache_path = os.path.join(DADOS_DIR, "pix_regional_cache.json")
    if os.path.exists(cache_path):
        try:
            df = pd.read_json(cache_path)
            if not df.empty:
                return _process_estados(df)
        except Exception:
            pass
    return _process_estados(_fetch_municipios_api())


def _fetch_municipios_api(meses_voltar: int = 6) -> pd.DataFrame:
    """Busca dados de TransacoesPixPorMunicipio na API Olinda."""
    base_url = (
        "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos"
        "/versao/v1/odata/TransacoesPixPorMunicipio"
    )
    hoje = datetime.now()
    mes_atual = hoje.replace(day=1)
    todos = []
    meses_ok = 0
    tentativas = 0

    bar = st.progress(0, text="Buscando dados municipais na API BCB...")
    while meses_ok < meses_voltar and tentativas < 10:
        anomes = mes_atual.strftime("%Y%m")
        url = f"{base_url}(DataBase=@DataBase)?@DataBase='{anomes}'&$format=json"
        try:
            pg = url
            while pg:
                r = requests.get(pg, timeout=60)
                r.raise_for_status()
                data = r.json()
                todos.extend(data.get("value", []))
                pg = data.get("@odata.nextLink")
            if todos:
                meses_ok += 1
        except Exception:
            pass
        mes_atual -= relativedelta(months=1)
        tentativas += 1
        bar.progress(min(meses_ok / meses_voltar, 1.0), text=f"Baixando {anomes}...")

    bar.empty()
    if not todos:
        return pd.DataFrame()

    df = pd.DataFrame(todos)

    # --- LIMPEZA DE DADOS: Municípios ---
    if "Municipio" in df.columns and "Estado" in df.columns:
        df = df.dropna(subset=["Municipio", "Estado"])       # remove municípios sem nome
        df["Municipio"] = df["Municipio"].str.strip().str.title()  # padroniza capitalização
    # -------------------------------------

    for c in ["VL_PagadorPF", "VL_PagadorPJ", "VL_RecebedorPF", "VL_RecebedorPJ"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    for c in ["QT_PagadorPF", "QT_PagadorPJ", "QT_RecebedorPF", "QT_RecebedorPJ"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["VALOR_TOTAL"] = df[["VL_PagadorPF", "VL_PagadorPJ", "VL_RecebedorPF", "VL_RecebedorPJ"]].sum(axis=1)
    df["QT_TOTAL"]    = df[["QT_PagadorPF", "QT_PagadorPJ", "QT_RecebedorPF", "QT_RecebedorPJ"]].sum(axis=1)

    # Remove valores negativos indicando anomalias no município
    df = df[df["VALOR_TOTAL"] >= 0]

    os.makedirs(DADOS_DIR, exist_ok=True)
    df.to_json(os.path.join(DADOS_DIR, "pix_regional_cache.json"), orient="records", indent=2)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR COM FILTROS
# ─────────────────────────────────────────────────────────────────────────────
def sidebar_filtros(df_fraudes, df_trans):
    with st.sidebar:
        st.markdown("## 💸 Painel BCB — Pix")
        st.divider()

        # ── Filtros Aba 1 e 2 (fraudes) ─────────────────────────────────────
        st.markdown("### 📅 Período (Fraudes)")
        filtro_periodo = {"todos": "Todos os meses", "ultimos3": "Últimos 3 meses", "ultimos6": "Últimos 6 meses"}
        sel_periodo = st.selectbox("Período", list(filtro_periodo.values()), key="f_periodo")
        periodo_key = {v: k for k, v in filtro_periodo.items()}[sel_periodo]

        st.divider()

        # ── Filtros Aba 3 (transações sistêmicas) ───────────────────────────
        st.markdown("### 🔄 Transações Sistêmicas")

        opts_pfpj = ["Todos"]
        opts_reg  = ["Todas"]

        if not df_trans.empty:
            if "PAG_PFPJ" in df_trans.columns:
                opts_pfpj += sorted(df_trans["PAG_PFPJ"].dropna().unique().tolist())
            if "PAG_REGIAO" in df_trans.columns:
                r = [x for x in df_trans["PAG_REGIAO"].dropna().unique() if x.strip().lower() != "nao disponivel"]
                opts_reg += sorted(r)

        sel_pfpj = st.selectbox("PF / PJ (Pagador)", opts_pfpj, key="f_pfpj")
        sel_reg  = st.selectbox("Região (Pagador)", opts_reg, key="f_reg")

        st.divider()

        # ── Filtros Aba 4 (municípios) ───────────────────────────────────────
        st.markdown("### 🗺️ Municípios")
        estados_br = [
            "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
            "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO",
        ]
        sel_uf     = st.selectbox("Estado (UF)", estados_br, index=estados_br.index("SP"), key="f_uf")
        sel_metrica = st.radio("Métrica", ["Valor (R$)", "Quantidade"], horizontal=True, key="f_metrica")
        sel_fluxo  = st.radio("Fluxo", ["Total", "Pagador PF", "Pagador PJ", "Recebedor PF", "Recebedor PJ"], key="f_fluxo")

    return periodo_key, sel_pfpj, sel_reg, sel_uf, sel_metrica, sel_fluxo


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES DE ESTILO PLOTLY
# ─────────────────────────────────────────────────────────────────────────────
def style_fig(fig, **kwargs):
    layout = {**PLOTLY_DARK, **kwargs}  # kwargs sobrescreve PLOTLY_DARK em caso de duplicata
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# ABA 1: VISÃO GERAL
# ─────────────────────────────────────────────────────────────────────────────
def aba_visao_geral(df, periodo_key):
    if df.empty:
        st.warning("Execute `exemplos/06_fraude_med.py` para gerar os dados de fraudes.")
        return

    # Aplica filtro de período
    if periodo_key == "ultimos3":
        df = df.tail(3)
    elif periodo_key == "ultimos6":
        df = df.tail(6)

    st.markdown("### Insight 1: Taxa de Eficácia das Contestações de Fraude")
    qtde_contestados = df['QtdePixcontestados'].sum()
    qtde_aceitas = df['Qtdecontestacoesaceitas'].sum()
    taxa_aceite_med = (qtde_aceitas / qtde_contestados) * 100 if qtde_contestados > 0 else 0

    st.metric("Taxa de Eficácia (Aceites)", f"{taxa_aceite_med:.1f}%", help="Contestações aceitas / Contestações totais")

    if taxa_aceite_med < 40:
        st.warning(f"🚨 Alerta Risco: A taxa de aceite das contestações de fraude está baixa ({taxa_aceite_med:.1f}%). Verifique o rigor na triagem.")

    fig_eficacia = go.Figure(data=[
        go.Bar(name='Rejeitadas', x=df['AnoMes'].astype(str), y=df['Qtdecontestacoesrejeitadas'], marker_color='#E57373'),
        go.Bar(name='Aceitas', x=df['AnoMes'].astype(str), y=df['Qtdecontestacoesaceitas'], marker_color='#81C784')
    ])
    fig_eficacia.update_layout(barmode='stack', title="Volume de Contestações: Aceitas vs Rejeitadas", **PLOTLY_DARK)
    st.plotly_chart(style_fig(fig_eficacia), use_container_width=True)

    st.divider()
    st.markdown("### Insight 2: Saturação de Marcação de Fraude (Chaves vs Usuários)")
    fig_marcacao = go.Figure()
    fig_marcacao.add_trace(go.Scatter(x=df['AnoMes'].astype(str), y=df['QtdeChavesPixcommarcacoesdefraude'], mode='lines+markers', name='Chaves com Fraude', line=dict(color='#FFCA28')))
    fig_marcacao.add_trace(go.Scatter(x=df['AnoMes'].astype(str), y=df['QtdeUsuarioscommarcacoesdefraude'], mode='lines+markers', name='Usuários com Fraude', line=dict(color='#BA68C8')))
    fig_marcacao.update_layout(title="Evolução: Marcação de Fraude na DICT", **PLOTLY_DARK)
    st.plotly_chart(style_fig(fig_marcacao), use_container_width=True)

    st.divider()
    st.markdown("### Insight 3: Conversão do Bloqueio Cautelar")
    fig_cautelar = px.pie(
        names=['Liberados ao Cliente', 'Devolvidos à Origem'],
        values=[df['ValorPixbloqueadoscautelarmenteeliberados'].sum(), df['ValorPixbloqueadoscautelarmenteedevolvidos'].sum()],
        title='Destino dos Recursos em Bloqueio Cautelar',
        color_discrete_sequence=['#4DD0E1', '#E57373'],
        hole=0.6
    )
    st.plotly_chart(style_fig(fig_cautelar), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# ABA 2: CONTESTAÇÕES vs DEVOLUÇÕES
# ─────────────────────────────────────────────────────────────────────────────
def aba_contestacoes(df_med, periodo_key):
    if df_med.empty:
        st.warning("Sem dados de fraudes disponíveis.")
        return

    if periodo_key == "ultimos3":
        df_med = df_med.tail(3)
    elif periodo_key == "ultimos6":
        df_med = df_med.tail(6)

    with st.expander("📖 Dicionário de Dados — o que significa cada campo?"):
        st.markdown("""
        | Parâmetro | Descrição |
        |-----------|-----------|
        | `PercentualdeDevolucao` | % do valor contestado que foi efetivamente devolvido ao cliente |
        | `ValorPixdevolvidosintegralmente` | Transações onde 100% do valor foi recuperado |
        | `ValorPixdevolvidosparcialmente` | Transações onde uma fração do valor original foi recuperada |
        | `ValorPixnaodevolvidossaldoinsuficiente` | Frustração por falta de fundos na conta de destino |
        | `Valornaodevolvidoscontaencerrada` | Frustração pois a conta de destino já havia sido encerrada |
        """)

    st.markdown("### Insight 1: Taxa Real de Recuperação (Percentual de Devolução)")
    media_devolucao = df_med['PercentualdeDevolucao'].mean() if len(df_med) > 0 else 0
    st.metric("Taxa Média de Devolução", f"{media_devolucao:.2f}%")

    if media_devolucao < 5.0 and len(df_med) > 0:
        st.error(f"⚠️ Atenção Crítica: Sucesso de devolução está em {media_devolucao:.2f}%. Contas laranjas estão esvaziando o saldo antes da atuação do banco recebedor.")

    fig_devolucaotaxa = px.line(
        df_med, 
        x='MesesFormatados', 
        y='PercentualdeDevolucao',
        title='Evolução % do Valor Devolvido vs Contestação Aceita',
        template='plotly_dark',
        markers=True
    )

    # Área preenchida + cor da linha
    fig_devolucaotaxa.update_traces(
        fill='tozeroy',
        fillcolor='rgba(0, 255, 136, 0.15)',
        line=dict(color='#00ff88', width=2),
        marker=dict(size=5, color='#00ff88')
    )

    # Linha de média
    media = df_med['PercentualdeDevolucao'].mean()
    fig_devolucaotaxa.add_hline(
        y=media,
        line_dash='dash',
        line_color='#facc15',
        annotation_text=f"Média: {media:.1f}%",
        annotation_position="top right",
        annotation_font_color='#facc15'
    )

    # Annotation no pico (máximo)
    if not df_med.empty:
        idx_max = df_med['PercentualdeDevolucao'].idxmax()
        fig_devolucaotaxa.add_annotation(
            x=df_med.loc[idx_max, 'MesesFormatados'],
            y=df_med.loc[idx_max, 'PercentualdeDevolucao'],
            text=f"⚠️ Pico: {df_med.loc[idx_max, 'PercentualdeDevolucao']:.1f}%",
            showarrow=True,
            arrowhead=2,
            font=dict(color='#f87171', size=11),
            arrowcolor='#f87171',
            ay=-40
        )

        # Annotation no mínimo
        idx_min = df_med['PercentualdeDevolucao'].idxmin()
        fig_devolucaotaxa.add_annotation(
            x=df_med.loc[idx_min, 'MesesFormatados'],
            y=df_med.loc[idx_min, 'PercentualdeDevolucao'],
            text=f"📉 Mínimo: {df_med.loc[idx_min, 'PercentualdeDevolucao']:.1f}%",
            showarrow=True,
            arrowhead=2,
            font=dict(color='#60a5fa', size=11),
            arrowcolor='#60a5fa',
            ay=40
        )

    # Renomeia eixos
    fig_devolucaotaxa.update_layout(
        **PLOTLY_DARK,
        xaxis_title="Mês/Ano",
        yaxis_title="% Devolvido",
        yaxis=dict(ticksuffix='%')
    )

    st.plotly_chart(style_fig(fig_devolucaotaxa), use_container_width=True)

    st.divider()
    st.markdown("### Insight 2: Motivos de Frustração da Devolução")

    # Coleta de dados
    valores_frustrados = {
        'Saldo Insuficiente': df_med['ValorPixnaodevolvidossaldoinsuficiente'].sum(),
        'Conta Encerrada':    df_med['Valornaodevolvidoscontaencerrada'].sum(),
        'Motivos Diversos':   df_med['ValorPixnaodevolvidosmotivosdiversos'].sum()
    }
    df_frustracao = pd.DataFrame(list(valores_frustrados.items()), columns=['Motivo', 'VALOR'])

    # Calcula % de participação
    total_frustracao = df_frustracao['VALOR'].sum()
    if total_frustracao > 0:
        df_frustracao['PCT'] = (df_frustracao['VALOR'] / total_frustracao * 100).round(1)
    else:
        df_frustracao['PCT'] = 0.0

    df_frustracao = df_frustracao.sort_values('VALOR', ascending=True)

    # Cor por gravidade
    cores = {
        'Saldo Insuficiente': '#f87171',
        'Conta Encerrada':    '#fb923c',
        'Motivos Diversos':   '#94a3b8'
    }
    df_frustracao['COR'] = df_frustracao['Motivo'].map(cores).fillna('#94a3b8')

    fig_frust = go.Figure()
    fig_frust.add_trace(go.Bar(
        y=df_frustracao['Motivo'],
        x=df_frustracao['VALOR'],
        orientation='h',
        marker_color=df_frustracao['COR'],
        text=df_frustracao.apply(
            lambda r: f"R$ {r['VALOR']/1e9:.1f}B  ({r['PCT']:.1f}%)", axis=1
        ),
        textposition='outside',
        textfont=dict(color='white', size=11)
    ))

    fig_frust.update_layout(
        title='Rastreio da Perda: Razões para Não Devolução do MED',
        xaxis_title='Valor (R$)',
        yaxis_title='Motivo',
        xaxis=dict(tickprefix='R$ '),
        **PLOTLY_DARK
    )
    st.plotly_chart(style_fig(fig_frust), use_container_width=True)

    # KPI cards abaixo
    col1, col2, col3 = st.columns(3)
    for col, (_, row) in zip(
        [col1, col2, col3],
        df_frustracao.sort_values('VALOR', ascending=False).iterrows()
    ):
        col.metric(
            label=row['Motivo'],
            value=f"R$ {row['VALOR']/1e9:.2f}B",
            delta=f"{row['PCT']:.1f}% do total",
            delta_color="off"
        )

    st.divider()
    st.markdown("### Insight 3: Qualidade da Recuperação (Total vs Parcial)")
    fig_recup = go.Figure(data=[
        go.Bar(name='Devolvido Integralmente', x=df_med['MesesFormatados'], y=df_med['ValorPixdevolvidosintegralmente'], marker_color='#64B5F6'),
        go.Bar(name='Devolvido Parcialmente', x=df_med['MesesFormatados'], y=df_med['ValorPixdevolvidosparcialmente'], marker_color='#FFB74D')
    ])
    fig_recup.update_layout(barmode='group', title='Qualidade Financeira da Devolução (Integral x Parcial)', **PLOTLY_DARK)
    st.plotly_chart(style_fig(fig_recup), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# ABA 3: ESTATÍSTICAS SISTÊMICAS PIX
# ─────────────────────────────────────────────────────────────────────────────
def aba_estatisticas(df_sistemico, sel_pfpj, sel_reg):
    if df_sistemico.empty:
        st.warning("Execute `exemplos/07_estatisticas_pix.py` para gerar os dados de transações.")
        return

    df = df_sistemico.copy()
    if sel_pfpj != "Todos" and "PAG_PFPJ" in df.columns:
        df = df[df["PAG_PFPJ"] == sel_pfpj]
    if sel_reg != "Todas" and "PAG_REGIAO" in df.columns:
        df = df[df["PAG_REGIAO"] == sel_reg]

    if df.empty:
        st.info("Nenhum dado para os filtros selecionados.")
        return
        
    df_sistemico = df

    with st.expander("📖 Dicionário de Dados — o que significa cada campo?"):
        st.markdown("""
        | Parâmetro | Descrição |
        |-----------|-----------|
        | `VALOR` | Valor financeiro total transacionado na relação selecionada |
        | `QUANTIDADE` | Número de transações realizadas na relação |
        | `PAG_PFPJ` / `REC_PFPJ` | Natureza jurídica do pagador / recebedor (PF ou PJ) |
        | `FORMAINICIACAO` | Método como o Pix foi iniciado (Chave, QR Code, Copia e Cola, etc) |
        | `PAG_IDADE` | Faixa etária do pagador |
        """)

    st.markdown("### Insight 1: Ticket Médio P2P vs P2B (PF/PJ)")

    df_box = df_sistemico.copy()
    df_box["VALOR"] = pd.to_numeric(df_box["VALOR"], errors="coerce")
    df_box["QUANTIDADE"] = pd.to_numeric(df_box["QUANTIDADE"], errors="coerce")

    # 1. Remove "Nao disponivel" de ambas as colunas
    df_box = df_box[
        ~df_box["PAG_PFPJ"].astype(str).str.strip().str.lower().isin(["nao disponivel", "nan"]) &
        ~df_box["REC_PFPJ"].astype(str).str.strip().str.lower().isin(["nao disponivel", "nan"])
    ]

    # Calcula o TICKET MÉDIO real por linha
    df_box = df_box[df_box["QUANTIDADE"] > 0]
    df_box["TICKET_MEDIO"] = df_box["VALOR"] / df_box["QUANTIDADE"]

    # Remove tickets absurdos (< R$1 e > p95 por grupo)
    df_box = df_box[df_box["TICKET_MEDIO"] > 1.0]

    def filtrar_p95(grupo):
        p95 = grupo["TICKET_MEDIO"].quantile(0.95)
        return grupo[grupo["TICKET_MEDIO"] <= p95]

    df_box = df_box.groupby(["PAG_PFPJ", "REC_PFPJ"], group_keys=False).apply(filtrar_p95)

    # 2 gráficos lado a lado
    col1, col2 = st.columns(2)
    for col, pag_tipo in zip([col1, col2], ["PF", "PJ"]):
        df_filtrado = df_box[df_box["PAG_PFPJ"] == pag_tipo]
        fig = px.box(
            df_filtrado, x="PAG_PFPJ", y="TICKET_MEDIO", color="REC_PFPJ",
            title=f"Pagador {pag_tipo} → Ticket Médio por Recebedor",
            template="plotly_dark",
            labels={"TICKET_MEDIO": "Ticket Médio (R$)"},
            category_orders={"REC_PFPJ": ["PF", "PJ"]}
        )
        fig.update_layout(**PLOTLY_DARK)
        col.plotly_chart(style_fig(fig), use_container_width=True)

    st.divider()
    st.markdown("### Insight 2: Acessibilidade e Iniciação (Forma da Transação)")
    if 'FORMAINICIACAO' in df_sistemico.columns:
        df_iniciacao = df_sistemico.groupby('FORMAINICIACAO', as_index=False)['QUANTIDADE'].sum()

        # Remove inválidos
        df_iniciacao = df_iniciacao[
            ~df_iniciacao['FORMAINICIACAO'].astype(str).str.strip().str.lower().isin(
                ["nao disponivel", "nan", ""]
            )
        ]

        # Traduz siglas para nomes legíveis
        mapa_siglas = {
            "QRDN": "QR Code Dinâmico",
            "DICT": "Chave Pix (DICT)",
            "MANU": "Dados Manuais",
            "QRES": "QR Code Estático",
            "INIC": "Iniciação por API",
            "AGND": "Agendamento",
        }
        df_iniciacao['METODO'] = df_iniciacao['FORMAINICIACAO'].map(mapa_siglas).fillna(df_iniciacao['FORMAINICIACAO'])

        # Calcula % de participação
        total = df_iniciacao['QUANTIDADE'].sum()
        df_iniciacao['PCT'] = (df_iniciacao['QUANTIDADE'] / total * 100).round(1)

        # Agrupa métodos com menos de 0.5% em "Outros"
        threshold = total * 0.005
        df_iniciacao['METODO'] = df_iniciacao.apply(
            lambda row: row['METODO'] if row['QUANTIDADE'] >= threshold else 'Outros',
            axis=1
        )
        df_iniciacao = df_iniciacao.groupby('METODO', as_index=False).agg(
            QUANTIDADE=('QUANTIDADE', 'sum')
        )
        # Recalcula PCT depois do agrupamento
        total_final = df_iniciacao['QUANTIDADE'].sum()
        df_iniciacao['PCT'] = (df_iniciacao['QUANTIDADE'] / total_final * 100).round(2)

        # Donut chart
        fig_iniciacao = px.pie(
            df_iniciacao,
            names='METODO',
            values='QUANTIDADE',
            title='Métodos de Iniciação do Pix (Distribuição de Volume)',
            hole=0.55,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_iniciacao.update_traces(
            textposition='outside',
            textinfo='label+percent',
            textfont_size=12,
            pull=[0.03] * len(df_iniciacao)
        )
        fig_iniciacao.update_layout(**PLOTLY_DARK)
        st.plotly_chart(style_fig(fig_iniciacao), use_container_width=True)

        # Tabela resumo
        st.markdown("**📋 Detalhamento por método:**")
        df_tabela = df_iniciacao[['METODO', 'QUANTIDADE', 'PCT']].sort_values('QUANTIDADE', ascending=False)
        df_tabela.columns = ['Método', 'Qtd Transações', '% do Total']
        df_tabela['Qtd Transações'] = df_tabela['Qtd Transações'].apply(lambda x: f"{x:,.0f}")
        df_tabela['% do Total'] = df_tabela['% do Total'].apply(lambda x: f"{x:.2f}%")
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Insight 3: Perfil Demográfico x Volume Financeiro (Idade)")
    if 'PAG_IDADE' in df_sistemico.columns:
        df_idade = df_sistemico.groupby('PAG_IDADE', as_index=False).agg(
            VALOR=('VALOR', 'sum'),
            QUANTIDADE=('QUANTIDADE', 'sum')
        )

        # Remove categorias inválidas
        invalidos = ["nao informado", "nao se aplica", "nao disponivel", "nan"]
        df_idade = df_idade[
            ~df_idade['PAG_IDADE'].astype(str).str.strip().str.lower().isin(invalidos)
        ]

        # Ticket médio real
        df_idade = df_idade[df_idade['QUANTIDADE'] > 0]
        df_idade['Ticket_Medio'] = df_idade['VALOR'] / df_idade['QUANTIDADE']

        # Ordem cronológica correta
        ordem_idade = [
            'até 19 anos', 'entre 20 e 29 anos', 'entre 30 e 39 anos',
            'entre 40 e 49 anos', 'entre 50 e 59 anos', 'mais de 60 anos'
        ]
        df_idade['PAG_IDADE'] = pd.Categorical(
            df_idade['PAG_IDADE'], categories=ordem_idade, ordered=True
        )
        df_idade = df_idade.sort_values('PAG_IDADE')

        # Lollipop chart
        fig_idade = go.Figure()

        for _, row in df_idade.iterrows():
            if pd.notna(row['PAG_IDADE']):
                fig_idade.add_shape(
                    type="line",
                    x0=row['PAG_IDADE'], x1=row['PAG_IDADE'],
                    y0=0, y1=row['Ticket_Medio'],
                    line=dict(color="#38bdf8", width=2)
                )

        fig_idade.add_trace(go.Scatter(
            x=df_idade['PAG_IDADE'],
            y=df_idade['Ticket_Medio'],
            mode='markers+text',
            marker=dict(size=16, color='#38bdf8', line=dict(color='white', width=2)),
            text=df_idade['Ticket_Medio'].apply(lambda v: f"R$ {v:,.0f}" if pd.notna(v) else ""),
            textposition='top center',
            textfont=dict(color='#f8fafc', size=11),
            name='Ticket Médio'
        ))

        fig_idade.update_layout(
            title='Ticket Médio Pix por Faixa Etária do Pagador',
            xaxis_title='Faixa Etária',
            yaxis_title='Ticket Médio (R$)',
            **PLOTLY_DARK
        )
        st.plotly_chart(style_fig(fig_idade), use_container_width=True)

        # Extrai os tickets reais das faixas para injetar na tabela de interpretação
        # Caso alguma categoria venha vazia do DF, preenche com 0 visualmente
        def pega_valor(faixa):
            try:
                v = df_idade[df_idade["PAG_IDADE"] == faixa]["Ticket_Medio"].values[0]
                return f"R$ {v:,.0f}" if pd.notna(v) else "Indisponível"
            except IndexError:
                return "Indisponível"

        st.markdown(
            f"""
            **📊 Insights do perfil demográfico x ticket médio:**
            
            Notamos uma tendência de crescimento claro estruturado conforme a maturidade financeira do pagador:
            
            | Faixa Etária | Ticket (R$) | Interpretação |
            | :--- | :--- | :--- |
            | **até 19 anos** | {pega_valor('até 19 anos')} | Jovens — pequenos pagamentos cotidianos, mesadas, lanches |
            | **20-29 anos** | {pega_valor('entre 20 e 29 anos')} | Início da vida financeira, divisão de contas, aluguel |
            | **30-39 anos** | {pega_valor('entre 30 e 39 anos')} | Adultos ativos financeiramente, contas recorrentes |
            | **40-49 anos** | {pega_valor('entre 40 e 49 anos')} | Pico produtivo da carreira, pagamentos mais elevados |
            | **50-59 anos** | {pega_valor('entre 50 e 59 anos')} | Maior estabilidade e poder aquisitivo histórico |
            | **60+ anos** | {pega_valor('mais de 60 anos')} | Maior ticket médio — poupança consolidada, aposentadoria, transações patrimoniais |
            """
        )


# ─────────────────────────────────────────────────────────────────────────────
# ABA 4: TRANSAÇÕES POR MUNICÍPIO
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Carregando GeoJSON do Brasil...")
def _load_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        return requests.get(url, timeout=30).json()
    except Exception:
        return None


@st.cache_data(show_spinner="Renderizando Insight 1 (Municípios)...")
def gerar_insight1_mun(df_municipios):
    if 'VALOR_TOTAL' not in df_municipios.columns:
        return None, None
    cidade_pico = df_municipios.sort_values(by='VALOR_TOTAL', ascending=False).iloc[0]
    
    top_15_cidades = df_municipios.groupby(['Municipio', 'Estado'], as_index=False)['VALOR_TOTAL'].sum().nlargest(15, 'VALOR_TOTAL')
    top_15_cidades['Local'] = top_15_cidades['Municipio'] + " - " + top_15_cidades['Estado']
    
    fig_top_mun = px.bar(top_15_cidades, x='VALOR_TOTAL', y='Local', orientation='h', title='Top 15 Municípios por Fluxo de Caixa (Valor Recebido/Enviado)', color='VALOR_TOTAL', color_continuous_scale='Viridis')
    fig_top_mun.update_layout(yaxis={'categoryorder':'total ascending'}, **PLOTLY_DARK)
    return cidade_pico, style_fig(fig_top_mun)

@st.cache_data(show_spinner="Renderizando Insight 2 (Municípios)...")
def gerar_insight2_mun(df_municipios):
    if 'QT_RecebedorPJ' not in df_municipios.columns or 'VL_RecebedorPJ' not in df_municipios.columns:
        return None
        
    df_scatter = df_municipios[
        ~df_municipios['Regiao'].astype(str).str.strip().str.lower().isin(
            ["nao informado", "nan", ""]
        )
    ].copy()

    fig_scatter = px.scatter(
        df_scatter,
        x='QT_RecebedorPJ',
        y='VL_RecebedorPJ',
        color='Regiao',
        size=df_scatter['VL_RecebedorPJ'].apply(
            lambda x: min(x, df_scatter['VL_RecebedorPJ'].quantile(0.98))
        ),
        size_max=12,
        hover_name='Municipio',
        log_x=True, log_y=True,
        title='Concentração Empresarial: Qtd Transações x Volume PJ',
        template='plotly_dark',
        opacity=0.6,
        labels={
            'QT_RecebedorPJ': 'Qtd Transações PJ',
            'VL_RecebedorPJ': 'Volume Recebido PJ (R$)',
            'Regiao': 'Região'
        }
    )

    fig_scatter.update_layout(
        **PLOTLY_DARK,
        yaxis=dict(
            type='log',
            range=[4, 13],
            autorange=False
        ),
        xaxis=dict(
            type='log',
            autorange=True
        )
    )
    return style_fig(fig_scatter)

@st.cache_data(show_spinner="Renderizando Insight 3 (Municípios)...")
def gerar_insight3_mun(df_municipios):
    if 'VL_RecebedorPF' not in df_municipios.columns or 'VL_RecebedorPJ' not in df_municipios.columns:
        return None
        
    df_pfpj = df_municipios[['Municipio', 'VL_RecebedorPF', 'VL_RecebedorPJ']].copy()
    df_pfpj = df_pfpj.groupby('Municipio', as_index=False).sum()
    
    df_pfpj['TOTAL'] = df_pfpj['VL_RecebedorPF'] + df_pfpj['VL_RecebedorPJ']
    df_pfpj = df_pfpj[df_pfpj['TOTAL'] > 0]
    
    df_pfpj['PCT_PF'] = (df_pfpj['VL_RecebedorPF'] / df_pfpj['TOTAL'] * 100).round(1)
    df_pfpj['PCT_PJ'] = (df_pfpj['VL_RecebedorPJ'] / df_pfpj['TOTAL'] * 100).round(1)
    df_pfpj = df_pfpj.nlargest(15, 'TOTAL')

    fig_pfpj = go.Figure()
    if 'PCT_PF' in df_pfpj.columns:
        fig_pfpj.add_trace(go.Bar(
            y=df_pfpj['Municipio'],
            x=df_pfpj['PCT_PF'],
            name='PF',
            orientation='h',
            marker_color='#6366f1',
            text=df_pfpj['PCT_PF'].apply(lambda v: f"{v:.1f}%" if v > 5 else ""),
            textposition='inside'
        ))
    if 'PCT_PJ' in df_pfpj.columns:
        fig_pfpj.add_trace(go.Bar(
            y=df_pfpj['Municipio'],
            x=df_pfpj['PCT_PJ'],
            name='PJ',
            orientation='h',
            marker_color='#f97316',
            text=df_pfpj['PCT_PJ'].apply(lambda v: f"{v:.1f}%" if v > 5 else ""),
            textposition='inside'
        ))

    fig_pfpj.update_layout(
        barmode='stack',
        title='Top 15 Cidades — Proporção do Volume Recebido PF vs PJ',
        xaxis=dict(title='% do Volume Recebido', range=[0, 100], ticksuffix='%'),
        yaxis=dict(title='Cidade', categoryorder='total ascending'),
        **PLOTLY_DARK
    )
    return style_fig(fig_pfpj)

def aba_municipios(sel_uf, sel_metrica, sel_fluxo):
    st.markdown(
        '<div class="info-box">💡 Os dados são carregados do cache local ou buscados na API Olinda BCB. '
        'Para atualizar, delete <code>dados/pix_regional_cache.json</code> e recarregue a página.</div>',
        unsafe_allow_html=True,
    )

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🔄 Atualizar dados da API"):
            st.cache_data.clear()
            st.rerun()

    df_municipios = load_dados_municipios()

    if df_municipios.empty:
        st.error("Não foi possível carregar os dados municipais. Verifique sua conexão com a internet.")
        return

    st.markdown("### Insight 1: Concentração e Dispersão Econômica Regional (Top 15 Nacional)")
    cidade_pico, fig_top_mun = gerar_insight1_mun(df_municipios)
    if fig_top_mun:
        st.info(f"📍 **Pólo Diário:** {cidade_pico.get('Municipio', '')} - {cidade_pico.get('Estado', '')} movimentou R$ {cidade_pico.get('VALOR_TOTAL', 0)/1e9:,.2f} bi no total.")
        st.plotly_chart(fig_top_mun, use_container_width=True)

    st.divider()
    st.markdown("### Insight 2: Análise de Capilaridade P2B Municipal")
    fig_scatter = gerar_insight2_mun(df_municipios)
    if fig_scatter:
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.markdown(
            """
            **📊 Insights da Análise P2B Municipal:**
            
            * **Tendência linear clara (escala log-log)**: Quanto mais transações um município possui, logicamente maior será o volume — atestando forte adoção corporativa do Pix que escala simetricamente.
            
            | Região | Posição no Gráfico | Dinâmica Comercial de Recebimento de Pix |
            | :--- | :--- | :--- |
            | 🟣 **Sudeste** | Canto superior direito | Francamente domina em escala total (volume multimilionário em massa e número massivo de contas de recebimento PJ). SP sendo o outlier de ouro do bloco. |
            | 🟠 **Nordeste** | Meio a espalhado pelo gráfico | Expansão formidável da digitalização no recebimento com crescimento acelerado pulverizado entre suas capitais e metrópoles. |
            | 🟢 **Sul** | Distribuído homogeneamente | Região caracterizada por altíssima capilaridade mercantil. Vários municípios de médio porte com excelentes fluxos médios de capital. |
            | 🟣 **Centro-Oeste** | Poucos pontos, muito concentrados no topo | Reflexo claro da geografia do Agronegócio e capitais isoladas: baixa densidade demográfica, mas alto poder e volume aquisitivo transacional rodando entre o produtor/PJ e suas cadeias rurais ou na Capital Nacional. |
            | 🟠 **Norte** | Parte inferior à esquerda / Baixo | Mais focada em polos regionais escassos (Manaus/Pará). Grande massa do território com baixíssima adoção corporativa de pagamentos digitais em comparação com as demais metades do país. |
            """
        )

    st.divider()
    st.markdown("### Insight 3: Participação PF x PJ no Volume Recebido")
    fig_pfpj = gerar_insight3_mun(df_municipios)
    if fig_pfpj:
        st.plotly_chart(fig_pfpj, use_container_width=True)



# ─────────────────────────────────────────────────────────────────────────────
# ABA 5: PROJEÇÕES & PREDITIVA
# ─────────────────────────────────────────────────────────────────────────────
def aba_preditiva(df_med):
    st.markdown("## 🔮 Projeções & Preditiva (Machine Learning)")
    st.markdown("Utilizando o modelo **Prophet** para prever o comportamento futuro baseado no histórico recente.")

    if df_med.empty or len(df_med) < 3:
        st.warning("Histórico de fraudes insuficiente para rodar o modelo preditivo (Mínimo de 3 meses necessários).")
        return

    st.divider()

    # Prepara dados para o Prophet (precisa ser 'ds' e 'y')
    # Converter AnoMes (ex: 202301) para primeiro dia do mês (ex: 2023-01-01)
    df_prophet = df_med[['AnoMes', 'QtdePixcontestados']].copy()
    df_prophet['ds'] = pd.to_datetime(df_prophet['AnoMes'].astype(str) + '01', format='%Y%m%d')
    df_prophet['y'] = df_prophet['QtdePixcontestados']

    st.markdown("### Insight 1: Projeção de Volume de Contestações de Fraude (Próximos 6 meses)")
    
    with st.spinner("Treinando modelo de Inteligência Artificial..."):
        m = Prophet(seasonality_mode='additive', yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
        try:
            m.fit(df_prophet[['ds', 'y']])
        except Exception as e:
            st.error("Não foi possível treinar o modelo preditivo com o volume de dados atual (podem faltar dados ou haver pouca variação).")
            # Log ou mostre o erro técnico em um expander
            with st.expander("Detalhes Técnicos do Erro"):
                st.code(str(e))
            return
        
        # Prever próximos 6 meses
        future = m.make_future_dataframe(periods=6, freq='MS')
        forecast = m.predict(future)

    # Pegando valor projetado do último mês
    ultimo_mes_projetado = forecast.iloc[-1]
    
    st.info(f"📈 **Projeção:** O modelo estima que em **{ultimo_mes_projetado['ds'].strftime('%b/%Y')}** teremos cerca de **{ultimo_mes_projetado['yhat']:,.0f}** contestações de fraude. (Margem: {ultimo_mes_projetado['yhat_lower']:,.0f} a {ultimo_mes_projetado['yhat_upper']:,.0f})", icon="ℹ️")

    # Gráfico do Prophet feito com Plotly
    fig_forecast = go.Figure()

    # Upper/Lower Bounds (Cone de Incerteza)
    fig_forecast.add_trace(go.Scatter(
        x=forecast['ds'].dt.strftime('%b/%y').tolist() + forecast['ds'].dt.strftime('%b/%y').tolist()[::-1],
        y=forecast['yhat_upper'].tolist() + forecast['yhat_lower'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(255, 152, 0, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=False
    ))

    # Linha Prevista
    fig_forecast.add_trace(go.Scatter(
        x=forecast['ds'].dt.strftime('%b/%y'), y=forecast['yhat'],
        mode='lines', name='Vértice Previsto (yhat)', line=dict(color='#FF9800', width=3, dash='dash')
    ))

    # Realidade Histórica
    fig_forecast.add_trace(go.Scatter(
        x=df_prophet['ds'].dt.strftime('%b/%y'), y=df_prophet['y'],
        mode='lines+markers', name='Realidade (Histórico)', line=dict(color='#38bdf8', width=3), marker=dict(size=8)
    ))

    fig_forecast.update_layout(title='Forecasting de Contestações MED', **PLOTLY_DARK)
    st.plotly_chart(style_fig(fig_forecast), use_container_width=True)

    st.divider()

    st.markdown("### Insight 2: Simulador de Sensibilidade da Eficácia do MED")
    st.markdown("Simule um cenário futuro ajustando os níveis de recuperação preventiva.")
    
    # Calcular média de devolução
    media_historica_devolucao = df_med['PercentualdeDevolucao'].mean() if len(df_med) > 0 else 5.0
    ticket_medio_fraude = 850.0 # valor base simulado
    
    col1, col2 = st.columns([1, 2])
    with col1:
        nova_taxa = st.slider("🔧 Simular % de Devolução", min_value=1.0, max_value=30.0, value=float(media_historica_devolucao), step=0.5, format="%.1f%%")
        
    with col2:
        projecao_financeira = ultimo_mes_projetado['yhat'] * ticket_medio_fraude
        recuperacao_simulada = projecao_financeira * (nova_taxa / 100)
        
        st.metric(f"💰 Recuperação Financeira Estimada em {ultimo_mes_projetado['ds'].strftime('%b/%Y')}", 
                  f"R$ {recuperacao_simulada:,.0f}", 
                  delta=f"Melhoria de {(nova_taxa - media_historica_devolucao):+.1f} pts percentuais" if nova_taxa > media_historica_devolucao else "No cenário base")

    
# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def dashboard():
    df_fraudes = load_dados_fraudes()
    df_trans   = load_dados_transacoes()

    periodo_key, sel_pfpj, sel_reg, sel_uf, sel_metrica, sel_fluxo = sidebar_filtros(df_fraudes, df_trans)

    # Header
    st.markdown(
        "<h1 style='margin-bottom:0'>💸 Estatísticas MED / BCB</h1>"
        "<p style='color:#94a3b8; margin-top:4px'>Painel de monitoramento do Sistema Pix — Banco Central do Brasil</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Visão Geral",
        "🔄 Contestações vs Devoluções",
        "📈 Estatísticas Sistêmicas PIX",
        "🗺️ Transações por Município",
        "🔮 Projeções & Preditiva",
    ])

    with tab1:
        aba_visao_geral(df_fraudes, periodo_key)

    with tab2:
        aba_contestacoes(df_fraudes, periodo_key)

    with tab3:
        aba_estatisticas(df_trans, sel_pfpj, sel_reg)
    with tab4:
        aba_municipios(sel_uf, sel_metrica, sel_fluxo)

    with tab5:
        aba_preditiva(df_fraudes)


# ─────────────────────────────────────────────────────────────────────────────
# ROTEAMENTO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def main():
    dashboard()


if __name__ == "__main__":
    main()
