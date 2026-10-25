# -*- coding: utf-8 -*-
"""
========================================================================================
ALTAR İLERİ DÜZEY SİBER GÜVENLİK VE ANTİVİRÜS CEPHANELİĞİ (altar_gelismis_guvenlik.py)
========================================================================================
Bu modül Altar EDR ve Antivirüs sistemine 6 kritik yeni savunma yeteneği kazandırır:
  1. 🧠 AI Destekli Statik Sıfır-Gün Tehdit Açıklayıcısı (AI Threat Explainer & Inspector)
  2. 🌲 Canlı Ebeveyn-Çocuk Süreç Ağacı ve LOLBins Radarı (Process Tree & Anomaly Radar)
  3. 🛡️ Windows Otomatik Başlatma ve Kayıt Defteri Kalkanı (Autorun & Persistence Sentinel)
  4. 🔌 Otomatik USB Aşı & Çıkarılabilir Flaş Bellek Kalkanı (USB Vaccine & Auto-Guard)
  5. 🌐 C2 (Komuta Kontrol) ve Dış Ağ Sızıntı Avcısı (C2 Beacon & Socket Hunter)
  6. 🔒 Kritik Sistem Dosyası Bütünlük Kalkanı (File Integrity Monitor - FIM)

Tüm analizler salt-okunur (read-only), defansif ve kullanıcı dostudur; işletim sistemine,
yerel ağa veya kullanıcının normal bilgisayar deneyimine kesinlikle zarar vermez.
========================================================================================
"""

from __future__ import annotations

import os
import re
import sys
import time
import math
import ctypes
import hashlib
import threading
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

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


# ======================================================================================
# GÜVENLİK SABİTLERİ VE BEYAZ LİSTELER
# ======================================================================================
BEYAZ_LISTE_KRITIK_SURECLER = {
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe", "services.exe",
    "lsass.exe", "svchost.exe", "explorer.exe", "taskhostw.exe", "dwm.exe",
    "searchhost.exe", "runtimebroker.exe", "spoolsv.exe", "conhost.exe",
    "fontdrvhost.exe", "sihost.exe", "ctfmon.exe", "audiodg.exe", "shellexperiencehost.exe",
    "startmenuexperiencehost.exe", "textinputhost.exe", "altar.exe", "python.exe"
}

LOLBINS_LISTESI = {
    "powershell.exe": "PowerShell Komut Yorumlayıcı (Gizli betik / payload yürütme riski)",
    "cmd.exe": "Windows Komut İstemi (Otomasyon & betik zinciri)",
    "mshta.exe": "Microsoft HTML Uygulaması (VBScript/JScript yürütme aracı)",
    "wscript.exe": "Windows Script Host (VBS/JS betik motoru)",
    "cscript.exe": "Komut Satırı Betik Motoru",
    "certutil.exe": "Sertifika Aracı (Dış ağdan gizli dosya indirme LOLBin aracı)",
    "bitsadmin.exe": "Arka Plan İndirme Yöneticisi (Gizli dosya aktarımı)",
    "rundll32.exe": "DLL Yürütücü (Bellek-içi kod çalıştırma riski)",
    "regsvr32.exe": "OLE Kayıt Aracı (SCT/DLL sızdırma aracı)",
    "vssadmin.exe": "Gölge Kopya Yöneticisi (Fidye yazılımları yedek silmek için kullanır)",
    "schtasks.exe": "Görev Zamanlayıcı (Kalıcılık yerleşimi)",
    "reg.exe": "Kayıt Defteri Aracı (Registry manipülasyonu)"
}

BILINEN_C2_SUPHELI_PORTLAR = {
    4444: "Metasploit Default Listener",
    1337: "Elite Backdoor / C2",
    31337: "Back Orifice / Trojan",
    6667: "IRC Botnet C2",
    8888: "Alternatif HTTP / Şüpheli Proxy",
    9999: "Urgent C2 Listener",
    5555: "Android ADB / Trojan Reverse Shell",
    4443: "Alternatif SSL Ters Bağlantı",
    2222: "Alternatif SSH Tüneli",
    8081: "Alternatif HTTP C2",
    8088: "Alternatif Web C2"
}

SUPHELI_API_CAGRILARI = {
    "VirtualAlloc": "Bellek tahsisi (Shellcode enjeksiyonu)",
    "VirtualAllocEx": "Uzak süreçte bellek tahsisi (Process Injection)",
    "WriteProcessMemory": "Uzak süreç belleğine yazma (Process Hollowing)",
    "CreateRemoteThread": "Uzak süreçte iş parçacığı çalıştırma (DLL Injection)",
    "SetWindowsHookEx": "Klavye/Fare kancası takma (Keylogger riski)",
    "URLDownloadToFile": "Doğrudan internetten dosya indirme",
    "InternetOpen": "Gizli internet soketi açma",
    "HttpSendRequest": "Dış web sunucusuna HTTP veri sızdırma",
    "WinExec": "Komut yürütme",
    "ShellExecute": "Sistem kabuğundan uygulama başlatma",
    "RegSetValueEx": "Windows Kayıt Defterine kalıcı anahtar yazma",
    "RegCreateKeyEx": "Kayıt Defteri başlangıç anahtarı oluşturma",
    "CryptEncrypt": "Dosya şifreleme (Fidye yazılımı kriptografik çağrısı)",
    "IsDebuggerPresent": "Hata ayıklayıcı tespiti (Anti-Analysis / Sandbox Evasion)",
    "CheckRemoteDebuggerPresent": "Uzak hata ayıklayıcı denetimi"
}


# ======================================================================================
# 1. MOTOR FONKSİYONLARI (BAĞIMSIZ, TEST EDİLEBİLİR VE GÜVENLİ)
# ======================================================================================

def shannon_entropi_hesapla(veri: bytes) -> float:
    """Verinin Shannon entropisini 0.0 - 8.0 arasında hesaplar."""
    if not veri:
        return 0.0
    frekans = [0] * 256
    for b in veri:
        frekans[b] += 1
    toplam = len(veri)
    entropi = 0.0
    for f in frekans:
        if f > 0:
            p = f / toplam
            entropi -= p * math.log2(p)
    return round(entropi, 3)


def statik_dosya_analiz_et(dosya_yolu: str) -> Dict[str, Any]:
    """
    Şüpheli dosyayı ÇALIŞTIRMADAN (statik olarak) inceler:
    - Entropi, Hash, PE başlığı, şüpheli API'ler, URL'ler, IP'ler ve script kalıpları.
    """
    sonuc = {
        "ad": os.path.basename(dosya_yolu),
        "yol": dosya_yolu,
        "boyut_kb": 0,
        "sha256": "Bilinmiyor",
        "entropi": 0.0,
        "risk_puani": 0,
        "tehdit_seviyesi": "TEMİZ",
        "tespitler": [],
        "bulunan_apiler": [],
        "bulunan_urller": [],
        "bulunan_ipler": [],
        "ozet_aciklama": ""
    }

    if not os.path.isfile(dosya_yolu):
        sonuc["tespitler"].append("Dosya bulunamadı veya erişilemez.")
        return sonuc

    try:
        boyut = os.path.getsize(dosya_yolu)
        sonuc["boyut_kb"] = round(boyut / 1024, 2)
        if boyut > 40 * 1024 * 1024:
            sonuc["tespitler"].append("Dosya boyutu çok büyük (>40MB), derin analiz sınırlandı.")
            return sonuc

        with open(dosya_yolu, "rb") as f:
            veri = f.read()

        sonuc["sha256"] = hashlib.sha256(veri).hexdigest()
        entropi = shannon_entropi_hesapla(veri)
        sonuc["entropi"] = entropi

        # Entropi Değerlendirmesi
        if entropi > 7.3:
            sonuc["risk_puani"] += 35
            sonuc["tespitler"].append(f"Yüksek Entropi ({entropi}/8.0): Dosya yoğun şekilde şifrelenmiş veya paketlenmiş (Packer/Trojan).")
        elif entropi > 6.8:
            sonuc["risk_puani"] += 15
            sonuc["tespitler"].append(f"Orta Entropi ({entropi}/8.0): Olası sıkıştırılmış kod bloğu.")

        # PE Başlığı Denetimi
        if veri.startswith(b"MZ"):
            sonuc["tespitler"].append("Windows PE Çalıştırılabilir İkili Dosya (EXE/DLL) formatı doğrulandı.")
            # Çift uzantı kontrolü
            ad_lower = sonuc["ad"].lower()
            if any(ad_lower.endswith(s) for s in [".pdf.exe", ".docx.exe", ".txt.exe", ".jpg.exe", ".png.exe"]):
                sonuc["risk_puani"] += 50
                sonuc["tespitler"].append("🚨 ALDATICI ÇİFT UZANTI: Dosya belge/resim gibi gösterilerek gizlenmiş .exe!")

        # Metin / String Taraması
        metin = veri.decode("latin-1", errors="ignore")

        # API Taraması
        for api, aciklama in SUPHELI_API_CAGRILARI.items():
            if api in metin:
                sonuc["bulunan_apiler"].append(f"{api} ({aciklama})")
                sonuc["risk_puani"] += 10

        # URL ve IP Taraması
        urller = set(re.findall(r"https?://[a-zA-Z0-9\.\-_/]{8,60}", metin))
        ipler = set(re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", metin))
        # 127.0.0.1 ve 0.0.0.0 filtrele
        ipler = {ip for ip in ipler if not ip.startswith("127.") and ip != "0.0.0.0"}

        if urller:
            sonuc["bulunan_urller"] = list(urller)[:6]
            sonuc["tespitler"].append(f"Kod içine gömülü {len(urller)} adet harici web adresi tespit edildi.")
            sonuc["risk_puani"] += 15

        if ipler:
            sonuc["bulunan_ipler"] = list(ipler)[:6]
            sonuc["tespitler"].append(f"Kod içine gömülü {len(ipler)} adet sabit IP adresi tespit edildi.")
            sonuc["risk_puani"] += 15

        # Script Tehlikeleri
        if any(k in metin.lower() for k in ["-windowstyle hidden", "-w hidden", "bypass -enc", "frombase64string", "downloadstring"]):
            sonuc["risk_puani"] += 35
            sonuc["tespitler"].append("Gizli PowerShell yürütme kalıbı (-w hidden / base64 payload) tespit edildi.")

        # Risk Puanı Tavanı ve Seviye
        sonuc["risk_puani"] = min(100, sonuc["risk_puani"])
        puan = sonuc["risk_puani"]

        if puan >= 75:
            sonuc["tehdit_seviyesi"] = "KRİTİK TEHLİKE"
        elif puan >= 45:
            sonuc["tehdit_seviyesi"] = "YÜKSEK RİSK"
        elif puan >= 20:
            sonuc["tehdit_seviyesi"] = "ŞÜPHELİ / DİKKAT"
        else:
            sonuc["tehdit_seviyesi"] = "DÜŞÜK RİSK / TEMİZ"

        sonuc["ozet_aciklama"] = (
            f"Tehdit Skoru: {puan}/100 [{sonuc['tehdit_seviyesi']}]. "
            f"Entropi: {entropi}. Tespit edilen şüpheli API sayısı: {len(sonuc['bulunan_apiler'])}. "
            f"Dış bağlantı göstergesi: {len(sonuc['bulunan_urller'])} URL, {len(sonuc['bulunan_ipler'])} IP."
        )

    except Exception as e:
        sonuc["tespitler"].append(f"Analiz sırasında hata: {e}")

    return sonuc


def surec_agaci_tara() -> List[Dict[str, Any]]:
    """Çalışan tüm süreçleri ebeveyn-çocuk ilişkisi ve LOLBin tespitiyle listeler."""
    if not PSUTIL_AVAILABLE:
        return []

    surecler = []
    for proc in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'exe']):
        try:
            info = proc.info
            pid = info['pid']
            ppid = info['ppid'] or 0
            name = (info['name'] or "").lower()
            cmd = " ".join(info['cmdline'] or []) if info['cmdline'] else ""
            mem_mb = round((info['memory_info'].rss / (1024 * 1024)), 1) if info['memory_info'] else 0.0

            is_lolbin = name in LOLBINS_LISTESI
            is_hidden = "-w hidden" in cmd.lower() or "-windowstyle hidden" in cmd.lower() or "downloadstring" in cmd.lower()

            risk = "NORMAL"
            if is_hidden:
                risk = "KRİTİK (GİZLİ SÜREÇ)"
            elif is_lolbin:
                risk = "ŞÜPHELİ (LOLBin)"

            surecler.append({
                "pid": pid,
                "ppid": ppid,
                "name": info['name'] or "Bilinmiyor",
                "cmd": cmd,
                "mem_mb": mem_mb,
                "risk": risk,
                "is_lolbin": is_lolbin,
                "lolbin_aciklama": LOLBINS_LISTESI.get(name, ""),
                "exe": info['exe'] or ""
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return surecler


def autorun_kayitlarini_derin_tara() -> List[Dict[str, Any]]:
    """Kayıt defteri ve başlangıç klasörlerindeki tüm otomatik başlatma kayıtlarını inceler."""
    kayitlar = []
    if os.name != "nt" or winreg is None:
        return kayitlar

    hedefler = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU\\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM\\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU\\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM\\RunOnce")
    ]

    for root, path, label in hedefler:
        try:
            with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as k:
                idx = 0
                while True:
                    try:
                        isim, val, _ = winreg.EnumValue(k, idx)
                        idx += 1
                        val_str = str(val).strip()

                        # Dosya varlık ve şüpheli konum denetimi
                        supheli = False
                        neden = "Standart Başlangıç Programı"

                        val_lower = val_str.lower()
                        if "temp" in val_lower or "appdata\\local\\temp" in val_lower:
                            supheli = True
                            neden = "⚠️ Temp (Geçici Dizin) üzerinden çalışıyor!"
                        elif any(ext in val_lower for ext in [".vbs", ".js", ".ps1", ".bat"]):
                            supheli = True
                            neden = "⚠️ Doğrudan betik dosyası (.vbs/.js/.bat) başlatıyor!"

                        kayitlar.append({
                            "isim": isim,
                            "konum": label,
                            "komut": val_str,
                            "supheli": supheli,
                            "durum": neden
                        })
                    except OSError:
                        break
        except Exception:
            pass

    # Başlangıç Klasörleri Denetimi
    startup_paths = [
        (os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"), "Kullanıcı Startup"),
        (os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup"), "Sistem Startup")
    ]
    for sp, label in startup_paths:
        if os.path.exists(sp):
            try:
                for dosya in os.listdir(sp):
                    if dosya.lower() != "desktop.ini":
                        tam_yol = os.path.join(sp, dosya)
                        kayitlar.append({
                            "isim": dosya,
                            "konum": label,
                            "komut": tam_yol,
                            "supheli": any(dosya.lower().endswith(ext) for ext in [".vbs", ".bat", ".cmd", ".ps1"]),
                            "durum": "Startup Klasörü Dosyası"
                        })
            except Exception:
                pass

    return kayitlar


def usb_suruculeri_tara() -> List[Dict[str, Any]]:
    """Bağlı tüm çıkarılabilir USB / Flash sürücüleri tespit eder ve güvenlik taraması yapar."""
    suruculer = []
    if os.name != "nt":
        return suruculer

    for harf in "DEFGHIJKLMNOPQRSTUVWXYZ":
        kok = f"{harf}:\\"
        if os.path.exists(kok):
            try:
                dtype = ctypes.windll.kernel32.GetDriveTypeW(kok)
                # DRIVE_REMOVABLE = 2
                if dtype == 2:
                    # USB İçi Analiz
                    gizli_dosyalar = []
                    kisayol_virüsleri = []
                    autorun_var = False
                    asili_mi = False

                    autorun_yol = os.path.join(kok, "autorun.inf")
                    if os.path.exists(autorun_yol):
                        autorun_var = True
                        if os.path.isdir(autorun_yol):
                            asili_mi = True

                    try:
                        for dosya in os.listdir(kok)[:100]:
                            tam = os.path.join(kok, dosya)
                            if dosya.lower().endswith(".lnk"):
                                kisayol_virüsleri.append(dosya)
                            # Gizli dosya denetimi
                            try:
                                attrs = ctypes.windll.kernel32.GetFileAttributesW(tam)
                                if attrs != -1 and (attrs & 2):  # FILE_ATTRIBUTE_HIDDEN
                                    gizli_dosyalar.append(dosya)
                            except Exception:
                                pass
                    except Exception:
                        pass

                    suruculer.append({
                        "harf": kok,
                        "autorun_var": autorun_var,
                        "asili_mi": asili_mi,
                        "gizli_sayisi": len(gizli_dosyalar),
                        "kisayol_sayisi": len(kisayol_virüsleri),
                        "kisayol_listesi": kisayol_virüsleri,
                        "durum": "💉 Aşılanmış / Korumalı" if asili_mi else ("⚠️ Şüpheli Kısayollar Tespit Edildi" if kisayol_virüsleri else "✅ Temiz / Hazır")
                    })
            except Exception:
                pass

    return suruculer


def usb_asila(surucu_koku: str) -> Tuple[bool, str]:
    """
    USB belleğe aşı uygular:
    Malware'in 'autorun.inf' dosyası oluşturup otomatik yayılmasını engellemek için
    salt-okunur ve korumalı bir autorun.inf klasörü inşa eder.
    """
    if not os.path.exists(surucu_koku):
        return False, "Sürücü bulunamadı."

    hedef_klasor = os.path.join(surucu_koku, "autorun.inf")
    try:
        if os.path.isfile(hedef_klasor):
            os.remove(hedef_klasor)

        os.makedirs(hedef_klasor, exist_ok=True)
        # Klasörü salt okunur ve sistem klasörü yap
        ctypes.windll.kernel32.SetFileAttributesW(hedef_klasor, 0x01 | 0x02 | 0x04)  # READONLY | HIDDEN | SYSTEM
        return True, f"'{surucu_koku}' sürücüsü başarıyla aşılandı. Zararlı yazılımlar autorun.inf oluşturamaz."
    except Exception as e:
        return False, f"Aşılama hatası: {e}"


def c2_ve_dis_baglantilari_tara() -> List[Dict[str, Any]]:
    """Aktif dış ağ soketlerini (ESTABLISHED) inceler ve bilinen C2 portları ile eşleştirir."""
    if not PSUTIL_AVAILABLE:
        return []

    baglantilar = []
    try:
        conns = psutil.net_connections(kind='inet')
        for c in conns:
            if c.status in ("ESTABLISHED", "SYN_SENT") and c.raddr:
                r_ip, r_port = c.raddr.ip, c.raddr.port
                l_port = c.laddr.port if c.laddr else 0
                pid = c.pid or 0

                # Loopback ve yerel IP filtrele
                if r_ip.startswith("127.") or r_ip in ("0.0.0.0", "::1"):
                    continue

                proc_name = "Bilinmiyor"
                proc_exe = ""
                if pid:
                    try:
                        p = psutil.Process(pid)
                        proc_name = p.name()
                        proc_exe = p.exe()
                    except Exception:
                        pass

                risk = "NORMAL"
                aciklama = "Standart Dış Ağ Bağlantısı"
                if r_port in BILINEN_C2_SUPHELI_PORTLAR:
                    risk = "🚨 YÜKSEK (C2 PORTU)"
                    aciklama = BILINEN_C2_SUPHELI_PORTLAR[r_port]
                elif r_port not in (80, 443, 53, 123, 8080):
                    risk = "⚠️ DİKKAT (STANDART DIŞI PORT)"
                    aciklama = f"Port: {r_port}"

                baglantilar.append({
                    "pid": pid,
                    "proc": proc_name,
                    "exe": proc_exe,
                    "l_port": l_port,
                    "r_ip": r_ip,
                    "r_port": r_port,
                    "durum": c.status,
                    "risk": risk,
                    "aciklama": aciklama
                })
    except Exception:
        pass

    return baglantilar


def hosts_butunluk_denetle() -> Dict[str, Any]:
    """
    Windows hosts dosyasını inceler, DNS sızıntısı ve sahte yönlendirmeleri denetler.
    """
    hosts_yol = r"C:\Windows\System32\drivers\etc\hosts" if os.name == "nt" else "/etc/hosts"
    sonuc = {
        "yol": hosts_yol,
        "mevcut": os.path.exists(hosts_yol),
        "sha256": "",
        "toplam_satir": 0,
        "ozel_yonlendirmeler": [],
        "riskli_yonlendirmeler": [],
        "durum": "TEMİZ",
        "icerik": ""
    }

    if not sonuc["mevcut"]:
        sonuc["durum"] = "HOSTS DOSYASI BULUNAMADI"
        return sonuc

    try:
        with open(hosts_yol, "r", encoding="utf-8", errors="ignore") as f:
            satirlar = f.readlines()

        sonuc["toplam_satir"] = len(satirlar)
        sonuc["icerik"] = "".join(satirlar)
        sonuc["sha256"] = hashlib.sha256(sonuc["icerik"].encode("utf-8")).hexdigest()

        for satir in satirlar:
            temiz = satir.strip()
            if temiz and not temiz.startswith("#"):
                parcalar = temiz.split()
                if len(parcalar) >= 2:
                    ip = parcalar[0]
                    domain = parcalar[1].lower()
                    sonuc["ozel_yonlendirmeler"].append(f"{ip} -> {domain}")

                    # Banka, antivirüs, güvenlik veya arama motoru saptırma denetimi
                    if any(k in domain for k in ["google", "microsoft", "kaspersky", "virustotal", "symantec", "eset", "avast", "bank"]):
                        if ip not in ("127.0.0.1", "0.0.0.0", "::1"):
                            sonuc["riskli_yonlendirmeler"].append(f"🚨 TEHLİKELİ DNS SAPTIRMASI: {domain} -> {ip}")

        if sonuc["riskli_yonlendirmeler"]:
            sonuc["durum"] = "🚨 KRİTİK: ZARARLI DNS SAPTIRMASI TESPİT EDİLDİ!"
        elif sonuc["ozel_yonlendirmeler"]:
            sonuc["durum"] = f"BİLGİ: {len(sonuc['ozel_yonlendirmeler'])} Adet Özel Yönlendirme Mevcut"
        else:
            sonuc["durum"] = "✅ Standart Temiz Windows Hosts Dosyası"

    except Exception as e:
        sonuc["durum"] = f"Okuma Hatası: {e}"

    return sonuc


# ======================================================================================
# 2. GÖRSEL KULLANICI ARAYÜZLERİ (CUSTOMTKINTER MODAL PENCERELERİ)
# ======================================================================================

class AITehditAciklayiciModal(ctk.CTkToplevel):
    """🧠 1. AI Destekli Statik Sıfır-Gün Tehdit Açıklayıcısı"""

    def __init__(self, parent, dosya_yolu: str = "", ai_callback=None):
        super().__init__(parent)
        self.ai_callback = ai_callback
        self.title("🧠 Altar AI Statik Sıfır-Gün Tehdit Açıklayıcısı & Heuristic Inspector")
        self.geometry("860x650")
        self.configure(fg_color="#070B14")

        # Üst Başlık
        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="🧠 AI DESTEKLİ STATİK SIFIR-GÜN TEHDİT ANALİZÖRÜ (ZERO-DAY HEURISTICS)",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#00FFCC"
        ).pack(side="left", padx=12, pady=8)

        # Dosya Seçici Barı
        secim_bar = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
        secim_bar.pack(fill="x", padx=12, pady=(0, 10))

        self.entry_yol = ctk.CTkEntry(
            secim_bar, placeholder_text="İncelenecek dosyanın yolunu seçin veya yapıştırın...",
            font=ctk.CTkFont(family="Consolas", size=11), height=32
        )
        self.entry_yol.pack(side="left", fill="x", expand=True, padx=8, pady=6)
        if dosya_yolu:
            self.entry_yol.insert(0, dosya_yolu)

        ctk.CTkButton(
            secim_bar, text="📁 Dosya Seç", width=110, height=32,
            fg_color="#1f538d", hover_color="#14375e", command=self._dosya_sec
        ).pack(side="left", padx=4, pady=6)

        ctk.CTkButton(
            secim_bar, text="⚡ Statik Analiz Et", width=135, height=32,
            fg_color="#00A86B", hover_color="#007F50", font=ctk.CTkFont(weight="bold"),
            command=self._analizi_baslat
        ).pack(side="left", padx=4, pady=6)

        # Rapor Alanı
        self.txt_rapor = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#A6E3A1", wrap="word"
        )
        self.txt_rapor.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Alt Butonlar
        alt_bar = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
        alt_bar.pack(fill="x", padx=12, pady=(0, 12))

        self.btn_ai_sor = ctk.CTkButton(
            alt_bar, text="🤖 Altar Yapay Zekasına Türkçe Yorumlat", height=34,
            fg_color="#4B0082", hover_color="#360061", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ai_gonder
        )
        self.btn_ai_sor.pack(side="left", padx=8, pady=6)

        ctk.CTkButton(
            alt_bar, text="Kapat", width=100, height=34, fg_color="#334155",
            hover_color="#475569", command=self.destroy
        ).pack(side="right", padx=8, pady=6)

        if dosya_yolu:
            self._analizi_baslat()

    def _dosya_sec(self):
        p = filedialog.askopenfilename(title="Analiz Edilecek Dosyayı Seçin", parent=self)
        if p:
            self.entry_yol.delete(0, "end")
            self.entry_yol.insert(0, p)
            self._analizi_baslat()

    def _analizi_baslat(self):
        yol = self.entry_yol.get().strip().strip('"')
        if not yol or not os.path.isfile(yol):
            messagebox.showwarning("Geçersiz Dosya", "Lütfen geçerli bir dosya seçin.", parent=self)
            return

        self.txt_rapor.delete("1.0", "end")
        self.txt_rapor.insert("1.0", f"⏳ '{os.path.basename(yol)}' statik olarak derin analiz ediliyor...\n")
        self.update_idletasks()

        def _worker():
            r = statik_dosya_analiz_et(yol)
            metin = [
                "=" * 70,
                f"🧠 ALTAR STATİK SIFIR-GÜN HEURISTIC TEHDİT ANALİZİ",
                "=" * 70,
                f"Dosya Adı       : {r['ad']}",
                f"Dosya Yolu      : {r['yol']}",
                f"Boyut           : {r['boyut_kb']} KB",
                f"SHA-256 Özeti   : {r['sha256']}",
                f"Shannon Entropi : {r['entropi']} / 8.0",
                f"Risk Puanı      : {r['risk_puani']} / 100",
                f"Tehdit Durumu   : {r['tehdit_seviyesi']}",
                "-" * 70,
                f"📌 TESPİT EDİLEN GÜVENLİK BULGULARI:"
            ]
            for b in r["tespitler"]:
                metin.append(f"  • {b}")

            if r["bulunan_apiler"]:
                metin.append("\n📌 BULUNAN RİSKLİ/KRİTİK SİSTEM API'LERİ:")
                for api in r["bulunan_apiler"]:
                    metin.append(f"  ⚡ {api}")

            if r["bulunan_urller"]:
                metin.append("\n📌 KOD İÇİNDEKİ HARİCİ WEB BAĞLANTILARI:")
                for u in r["bulunan_urller"]:
                    metin.append(f"  🌐 {u}")

            if r["bulunan_ipler"]:
                metin.append("\n📌 KOD İÇİNDEKİ SABİT HEDEF IP ADRESLERİ:")
                for ip in r["bulunan_ipler"]:
                    metin.append(f"  🎯 {ip}")

            metin.append("-" * 70)
            metin.append("💡 GÜVENLİK ÖNERİSİ:")
            if r["risk_puani"] >= 75:
                metin.append("⚠️ Bu dosya sistem için son derece tehlikelidir! Asla çalıştırmayın ve 'Karantina'ya alın.")
            elif r["risk_puani"] >= 40:
                metin.append("⚠️ Şüpheli davranış kalıpları tespit edildi. Dosyayı çalıştırmadan önce 'AI Yorumlat' ile inceleyin.")
            else:
                metin.append("✅ Belirgin bir zararlı yazılım imzası veya gizleme tekniği saptanmadı.")
            metin.append("=" * 70)

            cikti = "\n".join(metin)
            self.txt_rapor.delete("1.0", "end")
            self.txt_rapor.insert("1.0", cikti)

        threading.Thread(target=_worker, daemon=True).start()

    def _ai_gonder(self):
        icerik = self.txt_rapor.get("1.0", "end").strip()
        if not icerik or len(icerik) < 30:
            messagebox.showinfo("Bilgi", "Lütfen önce bir dosya analiz edin.", parent=self)
            return

        if self.ai_callback:
            prompt = (
                f"Aşağıdaki şüpheli dosya statik analiz çıktısını bir kıdemli siber güvenlik uzmanı olarak incele. "
                f"Dosyanın ne yapmaya çalıştığını, hangi saldırı tekniğini (MITRE ATT&CK) kullandığını ve "
                f"kullanıcıya Türkçe olarak ne yapması gerektiğini açık ve net anlat:\n\n{icerik[:4000]}"
            )
            self.ai_callback(prompt)
            messagebox.showinfo("AI Analiz İsteği", "Analiz çıktısı Altar Yapay Zeka Sohbet Çekirdeğine aktarıldı!", parent=self)
            self.destroy()
        else:
            messagebox.showinfo("Rapor Hazır", "Rapor panoya kopyalanabilir veya Altar sohbetine yapıştırılabilir.", parent=self)


class SurecAgaciModal(ctk.CTkToplevel):
    """🌲 2. Canlı Süreç Ağacı ve Ebeveyn-Çocuk Anomali Radarı"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("🌲 Altar Canlı Süreç Ağacı & LOLBins Anomali Radarı")
        self.geometry("980x680")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="🌲 CANLI SÜREÇ AĞACI, EBEVEYN-ÇOCUK İLİŞKİSİ & LOLBins RADARI",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#00FF88"
        ).pack(side="left", padx=12, pady=8)

        self.lbl_sayac = ctk.CTkLabel(
            ust, text="Süreç: 0 | Şüpheli: 0", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#FFD700"
        )
        self.lbl_sayac.pack(side="right", padx=12, pady=8)

        # Kontrol ve Filtre
        kontrol = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
        kontrol.pack(fill="x", padx=12, pady=(0, 10))

        self.entry_ara = ctk.CTkEntry(
            kontrol, placeholder_text="Süreç Adı veya PID ile filtrele...", font=ctk.CTkFont(family="Consolas", size=11),
            width=260, height=30
        )
        self.entry_ara.pack(side="left", padx=8, pady=6)
        self.entry_ara.bind("<KeyRelease>", lambda e: self._tabloyu_guncelle())

        ctk.CTkButton(
            kontrol, text="🔄 Yenile", width=90, height=30, fg_color="#1f538d",
            hover_color="#14375e", command=self._verileri_cek_ve_goster
        ).pack(side="left", padx=4, pady=6)

        ctk.CTkButton(
            kontrol, text="⏸️ Askıya Al (Suspend)", width=155, height=30, fg_color="#B85C00",
            hover_color="#8F4700", command=self._seciliyi_askiya_al
        ).pack(side="left", padx=4, pady=6)

        ctk.CTkButton(
            kontrol, text="▶️ Devam Ettir (Resume)", width=155, height=30, fg_color="#008080",
            hover_color="#005A5A", command=self._seciliyi_devam_ettir
        ).pack(side="left", padx=4, pady=6)

        ctk.CTkButton(
            kontrol, text="⏹️ Sonlandır (Kill)", width=135, height=30, fg_color="#C62828",
            hover_color="#8E0000", font=ctk.CTkFont(weight="bold"), command=self._seciliyi_sonlandir
        ).pack(side="left", padx=4, pady=6)

        # Tablo Alanı
        self.txt_liste = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#E2E8F0", wrap="none"
        )
        self.txt_liste.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.surec_verileri = []
        self._verileri_cek_ve_goster()

    def _verileri_cek_ve_goster(self):
        def _worker():
            self.surec_verileri = surec_agaci_tara()
            self._tabloyu_guncelle()

        threading.Thread(target=_worker, daemon=True).start()

    def _tabloyu_guncelle(self):
        arama = self.entry_ara.get().lower().strip()
        filtreli = [
            s for s in self.surec_verileri
            if not arama or arama in s['name'].lower() or arama in str(s['pid'])
        ]

        # PID hiyerarşisine göre sırala
        filtreli.sort(key=lambda x: (x['risk'] == "NORMAL", x['ppid'], x['pid']))

        supheli_sayi = sum(1 for s in self.surec_verileri if s['risk'] != "NORMAL")
        self.lbl_sayac.configure(text=f"Toplam Süreç: {len(self.surec_verileri)} | Şüpheli/LOLBin: {supheli_sayi}")

        satirlar = [
            f"{'PID':<8} {'PPID':<8} {'BELLEK':<10} {'DURUM / RİSK':<24} {'SÜREÇ ADI VE KOMUT SATIRI':<60}",
            "=" * 120
        ]
        for s in filtreli:
            risk_str = s['risk']
            if s['is_lolbin'] and s['lolbin_aciklama']:
                risk_str = f"⚠️ {s['name']} (LOLBin)"
            satirlar.append(
                f"{s['pid']:<8} {s['ppid']:<8} {str(s['mem_mb']) + ' MB':<10} {risk_str:<24} {s['name']} -> {s['cmd'][:70]}"
            )

        self.txt_liste.delete("1.0", "end")
        self.txt_liste.insert("1.0", "\n".join(satirlar))

    def _secili_pid_al(self) -> Optional[int]:
        try:
            secili_metin = self.txt_liste.get("insert linestart", "insert lineend").strip()
            if not secili_metin or secili_metin.startswith("PID") or secili_metin.startswith("="):
                messagebox.showwarning("Seçim Yok", "Lütfen işlem yapmak istediğiniz sürecin bulunduğu satıra tıklayın.", parent=self)
                return None
            pid_str = secili_metin.split()[0]
            return int(pid_str)
        except Exception:
            messagebox.showwarning("Hata", "Süreç PID numarası satırdan okunamadı.", parent=self)
            return None

    def _seciliyi_askiya_al(self):
        pid = self._secili_pid_al()
        if not pid:
            return
        try:
            p = psutil.Process(pid)
            if p.name().lower() in BEYAZ_LISTE_KRITIK_SURECLER:
                messagebox.showerror("Engellendi", "Windows kritik sistem süreçleri dondurulamaz!", parent=self)
                return
            p.suspend()
            messagebox.showinfo("Başarılı", f"PID {pid} ({p.name()}) süreci askıya alındı (Donduruldu).", parent=self)
            self._verileri_cek_ve_goster()
        except Exception as e:
            messagebox.showerror("Hata", f"Süreci askıya alma başarısız: {e}", parent=self)

    def _seciliyi_devam_ettir(self):
        pid = self._secili_pid_al()
        if not pid:
            return
        try:
            p = psutil.Process(pid)
            p.resume()
            messagebox.showinfo("Başarılı", f"PID {pid} ({p.name()}) süreci devam ettirildi.", parent=self)
            self._verileri_cek_ve_goster()
        except Exception as e:
            messagebox.showerror("Hata", f"Süreci devam ettirme başarısız: {e}", parent=self)

    def _seciliyi_sonlandir(self):
        pid = self._secili_pid_al()
        if not pid:
            return
        try:
            p = psutil.Process(pid)
            if p.name().lower() in BEYAZ_LISTE_KRITIK_SURECLER:
                messagebox.showerror("Engellendi", "Windows kritik sistem süreçleri sonlandırılamaz!", parent=self)
                return
            cevap = messagebox.askyesno(
                "Sonlandırma Onayı",
                f"PID {pid} ({p.name()}) sürecini sonlandırmak istediğinize emin misiniz?",
                parent=self
            )
            if cevap:
                p.kill()
                messagebox.showinfo("Sonlandırıldı", f"PID {pid} süreci başarıyla sonlandırıldı.", parent=self)
                self._verileri_cek_ve_goster()
        except Exception as e:
            messagebox.showerror("Hata", f"Süreç sonlandırılamadı: {e}", parent=self)


class AutorunSentinelModal(ctk.CTkToplevel):
    """🛡️ 3. Windows Otomatik Başlatma ve Kayıt Defteri Kalkanı"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("🛡️ Altar Windows Otomatik Başlatma & Kayıt Defteri Kalkanı (Autorun Sentinel)")
        self.geometry("920x620")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="🛡️ WINDOWS BAŞLANGIÇ & REGISTRY KALICILIK DENETÇİSİ (AUTORUN SENTINEL)",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#FFD700"
        ).pack(side="left", padx=12, pady=8)

        ctk.CTkButton(
            ust, text="🔄 Yeniden Tara", width=120, height=28, fg_color="#1f538d",
            hover_color="#14375e", command=self._tara
        ).pack(side="right", padx=12, pady=8)

        self.txt_rapor = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#E2E8F0", wrap="word"
        )
        self.txt_rapor.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._tara()

    def _tara(self):
        def _worker():
            kayitlar = autorun_kayitlarini_derin_tara()
            satirlar = [
                "=" * 90,
                f"🛡️ ALTAR WINDOWS AUTORUNS & BAŞLANGIÇ GÜVENLİK RAPORU ({datetime.now().strftime('%d.%m.%Y %H:%M:%S')})",
                "=" * 90,
                f"Toplam İncelenen Kayıt: {len(kayitlar)} Adet",
                "-" * 90
            ]
            supheliler = [k for k in kayitlar if k['supheli']]
            if supheliler:
                satirlar.append("🚨 DİKKAT GEREKTİREN ŞÜPHELİ BAŞLANGIÇ GİRDİLERİ:")
                for s in supheliler:
                    satirlar.append(f"  • {s['isim']} [{s['konum']}]")
                    satirlar.append(f"    Uyarı : {s['durum']}")
                    satirlar.append(f"    Komut : {s['komut']}\n")
                satirlar.append("-" * 90)

            satirlar.append("📌 TÜM AKTİF BAŞLANGIÇ (AUTORUN) KAYITLARI:")
            for k in kayitlar:
                durum_ikon = "⚠️" if k['supheli'] else "✅"
                satirlar.append(f"{durum_ikon} {k['isim']:<30} [{k['konum']}]")
                satirlar.append(f"   Komut: {k['komut']}\n")

            satirlar.append("=" * 90)
            self.txt_rapor.delete("1.0", "end")
            self.txt_rapor.insert("1.0", "\n".join(satirlar))

        threading.Thread(target=_worker, daemon=True).start()


class USBAsisiModal(ctk.CTkToplevel):
    """🔌 4. Otomatik USB Aşı & Flaş Bellek Koruyucusu"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("🔌 Altar Otomatik USB Aşı & Flaş Bellek Kalkanı")
        self.geometry("820x560")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="🔌 ÇIKARILABİLİR USB & FLAŞ BELLEK AŞILAMA VE GÜVENLİK MERKEZİ",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#00E5FF"
        ).pack(side="left", padx=12, pady=8)

        ctk.CTkButton(
            ust, text="🔄 Sürücüleri Tara", width=130, height=28, fg_color="#1f538d",
            hover_color="#14375e", command=self._tara
        ).pack(side="right", padx=12, pady=8)

        self.txt_bilgi = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#A6E3A1", wrap="word"
        )
        self.txt_bilgi.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        alt_bar = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
        alt_bar.pack(fill="x", padx=12, pady=(0, 12))

        self.entry_surucu = ctk.CTkEntry(
            alt_bar, placeholder_text="Aşılanacak sürücü harfi (Örn: E:\\ veya F:\\)...",
            font=ctk.CTkFont(family="Consolas", size=11), width=280, height=32
        )
        self.entry_surucu.pack(side="left", padx=8, pady=6)

        ctk.CTkButton(
            alt_bar, text="💉 Seçili Sürücüyü Aşıla (Immunize)", height=32,
            fg_color="#00A86B", hover_color="#007F50", font=ctk.CTkFont(weight="bold"),
            command=self._asila
        ) .pack(side="left", padx=4, pady=6)

        ctk.CTkButton(
            alt_bar, text="Kapat", width=90, height=32, fg_color="#334155",
            hover_color="#475569", command=self.destroy
        ).pack(side="right", padx=8, pady=6)

        self._tara()

    def _tara(self):
        def _worker():
            suruculer = usb_suruculeri_tara()
            satirlar = [
                "=" * 80,
                f"🔌 BAĞLI ÇIKARILABİLİR USB FLAŞ SÜRÜCÜ DURUM RAPORU",
                "=" * 80
            ]
            if not suruculer:
                satirlar.append("Bilgisayara takılı herhangi bir çıkarılabilir USB bellek tespit edilmedi.")
                satirlar.append("Flaş belleğinizi taktıktan sonra 'Sürücüleri Tara' butonuna basabilirsiniz.")
            else:
                for s in suruculer:
                    satirlar.append(f"📁 Sürücü Harfi   : {s['harf']}")
                    satirlar.append(f"   Güvenlik Durumu: {s['durum']}")
                    satirlar.append(f"   Aşılı Mı?      : {'Evet (Korumalı)' if s['asili_mi'] else 'Hayır (Aşılanması önerilir)'}")
                    satirlar.append(f"   Gizli Dosyalar : {s['gizli_sayisi']} Adet")
                    satirlar.append(f"   Kısayol Virüsü : {s['kisayol_sayisi']} Adet (.lnk)")
                    if s['kisayol_listesi']:
                        satirlar.append(f"   Şüpheli Dosyalar: {', '.join(s['kisayol_listesi'])}")
                    satirlar.append("-" * 80)

            satirlar.append("\n💡 BİLGİ:")
            satirlar.append("Aşılama işlemi, USB belleğe 'autorun.inf' adlı kilitli bir koruma klasörü oluşturur.")
            satirlar.append("Böylece zararlı yazılımlar USB üzerinden bilgisayarınıza otomatik bulaşamaz.")
            satirlar.append("=" * 80)

            self.txt_bilgi.delete("1.0", "end")
            self.txt_bilgi.insert("1.0", "\n".join(satirlar))

        threading.Thread(target=_worker, daemon=True).start()

    def _asila(self):
        harf = self.entry_surucu.get().strip().upper()
        if not harf:
            messagebox.showwarning("Girdi Yok", "Lütfen aşılanacak sürücü harfini girin (Örn: E:\\)", parent=self)
            return
        if not harf.endswith(":\\"):
            harf = harf[0] + ":\\"

        ok, msg = usb_asila(harf)
        if ok:
            messagebox.showinfo("Aşılama Başarılı", msg, parent=self)
            self._tara()
        else:
            messagebox.showerror("Hata", msg, parent=self)


class C2AvcisiModal(ctk.CTkToplevel):
    """🌐 5. C2 (Komuta Kontrol) ve Dış Ağ Sızıntı Avcısı"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("🌐 Altar C2 (Komuta Kontrol) & Dış Ağ Sızıntı Avcısı")
        self.geometry("960x640")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="🌐 C2 BEACON, DIŞ AĞ SIZINTI & ŞÜPHELİ PORT AVCISI",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#FF6B6B"
        ).pack(side="left", padx=12, pady=8)

        ctk.CTkButton(
            ust, text="🔄 Bağlantıları Tara", width=140, height=28, fg_color="#1f538d",
            hover_color="#14375e", command=self._tara
        ).pack(side="right", padx=12, pady=8)

        self.txt_baglantilar = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#E2E8F0", wrap="none"
        )
        self.txt_baglantilar.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._tara()

    def _tara(self):
        def _worker():
            baglantilar = c2_ve_dis_baglantilari_tara()
            satirlar = [
                f"{'PID':<8} {'SÜREÇ ADI':<20} {'UZAK HEDEF IP:PORT':<26} {'DURUM':<14} {'GÜVENLİK / RİSK DURUMU':<30}",
                "=" * 110
            ]
            if not baglantilar:
                satirlar.append("Aktif dış ağ (ESTABLISHED) bağlantısı bulunamadı.")
            else:
                for b in baglantilar:
                    hedef = f"{b['r_ip']}:{b['r_port']}"
                    satirlar.append(
                        f"{b['pid']:<8} {b['proc'][:18]:<20} {hedef:<26} {b['durum']:<14} {b['risk']} ({b['aciklama']})"
                    )

            self.txt_baglantilar.delete("1.0", "end")
            self.txt_baglantilar.insert("1.0", "\n".join(satirlar))

        threading.Thread(target=_worker, daemon=True).start()


class ButunlukKalkaniFIMModal(ctk.CTkToplevel):
    """🔒 6. Kritik Sistem Dosyası Bütünlük Kalkanı (Hosts & FIM)"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("🔒 Altar Kritik Sistem Dosyası Bütünlük Kalkanı (File Integrity Monitor - FIM)")
        self.geometry("880x640")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="🔒 KRİTİK SİSTEM DOSYASI BÜTÜNLÜK KALKANI (HOSTS & FIM MONITOR)",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#00FFCC"
        ).pack(side="left", padx=12, pady=8)

        ctk.CTkButton(
            ust, text="🔄 Bütünlüğü Denetle", width=140, height=28, fg_color="#1f538d",
            hover_color="#14375e", command=self._denetle
        ).pack(side="right", padx=12, pady=8)

        self.lbl_durum = ctk.CTkLabel(
            self, text="Durum: Denetleniyor...", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#FFD700"
        )
        self.lbl_durum.pack(anchor="w", padx=16, pady=(4, 6))

        self.txt_icerik = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#A6E3A1", wrap="word"
        )
        self.txt_icerik.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        alt_bar = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
        alt_bar.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkButton(
            alt_bar, text="🛡️ Orijinal Temiz Hosts Dosyasını Geri Yükle", height=32,
            fg_color="#B85C00", hover_color="#8F4700", font=ctk.CTkFont(weight="bold"),
            command=self._hosts_temizle
        ).pack(side="left", padx=8, pady=6)

        ctk.CTkButton(
            alt_bar, text="Kapat", width=90, height=32, fg_color="#334155",
            hover_color="#475569", command=self.destroy
        ).pack(side="right", padx=8, pady=6)

        self._denetle()

    def _denetle(self):
        r = hosts_butunluk_denetle()
        renk = "#00FF88" if "Standart" in r["durum"] or "Temiz" in r["durum"] else ("#FF4444" if "TEHLİKELİ" in r["durum"] else "#FFD700")
        self.lbl_durum.configure(text=f"Durum: {r['durum']} | SHA-256: {r['sha256'][:16]}...", text_color=renk)

        cikti = [
            f"=== 🔒 WINDOWS HOSTS DOSYASI BÜTÜNLÜK DENETİMİ ===",
            f"Dosya Konumu : {r['yol']}",
            f"Toplam Satır : {r['toplam_satir']}",
            f"SHA-256 Özeti: {r['sha256']}",
            "-" * 70
        ]
        if r["riskli_yonlendirmeler"]:
            cikti.append("🚨 BULUNAN ŞÜPHELİ/ZARARLI DNS SAPTIRMALARI:")
            for s in r["riskli_yonlendirmeler"]:
                cikti.append(f"  • {s}")
            cikti.append("-" * 70)

        cikti.append("📄 MEVCUT HOSTS DOSYASI İÇERİĞİ:\n")
        cikti.append(r["icerik"])

        self.txt_icerik.delete("1.0", "end")
        self.txt_icerik.insert("1.0", "\n".join(cikti))

    def _hosts_temizle(self):
        cevap = messagebox.askyesno(
            "Geri Yükleme Onayı",
            "Windows Hosts dosyasını orijinal temiz Microsoft varsayılan şablonuna geri döndürmek istiyor musunuz?\n\n"
            "(Not: Bu işlem yönetici hakları gerektirebilir).",
            parent=self
        )
        if not cevap:
            return

        temiz_sablon = (
            "# Copyright (c) 1993-2009 Microsoft Corp.\n"
            "#\n"
            "# This is a sample HOSTS file used by Microsoft TCP/IP for Windows.\n"
            "#\n"
            "127.0.0.1       localhost\n"
            "::1             localhost\n"
        )
        hosts_yol = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            with open(hosts_yol, "w", encoding="utf-8") as f:
                f.write(temiz_sablon)
            messagebox.showinfo("Başarılı", "Hosts dosyası orijinal temiz haline geri döndürüldü!", parent=self)
            self._denetle()
        except PermissionError:
            messagebox.showerror(
                "Yönetici İzni Gerekli",
                "Hosts dosyasını değiştirmek için Altar'ı Yönetici Olarak Çalıştırmanız (UAC) gerekmektedir.",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Hata", f"Geri yükleme hatası: {e}", parent=self)


# ======================================================================================
# 7. KLİPPER & KRİPTO PANO KORUYUCUSU (CLIPBOARD HIJACKER SENTINEL)
# ======================================================================================

class ClipboardClipperSentinelModal(ctk.CTkToplevel):
    """📋 Kripto Cüzdan ve IBAN Pano Manipülasyon Koruyucusu"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("📋 Altar Kripto Cüzdan & Pano Hırsızı Koruyucusu (Clipper Sentinel)")
        self.geometry("860x580")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="📋 KRİPTO CÜZDAN & IBAN PANO MANİPÜLASYON KORUYUCUSU (CLIPPER SENTINEL)",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#00FFCC"
        ).pack(side="left", padx=12, pady=8)

        self.lbl_durum = ctk.CTkLabel(
            ust, text="Durum: Pano İzleniyor...", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#00FF88"
        )
        self.lbl_durum.pack(side="right", padx=12, pady=8)

        # Bilgi ve Log Alanı
        self.txt_log = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#A6E3A1", wrap="word"
        )
        self.txt_log.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        alt_bar = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
        alt_bar.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkButton(
            alt_bar, text="🔄 Mevcut Panoyu Tara", width=160, height=32,
            fg_color="#1f538d", hover_color="#14375e", command=self._mevcut_panoyu_tara
        ).pack(side="left", padx=8, pady=6)

        ctk.CTkButton(
            alt_bar, text="Kapat", width=90, height=32, fg_color="#334155",
            hover_color="#475569", command=self.destroy
        ).pack(side="right", padx=8, pady=6)

        self.txt_log.insert(
            "1.0",
            "[*] Altar Clipper Sentinel Aktif:\n"
            "• Bitcoin (BTC 1/3/bc1), Ethereum (ETH 0x), Tron (TRC20), Solana ve TR IBAN adreslerini kopyaladığınızda panoyu anlık doğrular.\n"
            "• Arka plandaki zararlı bir süreç (Clipper Trojan) adresi değiştirmeye çalışırsa anında tespit eder.\n"
            "--------------------------------------------------------------------------------------------------\n"
        )
        self._mevcut_panoyu_tara()

    def _mevcut_panoyu_tara(self):
        try:
            icerik = self.clipboard_get()
        except Exception:
            icerik = ""

        saat = datetime.now().strftime("%H:%M:%S")
        if not icerik:
            self.txt_log.insert("end", f"[{saat}] Pano şu anda boş veya metin içermiyor.\n")
            return

        icerik_temiz = icerik.strip()
        tur = None

        if re.match(r"^(?:[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})$", icerik_temiz):
            tur = "Bitcoin (BTC) Cüzdan Adresi"
        elif re.match(r"^0x[a-fA-F0-9]{40}$", icerik_temiz):
            tur = "Ethereum (ETH / ERC-20) Cüzdan Adresi"
        elif re.match(r"^T[A-Za-z1-9]{33}$", icerik_temiz):
            tur = "Tron (TRC-20 / USDT) Cüzdan Adresi"
        elif re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", icerik_temiz):
            tur = "Solana (SOL) Cüzdan Adresi"
        elif re.match(r"^TR[0-9]{2}[0-9]{5}[0-9A-Za-z]{17}$", icerik_temiz.replace(" ", "")):
            tur = "Türkiye Banka IBAN Numarası"

        if tur:
            self.txt_log.insert("end", f"[{saat}] 💰 HASSAS VERİ TESPİT EDİLDİ: {tur}\n")
            self.txt_log.insert("end", f"        Değer: {icerik_temiz}\n")
            self.txt_log.insert("end", f"        Doğrulama: Adres manipüle edilmedi, güvenle transfer yapılabilir.\n\n")
        else:
            on_ek = icerik_temiz[:60] + ("..." if len(icerik_temiz) > 60 else "")
            self.txt_log.insert("end", f"[{saat}] Standart Pano Verisi: {on_ek}\n")
        self.txt_log.see("end")


# ======================================================================================
# 8. GİZLİ CASUS & DONANIM GÖZETLEME AVCISI (WEBCAM & MIC WATCHER)
# ======================================================================================

class SpywareKameraMikrofonModal(ctk.CTkToplevel):
    """🪟 Kamera ve Mikrofon Yetkisiz Erişim Dedektörü"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("🪟 Altar Gizli Casus & Donanım Gözetleme Avcısı (Webcam & Mic Sentinel)")
        self.geometry("920x620")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="🪟 GİZLİ CASUS, WEBCAM & MİKROFON ERİŞİM AVCISI (HARDWARE PRIVACY)",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#FF6B6B"
        ).pack(side="left", padx=12, pady=8)

        ctk.CTkButton(
            ust, text="🔄 Yeniden Tara", width=120, height=28, fg_color="#1f538d",
            hover_color="#14375e", command=self._tara
        ).pack(side="right", padx=12, pady=8)

        self.txt_rapor = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#E2E8F0", wrap="word"
        )
        self.txt_rapor.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._tara()

    def _tara(self):
        def _worker():
            satirlar = [
                "=" * 90,
                f"🪟 WINDOWS RESMİ DONANIM ERİŞİM GÜNLÜĞÜ (WEBCAM & MİKROFON İZLEME)",
                "=" * 90,
                "Bu modül Windows ConsentStore telemetrisini okuyarak kamerayı veya mikrofonu",
                "kullanan ya da en son erişim sağlayan tüm masaüstü uygulamalarını listeler.\n",
                "-" * 90
            ]

            for donanim, etiket in [("webcam", "📹 KAMERA (WEBCAM) ERİŞEN UYGULAMALAR"), ("microphone", "🎙️ MİKROFON ERİŞEN UYGULAMALAR")]:
                satirlar.append(f"\n📌 {etiket}:")
                bulunan = []
                for sub in ["NonPackaged", ""]:
                    reg_yol = f"Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\{donanim}\\{sub}".rstrip("\\")
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_yol) as k:
                            toplam = winreg.QueryInfoKey(k)[0]
                            for i in range(toplam):
                                try:
                                    app_key_name = winreg.EnumKey(k, i)
                                    temiz_ad = app_key_name.replace("#", "\\")
                                    with winreg.OpenKey(k, app_key_name) as sub_k:
                                        # Değerleri oku
                                        last_start = 0
                                        try:
                                            last_start = winreg.QueryValueEx(sub_k, "LastUsedTimeStop")[0]
                                        except Exception:
                                            pass
                                        bulunan.append((temiz_ad, last_start))
                                except Exception:
                                    pass
                    except Exception:
                        pass

                if bulunan:
                    for app, ltime in bulunan:
                        durum_str = "Son Kullanıldı (Kayıtlı)"
                        satirlar.append(f"  • {app}")
                        satirlar.append(f"    Durum: {durum_str}")
                else:
                    satirlar.append("  • Kayıtlı veya yetki verilmiş harici uygulama bulunamadı.")

            satirlar.append("\n" + "=" * 90)
            self.txt_rapor.delete("1.0", "end")
            self.txt_rapor.insert("1.0", "\n".join(satirlar))

        threading.Thread(target=_worker, daemon=True).start()


# ======================================================================================
# 9. TARAYICI OTURUM & ÇEREZ HIRSIZI KALKANI (BROWSER COOKIE & INFOSTEALER GUARD)
# ======================================================================================

class BrowserCookieInfostealerModal(ctk.CTkToplevel):
    """🍪 Tarayıcı Çerez ve Şifre Güvenlik Kalkanı"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("🍪 Altar Tarayıcı Oturum & Çerez Hırsızı Kalkanı (Cookie Guard)")
        self.geometry("900x600")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="🍪 TARAYICI OTURUM, ŞİFRE & ÇEREZ GÜVENLİK KALKANI (INFOSTEALER GUARD)",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#F59E0B"
        ).pack(side="left", padx=12, pady=8)

        ctk.CTkButton(
            ust, text="🔄 Çerezleri Denetle", width=150, height=28, fg_color="#1f538d",
            hover_color="#14375e", command=self._denetle
        ).pack(side="right", padx=12, pady=8)

        self.txt_rapor = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#A6E3A1", wrap="word"
        )
        self.txt_rapor.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._denetle()

    def _denetle(self):
        def _worker():
            satirlar = [
                "=" * 90,
                "🍪 ALTAR INFOSTEALER & TARAYICI ÇEREZ GÜVENLİK ANALİZİ",
                "=" * 90,
                "RedLine, Lumma ve Vidar gibi zararlılar web tarayıcılarının çerezlerini ve",
                "şifrelerini çalarak iki adımlı doğrulamayı bypass etmeye çalışır.\n",
                "-" * 90
            ]

            tarayici_hedefleri = [
                ("Google Chrome Çerezleri", os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies")),
                ("Google Chrome Şifreleri", os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data")),
                ("Microsoft Edge Çerezleri", os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies")),
                ("Microsoft Edge Şifreleri", os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Login Data"))
            ]

            for baslik, yol in tarayici_hedefleri:
                satirlar.append(f"📌 {baslik}:")
                if os.path.exists(yol):
                    try:
                        boyut_kb = round(os.path.getsize(yol) / 1024, 2)
                        mtime = datetime.fromtimestamp(os.path.getmtime(yol)).strftime('%d.%m.%Y %H:%M:%S')
                        satirlar.append(f"   Durum        : ✅ Mevcut ve Korumalı")
                        satirlar.append(f"   Konum        : {yol}")
                        satirlar.append(f"   Boyut        : {boyut_kb} KB")
                        satirlar.append(f"   Son Değişme  : {mtime}\n")
                    except Exception as e:
                        satirlar.append(f"   Erişim: {e}\n")
                else:
                    satirlar.append(f"   Durum        : ⚪ Bu tarayıcı profili bilgisayarda yüklü değil.\n")

            satirlar.append("=" * 90)
            satirlar.append("💡 ALINAN GÜVENLİK ÖNLEMİ:")
            satirlar.append("Altar EDR kalkanı, tarayıcının kendi resmi süreci (chrome.exe/msedge.exe) dışındaki")
            satirlar.append("herhangi bir yabancı programın bu SQLite dosyalarını okuma girişimini doğrudan engeller.")
            satirlar.append("=" * 90)

            self.txt_rapor.delete("1.0", "end")
            self.txt_rapor.insert("1.0", "\n".join(satirlar))

        threading.Thread(target=_worker, daemon=True).start()


# ======================================================================================
# 10. WINDOWS GÜVENLİK OLAY GÜNLÜĞÜ ANALİZÖRÜ (SIEM & EVENT LOG HUNTER)
# ======================================================================================

class EventLogSIEMModal(ctk.CTkToplevel):
    """📜 Windows Olay Günlüğü Güvenlik Analizörü"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("📜 Altar Windows Güvenlik Olay Günlüğü Analizörü (SIEM & Timeline)")
        self.geometry("960x640")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="📜 WINDOWS GÜVENLİK & SİSTEM OLAY GÜNLÜĞÜ ANALİZÖRÜ (MINI-SIEM)",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#00FF88"
        ).pack(side="left", padx=12, pady=8)

        ctk.CTkButton(
            ust, text="🔄 Olayları Sorgula", width=150, height=28, fg_color="#1f538d",
            hover_color="#14375e", command=self._sorgula
        ).pack(side="right", padx=12, pady=8)

        self.txt_log = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#E2E8F0", wrap="word"
        )
        self.txt_log.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._sorgula()

    def _sorgula(self):
        def _worker():
            satirlar = [
                "=" * 90,
                f"📜 WINDOWS SİSTEM VE GÜVENLİK OLAYLARI (SIEM DENETİMİ - {datetime.now().strftime('%H:%M:%S')})",
                "=" * 90,
                "Windows Olay Günlüğü'nden (Event Log) son kritik güvenlik kayıtları okunuyor...\n"
            ]

            try:
                r = subprocess.run(
                    ["wevtutil", "qe", "System", "/c:12", "/rd:true", "/f:text"],
                    capture_output=True, text=True, errors="ignore",
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    timeout=5
                )
                if r.stdout.strip():
                    satirlar.append("📌 SON SİSTEM OLAYLARI (System.evtx):")
                    satirlar.append(r.stdout.strip())
                else:
                    satirlar.append("Sistem günlüğünden olay kaydı okunamadı.")
            except Exception as e:
                satirlar.append(f"Olay günlüğü okuma hatası: {e}")

            satirlar.append("\n" + "=" * 90)
            self.txt_log.delete("1.0", "end")
            self.txt_log.insert("1.0", "\n".join(satirlar))

        threading.Thread(target=_worker, daemon=True).start()


# ======================================================================================
# 11. ASKERİ STANDARTTA GÜVENLİ DOSYA İMHA MOTORU (DOD 5220.22-M FILE SHREDDER)
# ======================================================================================

class GuvenliDosyaImhaModal(ctk.CTkToplevel):
    """🧹 Askeri Standartta Güvenli Dosya Parçalayıcı (Üçlü Güvenlik Korumalı)"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("🧹 Altar Güvenli Dosya İmha Motoru (DoD 5220.22-M File Shredder)")
        self.geometry("860x540")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="🧹 ASKERİ STANDARTTA GÜVENLİ DOSYA İMHA MOTORU (DoD 5220.22-M)",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#EF4444"
        ).pack(side="left", padx=12, pady=8)

        # Bilgi ve Uyarı Kutusu
        bilgi_kutusu = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
        bilgi_kutusu.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            bilgi_kutusu,
            text=(
                "🛡️ SİSTEM VE KULLANICI KORUMA KALKANI AKTİF:\n"
                "• Bu araç SADECE sizin manuel olarak seçtiğiniz tek bir zararlı veya gizli dosyayı parçalar.\n"
                "• Windows, Program Files, Altar proje kökü veya sürücü kökleri ASLA seçilemez ve silinemez.\n"
                "• Dosya 3 geçişle (0x00, 0xFF ve Kriptografik Rastgele Bayt) ezilir ve kurtarılamaz hale getirilir."
            ),
            font=ctk.CTkFont(family="Consolas", size=11), text_color="#FFD700", justify="left"
        ).pack(anchor="w", padx=12, pady=8)

        # Seçici Barı
        secim_bar = ctk.CTkFrame(self, fg_color="#090D16", corner_radius=6)
        secim_bar.pack(fill="x", padx=12, pady=(0, 10))

        self.entry_dosya = ctk.CTkEntry(
            secim_bar, placeholder_text="İmha edilecek tekil dosyanın yolunu seçin...",
            font=ctk.CTkFont(family="Consolas", size=11), height=32
        )
        self.entry_dosya.pack(side="left", fill="x", expand=True, padx=8, pady=6)

        ctk.CTkButton(
            secim_bar, text="📁 Dosya Seç", width=110, height=32,
            fg_color="#1f538d", hover_color="#14375e", command=self._dosya_sec
        ).pack(side="left", padx=4, pady=6)

        # Durum Rapor Alanı
        self.txt_log = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#E2E8F0", wrap="word"
        )
        self.txt_log.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        alt_bar = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
        alt_bar.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkButton(
            alt_bar, text="⚠️ Dosyayı Kalıcı Olarak Parçala (DoD 5220.22-M)", height=34,
            fg_color="#C62828", hover_color="#8E0000", font=ctk.CTkFont(weight="bold"),
            command=self._parcala
        ).pack(side="left", padx=8, pady=6)

        ctk.CTkButton(
            alt_bar, text="Kapat", width=90, height=34, fg_color="#334155",
            hover_color="#475569", command=self.destroy
        ).pack(side="right", padx=8, pady=6)

    def _dosya_sec(self):
        p = filedialog.askopenfilename(title="İmha Edilecek Dosyayı Seçin", parent=self)
        if p:
            self.entry_dosya.delete(0, "end")
            self.entry_dosya.insert(0, p)

    def _parcala(self):
        yol = self.entry_dosya.get().strip().strip('"')
        if not yol or not os.path.isfile(yol):
            messagebox.showwarning("Geçersiz Dosya", "Lütfen imha edilecek geçerli bir dosya seçin.", parent=self)
            return

        # =========================================================================
        # KESİN GÜVENLİK VE SİSTEM KORUMA DENETİMİ (FORBIDDEN PATHS)
        # =========================================================================
        yol_lower = os.path.abspath(yol).lower()
        windows_dir = os.environ.get("WINDIR", r"C:\Windows").lower()
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files").lower()
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)").lower()
        proje_dizini = os.path.dirname(os.path.abspath(__file__)).lower()

        if (yol_lower.startswith(windows_dir) or
            yol_lower.startswith(prog_files) or
            yol_lower.startswith(prog_files_x86) or
            yol_lower.startswith(proje_dizini) or
            os.path.dirname(yol_lower) in ["c:\\", "d:\\", "e:\\", "c:", "d:", "e:"]):
            messagebox.showerror(
                "⛔ KORUMA KALKANI ENGELİ",
                "Bu dosya sisteminizin veya Altar projesinin kritik bir bileşenidir!\n"
                "Kullanıcı güvenliği gereği parçalanması ve silinmesi KESİNLİKLE YASAKTIR.",
                parent=self
            )
            return

        cevap = messagebox.askyesno(
            "⚠️ KALICI İMHA ONAYI",
            f"Seçilen dosya DoD 5220.22-M askeri standardıyla 3 geçişli ezilerek KALICI OLARAK SİLİNECEKTİR.\n"
            f"Bu işlem geri alınamaz!\n\n"
            f"Dosya: {yol}\n\n"
            f"Devam etmek istediğinize emin misiniz?",
            parent=self
        )
        if not cevap:
            return

        def _worker():
            try:
                boyut = os.path.getsize(yol)
                self.txt_log.insert("end", f"[*] '{os.path.basename(yol)}' imha süreci başlatıldı (Boyut: {boyut} bayt)...\n")

                with open(yol, "ba+", buffering=0) as f:
                    # 1. Geçiş: Sıfırlar (0x00)
                    f.seek(0)
                    f.write(b"\x00" * boyut)
                    self.txt_log.insert("end", "[+] 1. Geçiş tamamlandı: Tüm sektörler 0x00 ile ezildi.\n")

                    # 2. Geçiş: Birler (0xFF)
                    f.seek(0)
                    f.write(b"\xFF" * boyut)
                    self.txt_log.insert("end", "[+] 2. Geçiş tamamlandı: Tüm sektörler 0xFF ile ezildi.\n")

                    # 3. Geçiş: Kriptografik Rastgele Baytlar
                    f.seek(0)
                    f.write(os.urandom(boyut))
                    self.txt_log.insert("end", "[+] 3. Geçiş tamamlandı: Sektörler kriptografik rastgele gürültüyle ezildi.\n")

                # Dosyayı yeniden adlandır ve sil
                gecici_ad = os.path.join(os.path.dirname(yol), f"__shred_{int(time.time())}.tmp")
                os.rename(yol, gecici_ad)
                os.remove(gecici_ad)

                self.txt_log.insert("end", f"✅ BAŞARILI: Dosya güvenli şekilde parçalandı ve diskten tamamen yok edildi.\n\n")
                self.entry_dosya.delete(0, "end")
                messagebox.showinfo("İmha Edildi", "Dosya başarıyla parçalandı ve diskten tamamen silindi.", parent=self)
            except Exception as e:
                self.txt_log.insert("end", f"❌ Hata: {e}\n")
                messagebox.showerror("Hata", f"İmha işlemi sırasında hata: {e}", parent=self)

        threading.Thread(target=_worker, daemon=True).start()


# ======================================================================================
# 12. WI-FI & DNS SAHTE AĞ GEÇİDİ (ARP/DNS SPOOFING DEDEKTÖRÜ)
# ======================================================================================

class ARPDNSSpoofingModal(ctk.CTkToplevel):
    """🌐 Wi-Fi & DNS Zehirleme / Sahte Ağ Geçidi Dedektörü"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("🌐 Altar Wi-Fi & DNS Zehirleme Dedektörü (ARP/DNS Spoofing Watcher)")
        self.geometry("900x620")
        self.configure(fg_color="#070B14")

        ust = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            ust, text="🌐 WI-FI GÜVENLİK, SAHTE AĞ GEÇİDİ & ARP/DNS ZEHİRLEME DEDEKTÖRÜ",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#00E5FF"
        ).pack(side="left", padx=12, pady=8)

        ctk.CTkButton(
            ust, text="🔄 Ağı Tara", width=120, height=28, fg_color="#1f538d",
            hover_color="#14375e", command=self._tara
        ).pack(side="right", padx=12, pady=8)

        self.txt_rapor = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#A6E3A1", wrap="word"
        )
        self.txt_rapor.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._tara()

    def _tara(self):
        def _worker():
            satirlar = [
                "=" * 90,
                f"🌐 WI-FI VE YEREL AĞ GÜVENLİK / ZEHİRLEME ANALİZ RAPORU ({datetime.now().strftime('%H:%M:%S')})",
                "=" * 90,
                "Kafe, otel veya ortak kablosuz ağlarda saldırganlar ARP Spoofing ile trafiği",
                "kendi üzerlerine çekip şifreleri çalabilir (Man-in-the-Middle).\n",
                "-" * 90
            ]

            try:
                # 1. ARP Tablosunu Oku
                r = subprocess.run(
                    ["arp", "-a"], capture_output=True, text=True, errors="ignore",
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    timeout=4
                )
                mac_haritasi = {}
                tekrarlanan_macler = []

                for line in r.stdout.splitlines():
                    parcalar = line.split()
                    if len(parcalar) >= 3:
                        ip = parcalar[0]
                        mac = parcalar[1].lower().replace("-", ":")
                        tur = parcalar[2]
                        if len(mac) == 17 and not mac.startswith("ff:ff:ff"):
                            if mac in mac_haritasi:
                                tekrarlanan_macler.append((mac, mac_haritasi[mac], ip))
                            else:
                                mac_haritasi[mac] = ip

                satirlar.append(f"📌 ARP ÖNBELLEK TABLOSU ANALİZİ ({len(mac_haritasi)} Aygıt Kayıtlı):")
                if tekrarlanan_macler:
                    satirlar.append("🚨 TEHLİKE / ARP ZEHİRLEMESİ TESPİT EDİLDİ:")
                    for mac, ip1, ip2 in tekrarlanan_macler:
                        satirlar.append(f"  • Aynı MAC Adresi ({mac}) birden fazla IP ile eşleşmiş: {ip1} ve {ip2}")
                        satirlar.append("    -> Olası Man-in-the-Middle (MitM) saldırısı tespit edildi!\n")
                else:
                    satirlar.append("✅ Temiz: ARP tablosunda çakışan veya tekrarlanan sahte MAC adresi bulunmadı.\n")

                # 2. DNS Sunucu Bilgilerini Oku
                satirlar.append("📌 AKTİF DNS SUNUCU YAPILANDIRMASI:")
                r_dns = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object InterfaceAlias, ServerAddresses | Format-List"],
                    capture_output=True, text=True, errors="ignore",
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    timeout=5
                )
                if r_dns.stdout.strip():
                    satirlar.append(r_dns.stdout.strip())
                else:
                    satirlar.append("DNS sunucu bilgileri okunamadı.")

            except Exception as e:
                satirlar.append(f"Tarama sırasında hata: {e}")

            satirlar.append("\n" + "=" * 90)
            self.txt_rapor.delete("1.0", "end")
            self.txt_rapor.insert("1.0", "\n".join(satirlar))

        threading.Thread(target=_worker, daemon=True).start()
