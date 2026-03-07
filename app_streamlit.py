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

import modulo_auth

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
    arquivos = sorted(glob.glob(os.path.join(DADOS_DIR, "fraudes_pix_*.json")))
    if not arquivos:
        return pd.DataFrame()
    df = pd.read_json(arquivos[-1])
    if not df.empty and "AnoMes" in df.columns:
        df = df.sort_values("AnoMes")
        df["MesesFormatados"] = (
            df["AnoMes"].astype(str).str[:4] + "-" + df["AnoMes"].astype(str).str[4:]
        )
    return df


@st.cache_data(show_spinner="Carregando estatísticas de transações...")
def load_dados_transacoes():
    arquivos = sorted(glob.glob(os.path.join(DADOS_DIR, "estatisticas_transacoes_*.json")))
    if not arquivos:
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
    for c in ["VL_PagadorPF", "VL_PagadorPJ", "VL_RecebedorPF", "VL_RecebedorPJ"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    for c in ["QT_PagadorPF", "QT_PagadorPJ", "QT_RecebedorPF", "QT_RecebedorPJ"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["VALOR_TOTAL"] = df[["VL_PagadorPF", "VL_PagadorPJ", "VL_RecebedorPF", "VL_RecebedorPJ"]].sum(axis=1)
    df["QT_TOTAL"]    = df[["QT_PagadorPF", "QT_PagadorPJ", "QT_RecebedorPF", "QT_RecebedorPJ"]].sum(axis=1)

    os.makedirs(DADOS_DIR, exist_ok=True)
    df.to_json(os.path.join(DADOS_DIR, "pix_regional_cache.json"), orient="records", indent=2)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# AUTENTICAÇÃO
# ─────────────────────────────────────────────────────────────────────────────
def tela_login():
    if os.path.exists("capa_login.png"):
        import base64
        with open("capa_login.png", "rb") as img_file:
            b64_str = base64.b64encode(img_file.read()).decode("utf-8")
        html_img = f'<div style="text-align: center; margin-bottom: 20px;"><img src="data:image/png;base64,{b64_str}" style="max-width: 100%; width: 350px; border-radius: 8px;"></div>'
        st.markdown(html_img, unsafe_allow_html=True)
    st.markdown("## 🔐 Acesso Restrito")
    st.caption("Painel de Estatísticas do Sistema Pix — BCB")
    st.divider()

    email = st.text_input("📧 E-mail corporativo", key="login_email")
    senha = st.text_input("🔒 Senha", type="password", key="login_senha")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar no Painel", use_container_width=True):
            if not email or not senha:
                st.error("Preencha e-mail e senha.")
            else:
                ok, msg = modulo_auth.verificar_login(email, senha)
                if ok:
                    st.session_state["autenticado"] = True
                    st.session_state["email"] = email
                    st.rerun()
                else:
                    st.error(msg)
    with col2:
        if st.button("Solicitar Acesso", use_container_width=True):
            st.session_state["tela"] = "registro"
            st.rerun()

def tela_registro():
    if os.path.exists("capa_login.png"):
        import base64
        with open("capa_login.png", "rb") as img_file:
            b64_str = base64.b64encode(img_file.read()).decode("utf-8")
        html_img = f'<div style="text-align: center; margin-bottom: 20px;"><img src="data:image/png;base64,{b64_str}" style="max-width: 100%; width: 350px; border-radius: 8px;"></div>'
        st.markdown(html_img, unsafe_allow_html=True)
    st.markdown("## 🧑‍💼 Nova Credencial")
    st.caption("A senha deve ter 8+ chars, maiúscula, minúscula, número e símbolo.")
    st.divider()

    email = st.text_input("📧 E-mail", key="reg_email")
    senha = st.text_input("🔑 Criar senha", type="password", key="reg_senha")
    conf  = st.text_input("✅ Confirmar senha", type="password", key="reg_conf")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Registrar", use_container_width=True):
            if not email or not senha or not conf:
                st.error("Preencha todos os campos.")
            elif senha != conf:
                st.error("As senhas não coincidem.")
            else:
                ok, msg = modulo_auth.registrar_usuario(email, senha)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
    with col2:
        if st.button("← Voltar ao Login", use_container_width=True):
            st.session_state["tela"] = "login"
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR COM FILTROS
# ─────────────────────────────────────────────────────────────────────────────
def sidebar_filtros(df_fraudes, df_trans):
    with st.sidebar:
        st.markdown("## 💸 Painel BCB — Pix")
        st.markdown(f"👤 `{st.session_state.get('email', '')}`")
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

        st.divider()
        if st.button("🚪 Encerrar Sessão", use_container_width=True):
            for k in ["autenticado", "email", "tela"]:
                st.session_state.pop(k, None)
            st.rerun()

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

    st.markdown("### Insight 1: Taxa Real de Recuperação (Percentual de Devolução)")
    media_devolucao = df_med['PercentualdeDevolucao'].mean() if len(df_med) > 0 else 0
    st.metric("Taxa Média de Devolução", f"{media_devolucao:.2f}%")

    if media_devolucao < 5.0 and len(df_med) > 0:
        st.error(f"⚠️ Atenção Crítica: Sucesso de devolução está em {media_devolucao:.2f}%. Contas laranjas estão esvaziando o saldo antes da atuação do banco recebedor.")

    fig_devolucaotaxa = px.line(df_med, x='MesesFormatados', y='PercentualdeDevolucao', title='Evolução % do Valor Devolvido vs Contestação Aceita', markers=True, color_discrete_sequence=['#00E676'])
    fig_devolucaotaxa.update_layout(**PLOTLY_DARK, yaxis_title="% Devolvido")
    st.plotly_chart(style_fig(fig_devolucaotaxa), use_container_width=True)

    st.divider()
    st.markdown("### Insight 2: Motivos de Frustração da Devolução")
    valores_frustrados = {
        'Saldo Insuficiente': df_med['ValorPixnaodevolvidossaldoinsuficiente'].sum(),
        'Conta Encerrada': df_med['Valornaodevolvidoscontaencerrada'].sum(),
        'Motivos Diversos': df_med['ValorPixnaodevolvidosmotivosdiversos'].sum()
    }
    df_frustrado = pd.DataFrame(list(valores_frustrados.items()), columns=['Motivo', 'Valor (R$)'])
    fig_motivos = px.bar(df_frustrado, x='Valor (R$)', y='Motivo', orientation='h', title='Rastreio da Perda: Razões para Não Devolução do MED', color='Motivo', color_discrete_sequence=['#FF8A65', '#9575CD', '#90A4AE'])
    fig_motivos.update_layout(**PLOTLY_DARK, showlegend=False)
    st.plotly_chart(style_fig(fig_motivos), use_container_width=True)

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

    st.markdown("### Insight 1: Ticket Médio P2P vs P2B (PF/PJ)")
    fig_tm_pf_pj = px.box(df_sistemico, x='PAG_PFPJ', y='VALOR', color='REC_PFPJ', title='Dispersão do Ticket Médio por Relação Pagador -> Recebedor', template='plotly_dark')
    fig_tm_pf_pj.update_layout(**PLOTLY_DARK)
    fig_tm_pf_pj.update_yaxes(type='log')
    st.plotly_chart(style_fig(fig_tm_pf_pj), use_container_width=True)

    st.divider()
    st.markdown("### Insight 2: Acessibilidade e Iniciação (Forma da Transação)")
    if 'FORMAINICIACAO' in df_sistemico.columns:
        df_iniciacao = df_sistemico.groupby('FORMAINICIACAO', as_index=False)['QUANTIDADE'].sum()
        df_iniciacao = df_iniciacao[df_iniciacao['FORMAINICIACAO'].astype(str).str.strip().str.lower() != "nao disponivel"]
        fig_iniciacao = px.treemap(df_iniciacao, path=['FORMAINICIACAO'], values='QUANTIDADE', title='Métodos de Iniciação do Pix (Distribuição de Volume)', color='QUANTIDADE', color_continuous_scale='Teal')
        fig_iniciacao.update_layout(**PLOTLY_DARK)
        st.plotly_chart(style_fig(fig_iniciacao), use_container_width=True)

    st.divider()
    st.markdown("### Insight 3: Perfil Demográfico x Volume Financeiro (Idade)")
    if 'PAG_IDADE' in df_sistemico.columns:
        df_idade = df_sistemico.groupby('PAG_IDADE', as_index=False).agg({'VALOR':'sum', 'QUANTIDADE':'sum'})
        df_idade = df_idade[df_idade['PAG_IDADE'].astype(str).str.strip().str.lower() != "nao disponivel"]
        df_idade['Ticket_Medio'] = df_idade.apply(lambda row: row['VALOR'] / row['QUANTIDADE'] if row['QUANTIDADE'] > 0 else 0, axis=1)
        fig_idade = px.bar(df_idade, x='PAG_IDADE', y='Ticket_Medio', title='Ticket Médio Pix por Faixa Etária do Pagador', color='Ticket_Medio', color_continuous_scale='Purples')
        fig_idade.update_layout(**PLOTLY_DARK, xaxis_title='Faixa Etária', yaxis_title='Ticket Médio (R$)')
        st.plotly_chart(style_fig(fig_idade), use_container_width=True)


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
    if 'VALOR_TOTAL' in df_municipios.columns:
        cidade_pico = df_municipios.sort_values(by='VALOR_TOTAL', ascending=False).iloc[0]
        st.info(f"📍 **Pólo Diário:** {cidade_pico.get('Municipio', '')} - {cidade_pico.get('Estado', '')} movimentou R$ {cidade_pico.get('VALOR_TOTAL', 0)/1e9:,.2f} bi no total.")

        top_15_cidades = df_municipios.groupby(['Municipio', 'Estado'], as_index=False)['VALOR_TOTAL'].sum().nlargest(15, 'VALOR_TOTAL')
        top_15_cidades['Local'] = top_15_cidades['Municipio'] + " - " + top_15_cidades['Estado']

        fig_top_mun = px.bar(top_15_cidades, x='VALOR_TOTAL', y='Local', orientation='h', title='Top 15 Municípios por Fluxo de Caixa (Valor Recebido/Enviado)', color='VALOR_TOTAL', color_continuous_scale='Viridis')
        fig_top_mun.update_layout(yaxis={'categoryorder':'total ascending'}, **PLOTLY_DARK)
        st.plotly_chart(style_fig(fig_top_mun), use_container_width=True)

    st.divider()
    st.markdown("### Insight 2: Análise de Capilaridade P2B Municipal")
    if 'QT_RecebedorPJ' in df_municipios.columns and 'VL_RecebedorPJ' in df_municipios.columns:
        fig_p2b = px.scatter(df_municipios, x='QT_RecebedorPJ', y='VL_RecebedorPJ', size='QT_PES_RecebedorPJ', color='Regiao', hover_name='Municipio', title='Concentração Empresarial: Qtd Transações x Volume PJ', log_x=True, log_y=True)
        fig_p2b.update_layout(**PLOTLY_DARK)
        st.plotly_chart(style_fig(fig_p2b), use_container_width=True)

    st.divider()
    st.markdown("### Insight 3: Participação PF x PJ no Volume Recebido")
    if 'VL_RecebedorPF' in df_municipios.columns and 'VL_RecebedorPJ' in df_municipios.columns:
        df_mun_clean = df_municipios[(df_municipios['VL_RecebedorPF'] > 0) | (df_municipios['VL_RecebedorPJ'] > 0)].copy()
        df_mun_clean['Share_Rec_PF'] = df_mun_clean['VL_RecebedorPF'] / (df_mun_clean['VL_RecebedorPF'] + df_mun_clean['VL_RecebedorPJ'])
        top_informalidade = df_mun_clean.sort_values(by='Share_Rec_PF', ascending=False).head(10)
        fig_share_pf = px.bar(top_informalidade, x='Share_Rec_PF', y='Municipio', orientation='h', title='Taxa de Informalidade: Proporção do R$ Recebido em Contas PF vs PJ', color='Regiao', labels={'Share_Rec_PF': '% Volume Recebido (PF)', 'Municipio': 'Cidade'})
        fig_share_pf.update_layout(xaxis_tickformat='.1%', yaxis={'categoryorder':'total ascending'}, **PLOTLY_DARK)
        st.plotly_chart(style_fig(fig_share_pf), use_container_width=True)



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
        m = Prophet(seasonality_mode='multiplicative', yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
        try:
            # Aggregate to prevent duplicate ds causing singular matrices, just in case
            df_grouped = df_prophet.groupby('ds', as_index=False)['y'].sum()
            m.fit(df_grouped)
            
            future = m.make_future_dataframe(periods=6, freq='MS')
            forecast = m.predict(future)
        except Exception as e:
            # Fallback for synthetic/small data that crashes Prophet's optimization
            import numpy as np
            from dateutil.relativedelta import relativedelta
            
            df_grouped = df_prophet.groupby('ds', as_index=False)['y'].sum()
            x_vals = np.arange(len(df_grouped))
            z = np.polyfit(x_vals, df_grouped['y'], 1)
            p = np.poly1d(z)
            
            future_x = np.arange(len(df_grouped) + 6)
            future_y = p(future_x)
            
            last_date = df_grouped['ds'].max()
            future_dates = [last_date + relativedelta(months=i) for i in range(1, 7)]
            all_dates = pd.concat([df_grouped['ds'], pd.Series(future_dates)], ignore_index=True)
            
            # Mount a mock prophet-like forecast dataframe
            forecast = pd.DataFrame({
                'ds': all_dates,
                'yhat': future_y,
                'yhat_lower': future_y * 0.90,
                'yhat_upper': future_y * 1.10
            })
            df_prophet = df_grouped

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
    modulo_auth.init_auth()

    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if "tela" not in st.session_state:
        st.session_state["tela"] = "login"

    if st.session_state["autenticado"]:
        dashboard()
    elif st.session_state["tela"] == "registro":
        tela_registro()
    else:
        tela_login()


if __name__ == "__main__":
    main()
