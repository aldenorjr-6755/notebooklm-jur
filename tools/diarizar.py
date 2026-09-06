#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
diarizar.py — diarização acústica de audiências (quem fala, e quando).

É o par de tools/transcrever_audiencia.py. Aquele script transcreve mas não
sabe separar vozes, e por isso emite o rótulo placeholder "Pessoa ?". Este aqui
faz a separação e, se receber a transcrição, devolve o mesmo formato com o
falante real no lugar do placeholder:

    [hh:mm:ss] SPEAKER_00: fala

POR QUE DOIS AMBIENTES
    transcrever_audiencia.py roda no Python 3.14 (faster-whisper, sem torch).
    Este roda no venv 3.12, porque pyannote exige torch e torch exige <3.14:

        ~/.notebooklm/.venv-diar312/Scripts/python.exe tools/diarizar.py ...

CREDENCIAL
    Os pesos do pyannote/speaker-diarization-community-1 são gated. Basta o
    login de usuário já feito (`hf auth login`, token em
    %USERPROFILE%\.cache\huggingface\token) — nada a configurar por venv.

CUSTO (medido nesta máquina: CPU de 12 núcleos, 10 threads, sem CUDA)
    ~1,1x tempo real. 1 h de audiência custa ~64 min de máquina e ocupa quase
    todos os núcleos. É tarefa de janela ociosa, não de uso interativo.

USO
    # só diarizar (gera .diar.json e .diar.rttm)
    python tools/diarizar.py audiencia.mp4

    # diarizar e casar com a transcrição já pronta
    python tools/diarizar.py audiencia.mp4 --transcricao audiencia.mp4.transc.txt

    # sabendo quantas vozes existem, a separação melhora
    python tools/diarizar.py audiencia.mp4 --falantes 3
    python tools/diarizar.py audiencia.mp4 --min-falantes 2 --max-falantes 5

    # já nomeando quem é quem (depois de conferir o resumo da 1ª execução).
    # --reusar aproveita o .diar.json da execução anterior: aplica os nomes em
    # segundos, sem recomputar a diarização (que custa ~1,1x o tempo do áudio).
    python tools/diarizar.py audiencia.mp4 --transcricao t.txt --reusar \
        --rotulos "SPEAKER_00=Juiz,SPEAKER_01=Defesa,SPEAKER_02=Depoente"

NOTAS DE AMBIENTE (armadilhas já pagas)
  - torchaudio 2.11 delega a leitura de áudio ao torchcodec, que exige as DLLs
    do FFmpeg no PATH. A máquina só tem ffmpeg.exe, então torchaudio.load()
    falha. Aqui o áudio é decodificado pelo ffmpeg do sistema para um WAV
    temporário e lido pelo módulo `wave` da stdlib — sem torchaudio.
  - Na API do pyannote 4 o pipeline devolve DiarizeOutput, não Annotation:
    o Annotation está em .speaker_diarization.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

MODELO = "pyannote/speaker-diarization-community-1"
SR = 16000


# ---------------------------------------------------------------- utilidades

def hhmmss(segundos: float) -> str:
    """Mesmo formato de transcrever_audiencia.py, para as saídas casarem."""
    s = int(round(segundos))
    h, resto = divmod(s, 3600)
    m, s = divmod(resto, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def erro(msg: str, codigo: int) -> int:
    print(f"ERRO: {msg}", file=sys.stderr)
    return codigo


# -------------------------------------------------------------------- áudio

def extrair_wav(entrada: Path, destino: Path) -> None:
    """Decodifica qualquer mídia para WAV 16 kHz mono via ffmpeg do sistema.

    Não usamos torchaudio: na 2.11 ele depende do torchcodec, que exige as DLLs
    do FFmpeg (esta máquina só tem o executável).
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg não encontrado no PATH — é ele que decodifica o áudio aqui."
        )
    cmd = [
        "ffmpeg", "-v", "error", "-y", "-i", str(entrada),
        "-vn", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(destino),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg falhou ao decodificar {entrada.name}:\n{proc.stderr.strip()}"
        )


def ler_wav(caminho: Path):
    """WAV 16 kHz mono -> (tensor 1xN float32, duração em segundos)."""
    import numpy as np
    import torch

    with wave.open(str(caminho), "rb") as w:
        if w.getframerate() != SR or w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise RuntimeError("esperado WAV PCM 16 bits, mono, 16 kHz")
        bruto = w.readframes(w.getnframes())
    amostras = np.frombuffer(bruto, dtype=np.int16).astype(np.float32) / 32768.0
    return torch.from_numpy(amostras).unsqueeze(0), len(amostras) / SR


# ---------------------------------------------------------------- diarização

def diarizar(wav, duracao: float, falantes: int | None,
             minimo: int | None, maximo: int | None):
    """Roda o pipeline e devolve os turnos ordenados [(início, fim, rótulo)]."""
    import torch
    from pyannote.audio import Pipeline

    print(f"[2/4] Carregando {MODELO}...", file=sys.stderr)
    pipeline = Pipeline.from_pretrained(MODELO)
    if pipeline is None:
        raise RuntimeError(
            f"não foi possível carregar {MODELO}.\n"
            "Confira: (1) `hf auth whoami` mostra seu usuário; (2) você aceitou\n"
            f"os termos em https://huggingface.co/{MODELO}"
        )
    pipeline.to(torch.device("cpu"))

    kwargs = {}
    if falantes is not None:
        kwargs["num_speakers"] = falantes
    else:
        if minimo is not None:
            kwargs["min_speakers"] = minimo
        if maximo is not None:
            kwargs["max_speakers"] = maximo

    print(f"[3/4] Diarizando {duracao / 60:.1f} min de áudio "
          f"(~{duracao * 1.1 / 60:.0f} min de CPU nesta máquina)...", file=sys.stderr)
    saida = pipeline({"waveform": wav, "sample_rate": SR}, **kwargs)

    # pyannote 4 devolve DiarizeOutput; versões anteriores, Annotation direto.
    anotacao = getattr(saida, "speaker_diarization", saida)
    turnos = [(seg.start, seg.end, rot)
              for seg, _, rot in anotacao.itertracks(yield_label=True)]
    turnos.sort(key=lambda t: t[0])
    return turnos


# ----------------------------------------------------------- casar com texto

def ler_transcricao(caminho: Path):
    """Lê `[hh:mm:ss] Falante: fala` -> [(início_em_segundos, texto)].

    Linhas fora do padrão são preservadas com início None, para não perder
    cabeçalho nem anotação manual que o revisor tenha inserido.
    """
    padrao = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\]\s*[^:]*:\s*(.*)$")
    linhas = []
    for bruta in caminho.read_text(encoding="utf-8").splitlines():
        if not bruta.strip():
            continue
        m = padrao.match(bruta)
        if m:
            h, mi, s, texto = m.groups()
            linhas.append((int(h) * 3600 + int(mi) * 60 + int(s), texto))
        else:
            linhas.append((None, bruta))
    return linhas


def falante_por_sobreposicao(inicio: float, fim: float, turnos) -> str:
    """Rótulo com maior sobreposição no intervalo; se nenhum, o mais próximo.

    A transcrição só traz o início de cada fala, arredondado ao segundo, e uma
    fala pode atravessar a troca de voz — por isso a atribuição vai para quem
    domina o intervalo, não para quem estiver no instante inicial.
    """
    melhor, maior = None, 0.0
    for t_ini, t_fim, rot in turnos:
        sobra = min(fim, t_fim) - max(inicio, t_ini)
        if sobra > maior:
            melhor, maior = rot, sobra
    if melhor:
        return melhor
    if not turnos:
        return "Pessoa ?"
    return min(turnos,
               key=lambda t: min(abs(t[0] - inicio), abs(t[1] - inicio)))[2]


def casar(linhas, turnos, duracao: float, rotulos: dict):
    """Reescreve a transcrição trocando o placeholder pelo falante."""
    inicios = sorted(i for i, _ in linhas if i is not None)
    saida = []
    for inicio, texto in linhas:
        if inicio is None:
            saida.append(texto)
            continue
        posteriores = [i for i in inicios if i > inicio]
        fim = min(posteriores) if posteriores else duracao
        rot = falante_por_sobreposicao(inicio, max(fim, inicio + 0.5), turnos)
        saida.append(f"[{hhmmss(inicio)}] {rotulos.get(rot, rot)}: {texto}")
    return saida


def parse_rotulos(bruto: str | None) -> dict:
    if not bruto:
        return {}
    mapa = {}
    for par in bruto.split(","):
        if "=" not in par:
            raise ValueError(f"--rotulos: esperado SPEAKER_00=Nome, veio {par!r}")
        k, v = par.split("=", 1)
        mapa[k.strip()] = v.strip()
    return mapa


# -------------------------------------------------------------------- saídas

def carregar_turnos(caminho: Path):
    """Relê os turnos de um .diar.json já gerado -> (turnos, duração)."""
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    turnos = [(t["inicio"], t["fim"], t["falante"]) for t in dados["turnos"]]
    turnos.sort(key=lambda t: t[0])
    return turnos, float(dados["duracao_seg"])


def escrever_rttm(turnos, uri: str, caminho: Path) -> None:
    """RTTM — formato padrão de diarização, lido por qualquer ferramenta."""
    linhas = [
        f"SPEAKER {uri} 1 {ini:.3f} {fim - ini:.3f} <NA> <NA> {rot} <NA> <NA>"
        for ini, fim, rot in turnos
    ]
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def resumo(turnos, duracao: float):
    total = {}
    for ini, fim, rot in turnos:
        total[rot] = total.get(rot, 0.0) + (fim - ini)
    fala = sum(total.values())
    linhas = [f"falantes: {len(total)} | turnos: {len(turnos)} | "
              f"fala {fala:.0f}s de {duracao:.0f}s ({fala / duracao * 100:.1f}%)"]
    for rot in sorted(total, key=lambda k: -total[k]):
        primeiro = next(i for i, _, r in turnos if r == rot)
        linhas.append(f"  {rot:12s} {total[rot]:7.1f}s "
                      f"({total[rot] / duracao * 100:4.1f}%) "
                      f"— fala pela 1ª vez em {hhmmss(primeiro)}")
    return linhas


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Diarização de audiência (pyannote community-1, CPU).")
    ap.add_argument("arquivo",
                    help="vídeo ou áudio da audiência (mp4, wav, mp3, m4a, mkv...)")
    ap.add_argument("--transcricao", default=None,
                    help="saída de transcrever_audiencia.py, para casar os falantes")
    ap.add_argument("--saida", default=None,
                    help="txt diarizado (padrão: <transcricao>.diarizado.txt)")
    ap.add_argument("--falantes", type=int, default=None,
                    help="número exato de vozes, se você souber")
    ap.add_argument("--min-falantes", type=int, default=None)
    ap.add_argument("--max-falantes", type=int, default=None)
    ap.add_argument("--rotulos", default=None,
                    help='ex.: "SPEAKER_00=Juiz,SPEAKER_01=Defesa"')
    ap.add_argument("--reusar", action="store_true",
                    help="reaproveita o .diar.json anterior em vez de diarizar "
                         "de novo (para só aplicar --rotulos)")
    args = ap.parse_args()

    entrada = Path(args.arquivo)
    if not entrada.exists():
        return erro(f"arquivo não encontrado: {entrada}", 1)
    if args.transcricao and not Path(args.transcricao).exists():
        return erro(f"transcrição não encontrada: {args.transcricao}", 1)
    if args.falantes is not None and (args.min_falantes or args.max_falantes):
        return erro("--falantes é exclusivo com --min-falantes/--max-falantes", 1)

    try:
        rotulos = parse_rotulos(args.rotulos)
    except ValueError as e:
        return erro(str(e), 1)

    base = str(entrada) + ".diar"
    json_saida, rttm_saida = Path(base + ".json"), Path(base + ".rttm")

    if args.reusar:
        # Só aplicar rótulos não exige torch, pyannote nem ffmpeg — este ramo
        # roda em qualquer Python, inclusive o 3.14 padrão da máquina.
        if not json_saida.exists():
            return erro(f"--reusar precisa de {json_saida.name}, que não existe.\n"
                        "Rode uma vez sem --reusar para gerá-lo.", 6)
        turnos, duracao = carregar_turnos(json_saida)
        print(f"[1/2] Reaproveitando {json_saida.name} — {len(turnos)} turnos, "
              "sem recomputar a diarização.", file=sys.stderr)
    else:
        try:
            import torch  # noqa: F401
            import pyannote.audio  # noqa: F401
        except ImportError:
            return erro(
                "torch/pyannote ausentes. Este script roda no venv 3.12, "
                "não no Python 3.14:\n"
                "  ~/.notebooklm/.venv-diar312/Scripts/python.exe "
                "tools/diarizar.py ...\n"
                "(a exceção é --reusar, que roda em qualquer Python)", 2)

        with tempfile.TemporaryDirectory() as tmp:
            temp_wav = Path(tmp) / "audio.wav"
            print(f"[1/4] Extraindo áudio de '{entrada.name}' (16 kHz mono)...",
                  file=sys.stderr)
            try:
                extrair_wav(entrada, temp_wav)
                wav, duracao = ler_wav(temp_wav)
            except RuntimeError as e:
                return erro(str(e), 3)

            try:
                turnos = diarizar(wav, duracao, args.falantes,
                                  args.min_falantes, args.max_falantes)
            except RuntimeError as e:
                return erro(str(e), 4)

        if not turnos:
            return erro("nenhuma fala detectada — confira se o áudio tem voz "
                        "audível", 5)

        json_saida.write_text(json.dumps(
            {"arquivo": entrada.name, "duracao_seg": round(duracao, 3),
             "modelo": MODELO,
             "turnos": [{"inicio": round(i, 3), "fim": round(f, 3), "falante": r}
                        for i, f, r in turnos]},
            ensure_ascii=False, indent=2), encoding="utf-8")
        escrever_rttm(turnos, entrada.stem, rttm_saida)

    print("\n" + "\n".join(resumo(turnos, duracao)), file=sys.stderr)
    print(f"turnos: {json_saida}\n        {rttm_saida}", file=sys.stderr)

    if args.transcricao:
        linhas = casar(ler_transcricao(Path(args.transcricao)),
                       turnos, duracao, rotulos)
        destino = Path(args.saida) if args.saida else Path(
            str(Path(args.transcricao).with_suffix("")) + ".diarizado.txt")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        print(f"transcrição diarizada: {destino}", file=sys.stderr)
        if not rotulos:
            print("\nOs rótulos são genéricos (SPEAKER_00, SPEAKER_01...). "
                  "Localize no texto\nquem é quem pela 1ª fala de cada um "
                  "(minutos acima) e rode de novo com\n--reusar, que aplica os "
                  "nomes em segundos, sem diarizar outra vez:\n"
                  f'  python tools/diarizar.py "{entrada.name}" '
                  f'--transcricao "{Path(args.transcricao).name}" --reusar \\\n'
                  '      --rotulos "SPEAKER_00=Juiz,SPEAKER_01=Defesa"',
                  file=sys.stderr)
    else:
        print("\n(sem --transcricao: só os turnos foram gerados)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
