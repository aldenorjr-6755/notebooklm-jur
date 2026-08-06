#!/usr/bin/env bash
# subir_rstj.sh — sobe os volumes da RSTJ para um notebook do NotebookLM.
#
#   ./subir_rstj.sh <notebook_id> <ano_inicial> <ano_final>
#
# Uma fonte por volume, titulada "RSTJ v. N (ano)" — o titulo e' o que aparece na
# citacao do NotebookLM, entao ele precisa bastar para localizar o volume.
#
# PARA quando o notebook recusa fonte por lotacao (rpc_code=9): seguir adiante
# gera registro morto, fonte que aparece na lista e nao responde. Ja aconteceu
# neste acervo — ver memoria `notebooklm-capacidade-e-ingestao-de-url`.
set -uo pipefail

NB="${1:?informe o notebook_id}"
DE="${2:?informe o ano inicial}"
ATE="${3:?informe o ano final}"

FONTES="$HOME/.notebooklm/rstj/fontes"
TSV="$HOME/.notebooklm/rstj/rstj_volumes.tsv"
LOG="$HOME/.notebooklm/rstj/_subir_${DE}_${ATE}.log"

ok=0; falha=0; pulado=0
echo "== $(date '+%F %T') · notebook $NB · anos $DE-$ATE ==" | tee -a "$LOG"

# colunas do TSV: 1 arquivo, 2 ano, 3 volume, 4 tomo
while IFS=$'\t' read -r arquivo ano volume tomo _resto; do
    [ "$arquivo" = "arquivo" ] && continue
    [ -z "${ano:-}" ] && continue
    if [ "$ano" -lt "$DE" ] || [ "$ano" -gt "$ATE" ]; then continue; fi

    titulo="RSTJ v. ${volume} (${ano})"
    [ "${tomo:-1}" != "1" ] && titulo="RSTJ v. ${volume} t. ${tomo} (${ano})"

    # $'\t' e obrigatorio: "OK\t..." entre aspas normais e' barra-invertida + t
    # LITERAL para o grep -F, o skip nunca casa e a retomada REENVIA tudo,
    # duplicando fonte no notebook. Foi o que aconteceu em 05/08/2026 na era A.
    if grep -qF "OK"$'\t'"${arquivo}"$'\t' "$LOG" 2>/dev/null; then
        pulado=$((pulado+1)); continue
    fi

    saida=$(nlm source add "$NB" --file "$FONTES/$arquivo" --title "$titulo" --wait --json 2>&1)
    if echo "$saida" | grep -q '"source_id"'; then
        ok=$((ok+1))
        printf 'OK\t%s\t%s\n' "$arquivo" "$titulo" >> "$LOG"
    else
        falha=$((falha+1))
        printf 'FALHA\t%s\t%s\n' "$arquivo" "$(echo "$saida" | tr '\n' ' ' | cut -c1-300)" >> "$LOG"
        if echo "$saida" | grep -qE 'rpc_code=9|full|limit'; then
            echo "PARADO: notebook lotado (rpc_code=9). Crie outro e retome." | tee -a "$LOG"
            break
        fi
    fi
done < "$TSV"

echo "== fim · ok=$ok falha=$falha pulado=$pulado ==" | tee -a "$LOG"
