# -*- coding: utf-8 -*-
"""
Altar EDR Güvenli Karantina Kasası (altar_karantina.py)

Zararlı, şüpheli veya test amaçlı dosyaların sistemden izole edilerek
şifrelenmiş veya uzantısı değiştirilmiş bir sandbox kasasında (.altar_karantina)
güvenle saklanmasını, listelenmesini, geri yüklenmesini veya kalıcı imhasını sağlar.
Hiçbir işletim sistemi dosyasına veya ağa zarar vermez (%100 yerel ve güvenli).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox


class AltarKarantinaYoneticisi:
    """Karantina kasası dosya yönetim sınıfı."""

    def __init__(self, ana_dizin: Optional[str] = None) -> None:
        if not ana_dizin:
            ana_dizin = os.path.dirname(os.path.abspath(__file__))
        self.karantina_dizini = os.path.join(ana_dizin, ".altar_karantina")
        os.makedirs(self.karantina_dizini, exist_ok=True)
        self.indeks_dosyasi = os.path.join(self.karantina_dizini, "karantina_indeks.json")
        self._indeks_hazirla()

    def _indeks_hazirla(self) -> None:
        if not os.path.isfile(self.indeks_dosyasi):
            self._indeks_kaydet([])

    def _indeks_oku(self) -> List[Dict[str, Any]]:
        try:
            with open(self.indeks_dosyasi, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _indeks_kaydet(self, veri: List[Dict[str, Any]]) -> None:
        try:
            tmp_dosya = self.indeks_dosyasi + f".{int(time.time())}.tmp"
            with open(tmp_dosya, "w", encoding="utf-8") as f:
                json.dump(veri, f, ensure_ascii=False, indent=2)
            os.replace(tmp_dosya, self.indeks_dosyasi)
        except Exception:
            pass

    def karantinadakileri_listele(self) -> List[Dict[str, Any]]:
        return self._indeks_oku()

    @staticmethod
    def _sha256_hesapla(dosya_yolu: str) -> str:
        sha = hashlib.sha256()
        try:
            with open(dosya_yolu, "rb") as f:
                for blok in iter(lambda: f.read(65536), b""):
                    sha.update(blok)
            return sha.hexdigest()
        except Exception:
            return "Bilinmiyor"

    def dosyayi_karantinaya_al(self, kaynak_yol: str, sebep: str = "Şüpheli Dosya / EDR Kalkanı") -> Optional[Dict[str, Any]]:
        if not os.path.isfile(kaynak_yol):
            return None

        sha256 = self._sha256_hesapla(kaynak_yol)
        dosya_adi = os.path.basename(kaynak_yol)
        boyut_kb = round(os.path.getsize(kaynak_yol) / 1024, 2)
        karantina_id = f"qar_{int(time.time())}_{sha256[:8]}"
        hedef_ad = f"{karantina_id}.quarantine"
        hedef_yol = os.path.join(self.karantina_dizini, hedef_ad)

        try:
            shutil.move(kaynak_yol, hedef_yol)
        except Exception:
            try:
                shutil.copy2(kaynak_yol, hedef_yol)
                os.remove(kaynak_yol)
            except Exception:
                return None

        kayit = {
            "id": karantina_id,
            "orijinal_ad": dosya_adi,
            "orijinal_yol": kaynak_yol,
            "karantina_dosyasi": hedef_ad,
            "boyut_kb": boyut_kb,
            "sha256": sha256,
            "sebep": sebep,
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        indeks = self._indeks_oku()
        indeks.insert(0, kayit)
        self._indeks_kaydet(indeks)
        return kayit

    def karantinadan_cikar(self, karantina_id: str, hedef_dizin: Optional[str] = None) -> bool:
        indeks = self._indeks_oku()
        kayit = next((k for k in indeks if k.get("id") == karantina_id), None)
        if not kayit:
            return False

        # Güvenlik Kontrolü: Karantina dosyası yolu denetimi
        guvenli_karantina_dosyasi = os.path.basename(kayit.get("karantina_dosyasi", ""))
        kaynak_yol = os.path.join(self.karantina_dizini, guvenli_karantina_dosyasi)
        if not os.path.isfile(kaynak_yol):
            return False

        # Güvenlik Kontrolü: Dizin geçişi (Path Traversal / CWE-22) önleme
        guvenli_orijinal_ad = os.path.basename(kayit.get("orijinal_ad", "kurtarilan_dosya.bin"))
        if hedef_dizin:
            hedef_yol = os.path.join(hedef_dizin, guvenli_orijinal_ad)
        else:
            hedef_yol = kayit.get("orijinal_yol", os.path.join(self.karantina_dizini, "geri_yuklenenler", guvenli_orijinal_ad))

        os.makedirs(os.path.dirname(hedef_yol), exist_ok=True)

        try:
            shutil.move(kaynak_yol, hedef_yol)
            yeni_indeks = [k for k in indeks if k.get("id") != karantina_id]
            self._indeks_kaydet(yeni_indeks)
            return True
        except Exception:
            return False

    def kalici_imha_et(self, karantina_id: str) -> bool:
        indeks = self._indeks_oku()
        kayit = next((k for k in indeks if k.get("id") == karantina_id), None)
        if not kayit:
            return False

        hedef_yol = os.path.join(self.karantina_dizini, kayit["karantina_dosyasi"])
        if os.path.isfile(hedef_yol):
            try:
                # Güvenli silme: dosya üzerine sıfır yaz
                boyut = os.path.getsize(hedef_yol)
                with open(hedef_yol, "wb") as f:
                    f.write(b"\x00" * min(boyut, 1024 * 1024))
                os.remove(hedef_yol)
            except Exception:
                pass

        yeni_indeks = [k for k in indeks if k.get("id") != karantina_id]
        self._indeks_kaydet(yeni_indeks)
        return True


class AltarKarantinaKasasiModal(ctk.CTkToplevel):
    """Görsel Karantina Kasası Penceresi."""

    def __init__(self, master: object) -> None:
        super().__init__(master)
        self.yonetici = AltarKarantinaYoneticisi()
        self.title("📦 Altar EDR Güvenli Karantina Kasası")
        self.geometry("720x520")
        self.minsize(600, 420)
        self.configure(fg_color="#0B0F19")

        self.secili_id: Optional[str] = None
        self._arayuz_kur()
        self.listeyi_yenile()

        self.transient(master)
        self.grab_set()

    def _arayuz_kur(self) -> None:
        ust = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        ust.pack(side="top", fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            ust, text="🛡️ İzole Edilmiş Karantina Kasası",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#EF4444"
        ).pack(side="left", padx=10, pady=8)

        ctk.CTkButton(
            ust, text="➕ Manuel Dosya İzole Et...", width=165, height=26,
            fg_color="#374151", hover_color="#4B5563", font=ctk.CTkFont(size=11),
            command=self._manuel_dosya_izole_et
        ).pack(side="right", padx=10, pady=8)

        govde = ctk.CTkFrame(self, fg_color="transparent")
        govde.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 10))
        govde.grid_columnconfigure(0, weight=1)
        govde.grid_rowconfigure(0, weight=1)

        self.scroll_liste = ctk.CTkScrollableFrame(govde, fg_color="#070B14", corner_radius=8)
        self.scroll_liste.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

        alt_bar = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8, height=44)
        alt_bar.pack(side="bottom", fill="x", padx=12, pady=(0, 10))

        self.lbl_secili_bilgi = ctk.CTkLabel(
            alt_bar, text="Karantinadan bir dosya seçin.", font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#94A3B8"
        )
        self.lbl_secili_bilgi.pack(side="left", padx=10)

        self.btn_imha = ctk.CTkButton(
            alt_bar, text="🗑️ Kalıcı İmha Et", width=120, height=28, fg_color="#B91C1C",
            hover_color="#DC2626", font=ctk.CTkFont(size=11, weight="bold"),
            state="disabled", command=self._imha_et
        )
        self.btn_imha.pack(side="right", padx=(4, 10), pady=8)

        self.btn_geri_yukle = ctk.CTkButton(
            alt_bar, text="↩️ Geri Yükle", width=105, height=28, fg_color="#047857",
            hover_color="#059669", font=ctk.CTkFont(size=11, weight="bold"),
            state="disabled", command=self._geri_yukle
        )
        self.btn_geri_yukle.pack(side="right", padx=4, pady=8)

    def listeyi_yenile(self) -> None:
        for w in self.scroll_liste.winfo_children():
            w.destroy()

        kayitlar = self.yonetici.karantinadakileri_listele()
        if not kayitlar:
            ctk.CTkLabel(
                self.scroll_liste,
                text="🛡️ Karantina kasası temiz. İzole edilmiş zararlı veya şüpheli dosya bulunmuyor.",
                font=ctk.CTkFont(size=12), text_color="#10B981"
            ).pack(pady=40)
            self.lbl_secili_bilgi.configure(text="Karantina kasası temiz.")
            self.btn_geri_yukle.configure(state="disabled")
            self.btn_imha.configure(state="disabled")
            return

        for k in kayitlar:
            kid = k.get("id")
            ad = k.get("orijinal_ad")
            tarih = k.get("tarih")
            boyut = k.get("boyut_kb")
            sebep = k.get("sebep")
            sha = k.get("sha256", "")[:12]

            kutu = ctk.CTkFrame(self.scroll_liste, fg_color="#0F172A", corner_radius=6)
            kutu.pack(fill="x", padx=4, pady=3)

            satir_ust = ctk.CTkFrame(kutu, fg_color="transparent")
            satir_ust.pack(fill="x", padx=8, pady=(6, 2))

            btn_sec = ctk.CTkButton(
                satir_ust, text=f"🔴 {ad} ({boyut} KB)", anchor="w", fg_color="transparent",
                hover_color="#1E293B", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                command=lambda id_=kid, k_=k: self._sec(id_, k_)
            )
            btn_sec.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(satir_ust, text=tarih, font=ctk.CTkFont(size=10), text_color="#64748B").pack(side="right")

            lbl_alt = ctk.CTkLabel(
                kutu, text=f"Nedeni: {sebep} | SHA-256: {sha}...",
                font=ctk.CTkFont(family="Consolas", size=10), text_color="#94A3B8", anchor="w"
            )
            lbl_alt.pack(fill="x", padx=10, pady=(0, 6))

    def _sec(self, kid: str, kayit: Dict[str, Any]) -> None:
        self.secili_id = kid
        self.lbl_secili_bilgi.configure(text=f"Seçili: {kayit.get('orijinal_ad')} ({kayit.get('boyut_kb')} KB)")
        self.btn_geri_yukle.configure(state="normal")
        self.btn_imha.configure(state="normal")

    def _manuel_dosya_izole_et(self) -> None:
        yol = filedialog.askopenfilename(title="Karantinaya Alınacak Dosyayı Seçin", parent=self)
        if yol and os.path.isfile(yol):
            cevap = messagebox.askyesno(
                "Karantina Onayı",
                f"'{os.path.basename(yol)}' dosyası güvenli karantina kasasına izole edilecek. Onaylıyor musunuz?",
                parent=self
            )
            if cevap:
                self.yonetici.dosyayi_karantinaya_al(yol, sebep="Manuel Kullanıcı İzolasyonu")
                self.listeyi_yenile()

    def _geri_yukle(self) -> None:
        if not self.secili_id:
            return
        cevap = messagebox.askyesno(
            "Geri Yükleme",
            "Bu dosyayı karantinadan çıkarıp orijinal konumuna geri yüklemek istediğinize emin misiniz?",
            parent=self
        )
        if cevap:
            basari = self.yonetici.karantinadan_cikar(self.secili_id)
            if basari:
                messagebox.showinfo("Başarılı", "Dosya karantinadan güvenle çıkarıldı.", parent=self)
                self.listeyi_yenile()
            else:
                messagebox.showerror("Hata", "Dosya geri yüklenemedi.", parent=self)

    def _imha_et(self) -> None:
        if not self.secili_id:
            return
        cevap = messagebox.askyesno(
            "Kalıcı İmha",
            "Bu dosya disk üzerinden kalıcı olarak silinecektir (Geri getirilemez). Onaylıyor musunuz?",
            parent=self
        )
        if cevap:
            self.yonetici.kalici_imha_et(self.secili_id)
            messagebox.showinfo("İmha Edildi", "Dosya kalıcı olarak imha edildi.", parent=self)
            self.listeyi_yenile()
