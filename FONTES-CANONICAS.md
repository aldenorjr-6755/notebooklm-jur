# Fontes canônicas — manual único

> Gerado por `~/.notebooklm/tools/gerar_fontes_canonicas.py` em 2026-09-07. **Não edite à mão**:
> acrescente a fonte (helper/dataset/agente/slash) e rode o gerador de novo.
> Referenciado por uma linha em cada `CLAUDE.md` — este arquivo é a única fonte de verdade.

## Regras de uso (valem para toda consulta)

1. **Nunca cite norma, súmula, tese ou precedente de memória** — rode o helper e cite o retorno.
2. Datasets são **snapshots**: confirme vigência (EC/lei alteradora/cancelamento) na fonte oficial.
3. Notebook do NotebookLM é **doutrina ou acervo indexado** — cite título/autor/data/URL e confirme o inteiro teor.
4. Falta de dado → escreva `[VERIFICAR]`. Não complete nem parafraseie dispositivo legal.
5. **"Artigo não encontrado" pode ser defeito do dataset, não erro da pergunta.** Em 2026-08-05,
   o RISTF rodava havia meses **sem 29 artigos** — inclusive todo o rito da súmula vinculante —
   porque o extrator só aceitava sufixo de letra maiúscula; e o RITJMA devolvia a redação
   **revogada** do art. 390. Antes de concluir que a norma não existe, rode:
   `python ~/.notebooklm/tools/lint_fontes_canonicas.py --so-suspeitos`
   (LACUNA = artigo sumiu · MOJIBAKE = acento corrompido, busca falha em silêncio ·
   REDACOES = redações sucessivas sem placa · ORFAO = dataset que helper nenhum consulta).

## Slash commands (escopo de usuário — valem em qualquer vault)

84 comandos em `~/.claude/commands/`. Um vault pode sombrear qualquer um deles com
uma versão local em `<vault>/.claude/commands/` (escopo de projeto vence).
Há hoje **255 slash commands locais** distribuídos por 13 cofres — a tabela
por vault está no fim deste documento, em *Recursos do Claude Code*.

| Slash | O que faz |
|---|---|
| `/adi-adc` | Lei 9.868/1999 (processo da ADI e ADC no STF) — edição temática anotada, por artigo ou palavra |
| `/adpf` | Lei 9.882/1999 (Arguição de Descumprimento de Preceito Fundamental — ADPF) — ed. temática anotada, por artigo ou palavra |
| `/aplicacao-sumula` | Busca ONLINE de Súmulas do STF (vinculantes/comuns) + aplicação, por número, palavra ou ramo |
| `/atomismo-holismo` | Diagnostica se uma análise jurídica (prova, argumento, norma, decisão) é atomista, holista ou dialeticamente equilibrada — notebook NotebookLM dedicado |
| `/bayes-juridico` | Aplica o Teorema de Bayes (likelihood ratio/odds) à prova jurídica e audita falácias probabilísticas — notebook NotebookLM dedicado |
| `/bnp` | Busca precedentes qualificados no Banco Nacional de Precedentes (BNP/Pangea, CNJ) — RG, RR, SV, Súmula, IAC, IRDR |
| `/boletim-precedentes` | Consulta os Boletins de Precedentes do STJ (nº 1–140, 2017–2026) e devolve o enunciado da tese firmada com a citação do Boletim |
| `/cadh-stf` | Localiza a leitura do STF sobre um artigo da CADH (obra "Convenção Americana sobre DH", 2ª ed.) |
| `/cadh` | Convenção Americana de Direitos Humanos (Pacto de São José / Decreto 678/92) — artigo ou palavra |
| `/cc` | Código Civil (Lei 10.406/2002, compilada) — texto literal por artigo ou palavra |
| `/cf` | Devolve o texto literal de um artigo da Constituição Federal (Planalto, até EC 139) |
| `/codoje` | Código de Divisão e Organização Judiciárias do Maranhão (consolidado até LC 298/2026) — por artigo ou palavra |
| `/coletanea-tse` | Consulta a Coletânea de Jurisprudência por Assunto do TSE — 22 temas eleitorais com teses e precedentes, no corpus local |
| `/constituicao` | Dado um artigo da CF, localiza a leitura do STF na obra "A Constituição e o Supremo |
| `/correicao-parcial` | Redige uma Correição Parcial criminal (medida residual contra erro de procedimento/inversão tumultuária) no padrão dos Tribunais, via subagente |
| `/corroboracao-falsificacionista` | Audita a força epistêmica de uma hipótese fática/acusatória pela Teoria da Corroboração Falsificacionista (Popper) — notebook NotebookLM dedicado |
| `/cp` | Código Penal (Decreto-Lei 2.848/1940, compilado) — texto literal por artigo ou palavra |
| `/cpc` | Código de Processo Civil (Lei 13.105/2015, compilada) — texto literal por artigo ou palavra |
| `/cpp` | Código de Processo Penal (Decreto-Lei 3.689/1941, compilado) — texto literal por artigo ou palavra |
| `/crimes-tributarios` | Crimes contra a Ordem Tributária (Lei 8.137/1990) — texto literal por artigo ou palavra |
| `/criminal-player` | Consulta o acervo "Criminal Player" / "Limite Penal" (coluna ConJur, 7 notebooks NotebookLM) e traz a doutrina de processo penal e epistemologia da prova sobre um tema |
| `/critica-penal` | Consulta o acervo "Crítica Penal" (coluna ConJur, NotebookLM) e traz a doutrina penal crítica/garantista sobre um tema |
| `/ctj-advocacia-oab` | Coletânea Temática de Jurisprudência STF — Advocacia e OAB (índice tema → página) |
| `/ctj-controle-constitucionalidade` | Coletânea Temática de Jurisprudência STF — Controle de Constitucionalidade (índice tema → página) |
| `/ctj-dh` | Coletânea Temática de Jurisprudência STF — Direitos Humanos (índice tema → página) |
| `/ctj-eleitoral` | Coletânea Temática de Jurisprudência STF — Direito Eleitoral (índice tema → página) |
| `/ctj-penal` | Coletânea Temática de Jurisprudência STF — Direito Penal e Processual Penal (índice tema → página) |
| `/ctn` | Código Tributário Nacional (Lei 5.172/1966, compilada) — texto literal por artigo ou palavra |
| `/direito-de-defesa` | Consulta o acervo "Direito de Defesa" (coluna ConJur, NotebookLM) e traz a doutrina penal de defesa — ênfase em lavagem/colarinho-branco — sobre um tema |
| `/direitos-fundamentais` | Consulta o acervo "Direitos Fundamentais" (coluna ConJur, NotebookLM) e traz a doutrina constitucional / de direitos fundamentais sobre um tema, com citação das fontes |
| `/drogas` | Lei de Drogas (Lei 11.343/2006) — texto literal por artigo ou palavra |
| `/eaoab` | Estatuto da Advocacia e da OAB (Lei 8.906/1994) — edição temática anotada do STF, por artigo ou palavra |
| `/foundherentismo` | Avalia a prova como peças de um quebra-cabeça de palavras cruzadas pela Epistemologia Foundherentista de Susan Haack — notebook NotebookLM dedicado |
| `/gerar-index` | Reconcilia os index.md dos vaults com o estado real das pastas (dry-run primeiro) |
| `/glossario` | Glossário Jurídico do STF — definição de termo jurídico (por verbete ou palavra) |
| `/health-check` | Audita a saúde de um vault — fallback genérico; prefira o /health-check local do vault |
| `/hediondos` | Lei dos Crimes Hediondos (Lei 8.072/1990) — texto literal por artigo ou palavra |
| `/ibe-abducao` | Compara hipóteses fáticas concorrentes pelo poder explicativo (Inferência à Melhor Explicação / Abdução Probatória) — notebook NotebookLM dedicado |
| `/informativo-stf` | Busca nos Informativos de Jurisprudência do STF (corpus dedicado, 2014–2026, ed. ~733–1220) |
| `/jecrim` | Lei dos Juizados Especiais (Lei 9.099/1995) — texto literal por artigo ou palavra (foco criminal) |
| `/jurisprudencia` | Busca full-text no corpus oficial de jurisprudência (Informativos/Teses/Repetitivos STF·STJ·TRF1) |
| `/justo-processo` | Consulta o acervo "Justo Processo" (coluna ConJur, NotebookLM) e traz a doutrina de processo penal / epistemologia da prova sobre um tema, com citação das fontes |
| `/lc105` | Lei do Sigilo Bancário (LC 105/2001, compilada) — texto literal por artigo ou palavra |
| `/lef` | Lei de Execução Fiscal (Lei 6.830/1980, compilada) — texto literal por artigo ou palavra |
| `/lei12030` | Lei das Perícias Oficiais (Lei 12.030/2009) — texto literal por artigo ou palavra |
| `/lei12830` | Lei da Investigação Criminal pelo Delegado de Polícia (Lei 12.830/2013) — texto literal por artigo ou palavra |
| `/lei12850` | Lei de Organização Criminosa (Lei 12.850/2013, compilada) — texto literal por artigo ou palavra |
| `/lei12965` | Marco Civil da Internet (Lei 12.965/2014) — texto literal por artigo ou palavra |
| `/lei13097` | Lei 13.097/2015 (compilada) — concentração dos atos na matrícula; texto literal por artigo ou palavra |
| `/lei9296` | Lei de Interceptação Telefônica (Lei 9.296/1996, compilada) — texto literal por artigo ou palavra |
| `/lei9605` | Lei de Crimes Ambientais (Lei 9.605/1998, compilada) — texto literal por artigo ou palavra |
| `/lei9613` | Lei de Lavagem de Dinheiro (Lei 9.613/1998, compilada) — texto literal por artigo ou palavra |
| `/lei9873` | Lei de Prescrição Administrativa (Lei 9.873/1999, compilada) — texto literal por artigo ou palavra |
| `/lep` | LEP — Lei de Execução Penal (Lei 7.210/1984, compilada) — texto literal por artigo ou palavra |
| `/lgpd` | Lei Geral de Proteção de Dados (LGPD, Lei 13.709/2018, compilada) — texto literal por artigo ou palavra |
| `/lindb` | LINDB — Lei de Introdução às Normas do Direito Brasileiro (DL 4.657/1942) — por artigo ou palavra |
| `/lrp` | Lei de Registros Públicos (Lei 6.015/1973, compilada) — texto literal por artigo ou palavra |
| `/maria-da-penha` | Lei Maria da Penha (Lei 11.340/2006) — texto literal por artigo ou palavra |
| `/meta-prova` | Camada META da epistemologia da prova — seleciona e arbitra entre os doze métodos probatórios e audita o resíduo que método nenhum captura |
| `/ms` | Lei 12.016/2009 (Mandado de Segurança individual e coletivo) — texto literal por artigo ou palavra |
| `/narrativismo` | Reconstrói e avalia narrativas fáticas concorrentes pelo Modelo das Histórias (Narrativismo) na Teoria da Prova — notebook NotebookLM dedicado |
| `/novo-caso` | Cria a pasta de um novo caso a partir do template |
| `/paf` | Lei 9.784/1999 (Processo Administrativo Federal) — texto literal por artigo ou palavra |
| `/pesquisa-perplexity` | Pipeline Perplexity (MCP, busca ao vivo) → NotebookLM (destilação sem alucinação) → Wiki |
| `/pesquisar-notebooklm` | Pesquisa pesada de um tema via NotebookLM e destila numa nota da Wiki |
| `/pidcp` | Pacto Internacional sobre Direitos Civis e Políticos (PIDCP/ONU, Decreto 592/92) — artigo ou palavra |
| `/processar-inbox` | Destila o 00-Inbox em notas atômicas por encadeamento de etapas, com crítica antes de gravar |
| `/ristf` | Texto literal de artigo do Regimento Interno do STF (até ER 59/2023) |
| `/ristj` | Texto literal de artigo do Regimento Interno do STJ (consolidado até ER 53/2026) |
| `/ritjma` | Texto literal de artigo do Regimento Interno do TJMA (consolidado até Res.-GP 13/2026) |
| `/rstj` | Busca no inteiro teor da Revista do STJ (RSTJ, 1989–2024) — 303 volumes, ~19 mil acórdãos, com página conferível |
| `/sc-direito-ambiental` | Coleção Supremo Contemporâneo — Direito Ambiental (índice tema → página) |
| `/sc-liberdade-expressao` | Coleção Supremo Contemporâneo — Liberdade de Expressão (índice tema → página) |
| `/senso-incomum` | Consulta o acervo "Senso Incomum" (Lenio Streck, ConJur) — hermenêutica/teoria da decisão — por tema |
| `/standards-of-proof` | Audita se o conjunto probatório atinge o standard of proof exigido pelo tipo de processo/decisão — notebook NotebookLM dedicado |
| `/sumula-stf` | Consulta as Súmulas (comuns) do STF — fonte canônica — por número ou palavra |
| `/sumula-stj` | Consulta as Súmulas do STJ (fonte canônica) por número ou palavra e padroniza a citação |
| `/sumula-tse` | Consulta as Súmulas do TSE (73 súmulas, 66 vigentes) por número ou tema e padroniza a citação |
| `/sumula-vinculante` | Consulta as Súmulas Vinculantes do STF (CF 103-A — efeito vinculante) por número ou palavra |
| `/termo-juridico` | Consulta o Tesauro Jurídico do STF e padroniza a terminologia (cria/atualiza nota da Wiki) |
| `/tese-rg` | Pesquisa os Temas de Repercussão Geral do STF e destila em nota da Wiki |
| `/tese` | Monta uma nota-tese completa sobre um tema cruzando NORMA (lei) + JURISPRUDÊNCIA + DOUTRINA (acervos ConJur), com citação e anti-invenção |
| `/tpi` | Estatuto de Roma do Tribunal Penal Internacional (TPI, Decreto 4.388/2002) — artigo ou palavra |
| `/wigmore` | Mapeia a estrutura inferencial de uma massa de evidência pelo Método Analítico de Wigmore (Wigmorean Charting) — notebook NotebookLM dedicado |

## Normas — texto literal por artigo

**Constituição, obras e tratados**

| Fonte | Comando | Cobertura |
|---|---|---|
| CF/1988 (texto Planalto) | `python $HOME/.notebooklm/tools/consultar_cf.py <art>` · `/cf` | 276 artigos (ADCT não indexado) |
| A Constituição e o Supremo (CF anotada pelo STF) | `consultar_constituicao_supremo.py <art>` · `/constituicao` | 264 artigos → página do PDF |
| RISTF | `consultar_regimento.py --fonte stf <art>` · `/ristf` | 399 artigos |
| RISTJ | `consultar_regimento.py --fonte stj <art>` · `/ristj` | 441 artigos |
| RITJMA | `consultar_regimento.py --fonte tjma <art>` · `/ritjma` | 727 artigos |
| RITSE | `consultar_regimento.py --fonte tse <art>` · `/ritse` | 94 artigos |
| Convenção Americana sobre Direitos Humanos (Pacto de São José da Costa Rica) — Decreto 678/1992 | `consultar_tratado.py --fonte cadh <art>` · `/cadh` | 82 artigos |
| Pacto Internacional sobre Direitos Civis e Políticos (PIDCP) — Decreto 592/1992 | `consultar_tratado.py --fonte pidcp <art>` · `/pidcp` | 53 artigos |
| Estatuto de Roma do Tribunal Penal Internacional (TPI) — Decreto 4.388/2002 | `consultar_tratado.py --fonte tpi <art>` · `/tpi` | 128 artigos |

**Códigos e leis** — helper único, 38 fontes:

```bash
python $HOME/.notebooklm/tools/consultar_codigo.py --fonte <sigla> <artigo|palavra>
```

| `--fonte` | Norma | Registros |
|---|---|---|
| `cc` | Código Civil (Lei 10.406/2002, compilada) | 2092 |
| `codoje` | Código de Divisão e Organização Judiciárias do Maranhão (consolidado até LC 298/2026) | 275 |
| `cp` | Código Penal (Decreto-Lei 2.848/1940, compilado) | 434 |
| `cpc` | Código de Processo Civil (Lei 13.105/2015, compilada) | 1073 |
| `cpp` | Código de Processo Penal (Decreto-Lei 3.689/1941, compilado) | 853 |
| `ctn` | Código Tributário Nacional (Lei 5.172/1966, compilada) | 225 |
| `eaoab` | Estatuto da Advocacia e da OAB (Lei 8.906/1994) — edição temática STF (anotada) | 88 |
| `lc105` | LC 105/2001 (Sigilo Bancário) | 13 |
| `lc64` | Lei das Inelegibilidades (LC 64/1990) | 33 |
| `lei11340` | Lei 11.340/2006 (Maria da Penha) | 57 |
| `lei11343` | Lei 11.343/2006 (Lei de Drogas) | 99 |
| `lei12016` | Lei 12.016/2009 (Mandado de Segurança individual e coletivo) | 29 |
| `lei12030` | Lei 12.030/2009 (Perícias Oficiais) | 6 |
| `lei12830` | Lei 12.830/2013 (Investigação Criminal pelo Delegado de Polícia) | 4 |
| `lei12850` | Lei 12.850/2013 (Organização Criminosa) | 36 |
| `lei12965` | Lei 12.965/2014 (Marco Civil da Internet) | 37 |
| `lei13097` | Lei 13.097/2015 (compilada) — concentração dos atos na matrícula | 169 |
| `lei13146` | Lei 13.146/2015 (Estatuto da Pessoa com Deficiencia) | 130 |
| `lei13431` | Lei 13.431/2017 (Sistema de Garantia de Direitos da Criança e do Adolescente Vítima ou Testemunha de Violência) | 29 |
| `lei13709` | Lei 13.709/2018 (LGPD) | 80 |
| `lei4737` | Código Eleitoral (Lei 4.737/1965 — texto TSE) | 385 |
| `lei6015` | Lei de Registros Públicos (Lei 6.015/1973, compilada) | 321 |
| `lei6830` | Lei 6.830/1980 (Execução Fiscal — LEF) | 42 |
| `lei8072` | Lei 8.072/1990 (Crimes Hediondos) | 13 |
| `lei8137` | Lei 8.137/1990 (Crimes contra a Ordem Tributária) | 23 |
| `lei8429` | Lei 8.429/1992 — Improbidade Administrativa (compilada com Lei 14.230/2021) | 35 |
| `lei9096` | Lei dos Partidos Políticos (Lei 9.096/1995) | 85 |
| `lei9099` | Lei 9.099/1995 (Juizados Especiais Cíveis e Criminais) | 99 |
| `lei9296` | Lei 9.296/1996 (Interceptação Telefônica) | 14 |
| `lei9504` | Lei das Eleições (Lei 9.504/1997) | 152 |
| `lei9605` | Lei 9.605/1998 (Crimes Ambientais) | 87 |
| `lei9613` | Lei 9.613/1998 (Lavagem de Dinheiro) | 29 |
| `lei9784` | Lei 9.784/1999 (Processo Administrativo Federal) | 80 |
| `lei9868` | Lei 9.868/1999 (ADI e ADC) — edição temática STF (anotada) | 39 |
| `lei9873` | Lei 9.873/1999 (Prescrição Administrativa) | 9 |
| `lei9882` | Lei 9.882/1999 (ADPF) — edição temática STF (anotada) | 14 |
| `lep` | LEP — Lei de Execução Penal (Lei 7.210/1984) | 219 |
| `lindb` | LINDB — Lei de Introdução às Normas do Direito Brasileiro (Decreto-Lei 4.657/1942) | 30 |

_"Registros" conta cada entrada do dataset — inclui variantes (`1.240-A`) e revogados em stub;
não é o número nominal de artigos da lei. Nova norma = rodar `extrair_codigo.py` + 1 linha no REG + slash + rodar este gerador._

## Jurisprudência e súmulas

| Fonte | Comando | Cobertura |
|---|---|---|
| Súmulas do STJ | `consultar_sumula_stj.py "<palavra>"` · `/sumula-stj` | 656 verbetes |
| Súmulas do STF (comuns) | `consultar_sumula_stf.py "<palavra>"` · `/sumula-stf` | 736 verbetes |
| Súmulas Vinculantes (CF 103-A) | `consultar_sumula_vinculante.py "<palavra>"` · `/sumula-vinculante` | 63 verbetes |
| Súmula do STF + aplicação (online, vigente) | `consultar_aplicacao_sumula.py --tipo sv\|comum <n>` · `/aplicacao-sumula` | versão atual + precedentes |
| Temas de Repercussão Geral | `consultar_repercussao_geral.py "<palavra>"` · `/tese-rg` | JSON oficial STF (com/sem RG) |
| Precedentes qualificados (BNP/Pangea CNJ) | `consultar_bnp.py` · `/bnp` | RG/RR/SV/IAC/IRDR; não cobre TSE |
| Corpus full-text STF·STJ·TRF1 | `consultar_jurisprudencia.py "<termo>"` · `/jurisprudencia` | Informativos, Teses, Repetitivos, BIJ, SV |
| Informativos do **STF** | `consultar_informativo_stf.py "<termo>"` · `/informativo-stf` | 13 arquivos, **2014–2026** (ed. ~733–1220) |
| Informativos do **STJ** | `consultar_informativo_stj.py "<termo>"` · `/consulta-informativo-stj` | 835 arquivos, nº 1–853 (1998–2025) — **sem 2019** |

**Informativo do STF — o que o helper resolve e o que não resolve.** O corpus tem duas
famílias: 2014–2019 (*Teses e Fundamentos*, por matéria, conversão DOCX legada) e 2020–2026
(*Informativo Temático*, por ramo, conversão PDF paginada — o helper cita a **página do PDF**).
O **número da edição** sai resolvido em ~90% dos trechos dos temáticos e ~94% em 2017–2018,
mas é **estruturalmente irrecuperável em 2014, 2015, 2016 e 2019**, onde não existe marcador
no texto: ali cite processo + relator e declare a edição como não identificada — nunca a
deduza pela faixa do arquivo.

**Lacuna declarada — Informativo do STF.** O acervo começa em **2014**; as edições **1 a ~732
(1995–2013) não estão nele**. Nada encontrado ali não é achado negativo: para o período
anterior use o agente `rtj-stf` (RTJ, 1957–2017) ou o portal do STF.

**Informativo do STJ — o que o helper resolve.** Para cada trecho devolve **nº da edição,
ano, órgão julgador, ramo do direito, processo, relator e tema de repetitivo**, lendo as duas
diagramações do acervo (até ~2016, texto corrido com a citação fechando a entrada; de ~2017,
campos `PROCESSO / RAMO DO DIREITO / TEMA / DESTAQUE`). A busca é **insensível a acento**.
O helper **se autolocaliza**: dentro de um vault com espelho próprio, o mesmo arquivo em
`.claude/tools/` lê `.claude/corpora/informativo_stj/fontes` — não há caminho externo.
Ele também separa o processo **julgado** do processo **citado como precedente**, e nomeia a
entrada **em segredo de justiça** em vez de lhe emprestar o número da entrada vizinha.

**Lacuna declarada — Informativo do STJ.** O **ano de 2019 inteiro está fora do acervo**
(~23 edições, nº 639–661): o ZIP de origem tem 0 byte e o corpus salta de `Inf0638` para
`Inf0662`. Nada encontrado ali não é achado negativo — para 2019 use o corpus full-text
STF·STJ·TRF1 (de 2015 em diante) ou `scon.stj.jus.br`.

**Proveniência — Informativo do STJ (2026-08-05).** O corpus foi **reconvertido dos RTF**
oficiais por `rtf_stj_para_md.py`. A conversão anterior descartava o escape `\uNNNN` do RTF
e preservava o fallback ASCII, trocando **todo acento por `?`** (`compet?ncia`) em 795 dos 835
arquivos, e deixando vazar lixo binário das imagens embutidas. Busca por "competência" achava
**29** arquivos; hoje acha **684**. Espelhos com `?` no lugar de acento estão desatualizados:
reponha com `implantar_informativo_stj.py --vault <NOME>`. Os 3 notebooks do NotebookLM que
indexavam a conversão velha foram **apagados em 2026-08-05** — a consulta é só local.

**Vocabulário controlado** — `consultar_tesauro.py` (descritor STF, `/termo-juridico`) · 
`consultar_glossario.py` (definições STF, `/glossario`) · `consultar_glossario_tse.py` (`/glossario-tse`).

**Súmula comum ≠ vinculante.** A vinculante obriga Judiciário e Administração (reclamação ao STF).

## Obras temáticas do STF (sumário tema → página)

Devolvem a **página** do PDF; o teor exige abrir o PDF nela (`Read` com `pages:`).

| `--fonte` | Obra | Slash |
|---|---|---|
| `ctj_advocacia_oab` | Coletânea Temática de Jurisprudência: Advocacia e OAB | `/ctj-advocacia-oab` |
| `ctj_controle_constitucionalidade` | Coletânea Temática de Jurisprudência: Controle de Constitucionalidade | `/ctj-controle-constitucionalidade` |
| `ctj_dh` | Coletânea Temática de Jurisprudência: Direitos Humanos | `/ctj-dh` |
| `ctj_eleitoral` | Coletânea Temática de Jurisprudência: Direito Eleitoral | `/ctj-eleitoral` |
| `ctj_penal` | Coletânea Temática de Jurisprudência: Direito Penal e Processual Penal | `/ctj-penal` |
| `sc_direito_ambiental` | Direito Ambiental | `/sc-direito-ambiental` |
| `sc_liberdade_expressao` | Liberdade de Expressão | `/sc-liberdade-expressao` |

_Comando: `consultar_obra_tematica.py --fonte <sigla> <tema>`._

## Notebooks do NotebookLM (registry vivo)

Extraído dos agentes que efetivamente os consultam — a fonte de verdade é o próprio agente.
Consulta direta: `notebooklm ask "<pergunta>" -n <id> --json`.

A varredura cobre **os dois escopos**: `~/.claude/agents/` e o `.claude/agents/` de cada vault.
A coluna **Onde** diz em qual deles o agente vive — num cofre Classe A ele mora dentro do vault,
e só é acionável com o Claude Code iniciado na raiz dele.

Marcados **(apagado)** os 6 notebooks já removidos da conta — registro em
`~/.notebooklm/notebooks_mortos.txt`. Não tente consultá-los.

| Agente | Onde | Notebooks |
|---|---|---|
| `abraham-maslow` | vault **Psicologia** | `a7969675-a508-49d6-ab00-8b8e4cf774dd` |
| `acervo-familia-sucessoes` | `~/.claude/` | `0efe9aef-c085-42d2-9dcb-28b1d5e7faf8` · `7ecafd16-fd43-4167-a6bd-ef9d58742ae5` · `b90f1834-9dff-4d4c-bcd9-39d5c93f4ed4` · `c29cb334-adae-4aed-bd50-b0efad82faeb` |
| `analise-capacidade-adjudicatoria` | `~/.claude/` | `bd675d49-8704-419b-97e7-73597e4c545e` |
| `analise-confronto-testemunhal` | `~/.claude/` | `10bb4a29-6c43-4bb3-94a1-5e76021c286f` · `9681d5f6-db1f-4cf6-afd1-9bdebea3e8f4` · `bc44b655-5b7c-436e-8b06-fecef4943b35` · `db064855-08a6-4f69-9dee-c46053c97202` · `fb0eba5a-8050-4437-9391-5cb8ddb23162` |
| `analise-decisao-sob-pressao-institucional` | `~/.claude/` | `17081d6b-8875-42ff-93d4-b2ce3f08371e` · `27b30c76-5fdb-4a69-bf17-719b10b3c797` · `7faae4b1-ddef-421e-a841-1e5b95226521` · `fb0eba5a-8050-4437-9391-5cb8ddb23162` |
| `analise-deteccao-engano-depoimento` | vault **Criminal** | `9681d5f6-db1f-4cf6-afd1-9bdebea3e8f4` |
| `analise-dinamica-juri` | vault **Criminal** | `56a8a026-1b5b-4831-8030-afc129416d05` |
| `analise-emocao-punicao-decisao` | vault **Criminal** | `50601a41-c3a1-4c7a-b283-01298590e83e` |
| `analise-entrevista-investigativa` | vault **Criminal** | `db064855-08a6-4f69-9dee-c46053c97202` |
| `analise-falsas-confissoes` | vault **Criminal** | `27b30c76-5fdb-4a69-bf17-719b10b3c797` |
| `analise-narrativista` | vault **Criminal** | `9a8fc69d-cd63-423e-b5f4-02cb01ed61d1` |
| `analise-narrativista` | vault **Eleitoral** | `9a8fc69d-cd63-423e-b5f4-02cb01ed61d1` |
| `analise-narrativista` | `~/.claude/` | `9a8fc69d-cd63-423e-b5f4-02cb01ed61d1` |
| `analise-obediencia-institucional-policial` | vault **Criminal** | `bc44b655-5b7c-436e-8b06-fecef4943b35` |
| `analise-percepcao-memoria-estresse` | vault **Criminal** | `10bb4a29-6c43-4bb3-94a1-5e76021c286f` |
| `analise-probatoria-abdutiva` | vault **Criminal** | `d08c1d17-4d50-453b-be44-d2c715838b89` |
| `analise-probatoria-abdutiva` | vault **Eleitoral** | `d08c1d17-4d50-453b-be44-d2c715838b89` |
| `analise-probatoria-abdutiva` | `~/.claude/` | `d08c1d17-4d50-453b-be44-d2c715838b89` |
| `analise-probatoria-bayesiana` | vault **Criminal** | `70efeab1-40df-4644-83e8-868d1202250f` |
| `analise-probatoria-bayesiana` | vault **Eleitoral** | `70efeab1-40df-4644-83e8-868d1202250f` |
| `analise-probatoria-bayesiana` | `~/.claude/` | `70efeab1-40df-4644-83e8-868d1202250f` |
| `analise-probatoria-standards` | vault **Criminal** | `25d6e667-500a-470e-9e70-acd818da6d40` |
| `analise-probatoria-standards` | vault **Eleitoral** | `25d6e667-500a-470e-9e70-acd818da6d40` |
| `analise-probatoria-standards` | `~/.claude/` | `25d6e667-500a-470e-9e70-acd818da6d40` |
| `analise-probatoria-wigmore` | vault **Criminal** | `6d255d90-1475-4a59-a582-ba0e13c98456` |
| `analise-probatoria-wigmore` | vault **Eleitoral** | `6d255d90-1475-4a59-a582-ba0e13c98456` |
| `analise-probatoria-wigmore` | `~/.claude/` | `6d255d90-1475-4a59-a582-ba0e13c98456` |
| `analise-reconhecimento-pessoas` | vault **Criminal** | `ff66be9a-cfbe-4ef0-9fef-175cfc3094f3` |
| `analise-resposta-imobilidade-tonica` | vault **Criminal** | `29b37d18-e8bf-49e3-b246-c4a522f0ad49` |
| `analise-testemunho-infantil` | vault **Criminal** | `60f750db-3396-42e5-b1cc-5b4b86caceb3` |
| `analise-validade-metodo-pericial` | `~/.claude/` | `130f97d7-bb0e-46cd-a762-f436b09da632` |
| `analise-vies-confirmacao-investigativa` | vault **Criminal** | `7faae4b1-ddef-421e-a841-1e5b95226521` |
| `analise-vies-implicito-racial` | vault **Criminal** | `a081bc9c-bf4c-40ea-89d6-27dd862bbd8b` |
| `argumentacao-defeasivel` | vault **Criminal** | `aefebf29-2f9c-4aa4-bc02-b7109f7a8f44` |
| `avaliacao-risco-periculosidade` | vault **Criminal** | `b3335faf-d51c-4f2f-b3de-1a5ba34310b5` |
| `boletim-precedentes-stj` | `~/.claude/` | `4688b958-d033-4dfd-bebf-e359fe7695f9` · `9deca780-1a21-4362-83cd-669c4fc3e759` · `f2e4a886-fa20-43bc-8f7c-8a1d82ae77fd` |
| `cadeia-custodia-prova-digital` | vault **Criminal** | `3fd409ea-05d1-45e2-af52-136351041675` |
| `carl-rogers-pca` | vault **Psicologia** | `8c715fc1-e83a-4a6a-8f07-9fac510385a8` |
| `corroboracao-falsificacionista` | vault **Criminal** | `92efec4d-de9b-48e9-bf3b-d8beba52d0e1` |
| `corroboracao-falsificacionista` | vault **Eleitoral** | `92efec4d-de9b-48e9-bf3b-d8beba52d0e1` |
| `corroboracao-falsificacionista` | `~/.claude/` | `92efec4d-de9b-48e9-bf3b-d8beba52d0e1` |
| `corte-idh-brasil` | `~/.claude/` | `7a68591b-bbd7-46cf-a2fa-549841b81975` |
| `criminal-player` | vault **Criminal** | `00189a90-4159-45a6-8a63-b12a188edfb7` · `01e2d344-092d-49ab-baa6-4dfc6f321769` · `86545fac-bce1-499d-ab9d-7293eb6a93df` · `95e2931a-a58a-4992-a3d2-b4c785431e87` · `9fefd066-1bdd-4e04-9870-dc0a578c2d3e` · `c6009154-1e97-4c97-aff3-7309fc5ba9f9` · `ddbdb106-e9a9-444a-bc4f-a49365c8a9be` |
| `criminal-player` | `~/.claude/` | `00189a90-4159-45a6-8a63-b12a188edfb7` · `01e2d344-092d-49ab-baa6-4dfc6f321769` · `86545fac-bce1-499d-ab9d-7293eb6a93df` · `95e2931a-a58a-4992-a3d2-b4c785431e87` · `9fefd066-1bdd-4e04-9870-dc0a578c2d3e` · `c6009154-1e97-4c97-aff3-7309fc5ba9f9` · `ddbdb106-e9a9-444a-bc4f-a49365c8a9be` |
| `dialetica-atomista-holista` | vault **Criminal** | `e47007ed-1e4a-498f-9f92-dba23d84473a` |
| `dialetica-atomista-holista` | vault **Eleitoral** | `e47007ed-1e4a-498f-9f92-dba23d84473a` |
| `dialetica-atomista-holista` | `~/.claude/` | `e47007ed-1e4a-498f-9f92-dba23d84473a` |
| `direito-de-defesa` | vault **Criminal** | `e5cba24b-9c78-4173-b5fa-3b7dc4e31449` |
| `direito-de-defesa` | `~/.claude/` | `e5cba24b-9c78-4173-b5fa-3b7dc4e31449` |
| `direitos-fundamentais` | vault **Ambiental** | `5dfe7b9a-4935-49f7-9ad7-6d029989b661` |
| `direitos-fundamentais` | vault **Constitucional** | `5dfe7b9a-4935-49f7-9ad7-6d029989b661` |
| `direitos-fundamentais` | `~/.claude/` | `5dfe7b9a-4935-49f7-9ad7-6d029989b661` |
| `direitos-fundamentais-migalhas` | vault **Constitucional** | `8a007870-e0f9-462a-b72d-2cd3b68b9a90` |
| `doutrina-constitucional` | vault **Constitucional** | `9fe29741-7edc-40d1-bcc7-5f1cda89c032` |
| `doutrina-constitucional` | `~/.claude/` | `9fe29741-7edc-40d1-bcc7-5f1cda89c032` |
| `doutrina-penal-critica` | vault **Criminal** | `cfd7c963-8e12-405a-a2f0-6281567f5329` |
| `doutrina-penal-critica` | `~/.claude/` | `cfd7c963-8e12-405a-a2f0-6281567f5329` |
| `epistemologia-do-testemunho` | vault **Criminal** | `2532e5f9-f47d-4ac4-9576-e7c0c23e8814` |
| `informativo-tse` | vault **Eleitoral** | `245fd015-9e5b-4e93-ab67-3c9e5f79c2fc` · `2b904247-8693-499a-a87b-cc18c4b874f0` · `42ad973e-8eaa-4b81-894d-034e006a969e` · `72c946e0-fcd7-48d0-842e-7dd1af077e96` · `cb7ec492-a514-4a0b-bce1-0b3b4c37effa` |
| `informativo-tse` | `~/.claude/` | `245fd015-9e5b-4e93-ab67-3c9e5f79c2fc` · `2b904247-8693-499a-a87b-cc18c4b874f0` · `42ad973e-8eaa-4b81-894d-034e006a969e` · `72c946e0-fcd7-48d0-842e-7dd1af077e96` · `cb7ec492-a514-4a0b-bce1-0b3b4c37effa` |
| `informativos-stf` | `~/.claude/` | `cb154c24-d844-45bc-b659-592a1ab6684a` |
| `injustica-epistemica` | vault **Criminal** | `fb0eba5a-8050-4437-9391-5cb8ddb23162` |
| `irvin-yalom` | vault **Psicologia** | `f5509d65-2531-4922-8d7c-2b374a6f79ae` |
| `jurisprudencia-corpus` | vault **Constitucional** | `cb154c24-d844-45bc-b659-592a1ab6684a` |
| `jurisprudencia-corpus` | `~/.claude/` | `cb154c24-d844-45bc-b659-592a1ab6684a` |
| `justo-processo` | vault **Criminal** | `3fd409ea-05d1-45e2-af52-136351041675` |
| `justo-processo` | `~/.claude/` | `3fd409ea-05d1-45e2-af52-136351041675` |
| `leslie-greenberg` | vault **Psicologia** | `49a3a3ff-640f-49f9-a539-6152e49c0575` |
| `migalhas-criminais` | vault **Criminal** | `f4b221d3-9ad7-45fc-b140-78539fa1b615` |
| `neurodireito-responsabilidade-penal` | vault **Criminal** | `32526abb-c2e8-4dcf-b46f-6a9759ebca9b` |
| `nova-limite-penal` | vault **Criminal** | `5a64160d-e7b6-4bc8-82d0-f763818a2f9d` |
| `perspectivas-direito-penal` | vault **Criminal** | `82440107-2cbd-4c63-890b-eb8b88f7726d` |
| `rstj-stj` | `~/.claude/` | `515811b7-2be9-4f28-a09a-54efbfab820f` · `cc13ec8e-917b-4956-8051-68ff2b91a258` · `d6d12379-a1db-406f-b81d-00a794cae7f3` |
| `rtj-stf` | vault **Constitucional** | `23559e60-804b-46fc-97ec-d7aeea131bd4` **(apagado)** · `a01e1821-48bd-4c80-880a-d00c29617255` **(apagado)** · `a35d98d9-8a0f-4c29-826e-da9e5a981291` **(apagado)** |
| `rtj-stf` | `~/.claude/` | `23559e60-804b-46fc-97ec-d7aeea131bd4` **(apagado)** · `a01e1821-48bd-4c80-880a-d00c29617255` **(apagado)** · `a35d98d9-8a0f-4c29-826e-da9e5a981291` **(apagado)** |

> **16 agentes do registry existem em mais de um escopo.** Duplicata **diverge em
> silêncio** quando editada de um lado só — e nada avisa, porque as duas resolvem.
>
> **Não conclua daqui que é resíduo a apagar.** Auditoria de 2026-07-28 comparou os 269 pares
> de agente e skill dos cofres Classe A: **106 eram cópia morta** (idêntica ou divergindo só em
> linha de caminho), mas **99 eram fork de domínio** — o `jurisprudencia-stj-stf` do Eleitoral,
> por exemplo, tem um bloco inteiro de matéria eleitoral que a global não tem — e **28 são
> compartilhados** entre dois cofres, de modo que apagar do global os desliga de ambos. Pior:
> em **96 dos 99 forks a cópia GLOBAL estava mais nova**, o que inverte o diagnóstico — ali o
> defasado é o cofre. Antes de remover qualquer par, classifique: idêntico × só-caminho ×
> substantivo, e confira a data dos dois lados.
>
> **Vault × `~/.claude/` (16):** **Ambiental** 1 · **Constitucional** 4 · **Criminal** 11 · **Eleitoral** 8. Num cofre Classe A isto é **resíduo de promoção**, salvo se o recurso for
> transversal (norma §1.2), caso em que a duplicata é deliberada.
>
> **Entre cofres, sem passar pelo global (8):** `analise-narrativista` · `analise-probatoria-abdutiva` · `analise-probatoria-bayesiana` · `analise-probatoria-standards` · `analise-probatoria-wigmore` · `corroboracao-falsificacionista` · `dialetica-atomista-holista` · `direitos-fundamentais`. Aqui é compartilhamento entre domínios — legítimo, mas cada cópia envelhece sozinha.

Acervos com vários notebooks por período (IDs no arquivo):

- `criminal_player` → `~/.notebooklm/criminal_player/notebooks_ids.txt`
- `senso_incomum` → `~/.notebooklm/senso_incomum/notebooks_ids.txt`

## Corpora locais (`~/.notebooklm/<acervo>/fontes/`)

| Acervo | Arquivos |
|---|---|
| `clone_jurisprudencia` | 70 |
| `coletanea_tse` | 22 |
| `constituicao_supremo` | 8 |
| `corte_idh` | 27 |
| `criminal_player` | 554 |
| `critica_penal` | 37 |
| `depoimento_especial` | 2 |
| `direito_de_defesa` | 140 |
| `direitos_fundamentais` | 202 |
| `ementa_cnj` | 2 |
| `informativo_stf` | 13 |
| `informativo_stj` | 835 |
| `informativo_tse` | 674 |
| `justo_processo` | 117 |
| `manuais_custodia` | 13 |
| `manuais_pericia` | 24 |
| `migalhas_criminais` | 32 |
| `migalhas_direitos_fundamentais` | 35 |
| `nova_limite_penal` | 10 |
| `perspectivas_direito_penal` | 11 |
| `ristj_343a` | 2 |
| `rstj` | 303 |
| `senso_incomum` | 749 |
| `validade_pericial` | 24 |

## Biblioteca (obras em PDF/HTML e sua versão Markdown)

`~/.notebooklm/biblioteca/` — **209 originais** em `pdf/` e `html/`, **208 convertidos** em `md/`.
Cada página do PDF vira `## [p. N]` no Markdown: a página devolvida por um helper
(`consultar_constituicao_supremo.py`, `consultar_cadh_stf.py`, `consultar_obra_tematica.py`)
resolve direto no `.md` — leia o Markdown em vez de abrir o PDF.

| Grupo | Arquivos |
|---|---|
| `md/Biblioteca-STF/` | 6 |
| `md/boletins_precedentes_stj/` | 138 |
| `md/Cadernos-STF/` | 9 |
| `md/SNE-admin/` | 8 |
| `md/SNE-TSE/` | 1 |
| `md/` (raiz — obras avulsas) | 46 |

Verificação da conversão (páginas, chars/página, NUL, OCR pendente):
`~/.notebooklm/biblioteca/RELATORIO-CONVERSAO.md`. Reconverter:
`python ~/.notebooklm/tools/converter_biblioteca_md.py --origem <pasta>`.

## Pipelines

- **Pesquisa pesada sem gastar contexto** — skill `notebooklm`: cria notebook, sobe fontes, pergunta, e só o destilado com citação volta para a Wiki. Slash `/pesquisar-notebooklm`.
- **Dado recente ou disperso na web** — MCP `mcp__perplexity__*` (`_search` fatos/URLs · `_ask` resposta com citação · `_reason` raciocínio em etapas · `_research` multi-fonte). Slash `/pesquisa-perplexity`.
- **PDF escaneado → Markdown** — watcher em `~/.notebooklm/` (Tesseract/Ghostscript) ou `converter_pdf_ocr.py`. Compare o tamanho antes de destilar: conversão perde conteúdo em silêncio.
- **Página, tamanho e tarja em PDF** — `tools/pdf_ops.py` (PyMuPDF, sem servidor; Tesseract/Ghostscript via `pdf2md/ambiente.py`). Skill `/pdf-ops`. `info` (quantas páginas são digitalizadas) · `juntar` · `dividir --tamanho 10MB` (limite de upload do PJe; `--cada N`, `--paginas 1-50,51-`) · `comprimir` · `redigir --termos … --identificadores [--ocr]` (tarja QUEIMADA de nomes, CPF, CNPJ, e-mail, telefone; página digitalizada só com `--ocr`; os nomes do mapa do `anonimizar.py` servem de `--termos-arquivo`) · `girar` · `extrair` · `pdfa` (Ghostscript do PDF24). Nunca sobrescreve a entrada; exit 3 = termo não encontrado, página digitalizada sem OCR ou parte que não coube. NÃO converte PDF em Markdown (isso é `pdf2md`). Stirling-PDF foi avaliado e descartado em 2026-09-07: não pagina e o OCR só roda em servidor Java.
- **Saída .docx** — skill `docx-juridico-padrao` (Sitka Text 12, entrelinha 1,16, 6 pt depois, margens 2 cm; citação em bloco recuado 2 cm com Segoe UI 12/1,08). Só fuja do padrão a pedido explícito.
- **Nota-tese** — slash `/tese`: cruza vocabulário → norma → jurisprudência → doutrina, cada camada com citação, e rotula norma × jurisprudência × doutrina.
- **Autos do PJe → atos → índice híbrido → recuperação citável** (espec `~/.notebooklm/ESPEC-INTELIGENCIA-JURIDICA-CRIMINAL.md`):
  1. `pdf2md` perfil PJe (ou `pdf_para_markdown.py`) → `.md` paginado `## [p. N]`;
  2. `fatiar_atos.py <vol01.md> [vol02.md …] --cnj <CNJ>` → um `.md` por ato processual (fronteira = `Num. X - Pág. N` + assinatura, OCR do id tolerado), `atos.jsonl`, `relatorio_fatiamento.md`;
  3. `.venv-rag314/Scripts/python indexar.py casos --extracted <pasta>/extracted` → SQLite FTS5 + LanceDB/bge-m3, um chunk por página, em `%LOCALAPPDATA%\cerebro\casos.*` (**fora do OneDrive**; corpora públicos vão para `vault.*` com `indexar.py vault --pasta … --colecao …`);
  4. `.venv-rag314/Scripts/python buscar.py casos "<pergunta>" --cnj <CNJ> [--tipo DECISAO] [--json]` → FTS5 ∪ vetorial → reranker `bge-reranker-v2-m3` → top-k prefixado `[ID <id_pje> | <vol> p. <n> | <tipo> | <data>]`. A minuta só cita o que veio daqui; o validador de fontes confere o prefixo.
  5. distiladores sem LLM sobre o `atos.jsonl`: `cronologia_atos.py` (linha do tempo por ato + `marcos.json`: recebimento, audiência, sentença, trânsito, lidos do tipo e do texto na forma afirmativa) · `prazo_cpp.py --atos …` (radar de prazos da defesa em dias corridos, CPP 798, Súm. 310/710 STF, rito detectado na capa; `--intimacao D --dias N` calcula um prazo; `--comarca` liga feriado municipal) · `prescricao_cp.py --dispositivo lei9605:50 --fato D --atos …` (CP 109-117, pena lida do dataset do artigo, marcos do `marcos.json`, `--pena-concreta` para CP 110 §1º). Feriados em `calendario_forense.py`.
  6. `distilar_atos.py atos.jsonl [--distiladores controversia,nulidades,prisao,dosimetria]` → LLM local (qwen3:8b, temperatura 0, JSON com schema do Ollama, um ato por chamada, trecho literal conferido) grava `distill/llm/*.json` e `distill/{controversia,nulidades,prisao,dosimetria}.md`; atos acima do teto vão para `distill/para_nuvem.json`. O local EXTRAI, não julga: vícios/nulidades são do agente `auditoria-nulidades-criminal`.
  7. nuvem: `anonimizar.py --cnj X --capa … --denuncia … [--nomes …] [--termos …]` monta o mapa de pseudônimos (fora do OneDrive) e `llm_nuvem.py --tier forte|longo|barato|nacional --cnj X --arquivo … [--dry-run]` anonimiza → chama (tiers em `config_llm.json`, `data_collection: deny`) → reverte, logando só hash/tokens/custo em `relatorios/llm-log.jsonl`. Chaves só por variável de ambiente (`OPENROUTER_API_KEY`, `FCC_PROXY_TOKEN`, `MARITACA_API_KEY`).
  8. gate pós-inferência: `validar_minuta.py minuta.md --atos <extracted>/atos.jsonl --peca resposta-acusacao|memoriais|apelacao|hc|rese|resp|re|… [--rito jecrim] [--intimacao D]` → `validador_fontes.py` (súmulas, temas de RG, artigos dos datasets, precedentes/temas por busca literal nos corpora, informativos, IDs e páginas do caso; marcador inline `[VERIFICAÇÃO NECESSÁRIA: …]`) + `validador_processual.py` (nulidade→pedido, pedido→fundamentação, rito, honorários em peça criminal, rol de testemunhas, prequestionamento/RG, tempestividade, âncoras) → `*.validada.md`, dois relatórios, `*.citacoes_para_verificar.json` para o agente `verificador-citacoes`. Só APROVADO vai ao .docx; 'não localizada' nunca é 'não existe'.
  Seletores do PJe (TJMA = método `pje4`) lidos da extensão MinutaIA Conecta: `tools/pje_seletores_conecta.json`. Benchmark do LLM local: `Criminal/40-Recursos/benchmark-llm-local.md`.

## Recursos do Claude Code — os dois escopos

**Escopo de usuário (`~/.claude/`) — vale em qualquer vault:**

- **186 agentes** em `~/.claude/agents/` — descobertos por intenção; a descrição de cada um já diz quando acioná-lo. Não replique catálogo de agente em `CLAUDE.md`.
- **115 skills** em `~/.claude/skills/`.
- **84 slash commands** em `~/.claude/commands/`.

**Escopo de vault (`<vault>/.claude/`) — 13 cofres com infra própria.**
Só acionável com o Claude Code iniciado **na raiz do vault**; o que é local sombreia o global
de mesmo nome. Classe **A** guarda tudo dentro de si e sobrevive a um `git clone` sozinho;
classe **B** é casca em torno do global e declara as dependências em `REQUISITOS-EXTERNOS.md`
(norma: `~/.notebooklm/PADRAO-VAULT.md` §1).

| Vault | Classe | Agentes | Skills | Slashes | Helpers |
|---|---|---|---|---|---|
| Ambiental | **A** — autossuficiente | 14 | 11 | 38 | 14 |
| Constitucional | **A** — autossuficiente | 16 | 16 | 50 | 23 |
| Criminal | **A** — autossuficiente | 73 | 136 | 50 | 38 |
| Dissertacao | B — leve | 0 | 1 | 6 | 0 |
| Eleitoral | **A** — autossuficiente | 26 | 8 | 66 | 19 |
| ExecucaoPenal | B — leve | 1 | 2 | 7 | 1 |
| Familia | B — leve | 0 | 1 | 8 | 0 |
| JuntaMedica | B — leve | 0 | 1 | 0 | 0 |
| Longevidade | B — leve | 0 | 1 | 0 | 0 |
| MestradoCeuma | B — leve | 0 | 1 | 1 | 0 |
| ProcessoCivil | B — leve | 1 | 2 | 7 | 1 |
| Psicologia | **A** — autossuficiente | 7 | 10 | 6 | 5 |
| Trabalhista | **A** — autossuficiente | 8 | 2 | 16 | 5 |

