# -*- coding: utf-8 -*-
"""
================================================================================
ALTAR SEKMELER VE AÇIK ÖZELLİKLER GEZGİNİ (altar_sekmeler_gezgini.py)
================================================================================
* Altar arayüzündeki Sohbet ve diğer sekmeler sırasında bulunan sol ve sağ
  "📑 Sekmeler" butonlarına tıklandığında açılan kapsamlı navigatör modalı.
* Altar üzerinde açılmış olan tüm uygulama pencerelerini (Sinematik Video,
  Altar Belge & Canva Sunum, Ses Kaydedici, Ekran Video, Kamera, Ağ Radarı,
  Karantina Kasası, Ollama Kurucu, README, Komut Paleti) canlı takip eder.
* 10 temel çalışma sekmesini ve harici özellikleri kategorize ederek listeler;
  tıklanıldığında otomatik olarak ilgili sekmeye veya pencereye anında geçiş sağlar.
* Canlı arama & filtreleme, yarı-saydam siber cam (glassmorphism) tasarımı ve
  ESC kısayolu ile ultra hızlı erişim sunar.
================================================================================
"""

import os
import sys
import tkinter as tk
from typing import Any, Callable, Dict, List, Optional
import customtkinter as ctk

# Windows API Entegrasyonu (Ön Plan Odaklanması)
if os.name == "nt":
    import ctypes


class AltarSekmelerVeOzelliklerGezgini(ctk.CTkToplevel):
    """
    Altar üzerinden açılan yeni özellikleri ve tüm çalışma sekmelerini
    listeleyen, tek tıkla geçiş yaptıran interaktif cam navigasyon penceresi.
    """

    def __init__(self, parent: Any, on_sekme_sec: Optional[Callable] = None, **kwargs) -> None:
        super().__init__(parent)
        self.parent = parent
        self.on_sekme_sec = on_sekme_sec

        self.title("🗂️ Altar Sekmeler & Açık Özellikler Gezgini")
        self.configure(fg_color="#070B14")

        # Pencere Boyutları ve Ekran Ortalaması
        gen = 840
        yuk = 640
        ekran_g = self.winfo_screenwidth()
        ekran_y = self.winfo_screenheight()
        x = max(10, (ekran_g - gen) // 2)
        y = max(10, (ekran_y - yuk) // 2)
        self.geometry(f"{gen}x{yuk}+{x}+{y}")
        self.minsize(680, 500)

        # Çerçevesiz / Modern Modal Stili
        self.attributes("-topmost", True)
        self.focus_force()

        if os.name == "nt":
            self.after(30, self._windows_on_plana_al)

        # Tuş Dinleyicileri
        self.bind("<Escape>", lambda _: self.destroy())

        # Veri Kayıtları
        self._harici_ozellikler = self._harici_ozellikleri_olustur()
        self._ana_sekmeler = self._ana_sekmeleri_olustur()

        # Arayüz Bileşenlerini Kur
        self._arayuz_olustur()

    def _windows_on_plana_al(self) -> None:
        try:
            hwnd = self.winfo_id()
            ctypes.windll.user32.BringWindowToTop(hwnd)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    def _harici_ozellikleri_olustur(self) -> List[Dict[str, Any]]:
        """Altar üzerinden bağımsız pencere olarak açılabilen modülleri derler."""
        p = self.parent
        aktifler = getattr(p, "_aktif_pencereler", {})

        return [
            {
                "id": "video",
                "ikon": "🎬",
                "baslik": "Sinematik MP4 Video Oynatıcı",
                "kategori": "Multimedya & Video",
                "aciklama": "MP4/MKV videolarını 60 FPS sinematik intro ve çerçevesiz tam ekranda ses senkronlu oynatır.",
                "aksiyon": p.sinematik_video_sec_ve_oynat if hasattr(p, "sinematik_video_sec_ve_oynat") else None,
                "pencere": aktifler.get("video"),
            },
            {
                "id": "word",
                "ikon": "📝",
                "baslik": "Altar Belge & Canva Sunum Stüdyosu",
                "kategori": "Ofis & Grafik Tasarım",
                "aciklama": "SHA-256 imzalı .altar kelime işlemcisi ve Canva tarzı 16:9 geniş ekran profesyonel slayt stüdyosu.",
                "aksiyon": p.word_programini_ac if hasattr(p, "word_programini_ac") else None,
                "pencere": aktifler.get("word"),
            },
            {
                "id": "ses",
                "ikon": "🎙️",
                "baslik": "Altar Ses Kaydedici & Spektrum Stüdyosu",
                "kategori": "Ses & Akustik",
                "aciklama": "Mikrofon ses kaydı, gürültü engelleme, canlı frekans spektrumu ve WAV dışa aktarımı.",
                "aksiyon": p.ses_kaydedici_studyosunu_ac if hasattr(p, "ses_kaydedici_studyosunu_ac") else None,
                "pencere": aktifler.get("ses"),
            },
            {
                "id": "ekran_video",
                "ikon": "📹",
                "baslik": "Altar Ekran Video Kaydedici & Stüdyo",
                "kategori": "Masaüstü & Ekran Kaydı",
                "aciklama": "Masaüstü tam ekran video kaydı, 30/60 FPS ayarı, mikrofon ve sistem sesi birleştirme.",
                "aksiyon": p.video_kaydedici_studyosunu_ac if hasattr(p, "video_kaydedici_studyosunu_ac") else None,
                "pencere": aktifler.get("ekran_video"),
            },
            {
                "id": "kamera",
                "ikon": "📷",
                "baslik": "Altar Kamera & Güvenlik Gözü",
                "kategori": "Görüntüleme & Optik",
                "aciklama": "Webcam canlı video yakalama, anlık fotoğraf çekimi ve hareket algılama kayıt merkezi.",
                "aksiyon": p.kamera_studyosunu_ac if hasattr(p, "kamera_studyosunu_ac") else None,
                "pencere": aktifler.get("kamera"),
            },
            {
                "id": "radar",
                "ikon": "🌐",
                "baslik": "Altar Ağ Radarı & Ham Paket Analizi",
                "kategori": "Siber Güvenlik & Ağ",
                "aciklama": "Aktif sistem TCP/UDP soketleri, IP adresleri, uzak bağlantı haritası ve ağ trafiği.",
                "aksiyon": p.ag_radarini_ac if hasattr(p, "ag_radarini_ac") else None,
                "pencere": aktifler.get("radar"),
            },
            {
                "id": "karantina",
                "ikon": "🛡️",
                "baslik": "Altar Karantina Kasası & Tehdit İzolatörü",
                "kategori": "Siber Güvenlik & EDR",
                "aciklama": "Zararlı ve şüpheli dosyaları şifreleyerek karantinaya alan güvenli izolasyon kasası.",
                "aksiyon": p.karantina_kasasini_ac if hasattr(p, "karantina_kasasini_ac") else None,
                "pencere": aktifler.get("karantina"),
            },
            {
                "id": "ollama",
                "ikon": "🚀",
                "baslik": "Altar Ollama Otomatik Kurucu & AI Motoru",
                "kategori": "Yapay Zeka & Çekirdek",
                "aciklama": "Ollama indirme, UAC yükseltme, güvenlik duvarı ve yerel siber AI modellerini kuran sihirbaz.",
                "aksiyon": p.ollama_otomatik_kurulumunu_ac if hasattr(p, "ollama_otomatik_kurulumunu_ac") else None,
                "pencere": aktifler.get("ollama"),
            },
            {
                "id": "readme",
                "ikon": "📖",
                "baslik": "Altar README & Kapsamlı Sistem Kılavuzu",
                "kategori": "Rehber & Dokümantasyon",
                "aciklama": "Tüm sekmeleri ve harici araçları kategorize ederek anlatan çevrimdışı interaktif rehber.",
                "aksiyon": p.readme_merkezini_ac if hasattr(p, "readme_merkezini_ac") else None,
                "pencere": aktifler.get("readme"),
            },
            {
                "id": "komut",
                "ikon": "⌨️",
                "baslik": "Altar Hızlı Komut Paleti (Ctrl+K)",
                "kategori": "Navigasyon & Araçlar",
                "aciklama": "Klavyeden anında eylem çalıştırma, sekme geçişi ve özellik arama merkezi.",
                "aksiyon": p.komut_paletini_ac if hasattr(p, "komut_paletini_ac") else None,
                "pencere": aktifler.get("komut"),
            },
            {
                "id": "nasa",
                "ikon": "🔥",
                "baslik": "NASA Soğuk Alev & Uzay Telemetri Simülasyonu",
                "kategori": "Uzay & Yanma Fiziği",
                "aciklama": "Mikroyerçekimi soğuk alev (cool flame) kimyasal reaksiyonu ve D² sönme telemetrisi.",
                "aksiyon": p.toggle_nasa_sim if hasattr(p, "toggle_nasa_sim") else None,
                "pencere": None,
            },
        ]

    def _ana_sekmeleri_olustur(self) -> List[Dict[str, Any]]:
        """Altar tabview üzerinde bulunan 10 temel çalışma sekmesini derler."""
        return [
            {
                "ad": "📁 Dosya Gezgini & Kasa",
                "ikon": "📁",
                "baslik": "Dosya Gezgini & Kasa",
                "kategori": "Depolama & Kriptografi",
                "aciklama": "Disklerde hızlı gezinme, salt-okunur hex analizi, SHA-256 ve PBKDF2 şifreli kasa.",
            },
            {
                "ad": "🎮 Oyun",
                "ikon": "🎮",
                "baslik": "Siber Oyun Merkezi",
                "kategori": "Eğlence & Simülasyon",
                "aciklama": "Galaktik Savunma, Kuantum Yılan, Siber Hack ve AI Pong 2.0 arcade oyunları.",
            },
            {
                "ad": "💬 Sohbet",
                "ikon": "💬",
                "baslik": "Yapay Zeka Sohbet & Çekirdek",
                "kategori": "Yapay Zeka & Asistan",
                "aciklama": "Yerel Ollama ve Gemini API destekli hibrit mühendislik ve kodlama asistanı.",
            },
            {
                "ad": "🎵 Müzik",
                "ikon": "🎵",
                "baslik": "Müzik Merkezi & YouTube Çalıcı",
                "kategori": "Multimedya & Ses",
                "aciklama": "YouTube / YT Music ses indirici, yerel oynatıcı ve canlı şelale sinematik arka planı.",
            },
            {
                "ad": "🐍 Python IDE & Editör",
                "ikon": "🐍",
                "baslik": "Python IDE & Kod Editörü",
                "kategori": "Yazılım Geliştirme",
                "aciklama": "Çok sekmeli Python geliştirme ortamı, Pip paket yöneticisi ve canlı sözdizimi denetimi.",
            },
            {
                "ad": "📊 Kazınan Veri & Analiz Merkezi",
                "ikon": "📊",
                "baslik": "Kazınan Veri & Analiz Merkezi",
                "kategori": "Veri Madenciliği & Web",
                "aciklama": "Web kazıma (Scraper), yapılandırılmış JSON/CSV veri analizi ve istatistik paneli.",
            },
            {
                "ad": "📐 CNC G-Code 2D Simülatör",
                "ikon": "📐",
                "baslik": "CNC G-Code 2D Simülatör",
                "kategori": "Mekatronik & İmalat",
                "aciklama": "CNC takım yolu simülatörü, G00/G01 koordinat çözümleyici ve hız optimizasyonu.",
            },
            {
                "ad": "🛡️ Güvenlik",
                "ikon": "🛡️",
                "baslik": "Güvenlik & IPS Savunma Kalkanı",
                "kategori": "Siber Güvenlik & Ağ",
                "aciklama": "Ağ IPS kalkanı, port filtreleme tuzakları, modem güvenlik tarayıcısı ve paket gözetimi.",
            },
            {
                "ad": "🔬 Tersine Mühendislik",
                "ikon": "🔬",
                "baslik": "Tersine Mühendislik & Hex Analizörü",
                "kategori": "İkili Analiz & Güvenlik",
                "aciklama": "Binary hex görüntüleyici, PE header okuyucu, string çıkarıcı ve entropy hesaplayıcı.",
            },
            {
                "ad": "🦠 Antivirüs & EDR",
                "ikon": "🦠",
                "baslik": "Antivirüs & EDR Tehdit Avcısı",
                "kategori": "Uç Nokta Güvenliği (EDR)",
                "aciklama": "Süreç davranış analizi, şüpheli DLL enjeksiyonu algılama ve aktif tehdit bertarafı.",
            },
        ]

    def _arayuz_olustur(self) -> None:
        # Üst Başlık ve Arama Çubuğu
        ust_cerceve = ctk.CTkFrame(self, fg_color="#0D1322", corner_radius=10, border_width=1, border_color="#1E3A8A")
        ust_cerceve.pack(fill="x", padx=14, pady=(14, 8))

        ust_baslik_satir = ctk.CTkFrame(ust_cerceve, fg_color="transparent")
        ust_baslik_satir.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            ust_baslik_satir,
            text="🗂️ ALTAR SEKMELER VE ÇALIŞAN ÖZELLİKLER GEZGİNİ",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            text_color="#38BDF8"
        ).pack(side="left")

        # Kapatma Butonu
        btn_kapat = ctk.CTkButton(
            ust_baslik_satir,
            text="✕ Kapat (ESC)",
            width=95,
            height=26,
            fg_color="#991B1B",
            hover_color="#7F1D1D",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self.destroy
        )
        btn_kapat.pack(side="right")

        # Arama Kutusu
        self.entry_ara = ctk.CTkEntry(
            ust_cerceve,
            placeholder_text="🔍 Sekme veya özellik adı yazarak anında filtreleyin (Örn: Video, Sohbet, Müzik, Kasa, Python, EDR)...",
            font=ctk.CTkFont(family="Consolas", size=12),
            height=34,
            fg_color="#030712",
            border_color="#0284C7"
        )
        self.entry_ara.pack(fill="x", padx=12, pady=(0, 10))
        self.entry_ara.bind("<KeyRelease>", self._filtrele)
        self.entry_ara.focus_set()

        # Kaydırılabilir Kartlar Alanı
        self.scroll_alani = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_alani.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        # İlk Listelemeyi Yap
        self._kartlari_ciz("")

    def _filtrele(self, event=None) -> None:
        kelime = self.entry_ara.get().strip().lower()
        self._kartlari_ciz(kelime)

    def _kartlari_ciz(self, filtre: str) -> None:
        # Önceki kartları temizle
        for w in self.scroll_alani.winfo_children():
            w.destroy()

        # -------------------------------------------------------------
        # 1. BÖLÜM: HARİCİ PENCERE VE ÇALIŞAN UYGULAMA ÖZELLİKLERİ
        # -------------------------------------------------------------
        hariciler = [
            item for item in self._harici_ozellikler
            if not filtre or (filtre in item["baslik"].lower() or filtre in item["kategori"].lower() or filtre in item["aciklama"].lower())
        ]

        if hariciler:
            baslik_frame_1 = ctk.CTkFrame(self.scroll_alani, fg_color="#0A192F", corner_radius=6, height=28)
            baslik_frame_1.pack(fill="x", pady=(4, 6))
            ctk.CTkLabel(
                baslik_frame_1,
                text=f"🚀 UYGULAMA PENCERELERİ & ÇALIŞAN ÖZELLİKLER ({len(hariciler)})",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                text_color="#00FFCC"
            ).pack(side="left", padx=10, pady=3)

            for item in hariciler:
                self._harici_kart_olustur(item)

        # -------------------------------------------------------------
        # 2. BÖLÜM: ALTAR ANA ÇALIŞMA SEKMELERİ (10 TEMEL SEKME)
        # -------------------------------------------------------------
        sekmeler = [
            item for item in self._ana_sekmeler
            if not filtre or (filtre in item["baslik"].lower() or filtre in item["kategori"].lower() or filtre in item["aciklama"].lower())
        ]

        if sekmeler:
            baslik_frame_2 = ctk.CTkFrame(self.scroll_alani, fg_color="#1E1B4B", corner_radius=6, height=28)
            baslik_frame_2.pack(fill="x", pady=(12, 6))
            ctk.CTkLabel(
                baslik_frame_2,
                text=f"📑 ALTAR ANA ÇALIŞMA SEKMELERİ ({len(sekmeler)})",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                text_color="#A78BFA"
            ).pack(side="left", padx=10, pady=3)

            guncel_aktif_sekme = ""
            if hasattr(self.parent, "tabview"):
                try:
                    guncel_aktif_sekme = self.parent.tabview.get()
                except Exception:
                    pass

            for item in sekmeler:
                self._sekme_kart_olustur(item, guncel_aktif_sekme)

    def _harici_kart_olustur(self, item: Dict[str, Any]) -> None:
        pencere = item.get("pencere")
        acik_mi = False
        if pencere:
            try:
                acik_mi = pencere.winfo_exists()
            except Exception:
                acik_mi = False

        kart = ctk.CTkFrame(
            self.scroll_alani,
            fg_color="#0B132B",
            corner_radius=8,
            border_width=1,
            border_color="#10B981" if acik_mi else "#1E3A8A"
        )
        kart.pack(fill="x", pady=3)

        sol = ctk.CTkFrame(kart, fg_color="transparent")
        sol.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        ust_satir = ctk.CTkFrame(sol, fg_color="transparent")
        ust_satir.pack(fill="x")

        ctk.CTkLabel(
            ust_satir,
            text=f"{item['ikon']} {item['baslik']}",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color="#E2E8F0"
        ).pack(side="left")

        ctk.CTkLabel(
            ust_satir,
            text=f"• {item['kategori']}",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#38BDF8"
        ).pack(side="left", padx=8)

        ctk.CTkLabel(
            sol,
            text=item["aciklama"],
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            wraplength=540,
            justify="left"
        ).pack(anchor="w", pady=(3, 0))

        # Sağ Eylem Butonu
        sag = ctk.CTkFrame(kart, fg_color="transparent")
        sag.pack(side="right", padx=12, pady=8)

        if acik_mi:
            btn = ctk.CTkButton(
                sag,
                text="🟢 AÇIK (Öne Al)",
                width=130,
                height=30,
                fg_color="#065F46",
                hover_color="#047857",
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                command=lambda p=pencere: self._harici_one_al(p)
            )
        else:
            btn = ctk.CTkButton(
                sag,
                text="⚪ Başlat / Aç",
                width=130,
                height=30,
                fg_color="#1E293B",
                hover_color="#0284C7",
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                command=lambda act=item["aksiyon"]: self._harici_baslat(act)
            )
        btn.pack()

    def _sekme_kart_olustur(self, item: Dict[str, Any], guncel_sekme: str) -> None:
        aktif_mi = (item["ad"] == guncel_sekme)

        kart = ctk.CTkFrame(
            self.scroll_alani,
            fg_color="#111827",
            corner_radius=8,
            border_width=1,
            border_color="#6366F1" if aktif_mi else "#1F2937"
        )
        kart.pack(fill="x", pady=3)

        sol = ctk.CTkFrame(kart, fg_color="transparent")
        sol.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        ust_satir = ctk.CTkFrame(sol, fg_color="transparent")
        ust_satir.pack(fill="x")

        ctk.CTkLabel(
            ust_satir,
            text=f"{item['ikon']} {item['baslik']}",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color="#F1F5F9" if aktif_mi else "#CBD5E1"
        ).pack(side="left")

        ctk.CTkLabel(
            ust_satir,
            text=f"• {item['kategori']}",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#A78BFA"
        ).pack(side="left", padx=8)

        ctk.CTkLabel(
            sol,
            text=item["aciklama"],
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            wraplength=540,
            justify="left"
        ).pack(anchor="w", pady=(3, 0))

        # Sağ Eylem Butonu
        sag = ctk.CTkFrame(kart, fg_color="transparent")
        sag.pack(side="right", padx=12, pady=8)

        if aktif_mi:
            btn = ctk.CTkButton(
                sag,
                text="🔵 AKTİF SEKME",
                width=130,
                height=30,
                fg_color="#4338CA",
                hover_color="#4F46E5",
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                command=self.destroy
            )
        else:
            btn = ctk.CTkButton(
                sag,
                text="🔘 Geçiş Yap",
                width=130,
                height=30,
                fg_color="#1E293B",
                hover_color="#4F46E5",
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                command=lambda sekme_adi=item["ad"]: self._sekmeye_gec(sekme_adi)
            )
        btn.pack()

    def _harici_one_al(self, pencere: Any) -> None:
        """Açık olan pencereyi ön plana ve odağa alır."""
        try:
            if hasattr(pencere, "deiconify"):
                pencere.deiconify()
            if hasattr(pencere, "lift"):
                pencere.lift()
            if hasattr(pencere, "focus_force"):
                pencere.focus_force()
            if os.name == "nt" and hasattr(pencere, "winfo_id"):
                try:
                    hwnd = pencere.winfo_id()
                    ctypes.windll.user32.BringWindowToTop(hwnd)
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                except Exception:
                    pass
        except Exception:
            pass
        self.destroy()

    def _harici_baslat(self, aksiyon: Optional[Callable[[], Any]]) -> None:
        """Harici özelliği çalıştırır."""
        self.destroy()
        if callable(aksiyon):
            try:
                aksiyon()
            except Exception as e:
                print(f"[!] Özellik başlatma hatası: {e}")

    def _sekmeye_gec(self, sekme_adi: str) -> None:
        """Altar ana sekmesine geçiş yapar ve ilgili paneli odaklar."""
        self.destroy()
        p = self.parent
        if hasattr(p, "tabview"):
            try:
                p.tabview.set(sekme_adi)
                if hasattr(p, "_ust_sekme_degisti"):
                    p._ust_sekme_degisti()
            except Exception as e:
                print(f"[!] Sekme geçiş hatası: {e}")


def sekmeler_gezgini_modal_ac(parent: Any) -> AltarSekmelerVeOzelliklerGezgini:
    """Modül dışından doğrudan çağrılabilecek güvenli başlatıcı."""
    return AltarSekmelerVeOzelliklerGezgini(parent)
