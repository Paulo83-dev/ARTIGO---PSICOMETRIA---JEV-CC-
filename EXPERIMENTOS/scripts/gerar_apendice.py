"""Gera ARTIGO/secoes/08_apendices.tex a partir das definições usadas nas chamadas aos modelos,
para que o texto do apêndice seja idêntico ao que os modelos receberam.

Uso:
    python EXPERIMENTOS/scripts/gerar_apendice.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import perguntas_rodada1 as r1  # noqa: E402
import perguntas_rodada2 as r2  # noqa: E402
import perguntas_rodada3 as r3  # noqa: E402
import rodar_llm  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "ARTIGO" / "secoes" / "08_apendices.tex"

NOMES = {
    "q1a": "Atratividade (convencimento)", "q1b": "Atratividade (proporção) --- pergunta de atratividade principal",
    "q2": "Plausibilidade", "q3": "Esforço para descartar", "q4": "É a resposta correta?",
    "q5": "Verdade local", "q6": "Correção parcial", "q7": "Eco do texto", "q9": "Equívoco comum",
    "q10": "Combinação incorreta de informações", "q11": "Oposição", "q12": "Fora do tema",
    "q13": "Apelo do senso comum", "q14": "Confusão conceitual", "q15": "Generalização excessiva",
    "q16": "Conhecimento prévio no lugar do texto", "q17": "Resposta a outra pergunta", "q18": "Eco do comando",
}


def tex(s):
    """Escapa texto para LaTeX e formata o caminho `alternativas.X` como código."""
    s = str(s)
    trocas = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
              "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    s = "".join(trocas.get(c, c) for c in s)
    s = re.sub(r"`([^`]+)`", r"\\texttt{\1}", s)
    return s.replace('"', "''")


def descrever(pid, q):
    q = r1._substituir(q, "C")
    L = [f"\\paragraph{{{tex(NOMES[pid])}}} (\\texttt{{{pid}}}, tipo {q['type'].capitalize()})", ""]
    for chave, rotulo in (("pergunta", "Pergunta"), ("foco", "Foco")):
        if chave in q["instructions"]:
            L.append(f"\\textit{{{rotulo}:}} {tex(q['instructions'][chave])}\\\\")
    if q["type"] == "score":
        L += ["\\textit{Níveis (do mais baixo ao mais alto):}", "\\begin{enumerate}[nosep,label=\\arabic*.,start=0]"]
        for n in q["criteria"]:
            L.append(f"  \\item {tex(n)}" if isinstance(n, str) else f"  \\item {tex(n['situacao'])}: {tex(n['sinais'])}")
        L.append("\\end{enumerate}")
    elif q["type"] == "noul":
        L += [f"\\textit{{Sim:}} {tex(q['criteria']['true'])}\\\\", f"\\textit{{Não:}} {tex(q['criteria']['false'])}"]
    return L + [""]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    L = ["% 08_apendices: GERADO AUTOMATICAMENTE por EXPERIMENTOS/scripts/gerar_apendice.py; não editar à mão.", "",
         "\\section{Perguntas feitas ao Jev}\\label{ap:perguntas}", "",
         "As perguntas estão reproduzidas exatamente como enviadas ao modelo, com a alternativa C como exemplo; "
         "nas demais alternativas, só muda a letra no caminho \\texttt{alternativas.X}. "
         "Em cada requisição, o estado foi o objeto de entrada da questão, sem gabarito. "
         "O código entre parênteses identifica a pergunta nos arquivos do repositório.", "",
         "\\subsection{Rodada 1: nove perguntas por alternativa}", ""]
    for pid, q in r1.PERGUNTAS.items():
        L += descrever(pid, q)
    L += ["\\subsection{Rodada 2: mecanismos de atração dos distratores}", ""]
    for pid, q in r2.PERGUNTAS.items():
        L += descrever(pid, q)
    par = r3.pergunta_par("D", "B")
    L += ["\\subsection{Rodada 3: comparações entre pares}", "",
          "Uma pergunta do tipo Choice para cada um dos 20 pares ordenados de alternativas. Exemplo para o par (D, B), "
          "com D apresentada primeiro:", "",
          f"\\textit{{Pergunta:}} {tex(par['instructions']['pergunta'])}\\\\",
          f"\\textit{{Foco:}} {tex(par['instructions']['foco'])}\\\\",
          "\\textit{Opções (nesta ordem):}", "\\begin{itemize}[nosep]"]
    L += [f"  \\item \\texttt{{{k}}}: {tex(v)}" for k, v in par["criteria"].items()]
    L += ["\\end{itemize}", "Na ordem inversa, a pergunta cita B primeiro e as opções aparecem na ordem B, D.", ""]

    cfg = json.loads((RAIZ / "EXPERIMENTOS/congelamento_teste_2024.json").read_text(encoding="utf-8"))
    m = cfg["metodos"]
    p = m["q1b+pares (principal)"]
    L += ["\\section{Parâmetros congelados}\\label{ap:parametros}", "",
          "Parâmetros ajustados em todas as questões de 2025 e aplicados sem alteração às de 2024 "
          "(arquivos \\texttt{congelamento\\_teste\\_2024.json} e \\texttt{congelamento\\_llm\\_2024.json} do repositório).", "",
          "\\begin{table}[ht]", "\\centering", "\\small", "\\caption{Parâmetros congelados do Jev e das linhas de base.}",
          "\\begin{tabular}{ll}", "\\toprule", "Método & Parâmetros \\\\", "\\midrule",
          f"Atratividade + pares (principal) & $\\beta_1 = {p['beta_padronizado'][0]:.5f}$, $\\beta_2 = {p['beta_padronizado'][1]:.5f}$ "
          f"(padronizados); médias $({p['media'][0]:.5f};\\ {p['media'][1]:.5f})$, desvios $({p['dp'][0]:.5f};\\ {p['dp'][1]:.5f})$ \\\\",
          f"Atratividade (proporção) & $\\beta = {m['q1b']['beta']:.5f}$ ($T = {m['q1b']['temperatura_equivalente']:.4f}$) \\\\",
          f"Atratividade (convencimento) & $\\beta = {m['q1a (sensibilidade)']['beta']:.5f}$ "
          f"($T = {m['q1a (sensibilidade)']['temperatura_equivalente']:.4f}$) \\\\",
          f"Oracle & taxa média de acerto $= {m['oracle (usa gabarito)']['acerto_medio']:.5f}$ \\\\",
          "Média por área & proporção média de cada letra em 2025, por área \\\\",
          "Bradley-Terry & $\\lambda = 0{,}01$; soma das forças igual a zero \\\\",
          "\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    llm = json.loads((RAIZ / "EXPERIMENTOS/congelamento_llm_2024.json").read_text(encoding="utf-8"))["metodos_llm"]
    c = llm["LLM B q1b+pares"]
    L += ["\\begin{table}[ht]", "\\centering", "\\small", "\\caption{Parâmetros congelados do LLM.}",
          "\\begin{tabular}{ll}", "\\toprule", "Método & Parâmetros \\\\", "\\midrule",
          f"Método A (letras) & $T = {llm['LLM A (letras)']['temperatura']:.4f}$ \\\\",
          f"Método B, atratividade & $\\beta = {llm['LLM B q1b']['beta']:.5f}$ \\\\",
          f"Método B, pares & $\\beta = {llm['LLM B pares']['beta']:.5f}$ \\\\",
          f"Método B, atratividade + pares & $\\beta_1 = {c['beta_padronizado'][0]:.5f}$, $\\beta_2 = {c['beta_padronizado'][1]:.5f}$ (padronizados) \\\\",
          "\\bottomrule", "\\end{tabular}", "\\end{table}", ""]

    L += ["\\section{Instruções do LLM}\\label{ap:llm}", "",
          "Mensagens de sistema usadas com o \\texttt{z-ai/glm-5.3-flash}. A mensagem do usuário continha a questão em texto "
          "(texto de apoio, texto principal e alternativas A--E) seguida, no método B, da pergunta, do foco e dos níveis "
          "ou das opções, com a mesma redação das perguntas feitas ao Jev (o caminho \\texttt{alternativas.X} foi "
          "substituído por ``alternativa X'').", "",
          "\\begin{itemize}[nosep]",
          f"  \\item Método A: {tex(rodar_llm.SISTEMA_LETRA)}",
          f"  \\item Método B, atratividade: {tex(rodar_llm.SISTEMA_NIVEL)}",
          f"  \\item Método B, pares: {tex(rodar_llm.SISTEMA_PAR)}",
          "\\end{itemize}", ""]
    SAIDA.write_text("\n".join(L), encoding="utf-8")
    print("Gerado:", SAIDA)


if __name__ == "__main__":
    main()
