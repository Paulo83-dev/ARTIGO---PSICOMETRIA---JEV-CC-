"""Análise da rodada 1 no ano de desenvolvimento (2025), com validação cruzada.

Para cada método, os parâmetros são ajustados em 4 dobras e usados para prever a 5ª;
as métricas são calculadas sobre as previsões fora da dobra. Ao final, cada método é
reajustado em todos os itens do ano, e esses parâmetros ficam registrados para o
congelamento da configuração.

Uso:
    python EXPERIMENTOS/scripts/analisar_rodada1.py --ano 2025 \
        --respostas EXPERIMENTOS/resultados/jev_rodada1_2025.jsonl \
        --saida EXPERIMENTOS/resultados/analise_rodada1_2025
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.stats import spearmanr

import sys
sys.path.insert(0, str(Path(__file__).parent))
from tabelas import COLUNAS_METRICAS, por_area, tabela  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
ACERVO = RAIZ / "exportacao_acervo" / "acervo_questoes_aprovadas_enem_2024_2025.json"
LETRAS = ["A", "B", "C", "D", "E"]
PERGUNTAS = ["q1a", "q1b", "q2", "q3", "q4", "q5", "q6", "q7", "q9"]
N_DOBRAS = 5
SEMENTE = 2025
GRADE_BETA = np.linspace(-8, 8, 1601)
GRADE_LAMBDA = [0.0, 0.001, 0.01, 0.1]
LIMIAR_FUNCIONAL = 0.05


# ---------------------------------------------------------------- dados

def carregar(ano, caminho_respostas):
    questoes = {q["registro_id"]: q for q in json.loads(ACERVO.read_text(encoding="utf-8"))["questoes"]
                if q["ano"] == ano}
    respostas = {}
    for linha in (RAIZ / caminho_respostas).read_text(encoding="utf-8").splitlines():
        reg = json.loads(linha)
        if reg["status_http"] == 200:
            respostas[reg["registro_id"]] = reg["resposta"]["answers"]
    ids = sorted(questoes)
    faltando = [i for i in ids if i not in respostas]
    if faltando:
        raise SystemExit(f"Itens sem resposta do Jev: {faltando}")

    Y = np.array([[questoes[i]["respostas_observadas"]["proporcoes_validas"][k] for k in LETRAS] for i in ids])
    Y = Y / Y.sum(axis=1, keepdims=True)
    gab = np.array([LETRAS.index(questoes[i]["gabarito"]) for i in ids])
    area = np.array([questoes[i]["entrada"]["area"] for i in ids])

    # X[item, alternativa, pergunta]: score (0–4) ou noul (0–1)
    X = np.zeros((len(ids), 5, len(PERGUNTAS)))
    for n, i in enumerate(ids):
        for j, pid in enumerate(PERGUNTAS):
            for k, letra in enumerate(LETRAS):
                r = respostas[i][f"{pid}_{letra}"]
                X[n, k, j] = r["score"] if r["type"] == "score" else r["noul"]
    comprimento = np.array([[len(questoes[i]["entrada"]["alternativas"][k]) for k in LETRAS] for i in ids], float)

    # Grupos: itens que compartilham texto de apoio ficam juntos.
    grupos = []
    for i in ids:
        apoio = questoes[i]["entrada"]["apoio_compartilhado"].strip()
        grupos.append("apoio:" + hashlib.sha256(apoio.encode()).hexdigest()[:12] if apoio
                      else questoes[i]["questao_base_id"])
    return ids, X, comprimento, Y, gab, area, np.array(grupos)


def dobras_agrupadas(grupos, area, n_dobras=N_DOBRAS, semente=SEMENTE):
    """Atribui grupos às dobras, equilibrando as áreas (distribuição circular por área)."""
    rng = np.random.default_rng(semente)
    area_do_grupo = {g: area[grupos == g][0] for g in np.unique(grupos)}
    dobra_do_grupo, contador = {}, 0
    for a in sorted(set(area_do_grupo.values())):
        gs = [g for g, ag in area_do_grupo.items() if ag == a]
        for g in rng.permutation(gs):
            dobra_do_grupo[g] = contador % n_dobras
            contador += 1
    return np.array([dobra_do_grupo[g] for g in grupos])


# ---------------------------------------------------------------- previsão

def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def brier_medio(P, Y):
    return float(((P - Y) ** 2).sum(axis=1).mean())


class SoftmaxUmaVariavel:
    """p ∝ exp(β·s), com s padronizada no treino. β = 1/T quando s é um escore de atratividade."""

    def ajustar(self, S, Y):
        self.media, self.dp = S.mean(), S.std() or 1.0
        Z = (S - self.media) / self.dp
        erros = [brier_medio(softmax(b * Z), Y) for b in GRADE_BETA]
        self.beta = float(GRADE_BETA[int(np.argmin(erros))])
        return self

    def prever(self, S):
        return softmax(self.beta * (S - self.media) / self.dp)

    def parametros(self):
        # β na escala original e a temperatura equivalente
        beta_orig = self.beta / self.dp
        return {"beta_padronizado": self.beta, "beta": beta_orig,
                "temperatura": (1 / beta_orig) if beta_orig > 0 else None}


class LogitCondicional:
    """p ∝ exp(Σ_j β_j·s_j) com penalidade ridge; λ escolhido por validação cruzada interna."""

    def _ajustar_lambda(self, Z, Y, lam):
        n_var = Z.shape[2]

        def objetivo(b):
            return brier_medio(softmax(Z @ b), Y) + lam * float(b @ b)

        res = minimize(objetivo, np.zeros(n_var), method="L-BFGS-B")
        return res.x

    def ajustar(self, S, Y, grupos_treino, area_treino):
        self.media = S.reshape(-1, S.shape[2]).mean(axis=0)
        self.dp = S.reshape(-1, S.shape[2]).std(axis=0)
        self.dp[self.dp == 0] = 1.0
        Z = (S - self.media) / self.dp
        dobras_int = dobras_agrupadas(grupos_treino, area_treino, n_dobras=4, semente=SEMENTE + 1)
        erro_por_lambda = {}
        for lam in GRADE_LAMBDA:
            erros = []
            for d in range(4):
                tr, te = dobras_int != d, dobras_int == d
                b = self._ajustar_lambda(Z[tr], Y[tr], lam)
                erros.append(((softmax(Z[te] @ b) - Y[te]) ** 2).sum(axis=1))
            erro_por_lambda[lam] = float(np.concatenate(erros).mean())
        self.lam = min(erro_por_lambda, key=erro_por_lambda.get)
        self.beta = self._ajustar_lambda(Z, Y, self.lam)
        return self

    def prever(self, S):
        return softmax(((S - self.media) / self.dp) @ self.beta)

    def parametros(self, nomes):
        return {"lambda": self.lam,
                "beta_padronizado": dict(zip(nomes, map(float, self.beta))),
                "media": dict(zip(nomes, map(float, self.media))),
                "dp": dict(zip(nomes, map(float, self.dp)))}


class DoisNiveis:
    """Modelo em dois níveis (logit aninhado), sem gabarito.

    Cada alternativa c é tratada como hipótese de ser a correta, com peso w_c = softmax(γ·z4),
    em que z4 é a pergunta "é a resposta correta?" (q4) padronizada. Sob a hipótese c:
      - a correta recebe a = sigmoide(α0 + α1·m_c), em que m_c é a atratividade do distrator mais
        forte (quanto mais forte, menor o acerto esperado);
      - os distratores dividem 1 − a por softmax(β·z_d), com z_d a pergunta de atratividade.
    A previsão final é a média das hipóteses ponderada por w. Com `gabarito` informado, w é
    substituído pela indicadora do gabarito (versão diagnóstica, que USA O GABARITO).
    """

    def __init__(self, idx_correcao, idx_distratores):
        self.idx_c = idx_correcao
        self.idx_d = idx_distratores  # lista de perguntas somadas (já padronizadas) no nível 2

    def _padronizar(self, S):
        return (S - self.media) / self.dp

    def _prever(self, theta, Z, gab=None):
        gama, a0, a1, beta = theta
        n = Z.shape[0]
        zc = Z[:, :, self.idx_c]
        zd = Z[:, :, self.idx_d].sum(axis=2)
        W = np.eye(5)[gab] if gab is not None else softmax(gama * zc)
        P = np.zeros((n, 5))
        for c in range(5):
            outros = [k for k in range(5) if k != c]
            m = zd[:, outros].max(axis=1)
            a = 1 / (1 + np.exp(-(a0 + a1 * m)))
            Q = np.zeros((n, 5))
            Q[:, c] = a
            Q[:, outros] = (1 - a)[:, None] * softmax(beta * zd[:, outros])
            P += W[:, [c]] * Q
        return P

    def ajustar(self, S, Y, gab=None):
        plano = S.reshape(-1, S.shape[2])
        self.media, self.dp = plano.mean(axis=0), plano.std(axis=0)
        self.dp[self.dp == 0] = 1.0
        Z = self._padronizar(S)
        melhor = None
        for inicio in ([2, 0, 0, 1], [5, 0, -1, 1], [1, -1, 0, 0.5]):
            res = minimize(lambda t: brier_medio(self._prever(t, Z, gab), Y), np.array(inicio, float),
                           method="L-BFGS-B")
            if melhor is None or res.fun < melhor.fun:
                melhor = res
        self.theta = melhor.x
        return self

    def prever(self, S, gab=None):
        return self._prever(self.theta, self._padronizar(S), gab)

    def parametros(self):
        g, a0, a1, b = map(float, self.theta)
        return {"gama": g, "alfa0": a0, "alfa1": a1, "beta": b}


def correlacoes_dentro_do_item(X, nomes):
    """Spearman entre perguntas, após centrar cada pergunta pela média do item (remove o efeito do item)."""
    from scipy.stats import spearmanr as sp
    Xc = X - X.mean(axis=1, keepdims=True)
    plano = Xc.reshape(-1, X.shape[2])
    R = sp(plano).statistic
    return {a: {b: float(R[i, j]) for j, b in enumerate(nomes)} for i, a in enumerate(nomes)}


def oracle(gab_treino, Y_treino, gab_teste):
    """Probabilidade do gabarito = acerto médio do treino; restante dividido igualmente. USA O GABARITO."""
    acerto = float(Y_treino[np.arange(len(gab_treino)), gab_treino].mean())
    P = np.full((len(gab_teste), 5), (1 - acerto) / 4)
    P[np.arange(len(gab_teste)), gab_teste] = acerto
    return P, acerto


# ---------------------------------------------------------------- métricas

def metricas(P, Y, gab, area):
    n = len(Y)
    idx = np.arange(n)
    brier_item = ((P - Y) ** 2).sum(axis=1)
    mae = np.abs(P - Y).mean(axis=1)

    spearman = [spearmanr(p, y).statistic for p, y in zip(P, Y) if np.ptp(p) > 0]

    # Só distratores, renormalizados (distribuição condicional ao erro)
    mascara = np.ones_like(P, bool)
    mascara[idx, gab] = False
    Pd = P[mascara].reshape(n, 4)
    Yd = Y[mascara].reshape(n, 4)
    Pd = Pd / Pd.sum(axis=1, keepdims=True)
    Yd = Yd / Yd.sum(axis=1, keepdims=True)
    brier_d = ((Pd - Yd) ** 2).sum(axis=1)
    spearman_d = [spearmanr(p, y).statistic for p, y in zip(Pd, Yd) if np.ptp(p) > 0]

    # Acerto do principal distrator (crédito 1/k em empate previsto entre k distratores)
    acerto_pd = []
    for p, y in zip(Pd, Yd):
        empatados = np.flatnonzero(np.isclose(p, p.max()))
        acerto_pd.append(float(np.argmax(y) in empatados) / len(empatados))

    # Divergência de Jensen–Shannon (base 2, entre 0 e 1)
    def js(p, q):
        m = (p + q) / 2
        def kl(a, b):
            ok = a > 0
            return float((a[ok] * np.log2(a[ok] / b[ok])).sum())
        return 0.5 * kl(p, m) + 0.5 * kl(q, m)
    js_item = [js(p, y) for p, y in zip(P, Y)]

    # AUC para detectar distratores não funcionais (< 5% de escolha): menor p = mais suspeito
    rotulo = (Y[mascara] < LIMIAR_FUNCIONAL).astype(int)
    escore = -P[mascara]
    auc = auc_mann_whitney(escore, rotulo)

    res = {
        "brier": float(brier_item.mean()),
        "mae": float(mae.mean()),
        "spearman_intraitem": float(np.mean(spearman)) if spearman else None,
        "jensen_shannon": float(np.mean(js_item)),
        "brier_distratores": float(brier_d.mean()),
        "spearman_distratores": float(np.mean(spearman_d)) if spearman_d else None,
        "acerto_principal_distrator": float(np.mean(acerto_pd)),
        "auc_nao_funcional": auc,
        "brier_por_area": {a: float(brier_item[area == a].mean()) for a in sorted(set(area))},
        "acerto_principal_distrator_por_area": {a: float(np.mean(np.array(acerto_pd)[area == a]))
                                                for a in sorted(set(area))},
    }
    return res, brier_item


def spearman_bruto_distratores(S, Y, gab):
    """Spearman médio, por item, entre o escore bruto (sem ajuste) e a proporção real, só entre distratores.

    Serve para as perguntas de característica: nelas a alternativa correta tem escore baixo por
    construção (ex.: "é um erro típico?"), e uma softmax ajustada nas 5 alternativas inverteria o sinal.
    """
    n = len(Y)
    mascara = np.ones_like(Y, bool)
    mascara[np.arange(n), gab] = False
    Sd, Yd = S[mascara].reshape(n, 4), Y[mascara].reshape(n, 4)
    r = [spearmanr(s, y).statistic for s, y in zip(Sd, Yd) if np.ptp(s) > 0]
    return {"spearman": float(np.mean(r)), "itens_com_variacao": len(r)}


def auc_mann_whitney(escore, rotulo):
    pos, neg = escore[rotulo == 1], escore[rotulo == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    maiores = (pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()
    return float(maiores / (len(pos) * len(neg)))


# ---------------------------------------------------------------- execução

def main():
    sys.stdout.reconfigure(encoding="utf-8")  # o console do Windows não imprime ↑ ↓ na codificação padrão
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2025)
    ap.add_argument("--respostas", required=True)
    ap.add_argument("--saida", required=True, help="prefixo dos arquivos de saída (.json e .md)")
    args = ap.parse_args()

    ids, X, comp, Y, gab, area, grupos = carregar(args.ano, args.respostas)
    dobra = dobras_agrupadas(grupos, area)
    n = len(ids)

    metodos = {}  # nome -> matriz de previsões fora da dobra
    parametros_finais = {}

    def validar(nome, ajustar_e_prever, usa_gabarito=False):
        P = np.zeros((n, 5))
        for d in range(N_DOBRAS):
            tr, te = dobra != d, dobra == d
            P[te] = ajustar_e_prever(tr, te)
        metodos[nome] = {"P": P, "usa_gabarito": usa_gabarito}

    # Linhas de base
    validar("uniforme", lambda tr, te: np.full((te.sum(), 5), 0.2))

    def media_por_area(tr, te):
        return np.array([Y[tr & (area == a)].mean(axis=0) for a in area[te]])
    validar("media_por_area", media_por_area)

    validar("oracle (usa gabarito)", lambda tr, te: oracle(gab[tr], Y[tr], gab[te])[0], usa_gabarito=True)
    parametros_finais["oracle (usa gabarito)"] = {"acerto_medio": oracle(gab, Y, gab)[1]}

    validar("comprimento", lambda tr, te: SoftmaxUmaVariavel().ajustar(comp[tr], Y[tr]).prever(comp[te]))
    parametros_finais["comprimento"] = SoftmaxUmaVariavel().ajustar(comp, Y).parametros()

    # Uma pergunta por vez
    for j, pid in enumerate(PERGUNTAS):
        S = X[:, :, j]
        validar(pid, lambda tr, te, S=S: SoftmaxUmaVariavel().ajustar(S[tr], Y[tr]).prever(S[te]))
        parametros_finais[pid] = SoftmaxUmaVariavel().ajustar(S, Y).parametros()

    # Combinação das 9 perguntas (logit condicional com ridge)
    validar("combinacao_9",
            lambda tr, te: LogitCondicional().ajustar(X[tr], Y[tr], grupos[tr], area[tr]).prever(X[te]))
    parametros_finais["combinacao_9"] = LogitCondicional().ajustar(X, Y, grupos, area).parametros(PERGUNTAS)

    # Dois níveis: q4 decide qual é a correta; a atratividade divide o restante entre os distratores
    iq = {p: j for j, p in enumerate(PERGUNTAS)}
    variantes = {
        "dois_niveis_q1b": [iq["q1b"]],
        "dois_niveis_q9": [iq["q9"]],
        "dois_niveis_q1b+q9": [iq["q1b"], iq["q9"]],
    }
    for nome, idx_d in variantes.items():
        validar(nome, lambda tr, te, idx_d=idx_d:
                DoisNiveis(iq["q4"], idx_d).ajustar(X[tr], Y[tr]).prever(X[te]))
        parametros_finais[nome] = DoisNiveis(iq["q4"], idx_d).ajustar(X, Y).parametros()
        # Diagnóstico: mesmo modelo, mas sabendo qual é a correta (teto do nível 2)
        nome_g = nome + " (usa gabarito)"
        validar(nome_g, lambda tr, te, idx_d=idx_d:
                DoisNiveis(iq["q4"], idx_d).ajustar(X[tr], Y[tr], gab[tr]).prever(X[te], gab[te]),
                usa_gabarito=True)

    # Métricas
    resultados, brier_itens = {}, {}
    for nome, m in metodos.items():
        res, bi = metricas(m["P"], Y, gab, area)
        res["usa_gabarito"] = m["usa_gabarito"]
        resultados[nome] = res
        brier_itens[nome] = bi

    saida = {
        "ano": args.ano,
        "n_itens": n,
        "n_dobras": N_DOBRAS,
        "semente": SEMENTE,
        "itens_por_area": {a: int((area == a).sum()) for a in sorted(set(area))},
        "resultados_fora_da_dobra": resultados,
        "spearman_bruto_entre_distratores": {
            **{pid: spearman_bruto_distratores(X[:, :, j], Y, gab) for j, pid in enumerate(PERGUNTAS)},
            "comprimento": spearman_bruto_distratores(comp, Y, gab),
        },
        "parametros_ajustados_em_todo_o_ano": parametros_finais,
        "correlacoes_entre_perguntas_dentro_do_item": correlacoes_dentro_do_item(X, PERGUNTAS),
        "previsoes_fora_da_dobra": {nome: {i: dict(zip(LETRAS, map(float, p))) for i, p in zip(ids, m["P"])}
                                    for nome, m in metodos.items()},
        "brier_por_item": {nome: dict(zip(ids, map(float, b))) for nome, b in brier_itens.items()},
    }
    prefixo = RAIZ / args.saida
    prefixo.parent.mkdir(parents=True, exist_ok=True)
    prefixo.with_suffix(".json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    prefixo.with_suffix(".md").write_text(tabela_markdown(saida), encoding="utf-8")
    print(tabela_markdown(saida))


def tabela_markdown(s):
    linhas = [f"# Rodada 1: resultados fora da dobra, ENEM {s['ano']} ({s['n_itens']} itens, {s['n_dobras']} dobras)",
              "",
              "↓ menor é melhor; ↑ maior é melhor; melhor valor de cada coluna em negrito. "
              "'Distratores' = só os 4 distratores, renormalizados.",
              ""]
    ordem = sorted(s["resultados_fora_da_dobra"].items(), key=lambda kv: kv[1]["brier"])
    linhas += tabela(ordem, COLUNAS_METRICAS)
    linhas += ["", "Observação: nas perguntas de característica (q4–q9), a softmax ajustada nas 5 alternativas "
               "pode inverter o sinal da pergunta; para elas, a métrica adequada é a da tabela seguinte.",
               "", "## Escore bruto × proporção real, só entre distratores (sem ajuste)", ""]
    linhas += tabela(list(s["spearman_bruto_entre_distratores"].items()),
                     [("spearman", "Spearman médio por item", "maior", "{:+.4f}"),
                      ("itens_com_variacao", "Itens com variação", None, "{}")], primeira="Pergunta")
    C = s["correlacoes_entre_perguntas_dentro_do_item"]
    nomes = list(C)
    linhas += ["", "## Correlação entre perguntas (Spearman, centrado por item)", "",
               "| | " + " | ".join(nomes) + " |", "|---|" + "---|" * len(nomes)]
    for a in nomes:
        linhas.append(f"| {a} | " + " | ".join(f"{C[a][b]:.2f}" for b in nomes) + " |")
    areas = list(s["itens_por_area"])
    rot = {a: f"{a} (n={s['itens_por_area'][a]})" for a in areas}
    linhas += ["", "## Brier por área", ""] + por_area(ordem, "brier_por_area", areas, "menor", rot)
    linhas += ["", "## Acerto do principal distrator por área", ""]
    linhas += por_area(ordem, "acerto_principal_distrator_por_area", areas, "maior")
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    main()
