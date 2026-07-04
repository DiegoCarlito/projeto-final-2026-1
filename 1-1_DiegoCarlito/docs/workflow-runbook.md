# Workflow Runbook

> **Projeto:** Previsão de Churn
> **Aluno(a):** [seu nome]

---

## Processo obrigatório de execução

Siga as etapas abaixo na ordem indicada. Cada etapa deve gerar pelo menos um commit com mensagem descritiva e racionalidade (ver tabela de commits em `project-context.md`, seção 7).

### Etapa 1: Ler o Mission Brief
- [ ] Ler e compreender o mission brief
- [ ] Identificar entradas, saídas e restrições
- [ ] Anotar dúvidas ou ambiguidades

### Etapa 2: Propor três soluções possíveis
- [ ] Descrever solution-a (baseline simples)
- [ ] Descrever solution-b (explicabilidade como ferramenta)
- [ ] Descrever solution-c (fluxo multi-etapa com guardrails)

### Etapa 3: Registrar cada solução em pasta separada
- [ ] Criar `solutions/solution-a/`
- [ ] Criar `solutions/solution-b/`
- [ ] Criar `solutions/solution-c/`

### Etapa 4: Implementar protótipos mínimos
- [ ] Implementar protótipo da solution-a
- [ ] Implementar protótipo da solution-b
- [ ] Implementar protótipo da solution-c

### Etapa 5: Executar testes
- [ ] Criar testes em `tests/`
- [ ] Executar testes para cada solução
- [ ] Registrar resultados em `docs/evidence/`

### Etapa 6: Comparar as soluções

| Critério | Solution A | Solution B | Solution C |
|----------|-----------|-----------|-----------|
| Custo | | | |
| Complexidade | | | |
| Qualidade da explicação | | | |
| Riscos | | | |
| Manutenibilidade | | | |
| Adequação ao problema | | | |

### Etapa 7: Escolher uma solução final
- [ ] Solução escolhida:
- [ ] Justificativa:

### Etapa 8: Registrar a decisão em ADR
- [ ] Criar `docs/adr/001-escolha-da-solucao.md`

### Etapa 9: Gerar o Merge-Readiness Pack
- [ ] Preencher `docs/merge-readiness-pack.md`

### Etapa 10: Empacotar, integrar ao produto e escrever o relatório
- [ ] Docker sobe com um comando
- [ ] API integrada a um produto/painel
- [ ] `report.md` completo
- [ ] Verificar que cada etapa tem pelo menos um commit com racionalidade