import re

with open('app_streamlit.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import
if 'from prophet import Prophet' not in content:
    content = content.replace('import plotly.graph_objects as go\n', 'import plotly.graph_objects as go\nfrom prophet import Prophet\n')

# 2. Add forecasting tab logic just before def dashboard()
preditiva_code = """
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
        m.fit(df_prophet[['ds', 'y']])
        
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
"""

content = content.replace('# ─────────────────────────────────────────────────────────────────────────────\n# DASHBOARD PRINCIPAL\n', preditiva_code)

# 3. Add to tabs
content = content.replace(
    'tab1, tab2, tab3, tab4 = st.tabs([\n        "📊 Visão Geral",\n        "🔄 Contestações vs Devoluções",\n        "📈 Estatísticas Sistêmicas PIX",\n        "🗺️ Transações por Município",\n    ])',
    'tab1, tab2, tab3, tab4, tab5 = st.tabs([\n        "📊 Visão Geral",\n        "🔄 Contestações vs Devoluções",\n        "📈 Estatísticas Sistêmicas PIX",\n        "🗺️ Transações por Município",\n        "🔮 Projeções & Preditiva",\n    ])'
)

# 4. Add the with tab5: block
with_tab5 = """    with tab4:
        aba_municipios(sel_uf, sel_metrica, sel_fluxo)

    with tab5:
        aba_preditiva(df_fraudes)
"""
content = re.sub(r'\s+with tab4:\s+aba_municipios\(sel_uf, sel_metrica, sel_fluxo\)\n', "\n" + with_tab5, content)

with open('app_streamlit.py', 'w', encoding='utf-8') as f:
    f.write(content)
