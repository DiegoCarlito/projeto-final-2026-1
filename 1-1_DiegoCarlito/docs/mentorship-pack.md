# Mentorship Pack

> **Projeto:** Previsão de Churn
> **Aluno(a):** Diego Carlito Rodrigues de Souza

---

## 1. Orientações de julgamento

- O agente deve sempre focar na utilidade do dado gerado: precisão estatística não basta; a explicabilidade é o que torna o produto valioso.
- Prefira a simplicidade radical. Se um modelo linear resolver o problema de forma aceitável, não escale para Redes Neurais.
- A segurança e previsibilidade vêm antes da criatividade. O agente atua em domínio corporativo fechado.

---

## 2. Padrões de arquitetura

- Padrão estrutural em camadas: `API (Rotas HTTP) -> Orquestrador do Agente -> Ferramentas (Modelos / LLM)`.
- Fallbacks implementados e testados para serviços externos (LLMs).
- Containerização obrigatória desde as etapas iniciais (Docker).

---

## 3. Padrões de código

- **Linguagem:** Python 3.11+
- **Nomes Intencionais:** Variáveis e funções devem revelar intenção (ex: `calcular_probabilidade_churn`).
- **Responsabilidade Única:** Funções pequenas. Validar, prever e formatar são funções distintas.
- **Sem Magic Numbers/Strings:** Limiares e chaves devem ser constantes (`config.py`).
- **Tratamento de Erros:** Explícito. Sem `except: pass`. Capturar, tratar ou repassar graciosamente.
- **Testabilidade:** Lógica isolada de I/O.
- **Docstrings:** Presentes nas funções públicas, descrevendo propósito, parâmetros e retorno.

---

## 4. Estilo de documentação

- Decisões de design devem ser registradas na pasta `docs/adr/`.
- O histórico de commits (Corpo da Mensagem) deve documentar a racionalidade técnica daquela etapa.

---

## 5. Qualidade esperada

- Nenhuma rota da API deve vazar stack traces para o usuário final.
- Cobertura de testes garantindo o fluxo crítico: entrada válida, entrada inválida (guardrail) e indisponibilidade do serviço externo (fallback).

---

## 6. Exemplos de boas respostas

```json
{
  "churn_probability": 0.85,
  "risk_factors": ["Contrato mensal e ausência de suporte aumentam o risco."],
  "recommended_action": "Oferecer 10% de desconto no plano anual."
}

```

---

## 7. Exemplos de más respostas

```json
{
  "churn_probability": "Alto", 
  "risk_factors": "Coeficiente X foi 0.4 e feature_2 é falsa.",
  "recommended_action": "Retreinar o modelo."
}
// Motivo: Tipagem errada (float esperado), vazamento de jargão técnico (coeficientes), ação fora do domínio da equipe de negócios.

```

---

## 8. Princípios-guia

```
O agente deve sempre explicar a decisão técnica antes de implementar.
O agente deve preferir soluções simples, testáveis e observáveis.
O agente não deve esconder incertezas.
O agente deve registrar alternativas descartadas.

```