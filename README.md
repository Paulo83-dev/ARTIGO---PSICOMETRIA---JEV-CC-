# Atratividade de distratores do ENEM com o modelo Jev

Este repositório reúne os dados e o código de uma pesquisa em psicometria que investiga se o **Jev** (TypeSafe AI), um modelo de linguagem que devolve decisões estruturadas com probabilidades em vez de texto, consegue antecipar **como os participantes do ENEM distribuem suas escolhas entre as alternativas A–E** de uma questão, incluindo a atratividade de cada distrator.

As previsões do Jev são comparadas com as proporções reais de escolha calculadas a partir dos microdados oficiais do Inep.

## Estrutura

```
exportacao_acervo/
  acervo_questoes_aprovadas_enem_2024_2025.json   acervo de questões (entrada do experimento)
VIZUALIZAÇÂO HTML/
  REVISAO_INTEGRAL_ACERVO_2024.html                revisão da curadoria, questão a questão, com o gráfico real × previsto
  REVISAO_INTEGRAL_ACERVO_2025.html
EXPERIMENTOS/
  rodada1_especificacao.md                         perguntas feitas ao Jev e desenho da rodada
  scripts/                                         código para montar as perguntas e chamar a API
  resultados/                                      respostas brutas do Jev e resultados das análises
```

## Dados

**Acervo.** Questões dos cadernos azuis do ENEM 2024 e 2025 que são **textualmente autossuficientes**: foram excluídas as que dependem de imagem, gráfico, diagrama ou quadro, no enunciado ou nas alternativas, e as anuladas. A elegibilidade foi definida sem usar gabarito, parâmetros TRI, frequências observadas ou desempenho de modelos.

Para cada questão, o acervo traz:
- `entrada`: área, texto de apoio, texto principal e alternativas A–E. **É o único conteúdo enviado ao modelo.**
- `gabarito` e `parametros_tri_oficiais` (a, b, c) da tabela oficial de itens;
- `respostas_observadas`: contagens e proporções A–E entre as marcações válidas dos participantes presentes nas provas regulares impressas.

O dicionário completo dos campos está dentro do próprio arquivo JSON (`dicionario_de_campos`).

**O que não está no repositório.** Os microdados do ENEM e os cadernos de prova em PDF são públicos e podem ser obtidos no portal do Inep; não são redistribuídos aqui. O acervo já contém as contagens agregadas necessárias para as análises, sem nenhuma resposta individual.

### Como citar os dados

Os microdados devem ser citados conforme a orientação do Inep (seção 5 do Leia-me de cada edição):

- INSTITUTO NACIONAL DE ESTUDOS E PESQUISAS EDUCACIONAIS ANÍSIO TEIXEIRA. **Microdados do Enem 2024**. Brasília: Inep, 2025. Disponível em: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem. Acesso em: 25 set. 2026.
- INSTITUTO NACIONAL DE ESTUDOS E PESQUISAS EDUCACIONAIS ANÍSIO TEIXEIRA. **Microdados do Enem 2025**. Brasília: Inep, 2026. Disponível em: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem. Acesso em: 25 set. 2026.

## Desenho experimental

- **Desenvolvimento: ENEM 2025.** Todas as escolhas (perguntas, temperatura, combinação) são feitas apenas com estes itens, usando validação cruzada.
- **Teste: ENEM 2024.** A configuração escolhida é congelada e registrada antes de ser aplicada, uma única vez, aos itens de 2024.
- **Modelo:** versão fixa `jev-1.13.0`.

Os detalhes de cada rodada estão no arquivo de especificação correspondente em `EXPERIMENTOS/`. A configuração do teste, as hipóteses e as regras de decisão estão em `EXPERIMENTOS/congelamento_teste_2024.md` (texto) e `congelamento_teste_2024.json` (parâmetros lidos pelo código); o teste é avaliado por `EXPERIMENTOS/scripts/avaliar_teste.py`.

## Como reproduzir

Requisitos: Python 3.11 ou superior e o pacote `httpx`.

1. Crie um arquivo `.env` na raiz com a sua chave da TypeSafe:
   ```
   TYPESAFE_API_KEY=sua_chave
   ```
2. Envie as perguntas ao Jev (um item por requisição; itens já respondidos são pulados):
   ```
   python EXPERIMENTOS/scripts/rodar_jev.py --rodada 1 --ano 2025 --saida EXPERIMENTOS/resultados/jev_rodada1_2025.jsonl
   ```

3. Rode a análise com validação cruzada no ano de desenvolvimento (gera um `.json` com todas as previsões e parâmetros e um `.md` com as tabelas):
   ```
   python EXPERIMENTOS/scripts/analisar_rodada1.py --ano 2025 --respostas EXPERIMENTOS/resultados/jev_rodada1_2025.jsonl --saida EXPERIMENTOS/resultados/analise_rodada1_2025
   ```
   Requer também `numpy` e `scipy`.
4. Rodada 2 (perguntas sobre o mecanismo de atração): envie com `--rodada 2` e analise combinando as duas rodadas:
   ```
   python EXPERIMENTOS/scripts/rodar_jev.py --rodada 2 --ano 2025 --saida EXPERIMENTOS/resultados/jev_rodada2_2025.jsonl
   python EXPERIMENTOS/scripts/analisar_rodada2.py --ano 2025 --respostas1 EXPERIMENTOS/resultados/jev_rodada1_2025.jsonl --respostas2 EXPERIMENTOS/resultados/jev_rodada2_2025.jsonl --saida EXPERIMENTOS/resultados/analise_rodada2_2025
   ```
5. Rodada 3 (comparações entre pares de alternativas):
   ```
   python EXPERIMENTOS/scripts/rodar_jev.py --rodada 3 --ano 2025 --saida EXPERIMENTOS/resultados/jev_rodada3_2025.jsonl
   python EXPERIMENTOS/scripts/analisar_rodada3.py --ano 2025 --respostas1 EXPERIMENTOS/resultados/jev_rodada1_2025.jsonl --respostas3 EXPERIMENTOS/resultados/jev_rodada3_2025.jsonl --saida EXPERIMENTOS/resultados/analise_rodada3_2025
   ```
6. Teste em 2024: os comandos estão na seção 6 de `EXPERIMENTOS/congelamento_teste_2024.md`.
7. Comparação com um LLM generativo (`z-ai/glm-5.3-flash` via OpenRouter; requer `OPENROUTER_API_KEY` no `.env`). Especificação em `EXPERIMENTOS/comparacao_llm_especificacao.md`:
   ```
   python EXPERIMENTOS/scripts/rodar_llm.py --ano 2025 --saida EXPERIMENTOS/resultados/llm_glm_2025.jsonl
   python EXPERIMENTOS/scripts/analisar_llm.py desenvolvimento --ano 2025 --llm EXPERIMENTOS/resultados/llm_glm_2025.jsonl --jev1 EXPERIMENTOS/resultados/jev_rodada1_2025.jsonl --jev3 EXPERIMENTOS/resultados/jev_rodada3_2025.jsonl --saida EXPERIMENTOS/resultados/analise_llm_2025 --congelamento EXPERIMENTOS/congelamento_llm_2024.json
   python EXPERIMENTOS/scripts/rodar_llm.py --ano 2024 --saida EXPERIMENTOS/resultados/llm_glm_2024.jsonl
   python EXPERIMENTOS/scripts/analisar_llm.py teste --congelamento EXPERIMENTOS/congelamento_llm_2024.json --llm EXPERIMENTOS/resultados/llm_glm_2024.jsonl --teste-jev EXPERIMENTOS/resultados/teste_2024.json --saida EXPERIMENTOS/resultados/comparacao_llm_2024
   ```

Cada linha do arquivo de saída das chamadas guarda o corpo exato enviado, o SHA-256 desse corpo, o status HTTP e a resposta bruta. As análises podem ser refeitas a partir desses arquivos, sem novas chamadas à API. Uma nova chamada pode dar respostas diferentes se o serviço mudar.

## Artigo

O texto do artigo está em `ARTIGO/` (LaTeX, pronto para o Overleaf; arquivo principal `main.tex`). As tabelas, as figuras e o apêndice (perguntas e parâmetros congelados) são gerados a partir dos resultados salvos e das definições usadas nas chamadas aos modelos; nenhum número das tabelas é digitado à mão. A análise descritiva de onde o método erra (feita depois do teste, sem ajustar nada) vem antes das tabelas:
```
python EXPERIMENTOS/scripts/analise_erros.py
python EXPERIMENTOS/scripts/gerar_tabelas.py
python EXPERIMENTOS/scripts/figuras_artigo.py
python EXPERIMENTOS/scripts/gerar_apendice.py
```

## Páginas de revisão

Cada questão elegível das páginas em `VIZUALIZAÇÂO HTML/` traz um gráfico com a proporção real de escolha de cada alternativa e a previsão do método principal (em 2025, previsão fora da dobra; em 2024, previsão do teste com os parâmetros congelados), e um seletor permite ordenar as questões pelo Brier, pelo erro na taxa de acerto ou pela taxa de acerto real. Os gráficos e o seletor são gerados a partir dos resultados salvos:
```
python EXPERIMENTOS/scripts/graficos_html.py
```
