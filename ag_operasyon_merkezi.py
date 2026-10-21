import os
import sys
import time
import random
import ctypes
import ipaddress
import threading
import subprocess
import urllib.request
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

try:
    import winreg
except ImportError:
    winreg = None

from scapy.all import ARP, Ether, srp, IP, ICMP, TCP, UDP, Raw, sr1, sniff
import customtkinter as ctk
from tkinter import messagebox

uretici_hafizasi = {}
_vendor_lock = threading.Lock()
proje_dizini = os.path.dirname(os.path.abspath(__file__))
dosya_sunucu = os.path.join(proje_dizini, 'supheli_sunucular.txt')
dosya_bireysel = os.path.join(proje_dizini, 'supheli_bireysel_bilgisayarlar.txt')

yerel_ag_bloklari = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.30.", "172.31.", "127.")
guvenilir_sunucular = ["8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1"]

bpf_filtresi = (
    "ip and "
    "not (tcp port 80 or tcp port 443 or tcp port 27015) and "
    "not (udp portrange 27015-27020)"
)

_akis_throttling = {}
_sunucu_disk_tamponu = deque(maxlen=500)
_bireysel_disk_tamponu = deque(maxlen=500)
_disk_kilit = threading.Lock()
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0


def _arka_plan_log_yazici():
    """Paket yakalama sırasında diski kilitlememek için 2 saniyede bir toplu olarak dosyaya yazar."""
    while True:
        time.sleep(2.0)
        with _disk_kilit:
            if _sunucu_disk_tamponu:
                satirlar = list(_sunucu_disk_tamponu)
                _sunucu_disk_tamponu.clear()
                try:
                    with open(dosya_sunucu, "a", encoding="utf-8") as f:
                        f.write("".join(satirlar))
                except Exception:
                    pass
            if _bireysel_disk_tamponu:
                satirlar = list(_bireysel_disk_tamponu)
                _bireysel_disk_tamponu.clear()
                try:
                    with open(dosya_bireysel, "a", encoding="utf-8") as f:
                        f.write("".join(satirlar))
                except Exception:
                    pass


threading.Thread(target=_arka_plan_log_yazici, daemon=True).start()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() if os.name == 'nt' else os.geteuid() == 0
    except Exception:
        return False


def mac_ureticisi_bul(mac_adresi: str) -> str:
    if mac_adresi in uretici_hafizasi:
        return uretici_hafizasi[mac_adresi]
    with _vendor_lock:
        if mac_adresi in uretici_hafizasi:
            return uretici_hafizasi[mac_adresi]
        try:
            url = f"https://api.macvendors.com/{mac_adresi}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Python Ağ Radarı'})
            with urllib.request.urlopen(req, timeout=1.8) as cevap:
                uretici = cevap.read().decode('utf-8').strip()
            uretici_hafizasi[mac_adresi] = uretici
            time.sleep(0.35)
            return uretici
        except Exception:
            uretici_hafizasi[mac_adresi] = "Bilinmiyor / Gizli MAC"
            return uretici_hafizasi[mac_adresi]


def os_ve_cihaz_tahmini(ip_adresi: str, uretici: str) -> str:
    try:
        paket = IP(dst=ip_adresi) / ICMP()
        cevap = sr1(paket, timeout=0.5, verbose=0)
        if cevap is None:
            return "TTL Alınamadı (Güvenlik Duvarı)"
        ttl = cevap.ttl
        uretici_kucuk = uretici.lower()
        if 64 < ttl <= 128:
            if any(marka in uretici_kucuk for marka in ["intel", "realtek", "hp", "dell", "asus", "lenovo", "msi"]):
                return f"Windows PC/Laptop (TTL:{ttl})"
            return f"Muhtemel Windows (TTL:{ttl})"
        elif ttl <= 64:
            if "apple" in uretici_kucuk:
                return f"iPhone/iPad/Mac (TTL:{ttl})"
            elif any(marka in uretici_kucuk for marka in ["samsung", "xiaomi", "huawei", "oppo", "realme"]):
                return f"Android Telefon/Tablet (TTL:{ttl})"
            return f"Telefon/Tablet/Linux (TTL:{ttl})"
        elif ttl > 128:
            return f"Modem/Router/Switch (TTL:{ttl})"
        return f"Bilinmeyen Cihaz (TTL:{ttl})"
    except Exception:
        return "Analiz Edilemedi"


def ag_taramasi_yap_tek_sefer(ag_blogu="192.168.1.0/24", log_callback=None) -> list:
    try:
        ag_blogu = str(ipaddress.ip_network(ag_blogu.strip(), strict=False))
    except ValueError:
        if log_callback:
            log_callback(f"[!] Geçersiz IP/CIDR ağ bloğu: '{ag_blogu}'. Örnek: 192.168.1.0/24")
        return []

    zaman = datetime.now().strftime("%H:%M:%S")
    if log_callback:
        log_callback(f"[{zaman}] 🔍 {ag_blogu} Ağı Taranıyor (ARP + Paralel ICMP TTL)...")

    arp_istegi = ARP(pdst=ag_blogu)
    yayin_paketi = Ether(dst="ff:ff:ff:ff:ff:ff") / arp_istegi
    cevaplananlar, _ = srp(yayin_paketi, timeout=1.8, verbose=0)

    cihazlar = [{'ip': alinan.psrc, 'mac': alinan.hwsrc} for _, alinan in cevaplananlar]
    baslik = f"{'IP ADRESİ':<15} | {'MAC ADRESİ':<17} | {'ÜRETİCİ (MARKA)':<24} | {'TAHMİNİ DONANIM'}"
    cizgi = "-" * 88
    if log_callback:
        log_callback(cizgi + "\n" + baslik + "\n" + cizgi)

    def _cihaz_analiz(cihaz):
        ip, mac = cihaz['ip'], cihaz['mac']
        uretici = mac_ureticisi_bul(mac)
        cihaz_turu = os_ve_cihaz_tahmini(ip, uretici)
        return f"{ip:<15} | {mac:<17} | {uretici[:22]:<24} | {cihaz_turu}"

    sonuc_listesi = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for satir in ex.map(_cihaz_analiz, cihazlar):
            sonuc_listesi.append(satir)
            if log_callback:
                log_callback(satir)

    if log_callback:
        log_callback(cizgi + f"\n[+] Toplam {len(cihazlar)} aktif cihaz tespit edildi.\n")
    return sonuc_listesi


def paket_analiz_isleyici(paket, log_callback=None):
    if IP in paket:
        ip_src = paket[IP].src
        ip_dst = paket[IP].dst

        if ip_src.startswith(yerel_ag_bloklari) and ip_dst.startswith(yerel_ag_bloklari):
            return
        if ip_src in guvenilir_sunucular or ip_dst in guvenilir_sunucular:
            return

        simdi = time.time()
        if len(_akis_throttling) > 1500:
            _akis_throttling.clear()
        anahtar = (ip_src, ip_dst)
        if simdi - _akis_throttling.get(anahtar, 0.0) < 1.5:
            return
        _akis_throttling[anahtar] = simdi

        sunucu_mu = False
        kategori_etiketi = "[!] BİREYSEL/BİLGİSAYAR İSTEĞİ"
        protokol_bilgisi = "Bilinmeyen Protokol"

        if paket.haslayer(TCP):
            sport, dport = paket[TCP].sport, paket[TCP].dport
            protokol_bilgisi = f"TCP Port: {sport} -> {dport}"
            if sport <= 1024 or dport <= 1024 or sport in [8080, 8443, 3389] or dport in [8080, 8443, 3389]:
                sunucu_mu = True
                kategori_etiketi = "[!] SUNUCU İSTEĞİ"
        elif paket.haslayer(UDP):
            sport, dport = paket[UDP].sport, paket[UDP].dport
            protokol_bilgisi = f"UDP Port: {sport} -> {dport}"
            if sport <= 1024 or dport <= 1024:
                sunucu_mu = True
                kategori_etiketi = "[!] SUNUCU İSTEĞİ"
        elif paket.haslayer(ICMP):
            protokol_bilgisi = "ICMP (Ping / Keşif İsteği)"
            kategori_etiketi = "[!] BİREYSEL (PING İSTEĞİ)"

        zaman = datetime.now().strftime("%H:%M:%S")
        log_mesaji = f"[{zaman}] {kategori_etiketi} | {ip_src} -> {ip_dst} ({protokol_bilgisi})"

        if paket.haslayer(Raw):
            try:
                payload = paket[Raw].load[:400].decode(errors='ignore')
                if any(k in payload.upper() for k in ("SELECT ", "<SCRIPT>", "CMD.EXE", "UNION ", "/ETC/PASSWD")):
                    log_mesaji += f"\n    🚨 [KRİTİK TEHLİKE]: Zararlı Kod Enjeksiyonu! İçerik: {payload[:120]}"
            except Exception:
                pass

        if log_callback:
            log_callback(log_mesaji)

        kayit_satiri = log_mesaji + "\n" + "-" * 50 + "\n"
        with _disk_kilit:
            if sunucu_mu:
                _sunucu_disk_tamponu.append(kayit_satiri)
            else:
                _bireysel_disk_tamponu.append(kayit_satiri)


def rastgele_mac_uret() -> str:
    mac = [0x02, 0x00, 0x00, random.randint(0x00, 0x7f), random.randint(0x00, 0xff), random.randint(0x00, 0xff)]
    return ''.join(map(lambda x: "%02x" % x, mac)).upper()


def mac_adresini_degistir(arayuz_adi="Wi-Fi", log_callback=None) -> str:
    if not is_admin() or winreg is None:
        msg = "[!] HATA: Kayıt defterine (Registry) müdahale etmek için Yönetici izni gereklidir."
        if log_callback:
            log_callback(msg)
        return msg

    yeni_mac = rastgele_mac_uret()
    if log_callback:
        log_callback(f"[*] Yeni Yerel Yönetimli MAC Üretildi: {yeni_mac}")

    reg_yolu = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"
    bulundu = False

    try:
        reg_anahtar = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_yolu)
        for i in range(winreg.QueryInfoKey(reg_anahtar)[0]):
            alt_anahtar_adi = winreg.EnumKey(reg_anahtar, i)
            if not alt_anahtar_adi.isdigit():
                continue
            try:
                alt_anahtar = winreg.OpenKey(reg_anahtar, alt_anahtar_adi, 0, winreg.KEY_ALL_ACCESS)
                isim, _ = winreg.QueryValueEx(alt_anahtar, "DriverDesc")
                if any(k in isim for k in ("Wireless", "Wi-Fi", "802.11", "WLAN")) or arayuz_adi.lower() in isim.lower():
                    if log_callback:
                        log_callback(f"[+] Hedef Ağ Kartı Bulundu: {isim}")
                    winreg.SetValueEx(alt_anahtar, "NetworkAddress", 0, winreg.REG_SZ, yeni_mac)
                    bulundu = True
                    winreg.CloseKey(alt_anahtar)
                    break
                winreg.CloseKey(alt_anahtar)
            except OSError:
                continue
        winreg.CloseKey(reg_anahtar)

        if not bulundu:
            uyari = "[-] Uygun kablosuz ağ kartı Registry'de bulunamadı."
            if log_callback:
                log_callback(uyari)
            return uyari

        if log_callback:
            log_callback(f"[*] '{arayuz_adi}' yeniden başlatılıyor ve yeni IP alınıyor (5 sn)...")
        subprocess.run(
            ["netsh", "interface", "set", "interface", arayuz_adi, "disable"],
            shell=False, capture_output=True, creationflags=_NO_WINDOW
        )
        time.sleep(3)
        subprocess.run(
            ["netsh", "interface", "set", "interface", arayuz_adi, "enable"],
            shell=False, capture_output=True, creationflags=_NO_WINDOW
        )
        msg = f"[+] BAŞARILI! Yeni MAC ({yeni_mac}) ve yeni IP aktif edildi."
        if log_callback:
            log_callback(msg)
        return msg
    except Exception as e:
        hata = f"[-] MAC değiştirme hatası: {e}"
        if log_callback:
            log_callback(hata)
        return hata


def orijinal_mac_geri_yukle(arayuz_adi="Wi-Fi", log_callback=None):
    if not is_admin() or winreg is None:
        if log_callback:
            log_callback("[!] Yönetici izni gereklidir.")
        return
    reg_yolu = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"
    try:
        reg_anahtar = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_yolu)
        for i in range(winreg.QueryInfoKey(reg_anahtar)[0]):
            alt_adi = winreg.EnumKey(reg_anahtar, i)
            if not alt_adi.isdigit():
                continue
            try:
                alt = winreg.OpenKey(reg_anahtar, alt_adi, 0, winreg.KEY_ALL_ACCESS)
                isim, _ = winreg.QueryValueEx(alt, "DriverDesc")
                if any(k in isim for k in ("Wireless", "Wi-Fi", "802.11", "WLAN")):
                    try:
                        winreg.DeleteValue(alt, "NetworkAddress")
                    except FileNotFoundError:
                        pass
                    winreg.CloseKey(alt)
                    break
                winreg.CloseKey(alt)
            except OSError:
                continue
        winreg.CloseKey(reg_anahtar)
        subprocess.run(
            ["netsh", "interface", "set", "interface", arayuz_adi, "disable"],
            shell=False, capture_output=True, creationflags=_NO_WINDOW
        )
        time.sleep(2)
        subprocess.run(
            ["netsh", "interface", "set", "interface", arayuz_adi, "enable"],
            shell=False, capture_output=True, creationflags=_NO_WINDOW
        )
        if log_callback:
            log_callback("[+] Orijinal donanım MAC adresi geri yüklendi ve ağ yenilendi.")
    except Exception as e:
        if log_callback:
            log_callback(f"[-] Geri yükleme hatası: {e}")


class AgOperasyonPaneli(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#0B1320", corner_radius=8, border_width=1, border_color="#1E293B")
        self.radar_aktif = False
        self.izleme_aktif = False
        self._log_tamponu = deque(maxlen=250)

        open(dosya_sunucu, 'a', encoding='utf-8').close()
        open(dosya_bireysel, 'a', encoding='utf-8').close()

        self._arayuz_olustur()
        self.after(250, self._toplu_log_yazici)

    def _arayuz_olustur(self):
        ust = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
        ust.pack(side="top", fill="x", padx=6, pady=4)

        ctk.CTkLabel(
            ust, text="🌐 1. BÖLÜM: AĞ TARAYICISI | AĞ İZLEME | IP-MAC DEĞİŞTİRİCİ",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#00FFCC"
        ).pack(side="left", padx=8, pady=3)

        self.entry_ag_hedef = ctk.CTkEntry(ust, width=135, height=24, font=ctk.CTkFont(family="Consolas", size=11))
        self.entry_ag_hedef.pack(side="right", padx=6, pady=3)
        self.entry_ag_hedef.insert(0, "192.168.1.0/24")

        self.entry_arayuz = ctk.CTkEntry(ust, width=75, height=24, font=ctk.CTkFont(family="Consolas", size=11))
        self.entry_arayuz.pack(side="right", padx=4, pady=3)
        self.entry_arayuz.insert(0, "Wi-Fi")

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(side="top", fill="x", padx=6, pady=2)

        self.btn_tek_tara = ctk.CTkButton(btn_bar, text="📡 Ağı Şimdi Tara", width=102, height=24, font=ctk.CTkFont(size=11), fg_color="#1f538d", command=self.tek_sefer_tara_baslat)
        self.btn_tek_tara.pack(side="left", padx=1)

        self.btn_canli_radar = ctk.CTkButton(btn_bar, text="🔄 Canlı Radar: Kapalı", width=122, height=24, font=ctk.CTkFont(size=11), fg_color="#006666", command=self.canli_radar_ac_kapat)
        self.btn_canli_radar.pack(side="left", padx=1)

        self.btn_ag_izle = ctk.CTkButton(btn_bar, text="👁️ Ağ İzleme (BPF)", width=122, height=24, font=ctk.CTkFont(size=11), fg_color="#4B0082", command=self.ag_izleme_ac_kapat)
        self.btn_ag_izle.pack(side="left", padx=1)

        self.btn_mac_degis = ctk.CTkButton(btn_bar, text="🎭 IP & MAC Değiştir", width=114, height=24, font=ctk.CTkFont(size=11), fg_color="#B85C00", hover_color="#8F4700", command=self.mac_degistir_baslat)
        self.btn_mac_degis.pack(side="left", padx=1)

        self.btn_mac_sifirla = ctk.CTkButton(btn_bar, text="♻️ Orijinal MAC", width=92, height=24, font=ctk.CTkFont(size=11), fg_color="#2E7D32", command=self.mac_orijinal_baslat)
        self.btn_mac_sifirla.pack(side="left", padx=1)

        ctk.CTkButton(btn_bar, text="📄 Sunucu Log", width=80, height=24, font=ctk.CTkFont(size=11), fg_color="#374151", command=lambda: self.log_dosyasi_goster(dosya_sunucu, "ŞÜPHELİ SUNUCU KAYITLARI")).pack(side="left", padx=1)
        ctk.CTkButton(btn_bar, text="💻 Bireysel Log", width=84, height=24, font=ctk.CTkFont(size=11), fg_color="#374151", command=lambda: self.log_dosyasi_goster(dosya_bireysel, "ŞÜPHELİ BİREYSEL KAYITLAR")).pack(side="left", padx=1)

        self.txt_cikti = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=11), fg_color="#05080F", text_color="#00FF88", height=115, wrap="none")
        self.txt_cikti.pack(side="top", fill="both", expand=True, padx=6, pady=(2, 6))
        self.log_ekle("[*] Birleşik Ağ Operasyon Merkezi Hazır (Ağ Tarayıcısı + BPF Ağ İzleme + IP/MAC Değiştirici).")

    def log_ekle(self, mesaj: str):
        self._log_tamponu.append(mesaj)

    def _toplu_log_yazici(self):
        try:
            if not self.winfo_exists():
                return
            if self._log_tamponu:
                parcalar = []
                while self._log_tamponu and len(parcalar) < 30:
                    parcalar.append(self._log_tamponu.popleft())
                self.txt_cikti.insert("end", "\n".join(parcalar) + "\n")
                satir_sayisi = int(self.txt_cikti.index("end-1c").split(".")[0])
                if satir_sayisi > 300:
                    self.txt_cikti.delete("1.0", f"{satir_sayisi - 200}.0")
                self.txt_cikti.see("end")
            self.after(250, self._toplu_log_yazici)
        except Exception:
            pass

    def tek_sefer_tara_baslat(self):
        ag = self.entry_ag_hedef.get().strip() or "192.168.1.0/24"
        threading.Thread(target=ag_taramasi_yap_tek_sefer, args=(ag, self.log_ekle), daemon=True).start()

    def canli_radar_ac_kapat(self):
        self.radar_aktif = not self.radar_aktif
        if self.radar_aktif:
            self.btn_canli_radar.configure(text="🔄 Canlı Radar: AKTİF", fg_color="#00A86B")
            ag = self.entry_ag_hedef.get().strip() or "192.168.1.0/24"
            def _loop():
                while self.radar_aktif:
                    ag_taramasi_yap_tek_sefer(ag, self.log_ekle)
                    for _ in range(5):
                        if not self.radar_aktif:
                            break
                        time.sleep(1)
            threading.Thread(target=_loop, daemon=True).start()
        else:
            self.btn_canli_radar.configure(text="🔄 Canlı Radar: Kapalı", fg_color="#006666")
            self.log_ekle("[*] Canlı Ağ Radarı durduruldu.")

    def ag_izleme_ac_kapat(self):
        self.izleme_aktif = not self.izleme_aktif
        if self.izleme_aktif:
            self.btn_ag_izle.configure(text="👁️ Ağ İzleme: AKTİF", fg_color="#00A86B")
            self.log_ekle("[*] Gelişmiş BPF Ağ Dinleyicisi Başlatıldı.")
            def _sniff_worker():
                try:
                    sniff(filter=bpf_filtresi, prn=lambda p: paket_analiz_isleyici(p, self.log_ekle), store=0, stop_filter=lambda p: not self.izleme_aktif)
                except Exception as e:
                    self.log_ekle(f"[-] Dinleme hatası: {e}")
            threading.Thread(target=_sniff_worker, daemon=True).start()
        else:
            self.btn_ag_izle.configure(text="👁️ Ağ İzleme (BPF)", fg_color="#4B0082")
            self.log_ekle("[*] BPF Ağ İzleme durduruldu.")

    def mac_degistir_baslat(self):
        arayuz = self.entry_arayuz.get().strip() or "Wi-Fi"
        threading.Thread(target=mac_adresini_degistir, args=(arayuz, self.log_ekle), daemon=True).start()

    def mac_orijinal_baslat(self):
        arayuz = self.entry_arayuz.get().strip() or "Wi-Fi"
        threading.Thread(target=orijinal_mac_geri_yukle, args=(arayuz, self.log_ekle), daemon=True).start()

    def log_dosyasi_goster(self, dosya_yolu: str, baslik: str):
        self._log_tamponu.clear()
        self.txt_cikti.delete("1.0", "end")

        def _oku():
            self.log_ekle(f"=== 📂 {baslik} ({os.path.basename(dosya_yolu)}) ===")
            if os.path.exists(dosya_yolu):
                try:
                    with open(dosya_yolu, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(max(0, os.path.getsize(dosya_yolu) - 8000))
                        icerik = f.read().strip()
                    self.log_ekle(icerik if icerik else "Henüz şüpheli kayıt bulunmuyor.")
                except Exception as e:
                    self.log_ekle(f"Okuma hatası: {e}")

        threading.Thread(target=_oku, daemon=True).start()