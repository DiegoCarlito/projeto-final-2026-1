## Sessão 1 (04/07/2026)

> Alinhamento Inicial & Spec-Driven Development (SDD)

---

### 1. Atividades Realizadas

Estabelecemos a fundação documental e estratégica do projeto seguindo as diretrizes de Engenharia de Software Agêntica (Spec-Driven Development). O foco foi mapear o escopo do problema, o comportamento esperado do agente e as regras de qualidade do código antes do início da implementação técnica.

Os seguintes artefatos obrigatórios foram inteiramente especificados, revisados e validados:

1. **`docs/mission-brief.md`**: Definição clara do contrato entre humano e agente. Mapeamos os objetivos do Analista Assistente de Retenção, os utilizadores-alvo (equipa de Customer Success), o formato estrito de entrada e saída (JSON), limites de escopo e os principais riscos operacionais (falsos positivos, latência e alucinações).
2. **`agent.md`**: Especificação completa da persona do agente, o tom de resposta puramente corporativo e orientado a negócios (evitando jargões técnicos excessivos), as ferramentas iniciais (`predict_churn_model` e `extract_feature_importance`), critérios de paragem e a política de degradação graciosa (fallback).
3. **`docs/mentorship-pack.md`**: Formalização dos padrões de código exigidos (princípios de Clean Code, Python 3.11+, tratamento explícito de erros, funções pequenas com responsabilidade única, proibição de *magic numbers*) e orientações de arquitetura.
4. **`docs/workflow-runbook.md`**: Alinhamento do passo a passo sequencial auditável para garantir a execução correta das 10 etapas do projeto.

---

### 2. Planejamento para a Próxima Sessão (05/07)

- Executar a **Etapa 2 e 3** do Runbook: Propor formalmente e estruturar os diretórios das três soluções obrigatórias (`solution-a`, `solution-b`, `solution-c`).
- Iniciar o desenvolvimento do protótipo mínimo da **`solution-a`**: pipeline contendo um modelo tabular simples (Regressão Logística ou Árvore de Decisão) + integração com LLM atuando puramente como formatador da explicação com base nos pesos reais das variáveis.

## Sessão 2 (05/07/2026)

> Estruturação do Framework de Soluções & Implementação da Solution A

---

### 1. Atividades Realizadas

Focamos na estruturação arquitetural das três abordagens exigidas e na implementação do baseline (Solution A), garantindo a separação de responsabilidades e a preparação da infraestrutura de código.

Os seguintes marcos técnicos e documentais foram concluídos:

1. **Estruturação de Diretórios e Runbook (Etapas 2 e 3):** Descrevemos formalmente as três soluções no `workflow-runbook.md` e criamos a árvore de pastas modular em `/solutions`.
2. **Documentação Arquitetural:** Escrevemos os arquivos `README.md` detalhados para cada solução e um documento centralizador. Atualizamos o escopo para utilizar o modelo **Gemini 2.5 Flash** (rápido e sem custo), mantendo a arquitetura híbrida (Determinística + Agente IA).
3. **Desenvolvimento da Solution A (Etapa 4):** Implementamos o código completo e funcional do protótipo mínimo:
    - `train.py`: Pipeline de pré-processamento e treino usando Regressão Logística.
    - `model_wrapper.py`: Isolamento do modelo estatístico e lógica de extração dos coeficientes globais de risco.
    - `agent_a.py`: Agente orquestrador que conecta a predição ao Gemini 2.5 Flash, incluindo mecânica inicial de Fallback para resiliência.
    - `app.py`: Camada de exposição da API via FastAPI.
4. **Segurança de Credenciais:** Configuração de variáveis de ambiente via `.env` e isolamento via `.gitignore` para proteção da API Key.

*Nota: A execução local e a validação do pipeline desenvolvido foram agendadas para o início da próxima sessão.*

---

### 2. Planejamento para a Próxima Sessão (06/07 — retomado em 09/07)

- **Validação Prática da Solution A:** Garantir a obtenção do dataset, executar o script de treinamento, subir o servidor local e testar o endpoint de predição via Swagger/Postman para validar o retorno do JSON com a explicação do LLM.
- **Desenvolvimento da Solution B (Etapa 4):** Iniciar o código do modelo preditivo avançado (Random Forest) e implementar a ferramenta de explicabilidade local (SHAP Tool) para que o Agente justifique o risco com pesos matemáticos exatos para cada cliente.

## Sessão 3 (09/07/2026)

> Consolidação do fluxo de desenvolvimento em uma única ferramenta agêntica (Claude Code)

---

### 1. Atividades Realizadas

O uso do GitHub Copilot e do chat do Gemini Pro para desenvolvimento foi descontinuado. O Claude Code passa a ser a única ferramenta de IA de desenvolvimento do projeto, cobrindo especificação, geração de código, testes, execução e revisão — diferença chave em relação ao fluxo anterior, em que nenhuma IA de fato executava comandos no ambiente.

1. **Criação de `CLAUDE.md` na raiz do repositório:** substitui `docs/ai-workflow/gemini-system-instructions.md` (removido) e `.github/copilot-instructions.md` (removido). É carregado automaticamente pelo Claude Code em toda sessão, eliminando a necessidade de colar instruções de sistema manualmente. Documenta o papel do Claude Code, as regras operacionais (stack fixa, Clean Code, runbook sequencial, sinalização de commits) e, com destaque, a regra de arquitetura que separa a ferramenta de desenvolvimento (Claude Code) do modelo usado em runtime pelo produto (Gemini 2.5 Flash via API).
2. **Atualização de `docs/ai-workflow/project-context.md`:** seção 1 (ferramentas) e seção 10 (papel da IA) revisadas para refletir o Claude Code; seção 6 (stack técnica) passou a listar explicitamente o Gemini 2.5 Flash como dependência de runtime do agente, evitando confusão futura com a ferramenta de desenvolvimento; árvore de pastas (seção 5) atualizada.
3. **Limpeza de configuração do Copilot:** removidas as referências a `github.copilot*` de `.vscode/settings.json` e `.vscode/extensions.json`.

*Nota: nenhuma regra de arquitetura do produto (modelo tabular, SHAP, Gemini 2.5 Flash, guardrails, fallback) foi alterada com a consolidação de ferramentas — apenas o fluxo de desenvolvimento.*

---

### 2. Continuação: retomada do plano pendente da Sessão 2

4. **Validação prática da Solution A:** instaladas as dependências, treinado o modelo (acurácia 0.7875), servidor subido localmente e testado `POST /api/v1/predict` com um cliente real — resposta gerada pelo Gemini 2.5 Flash de verdade (não fallback) e guardrail de entrada inválida confirmado (HTTP 422). Evidências em `docs/evidence/04-solution-a-validacao.md`.
5. **Desenvolvimento da Solution B (Etapa 4):** implementado o protótipo completo — `train.py` (Random Forest com `class_weight="balanced"`, métricas além de acurácia: precisão/recall/F1/ROC-AUC), `model_wrapper.py`, `shap_tool.py` (ferramenta de explicabilidade local via `shap.TreeExplainer`), `agent_b.py` (orquestra modelo → SHAP → Gemini 2.5 Flash, com fallback) e `app.py`. Treinado (ROC-AUC 0.8388) e validado ponta a ponta localmente, incluindo guardrail de entrada. Evidências em `docs/evidence/04-solution-b-validacao.md`.
6. **Workflow Runbook:** marcados como concluídos os itens de solution-a e solution-b na Etapa 4.

*Nota: o modelo da Solution A foi retreinado do zero, não houve reaproveitamento de artefato de sessão anterior (o `model.joblib` é gerado localmente e ignorado pelo git).*

7. **Correção do `train.py` da Solution A:** adicionada `evaluate_model()` reportando precisão/recall/F1/ROC-AUC (não só acurácia), alinhando com a exigência do `project-context.md` §2. Retreinado: acurácia 0.7875, ROC-AUC 0.8319, recall de 0.52 na classe Churn — bem abaixo do recall de 0.78 da Solution B, que usa `class_weight="balanced"`. Diferença registrada como característica conhecida do baseline, não como bug (`docs/evidence/04-solution-a-validacao.md`).

---

8. **Desenvolvimento da Solution C (Etapa 4):** implementado o pipeline multi-etapa completo — `guardrails.py` (Pydantic com `Literal` nos campos categóricos, rejeitando valores fora de escopo que A/B deixavam passar silenciosamente; `is_valid_llm_output` como guardrail de saída), `fallback.py` (degradação graciosa por zona de confiança), `agent_c.py` (orquestra: prevê → classifica zona de confiança → SHAP → LLM com timeout → guardrail de saída → fallback), reaproveitando `model_wrapper.py`/`shap_tool.py` da Solution B. Treinado e validado ponta a ponta: zona cinzenta (0.45–0.55) testada com sucesso via LLM real; escalonamento de alto risco (>95% + fatura alta) verificado diretamente na lógica de decisão, já que o dataset real não atinge essa faixa de probabilidade; guardrails de entrada testados (campo faltando e categoria fora de escopo, ambos HTTP 422). Evidências em `docs/evidence/04-solution-c-validacao.md`.
9. **Achado real durante a validação:** o timeout inicial sugerido no README da Solution C (2.0s) estourava quase sempre contra a latência real do Gemini 2.5 Flash; ajustado para 8.0s com base em medição empírica. Mesmo assim, duas chamadas reais retornaram `DeadlineExceeded` (504 do lado do Google, não do timeout do cliente) — o fallback determinístico assumiu corretamente nas duas vezes, sem expor erro técnico ao usuário. Evidência genuína (não simulada) do risco "Latência alta / Falha na API do LLM" do `mission-brief.md` §8 sendo mitigado na prática.
10. **Workflow Runbook:** Etapa 4 concluída — as três soluções (A, B, C) têm protótipo mínimo implementado e validado localmente.

---

11. **Etapa 5 do runbook — testes automatizados:** criada uma suíte pytest por solução (`solutions/solution-{a,b,c}/tests/`), não no `tests/` da raiz — decisão deliberada, já que cada solução é um app independente com seu próprio `src/` e `model.joblib`; o `tests/` da raiz (vazio, só `.gitkeep`) ficou parado nesta sessão e foi removido depois, junto com as outras pastas vazias do scaffolding inicial (ver nota de limpeza mais abaixo). 27 testes no total (4 + 5 + 18), todos passando, LLM sempre mockado (`monkeypatch`) para a suíte rodar determinística e rapidamente sem depender de rede/API key. Solution C tem a cobertura mais ampla: guardrail de saída, zona cinzenta, escalonamento de alto risco e a rejeição de categoria fora de escopo (`Contract: "Weekly"`) que A/B não pegam. Evidência em `docs/evidence/05-testes-automatizados.md`.

---

12. **Etapa 6 do runbook — comparação das três soluções:** tabela preenchida em `docs/workflow-runbook.md` (custo, complexidade, qualidade da explicação, riscos, manutenibilidade, adequação ao problema), com base nas métricas reais de treino e nas evidências coletadas nesta e nas sessões anteriores.
13. **Etapa 7 e 8 — decisão final e ADR:** **Solution C escolhida** para seguir para a integração final. Justificativa registrada em `docs/adr/001-escolha-da-solucao.md`: é a única que atende à régua "Reliable" do curso por completo (guardrails de entrada/saída, fallback validado contra uma falha real de API, zona cinzenta, escalonamento humano), sem sacrificar o recall (0.78) e a explicação SHAP local herdados da Solution B. Limitação registrada explicitamente: o threshold de "fatura alta" para escalonamento (`agent_c.py::HIGH_RISK_MONTHLY_CHARGES_THRESHOLD`) ainda não foi validado com o negócio.

---

14. **Etapa 9 — Merge-Readiness Pack:** `docs/merge-readiness-pack.md` preenchido por completo (comparação final, 27 testes, evidências, limitações, riscos, decisões arquiteturais, instruções de execução, checklist).
15. **Etapa 10 (parcial) — painel web:** perguntado ao usuário qual abordagem de frontend usar, já que não estava na stack fixada; escolhida a opção sem dependências novas — HTML/JS estático servido pelo próprio FastAPI via `StaticFiles`. Criado `solutions/solution-c/static/index.html` (formulário com os 19 campos do cliente) e montado em `app.py`. Testado de verdade com Playwright + Chromium headless (não só inspecionado): carregamento do formulário e submissão end-to-end com resultado renderizado — capturas em `docs/evidence/screenshots/`.
16. **Etapa 10 (parcial) — Docker:** `docker/Dockerfile` (Python 3.12 — ajustado depois de o build falhar com 3.11, já que `shap==0.52.0` exige 3.12+), `.dockerignore` e `docker-compose.yml` na raiz. Testado com `docker compose` de verdade: build limpo (métricas de treino idênticas às locais), subida com `GEMINI_API_KEY` real (LLM executando de dentro do container) e subida sem chave (fallback ativado, sem crash) — evidência em `docs/evidence/10-docker-painel.md`. `README.md` criado na raiz (não existia) com instruções de subida em um comando.
17. **Workflow Runbook:** Etapa 9 concluída; Etapa 10 com Docker e painel concluídos, falta só `report.md`.

---

18. **Etapa 10 (final) — `report.md`:** escrito por completo seguindo a estrutura exigida (cabeçalho, definição do problema, arquitetura com diagrama textual, descrição do agente com iterações de prompt e o que não funcionou, avaliação com métricas reais das três soluções, reflexão, impactos e ética, referências). Dois pontos deixados como placeholder explícito, pois só o aluno pode preencher: link de deploy público e vídeo de demonstração (com roteiro sugerido já escrito).

---

19. **Auditoria final de commits vs. tabela do `project-context.md` §7:** todos os 10 itens têm pelo menos um commit correspondente. Dois achados registrados, não corrigidos: (a) commits #1–#4 (mission-brief, agent.md, mentorship-pack/workflow-runbook, solution-a — todos de 04–05/07, anteriores à consolidação em Claude Code) não têm racionalidade no corpo da mensagem, só o título, descumprindo a regra do §7; (b) os itens #9 (merge-readiness pack) e #10 (Docker/painel/report) foram para o mesmo commit (`d6300ae`) em vez de dois separados. Decisão do usuário: deixar como está — reescrever os commits #1–#4 exigiria rebase + force-push de histórico já publicado em `origin/main`, uma operação destrutiva não autorizada. Etapa 10 do Workflow Runbook fechada com essa ressalva registrada.

---

20. **Limpeza de repositório:** removidas todas as pastas que só continham `.gitkeep` (placeholder de scaffolding inicial, nunca usado): `tests/` e `src/agent/`, `src/api/`, `src/model/` na raiz (o projeto evoluiu para manter cada solução autocontida em `solutions/solution-*/src/`, essas pastas na raiz nunca chegaram a ser usadas). `.gitkeep` também removido de `docker/` e `docs/evidence/`, que já têm conteúdo real. `.vscode/` apagado por completo e adicionado ao `.gitignore` (não fazia mais sentido manter um `extensions.json` isolado sem o resto da configuração). Arquivos de `docs/evidence/` renomeados para um esquema consistente, sem data ambígua no nome: `solution-{a,b,c}-validacao-09-07.md` → `04-solution-{a,b,c}-validacao.md` (prefixo = etapa do runbook), `etapa5-testes-automatizados-09-07.md` → `05-testes-automatizados.md`, `etapa10-docker-painel-09-07.md` → `10-docker-painel.md`. Todas as referências cruzadas nos outros documentos (`merge-readiness-pack.md`, ADR-001, `report.md`, `workflow-runbook.md`) atualizadas para os novos caminhos. Árvore de pastas do `project-context.md` §5 atualizada para refletir a estrutura real.

---

21. **Deploy público (`report.md` §Cabeçalho e §Deployment):** Hugging Face Spaces descartado — o usuário confirmou que o SDK Docker exige pagamento na conta usada, ao contrário do que a documentação sugeria (não insisti nisso; busquei confirmação externa, os resultados foram inconsistentes, e priorizei a experiência direta do usuário sobre a busca). Optado por Render: como o dataset não pode ser baixado por uma plataforma de build externa (mesma restrição de licença), o caminho foi build local da imagem (com o modelo já treinado, sem CSV) → push para `ghcr.io/diegocarlito/churn-solution-c` → Render só puxa a imagem pronta. Dockerfile de deploy ajustado para ler a porta de `${PORT:-8000}` (Render injeta via env var). Aplicação no ar em https://churn-solution-c.onrender.com/, validada com chamadas reais pós-deploy: guardrail de entrada (422), sucesso com LLM real e fallback genuíno na mesma bateria de testes. Evidência em `docs/evidence/11-deploy-render.md`.

*Nota sobre credenciais:* o usuário colou um token do GitHub (`write:packages`) diretamente na conversa para o push da imagem. Usado imediatamente, `docker logout` executado logo depois para não deixar a credencial persistida localmente, e o usuário foi orientado a revogar o token no GitHub após o uso.

---

### 3. Planejamento para a Próxima Sessão

- Preencher o último placeholder do `report.md`: vídeo de demonstração (roteiro sugerido já atualizado para usar a URL pública).
- Considerar CI (GitHub Actions rodando pytest) — registrado como próximo passo no `report.md`, não bloqueante para a entrega.