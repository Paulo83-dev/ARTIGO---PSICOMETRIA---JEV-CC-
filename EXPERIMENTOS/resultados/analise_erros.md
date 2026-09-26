# Onde o método erra (análise descritiva, depois do teste)

↓ menor é melhor; ↑ maior é melhor.

## Taxa de acerto prevista × real, teste de 2024

| Método | MAE do acerto ↓ | Pearson ↑ | Spearman ↑ | Spearman com b da TRI | Brier ↓ | Fração do Brier no gabarito |
|---|---|---|---|---|---|---|
| q1b+pares (principal) | 0.1187 | 0.454 | 0.449 | -0.485 | 0.0420 | 53.6% |
| q1b | 0.1244 | 0.390 | 0.387 | -0.429 | 0.0453 | 54.9% |
| q1a (sensibilidade) | 0.1257 | 0.387 | 0.395 | -0.435 | 0.0460 | 54.4% |
| oracle (usa gabarito) | 0.1349 | — | — | — | 0.0521 | 53.4% |
| media_por_area 2025 | 0.2068 | 0.069 | 0.004 | 0.024 | 0.1014 | 66.8% |
| uniforme | 0.2087 | — | — | — | 0.1024 | 66.5% |
| LLM A (letras) | 0.1400 | 0.083 | 0.008 | 0.018 | 0.0529 | 55.6% |
| LLM B q1b | 0.1322 | 0.317 | 0.314 | -0.275 | 0.0502 | 52.9% |
| LLM B pares | 0.1189 | 0.439 | 0.439 | -0.362 | 0.0459 | 49.7% |
| LLM B q1b+pares | 0.1226 | 0.433 | 0.443 | -0.371 | 0.0444 | 51.2% |

## 2025 (método principal, 114 questões)

- Oracle informada (sabe o gabarito e o acerto real, divide o resto igualmente): Brier 0.0171 (método principal: 0.0391)
- Acerto real de 9.2% a 78.4%; previsto de 15.9% a 52.3%
- Brier entre distratores (todas as questões, 114): previsão 0.0404, divisão igual 0.0494
- Brier entre distratores (questões com distrator mais escolhido que a correta, 28): previsão 0.0519, divisão igual 0.0531

| Acerto real | Questões | Acerto previsto médio | Acerto real médio |
|---|---|---|---|
| até 25% | 21 | 32.7% | 18.3% |
| de 25% a 55% | 73 | 36.9% | 39.1% |
| acima de 55% | 20 | 46.3% | 63.3% |

10 melhores previsões: Brier 0.0048; acerto real 39.0%, previsto 38.3% (erro 3.2%); armadilhas 1; distrator principal certo 4; áreas {'LC': 1, 'CH': 6, 'CN': 2, 'MT': 1}; questões: 2025-CH-054, 2025-MT-157, 2025-CN-124, 2025-CN-131, 2025-CH-084, 2025-CH-088, 2025-LC-016, 2025-CH-053, 2025-CH-072, 2025-CH-071

10 piores previsões: Brier 0.1298; acerto real 32.9%, previsto 42.3% (erro 25.7%); armadilhas 7; distrator principal certo 3; áreas {'LC': 3, 'CH': 3, 'CN': 2, 'MT': 2}; questões: 2025-CN-112, 2025-LC-032, 2025-MT-151, 2025-CH-059, 2025-CN-116, 2025-CH-066, 2025-CH-079, 2025-LC-019, 2025-MT-146, 2025-LC-002-L1

## 2024 (método principal, 120 questões)

- Oracle informada (sabe o gabarito e o acerto real, divide o resto igualmente): Brier 0.0173 (método principal: 0.0420)
- Acerto real de 8.7% a 83.2%; previsto de 17.1% a 51.5%
- Brier entre distratores (todas as questões, 120): previsão 0.0346, divisão igual 0.0437
- Brier entre distratores (questões com distrator mais escolhido que a correta, 32): previsão 0.0395, divisão igual 0.0514

| Acerto real | Questões | Acerto previsto médio | Acerto real médio |
|---|---|---|---|
| até 25% | 20 | 31.5% | 18.5% |
| de 25% a 55% | 77 | 40.0% | 37.7% |
| acima de 55% | 23 | 45.3% | 66.7% |

10 melhores previsões: Brier 0.0031; acerto real 39.7%, previsto 38.3% (erro 2.7%); armadilhas 3; distrator principal certo 9; áreas {'LC': 3, 'CH': 6, 'CN': 0, 'MT': 1}; questões: 2024-LC-029, 2024-CH-065, 2024-CH-070, 2024-MT-162, 2024-CH-055, 2024-CH-058, 2024-LC-024, 2024-CH-050, 2024-CH-064, 2024-LC-032

10 piores previsões: Brier 0.1607; acerto real 51.0%, previsto 43.2% (erro 32.3%); armadilhas 4; distrator principal certo 1; áreas {'LC': 5, 'CH': 4, 'CN': 1, 'MT': 0}; questões: 2024-LC-026, 2024-CH-078, 2024-CN-095, 2024-CH-082, 2024-LC-007, 2024-CH-049, 2024-LC-009, 2024-LC-042, 2024-CH-069, 2024-LC-044
