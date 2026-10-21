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

import gc
import math
import json
import time
import re
import ctypes
import subprocess
import threading
import multiprocessing
import importlib.util
from collections import deque
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

# =========================================================
# ARAYÜZ REGEX DESENLERİ VE DONANIM KONTROLLERİ
# =========================================================
_RE_ANY_CODE_BLOCK = re.compile(r'```(.*?)```', re.DOTALL)
_RE_THOUGHT_CLEAN = re.compile(
    r'<(think|düşünce|thought|durum_analizi|kural_denetimi)>.*?</\1>|'
    r'<think>.*?$|'
    r'(?is)^\s*(Thinking Process|Düşünme Süreci|Thought Process):.*?(?:\n\s*\n\s*(?=[A-ZÇĞİÖŞÜa-zçğıöşü])|\Z)',
    re.DOTALL | re.IGNORECASE
)
_RE_GCODE_COMMENT = re.compile(r'\(.*?\)')

if getattr(sys, "frozen", False):
    _ANA_DIZIN = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    if not os.path.exists(os.path.join(_ANA_DIZIN, "Word Programı.py")) and os.path.exists(os.path.join(os.path.dirname(sys.executable), "Word Programı.py")):
        _ANA_DIZIN = os.path.dirname(sys.executable)
else:
    _ANA_DIZIN = os.path.dirname(os.path.abspath(__file__))


def _dinamik_modul_yukle(modul_takma_adi: str, olasi_dosya_adlari: tuple):
    # 1. Önce güncel disk dosyalarından yüklemeyi dene
    aday_dizinler = [_ANA_DIZIN]
    if getattr(sys, "frozen", False):
        exe_dizini = os.path.dirname(sys.executable)
        if exe_dizini not in aday_dizinler:
            aday_dizinler.append(exe_dizini)
        internal_dizini = os.path.join(exe_dizini, "_internal")
        if os.path.isdir(internal_dizini) and internal_dizini not in aday_dizinler:
            aday_dizinler.append(internal_dizini)
        mei = getattr(sys, "_MEIPASS", None)
        if mei and mei not in aday_dizinler:
            aday_dizinler.append(mei)

    for dizin in aday_dizinler:
        for dosya_adi in olasi_dosya_adlari:
            tam_yol = os.path.join(dizin, dosya_adi)
            if os.path.exists(tam_yol):
                try:
                    spec = importlib.util.spec_from_file_location(modul_takma_adi, tam_yol)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    return mod
                except Exception as e:
                    print(f"[!] '{dosya_adi}' yüklenirken uyarı: {e}")

    # 2. Disk üzerinde bulunamazsa derlenmiş Python modülü olarak yükle (PyInstaller PYZ)
    for dosya_adi in olasi_dosya_adlari:
        mod_adi = dosya_adi.replace(".py", "").replace(" ", "_")
        try:
            return importlib.import_module(mod_adi)
        except Exception:
            pass

    return None


# =========================================================
# HARİCİ SEKMELER VE PENCERELER İÇİN MODÜL KÖPRÜLERİ
# =========================================================
try:
    from scraper import NasaScraperWindow
    NASA_SCRAPER_AVAILABLE = True
except ImportError:
    try:
        from nasa_scraper import NasaScraperWindow
        NASA_SCRAPER_AVAILABLE = True
    except ImportError:
        NASA_SCRAPER_AVAILABLE = False

try:
    from uzay_telemetri_merkezi import UzayTelemetriMerkezi
    TELEMETRI_MERKEZI_AVAILABLE = True
except ImportError:
    TELEMETRI_MERKEZI_AVAILABLE = False

try:
    from siber_hex_analizor import SiberHexAnalizor, TersineMuhendislikSekmesi
    SIBER_HEX_AVAILABLE = True
except ImportError:
    SIBER_HEX_AVAILABLE = False
    TersineMuhendislikSekmesi = None

# Güvenlik Duvarı Tuzaklı.py Modül Köprüsü
_gd_mod = _dinamik_modul_yukle("guvenlik_duvari_modulu", ("Guvenlik_Duvari_Tuzakli.py", "Guvenlik_Duvari_Tuzakli", "Güvenlik Duvarı Tuzaklı.py"))
GuvenlikDuvariSekmesi = getattr(_gd_mod, "GuvenlikDuvariSekmesi", None) if _gd_mod else None
gd_sertifika_kur = getattr(_gd_mod, "sertifika_kur", None) if _gd_mod else None
gd_sertifika_kaldir = getattr(_gd_mod, "sertifika_kaldir", None) if _gd_mod else None
gd_fatih_otomatik_koruma = getattr(_gd_mod, "fatih_otomatik_koruma", None) if _gd_mod else None
GUVENLIK_SEKME_AVAILABLE = GuvenlikDuvariSekmesi is not None

# Swansoft 3D CNC Simülatörü Köprüsü
try:
    from Swansoft import SwansoftCNCSekmesi
    SWANSOFT_AVAILABLE = True
except Exception as _sw_err:
    print(f"[!] Swansoft modülü yüklenemedi: {_sw_err}")
    SWANSOFT_AVAILABLE = False
    SwansoftCNCSekmesi = None

# Güvenlik Alt 1. Bölüm: Birleşik Ağ Operasyon Merkezi
try:
    from ag_operasyon_merkezi import AgOperasyonPaneli
    AG_OPERASYON_AVAILABLE = True
except Exception as _ag_err:
    print(f"[!] ag_operasyon_merkezi yüklenemedi: {_ag_err}")
    AG_OPERASYON_AVAILABLE = False
    AgOperasyonPaneli = None

# Güvenlik Alt 2. Bölüm: Dosya Şifreleme Köprüsü
_ds_mod = _dinamik_modul_yukle("dosya_sifreleme_modulu", ("Dosya_Şifreleme.py", "Dosya Şifreleme.py", "dosya_sifreleme.py"))
DosyaSifrelemePaneli = getattr(_ds_mod, "DosyaSifrelemePaneli", None) if _ds_mod else None
DOSYA_SIFRELEME_AVAILABLE = DosyaSifrelemePaneli is not None

# Kazınan Veri & Analiz Merkezi Alt 1. Bölüm: Modem.py (Turbo Hotspot & QoS) Köprüsü
_modem_mod = _dinamik_modul_yukle("modem_hotspot_modulu", ("Modem.py", "modem.py"))
ModemHotspotPaneli = getattr(_modem_mod, "ModemHotspotPaneli", None) if _modem_mod else None
MODEM_PANEL_AVAILABLE = ModemHotspotPaneli is not None

# Kazınan Veri & Analiz Merkezi Alt 2. Bölüm: Port scanner.py (Port & Uygulama Yöneticisi) Köprüsü
_port_mod = _dinamik_modul_yukle("port_scanner_modulu", ("Port scanner.py", "Port_scanner.py", "port_scanner.py"))
PortVeUygulamaPaneli = getattr(_port_mod, "PortVeUygulamaPaneli", None) if _port_mod else None
PORT_PANEL_AVAILABLE = PortVeUygulamaPaneli is not None

# Ses kaydedici.py (Gelişmiş Ses Kayıt Stüdyosu & Hızlı Kaydedici) Köprüsü
_ses_mod = _dinamik_modul_yukle("ses_kaydedici_modulu", ("Ses kaydedici.py", "Ses_kaydedici.py", "ses_kaydedici.py"))
GelismisSesKayitMotoru = getattr(_ses_mod, "GelismisSesKayitMotoru", None) if _ses_mod else None
AltarSesKaydediciPenceresi = getattr(_ses_mod, "AltarSesKaydediciPenceresi", None) if _ses_mod else None
SES_KAYDEDICI_AVAILABLE = GelismisSesKayitMotoru is not None

# Video_Kaydedici.py (Eşzamanlı Ekran + Ses Video Kaydedici) Köprüsü
_vid_mod = _dinamik_modul_yukle("video_kaydedici_modulu", ("Video_Kaydedici.py", "video_kaydedici.py", "Video kaydedici.py"))
GelismisEkranVideoMotoru = getattr(_vid_mod, "GelismisEkranVideoMotoru", None) if _vid_mod else None
AltarVideoKaydediciPenceresi = getattr(_vid_mod, "AltarVideoKaydediciPenceresi", None) if _vid_mod else None
VIDEO_KAYDEDICI_AVAILABLE = GelismisEkranVideoMotoru is not None

# Kamera_Kaydedici.py (Eşzamanlı Webcam Kamera + Ses Kaydedici) Köprüsü
_kam_mod = _dinamik_modul_yukle("kamera_kaydedici_modulu", ("Kamera_Kaydedici.py", "kamera_kaydedici.py", "Kamera kaydedici.py"))
GelismisKameraKayitMotoru = getattr(_kam_mod, "GelismisKameraKayitMotoru", None) if _kam_mod else None
AltarKameraStüdyosuPenceresi = getattr(_kam_mod, "AltarKameraStüdyosuPenceresi", None) if _kam_mod else None
KAMERA_KAYDEDICI_AVAILABLE = GelismisKameraKayitMotoru is not None

# Tersine Mühendislik Alt Paneli (Tek Parça Tam Genişlik): DPI.py Köprüsü
_dpi_mod = _dinamik_modul_yukle("dpi_savunma_modulu", ("DPI.py", "dpi.py"))
DerinPaketAnalizPaneli = getattr(_dpi_mod, "DerinPaketAnalizPaneli", None) if _dpi_mod else None
DPI_PANEL_AVAILABLE = DerinPaketAnalizPaneli is not None

# dosya_gezgini_kasa.py (Dosya Gezgini & Kullanıcı Şifreli Dizin Kasası) Köprüsü
_gezgin_mod = _dinamik_modul_yukle(
    "dosya_gezgini_kasa_modulu",
    ("dosya_gezgini_kasa.py", "Dosya_Gezgini_Kasa.py")
)
DosyaGezginiVeKasaSekmesi = getattr(_gezgin_mod, "DosyaGezginiVeKasaSekmesi", None) if _gezgin_mod else None
DOSYA_GEZGINI_AVAILABLE = DosyaGezginiVeKasaSekmesi is not None

# altar_edr_kalkan.py (5 Katmanlı Antivirüs, EDR & Fidye Kalkanı) Köprüsü
_edr_mod = _dinamik_modul_yukle("altar_edr_kalkan_modulu", ("altar_edr_kalkan.py", "Altar_EDR_Kalkan.py"))
AltarEDRAntivirusSekmesi = getattr(_edr_mod, "AltarEDRAntivirusSekmesi", None) if _edr_mod else None
EDR_KALKAN_AVAILABLE = AltarEDRAntivirusSekmesi is not None

# altar_python_ide.py (Tümleşik Python IDE & Kod Editörü) Köprüsü
_ide_mod = _dinamik_modul_yukle("altar_python_ide_modulu", ("altar_python_ide.py", "Altar_Python_IDE.py"))
AltarPythonIDESekmesi = getattr(_ide_mod, "AltarPythonIDESekmesi", None) if _ide_mod else None
PYTHON_IDE_AVAILABLE = AltarPythonIDESekmesi is not None

# Sohbet Oturumu ve Kalıcılık Yöneticisi Köprüsü
from altar_oturum_yoneticisi import AltarOturumYoneticisi, AltarSohbetOturumlariModal

# Hızlı Komut Paleti (Ctrl+K) Köprüsü
from altar_komut_paleti import AltarKomutPaletiModal

# EDR Güvenli Karantina Kasası Köprüsü
from altar_karantina import AltarKarantinaYoneticisi, AltarKarantinaKasasiModal

# Doğa Açılış Splash Penceresi & Canlı Mavi Alev Animasyon Motoru
from altar_animasyon_motoru import AltarDogaSplashPenceresi, AltarMaviAtesWidget

# Altar Çoklu Tema Motoru (Zümrüt Doğa, Siber Orijinal, Matrix, Cyberpunk)
from altar_tema_motoru import AltarTemaMotoru

# Altar Canlı Ağ Bağlantı Radarı (Salt-Okunur)
from altar_ag_radari import AltarAgRadariModal

try:
    from PIL import Image, ImageGrab
    VISION_AVAILABLE = True
except ImportError:
    ImageGrab = None
    VISION_AVAILABLE = False

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# =========================================================
# WORD PROGRAMI.PY (ALTAR BELGE) BAĞIMSIZ SÜREÇ BAŞLATICI
# =========================================================
def _word_editor_surecini_baslat(baslangic_metni: str = ""):
    """
    PyQt6 tabanlı 'Word Programı.py' (Altar Belge & Canva Sunum Stüdyosu) dosyasını
    bağımsız bir süreçte (Process) 60 FPS sinematik animasyon ve tam ekran (Full Screen)
    olarak başlatır. Kullanıcı tıklamasına gerek kalmadan otomatik ön plan odağı (Foreground Focus) verilir.
    """
    try:
        olasi_isimler = ["Word Programı.py", "word_programi.py", "AltarEditorPro.py"]
        hedef_dosya = None

        olasi_dizinler = [_ANA_DIZIN]
        if getattr(sys, "frozen", False):
            exe_d = os.path.dirname(sys.executable)
            if exe_d not in olasi_dizinler:
                olasi_dizinler.append(exe_d)
            mei = getattr(sys, "_MEIPASS", None)
            if mei and mei not in olasi_dizinler:
                olasi_dizinler.append(mei)

        for dizin in olasi_dizinler:
            for isim in olasi_isimler:
                tam_yol = os.path.join(dizin, isim)
                if os.path.exists(tam_yol):
                    hedef_dosya = tam_yol
                    break
            if hedef_dosya:
                break

        if not hedef_dosya:
            return

        spec = importlib.util.spec_from_file_location("word_programi_modulu", hedef_dosya)
        word_modulu = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(word_modulu)

        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)

        splash = None
        try:
            from altar_canva_sunum import AltarSinematikAcilisPenceresi
            splash = AltarSinematikAcilisPenceresi()
        except Exception as e:
            print(f"[!] Sinematik açılış yükleme uyarısı: {e}")

        pencere = word_modulu.AltarEditorPro()

        if baslangic_metni and baslangic_metni.strip():
            pencere.editor.setPlainText(baslangic_metni)
            pencere.not_defteri.setPlainText(
                f"Bu belge Altar sisteminden ({datetime.now().strftime('%d.%m.%Y %H:%M')}) aktarıldı."
            )

        def _pencereyi_tam_ekran_one_getir():
            pencere.showFullScreen()
            pencere.raise_()
            pencere.activateWindow()
            if os.name == "nt":
                try:
                    import ctypes
                    hwnd = int(pencere.winId())
                    ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                    ctypes.windll.user32.BringWindowToTop(hwnd)
                except Exception:
                    pass

        if splash:
            splash.tamamlandi.connect(_pencereyi_tam_ekran_one_getir)
            splash.showFullScreen()
            splash.raise_()
            splash.activateWindow()
            if os.name == "nt":
                try:
                    import ctypes
                    hwnd_sp = int(splash.winId())
                    ctypes.windll.user32.SetForegroundWindow(hwnd_sp)
                    ctypes.windll.user32.BringWindowToTop(hwnd_sp)
                except Exception:
                    pass
        else:
            _pencereyi_tam_ekran_one_getir()

        sys.exit(app.exec())
    except Exception as e:
        print(f"[!] Altar Belge başlatma hatası: {e}")


# =========================================================
# 64-BİT KORUMALI GPU TELEMETRİ OKUYUCU
# =========================================================
class _NvmlUtilization(ctypes.Structure):
    _fields_ = [("gpu", ctypes.c_uint), ("memory", ctypes.c_uint)]


class SafeGPUReader:
    """64-bit işaretçi (pointer) taşmalarını önlemek için argtypes/restype tanımlı güvenli NVML okuyucu."""
    def __init__(self):
        self.nvml_lib = None
        self.handle = ctypes.c_void_p()
        self.aktif = False
        self._kilit = threading.Lock()
        self._baslat()

    def _baslat(self):
        if os.name != 'nt':
            return
        olasi_dll_yollari = [
            r"C:\Windows\System32\nvml.dll",
            r"C:\Program Files\NVIDIA Corporation\NVSMI\nvml.dll",
            "nvml.dll"
        ]
        for yol in olasi_dll_yollari:
            try:
                lib = ctypes.WinDLL(yol)
                lib.nvmlInit_v2.argtypes = []
                lib.nvmlInit_v2.restype = ctypes.c_int

                lib.nvmlDeviceGetHandleByIndex_v2.argtypes = [ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)]
                lib.nvmlDeviceGetHandleByIndex_v2.restype = ctypes.c_int

                lib.nvmlDeviceGetUtilizationRates.argtypes = [ctypes.c_void_p, ctypes.POINTER(_NvmlUtilization)]
                lib.nvmlDeviceGetUtilizationRates.restype = ctypes.c_int

                if lib.nvmlInit_v2() == 0:
                    if lib.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(self.handle)) == 0:
                        self.nvml_lib = lib
                        self.aktif = True
                        break
            except Exception:
                continue

    def gpu_yuzdesi_oku(self, ollama_client=None) -> int:
        if self.aktif and self.nvml_lib and self.handle:
            try:
                with self._kilit:
                    util = _NvmlUtilization()
                    if self.nvml_lib.nvmlDeviceGetUtilizationRates(self.handle, ctypes.byref(util)) == 0:
                        return int(util.gpu)
            except Exception:
                pass
        return 0


# =========================================================
# AYARLAR PENCERESİ
# =========================================================
class AltarSettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚙ Altar Kontrol Paneli ve Sistem Ayarları")
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        label_title = ctk.CTkLabel(self, text="⚙️ ALT SEVİYE AYARLAR ÇEKİRDEĞİ",
                                   font=ctk.CTkFont(size=16, weight="bold"))
        label_title.pack(pady=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)

        ctk.CTkLabel(self.scroll_frame, text="Hafıza ve RAG Sınırları", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", pady=(15, 0), padx=10)
        self.memory_limit = ctk.CTkOptionMenu(self.scroll_frame,
                                              values=["Son 4 Konuşma", "Son 8 Konuşma", "Sınırsız (VRAM Yoğun)"])
        self.memory_limit.pack(pady=5, padx=20, anchor="w")

        btn_save = ctk.CTkButton(self, text="Sistem Değişikliklerini Kaydet", command=self.destroy)
        btn_save.pack(pady=15)


# =========================================================
# SİMÜLASYONLAR & NASA YARIŞMA MERKEZİ PENCERESİ
# =========================================================
class AltarSimulasyonMerkeziPenceresi(ctk.CTkToplevel):
    """
    Hızlı Kamera Kaydı butonunun yanındaki '🚀 Simülasyonlar' butonuna tıklandığında açılan;
    NASA Yanma Analizi uzmanlık modunu, Canlı 0G/1G Damlacık & d²-Yasası Fizik Simülatörünü,
    Uzay Telemetri & 0G Alev Laboratuvarını (Radar & Alev), NASA Web Veri Seti Kazıyıcısını (Web),
    Kazınan Veri/JSON Arşivini ve 2D/3D CNC Simülatörünü tek merkezde toplayan kontrol penceresi.
    """
    _YAKIT_VERILERI = {
        "n-Heptan (C7H16)": {"k_baz": 0.78, "t_baz": 2180, "soot_baz": 0.65, "renk": "#38BDF8"},
        "Metan (CH4)": {"k_baz": 0.92, "t_baz": 2230, "soot_baz": 0.25, "renk": "#60A5FA"},
        "Etanol (C2H5OH)": {"k_baz": 0.68, "t_baz": 2090, "soot_baz": 0.35, "renk": "#34D399"},
        "Sıvı Hidrojen (LH2)": {"k_baz": 1.35, "t_baz": 2480, "soot_baz": 0.02, "renk": "#A78BFA"},
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("🚀 Altar Simülasyonlar & NASA Yarışma Merkezi")
        self.geometry("1280x800")
        self.minsize(1024, 680)

        # Canlı 0G/1G Damlacık Simülatörü Durum Değişkenleri
        self._sim_aktif = False
        self._sim_zaman = 0.0
        self._sim_faz = 0.0
        self._tam_ekran_mi = True
        self.bind("<F11>", self._tam_ekran_degistir)
        self.bind("<Escape>", self._tam_ekrandan_cik)

        self._arayuz_olustur()
        self.update_idletasks()
        self.after(60, self._tam_ekran_yap)
        self.after(150, self._canli_fizik_ciz)

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

    def _arayuz_olustur(self):
        ust_baslik = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=10, border_width=1, border_color="#1B263B")
        ust_baslik.pack(side="top", fill="x", padx=16, pady=(10, 6))

        sol_baslik_kutu = ctk.CTkFrame(ust_baslik, fg_color="transparent")
        sol_baslik_kutu.pack(side="left", padx=16, pady=8)

        ctk.CTkLabel(
            sol_baslik_kutu,
            text="🚀 ALTAR SİMÜLASYONLAR & NASA YARIŞMA KOMUTA MERKEZİ",
            font=ctk.CTkFont(family="Consolas", size=17, weight="bold"),
            text_color="#00FFCC"
        ).pack(anchor="w")

        ctk.CTkLabel(
            sol_baslik_kutu,
            text="BASS • ACME • Saffire • Canlı d²-Yasası 0G Damlacık Simülatörü • 3D Yörünge • NTRS Kazıyıcı • 2D/3D CNC",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#FFD700"
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            ust_baslik,
            text="✖ Pencereyi Kapat",
            width=140,
            height=34,
            fg_color="#8B0000",
            hover_color="#5C0000",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        ).pack(side="right", padx=16, pady=8)

        ctk.CTkButton(
            ust_baslik,
            text="🗗 Tam Ekran (F11)",
            width=140,
            height=34,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._tam_ekran_degistir
        ).pack(side="right", padx=(0, 8), pady=8)

        # 1. BÖLÜM: NASA YARIŞMASI VE MÜHENDİSLİK SİMÜLASYON BUTONLARI
        araclar_cerceve = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=10, border_width=1, border_color="#30363D")
        araclar_cerceve.pack(side="top", fill="x", padx=16, pady=4)

        ctk.CTkLabel(
            araclar_cerceve,
            text="🛰️ 1. NASA Yarışması & Mühendislik Simülasyon Modülleri (Tıklayarak Tam Ekran Açın):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#58A6FF"
        ).pack(anchor="w", padx=16, pady=(8, 4))

        grid_f = ctk.CTkFrame(araclar_cerceve, fg_color="transparent")
        grid_f.pack(fill="x", padx=12, pady=(2, 8))
        grid_f.grid_columnconfigure(0, weight=1, uniform="sim_cols")
        grid_f.grid_columnconfigure(1, weight=1, uniform="sim_cols")
        grid_f.grid_columnconfigure(2, weight=1, uniform="sim_cols")

        ctk.CTkButton(
            grid_f,
            text="📈 Radar & Alev Laboratuvarı\n(0G/1G Alev • 3D Yörünge • COM Telemetri)",
            height=48,
            fg_color="#00A86B",
            hover_color="#007F50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ac_telemetri_lab
        ).grid(row=0, column=0, sticky="ew", padx=5, pady=4)

        ctk.CTkButton(
            grid_f,
            text="🌐 NASA Web & Veri Kazıyıcı\n(NTRS • Glenn • Canlı Veri Seti İzleme)",
            height=48,
            fg_color="#FF4500",
            hover_color="#8B0000",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ac_nasa_web_kaziyici
        ).grid(row=0, column=1, sticky="ew", padx=5, pady=4)

        ctk.CTkButton(
            grid_f,
            text="📊 Kazınan Veri & Analiz Merkezi\n(Kategorize Tablo, Makale & RAG İnceleme)",
            height=48,
            fg_color="#1f538d",
            hover_color="#14375e",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ac_analiz_sekmesi
        ).grid(row=0, column=2, sticky="ew", padx=5, pady=4)

        ctk.CTkButton(
            grid_f,
            text="📂 SSD Arşivinden JSON Yükle\n(Kazınmış NASA Veri Setlerini Aç)",
            height=46,
            fg_color="#4B0082",
            hover_color="#2b004d",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ac_ssd_json
        ).grid(row=1, column=0, sticky="ew", padx=5, pady=4)

        ctk.CTkButton(
            grid_f,
            text="📐 CNC G-Code 2D & Swansoft 3D\n(Takım Yolu & Katı Model Simülatörü)",
            height=46,
            fg_color="#008080",
            hover_color="#005959",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ac_cnc_simulator
        ).grid(row=1, column=1, sticky="ew", padx=5, pady=4)

        ctk.CTkButton(
            grid_f,
            text="🛡️ Siber Hex & Binary Analizör\n(01 -> Kod & Tersine Mühendislik)",
            height=46,
            fg_color="#6A0DAD",
            hover_color="#4B0082",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ac_siber_hex
        ).grid(row=1, column=2, sticky="ew", padx=5, pady=4)

        # 2. BÖLÜM: İKİ SÜTUNLU ALT GÖVDE (SOL: SENARYOLAR & AI | SAĞ: CANLI d²-YASASI FİZİK SİMÜLATÖRÜ)
        alt_govde = ctk.CTkFrame(self, fg_color="transparent")
        alt_govde.pack(side="top", fill="both", expand=True, padx=16, pady=(4, 12))
        alt_govde.grid_columnconfigure(0, weight=11, uniform="alt_sim")
        alt_govde.grid_columnconfigure(1, weight=11, uniform="alt_sim")
        alt_govde.grid_rowconfigure(0, weight=1)

        # --- SOL KART: NASA YANMA ANALİZİ UZMANLIK MODU VE HAZIR DENEY SENARYOLARI ---
        yanma_cerceve = ctk.CTkFrame(alt_govde, fg_color="#121824", corner_radius=10, border_width=1, border_color="#1E293B")
        yanma_cerceve.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(
            yanma_cerceve,
            text="🔥 2A. NASA Mikro Yerçekimi Yanma Analizi (BASS / ACME / Saffire):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FF9F1C"
        ).pack(anchor="w", padx=14, pady=(8, 2))

        ctk.CTkLabel(
            yanma_cerceve,
            text=(
                "• ISS Kural 1: Halon yasaktır; İnce Su Sisi (Fine Water Mist) veya CO2 kullanılır.\n"
                "• ISS Kural 2: Kapalı modülde O2 artışı fan açıldığını veya O2 sızıntısını gösterir.\n"
                "• ISS Kural 3: O2 < %18 altında eksik yanma, küresel İS (Soot) kabuğu ve CO oluşur."
            ),
            justify="left",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#A3B8CC"
        ).pack(anchor="w", padx=14, pady=(0, 6))

        senaryo_bar = ctk.CTkFrame(yanma_cerceve, fg_color="transparent")
        senaryo_bar.pack(fill="x", padx=10, pady=2)
        senaryo_bar.grid_columnconfigure(0, weight=1, uniform="sen_cols")
        senaryo_bar.grid_columnconfigure(1, weight=1, uniform="sen_cols")

        senaryolar = [
            (
                "🧪 Senaryo 1: ISS O2 Artışı & Sızıntı",
                "ISS kapalı yanma modülünde deney sırasında sıcaklık 620 K iken Oksijen (O2) oranı %20.8'den %23.4'e yükseldi ve CO 45 ppm ölçüldü. Bu telemetri anomalisini NASA BASS/Saffire kurallarına göre analiz et ve müdahale protokolünü yaz."
            ),
            (
                "🔥 Senaryo 2: 0G Düşük O2 & Soot/CO",
                "Mikro yerçekiminde (0G) gerçekleşen heptan damlacık yanmasında O2 seviyesi %16.2'ye düştü, alev etrafında sarı/turuncu halka ve 380 ppm CO tespit edildi. Küresel difüzyon, Soot (is) kabuğu ve eksik yanma fiziğini analiz et."
            ),
            (
                "🚿 Senaryo 3: ISS Yangın Söndürme",
                "Uluslararası Uzay İstasyonu (ISS) aviyonik kabininde başlayan elektrik kaynaklı yangında neden Halon kullanılmadığını ve İnce Su Sisi (Fine Water Mist) ile CO2 söndürme protokolünün adım adım uygulanışını raporla."
            ),
            (
                "🛰️ Senaryo 4: Saffire Radyatif Isı",
                "NASA Saffire ve ACME deneylerinde mikro yerçekiminde kaldırma kuvveti (buoyancy) yokluğunda alev yayılım hızı, stokiyometrik oran ve radyatif ısı kaybı mekanizmalarını bilimsel olarak analiz et."
            )
        ]

        for idx, (etiket, metin) in enumerate(senaryolar):
            r, c = divmod(idx, 2)
            ctk.CTkButton(
                senaryo_bar,
                text=etiket,
                height=32,
                fg_color="#374151",
                hover_color="#1F2937",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda m=metin: self._senaryo_doldur(m)
            ).grid(row=r, column=c, sticky="ew", padx=4, pady=3)

        self.txt_nasa_soru = ctk.CTkTextbox(
            yanma_cerceve,
            height=95,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#090D16",
            text_color="#00FFCC",
            border_width=1,
            border_color="#30363D"
        )
        self.txt_nasa_soru.pack(fill="both", expand=True, padx=14, pady=(6, 8))
        self.txt_nasa_soru.insert(
            "1.0",
            "ISS kapalı yanma modülünde sıcaklık 640 K, O2 %17.1, CO 410 ppm ve fan hızı 0 RPM ölçüldü. Mikro yerçekimi alev fiziğini ve ISS acil müdahale protokolünü analiz et."
        )

        alt_aksiyon = ctk.CTkFrame(yanma_cerceve, fg_color="transparent")
        alt_aksiyon.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkButton(
            alt_aksiyon,
            text="🔥 AI İle Şimdi Analiz Et",
            height=38,
            fg_color="#C62828",
            hover_color="#8E0000",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._nasa_analizi_gonder
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            alt_aksiyon,
            text="📄 Jüri Raporunu Altar Belge'de Aç",
            height=38,
            fg_color="#008080",
            hover_color="#005959",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._juri_raporu_olustur
        ).pack(side="right", padx=(4, 0))

        # --- SAĞ KART: CANLI 0G/1G DAMLACIK YANMA & d²-YASASI FİZİK SİMÜLATÖRÜ ---
        fizik_cerceve = ctk.CTkFrame(alt_govde, fg_color="#121824", corner_radius=10, border_width=1, border_color="#1E293B")
        fizik_cerceve.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ctk.CTkLabel(
            fizik_cerceve,
            text="🔬 2B. Canlı 0G/1G Damlacık Yanma & d²-Yasası Fizik Simülatörü:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#00E5FF"
        ).pack(anchor="w", padx=14, pady=(8, 4))

        kontrol_grid = ctk.CTkFrame(fizik_cerceve, fg_color="#0B1320", corner_radius=8)
        kontrol_grid.pack(fill="x", padx=12, pady=2)
        kontrol_grid.grid_columnconfigure(1, weight=1)
        kontrol_grid.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(kontrol_grid, text="Yakıt:", font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=0, column=0, padx=(8, 4), pady=4, sticky="w"
        )
        self.yakit_var = ctk.StringVar(value="n-Heptan (C7H16)")
        ctk.CTkOptionMenu(
            kontrol_grid,
            variable=self.yakit_var,
            values=list(self._YAKIT_VERILERI.keys()),
            width=145,
            height=24,
            font=ctk.CTkFont(size=11),
            command=lambda _: self._parametreyi_yenile()
        ).grid(row=0, column=1, padx=4, pady=4, sticky="w")

        self.lbl_yercekimi = ctk.CTkLabel(
            kontrol_grid, text="Yerçekimi: 0.00g (0G)", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#00FFCC"
        )
        self.lbl_yercekimi.grid(row=0, column=2, padx=6, pady=4, sticky="w")
        self.slider_g = ctk.CTkSlider(
            kontrol_grid, from_=0.0, to=1.0, number_of_steps=20, width=120, command=lambda _: self._parametreyi_yenile()
        )
        self.slider_g.set(0.0)
        self.slider_g.grid(row=0, column=3, padx=(2, 8), pady=4, sticky="ew")

        self.lbl_o2 = ctk.CTkLabel(
            kontrol_grid, text="Oksijen: %21.0", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#FFD700"
        )
        self.lbl_o2.grid(row=1, column=0, columnspan=2, padx=8, pady=4, sticky="w")
        self.slider_o2 = ctk.CTkSlider(
            kontrol_grid, from_=14.0, to=35.0, number_of_steps=42, width=130, command=lambda _: self._parametreyi_yenile()
        )
        self.slider_o2.set(21.0)
        self.slider_o2.grid(row=1, column=1, padx=(85, 4), pady=4, sticky="ew")

        self.lbl_cap = ctk.CTkLabel(
            kontrol_grid, text="Çap (d₀): 2.5 mm", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#FF9F1C"
        )
        self.lbl_cap.grid(row=1, column=2, padx=6, pady=4, sticky="w")
        self.slider_d0 = ctk.CTkSlider(
            kontrol_grid, from_=1.0, to=4.0, number_of_steps=30, width=120, command=lambda _: self._parametreyi_yenile()
        )
        self.slider_d0.set(2.5)
        self.slider_d0.grid(row=1, column=3, padx=(2, 8), pady=4, sticky="ew")

        self.sim_canvas = tk.Canvas(
            fizik_cerceve, bg="#050811", height=195, highlightthickness=1, highlightbackground="#1E293B"
        )
        self.sim_canvas.pack(fill="both", expand=True, padx=12, pady=6)
        self.sim_canvas.bind("<Configure>", lambda _: self._canli_fizik_ciz())

        sim_buton_bar = ctk.CTkFrame(fizik_cerceve, fg_color="transparent")
        sim_buton_bar.pack(fill="x", padx=12, pady=(0, 10))

        self.btn_sim_baslat = ctk.CTkButton(
            sim_buton_bar,
            text="▶️ Canlı Simülasyonu Başlat",
            height=36,
            fg_color="#00A86B",
            hover_color="#007F50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._sim_baslat_durdur
        )
        self.btn_sim_baslat.pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            sim_buton_bar,
            text="🔄 Sıfırla",
            width=80,
            height=36,
            fg_color="#374151",
            hover_color="#1F2937",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._sim_sifirla
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            sim_buton_bar,
            text="🤖 Simülasyon Verilerini Senaryoya Aktar",
            height=36,
            fg_color="#1f538d",
            hover_color="#14375e",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._sim_verilerini_senaryoya_aktar
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

    def _hesapla_yanma_parametreleri(self) -> dict:
        yakit = self.yakit_var.get()
        bilgi = self._YAKIT_VERILERI.get(yakit, self._YAKIT_VERILERI["n-Heptan (C7H16)"])
        g_val = float(self.slider_g.get())
        o2_val = float(self.slider_o2.get())
        d0_val = float(self.slider_d0.get())

        # Oksijen ve yerçekimine bağlı yanma sabiti K (mm²/s) - Grashof doğal konveksiyon katkısı
        o2_faktor = max(0.0, (o2_val - 13.5) / 7.5)
        konveksiyon_faktor = 1.0 + 0.38 * (g_val ** 0.5)
        k_sabiti = round(bilgi["k_baz"] * (o2_faktor ** 0.65) * konveksiyon_faktor, 3) if o2_val >= 14.8 else 0.0
        sonme_var = o2_val < 15.0 or k_sabiti <= 0.01

        t_alev = int(bilgi["t_baz"] * (0.78 + 0.22 * min(o2_val / 21.0, 1.5)) - (110 if g_val < 0.1 else 0))
        if sonme_var:
            t_alev = 310

        tb_suresi = round((d0_val ** 2) / max(k_sabiti, 0.01), 2) if not sonme_var else 0.0
        soot_indeks = min(100, int(bilgi["soot_baz"] * 100 * (1.35 if g_val < 0.15 else 0.85) * (21.0 / max(o2_val, 14.0))))
        co_ppm = int(soot_indeks * (5.2 if o2_val < 18.0 else 1.4))

        return {
            "yakit": yakit,
            "g": g_val,
            "o2": o2_val,
            "d0": d0_val,
            "k": k_sabiti,
            "t_alev": t_alev,
            "tb": tb_suresi,
            "soot": soot_indeks,
            "co_ppm": co_ppm,
            "sonme": sonme_var,
            "renk": bilgi["renk"]
        }

    def _parametreyi_yenile(self):
        g_val = float(self.slider_g.get())
        o2_val = float(self.slider_o2.get())
        d0_val = float(self.slider_d0.get())
        ortam = "0G ISS" if g_val < 0.05 else ("Ay" if g_val < 0.25 else ("Mars" if g_val < 0.45 else "Dünya"))
        self.lbl_yercekimi.configure(text=f"Yerçekimi: {g_val:.2f}g ({ortam})")
        self.lbl_o2.configure(text=f"Oksijen: %{o2_val:.1f}")
        self.lbl_cap.configure(text=f"Çap (d₀): {d0_val:.1f} mm")
        self._canli_fizik_ciz()

    def _sim_baslat_durdur(self):
        self._sim_aktif = not self._sim_aktif
        if self._sim_aktif:
            self.btn_sim_baslat.configure(text="⏸️ Duraklat", fg_color="#D97706", hover_color="#B45309")
            self._sim_dongusu()
        else:
            self.btn_sim_baslat.configure(text="▶️ Canlı Simülasyonu Başlat", fg_color="#00A86B", hover_color="#007F50")

    def _sim_sifirla(self):
        self._sim_aktif = False
        self._sim_zaman = 0.0
        self.btn_sim_baslat.configure(text="▶️ Canlı Simülasyonu Başlat", fg_color="#00A86B", hover_color="#007F50")
        self._canli_fizik_ciz()

    def _sim_dongusu(self):
        if not self._sim_aktif or not self.winfo_exists():
            return
        p = self._hesapla_yanma_parametreleri()
        if not p["sonme"] and p["tb"] > 0:
            self._sim_zaman += 0.08
            if self._sim_zaman >= p["tb"]:
                self._sim_zaman = 0.0
        self._sim_faz += 0.35
        self._canli_fizik_ciz()
        self.after(60, self._sim_dongusu)

    def _canli_fizik_ciz(self):
        if not hasattr(self, "sim_canvas") or not self.sim_canvas.winfo_exists():
            return
        c = self.sim_canvas
        c.delete("all")
        w = max(c.winfo_width(), 520)
        h = max(c.winfo_height(), 190)
        p = self._hesapla_yanma_parametreleri()

        # Sol Yarı: 0G Küresel vs 1G Konvektif Damlacık Yanma Görselleştirmesi
        sol_merkez_x = int(w * 0.23)
        sol_merkez_y = int(h * 0.54)
        c.create_line(int(w * 0.46), 10, int(w * 0.46), h - 10, fill="#1E293B", width=1, dash=(3, 3))

        d0 = p["d0"]
        k = p["k"]
        t = min(self._sim_zaman, p["tb"]) if p["tb"] > 0 else 0.0
        d_kare = max(0.0, (d0 ** 2) - k * t)
        anlik_d = math.sqrt(d_kare)

        c.create_text(
            sol_merkez_x, 16,
            text="0G KÜRESEL DIFÜZYON ALEVİ" if p["g"] < 0.1 else f"{p['g']:.2f}G KONVEKTİF ALEV",
            fill="#00FFCC", font=("Consolas", 10, "bold")
        )

        if p["sonme"]:
            c.create_oval(
                sol_merkez_x - 18, sol_merkez_y - 18, sol_merkez_x + 18, sol_merkez_y + 18,
                fill="#475569", outline="#94A3B8", width=2
            )
            c.create_text(
                sol_merkez_x, sol_merkez_y + 38,
                text="⚠️ KRİTİK O2 ALTINDA ALEV SÖNDÜ (LOC)",
                fill="#FF4444", font=("Consolas", 9, "bold")
            )
        else:
            titresim = 2.0 * math.sin(self._sim_faz)
            alev_r = max(14.0, (anlik_d / d0) * 48.0 + titresim)
            uzama_ust = p["g"] * 34.0

            # Dış mavi reaksiyon zonu
            c.create_oval(
                sol_merkez_x - alev_r,
                sol_merkez_y - alev_r - uzama_ust,
                sol_merkez_x + alev_r,
                sol_merkez_y + alev_r * (1.0 - 0.25 * p["g"]),
                outline=p["renk"], width=3
            )
            # İç sarı/turuncu İS (Soot) kabuğu
            if p["soot"] > 15:
                soot_r = alev_r * 0.68
                soot_renk = "#F59E0B" if p["o2"] < 18.5 else "#FBBF24"
                c.create_oval(
                    sol_merkez_x - soot_r,
                    sol_merkez_y - soot_r - uzama_ust * 0.6,
                    sol_merkez_x + soot_r,
                    sol_merkez_y + soot_r * 0.85,
                    outline=soot_renk, width=2, dash=(4, 2)
                )
            # Merkezdeki sıvı yakıt damlacığı
            damla_r = max(3.0, (anlik_d / 4.0) * 20.0)
            c.create_oval(
                sol_merkez_x - damla_r, sol_merkez_y - damla_r,
                sol_merkez_x + damla_r, sol_merkez_y + damla_r,
                fill="#E2E8F0", outline="#38BDF8", width=1.5
            )
            c.create_text(
                sol_merkez_x, h - 15,
                text=f"Anlık Çap d(t): {anlik_d:.2f} mm | t = {t:.1f}/{p['tb']:.1f} sn",
                fill="#A3B8CC", font=("Consolas", 9)
            )

        # Sağ Yarı: d²-Yasası Grafiği (d² = d0² - K*t) ve Telemetri Özeti
        gx0 = int(w * 0.51)
        gy0 = h - 32
        gx1 = int(w * 0.96)
        gy1 = 32
        gw = max(gx1 - gx0, 80)
        gh = max(gy0 - gy1, 60)

        c.create_text(
            (gx0 + gx1) // 2, 15,
            text=f"d²-YASASI GRAFİĞİ (K={p['k']:.2f} mm²/s | Tf={p['t_alev']} K)",
            fill="#FFD700", font=("Consolas", 10, "bold")
        )
        c.create_line(gx0, gy0, gx1, gy0, fill="#64748B", width=1.5)
        c.create_line(gx0, gy0, gx0, gy1, fill="#64748B", width=1.5)
        c.create_text(gx0 - 14, gy1 + 4, text="d²", fill="#94A3B8", font=("Consolas", 9, "bold"))
        c.create_text(gx1 - 10, gy0 + 12, text="t(s)", fill="#94A3B8", font=("Consolas", 8))

        if not p["sonme"] and p["tb"] > 0:
            c.create_line(gx0, gy1 + 6, gx1 - 8, gy0, fill="#00FF88", width=2.5)
            oran = min(1.0, max(0.0, t / p["tb"]))
            px = gx0 + oran * (gx1 - 8 - gx0)
            py = (gy1 + 6) + oran * (gy0 - (gy1 + 6))
            c.create_oval(px - 5, py - 5, px + 5, py + 5, fill="#FF3366", outline="#FFFFFF")

        bilgi_metni = f"Soot İndeksi: %{p['soot']}  |  Tahmini CO: {p['co_ppm']} ppm  |  Yanma Süresi: {p['tb']} s"
        c.create_text((gx0 + gx1) // 2, h - 12, text=bilgi_metni, fill="#00E5FF", font=("Consolas", 9, "bold"))

    def _sim_verilerini_senaryoya_aktar(self):
        p = self._hesapla_yanma_parametreleri()
        durum = "kritik oksijen sınırının altında sönme (LOC)" if p["sonme"] else "aktif difüzyon yanması"
        metin = (
            f"NASA Mikroçekim Damlacık Yanma Deneyi ({p['yakit']}): "
            f"Yerçekimi {p['g']:.2f}g, Oksijen %{p['o2']:.1f}, Başlangıç Çapı d0={p['d0']:.1f} mm. "
            f"Hesaplanan d²-yasası yanma hızı sabiti K={p['k']:.3f} mm²/s, Alev Sıcaklığı Tf={p['t_alev']} K, "
            f"Tam yanma süresi tb={p['tb']} sn, Soot (is) indeksi %{p['soot']}, CO emisyonu {p['co_ppm']} ppm ({durum}). "
            f"Bu deney verilerini NASA BASS/ACME/Saffire standartlarına göre bilimsel olarak analiz et."
        )
        self._senaryo_doldur(metin)

    def _juri_raporu_olustur(self):
        p = self._hesapla_yanma_parametreleri()
        senaryo_metni = self.txt_nasa_soru.get("1.0", "end-1c").strip()
        rapor = (
            "========================================================================\n"
            "      NASA UZAY YANMA & MİKROÇEKİM SİMÜLASYON JÜRİ TEKNİK RAPORU\n"
            "========================================================================\n"
            f"Rapor Tarihi        : {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"Test Edilen Yakıt   : {p['yakit']}\n"
            f"Yerçekimi İvmesi    : {p['g']:.2f} g\n"
            f"Ortam Oksijen Oranı : %{p['o2']:.1f}\n"
            f"Damlacık Çapı (d0)  : {p['d0']:.2f} mm\n"
            "------------------------------------------------------------------------\n"
            "1. HESAPLANAN d²-YASASI VE TERMODİNAMİK PARAMETRELER\n"
            f"   • Yanma Hızı Sabiti (K)     : {p['k']:.3f} mm²/s\n"
            f"   • Alev Sıcaklığı (Tf)       : {p['t_alev']} K\n"
            f"   • Tam Yanma Süresi (tb)     : {p['tb']} sn\n"
            f"   • İS (Soot) Kabuk İndeksi   : %{p['soot']}\n"
            f"   • Tahmini CO Birikimi       : {p['co_ppm']} ppm\n"
            "------------------------------------------------------------------------\n"
            "2. DENEY SENARYOSU VE MÜDAHALE PROTOKOLÜ NOTU\n"
            f"{senaryo_metni}\n"
            "========================================================================\n"
        )
        p_proc = multiprocessing.Process(target=_word_editor_surecini_baslat, args=(rapor,), daemon=True)
        p_proc.start()

    def _senaryo_doldur(self, metin: str):
        self.txt_nasa_soru.delete("1.0", "end")
        self.txt_nasa_soru.insert("1.0", metin)

    def _nasa_analizi_gonder(self):
        soru = self.txt_nasa_soru.get("1.0", "end-1c").strip()
        if not soru:
            messagebox.showwarning("Uyarı", "Lütfen analiz edilecek NASA yanma/telemetri sorusunu yazın.", parent=self)
            return
        self.parent.nasa_yanma_analizi_calistir(soru)

    def _ac_telemetri_lab(self):
        self.parent.telemetri_merkezini_ac()

    def _ac_nasa_web_kaziyici(self):
        self.parent.toggle_nasa_sim()

    def _ac_analiz_sekmesi(self):
        self.parent.tabview.set("📊 Kazınan Veri & Analiz Merkezi")
        self.parent._ust_sekme_degisti()
        self.destroy()

    def _ac_ssd_json(self):
        self.parent.tabview.set("📊 Kazınan Veri & Analiz Merkezi")
        self.parent._ust_sekme_degisti()
        self.parent.ssd_arsivinden_json_yukle()

    def _ac_cnc_simulator(self):
        self.parent.tabview.set("📐 CNC G-Code 2D Simülatör")
        self.parent._ust_sekme_degisti()
        self.destroy()

    def _ac_siber_hex(self):
        self.parent.siber_hex_merkezini_ac()


# =========================================================
# ANA ARAYÜZ SINIFI (Local AI.py Tarafından Miras Alınır)
# =========================================================
class AltarArayuzMerkezi(ctk.CTk):
    """
    Altar'ın tüm görsel tasarımını, 7 ana sekmesini, alt panellerini,
    multimedya (Ses/Video/Kamera) butonlarını, 2D/3D CNC simülatörünü
    ve 55ms merkezi UI döngüsünü eksiksiz barındıran arayüz sınıfı.
    """
    def __init__(self):
        super().__init__()
        self.title(" " * 85 + "Altar")
        self.geometry("1250x780")
        self.minsize(1050, 680)
        self.protocol("WM_DELETE_WINDOW", self._uygulamayi_guvenli_kapat)

        # Alt sınıf (AltarMainUI) tarafından doldurulan varsayılan motor nitelikleri
        self.yuklu_modeller = ["jaahas/qwen3.5-uncensored:9b"]
        self._secili_yerel_model_bellek = "jaahas/qwen3.5-uncensored:9b"
        self.api_modeller = ["API Modelleri Taranıyor..."]
        self.api_engine = None
        self.client = None
        self.db_manager = None
        self.gecmis = []

        self.ekli_resim_yolu = None
        self.nasa_sim_aktif = False
        self.son_kazinan_paket = None
        self.gpu_reader = SafeGPUReader()
        self.ses_kayit_motoru = GelismisSesKayitMotoru() if SES_KAYDEDICI_AVAILABLE else None
        self.ekran_video_motoru = GelismisEkranVideoMotoru() if VIDEO_KAYDEDICI_AVAILABLE else None
        self.kamera_video_motoru = GelismisKameraKayitMotoru() if KAMERA_KAYDEDICI_AVAILABLE else None

        # Donanım Klavye & Fare Çift Kilit Kalkanı
        self._kilit_servisi = None
        try:
            from altar_klavye_kilit import klavye_kalkanini_baslat
            self._kilit_servisi = klavye_kalkanini_baslat()
            if self._kilit_servisi:
                self._kilit_servisi.durum_callback_kaydet(self._guvenli_kilit_butonu_guncelle)
        except Exception:
            pass

        # Merkezi Thread-Safe Kuyruklar ve Yükleme Bayrakları
        self._chat_tamponu = deque()
        self._ui_gorev_kuyrugu = deque()
        self._chat_kilit = threading.Lock()
        self._gcode_yuklendi = False
        self._guvenlik_yuklendi = False
        self._tersine_yuklendi = False
        self._analiz_alt_yuklendi = False
        self._gezgin_yuklendi = False
        self._edr_yuklendi = False
        self._ide_yuklendi = False
        self.yapay_zeka_aktif = False  # Başlangıçta RAM ve pil tasarrufu için kapalı başlar
        self.sesli_yanit_aktif = False  # Çevrimdışı Türkçe sesli yanıt (TTS) durumu
        self._tts_proc = None
        self.btn_ai_guc = None

        # Dinamik Sekme Panelleri Referansları
        self.edr_panel = None
        self.gezgin_panel = None
        self.ide_panel = None
        self.swansoft_panel = None
        self.guvenlik_panel = None
        self.tersine_muh_panel = None
        self.sol_ag_bolumu = None
        self.sag_sifreleme_bolumu = None
        self.sol_modem_bolumu = None
        self.sag_port_bolumu = None
        self.dpi_tam_panel = None
        self._aktif_pencereler = {}
        self.sinematik_arka_plan = None

        # Sohbet Oturumları ve Kalıcılık Yöneticisi
        self.oturum_yoneticisi = AltarOturumYoneticisi(_ANA_DIZIN)
        self.aktif_oturum_id = self.oturum_yoneticisi.aktif_oturum_id_getir()
        if not self.aktif_oturum_id:
            ilk_oturum = self.oturum_yoneticisi.yeni_oturum_olustur("Genel Sohbet")
            self.aktif_oturum_id = ilk_oturum["id"]

        # Karantina Kasası Yöneticisi
        self.karantina_yoneticisi = AltarKarantinaYoneticisi(_ANA_DIZIN)

        # Açılış Doğa & Şelale Animasyonu için ana pencereyi başlangıçta gizle
        self.withdraw()
        self.after(50, self._doga_splash_baslat)

        # Tam Ekran Yönetimi ve Kısayollar (F11: Tam Ekran Aç/Kapat, Esc: Tam Ekrandan Çık)
        self._tam_ekran_mi = True
        self.bind_all("<F11>", self._tam_ekran_degistir)
        self.bind_all("<Escape>", self._tam_ekrandan_cik)

        # Dinamik Font Boyutu & Hızlı Komut Paleti Kısayolları (Ctrl+K)
        self._chat_font_boyutu = 14
        self.bind_all("<Control-k>", lambda _: self.komut_paletini_ac())
        self.bind_all("<Control-K>", lambda _: self.komut_paletini_ac())

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _doga_splash_baslat(self):
        """Karanlıktan zümrüt yeşili doğaya ve şelaleye açılan görsel açılış animasyonunu başlatır."""
        try:
            AltarDogaSplashPenceresi(self, tamamlandi_callback=self._doga_splash_bitti)
        except Exception as e:
            self._doga_splash_bitti()

    def _doga_splash_bitti(self):
        """Açılış animasyonu bittiğinde ana pencereyi güvenle gösterip doğrudan tam ekran ve aktif ön plan yapar."""
        try:
            if self.winfo_exists():
                self.deiconify()
                self._pencereyi_tam_ekran_yap()
                self.lift()
                self.attributes("-topmost", True)
                self.attributes("-topmost", False)
                self.focus_force()
                if sys.platform == "win32":
                    try:
                        hwnd = self.winfo_id()
                        user32 = ctypes.windll.user32
                        parent = user32.GetParent(hwnd)
                        target = parent if parent else hwnd
                        user32.ShowWindow(target, 5)  # SW_SHOW
                        user32.BringWindowToTop(target)
                        user32.SetForegroundWindow(target)
                    except Exception:
                        pass
                self.after(50, self._pencereyi_tam_ekran_yap)
        except Exception:
            pass

    def _sinematik_animasyon_oynat(self):
        """Kullanıcının menüden veya komut paletinden sinematik doğa animasyonunu tekrar izlemesini sağlar."""
        try:
            self.withdraw()
            AltarDogaSplashPenceresi(self, tamamlandi_callback=self._doga_splash_bitti)
        except Exception as e:
            self._doga_splash_bitti()

    def ag_radarini_ac(self):
        """Aktif sistem TCP/UDP bağlantılarını salt-okunur gösteren radar modalını açar."""
        try:
            win_rad = AltarAgRadariModal(self)
            self._aktif_pencereler["radar"] = win_rad
        except Exception as e:
            messagebox.showwarning("Ağ Radarı", f"Ağ radarı açılırken uyarı: {e}", parent=self)


    # =========================================================================
    # YENİ MODÜLLER: OYUN MERKEZİ, MÜZİK & SİNEMATİK SAHNE, VİDEO & OLLAMA KURUCU
    # =========================================================================
    def _oyun_sekmesini_tekil_hazirla(self):
        """Python ile tasarlanan siber oyun merkezini sekmeye yükler."""
        try:
            from altar_oyun_merkezi import AltarOyunMerkezi
            self.oyun_paneli = AltarOyunMerkezi(self.tab_oyun)
            self.oyun_paneli.pack(fill="both", expand=True)
        except Exception as e:
            ctk.CTkLabel(
                self.tab_oyun,
                text=f"Oyun Merkezi Yüklenemedi:\n{e}",
                font=ctk.CTkFont(family="Consolas", size=13),
                text_color="#FF3333"
            ).pack(expand=True)

    def _muzik_sekmesini_tekil_hazirla(self):
        """YouTube/Yerel Müzik ve Sinematik Animasyon Sahnesini sekmeye yükler."""
        try:
            from altar_muzik_merkezi import AltarMuzikMerkezi
            self.muzik_paneli = AltarMuzikMerkezi(self.tab_muzik)
            self.muzik_paneli.pack(fill="both", expand=True)
        except Exception as e:
            ctk.CTkLabel(
                self.tab_muzik,
                text=f"Müzik Merkezi Yüklenemedi:\n{e}",
                font=ctk.CTkFont(family="Consolas", size=13),
                text_color="#FF3333"
            ).pack(expand=True)

    def oyun_merkezini_ac(self):
        """Oyun sekmesine geçer veya oyun merkezini odaklar."""
        for tab_name in ["🎮 Oyun", "Oyun"]:
            try:
                self.tabview.set(tab_name)
                self._ust_sekme_degisti()
                return
            except Exception:
                pass

    def muzik_merkezini_ac(self):
        """Müzik sekmesine geçer veya müzik sahnesini odaklar."""
        for tab_name in ["🎵 Müzik", "Müzik"]:
            try:
                self.tabview.set(tab_name)
                self._ust_sekme_degisti()
                return
            except Exception:
                pass

    def acik_sekmeler_gezgini_ac(self):
        """Altar sekmelerini ve çalışan tüm harici özellikleri listeleyen gezgin modalını açar."""
        try:
            from altar_sekmeler_gezgini import sekmeler_gezgini_modal_ac
            return sekmeler_gezgini_modal_ac(self)
        except Exception as e:
            messagebox.showerror("Hata", f"Sekmeler gezgini açılamadı:\n{e}", parent=self)

    def sinematik_video_sec_ve_oynat(self):
        """Kullanıcıdan MP4/video seçtirip Altar Sinematik Oynatıcı ile tam ekranda açar."""
        from tkinter import filedialog
        dosya = filedialog.askopenfilename(
            parent=self,
            title="Sinematik Oynatılacak Video Seçin",
            filetypes=[("Video Dosyaları", "*.mp4 *.mkv *.avi *.mov"), ("Tüm Dosyalar", "*.*")]
        )
        if dosya:
            try:
                from altar_video_oynatici import sinematik_video_oynat
                win = sinematik_video_oynat(dosya, parent=self)
                if win:
                    self._aktif_pencereler["video"] = win
            except Exception as e:
                messagebox.showerror("Hata", f"Sinematik video oynatılamadı:\n{e}", parent=self)
    def ollama_otomatik_kurulumunu_ac(self):
        """Ollama ve Yapay Zeka Model Kurucu Sihirbazını UAC ile başlatır."""
        try:
            try:
                from altar_ollama_kurucu import AltarOllamaKurucuArayuz, yonetici_mi, yonetici_olarak_yeniden_baslat
            except ImportError:
                from altar_ollama_kurucu import AltarOllamaSinematikSetup as AltarOllamaKurucuArayuz, yonetici_mi, yonetici_olarak_otomatik_yukselt as yonetici_olarak_yeniden_baslat
            if not yonetici_mi():
                yonetici_olarak_yeniden_baslat()
            else:
                kurucu = AltarOllamaKurucuArayuz(otomatik_baslat=False)
                kurucu.mainloop()
        except Exception as e:
            messagebox.showerror("Hata", f"Ollama kurucu başlatılamadı:\n{e}", parent=self)

    def readme_merkezini_ac(self):
        """Kapsamlı çevrimdışı sistem kullanım kılavuzunu (README) tam ekran olarak açar."""
        try:
            from altar_readme import readme_merkezi_ac
            win = readme_merkezi_ac(self)
            if win:
                self._aktif_pencereler["readme"] = win
                win.lift()
                win.focus_force()
        except Exception as e:
            messagebox.showwarning("README Kılavuzu", f"README açılırken hata: {e}", parent=self)

    def _tema_degistir(self, secilen_tema: str):
        """Seçilen renk paletini ana pencere panellerine uygular."""
        try:
            palet = AltarTemaMotoru.tema_degistir(secilen_tema)
            if hasattr(self, "top_panel"):
                self.top_panel.configure(fg_color=palet["panel_bg"], border_color=palet["kenarlik"])
            if hasattr(self, "lbl_telemetri"):
                self.lbl_telemetri.configure(text_color=palet["neon"])
            if hasattr(self, "chat_display"):
                self.chat_display.configure(fg_color=palet["ana_bg"], text_color=palet["yazi_ana"])
            if hasattr(self, "bottom_panel"):
                self.bottom_panel.configure(fg_color=palet["panel_bg"])
            if hasattr(self, "combo_tema"):
                self.combo_tema.configure(fg_color=palet["vurgu"], button_color=palet["vurgu_hover"])
        except Exception:
            pass

    def _yerel_model_secimi_degisti(self, secilen_model: str):
        """Ana thread'de seçilen modeli saf Python değişkenine kaydeder (Arka plan thread güvenliği için)."""
        self._secili_yerel_model_bellek = secilen_model

    def _pencereyi_tam_ekran_yap(self):
        """Tüm üst ve orta sekme bileşenleri oluşturulduktan sonra pencereyi güvenle tam ekran yapar (Windows görev çubuğu ve başlık çubuğu dahil tüm ekranı kaplar)."""
        try:
            if self.winfo_exists():
                self.update_idletasks()
                self.attributes("-fullscreen", True)
                self._tam_ekran_mi = True
                if hasattr(self, "btn_fullscreen"):
                    self.btn_fullscreen.configure(text="🗗")
                self.lift()
                self.focus_force()
                self.update_idletasks()
        except Exception:
            pass

    def _tam_ekran_degistir(self, event=None):
        """F11 veya üst bardaki tam ekran butonu tıklandığında tam ekran modunu açar/kapatır."""
        try:
            self._tam_ekran_mi = not getattr(self, "_tam_ekran_mi", False)
            self.attributes("-fullscreen", self._tam_ekran_mi)
            if hasattr(self, "btn_fullscreen"):
                self.btn_fullscreen.configure(text="🗗" if self._tam_ekran_mi else "🗖")
        except Exception:
            pass

    def _tam_ekrandan_cik(self, event=None):
        """Escape tuşuna basıldığında tam ekran modundan çıkarak pencereli moda döner."""
        try:
            if getattr(self, "_tam_ekran_mi", False):
                self._tam_ekran_mi = False
                self.attributes("-fullscreen", False)
                if hasattr(self, "btn_fullscreen"):
                    self.btn_fullscreen.configure(text="🗖")
        except Exception:
            pass

    def _simge_durumuna_kucult(self):
        """Pencereyi simge durumuna küçültür."""
        try:
            self.iconify()
        except Exception:
            pass

    def _arayuz_bilesenlerini_kur(self, profil_listesi: list):
        """Ana pencere bileşenlerini, üst barı, 7 sekmeyi ve tüm alt araç butonlarını oluşturur."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)

        # --- ÜST MENÜ BAR (ÇİFT SATIRLI FERAH MİMARİ - HİÇBİR BUTON SIKIŞMAZ VE KIRPILMAZ) ---
        self.top_panel = ctk.CTkFrame(self.main_frame, corner_radius=8, fg_color="#111827", border_width=1, border_color="#1E293B")
        self.top_panel.pack(side="top", fill="x", padx=10, pady=(6, 4))

        # 1. SATIR: Yapay Zeka Güç Butonu (EN SOLDA - ASLA KIRPILMAZ) ve Model/Motor/API Seçimleri
        self.top_row_1 = ctk.CTkFrame(self.top_panel, fg_color="transparent")
        self.top_row_1.pack(side="top", fill="x", padx=8, pady=(6, 3))

        # --- SAĞ ÜST: TAM EKRAN VE PENCERE YÖNETİM BUTONLARI (ÖNCE SAĞA SABİTLENİR - ASLA KAYBOLMAZ) ---
        self.btn_pencere_kapat = ctk.CTkButton(
            self.top_row_1,
            text="✕",
            width=32,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#dc2626",
            hover_color="#991b1b",
            command=self._uygulamayi_guvenli_kapat
        )
        self.btn_pencere_kapat.pack(side="right", padx=(2, 0))

        self.btn_fullscreen = ctk.CTkButton(
            self.top_row_1,
            text="🗗",
            width=32,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#374151",
            hover_color="#4b5563",
            command=self._tam_ekran_degistir
        )
        self.btn_fullscreen.pack(side="right", padx=(2, 2))

        self.btn_pencere_kucult = ctk.CTkButton(
            self.top_row_1,
            text="—",
            width=32,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#374151",
            hover_color="#4b5563",
            command=self._simge_durumuna_kucult
        )
        self.btn_pencere_kucult.pack(side="right", padx=(4, 4))

        # 2. SATIR: Sistem Telemetrisi, UAC Yetki Rozeti ve Hızlı Komut Paleti
        self.top_row_2 = ctk.CTkFrame(self.top_panel, fg_color="transparent")
        self.top_row_2.pack(side="top", fill="x", padx=8, pady=(2, 6))

        # --- 1. SATIR SOL BİLEŞENLERİ ---
        # Yapay Zeka Aç / Kapat (RAM & Pil Tasarruf) Butonu - EN SOLDA GÖRÜNÜR VE FERAH
        self.btn_ai_guc = ctk.CTkButton(
            self.top_row_1,
            text="🔴 Yapay Zeka: Kapalı",
            width=165,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#8B0000",
            hover_color="#5C0000",
            command=self.yapay_zeka_guc_degistir
        )
        self.btn_ai_guc.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(self.top_row_1, text="Motor:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            side="left", padx=(4, 2)
        )
        self.motor_var = ctk.StringVar(value="Yerel (Ollama)")
        self.motor_selector = ctk.CTkOptionMenu(
            self.top_row_1,
            variable=self.motor_var,
            values=["Yerel (Ollama)", "Bulut (API)"],
            width=125,
            height=28,
            fg_color="#b85c00",
            button_color="#8f4700",
            button_hover_color="#6e3700"
        )
        self.motor_selector.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(self.top_row_1, text="Model:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            side="left", padx=(4, 2)
        )
        varsayilan_model = "jaahas/qwen3.5-uncensored:9b" if "jaahas/qwen3.5-uncensored:9b" in self.yuklu_modeller else \
            self.yuklu_modeller[0]
        self._secili_yerel_model_bellek = varsayilan_model
        self.active_model_var = ctk.StringVar(value=varsayilan_model)
        self.model_selector = ctk.CTkOptionMenu(
            self.top_row_1,
            variable=self.active_model_var,
            values=self.yuklu_modeller,
            width=165,
            height=28,
            command=self._yerel_model_secimi_degisti
        )
        self.model_selector.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(self.top_row_1, text="Profil:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            side="left", padx=(4, 2)
        )
        varsayilan_profil = "Sohbet" if "Sohbet" in profil_listesi else profil_listesi[0]
        self.active_lang_var = ctk.StringVar(value=varsayilan_profil)
        self.lang_selector = ctk.CTkOptionMenu(
            self.top_row_1,
            variable=self.active_lang_var,
            values=profil_listesi,
            width=105,
            height=28,
            fg_color="#4B0082"
        )
        self.lang_selector.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(self.top_row_1, text="API:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            side="left", padx=(4, 2)
        )
        varsayilan_api = self.api_modeller[0] if self.api_modeller else "Bulunamadı"
        self.active_api_model_var = ctk.StringVar(value=varsayilan_api)
        self.api_model_selector = ctk.CTkOptionMenu(
            self.top_row_1,
            variable=self.active_api_model_var,
            values=self.api_modeller,
            width=175,
            height=28,
            fg_color="#8b0000",
            button_color="#5c0000",
            button_hover_color="#3d0000"
        )
        self.api_model_selector.pack(side="left", padx=(0, 4))

        # Altar Çoklu Tema Seçici Açılır Menü
        ctk.CTkLabel(self.top_row_1, text="Tema:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            side="left", padx=(6, 2)
        )
        self.combo_tema_var = ctk.StringVar(value="🌲 Zümrüt Doğa & Şelale")
        self.combo_tema = ctk.CTkOptionMenu(
            self.top_row_1,
            variable=self.combo_tema_var,
            values=AltarTemaMotoru.tema_listesi(),
            width=165,
            height=28,
            fg_color="#059669",
            button_color="#047857",
            command=self._tema_degistir
        )
        self.combo_tema.pack(side="left", padx=(0, 4))

        # Tema yanındaki Kilit Butonu (Klavye & Fare Donanımsal Kilitleme)
        self.btn_kilit = ctk.CTkButton(
            self.top_row_1,
            text="🔒",
            width=32,
            height=28,
            font=ctk.CTkFont(size=14),
            fg_color="#1E293B",
            hover_color="#334155",
            border_width=1,
            border_color="#334155",
            command=self.klavye_fare_kilit_degistir
        )
        self.btn_kilit.pack(side="left", padx=(4, 6))

        # --- 2. SATIR BİLEŞENLERİ ---
        # Hızlı Komut Paleti (Ctrl+K) Butonu
        self.btn_palet = ctk.CTkButton(
            self.top_row_2, text="🔍 Komut Paleti (Ctrl+K)", width=170, height=24,
            fg_color="#1E293B", hover_color="#334155",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self.komut_paletini_ac
        )
        self.btn_palet.pack(side="left", padx=(0, 6))

        # UAC / Admin Durum Rozeti (Sisteme veya Kullanıcıya Zararsız Yetki Durumu)
        is_admin = False
        if os.name == "nt":
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                pass
        self._is_admin = is_admin
        uac_metin = "🛡️ UAC: Yönetici" if is_admin else "🛡️ UAC: Standart"
        uac_renk = "#059669" if is_admin else "#D97706"
        uac_hover = "#047857" if is_admin else "#B45309"

        self.btn_uac = ctk.CTkButton(
            self.top_row_2, text=uac_metin, width=125, height=24,
            fg_color=uac_renk, hover_color=uac_hover,
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            command=self.uac_yetki_kontrolu
        )
        self.btn_uac.pack(side="left", padx=(0, 8))

        # Canlı Ağ Bağlantı Radarı (Salt-Okunur) Butonu
        self.btn_ag_radari = ctk.CTkButton(
            self.top_row_2, text="🌐 Ağ Radarı", width=110, height=24,
            fg_color="#0D9488", hover_color="#0F766E",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            command=self.ag_radarini_ac
        )
        self.btn_ag_radari.pack(side="left", padx=(0, 8))

        # Canlı Mikroçekim Mavi / Plazma Ateş Animasyon Widgetı
        try:
            self.mavi_ates_widget = AltarMaviAtesWidget(self.top_row_2, genislik=95, yukseklik=24, bg_color="#111827")
            self.mavi_ates_widget.pack(side="left", padx=(0, 8))
        except Exception:
            pass

        # README & Kapsamlı Sistem Kullanım Kılavuzu Butonu (API Modelinin Altındaki Alanda)
        self.btn_readme = ctk.CTkButton(
            self.top_row_2,
            text="📖 README",
            width=100,
            height=24,
            fg_color="#1D4ED8",
            hover_color="#1E40AF",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self.readme_merkezini_ac
        )
        self.btn_readme.pack(side="left", padx=(0, 6))

        # Altar Sinematik Tam Ekran Video Oynatıcı Butonu
        self.btn_sinematik_video = ctk.CTkButton(
            self.top_row_2,
            text="🎬 Sinematik Video",
            width=135,
            height=24,
            fg_color="#1F538D",
            hover_color="#14375E",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self.sinematik_video_sec_ve_oynat
        )
        self.btn_sinematik_video.pack(side="left", padx=(0, 8))


        lbl_bilgi_ek = ctk.CTkLabel(
            self.top_row_2, text="⚡ Hibrit AI Çekirdeği (Yerel Ollama & Google Gemini API)",
            font=ctk.CTkFont(size=11), text_color="#38BDF8"
        )
        lbl_bilgi_ek.pack(side="left", padx=4)

        # Sağ üstteki telemetri etiketi (CPU, GPU, RAM) - 2. Satırın En Sağında Ferah Şekilde
        self.lbl_telemetri = ctk.CTkLabel(
            self.top_row_2,
            text="CPU: %0 | GPU: %0 | Altar RAM: %0.0 (0 MB) | Sistem: %0",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#00FF88"
        )
        self.lbl_telemetri.pack(side="right", padx=(4, 6))

        # --- ORTA EKRAN: 8 SEKMELİ YAPI ---
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=8, command=self._ust_sekme_degisti)
        self.tabview.pack(side="top", fill="both", expand=True, padx=10, pady=(4, 10))

        self.tab_gezgin = self.tabview.add("📁 Dosya Gezgini & Kasa")
        self.tab_oyun = self.tabview.add("🎮 Oyun")
        self.tab_sohbet = self.tabview.add("💬 Sohbet")
        self.tab_muzik = self.tabview.add("🎵 Müzik")
        self.tab_ide = self.tabview.add("🐍 Python IDE & Editör")
        self.tab_analiz = self.tabview.add("📊 Kazınan Veri & Analiz Merkezi")
        self.tab_gcode = self.tabview.add("📐 CNC G-Code 2D Simülatör")
        self.tab_guvenlik = self.tabview.add("🛡️ Güvenlik")
        self.tab_tersine_muh = self.tabview.add("🔬 Tersine Mühendislik")
        self.tab_edr = self.tabview.add("🦠 Antivirüs & EDR")
        self.tabview.set("💬 Sohbet")

        # SOHBET VE SEKMELER SIRASINDAKİ SOL VE SAĞ BOŞLUKLARA "SEKMELER" BUTONLARI
        self.btn_sekmeler_sol = ctk.CTkButton(
            self.tabview,
            text="📑 Sekmeler",
            width=115,
            height=28,
            corner_radius=8,
            fg_color="#0F172A",
            hover_color="#0284C7",
            border_width=1,
            border_color="#38BDF8",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self.acik_sekmeler_gezgini_ac
        )
        self.btn_sekmeler_sol.place(x=14, y=14)

        self.btn_sekmeler_sag = ctk.CTkButton(
            self.tabview,
            text="📑 Sekmeler",
            width=115,
            height=28,
            corner_radius=8,
            fg_color="#0F172A",
            hover_color="#0284C7",
            border_width=1,
            border_color="#38BDF8",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self.acik_sekmeler_gezgini_ac
        )
        self.btn_sekmeler_sag.place(relx=1.0, x=-130, y=14)

        # Sohbet Sekmesi: İki Bölmeli Şeffaf Sinematik Arayüz (Sol: AI Terminali, Sağ: AI Sinir Ağı Animasyonu)
        self.sohbet_govde = ctk.CTkFrame(self.tab_sohbet, fg_color="transparent")
        self.sohbet_govde.pack(fill="both", expand=True)

        self.chat_display = ctk.CTkTextbox(
            self.sohbet_govde,
            font=ctk.CTkFont(family="Consolas", size=self._chat_font_boyutu),
            wrap="word",
            fg_color="#080D1A",
            border_width=1,
            border_color="#1E293B"
        )
        self.chat_display.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # Sağ Panel: Canlı Siber AI Nöron Ağı & Sinir Ağı Sinematik Animasyonu
        try:
            from altar_animasyon_motoru import AltarSinematikArkaPlanKanvasi
            self.sinematik_arka_plan = AltarSinematikArkaPlanKanvasi(
                self.sohbet_govde, mod="sohbet", width=360
            )
            self.sinematik_arka_plan.pack(side="right", fill="both", expand=False)
        except Exception as e_bg:
            print(f"[!] Sinematik arka plan yükleme uyarısı: {e_bg}")
        self.chat_display.bind("<Control-MouseWheel>", self._chat_font_olcekle)

        karsilama_rehberi = "💬 Altar Çevrimdışı Yapay Zeka & Mühendislik Platformu Hazır.\n(Detaylı özellik ve sekmeler kılavuzuna üstteki '📖 README' butonundan erişebilirsiniz.)\n\n"
        self.chat_display.insert("end", karsilama_rehberi)

        self.chat_display.tag_config("code_style", foreground="#E6DB74")
        self.chat_display.tag_config("thought_style", foreground="#8A8A8A")
        self.chat_display.tag_config("telemetry_style", foreground="#00CED1")
        self.chat_display.tag_config("warning_style", foreground="#FF3333")
        self.chat_display._textbox.tag_configure("warning_style", font=("Consolas", 14, "bold"))
        self.chat_display.configure(state="disabled")

        self._analiz_sekmesini_hazirla()

        # =====================================================================
        # ALT PANEL VE EN SOL ÜST ŞERİT (SES + EKRAN VİDEO + KAMERA BUTONLARI DAHİL)
        # =====================================================================
        self.bottom_panel = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.bottom_panel.pack(side="bottom", fill="x", padx=10, pady=(0, 10), before=self.tabview)

        self.ust_ince_serit = ctk.CTkFrame(self.bottom_panel, fg_color="transparent", height=22)
        self.ust_ince_serit.pack(side="top", fill="x", padx=0, pady=(0, 3))

        self.btn_ses_studyosu = ctk.CTkButton(
            self.ust_ince_serit, text="🎙️ Ses Kaydedici", width=115, height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#C62828", hover_color="#8E0000",
            command=self.ses_kaydedici_studyosunu_ac
        )
        self.btn_ses_studyosu.pack(side="left", padx=(0, 4))

        self.btn_hizli_ses_kayit = ctk.CTkButton(
            self.ust_ince_serit, text="🔴 Hızlı Kayıt", width=92, height=20,
            font=ctk.CTkFont(size=11),
            fg_color="#374151", hover_color="#1F2937",
            command=self.hizli_ses_kaydi_baslat_durdur
        )
        self.btn_hizli_ses_kayit.pack(side="left", padx=(0, 6))

        self.btn_video_studyosu = ctk.CTkButton(
            self.ust_ince_serit, text="🎬 Video Kaydı", width=105, height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1f538d", hover_color="#14375e",
            command=self.video_kaydedici_studyosunu_ac
        )
        self.btn_video_studyosu.pack(side="left", padx=(0, 4))

        self.btn_hizli_video_kayit = ctk.CTkButton(
            self.ust_ince_serit, text="⏺️ Hızlı Video", width=92, height=20,
            font=ctk.CTkFont(size=11),
            fg_color="#374151", hover_color="#1F2937",
            command=self.hizli_video_kaydi_baslat_durdur
        )
        self.btn_hizli_video_kayit.pack(side="left", padx=(0, 6))

        self.btn_kamera_studyosu = ctk.CTkButton(
            self.ust_ince_serit, text="📷 Kamera", width=90, height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#4B0082", hover_color="#2b004d",
            command=self.kamera_studyosunu_ac
        )
        self.btn_kamera_studyosu.pack(side="left", padx=(0, 4))

        self.btn_hizli_kamera_kayit = ctk.CTkButton(
            self.ust_ince_serit, text="⏺️ Hızlı Kamera", width=98, height=20,
            font=ctk.CTkFont(size=11),
            fg_color="#374151", hover_color="#1F2937",
            command=self.hizli_kamera_kaydi_baslat_durdur
        )
        self.btn_hizli_kamera_kayit.pack(side="left", padx=(0, 6))

        self.btn_simulasyonlar = ctk.CTkButton(
            self.ust_ince_serit, text="🚀 Simülasyonlar", width=118, height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#D97706", hover_color="#B45309",
            command=self.simulasyonlar_merkezini_ac
        )
        self.btn_simulasyonlar.pack(side="left", padx=(0, 6))

        self.btn_ekran_sor = ctk.CTkButton(
            self.ust_ince_serit, text="✂️ Ekranı Sor", width=102, height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284C7", hover_color="#0369A1",
            command=self.ekrandan_bolge_yakala_ve_sor
        )
        self.btn_ekran_sor.pack(side="left", padx=(0, 6))

        self.btn_sesli_yanit = ctk.CTkButton(
            self.ust_ince_serit, text="🔇 Sesli: Kapalı", width=108, height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#374151", hover_color="#1F2937",
            command=self.sesli_yanit_durum_degistir
        )
        self.btn_sesli_yanit.pack(side="left", padx=(0, 6))

        self.btn_ram_temizle = ctk.CTkButton(
            self.ust_ince_serit, text="🧹 RAM Temizle", width=106, height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#059669", hover_color="#047857",
            command=self.ram_optimize_et
        )
        self.btn_ram_temizle.pack(side="left", padx=(0, 6))

        self.btn_kodu_ideye_aktar = ctk.CTkButton(
            self.ust_ince_serit, text="🐍 Kodu IDE'ye Aktar", width=128, height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#6366F1", hover_color="#4F46E5",
            command=self.son_kodu_ideye_aktar
        )
        self.btn_kodu_ideye_aktar.pack(side="left", padx=(0, 6))

        self.btn_oturumlar = ctk.CTkButton(
            self.ust_ince_serit, text="📂 Oturumlar", width=95, height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#7C3AED", hover_color="#6D28D9",
            command=self.sohbet_oturumlarini_ac
        )
        self.btn_oturumlar.pack(side="left", padx=(0, 6))

        self.btn_karantina = ctk.CTkButton(
            self.ust_ince_serit, text="📦 Karantina", width=95, height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#991B1B", hover_color="#7F1D1D",
            command=self.karantina_kasasini_ac
        )
        self.btn_karantina.pack(side="left", padx=(0, 8))

        self.lbl_ek_bilgi = ctk.CTkLabel(self.ust_ince_serit, text="", text_color="#00AAFF", font=ctk.CTkFont(size=12))
        self.lbl_ek_bilgi.pack(side="left", padx=4)

        self.action_frame = ctk.CTkFrame(self.bottom_panel, fg_color="transparent")
        self.action_frame.pack(side="left", padx=(0, 10))

        self.btn_export = ctk.CTkButton(self.action_frame, text="💾 Raporu Kaydet", width=115, height=22,
                                        command=self.sohbeti_disa_aktar,
                                        fg_color="#1f538d", hover_color="#14375e")
        self.btn_export.pack(side="top", pady=1)

        self.btn_word_pro = ctk.CTkButton(self.action_frame, text="📝 Altar Belge", width=115, height=22,
                                          command=self.word_programini_ac,
                                          fg_color="#008080", hover_color="#005959")
        self.btn_word_pro.pack(side="top", pady=1)

        self.btn_resim = ctk.CTkButton(self.action_frame, text="📎 Resim", width=115, height=22,
                                       command=self.resim_ekle,
                                       fg_color="#4B0082", hover_color="#2b004d")
        self.btn_resim.pack(side="top", pady=1)

        self.btn_ses = ctk.CTkButton(self.action_frame, text="🎤 Ses", width=115, height=22,
                                     command=self.sesli_yazdir,
                                     fg_color="#006400", hover_color="#004d00")
        self.btn_ses.pack(side="top", pady=1)

        self.btn_belge = ctk.CTkButton(self.action_frame, text="📄 Belge", width=115, height=22,
                                       command=self.belge_ekle,
                                       fg_color="#8B4500", hover_color="#5c2e00")
        self.btn_belge.pack(side="top", pady=1)

        self.btn_nasa_sim = ctk.CTkButton(self.action_frame, text="🌐 Web", width=115, height=22,
                                          command=self.toggle_nasa_sim,
                                          fg_color="#FF4500", hover_color="#8B0000")
        self.btn_nasa_sim.pack(side="top", pady=1)

        self.btn_telemetri_lab = ctk.CTkButton(self.action_frame, text="📈 Radar & Alev", width=115, height=22,
                                               command=self.telemetri_merkezini_ac,
                                               fg_color="#00A86B", hover_color="#007F50")
        self.btn_telemetri_lab.pack(side="top", pady=1)

        self.btn_siber_hex = ctk.CTkButton(self.action_frame, text="🛡️ Siber Hex", width=115, height=22,
                                           command=self.siber_hex_merkezini_ac,
                                           fg_color="#4B0082", hover_color="#2b004d")
        self.btn_siber_hex.pack(side="top", pady=1)

        self.btn_meb_sertifika = ctk.CTkButton(self.action_frame, text="📜 MEB Sertifika", width=115, height=22,
                                               command=self.meb_sertifika_yoneticisi_ac,
                                               fg_color="#008B8B", hover_color="#005959")
        self.btn_meb_sertifika.pack(side="top", pady=1)

        self.user_input = ctk.CTkTextbox(self.bottom_panel, font=ctk.CTkFont(size=self._chat_font_boyutu), height=145, border_width=2,
                                         border_color="#3a3a3a")
        self.user_input.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.user_input.bind("<Control-MouseWheel>", self._chat_font_olcekle)

        def on_enter_pressed(event):
            if event.state & 0x0001:
                return
            else:
                self.send_command()
                return "break"

        self.user_input.bind("<Return>", on_enter_pressed)

        self.btn_send = ctk.CTkButton(self.bottom_panel, text="İlet", width=100, height=145, command=self.send_command)
        self.btn_send.pack(side="right")

        # Alt özel bölüm konteynerleri
        self.guvenlik_alt_iki_bolum = ctk.CTkFrame(self.bottom_panel, fg_color="transparent", height=185)
        self.guvenlik_alt_iki_bolum.grid_columnconfigure(0, weight=6)
        self.guvenlik_alt_iki_bolum.grid_columnconfigure(1, weight=5)
        self.guvenlik_alt_iki_bolum.grid_rowconfigure(0, weight=1)

        self.analiz_alt_iki_bolum = ctk.CTkFrame(self.bottom_panel, fg_color="transparent", height=195)
        self.analiz_alt_iki_bolum.grid_columnconfigure(0, weight=1)
        self.analiz_alt_iki_bolum.grid_columnconfigure(1, weight=1)
        self.analiz_alt_iki_bolum.grid_rowconfigure(0, weight=1)

        self.tersine_alt_dpi_tek_bolum = ctk.CTkFrame(self.bottom_panel, fg_color="transparent", height=195)

        # Ana Thread UI, Telemetri ve Kademeli Varsayılan Güvenlik Kalkanlarını Başlat
        self.update_idletasks()
        if self.state() != "withdrawn":
            self.after(80, self._pencereyi_tam_ekran_yap)
        self.after(50, self._merkezi_ui_dongusu)
        self.after(1800, self._varsayilan_edr_kalkanini_baslat)
        self.after(2800, self._varsayilan_ag_ips_kalkanini_baslat)
        self.after(1500, self.telemetri_guncelle)

    def _varsayilan_edr_kalkanini_baslat(self):
        """Uygulama açıldıktan 600ms sonra 5-Katmanlı EDR Antivirüs Kalkanını otomatik devreye alır."""
        if not self._edr_yuklendi and self.winfo_exists():
            self._edr_yuklendi = True
            self._edr_sekmesini_tekil_hazirla()

    def _varsayilan_ag_ips_kalkanini_baslat(self):
        """Uygulama açıldıktan 1200ms sonra Ağ IPS Güvenlik Duvarını kademeli olarak devreye alır."""
        if not self._guvenlik_yuklendi and self.winfo_exists():
            self._guvenlik_yuklendi = True
            self._guvenlik_sekmesini_tekil_hazirla()

    def _uygulamayi_guvenli_kapat(self):
        """Uygulama kapatılırken aktif kayıtları, güvenlik kalkanlarını ve yerel AI belleğini güvenli şekilde temizler."""
        try:
            self.yapay_zeka_aktif = False
            if self.edr_panel and hasattr(self.edr_panel, "motor"):
                self.edr_panel.motor.edr_aktif = False
            if self.guvenlik_panel and hasattr(self.guvenlik_panel, "ips"):
                self.guvenlik_panel.ips.calisiyor = False
            if self.ses_kayit_motoru and self.ses_kayit_motoru.kayit_aktif:
                self.ses_kayit_motoru.kaydi_durdur()
            if self.ekran_video_motoru and self.ekran_video_motoru.kayit_aktif:
                self.ekran_video_motoru.kaydi_durdur()
            if self.kamera_video_motoru:
                self.kamera_video_motoru.kamerayi_kapat()
            if self.ide_panel and hasattr(self.ide_panel, "calisan_kodu_durdur"):
                self.ide_panel.calisan_kodu_durdur()
            try:
                from altar_klavye_kilit import klavye_kalkanini_durdur
                klavye_kalkanini_durdur()
            except Exception:
                pass
        except Exception:
            pass
        self.destroy()

    def klavye_fare_kilit_degistir(self):
        """Tema yanındaki kilit butonuna tıklandığında klavye ve fare kilit durumunu değiştirir."""
        try:
            from altar_klavye_kilit import AltarKlavyeFareKilitServisi
            servis = AltarKlavyeFareKilitServisi.ornek_al()
            servis.kilit_durumu_ayarla(not servis.kilitli)
        except Exception as e:
            print(f"[!] Kilit değiştirme uyarısı: {e}")

    def _guvenli_kilit_butonu_guncelle(self, kilitli: bool):
        """Arka plan iş parçacığından UI kilit butonunu güvenle günceller."""
        try:
            self.after(0, lambda: self._kilit_butonu_ui_guncelle(kilitli))
        except Exception:
            pass

    def _kilit_butonu_ui_guncelle(self, kilitli: bool):
        """Kilit butonunun görsel durumunu günceller."""
        if hasattr(self, "btn_kilit") and self.btn_kilit.winfo_exists():
            if kilitli:
                self.btn_kilit.configure(
                    text="🔒",
                    fg_color="#DC2626",
                    hover_color="#B91C1C",
                    border_color="#EF4444"
                )
            else:
                self.btn_kilit.configure(
                    text="🔒",
                    fg_color="#1E293B",
                    hover_color="#334155",
                    border_color="#334155"
                )

    # =====================================================================
    # MERKEZİ THREAD-SAFE ARAYÜZ GÜNCELLEME DÖNGÜSÜ
    # =====================================================================
    def _ui_gorevi_ekle(self, fonk):
        """Arka plan thread'lerinden Tkinter'a güvenli görev iletir (self.after çakışmasını önler)."""
        self._ui_gorev_kuyrugu.append(fonk)

    def _merkezi_ui_dongusu(self):
        """Yalnızca Ana (Main) Thread'de çalışarak tüm sohbet ve arayüz güncellemelerini güvenle işler."""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        islenen_gorev = 0
        while self._ui_gorev_kuyrugu and islenen_gorev < 25:
            try:
                gorev = self._ui_gorev_kuyrugu.popleft()
                gorev()
            except Exception:
                pass
            islenen_gorev += 1

        paketler = None
        with self._chat_kilit:
            if self._chat_tamponu:
                paketler = list(self._chat_tamponu)
                self._chat_tamponu.clear()

        if paketler:
            self.chat_display.configure(state="normal")
            son_final = False
            for metin, tag, final in paketler:
                if tag:
                    self.chat_display.insert("end", metin, tag)
                else:
                    self.chat_display.insert("end", metin)
                if final:
                    son_final = True

            if son_final:
                self.kodlari_renklendir()
            self.chat_display.see("end")
            self.chat_display.configure(state="disabled")

        try:
            if self.winfo_exists():
                self.after(55, self._merkezi_ui_dongusu)
        except Exception:
            pass

    def kodlari_renklendir(self):
        try:
            self.chat_display.tag_remove("code_style", "1.0", "end")
            self.chat_display.tag_remove("thought_style", "1.0", "end")
            metin = self.chat_display.get("1.0", "end")

            for match in _RE_ANY_CODE_BLOCK.finditer(metin):
                baslangic_indeksi = f"1.0 + {match.start()} chars"
                bitis_indeksi = f"1.0 + {match.end()} chars"
                self.chat_display.tag_add("code_style", baslangic_indeksi, bitis_indeksi)

            for match in _RE_THOUGHT_CLEAN.finditer(metin):
                baslangic_indeksi = f"1.0 + {match.start()} chars"
                bitis_indeksi = f"1.0 + {match.end()} chars"
                self.chat_display.tag_add("thought_style", baslangic_indeksi, bitis_indeksi)
        except Exception:
            pass

    def update_chat_safe(self, text, final=False, tag=None):
        """
        Arka plan thread'lerinden hiçbir Tkinter fonksiyonu (self.after dahil) ÇAĞIRMAZ!
        Yalnızca saf Python deque kuyruğuna ekler; çizimi Ana Thread'deki _merkezi_ui_dongusu yapar.
        """
        with self._chat_kilit:
            if self._chat_tamponu and self._chat_tamponu[-1][1] == tag and not self._chat_tamponu[-1][2]:
                eski_metin, eski_tag, _ = self._chat_tamponu[-1]
                self._chat_tamponu[-1] = (eski_metin + text, eski_tag, final)
            else:
                self._chat_tamponu.append((text, tag, final))

    def open_settings(self):
        AltarSettingsWindow(self)

    def log_to_chat(self, tag, message, final=False):
        self.update_chat_safe(f"[{tag}]: {message}\n\n", final=final)

    def _api_modellerini_arka_planda_yukle(self):
        try:
            if not self.api_engine:
                return
            dinamik_api_modelleri = self.api_engine.siber_radar_modelleri_getir()
            liste = list(dinamik_api_modelleri.keys()) if dinamik_api_modelleri else ["API Model Bulunamadı"]

            def _guncelle():
                if not self.winfo_exists():
                    return
                self.api_modeller = liste
                self.api_model_selector.configure(values=liste)
                self.active_api_model_var.set(liste[0])

            self._ui_gorevi_ekle(_guncelle)
        except Exception:
            pass

    # =====================================================================
    # YAPAY ZEKA AÇ / KAPAT (RAM & PİL TASARRUFU) KONTROLLERİ
    # =====================================================================
    def yapay_zeka_guc_degistir(self):
        self.yapay_zeka_aktif = not self.yapay_zeka_aktif
        if self.yapay_zeka_aktif:
            self.btn_ai_guc.configure(
                text="🟢 Yapay Zeka: Açık",
                fg_color="#00A86B",
                hover_color="#007F50"
            )
            self.log_to_chat("SİSTEM", "⚡ Yapay Zeka motoru AKTİF edildi. Sorularınızı iletebilirsiniz.", final=True)
            threading.Thread(target=self.yerel_modeli_bellege_hazirla, daemon=True).start()
        else:
            self.btn_ai_guc.configure(
                text="🔴 Yapay Zeka: Kapalı",
                fg_color="#8B0000",
                hover_color="#5C0000"
            )
            self.log_to_chat(
                "SİSTEM",
                "💤 Yapay Zeka KAPATILDI. Yerel model RAM/VRAM'den boşaltılıyor (Pil ve Bellek Tasarruf Modu)...",
                final=True
            )
            threading.Thread(target=self.yerel_modeli_bellekten_bosalt, daemon=True).start()

    def yerel_modeli_bellege_hazirla(self):
        """Alt sınıf (Local AI.py -> AltarMainUI) tarafından ezilir ve modeli num_ctx=2048 ile önceden ısıtır."""
        pass

    def yerel_modeli_bellekten_bosalt(self):
        """Alt sınıf (Local AI.py -> AltarMainUI) tarafından ezilir ve Ollama modelini RAM'den siler."""
        pass

    def _harici_raporu_ai_ile_analiz_et(self, rapor_metni: str):
        if not self.yapay_zeka_aktif:
            messagebox.showwarning(
                "Yapay Zeka Kapalı",
                "Yapay Zeka şu anda RAM ve pil tasarrufu için KAPALI durumda!\n\n"
                "Analiz yapmak için lütfen üst menüdeki '🔴 Yapay Zeka: Kapalı' butonuna tıklayarak aktif edin.",
                parent=self
            )
            return

        self.tabview.set("💬 Sohbet")
        self._ust_sekme_degisti()
        komut = (
            "Aşağıda Altar Güvenlik / Tersine Mühendislik / DPI / EDR Antivirüs / Dosya Gezgini modülünden alınan teknik çıktı yer almaktadır. "
            "Lütfen bu veriyi detaylıca analiz et, mimari yapıyı, olası tehditleri ve satır satır işleyişi açıkla:\n\n"
            f"{rapor_metni[:6000]}"
        )
        self.log_to_chat("Sen (Güvenlik & EDR Analizi)", "Seçili teknik çıktıyı analiz et.", final=True)
        aktif_motor = self.motor_var.get()
        secilen_dil = self.active_lang_var.get()
        if aktif_motor == "Yerel (Ollama)":
            secilen_model = self.active_model_var.get()
            self._secili_yerel_model_bellek = secilen_model
            threading.Thread(
                target=self.model_ile_konus,
                args=(secilen_model, secilen_dil, komut, None),
                daemon=True
            ).start()
        else:
            threading.Thread(
                target=self.api_ile_konus,
                args=(self.active_api_model_var.get(), secilen_dil, komut, None),
                daemon=True
            ).start()

    def _dogal_dil_komut_koprusu(self, komut: str) -> bool:
        """
        Kullanıcının sohbet kutusuna yazdığı doğrudan modül açma / RAM temizleme / sesli yanıt
        komutlarını %100 güvenli bir şekilde algılar ve ilgili Altar modülünü tetikler.
        """
        k = komut.strip().lower()
        if not k or len(k) > 65:
            return False

        eslesmeler = [
            (("simülasyonları aç", "simulasyonlari ac", "nasa merkezini aç", "simülasyon aç"), self.simulasyonlar_merkezini_ac, "🚀 Simülasyonlar & NASA Yarışma Merkezi açıldı."),
            (("radar ve alev", "alev laboratuvarını aç", "telemetri merkezini aç"), self.telemetri_merkezini_ac, "📈 Radar & Alev Laboratuvarı açıldı."),
            (("ram temizle", "belleği temizle", "ram optimize et"), self.ram_optimize_et, "🧹 Altar RAM optimizasyonu başlatıldı."),
            (("kasa sekmesini aç", "dosya gezginini aç", "kasayı aç"), lambda: (self.tabview.set("📁 Dosya Gezgini & Kasa"), self._ust_sekme_degisti()), "📁 Dosya Gezgini & Kasa sekmesine geçildi."),
            (("antivirüs sekmesini aç", "edr aç", "antivirüsü aç"), lambda: (self.tabview.set("🦠 Antivirüs & EDR"), self._ust_sekme_degisti()), "🦠 Antivirüs & EDR sekmesine geçildi."),
            (("cnc simülatörünü aç", "cnc aç", "gcode aç"), lambda: (self.tabview.set("📐 CNC G-Code 2D Simülatör"), self._ust_sekme_degisti()), "📐 CNC G-Code Simülatör sekmesine geçildi."),
            (("tersine mühendislik aç", "hex analizörü aç"), lambda: (self.tabview.set("🔬 Tersine Mühendislik"), self._ust_sekme_degisti()), "🔬 Tersine Mühendislik sekmesine geçildi."),
            (("python ide aç", "editörü aç", "kod editörünü aç", "ide aç"), lambda: (self.tabview.set("🐍 Python IDE & Editör"), self._ust_sekme_degisti()), "🐍 Python IDE & Editör sekmesine geçildi."),
            (("kodu ideye aktar", "kodu editöre aktar"), self.son_kodu_ideye_aktar, "🐍 Sohbetteki son kod bloğu Python IDE'ye aktarıldı."),
            (("altar belgeyi aç", "word aç", "belge editörünü aç"), self.word_programini_ac, "📝 Altar Belge başlatıldı."),
            (("ekranı sor", "ekran görüntüsü yakala"), self.ekrandan_bolge_yakala_ve_sor, "✂️ Ekran bölge seçici başlatıldı."),
        ]

        for anahtarlar, aksiyon, bilgi in eslesmeler:
            if any(a in k for a in anahtarlar):
                self.user_input.delete("1.0", "end")
                self.log_to_chat("Sen", komut, final=True)
                self.log_to_chat("SİSTEM (Doğal Dil Köprüsü)", bilgi, final=True)
                aksiyon()
                return True
        return False

    def son_kodu_ideye_aktar(self):
        """
        Sohbet ekranındaki en son üretilen Python/kod bloğunu otomatik olarak yakalar,
        '🐍 Python IDE & Editör' sekmesini açar ve kodu doğrudan editöre yükler.
        """
        try:
            sohbet_metni = self.chat_display.get("1.0", "end")
            kod_bloklari = re.findall(r"```(?:python|py)?\s*(.*?)```", sohbet_metni, re.DOTALL | re.IGNORECASE)
            secilen_kod = ""
            if kod_bloklari:
                secilen_kod = kod_bloklari[-1].strip()
            else:
                genel_bloklar = re.findall(r"```(?:\w+)?\s*(.*?)```", sohbet_metni, re.DOTALL)
                if genel_bloklar:
                    secilen_kod = genel_bloklar[-1].strip()

            self.tabview.set("🐍 Python IDE & Editör")
            self._ust_sekme_degisti()

            if self.ide_panel and hasattr(self.ide_panel, "kod_editore_yukle"):
                if secilen_kod:
                    self.ide_panel.kod_editore_yukle(secilen_kod, kaynak_baslik="ai_uretilen_kod.py")
                else:
                    self.ide_panel._terminale_yaz(
                        "[BİLGİ] Sohbet ekranında henüz ```python ... ``` formatında bir kod bloğu bulunamadı. "
                        "Doğrudan editöre kod yazabilir veya sol panelden .py dosyası seçebilirsiniz.\n",
                        "bilgi"
                    )
        except Exception as e:
            self.log_to_chat("HATA", f"Kod IDE'ye aktarılırken hata: {e}", final=True)

    def send_command(self):
        cmd = self.user_input.get("1.0", "end-1c").strip()

        if not cmd and not self.ekli_resim_yolu:
            return

        if not self.ekli_resim_yolu and self._dogal_dil_komut_koprusu(cmd):
            return

        if not self.yapay_zeka_aktif:
            messagebox.showwarning(
                "Yapay Zeka Kapalı",
                "Yapay Zeka şu anda RAM ve pil tasarrufu için KAPALI durumda!\n\n"
                "Soru sormak için lütfen üst menüdeki '🔴 Yapay Zeka: Kapalı' butonuna tıklayarak aktif edin.",
                parent=self
            )
            return

        self.user_input.delete("1.0", "end")

        if cmd.startswith("!"):
            cmd = cmd[1:].strip()

        if cmd and hasattr(self, "oturum_yoneticisi") and hasattr(self, "aktif_oturum_id"):
            self.oturum_yoneticisi.mesaji_oturuma_ekle(self.aktif_oturum_id, "user", cmd)

        self.log_to_chat("Sen", cmd, final=True)
        aktif_motor = self.motor_var.get()
        secilen_dil = self.active_lang_var.get()
        resim_dosyasi = self.ekli_resim_yolu

        self.ekli_resim_yolu = None
        self.lbl_ek_bilgi.configure(text="")

        if aktif_motor == "Yerel (Ollama)":
            secilen_model = self.active_model_var.get()
            self._secili_yerel_model_bellek = secilen_model
            threading.Thread(target=self.model_ile_konus, args=(secilen_model, secilen_dil, cmd, resim_dosyasi),
                             daemon=True).start()
        else:
            secilen_api_modeli = self.active_api_model_var.get()
            threading.Thread(target=self.api_ile_konus, args=(secilen_api_modeli, secilen_dil, cmd, resim_dosyasi),
                             daemon=True).start()

    # Alt sınıf (Local AI.py -> AltarMainUI) tarafından ezilen (override edilen) sanal metot imzaları
    def model_ile_konus(self, model_adi, dil_secimi, girdi, resim_yolu=None):
        pass

    def api_ile_konus(self, model_adi, dil_secimi, girdi, resim_yolu=None):
        pass

    def _belgeyi_isle_ve_kaydet(self, dosya_yolu):
        pass

    # =====================================================================
    # SOHBET OTURUMLARI, KOMUT PALETİ, UAC & KARANTİNA YÖNETİMİ
    # =====================================================================
    def _chat_font_olcekle(self, event):
        delta = getattr(event, "delta", 0)
        if delta > 0:
            self._chat_font_boyutu = min(28, self._chat_font_boyutu + 1)
        elif delta < 0:
            self._chat_font_boyutu = max(9, self._chat_font_boyutu - 1)
        yeni_font = ctk.CTkFont(family="Consolas", size=self._chat_font_boyutu)
        self.chat_display.configure(font=yeni_font)
        self.user_input.configure(font=yeni_font)
        return "break"

    def sohbet_oturumlarini_ac(self):
        AltarSohbetOturumlariModal(self, self.oturum_yoneticisi, secim_callback=self.oturum_degistir)

    def oturum_degistir(self, oturum_id: str, temizle: bool = False):
        self.aktif_oturum_id = oturum_id
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        if hasattr(self, "gecmis"):
            self.gecmis.clear()

        if temizle:
            karsilama = (
                "========================================================================================\n"
                "                           💬 YENİ SOHBET OTURUMU BAŞLATILDI\n"
                "========================================================================================\n"
                "Önceki konuşma bağlamı sıfırlandı. Sorunuzu yazıp Enter'a basabilirsiniz.\n\n"
            )
            self.chat_display.insert("end", karsilama)
            self.chat_display.configure(state="disabled")
            self.lbl_ek_bilgi.configure(text="💬 Yeni sohbet oturumu hazır")
            return

        veri = self.oturum_yoneticisi.oturum_yukle(oturum_id)
        if not veri:
            self.chat_display.configure(state="disabled")
            return

        meta = veri.get("meta", {})
        mesajlar = veri.get("mesajlar", [])
        baslik = meta.get("baslik", "Sohbet")

        self.chat_display.insert("end", f"=== 📂 OTURUM YÜKLENDİ: {baslik} ({len(mesajlar)} Mesaj) ===\n\n")

        for m in mesajlar:
            rol = m.get("role", "user")
            icerik = m.get("content", "")
            zaman = m.get("timestamp", "")
            if rol == "user":
                self.chat_display.insert("end", f"[Sen - {zaman}]:\n{icerik}\n\n")
            else:
                self.chat_display.insert("end", f"[Altar Asistan - {zaman}]:\n{icerik}\n\n" + "-" * 40 + "\n\n")

            if hasattr(self, "gecmis"):
                self.gecmis.append({"role": rol, "content": icerik})

        self.kodlari_renklendir()
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        self.lbl_ek_bilgi.configure(text=f"📂 '{baslik}' yüklendi")

    def yeni_sohbet_baslat(self):
        yeni = self.oturum_yoneticisi.yeni_oturum_olustur()
        self.oturum_degistir(yeni["id"], temizle=True)

    def karantina_kasasini_ac(self):
        win_kar = AltarKarantinaKasasiModal(self)
        self._aktif_pencereler["karantina"] = win_kar

    def uac_yetki_kontrolu(self):
        if getattr(self, "_is_admin", False):
            messagebox.showinfo(
                "Yönetici İzni",
                "🛡️ Altar şu anda 'Yönetici' (Administrator) haklarıyla çalışıyor.\n\n"
                "Ağ IPS kalkanı, scapy ham paket dinleme ve sistem port kontrolleri tam yetkilidir.",
                parent=self
            )
        else:
            cevap = messagebox.askyesno(
                "Yönetici Olarak Yeniden Başlat",
                "Altar şu anda 'Standart Kullanıcı' modunda çalışıyor.\n\n"
                "Ağ IPS Kalkanı ve ham soket filtreleme gibi güvenlik modüllerinin %100 yetkiyle "
                "çalışabilmesi için Altar'ı Yönetici (Administrator / UAC) olarak yeniden başlatmak ister misiniz?",
                parent=self
            )
            if cevap and os.name == "nt":
                try:
                    if getattr(sys, "frozen", False):
                        params = ""
                    else:
                        params = f'"{os.path.abspath(sys.argv[0])}"'
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
                    self._uygulamayi_guvenli_kapat()
                except Exception as e:
                    messagebox.showerror("Hata", f"Yönetici olarak başlatılamadı:\n{e}", parent=self)

    def komut_paletini_ac(self):
        eylemler = [
            {"ikon": "🎮", "baslik": "Siber Oyun Merkezine Geç (Python Oyunları)", "kategori": "Oyun", "aksiyon": self.oyun_merkezini_ac},
            {"ikon": "🎵", "baslik": "Müzik ve Sinematik Sahneye Geç (YouTube / Yerel)", "kategori": "Multimedya", "aksiyon": self.muzik_merkezini_ac},
            {"ikon": "🎬", "baslik": "Sinematik MP4 Video Oynatıcıyı Aç (Tam Ekran)", "kategori": "Multimedya", "aksiyon": self.sinematik_video_sec_ve_oynat},
            {"ikon": "⚡", "baslik": "Ollama ve Yapay Zeka Modellerini Otomatik Kur", "kategori": "Sistem", "aksiyon": self.ollama_otomatik_kurulumunu_ac},
            {"ikon": "💬", "baslik": "Sohbet Sekmesine Geç", "kategori": "Sekme", "aksiyon": lambda: (self.tabview.set("💬 Sohbet"), self._ust_sekme_degisti())},
            {"ikon": "🐍", "baslik": "Python IDE & Editörü Aç", "kategori": "Yazılım", "aksiyon": lambda: (self.tabview.set("🐍 Python IDE & Editör"), self._ust_sekme_degisti())},
            {"ikon": "📄", "baslik": "Yeni Python Dosyası Aç (IDE)", "kategori": "Yazılım", "aksiyon": lambda: (self.tabview.set("🐍 Python IDE & Editör"), self._ust_sekme_degisti(), self.ide_panel and self.ide_panel.yeni_sekme_ac())},
            {"ikon": "📦", "baslik": "Pip Paket Yöneticisini Aç", "kategori": "Yazılım", "aksiyon": lambda: (self.tabview.set("🐍 Python IDE & Editör"), self._ust_sekme_degisti(), self.ide_panel and self.ide_panel.pip_yoneticisini_ac())},
            {"ikon": "📁", "baslik": "Dosya Gezgini & Kasa Sekmesine Geç", "kategori": "Sekme", "aksiyon": lambda: (self.tabview.set("📁 Dosya Gezgini & Kasa"), self._ust_sekme_degisti())},
            {"ikon": "📊", "baslik": "Kazınan Veri & Analiz Merkezi Sekmesine Geç", "kategori": "Sekme", "aksiyon": lambda: (self.tabview.set("📊 Kazınan Veri & Analiz Merkezi"), self._ust_sekme_degisti())},
            {"ikon": "📐", "baslik": "CNC G-Code 2D Simülatör Sekmesine Geç", "kategori": "Sekme", "aksiyon": lambda: (self.tabview.set("📐 CNC G-Code 2D Simülatör"), self._ust_sekme_degisti())},
            {"ikon": "🛡️", "baslik": "Ağ IPS Güvenlik Kalkanı Sekmesine Geç", "kategori": "Sekme", "aksiyon": lambda: (self.tabview.set("🛡️ Güvenlik"), self._ust_sekme_degisti())},
            {"ikon": "🔬", "baslik": "Tersine Mühendislik & Hex Sekmesine Geç", "kategori": "Sekme", "aksiyon": lambda: (self.tabview.set("🔬 Tersine Mühendislik"), self._ust_sekme_degisti())},
            {"ikon": "🦠", "baslik": "Antivirüs & EDR Sekmesine Geç", "kategori": "Sekme", "aksiyon": lambda: (self.tabview.set("🦠 Antivirüs & EDR"), self._ust_sekme_degisti())},
            {"ikon": "🧹", "baslik": "RAM'i Temizle ve Bellek Optimize Et", "kategori": "Sistem", "aksiyon": self.ram_optimize_et},
            {"ikon": "📂", "baslik": "Sohbet Oturumları ve Geçmişi Aç", "kategori": "Sohbet", "aksiyon": self.sohbet_oturumlarini_ac},
            {"ikon": "➕", "baslik": "Yeni Sohbet Başlat", "kategori": "Sohbet", "aksiyon": self.yeni_sohbet_baslat},
            {"ikon": "🎙️", "baslik": "Ses Kaydedici Stüdyosunu Aç", "kategori": "Multimedya", "aksiyon": self.ses_kaydedici_studyosunu_ac},
            {"ikon": "🎬", "baslik": "Ekran & Ses Video Kaydediciyi Aç", "kategori": "Multimedya", "aksiyon": self.video_kaydedici_studyosunu_ac},
            {"ikon": "📷", "baslik": "Kamera & Webcam Stüdyosunu Aç", "kategori": "Multimedya", "aksiyon": self.kamera_studyosunu_ac},
            {"ikon": "🚀", "baslik": "Simülasyonlar & NASA Merkezini Aç", "kategori": "Bilim", "aksiyon": self.simulasyonlar_merkezini_ac},
            {"ikon": "📝", "baslik": "Altar Belgeyi Aç (Kelime İşlemci)", "kategori": "Araç", "aksiyon": self.word_programini_ac},
            {"ikon": "💾", "baslik": "Sohbeti Dosyaya Kaydet (.md / .txt)", "kategori": "Rapor", "aksiyon": self.sohbeti_disa_aktar},
            {"ikon": "✂️", "baslik": "Ekrandan Bölge Yakala ve AI'a Sor", "kategori": "Araç", "aksiyon": self.ekrandan_bolge_yakala_ve_sor},
            {"ikon": "📦", "baslik": "EDR Karantina Kasasını Aç", "kategori": "Güvenlik", "aksiyon": self.karantina_kasasini_ac},
            {"ikon": "🌐", "baslik": "Canlı Ağ Radarı Modalını Aç", "kategori": "Ağ", "aksiyon": self.ag_radarini_ac},
            {"ikon": "🎬", "baslik": "Sinematik Doğa Açılış Animasyonunu Oynat (60 FPS)", "kategori": "Görsel", "aksiyon": self._sinematik_animasyon_oynat},
            {"ikon": "🧩", "baslik": "Python IDE Şablon Kütüphanesini Aç", "kategori": "Yazılım", "aksiyon": lambda: (self.tabview.set("🐍 Python IDE & Editör"), self._ust_sekme_degisti(), self.ide_panel and self.ide_panel.sablon_secici_ac())},
            {"ikon": "🌲", "baslik": "Temayı Değiştir: Zümrüt Doğa & Şelale", "kategori": "Tema", "aksiyon": lambda: self._tema_degistir("🌲 Zümrüt Doğa & Şelale")},
            {"ikon": "🌌", "baslik": "Temayı Değiştir: Altar Siber Orijinal", "kategori": "Tema", "aksiyon": lambda: self._tema_degistir("🌌 Altar Siber Orijinal")},
            {"ikon": "⚡", "baslik": "Temayı Değiştir: Matrix Neon", "kategori": "Tema", "aksiyon": lambda: self._tema_degistir("⚡ Matrix Neon")},
            {"ikon": "🔮", "baslik": "Temayı Değiştir: Cyberpunk Synthwave", "kategori": "Tema", "aksiyon": lambda: self._tema_degistir("🔮 Cyberpunk Synthwave")},
            {"ikon": "⚡", "baslik": "Yapay Zeka Gücünü Aç / Kapat", "kategori": "Yapay Zeka", "aksiyon": self.yapay_zeka_guc_degistir},
        ]
        AltarKomutPaletiModal(self, eylemler)

    # =====================================================================
    # SEKME GEÇİŞLERİ VE PANEL HAZIRLAMA METOTLARI
    # =====================================================================
    def _ust_sekme_degisti(self):
        aktif_sekme = self.tabview.get()
        if hasattr(self, "sinematik_arka_plan") and self.sinematik_arka_plan:
            try:
                self.sinematik_arka_plan.mod_degistir(aktif_sekme)
            except Exception:
                pass

        if "Oyun" in aktif_sekme:
            if not getattr(self, "_oyun_yuklendi", False):
                self._oyun_yuklendi = True
                self._oyun_sekmesini_tekil_hazirla()
            self.bottom_panel.pack_forget()

        elif "Müzik" in aktif_sekme:
            if not getattr(self, "_muzik_yuklendi", False):
                self._muzik_yuklendi = True
                self._muzik_sekmesini_tekil_hazirla()
            self.bottom_panel.pack_forget()

        elif "Dosya Gezgini" in aktif_sekme:
            if not self._gezgin_yuklendi:
                self._gezgin_yuklendi = True
                self._gezgin_sekmesini_tekil_hazirla()
            self.bottom_panel.pack_forget()

        elif aktif_sekme == "📐 CNC G-Code 2D Simülatör":
            if not self._gcode_yuklendi:
                self._gcode_yuklendi = True
                self._gcode_simulator_sekmesini_hazirla()
            self.bottom_panel.pack_forget()

        elif aktif_sekme == "🛡️ Güvenlik":
            if not self._guvenlik_yuklendi:
                self._guvenlik_yuklendi = True
                self._guvenlik_sekmesini_tekil_hazirla()
            if not getattr(self, "_guvenlik_alt_yuklendi", False):
                self._guvenlik_alt_yuklendi = True
                self._guvenlik_alt_panellerini_hazirla()
            self.bottom_panel.pack(side="bottom", fill="x", padx=10, pady=(0, 10), before=self.tabview)
            self.ust_ince_serit.pack_forget()
            self.action_frame.pack_forget()
            self.user_input.pack_forget()
            self.btn_send.pack_forget()
            self.analiz_alt_iki_bolum.pack_forget()
            self.tersine_alt_dpi_tek_bolum.pack_forget()
            self.guvenlik_alt_iki_bolum.pack(side="left", fill="both", expand=True, padx=0)

        elif aktif_sekme == "📊 Kazınan Veri & Analiz Merkezi":
            if not self._analiz_alt_yuklendi:
                self._analiz_alt_yuklendi = True
                self._analiz_alt_panellerini_hazirla()
            self.bottom_panel.pack(side="bottom", fill="x", padx=10, pady=(0, 10), before=self.tabview)
            self.ust_ince_serit.pack_forget()
            self.action_frame.pack_forget()
            self.user_input.pack_forget()
            self.btn_send.pack_forget()
            self.guvenlik_alt_iki_bolum.pack_forget()
            self.tersine_alt_dpi_tek_bolum.pack_forget()
            self.analiz_alt_iki_bolum.pack(side="left", fill="both", expand=True, padx=0)

        elif aktif_sekme == "🔬 Tersine Mühendislik":
            if not self._tersine_yuklendi:
                self._tersine_yuklendi = True
                self._tersine_muhendislik_sekmesini_tekil_hazirla()
            self.bottom_panel.pack(side="bottom", fill="x", padx=10, pady=(0, 10), before=self.tabview)
            self.ust_ince_serit.pack_forget()
            self.action_frame.pack_forget()
            self.user_input.pack_forget()
            self.btn_send.pack_forget()
            self.guvenlik_alt_iki_bolum.pack_forget()
            self.analiz_alt_iki_bolum.pack_forget()
            self.tersine_alt_dpi_tek_bolum.pack(side="left", fill="both", expand=True, padx=0)

        elif aktif_sekme == "🦠 Antivirüs & EDR":
            if not self._edr_yuklendi:
                self._edr_yuklendi = True
                self._edr_sekmesini_tekil_hazirla()
            self.bottom_panel.pack_forget()

        elif aktif_sekme == "🐍 Python IDE & Editör":
            if not self._ide_yuklendi:
                self._ide_yuklendi = True
                self._ide_sekmesini_tekil_hazirla()
            self.bottom_panel.pack_forget()

        else:
            # Sohbet sekmesi
            self.bottom_panel.pack(side="bottom", fill="x", padx=10, pady=(0, 10), before=self.tabview)
            self.guvenlik_alt_iki_bolum.pack_forget()
            self.analiz_alt_iki_bolum.pack_forget()
            self.tersine_alt_dpi_tek_bolum.pack_forget()
            self.user_input.pack_forget()
            self.btn_send.pack_forget()
            self.action_frame.pack_forget()
            self.ust_ince_serit.pack_forget()

            self.ust_ince_serit.pack(side="top", fill="x", padx=0, pady=(0, 3))
            self.action_frame.pack(side="left", padx=(0, 10))
            self.user_input.pack(side="left", fill="both", expand=True, padx=(0, 10))
            self.btn_send.pack(side="right")

    def _edr_sekmesini_tekil_hazirla(self):
        if EDR_KALKAN_AVAILABLE and AltarEDRAntivirusSekmesi:
            self.edr_panel = AltarEDRAntivirusSekmesi(
                self.tab_edr,
                ai_analiz_callback=self._harici_raporu_ai_ile_analiz_et
            )
            self.edr_panel.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(
                self.tab_edr,
                text="⚠️ 'altar_edr_kalkan.py' dosyası aynı klasörde bulunamadı.",
                text_color="#FF4444"
            ).pack(pady=40)

    def _ide_sekmesini_tekil_hazirla(self):
        if PYTHON_IDE_AVAILABLE and AltarPythonIDESekmesi:
            self.ide_panel = AltarPythonIDESekmesi(
                self.tab_ide,
                calisma_dizini=_ANA_DIZIN,
                ai_aktarim_callback=self._ide_kodunu_ai_ile_analiz_et
            )
            self.ide_panel.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(
                self.tab_ide,
                text="⚠️ 'altar_python_ide.py' dosyası aynı klasörde bulunamadı.",
                text_color="#FF4444"
            ).pack(pady=40)

    def _ide_kodunu_ai_ile_analiz_et(self, istek_metni: str):
        self.active_lang_var.set("Yazılım")
        self._harici_raporu_ai_ile_analiz_et(istek_metni)

    def _gezgin_sekmesini_tekil_hazirla(self):
        if DOSYA_GEZGINI_AVAILABLE and DosyaGezginiVeKasaSekmesi:
            self.gezgin_panel = DosyaGezginiVeKasaSekmesi(
                self.tab_gezgin,
                ai_analiz_callback=self._harici_raporu_ai_ile_analiz_et
            )
            self.gezgin_panel.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(
                self.tab_gezgin,
                text="⚠️ 'dosya_gezgini_kasa.py' dosyası aynı klasörde bulunamadı.",
                text_color="#FF4444"
            ).pack(pady=40)

    def _analiz_alt_panellerini_hazirla(self):
        if MODEM_PANEL_AVAILABLE and ModemHotspotPaneli:
            self.sol_modem_bolumu = ModemHotspotPaneli(self.analiz_alt_iki_bolum)
            self.sol_modem_bolumu.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        else:
            ctk.CTkLabel(
                self.analiz_alt_iki_bolum, text="⚠️ 'Modem.py' içinde ModemHotspotPaneli bulunamadı.", text_color="#FF4444"
            ).grid(row=0, column=0, sticky="nsew", padx=5)

        if PORT_PANEL_AVAILABLE and PortVeUygulamaPaneli:
            self.sag_port_bolumu = PortVeUygulamaPaneli(self.analiz_alt_iki_bolum)
            self.sag_port_bolumu.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        else:
            ctk.CTkLabel(
                self.analiz_alt_iki_bolum, text="⚠️ 'Port scanner.py' içinde PortVeUygulamaPaneli bulunamadı.", text_color="#FF4444"
            ).grid(row=0, column=1, sticky="nsew", padx=5)

    def _guvenlik_sekmesini_tekil_hazirla(self):
        if GUVENLIK_SEKME_AVAILABLE and GuvenlikDuvariSekmesi:
            self.guvenlik_panel = GuvenlikDuvariSekmesi(
                self.tab_guvenlik, ai_analiz_callback=self._harici_raporu_ai_ile_analiz_et
            )
            self.guvenlik_panel.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(
                self.tab_guvenlik,
                text="⚠️ 'Güvenlik Duvarı Tuzaklı.py' dosyası bulunamadı veya yüklenemedi.",
                text_color="#FF4444"
            ).pack(pady=40)

    def _guvenlik_alt_panellerini_hazirla(self):
        if AG_OPERASYON_AVAILABLE and AgOperasyonPaneli:
            self.sol_ag_bolumu = AgOperasyonPaneli(self.guvenlik_alt_iki_bolum)
            self.sol_ag_bolumu.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        else:
            ctk.CTkLabel(
                self.guvenlik_alt_iki_bolum, text="⚠️ 'ag_operasyon_merkezi.py' bulunamadı.", text_color="#FF4444"
            ).grid(row=0, column=0, sticky="nsew", padx=5)

        if DOSYA_SIFRELEME_AVAILABLE and DosyaSifrelemePaneli:
            self.sag_sifreleme_bolumu = DosyaSifrelemePaneli(self.guvenlik_alt_iki_bolum)
            self.sag_sifreleme_bolumu.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        else:
            ctk.CTkLabel(
                self.guvenlik_alt_iki_bolum, text="⚠️ 'Dosya_Şifreleme.py' bulunamadı.", text_color="#FF4444"
            ).grid(row=0, column=1, sticky="nsew", padx=5)

    def _tersine_muhendislik_sekmesini_tekil_hazirla(self):
        if SIBER_HEX_AVAILABLE and TersineMuhendislikSekmesi:
            self.tersine_muh_panel = TersineMuhendislikSekmesi(
                self.tab_tersine_muh, ai_analiz_callback=self._harici_raporu_ai_ile_analiz_et
            )
            self.tersine_muh_panel.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(
                self.tab_tersine_muh,
                text="⚠️ 'siber_hex_analizor.py' dosyası bulunamadı.",
                text_color="#FF4444"
            ).pack(pady=40)

        if DPI_PANEL_AVAILABLE and DerinPaketAnalizPaneli:
            self.dpi_tam_panel = DerinPaketAnalizPaneli(
                self.tersine_alt_dpi_tek_bolum,
                ai_analiz_callback=self._harici_raporu_ai_ile_analiz_et
            )
            self.dpi_tam_panel.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(
                self.tersine_alt_dpi_tek_bolum,
                text="⚠️ 'DPI.py' içinde DerinPaketAnalizPaneli bulunamadı.",
                text_color="#FF4444"
            ).pack(pady=30)

    def _guvenlik_ve_tersine_muhendislik_sekmelerini_hazirla(self):
        if not self._guvenlik_yuklendi:
            self._guvenlik_yuklendi = True
            self._guvenlik_sekmesini_tekil_hazirla()
        if not self._tersine_yuklendi:
            self._tersine_yuklendi = True
            self._tersine_muhendislik_sekmesini_tekil_hazirla()

    # =====================================================================
    # SES, VİDEO VE KAMERA STÜDYOSU / HIZLI KAYIT METOTLARI
    # =====================================================================
    def ses_kaydedici_studyosunu_ac(self):
        if not SES_KAYDEDICI_AVAILABLE or not AltarSesKaydediciPenceresi:
            messagebox.showerror("Eksik Modül", "'Ses kaydedici.py' modülü bulunamadı veya yüklenemedi!", parent=self)
            return
        win_ses = AltarSesKaydediciPenceresi(
            self,
            motor=self.ses_kayit_motoru,
            metin_aktar_callback=lambda m: self._ui_gorevi_ekle(lambda: self.user_input.insert("end", m + " "))
        )
        self._aktif_pencereler["ses"] = win_ses

    def hizli_ses_kaydi_baslat_durdur(self):
        if not self.ses_kayit_motoru:
            messagebox.showerror("Eksik Modül", "'Ses kaydedici.py' modülü bulunamadı!", parent=self)
            return

        if not self.ses_kayit_motoru.kayit_aktif:
            yol = self.ses_kayit_motoru.kaydi_baslat(
                bitti_callback=lambda basarili, d_yolu: self._ui_gorevi_ekle(
                    lambda: self.lbl_ek_bilgi.configure(
                        text=f"✅ Ses Kaydedildi: {os.path.basename(d_yolu)}" if basarili else "❌ Ses kayıt hatası!"
                    )
                )
            )
            self.btn_hizli_ses_kayit.configure(text="⏹️ Kaydı Bitir", fg_color="#00A86B")
            self.lbl_ek_bilgi.configure(text=f"🔴 Kaydediliyor: {os.path.basename(yol)}...")
        else:
            self.ses_kayit_motoru.kaydi_durdur()
            self.btn_hizli_ses_kayit.configure(text="🔴 Hızlı Kayıt", fg_color="#374151")

    def video_kaydedici_studyosunu_ac(self):
        if not VIDEO_KAYDEDICI_AVAILABLE or not AltarVideoKaydediciPenceresi:
            messagebox.showerror("Eksik Modül", "'Video_Kaydedici.py' modülü bulunamadı veya yüklenemedi!", parent=self)
            return
        win_video = AltarVideoKaydediciPenceresi(self, motor=self.ekran_video_motoru)
        self._aktif_pencereler["ekran_video"] = win_video

    def hizli_video_kaydi_baslat_durdur(self):
        if not self.ekran_video_motoru:
            messagebox.showerror("Eksik Modül", "'Video_Kaydedici.py' modülü bulunamadı!", parent=self)
            return

        if not self.ekran_video_motoru.kayit_aktif:
            yol = self.ekran_video_motoru.kaydi_baslat(
                bitti_callback=lambda basarili, d_yolu: self._ui_gorevi_ekle(
                    lambda: self.lbl_ek_bilgi.configure(text=f"✅ Video Kaydedildi: {os.path.basename(d_yolu)}")
                )
            )
            self.btn_hizli_video_kayit.configure(text="⏹️ Videoyu Bitir", fg_color="#00A86B")
            self.lbl_ek_bilgi.configure(text=f"🎬 Ekran+Ses Kaydediliyor: {os.path.basename(yol)}...")
        else:
            self.lbl_ek_bilgi.configure(text="⏳ Video ve ses birleştiriliyor...")
            self.ekran_video_motoru.kaydi_durdur()
            self.btn_hizli_video_kayit.configure(text="⏺️ Hızlı Video", fg_color="#374151")

    def kamera_studyosunu_ac(self):
        if not KAMERA_KAYDEDICI_AVAILABLE or not AltarKameraStüdyosuPenceresi:
            messagebox.showerror("Eksik Modül", "'Kamera_Kaydedici.py' modülü bulunamadı veya yüklenemedi!", parent=self)
            return
        win_kam = AltarKameraStüdyosuPenceresi(self, motor=self.kamera_video_motoru)
        self._aktif_pencereler["kamera"] = win_kam

    def hizli_kamera_kaydi_baslat_durdur(self):
        if not self.kamera_video_motoru:
            messagebox.showerror("Eksik Modül", "'Kamera_Kaydedici.py' modülü bulunamadı!", parent=self)
            return

        if not self.kamera_video_motoru.kayit_aktif:
            yol = self.kamera_video_motoru.kaydi_baslat(
                bitti_callback=lambda basarili, d_yolu: self._ui_gorevi_ekle(
                    lambda: (
                        self.lbl_ek_bilgi.configure(text=f"✅ Kamera Kaydedildi: {os.path.basename(d_yolu)}"),
                        self.kamera_video_motoru.kamerayi_kapat()
                    )
                )
            )
            self.btn_hizli_kamera_kayit.configure(text="⏹️ Kamerayı Bitir", fg_color="#00A86B")
            self.lbl_ek_bilgi.configure(text=f"📷 Kamera+Ses Kaydediliyor: {os.path.basename(yol)}...")
        else:
            self.lbl_ek_bilgi.configure(text="⏳ Kamera kaydı birleştiriliyor...")
            self.kamera_video_motoru.kaydi_durdur()
            self.btn_hizli_kamera_kayit.configure(text="⏺️ Hızlı Kamera", fg_color="#374151")

    # =====================================================================
    # KAZINAN VERİ & ANALİZ MERKEZİ SEKMESİ METOTLARI
    # =====================================================================
    def _analiz_sekmesini_hazirla(self):
        ust_bar = ctk.CTkFrame(self.tab_analiz, fg_color="transparent")
        ust_bar.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            ust_bar, text="📂 Kategori Filtresi:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=5)

        self.kategori_filtre_var = ctk.StringVar(value="Tüm Kategoriler")
        self.kategori_menu = ctk.CTkOptionMenu(
            ust_bar,
            variable=self.kategori_filtre_var,
            values=[
                "Tüm Kategoriler",
                "1. Başlık Hiyerarşisi",
                "2. Veri Tabloları",
                "3. İndirilebilir Belgeler & Veri Setleri",
                "4. Önemli Paragraflar & Makaleler",
                "5. Sayfa Bağlantıları"
            ],
            width=260,
            command=self.kategori_gorunumu_guncelle
        )
        self.kategori_menu.pack(side="left", padx=8)

        ctk.CTkButton(
            ust_bar, text="📂 SSD Arşivinden JSON Yükle", width=190,
            fg_color="#4B0082", command=self.ssd_arsivinden_json_yukle
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            ust_bar, text="🧠 Seçili Kategoriyi AI İle Analiz Et", width=220,
            fg_color="#008080", command=self.secili_kategoriyi_ai_ile_analiz_et
        ).pack(side="right", padx=5)

        self.analiz_textbox = ctk.CTkTextbox(
            self.tab_analiz, font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word", fg_color="#121824", text_color="#00FFCC"
        )
        self.analiz_textbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.analiz_textbox.insert(
            "end",
            "📊 [KAZINAN VERİ & ANALİZ MERKEZİ]\n"
            "Sol alttaki 'Web' butonuna tıklayarak herhangi bir web sitesini kategorize edip buraya gönderebilir "
            "veya SSD'deki 'scraped_archive' klasöründen daha önce kazıdığınız JSON dosyalarını yükleyebilirsiniz.\n"
        )
        self.analiz_textbox.configure(state="disabled")

    def analiz_sekmesine_veri_ekle(self, veri_paketi: dict, tam_metin: str):
        self.son_kazinan_paket = veri_paketi
        self.tabview.set("📊 Kazınan Veri & Analiz Merkezi")
        self._ust_sekme_degisti()
        self.kategori_filtre_var.set("Tüm Kategoriler")
        self.analiz_textbox.configure(state="normal")
        self.analiz_textbox.delete("1.0", "end")
        self.analiz_textbox.insert("end", tam_metin)
        self.analiz_textbox.configure(state="disabled")

    def kategori_gorunumu_guncelle(self, secim: str):
        if not self.son_kazinan_paket:
            return
        kat = self.son_kazinan_paket.get("kategoriler", {})
        baslik = f"📌 KAYNAK: {self.son_kazinan_paket.get('kaynak_url')} ({self.son_kazinan_paket.get('kazima_tarihi')})\n\n"

        if secim == "1. Başlık Hiyerarşisi":
            icerik = "\n".join(kat.get("baslik_hiyerarsisi", [])) or "Bu kategoride veri yok."
        elif secim == "2. Veri Tabloları":
            icerik = "\n\n".join(kat.get("veri_tablolari", [])) or "Bu kategoride tablo bulunamadı."
        elif secim == "3. İndirilebilir Belgeler & Veri Setleri":
            icerik = "\n".join(kat.get("indirilebilir_veri_ve_belgeler", [])) or "İndirilebilir belge bulunamadı."
        elif secim == "4. Önemli Paragraflar & Makaleler":
            icerik = "\n\n".join([f"• {p}" for p in kat.get("onemli_paragraflar", [])]) or "Paragraf bulunamadı."
        elif secim == "5. Sayfa Bağlantıları":
            icerik = "\n".join(kat.get("sayfa_baglantilari", [])) or "Bağlantı bulunamadı."
        else:
            icerik = json.dumps(self.son_kazinan_paket, ensure_ascii=False, indent=2)

        self.analiz_textbox.configure(state="normal")
        self.analiz_textbox.delete("1.0", "end")
        self.analiz_textbox.insert("end", baslik + icerik)
        self.analiz_textbox.configure(state="disabled")

    def ssd_arsivinden_json_yukle(self):
        arsiv_yolu = os.path.join(_ANA_DIZIN, "scraped_archive")
        if not os.path.exists(arsiv_yolu):
            os.makedirs(arsiv_yolu)
        dosya = filedialog.askopenfilename(
            initialdir=arsiv_yolu,
            title="Kategorize JSON Verisi Seç",
            filetypes=[("JSON Veri Dosyası", "*.json"), ("Tüm Dosyalar", "*.*")]
        )
        if dosya:
            try:
                with open(dosya, "r", encoding="utf-8") as f:
                    paket = json.load(f)
                self.son_kazinan_paket = paket
                self.kategori_gorunumu_guncelle("Tüm Kategoriler")
            except Exception as e:
                messagebox.showerror("Hata", f"JSON dosyası okunamadı: {e}", parent=self)

    def secili_kategoriyi_ai_ile_analiz_et(self):
        if not self.yapay_zeka_aktif:
            messagebox.showwarning(
                "Yapay Zeka Kapalı",
                "Yapay Zeka şu anda RAM ve pil tasarrufu için KAPALI durumda!\n\n"
                "Analiz yapmak için lütfen üst menüdeki '🔴 Yapay Zeka: Kapalı' butonuna tıklayarak aktif edin.",
                parent=self
            )
            return

        icerik = self.analiz_textbox.get("1.0", "end").strip()
        if not icerik or not self.son_kazinan_paket:
            messagebox.showwarning("Uyarı", "Analiz edilecek kazınmış veri bulunamadı.", parent=self)
            return

        self.tabview.set("💬 Sohbet")
        self._ust_sekme_degisti()
        komut = (
            f"Aşağıda web kazıyıcı tarafından kategorize edilmiş veriler yer almaktadır. "
            f"Lütfen bu verileri detaylıca incele, önemli bulguları, sayısal değerleri ve kritik noktaları raporla:\n\n{icerik[:6000]}"
        )
        self.log_to_chat("Sen (Analiz Merkezi)", "Seçili kategorize web verisini analiz et.", final=True)

        aktif_motor = self.motor_var.get()
        secilen_dil = self.active_lang_var.get()
        if aktif_motor == "Yerel (Ollama)":
            secilen_model = self.active_model_var.get()
            self._secili_yerel_model_bellek = secilen_model
            threading.Thread(
                target=self.model_ile_konus,
                args=(secilen_model, secilen_dil, komut, None),
                daemon=True
            ).start()
        else:
            threading.Thread(
                target=self.api_ile_konus,
                args=(self.active_api_model_var.get(), secilen_dil, komut, None),
                daemon=True
            ).start()

    # =====================================================================
    # SWANSOFT 3D VE DAHİLİ 2D G-CODE SİMÜLATÖR METOTLARI
    # =====================================================================
    def _gcode_simulator_sekmesini_hazirla(self):
        if SWANSOFT_AVAILABLE and SwansoftCNCSekmesi:
            self.swansoft_panel = SwansoftCNCSekmesi(self.tab_gcode)
            self.swansoft_panel.pack(fill="both", expand=True)
            return

        cerceve = ctk.CTkFrame(self.tab_gcode, fg_color="transparent")
        cerceve.pack(fill="both", expand=True, padx=5, pady=5)

        sol_panel = ctk.CTkFrame(cerceve, width=360)
        sol_panel.pack(side="left", fill="y", padx=(0, 8))

        ctk.CTkLabel(
            sol_panel, text="⚙️ G-Code Girişi (X-Y Simülasyonu)", font=ctk.CTkFont(weight="bold")
        ).pack(pady=(8, 4), padx=10, anchor="w")

        self.gcode_editor = ctk.CTkTextbox(
            sol_panel, width=340, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#121212"
        )
        self.gcode_editor.pack(fill="both", expand=True, padx=8, pady=4)
        ornek_gcode = (
            "G21 G90 G17\n"
            "G00 X0 Y0 Z5\n"
            "G01 Z-1 F200\n"
            "G01 X60 Y0 F500\n"
            "G01 X60 Y40\n"
            "G01 X0 Y40\n"
            "G01 X0 Y0\n"
            "G00 Z10\n"
            "G00 X15 Y10\n"
            "G01 Z-1\n"
            "G01 X45 Y10\n"
            "G01 X30 Y30\n"
            "G01 X15 Y10\n"
            "G00 Z15\n"
            "M30"
        )
        self.gcode_editor.insert("1.0", ornek_gcode)

        btn_ciz = ctk.CTkButton(
            sol_panel, text="▶️ Takım Yolunu 2D Çiz & Denetle",
            fg_color="#00A86B", hover_color="#007F50", command=self.gcode_takim_yolunu_ciz
        )
        btn_ciz.pack(fill="x", padx=8, pady=6)

        sag_panel = ctk.CTkFrame(cerceve, fg_color="#0d1117")
        sag_panel.pack(side="right", fill="both", expand=True)

        self.lbl_gcode_bilgi = ctk.CTkLabel(
            sag_panel,
            text="🟥 Kesikli Kırmızı: G00 (Boşta Hızlı Hareket)  |  🟩 Yeşil: G01/G02/G03 (Talaşlı Kesim)",
            font=ctk.CTkFont(family="Consolas", size=12), text_color="#00FFCC"
        )
        self.lbl_gcode_bilgi.pack(side="top", pady=4)

        self.gcode_canvas = tk.Canvas(sag_panel, bg="#090d16", highlightthickness=1, highlightbackground="#30363d")
        self.gcode_canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def gcode_takim_yolunu_ciz(self):
        metin = self.gcode_editor.get("1.0", "end")
        self.gcode_canvas.delete("all")

        w = max(self.gcode_canvas.winfo_width(), 500)
        h = max(self.gcode_canvas.winfo_height(), 400)

        cur_x, cur_y, cur_z = 0.0, 0.0, 5.0
        cur_mod = "G00"
        segmentler = []
        xs, ys = [0.0], [0.0]

        for satir in metin.splitlines():
            temiz = _RE_GCODE_COMMENT.sub('', satir).split(';')[0].upper().strip()
            if not temiz:
                continue
            if re.search(r'\bG0*0\b', temiz):
                cur_mod = "G00"
            elif re.search(r'\bG0*[123]\b', temiz):
                cur_mod = "G01"

            mx = re.search(r'X([-+]?\d*\.?\d+)', temiz)
            my = re.search(r'Y([-+]?\d*\.?\d+)', temiz)
            mz = re.search(r'Z([-+]?\d*\.?\d+)', temiz)

            nx = float(mx.group(1)) if mx else cur_x
            ny = float(my.group(1)) if my else cur_y
            nz = float(mz.group(1)) if mz else cur_z

            if (nx != cur_x) or (ny != cur_y):
                segmentler.append((cur_x, cur_y, nx, ny, cur_mod))
                xs.append(nx)
                ys.append(ny)

            cur_x, cur_y, cur_z = nx, ny, nz

        if not segmentler:
            return

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1.0)
        span_y = max(max_y - min_y, 1.0)

        kenar_boslugu = 50
        olcek = min((w - 2 * kenar_boslugu) / span_x, (h - 2 * kenar_boslugu) / span_y)

        def ekran_koordinati(x_val, y_val):
            sx = kenar_boslugu + (x_val - min_x) * olcek
            sy = h - (kenar_boslugu + (y_val - min_y) * olcek)
            return sx, sy

        ox, oy = ekran_koordinati(0, 0)
        self.gcode_canvas.create_oval(ox - 4, oy - 4, ox + 4, oy + 4, fill="#FFFF00", outline="#FFFF00")
        self.gcode_canvas.create_text(ox + 28, oy - 10, text="(X0, Y0)", fill="#FFFF00", font=("Consolas", 9))

        for x1, y1, x2, y2, mod in segmentler:
            sx1, sy1 = ekran_koordinati(x1, y1)
            sx2, sy2 = ekran_koordinati(x2, y2)
            if mod == "G00":
                self.gcode_canvas.create_line(sx1, sy1, sx2, sy2, fill="#FF4444", width=1.5, dash=(4, 4))
            else:
                self.gcode_canvas.create_line(sx1, sy1, sx2, sy2, fill="#00FF88", width=2.5)

    # =====================================================================
    # SOL ALT ARAÇ BUTONLARI VE DONANIM TELEMETRİSİ
    # =====================================================================
    def word_programini_ac(self):
        olasi_isimler = ["Word Programı.py", "word_programi.py", "AltarEditorPro.py"]
        bulunan = any(os.path.exists(os.path.join(_ANA_DIZIN, isim)) for isim in olasi_isimler)

        if not bulunan:
            messagebox.showerror(
                "Eksik Modül",
                "'Word Programı.py' dosyası aynı klasörde bulunamadı!\nLütfen dosyanın ana kodla aynı dizinde olduğundan emin olun.",
                parent=self
            )
            return

        p = multiprocessing.Process(target=_word_editor_surecini_baslat, args=("",), daemon=True)
        p.start()

    def telemetri_guncelle(self):
        if not self.winfo_exists():
            return

        def _arka_plan_oku():
            try:
                cpu = psutil.cpu_percent(interval=None) if PSUTIL_AVAILABLE else 0.0
                if PSUTIL_AVAILABLE:
                    mem = psutil.virtual_memory()
                    ram_yuzde = mem.percent
                    toplam_mb = max(mem.total / (1024 ** 2), 1.0)
                    try:
                        altar_proc = psutil.Process(os.getpid())
                        altar_mb = altar_proc.memory_info().rss / (1024 ** 2)
                        altar_yuzde = (altar_mb / toplam_mb) * 100.0
                    except Exception:
                        altar_mb, altar_yuzde = 0.0, 0.0
                else:
                    ram_yuzde, altar_mb, altar_yuzde = 0.0, 0.0, 0.0

                gpu = self.gpu_reader.gpu_yuzdesi_oku(ollama_client=None)

                renk = "#FF4444" if (altar_yuzde > 50 or cpu > 90) else "#00FF88"
                telemetri_metni = (
                    f"CPU: %{cpu:.0f} | GPU: %{gpu:.0f} | "
                    f"Altar RAM: %{altar_yuzde:.1f} ({altar_mb:.0f} MB) | Sistem: %{ram_yuzde:.0f}"
                )

                def _etiket_yaz():
                    if self.winfo_exists():
                        self.lbl_telemetri.configure(text=telemetri_metni, text_color=renk)

                self._ui_gorevi_ekle(_etiket_yaz)
            except Exception:
                pass

        threading.Thread(target=_arka_plan_oku, daemon=True).start()
        self.after(3000, self.telemetri_guncelle)

    def sohbeti_disa_aktar(self):
        icerik = self.chat_display.get("1.0", "end").strip()
        if not icerik:
            messagebox.showinfo("Bilgi", "Kaydedilecek sohbet içeriği bulunamadı.", parent=self)
            return

        varsayilan_ad = f"Altar_Rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        dosya_yolu = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".md",
            initialfile=varsayilan_ad,
            filetypes=[("Markdown Raporu", "*.md"), ("Metin Dosyası", "*.txt")]
        )
        if dosya_yolu:
            if os.path.exists(dosya_yolu):
                messagebox.showwarning(
                    "Güvenlik Koruması",
                    "Seçtiğiniz isimde bir dosya zaten mevcut! Hiçbir dosyanın içeriğinin değişmemesi için üzerine yazma işlemi engellendi. Lütfen yeni bir dosya adı girin.",
                    parent=self
                )
                return
            try:
                with open(dosya_yolu, "x", encoding="utf-8") as f:
                    f.write("# ALTAR - ANALİZ RAPORU\n")
                    f.write(
                        f"**Tarih:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Profil:** {self.active_lang_var.get()}\n\n---\n\n")
                    f.write(icerik)
                messagebox.showinfo("Başarılı", f"Rapor yeni dosya olarak güvenle kaydedildi:\n{dosya_yolu}", parent=self)
            except Exception as e:
                messagebox.showerror("Kayıt Hatası", f"Dosya oluşturulurken hata meydana geldi: {e}", parent=self)

    def toggle_nasa_sim(self):
        if not NASA_SCRAPER_AVAILABLE:
            messagebox.showerror("Eksik Modül",
                                 "scraper.py dosyası bulunamadı! Lütfen iki kodun aynı klasörde olduğundan emin olun.",
                                 parent=self)
            return
        NasaScraperWindow(self)

    def simulasyonlar_merkezini_ac(self):
        """Hızlı Kamera Kaydı yanındaki '🚀 Simülasyonlar' butonuna tıklandığında NASA ve Simülasyon merkezini açar."""
        AltarSimulasyonMerkeziPenceresi(self)

    def nasa_yanma_analizi_calistir(self, ozel_soru: str = ""):
        """Simülasyonlar penceresinden gelen NASA Yanma Analizi isteklerini doğrudan 'NASA Yanma Analizi' profiliyle çalıştırır."""
        if not self.yapay_zeka_aktif:
            messagebox.showwarning(
                "Yapay Zeka Kapalı",
                "Yapay Zeka şu anda RAM ve pil tasarrufu için KAPALI durumda!\n\n"
                "NASA Yanma Analizi yapmak için lütfen üst menüdeki '🔴 Yapay Zeka: Kapalı' butonuna tıklayarak aktif edin.",
                parent=self
            )
            return

        komut = ozel_soru.strip() or self.user_input.get("1.0", "end-1c").strip()
        if not komut:
            return

        self.tabview.set("💬 Sohbet")
        self._ust_sekme_degisti()
        self.log_to_chat("Sen (NASA Yanma Analizi)", komut, final=True)

        aktif_motor = self.motor_var.get()
        if aktif_motor == "Yerel (Ollama)":
            secilen_model = self.active_model_var.get()
            self._secili_yerel_model_bellek = secilen_model
            threading.Thread(
                target=self.model_ile_konus,
                args=(secilen_model, "NASA Yanma Analizi", komut, None),
                daemon=True
            ).start()
        else:
            secilen_api_modeli = self.active_api_model_var.get()
            threading.Thread(
                target=self.api_ile_konus,
                args=(secilen_api_modeli, "NASA Yanma Analizi", komut, None),
                daemon=True
            ).start()

    def telemetri_merkezini_ac(self):
        if not TELEMETRI_MERKEZI_AVAILABLE:
            messagebox.showerror("Eksik Modül", "uzay_telemetri_merkezi.py dosyası bulunamadı!", parent=self)
            return
        UzayTelemetriMerkezi(self)

    def siber_hex_merkezini_ac(self):
        if not SIBER_HEX_AVAILABLE:
            messagebox.showerror("Eksik Modül", "siber_hex_analizor.py dosyası bulunamadı!", parent=self)
            return
        SiberHexAnalizor(self)

    def meb_sertifika_yoneticisi_ac(self):
        if not gd_sertifika_kur:
            messagebox.showerror("Eksik Modül", "'Güvenlik Duvarı Tuzaklı.py' içinde sertifika modülü bulunamadı!", parent=self)
            return

        secim = messagebox.askyesnocancel(
            "📜 MEB FATİH Sertifika & Otomatik Kalkan",
            "MEB Sertifika Yöneticisi:\n\n"
            "• EVET: MEB Sertifikasını (MEB_SERTIFIKASI.cer) şimdi otomatik kur ve Arka Plan FATİH Kalkanını başlat.\n"
            "• HAYIR: Sistemdeki MEB Sertifikasını hemen kaldır (Temizle).\n"
            "• İPTAL: İşlemi iptal et.",
            parent=self
        )
        if secim is True:
            def _kur_ve_izle():
                gd_sertifika_kur(log_callback=lambda m: self.log_to_chat("MEB SERTİFİKA", m, final=True))
                if gd_fatih_otomatik_koruma:
                    gd_fatih_otomatik_koruma(log_callback=lambda m: self.log_to_chat("FATİH KALKANI", m, final=True))

            threading.Thread(target=_kur_ve_izle, daemon=True).start()
        elif secim is False:
            if gd_sertifika_kaldir:
                threading.Thread(
                    target=gd_sertifika_kaldir,
                    args=(False, lambda m: self.log_to_chat("MEB SERTİFİKA", m, final=True)),
                    daemon=True
                ).start()

    def resim_ekle(self):
        if not VISION_AVAILABLE:
            messagebox.showwarning("Eksik Kütüphane",
                                   "Görsel analizi için 'Pillow' kütüphanesini yüklemelisiniz (pip install Pillow).",
                                   parent=self)
            return

        dosya = filedialog.askopenfilename(
            parent=self,
            filetypes=[("Resim Dosyaları", "*.png;*.jpg;*.jpeg"), ("Tüm Dosyalar", "*.*")])
        if dosya:
            self.ekli_resim_yolu = dosya
            dosya_adi = os.path.basename(dosya)
            self.lbl_ek_bilgi.configure(text=f"📎 Eklendi: {dosya_adi}")

    def belge_ekle(self):
        dosya = filedialog.askopenfilename(
            parent=self,
            filetypes=[("Desteklenen Belgeler", "*.altar;*.pdf;*.txt;*.docx;*.json;*.md"), ("Tüm Dosyalar", "*.*")])
        if dosya:
            dosya_adi = os.path.basename(dosya)
            self.lbl_ek_bilgi.configure(text=f"📄 İşleniyor: {dosya_adi}")
            threading.Thread(target=self._belgeyi_isle_ve_kaydet, args=(dosya,), daemon=True).start()

    def sesli_yazdir(self):
        if not STT_AVAILABLE:
            messagebox.showwarning("Eksik Kütüphane",
                                   "Ses tanıma için 'SpeechRecognition' ve 'pyaudio' yüklemelisiniz (pip install SpeechRecognition pyaudio).",
                                   parent=self)
            return

        def dinle():
            self._ui_gorevi_ekle(lambda: self.btn_ses.configure(text="Dinliyor...", fg_color="#b85c00"))
            r = sr.Recognizer()
            try:
                with sr.Microphone() as source:
                    audio = r.listen(source, timeout=5, phrase_time_limit=15)
                    metin = r.recognize_google(audio, language="tr-TR")
                    self._ui_gorevi_ekle(lambda m=metin: self.user_input.insert("end", m + " "))
            except Exception as e:
                print(f"Ses anlaşılamadı veya mikrofon açılamadı: {e}")
            finally:
                self._ui_gorevi_ekle(lambda: self.btn_ses.configure(text="🎤 Ses", fg_color="#006400"))

        threading.Thread(target=dinle, daemon=True).start()

    # =====================================================================
    # YENİ %100 GÜVENLİ ARAÇLAR: EKRANI SOR, YEREL TTS & RAM OPTİMİZASYONU
    # =====================================================================
    def ekrandan_bolge_yakala_ve_sor(self):
        """
        Kullanıcının ekrandan fare ile güvenli bir bölge seçmesini (Snipping) sağlar,
        görüntüyü yerel data/ klasörüne kaydedip görsel analiz için sohbet girişine ekler.
        """
        if not VISION_AVAILABLE or ImageGrab is None:
            messagebox.showwarning("Eksik Kütüphane", "Ekran yakalama için 'Pillow' kütüphanesi gereklidir.", parent=self)
            return

        secim_penceresi = tk.Toplevel(self)
        secim_penceresi.attributes("-fullscreen", True)
        secim_penceresi.attributes("-alpha", 0.28)
        secim_penceresi.attributes("-topmost", True)
        secim_penceresi.configure(bg="#000000", cursor="cross")

        tuval = tk.Canvas(secim_penceresi, bg="#000000", highlightthickness=0, cursor="cross")
        tuval.pack(fill="both", expand=True)
        tuval.create_text(
            secim_penceresi.winfo_screenwidth() // 2,
            40,
            text="✂️ Analiz edilecek ekran bölgesini fareyle sürükleyerek seçin (İptal için ESC)",
            fill="#00FFCC",
            font=("Consolas", 15, "bold")
        )

        durum = {"x0": 0, "y0": 0, "rect": None}

        def _basla(event):
            durum["x0"] = event.x_root
            durum["y0"] = event.y_root
            if durum["rect"]:
                tuval.delete(durum["rect"])
            durum["rect"] = tuval.create_rectangle(
                event.x, event.y, event.x, event.y, outline="#00FF88", width=2
            )

        def _surukle(event):
            if durum["rect"]:
                tuval.coords(durum["rect"], durum["x0"], durum["y0"], event.x_root, event.y_root)

        def _bitir(event):
            x1, y1 = min(durum["x0"], event.x_root), min(durum["y0"], event.y_root)
            x2, y2 = max(durum["x0"], event.x_root), max(durum["y0"], event.y_root)
            secim_penceresi.destroy()
            self.update_idletasks()
            if (x2 - x1) < 12 or (y2 - y1) < 12:
                return
            try:
                veri_dizin = os.path.join(_ANA_DIZIN, "data")
                os.makedirs(veri_dizin, exist_ok=True)
                kayit_yolu = os.path.join(veri_dizin, f"ekran_analiz_{datetime.now().strftime('%H%M%S')}.png")
                goruntu = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                goruntu.save(kayit_yolu, "PNG")
                self.ekli_resim_yolu = kayit_yolu
                self.lbl_ek_bilgi.configure(text=f"✂️ Ekran Bölgesi Eklendi: {os.path.basename(kayit_yolu)}")
                self.tabview.set("💬 Sohbet")
                self._ust_sekme_degisti()
                if not self.user_input.get("1.0", "end-1c").strip():
                    self.user_input.insert("1.0", "Bu ekran görüntüsündeki içeriği, kodu veya hatayı detaylıca analiz et.")
            except Exception as e:
                messagebox.showerror("Ekran Yakalama Hatası", f"Ekran görüntüsü alınamadı: {e}", parent=self)

        tuval.bind("<ButtonPress-1>", _basla)
        tuval.bind("<B1-Motion>", _surukle)
        tuval.bind("<ButtonRelease-1>", _bitir)
        secim_penceresi.bind("<Escape>", lambda _: secim_penceresi.destroy())

    def sesli_yanit_durum_degistir(self):
        """Çevrimdışı Windows SAPI tabanlı Türkçe Sesli Yanıt (TTS) özelliğini açar veya kapatır."""
        self.sesli_yanit_aktif = not self.sesli_yanit_aktif
        if self.sesli_yanit_aktif:
            self.btn_sesli_yanit.configure(text="🔊 Sesli: Açık", fg_color="#008080", hover_color="#005959")
            self.lbl_ek_bilgi.configure(text="🔊 Sesli Yanıt Aktif (Cevaplar sesli okunacak)")
        else:
            self._sesli_okumayi_durdur()
            self.btn_sesli_yanit.configure(text="🔇 Sesli: Kapalı", fg_color="#374151", hover_color="#1F2937")
            self.lbl_ek_bilgi.configure(text="🔇 Sesli Yanıt Kapatıldı")

    def _sesli_okumayi_durdur(self):
        proc = self._tts_proc
        self._tts_proc = None
        if proc is not None:
            try:
                proc.terminate()
            except Exception:
                pass

    def metni_sesli_oku(self, metin: str):
        """
        Yanıt metnini yalnızca standart girdi (stdin) üzerinden Windows yerel SAPI motoruna
        ileterek %100 güvenli (komut enjeksiyonuna kapalı) ve çevrimdışı olarak seslendirir.
        """
        if not self.sesli_yanit_aktif or os.name != "nt" or not metin:
            return
        temiz = _RE_ANY_CODE_BLOCK.sub(" kod bloğu ", metin)
        temiz = _RE_THOUGHT_CLEAN.sub("", temiz)
        temiz = re.sub(r"[#*`_~>|=\[\]]+", " ", temiz)
        temiz = re.sub(r"\s+", " ", temiz).strip()[:900]
        if not temiz:
            return

        def _tts_worker():
            self._sesli_okumayi_durdur()
            ps_komut = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$t = [Console]::In.ReadToEnd(); "
                "if ($t) { $s.Speak($t) }"
            )
            try:
                bayrak = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                proc = subprocess.Popen(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_komut],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    creationflags=bayrak
                )
                self._tts_proc = proc
                proc.communicate(input=temiz, timeout=90)
            except Exception:
                pass

        threading.Thread(target=_tts_worker, daemon=True).start()

    def ram_optimize_et(self):
        """
        Hiçbir sistem servisine veya ağa müdahale etmeden yalnızca Altar'ın kendi Python
        çöp toplayıcısını (gc.collect) ve kendi çalışma kümesini (Working Set) temizler.
        """
        def _optimize_worker():
            onceki_mb = 0.0
            try:
                if PSUTIL_AVAILABLE:
                    onceki_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2)
            except Exception:
                pass

            gc.collect()

            if not self.yapay_zeka_aktif and hasattr(self, "yerel_modeli_bellekten_bosalt"):
                try:
                    self.yerel_modeli_bellekten_bosalt()
                except Exception:
                    pass

            if os.name == "nt":
                try:
                    mevcut_proc = ctypes.windll.kernel32.GetCurrentProcess()
                    ctypes.windll.kernel32.SetProcessWorkingSetSize(mevcut_proc, ctypes.c_size_t(-1), ctypes.c_size_t(-1))
                except Exception:
                    pass

            sonraki_mb = onceki_mb
            try:
                if PSUTIL_AVAILABLE:
                    sonraki_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2)
            except Exception:
                pass

            kazanc = max(0.0, onceki_mb - sonraki_mb)
            mesaj = f"🧹 Altar RAM Optimize Edildi: {sonraki_mb:.0f} MB (-{kazanc:.0f} MB kazanıldı)"
            self._ui_gorevi_ekle(lambda: self.lbl_ek_bilgi.configure(text=mesaj))
            self._ui_gorevi_ekle(self.telemetri_guncelle)

        threading.Thread(target=_optimize_worker, daemon=True).start()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    test_ui = AltarArayuzMerkezi()
    test_ui._arayuz_bilesenlerini_kur(["NASA Yanma Analizi", "Genel (Serbest Arama)", "Python", "G-Code / CNC", "Ağ Analizi"])
    test_ui.mainloop()