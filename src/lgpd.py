from __future__ import annotations

import re
import unicodedata


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalize(text: str) -> str:
    text = str(text).lower().strip()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    return text


# ============================================================
# SITUAÇÕES QUE DEVEM SER RECUSADAS
# ============================================================

REFUSE_PATTERNS = [

    # Salário individual
    r"\bsalario do funcionario\b",
    r"\bsalario de [a-z]+\b",
    r"\bquanto ganha\b",
    r"\bremuneracao de [a-z]+\b",

    # CPF
    r"\bqual.*cpf\b",
    r"\bcpf.*cliente\b",
    r"\bcpf.*funcionario\b",

    # Dados bancários
    r"\bdados bancarios de\b",
    r"\bconta bancaria de\b",
    r"\bagencia.*conta.*de\b",

    # Credenciais
    r"\bqual.*senha\b",
    r"\bsenha.*funcionario\b",
    r"\bsenha.*cliente\b",
    r"\bqual.*token\b",
    r"\btoken.*funcionario\b",
    r"\bcredencial.*funcionario\b",
    r"\bchave de api\b",

    # Saúde
    r"\bdados de saude de\b",
    r"\bhistorico medico de\b",
    r"\bdiagnostico de\b",
    r"\bdoenca de\b",
]


# ============================================================
# DADOS QUE PODEM SER MASCARADOS
# ============================================================

MASK_PATTERNS = [

    # E-mail
    r"\bemail\b",
    r"\be-mail\b",
    r"\bemail pessoal\b",
    r"\be-mail pessoal\b",

    # Telefone
    r"\btelefone\b",
    r"\btelefone pessoal\b",
    r"\bcelular\b",

    # Endereço
    r"\bendereco residencial\b",

    # Cartão
    r"\bnumero do cartao\b",
    r"\bcartao de credito\b",
]


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

def classify_query(query: str) -> str:

    query = normalize(query)

    # Primeiro: verificar recusa
    for pattern in REFUSE_PATTERNS:

        if re.search(
            pattern,
            query
        ):
            return "recusar"

    # Segundo: verificar mascaramento
    for pattern in MASK_PATTERNS:

        if re.search(
            pattern,
            query
        ):
            return "mascarar"

    # Caso normal
    return "responder"


# ============================================================
# MASCARAMENTO DE E-MAIL
# ============================================================

def mask_email(text: str) -> str:

    pattern = (
        r"\b([A-Za-z0-9._%+-]+)"
        r"@"
        r"([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
    )

    def replace(match):

        usuario = match.group(1)

        if len(usuario) <= 2:

            usuario_mascarado = (
                usuario[0] + "***"
            )

        else:

            usuario_mascarado = (
                usuario[:2] + "***"
            )

        return (
            f"{usuario_mascarado}"
            "@***.com"
        )

    return re.sub(
        pattern,
        replace,
        text
    )


# ============================================================
# MASCARAMENTO DE TELEFONE
# ============================================================

def mask_phone(text: str) -> str:

    pattern = (
        r"(?<!\d)"
        r"(?:\+?55\s?)?"
        r"(?:\(?\d{2}\)?\s?)?"
        r"9?\d{4,5}[-\s]?\d{4}"
        r"(?!\d)"
    )

    def replace(match):

        numero = re.sub(
            r"\D",
            "",
            match.group()
        )

        if len(numero) >= 4:

            return (
                "(**) 9****-**"
                + numero[-2:]
            )

        return "********"

    return re.sub(
        pattern,
        replace,
        text
    )


# ============================================================
# MASCARAMENTO DE CARTÃO
# ============================================================

def mask_card(text: str) -> str:

    pattern = (
        r"(?<!\d)"
        r"(?:\d[ -]?){13,19}"
        r"(?!\d)"
    )

    def replace(match):

        numero = re.sub(
            r"\D",
            "",
            match.group()
        )

        return (
            "**** **** **** "
            + numero[-4:]
        )

    return re.sub(
        pattern,
        replace,
        text
    )


# ============================================================
# MASCARAMENTO GERAL
# ============================================================

def mask_sensitive_data(text: str) -> str:

    text = mask_email(text)

    text = mask_phone(text)

    text = mask_card(text)

    return text