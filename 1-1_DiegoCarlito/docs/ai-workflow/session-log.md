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