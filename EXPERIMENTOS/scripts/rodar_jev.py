"""Envia as perguntas de uma rodada ao Jev, um item por requisição, e grava tudo em JSONL.

Uso:
    python EXPERIMENTOS/scripts/rodar_jev.py --rodada 1 --ano 2025 --saida EXPERIMENTOS/resultados/jev_rodada1_2025.jsonl

Cada linha do JSONL guarda o corpo exato enviado, o SHA-256 desse corpo, o status HTTP e a
resposta bruta. Itens que já têm resposta válida no arquivo de saída não são reenviados.
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
import perguntas_rodada1  # noqa: E402
import perguntas_rodada2  # noqa: E402
import perguntas_rodada3  # noqa: E402

RODADAS = {1: perguntas_rodada1, 2: perguntas_rodada2, 3: perguntas_rodada3}

RAIZ = Path(__file__).resolve().parents[2]
ACERVO = RAIZ / "exportacao_acervo" / "acervo_questoes_aprovadas_enem_2024_2025.json"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODELO = "jev-1.13.0"
TENTATIVAS = 4


def ler_chave():
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.strip().startswith("TYPESAFE_API_KEY="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("TYPESAFE_API_KEY não encontrada no .env")


def corpo_canonico(corpo):
    return json.dumps(corpo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def ja_respondidos(saida):
    if not saida.exists():
        return set()
    feitos = set()
    for linha in saida.read_text(encoding="utf-8").splitlines():
        reg = json.loads(linha)
        if reg.get("status_http") == 200:
            feitos.add(reg["registro_id"])
    return feitos


def enviar(cliente, chave, corpo):
    espera = 2.0
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            r = cliente.post(ENDPOINT, json=corpo, headers={"Authorization": f"Bearer {chave}"}, timeout=120)
        except httpx.TransportError as erro:
            if tentativa == TENTATIVAS:
                return None, {"erro_transporte": str(erro)}, tentativa
        else:
            if r.status_code not in (429, 500, 502, 503, 529) or tentativa == TENTATIVAS:
                try:
                    return r.status_code, r.json(), tentativa
                except ValueError:
                    return r.status_code, {"texto": r.text}, tentativa
            espera = float(r.headers.get("retry-after", espera))
        time.sleep(espera)
        espera *= 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--itens", nargs="*", help="registro_id dos itens; omitido = todos do ano")
    ap.add_argument("--ano", type=int, help="usar todos os itens deste ano")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--rodada", type=int, choices=sorted(RODADAS), default=1)
    args = ap.parse_args()

    questoes = json.loads(ACERVO.read_text(encoding="utf-8"))["questoes"]
    if args.itens:
        por_id = {q["registro_id"]: q for q in questoes}
        itens = [por_id[i] for i in args.itens]
    elif args.ano:
        itens = [q for q in questoes if q["ano"] == args.ano]
    else:
        raise SystemExit("Informe --itens ou --ano")

    saida = RAIZ / args.saida
    saida.parent.mkdir(parents=True, exist_ok=True)
    feitos = ja_respondidos(saida)
    perguntas = RODADAS[args.rodada].montar_perguntas()
    chave = ler_chave()

    with httpx.Client() as cliente, saida.open("a", encoding="utf-8") as f:
        for q in itens:
            if q["registro_id"] in feitos:
                print(f"{q['registro_id']}: já respondido, pulando")
                continue
            # O state é o objeto `entrada`, sem gabarito, parâmetros TRI ou frequências.
            corpo = {"state": q["entrada"], "model": MODELO, "questions": perguntas}
            status, resposta, tentativas = enviar(cliente, chave, corpo)
            registro = {
                "registro_id": q["registro_id"],
                "momento_utc": datetime.now(timezone.utc).isoformat(),
                "sha256_corpo": hashlib.sha256(corpo_canonico(corpo).encode("utf-8")).hexdigest(),
                "status_http": status,
                "tentativas": tentativas,
                "corpo": corpo,
                "resposta": resposta,
            }
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
            f.flush()
            uso = resposta.get("usage", {}) if isinstance(resposta, dict) else {}
            print(f"{q['registro_id']}: HTTP {status}, modelo {resposta.get('model') if isinstance(resposta, dict) else '-'}, "
                  f"tokens de entrada {uso.get('input_tokens')}")


if __name__ == "__main__":
    main()
