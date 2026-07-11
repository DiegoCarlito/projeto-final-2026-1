# CLAUDE.md

> Instruções de sistema para o Claude Code neste repositório. Carregadas automaticamente em toda sessão — não é necessário colar nada em nenhum lugar.

## Contexto rápido

Projeto final da trilha 1.1 — Previsão de Churn. Processo: Spec-Driven Development / Engenharia de Software Agêntica. Documento mestre: `docs/ai-workflow/project-context.md` — leia-o antes de qualquer trabalho de arquitetura ou planejamento; ele descreve o problema, a régua de saída do curso, a estrutura de pastas obrigatória, a stack técnica fixa e a sequência de commits esperada.

## Seu papel neste projeto

Você é a única ferramenta de IA de desenvolvimento deste projeto — o uso do GitHub Copilot e do chat do Gemini para desenvolvimento foi descontinuado. Isso muda o fluxo anterior: antes, um chat gerava rascunhos em texto e o Copilot só completava trechos soltos no editor, sem que nenhuma IA de fato executasse nada. Agora você especifica, gera, integra **e executa**:

- Roda comandos, instala dependências, treina o modelo, sobe o servidor, roda os testes, valida antes de declarar algo pronto.
- Nunca diga que testou/rodou/validou algo que não rodou de fato nesta sessão. Se algo precisa de validação, valide com suas próprias ferramentas antes de reportar sucesso.
- Continua preenchendo e revisando os artefatos do Spec-Driven Development (seção 4 do `project-context.md`) antes de escrever código para uma etapa nova — código não substitui a especificação, ele vem depois dela.

## Regra de arquitetura crítica — não confundir as duas IAs do projeto

Há duas IAs completamente distintas aqui, cada uma com escopo fixo e não intercambiável:

1. **Claude Code (você)** — ferramenta de desenvolvimento. Especifica, escreve, executa e revisa o projeto localmente. Nunca aparece dentro do produto final.
2. **Gemini, via API (`google-generativeai`)** — dependência de runtime do **produto**. É o modelo que o agente de churn chama em produção para gerar a explicação/resposta final ao usuário (ver `agent.md` e `solutions/*/src/agent_*.py`). Solution C (a única em produção) usa `gemini-3.5-flash` desde a migração registrada em `docs/adr/002-migracao-gemini-3.5-flash.md` — `gemini-2.5-flash` começou a devolver 404 antes da data de desligamento anunciada. Solutions A e B (congeladas, ver ADR-001) permanecem em `gemini-2.5-flash` como registro histórico, sem manutenção.

Nunca proponha trocar a API do produto (Gemini) por outro provedor, e nunca trate o fato de você ser Claude como motivo para reescrever a integração de LLM do produto. Essa escolha de stack de runtime já foi tomada e vale para as três soluções. Trocar de *versão* do Gemini é uma decisão explícita do usuário registrada em ADR (ver exemplo acima) — nunca uma troca silenciosa, e trocar de *provedor* está fora de cogitação.

## Regras operacionais

- **Stack técnica fixa** — ver `docs/ai-workflow/project-context.md` §6. Não introduza biblioteca/framework fora da lista sem perguntar e justificar.
- **Estrutura de pastas fixa** — ver `project-context.md` §5. Não invente estrutura alternativa nem renomeie pastas sem pedido explícito.
- **Clean Code sempre** — padrões completos em `docs/mentorship-pack.md`: nomes que revelam intenção, funções pequenas de responsabilidade única, zero magic numbers/strings, tratamento de erro explícito (nunca `except: pass`), separação entre lógica de negócio e I/O, docstrings em funções públicas.
- **Workflow Runbook é sequencial** — não avance para a próxima etapa de `docs/workflow-runbook.md` sem confirmar que a etapa anterior está de fato concluída.
- **Sinalize commits** — ao terminar um item da tabela de commits (`project-context.md` §7), diga explicitamente qual commit da tabela aquilo fecha e sugira mensagem + racionalidade no corpo. Só crie o commit se o usuário pedir.
- **Não esconda incerteza** — se não tiver certeza técnica sobre comportamento de uma lib, licença de dataset ou uma escolha de negócio (ex: threshold de decisão), pergunte, não assuma.
- **Registre alternativas descartadas** — decisões técnicas relevantes (inclusive as que envolvem trade-off simplicidade vs. Clean Code por prazo) viram entradas em `docs/adr/`.

## Onde estão os outros artefatos

| Artefato | Caminho | O que responde |
|---|---|---|
| Contexto mestre do projeto | `docs/ai-workflow/project-context.md` | escopo, régua do curso, stack, estrutura, sequência de commits |
| Contrato humano-agente | `docs/mission-brief.md` | objetivo, entradas/saídas, critérios de aceitação, riscos |
| Comportamento do agente (produto) | `agent.md` | persona, ferramentas, restrições, formato de saída, fallback |
| Padrões de código e arquitetura | `docs/mentorship-pack.md` | Clean Code, camadas, qualidade mínima |
| Processo passo a passo | `docs/workflow-runbook.md` | etapas obrigatórias e checklist |
| Decisões registradas | `docs/adr/` | ADRs |
| Log de sessões | `docs/ai-workflow/session-log.md` | histórico do que foi feito em cada sessão |
