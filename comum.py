"""Constantes e funções usadas por mais de uma página do app."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).parent
CAMINHO = RAIZ / "dados" / "ativos.csv"
HOJE = pd.Timestamp(date.today())
DISCO_CRITICO = 60  # % de saúde abaixo da qual o disco merece troca

# mesma cor para o mesmo status em todos os gráficos
CORES_STATUS = {"Em uso": "#34A36B", "Estoque": "#4FA3E0",
                "Manutenção": "#E0A030", "Descartado": "#8A94A6"}
CORES_TIPO = {"Notebook": "#4FA3E0", "Desktop": "#F28E2B", "Servidor": "#B07AA1"}

SISTEMAS_POR_TIPO = {
    "Notebook": ["Windows 11 Pro", "Windows 10 Pro", "Linux"],
    "Desktop": ["Windows 11 Pro", "Windows 10 Pro", "Linux"],
    "Servidor": ["Ubuntu Server 24.04", "Windows Server 2022"],
    "Celular": ["Android", "iOS"],
}
COMPUTADORES = {"Notebook", "Desktop", "Servidor"}
SEM_RESPONSAVEL = {"Switch", "Servidor", "Impressora"}  # equipamentos de infraestrutura


def iniciar_estado() -> None:
    """st.session_state é um dicionário de cada visitante que sobrevive às
    reexecuções do script e à troca de página."""
    st.session_state.setdefault("novos", [])       # ativos cadastrados nesta sessão
    st.session_state.setdefault("form_id", 0)      # trocar o id limpa o formulário
    st.session_state.setdefault("mensagem", None)  # aviso exibido após o cadastro


@st.cache_data  # lê o CSV uma vez só e reaproveita nas próximas execuções
def carregar_base() -> pd.DataFrame:
    return pd.read_csv(CAMINHO, parse_dates=["data_aquisicao", "garantia_ate"])


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["idade_anos"] = ((HOJE - df["data_aquisicao"]).dt.days / 365).round(1)
    df["garantia_vencida"] = df["garantia_ate"] < HOJE
    df["responsavel"] = df["responsavel"].fillna("—")
    return df


def ativos() -> pd.DataFrame:
    """Base do CSV + o que foi cadastrado nesta sessão, já com colunas calculadas."""
    base = carregar_base()
    novos = pd.DataFrame(st.session_state.novos)
    return preparar(pd.concat([base, novos], ignore_index=True) if not novos.empty else base)


def moeda(valor: float) -> str:
    return f"R$ {valor:,.0f}".replace(",", ".")


def proximo_codigo(df: pd.DataFrame) -> str:
    ultimo = df["codigo"].str.removeprefix("TI-").astype(int).max()
    return f"TI-{ultimo + 1:06d}"
