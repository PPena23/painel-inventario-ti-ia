"""Página Assistente: chat com o Gemini que consulta o inventário por function calling."""

import os

import streamlit as st
from google import genai
from google.genai import errors, types

from ferramentas_ia import FERRAMENTAS

INSTRUCOES = """Você é o assistente do inventário de TI de uma empresa (dados fictícios).
Responda em português do Brasil, de forma curta e objetiva.
Para qualquer número, contagem, valor ou lista de ativos, SEMPRE use as ferramentas
buscar_ativos ou resumo_por. Nunca invente ou estime dados.
Valores em reais no formato R$ 1.234,56. Quando listar ativos, cite o código (TI-000123).
Se a pergunta não for sobre o inventário de TI, diga educadamente que só ajuda com isso."""

SUGESTOES = [
    "Quantos notebooks têm mais de 5 anos?",
    "Quais computadores estão com o disco abaixo de 50%?",
    "Qual setor tem o parque de maior valor?",
    "Quantos ativos estão com a garantia vencida, por tipo?",
]


def ler_chave() -> str | None:
    """Procura a chave em .streamlit/secrets.toml e depois na variável de ambiente."""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:  # não existe secrets.toml
        pass
    return os.environ.get("GEMINI_API_KEY")


@st.cache_resource  # um cliente por chave, reaproveitado entre execuções
def cliente(chave: str) -> genai.Client:
    return genai.Client(api_key=chave)


@st.cache_data(ttl=3600, show_spinner=False)
def modelos_flash(chave: str) -> list[str]:
    """Pergunta à API quais modelos "flash" a chave pode usar. Assim o app não
    quebra quando o Google lança ou aposenta uma versão."""
    nomes = [m.name.removeprefix("models/") for m in cliente(chave).models.list()
             if "generateContent" in (m.supported_actions or []) and "flash" in m.name
             and not any(x in m.name for x in ("image", "tts", "audio", "live"))]
    # Flash-Lite primeiro: no plano gratuito ele permite bem mais pedidos por dia
    return sorted(nomes, key=lambda n: ("lite" not in n, n))


st.title("Assistente de IA")
st.caption("Pergunte sobre o inventário em linguagem natural. A IA consulta os dados "
           "com funções Python e só depois responde.")

chave = ler_chave()
if not chave:
    st.warning("Falta configurar a chave da API do Gemini.")
    st.markdown("""
1. Gere uma chave gratuita em **aistudio.google.com** → *Get API key*.
2. Crie o arquivo `.streamlit/secrets.toml` na pasta do projeto com a linha:
   ```toml
   GEMINI_API_KEY = "cole-sua-chave-aqui"
   ```
3. Recarregue esta página.
""")
    st.stop()

try:
    modelos = modelos_flash(chave)
except errors.APIError as e:
    st.error(f"Não consegui falar com a API do Gemini. Confira a chave. ({e.code})")
    st.stop()

with st.sidebar:
    st.header("Assistente")
    modelo = st.selectbox("Modelo", modelos, help="Flash-Lite gasta menos da cota gratuita.")
    if st.button("Nova conversa"):
        st.session_state.mensagens_ia = []
        st.session_state.pop("chat_ia", None)
        st.rerun()

# um objeto de chat guarda o histórico da conversa com o modelo;
# troca de modelo = conversa nova
if st.session_state.get("modelo_ia") != modelo:
    st.session_state.modelo_ia = modelo
    st.session_state.chat_ia = cliente(chave).chats.create(
        model=modelo,
        config=types.GenerateContentConfig(system_instruction=INSTRUCOES, tools=FERRAMENTAS),
    )
    st.session_state.mensagens_ia = []

for msg in st.session_state.mensagens_ia:
    with st.chat_message(msg["papel"]):
        st.markdown(msg["texto"])
        if msg.get("chamadas"):
            with st.expander("Consultas feitas"):
                st.code("\n".join(msg["chamadas"]), language="python")

pergunta = st.chat_input("Ex.: quantos monitores estão em estoque?")
if not st.session_state.mensagens_ia and not pergunta:
    st.markdown("**Sugestões:**")
    colunas = st.columns(2)
    for i, sugestao in enumerate(SUGESTOES):
        if colunas[i % 2].button(sugestao, width="stretch"):
            pergunta = sugestao

if pergunta:
    st.session_state.mensagens_ia.append({"papel": "user", "texto": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    st.session_state.chamadas_ia = []
    with st.chat_message("assistant"):
        try:
            with st.spinner("Consultando o inventário..."):
                resposta = st.session_state.chat_ia.send_message(pergunta).text
        except errors.APIError as e:
            resposta = ("⏳ A cota gratuita do Gemini acabou por agora. Tente de novo mais tarde "
                        "ou troque de modelo na barra lateral." if e.code == 429
                        else f"Erro ao consultar o Gemini ({e.code}): {e.message}")
        st.markdown(resposta or "Não consegui gerar uma resposta. Tente reformular a pergunta.")

    st.session_state.mensagens_ia.append({"papel": "assistant", "texto": resposta,
                                          "chamadas": st.session_state.chamadas_ia})
    st.rerun()
