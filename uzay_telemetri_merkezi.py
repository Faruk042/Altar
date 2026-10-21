import os
import sys
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

import csv
import math
import struct
import wave
import io
import time
import array
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

# =========================================================
# NASA YÖRÜNGE KONSEPTİ RENK PALETİ
# =========================================================
BG_COLOR = "#050A1F"
PANEL_COLOR = "#0D1B2A"
GRID_COLOR = "#1B263B"
TEXT_COLOR = "#778DA9"
HIGHLIGHT_COLOR = "#00FFCC"
BTN_COLOR = "#00A86B"
BTN_HOVER = "#007F50"
LINE1_COLOR = "#FF007F"   # Ana Eksen (Pembe/Kırmızı)
LINE2_COLOR = "#00BFFF"   # İkincil Eksen (Siber Mavi)
TREND_COLOR = "#FFD700"   # Hareketli Ortalama (Altın Sarısı)


class UzayTelemetriMerkezi(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("🛰️ Altar - Uzay Telemetri, Küresel Alev ve Sonifikasyon Merkezi (%100 Salt-Okunur)")
        self.geometry("1280x800")
        self.configure(fg_color=BG_COLOR)
        self._tam_ekran_mi = True
        self.after(20, self._tam_ekran_yap)
        self.bind("<F11>", self._tam_ekran_degistir)
        self.bind("<Escape>", self._tam_ekrandan_cik)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Bellek-İçi Veri Yapıları (Diske hiçbir şey yazılmaz)
        self.dosya_adi = "Veri Yüklenmedi"
        self.sutunlar = []
        self.veri_sozlugu = {}  # {sutun_adi: [float_degerler]}
        self.ham_satirlar = []
        self.cizim_noktalari_y1 = []
        self.cizim_noktalari_y2 = []

        # Simülasyon, Ses ve Performans Bayrakları
        self.alev_sim_calisiyor = False
        self.ses_calisiyor = False
        self.su_sisi_aktif = False
        self._resize_timer = None
        self._son_hover_zamani = 0.0

        self._arayuz_olustur()

    def _arayuz_olustur(self):
        # ÜST KONTROL PANELİ
        self.top_bar = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=10, border_width=1, border_color=GRID_COLOR)
        self.top_bar.pack(side="top", fill="x", padx=15, pady=(12, 6))

        baslik_kutu = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        baslik_kutu.pack(side="left", padx=15, pady=8)

        ctk.CTkLabel(
            baslik_kutu,
            text="🌌 NASA MİKRO YERÇEKİMİ TELEMETRİ & FİZİK LABORATUVARI",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color=HIGHLIGHT_COLOR
        ).pack(anchor="w")

        self.lbl_dosya_durum = ctk.CTkLabel(
            baslik_kutu,
            text="🔒 Güvenlik Kalkanı: %100 Salt-Okunur (RAM İçi Çalışma) | Aktif Veri: Yok",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=TEXT_COLOR
        )
        self.lbl_dosya_durum.pack(anchor="w")

        sag_kutu = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        sag_kutu.pack(side="right", padx=15, pady=8)

        self.btn_yukle = ctk.CTkButton(
            sag_kutu, text="📂 CSV / Telemetri Verisi Oku (Salt-Okunur)",
            fg_color="#1f538d", hover_color="#14375e", width=260, command=self.csv_salt_okunur_yukle
        )
        self.btn_yukle.pack(side="left", padx=8)

        self.btn_ornek_veri = ctk.CTkButton(
            sag_kutu, text="🧪 RAM'de Örnek NASA Verisi Oluştur",
            fg_color="#6A0dad", hover_color="#4B0082", width=230, command=self.ramde_ornek_veri_uret
        )
        self.btn_ornek_veri.pack(side="left", padx=8)

        self.btn_tam_ekran = ctk.CTkButton(
            sag_kutu, text="🗗 Tam Ekran (F11)",
            fg_color="#1E293B", hover_color="#334155", width=120, command=self._tam_ekran_degistir
        )
        self.btn_tam_ekran.pack(side="left", padx=4)

        self.btn_kapat = ctk.CTkButton(
            sag_kutu, text="✕ Kapat",
            fg_color="#dc2626", hover_color="#991b1b", width=75, font=ctk.CTkFont(size=11, weight="bold"),
            command=self.on_closing
        )
        self.btn_kapat.pack(side="left", padx=(4, 0))

        # SEKMELİ ANA ÇALIŞMA ALANI
        self.tabview = ctk.CTkTabview(self, corner_radius=10, fg_color=PANEL_COLOR)
        self.tabview.pack(side="top", fill="both", expand=True, padx=15, pady=(4, 15))

        self.tab_radar = self.tabview.add("📈 1. Çift Eksenli Korelasyon & Anomali Radarı")
        self.tab_alev = self.tabview.add("🔥 2. Küresel Alev & İs (Soot) Simülatörü")
        self.tab_ses = self.tabview.add("🔊 3. Veri Seslendirme (Sonification) & Osiloskop")

        self._sekme_radar_hazirla()
        self._sekme_alev_hazirla()
        self._sekme_ses_hazirla()

    # =========================================================================
    # VERİ OKUMA (SALT-OKUNUR) VE RAM-İÇİ TEST VERİSİ
    # =========================================================================
    def csv_salt_okunur_yukle(self):
        dosya_yolu = filedialog.askopenfilename(
            parent=self,
            title="Salt-Okunur Telemetri CSV Dosyası Seçin",
            filetypes=[("CSV Veri Dosyaları", "*.csv"), ("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
        )
        if not dosya_yolu:
            return

        def _csv_oku_worker():
            try:
                with open(dosya_yolu, "r", encoding="utf-8", errors="replace") as f:
                    okuyucu = list(csv.reader(f))

                if len(okuyucu) < 2:
                    self.after(0, lambda: messagebox.showwarning("Uyarı", "Dosyada yeterli veri satırı bulunamadı.", parent=self))
                    return

                basliklar = [b.strip() or f"Sutun_{i+1}" for i, b in enumerate(okuyucu[0])]
                gecici_sozluk = {b: [] for b in basliklar}

                for satir in okuyucu[1:]:
                    if not satir or len(satir) < len(basliklar):
                        continue
                    for i, b in enumerate(basliklar):
                        try:
                            gecici_sozluk[b].append(float(satir[i]))
                        except ValueError:
                            pass

                sayisal_sutunlar = [b for b, d in gecici_sozluk.items() if len(d) >= 2]
                if not sayisal_sutunlar:
                    self.after(0, lambda: messagebox.showwarning("Uyarı", "Dosyada sayısal veri içeren sütun bulunamadı.", parent=self))
                    return

                self.sutunlar = sayisal_sutunlar
                self.veri_sozlugu = {b: gecici_sozluk[b] for b in sayisal_sutunlar}
                self.dosya_adi = os.path.basename(dosya_yolu)

                def _tamamla():
                    self._menuleri_guncelle()
                    messagebox.showinfo(
                        "Salt-Okunur Yükleme Başarılı",
                        f"'{self.dosya_adi}' dosyasından {len(sayisal_sutunlar)} sayısal sütun RAM'e aktarıldı.\nHiçbir dosya değiştirilmedi.",
                        parent=self
                    )

                self.after(0, _tamamla)
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("Okuma Hatası", f"Dosya okunurken hata oluştu:\n{err}", parent=self))

        threading.Thread(target=_csv_oku_worker, daemon=True).start()

    def ramde_ornek_veri_uret(self):
        """Diske hiçbir şey yazmadan doğrudan RAM'de 60 saniyelik mikro yerçekimi yanma verisi üretir."""
        zaman, sicaklik, oksijen, co_ppm, risk = [], [], [], [], []
        for t in range(60):
            zaman.append(float(t))
            if t < 15:
                o2 = 21.0 - t * 0.15
                temp = 280.0 + t * 6.5
                co = 15.0 + t * 3.0
            elif 15 <= t < 35:
                o2 = 18.5 - (t - 15) * 0.22
                temp = 380.0 + math.sin(t) * 25.0
                co = 80.0 + (t - 15) * 18.0
            elif 35 <= t < 45:
                o2 = 26.5 + (t - 35) * 0.6
                temp = 490.0 + (t - 35) * 19.0
                co = 220.0 - (t - 35) * 10.0
            else:
                o2 = 20.8
                temp = max(120.0, 620.0 - (t - 45) * 35.0)
                co = max(20.0, 110.0 - (t - 45) * 6.0)

            r_skor = round((temp / 400.0) * (co / 100.0), 2)
            sicaklik.append(round(temp, 2))
            oksijen.append(round(o2, 2))
            co_ppm.append(round(co, 2))
            risk.append(r_skor)

        self.sutunlar = ["Zaman_s", "Sicaklik_C", "Oksijen_Yuzdesi", "CO_Karbonmonoksit_ppm", "Risk_Puanu"]
        self.veri_sozlugu = {
            "Zaman_s": zaman,
            "Sicaklik_C": sicaklik,
            "Oksijen_Yuzdesi": oksijen,
            "CO_Karbonmonoksit_ppm": co_ppm,
            "Risk_Puanu": risk
        }
        self.dosya_adi = "RAM_Simule_Mikroyercekimi_Deneyi.csv (Bellek-İçi)"
        self._menuleri_guncelle()

    def _menuleri_guncelle(self):
        self.lbl_dosya_durum.configure(
            text=f"🔒 Güvenlik Kalkanı: %100 Salt-Okunur | Aktif Veri: {self.dosya_adi} ({len(self.sutunlar)} Sütun)",
            text_color=HIGHLIGHT_COLOR
        )
        self.combo_x.configure(values=self.sutunlar, state="normal")
        self.combo_y1.configure(values=self.sutunlar, state="normal")
        self.combo_y2.configure(values=["Yok"] + self.sutunlar, state="normal")
        self.combo_ses_sutun.configure(values=self.sutunlar, state="normal")

        self.combo_x.set(self.sutunlar[0])
        self.combo_y1.set(self.sutunlar[1] if len(self.sutunlar) > 1 else self.sutunlar[0])
        self.combo_y2.set(self.sutunlar[2] if len(self.sutunlar) > 2 else "Yok")
        self.combo_ses_sutun.set(self.sutunlar[1] if len(self.sutunlar) > 1 else self.sutunlar[0])

        self.radar_ciz()

    # =========================================================================
    # SEKME 1: ÇİFT EKSENLİ KORELASYON VE Z-SKORU ANOMALİ RADARI
    # =========================================================================
    def _sekme_radar_hazirla(self):
        ust = ctk.CTkFrame(self.tab_radar, fg_color="transparent")
        ust.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(ust, text="X Ekseni:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
        self.combo_x = ctk.CTkOptionMenu(ust, values=["Veri Yok"], width=140, state="disabled", command=lambda _: self.radar_ciz())
        self.combo_x.pack(side="left", padx=4)

        ctk.CTkLabel(ust, text="Y1 (Pembe):", text_color=LINE1_COLOR, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
        self.combo_y1 = ctk.CTkOptionMenu(ust, values=["Veri Yok"], width=150, state="disabled", command=lambda _: self.radar_ciz())
        self.combo_y1.pack(side="left", padx=4)

        ctk.CTkLabel(ust, text="Y2 (Mavi):", text_color=LINE2_COLOR, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
        self.combo_y2 = ctk.CTkOptionMenu(ust, values=["Yok"], width=150, state="disabled", command=lambda _: self.radar_ciz())
        self.combo_y2.pack(side="left", padx=4)

        self.chk_trend_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            ust, text="Hareketli Ortalama (Trend)", variable=self.chk_trend_var,
            text_color=TREND_COLOR, command=self.radar_ciz
        ).pack(side="left", padx=12)

        ctk.CTkButton(
            ust, text="🔄 Yeniden Hesapla & Çiz", fg_color=BTN_COLOR, hover_color=BTN_HOVER,
            width=160, command=self.radar_ciz
        ).pack(side="right", padx=6)

        orta = ctk.CTkFrame(self.tab_radar, fg_color="transparent")
        orta.pack(fill="both", expand=True, padx=10, pady=6)

        self.radar_canvas = tk.Canvas(orta, bg="#050B14", highlightthickness=1, highlightbackground=GRID_COLOR)
        self.radar_canvas.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.radar_canvas.bind("<Configure>", self._radar_boyut_degisti)
        self.radar_canvas.bind("<Motion>", self._radar_hover)

        sag_panel = ctk.CTkFrame(orta, width=290, fg_color="#081221", corner_radius=8, border_width=1, border_color=GRID_COLOR)
        sag_panel.pack(side="right", fill="y")
        sag_panel.pack_propagate(False)

        ctk.CTkLabel(
            sag_panel, text="📊 BİLİMSEL TELEMETRİ RAPORU",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color=HIGHLIGHT_COLOR
        ).pack(pady=(12, 6))

        self.txt_istatistik = ctk.CTkTextbox(
            sag_panel, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#050B14", text_color="#E0E1DD", wrap="word"
        )
        self.txt_istatistik.pack(fill="both", expand=True, padx=8, pady=8)
        self.txt_istatistik.insert("1.0", "Veri yüklendiğinde Pearson Korelasyonu, Z-Skoru Anomalileri ve Standart Sapma burada listelenir.")
        self.txt_istatistik.configure(state="disabled")

    def _radar_boyut_degisti(self, _event=None):
        if self._resize_timer:
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(120, self.radar_ciz)

    def _pearson_korelasyon(self, x_list, y_list) -> float:
        n = min(len(x_list), len(y_list))
        if n < 2:
            return 0.0
        ort_x = sum(x_list[:n]) / n
        ort_y = sum(y_list[:n]) / n
        pay = sum((x_list[i] - ort_x) * (y_list[i] - ort_y) for i in range(n))
        payda_x = math.sqrt(sum((x_list[i] - ort_x) ** 2 for i in range(n)))
        payda_y = math.sqrt(sum((y_list[i] - ort_y) ** 2 for i in range(n)))
        if payda_x == 0 or payda_y == 0:
            return 0.0
        return pay / (payda_x * payda_y)

    def radar_ciz(self):
        if not self.veri_sozlugu:
            return

        x_isim = self.combo_x.get()
        y1_isim = self.combo_y1.get()
        y2_isim = self.combo_y2.get()

        x_veri = self.veri_sozlugu.get(x_isim, [])
        y1_veri = self.veri_sozlugu.get(y1_isim, [])
        y2_veri = self.veri_sozlugu.get(y2_isim, []) if y2_isim != "Yok" else []

        n = min(len(x_veri), len(y1_veri))
        if y2_veri:
            n = min(n, len(y2_veri))
        if n < 2:
            return

        x_veri, y1_veri = x_veri[:n], y1_veri[:n]
        if y2_veri:
            y2_veri = y2_veri[:n]

        self.radar_canvas.delete("all")
        self.cizim_noktalari_y1.clear()
        self.cizim_noktalari_y2.clear()

        w = max(self.radar_canvas.winfo_width(), 650)
        h = max(self.radar_canvas.winfo_height(), 450)
        kb = 70

        min_x, max_x = min(x_veri), max(x_veri)
        span_x = max(max_x - min_x, 1e-5)
        x_olcek = (w - 2 * kb) / span_x

        min_y1, max_y1 = min(y1_veri), max(y1_veri)
        span_y1 = max(max_y1 - min_y1, 1e-5)
        y1_olcek = (h - 2 * kb) / span_y1

        ort_y1 = sum(y1_veri) / n
        std_y1 = math.sqrt(sum((v - ort_y1) ** 2 for v in y1_veri) / n) or 1e-5

        # Izgara ve Eksenler
        for i in range(11):
            py = kb + i * ((h - 2 * kb) / 10)
            deger_y1 = max_y1 - (i / 10) * span_y1
            self.radar_canvas.create_line(kb, py, w - kb, py, fill=GRID_COLOR, dash=(2, 4))
            self.radar_canvas.create_text(kb - 8, py, text=f"{deger_y1:.1f}", fill=LINE1_COLOR, font=("Consolas", 9), anchor="e")

            px = kb + i * ((w - 2 * kb) / 10)
            deger_x = min_x + (i / 10) * span_x
            self.radar_canvas.create_line(px, kb, px, h - kb, fill=GRID_COLOR, dash=(2, 4))
            self.radar_canvas.create_text(px, h - kb + 16, text=f"{deger_x:.1f}", fill=TEXT_COLOR, font=("Consolas", 9))

        self.radar_canvas.create_line(kb, h - kb, w - kb, h - kb, fill=TEXT_COLOR, width=2)
        self.radar_canvas.create_line(kb, kb, kb, h - kb, fill=LINE1_COLOR, width=2)

        # Y1 Çizimi ve Z-Skoru Anomali Tespiti (|Z| >= 1.9)
        anomali_sayisi = 0
        y1_cizgi_koordinatlari = []
        for i in range(n):
            px = kb + (x_veri[i] - min_x) * x_olcek
            py1 = h - kb - (y1_veri[i] - min_y1) * y1_olcek
            z_skor = abs(y1_veri[i] - ort_y1) / std_y1
            self.cizim_noktalari_y1.append((px, py1, x_veri[i], y1_veri[i], y1_isim, LINE1_COLOR, z_skor))
            y1_cizgi_koordinatlari.extend((px, py1))

            if z_skor >= 1.9:
                anomali_sayisi += 1
                self.radar_canvas.create_oval(px - 10, py1 - 10, px + 10, py1 + 10, outline="#FF2222", width=2)
                self.radar_canvas.create_text(px, py1 - 16, text="⚠️", fill="#FF2222", font=("Consolas", 9))

        if len(y1_cizgi_koordinatlari) >= 4:
            self.radar_canvas.create_line(*y1_cizgi_koordinatlari, fill=LINE1_COLOR, width=2.5, smooth=True)

        # Hareketli Ortalama (Window = 5)
        if self.chk_trend_var.get() and n >= 5:
            trend_koordinatlari = []
            for i in range(n):
                dilim = y1_veri[max(0, i - 2):min(n, i + 3)]
                t_val = sum(dilim) / len(dilim)
                px = kb + (x_veri[i] - min_x) * x_olcek
                py_t = h - kb - (t_val - min_y1) * y1_olcek
                trend_koordinatlari.extend((px, py_t))
            if len(trend_koordinatlari) >= 4:
                self.radar_canvas.create_line(*trend_koordinatlari, fill=TREND_COLOR, width=1.8, dash=(5, 3))

        # Y2 Çizimi
        korelasyon_metni = "Seçilmedi"
        if y2_veri:
            min_y2, max_y2 = min(y2_veri), max(y2_veri)
            span_y2 = max(max_y2 - min_y2, 1e-5)
            y2_olcek = (h - 2 * kb) / span_y2
            self.radar_canvas.create_line(w - kb, kb, w - kb, h - kb, fill=LINE2_COLOR, width=2)

            for i in range(11):
                py = kb + i * ((h - 2 * kb) / 10)
                deger_y2 = max_y2 - (i / 10) * span_y2
                self.radar_canvas.create_text(w - kb + 8, py, text=f"{deger_y2:.1f}", fill=LINE2_COLOR, font=("Consolas", 9), anchor="w")

            y2_cizgi_koordinatlari = []
            for i in range(n):
                px = kb + (x_veri[i] - min_x) * x_olcek
                py2 = h - kb - (y2_veri[i] - min_y2) * y2_olcek
                self.cizim_noktalari_y2.append((px, py2, x_veri[i], y2_veri[i], y2_isim, LINE2_COLOR, 0.0))
                y2_cizgi_koordinatlari.extend((px, py2))

            if len(y2_cizgi_koordinatlari) >= 4:
                self.radar_canvas.create_line(*y2_cizgi_koordinatlari, fill=LINE2_COLOR, width=2.5, smooth=True)

            r_degeri = self._pearson_korelasyon(y1_veri, y2_veri)
            yorum = "Güçlü Doğru Orantı" if r_degeri > 0.6 else ("Güçlü Ters Orantı" if r_degeri < -0.6 else "Zayıf/Orta İlişki")
            korelasyon_metni = f"r = {r_degeri:.3f}\n({yorum})"

        rapor = (
            f"📌 AKTİF VERİ SETİ:\n{self.dosya_adi}\n"
            f"Toplam Veri Noktası: {n}\n"
            f"{'='*30}\n"
            f"🔴 ANA EKSEN ({y1_isim}):\n"
            f"  • Min      : {min_y1:.2f}\n"
            f"  • Max      : {max_y1:.2f}\n"
            f"  • Ortalama : {ort_y1:.2f}\n"
            f"  • Std Sapma: {std_y1:.2f}\n"
            f"  • Z-Anomali: {anomali_sayisi} Nokta (|Z|>=1.9)\n"
            f"{'='*30}\n"
        )
        if y2_veri:
            ort_y2 = sum(y2_veri) / n
            rapor += (
                f"🔵 İKİNCİL EKSEN ({y2_isim}):\n"
                f"  • Min      : {min(y2_veri):.2f}\n"
                f"  • Max      : {max(y2_veri):.2f}\n"
                f"  • Ortalama : {ort_y2:.2f}\n"
                f"{'='*30}\n"
                f"🔗 PEARSON KORELASYONU:\n  {korelasyon_metni}\n"
            )

        self.txt_istatistik.configure(state="normal")
        self.txt_istatistik.delete("1.0", "end")
        self.txt_istatistik.insert("1.0", rapor)
        self.txt_istatistik.configure(state="disabled")

    def _radar_hover(self, event):
        simdi = time.perf_counter()
        if simdi - self._son_hover_zamani < 0.016:  # 60 FPS sınırı (Gereksiz CPU kullanımını önler)
            return
        self._son_hover_zamani = simdi

        self.radar_canvas.delete("hover_tag")
        fx, fy = event.x, event.y
        w = self.radar_canvas.winfo_width()
        h = self.radar_canvas.winfo_height()

        self.radar_canvas.create_line(fx, 50, fx, h - 50, fill="#334155", dash=(2, 2), tags="hover_tag")
        self.radar_canvas.create_line(50, fy, w - 50, fy, fill="#334155", dash=(2, 2), tags="hover_tag")

        en_yakin = None
        min_m = 18.0
        for nokta in (self.cizim_noktalari_y1 + self.cizim_noktalari_y2):
            m = math.hypot(nokta[0] - fx, nokta[1] - fy)
            if m < min_m:
                min_m = m
                en_yakin = nokta

        if en_yakin:
            px, py, gx, gy, isim, renk, z_skor = en_yakin
            self.radar_canvas.create_oval(px - 7, py - 7, px + 7, py + 7, outline="#FFFFFF", width=2, tags="hover_tag")
            metin = f"[{isim}]\nX: {gx:.2f} | Y: {gy:.2f}\nZ-Skoru: {z_skor:.2f}"
            kx = px + 14 if px < w - 180 else px - 170
            ky = py - 50 if py > 70 else py + 15
            self.radar_canvas.create_rectangle(kx, ky, kx + 160, ky + 52, fill="#0D1B2A", outline=renk, width=2, tags="hover_tag")
            self.radar_canvas.create_text(kx + 80, ky + 26, text=metin, fill="#FFFFFF", font=("Consolas", 9, "bold"), tags="hover_tag")

    # =========================================================================
    # SEKME 2: 2D MİKRO YERÇEKİMİ KÜRESEL ALEV & İS (SOOT) SİMÜLATÖRÜ
    # =========================================================================
    def _sekme_alev_hazirla(self):
        sol = ctk.CTkFrame(self.tab_alev, width=340, fg_color="#081221", corner_radius=10)
        sol.pack(side="left", fill="y", padx=10, pady=10)
        sol.pack_propagate(False)

        ctk.CTkLabel(
            sol, text="🔥 KÜRESEL ALEV PARAMETRELERİ",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"), text_color=HIGHLIGHT_COLOR
        ).pack(pady=(15, 10))

        self.lbl_sicaklik_val = ctk.CTkLabel(sol, text="Sıcaklık: 350 °C", font=ctk.CTkFont(family="Consolas", size=12))
        self.lbl_sicaklik_val.pack(anchor="w", padx=20)
        self.slider_sicaklik = ctk.CTkSlider(sol, from_=100, to=750, command=self._manuel_alev_guncelle)
        self.slider_sicaklik.set(350)
        self.slider_sicaklik.pack(fill="x", padx=20, pady=(2, 12))

        self.lbl_o2_val = ctk.CTkLabel(sol, text="Oksijen (O2): %21.0", font=ctk.CTkFont(family="Consolas", size=12))
        self.lbl_o2_val.pack(anchor="w", padx=20)
        self.slider_o2 = ctk.CTkSlider(sol, from_=10.0, to=35.0, command=self._manuel_alev_guncelle)
        self.slider_o2.set(21.0)
        self.slider_o2.pack(fill="x", padx=20, pady=(2, 12))

        self.lbl_co_val = ctk.CTkLabel(sol, text="Karbonmonoksit / İs: 40 ppm", font=ctk.CTkFont(family="Consolas", size=12))
        self.lbl_co_val.pack(anchor="w", padx=20)
        self.slider_co = ctk.CTkSlider(sol, from_=0, to=500, command=self._manuel_alev_guncelle)
        self.slider_co.set(40)
        self.slider_co.pack(fill="x", padx=20, pady=(2, 15))

        self.btn_csv_oynat = ctk.CTkButton(
            sol, text="▶️ Yüklü CSV Verisini Canlı Simüle Et",
            fg_color=BTN_COLOR, hover_color=BTN_HOVER, command=self.toggle_alev_csv_simulasyonu
        )
        self.btn_csv_oynat.pack(fill="x", padx=20, pady=6)

        self.btn_su_sisi = ctk.CTkButton(
            sol, text="💦 ISS İnce Su Sisi (Water Mist) Püskürt",
            fg_color="#0077B6", hover_color="#023E8A", command=self.su_sisi_tetikle
        )
        self.btn_su_sisi.pack(fill="x", padx=20, pady=6)

        self.lbl_alev_fizik_analiz = ctk.CTkLabel(
            sol,
            text="DURUM: Stabil Mikro Yerçekimi Alevi\n• Küresel (Spherical) Difüzyon Aktif\n• İs (Soot) Kabuğu: Düşük",
            font=ctk.CTkFont(family="Consolas", size=12), text_color="#00FF88", justify="left", wraplength=300
        )
        self.lbl_alev_fizik_analiz.pack(padx=20, pady=15, anchor="w")

        self.alev_canvas = tk.Canvas(self.tab_alev, bg="#030712", highlightthickness=1, highlightbackground=GRID_COLOR)
        self.alev_canvas.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)
        self.after(300, lambda: self._kuresel_alev_ciz(350.0, 21.0, 40.0))

    def _manuel_alev_guncelle(self, _=None):
        t = self.slider_sicaklik.get()
        o2 = self.slider_o2.get()
        co = self.slider_co.get()
        self.lbl_sicaklik_val.configure(text=f"Sıcaklık: {t:.1f} °C")
        self.lbl_o2_val.configure(text=f"Oksijen (O2): %{o2:.1f}")
        self.lbl_co_val.configure(text=f"Karbonmonoksit / İs: {co:.0f} ppm")
        self._kuresel_alev_ciz(t, o2, co)

    def su_sisi_tetikle(self):
        self.su_sisi_aktif = True
        self.slider_sicaklik.set(max(100, self.slider_sicaklik.get() - 180))
        self.slider_co.set(max(10, self.slider_co.get() - 120))
        self._manuel_alev_guncelle()
        self.after(1500, lambda: setattr(self, 'su_sisi_aktif', False))

    def toggle_alev_csv_simulasyonu(self):
        if not self.veri_sozlugu:
            self.ramde_ornek_veri_uret()

        self.alev_sim_calisiyor = not self.alev_sim_calisiyor
        if self.alev_sim_calisiyor:
            self.btn_csv_oynat.configure(text="🛑 Simülasyonu Durdur", fg_color="#8B0000")
            threading.Thread(target=self._alev_csv_loop, daemon=True).start()
        else:
            self.btn_csv_oynat.configure(text="▶️ Yüklü CSV Verisini Canlı Simüle Et", fg_color=BTN_COLOR)

    def _alev_csv_loop(self):
        s_list = self.veri_sozlugu.get("Sicaklik_C") or self.veri_sozlugu[self.sutunlar[1 if len(self.sutunlar) > 1 else 0]]
        o2_list = self.veri_sozlugu.get("Oksijen_Yuzdesi") or [21.0] * len(s_list)
        co_list = self.veri_sozlugu.get("CO_Karbonmonoksit_ppm") or [50.0] * len(s_list)

        for i in range(len(s_list)):
            if not self.alev_sim_calisiyor:
                break
            t_val = max(100.0, min(750.0, float(s_list[i])))
            o2_val = max(10.0, min(35.0, float(o2_list[i]) if i < len(o2_list) else 21.0))
            co_val = max(0.0, min(500.0, float(co_list[i]) if i < len(co_list) else 50.0))

            self.after(0, lambda t=t_val, o=o2_val, c=co_val: (
                self.slider_sicaklik.set(t),
                self.slider_o2.set(o),
                self.slider_co.set(c),
                self._manuel_alev_guncelle()
            ) if self.winfo_exists() else None)
            time.sleep(0.25)

        self.alev_sim_calisiyor = False
        self.after(0, lambda: self.btn_csv_oynat.configure(text="▶️ Yüklü CSV Verisini Canlı Simüle Et", fg_color=BTN_COLOR) if self.winfo_exists() else None)

    def _kuresel_alev_ciz(self, sicaklik: float, o2: float, co: float):
        if not self.winfo_exists():
            return
        self.alev_canvas.delete("all")
        w = max(self.alev_canvas.winfo_width(), 600)
        h = max(self.alev_canvas.winfo_height(), 450)
        cx, cy = w / 2, h / 2

        yaricap = int(35 + (sicaklik - 100) * 0.22 * (o2 / 21.0))
        yaricap = max(20, min(200, yaricap))

        for k in range(4, 0, -1):
            r_halo = yaricap + k * 22
            renk_halo = "#1A0B2E" if o2 >= 18 else "#2A1205"
            self.alev_canvas.create_oval(cx - r_halo, cy - r_halo, cx + r_halo, cy + r_halo, outline=renk_halo, width=3)

        if o2 < 18.5 or co > 150:
            r_soot = int(yaricap * 1.18)
            self.alev_canvas.create_oval(
                cx - r_soot, cy - r_soot, cx + r_soot, cy + r_soot,
                fill="#D97706", outline="#F59E0B", width=3
            )
            for aci in range(0, 360, 20):
                rad = math.radians(aci + (sicaklik % 20))
                px = cx + math.cos(rad) * (r_soot + 14)
                py = cy + math.sin(rad) * (r_soot + 14)
                self.alev_canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill="#78350F", outline="#F59E0B")

        dis_renk = "#0077FF" if o2 >= 18.5 else "#EA580C"
        orta_renk = "#38BDF8" if o2 >= 18.5 else "#FACC15"
        cekirdek_renk = "#E0F2FE"

        self.alev_canvas.create_oval(cx - yaricap, cy - yaricap, cx + yaricap, cy + yaricap, fill=dis_renk, outline="#00FFCC", width=2)
        r_orta = int(yaricap * 0.72)
        self.alev_canvas.create_oval(cx - r_orta, cy - r_orta, cx + r_orta, cy + r_orta, fill=orta_renk, outline="")
        r_ic = int(yaricap * 0.38)
        self.alev_canvas.create_oval(cx - r_ic, cy - r_ic, cx + r_ic, cy + r_ic, fill=cekirdek_renk, outline="")

        if self.su_sisi_aktif:
            for aci in range(0, 360, 15):
                rad = math.radians(aci)
                sx = cx + math.cos(rad) * (yaricap * 0.85)
                sy = cy + math.sin(rad) * (yaricap * 0.85)
                self.alev_canvas.create_oval(sx - 4, sy - 4, sx + 4, sy + 4, fill="#00FFFF", outline="#FFFFFF")

        if o2 < 18.0:
            durum = "⚠️ EKSİK YANMA & YÜKSEK İS (SOOT) RİSKİ!\n• O2 <%18: Karbonmonoksit ve kurum artıyor.\n• Tavsiye: Havalandırma izolasyonu ve İnce Su Sisi."
            renk_d = "#F59E0B"
        elif o2 > 25.0:
            durum = "🚨 YÜKSEK OKSİJEN / FAN SIZINTISI ALARMI!\n• Kapalı modülde O2 artışı dış fan beslemesini gösterir.\n• Alev çapı hızla genişliyor! Su sisi (Water Mist) uygulayın."
            renk_d = "#FF3333"
        else:
            durum = "✅ STABİL MİKRO YERÇEKİMİ KÜRESEL ALEVİ\n• Kaldırma kuvveti (buoyancy) yok.\n• Mavi küresel difüzyon dengede."
            renk_d = "#00FF88"

        self.lbl_alev_fizik_analiz.configure(text=durum, text_color=renk_d)
        self.alev_canvas.create_text(
            w / 2, 28,
            text=f"Küresel Alev Çapı: {yaricap*2} birimsel mm | T: {sicaklik:.1f}°C | O2: %{o2:.1f} | CO: {co:.0f} ppm",
            fill=HIGHLIGHT_COLOR, font=("Consolas", 13, "bold")
        )

    # =========================================================================
    # SEKME 3: BELLEK-İÇİ VERİ SESLENDİRME (SONIFICATION) & OSİLOSKOP
    # =========================================================================
    def _sekme_ses_hazirla(self):
        ust = ctk.CTkFrame(self.tab_ses, fg_color="transparent")
        ust.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(ust, text="Seslendirilecek Veri Sütunu:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=6)
        self.combo_ses_sutun = ctk.CTkOptionMenu(ust, values=["Veri Yok"], width=180, state="disabled")
        self.combo_ses_sutun.pack(side="left", padx=6)

        self.btn_ses_baslat = ctk.CTkButton(
            ust, text="🔊 Veriyi RAM'de Sese Dönüştür & Çal (Sonification)",
            fg_color=BTN_COLOR, hover_color=BTN_HOVER, width=320, command=self.toggle_sonification
        )
        self.btn_ses_baslat.pack(side="left", padx=12)

        self.lbl_frekans = ctk.CTkLabel(
            ust, text="Anlık Frekans: 0 Hz",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color=HIGHLIGHT_COLOR
        )
        self.lbl_frekans.pack(side="right", padx=15)

        self.osc_canvas = tk.Canvas(self.tab_ses, bg="#040814", highlightthickness=1, highlightbackground=GRID_COLOR)
        self.osc_canvas.pack(fill="both", expand=True, padx=15, pady=10)

    def _ramde_wav_olustur_ve_cal(self, frekanslar: list, nota_suresi: float = 0.12):
        """Hiçbir dosya oluşturmadan doğrudan RAM'de (array + io.BytesIO) hızlı PCM WAV ses dalgası sentezler ve çalar."""
        if not WINSOUND_AVAILABLE:
            return
        sample_rate = 22050
        toplam_ornek = int(sample_rate * nota_suresi)
        ram_buffer = io.BytesIO()

        # Zarf değerlerini bir kez önceden hesapla (Hızlandırma)
        zarf_tablosu = [16000.0 * math.sin(math.pi * (i / toplam_ornek)) for i in range(toplam_ornek)]
        iki_pi_sr = (2.0 * math.pi) / sample_rate

        ses_dizisi = array.array('h')
        for freq in frekanslar:
            adim_katsayisi = iki_pi_sr * freq
            ses_dizisi.extend(
                int(zarf_tablosu[i] * math.sin(adim_katsayisi * i))
                for i in range(toplam_ornek)
            )

        with wave.open(ram_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(ses_dizisi.tobytes())

        winsound.PlaySound(ram_buffer.getvalue(), winsound.SND_MEMORY | winsound.SND_ASYNC)

    def toggle_sonification(self):
        if not self.veri_sozlugu:
            self.ramde_ornek_veri_uret()

        if self.ses_calisiyor:
            self.ses_calisiyor = False
            if WINSOUND_AVAILABLE:
                winsound.PlaySound(None, winsound.SND_PURGE)
            self.btn_ses_baslat.configure(text="🔊 Veriyi RAM'de Sese Dönüştür & Çal (Sonification)", fg_color=BTN_COLOR)
            return

        sutun = self.combo_ses_sutun.get()
        veriler = self.veri_sozlugu.get(sutun, [])
        if not veriler:
            return

        self.ses_calisiyor = True
        self.btn_ses_baslat.configure(text="🛑 Seslendirmeyi Durdur", fg_color="#8B0000")
        threading.Thread(target=self._sonification_loop, args=(veriler[:60], sutun), daemon=True).start()

    def _sonification_loop(self, veriler: list, sutun_adi: str):
        min_v, max_v = min(veriler), max(veriler)
        span = max(max_v - min_v, 1e-5)

        frekans_listesi = [int(240 + ((v - min_v) / span) * 1200) for v in veriler]
        self._ramde_wav_olustur_ve_cal(frekans_listesi, nota_suresi=0.14)

        for i, (deger, freq) in enumerate(zip(veriler, frekans_listesi)):
            if not self.ses_calisiyor:
                break
            self.after(0, lambda d=deger, f=freq, idx=i: self._osiloskop_ciz(d, f, idx, len(veriler), sutun_adi))
            time.sleep(0.14)

        self.ses_calisiyor = False
        self.after(0, lambda: self.btn_ses_baslat.configure(
            text="🔊 Veriyi RAM'de Sese Dönüştür & Çal (Sonification)", fg_color=BTN_COLOR
        ) if self.winfo_exists() else None)

    def _osiloskop_ciz(self, deger: float, frekans: int, adim: int, toplam: int, sutun_adi: str):
        if not self.winfo_exists():
            return
        self.osc_canvas.delete("all")
        w = max(self.osc_canvas.winfo_width(), 600)
        h = max(self.osc_canvas.winfo_height(), 350)
        orta_y = h / 2

        self.lbl_frekans.configure(text=f"Veri: {deger:.2f} | Frekans: {frekans} Hz ({adim+1}/{toplam})")
        self.osc_canvas.create_line(0, orta_y, w, orta_y, fill=GRID_COLOR, width=1)

        noktalar = []
        dalga_sikligi = frekans / 90.0
        genlik = min(h * 0.38, 40 + (frekans - 240) * 0.1)

        for x in range(0, w, 4):
            rad = (x / w) * math.pi * 2 * dalga_sikligi
            y = orta_y + math.sin(rad) * genlik
            noktalar.extend([x, y])

        if len(noktalar) >= 4:
            renk = "#FF007F" if frekans > 1000 else "#00FFCC"
            self.osc_canvas.create_line(*noktalar, fill=renk, width=3, smooth=True)

        self.osc_canvas.create_text(
            w / 2, 30,
            text=f"🎵 RAM-İÇİ AKUSTİK TELEMETRİ SENTEZLEYİCİ ({sutun_adi}) - Diskte Dosya Oluşturulmaz",
            fill=HIGHLIGHT_COLOR, font=("Consolas", 13, "bold")
        )

    def _tam_ekran_yap(self):
        try:
            if self.winfo_exists():
                self.attributes("-fullscreen", True)
                self._tam_ekran_mi = True
                self.lift()
                self.focus_force()
        except Exception:
            pass

    def _tam_ekran_degistir(self, event=None):
        try:
            self._tam_ekran_mi = not getattr(self, "_tam_ekran_mi", False)
            self.attributes("-fullscreen", self._tam_ekran_mi)
        except Exception:
            pass

    def _tam_ekrandan_cik(self, event=None):
        try:
            if getattr(self, "_tam_ekran_mi", False):
                self._tam_ekran_mi = False
                self.attributes("-fullscreen", False)
        except Exception:
            pass

    def on_closing(self):
        self.alev_sim_calisiyor = False
        self.ses_calisiyor = False
        if WINSOUND_AVAILABLE:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    kok = ctk.CTk()
    kok.withdraw()
    pencere = UzayTelemetriMerkezi(kok)
    pencere.protocol("WM_DELETE_WINDOW", kok.destroy)
    kok.mainloop()