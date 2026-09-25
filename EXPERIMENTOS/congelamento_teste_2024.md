# Congelamento da configuração para o teste no ENEM 2024

**Data do congelamento:** 25 de setembro de 2026.
**Prova do momento do congelamento:** o commit que adiciona este arquivo ao repositório no GitHub, com a sua data. Nenhuma chamada ao Jev com itens de 2024 foi feita antes desse commit.

Os parâmetros exatos, em formato lido pelo código, estão em `congelamento_teste_2024.json`. O teste é aplicado pelo script `scripts/avaliar_teste.py`, que não ajusta nada: só lê o congelamento, confere as requisições e calcula as métricas e as hipóteses.

## 1. Como a configuração foi escolhida

Todas as escolhas foram feitas **exclusivamente com os 114 itens do ENEM 2025**, com validação cruzada em 5 dobras agrupadas:

- **Rodada 1** (`rodada1_especificacao.md`, `resultados/analise_rodada1_2025.md`): 9 perguntas por alternativa. A melhor pergunta isolada foi a **q1b** (atratividade em termos de quantos participantes escolheriam), com Brier fora da dobra de 0,0404. Combinar as 9 perguntas e o modelo em dois níveis não trouxe ganho. As perguntas de atratividade e correção se mostraram muito correlacionadas entre si (0,75 a 0,98).
- **Rodada 2** (`rodada2_especificacao.md`, `resultados/analise_rodada2_2025.md`): 9 perguntas sobre o mecanismo de atração dos distratores. Nenhuma, somada à q1b, reduziu o Brier de forma confiável (todos os intervalos de 95% das diferenças incluíram zero).
- **Rodada 3** (`rodada3_especificacao.md`, `resultados/analise_rodada3_2025.md`): comparações entre pares de alternativas (Choice entre duas, nas duas ordens), agregadas por Bradley-Terry. Pela regra de decisão definida na especificação antes da execução, a **combinação q1b + pares** substitui a q1b: diferença de Brier de −0,0013, IC 95% [−0,0025; −0,0001].

**Ressalva registrada:** na rodada 3 foram testadas três variantes de pares. Com correção de Bonferroni para essas três comparações, o intervalo da diferença passa a incluir zero (IC 98,3% [−0,0027; +0,0002]). A regra pré-definida foi seguida, e a hipótese H4 verifica em 2024 se o ganho sobre a q1b se repete.

## 2. Método principal: q1b + pares

Duas requisições por item, idênticas às usadas em 2025, com `jev-1.13.0` e o objeto `entrada` como `state`, sem gabarito:
- **rodada 1:** as 9 perguntas × 5 alternativas (da q1b, só o `score` é usado);
- **rodada 3:** os 20 pares ordenados de alternativas.

Cálculo da previsão, para cada item:
1. Para cada par {i, j}, combinar as duas ordens: p_ij = ½ · [P(i | i primeiro) + 1 − P(j | j primeiro)].
2. Estimar as forças de Bradley-Terry θ_A…θ_E, com soma zero e penalidade ridge λ = 0,01 (não usa as respostas dos participantes).
3. Com s₁ = `score` da q1b e s₂ = θ, padronizados pelas médias e desvios de 2025 (s₁: média 1,38207, desvio 0,97183; s₂: média 0, desvio 1,57860):

   p_k = softmax(**0,17538** · z₁ₖ + **0,29052** · z₂ₖ).

## 3. Comparadores (também congelados)

| Método | Descrição | Parâmetro de 2025 |
|---|---|---|
| q1b | Softmax da q1b com uma temperatura | β = 0,44246 (T = 2,2601) |
| q1a (sensibilidade) | Mesma transformação com a q1a | β = 0,43846 (T = 2,2807) |
| Oracle (**usa o gabarito**) | Gabarito recebe o acerto médio de 2025; os 4 distratores dividem o restante igualmente | acerto médio = 0,39507 |
| Uniforme | 20% para cada alternativa | — |
| Média por área de 2025 | Proporção média de cada letra, por área, em 2025 | ver `.json` |

## 4. Hipóteses e regras de decisão

| Id | Papel | Hipótese | Considerada sustentada se |
|---|---|---|---|
| **H1** | **Principal** | O Brier da combinação q1b + pares é menor que o da Oracle, que conhece o gabarito | o IC 95% da diferença (combinação − Oracle) estiver inteiramente abaixo de zero |
| H2 | Secundária | O Brier da combinação é menor que o da uniforme | o IC 95% da diferença (combinação − uniforme) estiver inteiramente abaixo de zero |
| H3 | Secundária | O acerto do principal distrator da combinação é maior que o acaso (0,25) | o limite inferior do IC 95% estiver acima de 0,25 |
| H4 | Secundária | O Brier da combinação é menor que o da q1b sozinha | o IC 95% da diferença (combinação − q1b) estiver inteiramente abaixo de zero |

- **Intervalos:** bootstrap percentil com 5.000 reamostragens e semente 2024. A unidade de reamostragem é o **grupo de itens** (itens que compartilham texto de apoio são sorteados juntos).
- **Brier:** soma dos 5 erros quadráticos entre as proporções previstas e as observadas, com média entre os itens. Cada item tem o mesmo peso.
- **Principal distrator:** proporção de itens em que o distrator de maior probabilidade prevista é o mais escolhido; em empate previsto entre k distratores, crédito de 1/k.

## 5. O que é descritivo (não confirmatório)

- A acurácia das comparações por par (pares só de distratores, pares com a correta, pares com diferença real maior que 10 pontos), a consistência entre as duas ordens e o viés de posição.
- Todas as demais métricas (MAE, Spearman, Jensen–Shannon, métricas só de distratores, AUC para distratores com menos de 5%).
- Os resultados por área (CN e MT têm poucos itens).
- As comparações com a q1a e com a média por área.
- As perguntas da rodada 2 **não** são aplicadas a 2024.

## 6. Procedimento do teste

1. Enviar as requisições:
   ```
   python EXPERIMENTOS/scripts/rodar_jev.py --rodada 1 --ano 2024 --saida EXPERIMENTOS/resultados/jev_rodada1_2024.jsonl
   python EXPERIMENTOS/scripts/rodar_jev.py --rodada 3 --ano 2024 --saida EXPERIMENTOS/resultados/jev_rodada3_2024.jsonl
   ```
2. Avaliar:
   ```
   python EXPERIMENTOS/scripts/avaliar_teste.py --congelamento EXPERIMENTOS/congelamento_teste_2024.json --respostas EXPERIMENTOS/resultados/jev_rodada1_2024.jsonl --respostas3 EXPERIMENTOS/resultados/jev_rodada3_2024.jsonl --saida EXPERIMENTOS/resultados/teste_2024
   ```
3. Os resultados são reportados como saírem, sustentando ou não as hipóteses. Nenhum parâmetro, pergunta ou métrica pode ser alterado depois do passo 1.

Se alguma requisição falhar, ela é reenviada com o mesmo corpo (o script pula os itens já respondidos). O script de avaliação interrompe o teste se alguma requisição usar outro modelo, outro `state` ou outras perguntas, ou se faltar algum item.
