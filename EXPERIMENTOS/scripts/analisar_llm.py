"""Análise da comparação com o LLM (ver EXPERIMENTOS/comparacao_llm_especificacao.md).

Modo desenvolvimento (2025): ajusta temperaturas e pesos do LLM por validação cruzada nas mesmas
5 dobras, compara com o Jev fora da dobra e grava o congelamento dos parâmetros do LLM.

    python EXPERIMENTOS/scripts/analisar_llm.py desenvolvimento --ano 2025 \
        --llm EXPERIMENTOS/resultados/llm_glm_2025.jsonl \
        --jev1 EXPERIMENTOS/resultados/jev_rodada1_2025.jsonl --jev3 EXPERIMENTOS/resultados/jev_rodada3_2025.jsonl \
        --saida EXPERIMENTOS/resultados/analise_llm_2025 --congelamento EXPERIMENTOS/congelamento_llm_2024.json

Modo teste (2024): aplica os parâmetros congelados, sem ajuste, e calcula as comparações C1–C4.

    python EXPERIMENTOS/scripts/analisar_llm.py teste --congelamento EXPERIMENTOS/congelamento_llm_2024.json \
        --llm EXPERIMENTOS/resultados/llm_glm_2024.jsonl --teste-jev EXPERIMENTOS/resultados/teste_2024.json \
        --saida EXPERIMENTOS/resultados/comparacao_llm_2024
"""

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from analisar_rodada1 import (  # noqa: E402
    LETRAS, N_DOBRAS, PERGUNTAS as PERGUNTAS_R1, RAIZ, SoftmaxUmaVariavel, brier_medio, carregar,
    dobras_agrupadas, metricas, softmax,
)
from analisar_rodada2 import LogitSimples  # noqa: E402
from analisar_rodada3 import bradley_terry, carregar_pares, combinar_ordens, diagnosticos, tabela_pares  # noqa: E402
from avaliar_teste import bootstrap_grupos  # noqa: E402
from tabelas import COLUNAS_METRICAS, por_area, tabela  # noqa: E402

GRADE_T = np.exp(np.linspace(np.log(0.1), np.log(100), 701))
PRECO_JEV_POR_MTOK = 0.042  # US$ por milhão de tokens de entrada (docs.typesafe.ai/models, jev-1.13.0)


# ---------------------------------------------------------------- dados do LLM

def carregar_llm(ids, caminho):
    """Último registro válido de cada (item, método, chave)."""
    reg = {}
    for linha in (RAIZ / caminho).read_text(encoding="utf-8").splitlines():
        r = json.loads(linha)
        if r["status_http"] == 200 and r["probabilidades"]:
            reg[(r["registro_id"], r["metodo"], r["chave"])] = r
    n = len(ids)
    logp = np.zeros((n, 5, 5))  # [item, rotação, alternativa original]
    q1b = np.zeros((n, 5))
    P1 = np.full((n, 5, 5), np.nan)
    uso = {"custo_usd": 0.0, "segundos": [], "tokens_entrada": 0, "chamadas": 0, "com_raciocinio": 0}
    for a, rid in enumerate(ids):
        for r in range(5):
            x = reg[(rid, "A_letras", f"rot{r}")]
            for pos, orig in enumerate(x["ordem_exibida"]):
                logp[a, r, LETRAS.index(orig)] = math.log(max(x["probabilidades"][LETRAS[pos]], 1e-12))
        for k, letra in enumerate(LETRAS):
            p = reg[(rid, "B_q1b", letra)]["probabilidades"]
            q1b[a, k] = sum(int(nivel) * v for nivel, v in p.items())
        for i in range(5):
            for j in range(5):
                if i != j:
                    P1[a, i, j] = reg[(rid, "B_pares", f"{LETRAS[i]}_{LETRAS[j]}")]["probabilidades"][LETRAS[i]]
    for (rid, _, _), x in reg.items():
        if rid in ids:
            uso["custo_usd"] += x["custo_usd"] or 0.0
            uso["segundos"].append(x["segundos"])
            uso["tokens_entrada"] += x["tokens_entrada"] or 0
            uso["chamadas"] += 1
            uso["com_raciocinio"] += (x["tokens_raciocinio"] or 0) > 0
    uso["segundos_mediana_por_chamada"] = float(np.median(uso.pop("segundos")))
    return logp, q1b, P1, uso


class LetrasRotacoes:
    """p = média das rotações de softmax(log p / T), com T ajustado por grade."""

    @staticmethod
    def prever_T(logp, T):
        return np.mean([softmax(logp[:, r, :] / T) for r in range(logp.shape[1])], axis=0)

    def ajustar(self, logp, Y):
        erros = [brier_medio(self.prever_T(logp, T), Y) for T in GRADE_T]
        self.T = float(GRADE_T[int(np.argmin(erros))])
        return self

    def prever(self, logp):
        return self.prever_T(logp, self.T)


def uso_jev(caminhos, ids):
    tokens = 0
    for c in caminhos:
        for linha in (RAIZ / c).read_text(encoding="utf-8").splitlines():
            r = json.loads(linha)
            if r["status_http"] == 200 and r["registro_id"] in ids:
                tokens += r["resposta"]["usage"]["input_tokens"]
    return {"tokens_entrada": tokens, "custo_usd": tokens / 1e6 * PRECO_JEV_POR_MTOK}


# ---------------------------------------------------------------- desenvolvimento

def desenvolvimento(args):
    ids, X1, _, Y, gab, area, grupos = carregar(args.ano, args.jev1)
    logp, q1b_llm, P1_llm, uso = carregar_llm(ids, args.llm)
    theta_llm = np.array([bradley_terry(p) for p in combinar_ordens(P1_llm)])
    p_jev = combinar_ordens(carregar_pares(ids, args.jev3))
    theta_jev = np.array([bradley_terry(p) for p in p_jev])
    q1b_jev = X1[:, :, PERGUNTAS_R1.index("q1b")]
    dobra = dobras_agrupadas(grupos, area)
    n = len(ids)

    F_llm = np.stack([q1b_llm, theta_llm], axis=2)
    F_jev = np.stack([q1b_jev, theta_jev], axis=2)
    construtores = {
        "LLM A (letras)": lambda: (LetrasRotacoes(), logp),
        "LLM B q1b": lambda: (SoftmaxUmaVariavel(), q1b_llm),
        "LLM B pares": lambda: (SoftmaxUmaVariavel(), theta_llm),
        "LLM B q1b+pares": lambda: (LogitSimples(), F_llm),
        "Jev q1b": lambda: (SoftmaxUmaVariavel(), q1b_jev),
        "Jev q1b+pares": lambda: (LogitSimples(), F_jev),
    }
    metodos = {}
    for nome, cons in construtores.items():
        P = np.zeros((n, 5))
        for d in range(N_DOBRAS):
            tr, te = dobra != d, dobra == d
            modelo, S = cons()
            P[te] = modelo.ajustar(S[tr], Y[tr]).prever(S[te])
        metodos[nome] = P

    resultados = {nome: metricas(P, Y, gab, area)[0] for nome, P in metodos.items()}
    saida = {"ano": args.ano, "n_itens": n, "resultados_fora_da_dobra": resultados,
             "diagnosticos_pares_llm": diagnosticos(P1_llm, combinar_ordens(P1_llm), Y, gab),
             "uso_llm": uso, "uso_jev": uso_jev([args.jev1, args.jev3], set(ids))}
    grava(args.saida, saida, markdown_dev(saida))

    # Congelamento: parâmetros do LLM ajustados em todo o ano de desenvolvimento
    letras = LetrasRotacoes().ajustar(logp, Y)
    s_q1b = SoftmaxUmaVariavel().ajustar(q1b_llm, Y)
    s_par = SoftmaxUmaVariavel().ajustar(theta_llm, Y)
    comb = LogitSimples().ajustar(F_llm, Y)
    cfg = {
        "descricao": "Parâmetros do LLM de comparação ajustados só no ENEM 2025, a aplicar uma única vez ao ENEM 2024. "
                     "Ver comparacao_llm_especificacao.md.",
        "data_congelamento": date.today().isoformat(),
        "ano_desenvolvimento": args.ano, "ano_teste": 2024,
        "modelo": "z-ai/glm-5.3-flash", "provedor": "Together",
        "requisicoes": "python EXPERIMENTOS/scripts/rodar_llm.py --ano 2024 --saida EXPERIMENTOS/resultados/llm_glm_2024.jsonl",
        "metodos_llm": {
            "LLM A (letras)": {"tipo": "letras", "temperatura": letras.T},
            "LLM B q1b": {"tipo": "softmax", "variavel": "q1b", "beta": s_q1b.parametros()["beta"]},
            "LLM B pares": {"tipo": "softmax", "variavel": "pares", "beta": s_par.parametros()["beta"]},
            "LLM B q1b+pares": {"tipo": "logit", "media": comb.media.tolist(), "dp": comb.dp.tolist(),
                                "beta_padronizado": comb.beta.tolist()},
        },
        "comparacoes": [
            {"id": "C1", "a": "q1b+pares (principal)", "b": "LLM A (letras)",
             "descricao": "Jev q1b + pares × LLM, método A (letras)"},
            {"id": "C2", "a": "q1b+pares (principal)", "b": "LLM B q1b+pares",
             "descricao": "Jev q1b + pares × LLM, método B (q1b + pares)"},
            {"id": "C3", "a": "q1b", "b": "LLM B q1b", "descricao": "Jev q1b × LLM q1b (método B)"},
            {"id": "C4", "a": "LLM A (letras)", "b": "oracle (usa gabarito)",
             "descricao": "LLM método A × Oracle"},
        ],
        "bootstrap": {"reamostragens": 5000, "semente": 2024,
                      "unidade": "grupo de itens (itens que compartilham texto de apoio são sorteados juntos)"},
    }
    (RAIZ / args.congelamento).write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(markdown_dev(saida))


# ---------------------------------------------------------------- teste

def teste(args):
    cfg = json.loads((RAIZ / args.congelamento).read_text(encoding="utf-8"))
    jev = json.loads((RAIZ / args.teste_jev).read_text(encoding="utf-8"))
    ano = cfg["ano_teste"]
    ids = sorted(jev["previsoes"][next(iter(jev["previsoes"]))])
    _, _, _, Y, gab, area, grupos = carregar(ano, args.jev1)
    logp, q1b_llm, P1_llm, uso = carregar_llm(ids, args.llm)
    theta_llm = np.array([bradley_terry(p) for p in combinar_ordens(P1_llm)])

    m = cfg["metodos_llm"]
    metodos = {nome: np.array([[P[i][k] for k in LETRAS] for i in ids]) for nome, P in jev["previsoes"].items()}
    metodos["LLM A (letras)"] = LetrasRotacoes.prever_T(logp, m["LLM A (letras)"]["temperatura"])
    metodos["LLM B q1b"] = softmax(m["LLM B q1b"]["beta"] * q1b_llm)
    metodos["LLM B pares"] = softmax(m["LLM B pares"]["beta"] * theta_llm)
    c = m["LLM B q1b+pares"]
    Z = (np.stack([q1b_llm, theta_llm], axis=2) - np.array(c["media"])) / np.array(c["dp"])
    metodos["LLM B q1b+pares"] = softmax(Z @ np.array(c["beta_padronizado"]))

    brier = {nome: ((P - Y) ** 2).sum(axis=1) for nome, P in metodos.items()}
    b = cfg["bootstrap"]
    comparacoes = []
    for comp in cfg["comparacoes"]:
        d = brier[comp["a"]] - brier[comp["b"]]
        bs = bootstrap_grupos(d, grupos, b["reamostragens"], b["semente"])
        comparacoes.append({**comp, "diferenca_brier": float(d.mean()),
                            "ic95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]})
    saida = {"ano": ano, "n_itens": len(ids), "comparacoes": comparacoes,
             "resultados": {nome: metricas(P, Y, gab, area)[0] for nome, P in metodos.items()},
             "diagnosticos_pares_llm": diagnosticos(P1_llm, combinar_ordens(P1_llm), Y, gab),
             "diagnosticos_pares_jev": jev["diagnosticos_pares"],
             "uso_llm": uso, "uso_jev": uso_jev([args.jev1, args.jev3], set(ids)),
             "previsoes_llm": {nome: {i: dict(zip(LETRAS, map(float, p))) for i, p in zip(ids, metodos[nome])}
                               for nome in m}}
    grava(args.saida, saida, markdown_teste(saida))
    print(markdown_teste(saida))


# ---------------------------------------------------------------- relatórios

def grava(prefixo, dados, md):
    p = RAIZ / prefixo
    p.with_suffix(".json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    p.with_suffix(".md").write_text(md, encoding="utf-8")


def tabela_uso(s):
    ul, uj, n = s["uso_llm"], s["uso_jev"], s["n_itens"]
    return ["| Modelo | Chamadas | Tokens de entrada | Custo total (US$) ↓ | Custo por item (US$) ↓ |",
            "|---|---|---|---|---|",
            f"| Jev (rodadas 1 e 3) | {2 * n} | {uj['tokens_entrada']:,} | **{uj['custo_usd']:.4f}** | "
            f"**{uj['custo_usd'] / n:.5f}** |",
            f"| LLM (métodos A e B) | {ul['chamadas']} | {ul['tokens_entrada']:,} | {ul['custo_usd']:.4f} | "
            f"{ul['custo_usd'] / n:.5f} |",
            "", f"LLM: mediana de {ul['segundos_mediana_por_chamada']:.2f} s por chamada; "
            f"{ul['com_raciocinio']} de {ul['chamadas']} chamadas ({ul['com_raciocinio'] / ul['chamadas']:.0%}) "
            "tiveram tokens de raciocínio. Custo do Jev calculado pelos tokens de entrada a US$ 0,042 por milhão."]


def markdown_dev(s):
    L = [f"# Comparação com o LLM: desenvolvimento, ENEM {s['ano']} ({s['n_itens']} itens, 5 dobras)", "",
         "↓ menor é melhor; ↑ maior é melhor; melhor valor de cada coluna em negrito.", "",
         "## Previsão fora da dobra", ""]
    L += tabela(sorted(s["resultados_fora_da_dobra"].items(), key=lambda kv: kv[1]["brier"]), COLUNAS_METRICAS)
    L += ["", "## Comparações entre pares do LLM", ""] + tabela_pares(s["diagnosticos_pares_llm"])
    L += ["", "## Custo", ""] + tabela_uso(s)
    return "\n".join(L) + "\n"


def markdown_teste(s):
    L = [f"# Comparação com o LLM: teste, ENEM {s['ano']} ({s['n_itens']} itens)", "",
         "Comparação acrescentada depois do teste principal, com parâmetros do LLM congelados em 2025.", "",
         "↓ menor é melhor; ↑ maior é melhor; melhor valor de cada coluna em negrito.", "",
         "## Comparações (diferença de Brier, a − b; negativo favorece a)", "",
         "| Id | Comparação | Diferença | IC 95% |", "|---|---|---|---|"]
    for c in s["comparacoes"]:
        L.append(f"| {c['id']} | {c['descricao']} | {c['diferenca_brier']:+.5f} | "
                 f"[{c['ic95'][0]:+.5f}; {c['ic95'][1]:+.5f}] |")
    ordem = sorted(s["resultados"].items(), key=lambda kv: kv[1]["brier"])
    L += ["", "## Métricas", ""] + tabela(ordem, COLUNAS_METRICAS)
    areas = sorted(next(iter(s["resultados"].values()))["brier_por_area"])
    L += ["", "## Brier por área", ""] + por_area(ordem, "brier_por_area", areas, "menor")
    L += ["", "## Comparações entre pares", "", "**Jev**", ""] + tabela_pares(s["diagnosticos_pares_jev"])
    L += ["", "**LLM**", ""] + tabela_pares(s["diagnosticos_pares_llm"])
    L += ["", "## Custo", ""] + tabela_uso(s)
    return "\n".join(L) + "\n"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["desenvolvimento", "teste"])
    ap.add_argument("--ano", type=int, default=2025)
    ap.add_argument("--llm", required=True)
    ap.add_argument("--jev1", default=None)
    ap.add_argument("--jev3", default=None)
    ap.add_argument("--teste-jev", default=None)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--congelamento", required=True)
    args = ap.parse_args()
    if args.modo == "desenvolvimento":
        desenvolvimento(args)
    else:
        args.jev1 = args.jev1 or "EXPERIMENTOS/resultados/jev_rodada1_2024.jsonl"
        args.jev3 = args.jev3 or "EXPERIMENTOS/resultados/jev_rodada3_2024.jsonl"
        teste(args)


if __name__ == "__main__":
    main()
