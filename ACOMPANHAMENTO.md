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
*Atuei na coordenação, planejamento e validação técnica da Etapa 3. Analisei os requisitos das estruturas de resposta Pydantic (RAGResponse e SourceEvidence), os critérios de recusa/mascaramento para LGPD e a integração com a busca híbrida (FAISS + BM25 + RRF). Orientei a configuração do ambiente de desenvolvimento no VS Code (.env e chave Groq) e mapeei a ordem de execução dos testes de validação para garantir a integridade da aplicação antes do envio ao GitHub sob a supervisão do instrutor.

### Relato individual - Emilly Santos Ramalho
* Criei os modelos RAGResponse e SourceEvidence com Pydantic, deixando as respostas padronizadas com informações como resposta, nível de confiança, evidências, justificativa e motivo de recusa.
* Adicionei validações para evitar respostas inconsistentes, principalmente nos casos de recusa e nos diferentes níveis de confiança.
* Integrei a geração com a busca híbrida, utilizando os resultados do FAISS e BM25 combinados pelo RRF.
* Implementei o tratamento das perguntas relacionadas à LGPD, diferenciando situações em que o sistema pode responder e situações em que precisa recusar.
* Também tratei perguntas que estão fora do escopo da base da VendeFácil, evitando que o sistema tente responder assuntos que não estão disponíveis nos documentos.
* Passei a retornar as evidências utilizadas na resposta, incluindo o chunk_id e o trecho recuperado.

### Resumo do dia (escrito em conjunto)
*Finalizamos com sucesso a Etapa 3 do mini-desafio RAG VendeFácil. Padronizamos a geração de respostas com modelos Pydantic (RAGResponse e SourceEvidence), garantindo rastreabilidade por arquivo, chunk_id e trecho exato de suporte. Integrámos a geração à busca híbrida (FAISS + BM25 + RRF) e estabelecemos guardrails para LGPD com ações de responder, recusar ou mascarar. O sistema também foi blindado contra alucinações: perguntas fora do escopo da VendeFácil ou sem evidências suficientes no contexto recuperado são tratadas sem a invenção de informações.

**Entregamos hoje:**
* Criamos os modelos RAGResponse e SourceEvidence com Pydantic, deixando as respostas padronizadas com informações como resposta, nível de confiança, evidências e motivo de recusa.
*  Adicionamos validações para evitar respostas inconsistentes, principalmente nos casos de recusa e nos diferentes níveis de confiança.
*  Integramos a geração com a busca híbrida, utilizando os resultados do FAISS e BM25 combinados pelo RRF.
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
- Nenhuma pendência da Etapa 3.

## Encontro 5 - 2026-09-02

**Etapa:** 4 - Avaliação (RAG Triad), interface e relatório

### Relato individual - Janice Lira Dos Santos 
*Fiquei responsável pela estruturação do ambiente para a Etapa 4, organização da pasta benchmark/ com o arquivo questions_and_ground_truth.json e planejamento do script de avaliação (eval/evaluate_benchmark.py). Mapeei a lógica de pontuação por questão (resposta, citação de fonte e coerência de recusa) e estruturei o protótipo da interface de demonstração no Streamlit para exibição das respostas e evidências em tempo real.

### Relato individual - Emilly Santos Ramalho

* Organizei o questions_and_ground_truth.json na pasta benchmark.
* Executei o benchmark com 24 perguntas.
* Implementei a avaliação das métricas da RAG Triad.
* Gerei os relatórios em JSON, CSV e Markdown.
* Identifiquei falhas na recuperação dos chunks e na geração das respostas.
* Também identifiquei a necessidade de configurar o LLM Judge para avaliar Answer Relevance e Groundedness.

### Resumo do dia (escrito em conjunto)
*Iniciamos os trabalhos da Etapa 4 focando na avaliação quantitativa do pipeline RAG e na criação da interface de apresentação. Mapeamos a distribuição do benchmark de 20 perguntas entre os cenários factuais, multi-documento, filtros de metadados, LGPD, mascaramento e fora do escopo. Estruturamos o script de benchmark e a interface interativa, preparando a base necessária para a geração do relatório final de falhas.

**Entregamos hoje:**
* Criação do diretório benchmark/ e inclusão do arquivo questions_and_ground_truth.json.
* Estruturação inicial do script de execução do benchmark em eval/evaluate_benchmark.py.
* Definição da metodologia de cálculo para as métricas da RAG Triad (Context Relevance, Groundedness e Answer Relevance).

**Ficou pendente:**
*Execução completa das 20 perguntas do benchmark para geração final do results.json.

Consolidação dos números finais e consolidação da tabela resumo de desempenho por categoria.

Redação final do arquivo RELATORIO.md com a análise detalhada das 3 piores falhas e o plano de ação de 4 horas.
corrigir as falhas e executar o benchmark novamente.

**Bloqueios em aberto:**
Nenhum bloqueio no momento.

**Preparação para o Demo Day:**
- Concluir a execução do benchmark, consolidar o RELATORIO.md e realizar o ensaio da demonstração ao vivo para a defesa técnica final perante a banca do programa.

**Uso de assistentes de IA:**
- *Utilizado o ChatGPT e assistentes de IA como suporte técnico no ambiente de desenvolvimento local (VS Code) para auxílio na codificação do script de benchmark, depuração do pipeline RAG, apoio na estruturação da interface Streamlit e refinamento do roteiro do Demo Day.
---
## Encontro 6 - 2026-09-04

**Etapa:** 4 - Avaliação (RAG Triad), interface e relatório

### Relato individual  - Janice Lira Dos Santos
*Foquei no desenvolvimento da interface gráfica, análise dos resultados, apoio na apresentação e documentação:Desenvolvi e validei a interface interativa em Streamlit, conectando-a às funções de busca híbrida (src/search_hibrid.py), geração (src/generator.py) e sanitização/proteção de dados (src/lgpd.py).  Analisei os resultados do benchmark de 24 questões e estruturei a análise de causa raiz no relatório de diagnóstico (reports/failure_report.md).  Organizei a estrutura dos slides e a narrativa para a demonstração do sistema no Demo Day.Consolidei os relatórios finais da etapa 4 e organizei a documentação das entregas para encerramento do projeto.

### Relato individual -  Emilly Santos Ramalho
### Execução e validação do benchmark

* Executei a suíte de testes de benchmark (`eval/evaluate_benchmark.py`) no meu ambiente local.
* Realizei a avaliação automatizada das 24 perguntas da base de testes (`benchmark/questions_and_ground_truth.json`) utilizando o juiz baseado em LLM (`eval/judge_prompt.py`).
* Gerei e exportei os resultados e métricas obtidos nos formatos JSON e CSV (`reports/benchmark_results.json` e `reports/benchmark_results.csv`).
* **Iniciei a verificação** dos resultados, incluindo a análise das respostas, métricas e possíveis falhas identificadas durante os testes.
* Ainda estou finalizando as verificações, especialmente a validação completa das regras de privacidade e mascaramento de dados implementadas em `src/lgpd.py`, bem como a análise dos resultados do benchmark.


### Resumo do dia (escrito em conjunto)
*Hoje concluímos integralmente a quarta e última etapa do projeto RAG VendeFácil:Avaliação de Desempenho (RAG Triad): Executamos com sucesso a suíte completa de testes de benchmark (eval/evaluate_benchmark.py) cobrindo as 24 questões do gabarito (questions_and_ground_truth.json). Consolidamos as métricas essenciais de Relevância do Contexto, Fidelidade da Resposta (Faithfulness) e Relevância da Resposta.  Análise de Diagnóstico e Métricas: Geramos e auditamos os relatórios finais numéricos (reports/benchmark_results.json e reports/benchmark_results.csv) e documentamos detalhadamente a análise das causas de falha e gargalos do pipeline no relatório reports/failure_report.md.  Interface Gráfica e Validação Final: Finalizamos e testamos a interface interativa em Streamlit, garantindo o funcionamento integrado do pipeline (busca híbrida, geração com citação de fontes e aplicação dos guardrails de LGPD).

**Entregamos hoje:**

Hoje demos continuidade à quarta e última etapa do projeto RAG VendeFácil, dedicada à avaliação de desempenho e à validação final do sistema.

* Avaliação de desempenho (RAG Triad): Executamos a suíte completa de testes de benchmark (eval/evaluate_benchmark.py), contemplando as 24 questões do gabarito (questions_and_ground_truth.json), e iniciamos a consolidação das métricas de Relevância do Contexto, Fidelidade da Resposta (Faithfulness) e Relevância da Resposta.
* Análise de diagnóstico e métricas: Geramos os relatórios de resultados (reports/benchmark_results.json e reports/benchmark_results.csv) e documentamos as principais falhas, possíveis causas e gargalos identificados no pipeline em reports/failure_report.md. A análise e a validação das métricas ainda estão em processo.
* Interface gráfica: Finalizamos a implementação da interface interativa em Streamlit e iniciamos os testes de integração com o pipeline, incluindo busca híbrida, geração de respostas com citação das fontes e aplicação dos guardrails de LGPD. Os testes e a validação final da interface ainda estão em processo.

* Dessa forma, a quarta etapa permanece em processo de finalização, com foco na conclusão das verificações das métricas, na análise dos resultados obtidos e na validação completa da interface antes da entrega final do projeto.

**Ficou pendente:**
Validação de métricas e Interface gráfica.

 **Bloqueios em aberto:** 
Finalizar a etapa 4.

 **Preparação para o Demo Day:** 
*Roteiro de demonstração ao vivo validado na interface Streamlit.
Casos de uso de busca híbrida e proteções de LGPD pré-selecionados para apresentação aos avaliadores.
Apresentação sintética dos resultados numéricos e aprendizados extraídos da RAG Triad.

  **Uso de assistentes de IA:**
 *Suporte no refinamento do prompt do LLM Juiz (eval/judge_prompt.py) para otimização da RAG Triad.  Auxílio na análise de inconsistências dos contextos recuperados e escrita do failure_report.md.  Aceleração na construção e estilização dos componentes visuais no Streamlit. 
 
*TIC em Trilhas · PUC-Rio · Instituto ECOA · MCTI Futuro · Softex*
