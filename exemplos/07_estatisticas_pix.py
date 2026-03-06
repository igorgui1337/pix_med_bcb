import json
import os
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta

def fetch_estatisticas_pix(meses_voltar=6):
    """
    Busca os dados de Estatísticas de Transações Pix na API Olinda do BCB.
    Retorna os dados dos últimos 'meses_voltar'.
    """
    base_url = "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/EstatisticasTransacoesPix"
    
    # Achar o mês atual para o loop
    hoje = datetime.now()
    mes_atual = hoje.replace(day=1)
    
    todos_dados = []
    meses_sem_dados = 0
    meses_com_dados = 0
    max_meses_sem_dados = 3 # Se voltar 3 meses seguidos e não achar nada, para.
    
    anomes_inicio = None
    anomes_fim = None
    
    print(f"📥 Iniciando busca das Estatísticas de Transações Pix (últimos {meses_voltar} meses preenchidos)...")
    
    # Vamos voltar no tempo até encontrar a quantidade de meses pedida
    while meses_com_dados < meses_voltar and meses_sem_dados < max_meses_sem_dados:
        # Formato esperado pela API: 'YYYYMM' COM ASPAS SIMPLES
        anomes_str = mes_atual.strftime("%Y%m")
        # Muito importante: as aspas simples e o não-encoding
        url = f"{base_url}(Database=@Database)?@Database='{anomes_str}'&$format=json"
        
        print(f"Buscando {anomes_str}...")
        
        try:
            url_pagina = url
            dados_mes = []
            
            while url_pagina:
                response = requests.get(url_pagina, timeout=30)
                response.raise_for_status()
                json_data = response.json()
                
                pagina_atual = json_data.get('value', [])
                if pagina_atual:
                    dados_mes.extend(pagina_atual)
                    
                # Paginação (se a API devolver mais de 10k registros por requisição)
                if '@odata.nextLink' in json_data:
                    url_pagina = json_data['@odata.nextLink']
                else:
                    url_pagina = None
            
            if dados_mes:
                todos_dados.extend(dados_mes)
                meses_sem_dados = 0
                meses_com_dados += 1
                if anomes_fim == None:
                    anomes_fim = anomes_str
                anomes_inicio = anomes_str
                print(f"   -> {len(dados_mes)} registros baixados para {anomes_str}.")
            else:
                meses_sem_dados += 1
                print(f"   Sem dados para {anomes_str}.")
                
        except Exception as e:
            print(f"❌ Erro ao buscar {anomes_str}: {e}")
            
        # Volta 1 mês
        mes_atual -= relativedelta(months=1)

    if not todos_dados:
        print("⚠️ Nenhum dado encontrado. A API pode estar fora ou formato mudou.")
        return []
        
    print(f"✅ Coleta finalizada! {len(todos_dados)} registros (linhas) extraídos do período {anomes_inicio} a {anomes_fim}.")
    return todos_dados, anomes_inicio, anomes_fim

def salvar_dados(dados, anomes_inicio, anomes_fim):
    """Salva os dados extraídos em um arquivo JSON local na pasta 'dados'."""
    # Define caminhos
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dados_dir = os.path.join(base_dir, "dados")
    
    if not os.path.exists(dados_dir):
        os.makedirs(dados_dir)
        
    nome_arquivo = f"estatisticas_transacoes_{anomes_inicio}_{anomes_fim}.json"
    caminho_arquivo = os.path.join(dados_dir, nome_arquivo)
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
        
    print(f"📁 Arquivo salvo em: {caminho_arquivo}")
    return caminho_arquivo

if __name__ == "__main__":
    print("-" * 50)
    print("EXTRAÇÃO: ESTATÍSTICAS DE TRANSAÇÕES PIX (BCB - Olinda)")
    print("-" * 50)
    
    res = fetch_estatisticas_pix(meses_voltar=6)
    if res:
        dados, inicio, fim = res
        caminho = salvar_dados(dados, inicio, fim)
        
        print(f"\nExemplo do primeiro registro:")
        print(json.dumps(dados[0], indent=2, ensure_ascii=False))
