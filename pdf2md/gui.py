#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Interface grafica do pdf2md (Tkinter, sem dependencia externa).

    python -m pdf2md --gui        ou        PDF2MD.bat

A conversao roda numa thread separada e conversa com a janela por uma fila,
para que a interface continue respondendo (e cancelavel) mesmo durante um
processo do PJe com milhares de paginas.
"""
from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import ambiente
from .nucleo import coletar_pdfs, converter, detectar_perfil
from .perfis import ORDEM, PERFIS, obter

TITULO = "pdf2md — conversor de PDF para Markdown"
ROTULO_OCR = {"auto": "Automatico (so nas paginas digitalizadas)",
              "sempre": "Sempre (refaz OCR em todas as paginas)",
              "nunca": "Nunca (so a camada de texto do PDF)"}
OCR_POR_ROTULO = {v: k for k, v in ROTULO_OCR.items()}


class App(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=10)
        self.master = master
        self.pack(fill="both", expand=True)

        self.arquivos: list[Path] = []
        self.fila: queue.Queue = queue.Queue()
        self.cancelar = threading.Event()
        self.worker: threading.Thread | None = None
        self.ultimo_destino: Path | None = None
        self._ajuste_manual = tk.BooleanVar(value=False)

        self._montar()
        self._aplicar_perfil()
        self._alternar_ajuste()
        # Guarda o id para poder cancelar: fechar a janela com um `after`
        # pendente faz o Tcl reclamar de "invalid command name".
        self._tick = self.after(120, self._drenar_fila)
        self.bind("<Destroy>", self._ao_destruir)

    # ------------------------------------------------------------------ UI
    def _montar(self) -> None:
        self.master.title(TITULO)
        self.master.geometry("1020x740")
        self.master.minsize(880, 620)

        # ---------- arquivos ----------
        cx = ttk.LabelFrame(self, text=" 1. Arquivos a converter ", padding=8)
        cx.pack(fill="both", expand=True)

        # Barra de acoes NO TOPO, horizontal. Quando estes botoes ficavam numa
        # coluna a direita da lista, a lista (com expand=True) era empacotada
        # primeiro e os empurrava para fora da janela.
        bt = ttk.Frame(cx)
        bt.pack(side="top", fill="x", pady=(0, 8))
        for txt, cmd, esp in (("Adicionar PDFs...", self.add_arquivos, (0, 6)),
                              ("Adicionar pasta...", self.add_pasta, (0, 6)),
                              ("Remover selecionado", self.remover, (0, 6)),
                              ("Limpar lista", self.limpar, (0, 0))):
            ttk.Button(bt, text=txt, command=cmd).pack(side="left", padx=esp)
        self.var_recursivo = tk.BooleanVar(value=True)
        ttk.Checkbutton(bt, text="Incluir subpastas",
                        variable=self.var_recursivo).pack(side="left", padx=(16, 0))

        # Lista abaixo da barra, ocupando o resto do espaco.
        corpo = ttk.Frame(cx)
        corpo.pack(side="top", fill="both", expand=True)

        cols = ("arquivo", "pag", "tipo", "pasta")
        self.lista = ttk.Treeview(corpo, columns=cols, show="headings", height=8)
        for c, t, w, mini, cresce in (
                ("arquivo", "Arquivo", 260, 140, True),
                ("pag", "Pag.", 50, 45, False),
                ("tipo", "Tipo detectado", 140, 110, False),
                ("pasta", "Pasta", 240, 120, True)):
            self.lista.heading(c, text=t)
            self.lista.column(c, width=w, minwidth=mini, stretch=cresce,
                              anchor="e" if c == "pag" else "w")
        sb = ttk.Scrollbar(corpo, orient="vertical", command=self.lista.yview)
        self.lista.configure(yscrollcommand=sb.set)
        self.lista.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ---------- opcoes ----------
        op = ttk.LabelFrame(self, text=" 2. Como converter ", padding=8)
        op.pack(fill="x", pady=(10, 0))
        # A coluna recebe peso para que a celula do rotulo seja dimensionada
        # pelo FRAME, e nao pelo conteudo do proprio rotulo. Sem isso, largura
        # e wraplength se realimentam e a descricao encolhe sozinha.
        op.columnconfigure(0, weight=1)

        # A descricao do perfil fica em LINHA PROPRIA, nao ao lado do combo:
        # ao lado, ela empurrava Idioma e DPI para fora da janela.
        linha_perfil = ttk.Frame(op)
        linha_perfil.grid(row=0, column=0, columnspan=6, sticky="we")
        ttk.Label(linha_perfil, text="Perfil:").pack(side="left")
        self.var_perfil = tk.StringVar(value="auto")
        self.cb_perfil = ttk.Combobox(
            linha_perfil, state="readonly", width=30,
            values=[PERFIS[n].rotulo for n in ORDEM])
        self.cb_perfil.current(0)
        self.cb_perfil.pack(side="left", padx=(6, 0))
        self.cb_perfil.bind("<<ComboboxSelected>>", lambda _e: self._aplicar_perfil())

        self.lbl_desc = ttk.Label(op, text="", wraplength=880,
                                  foreground="#444", justify="left")
        self.lbl_desc.grid(row=1, column=0, columnspan=6, sticky="we", pady=(4, 0))
        # A quebra acompanha a largura real: com valor fixo, a ultima palavra
        # de cada linha ficava cortada na borda ao redimensionar a janela.
        # A quebra segue a largura que o PROPRIO rotulo recebeu. Medir pelo
        # frame nao serve: ele tem 1000 px enquanto a celula do rotulo tem 899,
        # e a diferenca vazava para fora da janela. Mexer no wraplength altera
        # so a altura, entao nao ha laco de reconfiguracao — ainda assim, so
        # reescreve quando muda de fato.
        def _ajustar_quebra(evento):
            largura = max(evento.width - 8, 320)
            if abs(int(self.lbl_desc.cget("wraplength")) - largura) > 4:
                self.lbl_desc.configure(wraplength=largura)

        self.lbl_desc.bind("<Configure>", _ajustar_quebra)

        ttk.Checkbutton(op, text="Ajustar as opcoes manualmente "
                                 "(caso contrario, valem as do perfil)",
                        variable=self._ajuste_manual,
                        command=self._alternar_ajuste
                        ).grid(row=2, column=0, columnspan=6, sticky="w", pady=(8, 4))

        self.campos: list[tk.Widget] = []

        # Linha unica com OCR / Idioma / DPI, empacotada da esquerda para a
        # direita — assim ela nunca ultrapassa a largura util.
        linha_ocr = ttk.Frame(op)
        linha_ocr.grid(row=3, column=0, columnspan=6, sticky="we", padx=(12, 0))

        def rotulo(pai, txt, esq=0):
            w = ttk.Label(pai, text=txt)
            w.pack(side="left", padx=(esq, 4))
            self.campos.append(w)

        rotulo(linha_ocr, "OCR:")
        self.var_ocr = tk.StringVar()
        self.cb_ocr = ttk.Combobox(linha_ocr, state="readonly", width=34,
                                   values=list(ROTULO_OCR.values()),
                                   textvariable=self.var_ocr)
        self.cb_ocr.pack(side="left")
        self.campos.append(self.cb_ocr)

        rotulo(linha_ocr, "Idioma:", 18)
        idiomas = ambiente.idiomas_disponiveis() or ["por"]
        idiomas = [i for i in idiomas if i != "osd"] + ["por+eng"]
        self.var_idioma = tk.StringVar()
        self.cb_idioma = ttk.Combobox(linha_ocr, width=9, values=idiomas,
                                      textvariable=self.var_idioma)
        self.cb_idioma.pack(side="left")
        self.campos.append(self.cb_idioma)

        rotulo(linha_ocr, "DPI:", 18)
        self.var_dpi = tk.IntVar()
        self.sp_dpi = ttk.Spinbox(linha_ocr, from_=150, to=600, increment=50,
                                  width=6, textvariable=self.var_dpi)
        self.sp_dpi.pack(side="left")
        self.campos.append(self.sp_dpi)

        self.var_imagens = tk.BooleanVar()
        self.var_rodape = tk.BooleanVar()
        self.var_estrut = tk.BooleanVar()
        self.var_preproc = tk.BooleanVar()
        grade = ttk.Frame(op)
        grade.grid(row=4, column=0, columnspan=6, sticky="we", padx=(12, 0),
                   pady=(4, 0))
        for i, (txt, var) in enumerate((
                ("Extrair imagens para pasta ao lado", self.var_imagens),
                ("Limpar rodape do PJe (assinatura/URL)", self.var_rodape),
                ("Analisar estrutura (titulos e tabelas)", self.var_estrut),
                ("Realcar imagem antes do OCR (scan ruim)", self.var_preproc))):
            w = ttk.Checkbutton(grade, text=txt, variable=var)
            w.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 24), pady=2)
            self.campos.append(w)
        grade.columnconfigure(0, minsize=300)

        # ---------- saida ----------
        sd = ttk.LabelFrame(self, text=" 3. Onde salvar ", padding=8)
        sd.pack(fill="x", pady=(10, 0))
        self.var_saida = tk.StringVar()
        self.var_mesma_pasta = tk.BooleanVar(value=True)
        ttk.Checkbutton(sd, text="Ao lado do PDF original",
                        variable=self.var_mesma_pasta,
                        command=self._alternar_saida).grid(row=0, column=0, sticky="w")
        self.e_saida = ttk.Entry(sd, textvariable=self.var_saida, width=64)
        self.e_saida.grid(row=0, column=1, padx=8, sticky="we")
        self.b_saida = ttk.Button(sd, text="Escolher...", command=self.escolher_saida)
        self.b_saida.grid(row=0, column=2)
        sd.columnconfigure(1, weight=1)

        ttk.Label(sd, text="Paginas (opcional, ex.: 1-50):").grid(
            row=1, column=0, sticky="w", pady=(6, 0))
        self.var_paginas = tk.StringVar()
        ttk.Entry(sd, textvariable=self.var_paginas, width=14).grid(
            row=1, column=1, sticky="w", padx=8, pady=(6, 0))
        self._alternar_saida()

        # ---------- acao ----------
        ac = ttk.Frame(self)
        ac.pack(fill="x", pady=(10, 0))
        self.b_converter = ttk.Button(ac, text="CONVERTER", command=self.iniciar)
        self.b_converter.pack(side="left")
        self.b_cancelar = ttk.Button(ac, text="Cancelar", command=self.parar,
                                     state="disabled")
        self.b_cancelar.pack(side="left", padx=6)
        self.b_abrir = ttk.Button(ac, text="Abrir pasta de saida",
                                  command=self.abrir_saida, state="disabled")
        self.b_abrir.pack(side="left", padx=6)
        ttk.Button(ac, text="Diagnostico", command=self.mostrar_diagnostico
                   ).pack(side="right")

        self.pb_arquivo = ttk.Progressbar(self, mode="determinate")
        self.pb_arquivo.pack(fill="x", pady=(8, 0))
        self.var_status = tk.StringVar(value="Pronto.")
        ttk.Label(self, textvariable=self.var_status).pack(anchor="w", pady=(2, 0))

        # ---------- log ----------
        lg = ttk.LabelFrame(self, text=" Relatorio ", padding=4)
        lg.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(lg, height=9, wrap="word", font=("Consolas", 9))
        sb2 = ttk.Scrollbar(lg, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb2.set, state="disabled")
        self.log.pack(side="left", fill="both", expand=True)
        sb2.pack(side="left", fill="y")
        self.log.tag_configure("erro", foreground="#b00020")
        self.log.tag_configure("alerta", foreground="#a06000")
        self.log.tag_configure("ok", foreground="#0a6b28")
        self.log.tag_configure("titulo", font=("Consolas", 9, "bold"))

        if not ambiente.diagnostico()["tesseract"]:
            self._log("AVISO: Tesseract nao encontrado — paginas digitalizadas "
                      "ficarao vazias. Veja 'Diagnostico'.\n", "alerta")

    # -------------------------------------------------------------- estado
    def _perfil_atual(self):
        return obter(ORDEM[self.cb_perfil.current()])

    def _aplicar_perfil(self) -> None:
        """Mostra, nos controles, o que o perfil escolhido faz por padrao."""
        p = self._perfil_atual()
        desc = p.descricao
        if p.nome == "auto" and not self._ajuste_manual.get():
            desc += ("  As opcoes abaixo sao entao definidas POR ARQUIVO, pelo "
                     "perfil detectado — marque \"ajustar manualmente\" para "
                     "impor as suas.")
        self.lbl_desc.configure(text=desc)
        self.var_ocr.set(ROTULO_OCR[p.ocr])
        self.var_idioma.set(p.ocr_idioma)
        self.var_dpi.set(p.ocr_dpi)
        self.var_imagens.set(p.extrair_imagens)
        self.var_rodape.set(p.limpar_rodape)
        self.var_estrut.set(p.estruturado)
        self.var_preproc.set(p.ocr_preproc)

    def _alternar_ajuste(self) -> None:
        estado = "normal" if self._ajuste_manual.get() else "disabled"
        for w in self.campos:
            try:
                if isinstance(w, ttk.Combobox):
                    w.configure(state="readonly" if estado == "normal" else "disabled")
                else:
                    w.configure(state=estado)
            except tk.TclError:
                pass
        if not self._ajuste_manual.get():
            self._aplicar_perfil()

    def _alternar_saida(self) -> None:
        estado = "disabled" if self.var_mesma_pasta.get() else "normal"
        self.e_saida.configure(state=estado)
        self.b_saida.configure(state=estado)

    # ------------------------------------------------------------ arquivos
    def add_arquivos(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Selecione os PDFs",
            filetypes=[("Documentos PDF", "*.pdf"), ("Todos", "*.*")])
        self._incluir(paths)

    def add_pasta(self) -> None:
        d = filedialog.askdirectory(title="Selecione a pasta com os PDFs")
        if d:
            self._incluir([d])

    def _incluir(self, paths) -> None:
        if not paths:
            return
        novos = coletar_pdfs(paths, recursivo=self.var_recursivo.get())
        ja = {str(p).lower() for p in self.arquivos}
        add = [p for p in novos if str(p).lower() not in ja]
        if not add:
            return
        self.var_status.set("Inspecionando %d arquivo(s)..." % len(add))
        self.update_idletasks()
        for p in add:
            self.arquivos.append(p)
            try:
                import fitz

                d = fitz.open(str(p))
                npag = d.page_count
                d.close()
                tipo = PERFIS[detectar_perfil(p)].rotulo
            except Exception:
                npag, tipo = 0, "ilegivel"
            self.lista.insert("", "end", values=(p.name, npag, tipo, str(p.parent)))
        self.var_status.set("%d arquivo(s) na fila." % len(self.arquivos))

    def remover(self) -> None:
        for iid in self.lista.selection():
            idx = self.lista.index(iid)
            self.lista.delete(iid)
            if 0 <= idx < len(self.arquivos):
                self.arquivos.pop(idx)
        self.var_status.set("%d arquivo(s) na fila." % len(self.arquivos))

    def limpar(self) -> None:
        self.arquivos.clear()
        self.lista.delete(*self.lista.get_children())
        self.var_status.set("Pronto.")

    def escolher_saida(self) -> None:
        d = filedialog.askdirectory(title="Pasta de saida dos .md")
        if d:
            self.var_saida.set(d)

    def abrir_saida(self) -> None:
        alvo = self.ultimo_destino
        if not alvo or not Path(alvo).exists():
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(alvo))  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(alvo)])
            else:
                subprocess.Popen(["xdg-open", str(alvo)])
        except Exception as exc:
            messagebox.showerror(TITULO, "Nao consegui abrir a pasta:\n%s" % exc)

    def mostrar_diagnostico(self) -> None:
        messagebox.showinfo("Diagnostico do ambiente", ambiente.texto_diagnostico())

    # ------------------------------------------------------------ execucao
    def _log(self, txt: str, tag: str | None = None) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", txt, tag or "")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _intervalo(self):
        txt = self.var_paginas.get().strip()
        if not txt:
            return None
        try:
            partes = txt.replace(":", "-").split("-")
            ini = int(partes[0])
            fim = int(partes[1]) if len(partes) > 1 and partes[1].strip() else 0
            return (ini, fim)
        except (ValueError, IndexError):
            messagebox.showwarning(TITULO, "Intervalo invalido: %r.\n"
                                           "Use por exemplo 1-50." % txt)
            return "invalido"

    def iniciar(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        if not self.arquivos:
            messagebox.showinfo(TITULO, "Adicione ao menos um PDF.")
            return
        faixa = self._intervalo()
        if faixa == "invalido":
            return

        destino = None
        if not self.var_mesma_pasta.get():
            d = self.var_saida.get().strip()
            if not d:
                messagebox.showinfo(TITULO, "Escolha a pasta de saida.")
                return
            destino = d

        nome_perfil = ORDEM[self.cb_perfil.current()]
        sobrescritas = {}
        if self._ajuste_manual.get():
            sobrescritas = dict(
                ocr=OCR_POR_ROTULO.get(self.var_ocr.get(), "auto"),
                ocr_idioma=self.var_idioma.get().strip() or "por",
                ocr_dpi=int(self.var_dpi.get() or 300),
                ocr_preproc=self.var_preproc.get(),
                extrair_imagens=self.var_imagens.get(),
                estruturado=self.var_estrut.get(),
                limpar_rodape=self.var_rodape.get(),
            )

        self.cancelar.clear()
        self.b_converter.configure(state="disabled")
        self.b_cancelar.configure(state="normal")
        self.b_abrir.configure(state="disabled")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._log("%d arquivo(s) | perfil: %s\n\n"
                  % (len(self.arquivos), PERFIS[nome_perfil].rotulo), "titulo")

        args = (list(self.arquivos), destino, nome_perfil, sobrescritas, faixa)
        self.worker = threading.Thread(target=self._trabalhar, args=args, daemon=True)
        self.worker.start()

    def parar(self) -> None:
        self.cancelar.set()
        self.var_status.set("Cancelando ao fim da pagina atual...")

    def _trabalhar(self, arquivos, destino, nome_perfil, sobrescritas, faixa) -> None:
        put = self.fila.put
        total_arq = len(arquivos)
        resultados = []
        for i, pdf in enumerate(arquivos, start=1):
            if self.cancelar.is_set():
                break
            put(("arquivo", i, total_arq, pdf.name))

            def prog(feito, tot, rot, _i=i, _n=total_arq, _nm=pdf.name):
                put(("passo", feito, tot, "[%d/%d] %s — %s" % (_i, _n, _nm, rot)))

            r = converter(pdf, destino=destino, perfil=nome_perfil,
                          sobrescritas=sobrescritas, intervalo=faixa,
                          progresso=prog, cancelar=self.cancelar)
            resultados.append(r)
            put(("resultado", r))
        put(("fim", resultados))

    def _drenar_fila(self) -> None:
        try:
            while True:
                msg = self.fila.get_nowait()
                tipo = msg[0]
                if tipo == "arquivo":
                    _, i, n, nome = msg
                    self.var_status.set("[%d/%d] %s" % (i, n, nome))
                elif tipo == "passo":
                    _, feito, tot, rot = msg
                    self.pb_arquivo.configure(maximum=max(tot, 1), value=feito)
                    self.var_status.set(rot)
                elif tipo == "resultado":
                    self._mostrar_resultado(msg[1])
                elif tipo == "fim":
                    self._finalizar(msg[1])
        except queue.Empty:
            pass
        # So reagenda se a janela ainda existe: fechar o app com uma conversao
        # em curso deixaria este `after` disparando sobre widgets destruidos.
        if self.winfo_exists():
            self._tick = self.after(120, self._drenar_fila)

    def _ao_destruir(self, evento=None) -> None:
        if evento is not None and evento.widget is not self:
            return
        self.cancelar.set()          # nao deixa a thread trabalhando a toa
        if getattr(self, "_tick", None):
            try:
                self.after_cancel(self._tick)
            except tk.TclError:
                pass
            self._tick = None

    def _mostrar_resultado(self, r) -> None:
        if r.erro:
            self._log("ERRO  %s: %s\n" % (r.origem.name, r.erro), "erro")
            return
        if r.cancelado:
            self._log("CANCELADO  %s\n" % r.origem.name, "alerta")
            return

        detectado = (" [%s]" % PERFIS[r.perfil].rotulo) if r.perfil_detectado else ""
        self._log("%s%s\n" % (r.origem.name, detectado), "titulo")
        self._log("   %d pag | %d caracteres (media %.0f/pag) | %d pag por OCR"
                  " | %d imagem(ns) | %.1fs\n"
                  % (r.paginas, r.chars, r.media_chars, r.paginas_ocr,
                     r.imagens, r.duracao))
        if r.rodapes_removidos:
            self._log("   %d linha(s) de rodape do PJe removidas\n" % r.rodapes_removidos)
        if r.docs_pje:
            self._log("   %d documento(s) identificados nos autos\n" % len(r.docs_pje))
        if r.paginas_vazias:
            amostra = ", ".join(str(x) for x in r.paginas_vazias[:15])
            if len(r.paginas_vazias) > 15:
                amostra += " ..."
            self._log("   ATENCAO: %d pagina(s) sem texto (%s). Converta de novo com "
                      "OCR 'sempre' e DPI maior antes de citar.\n"
                      % (len(r.paginas_vazias), amostra), "alerta")
        if r.destino:
            self._log("   -> %s\n" % r.destino, "ok")
            self.ultimo_destino = Path(r.destino).parent
        self._log("\n")

    def _finalizar(self, resultados) -> None:
        self.b_converter.configure(state="normal")
        self.b_cancelar.configure(state="disabled")
        self.pb_arquivo.configure(value=0)
        if self.ultimo_destino:
            self.b_abrir.configure(state="normal")

        ok = [r for r in resultados if r.ok]
        erros = [r for r in resultados if r.erro]
        vazias = sum(len(r.paginas_vazias) for r in ok)
        chars = sum(r.chars for r in ok)

        self._log("=" * 62 + "\n", "titulo")
        self._log("%d convertido(s) | %d caractere(s) | %d erro(s)\n"
                  % (len(ok), chars, len(erros)),
                  "erro" if erros else "ok")
        if vazias:
            self._log("%d pagina(s) ficaram SEM TEXTO — a conversao esta incompleta "
                      "nessas paginas.\n" % vazias, "alerta")
        elif ok:
            self._log("Nenhuma pagina ficou sem texto.\n", "ok")
        self.var_status.set("Concluido: %d de %d arquivo(s)."
                            % (len(ok), len(resultados)))


def main() -> int:
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
