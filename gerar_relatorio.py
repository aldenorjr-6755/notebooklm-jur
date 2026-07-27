# -*- coding: utf-8 -*-
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUT = r"C:\Users\alden\.notebooklm\Relatorio_Defesa_Legista_Fabio_Magalhaes.pdf"

# ---- Paleta Claude ----
CORAL   = colors.HexColor("#D97757")   # coral/terracota (cor de assinatura Claude)
CORAL_D = colors.HexColor("#B14F30")   # coral escuro
TINTA   = colors.HexColor("#2B2A27")   # texto (cinza-quente escuro)
CINZA   = colors.HexColor("#6B655C")   # secundário
CREME   = colors.HexColor("#F5F2EB")   # fundo creme claro
CREME_D = colors.HexColor("#EDE8DD")   # creme um pouco mais escuro

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("TituloPrincipal", parent=styles["Title"],
    fontName="Helvetica-Bold", fontSize=17, textColor=CORAL_D, spaceAfter=6,
    leading=21, alignment=TA_CENTER))
styles.add(ParagraphStyle("Subtitulo", parent=styles["Normal"],
    fontName="Helvetica", fontSize=11, textColor=TINTA, alignment=TA_CENTER,
    spaceAfter=4, leading=15))
styles.add(ParagraphStyle("MetaInfo", parent=styles["Normal"],
    fontName="Helvetica", fontSize=9.5, textColor=CINZA, alignment=TA_CENTER,
    spaceAfter=2, leading=13))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"],
    fontName="Helvetica-Bold", fontSize=12.5, textColor=CORAL_D, spaceBefore=16,
    spaceAfter=6, leading=16))
styles.add(ParagraphStyle("Corpo", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10.5, alignment=TA_JUSTIFY, spaceAfter=8, leading=15, textColor=TINTA))
styles.add(ParagraphStyle("Citacao", parent=styles["Normal"],
    fontName="Helvetica-Oblique", fontSize=10, alignment=TA_JUSTIFY, leading=14.5,
    leftIndent=18, rightIndent=10, spaceBefore=2, spaceAfter=8, textColor=TINTA))
styles.add(ParagraphStyle("RotuloFonte", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=9.5, textColor=CORAL_D, spaceBefore=4,
    spaceAfter=1, leading=13))
styles.add(ParagraphStyle("Rodape", parent=styles["Normal"],
    fontName="Helvetica-Oblique", fontSize=8.5, textColor=CINZA, alignment=TA_JUSTIFY,
    leading=12))
styles.add(ParagraphStyle("TOCTitulo", parent=styles["Heading1"],
    fontName="Helvetica-Bold", fontSize=14, textColor=CORAL_D, spaceAfter=10))
toc_lvl0 = ParagraphStyle("TOC0", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10.5, textColor=TINTA, leading=20, leftIndent=6)


class RelatorioDoc(BaseDocTemplate):
    """DocTemplate que notifica entradas de sumário a partir dos cabeçalhos."""
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "H2":
            txt = flowable.getPlainText()
            key = "h2-" + "".join(c for c in txt if c.isalnum())[:24]
            self.canv.bookmarkPage(key)
            self.notify("TOCEntry", (0, txt, self.page, key))


def cit(texto):
    p = Paragraph(texto, styles["Citacao"])
    t = Table([[p]], colWidths=[16.0 * cm])
    t.setStyle(TableStyle([
        ("LINEBEFORE", (0, 0), (0, -1), 2.4, CORAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, -1), CREME),
    ]))
    return t


story = []
def H(t): story.append(Paragraph(t, styles["H2"]))
def P(t): story.append(Paragraph(t, styles["Corpo"]))
def R(t): story.append(Paragraph(t, styles["RotuloFonte"]))
def Q(t): story.append(cit(t)); story.append(Spacer(1, 2))

# ===== Capa / cabeçalho =====
story.append(Spacer(1, 6))
story.append(Paragraph("RELATÓRIO DETALHADO", styles["TituloPrincipal"]))
story.append(Paragraph(
    "Estratégias da Defesa de Carlos Alberto Silva em Relação ao Legista "
    "Dr. Fábio Antônio Costa Alves Magalhães", styles["Subtitulo"]))
story.append(Spacer(1, 8))
story.append(Paragraph("<b>Processo nº</b> 0036508-74.2009.8.10.0001", styles["MetaInfo"]))
story.append(Paragraph("<b>Vítima:</b> Kátia Francisca Moraes Silva", styles["MetaInfo"]))
story.append(Paragraph("<b>Perito/Legista:</b> Dr. Fábio Antônio Costa Alves Magalhães", styles["MetaInfo"]))
story.append(Spacer(1, 8))
story.append(HRFlowable(width="100%", thickness=1.4, color=CORAL, spaceAfter=12))

# ===== Sumário =====
story.append(Paragraph("Sumário", styles["TOCTitulo"]))
toc = TableOfContents()
toc.levelStyles = [toc_lvl0]
toc.dotsMinLevel = 0
story.append(toc)
story.append(PageBreak())

# ===== Conteúdo =====
H("Síntese")
P("A defesa estruturou sua atuação sobre o eixo de <b>descredibilizar a perícia "
  "médico-legal</b>, explorando falhas, ambiguidades e contradições nos documentos "
  "produzidos pelo Dr. Fábio Magalhães e em suas declarações em juízo. Essas "
  "inconsistências foram utilizadas para (i) afastar a autoria, (ii) sustentar a "
  "tese de suicídio, (iii) fortalecer o álibi do réu e (iv) obter a anulação da "
  "primeira condenação proferida pelo Tribunal do Júri.")

H("1. Contradição entre o Atestado de Óbito e o Laudo Cadavérico")
P("A defesa apontou discrepância formal nos documentos assinados pelo próprio "
  "legista: o <b>atestado de óbito</b> fixava a morte na noite de domingo "
  "(21h de 12/07/2009), enquanto o <b>laudo cadavérico original</b>, com base em "
  "&ldquo;rigidez cadavérica parcial&rdquo;, apontava a madrugada de segunda-feira "
  "(&asymp; 03h45 de 13/07).")
R("Petição da Defesa (Resposta à Acusação):")
Q("&ldquo;O Exame Cadavérico de fls. 31 declina o seguinte: <b>'rigidez cadavérica "
  "parcial, indicando tempo de morte superior a dezoito horas, tomando como base o "
  "momento da necropsia, realizada às vinte e uma horas e quarenta e cinco minutos "
  "do dia treze de julho de dois mil e nove;'</b> (sic)&rdquo;")
Q("&ldquo;Pode-se inferir, por uma simples conta aritmética que a vítima veio a óbito "
  "ás 03:45 horas da madrugada do dia 13.07.2009 [&hellip;] Havendo, inclusive, "
  "contradição com o Atestado de Óbito, fls. 24, FIRMADO pelo médico Fábio Antonio "
  "C. A. Magalhães, atestando que a morte de KÁTIA FRANCISCA ocorreu <b>às 21horas "
  "do dia 12 de julho de 2009</b>&rdquo;")
R("Laudo Cadavérico Original (assinado pelo legista):")
Q("&ldquo;rigidez cadavérica parcial, indicando tempo de morte superior a dezoito "
  "horas, tomando como base o momento da necrópsia, realizada às vinte e uma horas "
  "e quarenta e cinco minutos do dia treze de julho de dois mil e nove&rdquo;")
R("Sustentação oral da defesa em audiência:")
Q("&ldquo;A dúvida eh da seguinte forma. O atestado emitido pelo pelo cartório consta "
  "que <b>a Cátia faleceu às 21 horas do dia 12 de julho</b>, né? [&hellip;] A gente "
  "tem que saber o horário realmente preciso, se ela faleceu às 21 hor de julho ou "
  "às 3:45 do dia 13 de julho, que como consta também no laudo&hellip;&rdquo;")

H("2. Incompatibilidade do horário da morte com os registros telefônicos")
P("Usando o horário-limite do próprio laudo (03h45 de 13/07), a defesa cruzou o dado "
  "com a quebra de sigilo telefônico, mostrando que o celular da vítima movimentou "
  "chamadas <i>depois</i> do óbito atestado.")
R("Petições da Defesa:")
Q("&ldquo;Nessa intimidade, consta <b>uma ligação do dia 13.07.09, às 06:38:39 horas, "
  "FEITA PELA VÍTIMA ao referido celular o que leva a crer que a HORA/DATA da morte "
  "da vítima descrita acima não é verdadeira</b>, fato que merece ser investigado "
  "para que não se cometa precipitações como a que ocorreu com a presente denúncia "
  "ministerial&rdquo;")
Q("&ldquo;O fato insólito é que no 13 de julho, já na segunda-feira, <b>a vítima fez "
  "mais uma ligação para o número de MARCELO HENRIQUE GUIMARÃES CARVALHO, concluindo "
  "que a vítima ainda estava viva, quando a perícia já confirmava o seu óbito desde "
  "as 21:00 horas do dia 12, levando a crer que a perícia é uma prova extremamente "
  "falha</b>, não se prestando para ser o esteio da denúncia ministerial&hellip;&rdquo;")
R("Sustentação oral da defesa em audiência:")
Q("&ldquo;O que mais deixou a gente dúvida é que <b>após essa data, esse horário do "
  "óbito, ela continua recebendo ligação do seu Marcelo</b>. [&hellip;] A bem que ela "
  "fez a ligação do número dela é 6:38 do dia 6 e falou 5 segundos com essa pessoa. "
  "Então qual foi o horário que ela realmente faleceu?&rdquo;")

H("3. Precipitação do legista quanto à causa mortis (suicídio &times; homicídio)")
P("O legista inicialmente declarou &ldquo;enforcamento&rdquo; (compatível com a tese "
  "defensiva de suicídio da vítima, que sofria de depressão) e depois alterou para "
  "&ldquo;estrangulamento&rdquo; (homicídio). Em audiência, a defesa o levou a admitir "
  "a &ldquo;precipitação&rdquo;.")
R("Interrogatório / depoimento do legista em juízo:")
Q("<b>Defesa/Juízo:</b> &ldquo;O senhor pode ler, por favor. O que que o senhor tá "
  "lendo aí? [&hellip;]&rdquo;<br/><b>Legista:</b> &ldquo;<b>Ah, por por enforcamento, "
  "né, que nós botamos esse documento.</b>&rdquo;<br/><b>Defesa/Juízo:</b> &ldquo;Então "
  "a palavra enforcamento tá consignada no atestado de óbito duas vezes.&rdquo;<br/>"
  "<b>Legista (admitindo a falha):</b> &ldquo;<b>A gente inicialmente você até por uma "
  "questão da precipitação, realmente de você emitir um laudo e tal, a gente botou "
  "enforcamento.</b> Eu botei enforcamento, mas avaliando a viendo a complexidade me "
  "avaliando. Aí realmente a gente concluiu que foi o estrangulamento&rdquo;")
R("Conclusão final do Laudo Cadavérico (que embasou a denúncia):")
Q("&ldquo;Concluímos que KÁTIA FRANCISCA MORAES SILVA teve como <b>&lsquo;causa "
  "mortis&rsquo; asfixia por estrangulamento.</b>&rdquo;")

H("4. Nulidade do primeiro julgamento pelo &ldquo;novo laudo&rdquo; surpresa")
P("A impugnação mais contundente. Sete anos após o crime e na véspera do primeiro "
  "júri, o legista apresentou um <b>novo laudo</b> alterando o estado do corpo para "
  "&ldquo;rigidez total&rdquo;, deslocando a hora da morte para o intervalo de 09h45 "
  "a 17h45 de 13/07 &mdash; o que destruía o álibi. A defesa arguiu nulidade por "
  "violação ao <b>art. 479 do CPP</b> (juntada fora do prazo de 3 dias úteis), tese "
  "acolhida pelo TJMA.")
R("Petição da Defesa:")
Q("&ldquo;Julgamento anterior foi anulado <b>em razão do Médico Legista ter se "
  "dirigido até ao Juiz da Vara processante um dia antes do Julgamento anterior, e "
  "ter levado um novo exame cadavérico (sete anos depois do fato) para ser juntado "
  "aos autos, documento que mudava toda a dinâmica da acusação</b> e o eminente "
  "magistrado inacreditavelmente aceitou a juntada de tal documento aos autos, um dia "
  "antes do julgamento.&rdquo;")
R("Novo laudo apresentado pelo legista (datado na véspera do júri):")
Q("&ldquo;São Luís (MA), <b>08 de julho de 2016</b>. Dr. Fábio Antônio Costa Alves "
  "Magalhães Médico Legista&rdquo;")
R("Depoimento do legista tentando justificar a mudança:")
Q("&ldquo;A gente decidiu, <b>decidi pela minha avaliação mesmo e botar estabelecer "
  "entre 12 horas o máximo de o máximo de ocorrência do óbito</b>.&rdquo;<br/>"
  "&ldquo;O tempo limite a gente estabelece ali até 9:45 da manhã desse dia 13.&rdquo;")
R("Decisões judiciais / manifestações confirmando a anulação:")
Q("&ldquo;&hellip;o Tribunal de Justiça do Maranhão <b>acolheu a preliminar suscitada "
  "pela defesa, com fundamento no artigo 479 c/c no inciso IV, do artigo 564, ambos do "
  "CPB, anulando a sessão do JÚRI e determinando a submissão do acusado a um novo "
  "julgamento</b> pelo Tribunal do Júri.&rdquo;")
Q("&ldquo;&hellip;recorreu da sentença condenatória, apresentando razões, <b>visando "
  "que o julgamento fosse anulado por violação ao artigo 479 do CPP, consistente na "
  "juntada do laudo exame cadavérico na véspera do julgamento</b>&hellip;&rdquo;")

H("5. Impugnação da dinâmica de luta corporal atestada pelo legista")
P("O legista atestou escoriações na mão da vítima, indicando resistência. A defesa "
  "virou a própria conclusão pericial contra a acusação: se houve luta, o agressor "
  "teria marcas &mdash; e o réu não tinha nenhuma.")
R("Petição da Defesa:")
Q("&ldquo;Diz ainda o exame cadavérico que houve luta corporal, materializada na "
  "escoriação encontrada em uma das mãos da vítima. <b>Isso leva a crer que o seu "
  "algoz também estava com alguma escoriação, já que é próprio das vítimas, ao tentar "
  "se defender, partir para o ataque e produzir alguma lesão no seu carrasco. O "
  "acusado não possui nenhuma lesão/escoriação produzida pela vítima</b>, o que "
  "podemos concluir que ele não fora a pessoa que travou a luta corporal, mencionada "
  "no laudo.&rdquo;")
R("Laudo Cadavérico (base da refutação):")
Q("&ldquo;presença de pequena escoriação no dorso da mão direita, medindo meio "
  "centímetro de diâmetro, <b>indicando resistência da vítima</b>&rdquo;")

# ===== Fontes =====
story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", thickness=0.8, color=CORAL, spaceAfter=8))
H("Fontes consultadas no notebook")

dados = [
    ["Tipo", "Documento (fonte)"],
    ["Autos do processo\n(petições, laudos, atestado, decisões)",
     "0036508-74.2009.8.10.0001 — Volumes 01 a 07"],
    ["Depoimento do legista em juízo",
     "MÉDICO LEGISTA FÁBIO ANTÔNIO COSTA ALVES MAGALHÃES.mp3;\n"
     "Testemunha da Defesa Fábio Antônio Costa Alves.mp3"],
    ["Interrogatórios do réu",
     "ACUSADO CARLOS ALBERTO SILVA.mp3; CARLOS ALBERTO SILVA.mp3;\n"
     "RÉU CARLOS ALBERTO SILVA.mp3"],
    ["Perita criminal", "PERITA CRIMINAL LIDIANE FREITAS PEDROSO.mp3"],
    ["Testemunhas",
     "Depoimentos de defesa (Márcio José; Rogério Soares) e de acusação"],
]
cell = ParagraphStyle("cell", parent=styles["Normal"], fontName="Helvetica",
                      fontSize=9, leading=12, textColor=TINTA)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold",
                       textColor=colors.white)
tbl_data = []
for i, (a, b) in enumerate(dados):
    if i == 0:
        tbl_data.append([Paragraph(a, cellb), Paragraph(b, cellb)])
    else:
        tbl_data.append([Paragraph(a.replace("\n", "<br/>"), cell),
                         Paragraph(b.replace("\n", "<br/>"), cell)])
t = Table(tbl_data, colWidths=[5.5 * cm, 10.5 * cm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), CORAL),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREME_D]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8CFBE")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
]))
story.append(t)
story.append(Spacer(1, 10))
story.append(Paragraph(
    "<b>Observação técnica:</b> os marcadores numéricos de citação retornados pela "
    "consulta apontam para trechos internos do índice do NotebookLM e não correspondem "
    "diretamente à numeração de páginas/fls. dos autos. As referências de fls. "
    "(&ldquo;fls. 24&rdquo;, &ldquo;fls. 31&rdquo;) são as que constam literalmente no "
    "texto das próprias petições transcritas acima.", styles["Rodape"]))


def rodape(canvas, doc):
    canvas.saveState()
    # faixa creme no topo
    canvas.setFillColor(CREME)
    canvas.rect(0, A4[1] - 0.5 * cm, A4[0], 0.5 * cm, stroke=0, fill=1)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(CINZA)
    canvas.drawString(2 * cm, 1.2 * cm,
                      "Relatório gerado a partir do notebook “Processo Penal "
                      "Carlos Alberto Silva e Vítima Kátia Moraes Silva”")
    canvas.drawRightString(19 * cm, 1.2 * cm, "Pág. %d" % doc.page)
    canvas.setStrokeColor(CORAL)
    canvas.setLineWidth(0.6)
    canvas.line(2 * cm, 1.5 * cm, 19 * cm, 1.5 * cm)
    canvas.restoreState()


frame = Frame(2 * cm, 1.8 * cm, A4[0] - 4 * cm, A4[1] - 3.6 * cm, id="main")
doc = RelatorioDoc(
    OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
    topMargin=1.8 * cm, bottomMargin=1.8 * cm,
    title="Relatório - Estratégias da Defesa quanto ao Legista Fábio Magalhães",
    author="NotebookLM")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=rodape)])
doc.multiBuild(story)
print("PDF gerado:", OUT)
