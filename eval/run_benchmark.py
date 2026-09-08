"""Entrada oficial para executar o benchmark completo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from eval.evaluate_benchmark import (
    RESULTS_JSON,
    calculate_summary,
    main as evaluate_all,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa as 20 perguntas do benchmark RAG.")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Exibe o resumo já salvo sem executar o RAG.",
    )
    args = parser.parse_args()

    if args.summary_only:
        data = json.loads(Path(RESULTS_JSON).read_text(encoding="utf-8"))
        print(json.dumps(data["summary"], ensure_ascii=False, indent=2))
        return

    evaluate_all()

    data = json.loads(Path(RESULTS_JSON).read_text(encoding="utf-8"))
    summary = data["summary"]
    print("\nResumo por categoria:")
    for category, values in summary.get("by_category", {}).items():
        print(
            f"- {category}: {values['total_questions']} questões, "
            f"acerto {values['answer_accuracy'] * 100:.1f}%, "
            f"nota média {values['average_score']:.2f}"
        )


if __name__ == "__main__":
    main()