#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anonimizar.py — pseudonimizacao ESTAVEL de texto de autos antes de sair da maquina (espec §5.4).

O que troca:
  * PESSOAS: nomes lidos da capa do PJe ("NOME (REU)", "NOME (ADVOGADO)"...), do "ROL DE TESTEMUNHAS"
    da denuncia e de listas dadas por --nomes (um nome por linha). Casamento insensivel a caixa e a
    acento (OCR escreve REGO e RÊGO). Cada nome vira PESSOA_n, sempre o mesmo n no mesmo caso.
  * IDENTIFICADORES por regex: CPF, CNPJ, RG, telefone, e-mail, CEP, placa, IMEI, conta/agencia.
  * TERMOS extras por --termos (ex.: nome da fazenda, do bairro): viram LOCAL_n / TERMO_n.
O que NAO troca (de proposito): numero CNJ (publico), orgaos (MP, TJMA, IBAMA), assinantes do
carimbo do PJe (servidores e magistrados sao agentes publicos; inclua por --nomes se quiser).

Mapa por caso em %LOCALAPPDATA%\\cerebro\\anon\\<CNJ>.json (FORA do OneDrive). Ainda nao e' cifrado:
a pasta fica no perfil do usuario; ciframento e' pendencia declarada na espec.

--sugerir lista candidatos a nome (sequencias em MAIUSCULAS que nao sao instituicao) para o
humano aprovar; nunca aplica sugestao sozinho. Revisao humana do mapa e' obrigatoria na primeira
peca de cada caso.

Uso:
  python anonimizar.py --cnj <CNJ> --capa extracted/atos/0001_CAPA*.md --nomes extra.txt --sugerir atos/0002_*.md
  python anonimizar.py --cnj <CNJ> ato.md               -> escreve ato.anon.md
  python anonimizar.py --cnj <CNJ> --stdout ato.md      -> imprime
  python anonimizar.py --cnj <CNJ> --reverter resposta.md
  python anonimizar.py --cnj <CNJ> --mapa               -> mostra o mapa
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

DIR_ANON = Path(os.environ.get("CEREBRO_DIR") or Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "cerebro") / "anon"

# nome e papel na MESMA linha ([ \t], nunca \s: com \s o casamento preguicoso engolia as linhas
# anteriores — "MINISTERIO PUBLICO ... AUTOR ... ELIO DIAS DA CRUZ (REU)" virava um nome so)
RE_CAPA_PARTE = re.compile(r"^[ \t]*([A-ZÁÉÍÓÚÂÊÔÃÕÇÜ][A-ZÁÉÍÓÚÂÊÔÃÕÇÜ' \t\.-]{4,80}?)[ \t]*\((R[ÉE]U|R[ÉE]|AUTORA?|ADVOGAD[OA]|V[ÍI]TIMA|TESTEMUNHA|INVESTIGAD[OA]|INDICIAD[OA]|DENUNCIAD[OA]|QUERELAD[OA]|QUERELANTE|REPRESENTANTE|ASSISTENTE|DEFENSOR[A]?|CURADOR[A]?|TERCEIRO INTERESSADO)\)\s*$", re.M)
STOP_INSTITUICAO = {"TRIBUNAL", "JUSTIÇA", "JUSTICA", "MINISTÉRIO", "MINISTERIO", "PÚBLICO", "PUBLICO", "ESTADUAL", "FEDERAL",
                    "VARA", "COMARCA", "ESTADO", "MARANHÃO", "MARANHAO", "JUIZ", "JUÍZA", "JUIZA", "SENHOR", "SENHORA",
                    "EXCELENTÍSSIMO", "EXCELENTISSIMO", "EXCELENTÍSSIMA", "EXCELENTISSIMA", "DOUTOR", "DOUTORA", "DIREITO",
                    "PENAL", "AÇÃO", "ACAO", "PÚBLICA", "PUBLICA", "PROCESSO", "DENÚNCIA", "DENUNCIA", "ROL", "TESTEMUNHAS",
                    "PODER", "JUDICIÁRIO", "JUDICIARIO", "FÓRUM", "FORUM", "SECRETARIA", "PROMOTORIA", "DEFENSORIA",
                    "POLÍCIA", "POLICIA", "CIVIL", "MILITAR", "DELEGACIA", "IBAMA", "ICMBIO", "SEMA", "INSTITUTO",
                    "BRASILEIRO", "NACIONAL", "MEIO", "AMBIENTE", "RECURSOS", "NATURAIS", "OPERAÇÃO", "OPERACAO",
                    "CONTROLE", "REMOTO", "AUTO", "INFRAÇÃO", "INFRACAO", "TERMO", "EMBARGO", "LEI", "ART", "CÓDIGO",
                    "CODIGO", "PENA", "RECLUSÃO", "RECLUSAO", "DETENÇÃO", "DETENCAO", "DECISÃO", "DECISAO", "DESPACHO",
                    "SENTENÇA", "SENTENCA", "CERTIDÃO", "CERTIDAO", "CARTA", "PRECATÓRIA", "PRECATORIA", "MANDADO",
                    "OFÍCIO", "OFICIO", "AUDIÊNCIA", "AUDIENCIA", "INSTRUÇÃO", "INSTRUCAO", "JULGAMENTO", "RESPOSTA",
                    "ACUSAÇÃO", "ACUSACAO", "ALEGAÇÕES", "ALEGACOES", "FINAIS", "MEMORIAIS", "DOS", "DAS", "DE", "DA",
                    "DO", "E", "PARA", "COM", "SEM", "NUM", "PÁG", "PAG", "ID", "OAB", "MA", "CEP", "AV", "RUA", "SÃO",
                    "SAO", "LUÍS", "LUIS", "ITINGA", "IMPERATRIZ", "BRASIL", "GOVERNO", "SUPERINTENDÊNCIA", "SUPERINTENDENCIA"}
# nomes ficam numa linha so: [ \t]+ (nao \s+) para nao colar palavras de linhas vizinhas
RE_MAIUSCULAS = re.compile(r"\b([A-ZÁÉÍÓÚÂÊÔÃÕÇÜ]{2,}(?:[ \t]+(?:DE|DA|DO|DOS|DAS|E)[ \t]+|[ \t]+)[A-ZÁÉÍÓÚÂÊÔÃÕÇÜ]{2,}(?:(?:[ \t]+(?:DE|DA|DO|DOS|DAS|E))?[ \t]+[A-ZÁÉÍÓÚÂÊÔÃÕÇÜ]{2,}){0,4})\b")

IDENTIFICADORES = [
    ("CPF", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")),
    ("CNPJ", re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("TEL", re.compile(r"(?<!\d)(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[-\s]\d{4}(?!\d)")),
    ("PLACA", re.compile(r"\b[A-Z]{3}-?\d[A-Z0-9]\d{2}\b")),
    ("IMEI", re.compile(r"(?<!\d)\d{15}(?!\d)")),
    ("CEP", re.compile(r"\b\d{5}-\d{3}\b")),
    ("RG", re.compile(r"(?<=\bRG\s)\s*n?[ºo°.]?\s*:?\s*\d{1,2}\.?\d{3}\.?\d{3}-?[\dXx]?\b|(?<=\bRG n[ºo°] )\d{5,14}\b|(?<=\bRG n[ºo°]: )\d{5,14}\b|(?<=\bRG: )\d{5,14}\b|(?<=\bRG )\d{5,14}\b", re.I)),
]
# numeros que NAO sao identificadores pessoais e casam com as regex acima: CNJ e Num. do PJe
RE_PRESERVAR = [re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}"), re.compile(r"Num\.\s*\d+"), re.compile(r"\b\d{20,}\b")]


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


_VAR = {"A": "AÁÀÂÃÄ", "E": "EÉÈÊË", "I": "IÍÌÎ", "O": "OÓÒÔÕÖ", "U": "UÚÙÛÜ", "C": "CÇ"}


def _regex_nome(nome: str) -> re.Pattern:
    """Regex do nome tolerante a acento e a espacos multiplos; caixa insensivel."""
    partes = []
    for ch in _sem_acento(nome).upper():
        if ch == " ":
            partes.append(r"\s+")
        elif ch in _VAR:
            partes.append("[" + _VAR[ch] + _VAR[ch].lower() + "]")
        else:
            partes.append(re.escape(ch) if not ch.isalpha() else "[" + ch + ch.lower() + "]")
    return re.compile(r"(?<![A-Za-zÀ-ÿ])" + "".join(partes) + r"(?![A-Za-zÀ-ÿ])")


class Anonimizador:
    def __init__(self, cnj: str):
        self.cnj = cnj
        DIR_ANON.mkdir(parents=True, exist_ok=True)
        self.caminho = DIR_ANON / f"{cnj}.json"
        self.mapa: dict = {"cnj": cnj, "pessoas": {}, "termos": {}, "identificadores": {}}
        if self.caminho.is_file():
            self.mapa = json.loads(self.caminho.read_text(encoding="utf-8"))

    def salvar(self):
        self.caminho.write_text(json.dumps(self.mapa, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- cadastro
    def _proximo(self, prefixo: str, grupo: dict) -> str:
        n = 1 + len({v for v in grupo.values() if v.startswith(prefixo + "_")})
        return f"{prefixo}_{n}"

    def adicionar_pessoa(self, nome: str, papel: str = "") -> str:
        chave = _sem_acento(" ".join(nome.split())).upper()
        if len(chave) < 5:
            return ""
        if chave not in self.mapa["pessoas"]:
            self.mapa["pessoas"][chave] = {"token": self._proximo("PESSOA", {k: v["token"] for k, v in self.mapa["pessoas"].items()}),
                                           "original": " ".join(nome.split()), "papel": papel}
        return self.mapa["pessoas"][chave]["token"]

    def adicionar_termo(self, termo: str, prefixo: str = "TERMO") -> str:
        chave = _sem_acento(" ".join(termo.split())).upper()
        if chave not in self.mapa["termos"]:
            self.mapa["termos"][chave] = {"token": self._proximo(prefixo, {k: v["token"] for k, v in self.mapa["termos"].items()}),
                                          "original": " ".join(termo.split())}
        return self.mapa["termos"][chave]["token"]

    def ler_capa(self, texto: str) -> int:
        n = 0
        for m in RE_CAPA_PARTE.finditer(texto):
            nome, papel = m.group(1).strip(" .-"), m.group(2)
            if nome.split()[0] in STOP_INSTITUICAO and len(nome.split()) > 3 and "PUBLICO" in _sem_acento(nome):
                continue   # MINISTERIO PUBLICO ... (AUTOR)
            self.adicionar_pessoa(nome, papel)
            n += 1
        return n

    def ler_rol_testemunhas(self, texto: str) -> int:
        """Le o bloco 'ROL DE TESTEMUNHAS': uma testemunha por linha ('NOME, qualificacao'), ate a
        primeira linha que nao comeca por nome em maiusculas (ex.: 'Denunciado:', local/data, assinatura)."""
        n = 0
        m = re.search(r"ROL\s+DE\s+TESTEMUNHAS?[:\s]*\n", texto, re.I)
        if not m:
            return 0
        sem_nome = 0
        for ln in texto[m.end():].split("\n"):
            s = ln.strip()
            if not s:
                continue
            if re.match(r"(DENUNCIAD|ACUSAD|R[ÉE]U\b|ITINGA|S[ÃA]O LU[ÍI]S|SIMP|COTA\b|MM[ºo]?\.?\s*JU)", s, re.I):
                break
            mm = RE_MAIUSCULAS.match(s)
            if not mm or not self._candidato(mm.group(1)):
                # continuacao da qualificacao da testemunha anterior ("documentos anexos;"): tolera ate 2
                sem_nome += 1
                if sem_nome > 2:
                    break
                continue
            sem_nome = 0
            chave = _sem_acento(mm.group(1)).upper()
            if chave in self.mapa["pessoas"]:
                continue        # ja cadastrado com outro papel (reu pela capa): nao rebaixa a testemunha
            self.adicionar_pessoa(mm.group(1), "TESTEMUNHA")
            n += 1
        return n

    def _candidato(self, c: str) -> bool:
        toks = [t for t in c.split() if t not in ("DE", "DA", "DO", "DOS", "DAS", "E")]
        return 2 <= len(toks) <= 6 and not any(t in STOP_INSTITUICAO for t in toks) and not any(ch.isdigit() for ch in c)

    def sugerir(self, texto: str) -> list[str]:
        ja = set(self.mapa["pessoas"])
        out = {}
        for c in RE_MAIUSCULAS.findall(texto):
            if self._candidato(c) and _sem_acento(c).upper() not in ja:
                out[c] = out.get(c, 0) + 1
        return [f"{c} (x{n})" for c, n in sorted(out.items(), key=lambda x: -x[1])]

    # ---- aplicacao
    def anonimizar(self, texto: str) -> str:
        preservar: list[str] = []

        def guardar(m):
            preservar.append(m.group(0))
            return f"\x00{len(preservar) - 1}\x00"
        for rx in RE_PRESERVAR:
            texto = rx.sub(guardar, texto)
        # pessoas: nomes mais longos primeiro (evita trocar "DIAS DA CRUZ" dentro de "ELIO DIAS DA CRUZ")
        for chave, v in sorted(self.mapa["pessoas"].items(), key=lambda kv: -len(kv[0])):
            texto = _regex_nome(v["original"]).sub(v["token"], texto)
            # sobrenome composto isolado (>= 2 palavras finais), tolerado como variante
            partes = v["original"].split()
            if len(partes) >= 3:
                texto = _regex_nome(" ".join(partes[-2:])).sub(v["token"], texto)
        for chave, v in sorted(self.mapa["termos"].items(), key=lambda kv: -len(kv[0])):
            texto = _regex_nome(v["original"]).sub(v["token"], texto)
        for prefixo, rx in IDENTIFICADORES:
            def sub(m, prefixo=prefixo):
                val = m.group(0)
                if val not in self.mapa["identificadores"]:
                    n = 1 + sum(1 for x in self.mapa["identificadores"].values() if x.startswith(prefixo + "_"))
                    self.mapa["identificadores"][val] = f"{prefixo}_{n}"
                return self.mapa["identificadores"][val]
            texto = rx.sub(sub, texto)
        texto = re.sub(r"\x00(\d+)\x00", lambda m: preservar[int(m.group(1))], texto)
        return texto

    def reverter(self, texto: str) -> str:
        for v in self.mapa["pessoas"].values():
            texto = re.sub(r"\b" + re.escape(v["token"]) + r"\b", v["original"], texto)
        for v in self.mapa["termos"].values():
            texto = re.sub(r"\b" + re.escape(v["token"]) + r"\b", v["original"], texto)
        for orig, tok in self.mapa["identificadores"].items():
            texto = re.sub(r"\b" + re.escape(tok) + r"\b", orig, texto)
        return texto

    def resumo(self) -> str:
        p = [f"{v['token']} = {v['original']} ({v['papel'] or '-'})" for v in self.mapa["pessoas"].values()]
        t = [f"{v['token']} = {v['original']}" for v in self.mapa["termos"].values()]
        i = [f"{tok} = {orig}" for orig, tok in self.mapa["identificadores"].items()]
        return "\n".join(["pessoas:"] + (p or ["  (nenhuma)"]) + ["termos:"] + (t or ["  (nenhum)"]) + ["identificadores:"] + (i or ["  (nenhum)"]))


def _corpo(caminho: Path) -> str:
    md = io.open(caminho, encoding="utf-8", errors="replace").read()
    return md.split("\n---\n", 1)[-1] if md.startswith("---") else md


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivos", nargs="*")
    ap.add_argument("--cnj", required=True)
    ap.add_argument("--capa", help="ato da capa (lista de partes)")
    ap.add_argument("--denuncia", help="ato da denúncia (rol de testemunhas)")
    ap.add_argument("--nomes", help="arquivo com um nome por linha (opcional: NOME|PAPEL)")
    ap.add_argument("--termos", help="arquivo com termos a mascarar (fazenda, bairro...), um por linha")
    ap.add_argument("--sugerir", action="store_true", help="lista candidatos a nome nos arquivos, sem aplicar")
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("--reverter", action="store_true")
    ap.add_argument("--mapa", action="store_true", help="mostra o mapa do caso")
    a = ap.parse_args(argv)
    an = Anonimizador(a.cnj)
    if a.capa:
        print(f"capa: {an.ler_capa(_corpo(Path(a.capa)))} partes lidas")
    if a.denuncia:
        print(f"denúncia: {an.ler_rol_testemunhas(_corpo(Path(a.denuncia)))} testemunhas lidas do rol")
    if a.nomes:
        for ln in io.open(a.nomes, encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nome, _, papel = ln.partition("|")
                an.adicionar_pessoa(nome.strip(), papel.strip())
    if a.termos:
        for ln in io.open(a.termos, encoding="utf-8"):
            if ln.strip() and not ln.startswith("#"):
                an.adicionar_termo(ln.strip(), "LOCAL")
    an.salvar()
    if a.mapa:
        print(an.resumo())
    if a.sugerir:
        for f in a.arquivos:
            print(f"== candidatos em {f} (aprovar em --nomes):")
            for c in an.sugerir(_corpo(Path(f)))[:40]:
                print("  ", c)
        return 0
    for f in a.arquivos:
        p = Path(f)
        txt = io.open(p, encoding="utf-8", errors="replace").read()
        out = an.reverter(txt) if a.reverter else an.anonimizar(txt)
        an.salvar()
        if a.stdout:
            print(out)
        else:
            dest = p.with_suffix((".rev" if a.reverter else ".anon") + p.suffix)
            io.open(dest, "w", encoding="utf-8", newline="\n").write(out)
            print(f"-> {dest}")
    if not a.arquivos and not a.mapa:
        print(an.resumo())
    return 0


if __name__ == "__main__":
    sys.exit(main())
