"""Ponto de entrada do app multipágina.

Rodar:  .venv\\Scripts\\streamlit run app.py
Este arquivo roda em toda interação: configura a página, aplica o CSS,
monta o menu e executa a página escolhida (pasta paginas/).
"""

import streamlit as st

from comum import CAMINHO, RAIZ, iniciar_estado

st.set_page_config(page_title="Inventário de TI", page_icon="🖥️", layout="wide")

# CSS próprio por cima do tema definido em .streamlit/config.toml
st.markdown(f"<style>{(RAIZ / 'estilo' / 'estilo.css').read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)

if not CAMINHO.exists():
    st.warning("Base não encontrada. Rode `python gerar_dados.py` primeiro.")
    st.stop()

iniciar_estado()

pagina = st.navigation([
    st.Page("paginas/painel.py", title="Painel", icon=":material/dashboard:", default=True),
    st.Page("paginas/cadastro.py", title="Cadastrar ativo", icon=":material/add_box:"),
    st.Page("paginas/assistente.py", title="Assistente de IA", icon=":material/smart_toy:"),
    st.Page("paginas/sobre.py", title="Sobre o projeto", icon=":material/info:"),
])

st.logo(str(RAIZ / "estilo" / "logo.svg"), size="large")
pagina.run()
