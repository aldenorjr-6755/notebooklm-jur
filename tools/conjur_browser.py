# -*- coding: utf-8 -*-
"""Busca HTML do ConJur com Chrome REAL (Playwright), porque conjur.com.br
passou a exigir desafio JS do Cloudflare — urllib/curl levam 403 "Just a moment".

Padrão calibrado em ~/.notebooklm/jusbrasil/jusbrasil_client.py: headless NÃO
passa; Chrome headed com a janela fora da tela (--window-position) passa.
Perfil persistente próprio para guardar o cookie cf_clearance entre execuções.
"""
from __future__ import annotations
import os, time

PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".notebooklm", "tools", "profile_conjur")


class Navegador:
    def __init__(self, visivel: bool = False):
        self.visivel = visivel
        self._pw = None
        self._ctx = None

    def _ensure(self):
        if self._ctx is not None:
            return
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        args = ["--disable-blink-features=AutomationControlled"]
        if not self.visivel:
            args += ["--window-position=-32000,-32000"]
        os.makedirs(PROFILE_DIR, exist_ok=True)
        self._ctx = self._pw.chromium.launch_persistent_context(
            PROFILE_DIR, headless=False, channel="chrome",
            viewport={"width": 1280, "height": 900}, args=args,
        )

    def html(self, url: str, espera: float = 1.5, tentativas: int = 3) -> str:
        self._ensure()
        pg = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
        for t in range(tentativas):
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(espera)
            h = pg.content()
            if "Just a moment" not in h and "challenges.cloudflare.com" not in h:
                return h
            time.sleep(4 + 3 * t)          # dá tempo ao desafio JS resolver
            h = pg.content()
            if "Just a moment" not in h:
                return h
        raise RuntimeError("Cloudflare não liberou: " + url)

    def close(self):
        try:
            if self._ctx is not None:
                self._ctx.close()
        finally:
            self._ctx = None
            if self._pw is not None:
                self._pw.stop()
                self._pw = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


if __name__ == "__main__":
    import sys, re
    with Navegador() as nav:
        h = nav.html(sys.argv[1] if len(sys.argv) > 1
                     else "https://www.conjur.com.br/colunistas/senso-incomum/")
        print(len(h), "chars")
        print(len(re.findall(r'href="(https://www\.conjur\.com\.br/\d{4}-[a-z]{3}-\d{2}/[^"]+)"', h)), "links de artigo")
