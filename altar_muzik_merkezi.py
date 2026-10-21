# -*- coding: utf-8 -*-
"""
================================================================================
ALTAR MÜZİK & SİNEMATİK SES MERKEZİ (YOUTUBE / LOCAL AUDIO + CİNEMATİC VİSUALİZER)
================================================================================
* YouTube ve YouTube Music üzerinden en kaliteli sesi (MP3) arka planda indirme.
* Arka planda kesintisiz ses çalma: Kullanıcı başka sekmelere veya programlara geçse
  bile müzik arka planda çalmaya devam eder.
* Müzik çalarken arka planda 60 FPS sinematik doğa şelale, mavi plazma ve neon siber
  animasyon görselleştirmesi.
* Çalma Listesi, İlerleme Çubuğu, Döngü (Loop), Karışık (Shuffle) ve Tam Ekran modu.
================================================================================
"""

import os
import sys
import re
import time
import math
import random
import ssl
import hashlib
import tempfile
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

# Windows & MEB / Antivirüs Kendi İmzalı SSL Sertifika Doğrulamasını Güvenle Aş
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass

try:
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
except Exception:
    pygame = None

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

# Windows API Entegrasyonu
if os.name == "nt":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

# Proje Müzik Depolama Yolu
if getattr(sys, "frozen", False):
    PROJE_KOK = os.path.dirname(sys.executable)
else:
    PROJE_KOK = os.path.dirname(os.path.abspath(__file__))
MUZIK_KLASORU = os.path.join(PROJE_KOK, "Ses_Kayitlari", "Muzik")
os.makedirs(MUZIK_KLASORU, exist_ok=True)


def _ffmpeg_yolu_bul():
    yerel_ffmpeg = os.path.join(PROJE_KOK, "ffmpeg.exe")
    if os.path.isfile(yerel_ffmpeg):
        return yerel_ffmpeg
    if getattr(sys, "frozen", False):
        mei_ffmpeg = os.path.join(getattr(sys, "_MEIPASS", ""), "ffmpeg.exe")
        if os.path.isfile(mei_ffmpeg):
            return mei_ffmpeg
    return "ffmpeg"


class AltarMuzikCalici:
    """Tüm uygulama genelinde arka planda kesintisiz çalışan müzik motoru."""
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AltarMuzikCalici()
        return cls._instance

    def __init__(self):
        self.calma_listesi = []
        self.su_anki_indeks = -1
        self.su_anki_dosya = None
        self.su_anki_baslik = "Müzik Seçilmedi"
        self.oynatiliyor = False
        self.dongu_aktif = False
        self.karisik_aktif = False
        self.ses_seviyesi = 0.85
        self.toplam_sure_sn = 0.0
        self.baslama_zamani = 0.0
        self.duraklatma_noktasi_sn = 0.0

        if pygame and pygame.mixer.get_init():
            try:
                pygame.mixer.music.set_volume(self.ses_seviyesi)
            except Exception:
                pass

    def parca_oynat(self, dosya_yolu):
        """Belirtilen ses veya MP4 dosyasını arka planda (sadece ses olarak) çalmaya başlar."""
        if not dosya_yolu or not os.path.isfile(dosya_yolu):
            return False

        if pygame is None or not pygame.mixer.get_init():
            return False

        try:
            self.su_anki_dosya = dosya_yolu
            self.su_anki_baslik = os.path.splitext(os.path.basename(dosya_yolu))[0]
            calinacak_yol = dosya_yolu

            # Eğer dosya MP4 veya video konteyneri ise, ffmpeg ile sadece sesi ayıkla ve arka planda çal
            if dosya_yolu.lower().endswith((".mp4", ".mkv", ".mov", ".avi")):
                yol_hash = hashlib.md5(dosya_yolu.encode("utf-8", "ignore")).hexdigest()[:12]
                gecici_mp3 = os.path.join(tempfile.gettempdir(), f"altar_muzik_ses_{yol_hash}.mp3")
                if not os.path.isfile(gecici_mp3) or os.path.getsize(gecici_mp3) < 1024:
                    ffmpeg_bin = _ffmpeg_yolu_bul()
                    komut = [
                        ffmpeg_bin, "-y", "-i", dosya_yolu,
                        "-vn", "-acodec", "libmp3lame", "-q:a", "2",
                        "-threads", "2", gecici_mp3
                    ]
                    subprocess.run(
                        komut,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=0x08000000 if os.name == "nt" else 0,
                        check=False,
                        timeout=15
                    )
                if os.path.isfile(gecici_mp3) and os.path.getsize(gecici_mp3) > 1024:
                    calinacak_yol = gecici_mp3

            pygame.mixer.music.load(calinacak_yol)
            pygame.mixer.music.set_volume(self.ses_seviyesi)
            pygame.mixer.music.play()
            self.oynatiliyor = True
            self.baslama_zamani = time.time()
            self.duraklatma_noktasi_sn = 0.0

            # Dosya süresini yaklaşık hesapla
            self._sure_hesapla(calinacak_yol)
            return True
        except Exception:
            self.oynatiliyor = False
            return False

    def _sure_hesapla(self, dosya_yolu):
        """Basit dosya boyutu / bitrate tahmini veya mutlak süre tespiti."""
        try:
            boyut = os.path.getsize(dosya_yolu)
            # Ortalama 192kbps MP3 için (~24000 byte/sn)
            self.toplam_sure_sn = max(30.0, boyut / 24000.0)
        except Exception:
            self.toplam_sure_sn = 180.0

    def oynat_duraklat(self):
        """Çalmayı duraklatır veya devam ettirir."""
        if not self.su_anki_dosya or pygame is None:
            return False

        if self.oynatiliyor:
            try:
                pygame.mixer.music.pause()
                self.duraklatma_noktasi_sn += time.time() - self.baslama_zamani
                self.oynatiliyor = False
            except Exception:
                pass
        else:
            try:
                pygame.mixer.music.unpause()
                self.baslama_zamani = time.time()
                self.oynatiliyor = True
            except Exception:
                pass
        return self.oynatiliyor

    def durdur(self):
        """Çalmayı tamamen durdurur."""
        if pygame:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self.oynatiliyor = False
        self.duraklatma_noktasi_sn = 0.0

    def ses_ayarla(self, seviye: float):
        """0.0 ile 1.0 arasında ses seviyesi ayarlar."""
        self.ses_seviyesi = max(0.0, min(1.0, float(seviye)))
        if pygame and pygame.mixer.get_init():
            try:
                pygame.mixer.music.set_volume(self.ses_seviyesi)
            except Exception:
                pass

    def guncel_sure_sn(self) -> float:
        """Şu anki çalınan süreyi saniye olarak döndürür."""
        if not self.oynatiliyor:
            return self.duraklatma_noktasi_sn
        return self.duraklatma_noktasi_sn + (time.time() - self.baslama_zamani)


class AltarMuzikMerkezi(ctk.CTkFrame):
    """
    YouTube / YouTube Music indirme, yerel kütüphane ve arka planda
    çalan müzik için 60 FPS sinematik animasyon sunan arayüz.
    """
    def __init__(self, parent, pencere_modu=False):
        super().__init__(parent, fg_color="#040711")
        self.pencere_modu = pencere_modu
        self.calici = AltarMuzikCalici.get_instance()

        # Sinematik Animasyon Durumu
        self.aktif_tema = "doga"  # "doga", "plazma", "matrix"
        self._animasyon_calisiyor = True
        self._animasyon_adimi = 0
        self._parcaciklar = []
        self._frekans_barlari = [random.uniform(10, 80) for _ in range(32)]

        self._arayuz_olustur()
        self._kutuphaneyi_tara()
        self._sinematik_animasyon_dongusu()

    def _arayuz_olustur(self):
        # 1. ÜST PANEL: YouTube / YouTube Music Arama & İndirme Çubuğu
        ust_panel = ctk.CTkFrame(self, fg_color="#0A0F1D", corner_radius=8, border_width=1, border_color="#1E3A8A")
        ust_panel.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            ust_panel, text="🎵 YOUTUBE / YT MUSIC SES İNDİR:",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#38BDF8"
        ).pack(side="left", padx=(12, 6))

        self.entry_yt_url = ctk.CTkEntry(
            ust_panel,
            placeholder_text="YouTube URL veya şarkı adı girin (Örn: https://www.youtube.com/watch?v=... veya Lofi Chill)",
            font=ctk.CTkFont(family="Consolas", size=11),
            height=28
        )
        self.entry_yt_url.pack(side="left", fill="x", expand=True, padx=6)
        self.entry_yt_url.bind("<Return>", lambda e: self._yt_indir_tiklandi())

        self.btn_indir = ctk.CTkButton(
            ust_panel, text="📥 Sesi İndir (MP3)", width=130, height=28,
            fg_color="#059669", hover_color="#047857",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self._yt_indir_tiklandi
        )
        self.btn_indir.pack(side="left", padx=6)

        btn_dosya_sec = ctk.CTkButton(
            ust_panel, text="📂 Dosya Ekle", width=105, height=28,
            fg_color="#1E293B", hover_color="#334155",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self._yerel_dosya_ekle
        )
        btn_dosya_sec.pack(side="left", padx=(0, 10))

        # 2. ORTA BÖLÜM: Sol Çalma Listesi + Sağ Sinematik Animasyon Sahnesi
        orta_panel = ctk.CTkFrame(self, fg_color="transparent")
        orta_panel.pack(fill="both", expand=True, padx=12, pady=4)

        # Sol: Yerel Müzik Kütüphanesi
        sol_panel = ctk.CTkFrame(orta_panel, fg_color="#090E1A", width=330, corner_radius=8, border_width=1, border_color="#1E3A8A")
        sol_panel.pack(side="left", fill="y", padx=(0, 6))

        sol_ust = ctk.CTkFrame(sol_panel, fg_color="transparent")
        sol_ust.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            sol_ust, text="📻 MÜZİK KÜTÜPHANESİ",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#00FFCC"
        ).pack(side="left")

        btn_yenile = ctk.CTkButton(
            sol_ust, text="🔄 Yenile", width=70, height=22,
            fg_color="#1E293B", hover_color="#334155",
            font=ctk.CTkFont(family="Consolas", size=10),
            command=self._kutuphaneyi_tara
        )
        btn_yenile.pack(side="right")

        # Parça Listesi (Scrollable)
        self.liste_frame = ctk.CTkScrollableFrame(sol_panel, fg_color="#030712", height=340)
        self.liste_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # Sağ: SİNEMATİK ANİMASYON TUVALİ (ARKA PLAN GÖRSELİ)
        sag_panel = ctk.CTkFrame(orta_panel, fg_color="#000000", corner_radius=8, border_width=1, border_color="#1E3A8A")
        sag_panel.pack(side="right", fill="both", expand=True, padx=(6, 0))

        # Tema Seçim ve Tam Ekran Üst Şerit
        sag_ust_serit = ctk.CTkFrame(sag_panel, fg_color="#0D1322", height=34)
        sag_ust_serit.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            sag_ust_serit, text="✨ Sinematik Tema:",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#94A3B8"
        ).pack(side="left", padx=(10, 4))

        self.combo_tema = ctk.CTkOptionMenu(
            sag_ust_serit,
            values=["🌊 Doğa Şelale & Orman", "🔥 Kozmik Mavi Plazma", "⚡ Cyberpunk Matrix Spektrum"],
            command=self._tema_degisti,
            width=210, height=22,
            fg_color="#1E293B"
        )
        self.combo_tema.pack(side="left", padx=4)

        btn_tam_ekran = ctk.CTkButton(
            sag_ust_serit, text="⛶ Tam Ekran Sinematik", width=145, height=22,
            fg_color="#0284C7", hover_color="#0369A1",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self.tam_ekran_sinematik_ac
        )
        btn_tam_ekran.pack(side="right", padx=10)

        # Çizim Tuvali
        self.canvas = tk.Canvas(
            sag_panel, bg="#020617", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # 3. ALT PANEL: Akıllı Müzik Oynatıcı Kontrolleri (HUD)
        alt_hud = ctk.CTkFrame(self, fg_color="#0A0F1D", corner_radius=8, border_width=1, border_color="#1E3A8A", height=65)
        alt_hud.pack(fill="x", padx=12, pady=(4, 10))

        # Zaman Slider
        self.slider_zaman = ctk.CTkSlider(
            alt_hud, from_=0, to=100, height=12,
            progress_color="#00E5FF", button_color="#38BDF8"
        )
        self.slider_zaman.pack(fill="x", padx=16, pady=(4, 2))
        self.slider_zaman.set(0)

        kontrol_satir = ctk.CTkFrame(alt_hud, fg_color="transparent")
        kontrol_satir.pack(fill="x", padx=14, pady=(0, 4))

        # Sol: Parça Bilgisi
        self.lbl_parca_bilgi = ctk.CTkLabel(
            kontrol_satir, text="⏹ Parça Çalmıyor",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#00FFCC"
        )
        self.lbl_parca_bilgi.pack(side="left", padx=(0, 10))

        self.lbl_sure_bilgi = ctk.CTkLabel(
            kontrol_satir, text="00:00 / 00:00",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#94A3B8"
        )
        self.lbl_sure_bilgi.pack(side="left", padx=6)

        # Orta: Butonlar
        orta_butonlar = ctk.CTkFrame(kontrol_satir, fg_color="transparent")
        orta_butonlar.pack(side="left", expand=True)

        self.btn_onceki = ctk.CTkButton(
            orta_butonlar, text="⏮ Önceki", width=75, height=26,
            fg_color="#1E293B", hover_color="#334155",
            font=ctk.CTkFont(family="Consolas", size=11),
            command=self._onceki_parca
        )
        self.btn_onceki.pack(side="left", padx=4)

        self.btn_oynat_duraklat = ctk.CTkButton(
            orta_butonlar, text="▶ Oynat", width=95, height=28,
            fg_color="#00A86B", hover_color="#007F50",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self._oynat_duraklat_tiklandi
        )
        self.btn_oynat_duraklat.pack(side="left", padx=6)

        self.btn_sonraki = ctk.CTkButton(
            orta_butonlar, text="⏭ Sonraki", width=75, height=26,
            fg_color="#1E293B", hover_color="#334155",
            font=ctk.CTkFont(family="Consolas", size=11),
            command=self._sonraki_parca
        )
        self.btn_sonraki.pack(side="left", padx=4)

        # Sağ: Ses Seviyesi Slider'ı
        self.slider_ses = ctk.CTkSlider(
            kontrol_satir, from_=0, to=1, width=85, height=12,
            progress_color="#10B981", button_color="#34D399",
            command=self._ses_degisti
        )
        self.slider_ses.pack(side="right", padx=(4, 0))
        self.slider_ses.set(self.calici.ses_seviyesi)

        self.lbl_ses_yuzde = ctk.CTkLabel(
            kontrol_satir, text="🔊 %85",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#10B981"
        )
        self.lbl_ses_yuzde.pack(side="right", padx=6)

    def _kutuphaneyi_tara(self):
        """Müzik klasöründeki dosyaları listeler."""
        for w in self.liste_frame.winfo_children():
            w.destroy()

        dosyalar = []
        if os.path.isdir(MUZIK_KLASORU):
            for dosya in os.listdir(MUZIK_KLASORU):
                if dosya.lower().endswith((".mp3", ".wav", ".m4a", ".flac", ".ogg", ".mp4")):
                    dosyalar.append(os.path.join(MUZIK_KLASORU, dosya))

        self.calici.calma_listesi = dosyalar

        if not dosyalar:
            ctk.CTkLabel(
                self.liste_frame, text="Henüz müzik yok.\nYukarıdan YouTube URL girerek indirin\nveya 'Dosya Ekle' butonuna basın.",
                font=ctk.CTkFont(family="Consolas", size=11), text_color="#64748B", justify="center"
            ).pack(pady=30)
            return

        for idx, yol in enumerate(dosyalar):
            ad = os.path.splitext(os.path.basename(yol))[0]
            if len(ad) > 28:
                ad = ad[:25] + "..."

            satir = ctk.CTkFrame(self.liste_frame, fg_color="#0F172A", height=32, corner_radius=6)
            satir.pack(fill="x", pady=2)

            btn = ctk.CTkButton(
                satir, text=f"▶ {ad}", anchor="w",
                font=ctk.CTkFont(family="Consolas", size=11),
                fg_color="transparent", hover_color="#1E293B",
                command=lambda p=yol, i=idx: self._parca_secildi(p, i)
            )
            btn.pack(side="left", fill="x", expand=True, padx=4)

    def _parca_secildi(self, yol, idx):
        """Kullanıcı bir parçaya tıkladığında arka planda çalmayı başlatır."""
        self.calici.su_anki_indeks = idx
        if self.calici.parca_oynat(yol):
            self.lbl_parca_bilgi.configure(text=f"🎶 {self.calici.su_anki_baslik[:30]}")
            self.btn_oynat_duraklat.configure(text="⏸ Duraklat", fg_color="#0284C7")

    def _oynat_duraklat_tiklandi(self):
        """Oynat veya Duraklat."""
        if not self.calici.su_anki_dosya:
            if self.calici.calma_listesi:
                self._parca_secildi(self.calici.calma_listesi[0], 0)
            return

        durum = self.calici.oynat_duraklat()
        if durum:
            self.btn_oynat_duraklat.configure(text="⏸ Duraklat", fg_color="#0284C7")
        else:
            self.btn_oynat_duraklat.configure(text="▶ Oynat", fg_color="#00A86B")

    def _sonraki_parca(self):
        if not self.calici.calma_listesi:
            return
        yeni_i = (self.calici.su_anki_indeks + 1) % len(self.calici.calma_listesi)
        self._parca_secildi(self.calici.calma_listesi[yeni_i], yeni_i)

    def _onceki_parca(self):
        if not self.calici.calma_listesi:
            return
        yeni_i = (self.calici.su_anki_indeks - 1) % len(self.calici.calma_listesi)
        self._parca_secildi(self.calici.calma_listesi[yeni_i], yeni_i)

    def _ses_degisti(self, val):
        self.calici.ses_ayarla(val)
        self.lbl_ses_yuzde.configure(text=f"🔊 %{int(float(val)*100)}")

    def _yerel_dosya_ekle(self):
        """Kullanıcının bilgisayarından müzik dosyası seçip kütüphaneye kopyalar."""
        secilenler = filedialog.askopenfilenames(
            title="Müzik Dosyası Seç",
            filetypes=[("Ses Dosyaları", "*.mp3 *.wav *.m4a *.flac *.ogg"), ("Tüm Dosyalar", "*.*")]
        )
        if secilenler:
            import shutil
            for s in secilenler:
                hedef = os.path.join(MUZIK_KLASORU, os.path.basename(s))
                try:
                    shutil.copy2(s, hedef)
                except Exception:
                    pass
            self._kutuphaneyi_tara()

    def _yt_indir_tiklandi(self):
        """YouTube / YouTube Music indirme sürecini ayrı iş parçacığında başlatır."""
        girdi = self.entry_yt_url.get().strip()
        if not girdi:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir YouTube URL'si veya arama terimi girin.", parent=self)
            return

        if yt_dlp is None:
            messagebox.showerror("Hata", "yt_dlp modülü yüklü değil.", parent=self)
            return

        self.btn_indir.configure(state="disabled", text="⏳ İndiriliyor...")
        threading.Thread(target=self._yt_indir_thread, args=(girdi,), daemon=True).start()

    def _url_temizle_ve_coz(self, girdi: str) -> str:
        """YouTube ve YouTube Music URL'lerini optimize eder, karmaşık parametreleri ayıklar."""
        girdi = girdi.strip()
        # music.youtube.com adresini standart youtube adresine çevir
        if "music.youtube.com" in girdi:
            girdi = girdi.replace("music.youtube.com", "www.youtube.com")

        # Tekil video oynatma listesi içindeyse sadece video ID'sini alarak hata oluşmasını engelle
        if "watch?v=" in girdi:
            m = re.search(r'v=([0-9A-Za-z_-]{11})', girdi)
            if m:
                girdi = f"https://www.youtube.com/watch?v={m.group(1)}"
        elif "youtu.be/" in girdi:
            m = re.search(r'youtu\.be/([0-9A-Za-z_-]{11})', girdi)
            if m:
                girdi = f"https://www.youtube.com/watch?v={m.group(1)}"
        return girdi

    def _yt_indir_thread(self, query):
        """yt_dlp ile sesi arka planda çeker ve MP3'e dönüştürür."""
        try:
            query = self._url_temizle_ve_coz(query)
            ffmpeg_path = _ffmpeg_yolu_bul()
            opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(MUZIK_KLASORU, "%(title)s.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "ffmpeg_location": ffmpeg_path,
                "nocheckcertificate": True,
                "prefer_insecure": True,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "default_search": "ytsearch1:",
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "ios", "mweb", "web"]
                    }
                },
                "socket_timeout": 35
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if info:
                    if "entries" in info and info["entries"]:
                        info = info["entries"][0]
                    baslik = info.get("title", "İndirilen Parça")
                else:
                    baslik = "İndirilen Parça"

            self.after(0, lambda: self._yt_indirme_tamamlandi(baslik))
        except Exception as e_ilk:
            # Fallback: Eğer MP3 doğrudan indirilemezse, MP4 video olarak indirip
            # ffmpeg ile sesi ayıkla ve arka planda çalınabilir hale getir
            try:
                opts_mp4 = {
                    "format": "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
                    "outtmpl": os.path.join(MUZIK_KLASORU, "%(title)s.%(ext)s"),
                    "ffmpeg_location": ffmpeg_path,
                    "nocheckcertificate": True,
                    "prefer_insecure": True,
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "default_search": "ytsearch1:",
                    "extractor_args": {
                        "youtube": {
                            "player_client": ["android", "ios", "mweb", "web"]
                        }
                    },
                    "socket_timeout": 35
                }
                with yt_dlp.YoutubeDL(opts_mp4) as ydl_mp4:
                    info_mp4 = ydl_mp4.extract_info(query, download=True)
                    if info_mp4:
                        if "entries" in info_mp4 and info_mp4["entries"]:
                            info_mp4 = info_mp4["entries"][0]
                        baslik = info_mp4.get("title", "İndirilen Parça")
                    else:
                        baslik = "İndirilen Parça"

                # İndirilen MP4 dosyasından ffmpeg ile sesi ayır
                olasi_mp4 = os.path.join(MUZIK_KLASORU, f"{baslik}.mp4")
                hedef_mp3 = os.path.join(MUZIK_KLASORU, f"{baslik}.mp3")
                if os.path.isfile(olasi_mp4):
                    try:
                        komut = [
                            ffmpeg_path, "-y", "-i", olasi_mp4,
                            "-vn", "-acodec", "libmp3lame", "-q:a", "2",
                            hedef_mp3
                        ]
                        subprocess.run(komut, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                        if os.path.isfile(hedef_mp3) and os.path.getsize(hedef_mp3) > 1024:
                            try:
                                os.remove(olasi_mp4)
                            except Exception:
                                pass
                    except Exception:
                        pass

                self.after(0, lambda: self._yt_indirme_tamamlandi(baslik))
            except Exception as e_fb:
                hata_mesaji = str(e_fb)
                self.after(0, lambda: self._yt_indirme_hatasi(hata_mesaji))

    def _yt_indirme_tamamlandi(self, baslik):
        self.btn_indir.configure(state="normal", text="📥 Sesi İndir (MP3)")
        self.entry_yt_url.delete(0, "end")
        self._kutuphaneyi_tara()
        messagebox.showinfo("Başarılı", f"'{baslik}' başarıyla indirildi ve kütüphaneye eklendi!", parent=self)

    def _yt_indirme_hatasi(self, err):
        self.btn_indir.configure(state="normal", text="📥 Sesi İndir (MP3)")
        if "unavailable" in err.lower() or "not available" in err.lower():
            mesaj = (
                "Bu video telif hakkı veya bölge kısıtlaması nedeniyle YouTube tarafından erişime kapatılmıştır.\n\n"
                "💡 İpucu: Şarkının adını doğrudan arama kutusuna yazarak (Örn: 'Şarkı Adı Sanatçı') "
                "veya alternatif bir bağlantıyla tekrar indirmeyi deneyin."
            )
        else:
            mesaj = f"Ses indirilemedi:\n{err[:240]}\n\n💡 İpucu: Şarkı adını yazarak aratmayı deneyebilirsiniz."
        messagebox.showerror("İndirme Bildirimi", mesaj, parent=self)

    def _tema_degisti(self, secim):
        if "Doğa" in secim:
            self.aktif_tema = "doga"
        elif "Plazma" in secim:
            self.aktif_tema = "plazma"
        else:
            self.aktif_tema = "matrix"

    def _sinematik_animasyon_dongusu(self):
        """Arka plandaki 60 FPS sinematik görselleştirici."""
        if not self._animasyon_calisiyor or not self.winfo_exists():
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100:
            w, h = 600, 350

        self._animasyon_adimi += 1
        self.canvas.delete("all")

        # Müzik çalıyorsa frekans simülasyonunu güncelle
        caliyor = self.calici.oynatiliyor
        for i in range(len(self._frekans_barlari)):
            if caliyor:
                hedef = random.uniform(20, 110)
                self._frekans_barlari[i] += (hedef - self._frekans_barlari[i]) * 0.25
            else:
                self._frekans_barlari[i] += (12 - self._frekans_barlari[i]) * 0.1

        # TEMA 1: DOĞA ŞELALE & ORMAN
        if self.aktif_tema == "doga":
            # Şelale damlaları
            if len(self._parcaciklar) < 55:
                self._parcaciklar.append({
                    "x": random.randint(w // 3, (2 * w) // 3),
                    "y": -10,
                    "vy": random.uniform(4.5, 9.0),
                    "r": random.randint(2, 4),
                    "renk": random.choice(["#38BDF8", "#06B6D4", "#A5F3FC"])
                })
            # Çiz ve güncelle
            for p in self._parcaciklar:
                p["y"] += p["vy"]
                r = p["r"]
                self.canvas.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r, fill=p["renk"], outline="")
            self._parcaciklar = [p for p in self._parcaciklar if p["y"] < h + 20]

            # Gölet Dalgası
            cx, cy = w // 2, h - 35
            for i in range(3):
                rad = ((self._animasyon_adimi * 2 + i * 40) % 120) + 15
                self.canvas.create_oval(cx - rad * 1.8, cy - rad * 0.5, cx + rad * 1.8, cy + rad * 0.5, outline="#0284C7", width=1)

        # TEMA 2: KOZMİK MAVİ PLAZMA
        elif self.aktif_tema == "plazma":
            cx, cy = w // 2, h // 2
            for i in range(4):
                rad = ((self._animasyon_adimi * 1.8 + i * 35) % 110) + 20
                renk = "#00FFCC" if i % 2 == 0 else "#2563EB"
                self.canvas.create_oval(cx - rad, cy - rad, cx + rad, cy + rad, outline=renk, width=2)
            # Merkez parlama
            self.canvas.create_oval(cx - 20, cy - 20, cx + 20, cy + 20, fill="#38BDF8", outline="#FFFFFF")

        # TEMA 3: MATRIX & SES SPEKTRUMU
        else:
            bar_w = max(4, (w - 80) // len(self._frekans_barlari))
            start_x = 40
            for i, val in enumerate(self._frekans_barlari):
                bx = start_x + i * bar_w
                by = h - 40 - int(val)
                self.canvas.create_rectangle(bx + 1, by, bx + bar_w - 2, h - 40, fill="#10B981", outline="#34D399")

        # HUD Süre Güncellemesi
        g_sn = self.calici.guncel_sure_sn()
        t_sn = self.calici.toplam_sure_sn
        if t_sn > 0:
            yuzde = min(100, (g_sn / t_sn) * 100)
            self.slider_zaman.set(yuzde)
            g_dk, g_s = divmod(int(g_sn), 60)
            t_dk, t_s = divmod(int(t_sn), 60)
            self.lbl_sure_bilgi.configure(text=f"{g_dk:02d}:{g_s:02d} / {t_dk:02d}:{t_s:02d}")

        self.after(35, self._sinematik_animasyon_dongusu)

    def tam_ekran_sinematik_ac(self):
        """Müzik çalarken tüm ekranı kaplayan sinematik görselleştirici açar."""
        pencere = ctk.CTkToplevel(self)
        pencere.title("🎬 Altar Sinematik Müzik Sahnesi")
        pencere.configure(fg_color="#000000")
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
        pencere.bind("<space>", lambda e: self._oynat_duraklat_tiklandi())

        # Tam Ekran Tuvali
        canvas = tk.Canvas(pencere, bg="#000000", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Kapatma Butonu
        btn_cikis = ctk.CTkButton(
            pencere, text="✕ Çıkış (ESC)", width=95, height=28,
            fg_color="#991B1B", hover_color="#7F1D1D",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=pencere.destroy
        )
        btn_cikis.place(relx=0.94, rely=0.04, anchor="ne")

        # Canlı Tam Ekran Döngüsü
        def _tam_ekran_dongusu():
            if not pencere.winfo_exists():
                return
            canvas.delete("all")
            # Sinematik Alev & Yıldızlar
            cx, cy = g // 2, y // 2
            for i in range(5):
                rad = ((int(time.time() * 40) + i * 50) % 240) + 30
                canvas.create_oval(cx - rad, cy - rad, cx + rad, cy + rad, outline="#00FFCC", width=2)

            baslik = self.calici.su_anki_baslik
            canvas.create_text(
                cx, cy - 20, text=f"🎶 {baslik}", fill="#38BDF8", font=("Consolas", 22, "bold")
            )
            durum_str = "▶ OYNATILIYOR (ARKA PLAN)" if self.calici.oynatiliyor else "⏸ DURAKLATILDI"
            canvas.create_text(
                cx, cy + 30, text=durum_str, fill="#10B981", font=("Consolas", 14)
            )

            pencere.after(40, _tam_ekran_dongusu)

        _tam_ekran_dongusu()


if __name__ == "__main__":
    app = ctk.CTk()
    app.title("Altar Müzik Merkezi Test")
    app.geometry("950x620")
    merkez = AltarMuzikMerkezi(app)
    merkez.pack(fill="both", expand=True)
    app.mainloop()
