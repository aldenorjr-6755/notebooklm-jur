# -*- coding: utf-8 -*-
import os, sys
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
from faster_whisper import WhisperModel

AUD = r"C:\Users\alden\.notebooklm\aud_0842458.mp3"
OUT = r"C:\Users\alden\.notebooklm\transcricao_segmentos.txt"

def mmss(s):
    s = int(s)
    return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

print("Carregando modelo...", flush=True)
model = WhisperModel("small", device="cpu", compute_type="int8")
print("Transcrevendo...", flush=True)
segments, info = model.transcribe(AUD, language="pt", vad_filter=True,
                                  beam_size=1, condition_on_previous_text=False)
n = 0
with open(OUT, "w", encoding="utf-8") as f:
    for seg in segments:
        line = f"[{mmss(seg.start)}] {seg.text.strip()}"
        f.write(line + "\n")
        f.flush()
        n += 1
        if n % 50 == 0:
            print(f"...{n} segmentos, t={mmss(seg.start)}", flush=True)
print(f"FIM: {n} segmentos -> {OUT}", flush=True)
