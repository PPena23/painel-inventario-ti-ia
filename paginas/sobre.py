"""Página Sobre: o que o projeto demonstra e com quais tecnologias."""

import streamlit as st

st.title("Sobre o projeto")

st.markdown("""
Painel de inventário de TI feito em **Python + Streamlit** para estudo e portfólio.
Ele é inspirado em um sistema real de inventário que desenvolvi para uma empresa
do agronegócio. **Todos os dados aqui são fictícios**, gerados pelo script
`gerar_dados.py`.
""")

c1, c2 = st.columns(2)
with c1:
    st.subheader("O que ele faz")
    st.markdown("""
- Painel com indicadores, 4 gráficos interativos e tabela filtrável
- Filtros por busca, tipo, setor, status, discos críticos e garantia vencida
- Exportação do resultado filtrado em CSV
- Cadastro de ativos com validação, refletido na hora no painel
- Assistente de IA (Gemini) que responde perguntas sobre o inventário consultando os dados por *function calling*
""")
with c2:
    st.subheader("Conceitos de Streamlit usados")
    st.markdown("""
- App **multipágina** com `st.navigation` e `st.Page`
- **Session State** para guardar cadastros entre reexecuções e páginas
- **Cache** (`st.cache_data`) para ler a base uma vez só
- **Formulários** (`st.form`) com validação no servidor
- `column_config` para barras de progresso, datas e moeda na tabela
- **Tema** em `.streamlit/config.toml` e **CSS** próprio em `estilo/estilo.css`
""")

st.subheader("Stack")
st.markdown("`Python 3.12` · `Streamlit` · `pandas` · `Plotly Express` · `Google Gemini API (google-genai)`")

st.divider()
st.caption("Pedro Pena · linkedin.com/in/pedropena23")
