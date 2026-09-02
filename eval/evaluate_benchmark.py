from __future__ import annotations

import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.generator import RAGGenerator

from eval.judge_prompt import (
    build_answer_relevance_prompt,
    build_groundedness_prompt,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

BENCHMARK_FILE = (
    ROOT_DIR
    / "benchmark"
    / "questions_and_ground_truth.json"
)

REPORTS_DIR = ROOT_DIR / "reports"

RESULTS_JSON = (
    REPORTS_DIR / "benchmark_results.json"
)

RESULTS_CSV = (
    REPORTS_DIR / "benchmark_results.csv"
)

FAILURE_REPORT = (
    REPORTS_DIR / "failure_report.md"
)


# ============================================================
# ENV
# ============================================================

load_dotenv(ROOT_DIR / ".env")


# ============================================================
# UTILIDADES
# ============================================================

def safe_str(value: Any) -> str:
    """
    Converte qualquer valor para string segura.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def normalize_text(text: str) -> str:
    """
    Normaliza texto para comparações simples.
    """

    text = safe_str(text).lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def first_existing(
    data: dict,
    keys: list[str],
    default: Any = None,
) -> Any:
    """
    Retorna o primeiro campo existente.
    """

    for key in keys:
        if key in data:
            return data[key]

    return default


# ============================================================
# CARREGAMENTO DO BENCHMARK
# ============================================================

def load_benchmark() -> list[dict]:
    """
    Carrega o benchmark.

    Aceita tanto:

    [
        {...},
        {...}
    ]

    quanto:

    {
        "questions": [
            {...},
            {...}
        ]
    }
    """

    if not BENCHMARK_FILE.exists():
        raise FileNotFoundError(
            f"Benchmark não encontrado em:\n"
            f"{BENCHMARK_FILE}\n\n"
            f"Crie a pasta 'benchmark' na raiz e coloque "
            f"'questions_and_ground_truth.json' dentro dela."
        )

    with open(
        BENCHMARK_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    if isinstance(data, list):
        questions = data

    elif isinstance(data, dict):

        questions = first_existing(
            data,
            [
                "questions",
                "items",
                "benchmark",
                "data",
            ],
        )

        if questions is None:
            raise ValueError(
                "O JSON do benchmark foi carregado, "
                "mas não encontrei uma lista de perguntas. "
                "Campos esperados: questions, items, benchmark ou data."
            )

    else:
        raise ValueError(
            "Formato inválido do benchmark."
        )

    if not isinstance(questions, list):
        raise ValueError(
            "A lista de perguntas do benchmark não é válida."
        )

    return questions


# ============================================================
# EXTRAÇÃO DOS CAMPOS DO BENCHMARK
# ============================================================

def extract_question(item: dict) -> str:
    """
    Extrai a pergunta.
    """

    question = first_existing(
        item,
        [
            "question",
            "pergunta",
            "query",
            "input",
        ],
    )

    question = safe_str(question)

    if not question:
        raise ValueError(
            f"Pergunta não encontrada no item:\n{item}"
        )

    return question


def extract_reference_answer(item: dict) -> str:
    """
    Extrai a resposta esperada.
    """

    answer = first_existing(
        item,
        [
            "ground_truth_answer",
            "reference_answer",
            "expected_answer",
            "answer",
            "ground_truth",
            "expected_output",
            "resposta_esperada",
        ],
        "",
    )

    # Caso ground_truth seja um objeto
    if isinstance(answer, dict):

        answer = first_existing(
            answer,
            [
                "answer",
                "response",
                "text",
                "expected_answer",
            ],
            "",
        )

    return safe_str(answer)


def extract_expected_chunk_ids(item: dict) -> list[str]:
    """
    Extrai os chunk_ids esperados.

    Aceita diferentes nomes para facilitar compatibilidade
    com o formato do benchmark.
    """

    value = first_existing(
        item,
        [
            "ground_truth_chunk_ids",
            "expected_chunk_ids",
            "relevant_chunk_ids",
            "chunk_ids",
            "chunks",
            "source_chunk_ids",
        ],
        [],
    )

    if value is None:
        return []

    # Lista
    if isinstance(value, list):

        result = []

        for item_value in value:

            if isinstance(item_value, dict):

                chunk_id = first_existing(
                    item_value,
                    [
                        "chunk_id",
                        "id",
                    ],
                )

                if chunk_id:
                    result.append(
                        safe_str(chunk_id)
                    )

            else:
                value_str = safe_str(item_value)

                if value_str:
                    result.append(value_str)

        return result

    # String única
    if isinstance(value, str):

        # Se for uma lista serializada
        try:
            parsed = json.loads(value)

            if isinstance(parsed, list):
                return [
                    safe_str(x)
                    for x in parsed
                    if safe_str(x)
                ]

        except Exception:
            pass

        return [value.strip()] if value.strip() else []

    return []


def extract_expected_refusal(
    item: dict,
) -> bool | None:
    """
    Identifica se o benchmark espera uma recusa.
    """

    value = first_existing(
        item,
        [
            "is_refusal",
            "expected_refusal",
            "should_refuse",
            "recusa",
        ],
        None,
    )

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    value = normalize_text(
        safe_str(value)
    )

    return value in {
        "true",
        "1",
        "sim",
        "yes",
        "recusar",
        "recusado",
    }


def extract_expected_refusal_reason(
    item: dict,
) -> str | None:
    """
    Extrai o motivo esperado da recusa.
    """

    value = first_existing(
        item,
        [
            "refusal_reason",
            "expected_refusal_reason",
            "reason",
            "motivo_recusa",
        ],
        None,
    )

    if value is None:
        return None

    return safe_str(value)


# ============================================================
# EXTRAÇÃO DA RESPOSTA DO RAG
# ============================================================

def response_to_dict(response: Any) -> dict:
    """
    Converte resposta Pydantic/dict para dict.
    """

    if response is None:
        return {}

    if isinstance(response, dict):
        return response

    if hasattr(
        response,
        "model_dump",
    ):
        try:
            return response.model_dump()
        except Exception:
            pass

    if hasattr(
        response,
        "dict",
    ):
        try:
            return response.dict()
        except Exception:
            pass

    return {
        "answer": safe_str(response)
    }


def extract_answer(
    response: dict,
) -> str:

    return safe_str(
        first_existing(
            response,
            [
                "answer",
                "response",
                "text",
                "content",
            ],
            "",
        )
    )


def extract_sources(
    response: dict,
) -> list[dict]:

    sources = first_existing(
        response,
        [
            "sources_used",
            "sources",
            "evidences",
            "evidence",
            "retrieved_sources",
        ],
        [],
    )

    if not isinstance(
        sources,
        list,
    ):
        return []

    normalized = []

    for source in sources:

        if not isinstance(
            source,
            dict,
        ):
            continue

        chunk_id = first_existing(
            source,
            [
                "chunk_id",
                "id",
            ],
            "",
        )

        filepath = first_existing(
            source,
            [
                "filepath",
                "file_path",
                "source",
                "filename",
            ],
            "desconhecido",
        )

        quotation = first_existing(
            source,
            [
                "quotation",
                "quote",
                "text",
                "content",
            ],
            "",
        )

        normalized.append(
            {
                "filepath": safe_str(filepath),
                "chunk_id": safe_str(chunk_id),
                "quotation": safe_str(quotation),
            }
        )

    return normalized


def extract_is_refusal(
    response: dict,
) -> bool:

    value = response.get(
        "is_refusal",
        False,
    )

    if isinstance(
        value,
        bool,
    ):
        return value

    return normalize_text(
        safe_str(value)
    ) in {
        "true",
        "1",
        "sim",
        "yes",
    }


def extract_confidence(
    response: dict,
) -> str:

    return safe_str(
        response.get(
            "confidence_level",
            "",
        )
    )


def extract_refusal_reason(
    response: dict,
) -> str | None:

    value = response.get(
        "refusal_reason"
    )

    if value is None:
        return None

    return safe_str(value)


# ============================================================
# CONTEXT RELEVANCE
# ============================================================

def calculate_context_relevance(
    expected_chunk_ids: list[str],
    retrieved_chunk_ids: list[str],
) -> float:
    """
    Mede Context Relevance comparando chunk_ids.

    Fórmula usada:

        chunks esperados encontrados
        ----------------------------
        chunks esperados

    Se não houver chunk_ids esperados, retorna 1.0 quando
    não há contexto esperado ou 0.0 quando existem resultados
    inesperados.
    """

    expected = {
        safe_str(x)
        for x in expected_chunk_ids
        if safe_str(x)
    }

    retrieved = {
        safe_str(x)
        for x in retrieved_chunk_ids
        if safe_str(x)
    }

    if not expected:

        if not retrieved:
            return 1.0

        return 0.0

    intersection = expected & retrieved

    return round(
        len(intersection)
        / len(expected),
        4,
    )


# ============================================================
# CORREÇÃO DA RESPOSTA
# ============================================================

def calculate_correctness(
    answer: str,
    reference_answer: str,
    is_refusal: bool,
    expected_refusal: bool | None,
) -> float:
    """
    Estimativa determinística simples de correção.

    A avaliação semântica mais importante será feita pelo LLM Judge.

    Esta função cuida especialmente das recusas.
    """

    if expected_refusal is not None:

        if is_refusal == expected_refusal:
            return 1.0

        return 0.0

    if not reference_answer:
        return 1.0 if answer else 0.0

    normalized_answer = normalize_text(
        answer
    )

    normalized_reference = normalize_text(
        reference_answer
    )

    if not normalized_answer:
        return 0.0

    if (
        normalized_answer
        == normalized_reference
    ):
        return 1.0

    return 0.0


# ============================================================
# LLM JUDGE
# ============================================================

class LLMJudge:
    """
    Judge usando OpenAI-compatible API.

    Prioridade:

    1. OPENROUTER_API_KEY
    2. OPENAI_API_KEY

    Isso permite utilizar um provider OpenAI-compatible
    sem acoplar o benchmark ao gerador.
    """

    def __init__(self):

        self.client = None
        self.model = None

        api_key = (
            os.getenv(
                "OPENROUTER_API_KEY"
            )
            or os.getenv(
                "OPENAI_API_KEY"
            )
        )

        if not api_key:
            print(
                "\n[AVISO] Nenhuma API key encontrada "
                "para o LLM Judge."
            )

            print(
                "Answer Relevance e Groundedness "
                "serão marcados como N/A."
            )

            return

        try:

            from openai import OpenAI

            if os.getenv(
                "OPENROUTER_API_KEY"
            ):

                self.client = OpenAI(
                    api_key=api_key,
                    base_url=(
                        "https://openrouter.ai/api/v1"
                    ),
                )

                self.model = os.getenv(
                    "JUDGE_MODEL",
                    "openai/gpt-4.1-mini",
                )

            else:

                self.client = OpenAI(
                    api_key=api_key
                )

                self.model = os.getenv(
                    "JUDGE_MODEL",
                    "gpt-4o-mini",
                )

        except Exception as exc:

            print(
                f"\n[AVISO] Não foi possível "
                f"inicializar o LLM Judge: {exc}"
            )

            self.client = None

    @property
    def available(self) -> bool:
        return self.client is not None

    def _call(
        self,
        prompt: str,
    ) -> dict:

        if not self.available:
            return {
                "score": None,
                "reasoning": (
                    "LLM Judge não configurado."
                ),
            }

        try:

            response = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Você é um avaliador "
                                "preciso de sistemas RAG. "
                                "Responda somente JSON válido."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0,
                    max_tokens=300,
                )
            )

            content = (
                response
                .choices[0]
                .message
                .content
            )

            return parse_json_response(
                content
            )

        except Exception as exc:

            return {
                "score": None,
                "reasoning": (
                    f"Erro no LLM Judge: {exc}"
                ),
            }

    def answer_relevance(
        self,
        question: str,
        answer: str,
        reference_answer: str,
    ) -> dict:

        prompt = build_answer_relevance_prompt(
            question=question,
            answer=answer,
            reference_answer=reference_answer,
        )

        return self._call(prompt)

    def groundedness(
        self,
        question: str,
        context: str,
        answer: str,
    ) -> dict:

        prompt = build_groundedness_prompt(
            question=question,
            context=context,
            answer=answer,
        )

        return self._call(prompt)


# ============================================================
# PARSER JSON DO JUDGE
# ============================================================

def parse_json_response(
    text: str,
) -> dict:
    """
    Faz parsing defensivo da resposta do LLM.

    Resolve casos como:

    ```json
    {...}
    ```

    ou texto antes/depois do JSON.
    """

    text = safe_str(text)

    if not text:
        return {
            "score": None,
            "reasoning": (
                "Judge retornou resposta vazia."
            ),
        }

    # Tentativa 1
    try:

        data = json.loads(text)

        return normalize_judge_result(
            data
        )

    except json.JSONDecodeError:
        pass

    # Tentativa 2: bloco ```json
    match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        re.DOTALL,
    )

    if match:

        try:

            data = json.loads(
                match.group(1)
            )

            return normalize_judge_result(
                data
            )

        except json.JSONDecodeError:
            pass

    # Tentativa 3: primeiro objeto JSON
    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:

        candidate = text[
            start : end + 1
        ]

        try:

            data = json.loads(
                candidate
            )

            return normalize_judge_result(
                data
            )

        except json.JSONDecodeError:
            pass

    return {
        "score": None,
        "reasoning": (
            "Não foi possível interpretar "
            "o JSON retornado pelo Judge."
        ),
    }


def normalize_judge_result(
    data: Any,
) -> dict:

    if not isinstance(
        data,
        dict,
    ):
        return {
            "score": None,
            "reasoning": (
                "Formato inválido retornado pelo Judge."
            ),
        }

    score = data.get(
        "score"
    )

    try:

        if score is not None:
            score = float(score)

            score = max(
                0.0,
                min(
                    1.0,
                    score,
                ),
            )

    except (
        TypeError,
        ValueError,
    ):

        score = None

    reasoning = safe_str(
        data.get(
            "reasoning",
            "",
        )
    )

    return {
        "score": score,
        "reasoning": reasoning,
    }


# ============================================================
# CONTEXTO PARA O JUDGE
# ============================================================

def build_context(
    sources: list[dict],
) -> str:

    if not sources:
        return (
            "Nenhuma evidência foi recuperada."
        )

    parts = []

    for index, source in enumerate(
        sources,
        start=1,
    ):

        filepath = source.get(
            "filepath",
            "desconhecido",
        )

        chunk_id = source.get(
            "chunk_id",
            "desconhecido",
        )

        quotation = source.get(
            "quotation",
            "",
        )

        parts.append(
            f"[EVIDÊNCIA {index}]\n"
            f"arquivo: {filepath}\n"
            f"chunk_id: {chunk_id}\n"
            f"conteúdo: {quotation}"
        )

    return "\n\n".join(
        parts
    )


# ============================================================
# COERÊNCIA DA RECUSA
# ============================================================

def calculate_refusal_coherence(
    is_refusal: bool,
    confidence_level: str,
    expected_refusal: bool | None,
    expected_reason: str | None,
    actual_reason: str | None,
) -> float:
    """
    Calcula a parte de coerência:

    - is_refusal
    - confidence_level
    - refusal_reason
    """

    score = 0.0

    if expected_refusal is None:

        if not is_refusal:
            return 1.0

        confidence = normalize_text(
            confidence_level
        )

        if confidence in {
            "recusado",
            "refused",
        }:
            return 1.0

        return 0.5

    # is_refusal correto
    if is_refusal == expected_refusal:
        score += 0.5

    # confidence
    confidence = normalize_text(
        confidence_level
    )

    if expected_refusal:

        if confidence in {
            "recusado",
            "refused",
        }:
            score += 0.3

    else:

        if confidence not in {
            "recusado",
            "refused",
        }:
            score += 0.3

    # motivo
    if expected_reason:

        expected = normalize_text(
            expected_reason
        )

        actual = normalize_text(
            actual_reason or ""
        )

        if (
            expected
            and expected in actual
        ):
            score += 0.2

    else:

        score += 0.2

    return round(
        min(score, 1.0),
        4,
    )


# ============================================================
# EXECUÇÃO DE UMA QUESTÃO
# ============================================================

def evaluate_question(
    rag: RAGGenerator,
    judge: LLMJudge,
    item: dict,
    number: int,
) -> dict:

    question = extract_question(
        item
    )

    reference_answer = (
        extract_reference_answer(
            item
        )
    )

    expected_chunk_ids = (
        extract_expected_chunk_ids(
            item
        )
    )

    expected_refusal = (
        extract_expected_refusal(
            item
        )
    )

    expected_refusal_reason = (
        extract_expected_refusal_reason(
            item
        )
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"QUESTÃO {number}"
    )

    print(
        "=" * 70
    )

    print(
        f"Pergunta: {question}"
    )

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # EXECUTA O RAG
    # --------------------------------------------------------

    try:

        raw_response = rag.ask(
            question
        )

        response = response_to_dict(
            raw_response
        )

        execution_error = None

    except Exception as exc:

        response = {
            "answer": "",
            "sources_used": [],
            "confidence_level": "",
            "is_refusal": False,
            "refusal_reason": None,
        }

        execution_error = (
            f"{type(exc).__name__}: {exc}"
        )

        print(
            f"\nERRO AO EXECUTAR RAG:\n"
            f"{execution_error}"
        )

    latency_ms = (
        time.perf_counter()
        - start_time
    ) * 1000

    # --------------------------------------------------------
    # EXTRAI RESULTADO
    # --------------------------------------------------------

    answer = extract_answer(
        response
    )

    sources = extract_sources(
        response
    )

    retrieved_chunk_ids = [
        source["chunk_id"]
        for source in sources
        if source.get("chunk_id")
    ]

    is_refusal = extract_is_refusal(
        response
    )

    confidence_level = (
        extract_confidence(
            response
        )
    )

    refusal_reason = (
        extract_refusal_reason(
            response
        )
    )

    # --------------------------------------------------------
    # CONTEXT RELEVANCE
    # --------------------------------------------------------

    context_relevance = (
        calculate_context_relevance(
            expected_chunk_ids,
            retrieved_chunk_ids,
        )
    )

    # --------------------------------------------------------
    # CORREÇÃO
    # --------------------------------------------------------

    correctness = (
        calculate_correctness(
            answer=answer,
            reference_answer=reference_answer,
            is_refusal=is_refusal,
            expected_refusal=expected_refusal,
        )
    )

    # --------------------------------------------------------
    # COERÊNCIA
    # --------------------------------------------------------

    coherence = (
        calculate_refusal_coherence(
            is_refusal=is_refusal,
            confidence_level=confidence_level,
            expected_refusal=expected_refusal,
            expected_reason=expected_refusal_reason,
            actual_reason=refusal_reason,
        )
    )

    # --------------------------------------------------------
    # LLM JUDGE
    # --------------------------------------------------------

    answer_relevance_result = {
        "score": None,
        "reasoning": (
            "Não avaliado."
        ),
    }

    groundedness_result = {
        "score": None,
        "reasoning": (
            "Não avaliado."
        ),
    }

    # Para perguntas recusadas, não precisamos mandar
    # conteúdo sensível desnecessariamente ao Judge.
    if (
        not is_refusal
        and answer
    ):

        answer_relevance_result = (
            judge.answer_relevance(
                question=question,
                answer=answer,
                reference_answer=reference_answer,
            )
        )

        context = build_context(
            sources
        )

        groundedness_result = (
            judge.groundedness(
                question=question,
                context=context,
                answer=answer,
            )
        )

    # --------------------------------------------------------
    # PONTUAÇÃO DO DESAFIO
    # --------------------------------------------------------

    # 0.5 resposta correta
    points_correctness = (
        0.5 * correctness
    )

    # 0.3 fonte correta
    points_citation = (
        0.3 * context_relevance
    )

    # 0.2 coerência
    points_coherence = (
        0.2 * coherence
    )

    total_score = (
        points_correctness
        + points_citation
        + points_coherence
    )

    total_score = round(
        total_score,
        4,
    )

    # --------------------------------------------------------
    # DIAGNÓSTICO
    # --------------------------------------------------------

    failures = []

    if correctness < 1.0:
        failures.append(
            "resposta_incorreta"
        )

    if context_relevance < 1.0:
        failures.append(
            "recuperacao"
        )

    if coherence < 1.0:
        failures.append(
            "confidence_ou_recusa"
        )

    groundedness = (
        groundedness_result.get(
            "score"
        )
    )

    answer_relevance = (
        answer_relevance_result.get(
            "score"
        )
    )

    if (
        answer_relevance is not None
        and answer_relevance < 0.7
    ):
        failures.append(
            "answer_relevance"
        )

    if (
        groundedness is not None
        and groundedness < 0.7
    ):
        failures.append(
            "groundedness"
        )

    if execution_error:
        failures.append(
            "erro_execucao"
        )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    result = {
        "question_number": number,
        "question": question,

        "reference_answer": reference_answer,

        "answer": answer,

        "expected_chunk_ids": (
            expected_chunk_ids
        ),

        "retrieved_chunk_ids": (
            retrieved_chunk_ids
        ),

        "sources_used": sources,

        "context_relevance": (
            context_relevance
        ),

        "answer_relevance": (
            answer_relevance
        ),

        "answer_relevance_reasoning": (
            answer_relevance_result.get(
                "reasoning"
            )
        ),

        "groundedness": (
            groundedness
        ),

        "groundedness_reasoning": (
            groundedness_result.get(
                "reasoning"
            )
        ),

        "confidence_level": (
            confidence_level
        ),

        "is_refusal": (
            is_refusal
        ),

        "expected_refusal": (
            expected_refusal
        ),

        "refusal_reason": (
            refusal_reason
        ),

        "expected_refusal_reason": (
            expected_refusal_reason
        ),

        "correctness": (
            correctness
        ),

        "citation_score": (
            context_relevance
        ),

        "coherence_score": (
            coherence
        ),

        "points_correctness": (
            round(
                points_correctness,
                4,
            )
        ),

        "points_citation": (
            round(
                points_citation,
                4,
            )
        ),

        "points_coherence": (
            round(
                points_coherence,
                4,
            )
        ),

        "total_score": total_score,

        "latency_ms": round(
            latency_ms,
            2,
        ),

        "failures": failures,

        "execution_error": (
            execution_error
        ),
    }

    # --------------------------------------------------------
    # PRINT
    # --------------------------------------------------------

    print(
        "\nResposta:"
    )

    print(
        answer or "(vazia)"
    )

    print(
        f"\nContext Relevance: "
        f"{context_relevance:.2f}"
    )

    print(
        f"Answer Relevance: "
        f"{format_score(answer_relevance)}"
    )

    print(
        f"Groundedness: "
        f"{format_score(groundedness)}"
    )

    print(
        f"Pontuação: "
        f"{total_score:.2f} / 1.00"
    )

    if failures:

        print(
            "Falhas: "
            + ", ".join(
                failures
            )
        )

    else:

        print(
            "Status: OK"
        )

    return result


# ============================================================
# FORMATAÇÃO
# ============================================================

def format_score(
    score: float | None,
) -> str:

    if score is None:
        return "N/A"

    return f"{score:.2f}"


# ============================================================
# RELATÓRIO JSON
# ============================================================

def save_json(
    results: list[dict],
) -> None:

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = calculate_summary(
        results
    )

    data = {
        "summary": summary,
        "results": results,
    }

    with open(
        RESULTS_JSON,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"\nJSON salvo em:\n"
        f"{RESULTS_JSON}"
    )


# ============================================================
# RELATÓRIO CSV
# ============================================================

def save_csv(
    results: list[dict],
) -> None:

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "question_number",
        "question",
        "correctness",
        "context_relevance",
        "answer_relevance",
        "groundedness",
        "confidence_level",
        "is_refusal",
        "refusal_reason",
        "total_score",
        "latency_ms",
        "failures",
    ]

    with open(
        RESULTS_CSV,
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()

        for result in results:

            row = {
                field: result.get(
                    field,
                    "",
                )
                for field in fields
            }

            row["failures"] = ", ".join(
                result.get(
                    "failures",
                    [],
                )
            )

            writer.writerow(
                row
            )

    print(
        f"CSV salvo em:\n"
        f"{RESULTS_CSV}"
    )


# ============================================================
# RESUMO
# ============================================================

def average(
    values: list[float],
) -> float | None:

    if not values:
        return None

    return round(
        sum(values)
        / len(values),
        4,
    )


def calculate_summary(
    results: list[dict],
) -> dict:

    total = len(
        results
    )

    if total == 0:
        return {
            "total_questions": 0
        }

    context_values = [
        r["context_relevance"]
        for r in results
        if r.get(
            "context_relevance"
        )
        is not None
    ]

    answer_values = [
        r["answer_relevance"]
        for r in results
        if r.get(
            "answer_relevance"
        )
        is not None
    ]

    grounded_values = [
        r["groundedness"]
        for r in results
        if r.get(
            "groundedness"
        )
        is not None
    ]

    scores = [
        r["total_score"]
        for r in results
    ]

    correct_answers = sum(
        1
        for r in results
        if r.get(
            "correctness"
        )
        == 1.0
    )

    citation_ok = sum(
        1
        for r in results
        if r.get(
            "context_relevance"
        )
        == 1.0
    )

    coherent = sum(
        1
        for r in results
        if r.get(
            "coherence_score"
        )
        == 1.0
    )

    failures = {}

    for result in results:

        for failure in result.get(
            "failures",
            [],
        ):

            failures[failure] = (
                failures.get(
                    failure,
                    0,
                )
                + 1
            )

    return {
        "total_questions": total,

        "correct_answers": (
            correct_answers
        ),

        "answer_accuracy": round(
            correct_answers / total,
            4,
        ),

        "citation_full_match": round(
            citation_ok / total,
            4,
        ),

        "coherence_full_match": round(
            coherent / total,
            4,
        ),

        "context_relevance": (
            average(
                context_values
            )
        ),

        "answer_relevance": (
            average(
                answer_values
            )
        ),

        "groundedness": (
            average(
                grounded_values
            )
        ),

        "average_score": average(
            scores
        ),

        "score_percent": round(
            (
                sum(scores)
                / total
            )
            * 100,
            2,
        ),

        "failure_counts": failures,
    }


# ============================================================
# RELATÓRIO DE FALHAS
# ============================================================

def save_failure_report(
    results: list[dict],
) -> None:

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    failed = [
        result
        for result in results
        if result.get(
            "failures"
        )
    ]

    lines = []

    lines.append(
        "# Relatório de Falhas — Benchmark RAG"
    )

    lines.append("")

    lines.append(
        f"Total de questões: {len(results)}"
    )

    lines.append(
        f"Questões com falha: {len(failed)}"
    )

    lines.append("")

    lines.append(
        "## Diagnóstico"
    )

    lines.append("")

    lines.append(
        "As falhas são classificadas em:"
    )

    lines.append("")

    lines.append(
        "- `recuperacao`: chunk esperado não foi recuperado."
    )

    lines.append(
        "- `resposta_incorreta`: resposta não corresponde ao esperado."
    )

    lines.append(
        "- `answer_relevance`: resposta não atende bem à pergunta."
    )

    lines.append(
        "- `groundedness`: resposta contém informação sem suporte."
    )

    lines.append(
        "- `confidence_ou_recusa`: confidence ou recusa incoerente."
    )

    lines.append(
        "- `erro_execucao`: o RAG apresentou erro."
    )

    lines.append("")

    if not failed:

        lines.append(
            "## Nenhuma falha encontrada 🎉"
        )

    else:

        lines.append(
            "## Questões com falha"
        )

        lines.append("")

        for result in failed:

            number = result[
                "question_number"
            ]

            question = result[
                "question"
            ]

            lines.append(
                f"### Questão {number}"
            )

            lines.append("")

            lines.append(
                f"**Pergunta:** {question}"
            )

            lines.append("")

            lines.append(
                "**Falhas:** "
                + ", ".join(
                    result[
                        "failures"
                    ]
                )
            )

            lines.append("")

            lines.append(
                f"**Context Relevance:** "
                f"{format_score(result.get('context_relevance'))}"
            )

            lines.append(
                f"**Answer Relevance:** "
                f"{format_score(result.get('answer_relevance'))}"
            )

            lines.append(
                f"**Groundedness:** "
                f"{format_score(result.get('groundedness'))}"
            )

            lines.append("")

            lines.append(
                "**Resposta:**"
            )

            lines.append("")

            lines.append(
                result.get(
                    "answer",
                    "",
                )
                or "(vazia)"
            )

            lines.append("")

            lines.append(
                "**Chunks esperados:**"
            )

            lines.append("")

            lines.append(
                ", ".join(
                    result.get(
                        "expected_chunk_ids",
                        [],
                    )
                )
                or "nenhum"
            )

            lines.append("")

            lines.append(
                "**Chunks recuperados:**"
            )

            lines.append("")

            lines.append(
                ", ".join(
                    result.get(
                        "retrieved_chunk_ids",
                        [],
                    )
                )
                or "nenhum"
            )

            lines.append("")

            lines.append(
                "---"
            )

            lines.append("")

    with open(
        FAILURE_REPORT,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "\n".join(
                lines
            )
        )

    print(
        f"Relatório de falhas salvo em:\n"
        f"{FAILURE_REPORT}"
    )


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def main():

    print(
        "\n"
        + "=" * 70
    )

    print(
        "ETAPA 4 — BENCHMARK + RAG TRIAD"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # BENCHMARK
    # --------------------------------------------------------

    print(
        "\n1. Carregando benchmark..."
    )

    questions = load_benchmark()

    print(
        f"Perguntas carregadas: "
        f"{len(questions)}"
    )

    if len(questions) != 20:

        print(
            "\n[AVISO]"
        )

        print(
            "O desafio espera 20 perguntas, "
            f"mas foram encontradas {len(questions)}."
        )

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    print(
        "\n2. Inicializando RAG..."
    )

    rag = RAGGenerator()

    print(
        "RAG inicializado."
    )

    # --------------------------------------------------------
    # JUDGE
    # --------------------------------------------------------

    print(
        "\n3. Inicializando LLM Judge..."
    )

    judge = LLMJudge()

    if judge.available:

        print(
            f"Judge disponível: "
            f"{judge.model}"
        )

    else:

        print(
            "Judge indisponível."
        )

        print(
            "As métricas Answer Relevance "
            "e Groundedness ficarão como N/A."
        )

    # --------------------------------------------------------
    # EXECUTA
    # --------------------------------------------------------

    results = []

    for index, item in enumerate(
        questions,
        start=1,
    ):

        try:

            result = evaluate_question(
                rag=rag,
                judge=judge,
                item=item,
                number=index,
            )

        except Exception as exc:

            question = ""

            try:
                question = extract_question(
                    item
                )
            except Exception:
                pass

            result = {
                "question_number": index,
                "question": question,
                "reference_answer": "",
                "answer": "",
                "expected_chunk_ids": [],
                "retrieved_chunk_ids": [],
                "sources_used": [],
                "context_relevance": 0.0,
                "answer_relevance": None,
                "groundedness": None,
                "confidence_level": "",
                "is_refusal": False,
                "expected_refusal": None,
                "refusal_reason": None,
                "expected_refusal_reason": None,
                "correctness": 0.0,
                "citation_score": 0.0,
                "coherence_score": 0.0,
                "points_correctness": 0.0,
                "points_citation": 0.0,
                "points_coherence": 0.0,
                "total_score": 0.0,
                "latency_ms": 0.0,
                "failures": [
                    "erro_execucao"
                ],
                "execution_error": (
                    f"{type(exc).__name__}: {exc}"
                ),
            }

            print(
                f"\nERRO NA QUESTÃO {index}: "
                f"{exc}"
            )

        results.append(
            result
        )

    # --------------------------------------------------------
    # RELATÓRIOS
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "GERANDO RELATÓRIOS"
    )

    print(
        "=" * 70
    )

    save_json(
        results
    )

    save_csv(
        results
    )

    save_failure_report(
        results
    )

    # --------------------------------------------------------
    # RESUMO FINAL
    # --------------------------------------------------------

    summary = calculate_summary(
        results
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "RESULTADO FINAL"
    )

    print(
        "=" * 70
    )

    print(
        f"\nPerguntas: "
        f"{summary['total_questions']}"
    )

    print(
        f"Acerto: "
        f"{summary['answer_accuracy'] * 100:.2f}%"
    )

    print(
        f"Context Relevance: "
        f"{format_score(summary.get('context_relevance'))}"
    )

    print(
        f"Answer Relevance: "
        f"{format_score(summary.get('answer_relevance'))}"
    )

    print(
        f"Groundedness: "
        f"{format_score(summary.get('groundedness'))}"
    )

    print(
        f"Pontuação média: "
        f"{format_score(summary.get('average_score'))}"
    )

    print(
        f"Pontuação final: "
        f"{summary['score_percent']:.2f}%"
    )

    print(
        "\nArquivos gerados:"
    )

    print(
        f"- {RESULTS_JSON}"
    )

    print(
        f"- {RESULTS_CSV}"
    )

    print(
        f"- {FAILURE_REPORT}"
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "BENCHMARK FINALIZADO"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()