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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Fundo geral */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.85);
    border-right: 1px solid rgba(56, 189, 248, 0.2);
    backdrop-filter: blur(12px);
}
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #38bdf8;
}

/* Cards de métricas */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 16px;
    backdrop-filter: blur(8px);
}
[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 0.85rem;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f8fafc;
    font-weight: 700;
    font-size: 1.6rem;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.8rem;
}

/* Abas */
[data-testid="stTabs"] [data-baseweb="tab"] {
    color: #94a3b8;
    font-weight: 600;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #38bdf8 !important;
    border-bottom: 2px solid #38bdf8 !important;
}

/* Títulos */
h1, h2, h3 { color: #f8fafc; }

/* Inputs e selects */
[data-baseweb="select"] div, [data-baseweb="input"] input {
    background: rgba(30, 41, 59, 0.8) !important;
    border-color: rgba(56, 189, 248, 0.3) !important;
    color: #f8fafc !important;
}

/* Botões */
.stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #6366f1);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(14, 165, 233, 0.35);
}

/* Gráficos Plotly — fundo transparente */
.js-plotly-plot .plotly .bg {
    fill: transparent !important;
}

/* Info boxes */
.info-box {
    background: rgba(56, 189, 248, 0.08);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 10px;
    padding: 12px 16px;
    color: #94a3b8;
    font-size: 0.88rem;
    margin-bottom: 16px;
}

/* Login card */
.login-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 40px;
    backdrop-filter: blur(12px);
    max-width: 440px;
    margin: 80px auto 0;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE PLOTLY (tema dark reutilizável)
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_DARK = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#f8fafc",
    font_family="Outfit",
    title_font_family="Outfit",
    title_font_size=18,
    hovermode="x unified",
    margin=dict(t=55, l=20, r=20, b=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
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

    st.markdown("</div>", unsafe_allow_html=True)


def tela_registro():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
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

    st.markdown("</div>", unsafe_allow_html=True)


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

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("🕵️ Marcações de Fraude",    f"{df['QtdeUsuarioscommarcacoesdefraude'].sum():,}")
    c2.metric("💰 Recuperado pelo MED",     f"R$ {df['ValorPixdevolvidosintegralmente'].sum():,.0f}")
    c3.metric("⚠️ Perda Residual",          f"R$ {df['ValorPixresidualnaodevolvido'].sum():,.0f}")

    st.divider()

    # Gráfico de área: evolução temporal
    fig_ev = px.area(
        df, x="MesesFormatados",
        y=["QtdePixcontestados", "Qtdecontestacoesaceitas"],
        title="Evolução: Pix Contestados vs Devoluções Aceitas",
        labels={"value": "Volume", "variable": "Métrica", "MesesFormatados": ""},
        color_discrete_sequence=["#38bdf8", "#8b5cf6"],
    )
    style_fig(fig_ev)

    # Gráfico pizza: motivos de não devolução (último mês)
    ultimo = df.iloc[-1]
    fig_pie = px.pie(
        names=["Saldo Insuficiente", "Conta Encerrada", "Outros"],
        values=[
            ultimo.get("ValorPixnaodevolvidossaldoinsuficiente", 0),
            ultimo.get("Valornaodevolvidoscontaencerrada", 0),
            ultimo.get("ValorPixnaodevolvidosmotivosdiversos", 0),
        ],
        hole=0.5,
        title=f"Por que não devolvido? ({ultimo['MesesFormatados']})",
        color_discrete_sequence=["#f43f5e", "#f59e0b", "#10b981"],
    )
    style_fig(fig_pie, hovermode=False)

    col_a, col_b = st.columns([2, 1])
    col_a.plotly_chart(fig_ev,  use_container_width=True)
    col_b.plotly_chart(fig_pie, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# ABA 2: CONTESTAÇÕES vs DEVOLUÇÕES
# ─────────────────────────────────────────────────────────────────────────────
def aba_contestacoes(df, periodo_key):
    if df.empty:
        st.warning("Sem dados de fraudes disponíveis.")
        return

    if periodo_key == "ultimos3":
        df = df.tail(3)
    elif periodo_key == "ultimos6":
        df = df.tail(6)

    # Colunas flexíveis
    col_int = next(
        (c for c in ["QuantidadedevolvidaintegralmentepormeiodoMED", "QtdePixdevolvidosintegralmente"] if c in df.columns),
        None,
    )
    col_par = next(
        (c for c in ["QuantidadedevolvidaparcialmentepormeiodoMED", "QtdePixdevolvidosparcialmente"] if c in df.columns),
        None,
    )

    df = df.copy()
    df["TotalDevolvido"] = (df[col_int] if col_int else 0) + (df[col_par] if col_par else 0)
    df["TaxaSucesso"]    = (df["TotalDevolvido"] / df["QtdePixcontestados"]) * 100

    total_cont = df["QtdePixcontestados"].sum()
    total_dev  = df["TotalDevolvido"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("📢 Total Contestações",    f"{total_cont:,}")
    c2.metric("🤝 Total Devolvido (Qtd)", f"{total_dev:,}")
    c3.metric("📊 Taxa de Sucesso Média", f"{(total_dev/total_cont*100):.2f}%")

    st.divider()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df["MesesFormatados"], y=df["QtdePixcontestados"], name="Contestações",      marker_color="#f43f5e", opacity=0.85), secondary_y=False)
    fig.add_trace(go.Bar(x=df["MesesFormatados"], y=df["TotalDevolvido"],     name="Devoluções",        marker_color="#10b981", opacity=0.85), secondary_y=False)
    fig.add_trace(go.Scatter(x=df["MesesFormatados"], y=df["TaxaSucesso"], name="Taxa Devolução (%)",
                             mode="lines+markers", line=dict(color="#38bdf8", width=3), marker=dict(size=8, symbol="diamond")), secondary_y=True)

    fig.update_layout(**{**PLOTLY_DARK, "title_text": "Volume Mensal: Contestações vs Devoluções Efetivas", "barmode": "group"})
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(title_text="Qtd", gridcolor="rgba(255,255,255,0.05)", secondary_y=False)
    fig.update_yaxes(title_text="Taxa %", showgrid=False, secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# ABA 3: ESTATÍSTICAS SISTÊMICAS PIX
# ─────────────────────────────────────────────────────────────────────────────
def aba_estatisticas(df_t, sel_pfpj, sel_reg):
    if df_t.empty:
        st.warning("Execute `exemplos/07_estatisticas_pix.py` para gerar os dados de transações.")
        return

    # Aplica filtros
    df = df_t.copy()
    if sel_pfpj != "Todos" and "PAG_PFPJ" in df.columns:
        df = df[df["PAG_PFPJ"] == sel_pfpj]
    if sel_reg != "Todas" and "PAG_REGIAO" in df.columns:
        df = df[df["PAG_REGIAO"] == sel_reg]

    if df.empty:
        st.info("Nenhum dado para os filtros selecionados.")
        return

    # Período coberto
    periodo = ", ".join(sorted(str(m)[:4] + "-" + str(m)[4:] for m in df["AnoMes"].unique())) if "AnoMes" in df.columns else "N/A"

    total_qtd    = df["QUANTIDADE"].sum()   if "QUANTIDADE" in df.columns else 0
    total_valor  = df["VALOR"].sum()        if "VALOR"      in df.columns else 0
    ticket_medio = total_valor / total_qtd  if total_qtd > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Qtd Total Transações", f"{total_qtd:,.0f}",    delta=f"Período: {periodo}")
    c2.metric("💵 Volume Financeiro",    f"R$ {total_valor/1e12:.2f} tri")
    c3.metric("🧾 Ticket Médio",         f"R$ {ticket_medio:,.2f}")

    st.divider()

    col_a, col_b = st.columns(2)

    # Gráfico 1: por TIPO
    with col_a:
        if "TIPO" in df.columns:
            df_tipo = df.groupby("TIPO", as_index=False)[["QUANTIDADE", "VALOR"]].sum().sort_values("QUANTIDADE", ascending=False)
            fig_tipo = px.bar(df_tipo, x="TIPO", y="QUANTIDADE", title="Volume por Tipo de Transação",
                              color="TIPO", color_discrete_sequence=px.colors.qualitative.Bold, text_auto=".2s")
            style_fig(fig_tipo, showlegend=False)
            st.plotly_chart(fig_tipo, use_container_width=True)

    # Gráfico 2: treemap por Região
    with col_b:
        if "PAG_REGIAO" in df.columns:
            df_reg = df.groupby("PAG_REGIAO", as_index=False)[["QUANTIDADE", "VALOR"]].sum()
            df_reg = df_reg[df_reg["PAG_REGIAO"].str.strip().str.lower() != "nao disponivel"]
            fig_reg = px.treemap(df_reg, path=["PAG_REGIAO"], values="VALOR",
                                 title="Volume Financeiro por Região (Pagador)",
                                 color="VALOR", color_continuous_scale="Tealgrn")
            fig_reg.update_layout(**{**PLOTLY_DARK, "hovermode": False, "margin": dict(t=50, l=10, r=10, b=10), "coloraxis_showscale": False})

            st.plotly_chart(fig_reg, use_container_width=True)

    # Gráfico 3: PF vs PJ
    if "PAG_PFPJ" in df.columns and "REC_PFPJ" in df.columns:
        df_pag  = df.groupby("PAG_PFPJ", as_index=False)[["QUANTIDADE"]].sum().rename(columns={"PAG_PFPJ": "PFPJ", "QUANTIDADE": "Pagador"})
        df_rec  = df.groupby("REC_PFPJ", as_index=False)[["QUANTIDADE"]].sum().rename(columns={"REC_PFPJ": "PFPJ", "QUANTIDADE": "Recebedor"})
        df_pfpj = pd.merge(df_pag, df_rec, on="PFPJ", how="outer").fillna(0)
        df_pfpj = df_pfpj[df_pfpj["PFPJ"].str.strip().str.lower() != "nao disponivel"]

        fig_pfpj = go.Figure([
            go.Bar(name="Pagador",    x=df_pfpj["PFPJ"], y=df_pfpj["Pagador"],    marker_color="#38bdf8"),
            go.Bar(name="Recebedor",  x=df_pfpj["PFPJ"], y=df_pfpj["Recebedor"],  marker_color="#a78bfa"),
        ])
        fig_pfpj.update_layout(**{**PLOTLY_DARK, "title": "Comparativo PF vs PJ: Pagador e Recebedor", "barmode": "group"})
        fig_pfpj.update_xaxes(showgrid=False)
        fig_pfpj.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig_pfpj, use_container_width=True)

    # Gráfico 4: Finalidade (se disponível)
    if "FINALIDADE" in df.columns:
        df_fin = df.groupby("FINALIDADE", as_index=False)[["QUANTIDADE", "VALOR"]].sum()
        df_fin = df_fin[df_fin["FINALIDADE"].str.strip().str.lower() != "nao disponivel"]
        df_fin = df_fin.sort_values("VALOR", ascending=False)
        fig_fin = px.bar(df_fin, x="FINALIDADE", y="VALOR",
                         title="Volume Financeiro por Finalidade",
                         color="FINALIDADE", color_discrete_sequence=px.colors.qualitative.Pastel,
                         text_auto=".2s")
        style_fig(fig_fin, showlegend=False)
        st.plotly_chart(fig_fin, use_container_width=True)


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

    df_mun = load_dados_municipios()

    if df_mun.empty:
        st.error("Não foi possível carregar os dados municipais. Verifique sua conexão com a internet.")
        return

    # Determina coluna de métrica e fluxo
    fluxo_col_map = {
        "Total":        {"Valor (R$)": "VALOR_TOTAL",    "Quantidade": "QT_TOTAL"},
        "Pagador PF":   {"Valor (R$)": "VL_PagadorPF",  "Quantidade": "QT_PagadorPF"},
        "Pagador PJ":   {"Valor (R$)": "VL_PagadorPJ",  "Quantidade": "QT_PagadorPJ"},
        "Recebedor PF": {"Valor (R$)": "VL_RecebedorPF","Quantidade": "QT_RecebedorPF"},
        "Recebedor PJ": {"Valor (R$)": "VL_RecebedorPJ","Quantidade": "QT_RecebedorPJ"},
    }
    metrica_col = fluxo_col_map.get(sel_fluxo, {}).get(sel_metrica, "VALOR_TOTAL")
    if metrica_col not in df_mun.columns:
        metrica_col = "VALOR_TOTAL"

    label_metrica = sel_metrica

    # ── KPIs Nacionais ─────────────────────────────────────────────────────
    total_nacional = df_mun[metrica_col].sum() if metrica_col in df_mun.columns else 0
    n_estados      = df_mun["Estado"].nunique()  if "Estado"    in df_mun.columns else 0
    n_municipios   = df_mun["Municipio"].nunique() if "Municipio" in df_mun.columns else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("🌎 Total Nacional",   f"R$ {total_nacional/1e9:.1f} bi" if "Valor" in sel_metrica else f"{total_nacional:,.0f}")
    c2.metric("🏛️ Estados cobertos", str(n_estados))
    c3.metric("🏙️ Municípios",       str(n_municipios))

    st.divider()

    # ── Mapa Choropleth por Estado ──────────────────────────────────────────
    geojson = _load_geojson()
    if "Estado" in df_mun.columns and geojson:
        df_estado = df_mun.groupby("Estado", as_index=False)[[metrica_col]].sum()

        fig_mapa = px.choropleth_mapbox(
            df_estado,
            geojson=geojson,
            locations="Estado",
            featureidkey="properties.sigla",
            color=metrica_col,
            color_continuous_scale="Viridis",
            mapbox_style="carto-darkmatter",
            zoom=3.5,
            center={"lat": -15.78, "lon": -47.93},
            opacity=0.75,
            labels={metrica_col: label_metrica},
            title=f"Distribuição por Estado — {sel_fluxo} ({sel_metrica})",
        )
        fig_mapa.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f8fafc",
            font_family="Outfit",
            margin={"r": 0, "t": 45, "l": 0, "b": 0},
            coloraxis_colorbar=dict(title=label_metrica),
        )
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.warning("GeoJSON não disponível. Mapa não pôde ser renderizado.")

    st.divider()

    # ── Gráfico de barras: Top 20 Municípios do estado selecionado ──────────
    st.markdown(f"### 🏙️ Top 20 Municípios — **{sel_uf}**")

    filtro_buscador = st.text_input("🔍 Buscar município", placeholder="Ex: São Paulo", key="busca_mun")

    if "Estado" in df_mun.columns and "Municipio" in df_mun.columns:
        df_uf = df_mun[df_mun["Estado"] == sel_uf].copy()

        if filtro_buscador:
            df_uf = df_uf[df_uf["Municipio"].str.contains(filtro_buscador, case=False, na=False)]

        df_top = (
            df_uf.groupby("Municipio", as_index=False)[[metrica_col]].sum()
            .sort_values(metrica_col, ascending=False)
            .head(20)
        )

        if df_top.empty:
            st.info(f"Nenhum município encontrado para '{sel_uf}'" + (f" com filtro '{filtro_buscador}'" if filtro_buscador else "") + ".")
        else:
            fig_bar = px.bar(
                df_top,
                x=metrica_col,
                y="Municipio",
                orientation="h",
                title=f"Top 20 — {sel_uf} | {sel_fluxo} | {sel_metrica}",
                color=metrica_col,
                color_continuous_scale="Blues",
                labels={metrica_col: label_metrica, "Municipio": ""},
                text_auto=".2s",
            )
            fig_bar.update_layout(**{
                **PLOTLY_DARK,
                "hovermode": False,
                "coloraxis_showscale": False,
                "yaxis": {"categoryorder": "total ascending"},
                "margin": {"t": 50, "b": 20, "l": 140, "r": 20},
            })
            fig_bar.update_xaxes(showgrid=False)
            fig_bar.update_yaxes(showgrid=False)
            st.plotly_chart(fig_bar, use_container_width=True)

    # ── Tabela detalhada ────────────────────────────────────────────────────
    with st.expander("📋 Ver tabela completa de municípios"):
        if "Estado" in df_mun.columns:
            df_tabela = df_mun[df_mun["Estado"] == sel_uf].copy()
            if filtro_buscador:
                df_tabela = df_tabela[df_tabela["Municipio"].str.contains(filtro_buscador, case=False, na=False)]

            cols_show = [c for c in ["Municipio", "Estado", "VALOR_TOTAL", "QT_TOTAL",
                                      "VL_PagadorPF", "VL_PagadorPJ", "VL_RecebedorPF", "VL_RecebedorPJ"] if c in df_tabela.columns]
            st.dataframe(
                df_tabela[cols_show].sort_values(metrica_col, ascending=False).reset_index(drop=True),
                use_container_width=True,
                height=350,
            )


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

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Visão Geral",
        "🔄 Contestações vs Devoluções",
        "📈 Estatísticas Sistêmicas PIX",
        "🗺️ Transações por Município",
    ])

    with tab1:
        aba_visao_geral(df_fraudes, periodo_key)

    with tab2:
        aba_contestacoes(df_fraudes, periodo_key)

    with tab3:
        aba_estatisticas(df_trans, sel_pfpj, sel_reg)

    with tab4:
        aba_municipios(sel_uf, sel_metrica, sel_fluxo)


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
