from __future__ import annotations
import os
import re
import csv
import json
import glob


PADROES_SENSIVEIS = [
    re.compile(r"\bsenha\b", re.IGNORECASE),
    re.compile(r"\bsalary\b|\bsal[aá]rio\b", re.IGNORECASE),
    re.compile(r"\broot\b", re.IGNORECASE),
    re.compile(r"\bapi[_ -]?key\b|\bchave de api\b", re.IGNORECASE),
    re.compile(r"\bcpf\b", re.IGNORECASE),
    re.compile(r"\bcart[aã]o\b.{0,20}\bfinal\b", re.IGNORECASE),
    re.compile(r"\bcredencia(is|l)\b", re.IGNORECASE),
]


def contem_informacao_sensivel(texto: str) -> bool:
    return any(p.search(texto) for p in PADROES_SENSIVEIS)


def carregar_tickets(caminho: str) -> list[dict]:
    documentos = []
    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            t = json.loads(linha)

            texto = (
                f"Chamado {t['ticket_id']} - {t['title']}\n"
                f"Cliente: {t.get('customer_name', '')} ({t.get('customer_id', '')})\n"
                f"Categoria: {t.get('category', '')} | Prioridade: {t.get('priority', '')} | "
                f"Status: {t.get('status', '')}\n"
                f"Descrição: {t.get('description', '')}\n"
            )
            if t.get("resolution"):
                texto += f"Resolução: {t['resolution']}\n"

            documentos.append({
                "text": texto.strip(),
                "metadata": {
                    "source": caminho,
                    "doc_type": "ticket",
                    "ticket_id": t.get("ticket_id"),
                    "customer_id": t.get("customer_id"),
                    "state": t.get("state"),
                    "module": t.get("module"),
                    "priority": t.get("priority"),
                    "status": t.get("status"),
                    "is_sensitive": contem_informacao_sensivel(texto),
                },
            })
    return documentos

def carregar_produtos(caminho: str) -> list[dict]:
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    documentos = []
    for nome_plano, info in dados.get("pricing_plans", {}).items():
        texto = (
            f"Plano {nome_plano} da VendeFácil.\n"
            f"Mensalidade: R$ {info.get('monthly_fee_brl')}. "
            f"Terminais inclusos: {info.get('included_terminals')}. "
            f"Terminal extra: R$ {info.get('extra_terminal_fee_brl')}.\n"
            f"{info.get('description', '')}"
        )
        documentos.append({
            "text": texto.strip(),
            "metadata": {
                "source": caminho,
                "doc_type": "pricing_plan",
                "plan": nome_plano,
                "is_sensitive": False,
            },
        })
    return documentos


def carregar_lojas(caminho: str) -> list[dict]:
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    documentos = []
    for loja in dados.get("network_stores", []):
        modulos = ", ".join(loja.get("active_modules", []))
        texto = (
            f"Loja {loja.get('store_name')} ({loja.get('store_id')}), "
            f"cliente {loja.get('company_name')} ({loja.get('customer_id')}), "
            f"localizada em {loja.get('city')}/{loja.get('state')}.\n"
            f"Terminais de PDV: {loja.get('pos_terminals_count')}. "
            f"Módulos ativos: {modulos}."
        )
        documentos.append({
            "text": texto.strip(),
            "metadata": {
                "source": caminho,
                "doc_type": "store_profile",
                "customer_id": loja.get("customer_id"),
                "state": loja.get("state"),
                "is_sensitive": False,
            },
        })
    return documentos

def carregar_funcionarios(caminho: str) -> list[dict]:
    documentos = []
    with open(caminho, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for linha in reader:
            texto = (
                f"Funcionário {linha['name']} ({linha['id']}), "
                f"cargo {linha['role']}, departamento {linha['department']}, "
                f"admitido em {linha['hire_date']}, status {linha['status']}. "
                f"Salário: R$ {linha['salary']}."
            )
            documentos.append({
                "text": texto,
                "metadata": {
                    "source": caminho,
                    "doc_type": "employee_record",
                    "department": linha.get("department"),
                    "is_sensitive": True,
                },
            })
    return documentos

def carregar_markdown(caminho: str, doc_type: str, modulo: str | None = None) -> dict:
    with open(caminho, "r", encoding="utf-8") as f:
        texto = f.read()

    return {
        "text": texto,
        "metadata": {
            "source": caminho,
            "doc_type": doc_type,
            "module": modulo,
            "is_sensitive": contem_informacao_sensivel(texto),
        },
    }


def carregar_pasta_markdown(pasta: str, doc_type: str, modulo_por_subpasta: bool = False) -> list[dict]:
    """Carrega todos os .md de uma pasta (opcionalmente uma pasta por módulo)."""
    documentos = []
    for caminho in sorted(glob.glob(os.path.join(pasta, "**", "*.md"), recursive=True)):
        modulo = None
        if modulo_por_subpasta:
            modulo = os.path.basename(os.path.dirname(caminho))
        documentos.append(carregar_markdown(caminho, doc_type, modulo))
    return documentos


_PADRAO_CUSTOMER_NO_NOME = re.compile(r"customer_(\d+)", re.IGNORECASE)


def carregar_emails(pasta: str) -> list[dict]:
    documentos = []
    for caminho in sorted(glob.glob(os.path.join(pasta, "*.txt"))):
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read()

        nome_arquivo = os.path.basename(caminho)
        match = _PADRAO_CUSTOMER_NO_NOME.search(nome_arquivo)
        customer_id = f"CUST{match.group(1).zfill(3)}" if match else None
        tipo_email = "customer_email" if nome_arquivo.startswith("customer_") else "internal_email"

        documentos.append({
            "text": texto,
            "metadata": {
                "source": caminho,
                "doc_type": tipo_email,
                "customer_id": customer_id,
                "is_sensitive": contem_informacao_sensivel(texto),
            },
        })
    return documentos


def carregar_todas_as_fontes_vetorizaveis(data_dir: str) -> list[dict]:
    documentos: list[dict] = []

    documentos += carregar_tickets(os.path.join(data_dir, "semi_structured", "tickets.jsonl"))
    documentos += carregar_produtos(os.path.join(data_dir, "structured", "products.json"))
    documentos += carregar_lojas(os.path.join(data_dir, "structured", "stores.json"))
    documentos += carregar_funcionarios(os.path.join(data_dir, "structured", "employees.csv"))

    documentos += carregar_pasta_markdown(
        os.path.join(data_dir, "unstructured", "policies"), doc_type="policy"
    )
    documentos += carregar_pasta_markdown(
        os.path.join(data_dir, "unstructured", "meetings"), doc_type="meeting_notes"
    )
    documentos += carregar_pasta_markdown(
        os.path.join(data_dir, "unstructured", "documentation"),
        doc_type="documentation",
        modulo_por_subpasta=True,
    )
    documentos += carregar_emails(os.path.join(data_dir, "unstructured", "emails"))

    return documentos
