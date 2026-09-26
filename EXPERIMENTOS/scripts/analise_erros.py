"""Análise descritiva de onde o método erra, feita depois do teste (nenhum parâmetro é ajustado).

1. Taxa de acerto prevista (probabilidade dada ao gabarito) × taxa de acerto real, e × parâmetro b da TRI.
2. Quanto do Brier está na alternativa correta; Brier de uma "Oracle informada", que conhece o gabarito e a
   taxa real de acerto de cada questão e divide o resto igualmente entre os distratores.
3. Divisão entre os distratores (proporções renormalizadas) × divisão igual, em todas as questões e nas
   questões em que um distrator foi mais escolhido que a correta.
4. Taxa de acerto prevista e real por faixa de acerto real, e as 10 melhores e 10 piores previsões.

Usa as previsões salvas: 2025 fora da dobra (analise_rodada3_2025.json) e 2024 do teste (teste_2024.json).

Uso:
    python EXPERIMENTOS/scripts/analise_erros.py
"""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

RAIZ = Path(__file__).resolve().parents[2]
RES = RAIZ / "EXPERIMENTOS" / "resultados"
LETRAS = "ABCDE"
FAIXAS = [(0.0, 0.25, "até 25%"), (0.25, 0.55, "de 25% a 55%"), (0.55, 1.01, "acima de 55%")]
N_EXTREMOS = 10
PRINCIPAL = {2025: "q1b+pares_bradley_terry", 2024: "q1b+pares (principal)"}
METODOS_2024 = ["q1b+pares (principal)", "q1b", "q1a (sensibilidade)", "oracle (usa gabarito)",
                "media_por_area 2025", "uniforme"]


def ler(nome):
    return json.loads((RES / nome).read_text(encoding="utf-8"))


def matrizes(prev, acervo):
    ids = list(prev)
    P = np.array([[prev[i][k] for k in LETRAS] for i in ids])
    Y = np.array([[acervo[i]["respostas_observadas"]["proporcoes_validas"][k] for k in LETRAS] for i in ids])
    g = np.array([LETRAS.index(acervo[i]["gabarito"]) for i in ids])
    b = np.array([acervo[i]["parametros_tri_oficiais"]["b"] for i in ids])
    return ids, P, Y, g, b


def correlacao(f, x, y):
    """None quando a previsão é constante (Oracle, uniforme): a correlação não é definida."""
    return float(f(x, y).statistic) if np.ptp(x) > 1e-9 else None


def acerto(P, Y, g, b):
    n = np.arange(len(g))
    p_c, y_c = P[n, g], Y[n, g]
    erro = (P - Y) ** 2
    brier = float(erro.sum(axis=1).mean())
    return {
        "mae_acerto": float(np.abs(p_c - y_c).mean()),
        "pearson_acerto": correlacao(pearsonr, p_c, y_c),
        "spearman_acerto": correlacao(spearmanr, p_c, y_c),
        "spearman_com_b_tri": correlacao(spearmanr, p_c, b),
        "brier": brier,
        "fracao_do_brier_no_gabarito": float(erro[n, g].mean() / brier),
    }


def distratores(P, Y, g, mascara=None):
    """Brier das proporções dos quatro distratores, renormalizadas, para a previsão e para a divisão igual."""
    bp, bi = [], []
    for k in range(len(g)):
        if mascara is not None and not mascara[k]:
            continue
        d = [j for j in range(5) if j != g[k]]
        yd = Y[k, d] / Y[k, d].sum()
        pd = P[k, d] / P[k, d].sum()
        bp.append(((pd - yd) ** 2).sum())
        bi.append(((0.25 - yd) ** 2).sum())
    return {"n_questoes": len(bp), "brier_previsao": float(np.mean(bp)), "brier_divisao_igual": float(np.mean(bi))}


def analisar_ano(ano, prev, acervo):
    ids, P, Y, g, b = matrizes(prev, acervo)
    n = np.arange(len(ids))
    p_c, y_c = P[n, g], Y[n, g]
    armadilha = Y.max(axis=1) > y_c
    informada = np.repeat(((1 - y_c) / 4)[:, None], 5, axis=1)
    informada[n, g] = y_c
    faixas = []
    for lo, hi, rot in FAIXAS:
        m = (y_c >= lo) & (y_c < hi)
        faixas.append({"faixa": rot, "n_questoes": int(m.sum()),
                       "acerto_previsto_medio": float(p_c[m].mean()), "acerto_real_medio": float(y_c[m].mean())})
    brier_item = ((P - Y) ** 2).sum(axis=1)
    ordem = np.argsort(brier_item)

    def resumo_grupo(idx):
        distr_ok = []
        for k in idx:
            d = [j for j in range(5) if j != g[k]]
            distr_ok.append(max(d, key=lambda j: Y[k, j]) == max(d, key=lambda j: P[k, j]))
        return {"questoes": [ids[k] for k in idx], "brier_medio": float(brier_item[idx].mean()),
                "acerto_real_medio": float(y_c[idx].mean()), "acerto_previsto_medio": float(p_c[idx].mean()),
                "erro_medio_no_acerto": float(np.abs(p_c[idx] - y_c[idx]).mean()),
                "armadilhas": int(armadilha[idx].sum()), "distrator_principal_certo": int(sum(distr_ok)),
                "por_area": {a: int(sum(acervo[ids[k]]["entrada"]["area"] == a for k in idx)) for a in ("LC", "CH", "CN", "MT")}}

    return {
        "n_questoes": len(ids),
        "metodo_principal": acerto(P, Y, g, b),
        "oracle_informada": {"brier": float(((informada - Y) ** 2).sum(axis=1).mean())},
        "amplitude_do_acerto": {"real": [float(y_c.min()), float(y_c.max())], "previsto": [float(p_c.min()), float(p_c.max())]},
        "distratores_todas": distratores(P, Y, g),
        "distratores_armadilhas": distratores(P, Y, g, armadilha),
        "faixas_de_acerto": faixas,
        "melhores": resumo_grupo(ordem[:N_EXTREMOS]),
        "piores": resumo_grupo(ordem[::-1][:N_EXTREMOS]),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    acervo = {q["registro_id"]: q for q in json.loads(
        (RAIZ / "exportacao_acervo/acervo_questoes_aprovadas_enem_2024_2025.json").read_text(encoding="utf-8"))["questoes"]}
    teste = ler("teste_2024.json")["previsoes"]
    llm = ler("comparacao_llm_2024.json")["previsoes_llm"]
    dev = ler("analise_rodada3_2025.json")["previsoes_fora_da_dobra"]

    saida = {
        "descricao": "Análise descritiva feita depois do teste; nenhum parâmetro foi ajustado.",
        "por_ano": {"2025": analisar_ano(2025, dev[PRINCIPAL[2025]], acervo),
                    "2024": analisar_ano(2024, teste[PRINCIPAL[2024]], acervo)},
        "acerto_por_metodo_2024": {},
    }
    for nome, prev in [(m, teste[m]) for m in METODOS_2024] + list(llm.items()):
        _, P, Y, g, b = matrizes(prev, acervo)
        saida["acerto_por_metodo_2024"][nome] = acerto(P, Y, g, b)
    (RES / "analise_erros.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    (RES / "analise_erros.md").write_text(markdown(saida), encoding="utf-8")
    print(markdown(saida))


def markdown(s):
    pct = lambda v: f"{100 * v:.1f}%"
    L = ["# Onde o método erra (análise descritiva, depois do teste)", "",
         "↓ menor é melhor; ↑ maior é melhor.", "",
         "## Taxa de acerto prevista × real, teste de 2024", "",
         "| Método | MAE do acerto ↓ | Pearson ↑ | Spearman ↑ | Spearman com b da TRI | Brier ↓ | Fração do Brier no gabarito |",
         "|---|---|---|---|---|---|---|"]
    f = lambda v, c=3: "—" if v is None else f"{v:.{c}f}"
    for nome, m in s["acerto_por_metodo_2024"].items():
        L.append(f"| {nome} | {m['mae_acerto']:.4f} | {f(m['pearson_acerto'])} | {f(m['spearman_acerto'])} | "
                 f"{f(m['spearman_com_b_tri'])} | {m['brier']:.4f} | {pct(m['fracao_do_brier_no_gabarito'])} |")
    for ano, a in s["por_ano"].items():
        L += ["", f"## {ano} (método principal, {a['n_questoes']} questões)", "",
              f"- Oracle informada (sabe o gabarito e o acerto real, divide o resto igualmente): Brier {a['oracle_informada']['brier']:.4f}"
              f" (método principal: {a['metodo_principal']['brier']:.4f})",
              f"- Acerto real de {pct(a['amplitude_do_acerto']['real'][0])} a {pct(a['amplitude_do_acerto']['real'][1])}; "
              f"previsto de {pct(a['amplitude_do_acerto']['previsto'][0])} a {pct(a['amplitude_do_acerto']['previsto'][1])}"]
        for rot, d in (("todas as questões", a["distratores_todas"]), ("questões com distrator mais escolhido que a correta", a["distratores_armadilhas"])):
            L.append(f"- Brier entre distratores ({rot}, {d['n_questoes']}): previsão {d['brier_previsao']:.4f}, divisão igual {d['brier_divisao_igual']:.4f}")
        L += ["", "| Acerto real | Questões | Acerto previsto médio | Acerto real médio |", "|---|---|---|---|"]
        for fx in a["faixas_de_acerto"]:
            L.append(f"| {fx['faixa']} | {fx['n_questoes']} | {pct(fx['acerto_previsto_medio'])} | {pct(fx['acerto_real_medio'])} |")
        for rot in ("melhores", "piores"):
            r = a[rot]
            L += ["", f"{N_EXTREMOS} {rot} previsões: Brier {r['brier_medio']:.4f}; acerto real {pct(r['acerto_real_medio'])}, "
                  f"previsto {pct(r['acerto_previsto_medio'])} (erro {pct(r['erro_medio_no_acerto'])}); armadilhas {r['armadilhas']}; "
                  f"distrator principal certo {r['distrator_principal_certo']}; áreas {r['por_area']}; questões: {', '.join(r['questoes'])}"]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
