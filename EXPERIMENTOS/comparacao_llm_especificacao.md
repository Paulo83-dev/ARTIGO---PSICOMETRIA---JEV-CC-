# Comparação com um LLM generativo

Status: **executada em 2025** (2026-09-25); parâmetros do LLM congelados em `congelamento_llm_2024.json`.

**Natureza desta análise:** comparação **acrescentada depois** do teste principal de 2024. Ela não altera as hipóteses H1 a H4 nem seus resultados. Segue o mesmo protocolo: todos os parâmetros do LLM são ajustados **só em 2025**, congelados e aplicados **uma única vez** a 2024.

## 1. Pergunta

O desempenho obtido com o Jev poderia ser alcançado por um LLM generativo comum? E, se sim, a vantagem vem do **modelo** ou do **método de perguntar**?

## 2. Modelo e chamada

| Elemento | Decisão |
|---|---|
| Modelo | `z-ai/glm-5.3-flash` (Z.ai), via OpenRouter |
| Provedor | **Together**, fixo, sem alternativa (`allow_fallbacks: false`, `require_parameters: true`). Escolhido por devolver as 20 probabilidades de tokens mais altas (outros provedores devolvem 5 ou nenhuma) |
| Geração | `temperature: 0`, `top_logprobs: 20` (o provedor não aceita `seed`) |
| Raciocínio | O modelo não permite desligá-lo (`effort: "none"` e `enabled: false` são recusados; com `"minimal"` ele ainda raciocina). Usa-se `reasoning.effort: "low"`. O número de tokens de raciocínio de cada chamada é registrado e reportado |
| Limite de saída | `max_tokens: 4000`. Na primeira execução em 2025 o limite era 1.000, e 4 chamadas (de 3.420) esgotaram o limite raciocinando, sem resposta; só essas 4 foram reenviadas com 4.000. Com `temperature: 0`, o limite só afeta chamadas que seriam cortadas |
| Conteúdo enviado | O mesmo objeto `entrada` do Jev, formatado como texto: texto de apoio (se houver), texto principal e alternativas A–E. Sem gabarito |
| Registro | Corpo exato de cada chamada, SHA-256, provedor que respondeu, resposta bruta, tokens e custo |

## 3. Método A: probabilidades das letras (padrão da literatura)

Adaptação de Säuberli et al. (2025) a 5 alternativas.

- **Instrução (sistema):** "Responda à questão de múltipla escolha com apenas uma letra (A, B, C, D ou E), sem explicação."
- **5 rotações cíclicas** das alternativas, para neutralizar o viés de posição: na rotação r, a alternativa que ocupa cada posição é deslocada r casas.
- Em cada rotação, as probabilidades das 5 letras vêm do **primeiro token da resposta** que seja uma letra de A a E. Letra ausente entre as 20 mais prováveis recebe a menor probabilidade devolvida naquela posição (limite superior conservador). As 5 probabilidades são renormalizadas.
- **Temperatura:** em cada rotação, p ∝ exp(log p / T); as probabilidades são realinhadas às alternativas originais e é feita a média das 5 rotações. T é ajustado em 2025 (validação cruzada nas mesmas 5 dobras).

Chamadas: 5 por item.

## 4. Método B: as mesmas perguntas feitas ao Jev

O LLM recebe **a mesma redação** da q1b e das comparações entre pares, e as probabilidades dos tokens fazem o papel das probabilidades do Jev.

- **q1b:** uma chamada por alternativa. A instrução reproduz a pergunta, o foco e os 5 níveis da q1b (situação e sinais), numerados de 0 a 4, e pede "Responda apenas com o número do nível". O escore é a **média dos níveis ponderada pelas probabilidades** dos dígitos 0 a 4 (renormalizadas), como o `score` do Jev.
- **Pares:** uma chamada por par ordenado (20), com a mesma pergunta da rodada 3, pedindo "Responda apenas com a letra da alternativa escolhida". A probabilidade de cada opção vem dos tokens das duas letras, renormalizados.
- **Agregação:** idêntica à do Jev: média das duas ordens, Bradley-Terry com λ = 0,01, e combinação q1b + pares por logit condicional, com parâmetros próprios do LLM ajustados em 2025.

Chamadas: 25 por item.

## 5. Custo estimado

30 chamadas por item × 234 itens ≈ 7.000 chamadas de cerca de 350 a 450 tokens de entrada: por volta de 3 milhões de tokens, **menos de US$ 1** no total (US$ 0,15 por milhão de tokens de entrada no Together). O custo real e o tempo por item são registrados e reportados.

## 5a. Observação da execução em 2025 (antes do congelamento)

Em cerca de 20% das chamadas o modelo raciocinou antes de responder (mediana de 41 a 77 tokens de raciocínio, conforme o método), sobretudo em itens de MT e CN. Quando raciocina, as probabilidades da resposta ficam concentradas numa única opção (na q1b, a probabilidade máxima média passa de 0,58 para 0,98). Esse comportamento é do próprio modelo e não pode ser desligado; ele é mantido e reportado, porque faz parte do que se compara.

## 6. Análise

**Em 2025 (desenvolvimento):** validação cruzada nas mesmas 5 dobras, só para ajustar as temperaturas e os pesos do LLM. Nenhuma escolha de método é feita: os métodos A e B e suas agregações estão fixados acima.

**Congelamento:** os parâmetros do LLM ajustados em todo o 2025 são registrados num arquivo próprio, commitado e enviado antes de qualquer chamada com 2024.

**Em 2024 (comparações, com IC 95% por bootstrap pareado por grupos, como no teste principal):**

| Id | Comparação |
|---|---|
| C1 | Jev q1b + pares × LLM, método A (letras) |
| C2 | Jev q1b + pares × LLM, método B (q1b + pares) |
| C3 | Jev q1b × LLM q1b (método B) |
| C4 | LLM método A × Oracle (como em Säuberli et al.) |

Métricas: as mesmas do teste principal (Brier, métricas de distratores, principal distrator, AUC), a acurácia das comparações entre pares, e o **custo e o tempo** por item de cada modelo.

## 7. Pendências

- [ ] Revisar o desenho.
