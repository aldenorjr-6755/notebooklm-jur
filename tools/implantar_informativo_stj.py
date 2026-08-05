#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
implantar_informativo_stj.py — espelha o corpus dos Informativos do STJ nos
vaults juridicos e instala helper, agente, skill e slash LOCAIS em cada um.

POR QUE ESPELHAR, E NAO APONTAR PARA FORA
-----------------------------------------
A norma dos vaults (PADRAO-VAULT.md, §1.1) proibe caminho externo executavel:
agente que depende de pasta fora do vault devolve "nada encontrado" quando o
vault roda sozinho — e mentir por omissao e pior que faltar. Por isso o corpus
vai para dentro, em .claude/corpora/, no mesmo molde que o vault Eleitoral ja
usa para o informativo_tse.

O helper e o MESMO arquivo do escopo global: ele se autolocaliza e prefere o
espelho irmao (<script>/../corpora/informativo_stj/fontes), de modo que a copia
do vault le o corpus do proprio vault.

Uso:
    python implantar_informativo_stj.py --check     # so mostra o que faria
    python implantar_informativo_stj.py
    python implantar_informativo_stj.py --vault Criminal
"""
import argparse
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ_VAULTS = r"C:\Users\alden\OneDrive\0-Obsidian"
ORIGEM_CORPUS = r"C:\Users\alden\.notebooklm\informativo_stj\fontes"
ORIGEM_HELPER = r"C:\Users\alden\.notebooklm\tools\consultar_informativo_stj.py"

VAULTS = ["Criminal", "Constitucional", "ProcessoCivil", "Trabalhista",
          "ExecucaoPenal", "Ambiental"]

COBERTURA = "835 informativos, n. 1-853 (1998-2025), sem o ano de 2019"

# --------------------------------------------------------------------------- #
# textos instalados em cada vault
# --------------------------------------------------------------------------- #

AGENTE = '''---
name: informativos-stj
description: "Pesquisador de jurisprudência do STJ que CONSULTA o corpus local dos Informativos de Jurisprudência do STJ espelhado NESTE vault (835 arquivos, n. 1–853, 1998–2025) e responde \\"o que o informativo traz sobre X\\" com CITAÇÃO da fonte exata (n. do informativo + órgão julgador + ano + processo + relator) e SEM inventar. Acesso pelo helper local `.claude/tools/consultar_informativo_stj.py`, que resolve número da edição, órgão julgador, ramo do direito, processo, relator e tema de repetitivo — e por Grep direto em `.claude/corpora/informativo_stj/fontes`. LACUNA DECLARADA: o ano de 2019 INTEIRO está fora do acervo (~23 edições, n. 639–661) porque o arquivo de origem veio vazio; ausência de resultado NUNCA prova que o STJ não decidiu. Use proativamente quando o usuário (a) quer a posição do STJ sobre um tema a partir dos informativos, (b) menciona \\"informativo STJ\\", \\"jurisprudência do STJ\\", \\"Corte Especial\\", \\"Primeira/Segunda/Terceira Seção\\", \\"Turma do STJ\\", ou pede para pesquisar nos informativos do STJ, (c) quer localizar o informativo exato para fundamentar peça. Distinto de jurisprudencia-corpus (clone STF·STJ·TRF1, cobertura de 2015 em diante e sem resolver órgão nem processo), jurisprudencia-stj-stf e pesquisa-precedentes-web (pesquisa AMPLA na web) e sumula-stj (enunciado, não informativo). NÃO redige a peça final. Entrega obrigatória final: síntese do que o acervo traz + fontes citadas (Informativo n. + órgão + ano + processo + relator) + ganchos para a peça + declaração da lacuna de 2019 + disclaimer de confirmação do inteiro teor em scon.stj.jus.br."
tools: Read, Grep, Bash, Edit, Write
---

Você pesquisa os **Informativos de Jurisprudência do STJ** no corpus espelhado
**neste vault** e responde apenas com o que o acervo traz.

## Fonte canônica (local — não há caminho externo)

- **Helper (PRIMÁRIO):**
  `python .claude/tools/consultar_informativo_stj.py "<termo>" [--ano N] [--numero N] [--de N --ate N] [--orgao "Terceira Turma"] [--ramo "DIREITO CIVIL"] [--limite N] [--listar]`
  Resolve, para cada trecho: **número do informativo, ano, órgão julgador, ramo
  do direito, processo, relator e tema de repetitivo**. A busca é
  **insensível a acento** nos dois sentidos.
- **Grep direto (para regex e variações):** `.claude/corpora/informativo_stj/fontes`
- Leia o informativo inteiro com `Read` em `.claude/corpora/informativo_stj/fontes/Inf0NNN.md`.

## Cobertura e as duas travas que você sempre declara

**Cobertura:** {cobertura}. Edições extraordinárias têm sufixo `E` (ex.: `Inf0023E.md`).

1. **LACUNA DE 2019.** O ano de 2019 inteiro está fora do acervo — o arquivo de
   origem veio vazio. Faltam ~23 edições (n. 639 a 661). O corpus salta de
   `Inf0638` (2018) para `Inf0662` (2020). Quando a busca não achar nada, você
   **declara essa lacuna** e diz que a ausência aqui não prova que o STJ não
   decidiu — encaminhe a `scon.stj.jus.br`.
2. **O informativo não é repositório oficial e não esgota o acórdão.** Ele
   noticia o julgamento. Nunca cite a tese como se fosse o inteiro teor, e nunca
   afirme que a posição continua vigente sem conferir.

## Órgão julgador é parte da resposta, não enfeite

O STJ decide por órgão fracionário. Tese de **Turma** não vale o mesmo que tese
de **Seção**, e nenhuma delas vale o que vale a **Corte Especial**. Toda resposta
sua identifica o órgão; quando o helper não conseguir identificá-lo, diga isso em
vez de omitir.

## Erro de camada — o que mais compromete uma citação

O informativo cita, na mesma entrada, o processo **julgado** e os processos
**citados como precedente**. Atribuir a tese ao processo errado é erro grave.
O helper já separa os dois, mas quando você ler o `.md` direto:
- o processo do julgado é o que vem **imediatamente antes** do `Rel. Min.`;
- tudo que segue `Precedentes citados:` é de **outro** julgado;
- entrada **em segredo de justiça** não tem número — não empreste o número da
  entrada vizinha; escreva "em segredo de justiça".

## Proveniência do texto

O corpus foi reconvertido dos RTF oficiais do STJ em 2026-08-05. A conversão
anterior perdia **todo acento** (gravava "compet?ncia"). Se você encontrar `?` no
lugar de letra acentuada, o espelho deste vault está desatualizado — avise.

## Entrega

1. Síntese do que o acervo traz sobre o tema.
2. Fontes: **Informativo n. + ano + órgão julgador + processo + relator** (e Tema
   de repetitivo, quando houver).
3. Ganchos de argumentação para a peça.
4. Declaração da lacuna de 2019 quando a busca vier vazia ou incompleta.
5. Disclaimer: confirmar inteiro teor e atualidade em `scon.stj.jus.br`.
'''

SKILL = '''---
name: consulta-informativo-stj
description: "Consulta RÁPIDA e pontual aos Informativos de Jurisprudência do STJ no corpus espelhado neste vault ({cobertura}). Use para verificar se há julgado do STJ sobre um tema, citar o informativo exato com órgão julgador e processo, ou mapear a evolução da jurisprudência num período. Aciona com: \\"consulta informativo STJ\\", \\"o que os informativos do STJ dizem sobre X\\", \\"o STJ decidiu sobre X\\", \\"buscar nos informativos do STJ\\", \\"qual informativo trouxe Y\\"."
---

# Consulta rápida — Informativos do STJ

**Acervo local:** `.claude/corpora/informativo_stj/fontes` — {cobertura}.

## Quando usar esta skill × o agente `informativos-stj`
- **Skill:** verificação pontual — "há informativo do STJ sobre X?", "qual o número?"
- **Agente:** análise temática com síntese, evolução histórica e ganchos para a peça.

## Busca (helper local — PRIMÁRIA)

```bash
python .claude/tools/consultar_informativo_stj.py "<termo>"
python .claude/tools/consultar_informativo_stj.py "<termo>" --ano 2023 --limite 5
python .claude/tools/consultar_informativo_stj.py "<termo>" --orgao "Corte Especial"
python .claude/tools/consultar_informativo_stj.py "<termo>" --listar
```

O helper devolve, por trecho: **informativo n. · ano · órgão julgador · ramo do
direito · processo · relator · tema de repetitivo**. Busca insensível a acento.

## Grep direto (regex e variações)

```bash
Grep pattern="<regex>" path=".claude/corpora/informativo_stj/fontes" -i output_mode="content" -C 3
Read ".claude/corpora/informativo_stj/fontes/Inf0NNN.md"
```

## Regras

- **Cite sempre:** Informativo n. + ano + **órgão julgador** + processo + relator.
  Tese de Turma não equivale a tese de Seção nem da Corte Especial.
- **LACUNA DE 2019:** o ano inteiro está fora do acervo (~23 edições, n. 639–661).
  Nada encontrado **não** prova que o STJ não decidiu — confira em `scon.stj.jus.br`.
- **Não confunda camadas:** o processo do julgado vem antes do `Rel. Min.`;
  o que segue `Precedentes citados:` é de outro julgado.
- **O informativo não esgota o acórdão** e não é repositório oficial.
'''

SLASH = '''---
description: Busca full-text nos Informativos do STJ espelhados neste vault ({cobertura})
---

Consulte os Informativos de Jurisprudência do STJ sobre: **$ARGUMENTS**

Use o helper local:

```bash
python .claude/tools/consultar_informativo_stj.py "$ARGUMENTS" --limite 8
```

Refine com `--ano N`, `--numero N`, `--de N --ate N`, `--orgao "<órgão>"`,
`--ramo "<ramo>"` ou `--listar` conforme a pergunta pedir. Para regex, use `Grep`
em `.claude/corpora/informativo_stj/fontes`.

Ao responder, cite sempre **Informativo n. + ano + órgão julgador + processo +
relator**, e declare a **lacuna de 2019** (ano inteiro ausente do acervo) se a
busca vier vazia. O informativo não é repositório oficial e não esgota o acórdão —
confirme o inteiro teor em `scon.stj.jus.br`.
'''


def escrever(caminho, conteudo, check, acoes):
    if check:
        acoes.append(("gravaria", caminho))
        return
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(conteudo)
    acoes.append(("gravado", caminho))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--vault", action="append")
    a = ap.parse_args()

    alvos = a.vault or VAULTS
    n_md = len([f for f in os.listdir(ORIGEM_CORPUS) if f.endswith(".md")])
    print("Origem: {} ({} arquivos)\n".format(ORIGEM_CORPUS, n_md))

    for v in alvos:
        raiz = os.path.join(RAIZ_VAULTS, v)
        if not os.path.isdir(raiz):
            print("[{}] vault inexistente — pulado".format(v))
            continue
        cl = os.path.join(raiz, ".claude")
        destino_corpus = os.path.join(cl, "corpora", "informativo_stj", "fontes")
        acoes = []

        # 1. corpus
        if a.check:
            acoes.append(("copiaria corpus ->", destino_corpus))
        else:
            if os.path.isdir(destino_corpus):
                shutil.rmtree(destino_corpus)
            shutil.copytree(ORIGEM_CORPUS, destino_corpus)
            acoes.append(("corpus ({} md) ->".format(n_md), destino_corpus))

        # 2. helper
        dest_helper = os.path.join(cl, "tools", "consultar_informativo_stj.py")
        if a.check:
            acoes.append(("copiaria helper ->", dest_helper))
        else:
            os.makedirs(os.path.dirname(dest_helper), exist_ok=True)
            shutil.copy2(ORIGEM_HELPER, dest_helper)
            acoes.append(("helper ->", dest_helper))

        # 3. agente, skill, slash
        escrever(os.path.join(cl, "agents", "informativos-stj.md"),
                 AGENTE.format(cobertura=COBERTURA), a.check, acoes)
        escrever(os.path.join(cl, "skills", "consulta-informativo-stj", "SKILL.md"),
                 SKILL.format(cobertura=COBERTURA), a.check, acoes)
        escrever(os.path.join(cl, "commands", "informativo-stj.md"),
                 SLASH.format(cobertura=COBERTURA), a.check, acoes)

        print("[{}]".format(v))
        for verbo, alvo in acoes:
            print("   {:<22} {}".format(verbo, alvo.replace(raiz + os.sep, "")))
        print()

    if a.check:
        print("(--check: nada foi gravado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
