import os
import time
import math
import shutil
import hashlib
import threading
import subprocess
from collections import deque
from datetime import datetime

try:
    import winreg
except ImportError:
    winreg = None

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

import customtkinter as ctk
from tkinter import filedialog, messagebox

try:
    from altar_gelismis_guvenlik import (
        AITehditAciklayiciModal,
        SurecAgaciModal,
        AutorunSentinelModal,
        USBAsisiModal,
        C2AvcisiModal,
        ButunlukKalkaniFIMModal,
        statik_dosya_analiz_et,
        hosts_butunluk_denetle
    )
    GELISMIS_GUVENLIK_AVAILABLE = True
except ImportError:
    GELISMIS_GUVENLIK_AVAILABLE = False


_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
_ANA_DIZIN = os.path.dirname(os.path.abspath(__file__))
_MEVCUT_PID = os.getpid()

KARANTINA_KLASORU = os.path.join(_ANA_DIZIN, "Altar_Karantina")
TUZAK_KLASORU = os.path.join(_ANA_DIZIN, "Altar_Ransomware_Tuzagi")
os.makedirs(KARANTINA_KLASORU, exist_ok=True)
os.makedirs(TUZAK_KLASORU, exist_ok=True)

# Sistemin, geliştirme ortamının ve yerel yapay zeka (Ollama) sunucusunun
# yanlışlıkla durdurulmasını veya kilitlenmesini önleyen beyaz liste
GUVENLI_SISTEM_SURECLERI = {
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe", "services.exe",
    "lsass.exe", "svchost.exe", "explorer.exe", "taskhostw.exe", "dwm.exe",
    "searchhost.exe", "runtimebroker.exe", "spoolsv.exe", "conhost.exe",
    "fontdrvhost.exe", "sihost.exe", "ctfmon.exe", "audiodg.exe",
    "python.exe", "pythonw.exe", "py.exe", "pyw.exe", "pycharm64.exe", "code.exe",
    "ollama.exe", "ollama_llama_server.exe", "llama-server.exe", "ollama_runner.exe",
    "chrome.exe", "msedge.exe", "firefox.exe", "ffmpeg.exe", "ffprobe.exe"
}

# Zararlı yazılımların sık kullandığı LOLBins ve tehlikeli komut satırı desenleri
TEHLIKELI_CMD_DESENLERI = [
    ("-enc ", "Gizli Base64 Kodlu PowerShell Komutu"),
    ("-encodedcommand", "Gizli Base64 PowerShell İstismarı"),
    ("downloadstring(", "Bellek-İçi (Fileless) Zararlı İndirme"),
    ("invoke-expression", "Dinamik Kod Çalıştırma (IEX)"),
    ("iex(", "Dinamik PowerShell Komut Enjeksiyonu"),
    ("vssadmin delete shadows", "Fidye Yazılımı (Gölge Kopya Silme Girişimi)"),
    ("wbadmin delete catalog", "Fidye Yazılımı (Yedek Kataloğu Silme)"),
    ("bcdedit /set {default} recoveryenabled no", "Windows Kurtarma Modunu Devre Dışı Bırakma"),
    ("certutil -urlcache", "Certutil Üzerinden Zararlı Dosya İndirme (LOLBin)"),
    ("mshta http", "MSHTA Uzaktan Zararlı Betik Çalıştırma"),
    ("regsvr32 /s /n /u /i:http", "Squiblydoo Regsvr32 Zararlı Bypass")
]

# PE Dosyalarında Süreç Enjeksiyonu (Process Hollowing / DLL Injection) API İmzaları
ENJEKSIYON_API_IMZALARI = (
    b"VirtualAllocEx", b"WriteProcessMemory", b"CreateRemoteThread",
    b"NtUnmapViewOfSection", b"SetWindowsHookEx", b"QueueUserAPC",
    b"IsDebuggerPresent", b"CryptEncrypt"
)


# =========================================================================
# SEZGİSEL (HEURISTIC) ANTİVİRÜS VE ENTROPİ TARAMA MOTORU
# =========================================================================
class SezgiselAntivirusTarayici:
    @staticmethod
    def shannon_entropi(veri: bytes) -> float:
        if not veri:
            return 0.0
        uzunluk = len(veri)
        entropi = 0.0
        for b in range(256):
            sayim = veri.count(b)
            if sayim > 0:
                p = sayim / uzunluk
                entropi -= p * math.log2(p)
        return entropi

    @classmethod
    def dosyayi_analiz_et(cls, dosya_yolu: str) -> dict:
        """
        Dosyayı çalıştırmadan (%100 Salt-Okunur) entropi, çift uzantı,
        PE başlığı ve süreç enjeksiyonu API'leri açısından denetler.
        """
        sonuc = {
            "yol": dosya_yolu,
            "ad": os.path.basename(dosya_yolu),
            "risk_puani": 0,
            "durum": "✅ TEMİZ",
            "bulgular": [],
            "sha256": ""
        }
        if not os.path.isfile(dosya_yolu):
            return sonuc

        try:
            boyut = os.path.getsize(dosya_yolu)
            if boyut == 0:
                return sonuc

            with open(dosya_yolu, "rb") as f:
                ornek_veri = f.read(min(boyut, 1024 * 1024))

            sonuc["sha256"] = hashlib.sha256(ornek_veri).hexdigest()
            dosya_adi_kucuk = sonuc["ad"].lower()

            # Altar Kriptografik Kasa (.altar_lock) dosyalarını tanı ve yanlış alarm üretme
            if dosya_adi_kucuk.endswith(".altar_lock") or ornek_veri.startswith(b"ALTAR_VAULT_V2\n"):
                sonuc["durum"] = "✅ TEMİZ (Altar Kasa)"
                sonuc["bulgular"].append("Altar Kriptografik Kasa ile korunmuş dosya")
                return sonuc

            # 1. Çift Uzantı (Masquerading) Kontrolü
            sahte_uzantilar = (
                ".pdf.exe", ".doc.exe", ".docx.exe", ".jpg.exe",
                ".png.exe", ".txt.exe", ".xls.scr", ".pdf.scr"
            )
            if any(dosya_adi_kucuk.endswith(u) for u in sahte_uzantilar):
                sonuc["risk_puani"] += 65
                sonuc["bulgular"].append("Çift Uzantı Tuzak Dosyası (Masquerading)")

            # 2. İkili Çalıştırılabilir (MZ / PE) Analizi
            pe_dosyasi = ornek_veri.startswith(b"MZ")
            uzanti = os.path.splitext(dosya_adi_kucuk)[1]
            if pe_dosyasi and uzanti in (".txt", ".jpg", ".png", ".pdf", ".mp4", ".mp3"):
                sonuc["risk_puani"] += 75
                sonuc["bulgular"].append(f"Gizlenmiş EXE/PE İmzası (Uzantı '{uzanti}' ama içerik çalıştırılabilir kod)")

            # 3. Shannon Entropi (Paketlenmiş / Şifreli Zararlı) Kontrolü
            entropi = cls.shannon_entropi(ornek_veri[:131072])
            if pe_dosyasi and entropi > 7.25:
                sonuc["risk_puani"] += 35
                sonuc["bulgular"].append(f"Yüksek Entropi ({entropi:.2f}/8.00 - UPX/VMProtect Paketli veya Şifreli)")

            # 4. Tehlikeli Process Injection API Kombinasyonu
            if pe_dosyasi:
                bulunan_apiler = [api.decode() for api in ENJEKSIYON_API_IMZALARI if api in ornek_veri]
                if "VirtualAllocEx" in bulunan_apiler and "WriteProcessMemory" in bulunan_apiler:
                    sonuc["risk_puani"] += 55
                    sonuc["bulgular"].append("Süreç Enjeksiyonu (Process Injection) API Kombinasyonu")
                elif len(bulunan_apiler) >= 3:
                    sonuc["risk_puani"] += 30
                    sonuc["bulgular"].append(f"Şüpheli Sistem API'leri: {', '.join(bulunan_apiler[:4])}")

            # 5. Betik (.bat, .vbs, .ps1) İçerik Kontrolü
            if uzanti in (".bat", ".cmd", ".ps1", ".vbs", ".js"):
                metin_kucuk = ornek_veri[:32768].decode("utf-8", errors="ignore").lower()
                for desen, aciklama in TEHLIKELI_CMD_DESENLERI:
                    if desen in metin_kucuk:
                        sonuc["risk_puani"] += 60
                        sonuc["bulgular"].append(f"Zararlı Betik Komutu ({aciklama})")

            if sonuc["risk_puani"] >= 60:
                sonuc["durum"] = "🚨 ZARARLI / YÜKSEK RİSK"
            elif sonuc["risk_puani"] >= 30:
                sonuc["durum"] = "⚠️ ŞÜPHELİ"
            else:
                sonuc["durum"] = "✅ TEMİZ"

        except Exception:
            pass
        return sonuc


# =========================================================================
# ANA EDR VE NGFW ÇEKİRDEK MOTORU
# =========================================================================
class AltarEDRDefenseEngine:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.edr_aktif = False
        self.oto_dondur_aktif = True
        self.indirilenler_kalkani_aktif = True

        self.kilit = threading.Lock()
        self.bilinen_pidler = set()
        self.bilinen_baglantilar = set()
        self.tuzak_dosyalar = {}
        self.baslangic_snapshot = {}
        self.hosts_hash = ""
        self.indirilenler_bilinen = set()

        self.istatistikler = {
            "TARANAN_SUREC": 0,
            "URT_BAGLANTI": 0,
            "ENGEL_TEHDIT": 0,
            "KARANTINA": 0
        }

        threading.Thread(target=self._arka_plan_ilk_hazirlik, daemon=True).start()

    def _arka_plan_ilk_hazirlik(self):
        try:
            self._tuzak_dosyalari_hazirla()
            self._persistence_snapshot_al()
            self._indirilenler_snapshot_al()
        except Exception:
            pass

    def _log(self, mesaj: str, kategori: str = "INFO"):
        zaman = datetime.now().strftime("%H:%M:%S")
        satir = f"[{zaman}] {mesaj}"
        if self.log_callback:
            try:
                self.log_callback(satir, kategori)
            except Exception:
                pass

    # ---------------------------------------------------------------------
    # 1. FİDYE YAZILIMI TUZAK DOSYA (CANARY TRAP) SİSTEMİ
    # ---------------------------------------------------------------------
    def _tuzak_dosyalari_hazirla(self):
        tuzak_isimleri = [
            "00_ALTAR_CANARY_DOKUNMA_FINANS.xlsx",
            "00_ALTAR_CANARY_DOKUNMA_SIFRELER.docx",
            "00_ALTAR_CANARY_YEDEK_ANAHTAR.txt"
        ]
        icerik = (
            b"ALTAR EDR RANSOMWARE CANARY TRAP FILE - DO NOT MODIFY\n"
            b"Bu dosya fidye yazilimlarini (Ransomware) yakalamak icin olusturulmus bir tuzaktir.\n"
        )
        with self.kilit:
            self.tuzak_dosyalar.clear()
            for isim in tuzak_isimleri:
                tam_yol = os.path.join(TUZAK_KLASORU, isim)
                try:
                    if not os.path.exists(tam_yol):
                        with open(tam_yol, "wb") as f:
                            f.write(icerik)
                    with open(tam_yol, "rb") as f:
                        ozet = hashlib.sha256(f.read()).hexdigest()
                    self.tuzak_dosyalar[tam_yol] = ozet
                except Exception:
                    pass

    def tuzak_dosyalari_denetle(self):
        for yol, orijinal_hash in list(self.tuzak_dosyalar.items()):
            try:
                if not os.path.exists(yol):
                    self.istatistikler["ENGEL_TEHDIT"] += 1
                    self._log(f"🚨 [FİDYE YAZILIMI ALARMI] Tuzak dosya silindi: {os.path.basename(yol)}!", "THREAT")
                    self._tuzak_dosyalari_hazirla()
                    continue

                with open(yol, "rb") as f:
                    guncel_hash = hashlib.sha256(f.read()).hexdigest()

                if guncel_hash != orijinal_hash:
                    self.istatistikler["ENGEL_TEHDIT"] += 1
                    self._log(
                        f"🚨 [KRİTİK RANSOMWARE TESPİTİ] '{os.path.basename(yol)}' tuzak dosyası değiştirildi/şifrelendi!",
                        "THREAT"
                    )
                    self._tuzak_dosyalari_hazirla()
            except Exception:
                pass

    # ---------------------------------------------------------------------
    # 2. KAYIT DEFTERİ (AUTORUNS) VE HOSTS BEKÇİSİ
    # ---------------------------------------------------------------------
    @staticmethod
    def autorun_kayitlarini_oku() -> dict:
        kayitlar = {}
        if os.name != "nt" or winreg is None:
            return kayitlar

        hedefler = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU\\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM\\Run")
        ]
        for kok, yol, etiket in hedefler:
            try:
                anahtar = winreg.OpenKey(kok, yol, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        ad, deger, _ = winreg.EnumValue(anahtar, i)
                        kayitlar[f"[{etiket}] {ad}"] = str(deger)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(anahtar)
            except Exception:
                pass
        return kayitlar

    def _persistence_snapshot_al(self):
        self.baslangic_snapshot = self.autorun_kayitlarini_oku()
        hosts_yolu = r"C:\Windows\System32\drivers\etc\hosts"
        if os.path.exists(hosts_yolu):
            try:
                with open(hosts_yolu, "rb") as f:
                    self.hosts_hash = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                pass

    def kalicilik_ve_hosts_denetle(self):
        guncel = self.autorun_kayitlarini_oku()
        for anahtar, deger in guncel.items():
            if anahtar not in self.baslangic_snapshot:
                self.istatistikler["ENGEL_TEHDIT"] += 1
                self._log(f"⚠️ [AUTORUN / REGISTRY UYARISI] Başlangıca yeni program eklendi: {anahtar} -> {deger}", "THREAT")
            elif self.baslangic_snapshot[anahtar] != deger:
                self.istatistikler["ENGEL_TEHDIT"] += 1
                self._log(f"⚠️ [REGISTRY DEĞİŞİKLİĞİ] Başlangıç kaydı değiştirildi: {anahtar} -> {deger}", "THREAT")
        self.baslangic_snapshot = guncel

        hosts_yolu = r"C:\Windows\System32\drivers\etc\hosts"
        if self.hosts_hash and os.path.exists(hosts_yolu):
            try:
                with open(hosts_yolu, "rb") as f:
                    yeni_h = hashlib.sha256(f.read()).hexdigest()
                if yeni_h != self.hosts_hash:
                    self.hosts_hash = yeni_h
                    self.istatistikler["ENGEL_TEHDIT"] += 1
                    self._log("🚨 [HOSTS DOSYASI DEĞİŞTİRİLDİ] Sistem DNS yönlendirme tablosuna müdahale edildi!", "THREAT")
            except Exception:
                pass

    # ---------------------------------------------------------------------
    # 3. İNDİRİLENLER (DOWNLOADS) CANLI KALKANI
    # ---------------------------------------------------------------------
    def _indirilenler_snapshot_al(self):
        dl_yolu = os.path.expanduser("~\\Downloads")
        if os.path.isdir(dl_yolu):
            try:
                self.indirilenler_bilinen = set(os.listdir(dl_yolu))
            except Exception:
                pass

    def indirilenler_klasorunu_denetle(self):
        if not self.indirilenler_kalkani_aktif:
            return
        dl_yolu = os.path.expanduser("~\\Downloads")
        if not os.path.isdir(dl_yolu):
            return
        try:
            mevcut = set(os.listdir(dl_yolu))
            yeni_dosyalar = mevcut - self.indirilenler_bilinen
            self.indirilenler_bilinen = mevcut

            for dosya_adi in yeni_dosyalar:
                if dosya_adi.endswith((".crdownload", ".part", ".tmp")):
                    continue
                tam_yol = os.path.join(dl_yolu, dosya_adi)
                if os.path.isfile(tam_yol):
                    analiz = SezgiselAntivirusTarayici.dosyayi_analiz_et(tam_yol)
                    if analiz["risk_puani"] >= 50:
                        self.istatistikler["ENGEL_TEHDIT"] += 1
                        self._log(
                            f"🚨 [İNDİRİLENLER KALKANI] Tehlikeli dosya yakalandı: {dosya_adi} (Risk: {analiz['risk_puani']})",
                            "THREAT"
                        )
                    else:
                        self._log(f"📥 [İNDİRİLENLER KALKANI] Yeni dosya tarandı ve temiz: {dosya_adi}", "INFO")
        except Exception:
            pass

    # ---------------------------------------------------------------------
    # 4. DAVRANIŞSAL SÜREÇ (LOLBins) VE SIFIR-GÜVEN UYGULAMA DUVARI
    # ---------------------------------------------------------------------
    def surec_ve_ag_davranisi_denetle(self):
        if not PSUTIL_AVAILABLE:
            return

        if len(self.bilinen_pidler) > 6000:
            self.bilinen_pidler.clear()

        # A) Yeni Başlatılan Süreçlerin Komut Satırı ve Ebeveyn Analizi
        for proc in psutil.process_iter(['pid', 'ppid', 'name']):
            try:
                info = proc.info
                pid = info['pid']
                if pid in self.bilinen_pidler or pid in (0, 4, _MEVCUT_PID):
                    continue
                self.bilinen_pidler.add(pid)
                self.istatistikler["TARANAN_SUREC"] += 1

                isim = (info['name'] or "").lower()
                # Güvenli sistem veya Ollama yapay zeka süreçlerine OpenProcess/cmdline çağrısı yapma (Sıfır Çakışma)
                if isim in GUVENLI_SISTEM_SURECLERI:
                    continue

                try:
                    komut = " ".join(proc.cmdline() or []).lower()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    komut = ""

                if komut:
                    for desen, aciklama in TEHLIKELI_CMD_DESENLERI:
                        if desen in komut:
                            self.istatistikler["ENGEL_TEHDIT"] += 1
                            self._log(f"🚨 [EDR DAVRANIŞ TESPİTİ] {aciklama} | Süreç: {isim} (PID: {pid})", "THREAT")
                            if self.oto_dondur_aktif:
                                try:
                                    proc.suspend()
                                    self._log(f"⏸️ [OTOMATİK MÜDAHALE] Zararlı süreç donduruldu (PID: {pid})", "ACTION")
                                except Exception:
                                    pass

                # Şüpheli Ebeveyn-Çocuk (Office -> CMD/PowerShell) Kontrolü
                if isim in ("cmd.exe", "powershell.exe", "pwsh.exe", "wscript.exe", "cscript.exe", "mshta.exe"):
                    ppid = info.get('ppid') or 0
                    if ppid > 0 and ppid != _MEVCUT_PID:
                        try:
                            ebeveyn_ad = psutil.Process(ppid).name().lower()
                            if ebeveyn_ad in ("winword.exe", "excel.exe", "powerpnt.exe", "acrord32.exe"):
                                self.istatistikler["ENGEL_TEHDIT"] += 1
                                self._log(
                                    f"🚨 [MAKRO / EXPLOIT ALARMI] '{ebeveyn_ad}' belgesi arka planda '{isim}' (PID: {pid}) başlattı!",
                                    "THREAT"
                                )
                        except Exception:
                            pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # B) Uygulama Bazlı Sıfır-Güven (Zero-Trust) Dış Ağ Denetimi (Ollama 11434 Muafiyetli)
        try:
            if len(self.bilinen_baglantilar) > 4000:
                self.bilinen_baglantilar.clear()

            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED' and conn.raddr and conn.pid:
                    if conn.pid in (0, 4, _MEVCUT_PID):
                        continue
                    uzak_ip = conn.raddr.ip
                    uzak_port = conn.raddr.port
                    yerel_port = conn.laddr.port if conn.laddr else 0

                    # Ollama yerel yapay zeka portunu (11434) ve yerel ağ/loopback trafiğini denetim dışı bırak
                    if uzak_port == 11434 or yerel_port == 11434 or uzak_ip.startswith(("127.", "192.168.", "10.", "::1")):
                        continue

                    baglanti_imza = (conn.pid, uzak_ip, uzak_port)
                    if baglanti_imza in self.bilinen_baglantilar:
                        continue
                    self.bilinen_baglantilar.add(baglanti_imza)
                    self.istatistikler["URT_BAGLANTI"] += 1

                    try:
                        p = psutil.Process(conn.pid)
                        p_adi = p.name()
                        if p_adi.lower() in GUVENLI_SISTEM_SURECLERI:
                            continue
                        exe_yolu = p.exe()
                    except Exception:
                        continue

                    kucuk_yol = exe_yolu.lower()
                    if any(k in kucuk_yol for k in ("\\appdata\\local\\temp\\", "\\downloads\\", "\\users\\public\\")):
                        self.istatistikler["ENGEL_TEHDIT"] += 1
                        self._log(
                            f"🚨 [ZERO-TRUST AĞ UYARISI] Geçici klasördeki '{p_adi}' (PID:{conn.pid}) dış IP'ye bağlanıyor: {uzak_ip}:{uzak_port}",
                            "THREAT"
                        )
        except Exception:
            pass

    def karantinaya_al(self, dosya_yolu: str) -> tuple:
        """Şüpheli dosyayı silmeden güvenli karantina klasörüne taşır ve çalışmasını engeller."""
        if not os.path.isfile(dosya_yolu):
            return False, "Dosya bulunamadı."
        gercek_yol = os.path.normcase(os.path.realpath(os.path.abspath(dosya_yolu)))
        ana_dizin_norm = os.path.normcase(os.path.realpath(_ANA_DIZIN))
        karantina_norm = os.path.normcase(os.path.realpath(KARANTINA_KLASORU))
        if os.path.dirname(gercek_yol) == ana_dizin_norm:
            return False, "Altar çekirdek modül dosyaları karantinaya alınamaz."
        if gercek_yol.startswith(karantina_norm):
            return False, "Dosya zaten karantina klasöründe bulunuyor."
        try:
            zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
            yeni_ad = f"KARANTINA_{zaman}_{os.path.basename(dosya_yolu)}.quarantine"
            hedef = os.path.join(KARANTINA_KLASORU, yeni_ad)
            shutil.move(dosya_yolu, hedef)
            self.istatistikler["KARANTINA"] += 1
            self._log(f"☣️ [KARANTİNAYA ALINDI] '{os.path.basename(dosya_yolu)}' izole edildi -> {yeni_ad}", "ACTION")
            return True, hedef
        except Exception as e:
            return False, str(e)

    def uygulama_ag_engelle(self, exe_yolu: str) -> tuple:
        """Belirtilen .exe dosyasının internete çıkışını Windows Güvenlik Duvarı'nda engeller."""
        if not os.path.isfile(exe_yolu):
            return False, "Uygulama (.exe) dosyası bulunamadı."
        try:
            temiz_exe = os.path.abspath(exe_yolu)
            kural_adi = f"ALTAR_APP_BLOCK_{os.path.basename(temiz_exe)}"
            komut = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={kural_adi}", "dir=out", "action=block",
                f"program={temiz_exe}", "enable=yes"
            ]
            sonuc = subprocess.run(komut, shell=False, capture_output=True, text=True, creationflags=_NO_WINDOW)
            if sonuc.returncode == 0:
                self.istatistikler["ENGEL_TEHDIT"] += 1
                self._log(f"⛔ [UYGULAMA DUVARI] '{os.path.basename(exe_yolu)}' internete çıkışı engellendi.", "ACTION")
                return True, kural_adi
            return False, sonuc.stderr or sonuc.stdout
        except Exception as e:
            return False, str(e)


# =========================================================================
# ALTAR ARAYÜZ SEKMESİ: 🦠 ANTİVİRÜS & EDR KOMUTA MERKEZİ
# =========================================================================
class AltarEDRAntivirusSekmesi(ctk.CTkFrame):
    """
    Üst sekme çubuğuna yerleşen ve VARSAYILAN OLARAK AKTİF başlayan
    5 katmanlı Yeni Nesil Antivirüs, EDR Davranış Kalkanı, Ransomware Tuzak Koruyucu.
    """
    def __init__(self, parent, ai_analiz_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.ai_analiz_callback = ai_analiz_callback
        self._log_tamponu = deque(maxlen=250)
        self._rapor_kuyrugu = deque(maxlen=10)
        self.motor = AltarEDRDefenseEngine(log_callback=self._log_geldi)

        self.lbl_durum = None
        self.lbl_sayac = None
        self.btn_edr_baslat = None
        self.oto_dondur_var = ctk.BooleanVar(value=True)
        self.txt_edr_log = None
        self.txt_tarama_rapor = None
        self.entry_karantina_hedef = None

        self._arayuz_kur()
        self.after(250, self._ui_zamanlayici_dongusu)
        # VARSAYILAN OLARAK OTOMATİK BAŞLAT
        self.after(350, self._varsayilan_olarak_baslat)

    def _varsayilan_olarak_baslat(self):
        if self.winfo_exists() and not self.motor.edr_aktif:
            self.edr_baslat_durdur()

    def _arayuz_kur(self):
        # 1. ÜST DURUM VE TELEMETRİ ÇUBUĞU
        ust_bar = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust_bar.pack(side="top", fill="x", padx=6, pady=(4, 6))

        self.lbl_durum = ctk.CTkLabel(
            ust_bar,
            text="🦠 ALTAR NEXT-GEN ANTİVİRÜS, EDR DAVRANIŞ KALKANI & FİDYE YAZILIMI KORUYUCU | Durum: Başlatılıyor...",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#00FFCC"
        )
        self.lbl_durum.pack(side="left", padx=12, pady=6)

        self.lbl_sayac = ctk.CTkLabel(
            ust_bar,
            text="İncelenen Süreç: 0 | Ağ Soketi: 0 | Tehdit/Alarm: 0 | Karantina: 0",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#FFD700"
        )
        self.lbl_sayac.pack(side="right", padx=12, pady=6)

        # 2. HIZLI KALKAN KONTROL ÇUBUĞU
        kontrol = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=8)
        kontrol.pack(side="top", fill="x", padx=6, pady=(0, 6))

        self.btn_edr_baslat = ctk.CTkButton(
            kontrol, text="▶️ Gerçek Zamanlı EDR & Fidye Kalkanını Başlat", width=275, height=28,
            fg_color="#00A86B", hover_color="#007F50", font=ctk.CTkFont(size=12, weight="bold"),
            command=self.edr_baslat_durdur
        )
        self.btn_edr_baslat.pack(side="left", padx=8, pady=6)

        ctk.CTkCheckBox(
            kontrol, text="Saldırgan Süreci Otomatik Dondur (Suspend)",
            variable=self.oto_dondur_var, text_color="#FF6B6B", font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: setattr(self.motor, "oto_dondur_aktif", self.oto_dondur_var.get())
        ).pack(side="left", padx=8, pady=6)

        ctk.CTkButton(
            kontrol, text="🔍 Dosya Tara", width=105, height=26,
            fg_color="#1f538d", command=self.tek_dosya_sec_tara
        ).pack(side="left", padx=4, pady=6)

        ctk.CTkButton(
            kontrol, text="📁 Klasör Tara", width=105, height=26,
            fg_color="#4B0082", command=self.klasor_sec_tara
        ).pack(side="left", padx=4, pady=6)

        ctk.CTkButton(
            kontrol, text="🔑 Başlangıç (Autoruns) Denetle", width=185, height=26,
            fg_color="#B85C00", command=self.autoruns_raporu_goster
        ).pack(side="left", padx=4, pady=6)

        ctk.CTkButton(
            kontrol, text="🧠 AI Tehdit Analizi", width=135, height=26,
            fg_color="#008080", command=self.raporu_ai_gonder
        ).pack(side="right", padx=8, pady=6)

        # 2.5 İLERİ DÜZEY GÜVENLİK VE ANTİVİRÜS CEPHANELİĞİ ARAÇ ÇUBUĞU
        araclar_bar = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#1E293B")
        araclar_bar.pack(side="top", fill="x", padx=6, pady=(0, 6))

        ctk.CTkLabel(
            araclar_bar, text="🛡️ CEPHANELİK:",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#00FFCC"
        ).pack(side="left", padx=(8, 4), pady=5)

        ctk.CTkButton(
            araclar_bar, text="🧠 AI Tehdit Açıklayıcı", width=145, height=26,
            fg_color="#3B82F6", hover_color="#2563EB", font=ctk.CTkFont(size=11, weight="bold"),
            command=self._ac_ai_tehdit_aciklayici
        ).pack(side="left", padx=3, pady=5)

        ctk.CTkButton(
            araclar_bar, text="🌲 Süreç Ağacı Radarı", width=140, height=26,
            fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=11, weight="bold"),
            command=self._ac_surec_agaci
        ).pack(side="left", padx=3, pady=5)

        ctk.CTkButton(
            araclar_bar, text="🔑 Autoruns Kalkanı", width=135, height=26,
            fg_color="#F59E0B", hover_color="#D97706", text_color="#000000", font=ctk.CTkFont(size=11, weight="bold"),
            command=self._ac_autorun_sentinel
        ).pack(side="left", padx=3, pady=5)

        ctk.CTkButton(
            araclar_bar, text="🔌 USB Flaş Koruyucu", width=140, height=26,
            fg_color="#06B6D4", hover_color="#0891B2", font=ctk.CTkFont(size=11, weight="bold"),
            command=self._ac_usb_asisi
        ).pack(side="left", padx=3, pady=5)

        ctk.CTkButton(
            araclar_bar, text="🌐 C2 Sızıntı Avcısı", width=135, height=26,
            fg_color="#EF4444", hover_color="#DC2626", font=ctk.CTkFont(size=11, weight="bold"),
            command=self._ac_c2_avcisi
        ).pack(side="left", padx=3, pady=5)

        ctk.CTkButton(
            araclar_bar, text="🔒 Bütünlük (Hosts FIM)", width=155, height=26,
            fg_color="#8B5CF6", hover_color="#7C3AED", font=ctk.CTkFont(size=11, weight="bold"),
            command=self._ac_butunluk_fim
        ).pack(side="left", padx=3, pady=5)

        # 3. ANA BÖLÜNMÜŞ GÖVDE (SOL: CANLI EDR MONITOR | SAĞ: SEZGİSEL TARAYICI & KARANTİNA)
        govde = ctk.CTkFrame(self, fg_color="transparent")
        govde.pack(side="top", fill="both", expand=True, padx=6, pady=(0, 6))
        govde.grid_columnconfigure(0, weight=11)
        govde.grid_columnconfigure(1, weight=9)
        govde.grid_rowconfigure(0, weight=1)

        # SOL PANEL: CANLI EDR, LOLBins, RANSOMWARE TUZAK VE ZERO-TRUST AĞ MONITORÜ
        sol = ctk.CTkFrame(govde, fg_color="#070B14", corner_radius=8, border_width=1, border_color="#1E293B")
        sol.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        ctk.CTkLabel(
            sol, text="👁️ CANLI EDR SÜREÇ DAVRANIŞI, LOLBins, FİDYE TUZAĞI & ZERO-TRUST AĞ GÜNLÜĞÜ",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#00FF88"
        ).pack(anchor="w", padx=10, pady=6)

        self.txt_edr_log = ctk.CTkTextbox(
            sol, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#E2E8F0", wrap="word"
        )
        self.txt_edr_log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.txt_edr_log.tag_config("THREAT", foreground="#FF4444")
        self.txt_edr_log.tag_config("ACTION", foreground="#FFD700")
        self.txt_edr_log.tag_config("INFO", foreground="#00FF88")

        self.txt_edr_log.insert(
            "1.0",
            "[*] Altar 5-Katmanlı EDR & Antivirüs Kalkanı Varsayılan Olarak Aktif:\n"
            "  1) Davranışsal LOLBins & Bellek-İçi (Fileless PowerShell/CMD) Komut Avcısı\n"
            "  2) Fidye Yazılımı (Ransomware) Kriptografik Tuzak Dosya (Canary) Bekçisi\n"
            "  3) Uygulama Katmanı Sıfır-Güven (Zero-Trust) Dış Ağ & İndirilenler Denetçisi\n"
            "  4) Windows Kayıt Defteri (Autoruns) ve Hosts Dosyası Koruyucusu\n"
            "  5) Sezgisel (Heuristic) PE Entropi, Çift Uzantı ve Enjeksiyon API Tarayıcısı\n"
            "--------------------------------------------------------------------------\n"
        )

        # SAĞ PANEL: SEZGİSEL TARAMA SONUÇLARI VE KARANTİNA YÖNETİMİ
        sag = ctk.CTkFrame(govde, fg_color="#070B14", corner_radius=8, border_width=1, border_color="#1E293B")
        sag.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        sag_ust = ctk.CTkFrame(sag, fg_color="#161B22", corner_radius=6)
        sag_ust.pack(fill="x", padx=8, pady=6)

        ctk.CTkLabel(
            sag_ust, text="🧪 SEZGİSEL (HEURISTIC) TARAMA & KARANTİNA MERKEZİ",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#00E5FF"
        ).pack(side="left", padx=8, pady=4)

        ctk.CTkButton(
            sag_ust, text="☣️ Karantina Klasörü", width=130, height=24,
            fg_color="#8B0000", command=lambda: os.startfile(KARANTINA_KLASORU) if os.name == 'nt' else None
        ).pack(side="right", padx=6, pady=4)

        self.txt_tarama_rapor = ctk.CTkTextbox(
            sag, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#A6E3A1", wrap="word"
        )
        self.txt_tarama_rapor.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self.txt_tarama_rapor.insert(
            "1.0",
            "🔍 Üstteki 'Dosya Tara' veya 'Klasör Tara' butonunu kullanarak şüpheli dosyaları çalıştırmadan:\n"
            "• Shannon Entropi (Paketlenmiş/Şifreli Trojan),\n"
            "• Process Injection API'leri (VirtualAllocEx / WriteProcessMemory),\n"
            "• Sahte Çift Uzantı (.pdf.exe) ve Gizli PE Başlığı\n"
            "kontrollerinden geçirebilirsiniz.\n"
        )

        alt_karantina_bar = ctk.CTkFrame(sag, fg_color="#161B22", corner_radius=6)
        alt_karantina_bar.pack(fill="x", padx=8, pady=(0, 8))

        self.entry_karantina_hedef = ctk.CTkEntry(
            alt_karantina_bar, placeholder_text="Karantinaya alınacak veya ağdan engellenecek dosya yolu...",
            font=ctk.CTkFont(family="Consolas", size=11), height=26
        )
        self.entry_karantina_hedef.pack(side="left", fill="x", expand=True, padx=6, pady=5)

        ctk.CTkButton(
            alt_karantina_bar, text="⛔ Ağdan Engelle", width=110, height=26,
            fg_color="#B85C00", hover_color="#8F4700", command=self.secili_uygulamayi_agdan_engelle
        ).pack(side="right", padx=(2, 6), pady=5)

        ctk.CTkButton(
            alt_karantina_bar, text="☣️ Karantina", width=105, height=26,
            fg_color="#C62828", hover_color="#8E0000", command=self.secili_dosyayi_karantinaya_al
        ).pack(side="right", padx=2, pady=5)

    # =========================================================================
    # MERKEZİ THREAD-SAFE ZAMANLAYICI VE TARAMA METOTLARI
    # =========================================================================
    def _log_geldi(self, satir: str, kategori: str):
        self._log_tamponu.append((satir, kategori))

    def _ui_zamanlayici_dongusu(self):
        if not self.winfo_exists():
            return

        if self._log_tamponu:
            sayac = 0
            while self._log_tamponu and sayac < 35:
                satir, kat = self._log_tamponu.popleft()
                sayac += 1
                tag = kat if kat in ("THREAT", "ACTION", "INFO") else "INFO"
                self.txt_edr_log.insert("end", satir + "\n", tag)

            satir_sayisi = int(self.txt_edr_log.index("end-1c").split(".")[0])
            if satir_sayisi > 350:
                self.txt_edr_log.delete("1.0", f"{satir_sayisi - 250}.0")
            self.txt_edr_log.see("end")

        if self._rapor_kuyrugu:
            while self._rapor_kuyrugu:
                yeni_rapor = self._rapor_kuyrugu.popleft()
                self.txt_tarama_rapor.delete("1.0", "end")
                self.txt_tarama_rapor.insert("1.0", yeni_rapor)

        st = self.motor.istatistikler
        self.lbl_sayac.configure(
            text=(
                f"İncelenen Süreç: {st['TARANAN_SUREC']} | "
                f"Ağ Soketi: {st['URT_BAGLANTI']} | "
                f"Tehdit/Alarm: {st['ENGEL_TEHDIT']} | "
                f"Karantina: {st['KARANTINA']}"
            )
        )
        self.after(250, self._ui_zamanlayici_dongusu)

    def edr_baslat_durdur(self):
        self.motor.edr_aktif = not self.motor.edr_aktif
        if self.motor.edr_aktif:
            self.btn_edr_baslat.configure(
                text="⏹️ Gerçek Zamanlı EDR Kalkanını Durdur", fg_color="#C62828", hover_color="#8E0000"
            )
            self.lbl_durum.configure(
                text="🛡️ ALTAR EDR, İNDİRİLENLER & RANSOMWARE KALKANI AKTİF (Varsayılan Canlı İzleme)", text_color="#00FF88"
            )
            self._log_geldi("[+] Gerçek Zamanlı EDR, Fidye Tuzağı (Canary) ve Zero-Trust Ağ Kalkanı otomatik devreye alındı.", "INFO")
            threading.Thread(target=self._edr_arka_plan_dongusu, daemon=True).start()
        else:
            self.btn_edr_baslat.configure(
                text="▶️ Gerçek Zamanlı EDR & Fidye Kalkanını Başlat", fg_color="#00A86B", hover_color="#007F50"
            )
            self.lbl_durum.configure(
                text="🦠 ALTAR NEXT-GEN ANTİVİRÜS & EDR | Durum: Beklemede", text_color="#FFD700"
            )
            self._log_geldi("[*] Gerçek Zamanlı EDR Kalkanı durduruldu.", "ACTION")

    def _edr_arka_plan_dongusu(self):
        sayac = 0
        while self.motor.edr_aktif:
            try:
                self.motor.tuzak_dosyalari_denetle()
                self.motor.surec_ve_ag_davranisi_denetle()
                self.motor.indirilenler_klasorunu_denetle()
                sayac += 1
                if sayac % 4 == 0:
                    self.motor.kalicilik_ve_hosts_denetle()
            except Exception:
                pass
            time.sleep(1.5)

    def tek_dosya_sec_tara(self):
        yol = filedialog.askopenfilename(title="Sezgisel Antivirüs İle Taranacak Dosyayı Seçin")
        if not yol:
            return
        self.entry_karantina_hedef.delete(0, "end")
        self.entry_karantina_hedef.insert(0, yol)

        def _tara():
            r = SezgiselAntivirusTarayici.dosyayi_analiz_et(yol)
            bulgu_str = "\n  • ".join(r["bulgular"]) if r["bulgular"] else "Zararlı imza veya sezgisel anomali bulunmadı."
            metin = (
                f"=== 🧪 SEZGİSEL (HEURISTIC) DOSYA ANALİZ RAPORU ===\n"
                f"Dosya Adı  : {r['ad']}\n"
                f"Tam Konum  : {r['yol']}\n"
                f"SHA-256    : {r['sha256']}\n"
                f"Risk Puanı : {r['risk_puani']} / 100\n"
                f"Sonuç      : {r['durum']}\n"
                f"{'-'*52}\n"
                f"Tespitler:\n  • {bulgu_str}\n"
            )
            self._rapor_kuyrugu.append(metin)

        threading.Thread(target=_tara, daemon=True).start()

    def klasor_sec_tara(self):
        dizin = filedialog.askdirectory(title="Taranacak Klasörü Seçin")
        if not dizin:
            return

        self.txt_tarama_rapor.delete("1.0", "end")
        self.txt_tarama_rapor.insert("1.0", f"⏳ '{dizin}' klasörü Sezgisel Antivirüs ile taranıyor...\n")

        def _klasor_worker():
            toplam = 0
            supheliler = []
            for r, dirs, files in os.walk(dizin):
                dirs[:] = [d for d in dirs if d not in (".git", ".venv", "venv", "__pycache__", "node_modules")]
                for f in files:
                    tam = os.path.join(r, f)
                    toplam += 1
                    analiz = SezgiselAntivirusTarayici.dosyayi_analiz_et(tam)
                    if analiz["risk_puani"] >= 30:
                        supheliler.append(analiz)
                    if toplam >= 250:
                        break
                if toplam >= 250:
                    break

            rapor = [
                "=== 📁 KLASÖR SEZGİSEL ANTİVİRÜS TARAMA ÖZETİ ===",
                f"Taranan Dizin : {dizin}",
                f"Taranan Dosya : {toplam} Adet | Şüpheli/Zararlı: {len(supheliler)} Adet",
                "-" * 54
            ]
            if supheliler:
                for s in supheliler:
                    rapor.append(f"{s['durum']} (Risk: {s['risk_puani']}) -> {s['ad']}")
                    rapor.append(f"   Neden: {', '.join(s['bulgular'])}")
                    rapor.append(f"   Yol  : {s['yol']}\n")
            else:
                rapor.append("✅ Taranan dosyaların hiçbirinde zararlı imza, çift uzantı veya yüksek entropili trojan saptanmadı.")

            self._rapor_kuyrugu.append("\n".join(rapor))

        threading.Thread(target=_klasor_worker, daemon=True).start()

    def autoruns_raporu_goster(self):
        kayitlar = self.motor.autorun_kayitlarini_oku()
        satirlar = ["=== 🔑 WINDOWS BAŞLANGIÇ (AUTORUNS / REGISTRY) PROGRAMLARI ===\n"]
        for k, v in kayitlar.items():
            satirlar.append(f"• {k}\n    Komut: {v}\n")
        self.txt_tarama_rapor.delete("1.0", "end")
        self.txt_tarama_rapor.insert("1.0", "\n".join(satirlar))

    def secili_dosyayi_karantinaya_al(self):
        hedef = self.entry_karantina_hedef.get().strip().strip('"')
        if not hedef:
            messagebox.showwarning("Hedef Yok", "Lütfen karantinaya alınacak dosyanın yolunu seçin veya yapıştırın.", parent=self)
            return
        ok, msg = self.motor.karantinaya_al(hedef)
        if ok:
            messagebox.showinfo("Karantina Başarılı", f"Dosya güvenli karantina kasasına izole edildi:\n{msg}", parent=self)
        else:
            messagebox.showerror("Hata", f"Karantina işlemi başarısız:\n{msg}", parent=self)

    def secili_uygulamayi_agdan_engelle(self):
        hedef = self.entry_karantina_hedef.get().strip().strip('"')
        if not hedef:
            messagebox.showwarning("Hedef Yok", "Lütfen ağ erişimi engellenecek uygulamanın (.exe) yolunu seçin.", parent=self)
            return
        ok, msg = self.motor.uygulama_ag_engelle(hedef)
        if ok:
            messagebox.showinfo("Uygulama Duvarı", f"Uygulamanın dış ağ erişimi Windows Güvenlik Duvarı'nda engellendi:\nKural: {msg}", parent=self)
        else:
            messagebox.showerror("Hata", f"Engelleme başarısız (Yönetici izni gerekebilir):\n{msg}", parent=self)


    # =========================================================================
    # 6 İLERİ DÜZEY GÜVENLİK VE ANTİVİRÜS ARACI TETİKLEYİCİLERİ
    # =========================================================================
    def _ac_ai_tehdit_aciklayici(self):
        hedef = self.entry_karantina_hedef.get().strip().strip('"')
        if GELISMIS_GUVENLIK_AVAILABLE:
            AITehditAciklayiciModal(self, dosya_yolu=hedef, ai_callback=self.ai_analiz_callback)
        else:
            messagebox.showwarning("Modül Yok", "altar_gelismis_guvenlik modülü bulunamadı.", parent=self)

    def _ac_surec_agaci(self):
        if GELISMIS_GUVENLIK_AVAILABLE:
            SurecAgaciModal(self)
        else:
            messagebox.showwarning("Modül Yok", "altar_gelismis_guvenlik modülü bulunamadı.", parent=self)

    def _ac_autorun_sentinel(self):
        if GELISMIS_GUVENLIK_AVAILABLE:
            AutorunSentinelModal(self)
        else:
            self.autoruns_raporu_goster()

    def _ac_usb_asisi(self):
        if GELISMIS_GUVENLIK_AVAILABLE:
            USBAsisiModal(self)
        else:
            messagebox.showwarning("Modül Yok", "altar_gelismis_guvenlik modülü bulunamadı.", parent=self)

    def _ac_c2_avcisi(self):
        if GELISMIS_GUVENLIK_AVAILABLE:
            C2AvcisiModal(self)
        else:
            messagebox.showwarning("Modül Yok", "altar_gelismis_guvenlik modülü bulunamadı.", parent=self)

    def _ac_butunluk_fim(self):
        if GELISMIS_GUVENLIK_AVAILABLE:
            ButunlukKalkaniFIMModal(self)
        else:
            messagebox.showwarning("Modül Yok", "altar_gelismis_guvenlik modülü bulunamadı.", parent=self)

    def raporu_ai_gonder(self):
        edr_metin = self.txt_edr_log.get("1.0", "end").strip()
        tarama_metin = self.txt_tarama_rapor.get("1.0", "end").strip()
        birlesik = f"ALTAR EDR & ANTİVİRÜS TELEMETRİSİ:\n{edr_metin[-3000:]}\n\nTARAMA RAPORU:\n{tarama_metin[:3000]}"
        if self.ai_analiz_callback:
            self.ai_analiz_callback(birlesik)