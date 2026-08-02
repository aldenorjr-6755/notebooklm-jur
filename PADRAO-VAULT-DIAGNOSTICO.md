# DIAGNÓSTICO DE CONFORMIDADE — 8 vaults

> Snapshot de **2026-07-26**. Envelhece — a norma está em `PADRAO-VAULT.md` e não envelhece.
> Contagens obtidas por `find | wc -l` na data, excluindo `.obsidian/`. Nenhum número aqui foi
> estimado.

---

## 1. Matriz de estado

| Vault | .md | agentes | commands | skills | tools | corpora | `settings` | CLAUDE.md | index.md | Classe de fato |
|---|---|---|---|---|---|---|---|---|---|---|
| Constitucional | 1265 | 24 | 43 | 11 | 71 | 8 (1064 md) | `json` | 339 | 17 | A |
| Eleitoral | 1145 | 23 | 60 | 4 | 58 | 6 (768 md) | `json` + local | 323 | 16 | A |
| Criminal | 603 | 0 | 39 | 0 | 0 | 0 | só local | 217 | 20 | B |
| Familia | 512 | 0 | 2 | 0 | 0 | 0 | só local | 462 | 9 | B |
| Ambiental | 253 | 24 | 32 | 6 | 62 | 3 (116 md) | `json` | 348 | 16 | A |
| Psicologia | 143 | — | — | — | — | — | **nenhum** | 73 | 8 | B |
| ProcessoCivil | 45 | 0 | **0** | 0 | 0 | 0 | **nenhum** | 92 | 12 | B |
| ExecucaoPenal | 39 | — | — | — | — | — | **nenhum** | 114 | 8 | B |

`—` = o diretório não existe. Psicologia e ExecucaoPenal não têm `.claude/` algum; ProcessoCivil tem
`.claude/commands/` vazio.

**Classe declarada em 2026-07-26** nos oito, em `CLAUDE.md` e `REQUISITOS-EXTERNOS.md` — a coluna
"Classe de fato" acima passou a ser também a classe declarada, e as duas conferem. Ver §8.

Criminal: dos 603 `.md`, **325** são conteúdo — o resto é `.claude/` (39), `_grafo/` (238) e
`graphify-out/` (1). Familia: dos 512, **447** são corpus bruto em `40-Recursos/corpus-stj-familia/`.

**A matriz acima é o estado ENCONTRADO na auditoria.** À época, nenhum dos oito declarava a classe —
era a lacuna universal, a única que atingia 100% do conjunto. Resolvida em 2026-07-26 (§8), junto
com a camada 1 (§4-5) e a propagação das ferramentas de auditoria (§9). As colunas `settings` e
`commands` desta matriz, portanto, **já não valem** para os cinco vaults Classe B: todos passaram a
ter `settings.json` e `/health-check` local.

---

## 2. Os 10 eixos de divergência

**1. Classe de autonomia** — três níveis de fato: autossuficientes (Ambiental, Constitucional,
Eleitoral), parciais com só `commands/` (Criminal 39, Familia 2), e sem infra (ProcessoCivil com
pasta vazia, Psicologia e ExecucaoPenal sem `.claude/`).

**2. Esquema de pastas** — seis vaults no canônico. Eleitoral usa esquema próprio de dez níveis
(`30-Areas`, `50-Outputs`, `60-MOCs`, `70-Agentes`, `90-Arquivo`, `99-Templates`). Psicologia usa
`20-Clinica`/`30-Pesquisa` — adequação legítima ao domínio, mas não declarada como desvio.

**3. Frontmatter** — dois esquemas incompatíveis. Inglês (`aliases/tags/status/created/source/related`)
em Ambiental e Constitucional; português (`titulo/tipo/area/tags/criado/fontes`) em Criminal,
ExecucaoPenal, Familia, ProcessoCivil e Eleitoral (que usa `titulo/tipo/area/tags/criado/fontes` sem
`status` nem `related`). Psicologia praticamente não tem: só `tags` em 103 das 118 notas, `titulo`
em 1. **Familia é o único com tags hierárquicas** (`familia/guarda`, normalizado em 2026-06-29) — é
por isso que virou norma.

**4. Prefixos** — `CONC-/JUR-/LEG-/TESE-` aplicados em Ambiental, Constitucional, ExecucaoPenal,
ProcessoCivil e parte de Familia. Nomes em prosa em Criminal (`10-Wiki/Conceitos/Cadeia de custódia
da prova penal (CPP 158-A).md`), Eleitoral (`AIJE.md`, `AIRC.md`) e Psicologia. Criminal contraria o
que o próprio `CLAUDE.md` declara.

**5. Templates** — `_Templates/TEMPLATE-*.md` em sete vaults; `99-Templates/_template-*.md` em
Eleitoral. **Nenhum dos oito tem o conjunto completo**, e há dois dialetos disjuntos:

| Dialeto | Vaults | Tem | Falta |
|---|---|---|---|
| "Julgado" | Ambiental, Constitucional, Criminal, ProcessoCivil | Caso · Conceito · Julgado · Tese | **Legislacao** |
| "Jurisprudencia" | ExecucaoPenal, Familia | Conceito · Jurisprudencia · Legislacao (+Checklist em Familia) | **Caso · Tese** |
| próprio | Eleitoral | `_template-caso` · `_template-nota` · `_template-tese` | Jurisprudencia · Legislacao |
| mínimo | Psicologia | Autor · Conceito | Obra · e todo o resto |

O caso mais concreto: Ambiental, Constitucional e Criminal têm `10-Wiki/Legislacao/` povoada (6, 7 e
18 notas `LEG-`) **sem nenhum template de legislação** — as notas foram escritas sem esquema.
Psicologia tem `10-Wiki/Obras/` povoada sem `TEMPLATE-Obra`.

**6. MOC** — `MOC-<Vault>.md` na raiz em seis vaults. Eleitoral usa `README.md` + pasta `60-MOCs/`
(15 notas). Psicologia tem `MOC-Psicologia.md` de 9 linhas que é stub apontando para `Mapa do
Vault.md` (108 linhas) — o invariante parece cumprido e não está.

**7. Caminhos absolutos** — 11 ocorrências reais em 3 vaults (§4 abaixo). Além disso, Eleitoral, que
se declara autossuficiente, mantém linha executável externa
(`python ~/.notebooklm/tools/gerar_fontes_canonicas.py`, CLAUDE.md:294-299) que a sua **própria
regra de linha 47** classifica como defeito.

**8. `settings`** — o portátil só existe nos três Classe A. Criminal e Familia têm apenas
`settings.local.json`: ao serem copiados, perdem as permissões. Três vaults não têm nenhum.
Eleitoral tem `skills/lint-vault/` mas seu `settings.json` não traz a permissão de executá-lo — o
único dos três em que `/lint-vault` pede autorização.

**9. `REQUISITOS-EXTERNOS.md`** — existe nos oito, com fidelidade desigual (§5).

**10. Pertencimento** — `~/.claude` hospeda 212 agentes, 73 commands e 152 skills, entre eles ~37
agentes criminais, 4 agentes + 4 skills de Psicologia, `acervo-familia-sucessoes`, `informativo-tse`,
`sc-direito-ambiental`. Nenhum vault Classe B declara essa dependência de forma completa.

---

## 3. Ferramentas de auditoria — quem tem

| Vault | `/health-check` | `lint-vault` |
|---|---|---|
| Ambiental | 61 linhas | skill própria |
| Constitucional | 72 linhas | skill própria |
| Eleitoral | 92 linhas | skill própria (sem permissão no `settings.json`) |
| Criminal · Familia · ProcessoCivil · Psicologia · ExecucaoPenal | ausente | ausente |

O par existia exatamente nos três Classe A. `health-check.md` já era o auditor de conformidade
estrutural que a §2.9 da norma exige — não precisava ser escrito do zero, precisava ser propagado e
recalibrado por vault.

> **Estado superado.** Propagado em 2026-07-26: os oito têm o par. Ver §9.

---

## 4. Caminhos absolutos — inventário completo · CORRIGIDO em 2026-07-26

**Doze** ocorrências (o diagnóstico inicial dizia onze — faltava
`consulta-doutrina-constitucional/SKILL.md:8`, que o primeiro `grep` perdeu por escape de barra
invertida). As duas linhas de detecção dentro dos `health-check.md` de Ambiental e Constitucional
estão excluídas: são o detector, não o defeito.

**Todas as doze foram corrigidas.** Varredura de conferência: zero ocorrências nos oito vaults.

| Arquivo | Linha | Apontava para | Gravidade | Correção aplicada |
|---|---|---|---|---|
| `Constitucional/.claude/skills/consulta-mutacao-constitucional/SKILL.md` | 10 | `C:\Users\alden\Constitucional\...` | **morto** — pré-migração ao OneDrive | `10-Wiki/Conceitos/CONC-Mutacao-…md` |
| `Constitucional/.claude/agents/direitos-fundamentais.md` | 32 | `SegundoCerebro\10-Wiki\Conceitos\` | **morto** — vault em desativação | `10-Wiki/Conceitos/` deste vault |
| `Constitucional/.claude/agents/jurisprudencia-corpus.md` | 38 | `SegundoCerebro\10-Wiki\Jurisprudencia\` | **morto** | `10-Wiki/Jurisprudencia/` deste vault |
| `Constitucional/.claude/agents/senso-incomum.md` | 30 | `SegundoCerebro\10-Wiki\Conceitos\` | **morto** | `10-Wiki/Conceitos/` deste vault |
| `Constitucional/.claude/agents/peca-legal-design.md` | 8 | `SegundoCerebro\40-Recursos\Modelos\` | **morto** | aponta para a skill local `docx-juridico-padrao` |
| `Constitucional/.claude/skills/docx-juridico-padrao/SKILL.md` | 8 | `SegundoCerebro\40-Recursos\Modelos\` | **morto** | ponteiro removido — a skill já traz toda a spec |
| `Criminal/.claude/commands/consulta-depoimento-especial.md` | 36 | `C:\Users\alden\.notebooklm\depoimento_especial\fontes` | executável, não portátil | `$HOME/.notebooklm/…` |
| `Criminal/.claude/commands/consulta-pericia.md` | 46 | `C:\Users\alden\.notebooklm\manuais_pericia\fontes` | executável, não portátil | `$HOME/.notebooklm/…` |
| `Eleitoral/.claude/corpora/coletanea_tse/fragmentar.py` | 10-11 | `C:\Users\alden\.notebooklm\coletanea_tse\` | **errado** — o corpus está no vault | ancorado em `os.path.dirname(__file__)` |
| `Constitucional/.claude/agents/doutrina-constitucional.md` | 13 | o próprio vault | autorreferência redundante | "raiz deste vault" |
| `Constitucional/.claude/agents/rtj-stf.md` | 13 | o próprio vault | autorreferência redundante | "raiz deste vault" |
| `Constitucional/.claude/skills/consulta-doutrina-constitucional/SKILL.md` | 8 | o próprio vault | autorreferência redundante | "deste vault" |

Os cinco que apontavam para `SegundoCerebro` eram os mais graves: o vault está em desativação e,
quando for apagado, cinco agentes e skills do Constitucional passariam a instruir gravação num
caminho inexistente — em silêncio.

O `fragmentar.py` do Eleitoral era pior do que "não portátil": o corpus `coletanea_tse` já vive
**dentro** do vault (`.claude/corpora/coletanea_tse/fontes/`, 22 arquivos), e o script lia a cópia
externa. Rodá-lo fragmentaria o corpus errado.

---

## 5. Lacunas por vault, do mais barato ao mais estrutural

### Camada 1 — defeitos objetivos, correção pontual · **CONCLUÍDA em 2026-07-26**

| # | Vault | Lacuna | Inv. | Status |
|---|---|---|---|---|
| 1 | Constitucional | 5 caminhos mortos p/ `SegundoCerebro`, 1 pré-OneDrive, 3 autorreferências | §2.7 | corrigido (9, não 6) |
| 2 | Criminal | 2 caminhos absolutos executáveis em `commands/` | §2.7 | corrigido → `$HOME/` |
| 3 | Eleitoral | `settings.json` sem permissão para o `lint-vault` que carrega | §2.8 | corrigido |
| 4 | Eleitoral | linha executável externa no `CLAUDE.md`, contra a própria regra da linha 47 | §1.1 | corrigido — seção reescrita: `.claude/tools/` é a fonte canônica; o manual da máquina virou bloco `[externo]` opcional |
| 5 | Psicologia | `REQUISITOS-EXTERNOS.md` listava 2 dos 4 helpers do `CLAUDE.md` | §1.1 | corrigido — os 4 listados, existência conferida em disco |
| 6 | Psicologia | ~~`index.md` diz 114, são 118~~ | §2.3 | **falso positivo do diagnóstico** — ver abaixo |
| 7 | Ambiental · Constitucional · Eleitoral | contagem do `index.md` da raiz defasada | §2.3 | corrigido — os 3 batem com o disco |
| 8 | Psicologia | `00-Grafo/index.md` existe contra o que o `CLAUDE.md` declara | §2.10 | corrigido — o `CLAUDE.md` passou a reconhecer a exceção |
| 9 | Constitucional | 3 notebooks RTJ mortos mantidos riscados | — | documentado, não é defeito |
| 10 | Constitucional | `00-Inbox/` sem `index.md` (surgiu ao corrigir o item 7) | §2.3 | criado |

**Erro corrigido no próprio diagnóstico (item 6).** O `index.md` da Psicologia declara "114 notas"
e o disco tem 114 notas — os 118 do levantamento inicial contavam os quatro `index.md` da própria
`10-Wiki/`. Índice conta **nota**, não arquivo. O critério correto é `find … ! -name index.md`, e
por ele os quatro vaults auditados batem. O que de fato faltava no índice da Psicologia era listar
`REQUISITOS-EXTERNOS`, `00-Grafo/` e `40-Recursos/` — isso foi corrigido.

**Conferência pós-correção:** zero caminhos absolutos nos oito vaults; `settings.json` dos três
Classe A válidos; `fragmentar.py` compila; `lint-vault` em Ambiental e Constitucional com **0**
links quebrados e 0 índices ausentes. Os 7 links quebrados do Eleitoral e as notas órfãs do
Constitucional são pré-existentes, em notas não tocadas, e pertencem à higiene corrente — não à
camada 1.

### Camada 2 — infraestrutura ausente

| # | Vault | Lacuna | Invariante |
|---|---|---|---|
| 10 | ~~**os 8** — não declaram a classe~~ | **RESOLVIDO em 2026-07-26** — ver §8 | §1.1 |
| 11 | Criminal · Familia | ~~só `settings.local.json`~~ | §2.8 | **resolvido** — `settings.json` portátil criado; o `.local` foi preservado |
| 12 | ProcessoCivil · Psicologia · ExecucaoPenal | ~~sem `settings.json`~~ | §2.8 | **resolvido** (mínimo: lint + helpers + grep; completar por vault fica pendente) |
| 13 | ProcessoCivil | ~~`.claude/commands/` vazio~~ | §2.2 | **resolvido** — passou a ter o `/health-check` |
| 14 | Psicologia · ExecucaoPenal | ~~sem `.claude/` algum~~ | §1 | **resolvido** — `.claude/{commands,settings.json}` criado; seguem Classe B |
| 15 | 5 vaults | ~~sem `/health-check`~~ | §2.9 | **resolvido** — ver §9 |
| 16 | 5 vaults | ~~sem acesso a `lint-vault`~~ | §2.9 | **resolvido** — a skill global serve os cinco; testada a partir de cada um |
| 17 | Familia | ~~`CLAUDE.md` duplica o `REQUISITOS-EXTERNOS.md`~~ | §2.1 | **resolvido** — ver §10 |
| 18 | Psicologia | ~~`MOC-Psicologia.md` é stub de 9 linhas~~ | §2.1 | **resolvido** — absorveu o `Mapa do Vault.md` |
| 19 | **os 8** | ~~conjunto de templates incompleto~~ | §2.4 | **resolvido** — 12 templates criados, 5 renomeados |
| 19b | ExecucaoPenal · Familia | ~~sem `TEMPLATE-Caso` nem `TEMPLATE-Tese`~~ | §2.4 | **era falso positivo** — as pastas estão vazias |
| 20 | 15 pastas vazias | ~~sem propósito declarado~~ | §2.2 | **resolvido** — vazio declarado em 7 `CLAUDE.md` |

Pastas vazias: `Ambiental/00-Inbox`, `Ambiental/Anexos`, `Constitucional/Anexos`,
`Eleitoral/00-Inbox`, `Eleitoral/20-Casos`, `Eleitoral/30-Areas`, `Eleitoral/90-Arquivo`,
`ExecucaoPenal/00-Inbox`, `ExecucaoPenal/20-Casos`, `Familia/00-Inbox`, `Familia/20-Casos`,
`Familia/30-Pecas`, `ProcessoCivil/Anexos`, `Psicologia/00-Inbox`, `Psicologia/30-Pesquisa`.
(`00-Inbox` vazio é sinal saudável — inbox processada. Os demais são andaime.)

### Camada 3 — convenções de conteúdo, correção em lote

| # | Vault | Lacuna | Invariante |
|---|---|---|---|
| 21 | ~~Ambiental · Constitucional~~ **e também Criminal, Familia, ExecucaoPenal, ProcessoCivil** | frontmatter em inglês | §2.6 | **resolvido** — ver §11 |
| 22 | Psicologia | ~~sem disciplina de frontmatter~~ | §2.6 | **resolvido** — 114/114, sem inventar `criado` |
| 23 | 7 vaults | ~~tags planas~~ | §2.6 | **resolvido** — hierárquicas em 100% dos 8 |
| 24 | ~~Criminal · Eleitoral · Psicologia~~ **e também Constitucional, ProcessoCivil, Familia** | notas sem prefixo | §2.5 | **resolvido** — 85 renomeadas; exceção declarada em Eleitoral e Psicologia |
| 25 | Ambiental · Constitucional · Criminal · ProcessoCivil | rename `TEMPLATE-Julgado` → `TEMPLATE-Jurisprudencia` | §2.4 |
| 26 | Eleitoral | `99-Templates/_template-*.md` → `_Templates/TEMPLATE-*.md` | §2.4 |
| 27 | Eleitoral · Psicologia | desvio de esquema de pastas não declarado | §2.2 |
| 28 | ProcessoCivil | `tipo: jurisprudencia` em notas conceituais (herdado do SegundoCerebro) | §2.6 |

**Ordem de execução.** A camada 1 e o item 10 (declaração de classe) foram feitos em 2026-07-26. O
próximo passo é propagar `/health-check` + `lint-vault` aos cinco vaults que não os têm (itens
15-16), para que as camadas seguintes passem a ser detectadas automaticamente em vez de auditadas à
mão — agora que a classe está declarada, o `/health-check` sabe qual regra aplicar a cada vault.
Depois os itens 11-13 (`settings.json`) e 17-19 (MOC, duplicação, templates). Só então a camada 3.

Lição da camada 1, que vale para as próximas: **dois dos defeitos catalogados estavam errados** —
um por escape de `grep` (uma ocorrência a menos do que a real) e outro por critério de contagem
(um falso positivo). Antes de corrigir em lote, confira o achado contra o disco com o critério
explícito; o inventário é hipótese, não fato.

---

## 6. Nota sobre `~/.claude` — o que é transversal e o que tem dono

Inventário de 2026-07-26: **212 agentes, 73 commands, 152 skills**. `~/.claude/CLAUDE.md` tem 3
linhas e contém apenas um ponteiro para a skill `graphify` — não há convenção global, roteamento de
vault nem política de caminhos no escopo do usuário.

Recursos com dono identificável por palavra-chave no nome:

| Domínio | agentes | commands | skills | Vault dono | Classe hoje |
|---|---|---|---|---|---|
| Criminal / penal | ~37 | 3 | ~11 | Criminal | B |
| Execução penal | 3 | 0 | 9 | ExecucaoPenal | B |
| Psicologia (`carl-rogers-pca`, `abraham-maslow`, `leslie-greenberg`, `irvin-yalom`) | 4 | 0 | 4 | Psicologia | B |
| Constitucional | 1 | 1 | 3 | Constitucional | **A** |
| Família / sucessões (`acervo-familia-sucessoes`) | 1 | 0 | 1 | Familia | B |
| Eleitoral (`informativo-tse`) | 1 | 1 | 1 | Eleitoral | **A** |
| Ambiental (`sc-direito-ambiental`, `crimes-ambientais-defesa`) | 0 | 1 | 1 | Ambiental | **A** |
| Processo civil | 0 | 1 | 1 | ProcessoCivil | B |

Leituras que isso permite:

- **Criminal é o candidato mais forte a promoção para Classe A** — 37 agentes e ~11 skills prontos,
  `~/.notebooklm/` com sete corpora próprios já mapeados no seu `CLAUDE.md`, e 39 commands locais
  funcionando. Falta mover, espelhar e declarar.
- **Psicologia é hoje uma casca em torno de recursos globais**: os quatro agentes que o seu
  `CLAUDE.md` aponta como caminho principal de consulta vivem todos em `~/.claude`. É um Classe B
  legítimo — desde que declare.
- **Constitucional, Eleitoral e Ambiental deixaram resíduo no global** mesmo já sendo Classe A. Não
  quebra nada (o local tem precedência), mas é duplicação a limpar quando houver ocasião.
- **ProcessoCivil não tem agente próprio nenhum** — e o seu `REQUISITOS-EXTERNOS.md` diz isso com
  exatidão ("nenhum é específico deste vault ainda"). É o vault B mais honesto do conjunto.
- **`~/.claude/settings.json` carrega resíduo de máquina**: uma regra `Bash` aponta para um
  scratchpad de sessão apagada do Eleitoral. Vale uma limpeza quando o global for reorganizado.

Nada disso foi executado. É insumo para a decisão de promover vaults, que é sua e vem depois.

---

## 7. Calibração do checklist

O checklist da §4 da norma foi rodado contra os dois extremos do conjunto, para conferir se reprova
nos eixos certos:

| Eixo | Ambiental (Classe A madura) | ExecucaoPenal (sem infra) |
|---|---|---|
| Raiz — 4 arquivos | passa | passa |
| Declaração de classe | **reprova** | **reprova** |
| `settings.json` | passa | **reprova** |
| `/health-check` | passa | **reprova** |
| `lint-vault` | passa | **reprova** |
| Templates (um por pasta) | **reprova** (falta Legislacao) | **reprova** (falta Caso, Tese) |
| Prefixos em `10-Wiki/Conceitos/` | passa (16/16) | passa (16/16) |
| Frontmatter em português | **reprova** (esquema em inglês) | passa (16/16) |
| Caminhos absolutos | passa | passa |

Os dois reprovam em eixos **opostos** — Ambiental na convenção de nota, ExecucaoPenal na
infraestrutura —, que é exatamente o que a matriz da §1 prevê. O checklist está calibrado.

Um ajuste saiu daí: o teste inicial procurava a palavra "autossuficiente" e deu **falso positivo nos
oito vaults**, porque a expressão aparece em prosa nos `REQUISITOS-EXTERNOS.md` sem constituir
declaração. Por isso a norma passou a exigir o marcador literal `**Classe A` / `**Classe B` (§1.1).

---

## 8. Declaração de classe — CONCLUÍDA em 2026-07-26

Marcador literal inserido nos **16 arquivos** (`CLAUDE.md` + `REQUISITOS-EXTERNOS.md` dos oito
vaults). Conferência automática: nos oito, o marcador do `CLAUDE.md`, o do `REQUISITOS-EXTERNOS.md`
e a classe real medida em disco (existência de `.claude/{agents,skills,tools}`) coincidem.

| Vault | Classe | O que a declaração registra |
|---|---|---|
| Ambiental · Constitucional · Eleitoral | **A** | tudo em `.claude/`; nenhuma linha executável aponta para fora |
| Criminal | **B** | 39 slash commands locais; ~37 agentes e ~11 skills em `~/.claude/` |
| Familia | **B** | corpus STJ interno (437 MDs) + 2 slash commands; agentes e skills externos |
| ProcessoCivil | **B** | `.claude/commands/` vazia; ainda sem agente próprio |
| Psicologia | **B** | sem `.claude/`; os 4 agentes-caminho-principal vivem no escopo de usuário |
| ExecucaoPenal | **B** | sem `.claude/`; tudo vem do escopo de usuário |

**Desambiguação necessária.** Quatro vaults Classe B abriam o `REQUISITOS-EXTERNOS.md` com "este
vault é **autossuficiente** para leitura e navegação" — a mesma prosa que produzira o falso positivo
do §7, e que agora colidiria frontalmente com a declaração de Classe B. Foi reescrita para "legível e
navegável offline", que diz a mesma coisa sem disputar o termo. Conferido: **"autossuficiente" é hoje
exclusivo dos vaults Classe A.**

Dois pontos declarados com honestidade, em vez de maquiados:
- **Familia** — o `CLAUDE.md` duplica o `REQUISITOS-EXTERNOS.md` e as listas divergem (item 17). A
  declaração diz qual dos dois vale (o arquivo da raiz) enquanto a duplicação não for desfeita.
- **ProcessoCivil** e **Psicologia/ExecucaoPenal** — a declaração registra explicitamente a
  `.claude/commands/` vazia e a ausência de `.claude/`, em vez de omitir.

Verificação pós-declaração: `lint-vault` em Ambiental **totalmente limpo**; Constitucional e
Eleitoral de volta à linha de base anterior à sessão (3 e 4 índices stale por mtime, 9 e 5 notas
órfãs, 7 links quebrados no Eleitoral — todos pré-existentes, em notas não tocadas). Zero caminhos
absolutos. Nenhuma regressão.

---

## 9. Auditoria propagada — CONCLUÍDA em 2026-07-26

Os oito vaults passaram a ter o par `/health-check` + `lint-vault` exigido pela §2.9 da norma.

| | `/health-check` | `lint-vault` | `settings.json` |
|---|---|---|---|
| Ambiental · Constitucional · Eleitoral (A) | local, já existia | skill própria | já existia |
| Criminal · ExecucaoPenal · Familia · ProcessoCivil · Psicologia (B) | **local, criado** | **skill global** (conforme §2.9) | **criado** |

**`lint-vault` não foi copiado.** A skill global (`~/.claude/skills/lint-vault/`) é byte-idêntica à
dos vaults Classe A, e a norma manda Classe B usar a global. Foi testada a partir de cada um dos
cinco: roda e produz relatório.

**`/health-check` foi escrito, não copiado.** O comando carrega as contagens esperadas e as
dependências *daquele* vault — copiar o do Ambiental seria propagar canários que apontam para
corpora inexistentes. Cada um dos cinco foi calibrado com números conferidos em disco, e a Parte 2
foi reescrita para o dever de Classe B: em vez de "nenhum caminho externo" (regra de Classe A), o
teste é **"toda dependência externa usada está declarada em `REQUISITOS-EXTERNOS.md` e resolve"**.

Parte 4 (conteúdo jurídico) é específica por domínio. Dois casos merecem nota: em **Familia**, o
achado de dado sensível cobre guarda, alimentos e violência doméstica, com segredo de justiça; em
**Psicologia**, o item 1 é sigilo profissional sobre processo terapêutico e o relatório é instruído
a trazê-lo sempre em primeiro lugar, independentemente da ordem dos demais.

### O que a ferramenta encontrou ao ser testada

O detector de coerência de Classe B (Parte 2b) apontou, na primeira rodada, dependências não
declaradas em quatro vaults. **A maioria era falso positivo do próprio detector**: os
`REQUISITOS-EXTERNOS.md` declaram helpers em notação de chaves —
`consultar_{codigo,bnp,sumula_stj,...}.py` — e um `grep` pelo nome inteiro não casa com essa forma.
Conferido contra o arquivo, restou **uma** lacuna real, uniforme: `gerar_fontes_canonicas.py` era
usado na seção "Fontes canônicas" do `CLAUDE.md` de Criminal, ExecucaoPenal, Familia e Psicologia
sem estar declarado. Declarado nos quatro.

A armadilha foi registrada dentro dos cinco `/health-check`, como bloco de cuidado — sem isso, toda
execução futura repetiria os mesmos falsos positivos.

Outros dois achados do teste de fumaça, corrigidos: o canário da LEP no `/health-check` do
ExecucaoPenal usava flag inexistente (`--artigo`; o helper recebe a consulta como posicional), e o
do Psicologia declarava "esperado: 8 índices" quando faltava o de `40-Recursos/` — o índice foi
criado e a expectativa passou a 9, para não consagrar um defeito como norma.

**Estado do `lint-vault` nos cinco após a propagação:** zero índices ausentes em todos. Os 5 links
quebrados do Criminal estão numa única nota criada por sessão paralela
(`JUR-Floyd-v-City-of-New-York-Stop-and-Frisk.md`, apontando para `[[Floyd-1o-grau]]` e
`[[Floyd-2o-grau]]`, que não existem) — pré-existentes, não tocados aqui.

### Efeito colateral: o `/health-check` global

O comando de escopo de usuário (`~/.claude/commands/health-check.md`) estava obsoleto: mandava
atualizar `60-MOCs/🗺️ MOC Principal.md`, caminho que não existe em sete dos oito vaults, e não
rodava o `lint-vault` nem checava caminhos. Foi reescrito como **fallback genérico** que reconhece
as duas classes, aponta para os exemplares (`Ambiental` para A, `ProcessoCivil` para B) e avisa que
o local deve prevalecer. Como os oito agora têm o comando local, o global só será alcançado por
vault novo — que é exatamente quando ele precisa dizer o que fazer.

---

## 10. Camada 2 concluída — itens 17-20, em 2026-07-26

### Item 17 — a duplicação do Familia

O diagnóstico presumia que a seção do `CLAUDE.md` era a cópia ruim a descartar. **Era o contrário:**
a seção tinha 70 linhas — mapa helper→slash, o que é interno ao vault, detalhe de permissões, IDs de
notebook e checklist de restauração —, contra 31 linhas no `REQUISITOS-EXTERNOS.md`. A resolução foi
migrar o conteúdo bom para o arquivo canônico e deixar no `CLAUDE.md` só um ponteiro.

Duas divergências apareceram na consolidação: o corpus era descrito como 436 MDs num arquivo e 437
noutro (são 437), e as permissões citavam só o `settings.local.json`, ignorando o `settings.json`
criado na etapa anterior. Ambas corrigidas.

### Item 18 — o MOC da Psicologia

`MOC-Psicologia.md` (9 linhas) apontava para `Mapa do Vault.md` (108 linhas), que era o MOC de fato.
A norma admitiria manter o nome próprio com desvio declarado, mas o custo era permanente. Optou-se
pela consistência: o conteúdo foi promovido a `MOC-Psicologia.md`, o `Mapa do Vault.md` deixou de
existir, e as 6 referências (incluindo duas em `00-Grafo/`, gerado) foram atualizadas.

### Item 19 — templates

**A decisão `TEMPLATE-Jurisprudencia` foi revertida para `TEMPLATE-Julgado`.** O motivo é novo e
decisivo: o e-book *O Segundo Cérebro Jurídico*, publicado em `Criminal/60-Ebook/`, **ensina**
`TEMPLATE-Julgado` em dois capítulos (`cap-05`, `apendice-a`). Manter a norma original criaria
conflito com a documentação já escrita, para ganhar apenas coerência estética com o nome da pasta.
Quatro vaults já usavam `Julgado`, contra dois. Renomeados os dois (ExecucaoPenal, Familia).

**Item 19b era falso positivo do diagnóstico.** ExecucaoPenal e Familia foram listados como faltando
`TEMPLATE-Caso` e `TEMPLATE-Tese` — mas `20-Casos/` e `10-Wiki/Teses/` estão **vazias** nos dois. A
regra é um template por pasta *povoada*; pasta vazia não exige template (exige declaração, item 20).
A norma foi ajustada para dizer isso explicitamente.

Criados 12 templates: `TEMPLATE-Legislacao` (Ambiental, Constitucional, Criminal, ProcessoCivil,
Eleitoral), `TEMPLATE-Checklist` (Ambiental, Constitucional, Criminal, ExecucaoPenal),
`TEMPLATE-Obra` (Psicologia), `TEMPLATE-Autor` (ProcessoCivil), `TEMPLATE-Conceito` e
`TEMPLATE-Julgado` (Eleitoral). Todos no esquema PT normativo.

No Eleitoral, os três templates existentes foram normalizados de `_template-<tipo>.md` para
`TEMPLATE-<Tipo>.md`. **Isso quase causou uma falha muda:** o `REQUISITOS-EXTERNOS.md` daquele vault
avisa que o mapa de folder templates do Templater (`.obsidian/plugins/templater-obsidian/data.json`)
aponta para arquivos por caminho, e que "mapa apontando para template inexistente é falha muda — o
Templater não avisa, a nota apenas nasce vazia". O JSON foi atualizado na mesma operação, ampliado
para as três pastas que ganharam template próprio, e reordenado (mais específico antes do genérico).
Conferido: os 6 mapeamentos resolvem para arquivo existente. Outras 9 referências textuais aos nomes
antigos foram corrigidas em `CLAUDE.md`, `README.md`, `REQUISITOS-EXTERNOS.md`, dois slash commands e
uma skill.

A norma foi ajustada em dois pontos: o nome do arquivo de template é invariante, mas **a pasta segue
o esquema declarado** em §2.2 (o Eleitoral mantém `99-Templates/`, coerente com seu esquema numerado);
e templates só são exigidos para pastas povoadas.

### Item 20 — pastas vazias

A norma ganhou uma exceção que faltava: **`00-Inbox/` vazia é o estado saudável**, não lacuna —
significa que a captura foi processada. É o acúmulo ali que é sintoma.

Para as demais, optou-se por **declarar em vez de remover** — remover é irreversível e várias são
reservas legítimas. Sete `CLAUDE.md` ganharam um bloco "Pastas hoje vazias, e por quê", logo abaixo
da tabela de estrutura. O caso mais relevante: `20-Casos/` está vazia em Eleitoral, ExecucaoPenal,
Familia e ProcessoCivil, e isso é **decisão, não descuido** — os quatro proíbem dado sensível no
cofre, e caso eleitoral, execução penal e família trazem nome, número de processo e segredo de
justiça. Ficou registrado como reserva condicionada à anonimização.

### Conferência

Template por pasta povoada: **completo nos oito**. Nenhum `TEMPLATE-Jurisprudencia` ou `_template-*`
remanescente. Vazio declarado em todos os sete vaults que têm pasta vazia. `lint-vault` nos oito:
**zero resíduos de template** (os novos não poluíram) e zero links quebrados nos vaults tocados.

Achados de terceiros, não corrigidos por não serem meus: os links quebrados do Criminal (`[[ADPF635]]`,
`[[Floyd-1o-grau]]`, `[[Floyd-2o-grau]]`) e os 7 do Eleitoral são pré-existentes, em notas de sessão
paralela. E **um caminho absoluto novo apareceu** em `Constitucional/00-Inbox/index.md`, num link
`file:///C:/Users/alden/.claude/CLAUDE.md` inserido por sessão paralela — viola §2.7 e fica para
decisão do usuário, já que foi edição deliberada de outro contexto.

---

## 11. Camada 3 concluída — itens 21-24, em 2026-07-26

### O diagnóstico subestimou dois itens

Só ao verificar o resultado é que apareceu o tamanho real:

- **Item 21** listava dois vaults em inglês (Ambiental, Constitucional). Eram **seis**: Criminal
  tinha 164 notas em `created/source/related`, e Familia, ExecucaoPenal e ProcessoCivil tinham
  frontmatter incompleto. A amostra de três notas que gerou o diagnóstico não era representativa.
- **Item 24** listava três vaults sem prefixo (Criminal, Eleitoral, Psicologia). Eram **seis**:
  Constitucional (18), ProcessoCivil (24) e Familia (4) também declaram o prefixo no próprio
  `CLAUDE.md` e não o aplicavam — exatamente o critério que motivou incluir o Criminal.

Ambos foram completados no alcance real, não no catalogado.

### O que foi feito

**Item 21 — frontmatter em português.** 93 notas convertidas em Ambiental e Constitucional, mais
171 no Criminal, 46 na Familia, 15 na ExecucaoPenal e 1 no ProcessoCivil. `created` → `criado`,
`updated` → `atualizado`, `source` → `fontes` (string vira lista), e acréscimo de `titulo` (do H1),
`tipo` (da pasta) e `area`. Convertidos também os 27 arquivos que os conversores iniciais não
alcançaram: notas de `40-Recursos/`, os MOCs e — o mais importante — **os 8 templates antigos**, que
continuariam parindo notas em inglês. Os blocos de documentação dos dois `CLAUDE.md` que ensinavam
o esquema em inglês foram reescritos.

Resultado: `titulo`, `tipo` e `area` em **688/688 notas** dos oito vaults; zero chaves em inglês;
zero YAML quebrado.

**Item 22 — Psicologia.** As "11 notas sem frontmatter" eram, na verdade, notas com **BOM** antes
do `---`, o que enganava a checagem. Todas as 114 ganharam `titulo`, `tipo` e `area`. **`criado`
ficou ausente de propósito**: a data real de criação não existe em lugar nenhum, e preenchê-la com
`mtime` ou com a data de hoje seria inventar dado com aparência de registro. A norma passa a exigir
`criado` nas notas novas, via template.

**Item 23 — tags hierárquicas.** Regra aplicada: a tag que repete o `tipo` fica plana; as demais
recebem o prefixo da área (`[conceito, EFT, casal]` → `[conceito, psicologia/eft, psicologia/casal]`).
Nenhuma taxonomia nova foi inventada — só reorganizou o que já existia. Precisou de três passadas:
a primeira só pegava tags em linha, deixando as em bloco; e Eleitoral e Familia tinham ficado fora
da lista de alvos. Estado final: **hierárquicas em 100% das notas dos oito vaults**.

**Item 24 — prefixos.** 85 notas renomeadas para o estilo já usado pelas demais (ASCII, hifens,
prefixo de tipo): Criminal 38, ProcessoCivil 24, Constitucional 18, Familia 4. Cada rename gravou o
**nome antigo em `aliases`** antes de mover — rede de segurança para qualquer link que escapasse — e
reescreveu os wikilinks em todo o vault, cobrindo as três formas (`[[X]]`, `[[X|texto]]`, `[[X#seção]]`).

Eleitoral (173 notas) e Psicologia (114) **não foram renomeados**: nomeiam pelo instituto (`AIJE.md`)
e pelo autor (`Carl Rogers.md`), e a norma ganhou a exceção correspondente (§2.5), condicionada a
duas coisas — a convenção declarada no `CLAUDE.md` e o campo `tipo` em 100% das notas. A condição
foi conferida: Eleitoral tinha 171/173 e as duas faltantes foram corrigidas (uma delas era resíduo
em esquema inglês, importado de outro vault).

### Conferência

| Eixo | Resultado |
|---|---|
| `titulo` · `tipo` · `area` | 688/688 notas |
| Chaves em inglês (`created`/`source`) | 0 |
| YAML quebrado | 0 em 688 |
| Tags hierárquicas | 100% dos 8 vaults |
| Notas sem prefixo (fora de `Autores/`) | 0 |
| `lint-vault` — links quebrados **novos** | **0**, após 85 renomeações |
| `lint-vault` — índices ausentes/desatualizados | 0 nos 8 |

Os 14 links quebrados que restam (7 no Criminal, 7 no Eleitoral) são pré-existentes, em notas de
sessões paralelas, e não foram tocados.

### Ressalva de método

Três vezes nesta sequência um achado meu não sobreviveu à conferência: o `grep` com escape errado
(§4), a contagem que somava `index.md` como nota (§5), o critério de template em pasta vazia (§10) —
e agora o alcance dos itens 21 e 24. O padrão é sempre o mesmo: **medir por amostra e generalizar**.
A conferência pós-execução é o que pegou todos. Ela não é formalidade.

---

## 12. Criminal promovido a Classe A — 2026-07-26

O conjunto passa a ter **4 vaults Classe A** (Ambiental, Constitucional, Eleitoral, Criminal) e
**4 Classe B** (ExecucaoPenal, Familia, ProcessoCivil, Psicologia).

| Camada | Antes | Depois |
|---|---|---|
| Agentes | 0 (86 em `~/.claude`) | **86** em `.claude/agents/` |
| Skills | 0 | **131** em `.claude/skills/` |
| Helpers + datasets | 0 | **28 py + 56 json** |
| Corpora | 0 | **14 acervos, 1.004 arquivos, 106 MB** |
| `settings.json` | mínimo | allowlist de Classe A |

**Cópia, não movimento.** O original continua em `~/.claude/` e `~/.notebooklm/`, servindo os quatro
vaults Classe B — é o mesmo critério que o Eleitoral já registrava ("três skills locais são cópias,
não movimentos"). Mover teria quebrado Familia, ExecucaoPenal e ProcessoCivil, que declaram depender
desses agentes.

### O que ficou fora, e por quê

Três acervos não foram espelhados, e a perda está declarada na §3 do `REQUISITOS-EXTERNOS.md` do
vault: **Informativos STJ** (835 MDs, 356 MB — triplicaria o vault; mesma decisão de Ambiental e
Constitucional), **biblioteca de PDFs** (382 MB, já destilada nos datasets) e **Senso Incomum**
(744 artigos de hermenêutica — acervo do vault Constitucional, não deste).

### O que a promoção revelou

A cópia em massa importou defeitos que estavam invisíveis no escopo global:

- **109 caminhos absolutos** `C:\Users\alden\...` dentro dos agentes e skills copiados — inclusive
  quatro apontando para o `SegundoCerebro`, vault em desativação, e um em `consultar_cadh_stf.py`
  com caminho absoluto hardcoded no código.
- **O `SKILL.md` global do `lint-vault` ainda usa o caminho pré-migração** (`C:\Users\alden\<Nome>`),
  que não existe desde que os vaults foram para o OneDrive. Foi substituído no Criminal pela versão
  corrigida do Ambiental — **mas o global segue defeituoso** e afeta quem o invocar de outro vault.
- Um typo de anos (`consultar_consituicao_supremo`, sem o "t") propagado em documentação.

Tudo corrigido dentro do vault. Estado final: **zero caminhos absolutos**; as únicas referências
externas são os três acervos opcionais declarados e ponteiros em prosa (`FONTES-CANONICAS.md`,
`PADRAO-VAULT.md`, convenção de `prazos/`).

### Armadilha de escape que custou três tentativas

O regex de reescrita `[Cc]:[\/]+[Uu]sers...` **não casava caminho com barra invertida** quando o
script era passado por heredoc do shell: uma das duas barras era consumida antes de chegar ao
Python, e a classe `[\/]` passava a aceitar só a barra normal. Diagnóstico só apareceu ao testar o
padrão isoladamente. Solução: escrever o script em arquivo (`Write`) em vez de heredoc, e montar o
separador com `chr(92)`. **Vale para qualquer reescrita de caminho Windows neste ambiente.**

### Conferência

Helpers rodando offline a partir da raiz do vault (`consultar_codigo --fonte cpp 158-A`,
`consultar_sumula_stj 545`, `consultar_criminal_player`), corpora respondendo a `grep`, `lint-vault`
local funcionando, `settings.json` válido, e o `/health-check` reescrito para auditar as duas
obrigações da Classe A — infraestrutura dentro e nenhuma linha executável para fora.

---

## 13. Convenção de declaração unificada nos 4 Classe A — 2026-07-26

Havia dois dialetos. Ambiental e Constitucional exigiam **marca inline** (`[externo]` ou
`[corpus externo opcional]`) em cada citação; Criminal declarava **por nome** numa seção do
`REQUISITOS-EXTERNOS.md`; Eleitoral misturava os dois. Unificado na declaração por nome.

**Por que a marca inline caiu — dois defeitos concretos, não preferência estética:**

1. No `verificador-citacoes` do Ambiental, a marca estava **dentro de linhas de comando**:
   `` `python .claude/tools/consultar_jurisprudencia.py **[externo — …]** --tribunal stj "termo"` ``.
   O comando não podia ser copiado e colado. Duas linhas nessa situação.
2. A marca tinha **duas formas aceitas**, e um `grep` que procurasse só uma produzia falso positivo.
   Aconteceu na auditoria da §12: reportei como defeito uma linha que já estava conforme.

A declaração por nome, em lugar único, é verificável por **diferença de listas** — a marca espalhada
pelo texto não era.

### A regra agora (norma §2.7)

Recurso externo citado tem de estar listado pelo nome na seção de declaração do
`REQUISITOS-EXTERNOS.md` do vault. Citado e não declarado = defeito. Declarado e não citado =
declaração a revisar. **Não contam como dependência:** `PADRAO-VAULT.md` (ponteiro da norma),
`FONTES-CANONICAS.md` (catálogo da máquina) e `prazos/` (diretório de saída).

Estado após a unificação — os quatro **conformes**, zero marcadores inline remanescentes:

| Vault | Declarados | Citados |
|---|---|---|
| Ambiental | informativo_stj · direitos_fundamentais | informativo_stj |
| Constitucional | informativo_stj · boletins_precedentes_stj · biblioteca | nenhum |
| Eleitoral | FONTES-CANONICAS + gerador · `~/.claude/{agents,skills,commands}` | gerador · commands |
| Criminal | informativo_stj · biblioteca · senso_incomum | os três |

### Três falsos positivos que o afinamento do detector eliminou

A primeira execução do confronto acusou defeito em três vaults. Nenhum era real:

- **Constitucional/senso_incomum** — a citação estava dentro de `.claude/corpora/`, num documento de
  levantamento. Corpus é material-fonte, não configuração: o grep passou a excluir `corpora/`.
- **Criminal/`~/.notebooklm/...`** — o regex casava a **reticência** da prosa. Passou a exigir letra
  depois da barra.
- **Criminal/prazos** — diretório de saída, que a própria regra já dizia não contar. Excluído no grep.

### Nota de método — o byte 0x01

Ao escrever o novo bloco da Parte 2 por heredoc do shell, o `\1` do `sed` foi gravado como o **byte
de controle 0x01**, não como os dois caracteres. O arquivo ficou com um comando quebrado e o `Edit`
não conseguia casar o texto. Varredura de bytes de controle em `.claude/` e no escopo global: **um
único arquivo afetado**, saneado.

Detalhe que quase escondeu o problema: `glob('**/*.md')` **não entra em diretório que começa com
ponto** — a primeira varredura passou longe de `.claude/`, que era exatamente onde estava o estrago.
Para varrer dotfolder, `os.walk`.

É a terceira armadilha de ambiente desta sequência, todas com a mesma origem — passar texto com
barra invertida pelo shell: (1) `[\/]` que deixa de casar barra invertida, (2) `io.open(...,"w")`
que converte LF em CRLF e derruba o agente do registro, (3) `\1` que vira 0x01. **Regra prática:
script que reescreve texto vai em arquivo, escrito pela ferramenta de escrita — nunca por heredoc.**

---

## 14. Auditoria de descrição/regras/extensão dos `CLAUDE.md` — 2026-08-01

Disparada por pedido do usuário para conferir os `CLAUDE.md` dos 13 vaults contra melhores práticas
(externas — docs oficiais da Anthropic — e internas — este `PADRAO-VAULT.md`). Cobre também os
**4 vaults nascidos depois do snapshot de 2026-07-26** e nunca antes auditados: Trabalhista,
JuntaMedica, MestradoCeuma e Dissertacao (este último já existia em 2026-07-26 mas não entrou na
matriz da época).

### Referencial externo (Anthropic, `code.claude.com/docs/en/best-practices` e `.../memory`)

Conferido via pesquisa web em 2026-08-01: `CLAUDE.md` sem formato obrigatório, mas "conciso e
legível"; suporta `@caminho` com import recursivo até **4 níveis** (não 5); hierarquia de memória
Enterprise > Projeto > Usuário > `CLAUDE.local.md` (depreciado). Nenhum dos 13 vaults usa `@import`
nativo — todos usam wikilink `[[...]]` para apontar a `REQUISITOS-EXTERNOS.md`, que é convenção do
Obsidian e **não é resolvida automaticamente pelo Claude Code** (a IA decide se abre ou não). Fica
registrado como opção, não como defeito: trocar por `@REQUISITOS-EXTERNOS.md` garantiria carregar o
conteúdo, ao custo de sempre pagar aquele token mesmo quando não precisar — dado que a norma já
sanciona a variação de tamanho (§7, "não uniformiza"), a opção fica em aberto por vault.

### Checklist §4 rodado contra os 4 vaults não cobertos em 2026-07-26

| Eixo | Trabalhista (A) | JuntaMedica (B, fora do domínio jurídico) | MestradoCeuma (B, projeto) | Dissertacao (B, projeto) |
|---|---|---|---|---|
| Raiz — 4 arquivos + MOC | passa | passa | **reprova — sem `MOC-MestradoCeuma.md` e sem desvio declarado** | passa |
| Declaração de classe | passa | passa | passa | passa |
| `settings.json` | passa | passa | passa | passa |
| `/health-check` local | passa | **n/a, declarado** (domínio clínico, fora do escopo do padrão jurídico) | **reprova — ausente e não declarado** (vault-irmão `Dissertacao` tem) | passa |
| `lint-vault` | usa global (skills/ vazia — pendência já declarada em `REQUISITOS-EXTERNOS.md` §3) | **n/a, declarado** | usa global | usa global |
| Caminhos absolutos | **reprova — corrigido nesta sessão** (3 ocorrências, ver abaixo) | passa | passa | passa (1 achado é falso positivo, ver abaixo) |
| Frontmatter em português, 7 chaves | passa (amostra) | **reprova parcial** — `titulo` ecoa o prefixo do arquivo (ver abaixo) | passa (amostra) | não amostrado nesta rodada (já coberto por auditorias anteriores do próprio vault) |

### Achados e o que foi corrigido nesta sessão

1. **Trabalhista/REQUISITOS-EXTERNOS.md — 3 caminhos absolutos** (`C:/Users/alden/.notebooklm/jusbrasil/jusbrasil_cli.py`, linhas 25/76/81). Violação direta do §2.7 ("zero caminho absoluto, sem exceção de classe"). **Corrigido** → `~/.notebooklm/jusbrasil/jusbrasil_cli.py`.
2. **Dissertacao e MestradoCeuma — `CLAUDE.md` e (achado nesta auditoria) também `REQUISITOS-EXTERNOS.md` de Dissertacao — sem acentuação** (ASCII puro, único caso do conjunto). Quebra a legibilidade em português e criava ambiguidade real: "Vault Dissertacao — constituicao" sem o til podia ler-se como se o vault fosse sobre Direito Constitucional, que não é. **Corrigido nos três arquivos**, preservando sem acento tudo que é literal (nomes de pasta, prefixos, valores de frontmatter, wikilinks) e reacentuando prosa e as citações do edital — ex.: "Alcantara" → "Alcântara" (Corte IDH), hoje fiel ao texto oficial em vez de perpetuar a corrupção.
3. **Eleitoral — bloco "Estilo de trabalho" divergente**: faltava o bullet "Fallback silencioso" presente nos outros 4 vaults com o mesmo bloco, e carregava um bullet redundante de idioma (já dito em "Quem sou eu"). **Corrigido.**
4. **JuntaMedica — ordem do cabeçalho**: blockquote de classe vinha *antes* do H1, único caso entre os 13. **Corrigido** (H1 primeiro, blockquote depois).
5. **`PADRAO-VAULT.md` §3 (modelos de referência) — desatualizado**: citava ProcessoCivil com "92 linhas"; o vault cresceu (seção "Ramos hospedados") e está em ~123. **Corrigido**, com nota de que `settings.json` e a declaração de classe — que o texto antigo listava como pendência — já foram resolvidos (ver §8-9 acima).
6. **Frase de propósito ausente em 8 dos 13 `CLAUDE.md`** (Criminal, Dissertacao, ExecucaoPenal, Familia, JuntaMedica, MestradoCeuma, ProcessoCivil, Psicologia) — só 4 vaults + o `SegundoCerebro` abriam dizendo o que o arquivo *é* ("lido automaticamente... é a constituição deste cofre"). Nenhuma norma exige a frase, mas é exatamente o tipo de descrição que evita que humano e IA tenham de inferir o papel do arquivo. **Adicionada nos 8**, dentro do blockquote de classe já existente.
7. **Falso positivo confirmado, não corrigido**: `Dissertacao/40-Recursos/UNB-2025-Xukuru-Ororuba-Corte-IDH.md:9126` tem um `file:///C:/Users/SAMSUNG/Downloads/...` — é hyperlink herdado do PDF de origem (nome de usuário de terceiro, não desta máquina), dentro da camada RAW, que deve ficar **fiel** ao original (§2.5.4). Não é o vault citando caminho absoluto próprio; não mexer.

### Achados registrados, não corrigidos nesta sessão — pendem decisão

8. **MestradoCeuma sem `MOC-MestradoCeuma.md`** — nenhum arquivo, stub ou substituto nomeado, e o `CLAUDE.md` não declara o desvio. É o único dos 13 vaults sem MOC nem exceção declarada. Criar o arquivo exige curadoria de conteúdo (não é correção mecânica) — fica para quando o usuário quiser.
9. **MestradoCeuma sem `/health-check` local** — o vault-irmão `Dissertacao` (mesmo padrão de vault de projeto) tem; aqui não há, e não está declarado como decisão consciente.
10. **JuntaMedica — `titulo` do frontmatter ecoa o prefixo do arquivo**: `titulo: CONC-Acidente-Isquemico-Transitorio` em vez de um nome legível ("Acidente Isquêmico Transitório (AIT)"), nas notas amostradas de `10-Wiki/Conceitos/`. Contraria o próprio padrão ("Nome legível da nota") — provável efeito de captura em lote sem revisão de título. Extensão do problema (quantas notas) não medida; requer critério clínico por nota, não só mecânico.

### Item 7 — blocos-padrão de `CLAUDE.md` (novo `PADRAO-VAULT.md` §6)

Quatro blocos de regra eram colados quase byte a byte em 8 a 12 vaults sem fonte única declarada —
e já haviam divergido de fato (achado 3 acima). Criado `PADRAO-VAULT.md` §6A-D com o texto canônico
de cada um, e anotada a proveniência (`*Bloco-padrão — texto canônico em \`PADRAO-VAULT.md\` §6X;
mudar a regra lá primeiro.*`) nas cópias locais:

| Bloco | Vaults anotados | Vaults com a mesma regra em formato divergente (não anotados) |
|---|---|---|
| §6A Estilo de trabalho | Ambiental, Constitucional, Criminal, Eleitoral, Trabalhista | — |
| §6B Aviso `obsidian_*`/porta 27124 | Ambiental, Constitucional, Dissertacao, ExecucaoPenal, Familia, Psicologia | Criminal e ProcessoCivil trazem o mesmo conteúdo, mas embutido como bullet dentro de "Convenções deste vault", não como bloco autônomo — não anotados para não forçar reestruturação fora do escopo pedido |
| §6C Índices de navegação | Ambiental, Constitucional, Criminal, Eleitoral, ExecucaoPenal, Familia, ProcessoCivil, Psicologia, Trabalhista | Dissertacao, MestradoCeuma e JuntaMedica não têm o bloco (vaults de projeto/pessoal com regra de índice mais enxuta) — não é defeito, registrado como ponto de checagem |
| §6D Fontes canônicas (2 variantes: Classe A / Classe B) | não anotado por vault — o texto varia por natureza (nomes de helpers próprios); a seção do padrão documenta as duas variantes e quem usa cada uma | — |

A cópia continua obrigatória nos 13 vaults (Classe A não pode depender de `@import` externo sem
quebrar portabilidade); o que mudou é que agora há **uma** fonte para conferir antes de editar
qualquer uma das cópias, em vez de confiar em memória de quantos lugares repetem a regra.

### Conferência

Zero caminhos absolutos remanescentes nos 4 vaults auditados (fora do falso positivo declarado no
item 7 acima). Acentuação: 3 arquivos corrigidos, zero pendências de ASCII detectadas nos demais 10
vaults + `PADRAO-VAULT.md`. Frase de propósito: presente agora em 12 dos 13 `CLAUDE.md` de domínio
(falta só o `SegundoCerebro`, que já tem versão equivalente própria e está em desativação).
