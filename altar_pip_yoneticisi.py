# -*- coding: utf-8 -*-
"""
Altar Görsel Pip Paket Yöneticisi (altar_pip_yoneticisi.py)

Kullanıcının terminale veya harici konsola çıkmasına gerek kalmadan
seçili Python ortamına (Örn: .venv veya Sistem Python 3.13) kütüphane
kurmasını, güncellemesini veya kaldırmasını sağlayan görsel arayüz modülü.
Tamamen izole ve güvenli `python -m pip` alt-süreçleriyle çalışır.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from tkinter import messagebox
from typing import Dict, List, Optional

import customtkinter as ctk


class AltarPipYoneticisiModal(ctk.CTkToplevel):
    """Görsel Pip Paket Yönetim Penceresi."""

    def __init__(self, master: object, python_exe: Optional[str] = None) -> None:
        super().__init__(master)
        self.python_exe = python_exe or sys.executable
        self.title(f"📦 Altar Pip Paket Yöneticisi — ({os.path.basename(self.python_exe)})")
        self.geometry("740x580")
        self.minsize(620, 480)
        self.configure(fg_color="#0B0F19")

        self.tum_paketler: List[Dict[str, str]] = []
        self.filtreli_paketler: List[Dict[str, str]] = []
        self.secili_paket: Optional[str] = None
        self._surec_calisiyor = False

        self._arayuz_kur()
        self.after(150, self.paketleri_listele)

        # Modal odaklanması
        self.transient(master)
        self.grab_set()

    def _arayuz_kur(self) -> None:
        # 1. Üst Bilgi Barı
        ust_cerceve = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        ust_cerceve.pack(side="top", fill="x", padx=12, pady=(10, 6))

        lbl_bilgi = ctk.CTkLabel(
            ust_cerceve,
            text=f"🐍 Aktif Python Ortamı: {self.python_exe}",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#00F5D4",
            anchor="w"
        )
        lbl_bilgi.pack(side="left", padx=10, pady=8, fill="x", expand=True)

        self.lbl_paket_sayisi = ctk.CTkLabel(
            ust_cerceve, text="Taranıyor...", font=ctk.CTkFont(size=11), text_color="#94A3B8"
        )
        self.lbl_paket_sayisi.pack(side="right", padx=10, pady=8)

        # 2. Hızlı Arama & Kurulum Bölümü
        islem_bar = ctk.CTkFrame(self, fg_color="transparent")
        islem_bar.pack(side="top", fill="x", padx=12, pady=(0, 6))

        self.txt_arama = ctk.CTkEntry(
            islem_bar, placeholder_text="🔍 Yüklü paketlerde ara...", width=200, height=32,
            font=ctk.CTkFont(size=12)
        )
        self.txt_arama.pack(side="left", padx=(0, 6))
        self.txt_arama.bind("<KeyRelease>", lambda _: self._arama_filtrele())

        self.txt_yeni_paket = ctk.CTkEntry(
            islem_bar, placeholder_text="Paket adı yazın (Örn: pandas, matplotlib, requests)...",
            height=32, font=ctk.CTkFont(size=12)
        )
        self.txt_yeni_paket.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.txt_yeni_paket.bind("<Return>", lambda _: self.paket_kur())

        self.btn_kur = ctk.CTkButton(
            islem_bar, text="⬇️ Kur (pip install)", width=135, height=32,
            fg_color="#047857", hover_color="#059669", font=ctk.CTkFont(size=12, weight="bold"),
            command=self.paket_kur
        )
        self.btn_kur.pack(side="right")

        # 3. Ana İçerik: Sol Paket Listesi | Sağ Terminal ve Butonlar
        govde = ctk.CTkFrame(self, fg_color="transparent")
        govde.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 10))
        govde.grid_columnconfigure(0, weight=5)
        govde.grid_columnconfigure(1, weight=6)
        govde.grid_rowconfigure(0, weight=1)

        # Sol Paket Listesi
        sol_kutu = ctk.CTkFrame(govde, fg_color="#111827", corner_radius=8)
        sol_kutu.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        sol_baslik = ctk.CTkFrame(sol_kutu, fg_color="transparent")
        sol_baslik.pack(fill="x", padx=8, pady=(6, 2))
        ctk.CTkLabel(
            sol_baslik, text="📦 Yüklü Kütüphaneler", font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#E2E8F0"
        ).pack(side="left")

        ctk.CTkButton(
            sol_baslik, text="🔄 Yenile", width=65, height=24, fg_color="#1F2937",
            hover_color="#374151", font=ctk.CTkFont(size=11), command=self.paketleri_listele
        ).pack(side="right")

        self.scroll_liste = ctk.CTkScrollableFrame(sol_kutu, fg_color="#070B14", corner_radius=6)
        self.scroll_liste.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # Sağ Panel: Canlı Log Terminali ve Seçili Paket İşlemleri
        sag_kutu = ctk.CTkFrame(govde, fg_color="#111827", corner_radius=8)
        sag_kutu.grid(row=0, column=1, sticky="nsew")

        sag_ust = ctk.CTkFrame(sag_kutu, fg_color="transparent")
        sag_ust.pack(fill="x", padx=8, pady=(6, 4))

        self.lbl_secili = ctk.CTkLabel(
            sag_ust, text="Seçili Paket: [Yok]", font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38BDF8"
        )
        self.lbl_secili.pack(side="left")

        self.btn_kaldir = ctk.CTkButton(
            sag_ust, text="🗑️ Kaldır", width=75, height=26, fg_color="#B91C1C",
            hover_color="#DC2626", font=ctk.CTkFont(size=11, weight="bold"),
            state="disabled", command=self.paket_kaldir
        )
        self.btn_kaldir.pack(side="right", padx=(4, 0))

        self.btn_guncelle = ctk.CTkButton(
            sag_ust, text="⬆️ Güncelle", width=85, height=26, fg_color="#1D4ED8",
            hover_color="#2563EB", font=ctk.CTkFont(size=11, weight="bold"),
            state="disabled", command=self.paket_guncelle
        )
        self.btn_guncelle.pack(side="right", padx=4)

        self.txt_log = ctk.CTkTextbox(
            sag_kutu, fg_color="#070B14", text_color="#A5D6FF",
            font=ctk.CTkFont(family="Consolas", size=11), wrap="word"
        )
        self.txt_log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.txt_log.insert("end", "Altar Görsel Pip Motoru Hazır.\n")

    def _log_yaz(self, metin: str) -> None:
        self.txt_log.insert("end", metin)
        self.txt_log.see("end")

    def paketleri_listele(self) -> None:
        self.lbl_paket_sayisi.configure(text="Taranıyor...")
        self._log_yaz("\n[BİLGİ] Yüklü paket listesi alınıyor...\n")

        def _arka_plan():
            try:
                sonuc = subprocess.run(
                    [self.python_exe, "-m", "pip", "list", "--format=json"],
                    capture_output=True, text=True, check=True, timeout=30
                )
                ham_veri = json.loads(sonuc.stdout)
                self.after(0, lambda: self._listeyi_doldur(ham_veri))
            except Exception as e:
                self.after(0, lambda: self._log_yaz(f"[HATA] Paket listesi alınamadı: {e}\n"))

        threading.Thread(target=_arka_plan, daemon=True).start()

    def _listeyi_doldur(self, paket_listesi: List[Dict[str, str]]) -> None:
        self.tum_paketler = sorted(paket_listesi, key=lambda x: x.get("name", "").lower())
        self.filtreli_paketler = list(self.tum_paketler)
        self.lbl_paket_sayisi.configure(text=f"Toplam: {len(self.tum_paketler)} paket")
        self._arama_filtrele()

    def _arama_filtrele(self) -> None:
        kelime = self.txt_arama.get().strip().lower()
        if kelime:
            self.filtreli_paketler = [p for p in self.tum_paketler if kelime in p.get("name", "").lower()]
        else:
            self.filtreli_paketler = list(self.tum_paketler)

        for widget in self.scroll_liste.winfo_children():
            widget.destroy()

        for p in self.filtreli_paketler:
            ad = p.get("name", "")
            surum = p.get("version", "")

            satir = ctk.CTkFrame(self.scroll_liste, fg_color="#0F172A", corner_radius=4, height=30)
            satir.pack(fill="x", padx=2, pady=2)
            satir.pack_propagate(False)

            btn = ctk.CTkButton(
                satir, text=f"{ad}  ({surum})", anchor="w", fg_color="transparent",
                hover_color="#1E293B", font=ctk.CTkFont(family="Consolas", size=11),
                command=lambda a=ad, s=surum: self._paket_sec(a, s)
            )
            btn.pack(side="left", fill="both", expand=True, padx=4)

    def _paket_sec(self, ad: str, surum: str) -> None:
        self.secili_paket = ad
        self.lbl_secili.configure(text=f"Seçili: {ad} ({surum})")
        self.btn_kaldir.configure(state="normal")
        self.btn_guncelle.configure(state="normal")

    def paket_kur(self) -> None:
        paket_adi = self.txt_yeni_paket.get().strip()
        if not paket_adi:
            return

        # Güvenlik Kontrolü: Komut/Bayrak Enjeksiyonu (Flag Injection / CWE-88) Koruması
        if paket_adi.startswith("-") or not re.match(r"^[A-Za-z0-9_.\-\[\]><=~! ]+$", paket_adi):
            messagebox.showerror(
                "Geçersiz Paket Adı",
                "Güvenlik Uyarısı: Paket adı tire (-) ile başlayamaz veya zararlı kabuk parametresi içeremez.\n"
                "Yalnızca standart Python kütüphane isimleri ve sürüm kuralları kabul edilir.",
                parent=self
            )
            return

        if self._surec_calisiyor:
            self._log_yaz("[UYARI] Devam eden bir pip işlemi var!\n")
            return

        self._surec_calistir([self.python_exe, "-m", "pip", "install", "--", paket_adi], f"'{paket_adi}' kuruluyor...")

    def paket_guncelle(self) -> None:
        if not self.secili_paket or self._surec_calisiyor:
            return
        self._surec_calistir(
            [self.python_exe, "-m", "pip", "install", "--upgrade", self.secili_paket],
            f"'{self.secili_paket}' güncelleniyor..."
        )

    def paket_kaldir(self) -> None:
        if not self.secili_paket or self._surec_calisiyor:
            return
        self._surec_calistir(
            [self.python_exe, "-m", "pip", "uninstall", "-y", self.secili_paket],
            f"'{self.secili_paket}' kaldırılıyor..."
        )

    def _surec_calistir(self, komut: List[str], baslik: str) -> None:
        self._surec_calisiyor = True
        self.btn_kur.configure(state="disabled")
        self.btn_kaldir.configure(state="disabled")
        self.btn_guncelle.configure(state="disabled")
        self._log_yaz(f"\n{'='*55}\n[İŞLEM BAŞLADI] {baslik}\n{'='*55}\n")

        def _calis():
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            try:
                proc = subprocess.Popen(
                    komut,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=creation_flags
                )
                for satir in iter(proc.stdout.readline, ""):
                    self.after(0, lambda s=satir: self._log_yaz(s))
                proc.stdout.close()
                proc.wait()
                self.after(0, lambda: self._log_yaz(f"[TAMAMLANDI] Çıkış Kodu: {proc.returncode}\n"))
            except Exception as e:
                self.after(0, lambda: self._log_yaz(f"[HATA]: {e}\n"))
            finally:
                self.after(0, self._surec_bitti)

        threading.Thread(target=_calis, daemon=True).start()

    def _surec_bitti(self) -> None:
        self._surec_calisiyor = False
        self.btn_kur.configure(state="normal")
        self.paketleri_listele()
