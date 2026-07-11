# Relatório — Previsão de Churn (Trilha 1.1)

## Cabeçalho

- **Link da aplicação:** https://churn-solution-c.onrender.com/ (Render, free tier — pode levar até ~1min para "acordar" após um período sem uso). Documentação interativa da API: https://churn-solution-c.onrender.com/docs
- **Link do repositório:** https://github.com/DiegoCarlito/projeto-final-2026-1
- **Aluno(a):** Diego Carlito Rodrigues de Souza

---

## Definição do problema

A perda de clientes (churn) corrói diretamente a receita recorrente de uma empresa de
telecomunicações — é mais caro conquistar um cliente novo do que reter um existente.
Modelos de previsão tradicionais respondem só "quem vai cancelar"; a equipe de retenção
precisa saber **por quê**, para escolher a intervenção certa (desconto, upgrade de
suporte, contato de relacionamento) em vez de aplicar a mesma oferta genérica para todo
mundo — e sem gastar margem com clientes que não iam cancelar de qualquer forma.

**Stakeholders:**
- **Equipe de retenção / Customer Success** — usuária direta do painel, decide a ação com base na explicação, não só no número.
- **Gestão de receita** — interessada na taxa de churn evitável e no custo das ofertas de retenção.
- **Cliente final** — afetado pela qualidade da decisão: uma oferta certeira ajuda, uma oferta genérica ou insistente pode incomodar.

**Métrica de negócio:** redução de churn evitável sem inflar o custo de retenção (evitar
oferecer desconto a quem não ia cancelar — falso positivo — e evitar deixar passar quem
ia cancelar — falso negativo).

**Métrica técnica:** o dataset é desbalanceado (a maioria dos clientes não cancela), então
acurácia sozinha esconde o problema real. A solução final usa **recall, precisão, F1 e
ROC-AUC** na classe Churn — recall de 0.78 e ROC-AUC de 0.8388 (ver `docs/evidence/04-solution-b-validacao.md`
e `docs/evidence/04-solution-c-validacao.md`), priorizando não deixar passar clientes
em risco real, mesmo ao custo de mais falsos positivos.

---

## Como o sistema é montado

**Diagrama de arquitetura (Solution C, a solução final — ADR-001):**

```
Cliente (perfil JSON, via painel ou API)
        │
        ▼
Guardrail de entrada (Pydantic + Literal — guardrails.py)
   rejeita tipo errado ou categoria fora do dataset, HTTP 422
        │
        ▼
Modelo tabular (Random Forest — model_wrapper.py) ──► probabilidade de churn
        │
        ▼
Classificação de zona de confiança (agent_c.py)
   padrão · zona cinzenta (0.45–0.55) · escalonamento (>95% + fatura alta)
        │
        ▼
ShapExplainer (shap_tool.py) ──► top 3 fatores de risco REAIS daquele cliente
        │
        ▼
Agente monta o prompt (probabilidade + fatores SHAP + instrução por zona)
        │
        ▼
Gemini 3.5 Flash (timeout 20s) ──► JSON com explicação em linguagem de negócio
        │
        ├── sucesso + guardrail de saída aprova ──► resposta final (+ escalonamento humano se aplicável)
        │
        └── falha (timeout / erro de API / JSON inválido) ──► fallback determinístico por zona
        │
        ▼
API FastAPI (POST /api/v1/predict) ──► Painel web estático (static/index.html)
```

**Agent/model exploration:** três abordagens foram implementadas e comparadas antes da
escolha (`docs/adr/001-escolha-da-solucao.md`):
- **Solution A** — Regressão Logística + LLM formatando coeficientes **globais** do modelo (baseline).
- **Solution B** — Random Forest + SHAP **local** como ferramenta consultada pelo agente antes de acionar o LLM.
- **Solution C** — B + guardrails de entrada/saída, zona cinzenta, escalonamento humano e fallback determinístico — **escolhida** por ser a única que atende à régua "Reliable" do curso por completo.

**Deployment:** empacotado em Docker (`docker/Dockerfile`, imagem `python:3.12-slim`). O
dataset não é redistribuído no repositório por restrição de licença do Kaggle
(`data/DATA_CARD.md`), então o build espera o CSV já baixado localmente e treina o modelo
**durante o build** — a imagem final já sobe com `model.joblib` pronto, sem depender de
volume montado em runtime. `docker-compose.yml` sobe tudo com um comando
(`GEMINI_API_KEY=sua_chave docker compose up --build`); sem a chave, o sistema ainda sobe
e responde em modo de fallback. O mesmo processo FastAPI expõe a API (`/api/v1/predict`) e
o painel estático (`/`, via `StaticFiles`) — um único serviço, uma única porta.

**Deploy público:** Render (free tier). Como o dataset não pode ser baixado por uma
plataforma de CI/build externa (mesma restrição de licença), o caminho até o deploy
público é diferente do local: a imagem é **buildada localmente** (onde o CSV existe),
publicada no GitHub Container Registry (`ghcr.io/diegocarlito/churn-solution-c`) e o
Render só faz *pull* dessa imagem já pronta — não tenta clonar o repositório nem treinar
nada. A porta é lida da variável `PORT` injetada pelo Render (`agent_c.py`/`app.py` não
mudam; só o `CMD` do Dockerfile de deploy usa `${PORT:-8000}` em vez de uma porta fixa).
Validado com chamadas reais pós-deploy: guardrail de entrada (HTTP 422 para categoria fora
de escopo), resposta com LLM real (`llm_executed: true`) e fallback genuíno em outra
chamada da mesma bateria — mesma variabilidade de latência já documentada localmente.
Detalhes em `docs/evidence/11-deploy-render.md`.

**CI/CD:** não há pipeline de integração contínua configurado nesta entrega (ex: GitHub
Actions rodando os testes a cada push) — os 27 testes automatizados rodam localmente via
`pytest`. Registrado como próximo passo na seção de Reflexão.

**Estratégia de confiabilidade:** guardrail de entrada rejeita payload inválido antes de
qualquer cálculo; timeout de 20s protege contra travamento na chamada ao LLM; guardrail de
saída rejeita JSON malformado ou fora do intervalo esperado; fallback determinístico
específico por zona de confiança garante que o usuário sempre recebe uma resposta útil,
nunca um erro técnico cru. Essa estratégia foi validada não só em teoria, mas contra uma
falha **real** da API do Gemini durante esta sessão (`DeadlineExceeded`, 504 do lado do
Google) — o fallback assumiu corretamente, dentro e fora do container Docker
(`docs/evidence/04-solution-c-validacao.md`, `docs/evidence/10-docker-painel.md`).

---

## Descrição do agente

**Modelo base e ferramentas:**
- **Modelo tabular:** Random Forest (`scikit-learn`), `class_weight="balanced"` para compensar o desbalanceamento de classes — recall 0.78 na classe Churn, ROC-AUC 0.8388, contra recall 0.52 do baseline linear (Solution A) sem esse ajuste.
- **Explicabilidade:** SHAP (`shap.TreeExplainer`) — contribuição matemática **local**, exata, de cada variável para o score daquele cliente específico, não coeficientes globais do modelo inteiro.
- **LLM:** Gemini 3.5 Flash via API (`google-generativeai`) — gratuito no free tier para o volume desta entrega. Migrado de `gemini-2.5-flash` em 11/07/2026 depois que esse modelo passou a devolver 404 em produção antes da data de desligamento oficialmente anunciada (`docs/adr/002-migracao-gemini-3.5-flash.md`). O LLM nunca decide os fatores de risco; só traduz os valores SHAP (já calculados matematicamente) para linguagem de negócio, reduzindo o risco de alucinação.

**Dados e contexto:** Telco Customer Churn (Kaggle/IBM), ~7.043 clientes, 21 colunas,
dados fictícios de uma empresa de telecom fictícia. Licença Kaggle vaga sobre termos de
redistribuição → o arquivo bruto não é versionado no repositório, só o `data/DATA_CARD.md`
público com origem, licença, como obter e vieses conhecidos (dados sintéticos, snapshot
único, sem geografia real).

**Guardrails:**
- **Entrada** (`guardrails.py::CustomerPayload`): schema Pydantic com `Literal` nos campos categóricos — rejeita não só tipo errado, mas também valores fora do escopo conhecido do dataset (ex: `Contract: "Weekly"` → HTTP 422). Diferença real em relação às Solutions A/B, que aceitam qualquer string e deixam o `OneHotEncoder` ignorar em silêncio.
- **Saída** (`guardrails.py::is_valid_llm_output`): rejeita JSON sem as três chaves esperadas, `churn_probability` fora de `[0, 1]`, lista de fatores vazia ou ação recomendada vazia — sinal de alucinação ou formato quebrado, aciona o fallback automaticamente.

**Iterações de prompt e design — o que não funcionou também conta:**
- Solution A usava só coeficientes globais no prompt → explicação plausível mas não necessariamente fiel àquele cliente específico.
- O timeout inicial do LLM na Solution C (2.0s, sugestão do próprio README de planejamento) **estourava quase sempre** contra a latência real do Gemini 2.5 Flash (uma chamada simples já leva ~1.5s); foi ajustado para 8.0s após medição empírica — e mesmo assim, duas chamadas reais na mesma sessão retornaram `DeadlineExceeded` (falha real do lado do Google), confirmando que o fallback não é um exercício teórico.
- Tentei validar a regra de escalonamento de alto risco (probabilidade > 95% + fatura alta) via uma requisição HTTP real, mas nenhum cliente do dataset atinge essa probabilidade com o modelo treinado (máximo observado: ~0.926) — resolvido testando a lógica de decisão diretamente (testes unitários em `test_solution_c.py`), não escondendo a limitação.
- O guardrail de saída só foi adicionado na Solution C depois de perceber, comparando com A/B, que nenhuma das duas primeiras protegia contra o LLM devolver algo malformado.
- **11/07/2026 — migração para gemini-3.5-flash (`docs/adr/002-migracao-gemini-3.5-flash.md`):** em produção, `gemini-2.5-flash` passou a devolver 404 "no longer available" (confirmado como indisponibilidade ampla do lado do Google, não restrição de conta nova). A migração para `gemini-3.5-flash` expôs dois problemas que o modelo anterior mascarava por sorte: (1) a latência real subiu para ~12s-16s por chamada completa, exigindo novo ajuste de timeout (8.0s → 20.0s); (2) o prompt pedia `"churn_probability"` como "float numérico" sem fixar a escala, e o `gemini-2.5-flash` inferia corretamente a escala decimal (0-1) enquanto o `gemini-3.5-flash` ecoava o valor no mesmo formato percentual mostrado no prompt (`46.06` em vez de `0.4606`) — reprovado corretamente pelo guardrail de saída, mas o LLM nunca teria sucesso sem tornar a instrução explícita. Evidência de que o guardrail de saída generaliza para falhas não previstas originalmente, mesmo trocando o modelo.

---

## Avaliação do sistema

**Performance (conjunto de teste, 20% hold-out, `random_state=42`):**

| Solução | Modelo | Acurácia | ROC-AUC | Recall (Churn) | Precisão (Churn) |
|---|---|---|---|---|---|
| A | Regressão Logística | 0.7875 | 0.8319 | 0.52 | 0.62 |
| B / C | Random Forest (`class_weight="balanced"`) | 0.7477 | 0.8388 | 0.78 | 0.52 |

A solução final (C) troca alguma precisão por recall — deliberado, dado que o custo de
negócio de **não perceber** um cliente em risco (falso negativo) tende a ser maior que o
custo de uma oferta de retenção desnecessária (falso positivo).

**Testes automatizados:** 27 testes (pytest), 0 falhas — guardrails de entrada/saída,
fluxo de sucesso com LLM, fallback, zona cinzenta e escalonamento
(`docs/evidence/05-testes-automatizados.md`).

**Latência observada:** uma chamada simples ao Gemini 2.5 Flash leva ~1.5s; com o prompt
completo (dados do cliente + fatores SHAP + geração de JSON), a latência varia o
suficiente para que, mesmo com timeout de 8s, algumas chamadas reais tenham estourado
(`DeadlineExceeded`) durante a validação desta sessão — taxa de fallback não medida
estatisticamente (poucas chamadas manuais/de teste), mas observada em pelo menos 2 de
~6 chamadas reais feitas nesta sessão. Sinaliza que a latência do LLM merece monitoramento
contínuo em produção, não só calibração pontual. **Atualização pós-migração (11/07/2026,
`docs/adr/002-migracao-gemini-3.5-flash.md`):** com `gemini-3.5-flash`, 3 chamadas reais
consecutivas com o prompt completo levaram 11.7s-15.6s cada — mais lento que o modelo
anterior, daí o timeout ter subido para 20s.

**Custo por chamada:** Gemini 3.5 Flash no free tier (família Flash segue com acesso
gratuito no Google AI Studio) — custo efetivo de $0 nesta entrega acadêmica, mesma
condição que valia para o `gemini-2.5-flash` usado até a migração de 11/07/2026. O modelo
tabular roda localmente (custo de inferência desprezível).

**UX:** painel web simples (`solutions/solution-c/static/index.html`) com formulário
único para os 19 campos do cliente, resultado mostrado com badges de zona de confiança e
de execução do LLM (deixa claro para quem usa se a explicação veio do Gemini ou do
fallback), fatores de risco em lista e ação recomendada destacada. Erros (guardrail de
entrada, serviço indisponível, falha de conexão) sempre mostram uma mensagem em português
amigável, nunca um stack trace — testado manualmente com Playwright
(`docs/evidence/10-docker-painel.md`).

---

## Demonstração

_[PENDENTE — link do vídeo. Roteiro sugerido, agora usando a aplicação já no ar: (1) abrir https://churn-solution-c.onrender.com/ (avisar que o free tier pode levar ~1min pra acordar) e mostrar o formulário; (2) preencher um cliente de alto risco (contrato mensal, fibra óptica, tenure baixo) e mostrar a explicação real do Gemini 3.5 Flash; (3) preencher um cliente de zona cinzenta (ex: os valores em `docs/evidence/04-solution-c-validacao.md` §3) e mostrar a ação exploratória leve; (4) tentar um payload com categoria fora de escopo (`Contract` inválido, testável em `/docs`) e mostrar o HTTP 422; (5) opcional: mostrar `docs/evidence/04-solution-c-validacao.md` §4 e `docs/evidence/11-deploy-render.md` como prova de fallback ativado por falhas reais da API, tanto local quanto em produção.]_

---

## Reflexão sobre o que aprenderam

**O que funcionou:**
- Ancorar a explicação do LLM em valores SHAP locais (em vez de coeficientes globais ou texto livre) reduz o risco de alucinação de forma concreta e testável.
- O fallback determinístico por zona de confiança não é só uma rede de segurança teórica — foi exercitado por uma falha real da API do Gemini durante a própria validação desta entrega, o que aumenta a confiança de que funciona em produção.
- Comparar três soluções de complexidade crescente (A → B → C) tornou o custo de cada camada de confiabilidade explícito e mensurável, em vez de "adicionar guardrails porque sim".

**O que não funcionou como planejado:**
- O timeout inicial de 2s era otimista demais e precisou de calibração empírica.
- A Solution A, por design, tem recall baixo (0.52) na classe que mais importa — uma limitação intencional do baseline mais simples, não um bug, mas que reforça por que a solução final precisava de um modelo diferente.
- O threshold de "fatura alta" para escalonamento humano (`agent_c.py::HIGH_RISK_MONTHLY_CHARGES_THRESHOLD = 100.0`) é um placeholder — não há dado de negócio real nesta entrega acadêmica para validá-lo.
- Não há CI configurado; os testes só rodam quando alguém lembra de rodar localmente.

**Próximos passos com mais tempo:**
- Configurar CI (ex: GitHub Actions) rodando os 27 testes a cada push, e um linter (`black`/`ruff`, já na stack) como gate.
- Validar o threshold de escalonamento com dados de negócio reais.
- Monitorar latência, custo por chamada e taxa de fallback em produção real (não só em testes manuais), com alertas se a taxa de fallback subir de forma anormal.
- Auditoria de viés entre grupos demográficos (ver seção seguinte) antes de qualquer uso além do escopo acadêmico.

---

## Impactos e ética

**Quem pode ser prejudicado por um erro do sistema:** um falso positivo (sugerir oferta de
retenção para quem não ia cancelar) custa margem à empresa; um falso negativo (não
sinalizar um cliente que de fato cancela) custa a receita do cliente perdido e, pior,
significa que ninguém tentou reter essa pessoa. Como o modelo prioriza recall sobre
precisão, o sistema tende a errar mais para o lado de "oferecer retenção demais" do que
"deixar passar quem ia cancelar" — uma escolha deliberada, mas que tem custo real de
margem se levada para produção sem ajuste fino do threshold de decisão.

**Viés entre grupos:** o modelo **não foi auditado** por fairness entre grupos
demográficos (gênero, idoso, presença de dependentes) nesta entrega — é uma limitação
real, não uma garantia de neutralidade. Antes de qualquer uso além do escopo acadêmico,
seria necessário verificar se o recall/precisão do modelo é consistente entre esses
grupos, para não sistematicamente sub-atender um grupo específico com ofertas de retenção.

**Privacidade:** o dataset usado é fictício — clientes e empresa inventados
(`data/DATA_CARD.md`) — então não há exposição de dados reais de pessoas nesta entrega.
Um sistema real equivalente usaria dados de clientes de verdade; nesse cenário, o payload
de entrada (perfil completo do cliente) não deveria ser logado sem anonimização, e o
acesso ao painel/API precisaria de autenticação — nenhuma das duas coisas está implementada
aqui, por estarem fora do escopo desta disciplina.

---

## Referências

1. Kaggle — Telco Customer Churn (IBM): https://www.kaggle.com/datasets/blastchar/telco-customer-churn
2. Google — Gemini API / `google-generativeai` SDK: https://ai.google.dev/gemini-api/docs
3. Lundberg, S. & Lee, S. — *A Unified Approach to Interpreting Model Predictions* (SHAP): https://github.com/shap/shap
4. FastAPI — documentação oficial: https://fastapi.tiangolo.com/
5. `docs/adr/001-escolha-da-solucao.md`, `docs/adr/002-migracao-gemini-3.5-flash.md`, `docs/merge-readiness-pack.md` e `docs/evidence/` — evidências e decisões internas deste projeto
