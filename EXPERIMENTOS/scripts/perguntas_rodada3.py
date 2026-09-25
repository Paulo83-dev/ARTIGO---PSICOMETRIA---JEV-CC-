"""Perguntas da rodada 3 ao Jev: comparações entre pares ordenados de alternativas
(ver EXPERIMENTOS/rodada3_especificacao.md)."""

from itertools import permutations

from perguntas_rodada1 import LETRAS

PARES_ORDENADOS = list(permutations(LETRAS, 2))  # 20 pares: (A, B), (B, A), ...


def pergunta_par(primeira, segunda):
    # A ordem de apresentação é a ordem da instrução e das opções em `criteria`.
    return {
        "type": "choice",
        "instructions": {
            "pergunta": f"Entre a alternativa em `alternativas.{primeira}` e a alternativa em "
                        f"`alternativas.{segunda}`, qual delas seria escolhida por mais participantes do ENEM "
                        f"ao responder esta questão?",
            "foco": "Considere participantes reais do ENEM, com níveis variados de preparo, lendo a questão inteira "
                    "em condições de prova. Compare apenas essas duas alternativas.",
        },
        "criteria": {
            primeira: f"A alternativa em `alternativas.{primeira}` seria escolhida por mais participantes.",
            segunda: f"A alternativa em `alternativas.{segunda}` seria escolhida por mais participantes.",
        },
    }


def montar_perguntas(ids=None):
    """Devolve o mapa {id_pergunta: pergunta} com os 20 pares ordenados."""
    return {f"par_{a}_{b}": pergunta_par(a, b) for a, b in PARES_ORDENADOS}
