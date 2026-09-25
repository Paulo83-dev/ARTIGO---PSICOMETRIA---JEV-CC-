# Comparação com o LLM: teste, ENEM 2024 (120 itens)

Comparação acrescentada depois do teste principal, com parâmetros do LLM congelados em 2025.

↓ menor é melhor; ↑ maior é melhor; melhor valor de cada coluna em negrito.

## Comparações (diferença de Brier, a − b; negativo favorece a)

| Id | Comparação | Diferença | IC 95% |
|---|---|---|---|
| C1 | Jev q1b + pares × LLM, método A (letras) | -0.01089 | [-0.01656; -0.00545] |
| C2 | Jev q1b + pares × LLM, método B (q1b + pares) | -0.00245 | [-0.00673; +0.00182] |
| C3 | Jev q1b × LLM q1b (método B) | -0.00496 | [-0.01040; +0.00062] |
| C4 | LLM método A × Oracle | +0.00075 | [-0.00289; +0.00421] |

## Métricas

| Método | Brier ↓ | MAE ↓ | JS ↓ | Spearman ↑ | Brier distr. ↓ | Spearman distr. ↑ | Principal distrator ↑ | AUC <5% ↑ |
|---|---|---|---|---|---|---|---|---|
| q1b+pares (principal) | **0.0420** | **0.0665** | **0.0322** | 0.6275 | **0.0346** | 0.4433 | **0.4583** | **0.7465** |
| LLM B q1b+pares | 0.0444 | 0.0706 | 0.0349 | 0.6067 | 0.0395 | 0.4150 | 0.4083 | 0.7435 |
| q1b | 0.0453 | 0.0695 | 0.0346 | **0.6411** | 0.0354 | **0.4679** | 0.4375 | 0.7228 |
| LLM B pares | 0.0459 | 0.0707 | 0.0361 | 0.6283 | 0.0418 | 0.4383 | 0.4417 | 0.7304 |
| q1a (sensibilidade) | 0.0460 | 0.0703 | 0.0351 | 0.6126 | 0.0363 | 0.4115 | 0.4167 | 0.7279 |
| LLM B q1b | 0.0502 | 0.0764 | 0.0393 | 0.5633 | 0.0424 | 0.3217 | 0.3167 | 0.7097 |
| oracle (usa gabarito) | 0.0521 | 0.0778 | 0.0409 | 0.5480 | 0.0437 | — | 0.2500 | 0.5000 |
| LLM A (letras) | 0.0529 | 0.0779 | 0.0409 | 0.4942 | 0.0404 | 0.2150 | 0.4083 | 0.5914 |
| media_por_area 2025 | 0.1014 | 0.1038 | 0.0747 | 0.1292 | 0.0423 | 0.1400 | 0.3167 | 0.5571 |
| uniforme | 0.1024 | 0.1057 | 0.0757 | — | 0.0437 | — | 0.2500 | 0.5000 |

## Brier por área

| Método | CH ↓ | CN ↓ | LC ↓ | MT ↓ |
|---|---|---|---|---|
| q1b+pares (principal) | 0.0393 | 0.0462 | **0.0486** | 0.0295 |
| LLM B q1b+pares | **0.0376** | 0.0462 | 0.0503 | 0.0450 |
| q1b | 0.0429 | 0.0523 | 0.0514 | 0.0309 |
| LLM B pares | 0.0378 | 0.0470 | 0.0520 | 0.0494 |
| q1a (sensibilidade) | 0.0433 | 0.0526 | 0.0520 | 0.0326 |
| LLM B q1b | 0.0388 | 0.0448 | 0.0644 | 0.0492 |
| oracle (usa gabarito) | 0.0440 | 0.0429 | 0.0643 | 0.0515 |
| LLM A (letras) | 0.0430 | 0.0578 | 0.0560 | 0.0636 |
| media_por_area 2025 | 0.1036 | 0.0445 | 0.1567 | **0.0255** |
| uniforme | 0.1041 | **0.0418** | 0.1563 | 0.0336 |

## Comparações entre pares

**Jev**

| Tipo de par | Acurácia | Pares |
|---|---|---|
| Só distratores | 0.6978 | 718 |
| Com a correta | 0.8854 | 480 |
| Só distratores, diferença real > 10 p.p. | 0.8033 | 239 |
| Com a correta, diferença real > 10 p.p. | 0.9462 | 372 |

**LLM**

| Tipo de par | Acurácia | Pares |
|---|---|---|
| Só distratores | 0.6592 | 716 |
| Com a correta | 0.8750 | 480 |
| Só distratores, diferença real > 10 p.p. | 0.7458 | 240 |
| Com a correta, diferença real > 10 p.p. | 0.9462 | 372 |

## Custo

| Modelo | Chamadas | Tokens de entrada | Custo total (US$) ↓ | Custo por item (US$) ↓ |
|---|---|---|---|---|
| Jev (rodadas 1 e 3) | 240 | 1,888,094 | **0.0793** | **0.00066** |
| LLM (métodos A e B) | 3600 | 1,669,404 | 0.2886 | 0.00241 |

LLM: mediana de 0.70 s por chamada; 603 de 3600 chamadas (17%) tiveram tokens de raciocínio. Custo do Jev calculado pelos tokens de entrada a US$ 0,042 por milhão.
