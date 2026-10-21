# -*- coding: utf-8 -*-
"""
Altar Python IDE Akıllı Proje Şablonları (altar_kod_sablonlari.py)

Yeni bir Python dosyası açarken sıfırdan başlamak yerine 100-150 satırlık
altın standartta, doğrudan çalışır ve modüler proje mimarileri sunar.
"""

from __future__ import annotations

from typing import Callable, Dict

import customtkinter as ctk


class AltarSablonKutuphanesi:
    """Hazır altın standart mimari şablonları deposu."""

    SABLONLAR: Dict[str, Dict[str, str]] = {
        "GUI_CTK": {
            "baslik": "Modern CustomTkinter GUI Uygulaması",
            "ikon": "🖥️",
            "dosya_adi": "modern_gui_uygulamasi.py",
            "kod": (
                "# -*- coding: utf-8 -*-\n"
                "\"\"\"\n"
                "Altar - Modern CustomTkinter Grafik Arayüz Şablonu\n"
                "Çalıştırmak için: F5 | Kaydetmek için: Ctrl+S\n"
                "\"\"\"\n\n"
                "import customtkinter as ctk\n\n\n"
                "class ModernUygulama(ctk.CTk):\n"
                "    def __init__(self):\n"
                "        super().__init__()\n"
                "        self.title(\"Altar Modern Arayüz Sistemi\")\n"
                "        self.geometry(\"600x420\")\n"
                "        self.configure(fg_color=\"#0B0F19\")\n\n"
                "        # Üst Panel\n"
                "        self.ust_bar = ctk.CTkFrame(self, fg_color=\"#111827\", corner_radius=8)\n"
                "        self.ust_bar.pack(fill=\"x\", padx=12, pady=10)\n\n"
                "        self.lbl_baslik = ctk.CTkLabel(\n"
                "            self.ust_bar, text=\"🌿 Altar Modern Kontrol Paneli\",\n"
                "            font=ctk.CTkFont(size=14, weight=\"bold\"), text_color=\"#10B981\"\n"
                "        )\n"
                "        self.lbl_baslik.pack(side=\"left\", padx=10, pady=8)\n\n"
                "        # Gövde ve Sayaç\n"
                "        self.govde = ctk.CTkFrame(self, fg_color=\"#070B14\", corner_radius=8)\n"
                "        self.govde.pack(fill=\"both\", expand=True, padx=12, pady=(0, 10))\n\n"
                "        self.sayac = 0\n"
                "        self.lbl_sayac = ctk.CTkLabel(\n"
                "            self.govde, text=\"Sayaç Değeri: 0\", font=ctk.CTkFont(size=16, weight=\"bold\"), text_color=\"#38BDF8\"\n"
                "        )\n"
                "        self.lbl_sayac.pack(pady=35)\n\n"
                "        self.btn_arttir = ctk.CTkButton(\n"
                "            self.govde, text=\"➕ Arttır\", width=120, height=32, fg_color=\"#059669\",\n"
                "            hover_color=\"#047857\", command=self.sayac_arttir\n"
                "        )\n"
                "        self.btn_arttir.pack(pady=6)\n\n"
                "    def sayac_arttir(self):\n"
                "        self.sayac += 1\n"
                "        self.lbl_sayac.configure(text=f\"Sayaç Değeri: {self.sayac}\")\n\n\n"
                "if __name__ == \"__main__\":\n"
                "    app = ModernUygulama()\n"
                "    app.mainloop()\n"
            ),
        },
        "VERI_ANALIZ": {
            "baslik": "Pandas & İstatistiksel Veri Analizi",
            "ikon": "📈",
            "dosya_adi": "veri_analizi_ornek.py",
            "kod": (
                "# -*- coding: utf-8 -*-\n"
                "\"\"\"\n"
                "Altar - İstatistiksel Simülasyon ve Veri Analiz Şablonu\n"
                "\"\"\"\n\n"
                "import random\n"
                "import math\n\n\n"
                "def veri_seti_olustur(ornek_sayisi: int = 50) -> list[dict]:\n"
                "    veriler = []\n"
                "    for i in range(1, ornek_sayisi + 1):\n"
                "        sicaklik = round(random.gauss(1450, 45), 2)\n"
                "        basinc = round(101.3 + math.sin(i * 0.2) * 5, 2)\n"
                "        oksijen = round(random.uniform(18.5, 21.0), 1)\n"
                "        veriler.append({\"id\": i, \"sicaklik_K\": sicaklik, \"basinc_kPa\": basinc, \"oksijen_pct\": oksijen})\n"
                "    return veriler\n\n\n"
                "def analiz_raporu_cikar(veriler: list[dict]) -> None:\n"
                "    sicakliklar = [v[\"sicaklik_K\"] for v in veriler]\n"
                "    ort = sum(sicakliklar) / len(sicakliklar)\n"
                "    maks = max(sicakliklar)\n"
                "    min_val = min(sicakliklar)\n"
                "    print(f\"=== VERİ ANALİZ RAPORU (Toplam {len(veriler)} Örnek) ===\")\n"
                "    print(f\"• Ortalama Sıcaklık: {ort:.2f} K\")\n"
                "    print(f\"• En Yüksek Sıcaklık: {maks:.2f} K\")\n"
                "    print(f\"• En Düşük Sıcaklık : {min_val:.2f} K\")\n"
                "    print(\"\\nİlk 5 Kayıt:\")\n"
                "    for v in veriler[:5]:\n"
                "        print(f\"  [#{v['id']}] Sıcaklık: {v['sicaklik_K']} K | Basınç: {v['basinc_kPa']} kPa | O2: %{v['oksijen_pct']}\")\n\n\n"
                "if __name__ == \"__main__\":\n"
                "    ornekler = veri_seti_olustur()\n"
                "    analiz_raporu_cikar(ornekler)\n"
            ),
        },
        "AG_SOKET": {
            "baslik": "Güvenli Soket & Ağ İstemcisi",
            "ikon": "🌐",
            "dosya_adi": "guvenli_ag_istemcisi.py",
            "kod": (
                "# -*- coding: utf-8 -*-\n"
                "\"\"\"\n"
                "Altar - TCP/IP Port ve Servis Doğrulayıcı Ağ Şablonu\n"
                "\"\"\"\n\n"
                "import socket\n"
                "import time\n\n\n"
                "def servis_kontrol_et(hedef: str, port: int, zaman_asimi: float = 2.0) -> bool:\n"
                "    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
                "    s.settimeout(zaman_asimi)\n"
                "    baslangic = time.perf_counter()\n"
                "    try:\n"
                "        sonuc = s.connect_ex((hedef, port))\n"
                "        gecen = (time.perf_counter() - baslangic) * 1000\n"
                "        if sonuc == 0:\n"
                "            print(f\"[+] Port AÇIK: {hedef}:{port} ({gecen:.1f} ms)\")\n"
                "            return True\n"
                "        else:\n"
                "            print(f\"[-] Port KAPALI: {hedef}:{port}\")\n"
                "            return False\n"
                "    except Exception as exc:\n"
                "        print(f\"[!] Bağlantı hatası: {exc}\")\n"
                "        return False\n"
                "    finally:\n"
                "        s.close()\n\n\n"
                "if __name__ == \"__main__\":\n"
                "    print(\"--- HIZLI YEREL SERVİS KONTROLÜ ---\")\n"
                "    servis_kontrol_et(\"127.0.0.1\", 80)     # Web Sunucu\n"
                "    servis_kontrol_et(\"127.0.0.1\", 11434)  # Ollama Yerel AI Portu\n"
            ),
        },
    }


class AltarSablonSeciciModal(ctk.CTkToplevel):
    """Kullanıcının hazır proje şablonu seçmesini sağlayan modal."""

    def __init__(self, master: object, callback: Optional[Callable] = None, on_kod_secildi: Optional[Callable] = None) -> None:
        super().__init__(master)
        self.callback = on_kod_secildi if on_kod_secildi is not None else callback
        self.title("➕ Altar Akıllı Proje Şablonu Seç")
        self.geometry("640x420")
        self.minsize(540, 360)
        self.configure(fg_color="#0B0F19")

        self._arayuz_kur()
        self.transient(master)
        self.grab_set()

    def _arayuz_kur(self) -> None:
        ust = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        ust.pack(side="top", fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            ust, text="📦 Hazır Mimari Şablonları (Doğrudan Çalışır)",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#10B981"
        ).pack(side="left", padx=10, pady=8)

        scroll = ctk.CTkScrollableFrame(self, fg_color="#070B14", corner_radius=8)
        scroll.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 10))

        for anahtar, sablon in AltarSablonKutuphanesi.SABLONLAR.items():
            kutu = ctk.CTkFrame(scroll, fg_color="#0F172A", corner_radius=6)
            kutu.pack(fill="x", padx=4, pady=4)

            satir = ctk.CTkFrame(kutu, fg_color="transparent")
            satir.pack(fill="x", padx=8, pady=8)

            lbl = ctk.CTkLabel(
                satir, text=f"{sablon['ikon']}  {sablon['baslik']}\n    Dosya: {sablon['dosya_adi']}",
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#E2E8F0", justify="left"
            )
            lbl.pack(side="left")

            btn = ctk.CTkButton(
                satir, text="Bu Şablonu Yükle ➡️", width=160, height=30,
                fg_color="#047857", hover_color="#059669", font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda s=sablon: self._sec(s)
            )
            btn.pack(side="right")

    def _sec(self, sablon: Dict[str, str]) -> None:
        self.destroy()
        if callable(self.callback):
            try:
                self.callback(sablon["kod"], sablon["dosya_adi"])
            except TypeError:
                try:
                    self.callback(sablon["dosya_adi"], sablon["kod"])
                except Exception:
                    self.callback(sablon["kod"])
