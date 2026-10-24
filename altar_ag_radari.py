# -*- coding: utf-8 -*-
"""
========================================================================================
ALTAR CANLI SİBER AĞ RADARI & TOPOLOJİ İSTASYONU (altar_ag_radari.py)
========================================================================================
* %100 Pasif ve Salt-Okunur (Read-Only) Ağ Keşfi:
  - Bilgisayara, yerel ağa, hiçbir sunucuya veya cihaza tek bir zararlı/müdahale paketi
    GÖNDERMEZ. Yalnızca işletim sisteminin yerel ARP tablosunu (arp -a) ve aktif
    soket bilgilerini (psutil.net_connections) güvenle okur.
* İnteraktif 2D Dairesel Siber Radar Haritası:
  - Merkezde: Altar Host (Bu Bilgisayar)
  - 1. Halka: Modem / Ağ Geçidi (Gateway)
  - 2. Halka: Yerel Ağ Cihazları (LAN: Telefon, PC, Yazıcı, TV)
  - 3. Halka: Aktif Dış İnternet Bağlantıları (WAN: Bulut, DNS, Web)
  - 360° Akıcı Dönen Radar Işını ve fosforlu iz animasyonu.
* Yabancı / Yeni Cihaz Tehdit Algılama:
  - Ağa yeni bir MAC/IP bağlandığında anında ekranda kırmızı uyarı halkası ve alarm rozeti.
* Tıklanabilir Cihaz Düğümleri & Teftiş Paneli:
  - Herhangi bir cihaza tıklandığında IP, MAC, OUI üretici tahmini ve Altar AI analiz köprüsü.
========================================================================================
"""

from __future__ import annotations

import os
import sys
import re
import math
import time
import json
import socket
import threading
import subprocess
from typing import Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

try:
    import psutil
    PSUTIL_VAR = True
except ImportError:
    PSUTIL_VAR = False

try:
    import winsound
    WINSOUND_VAR = True
except ImportError:
    WINSOUND_VAR = False


# Bilinen MAC Adresi (OUI) Üretici Eşleştirme Tablosu
OUI_TABLOSU = {
    "18-eb-d4": "TP-Link Technologies",
    "50-c7-bf": "TP-Link Technologies",
    "c0-25-67": "TP-Link Technologies",
    "00-1a-11": "Google Nest / Chromecast",
    "ac-de-48": "Apple Inc. (iPhone / Mac)",
    "00-17-f2": "Apple Inc.",
    "f0-18-98": "Apple Inc.",
    "3c-06-30": "Apple Inc.",
    "00-15-5d": "Microsoft Hyper-V",
    "08-00-27": "Oracle VirtualBox",
    "00-0c-29": "VMware Virtual Machine",
    "00-50-56": "VMware Virtual Machine",
    "dc-a6-32": "Raspberry Pi Foundation",
    "b8-27-eb": "Raspberry Pi Foundation",
    "e4-5f-01": "Raspberry Pi Foundation",
    "00-1e-67": "Intel Corporation",
    "a4-bb-6d": "Intel Corporation",
    "d8-07-b6": "Samsung Electronics",
    "78-4f-43": "Samsung Electronics",
    "f4-f5-e8": "Xiaomi Communications",
    "28-6c-07": "Xiaomi Communications",
    "00-e0-4c": "Realtek Semiconductor",
    "e0-d5-5e": "Huawei Technologies",
    "00-11-32": "Synology NAS",
}


def _oui_uretici_coz(mac: str) -> str:
    """MAC adresinin ilk 3 baytından üretici şirket tahmininde bulunur."""
    if not mac or len(mac) < 8:
        return "Bilinmeyen Üretici"
    prefix = mac[:8].lower().replace(":", "-")
    return OUI_TABLOSU.get(prefix, "Yerel Ağ Donanımı")


class AltarAgRadariModal(ctk.CTkToplevel):
    """Canlı Dairesel Ağ Topolojisi ve Siber Radar Haritası Penceresi."""

    def __init__(self, master: object) -> None:
        super().__init__(master)
        self.master = master
        self.title("📡 Altar Canlı Siber Ağ Radarı & Topoloji İstasyonu (%100 Pasif / Güvenli)")
        self.geometry("1060x680")
        self.minsize(920, 580)
        self.configure(fg_color="#060A13")

        # Radar Animasyon Değişkenleri
        self._aci: float = 0.0
        self._animasyon_aktif: bool = True
        self._sesli_alarm_aktif: bool = True
        self._otomatik_tarama_aktif: bool = True
        self._bilinen_macler: set = set()
        self._yeni_tespit_edilenler: List[dict] = []
        self._cihaz_dugumleri: Dict[str, dict] = {}
        self._secili_cihaz: Optional[dict] = None
        self._tarama_kilidi = threading.Lock()

        # Yerel Ağ Bilgileri
        self.yerel_ip: str = "127.0.0.1"
        self.ag_gecidi_ip: str = "192.168.1.1"
        self._yerel_bilgileri_al()

        self._arayuz_kur()
        self.transient(master)
        self.grab_set()

        # İlk taramayı ve animasyon döngüsünü başlat
        self.ag_taramasini_yurut(ilk_tarama=True)
        self.after(60, self._radar_animasyon_dongusu)
        self.after(3500, self._otomatik_tarama_dongusu)

        self.protocol("WM_DELETE_WINDOW", self._guvenli_kapat)

    def _yerel_bilgileri_al(self) -> None:
        """Kendi yerel IP adresini ve varsayılan ağ geçidini salt-okunur tespit eder."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.yerel_ip = s.getsockname()[0]
            s.close()
        except Exception:
            self.yerel_ip = "192.168.1.2"

        try:
            # IP'nin ilk 3 oktetinden varsayılan gateway tahmini
            parcalar = self.yerel_ip.split(".")
            if len(parcalar) == 4:
                self.ag_gecidi_ip = f"{parcalar[0]}.{parcalar[1]}.{parcalar[2]}.1"
        except Exception:
            self.ag_gecidi_ip = "192.168.1.1"

    def _arayuz_kur(self) -> None:
        # 1. ÜST BAŞLIK VE KONTROL BARI
        self.ust_bar = ctk.CTkFrame(self, fg_color="#0B132B", corner_radius=10, height=54)
        self.ust_bar.pack(side="top", fill="x", padx=14, pady=(12, 6))
        self.ust_bar.pack_propagate(False)

        sol_baslik = ctk.CTkFrame(self.ust_bar, fg_color="transparent")
        sol_baslik.pack(side="left", padx=12, fill="y")

        lbl_baslik = ctk.CTkLabel(
            sol_baslik, text="📡 ALTAŞ SİBER AĞ RADARI",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#38BDF8"
        )
        lbl_baslik.pack(anchor="w", pady=(6, 0))

        lbl_alt = ctk.CTkLabel(
            sol_baslik, text=f"Host IP: {self.yerel_ip}  |  Ağ Geçidi: {self.ag_gecidi_ip}  |  🛡️ Pasif / Salt-Okunur",
            font=ctk.CTkFont(size=11), text_color="#94A3B8"
        )
        lbl_alt.pack(anchor="w")

        # Butonlar
        sag_butonlar = ctk.CTkFrame(self.ust_bar, fg_color="transparent")
        sag_butonlar.pack(side="right", padx=12, fill="y")

        self.btn_tara = ctk.CTkButton(
            sag_butonlar, text="🔄 Şimdi Tara", width=95, height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284C7", hover_color="#0369A1",
            command=lambda: self.ag_taramasini_yurut(ilk_tarama=False)
        )
        self.btn_tara.pack(side="left", padx=4, pady=12)

        self.btn_radar_duraklat = ctk.CTkButton(
            sag_butonlar, text="⏸ Radarı Durdur", width=115, height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#334155", hover_color="#475569",
            command=self._radar_durum_degistir
        )
        self.btn_radar_duraklat.pack(side="left", padx=4, pady=12)

        self.btn_ses = ctk.CTkButton(
            sag_butonlar, text="🔊 Alarm: Açık", width=105, height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#059669", hover_color="#047857",
            command=self._ses_durum_degistir
        )
        self.btn_ses.pack(side="left", padx=4, pady=12)

        self.btn_disa_aktar = ctk.CTkButton(
            sag_butonlar, text="💾 Raporu Kaydet", width=115, height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#7C3AED", hover_color="#6D28D9",
            command=self._raporu_disa_aktar
        )
        self.btn_disa_aktar.pack(side="left", padx=4, pady=12)

        # 2. ANOMALİ / YENİ CİHAZ ALARM BARI
        self.alarm_bar = ctk.CTkFrame(self, fg_color="#450A0A", border_width=1, border_color="#DC2626", corner_radius=8, height=32)
        self.lbl_alarm = ctk.CTkLabel(
            self.alarm_bar, text="🛡️ Sistem ve yerel ağ güvenli: Beklenmeyen veya yetkisiz yeni cihaz bağlantısı tespit edilmedi.",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#FCA5A5"
        )
        self.lbl_alarm.pack(side="left", padx=12, pady=4)
        self.alarm_bar.pack(side="top", fill="x", padx=14, pady=(0, 6))

        # 3. ANA GÖVDE: RADAR (SOL) + TEFTİŞ PANELİ (SAĞ)
        ana_bolum = ctk.CTkFrame(self, fg_color="transparent")
        ana_bolum.pack(side="top", fill="both", expand=True, padx=14, pady=(0, 10))

        # SOL: TABVIEW (Sekme 1: Radar Haritası, Sekme 2: Ayrıntılı Soket Tablosu)
        self.tabview = ctk.CTkTabview(ana_bolum, fg_color="#0B132B")
        self.tabview.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.tab_radar = self.tabview.add("🌐 Canlı Siber Radar Haritası")
        self.tab_soketler = self.tabview.add("📋 Detaylı Bağlantı & Soket Tablosu")

        # RADAR SEKMESİ İÇERİĞİ (Tkinter Canvas)
        self._radar_arayuzunu_olustur(self.tab_radar)

        # SOKET TABLOSU SEKMESİ İÇERİĞİ
        self._soket_tablosu_arayuzunu_olustur(self.tab_soketler)

        # SAĞ: CİHAZ & TEHDİT TEFTİŞ PANELİ (INSPECTOR)
        self._teftis_panelini_olustur(ana_bolum)

    def _radar_arayuzunu_olustur(self, parent: ctk.CTkFrame) -> None:
        radar_kapsayici = ctk.CTkFrame(parent, fg_color="#050811", corner_radius=8)
        radar_kapsayici.pack(fill="both", expand=True, padx=4, pady=4)

        self.radar_canvas = tk.Canvas(
            radar_kapsayici, bg="#050811", highlightthickness=0, cursor="crosshair"
        )
        self.radar_canvas.pack(fill="both", expand=True)
        self.radar_canvas.bind("<Button-1>", self._radar_tiklandi)
        self.radar_canvas.bind("<Configure>", lambda _: self._canvas_yeniden_ciz())

        # Alt Gösterge / Açıklama Şeridi
        lejant_bar = ctk.CTkFrame(parent, fg_color="#070D1C", height=26, corner_radius=4)
        lejant_bar.pack(side="bottom", fill="x", padx=4, pady=(4, 0))

        ogeler = [
            ("💻", "#38BDF8", "Altar Host (Merkez)"),
            ("🌐", "#F59E0B", "Ağ Geçidi / Modem"),
            ("🟢", "#10B981", "Yerel Cihaz (LAN)"),
            ("☁️", "#A855F7", "Aktif Dış Ağ (WAN)"),
            ("🔴", "#EF4444", "Yeni / Şüpheli"),
        ]
        for ikon, renk, metin in ogeler:
            f = ctk.CTkFrame(lejant_bar, fg_color="transparent")
            f.pack(side="left", padx=10, pady=2)
            ctk.CTkLabel(f, text=ikon, font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(f, text=metin, font=ctk.CTkFont(size=10, weight="bold"), text_color=renk).pack(side="left")

    def _teftis_panelini_olustur(self, parent: ctk.CTkFrame) -> None:
        self.teftis_frame = ctk.CTkFrame(parent, fg_color="#0F172A", width=310, corner_radius=10)
        self.teftis_frame.pack(side="right", fill="y", padx=(0, 0))
        self.teftis_frame.pack_propagate(False)

        ctk.CTkLabel(
            self.teftis_frame, text="🔍 CİHAZ & TEHDİT TEFTİŞİ",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#38BDF8"
        ).pack(anchor="w", padx=14, pady=(14, 8))

        # Cihaz Kartı
        self.kart_kapsayici = ctk.CTkFrame(self.teftis_frame, fg_color="#1E293B", corner_radius=8)
        self.kart_kapsayici.pack(fill="x", padx=12, pady=4)

        self.lbl_kart_ikon = ctk.CTkLabel(self.kart_kapsayici, text="📡", font=ctk.CTkFont(size=28))
        self.lbl_kart_ikon.pack(pady=(12, 2))

        self.lbl_kart_ad = ctk.CTkLabel(
            self.kart_kapsayici, text="Bir Cihaz Seçin",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC"
        )
        self.lbl_kart_ad.pack()

        self.lbl_kart_durum = ctk.CTkLabel(
            self.kart_kapsayici, text="Radar üzerinden bir noktaya tıklayın",
            font=ctk.CTkFont(size=11), text_color="#94A3B8"
        )
        self.lbl_kart_durum.pack(pady=(0, 10))

        # Detaylar Listesi
        self.detay_kapsayici = ctk.CTkScrollableFrame(self.teftis_frame, fg_color="transparent", height=240)
        self.detay_kapsayici.pack(fill="both", expand=True, padx=8, pady=8)

        self.lbl_detay_ip = self._detay_satiri_ekle(self.detay_kapsayici, "IP Adresi:", "-")
        self.lbl_detay_mac = self._detay_satiri_ekle(self.detay_kapsayici, "MAC Adresi:", "-")
        self.lbl_detay_uretici = self._detay_satiri_ekle(self.detay_kapsayici, "Üretici (OUI):", "-")
        self.lbl_detay_tip = self._detay_satiri_ekle(self.detay_kapsayici, "Cihaz Türü:", "-")
        self.lbl_detay_surec = self._detay_satiri_ekle(self.detay_kapsayici, "İlgili Süreç (PID):", "-")
        self.lbl_detay_zaman = self._detay_satiri_ekle(self.detay_kapsayici, "İlk Tespit:", "-")

        # Aksiyon Butonları
        self.btn_ai_analiz = ctk.CTkButton(
            self.teftis_frame, text="🤖 Altar AI ile Güvenlik Analizi Yap",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#059669", hover_color="#047857", height=32,
            command=self._secili_cihazi_ai_ile_analiz_et
        )
        self.btn_ai_analiz.pack(fill="x", padx=12, pady=(4, 6))

        self.btn_port_tara = ctk.CTkButton(
            self.teftis_frame, text="🔍 Portlarını İncele",
            font=ctk.CTkFont(size=11),
            fg_color="#1E3A8A", hover_color="#2563EB", height=28,
            command=self._secili_cihazi_port_taramaya_gonder
        )
        self.btn_port_tara.pack(fill="x", padx=12, pady=(0, 12))

    def _detay_satiri_ekle(self, parent, etiket: str, varsayilan: str):
        satir = ctk.CTkFrame(parent, fg_color="transparent")
        satir.pack(fill="x", pady=2)
        ctk.CTkLabel(satir, text=etiket, font=ctk.CTkFont(size=10, weight="bold"), text_color="#94A3B8", width=105, anchor="w").pack(side="left")
        deger = ctk.CTkLabel(satir, text=varsayilan, font=ctk.CTkFont(family="Consolas", size=10), text_color="#E2E8F0", anchor="w")
        deger.pack(side="left", fill="x", expand=True)
        return deger

    def _soket_tablosu_arayuzunu_olustur(self, parent: ctk.CTkFrame) -> None:
        ust_filtre = ctk.CTkFrame(parent, fg_color="transparent")
        ust_filtre.pack(fill="x", padx=8, pady=6)

        ctk.CTkLabel(ust_filtre, text="Filtrele:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(side="left", padx=(0, 6))
        self.txt_filtre = ctk.CTkEntry(ust_filtre, placeholder_text="IP, Port veya Uygulama adı...", width=260, height=26)
        self.txt_filtre.pack(side="left", padx=(0, 8))
        self.txt_filtre.bind("<KeyRelease>", lambda _: self._soket_tablosunu_guncelle())

        self.lbl_soket_sayisi = ctk.CTkLabel(ust_filtre, text="", font=ctk.CTkFont(size=11), text_color="#38BDF8")
        self.lbl_soket_sayisi.pack(side="right", padx=8)

        self.scroll_soket = ctk.CTkScrollableFrame(parent, fg_color="#070B14", corner_radius=8)
        self.scroll_soket.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # =========================================================================
    # PASİF VE SALT-OKUNUR AĞ KEŞFİ (ARP TABLOSU + PSUTIL SOKETLERİ)
    # =========================================================================
    def ag_taramasini_yurut(self, ilk_tarama: bool = False) -> None:
        """İş parçacığında tamamen salt-okunur olarak yerel ARP önbelleğini ve soketleri okur."""
        threading.Thread(target=self._arka_plan_tarama, args=(ilk_tarama,), daemon=True).start()

    def _arka_plan_tarama(self, ilk_tarama: bool) -> None:
        with self._tarama_kilidi:
            cihazlar: List[dict] = []
            yeni_tespitler: List[dict] = []

            # 1. Altar Host (Merkez Düğüm)
            cihazlar.append({
                "id": "host",
                "ip": self.yerel_ip,
                "mac": "00-00-00-00-00-00",
                "uretici": "Altar Ana İstasyonu",
                "tur": "Host",
                "halka": 0,
                "yeni": False,
                "durum": "Yerel Çekirdek"
            })

            # 2. Windows Yerel ARP Tablosunu Ayrıştır (Pasif)
            try:
                out = subprocess.check_output(["arp", "-a"], text=True, errors="ignore")
                for line in out.splitlines():
                    m = re.search(r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([0-9a-fA-F\-]{17})\s+(\w+)", line)
                    if m:
                        ip, mac, tip = m.groups()
                        mac = mac.lower().replace(":", "-")
                        # Multicast ve broadcast adreslerini filtrele
                        if ip.startswith("224.") or ip.startswith("239.") or ip.endswith(".255") or ip == "255.255.255.255":
                            continue
                        if ip == self.yerel_ip:
                            continue

                        is_gateway = (ip == self.ag_gecidi_ip or ip.endswith(".1"))
                        halka = 1 if is_gateway else 2
                        cihaz_turu = "Ağ Geçidi / Modem" if is_gateway else "Yerel İstemci (LAN)"
                        uretici = _oui_uretici_coz(mac)

                        is_new = False
                        if not ilk_tarama and mac not in self._bilinen_macler and not is_gateway:
                            is_new = True
                            yeni_tespitler.append({"ip": ip, "mac": mac, "uretici": uretici})

                        self._bilinen_macler.add(mac)

                        cihazlar.append({
                            "id": f"lan_{ip}",
                            "ip": ip,
                            "mac": mac,
                            "uretici": uretici,
                            "tur": cihaz_turu,
                            "halka": halka,
                            "yeni": is_new,
                            "durum": "Aktif / Dinamik" if "dyn" in tip.lower() else "Statik"
                        })
            except Exception:
                pass

            # 3. Aktif Dış Ağ (WAN) Bağlantılarını Oku (psutil)
            if PSUTIL_VAR:
                try:
                    baglantilar = psutil.net_connections(kind="inet")
                    gorulen_wan = set()
                    for b in baglantilar:
                        if b.status == "ESTABLISHED" and b.raddr:
                            rip = b.raddr.ip
                            rport = b.raddr.port
                            # Yerel IP aralıklarını atla
                            if rip.startswith("127.") or rip.startswith("192.168.") or rip.startswith("10."):
                                continue
                            if rip in gorulen_wan or len(gorulen_wan) >= 12:
                                continue
                            gorulen_wan.add(rip)

                            proc_ad = "Bilinmiyor"
                            if b.pid:
                                try:
                                    proc_ad = psutil.Process(b.pid).name()
                                except Exception:
                                    pass

                            cihazlar.append({
                                "id": f"wan_{rip}",
                                "ip": rip,
                                "mac": "-",
                                "uretici": f"Uzak Sunucu (Port {rport})",
                                "tur": f"Dış Ağ: {proc_ad}",
                                "halka": 3,
                                "yeni": False,
                                "durum": f"ESTABLISHED ({proc_ad})"
                            })
                except Exception:
                    pass

            self.after(0, lambda: self._taramayi_uygula(cihazlar, yeni_tespitler))

    def _taramayi_uygula(self, cihazlar: List[dict], yeni_tespitler: List[dict]) -> None:
        """Ağ taraması sonuçlarını arayüze ve radara işler."""
        self._cihaz_dugumleri.clear()
        for c in cihazlar:
            self._cihaz_dugumleri[c["id"]] = c

        if yeni_tespitler:
            ilk_yeni = yeni_tespitler[0]
            self.alarm_bar.configure(fg_color="#7F1D1D", border_color="#EF4444")
            self.lbl_alarm.configure(
                text=f"⚠️ YENİ CİHAZ TESPİT EDİLDİ: {ilk_yeni['ip']} (MAC: {ilk_yeni['mac']} - {ilk_yeni['uretici']}) — Radarda kırmızı halka ile işaretlendi!",
                text_color="#FEE2E2"
            )
            if self._sesli_alarm_aktif and WINSOUND_VAR:
                try:
                    winsound.Beep(900, 200)
                except Exception:
                    pass
        else:
            self.alarm_bar.configure(fg_color="#0F1F17", border_color="#059669")
            toplam_lan = sum(1 for c in cihazlar if c["halka"] in (1, 2))
            toplam_wan = sum(1 for c in cihazlar if c["halka"] == 3)
            self.lbl_alarm.configure(
                text=f"🛡️ Yerel ağ güvenli: Toplam {toplam_lan} yerel cihaz ve {toplam_wan} aktif dış bağlantı izleniyor.",
                text_color="#A7F3D0"
            )

        self._soket_tablosunu_guncelle()
        self._canvas_yeniden_ciz()

    def _otomatik_tarama_dongusu(self) -> None:
        """Her 4 saniyede bir arka planda pasif tarama yapar."""
        if self._animasyon_aktif and self._otomatik_tarama_aktif:
            self.ag_taramasini_yurut(ilk_tarama=False)
        if self._animasyon_aktif:
            self.after(4000, self._otomatik_tarama_dongusu)

    # =========================================================================
    # DİNAMİK SİBER RADAR VE ÇEMBERSEL ÇİZİM MOTORU
    # =========================================================================
    def _canvas_yeniden_ciz(self) -> None:
        if not hasattr(self, "radar_canvas") or not self.radar_canvas.winfo_exists():
            return

        w = self.radar_canvas.winfo_width()
        h = self.radar_canvas.winfo_height()
        if w < 100 or h < 100:
            return

        self.radar_canvas.delete("all")
        cx, cy = w // 2, h // 2
        max_r = min(w, h) // 2 - 30
        if max_r < 50:
            return

        # 1. Arka Plan Izgarası ve Radyal Işınlar
        for aci_deg in range(0, 360, 45):
            rad = math.radians(aci_deg)
            x2 = cx + max_r * math.cos(rad)
            y2 = cy + max_r * math.sin(rad)
            self.radar_canvas.create_line(cx, cy, x2, y2, fill="#0F172A", width=1, dash=(2, 4))

        # 2. Üç Eşmerkezli Radar Halkası
        halka_oranlari = [0.35, 0.65, 0.95]
        halka_isimleri = ["1. Ağ Geçidi (Gateway)", "2. Yerel Ağ (LAN)", "3. Dış Bağlantılar (WAN)"]
        for oran, isim in zip(halka_oranlari, halka_isimleri):
            r = max_r * oran
            self.radar_canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline="#1E293B", width=1
            )
            self.radar_canvas.create_text(
                cx + 6, cy - r + 8, text=isim,
                fill="#334155", font=("Consolas", 8, "bold"), anchor="w"
            )

        # 3. Dönen Radar Işını (Sweep Beam) ve Fosfor İzi
        sweep_rad = math.radians(self._aci)
        for i in range(1, 4):
            trail_rad = math.radians(self._aci - i * 3)
            tx = cx + max_r * math.cos(trail_rad)
            ty = cy + max_r * math.sin(trail_rad)
            renk = "#0A2540" if i == 3 else ("#0D3D59" if i == 2 else "#0E5A6F")
            self.radar_canvas.create_line(cx, cy, tx, ty, fill=renk, width=1)

        # Ana Parlayan Yeşil Işın
        sx = cx + max_r * math.cos(sweep_rad)
        sy = cy + max_r * math.sin(sweep_rad)
        self.radar_canvas.create_line(cx, cy, sx, sy, fill="#00FFA3", width=2)

        # 4. Cihaz Düğümlerinin Koordinatlarını Hesapla ve Çiz
        lan_cihazlari = [c for c in self._cihaz_dugumleri.values() if c["halka"] == 2]
        wan_cihazlari = [c for c in self._cihaz_dugumleri.values() if c["halka"] == 3]

        for c in self._cihaz_dugumleri.values():
            halka = c["halka"]
            if halka == 0:
                # Merkez: Altar Host
                nx, ny = cx, cy
            elif halka == 1:
                # Gateway / Modem
                r = max_r * 0.35
                nx = cx + r * math.cos(math.radians(-90))
                ny = cy + r * math.sin(math.radians(-90))
            elif halka == 2:
                # LAN Cihazları dairesel dağıtılır
                idx = lan_cihazlari.index(c) if c in lan_cihazlari else 0
                bolum = 360 / max(1, len(lan_cihazlari))
                aci = math.radians(idx * bolum)
                r = max_r * 0.65
                nx = cx + r * math.cos(aci)
                ny = cy + r * math.sin(aci)
            else:
                # WAN Bağlantıları en dış halkaya dağıtılır
                idx = wan_cihazlari.index(c) if c in wan_cihazlari else 0
                bolum = 360 / max(1, len(wan_cihazlari))
                aci = math.radians(idx * bolum + 25)
                r = max_r * 0.95
                nx = cx + r * math.cos(aci)
                ny = cy + r * math.sin(aci)

            c["canvas_x"] = nx
            c["canvas_y"] = ny

            # Düğüm Çizimi
            node_r = 10 if halka == 0 else 7
            renk = "#38BDF8" if halka == 0 else ("#F59E0B" if halka == 1 else ("#10B981" if halka == 2 else "#A855F7"))
            if c.get("yeni"):
                renk = "#EF4444"

            # Seçili cihaz halkası
            if self._secili_cihaz and self._secili_cihaz.get("id") == c["id"]:
                self.radar_canvas.create_oval(
                    nx - 14, ny - 14, nx + 14, ny + 14,
                    outline="#38BDF8", width=2, dash=(2, 2)
                )

            # Yeni tespit edilmişse kırmızı puls halkası
            if c.get("yeni"):
                self.radar_canvas.create_oval(
                    nx - 13, ny - 13, nx + 13, ny + 13,
                    outline="#EF4444", width=2
                )

            self.radar_canvas.create_oval(
                nx - node_r, ny - node_r, nx + node_r, ny + node_r,
                fill=renk, outline="#FFFFFF", width=1, tags=(c["id"], "dugum")
            )

            # Etiket
            etiket = c["ip"] if halka != 0 else "Altar Host"
            self.radar_canvas.create_text(
                nx, ny + node_r + 8, text=etiket,
                fill="#CBD5E1", font=("Consolas", 8), tags=(c["id"], "etiket")
            )

    def _radar_animasyon_dongusu(self) -> None:
        """360 derece dönen radar tarama ışınını akıcı şekilde yürütür."""
        if self._animasyon_aktif:
            self._aci = (self._aci + 2.5) % 360
            self._canvas_yeniden_ciz()
            self.after(35, self._radar_animasyon_dongusu)

    def _radar_tiklandi(self, event) -> None:
        """Kullanıcı canvas üzerinde bir cihaza tıkladığında onu seçer ve teftiş kartını doldurur."""
        tik_x, tik_y = event.x, event.y
        en_yakin = None
        min_mesafe = 22.0

        for c in self._cihaz_dugumleri.values():
            nx = c.get("canvas_x", -100)
            ny = c.get("canvas_y", -100)
            d = math.hypot(tik_x - nx, tik_y - ny)
            if d < min_mesafe:
                min_mesafe = d
                en_yakin = c

        if en_yakin:
            self._cihazi_sec(en_yakin)

    def _cihazi_sec(self, cihaz: dict) -> None:
        self._secili_cihaz = cihaz
        self._canvas_yeniden_ciz()

        ikon = "💻" if cihaz["halka"] == 0 else ("🌐" if cihaz["halka"] == 1 else ("📱" if cihaz["halka"] == 2 else "☁️"))
        if cihaz.get("yeni"):
            ikon = "⚠️"

        self.lbl_kart_ikon.configure(text=ikon)
        self.lbl_kart_ad.configure(text=f"{cihaz['ip']}")
        durum_txt = "🔴 Şüpheli / Yeni Algılandı" if cihaz.get("yeni") else f"🟢 {cihaz.get('durum', 'Güvenli')}"
        self.lbl_kart_durum.configure(text=durum_txt)

        self.lbl_detay_ip.configure(text=cihaz.get("ip", "-"))
        self.lbl_detay_mac.configure(text=cihaz.get("mac", "-").upper())
        self.lbl_detay_uretici.configure(text=cihaz.get("uretici", "-"))
        self.lbl_detay_tip.configure(text=cihaz.get("tur", "-"))
        self.lbl_detay_surec.configure(text=cihaz.get("durum", "-"))
        self.lbl_detay_zaman.configure(text=time.strftime("%H:%M:%S"))

    # =========================================================================
    # SOKET TABLOSU
    # =========================================================================
    def _soket_tablosunu_guncelle(self) -> None:
        for w in self.scroll_soket.winfo_children():
            w.destroy()

        if not PSUTIL_VAR:
            ctk.CTkLabel(self.scroll_soket, text="psutil kütüphanesi aktif değil.", text_color="#EF4444").pack(pady=20)
            return

        try:
            baglantilar = psutil.net_connections(kind="inet")
        except Exception as e:
            ctk.CTkLabel(self.scroll_soket, text=f"Bağlantılar taranamadı: {e}", text_color="#EF4444").pack(pady=20)
            return

        filtre = self.txt_filtre.get().strip().lower() if hasattr(self, "txt_filtre") else ""

        # Başlık
        baslik = ctk.CTkFrame(self.scroll_soket, fg_color="#1E293B", corner_radius=4, height=26)
        baslik.pack(fill="x", padx=2, pady=(0, 4))
        baslik.pack_propagate(False)

        ctk.CTkLabel(baslik, text="Uygulama (PID)", font=ctk.CTkFont(size=10, weight="bold"), width=160, anchor="w").pack(side="left", padx=8)
        ctk.CTkLabel(baslik, text="Protokol", font=ctk.CTkFont(size=10, weight="bold"), width=70, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(baslik, text="Durum", font=ctk.CTkFont(size=10, weight="bold"), width=95, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(baslik, text="Yerel Adres", font=ctk.CTkFont(size=10, weight="bold"), width=140, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(baslik, text="Uzak Hedef", font=ctk.CTkFont(size=10, weight="bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=4)

        sayac = 0
        for b in baglantilar:
            if b.status in ("ESTABLISHED", "LISTEN", "TIME_WAIT", "SYN_SENT"):
                pid = b.pid or 0
                proc_ad = "Bilinmiyor"
                if pid > 0:
                    try:
                        proc_ad = psutil.Process(pid).name()
                    except Exception:
                        pass

                yerel = f"{b.laddr.ip}:{b.laddr.port}" if b.laddr else "-"
                uzak = f"{b.raddr.ip}:{b.raddr.port}" if b.raddr else "Dinleniyor (*)"
                tur = "TCP" if b.type == 1 else "UDP"

                tum_metin = f"{proc_ad} {pid} {yerel} {uzak} {b.status}".lower()
                if filtre and filtre not in tum_metin:
                    continue

                sayac += 1
                satir = ctk.CTkFrame(self.scroll_soket, fg_color="#0F172A", corner_radius=4, height=24)
                satir.pack(fill="x", padx=2, pady=1)
                satir.pack_propagate(False)

                renk = "#10B981" if b.status == "ESTABLISHED" else ("#38BDF8" if b.status == "LISTEN" else "#94A3B8")

                ctk.CTkLabel(satir, text=f"{proc_ad} ({pid})", font=ctk.CTkFont(family="Consolas", size=9), width=160, anchor="w").pack(side="left", padx=8)
                ctk.CTkLabel(satir, text=tur, font=ctk.CTkFont(family="Consolas", size=9), width=70, anchor="w").pack(side="left", padx=4)
                ctk.CTkLabel(satir, text=b.status, font=ctk.CTkFont(family="Consolas", size=9), text_color=renk, width=95, anchor="w").pack(side="left", padx=4)
                ctk.CTkLabel(satir, text=yerel, font=ctk.CTkFont(family="Consolas", size=9), width=140, anchor="w").pack(side="left", padx=4)
                ctk.CTkLabel(satir, text=uzak, font=ctk.CTkFont(family="Consolas", size=9), anchor="w").pack(side="left", fill="x", expand=True, padx=4)

                if sayac >= 80:
                    break

        if hasattr(self, "lbl_soket_sayisi"):
            self.lbl_soket_sayisi.configure(text=f"Listelenen Soket: {sayac}")

    # =========================================================================
    # KONTROL VE ENTEGRASYON METOTLARI
    # =========================================================================
    def _radar_durum_degistir(self) -> None:
        self._otomatik_tarama_aktif = not self._otomatik_tarama_aktif
        if self._otomatik_tarama_aktif:
            self.btn_radar_duraklat.configure(text="⏸ Radarı Durdur", fg_color="#334155")
        else:
            self.btn_radar_duraklat.configure(text="▶ Radarı Başlat", fg_color="#0284C7")

    def _ses_durum_degistir(self) -> None:
        self._sesli_alarm_aktif = not self._sesli_alarm_aktif
        if self._sesli_alarm_aktif:
            self.btn_ses.configure(text="🔊 Alarm: Açık", fg_color="#059669")
        else:
            self.btn_ses.configure(text="🔇 Alarm: Kapalı", fg_color="#374151")

    def _secili_cihazi_ai_ile_analiz_et(self) -> None:
        if not self._secili_cihaz:
            messagebox.showinfo("Bilgi", "Lütfen önce radardan analiz etmek istediğiniz bir cihaza tıklayın.", parent=self)
            return

        ip = self._secili_cihaz.get("ip", "")
        mac = self._secili_cihaz.get("mac", "")
        uretici = self._secili_cihaz.get("uretici", "")
        tur = self._secili_cihaz.get("tur", "")

        komut = (
            f"Altar Siber Ağ Radarı Güvenlik Raporu:\n"
            f"- Hedef IP: {ip}\n"
            f"- MAC Adresi: {mac}\n"
            f"- Donanım / Üretici: {uretici}\n"
            f"- Tespit Türü: {tur}\n\n"
            f"Bu cihazın yerel ağ veya dış bağlantı güvenliği açısından risklerini, açık port potansiyelini "
            f"ve olası siber zafiyetlerini Blue-Teaming prensipleriyle detaylıca analiz et."
        )

        try:
            if hasattr(self.master, "user_input") and hasattr(self.master, "send_command"):
                self.master.user_input.delete("1.0", "end")
                self.master.user_input.insert("1.0", komut)
                if hasattr(self.master, "tabview"):
                    self.master.tabview.set("💬 Sohbet")
                self.destroy()
                self.master.send_command()
                return
        except Exception:
            pass

        messagebox.showinfo("AI Analiz İsteği", f"Hedef analiz için Altar'a iletildi:\n{ip} ({uretici})", parent=self)

    def _secili_cihazi_port_taramaya_gonder(self) -> None:
        if not self._secili_cihaz:
            messagebox.showinfo("Bilgi", "Lütfen önce radardan bir cihaz seçin.", parent=self)
            return

        ip = self._secili_cihaz.get("ip", "")
        try:
            # Altar üzerindeki port tarayıcısını tetikle
            if hasattr(self.master, "tabview"):
                self.master.tabview.set("🛡️ Güvenlik")
            if hasattr(self.master, "port_scanner_hedef_ata"):
                self.master.port_scanner_hedef_ata(ip)
            self.destroy()
        except Exception:
            messagebox.showinfo("Hedef Seçildi", f"Seçilen IP: {ip} - Güvenlik sekmesinden taranabilir.", parent=self)

    def _raporu_disa_aktar(self) -> None:
        try:
            yol = filedialog.asksaveasfilename(
                title="Ağ Radarı Raporunu Kaydet",
                defaultextension=".json",
                filetypes=[("JSON Dosyası", "*.json"), ("Metin Dosyası", "*.txt")],
                parent=self
            )
            if not yol:
                return

            veriler = {
                "rapor_zamani": time.strftime("%Y-%m-%d %H:%M:%S"),
                "host_ip": self.yerel_ip,
                "ag_gecidi": self.ag_gecidi_ip,
                "tespit_edilen_cihazlar": list(self._cihaz_dugumleri.values())
            }

            if yol.endswith(".json"):
                with open(yol, "w", encoding="utf-8") as f:
                    json.dump(veriler, f, indent=4, ensure_ascii=False)
            else:
                with open(yol, "w", encoding="utf-8") as f:
                    f.write("=== ALTAŞ SİBER AĞ RADARI RAPORU ===\n")
                    f.write(f"Zaman: {veriler['rapor_zamani']}\n")
                    f.write(f"Host: {veriler['host_ip']} | Ağ Geçidi: {veriler['ag_gecidi']}\n\n")
                    for c in veriler["tespit_edilen_cihazlar"]:
                        f.write(f"- IP: {c['ip']} | MAC: {c['mac']} | Üretici: {c['uretici']} | Tür: {c['tur']}\n")

            messagebox.showinfo("Başarılı", f"Ağ topoloji raporu kaydedildi:\n{yol}", parent=self)
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor kaydedilemedi: {e}", parent=self)

    def _guvenli_kapat(self) -> None:
        self._animasyon_aktif = False
        self._otomatik_tarama_aktif = False
        self.destroy()
