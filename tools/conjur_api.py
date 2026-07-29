# -*- coding: utf-8 -*-
"""Consulta a WP REST API do ConJur de dentro do Chrome real (Playwright).

A API (`/wp-json/wp/v2/...`) devolve JSON estruturado, mas o domínio inteiro
está atrás do desafio JS do Cloudflare — daí fazer o `fetch` DENTRO da página
já liberada, reaproveitando o cookie cf_clearance do perfil persistente.
"""
from __future__ import annotations
import json, sys, time, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conjur_browser import Navegador

BASE = "https://conjur.com.br"


class ApiConjur:
    def __init__(self, visivel: bool = True):
        self.nav = Navegador(visivel=visivel)
        self._pronto = False

    def _ensure(self):
        if self._pronto:
            return
        self.nav._ensure()
        pg = self.nav._ctx.pages[0]
        pg.goto(BASE + "/", wait_until="domcontentloaded", timeout=90000)
        for _ in range(15):
            time.sleep(3)
            if "momento" not in pg.title().lower() and "moment" not in pg.title().lower():
                break
        self._pronto = True

    def get(self, caminho: str):
        """GET em /wp-json/... a partir do contexto da página (passa o Cloudflare)."""
        self._ensure()
        pg = self.nav._ctx.pages[0]
        url = caminho if caminho.startswith("http") else BASE + caminho
        r = pg.evaluate(
            """async (u) => {
                const resp = await fetch(u, {credentials:'include'});
                return {status: resp.status, body: await resp.text()};
            }""", url)
        if r["status"] != 200:
            raise RuntimeError(f"HTTP {r['status']} em {url}: {r['body'][:200]}")
        return json.loads(r["body"])

    def html(self, url: str) -> str:
        self._ensure()
        pg = self.nav._ctx.pages[0]
        r = pg.evaluate(
            """async (u) => {
                const resp = await fetch(u, {credentials:'include'});
                return {status: resp.status, body: await resp.text()};
            }""", url)
        if r["status"] != 200:
            raise RuntimeError(f"HTTP {r['status']} em {url}")
        return r["body"]

    def close(self):
        self.nav.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    with ApiConjur() as api:
        for termo in ["senso-incomum", "criminal-player", "justo-processo",
                      "direito-de-defesa", "critica-penal", "direitos-fundamentais"]:
            for tax in ("categories", "tags"):
                try:
                    d = api.get(f"/wp-json/wp/v2/{tax}?search={termo}&per_page=10")
                    for it in d:
                        print(f"{tax:11s} id={it['id']:<7} count={it.get('count'):<6} slug={it['slug']}")
                except Exception as e:
                    print(tax, termo, "ERRO", e)
