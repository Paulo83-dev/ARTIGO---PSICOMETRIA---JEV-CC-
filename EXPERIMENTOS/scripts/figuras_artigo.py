"""Gera as figuras do artigo a partir dos resultados salvos (sem novas chamadas a modelos).

Uso:
    python EXPERIMENTOS/scripts/figuras_artigo.py
"""

import json
import sys
from pathlib import Path

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "ARTIGO" / "figuras"

# Paleta divergente: vermelho (negativo) ↔ cinza neutro (zero) ↔ azul (positivo)
DIVERGENTE = LinearSegmentedColormap.from_list("divergente", ["#b3261e", "#e34948", "#f0efec", "#2a78d6", "#184f95"])
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"

NOMES = {
    "q1a": "Atratividade (convencimento)",
    "q1b": "Atratividade (proporção)",
    "q2": "Plausibilidade",
    "q3": "Esforço para descartar",
    "q4": "É a correta?",
    "q5": "Verdade local",
    "q6": "Correção parcial",
    "q7": "Eco do texto",
    "q9": "Equívoco comum",
}


def correlacoes():
    s = json.loads((RAIZ / "EXPERIMENTOS/resultados/analise_rodada1_2025.json").read_text(encoding="utf-8"))
    C = s["correlacoes_entre_perguntas_dentro_do_item"]
    ids = list(C)
    M = [[C[a][b] for b in ids] for a in ids]
    rotulos = [NOMES[i] for i in ids]

    plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(6.3, 5.2))
    im = ax.imshow(M, cmap=DIVERGENTE, vmin=-1, vmax=1)
    for i in range(len(ids)):
        for j in range(len(ids)):
            v = M[i][j]
            ax.text(j, i, f"{v:.2f}".replace(".", ",").replace("-", "−"), ha="center", va="center", fontsize=7,
                    color="white" if abs(v) > 0.6 else TINTA)
    ax.set_xticks(range(len(ids)), rotulos, rotation=45, ha="right", color=TINTA)
    ax.set_yticks(range(len(ids)), rotulos, color=TINTA)
    ax.tick_params(length=0)
    for lado in ax.spines.values():
        lado.set_visible(False)
    # 2px de separação entre células, na cor da superfície
    ax.set_xticks([x - 0.5 for x in range(1, len(ids))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(ids))], minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="minor", length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label("Correlação de Spearman (centrada por questão)", color=TINTA_2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(color=TINTA_2, labelcolor=TINTA_2)
    cb.ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}".replace(".", ",").replace("-", "−")))
    fig.tight_layout()
    SAIDA.mkdir(parents=True, exist_ok=True)
    fig.savefig(SAIDA / "correlacoes_perguntas.pdf", bbox_inches="tight")
    fig.savefig(SAIDA / "correlacoes_perguntas.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def curva_temperatura():
    """Brier da atratividade isolada (q1b) em função da temperatura, em 2025 e 2024.

    Diagnóstico feito depois do teste: nada aqui é usado no ajuste. Os números citados no texto
    são salvos em EXPERIMENTOS/resultados/sensibilidade_temperatura.json.
    """
    import numpy as np
    sys.path.insert(0, str(Path(__file__).parent))
    from analisar_rodada1 import PERGUNTAS, carregar, softmax

    congelamento = json.loads((RAIZ / "EXPERIMENTOS/congelamento_teste_2024.json").read_text(encoding="utf-8"))
    t_cong = 1 / congelamento["metodos"]["q1b"]["beta"]
    ts = np.geomspace(0.3, 30, 400)
    curvas, resumo = {}, {"temperatura_congelada": t_cong}
    for ano in (2025, 2024):
        _, X1, _, Y, _, _, _ = carregar(ano, f"EXPERIMENTOS/resultados/jev_rodada1_{ano}.jsonl")
        s = X1[:, :, PERGUNTAS.index("q1b")]
        brier = lambda T: float(((softmax(s / T) - Y) ** 2).sum(axis=1).mean())
        curvas[ano] = np.array([brier(T) for T in ts])
        i = int(curvas[ano].argmin())
        faixa = ts[curvas[ano] <= curvas[ano][i] * 1.05]
        resumo[str(ano)] = {"temperatura_otima": float(ts[i]), "brier_otimo": float(curvas[ano][i]),
                            "brier_com_temperatura_congelada": brier(t_cong),
                            "faixa_ate_5pct_acima_do_minimo": [float(faixa.min()), float(faixa.max())]}
    (RAIZ / "EXPERIMENTOS/resultados/sensibilidade_temperatura.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")

    virgula = lambda casas: matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.{casas}f}".replace(".", ","))
    plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(6.3, 3.4))
    cores = {2025: "#2a5c8a", 2024: "#c0662b"}
    rotulos = {2025: "2025 (desenvolvimento)", 2024: "2024 (teste)"}
    for ano, estilo in ((2025, "-"), (2024, "--")):
        ax.plot(ts, curvas[ano], estilo, color=cores[ano], lw=2, label=rotulos[ano])
        i = int(curvas[ano].argmin())
        ax.plot(ts[i], curvas[ano][i], "o", color=cores[ano], ms=6, mec="white", mew=1.5)
    ax.axvline(t_cong, color=TINTA_2, lw=1, ls=":")
    ax.text(t_cong * 1.06, 0.36, f"T congelada = {t_cong:.2f}".replace(".", ","), va="top", color=TINTA_2)
    ax.set_xscale("log")
    ax.set_xticks([0.3, 0.5, 1, 2, 5, 10, 20, 30])
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.yaxis.set_major_formatter(virgula(2))
    ax.set_xlabel("Temperatura $T$ (escala logarítmica)", color=TINTA)
    ax.set_ylabel("Brier A–E (menor é melhor)", color=TINTA)
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="center right")
    fig.tight_layout()
    fig.savefig(SAIDA / "curva_temperatura.pdf", bbox_inches="tight")
    fig.savefig(SAIDA / "curva_temperatura.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return resumo


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    correlacoes()
    print(json.dumps(curva_temperatura(), ensure_ascii=False, indent=1))
    print("Figuras geradas em", SAIDA)
