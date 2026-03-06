import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import os
import glob
import json

import modulo_auth  # Importa nossa lógica de autenticação segura

# ─────────────────────────────────────────────────────────────────────────────
# CARREGAMENTO DE DADOS PIX
# ─────────────────────────────────────────────────────────────────────────────
def load_dados_fraudes():
    """Procura pelo json salvo pelo exemplo 06 e converte em DataFrame Pandas."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pasta_dados = os.path.join(base_dir, "dados")
    
    arquivos_json = glob.glob(os.path.join(pasta_dados, "fraudes_pix_*.json"))
    if not arquivos_json: return pd.DataFrame()
    
    df = pd.read_json(arquivos_json[-1])
    if not df.empty and 'AnoMes' in df.columns:
        df = df.sort_values(by='AnoMes')
        df['MesesFormatados'] = df['AnoMes'].astype(str).str[:4] + "-" + df['AnoMes'].astype(str).str[4:]
    return df

def load_dados_transacoes():
    """Lê os dados brutos de Estatísticas de Transações Pix preservando todas as colunas."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pasta_dados = os.path.join(base_dir, "dados")
    
    arquivos_json = glob.glob(os.path.join(pasta_dados, "estatisticas_transacoes_*.json"))
    if not arquivos_json:
        return pd.DataFrame()
    
    try:
        df_transacoes = pd.read_json(arquivos_json[-1])
        return df_transacoes
    except Exception as e:
        print(f"Erro lendo transacoes: {e}")
        
    return pd.DataFrame()


def layout_aba_estatisticas():
    """Constrói a Aba 3 de forma completamente independente, com seus próprios dados."""
    import plotly.graph_objects as go

    df_t = load_dados_transacoes()

    if df_t.empty:
        return html.Div([
            html.I(className="fa-solid fa-triangle-exclamation fa-3x text-warning mb-3"),
            html.H4("Dados não encontrados", className="text-light"),
            html.P(
                "Execute o script exemplos/07_estatisticas_pix.py para gerar o arquivo "
                "estatisticas_transacoes_*.json na pasta dados/.",
                className="text-muted"
            )
        ], className="text-center p-5 glass-panel mt-4 mx-auto", style={"maxWidth": "600px"})

    # ── Período coberto ──────────────────────────────────────────────────────
    periodo = ", ".join(
        sorted(str(m)[:4] + "-" + str(m)[4:] for m in df_t['AnoMes'].unique())
    ) if 'AnoMes' in df_t.columns else "N/A"

    # ── KPIs globais ─────────────────────────────────────────────────────────
    total_qtd   = df_t['QUANTIDADE'].sum() if 'QUANTIDADE' in df_t.columns else 0
    total_valor = df_t['VALOR'].sum()      if 'VALOR'      in df_t.columns else 0
    ticket_medio = total_valor / total_qtd if total_qtd > 0 else 0

    kpi_qtd = dbc.Card([dbc.CardBody([
        html.P([html.I(className="fa-solid fa-layer-group me-2 text-primary"), "Qtd Total Transações"], className="metric-label"),
        html.H3(f"{total_qtd:,.0f}", className="metric-value text-primary"),
        html.Small(f"Período: {periodo}", className="text-muted")
    ])], className="glass-panel glass-card-hover h-100")

    kpi_valor = dbc.Card([dbc.CardBody([
        html.P([html.I(className="fa-solid fa-sack-dollar me-2 text-success"), "Volume Financeiro (R$)"], className="metric-label"),
        html.H3(f"R$ {total_valor / 1e12:.2f} tri", className="metric-value text-success", style={'fontSize': '1.8rem'}),
    ])], className="glass-panel glass-card-hover h-100")

    kpi_ticket = dbc.Card([dbc.CardBody([
        html.P([html.I(className="fa-solid fa-receipt me-2 text-info"), "Ticket Médio"], className="metric-label"),
        html.H3(f"R$ {ticket_medio:,.2f}", className="metric-value text-info", style={'fontSize': '1.8rem'}),
    ])], className="glass-panel glass-card-hover h-100")

    # ── Gráfico 1: Quantidade por TIPO ───────────────────────────────────────
    if 'TIPO' in df_t.columns:
        df_tipo = df_t.groupby('TIPO', as_index=False)[['QUANTIDADE', 'VALOR']].sum().sort_values('QUANTIDADE', ascending=False)
        fig_tipo = px.bar(
            df_tipo, x='TIPO', y='QUANTIDADE',
            title="Volume de Transações por Tipo",
            color='TIPO',
            color_discrete_sequence=px.colors.qualitative.Bold,
            text_auto='.2s'
        )
    else:
        fig_tipo = go.Figure()
        fig_tipo.add_annotation(text="Coluna TIPO não disponível", showarrow=False)

    fig_tipo.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc",
        title_font_family="Outfit", title_font_size=18, showlegend=False,
        margin=dict(t=50, l=20, r=20, b=40)
    )
    fig_tipo.update_xaxes(showgrid=False)
    fig_tipo.update_yaxes(gridcolor="rgba(255,255,255,0.05)")

    # ── Gráfico 2: Volume por Região Pagador (treemap) ───────────────────────
    if 'PAG_REGIAO' in df_t.columns:
        df_reg = df_t.groupby('PAG_REGIAO', as_index=False)[['QUANTIDADE', 'VALOR']].sum()
        df_reg = df_reg[df_reg['PAG_REGIAO'].str.strip().str.lower() != 'nao disponivel']
        fig_regiao = px.treemap(
            df_reg, path=['PAG_REGIAO'], values='VALOR',
            title="Volume Financeiro por Região (Pagador)",
            color='VALOR',
            color_continuous_scale='Tealgrn'
        )
    else:
        fig_regiao = go.Figure()
        fig_regiao.add_annotation(text="Coluna PAG_REGIAO não disponível", showarrow=False)

    fig_regiao.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc",
        title_font_family="Outfit", title_font_size=18,
        margin=dict(t=50, l=10, r=10, b=10),
        coloraxis_showscale=False
    )

    # ── Gráfico 3: PFPJ Pagador vs Recebedor ────────────────────────────────
    if 'PAG_PFPJ' in df_t.columns and 'REC_PFPJ' in df_t.columns:
        df_pag = df_t.groupby('PAG_PFPJ', as_index=False)[['QUANTIDADE']].sum().rename(columns={'PAG_PFPJ': 'PFPJ', 'QUANTIDADE': 'Pagador'})
        df_rec = df_t.groupby('REC_PFPJ', as_index=False)[['QUANTIDADE']].sum().rename(columns={'REC_PFPJ': 'PFPJ', 'QUANTIDADE': 'Recebedor'})
        df_pfpj = pd.merge(df_pag, df_rec, on='PFPJ', how='outer').fillna(0)
        df_pfpj = df_pfpj[df_pfpj['PFPJ'].str.strip().str.lower() != 'nao disponivel']

        fig_pfpj = go.Figure(data=[
            go.Bar(name='Pagador', x=df_pfpj['PFPJ'], y=df_pfpj['Pagador'], marker_color='#38bdf8'),
            go.Bar(name='Recebedor', x=df_pfpj['PFPJ'], y=df_pfpj['Recebedor'], marker_color='#a78bfa'),
        ])
        fig_pfpj.update_layout(
            title="Comparativo PF vs PJ: Pagador e Recebedor",
            barmode='group',
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc",
            title_font_family="Outfit", title_font_size=18,
            margin=dict(t=50, l=20, r=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_pfpj.update_xaxes(showgrid=False)
        fig_pfpj.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    else:
        fig_pfpj = go.Figure()
        fig_pfpj.add_annotation(text="Colunas PF/PJ não disponíveis", showarrow=False)

    return html.Div([
        dbc.Row([
            dbc.Col(kpi_qtd,   md=4, className="mb-4"),
            dbc.Col(kpi_valor, md=4, className="mb-4"),
            dbc.Col(kpi_ticket, md=4, className="mb-4")
        ]),
        dbc.Row([
            dbc.Col(html.Div(dcc.Graph(figure=fig_tipo,   config={'displayModeBar': False}), className="glass-panel p-3 h-100"), md=6, className="mb-4"),
            dbc.Col(html.Div(dcc.Graph(figure=fig_regiao, config={'displayModeBar': False}), className="glass-panel p-3 h-100"), md=6, className="mb-4"),
        ]),
        dbc.Row([
            dbc.Col(html.Div(dcc.Graph(figure=fig_pfpj,  config={'displayModeBar': False}), className="glass-panel p-3"), md=12, className="mb-4")
        ])
    ], className="mt-4")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DO APP DASH
# ─────────────────────────────────────────────────────────────────────────────
# Usamos o tema escuro do Dash Bootstrap e FontAwesome para ícones premium.
FA_URL = "https://use.fontawesome.com/releases/v6.4.2/css/all.css"
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.CYBORG, FA_URL],
    suppress_callback_exceptions=True
)
app.title = "Painel BCB - Fraudes Pix"

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENTES VISUAIS E TELAS
# ─────────────────────────────────────────────────────────────────────────────

# --- TELA DE LOGIN ---
def layout_login():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.I(className="fa-solid fa-shield-halved fa-3x mb-3", style={"color": "var(--accent-glow)"}),
                        html.H2("Acesso Restrito", className="fw-bold", style={"color": "#FFFFFF"}),
                        html.P("Painel de Fraudes do Sistema Pix BCB", className="text-muted"),
                    ], className="text-center mb-4"),
                    
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fa-solid fa-envelope")),
                        dbc.Input(id="input-email-login", type="email", placeholder="E-mail corporativo")
                    ], className="mb-3"),
                    
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fa-solid fa-lock")),
                        dbc.Input(id="input-senha-login", type="password", placeholder="Senha de acesso")
                    ], className="mb-4"),
                    
                    dbc.Button([html.I(className="fa-solid fa-right-to-bracket me-2"), "Entrar no Painel"], id="btn-login", color="primary", class_name="w-100 mb-3 glass-card-hover", n_clicks=0),
                    html.Div(id="msg-login", className="text-center mt-2"),
                    html.Hr(style={"borderColor": "var(--glass-border)"}),
                    html.P("Não tem uma credencial?", className="text-center mt-3 text-muted"),
                    dbc.Button("Solicitar Acesso", id="btn-ir-registro", color="outline-info", class_name="w-100 glass-card-hover", n_clicks=0)
                ], className="p-5 glass-panel", style={"marginTop": "100px"})
            ], xs=11, sm=8, md=6, lg=4)
        ], justify="center")
    ], fluid=True, className="min-vh-100")


# --- TELA DE CADASTRO ---
def layout_registro():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.I(className="fa-solid fa-user-plus fa-3x mb-3", style={"color": "#10b981"}),
                        html.H2("Nova Credencial", className="text-light fw-bold"),
                        html.P("A senha deve ter 8+ chars, maiúscula, minúscula, número e símbolo.", className="text-muted", style={"fontSize": "0.85em"}),
                    ], className="text-center mb-4"),
                    
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fa-solid fa-envelope")),
                        dbc.Input(id="input-email-reg", type="email", placeholder="E-mail com domínio corporativo")
                    ], className="mb-3"),
                    
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fa-solid fa-key")),
                        dbc.Input(id="input-senha-reg", type="password", placeholder="Criar senha forte")
                    ], className="mb-3"),
                    
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fa-solid fa-check-double")),
                        dbc.Input(id="input-senha-conf-reg", type="password", placeholder="Confirmar senha")
                    ], className="mb-4"),
                    
                    dbc.Button([html.I(className="fa-solid fa-user-check me-2"), "Registrar Usuário"], id="btn-registrar", color="success", class_name="w-100 mb-3 glass-card-hover", n_clicks=0),
                    html.Div(id="msg-registro", className="text-center mt-2"),
                    
                    html.Hr(style={"borderColor": "var(--glass-border)"}),
                    dbc.Button([html.I(className="fa-solid fa-arrow-left me-2"), "Voltar ao Login"], id="btn-ir-login", color="link", class_name="w-100 text-decoration-none text-muted glass-card-hover", n_clicks=0)
                ], className="p-5 glass-panel", style={"marginTop": "80px"})
            ], xs=11, sm=8, md=6, lg=5)
        ], justify="center")
    ], fluid=True, className="min-vh-100")


# --- TELA DO DASHBOARD PROTEGIDO ---
def layout_dashboard():
    df = load_dados_fraudes()
    
    # Navbar Moderna
    navbar = dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.Row([
                    dbc.Col(html.I(className="fa-brands fa-pix fa-2x", style={"color": "#32bcad"})),
                    dbc.Col(html.Span("Estatísticas MED / BCB", className="ms-2 navbar-brand-custom")),
                ], align="center", className="g-0"),
                href="#", style={"textDecoration": "none"}
            ),
            dbc.Button([html.I(className="fa-solid fa-power-off me-2"), "Encerrar Sessão"], id="btn-logout", color="outline-light", size="sm", className="glass-card-hover")
        ], fluid=True),
        color="rgba(15, 23, 42, 0.7)",
        dark=True,
        className="mb-4 shadow-sm border-bottom border-secondary",
        style={"backdropFilter": "blur(10px)"}
    )
    
    if df.empty:
        conteudo = html.Div([
            html.I(className="fa-solid fa-triangle-exclamation fa-4x text-warning mb-4"),
            html.H3("Nenhum dado local encontrado", className="text-light"),
            html.P("Execute o script de coleta do BCB (06_fraude_med.py) para gerar o arquivo JSON na pasta 'dados/'.", className="text-muted")
        ], className="text-center p-5 glass-panel mt-5 mx-auto", style={"maxWidth": "600px"})
    else:
        # ==========================================
        # ABA 1: VISÃO GERAL (O que já tínhamos)
        # ==========================================
        
        # Gráficos com paleta neon e fundos transparentes
        fig_evolucao = px.area(df, x='MesesFormatados', y=['QtdePixcontestados', 'Qtdecontestacoesaceitas'],
                               title="Evolução Temporal: Pix Contestados vs Devoluções Aceitas",
                               labels={"value": "Volume de Transações", "variable": "Métrica", "MesesFormatados": ""},
                               color_discrete_sequence=["#38bdf8", "#8b5cf6"])
        
        fig_evolucao.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc",
            title_font_family="Outfit", title_font_size=20, hovermode="x unified",
            margin=dict(t=50, l=20, r=20, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_evolucao.update_xaxes(showgrid=False)
        fig_evolucao.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        
        # Gráfico Pizza (Último mês)
        ultimo_mes = df.iloc[-1]
        motivos = ['Saldo Insuficiente', 'Conta Encerrada', 'Diversos']
        valores_motivos = [
            ultimo_mes.get('ValorPixnaodevolvidossaldoinsuficiente', 0),
            ultimo_mes.get('Valornaodevolvidoscontaencerrada', 0),
            ultimo_mes.get('ValorPixnaodevolvidosmotivosdiversos', 0)
        ]
        fig_motivos = px.pie(names=motivos, values=valores_motivos, hole=0.5,
                             title=f"Por que não devolvido? ({ultimo_mes['MesesFormatados']})",
                             color_discrete_sequence=["#f43f5e", "#f59e0b", "#10b981"])
        
        fig_motivos.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc",
            title_font_family="Outfit", hoverlabel=dict(bgcolor="rgba(15,23,42,0.9)", font_size=14, font_family="Outfit"),
            margin=dict(t=50, l=20, r=20, b=20)
        )
        
        # Componentes Numéricos (KPIs Aba 1)
        kpi_1 = dbc.Card([
            dbc.CardBody([
                html.P([html.I(className="fa-solid fa-user-ninja me-2 text-info"), "Marcações de Fraude"], className="metric-label"),
                html.H3(f"{df['QtdeUsuarioscommarcacoesdefraude'].sum():,}", className="metric-value text-info")
            ])
        ], className="glass-panel glass-card-hover h-100")
        
        kpi_2 = dbc.Card([
            dbc.CardBody([
                html.P([html.I(className="fa-solid fa-money-bill-transfer me-2 text-success"), "Recuperado pelo MED"], className="metric-label"),
                html.H3(f"R$ {df['ValorPixdevolvidosintegralmente'].sum():,.0f}", className="metric-value text-success")
            ])
        ], className="glass-panel glass-card-hover h-100")
        
        kpi_3 = dbc.Card([
            dbc.CardBody([
                html.P([html.I(className="fa-solid fa-triangle-exclamation me-2 text-danger"), "Perda Residual"], className="metric-label"),
                html.H3(f"R$ {df['ValorPixresidualnaodevolvido'].sum():,.0f}", className="metric-value text-danger")
            ])
        ], className="glass-panel glass-card-hover h-100")

        aba_visao_geral = html.Div([
            dbc.Row([dbc.Col(kpi_1, md=4, className="mb-4"), dbc.Col(kpi_2, md=4, className="mb-4"), dbc.Col(kpi_3, md=4, className="mb-4")]),
            dbc.Row([
                dbc.Col(html.Div(dcc.Graph(figure=fig_evolucao, config={'displayModeBar': False}), className="glass-panel p-3 h-100"), md=8, className="mb-4"),
                dbc.Col(html.Div(dcc.Graph(figure=fig_motivos, config={'displayModeBar': False}), className="glass-panel p-3 h-100"), md=4, className="mb-4"),
            ])
        ], className="mt-4")


        # ==========================================
        # ABA 2: ANÁLISE DE CONTESTAÇÕES vs DEVOLUÇÕES
        # ==========================================
        
        # Preparação dos Dados da Aba 2
        # Tenta lidar com possíveis variações no nome da coluna vindo da API
        col_integral = 'QuantidadedevolvidaintegralmentepormeiodoMED' if 'QuantidadedevolvidaintegralmentepormeiodoMED' in df.columns else 'QtdePixdevolvidosintegralmente'
        col_parcial = 'QuantidadedevolvidaparcialmentepormeiodoMED' if 'QuantidadedevolvidaparcialmentepormeiodoMED' in df.columns else 'QtdePixdevolvidosparcialmente'
        
        df['TotalDevolvidoPix'] = df.get(col_integral, 0) + df.get(col_parcial, 0)
        df['TaxaSucessoDevolucao'] = (df['TotalDevolvidoPix'] / df['QtdePixcontestados']) * 100
        
        # KPIs da Aba 2
        total_contestacoes = df['QtdePixcontestados'].sum()
        total_devolvido = df['TotalDevolvidoPix'].sum()
        
        kpi_aba2_1 = dbc.Card([
            dbc.CardBody([
                html.P([html.I(className="fa-solid fa-bullhorn me-2 text-warning"), "Total Contestações"], className="metric-label"),
                html.H3(f"{total_contestacoes:,}", className="metric-value text-warning")
            ])
        ], className="glass-panel glass-card-hover h-100")

        kpi_aba2_2 = dbc.Card([
            dbc.CardBody([
                html.P([html.I(className="fa-solid fa-hand-holding-dollar me-2 text-success"), "Total Devolvido (Qtd)"], className="metric-label"),
                html.H3(f"{total_devolvido:,}", className="metric-value text-success")
            ])
        ], className="glass-panel glass-card-hover h-100")
        
        kpi_aba2_3 = dbc.Card([
            dbc.CardBody([
                html.P([html.I(className="fa-solid fa-percent me-2 text-info"), "Taxa de Sucesso Média"], className="metric-label"),
                html.H3(f"{(total_devolvido / total_contestacoes * 100):.2f}%", className="metric-value text-info")
            ])
        ], className="glass-panel glass-card-hover h-100")
        
        # Gráfico Comparativo Aba 2
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots  # noqa: F811 (já importado globalmente abaixo se necessário)

        fig_compare = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Barras Contestações
        fig_compare.add_trace(
            go.Bar(x=df['MesesFormatados'], y=df['QtdePixcontestados'], name="Contestações Abertas", marker_color="#f43f5e", opacity=0.8),
            secondary_y=False,
        )
        
        # Barras Devoluções
        fig_compare.add_trace(
            go.Bar(x=df['MesesFormatados'], y=df['TotalDevolvidoPix'], name="Devoluções Realizadas", marker_color="#10b981", opacity=0.9),
            secondary_y=False,
        )
        
        # Linha Taxa de Sucesso
        fig_compare.add_trace(
            go.Scatter(x=df['MesesFormatados'], y=df['TaxaSucessoDevolucao'], name="Taxa de Devolução (%)", 
                       mode='lines+markers', line=dict(color='#38bdf8', width=3), marker=dict(size=8, symbol='diamond')),
            secondary_y=True,
        )
        
        fig_compare.update_layout(
            title_text="Volume Mensal: Contestações vs Devoluções Efetivas",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc",
            title_font_family="Outfit", title_font_size=20, hovermode="x unified",
            barmode='group',
            margin=dict(t=50, l=20, r=20, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_compare.update_xaxes(showgrid=False)
        fig_compare.update_yaxes(title_text="Qtd Transações", gridcolor="rgba(255,255,255,0.05)", secondary_y=False)
        fig_compare.update_yaxes(title_text="Taxa %", showgrid=False, secondary_y=True)

        aba_contestacoes = html.Div([
            dbc.Row([dbc.Col(kpi_aba2_1, md=4, className="mb-4"), dbc.Col(kpi_aba2_2, md=4, className="mb-4"), dbc.Col(kpi_aba2_3, md=4, className="mb-4")]),
            dbc.Row([
                dbc.Col(html.Div(dcc.Graph(figure=fig_compare, config={'displayModeBar': False}), className="glass-panel p-3 mb-4"), md=12)
            ])
        ], className="mt-4")


        # ==========================================
        # ABA 3: ESTATÍSTICAS SISTÊMICAS PIX (independente)
        # ==========================================
        aba_integrada = layout_aba_estatisticas()

        # ==========================================
        # ESTRUTURA DE ABAS
        # ==========================================
        conteudo = dbc.Tabs(
            [
                dbc.Tab(aba_visao_geral, label="Visão Geral", tab_id="tab-1", label_style={"color": "white", "fontWeight": "bold"}, active_tab_style={"backgroundColor": "rgba(56, 189, 248, 0.2)", "borderBottom": "2px solid #38bdf8"}),
                dbc.Tab(aba_contestacoes, label="Análise: Contestações vs Devoluções", tab_id="tab-2", label_style={"color": "white", "fontWeight": "bold"}, active_tab_style={"backgroundColor": "rgba(56, 189, 248, 0.2)", "borderBottom": "2px solid #38bdf8"}),
                dbc.Tab(aba_integrada, label="Estatísticas Sistêmicas PIX", tab_id="tab-3", label_style={"color": "white", "fontWeight": "bold"}, active_tab_style={"backgroundColor": "rgba(56, 189, 248, 0.2)", "borderBottom": "2px solid #38bdf8"}),
            ],
            id="tabs-dashboard",
            active_tab="tab-1",
            className="mb-3"
        )

    return html.Div([navbar, dbc.Container(conteudo, fluid=True)], className="min-vh-100 pb-5")


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT PRINCIPAL (Com roteamento de estado)
# ─────────────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Store(id='sessao-usuario', storage_type='session'),  # Armazena estado de login
    dcc.Location(id='url', refresh=False),                   # Roteamento de URL
    html.Div(id='page-content')                              # Espaço onde a tela vai desenhar
])

# ─────────────────────────────────────────────────────────────────────────────
# CALLBACKS (LÓGICA)
# ─────────────────────────────────────────────────────────────────────────────

# --- ROTEAMENTO E NAVEGAÇÃO ---
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('sessao-usuario', 'data')
)
def renderizar_pagina(pathname, sessao):
    logado = sessao and sessao.get('autenticado') == True
    
    # Validação de acesso restrito (Dashboard)
    if pathname == '/dashboard':
        if logado:
            return layout_dashboard()
        else:
            # Se tentou acessar painel sem logar, força o login
            return layout_login()
            
    # Páginas abertas
    if pathname == '/registro':
        return layout_registro()
        
    # Padrão: tela de login
    return layout_login()


# --- BOTÕES DE NAVEGAÇÃO E LOGOUT ---
# Centralizamos aqui os redirecionamentos usando pattern matching ou prevent_initial_call
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('btn-ir-registro', 'n_clicks'),
    prevent_initial_call=True
)
def go_to_registro(n):
    if n: return '/registro'
    return dash.no_update

@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('btn-ir-login', 'n_clicks'),
    prevent_initial_call=True
)
def go_to_login(n):
    if n: return '/login'
    return dash.no_update

@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Output('sessao-usuario', 'data', allow_duplicate=True),
    Input('btn-logout', 'n_clicks'),
    prevent_initial_call=True
)
def acao_logout(n):
    if n: 
        return '/login', {'autenticado': False, 'email': None}
    return dash.no_update, dash.no_update


@app.callback(
    Output('msg-registro', 'children'),
    Output('msg-registro', 'className'),
    Input('btn-registrar', 'n_clicks'),
    State('input-email-reg', 'value'),
    State('input-senha-reg', 'value'),
    State('input-senha-conf-reg', 'value'),
    prevent_initial_call=True
)
def processar_registro(n_clicks, email, senha, senha_conf):
    if not email or not senha or not senha_conf:
        return "Preencha todos os campos.", "text-warning mt-3 font-weight-bold"
        
    if senha != senha_conf:
        return "As senhas não coincidem.", "text-danger mt-3 font-weight-bold"
        
    sucesso, mensagem = modulo_auth.registrar_usuario(email, senha)
    
    if sucesso:
        return html.Span([html.I(className="bi bi-check-circle me-2"), mensagem]), "text-success mt-3 font-weight-bold"
    else:
        return html.Span([html.I(className="bi bi-exclamation-triangle me-2"), mensagem]), "text-danger mt-3 font-weight-bold"


@app.callback(
    Output('msg-login', 'children'),
    Output('msg-login', 'className'),
    Output('sessao-usuario', 'data'),
    Output('url', 'pathname', allow_duplicate=True),
    Input('btn-login', 'n_clicks'),
    State('input-email-login', 'value'),
    State('input-senha-login', 'value'),
    prevent_initial_call=True
)
def processar_login(n_clicks, email, senha):
    if not email or not senha:
        return "Digite o e-mail e a senha.", "text-warning mt-3", dash.no_update, dash.no_update
        
    sucesso, mensagem = modulo_auth.verificar_login(email, senha)
    
    if sucesso:
        # Cria a sessão e redireciona para o dashboard
        return "", "", {'autenticado': True, 'email': email}, '/dashboard'
    else:
        return mensagem, "text-danger mt-3 font-weight-bold", dash.no_update, dash.no_update


# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Inicializa os arquivos de pastas garantindo que eles existam antes do app subir
    modulo_auth.init_auth()
    print("🚀 Servidor local Dash iniciado em http://127.0.0.1:8050/")
    app.run(debug=True, port=8050)
