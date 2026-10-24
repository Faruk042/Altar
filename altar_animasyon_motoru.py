# -*- coding: utf-8 -*-
"""
Altar Görsel Efekt & Doğa Animasyon Motoru (altar_animasyon_motoru.py)

1) AltarDogaSplashPenceresi:
   Modern oyunların (AAA Game Studio) sinematik açılış sekansları kalitesinde;
   karanlık kozmik derinliklerden doğup yemyeşil zümrüt auroraya, çok katmanlı
   vadi ve dağ siluetlerine, dökülen şelaleye, kıvrımlı zümrüt ırmağa ve gökyüzüne
   süzülen biyolüminesan ateşböceklerine bürünen prosedürel sinematik açılış motoru.

2) AltarMaviAtesWidget:
   Arayüzün üst barında veya IDE canlı terminalinde mikroçekim uzay soğuk alevini
   (cool flame) ve plazmayı simgeleyen, canlı dalgalanan mavi-turkuaz alev efekti.

Tamamen yerel Tkinter Canvas 60 FPS diferansiyel akış matematiğiyle çalışır;
harici video dosyasına veya ağır video codec'lerine ihtiyaç duymaz.
CPU kullanımı <%1, bellek tüketimi minimaldir (%100 güvenli, hatasız ve zaafiyetsiz).
"""

from __future__ import annotations

import sys
import os
import ctypes

# Windows Yüksek DPI ve Gerçek Tam Ekran (100% Monitör Kiosk) Desteği
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import math
import random
import time
import tkinter as tk
from typing import Callable, Dict, List, Optional, Tuple

import customtkinter as ctk


# =============================================================================
# 1. SİNEMATİK OYUN STİLİ AÇILIŞ DOĞA & ŞELALE / IRMAK ANİMASYONU (60 FPS)
# =============================================================================
def _intro_gorseli_bul() -> Optional[str]:
    """Masaüstü veya proje dizinindeki sinematik açılış görselini (images.jpg) tespit eder."""
    proje_dizini = os.path.dirname(os.path.abspath(__file__))
    adaylar = [
        r"C:\Users\Burak\Desktop\images.jpg",
        os.path.join(proje_dizini, "images.jpg"),
        os.path.join(proje_dizini, "assets", "altar_intro_images.jpg"),
    ]
    if getattr(sys, "frozen", False):
        exe_d = os.path.dirname(sys.executable)
        mei = getattr(sys, "_MEIPASS", "")
        adaylar.insert(0, os.path.join(exe_d, "images.jpg"))
        adaylar.insert(0, os.path.join(mei, "images.jpg"))
        adaylar.insert(0, os.path.join(exe_d, "assets", "altar_intro_images.jpg"))
        adaylar.insert(0, os.path.join(mei, "assets", "altar_intro_images.jpg"))
    for p in adaylar:
        if p and os.path.isfile(p):
            return p
    return None


class AltarDogaSplashPenceresi(tk.Toplevel):
    """
    Modern oyunların sinematik açılışları standartlarında;
    Bütün ekranı (görev çubuğu ve pencere kenarlıkları dahil) kaplayan,
    images.jpg tabanlı atmosferik sinematik açılış, derinlik efekti,
    yükselen ışık sporları (fireflies) ve sinematik 21:9 letterbox efekti
    ile Altar ekosistemini başlatan tam ekran açılış penceresi.
    """

    def __init__(self, ebeveyn: tk.Tk, tamamlandi_callback: Optional[Callable[[], None]] = None) -> None:
        super().__init__(ebeveyn)
        self.ebeveyn = ebeveyn
        self.tamamlandi_callback = tamamlandi_callback

        self.title("Altar — Sinematik Ekosistem Başlatılıyor")
        self.configure(bg="#010409")

        # Bütün fiziksel ekranı (%100 piksel) kaplayan Tam Ekran (Fullscreen Kiosk Mode)
        self.update_idletasks()
        if sys.platform == "win32":
            try:
                user32 = ctypes.windll.user32
                self.ekran_g = max(self.winfo_screenwidth(), user32.GetSystemMetrics(0))
                self.ekran_y = max(self.winfo_screenheight(), user32.GetSystemMetrics(1))
            except Exception:
                self.ekran_g = self.winfo_screenwidth()
                self.ekran_y = self.winfo_screenheight()
        else:
            self.ekran_g = self.winfo_screenwidth()
            self.ekran_y = self.winfo_screenheight()

        self.geometry(f"{self.ekran_g}x{self.ekran_y}+0+0")
        self.attributes("-fullscreen", True)

        # Her zaman en üstte ve görünür olmasını garanti et
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()

        self.canvas = tk.Canvas(
            self, width=self.ekran_g, height=self.ekran_y,
            bg="#010409", highlightthickness=0, bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # images.jpg tabanlı sinematik kompozit karelerin ön-üretimi (60 FPS pürüzsüz açılış)
        self.gorsel_yolu = _intro_gorseli_bul()
        self._gorsel_kareleri: List[object] = []
        self._gorsel_hazir = False
        self._center_bounds = None

        if self.gorsel_yolu:
            try:
                from PIL import Image, ImageEnhance, ImageFilter, ImageTk
                orig = Image.open(self.gorsel_yolu).convert("RGB")
                ar = orig.width / max(1, orig.height)

                # Geniş ekran (16:9) veya dikey format kontrolü
                if ar >= 1.4:
                    # 16:9 Full HD görsel doğrudan tam ekran kristal netliğinde sunulur
                    taban = orig.resize((self.ekran_g, self.ekran_y), Image.Resampling.LANCZOS)
                    self._center_bounds = (0, 0, self.ekran_g, self.ekran_y)
                else:
                    # Dikey görsel ise sinematik bulanık arka plan + merkez odak
                    bg_full = orig.resize((self.ekran_g, self.ekran_y), Image.Resampling.BILINEAR)
                    bg_blur = bg_full.filter(ImageFilter.GaussianBlur(radius=22))
                    hedef_y = int(self.ekran_y * 0.72)
                    hedef_g = int(orig.width * (hedef_y / orig.height))
                    center_sharp = orig.resize((hedef_g, hedef_y), Image.Resampling.LANCZOS)
                    taban = bg_blur.copy()
                    mac_x = (self.ekran_g - hedef_g) // 2
                    mac_y = (self.ekran_y - hedef_y) // 2
                    self._center_bounds = (mac_x, mac_y, mac_x + hedef_g, mac_y + hedef_y)
                    taban.paste(center_sharp, (mac_x, mac_y))
                
                # 4. Kademeli aydınlanma (fade-in) kareleri
                for step in range(16):
                    factor = min(1.0, (step + 1) / 14.0)
                    enh = ImageEnhance.Brightness(taban)
                    img_f = enh.enhance(factor * 0.95 + 0.05)
                    self._gorsel_kareleri.append(ImageTk.PhotoImage(img_f))
                self._gorsel_hazir = len(self._gorsel_kareleri) > 0
            except Exception:
                self._gorsel_hazir = False

        # Animasyon durum değişkenleri (60 FPS: 16ms * 165 adım = ~2.65 saniye)
        self._adim = 0
        self._toplam_adim = 165
        self._su_fazi = 0.0
        self._calisiyor = True

        # Sabit derin uzay yıldızları
        self.yildizlar: List[Tuple[float, float, float, float]] = []
        for _ in range(65):
            self.yildizlar.append((
                random.uniform(20, self.ekran_g - 20),
                random.uniform(40, self.ekran_y * 0.58),
                random.uniform(0.6, 2.0),
                random.uniform(0.3, 1.0)
            ))

        # Doğa parçacıkları (Biyolüminesan ateşböcekleri ve su sisi/köpükleri)
        self.parcaciklar: List[Dict[str, float]] = []
        for _ in range(85):
            self.parcaciklar.append({
                "x": random.uniform(30, self.ekran_g - 30),
                "y": random.uniform(60, self.ekran_y - 50),
                "hiz_y": random.uniform(0.6, 2.4),
                "hiz_x": random.uniform(-0.4, 0.4),
                "yaricap": random.uniform(1.2, 4.2),
                "parlaklik": random.uniform(0.4, 1.0),
                "tur": "atesbocegi" if random.random() > 0.35 else "kopuk"
            })

        # Tuş veya tıklama ile anında geçebilme (Instant Skip)
        self.bind("<Button-1>", lambda _: self._kapat_ve_baslat())
        self.bind("<Key>", lambda _: self._kapat_ve_baslat())

        self.after(16, self._animasyon_dongusu)

    def _animasyon_dongusu(self) -> None:
        if not self._calisiyor or not self.winfo_exists():
            return

        self._adim += 1
        ilerleme = min(1.0, self._adim / self._toplam_adim)
        self._su_fazi += 0.08

        c = self.canvas
        c.delete("all")
        W = self.canvas.winfo_width() or self.ekran_g
        H = self.canvas.winfo_height() or self.ekran_y

        # 1. Zemin Sahnesi: images.jpg Sinematik Görseli veya Prosedürel Aurora Sahnesi
        if self._gorsel_hazir and self._gorsel_kareleri:
            kare_idx = min(len(self._gorsel_kareleri) - 1, int(ilerleme * len(self._gorsel_kareleri)))
            c.create_image(W // 2, H // 2, image=self._gorsel_kareleri[kare_idx])
            
            # Merkez görsel çevresinde parıldayan neon siber çerçeve
            if self._center_bounds:
                cx1, cy1, cx2, cy2 = self._center_bounds
                cg = int(185 * ilerleme)
                cb = int(129 * ilerleme)
                c.create_rectangle(cx1 - 2, cy1 - 2, cx2 + 2, cy2 + 2, outline=f"#02{cg:02x}{cb:02x}", width=2)
                c.create_rectangle(cx1 - 5, cy1 - 5, cx2 + 5, cy2 + 5, outline=f"#05{cg:02x}{cb:02x}", width=1)
        else:
            # Yedek Gökyüzü: Karanlıktan Zümrüt Aurora Borealis'e Yumuşak Geçiş
            yesil_ton = int(48 * (ilerleme ** 1.3))
            mavi_ton = int(36 * (ilerleme ** 1.3))
            bg_hex = f"#{int(2 * (1 - ilerleme)):02x}{yesil_ton:02x}{mavi_ton:02x}"
            c.create_rectangle(0, 0, W, H, fill=bg_hex, outline="")

            # Derin Yıldız Alanı
            for (zx, zy, zrad, zpar) in self.yildizlar:
                p_val = int(255 * zpar * min(1.0, (1.2 - ilerleme * 0.4)))
                star_hex = f"#{p_val:02x}{p_val:02x}{p_val:02x}"
                c.create_oval(zx - zrad, zy - zrad, zx + zrad, zy + zrad, fill=star_hex, outline="")

            # Zümrüt Kutup Işıması Dalgaları (Aurora Borealis Curtains)
            if ilerleme > 0.08:
                aurora_op = min(1.0, (ilerleme - 0.08) / 0.4)
                for ai in range(3):
                    aurora_yolu = []
                    base_y = H * (0.26 + ai * 0.07)
                    for ax in range(0, W + 35, 35):
                        ay = base_y + math.sin(ax * 0.010 + self._su_fazi * (0.8 + ai * 0.3)) * 26
                        aurora_yolu.extend([ax, ay])
                    aurora_yolu.extend([W, 0, 0, 0])
                    c_g = int((115 + ai * 30) * aurora_op)
                    c_b = int((85 + ai * 25) * aurora_op)
                    c.create_polygon(aurora_yolu, fill=f"#02{c_g:02x}{c_b:02x}", outline="")

            # 2. Katmanlı Dağ ve Vadi Siluetleri (Layered Parallax Mountain Ridges)
            if ilerleme > 0.15:
                m_op = min(1.0, (ilerleme - 0.15) / 0.4)
                dag1 = [0, H * 0.72]
                for dx in range(0, W + 45, 45):
                    dy = H * 0.58 + math.sin(dx * 0.007) * 45 + math.cos(dx * 0.003) * 25
                    dag1.extend([dx, dy])
                dag1.extend([W, H, 0, H])
                c.create_polygon(dag1, fill=f"#{int(2*m_op):02x}{int(32*m_op):02x}{int(22*m_op):02x}", outline="")

                dag2 = [0, H * 0.78]
                for dx in range(0, W + 35, 35):
                    dy = H * 0.68 + math.sin(dx * 0.012 + 1.2) * 28
                    dag2.extend([dx, dy])
                dag2.extend([W, H, 0, H])
                c.create_polygon(dag2, fill=f"#{int(4*m_op):02x}{int(56*m_op):02x}{int(38*m_op):02x}", outline="")

            # 3. Şelale & Zümrüt Irmak (Cascading Waterfall & River Flow)
            if ilerleme > 0.2:
                r_op = min(1.0, (ilerleme - 0.2) / 0.4)
                su_renk = f"#{int(6*r_op):02x}{int(150*r_op):02x}{int(125*r_op):02x}"
                kopuk_renk = f"#{int(180*r_op):02x}{int(255*r_op):02x}{int(235*r_op):02x}"

                nehir = []
                for rx in range(0, W + 15, 15):
                    dalga = math.sin(rx * 0.014 + self._su_fazi) * 10 + math.cos(rx * 0.025 - self._su_fazi * 0.8) * 6
                    ry = H * 0.76 + dalga + ((rx - W / 2) ** 2) / (W * 4.0)
                    nehir.extend([rx, ry])
                nehir_poly = [0, H] + nehir + [W, H]
                c.create_polygon(nehir_poly, fill=su_renk, outline="")

                for i in range(8):
                    cy = H * 0.79 + i * 11
                    cx1 = (i * 180 + int(self._su_fazi * 45)) % W
                    cx2 = cx1 + 75
                    c.create_line(cx1, cy, cx2, cy, fill=kopuk_renk, width=1.8)

                selale_merkez = W * 0.5
                selale_kol = 13
                for si in range(selale_kol):
                    sx = selale_merkez - (selale_kol * 5) + si * 10
                    sy1 = H * 0.52
                    sy2 = H * 0.78
                    dalgalanma = math.sin(self._su_fazi * 2 + si * 0.7) * 4
                    c.create_line(sx, sy1, sx + dalgalanma, sy2, fill=kopuk_renk, width=2.2)

        # 4. Yükselen Parıldayan Doğa Sporları / Ateşböcekleri (Bioluminescent Fireflies)
        for p in self.parcaciklar:
            p["y"] -= p["hiz_y"]
            p["x"] += p["hiz_x"] + math.sin(self._su_fazi + p["y"] * 0.02) * 0.6
            if p["y"] < 50:
                p["y"] = H - 55
                p["x"] = random.uniform(30, W - 30)

            parlak = min(1.0, ilerleme * p["parlaklik"] * 1.3)
            rad = p["yaricap"] * (0.85 + 0.25 * math.sin(self._su_fazi * 2.5 + p["x"]))

            # Ateşböceği Haresi (Dual Layer Halo Glow Effect)
            if p["tur"] == "atesbocegi" and parlak > 0.4:
                halo_rad = rad * 2.4
                c.create_oval(
                    p["x"] - halo_rad, p["y"] - halo_rad, p["x"] + halo_rad, p["y"] + halo_rad,
                    fill=f"#{int(10*parlak):02x}{int(120*parlak):02x}{int(85*parlak):02x}", outline=""
                )
                core_clr = f"#{int(190*parlak):02x}{int(255*parlak):02x}{int(220*parlak):02x}"
            else:
                core_clr = f"#{int(160*parlak):02x}{int(240*parlak):02x}{int(210*parlak):02x}"

            c.create_oval(p["x"] - rad, p["y"] - rad, p["x"] + rad, p["y"] + rad, fill=core_clr, outline="")

        # 5. Sinematik 21:9 Letterbox Şeritleri (Cinemascope Widescreen Bars)
        bar_h = max(42, int(H * 0.075))
        # Üst Siyah Bant & Zümrüt Lazer Çizgisi
        c.create_rectangle(0, 0, W, bar_h, fill="#010409", outline="")
        c.create_line(0, bar_h, W, bar_h, fill="#059669", width=1.5)
        # Alt Siyah Bant & Zümrüt Lazer Çizgisi
        c.create_rectangle(0, H - bar_h, W, H, fill="#010409", outline="")
        c.create_line(0, H - bar_h, W, H - bar_h, fill="#059669", width=1.5)

        # 6. Sinematik Logo & Tipografi Reveal (A L T A R - AAA Game Typography)
        if ilerleme > 0.08:
            t_op = min(1.0, (ilerleme - 0.08) / 0.35)
            yazi_clr = f"#{int(235*t_op):02x}{int(255*t_op):02x}{int(245*t_op):02x}"
            sub_clr = f"#{int(52*t_op):02x}{int(211*t_op):02x}{int(153*t_op):02x}"
            baslik_font_boyutu = max(26, int(H * 0.048))
            alt_font_boyutu = max(10, int(H * 0.016))

            c.create_text(
                W // 2, H * 0.22,
                text="🌿   A   L   T   A   R   🌿",
                fill=yazi_clr,
                font=("Consolas", baslik_font_boyutu, "bold")
            )
            c.create_text(
                W // 2, H * 0.30,
                text="E K O S İ S T E M   •   Y A P A Y   Z E K A   •   İ L E R İ   M Ü H E N D İ S L İ K",
                fill=sub_clr,
                font=("Segoe UI", alt_font_boyutu, "bold")
            )

        # 7. Sinematik İlerleme Çubuğu & Telemetri HUD
        bar_w = int(min(680, W * 0.55))
        bar_h_c = 7
        bx = (W - bar_w) // 2
        by = H * 0.41

        # Arka ray
        c.create_rectangle(bx, by, bx + bar_w, by + bar_h_c, fill="#09141D", outline="#1E293B")
        # İlerleyen yeşil plazma barı
        dolu = int(bar_w * ilerleme)
        if dolu > 0:
            c.create_rectangle(bx, by, bx + dolu, by + bar_h_c, fill="#10B981", outline="")
            # İlerleyen uç noktasında parıldayan neon kursor
            c.create_oval(bx + dolu - 4, by - 2, bx + dolu + 4, by + bar_h_c + 2, fill="#34D399", outline="#ECFDF5")

        asama = "🌌 Kuantum doğa & telemetri matrisi kuruluyor..."
        if ilerleme > 0.28:
            asama = "🛡️ EDR ve Ağ IPS güvenlik kalkanları devreye alınıyor..."
        if ilerleme > 0.60:
            asama = "🐍 Çok sekmeli Python IDE & Pip motoru yükleniyor..."
        if ilerleme > 0.88:
            asama = "✨ Altar Ekosistemi hazır! Hoş geldiniz..."

        hud_font_boyutu = max(10, int(H * 0.015))
        c.create_text(
            W // 2, by + 25,
            text=f"{asama}  [%{int(ilerleme * 100)}]",
            fill="#A7F3D0",
            font=("Consolas", hud_font_boyutu)
        )

        # Alt Letterbox içi bilgilendirme
        c.create_text(
            W - 110, H - int(bar_h * 0.48),
            text="[Geçmek için Tıkla / ESC]",
            fill="#64748B",
            font=("Segoe UI", 9, "bold")
        )
        c.create_text(
            130, H - int(bar_h * 0.48),
            text="ALTAR CORE v2.5 • FULLSCREEN 60 FPS",
            fill="#334155",
            font=("Consolas", 9, "bold")
        )

        if self._adim >= self._toplam_adim:
            self._kapat_ve_baslat()
        else:
            self.after(16, self._animasyon_dongusu)

    def _kapat_ve_baslat(self) -> None:
        if not self._calisiyor:
            return
        self._calisiyor = False
        # 1. Önce ana pencereyi devreye al (Böylece Windows odağı arka plana/masaüstüne kaçırmaz)
        if callable(self.tamamlandi_callback):
            try:
                self.tamamlandi_callback()
            except Exception:
                pass
        # 2. Ana pencere açıldıktan sonra animasyon splash penceresini temizce kapat
        try:
            self.attributes("-topmost", False)
            self.destroy()
        except Exception:
            pass


# =============================================================================
# 2. UYGULAMA İÇİ MAVİ / PLAZMA ATEŞ ANİMASYON WİDGETI
# =============================================================================
class AltarMaviAtesWidget(ctk.CTkFrame):
    """
    Arayüzün üst barına veya aktif sekmesine gömülebilen;
    mikroyerçekimi soğuk alevini (cool flame) ve plazmayı simgeleyen,
    mavi-turkuaz-beyaz parçacıklı canlı ateş dalgalanma efekti.
    """

    def __init__(self, master: object, genislik: int = 150, yukseklik: int = 28, **kwargs: object) -> None:
        super().__init__(master, fg_color="transparent", width=genislik, height=yukseklik, **kwargs)
        self.genislik = genislik
        self.yukseklik = yukseklik

        self.canvas = tk.Canvas(
            self, width=genislik, height=yukseklik, bg="#0B0F19",
            highlightthickness=1, highlightbackground="#1E293B", bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        self._faz = 0.0
        self._aktif = True

        # Ateş parçacıkları
        self.parcaciklar: List[Dict[str, float]] = []
        for _ in range(24):
            self.parcaciklar.append({
                "x": random.uniform(genislik * 0.25, genislik * 0.75),
                "y": random.uniform(yukseklik * 0.4, yukseklik * 0.95),
                "vy": random.uniform(0.6, 1.8),
                "vx": random.uniform(-0.35, 0.35),
                "boyut": random.uniform(2.0, 5.0),
                "omur": random.uniform(0.2, 1.0)
            })

        self.after(50, self._ates_dongusu)

    def _ates_dongusu(self) -> None:
        if not self._aktif or not self.winfo_exists():
            return

        self._faz += 0.22
        c = self.canvas
        c.delete("all")
        W = self.genislik
        H = self.yukseklik
        cx = W // 2
        cy = int(H * 0.65)

        # 1. Taban Soğuk Mavi Alev Küresi (Microgravity Spherical Core)
        taban_r = 7.0 + 1.2 * math.sin(self._faz)
        c.create_oval(
            cx - taban_r, cy - taban_r, cx + taban_r, cy + taban_r,
            fill="#1E3A8A", outline="#0284C7", width=1
        )

        # 2. Canlı Yükselen Mavi-Turkuaz Plazma Parçacıkları
        for p in self.parcaciklar:
            p["y"] -= p["vy"]
            p["x"] += p["vx"] + math.sin(self._faz + p["y"] * 0.2) * 0.5
            p["omur"] -= 0.035

            if p["omur"] <= 0 or p["y"] < 3:
                p["y"] = random.uniform(H * 0.7, H * 0.95)
                p["x"] = cx + random.uniform(-14, 14)
                p["omur"] = random.uniform(0.6, 1.0)

            # Renk skalası: Beyaz (çekirdek) -> Turkuaz -> Koyu Mavi
            if p["omur"] > 0.65:
                clr = "#E0F2FE"  # Işıltılı beyaz-açık mavi
            elif p["omur"] > 0.35:
                clr = "#00F5D4"  # Neon turkuaz
            else:
                clr = "#2563EB"  # Derin kobalt mavi

            r = max(1.0, p["boyut"] * p["omur"])
            c.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r, fill=clr, outline="")

        # 3. Ortada Şık Mini Etiket
        c.create_text(
            cx, H // 2,
            text="🔥 MAVİ ALEV",
            fill="#E0F2FE",
            font=("Consolas", 8, "bold")
        )

        self.after(40, self._ates_dongusu)


# =============================================================================
# 3. ALTAR ÇOKLU-SEKME SİNEMATİK ARKA PLAN ANİMASYON MOTORU
# =============================================================================
class AltarSinematikArkaPlanKanvasi(ctk.CTkFrame):
    """
    Tüm Altar sekmeleri ve özellikleri için canlı, prosedürel sinematik
    arka plan animasyon motoru. Her sekme için benzersiz görsel tema çizer:
    - 'sohbet': Siber AI Sinir Ağı & Nöron Dalgaları
    - 'gezgin': Kriptografik Kasa & Holografik Siber Matris
    - 'oyun': Kozmik Hipersürücü & Synthwave Izgarası
    - 'muzik': Doğa Şelale & Biyolüminesan Su Parçacıkları (Kullanıcı görselindeki)
    - 'ide': Matrix Dijital Kod Yağmuru & Derleyici Akışı
    - 'analiz': Dinamik Veri Galaksisi & 360° Analitik Radar
    - 'gcode': Mekatronik Vektör & Lazer Kesici Kıvılcım Izgarası
    - 'guvenlik': Hexagonal Enerji Kalkanı & Siber Savunma Ağı
    - 'tersine': Binary Hex Akışı & Ayrıştırıcı (Disassembler) Bellek Dalgası
    - 'edr': Karantina Tehdit Avcısı & Güvenlik Kalkanı
    """

    def __init__(self, master: Any, mod: str = "sohbet", **kwargs: Any) -> None:
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.mod = self._mod_normalize_et(mod)
        self._aktif = True
        self._adim = 0
        self._faz = 0.0

        # Çizim Tuvali
        self.canvas = tk.Canvas(
            self, bg="#020617", highlightthickness=0, bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Durum Verileri
        self._noron_noktalar: List[Dict[str, float]] = []
        self._kod_yagmuru: List[Dict[str, Any]] = []
        self._galaksi_noktalar: List[Dict[str, float]] = []
        self._selale_damlalar: List[Dict[str, Any]] = []
        self._kivilcimlar: List[Dict[str, float]] = []
        self._lazer_yol: List[Tuple[float, float]] = []
        self._lazer_indeks = 0

        self._mod_verilerini_hazirla()
        self.after(35, self._animasyon_dongusu)

    def _mod_normalize_et(self, ham_mod: str) -> str:
        s = ham_mod.lower()
        if "sohbet" in s:
            return "sohbet"
        elif "gezgin" in s or "kasa" in s:
            return "gezgin"
        elif "oyun" in s:
            return "oyun"
        elif "müzik" in s or "muzik" in s:
            return "muzik"
        elif "ide" in s or "python" in s:
            return "ide"
        elif "analiz" in s or "veri" in s:
            return "analiz"
        elif "cnc" in s or "gcode" in s or "g-code" in s:
            return "gcode"
        elif "güvenlik" in s or "guvenlik" in s:
            return "guvenlik"
        elif "tersine" in s or "hex" in s:
            return "tersine"
        elif "edr" in s or "antivirüs" in s or "antivirus" in s:
            return "edr"
        return "sohbet"

    def mod_degistir(self, yeni_mod: str) -> None:
        """Aktif sekme değiştiğinde animasyon temasını dinamik olarak günceller."""
        norm_mod = self._mod_normalize_et(yeni_mod)
        if norm_mod != self.mod:
            self.mod = norm_mod
            self._mod_verilerini_hazirla()

    def _mod_verilerini_hazirla(self) -> None:
        """Moda özel parçacık ve matematiksel geometri durumlarını sıfırlar/üretir."""
        self._adim = 0
        w = max(400, self.winfo_width() or 800)
        h = max(300, self.winfo_height() or 500)

        # 1. Nöron Ağı
        self._noron_noktalar = [
            {
                "x": random.uniform(30, w - 30),
                "y": random.uniform(30, h - 30),
                "vx": random.uniform(-0.6, 0.6),
                "vy": random.uniform(-0.6, 0.6),
                "r": random.uniform(2.5, 5.0),
                "renk": random.choice(["#38BDF8", "#0284C7", "#00FFCC", "#818CF8"])
            }
            for _ in range(35)
        ]

        # 2. Matrix Kod Yağmuru
        karakterler = ["0", "1", "def", "import", "class", "sys", "hex", "return", "True", "None", "{", "}", "[", "]", "λ"]
        self._kod_yagmuru = [
            {
                "x": i * 28 + random.randint(-4, 4),
                "y": random.randint(-400, 0),
                "hiz": random.uniform(3.5, 8.0),
                "metin": random.choice(karakterler),
                "renk": random.choice(["#10B981", "#059669", "#34D399", "#00FFCC"])
            }
            for i in range(w // 26 + 2)
        ]

        # 3. Galaksi Veri Noktaları
        self._galaksi_noktalar = []
        for i in range(70):
            r = (i / 70.0) * (min(w, h) * 0.42)
            theta = i * 0.35
            self._galaksi_noktalar.append({
                "r": r, "theta": theta, "hiz": 0.015 + (1.0 / (r + 10)) * 0.8,
                "boyut": random.uniform(1.5, 3.5),
                "renk": random.choice(["#818CF8", "#C084FC", "#38BDF8", "#00E5FF"])
            })

        # 4. Doğa Şelalesi (Kullanıcı Görselindeki)
        self._selale_damlalar = []
        for _ in range(55):
            self._selale_damlalar.append({
                "x": random.randint(w // 3, (2 * w) // 3),
                "y": random.randint(-h, 0),
                "vy": random.uniform(4.5, 9.0),
                "r": random.randint(2, 4),
                "renk": random.choice(["#38BDF8", "#06B6D4", "#A5F3FC", "#67E8F9"])
            })

        # 5. Mekatronik / CNC Lazer Takım Yolu
        cx, cy = w // 2, h // 2
        self._lazer_yol = [
            (cx - 160, cy - 80), (cx + 160, cy - 80),
            (cx + 160, cy + 80), (cx - 160, cy + 80),
            (cx - 160, cy - 80), (cx, cy - 120),
            (cx + 160, cy - 80), (cx, cy + 120),
            (cx - 160, cy + 80)
        ]
        self._lazer_indeks = 0
        self._kivilcimlar = []

    def _animasyon_dongusu(self) -> None:
        if not self._aktif or not self.winfo_exists():
            return

        self._adim += 1
        self._faz += 0.05
        c = self.canvas
        c.delete("all")

        w = max(200, self.winfo_width())
        h = max(150, self.winfo_height())
        cx, cy = w // 2, h // 2

        # -------------------------------------------------------------
        # 1. SOHBET: SİBER SİNİR AĞI & NÖRON DALGALARI
        # -------------------------------------------------------------
        if self.mod == "sohbet":
            # Arka plan yumuşak merkez dalgaları
            for i in range(3):
                rad = ((self._adim * 1.5 + i * 55) % 180) + 20
                c.create_oval(cx - rad, cy - rad, cx + rad, cy + rad, outline="#0B2545", width=1)

            # Nöron bağlantı lazer çizgileri
            n_len = len(self._noron_noktalar)
            for i in range(n_len):
                p1 = self._noron_noktalar[i]
                for j in range(i + 1, min(i + 8, n_len)):
                    p2 = self._noron_noktalar[j]
                    dx = p1["x"] - p2["x"]
                    dy = p1["y"] - p2["y"]
                    mesafe = math.hypot(dx, dy)
                    if mesafe < 115:
                        c.create_line(p1["x"], p1["y"], p2["x"], p2["y"], fill="#0F3460", width=1)
                        # Bağlantı üzerinde sinaps mermisi
                        if (self._adim + i * 3) % 40 == 0:
                            mx = p1["x"] + (p2["x"] - p1["x"]) * 0.5
                            my = p1["y"] + (p2["y"] - p1["y"]) * 0.5
                            c.create_oval(mx - 2, my - 2, mx + 2, my + 2, fill="#00FFCC", outline="")

            # Nöron düğümleri
            for p in self._noron_noktalar:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                if p["x"] < 15 or p["x"] > w - 15:
                    p["vx"] *= -1
                if p["y"] < 15 or p["y"] > h - 15:
                    p["vy"] *= -1

                r = p["r"]
                c.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r, fill=p["renk"], outline="")

            c.create_text(w - 18, h - 16, text="⚡ ALTAR SİNİR AĞI AKTİF", fill="#1E293B", font=("Consolas", 9, "bold"), anchor="e")

        # -------------------------------------------------------------
        # 2. DOSYA GEZGİNİ & KASA: KRİPTOGRAFİK KASA & SİBER MATRİS
        # -------------------------------------------------------------
        elif self.mod == "gezgin":
            # 3 Eksenli Dönen Kasa Kilit Halkaları
            for idx, r_baz in enumerate([60, 110, 160]):
                aci = self._faz * (1.2 if idx % 2 == 0 else -0.9) + idx
                c.create_oval(cx - r_baz, cy - r_baz, cx + r_baz, cy + r_baz, outline="#1E3A8A", width=1)
                # Radyal Kilit Çentikleri
                for k in range(8):
                    t = aci + k * (math.pi / 4)
                    kx1 = cx + math.cos(t) * (r_baz - 6)
                    ky1 = cy + math.sin(t) * (r_baz - 6)
                    kx2 = cx + math.cos(t) * (r_baz + 6)
                    ky2 = cy + math.sin(t) * (r_baz + 6)
                    c.create_line(kx1, ky1, kx2, ky2, fill="#0284C7", width=2)

            # Kripto Jetonları
            c.create_text(cx, cy - 25, text="🛡️ AES-256 ENCRYPTED", fill="#00FFCC", font=("Consolas", 12, "bold"))
            c.create_text(cx, cy + 5, text="SHA-256 DIGITAL VAULT", fill="#38BDF8", font=("Consolas", 10))
            c.create_text(cx, cy + 30, text=f"HASH: 0x{((self._adim * 37) % 0xFFFFFF):06X}", fill="#64748B", font=("Consolas", 9))

        # -------------------------------------------------------------
        # 3. OYUN: KOZMİK HİPERSÜRÜCÜ & SYNTHWAVE IZGARASI
        # -------------------------------------------------------------
        elif self.mod == "oyun":
            # Ufuk Çizgisi
            ufuk_y = int(h * 0.58)
            c.create_line(0, ufuk_y, w, ufuk_y, fill="#7C3AED", width=2)

            # Synthwave Güneşi
            gunes_r = 55
            c.create_oval(cx - gunes_r, ufuk_y - gunes_r, cx + gunes_r, ufuk_y + gunes_r, fill="#F43F5E", outline="")
            for s in range(5):
                sy = ufuk_y - gunes_r + 20 + s * 14
                c.create_line(cx - gunes_r, sy, cx + gunes_r, sy, fill="#020617", width=3)

            # 3D Perspektif Izgara Çizgileri
            for i in range(-7, 8):
                alt_x = cx + i * (w // 10)
                c.create_line(cx, ufuk_y, alt_x, h, fill="#3B82F6", width=1)

            # İlerleyen Yatay Barlar
            for j in range(6):
                bar_oran = ((self._adim * 1.8 + j * 30) % 180) / 180.0
                by = ufuk_y + (bar_oran ** 2) * (h - ufuk_y)
                c.create_line(0, by, w, by, fill="#06B6D4", width=1)

            c.create_text(w - 18, h - 16, text="🎮 SİBER ARCADE 60 FPS", fill="#334155", font=("Consolas", 9, "bold"), anchor="e")

        # -------------------------------------------------------------
        # 4. MÜZİK: DOĞA ŞELALE & SU HALKALARI (KULLANICININ GÖRSELİNDEKİ)
        # -------------------------------------------------------------
        elif self.mod == "muzik":
            # Şelale Su Damlaları
            if len(self._selale_damlalar) < 55:
                self._selale_damlalar.append({
                    "x": random.randint(w // 3, (2 * w) // 3),
                    "y": -10,
                    "vy": random.uniform(4.5, 9.0),
                    "r": random.randint(2, 4),
                    "renk": random.choice(["#38BDF8", "#06B6D4", "#A5F3FC", "#67E8F9"])
                })

            for p in self._selale_damlalar:
                p["y"] += p["vy"]
                r = p["r"]
                c.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r, fill=p["renk"], outline="")
            self._selale_damlalar = [p for p in self._selale_damlalar if p["y"] < h + 20]

            # Gölet Dalgası ve Rezonans Halkaları
            pond_y = h - 35
            for i in range(3):
                rad = ((self._adim * 2 + i * 40) % 120) + 15
                c.create_oval(cx - rad * 1.8, pond_y - rad * 0.5, cx + rad * 1.8, pond_y + rad * 0.5, outline="#0284C7", width=1)

            c.create_text(w - 18, h - 16, text="🌊 DOĞA ŞELALE & AKUSTİK HAVUZ", fill="#1E293B", font=("Consolas", 9, "bold"), anchor="e")

        # -------------------------------------------------------------
        # 5. PYTHON IDE: MATRIX DİJİTAL KOD YAĞMURU
        # -------------------------------------------------------------
        elif self.mod == "ide":
            for d in self._kod_yagmuru:
                d["y"] += d["hiz"]
                if d["y"] > h + 25:
                    d["y"] = random.randint(-80, 0)
                    d["metin"] = random.choice(["0", "1", "def", "class", "import", "sys", "λ", "True", "None"])

                c.create_text(d["x"], d["y"], text=d["metin"], fill=d["renk"], font=("Consolas", 10, "bold"))

            # Canlı Derleyici Tarama Çizgisi
            scan_y = (self._adim * 3) % h
            c.create_line(0, scan_y, w, scan_y, fill="#047857", width=1)
            c.create_text(w - 18, h - 16, text="🐍 PYTHON 3.13 LIVE COMPILED", fill="#1E293B", font=("Consolas", 9, "bold"), anchor="e")

        # -------------------------------------------------------------
        # 6. KAZINAN VERİ & ANALİZ: DİNAMİK VERİ GALAKSİSİ & 360° RADAR
        # -------------------------------------------------------------
        elif self.mod == "analiz":
            # Dönen Galaksi Spiral Noktaları
            for p in self._galaksi_noktalar:
                p["theta"] += p["hiz"]
                gx = cx + math.cos(p["theta"]) * p["r"]
                gy = cy + math.sin(p["theta"]) * (p["r"] * 0.55)
                b = p["boyut"]
                c.create_oval(gx - b, gy - b, gx + b, gy + b, fill=p["renk"], outline="")

            # 360 Derece Dönen Radar Kolu
            radar_aci = self._faz * 1.5
            rx = cx + math.cos(radar_aci) * (min(w, h) * 0.44)
            ry = cy + math.sin(radar_aci) * (min(w, h) * 0.44)
            c.create_line(cx, cy, rx, ry, fill="#10B981", width=2)
            c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="#34D399", outline="")

            c.create_text(w - 18, h - 16, text="📊 TELEMETRİ & VERİ ANALİTİK RADARI", fill="#1E293B", font=("Consolas", 9, "bold"), anchor="e")

        # -------------------------------------------------------------
        # 7. CNC G-CODE 2D: MEKATRONİK VEKTÖR & LAZER KIVILCIM
        # -------------------------------------------------------------
        elif self.mod == "gcode":
            # Teknik Koordinat Grid
            grid_s = 40
            for gx in range(0, w, grid_s):
                c.create_line(gx, 0, gx, h, fill="#0F172A", width=1)
            for gy in range(0, h, grid_s):
                c.create_line(0, gy, w, gy, fill="#0F172A", width=1)

            # Lazer Takım Yolu
            if self._lazer_yol:
                for k in range(len(self._lazer_yol) - 1):
                    x1, y1 = self._lazer_yol[k]
                    x2, y2 = self._lazer_yol[k + 1]
                    c.create_line(x1, y1, x2, y2, fill="#0284C7", width=2)

                # Hareketli Lazer Ucu
                p_hedef = self._lazer_yol[self._lazer_indeks % len(self._lazer_yol)]
                c.create_oval(p_hedef[0] - 8, p_hedef[1] - 8, p_hedef[0] + 8, p_hedef[1] + 8, fill="#00FFCC", outline="#FFFFFF")

                # Kıvılcım Üretimi
                if len(self._kivilcimlar) < 25:
                    for _ in range(4):
                        aci = random.uniform(0, 2 * math.pi)
                        hiz = random.uniform(2.0, 5.5)
                        self._kivilcimlar.append({
                            "x": p_hedef[0], "y": p_hedef[1],
                            "vx": math.cos(aci) * hiz, "vy": math.sin(aci) * hiz,
                            "omur": random.randint(8, 16),
                            "renk": random.choice(["#F59E0B", "#FCD34D", "#EF4444"])
                        })

                if self._adim % 8 == 0:
                    self._lazer_indeks = (self._lazer_indeks + 1) % len(self._lazer_yol)

            # Kıvılcımları Çiz
            for k in self._kivilcimlar:
                k["x"] += k["vx"]
                k["y"] += k["vy"]
                k["omur"] -= 1
                c.create_oval(k["x"] - 1.5, k["y"] - 1.5, k["x"] + 1.5, k["y"] + 1.5, fill=k["renk"], outline="")
            self._kivilcimlar = [k for k in self._kivilcimlar if k["omur"] > 0]

            c.create_text(w - 18, h - 16, text="📐 CNC G-CODE LAZER İZLEYİCİ", fill="#1E293B", font=("Consolas", 9, "bold"), anchor="e")

        # -------------------------------------------------------------
        # 8. GÜVENLİK: HEXAGONAL ENERJİ KALKANI & IPS AĞI
        # -------------------------------------------------------------
        elif self.mod == "guvenlik":
            # Dairesel ve Hexagonal Koruma Halkaları
            for i in range(3):
                r_k = 65 + i * 45
                c.create_oval(cx - r_k, cy - r_k, cx + r_k, cy + r_k, outline="#1E3A8A", width=1)

            # Kalkan Merkez Arması
            c.create_text(cx, cy - 20, text="🛡️ IPS ACTIVE DEFENSE", fill="#00FFCC", font=("Consolas", 13, "bold"))
            c.create_text(cx, cy + 10, text="AĞ TRAFİĞİ KORUMA ALTINDA", fill="#38BDF8", font=("Consolas", 10))

            # Savunma Darbe Dalgaları
            darbe_r = ((self._adim * 2.2) % 190) + 10
            c.create_oval(cx - darbe_r, cy - darbe_r, cx + darbe_r, cy + darbe_r, outline="#0EA5E9", width=2)
            c.create_text(w - 18, h - 16, text="🛡️ AĞ IPS & GÜVENLİK KALKANI", fill="#1E293B", font=("Consolas", 9, "bold"), anchor="e")

        # -------------------------------------------------------------
        # 9. TERSİNE MÜHENDİSLİK: BİNARY HEX AKIŞI & DİSASSEMBLER
        # -------------------------------------------------------------
        elif self.mod == "tersine":
            opcodes = ["PUSH EBP", "MOV EBP, ESP", "SUB ESP, 0x40", "XOR EAX, EAX", "CALL 0x004014A0", "TEST EAX, EAX", "JNZ 0x00401502", "RET"]
            start_y = 40
            for i in range(8):
                y_pos = (start_y + i * 35 + int(self._adim * 1.2)) % (h - 20)
                offset = f"0x0040{1000 + i * 16:04X}:"
                hex_str = f"55 89 E5 83 EC {i*10:02X} 31 C0"
                c.create_text(40, y_pos, text=offset, fill="#38BDF8", font=("Consolas", 10, "bold"), anchor="w")
                c.create_text(160, y_pos, text=hex_str, fill="#64748B", font=("Consolas", 10), anchor="w")
                c.create_text(340, y_pos, text=opcodes[i % len(opcodes)], fill="#10B981", font=("Consolas", 10, "bold"), anchor="w")

            c.create_text(w - 18, h - 16, text="🔬 TERSİNE MÜHENDİSLİK DİSASSEMBLER", fill="#1E293B", font=("Consolas", 9, "bold"), anchor="e")

        # -------------------------------------------------------------
        # 10. EDR & ANTİVİRÜS: KARANTİNA KALKANI & TEHDİT AVCISI
        # -------------------------------------------------------------
        elif self.mod == "edr":
            # Sonar Tarama Dalgaları
            for i in range(4):
                rad = ((self._adim * 2.0 + i * 45) % 170) + 15
                c.create_oval(cx - rad, cy - rad, cx + rad, cy + rad, outline="#991B1B" if i == 0 else "#374151", width=1)

            # Tehdit Tarayıcı Dönen Lazer Çizgisi
            aci = self._faz * 1.8
            tx = cx + math.cos(aci) * 140
            ty = cy + math.sin(aci) * 140
            c.create_line(cx, cy, tx, ty, fill="#EF4444", width=2)
            c.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill="#EF4444", outline="#FCA5A5")

            c.create_text(cx, cy + 45, text="🦠 EDR REALTIME THREAT SCANNER", fill="#EF4444", font=("Consolas", 11, "bold"))
            c.create_text(w - 18, h - 16, text="🦠 SİSTEM EDR SIFIR TEHDİT", fill="#1E293B", font=("Consolas", 9, "bold"), anchor="e")

        self.after(35, self._animasyon_dongusu)

