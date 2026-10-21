import os
import time
import socket
import threading
import subprocess
from collections import deque
import psutil

try:
    import customtkinter as ctk
    from tkinter import messagebox
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
_MEVCUT_PID = os.getpid()
_KORUNAN_SURECLER = {
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe", "services.exe",
    "lsass.exe", "svchost.exe", "explorer.exe", "dwm.exe",
    "ollama.exe", "ollama_llama_server.exe", "llama-server.exe", "ollama_runner.exe"
}

# Süreç bilgilerini 3 saniye boyunca RAM'de tutan thread-safe hızlandırıcı önbellek
_PROC_CACHE = {}
_PROC_CACHE_TIME = 0.0
_CACHE_LOCK = threading.Lock()


def _surec_bilgisi_getir_hizli(pid: int) -> tuple:
    global _PROC_CACHE_TIME
    simdi = time.time()
    with _CACHE_LOCK:
        if simdi - _PROC_CACHE_TIME > 3.0:
            _PROC_CACHE.clear()
            _PROC_CACHE_TIME = simdi
        if pid in _PROC_CACHE:
            return _PROC_CACHE[pid]

    uygulama = "Bilinmiyor"
    exe_yolu = ""
    ram_mb = 0.0
    if pid > 0:
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                uygulama = proc.name()
                ram_mb = proc.memory_info().rss / (1024 * 1024)
                try:
                    exe_yolu = proc.exe()
                except Exception:
                    exe_yolu = ""
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            uygulama = "Sistem / Erişim Korumalı"

    bilgi = (uygulama, ram_mb, exe_yolu)
    with _CACHE_LOCK:
        _PROC_CACHE[pid] = bilgi
    return bilgi


def aktif_portlari_getir(filtre_metni: str = "") -> list:
    sonuclar = []
    filtre = filtre_metni.strip().lower()

    try:
        baglantilar = psutil.net_connections(kind='inet')
    except Exception:
        return sonuclar

    for conn in baglantilar:
        yerel_ip = conn.laddr.ip if conn.laddr else "0.0.0.0"
        yerel_port = conn.laddr.port if conn.laddr else 0
        yerel_adres = f"{yerel_ip}:{yerel_port}"

        uzak_adres = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
        durum = conn.status
        pid = conn.pid or 0
        protokol = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"

        uygulama, ram_mb, exe_yolu = _surec_bilgisi_getir_hizli(pid)

        satir_metni = f"{protokol:<6} | {yerel_adres:<22} | {uzak_adres:<21} | {durum:<12} | {pid:<7} | {uygulama:<24} | {ram_mb:>6.1f} MB"
        if filtre and (filtre not in satir_metni.lower() and filtre not in exe_yolu.lower()):
            continue

        sonuclar.append({
            "protokol": protokol,
            "yerel_adres": yerel_adres,
            "port": yerel_port,
            "uzak_adres": uzak_adres,
            "durum": durum,
            "pid": pid,
            "uygulama": uygulama,
            "ram_mb": ram_mb,
            "exe_yolu": exe_yolu,
            "formatli": satir_metni
        })

    sonuclar.sort(key=lambda x: (x["durum"] != "LISTEN", x["port"]))
    return sonuclar


def aktif_portlari_tara():
    print(f"{'Protokol':<10} {'Yerel Adres':<25} {'Durum':<15} {'PID':<10} {'Uygulama Adı'}")
    print("-" * 80)
    for kayit in aktif_portlari_getir():
        print(f"{kayit['protokol']:<10} {kayit['yerel_adres']:<25} {kayit['durum']:<15} {kayit['pid']:<10} {kayit['uygulama']}")


def uygulama_sonlandir_pid_veya_port(hedef_girdi: str, zorla: bool = True) -> tuple:
    hedef = hedef_girdi.strip()
    if not hedef:
        return False, "Lütfen bir PID, Port numarası veya uygulama adı girin."

    hedef_pidler = set()
    for kayit in aktif_portlari_getir():
        if hedef.isdigit():
            sayi = int(hedef)
            if kayit["pid"] == sayi or kayit["port"] == sayi:
                if kayit["pid"] > 0:
                    hedef_pidler.add((kayit["pid"], kayit["uygulama"]))
        else:
            if hedef.lower() in kayit["uygulama"].lower():
                if kayit["pid"] > 0:
                    hedef_pidler.add((kayit["pid"], kayit["uygulama"]))

    if not hedef_pidler and hedef.isdigit():
        try:
            p = psutil.Process(int(hedef))
            hedef_pidler.add((p.pid, p.name()))
        except Exception:
            pass

    if not hedef_pidler:
        return False, f"'{hedef}' ile eşleşen aktif bir port veya uygulama (PID) bulunamadı."

    kapatilanlar, hatalar = [], []
    for pid, isim in hedef_pidler:
        if pid in (0, 4, _MEVCUT_PID) or isim.lower() in _KORUNAN_SURECLER:
            hatalar.append(f"Korunan sistem/Altar süreci ({isim} - PID {pid}) kapatılamaz.")
            continue
        try:
            p = psutil.Process(pid)
            p.kill() if zorla else p.terminate()
            kapatilanlar.append(f"{isim} (PID: {pid})")
        except Exception as e:
            hatalar.append(f"{isim} (PID {pid}): {e}")

    if kapatilanlar:
        return True, f"Devre Dışı Bırakılan Uygulamalar: {', '.join(kapatilanlar)}"
    return False, "Hata: " + "; ".join(hatalar)


def uygulama_dondur_veya_surdur(hedef_pid: int, dondur: bool = True) -> tuple:
    if hedef_pid in (0, 4, _MEVCUT_PID):
        return False, f"Korunan süreç (PID: {hedef_pid}) dondurulamaz."
    try:
        p = psutil.Process(hedef_pid)
        isim = p.name()
        if dondur and isim.lower() in _KORUNAN_SURECLER:
            return False, f"Korunan sistem süreci ('{isim}') dondurulamaz."
        if dondur:
            p.suspend()
            return True, f"⏸️ '{isim}' (PID: {hedef_pid}) askıya alındı (Donduruldu)."
        else:
            p.resume()
            return True, f"▶️ '{isim}' (PID: {hedef_pid}) tekrar etkinleştirildi (Devam Ediyor)."
    except Exception as e:
        return False, f"İşlem başarısız: {e}"


def uygulama_internetini_engelle(hedef_pid_veya_port: str, engelle: bool = True) -> tuple:
    kayitlar = aktif_portlari_getir()
    hedef_port, hedef_exe, hedef_isim = None, "", hedef_pid_veya_port.strip()

    for k in kayitlar:
        if hedef_isim.isdigit() and (k["pid"] == int(hedef_isim) or k["port"] == int(hedef_isim)):
            hedef_port, hedef_exe, hedef_isim = k["port"], k["exe_yolu"], k["uygulama"]
            break
        elif hedef_isim.lower() in k["uygulama"].lower():
            hedef_port, hedef_exe, hedef_isim = k["port"], k["exe_yolu"], k["uygulama"]
            break

    temiz_ad = "".join(c if c.isalnum() or c in "_-." else "_" for c in hedef_isim)
    kural_adi = f"Altar_AppBlock_{temiz_ad}"
    if not engelle:
        subprocess.run(
            ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={kural_adi}"],
            shell=False, capture_output=True, creationflags=_NO_WINDOW
        )
        return True, f"🔓 '{hedef_isim}' için güvenlik duvarı ağ engeli kaldırıldı."

    if hedef_exe and os.path.exists(hedef_exe):
        temiz_exe = os.path.abspath(hedef_exe)
        subprocess.run(
            [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={kural_adi}", "dir=in", "action=block", f"program={temiz_exe}", "enable=yes"
            ],
            shell=False, capture_output=True, creationflags=_NO_WINDOW
        )
        sonuc = subprocess.run(
            [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={kural_adi}", "dir=out", "action=block", f"program={temiz_exe}", "enable=yes"
            ],
            shell=False, capture_output=True, creationflags=_NO_WINDOW
        )
        if sonuc.returncode == 0:
            return True, f"⛔ '{hedef_isim}' uygulamasının internet/ağ erişimi Güvenlik Duvarı'nda engellendi!"

    if hedef_port and 1 <= int(hedef_port) <= 65535 and int(hedef_port) != 11434:
        sonuc = subprocess.run(
            [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={kural_adi}", "dir=in", "action=block", "protocol=TCP", f"localport={int(hedef_port)}"
            ],
            shell=False, capture_output=True, creationflags=_NO_WINDOW
        )
        if sonuc.returncode == 0:
            return True, f"⛔ Port {hedef_port} ({hedef_isim}) Güvenlik Duvarı'nda kapatıldı!"

    return False, "Güvenlik duvarı kuralı eklenemedi (Yönetici izni veya geçerli PID/Port gerekli)."


if CTK_AVAILABLE:
    class PortVeUygulamaPaneli(ctk.CTkFrame):
        def __init__(self, parent):
            super().__init__(parent, fg_color="#0B1320", corner_radius=8, border_width=1, border_color="#1E293B")
            self._arama_timer = None
            self._tarama_suruyor = False
            self._son_kayitlar_bellek = []
            self._ui_kuyrugu = deque()
            self._arayuz_olustur()
            self.after(120, self._ui_kuyruk_dongusu)
            self.after(400, self.portlari_yenile)

        def _ui_kuyruk_dongusu(self):
            try:
                if not self.winfo_exists():
                    return
                while self._ui_kuyrugu:
                    gorev = self._ui_kuyrugu.popleft()
                    gorev()
                self.after(120, self._ui_kuyruk_dongusu)
            except Exception:
                pass

        def _arayuz_olustur(self):
            ust = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
            ust.pack(side="top", fill="x", padx=6, pady=4)

            ctk.CTkLabel(
                ust, text="🔌 2. BÖLÜM: PORT TARAYICI & UYGULAMA DEVRE DIŞI BIRAKMA MERKEZİ",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#FFD700"
            ).pack(side="left", padx=8, pady=3)

            self.lbl_port_sayac = ctk.CTkLabel(
                ust, text="Aktif Bağlantı: 0",
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#58A6FF"
            )
            self.lbl_port_sayac.pack(side="right", padx=8, pady=3)

            filtre_bar = ctk.CTkFrame(self, fg_color="transparent")
            filtre_bar.pack(side="top", fill="x", padx=6, pady=2)

            self.entry_filtre = ctk.CTkEntry(
                filtre_bar, placeholder_text="Port, PID, IP veya Uygulama Adı Filtrele (Örn: 8080, chrome.exe, LISTEN)...",
                height=24, font=ctk.CTkFont(family="Consolas", size=11)
            )
            self.entry_filtre.pack(side="left", fill="x", expand=True, padx=(0, 4))
            self.entry_filtre.bind("<KeyRelease>", self._filtre_degisti_debounce)

            ctk.CTkButton(
                filtre_bar, text="🔄 Portları Tara", width=110, height=24, font=ctk.CTkFont(size=11),
                fg_color="#1f538d", command=self.portlari_yenile
            ).pack(side="right", padx=2)

            aksiyon_bar = ctk.CTkFrame(self, fg_color="transparent")
            aksiyon_bar.pack(side="top", fill="x", padx=6, pady=2)

            ctk.CTkLabel(aksiyon_bar, text="Hedef:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 2))
            self.entry_hedef = ctk.CTkEntry(
                aksiyon_bar, placeholder_text="PID, Port veya exe", width=112, height=24, font=ctk.CTkFont(family="Consolas", size=11)
            )
            self.entry_hedef.pack(side="left", padx=2)

            ctk.CTkButton(
                aksiyon_bar, text="🛑 Devre Dışı Bırak (Kill)", width=134, height=24, font=ctk.CTkFont(size=11),
                fg_color="#8B0000", hover_color="#5c0000", command=self.uygulama_kapat_tetikle
            ).pack(side="left", padx=1)

            ctk.CTkButton(
                aksiyon_bar, text="⏸️ Dondur", width=68, height=24, font=ctk.CTkFont(size=11),
                fg_color="#B85C00", command=lambda: self.dondur_surdur_tetikle(True)
            ).pack(side="left", padx=1)

            ctk.CTkButton(
                aksiyon_bar, text="▶️ Sürdür", width=68, height=24, font=ctk.CTkFont(size=11),
                fg_color="#2E7D32", command=lambda: self.dondur_surdur_tetikle(False)
            ).pack(side="left", padx=1)

            ctk.CTkButton(
                aksiyon_bar, text="⛔ Ağı Kes", width=72, height=24, font=ctk.CTkFont(size=11),
                fg_color="#4B0082", command=lambda: self.ag_engelle_tetikle(True)
            ).pack(side="left", padx=1)

            ctk.CTkButton(
                aksiyon_bar, text="🔓 Ağı Aç", width=68, height=24, font=ctk.CTkFont(size=11),
                fg_color="#008080", command=lambda: self.ag_engelle_tetikle(False)
            ).pack(side="left", padx=(1, 0))

            self.txt_port_liste = ctk.CTkTextbox(
                self, font=ctk.CTkFont(family="Consolas", size=11),
                fg_color="#05080F", text_color="#E2E8F0", height=95, wrap="none"
            )
            self.txt_port_liste.pack(side="top", fill="both", expand=True, padx=6, pady=(2, 6))

        def _filtre_degisti_debounce(self, _event=None):
            if self._arama_timer:
                self.after_cancel(self._arama_timer)
            self._arama_timer = self.after(150, self._bellekten_filtrele)

        def _bellekten_filtrele(self):
            """Arama kutusuna yazıldığında sistemi tekrar yormadan RAM'deki son listeden anında filtreler."""
            if not self._son_kayitlar_bellek:
                self.portlari_yenile()
                return
            filtre = self.entry_filtre.get().strip().lower()
            if not filtre:
                eslesenler = self._son_kayitlar_bellek
            else:
                eslesenler = [
                    k for k in self._son_kayitlar_bellek
                    if filtre in k["formatli"].lower() or filtre in k["exe_yolu"].lower()
                ]
            self._tabloyu_ekrana_ciz(eslesenler)

        def _tabloyu_ekrana_ciz(self, kayitlar: list):
            if not self.winfo_exists():
                return
            baslik = f"{'PROTO':<6} | {'YEREL ADRES:PORT':<22} | {'UZAK ADRES:PORT':<21} | {'DURUM':<12} | {'PID':<7} | {'UYGULAMA ADI':<24} | {'BELLEK'}"
            ayrac = "-" * 108
            metin = "\n".join([baslik, ayrac] + [k["formatli"] for k in kayitlar[:200]])
            self.lbl_port_sayac.configure(text=f"Aktif Bağlantı: {len(kayitlar)}")
            self.txt_port_liste.delete("1.0", "end")
            self.txt_port_liste.insert("1.0", metin)

        def portlari_yenile(self):
            if self._tarama_suruyor:
                return
            self._tarama_suruyor = True
            filtre = self.entry_filtre.get().strip().lower() if hasattr(self, "entry_filtre") else ""

            def _arka_plan():
                try:
                    tum_kayitlar = aktif_portlari_getir("")
                    self._son_kayitlar_bellek = tum_kayitlar
                    if filtre:
                        gosterilecek = [
                            k for k in tum_kayitlar
                            if filtre in k["formatli"].lower() or filtre in k["exe_yolu"].lower()
                        ]
                    else:
                        gosterilecek = tum_kayitlar

                    self._ui_kuyrugu.append(lambda: self._tabloyu_ekrana_ciz(gosterilecek))
                finally:
                    self._tarama_suruyor = False

            threading.Thread(target=_arka_plan, daemon=True).start()

        def uygulama_kapat_tetikle(self):
            hedef = self.entry_hedef.get().strip()
            def _islem():
                basari, mesaj = uygulama_sonlandir_pid_veya_port(hedef, zorla=True)
                self._ui_kuyrugu.append(lambda: (
                    self.txt_port_liste.insert("1.0", f"[{'BAŞARILI' if basari else 'UYARI'}] {mesaj}\n\n"),
                    self.after(200, self.portlari_yenile)
                ))
            threading.Thread(target=_islem, daemon=True).start()

        def dondur_surdur_tetikle(self, dondur: bool):
            hedef = self.entry_hedef.get().strip()
            if not hedef.isdigit():
                messagebox.showwarning("PID Gerekli", "Dondurma/Sürdürme işlemi için lütfen listedeki sayısal PID numarasını girin.")
                return
            pid_no = int(hedef)
            def _islem():
                _, mesaj = uygulama_dondur_veya_surdur(pid_no, dondur=dondur)
                self._ui_kuyrugu.append(lambda: self.txt_port_liste.insert("1.0", f"{mesaj}\n\n"))
            threading.Thread(target=_islem, daemon=True).start()

        def ag_engelle_tetikle(self, engelle: bool):
            hedef = self.entry_hedef.get().strip()
            if not hedef:
                return
            def _islem():
                _, mesaj = uygulama_internetini_engelle(hedef, engelle=engelle)
                self._ui_kuyrugu.append(lambda: self.txt_port_liste.insert("1.0", f"{mesaj}\n\n"))
            threading.Thread(target=_islem, daemon=True).start()


if __name__ == "__main__":
    aktif_portlari_tara()
    input("\nÇıkmak için Enter'a basın...")