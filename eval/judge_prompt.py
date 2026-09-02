"""
Prompts utilizados na avaliação da RAG Triad.

Métricas:
- Answer Relevance
- Groundedness
"""

ANSWER_RELEVANCE_PROMPT = """
Você é um avaliador especializado em sistemas RAG.

Sua tarefa é avaliar se a RESPOSTA realmente responde à PERGUNTA.

Não avalie se a resposta está bonita.
Não invente informações.
Não penalize uma resposta apenas porque ela está escrita de forma diferente
da resposta esperada.

Avalie somente a relevância da resposta em relação à pergunta.

ESCALA:

1.0 = responde completamente e diretamente à pergunta.
0.8 = responde corretamente, com pequenas omissões.
0.6 = responde parcialmente.
0.4 = responde de forma fraca ou incompleta.
0.2 = quase não responde à pergunta.
0.0 = não responde ou responde algo completamente diferente.

IMPORTANTE:
- Uma recusa correta para uma pergunta que deveria ser recusada deve ser considerada
  relevante.
- Uma resposta que inventa informação não deve receber nota alta.
- Não considere conhecimento externo ao contexto desta avaliação.

PERGUNTA:
{question}

RESPOSTA:
{answer}

RESPOSTA ESPERADA:
{reference_answer}

Retorne SOMENTE JSON válido.

Formato obrigatório:

{{
  "score": 0.0,
  "reasoning": "explicação curta"
}}
"""


GROUNDEDNESS_PROMPT = """
Você é um avaliador especializado em groundedness de sistemas RAG.

Sua tarefa é verificar se a RESPOSTA está fundamentada exclusivamente nas
EVIDÊNCIAS recuperadas.

Uma afirmação é fundamentada quando pode ser sustentada diretamente por
alguma das evidências fornecidas.

Uma afirmação é não fundamentada quando:
- não aparece nas evidências;
- contradiz as evidências;
- adiciona detalhes que não podem ser encontrados nas evidências;
- inventa fatos;
- atribui informações a uma fonte que não as contém.

IMPORTANTE:
Não use conhecimento externo para completar a resposta.

Avalie a resposta como um todo.

ESCALA:

1.0 = todas as afirmações relevantes estão fundamentadas.
0.8 = quase todas estão fundamentadas, com pequena extrapolação.
0.6 = parcialmente fundamentada.
0.4 = várias afirmações não possuem suporte.
0.2 = a maior parte não está fundamentada.
0.0 = a resposta é essencialmente inventada ou contradiz o contexto.

PERGUNTA:
{question}

EVIDÊNCIAS:

{context}

RESPOSTA:
{answer}

Retorne SOMENTE JSON válido.

Formato obrigatório:

{{
  "score": 0.0,
  "reasoning": "explicação curta"
}}
"""


def build_answer_relevance_prompt(
    question: str,
    answer: str,
    reference_answer: str,
) -> str:
    """
    Monta o prompt para Answer Relevance.
    """

    return ANSWER_RELEVANCE_PROMPT.format(
        question=question,
        answer=answer,
        reference_answer=reference_answer,
    )


def build_groundedness_prompt(
    question: str,
    context: str,
    answer: str,
) -> str:
    """
    Monta o prompt para Groundedness.
    """

    return GROUNDEDNESS_PROMPT.format(
        question=question,
        context=context,
        answer=answer,
    )