from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SourceEvidence(BaseModel):

    filepath: str = Field(
        ...,
        description="Arquivo de origem do trecho citado"
    )

    chunk_id: str = Field(
        ...,
        description="Identificador do chunk recuperado"
    )

    quotation: str = Field(
        ...,
        max_length=500,
        description="Trecho literal que sustenta a resposta"
    )


class RAGResponse(BaseModel):

    answer: str

    confidence_level: Literal[
        "alta",
        "media",
        "baixa",
        "recusado"
    ]

    sources_used: list[SourceEvidence]

    reasoning: str

    is_refusal: bool

    refusal_reason: Literal[
        "lgpd",
        "fora_de_escopo",
        "sem_evidencia",
        None
    ] = None

    @model_validator(mode="after")
    def validar_consistencia(self):

        # ==================================================
        # RESPOSTA RECUSADA
        # ==================================================

        if self.is_refusal:

            if self.confidence_level != "recusado":
                raise ValueError(
                    "Uma resposta recusada deve ter "
                    "confidence_level='recusado'."
                )

            if self.sources_used:
                raise ValueError(
                    "Uma resposta recusada não pode possuir fontes."
                )

            if self.refusal_reason is None:
                raise ValueError(
                    "Uma resposta recusada precisa informar "
                    "refusal_reason."
                )

        # ==================================================
        # RESPOSTA NORMAL
        # ==================================================

        else:

            if not self.sources_used:
                raise ValueError(
                    "Uma resposta não recusada precisa possuir "
                    "pelo menos uma evidência."
                )

            if self.refusal_reason is not None:
                raise ValueError(
                    "Uma resposta não recusada deve possuir "
                    "refusal_reason=None."
                )

            if self.confidence_level == "recusado":
                raise ValueError(
                    "Uma resposta não recusada não pode ter "
                    "confidence_level='recusado'."
                )

        return self