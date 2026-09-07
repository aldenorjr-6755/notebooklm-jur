# Especificação técnica e arquitetural — inteligência jurídica híbrida para advocacia criminal

> Preenchimento da especificação-base (Karpathy + CODE) com escolhas concretas, aferidas contra o
> hardware e a infraestrutura que **já existem** nesta máquina em 2026-09-07. Onde a base dizia
> "indique três opções", as três estão indicadas e uma é a recomendada. Onde a base trazia regra
> cível (CPC 319, 322-329, prazo em dias úteis), a regra foi trocada pela penal.
>
> Norma dos vaults: `~/.notebooklm/PADRAO-VAULT.md`. Manual da infra: `~/.notebooklm/FONTES-CANONICAS.md`.

---

## 0. O que foi apurado antes de especificar

### 0.1 Hardware (aferido)

| Item | Valor | Consequência arquitetural |
|---|---|---|
| CPU | Intel Core 7 150U, 10 núcleos / 12 threads, série U (baixo consumo) | inferência local é **CPU-only** e lenta |
| GPU | Intel Graphics integrada (sem CUDA, sem NPU) | nada de AWQ/vLLM; GGUF em CPU, iGPU só experimental |
| RAM | 32 GB | cabe modelo de 7-14B em Q4; 24B cabe mas roda a ~2 tok/s |
| Disco | ~157 GB livres em C: | espaço para 3-4 modelos GGUF + índices |

**Medido em 2026-09-07** (Ollama, API `/api/generate`, temperatura 0, `num_ctx` 8k, CPU; registro
completo em `Criminal/40-Recursos/benchmark-llm-local.md`):

| Modelo | Geração | Ingestão de prompt | Prompt de 2k tokens | Autos deste caso (733 págs ≈ 368k tokens) |
|---|---|---|---|---|
| qwen3:8b (Q4_K_M, 5,2 GB) | 5,5 tok/s (3,5 com contexto cheio) | **13-14 tok/s** | 147 s | ~7,3 h só de ingestão |
| phi4-mini (2,5 GB) | 11,5 tok/s | 23 tok/s | ~90 s (estim.) | ~4,4 h |
| bge-m3 (embedding, 1024d) | 2 textos em 5,4 s com carga; ~20-40 chunks/s em regime | | | minutos |
| bge-reranker-v2-m3 (venv `.venv-rag314`, torch CPU) | 2 pares em 1,1 s | | | reordenar 40 candidatos ≈ 20 s |

A ingestão de prompt ficou **3 a 4 vezes abaixo** da estimativa inicial (40-60 tok/s): esta CPU
série U não tem AVX-512 nem largura de memória para mais. Os dois modelos também **erraram o
art. 155 do CP** (qwen3 disse "corrupção passiva", phi4-mini disse "estupro"): modelo local não
carrega conhecimento jurídico confiável e só pode ser usado para extração estrutural sobre texto
que lhe foi entregue, nunca como fonte.

Conclusão que governa tudo abaixo: **o LLM local serve a tarefas curtas por ato processual de até
~2-4k tokens (classificar, extrair campos, tabelar), com saída JSON validada**. Atos grandes
(anexos, laudos, procedimentos administrativos) e toda leitura cross-document vão para nuvem, com
o texto anonimizado antes de sair da máquina. A divisão exata por faixa de tamanho está na §3.3.

### 0.2 Infraestrutura já existente (não reconstruir)

| Camada da espec | O que já existe | Onde |
|---|---|---|
| Segundo cérebro | 14 vaults Obsidian no padrão CODE/Karpathy; o **Criminal** é Classe A (72 agentes, 134 skills, 26 helpers, 14 corpora) | `~/OneDrive/0-Obsidian/Criminal/` |
| Capture (PDF→MD) | `pdf_para_markdown.py`, app `pdf2md` com perfil PJe e Tesseract `por` embutido, `doc_para_markdown.py`, `html_para_markdown.py`, `ocrmypdf` no PATH | `~/.notebooklm/` |
| Capture (áudio) | `transcrever.py` (faster-whisper) + `diarizar.py` (pyannote em CPU, RTF ~1,1x) | `~/.notebooklm/` |
| Fontes primárias | CF, CP, CPP, LEP, CPC, CC, CTN, EAOAB, leis especiais em JSON por artigo; súmulas STF/STJ/vinculantes; Temas de RG; informativos STF/STJ/TSE; RSTJ, RTJ; boletins de precedentes; 10 colunas ConJur/Migalhas | `~/.notebooklm/tools/*.json`, `~/.notebooklm/<corpus>/` |
| Entrada de autos | MCP PJe TJMA (autos por CNJ + OCR), DataJud, DJEN (API oficial, tarefa diária), Jusbrasil CLI, PDPJ | `~/.notebooklm/mcp_pje/`, `datajud/`, `djen_monitor/`, `jusbrasil/`, `pdpj/` |
| Grafo | graphify (god nodes, comunidades) já rodado no vault Criminal | `Criminal/graphify-out/` |
| Inferência local | Ollama com `qwen3:8b`, `phi4-mini` e `bge-m3` baixados em 2026-09-07; reranker `bge-reranker-v2-m3` no venv `.venv-rag314` (Python 3.14 do python.org, porque o Smart App Control bloqueia o Python do `uv`) | `%LOCALAPPDATA%\Programs\Ollama`, `~/.notebooklm/.venv-rag314` |
| Inferência remota | Claude Code (este ambiente); proxy `fcc` → DeepSeek V4 Pro (porta 8082, token expirado hoje); NotebookLM via CLI `nlm` | memória `fcc-deepseek-proxy`, `notebooklm-mcp-cli-*` |
| Anti-alucinação | agente `verificador-citacoes` (read-only, contexto isolado); skill `/verificar-fila`; lint de CPF/CNPJ | `~/.claude/agents/`, vault |
| Exportação | `gerar_docx_juridico.py` + skill `docx-juridico-padrao` (Sitka) | vault Criminal `.claude/tools/` |

O que **falta** (e é o objeto desta espec): índice híbrido esparso+denso, modelo local puxado,
fatiador por ato processual, distiladores determinísticos por caso, e os dois validadores de saída.

### 0.3 A extensão "MinutaIA Conecta" (o "ConectaIA")

O "Conecta" do rodapé do MinutaIA é a extensão Chrome **MinutaIA Conecta v3.0.22**
(ID `kimheklbcampgaeojcniknnhlmgfddac`, Chrome Web Store). Ela não estava instalada no perfil
padrão do Chrome desta máquina; o pacote foi lido em 2026-09-07 a partir do `.zip` em `Downloads`,
sem executar nada. Achados:

| Aspecto | O que a extensão faz | Consequência para esta espec |
|---|---|---|
| Alcance | injeta chat e botão "Exportar MinutaIA" em 279 hosts: PJe (inclusive `pje.tjma.jus.br` e `pje2.tjma.jus.br`), eproc, e-SAJ, Projudi, SEI, SEEU, STF, STJ, TRTs | cobre o mesmo PJe que o MCP PJe local já cobre |
| Leitura do PJe | capa (número, classe, polos e representação), grid de documentos com paginação, download de cada documento e do PDF único dos autos, usando a sessão logada do advogado | seletores e endpoints reaproveitados em §3.1.3 e em `~/.notebooklm/tools/pje_seletores_conecta.json` |
| Destino dos dados | PDFs guardados em pedaços no storage da extensão e entregues a `app.minutaia.com.br`; chat via `pjeia-backend.vercel.app/api/completions` (modelo padrão "modelplus"); upload por URL pré-assinada para Cloudflare R2 / Google Cloud Storage; host S3 em `sa-east-1` | **os autos saem da máquina** para Vercel, Cloudflare/GCS e AWS: incompatível com a regra de sigilo da §6 sem registro de tratamento e aceite |
| Autenticação | JWT do MinutaIA ou Google OAuth (só e-mail e perfil); multi-tenant (PGE-RS, defensorias, MPs, escritórios com marca própria) | nada a integrar |
| Permissões | `scripting`, `tabs`, `storage`, `unlimitedStorage`, `downloads`, `identity`, `declarativeNetRequest` (declarada, sem regras no pacote) e `optional_host_permissions: *://*/*` | a permissão opcional para todos os sites, se concedida, deixa a extensão ler qualquer página; manter negada |
| Código | build ofuscado (Vite/React), sem captura de teclado, senha ou exfiltração fora dos hosts declarados | risco residual baixo, mas é caixa-preta de terceiro |

Decisão: a extensão **não entra** na arquitetura. O que ela faz no PJe o MCP PJe do TJMA já faz
localmente (autos por CNJ, OCR, expedientes). Ela fica como referência de produto: o fluxo "capa
→ lista de documentos → download por ID → PDF único" e os seletores do PJe 2.9.7.0 (mesma versão
nos dois graus do TJMA, sondada em 2026-09-04/05) foram transcritos para o fatiador da fase 3.
Se for mantida instalada para uso do SaaS, registrar em `40-Recursos/registro-tratamento.md`
(§6) que autos passam por Jusbrasil/Vercel/Cloudflare/AWS.

---

## 1. Mapa dos serviços das duas telas para componentes locais

Jus IA e MinutaIA são SaaS: os autos sobem para a nuvem da Jusbrasil. A solução local replica os
serviços e ganha no que os SaaS não oferecem: sigilo por padrão, rastreabilidade de cada citação
até a folha/ID, versionamento em git e independência de fornecedor.

### 1.1 Tela Jus IA

| Serviço no SaaS | Fase CODE | Componente local (existente ou a construir) |
|---|---|---|
| Importar processo / Novo caso | Capture | `/pje <CNJ>` (autos + OCR) → `20-Casos/<CNJ>/raw/`; skill `/novo-caso` cria a pasta do template; DataJud para metadados |
| Analise os autos desse processo | Capture + Distill | fatiador por ato (§3.1) → distiladores (§3.3) → `index.md` + `cronologia.md`; agentes `analise-denuncia`, `analise-super-firac`, `auditoria-nulidades-criminal`, `mapa-nulidades`, `cotejo-depoimentos` |
| Me ajude a construir uma peça | Express | redatores por peça (`defesa-criminal-resposta-acusacao`, `alegacoes-finais-criminal`, `habeas-corpus`, `apelacao-criminal`, `pedido-liberdade-criminal`, execução penal 104-107) + validadores (§4) + `docx-juridico-padrao` |
| Mapeie teses relevantes para o caso | Organize | busca híbrida (§3.2) sobre fontes + subgrafo de `[[conceitos]]`; agentes `jurisprudencia-corpus`, `informativos-stj`, `boletim-precedentes-stj`, `tese-repetitiva`, `criminal-player`, `justo-processo` |
| Estudar viabilidade de um caso | Distill | `triagem-novo-caso` + `analise-probatoria-standards` + `advogado-do-diabo` (modo demolição) + calculadora de prescrição (§3.3) |
| Mapear teses contrárias a essa decisão | Distill | `analise-recursal-firac` + `advogado-do-diabo` (modo rebater) + `embargos-declaracao-criminal` + `cabimento-recursal-criminal` |
| Elaborar um parecer jurídico | Express | `parecer-juridico` sobre contexto injetado, com os dois validadores |
| Minuta / análise de contrato | Express | `minuta-contrato-servicos` (contrato de honorários criminal), `revisao-clausula`, `comparacao-contratos` |
| Busque informações em documentos | Organize | consulta híbrida com filtro por caso (`cnj`) e por tipo de ato; resposta sempre com `ID/fls.` |

### 1.2 Tela MinutaIA

| Serviço no SaaS | Componente local |
|---|---|
| Documentos com OCR ligado | `pdf2md` perfil PJe (PyMuPDF + Tesseract `por`); exit 3 = página sem texto → OCR obrigatório |
| Modelos: Flexível / Rigoroso / Molde | três estratégias de prompt sobre `30-Pecas/_modelos/` (§3.4.2): Molde = template com placeholders (`engenheiro-template-juridico`); Rigoroso = estrutura travada + estilo few-shot; Flexível = só referência de estilo |
| Legislação | `consultar_codigo.py --fonte cp|cpp|lep|...` (texto literal por artigo, offline) |
| Referências | corpora de jurisprudência (informativos, boletins, RSTJ/RTJ, clone STF·STJ·TRF1) |
| Biblioteca / Bibliotecários | corpora do vault / subagentes de acervo (`informativos-stj`, `rstj-stj`, `rtj-stf`, `corte-idh-brasil`, colunas ConJur) |
| Chat × Minuta | modo conversa (retrieval + resposta curta) × modo peça (Etapas A/B/C, §3.4) |
| Instantâneo × Planejado | single-turn × multi-turn com plano aprovado antes da redação (Planejado é o padrão para peça) |
| Rápido (seletor de modelo) | tier de modelo (§5.3): local / nuvem barata / nuvem forte |
| Habilidades (`#`) | as 134 skills do vault Criminal (slash) |
| Processamento em Lote | `pipeline.py --lote` sobre `20-Casos/*/raw/` (só Capture+Organize+Distill; Express nunca em lote) |
| "Sem contexto" (alerta) | gate de grounding: se o retrieval devolve zero chunks, a peça não é gerada; o sistema responde "sem base documental" |

---

## 2. Estrutura canônica do segundo cérebro

Decisão: **não criar `segundo-cerebro/` novo**. O vault Criminal já implementa a árvore da espec
com nomes diferentes e está sob norma (`PADRAO-VAULT.md`). Criar árvore paralela quebraria a regra
de fonte única e os 91 índices existentes. A tabela abaixo é o mapeamento oficial.

### 2.1 Mapeamento árvore da espec → vault Criminal

| Árvore da espec | Vault Criminal | Observação |
|---|---|---|
| `00_Inbox/` | `00-Inbox/` | capturas brutas; watcher PDF→MD desativado em 2026-08-03, reativável |
| `01_Fontes/Legislacao/` | `.claude/tools/*_artigos.json` + `10-Wiki/Legislacao/` | JSON é a fonte; a nota Wiki é a leitura anotada |
| `01_Fontes/Jurisprudencia/` | `.claude/corpora/` + `10-Wiki/Jurisprudencia/` | corpora = raw; nota = destilado com frontmatter §2.3 |
| `01_Fontes/Doutrina/` | `.claude/corpora/<coluna>/` + `10-Wiki/Doutrina/` | fichamentos com `fontes:` obrigatório |
| `01_Fontes/Modelos_Base/` | `30-Pecas/_modelos/` (criar) | peças autorais anonimizadas com teses consolidadas |
| `02_Processos/<CNJ>/` | `20-Casos/<CNJ>/` | §2.5.3 da norma: nº CNJ nomeia a pasta |
| `03_Conceitos/` | `10-Wiki/Conceitos/` | notas atômicas com `[[wikilinks]]`; MOC-Criminal.md é o hub |
| `04_Saidas/` | `50-Outputs/` (hoje `30-Pecas/`) | anonimização alcança esta pasta (§2.5.4 da norma) |

### 2.2 Pasta de caso (`20-Casos/<CNJ>/`)

```
20-Casos/0801524-21.2024.8.10.0093/
├── raw/                    # PDFs originais (PJe, IP, mídias) — nunca editados
│   ├── autos_2026-09-01.pdf
│   └── audiencia_2026-08-20.mp3
├── extracted/
│   ├── autos_2026-09-01.md         # saída do pdf2md, paginada ## [p. N]
│   ├── atos/                       # fatiado por ato (§3.1) — um .md por ato
│   │   ├── 0001_DENUNCIA_ID123456_p003-011.md
│   │   ├── 0002_RECEBIMENTO-DENUNCIA_ID123501_p012.md
│   │   └── ...
│   ├── atos.jsonl                  # índice dos atos: id, tipo, fls, data_juntada, hash
│   └── audiencia_2026-08-20.md     # transcrição diarizada [hh:mm:ss] Falante:
├── distill/
│   ├── prazos.md                   # tabela de prazos (CPP 798, dias corridos)
│   ├── controversia.md             # imputação × teses de defesa
│   ├── nulidades.md                # mapa de nulidades com fls.
│   ├── prisao.md                   # cautelares: datas, fundamentos, excesso de prazo
│   ├── prescricao.md               # CP 109-119, marcos interruptivos
│   └── jurisprudencia-filtrada.md  # saída do filtro de relevância
├── index.md                        # ficha analítica (partes, imputação, fase, riscos, próximos atos)
├── cronologia.md                   # linha do tempo fática estrita, cada linha com fls./ID
└── pecas/                          # minutas geradas (rascunho → revisão → protocolada)
    └── 2026-09_resposta-acusacao_v1.md
```

Regra de anonimização (norma §2.5.4): `raw/` e `extracted/` ficam com nomes reais e **nunca**
saem da máquina; tudo que vai para modelo em nuvem passa por `anonimizar.py` (§5.4).

**Decisão da fase 9 (2026-09-07):** como `20-Casos/` vive no OneDrive, a árvore acima com texto
integral fica na **área de trabalho local** `%LOCALAPPDATA%\cerebro\casos\<CNJ>\` (ao lado dos
bancos `casos.db`/`casos.lance`), e em `20-Casos/<CNJ>/` entram só a `ficha.md` (iniciais, como
manda o template do vault) e as saídas **pseudonimizadas** (`linha-do-tempo.md`, `controversia.md`,
`prazos.md`, `prescricao.md`). Os comandos `/analisar-autos` e `/minutar` do vault Criminal
implementam essa divisão.

### 2.3 Frontmatter de nota de jurisprudência criminal

```yaml
---
tipo: jurisprudencia
orgao: STJ
orgao_julgador: 6ª Turma
classe: HC
numero: 598.051/SP
relator: Min. Rogerio Schietti Cruz
data_julgamento: 2021-03-02
ramo_direito: Processo Penal
tema:
  - busca_domiciliar
  - consentimento_do_morador
  - prova_ilicita
dispositivos:
  - CF art. 5º XI
  - CPP art. 157
  - CPP art. 240 §1º
tags: [cautelar_probatoria, nulidade, onus_da_prova]
links:
  - "[[Inviolabilidade de Domicílio]]"
  - "[[Consentimento do Morador — Ônus da Prova]]"
  - "[[Prova Ilícita por Derivação]]"
status_validade: vigente          # vigente | superado | em_revisao
status_verificacao: verificada    # verificada | verificar | divergente  (saída do verificador-citacoes)
fonte_local: "[VERIFICAR: Informativo STJ de março/2021 — apontar arquivo em .claude/corpora/informativos_stj/]"
fonte_oficial: https://scon.stj.jus.br/
---
### Tese firmada
O ingresso em domicílio sem mandado exige consentimento livre, voluntário e comprovado, cujo ônus
de demonstração recai sobre o Estado; a mera ausência de objeção do morador não basta.

### Contexto de aplicação
Flagrante em residência por tráfico sem mandado e sem fundadas razões documentadas antes do
ingresso. Distinguishing: situação de flagrância visível de fora (STF, RE 603.616, Tema 280).

### Uso defensivo
Preliminar de nulidade da prova (CPP 157) em resposta à acusação, memoriais e HC; pedido de
desentranhamento e absolvição por insuficiência probatória residual.
```

Dois campos não existiam na espec-base e são obrigatórios aqui: `status_verificacao` (alimentado
pelo `verificador-citacoes`, gate anti-alucinação) e `fonte_local` (o validador de fontes, §4,
só aprova citação que tenha um arquivo local por trás).

### 2.4 Frontmatter do ato processual fatiado (`extracted/atos/*.md`)

```yaml
---
tipo: ato_processual
cnj: 0801524-21.2024.8.10.0093
ato_seq: 1
ato_tipo: DENUNCIA               # vocabulário fechado, §3.1.2
id_pje: 123456                   # "Num. 123456" do PJe
fls_ini: 3
fls_fim: 11
data_juntada: 2024-05-14
autor_do_ato: Ministério Público
hash_sha256: 9f2c...             # do texto extraído; muda → reindexa
origem_arquivo: raw/autos_2026-09-01.pdf
ocr: false                       # true se a página veio do Tesseract
---
```

---

## 3. Pipeline CODE

### 3.1 Fase 1 — Capture

#### 3.1.1 Componentes de parsing e OCR

| Opção | Tipo | Quando usar | Custo de sigilo |
|---|---|---|---|
| **PyMuPDF + Tesseract `por`** via `pdf2md` perfil PJe (**recomendado, já existe**) | local | todo autos do PJe; mede perda (`--check`), pagina `## [p. N]`, exit 3 avisa página-imagem | nenhum |
| **OCRmyPDF** (instalado) | local | gerar PDF pesquisável para juntar aos autos ou reler no leitor; camada OCR sobre digitalizado ruim (`--deskew --clean`) | nenhum |
| **Docling** (IBM) ou **marker-pdf** | local | laudos com tabelas (balística, contábil, extração de celular) onde a tabela precisa virar Markdown estruturado; pesado (torch CPU), rodar só nesses arquivos | nenhum |
| Google Document AI | online | lote grande de IP digitalizado torto, se e só se anonimizado ou público | dados saem da máquina |
| Azure AI Document Intelligence | online | idem, com região Brasil-Sul (residência de dados) | idem |
| Mistral OCR (`mistral-ocr-latest`) | online | melhor custo por página para PDF-imagem; sem residência BR | idem |

Regra: **OCR de autos é local**. Online só para material público (jurisprudência, doutrina) ou
anonimizado. Alternativa local de reserva para tabela: PaddleOCR PP-StructureV3.

Áudio de audiência: `transcrever.py` (faster-whisper) + `diarizar.py` (pyannote, CPU). Saída no
formato `[hh:mm:ss] Falante:`; entra em `extracted/` como ato do tipo `TERMO-AUDIENCIA-MIDIA`.

#### 3.1.2 Fatiamento estrutural por ato processual (`fatiar_atos.py`, a construir)

Proibido: janela de N tokens com sobreposição. Obrigatório: um chunk = um ato. O fatiador opera
sobre o `.md` paginado e usa três camadas de delimitação, na ordem:

1. **Marcador de sistema do PJe**: rodapé `Num. <id> - Pág. <n>` e linha `Assinado eletronicamente por ... em dd/mm/aaaa`. O `id` muda → novo ato. Esta é a fronteira primária e cobre a grande maioria dos autos do TJMA.
2. **Cabeçalho tipológico** (regex, maiúsculas, início de página ou após linha em branco), vocabulário fechado:

   | Classe | Marcadores |
   |---|---|
   | Investigação | `AUTO DE PRISÃO EM FLAGRANTE`, `PORTARIA`, `BOLETIM DE OCORRÊNCIA`, `TERMO DE DECLARAÇÕES`, `TERMO DE INTERROGATÓRIO`, `AUTO DE EXIBIÇÃO E APREENSÃO`, `AUTO DE RECONHECIMENTO`, `RELATÓRIO FINAL`, `REPRESENTAÇÃO` |
   | Perícia | `LAUDO`, `LAUDO PERICIAL`, `EXAME DE CORPO DE DELITO`, `LAUDO DE CONSTATAÇÃO`, `LAUDO TOXICOLÓGICO`, `EXAME NECROSCÓPICO` |
   | Acusação | `DENÚNCIA`, `ADITAMENTO À DENÚNCIA`, `QUEIXA-CRIME`, `ALEGAÇÕES FINAIS`, `CONTRARRAZÕES`, `PARECER` (MP em 2º grau) |
   | Defesa | `RESPOSTA À ACUSAÇÃO`, `DEFESA PRÉVIA`, `MEMORIAIS`, `RAZÕES DE APELAÇÃO`, `HABEAS CORPUS`, `PEDIDO DE LIBERDADE`, `PEDIDO DE REVOGAÇÃO` |
   | Juízo | `DECISÃO`, `DESPACHO`, `SENTENÇA`, `ACÓRDÃO`, `PRONÚNCIA`, `RECEBIMENTO DA DENÚNCIA`, `AUDIÊNCIA DE CUSTÓDIA`, `TERMO DE AUDIÊNCIA`, `ATA DE AUDIÊNCIA` |
   | Cartório | `CERTIDÃO`, `CERTIDÃO DE PUBLICAÇÃO`, `CERTIDÃO DE TRÂNSITO EM JULGADO`, `MANDADO`, `OFÍCIO`, `CARTA PRECATÓRIA`, `GUIA DE EXECUÇÃO`, `ATESTADO DE PENA` |

3. **Fallback**: se um `Num.` do PJe contém mais de um cabeçalho tipológico (juntada agrupada), fatia pelo cabeçalho e herda o `id_pje`; se não há cabeçalho nem `Num.` (IP físico digitalizado), fatia por página e marca `ato_tipo: INDETERMINADO` para revisão manual (ou classificação pelo LLM local, §5.1, com o rótulo gravado como `ato_tipo_inferido`).

Cada chunk grava o frontmatter da §2.4 e uma linha em `atos.jsonl`. A `data_juntada` vem da linha
de assinatura ou, na falta, do `Num.` (ordem monotônica) com `data_juntada: null`. Nunca inferir
data por LLM: campo vazio é melhor que campo inventado.

Validação de perda (regra canônica): antes de fatiar, comparar páginas e caracteres do PDF com o
`.md`; página com < 20 caracteres → OCR; `.md` com < 60% dos caracteres esperados → não prossegue.

#### 3.1.3 Seletores e endpoints do PJe do TJMA (reaproveitados da extensão MinutaIA Conecta)

Fonte: leitura estática de `NewChatLogic.js`, `dados.js.js` e `pje-init.js.js` da extensão
(§0.3). Arquivo canônico, consumido pelo `fatiar_atos.py` e pelo MCP PJe:
`~/.notebooklm/tools/pje_seletores_conecta.json`. O TJMA cai no método que a extensão chama de
**pje4** (PJe 2.9.7.0 nos dois graus). Grau: caminho começa com `/pje2g/` → 2º grau; `/pje/` → 1º.

**Capa do processo** (`listProcessoCompletoAdvogado.seam?id=…&ca=…`):

| Campo | Seletor |
|---|---|
| Número CNJ | `.titulo-topo-desktop`, primeiro token com `-` e `.` e ≥ 20 caracteres |
| Classe | `dt` com texto `Classe judicial` → `dd` seguinte |
| Polo ativo / representação | `#poloAtivo tbody td span` / `#poloAtivo .tree li small span` |
| Polo passivo / representação | `#poloPassivo tbody td span` / `#poloPassivo .tree li small span` |

**Grid da aba Documentos** (é a lista que alimenta `atos.jsonl` quando o PDF único não traz o `Num.`):

| Elemento | Seletor / regra |
|---|---|
| Abrir aba | `a#navbar\:linkAbaDocumentos` (click, esperar ~2 s) |
| Corpo e linhas | `#processoDocumentoGridList\:tb` / `… tr` |
| ID do documento | `td:first-child div span` |
| Metadado da linha | `td:nth-child(7) div` (conferir cabeçalho no TJMA) |
| Links | `td:last-child a[href]`; ignorar se `onclick` tem `alert(` ou `title` tem `indisponível` |
| Prioridade do link | 3 = `nomeArqProcDocBin` no href ou `target` começando com `idpdf` (PDF binário); 2 = ícone `fa-external-link`; 1 = `visualizarExpediente.seam` / `documentoHTML.seam` / ícone `fa-file-text-o` (HTML) |
| Nome do binário | regex `nomeArqProcDocBin=([^&]+)`, urldecode |
| Paginação | `input.rich-inslider-field-right` (setar `value` + `change`); total em `.rich-inslider-right-num`; detectar troca comparando `innerHTML` e o ID da 1ª/última linha |

**Endpoints** (`{base}` = `https://pje.tjma.jus.br/pje` ou `https://pje2.tjma.jus.br/pje2g`):

| Recurso | Rota |
|---|---|
| PDF único dos autos | `POST {base}/Processo/ConsultaProcesso/Detalhe/listProcessoCompletoAdvogado.seam` com `AJAXREQUEST=_viewRoot`, `detalheDocumento:downloadPJeDocs`, `javax.faces.ViewState` da página; resposta traz `window.open('<url>')` |
| Documento individual (legacy) | `{base}/seam/resource/rest/pje-legacy/documento/download/{idDoc}[?download=true]` |
| Documento individual (comum-api) | `{base}/seam/resource/rest/pje-comum-api/api/processos/id/{idProc}/documentos/id/{idDoc}/download?incluirCapa=false&grau={g}&incluirAssinatura=true` |
| Conteúdo HTML do documento | mesma rota com `/conteudo` no lugar de `/download` |
| Lista de documentos em JSON | `{base}/seam/resource/rest/pje-comum-api/api/processos/id/{idProc}/documentos?grau={g}` |
| Página de autos digitais | `{base}/Processo/ConsultaProcesso/Detalhe/listAutosDigitais.seam?idProcesso={idProc}&aba=documentos&origem=pje2web` |

O que o MCP PJe local já cobre: `listProcessoCompletoAdvogado.seam`, âncoras `divTimeLine:*` e
`documento/download/{id}`. O que falta trazer: o grid paginado (fonte redundante de IDs, tipo
e data para conferir o `atos.jsonl`), a rota JSON `pje-comum-api/.../documentos` (sondada no
TJMA em 2026-09-04/05, ver `mcp_pje/COMPARACAO-pje-ia.md`) e a detecção de tipo por magic
number (`%PDF`, PNG, JPEG) antes de decidir entre PDF, imagem e HTML. Seletores de DOM envelhecem
a cada atualização do PJe: cada campo do JSON deve ser sondado ao vivo antes de virar dependência.

### 3.2 Fase 2 — Organize (indexação híbrida)

#### 3.2.1 Via esparsa (literal: números de processo, artigos, IDs, nomes)

| Opção | Tipo | Avaliação para este ambiente |
|---|---|---|
| **SQLite FTS5** (**recomendado**) | local | zero dependência (vem no Python), tokenizer `unicode61 remove_diacritics 2` acha `Art. 3º-A` e `Súmula 7`; um arquivo por vault, versionável; consulta em ms |
| Meilisearch | local | binário único para Windows, tolerante a erro de digitação, boa UI; segundo processo a manter vivo |
| Tantivy (via LanceDB) ou `bm25s` | local | BM25 puro; o LanceDB já traz FTS Tantivy embutido, então vem junto com a via densa |
| Elastic Cloud / OpenSearch | online | excesso para um escritório; útil só se houver equipe e dezenas de milhares de atos |
| Typesense Cloud | online | simples, barato; mesmo problema: autos saem da máquina |
| Azure AI Search | online | híbrido nativo BM25+vetor; residência BR; só para os corpora públicos |

Decisão: **SQLite FTS5 para os autos (sigilo) + FTS do LanceDB para os corpora públicos**. Os
dois expõem a mesma função `buscar_literal(consulta, cnj=None, ato_tipo=None)`.

#### 3.2.2 Via densa (semântica)

Embedding: **`bge-m3`** via Ollama (`ollama pull bge-m3`, 1024 dims, 8k tokens, multilíngue com
português forte). **Medido em 2026-09-07: ~0,3 chunk/s em CPU** com chunks de uma página (~1,7k
chars), ou seja, ~35 min para indexar um processo de 750 páginas. É custo único por caso e roda em
lote noturno; a consulta embute só a pergunta (< 1 s). Alternativa: `nomic-embed-text` (mais leve,
inglês-centrado, pior em PT-BR). Não usar embedding online para autos.

| Armazenamento | Tipo | Avaliação |
|---|---|---|
| **LanceDB** (**recomendado**) | local, embutido | arquivo em disco, sem servidor, `pip install lancedb`; busca vetorial + FTS + híbrida com reranker na mesma chamada; filtros por metadado (`cnj`, `ato_tipo`); funciona em Windows |
| Qdrant (binário Windows) | local, servidor | melhor filtragem e payload; exige processo rodando; sem Docker aqui (não instalado) |
| SQLite + `sqlite-vec` | local, embutido | mantém tudo num único `.db` com o FTS5; extensão ainda jovem, sem HNSW (busca exata, ok até ~200k vetores) |
| Qdrant Cloud | online | free tier 1 GB; só para corpora públicos |
| Pinecone serverless | online | idem; sem residência BR |
| Weaviate Cloud | online | híbrido nativo; idem |

Regra de privacidade: **dois bancos**. `vault.lance` (corpora públicos: legislação, jurisprudência,
doutrina, modelos anonimizados) e `casos.lance` (atos processuais). O segundo nunca é sincronizado
para nuvem; o OneDrive **não** deve conter `casos.lance` (colocar em `%LOCALAPPDATA%\cerebro\`).

#### 3.2.3 Reranker

A espec-base indicava `bge-reranker-large`, que é **chinês/inglês** e degrada em português.
Trocar por **`bge-reranker-v2-m3`** (multilíngue, mesmo lineage do bge-m3), rodando em CPU via
`FlagEmbedding` ou `sentence-transformers` no venv 3.12 do `uv` (o mesmo em que o torch CPU já
funciona para a diarização). Custo: ~50-100 ms por par em CPU; reordenar 40 candidatos → ~3 s.
Online, só para corpora públicos: Cohere Rerank 3.5 (multilíngue), Jina Reranker v2 multilingual,
Voyage `rerank-2`.

**Medido em 2026-09-07:** o reranker custa ~1 s por par nesta CPU (1.000 chars, 256 tokens;
mais threads não ajudam), mais 9 s de carga por processo. Com 15 candidatos por via (~25 pares)
a consulta fica em 35-40 s; a fusão simples por posição (RRF), sem reranker, responde em 1,5 s e
devolveu o mesmo top-2 nas consultas de teste. Regra: **interativo = RRF; Express (minuta) =
reranker obrigatório**, porque ali a ordem decide o que entra no prompt. Alternativa mais leve
testada e **descartada** em 2026-09-07: `Alibaba-NLP/gte-multilingual-reranker-base` (306M) carrega
código próprio (`new-impl`) que quebra nos índices de posição com o transformers atual em CPU
(`IndexError ... size 256`). Candidatos ainda não testados: `jinaai/jina-reranker-v2-base-multilingual`,
`mixedbread-ai/mxbai-rerank-base-v2`; ou quantizar o v2-m3 em ONNX int8.

Fluxo de recuperação (`tools/buscar.py`): FTS5 (top 15) ∪ vetorial (top 15) → dedup por início
normalizado do texto (a denúncia copiada em cada carta precatória vira uma linha "mesmo texto
também em") → reranker ou RRF → top 8 → prompt, cada chunk prefixado com
`[ID <id_pje> | <vol> p. <n> | <ato_tipo> | <data>]`. Esse prefixo é o que o validador de fontes
(§4) confere depois. Saída `--json` para o pipeline.

#### 3.2.4 Grafo de contexto

Duas fontes, sem novo banco: (a) `[[wikilinks]]` + frontmatter das notas de `10-Wiki/` (lidos por
`grafo_wiki.py`, a construir, que devolve o subgrafo a N saltos de um conceito); (b) `graphify-out/`
já existente (comunidades e god nodes) para sugerir conceitos vizinhos não linkados. Uso no
pipeline: dado `distill/controversia.md`, extrair os conceitos citados, expandir 2 saltos e injetar
as notas do subgrafo como contexto de teses antes do retrieval semântico.

### 3.3 Fase 3 — Distill

Tarefas determinísticas. As que dependem só de regex e datas rodam **sem LLM**. As que exigem leitura
rodam no **LLM local, τ = 0.0, uma chamada por ato** (cabe na janela e no tempo), com saída JSON
validada por schema. Cross-document (síntese de todos os atos) vai para nuvem, anonimizado.

| Distilador | Motor | Entrada | Saída | Regra penal que substitui a cível da espec-base |
|---|---|---|---|---|
| `prazos.md` | script puro (`contagem_prazo_cpp.py`) | `atos.jsonl` (intimações, publicações, certidões) | tabela: ato, dies a quo, prazo, dies ad quem, fundamento | **CPP 798**: dias corridos, contínuos e peremptórios; exclui o dia do começo (§1º); Súm. 310 STF (sexta → segunda); Súm. 710 STF (intimação pessoal); calendário TJMA local (ex.: ponto facultativo 10-11/08/2026 registrado na memória) |
| `controversia.md` | LLM local por ato + síntese em nuvem | denúncia, resposta, memoriais | matriz imputação (fato, tipo, qualificadora, majorante) × tese defensiva (preliminar, mérito, dosimetria) × prova indicada com fls. | substitui "exordial × contestação" |
| `nulidades.md` | **inventário descritivo** por LLM local (o que o ato decide, motivos invocados, requerimentos da defesa apreciados e resultado, datas) + varredura de vícios **só pelo agente** `auditoria-nulidades-criminal` (nuvem) | decisões, despachos, atas | inventário; depois: vício, ato, fls., natureza, momento de arguição, prejuízo | CPP 563-573, 157, 158-A a F. Testado em 2026-09-07: pedir ao 8B local que "aponte vícios" fez o modelo copiar os exemplos do prompt ("Intimem-se" virou prova de "ausência de intimação"); a detecção saiu do distilador local |
| `prisao.md` | script + LLM local | APF, custódia, decisões cautelares | datas, fundamento de cada decisão, dias preso, reavaliação CPP 316 p.u. (90 dias), pedidos pendentes | — |
| `prescricao.md` | script puro (`prescricao_cp.py`) | denúncia (pena máxima), marcos interruptivos (`atos.jsonl`) | PPP abstrata e retroativa, CP 109-119, com cada marco e sua fls. | — |
| `dosimetria.md` (pós-sentença) | LLM local sobre a sentença | sentença | tabela por fase: circunstância, fração, fundamento, fls.; sinaliza bis in idem e fundamentação genérica | — |
| `jurisprudencia-filtrada.md` | retrieval híbrido + reranker + LLM em nuvem | `controversia.md` + `nulidades.md` | para cada tese: 3-5 precedentes do acervo local com `fonte_local`, marcados `status_verificacao` | substitui "confronto com 01_Fontes" |
| `cronologia.md` | script (ordena `atos.jsonl`) + LLM local para fatos internos ao ato | todos os atos | linha do tempo com uma linha por evento e fls. | — |

Regra de ouro do Distill: **nenhuma linha sem `fls.`/`ID`**. Linha sem âncora é descartada pelo
validador antes de chegar ao Express.

**Roteamento por tamanho do ato** (decorrência do benchmark da §0.1; medido no caso de teste,
110 atos, mediana de 460 tokens, p90 de 5,8k, máximo de 56k):

| Faixa do ato | Motor | Por quê |
|---|---|---|
| até 2k tokens (a maioria dos despachos, decisões, certidões, termos) | LLM local (qwen3:8b; phi4-mini para classificação) | ~2,5 min por ato no pior caso; lote noturno cobre o processo inteiro |
| 2k a 8k tokens | LLM local só se houver folga; senão nuvem barata | 8k tokens = 10 min só de ingestão |
| acima de 8k (anexos, laudos, procedimentos administrativos, IP) | nuvem barata, anonimizado | um anexo de 56k tokens levaria mais de 1 h local |
| síntese cross-document (`controversia`, `jurisprudencia-filtrada`, `cronologia` final) | nuvem forte | precisa ver todos os atos de uma vez |

Nunca pedir ao modelo local conhecimento jurídico (o que diz um artigo, qual a pena): ele erra e
não sabe que erra. Todo dispositivo entra no prompt pelo texto literal de `consultar_codigo.py`.

**Custo da saída, medido em 2026-09-07:** a geração (~3 tok/s com contexto cheio) pesa mais que a
leitura. A denúncia de 1,4k tokens com JSON de 900 tokens levou 316 s. Por isso os schemas do
`distilar_atos.py` são curtos (trecho literal de até 15 palavras, listas de até 8 itens,
`num_predict` 700) e a saída estruturada usa o `format` do Ollama, que impõe o schema no decode.
Cada `trecho` é conferido contra o texto do ato (`localizado`): o que não for encontrado fica
marcado no relatório, nunca apagado.

### 3.4 Fase 4 — Express (minutagem em camadas)

#### 3.4.1 Etapas

| Etapa | Fonte exclusiva | Modelo | Controle |
|---|---|---|---|
| **A — Fatos** | `cronologia.md` + chunks dos atos citados | nuvem (Sonnet-classe), τ 0.2 | cada frase factual com `(ID/fls.)`; frase sem âncora é devolvida |
| **B — Fundamentação** | `controversia.md`, `nulidades.md`, `jurisprudencia-filtrada.md`, notas de `10-Wiki/` do subgrafo, artigos via `consultar_codigo.py` | nuvem (Sonnet/Opus-classe), τ 0.3 | subsunção fato (fls.) → norma (artigo literal injetado) → precedente (`fonte_local`); citação sem `fonte_local` é proibida no prompt |
| **C — Pedidos** | Etapa B aprovada | nuvem, τ 0.1 | conformidade ao rito **penal**: CPP 41 (denúncia) / 396-A (resposta) / 403 §3º (memoriais) / 593 (apelação) / 647-667 (HC) / LEP 197; cada pedido deve corresponder a uma tese da Etapa B (validador processual, §4) |
| **D — Formato** | Etapa C | script | `gerar_docx_juridico.py` (Sitka, padrão tipográfico); resumo executivo quando a peça for ao STJ (skill `resumo-stj-343a`, que não incide no criminal até ato próprio) |

Modo **Planejado** (padrão para peça): o sistema apresenta o plano (teses ordenadas por força,
precedentes escolhidos, pedidos) e só redige após aprovação. Modo **Instantâneo**: só para chat
e consultas curtas, nunca para peça.

#### 3.4.2 Modelos: Molde / Rigoroso / Flexível

| Modo | O que entra no prompt | Quem produz |
|---|---|---|
| Molde | template com texto fixo + placeholders entre crases; o modelo só preenche | `engenheiro-template-juridico` → `engenheiro-prompt-minuta-juridica` |
| Rigoroso | estrutura de títulos travada + 1-2 peças-modelo anonimizadas como few-shot de estilo | redator da peça com `30-Pecas/_modelos/` |
| Flexível | só diretrizes de estilo (voz ativa, plain language, Legal Design) | redator + `peca-legal-design` |

---

## 4. Verificação de alucinação (strict grounding)

```
[Prompt com contexto RAG] → [LLM] → minuta.md
        │
        ├── validador_fontes.py  (sintático)
        │     regex de citações: REsp/AREsp/HC/RHC/AgRg n. X, Súmula (Vinculante) N,
        │     Tema N (RG/repetitivo), Informativo N, art. N (CP/CPP/LEP/CF/lei), fls. N, ID N
        │     → cada uma precisa existir em (a) contexto injetado OU (b) fonte canônica local
        │       (sumulas_stj.json, sumulas_stf.json, cp_artigos.json, cpp_artigos.json,
        │        temas_rg, informativos, atos.jsonl do caso)
        │     → ausente: insere [VERIFICAÇÃO NECESSÁRIA: citação não localizada na base documental]
        │     → artigo citado com texto divergente do JSON: [VERIFICAÇÃO NECESSÁRIA: redação do art. N difere da fonte]
        │
        ├── validador_processual.py  (estrutural)
        │     → cada pedido da seção "Pedidos" referencia ≥ 1 tese da fundamentação
        │     → cada nulidade alegada tem pedido correspondente (desentranhamento/anulação)
        │     → tempestividade: prazo de prazos.md × data de hoje
        │     → peça ao STJ/STF: prequestionamento presente para cada dispositivo do REsp/RE
        │     → rito: pedidos incompatíveis com a peça (ex.: honorários em HC) → alerta
        │
        └── verificador-citacoes (agente, semântico, contexto isolado)
              → confere se a tese atribuída ao precedente é a que ele de fato firmou
              → grava status_verificacao na nota de jurisprudência
        ↓
Status: APROVADO | ALERTA (n itens) → só APROVADO vai para o .docx
```

Detalhes que a espec-base não previa e o histórico deste ambiente exige:

- **Erro de camada** (memória `citacao-jurisprudencial-conferir-no-corpus`): citante ≠ citado; monocrática ≠ Turma. O validador semântico deve confrontar o órgão julgador do frontmatter com o que a minuta afirma.
- **Ausência não prova inexistência** (memória `informativo-nao-esgota-o-acordao`): "não localizada na base" gera alerta para conferência humana, nunca exclusão automática do trecho.
- **Ordinal corrompido** em RSTJ pré-2008 (`5º` → `52`): citação de artigo cuja `fonte_local` seja RSTJ < 2008 recebe alerta automático para conferência no PDF oficial.
- O marcador `[VERIFICAÇÃO NECESSÁRIA]` é greppável e entra na fila do `/verificar-fila`.

---

## 5. Matriz de componentes

| Camada | Recomendado | Alternativas locais | Alternativas online | Justificativa |
|---|---|---|---|---|
| Parsing & OCR | PyMuPDF + Tesseract `por` (`pdf2md`, existe) | OCRmyPDF (existe); Docling / marker-pdf para tabelas de laudo | Google Document AI; Azure Document Intelligence (BR-Sul); Mistral OCR | autos nunca saem; mede perda; online só para público/anonimizado |
| Índice esparso | SQLite FTS5 (autos) + Tantivy do LanceDB (corpora) | Meilisearch; `bm25s` | Elastic Cloud; Typesense Cloud; Azure AI Search | exatidão alfanumérica sem servidor |
| Embedding | `bge-m3` via Ollama | `nomic-embed-text`; `multilingual-e5-large` | OpenAI `text-embedding-3-large`; Voyage `voyage-3`; Cohere `embed-v4` | PT-BR forte, 8k tokens, CPU |
| Banco vetorial | LanceDB embutido (dois bancos: vault / casos) | Qdrant binário; SQLite + `sqlite-vec` | Qdrant Cloud; Pinecone; Weaviate Cloud | sem servidor, híbrido nativo, filtros por metadado |
| Reranker | `bge-reranker-v2-m3` (CPU, venv uv 3.12) | `mxbai-rerank-large-v2` | Cohere Rerank 3.5; Jina Reranker v2; Voyage rerank-2 | multilíngue; o `-large` da espec-base é zh/en |
| Inferência local | Ollama (instalado) com Qwen3-8B Q4_K_M | llama.cpp SYCL/Vulkan para a iGPU (ganho marginal); Phi-4-mini para velocidade; Gemma 3 12B para qualidade | — | §0.1: só tarefas por ato, τ = 0 |
| LLM em nuvem | OpenRouter com allowlist de provedores ZDR; Claude Code para orquestração | proxy `fcc` → DeepSeek V4 Pro (existe) | ver §5.3 | anonimizado antes de sair; escolha por tier |
| Grafo | `[[wikilinks]]` + frontmatter (Obsidian) + graphify | — | — | já existe; sem Neo4j |
| Interface / agente | **Claude Code** (72 agentes + 134 skills do vault Criminal) + **Obsidian** (leitura/edição) | OpenWebUI (pip em venv 3.12 do uv; sem Docker aqui) só se equipe não técnica precisar de chat | — | a camada de agente já existe e é auditável em git; OpenWebUI duplicaria |
| Exportação | `gerar_docx_juridico.py` + `docx-juridico-padrao` | md2docx.js | — | padrão tipográfico já fixado |
| Ingestão de autos | MCP PJe TJMA + DJEN API + DataJud + Jusbrasil CLI | PDPJ (token bridge) | Jus IA "Importar processo" (SaaS) | já testado em 1º e 2º graus |

### 5.1 Inferência local — o que baixar (comandos)

```bash
ollama pull qwen3:8b          # ~5 GB, distiladores por ato, PT-BR bom, tool-calling
ollama pull bge-m3            # embedding 1024d
ollama pull phi4-mini         # ~2,5 GB, classificação rápida de ato_tipo quando o regex falha
# opcional, qualidade > velocidade:
ollama pull gemma3:12b        # ~8 GB, ~3-5 tok/s
```

Configuração recomendada: `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_KEEP_ALIVE=30m`, `num_ctx` 16k para
distiladores (um ato raramente passa de 12k tokens). Não subir `num_ctx` para 128k em CPU: o
tempo de pré-preenchimento inviabiliza.

Benchmark obrigatório antes de fixar o modelo (1 minuto):

```bash
ollama run qwen3:8b --verbose "Resuma em 3 linhas: o art. 155 do CP tipifica o furto."
```

Registrar `eval rate` e `prompt eval rate` em `40-Recursos/benchmark-llm-local.md`.

### 5.2 iGPU Intel

Ollama não suporta a Intel Graphics integrada oficialmente; há build experimental com Vulkan
(`OLLAMA_VULKAN=1`) e o llama.cpp tem backend SYCL. Em iGPU com memória compartilhada o ganho
sobre 12 threads de CPU é pequeno (10-30%) e a estabilidade em Windows é irregular. Tratar como
experimento, não como base do sistema.

### 5.3 LLMs em nuvem via OpenRouter — tiers

IDs do catálogo mudam; conferir em openrouter.ai/models antes de fixar em `config.json`.

| Tier | Uso | Modelos (ordem de preferência) | Observação |
|---|---|---|---|
| Forte (peça, parecer, síntese cross-document) | Etapas A-C, `jurisprudencia-filtrada` | `anthropic/claude-opus-5`, `anthropic/claude-sonnet-5` | Fable 5.1 (Claude Code) para orquestração e auditoria final |
| Leitura longa (autos inteiros anonimizados, 300-1000 páginas) | contexto de 1M tokens | `google/gemini-*-pro` (1M), `anthropic/claude-sonnet-5` (1M com flag) | preferir retrieval a contexto bruto; usar só quando o retrieval não basta |
| Barato/volume (classificação, extração em lote, distiladores que o local não dá conta no prazo) | lote noturno | `deepseek/deepseek-v4-*` (via `fcc` ou OpenRouter), `qwen/qwen3-235b-a22b`, `google/gemini-*-flash` | ordem de 10x mais barato que o tier forte |
| Nacional (residência de dados no Brasil) | quando o cliente exigir | Maritaca `sabia-3` (API própria, não OpenRouter) | PT-BR nativo; conferir termos de retenção |

Políticas obrigatórias na conta OpenRouter: (a) desativar provedores que treinam com prompts
("Zero Data Retention" / `data_collection: deny`); (b) allowlist de provedores por modelo; (c)
`X-Title` e `HTTP-Referer` fixos para auditoria; (d) chave em variável de ambiente
`OPENROUTER_API_KEY` (hoje **não existe** no ambiente; nenhuma chave de LLM está definida).

Custo, ordem de grandeza (conferir preço do dia): autos de 300 páginas ≈ 200k tokens; leitura
integral no tier forte ≈ US$ 0,6-3; no tier barato ≈ US$ 0,05-0,3. Com retrieval (8-12 chunks por
pergunta, ~8k tokens) o custo por peça cai para centavos por etapa.

### 5.4 Anonimização antes de sair da máquina (`anonimizar.py`, a construir)

Aplica a §2.5.4 da norma ao fluxo de nuvem: substitui nomes de partes, CPF/CNPJ, RG, endereços,
placas, IMEI e números de telefone por tokens estáveis (`PESSOA_1`, `CPF_1`) mantendo um mapa
local cifrado por caso (`20-Casos/<CNJ>/.mapa_anon.json`, fora do OneDrive). O número CNJ é
público e permanece. A resposta do modelo é desanonimizada localmente antes de gravar em `pecas/`.
Regex + dicionário de partes extraído da autuação (`atos.jsonl`, ato `AUTUACAO`/capa); revisão
humana do mapa obrigatória na primeira peça de cada caso.

Implementado em `tools/anonimizar.py` (2026-09-07). Limites conhecidos, para a revisão humana:
o dicionário vem da capa e do rol da denúncia, então nomes que só aparecem no corpo dos atos
(vítimas citadas, informantes, servidores) precisam entrar por `--nomes`, e `--sugerir` lista os
candidatos em maiúsculas para aprovação; locais (fazenda, bairro) só por `--termos`; assinantes
do carimbo do PJe (magistrado, promotor, servidor) não são mascarados por padrão; o mapa ainda
não é cifrado. A reversão devolve o nome canônico (sem as variantes de acento e de quebra de
linha do OCR), logo o texto revertido não é byte a byte igual ao original.

---

## 6. Sigilo, LGPD e ética

- Autos, mídias e o banco `casos.lance` ficam fora do OneDrive e fora de qualquer API externa. Sigilo profissional: EAOAB art. 7º II e art. 34 VII; Código de Ética arts. 35-38.
- LGPD: dados de investigado são sensíveis por conexão (art. 5º II, art. 11); base legal do tratamento é o exercício regular de direitos (art. 7º VI); registrar em `40-Recursos/registro-tratamento.md` quais modelos externos recebem o quê (anonimizado).
- Uso de IA generativa na advocacia: seguir as recomendações do Conselho Federal da OAB para IA generativa [VERIFICAR: ato aprovado em 2024, número e texto vigente] e a Recomendação CNJ 140/2023 no que couber; a peça declara revisão humana e nunca cita o que o validador marcou.
- Logs: cada chamada a modelo (local ou nuvem) grava `modelo, tokens_in, tokens_out, hash do prompt anonimizado, caso` em `~/.notebooklm/relatorios/llm-log.jsonl`. Sem o texto do prompt.
- Retenção: `raw/` e `extracted/` seguem o prazo do caso (Provimento 188/2018 OAB, 5 anos após o encerramento); `.mapa_anon.json` é destruído no encerramento.

---

## 7. Roteiro de implantação

| Fase | Entrega | Existe? | Esforço | Dependência |
|---|---|---|---|---|
| 1 | `ollama pull` (qwen3:8b, bge-m3, phi4-mini) + benchmark registrado | **feito 2026-09-07** (§0.1) | — | — |
| 2 | venv com `lancedb`, `sentence-transformers`, `torch` CPU e o reranker baixado | **feito 2026-09-07**: `.venv-rag314` (python.org 3.14; o SAC bloqueou o Python do `uv`); lancedb 0.38, torch 2.14+cpu, reranker testado | — | — |
| 3 | `fatiar_atos.py` (§3.1.2) + `atos.jsonl` + testes nos autos de `~/.notebooklm/autos/0800515` e `casos/0801524-21.2024.8.10.0093`; conferência cruzada com o grid do PJe (§3.1.3, `pje_seletores_conecta.json`) | **feito 2026-09-07** em `tools/fatiar_atos.py`: 733 págs → 110 atos, 8 indeterminados, 14 ids de OCR unificados, 2 atos atravessando volume; falta a conferência cruzada com o grid do PJe (depende do MCP) | — | MCP PJe |
| 4 | `indexar.py`: FTS5 + LanceDB (dois bancos) + `buscar.py` híbrido com reranker | **feito 2026-09-07** (`tools/rag_comum.py`, `indexar.py`, `buscar.py`; bancos em `%LOCALAPPDATA%\cerebro\`). Caso de teste: 747 chunks (uma página cada) em 37 min de embedding; consulta com reranker 35-40 s, sem reranker (fusão RRF) 1,5 s com o mesmo top-2; corpus Crítica Penal indexado no banco `vault` (102 chunks, só FTS por ora). Reranker leve `gte-multilingual-reranker-base` testado e descartado (código próprio incompatível). Falta: embeddings dos corpora públicos em lote noturno; reranker mais leve ainda em aberto | — | fases 1-2 |
| 5 | distiladores sem LLM: prazos (dias corridos), prescrição, cronologia | **feito 2026-09-07** em `tools/`: `calendario_forense.py` (feriados nacionais + estaduais MA + TJMA + municipais por `--comarca`), `prazo_cpp.py` (cálculo CPP 798 com Súm. 310/710 STF e radar de prazos por ato, rito detectado na capa: JECrim aplica Lei 9.099), `prescricao_cp.py` (CP 109-117 com pena lida do dataset do artigo, marcos do `marcos.json`, pena concreta CP 110 §1º, suspensões só por parâmetro), `cronologia_atos.py` (linha do tempo por ato + marcos lidos do tipo E do texto, só na forma afirmativa). Testado no caso de Itinga: rito JECrim detectado, 18 atos abrindo prazo, recebimento da denúncia achado dentro da ata de 2026-04-10, Lei 9.605 art. 50 → 4 anos de prescrição | — | fase 3 |
| 6 | distiladores com LLM local (controvérsia, nulidades, prisão, dosimetria) com JSON schema | **feito 2026-09-07** em `tools/distilar_atos.py` (qwen3:8b, temperatura 0, `format` de schema do Ollama, um ato por chamada, cache por hash, roteamento por tamanho, reparo de JSON truncado, trecho literal conferido). Caso de Itinga: 15 atos distilados em 71 min de modelo, **106/113 trechos localizados (94%)**; `controversia.md` com imputação (art. 50 da Lei 9.605, período 16/08/2019 a 21/07/2023, provas, ANPP e transação negados) e as teses das duas respostas à acusação e das alegações finais do MP; `nulidades.md` virou **inventário descritivo** das 10 decisões/atas (o 8B não julga: detecção de vício saiu do local e ficou com o agente); `prisao.md` e `dosimetria.md` vazios por não haver cautelar nem sentença; 1 anexo de 65k tokens em `para_nuvem.json`. Custo típico: 1,5-5 min por ato (a geração a ~3 tok/s domina); ato de 6k tokens = 15 min | — | fases 1, 3 |
| 7 | `anonimizar.py` + `config_llm.json` de tiers + cliente `llm_nuvem.py` + `OPENROUTER_API_KEY` | **feito 2026-09-07, menos a chave**: `tools/anonimizar.py` (partes lidas da capa, testemunhas do rol da denúncia, `--nomes`/`--termos` aprovados pelo humano, `--sugerir` lista candidatos; CPF/CNPJ/RG/telefone/e-mail/placa/IMEI/CEP por regex; mapa em `%LOCALAPPDATA%\cerebro\anon\<CNJ>.json`, fora do OneDrive, **ainda sem cifra**); `tools/config_llm.json` (tiers forte/longo/barato/nacional, política `data_collection: deny`, preços só para estimativa); `tools/llm_nuvem.py` (anonimiza → chama → reverte; log em `relatorios/llm-log.jsonl` só com hash, tokens e custo; `--dry-run` sem chave). Testado no caso de Itinga: réu, advogado, 3 testemunhas, CPF, RG e a fazenda mascarados; reversão canoniza acento e quebra de linha (não é byte a byte). **Nenhuma chave de LLM existe no ambiente**: a chamada real fica para quando `OPENROUTER_API_KEY` for definida | — | conta OpenRouter com ZDR |
| 8 | `validador_fontes.py` + `validador_processual.py` + integração com `verificador-citacoes` | **feito 2026-09-07** em `tools/`: `validador_fontes.py` (súmulas STJ/STF/vinculantes, temas de RG do STF, artigos de 40 datasets, precedentes e temas por busca literal nos corpora, informativos, IDs/páginas do `atos.jsonl`; redação entre aspas adjacente ao artigo conferida; marcador inline `[VERIFICAÇÃO NECESSÁRIA: …]`; "não localizada" nunca vira "não existe"), `validador_processual.py` (nulidade→pedido, pedido→fundamentação, rito por peça, honorários em peça criminal, rol de testemunhas 8/5, prequestionamento e repercussão geral em REsp/RE, tempestividade via `prazo_cpp`, âncoras nos fatos) e `validar_minuta.py` (gate único: status, minuta anotada, dois relatórios e `citacoes_para_verificar.json` para o agente). Teste com minuta sintética: 20 citações, todas as 4 falsas apanhadas, todas as reais aprovadas; 4 alertas altos corretos (honorários, rol de 6 no JECrim, nulidade sem pedido, intempestiva) | — | JSONs canônicos (existem) |
| 9 | comando `/analisar-autos <CNJ>` (Capture→Distill) e `/minutar <peça> <CNJ>` (Express planejado) no vault Criminal | **feito 2026-09-07**: `Criminal/.claude/commands/analisar-autos.md` (11 passos: pdf2md → fatiar → cronologia → prazos → prescrição → indexar → distilar → anonimizar → ficha por iniciais → delegação a `auditoria-nulidades-criminal`/`relatorio-inteligencia-criminal`) e `minutar.md` (plano → etapas A/B/C → gate → `verificador-citacoes` → docx). Scripts espelhados em `Criminal/.claude/tools/pipeline/` (16 arquivos + README), cientes do layout do vault (datasets em `..`, corpora em `../../corpora`, RG em `../../prazos`); `rag_comum.py` reexecuta-se no venv sozinho, para o comando ficar em caminho relativo (Classe A). Runtime declarado em `REQUISITOS-EXTERNOS.md` §9 e linha no `CLAUDE.md` do vault | — | fases 3-8 |
| 10 | lote noturno + relatório de custo por caso | **feito 2026-09-07**: `tools/lote_noturno.py` (um `caso.json` por caso em `%LOCALAPPDATA%\cerebro\casos\<CNJ>\`; etapas idempotentes por mtime e cache: fatiar → cronologia → prazos → prescrição → pseudonimizar e copiar para `20-Casos/` → indexar → distilar, as longas só dentro de `--janela-min`; `--sem-llm`, `--dry-run`, `--so-relatorio`) + `LOTE_NOTURNO.bat` (janela de 6 h; o `schtasks` para 02:00 está documentado no script e **não foi registrado**: é decisão sua). Relatório `relatorios/custo-<data>.md/.json`: tempo por etapa, tokens e minutos do modelo local por caso (do cache `distill/llm/`), chamadas/tokens/US$ em nuvem (do `llm-log.jsonl`). Testado no caso de Itinga em modo determinístico: 3 saídas pseudonimizadas copiadas para o vault, zero nome real vazado; custo local acumulado 71 min, nuvem US$ 0 | — | fase 9 |
| 11 | OpenWebUI (opcional, só se houver equipe não técnica) | **bloqueada na instalação, integração pronta (2026-09-07)**: o `open-webui` 0.11.3 exige Python 3.11-3.12; o único Python que o Smart App Control aceita aqui é o 3.14 do python.org (o 3.12 do `uv` é bloqueado) e não há Docker. Caminhos: instalar o Python 3.12 do python.org (assinado) e `pip install open-webui` num venv dele, ou Docker Desktop. O que já está feito e independe da UI: `tools/rag_server.py` (HTTP local em 127.0.0.1:8765, só stdlib, roda no venv RAG: `/saude`, `/buscar`, `/casos`, `/caso/<cnj>/<arquivo>`, `POST /validar`, `POST /anonimizar`, `POST /reverter`) e `tools/openwebui_tool_cerebro.py` (Tool do Open WebUI que chama esse servidor: listar casos, buscar nos autos com âncora, ler linha do tempo/prazos/controvérsia, anonimizar antes da nuvem, validar minuta). Testado por HTTP no caso de Itinga | — | Python 3.12 assinado ou Docker |

Total estimado: 10-14 dias úteis de construção, quase tudo em Python padrão, sem servidor
permanente além do Ollama.

---

## 8. Decisões que dependem de você

1. **OpenRouter ou contas diretas** (Anthropic/Google/DeepSeek): OpenRouter simplifica o roteamento por tier; contas diretas dão termos de retenção mais claros. Recomendo OpenRouter com ZDR para começar.
2. **Onde fica `casos.lance`**: proposta `%LOCALAPPDATA%\cerebro\` (fora do OneDrive). Se você precisa dos índices em duas máquinas, a alternativa é reindexar em cada uma a partir do `extracted/` (barato) em vez de sincronizar o banco.
3. **Manter ou remover a extensão MinutaIA Conecta.** Se ficar, os autos passam por Jusbrasil/Vercel/Cloudflare/AWS e isso precisa constar no registro de tratamento (§6); a permissão opcional `*://*/*` deve continuar negada.
4. **Reativar o watcher `inbox_pdf2md`** para que todo PDF que cair em `00-Inbox/` já saia fatiado (hoje desativado).
