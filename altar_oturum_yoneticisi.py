# -*- coding: utf-8 -*-
"""
Altar Sohbet Oturumu ve Kalıcılık Yöneticisi (altar_oturum_yoneticisi.py)

Kullanıcının yaptığı tüm konuşmaları, AI yanıtlarını ve kod çözümlerini
oturumlara (Sessions) ayırarak güvenli JSON formatında kalıcı olarak saklar.
Kullanıcı istediği zaman:
  1) Yeni sohbet başlatabilir,
  2) Geçmiş sohbetleri listeleyip seçerek ekrana geri yükleyebilir,
  3) Oturum başlıklarını düzenleyebilir veya silebilir.
Hiçbir harici sunucuya veri göndermez; tamamen yerel diskte çalışır (%100 güvenli).
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from tkinter import messagebox
import customtkinter as ctk


class AltarOturumYoneticisi:
    """Yerel disk üzerinde sohbet oturumlarını yöneten kalıcılık katmanı."""

    def __init__(self, ana_dizin: Optional[str] = None) -> None:
        if not ana_dizin:
            ana_dizin = os.path.dirname(os.path.abspath(__file__))
        self.depo_dizini = os.path.join(ana_dizin, ".altar_hafiza", "sohbet_oturumlari")
        os.makedirs(self.depo_dizini, exist_ok=True)
        self.indeks_dosyasi = os.path.join(self.depo_dizini, "oturumlar_indeks.json")
        self._indeks_hazirla()

    def _indeks_hazirla(self) -> None:
        if not os.path.isfile(self.indeks_dosyasi):
            ilk_indeks = {"aktif_oturum_id": "", "oturumlar": []}
            self._indeks_kaydet(ilk_indeks)

    def _indeks_oku(self) -> Dict[str, Any]:
        try:
            with open(self.indeks_dosyasi, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"aktif_oturum_id": "", "oturumlar": []}

    def _guvenli_oturum_yolu(self, oturum_id: str) -> Optional[str]:
        """Dizin geçişi (Path Traversal / CWE-22) saldırılarını önleyerek güvenli JSON yolunu doğrular."""
        if not oturum_id or not re.match(r"^[A-Za-z0-9_\-]+$", oturum_id):
            return None
        guvenli_ad = f"{os.path.basename(oturum_id)}.json"
        tam_yol = os.path.abspath(os.path.join(self.depo_dizini, guvenli_ad))
        depo_kok = os.path.abspath(self.depo_dizini)
        if not tam_yol.startswith(depo_kok):
            return None
        return tam_yol

    def _indeks_kaydet(self, veri: Dict[str, Any]) -> None:
        try:
            tmp_indeks = self.indeks_dosyasi + f".{uuid.uuid4().hex[:4]}.tmp"
            with open(tmp_indeks, "w", encoding="utf-8") as f:
                json.dump(veri, f, ensure_ascii=False, indent=2)
            os.replace(tmp_indeks, self.indeks_dosyasi)
        except Exception:
            pass

    def oturumlari_listele(self) -> List[Dict[str, Any]]:
        indeks = self._indeks_oku()
        oturumlar = indeks.get("oturumlar", [])
        # En yeniden en eskiye sırala
        return sorted(oturumlar, key=lambda x: x.get("son_guncelleme", ""), reverse=True)

    def aktif_oturum_id_getir(self) -> str:
        indeks = self._indeks_oku()
        return indeks.get("aktif_oturum_id", "")

    def yeni_oturum_olustur(self, baslik: str = "Yeni Sohbet") -> Dict[str, Any]:
        oturum_id = f"sess_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        zaman_damgasi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        yeni_kayit = {
            "id": oturum_id,
            "baslik": baslik,
            "olusturma_tarihi": zaman_damgasi,
            "son_guncelleme": zaman_damgasi,
            "mesaj_sayisi": 0,
        }

        # Oturum dosyasını oluştur
        dosya_yolu = os.path.join(self.depo_dizini, f"{oturum_id}.json")
        try:
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                json.dump({"meta": yeni_kayit, "mesajlar": []}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        # İndekse ekle
        indeks = self._indeks_oku()
        indeks.setdefault("oturumlar", []).insert(0, yeni_kayit)
        indeks["aktif_oturum_id"] = oturum_id
        self._indeks_kaydet(indeks)

        return yeni_kayit

    def oturum_yukle(self, oturum_id: str) -> Optional[Dict[str, Any]]:
        dosya_yolu = self._guvenli_oturum_yolu(oturum_id)
        if not dosya_yolu or not os.path.isfile(dosya_yolu):
            return None
        try:
            with open(dosya_yolu, "r", encoding="utf-8") as f:
                veri = json.load(f)
            indeks = self._indeks_oku()
            indeks["aktif_oturum_id"] = oturum_id
            self._indeks_kaydet(indeks)
            return veri
        except Exception:
            return None

    def mesaji_oturuma_ekle(self, oturum_id: str, rol: str, icerik: str) -> None:
        if not oturum_id:
            return
        dosya_yolu = self._guvenli_oturum_yolu(oturum_id)
        if not dosya_yolu or not os.path.isfile(dosya_yolu):
            self.yeni_oturum_olustur()
            dosya_yolu = self._guvenli_oturum_yolu(oturum_id)
            if not dosya_yolu or not os.path.isfile(dosya_yolu):
                return

        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yeni_mesaj = {"role": rol, "content": icerik, "timestamp": zaman}

        try:
            with open(dosya_yolu, "r+", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {"meta": {}, "mesajlar": []}

                mesajlar = data.setdefault("mesajlar", [])
                mesajlar.append(yeni_mesaj)

                # Başlık otomatik üretimi (ilk kullanıcı mesajından)
                meta = data.setdefault("meta", {})
                if meta.get("baslik") in ("Yeni Sohbet", "") and rol == "user":
                    ilk_satir = icerik.strip().split("\n")[0][:45]
                    meta["baslik"] = ilk_satir if ilk_satir else "Sohbet"

                meta["son_guncelleme"] = zaman
                meta["mesaj_sayisi"] = len(mesajlar)

                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.truncate()

            # İndeksi güncelle
            indeks = self._indeks_oku()
            for ot in indeks.get("oturumlar", []):
                if ot.get("id") == oturum_id:
                    ot["baslik"] = meta.get("baslik", ot.get("baslik"))
                    ot["son_guncelleme"] = zaman
                    ot["mesaj_sayisi"] = len(mesajlar)
                    break
            self._indeks_kaydet(indeks)
        except Exception:
            pass

    def oturum_baslik_guncelle(self, oturum_id: str, yeni_baslik: str) -> bool:
        yeni_baslik = yeni_baslik.strip()
        if not yeni_baslik:
            return False
        dosya_yolu = self._guvenli_oturum_yolu(oturum_id)
        if dosya_yolu and os.path.isfile(dosya_yolu):
            try:
                with open(dosya_yolu, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data.setdefault("meta", {})["baslik"] = yeni_baslik
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.truncate()
            except Exception:
                pass

        indeks = self._indeks_oku()
        for ot in indeks.get("oturumlar", []):
            if ot.get("id") == oturum_id:
                ot["baslik"] = yeni_baslik
                break
        self._indeks_kaydet(indeks)
        return True

    def oturum_sil(self, oturum_id: str) -> bool:
        dosya_yolu = self._guvenli_oturum_yolu(oturum_id)
        if dosya_yolu and os.path.isfile(dosya_yolu):
            try:
                os.remove(dosya_yolu)
            except Exception:
                pass

        indeks = self._indeks_oku()
        indeks["oturumlar"] = [ot for ot in indeks.get("oturumlar", []) if ot.get("id") != oturum_id]
        if indeks.get("aktif_oturum_id") == oturum_id:
            indeks["aktif_oturum_id"] = indeks["oturumlar"][0]["id"] if indeks["oturumlar"] else ""
        self._indeks_kaydet(indeks)
        return True


class AltarSohbetOturumlariModal(ctk.CTkToplevel):
    """Kullanıcının geçmiş sohbet oturumlarını listeleyen ve geri yükleyen görsel modal."""

    def __init__(self, master: object, oturum_yoneticisi: Optional[AltarOturumYoneticisi] = None, secim_callback: Any = None, on_oturum_sec: Any = None, **kwargs) -> None:
        super().__init__(master)
        self.yonetici = oturum_yoneticisi or AltarOturumYoneticisi()
        self.secim_callback = secim_callback or on_oturum_sec
        self.title("📂 Altar Sohbet Oturumları ve Geçmiş")
        self.geometry("740x520")
        self.minsize(620, 420)
        self.configure(fg_color="#0B0F19")

        self.secili_oturum_id: Optional[str] = None
        self._arayuz_kur()
        self.listeyi_yenile()

        self.transient(master)
        self.grab_set()

    def _arayuz_kur(self) -> None:
        ust = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        ust.pack(side="top", fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            ust, text="💬 Sohbet Oturumları ve Geçmiş Kayıtlar",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#A78BFA"
        ).pack(side="left", padx=10, pady=8)

        ctk.CTkButton(
            ust, text="➕ Yeni Sohbet Başlat", width=160, height=28,
            fg_color="#047857", hover_color="#059669", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._yeni_sohbet_baslat
        ).pack(side="right", padx=10, pady=8)

        # Gövde: Sol Liste | Sağ Detay
        govde = ctk.CTkFrame(self, fg_color="transparent")
        govde.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 10))
        govde.grid_columnconfigure(0, weight=5)
        govde.grid_columnconfigure(1, weight=5)
        govde.grid_rowconfigure(0, weight=1)

        sol_kutu = ctk.CTkFrame(govde, fg_color="#111827", corner_radius=8)
        sol_kutu.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.scroll_liste = ctk.CTkScrollableFrame(sol_kutu, fg_color="#070B14", corner_radius=6)
        self.scroll_liste.pack(fill="both", expand=True, padx=8, pady=8)

        sag_kutu = ctk.CTkFrame(govde, fg_color="#111827", corner_radius=8)
        sag_kutu.grid(row=0, column=1, sticky="nsew")

        sag_ust = ctk.CTkFrame(sag_kutu, fg_color="transparent")
        sag_ust.pack(fill="x", padx=8, pady=6)

        self.lbl_detay_baslik = ctk.CTkLabel(
            sag_ust, text="Seçili Oturum: [Yok]", font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38BDF8", anchor="w"
        )
        self.lbl_detay_baslik.pack(side="left", fill="x", expand=True)

        self.txt_onizleme = ctk.CTkTextbox(
            sag_kutu, fg_color="#070B14", font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#CBD5E1", wrap="word"
        )
        self.txt_onizleme.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Alt Buton Barı
        alt_bar = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8, height=44)
        alt_bar.pack(side="bottom", fill="x", padx=12, pady=(0, 10))

        self.btn_yukle = ctk.CTkButton(
            alt_bar, text="📂 Bu Oturumu Aktif Et ve Yükle", width=220, height=30,
            fg_color="#1E3A8A", hover_color="#2563EB", font=ctk.CTkFont(size=12, weight="bold"),
            state="disabled", command=self._seciliyi_yukle
        )
        self.btn_yukle.pack(side="left", padx=10, pady=6)

        self.btn_adlandir = ctk.CTkButton(
            alt_bar, text="✏️ Başlığı Düzenle", width=140, height=30,
            fg_color="#374151", hover_color="#4B5563", font=ctk.CTkFont(size=11, weight="bold"),
            state="disabled", command=self._baslik_duzenle
        )
        self.btn_adlandir.pack(side="left", padx=4, pady=6)

        self.btn_sil = ctk.CTkButton(
            alt_bar, text="🗑️ Oturumu Sil", width=115, height=30,
            fg_color="#B91C1C", hover_color="#DC2626", font=ctk.CTkFont(size=11, weight="bold"),
            state="disabled", command=self._oturumu_sil
        )
        self.btn_sil.pack(side="right", padx=10, pady=6)

    def listeyi_yenile(self) -> None:
        for w in self.scroll_liste.winfo_children():
            w.destroy()

        oturumlar = self.yonetici.oturumlari_listele()
        aktif_id = self.yonetici.aktif_oturum_id_getir()

        if not oturumlar:
            ctk.CTkLabel(
                self.scroll_liste, text="Henüz kayıtlı oturum yok.", font=ctk.CTkFont(size=12), text_color="#64748B"
            ).pack(pady=30)
            return

        for ot in oturumlar:
            oid = ot.get("id")
            baslik = ot.get("baslik", "Adsız")
            tarih = ot.get("son_guncelleme", "")[:16]
            sayi = ot.get("mesaj_sayisi", 0)
            aktif_mi = (oid == aktif_id)

            kutu = ctk.CTkFrame(self.scroll_liste, fg_color="#1E293B" if aktif_mi else "#0F172A", corner_radius=6)
            kutu.pack(fill="x", padx=4, pady=3)

            btn = ctk.CTkButton(
                kutu,
                text=f"{'🟢 ' if aktif_mi else '💬 '}{baslik}\n   ({sayi} mesaj - {tarih})",
                anchor="w",
                fg_color="transparent",
                hover_color="#334155" if aktif_mi else "#1E293B",
                font=ctk.CTkFont(size=11, weight="bold" if aktif_mi else "normal"),
                command=lambda i=oid: self._oturum_sec(i)
            )
            btn.pack(fill="both", expand=True, padx=4, pady=4)

    def _oturum_sec(self, oturum_id: str) -> None:
        self.secili_oturum_id = oturum_id
        veri = self.yonetici.oturum_yukle(oturum_id)
        if not veri:
            return

        meta = veri.get("meta", {})
        mesajlar = veri.get("mesajlar", [])
        self.lbl_detay_baslik.configure(text=f"Seçili: {meta.get('baslik')} ({len(mesajlar)} Mesaj)")
        self.btn_yukle.configure(state="normal")
        self.btn_adlandir.configure(state="normal")
        self.btn_sil.configure(state="normal")

        self.txt_onizleme.delete("1.0", "end")
        if not mesajlar:
            self.txt_onizleme.insert("end", "[Bu oturumda henüz mesaj bulunmuyor.]")
        else:
            for m in mesajlar[-25:]:
                rol = "Sen" if m.get("role") == "user" else "Altar Asistan"
                self.txt_onizleme.insert("end", f"[{rol} - {m.get('timestamp', '')[:16]}]:\n{m.get('content', '')[:400]}\n\n" + "-"*40 + "\n\n")

    def _yeni_sohbet_baslat(self) -> None:
        yeni = self.yonetici.yeni_oturum_olustur()
        if callable(self.secim_callback):
            self.secim_callback(yeni["id"], temizle=True)
        self.destroy()

    def _seciliyi_yukle(self) -> None:
        if self.secili_oturum_id and callable(self.secim_callback):
            self.secim_callback(self.secili_oturum_id, temizle=False)
            self.destroy()

    def _baslik_duzenle(self) -> None:
        if not self.secili_oturum_id:
            return
        diyalog = ctk.CTkInputDialog(text="Yeni Oturum Başlığı:", title="Oturumu Yeniden Adlandır")
        yeni_ad = diyalog.get_input()
        if yeni_ad and yeni_ad.strip():
            self.yonetici.oturum_baslik_guncelle(self.secili_oturum_id, yeni_ad)
            self.listeyi_yenile()
            self._oturum_sec(self.secili_oturum_id)

    def _oturumu_sil(self) -> None:
        if not self.secili_oturum_id:
            return
        from tkinter import messagebox
        cevap = messagebox.askyesno("Oturumu Sil", "Bu sohbet oturumu ve tüm geçmişi kalıcı olarak silinecektir. Onaylıyor musunuz?", parent=self)
        if cevap:
            self.yonetici.oturum_sil(self.secili_oturum_id)
            self.secili_oturum_id = None
            self.txt_onizleme.delete("1.0", "end")
            self.lbl_detay_baslik.configure(text="Seçili Oturum: [Yok]")
            self.btn_yukle.configure(state="disabled")
            self.btn_adlandir.configure(state="disabled")
            self.btn_sil.configure(state="disabled")
            self.listeyi_yenile()

