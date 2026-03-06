"""
bcb_client.py
=============
Cliente Python para a API CKAN do Banco Central do Brasil (BCB).
URL Base: https://dadosabertos.bcb.gov.br/api/3

Principais funcionalidades:
    - Listar packages (datasets)
    - Buscar packages por palavra-chave
    - Obter detalhes de um package específico
    - Buscar grupos disponíveis
    - Baixar recursos (CSV, JSON, etc.)
"""

import requests
import json
from typing import Optional


BASE_URL = "https://dadosabertos.bcb.gov.br/api/3/action"


def _get(endpoint: str, params: Optional[dict] = None) -> dict:
    """
    Realiza uma requisição GET na API CKAN do BCB.

    Args:
        endpoint: Nome da action CKAN (ex: 'package_list')
        params:   Parâmetros de query opcionais

    Returns:
        Dicionário com a resposta da API
    """
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise ValueError(f"API retornou erro: {data.get('error', {})}")
        return data
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Timeout ao acessar {url}")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Erro de conexão: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# DATASETS (Packages)
# ─────────────────────────────────────────────────────────────────────────────

def listar_datasets(limite: int = 100, offset: int = 0) -> list:
    """
    Retorna uma lista com os IDs/nomes de todos os datasets disponíveis.

    Args:
        limite:  Número máximo de resultados por página (padrão: 100)
        offset:  Deslocamento para paginação (padrão: 0)

    Returns:
        Lista de strings com os nomes dos datasets
    """
    data = _get("package_list", params={"limit": limite, "offset": offset})
    return data["result"]


def buscar_datasets(query: str, linhas: int = 10) -> list:
    """
    Busca datasets pelo texto, retornando os mais relevantes.

    Args:
        query:  Termo de busca (ex: 'selic', 'ipca', 'cambio')
        linhas: Número máximo de resultados (padrão: 10)

    Returns:
        Lista de dicionários com informações dos datasets encontrados
    """
    data = _get("package_search", params={"q": query, "rows": linhas})
    return data["result"]["results"]


def obter_dataset(nome_ou_id: str) -> dict:
    """
    Retorna os detalhes completos de um dataset específico,
    incluindo seus recursos (arquivos para download).

    Args:
        nome_ou_id: Nome ou ID do dataset (ex: '11-taxa-de-juros---selic')

    Returns:
        Dicionário com metadados e recursos do dataset
    """
    data = _get("package_show", params={"id": nome_ou_id})
    return data["result"]


# ─────────────────────────────────────────────────────────────────────────────
# GRUPOS
# ─────────────────────────────────────────────────────────────────────────────

def listar_grupos() -> list:
    """
    Retorna todos os grupos de datasets disponíveis no portal do BCB.

    Returns:
        Lista de strings com os nomes dos grupos
    """
    data = _get("group_list", params={"all_fields": False})
    return data["result"]


def obter_grupo(nome_grupo: str) -> dict:
    """
    Retorna os detalhes de um grupo específico.

    Args:
        nome_grupo: Nome do grupo

    Returns:
        Dicionário com metadados do grupo
    """
    data = _get("group_show", params={"id": nome_grupo})
    return data["result"]


# ─────────────────────────────────────────────────────────────────────────────
# RECURSOS
# ─────────────────────────────────────────────────────────────────────────────

def obter_recurso(resource_id: str) -> dict:
    """
    Retorna os detalhes de um recurso específico (arquivo de um dataset).

    Args:
        resource_id: ID do recurso

    Returns:
        Dicionário com metadados do recurso
    """
    data = _get("resource_show", params={"id": resource_id})
    return data["result"]


def baixar_recurso_csv(url_recurso: str) -> str:
    """
    Baixa o conteúdo de um recurso CSV diretamente pela URL.

    Args:
        url_recurso: URL de download do recurso

    Returns:
        Conteúdo do arquivo como string
    """
    try:
        response = requests.get(url_recurso, timeout=60)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Erro ao baixar recurso: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────────────────────────────────────────

def listar_recursos_de_dataset(nome_ou_id: str) -> list:
    """
    Retorna apenas os recursos (arquivos) de um dataset,
    com nome, formato e URL de download.

    Args:
        nome_ou_id: Nome ou ID do dataset

    Returns:
        Lista de dicionários com info dos recursos
    """
    dataset = obter_dataset(nome_ou_id)
    recursos = []
    for r in dataset.get("resources", []):
        recursos.append({
            "id":       r.get("id"),
            "nome":     r.get("name"),
            "formato":  r.get("format"),
            "url":      r.get("url"),
            "descricao": r.get("description"),
        })
    return recursos


if __name__ == "__main__":
    print("Testando cliente da API BCB...")
    datasets = listar_datasets(limite=5)
    print(f"\nPrimeiros 5 datasets: {datasets}")
