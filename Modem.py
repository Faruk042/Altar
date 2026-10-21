import subprocess
import os
import sys
import ctypes
import ipaddress
import re
import time
import threading
import shlex
import tempfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor

try:
    import psutil
    PSUTIL_VAR = True
except ImportError:
    PSUTIL_VAR = False

try:
    import customtkinter as ctk
    from tkinter import messagebox
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() if os.name == 'nt' else os.geteuid() == 0
    except Exception:
        return False


def _sessiz_komut_calistir(komut_listesi):
    """Birden fazla sistem komutunu konsol penceresi açmadan, kabuksuz (shell=False) ve güvenle çalıştırır."""
    for komut_str in komut_listesi:
        try:
            parcalar = shlex.split(komut_str)
            subprocess.run(
                parcalar, shell=False,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=_NO_WINDOW
            )
        except Exception:
            pass


def ps_calistir(ps_kod, cikti_yakala=False):
    """PowerShell kodlarını geçici izole dosya üzerinden güvenli, penceresiz ve UTF-8 uyumlu çalıştırır."""
    dosya_adi = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8-sig", suffix=".ps1", delete=False) as f:
            dosya_adi = f.name
            f.write(ps_kod)

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        if cikti_yakala:
            sonuc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", dosya_adi],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                startupinfo=startupinfo, creationflags=_NO_WINDOW
            )
            return sonuc.stdout.strip()
        else:
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", dosya_adi],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                startupinfo=startupinfo, creationflags=_NO_WINDOW
            )
            return ""
    finally:
        if dosya_adi and os.path.exists(dosya_adi):
            try:
                os.remove(dosya_adi)
            except Exception:
                pass


def bant_genisligi_optimize_et(log_callback=None):
    """Bağlı cihazlara maksimum internet hızı sağlamak için Windows ağ ve adaptör kısıtlamalarını kaldırır."""
    msg = "[TURBO] Bağlı cihazlar için maksimum bant genişliği ve QoS ayarları uygulanıyor..."
    print(f"\n{msg}")
    if log_callback:
        log_callback(msg)

    _sessiz_komut_calistir([
        "netsh int tcp set global autotuninglevel=normal",
        "netsh int tcp set global rss=enabled",
        "netsh int tcp set global rsc=disabled",
        "netsh int tcp set global ecncapability=disabled",
        "powercfg -setacvalueindex SCHEME_CURRENT 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 12bbebe6-58d6-4636-95bb-3217ef867c1a 0",
        "powercfg -setdcvalueindex SCHEME_CURRENT 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 12bbebe6-58d6-4636-95bb-3217ef867c1a 0",
        "powercfg -setactive SCHEME_CURRENT"
    ])

    ps_optimize = """
    $psched = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\Psched"
    if (-not (Test-Path $psched)) { New-Item -Path $psched -Force | Out-Null }
    Set-ItemProperty -Path $psched -Name "NonBestEffortLimit" -Value 0 -Type DWord -ErrorAction SilentlyContinue

    $mmcss = "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile"
    if (Test-Path $mmcss) {
        Set-ItemProperty -Path $mmcss -Name "NetworkThrottlingIndex" -Value 0xffffffff -Type DWord -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $mmcss -Name "SystemResponsiveness" -Value 0 -Type DWord -ErrorAction SilentlyContinue
    }

    Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | ForEach-Object {
        Disable-NetAdapterRsc -Name $_.Name -ErrorAction SilentlyContinue
        Disable-NetAdapterPowerManagement -Name $_.Name -ErrorAction SilentlyContinue
        Disable-NetAdapterLso -Name $_.Name -ErrorAction SilentlyContinue
        Enable-NetAdapterBinding -Name $_.Name -ComponentID "ms_pacer" -ErrorAction SilentlyContinue
    }

    Stop-Service -Name "DoSvc" -Force -ErrorAction SilentlyContinue

    $svchost = Get-CimInstance Win32_Service -Filter "Name='SharedAccess'"
    if ($svchost -and $svchost.ProcessId -gt 0) {
        $proc = Get-Process -Id $svchost.ProcessId -ErrorAction SilentlyContinue
        if ($proc) { $proc.PriorityClass = "High" }
    }

    Write-Output "[BAŞARILI] Tüm bant genişliği kısıtlamaları kaldırıldı ve QoS motoru hazırlandı!"
    """
    cikti = ps_calistir(ps_optimize, cikti_yakala=True)
    if log_callback and cikti:
        log_callback(cikti)


def hotspot_baslat(ssid, password, bant_secimi="oto", log_callback=None):
    """Mevcut internet bağlantısını kullanarak bilgisayarı yüksek hızlı modem gibi yapılandırır."""
    if len(password) < 8:
        uyari = "[HATA] Hotspot şifresi en az 8 karakter olmalıdır!"
        print(uyari)
        if log_callback:
            log_callback(uyari)
        return

    _sessiz_komut_calistir(["ipconfig /flushdns"])
    bant_genisligi_optimize_et(log_callback=log_callback)

    guvenli_ssid = ssid.replace("'", "''")
    guvenli_sifre = password.replace("'", "''")
    guvenli_bant = bant_secimi.replace("'", "''")

    ps_kod = f"""
    Set-Service -Name "SharedAccess" -StartupType Automatic -ErrorAction SilentlyContinue
    Restart-Service -Name "SharedAccess" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1

    $ConnectionProfile = [Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType=WindowsRuntime]::GetInternetConnectionProfile()
    if (-not $ConnectionProfile) {{ Write-Output "[HATA] Aktif bir internet bağlantısı bulunamadı!"; exit }}

    $TetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows.Networking.NetworkOperators, ContentType=WindowsRuntime]::CreateFromConnectionProfile($ConnectionProfile)

    $Config = $TetheringManager.GetCurrentAccessPointConfiguration()
    $Config.Ssid = '{guvenli_ssid}'
    $Config.Passphrase = '{guvenli_sifre}'

    $SecilenBant = '{guvenli_bant}'
    try {{
        if ($SecilenBant -eq "5" -or $SecilenBant -eq "oto") {{
            if ($Config.IsBandSupported(2)) {{
                $Config.Band = 2
                Write-Output "[HIZ OPTİMİZASYONU] 5 GHz Yüksek Hız Bandı aktif edildi!"
            }} else {{
                $Config.Band = 1
                Write-Output "[BİLGİ] Adaptörünüz 5 GHz desteklemiyor, 2.4 GHz bandı kullanılıyor."
            }}
        }} elseif ($SecilenBant -eq "2.4") {{
            $Config.Band = 1
            Write-Output "[BİLGİ] 2.4 GHz (Geniş Kapsama) bandı seçildi."
        }}
    }} catch {{
        Write-Output "[BİLGİ] Bant seçimi varsayılan olarak bırakıldı."
    }}

    $ConfigAction = $TetheringManager.ConfigureAccessPointAsync($Config)
    while ($ConfigAction.Status -eq 0) {{ Start-Sleep -Milliseconds 80 }}

    $StartAction = $TetheringManager.StartTetheringAsync()
    while ($StartAction.Status -eq 0) {{ Start-Sleep -Milliseconds 80 }}

    Get-NetAdapter | Where-Object {{$_.InterfaceDescription -match "Direct" -or $_.Name -match "Yerel|Local"}} | ForEach-Object {{
        Disable-NetAdapterRsc -Name $_.Name -ErrorAction SilentlyContinue
        Disable-NetAdapterPowerManagement -Name $_.Name -ErrorAction SilentlyContinue
        Enable-NetAdapterBinding -Name $_.Name -ComponentID "ms_pacer" -ErrorAction SilentlyContinue
    }}

    Write-Output "[BAŞARILI] Bilgisayarınız artık tam kapasiteli bir modem! Ağ Adı: '{guvenli_ssid}'"
    """
    cikti = ps_calistir(ps_kod, cikti_yakala=True)
    print(cikti)
    if log_callback and cikti:
        log_callback(cikti)


def hotspot_durdur(log_callback=None):
    """Modem (Hotspot) işlevini durdurur."""
    ps_kod = """
    $ConnectionProfile = [Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType=WindowsRuntime]::GetInternetConnectionProfile()
    if ($ConnectionProfile) {
        $TetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows.Networking.NetworkOperators, ContentType=WindowsRuntime]::CreateFromConnectionProfile($ConnectionProfile)
        $StopAction = $TetheringManager.StopTetheringAsync()
        while ($StopAction.Status -eq 0) { Start-Sleep -Milliseconds 80 }
        Write-Output "[BAŞARILI] Hotspot ve internet paylaşımı kapatıldı."
    } else {
        Write-Output "[BİLGİ] Kapatılacak aktif bir paylaşım bulunamadı."
    }
    """
    cikti = ps_calistir(ps_kod, cikti_yakala=True)
    print(cikti)
    if log_callback and cikti:
        log_callback(cikti)


def cihaz_turu_tahmin_et(hostname, mac):
    hostname_lower = hostname.lower()
    telefon_anahtar = ['iphone', 'android', 'galaxy', 'redmi', 'huawei', 'oppo', 'vivo', 'poco', 'ipad', 'mi', 'tab']
    pc_anahtar = ['desktop', 'laptop', 'pc', 'windows', 'macbook']

    if any(kelime in hostname_lower for kelime in telefon_anahtar):
        return "Telefon / Tablet"
    elif any(kelime in hostname_lower for kelime in pc_anahtar):
        return "Bilgisayar"

    mac_temiz = mac.replace(":", "").replace("-", "").strip()
    if len(mac_temiz) >= 2 and mac_temiz[1].upper() in ['2', '6', 'A', 'E']:
        return "Mobil Cihaz (Gizli MAC)"
    return "Bilinmeyen Cihaz"


def bagli_cihazlari_getir():
    """Bağlı cihazların MAC, IP (ARP tablosundan) ve Hostname bilgilerini döndürür."""
    ps_kod = """
    $ConnectionProfile = [Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType=WindowsRuntime]::GetInternetConnectionProfile()
    if (-not $ConnectionProfile) { Write-Output "HATA_INTERNET"; exit }
    $TetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows.Networking.NetworkOperators, ContentType=WindowsRuntime]::CreateFromConnectionProfile($ConnectionProfile)
    if ($TetheringManager.TetheringOperationalState -ne 1) { Write-Output "HATA_KAPALI"; exit }

    $Clients = $TetheringManager.GetTetheringClients()
    if ($Clients.Count -eq 0) { Write-Output "BOS"; exit }

    $Neighbors = Get-NetNeighbor -AddressFamily IPv4 -ErrorAction SilentlyContinue

    foreach ($client in $Clients) {
        $mac = $client.MacAddress
        $cleanMac = ($mac -replace '[:\\-]', '').ToUpper()
        $hostnames = ($client.HostNames | ForEach-Object { $_.RawName }) -join ", "
        if (-not $hostnames) { $hostnames = "İsimsiz Cihaz" }

        $ip = "IP Bekleniyor"
        if ($Neighbors) {
            $eslesen = $Neighbors | Where-Object { ($_.LinkLayerAddress -replace '[:\\-]', '').ToUpper() -eq $cleanMac -and $_.IPAddress -notmatch '^169\\.254' } | Select-Object -First 1
            if ($eslesen) { $ip = $eslesen.IPAddress }
        }
        Write-Output "$mac|$ip|$hostnames"
    }
    """
    cikti = ps_calistir(ps_kod, cikti_yakala=True)
    satirlar = [s.strip() for s in cikti.split('\n') if s.strip()]

    if "HATA_INTERNET" in satirlar:
        return "HATA_INTERNET", []
    if "HATA_KAPALI" in satirlar:
        return "HATA_KAPALI", []
    if "BOS" in satirlar or not satirlar:
        return "BOS", []

    cihaz_listesi = []
    for satir in satirlar:
        if "|" in satir:
            parcalar = satir.split("|")
            if len(parcalar) >= 3:
                mac, ip, hostname = parcalar[0].strip(), parcalar[1].strip(), parcalar[2].strip()
                cihaz_listesi.append({
                    "mac": mac,
                    "ip": ip,
                    "hostname": hostname,
                    "tur": cihaz_turu_tahmin_et(hostname, mac)
                })
    return "TAMAM", cihaz_listesi


def aktif_qos_kurallarini_getir():
    """Altar tarafından oluşturulmuş aktif QoS ve hız sınırı kurallarını sözlük olarak döndürür."""
    ps_kod = """
    Get-NetQosPolicy -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "Altar_QoS_*" } | ForEach-Object {
        $ip = $_.IPDstPrefixMatchCondition
        if (-not $ip) { $ip = $_.IPSrcPrefixMatchCondition }
        $hiz = $_.ThrottleRateActionBitsPerSecond
        $dscp = $_.DSCPAction
        Write-Output "$($_.Name)|$ip|$hiz|$dscp"
    }
    """
    cikti = ps_calistir(ps_kod, cikti_yakala=True)
    kurallar = {}
    for satir in cikti.split('\n'):
        if "|" in satir:
            isim, ip_prefix, hiz, dscp = [x.strip() for x in satir.split("|", 3)]
            temiz_ip = ip_prefix.replace("/32", "")
            aciklama = []
            if dscp == "46":
                aciklama.append("VIP Öncelik")
            elif dscp == "8":
                aciklama.append("Düşük Öncelik")
            if hiz and hiz != "0":
                try:
                    mbps = float(hiz) / 1_000_000
                    aciklama.append(f"Limit: {mbps:.1f} Mbps")
                except Exception:
                    aciklama.append(f"Limit: {hiz} bps")
            kurallar[temiz_ip] = {
                "isim": isim,
                "ip": temiz_ip,
                "detay": " + ".join(aciklama) if aciklama else "Standart Kural"
            }
    return kurallar


def cihazlari_listele(log_callback=None):
    if log_callback:
        log_callback("[BİLGİ] Hotspot'a bağlı cihazlar ve IP/QoS durumları paralel taranıyor...")

    # İki PowerShell sorgusunu aynı anda paralel çalıştırarak bekleme süresini %50 azaltır
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_cihaz = ex.submit(bagli_cihazlari_getir)
        f_qos = ex.submit(aktif_qos_kurallarini_getir)
        durum, cihazlar = f_cihaz.result()
        kurallar = f_qos.result()

    if durum == "HATA_KAPALI":
        msg = "[UYARI] Hotspot şu anda kapalı."
        print(msg)
        if log_callback:
            log_callback(msg)
        return
    elif durum == "BOS":
        msg = "[BİLGİ] Hotspot ağınıza bağlı hiçbir cihaz yok."
        print(msg)
        if log_callback:
            log_callback(msg)
        return
    elif durum == "HATA_INTERNET":
        msg = "[HATA] Aktif internet bağlantısı bulunamadı."
        print(msg)
        if log_callback:
            log_callback(msg)
        return

    rapor = [f"--- BAĞLI CİHAZLAR ({len(cihazlar)} Adet) ---"]
    for i, c in enumerate(cihazlar, 1):
        kural_bilgisi = kurallar.get(c["ip"], {}).get("detay", "Sınırsız / Normal")
        rapor.append(f"[{i}] {c['hostname']} | IP: {c['ip']} | MAC: {c['mac']} | Tür: {c['tur']} | QoS: {kural_bilgisi}")

    tam_metin = "\n".join(rapor)
    print(tam_metin)
    if log_callback:
        log_callback(tam_metin)


def mac_adresinden_ip_bul(mac_girdi):
    temiz_mac = re.sub(r"[^0-9A-F]", "", mac_girdi.upper())
    if len(temiz_mac) != 12:
        return ""
    ps_kod = f"""
    $n = Get-NetNeighbor -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {{ ($_.LinkLayerAddress -replace '[:\\-]', '').ToUpper() -eq '{temiz_mac}' -and $_.IPAddress -notmatch '^169\\.254' }} | Select-Object -First 1
    if ($n) {{ Write-Output $n.IPAddress }}
    """
    return ps_calistir(ps_kod, cikti_yakala=True)


def qos_kural_uygula(hedef_ip, mod, mbps_sinir=0.0, log_callback=None):
    """Belirtilen IP adresine Windows NetQos üzerinden öncelik veya hız sınırı uygular."""
    if ":" in hedef_ip or "-" in hedef_ip:
        cozulen = mac_adresinden_ip_bul(hedef_ip)
        if not cozulen:
            if log_callback:
                log_callback(f"[HATA] {hedef_ip} MAC adresine ait IP ARP tablosunda bulunamadı!")
            return
        hedef_ip = cozulen

    try:
        hedef_ip = str(ipaddress.ip_address(hedef_ip.strip()))
    except ValueError:
        if log_callback:
            log_callback(f"[HATA] Geçersiz IP adresi formatı: {hedef_ip}")
        return

    ip_kod = hedef_ip.replace(".", "_")
    kural_down = f"Altar_QoS_Down_{ip_kod}"
    kural_up = f"Altar_QoS_Up_{ip_kod}"

    parametreler = []
    if mod == "vip":
        parametreler.append("-DSCPAction 46")
    elif mod == "dusuk":
        parametreler.append("-DSCPAction 8")

    if mbps_sinir > 0:
        bps = int(mbps_sinir * 1_000_000)
        parametreler.append(f"-ThrottleRateActionBitsPerSecond {bps}")

    ek_param = " ".join(parametreler)

    ps_kod = f"""
    Remove-NetQosPolicy -Name "{kural_down}" -Confirm:$false -ErrorAction SilentlyContinue
    Remove-NetQosPolicy -Name "{kural_up}" -Confirm:$false -ErrorAction SilentlyContinue
    New-NetQosPolicy -Name "{kural_down}" -IPDstPrefixMatchCondition "{hedef_ip}/32" -NetworkProfile All {ek_param} -ErrorAction SilentlyContinue | Out-Null
    New-NetQosPolicy -Name "{kural_up}" -IPSrcPrefixMatchCondition "{hedef_ip}/32" -NetworkProfile All {ek_param} -ErrorAction SilentlyContinue | Out-Null
    Write-Output "[BAŞARILI] {hedef_ip} için QoS ({mod.upper()}, Limit: {mbps_sinir} Mbps) devreye alındı!"
    """
    cikti = ps_calistir(ps_kod, cikti_yakala=True)
    print(cikti)
    if log_callback and cikti:
        log_callback(cikti)


def tum_qos_kurallarini_sifirla(log_callback=None):
    ps_calistir('Remove-NetQosPolicy -Name "Altar_QoS_*" -Confirm:$false -ErrorAction SilentlyContinue')
    msg = "[BAŞARILI] Tüm cihazların hız sınırları ve QoS öncelik kuralları sıfırlandı!"
    print(msg)
    if log_callback:
        log_callback(msg)


def kapsamli_ag_onarimi(log_callback=None):
    if log_callback:
        log_callback("[*] Windows Ağ, DNS, QoS ve ICS servisleri derinlemesine onarılıyor...")

    _sessiz_komut_calistir([
        "ipconfig /flushdns",
        "netsh winsock reset",
        "netsh int ip reset"
    ])

    ps_kod = """
    Remove-NetQosPolicy -Name "Altar_QoS_*" -Confirm:$false -ErrorAction SilentlyContinue
    Restart-Service -Name "SharedAccess" -Force -ErrorAction SilentlyContinue
    Restart-Service -Name "WlanSvc" -Force -ErrorAction SilentlyContinue
    Write-Output "[BAŞARILI] DNS, Winsock, QoS ve Hotspot servisleri onarıldı!"
    """
    cikti = ps_calistir(ps_kod, cikti_yakala=True)
    if log_callback and cikti:
        log_callback(cikti)


# =========================================================================
# ALTAR KAZINAN VERİ & ANALİZ MERKEZİ ALT 1. BÖLÜM: MODEM & HOTSPOT PANELİ
# =========================================================================
if CTK_AVAILABLE:
    class ModemHotspotPaneli(ctk.CTkFrame):
        """
        Bilgisayarı tam kapasiteli bir Modem / Hotspot ve QoS Yöneticisi olarak
        kullanmayı sağlayan 1. Bölüm Arayüz Paneli.
        """
        def __init__(self, parent):
            super().__init__(parent, fg_color="#0B1320", corner_radius=8, border_width=1, border_color="#1E293B")
            self.trafik_izleme_aktif = False
            self._islem_aktif = False
            self._son_hiz_metni = ""
            self._log_tamponu = deque(maxlen=150)
            self._arayuz_olustur()
            self.after(200, self._toplu_log_guncelle)

        def _arayuz_olustur(self):
            ust = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
            ust.pack(side="top", fill="x", padx=6, pady=4)

            ctk.CTkLabel(
                ust, text="📡 1. BÖLÜM: TURBO MODEM (HOTSPOT) & QoS HIZ YÖNETİCİSİ",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#00FFCC"
            ).pack(side="left", padx=8, pady=3)

            self.lbl_canli_hiz = ctk.CTkLabel(
                ust, text="⬇️ 0.0 KB/s | ⬆️ 0.0 KB/s",
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#FFD700"
            )
            self.lbl_canli_hiz.pack(side="right", padx=8, pady=3)

            # 1. Satır: SSID, Şifre, Bant ve Başlat/Durdur Butonları
            ayar_bar = ctk.CTkFrame(self, fg_color="transparent")
            ayar_bar.pack(side="top", fill="x", padx=6, pady=2)

            ctk.CTkLabel(ayar_bar, text="Ağ Adı:", font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
            self.entry_ssid = ctk.CTkEntry(ayar_bar, width=100, height=24, font=ctk.CTkFont(size=11))
            self.entry_ssid.pack(side="left", padx=2)
            self.entry_ssid.insert(0, "Altar_Turbo_Net")

            ctk.CTkLabel(ayar_bar, text="Şifre:", font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
            self.entry_sifre = ctk.CTkEntry(ayar_bar, width=90, height=24, font=ctk.CTkFont(size=11))
            self.entry_sifre.pack(side="left", padx=2)
            self.entry_sifre.insert(0, "Altar12345")

            self.bant_var = ctk.StringVar(value="oto")
            self.combo_bant = ctk.CTkOptionMenu(
                ayar_bar, variable=self.bant_var, values=["oto", "5", "2.4"], width=64, height=24, font=ctk.CTkFont(size=11)
            )
            self.combo_bant.pack(side="left", padx=2)

            ctk.CTkButton(
                ayar_bar, text="🚀 Modem Başlat", width=102, height=24, font=ctk.CTkFont(size=11),
                fg_color="#00A86B", hover_color="#007F50", command=self.modem_baslat_tetikle
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                ayar_bar, text="⏹️ Durdur", width=72, height=24, font=ctk.CTkFont(size=11),
                fg_color="#8B0000", hover_color="#5c0000", command=self.modem_durdur_tetikle
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                ayar_bar, text="⚡ Turbo", width=66, height=24, font=ctk.CTkFont(size=11),
                fg_color="#B85C00", command=lambda: self._gorev_baslat(bant_genisligi_optimize_et, self.log_yaz)
            ).pack(side="left", padx=2)

            # 2. Satır: Bağlı Cihaz Analizi, QoS Hız Limiti ve Ağ Onarımı
            qos_bar = ctk.CTkFrame(self, fg_color="transparent")
            qos_bar.pack(side="top", fill="x", padx=6, pady=2)

            ctk.CTkButton(
                qos_bar, text="📱 Cihazları Listele", width=104, height=24, font=ctk.CTkFont(size=11),
                fg_color="#1f538d", command=lambda: self._gorev_baslat(cihazlari_listele, self.log_yaz)
            ).pack(side="left", padx=(0, 2))

            self.entry_qos_hedef = ctk.CTkEntry(
                qos_bar, placeholder_text="Hedef IP/MAC", width=92, height=24, font=ctk.CTkFont(size=11)
            )
            self.entry_qos_hedef.pack(side="left", padx=1)

            self.qos_mod_var = ctk.StringVar(value="vip")
            ctk.CTkOptionMenu(
                qos_bar, variable=self.qos_mod_var, values=["vip", "dusuk", "normal"], width=68, height=24, font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=1)

            self.entry_qos_mbps = ctk.CTkEntry(
                qos_bar, placeholder_text="Mbps (0=Sınırsız)", width=76, height=24, font=ctk.CTkFont(size=11)
            )
            self.entry_qos_mbps.pack(side="left", padx=1)

            ctk.CTkButton(
                qos_bar, text="🎯 QoS Uygula", width=82, height=24, font=ctk.CTkFont(size=11),
                fg_color="#4B0082", command=self.qos_uygula_tetikle
            ).pack(side="left", padx=1)

            ctk.CTkButton(
                qos_bar, text="♻️ QoS Sıfırla", width=80, height=24, font=ctk.CTkFont(size=11),
                fg_color="#374151", command=lambda: self._gorev_baslat(tum_qos_kurallarini_sifirla, self.log_yaz)
            ).pack(side="left", padx=1)

            self.btn_trafik = ctk.CTkButton(
                qos_bar, text="📈 Hız İzle", width=68, height=24, font=ctk.CTkFont(size=11),
                fg_color="#006666", command=self.canli_trafik_toggle
            )
            self.btn_trafik.pack(side="left", padx=1)

            ctk.CTkButton(
                qos_bar, text="🛠️ Onar", width=62, height=24, font=ctk.CTkFont(size=11),
                fg_color="#2E7D32", command=lambda: self._gorev_baslat(kapsamli_ag_onarimi, self.log_yaz)
            ).pack(side="left", padx=(1, 0))

            # Log Kutusu
            self.txt_modem_log = ctk.CTkTextbox(
                self, font=ctk.CTkFont(family="Consolas", size=11),
                fg_color="#05080F", text_color="#00FF88", height=95, wrap="word"
            )
            self.txt_modem_log.pack(side="top", fill="both", expand=True, padx=6, pady=(2, 6))
            self.log_yaz("[*] Altar Turbo Modem (Hotspot) & QoS Yöneticisi Hazır.")

        def _gorev_baslat(self, fonk, *args):
            if self._islem_aktif:
                return
            self._islem_aktif = True

            def _sarici():
                try:
                    fonk(*args)
                finally:
                    self._islem_aktif = False

            threading.Thread(target=_sarici, daemon=True).start()

        def log_yaz(self, metin: str):
            self._log_tamponu.append(metin)

        def _toplu_log_guncelle(self):
            try:
                if not self.winfo_exists():
                    return
                if self._son_hiz_metni:
                    self.lbl_canli_hiz.configure(text=self._son_hiz_metni)
                    self._son_hiz_metni = ""
                if self._log_tamponu:
                    satirlar = []
                    while self._log_tamponu:
                        satirlar.append(self._log_tamponu.popleft())
                    self.txt_modem_log.insert("end", "\n".join(satirlar) + "\n")
                    self.txt_modem_log.see("end")
                self.after(200, self._toplu_log_guncelle)
            except Exception:
                pass

        def modem_baslat_tetikle(self):
            ssid = self.entry_ssid.get().strip() or "Altar_Turbo_Net"
            sifre = self.entry_sifre.get().strip()
            bant = self.bant_var.get()
            self._gorev_baslat(hotspot_baslat, ssid, sifre, bant, self.log_yaz)

        def modem_durdur_tetikle(self):
            self._gorev_baslat(hotspot_durdur, self.log_yaz)

        def qos_uygula_tetikle(self):
            hedef = self.entry_qos_hedef.get().strip()
            if not hedef:
                messagebox.showwarning("Eksik Bilgi", "Lütfen QoS uygulanacak cihazın IP veya MAC adresini girin.")
                return
            mod = self.qos_mod_var.get()
            try:
                mbps = float(self.entry_qos_mbps.get().strip().replace(",", ".") or 0.0)
            except ValueError:
                mbps = 0.0
            self._gorev_baslat(qos_kural_uygula, hedef, mod, mbps, self.log_yaz)

        def canli_trafik_toggle(self):
            if not PSUTIL_VAR:
                self.log_yaz("[HATA] Canlı hız izleme için 'psutil' gerekli.")
                return
            self.trafik_izleme_aktif = not self.trafik_izleme_aktif
            if self.trafik_izleme_aktif:
                self.btn_trafik.configure(text="📈 İzleniyor", fg_color="#00A86B")

                def _izle():
                    eski = psutil.net_io_counters()
                    while self.trafik_izleme_aktif:
                        time.sleep(1)
                        yeni = psutil.net_io_counters()
                        down_kb = (yeni.bytes_recv - eski.bytes_recv) / 1024.0
                        up_kb = (yeni.bytes_sent - eski.bytes_sent) / 1024.0
                        d_str = f"{down_kb/1024:.2f} MB/s" if down_kb > 1024 else f"{down_kb:.1f} KB/s"
                        u_str = f"{up_kb/1024:.2f} MB/s" if up_kb > 1024 else f"{up_kb:.1f} KB/s"
                        self._son_hiz_metni = f"⬇️ {d_str} | ⬆️ {u_str}"
                        eski = yeni

                threading.Thread(target=_izle, daemon=True).start()
            else:
                self.btn_trafik.configure(text="📈 Hız İzle", fg_color="#006666")
                self.lbl_canli_hiz.configure(text="⬇️ 0.0 KB/s | ⬆️ 0.0 KB/s")


if __name__ == "__main__":
    if not is_admin():
        print("\n[BİLGİ] İnternet paylaşımı (Hotspot) ve QoS yönetimi için Yönetici izinleri gerekiyor...")
        time.sleep(1)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1)
        sys.exit()

    try:
        if os.name == 'nt':
            ctypes.windll.kernel32.SetConsoleTitleW("Altar Ağ Yöneticisi - Turbo & QoS Sürümü")
    except Exception:
        pass
    while True:
        print("\n--- ALTAR AĞ YÖNETİCİSİ (TURBO & QoS SÜRÜMÜ) ---")
        secim = input(
            "1 - Ağı Başlat (Turbo İnternet Paylaşımı)\n"
            "2 - Ağı Durdur\n"
            "3 - Bağlı Cihazları Analiz Et (IP, MAC ve QoS Durumu)\n"
            "4 - Sadece Hız ve Bant Genişliği Turbo Ayarlarını Uygula\n"
            "5 - Ağ ve DNS Onarımı\n"
            "6 - Çıkış\n"
            "Seçiminiz: "
        )
        if secim == '1':
            ssid = input("Ağ Adı (SSID): ")
            sifre = input("Şifre (En az 8 karakter): ")
            bant = input("Frekans Bandı [oto / 5 / 2.4]: ").strip().lower() or "oto"
            hotspot_baslat(ssid, sifre, bant)
        elif secim == '2':
            hotspot_durdur()
        elif secim == '3':
            cihazlari_listele()
        elif secim == '4':
            bant_genisligi_optimize_et()
        elif secim == '5':
            kapsamli_ag_onarimi()
        elif secim == '6':
            hotspot_durdur()
            break