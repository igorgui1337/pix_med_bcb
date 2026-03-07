import os
import json
import pandas as pd
import requests
import glob
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ─────────────────────────────────────────────────────────────────────────────
# 1. EXTRAÇÃO DE DADOS (API OLINDA - BCB)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_pix_municipio(meses_voltar=6):
    """
    Extrai dados do endpoint TransacoesPixPorMunicipio da API Olinda do BCB.
    """
    # A API Olinda é case-sensitive: DataBase (com B maiúsculo)
    base_url = "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/TransacoesPixPorMunicipio"
    hoje = datetime.now()
    mes_atual = hoje.replace(day=1)
    
    todos_dados = []
    meses_com_dados = 0
    meses_tentados = 0
    max_tentativas = 10 # Aumentado para garantir encontrar 6 meses

    print(f"📥 Iniciando extração de Transações Pix por Município (últimos {meses_voltar} meses)...")

    while meses_com_dados < meses_voltar and meses_tentados < max_tentativas:
        anomes_str = mes_atual.strftime("%Y%m")
        # Sintaxe exata descoberta via Swagger: DataBase=@DataBase
        url = f"{base_url}(DataBase=@DataBase)?@DataBase='{anomes_str}'&$format=json"
        
        print(f"Buscando {anomes_str}...")
        try:
            url_pagina = url
            dados_mes = []
            while url_pagina:
                response = requests.get(url_pagina, timeout=60)
                response.raise_for_status()
                json_data = response.json()
                pagina_atual = json_data.get('value', [])
                if pagina_atual:
                    dados_mes.extend(pagina_atual)
                
                # Paginação via nextLink
                url_pagina = json_data.get('@odata.nextLink')
            
            if dados_mes:
                todos_dados.extend(dados_mes)
                meses_com_dados += 1
                print(f"   -> {len(dados_mes)} registros encontrados.")
            else:
                print(f"   ⚠️ Sem dados para {anomes_str}.")
        except Exception as e:
            print(f"   ❌ Erro em {anomes_str}: {e}")
        
        mes_atual -= relativedelta(months=1)
        meses_tentados += 1

    if not todos_dados:
        return pd.DataFrame()

    df_raw = pd.DataFrame(todos_dados)
    
    # Processamento de Valores (Soma dos fluxos para ter o Volume Total)
    cols_valor = ['VL_PagadorPF', 'VL_PagadorPJ', 'VL_RecebedorPF', 'VL_RecebedorPJ']
    for c in cols_valor:
        df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)
    
    df_raw['VALOR_TOTAL'] = df_raw[cols_valor].sum(axis=1)
    
    # Processamento de Quantidades
    cols_qtd = ['QT_PagadorPF', 'QT_PagadorPJ', 'QT_RecebedorPF', 'QT_RecebedorPJ']
    for c in cols_qtd:
        df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)
    
    df_raw['QT_TOTAL'] = df_raw[cols_qtd].sum(axis=1)
    
    # Salvar para cache local
    os.makedirs("dados", exist_ok=True)
    df_raw.to_json("dados/pix_regional_cache.json", orient="records", indent=4)
    return df_raw

def load_data():
    """Carrega dados do cache ou baixa se não existirem."""
    cache_path = "dados/pix_regional_cache.json"
    if os.path.exists(cache_path):
        print("📁 Carregando dados do cache local...")
        try:
            return pd.read_json(cache_path)
        except:
            return fetch_pix_municipio()
    return fetch_pix_municipio()

# ─────────────────────────────────────────────────────────────────────────────
# 2. PREPARAÇÃO DOS DADOS
# ─────────────────────────────────────────────────────────────────────────────
df = load_data()

if df.empty:
    print("⚠️ Nenhum dado disponível para o Dashboard.")
    df_estado = pd.DataFrame(columns=['Estado', 'VALOR_TOTAL', 'QT_TOTAL'])
else:
    # Agrupamento por Estado (UF) para o mapa
    df_estado = df.groupby('Estado', as_index=False)[['VALOR_TOTAL', 'QT_TOTAL']].sum()
    
# GeoJSON dos Estados do Brasil (IBGE oficial via raw github)
GEOJSON_BR_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

print("🗺️ Carregando GeoJSON do Brasil...")
try:
    geojson_data = requests.get(GEOJSON_BR_URL, timeout=30).json()
except Exception as e:
    print(f"⚠️ Erro ao carregar GeoJSON: {e}")
    geojson_data = None

# Figura do Mapa Inicial (Gerada apenas uma vez para performance)
def get_mapa_fig():
    fig = px.choropleth_mapbox(
        df_estado if not df_estado.empty else pd.DataFrame(columns=["Estado", "VALOR_TOTAL"]),
        geojson=geojson_data,
        locations="Estado",
        featureidkey="properties.sigla",
        color="VALOR_TOTAL",
        color_continuous_scale="Viridis",
        mapbox_style="carto-darkmatter",
        zoom=3.5,
        center={"lat": -15.78, "lon": -47.93},
        opacity=0.7,
        labels={"VALOR_TOTAL": "Volume Total (R$)"}
    )
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        coloraxis_colorbar={"title": "R$"},
        uirevision='constant' # Mantém o zoom ao trocar de estado
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# 3. INTERFACE DASH (UI)
# ─────────────────────────────────────────────────────────────────────────────
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2([html.I(className="fa-solid fa-map-location-dot me-3"), "Monitoramento Regional Pix"], className="text-center my-4 text-info")
        ], width=12)
    ]),
    
    dbc.Row([
        # Lado Esquerdo: MAPA
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Volume Total por Estado (Heatmap)"),
                dbc.CardBody([
                    dcc.Graph(
                        id="mapa-brasil",
                        figure=get_mapa_fig(),
                        style={"height": "75vh"},
                        config={"displayModeBar": False}
                    )
                ])
            ], className="shadow border-0 h-100")
        ], width=6),
        
        # Lado Direito: GRID POR MUNICÍPIO
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(id="titulo-detalhe", children="Selecione um estado no mapa"),
                dbc.CardBody([
                    dcc.Graph(
                        id="grafico-municipios",
                        style={"height": "75vh"},
                        config={"displayModeBar": False}
                    )
                ])
            ], className="shadow border-0 h-100")
        ], width=6)
    ])
], fluid=True, className="py-3")

# ─────────────────────────────────────────────────────────────────────────────
# 4. CALLBACKS INTERATIVOS
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    [Output("grafico-municipios", "figure"),
     Output("titulo-detalhe", "children")],
    [Input("mapa-brasil", "clickData")]
)
def update_municipios(click_data):
    if df.empty:
        return px.bar(title="Sem dados"), "Aguardando dados..."

    uf_sigla = "SP" # Default inicial
    if click_data:
        try:
            uf_sigla = click_data["points"][0]["location"]
        except:
            pass

    # Filtração ultra rápida apenas dos municípios do estado
    df_filt = df[df["Estado"] == uf_sigla].groupby('Municipio', as_index=False)['VALOR_TOTAL'].sum()
    df_filt = df_filt.sort_values(by="VALOR_TOTAL", ascending=False).head(20)
    
    fig_bar = px.bar(
        df_filt,
        x="VALOR_TOTAL",
        y="Municipio",
        orientation="h",
        title=f"Top 20 Municípios - {uf_sigla}",
        color="VALOR_TOTAL",
        color_continuous_scale="Blues",
        labels={"VALOR_TOTAL": "Volume (R$)", "Municipio": ""}
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        yaxis={"categoryorder":"total ascending"},
        margin={"t":40, "b":20, "l":120, "r":20}
    )

    return fig_bar, f"Detalhamento: {uf_sigla}"

if __name__ == "__main__":
    app.run(debug=True, port=8051)
