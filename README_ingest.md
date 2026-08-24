# Pipeline de Ingestão -- Etapa 1 (Mini Desafio RAG VendeFácil)

## O que este pipeline faz

```
Fontes heterogêneas (JSONL, JSON, CSV, Markdown, TXT)
        |
        v
  Loaders (src/loaders.py)      -- le e normaliza cada formato em {text, metadata}
        |
        v
  Chunking (src/chunking.py)    -- so para textos longos (politicas, atas, docs)
        |
        v
  Embeddings (src/embeddings.py) -- modelo local gratuito por padrao
        |
        v
  Indice vetorial FAISS (src/vector_store.py) -- com filtro por metadados
```

## Decisao de arquitetura mais importante: nem tudo vira embedding

`customers.csv` (2.000 linhas), `sales.csv` (3.000 linhas) e
`system_logs.csv` (450 linhas) **nao entram no indice vetorial**. Ficam
disponiveis via `src/structured_store.py`, que carrega cada um como um
DataFrame do pandas para consulta exata/agregada.

**Por que**: perguntas como "quanto vendemos em MG este mes" ou "qual
cliente tem mais chamados" sao perguntas de **contagem/soma/agregacao**.
RAG nao resolve bem esse tipo de pergunta -- a busca vetorial so retorna um
top-k de chunks parecidos, nao faz uma varredura completa da tabela. Um
`pandas.groupby()` (ou SQL) responde com 100% de precisao; embedar 3.000
linhas de venda uma a uma nao ajudaria e ainda arriscaria trazer a
linha errada por "parecenca" textual.

## O que entra no indice vetorial, e por que

| Fonte | doc_type | Vira quantos chunks? |
|---|---|---|
| `tickets.jsonl` | `ticket` | 1 chamado = 1 chunk (curto, sintoma+solucao juntos) |
| `products.json` | `pricing_plan` | 1 chunk por plano |
| `stores.json` | `store_profile` | 1 chunk por loja |
| `employees.csv` | `employee_record` | 1 chunk por funcionario (sensivel, ver abaixo) |
| `policies/*.md` | `policy` | Dividido por chunking recursivo |
| `meetings/*.md` | `meeting_notes` | Dividido por chunking recursivo |
| `documentation/<modulo>/*.md` | `documentation` | Dividido, com `module` extraido da subpasta |
| `emails/*.txt` | `customer_email` / `internal_email` | Dividido; `customer_id` extraido do nome do arquivo quando presente |

## Metadados extraidos (para filtro na busca)

Seguindo o schema de `starter/schema.py` (`QueryMetadataFilter`): `state`,
`module`, `customer_id`, `priority` sao extraidos diretamente dos campos ja
estruturados de `tickets.jsonl` (nao precisou de LLM para isso, o dado ja
vem certo). Alem disso, todo chunk recebe:

- `doc_type`: para filtrar por tipo de fonte.
- `is_sensitive`: `True` se o texto contem padroes de senha, salario,
  usuario root, CPF, chave de API ou credencial. Isso **nao impede** o
  chunk de ser indexado -- o sistema RAG precisa "ver" a informacao para
  saber que ela e sensivel na hora da resposta. O bloqueio de verdade
  (recusar responder) e responsabilidade da Etapa 3 (Guardrails), usando
  esta flag como sinal.

## Como rodar

```bash
pip install -r requirements.txt
python -m src.ingest --data-dir data --saida index_store
python -m src.testar_busca
```

Por padrao usa embeddings locais e gratuitos (`sentence-transformers`) --
nao precisa de nenhuma chave de API. Se quiser trocar para a OpenAI, copie
`.env.example` para `.env` e ajuste `EMBEDDING_PROVIDER=openai`.

## O que falta para as proximas etapas

- **Etapa 2**: um roteador de queries que decida, para cada pergunta, se vai
  no indice vetorial (`VectorStore`) ou na camada estruturada
  (`StructuredStore`) -- e complementar a busca vetorial com **BM25**
  (busca por palavra-chave) para a "busca hibrida" exigida no desafio.
- **Etapa 3**: usar a flag `is_sensitive` para implementar os guardrails de
  fato (recusar responder perguntas sobre salario, senha, etc.), e montar o
  pipeline de geracao com saida estruturada em `RAGResponse`
  (`starter/schema.py`).
- **Etapa 4**: avaliacao via RAG Triad (relevancia do contexto, relevancia
  da resposta, groundedness).
