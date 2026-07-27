# TRIAGEM DAS COLISÕES DE AGENTE ENTRE VAULTS CLASSE A

> **Grupos A e C EXECUTADOS em 2026-07-26** — ver as duas últimas seções.

> Snapshot datado — **2026-07-26**. Envelhece. A norma é `PADRAO-VAULT.md` (§1.2, escopo global).
> Companheiro de `PADRAO-VAULT-DIAGNOSTICO.md`.

## Situação medida

Os quatro vaults Classe A (Ambiental, Constitucional, Criminal, Eleitoral) somam **157 agentes
locais** em **111 nomes distintos**: 34 nomes aparecem em mais de um vault. Comparação byte a byte
desses 34: **31 divergem, 3 são idênticos**.

A divergência quase nunca é drift — as cópias têm a **mesma contagem de linhas e bytes diferentes**,
porque a customização foi feita *dentro* da linha. Treze arquivos do Eleitoral trazem o marcador
literal `ANCORAGEM`.

Critério da triagem: a divergência é **conteúdo de domínio** (→ fica local) ou **convenção de
caminho/pasta** (→ colapsa em cópia única global)?

---

## Grupo A — TRANSVERSAL: colapsar em cópia única global (12)

Divergência nula ou puramente de convenção de saída/caminho. Nenhum conteúdo de domínio.

| # | Agente | Vaults | Natureza da divergência |
|---|---|---|---|
| 1 | `analise-juridica-firac` | Const, Crim | **idênticos** |
| 2 | `recurso-extraordinario-criminal` | Const, Crim | **idênticos** |
| 3 | `tese-repetitiva` | Amb, Const, Crim | **idênticos** |
| 4 | `alegacoes-finais-criminal` | Amb, Crim | só pasta de saída: `20-Casos/<CODIGO>/` × `prazos/` |
| 5 | `apelacao-criminal` | Amb, Crim | idem |
| 6 | `auditoria-nulidades-criminal` | Amb, Crim | idem |
| 7 | `defesa-criminal-resposta-acusacao` | Amb, Crim | idem |
| 8 | `quesitos-periciais` | Amb, Crim | idem |
| 9 | `revisao-portugues-juridico` | Amb, Const, Crim | idem (Const ≡ Crim) |
| 10 | `peca-legal-design` | Amb, Const, Crim | pasta + **caminho legado morto** (ver defeito D2) |
| 11 | `corte-idh-brasil` | Const, Crim | caminho do corpus — **Criminal aponta para PDF** (ver D3) |
| 12 | `senso-incomum` | Const, Crim | caminho do corpus — **Criminal usa `~/.notebooklm/`** (ver D1) |

**Ação:** eleger uma versão canônica, resolver antes a convenção de pasta de saída na norma, mover
para `~/.claude/agents/` e apagar as cópias locais. Nos itens 10–12 a versão do **Constitucional** é
a correta (usa `.claude/corpora/` relativo e o `.md` paginado); a do Criminal carrega defeito.

---

## Grupo B — ANCORADO: mantém cópia local, sem versão comum aproveitável (16)

O texto local contém bloco de domínio que não sobrevive ao merge.

### B.1 — Marcador literal `ANCORAGEM` (13, todos Criminal ↔ Eleitoral)

`analise-narrativista` · `analise-probatoria-abdutiva` · `analise-probatoria-bayesiana` ·
`analise-probatoria-causal` · `analise-probatoria-foundherentista` · `analise-probatoria-standards` ·
`analise-probatoria-wigmore` · `analise-prova-oral` · `confronto-depoimento-laudo` ·
`corroboracao-falsificacionista` · `cotejo-depoimentos` · `dialetica-atomista-holista` ·
`interrogatorio-cruzado`

Exemplo (`analise-prova-oral`, cópia do Eleitoral):

> **ANCORAGEM ELEITORAL (vault Eleitoral):** em AIJE e em representação por captação ilícita a prova
> é majoritariamente oral e vem de pessoas com interesse direto no pleito (cabos eleitorais,
> adversários, servidores…)

### B.2 — Ancorados sem o marcador (3)

| Agente | Vaults | Bloco de domínio |
|---|---|---|
| `habeas-corpus` | Crim, Elei | Eleitoral: HC EM MATÉRIA ELEITORAL — competência da J. Eleitoral (CE 355+; STF, Pet 8.335), TRE contra ato de juiz eleitoral (CE 29, I, "e"), TSE contra ato de TRE (CE 22, I, "e"), trancamento de ação penal eleitoral |
| `direitos-fundamentais` | Amb, Const | **corpora diferentes**: Ambiental espelha subconjunto ambiental/climático de 64 artigos; Constitucional espelha os 201 |
| `verificador-citacoes` | Amb, Const | ancorado na infra de cada vault: o Ambiental declara não acompanhar o corpus STF·STJ·TRF1 e roteia para `/tese-rg`, `/sc-ambiental` |

**Ação:** nenhuma. São forks legítimos — é exatamente o que a Classe A compra.

---

## Grupo C — HÍBRIDO: 1 cópia global + 1 fork ancorado no Eleitoral (6)

Padrão recorrente: Ambiental ≡ Constitucional ≡ Criminal (≈ versão global) e **só o Eleitoral
diverge**, com bloco próprio.

| Agente | Ancoragem eleitoral |
|---|---|
| `doutrina` | rol próprio de eleitoralistas — José Jairo Gomes, Zilio, Ramayana, Adriano Soares da Costa, Edson de Resende Castro, Thales Tácito, Coneglian |
| `jurisprudencia-stj-stf` | complemento dos superiores comuns à jurisprudência do próprio TSE (que é do `informativo-tse`); inelegibilidade sob ótica constitucional |
| `pesquisa-precedentes-web` | alvo primário `site:tse.jus.br` + TRE da circunscrição; via para o que o corpus local não alcança |
| `lei-e-sumula` | datasets locais: CE, Lei das Eleições, Lei dos Partidos, LC 64/90 via `consultar_codigo.py --fonte`; súmulas TSE; RITSE |
| `mandado-seguranca` | alvo típico é o ato da J. Eleitoral em função ADMINISTRATIVA (registro de partido, cartório eleitoral, negativa de certidão, presidente de mesa) |
| `parecer-juridico` | parecer PRÉ-ELEITORAL preventivo: viabilidade de candidatura, inelegibilidade antes do registro (LC 64/90 art. 1º), desincompatibilização |

**Ação:** colapsar as três cópias coincidentes numa global; manter só a do Eleitoral local. Decidir
se o fork mantém o mesmo nome (override local, permitido na Classe A) ou ganha sufixo.

---

## Defeitos colaterais encontrados na triagem

| # | Defeito | Onde |
|---|---|---|
| D1 | **Violação de Classe A** — caminho externo executável (`~/.notebooklm/`, `~/.claude/`) em vault Classe A, vedado pela §1.1 | `Criminal/.claude/agents/`: `informativos-stj.md`, `pesquisa-precedentes-web.md`, `senso-incomum.md` · `Ambiental/.claude/agents/dosimetria-pena.md` |
| D2 | **Caminho legado morto** — aponta para `40-Recursos/Modelos/Especificações tipográficas padrão (.docx).md` e nomeia o "Segundo Cérebro" (vault em desativação); a pasta `40-Recursos/Modelos` **não existe** no Criminal | `Criminal/.claude/agents/peca-legal-design.md` |
| D3 | **Contraria a regra canônica de conversão** — manda ler o PDF em `Anexos/CADH_STF_anotada_2ed.pdf` em vez do `.md` paginado que o Constitucional já usa | `Criminal/.claude/agents/corte-idh-brasil.md` |

---

## Resumo

| Grupo | Nomes | Destino |
|---|---|---|
| A — transversal | 12 | cópia única em `~/.claude/agents/` |
| B — ancorado | 16 | permanece local (fork legítimo) |
| C — híbrido | 6 | 1 global + 1 fork no Eleitoral |
| **Total** | **34** | |

Redução: de **157 arquivos de agente** para ~**129** (−12 do grupo A, −16 do grupo C), sem perda de
conteúdo ancorado.

**Pré-requisito de execução:** unificar na norma a convenção de pasta de saída
(`20-Casos/<CODIGO>/` × `prazos/`) — ela sozinha responde por 7 das 31 divergências.


---

## EXECUÇÃO DO GRUPO A — 2026-07-26

**Convenção de saída unificada em `prazos/`**, fixada na §2.7 da norma. `20-Casos/` ficou reservada
ao conteúdo curado sem dado sensível (§2.2); minuta gerada carrega dado do caso e não cabe lá.
Corrigidos os 11 arquivos do Ambiental que usavam `20-Casos/<CODIGO>/` como destino de saída (4 deles
traziam ainda o erro de concordância "salve em a pasta do caso", de um `sed` anterior). O slash
`caso-ambiental`, que **cria** a pasta do caso, foi deixado intacto — ali o caminho é destino
legítimo, não convenção de saída.

**Achado que inverteu a hipótese de trabalho.** A divergência local × global **não era drift**: as
cópias de vault tinham os caminhos reescritos de `~/.notebooklm/...` para `.claude/...` na promoção a
Classe A. O conteúdo era o mesmo — e, onde não era, **o global estava à frente**. Caso mais grave,
`defesa-criminal-resposta-acusacao`: o global carrega o aviso

> ⚠️ **NÃO CITE "Tema 1.099 STF" para insignificância.** Conferido em 2026-07-26 no banco oficial de
> Temas de Repercussão Geral: o Tema 1.099 (ARE 1255885) é de **ICMS**.

e a cópia do vault Criminal ainda citava o Tema 1.099 falso em **quatro** pontos. A correção nunca
atravessou o fork. É a materialização exata do risco previsto na análise da classe A.

**Executado:**

1. Duas correções no global, antes de apagar qualquer coisa:
   - `corte-idh-brasil` → do PDF `Anexos/CADH_STF_anotada_2ed.pdf` para `~/.notebooklm/biblioteca/md/CADH_STF_anotada_2ed.md` (regra canônica: ler o `.md` paginado);
   - `peca-legal-design` → "gerado no Segundo Cérebro" (vault em desativação) → "gerado neste ambiente".
2. **27 cópias locais removidas** — Ambiental 8, Constitucional 7, Criminal 12, Eleitoral 0.
   Total de agentes locais nos quatro Classe A: **157 → 130**.
3. Declaração por nome (§2.7) em `REQUISITOS-EXTERNOS.md`: Ambiental §5, Constitucional §6, Criminal §8.
4. Contagens sincronizadas em `CLAUDE.md`, `REQUISITOS-EXTERNOS.md` e nos canários de `/health-check`
   (Ambiental 24→16, Constitucional 24→17, Criminal 86→74). Corrigidas de passagem duas defasagens
   pré-existentes: Ambiental dizia 6 skills (são 7), Criminal dizia 131 (são 132).
5. Nota de escopo no catálogo de agentes dos três `CLAUDE.md` — os 12 continuam citados e invocáveis,
   agora em exemplar único.
6. Commit em cada vault e em `~/.claude`. Backup dos 39 arquivos (27 locais + 12 globais) no
   scratchpad da sessão.

**Verificado após a execução:** 0 cópias locais remanescentes do grupo A · 12/12 presentes no global ·
0 ocorrências da convenção antiga · contagem declarada = contagem real nos quatro vaults.

### Pendente — não executado

- **Grupo C** (6 nomes): colapsar as três cópias coincidentes e manter só o fork do Eleitoral.
- **D1 — violações de Classe A** ainda de pé: `Ambiental/.claude/agents/dosimetria-pena.md` e, no
  Criminal, `informativos-stj.md` e `pesquisa-precedentes-web.md` (`senso-incomum.md` saiu com o
  grupo A). São caminhos `~/`-based em vault Classe A, vedados pela §1.1.
- **Grupo B** (16 nomes): nada a fazer — forks legítimos.


---

## EXECUÇÃO DO GRUPO C — 2026-07-26

Padrão confirmado por diff, depois de normalizar os caminhos que a promoção a Classe A reescreveu:
nos seis nomes, **Ambiental, Constitucional e Criminal eram coincidentes com o global** (0 linhas de
diferença), e **só o Eleitoral divergia** — 2 a 6 linhas, sempre o bloco de ancoragem eleitoral.

Três exceções, todas defeito da cópia de vault, nenhuma perda ao adotar o global:

- `jurisprudencia-stj-stf` (Ambiental) e `pesquisa-precedentes-web` (Ambiental) traziam a **marca
  inline `[externo — …]` que a §2.7 declara abandonada** — e traziam-na exatamente no defeito que a
  norma descreve: **dentro da linha de comando**, duplicada, quebrando o copiar-colar do helper.
- `pesquisa-precedentes-web` (Constitucional) gravava em **`00-Inbox/`** — uma *terceira* convenção
  de saída, além de `prazos/` e `20-Casos/<CODIGO>/`.

**Executado:** 15 cópias removidas (Ambiental 6, Constitucional 6, Criminal 3); os 6 forks do
Eleitoral preservados e **declarados** na nova §H do seu `REQUISITOS-EXTERNOS.md`, com a advertência
de não "corrigir" a duplicação — ela é o motivo de aquele vault ser Classe A. Conferido que os seis
usam só caminho relativo, sem violar a §1.1. Declarações de grupo C acrescidas às seções já criadas
no grupo A; contagens de `CLAUDE.md`, `REQUISITOS-EXTERNOS.md` e canários de `/health-check`
sincronizadas. Commit nos quatro vaults.

**Decisão sobre o nome do fork:** mantido igual ao global. Agente de projeto vence o global de mesmo
nome, é o comportamento documentado, e sufixar quebraria todas as referências no `CLAUDE.md` e nos
slash commands do Eleitoral.

### Estado final

| | Antes | Grupo A | Grupo C | Agora |
|---|---|---|---|---|
| Ambiental | 24 | 16 | 10 | **10** |
| Constitucional | 24 | 17 | 11 | **11** |
| Criminal | 86 | 74 | 71 | **71** |
| Eleitoral | 23 | 23 | 23 | **23** |
| **Total** | **157** | 130 | 115 | **115** |

**Colisões remanescentes: 16** — exatamente o grupo B, forks ancorados legítimos. Efeito colateral:
zeraram-se as últimas 2 ocorrências da marca inline abandonada nos quatro vaults.

### Pendente

**D1 — violações de Classe A**, três de pé: `Ambiental/.claude/agents/dosimetria-pena.md` e, no
Criminal, `informativos-stj.md` e `pesquisa-precedentes-web.md` — este último saiu com o grupo C,
restando **dois**. São caminhos `~/`-based em vault Classe A, vedados pela §1.1.


---

## VIOLAÇÕES DE CLASSE A (D1) — 2026-07-26

**Resolvidas as duas apontadas:**

- `Ambiental/.claude/agents/dosimetria-pena.md` — executava `Grep` em
  `~/.notebooklm/informativo_stj/fontes/` (corpus que o próprio vault declara não replicar) e ainda
  trazia a marca inline `**[corpus externo opcional — …]**`, aposentada pela §2.7. Passou a apontar
  para o substituto já declarado na §3 (`/sumula-stj`, `/teses-stj`, `jurisprudencia-stj-stf`),
  copiando o padrão que `verificador-citacoes` já usava: nomeia o corpus em prosa, sem caminho.
  A coluna "quem o citaria" da §3 foi corrigida.
- `Criminal/.claude/agents/informativos-stj.md` **e** a skill `consulta-informativo-stj` — ambos
  construídos inteiramente sobre o mesmo corpus não replicado (pasta, `Grep` e `Read`). Eram caminho
  externo executável **e** recurso inoperante dentro do vault. Removidos; exemplar único é o global,
  que vive onde o corpus vive. Criminal: 71 → **70 agentes**, 132 → **131 skills**.

De passagem, corrigida no global uma barra invertida solta em `informativos-stj`
(`…/fontes\`` → `…/fontes``), que quebrava o copiar-colar do caminho.

### Duas correções ao que este documento afirmava antes

1. **A contagem "2 violações" veio de um grep só em `agents/`.** Ampliada a varredura para todo o
   `.claude/`, aparecem outras — ver abaixo. O número certo nunca foi 2 para o vault inteiro.
2. **"Zeraram-se as marcas inline abandonadas" estava errado.** O grep usava o padrão `\[externo` e
   não pegava a variante `[corpus externo opcional]`, que sobrevivia em `dosimetria-pena` — o mesmo
   falso resultado por variante de forma que a §2.7 dá como motivo para ter aposentado a prática.
   Agora, com padrão amplo (`\*\*\[[^]]*externo[^]]*\]\*\*`), são **0** nos quatro vaults.

### Ainda de pé — camada de helpers, não auditada antes

Não são exceção tolerada: `.py` é camada executável. (Diferente de `PROVENIENCIA.md` e da citação de
`PADRAO-VAULT.md` em `verificar-fila`, que a §1.1 e a §2.7 isentam expressamente.)

| Arquivo | Ocorrência | Natureza |
|---|---|---|
| `Criminal/.claude/tools/consultar_senso_incomum.py` | `DIR = r"~/.notebooklm/senso_incomum/fontes"` | **fonte de dados** — o corpus não é replicado aqui; helper órfão desde que o agente `senso-incomum` saiu no grupo A |
| `Criminal/.claude/tools/consultar_cadh_stf.py` | `PDF=`, `MD=` | fallback de inteiro teor; o índice JSON é local |
| `Criminal/.claude/tools/consultar_constituicao_supremo.py` | `PDF =` | idem; e com separador misto (`biblioteca\pdf\…`) |
| `Criminal/.claude/tools/consultar_sumula_stj.py` | só docstring | **proveniência — tolerada pela §1.1**, não é defeito |

Os três primeiros pedem decisão, não conserto mecânico: espelhar o recurso, apontar para substituto
local, ou retirar o helper.


---

## HELPERS COM CAMINHO EXTERNO — 2026-07-26

Os três resolvidos, todos em `Criminal/.claude/tools/`:

| Helper | Decisão | Motivo |
|---|---|---|
| `consultar_senso_incomum.py` | **removido** | lia corpus não replicado; órfão desde que `senso-incomum` saiu no grupo A — zero referências no vault inteiro |
| `consultar_cadh_stf.py` | **removido** | idem; o consumidor era `corte-idh-brasil`, também saído no grupo A |
| `consultar_constituicao_supremo.py` | **corrigido** | `/constituicao` o usa e os 8 volumes estão espelhados aqui |
| `consultar_sumula_stj.py` | intocado | menção externa só na docstring — proveniência, tolerada pela §1.1 |

Helpers do Criminal: 28 → **26**.

**O defeito do `consultar_constituicao_supremo.py` era mais fundo que o `PDF =` externo que o grep
apontou.** A constante `FONTES` — a que alimenta o `--texto` — era:

```python
FONTES = os.path.join(os.path.expanduser("~"), ".notebooklm", "constituicao_supremo", "fontes")
```

Isto é: o `--texto` lia de fora do vault e o espelho local de 8 volumes era **peso morto**. Passou à
forma que Constitucional e Eleitoral já usavam (`os.path.dirname(TOOLS)/corpora/...`) e foi testado
nos dois modos. Os índices JSON ficaram: `cadh_artigos.json` ainda serve a `consultar_cadh.py`
(`/cadh`, `/pidcp`); `cadh_stf_indice.json` ficou sem leitor local.

### Terceira lição de método no mesmo dia

O grep literal por `~/.notebooklm` **não pega caminho construído**:
`os.path.join(os.path.expanduser("~"), ".notebooklm", …)` não contém a string procurada. O defeito
mais grave dos três só apareceu ao **ler** o arquivo. A varredura de conformidade precisa das duas
formas — literal e construída (`expanduser`, `os.environ["HOME"|"USERPROFILE"]`).

### Surgiu dessa varredura — RESOLVIDO em seguida

`*/.claude/skills/verificar-fila/scripts/fila_verificar.py` — idêntico nos quatro vaults — tem, na
linha 164, `base = os.path.expanduser("~/OneDrive/0-Obsidian")`: fallback que fixa em código **onde a
coleção de vaults mora**. Não é `~/.notebooklm` nem `~/.claude`, mas é caminho externo em linha
executável, e quebra na hipótese que a §2.7 descreve — os vaults já migraram uma vez de
`C:\Users\alden\<Nome>` para o OneDrive. Cabe decidir se entra na exceção do `/health-check`
(script que precisa citar o que caça) ou se deve resolver o vault por argumento e cwd.


---

## `fila_verificar.py` — RESOLVIDO em 2026-07-26

O fallback `base = os.path.expanduser("~/OneDrive/0-Obsidian")` saiu. `achar_vault()` resolve em
duas etapas, sem raiz de coleção em código:

1. **caminho** — absoluto, ou relativo ao diretório atual (`.` para o vault corrente);
2. **nome simples** — procurado subindo do cwd até achar `<ancestral>/<nome>` que tenha `CLAUDE.md`
   ou `.claude/`. De dentro de um vault, o nome de um irmão resolve, onde quer que a coleção esteja
   montada. Argumento com separador de caminho não vira adivinhação: falha direto.

De fora da coleção, nome simples agora **falha** — com mensagem que explica o que fazer. É a
contrapartida deliberada de não fixar a raiz.

Testado nos seis cenários (`.`, irmão, próprio nome, caminho absoluto de fora, nome de fora,
caminho inexistente) e nas cinco cópias — os quatro vaults Classe A e a global, esta rodando sobre
um vault Classe B. `SKILL.md` dos vaults documenta a nova resolução.

### Dois tropeços do próprio conserto, registrados porque se repetem

- **`\U` em docstring.** A explicação citava `C:\Users\...`; em string não-raw, `\U` abre escape
  unicode e o arquivo virou `SyntaxError`. Some do teste de importação e só aparece ao executar.
  A frase foi reescrita sem caminho literal.
- **CRLF silencioso.** `io.open(p, "w")` no Windows converteu o arquivo inteiro para CRLF: o `git
  diff` acusou 506 linhas onde havia 48 de mudança real. Normalizado de volta para LF nas cinco
  cópias — o que, de quebra, zerou uma deriva de fim de linha que já existia em Ambiental e
  Eleitoral e aparecia como modificação pendente sem conteúdo.
- **Cópia por cima sem conferir.** O `SKILL.md` global **não** era igual ao dos vaults (tem seção
  `## Uso` com a sintaxe de slash própria) e foi sobrescrito ao propagar; restaurado do git. Os
  quatro dos vaults, esses sim, eram idênticos. Conferir antes de propagar, não depois.


---

## `/health-check` NOS QUATRO — 2026-07-26

Todos os canários de infraestrutura fecham; as contagens mexidas na triagem batem exatas. O que a
rodada produziu de útil foram **dois falsos positivos da própria auditoria** — os dois corrigidos.

### 1. `lint_vault.py` — a métrica de nota órfã estava quebrada

`build_name_index()` devolvia o relpath com o separador nativo do SO
(`10-Wiki\Legislacao\x.md`), enquanto `outbound_count` normaliza para `/`. No Windows as duas chaves
**nunca casavam**: `inbound_count.get(rel, 0)` dava sempre 0, e a regra `out_n == 0 and in_n == 0`
degenerava em `out_n == 0`. Ou seja: **toda nota sem link de saída era acusada de órfã**,
independentemente de quantas apontassem para ela.

As seis "órfãs" reportadas tinham de **2 a 13 links de entrada** cada — as notas "fonte canônica" do
Eleitoral são stubs de referência, muito linkadas e que não linkam ninguém. E o "0 órfãs" do
Ambiental e do Criminal era acidental: passaram porque suas notas têm links de saída.

Corrigido nas cinco cópias. Depois da correção: **0 órfãs e 0 links quebrados nos quatro vaults.**

### 2. Infra de pasta contada como nota

`LEIA-ME.md` da Inbox do Constitucional aparecia como órfã. O script já tinha a lista de infra
(`CLAUDE.md`, `REQUISITOS-EXTERNOS.md`, `LEIA-ME.md`, `README.md`, `index.md`, `MOC*`) e a aplicava
em duas outras verificações — **menos** na de órfã. Alinhado.

### 3. Parte 2 do `/health-check` — isenção agora é do grep, não do olho

`PADRAO-VAULT*` e `FONTES-CANONICAS`, que a §2.7 isenta, vinham na lista de "citados" e cabia ao
leitor descartá-los. Pior: **prosa histórica que cite um caminho já removido** entrava como
declaração — o texto que descrevia o defeito corrigido do `consultar_constituicao_supremo.py` fazia
`~/.notebooklm/constituicao_supremo` reaparecer como recurso externo de um corpus que está
espelhado localmente. Filtro embutido nos quatro; a prosa do Criminal reescrita sem o caminho
literal.

Listas finais de "citado", todas declaradas: Ambiental e Constitucional `~/.claude/agents`;
Criminal `~/.claude/agents` + `~/.notebooklm/biblioteca`; Eleitoral `~/.claude/commands` +
`~/.notebooklm/tools`.

### Pendente do health-check

- **54 notas `status: rascunho` na Wiki do Criminal** — único achado que a norma nomeia como
  problema de método ("rascunho que não sobe é colecionismo"). Não tocado.
- Dois canários de tamanho levemente defasados (Constitucional espera ~119M e tem 118M; Criminal
  espera ~110M e tem 105M). Cosmético.
- 122 marcadores `[VERIFICAR]` em aberto nos quatro — dívida de conferência, trabalho do
  `/verificar-fila`.


---

## AS 54 NOTAS EM `rascunho` DO CRIMINAL — 2026-07-26

Resolvidas, mas **não por troca de flag**. `processado` afirma que a nota está conferida; virar 54
status de uma vez sem auditar seria a mesma patologia que a skill `verificar-fila` proíbe — converter
dívida invisível em nota aparentemente pronta para citar.

O primeiro teste já mostrou que a suspeita era fundada: a nota mais curta atribuía ao **CPP art. 7º**
os "direitos do advogado no inquérito". O art. 7º do CPP é **reprodução simulada dos fatos**; os
direitos do advogado são do **EAOAB (Lei 8.906/94), art. 7º**. Erro real, numa nota prestes a ser
promovida.

Daí a auditoria das **112 citações mecanicamente conferíveis**, contra os datasets canônicos locais:

| Camada | Conferidas | Resultado |
|---|---|---|
| Artigos de código (CPP/CP) | 44 distintos | **1 erro** — o CPP art. 7º acima. Corrigido |
| Súmulas (SV 11/14/24; STJ 64/440/676) | 6 | todas reais |
| Jurisprudência (Tema/HC/REsp/ADI/ADPF/ARE) | 48 distintas | 46 com lastro no clone STF·STJ·TRF1; 1 confirmada no corpus `criminal_player`; **1 sem lastro** |

Método dos artigos: sobreposição de termos entre a glosa da nota e o texto legal local, com revisão
manual dos casos de baixa sobreposição — a maioria era falso positivo do heurístico (glosa usa termo
doutrinário que não aparece na lei: "emendatio libelli" não está no texto do art. 383).

**Sobre a Súmula 676:** o `/sumula-stj` não a alcança porque o dataset para na 656 — mas isso **não
é achado novo**: a base vem do PDF de inteiro teor de 16/11/2022 e a limitação já está registrada
na memória `sumulas-stj-fonte-canonica` ("súmulas posteriores → site STJ / pesquisa-precedentes-web").
A 676 (3ª Seção, 11/12/2024) é real e o vault tem nota própria dela marcada "CONFERIDA".

**Resultado:** 53 notas a `processado`, 1 a `verificar` (o `REsp 1.736.065`, sem lastro em nenhum
corpus, marcado `[VERIFICAR]`), **0 em rascunho**. Conferido que nenhuma nota com marcador ficou
como `processado` — o invariante do §2.6 — e que nenhuma das 54 já carregava marcador antes.

**Limite declarado da auditoria:** para jurisprudência conferiu-se a **existência do número** no
corpus, não a exatidão da tese descrita. Isso afasta o número inventado, que é o risco principal,
mas não substitui a leitura do inteiro teor antes de citar em peça.
