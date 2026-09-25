"""Análise da rodada 2 no ano de desenvolvimento (2025), conforme EXPERIMENTOS/rodada2_especificacao.md.

1. Spearman bruto entre distratores de cada característica.
2. Correlação de cada característica com q1b dentro do item.
3. q1b + uma característica (logit condicional), com validação cruzada.
4. Procedimento de seleção de até duas características para somar à q1b, avaliado com
   validação cruzada aninhada (a seleção é refeita dentro de cada dobra externa, só com o treino).

Uso:
    python EXPERIMENTOS/scripts/analisar_rodada2.py --ano 2025 \
        --respostas1 EXPERIMENTOS/resultados/jev_rodada1_2025.jsonl \
        --respostas2 EXPERIMENTOS/resultados/jev_rodada2_2025.jsonl \
        --saida EXPERIMENTOS/resultados/analise_rodada2_2025
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from analisar_rodada1 import (  # noqa: E402
    LETRAS, N_DOBRAS, PERGUNTAS as PERGUNTAS_R1, RAIZ, SEMENTE, SoftmaxUmaVariavel, brier_medio,
    carregar, dobras_agrupadas, metricas, softmax, spearman_bruto_distratores,
)
from perguntas_rodada2 import PERGUNTAS as DEF_R2  # noqa: E402

PERGUNTAS_R2 = list(DEF_R2)
CANDIDATAS = ["q7", "q9"] + PERGUNTAS_R2  # características que podem ser somadas à q1b
MAX_CARACTERISTICAS = 2
LAMBDA = 0.001  # penalidade ridge fixa (pequena), para estabilidade


def carregar_rodada2(ids, caminho):
    resp = {}
    for linha in (RAIZ / caminho).read_text(encoding="utf-8").splitlines():
        reg = json.loads(linha)
        if reg["status_http"] == 200:
            resp[reg["registro_id"]] = reg["resposta"]["answers"]
    X2 = np.zeros((len(ids), 5, len(PERGUNTAS_R2)))
    for n, i in enumerate(ids):
        for j, pid in enumerate(PERGUNTAS_R2):
            for k, letra in enumerate(LETRAS):
                r = resp[i][f"{pid}_{letra}"]
                X2[n, k, j] = r["score"] if r["type"] == "score" else r["noul"]
    return X2


class LogitSimples:
    """p ∝ exp(Σ_j β_j·z_j), variáveis padronizadas no treino, penalidade ridge fixa."""

    def ajustar(self, S, Y):
        plano = S.reshape(-1, S.shape[2])
        self.media, self.dp = plano.mean(axis=0), plano.std(axis=0)
        self.dp[self.dp == 0] = 1.0
        Z = (S - self.media) / self.dp
        obj = lambda b: brier_medio(softmax(Z @ b), Y) + LAMBDA * float(b @ b)
        self.beta = minimize(obj, np.ones(S.shape[2]) * 0.5, method="L-BFGS-B").x
        return self

    def prever(self, S):
        return softmax(((S - self.media) / self.dp) @ self.beta)


def cv_brier(F, Y, grupos, area, semente):
    """Brier fora da dobra de um logit com as variáveis F, em 4 dobras internas."""
    d = dobras_agrupadas(grupos, area, n_dobras=4, semente=semente)
    erros = []
    for k in range(4):
        tr, te = d != k, d == k
        P = LogitSimples().ajustar(F[tr], Y[tr]).prever(F[te])
        erros.append(((P - Y[te]) ** 2).sum(axis=1))
    return float(np.concatenate(erros).mean())


def selecionar(base, feats, Y, grupos, area, semente=SEMENTE + 7):
    """Seleção progressiva: parte da q1b e acrescenta a característica que mais reduz o Brier
    (validação cruzada interna), até MAX_CARACTERISTICAS, parando se não houver melhora."""
    escolhidas = []
    atual = cv_brier(base[..., None], Y, grupos, area, semente)
    historico = [{"variaveis": ["q1b"], "brier_cv": atual}]
    for _ in range(MAX_CARACTERISTICAS):
        testes = {}
        for c in CANDIDATAS:
            if c in escolhidas:
                continue
            F = np.stack([base] + [feats[x] for x in escolhidas + [c]], axis=2)
            testes[c] = cv_brier(F, Y, grupos, area, semente)
        melhor = min(testes, key=testes.get)
        if testes[melhor] >= atual:
            break
        escolhidas.append(melhor)
        atual = testes[melhor]
        historico.append({"variaveis": ["q1b"] + escolhidas, "brier_cv": atual})
    return escolhidas, historico


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2025)
    ap.add_argument("--respostas1", required=True)
    ap.add_argument("--respostas2", required=True)
    ap.add_argument("--saida", required=True)
    args = ap.parse_args()

    ids, X1, comp, Y, gab, area, grupos = carregar(args.ano, args.respostas1)
    X2 = carregar_rodada2(ids, args.respostas2)
    feats = {p: X1[:, :, PERGUNTAS_R1.index(p)] for p in ["q7", "q9"]}
    feats.update({p: X2[:, :, j] for j, p in enumerate(PERGUNTAS_R2)})
    q1b = X1[:, :, PERGUNTAS_R1.index("q1b")]
    dobra = dobras_agrupadas(grupos, area)
    n = len(ids)

    # 1 e 2: poder de ordenar distratores e redundância com q1b (centrado por item)
    def corr_q1b(S):
        a = (S - S.mean(axis=1, keepdims=True)).ravel()
        b = (q1b - q1b.mean(axis=1, keepdims=True)).ravel()
        return float(spearmanr(a, b).statistic)

    diagnostico = {c: {**spearman_bruto_distratores(feats[c], Y, gab), "corr_q1b": corr_q1b(feats[c])}
                   for c in CANDIDATAS}

    # 3 e 4: previsões fora da dobra
    metodos = {}

    def validar(nome, fn):
        P = np.zeros((n, 5))
        for d in range(N_DOBRAS):
            tr, te = dobra != d, dobra == d
            P[te] = fn(tr, te)
        metodos[nome] = P

    validar("q1b", lambda tr, te: SoftmaxUmaVariavel().ajustar(q1b[tr], Y[tr]).prever(q1b[te]))
    for c in CANDIDATAS:
        F = np.stack([q1b, feats[c]], axis=2)
        validar(f"q1b+{c}", lambda tr, te, F=F: LogitSimples().ajustar(F[tr], Y[tr]).prever(F[te]))

    selecoes_por_dobra = []

    def selecao_aninhada(tr, te):
        esc, _ = selecionar(q1b[tr], {k: v[tr] for k, v in feats.items()}, Y[tr], grupos[tr], area[tr])
        selecoes_por_dobra.append(esc)
        F = np.stack([q1b] + [feats[x] for x in esc], axis=2)
        return LogitSimples().ajustar(F[tr], Y[tr]).prever(F[te])

    validar("selecao_ate_2 (aninhada)", selecao_aninhada)

    escolha_final, historico_final = selecionar(q1b, feats, Y, grupos, area)
    F_final = np.stack([q1b] + [feats[x] for x in escolha_final], axis=2)
    modelo_final = LogitSimples().ajustar(F_final, Y)

    resultados = {nome: metricas(P, Y, gab, area)[0] for nome, P in metodos.items()}
    saida = {
        "ano": args.ano, "n_itens": n,
        "diagnostico_caracteristicas": diagnostico,
        "resultados_fora_da_dobra": resultados,
        "selecao_em_cada_dobra_externa": selecoes_por_dobra,
        "selecao_final_em_todo_o_ano": {
            "variaveis": ["q1b"] + escolha_final,
            "historico": historico_final,
            "beta_padronizado": dict(zip(["q1b"] + escolha_final, map(float, modelo_final.beta))),
            "media": dict(zip(["q1b"] + escolha_final, map(float, modelo_final.media))),
            "dp": dict(zip(["q1b"] + escolha_final, map(float, modelo_final.dp))),
        },
        "previsoes_fora_da_dobra": {nome: {i: dict(zip(LETRAS, map(float, p))) for i, p in zip(ids, P)}
                                    for nome, P in metodos.items()},
    }
    prefixo = RAIZ / args.saida
    prefixo.with_suffix(".json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    prefixo.with_suffix(".md").write_text(markdown(saida), encoding="utf-8")
    print(markdown(saida))


def markdown(s):
    f = lambda v: "—" if v is None else f"{v:.4f}"
    L = [f"# Rodada 2: resultados, ENEM {s['ano']} ({s['n_itens']} itens)", "",
         "## Características: ordenação dos distratores e redundância com q1b", "",
         "Spearman bruto: escore sem ajuste × proporção real, só entre distratores (maior = melhor). "
         "Correlação com q1b: dentro do item (menor = mais informação nova).", "",
         "| Pergunta | Spearman bruto entre distratores | Correlação com q1b |", "|---|---|---|"]
    for c, d in sorted(s["diagnostico_caracteristicas"].items(), key=lambda kv: -kv[1]["spearman"]):
        L.append(f"| {c} | {d['spearman']:+.4f} | {d['corr_q1b']:+.2f} |")
    L += ["", "## Previsão fora da dobra (5 dobras)", "",
          "| Método | Brier | Spearman | Brier distr. | Spearman distr. | Principal distrator | AUC <5% |",
          "|---|---|---|---|---|---|---|"]
    for nome, r in sorted(s["resultados_fora_da_dobra"].items(), key=lambda kv: kv[1]["brier"]):
        L.append(f"| {nome} | {f(r['brier'])} | {f(r['spearman_intraitem'])} | {f(r['brier_distratores'])} | "
                 f"{f(r['spearman_distratores'])} | {f(r['acerto_principal_distrator'])} | {f(r['auc_nao_funcional'])} |")
    L += ["", "## Seleção de características",
          "", "Escolhas em cada dobra externa (só com o treino): "
          + "; ".join(", ".join(e) or "nenhuma" for e in s["selecao_em_cada_dobra_externa"]),
          "", "Seleção em todo o ano: " + ", ".join(s["selecao_final_em_todo_o_ano"]["variaveis"])]
    for h in s["selecao_final_em_todo_o_ano"]["historico"]:
        L.append(f"- {' + '.join(h['variaveis'])}: Brier CV interno {h['brier_cv']:.4f}")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
