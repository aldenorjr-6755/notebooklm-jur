#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gera um banco de prompts em HTML a partir dos subagents .md de ~/.claude/agents."""
import json
import os
import re
from pathlib import Path

AGENTS_DIR = Path(os.path.expanduser("~")) / ".claude" / "agents"
OUT = Path(r"C:\Users\alden\.notebooklm\prazos\banco-de-prompts.html")

def parse(md_text):
    """Extrai (name, description, tools, model, body) de um .md com frontmatter YAML."""
    name = desc = tools = model = ""
    body = md_text
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) >= 3:
            fm, body = parts[1], parts[2]
            for line in fm.splitlines():
                m = re.match(r"^(name|description|tools|model)\s*:\s*(.*)$", line.strip())
                if m:
                    k, v = m.group(1), m.group(2).strip()
                    if k == "name": name = v
                    elif k == "description": desc = v
                    elif k == "tools": tools = v
                    elif k == "model": model = v
    return name, desc, tools, model, body.strip()

# Regras de categorização (primeira correspondência vence)
RULES = [
    ("Meta / Engenharia de prompt", ["engenheiro-", "orquestrador-prompt"]),
    ("Utilitário / Estilo", ["humanizacao-texto"]),
    ("Pesquisa & Conhecimento", ["jurisprudencia-stj", "doutrina", "lei-e-sumula",
        "tese-repetitiva", "pesquisa-precedentes", "ementario", "ementa-padrao"]),
    ("Análise de autos & Estratégia", ["analise-juridica-firac", "analise-super-firac",
        "analise-recursal-firac", "analise-probatoria", "resumo-processo", "advogado-do-diabo",
        "estrategia-contestacao", "estrategia-apelacao", "relatorio-inteligencia"]),
    ("Lado-julgador", ["sentenca-civel", "sentenca-criminal", "decisao-saneamento",
        "relatorio-peticao-inicial"]),
    ("Instrução, prova & oratória", ["interrogatorio-cruzado", "inquiricao-audiencia",
        "quesitos-periciais", "especificacao-provas", "audiencia-instrucao", "sustentacao-oral",
        "arsenal-retorico", "transcricao-audiencia", "narrativa-dos-fatos"]),
    ("Execução penal", ["agravo-execucao", "pedido-remicao", "pedido-indulto",
        "pedido-progressao", "revisao-criminal"]),
    ("Criminal", ["criminal", "habeas-corpus", "custodia", "flagrante", "interrogatorio-policial",
        "nulidades", "defesa-criminal", "cabimento-recursal", "restituicao-coisas",
        "pedido-liberdade", "analise-inquerito", "dossie-tribunal-juri", "rese", "denuncia"]),
    ("Família & Sucessões", ["divorcio", "alimentos", "inventario"]),
    ("Imobiliário", ["usucapiao", "despejo"]),
    ("Tributário", ["execucao-fiscal", "mandado-seguranca-tributario"]),
    ("Direito Público", ["mandado-seguranca"]),
    ("Societário & Empresarial", ["contrato-social", "due-diligence"]),
    ("Contratual", ["minuta-contrato", "revisao-clausula", "comparacao-contratos"]),
    ("Consumidor", ["cdc"]),
    ("Digital / LGPD", ["lgpd", "direito-digital"]),
    ("Recursos cíveis & superiores", ["apelacao-civel", "contrarrazoes", "agravo-instrumento",
        "agravo-regimental", "embargos-declaracao", "recurso-especial-civel",
        "recurso-extraordinario-civel", "destrancamento", "recurso"]),
    ("Cível — peças & instrução", ["peticao-inicial", "contestacao", "replica", "acao-cobranca",
        "cumprimento-sentenca", "impugnacao-cumprimento", "calculo-judicial", "alegacoes-finais-civel"]),
    ("Relação com cliente", ["triagem", "orientacao-inicial", "onboarding", "follow-up", "traducao-cliente"]),
    ("Gestão de prazos & carteira", ["monitor-dje", "lembrete-prazo", "andamento-processual",
        "intimacao", "ciencia"]),
    ("Operação & consultivo", ["agenda-audiencia", "cobranca-honorarios", "backup-escritorio",
        "procuracao", "parecer-juridico"]),
]

def categorize(fname):
    f = fname.lower()
    for cat, kws in RULES:
        if any(k in f for k in kws):
            return cat
    return "Outros"

agents = []
for p in sorted(AGENTS_DIR.glob("*.md")):
    if p.name.lower() == "readme.md":
        continue
    txt = p.read_text(encoding="utf-8")
    name, desc, tools, model, body = parse(txt)
    agents.append({
        "name": name or p.stem,
        "file": p.name,
        "desc": desc,
        "tools": [t.strip() for t in tools.split(",")] if tools else [],
        "model": model,
        "cat": categorize(p.name),
        "body": body,
        "full": txt.strip(),
    })

# ordena por categoria depois nome
cat_order = [c for c, _ in RULES] + ["Outros"]
agents.sort(key=lambda a: (cat_order.index(a["cat"]) if a["cat"] in cat_order else 99, a["name"]))

cats = []
for a in agents:
    if a["cat"] not in cats:
        cats.append(a["cat"])

data_json = json.dumps(agents, ensure_ascii=False).replace("</", "<\\/")
cats_json = json.dumps(cats, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Banco de Prompts — Subagents Jurídicos</title>
<style>
  :root{
    --bg:#0f1115; --card:#171a21; --card2:#1d212b; --txt:#e7e9ee; --mut:#9aa3b2;
    --acc:#5b8cff; --acc2:#7c5bff; --line:#2a2f3a; --chip:#222836; --ok:#36d399;
  }
  @media (prefers-color-scheme: light){
    :root{ --bg:#f4f6fb; --card:#ffffff; --card2:#f0f3f9; --txt:#1a1f2b; --mut:#5a6473;
           --line:#e3e8f0; --chip:#eef2f8; }
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
  header{position:sticky;top:0;z-index:10;background:linear-gradient(180deg,var(--bg),rgba(0,0,0,0));
         padding:18px 20px 10px;backdrop-filter:blur(6px)}
  h1{margin:0 0 2px;font-size:20px;font-weight:700}
  h1 .accent{background:linear-gradient(90deg,var(--acc),var(--acc2));-webkit-background-clip:text;background-clip:text;color:transparent}
  .sub{color:var(--mut);font-size:13px;margin-bottom:12px}
  .controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
  #q{flex:1;min-width:220px;padding:11px 14px;border-radius:10px;border:1px solid var(--line);
     background:var(--card);color:var(--txt);font-size:14px;outline:none}
  #q:focus{border-color:var(--acc)}
  .chips{display:flex;gap:6px;flex-wrap:wrap;padding:10px 20px 4px}
  .chip{padding:6px 11px;border-radius:999px;border:1px solid var(--line);background:var(--chip);
        color:var(--mut);font-size:12.5px;cursor:pointer;user-select:none;white-space:nowrap}
  .chip.active{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600}
  main{padding:8px 20px 60px;max-width:1200px;margin:0 auto}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:15px 16px;
        display:flex;flex-direction:column;gap:9px}
  .card h3{margin:0;font-size:15.5px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
  .meta{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
  .tag{font-size:11px;padding:2px 8px;border-radius:999px;background:var(--chip);color:var(--mut);border:1px solid var(--line)}
  .tag.cat{background:linear-gradient(90deg,rgba(91,140,255,.16),rgba(124,91,255,.16));color:var(--acc);border-color:transparent}
  .tag.web{color:var(--ok)}
  .desc{color:var(--mut);font-size:13px;max-height:4.5em;overflow:hidden;position:relative;transition:max-height .25s}
  .desc.open{max-height:60em}
  .row{display:flex;gap:8px;margin-top:2px}
  button.act{flex:1;padding:8px 10px;border-radius:9px;border:1px solid var(--line);background:var(--card2);
        color:var(--txt);font-size:12.5px;cursor:pointer;transition:.15s}
  button.act:hover{border-color:var(--acc);color:var(--acc)}
  button.act.copied{border-color:var(--ok);color:var(--ok)}
  pre.body{display:none;white-space:pre-wrap;word-break:break-word;background:var(--card2);
       border:1px solid var(--line);border-radius:10px;padding:12px;margin:4px 0 0;font:12px/1.5 ui-monospace,Menlo,monospace;max-height:420px;overflow:auto}
  pre.body.open{display:block}
  .empty{color:var(--mut);text-align:center;padding:40px}
  footer{color:var(--mut);font-size:12px;text-align:center;padding:24px}
  a{color:var(--acc)}
</style>
</head>
<body>
<header>
  <h1><span class="accent">Banco de Prompts</span> — Subagents Jurídicos</h1>
  <div class="sub" id="count"></div>
  <div class="controls">
    <input id="q" type="search" placeholder="Buscar por nome, descrição ou conteúdo do prompt…" autofocus>
  </div>
</header>
<div class="chips" id="chips"></div>
<main><div class="grid" id="grid"></div><div class="empty" id="empty" style="display:none">Nenhum agente encontrado.</div></main>
<footer>Gerado a partir de <code>~/.claude/agents</code> · clique em <b>Ver prompt</b> para expandir · <b>Copiar</b> põe o texto na área de transferência.</footer>
<script>
const AGENTS = __DATA__;
const CATS = __CATS__;
let activeCat = "Todos", query = "";

const grid = document.getElementById('grid');
const chipsEl = document.getElementById('chips');
const countEl = document.getElementById('count');
const emptyEl = document.getElementById('empty');

function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}

function makeChip(label){
  const c=document.createElement('span');
  c.className='chip'+(label===activeCat?' active':'');
  c.textContent=label;
  c.onclick=()=>{activeCat=label;render();[...chipsEl.children].forEach(x=>x.classList.toggle('active',x.textContent===label));};
  return c;
}
chipsEl.appendChild(makeChip("Todos"));
CATS.forEach(c=>chipsEl.appendChild(makeChip(c)));

function copy(txt, btn){
  navigator.clipboard.writeText(txt).then(()=>{
    const old=btn.textContent; btn.textContent='✓ Copiado'; btn.classList.add('copied');
    setTimeout(()=>{btn.textContent=old;btn.classList.remove('copied');},1300);
  });
}

function card(a){
  const el=document.createElement('div'); el.className='card';
  const web=a.tools.some(t=>/WebSearch/i.test(t));
  el.innerHTML =
    '<h3>'+esc(a.name)+'</h3>'+
    '<div class="meta"><span class="tag cat">'+esc(a.cat)+'</span>'+
      (a.model?'<span class="tag">'+esc(a.model)+'</span>':'')+
      (web?'<span class="tag web">🌐 web</span>':'')+
      '<span class="tag">'+a.tools.length+' tools</span></div>'+
    '<div class="desc">'+esc(a.desc)+'</div>'+
    '<div class="row">'+
      '<button class="act" data-act="desc">Ver descrição</button>'+
      '<button class="act" data-act="body">Ver prompt</button>'+
    '</div>'+
    '<pre class="body"></pre>'+
    '<div class="row">'+
      '<button class="act" data-act="copybody">Copiar prompt</button>'+
      '<button class="act" data-act="copyfull">Copiar .md</button>'+
      '<button class="act" data-act="download">⬇ Baixar .md</button>'+
    '</div>';
  const descEl=el.querySelector('.desc');
  const pre=el.querySelector('pre.body'); pre.textContent=a.body;
  el.querySelector('[data-act=desc]').onclick=(e)=>{descEl.classList.toggle('open');
     e.target.textContent=descEl.classList.contains('open')?'Ocultar descrição':'Ver descrição';};
  el.querySelector('[data-act=body]').onclick=(e)=>{pre.classList.toggle('open');
     e.target.textContent=pre.classList.contains('open')?'Ocultar prompt':'Ver prompt';};
  el.querySelector('[data-act=copybody]').onclick=(e)=>copy(a.body,e.target);
  el.querySelector('[data-act=copyfull]').onclick=(e)=>copy(a.full,e.target);
  el.querySelector('[data-act=download]').onclick=()=>download(a.file,a.full);
  return el;
}

function download(name, text){
  const blob=new Blob([text],{type:'text/markdown;charset=utf-8'});
  const url=URL.createObjectURL(blob);
  const link=document.createElement('a'); link.href=url; link.download=name; link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1500);
}

function render(){
  const q=query.trim().toLowerCase();
  const list=AGENTS.filter(a=>{
    if(activeCat!=="Todos" && a.cat!==activeCat) return false;
    if(!q) return true;
    return (a.name+' '+a.desc+' '+a.body).toLowerCase().includes(q);
  });
  grid.innerHTML='';
  list.forEach(a=>grid.appendChild(card(a)));
  emptyEl.style.display=list.length?'none':'block';
  countEl.textContent=list.length+' de '+AGENTS.length+' agentes'+(activeCat!=="Todos"?' · '+activeCat:'');
}
document.getElementById('q').addEventListener('input',e=>{query=e.target.value;render();});
render();
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA__", data_json).replace("__CATS__", cats_json)
OUT.write_text(HTML, encoding="utf-8")
print("OK ->", OUT)
print("Agentes:", len(agents), "| Categorias:", len(cats))
