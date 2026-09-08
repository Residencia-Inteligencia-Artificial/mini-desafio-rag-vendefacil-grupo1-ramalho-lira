"""Interface de demonstração local do assistente VendeFácil."""

from __future__ import annotations

from src.generator import RAGGenerator


def main() -> None:
    rag = RAGGenerator()
    print("VendeFácil RAG. Digite uma pergunta ou 'sair'.")
    while True:
        try:
            question = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"sair", "exit", "quit"}:
            break
        if not question:
            continue
        response = rag.ask(question)
        if hasattr(response, "model_dump"):
            response = response.model_dump()
        print(f"\nAssistente: {response.get('answer', '')}")
        for source in response.get("sources_used", []):
            print(
                f"- {source.get('filepath', 'desconhecido')} "
                f"[{source.get('chunk_id', 'sem chunk')}]"
            )


if __name__ == "__main__":
    main()