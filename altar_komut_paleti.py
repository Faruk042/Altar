# -*- coding: utf-8 -*-
"""
Altar Hızlı Komut Paleti (altar_komut_paleti.py) - Ctrl+K

VS Code veya Raycast benzeri, klavyeden Ctrl+K tuşuna basıldığında açılan
merkezi hızlı erişim penceresi. Kullanıcı tek kelime yazarak tüm Altar
araçlarına, sekmelerine, stüdyolara ve güvenlik modüllerine anında sıçrayabilir.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import customtkinter as ctk


class AltarKomutPaletiModal(ctk.CTkToplevel):
    """Hızlı komut arama ve klavye odaklı çalıştırma paleti."""

    def __init__(self, master: object, eylemler: Optional[List[Dict[str, Any]]] = None, **kwargs: Any) -> None:
        super().__init__(master)
        if eylemler is None:
            eylemler = kwargs.get("komutlar") or []
        self.eylemler = eylemler
        self.filtreli_eylemler = list(eylemler)
        self.secili_indeks = 0

        self.title("🔍 Altar Hızlı Komut Paleti (Ctrl+K)")
        self.geometry("620x420")
        self.minsize(500, 350)
        self.configure(fg_color="#0B0F19")
        self.resizable(False, False)

        # Pencereyi ortala
        try:
            self.update_idletasks()
            pw = master.winfo_width()
            ph = master.winfo_height()
            px = master.winfo_x()
            py = master.winfo_y()
            x = px + max(0, (pw - 620) // 2)
            y = py + max(0, (ph - 420) // 3)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._arayuz_kur()
        self.transient(master)
        self.grab_set()
        self.after(50, lambda: self.txt_arama.focus_set())

        # Tuş bağlantıları
        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Up>", self._yukari_hareket)
        self.bind("<Down>", self._asagi_hareket)
        self.bind("<Return>", lambda _: self._seciliyi_calistir())

    def _arayuz_kur(self) -> None:
        ust = ctk.CTkFrame(self, fg_color="#111827", corner_radius=10)
        ust.pack(side="top", fill="x", padx=12, pady=(12, 6))

        lbl_ikon = ctk.CTkLabel(ust, text="⚡", font=ctk.CTkFont(size=18))
        lbl_ikon.pack(side="left", padx=(10, 4))

        self.txt_arama = ctk.CTkEntry(
            ust, placeholder_text="Komut, araç veya sekme adı yazın (Örn: ide, ram, video, edr)...",
            height=38, font=ctk.CTkFont(size=13), border_width=0, fg_color="transparent"
        )
        self.txt_arama.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        self.txt_arama.bind("<KeyRelease>", self._arama_filtrele)

        lbl_esc = ctk.CTkLabel(ust, text="ESC = Kapat", font=ctk.CTkFont(size=10), text_color="#64748B")
        lbl_esc.pack(side="right", padx=10)

        # Liste çerçevesi
        self.scroll_liste = ctk.CTkScrollableFrame(self, fg_color="#070B14", corner_radius=8)
        self.scroll_liste.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 10))

        self._listeyi_ciz()

    def _arama_filtrele(self, event: Optional[object] = None) -> None:
        if event and getattr(event, "keysym", "") in ("Up", "Down", "Return", "Escape"):
            return
        sorgu = self.txt_arama.get().strip().lower()
        if sorgu:
            self.filtreli_eylemler = [
                e for e in self.eylemler
                if sorgu in e["baslik"].lower() or sorgu in e.get("aciklama", "").lower() or sorgu in e.get("kategori", "").lower()
            ]
        else:
            self.filtreli_eylemler = list(self.eylemler)

        self.secili_indeks = 0
        self._listeyi_ciz()

    def _listeyi_ciz(self) -> None:
        for w in self.scroll_liste.winfo_children():
            w.destroy()

        if not self.filtreli_eylemler:
            ctk.CTkLabel(
                self.scroll_liste, text="Eşleşen komut bulunamadı.", font=ctk.CTkFont(size=12), text_color="#64748B"
            ).pack(pady=20)
            return

        for idx, e in enumerate(self.filtreli_eylemler):
            secili_mi = (idx == self.secili_indeks)
            bg_clr = "#1E3A8A" if secili_mi else "#0F172A"

            satir = ctk.CTkFrame(self.scroll_liste, fg_color=bg_clr, corner_radius=6, height=36)
            satir.pack(fill="x", padx=4, pady=2)
            satir.pack_propagate(False)

            btn = ctk.CTkButton(
                satir,
                text=f"{e['ikon']}  {e['baslik']}",
                anchor="w",
                fg_color="transparent",
                hover_color="#2563EB" if secili_mi else "#1E293B",
                font=ctk.CTkFont(size=12, weight="bold" if secili_mi else "normal"),
                command=lambda i=idx: self._satir_tiklandi(i)
            )
            btn.pack(side="left", fill="both", expand=True, padx=6)

            if e.get("kategori"):
                lbl_kat = ctk.CTkLabel(
                    satir, text=e["kategori"], font=ctk.CTkFont(size=10), text_color="#94A3B8"
                )
                lbl_kat.pack(side="right", padx=10)

    def _yukari_hareket(self, event: object) -> str:
        if self.secili_indeks > 0:
            self.secili_indeks -= 1
            self._listeyi_ciz()
        return "break"

    def _asagi_hareket(self, event: object) -> str:
        if self.secili_indeks < len(self.filtreli_eylemler) - 1:
            self.secili_indeks += 1
            self._listeyi_ciz()
        return "break"

    def _satir_tiklandi(self, idx: int) -> None:
        self.secili_indeks = idx
        self._seciliyi_calistir()

    def _seciliyi_calistir(self) -> None:
        if 0 <= self.secili_indeks < len(self.filtreli_eylemler):
            eylem = self.filtreli_eylemler[self.secili_indeks]
            fonk = eylem.get("aksiyon")
            self.destroy()
            if callable(fonk):
                fonk()
