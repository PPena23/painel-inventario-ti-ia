"""Página Painel: KPIs, filtros, gráficos (Plotly) e tabela."""

import pandas as pd
import plotly.express as px
import streamlit as st

from comum import CORES_STATUS, CORES_TIPO, DISCO_CRITICO, ativos, moeda

df = ativos()

# ---------------------------------------------------------------- filtros
with st.sidebar:
    st.header("Filtros")
    busca = st.text_input("Buscar", placeholder="Código, modelo ou responsável")
    tipos = st.multiselect("Tipo", sorted(df["tipo"].unique()), placeholder="Todos")
    setores = st.multiselect("Setor", sorted(df["setor"].unique()), placeholder="Todos")
    status = st.multiselect("Status", sorted(df["status"].unique()),
                            default=["Em uso", "Estoque", "Manutenção"], placeholder="Todos")
    so_criticos = st.toggle(f"Só discos com saúde < {DISCO_CRITICO}%")
    so_sem_garantia = st.toggle("Só garantia vencida")

# filtro vazio = sem restrição; cada filtro preenchido estreita a máscara
filtro = pd.Series(True, index=df.index)
if busca:
    alvo = df["codigo"] + " " + df["modelo"] + " " + df["responsavel"]
    filtro &= alvo.str.contains(busca, case=False, regex=False)
if tipos:
    filtro &= df["tipo"].isin(tipos)
if setores:
    filtro &= df["setor"].isin(setores)
if status:
    filtro &= df["status"].isin(status)
if so_criticos:
    filtro &= df["saude_disco_pct"] < DISCO_CRITICO
if so_sem_garantia:
    filtro &= df["garantia_vencida"]

filtrado = df[filtro]

st.title("Painel de Inventário de TI")
st.caption("Visão geral do parque de equipamentos · dados fictícios")

if filtrado.empty:
    st.info("Nenhum ativo encontrado com esses filtros.")
    st.stop()

# ------------------------------------------------------------------- KPIs
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Ativos", len(filtrado), help=f"{len(df)} ativos na base inteira.")
c2.metric("Em uso", int((filtrado["status"] == "Em uso").sum()))
c3.metric("Valor do parque", moeda(filtrado["valor_rs"].sum()))
c4.metric("Garantia vencida", int(filtrado["garantia_vencida"].sum()),
          help="Ativos cuja data de garantia já passou.")
c5.metric("Discos críticos", int((filtrado["saude_disco_pct"] < DISCO_CRITICO).sum()),
          help=f"Computadores com saúde do disco abaixo de {DISCO_CRITICO}%.")

# ---------------------------------------------------------------- gráficos
st.subheader("Visão geral")
g1, g2 = st.columns(2)

with g1:
    por_tipo = filtrado.groupby(["tipo", "status"], as_index=False).size()
    fig = px.bar(por_tipo, x="size", y="tipo", color="status", orientation="h",
                 color_discrete_map=CORES_STATUS, title="Ativos por tipo e status",
                 labels={"size": "Quantidade", "tipo": "", "status": "Status"})
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")

with g2:
    por_setor = (filtrado.groupby("setor", as_index=False)["valor_rs"].sum()
                 .sort_values("valor_rs"))
    fig = px.bar(por_setor, x="valor_rs", y="setor", orientation="h",
                 title="Valor do parque por setor",
                 labels={"valor_rs": "Valor (R$)", "setor": ""})
    fig.update_traces(marker_color="#4FA3E0", hovertemplate="%{y}: R$ %{x:,.0f}<extra></extra>")
    st.plotly_chart(fig, width="stretch")

g3, g4 = st.columns(2)

with g3:
    computadores = filtrado.dropna(subset=["saude_disco_pct"])
    if computadores.empty:
        st.info("Nenhum computador nos filtros atuais para analisar os discos.")
    else:
        fig = px.scatter(computadores, x="idade_anos", y="saude_disco_pct", color="tipo",
                         hover_data=["codigo", "modelo", "responsavel"],
                         color_discrete_map=CORES_TIPO,
                         title="Saúde do disco × idade do computador",
                         labels={"idade_anos": "Idade (anos)",
                                 "saude_disco_pct": "Saúde do disco (%)", "tipo": "Tipo"})
        fig.add_hline(y=DISCO_CRITICO, line_dash="dash", line_color="#E5646B",
                      annotation_text="limite crítico", annotation_position="bottom right")
        st.plotly_chart(fig, width="stretch")

with g4:
    por_ano = (filtrado.assign(ano=filtrado["data_aquisicao"].dt.year)
               .groupby("ano", as_index=False)["valor_rs"].sum())
    fig = px.bar(por_ano, x="ano", y="valor_rs", title="Investimento por ano de aquisição",
                 labels={"ano": "Ano", "valor_rs": "Valor (R$)"})
    fig.update_traces(marker_color="#34A36B", hovertemplate="%{x}: R$ %{y:,.0f}<extra></extra>")
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, width="stretch")

# ------------------------------------------------------------------ tabela
st.subheader(f"Ativos ({len(filtrado)})")
colunas = ["codigo", "tipo", "marca", "modelo", "setor", "responsavel", "status",
           "sistema", "saude_disco_pct", "idade_anos", "garantia_ate", "valor_rs"]
st.dataframe(
    filtrado[colunas],
    width="stretch",
    hide_index=True,
    column_config={
        "codigo": "Código",
        "tipo": "Tipo",
        "marca": "Marca",
        "modelo": "Modelo",
        "setor": "Setor",
        "responsavel": "Responsável",
        "status": "Status",
        "sistema": "Sistema",
        "saude_disco_pct": st.column_config.ProgressColumn(
            "Saúde do disco", format="%d%%", min_value=0, max_value=100),
        "idade_anos": st.column_config.NumberColumn("Idade (anos)", format="%.1f"),
        "garantia_ate": st.column_config.DateColumn("Garantia até", format="DD/MM/YYYY"),
        "valor_rs": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
    },
)

st.download_button(
    "⬇️ Baixar CSV filtrado",
    filtrado[colunas].to_csv(index=False).encode("utf-8-sig"),  # BOM: Excel abre acentos certo
    file_name="ativos_filtrados.csv",
    mime="text/csv",
)
