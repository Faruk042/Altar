# -*- coding: utf-8 -*-
"""
================================================================================
ALTAR SİNEMATİK MP4 VİDEO OYNATICI (BORDERLESS FULLSCREEN & SİNEMATİK AÇILIŞ)
================================================================================
* MP4 videolarını sinematik doha/siber animasyon geçişiyle başlatır.
* Görev çubuğu ve başlık çubuğu dahil tüm ekranı kaplayan gerçek çerçevesiz (borderless)
  tam ekranda açılır; fare tıklaması gerektirmeden otomatik odaklanır (SetForegroundWindow).
* OpenCV + FFmpeg + Pygame Mixer tabanlı donanım hızlandırmalı ve ses senkronlu oynatım.
* Akıllı HUD kontrolleri: Oynat/Duraklat (Space), Zaman Çubuğu (Sol/Sağ ok),
  Ses Düzeyi (Yukarı/Aşağı ok), Tam Ekran (F11), Çıkış (ESC).
================================================================================
"""

import os
import sys
import time
import math
import hashlib
import tempfile
import threading
import subprocess
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import customtkinter as ctk

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
except Exception:
    pygame = None

# Windows API Entegrasyonu (Tam Ekran ve Ön Plan Odaklanması)
if os.name == "nt":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass


def _ffmpeg_yolu_bul():
    """Proje dizinindeki veya sistem PATH'indeki ffmpeg.exe dosyasını tespit eder."""
    if getattr(sys, "frozen", False):
        proje_dizini = os.path.dirname(sys.executable)
    else:
        proje_dizini = os.path.dirname(os.path.abspath(__file__))
    yerel_ffmpeg = os.path.join(proje_dizini, "ffmpeg.exe")
    if os.path.isfile(yerel_ffmpeg):
        return yerel_ffmpeg
    if getattr(sys, "frozen", False):
        mei_ffmpeg = os.path.join(getattr(sys, "_MEIPASS", ""), "ffmpeg.exe")
        if os.path.isfile(mei_ffmpeg):
            return mei_ffmpeg
    return "ffmpeg"


class AltarSinematikVideoOynatici(ctk.CTkToplevel):
    """
    Sinematik açılış animasyonuyla donatılmış, tam ekran MP4 video oynatıcı penceresi.
    """
    def __init__(self, parent=None, video_yolu=None):
        super().__init__(parent)
        self.video_yolu = video_yolu or ""
        self.parent = parent

        self.title("🎬 Altar Sinematik Video Oynatıcı")
        self.configure(fg_color="#000000")

        # Gerçek Çerçevesiz (Borderless) Tam Ekran Yapılandırması
        self.tam_ekran_mi = True
        self.overrideredirect(True)

        # Monitör fiziksel çözünürlüğünü al
        self.ekran_g = self.winfo_screenwidth()
        self.ekran_y = self.winfo_screenheight()
        self.geometry(f"{self.ekran_g}x{self.ekran_y}+0+0")

        # Pencereyi en üste ve odak noktasına al (Tıklama gerektirmeyen otomatik odak)
        self.attributes("-topmost", True)
        self.focus_force()
        if os.name == "nt":
            self.after(50, self._windows_en_one_al)

        # Durum Değişkenleri
        self.oynatiliyor = False
        self.animasyon_tamamlandi = False
        self.ses_var = False
        self.gecici_ses_yolu = None
        self.ses_kanali = None
        self.video_cap = None
        self.toplam_kare = 0
        self.fps = 30.0
        self.toplam_sure_sn = 0.0
        self.guncel_sure_sn = 0.0
        self.ses_seviyesi = 0.85
        self.hud_gorunur = True
        self._son_fare_hareketi = time.time()
        self._kare_kilidi = threading.Lock()
        self._durdur_bayragi = threading.Event()
        self._guncel_foto = None

        # Tuş ve Fare Dinleyicileri
        self.bind("<Escape>", lambda e: self.kapat())
        self.bind("<q>", lambda e: self.kapat())
        self.bind("<Q>", lambda e: self.kapat())
        self.bind("<F11>", lambda e: self._tam_ekran_degistir())
        self.bind("<space>", lambda e: self._oynat_duraklat_degistir())
        self.bind("<Left>", lambda e: self._zaman_sar(-5))
        self.bind("<Right>", lambda e: self._zaman_sar(5))
        self.bind("<Up>", lambda e: self._ses_degistir(0.05))
        self.bind("<Down>", lambda e: self._ses_degistir(-0.05))
        self.bind("<Motion>", self._fare_hareketi_algilandi)

        # Arayüz Bileşenlerini Hazırla
        self._bilesenleri_olustur()

        # Sinematik Açılış Animasyonunu Başlat
        self._sinematik_acilis_baslat()

    def _windows_en_one_al(self):
        """Windows API ile pencereyi kesin olarak en öne alır."""
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            my_hwnd = self.winfo_id()
            ctypes.windll.user32.ShowWindow(my_hwnd, 3)  # SW_MAXIMIZE
            ctypes.windll.user32.BringWindowToTop(my_hwnd)
            ctypes.windll.user32.SetForegroundWindow(my_hwnd)
        except Exception:
            pass

    def _bilesenleri_olustur(self):
        """Tuval ve HUD kontrollerini oluşturur."""
        # Ana Çizim Tuvali (Video ve Animasyonlar Burada Çizilir)
        self.canvas = tk.Canvas(
            self,
            width=self.ekran_g,
            height=self.ekran_y,
            bg="#000000",
            highlightthickness=0,
            cursor=""
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", lambda e: self._tuval_tiklandi(e))
        self.canvas.bind("<Double-Button-1>", lambda e: self._tam_ekran_degistir())

        # Alt Kısım Akıllı HUD Paneli (Şeffaf / Koyu Siber Cam Görünüm)
        self.hud_frame = ctk.CTkFrame(
            self,
            fg_color="#0A0F1D",
            corner_radius=12,
            border_width=1,
            border_color="#1E3A8A",
            height=64
        )
        # HUD'u altta ortalayarak yerleştir
        self.hud_frame.place(relx=0.5, rely=0.93, anchor="center", relwidth=0.92)

        # İlerleme Çubuğu (Seek Bar)
        self.slider_zaman = ctk.CTkSlider(
            self.hud_frame,
            from_=0,
            to=100,
            command=self._slider_kaydirildi,
            progress_color="#00E5FF",
            button_color="#38BDF8",
            button_hover_color="#0284C7",
            height=14
        )
        self.slider_zaman.pack(fill="x", padx=18, pady=(6, 2))
        self.slider_zaman.set(0)

        # Alt Butonlar Satırı
        hud_alt_satir = ctk.CTkFrame(self.hud_frame, fg_color="transparent")
        hud_alt_satir.pack(fill="x", padx=14, pady=(2, 6))

        # Sol Kısım: Oynat/Duraklat, Süre ve Video Başlığı
        self.btn_oynat = ctk.CTkButton(
            hud_alt_satir,
            text="⏸ Duraklat",
            width=95,
            height=28,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self._oynat_duraklat_degistir
        )
        self.btn_oynat.pack(side="left", padx=(0, 10))

        self.lbl_sure = ctk.CTkLabel(
            hud_alt_satir,
            text="00:00 / 00:00",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#94A3B8"
        )
        self.lbl_sure.pack(side="left", padx=(0, 15))

        dosya_adi = os.path.basename(self.video_yolu) if self.video_yolu else "Tanımsız Medya"
        if len(dosya_adi) > 45:
            dosya_adi = dosya_adi[:42] + "..."
        self.lbl_baslik = ctk.CTkLabel(
            hud_alt_satir,
            text=f"🎬 {dosya_adi}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#38BDF8"
        )
        self.lbl_baslik.pack(side="left", padx=4)

        # Sağ Kısım: Ses, Tam Ekran ve Kapatma Butonları
        self.btn_kapat = ctk.CTkButton(
            hud_alt_satir,
            text="✕ Çıkış (ESC)",
            width=90,
            height=28,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color="#991B1B",
            hover_color="#7F1D1D",
            command=self.kapat
        )
        self.btn_kapat.pack(side="right", padx=(6, 0))

        self.btn_tam_ekran = ctk.CTkButton(
            hud_alt_satir,
            text="⛶ Tam Ekran",
            width=95,
            height=28,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color="#1E293B",
            hover_color="#334155",
            command=self._tam_ekran_degistir
        )
        self.btn_tam_ekran.pack(side="right", padx=(6, 4))

        self.slider_ses = ctk.CTkSlider(
            hud_alt_satir,
            from_=0,
            to=1,
            width=90,
            height=14,
            command=self._slider_ses_degisti,
            progress_color="#10B981",
            button_color="#34D399"
        )
        self.slider_ses.pack(side="right", padx=(4, 6))
        self.slider_ses.set(self.ses_seviyesi)

        self.lbl_ses = ctk.CTkLabel(
            hud_alt_satir,
            text="🔊 %85",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#10B981"
        )
        self.lbl_ses.pack(side="right", padx=(10, 4))

    def _sinematik_acilis_baslat(self):
        """Sinematik parçacık & parlama introyu başlatır, ardından videoyu çözer."""
        self._acilis_adimi = 0
        self._acilis_parcaciklar = [
            {
                "x": self.ekran_g / 2 + math.cos(i) * (i * 12),
                "y": self.ekran_y / 2 + math.sin(i) * (i * 12),
                "vx": math.cos(i) * 3.5,
                "vy": math.sin(i) * 3.5,
                "r": (i % 4) + 2,
                "renk": "#00FFCC" if i % 2 == 0 else "#38BDF8"
            }
            for i in range(40)
        ]
        self._animasyon_dongusu()

    def _animasyon_dongusu(self):
        """Açılış sinematik animasyonu (yaklaşık 1.3 saniye)."""
        if self._durdur_bayragi.is_set():
            return

        if self._acilis_adimi < 36:
            self._acilis_adimi += 1
            self.canvas.delete("all")

            # Arka plan parlama dalgası
            ilerleme = self._acilis_adimi / 36.0
            dalga_yaricap = int(ilerleme * (self.ekran_g / 2.2))
            cx, cy = self.ekran_g // 2, self.ekran_y // 2

            # Merkez halka
            if dalga_yaricap > 10:
                self.canvas.create_oval(
                    cx - dalga_yaricap, cy - dalga_yaricap,
                    cx + dalga_yaricap, cy + dalga_yaricap,
                    outline="#0D9488", width=2
                )

            # Parçacıklar
            for p in self._acilis_parcaciklar:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                r = p["r"]
                self.canvas.create_oval(
                    p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r,
                    fill=p["renk"], outline=""
                )

            # Sinematik Metinler
            opaklik_metin = "ALTAR SİNEMATİK MEDYA MOTORU"
            self.canvas.create_text(
                cx, cy - 20,
                text=opaklik_metin,
                fill="#00FFCC",
                font=("Consolas", 24, "bold")
            )

            dosya_etiketi = os.path.basename(self.video_yolu) if self.video_yolu else ""
            self.canvas.create_text(
                cx, cy + 30,
                text=f"Hazırlanıyor: {dosya_etiketi}",
                fill="#94A3B8",
                font=("Consolas", 13)
            )

            self.after(30, self._animasyon_dongusu)
        else:
            self.animasyon_tamamlandi = True
            self.canvas.delete("all")
            self._videoyu_baslat()

    def _videoyu_baslat(self):
        """Videonun ses ve görüntü kaynaklarını çözer ve oynatmayı başlatır."""
        if not self.video_yolu or not os.path.isfile(self.video_yolu):
            messagebox.showerror("Hata", f"Geçersiz veya bulunamayan video dosyası:\n{self.video_yolu}", parent=self)
            self.kapat()
            return

        if cv2 is None:
            messagebox.showerror("Hata", "OpenCV (cv2) modülü bulunamadı.", parent=self)
            self.kapat()
            return

        # Arka planda sesi ayrıştır ve hazırla
        threading.Thread(target=self._sesi_hazirla_ve_oynat, daemon=True).start()

        # Video Yakalayıcıyı Başlat
        self.video_cap = cv2.VideoCapture(self.video_yolu)
        if not self.video_cap.isOpened():
            messagebox.showerror("Hata", "Video akışı açılamadı.", parent=self)
            self.kapat()
            return

        self.fps = self.video_cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.toplam_kare = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if self.toplam_kare > 0 and self.fps > 0:
            self.toplam_sure_sn = self.toplam_kare / self.fps

        self.oynatiliyor = True
        self.btn_oynat.configure(text="⏸ Duraklat")

        # Video döngüsünü başlat
        self._kare_goster_dongusu()

        # Otomatik HUD gizleme zamanlayıcısını başlat
        self._hud_kontrol_dongusu()

    def _sesi_hazirla_ve_oynat(self):
        """FFmpeg ile videodan sesi çıkarıp pygame mixer ile çalar."""
        if pygame is None:
            return

        try:
            ffmpeg_bin = _ffmpeg_yolu_bul()
            temp_dir = tempfile.gettempdir()
            yol_hash = hashlib.md5(self.video_yolu.encode("utf-8", "ignore")).hexdigest()[:10]
            self.gecici_ses_yolu = os.path.join(temp_dir, f"altar_ses_{yol_hash}.mp3")

            if not os.path.exists(self.gecici_ses_yolu):
                komut = [
                    ffmpeg_bin, "-y", "-i", self.video_yolu,
                    "-vn", "-acodec", "libmp3lame", "-q:a", "4",
                    "-threads", "2", self.gecici_ses_yolu
                ]
                subprocess.run(
                    komut,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000 if os.name == "nt" else 0,
                    check=False,
                    timeout=15
                )

            if os.path.isfile(self.gecici_ses_yolu) and os.path.getsize(self.gecici_ses_yolu) > 1024:
                self.ses_var = True
                pygame.mixer.music.load(self.gecici_ses_yolu)
                pygame.mixer.music.set_volume(self.ses_seviyesi)
                pygame.mixer.music.play()
        except Exception:
            self.ses_var = False

    def _kare_goster_dongusu(self):
        """OpenCV karelerini okur, ekran boyutuna ölçekler ve tuvalde çizer."""
        if self._durdur_bayragi.is_set() or not self.winfo_exists():
            return

        if self.oynatiliyor and self.video_cap and self.video_cap.isOpened():
            ret, frame = self.video_cap.read()
            if ret:
                guncel_kare_no = int(self.video_cap.get(cv2.CAP_PROP_POS_FRAMES))
                if self.fps > 0:
                    self.guncel_sure_sn = guncel_kare_no / self.fps

                # HUD Süre & Slider Güncelle
                self._sure_etiketini_guncelle()

                # Kareyi BGR'den RGB'ye dönüştür ve ekrana oranla
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, _ = frame_rgb.shape

                # En boy oranını koruyarak tam ekrana sığdır
                oran = min(self.ekran_g / w, self.ekran_y / h)
                yeni_w = max(1, int(w * oran))
                yeni_h = max(1, int(h * oran))

                frame_resized = cv2.resize(frame_rgb, (yeni_w, yeni_h), interpolation=cv2.INTER_LINEAR)
                img_pil = Image.fromarray(frame_resized)
                foto = ImageTk.PhotoImage(image=img_pil)

                # Tuval üzerinde merkezle
                cx, cy = self.ekran_g // 2, self.ekran_y // 2
                self.canvas.delete("kare")
                self.canvas.create_image(cx, cy, image=foto, tags="kare")
                self._guncel_foto = foto
            else:
                # Video bittiğinde başa sar veya durdur
                self.oynatiliyor = False
                self.btn_oynat.configure(text="▶ Oynat")
                if pygame and self.ses_var:
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass

        # FPS zamanlaması (30 FPS ise ~33ms)
        gecikme_ms = max(15, int(1000 / self.fps)) if self.fps > 0 else 33
        self.after(gecikme_ms, self._kare_goster_dongusu)

    def _sure_etiketini_guncelle(self):
        """Süre etiketini ve ilerleme çubuğunu senkronize eder."""
        if self.toplam_sure_sn > 0:
            yuzde = (self.guncel_sure_sn / self.toplam_sure_sn) * 100
            self.slider_zaman.set(yuzde)

            g_dk, g_sn = divmod(int(self.guncel_sure_sn), 60)
            t_dk, t_sn = divmod(int(self.toplam_sure_sn), 60)
            self.lbl_sure.configure(text=f"{g_dk:02d}:{g_sn:02d} / {t_dk:02d}:{t_sn:02d}")

    def _slider_kaydirildi(self, deger):
        """Kullanıcı ilerleme çubuğunu kaydırdığında videoyu sarar."""
        if self.video_cap and self.toplam_kare > 0:
            hedef_kare = int((float(deger) / 100.0) * self.toplam_kare)
            self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, hedef_kare)
            if self.fps > 0:
                self.guncel_sure_sn = hedef_kare / self.fps
                if pygame and self.ses_var:
                    try:
                        pygame.mixer.music.play(start=self.guncel_sure_sn)
                    except Exception:
                        pass

    def _zaman_sar(self, sn_fark):
        """Klavyeyle videoyu ileri veya geri sarar."""
        if self.video_cap and self.toplam_kare > 0 and self.fps > 0:
            yeni_sn = max(0, min(self.toplam_sure_sn, self.guncel_sure_sn + sn_fark))
            hedef_kare = int(yeni_sn * self.fps)
            self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, hedef_kare)
            self.guncel_sure_sn = yeni_sn
            if pygame and self.ses_var:
                try:
                    pygame.mixer.music.play(start=self.guncel_sure_sn)
                except Exception:
                    pass

    def _oynat_duraklat_degistir(self):
        """Oynatma ve duraklatma arasında geçiş yapar."""
        if not self.animasyon_tamamlandi:
            self._acilis_adimi = 36
            return

        self.oynatiliyor = not self.oynatiliyor
        if self.oynatiliyor:
            # Video sona ulaştıysa başa sar
            if self.video_cap and self.toplam_kare > 0:
                pos = int(self.video_cap.get(cv2.CAP_PROP_POS_FRAMES))
                if pos >= self.toplam_kare - 1:
                    self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.guncel_sure_sn = 0.0
                    if pygame and self.ses_var:
                        try:
                            pygame.mixer.music.play()
                        except Exception:
                            pass
            self.btn_oynat.configure(text="⏸ Duraklat")
            if pygame and self.ses_var:
                try:
                    pygame.mixer.music.unpause()
                except Exception:
                    pass
        else:
            self.btn_oynat.configure(text="▶ Oynat")
            if pygame and self.ses_var:
                try:
                    pygame.mixer.music.pause()
                except Exception:
                    pass

    def _ses_degistir(self, fark):
        """Ses düzeyini artırır veya azaltır."""
        self.ses_seviyesi = max(0.0, min(1.0, self.ses_seviyesi + fark))
        self.slider_ses.set(self.ses_seviyesi)
        self._slider_ses_degisti(self.ses_seviyesi)

    def _slider_ses_degisti(self, deger):
        """Ses slider'ı hareket ettirildiğinde."""
        self.ses_seviyesi = float(deger)
        yuzde = int(self.ses_seviyesi * 100)
        self.lbl_ses.configure(text=f"🔊 %{yuzde}")
        if pygame and self.ses_var:
            try:
                pygame.mixer.music.set_volume(self.ses_seviyesi)
            except Exception:
                pass

    def _tam_ekran_degistir(self):
        """Tam ekran ve pencere modu arasında geçiş yapar."""
        self.tam_ekran_mi = not self.tam_ekran_mi
        if self.tam_ekran_mi:
            self.overrideredirect(True)
            self.geometry(f"{self.ekran_g}x{self.ekran_y}+0+0")
            self.btn_tam_ekran.configure(text="⛶ Pencere Modu")
        else:
            self.overrideredirect(False)
            gen = int(self.ekran_g * 0.8)
            yuk = int(self.ekran_y * 0.8)
            x = (self.ekran_g - gen) // 2
            y = (self.ekran_y - yuk) // 2
            self.geometry(f"{gen}x{yuk}+{x}+{y}")
            self.btn_tam_ekran.configure(text="⛶ Tam Ekran")

    def _fare_hareketi_algilandi(self, event=None):
        """Fare hareket ettiğinde HUD'u gösterir ve sayaç sıfırlar."""
        self._son_fare_hareketi = time.time()
        if not self.hud_gorunur:
            self.hud_frame.place(relx=0.5, rely=0.93, anchor="center", relwidth=0.92)
            self.canvas.configure(cursor="")
            self.hud_gorunur = True

    def _hud_kontrol_dongusu(self):
        """2.5 saniye fare hareketsiz kalırsa HUD'u otomatik gizler."""
        if self._durdur_bayragi.is_set() or not self.winfo_exists():
            return

        if self.hud_gorunur and self.oynatiliyor:
            if time.time() - self._son_fare_hareketi > 2.5:
                self.hud_frame.place_forget()
                self.canvas.configure(cursor="none")
                self.hud_gorunur = False

        self.after(500, self._hud_kontrol_dongusu)

    def _tuval_tiklandi(self, event):
        """Tuvale tek tıklandığında oynat/duraklat yapar; açılıştaysa açılışı anında atlar."""
        if not self.animasyon_tamamlandi:
            self._acilis_adimi = 36
            return
        if event.y < self.ekran_y - 85:
            self._oynat_duraklat_degistir()

    def kapat(self):
        """Tüm kaynakları güvenle temizleyerek oynatıcıyı kapatır."""
        self._durdur_bayragi.set()
        self.oynatiliyor = False

        if pygame and self.ses_var:
            try:
                pygame.mixer.music.stop()
                if hasattr(pygame.mixer.music, "unload"):
                    pygame.mixer.music.unload()
            except Exception:
                pass

        if self.video_cap:
            try:
                self.video_cap.release()
            except Exception:
                pass

        # Geçici ses dosyasını temizle
        if self.gecici_ses_yolu and os.path.isfile(self.gecici_ses_yolu):
            try:
                os.remove(self.gecici_ses_yolu)
            except Exception:
                pass

        try:
            self.destroy()
        except Exception:
            pass


def sinematik_video_oynat(video_yolu: str, parent=None):
    """
    Dış modüllerden doğrudan çağrılabilecek güvenli başlatıcı fonksiyon.
    """
    if not video_yolu or not os.path.exists(video_yolu):
        messagebox.showerror("Hata", f"Video dosyası bulunamadı:\n{video_yolu}", parent=parent)
        return None

    try:
        pencere = AltarSinematikVideoOynatici(parent=parent, video_yolu=video_yolu)
        return pencere
    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("Hata", f"Sinematik video oynatıcı başlatılırken hata oluştu:\n{e}", parent=parent)
        return None


if __name__ == "__main__":
    app = ctk.CTk()
    app.withdraw()
    ornek_video = sys.argv[1] if len(sys.argv) > 1 else ""
    if not ornek_video:
        from tkinter import filedialog
        ornek_video = filedialog.askopenfilename(
            title="Oynatılacak MP4 Videosunu Seçin",
            filetypes=[("MP4 Videoları", "*.mp4"), ("Tüm Videolar", "*.*")]
        )
    if ornek_video:
        oynatici = AltarSinematikVideoOynatici(parent=app, video_yolu=ornek_video)
        app.mainloop()
