"""Gera as tabelas do artigo (ARTIGO/tabelas/*.tex) a partir dos resultados salvos.

Nenhum número é digitado à mão: tudo vem do acervo e dos arquivos em EXPERIMENTOS/resultados/.
Convenção: ↓ menor é melhor, ↑ maior é melhor, melhor valor de cada coluna em negrito, vírgula decimal.

Uso:
    python EXPERIMENTOS/scripts/gerar_tabelas.py
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RES = RAIZ / "EXPERIMENTOS" / "resultados"
SAIDA = RAIZ / "ARTIGO" / "tabelas"
AVISO = "% GERADO AUTOMATICAMENTE por EXPERIMENTOS/scripts/gerar_tabelas.py; não editar à mão.\n"


def ler(nome):
    return json.loads((RES / nome).read_text(encoding="utf-8"))


def num(v, casas):
    """Número em LaTeX com vírgula decimal e sinal de menos tipográfico."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "---"
    s = f"{abs(v):.{casas}f}".replace(".", "{,}")
    return f"$-{s}$" if v < 0 else f"${s}$"


def ic(par, casas):
    return f"$[{num(par[0], casas)[1:-1]};\\ {num(par[1], casas)[1:-1]}]$"


def tabela_metricas(linhas, colunas, separar_apos=None):
    """linhas: [(rótulo, dict)]; colunas: [(chave, cabeçalho, 'menor'|'maior'|None, casas)].
    Negrito no melhor valor de cada coluna com sentido."""
    melhor = {}
    for chave, _, sentido, casas in colunas:
        vals = [round(d[chave], casas) for _, d in linhas if d.get(chave) is not None]
        if sentido and vals:
            melhor[chave] = min(vals) if sentido == "menor" else max(vals)
    corpo = []
    for i, (rotulo, d) in enumerate(linhas):
        cel = []
        for chave, _, sentido, casas in colunas:
            v = d.get(chave)
            t = num(v, casas)
            if v is not None and chave in melhor and round(v, casas) == melhor[chave]:
                t = f"$\\mathbf{{{t[1:-1]}}}$"
            cel.append(t)
        corpo.append(f"{rotulo} & " + " & ".join(cel) + r" \\")
        if separar_apos is not None and i == separar_apos:
            corpo.append(r"\midrule")
    seta = {"menor": r" \menor", "maior": r" \maior", None: ""}
    cab = "Método & " + " & ".join(c[1] + seta[c[2]] for c in colunas) + r" \\"
    return cab, corpo


def ambiente(legenda, rotulo, alinhamento, cab, corpo, extra=""):
    return (AVISO + "\\begin{table}[ht]\n\\centering\n"
            f"\\caption{{{legenda}}}\\label{{{rotulo}}}\n\\small\n{extra}"
            f"\\begin{{tabular}}{{{alinhamento}}}\n\\toprule\n{cab}\n\\midrule\n"
            + "\n".join(corpo) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")


def grava(nome, conteudo):
    (SAIDA / nome).write_text(conteudo, encoding="utf-8")
    print("  ", nome)


# ---------------------------------------------------------------- tabelas

def tab_itens():
    q = json.loads((RAIZ / "exportacao_acervo/acervo_questoes_aprovadas_enem_2024_2025.json").read_text(encoding="utf-8"))
    c = Counter((x["ano"], x["entrada"]["area"]) for x in q["questoes"])
    nomes = [("LC", "Linguagens (LC)"), ("CH", "Ciências Humanas (CH)"),
             ("CN", "Ciências da Natureza (CN)"), ("MT", "Matemática (MT)")]
    corpo = [f"{n} & {c[(2025, a)]} & {c[(2024, a)]} \\\\" for a, n in nomes]
    corpo += [r"\midrule", f"Total & {sum(c[(2025, a)] for a, _ in nomes)} & {sum(c[(2024, a)] for a, _ in nomes)} \\\\"]
    grava("tab_itens.tex", ambiente("Questões textualmente autossuficientes por área e edição.", "tab:itens",
                                    "lcc", r"Área & 2025 (desenvolvimento) & 2024 (teste) \\", corpo))


COLS_DEV = [("brier", "Brier", "menor", 4), ("spearman_distratores", "Spearman distr.", "maior", 3),
            ("acerto_principal_distrator", "Principal distrator", "maior", 3),
            ("auc_nao_funcional", r"AUC $<$5\%", "maior", 3)]


def tab_desenvolvimento():
    r1 = ler("analise_rodada1_2025.json")["resultados_fora_da_dobra"]
    r3 = ler("analise_rodada3_2025.json")["resultados_fora_da_dobra"]
    assert abs(r1["q1b"]["brier"] - r3["q1b"]["brier"]) < 1e-12  # mesma q1b nas duas análises
    linhas = [("Atratividade + pares (combinação)", r3["q1b+pares_bradley_terry"]),
              ("Pares (Bradley-Terry)", r3["pares_bradley_terry"]),
              ("Atratividade (proporção)", r1["q1b"]),
              ("Combinação das nove perguntas (rodada 1)", r1["combinacao_9"]),
              ("Atratividade (convencimento)", r1["q1a"]),
              ("Modelo em dois níveis", r1["dois_niveis_q1b"]),
              ("Oracle (usa o gabarito)", r1["oracle (usa gabarito)"]),
              ("Uniforme", r1["uniforme"]),
              ("Média por área", r1["media_por_area"])]
    cab, corpo = tabela_metricas(linhas, COLS_DEV, separar_apos=5)
    grava("tab_desenvolvimento.tex", ambiente(
        "Desenvolvimento em 2025: previsões fora da dobra (114 questões, 5 dobras). Análise descritiva.",
        "tab:desenvolvimento", "lcccc", cab, corpo))


def tab_hipoteses():
    h = {x["id"]: x for x in ler("teste_2024.json")["hipoteses"]}
    textos = {"H1": r"Brier: principal $-$ Oracle (usa o gabarito)", "H2": r"Brier: principal $-$ uniforme",
              "H3": "Acerto do principal distrator", "H4": r"Brier: principal $-$ atratividade isolada"}
    corpo = []
    for k in ["H1", "H2", "H3", "H4"]:
        casas = 3 if k == "H3" else 4
        corpo.append(f"{k} & {textos[k]} & {num(h[k]['estimativa'], casas)} & {ic(h[k]['ic95'], casas)} & "
                     f"{'sim' if h[k]['sustentada'] else 'não'} \\\\")
    grava("tab_hipoteses.tex", ambiente(
        "Teste em 2024: hipóteses pré-registradas (120 questões). Diferenças negativas de Brier favorecem o método principal.",
        "tab:hipoteses", "llccc", r"& Hipótese & Estimativa & IC 95\% & Sustentada \\", corpo))


def rotulos_teste(res):
    return [("Atratividade + pares (principal)", res["q1b+pares (principal)"]),
            ("Atratividade (proporção)", res["q1b"]),
            ("Atratividade (convencimento)", res["q1a (sensibilidade)"]),
            ("Oracle (usa o gabarito)", res["oracle (usa gabarito)"]),
            ("Média por área de 2025", res["media_por_area 2025"]),
            ("Uniforme", res["uniforme"])]


def tab_teste():
    res = ler("teste_2024.json")["resultados"]
    cols = [("brier", "Brier", "menor", 4), ("mae", "MAE", "menor", 4), ("spearman_intraitem", "Spearman", "maior", 3),
            ("spearman_distratores", "Spearman distr.", "maior", 3),
            ("acerto_principal_distrator", "Principal distrator", "maior", 3),
            ("auc_nao_funcional", r"AUC $<$5\%", "maior", 3)]
    cab, corpo = tabela_metricas(rotulos_teste(res), cols)
    grava("tab_teste.tex", ambiente("Teste em 2024: métricas descritivas (120 questões).", "tab:teste", "lcccccc",
                                    cab, corpo, extra="\\setlength{\\tabcolsep}{4pt}\n"))


def tab_areas():
    res = ler("teste_2024.json")["resultados"]
    q = json.loads((RAIZ / "exportacao_acervo/acervo_questoes_aprovadas_enem_2024_2025.json").read_text(encoding="utf-8"))
    n = Counter(x["entrada"]["area"] for x in q["questoes"] if x["ano"] == 2024)
    areas = ["LC", "CH", "CN", "MT"]
    linhas = [(r, d["brier_por_area"]) for r, d in rotulos_teste(res) if r != "Atratividade (convencimento)"]
    cab, corpo = tabela_metricas(linhas, [(a, f"{a} ({n[a]})", "menor", 4) for a in areas])
    cab = cab.replace(r" \menor", "")  # a seta vai na legenda, para não repetir em cada coluna
    ganho = [1 - res["q1b+pares (principal)"]["brier_por_area"][a] / res["uniforme"]["brier_por_area"][a] for a in areas]
    corpo += [r"\midrule", r"Ganho do principal sobre a uniforme \maior & "
              + " & ".join(num(g * 100, 0)[:-1] + r"\%$" for g in ganho) + r" \\"]
    grava("tab_areas.tex", ambiente(
        r"Teste em 2024: Brier por área (\menor) e ganho do método principal sobre a uniforme (análise descritiva).",
        "tab:areas", "lcccc", cab, corpo))


def tab_llm():
    c = ler("comparacao_llm_2024.json")["comparacoes"]
    textos = {"C1": r"Jev, principal $\times$ LLM, método A (letras)",
              "C2": r"Jev, principal $\times$ LLM, método B (atratividade + pares)",
              "C3": r"Jev, atratividade $\times$ LLM, atratividade (método B)",
              "C4": r"LLM, método A $\times$ Oracle (usa o gabarito)"}
    corpo = [f"{x['id']} & {textos[x['id']]} & {num(x['diferenca_brier'], 4)} & {ic(x['ic95'], 4)} \\\\" for x in c]
    grava("tab_llm.tex", ambiente(
        r"Comparação com o LLM em 2024 (análise acrescentada depois do teste principal). Diferenças de Brier, $a - b$; valores negativos favorecem $a$.",
        "tab:llm", "llcc", r"& Comparação ($a$ $\times$ $b$) & Diferença & IC 95\% \\", corpo))


def tab_llm_metricas():
    s = ler("comparacao_llm_2024.json")
    res, n = s["resultados"], s["n_itens"]
    custo_jev, custo_llm = s["uso_jev"]["custo_usd"] / n, s["uso_llm"]["custo_usd"] / n
    linhas = [("Jev: atratividade + pares", {**res["q1b+pares (principal)"], "custo": custo_jev}),
              ("Jev: atratividade", {**res["q1b"], "custo": custo_jev}),
              ("LLM B: atratividade + pares", {**res["LLM B q1b+pares"], "custo": custo_llm}),
              ("LLM B: pares", {**res["LLM B pares"], "custo": custo_llm}),
              ("LLM B: atratividade", {**res["LLM B q1b"], "custo": custo_llm}),
              ("LLM A: letras", {**res["LLM A (letras)"], "custo": custo_llm})]
    cab, corpo = tabela_metricas(linhas, COLS_DEV + [("custo", r"Custo/questão (US\$)", "menor", 5)])
    grava("tab_llm_metricas.tex", ambiente(
        "Jev e LLM em 2024: métricas e custo por questão (análise descritiva). O custo do Jev inclui as duas requisições; o do LLM, as 30 chamadas.",
        "tab:llm-metricas", "lccccc", cab, corpo, extra="\\setlength{\\tabcolsep}{4pt}\n"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    SAIDA.mkdir(parents=True, exist_ok=True)
    print("Tabelas geradas em", SAIDA)
    for f in (tab_itens, tab_desenvolvimento, tab_hipoteses, tab_teste, tab_areas, tab_llm, tab_llm_metricas):
        f()


if __name__ == "__main__":
    main()
