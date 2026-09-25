# Teste da configuração congelada: ENEM 2024 (120 itens)

↓ menor é melhor; ↑ maior é melhor; melhor valor de cada coluna em negrito.

## Hipóteses pré-registradas

| Id | Hipótese | Estimativa | IC 95% | Sustentada? |
|---|---|---|---|---|
| H1 | Brier da combinação q1b + pares menor que o da Oracle (que conhece o gabarito) | -0.01013 | [-0.01572; -0.00462] | sim |
| H2 | Brier da combinação q1b + pares menor que o da distribuição uniforme | -0.06040 | [-0.07660; -0.04423] | sim |
| H3 | Acerto do principal distrator da combinação acima do acaso (0,25) | +0.45833 | [+0.36667; +0.55000] | sim |
| H4 | Brier da combinação q1b + pares menor que o da q1b sozinha | -0.00329 | [-0.00496; -0.00180] | sim |

## Comparações entre pares (descritivo)

- Consistência entre as duas ordens: 0.9536
- Proporção em que o Jev escolhe a alternativa apresentada primeiro: 0.4854

| Tipo de par | Acurácia | Pares |
|---|---|---|
| Só distratores | 0.6978 | 718 |
| Com a correta | 0.8854 | 480 |
| Só distratores, diferença real > 10 p.p. | 0.8033 | 239 |
| Com a correta, diferença real > 10 p.p. | 0.9462 | 372 |

## Métricas descritivas

| Método | Brier ↓ | MAE ↓ | JS ↓ | Spearman ↑ | Brier distr. ↓ | Spearman distr. ↑ | Principal distrator ↑ | AUC <5% ↑ |
|---|---|---|---|---|---|---|---|---|
| q1b+pares (principal) | **0.0420** | **0.0665** | **0.0322** | 0.6275 | **0.0346** | 0.4433 | **0.4583** | **0.7465** |
| q1b | 0.0453 | 0.0695 | 0.0346 | **0.6411** | 0.0354 | **0.4679** | 0.4375 | 0.7228 |
| q1a (sensibilidade) | 0.0460 | 0.0703 | 0.0351 | 0.6126 | 0.0363 | 0.4115 | 0.4167 | 0.7279 |
| oracle (usa gabarito) | 0.0521 | 0.0778 | 0.0409 | 0.5480 | 0.0437 | — | 0.2500 | 0.5000 |
| media_por_area 2025 | 0.1014 | 0.1038 | 0.0747 | 0.1292 | 0.0423 | 0.1400 | 0.3167 | 0.5571 |
| uniforme | 0.1024 | 0.1057 | 0.0757 | — | 0.0437 | — | 0.2500 | 0.5000 |

## Brier por área (descritivo)

| Método | CH ↓ | CN ↓ | LC ↓ | MT ↓ |
|---|---|---|---|---|
| q1b+pares (principal) | **0.0393** | 0.0462 | **0.0486** | 0.0295 |
| q1b | 0.0429 | 0.0523 | 0.0514 | 0.0309 |
| q1a (sensibilidade) | 0.0433 | 0.0526 | 0.0520 | 0.0326 |
| oracle (usa gabarito) | 0.0440 | 0.0429 | 0.0643 | 0.0515 |
| media_por_area 2025 | 0.1036 | 0.0445 | 0.1567 | **0.0255** |
| uniforme | 0.1041 | **0.0418** | 0.1563 | 0.0336 |
