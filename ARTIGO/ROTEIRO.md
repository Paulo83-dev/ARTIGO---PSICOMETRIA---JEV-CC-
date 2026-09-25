# Roteiro do artigo

Status: **primeira versão de todas as seções escrita** (2026-09-25). Pendências: Figura do desenho experimental; enxugar o resumo conforme o periódico.

**Título provisório:** Prevendo a atratividade de distratores do ENEM com um modelo de decisão calibrada: atratividade por alternativa e comparações entre pares

Convenção: **[D]** = análise descritiva ou exploratória; **[C]** = hipótese pré-registrada (confirmatória); **[P]** = análise acrescentada depois do teste principal.

---

## Resumo (`00_resumo.tex`)
Problema (pré-teste caro; distratores), objetivo, dados (234 itens textuais do ENEM, 2024–2025, microdados do Inep), método (Jev: atratividade por alternativa + comparações entre pares; calibração por temperatura; desenvolvimento em 2025, teste congelado em 2024), resultados principais (H1–H4; pares de distratores ≈ 70%/80%; comparação com LLM), conclusão.

## 1. Introdução (`01_introducao.tex`)
- Itens de múltipla escolha e o papel dos distratores; o pré-teste com estudantes como forma de conhecer o funcionamento dos distratores, e seu custo e risco de exposição dos itens.
- Previsão a partir do texto: da dificuldade (TRI) à distribuição completa de escolhas (*candidate distribution matching*).
- O problema dos LLMs: acertam a resposta, mas não reproduzem a atratividade dos distratores (Säuberli et al., 2025).
- Lacunas: (a) métodos de avaliação de distratores raramente validados contra escolhas reais; (b) português e ENEM sub-representados; (c) modelos de decisão calibrada nunca avaliados como preditores de comportamento populacional.
- Proposta: usar o Jev com perguntas de atratividade por alternativa e comparações entre pares, agregadas por modelos de escolha (Luce, Bradley-Terry, Bock).
- Contribuições (lista numerada) e visão geral dos resultados.

## 2. Referencial teórico e trabalhos relacionados (`02_referencial.tex`)
- **2.1 Distratores na psicometria:** distratores funcionais e o critério de 5% (Haladyna & Downing; Tarrant et al.); modelo nominal de Bock como softmax de tendências de resposta; razões de seleção e modelo de escolha de Luce (Love; Revuelta); logit aninhado: acerto × escolha entre distratores (Bolt et al., 2012; Haberman et al., 2019); formato DOMC e atratividade absoluta × relativa (Bolt et al., 2019).
- **2.2 Avaliação automática de distratores:** taxonomia e lacuna de validação (Benedetto et al., 2025); plausibilidade por modelos de leitura (Raina et al., 2023); ranqueadores de pares e fatores de plausibilidade (Lee et al., 2025; Scarlatos et al., 2024); estratégias de construção (Nagai & Uto, 2025; Zhang et al., 2020).
- **2.3 Previsão de escolhas e parâmetros a partir do texto:** *candidate distribution matching* (Liusie et al., 2023); plausibilidade psicométrica de LLMs e a linha de base Oracle (Säuberli et al., 2025); respondentes simulados (Liu et al., 2025); TRI no ENEM a partir do texto (Marinho et al., 2023).
- **2.4 Calibração e modelos de decisão estruturada:** *temperature scaling* (Guo et al., 2017); o Jev e as primitivas (TypeSafe AI); avaliação independente do Jev (Li et al., 2026).

## 3. Método (`03_metodo.tex`)
- **3.1 Dados:** curadoria das questões textualmente autossuficientes (critérios, exclusões, validação); cálculo das proporções de escolha pelos microdados (população, respostas válidas); parâmetros TRI oficiais. *Tabela 1: itens por área e ano.*
- **3.2 O Jev:** modelo de linguagem pós-treinado para decisões estruturadas com probabilidades calibradas; primitivas Choice, Score e Noul; versão `jev-1.13.0`; entrada sem gabarito.
- **3.3 Das respostas do Jev à distribuição A–E:** (a) atratividade por alternativa (Score) + softmax com temperatura; (b) comparações entre pares (Choice entre duas, nas duas ordens) + Bradley-Terry; (c) combinação por logit condicional. Fundamentação: Bock, Luce, *temperature scaling*. *Figura 1: exemplo de um item, das comparações às porcentagens.*
- **3.4 Desenho experimental:** desenvolvimento em 2025 com validação cruzada em 5 dobras agrupadas (rodadas 1, 2 e 3); regra de decisão definida antes de cada rodada; congelamento registrado em commit datado; teste único em 2024. *Figura 2: fluxo do desenho.*
- **3.5 Linhas de base:** uniforme; média por área; Oracle (usa o gabarito).
- **3.6 Métricas e hipóteses:** Brier A–E; métricas de distratores (renormalizadas); principal distrator; AUC para distratores não funcionais; hipóteses H1–H4; bootstrap por grupos.
- **3.7 Comparação com um LLM generativo [P]:** GLM-5.3-Flash; método A (letras em 5 rotações); método B (mesmas perguntas); mesmo protocolo de congelamento.

## 4. Resultados (`04_resultados.tex`)
- **4.1 Desenvolvimento (2025) [D]:** rodada 1 (a q1b como melhor pergunta; redundância entre perguntas; *Figura 3: correlações entre perguntas*); rodada 2 (perguntas de mecanismo sem ganho confiável); rodada 3 (pares; decisão pela regra pré-definida e ressalva de multiplicidade). *Tabela 2.*
- **4.2 Teste em 2024 [C]:** H1–H4. *Tabela 3: hipóteses; Tabela 4: métricas.*
- **4.3 Distratores e comparações entre pares [D]:** acurácia em pares de distratores (≈ 70%; ≈ 80% com diferença > 10 p.p.), consistência entre ordens, viés de posição; comparação com a literatura.
- **4.4 Resultados por área [D]:** Brier bruto × ganho sobre a uniforme; LC e CH × CN e MT. *Tabela 5.*
- **4.5 Comparação com o LLM [P]:** C1–C4, métricas, custo. *Tabela 6.*

## 5. Discussão (`05_discussao.tex`)
- O juízo único de "quão correta a alternativa parece" e por que as perguntas de mecanismo não ajudaram.
- Por que as comparações entre pares ajudam: o meio-termo entre avaliar isoladamente e comparar todas (DOMC, Luce).
- Método × modelo: o método funciona também num LLM; o Jev se destaca em custo, calibração e estabilidade; só o Jev superou a Oracle.
- Onde funciona e onde não: leitura e interpretação (LC, CH) × cálculo (CN, MT).
- Implicações para a elaboração de itens e para a triagem antes do pré-teste (apoio, não substituição).
- **Limitações:** só itens textuais; dois anos e uma população; uma única distribuição "típica" (sem variação por habilidade); pressuposto de Luce; modelo proprietário e versão fixa; itens públicos (possível exposição no treino dos modelos); análises exploratórias e multiplicidade no desenvolvimento; comparação com LLM acrescentada depois do teste principal.

## 6. Conclusão (`06_conclusao.tex`)

## Disponibilidade de dados e código (`07_disponibilidade.tex`)
Repositório no GitHub; acervo, respostas brutas, scripts, especificações e congelamentos; fontes oficiais do Inep.

## Apêndices (`08_apendices.tex`)
- A. Perguntas completas feitas ao Jev (rodadas 1, 2 e 3).
- B. Parâmetros congelados.
- C. Tabelas completas do desenvolvimento.
- D. Prompts do LLM.
