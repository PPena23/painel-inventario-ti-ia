"""Ferramentas que o assistente de IA pode chamar para consultar o inventário.

Em vez de mandar a planilha inteira para o modelo e torcer para ele somar
certo, damos a ele funções Python. O Gemini decide qual chamar e com quais
filtros; o pandas faz a conta exata e o modelo só redige a resposta.
(Isso se chama "function calling".)

O SDK lê o nome, os tipos e a docstring de cada função para explicar a
ferramenta ao modelo, por isso as docstrings estão bem detalhadas.
"""

import json
from typing import Optional

import pandas as pd
import streamlit as st

from comum import ativos

CAMPOS_AGRUPAVEIS = ["tipo", "setor", "status", "marca", "sistema", "modelo"]


def _registrar(nome: str, argumentos: dict) -> None:
    """Guarda as chamadas feitas para mostrar ao usuário de onde veio a resposta."""
    usados = {k: v for k, v in argumentos.items() if v is not None}
    st.session_state.setdefault("chamadas_ia", []).append(f"{nome}({usados})")


def _registros(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> lista de dicionários só com tipos nativos (NaN vira None),
    que é o formato que o SDK consegue enviar ao modelo."""
    return json.loads(df.to_json(orient="records", force_ascii=False))


def _filtrar(tipo, setor, status, idade_minima_anos, saude_disco_maxima,
             garantia_vencida) -> pd.DataFrame:
    df = ativos()
    if tipo:
        df = df[df["tipo"].str.lower() == tipo.lower()]
    if setor:
        df = df[df["setor"].str.lower() == setor.lower()]
    if status:
        df = df[df["status"].str.lower() == status.lower()]
    if idade_minima_anos is not None:
        df = df[df["idade_anos"] >= idade_minima_anos]
    if saude_disco_maxima is not None:
        df = df[df["saude_disco_pct"] <= saude_disco_maxima]
    if garantia_vencida is not None:
        df = df[df["garantia_vencida"] == garantia_vencida]
    return df


def buscar_ativos(
    tipo: Optional[str] = None,
    setor: Optional[str] = None,
    status: Optional[str] = None,
    idade_minima_anos: Optional[float] = None,
    saude_disco_maxima: Optional[int] = None,
    garantia_vencida: Optional[bool] = None,
    limite: int = 10,
) -> dict:
    """Conta e lista ativos de TI do inventário que atendem a todos os filtros informados.

    Args:
        tipo: Notebook, Desktop, Monitor, Celular, Impressora, Switch ou Servidor.
        setor: Administrativo, Financeiro, Comercial, Logística, Produção, Qualidade, RH, TI ou Diretoria.
        status: Em uso, Estoque, Manutenção ou Descartado.
        idade_minima_anos: só ativos com pelo menos essa idade, em anos.
        saude_disco_maxima: só computadores com saúde do disco menor ou igual a esse percentual (0 a 100).
        garantia_vencida: true para só garantia vencida, false para só garantia em dia.
        limite: quantos ativos de exemplo devolver na lista (máximo 50).

    Returns:
        quantidade total, valor total em reais e uma lista de exemplos com os campos principais.
    """
    _registrar("buscar_ativos", locals())
    df = _filtrar(tipo, setor, status, idade_minima_anos, saude_disco_maxima, garantia_vencida)
    colunas = ["codigo", "tipo", "modelo", "setor", "responsavel", "status",
               "idade_anos", "saude_disco_pct", "garantia_ate", "valor_rs"]
    exemplos = df.sort_values("idade_anos", ascending=False).head(min(limite, 50))[colunas]
    exemplos = exemplos.assign(garantia_ate=exemplos["garantia_ate"].dt.strftime("%d/%m/%Y"))
    return {
        "quantidade": int(len(df)),
        "valor_total_rs": round(float(df["valor_rs"].sum()), 2),
        "exemplos_mais_antigos_primeiro": _registros(exemplos),
    }


def resumo_por(
    campo: str,
    tipo: Optional[str] = None,
    setor: Optional[str] = None,
    status: Optional[str] = None,
    idade_minima_anos: Optional[float] = None,
    saude_disco_maxima: Optional[int] = None,
    garantia_vencida: Optional[bool] = None,
) -> dict:
    """Agrupa os ativos filtrados por um campo e devolve quantidade e valor de cada grupo.

    Use para perguntas como "quantos ativos por setor" ou "qual setor tem mais notebooks".

    Args:
        campo: tipo, setor, status, marca, sistema ou modelo.
        tipo: filtro opcional, mesmos valores de buscar_ativos.
        setor: filtro opcional, mesmos valores de buscar_ativos.
        status: filtro opcional, mesmos valores de buscar_ativos.
        idade_minima_anos: filtro opcional, idade mínima em anos.
        saude_disco_maxima: filtro opcional, saúde do disco máxima em %.
        garantia_vencida: filtro opcional, true ou false.

    Returns:
        lista de grupos ordenada da maior para a menor quantidade.
    """
    _registrar("resumo_por", locals())
    if campo not in CAMPOS_AGRUPAVEIS:
        return {"erro": f"Campo inválido. Use um destes: {', '.join(CAMPOS_AGRUPAVEIS)}."}
    df = _filtrar(tipo, setor, status, idade_minima_anos, saude_disco_maxima, garantia_vencida)
    grupos = (df.groupby(campo).agg(quantidade=("codigo", "count"), valor_total_rs=("valor_rs", "sum"))
              .sort_values("quantidade", ascending=False).reset_index())
    grupos["valor_total_rs"] = grupos["valor_total_rs"].round(2)
    return {"total": int(len(df)), "grupos": _registros(grupos)}


FERRAMENTAS = [buscar_ativos, resumo_por]
