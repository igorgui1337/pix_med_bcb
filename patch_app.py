import re

with open('app_streamlit.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Aba 1
content = re.sub(
    r'def aba_visao_geral\(df, periodo_key\):.*?def aba_contestacoes',
    '''def aba_visao_geral(df, periodo_key):
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
def aba_contestacoes''',
    content,
    flags=re.DOTALL
)

# Replace Aba 2
content = re.sub(
    r'def aba_contestacoes\(df, periodo_key\):.*?def aba_estatisticas',
    '''def aba_contestacoes(df_med, periodo_key):
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
def aba_estatisticas''',
    content,
    flags=re.DOTALL
)

# Replace Aba 3
content = re.sub(
    r'def aba_estatisticas\(df_t, sel_pfpj, sel_reg\):.*?def _load_geojson',
    '''def aba_estatisticas(df_sistemico, sel_pfpj, sel_reg):
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
def _load_geojson''',
    content,
    flags=re.DOTALL
)

# For Aba 4 we replace it up to def dashboard
content = re.sub(
    r'def aba_municipios\(sel_uf, sel_metrica, sel_fluxo\):.*?def dashboard\(\):',
    '''def aba_municipios(sel_uf, sel_metrica, sel_fluxo):
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
# DASHBOARD PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def dashboard():''',
    content,
    flags=re.DOTALL
)

with open('app_streamlit.py', 'w', encoding='utf-8') as f:
    f.write(content)
