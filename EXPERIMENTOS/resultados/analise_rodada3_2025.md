# Rodada 3: comparações entre pares, ENEM 2025 (114 itens)

## Diagnósticos

- Consistência entre as duas ordens: 0.9599
- Proporção em que o Jev escolhe a alternativa apresentada primeiro: 0.4877

| Tipo de par | Acurácia | Pares |
|---|---|---|
| so_distratores | 0.6711 | 681 |
| com_correta | 0.8838 | 456 |
| so_distratores_dif>10pp | 0.7478 | 226 |
| com_correta_dif>10pp | 0.9481 | 347 |

## Previsão fora da dobra (5 dobras)

| Método | Brier | Spearman | Brier distr. | Spearman distr. | Principal distrator | AUC <5% |
|---|---|---|---|---|---|---|
| q1b+pares_bradley_terry | 0.0391 | 0.5965 | 0.0404 | 0.3825 | 0.4474 | 0.8367 |
| pares_bradley_terry | 0.0396 | 0.5904 | 0.0423 | 0.3860 | 0.4518 | 0.8306 |
| q1b | 0.0404 | 0.5776 | 0.0419 | 0.3454 | 0.4167 | 0.8302 |
| pares_borda | 0.0432 | 0.5892 | 0.0467 | 0.3854 | 0.4518 | 0.7671 |

## Regra de decisão: diferença de Brier em relação à q1b

| Método | Diferença | IC 95% | Substitui a q1b? |
|---|---|---|---|
| pares_bradley_terry | -0.00082 | [-0.00283; +0.00116] | não |
| pares_borda | +0.00278 | [-0.00092; +0.00658] | não |
| q1b+pares_bradley_terry | -0.00130 | [-0.00245; -0.00013] | sim |
