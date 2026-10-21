# -*- coding: utf-8 -*-
"""
================================================================================
ALTAR SİBER & RETRO OYUN MERKEZİ (GELİŞMİŞ GRAFİK VE MEKANİKLER)
================================================================================
* 4 Derinlikli, Yüksek Performanslı Python Oyunu:
  1. Galaktik Savunma 2.0 (Nebula Interceptor):
     - Parallaks yıldız derinliği, itici alev parçacıkları, çoklu düşman sınıfları,
       ana boss gemisi, 3'lü lazer, kalkan, EMP nükleer bomba ve kombo sistemi.
  2. Kuantum Siber Yılan 2.0:
     - Çift katmanlı neon ışıma (bloom), parlayan kuyruk tozu, dalgalanan grid,
       altın kripto yemleri, zaman dondurma ve duvardan/kendinden geçiş kuantum modu.
  3. Siber Güvenlik & Terminal Hack 2.0:
     - CRT scanline terminali, canlı hex bellek matrisi, port dizileme,
     - Hacker Envanteri: Brute-Force Exploit, DDoS Flooder, Proxy Bouncer.
  4. Nöral AI Pong Düellosu 2.0:
     - Synthwave neon ızgara, kuyruklu yıldız top izi, falso/spin ve şut mekaniği,
     - Büyüyen raketler, ateş topu, 3 farklı yapay zeka zorluk modu.
* Yerel JSON Skor Tablosu (.altar_hafiza/oyun_skorlari.json).
* Çerçevesiz (Borderless) Tam Ekran ve Windows API otomatik odaklanma.
================================================================================
"""

import os
import sys
import time
import math
import json
import random
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Windows API Entegrasyonu
if os.name == "nt":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

SKOR_DIZINI = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".altar_hafiza")
SKOR_DOSYASI = os.path.join(SKOR_DIZINI, "oyun_skorlari.json")


def _skorlari_yukle():
    os.makedirs(SKOR_DIZINI, exist_ok=True)
    if os.path.isfile(SKOR_DOSYASI):
        try:
            with open(SKOR_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "galaktik_savunma": {"skor": 0, "isim": "Uzay_Pilotu"},
        "kuantum_yilan": {"skor": 0, "isim": "Neon_Gezgini"},
        "siber_hack": {"skor": 0, "isim": "Altar_Agent"},
        "ai_pong": {"skor": 0, "isim": "Altar_Duelist"}
    }


def _skor_kaydet(oyun_kodu, yeni_skor, isim="Oyuncu"):
    skorlar = _skorlari_yukle()
    mevcut = skorlar.get(oyun_kodu, {}).get("skor", 0)
    if yeni_skor > mevcut:
        skorlar[oyun_kodu] = {"skor": yeni_skor, "isim": isim, "tarih": time.strftime("%Y-%m-%d %H:%M")}
        try:
            with open(SKOR_DOSYASI, "w", encoding="utf-8") as f:
                json.dump(skorlar, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return True
    return False


# ==============================================================================
# OYUN 1: GALAKTİK SAVUNMA 2.0 (GELİŞMİŞ GRAFİK, DÜŞMAN SINIFLARI & BOSS)
# ==============================================================================
class GalaktikSavunmaOyunu(ctk.CTkFrame):
    def __init__(self, parent, ana_merkez=None):
        super().__init__(parent, fg_color="#020617")
        self.ana_merkez = ana_merkez
        self.oyun_aktif = False
        self.skor = 0
        self.can = 3
        self.kalkan_enerji = 100
        self.gemi_x = 350
        self.gemi_y = 480
        self.gemi_vx = 0
        self.sektor = 1
        self.emp_adedi = 2
        self.uclu_lazer_zamani = 0.0

        # Nesneler
        self.mermiler = []
        self.dusmanlar = []
        self.parcaciklar = []
        self.guclendirmeler = []
        self.yildizlar = []
        self.yazi_efektleri = []
        self.boss = None

        self.tuslar = {"Left": False, "Right": False, "space": False, "b": False}
        self._arayuz_olustur()

    def _arayuz_olustur(self):
        ust = ctk.CTkFrame(self, fg_color="#0B132B", height=44, corner_radius=6)
        ust.pack(fill="x", padx=10, pady=(8, 4))

        self.lbl_hud = ctk.CTkLabel(
            ust,
            text="🚀 SEKTÖR: 1 | Skor: 0 | Kalkan: ❤❤❤ (100%) | EMP Bombası: 💣x2",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#38BDF8"
        )
        self.lbl_hud.pack(side="left", padx=14)

        btn_baslat = ctk.CTkButton(
            ust, text="🚀 Oyunu Başlat", width=120, height=28,
            fg_color="#059669", hover_color="#047857",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self.oyunu_baslat
        )
        btn_baslat.pack(side="right", padx=12)

        self.canvas = tk.Canvas(
            self, bg="#02040A", highlightthickness=1, highlightbackground="#1E293B"
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        self.canvas.bind("<KeyPress>", self._tus_basildi)
        self.canvas.bind("<KeyRelease>", self._tus_birakildi)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())

        # Parallaks Yıldız Katmanları (Hızlı, Orta, Yavaş)
        self.yildizlar = [
            {"x": random.randint(0, 1000), "y": random.randint(0, 800), "hiz": random.choice([0.6, 1.4, 3.2]), "r": random.choice([1, 1.5, 2]), "renk": random.choice(["#334155", "#64748B", "#38BDF8"])}
            for _ in range(70)
        ]

    def oyunu_baslat(self):
        self.canvas.focus_set()
        w = max(400, self.canvas.winfo_width())
        h = max(300, self.canvas.winfo_height())
        self.gemi_x = w // 2
        self.gemi_y = h - 65
        self.gemi_vx = 0
        self.skor = 0
        self.can = 3
        self.kalkan_enerji = 100
        self.sektor = 1
        self.emp_adedi = 2
        self.uclu_lazer_zamani = 0.0
        self.mermiler.clear()
        self.dusmanlar.clear()
        self.parcaciklar.clear()
        self.guclendirmeler.clear()
        self.yazi_efektleri.clear()
        self.boss = None
        self.oyun_aktif = True
        self._oyun_dongusu()

    def _tus_basildi(self, event):
        k = event.keysym
        if k in ("Left", "a", "A"):
            self.tuslar["Left"] = True
        elif k in ("Right", "d", "D"):
            self.tuslar["Right"] = True
        elif k == "space" and self.oyun_aktif:
            self._ates_et()
        elif k in ("b", "B") and self.oyun_aktif:
            self._emp_bombasi_patlat()

    def _tus_birakildi(self, event):
        k = event.keysym
        if k in ("Left", "a", "A"):
            self.tuslar["Left"] = False
        elif k in ("Right", "d", "D"):
            self.tuslar["Right"] = False

    def _ates_et(self):
        # Normal veya 3'lü Lazer Modu
        if time.time() < self.uclu_lazer_zamani:
            self.mermiler.append({"x": self.gemi_x - 14, "y": self.gemi_y - 20, "vx": -2.0, "vy": -15, "renk": "#00FFCC"})
            self.mermiler.append({"x": self.gemi_x, "y": self.gemi_y - 24, "vx": 0.0, "vy": -16, "renk": "#38BDF8"})
            self.mermiler.append({"x": self.gemi_x + 14, "y": self.gemi_y - 20, "vx": 2.0, "vy": -15, "renk": "#00FFCC"})
        else:
            self.mermiler.append({"x": self.gemi_x - 8, "y": self.gemi_y - 20, "vx": 0.0, "vy": -15, "renk": "#00FFCC"})
            self.mermiler.append({"x": self.gemi_x + 8, "y": self.gemi_y - 20, "vx": 0.0, "vy": -15, "renk": "#00FFCC"})

    def _emp_bombasi_patlat(self):
        if self.emp_adedi > 0 and self.oyun_aktif:
            self.emp_adedi -= 1
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            # Ekrandaki tüm düşmanları yok et
            for d in self.dusmanlar:
                self.skor += 30
                self._patlama_efekti(d["x"], d["y"], buyukluk=14, renk="#A855F7")
            self.dusmanlar.clear()
            self._yazi_efekti_ekle(w // 2, h // 2, "⚡ EMP PATLAMASI! ⚡", "#C084FC")

    def _patlama_efekti(self, x, y, buyukluk=12, renk="#F97316"):
        for _ in range(buyukluk):
            hiz = random.uniform(2.5, 7.5)
            aci = random.uniform(0, 2 * math.pi)
            self.parcaciklar.append({
                "x": x, "y": y,
                "vx": math.cos(aci) * hiz, "vy": math.sin(aci) * hiz,
                "omur": random.randint(15, 30), "renk": renk, "r": random.randint(2, 4)
            })

    def _yazi_efekti_ekle(self, x, y, metin, renk):
        self.yazi_efektleri.append({"x": x, "y": y, "metin": metin, "renk": renk, "omur": 24})

    def _oyun_dongusu(self):
        if not self.oyun_aktif or not self.winfo_exists():
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100:
            w, h = 750, 500

        # Gemi Hızlanma ve Sönümlenme Fiziği (Inertia)
        if self.tuslar["Left"]:
            self.gemi_vx = max(-14, self.gemi_vx - 2.2)
        elif self.tuslar["Right"]:
            self.gemi_vx = min(14, self.gemi_vx + 2.2)
        else:
            self.gemi_vx *= 0.82

        self.gemi_x += self.gemi_vx
        self.gemi_x = max(35, min(w - 35, self.gemi_x))

        # İtici Parçacıkları Saç
        if random.random() > 0.2:
            self.parcaciklar.append({
                "x": self.gemi_x + random.uniform(-4, 4), "y": self.gemi_y + 16,
                "vx": random.uniform(-1.0, 1.0), "vy": random.uniform(4.0, 8.0),
                "omur": 14, "renk": random.choice(["#F97316", "#FBBF24", "#00FFCC"]), "r": random.randint(2, 3)
            })

        # Sektör Seviyesi & Düşman Üretimi
        self.sektor = 1 + (self.skor // 300)
        uretme_olasiligi = min(0.085, 0.038 + (self.sektor * 0.008))

        if random.random() < uretme_olasiligi and (self.boss is None):
            tip = random.choices(["avci", "agir_kruvazor", "kamikaze"], weights=[60, 25, 15])[0]
            if tip == "avci":
                self.dusmanlar.append({
                    "tip": "avci", "x": random.randint(40, w - 40), "y": -25,
                    "vx": random.uniform(-1.2, 1.2), "vy": random.uniform(3.0, 4.8),
                    "can": 1, "r": 15, "renk": "#EF4444"
                })
            elif tip == "agir_kruvazor":
                self.dusmanlar.append({
                    "tip": "agir_kruvazor", "x": random.randint(50, w - 50), "y": -35,
                    "vx": random.uniform(-0.6, 0.6), "vy": random.uniform(1.8, 2.6),
                    "can": 3, "r": 24, "renk": "#F97316"
                })
            elif tip == "kamikaze":
                self.dusmanlar.append({
                    "tip": "kamikaze", "x": random.randint(40, w - 40), "y": -20,
                    "vx": random.uniform(-2.5, 2.5), "vy": random.uniform(6.0, 8.5),
                    "can": 1, "r": 12, "renk": "#A855F7"
                })

        # Boss Mothership Mekaniği (Her 400 Skorda Bir)
        if self.skor >= 400 and (self.boss is None) and (self.skor % 400 < 50):
            self.boss = {
                "x": w // 2, "y": 70, "vx": 3.0, "can": 35, "max_can": 35,
                "w": 110, "h": 40, "renk": "#DC2626"
            }
            self._yazi_efekti_ekle(w // 2, 140, "⚠ DİKKAT: ANA SAVAŞ GEMİSİ YAKLAŞIYOR! ⚠", "#EF4444")

        # Boss Güncelle
        if self.boss:
            self.boss["x"] += self.boss["vx"]
            if self.boss["x"] < 80 or self.boss["x"] > w - 80:
                self.boss["vx"] = -self.boss["vx"]
            # Boss lazer ateşi
            if random.random() < 0.05:
                self.dusmanlar.append({
                    "tip": "kamikaze", "x": self.boss["x"] + random.choice([-30, 30]), "y": self.boss["y"] + 25,
                    "vx": random.uniform(-1, 1), "vy": 6.0, "can": 1, "r": 10, "renk": "#F87171"
                })

        # Mermileri Güncelle
        for m in self.mermiler:
            m["x"] += m["vx"]
            m["y"] += m["vy"]
        self.mermiler = [m for m in self.mermiler if m["y"] > -20]

        # Düşmanları Güncelle
        for d in self.dusmanlar:
            d["x"] += d["vx"]
            d["y"] += d["vy"]
            if d["x"] < 25 or d["x"] > w - 25:
                d["vx"] = -d["vx"]

        # Güçlendirmeleri Güncelle
        for g in self.guclendirmeler:
            g["y"] += 2.8
            # Gemi topladı mı?
            if math.hypot(g["x"] - self.gemi_x, g["y"] - self.gemi_y) < 32:
                if g["tur"] == "lazer":
                    self.uclu_lazer_zamani = time.time() + 12.0
                    self._yazi_efekti_ekle(self.gemi_x, self.gemi_y - 30, "⚡ 3'LÜ LAZER AKTİF! ⚡", "#00FFCC")
                elif g["tur"] == "kalkan":
                    self.can = min(3, self.can + 1)
                    self.kalkan_enerji = 100
                    self._yazi_efekti_ekle(self.gemi_x, self.gemi_y - 30, "🛡 KALKAN YENİLENDİ!", "#38BDF8")
                elif g["tur"] == "emp":
                    self.emp_adedi = min(4, self.emp_adedi + 1)
                    self._yazi_efekti_ekle(self.gemi_x, self.gemi_y - 30, "💣 +1 EMP BOMBASI!", "#C084FC")
                g["omur"] = 0
        self.guclendirmeler = [g for g in self.guclendirmeler if g["y"] < h + 20 and g.get("omur", 1) > 0]

        # Mermi - Boss Çarpışması
        if self.boss:
            bx, by = self.boss["x"], self.boss["y"]
            for m in list(self.mermiler):
                if abs(m["x"] - bx) < self.boss["w"] // 2 and abs(m["y"] - by) < self.boss["h"] // 2:
                    self.mermiler.remove(m)
                    self.boss["can"] -= 1
                    self._patlama_efekti(m["x"], m["y"], buyukluk=4, renk="#FACC15")
                    if self.boss["can"] <= 0:
                        self.skor += 250
                        self._patlama_efekti(bx, by, buyukluk=35, renk="#EF4444")
                        self._yazi_efekti_ekle(bx, by, "🏆 BOSS İMHA EDİLDİ! (+250)", "#FACC15")
                        self.boss = None
                        break

        # Mermi - Düşman Çarpışmaları
        kalan_dusmanlar = []
        for d in self.dusmanlar:
            vuruldu = False
            for m in list(self.mermiler):
                if math.hypot(d["x"] - m["x"], d["y"] - m["y"]) < d["r"] + 8:
                    if m in self.mermiler:
                        self.mermiler.remove(m)
                    d["can"] -= 1
                    if d["can"] <= 0:
                        vuruldu = True
                        puan = 20 if d["tip"] == "avci" else (50 if d["tip"] == "agir_kruvazor" else 35)
                        self.skor += puan
                        self._patlama_efekti(d["x"], d["y"], buyukluk=12, renk=d["renk"])
                        # Güçlendirme Düşürme Şansı (%18)
                        if random.random() < 0.18:
                            tur = random.choice(["lazer", "kalkan", "emp"])
                            self.guclendirmeler.append({"x": d["x"], "y": d["y"], "tur": tur})
                    else:
                        self._patlama_efekti(m["x"], m["y"], buyukluk=4, renk="#FACC15")
                    break

            if not vuruldu:
                # Gemiye Çarpma
                if math.hypot(d["x"] - self.gemi_x, d["y"] - self.gemi_y) < d["r"] + 20:
                    self.can -= 1
                    self.kalkan_enerji = max(0, self.kalkan_enerji - 40)
                    self._patlama_efekti(d["x"], d["y"], buyukluk=16, renk="#EF4444")
                    self._yazi_efekti_ekle(self.gemi_x, self.gemi_y - 40, "⚠ DARBE ALINDI!", "#EF4444")
                elif d["y"] < h + 30:
                    kalan_dusmanlar.append(d)
                else:
                    kalan_dusmanlar.append(d)
        self.dusmanlar = [d for d in kalan_dusmanlar if d["y"] < h + 30]

        # Parçacıklar
        for p in self.parcaciklar:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["omur"] -= 1
        self.parcaciklar = [p for p in self.parcaciklar if p["omur"] > 0]

        # Yazı Efektleri
        for yz in self.yazi_efektleri:
            yz["y"] -= 1.0
            yz["omur"] -= 1
        self.yazi_efektleri = [yz for yz in self.yazi_efektleri if yz["omur"] > 0]

        # ÇİZİM
        self.canvas.delete("all")

        # Parallaks Yıldızlar
        for yz in self.yildizlar:
            yz["y"] = (yz["y"] + yz["hiz"]) % h
            r = yz["r"]
            self.canvas.create_oval(yz["x"] - r, yz["y"] - r, yz["x"] + r, yz["y"] + r, fill=yz["renk"], outline="")

        # Gemi Çizimi (Modern İleri Seviye Starfighter)
        gx, gy = self.gemi_x, self.gemi_y

        # Kalkan Balonu (Varsa)
        if self.can > 1:
            self.canvas.create_oval(gx - 32, gy - 32, gx + 32, gy + 32, outline="#00E5FF", width=1)

        # Kanatlar ve Gövde
        self.canvas.create_polygon(
            gx, gy - 26, gx - 24, gy + 16, gx - 12, gy + 8,
            gx, gy + 14, gx + 12, gy + 8, gx + 24, gy + 16,
            fill="#0F172A", outline="#00E5FF", width=2
        )
        # Kokpit Camı
        self.canvas.create_oval(gx - 5, gy - 14, gx + 5, gy + 2, fill="#38BDF8", outline="#E2E8F0")

        # Mermiler
        for m in self.mermiler:
            self.canvas.create_line(m["x"], m["y"], m["x"], m["y"] - 14, fill=m["renk"], width=3)

        # Düşmanlar
        for d in self.dusmanlar:
            dx, dy, r = d["x"], d["y"], d["r"]
            if d["tip"] == "avci":
                self.canvas.create_polygon(dx, dy + r, dx - r, dy - r, dx + r, dy - r, fill=d["renk"], outline="#FECACA")
            elif d["tip"] == "agir_kruvazor":
                self.canvas.create_polygon(dx - r, dy, dx - r // 2, dy - r, dx + r // 2, dy - r, dx + r, dy, dx + r // 2, dy + r, dx - r // 2, dy + r, fill=d["renk"], outline="#FEF08A", width=2)
                # Küçük can barı
                self.canvas.create_rectangle(dx - 15, dy - r - 8, dx + 15, dy - r - 4, fill="#334155")
                self.canvas.create_rectangle(dx - 15, dy - r - 8, dx - 15 + (d["can"] / 3) * 30, dy - r - 4, fill="#22C55E")
            else:
                self.canvas.create_oval(dx - r, dy - r, dx + r, dy + r, fill=d["renk"], outline="#E9D5FF")

        # Boss Çizimi
        if self.boss:
            bx, by, bw, bh = self.boss["x"], self.boss["y"], self.boss["w"], self.boss["h"]
            self.canvas.create_rectangle(bx - bw // 2, by - bh // 2, bx + bw // 2, by + bh // 2, fill="#7F1D1D", outline="#EF4444", width=3)
            # Boss Can Barı
            self.canvas.create_rectangle(bx - 60, by - 35, bx + 60, by - 25, fill="#1E293B", outline="#FFFFFF")
            self.canvas.create_rectangle(bx - 60, by - 35, bx - 60 + (self.boss["can"] / self.boss["max_can"]) * 120, by - 25, fill="#EF4444")
            self.canvas.create_text(bx, by - 44, text="ANA GEMİ (BOSS)", fill="#EF4444", font=("Consolas", 10, "bold"))

        # Güçlendirme Küreleri
        for g in self.guclendirmeler:
            gx, gy = g["x"], g["y"]
            renk = "#00FFCC" if g["tur"] == "lazer" else ("#38BDF8" if g["tur"] == "kalkan" else "#C084FC")
            sembol = "⚡" if g["tur"] == "lazer" else ("🛡" if g["tur"] == "kalkan" else "💣")
            self.canvas.create_oval(gx - 12, gy - 12, gx + 12, gy + 12, fill="#0F172A", outline=renk, width=2)
            self.canvas.create_text(gx, gy, text=sembol, fill=renk, font=("Consolas", 11, "bold"))

        # Parçacıklar
        for p in self.parcaciklar:
            r = p.get("r", 2)
            self.canvas.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r, fill=p["renk"], outline="")

        # Kayan Yazı Efektleri
        for yz in self.yazi_efektleri:
            self.canvas.create_text(yz["x"], yz["y"], text=yz["metin"], fill=yz["renk"], font=("Consolas", 12, "bold"))

        # Can Kontrolü
        if self.can <= 0:
            self.oyun_aktif = False
            _skor_kaydet("galaktik_savunma", self.skor)
            self.lbl_hud.configure(text=f"OYUN BİTTİ! Toplam Skor: {self.skor}")
            self.canvas.create_text(
                w // 2, h // 2,
                text=f"💥 GEMİ İMHA EDİLDİ 💥\nNihai Skor: {self.skor}\nSektör: {self.sektor}",
                fill="#EF4444", font=("Consolas", 22, "bold"), justify="center"
            )
            return

        lazer_durum = " | ⚡ 3'LÜ LAZER!" if time.time() < self.uclu_lazer_zamani else ""
        self.lbl_hud.configure(
            text=f"🚀 SEKTÖR: {self.sektor} | Skor: {self.skor} | Kalkan: {'❤'*self.can} | EMP Bombası: 💣x{self.emp_adedi}{lazer_durum}"
        )
        self.after(22, self._oyun_dongusu)

# ==============================================================================
# ANA OYUN MERKEZİ HUB (GALAKTİK SAVUNMA - 60 FPS)
# ==============================================================================
class AltarOyunMerkezi(ctk.CTkFrame):
    def __init__(self, parent, pencere_modu=False):
        super().__init__(parent, fg_color="#050811")
        self.pencere_modu = pencere_modu
        self.aktif_oyun = None

        self._arayuz_olustur()

    def _arayuz_olustur(self):
        ust_bar = ctk.CTkFrame(self, fg_color="#0A0F1D", height=50, corner_radius=8, border_width=1, border_color="#1E3A8A")
        ust_bar.pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            ust_bar, text="🚀 ALTAR GALAKTİK SAVUNMA (NEBULA INTERCEPTOR - 60 FPS)",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#00FFCC"
        ).pack(side="left", padx=14)

        btn_tam_ekran = ctk.CTkButton(
            ust_bar, text="⛶ Tam Ekran Oyna (Kiosk)", width=170, height=30,
            fg_color="#0284C7", hover_color="#0369A1",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self.tam_ekran_oyun_merkezi_ac
        )
        btn_tam_ekran.pack(side="right", padx=12)

        self.icerik_alani = ctk.CTkFrame(self, fg_color="transparent")
        self.icerik_alani.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.aktif_oyun = GalaktikSavunmaOyunu(self.icerik_alani, ana_merkez=self)
        self.aktif_oyun.pack(fill="both", expand=True)

    def tam_ekran_oyun_merkezi_ac(self):
        pencere = ctk.CTkToplevel(self)
        pencere.title("🚀 Altar Galaktik Savunma - Tam Ekran")
        pencere.configure(fg_color="#020617")
        pencere.overrideredirect(True)

        g = pencere.winfo_screenwidth()
        y = pencere.winfo_screenheight()
        pencere.geometry(f"{g}x{y}+0+0")
        pencere.attributes("-topmost", True)
        pencere.focus_force()

        if os.name == "nt":
            try:
                hwnd = pencere.winfo_id()
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass

        pencere.bind("<Escape>", lambda e: pencere.destroy())
        pencere.bind("<F11>", lambda e: pencere.destroy())

        hub = AltarOyunMerkezi(pencere, pencere_modu=True)
        hub.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = ctk.CTk()
    app.title("Altar Galaktik Savunma Test")
    app.geometry("950x700")
    merkez = AltarOyunMerkezi(app)
    merkez.pack(fill="both", expand=True)
    app.mainloop()
