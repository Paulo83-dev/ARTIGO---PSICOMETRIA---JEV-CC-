"""Aplica a configuração congelada ao ano de teste e avalia as hipóteses pré-registradas.

Nada é ajustado aqui: todos os parâmetros vêm do arquivo de congelamento.

Uso:
    python EXPERIMENTOS/scripts/avaliar_teste.py \
        --congelamento EXPERIMENTOS/congelamento_teste_2024.json \
        --respostas EXPERIMENTOS/resultados/jev_rodada1_2024.jsonl \
        --saida EXPERIMENTOS/resultados/teste_2024
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from analisar_rodada1 import LETRAS, PERGUNTAS, RAIZ, ACERVO, carregar, metricas, softmax  # noqa: E402
import perguntas_rodada1  # noqa: E402
import perguntas_rodada3  # noqa: E402


def conferir_requisicoes(caminho, cfg, ano, modulo_perguntas=perguntas_rodada1):
    """Confirma que as chamadas usaram exatamente o modelo, o `state` e as perguntas congelados."""
    questoes = {q["registro_id"]: q for q in json.loads(ACERVO.read_text(encoding="utf-8"))["questoes"]
                if q["ano"] == ano}
    perguntas = modulo_perguntas.montar_perguntas()
    respondidos = set()
    problemas = []
    for linha in (RAIZ / caminho).read_text(encoding="utf-8").splitlines():
        reg = json.loads(linha)
        if reg["status_http"] != 200:
            continue
        c = reg["corpo"]
        if c["model"] != cfg["modelo"] or reg["resposta"].get("model") != cfg["modelo_respondente"]:
            problemas.append(f"{reg['registro_id']}: modelo diferente")
        if c["state"] != questoes[reg["registro_id"]]["entrada"]:
            problemas.append(f"{reg['registro_id']}: state diferente da entrada do acervo")
        if c["questions"] != perguntas:
            problemas.append(f"{reg['registro_id']}: perguntas diferentes das congeladas")
        respondidos.add(reg["registro_id"])
    faltando = sorted(set(questoes) - respondidos)
    if faltando:
        problemas.append(f"itens sem resposta válida: {faltando}")
    if problemas:
        raise SystemExit("Requisições não conferem com o congelamento:\n" + "\n".join(problemas))


def prever(cfg_metodo, X, Y_shape, gab, area, theta=None):
    tipo = cfg_metodo["tipo"]
    n = Y_shape[0]
    if tipo == "logit_q1b_pares":
        # z = Σ β_j·(s_j − média_j)/dp_j, com s = (q1b, força de Bradley-Terry dos pares)
        S = np.stack([X[:, :, PERGUNTAS.index("q1b")], theta], axis=2)
        Z = (S - np.array(cfg_metodo["media"])) / np.array(cfg_metodo["dp"])
        return softmax(Z @ np.array(cfg_metodo["beta_padronizado"]))
    if tipo == "softmax_pergunta":
        S = X[:, :, PERGUNTAS.index(cfg_metodo["pergunta"])]
        return softmax(cfg_metodo["beta"] * S)
    if tipo == "uniforme":
        return np.full((n, 5), 0.2)
    if tipo == "oracle":
        a = cfg_metodo["acerto_medio"]
        P = np.full((n, 5), (1 - a) / 4)
        P[np.arange(n), gab] = a
        return P
    if tipo == "media_por_area":
        return np.array([[cfg_metodo["medias"][ar][k] for k in LETRAS] for ar in area])
    raise ValueError(tipo)


def bootstrap_grupos(valores_por_item, grupos, reps, semente):
    """Médias de reamostragens em que os grupos (itens ligados) são sorteados inteiros."""
    rng = np.random.default_rng(semente)
    ug = np.unique(grupos)
    por_grupo = [np.flatnonzero(grupos == g) for g in ug]
    medias = np.empty(reps)
    for r in range(reps):
        idx = np.concatenate([por_grupo[i] for i in rng.integers(0, len(ug), len(ug))])
        medias[r] = valores_por_item[idx].mean()
    return medias


def acerto_principal_distrator_por_item(P, Y, gab):
    n = len(Y)
    m = np.ones_like(P, bool)
    m[np.arange(n), gab] = False
    Pd, Yd = P[m].reshape(n, 4), Y[m].reshape(n, 4)
    out = []
    for p, y in zip(Pd, Yd):
        emp = np.flatnonzero(np.isclose(p, p.max()))
        out.append(float(np.argmax(y) in emp) / len(emp))
    return np.array(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--congelamento", required=True)
    ap.add_argument("--respostas", required=True, help="respostas da rodada 1")
    ap.add_argument("--respostas3", required=True, help="respostas da rodada 3 (pares)")
    ap.add_argument("--saida", required=True)
    args = ap.parse_args()

    # Importado aqui para evitar importação circular (analisar_rodada3 usa bootstrap_grupos deste módulo).
    from analisar_rodada3 import bradley_terry, carregar_pares, combinar_ordens, diagnosticos

    cfg = json.loads((RAIZ / args.congelamento).read_text(encoding="utf-8"))
    ano = cfg["ano_teste"]
    conferir_requisicoes(args.respostas, cfg, ano, perguntas_rodada1)
    conferir_requisicoes(args.respostas3, cfg, ano, perguntas_rodada3)
    ids, X, _, Y, gab, area, grupos = carregar(ano, args.respostas)
    P1 = carregar_pares(ids, args.respostas3)
    p_pares = combinar_ordens(P1)
    theta = np.array([bradley_terry(p_pares[k]) for k in range(len(ids))])

    metodos = {nome: prever(m, X, Y.shape, gab, area, theta) for nome, m in cfg["metodos"].items()}
    resultados = {nome: metricas(P, Y, gab, area)[0] for nome, P in metodos.items()}
    brier = {nome: ((P - Y) ** 2).sum(axis=1) for nome, P in metodos.items()}

    b = cfg["bootstrap"]
    hipoteses = []
    for h in cfg["hipoteses"]:
        if h["tipo"] == "diferenca_brier":
            d = brier[h["metodo"]] - brier[h["comparador"]]
            bs = bootstrap_grupos(d, grupos, b["reamostragens"], b["semente"])
            ic = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
            sustentada = ic[1] < 0
            estimativa = float(d.mean())
        elif h["tipo"] == "principal_distrator_acima_do_acaso":
            v = acerto_principal_distrator_por_item(metodos[h["metodo"]], Y, gab)
            bs = bootstrap_grupos(v, grupos, b["reamostragens"], b["semente"])
            ic = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
            sustentada = ic[0] > h["acaso"]
            estimativa = float(v.mean())
        hipoteses.append({**h, "estimativa": estimativa, "ic95": ic, "sustentada": bool(sustentada)})

    saida = {"ano": ano, "n_itens": len(ids), "congelamento": args.congelamento,
             "hipoteses": hipoteses, "resultados": resultados,
             "diagnosticos_pares": diagnosticos(P1, p_pares, Y, gab),
             "previsoes": {nome: {i: dict(zip(LETRAS, map(float, p))) for i, p in zip(ids, P)}
                           for nome, P in metodos.items()}}
    prefixo = RAIZ / args.saida
    prefixo.parent.mkdir(parents=True, exist_ok=True)
    prefixo.with_suffix(".json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    prefixo.with_suffix(".md").write_text(markdown(saida), encoding="utf-8")
    print(markdown(saida))


def markdown(s):
    f = lambda v: "—" if v is None else f"{v:.4f}"
    L = [f"# Teste da configuração congelada: ENEM {s['ano']} ({s['n_itens']} itens)", "",
         "## Hipóteses pré-registradas", "",
         "| Id | Hipótese | Estimativa | IC 95% | Sustentada? |", "|---|---|---|---|---|"]
    for h in s["hipoteses"]:
        L.append(f"| {h['id']} | {h['descricao']} | {h['estimativa']:+.5f} | "
                 f"[{h['ic95'][0]:+.5f}; {h['ic95'][1]:+.5f}] | {'sim' if h['sustentada'] else 'não'} |")
    dg = s["diagnosticos_pares"]
    L += ["", "## Comparações entre pares (descritivo)", "",
          f"- Consistência entre as duas ordens: {dg['consistencia_entre_ordens']:.4f}",
          f"- Proporção em que o Jev escolhe a alternativa apresentada primeiro: {dg['proporcao_escolhe_a_primeira']:.4f}",
          "", "| Tipo de par | Acurácia | Pares |", "|---|---|---|"]
    for t, v in dg["acuracia_por_par"].items():
        L.append(f"| {t} | {v['acuracia']:.4f} | {v['n_pares']} |")
    L += ["", "## Métricas descritivas", "",
          "| Método | Brier | MAE | Spearman | Brier distr. | Spearman distr. | Principal distrator | AUC <5% |",
          "|---|---|---|---|---|---|---|---|"]
    for nome, r in sorted(s["resultados"].items(), key=lambda kv: kv[1]["brier"]):
        L.append(f"| {nome} | {f(r['brier'])} | {f(r['mae'])} | {f(r['spearman_intraitem'])} | "
                 f"{f(r['brier_distratores'])} | {f(r['spearman_distratores'])} | "
                 f"{f(r['acerto_principal_distrator'])} | {f(r['auc_nao_funcional'])} |")
    areas = sorted(next(iter(s["resultados"].values()))["brier_por_area"])
    L += ["", "## Brier por área (descritivo)", "", "| Método | " + " | ".join(areas) + " |",
          "|---|" + "---|" * len(areas)]
    for nome, r in sorted(s["resultados"].items(), key=lambda kv: kv[1]["brier"]):
        L.append(f"| {nome} | " + " | ".join(f(r["brier_por_area"][a]) for a in areas) + " |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
