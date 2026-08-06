# RSTJ — Revista do Superior Tribunal de Justiça (1989–2024)

Corpus local de **inteiro teor** do STJ desde a instalação do Tribunal.
É a única fonte do acervo que alcança os anos 90: os Informativos do STJ só
começam em 1998 e são **resumo**; aqui há ementa, acórdão, relatório, votos e
notas taquigráficas.

| | |
|---|---|
| Arquivos | 303 `.md` (`fontes/`) |
| Cobertura | 1989–2024, v. 1–274 (volumes grandes vêm partidos em tomos `_1`, `_2`) |
| Páginas | 182.325 |
| Caracteres | 389.096.544 |
| Acórdãos | ~19.132 (cabeçalho único por volume) |
| Índice | `rstj_volumes.tsv` — uma linha por volume |
| Helper | `~/.notebooklm/tools/consultar_rstj.py` |
| Gerador do índice | `~/.notebooklm/tools/gerar_indice_rstj.py` |

Sem lacuna de volume na faixa 1–274.

## Como chegou aqui

Convertido de PDF por `pdf2md` (PyMuPDF) em 2026-07-29, com paginação `## [p. N]`
e medição embutida no cabeçalho de cada arquivo. Ficou até 2026-08-05 em
`OneDrive\Ezzio Gabriel\RSTJ\MD`, fora do acervo canônico e como *placeholder*
online-only — cada busca full-text baixava 393 MB da nuvem. Movido para cá nessa
data, com conferência de nome, tamanho e hash.

## Três defeitos declarados

**1. Ordinal corrompido — 204 dos 303 volumes, todos entre 1989 e 2007.**
A conversão destruiu o `º`: gravou `art. 5º` como `art. 52`, `art. 5<sup>2</sup>`,
`art. 5!!` ou `art. 5~`. Onde o lixo tem forma (`<sup>2</sup>`, `!!`, `~`) dá para
reconhecer e o helper avisa; **onde virou dígito puro (`art. 52`) não há como
distinguir do artigo 52 de verdade.**

> Consequência prática: **não cite dispositivo literal de volume anterior a 2008
> sem conferir a página no PDF oficial.** A ementa e o raciocínio do acórdão
> continuam confiáveis; o *número do dispositivo* não.

Não há conserto a partir do `.md` — só reconvertendo do PDF do STJ. A coluna
`ordinal_ok` do índice marca volume a volume, e `consultar_rstj.py --so-integros`
exclui os afetados.

É o mesmo tipo de estrago que os Informativos do STJ sofreram na conversão de RTF
(acento virando `?`), corrigido por `rtf_stj_para_md.py` — com a diferença de que
lá o original preservava a informação e aqui não.

**2. Páginas não transcritas — 202 volumes.**
Ao menos uma página chegou só como imagem (capa, folha de rosto, fac-símile). O
cabeçalho de cada `.md` lista quais. Ausência de trecho nessas páginas não prova
ausência de conteúdo.

**3. PDFs de origem ausentes.**
Não estão nesta máquina. O aviso "consulte o PDF original" que o conversor deixou
aponta para www.stj.jus.br, não para disco local. As referências a imagens
(`*_imagens/pNNNN_img01.png`) também são links mortos.

## Regra de citação

Citar sempre pela referência oficial do periódico, que o índice guarda nas colunas
`ref_*`: `R. Sup. Trib. Just., Brasília, v. N, n. N, p. X-Y, mês ano.` — mais a
página `## [p. N]` do trecho, que o helper devolve.

A RSTJ é registro **histórico**: o julgado pode estar superado por lei, emenda,
súmula ou virada da Corte. O helper nunca apresenta achado como posição vigente.
