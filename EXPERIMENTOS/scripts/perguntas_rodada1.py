"""Perguntas da rodada 1 ao Jev (ver EXPERIMENTOS/rodada1_especificacao.md).

Cada pergunta é definida uma vez, com o marcador {alt} no lugar da letra;
`montar_perguntas()` gera as 5 versões (A–E) de cada uma.
"""

LETRAS = ["A", "B", "C", "D", "E"]


def _nivel(situacao, sinais):
    return {"situacao": situacao, "sinais": sinais}


PERGUNTAS = {
    # Q1a: atratividade por grau de convencimento
    "q1a": {
        "type": "score",
        "instructions": {
            "pergunta": "Quão atraente a alternativa em `alternativas.{alt}` pareceria como resposta "
                        "para um participante típico do ENEM tentando resolver esta questão?",
            "foco": "Avalie a alternativa isoladamente. Julgue a plausibilidade de ela ser escolhida, "
                    "inclusive por erro comum.",
        },
        "criteria": [
            "Esta alternativa é claramente incompatível com o enunciado; um participante atento a descartaria imediatamente.",
            "Esta alternativa pode atrair uma leitura superficial, mas um entendimento básico da questão a torna pouco plausível.",
            "Esta alternativa é plausível para participantes que cometam uma interpretação ou um cálculo equivocado.",
            "Esta alternativa é bastante convincente e pode competir com outras respostas para muitos participantes.",
            "Esta alternativa é fortemente convincente para quem tenta resolver a questão e tende a ser escolhida com frequência.",
        ],
    },
    # Q1b: atratividade por proporção de participantes
    "q1b": {
        "type": "score",
        "instructions": {
            "pergunta": "Quantos participantes do ENEM escolheriam a alternativa em `alternativas.{alt}` "
                        "como resposta desta questão?",
            "foco": "Considere participantes reais do ENEM, com níveis variados de preparo, lendo a questão "
                    "inteira em condições de prova. Julgue apenas a alternativa indicada.",
        },
        "criteria": [
            _nivel("Quase ninguém escolheria",
                   "Descabida mesmo numa leitura apressada; só seria marcada por engano ou chute puro"),
            _nivel("Poucos escolheriam",
                   "Parece errada para a maioria; atrai sobretudo quem não entendeu o comando ou chutou"),
            _nivel("Uma parcela considerável escolheria",
                   "Parece razoável numa leitura rápida, mas uma leitura atenta revela o problema"),
            _nivel("Muitos escolheriam",
                   "Parece a resposta certa para quem não domina bem o texto ou o conteúdo"),
            _nivel("A maioria escolheria",
                   "Parece a melhor resposta para quase todos os participantes"),
        ],
    },
    # Q2: plausibilidade como resposta
    "q2": {
        "type": "score",
        "instructions": {
            "pergunta": "Quão plausível a alternativa em `alternativas.{alt}` parece como resposta ao que a questão pede?",
            "foco": "Julgue se ela tem a aparência de uma resposta adequada ao comando, considerando o texto da questão. "
                    "Não julgue se ela está de fato correta.",
        },
        "criteria": [
            _nivel("Não tem relação com o que foi pedido",
                   "Fala de outro assunto ou não responde ao tipo de pergunta feita"),
            _nivel("Tem relação com o tema, mas claramente não serve como resposta",
                   "Menciona elementos do texto, mas não responde ao comando"),
            _nivel("Serve em parte como resposta",
                   "Responde ao comando de forma vaga, incompleta ou com um problema perceptível"),
            _nivel("Parece uma resposta adequada",
                   "Responde ao comando de forma coerente; se houver problema, ele é sutil"),
            _nivel("Parece a resposta mais adequada possível",
                   "Responde ao comando de forma completa, precisa e bem ajustada ao texto"),
        ],
    },
    # Q3: esforço para descartar
    "q3": {
        "type": "score",
        "instructions": {
            "pergunta": "O que um participante precisa fazer para perceber que a alternativa em "
                        "`alternativas.{alt}` não é a resposta desta questão?",
            "foco": "Considere o caminho mais curto para descartá-la. Se ela não puder ser descartada, "
                    "escolha o nível correspondente.",
        },
        "criteria": [
            _nivel("Basta ler a própria alternativa",
                   "É incoerente, absurda ou fora do tema, independentemente da questão"),
            _nivel("Basta ler o comando da questão",
                   "Não responde ao que foi pedido, mesmo sem ler o texto de apoio"),
            _nivel("É preciso ler com atenção o texto de apoio ou os dados do enunciado",
                   "Contradiz, distorce ou extrapola algo que está explícito no texto ou nos dados"),
            _nivel("É preciso interpretação aprofundada, conhecimento específico ou várias etapas de raciocínio",
                   "O erro só aparece com inferência, domínio do conteúdo ou cálculo"),
            _nivel("Não é possível descartá-la",
                   "Mesmo com leitura atenta e bom conhecimento, ela parece a resposta correta"),
        ],
    },
    # Q4: é a resposta correta?
    "q4": {
        "type": "noul",
        "instructions": {
            "pergunta": "A alternativa em `alternativas.{alt}` é a resposta correta desta questão?",
        },
        "criteria": {
            "true": "A alternativa responde corretamente ao comando, de acordo com o texto e o conhecimento da área.",
            "false": "A alternativa não responde corretamente ao comando.",
        },
    },
    # Q5: verdade local
    "q5": {
        "type": "noul",
        "instructions": {
            "pergunta": "O conteúdo da alternativa em `alternativas.{alt}`, considerado isoladamente, é verdadeiro?",
            "foco": "Julgue apenas se o que a alternativa afirma é verdadeiro ou compatível com o texto da questão "
                    "e com o conhecimento correto da área. Não importa se ela responde ao que o comando pede.",
        },
        "criteria": {
            "true": "O que a alternativa afirma é verdadeiro ou compatível com o texto, mesmo que não responda ao comando.",
            "false": "O que a alternativa afirma é falso, contradiz o texto ou não tem apoio nele.",
        },
    },
    # Q6: correção parcial
    "q6": {
        "type": "score",
        "instructions": {
            "pergunta": "Quanto do que a alternativa em `alternativas.{alt}` afirma está correto "
                        "em relação ao que a questão pede?",
        },
        "criteria": [
            _nivel("Nada está correto",
                   "O conteúdo inteiro é errado ou irrelevante para o comando"),
            _nivel("Contém um elemento correto, mas o essencial está errado",
                   "Aproveita uma ideia certa, mas a conclusão ou o foco estão errados"),
            _nivel("Mistura partes corretas e incorretas em proporção semelhante",
                   "Metade da afirmação procede e a outra metade não"),
            _nivel("Quase tudo está correto, com um erro ou omissão importante",
                   "Está perto da resposta, mas uma palavra, condição ou detalhe a torna errada"),
            _nivel("Está totalmente correta",
                   "Responde ao comando sem erro nem omissão"),
        ],
    },
    # Q7: eco do texto
    "q7": {
        "type": "score",
        "instructions": {
            "pergunta": "Quanto a alternativa em `alternativas.{alt}` reaproveita palavras, expressões ou ideias "
                        "que aparecem explicitamente no texto da questão?",
            "foco": "Avalie só a semelhança de superfície com o texto, e não se a alternativa está correta.",
        },
        "criteria": [
            _nivel("Nada do texto aparece", "Vocabulário e ideias sem relação com o texto"),
            _nivel("Trata do mesmo tema com vocabulário próprio", "Assunto próximo, mas sem palavras-chave do texto"),
            _nivel("Usa algumas palavras-chave do texto", "Termos importantes do texto aparecem, em frases diferentes"),
            _nivel("Parafraseia de perto um trecho do texto", "Reformula uma frase ou ideia específica do texto"),
            _nivel("Copia literalmente trechos do texto", "Repete palavra por palavra partes do texto"),
        ],
    },
    # Q9: equívoco comum
    "q9": {
        "type": "score",
        "instructions": {
            "pergunta": "A alternativa em `alternativas.{alt}` corresponde a um erro que estudantes do ensino médio "
                        "costumam cometer nesta questão?",
            "foco": "Considere erros típicos: leitura apressada, confusão entre conceitos parecidos, generalização "
                    "excessiva, inversão de causa e efeito, uso de conhecimento prévio no lugar do texto, "
                    "erro de cálculo comum.",
        },
        "criteria": [
            _nivel("Não reflete nenhum erro típico",
                   "A alternativa é correta, ou é um erro arbitrário que quase ninguém cometeria"),
            _nivel("Reflete um erro possível, mas pouco comum",
                   "Exige uma confusão incomum para ser escolhida"),
            _nivel("Reflete um erro comum entre estudantes com dificuldade no conteúdo",
                   "Atrai quem tem lacunas de conhecimento ou de leitura"),
            _nivel("Reflete um erro muito comum, cometido mesmo por estudantes razoavelmente preparados",
                   "Explora uma armadilha conhecida da área ou do tipo de questão"),
            _nivel("Reflete o erro mais típico que esta questão provoca",
                   "É a armadilha principal do item"),
        ],
    },
}


def _substituir(obj, alt):
    if isinstance(obj, str):
        return obj.replace("{alt}", alt)
    if isinstance(obj, dict):
        return {k: _substituir(v, alt) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substituir(v, alt) for v in obj]
    return obj


def montar_perguntas(ids=None):
    """Devolve o mapa {id_pergunta: pergunta} com as 5 versões de cada pergunta."""
    ids = ids or list(PERGUNTAS)
    return {
        f"{pid}_{alt}": _substituir(PERGUNTAS[pid], alt)
        for pid in ids
        for alt in LETRAS
    }
