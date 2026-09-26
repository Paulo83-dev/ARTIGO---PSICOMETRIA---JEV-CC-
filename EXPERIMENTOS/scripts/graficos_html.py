"""Acrescenta a cada questão elegível das páginas de revisão (VIZUALIZAÇÂO HTML/) um gráfico com a
proporção real de escolha de cada alternativa e a previsão do método principal (atratividade + pares), e um
seletor para ordenar as questões pelo Brier, pelo erro na taxa de acerto ou pela taxa de acerto real.

- 2025: previsões fora da dobra (validação cruzada), de EXPERIMENTOS/resultados/analise_rodada3_2025.json;
- 2024: previsões com os parâmetros congelados (teste), de EXPERIMENTOS/resultados/teste_2024.json.

O bloco fica entre marcadores e é substituído a cada execução; rodar de novo não duplica nada.

Uso:
    python EXPERIMENTOS/scripts/graficos_html.py
"""

import json
import math
import re
import sys
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTA = RAIZ / "VIZUALIZAÇÂO HTML"
LETRAS = "ABCDE"
INICIO, FIM = "<!-- previsao:inicio -->", "<!-- previsao:fim -->"
CSS_INICIO, CSS_FIM = "/* previsao:css:inicio */", "/* previsao:css:fim */"

COR_REAL, COR_PREV = "#8a96a3", "#2a5c8a"
CSS = f"""{CSS_INICIO}
.previsao {{margin-top:14px;padding:12px 14px;border:1px solid #d7dee6;border-radius:6px;background:#fbfcfd}}
.previsao h4 {{margin:0 0 4px}} .previsao .nota {{font-size:.82rem;color:#5b6570;margin:0 0 8px}}
.previsao .legenda {{display:flex;gap:16px;font-size:.85rem;color:#425365;margin-bottom:4px;flex-wrap:wrap}}
.previsao .legenda span::before {{content:"";display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:6px;vertical-align:-1px;background:var(--c)}}
.previsao svg {{width:100%;max-width:640px;height:auto;display:block}}
.previsao svg text {{font-family:system-ui,Segoe UI,sans-serif;font-size:12px;fill:#425365}}
.previsao svg .letra {{font-weight:700;fill:#17212b}} .previsao rect:hover {{opacity:.8}}
.previsao .resumo {{font-size:.85rem;color:#425365;margin:6px 0 0}}
{CSS_FIM}"""


def pct(v):
    return f"{100 * v:.1f}%".replace(".", ",")


def svg(real, prev, gabarito):
    larg, esq, dir_, linha = 600, 58, 58, 34
    util = larg - esq - dir_
    topo = max(max(real.values()), max(prev.values()))
    escala = max(0.6, math.ceil(topo * 10) / 10)  # eixo de 0 a pelo menos 60%
    alt = linha * 5 + 22
    x = lambda v: esq + util * v / escala
    partes = [f'<svg viewBox="0 0 {larg} {alt}" role="img" aria-label="Proporção real e prevista por alternativa">']
    for t in [i / 10 for i in range(0, int(round(escala * 10)) + 1, 2 if escala > 0.6 else 1)]:
        partes.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="0" y2="{linha * 5}" stroke="#e3e8ee"/>'
                      f'<text x="{x(t):.1f}" y="{linha * 5 + 15}" text-anchor="middle">{round(t * 100)}%</text>')
    for i, k in enumerate(LETRAS):
        y0 = i * linha + 5
        rotulo = f"{k} ✓" if k == gabarito else k
        partes.append(f'<text class="letra" x="{esq - 10}" y="{y0 + 16}" text-anchor="end">{rotulo}</text>')
        for j, (serie, v, cor) in enumerate((("Real", real[k], COR_REAL), ("Previsto", prev[k], COR_PREV))):
            y = y0 + j * 12
            w = max(x(v) - esq, 1.5)
            partes.append(f'<rect x="{esq}" y="{y}" width="{w:.1f}" height="10" rx="2" fill="{cor}">'
                          f'<title>{k}, {serie.lower()}: {pct(v)}</title></rect>'
                          f'<text x="{esq + w + 5:.1f}" y="{y + 9}">{pct(v)}</text>')
    partes.append("</svg>")
    return "".join(partes)


def bloco(real, prev, gabarito, ano):
    brier = sum((prev[k] - real[k]) ** 2 for k in LETRAS)
    distr = [k for k in LETRAS if k != gabarito]
    d_real = max(distr, key=real.get)
    d_prev = max(distr, key=prev.get)
    nota = ("Previsão fora da dobra (validação cruzada em 2025): o ajuste que gerou esta previsão não usou esta questão."
            if ano == 2025 else
            "Previsão do teste: parâmetros congelados com as questões de 2025, sem nenhum ajuste em 2024.")
    return (f'{INICIO}<section class="previsao"><h4>Escolhas reais × previsão do método principal</h4>'
            f'<p class="nota">{escape(nota)} ✓ indica o gabarito.</p>'
            f'<div class="legenda"><span style="--c:{COR_REAL}">Real (microdados)</span>'
            f'<span style="--c:{COR_PREV}">Previsto (atratividade + pares)</span></div>'
            f'{svg(real, prev, gabarito)}'
            f'<p class="resumo">Distrator mais escolhido: real <strong>{d_real}</strong>, previsto <strong>{d_prev}</strong> '
            f'{"(acertou)" if d_real == d_prev else "(errou)"} · Brier da questão: {f"{brier:.4f}".replace(".", ",")}'
            f'</p></section>{FIM}')


ORD_INICIO, ORD_FIM = "<!-- ordenar:inicio -->", "<!-- ordenar:fim -->"
ORD_JS_INICIO, ORD_JS_FIM = "<!-- ordenar:script:inicio -->", "<!-- ordenar:script:fim -->"
ORDENADOR = (ORD_INICIO + '<select id="ordenar" aria-label="Ordenar questões">'
             '<option value="ordem:asc">Ordem da prova</option>'
             '<option value="brier:asc">Brier: melhores previsões primeiro</option>'
             '<option value="brier:desc">Brier: piores previsões primeiro</option>'
             '<option value="erro:desc">Maior erro na taxa de acerto primeiro</option>'
             '<option value="real:desc">Mais fáceis primeiro (acerto real)</option>'
             '<option value="real:asc">Mais difíceis primeiro (acerto real)</option>'
             '</select>' + ORD_FIM)
# Reordena os <article> dentro do elemento pai; questões sem previsão (excluídas) vão para o fim.
SCRIPT_ORDENAR = ORD_JS_INICIO + """<script>
(() => {
  const sel = document.getElementById('ordenar');
  const itens = [...document.querySelectorAll('.item')];
  itens.forEach((it, i) => { it.dataset.ordem = i; });
  const pai = itens[0].parentNode;
  const campos = {brier: 'brier', erro: 'erroAcerto', real: 'acertoReal'};
  const valor = (it, campo) => campo === 'ordem' ? +it.dataset.ordem
    : (it.dataset[campos[campo]] === undefined ? null : +it.dataset[campos[campo]]);
  sel.addEventListener('change', () => {
    const [campo, sentido] = sel.value.split(':');
    const ordenados = [...itens].sort((a, b) => {
      const x = valor(a, campo), y = valor(b, campo);
      if (x === null || y === null) return (x === null) - (y === null) || a.dataset.ordem - b.dataset.ordem;
      return (sentido === 'desc' ? y - x : x - y) || a.dataset.ordem - b.dataset.ordem;
    });
    ordenados.forEach(it => pai.appendChild(it));
  });
})();
</script>""" + ORD_JS_FIM


def atributos(artigo, real, prev, gabarito):
    """Grava no <article> os valores usados pelo ordenador (substitui os de uma execução anterior)."""
    artigo = re.sub(r' data-(?:brier|acerto-real|acerto-prev|erro-acerto)="[^"]*"', "", artigo)
    brier = sum((prev[k] - real[k]) ** 2 for k in LETRAS)
    attrs = (f' data-brier="{brier:.6f}" data-acerto-real="{real[gabarito]:.6f}" '
             f'data-acerto-prev="{prev[gabarito]:.6f}" data-erro-acerto="{abs(prev[gabarito] - real[gabarito]):.6f}"')
    return artigo.replace(">", attrs + ">", 1)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    acervo = json.loads((RAIZ / "exportacao_acervo/acervo_questoes_aprovadas_enem_2024_2025.json").read_text(encoding="utf-8"))
    questoes = {q["registro_id"]: q for q in acervo["questoes"]}
    previsoes = {
        2025: json.loads((RAIZ / "EXPERIMENTOS/resultados/analise_rodada3_2025.json").read_text(encoding="utf-8"))
        ["previsoes_fora_da_dobra"]["q1b+pares_bradley_terry"],
        2024: json.loads((RAIZ / "EXPERIMENTOS/resultados/teste_2024.json").read_text(encoding="utf-8"))
        ["previsoes"]["q1b+pares (principal)"],
    }
    for ano, prev in previsoes.items():
        caminho = PASTA / f"REVISAO_INTEGRAL_ACERVO_{ano}.html"
        html = caminho.read_text(encoding="utf-8")
        # remove a versão anterior junto com a quebra de linha acrescentada, para que rodar de novo não mude nada
        html = re.sub(re.escape(INICIO) + ".*?" + re.escape(FIM) + "\n", "", html, flags=re.S)
        html = re.sub("\n" + re.escape(CSS_INICIO) + ".*?" + re.escape(CSS_FIM) + "\n", "", html, flags=re.S)
        html = html.replace("</style>", "\n" + CSS + "\n</style>", 1)
        for ini, fim in ((ORD_INICIO, ORD_FIM), (ORD_JS_INICIO, ORD_JS_FIM)):
            html = re.sub(re.escape(ini) + ".*?" + re.escape(fim), "", html, flags=re.S)
        html = html.replace('<span id="shown">', ORDENADOR + '<span id="shown">', 1)
        html = html.replace("</body>", SCRIPT_ORDENAR + "</body>", 1)

        feitos = 0

        def inserir(m):
            nonlocal feitos
            artigo = m.group(0)
            rid = re.search(r"<small>(\d{4}-[A-Z]{2}-\d{3}(?:-L\d)?)", artigo).group(1)  # 2024 e 2025 têm cabeçalhos diferentes
            if rid not in prev:
                return artigo
            q = questoes[rid]
            real = q["respostas_observadas"]["proporcoes_validas"]
            feitos += 1
            artigo = atributos(artigo, real, prev[rid], q["gabarito"])
            # depois da lista de alternativas (<ul> em 2024, <ol> dentro de <section> em 2025), antes dos detalhes
            return re.sub(r"</(?:ul|ol)>(?:</section>)?\n",
                          lambda f: f.group(0) + bloco(real, prev[rid], q["gabarito"], ano) + "\n", artigo, count=1)

        html = re.sub(r'<article class="item".*?</article>', inserir, html, flags=re.S)
        caminho.write_text(html, encoding="utf-8")
        print(f"{ano}: gráficos em {feitos} de {len(prev)} questões")


if __name__ == "__main__":
    main()
