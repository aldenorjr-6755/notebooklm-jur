#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
exportar_para_tecjustica.py — injeta nossa transcrição no app TecJustiça
Transcribe, para usar só a tela de revisão dele.

POR QUE EXISTE
    O app (MIT, github.com/marcosmarf27/tecjustica-transcribe-desktop-releases)
    tem uma tela de revisão que o nosso pipeline não tem: clicar numa fala e o
    vídeo pular para aquele segundo, renomear SPEAKER_00 para "Juíza" de uma
    vez em toda a transcrição, corrigir a palavra errada, exportar DOCX.
    O motor dele, porém, é WhisperX + CUDA e exige aceitar mais duas licenças
    de modelo no HuggingFace.

    Este script faz o caminho do meio: o trabalho pesado continua sendo do
    transcrever_audiencia.py + diarizar.py, e o resultado é escrito direto no
    armazenamento do app, que passa a servir de tela de revisão.

COMO O APP GUARDA OS DADOS (auditado no código-fonte da v1.3.0)
    Apesar de o preload.js falar em "SQLite CRUD", não há SQLite: é um array
    JSON simples em %APPDATA%\TecJustiça Transcribe\transcriptions.json.
    Arquivo ausente é lido como lista vazia, então criar do zero é seguro.

USO
    # 1) transcrever e diarizar como sempre
    python tools/transcrever_audiencia.py audiencia.mp4 --saida audiencia.txt
    .venv-diar312/Scripts/python.exe tools/diarizar.py audiencia.mp4 \
        --transcricao audiencia.txt

    # 2) publicar no app (não precisa de torch — roda no Python 3.14)
    python tools/exportar_para_tecjustica.py audiencia.mp4 \
        --transcricao audiencia.txt

    # já nomeando quem é quem
    python tools/exportar_para_tecjustica.py audiencia.mp4 \
        --transcricao audiencia.txt \
        --rotulos "SPEAKER_00=Juíza,SPEAKER_01=Defesa"

CUIDADOS
  - FECHE o app antes de rodar: ele reescreve o transcriptions.json inteiro ao
    salvar e sobrescreveria o que inserimos aqui.
  - O formato é interno e não documentado, lido da v1.3.0. Atualização do app
    pode mudá-lo. Por isso o arquivo é copiado para .bak antes de qualquer
    escrita, e --conferir mostra o que seria feito sem gravar nada.
  - Reexecutar com o mesmo vídeo ATUALIZA o registro existente (casa por
    caminho do arquivo) em vez de duplicar, e preserva os nomes de falante que
    você já tiver dado dentro do app.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Reaproveita a lógica de casamento do diarizar.py — a atribuição de falante
# tem de ser idêntica à do .diarizado.txt, senão o app mostraria outra coisa.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from diarizar import (  # noqa: E402
    carregar_turnos,
    falante_por_sobreposicao,
    hhmmss,
    ler_transcricao,
    parse_rotulos,
)

PRODUTO = "TecJustiça Transcribe"  # build.productName do package.json do app


def erro(msg: str, codigo: int) -> int:
    print(f"ERRO: {msg}", file=sys.stderr)
    return codigo


def pasta_userdata() -> Path:
    """%APPDATA%\\TecJustiça Transcribe — o app.getPath('userData') do Electron."""
    import os

    appdata = os.environ.get("APPDATA")
    if not appdata:  # Linux/macOS, para quem rodar o AppImage
        base = Path.home() / ".config"
    else:
        base = Path(appdata)
    return base / PRODUTO


def montar_segmentos(linhas, turnos, duracao: float):
    """Transcrição + turnos -> segmentos no formato do app.

    O app usa start, end, text e speaker (player, fita e lista de segmentos).
    A nossa transcrição só guarda o INÍCIO de cada fala, arredondado ao
    segundo, então o fim de cada segmento é o início do seguinte — precisão de
    cerca de meio segundo, suficiente para clicar e ouvir, e é o mesmo critério
    que o diarizar.py usa para atribuir o falante.
    """
    inicios = sorted(i for i, _ in linhas if i is not None)
    segmentos = []
    for inicio, texto in linhas:
        if inicio is None:
            continue
        posteriores = [i for i in inicios if i > inicio]
        fim = min(posteriores) if posteriores else duracao
        fim = max(fim, inicio + 0.5)
        segmentos.append({
            "start": float(inicio),
            "end": float(min(fim, duracao)),
            "text": texto,
            "speaker": falante_por_sobreposicao(inicio, fim, turnos),
        })
    return segmentos


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Publica nossa transcrição no app TecJustiça Transcribe.")
    ap.add_argument("arquivo", help="vídeo/áudio da audiência (o app toca este arquivo)")
    ap.add_argument("--transcricao", required=True,
                    help="saída de transcrever_audiencia.py (ou o .diarizado.txt)")
    ap.add_argument("--diar", default=None,
                    help="o .diar.json (padrão: <arquivo>.diar.json)")
    ap.add_argument("--rotulos", default=None,
                    help='ex.: "SPEAKER_00=Juíza,SPEAKER_01=Defesa"')
    ap.add_argument("--modelo", default="small", help="só rótulo informativo no app")
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--userdata", default=None,
                    help="pasta de dados do app (padrão: %%APPDATA%%\\" + PRODUTO + ")")
    ap.add_argument("--conferir", action="store_true",
                    help="mostra o que faria, sem gravar nada")
    args = ap.parse_args()

    midia = Path(args.arquivo).resolve()
    if not midia.exists():
        return erro(f"arquivo não encontrado: {midia}", 1)

    transc = Path(args.transcricao)
    if not transc.exists():
        return erro(f"transcrição não encontrada: {transc}", 1)

    diar = Path(args.diar) if args.diar else Path(str(midia) + ".diar.json")
    if not diar.exists():
        return erro(f"{diar.name} não existe — rode antes:\n"
                    f"  .venv-diar312/Scripts/python.exe tools/diarizar.py "
                    f'"{midia.name}"', 2)

    try:
        rotulos = parse_rotulos(args.rotulos)
    except ValueError as e:
        return erro(str(e), 1)

    turnos, duracao = carregar_turnos(diar)
    segmentos = montar_segmentos(ler_transcricao(transc), turnos, duracao)
    if not segmentos:
        return erro(f"nenhuma linha no formato [hh:mm:ss] em {transc.name}", 3)

    vozes = sorted({s["speaker"] for s in segmentos})
    userdata = Path(args.userdata) if args.userdata else pasta_userdata()
    banco = userdata / "transcriptions.json"

    print(f"mídia .......: {midia}")
    print(f"segmentos ...: {len(segmentos)} | duração {hhmmss(duracao)}")
    print(f"falantes ....: {len(vozes)} — "
          + ", ".join(f"{v} -> {rotulos.get(v, v)}" for v in vozes))
    print(f"destino .....: {banco}")

    if not userdata.exists():
        print(f"\nA pasta do app não existe. Ela só aparece depois que o "
              f"{PRODUTO}\nfor instalado e aberto ao menos uma vez.",
              file=sys.stderr)
        if not args.conferir:
            return erro("nada foi gravado — instale/abra o app antes, ou use "
                        "--userdata para apontar outra pasta", 4)

    if args.conferir:
        print("\n[--conferir] nada gravado. Amostra dos 3 primeiros segmentos:")
        for s in segmentos[:3]:
            print(f"  [{hhmmss(s['start'])}->{hhmmss(s['end'])}] "
                  f"{rotulos.get(s['speaker'], s['speaker'])}: {s['text'][:48]}...")
        return 0

    try:
        registros = json.loads(banco.read_text(encoding="utf-8"))
        if not isinstance(registros, list):
            return erro(f"{banco.name} não é uma lista JSON — não vou mexer nele", 5)
    except FileNotFoundError:
        registros = []
    except json.JSONDecodeError as e:
        return erro(f"{banco.name} está corrompido ({e}) — não vou sobrescrever", 5)

    if banco.exists():
        backup = banco.with_suffix(".json.bak")
        shutil.copy2(banco, backup)
        print(f"backup ......: {backup.name}")

    agora = datetime.now(timezone.utc).isoformat()
    alvo = str(midia)
    idx = next((i for i, r in enumerate(registros)
                if r.get("filepath") == alvo), None)

    # Nomes de falante dados dentro do app têm precedência: quem renomeou lá
    # não quer ver o nome voltar para SPEAKER_00 na próxima publicação.
    mapa = dict(rotulos)
    if idx is not None and registros[idx].get("speaker_map_json"):
        try:
            mapa = {**rotulos, **json.loads(registros[idx]["speaker_map_json"])}
        except json.JSONDecodeError:
            pass

    registro = {
        "id": registros[idx]["id"] if idx is not None else str(uuid.uuid4()),
        "filename": midia.name,
        "filepath": alvo,
        "model": args.modelo,
        "language": args.idioma,
        "diarize": 1,
        "duration_seconds": round(duracao, 3),
        "status": "completed",
        "error_message": None,
        "segments_json": json.dumps(segmentos, ensure_ascii=False),
        "files_json": json.dumps({"txt": str(transc.resolve())}, ensure_ascii=False),
        "speaker_map_json": json.dumps(mapa, ensure_ascii=False) if mapa else None,
        "created_at": registros[idx]["created_at"] if idx is not None else agora,
        "completed_at": agora,
        "edited": 0,
    }

    if idx is not None:
        registros[idx] = registro
        acao = "atualizado"
    else:
        registros.append(registro)
        acao = "inserido"

    banco.parent.mkdir(parents=True, exist_ok=True)
    banco.write_text(json.dumps(registros, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    print(f"\nRegistro {acao} ({registro['id']}). "
          f"{len(registros)} transcrição(ões) no app.")
    print(f"Abra o {PRODUTO} e ela estará na tela inicial.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
