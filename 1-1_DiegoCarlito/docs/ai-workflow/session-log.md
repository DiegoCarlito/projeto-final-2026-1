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

### 2. Planejamento para a Próxima Sessão (06/07)

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

*Nota: nenhuma regra de arquitetura do produto (modelo tabular, SHAP, Gemini 2.5 Flash, guardrails, fallback) foi alterada nesta sessão — apenas o fluxo de ferramentas de desenvolvimento.*