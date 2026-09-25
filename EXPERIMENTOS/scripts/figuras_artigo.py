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


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    correlacoes()
    print("Figuras geradas em", SAIDA)
