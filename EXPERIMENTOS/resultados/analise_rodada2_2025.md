# Rodada 2: resultados, ENEM 2025 (114 itens)

## Características: ordenação dos distratores e redundância com q1b

Spearman bruto: escore sem ajuste × proporção real, só entre distratores (maior = melhor). Correlação com q1b: dentro do item (menor = mais informação nova).

| Pergunta | Spearman bruto entre distratores | Correlação com q1b |
|---|---|---|
| q14 | +0.3237 | +0.68 |
| q9 | +0.2835 | -0.01 |
| q7 | +0.2449 | +0.52 |
| q18 | +0.2279 | +0.46 |
| q13 | +0.2007 | +0.67 |
| q17 | +0.0957 | -0.34 |
| q10 | +0.0797 | -0.20 |
| q15 | -0.0159 | -0.52 |
| q11 | -0.0405 | -0.57 |
| q16 | -0.0487 | -0.45 |
| q12 | -0.2259 | -0.77 |

## Previsão fora da dobra (5 dobras)

| Método | Brier | Spearman | Brier distr. | Spearman distr. | Principal distrator | AUC <5% |
|---|---|---|---|---|---|---|
| q1b+q10 | 0.0390 | 0.5254 | 0.0452 | 0.2404 | 0.3509 | 0.8178 |
| selecao_ate_2 (aninhada) | 0.0395 | 0.5395 | 0.0453 | 0.2561 | 0.3860 | 0.7763 |
| q1b+q13 | 0.0401 | 0.5675 | 0.0418 | 0.3281 | 0.4035 | 0.8080 |
| q1b+q18 | 0.0404 | 0.5860 | 0.0413 | 0.3596 | 0.4298 | 0.8151 |
| q1b | 0.0404 | 0.5776 | 0.0419 | 0.3454 | 0.4167 | 0.8302 |
| q1b+q7 | 0.0405 | 0.5895 | 0.0414 | 0.3702 | 0.4474 | 0.8206 |
| q1b+q15 | 0.0405 | 0.5518 | 0.0431 | 0.3053 | 0.4123 | 0.8263 |
| q1b+q9 | 0.0407 | 0.5649 | 0.0426 | 0.3175 | 0.4211 | 0.8343 |
| q1b+q16 | 0.0407 | 0.5596 | 0.0423 | 0.3140 | 0.4035 | 0.8499 |
| q1b+q17 | 0.0408 | 0.5675 | 0.0423 | 0.3263 | 0.4211 | 0.8408 |
| q1b+q11 | 0.0408 | 0.5491 | 0.0433 | 0.2912 | 0.3860 | 0.8102 |
| q1b+q12 | 0.0409 | 0.5711 | 0.0425 | 0.3333 | 0.3947 | 0.8237 |
| q1b+q14 | 0.0410 | 0.5658 | 0.0433 | 0.3193 | 0.4035 | 0.8064 |

## Seleção de características

Escolhas em cada dobra externa (só com o treino): q10, q18; q10, q13; q10, q18; q10, q13; q10, q13

Seleção em todo o ano: q1b, q10, q7
- q1b: Brier CV interno 0.0402
- q1b + q10: Brier CV interno 0.0390
- q1b + q10 + q7: Brier CV interno 0.0386
