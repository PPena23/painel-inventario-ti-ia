"""Página Cadastro: formulário com validação; os ativos ficam em st.session_state."""

import pandas as pd
import streamlit as st

from comum import (COMPUTADORES, CORES_STATUS, HOJE, SEM_RESPONSAVEL, SISTEMAS_POR_TIPO,
                   ativos, carregar_base, proximo_codigo)


def validar(dados: dict) -> list[str]:
    """Devolve a lista de erros; lista vazia significa cadastro válido."""
    erros = []
    if len(dados["marca"]) < 2:
        erros.append("Informe a marca.")
    if len(dados["modelo"]) < 2:
        erros.append("Informe o modelo.")
    if (dados["status"] == "Em uso" and dados["tipo"] not in SEM_RESPONSAVEL
            and not dados["responsavel"]):
        erros.append("Ativo em uso precisa de um responsável.")
    if dados["responsavel"] and len(dados["responsavel"].split()) < 2:
        erros.append("Informe nome e sobrenome do responsável.")
    if dados["data_aquisicao"] > HOJE:
        erros.append("A data de aquisição não pode estar no futuro.")
    if dados["garantia_ate"] < dados["data_aquisicao"]:
        erros.append("A garantia não pode terminar antes da aquisição.")
    if dados["valor_rs"] <= 0:
        erros.append("O valor precisa ser maior que zero.")
    return erros


df = ativos()
base = carregar_base()

st.title("Cadastrar ativo")
st.caption("Os cadastros ficam só na sua sessão (é uma demonstração pública) "
           "e aparecem na hora no painel, nos filtros e nos gráficos.")

if st.session_state.mensagem:
    st.success(st.session_state.mensagem)
    st.session_state.mensagem = None

# o tipo fica fora do formulário porque muda os campos exibidos abaixo;
# dentro de um st.form nada reage até clicar em "Cadastrar"
opcoes_tipo = sorted(set(base["tipo"]))
tipo = st.selectbox("Tipo de equipamento", opcoes_tipo, index=opcoes_tipo.index("Notebook"),
                    key=f"tipo_{st.session_state.form_id}")
computador = tipo in COMPUTADORES

with st.form(f"cadastro_{st.session_state.form_id}"):
    st.markdown(f"**Código que será gerado:** `{proximo_codigo(df)}`")
    c1, c2 = st.columns(2)
    marca = c1.text_input("Marca *")
    modelo = c2.text_input("Modelo *")
    setor = c1.selectbox("Setor *", sorted(base["setor"].unique()))
    status = c2.selectbox("Status *", list(CORES_STATUS))
    responsavel = st.text_input(
        "Responsável" + ("" if tipo in SEM_RESPONSAVEL else " (obrigatório se estiver em uso)"),
        placeholder="Nome e sobrenome")
    sistema = st.selectbox("Sistema", SISTEMAS_POR_TIPO.get(tipo, ["—"]))

    if computador:
        c3, c4 = st.columns(2)
        ram = c3.selectbox("Memória RAM (GB)", [4, 8, 16, 32, 64], index=2)
        saude = c4.slider("Saúde do disco (%)", 0, 100, 100)
    else:
        ram, saude = None, None

    c5, c6, c7 = st.columns(3)
    aquisicao = c5.date_input("Data de aquisição *", value=HOJE.date(), format="DD/MM/YYYY")
    garantia = c6.date_input("Garantia até *", value=(HOJE + pd.DateOffset(years=1)).date(),
                             format="DD/MM/YYYY")
    valor = c7.number_input("Valor (R$) *", min_value=0.0, step=100.0, format="%.2f")

    enviado = st.form_submit_button("Cadastrar", type="primary")

if enviado:
    dados = {
        "codigo": proximo_codigo(df),
        "tipo": tipo,
        "marca": marca.strip(),
        "modelo": modelo.strip(),
        "setor": "TI" if tipo in {"Switch", "Servidor"} else setor,
        "responsavel": responsavel.strip(),
        "status": status,
        "sistema": sistema,
        "ram_gb": ram,
        "saude_disco_pct": saude,
        "data_aquisicao": pd.Timestamp(aquisicao),
        "garantia_ate": pd.Timestamp(garantia),
        "valor_rs": round(valor, 2),
    }
    erros = validar(dados)
    if erros:
        st.error("Corrija antes de cadastrar:\n\n" + "\n".join(f"- {e}" for e in erros))
    else:
        dados["responsavel"] = dados["responsavel"] or None
        st.session_state.novos.append(dados)
        st.session_state.mensagem = f"✅ {dados['codigo']} ({tipo} {dados['modelo']}) cadastrado."
        st.session_state.form_id += 1  # chaves novas = formulário em branco
        st.rerun()

if st.session_state.novos:
    st.subheader(f"Cadastrados nesta sessão ({len(st.session_state.novos)})")
    st.dataframe(pd.DataFrame(st.session_state.novos)[
        ["codigo", "tipo", "marca", "modelo", "setor", "responsavel", "status"]],
        hide_index=True, width="stretch")
    if st.button("Desfazer cadastros desta sessão"):
        st.session_state.novos = []
        st.rerun()
