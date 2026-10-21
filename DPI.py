import os
import sys
import math
import time
import struct
import socket
import hashlib
import ctypes
import threading
from datetime import datetime
from collections import deque

try:
    import pydivert
    PYDIVERT_AVAILABLE = True
except ImportError:
    pydivert = None
    PYDIVERT_AVAILABLE = False

try:
    import scapy.all as scapy
    SCAPY_AVAILABLE = True
except ImportError:
    scapy = None
    SCAPY_AVAILABLE = False

try:
    import customtkinter as ctk
    from tkinter import messagebox
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() if os.name == 'nt' else os.geteuid() == 0
    except Exception:
        return False


# =========================================================================
# %100 RAM-İÇİ DERİN PAKET ANALİZ (DPI) VE AKTİF SAVUNMA ÇEKİRDEĞİ
# =========================================================================
class AltarDPIDefenseEngine:
    """
    Bilgisayarda hiçbir dosya/klasör oluşturmayan (%100 RAM-İçi) ve
    ağ bağlantısını asla kesmeyen (Fail-Open korumalı) Derin Paket Analiz Motoru.
    """
    ZARARLI_L7_IMZALAR = (
        (b"union select", "SQL Injection Girişimi"),
        (b"/etc/passwd", "Linux Hassas Dosya Erişimi (LFI)"),
        (b"..\\..\\", "Windows Dizin Geçiş Saldırısı (Path Traversal)"),
        (b"../../", "Dizin Geçiş Saldırısı (Path Traversal)"),
        (b"cmd.exe", "Uzaktan Komut Çalıştırma (RCE - cmd.exe)"),
        (b"powershell", " Zararlı PowerShell Payload"),
        (b"<script>", "Cross-Site Scripting (XSS) Payload"),
        (b"xp_cmdshell", "MSSQL Komut Enjeksiyonu"),
        (b"jndi:ldap", "Log4Shell (JNDI) İstismar Girişimi")
    )

    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.calisiyor = False
        self.aktif_mod = "WinDivert Kalkan + Desync"
        self.hedef_kelimeler = []           # Boş veya ['*'] ise tüm TLS hedeflerini kapsar
        self.bolme_noktasi = 10             # Orijinal Ters TCP parçalama bayt ofseti
        self.gelen_saldiri_engelle = True   # Gelen L7 saldırı paketlerini RAM'de düşürür

        # %100 RAM-İçi Veri Yapıları (Disk kullanımı sıfırdır)
        self.kilit = threading.Lock()
        self.ram_loglari = deque(maxlen=350)
        self.sni_loglari = deque(maxlen=200)
        self.tehdit_loglari = deque(maxlen=200)
        self.desync_loglari = deque(maxlen=200)
        self._sni_son_gorulme = {}

        self.istatistikler = {
            "TOPLAM_PAKET": 0,
            "TLS_SNI": 0,
            "DESYNC_UYGULANAN": 0,
            "TEHDIT_ENGEL": 0,
            "YUKSEK_ENTROPI": 0,
            "ORT_ENTROPI": 0.0
        }

    def hedef_ayarla(self, girdi_metni: str, bolme_bayt: int = 10):
        temiz = girdi_metni.strip().lower()
        if not temiz or temiz == "*":
            self.hedef_kelimeler = []
        else:
            self.hedef_kelimeler = [k.strip().encode("utf-8") for k in temiz.split(",") if k.strip()]
        self.bolme_noktasi = max(2, min(int(bolme_bayt), 64))

    def _log_kaydet(self, metin: str, kategori: str = "GENEL"):
        zaman = datetime.now().strftime("%H:%M:%S")
        tam_satir = f"[{zaman}] {metin}"
        with self.kilit:
            self.ram_loglari.append(tam_satir)
            if kategori == "SNI":
                self.sni_loglari.append(tam_satir)
            elif kategori == "TEHDIT":
                self.tehdit_loglari.append(tam_satir)
            elif kategori == "DESYNC":
                self.desync_loglari.append(tam_satir)

        if self.log_callback:
            try:
                self.log_callback(tam_satir, kategori)
            except Exception:
                pass

    @staticmethod
    def shannon_entropi_hesapla(veri: bytes) -> float:
        if not veri:
            return 0.0
        uzunluk = len(veri)
        frekans = [0] * 256
        for b in veri:
            frekans[b] += 1
        entropi = 0.0
        for f in frekans:
            if f > 0:
                p = f / uzunluk
                entropi -= p * math.log2(p)
        return entropi

    @staticmethod
    def tls_client_hello_cozumle(payload: bytes) -> dict:
        """
        TLS ClientHello (0x16 0x03) paketinden SNI (Sunucu Adı), TLS Sürümü ve
        basitleştirilmiş JA3 TLS Parmak İzini (MD5) tamamen RAM üzerinde çıkarır.
        """
        bilgi = {"tls_mi": False, "sni": "", "surum": "", "ja3_hash": "", "cipher_sayisi": 0}
        if not payload or len(payload) < 44 or payload[0] != 0x16 or payload[1] != 0x03 or payload[5] != 0x01:
            return bilgi

        bilgi["tls_mi"] = True
        surum_haritasi = {(3, 1): "TLS 1.0", (3, 2): "TLS 1.1", (3, 3): "TLS 1.2", (3, 4): "TLS 1.3"}
        ch_ver = (payload[9], payload[10])
        bilgi["surum"] = surum_haritasi.get(ch_ver, f"TLS ({ch_ver[0]}.{ch_ver[1]})")

        try:
            session_id_len = payload[43]
            c_off = 44 + session_id_len
            if c_off + 2 > len(payload):
                return bilgi

            c_len = int.from_bytes(payload[c_off:c_off + 2], 'big')
            bilgi["cipher_sayisi"] = c_len // 2
            ciphers = []
            for idx in range(c_off + 2, min(c_off + 2 + c_len, len(payload) - 1), 2):
                cs = int.from_bytes(payload[idx:idx + 2], 'big')
                if (cs & 0x0F0F) != 0x0A0A:
                    ciphers.append(str(cs))

            comp_off = c_off + 2 + c_len
            if comp_off + 1 > len(payload):
                return bilgi
            comp_len = payload[comp_off]
            ext_off = comp_off + 1 + comp_len

            if ext_off + 2 > len(payload):
                return bilgi
            ext_total_len = int.from_bytes(payload[ext_off:ext_off + 2], 'big')

            curr = ext_off + 2
            sni_str = ""
            ext_types = []

            while curr + 4 <= min(ext_off + 2 + ext_total_len, len(payload)):
                ext_type = int.from_bytes(payload[curr:curr + 2], 'big')
                ext_len = int.from_bytes(payload[curr + 2:curr + 4], 'big')
                if (ext_type & 0x0F0F) != 0x0A0A:
                    ext_types.append(str(ext_type))

                if ext_type == 0 and curr + 9 <= len(payload):
                    name_len = int.from_bytes(payload[curr + 7:curr + 9], 'big')
                    if curr + 9 + name_len <= len(payload):
                        sni_str = payload[curr + 9:curr + 9 + name_len].decode('utf-8', errors='ignore')

                curr += 4 + ext_len

            bilgi["sni"] = sni_str
            ja3_ham = f"{ch_ver[0] * 256 + ch_ver[1]},{'-'.join(ciphers[:15])},{'-'.join(ext_types[:15])}"
            bilgi["ja3_hash"] = hashlib.md5(ja3_ham.encode('utf-8')).hexdigest()[:16]
        except Exception:
            pass

        return bilgi

    def l7_tehdit_analizi_yap(self, payload: bytes, src_ip: str, dst_ip: str, src_port: int, dst_port: int) -> tuple:
        if not payload:
            return False, "", 0.0
        if src_ip in ("127.0.0.1", "::1") or dst_ip in ("127.0.0.1", "::1") or src_port in (11434, 5000) or dst_port in (11434, 5000):
            return False, "", 0.0

        entropi = self.shannon_entropi_hesapla(payload[:384])
        with self.kilit:
            eski_ort = self.istatistikler["ORT_ENTROPI"]
            self.istatistikler["ORT_ENTROPI"] = (eski_ort * 0.95) + (entropi * 0.05) if eski_ort > 0 else entropi

        if src_port != 443 and dst_port != 443:
            kucuk_payload = payload[:768].lower()
            for imza, aciklama in self.ZARARLI_L7_IMZALAR:
                if imza in kucuk_payload:
                    return True, f"L7 İMZA YAKALANDI ({aciklama}) | {src_ip}:{src_port} -> {dst_ip}:{dst_port}", entropi

            if len(payload) > 180 and entropi > 7.65 and dst_port not in (80, 443, 53, 22):
                with self.kilit:
                    self.istatistikler["YUKSEK_ENTROPI"] += 1
                self._log_kaydet(
                    f"⚠️ [ANOMALİ / YÜKSEK ENTROPİ: {entropi:.2f}] Şifreli Tünel Şüphesi: {src_ip}:{src_port} -> {dst_ip}:{dst_port} ({len(payload)}B)",
                    kategori="TEHDIT"
                )

        if (dst_port == 53 or src_port == 53) and len(payload) > 220 and entropi > 5.8:
            return True, f"DNS TÜNELLEME / DGA ŞÜPHESİ (Boyut: {len(payload)}B, Entropi: {entropi:.2f}) | {src_ip} -> {dst_ip}", entropi

        return False, "", entropi

    def _hedef_eslesiyor_mu(self, payload: bytes, sni_metni: str) -> bool:
        if not self.hedef_kelimeler:
            return True
        kucuk_payload = payload.lower()
        kucuk_sni = sni_metni.lower().encode('utf-8')
        return any((h in kucuk_sni or h in kucuk_payload) for h in self.hedef_kelimeler)

    def _sni_log_izin_ver(self, sni: str, dst_ip: str) -> bool:
        simdi = time.time()
        if len(self._sni_son_gorulme) > 1000:
            self._sni_son_gorulme.clear()
        anahtar = (sni, dst_ip)
        if simdi - self._sni_son_gorulme.get(anahtar, 0.0) < 1.5:
            return False
        self._sni_son_gorulme[anahtar] = simdi
        return True

    # =========================================================================
    # MOTOR 1: WINDIVERT INLINE AKTİF KORUMA VE TERS TCP PARÇALAMA (DESYNC)
    # =========================================================================
    def windivert_motorunu_calistir(self, desync_aktif: bool = True):
        if not PYDIVERT_AVAILABLE:
            self._log_kaydet("[-] 'pydivert' kütüphanesi bulunamadı! Pasif Scapy DPI moduna geçiliyor...", "TEHDIT")
            self.scapy_pasif_motorunu_calistir()
            return

        if not is_admin():
            self._log_kaydet("[-] HATA: WinDivert sürücüsü için Yönetici (Administrator) izni gereklidir!", "TEHDIT")
            self.calisiyor = False
            return

        filtre = "(not loopback) and (tcp.PayloadLength > 0 or udp.PayloadLength > 180)"
        self._log_kaydet(
            f"[*] WinDivert DPI Motoru Başlatıldı (Ters TCP Desync: {'AÇIK' if desync_aktif else 'KAPALI'} | Bölme: {self.bolme_noktasi} Bayt)",
            "GENEL"
        )

        try:
            with pydivert.WinDivert(filtre) as w:
                for packet in w:
                    if not self.calisiyor:
                        w.send(packet)
                        break

                    paket_gonderildi = False
                    try:
                        payload = bytes(packet.payload) if packet.payload else b""
                        src_ip = str(packet.src_addr)
                        dst_ip = str(packet.dst_addr)
                        src_port = int(packet.src_port or 0)
                        dst_port = int(packet.dst_port or 0)

                        with self.kilit:
                            self.istatistikler["TOPLAM_PAKET"] += 1

                        # A) L7 Saldırı ve Entropi Analizi
                        tehdit_var, tehdit_mesaji, _ = self.l7_tehdit_analizi_yap(
                            payload, src_ip, dst_ip, src_port, dst_port
                        )
                        if tehdit_var:
                            with self.kilit:
                                self.istatistikler["TEHDIT_ENGEL"] += 1
                            if packet.is_inbound and self.gelen_saldiri_engelle:
                                self._log_kaydet(f"🛡️ [ENGELLENDİ / DROP] {tehdit_mesaji}", "TEHDIT")
                                paket_gonderildi = True
                                continue
                            else:
                                self._log_kaydet(f"🚨 [TEHDİT TESPİTİ] {tehdit_mesaji}", "TEHDIT")

                        # B) TLS ClientHello (Port 443) SNI, JA3 ve Ters TCP Parçalama (Reverse Desync)
                        if payload.startswith(b'\x16\x03') and packet.tcp:
                            tls_bilgi = self.tls_client_hello_cozumle(payload)
                            if tls_bilgi["tls_mi"]:
                                sni = tls_bilgi["sni"] or "Gizli/ECH SNI"
                                ja3 = tls_bilgi["ja3_hash"]
                                surum = tls_bilgi["surum"]

                                with self.kilit:
                                    self.istatistikler["TLS_SNI"] += 1

                                if self._sni_log_izin_ver(sni, dst_ip):
                                    self._log_kaydet(
                                        f"🔒 [TLS SNI] {sni:<28} | {surum} | JA3: {ja3} | {src_ip} -> {dst_ip}",
                                        "SNI"
                                    )

                                if desync_aktif and packet.is_outbound and dst_port == 443 and len(payload) > self.bolme_noktasi:
                                    if self._hedef_eslesiyor_mu(payload, sni):
                                        orijinal_seq = packet.tcp.seq_num
                                        kesim = self.bolme_noktasi

                                        # 1. AŞAMA: İkinci parçayı (kuyruğu) önce gönder
                                        parca2 = payload[kesim:]
                                        packet.tcp.seq_num = (orijinal_seq + kesim) & 0xFFFFFFFF
                                        packet.payload = parca2
                                        w.send(packet)

                                        # 2. AŞAMA: Birinci parçayı (başı) sonra gönder
                                        parca1 = payload[:kesim]
                                        packet.tcp.seq_num = orijinal_seq
                                        packet.payload = parca1
                                        w.send(packet)

                                        paket_gonderildi = True
                                        with self.kilit:
                                            self.istatistikler["DESYNC_UYGULANAN"] += 1

                                        self._log_kaydet(
                                            f"⚡ [TERS DESYNC UYGULANDI] Hedef: {sni} | Seq: {orijinal_seq} ({kesim}B + {len(parca2)}B ters sıra iletildi)",
                                            "DESYNC"
                                        )
                                        continue

                    except Exception:
                        pass
                    finally:
                        if not paket_gonderildi:
                            try:
                                w.send(packet)
                            except Exception:
                                pass

        except Exception as e:
            self._log_kaydet(f"[-] WinDivert hatası: {e}", "TEHDIT")
        finally:
            self.calisiyor = False
            self._log_kaydet("[*] WinDivert DPI Motoru güvenli şekilde durduruldu.", "GENEL")

    # =========================================================================
    # MOTOR 2: SCAPY PASİF DPI MOTORU (SIFIR GECİKME / SALT-OKUNUR ANALİZ)
    # =========================================================================
    def scapy_pasif_motorunu_calistir(self):
        if not SCAPY_AVAILABLE:
            self._log_kaydet("[-] Scapy kütüphanesi bulunamadı.", "TEHDIT")
            self.calisiyor = False
            return

        self._log_kaydet("[*] Pasif Scapy DPI Motoru Başlatıldı (Ağ paketlerine müdahale etmeden %100 RAM analizi).", "GENEL")

        def _paket_isle(pkt):
            if not self.calisiyor or not pkt.haslayer(scapy.IP) or not pkt.haslayer(scapy.Raw):
                return
            try:
                payload = bytes(pkt[scapy.Raw].load)
                src_ip, dst_ip = pkt[scapy.IP].src, pkt[scapy.IP].dst
                sport = pkt[scapy.TCP].sport if pkt.haslayer(scapy.TCP) else (pkt[scapy.UDP].sport if pkt.haslayer(scapy.UDP) else 0)
                dport = pkt[scapy.TCP].dport if pkt.haslayer(scapy.TCP) else (pkt[scapy.UDP].dport if pkt.haslayer(scapy.UDP) else 0)

                with self.kilit:
                    self.istatistikler["TOPLAM_PAKET"] += 1

                tehdit_var, tehdit_mesaji, _ = self.l7_tehdit_analizi_yap(payload, src_ip, dst_ip, sport, dport)
                if tehdit_var:
                    with self.kilit:
                        self.istatistikler["TEHDIT_ENGEL"] += 1
                    self._log_kaydet(f"🚨 [PASİF DPI TEHDİT TESPİTİ] {tehdit_mesaji}", "TEHDIT")

                if payload.startswith(b'\x16\x03'):
                    tls_bilgi = self.tls_client_hello_cozumle(payload)
                    if tls_bilgi["tls_mi"]:
                        with self.kilit:
                            self.istatistikler["TLS_SNI"] += 1
                        sni = tls_bilgi["sni"] or "Gizli SNI"
                        if self._sni_log_izin_ver(sni, dst_ip):
                            self._log_kaydet(
                                f"🔒 [TLS SNI] {sni:<28} | {tls_bilgi['surum']} | JA3: {tls_bilgi['ja3_hash']} | {src_ip} -> {dst_ip}",
                                "SNI"
                            )
            except Exception:
                pass

        try:
            scapy.sniff(
                filter="tcp or udp",
                prn=_paket_isle,
                store=False,
                stop_filter=lambda p: not self.calisiyor
            )
        except Exception as e:
            self._log_kaydet(f"[-] Pasif DPI hatası: {e}", "TEHDIT")
        finally:
            self.calisiyor = False


# =========================================================================
# ALTAR TERSİNE MÜHENDİSLİK SEKMESİ ALT PANELİ (250ms TOPLU ÇİZİM İLE SIFIR KASMA)
# =========================================================================
if CTK_AVAILABLE:
    class DerinPaketAnalizPaneli(ctk.CTkFrame):
        """
        Tersine Mühendislik sekmesinin alt kısmına tek parça (bölünmeden) yerleşen
        Derin Paket Analizi (DPI), TLS SNI/JA3 Çözümleyici ve Ters TCP Desync Kontrol Merkezi.
        """
        def __init__(self, parent, ai_analiz_callback=None):
            super().__init__(parent, fg_color="#0B1320", corner_radius=8, border_width=1, border_color="#1E293B")
            self.ai_analiz_callback = ai_analiz_callback
            self.aktif_filtre = "TUMU"
            self._ekran_tamponu = deque(maxlen=250)
            self.motor = AltarDPIDefenseEngine(log_callback=self._yeni_log_geldi)

            self._arayuz_olustur()
            self.after(250, self._tamponu_ekrana_bosalt)
            self._telemetri_dongusu()

        def _arayuz_olustur(self):
            # 1. ÜST BAŞLIK VE CANLI TELEMETRİ SAYACI
            ust = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
            ust.pack(side="top", fill="x", padx=8, pady=(5, 3))

            ctk.CTkLabel(
                ust,
                text="🛡️ ALTAR DERİN PAKET ANALİZİ (DPI), JA3/SNI RADARI & TERS TCP DESYNC SAVUNMA MERKEZİ (%100 RAM)",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                text_color="#00FFCC"
            ).pack(side="left", padx=10, pady=4)

            self.lbl_sayac = ctk.CTkLabel(
                ust,
                text="Paket: 0 | TLS/SNI: 0 | Desync: 0 | Tehdit: 0 | Entropi: 0.00",
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                text_color="#FFD700"
            )
            self.lbl_sayac.pack(side="right", padx=10, pady=4)

            # 2. KONTROL VE FİLTRE ÇUBUĞU
            kontrol_bar = ctk.CTkFrame(self, fg_color="transparent")
            kontrol_bar.pack(side="top", fill="x", padx=8, pady=2)

            ctk.CTkLabel(kontrol_bar, text="Mod:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(2, 3))
            self.mod_var = ctk.StringVar(value="WinDivert Kalkan + Desync")
            self.combo_mod = ctk.CTkOptionMenu(
                kontrol_bar,
                variable=self.mod_var,
                values=[
                    "WinDivert Kalkan + Desync",
                    "WinDivert Salt-Savunma (Desync Kapalı)",
                    "Scapy Pasif DPI (Sıfır Gecikme)"
                ],
                width=235, height=24, font=ctk.CTkFont(size=11)
            )
            self.combo_mod.pack(side="left", padx=3)

            ctk.CTkLabel(kontrol_bar, text="Hedef Site/Alan:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(6, 2))
            self.entry_hedef = ctk.CTkEntry(
                kontrol_bar, width=155, height=24,
                placeholder_text="Örn: udemy, discord veya *",
                font=ctk.CTkFont(family="Consolas", size=11)
            )
            self.entry_hedef.pack(side="left", padx=2)
            self.entry_hedef.insert(0, "*")

            ctk.CTkLabel(kontrol_bar, text="Bölme(B):", font=ctk.CTkFont(size=11)).pack(side="left", padx=(4, 2))
            self.entry_bolme = ctk.CTkEntry(kontrol_bar, width=42, height=24, font=ctk.CTkFont(family="Consolas", size=11))
            self.entry_bolme.pack(side="left", padx=2)
            self.entry_bolme.insert(0, "10")

            self.btn_baslat = ctk.CTkButton(
                kontrol_bar, text="▶️ DPI Kalkanını Başlat", width=145, height=24,
                fg_color="#00A86B", hover_color="#007F50", font=ctk.CTkFont(size=11, weight="bold"),
                command=self.dpi_baslat_durdur
            )
            self.btn_baslat.pack(side="left", padx=4)

            # Görünüm Filtre Butonları
            ctk.CTkButton(
                kontrol_bar, text="📋 Tüm Akış", width=80, height=24, font=ctk.CTkFont(size=11),
                fg_color="#1f538d", command=lambda: self.gorunum_degistir("TUMU")
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                kontrol_bar, text="🔒 TLS SNI & JA3", width=105, height=24, font=ctk.CTkFont(size=11),
                fg_color="#4B0082", command=lambda: self.gorunum_degistir("SNI")
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                kontrol_bar, text="⚡ Desync", width=75, height=24, font=ctk.CTkFont(size=11),
                fg_color="#B85C00", command=lambda: self.gorunum_degistir("DESYNC")
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                kontrol_bar, text="🚨 Tehditler", width=85, height=24, font=ctk.CTkFont(size=11),
                fg_color="#8B0000", command=lambda: self.gorunum_degistir("TEHDIT")
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                kontrol_bar, text="🧠 AI Analiz", width=88, height=24, font=ctk.CTkFont(size=11),
                fg_color="#008080", command=self.dpi_raporunu_ai_gonder
            ).pack(side="right", padx=2)

            ctk.CTkButton(
                kontrol_bar, text="🧹 Temizle", width=72, height=24, font=ctk.CTkFont(size=11),
                fg_color="#374151", command=self.ekrani_temizle
            ).pack(side="right", padx=2)

            # 3. CANLI PAKET VE PROTOKOL ANALİZ EKRANI
            self.txt_dpi_ekran = ctk.CTkTextbox(
                self, font=ctk.CTkFont(family="Consolas", size=11),
                fg_color="#05080F", text_color="#00FF88", height=110, wrap="none"
            )
            self.txt_dpi_ekran.pack(side="top", fill="both", expand=True, padx=8, pady=(2, 6))
            self.txt_dpi_ekran.tag_config("SNI", foreground="#58A6FF")
            self.txt_dpi_ekran.tag_config("TEHDIT", foreground="#FF4444")
            self.txt_dpi_ekran.tag_config("DESYNC", foreground="#FFD700")
            self.txt_dpi_ekran.insert(
                "end",
                "[*] Altar Derin Paket Analizi (DPI) ve Ters TCP Desync Savunma Merkezi Hazır (%100 RAM-İçi, Sıfır Disk Yazımı).\n"
                "• Hedef kutusuna belirli siteleri (örn: udemy, discord) veya tüm TLS bağlantıları için '*' yazıp '▶️ DPI Kalkanını Başlat' butonuna basın.\n"
            )

        def dpi_baslat_durdur(self):
            if not self.motor.calisiyor:
                try:
                    bolme = int(self.entry_bolme.get().strip() or 10)
                except ValueError:
                    bolme = 10
                self.motor.hedef_ayarla(self.entry_hedef.get(), bolme)
                self.motor.calisiyor = True
                secilen_mod = self.mod_var.get()

                self.btn_baslat.configure(text="⏹️ DPI Kalkanını Durdur", fg_color="#C62828", hover_color="#8E0000")

                if "Scapy" in secilen_mod:
                    threading.Thread(target=self.motor.scapy_pasif_motorunu_calistir, daemon=True).start()
                else:
                    desync_acik = "Desync" in secilen_mod and "Kapalı" not in secilen_mod
                    threading.Thread(target=self.motor.windivert_motorunu_calistir, args=(desync_acik,), daemon=True).start()
            else:
                self.motor.calisiyor = False
                self.btn_baslat.configure(text="▶️ DPI Kalkanını Başlat", fg_color="#00A86B", hover_color="#007F50")

        def _yeni_log_geldi(self, satir: str, kategori: str):
            if self.aktif_filtre == "TUMU" or self.aktif_filtre == kategori:
                self._ekran_tamponu.append((satir, kategori))

        def _tamponu_ekrana_bosalt(self):
            if not self.winfo_exists():
                return
            if self._ekran_tamponu:
                sayac = 0
                while self._ekran_tamponu and sayac < 30:
                    satir, kategori = self._ekran_tamponu.popleft()
                    sayac += 1
                    tag = kategori if kategori in ("SNI", "TEHDIT", "DESYNC") else None
                    if tag:
                        self.txt_dpi_ekran.insert("end", satir + "\n", tag)
                    else:
                        self.txt_dpi_ekran.insert("end", satir + "\n")
                satir_sayisi = int(self.txt_dpi_ekran.index("end-1c").split(".")[0])
                if satir_sayisi > 300:
                    self.txt_dpi_ekran.delete("1.0", f"{satir_sayisi - 200}.0")
                self.txt_dpi_ekran.see("end")
            self.after(250, self._tamponu_ekrana_bosalt)

        def gorunum_degistir(self, filtre_kodu: str):
            self.aktif_filtre = filtre_kodu
            self._ekran_tamponu.clear()
            self.txt_dpi_ekran.delete("1.0", "end")
            with self.motor.kilit:
                if filtre_kodu == "SNI":
                    kayitlar = list(self.motor.sni_loglari)
                elif filtre_kodu == "TEHDIT":
                    kayitlar = list(self.motor.tehdit_loglari)
                elif filtre_kodu == "DESYNC":
                    kayitlar = list(self.motor.desync_loglari)
                else:
                    kayitlar = list(self.motor.ram_loglari)

            if kayitlar:
                self.txt_dpi_ekran.insert("1.0", "\n".join(kayitlar) + "\n")
                self.txt_dpi_ekran.see("end")
            else:
                self.txt_dpi_ekran.insert("1.0", f"[*] '{filtre_kodu}' kategorisinde henüz kayıt yok.\n")

        def ekrani_temizle(self):
            self._ekran_tamponu.clear()
            self.txt_dpi_ekran.delete("1.0", "end")

        def dpi_raporunu_ai_gonder(self):
            icerik = self.txt_dpi_ekran.get("1.0", "end").strip()
            if not icerik:
                return
            if self.ai_analiz_callback:
                self.ai_analiz_callback(f"ALTAR DPI (DERİN PAKET ANALİZİ, JA3 VE DESYNC) TELEMETRİSİ:\n{icerik}")

        def _telemetri_dongusu(self):
            if not self.winfo_exists():
                return
            with self.motor.kilit:
                st = self.motor.istatistikler.copy()
            self.lbl_sayac.configure(
                text=(
                    f"Paket: {st['TOPLAM_PAKET']} | TLS/SNI: {st['TLS_SNI']} | "
                    f"Desync: {st['DESYNC_UYGULANAN']} | Tehdit: {st['TEHDIT_ENGEL']} | "
                    f"Entropi: {st['ORT_ENTROPI']:.2f}"
                )
            )
            if not self.motor.calisiyor and "Durdur" in self.btn_baslat.cget("text"):
                self.btn_baslat.configure(text="▶️ DPI Kalkanını Başlat", fg_color="#00A86B", hover_color="#007F50")
            self.after(1500, self._telemetri_dongusu)


def altar_ters_parcalama_baslat():
    print("=" * 65)
    print("  ALTAR DPI (DERİN PAKET ANALİZİ) & TERS TCP DESYNC SAVUNMA MOTORU")
    print("=" * 65)

    hedef_girdi = input("[?] Kalkan hangi site için aktif edilsin? (Örn: udemy veya tümü için *): ").strip().lower()
    motor = AltarDPIDefenseEngine(log_callback=lambda satir, kat: print(satir))
    motor.hedef_ayarla(hedef_girdi, bolme_bayt=10)
    motor.calisiyor = True

    print(f"\n[*] Hedef '{hedef_girdi or '*'}' olarak ayarlandı.")
    print("[*] DPI Analizi, JA3 Parmak İzi ve Ters TCP Kalkanı devrede. Çıkmak için CTRL+C yapın.\n")

    try:
        motor.windivert_motorunu_calistir(desync_aktif=True)
    except KeyboardInterrupt:
        motor.calisiyor = False
        print("\n[*] Altar DPI güvenli bir şekilde kapatılıyor...")


if __name__ == "__main__":
    if is_admin():
        altar_ters_parcalama_baslat()
    else:
        print("[!] Lütfen terminali/CMD'yi 'Yönetici Olarak Çalıştır' diyerek açın.")
        input("Çıkmak için Enter'a basın...")