# -*- coding: utf-8 -*-
"""
Altar Canlı Ağ Bağlantı Radarı (altar_ag_radari.py)

Bilgisayarın aktif TCP/UDP bağlantılarını (yerel portlar, uzak IP adresleri,
bağlı süreç isimleri) tamamen SALT-OKUNUR şekilde listeler.
Ağa veya sisteme hiçbir paket göndermez, müdahale etmez (%100 güvenli).
"""

from __future__ import annotations

import os
from typing import Dict, List

import customtkinter as ctk

try:
    import psutil
    PSUTIL_VAR = True
except ImportError:
    PSUTIL_VAR = False


class AltarAgRadariModal(ctk.CTkToplevel):
    """Canlı aktif ağ bağlantılarını gösteren radar modalı."""

    def __init__(self, master: object) -> None:
        super().__init__(master)
        self.title("🌐 Altar Canlı Ağ Bağlantı Radarı (Salt-Okunur)")
        self.geometry("780x520")
        self.minsize(640, 420)
        self.configure(fg_color="#0B0F19")

        self._arayuz_kur()
        self.baglantilari_tara()

        self.transient(master)
        self.grab_set()

    def _arayuz_kur(self) -> None:
        ust = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        ust.pack(side="top", fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            ust, text="📡 Aktif Sistem Ağ Bağlantıları (TCP / UDP)",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#38BDF8"
        ).pack(side="left", padx=10, pady=8)

        ctk.CTkButton(
            ust, text="🔄 Yenile", width=80, height=26, fg_color="#1E3A8A",
            hover_color="#2563EB", font=ctk.CTkFont(size=11), command=self.baglantilari_tara
        ).pack(side="right", padx=10, pady=8)

        self.lbl_sayi = ctk.CTkLabel(ust, text="", font=ctk.CTkFont(size=11), text_color="#94A3B8")
        self.lbl_sayi.pack(side="right", padx=10)

        # Tablo Çerçevesi
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#070B14", corner_radius=8)
        self.scroll.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 10))

    def baglantilari_tara(self) -> None:
        for w in self.scroll.winfo_children():
            w.destroy()

        if not PSUTIL_VAR:
            ctk.CTkLabel(
                self.scroll, text="psutil kütüphanesi yüklü değil.", font=ctk.CTkFont(size=12), text_color="#EF4444"
            ).pack(pady=30)
            return

        try:
            baglantilar = psutil.net_connections(kind="inet")
        except Exception as exc:
            ctk.CTkLabel(
                self.scroll, text=f"Ağ bağlantıları taranamadı: {exc}", font=ctk.CTkFont(size=11), text_color="#EF4444"
            ).pack(pady=30)
            return

        aktif_liste = []
        for b in baglantilar:
            if b.status in ("ESTABLISHED", "LISTEN", "SYN_SENT", "TIME_WAIT"):
                pid = b.pid or 0
                proc_ad = "Bilinmiyor"
                if pid > 0:
                    try:
                        proc_ad = psutil.Process(pid).name()
                    except Exception:
                        pass

                yerel = f"{b.laddr.ip}:{b.laddr.port}" if b.laddr else "-"
                uzak = f"{b.raddr.ip}:{b.raddr.port}" if b.raddr else "Dinleniyor (*)"
                aktif_liste.append({
                    "proc": proc_ad,
                    "pid": pid,
                    "durum": b.status,
                    "yerel": yerel,
                    "uzak": uzak,
                    "tur": "TCP" if b.type == 1 else "UDP"
                })

        self.lbl_sayi.configure(text=f"Aktif Bağlantı: {len(aktif_liste)}")

        # Başlık Satırı
        baslik_kutusu = ctk.CTkFrame(self.scroll, fg_color="#1E293B", corner_radius=4, height=28)
        baslik_kutusu.pack(fill="x", padx=2, pady=(0, 4))
        baslik_kutusu.pack_propagate(False)

        ctk.CTkLabel(baslik_kutusu, text="Uygulama (PID)", font=ctk.CTkFont(size=11, weight="bold"), width=160, anchor="w").pack(side="left", padx=8)
        ctk.CTkLabel(baslik_kutusu, text="Protokol", font=ctk.CTkFont(size=11, weight="bold"), width=70, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(baslik_kutusu, text="Durum", font=ctk.CTkFont(size=11, weight="bold"), width=100, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(baslik_kutusu, text="Yerel Adres", font=ctk.CTkFont(size=11, weight="bold"), width=150, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(baslik_kutusu, text="Uzak Hedef", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=4)

        for item in aktif_liste[:60]:
            satir = ctk.CTkFrame(self.scroll, fg_color="#0F172A", corner_radius=4, height=26)
            satir.pack(fill="x", padx=2, pady=1)
            satir.pack_propagate(False)

            renk = "#10B981" if item["durum"] == "ESTABLISHED" else ("#38BDF8" if item["durum"] == "LISTEN" else "#94A3B8")

            ctk.CTkLabel(satir, text=f"{item['proc']} ({item['pid']})", font=ctk.CTkFont(family="Consolas", size=10), width=160, anchor="w").pack(side="left", padx=8)
            ctk.CTkLabel(satir, text=item["tur"], font=ctk.CTkFont(family="Consolas", size=10), width=70, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(satir, text=item["durum"], font=ctk.CTkFont(family="Consolas", size=10), text_color=renk, width=100, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(satir, text=item["yerel"], font=ctk.CTkFont(family="Consolas", size=10), width=150, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(satir, text=item["uzak"], font=ctk.CTkFont(family="Consolas", size=10), anchor="w").pack(side="left", fill="x", expand=True, padx=4)
