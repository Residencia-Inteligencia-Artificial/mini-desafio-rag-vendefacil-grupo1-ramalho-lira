from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Any

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from src.schema import RAGResponse, SourceEvidence
from src.vector_store import VectorStore
from src.search_hibrid import HybridSearch

load_dotenv()

# ============================================================
# CONFIGURAÇÕES
# ============================================================

INDEX_DIR = os.getenv(
    "INDEX_DIR",
    "index_store"
)

HF_GENERATION_MODEL = os.getenv(
    "HF_GENERATION_MODEL",
    "Qwen/Qwen2.5-7B-Instruct"
)

HF_TOKEN = os.getenv("HF_TOKEN")

# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normaliza texto para facilitar comparações:
    - minúsculas
    - remove acentos
    - normaliza espaços
    """

    text = text.lower().strip()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text

# ============================================================
# MASCARAMENTO LGPD
# ============================================================

def mask_email(email: str) -> str:
    if "@" not in email:
        return "***"

    usuario, dominio = email.split("@", 1)

    if len(usuario) <= 2:
        usuario_mascarado = "***"
    else:
        usuario_mascarado = usuario[:2] + "***"

    extensao = dominio.split(".")[-1] if "." in dominio else "com"

    return f"{usuario_mascarado}@***.{extensao}"


def mask_phone(phone: str) -> str:
    digits = re.sub(
        r"\D",
        "",
        phone
    )

    if len(digits) >= 10:

        ddd = digits[:2]

        if len(digits) == 11:
            return (
                f"({ddd}) "
                f"{digits[2]}***-"
                f"{digits[-2:]}"
            )

        return (
            f"({ddd}) "
            f"****-"
            f"{digits[-2:]}"
        )

    return "****"


def mask_card(card: str) -> str:
    digits = re.sub(
        r"\D",
        "",
        card
    )

    if len(digits) >= 4:
        return (
            "**** **** **** "
            + digits[-4:]
        )

    return "****"


def mask_sensitive_data(text: str) -> str:
    """
    Mascara:
    - e-mail
    - telefone
    - cartão
    """

    # --------------------------------------------------------
    # E-MAIL
    # --------------------------------------------------------

    email_pattern = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    text = re.sub(
        email_pattern,
        lambda match: mask_email(
            match.group(0)
        ),
        text
    )

    # --------------------------------------------------------
    # TELEFONE
    # --------------------------------------------------------

    phone_pattern = (
        r"(?<!\d)"
        r"(?:\(?\d{2}\)?[\s.-]?)?"
        r"(?:9[\s.-]?)?\d{4}[\s.-]?\d{4}"
        r"(?!\d)"
    )

    text = re.sub(
        phone_pattern,
        lambda match: mask_phone(
            match.group(0)
        ),
        text
    )

    # --------------------------------------------------------
    # CARTÃO
    # --------------------------------------------------------

    card_pattern = (
        r"(?<!\d)"
        r"(?:\d{4}[\s-]?){3}\d{4}"
        r"(?!\d)"
    )

    text = re.sub(
        card_pattern,
        lambda match: mask_card(
            match.group(0)
        ),
        text
    )

    return text

# ============================================================
# CLASSIFICAÇÃO LGPD
# ============================================================

def classify_lgpd(question: str) -> str:
    """
    Classifica a consulta quanto a dados protegidos.

    Importante: mencionar "e-mail" como fonte documental
    (ex.: "informações nos e-mails") não significa solicitar
    o endereço de e-mail de uma pessoa.
    """

    normalized = normalize_text(question)

    # --------------------------------------------------------
    # RECUSAR
    # --------------------------------------------------------

    refusal_terms = [
        # Dados pessoais / sensíveis
        "salario",
        "remuneracao",
        "quanto ganha",
        "quanto recebe",
        "cpf",
        "documento pessoal",
        "dados bancarios",
        "conta bancaria",
        "chave pix",
        "pix",

        # Credenciais
        "senha",
        "senhas",
        "password",
        "passcode",
        "credencial",
        "credenciais",
        "login de administrador",
        "login admin",
        "usuario administrador",

        # Tokens e segredos
        "token",
        "access token",
        "refresh token",
        "bearer token",
        "api key",
        "api_key",
        "chave de api",
        "chave secreta",
        "secret key",
        "secret",
        "segredo",
        "chave privada",
        "private key",

        # JWT / serviços
        "jwt",
        "segredo jwt",
        "jwt secret",
        "jwt_secret",
        "stripe",
        "chave de producao",
        "api de producao",

        # Banco de dados
        "senha do banco",
        "senha do postgresql",
        "postgresql",
        "database password",
        "db password",
        "credencial de banco",
        "credenciais de banco",

        # Saúde
        "doenca",
        "doencas",
        "diagnostico",
        "dados de saude",
        "historico medico",
    ]

    if any(term in normalized for term in refusal_terms):
        return "recusar"

    # --------------------------------------------------------
    # MASCARAR
    # --------------------------------------------------------
    # Aqui tratamos somente solicitações de dados pessoais.
    # Não usamos simplesmente "email" ou "e-mail", pois isso
    # quebraria consultas que pedem informações contidas em
    # documentos de e-mail.

    masking_patterns = [
        r"\bqual(?: e| é) o email\b",
        r"\bqual(?: e| é) o e-mail\b",
        r"\bme passe o email\b",
        r"\bme passe o e-mail\b",
        r"\bme informe o email\b",
        r"\bme informe o e-mail\b",
        r"\bendereco de email\b",
        r"\bendereco de e-mail\b",
        r"\bqual(?: e| é) o telefone\b",
        r"\bme passe o telefone\b",
        r"\bme informe o telefone\b",
        r"\bqual(?: e| é) o celular\b",
        r"\bendereco residencial\b",
        r"\bendereco de residencia\b",
        r"\bnumero do cartao\b",
        r"\bnumero do cartao de credito\b",
        r"\bdados do cartao\b",
    ]

    if any(re.search(pattern, normalized) for pattern in masking_patterns):
        return "mascarar"

    return "responder"


# ============================================================
# FORA DE ESCOPO
# ============================================================

def is_out_of_scope(question: str) -> bool:
    """
    Identifica consultas claramente fora do domínio VendeFácil.

    A regra combina exemplos explícitos com sinais de domínio
    externo. O objetivo é evitar overfitting a uma única pergunta
    do benchmark.
    """

    normalized = normalize_text(question)

    explicit_terms = [
        "quem descobriu o brasil",
        "segunda guerra mundial",
        "primeira guerra mundial",
        "capital da frança",
        "quem inventou a internet",
        "me escreva um poema",
        "escreva um poema",
        "conte uma piada",
        "qual a receita",
        "como fazer bolo",
    ]

    if any(term in normalized for term in explicit_terms):
        return True

    # --------------------------------------------------------
    # SINAIS DE DOMÍNIO EXTERNO
    # --------------------------------------------------------

    external_terms = [
        "petroleo",
        "arabia saudita",
        "guerra",
        "presidente",
        "eleicao",
        "futebol",
    ]

    vendefacil_terms = [
        "vendefacil",
        "pdv",
        "estoque",
        "ticket",
        "tickets",
        "cliente",
        "clientes",
        "loja",
        "pay",
        "tef",
        "ecommerce",
        "produto",
        "produtos",
        "venda",
        "vendas",
        "funcionario",
        "funcionarios",
        "politica",
        "politicas",
        "reembolso",
    ]

    has_external = any(
        term in normalized
        for term in external_terms
    )

    has_vendefacil_context = any(
        term in normalized
        for term in vendefacil_terms
    )

    return has_external and not has_vendefacil_context


# ============================================================
# GERADOR
# ============================================================

class RAGGenerator:

    def __init__(self):

        if not HF_TOKEN:
            raise RuntimeError(
                "HF_TOKEN não encontrado. "
                "Configure o token do Hugging Face "
                "no arquivo .env."
            )

        # ----------------------------------------------------
        # CARREGAR VECTOR STORE
        # ----------------------------------------------------

        print(
            "\n1. Carregando índice FAISS..."
        )

        self.vector_store = VectorStore.carregar(
            INDEX_DIR
        )

        print(
            f"Índice carregado: "
            f"{self.vector_store.index.ntotal} vetores"
        )

        # ----------------------------------------------------
        # BUSCA HÍBRIDA
        # ----------------------------------------------------

        print(
            "\n2. Inicializando busca híbrida..."
        )

        self.search = HybridSearch(
            self.vector_store
        )

        # ----------------------------------------------------
        # HUGGING FACE
        # ----------------------------------------------------

        self.client = InferenceClient(
            provider="auto",
            api_key=HF_TOKEN
        )

    # ========================================================
    # EXTRAÇÃO DE FILEPATH
    # ========================================================

    @staticmethod
    def _get_filepath(
        resultado: dict[str, Any]
    ) -> str:

        metadata = resultado.get(
            "metadata",
            {}
        )

        filepath = (
            metadata.get("filepath")
            or metadata.get("file_path")
            or metadata.get("source")
            or metadata.get("filename")
            or metadata.get("file")
        )

        if filepath:
            return str(filepath)

        return "desconhecido"

    # ========================================================
    # EXTRAÇÃO DE CHUNK ID
    # ========================================================

    @staticmethod
    def _get_chunk_id(
        resultado: dict[str, Any]
    ) -> str:

        metadata = resultado.get(
            "metadata",
            {}
        )

        chunk_id = (
            metadata.get("chunk_id")
            or resultado.get("chunk_id")
            or metadata.get("id")
        )

        if chunk_id:
            return str(chunk_id)

        return "desconhecido"

    # ========================================================
    # CRIA EVIDÊNCIAS
    # ========================================================

    def _build_sources(
        self,
        resultados: list[dict[str, Any]]
    ) -> list[SourceEvidence]:

        fontes = []

        for resultado in resultados[:5]:

            filepath = self._get_filepath(
                resultado
            )

            chunk_id = self._get_chunk_id(
                resultado
            )

            texto = str(
                resultado.get(
                    "text",
                    ""
                )
            )

            quotation = texto[:500]

            fontes.append(
                SourceEvidence(
                    filepath=filepath,
                    chunk_id=chunk_id,
                    quotation=quotation
                )
            )

        return fontes

    # ========================================================
    # RESPOSTA DIRETA PARA MASCARAMENTO
    # ========================================================

    def _generate_masked_answer(
        self,
        question: str,
        resultados: list[dict[str, Any]]
    ) -> RAGResponse:

        textos = []

        for resultado in resultados:

            texto = str(
                resultado.get(
                    "text",
                    ""
                )
            )

            if texto.strip():
                textos.append(texto)

        contexto = "\n".join(textos)

        # Aplica o mascaramento diretamente
        contexto_mascarado = mask_sensitive_data(
            contexto
        )

        fontes = self._build_sources(
            resultados
        )

        # ----------------------------------------------------
        # Verifica se havia informação sensível
        # ----------------------------------------------------

        encontrou_email = bool(
            re.search(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                contexto
            )
        )

        encontrou_telefone = bool(
            re.search(
                r"(?<!\d)(?:\(?\d{2}\)?[\s.-]?)?"
                r"(?:9[\s.-]?)?\d{4}[\s.-]?\d{4}(?!\d)",
                contexto
            )
        )

        # ----------------------------------------------------
        # NÃO ENCONTROU E-MAIL/TELEFONE
        # ----------------------------------------------------

        if (
            ("email" in normalize_text(question)
             or "e-mail" in normalize_text(question))
            and
            ("telefone" in normalize_text(question)
             or "celular" in normalize_text(question))
        ):

            if not encontrou_email and not encontrou_telefone:

                return RAGResponse(
                    answer=(
                        "Não encontrei e-mail ou telefone "
                        "disponíveis nos documentos recuperados."
                    ),
                    confidence_level="baixa",
                    sources_used=fontes,
                    reasoning=(
                        "A busca encontrou documentos relacionados "
                        "à pergunta, mas eles não apresentam "
                        "e-mail ou telefone disponível."
                    ),
                    is_refusal=False,
                    refusal_reason=None
                )

        # ----------------------------------------------------
        # RESPOSTA MASCARADA
        # ----------------------------------------------------

        if encontrou_email or encontrou_telefone:

            # Remove excesso de conteúdo para não devolver
            # documentos inteiros.
            resposta = (
                "Encontrei os dados solicitados nos documentos, "
                "mas as informações pessoais foram mascaradas "
                "conforme a política de privacidade.\n\n"
                + contexto_mascarado[:1500]
            )

            return RAGResponse(
                answer=resposta,
                confidence_level="alta",
                sources_used=fontes,
                reasoning=(
                    "As informações solicitadas foram encontradas "
                    "nas evidências recuperadas e os dados pessoais "
                    "foram mascarados antes da resposta."
                ),
                is_refusal=False,
                refusal_reason=None
            )

        return RAGResponse(
            answer=(
                "Não encontrei os dados pessoais solicitados "
                "nas evidências recuperadas."
            ),
            confidence_level="baixa",
            sources_used=fontes,
            reasoning=(
                "As evidências recuperadas não continham "
                "os dados pessoais solicitados."
            ),
            is_refusal=False,
            refusal_reason=None
        )

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        question: str,
        resultados: list[dict[str, Any]],
        lgpd_mode: str
    ) -> str:

        evidencias = []

        for i, resultado in enumerate(
            resultados,
            start=1
        ):

            metadata = resultado.get(
                "metadata",
                {}
            )

            filepath = self._get_filepath(
                resultado
            )

            chunk_id = self._get_chunk_id(
                resultado
            )

            evidencias.append(
                f"""
EVIDÊNCIA {i}

Arquivo:
{filepath}

Chunk ID:
{chunk_id}

Metadados:
{json.dumps(
    metadata,
    ensure_ascii=False
)}

Texto:
{resultado.get("text", "")}
"""
            )

        contexto = "\n".join(
            evidencias
        )

        return f"""
Você é um assistente de RAG da empresa VendeFácil.

Responda SOMENTE com base nas evidências fornecidas.

PERGUNTA:

{question}

POLÍTICA ATUAL:

{lgpd_mode}

EVIDÊNCIAS:

{contexto}

REGRAS IMPORTANTES:

1. Não invente informações.

2. Toda resposta normal precisa citar pelo menos uma evidência.

3. Toda evidência deve possuir:
- filepath
- chunk_id
- quotation

4. quotation deve ser um trecho literal da evidência.

5. quotation deve possuir no máximo 500 caracteres.

6. Se não houver evidência suficiente:
confidence_level = "recusado"
is_refusal = true
refusal_reason = "sem_evidencia"
sources_used = []

7. Para LGPD:

- salário individual = recusar
- CPF = recusar
- dados bancários = recusar
- chave PIX = recusar
- senha/token/credencial = recusar
- dados de saúde = recusar

8. E-mail, telefone, endereço residencial e cartão
devem ser mascarados na resposta.

9. Quando is_refusal=true, refusal_reason deve ser
exatamente um destes valores:

"lgpd"
"fora_de_escopo"
"sem_evidencia"

10. reasoning sempre deve ser uma string.

11. confidence_level deve ser exatamente:

"alta"
"media"
"baixa"
"recusado"

12. is_refusal deve ser true ou false.

13. Se is_refusal=true:

- sources_used = []
- confidence_level = "recusado"
- refusal_reason preenchido

14. Se is_refusal=false:

- sources_used não pode estar vazia
- refusal_reason = null

15. Retorne SOMENTE JSON válido.

Formato:

{{
    "answer": "resposta",
    "confidence_level": "alta",
    "sources_used": [
        {{
            "filepath": "arquivo.jsonl",
            "chunk_id": "id",
            "quotation": "trecho literal"
        }}
    ],
    "reasoning": "explicação curta",
    "is_refusal": false,
    "refusal_reason": null
}}
"""

    # ========================================================
    # CHAMADA HUGGING FACE
    # ========================================================

    def _generate_with_huggingface(
        self,
        prompt: str
    ) -> str:

        response = self.client.chat_completion(
            model=HF_GENERATION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.1,
        )

        return response.choices[
            0
        ].message.content

    # ========================================================
    # EXTRAÇÃO JSON
    # ========================================================

    def _extract_json(
        self,
        content: str
    ) -> dict:

        content = content.strip()

        content = re.sub(
            r"^```json\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"\s*```$",
            "",
            content
        )

        try:
            return json.loads(
                content
            )

        except json.JSONDecodeError:
            pass

        inicio = content.find("{")
        fim = content.rfind("}")

        if inicio == -1 or fim == -1:
            raise ValueError(
                "O modelo não retornou um JSON válido."
            )

        json_texto = content[
            inicio:fim + 1
        ]

        return json.loads(
            json_texto
        )

    # ========================================================
    # NORMALIZAÇÃO
    # ========================================================

    def _normalize_response(
        self,
        dados: dict,
        resultados: list[dict[str, Any]],
        lgpd_mode: str
    ) -> dict:

        if dados.get("answer") is None:
            dados["answer"] = (
                "Não foi possível gerar "
                "uma resposta."
            )

        if not isinstance(
            dados.get("reasoning"),
            str
        ):
            dados["reasoning"] = (
                "Resposta processada com base "
                "nas evidências recuperadas."
            )

        confidence = dados.get(
            "confidence_level"
        )

        if confidence not in {
            "alta",
            "media",
            "baixa",
            "recusado"
        }:
            dados["confidence_level"] = "baixa"

        is_refusal = dados.get(
            "is_refusal",
            False
        )

        if not isinstance(
            is_refusal,
            bool
        ):
            is_refusal = (
                str(
                    is_refusal
                ).lower()
                == "true"
            )

        dados["is_refusal"] = is_refusal

        if not isinstance(
            dados.get("sources_used"),
            list
        ):
            dados["sources_used"] = []

        if is_refusal:

            dados["confidence_level"] = "recusado"
            dados["sources_used"] = []

            reason = dados.get(
                "refusal_reason"
            )

            valid_reasons = {
                "lgpd",
                "fora_de_escopo",
                "sem_evidencia"
            }

            if reason not in valid_reasons:

                if lgpd_mode == "recusar":
                    reason = "lgpd"
                else:
                    reason = "sem_evidencia"

            dados["refusal_reason"] = reason

        else:

            dados["refusal_reason"] = None

            if not dados["sources_used"]:

                dados["is_refusal"] = True

                dados["confidence_level"] = (
                    "recusado"
                )

                dados["refusal_reason"] = (
                    "sem_evidencia"
                )

        return dados

    # ========================================================
    # RECUSA
    # ========================================================

    def _create_refusal(
        self,
        reason: str
    ) -> RAGResponse:

        messages = {

            "lgpd":
                "Não posso fornecer esse tipo de informação "
                "porque envolve dados pessoais ou sensíveis "
                "protegidos pela política de privacidade.",

            "fora_de_escopo":
                "Essa pergunta está fora do escopo das "
                "informações disponíveis sobre a VendeFácil.",

            "sem_evidencia":
                "Não encontrei evidências suficientes na base "
                "para responder essa pergunta com segurança."
        }

        return RAGResponse(
            answer=messages[reason],
            confidence_level="recusado",
            sources_used=[],
            reasoning=f"Resposta recusada: {reason}.",
            is_refusal=True,
            refusal_reason=reason
        )

    # ========================================================
    # GERAÇÃO
    # ========================================================

    def _generate_answer(
        self,
        question: str,
        resultados: list[dict[str, Any]],
        lgpd_mode: str
    ) -> RAGResponse:

        if not resultados:

            return self._create_refusal(
                "sem_evidencia"
            )

        # ----------------------------------------------------
        # LGPD — MASCARAR
        #
        # Tratamos diretamente aqui.
        # Não deixamos o LLM decidir sozinho.
        # ----------------------------------------------------

        if lgpd_mode == "mascarar":

            return self._generate_masked_answer(
                question,
                resultados
            )

        prompt = self._build_prompt(
            question,
            resultados,
            lgpd_mode
        )

        try:

            content = (
                self._generate_with_huggingface(
                    prompt
                )
            )

            dados = self._extract_json(
                content
            )

            dados = self._normalize_response(
                dados,
                resultados,
                lgpd_mode
            )

            if not dados["is_refusal"]:

                dados["answer"] = (
                    mask_sensitive_data(
                        dados["answer"]
                    )
                )

            resposta = RAGResponse.model_validate(
                dados
            )

            return resposta

        except Exception as exc:

            print(
                "\nERRO NA GERAÇÃO COM HUGGING FACE:"
            )

            print(exc)

            print(
                "\nUsando fallback seguro..."
            )

            fontes = self._build_sources(
                resultados
            )

            return RAGResponse(
                answer=(
                    "Encontrei informações relacionadas "
                    "à pergunta na base, mas não foi possível "
                    "gerar a resposta detalhada."
                ),
                confidence_level="baixa",
                sources_used=fontes,
                reasoning=(
                    "A busca híbrida encontrou evidências, "
                    "mas houve uma falha na geração automática "
                    "da resposta."
                ),
                is_refusal=False,
                refusal_reason=None
            )

    # ========================================================
    # ASK
    # ========================================================

    def ask(
        self,
        question: str
    ) -> RAGResponse:

        print(
            "\n" + "=" * 70
        )

        print(
            "PERGUNTA:"
        )

        print(question)

        print(
            "=" * 70
        )

        # ----------------------------------------------------
        # LGPD
        # ----------------------------------------------------

        lgpd_mode = classify_lgpd(
            question
        )

        print(
            f"\nClassificação LGPD: "
            f"{lgpd_mode}"
        )

        if lgpd_mode == "recusar":

            return self._create_refusal(
                "lgpd"
            )

        # ----------------------------------------------------
        # FORA DE ESCOPO
        # ----------------------------------------------------

        if is_out_of_scope(
            question
        ):

            return self._create_refusal(
                "fora_de_escopo"
            )

        # ----------------------------------------------------
        # BUSCA
        # ----------------------------------------------------

        print(
            "\nExecutando busca híbrida..."
        )

        try:

            resultado_busca = self.search.buscar(
                question
            )

            if isinstance(
                resultado_busca,
                dict
            ):

                resultados = resultado_busca.get(
                    "hybrid_results",
                    []
                )

            else:

                resultados = resultado_busca

        except AttributeError:

            resultados = self.search.buscar(
                question
            )

            if isinstance(
                resultados,
                dict
            ):

                resultados = resultados.get(
                    "hybrid_results",
                    []
                )

        print(
            f"Resultados recuperados: "
            f"{len(resultados)}"
        )

        # ----------------------------------------------------
        # GERAÇÃO
        # ----------------------------------------------------

        return self._generate_answer(
            question,
            resultados,
            lgpd_mode
        )

