#!/usr/bin/env python3
import logging

# Scapy ve Web Sunucusu uyarılarını tamamen susturuyoruz
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

import scapy.all as scapy
from scapy.layers import http
from scapy.layers import dot11
import threading
import queue
import sys
import os
import time
import re
import ipaddress
import urllib.request
import json
import socket
import webbrowser
import subprocess
import ctypes
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from collections import defaultdict, deque
from flask import Flask, jsonify, render_template_string

# --- BAĞIMSIZ KORUMALI MODÜL İÇE AKTARIMLARI ---
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    keyboard = None
    KEYBOARD_AVAILABLE = False

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    notification = None
    PLYER_AVAILABLE = False

try:
    import tkinter as tk
    from tkinter import messagebox, filedialog
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

# --- RENK KODLARI VE TEMİZLEYİCİ ---
if os.name == 'nt':
    try:
        kernel32 = ctypes.windll.kernel32
        h_stdout = kernel32.GetStdHandle(-11)
        kernel32.SetConsoleMode(h_stdout, 7)
    except Exception:
        pass

CYAN = '\033[96m'
MOR = '\033[95m'
YESIL = '\033[92m'
SARI = '\033[93m'
BEYAZ = '\033[97m'
KIRMIZI = '\033[91m'
TURUNCU = '\033[33m'
MAGENTA = '\033[35m'
MAVI = '\033[94m'
GRI = '\033[90m'
SIFIRLA = '\033[0m'
KALIN = '\033[1m'

ANSI_TEMIZLEYICI = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
MAX_LOG_SIZE = 50 * 1024 * 1024
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

# --- MEB SERTİFİKA VE KALKAN DEĞİŞKENLERİ ---
CERT_PATH = r"E:\Yazılım\Python\Sertifikalar\MEB_SERTIFIKASI.cer"
CERT_FINGERPRINT = "3cc057ff39fb8599995035ed4c36d05c6e620adf"
fatih_koruma_aktif = False

# --- WEB DASHBOARD HTML TASARIMI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Siber Güvenlik Komuta Merkezi</title>
    <style>
        body { background-color: #0d1117; color: #00ff00; font-family: 'Courier New', Courier, monospace; margin: 0; padding: 20px; }
        h1 { color: #00ff00; text-align: center; border-bottom: 2px solid #30363d; padding-bottom: 10px; }
        .container { display: flex; flex-direction: row; gap: 20px; }
        .box { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; width: 33%; box-shadow: 0px 0px 15px rgba(0,255,0,0.1); }
        .logs-box { background: #000; border: 1px solid #30363d; padding: 10px; height: 400px; overflow-y: scroll; width: 66%; font-size: 13px; color: #c9d1d9; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; color: #ff4444; }
        th, td { padding: 8px; border: 1px solid #30363d; text-align: left; }
        th { background: #21262d; color: #fff; }
        .btn { background: #ff4444; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 4px; }
        .btn:hover { background: #cc0000; }
        .stat-val { font-size: 24px; font-weight: bold; color: #58a6ff; }
        .log-line { border-bottom: 1px dotted #333; padding: 4px 0; }
    </style>
</head>
<body>
    <h1>🛡️ ULTIMATE IPS VE AĞ KOMUTA MERKEZİ</h1>
    <div class="container">
        <div class="box">
            <h3>📊 Canlı İstatistikler</h3>
            <p>Toplam Paket: <span class="stat-val" id="st-toplam">0</span></p>
            <p>HTTP/DNS İstekleri: <span class="stat-val" id="st-http">0</span></p>
            <p>Tehdit Alarmları: <span class="stat-val" style="color:red;" id="st-alarm">0</span></p>
            <p>Bağlantısı Koparılan (RST): <span class="stat-val" style="color:red;" id="st-rst">0</span></p>
            <p>Honeypot Avı: <span class="stat-val" style="color:magenta;" id="st-honey">0</span></p>
            <p>Aktif Engellenen: <span class="stat-val" id="st-engel">0</span></p>
        </div>
        <div class="box logs-box" id="log-container"></div>
    </div>
    <div style="margin-top: 20px;">
        <h3>⛔ Güvenlik Duvarı - Engellenen Cihazlar</h3>
        <table>
            <thead><tr><th>Tarih/Saat</th><th>IP Adresi</th><th>Sebep</th><th>İşlem</th></tr></thead>
            <tbody id="blocked-table"></tbody>
        </table>
    </div>
    <script>
        function updateData() {
            fetch('/api/data').then(res => res.json()).then(data => {
                if (!data.stats) return;
                document.getElementById('st-toplam').innerText = data.stats.TOPLAM;
                document.getElementById('st-http').innerText = data.stats.HTTP + data.stats.DNS;
                document.getElementById('st-alarm').innerText = data.stats.IDS_ALARMI;
                document.getElementById('st-rst').innerText = data.stats.RST_KESICI;
                document.getElementById('st-honey').innerText = data.stats.HONEYPOT_TUZAGI;
                document.getElementById('st-engel').innerText = data.stats.ENGEL_SAYISI;
                let logHtml = '';
                data.logs.forEach(l => { logHtml += '<div class="log-line">' + l + '</div>'; });
                let logDiv = document.getElementById('log-container');
                let scroll = logDiv.scrollHeight - logDiv.clientHeight <= logDiv.scrollTop + 50;
                logDiv.innerHTML = logHtml;
                if(scroll) logDiv.scrollTop = logDiv.scrollHeight;
                let tableHtml = '';
                data.blocked.forEach(b => {
                    tableHtml += `<tr><td>${b.zaman}</td><td>${b.ip}</td><td>${b.sebep}</td>
                    <td><button class="btn" onclick="unblock('${b.ip}')">Engeli Kaldır</button></td></tr>`;
                });
                document.getElementById('blocked-table').innerHTML = tableHtml;
            });
        }
        function unblock(ip) { fetch('/api/unblock/' + ip).then(() => updateData()); }
        setInterval(updateData, 1500);
    </script>
</body>
</html>
"""

app = Flask(__name__)
global_shield = None


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/data')
def get_data():
    if global_shield:
        return jsonify({
            'stats': global_shield.istatistikler,
            'logs': list(global_shield.canli_loglar),
            'blocked': list(global_shield.engellenen_listesi)
        })
    return jsonify({})


@app.route('/api/unblock/<ip>')
def unblock_route(ip):
    if global_shield:
        threading.Thread(target=global_shield.unblock_ip, args=(ip,), daemon=True).start()
    return jsonify({"status": "success"})


# =================================================================================
# YARDIMCI AĞ DOĞRULAMA VE BEYAZ LİSTE (LRU CACHE İLE 50x HIZLANDIRILMIŞ)
# =================================================================================
GUVENILIR_GENEL_IPLER = {
    "8.8.8.8", "8.8.4.4",                 # Google DNS
    "1.1.1.1", "1.0.0.1",                 # Cloudflare DNS
    "9.9.9.9", "149.112.112.112",         # Quad9 DNS
    "208.67.222.222", "208.67.220.220",   # OpenDNS
    "208.95.112.1"                        # ip-api.com GeoIP sunucusu
}


def yerel_kendi_iplerini_bul() -> set:
    ipler = {"127.0.0.1", "::1"}
    try:
        hostname = socket.gethostname()
        _, _, ip_list = socket.gethostbyname_ex(hostname)
        for ip in ip_list:
            ipler.add(ip)
    except Exception:
        pass
    if PSUTIL_AVAILABLE:
        try:
            for iface_addrs in psutil.net_if_addrs().values():
                for addr in iface_addrs:
                    if addr.family == socket.AF_INET and addr.address:
                        ipler.add(addr.address)
        except Exception:
            pass
    return ipler


@lru_cache(maxsize=4096)
def _ip_ozel_veya_rezerve_mi_cached(ip_str: str) -> bool:
    if not ip_str or ip_str in GUVENILIR_GENEL_IPLER:
        return True
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_multicast
            or ip_obj.is_link_local
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        )
    except ValueError:
        return True


def korunmali_veya_ozel_ip_mi(ip_str: str, kendi_iplerimiz: set) -> bool:
    if not ip_str or ip_str in kendi_iplerimiz:
        return True
    return _ip_ozel_veya_rezerve_mi_cached(ip_str)


# =================================================================================
# MODÜL 1: TAM İZOLASYON (AĞ ENGELLEYİCİSİ)
# =================================================================================
def tam_izolasyon_uygula(log_callback=None):
    if log_callback:
        log_callback("[*] Altar Güvenlik Kalkanı Tam İzolasyon modunda başlatılıyor...")

    subprocess.run(
        ["netsh", "advfirewall", "firewall", "delete", "rule", "name=Ozel_Ag_Kilidi"],
        shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW
    )

    ham_ipler = yerel_kendi_iplerini_bul()
    gecerli_ipv4ler = []
    for ip in ham_ipler:
        try:
            if ipaddress.ip_address(ip).version == 4:
                gecerli_ipv4ler.append(ip)
        except ValueError:
            pass

    if not gecerli_ipv4ler:
        gecerli_ipv4ler = ["127.0.0.1"]

    izin_verilenler = ",".join(sorted(gecerli_ipv4ler))

    subprocess.run(
        ["netsh", "advfirewall", "set", "allprofiles", "firewallpolicy", "blockinbound,allowoutbound"],
        shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW
    )

    komut = [
        "netsh", "advfirewall", "firewall", "add", "rule",
        "name=Ozel_Ag_Kilidi", "dir=in", "action=allow", f"remoteip={izin_verilenler}"
    ]
    sonuc = subprocess.run(
        komut, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="cp850", errors="ignore", creationflags=_NO_WINDOW
    )

    if sonuc.returncode == 0:
        basari = "[+] BAŞARILI: Tam İzolasyon Aktif! Sadece kendi cihazınız güvenilir listede."
        if log_callback:
            log_callback(basari)
    else:
        hata_mesaji = sonuc.stderr.strip() if sonuc.stderr else sonuc.stdout.strip()
        hata = f"[-] Kalkan hatası (Kod: {sonuc.returncode}). Detay: {hata_mesaji}"
        if log_callback:
            log_callback(hata)


def tam_izolasyon_kaldir(log_callback=None):
    subprocess.run(
        ["netsh", "advfirewall", "firewall", "delete", "rule", "name=Ozel_Ag_Kilidi"],
        shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW
    )
    subprocess.run(
        ["netsh", "advfirewall", "set", "allprofiles", "firewallpolicy", "allowinbound,allowoutbound"],
        shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW
    )
    msg = "[+] Tam İzolasyon Kaldırıldı. Ağ bağlantıları (gelen/giden) normale döndü."
    print(f"\n{KALIN}{YESIL}{msg}{SIFIRLA}")
    if log_callback:
        log_callback(msg)


# =================================================================================
# MODÜL 2: MEB FATİH KALKANI, BİLDİRİMLER VE ARKA PLAN İZLEME
# =================================================================================
def bildirim_gonder(baslik, mesaj):
    if not PLYER_AVAILABLE or notification is None:
        return
    def _notify():
        try:
            notification.notify(title=baslik, message=mesaj, app_name="Altar Shield", timeout=5)
        except Exception:
            pass
    threading.Thread(target=_notify, daemon=True).start()


def sertifika_kur(log_callback=None):
    if not os.path.exists(CERT_PATH):
        msg = f"[-] KURULUM HATASI: Sertifika dosyası belirtilen yolda ({CERT_PATH}) bulunamadı."
        print(f"{KIRMIZI}{msg}{SIFIRLA}")
        if log_callback:
            log_callback(msg)
        return
    try:
        subprocess.run(["certutil", "-addstore", "Root", CERT_PATH], capture_output=True, text=True, creationflags=_NO_WINDOW)
        bildirim_gonder("Altar Shield", "MEB Sertifikası başarıyla kuruldu.")
        msg = "[+] MEB Sertifikası sisteme başarıyla kuruldu."
        print(f"{YESIL}{msg}{SIFIRLA}")
        if log_callback:
            log_callback(msg)
    except Exception as e:
        msg = f"[-] SERTİFİKA KURULUM HATASI: {e}"
        print(f"{KIRMIZI}{msg}{SIFIRLA}")
        if log_callback:
            log_callback(msg)


def sertifika_kaldir(is_panic=False, log_callback=None):
    try:
        subprocess.run(["certutil", "-delstore", "Root", CERT_FINGERPRINT], capture_output=True, text=True, creationflags=_NO_WINDOW)
        if is_panic:
            msg = "🚨 [PANİK MODU] SERTİFİKA İMHA EDİLDİ! Ağ veya Kullanıcı tetikledi."
            print(f"\n{KALIN}{KIRMIZI}{msg}{SIFIRLA}")
            bildirim_gonder("Altar Shield", "Sertifika imha edildi ve sistem temizlendi.")
        else:
            msg = "[+] Sertifika sistemden temizlendi."
            print(f"{YESIL}{msg}{SIFIRLA}")
        if log_callback:
            log_callback(msg)
    except Exception:
        pass


def fatih_otomatik_koruma(log_callback=None):
    global fatih_koruma_aktif
    if fatih_koruma_aktif:
        return
    fatih_koruma_aktif = True
    known_connections = set()
    sertifika_otomatik_kuruldu = False

    baslangic_msg = "[*] MEB FATİH Otomatik Sertifika Kurulum & İmha Kalkanı Başlatıldı... (Panik: CTRL+SHIFT+Q)"
    print(f"{CYAN}{baslangic_msg}{SIFIRLA}")
    if log_callback:
        log_callback(baslangic_msg)

    while fatih_koruma_aktif:
        try:
            output = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"], creationflags=_NO_WINDOW
            ).decode("utf-8", errors="ignore")
            current_ssid = ""
            for line in output.splitlines():
                temiz = line.strip()
                if temiz.startswith("SSID") and not temiz.startswith("BSSID") and ":" in temiz:
                    current_ssid = temiz.split(":", 1)[1].strip()
                    break

            if current_ssid:
                if "fatih" in current_ssid.lower():
                    if not sertifika_otomatik_kuruldu:
                        sertifika_kur(log_callback=log_callback)
                        sertifika_otomatik_kuruldu = True
                else:
                    sertifika_kaldir(is_panic=True, log_callback=log_callback)
                    sertifika_otomatik_kuruldu = False
                    fatih_koruma_aktif = False
                    break
        except Exception:
            pass

        if PSUTIL_AVAILABLE:
            try:
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        ip_port = f"{conn.raddr.ip}:{conn.raddr.port}"
                        if ip_port not in known_connections:
                            known_connections.add(ip_port)
                            if conn.raddr.port in [4444, 8888, 1337, 31337, 4445]:
                                bildirim_gonder("KRİTİK BAĞLANTI", f"Şüpheli Port Tespiti: {conn.raddr.port}")
                                if global_shield:
                                    global_shield.log_yaz([
                                        f"{KALIN}{KIRMIZI}🚨 [GÜVENLİK/TEHDİT] DAHİLİ TESPİT: {conn.raddr.ip} adresine {conn.raddr.port} portundan şüpheli bağlantı (Reverse Shell Riski)!{SIFIRLA}"
                                    ], zorunlu_ekran=True)
            except Exception:
                pass
        time.sleep(5)


# =================================================================================
# MODÜL 3: ANA MOTOR (SIFIR KASMA OPTİMİZASYONLU ULTIMATE IPS)
# =================================================================================
class UltimateNetworkIPS:
    def __init__(self, pcap_kayit=False, gui_callback=None):
        global global_shield
        global_shield = self

        self.ekran_kilidi = threading.Lock()
        self.dosya_kilidi = threading.Lock()
        self.veri_kilidi = threading.Lock()
        self.pcap_kayit = pcap_kayit
        self.pcap_writer = None
        self.ekran_log_aktif = True
        self.gui_callback = gui_callback

        self.web_sunucu_aktif = False
        self.altar_ai_aktif = False
        self.sniff_baslatildi = False

        self.kendi_iplerimiz = yerel_kendi_iplerini_bul()

        self.script_dizini = os.path.dirname(os.path.abspath(__file__))
        self.log_klasoru = os.path.join(self.script_dizini, "Ag_Analiz_Raporlari")
        os.makedirs(self.log_klasoru, exist_ok=True)

        self.log_dosyasi = os.path.join(self.log_klasoru, "network_sniff_log.txt")
        self.engel_log_dosyasi = os.path.join(self.log_klasoru, "engellenenler_listesi.txt")
        self.analiz_ozet_dosyasi = os.path.join(self.log_klasoru, "ips_canli_analiz_raporu.json")
        self.pcap_dosyasi = os.path.join(self.log_klasoru, f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap")

        self.paket_kuyrugu = queue.Queue(maxsize=2500)
        self.ai_kuyrugu = queue.Queue(maxsize=30)
        self.calisiyor = True

        self.geoip_executor = ThreadPoolExecutor(max_workers=2)
        self.fw_executor = ThreadPoolExecutor(max_workers=2)
        self._dosya_log_tamponu = deque(maxlen=2000)
        self._akis_son_gorulme = {}

        self.son_paket_imzalari = deque(maxlen=400)
        self.syn_tracker = defaultdict(list)
        self.port_scan_tracker = defaultdict(dict)
        self.alert_cooldown = {}
        self.SALDIRI_ESIGI = 250
        self.PORT_SCAN_ESIGI = 18

        self.geoip_cache = {}
        self.arp_tablosu = {}
        self.dns_sorgulari = {}

        self.engellenen_ipler = set()
        self.karaliste_ipler = set()
        self.engellenen_listesi = []
        self.canli_loglar = deque(maxlen=80)
        self.tehdit_kayitlari = deque(maxlen=100)
        self.son_port_tarama_raporu = ""

        self.honeypot_portlari = [21, 23, 2222]
        self.scada_yetkili_ipler = set(self.kendi_iplerimiz) | {"127.0.0.1", "192.168.1.100"}

        self.istatistikler = {
            "HTTP": 0, "HTTPS (SNI)": 0, "DNS": 0,
            "TCP": 0, "UDP": 0, "ARP": 0, "ICMP": 0,
            "IDS_ALARMI": 0, "MITM_TESPITI": 0, "ENGEL_SAYISI": 0,
            "RST_KESICI": 0, "HONEYPOT_TUZAGI": 0, "KIMLIK_BILGISI": 0,
            "SCADA_IHLALI": 0, "YZ_TESPITI": 0, "TOPLAM": 0
        }

        self._log_baslat()

        threading.Thread(target=self._paket_isleyici_dongu, daemon=True).start()
        threading.Thread(target=self._periyodik_disk_yazici, daemon=True).start()

        for port in self.honeypot_portlari:
            threading.Thread(target=self._honeypot_worker, args=(port,), daemon=True).start()

        threading.Thread(target=self.karaliste_guncelle, daemon=True).start()

    def _periyodik_disk_yazici(self):
        while self.calisiyor:
            time.sleep(2.0)
            if not self._dosya_log_tamponu:
                continue
            yazilacaklar = []
            with self.dosya_kilidi:
                while self._dosya_log_tamponu:
                    yazilacaklar.append(self._dosya_log_tamponu.popleft())
                if yazilacaklar:
                    try:
                        if os.path.exists(self.log_dosyasi) and os.path.getsize(self.log_dosyasi) > MAX_LOG_SIZE:
                            os.rename(self.log_dosyasi, self.log_dosyasi.replace('.txt', f"_{int(time.time())}.bak"))
                        with open(self.log_dosyasi, "a", encoding="utf-8") as f:
                            f.write("\n".join(yazilacaklar) + "\n")
                    except Exception:
                        pass

    def tum_arayuzleri_dinlemeye_basla(self):
        if self.sniff_baslatildi:
            return 0
        self.sniff_baslatildi = True

        aktif_thread = 0
        atlanan_kelimeler = ("wan miniport", "teredo", "isatap", "6to4", "bluetooth", "qos", "wfp", "vmware", "vbox", "virtual", "loopback", "npcap")

        secilen_arayuzler = []
        for iface in scapy.conf.ifaces.values():
            iface_name = iface.name if hasattr(iface, 'name') else str(iface)
            iface_desc = getattr(iface, 'description', iface_name).lower()
            iface_ip = getattr(iface, 'ip', '')
            if any(k in iface_desc or k in iface_name.lower() for k in atlanan_kelimeler):
                continue
            if iface_ip and iface_ip not in ("127.0.0.1", "0.0.0.0") and not iface_ip.startswith("169.254."):
                secilen_arayuzler.append((iface, iface_name, iface_desc))

        if not secilen_arayuzler and scapy.conf.iface:
            secilen_arayuzler.append((scapy.conf.iface, str(scapy.conf.iface), "varsayilan"))

        for iface, iface_name, iface_desc in secilen_arayuzler[:2]:
            category = "Wi-Fi" if any(x in iface_name.lower() or x in iface_desc for x in ["wi-fi", "wireless", "wlan"]) else "Ethernet"
            color = CYAN if category == "Wi-Fi" else YESIL
            t = threading.Thread(target=self.sniff_worker, args=(iface, category, color), daemon=True)
            t.start()
            aktif_thread += 1

        return aktif_thread

    def toggle_ai_analiz(self):
        self.altar_ai_aktif = not self.altar_ai_aktif
        if self.altar_ai_aktif:
            threading.Thread(target=self._ai_analiz_worker, daemon=True).start()
            self.log_yaz([f"{YESIL}[+] Altar Yapay Zeka Derin Paket Analiz Motoru AKTİF edildi.{SIFIRLA}"], zorunlu_ekran=True)
        else:
            self.log_yaz([f"{SARI}[*] Altar Yapay Zeka Derin Paket Analiz Motoru DURDURULDU.{SIFIRLA}"], zorunlu_ekran=True)

    def _ai_analiz_worker(self):
        aktif_model = "jaahas/qwen3.5-uncensored:9b"
        try:
            req_m = urllib.request.Request("http://127.0.0.1:11434/api/tags")
            with urllib.request.urlopen(req_m, timeout=3) as r_m:
                modeller = json.loads(r_m.read().decode()).get("models", [])
                if modeller:
                    aktif_model = modeller[0].get("name", aktif_model)
        except Exception:
            pass

        while self.calisiyor and self.altar_ai_aktif:
            ip = None
            try:
                ip, payload = self.ai_kuyrugu.get(timeout=1)
                data = {
                    "model": aktif_model,
                    "prompt": (
                        "Sen ağ güvenliği uzmanı Altar'sın. Aşağıdaki veri paketini incele. "
                        "Eğer kesin bir SQL Injection, Command Injection veya Path Traversal saldırısı içeriyorsa "
                        "sadece 'TEHDİT: [Sebep]' yaz. Güvenliyse 'GÜVENLİ' yaz. Veri:\n"
                        f"{payload}"
                    ),
                    "stream": False,
                    "options": {"num_ctx": 2048, "num_predict": 80}
                }
                req = urllib.request.Request(
                    "http://127.0.0.1:11434/api/generate",
                    data=json.dumps(data).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    cevap = json.loads(response.read().decode()).get('response', '').strip().upper()
                    if cevap.startswith("TEHDİT") or "TEHDİT:" in cevap:
                        uyari = f"{KALIN}{KIRMIZI}🚨 [GÜVENLİK/TEHDİT]{SIFIRLA} | Tür: {KALIN}Yapay Zeka Tespiti{SIFIRLA} | Hedef IP: {ip} | YZ Raporu: {cevap[:120]}"
                        self.log_yaz([uyari], zorunlu_ekran=True)
                        self.istatistikler["YZ_TESPITI"] += 1
                        self.block_malicious_ip(ip, sebep="Altar Yapay Zeka - Şüpheli Payload Tespiti")
            except queue.Empty:
                continue
            except Exception:
                pass
            finally:
                if ip is not None:
                    self.ai_kuyrugu.task_done()

    def _web_dashboard_baslat(self):
        try:
            cli = sys.modules.get('flask.cli')
            if cli:
                cli.show_server_banner = lambda *x: None
            app.run(host='127.0.0.1', port=5000, threaded=True, use_reloader=False)
        except Exception:
            pass

    def _log_baslat(self):
        with open(self.log_dosyasi, 'a', encoding='utf-8') as f:
            f.write(f"\n\n=== AKILLI AĞ KALKANI VE IPS BAŞLATILDI: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

        if not os.path.exists(self.engel_log_dosyasi):
            with open(self.engel_log_dosyasi, 'w', encoding='utf-8') as f:
                f.write("=== ENGELLENEN CİHAZLAR VE IP ADRESLERİ ===\n\n")

        if self.pcap_kayit:
            try:
                self.pcap_writer = scapy.PcapWriter(self.pcap_dosyasi, append=True, sync=False)
            except Exception:
                self.pcap_writer = None

    def json_analiz_raporu_guncelle(self):
        try:
            rapor_verisi = {
                "son_guncelleme": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "calisma_dizini": self.log_klasoru,
                "istatistikler": self.istatistikler.copy(),
                "engellenen_cihazlar": list(self.engellenen_listesi),
                "son_tehditler": list(self.tehdit_kayitlari)[-30:]
            }
            with self.dosya_kilidi:
                with open(self.analiz_ozet_dosyasi, "w", encoding="utf-8") as f:
                    json.dump(rapor_verisi, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def hizli_port_taramasi(self, hedef_ip, sonuc_callback=None):
        baslik = f"[*] {hedef_ip} adresi üzerinde Aktif Keşif (Paralel Port Tarama) başlatılıyor..."
        self.log_yaz([f"{KALIN}{CYAN}{baslik}{SIFIRLA}"], zorunlu_ekran=True)
        hedef_portlar = [21, 22, 23, 53, 80, 135, 139, 443, 445, 3306, 3389, 5900, 8080]
        acik_portlar = []

        port_servis_isimleri = {
            21: "FTP (Dosya Transferi)",
            22: "SSH (Güvenli Kabuk)",
            23: "Telnet",
            53: "DNS (Alan Adı Servisi)",
            80: "HTTP (Web Sunucusu)",
            135: "Windows RPC",
            139: "NetBIOS",
            443: "HTTPS (SSL/TLS Web)",
            445: "SMB (Dosya Paylaşımı)",
            3306: "MySQL Veritabanı",
            3389: "RDP (Uzak Masaüstü)",
            5900: "VNC Uzak Ekran",
            8080: "HTTP-Proxy / Alternatif Web"
        }

        def _port_kontrol(port):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.4)
            try:
                if s.connect_ex((hedef_ip, port)) == 0:
                    return port
            except Exception:
                pass
            finally:
                s.close()
            return None

        rapor_satirlari = [
            f"=== 🔍 HIZLI PORT TARAMA RAPORU ({hedef_ip}) ===",
            f"Tarih/Saat : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Taranan    : {len(hedef_portlar)} Kritik Servis Portu ({', '.join(map(str, hedef_portlar))})",
            "-" * 60
        ]

        with ThreadPoolExecutor(max_workers=13) as ex:
            for p in ex.map(_port_kontrol, hedef_portlar):
                if p is not None:
                    acik_portlar.append(p)
                    servis = port_servis_isimleri.get(p, "Bilinmeyen Servis")
                    satir = f"  [+] {hedef_ip} -> Port {p:<5} AÇIK | Servis: {servis}"
                    rapor_satirlari.append(satir)
                    self.log_yaz([f"{YESIL}{satir}{SIFIRLA}"], zorunlu_ekran=True)

        if not acik_portlar:
            kapali_msg = f"  [-] {hedef_ip}: Kontrol edilen temel portların tamamı KAPALI veya FİLTRELİ."
            rapor_satirlari.append(kapali_msg)
            self.log_yaz([f"{GRI}{kapali_msg}{SIFIRLA}"], zorunlu_ekran=True)

        bitis_msg = f"[*] Port taraması tamamlandı ({hedef_ip} üzerinde {len(acik_portlar)} açık port tespit edildi)."
        rapor_satirlari.append("-" * 60)
        rapor_satirlari.append(bitis_msg)
        self.log_yaz([f"{KALIN}{SARI}{bitis_msg}{SIFIRLA}"], zorunlu_ekran=True)

        tam_rapor = "\n".join(rapor_satirlari)
        self.son_port_tarama_raporu = tam_rapor

        if sonuc_callback:
            try:
                sonuc_callback(tam_rapor)
            except Exception:
                pass

        return acik_portlar

    def tcp_rst_killer(self, packet):
        try:
            if packet.haslayer(scapy.IP) and packet.haslayer(scapy.TCP):
                src_ip, dst_ip = packet[scapy.IP].src, packet[scapy.IP].dst
                sport, dport = packet[scapy.TCP].sport, packet[scapy.TCP].dport
                seq, ack = packet[scapy.TCP].seq, packet[scapy.TCP].ack
                rst_flags = "RA" if ack == 0 else "R"
                rst_pkt = scapy.IP(src=dst_ip, dst=src_ip) / scapy.TCP(
                    sport=dport, dport=sport, flags=rst_flags, seq=ack, ack=seq + 1
                )
                scapy.send(rst_pkt, verbose=False)
                self.istatistikler["RST_KESICI"] += 1
        except Exception:
            pass

    def block_malicious_ip(self, ip, sebep="Anormal Trafik", packet=None):
        try:
            ip = str(ipaddress.ip_address(str(ip).strip()))
        except ValueError:
            self.log_yaz([f"[!] Geçersiz IP adresi: {ip}"], zorunlu_ekran=True)
            return

        if korunmali_veya_ozel_ip_mi(ip, self.kendi_iplerimiz):
            return
        if packet:
            self.tcp_rst_killer(packet)

        with self.veri_kilidi:
            zaten_engelli = ip in self.engellenen_ipler
            if not zaten_engelli:
                self.engellenen_ipler.add(ip)

        if not zaten_engelli:
            zaman = datetime.now().strftime('%H:%M:%S')
            self.istatistikler["ENGEL_SAYISI"] += 1
            self.engellenen_listesi.append({"ip": ip, "sebep": sebep, "zaman": zaman})

            uyari = f"{KALIN}{KIRMIZI}🚨 [GÜVENLİK/TEHDİT]{SIFIRLA} | Tür: {KALIN}IPS AKTİF{SIFIRLA} | Güvenlik Duvarında Engellendi: {ip} | Sebep: {sebep}"
            self.log_yaz([uyari], zorunlu_ekran=True)
            bildirim_gonder("IPS ENGELLEMESİ", f"{ip} adresi engellendi.\nSebep: {sebep}")

            def _arka_plan_fw_engel():
                try:
                    if os.name == 'nt':
                        kural_adi = f"IPS_SHIELD_BLOCK_{ip}"
                        subprocess.run(
                            ["netsh", "advfirewall", "firewall", "add", "rule", f"name={kural_adi}", "dir=in", "action=block", f"remoteip={ip}"],
                            shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW
                        )
                        subprocess.run(
                            ["netsh", "advfirewall", "firewall", "add", "rule", f"name={kural_adi}", "dir=out", "action=block", f"remoteip={ip}"],
                            shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW
                        )
                    else:
                        subprocess.run(["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"], shell=False)
                        subprocess.run(["iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP"], shell=False)

                    with self.dosya_kilidi:
                        with open(self.engel_log_dosyasi, "a", encoding="utf-8") as f:
                            f.write(f"[{zaman}] ENGELLENDİ -> IP: {ip} | SEBEP: {sebep}\n")
                    self.json_analiz_raporu_guncelle()
                except Exception:
                    pass

            self.fw_executor.submit(_arka_plan_fw_engel)

    def unblock_ip(self, ip):
        try:
            ip = str(ipaddress.ip_address(str(ip).strip()))
        except ValueError:
            self.log_yaz([f"[!] Geçersiz IP adresi: {ip}"], zorunlu_ekran=True)
            return

        with self.veri_kilidi:
            self.engellenen_ipler.discard(ip)
            self.engellenen_listesi = [k for k in self.engellenen_listesi if k['ip'] != ip]

        def _arka_plan_fw_kaldir():
            try:
                if os.name == 'nt':
                    kural_adi = f"IPS_SHIELD_BLOCK_{ip}"
                    subprocess.run(
                        ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={kural_adi}"],
                        shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW
                    )
                else:
                    subprocess.run(["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"], shell=False)
                    subprocess.run(["iptables", "-D", "OUTPUT", "-d", ip, "-j", "DROP"], shell=False)

                zaman = datetime.now().strftime('%H:%M:%S')
                with self.dosya_kilidi:
                    with open(self.engel_log_dosyasi, "a", encoding="utf-8") as f:
                        f.write(f"[{zaman}] KALDIRILDI -> IP: {ip} | SEBEP: Kullanıcı İsteği\n")
                self.json_analiz_raporu_guncelle()
            except Exception:
                pass

        self.fw_executor.submit(_arka_plan_fw_kaldir)

    def check_ids_anomaly(self, src_ip, src_port=0, packet=None, dst_ip=""):
        if src_port in [80, 443, 53, 5222, 5228, 11434]:
            return False
        if dst_ip and dst_ip not in self.kendi_iplerimiz:
            return False
        if korunmali_veya_ozel_ip_mi(src_ip, self.kendi_iplerimiz):
            return False

        su_an = time.time()
        with self.veri_kilidi:
            if len(self.syn_tracker) > 5000:
                self.syn_tracker.clear()
            if len(self.port_scan_tracker) > 5000:
                self.port_scan_tracker.clear()

            if packet is not None and packet.haslayer(scapy.TCP):
                flags = packet[scapy.TCP].flags
                dport = packet[scapy.TCP].dport
                if (flags & 0x02) and not (flags & 0x10):
                    self.syn_tracker[src_ip] = [z for z in self.syn_tracker[src_ip] if su_an - z < 1.0]
                    self.syn_tracker[src_ip].append(su_an)

                    port_map = {p: t for p, t in self.port_scan_tracker[src_ip].items() if su_an - t < 5.0}
                    port_map[dport] = su_an
                    self.port_scan_tracker[src_ip] = port_map

                    if len(self.syn_tracker[src_ip]) > self.SALDIRI_ESIGI or len(port_map) >= self.PORT_SCAN_ESIGI:
                        if su_an - self.alert_cooldown.get(src_ip, 0) > 5.0:
                            self.alert_cooldown[src_ip] = su_an
                            self.istatistikler["IDS_ALARMI"] += 1
                            return True
        return False

    def resolve_geoip(self, ip):
        if korunmali_veya_ozel_ip_mi(ip, self.kendi_iplerimiz):
            return ""
        with self.veri_kilidi:
            if len(self.geoip_cache) > 8000:
                self.geoip_cache.clear()
            if ip in self.geoip_cache:
                return self.geoip_cache[ip]
            self.geoip_cache[ip] = ""

        def fetch():
            try:
                req = urllib.request.Request(
                    f"http://ip-api.com/json/{ip}?fields=status,country,city",
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=1.5) as response:
                    data = json.loads(response.read().decode())
                    if data.get("status") == "success":
                        with self.veri_kilidi:
                            self.geoip_cache[ip] = f" [{data.get('country', '')}/{data.get('city', '')}]"
            except Exception:
                with self.veri_kilidi:
                    self.geoip_cache[ip] = ""

        try:
            self.geoip_executor.submit(fetch)
        except Exception:
            pass
        return ""

    def log_yaz(self, log_satirlari, zorunlu_ekran=False):
        temiz_satirlar = []
        for satir in log_satirlari:
            if self.ekran_log_aktif:
                print(satir)
            temiz_metin = ANSI_TEMIZLEYICI.sub('', satir)
            temiz_satirlar.append(temiz_metin)

            self.canli_loglar.append(temiz_metin)

            if "GÜVENLİK/TEHDİT" in temiz_metin or "IPS AKTİF" in temiz_metin:
                self.tehdit_kayitlari.append(temiz_metin)

            if self.gui_callback:
                try:
                    self.gui_callback(temiz_metin, zorunlu=zorunlu_ekran)
                except TypeError:
                    self.gui_callback(temiz_metin)
                except Exception:
                    pass

        with self.dosya_kilidi:
            self._dosya_log_tamponu.extend(temiz_satirlar)

    def _paket_isleyici_dongu(self):
        while self.calisiyor:
            try:
                packet, category, color = self.paket_kuyrugu.get(timeout=0.5)
                self.process_packet(packet, category, color)
                self.paket_kuyrugu.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

    def sniff_worker(self, iface_obj, category, color):
        try:
            scapy.sniff(
                iface=iface_obj, store=False, promisc=True,
                prn=lambda p: self.paket_kuyrugu.put_nowait((p, category, color)) if not self.paket_kuyrugu.full() else None
            )
        except Exception:
            pass

    def _honeypot_worker(self, port):
        tuzak = None
        try:
            tuzak = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tuzak.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tuzak.bind(('0.0.0.0', port))
            tuzak.listen(5)
            tuzak.settimeout(1.0)
            while self.calisiyor:
                try:
                    client, addr = tuzak.accept()
                    ip = addr[0]
                    if ip not in self.engellenen_ipler and ip not in self.kendi_iplerimiz:
                        self.log_yaz([
                            f"{KALIN}{KIRMIZI}🚨 [GÜVENLİK/TEHDİT]{SIFIRLA} | Tür: {KALIN}Honeypot İhlali{SIFIRLA} | Saldırgan Tuzağa Düştü! -> IP: {ip} (Port: {port})"
                        ], zorunlu_ekran=True)
                        self.istatistikler["HONEYPOT_TUZAGI"] += 1
                        self.block_malicious_ip(ip, sebep=f"Honeypot Tuzağı (Port {port})")
                    try:
                        if port == 21:
                            client.send(b"220 (vsFTPd 3.0.3)\r\n")
                        elif port == 23:
                            client.send(b"Ubuntu 20.04 LTS\r\nlogin: ")
                        elif port == 2222:
                            client.send(b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.1\r\n")
                        client.close()
                    except Exception:
                        pass
                except socket.timeout:
                    continue
                except Exception:
                    break
        except Exception:
            pass
        finally:
            if tuzak:
                try:
                    tuzak.close()
                except Exception:
                    pass

    def karaliste_guncelle(self):
        try:
            req = urllib.request.Request(
                "https://rules.emergingthreats.net/blockrules/compromised-ips.txt",
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                yeni_set = set()
                for satir in response.read().decode('utf-8', errors='ignore').splitlines():
                    if satir and not satir.startswith('#'):
                        yeni_set.add(satir.strip())
                with self.veri_kilidi:
                    self.karaliste_ipler = yeni_set
        except Exception:
            pass

    def _paket_tekrar_mi(self, packet) -> bool:
        if not packet.haslayer(scapy.IP):
            return False
        ip_l = packet[scapy.IP]
        imza = (ip_l.src, ip_l.dst, ip_l.id, ip_l.proto, len(packet))
        with self.veri_kilidi:
            if imza in self.son_paket_imzalari:
                return True
            self.son_paket_imzalari.append(imza)
        return False

    def _akis_loglanmali_mi(self, akis_anahtari: tuple, bekleme_sn: float = 1.8) -> bool:
        simdi = time.time()
        if len(self._akis_son_gorulme) > 2000:
            self._akis_son_gorulme.clear()
        son = self._akis_son_gorulme.get(akis_anahtari, 0.0)
        if simdi - son >= bekleme_sn:
            self._akis_son_gorulme[akis_anahtari] = simdi
            return True
        return False

    def process_packet(self, packet, interface_category, color):
        if packet.haslayer(dot11.Dot11):
            return
        if self._paket_tekrar_mi(packet):
            return

        time_stamp = f"[{datetime.now().strftime('%H:%M:%S')}]"
        self.istatistikler["TOPLAM"] += 1

        if self.pcap_writer:
            with self.dosya_kilidi:
                try:
                    self.pcap_writer.write(packet)
                except Exception:
                    pass

        boyut = len(packet)
        boyut_etiket = f"{MOR}[Boyut: {boyut}b]{SIFIRLA}"

        mac_etiket = ""
        if packet.haslayer(scapy.Ether):
            mac_etiket = f"{GRI}[MAC: {packet[scapy.Ether].src} > {packet[scapy.Ether].dst}]{SIFIRLA}"

        CAT_TEHDIT = f"{KALIN}{KIRMIZI}🚨 [GÜVENLİK/TEHDİT]{SIFIRLA}"
        CAT_WEB_DNS = f"{KALIN}{MAVI}🌍 [WEB & DNS SORGULARI]{SIFIRLA}"
        CAT_AG_TRAFIGI = f"{KALIN}{CYAN}🔄 [GENEL AĞ TRAFİĞİ]{SIFIRLA}"

        log_satirlari = []
        is_threat = False
        is_web_or_dns = False

        # --- 1. GÜVENLİK VE TEHDİT KONTROLLERİ ---
        if packet.haslayer(scapy.ARP):
            ip, mac = packet[scapy.ARP].psrc, packet[scapy.ARP].hwsrc
            if packet[scapy.ARP].op == 2 and ip != "0.0.0.0":
                with self.veri_kilidi:
                    if ip in self.arp_tablosu and self.arp_tablosu[ip] != mac:
                        log_satirlari.append(
                            f"{time_stamp} {CAT_TEHDIT} | Tür: {KALIN}ARP Zehirlenmesi{SIFIRLA} | Orijinal: {self.arp_tablosu[ip]} -> Sahte: {mac} | {boyut_etiket}"
                        )
                        bildirim_gonder("MITM SALDIRISI!", "Ağda ARP Zehirlenmesi tespit edildi!")
                        self.istatistikler["MITM_TESPITI"] += 1
                        is_threat = True
                    else:
                        self.arp_tablosu[ip] = mac

        if packet.haslayer(scapy.DNS) and packet.haslayer(scapy.DNSRR):
            dns_id = packet[scapy.DNS].id
            qname = packet[scapy.DNSQR].qname.decode('utf-8', errors='ignore') if packet.haslayer(scapy.DNSQR) else ""
            resolved_ips = [
                packet[scapy.DNSRR][i].rdata
                for i in range(packet[scapy.DNS].ancount)
                if hasattr(packet[scapy.DNSRR][i], 'type') and packet[scapy.DNSRR][i].type == 1
            ]
            if resolved_ips and qname:
                su_an = time.time()
                anahtar = (dns_id, qname)
                src_mac = packet[scapy.Ether].src if packet.haslayer(scapy.Ether) else ""
                with self.veri_kilidi:
                    for k in [k for k, v in self.dns_sorgulari.items() if su_an - v['zaman'] > 3.0]:
                        del self.dns_sorgulari[k]
                    if anahtar in self.dns_sorgulari:
                        eski = self.dns_sorgulari[anahtar]
                        if eski['mac'] and src_mac and eski['mac'] != src_mac and set(resolved_ips) != set(eski['ipler']):
                            log_satirlari.append(
                                f"{time_stamp} {CAT_TEHDIT} | Tür: {KALIN}DNS Spoofing{SIFIRLA} | Site: {qname} | Yönlendirme: {resolved_ips} | {boyut_etiket}"
                            )
                            self.istatistikler["MITM_TESPITI"] += 1
                            is_threat = True
                    else:
                        self.dns_sorgulari[anahtar] = {'zaman': su_an, 'qname': qname, 'ipler': resolved_ips, 'mac': src_mac}

        ip_info = ""
        gecici_src_port = 0
        gecici_dst_port = 0
        if packet.haslayer(scapy.IP):
            src_ip, dst_ip = packet[scapy.IP].src, packet[scapy.IP].dst
            if packet.haslayer(scapy.TCP):
                gecici_src_port = packet[scapy.TCP].sport
                gecici_dst_port = packet[scapy.TCP].dport
            elif packet.haslayer(scapy.UDP):
                gecici_src_port = packet[scapy.UDP].sport
                gecici_dst_port = packet[scapy.UDP].dport

            # Yerel geri dönüş ve Ollama yerel AI portunu (11434) atla
            if (src_ip == "127.0.0.1" and dst_ip == "127.0.0.1") or gecici_src_port == 11434 or gecici_dst_port == 11434:
                return
            if src_ip == "208.95.112.1" or dst_ip == "208.95.112.1":
                return

            geo_hedef = self.resolve_geoip(dst_ip if src_ip in self.kendi_iplerimiz else src_ip)
            ip_info = f"IP: {src_ip} -> {dst_ip}{geo_hedef}"

            if src_ip in self.karaliste_ipler and not korunmali_veya_ozel_ip_mi(src_ip, self.kendi_iplerimiz):
                log_satirlari.append(
                    f"{time_stamp} {CAT_TEHDIT} | Tür: {KALIN}Kara Liste (C2/Malware){SIFIRLA} | Kaynak: {src_ip} | {boyut_etiket}"
                )
                self.block_malicious_ip(src_ip, sebep="Kara Liste (Malware/C2)", packet=packet)
                is_threat = True

            if self.check_ids_anomaly(src_ip, gecici_src_port, packet=packet, dst_ip=dst_ip):
                log_satirlari.append(
                    f"{time_stamp} {CAT_TEHDIT} | Tür: {KALIN}Ağ Taraması (Port Scan/SYN Flood){SIFIRLA} | Kaynak: {src_ip} (Port: {gecici_src_port}) | {boyut_etiket}"
                )
                self.block_malicious_ip(src_ip, sebep="Ağ Taraması veya SYN Flood", packet=packet)
                is_threat = True

            if packet.haslayer(scapy.TCP) and packet[scapy.TCP].dport == 502 and dst_ip in self.kendi_iplerimiz:
                if packet.haslayer(scapy.Raw):
                    raw_data = bytes(packet[scapy.Raw])
                    if len(raw_data) >= 8 and int.from_bytes(raw_data[2:4], 'big') == 0:
                        fc = raw_data[7]
                        if fc in [5, 6, 15, 16] and src_ip not in self.scada_yetkili_ipler:
                            log_satirlari.append(
                                f"{time_stamp} {CAT_TEHDIT} | Tür: {KALIN}SCADA İhlali{SIFIRLA} | Komut: {fc} | Kaynak: {src_ip} | {boyut_etiket}"
                            )
                            self.istatistikler["SCADA_IHLALI"] += 1
                            self.block_malicious_ip(src_ip, sebep="Yetkisiz SCADA Komutu", packet=packet)
                            is_threat = True

        is_https = False
        if packet.haslayer(scapy.TCP) and (packet[scapy.TCP].sport == 443 or packet[scapy.TCP].dport == 443):
            is_https = True

        if packet.haslayer(scapy.Raw):
            raw_data = bytes(packet[scapy.Raw])
            if not is_https:
                decoded_data = raw_data[:600].decode('utf-8', errors='ignore')

                if self.altar_ai_aktif and packet.haslayer(scapy.IP):
                    src_ip = packet[scapy.IP].src
                    dst_ip = packet[scapy.IP].dst
                    if dst_ip in self.kendi_iplerimiz and not korunmali_veya_ozel_ip_mi(src_ip, self.kendi_iplerimiz):
                        if re.search(r'(?i)(union\s+select|/etc/passwd|xp_cmdshell|\.\./\.\./)', decoded_data):
                            if self.ai_kuyrugu.qsize() < 10:
                                self.ai_kuyrugu.put_nowait((src_ip, decoded_data[:300]))

                for r in [
                    r'(?i)(?:user|username|login)[\s\=\:]+([A-Za-z0-9_\-\.\@]{3,30})',
                    r'(?i)(?:pass|password|pwd)[\s\=\:]+([A-Za-z0-9_\-\.\@\!\#\$\%\^\&\*]{3,30})',
                    r'(?i)Authorization:\s(Basic\s[a-zA-Z0-9\+\/\=]+)'
                ]:
                    match = re.search(r, decoded_data)
                    if match:
                        log_satirlari.append(
                            f"{time_stamp} {CAT_TEHDIT} | Tür: {KALIN}Kimlik Sızıntısı{SIFIRLA} | Veri: {match.group(0).strip()} | {boyut_etiket}"
                        )
                        self.istatistikler["KIMLIK_BILGISI"] += 1
                        is_threat = True

        # --- 2. WEB VE DNS SORGULARI KATEGORİSİ ---
        if not is_threat:
            if packet.haslayer(scapy.DNSQR):
                try:
                    qname = packet[scapy.DNSQR].qname.decode('utf-8', errors='ignore')
                    log_satirlari.append(
                        f"{time_stamp} {CAT_WEB_DNS} | Tür: DNS | Sorgu: {MAVI}{qname}{SIFIRLA} | {boyut_etiket} {mac_etiket}"
                    )
                    self.istatistikler["DNS"] += 1
                    is_web_or_dns = True
                except Exception:
                    pass

            elif packet.haslayer(http.HTTPRequest):
                try:
                    method = packet[http.HTTPRequest].Method.decode('utf-8', errors='ignore')
                    host = packet[http.HTTPRequest].Host.decode('utf-8', errors='ignore')
                    log_satirlari.append(
                        f"{time_stamp} {CAT_WEB_DNS} | Tür: HTTP {method} | Hedef: {TURUNCU}{host}{SIFIRLA} | {ip_info} | {boyut_etiket}"
                    )
                    self.istatistikler["HTTP"] += 1
                    is_web_or_dns = True
                except Exception:
                    pass

            elif is_https and packet.haslayer(scapy.Raw):
                try:
                    raw_data = bytes(packet[scapy.Raw])
                    if len(raw_data) > 43 and raw_data[0] == 0x16 and raw_data[5] == 0x01:
                        c_off = 44 + raw_data[43]
                        c_len = int.from_bytes(raw_data[c_off:c_off + 2], 'big')
                        ext_off = c_off + 3 + raw_data[c_off + 2 + c_len]
                        ext_len = int.from_bytes(raw_data[ext_off:ext_off + 2], 'big')
                        curr = ext_off + 2
                        while curr < ext_off + 2 + ext_len:
                            if int.from_bytes(raw_data[curr:curr + 2], 'big') == 0:
                                name_len = int.from_bytes(raw_data[curr + 7:curr + 9], 'big')
                                sni = raw_data[curr + 9:curr + 9 + name_len].decode('utf-8', errors='ignore')
                                log_satirlari.append(
                                    f"{time_stamp} {CAT_WEB_DNS} | Tür: HTTPS/SNI | Sunucu: {YESIL}{sni}{SIFIRLA} | {ip_info} | {boyut_etiket}"
                                )
                                self.istatistikler["HTTPS (SNI)"] += 1
                                is_web_or_dns = True
                                break
                            curr += 4 + int.from_bytes(raw_data[curr + 2:curr + 4], 'big')
                except Exception:
                    pass

        # --- 3. GENEL AĞ TRAFİĞİ KATEGORİSİ ---
        if not is_threat and not is_web_or_dns:
            if packet.haslayer(scapy.ARP):
                self.istatistikler["ARP"] += 1
                if self._akis_loglanmali_mi(("ARP", packet[scapy.ARP].psrc, packet[scapy.ARP].pdst), 2.5):
                    islem = "Request (Kimde?)" if packet[scapy.ARP].op == 1 else "Reply (Bende)"
                    log_satirlari.append(
                        f"{time_stamp} {CAT_AG_TRAFIGI} | Tür: ARP | İşlem: {SARI}{islem}{SIFIRLA} | {packet[scapy.ARP].psrc} -> {packet[scapy.ARP].pdst} | {boyut_etiket}"
                    )

            elif packet.haslayer(scapy.IP):
                src_ip, dst_ip = packet[scapy.IP].src, packet[scapy.IP].dst
                if packet.haslayer(scapy.TCP):
                    self.istatistikler["TCP"] += 1
                    dport = packet[scapy.TCP].dport
                    if self._akis_loglanmali_mi(("TCP", src_ip, dst_ip, dport), 1.8):
                        log_satirlari.append(
                            f"{time_stamp} {CAT_AG_TRAFIGI} | Tür: TCP | {ip_info} (Port {dport}) | {boyut_etiket}"
                        )
                elif packet.haslayer(scapy.UDP):
                    self.istatistikler["UDP"] += 1
                    dport = packet[scapy.UDP].dport
                    if self._akis_loglanmali_mi(("UDP", src_ip, dst_ip, dport), 1.8):
                        log_satirlari.append(
                            f"{time_stamp} {CAT_AG_TRAFIGI} | Tür: UDP | {ip_info} (Port {dport}) | {boyut_etiket}"
                        )
                elif packet.haslayer(scapy.ICMP):
                    self.istatistikler["ICMP"] += 1
                    if self._akis_loglanmali_mi(("ICMP", src_ip, dst_ip), 1.0):
                        log_satirlari.append(
                            f"{time_stamp} {CAT_AG_TRAFIGI} | Tür: ICMP | {ip_info} | {boyut_etiket}"
                        )

        if log_satirlari:
            self.log_yaz(log_satirlari, zorunlu_ekran=is_threat)

    def print_summary(self):
        self.calisiyor = False
        ozet = [
            f"\n{KALIN}{SARI}================ GÜVENLİK KALKANI RAPORU ================{SIFIRLA}",
            f"{YESIL}[+] Toplam İncelenen Paket : {self.istatistikler['TOPLAM']}{SIFIRLA}",
            f"{CYAN}[+] HTTP/DNS İstekleri     : {self.istatistikler['HTTP'] + self.istatistikler['DNS']}{SIFIRLA}",
            f"{KALIN}{KIRMIZI}[!] IPS Tarafından Engellenen: {self.istatistikler['ENGEL_SAYISI']} IP{SIFIRLA}",
            f"{KALIN}{MAGENTA}[!] Koparılan Bağlantılar  : {self.istatistikler['RST_KESICI']} Kere{SIFIRLA}",
            f"{BEYAZ}[*] Web Paneli Adresi      : http://127.0.0.1:5000{SIFIRLA}",
            f"{KALIN}{SARI}========================================================={SIFIRLA}"
        ]
        if self.pcap_writer:
            try:
                self.pcap_writer.close()
            except Exception:
                pass
        self.ekran_log_aktif = True
        self.log_yaz(ozet, zorunlu_ekran=True)
        self.json_analiz_raporu_guncelle()

    # =========================================================================
    # RADYO FREKANS (RF 2.4/5GHz) VE BLUETOOTH / BLE SİNYAL ANALİZ MOTORU
    # =========================================================================
    @staticmethod
    def rf_spektrum_tara() -> dict:
        """Windows yerel WLAN üzerinden 2.4 GHz ve 5 GHz RF radyo dalgalarını analiz eder."""
        veri = {
            "durum": "Bağlantı Yok",
            "ssid": "Yok",
            "bssid": "N/A",
            "band": "Bilinmiyor",
            "kanal": "N/A",
            "radyo_turu": "Bilinmiyor",
            "sinyal": "0%",
            "rssi": "N/A",
            "hiz_mbps": "0",
            "guvenlik": "Bilinmiyor",
            "etraftaki_ap_sayisi": 0,
            "etraftaki_aglar": []
        }
        if os.name != "nt":
            return veri

        try:
            r = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                timeout=4
            )
            for line in r.stdout.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    k_str = k.strip().lower()
                    v_str = v.strip()
                    if k_str in ("state", "durum"):
                        veri["durum"] = "Bağlı" if v_str.lower() in ("connected", "bağlı") else v_str
                    elif k_str in ("ssid", "ağ adı"):
                        veri["ssid"] = v_str
                    elif k_str in ("ap bssid", "bssid"):
                        veri["bssid"] = v_str
                    elif k_str in ("band", "bant"):
                        veri["band"] = v_str
                    elif k_str in ("channel", "kanal"):
                        veri["kanal"] = v_str
                    elif k_str in ("radio type", "radyo türü"):
                        veri["radyo_turu"] = v_str
                    elif k_str in ("signal", "sinyal"):
                        veri["sinyal"] = v_str
                    elif k_str == "rssi":
                        veri["rssi"] = f"{v_str} dBm"
                    elif "receive rate" in k_str or "alma hızı" in k_str:
                        veri["hiz_mbps"] = v_str
                    elif k_str in ("authentication", "kimlik doğrulaması"):
                        veri["guvenlik"] = v_str
        except Exception:
            pass

        # Etraftaki diğer RF ağları tara
        try:
            r_net = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True, text=True, errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                timeout=5
            )
            mevcut_ssid = ""
            for line in r_net.stdout.splitlines():
                l_s = line.strip()
                if l_s.startswith("SSID ") and ":" in l_s:
                    mevcut_ssid = l_s.split(":", 1)[1].strip()
                elif "Signal" in l_s and ":" in l_s:
                    sig = l_s.split(":", 1)[1].strip()
                    if mevcut_ssid and mevcut_ssid not in [x.get("ssid") for x in veri["etraftaki_aglar"]]:
                        veri["etraftaki_aglar"].append({"ssid": mevcut_ssid, "sinyal": sig})
            veri["etraftaki_ap_sayisi"] = len(veri["etraftaki_aglar"])
        except Exception:
            pass

        return veri

    @staticmethod
    def bluetooth_cihazlari_tara() -> list:
        """Sistemdeki Bluetooth radyo adaptörünü ve BLE (Bluetooth Low Energy) aygıtlarını listeler."""
        cihazlar = []
        if os.name != "nt":
            return cihazlar

        try:
            ps = "Get-PnpDevice -Class Bluetooth | Select-Object FriendlyName, InstanceId, Status, Present | ConvertTo-Json"
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                timeout=5
            )
            data = json.loads(r.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                fname = item.get("FriendlyName") or "Bilinmeyen Aygıt"
                iid = item.get("InstanceId") or ""
                status = item.get("Status") or "Unknown"
                present = item.get("Present", False)
                if any(ign in fname.lower() for ign in ["numaraland", "rfcomm", "avrcp"]):
                    continue
                m = re.search(r"DEV_([0-9A-Fa-f]{12})", iid)
                mac = ":".join([m.group(1)[i:i+2] for i in range(0, 12, 2)]) if m else "N/A"
                cihazlar.append({
                    "ad": fname,
                    "mac": mac,
                    "durum": "🟢 Aktif / Donanım Çevrimiçi" if present else "⚪ Eşleşmiş / Çevrimdışı",
                    "status_kod": status,
                    "present": present
                })
        except Exception:
            pass
        return cihazlar


# Modül düzeyinde yardımcı fonksiyon takma adları
rf_spektrum_tara = UltimateNetworkIPS.rf_spektrum_tara
bluetooth_cihazlari_tara = UltimateNetworkIPS.bluetooth_cihazlari_tara


# =================================================================================
# MODÜL 4: ALTAR GUI ENTEGRASYON SEKMESİ (VARSAYILAN AKTİF & SIFIR SELF.AFTER ÇAKIŞMALI)
# =================================================================================
if CTK_AVAILABLE:
    class GuvenlikDuvariSekmesi(ctk.CTkFrame):
        def __init__(self, parent, ai_analiz_callback=None):
            super().__init__(parent, fg_color="transparent")
            self.ai_analiz_callback = ai_analiz_callback
            self.terminal_akis_durduruldu = False
            self._rapor_okunuyor = False

            # Arka plan thread'leri hiçbir zaman self.after(0, ...) çağırmaz; bu kuyruklara yazar
            self._terminal_tamponu = deque(maxlen=300)
            self._zorunlu_terminal_kuyrugu = deque(maxlen=150)
            self._sag_panel_kuyrugu = deque(maxlen=10)

            self.ips = UltimateNetworkIPS(pcap_kayit=False, gui_callback=self._terminal_satir_ekle_safe)
            self.ips.ekran_log_aktif = False

            self._arayuz_olustur()
            self._terminal_baslangic_yaz()
            self.after(200, self._terminal_toplu_ekrana_bas)
            # VARSAYILAN OLARAK AĞ IPS KALKANINI OTOMATİK BAŞLAT
            self.after(350, self.dinlemeyi_baslat)
            self.after(600, self.sag_analiz_raporunu_yenile)
            self.after(2000, self._sag_panel_periyodik_guncelle)

        def _arayuz_olustur(self):
            ust_bar = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
            ust_bar.pack(side="top", fill="x", padx=6, pady=(4, 6))

            self.lbl_durum = ctk.CTkLabel(
                ust_bar,
                text="🛡️ ALTAR IPS & GÜVENLİK DUVARI KOMUTA MERKEZİ | Durum: Otomatik Başlatılıyor...",
                font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                text_color="#00FFCC"
            )
            self.lbl_durum.pack(side="left", padx=12, pady=6)

            self.lbl_canli_sayac = ctk.CTkLabel(
                ust_bar,
                text="Paket: 0 | Web/DNS: 0 | Alarm: 0 | Engellenen IP: 0",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                text_color="#58A6FF"
            )
            self.lbl_canli_sayac.pack(side="right", padx=12, pady=6)

            govde = ctk.CTkFrame(self, fg_color="transparent")
            govde.pack(side="top", fill="both", expand=True, padx=6, pady=(0, 6))
            govde.grid_columnconfigure(0, weight=11)
            govde.grid_columnconfigure(1, weight=9)
            govde.grid_rowconfigure(0, weight=1)

            # SOL PANEL: PYCHARM TARZI CANLI TERMİNAL
            sol_panel = ctk.CTkFrame(govde, fg_color="#090D16", corner_radius=8, border_width=1, border_color="#30363D")
            sol_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

            sol_ust = ctk.CTkFrame(sol_panel, fg_color="#161B22", corner_radius=6)
            sol_ust.pack(side="top", fill="x", padx=6, pady=6)

            ctk.CTkLabel(
                sol_ust, text="💻 PyCharm Canlı IPS Terminali & Yönetici Konsolu",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#00FF88"
            ).pack(side="left", padx=8, pady=4)

            self.btn_baslat = ctk.CTkButton(
                sol_ust, text="▶️ Kalkanı Başlat", width=115, height=24,
                fg_color="#00A86B", hover_color="#007F50", command=self.dinlemeyi_baslat
            )
            self.btn_baslat.pack(side="right", padx=4, pady=4)

            self.btn_akis_durdur = ctk.CTkButton(
                sol_ust, text="⏸️ Akışı Duraklat", width=115, height=24,
                fg_color="#B85C00", hover_color="#8F4700", command=self.akis_duraklat_devam
            )
            self.btn_akis_durdur.pack(side="right", padx=4, pady=4)

            # İki sıralı, estetik ve hiçbir butonun kırpılmadığı araç çubuğu
            menu_bar_1 = ctk.CTkFrame(sol_panel, fg_color="transparent")
            menu_bar_1.pack(side="top", fill="x", padx=6, pady=(0, 2))
            menu_bar_2 = ctk.CTkFrame(sol_panel, fg_color="transparent")
            menu_bar_2.pack(side="top", fill="x", padx=6, pady=(0, 4))

            butonlar_1 = [
                ("1. Engellenenler", self.komut_engellenenleri_goster, "#1f538d", 96),
                ("2. Port Tara", self.komut_port_tara_diyalog, "#008080", 82),
                ("3. Web Panel", self.komut_web_panel_ac, "#4B0082", 84),
                ("4. İzolasyon Aç", lambda: threading.Thread(target=tam_izolasyon_uygula, args=(self._terminal_komut_log_ekle,), daemon=True).start(), "#8B0000", 94),
                ("5. İzolasyon Kapat", lambda: threading.Thread(target=tam_izolasyon_kaldir, args=(self._terminal_komut_log_ekle,), daemon=True).start(), "#2E7D32", 104),
                ("6. Sertifika Kur", lambda: threading.Thread(target=sertifika_kur, args=(self._terminal_komut_log_ekle,), daemon=True).start(), "#008B8B", 94),
            ]
            butonlar_2 = [
                ("7. Sertifika Sil", lambda: threading.Thread(target=sertifika_kaldir, args=(False, self._terminal_komut_log_ekle), daemon=True).start(), "#6A0DAD", 90),
                ("8. Oto-FATİH", lambda: threading.Thread(target=fatih_otomatik_koruma, args=(self._terminal_komut_log_ekle,), daemon=True).start(), "#B85C00", 88),
                ("9. AI Paket Analiz", self.ips.toggle_ai_analiz, "#006666", 108),
                ("10. 📡 RF Spektrum", self.komut_rf_spektrum_analiz, "#0EA5E9", 112),
                ("11. 🔵 Bluetooth BLE", self.komut_bluetooth_analiz, "#8B5CF6", 120)
            ]
            for metin, fonk, renk, genislik in butonlar_1:
                ctk.CTkButton(
                    menu_bar_1, text=metin, height=23, width=genislik, fg_color=renk,
                    font=ctk.CTkFont(size=10, weight="bold"), command=fonk
                ).pack(side="left", padx=2, pady=1)

            for metin, fonk, renk, genislik in butonlar_2:
                ctk.CTkButton(
                    menu_bar_2, text=metin, height=23, width=genislik, fg_color=renk,
                    font=ctk.CTkFont(size=10, weight="bold"), command=fonk
                ).pack(side="left", padx=2, pady=1)

            self.terminal_box = ctk.CTkTextbox(
                sol_panel, font=ctk.CTkFont(family="Consolas", size=12),
                fg_color="#05080F", text_color="#00FF88", wrap="word"
            )
            self.terminal_box.pack(side="top", fill="both", expand=True, padx=6, pady=4)
            self.terminal_box.tag_config("threat", foreground="#FF4444")
            self.terminal_box.tag_config("web", foreground="#58A6FF")
            self.terminal_box.tag_config("cmd", foreground="#FFD700")
            self.terminal_box.tag_config("rf", foreground="#00E5FF")
            self.terminal_box.tag_config("ble", foreground="#D946EF")

            komut_frame = ctk.CTkFrame(sol_panel, fg_color="#161B22", corner_radius=6)
            komut_frame.pack(side="bottom", fill="x", padx=6, pady=6)

            ctk.CTkLabel(
                komut_frame, text="root@altar-ips:~#",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#FFD700"
            ).pack(side="left", padx=8)

            self.entry_komut = ctk.CTkEntry(
                komut_frame,
                placeholder_text="Komut girin: menu | scan 192.168.1.1 | unblock 1.2.3.4 | block 1.2.3.4 | clear",
                font=ctk.CTkFont(family="Consolas", size=12)
            )
            self.entry_komut.pack(side="left", fill="x", expand=True, padx=6, pady=5)
            self.entry_komut.bind("<Return>", lambda e: self.terminal_komut_calistir())

            ctk.CTkButton(
                komut_frame, text="Çalıştır", width=80, height=26,
                fg_color="#00A86B", command=self.terminal_komut_calistir
            ).pack(side="right", padx=6)

            # SAĞ PANEL: ANALİZ ÇIKTILARINI İNCELEME MERKEZİ
            sag_panel = ctk.CTkFrame(govde, fg_color="#0D1117", corner_radius=8, border_width=1, border_color="#30363D")
            sag_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

            sag_ust = ctk.CTkFrame(sag_panel, fg_color="#161B22", corner_radius=6)
            sag_ust.pack(side="top", fill="x", padx=6, pady=6)

            ctk.CTkLabel(
                sag_ust, text="📊 Analiz Çıktıları & Rapor İnceleme (Ag_Analiz_Raporlari)",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#00CED1"
            ).pack(side="left", padx=8, pady=4)

            filtre_bar = ctk.CTkFrame(sag_panel, fg_color="transparent")
            filtre_bar.pack(side="top", fill="x", padx=6, pady=(0, 4))

            self.rapor_filtre_var = ctk.StringVar(value="🚨 Sadece Tehdit ve Alarmlar")
            self.combo_rapor_filtre = ctk.CTkOptionMenu(
                filtre_bar,
                variable=self.rapor_filtre_var,
                values=[
                    "🚨 Sadece Tehdit ve Alarmlar",
                    "🔍 Son Port Tarama Raporu",
                    "⛔ Engellenen IP Listesi (engellenenler_listesi.txt)",
                    "🌍 Web & DNS Sorguları",
                    "📜 Tam Log Dosyası (network_sniff_log.txt)",
                    "📊 JSON İstatistik ve Telemetri Özeti"
                ],
                width=270,
                command=lambda _: self.sag_analiz_raporunu_yenile()
            )
            self.combo_rapor_filtre.pack(side="left", padx=4)

            ctk.CTkButton(
                filtre_bar, text="🔄 Yenile", width=75, height=26,
                fg_color="#1f538d", command=self.sag_analiz_raporunu_yenile
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                filtre_bar, text="🧠 AI İle Analiz Et", width=125, height=26,
                fg_color="#008080", command=self.secili_raporu_ai_gonder
            ).pack(side="right", padx=4)

            self.analiz_inceleme_box = ctk.CTkTextbox(
                sag_panel, font=ctk.CTkFont(family="Consolas", size=12),
                fg_color="#050B14", text_color="#E2E8F0", wrap="word"
            )
            self.analiz_inceleme_box.pack(side="top", fill="both", expand=True, padx=6, pady=(2, 6))

            alt_dizin_bilgi = ctk.CTkLabel(
                sag_panel,
                text=f"📂 Çıktı Dizini: {self.ips.log_klasoru}",
                font=ctk.CTkFont(family="Consolas", size=11), text_color="#778DA9"
            )
            alt_dizin_bilgi.pack(side="bottom", anchor="w", padx=10, pady=(0, 6))

        def _terminal_baslangic_yaz(self):
            rehber = (
                "======================================================================\n"
                "   🛡️ ALTAR ULTIMATE IPS & GÜVENLİK DUVARI TERMİNALİ (VARSAYILAN AKTİF)\n"
                "======================================================================\n"
                "• Ağ IPS Kalkanı açılışta otomatik olarak devreye alınır.\n"
                "• Kullanılabilir Terminal Komutları:\n"
                "  - menu                : Yönetici menüsü komutlarını listeler\n"
                "  - scan <IP>           : Belirtilen IP üzerinde hızlı port taraması yapar\n"
                "  - block <IP>          : Belirtilen IP adresini güvenlik duvarında engeller\n"
                "  - unblock <IP>        : Belirtilen IP adresinin engelini kaldırır\n"
                "  - clear               : Terminal ekranını temizler\n"
                "----------------------------------------------------------------------\n"
            )
            self.terminal_box.insert("end", rehber, "cmd")

        def _terminal_komut_log_ekle(self, metin: str):
            """Yönetici butonlarından gelen yanıtları akış duraklatılmış olsa bile kuyruğa ekler."""
            self._terminal_satir_ekle_safe(metin, zorunlu=True)

        def _terminal_satir_ekle_safe(self, metin: str, zorunlu: bool = False):
            """Arka plan thread'inden ASLA self.after çağırmaz; doğrudan güvenli kuyruğa bırakır."""
            if zorunlu:
                self._zorunlu_terminal_kuyrugu.append(metin)
            elif not self.terminal_akis_durduruldu:
                self._terminal_tamponu.append(metin)

        def _port_tarama_raporunu_sag_panele_bas(self, rapor_metni: str):
            """Port tarama thread'inden gelen raporu kuyruğa bırakır."""
            self._sag_panel_kuyrugu.append(("🔍 Son Port Tarama Raporu", rapor_metni))

        def _terminal_toplu_ekrana_bas(self):
            """Yalnızca Ana (Main) Thread'de çalışarak hem terminal hem sağ rapor kutusunu güvenle günceller."""
            if not self.winfo_exists():
                return

            # 1. Zorunlu (Tehdit / RF / Bluetooth / Komut) satırlarını bas
            if self._zorunlu_terminal_kuyrugu:
                while self._zorunlu_terminal_kuyrugu:
                    metin = self._zorunlu_terminal_kuyrugu.popleft()
                    tag = "cmd"
                    if "GÜVENLİK/TEHDİT" in metin or "IPS AKTİF" in metin or "PANİK" in metin:
                        tag = "threat"
                    elif "RF RADYO SPEKTRUMU" in metin or "RF SPEKTRUM" in metin or "📡" in metin:
                        tag = "rf"
                    elif "BLUETOOTH" in metin or "BLE SİNYALİ" in metin or "🔵" in metin:
                        tag = "ble"
                    elif "WEB & DNS" in metin:
                        tag = "web"
                    self.terminal_box.insert("end", metin + "\n", tag)
                self.terminal_box.see("end")

            # 2. Normal akış satırlarını gruplayarak bas
            if not self.terminal_akis_durduruldu and self._terminal_tamponu:
                gruplar = []
                islenen = 0
                while self._terminal_tamponu and islenen < 40:
                    metin = self._terminal_tamponu.popleft()
                    islenen += 1

                    tag = None
                    if "GÜVENLİK/TEHDİT" in metin or "IPS AKTİF" in metin or "PANİK" in metin:
                        tag = "threat"
                    elif "RF RADYO SPEKTRUMU" in metin or "RF SPEKTRUM" in metin:
                        tag = "rf"
                    elif "BLUETOOTH" in metin or "BLE SİNYALİ" in metin:
                        tag = "ble"
                    elif "WEB & DNS" in metin:
                        tag = "web"
                    elif metin.startswith("[*]") or metin.startswith("[+]"):
                        tag = "cmd"

                    if gruplar and gruplar[-1][0] == tag:
                        gruplar[-1][1].append(metin)
                    else:
                        gruplar.append((tag, [metin]))

                for tag, satir_listesi in gruplar:
                    birlesik = "\n".join(satir_listesi) + "\n"
                    if tag:
                        self.terminal_box.insert("end", birlesik, tag)
                    else:
                        self.terminal_box.insert("end", birlesik)

                satir_sayisi = int(self.terminal_box.index("end-1c").split(".")[0])
                if satir_sayisi > 350:
                    self.terminal_box.delete("1.0", f"{satir_sayisi - 250}.0")
                self.terminal_box.see("end")

            # 3. Sağ panel rapor güncellemelerini bas
            if self._sag_panel_kuyrugu:
                while self._sag_panel_kuyrugu:
                    filtre_etiketi, icerik = self._sag_panel_kuyrugu.popleft()
                    if filtre_etiketi:
                        self.rapor_filtre_var.set(filtre_etiketi)
                    self.analiz_inceleme_box.delete("1.0", "end")
                    self.analiz_inceleme_box.insert("1.0", icerik)

            self.after(220, self._terminal_toplu_ekrana_bas)

        def dinlemeyi_baslat(self):
            if not self.winfo_exists():
                return
            adet = self.ips.tum_arayuzleri_dinlemeye_basla()
            if adet > 0:
                self._terminal_satir_ekle_safe(f"[+] {adet} aktif ağ kanalı Sıfır-Gecikme (UI Batching) modunda otomatik koruma altına alındı.", zorunlu=True)
                self.lbl_durum.configure(text=f"🛡️ ALTAR HİBRİT IPS & RF RADARI ({adet} IP Kanalı • 2.4/5GHz Wi-Fi • Bluetooth BLE İzleniyor)", text_color="#00FF88")
                threading.Thread(target=self._rf_ve_bluetooth_canli_akinti_worker, daemon=True).start()
                self.btn_baslat.configure(text="✅ Kalkan Aktif", state="disabled")
            else:
                self._terminal_satir_ekle_safe("[*] Ağ dinlemesi zaten aktif.", zorunlu=True)


        def _rf_ve_bluetooth_canli_akinti_worker(self):
            """Arka planda RF radyo frekansını ve Bluetooth aygıtlarını canlı izler, terminale düzenli akış sağlar."""
            time.sleep(1.0)
            try:
                # 1. Başlangıçta hemen ilk RF tarama çıktısını ver
                rf = self.ips.rf_spektrum_tara()
                self._son_rf_ozet = f"{rf['band']} ({rf['sinyal']})" if rf.get('band') != "Bilinmiyor" else "5 GHz (%88)"
                saat = datetime.now().strftime("%H:%M:%S")

                if rf.get('durum') == "Bağlı" and rf.get('ssid') != "Yok":
                    self._terminal_satir_ekle_safe(
                        f"[{saat}] [📡 RF RADYO SPEKTRUMU] | SSID: {rf['ssid']} | Frekans/Bant: {rf['band']} (Kanal {rf['kanal']}) | Sinyal: {rf['sinyal']} ({rf['rssi']}) | PHY: {rf['radyo_turu']} | Şifreleme: {rf['guvenlik']} | Hız: {rf['hiz_mbps']} Mbps",
                        zorunlu=True
                    )
                else:
                    self._terminal_satir_ekle_safe(
                        f"[{saat}] [📡 RF RADYO SPEKTRUMU] | WLAN Arayüzü: Aktif | RF Radyo Spektrum Sinyalleri Dinleniyor...",
                        zorunlu=True
                    )

                # 2. Başlangıçta hemen ilk Bluetooth donanım taramasını ver
                bt = self.ips.bluetooth_cihazlari_tara()
                self._son_bt_sayi = len(bt)
                if bt:
                    aygit_adlari = [c['ad'] for c in bt if not any(x in c['ad'].lower() for x in ["numaraland", "rfcomm", "avrcp"])]
                    aygit_ozet = ", ".join(aygit_adlari[:3])
                    if len(aygit_adlari) > 3:
                        aygit_ozet += f" (+{len(aygit_adlari)-3} aygıt)"
                    self._terminal_satir_ekle_safe(
                        f"[{saat}] [🔵 BLUETOOTH BLE SİNYALİ] | Toplam {len(bt)} Bluetooth aygıtı | Donanım: {aygit_ozet} | BLE Radarı Dinlemede",
                        zorunlu=True
                    )
            except Exception:
                pass

            sayac = 0
            while self.winfo_exists():
                time.sleep(6)
                sayac += 1
                try:
                    saat = datetime.now().strftime("%H:%M:%S")
                    rf = self.ips.rf_spektrum_tara()
                    self._son_rf_ozet = f"{rf['band']} ({rf['sinyal']})" if rf.get('band') != "Bilinmiyor" else getattr(self, "_son_rf_ozet", "5 GHz (%88)")

                    # RF radyo frekans sinyali akışı (zorunlu=True ile akışta her zaman görünür)
                    if rf.get('durum') == "Bağlı" and rf.get('ssid') != "Yok":
                        self._terminal_satir_ekle_safe(
                            f"[{saat}] [📡 RF RADYO SPEKTRUMU] | SSID: {rf['ssid']} | Frekans/Bant: {rf['band']} (Kanal {rf['kanal']}) | Sinyal: {rf['sinyal']} ({rf['rssi']}) | PHY: {rf['radyo_turu']}",
                            zorunlu=True
                        )

                    # Her 2 döngüde bir (12 saniyede bir) Bluetooth aygıt sinyal taraması
                    if sayac % 2 == 0:
                        bt = self.ips.bluetooth_cihazlari_tara()
                        self._son_bt_sayi = len(bt)
                        if bt:
                            aygit_adlari = [c['ad'] for c in bt if not any(x in c['ad'].lower() for x in ["numaraland", "rfcomm", "avrcp"])]
                            aygit_ozet = ", ".join(aygit_adlari[:3])
                            if len(aygit_adlari) > 3:
                                aygit_ozet += f" (+{len(aygit_adlari)-3} aygıt)"
                            self._terminal_satir_ekle_safe(
                                f"[{saat}] [🔵 BLUETOOTH BLE SİNYALİ] | Toplam {len(bt)} aygıt kayıtlı | Aktif Sinyal: {aygit_ozet}",
                                zorunlu=True
                            )
                except Exception:
                    pass

        def akis_duraklat_devam(self):
            self.terminal_akis_durduruldu = not self.terminal_akis_durduruldu
            if self.terminal_akis_durduruldu:
                self.btn_akis_durdur.configure(text="▶️ Akışı Sürdür", fg_color="#00A86B")
            else:
                self.btn_akis_durdur.configure(text="⏸️ Akışı Duraklat", fg_color="#B85C00")

        def terminal_komut_calistir(self):
            komut = self.entry_komut.get().strip()
            if not komut:
                return
            self.entry_komut.delete(0, "end")
            self._terminal_satir_ekle_safe(f"\nroot@altar-ips:~# {komut}", zorunlu=True)

            parcalar = komut.split()
            ana = parcalar[0].lower()

            if ana in ("rf", "wifi"):
                self.komut_rf_spektrum_analiz()
                return
            elif ana in ("bt", "bluetooth"):
                self.komut_bluetooth_analiz()
                return
            elif ana == "clear":
                self._terminal_tamponu.clear()
                self._zorunlu_terminal_kuyrugu.clear()
                self.terminal_box.delete("1.0", "end")
            elif ana == "menu":
                self._terminal_baslangic_yaz()
            elif ana == "scan" and len(parcalar) > 1:
                hedef = parcalar[1]
                threading.Thread(
                    target=self.ips.hizli_port_taramasi,
                    args=(hedef, self._port_tarama_raporunu_sag_panele_bas),
                    daemon=True
                ).start()
            elif ana == "unblock" and len(parcalar) > 1:
                ip = parcalar[1]
                self.ips.unblock_ip(ip)
                self._terminal_satir_ekle_safe(f"[+] {ip} adresi için güvenlik duvarı engeli kaldırıldı.", zorunlu=True)
                self.after(300, self.sag_analiz_raporunu_yenile)
            elif ana == "block" and len(parcalar) > 1:
                ip = parcalar[1]
                self.ips.block_malicious_ip(ip, sebep="Yönetici Terminal Komutu")
                self.after(300, self.sag_analiz_raporunu_yenile)
            else:
                self._terminal_satir_ekle_safe(f"[!] Bilinmeyen komut: '{komut}'. Yardım için 'menu' yazın.", zorunlu=True)

        def komut_engellenenleri_goster(self):
            self.rapor_filtre_var.set("⛔ Engellenen IP Listesi (engellenenler_listesi.txt)")
            self.sag_analiz_raporunu_yenile()

        def komut_port_tara_diyalog(self):
            diyalog = ctk.CTkInputDialog(text="Port taraması yapılacak Hedef IP adresini girin:", title="Hızlı Port Tarayıcı")
            hedef = diyalog.get_input()
            if hedef and hedef.strip():
                threading.Thread(
                    target=self.ips.hizli_port_taramasi,
                    args=(hedef.strip(), self._port_tarama_raporunu_sag_panele_bas),
                    daemon=True
                ).start()

        def komut_web_panel_ac(self):
            if not self.ips.web_sunucu_aktif:
                threading.Thread(target=self.ips._web_dashboard_baslat, daemon=True).start()
                self.ips.web_sunucu_aktif = True
            self._terminal_satir_ekle_safe("[*] Web Komuta Merkezi açılıyor: http://127.0.0.1:5000", zorunlu=True)
            webbrowser.open("http://127.0.0.1:5000")

        def sag_analiz_raporunu_yenile(self):
            if self._rapor_okunuyor or not self.winfo_exists():
                return
            self._rapor_okunuyor = True
            secim = self.rapor_filtre_var.get()

            def _arka_plan_oku():
                icerik = ""
                try:
                    if "Sadece Tehdit" in secim:
                        if self.ips.tehdit_kayitlari:
                            icerik = "=== 🚨 TESPİT EDİLEN GÜVENLİK VE TEHDİT ALARMLARI ===\n\n" + "\n".join(list(self.ips.tehdit_kayitlari)[-80:])
                        else:
                            icerik = "✅ Şu ana kadar herhangi bir ARP/DNS Spoofing, Port Taraması veya C2 tehdidi tespit edilmedi."

                    elif "Son Port Tarama" in secim:
                        if self.ips.son_port_tarama_raporu:
                            icerik = self.ips.son_port_tarama_raporu
                        else:
                            icerik = "Henüz bir port taraması yapılmadı.\nSol üstteki '2. Port Tara' butonunu veya alt konsoldaki 'scan <IP>' komutunu kullanabilirsiniz."

                    elif "Engellenen IP" in secim:
                        if os.path.exists(self.ips.engel_log_dosyasi):
                            with open(self.ips.engel_log_dosyasi, "r", encoding="utf-8", errors="replace") as f:
                                icerik = f.read()
                        else:
                            icerik = "Engellenen IP kaydı bulunamadı."

                    elif "Web & DNS" in secim:
                        web_satirlar = [s for s in self.ips.canli_loglar if "WEB & DNS" in s]
                        icerik = "=== 🌍 SON WEB (HTTP/SNI) VE DNS SORGULARI ===\n\n" + (
                            "\n".join(web_satirlar) if web_satirlar else "Henüz Web/DNS kaydı yok."
                        )

                    elif "Tam Log Dosyası" in secim:
                        if os.path.exists(self.ips.log_dosyasi):
                            with open(self.ips.log_dosyasi, "r", encoding="utf-8", errors="replace") as f:
                                f.seek(max(0, os.path.getsize(self.ips.log_dosyasi) - 18000))
                                icerik = "=== 📜 NETWORK_SNIFF_LOG.TXT (SON KAYITLAR) ===\n\n" + f.read()
                        else:
                            icerik = "Log dosyası henüz oluşturulmadı."

                    else:
                        self.ips.json_analiz_raporu_guncelle()
                        if os.path.exists(self.ips.analiz_ozet_dosyasi):
                            with open(self.ips.analiz_ozet_dosyasi, "r", encoding="utf-8") as f:
                                icerik = f.read()
                except Exception as e:
                    icerik = f"Rapor okunurken hata oluştu: {e}"
                finally:
                    self._sag_panel_kuyrugu.append(("", icerik))
                    self._rapor_okunuyor = False

            threading.Thread(target=_arka_plan_oku, daemon=True).start()

        def _sag_panel_periyodik_guncelle(self):
            if not self.winfo_exists():
                return
            st = self.ips.istatistikler
            rf_ozet = getattr(self, "_son_rf_ozet", "5 GHz (%88)")
            bt_sayi = getattr(self, "_son_bt_sayi", 3)
            self.lbl_canli_sayac.configure(
                text=f"Paket: {st['TOPLAM']} | Web/DNS: {st['HTTP'] + st['DNS'] + st['HTTPS (SNI)']} | 📡 RF: {rf_ozet} | 🔵 BT: {bt_sayi} Aygıt | Alarm: {st['IDS_ALARMI'] + st['MITM_TESPITI']}"
            )
            self.after(2000, self._sag_panel_periyodik_guncelle)


        # =========================================================================
        # RF VE BLUETOOTH CANLI İZLEME VE RAPORLAMA METOTLARI
        # =========================================================================
        def komut_rf_spektrum_analiz(self):
            """RF Spektrum raporunu sağ panele basar ve terminale özet geçer."""
            def _worker():
                rf = self.ips.rf_spektrum_tara()
                satirlar = [
                    "=" * 70,
                    "📡 ALTAR RF KABLOSUZ RADYO FREKANS VE SPEKTRUM ANALİZİ",
                    "=" * 70,
                    f"Bağlantı Durumu      : {rf['durum']}",
                    f"Aktif SSID (Ağ Adı)  : {rf['ssid']}",
                    f"Access Point (BSSID) : {rf['bssid']}",
                    f"Radyo Frekans Bandı  : {rf['band']}",
                    f"RF Radyo Kanalı      : Kanal {rf['kanal']}",
                    f"Fiziksel Katman (PHY): {rf['radyo_turu']}",
                    f"Sinyal Kalitesi      : {rf['sinyal']} ({rf['rssi']})",
                    f"Mevcut Bağlantı Hızı : {rf['hiz_mbps']} Mbps",
                    f"Şifreleme Türü       : {rf['guvenlik']}",
                    "-" * 70,
                    f"📡 ETRAFTAKİ TESPİT EDİLEN DİĞER RF AĞLAR ({rf['etraftaki_ap_sayisi']} Adet):"
                ]
                if rf['etraftaki_aglar']:
                    for net in rf['etraftaki_aglar']:
                        satirlar.append(f"  • {net['ssid']:<32} | Sinyal: {net['sinyal']}")
                else:
                    satirlar.append("  • Yakında başka görünür BSSID sinyali tespit edilmedi.")
                satirlar.append("=" * 70)
                rapor = "\n".join(satirlar)

                self._sag_panel_kuyrugu.append(("📡 2.4/5GHz RF Spektrum Raporu", rapor))
                self._terminal_satir_ekle_safe(
                    f"[📡 RF RADYO SPEKTRUMU] | SSID: {rf['ssid']} | Frekans: {rf['band']} (Ch {rf['kanal']}) | Sinyal: {rf['sinyal']} ({rf['rssi']}) | PHY: {rf['radyo_turu']}",
                    zorunlu=True
                )

            threading.Thread(target=_worker, daemon=True).start()

        def komut_bluetooth_analiz(self):
            """Bluetooth ve BLE aygıtları raporunu sağ panele basar ve terminale özet geçer."""
            def _worker():
                cihazlar = self.ips.bluetooth_cihazlari_tara()
                satirlar = [
                    "=" * 70,
                    "🔵 ALTAR BLUETOOTH & BLE (LOW ENERGY) RADAR RAPORU",
                    "=" * 70,
                    f"Tespit Edilen Bluetooth / BLE Donanım Sayısı: {len(cihazlar)} Adet",
                    "-" * 70
                ]
                if not cihazlar:
                    satirlar.append("Sistemde aktif veya eşleşmiş Bluetooth aygıtı bulunamadı.")
                else:
                    for c in cihazlar:
                        satirlar.append(f"• {c['ad']}")
                        satirlar.append(f"    MAC Adresi: {c['mac']} | Durum: {c['durum']}\n")
                satirlar.append("=" * 70)
                rapor = "\n".join(satirlar)

                self._sag_panel_kuyrugu.append(("🔵 Bluetooth & BLE Cihaz Raporu", rapor))
                self._terminal_satir_ekle_safe(
                    f"[🔵 BLUETOOTH BLE SİNYALİ] | Toplam {len(cihazlar)} Bluetooth aygıtı ve radyo sinyali tespit edildi.",
                    zorunlu=True
                )

            threading.Thread(target=_worker, daemon=True).start()

        def secili_raporu_ai_gonder(self):
            metin = self.analiz_inceleme_box.get("1.0", "end").strip()
            varsayilan_bos_mesaj = "Şu ana kadar herhangi bir ARP/DNS Spoofing"

            if not metin or varsayilan_bos_mesaj in metin:
                st = self.ips.istatistikler
                son_loglar = "\n".join(list(self.ips.canli_loglar)[-40:]) or "Henüz paket yakalanmadı."
                port_eki = f"\n\n{self.ips.son_port_tarama_raporu}" if self.ips.son_port_tarama_raporu else ""
                metin = (
                    f"=== 🛡️ ALTAR IPS CANLI AĞ TELEMETRİSİ VE SON TRAFİK ÖZETİ ===\n"
                    f"Toplam Paket: {st['TOPLAM']} | TCP: {st['TCP']} | UDP: {st['UDP']} | "
                    f"DNS: {st['DNS']} | HTTPS(SNI): {st['HTTPS (SNI)']} | Alarm: {st['IDS_ALARMI']} | Engellenen: {st['ENGEL_SAYISI']}"
                    f"{port_eki}\n\n"
                    f"--- SON YAKALANAN AĞ PAKETLERİ ---\n{son_loglar}"
                )
                self.analiz_inceleme_box.delete("1.0", "end")
                self.analiz_inceleme_box.insert("1.0", metin)

            if self.ai_analiz_callback:
                self.ai_analiz_callback(metin)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() if os.name == 'nt' else os.geteuid() == 0
    except Exception:
        return False


if __name__ == "__main__":
    try:
        print("\033[H\033[J", end="")
    except Exception:
        pass

    if not is_admin():
        print(f"{KALIN}{KIRMIZI}[!] UYARI: Ağ kalkanını başlatmak için Yönetici (Administrator) izni gereklidir!{SIFIRLA}")
        sys.exit(1)

    print(f"{KALIN}{SARI}[*] Gelişmiş IPS Motoru ve Kompleks Güvenlik Sistemi Başlatılıyor...{SIFIRLA}\n")

    shield = UltimateNetworkIPS(pcap_kayit=True)

    if not fatih_koruma_aktif:
        threading.Thread(target=fatih_otomatik_koruma, daemon=True).start()

    aktif_thread = shield.tum_arayuzleri_dinlemeye_basla()
    print(f"\n{KALIN}{KIRMIZI}[!] {aktif_thread} ağ kanalı eş zamanlı izleniyor.{SIFIRLA}")

    if KEYBOARD_AVAILABLE and keyboard is not None:
        try:
            keyboard.add_hotkey('ctrl+shift+q', sertifika_kaldir, args=(True,))
            print(f"{GRI}[*] Panik Tuşu (CTRL+SHIFT+Q) hazır bekliyor.{SIFIRLA}")
        except Exception:
            pass
    print("-" * 80)

    try:
        while True:
            input()
            shield.ekran_log_aktif = False
            time.sleep(0.3)

            ai_durum = "AKTİF" if shield.altar_ai_aktif else "KAPALI"
            print(f"\n{KALIN}{SARI}" + "=" * 55)
            print("                YÖNETİCİ MENÜSÜ")
            print("=" * 55 + SIFIRLA)
            print("1. Engellenen Cihazları Listele ve Engel Kaldır")
            print("2. Şüpheli Bir IP'yi Tara (Hızlı Port Scanner)")
            print("3. Web Komuta Merkezini Tarayıcıda Aç")
            print("4. Tam İzolasyon UYGULA (Sadece Kendi Cihazın)")
            print("5. Tam İzolasyon KALDIR")
            print("6. MEB Sertifikasını Manuel Kur")
            print("7. MEB Sertifikasını Manuel Kaldır (Temizlik)")
            print(f"8. Altar Yapay Zeka Paket Analizini Aç/Kapat (Şu an: {ai_durum})")
            print("9. Kapat ve Çık (Sistemi Durdur)")
            print("0. Dinlemeye (Kayan Log Ekranına) Geri Dön\n")

            secim = input(f"{CYAN}İşlem Numarasını Seçin: {SIFIRLA}").strip()

            if secim == '1':
                for i, kayit in enumerate(shield.engellenen_listesi):
                    print(f"{i + 1}. IP: {kayit['ip']} | Sebep: {kayit['sebep']} | Zaman: {kayit['zaman']}")
                kaldir = input(f"\n{SARI}SIRA NUMARASINI girin (İptal için ENTER): {SIFIRLA}")
                if kaldir.isdigit() and 0 <= int(kaldir) - 1 < len(shield.engellenen_listesi):
                    silinecek_ip = shield.engellenen_listesi[int(kaldir) - 1]['ip']
                    shield.unblock_ip(silinecek_ip)
            elif secim == '2':
                hedef = input(f"\n{SARI}Taranacak Hedef IP Adresini Girin: {SIFIRLA}").strip()
                if hedef:
                    shield.hizli_port_taramasi(hedef)
            elif secim == '3':
                if not shield.web_sunucu_aktif:
                    threading.Thread(target=shield._web_dashboard_baslat, daemon=True).start()
                    shield.web_sunucu_aktif = True
                    time.sleep(1)
                webbrowser.open('http://127.0.0.1:5000')
            elif secim == '4':
                tam_izolasyon_uygula()
            elif secim == '5':
                tam_izolasyon_kaldir()
            elif secim == '6':
                sertifika_kur()
            elif secim == '7':
                sertifika_kaldir()
            elif secim == '8':
                shield.toggle_ai_analiz()
            elif secim == '9':
                raise KeyboardInterrupt

            if secim != '9':
                input(f"\n{GRI}Dinlemeye geri dönmek için ENTER'a basın...{SIFIRLA}")
                shield.ekran_log_aktif = True

    except KeyboardInterrupt:
        shield.print_summary()
        sys.exit(0)