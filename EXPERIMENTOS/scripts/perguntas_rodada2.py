"""Perguntas da rodada 2 ao Jev: mecanismos de atração dos distratores
(ver EXPERIMENTOS/rodada2_especificacao.md)."""

from perguntas_rodada1 import LETRAS, _nivel, _substituir  # noqa: F401

PERGUNTAS = {
    # Q10: combinação incorreta de informações
    "q10": {
        "type": "noul",
        "instructions": {
            "pergunta": "A alternativa em `alternativas.{alt}` junta informações que aparecem em partes diferentes "
                        "do texto da questão, relacionando-as de um modo que o texto não sustenta?",
        },
        "criteria": {
            "true": "Combina elementos presentes no texto, mas a relação estabelecida entre eles (causa, comparação, "
                    "conclusão) não está no texto.",
            "false": "Não combina elementos do texto dessa forma, ou a relação que estabelece está no texto.",
        },
    },
    # Q11: oposição
    "q11": {
        "type": "noul",
        "instructions": {
            "pergunta": "A alternativa em `alternativas.{alt}` afirma o contrário do que o texto da questão "
                        "ou o conhecimento correto da área indicam?",
        },
        "criteria": {
            "true": "Inverte o sentido de uma ideia do texto ou da área (nega o que é afirmado, troca causa e efeito, "
                    "inverte uma relação).",
            "false": "Não inverte o sentido de nenhuma ideia do texto ou da área.",
        },
    },
    # Q12: fora do tema
    "q12": {
        "type": "noul",
        "instructions": {
            "pergunta": "A alternativa em `alternativas.{alt}` trata de um assunto que não aparece no texto "
                        "da questão nem no comando?",
        },
        "criteria": {
            "true": "Fala de algo alheio ao tema do texto e do que foi perguntado.",
            "false": "Trata do tema do texto ou do que foi perguntado.",
        },
    },
    # Q13: apelo do senso comum
    "q13": {
        "type": "score",
        "instructions": {
            "pergunta": "Quanto a alternativa em `alternativas.{alt}` soa correta pelo senso comum, "
                        "sem depender do texto da questão?",
            "foco": "Imagine alguém que leu apenas a alternativa, sem o texto nem o comando. "
                    "Julgue o quanto ela pareceria uma afirmação razoável.",
        },
        "criteria": [
            _nivel("Soa estranha ou absurda", "Contraria o senso comum ou é incoerente em si"),
            _nivel("Soa pouco familiar",
                   "É uma afirmação técnica ou específica que poucos aceitariam sem pensar"),
            _nivel("Soa neutra", "Não chama atenção nem como certa nem como errada"),
            _nivel("Soa razoável", "É o tipo de afirmação que muitos aceitariam como verdadeira"),
            _nivel("Soa como verdade evidente",
                   "Parece óbvia, familiar ou politicamente correta; quase todos concordariam"),
        ],
    },
    # Q14: confusão conceitual
    "q14": {
        "type": "score",
        "instructions": {
            "pergunta": "A alternativa em `alternativas.{alt}` usa um conceito, termo ou relação que pode ser "
                        "facilmente confundido com o que a questão pede?",
            "foco": "Considere conceitos vizinhos, termos parecidos ou relações próximas que um estudante "
                    "poderia trocar entre si.",
        },
        "criteria": [
            _nivel("Nenhuma proximidade", "Usa conceitos claramente distintos do que a questão pede"),
            _nivel("Proximidade vaga", "Pertence à mesma área, mas a diferença é evidente"),
            _nivel("Proximidade moderada", "Usa um conceito vizinho que exige atenção para distinguir"),
            _nivel("Proximidade forte",
                   "Usa um conceito ou termo que estudantes frequentemente confundem com o pedido"),
            _nivel("Quase indistinguível", "A diferença para o que a questão pede é mínima e sutil"),
        ],
    },
    # Q15: generalização excessiva
    "q15": {
        "type": "noul",
        "instructions": {
            "pergunta": "A alternativa em `alternativas.{alt}` apresenta uma ideia de forma mais ampla ou mais "
                        "absoluta do que o texto da questão permite?",
        },
        "criteria": {
            "true": "Estende uma ideia além do que o texto sustenta, por exemplo com \"sempre\", \"todos\", "
                    "\"nunca\", \"apenas\", \"qualquer\", ou transformando um caso particular em regra.",
            "false": "Mantém o alcance que o texto sustenta.",
        },
    },
    # Q16: conhecimento prévio no lugar do texto
    "q16": {
        "type": "noul",
        "instructions": {
            "pergunta": "A alternativa em `alternativas.{alt}` afirma algo que é verdadeiro no mundo ou no senso "
                        "comum, mas que não é dito nem sustentado pelo texto da questão?",
        },
        "criteria": {
            "true": "A afirmação pode ser verdadeira em geral, mas o texto não a apoia.",
            "false": "A afirmação é apoiada pelo texto, ou é falsa em geral.",
        },
    },
    # Q17: resposta a outra pergunta
    "q17": {
        "type": "noul",
        "instructions": {
            "pergunta": "A alternativa em `alternativas.{alt}` seria uma resposta adequada para uma pergunta "
                        "diferente sobre o mesmo texto, mas não para a pergunta que foi feita?",
        },
        "criteria": {
            "true": "Responde a outro aspecto do texto (outra personagem, outro trecho, outra finalidade), "
                    "e não ao que o comando pede.",
            "false": "Trata do que o comando pede, ou não serviria como resposta a nenhuma pergunta sobre o texto.",
        },
    },
    # Q18: eco do comando
    "q18": {
        "type": "score",
        "instructions": {
            "pergunta": "Quanto a alternativa em `alternativas.{alt}` reaproveita palavras ou expressões do comando "
                        "da questão, isto é, da pergunta propriamente dita?",
            "foco": "Considere apenas o comando, e não o texto de apoio. Avalie só a semelhança de superfície.",
        },
        "criteria": [
            _nivel("Nada do comando aparece", "Nenhuma palavra ou expressão do comando"),
            _nivel("Relação distante", "Tema do comando, com vocabulário próprio"),
            _nivel("Algumas palavras do comando", "Repete um ou dois termos do comando"),
            _nivel("Muitas palavras do comando", "Repete vários termos ou a estrutura da pergunta"),
            _nivel("Espelha o comando", "Reformula a própria pergunta como resposta"),
        ],
    },
}


def montar_perguntas(ids=None):
    """Devolve o mapa {id_pergunta: pergunta} com as 5 versões de cada pergunta."""
    ids = ids or list(PERGUNTAS)
    return {f"{pid}_{alt}": _substituir(PERGUNTAS[pid], alt) for pid in ids for alt in LETRAS}
