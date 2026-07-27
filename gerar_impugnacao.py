# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# ---- Page / base style ----
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(3.0)
sec.bottom_margin = Cm(2.0)
sec.left_margin = Cm(3.0)
sec.right_margin = Cm(2.0)

normal = doc.styles['Normal']
normal.font.name = 'Times New Roman'
normal.font.size = Pt(12)
pf = normal.paragraph_format
pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
pf.space_after = Pt(0)
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def set_cell_bg(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color)
    tcPr.append(shd)


def p(text='', *, bold=False, italic=False, align='justify', size=12,
      space_before=0, space_after=6, first_line=None, all_caps=False,
      underline=False):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(space_before)
    par.paragraph_format.space_after = Pt(space_after)
    al = {'justify': WD_ALIGN_PARAGRAPH.JUSTIFY, 'center': WD_ALIGN_PARAGRAPH.CENTER,
          'right': WD_ALIGN_PARAGRAPH.RIGHT, 'left': WD_ALIGN_PARAGRAPH.LEFT}[align]
    par.paragraph_format.alignment = al
    if first_line is not None:
        par.paragraph_format.first_line_indent = Cm(first_line)
    if text:
        run = par.add_run(text.upper() if all_caps else text)
        run.bold = bold
        run.italic = italic
        run.underline = underline
        run.font.size = Pt(size)
    return par


def runs(par_parts, *, align='justify', first_line=1.25, space_after=6, space_before=0):
    """par_parts: list of (text, dict-of-format)"""
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(space_before)
    par.paragraph_format.space_after = Pt(space_after)
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if align == 'justify' else WD_ALIGN_PARAGRAPH.LEFT
    if first_line is not None:
        par.paragraph_format.first_line_indent = Cm(first_line)
    for text, fmt in par_parts:
        r = par.add_run(text)
        r.bold = fmt.get('bold', False)
        r.italic = fmt.get('italic', False)
        r.font.size = Pt(fmt.get('size', 12))
    return par


def heading(text, size=12):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(12)
    par.paragraph_format.space_after = Pt(6)
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    par.paragraph_format.keep_with_next = True
    r = par.add_run(text)
    r.bold = True
    r.font.size = Pt(size)
    return par


# ============ ENDEREÇAMENTO ============
p('EXCELENTÍSSIMO(A) SENHOR(A) SECRETÁRIO(A) MUNICIPAL DE FAZENDA DO MUNICÍPIO DE '
  'SANTA LUZIA DO PARUÁ – ESTADO DO MARANHÃO', bold=True, align='justify',
  first_line=None, space_after=6)
p('(Autoridade administrativa julgadora de primeira instância – art. 251 da Lei '
  'Municipal nº 321/2011 – Código Tributário Municipal)', italic=True, size=10,
  align='justify', first_line=None, space_after=18)

# Reference block
p('Ref.: Termo de Início de Ação de Fiscalização – TIAF nº 04/2025', bold=True,
  align='justify', first_line=None, space_after=0)
p('Auto de Infração nº 01/2025 – Ofício nº 122/2025', bold=True,
  align='justify', first_line=None, space_after=0)
p('Tributo: ISSQN – Imposto Sobre Serviços de Qualquer Natureza', bold=True,
  align='justify', first_line=None, space_after=0)
p('Período impugnado: competências de jul/2020 a set/2025', bold=True,
  align='justify', first_line=None, space_after=18)

runs([
    ('CARTÓRIO DO 2º OFÍCIO EXTRAJUDICIAL DE SANTA LUZIA DO PARUÁ', {'bold': True}),
    (', serventia extrajudicial inscrita no CNPJ próprio, com capacidade tributária '
     'própria e distinta da pessoa de sua titular, sob a titularidade de ', {}),
    ('ELIANE DELMONDES DE SOUSA', {'bold': True}),
    (', por seu advogado que esta subscreve (instrumento de mandato anexo), vem, '
     'respeitosamente, à presença de Vossa Excelência, com fundamento no art. 5º, '
     'incisos LIV e LV, da Constituição Federal, e nos arts. 240, 248 e seguintes da '
     'Lei Municipal nº 321/2011 (Código Tributário Municipal – CTM), apresentar', {}),
], first_line=1.25, space_after=10)

p('IMPUGNAÇÃO AO LANÇAMENTO', bold=True, align='center', first_line=None,
  space_before=6, space_after=0)
p('(Auto de Infração nº 01/2025 – TIAF nº 04/2025)', bold=True, align='center',
  first_line=None, space_after=10)

p('em face da exigência fiscal de ISSQN consubstanciada no Auto de Infração nº '
  '01/2025, decorrente do TIAF nº 04/2025 e do Ofício nº 122/2025, pelas razões '
  'de fato e de direito a seguir aduzidas.', first_line=1.25, space_after=8)

# ============ I — TEMPESTIVIDADE ============
heading('I – DA TEMPESTIVIDADE E DE QUESTÃO PRELIMINAR DE ORDEM PÚBLICA')
p('A notificação de consolidação do débito, datada de 03 de junho de 2026, não '
  'informou ao contribuinte o prazo, a forma, o fundamento legal nem o órgão '
  'competente para a defesa administrativa — vício que adiante se argui em '
  'preliminar. Por cautela, e considerando que a fluência do prazo do art. 248 do '
  'CTM pressupõe ciência regular acompanhada da informação quanto ao direito de '
  'impugnar, é tempestiva a presente peça, protocolada na primeira oportunidade '
  'após a ciência da exigência.', first_line=1.25, space_after=6)

# ============ II — NULIDADE: omissão do direito de impugnar ============
heading('II – PRELIMINAR DE NULIDADE — CERCEAMENTO DE DEFESA PELA OMISSÃO QUANTO '
        'AO DIREITO DE IMPUGNAÇÃO')
p('A notificação relativa ao TIAF nº 04/2025 e ao Auto de Infração nº 01/2025 '
  'limitou-se a apresentar proposta de parcelamento e guias de recolhimento — '
  '“aproveita-se e enviamos em anexo as guias de recolhimento com vencimento para '
  '02/07/2026” —, sem informar ao contribuinte que lhe assiste o direito de '
  'impugnar a exigência. Tratou-se o lançamento como dívida já definitiva, '
  'oferecendo-se tão somente o pagamento à vista ou parcelado.', first_line=1.25,
  space_after=6)
p('Em nenhum dos documentos há indicação:', first_line=1.25, space_after=2)

for t in [
    'do prazo de 20 (vinte) dias para a impugnação (art. 248 do CTM);',
    'da autoridade administrativa julgadora competente (Secretário de Fazenda — art. 251 do CTM);',
    'da possibilidade de recurso voluntário à segunda instância (arts. 253 e 254 do CTM);',
    'da faculdade de defesa independentemente de prévio depósito (art. 248 do CTM).',
]:
    par = doc.add_paragraph(style='List Bullet')
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_after = Pt(2)
    par.add_run(t).font.size = Pt(12)

p('A omissão dessas informações essenciais, com a indução do contribuinte ao '
  'pagamento, viola o devido processo legal e a ampla defesa (art. 5º, LIV e LV, '
  'da CF) e a própria lei municipal, que assegura o contencioso administrativo '
  'fiscal (arts. 240 e 248 a 254 do CTM). Tal vício macula de nulidade o ato de '
  'exigência, impondo o seu refazimento com a regular cientificação do prazo, da '
  'forma e da via impugnatória.', first_line=1.25, space_before=4, space_after=6)

# ============ III — DECADÊNCIA ============
heading('III – DA DECADÊNCIA DAS COMPETÊNCIAS DE 2020 E DO 1º SEMESTRE DE 2021 '
        '(ART. 150, § 4º, DO CTN — CONTAGEM MENSAL)')
p('O ISSQN é tributo sujeito a lançamento por homologação (art. 155 do CTM; art. '
  '150 do CTN). No caso, sempre houve antecipação de pagamento pelo cartório — '
  'fato incontroverso e expressamente reconhecido pela própria Prefeitura, que '
  '“considerou os comprovantes de pagamento” e “abateu do montante integral” os '
  'valores pagos.', first_line=1.25, space_after=6)
p('Havendo pagamento antecipado, o prazo decadencial rege-se pelo art. 150, § 4º, '
  'do CTN (e art. 155, §§ 4º e 5º, do CTM) — 5 (cinco) anos contados de cada fato '
  'gerador —, e não pela regra do art. 173, I. E, porque o ISS possui fato gerador '
  'mensal, a contagem opera-se mês a mês: a cada competência corresponde um termo '
  'decadencial autônomo.', first_line=1.25, space_after=6)
p('Tomando-se a data da constituição do crédito veiculada na consolidação (03 de '
  'junho de 2026) — e considerando que sequer foi informada a data de ciência do '
  'Auto de Infração nº 01/2025, dúvida que se resolve em favor do contribuinte —, '
  'já se exauriu o prazo quinquenal de homologação quanto a:', first_line=1.25,
  space_after=2)
for t in [
    'todas as competências de janeiro a dezembro de 2020; e',
    'as competências de janeiro a junho de 2021.',
]:
    par = doc.add_paragraph(style='List Bullet')
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_after = Pt(2)
    par.add_run(t).font.size = Pt(12)
p('Quanto a tais meses, considera-se homologado o lançamento e definitivamente '
  'extinto o crédito (art. 155, §§ 4º e 5º, do CTM; art. 150, § 4º, do CTN). '
  'Reforça-o o fato de que essas exatas competências foram pagas e homologadas por '
  'guias emitidas pela própria Prefeitura — Guia nº 054/21 (jan/dez 2020, R$ '
  '9.487,59) e Guia nº 041/21 (jan/jun 2021, R$ 5.689,52) —, com posterior '
  'expedição de Certidões Negativas de Débito. Requer-se, pois, o reconhecimento '
  'da decadência das competências de janeiro de 2020 a junho de 2021.',
  first_line=1.25, space_before=4, space_after=6)

# ============ IV — PAGAMENTO / INFORMAÇÕES À DISPOSIÇÃO ============
heading('IV – SEMPRE HOUVE PAGAMENTO E AS INFORMAÇÕES SEMPRE ESTIVERAM À '
        'DISPOSIÇÃO DA PREFEITURA')
p('A exigência ignora que o cartório sempre recolheu o ISSQN e que toda a base de '
  'cálculo (a arrecadação da serventia) sempre esteve à disposição do Fisco '
  'municipal:', first_line=1.25, space_after=2)
for t in [
    'a arrecadação bruta é declarada oficialmente ao Tribunal de Justiça do Estado '
    'do Maranhão, com base nas remessas do registrador ao SIAFERJ-WEB (Fundo '
    'Especial de Modernização e Reaparelhamento do Poder Judiciário — FERJ), '
    'conforme Declarações de Rendimentos anexas; bastava à Prefeitura requisitar '
    'tais dados ao Tribunal de Justiça — providência simples e gratuita — para '
    'conhecer os valores, sem necessidade de autuação retroativa;',
    'o próprio Município emitia as Guias de Avaliação e Pagamento de ISSQN (nºs '
    '054/21, 041/21, 052/21, 006/22, 008/22 e 009/22), recebia os recolhimentos e '
    'expedia Certidões Negativas de Débito em 2021 e 2022.',
]:
    par = doc.add_paragraph(style='List Bullet')
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_after = Pt(2)
    par.add_run(t).font.size = Pt(12)
p('Como já sustentado nas defesas anteriores, “é desarrazoado pensar que uma '
  'serventia procederia aos recolhimentos em favor dos fundos especiais de '
  'Modernização e Reaparelhamento do Judiciário – FERJ e descumpriria as '
  'obrigações com a municipalidade”.', first_line=1.25, space_before=4, space_after=6)
p('Essa conduta gera a homologação dos valores recolhidos e atrai a proteção da '
  'confiança e a irretroatividade da alteração de critério jurídico (art. 146 do '
  'CTN). A Prefeitura não pode, anos depois, alterar de ofício o critério de '
  'apuração e projetá-lo sobre fatos geradores pretéritos, como reiteradamente '
  'decide o Superior Tribunal de Justiça:', first_line=1.25, space_after=4)

for t in [
    '“na hipótese de erro de direito (equívoco na valoração jurídica dos fatos), o '
    'ato administrativo de lançamento revela-se imodificável, máxime em virtude do '
    'princípio da proteção à confiança, encartado no art. 146 do CTN” (STJ, AgInt '
    'no AREsp);',
    '“esta modificação de entendimento, de ofício, por parte dos agentes públicos '
    'incumbidos da fiscalização do tributo não pode se furtar à regra do artigo 146 '
    'do CTN [...]. Apenas os fatos posteriores à alteração de critérios sujeitam-se '
    'aos seus efeitos” (STJ, AgInt no AREsp).',
]:
    par = doc.add_paragraph()
    par.paragraph_format.left_indent = Cm(2.5)
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_after = Pt(4)
    r = par.add_run(t)
    r.italic = True
    r.font.size = Pt(11)
p('O limite fixado pelo próprio STJ — de que a proteção do art. 146 pressupõe '
  'homologação ou lançamento prévio — encontra-se plenamente satisfeito, pois os '
  'recolhimentos do cartório foram homologados pela emissão de guias pelo próprio '
  'Município e pela expedição de CNDs.', first_line=1.25, space_after=6)

# ============ V — BIS IN IDEM ============
heading('V – DA DUPLICIDADE DE LANÇAMENTO E DO BIS IN IDEM')
p('As competências de julho de 2020 a março de 2024 já haviam sido objeto de '
  'fiscalização e lançamento nos autos AI 2023/001 (jan/2018 a jun/2023), AI '
  '2024/001 (jul a dez/2023) e AI 2024/002 (jan a mar/2024), além das guias '
  'emitidas e pagas. O TIAF nº 04/2025 relança as mesmas competências, '
  'configurando dupla exigência sobre idênticos fatos geradores, o que é vedado. '
  'A tabela a seguir demonstra a sobreposição:', first_line=1.25, space_after=8)

# Tabela de sobreposição
tbl = doc.add_table(rows=1, cols=3)
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl.style = 'Table Grid'
widths = [Cm(5.0), Cm(7.0), Cm(4.0)]
hdr = tbl.rows[0].cells
for i, h in enumerate(['Competências', 'Fiscalizações sobrepostas', 'Quantidade']):
    hdr[i].text = ''
    rr = hdr[i].paragraphs[0].add_run(h)
    rr.bold = True
    rr.font.size = Pt(10)
    hdr[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_cell_bg(hdr[i], 'D9D9D9')

rows_data = [
    ('jul/2020 – dez/2020', 'AI 2023/001 + TIAF 04/2025 (+ Guia 054/21 paga)', '6 meses'),
    ('jan/2021 – dez/2021', 'AI 2023/001 + TIAF 04/2025 (+ Guias 041/21 e 052/21 pagas)', '12 meses'),
    ('jan/2022 – dez/2022', 'AI 2023/001 + TIAF 04/2025 (+ Guias 006, 008 e 009/22 pagas)', '12 meses'),
    ('jan/2023 – jun/2023', 'AI 2023/001 + TIAF 04/2025', '6 meses'),
    ('jul/2023 – dez/2023', 'AI 2024/001 + TIAF 04/2025', '6 meses'),
    ('jan/2024 – mar/2024', 'AI 2024/002 + TIAF 04/2025', '3 meses'),
]
for c0, c1, c2 in rows_data:
    cells = tbl.add_row().cells
    for j, val in enumerate([c0, c1, c2]):
        cells[j].text = ''
        rr = cells[j].paragraphs[0].add_run(val)
        rr.font.size = Pt(10)
        cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 1 else WD_ALIGN_PARAGRAPH.CENTER

for i, w in enumerate(widths):
    for row in tbl.rows:
        row.cells[i].width = w

p('Em síntese, todas as competências de julho de 2020 a março de 2024 foram '
  'fiscalizadas e lançadas mais de uma vez. Requer-se a exclusão de tais '
  'competências, sob pena de bis in idem.', first_line=1.25, space_before=8,
  space_after=6)

# ============ VI — REITERAÇÃO ============
heading('VI – DA REITERAÇÃO DAS TESES JÁ DEDUZIDAS NA IMPUGNAÇÃO, NA REVISÃO E NO '
        'RECURSO VOLUNTÁRIO ANTERIORES')
p('Ficam expressamente reiterados, como se aqui integralmente transcritos, todos '
  'os fundamentos das defesas anteriores (revisão ao AI 2023/001, impugnação aos '
  'AI 2024/001 e 2024/002 e recurso voluntário), em especial:', first_line=1.25,
  space_after=2)
for t in [
    'ausência de notificação regular da lavratura e erro na sujeição passiva '
    '(notificação dirigida à pessoa física, e não ao CNPJ da serventia, que possui '
    'capacidade tributária própria);',
    'falta de diligência e de oitiva prévia do contribuinte, em afronta à ampla defesa;',
    'presunção de legalidade e veracidade das CNDs emitidas em 2021 e 2022 e das '
    'guias pagas até 10/03/2022, cabendo ao Fisco o ônus de demonstrar eventual '
    'incorreção;',
    'homologação expressa dos recolhimentos até a competência de fevereiro de 2022 '
    'e decadência das competências mais antigas;',
    'denúncia espontânea (art. 138 do CTN) e os benefícios de redução e anistia já '
    'invocados (Lei nº 14.740/2023 e Lei estadual nº 11.625/2021), de forma subsidiária;',
    'sucumbência fazendária — o reconhecimento administrativo de erro quanto aos '
    'exercícios de 2018 a 2022 afasta a exigibilidade de atualização monetária, '
    'multa e juros sobre o saldo remanescente.',
]:
    par = doc.add_paragraph(style='List Bullet')
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_after = Pt(2)
    par.add_run(t).font.size = Pt(12)

# ============ VII — AUSÊNCIA DE PLANILHAS / CÁLCULO ============
heading('VII – DA AUSÊNCIA DE PLANILHAS, CRITÉRIOS DE CÁLCULO, ÍNDICE DE CORREÇÃO, '
        'TERMO INICIAL DA MORA E DEMAIS ELEMENTOS — ILIQUIDEZ E INCERTEZA')
p('O lançamento é nulo por iliquidez e por cerceamento de defesa, pois apresenta '
  'apenas um quadro-resumo com as rubricas “Principal / Juros / Multa / Total”, '
  'sem os elementos mínimos exigidos pelos arts. 142 do CTN e 176 do CTM. Faltam:',
  first_line=1.25, space_after=2)
for t in [
    'a memória e a planilha de cálculo, mês a mês, com a base de cálculo (preço do '
    'serviço — art. 51 do CTM) efetivamente considerada em cada competência e as '
    'deduções dos pagamentos já efetuados;',
    'a indicação do índice de correção monetária aplicado (o art. 176, § 1º, do CTM '
    'impõe a UFIR, com atualização mensal);',
    'a especificação da taxa de juros de mora (art. 176, § 4º — 1% ao mês) e da '
    'multa de mora (art. 176, § 3º — 2% ao mês, limitada a 50%), bem como a '
    'demonstração de sua aplicação;',
    'a indicação do termo inicial da mora — data a partir da qual incidem juros e '
    'correção (“do dia seguinte ao do vencimento”, art. 176, § 4º);',
    'a data da lavratura e da ciência do Auto de Infração nº 01/2025.',
]:
    par = doc.add_paragraph(style='List Bullet')
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_after = Pt(2)
    par.add_run(t).font.size = Pt(12)
p('Sem tais elementos, o contribuinte não tem como conferir nem refutar o cálculo, '
  'o que, por si só, vicia o lançamento (art. 142 do CTN) e cerceia o direito de '
  'defesa.', first_line=1.25, space_before=4, space_after=6)

# ============ VIII — PEDIDOS ============
heading('VIII – DOS PEDIDOS')
p('Ante o exposto, requer-se:', first_line=1.25, space_after=4)

pedidos = [
    ('a) preliminarmente, a NULIDADE da notificação e do lançamento por omissão do '
     'direito de impugnação (prazo, forma, autoridade julgadora e recurso — arts. '
     '248, 251, 253 e 254 do CTM; art. 5º, LIV e LV, da CF), com o refazimento do '
     'ato e a reabertura de prazo;'),
    ('b) a NULIDADE do lançamento por iliquidez e incerteza, ante a falta de '
     'planilhas, memória de cálculo, índice de correção, taxa de juros e termo '
     'inicial da mora (arts. 142 do CTN e 176 do CTM);'),
    ('c) no mérito, o reconhecimento da DECADÊNCIA das competências de janeiro de '
     '2020 a junho de 2021, por força do art. 150, § 4º, do CTN e do art. 155, §§ '
     '4º e 5º, do CTM (contagem mensal), com a consequente extinção definitiva dos '
     'respectivos créditos;'),
    ('d) a EXCLUSÃO das competências lançadas em duplicidade (jul/2020 a mar/2024), '
     'já constituídas nos AI 2023/001, 2024/001 e 2024/002, sob pena de bis in idem;'),
    ('e) no mérito, a IMPROCEDÊNCIA INTEGRAL da exigência, reconhecendo-se que '
     'sempre houve pagamento e que os dados estavam à disposição da Prefeitura '
     '(TJMA/FERJ/SIAFERJ, guias pagas e CNDs), com aplicação do art. 146 do CTN e '
     'da proteção da confiança;'),
    ('f) subsidiariamente, a REVISÃO dos valores, com o abatimento de todos os '
     'pagamentos comprovados, o recálculo demonstrado e a aplicação dos benefícios '
     'de denúncia espontânea e anistia já requeridos;'),
    ('g) a REITERAÇÃO e o aproveitamento de todos os fundamentos da impugnação, da '
     'revisão e do recurso voluntário anteriores.'),
]
for t in pedidos:
    par = doc.add_paragraph()
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.first_line_indent = Cm(1.25)
    par.paragraph_format.space_after = Pt(6)
    par.add_run(t).font.size = Pt(12)

p('Requer, por fim, a produção de todas as provas admitidas em direito, em '
  'especial a juntada posterior de documentos e a requisição, junto ao Tribunal '
  'de Justiça do Estado do Maranhão, das declarações de arrecadação do FERJ/'
  'SIAFERJ-WEB referentes ao período fiscalizado.', first_line=1.25, space_before=4,
  space_after=12)

p('Nestes termos,', first_line=1.25, space_after=0)
p('Pede deferimento.', first_line=1.25, space_after=18)

p('Santa Luzia do Paruá – MA, _____ de ____________ de 2026.', align='center',
  first_line=None, space_after=36)

p('_______________________________________', align='center', first_line=None,
  space_after=0)
p('Advogado(a)', align='center', first_line=None, space_after=0, bold=True)
p('OAB/MA nº __________', align='center', first_line=None, space_after=0)

out = r'C:\Users\alden\.notebooklm\Impugnacao_TIAF_04-2025_ISSQN_Santa_Luzia_do_Parua.docx'
doc.save(out)
print('OK ->', out)
