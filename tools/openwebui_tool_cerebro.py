"""
title: Cérebro Jurídico — autos do caso
author: local
version: 0.1
description: Busca nos autos fatiados do caso (FTS5 + vetorial) e lê linha do tempo, prazos, prescrição e controvérsia, via rag_server.py local. Só devolve trechos com âncora [ID | vol p. N | tipo | data].
requirements: requests
"""
# Ferramenta (Tool) do Open WebUI. Instalar: Workspace > Tools > + > colar este arquivo.
# Exige `tools/rag_server.py` rodando em 127.0.0.1:8765 (venv RAG). Nada sai da máquina por aqui;
# se o modelo do chat for em nuvem, a UI deve chamar `anonimizar` antes (metodo abaixo).

import requests
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        base_url: str = Field(default="http://127.0.0.1:8765", description="rag_server.py")
        k: int = Field(default=8, description="trechos por consulta")
        reranker: bool = Field(default=False, description="reranker bge (35-40 s) em vez de RRF (1,5 s)")

    def __init__(self):
        self.valves = self.Valves()

    def listar_casos(self) -> str:
        """Lista os casos disponíveis na área de trabalho e o que cada um já tem processado."""
        r = requests.get(f"{self.valves.base_url}/casos", timeout=30).json()
        return "\n".join(f"- {c['cnj']} ({c.get('comarca') or 'comarca ?'}): {', '.join(c['tem'])}" for c in r) or "nenhum caso"

    def buscar_nos_autos(self, pergunta: str, cnj: str, tipo_de_ato: str = "") -> str:
        """Busca trechos dos autos do caso pela pergunta. Cada trecho vem com a âncora [ID | volume p. N | tipo | data]; cite-a sempre.
        :param pergunta: o que procurar (fatos, termos, número de documento)
        :param cnj: número CNJ do caso
        :param tipo_de_ato: opcional: DENUNCIA, DECISAO, SENTENCA, TERMO DE AUDIENCIA, CERTIDAO…
        """
        p = {"q": pergunta, "cnj": cnj, "k": self.valves.k, "reranker": "1" if self.valves.reranker else "0"}
        if tipo_de_ato:
            p["tipo"] = tipo_de_ato
        r = requests.get(f"{self.valves.base_url}/buscar", params=p, timeout=300).json()
        if "erro" in r:
            return f"erro: {r['erro']}"
        out = []
        for i, x in enumerate(r.get("resultados", []), 1):
            t = " ".join(x["texto"].split())[:900]
            out.append(f"{i}. {x['ref']}\n{t}")
        return "\n\n".join(out) or "nada encontrado (o caso está indexado? veja listar_casos)"

    def ler_do_caso(self, cnj: str, arquivo: str = "linha-do-tempo.md") -> str:
        """Lê um arquivo já processado do caso: linha-do-tempo.md, distill/prazos.md, distill/prescricao.md, distill/controversia.md, distill/nulidades.md.
        :param cnj: número CNJ
        :param arquivo: caminho relativo dentro do caso
        """
        r = requests.get(f"{self.valves.base_url}/caso/{cnj}/{arquivo}", timeout=60)
        return r.text[:12000] if r.ok else f"erro {r.status_code}: {r.text[:200]}"

    def anonimizar(self, cnj: str, texto: str) -> str:
        """Troca nomes de partes/testemunhas e CPF/RG/telefone por pseudônimos estáveis (PESSOA_n, CPF_n) antes de mandar texto a um modelo em nuvem.
        :param cnj: número CNJ (o mapa é por caso)
        :param texto: texto a pseudonimizar
        """
        r = requests.post(f"{self.valves.base_url}/anonimizar", json={"cnj": cnj, "texto": texto}, timeout=60).json()
        return r.get("texto", f"erro: {r}")

    def validar_minuta(self, cnj: str, minuta: str, peca: str = "outra", rito: str = "ordinario") -> str:
        """Passa a minuta pelo gate: citações conferidas nas fontes canônicas e nos autos, pedidos × fundamentação, rito e prazo. Devolve o status e os alertas.
        :param cnj: número CNJ
        :param minuta: texto completo da minuta
        :param peca: resposta-acusacao, memoriais, apelacao, hc, rese, resp, re…
        :param rito: ordinario, sumario ou jecrim
        """
        r = requests.post(f"{self.valves.base_url}/validar", json={"cnj": cnj, "minuta": minuta, "peca": peca, "rito": rito}, timeout=600).json()
        res = r.get("resumo", {})
        return f"STATUS: {res.get('status')}\n\n{r.get('minuta.validacao-fontes.md', '')[:4000]}\n\n{r.get('minuta.validacao-processual.md', '')[:4000]}"
