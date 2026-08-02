# PADRÃO DE VAULT — especificação canônica

> Norma que governa **todos** os vaults Obsidian em `~/OneDrive/0-Obsidian/`.
> Mora aqui, e não dentro de um vault, porque uma norma que vale para os oito não pode
> pertencer a um deles. Mesmo lugar de `FONTES-CANONICAS.md` (manual único da infra compartilhada).
>
> Estado da conformidade real: ver `PADRAO-VAULT-DIAGNOSTICO.md` (snapshot datado, envelhece).
> Este arquivo é a norma e não envelhece com o inventário.

Fixada em 2026-07-26. Método de base: CODE (Tiago Forte) + arquitetura Karpathy (RAW → WIKI → OUTPUTS).

---

## 1. As duas classes de vault

O padrão é **híbrido explícito**: admite dois modelos de autonomia. O que ele **não** admite é um
vault que não diga em qual está, ou que diga um e se comporte como o outro.

| | **Classe A — autossuficiente** | **Classe B — leve** |
|---|---|---|
| `.claude/agents/` | dentro do vault | em `~/.claude/agents/` |
| `.claude/skills/` | dentro do vault | em `~/.claude/skills/` |
| `.claude/tools/` (helpers + datasets) | dentro do vault | em `~/.notebooklm/tools/` |
| `.claude/corpora/` | dentro do vault | em `~/.notebooklm/<corpus>/` |
| `.claude/commands/` | dentro do vault | dentro do vault (sempre local) |
| `.claude/settings.json` | obrigatório | obrigatório |
| Caminho executável permitido | **só** `.claude/...` relativo | `~/`-based, cada um declarado |
| Sobrevive a `git clone` numa máquina nova | sim, sozinho | não, precisa da infra externa |

### 1.1 A regra que dá liga ao híbrido

**A classe é declarada na primeira seção de `REQUISITOS-EXTERNOS.md` e ecoada no cabeçalho do
`CLAUDE.md`. O vault tem de ser coerente com a própria declaração.**

A declaração usa um **marcador formal e greppável**, na primeira linha útil dos dois arquivos:

```
> **Classe A — autossuficiente.**
> **Classe B — leve.** Depende de `~/.claude/` e `~/.notebooklm/` (ver seções abaixo).
```

O marcador literal importa: prosa solta do tipo "este vault é autossuficiente para leitura" aparece
hoje em quase todos os `REQUISITOS-EXTERNOS.md` sem constituir declaração de classe, e um `grep`
por "autossuficiente" dá falso positivo em oito de oito. A auditoria procura `**Classe A` / `**Classe B`.

Daí decorrem dois deveres assimétricos:

- **Classe A não pode ter linha executável com caminho externo.** Caminho de fora é tolerado
  **apenas** como proveniência — campo `fontes`, prosa de origem, referência bibliográfica.
  Um `python ~/.notebooklm/tools/x.py` num vault Classe A é defeito, não conveniência.
- **Classe B tem de listar em `REQUISITOS-EXTERNOS.md` toda dependência externa que de fato usa.**
  Listar metade dos helpers que o próprio `CLAUDE.md` invoca é defeito: o arquivo existe justamente
  para ser a lista de reposição numa máquina nova.

Migrar de B para A é promoção legítima e esperada quando o vault amadurece. O caminho é: mover os
agentes e skills do domínio de `~/.claude/` para `<vault>/.claude/`, espelhar os corpora, criar
`settings.json` e trocar a declaração de classe.

### 1.2 O que fica no escopo global (`~/.claude`) em qualquer hipótese

Só o **transversal** — o que serve a mais de um domínio e não pertence a nenhum: helpers de código e
súmula genéricos, agentes de pesquisa jurisprudencial ampla, skills de formato (`docx-juridico-padrao`,
`pdf-ocr-to-markdown`), utilitários de sistema. Agente ou skill de um domínio só vive no global
enquanto o vault dono for Classe B — e, mesmo assim, **declarado** por esse vault.

---

## 2. Invariantes — valem para as duas classes

### 2.1 Raiz do vault

Quatro arquivos, sem exceção:

| Arquivo | Papel |
|---|---|
| `CLAUDE.md` | constituição do vault: escopo, pastas, convenções, fontes, limites |
| `index.md` | índice de navegação da raiz (Karpathy) |
| `MOC-<Vault>.md` | mapa de conteúdo curado |
| `REQUISITOS-EXTERNOS.md` | declaração de classe + dependências + checklist de restauração |

O MOC fica **na raiz**. Vault que guarde os MOCs em subpasta (`60-MOCs/`) ou que use um nome próprio
(`Mapa do Vault.md`) declara o desvio no `CLAUDE.md` — e não deixa um stub vazio na raiz fingindo
que o invariante foi cumprido.

`CLAUDE.md` **aponta** para `REQUISITOS-EXTERNOS.md` por wikilink; não duplica o conteúdo dele.
Duas fontes de verdade divergem — é questão de tempo.

### 2.2 Esquema de pastas

Canônico:

```
00-Inbox/          RAW   captura, processar semanalmente
10-Wiki/           WIKI  conhecimento atômico e permanente
  Conceitos/             CONC-
  Jurisprudencia/        JUR-
  Legislacao/            LEG-
  Teses/                 TESE-
20-Casos/          OUT   casos concretos (sem dado sensível)
30-Pecas/          OUT   modelos e peças
40-Recursos/       RAW   doutrina, corpora internos, material bruto
50-Checklist/      OUT   CK-
90-Arquivo/        RAW   bruto já destilado (criada sob demanda)
_Templates/              TEMPLATE-
```

**`90-Arquivo/` — o destino do bruto destilado.** Fixada em 2026-07-26. Depois que o item do
`00-Inbox/` vira nota atômica na `10-Wiki/`, o original desce para `90-Arquivo/` e nunca se apaga:
bruto é evidência, e a síntese que gerar dúvida se confere nele. É pasta **sob demanda** — só existe
onde há bruto arquivado, e por isso sua ausência não é lacuna (§2.2).

O arquivo não pode morar dentro do `00-Inbox/`. Enquanto morava (`00-Inbox/_processados/`, convenção
não declarada em três vaults), o Inbox do Criminal exibia 50 itens e contradizia de fora o próprio
invariante de que Inbox vazia é o estado saudável — captura pendente e evidência arquivada são
estados opostos e não cabem na mesma pasta.

> **Conflito com documentação publicada.** O e-book *O Segundo Cérebro Jurídico* ensina
> `_processados/` nos capítulos 3, 5 e 6 e nos apêndices A e B. Diferente do caso `TEMPLATE-Julgado`
> (§2.4), aqui a norma prevaleceu sobre o texto publicado: o defeito era estrutural, não de
> nomenclatura. O e-book ficou intacto e pende errata.

Desvio de domínio é **permitido e declarado** no `CLAUDE.md`. Um vault de psicologia clínica trocar
`20-Casos/30-Pecas` por `20-Clinica/30-Pesquisa` é adequação legítima; o que não pode é o desvio ser
silencioso.

**Pasta vazia é lacuna, não estrutura** — com uma exceção: **`00-Inbox/` vazia é o estado saudável**,
significa que a captura foi processada. É acúmulo ali que é sintoma, não vazio.

Fora o inbox, pasta sem nenhuma nota ou tem o vazio **declarado** no `CLAUDE.md` — dizendo por que
está reservada e o que a preencheria — ou é removida. Andaime esquecido polui o índice e mente sobre
o tamanho do vault; declarar custa uma linha e distingue "reservado" de "abandonado".

Cabe declarar como reservada, por exemplo, a `20-Casos/` de um vault cujo `CLAUDE.md` proíbe dado
sensível: o vazio ali é decisão, não descuido.

### 2.3 `index.md`

Um por pasta de conteúdo povoada, incluindo subpastas de `10-Wiki/`. Isentos: `_Templates/`,
`Anexos/`, artefatos gerados (`graphify-out/`, `_grafo/`) e pastas vazias.

O índice é regenerado sempre que uma nota é criada, editada ou movida na pasta. Contagem defasada
no índice de raiz é defeito objetivo — o `lint-vault` detecta por mtime.

### 2.4 Templates

Nomeados `TEMPLATE-<Tipo>.md`, na pasta de templates do vault — `_Templates/` no esquema canônico,
ou a pasta equivalente do esquema declarado (`99-Templates/` no Eleitoral). **O nome do arquivo é
invariante; a pasta segue o esquema declarado em §2.2.**

**Um template por pasta canônica de produção povoada** — a regra é essa, e dela sai o conjunto:

| Pasta | Template |
|---|---|
| `10-Wiki/Conceitos/` | `TEMPLATE-Conceito.md` |
| `10-Wiki/Jurisprudencia/` | `TEMPLATE-Julgado.md` |
| `10-Wiki/Legislacao/` | `TEMPLATE-Legislacao.md` |
| `10-Wiki/Teses/` | `TEMPLATE-Tese.md` |
| `20-Casos/` | `TEMPLATE-Caso.md` |
| `50-Checklist/` | `TEMPLATE-Checklist.md` |

Pasta vazia não exige template (mas pasta vazia é lacuna — §2.2). Subpasta própria de `10-Wiki/`
(`Autores/`, `Obras/`) exige o template correspondente: subpasta sem template produz notas sem
esquema, e é assim que um vault acaba com 15% das notas sem frontmatter.

**Decisão fixada:** `TEMPLATE-Julgado.md`. A pasta `Jurisprudencia/` nomeia a *coleção*; o template
nomeia o *tipo de nota*, e cada nota ali documenta um julgado (ou súmula, ou tema). Quatro vaults já
usavam `Julgado`, contra dois com `Jurisprudencia`, e o e-book *O Segundo Cérebro Jurídico* ensina
`TEMPLATE-Julgado` em dois capítulos — mudar o padrão criaria conflito com a documentação publicada.

> Correção de rota: a primeira versão desta norma fixou `TEMPLATE-Jurisprudencia`, por coerência com
> o nome da pasta. Estava errado — o argumento era estético e ignorava tanto a prática majoritária
> quanto o e-book. Revertido em 2026-07-26.

Nota de estado: em 2026-07-26 **nenhum dos oito vaults tinha o conjunto completo**, e havia dois
dialetos disjuntos. A regra "um por pasta povoada" existe para não voltar a divergir.

### 2.5 Nomes de nota

Notas de `10-Wiki/` levam prefixo de tipo: `CONC-`, `JUR-`, `LEG-`, `TESE-`. Checklists levam `CK-`.

O prefixo agrupa por tipo no explorador, torna o wikilink autoexplicativo e permite `grep` por
categoria. Nome em prosa dentro de `10-Wiki/` é desvio — sobretudo quando o `CLAUDE.md` do próprio
vault declara o prefixo e as notas não o seguem, que é incoerência interna, não convenção.

**Exceção declarada.** Um vault pode nomear pelo próprio instituto (`AIJE.md`) ou pelo autor
(`Carl Rogers.md`) em vez do prefixo, desde que (a) declare a convenção no `CLAUDE.md` e (b) o campo
`tipo` do frontmatter carregue o tipo em 100% das notas — é ele que passa a ser o marcador. O que a
norma não admite é o vault declarar o prefixo e não aplicá-lo.

Ao renomear nota já ligada, grave o nome antigo em `aliases` e reescreva os wikilinks na mesma
operação. O alias é a rede de segurança: link que escapar da reescrita continua resolvendo.

### 2.5.1 Ligação: link, âncora de seção e transclusão

Fixado em 2026-07-26. São três operações distintas e a escolha entre elas não é estilo:

| Forma | Sintaxe | Quando |
|---|---|---|
| Link | `[[CONC-Prisao-Preventiva]]` | remeter à nota inteira |
| Âncora de seção | `[[CONC-Prisao-Preventiva#Tese central]]` | remeter a **um trecho** de nota longa |
| Transclusão | `![[CONC-Prisao-Preventiva#Tese central]]` | **reusar** o trecho, exibindo-o aqui |

**A regra é: texto que precisa aparecer em dois lugares se transclui, não se copia.** Checklist que
repete a definição do conceito, MOC que reproduz o enunciado da tese, peça-modelo que recita a base
legal — tudo isso hoje é cópia, e cópia diverge do original em silêncio. A transclusão mantém um
único texto-fonte e o exibe onde for preciso; corrigido o original, corrige-se em todo lugar.

A âncora de seção resolve o problema irmão: nota longa recebe link genérico e o leitor (humano ou
agente) tem de varrer 1.000 palavras para achar o parágrafo que interessava. Para transcluir ou
ancorar é preciso que a nota de destino tenha `##` estáveis — o que é mais um motivo para os
títulos dos templates serem fixos.

Estado em 2026-07-26: das 1.562 notas dos oito vaults, **uma** usava transclusão e **uma** usava
âncora de seção. Não é preferência estabelecida contra o recurso; é recurso que nunca entrou na
norma nem nos templates, e por isso não foi usado. Os templates passam a trazer o gancho.

Duas cautelas:

- **Não transcluir camada RAW.** Trecho de `90-Arquivo/` ou `40-Recursos/` entra por citação com
  fonte e página (`## [p. N]`), não por `![[ ]]`: o bruto é evidência e deve ser citado como tal,
  com a origem visível ao lado.
- **Transclusão não substitui destilação.** Nota que é só um punhado de `![[ ]]` de outras notas
  não é nota atômica — é índice, e o lugar dela é o `index.md` ou o MOC.

### 2.5.2 Atomicidade — o que é nota longa demais

Fixado em 2026-07-26, depois de medir os nove vaults. **Extensão isolada não é defeito.** A
literatura de Zettelkasten fala em 80-100 palavras por nota; num vault jurídico isso é irreal — um
instituto exige base legal, posição dos tribunais, contraponto e ângulo de defesa, e nada disso cabe
em cem palavras. O que se audita não é o tamanho: é se a nota trata **uma coisa**.

Notas a partir de **900 palavras** entram em triagem e caem em quatro categorias. Só uma é defeito:

| Categoria | O que é | Conduta |
|---|---|---|
| **Catálogo** | coleção, índice, mapa mental, registry — longo por natureza | não fatiar |
| **Lei anotada** | um `##` por artigo do diploma | não fatiar: quebra a unidade da lei |
| **Densa** | uma linha argumentativa só, tratada a fundo | não fatiar; **ancorar** as seções |
| **Bloco inchado** | uma seção concentra ≥25% da nota e passa de 400 palavras | **extrair** |

O bloco inchado é o defeito real, e nestes vaults ele tem forma reconhecível: a nota de conceito
**engoliu um catálogo de jurisprudência**, ou a seção "Onde aprofundar" — que era para ser ponteiro —
virou conteúdo. O remédio não é picar a nota ao meio: é devolver o bloco à camada a que ele pertence
(`10-Wiki/Jurisprudencia/` para julgado, `index.md`/MOC para ponteiro) e **transcluir de volta** o
que ainda precisar aparecer ali (§2.5.1).

Duas consequências que a norma assume:

- **Fatiar por contagem de palavras é proibido.** Fragmento que não se sustenta sozinho não é nota
  atômica — é nota mutilada, e o vault fica pior. Se as partes não têm título próprio defensável, a
  nota é *densa*, não *inchada*.
- **O lint sinaliza, não condena.** A seção de notas longas do `lint-vault` classifica e sugere;
  a decisão de extrair é humana, caso a caso.

Medição de 2026-07-26, para calibrar expectativa: 69 notas passavam de 900 palavras nos nove vaults;
**38 delas não eram defeito** (catálogo, lei anotada ou densa).

### 2.5.3 Identificação de caso — numeração CNJ

Fixado em 2026-07-27. **Todo caso que seja processo judicial é identificado pelo número único CNJ**
(Resolução CNJ 65/2008), no formato `NNNNNNN-DD.AAAA.J.TR.OOOO`, em **todos** os vaults.

O número CNJ é o identificador; o rótulo humano vive no `titulo` e nos `aliases`.

| Onde | Forma |
|---|---|
| Nome da pasta/nota em `20-Casos/` | `0839168-12.2026.8.10.0001` — só o número |
| Frontmatter | `cnj: "0839168-12.2026.8.10.0001"` — obrigatório em `tipo: caso` |
| Rótulo legível | `titulo:` e `aliases: ["Op. Inauditus", "núcleo PM — VECCO"]` |
| Autos conexos | `cnj_relacionados: ["0814474-76.2026.8.10.0001", …]` |

Código interno (`2026-VECCO-001`, `Caso-03`) **não** identifica caso. Ele parece organizado e não é:
não casa com o PJe, não casa com a peça protocolada, não casa com a intimação, e obriga a manter de
cabeça uma tabela de-para que ninguém mantém. O número CNJ já é o identificador que o tribunal, o
DJEN, o DataJud e o cliente usam — o vault passa a usar o mesmo.

**Caso ainda sem número CNJ.** Inquérito, PIC, procedimento administrativo e cautelar não distribuída
não têm número único. Aí:

```yaml
cnj: sem-numero
identificador: "IP 7685/2026-SENARC"   # o número que o órgão de origem de fato usa
```

A pasta fica com o nome provisório até a distribuição. **Distribuído, renomeia-se para o CNJ** e o
nome antigo vai para `aliases` — é a mesma regra de renomeação do §2.5, e o alias é o que impede o
wikilink antigo de quebrar.

**Conflito com a regra de sigilo — resolvido aqui.** Quatro `CLAUDE.md` diziam "nunca número de
processo identificável em `20-Casos/`". Essa cláusula fica **revogada** nesta parte, e o motivo é
que ela misturava duas coisas:

- o **número dos autos** é dado público de identificação processual (é o que se digita na consulta
  do tribunal) — fica no vault, sempre;
- a **identificação das partes** (nome completo, CPF, endereço, matrícula prisional, nome de criança
  ou adolescente) continua fora: iniciais e função, como já era.

A cautela real não é sobre gravar o número: é sobre **o que sai do vault**. Antes de mandar caso a
serviço externo (NotebookLM, Perplexity) ou para terceiro, conferir segredo de justiça e anonimizar —
regra que já existia e continua valendo integralmente.

**Onde a regra não incide.** Vault cujo "caso" não é processo judicial — grupo vulnerável na
`20-Grupos/` do Dissertacao, nota de processo clínico na `20-Clinica/Casos/` do Psicologia — não tem
número CNJ para usar. O desvio é legítimo e **declarado no `CLAUDE.md`**, com o identificador que o
substitui. O que a norma não admite é vault jurídico inventar código próprio para processo que tem
número.

O `lint-vault` detecta (nota `tipo: caso` sem `cnj`, `cnj` malformado, pasta de caso com nome que
não é CNJ nem tem `sem-numero` declarado).

### 2.5.4 Anonimização — vale para a camada OUTPUTS inteira

Fixado em 2026-07-27. A regra de anonimização das partes **não para em `20-Casos/`**: alcança
também a camada de saída — `30-Pecas/`, `50-Outputs/` e equivalentes do esquema declarado.

O motivo é que a separação anterior não se sustentava. Anonimizar a ficha do caso e deixar o nome
completo e o CPF do cliente na minuta guardada ao lado protege exatamente nada: as duas notas vivem
no mesmo vault, sincronizam para a mesma nuvem e entram no mesmo `graphify`, no mesmo backup e no
mesmo `notebooklm source add` distraído.

| Camada | O que fica gravado |
|---|---|
| `10-Wiki/` | não há parte — é conhecimento |
| `20-Casos/` | **iniciais + função** (`S.F.P.`, `A.P.G.J. — Desembargador`) |
| `30-Pecas/` · `50-Outputs/` | **iniciais + marcador de preenchimento** no lugar da qualificação |
| `40-Recursos/` · `90-Arquivo/` · `Anexos/` | **texto fiel** — é evidência, não se reescreve |

**A minuta não perde utilidade: ganha um campo a preencher.** No lugar da qualificação vai o
marcador, que também serve de lembrete de conferir a qualificação na fonte certa (os autos), e não
na memória de quem redigiu:

```
**Representado:** S.F.P. — [QUALIFICAÇÃO COMPLETA: preencher no protocolo, conforme os autos]
```

Quem exporta preenche na hora de protocolar. O que a norma proíbe é **guardar** a qualificação na
camada curada, não usá-la na peça que vai ao juízo.

**RAW continua fiel.** Extrato de PJe, laudo, acórdão e transcrição ficam com os nomes que têm — é
evidência, e evidência adulterada não serve para conferir síntese nenhuma. A consequência prática é
que o bruto com nome **não pode morar em pasta de OUTPUTS**: seu lugar é `90-Arquivo/` (§2.2).

**Autoridade não é parte.** Juiz, promotor, delegado e perito que atuam de ofício seguem nomeados —
identificá-los é descrever ato público do processo, não expor dado de cliente.

O `lint-vault` detecta CPF e CNPJ na camada curada — é o sinal mecanicamente verificável de que uma
qualificação escapou. Nome completo ele não detecta, e por isso o marcador é convenção de escrita,
não achado de auditoria.

### 2.6 Frontmatter — esquema em português

**Obrigatório:**

```yaml
---
titulo: Nome legível da nota
tipo: conceito | jurisprudencia | legislacao | tese | caso | checklist
area: <domínio do vault>
tags: [<area>/<subtema>, <tipo>]
status: rascunho | processado | verificar | arquivado
criado: AAAA-MM-DD
fontes:
  - Fonte 1 (com URL ou id de notebook quando houver)
---
```

**Obrigatório em `tipo: caso`:** `cnj` — número único CNJ ou `sem-numero` + `identificador` (§2.5.3).

**Opcional:** `atualizado`, `subtema`, `aliases`, `related`, `cnj_relacionados`.

#### Dois eixos de classificação, e só um carregador para cada

Fixado em 2026-07-26. A nota é classificada por **assunto** e por **estado**, e os dois eixos são
independentes e obrigatórios:

| Eixo | Pergunta | Carregador | Forma |
|---|---|---|---|
| Assunto | *do que trata?* | `tags` | `<area>/<subtema>` + `<tipo>` |
| Estado | *em que pé está?* | `status` | vocabulário fechado abaixo |

O eixo de estado entrou porque tag de tópico não ajuda na hora de produzir: para achar o que falta
terminar, o que ainda não foi conferido e o que já pode ser citado em peça, é o estado que se
consulta, não o assunto. O eixo de assunto ficou porque é ele que sustenta MOC, índice e navegação.

**Cada eixo tem um único carregador.** Estado não vira também tag `status/x`: duas fontes de verdade
divergem, e a norma já rejeita isso em §2.1. Com o Dataview instalado nos oito, `WHERE status = "x"`
resolve a consulta que a tag resolveria, e ainda entra em tabela de índice.

**Vocabulário fechado de `status`:**

| Valor | Significado |
|---|---|
| `rascunho` | capturado, ainda não destilado nem conectado |
| `processado` | destilado, com frontmatter completo e ligado ao MOC |
| `verificar` | tem `[VERIFICAR]` pendente — **não citar em peça antes de conferir** |
| `arquivado` | superado por norma nova ou virada de jurisprudência; fica pelo histórico |

Valor fora dessa lista é defeito. Comentário inline no valor (`status: rascunho  # rascunho | …`)
também é defeito: o comentário pertence ao template, não à nota preenchida.

`verificar` não é decorativo. O risco de citação inventada tem sanção real, e é esse valor que
distingue a nota que pode ir para uma peça da que ainda depende do `verificador-citacoes`.

Regras:

- **Tags hierárquicas** `<area>/<subtema>` (`familia/guarda`, `criminal/prova`). Rolam para o pai na
  contagem do Obsidian e evitam o achatamento de centenas de tags planas.
- **O `<tipo>` da lista de tags é plano de propósito** — `conceito`, `jurisprudencia`, `tese`. Não é
  achatamento e não deve ser reportado como defeito. Auditoria que conte tag plana sem descontar o
  `<tipo>` produz falso positivo em massa: no inventário de 2026-07-26, as sete tags planas mais
  frequentes dos oito vaults eram todas o `<tipo>` prescrito aqui.
- `subtema` literal na lista de tags é **resíduo de template**, não tag. O `lint-vault` caça.
- `tipo` reflete a **natureza da nota**, não a da fonte. Nota conceitual que cita um julgado é
  `tipo: conceito`, não `tipo: jurisprudencia`.
- `fontes` é onde caminho externo e id de NotebookLM são legítimos, em qualquer classe de vault.
- Nota sem frontmatter não é nota — é rascunho no `00-Inbox/`.

#### O que não é nota, e por isso não exige frontmatter

O esquema acima governa **nota**. Não governa:

- **Camada RAW convertida** — o que vive em `90-Arquivo/`, `40-Recursos/` e `Anexos/` é fonte, não
  nota: PDF virado Markdown, protocolo oficial, texto de lei paginado em `## [p. N]`. Exigir
  `titulo`/`tipo`/`tags` de um POP da perícia é inventar metadado sobre documento de terceiro. A
  proveniência dessas conversões mora no `index.md` da pasta, que é onde se procura.
- **Arquivos de infraestrutura da raiz** — `CLAUDE.md`, `REQUISITOS-EXTERNOS.md`, `LEIA-ME.md`.
- **`index.md` e MOC**, que têm esquema próprio e mínimo: `type: index` e `updated: AAAA-MM-DD`.
  Esse esquema é obrigatório — `index.md` sem ele é defeito, e é a lacuna real que a auditoria de
  2026-07-26 encontrou (12 índices e 1 MOC).

### 2.7 Política de caminhos

**Zero caminho absoluto `C:\Users\...` em qualquer arquivo do vault.** Sem exceção de classe.

| Contexto | Forma correta |
|---|---|
| Dentro do vault | relativo: `.claude/tools/x.py`, `10-Wiki/Conceitos/...` |
| Infra externa (só Classe B) | `~/`-based: `~/.notebooklm/tools/x.py` |
| Outro vault | wikilink ou nome do vault em prosa — nunca caminho de disco |
| **Saída gerada** (minuta, CSV, relatório) | **`prazos/`** — nunca `/tmp/`, nunca `20-Casos/` |

**A pasta de saída é `prazos/`. Fixado em 2026-07-26.** Vale nas duas classes. Até então o Ambiental
gravava em `20-Casos/<CODIGO>/` e os demais em `prazos/`, e a divergência sozinha respondia por 7 das
31 colisões de agente entre vaults Classe A (`PADRAO-VAULT-TRIAGEM-COLISOES.md`).

`20-Casos/` **não** serve de pasta de saída: a §2.2 a define como conteúdo curado **sem dado
sensível**, e minuta gerada carrega dado do caso. São coisas distintas — `20-Casos/<CODIGO>/` é a
nota do caso, `prazos/` é o rascunho gerado. Slash command que **cria** a pasta do caso segue usando
`20-Casos/<CODIGO>/`: ali o caminho é o destino legítimo, não convenção de saída.

Caminho absoluto quebra em máquina nova, quebra quando o vault muda de lugar (os oito já migraram
de `C:\Users\alden\<Nome>` para o OneDrive) e quebra quando aponta para vault desativado.

Único uso tolerado: a **linha de detecção** dentro do próprio `/health-check`, que precisa citar o
padrão que caça.

### Como se declara um recurso externo — por nome

Vault Classe A pode citar recurso externo **desde que ele esteja listado pelo nome** na seção de
declaração do seu `REQUISITOS-EXTERNOS.md` (a que registra o que ficou fora, com o substituto local
de cada item). A auditoria é um confronto de duas listas:

- recurso **citado** em `CLAUDE.md`/`.claude/` e **não declarado** → defeito;
- recurso **declarado** e não mais citado → declaração a revisar (ou foi internalizado e a linha deve
  sair, ou nunca foi usado e vale como registro do que ficou fora).

Não contam como dependência: `PADRAO-VAULT.md` (ponteiro desta norma), `FONTES-CANONICAS.md`
(catálogo da máquina) e a convenção de gravar saída em `prazos/`.

> **Marca inline foi abandonada.** Até 2026-07-26, Ambiental e Constitucional exigiam anotar cada
> citação externa com `[externo]` ou `[corpus externo opcional]` no próprio texto. A prática caiu por
> dois motivos concretos: a marca chegou a ser inserida **dentro de linha de comando**, quebrando o
> copiar-colar, e um `grep` que procurasse só uma das duas formas produzia falso positivo. Declaração
> por nome, em lugar único, é verificável por diferença de listas — a marca espalhada não era.

### 2.8 `settings.json`

`settings.json` é o portátil e é **obrigatório** nas duas classes — acompanha a cópia do vault e
carrega as permissões que o vault precisa para funcionar. `settings.local.json` é só para o que é
específico da máquina.

Ter apenas `settings.local.json` significa que o vault não funciona ao ser copiado: as permissões
ficaram para trás.

Coerência mínima: se o vault tem `skills/lint-vault/`, o `settings.json` permite executá-lo.

### 2.9 Auditoria — `/health-check` + `lint-vault`

Todo vault tem os dois:

- **`.claude/commands/health-check.md`** — auditor de conformidade estrutural, parametrizado com as
  contagens esperadas daquele vault (canários de infraestrutura, caminho externo na camada
  executável, dívida `[VERIFICAR]`, rascunho antigo, dado sensível em `20-Casos/`). Relata primeiro,
  corrige só depois de confirmação humana.
- **`lint-vault`** — higiene das notas (wikilinks quebrados, `index.md` ausente ou defasado, notas
  órfãs, resíduo de template, cobertura do MOC, e os dois eixos do §2.6). Classe A o carrega como
  skill própria; Classe B usa a global.
- **`verificar-fila`** — trabalha a dívida de conferência que o eixo `status` torna visível, em ciclo
  gerar-avaliar-reparar: lista as notas em `verificar`, confere cada citação pelo agente
  `verificador-citacoes`, repara **só** o trecho reprovado e libera a nota apenas com dívida zerada.

**Invariante do §2.6 que o lint checa e a fila trabalha:** nota com `[VERIFICAR]` no corpo tem
`status: verificar`, e nota em `verificar` tem marcador no corpo. Nota marcada `processado` com
dívida pendente é a incoerência mais cara do vault — parece pronta para citar em peça e não está.

O que a norma **não** admite é esvaziar a fila apagando marcador sem conferência: isso converte
dívida visível em risco invisível, e é pior do que não rodar nada. Citação que não se confirma
continua marcada, e o que se registra é a busca feita — onde, quando, com que resultado.

Referência de implementação: `Ambiental/.claude/commands/health-check.md` e
`Ambiental/.claude/skills/lint-vault/scripts/lint_vault.py`.

### 2.10 Artefatos gerados

`graphify-out/`, `_grafo/`, `00-Grafo/`, caches e builds são **regeneráveis** e carregam caminhos da
máquina de origem. Declarados como tal em `REQUISITOS-EXTERNOS.md` e cobertos por `.graphifyignore`.
Não entram na contagem de notas do vault nem exigem `index.md`.

---

## 3. Modelos de referência

| Classe | Exemplar | Por quê |
|---|---|---|
| **A** | `Ambiental` | 24 agentes, 6 skills, 62 helpers/datasets, 3 corpora, `settings.json` próprio, `/health-check` calibrado. Gêmeo de `Constitucional` no `settings.json` e no esqueleto do `CLAUDE.md`. |
| **B** | `ProcessoCivil` | `CLAUDE.md` enxuto (~123 linhas), cobertura de `index.md` completa, `REQUISITOS-EXTERNOS.md` fiel ao que usa, `settings.json` e declaração de classe presentes (ver `PADRAO-VAULT-DIAGNOSTICO.md` §8-9). |

Ao criar vault novo, copiar a estrutura do exemplar da classe pretendida e rodar o checklist da §4
antes da primeira nota.

---

## 4. Checklist de conformidade

Mecânico e verificável. Serve para auditar vault existente e para dar por pronto um vault novo.

**Declaração**
- [ ] `REQUISITOS-EXTERNOS.md` traz o marcador `**Classe A` ou `**Classe B` na primeira seção
- [ ] `CLAUDE.md` ecoa o mesmo marcador no cabeçalho e aponta para `REQUISITOS-EXTERNOS.md` por wikilink
- [ ] `CLAUDE.md` não duplica o conteúdo do `REQUISITOS-EXTERNOS.md`

**Raiz e estrutura**
- [ ] Existem `CLAUDE.md`, `index.md`, `MOC-<Vault>.md`, `REQUISITOS-EXTERNOS.md`
- [ ] MOC na raiz é real (não stub); desvio de local declarado no `CLAUDE.md`
- [ ] Esquema de pastas canônico, ou desvio declarado no `CLAUDE.md`
- [ ] Nenhuma pasta vazia sem propósito declarado
- [ ] `index.md` em toda pasta de conteúdo povoada
- [ ] Contagem do `index.md` da raiz bate com o disco

**Convenções de nota**
- [ ] `_Templates/` com um `TEMPLATE-<Tipo>.md` por pasta canônica de produção povoada
- [ ] Template para toda subpasta própria de `10-Wiki/`
- [ ] Notas de `10-Wiki/` com prefixo `CONC-`/`JUR-`/`LEG-`/`TESE-`
- [ ] Frontmatter com as sete chaves obrigatórias em português (inclui `status`)
- [ ] `status` dentro do vocabulário fechado, sem comentário inline no valor
- [ ] Tags hierárquicas `<area>/<subtema>` — descontando o `<tipo>`, que é plano por norma
- [ ] Nenhum `subtema` literal na lista de tags (resíduo de template)
- [ ] `tipo` reflete a natureza da nota, não a da fonte
- [ ] Caso judicial nomeado e identificado pelo número CNJ; `cnj` no frontmatter (§2.5.3)
- [ ] Caso sem CNJ traz `cnj: sem-numero` + `identificador` do órgão de origem
- [ ] Partes por iniciais em `20-Casos/` **e** na camada de saída (`30-Pecas/`, `50-Outputs/`) — §2.5.4
- [ ] Nenhum CPF/CNPJ na camada curada; qualificação substituída por marcador de preenchimento
- [ ] Bruto com nome de parte mora em `90-Arquivo/`, nunca em pasta de OUTPUTS
- [ ] `index.md` e MOC com `type: index` + `updated:`
- [ ] RAW (`90-Arquivo/`, `40-Recursos/`, `Anexos/`) e infra da raiz **não** cobrados de frontmatter
- [ ] Texto repetido em duas notas está transcluído (`![[nota#seção]]`), não copiado

**Infraestrutura**
- [ ] `.claude/settings.json` existe
- [ ] `settings.local.json` só com o que é da máquina
- [ ] `settings.json` permite executar o que o vault carrega (lint, helpers)
- [ ] Classe A: `agents/`, `skills/`, `tools/`, `corpora/` dentro do vault
- [ ] Classe B: toda dependência externa usada está listada em `REQUISITOS-EXTERNOS.md`

**Caminhos**
- [ ] Zero `C:\Users\...` (exceto a linha de detecção do `/health-check`)
- [ ] Classe A: nenhuma linha executável com caminho externo
- [ ] Nenhum caminho apontando para vault desativado ou local pré-migração

**Auditoria**
- [ ] `.claude/commands/health-check.md` presente e com contagens calibradas
- [ ] `lint-vault` acessível (skill própria em A, global em B)
- [ ] Artefatos gerados declarados como regeneráveis e cobertos por `.graphifyignore`

---

## 6. Blocos-padrão de CLAUDE.md — texto canônico para copiar

Fixado em 2026-08-01. Alguns trechos de `CLAUDE.md` se repetem, quase byte a byte, em vários vaults —
não por acaso: é a mesma regra de máquina (porta do Local REST API, convenção de `index.md`) ou a
mesma preferência de estilo de trabalho, válida em qualquer domínio. Sem uma fonte única, a cópia
diverge em silêncio — já aconteceu: o vault Eleitoral perdeu o bullet de *fallback* silencioso que os
outros quatro com o mesmo bloco têm, e ganhou em troca um bullet redundante de idioma.

**A regra:** o texto abaixo é o canônico. Vault que carrega um destes blocos **copia o texto**
integralmente no próprio `CLAUDE.md` — não usa `@import` nem wikilink para fora, isso quebraria a
portabilidade de Classe A — e cita a proveniência numa linha curta logo abaixo do título da seção,
ex.: `*Bloco-padrão — texto canônico em \`PADRAO-VAULT.md\` §6A; mudar a regra lá primeiro.*`. Ao
alterar a regra, edita-se **aqui primeiro**, depois se propaga às cópias listadas em cada bloco. É o
mesmo princípio já usado para agentes e skills copiados entre vaults ("cópias resincronizáveis,
editar o global não afeta o vault") — aplicado a mais um tipo de artefato: o texto de regra em prosa.

### §6A — Estilo de trabalho e preferências de saída

```
## Estilo de trabalho e preferências de saída

- **Comandos curtos = execute.** "Sim", "Acrescente X", "Crie Y" são ordens — execute sem pedir confirmação nem listar o plano antes.
- **Sem preâmbulo.** Não descreva o que vai fazer antes de fazer. Faça e resuma no final.
- **Resumo final conciso.** Ao terminar tarefa com múltiplos arquivos, entregue uma tabela compacta do que foi criado ou alterado — nada mais.
- **Criação em paralelo.** Ao criar múltiplas notas independentes, escreva todas em paralelo.
- **Fallback silencioso.** Se um recurso opcional falhar (<recursos opcionais do vault>), siga pelo local sem narrar a falha em três parágrafos — uma linha basta.
- **Sem emojis** salvo pedido explícito.
```

O parêntese do bullet de *fallback* nomeia os recursos opcionais do próprio vault (ex.: "Perplexity,
NotebookLM" ou, no Trabalhista, "Perplexity, Jusbrasil") — é a única variação permitida. Em uso:
Ambiental, Constitucional, Criminal, Eleitoral, Trabalhista.

### §6B — Aviso: não usar `obsidian_*` em vault sem porta própria

```
> **NÃO use os tools `obsidian_*` neste vault.** O plugin Local REST API está instalado aqui e a API
> escuta em `127.0.0.1:27124` **sem identificar o vault** — se outro cofre estiver com o plugin
> ligado, a escrita cai nele, **sem erro nenhum**. Na configuração atual da máquina o MCP global
> alcança o vault Eleitoral; escrever por MCP daqui é escrever no vault errado em silêncio.
```

Vale para vault cujo `CLAUDE.md` **não** ativa deliberadamente os `obsidian_*` — o Eleitoral é a
exceção declarada, e carrega o canário de porta próprio em vez deste aviso (§2, item "TRAVA DE VAULT
ÚNICO" do seu `CLAUDE.md`). Em uso: Ambiental, Constitucional, Criminal, Dissertacao, ExecucaoPenal,
Familia, ProcessoCivil, Psicologia.

### §6C — Índices de navegação (index.md)

```
## Índices de navegação (index.md)

- Cada pasta de conteúdo tem um `index.md`: uma linha por nota (`[[nota]] — gancho`) e links para os índices das subpastas.
- REGRA DE LEITURA: antes de abrir notas de uma pasta, consulte o `index.md` dela e escolha só os arquivos necessários (economia de contexto e tokens).
- REGRA DE ESCRITA: ao criar, renomear, mover ou excluir nota, atualize o `index.md` da pasta na mesma operação.
- `.claude/`, `Anexos/` e pastas geradas por pipeline não têm índice e não devem ser editadas manualmente.
```

Em uso: Ambiental, Constitucional, Criminal, Eleitoral, ExecucaoPenal, Familia, ProcessoCivil,
Psicologia, Trabalhista. **Não usado** em Dissertacao, MestradoCeuma e JuntaMedica — vaults de
projeto ou pessoal com regra de índice mais enxuta ou ausente; não é defeito por si, mas fica
registrado como ponto de checagem em `PADRAO-VAULT-DIAGNOSTICO.md` §14.

### §6D — Fontes canônicas e slash commands (infra compartilhada)

Duas variantes, conforme a classe — não são o mesmo bloco, mas resolvem o mesmo problema, que é
apontar para `~/.notebooklm/FONTES-CANONICAS.md` sem duplicar o catálogo da máquina:

- **Variante Classe A** — `.claude/tools/` do próprio vault é a fonte canônica; o manual da máquina
  entra só como conferência cruzada opcional. Em uso: Ambiental, Constitucional, Criminal, Eleitoral.
- **Variante Classe B** — `~/.notebooklm/FONTES-CANONICAS.md` é a fonte direta, sem canônico local
  equivalente. Em uso: ExecucaoPenal, Familia, ProcessoCivil, Trabalhista.

Ambas citam o manual gerado por `python ~/.notebooklm/tools/gerar_fontes_canonicas.py` — fonte nova é
rodar o gerador, nunca editar o catálogo à mão. Por variar por vault no texto (nome dos próprios
helpers), esta seção **não** exige cópia byte-idêntica como §6A-C — só a citação da proveniência do
padrão, quando presente.

## 7. O que a norma deliberadamente não uniformiza

- **Tamanho.** Um vault de 39 notas e um de 1.265 são igualmente conformes.
- **Vocabulário de domínio.** `area`, `subtema` e o conjunto de tags são de cada vault.
- **Profundidade do `CLAUDE.md`.** 73 linhas ou 462, conforme a complexidade do domínio — desde que
  não duplique o `REQUISITOS-EXTERNOS.md`.
- **Corpora.** Quais acervos espelhar é decisão de custo-benefício por vault, registrada no
  `REQUISITOS-EXTERNOS.md` com o que ficou de fora e por quê.
