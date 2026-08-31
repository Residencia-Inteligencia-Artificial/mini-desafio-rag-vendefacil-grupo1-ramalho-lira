# Acompanhamento - Mini Desafio RAG VendeFácil

**Integrante 1:** Janice Lira - [@Janice977](https://github.com/Janice977)
**Integrante 2:** Emilly Ramalho - [@EmillySRamalho](https://github.com/EmillySRamalho)

**Repositório:** `mini-desafio-rag-vendefacil-grupo1-ramalho-lira`

---

## Como preencher

- Um bloco por encontro, em **ordem cronológica** - o encontro mais recente vai no **fim** do arquivo.
- O relato individual é escrito **pelo próprio integrante**, em primeira pessoa. Não escreva pelo colega.
- Escrever entre **17:30 e 17:40**. `commit` + `push` até as **18:00**, mesmo que o dia não tenha fechado.
- Mensagem de commit: `acompanhamento: AAAA-MM-DD`

**Um relato útil responde:** o que eu implementei, qual decisão técnica eu tomei e por quê, onde travei, e como (ou se) resolvi.

<details>
<summary>Exemplo de relato individual bom × ruim</summary>

❌ *"Trabalhei na parte de ingestão junto com meu colega. Avançamos bastante e conseguimos carregar os arquivos."*

✅ *"Implementei os loaders de CSV e JSONL em `src/ingest.py`. Decidi serializar cada linha do `customers.csv` como frase em linguagem natural em vez de manter o formato separado por vírgula, porque nos primeiros testes de similaridade os chunks CSV crus não recuperavam nada - o embedding não separa campo de valor. Travei ~40 min no `tickets.jsonl`: o `state` estava indo para o texto do chunk mas não para os metadados, então o filtro voltava vazio. Resolvi movendo a extração para antes da criação do `Document`. Usei o Claude para gerar o esqueleto do parser de JSONL; ajustei o schema de metadados na mão."*

</details>

---

## Encontro 1 - 2026-08-24

**Etapa:** 1 - Ingestão heterogênea, metadados e indexação vetorial

### Relato individual - Janice lira dos Santos 

* Etapa 1, primeiramente clonei o repositório do projeto no Google Colab para executar os testes do pipeline de ingestão.Depois rodei o comando python -m src.ingest, que processou 217 documentos de fontes variadas (tickets, políticas, e-mails, etc.) e gerou 251 chunks. Depois optei por deixar as tabelas estruturadas (customers.csv, sales.csv e system_logs.csv) fora do índice vetorial, pois a busca semântica não responde bem a perguntas de agregação em tabelas grandes. Em seguida, utilizei o Claude para gerar a estrutura base do código (loaders, chunking, FAISS), mas revisei manualmente a lógica de detecção de dados sensíveis.Enfim, Fiz buscas de teste para validar o comportamento do sistema e confirmar que os filtros por metadados (state e doc_type) estavam funcionando corretamente.

### Relato individual - Emilly Santos Ramalho

* Leitura do desafio
* Eu criei a organização no github e adicionei os membros
* Criei o repositorio do Desafio
* Clonamos os repositórios em nossa máquina
* Demos inicio a etapa 1, ainda está sendo revisada e sendo feita algumas alterações.


### Resumo do dia (escrito em conjunto)

Nós decidimos realizar todas as etapas em conjunto, trabalhando em parceria direta durante a sessão no Colab. Clonamos o repositório lado a lado e executamos o pipeline de ingestão desenvolvido para o projeto.

Ao executar o comando `python -m src.ingest`, acompanhamos todo o processamento de **217 documentos provenientes de fontes heterogêneas**, como e-mails, políticas e tickets, que resultou na geração de **251 chunks**.

Durante a execução, discutimos as decisões relacionadas ao tratamento dos dados. Em conjunto, concluímos que manter as tabelas `customers.csv`, `sales.csv` e `system_logs.csv` fora do índice vetorial seria a abordagem mais adequada, considerando que dados estruturados de grande volume e consultas de agregação não se encaixam bem no modelo de busca semântica.

Embora tenhamos utilizado o Claude como apoio para acelerar a criação da estrutura inicial, incluindo os carregadores, a lógica de chunking e a integração com FAISS, realizamos uma análise conjunta e detalhada da implementação. Revisamos linha por linha, principalmente a lógica responsável pela detecção e tratamento de dados sensíveis.

Por fim, realizamos testes manuais em conjunto, utilizando consultas de exemplo para validar o comportamento do sistema. Esses testes permitiram confirmar, na prática, que os filtros baseados em metadados, como `state` e `doc_type`, estavam sendo aplicados corretamente e retornando os documentos esperados.

**Entregamos hoje:**

* [ ] Clonagem e configuração do repositório no Colab.
* [ ] Execução do pipeline de ingestão com sucesso.
* [ ] Processamento de 217 documentos de fontes heterogêneas.
* [ ] Geração de 251 chunks.
* [ ] Definição dos arquivos CSV que permanecerão fora do índice vetorial.
* [ ] Revisão conjunta da lógica de detecção de dados sensíveis.
* [ ] Validação dos filtros por metadados (`state` e `doc_type`) por meio de testes manuais.

**Ficou pendente:**

* [ ] Continuar a validação do pipeline com outros cenários de consulta.
* [ ] Avaliar possíveis ajustes na estratégia de chunking e recuperação, caso sejam identificados problemas nos próximos testes.

**Bloqueios em aberto:**

* [ ] Nenhum bloqueio técnico identificado até o momento.

**Próximo passo (início do encontro 2):**

* [ ] Dar continuidade aos testes do sistema de busca.
* [ ] Avaliar a qualidade e relevância dos resultados recuperados.
* [ ] Verificar se os filtros e metadados continuam funcionando corretamente em diferentes cenários.
* [ ] Avançar para as próximas etapas da implementação do pipeline RAG.

**Uso de assistentes de IA:**

* Utilizamos o Claude como ferramenta de apoio para acelerar a criação da estrutura inicial do projeto, principalmente nos carregadores, na lógica de chunking e na integração com FAISS.
* Todo o código gerado com auxílio da IA foi analisado, discutido e revisado em conjunto antes de ser utilizado.
* A lógica de detecção de dados sensíveis recebeu revisão manual detalhada, garantindo que as decisões técnicas fossem compreendidas e validadas pela equipe.


## Encontro 2 - 2026-08-26

**Etapa:** 2 - Busca híbrida e filtragem por metadados

### Relato individual - Janice Lira dos Santos
*Atuei na **organização, documentação e versionamento dos entregáveis da Etapa 2**, realizada em trabalhoem dupla.

Minhas principais atividades foram:
* Criação e atualização do `acompanhamento.md`;
* Organização e revisão dos arquivos da etapa, incluindo o notebook `etapa_2_rag_vendefacil.ipynb`;
* Publicação, commit e versionamento dos arquivos no repositório do GitHub.

**Entregáveis sob minha responsabilidade:** documentação da etapa e publicação/versionamento dos arquivos no GitHub.

### Relato individual - Emilly Santos Ramalho

*  Fizemos a ingestão dos diferentes tipos de arquivos da base.
*  Aplicamos o chunking adaptativo de acordo com cada tipo de documento.
*  Organizamos os metadados de cada chunk.
*  Geramos os embeddings usando all-MiniLM-L6-v2.
*  Criamos e salvamos o índice vetorial com FAISS.
*  Testamos a busca com algumas perguntas para verificar os resultados.
*  Ao final, chegamos a 5.745 chunks indexados.

### Resumo do dia (escrito em conjunto)

* Realizamos algumas alterações na Etapa 1, incluindo a atualização de pastas e arquivos utilizados no processo de ingestão.
* Devido às mudanças na base, houve uma alteração na quantidade de chunks, então foi necessário recalcular e reprocessar a base vetorial local.
* Ao final do processamento, foram gerados 5.745 chunks.
* Geramos os embeddings utilizando o modelo sentence-transformers/all-MiniLM-L6-v2.
* Indexamos os embeddings utilizando o FAISS e salvamos o índice localmente.
* Também realizamos uma verificação de sanidade (sanity check) com três perguntas de teste para validar a recuperação dos conteúdos.
* Por fim, testamos o carregamento do índice já existente, confirmando que ele pode ser reutilizado sem precisar realizar uma nova indexação.

**Ficou pendente:**
-Foi iniciado a parte dois, mas será comitado somente no proximo encontro.

**Bloqueios em aberto:**
- Algumas alterações na etapa 1, atrasou um pouco o andamento da etapa 2.

**Próximo passo (início do encontro 3):**
- Iremos dar continuidade na etapa 2.

**Uso de assistentes de IA:**
- Utilizamos IA como apoio ao longo do desenvolvimento, principalmente para entender erros, discutir soluções e revisar partes do código. As sugestões foram adaptadas ao projeto e testadas pelo grupo durante a execução da Etapa 1.

---

## Encontro 3 - 2026-08-28

**Etapa:** 3 - Síntese estruturada, evidência e guardrails de LGPD

### Relato individual - Janice Lira dos Santos
*Nesta etapa desenvolvida em dupla com a Ramalho, atuei ativamente na estruturação do repositório, documentação dos avanços do projeto e no versionamento e sincronização das entregas no GitHub.
Minhas principais contribuições foram:
Documentação Técnica: Registrei detalhadamente o funcionamento da arquitetura de busca híbrida no arquivo acompanhamento.md, abrangendo a integração entre FAISS, BM25 e o algoritmo RRF.
Organização do Repositório: Padronizei a estrutura do notebook e dos arquivos do projeto, garantindo o correto alinhamento das entregas no GitHub.
Gestão de Versionamento: Realizei os commits individuais e a sincronização do repositório na branch principal.

### Relato individual - Emilly Santos Ramalho

* Dei continuidade ao desenvolvimento da busca, combinando os resultados do FAISS e do BM25.
* Ajustei o sistema para conseguir entender melhor as perguntas e identificar automaticamente os filtros necessários.
* Trabalhei na aplicação dos metadados durante a busca, deixando os resultados mais específicos para cada consulta.
* Fiz alguns testes com diferentes perguntas e fui ajustando o reconhecimento de termos e sinônimos conforme os resultados.
* No final, validei a busca com perguntas reais para conferir se os documentos retornados faziam sentido com o que estava sendo solicitado.

### Resumo do dia (escrito em conjunto)
*Implementamos a busca híbrida combinando a busca densa (FAISS) e a busca esparsa (BM25) com fusão via RRF.
Ajustamos o Query Analyzer para interpretar diferentes formas de perguntas, aprimorando a identificação de intenções, termos e sinônimos.
Aplicamos a filtragem por metadados para restringir a busca ao contexto exato da pergunta.
Realizamos testes práticos com múltiplos cenários de perguntas para validar a extração de filtros e a qualidade da recuperação.
Atualizamos a documentação individual do grupo e realizamos o versionamento e publicação dos arquivos no GitHub.

**Entregamos hoje:**
* Demos continuidade ao projeto trabalhando na busca híbrida, juntando a busca por embeddings com o BM25.
* Criamos o Query Analyzer para ajudar o sistema a entender a pergunta, normalizar o texto e identificar informações como tipo de documento, estado e módulo.
* Ajustamos os filtros para que a busca consiga considerar os metadados dos documentos antes de retornar os resultados.
* Implementamos o RRF para combinar os resultados do FAISS e do BM25 em um único ranking.
* Fizemos alguns testes com perguntas diferentes para verificar se os filtros estavam sendo identificados corretamente e se os resultados retornados realmente correspondiam ao que estava sendo perguntado.
* Durante os testes, fomos ajustando o reconhecimento de termos como “tickets”, “clientes”, “Minas Gerais” e “estoque”, deixando o analisador mais flexível para diferentes formas de fazer a mesma pergunta.

**Ficou pendente:**
*Consolidação final das métricas de avaliação do pipeline de busca e integração com a camada de geração de respostas do LLM.

**Bloqueios em aberto:**
* Nenhum bloqueio no momento.

**Próximo passo (início do encontro 4):**
- Iniciar a etapa 3, já que a segunda foi finalizada.

**Uso de assistentes de IA:**
- Utilizamos IA como apoio ao longo do desenvolvimento, principalmente para entender erros, discutir soluções e revisar partes do código. As sugestões foram adaptadas ao projeto e testadas pelo grupo durante a execução da Etapa 2.

---

## Encontro 4 - 2026-08-31

**Etapa:** 4 - Avaliação (RAG Triad), interface e relatório

### Relato individual - Janice Lira Dos Santos 

### Relato individual - Emilly Santos Ramalho

* Criei os modelos RAGResponse e SourceEvidence com Pydantic, deixando as respostas padronizadas com informações como resposta, nível de confiança, evidências, justificativa e motivo de recusa.
* Adicionei validações para evitar respostas inconsistentes, principalmente nos casos de recusa e nos diferentes níveis de confiança.
* Integrei a geração com a busca híbrida, utilizando os resultados do FAISS e BM25 combinados pelo RRF.
* Implementei o tratamento das perguntas relacionadas à LGPD, diferenciando situações em que o sistema pode responder e situações em que precisa recusar.
* Também tratei perguntas que estão fora do escopo da base da VendeFácil, evitando que o sistema tente responder assuntos que não estão disponíveis nos documentos.
* Passei a retornar as evidências utilizadas na resposta, incluindo o chunk_id e o trecho recuperado.

### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**

* Criamos os modelos RAGResponse e SourceEvidence com Pydantic, deixando as respostas padronizadas com informações como resposta, nível de confiança, evidências e motivo de recusa.
* Adicionamos validações para evitar respostas inconsistentes, principalmente nos casos de recusa e nos diferentes níveis de confiança.
* Integramos a geração com a busca híbrida, utilizando os resultados do FAISS e BM25 combinados pelo RRF.
* Implementamos o tratamento das perguntas relacionadas à LGPD, diferenciando as situações em que o sistema pode responder e aquelas em que precisa recusar.
* Também tratamos perguntas que estão fora do escopo da base da VendeFácil, evitando que o sistema tente responder assuntos que não estão disponíveis nos documentos.
* Passamos a retornar as evidências utilizadas nas respostas, incluindo o chunk_id e o trecho recuperado.
* No geral, testamos diferentes situações para verificar se todo o fluxo estava funcionando corretamente.

* Fizemos testes de buscas normais, verificando se as respostas e evidências retornadas estavam corretas. ✅
* Testamos perguntas que envolvem informações protegidas pela LGPD, garantindo que o sistema recusasse quando necessário. ✅
* Testamos perguntas fora do escopo da base para verificar se o sistema identificava e recusava corretamente. ✅
* Também testamos situações em que as informações solicitadas não estavam disponíveis nos documentos, evitando que o sistema inventasse dados. ✅
* Por fim, verificamos se as respostas apresentavam o nível de confiança e as evidências de forma consistente. ✅

Com isso, conseguimos validar o fluxo compl

**Ficou pendente:**
- Ainda Falta finalizar a etapa 4.

**Bloqueios em aberto:**
- 

**Preparação para o Demo Day:**
-

**Uso de assistentes de IA:**
- Utilizamos IA como apoio ao longo do desenvolvimento, principalmente para entender erros, discutir soluções e revisar partes do código. As sugestões foram adaptadas ao projeto e testadas pelo grupo durante a execução da Etapa 3.

---

*TIC em Trilhas · PUC-Rio · Instituto ECOA · MCTI Futuro · Softex*
