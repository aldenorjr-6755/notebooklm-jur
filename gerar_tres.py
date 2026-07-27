# -*- coding: utf-8 -*-
from pdf_base import build

LEG = ("Caso Kátia Francisca Moraes Silva — Proc. 0036508-74.2009.8.10.0001 — "
       "material de apoio ao perito")
META = [
    "<b>Processo nº</b> 0036508-74.2009.8.10.0001 — Tribunal do Júri",
    "<b>Vítima:</b> Kátia Francisca Moraes Silva",
    "<b>Perito/Legista:</b> Dr. Fábio Antônio Costa Alves Magalhães",
]

# ====================================================================
# PDF 1 — PREPARAÇÃO PARA AUDIÊNCIA
# ====================================================================
c1 = []
c1 += [("H", "Nota deontológica")]
c1 += [("P", "O presente material não constitui ensaio de versão nem blindagem de "
        "depoimento. O perito é auxiliar do juízo e deve a verdade técnica (arts. 156 "
        "e 158 do CPP). O objetivo é estritamente legítimo: organizar a exposição "
        "coerente de esclarecimentos que o perito <b>já prestou</b> nos autos, de modo "
        "que as aparentes divergências sejam compreendidas em sua real dimensão "
        "científica. Nenhuma orientação aqui se afasta do que consta dos laudos e do "
        "depoimento gravado.")]

c1 += [("H", "Contexto da audiência")]
c1 += [("ITEM", "<b>Tipo de ação:</b> ação penal — homicídio (Tribunal do Júri)."),
       ("ITEM", "<b>Depoente:</b> perito médico-legista — esclarecimentos técnicos "
        "(art. 159, §5º, I, e art. 473, §3º, CPP)."),
       ("ITEM", "<b>Relação com o caso:</b> autor do exame cadavérico, do atestado de "
        "óbito e do laudo retificador de 2016."),
       ("ITEM", "<b>Quem o inquire:</b> Juiz, Ministério Público e, em reperguntas, a "
        "defesa do acusado (parte contrária a esta preparação)."),
       ("ITEM", "<b>Posição:</b> depõe sobre matéria técnica de sua expertise; pode "
        "emitir juízo de valor dentro da ciência médico-legal.")]

c1 += [("H", "Mapa das divergências")]
c1 += [("P", "São três pontos de atrito que a defesa explorará: (1) a causa da morte "
        "mudou; (2) o horário mudou duas vezes; (3) a retificação veio sete anos "
        "depois, na véspera do 1º júri. Demonstra-se que os três se resolvem por uma "
        "única chave técnica coerente.")]
c1 += [("TBL", [
    ["Documento", "Causa da morte", "Hora / data do óbito", "Base técnica"],
    ["Atestado de óbito (preliminar)", "“enforcamento”", "21h de 12/07 (domingo)",
     "impressão de cena; dado administrativo"],
    ["Laudo cadavérico original", "estrangulamento", "~03h45 de 13/07",
     "rigidez parcial (> 18h)"],
    ["Laudo retificador (2016) — definitivo", "estrangulamento (com simulação de "
     "enforcamento post mortem)", "09h45–17h45 de 13/07",
     "rigidez total (4–12h) + fratura/luxação cervical"],
], [3.3, 3.0, 3.4, 4.0])]
from reportlab.lib.units import cm as _cm
c1[-1] = ("TBL", c1[-1][1], [w * _cm for w in c1[-1][2]])

c1 += [("H", "Discurso harmonizador")]
c1 += [("P", "<i>Texto-base para a exposição do perito — linguagem acessível a "
        "jurados leigos. Tom sereno, didático, colaborativo.</i>")]
c1 += [("H3", "1. Por que o atestado difere do laudo")]
c1 += [("P", "O atestado de óbito é documento administrativo, emitido de imediato "
        "para sepultamento e cartório: registra uma <b>primeira impressão</b>. O laudo "
        "cadavérico é o documento técnico, fruto da necrópsia.")]
c1 += [("Q", "&ldquo;A gente inicialmente, até por uma questão da precipitação de você "
        "emitir um laudo, botou enforcamento; mas avaliando, vendo a complexidade, a "
        "gente concluiu que foi o estrangulamento.&rdquo;")]
c1 += [("H3", "2. Por que estrangulamento, e não suicídio por enforcamento")]
c1 += [("ITEM", "<b>Sulco contínuo e horizontal</b> em toda a circunferência do "
        "pescoço — força externa (estrangulamento); no enforcamento o sulco é oblíquo "
        "e descontínuo."),
       ("ITEM", "<b>Fratura da cartilagem cricoide</b> e <b>luxação da 5ª vértebra "
        "cervical</b> — lesões de força ativa."),
       ("ITEM", "<b>Segundo sulco, oblíquo, na nuca, com pele apergaminhada</b> — "
        "produzido <b>após a morte</b>: simulação de enforcamento.")]
c1 += [("Q", "&ldquo;Verificamos uma tração horizontal em toda a região cervical, "
        "indicando que ela sofreu essa pressão horizontal; ao passo que com o "
        "enforcamento teríamos uma descontinuidade.&rdquo;")]
c1 += [("Q", "&ldquo;Uma simulação do enforcamento, uma simulação pós-morte, "
        "provavelmente.&rdquo;")]
c1 += [("H3", "3. Por que o horário foi corrigido — o ponto central")]
c1 += [("P", "O horário se calcula, entre outros sinais, pela <b>rigidez cadavérica</b>. "
        "No exame inicial havia <b>mobilidade no pescoço</b>, interpretada como rigidez "
        "em regressão (parcial) — o que indicaria morte mais antiga (madrugada). À "
        "reavaliação, percebeu-se que a mobilidade não era regressão da rigidez, mas "
        "decorria de o <b>pescoço estar fraturado/luxado</b>. O restante do corpo "
        "estava em <b>rigidez total</b> = morte de 4 a 12 horas = entre 09h45 e 17h45 "
        "do dia 13.")]
c1 += [("Q", "&ldquo;A dúvida se deu em relação à mobilidade da região cervical; e "
        "pela lógica, essa mobilidade se deu exatamente pela fratura, pela luxação da "
        "região do pescoço.&rdquo;")]
c1 += [("Q", "&ldquo;Uma luxação pode ser confundida com a regressão da rigidez.&rdquo;")]
c1 += [("H3", "4. A retificação harmoniza tudo — inclusive a dúvida da defesa")]
c1 += [("P", "A correção do horário <b>resolve</b> a contradição do telefonema. Pelo "
        "laudo original (morte às 03h45), a ligação das 06h38 do dia 13 seria "
        "impossível; pela conclusão definitiva (morte a partir das 09h45), a ligação "
        "ocorre com a vítima <b>ainda viva</b> — exatamente o esperado. A retificação "
        "<b>reconcilia</b> a perícia com a prova telefônica.")]
c1 += [("Q", "&ldquo;É um caso muito complexo, que gira em torno da subjetividade da "
        "ocorrência; o laudo tem que gerar certeza — a precisão mesmo seria "
        "considerá-la como rigidez total.&rdquo;")]
c1 += [("H3", "5. O que não era da atribuição do perito")]
c1 += [("P", "A seringa encontrada no local <b>não foi periciada</b> pelo legista; a "
        "toxicologia coube ao ICRIM (negativa para barbitúricos e benzodiazepínicos).")]
c1 += [("Q", "&ldquo;O laudo já não foi feito por mim, doutora; foi o pessoal do "
        "ICRIM.&rdquo;")]

c1 += [("H", "Antecipação — perguntas prováveis da defesa")]
c1 += [("TBL", [
    ["#", "Pergunta provável da defesa", "Linha de resposta (verdadeira)",
     "Armadilha a evitar", "Impacto"],
    ["1", "“O senhor admite que errou no primeiro laudo?”",
     "Corrigi a interpretação de um sinal (a rigidez), à luz da fratura cervical. A "
     "conclusão sobre a causa (estrangulamento) nunca mudou.",
     "Dizer “sim, errei” sem qualificar.", "Alto"],
    ["2", "“Como confiar num laudo que muda 7 anos depois, na véspera do júri?”",
     "Revisão por reiteradas solicitações e complexidade. A data da juntada aos autos "
     "é decisão do juízo, não do perito.",
     "Assumir a tempestividade processual (art. 479 CPP).", "Alto"],
    ["3", "“O atestado, escrito pelo senhor, diz ‘enforcamento’ e 21h do dia 12.”",
     "Documento administrativo de primeira impressão; o horário foi erro de grafia; a "
     "causa, impressão preliminar corrigida pela necrópsia.",
     "Equiparar atestado a laudo técnico.", "Médio"],
    ["4", "“Distinguir rigidez parcial de total não é subjetivo?”",
     "Parcial = regressão = morte antiga; total = 4–12h. A confusão veio da mobilidade "
     "por luxação. Ancorar em sinais objetivos (fratura, livores, Tardieu).",
     "Admitir que “tudo é subjetivo”.", "Alto"],
    ["5", "“Havia luta, mas o réu não tinha arranhões. Como explica?”",
     "A escoriação indica resistência da vítima. Correspondência de lesões no agressor "
     "depende de dinâmica/vestimenta/instrumento — não é regra médica.",
     "Opinar sobre autoria.", "Médio"],
    ["6", "“E a seringa? Não sugere automedicação/suicídio?”",
     "Não periciei a seringa; coube ao ICRIM. Toxicológico negativo para barbitúricos "
     "e benzodiazepínicos.",
     "Opinar sobre objeto que não examinou.", "Baixo/Médio"],
    ["7", "“Ela ligou às 06h38, mas seu 1º laudo dizia morte às 03h45.”",
     "Exato — por isso a revisão era necessária. A conclusão definitiva (a partir das "
     "09h45) é compatível com a ligação das 06h38.",
     "Defender o horário antigo.", "Alto"],
    ["8", "“O senhor ‘pendurou’ a tese de simulação para fechar a acusação?”",
     "Sinais objetivos: sulco horizontal contínuo + sulco oblíquo na nuca com "
     "apergaminhamento = produzido post mortem.",
     "Apresentar a simulação como mera dedução.", "Médio"],
    ["9", "“O senhor depõe de cor ou está lendo o laudo?”",
     "Apoio-me nas minhas anotações e fotografias da necrópsia.",
     "Fingir memória integral de evento de 2009.", "Baixo"],
], [w * _cm for w in [0.7, 4.0, 5.2, 3.4, 1.4]])]

c1 += [("H", "Objeções cabíveis")]
c1 += [("TBL", [
    ["Se a defesa…", "Fundamento da objeção"],
    ["Fizer pergunta capciosa/sugestiva (“não é verdade que o senhor inventou…”)",
     "Art. 212 CPP / art. 459 CPC — pergunta indutiva/vexatória"],
    ["Pedir opinião jurídica (“houve dolo?”, “foi qualificado?”)",
     "Extrapola a expertise médico-legal — matéria do júri"],
    ["Atribuir ao perito a tempestividade da juntada",
     "A regularidade processual (art. 479 CPP) é do juízo"],
    ["Insistir em ponto já respondido",
     "Pergunta repetitiva/protelatória"],
], [w * _cm for w in [8.0, 8.0]])]

c1 += [("H", "Observações táticas")]
c1 += [("H3", "Postura do perito")]
c1 += [("ITEM", "Falar devagar e didaticamente — jurados são leigos."),
       ("ITEM", "Ancorar sempre no objetivo: foto, fratura, sulco, apergaminhamento."),
       ("ITEM", "Tratar a correção como virtude científica, nunca como confissão de "
        "incompetência.")]
c1 += [("H3", "Três frases para ter na ponta da língua")]
c1 += [("ITEM", "“A causa da morte nunca mudou; o que refinei foi o horário, por uma "
        "razão anatômica: o pescoço estava fraturado.”"),
       ("ITEM", "“A correção do horário é o que torna a perícia compatível com a "
        "ligação das 06h38.”"),
       ("ITEM", "“A data da juntada do laudo aos autos é decisão do juízo; a mim cabe "
        "a conclusão técnica.”")]
c1 += [("H3", "Linhas que o perito NÃO deve cruzar")]
c1 += [("ITEM", "Não opinar sobre autoria (quem matou)."),
       ("ITEM", "Não opinar sobre matéria que não periciou (seringa)."),
       ("ITEM", "Não discutir nulidade processual — remeter ao juízo.")]

build("1_Preparacao_Audiencia_Legista.pdf",
      "PREPARAÇÃO PARA AUDIÊNCIA",
      "Esclarecimentos do Perito Médico-Legista e Antecipação das Reperguntas da Defesa",
      META, c1, LEG)

# ====================================================================
# PDF 2 — QUESITOS COMPLEMENTARES ESCRITOS (art. 159, §5º, CPP)
# ====================================================================
c2 = []
c2 += [("H", "Preâmbulo")]
c2 += [("P", "Com fundamento no art. 159, §5º, inciso I, do Código de Processo Penal, "
        "formulam-se os quesitos complementares abaixo, a serem respondidos pelo perito "
        "médico-legista Dr. Fábio Antônio Costa Alves Magalhães, autor do exame "
        "cadavérico, do atestado de óbito e do laudo retificador, com o objetivo de "
        "esclarecer ao Juízo e ao Conselho de Sentença os pontos técnicos do caso.")]
c2 += [("RODAPE_NOTE", "Observação: os quesitos foram redigidos de modo a permitir "
        "resposta técnica objetiva, sem indução, em consonância com os arts. 156 e 158 "
        "do CPP.")]

c2 += [("H", "I. Da causa jurídica da morte")]
c2 += [("QUES", "<b>Quesito 1.</b> Qual foi a <b>causa mortis</b> definitiva da vítima, "
        "conforme conclusão do exame cadavérico e do laudo retificador?"),
       ("QUES", "<b>Quesito 2.</b> Os achados necroscópicos são compatíveis com "
        "<b>suicídio por enforcamento</b>? Justifique tecnicamente."),
       ("QUES", "<b>Quesito 3.</b> Qual a distinção médico-legal entre as lesões "
        "produzidas por <b>estrangulamento</b> (força externa ativa) e por "
        "<b>enforcamento</b> (peso do próprio corpo)?")]

c2 += [("H", "II. Dos sinais cervicais")]
c2 += [("QUES", "<b>Quesito 4.</b> O sulco encontrado ao redor do pescoço da vítima "
        "era <b>contínuo e horizontal</b> ou <b>oblíquo e descontínuo</b>? O que cada "
        "padrão indica?"),
       ("QUES", "<b>Quesito 5.</b> Foi constatada <b>fratura da cartilagem cricoide</b> "
        "e <b>luxação da quinta vértebra cervical</b>? Tais lesões são compatíveis com "
        "ação de força mecânica ativa de terceiro?"),
       ("QUES", "<b>Quesito 6.</b> Há, na nuca, um <b>segundo sulco oblíquo com pele "
        "apergaminhada</b>? O “apergaminhamento” indica que a lesão foi produzida "
        "<b>antes ou depois</b> da morte? Em que isso implica?")]

c2 += [("H", "III. Da rigidez cadavérica e do horário da morte")]
c2 += [("QUES", "<b>Quesito 7.</b> Explique a diferença entre <b>rigidez cadavérica "
        "parcial</b> e <b>rigidez total</b> e como cada estado se reflete no cálculo "
        "do tempo de morte."),
       ("QUES", "<b>Quesito 8.</b> No exame inicial, a <b>mobilidade da região "
        "cervical</b> foi interpretada como regressão da rigidez. Tal mobilidade pode "
        "decorrer de <b>luxação/fratura cervical</b> e ser confundida com regressão da "
        "rigidez?"),
       ("QUES", "<b>Quesito 9.</b> À luz da reavaliação (rigidez total), qual o "
        "<b>intervalo definitivo</b> para a ocorrência do óbito, tomando como base a "
        "necrópsia realizada às 21h45 do dia 13/07/2009?")]

c2 += [("H", "IV. Da compatibilidade com a prova telefônica")]
c2 += [("QUES", "<b>Quesito 10.</b> Considerando o intervalo definitivo do óbito "
        "(09h45–17h45 do dia 13/07), uma <b>ligação telefônica atribuída à vítima às "
        "06h38</b> do dia 13/07 é <b>compatível</b> com a hipótese de a vítima ainda "
        "estar viva naquele horário?")]

c2 += [("H", "V. Dos sinais de resistência")]
c2 += [("QUES", "<b>Quesito 11.</b> A <b>escoriação no dorso da mão direita</b> indica "
        "resistência da vítima? Sob o ponto de vista médico-legal, é <b>regra "
        "necessária</b> que o agressor apresente lesões correspondentes?")]

c2 += [("H", "VI. Da seringa e exames de terceiros")]
c2 += [("QUES", "<b>Quesito 12.</b> A análise da <b>seringa</b> e da substância nela "
        "contida foi realizada pelo perito médico-legista ou por outro órgão? Qual o "
        "resultado, segundo o laudo competente?")]

c2 += [("H", "VII. Quesito de esclarecimento final")]
c2 += [("QUES", "<b>Quesito 13.</b> O perito ratifica que a <b>conclusão definitiva</b> "
        "do caso é a constante do laudo retificador, e que a alteração entre os "
        "documentos diz respeito ao <b>refinamento do horário</b> (por razão "
        "anatômica), e não à <b>causa da morte</b>, sempre concluída como "
        "estrangulamento?")]

build("2_Quesitos_Complementares_Legista.pdf",
      "QUESITOS COMPLEMENTARES",
      "Esclarecimentos ao Perito Médico-Legista — art. 159, §5º, I, do CPP",
      META, c2, LEG)

# ====================================================================
# PDF 3 — ROTEIRO DE REPERGUNTAS DA ACUSAÇÃO / ASSISTENTE
# ====================================================================
c3 = []
c3 += [("H", "Contexto e finalidade")]
c3 += [("P", "Roteiro de reperguntas a ser utilizado pela acusação / assistente de "
        "acusação <b>após</b> a inquirição da defesa, com o objetivo de reforçar a "
        "coerência técnica do perito, consolidar os pontos objetivos da perícia e "
        "neutralizar eventuais dúvidas semeadas. Perguntas abertas constroem narrativa; "
        "perguntas fechadas fixam pontos no registro. Tom respeitoso e colaborativo.")]

c3 += [("H", "Bloco 1 — Qualificação técnica e método")]
c3 += [("QUES", "<b>1.</b> Doutor, há quanto tempo o senhor atua como médico-legista e "
        "quantas necrópsias por asfixia já realizou?"),
       ("P", "<i>Finalidade:</i> estabelecer autoridade técnica (função fundacional)."),
       ("QUES", "<b>2.</b> Ao reavaliar este caso, o senhor se apoiou em quê — memória, "
        "anotações, fotografias da necrópsia?"),
       ("P", "<i>Finalidade:</i> legitimar a base documental dos esclarecimentos.")]

c3 += [("H", "Bloco 2 — A causa da morte (objetiva)")]
c3 += [("QUES", "<b>3.</b> O sulco ao redor do pescoço era contínuo e horizontal. O que "
        "esse padrão indica, do ponto de vista médico-legal?"),
       ("P", "<i>Finalidade:</i> fixar o achado-chave do estrangulamento."),
       ("QUES", "<b>4.</b> O senhor constatou fratura da cartilagem cricoide e luxação "
        "da 5ª vértebra cervical. Essas lesões são compatíveis com o simples peso do "
        "corpo em um enforcamento?"),
       ("P", "<i>Finalidade:</i> afastar a hipótese de suicídio com base objetiva."),
       ("QUES", "<b>5.</b> O senhor mencionou um segundo sulco, oblíquo, na nuca, com "
        "pele apergaminhada. O que o apergaminhamento revela sobre o momento da lesão?"),
       ("P", "<i>Finalidade:</i> demonstrar a simulação de enforcamento post mortem.")]

c3 += [("H", "Bloco 3 — A correção do horário (didática)")]
c3 += [("QUES", "<b>6.</b> O senhor poderia explicar, em termos simples para os "
        "senhores jurados, a diferença entre rigidez parcial e rigidez total?"),
       ("P", "<i>Finalidade:</i> traduzir o ponto técnico central ao leigo."),
       ("QUES", "<b>7.</b> Por que a mobilidade do pescoço o levou, inicialmente, a "
        "uma leitura, e o que o fez corrigi-la depois?"),
       ("P", "<i>Finalidade:</i> apresentar a correção como rigor, não como falha."),
       ("QUES", "<b>8.</b> A causa da morte (estrangulamento) chegou a mudar em algum "
        "momento, ou o que se ajustou foi exclusivamente o horário?"),
       ("P", "<i>Finalidade:</i> separar o que mudou (horário) do que nunca mudou "
        "(causa).")]

c3 += [("H", "Bloco 4 — A harmonização da prova telefônica")]
c3 += [("QUES", "<b>9.</b> Considerando sua conclusão definitiva, a ligação atribuída "
        "à vítima às 06h38 do dia 13 é compatível com ela estar viva naquele momento?"),
       ("P", "<i>Finalidade:</i> converter a dúvida da defesa em confirmação da "
        "perícia."),
       ("QUES", "<b>10.</b> Em outras palavras, a sua reavaliação aproxima ou afasta a "
        "perícia da prova telefônica dos autos?"),
       ("P", "<i>Finalidade:</i> consolidar a coerência do conjunto probatório.")]

c3 += [("H", "Bloco 5 — Limites e honestidade técnica")]
c3 += [("QUES", "<b>11.</b> A análise da seringa coube ao senhor ou a outro órgão? "
        "Qual o resultado oficial?"),
       ("P", "<i>Finalidade:</i> demonstrar transparência e delimitar atribuições."),
       ("QUES", "<b>12.</b> A escoriação na mão da vítima indica o quê? É regra que o "
        "agressor sempre saia marcado de um estrangulamento?"),
       ("P", "<i>Finalidade:</i> neutralizar o argumento da ausência de lesões no réu, "
        "sem opinar sobre autoria.")]

c3 += [("H", "Bloco 6 — Fechamento")]
c3 += [("QUES", "<b>13.</b> Doutor, o senhor ratifica integralmente a conclusão do "
        "laudo retificador como sua conclusão técnica definitiva?"),
       ("P", "<i>Finalidade:</i> fixar a ratificação no registro."),
       ("QUES", "<b>14.</b> Há algo mais, do ponto de vista técnico, que o senhor "
        "considere relevante esclarecer ao Juízo e aos jurados?"),
       ("P", "<i>Finalidade:</i> abrir espaço para complementação espontânea.")]

c3 += [("H", "Perguntas a evitar (também pela acusação)")]
c3 += [("TBL", [
    ["Tipo", "Exemplo", "Por quê"],
    ["Sugestiva", "“Não é verdade que foi homicídio?”", "Induz a resposta (art. 459 CPC)"],
    ["Opinativa sobre autoria", "“Foi o réu que matou?”", "Extrapola a perícia"],
    ["Repetitiva", "Reperguntar ponto já fixado", "Protelatória / cansa o júri"],
    ["Juridicizante", "“Houve dolo eventual?”", "Matéria do Conselho de Sentença"],
], [w * _cm for w in [3.0, 7.0, 6.0]])]

c3 += [("H", "Observações táticas")]
c3 += [("ITEM", "Reperguntar apenas o necessário para <b>reparar</b> ou <b>reforçar</b> "
        "— evitar reabrir pontos que a defesa não conseguiu explorar."),
       ("ITEM", "Usar as <b>palavras do próprio perito</b> nas reperguntas, para dar "
        "naturalidade e coerência."),
       ("ITEM", "Encerrar deixando no ar a <b>frase-síntese</b>: a causa nunca mudou; "
        "o horário foi refinado por razão anatômica.")]

build("3_Roteiro_Reperguntas_Acusacao.pdf",
      "ROTEIRO DE REPERGUNTAS",
      "Acusação / Assistente de Acusação — Reforço dos Esclarecimentos do Perito",
      META, c3, LEG)

print("OK — 3 PDFs gerados.")
