# Rodada 2: perguntas sobre o mecanismo de atração dos distratores

Status: **executada** no ENEM 2025 em 2026-09-25 (redação aprovada antes da execução).

## 1. Motivação (a partir da rodada 1 em 2025)

- As perguntas de atratividade, plausibilidade e correção (q1a, q1b, q2, q3, q4, q5, q6) têm correlação de 0,75 a 0,98 entre si, dentro do item: o Jev aplica, na prática, **um único juízo de "o quanto a alternativa está certa"**.
- Só **q7** (eco do texto, correlação ≈ 0,5 com q1b) e **q9** (equívoco comum, ≈ 0) trazem informação diferente. A q9 ordena bem os distratores (Spearman bruto +0,28) mesmo sendo independente de q1b.
- Por isso a combinação das 9 perguntas não superou a q1b sozinha.

**Objetivo da rodada 2:** perguntas sobre **por que** um distrator atrai, que o Jev possa responder **sem** julgar se a alternativa está correta. Cada pergunta corresponde a uma estratégia de construção de distratores ou a um fator de plausibilidade da literatura (ver `FICHAMENTO`, síntese S2: Nagai & Uto, 2025; Lee et al., 2025; Benedetto et al., 2025).

## 2. Desenho

| Elemento | Decisão |
|---|---|
| Modelo, `state`, idioma, formato | Iguais à rodada 1 (`jev-1.13.0`; `entrada` sem gabarito; português; caminho `` `alternativas.X` ``) |
| Dados | Só **2025**. O teste em 2024 continua reservado |
| Requisição | Uma por item, só com as perguntas novas (9 × 5 = 45). As respostas da rodada 1 são reaproveitadas pelo `registro_id` |
| Uso | Perguntas de **característica**: não são usadas sozinhas numa softmax das 5 alternativas (ver rodada 1) |

## 3. Análise prevista (definida antes de rodar)

1. **Spearman bruto entre distratores**, por pergunta (quanto a pergunta ordena os distratores na direção certa).
2. **Correlação com q1b dentro do item** (quanto a pergunta traz informação nova; queremos valores baixos).
3. **Modelo q1b + característica(s):** logit condicional nas 5 alternativas, com validação cruzada em 5 dobras, comparado com a q1b sozinha no Brier e nas métricas de distratores.
4. Para evitar sobreajuste, o modelo final pode acrescentar **no máximo duas** características à q1b, escolhidas pela validação cruzada.

## 4. As perguntas

Mesmas convenções da rodada 1. A alternativa **C** serve de exemplo.

---

### Q10: Combinação incorreta de informações

Noul. Estratégia 3 de Nagai & Uto (2025).

```json
{"pergunta": "A alternativa em `alternativas.C` junta informações que aparecem em partes diferentes do texto da questão, relacionando-as de um modo que o texto não sustenta?"}
```
- **true:** combina elementos presentes no texto, mas a relação estabelecida entre eles (causa, comparação, conclusão) não está no texto.
- **false:** não combina elementos do texto dessa forma, ou a relação que estabelece está no texto.

---

### Q11: Oposição

Noul. Estratégia 1 de Nagai & Uto (2025).

```json
{"pergunta": "A alternativa em `alternativas.C` afirma o contrário do que o texto da questão ou o conhecimento correto da área indicam?"}
```
- **true:** inverte o sentido de uma ideia do texto ou da área (nega o que é afirmado, troca causa e efeito, inverte uma relação).
- **false:** não inverte o sentido de nenhuma ideia do texto ou da área.

---

### Q12: Fora do tema

Noul. Estratégia 2 de Nagai & Uto (2025). Espera-se que indique **pouca** atração.

```json
{"pergunta": "A alternativa em `alternativas.C` trata de um assunto que não aparece no texto da questão nem no comando?"}
```
- **true:** fala de algo alheio ao tema do texto e do que foi perguntado.
- **false:** trata do tema do texto ou do que foi perguntado.

---

### Q13: Apelo do senso comum

Score. Rubrica de Lee et al. (2025), critério "apelo intuitivo"; fator "armadilha de familiaridade".

```json
{
  "pergunta": "Quanto a alternativa em `alternativas.C` soa correta pelo senso comum, sem depender do texto da questão?",
  "foco": "Imagine alguém que leu apenas a alternativa, sem o texto nem o comando. Julgue o quanto ela pareceria uma afirmação razoável."
}
```

| Situação | Sinais |
|---|---|
| Soa estranha ou absurda | Contraria o senso comum ou é incoerente em si |
| Soa pouco familiar | É uma afirmação técnica ou específica que poucos aceitariam sem pensar |
| Soa neutra | Não chama atenção nem como certa nem como errada |
| Soa razoável | É o tipo de afirmação que muitos aceitariam como verdadeira |
| Soa como verdade evidente | Parece óbvia, familiar ou politicamente correta; quase todos concordariam |

---

### Q14: Confusão conceitual

Score. Fator "sobreposição conceitual" de Lee et al. (2025).

```json
{
  "pergunta": "A alternativa em `alternativas.C` usa um conceito, termo ou relação que pode ser facilmente confundido com o que a questão pede?",
  "foco": "Considere conceitos vizinhos, termos parecidos ou relações próximas que um estudante poderia trocar entre si."
}
```

| Situação | Sinais |
|---|---|
| Nenhuma proximidade | Usa conceitos claramente distintos do que a questão pede |
| Proximidade vaga | Pertence à mesma área, mas a diferença é evidente |
| Proximidade moderada | Usa um conceito vizinho que exige atenção para distinguir |
| Proximidade forte | Usa um conceito ou termo que estudantes frequentemente confundem com o pedido |
| Quase indistinguível | A diferença para o que a questão pede é mínima e sutil |

---

### Q15: Generalização excessiva

Noul. Fator "supergeneralização" de Lee et al. (2025).

```json
{"pergunta": "A alternativa em `alternativas.C` apresenta uma ideia de forma mais ampla ou mais absoluta do que o texto da questão permite?"}
```
- **true:** estende uma ideia além do que o texto sustenta, por exemplo com "sempre", "todos", "nunca", "apenas", "qualquer", ou transformando um caso particular em regra.
- **false:** mantém o alcance que o texto sustenta.

---

### Q16: Conhecimento prévio no lugar do texto

Noul. Erro típico em questões de leitura: responder pelo que se sabe, e não pelo que o texto diz.

```json
{"pergunta": "A alternativa em `alternativas.C` afirma algo que é verdadeiro no mundo ou no senso comum, mas que não é dito nem sustentado pelo texto da questão?"}
```
- **true:** a afirmação pode ser verdadeira em geral, mas o texto não a apoia.
- **false:** a afirmação é apoiada pelo texto, ou é falsa em geral.

---

### Q17: Resposta a outra pergunta

Noul. Distrator que é "verdadeiro, mas não responde ao comando".

```json
{"pergunta": "A alternativa em `alternativas.C` seria uma resposta adequada para uma pergunta diferente sobre o mesmo texto, mas não para a pergunta que foi feita?"}
```
- **true:** responde a outro aspecto do texto (outra personagem, outro trecho, outra finalidade), e não ao que o comando pede.
- **false:** trata do que o comando pede, ou não serviria como resposta a nenhuma pergunta sobre o texto.

---

### Q18: Eco do comando

Score. Complementa a q7 (eco do texto): atração por palavras da **pergunta**, e não do texto de apoio.

```json
{
  "pergunta": "Quanto a alternativa em `alternativas.C` reaproveita palavras ou expressões do comando da questão, isto é, da pergunta propriamente dita?",
  "foco": "Considere apenas o comando, e não o texto de apoio. Avalie só a semelhança de superfície."
}
```

| Situação | Sinais |
|---|---|
| Nada do comando aparece | Nenhuma palavra ou expressão do comando |
| Relação distante | Tema do comando, com vocabulário próprio |
| Algumas palavras do comando | Repete um ou dois termos do comando |
| Muitas palavras do comando | Repete vários termos ou a estrutura da pergunta |
| Espelha o comando | Reformula a própria pergunta como resposta |

---

## 5. Pendências

- [ ] Revisar a redação das perguntas.
- [ ] Decidir se alguma pergunta deve sair (por exemplo, as que não se aplicam bem a MT: Q12, Q16, Q17).
