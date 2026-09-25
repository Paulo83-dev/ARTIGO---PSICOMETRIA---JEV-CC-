"""Formatação das tabelas em Markdown dos relatórios.

Convenção: ↓ no cabeçalho quando menor é melhor, ↑ quando maior é melhor, e o melhor valor
de cada coluna em negrito (em caso de empate, todos os empatados).
"""

import math

SETA = {"menor": " ↓", "maior": " ↑", None: ""}


def _vazio(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def tabela(linhas, colunas, primeira="Método"):
    """linhas: lista de (nome, {chave: valor}).
    colunas: lista de (chave, rótulo, sentido, formato), com sentido em {"menor", "maior", None}
    e formato uma string de formatação, por exemplo "{:.4f}" ou "{:+.4f}"."""
    melhores = {}
    for chave, _, sentido, _ in colunas:
        valores = [d.get(chave) for _, d in linhas if not _vazio(d.get(chave))]
        if sentido and valores:
            melhores[chave] = (min if sentido == "menor" else max)(valores)

    cab = f"| {primeira} | " + " | ".join(rotulo + SETA[sentido] for _, rotulo, sentido, _ in colunas) + " |"
    sep = "|---|" + "---|" * len(colunas)
    saida = [cab, sep]
    for nome, d in linhas:
        celulas = []
        for chave, _, sentido, fmt in colunas:
            v = d.get(chave)
            if _vazio(v):
                celulas.append("—")
                continue
            texto = fmt.format(v)
            if chave in melhores and math.isclose(v, melhores[chave], rel_tol=0, abs_tol=1e-12):
                texto = f"**{texto}**"
            celulas.append(texto)
        saida.append(f"| {nome} | " + " | ".join(celulas) + " |")
    return saida


# Colunas padrão das tabelas de métricas
COLUNAS_METRICAS = [
    ("brier", "Brier", "menor", "{:.4f}"),
    ("mae", "MAE", "menor", "{:.4f}"),
    ("jensen_shannon", "JS", "menor", "{:.4f}"),
    ("spearman_intraitem", "Spearman", "maior", "{:.4f}"),
    ("brier_distratores", "Brier distr.", "menor", "{:.4f}"),
    ("spearman_distratores", "Spearman distr.", "maior", "{:.4f}"),
    ("acerto_principal_distrator", "Principal distrator", "maior", "{:.4f}"),
    ("auc_nao_funcional", "AUC <5%", "maior", "{:.4f}"),
]


def por_area(linhas, chave_area, areas, sentido, rotulos=None):
    """Tabela método × área a partir de um dicionário por área dentro de cada linha."""
    rotulos = rotulos or {a: a for a in areas}
    return tabela([(nome, d[chave_area]) for nome, d in linhas],
                  [(a, rotulos[a], sentido, "{:.4f}") for a in areas])
