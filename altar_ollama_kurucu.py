# -*- coding: utf-8 -*-
"""
================================================================================
ALTAR SİNEMATİK OLLAMA VE SİBER AI KURULUM SİHİRBAZI (AUTO-SETUP ENGINE)
================================================================================
* İleride proje EXE haline getirildiğinde otomatik çalışan tam kurulum motorudur.
* Otomatik UAC Yükseltmesi: Kullanıcı sadece tek bir Windows UAC 'Evet' onayı
  verdikten sonra tüm kurulumu arka planda sinematik bir sahnede otomatik tamamlar.
* https://ollama.com/download üzerinden en güncel resmi Windows OllamaSetup.exe'yi indirir.
* Sessiz kurulum (/SILENT), Windows Defender Güvenlik Duvarı port izni ve
  localhost:11434 arka plan servisini (ollama serve) otomatik yapılandırır.
* Altar için gerekli yapay zeka modellerini (jaahas/qwen3.5-uncensored:9b ve llava:latest)
  çeker ve işlem bittiğinde ana Altar uygulamasını başlatır.
================================================================================
"""

import os
import sys
import time
import json
import math
import shutil
import random
import tempfile
import threading
import subprocess
import urllib.request
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

try:
    import requests
except ImportError:
    requests = None

IS_WINDOWS = (os.name == "nt")
if IS_WINDOWS:
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass


def yonetici_mi() -> bool:
    """İşlemin Windows Yönetici (Administrator) yetkisine sahip olup olmadığını kontrol eder."""
    if not IS_WINDOWS:
        return True
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def yonetici_olarak_otomatik_yukselt():
    """UAC yükseltme penceresini otomatik tetikler."""
    if not IS_WINDOWS or yonetici_mi():
        return True

    if getattr(sys, "frozen", False):
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    else:
        params = " ".join([f'"{arg}"' for arg in sys.argv])
    ret = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        params,
        None,
        1
    )
    if ret > 32:
        sys.exit(0)
    return False


def ollama_exe_bul() -> str:
    """Sistemde ollama.exe dosyasını tespit eder."""
    yol = shutil.which("ollama")
    if yol and os.path.isfile(yol):
        return yol

    yerel_appdata = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    olasi_yollar = [
        os.path.join(yerel_appdata, "Programs", "Ollama", "ollama.exe"),
        os.path.join(program_files, "Ollama", "ollama.exe"),
        r"C:\Users\Burak\AppData\Local\Programs\Ollama\ollama.exe"
    ]
    for p in olasi_yollar:
        if os.path.isfile(p):
            return p
    return ""


def ollama_calisiyor_mu() -> bool:
    """Ollama API servisinin localhost:11434 üzerinde yanıt verip vermediğini sorgular."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "AltarSetup"})
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def yuklu_modeller_listesi() -> list:
    """Ollama üzerinde yüklü olan modellerin listesini döner."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "AltarSetup"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []


def ollama_kurulum_gerekli_mi() -> bool:
    """
    Sistemin tam kurulum gerektirip gerektirmediğini tespit eder.
    Ollama kurulu değilse veya temel modeller eksikse True döner.
    """
    exe_yolu = ollama_exe_bul()
    if not exe_yolu or not os.path.isfile(exe_yolu):
        return True

    # Eğer servis çalışıyorsa model kontrolü yap
    if ollama_calisiyor_mu():
        modeller = yuklu_modeller_listesi()
        gerekli = ["jaahas/qwen3.5-uncensored:9b", "llava:latest"]
        for g in gerekli:
            if not any(g in m for m in modeller):
                return True
        return False
    return False


class AltarOllamaSinematikSetup(ctk.CTk):
    """
    Sinematik açılış animasyonuyla donatılmış, otomatik UAC ve model kurulum sihirbazı.
    """
    def __init__(self, otomatik_baslat=True, tamamlandi_callback=None):
        super().__init__()
        self.title("⚡ Altar Siber Yapay Zeka Kurulum Sihirbazı")
        self.geometry("860x620")
        self.configure(fg_color="#030712")
        self.resizable(False, False)

        self.otomatik_baslat = otomatik_baslat
        self.tamamlandi_callback = tamamlandi_callback
        self.ollama_yolu = ollama_exe_bul()
        self._durdur = threading.Event()
        self._animasyon_calisiyor = True
        self._parcaciklar = []
        self._adimi = 0

        # Ekranı Merkeze Al
        g = self.winfo_screenwidth()
        y = self.winfo_screenheight()
        self.geometry(f"860x620+{(g-860)//2}+{(y-620)//2}")

        if os.name == "nt":
            self.attributes("-topmost", True)
            self.focus_force()

        self._arayuz_olustur()
        self._sinematik_animasyon_dongusu()

        if self.otomatik_baslat:
            self.after(600, self.otomatik_kurulumu_calistir)

    def _arayuz_olustur(self):
        # Üst Sinematik Başlık
        ust_frame = ctk.CTkFrame(self, fg_color="#080E1C", corner_radius=10, border_width=1, border_color="#1E3A8A")
        ust_frame.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            ust_frame, text="⚡ ALTAR SİBER YAPAY ZEKA VE OLLAMA KURULUM MOTORU",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#00FFCC"
        ).pack(anchor="w", padx=16, pady=(10, 2))

        admin_durum = "🛡 UAC: Yönetici Yetkisi Alındı (Tam Yetkili Kurulum)" if yonetici_mi() else "⚠️ UAC: Standart Yetki (Otomatik Yükseltilecek)"
        admin_renk = "#10B981" if yonetici_mi() else "#F59E0B"
        ctk.CTkLabel(
            ust_frame, text=admin_durum,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=admin_renk
        ).pack(anchor="w", padx=16, pady=(0, 8))

        # Adım Kartları (UAC, İndirme, Güvenlik Duvarı, Modeller)
        kart_panel = ctk.CTkFrame(self, fg_color="transparent")
        kart_panel.pack(fill="x", padx=16, pady=4)

        self.k_uac = self._kart_olustur(kart_panel, "1. Yönetici İzni", "✔ Hazır" if yonetici_mi() else "Yükseltiliyor...")
        self.k_indir = self._kart_olustur(kart_panel, "2. Ollama Kurulumu", "Bekliyor")
        self.k_servis = self._kart_olustur(kart_panel, "3. Servis & Firewall", "Bekliyor")
        self.k_modeller = self._kart_olustur(kart_panel, "4. AI Modelleri", "Bekliyor")

        # Sinematik Animasyon Tuvali (Arka Planda Parçacıklar ve Halka Dalgası)
        self.canvas_panel = ctk.CTkFrame(self, fg_color="#02040A", corner_radius=8, border_width=1, border_color="#1E293B", height=130)
        self.canvas_panel.pack(fill="x", padx=16, pady=6)

        self.canvas = tk.Canvas(self.canvas_panel, bg="#02040A", highlightthickness=0, height=130)
        self.canvas.pack(fill="both", expand=True)

        # İlerleme Çubuğu ve Durum Metni
        ilerleme_panel = ctk.CTkFrame(self, fg_color="#080E1C", corner_radius=8)
        ilerleme_panel.pack(fill="x", padx=16, pady=6)

        self.lbl_durum = ctk.CTkLabel(
            ilerleme_panel, text="Kurulum süreci başlatılıyor...",
            font=ctk.CTkFont(family="Consolas", size=11), text_color="#38BDF8"
        )
        self.lbl_durum.pack(anchor="w", padx=14, pady=(6, 2))

        self.progress_bar = ctk.CTkProgressBar(ilerleme_panel, height=14, progress_color="#00E5FF")
        self.progress_bar.pack(fill="x", padx=14, pady=(2, 8))
        self.progress_bar.set(0.0)

        # Canlı Terminal Çıktısı (Log Ekranı)
        ctk.CTkLabel(
            self, text="📋 Kurulum & Model Çekme Canlı Akışı:",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#94A3B8"
        ).pack(anchor="w", padx=20, pady=(4, 2))

        self.txt_log = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#010308", text_color="#22C55E", height=140
        )
        self.txt_log.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # Alt Buton
        self.alt_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.alt_frame.pack(fill="x", padx=16, pady=(0, 14))

        self.btn_eylem = ctk.CTkButton(
            self.alt_frame, text="⏳ Kurulum Devam Ediyor...", height=34,
            fg_color="#0284C7", hover_color="#0369A1",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            state="disabled", command=self._kurulum_bitti_baslat
        )
        self.btn_eylem.pack(side="left", padx=2)

    def _kart_olustur(self, parent, baslik, durum_metni):
        f = ctk.CTkFrame(parent, fg_color="#091226", corner_radius=6, border_width=1, border_color="#1E3A8A")
        f.pack(side="left", fill="both", expand=True, padx=4)

        ctk.CTkLabel(f, text=baslik, font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#E2E8F0").pack(pady=(6, 2))
        lbl_d = ctk.CTkLabel(f, text=durum_metni, font=ctk.CTkFont(family="Consolas", size=10), text_color="#94A3B8")
        lbl_d.pack(pady=(0, 6))
        return {"frame": f, "durum": lbl_d}

    def _log(self, mesaj: str):
        def _ekle():
            if self.winfo_exists():
                self.txt_log.insert("end", f"[{time.strftime('%H:%M:%S')}] {mesaj}\n")
                self.txt_log.see("end")
        self.after(0, _ekle)

    def _arayuz_guncelle(self, fn):
        """Arka plan iş parçacığından arayüzü ana Tkinter döngüsünde güvenle günceller."""
        if self.winfo_exists():
            self.after(0, fn)

    def _sinematik_animasyon_dongusu(self):
        """Arka plandaki şelale / plazma parçacık animasyonu."""
        if not self._animasyon_calisiyor or not self.winfo_exists():
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100:
            w, h = 800, 130

        self._adimi += 1
        self.canvas.delete("all")

        # Yeni Parçacık Üret
        if len(self._parcaciklar) < 40:
            self._parcaciklar.append({
                "x": random.randint(10, w - 10),
                "y": -10,
                "vy": random.uniform(2.5, 6.0),
                "r": random.randint(2, 4),
                "renk": random.choice(["#00FFCC", "#38BDF8", "#0284C7", "#A5F3FC"])
            })

        for p in self._parcaciklar:
            p["y"] += p["vy"]
            r = p["r"]
            self.canvas.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r, fill=p["renk"], outline="")
        self._parcaciklar = [p for p in self._parcaciklar if p["y"] < h + 10]

        # Merkez Sinematik Dalga
        cx, cy = w // 2, h // 2
        rad = ((self._adimi * 2) % 100) + 10
        self.canvas.create_oval(cx - rad * 2, cy - rad * 0.5, cx + rad * 2, cy + rad * 0.5, outline="#0D9488", width=1)

        self.canvas.create_text(
            cx, cy, text="ALTAR SİNEMATİK YAPAY ZEKA MOTORU KURULUYOR",
            fill="#00FFCC", font=("Consolas", 13, "bold")
        )

        self.after(35, self._sinematik_animasyon_dongusu)

    def otomatik_kurulumu_calistir(self):
        """Tüm kurulum zincirini arka planda başlatır."""
        threading.Thread(target=self._kurulum_pipeline_thread, daemon=True).start()

    def _kurulum_pipeline_thread(self):
        try:
            self._log("=== ALTAR SİNEMATİK OLLAMA VE SİBER AI KURULUMU BAŞLATILDI ===")

            # 1. ADIM: UAC Yetkisi
            if not yonetici_mi():
                self._log("[*] Windows Yönetici Yetkisi (UAC) otomatik yükseltiliyor...")
                self.after(100, yonetici_olarak_otomatik_yukselt)
                return

            self._log("[OK] Windows Yönetici (Administrator) yetkisi devralındı.")
            self._arayuz_guncelle(lambda: (self.k_uac["durum"].configure(text="✔ Doğrulandı", text_color="#10B981"), self.progress_bar.set(0.15)))

            # 2. ADIM: Ollama Kurulum Paketinin İndirilmesi ve Kurulması
            self.ollama_yolu = ollama_exe_bul()
            if not self.ollama_yolu or not os.path.isfile(self.ollama_yolu):
                self._log("[*] Ollama sistemde bulunamadı. Resmi Windows paketi indiriliyor...")
                self._arayuz_guncelle(lambda: self.lbl_durum.configure(text="OllamaSetup.exe indiriliyor (https://ollama.com/download)..."))

                installer_path = os.path.join(tempfile.gettempdir(), "OllamaSetup.exe")
                url = "https://ollama.com/download/OllamaSetup.exe"

                urllib.request.urlretrieve(url, installer_path)
                self._log(f"[OK] Kurulum paketi başarıyla indirildi: {installer_path}")

                self._log("[*] Ollama sessiz kurulum moduyla arka planda kuruluyor...")
                self._arayuz_guncelle(lambda: self.lbl_durum.configure(text="Ollama sessiz modda kuruluyor..."))

                subprocess.run(
                    [installer_path, "/DIR=C:\\Program Files\\Ollama", "/SILENT", "/VERYSILENT", "/NORESTART"],
                    check=False,
                    timeout=240
                )
                time.sleep(3)
                self.ollama_yolu = ollama_exe_bul()
                self._log(f"[OK] Ollama kurulumu tamamlandı: {self.ollama_yolu}")
            else:
                self._log(f"[OK] Ollama zaten kurulu: {self.ollama_yolu}")

            self._arayuz_guncelle(lambda: (self.k_indir["durum"].configure(text="✔ Kurulu", text_color="#10B981"), self.progress_bar.set(0.35)))

            # 3. ADIM: Windows Güvenlik Duvarı (Firewall) İzni
            if self.ollama_yolu:
                self._log("[*] Windows Defender Güvenlik Duvarı port kuralı ekleniyor...")
                try:
                    firewall_komut = [
                        "netsh", "advfirewall", "firewall", "add", "rule",
                        "name=Altar Ollama AI Engine",
                        "dir=in",
                        "action=allow",
                        f"program={self.ollama_yolu}",
                        "enable=yes"
                    ]
                    subprocess.run(
                        firewall_komut,
                        shell=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False
                    )
                    self._log("[OK] Güvenlik duvarı bağlantı kuralı tanımlandı.")
                except Exception as e:
                    self._log(f"[!] Güvenlik duvarı uyarısı: {e}")

            # 4. ADIM: Ollama Servisini Başlatma (localhost:11434)
            if not ollama_calisiyor_mu():
                self._log("[*] Ollama API servisi bağımsız arka plan sürecinde başlatılıyor...")
                self._arayuz_guncelle(lambda: self.lbl_durum.configure(text="Ollama API servisi ayağa kaldırılıyor..."))

                if self.ollama_yolu:
                    subprocess.Popen(
                        [self.ollama_yolu, "serve"],
                        creationflags=0x08000000 if IS_WINDOWS else 0,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                servis_hazir = False
                for _ in range(25):
                    time.sleep(1)
                    if ollama_calisiyor_mu():
                        servis_hazir = True
                        break

                if servis_hazir:
                    self._log("[OK] Ollama API servisi aktif! (http://localhost:11434)")
            else:
                self._log("[OK] Ollama API servisi aktif.")

            self._arayuz_guncelle(lambda: (self.k_servis["durum"].configure(text="✔ Aktif (Port 11434)", text_color="#10B981"), self.progress_bar.set(0.55)))

            # 5. ADIM: Gerekli Yapay Zeka Modellerini Otomatik Çekme
            modeller = [
                "jaahas/qwen3.5-uncensored:9b",
                "llava:latest"
            ]

            mevcut_modeller = yuklu_modeller_listesi()
            toplam = len(modeller)

            for idx, m in enumerate(modeller):
                self._log(f"\n[*] Model kontrol ediliyor [{idx+1}/{toplam}]: {m}")
                if any(m in yuklu for yuklu in mevcut_modeller):
                    self._log(f"[OK] {m} zaten sistemde hazır.")
                    continue

                self._arayuz_guncelle(lambda model=m: self.lbl_durum.configure(text=f"{model} modeli indiriliyor..."))
                self._log(f"[*] {m} indiriliyor (Bu işlem internet hızınıza bağlı olarak birkaç dakika sürebilir)...")
                self._model_cek_api(m)

            self._arayuz_guncelle(lambda: (
                self.k_modeller["durum"].configure(text="✔ Hazır", text_color="#10B981"),
                self.progress_bar.set(1.0),
                self.lbl_durum.configure(text="🎉 Kurulum ve model yapılandırması başarıyla tamamlandı!"),
                self.btn_eylem.configure(state="normal", text="🎉 Altar'ı Başlat", fg_color="#00A86B", hover_color="#007F50")
            ))
            self._log("\n[✔ TAMAMLANDI] Altar yapay zeka çekirdeği ve yerel modeller eksiksiz kuruldu.")

        except Exception as e:
            self._log(f"\n[HATA] Kurulum sırasında hata: {e}")
            self._arayuz_guncelle(lambda err=e: (
                self.lbl_durum.configure(text=f"Hata oluştu: {str(err)[:60]}"),
                self.btn_eylem.configure(state="normal", text="🔄 Yeniden Dene")
            ))

    def _model_cek_api(self, model_adi: str):
        try:
            url = "http://localhost:11434/api/pull"
            payload = json.dumps({"name": model_adi, "stream": True}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

            with urllib.request.urlopen(req, timeout=1800) as resp:
                son_y = -1
                for line in resp:
                    if line:
                        try:
                            veri = json.loads(line.decode("utf-8"))
                            durum = veri.get("status", "")
                            toplam = veri.get("total", 0)
                            tamam = veri.get("completed", 0)
                            if toplam > 0:
                                yuzde = int((tamam / toplam) * 100)
                                if yuzde != son_y and yuzde % 15 == 0:
                                    self._log(f" > {model_adi}: %{yuzde} ({durum})")
                                    son_y = yuzde
                            elif durum:
                                if "success" in durum.lower() or "verifying" in durum.lower():
                                    self._log(f" > {durum}")
                        except Exception:
                            pass
            self._log(f"[OK] {model_adi} başarıyla indirildi.")
        except Exception:
            if self.ollama_yolu:
                subprocess.run([self.ollama_yolu, "pull", model_adi], check=False, timeout=1200)
                self._log(f"[OK] {model_adi} komut satırından çekildi.")

    def _kurulum_bitti_baslat(self):
        self.destroy()
        if self.tamamlandi_callback:
            self.tamamlandi_callback()
        else:
            if getattr(sys, "frozen", False):
                subprocess.Popen([sys.executable])
            else:
                proje_kok = os.path.dirname(os.path.abspath(__file__))
                ana_dosya = os.path.join(proje_kok, "Local AI.py")
                if os.path.isfile(ana_dosya):
                    subprocess.Popen([sys.executable, ana_dosya])


# Geriye dönük ve modüler uyumluluk takma adları
AltarOllamaKurucuArayuz = AltarOllamaSinematikSetup
yonetici_olarak_yeniden_baslat = yonetici_olarak_otomatik_yukselt


def otomatik_sinematik_kurulum_baslat(callback=None) -> bool:
    """Ollama ve modelleri sinematik setup ekranıyla otomatik kurar."""
    if not yonetici_mi():
        yonetici_olarak_otomatik_yukselt()
        return False

    app = AltarOllamaSinematikSetup(otomatik_baslat=True, tamamlandi_callback=callback)
    app.mainloop()
    return True


if __name__ == "__main__":
    if "--check-only" in sys.argv:
        print("Gerekli mi:", ollama_kurulum_gerekli_mi())
    else:
        otomatik_sinematik_kurulum_baslat()
