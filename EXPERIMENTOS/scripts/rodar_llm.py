"""Chamadas ao LLM de comparação (ver EXPERIMENTOS/comparacao_llm_especificacao.md).

Método A: resposta com uma letra, em 5 rotações cíclicas das alternativas (probabilidades das letras).
Método B: as mesmas perguntas feitas ao Jev (q1b por alternativa e os 20 pares ordenados).

Uso:
    python EXPERIMENTOS/scripts/rodar_llm.py --ano 2025 --saida EXPERIMENTOS/resultados/llm_glm_2025.jsonl

Cada linha do JSONL é uma chamada: item, método, chave, corpo exato, SHA-256 do corpo, status,
provedor, conteúdo, probabilidades extraídas, tokens, custo e tempo. Chamadas já concluídas são puladas.
"""

import argparse
import hashlib
import json
import math
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from perguntas_rodada1 import LETRAS, PERGUNTAS as P_R1  # noqa: E402
from perguntas_rodada3 import PARES_ORDENADOS, pergunta_par  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
ACERVO = RAIZ / "exportacao_acervo" / "acervo_questoes_aprovadas_enem_2024_2025.json"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODELO = "z-ai/glm-5.3-flash"
PROVEDOR = "Together"
TENTATIVAS = 6
PARALELO = 8

SISTEMA_LETRA = "Responda à questão de múltipla escolha com apenas uma letra (A, B, C, D ou E), sem explicação."
SISTEMA_NIVEL = "Responda apenas com o número do nível (0, 1, 2, 3 ou 4), sem explicação."
SISTEMA_PAR = "Responda apenas com a letra da alternativa escolhida, sem explicação."


def ler_chave():
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.strip().startswith("OPENROUTER_API_KEY="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("OPENROUTER_API_KEY não encontrada no .env")


def sem_caminho(texto, letra):
    # O LLM recebe a questão em texto; o caminho `alternativas.X` do Jev vira "a alternativa X".
    return texto.replace(f"a alternativa em `alternativas.{letra}`", f"a alternativa {letra}") \
                .replace(f"A alternativa em `alternativas.{letra}`", f"A alternativa {letra}") \
                .replace(f"`alternativas.{letra}`", f"alternativa {letra}")


def texto_questao(entrada, ordem=LETRAS):
    """Questão em texto. `ordem[p]` é a alternativa original exibida na posição LETRAS[p]."""
    partes = []
    if entrada["apoio_compartilhado"].strip():
        partes.append(entrada["apoio_compartilhado"].strip())
    partes.append(entrada["texto_principal"].strip())
    alts = "\n".join(f"{LETRAS[p]}) {entrada['alternativas'][orig]}" for p, orig in enumerate(ordem))
    return "\n\n".join(partes) + "\n\nAlternativas:\n" + alts


def montar_chamadas(entrada):
    """Lista de (metodo, chave, alvo, mensagens, metadados)."""
    chamadas = []
    # Método A: 5 rotações cíclicas
    for r in range(5):
        ordem = [LETRAS[(p + r) % 5] for p in range(5)]
        msgs = [{"role": "system", "content": SISTEMA_LETRA},
                {"role": "user", "content": texto_questao(entrada, ordem)}]
        chamadas.append(("A_letras", f"rot{r}", LETRAS, msgs, {"ordem_exibida": ordem}))
    # Método B: q1b por alternativa
    q1b = P_R1["q1b"]
    for alt in LETRAS:
        niveis = "\n".join(f"{i} — {n['situacao']}: {n['sinais']}" for i, n in enumerate(q1b["criteria"]))
        instr = (f"Pergunta: {sem_caminho(q1b['instructions']['pergunta'].replace('{alt}', alt), alt)}\n"
                 f"Foco: {q1b['instructions']['foco']}\n\nNíveis:\n{niveis}")
        msgs = [{"role": "system", "content": SISTEMA_NIVEL},
                {"role": "user", "content": texto_questao(entrada) + "\n\n" + instr}]
        chamadas.append(("B_q1b", alt, list("01234"), msgs, {}))
    # Método B: pares ordenados
    for a, b in PARES_ORDENADOS:
        q = pergunta_par(a, b)
        opcoes = "\n".join(f"{k}: {sem_caminho(sem_caminho(v, a), b)}" for k, v in q["criteria"].items())
        instr = (f"Pergunta: {sem_caminho(sem_caminho(q['instructions']['pergunta'], a), b)}\n"
                 f"Foco: {q['instructions']['foco']}\n\nOpções:\n{opcoes}")
        msgs = [{"role": "system", "content": SISTEMA_PAR},
                {"role": "user", "content": texto_questao(entrada) + "\n\n" + instr}]
        chamadas.append(("B_pares", f"{a}_{b}", [a, b], msgs, {}))
    return chamadas


def extrair_probabilidades(logprobs, alvo):
    """Probabilidades dos símbolos-alvo no primeiro token da resposta que seja um deles.
    Símbolo ausente entre os devolvidos recebe a menor probabilidade daquela posição."""
    conteudo = (logprobs or {}).get("content") or []
    for pos in conteudo:
        if pos["token"].strip() in alvo:
            top = pos.get("top_logprobs") or []
            probs = {s: 0.0 for s in alvo}
            for t in top:
                s = t["token"].strip()
                if s in probs:
                    probs[s] += math.exp(t["logprob"])
            piso = min(math.exp(t["logprob"]) for t in top) if top else 0.0
            ausentes = [s for s in alvo if probs[s] == 0.0]
            for s in ausentes:
                probs[s] = piso
            total = sum(probs.values())
            return {s: v / total for s, v in probs.items()}, ausentes
    return None, list(alvo)


def chamar(cliente, chave, mensagens):
    corpo = {"model": MODELO, "messages": mensagens, "temperature": 0, "max_tokens": 4000,
             "logprobs": True, "top_logprobs": 20, "reasoning": {"effort": "low"},
             "provider": {"order": [PROVEDOR], "allow_fallbacks": False, "require_parameters": True}}
    espera = 2.0
    for tentativa in range(1, TENTATIVAS + 1):
        t0 = time.perf_counter()
        try:
            r = cliente.post(ENDPOINT, json=corpo, headers={"Authorization": f"Bearer {chave}"}, timeout=180)
            dt = time.perf_counter() - t0
            if r.status_code == 200 or r.status_code not in (408, 429, 500, 502, 503, 529) or tentativa == TENTATIVAS:
                return corpo, r.status_code, r.json(), tentativa, dt
        except (httpx.TransportError, ValueError) as erro:
            if tentativa == TENTATIVAS:
                return corpo, None, {"erro": str(erro)}, tentativa, time.perf_counter() - t0
        time.sleep(espera)
        espera = min(espera * 2, 60)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--itens", nargs="*")
    args = ap.parse_args()

    questoes = [q for q in json.loads(ACERVO.read_text(encoding="utf-8"))["questoes"] if q["ano"] == args.ano]
    if args.itens:
        questoes = [q for q in questoes if q["registro_id"] in args.itens]
    saida = RAIZ / args.saida
    saida.parent.mkdir(parents=True, exist_ok=True)
    feitos = set()
    if saida.exists():
        for linha in saida.read_text(encoding="utf-8").splitlines():
            reg = json.loads(linha)
            if reg["status_http"] == 200 and reg["probabilidades"] is not None:
                feitos.add((reg["registro_id"], reg["metodo"], reg["chave"]))

    tarefas = [(q["registro_id"], *c) for q in questoes for c in montar_chamadas(q["entrada"])
               if (q["registro_id"], c[0], c[1]) not in feitos]
    print(f"{len(tarefas)} chamadas a fazer ({len(feitos)} já feitas)")
    chave = ler_chave()
    trava = threading.Lock()
    contagem = {"ok": 0, "falha": 0, "custo": 0.0}

    def executar(tarefa):
        rid, metodo, ch, alvo, msgs, meta = tarefa
        corpo, status, resp, tent, dt = chamar(cliente, chave, msgs)
        probs, ausentes, conteudo, provedor, uso = None, None, None, None, {}
        if status == 200:
            c = resp["choices"][0]
            conteudo, provedor, uso = c["message"].get("content"), resp.get("provider"), resp.get("usage", {})
            probs, ausentes = extrair_probabilidades(c.get("logprobs"), alvo)
        reg = {"registro_id": rid, "metodo": metodo, "chave": ch, **meta,
               "momento_utc": datetime.now(timezone.utc).isoformat(),
               "sha256_corpo": hashlib.sha256(json.dumps(corpo, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
               "status_http": status, "tentativas": tent, "segundos": round(dt, 3), "provedor": provedor,
               "conteudo": conteudo, "probabilidades": probs, "simbolos_ausentes": ausentes,
               "tokens_entrada": uso.get("prompt_tokens"), "tokens_saida": uso.get("completion_tokens"),
               "tokens_raciocinio": (uso.get("completion_tokens_details") or {}).get("reasoning_tokens"),
               "custo_usd": uso.get("cost"), "corpo": corpo,
               "resposta": resp if status != 200 else {"logprobs": resp["choices"][0].get("logprobs"),
                                                       "id": resp.get("id")}}
        with trava:
            with saida.open("a", encoding="utf-8") as f:
                f.write(json.dumps(reg, ensure_ascii=False) + "\n")
            ok = status == 200 and probs is not None
            contagem["ok" if ok else "falha"] += 1
            contagem["custo"] += uso.get("cost") or 0.0
            n = contagem["ok"] + contagem["falha"]
            if n % 200 == 0 or not ok:
                print(f"{n}/{len(tarefas)} feitas, {contagem['falha']} falhas, custo US$ {contagem['custo']:.4f}"
                      + ("" if ok else f" | falha: {rid} {metodo} {ch} HTTP {status}"))

    with httpx.Client() as cliente, ThreadPoolExecutor(PARALELO) as ex:
        for fut in as_completed([ex.submit(executar, t) for t in tarefas]):
            fut.result()
    print(f"Fim: {contagem['ok']} ok, {contagem['falha']} falhas, custo US$ {contagem['custo']:.4f}")


if __name__ == "__main__":
    main()
