# Evidência — Deploy público no Render (09/07/2026)

> Aplicação no ar: https://churn-solution-c.onrender.com/ (painel) ·
> https://churn-solution-c.onrender.com/docs (documentação interativa da API)

## 1. Por que o caminho de deploy é diferente do Docker local

O `docker/Dockerfile` do repositório principal treina o modelo **durante o build**,
esperando `data/telco_churn.csv` já baixado localmente — funciona bem para
`docker compose up --build` na máquina de quem já seguiu `data/DATA_CARD.md`, mas não
funciona para uma plataforma de deploy que clona o repositório do GitHub direto: o CSV
não está lá (não pode ser redistribuído, restrição de licença do Kaggle) e o build
quebraria na etapa de treino.

Testadas duas alternativas gratuitas antes de chegar nesta:
- **Hugging Face Spaces (SDK Docker):** descartado — confirmado pelo usuário que exige
  pagamento na conta usada, ao contrário do que a documentação pública sugeria.
- **Render, build direto do Dockerfile do repositório:** mesmo problema do CSV ausente.

**Solução adotada:** build local (onde o CSV existe) → imagem publicada no GitHub
Container Registry → Render só faz *pull* da imagem já pronta, sem tentar clonar nem
treinar nada.

## 2. Imagem de deploy

Pasta separada (fora do repositório git principal, para não misturar o artefato
`model.joblib` — apropriado *aqui*, mas não no repositório acadêmico — com o código
versionado): réplica do `src/` e `static/` da Solution C, mas com `src/model.joblib` já
treinado copiado diretamente (sem `train.py`, sem dataset). Único ajuste no Dockerfile em
relação ao `docker/Dockerfile` principal: a porta é lida de `${PORT:-8000}` em vez de fixa,
porque o Render injeta a porta via variável de ambiente `PORT`.

```
$ docker build -t ghcr.io/diegocarlito/churn-solution-c:latest .
$ docker push ghcr.io/diegocarlito/churn-solution-c:latest
latest: digest: sha256:90ab18f0bba041d8fcbf843164b13e34c01d0cdd2576cafe7b86e46e707ae65c
```

Testado localmente antes do push, simulando a variável `PORT` do Render:

```
$ docker run -e PORT=10000 -e GEMINI_API_KEY=... ghcr.io/diegocarlito/churn-solution-c:latest
INFO:     Uvicorn running on http://0.0.0.0:10000
```
Painel (`HTTP 200`) e `POST /api/v1/predict` (`HTTP 200`) confirmados antes de publicar.

## 3. Configuração no Render

- New → Web Service → "Deploy an existing image from a registry"
- Image: `ghcr.io/diegocarlito/churn-solution-c:latest`
- Instance Type: Free
- Environment: `GEMINI_API_KEY` configurada diretamente no dashboard do Render (nunca
  passada por chat nem commitada em lugar nenhum)

## 4. Validação pós-deploy (chamadas reais contra a URL pública)

**Painel:**
```
GET https://churn-solution-c.onrender.com/  → HTTP 200
GET https://churn-solution-c.onrender.com/docs → HTTP 200
```

**Guardrail de entrada** (categoria fora de escopo, `Contract: "Weekly"`):
```
HTTP 422 — "Input should be 'Month-to-month', 'One year' or 'Two year'"
```

**Zona cinzenta, três tentativas seguidas com o mesmo cliente** — mostra tanto o caminho
de sucesso quanto o fallback acontecendo de verdade em produção, mesma variabilidade de
latência já observada localmente (`docs/evidence/04-solution-c-validacao.md`):
```
tentativa 1 → llm_executed: True  | zone: gray_zone
tentativa 2 → llm_executed: False | zone: gray_zone   (fallback ativado)
tentativa 3 → llm_executed: True  | zone: gray_zone
```

## 5. Limitações do deploy

- Free tier do Render "dorme" após um período de inatividade — primeiro acesso depois
  disso pode levar até ~1 minuto para responder (irrelevante para o teste automatizado,
  mas relevante para quem for gravar o vídeo de demonstração: recomendo abrir a URL uma
  vez antes de começar a gravar).
- A imagem publicada em `ghcr.io/diegocarlito/churn-solution-c` não é atualizada
  automaticamente a partir do GitHub — qualquer mudança na Solution C exige repetir o
  build + push manualmente. Não configurado CI/CD para isso nesta entrega (mesma
  limitação já registrada no `report.md`, seção CI/CD).

## 6. Rebuild pós-migração para gemini-3.5-flash (11/07/2026)

Essa limitação (imagem não atualiza sozinha) se confirmou na prática: o push do código
para o GitHub (`docs/adr/002-migracao-gemini-3.5-flash.md`) não bastou — o painel em
produção continuou mostrando "Gemini 2.5 Flash" mesmo após um redeploy manual no Render,
porque o Render só faz *pull* da imagem em `ghcr.io/diegocarlito/churn-solution-c:latest`,
sem rebuildar nada. Repetido o processo da seção 2 (build local + push):

```
$ docker build -t ghcr.io/diegocarlito/churn-solution-c:latest .
$ docker push ghcr.io/diegocarlito/churn-solution-c:latest
latest: digest: sha256:6ce9acafc287fb197adb3c22f07284989723663163c1d5638e1e33ed154d1201
```

Testado localmente antes do push (`docker run -e PORT=10000 ...`) — painel já mostrando
"Gemini 3.5 Flash", `GET /` e `GET /docs` retornando `HTTP 200`. Após este push, é
necessário disparar **"Deploy latest commit"** (ou equivalente) no dashboard do Render —
um "Redeploy" de um deploy antigo no histórico reutiliza a imagem antiga e não resolve.
