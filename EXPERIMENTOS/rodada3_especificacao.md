# Rodada 3: comparações entre pares de alternativas

Status: **executada** no ENEM 2025 em 2026-09-25 (redação aprovada antes da execução). O congelamento do teste de 2024 fica suspenso até a conclusão desta rodada.

## 1. Motivação

- Na rodada 1, avaliando cada alternativa **isoladamente**, o Jev reduziu quase todas as perguntas a um juízo único de "quão correta a alternativa parece" (correlações de 0,75 a 0,98 entre perguntas). O ponto fraco é a **ordenação dos distratores** (Spearman entre distratores ≈ 0,35).
- Numa comparação **direta entre dois distratores**, nenhum dos dois é o correto, e a pergunta "qual deles mais participantes escolheriam?" pode exigir uma distinção mais fina.
- **Base teórica:** o modelo de escolha de Luce (1959). Se a razão entre as probabilidades de duas alternativas não depende das demais, a distribuição das 5 alternativas pode ser reconstruída a partir das comparações entre pares. Love (1997) e Revuelta (2005) analisam o item decompondo-o em pares (a correta contra cada distrator); o modelo de **Bradley-Terry** estima uma "força" por alternativa a partir dos pares. Lee et al. (2025) e Scarlatos et al. (2024) usam ranqueadores de pares de distratores (acurácia de 66% a 68%; especialistas humanos, 72%).

## 2. Desenho

| Elemento | Decisão |
|---|---|
| Modelo, `state`, idioma | Iguais às rodadas 1 e 2 |
| Dados | Só **2025** |
| Perguntas | Uma pergunta **Choice** para cada par **ordenado** de alternativas: 10 pares × 2 ordens = **20 perguntas** por item, numa requisição. IDs `par_A_B` (A apresentada primeiro), `par_B_A` etc. |
| Por que as duas ordens | O *JEV-as-a-Judge* (Li et al., 2026) mostra que inverter a ordem muda de 3% a 11% das decisões do Jev; as duas respostas são combinadas |

### A pergunta (exemplo para o par A, B, com A primeiro)

```json
{
  "type": "choice",
  "instructions": {
    "pergunta": "Entre a alternativa em `alternativas.A` e a alternativa em `alternativas.B`, qual delas seria escolhida por mais participantes do ENEM ao responder esta questão?",
    "foco": "Considere participantes reais do ENEM, com níveis variados de preparo, lendo a questão inteira em condições de prova. Compare apenas essas duas alternativas."
  },
  "criteria": {
    "A": "A alternativa em `alternativas.A` seria escolhida por mais participantes.",
    "B": "A alternativa em `alternativas.B` seria escolhida por mais participantes."
  }
}
```

Na ordem inversa (`par_B_A`), a pergunta cita B primeiro e as opções aparecem na ordem B, A. A formulação segue a da q1b ("quantos participantes escolheriam"), a melhor pergunta da rodada 1.

## 3. Agregação (definida antes de rodar)

1. **Combinar as ordens.** Para o par {i, j}: p_ij = ½ · [P(i | ordem i, j) + P(i | ordem j, i)].
2. **Bradley-Terry com resultados suaves.** Para cada item, as forças θ_A…θ_E maximizam Σ_{i<j} [p_ij · log σ(θ_i − θ_j) + (1 − p_ij) · log σ(θ_j − θ_i)], com Σθ = 0 e penalidade ridge λ = 0,01 (necessária porque o Jev devolve probabilidades 0 ou 1, o que levaria as forças ao infinito). Esse passo **não usa as respostas dos participantes**.
3. **Previsão:** p_k = softmax(β · θ_k), com β ajustado por validação cruzada, como a temperatura da q1b.

**Variantes** (também definidas antes):
- **Borda suave:** s_k = Σ_j p_kj (número esperado de "vitórias", de 0 a 4), com softmax e β ajustado. É mais simples e serve de verificação.
- **q1b + pares:** logit condicional com as duas variáveis (q1b e θ).

## 4. Análise e regra de decisão (definidas antes de rodar)

Mesmas 5 dobras agrupadas das rodadas anteriores.

**Diagnósticos:**
- **Consistência de ordem:** proporção de pares em que a alternativa preferida é a mesma nas duas ordens.
- **Acurácia por par:** proporção de pares em que a alternativa preferida pelo Jev foi de fato a mais escolhida. É reportada separadamente para **pares só de distratores** e para **pares com a correta**, e também só para pares cuja diferença real passa de 10 pontos percentuais (como em Scarlatos et al.).

**Regra de decisão:**
- Uma variante de pares (ou a combinação q1b + pares) **substitui a q1b como método principal** somente se o IC 95% (bootstrap pareado por grupos, 5.000 reamostragens) da diferença de Brier em relação à q1b estiver **inteiramente abaixo de zero**.
- Caso contrário, a **q1b continua como método principal** e a variante de pares com melhor Brier entra no congelamento como **método secundário descritivo**.

## 5. Pendências

- [ ] Revisar a redação da pergunta.
