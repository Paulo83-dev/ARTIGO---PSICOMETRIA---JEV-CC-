# Comparação com o LLM: desenvolvimento, ENEM 2025 (114 itens, 5 dobras)

↓ menor é melhor; ↑ maior é melhor; melhor valor de cada coluna em negrito.

## Previsão fora da dobra

| Método | Brier ↓ | MAE ↓ | JS ↓ | Spearman ↑ | Brier distr. ↓ | Spearman distr. ↑ | Principal distrator ↑ | AUC <5% ↑ |
|---|---|---|---|---|---|---|---|---|
| Jev q1b+pares | **0.0391** | **0.0660** | **0.0322** | 0.5965 | **0.0404** | 0.3825 | 0.4474 | **0.8367** |
| Jev q1b | 0.0404 | 0.0673 | 0.0334 | 0.5776 | 0.0419 | 0.3454 | 0.4167 | 0.8302 |
| LLM B q1b+pares | 0.0407 | 0.0677 | 0.0340 | 0.5982 | 0.0450 | 0.4140 | 0.4825 | 0.7792 |
| LLM B pares | 0.0434 | 0.0693 | 0.0358 | **0.6114** | 0.0471 | **0.4298** | **0.5088** | 0.7684 |
| LLM A (letras) | 0.0465 | 0.0746 | 0.0387 | 0.4930 | 0.0471 | 0.2193 | 0.3333 | 0.6832 |
| LLM B q1b | 0.0483 | 0.0754 | 0.0400 | 0.5456 | 0.0493 | 0.3193 | 0.4167 | 0.7213 |

## Comparações entre pares do LLM

| Tipo de par | Acurácia | Pares |
|---|---|---|
| Só distratores | 0.6794 | 680 |
| Com a correta | 0.8725 | 455 |
| Só distratores, diferença real > 10 p.p. | 0.7689 | 225 |
| Com a correta, diferença real > 10 p.p. | 0.9509 | 346 |

## Custo

| Modelo | Chamadas | Tokens de entrada | Custo total (US$) ↓ | Custo por item (US$) ↓ |
|---|---|---|---|---|
| Jev (rodadas 1 e 3) | 228 | 1,793,122 | **0.0753** | **0.00066** |
| LLM (métodos A e B) | 3420 | 1,583,042 | 0.2757 | 0.00242 |

LLM: mediana de 0.90 s por chamada; 705 de 3420 chamadas (21%) tiveram tokens de raciocínio. Custo do Jev calculado pelos tokens de entrada a US$ 0,042 por milhão.
