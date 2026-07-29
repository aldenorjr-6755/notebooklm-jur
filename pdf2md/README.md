# pdf2md — conversor de PDF para Markdown

Aplicativo de conversão de PDFs em Markdown paginado, feito para os quatro
tipos de documento que passam por aqui: **processos do PJe**, **livros**,
**decisões judiciais** e **laudos periciais com imagens**.

Implementa a regra canônica de `~/.claude/CLAUDE.md` ("Conversão de fontes
para Markdown"): PyMuPDF, paginação `## [p. N]` e **medição da perda antes
de destilar**.

---

## Standalone (executável, sem Python instalado)

```bash
python -m pdf2md.empacotar --limpar
```

Gera `dist/pdf2md/` (~430 MB), com o **Tesseract e o idioma português embutidos** —
a pasta roda em qualquer Windows, copiada para onde for:

| Arquivo | Para quê |
|---|---|
| `pdf2md.exe` | duplo-clique: abre a janela, sem console atrás |
| `pdf2md-cli.exe` | linha de comando |

Opções: `--onefile` (arquivo único, parte mais devagar porque descompacta a cada
uso), `--sem-tesseract` (pacote leve, mas exige Tesseract instalado),
`--idiomas por,eng`.

Ao final, o empacotador **verifica o próprio pacote** (`--autoteste`): confere as
dependências, o OCR em português e monta a janela sem exibi-la. Se algo faltar,
ele avisa `PACOTE COM DEFEITO` em vez de entregar um build quebrado — isso existe
porque um build saiu com a janela quebrada e a linha de comando intacta, e o
defeito só apareceria no primeiro duplo-clique.

Verificado: a saída do `.exe` é **idêntica** à do código-fonte nos quatro tipos de
documento, e a pasta funciona realocada e com o `PATH` limpo.

---

## Como usar

### Janela (aplicativo)

```bash
PDF2MD.bat
```

ou `python -m pdf2md --gui`. Arraste os PDFs pelo botão *Adicionar*, escolha
o perfil e clique em **CONVERTER**. A conversão roda em segundo plano e pode
ser cancelada a qualquer momento.

### Linha de comando

```bash
python -m pdf2md ARQUIVO.pdf
python -m pdf2md "C:\autos" -o "C:\saida" --perfil pje -r
python -m pdf2md laudo.pdf --perfil laudo
python -m pdf2md autos.pdf --check
python -m pdf2md --diagnostico
```

### Como biblioteca

```python
from pdf2md import converter, converter_lote, coletar_pdfs

r = converter("laudo.pdf", perfil="laudo")
print(r.chars, r.paginas_ocr, r.paginas_vazias)
```

---

## Perfis

| Perfil | O que faz |
|---|---|
| `auto` | Inspeciona o PDF e escolhe o perfil sozinho (padrão). |
| `pje` | Autos digitais: OCR só nas páginas digitalizadas, remoção do rodapé de assinatura eletrônica e **índice dos documentos** do processo (`Num.` / `Id.`). Modo rápido, para autos de milhares de páginas. |
| `livro` | Obra longa: hierarquia de títulos, tabelas e **sumário a partir dos bookmarks** do PDF. |
| `decisao` | Sentença, acórdão, despacho: estrutura preservada e paginação. |
| `laudo` | Laudo técnico: **extrai as figuras** para `<nome>_imagens/` e as referencia no ponto exato da página; OCR a 400 dpi com realce. |

Os perfis são só um ponto de partida — qualquer opção pode ser sobrescrita
(`--ocr`, `--idioma`, `--dpi`, `--imagens`, `--rapido`, `--limpar-rodape`),
ou, na janela, marcando *"Ajustar as opções manualmente"*.

---

## O que a ferramenta garante

- **O PDF original nunca é alterado nem apagado.**
- **A paginação vira `## [p. N]`** — toda citação é conferível contra a
  página do PDF.
- **A perda é medida e declarada** no cabeçalho de cada `.md`: caracteres
  extraídos, média por página, quanto veio de OCR, quantas imagens saíram,
  quantas linhas de rodapé foram removidas e **quais páginas ficaram por ler**.
  Conversão PDF→MD perde conteúdo em silêncio; aqui ela não perde calada.
- **A medição desconta o carimbo do PJe.** Uma página digitalizada de autos
  traz `Num. 57493199 - Pág. 1` em texto *nativo*: 20-70 caracteres que fazem
  qualquer contagem bruta concluir "página íntegra". Aqui o que conta é o texto
  **restante depois de descontar o carimbo** (60 caracteres), cruzado com a
  fração da página coberta por imagem — o que separa folha em branco de
  digitalização não lida.
- **Página digitalizada é marcada** com `` `OCR` `` ao lado do número, para
  que se saiba que aquele trecho passou por reconhecimento óptico e merece
  conferência.

### Códigos de saída (linha de comando)

| Código | Significado |
|---|---|
| 0 | Convertido, nenhuma página por ler. |
| 1 | Houve erro em algum arquivo. |
| 3 | Sobrou página não lida — repita com `--ocr sempre --dpi 400`. |

### O caso que originou a medição por texto útil

Num processo de 365 páginas, **83 (23%) eram imagem sem OCR** — entre elas a
ata de audiência, peça nuclear da controvérsia — e a conversão declarou
"nenhuma página ficou sem texto". O carimbo bastava para enganar a contagem.
Hoje esse arranjo é um **teste de regressão** (`--autoteste` monta um scan
carimbado e reprova se o OCR não disparar, ou se a página não for acusada
quando o OCR está desligado), executado a cada empacotamento.

---

## Decisões técnicas que valem registro

**O OCR interno do `pymupdf4llm` fica desligado de propósito.** Ele usa
RapidOCR e **ignora o parâmetro `ocr_language`**: sobre texto em português
devolve `RELATORIO`, `Contradicao`, `Obito`, `Ant6nio` — perde todo acento
sem avisar. Aqui o OCR é sempre o **Tesseract com o idioma do perfil**
(`por` por padrão), o que devolve `RELATÓRIO`, `Contradição`, `Óbito`.

**O censo da camada de texto é feito antes de tudo.** A extração estruturada
do `pymupdf4llm` **muta o documento em memória** (injeta o texto que ela
mesma reconhece); depois disso, `get_text` já não distingue página
digitalizada de página nativa. Medir antes é o que mantém honesto o número
de páginas convertidas por OCR.

**O OCR é seletivo por página**, não pelo arquivo. Num processo com 1.800
páginas em que 300 são digitalizadas, só essas 300 são renderizadas e
reconhecidas — e o PDF de origem não é reescrito.

**A imagem que é a própria digitalização da página não é extraída** como
figura (heurística: ocupa mais de 85% da página numa página sem camada de
texto), e figuras repetidas (logo, brasão) são deduplicadas por hash.

**O OpenCV foi removido do caminho crítico.** Ele entrava só para calcular um
limiar de Otsu antes do OCR — 112 MB para uma conta de histograma. O mesmo
limiar sai em NumPy puro, com resultado idêntico ao do `cv2.THRESH_OTSU` nas
páginas testadas.

**No empacotamento, `onnxruntime` NÃO é excluído.** O `pymupdf4llm` importa
`helpers.document_layout` já no seu `__init__`, e isso puxa `pymupdf.layout`,
que precisa dele. Excluí-lo fazia o `import pymupdf4llm` falhar dentro do
`.exe` — e, como a falha era tratada com degradação silenciosa, o executável
passava a gerar um Markdown diferente do que o mesmo PDF gerava no fonte. Hoje
essa degradação, se acontecer, sai declarada no cabeçalho do `.md`.

**A deduplicação das DLLs do Tesseract é por lista explícita.** O PyInstaller
copia para a raiz do bundle as DLLs que chegam via `datas`, duplicando 126 MB.
Uma primeira versão removia da raiz tudo que viesse da pasta do Tesseract — e
levou junto o `zlib1.dll`, do qual o `tcl86t.dll` depende: a conversão por
linha de comando continuava perfeita e **a janela deixava de abrir**. DLL
pequena e de nome genérico é compartilhada; só `libtesseract-5.dll` e
`libicudt75.dll` são exclusivas.

---

## Ambiente

`python -m pdf2md --diagnostico` mostra o estado das dependências. Nesta
máquina o Tesseract e o Ghostscript ficam **fora do PATH** — o módulo
`ambiente.py` os localiza e publica no PATH do processo automaticamente.

Requisitos: PyMuPDF, pymupdf4llm, pytesseract, Pillow (OpenCV e NumPy são
opcionais, usados só no realce de imagem antes do OCR). Tesseract com o
pacote `por` é necessário para OCR.

---

## Relação com os outros conversores

| Ferramenta | Papel |
|---|---|
| `pdf_para_markdown.py` | Conversor mínimo original: paginação e medição, sem OCR. Continua válido para PDF de texto nativo. |
| `pdf_watcher.py` | Vigia a pasta de Downloads e converte o que cair lá (OCRmyPDF sobre o arquivo inteiro). |
| ~~`pdf2md_app*/`~~ | Três tentativas anteriores (PyMuPDF4LLM, Tesseract e Marker), ~1,15 GB. **Apagadas em 2026-07-27**, substituídas por esta. Viviam fora do git — foi por isso que o `pdf2md/` entrou na lista de permissão do `.gitignore`. |
| **`pdf2md`** | Aplicativo completo: perfis por tipo de documento, OCR seletivo por página em português, extração de imagens, índice do PJe, janela, lote e executável standalone. |
