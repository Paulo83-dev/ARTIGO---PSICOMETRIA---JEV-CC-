"""Análise da rodada 3 (comparações entre pares) no ano de desenvolvimento, conforme
EXPERIMENTOS/rodada3_especificacao.md.

Uso:
    python EXPERIMENTOS/scripts/analisar_rodada3.py --ano 2025 \
        --respostas1 EXPERIMENTOS/resultados/jev_rodada1_2025.jsonl \
        --respostas3 EXPERIMENTOS/resultados/jev_rodada3_2025.jsonl \
        --saida EXPERIMENTOS/resultados/analise_rodada3_2025
"""

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).parent))
from analisar_rodada1 import (  # noqa: E402
    LETRAS, N_DOBRAS, PERGUNTAS as PERGUNTAS_R1, RAIZ, SoftmaxUmaVariavel, carregar, dobras_agrupadas, metricas,
)
from analisar_rodada2 import LogitSimples  # noqa: E402
from avaliar_teste import bootstrap_grupos  # noqa: E402

LAMBDA_BT = 0.01
PARES = list(combinations(range(5), 2))  # 10 pares não ordenados (i < j)


def carregar_pares(ids, caminho):
    """Devolve P1[n, i, j] = probabilidade de i quando i é apresentada primeiro contra j."""
    resp = {}
    for linha in (RAIZ / caminho).read_text(encoding="utf-8").splitlines():
        reg = json.loads(linha)
        if reg["status_http"] == 200:
            resp[reg["registro_id"]] = reg["resposta"]["answers"]
    P1 = np.full((len(ids), 5, 5), np.nan)
    for n, item in enumerate(ids):
        for i in range(5):
            for j in range(5):
                if i != j:
                    a = resp[item][f"par_{LETRAS[i]}_{LETRAS[j]}"]
                    P1[n, i, j] = a["probabilities"][LETRAS[i]]
    return P1


def combinar_ordens(P1):
    """p[n, i, j] = ½·[P(i | i primeiro) + P(i | j primeiro)] = ½·[P1[i,j] + 1 − P1[j,i]]."""
    p = np.full_like(P1, np.nan)
    for i in range(5):
        for j in range(5):
            if i != j:
                p[:, i, j] = 0.5 * (P1[:, i, j] + 1 - P1[:, j, i])
    return p


def bradley_terry(p_item):
    """Forças θ (soma zero) por máxima verossimilhança com resultados suaves e ridge λ."""
    def obj(theta):
        v = 0.0
        for i, j in PARES:
            d = theta[i] - theta[j]
            v -= p_item[i, j] * -np.logaddexp(0, -d) + (1 - p_item[i, j]) * -np.logaddexp(0, d)
        return v + LAMBDA_BT * float(theta @ theta)
    th = minimize(obj, np.zeros(5), method="L-BFGS-B").x
    return th - th.mean()


def diagnosticos(P1, p, Y, gab):
    n = len(Y)
    consist, primeiro, total = [], 0, 0
    acertos = {"so_distratores": [], "com_correta": [],
               "so_distratores_dif>10pp": [], "com_correta_dif>10pp": []}
    for k in range(n):
        for i, j in PARES:
            a, b = P1[k, i, j], P1[k, j, i]  # prob. da 1ª apresentada em cada ordem
            primeiro += (a > 0.5) + (b > 0.5)
            total += 2
            if a != 0.5 and b != 0.5:
                consist.append((a > 0.5) == (b < 0.5))  # mesma alternativa preferida nas duas ordens
            if p[k, i, j] == 0.5 or Y[k, i] == Y[k, j]:
                continue
            certo = (p[k, i, j] > 0.5) == (Y[k, i] > Y[k, j])
            tipo = "com_correta" if gab[k] in (i, j) else "so_distratores"
            acertos[tipo].append(certo)
            if abs(Y[k, i] - Y[k, j]) > 0.10:
                acertos[tipo + "_dif>10pp"].append(certo)
    return {
        "consistencia_entre_ordens": float(np.mean(consist)),
        "proporcao_escolhe_a_primeira": float(primeiro / total),
        "acuracia_por_par": {t: {"acuracia": float(np.mean(v)), "n_pares": len(v)} for t, v in acertos.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2025)
    ap.add_argument("--respostas1", required=True)
    ap.add_argument("--respostas3", required=True)
    ap.add_argument("--saida", required=True)
    args = ap.parse_args()

    ids, X1, _, Y, gab, area, grupos = carregar(args.ano, args.respostas1)
    P1 = carregar_pares(ids, args.respostas3)
    p = combinar_ordens(P1)
    theta = np.array([bradley_terry(p[k]) for k in range(len(ids))])
    borda = np.nansum(p, axis=2)
    q1b = X1[:, :, PERGUNTAS_R1.index("q1b")]
    dobra = dobras_agrupadas(grupos, area)
    n = len(ids)

    metodos = {}

    def validar(nome, fn):
        P = np.zeros((n, 5))
        for d in range(N_DOBRAS):
            tr, te = dobra != d, dobra == d
            P[te] = fn(tr, te)
        metodos[nome] = P

    uma = lambda S: (lambda tr, te: SoftmaxUmaVariavel().ajustar(S[tr], Y[tr]).prever(S[te]))
    validar("q1b", uma(q1b))
    validar("pares_bradley_terry", uma(theta))
    validar("pares_borda", uma(borda))
    F = np.stack([q1b, theta], axis=2)
    validar("q1b+pares_bradley_terry", lambda tr, te: LogitSimples().ajustar(F[tr], Y[tr]).prever(F[te]))

    resultados = {nome: metricas(P, Y, gab, area)[0] for nome, P in metodos.items()}
    brier = {nome: ((P - Y) ** 2).sum(axis=1) for nome, P in metodos.items()}
    comparacoes = {}
    for nome in metodos:
        if nome == "q1b":
            continue
        d = brier[nome] - brier["q1b"]
        bs = bootstrap_grupos(d, grupos, 5000, 2025)
        ic = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        comparacoes[nome] = {"diferenca_brier": float(d.mean()), "ic95": ic, "substitui_q1b": ic[1] < 0}

    saida = {
        "ano": args.ano, "n_itens": n,
        "diagnosticos": diagnosticos(P1, p, Y, gab),
        "resultados_fora_da_dobra": resultados,
        "comparacao_com_q1b": comparacoes,
        "parametros_ajustados_em_todo_o_ano": {
            "pares_bradley_terry": SoftmaxUmaVariavel().ajustar(theta, Y).parametros(),
            "pares_borda": SoftmaxUmaVariavel().ajustar(borda, Y).parametros(),
        },
        "forcas_bradley_terry": {i: dict(zip(LETRAS, map(float, t))) for i, t in zip(ids, theta)},
        "previsoes_fora_da_dobra": {nome: {i: dict(zip(LETRAS, map(float, pp))) for i, pp in zip(ids, P)}
                                    for nome, P in metodos.items()},
    }
    prefixo = RAIZ / args.saida
    prefixo.with_suffix(".json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    prefixo.with_suffix(".md").write_text(markdown(saida), encoding="utf-8")
    print(markdown(saida))


def markdown(s):
    f = lambda v: "—" if v is None else f"{v:.4f}"
    dg = s["diagnosticos"]
    L = [f"# Rodada 3: comparações entre pares, ENEM {s['ano']} ({s['n_itens']} itens)", "",
         "## Diagnósticos", "",
         f"- Consistência entre as duas ordens: {dg['consistencia_entre_ordens']:.4f}",
         f"- Proporção em que o Jev escolhe a alternativa apresentada primeiro: {dg['proporcao_escolhe_a_primeira']:.4f}",
         "", "| Tipo de par | Acurácia | Pares |", "|---|---|---|"]
    for t, v in dg["acuracia_por_par"].items():
        L.append(f"| {t} | {v['acuracia']:.4f} | {v['n_pares']} |")
    L += ["", "## Previsão fora da dobra (5 dobras)", "",
          "| Método | Brier | Spearman | Brier distr. | Spearman distr. | Principal distrator | AUC <5% |",
          "|---|---|---|---|---|---|---|"]
    for nome, r in sorted(s["resultados_fora_da_dobra"].items(), key=lambda kv: kv[1]["brier"]):
        L.append(f"| {nome} | {f(r['brier'])} | {f(r['spearman_intraitem'])} | {f(r['brier_distratores'])} | "
                 f"{f(r['spearman_distratores'])} | {f(r['acerto_principal_distrator'])} | {f(r['auc_nao_funcional'])} |")
    L += ["", "## Regra de decisão: diferença de Brier em relação à q1b", "",
          "| Método | Diferença | IC 95% | Substitui a q1b? |", "|---|---|---|---|"]
    for nome, c in s["comparacao_com_q1b"].items():
        L.append(f"| {nome} | {c['diferenca_brier']:+.5f} | [{c['ic95'][0]:+.5f}; {c['ic95'][1]:+.5f}] | "
                 f"{'sim' if c['substitui_q1b'] else 'não'} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
