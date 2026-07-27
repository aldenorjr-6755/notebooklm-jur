#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
transcrever_audiencia.py — pipeline local de transcrição de audiências.

Usa faster-whisper (CTranslate2, CPU-friendly, sem torch). O PyAV embutido
lê vídeo/áudio direto (mp4, mkv, wav, mp3, m4a...), então NÃO depende do
ffmpeg do sistema para decodificar.

Uso (no Git Bash / PowerShell, ambiente Windows + Python 3.14):
    python tools/transcrever_audiencia.py <arquivo> [--modelo small] [--idioma pt] [--saida prazos/transc.txt]

Modelos (CPU): tiny | base | small | medium | large-v3
  - "small"  = bom equilíbrio velocidade/qualidade no CPU (padrão)
  - "medium" = melhor qualidade, BEM mais lento no CPU
O modelo é baixado automaticamente do HuggingFace na 1ª execução e fica em cache.

Saída: formato exigido pelo agente transcricao-audiencia:
    [hh:mm:ss] Falante: fala
Como faster-whisper NÃO faz diarização acústica, o rótulo do falante sai como
"Pessoa ?" (placeholder). A separação real de quem fala (Juiz/Defesa/etc.)
deve ser feita por quem revisa, ou por uma etapa de diarização à parte
(pyannote/whisperX — exige torch, que hoje NÃO instala no Python 3.14).
"""
import argparse
import sys
from pathlib import Path


def hhmmss(segundos: float) -> str:
    s = int(round(segundos))
    h, resto = divmod(s, 3600)
    m, s = divmod(resto, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Transcrição de audiência (faster-whisper).")
    ap.add_argument("arquivo", help="vídeo ou áudio da audiência (mp4, wav, mp3, m4a, mkv...)")
    ap.add_argument("--modelo", default="small", help="tiny|base|small|medium|large-v3 (padrão: small)")
    ap.add_argument("--idioma", default="pt", help="código do idioma (padrão: pt)")
    ap.add_argument("--saida", default=None, help="arquivo .txt de saída (padrão: <arquivo>.transc.txt)")
    ap.add_argument("--computacao", default="int8", help="int8|int8_float32|float32 (CPU: int8 é o mais leve)")
    args = ap.parse_args()

    entrada = Path(args.arquivo)
    if not entrada.exists():
        print(f"ERRO: arquivo não encontrado: {entrada}", file=sys.stderr)
        return 1

    saida = Path(args.saida) if args.saida else entrada.with_suffix(entrada.suffix + ".transc.txt")
    saida.parent.mkdir(parents=True, exist_ok=True)

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("ERRO: faster-whisper não está instalado. Rode: python -m pip install faster-whisper",
              file=sys.stderr)
        return 2

    print(f"[1/3] Carregando modelo '{args.modelo}' (CPU, {args.computacao})... "
          f"(baixa do HuggingFace na 1ª vez)", file=sys.stderr)
    model = WhisperModel(args.modelo, device="cpu", compute_type=args.computacao)

    print(f"[2/3] Transcrevendo '{entrada.name}' (idioma={args.idioma})... "
          f"pode demorar bastante no CPU.", file=sys.stderr)
    segments, info = model.transcribe(
        str(entrada),
        language=args.idioma,
        vad_filter=True,          # remove silêncios longos -> timestamps mais limpos
        word_timestamps=False,    # segmento já basta para o formato [hh:mm:ss]
        beam_size=5,
    )

    linhas = []
    for seg in segments:
        texto = seg.text.strip()
        if not texto:
            continue
        # Placeholder de falante: diarização real não é feita aqui.
        linha = f"[{hhmmss(seg.start)}] Pessoa ?: {texto}"
        linhas.append(linha)
        print(linha)  # eco em tempo real (stderr seria melhor, mas stdout ajuda a acompanhar)

    saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"\n[3/3] Concluído. {len(linhas)} segmentos. Saída: {saida}", file=sys.stderr)
    print("AVISO: rótulos de falante são placeholders ('Pessoa ?'). "
          "Faça a diarização/rotulagem (Juiz/Defesa/Promotor/...) na revisão.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
