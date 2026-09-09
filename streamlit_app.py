from __future__ import annotations
import streamlit as st
from src.generator import RAGGenerator

st.set_page_config(
    page_title="VendeFacil RAG",
    page_icon="VF",
    layout="wide",
)

@st.cache_resource
def load_rag() -> RAGGenerator:
    return RAGGenerator()

def render_sources(response) -> None:
    sources = response.sources_used
    if not sources:
        st.info("Nenhuma fonte foi exibida para esta resposta.")
        return

    st.subheader("Fontes consultadas")
    for index, source in enumerate(sources, start=1):
        with st.expander(f"{index}. {source.filepath} | {source.chunk_id}"):
            st.write(source.quotation)

def main() -> None:
    st.title("VendeFacil RAG")
    st.caption("Assistente fundamentado na base de conhecimento da empresa.")

    with st.sidebar:
        st.header("Demonstração")
        st.write("Consulte produtos, tickets, politicas e documentação interna.")
        st.markdown("**Exemplos**")
        examples = [
            "Quais sao os produtos oferecidos pela empresa VendeFacil?",
            "Como proceder quando houver erro STK-409?",
            "Qual e a politica de home office da Engenharia?",
        ]
        selected_example = st.selectbox("Pergunta de exemplo", [""] + examples)

    question = st.text_area(
        "Pergunta",
        value=selected_example,
        height=100,
        placeholder="Digite uma pergunta sobre a VendeFacil...",
    )

    if st.button("Consultar", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Digite uma pergunta antes de consultar.")
            return

        with st.spinner("Consultando a base de conhecimento..."):
            try:
                response = load_rag().ask(question.strip())
            except Exception as error:
                st.error(f"Nao foi possivel consultar o assistente: {error}")
                return

        if response.is_refusal:
            st.warning(response.answer)
        else:
            st.success(response.answer)

        metrics = st.columns(3)
        metrics[0].metric("Confianca", response.confidence_level)
        metrics[1].metric("Recusa", "Sim" if response.is_refusal else "Nao")
        metrics[2].metric("Fontes", len(response.sources_used))

        if response.reasoning:
            with st.expander("Justificativa"):
                st.write(response.reasoning)
        render_sources(response)


if __name__ == "__main__":
    main()