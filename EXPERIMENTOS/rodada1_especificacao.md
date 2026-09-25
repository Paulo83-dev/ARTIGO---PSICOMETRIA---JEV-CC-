# Rodada 1: especificação das perguntas ao Jev

Status: **executada** no ENEM 2025 em 2026-09-25 (redação aprovada antes da execução).

## 1. Desenho

| Elemento | Decisão |
|---|---|
| Modelo | `jev-1.13.0` (versão fixa, não o alias `jev-latest`) |
| Desenvolvimento | ENEM **2025**, 114 itens. Todas as escolhas são feitas aqui, com validação cruzada em 5 dobras (itens que compartilham `apoio_compartilhado` ficam na mesma dobra) |
| Teste | ENEM **2024**, 120 itens. Roda **uma vez**, depois de a configuração ser congelada e registrada com data |
| `state` | O objeto `entrada` do acervo, sem alteração e **sem gabarito** |
| Idioma | Instruções e níveis em português |
| Requisição | **Uma por item**, com 9 perguntas × 5 alternativas = 45 perguntas. IDs no formato `q1a_A`, `q1a_B`, …, `q9_E` (os IDs não são enviados ao modelo) |

## 2. Como cada pergunta é usada

- **Perguntas de distribuição** (Q1a, Q1b, Q2, Q3): são monotônicas com a escolha para as 5 alternativas, inclusive o gabarito. Cada uma gera sozinha uma distribuição A–E por softmax com temperatura.
- **Perguntas de característica** (Q4, Q5, Q6, Q7, Q9): descrevem um aspecto da alternativa. Entram como **variáveis** numa combinação (softmax de uma soma ponderada, com pesos aprendidos só em 2025) e na análise explicativa dos distratores.

## 3. As perguntas

Convenções: as instruções são objetos com `pergunta` e `foco`. Os níveis de Score são objetos com `situacao` e `sinais`, do nível mais baixo ao mais alto, sem números nem porcentagens. Abaixo, a alternativa **C** serve de exemplo; nas outras, só muda a letra do caminho.

---

### Q1a: Atratividade por grau de convencimento

Score. Formula a atratividade em termos de **quão convincente** a alternativa é.

```json
{
  "pergunta": "Quão atraente a alternativa em `alternativas.C` pareceria como resposta para um participante típico do ENEM tentando resolver esta questão?",
  "foco": "Avalie a alternativa isoladamente. Julgue a plausibilidade de ela ser escolhida, inclusive por erro comum."
}
```

**Níveis:**
0. Esta alternativa é claramente incompatível com o enunciado; um participante atento a descartaria imediatamente.
1. Esta alternativa pode atrair uma leitura superficial, mas um entendimento básico da questão a torna pouco plausível.
2. Esta alternativa é plausível para participantes que cometam uma interpretação ou um cálculo equivocado.
3. Esta alternativa é bastante convincente e pode competir com outras respostas para muitos participantes.
4. Esta alternativa é fortemente convincente para quem tenta resolver a questão e tende a ser escolhida com frequência.

---

### Q1b: Atratividade por proporção de participantes

Score. Formula a atratividade em termos de **quantos participantes** escolheriam. A comparação entre Q1a e Q1b mostra se o enquadramento (grau de convencimento × quantidade de pessoas) muda o resultado.

```json
{
  "pergunta": "Quantos participantes do ENEM escolheriam a alternativa em `alternativas.C` como resposta desta questão?",
  "foco": "Considere participantes reais do ENEM, com níveis variados de preparo, lendo a questão inteira em condições de prova. Julgue apenas a alternativa indicada."
}
```

| Situação | Sinais |
|---|---|
| Quase ninguém escolheria | Descabida mesmo numa leitura apressada; só seria marcada por engano ou chute puro |
| Poucos escolheriam | Parece errada para a maioria; atrai sobretudo quem não entendeu o comando ou chutou |
| Uma parcela considerável escolheria | Parece razoável numa leitura rápida, mas uma leitura atenta revela o problema |
| Muitos escolheriam | Parece a resposta certa para quem não domina bem o texto ou o conteúdo |
| A maioria escolheria | Parece a melhor resposta para quase todos os participantes |

---

### Q2: Plausibilidade como resposta

Score. Mede a **aparência de resposta adequada ao comando**, não a correção.

```json
{
  "pergunta": "Quão plausível a alternativa em `alternativas.C` parece como resposta ao que a questão pede?",
  "foco": "Julgue se ela tem a aparência de uma resposta adequada ao comando, considerando o texto da questão. Não julgue se ela está de fato correta."
}
```

| Situação | Sinais |
|---|---|
| Não tem relação com o que foi pedido | Fala de outro assunto ou não responde ao tipo de pergunta feita |
| Tem relação com o tema, mas claramente não serve como resposta | Menciona elementos do texto, mas não responde ao comando |
| Serve em parte como resposta | Responde ao comando de forma vaga, incompleta ou com um problema perceptível |
| Parece uma resposta adequada | Responde ao comando de forma coerente; se houver problema, ele é sutil |
| Parece a resposta mais adequada possível | Responde ao comando de forma completa, precisa e bem ajustada ao texto |

---

### Q3: Esforço para descartar

Score. Baseada na escala de efeito distrativo de Zhang et al. (2020) e na dificuldade de rejeição de Revuelta (2005).

```json
{
  "pergunta": "O que um participante precisa fazer para perceber que a alternativa em `alternativas.C` não é a resposta desta questão?",
  "foco": "Considere o caminho mais curto para descartá-la. Se ela não puder ser descartada, escolha o nível correspondente."
}
```

| Situação | Sinais |
|---|---|
| Basta ler a própria alternativa | É incoerente, absurda ou fora do tema, independentemente da questão |
| Basta ler o comando da questão | Não responde ao que foi pedido, mesmo sem ler o texto de apoio |
| É preciso ler com atenção o texto de apoio ou os dados do enunciado | Contradiz, distorce ou extrapola algo que está explícito no texto ou nos dados |
| É preciso interpretação aprofundada, conhecimento específico ou várias etapas de raciocínio | O erro só aparece com inferência, domínio do conteúdo ou cálculo |
| Não é possível descartá-la | Mesmo com leitura atenta e bom conhecimento, ela parece a resposta correta |

---

### Q4: É a resposta correta?

Noul. Julgamento de correção **isolado**, para comparar com o Choice (o viés do "inteligente demais").

```json
{
  "pergunta": "A alternativa em `alternativas.C` é a resposta correta desta questão?"
}
```

`criteria`:
- **true:** a alternativa responde corretamente ao comando, de acordo com o texto e o conhecimento da área.
- **false:** a alternativa não responde corretamente ao comando.

---

### Q5: Verdade local

Noul. Captura o distrator "verdadeiro, mas que não responde ao comando".

```json
{
  "pergunta": "O conteúdo da alternativa em `alternativas.C`, considerado isoladamente, é verdadeiro?",
  "foco": "Julgue apenas se o que a alternativa afirma é verdadeiro ou compatível com o texto da questão e com o conhecimento correto da área. Não importa se ela responde ao que o comando pede."
}
```

`criteria`:
- **true:** o que a alternativa afirma é verdadeiro ou compatível com o texto, mesmo que não responda ao comando.
- **false:** o que a alternativa afirma é falso, contradiz o texto ou não tem apoio nele.

Limitação conhecida: em itens de MT com alternativas numéricas, "verdade local" pode não fazer sentido. A análise por área vai mostrar se a pergunta vale nesses casos.

---

### Q6: Correção parcial

Score.

```json
{
  "pergunta": "Quanto do que a alternativa em `alternativas.C` afirma está correto em relação ao que a questão pede?"
}
```

| Situação | Sinais |
|---|---|
| Nada está correto | O conteúdo inteiro é errado ou irrelevante para o comando |
| Contém um elemento correto, mas o essencial está errado | Aproveita uma ideia certa, mas a conclusão ou o foco estão errados |
| Mistura partes corretas e incorretas em proporção semelhante | Metade da afirmação procede e a outra metade não |
| Quase tudo está correto, com um erro ou omissão importante | Está perto da resposta, mas uma palavra, condição ou detalhe a torna errada |
| Está totalmente correta | Responde ao comando sem erro nem omissão |

---

### Q7: Eco do texto

Score. Semelhança **de superfície** com o texto da questão.

```json
{
  "pergunta": "Quanto a alternativa em `alternativas.C` reaproveita palavras, expressões ou ideias que aparecem explicitamente no texto da questão?",
  "foco": "Avalie só a semelhança de superfície com o texto, e não se a alternativa está correta."
}
```

| Situação | Sinais |
|---|---|
| Nada do texto aparece | Vocabulário e ideias sem relação com o texto |
| Trata do mesmo tema com vocabulário próprio | Assunto próximo, mas sem palavras-chave do texto |
| Usa algumas palavras-chave do texto | Termos importantes do texto aparecem, em frases diferentes |
| Parafraseia de perto um trecho do texto | Reformula uma frase ou ideia específica do texto |
| Copia literalmente trechos do texto | Repete palavra por palavra partes do texto |

---

### Q9: Equívoco comum

Score. O critério mais recomendado na literatura educacional. (A numeração segue o cardápio; a Q8 ficou para a rodada com gabarito.)

```json
{
  "pergunta": "A alternativa em `alternativas.C` corresponde a um erro que estudantes do ensino médio costumam cometer nesta questão?",
  "foco": "Considere erros típicos: leitura apressada, confusão entre conceitos parecidos, generalização excessiva, inversão de causa e efeito, uso de conhecimento prévio no lugar do texto, erro de cálculo comum."
}
```

| Situação | Sinais |
|---|---|
| Não reflete nenhum erro típico | A alternativa é correta, ou é um erro arbitrário que quase ninguém cometeria |
| Reflete um erro possível, mas pouco comum | Exige uma confusão incomum para ser escolhida |
| Reflete um erro comum entre estudantes com dificuldade no conteúdo | Atrai quem tem lacunas de conhecimento ou de leitura |
| Reflete um erro muito comum, cometido mesmo por estudantes razoavelmente preparados | Explora uma armadilha conhecida da área ou do tipo de questão |
| Reflete o erro mais típico que esta questão provoca | É a armadilha principal do item |

---

## 4. Métricas e linhas de base (resumo)

- **Principal:** Brier A–E por item: soma dos 5 erros quadráticos entre proporções previstas e observadas, com média entre os itens.
- **Acerto do principal distrator:** proporção de itens em que o distrator com maior probabilidade prevista é o distrator mais escolhido pelos participantes. Em empate previsto entre k distratores, crédito de 1/k. Reportada também por área.
- **Outras secundárias:** MAE; Spearman intraitem; Brier e Spearman **só entre distratores** (distribuição condicional ao erro); AUC para distratores com menos de 5%.
- **Linhas de base:** uniforme; média por área de 2025; Oracle (acerto médio de 2025 no gabarito, distratores iguais); Jev Choice; comprimento da alternativa como único preditor.
- **Estratificação:** por área, só descritiva em CN e MT (poucos itens).

## 5. Pendências

- [ ] Revisar a redação das perguntas e dos níveis.
- [ ] Confirmar "participante do ENEM" como população de referência.
- [ ] Definir a regra de combinação (quais perguntas entram e como os pesos são ajustados), antes de rodar 2025.
