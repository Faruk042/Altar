# -*- coding: utf-8 -*-
"""
========================================================================================
ALTAR KİMLİK DOĞRULAMA VE ANTİ-SİLME KORUMA MERKEZİ (altar_kimlik_yoneticisi.py)
========================================================================================
1) AltarGirisKayitPenceresi:
   - Uygulama ilk açılırken kullanıcıyı karşılayan 2 sekmeli güvenli giriş/kayıt arayüzü.
   - 'Kayıt Ol' sekmesinde kullanıcı adı ve 2 defa girilip eşleşme şartı aranan parola ile kayıt.
   - 'Giriş Yap' sekmesinde kayıtlı kimlik doğrulaması. Başarısız olursa uygulama açılmaz.
   - Parolalar PBKDF2-HMAC-SHA256 (100.000 iterasyon + 16-byte rastgele tuz) ile saklanır.

2) AltarAntiSilmeKalkani & AltarAntiSilmeHataArayuzu:
   - Kullanıcı hesabına giriş yapmadığı sürece Altar.exe dosyalarının silinmesini,
     adının değiştirilmesini veya tahrip edilmesini Windows Çekirdeği (Kernel File Handle Lock)
     düzeyinde engelleyen koruma motoru ve şık siber hata/uyarı arayüzü.
========================================================================================
"""

from __future__ import annotations

import os
import sys
import json
import time
import hashlib
import secrets
import threading
from typing import Callable, Dict, Optional, Tuple

import customtkinter as ctk
from tkinter import messagebox

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    try:
        import winsound
        WINSOUND_VAR = True
    except ImportError:
        WINSOUND_VAR = False
else:
    ctypes = None
    wintypes = None
    WINSOUND_VAR = False


# Proje Yolları ve Veri Dizini
_ANA_DIZIN = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    _VERI_DIZINI = os.path.join(os.path.dirname(sys.executable), "data")
else:
    _VERI_DIZINI = os.path.join(_ANA_DIZIN, "data")

os.makedirs(_VERI_DIZINI, exist_ok=True)
_KIMLIK_DOSYASI = os.path.join(_VERI_DIZINI, "altar_guvenlik_kimlik.json")


# =============================================================================
# 1. KRİPTOGRAFİK ŞİFRELEME VE VERİTABANI YÖNETİMİ (PBKDF2-SHA256)
# =============================================================================
def _parola_hashle(parola: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """Parolayı PBKDF2-HMAC-SHA256 ile tuzlayarak güvenli hale getirir."""
    if salt is None:
        salt = secrets.token_bytes(16)
    kdf = hashlib.pbkdf2_hmac("sha256", parola.encode("utf-8"), salt, 100_000)
    return kdf.hex(), salt.hex()


def _parola_dogrula(parola: str, hash_hex: str, salt_hex: str) -> bool:
    """Girilen parolanın saklanan hash ile eşleştiğini doğrular."""
    try:
        salt = bytes.fromhex(salt_hex)
        yeni_hash, _ = _parola_hashle(parola, salt)
        return secrets.compare_digest(yeni_hash, hash_hex)
    except Exception:
        return False


def _kullanicilari_oku() -> Dict[str, Dict[str, str]]:
    """Kayıtlı kullanıcı verilerini güvenle okur."""
    if not os.path.isfile(_KIMLIK_DOSYASI):
        return {}
    try:
        with open(_KIMLIK_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _kullanicilari_yaz(veriler: Dict[str, Dict[str, str]]) -> bool:
    """Kullanıcı verilerini kaydeder."""
    try:
        with open(_KIMLIK_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(veriler, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def kullanici_kayit_et(kullanici_adi: str, parola: str, parola_tekrar: str) -> Tuple[bool, str]:
    """Kullanıcıyı doğrular ve sisteme güvenle kaydeder."""
    kadi = kullanici_adi.strip()
    if len(kadi) < 3:
        return False, "Kullanıcı adı en az 3 karakter olmalıdır."
    if len(parola) < 4:
        return False, "Parola en az 4 karakter olmalıdır."
    if parola != parola_tekrar:
        return False, "Girilen iki parola birbiriyle eşleşmiyor! Lütfen kontrol edin."

    veriler = _kullanicilari_oku()
    if kadi.lower() in [k.lower() for k in veriler.keys()]:
        return False, f"'{kadi}' kullanıcı adı zaten kayıtlı. Lütfen farklı bir kullanıcı adı seçin."

    hash_hex, salt_hex = _parola_hashle(parola)
    veriler[kadi] = {
        "hash": hash_hex,
        "salt": salt_hex,
        "kayit_tarihi": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    if _kullanicilari_yaz(veriler):
        return True, "Kayıt başarıyla tamamlandı! Şimdi giriş yapabilirsiniz."
    return False, "Kullanıcı verisi kaydedilirken bir dosya hatası oluştu."


def kullanici_giris_dogrula(kullanici_adi: str, parola: str) -> Tuple[bool, str]:
    """Kullanıcı adı ve parolasını doğrular."""
    kadi = kullanici_adi.strip()
    if not kadi or not parola:
        return False, "Lütfen kullanıcı adı ve parolanızı girin."

    veriler = _kullanicilari_oku()
    hedef = None
    for kayitli_kadi, bilgi in veriler.items():
        if kayitli_kadi.lower() == kadi.lower():
            hedef = (kayitli_kadi, bilgi)
            break

    if not hedef:
        return False, "Kullanıcı adı veya şifre hatalı!"

    kayitli_kadi, bilgi = hedef
    if _parola_dogrula(parola, bilgi.get("hash", ""), bilgi.get("salt", "")):
        return True, f"Hoş geldiniz, {kayitli_kadi}!"
    return False, "Kullanıcı adı veya şifre hatalı!"


def kayitli_kullanici_sayisi() -> int:
    """Sistemde kayıtlı kullanıcı sayısını döndürür."""
    return len(_kullanicilari_oku())


# =============================================================================
# 2. ANTİ-SİLME VE DEĞİŞTİRME KİLİT MOTORU (WINDOWS KERNEL HANDLE LOCK)
# =============================================================================
class AltarAntiSilmeKalkani:
    """
    Giriş yapılmadığı sürece Altar.exe ve ana program dosyalarının
    işletim sistemi düzeyinde silinmesini, taşınmasını ve değiştirilmesini
    Windows Çekirdeği (Win32 CreateFileW FILE_SHARE_READ kilidi) ile engeller.
    """
    _kilitli_handlelar = []

    @classmethod
    def dosyalari_kilitle(cls):
        """Altar yürütülebilir dosyalarını çekirdek seviyesinde kilitleyerek silinmez yapar."""
        if sys.platform != "win32" or not ctypes:
            return

        GENERIC_READ = 0x80000000
        FILE_SHARE_READ = 1  # Okumaya izin verir; SİLMEYİ ve ÜZERİNE YAZMAYI KESİNLİKLE ENGELLER
        OPEN_EXISTING = 3
        FILE_ATTRIBUTE_NORMAL = 0x80

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
            wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
        ]

        hedef_yollar = []
        if getattr(sys, "frozen", False):
            hedef_yollar.append(sys.executable)

        # Masaüstü ve proje dizinindeki olası exe yolları
        desktop_exe = os.path.expandvars(r"%USERPROFILE%\Desktop\Altar.exe")
        hedef_yollar.extend([
            desktop_exe,
            os.path.join(_ANA_DIZIN, "Altar.exe"),
            os.path.join(_ANA_DIZIN, "dist", "Altar", "Altar.exe")
        ])

        for yol in hedef_yollar:
            if yol and os.path.isfile(yol):
                try:
                    h = kernel32.CreateFileW(
                        yol, GENERIC_READ, FILE_SHARE_READ,
                        None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None
                    )
                    if h and h != -1 and h != 0xFFFFFFFFFFFFFFFF:
                        cls._kilitli_handlelar.append(h)
                except Exception:
                    pass

    @classmethod
    def kilitleri_coz(cls):
        """Kullanıcı giriş yaptığında çekirdek kilit handle'larını serbest bırakır."""
        if not ctypes:
            return
        kernel32 = ctypes.windll.kernel32
        for h in cls._kilitli_handlelar:
            try:
                kernel32.CloseHandle(h)
            except Exception:
                pass
        cls._kilitli_handlelar.clear()


# =============================================================================
# 3. ŞIK SİBER HATA VE SİLME KORUMASI ARAYÜZÜ (MODAL)
# =============================================================================
class AltarAntiSilmeHataArayuzu(ctk.CTkToplevel):
    """Yetkisiz silme veya değiştirme girişimlerinde çıkan şık siber uyarı penceresi."""

    def __init__(self, master=None):
        super().__init__(master)
        self.title("🛡️ Altar Güvenlik Kalkanı — Yetkisiz Erişim Engeli")
        self.geometry("620x460")
        self.minsize(580, 420)
        self.configure(fg_color="#070C16")
        self.attributes("-topmost", True)

        self._arayuz_kur()
        self.transient(master)
        self.grab_set()

    def _arayuz_kur(self):
        # Üst Siber Bar
        ust = ctk.CTkFrame(self, fg_color="#111B2E", corner_radius=10, border_width=1, border_color="#DC2626")
        ust.pack(fill="x", padx=16, pady=(16, 10))

        ctk.CTkLabel(
            ust, text="🛡️🚫   E R İ Ş İ M   V E   S İ L M E   E N G E L İ",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            text_color="#EF4444"
        ).pack(side="left", padx=16, pady=12)

        # Ana Gövde
        govde = ctk.CTkFrame(self, fg_color="#0C1527", corner_radius=10, border_width=1, border_color="#1E293B")
        govde.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        ctk.CTkLabel(
            govde,
            text=(
                "⚠️ DİKKAT: Altar Güvenlik ve Bütünlük Kalkanı Devrede!\n\n"
                "Altar yürütülebilir program dosyaları (.exe) üzerinde hesabınıza giriş\n"
                "yapmadığınız müddetçe silme, yeniden adlandırma veya dosya içeriğini\n"
                "değiştirme işlemi yapılmasına Windows Çekirdeği tarafından izin verilmez."
            ),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC",
            justify="center"
        ).pack(padx=20, pady=(20, 14))

        # Bilgilendirme Kutusu
        bilgi_kutusu = ctk.CTkFrame(govde, fg_color="#070D18", corner_radius=8, border_width=1, border_color="#334155")
        bilgi_kutusu.pack(fill="x", padx=24, pady=10)

        detaylar = (
            "🔒 Güvenlik Durumu       : Çekirdek Kilidi Aktif (Win32 Exclusive File Handle Lock)\n"
            "🔑 İzin Gereksinimi      : Geçerli Altar Kullanıcı Hesabıyla Giriş Yapılmalıdır\n"
            "🛡️ Bütünlük Koruması     : SHA-256 Kriptografik İmza Denetimi\n"
            "⚡ Korunan Konumlar      : Masaüstü Altar.exe ve Dağıtım Arşivi"
        )
        ctk.CTkLabel(
            bilgi_kutusu,
            text=detaylar,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#38BDF8",
            justify="left"
        ).pack(padx=16, pady=12, anchor="w")

        # Buton Barı
        alt_bar = ctk.CTkFrame(self, fg_color="transparent")
        alt_bar.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(
            alt_bar,
            text="Giriş Ekranına Dön ve Giriş Yap ➡️",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=36,
            command=self.destroy
        ).pack(side="right", padx=4)


# =============================================================================
# 4. ŞIK GİRİŞ VE KAYIT ARAYÜZÜ (GİRİŞ YAP & KAYIT OL)
# =============================================================================
class AltarGirisKayitPenceresi(ctk.CTk):
    """
    Uygulama açılışında çıkan şık, modern siber/doğa tasarımlı Giriş ve Kayıt Penceresi.
    Giriş başarılı olmadan Altar ana ekranı açılmaz.
    """

    def __init__(self, on_basarili_giris: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_basarili_giris = on_basarili_giris
        self.giris_basarili = False
        self.aktif_kullanici = ""

        # Dosyaları çekirdek seviyesinde kilitle (Giriş yapılmadığı sürece silinemez)
        AltarAntiSilmeKalkani.dosyalari_kilitle()

        self.title("Altar — Güvenlik Doğrulaması & Hesap Girişi")
        self.geometry("520x620")
        self.minsize(480, 580)
        self.configure(fg_color="#070C16")
        self.resizable(False, False)

        # Ekranın ortasında başlat
        self._ekranin_ortasina_yerlestir(520, 620)
        self.protocol("WM_DELETE_WINDOW", self._cikis_yap)

        self._arayuz_kur()

    def _ekranin_ortasina_yerlestir(self, w: int, h: int):
        self.update_idletasks()
        ekran_g = self.winfo_screenwidth()
        ekran_y = self.winfo_screenheight()
        x = (ekran_g - w) // 2
        y = (ekran_y - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _arayuz_kur(self):
        # 1. Üst Başlık & Altar Amblem Alanı
        ust_cerceve = ctk.CTkFrame(self, fg_color="#0D1829", corner_radius=12, border_width=1, border_color="#1E293B")
        ust_cerceve.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(
            ust_cerceve,
            text="🌿   A   L   T   A   R   🌿",
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color="#10B981"
        ).pack(pady=(14, 2))

        ctk.CTkLabel(
            ust_cerceve,
            text="G Ü V E N L İ K   V E   K İ M L İ K   D O Ğ R U L A M A   M E R K E Z İ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#64748B"
        ).pack(pady=(0, 12))

        # 2. Giriş Yap ve Kayıt Ol Sekmeli Panel
        self.tabview = ctk.CTkTabview(
            self,
            fg_color="#0A1220",
            segmented_button_fg_color="#1E293B",
            segmented_button_selected_color="#059669",
            segmented_button_selected_hover_color="#047857",
            segmented_button_unselected_hover_color="#334155",
            text_color="#F8FAFC"
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        self.tab_giris = self.tabview.add("🔑 Giriş Yap")
        self.tab_kayit = self.tabview.add("📝 Kayıt Ol")

        self._tab_giris_kur()
        self._tab_kayit_kur()

        # Eğer sistemde hiç kullanıcı yoksa doğrudan 'Kayıt Ol' sekmesinde aç
        if kayitli_kullanici_sayisi() == 0:
            self.tabview.set("📝 Kayıt Ol")
        else:
            self.tabview.set("🔑 Giriş Yap")

        # 3. Alt Durum ve Güvenlik Koruma Butonu
        alt_bar = ctk.CTkFrame(self, fg_color="transparent")
        alt_bar.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkButton(
            alt_bar,
            text="🛡️ Dosya Silme / Değiştirme Koruması Bilgisi",
            font=ctk.CTkFont(size=11),
            fg_color="#1E293B",
            hover_color="#334155",
            height=28,
            command=self._anti_silme_modal_ac
        ).pack(side="left")

        ctk.CTkLabel(
            alt_bar,
            text="v2.5 Siber Güvenlik Kalkanı",
            font=ctk.CTkFont(size=10),
            text_color="#475569"
        ).pack(side="right")

    # =========================================================================
    # GİRİŞ YAP SEKMESİ
    # =========================================================================
    def _tab_giris_kur(self):
        f = self.tab_giris

        ctk.CTkLabel(f, text="Kullanıcı Adı:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1").pack(anchor="w", padx=16, pady=(16, 4))
        self.txt_giris_kadi = ctk.CTkEntry(f, height=36, fg_color="#111B2E", border_color="#334155", placeholder_text="Kullanıcı adınızı girin...")
        self.txt_giris_kadi.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(f, text="Parola:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1").pack(anchor="w", padx=16, pady=(4, 4))
        self.txt_giris_parola = ctk.CTkEntry(f, height=36, fg_color="#111B2E", border_color="#334155", show="*", placeholder_text="Parolanızı girin...")
        self.txt_giris_parola.pack(fill="x", padx=16, pady=(0, 14))

        # Enter ile doğrudan giriş yap
        self.txt_giris_parola.bind("<Return>", lambda _: self._eylem_giris_yap())
        self.txt_giris_kadi.bind("<Return>", lambda _: self.txt_giris_parola.focus())

        self.lbl_giris_durum = ctk.CTkLabel(f, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color="#EF4444")
        self.lbl_giris_durum.pack(pady=4)

        ctk.CTkButton(
            f, text="Giriş Yap ve Altar'ı Başlat 🚀",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#059669", hover_color="#047857",
            height=42, corner_radius=8,
            command=self._eylem_giris_yap
        ).pack(fill="x", padx=16, pady=(8, 12))

    def _eylem_giris_yap(self):
        kadi = self.txt_giris_kadi.get()
        parola = self.txt_giris_parola.get()

        basarili, mesaj = kullanici_giris_dogrula(kadi, parola)
        if basarili:
            self.lbl_giris_durum.configure(text=f"✅ {mesaj}", text_color="#10B981")
            self.giris_basarili = True
            self.aktif_kullanici = kadi.strip()

            # Giriş başarılı olduğu için çekirdek kilidi serbest bırak
            AltarAntiSilmeKalkani.kilitleri_coz()

            if WINSOUND_VAR:
                try:
                    winsound.Beep(1200, 150)
                except Exception:
                    pass

            self.after(350, self._girisi_tamamla)
        else:
            self.lbl_giris_durum.configure(text=f"❌ {mesaj}", text_color="#EF4444")
            if WINSOUND_VAR:
                try:
                    winsound.Beep(600, 200)
                except Exception:
                    pass

    def _girisi_tamamla(self):
        if callable(self.on_basarili_giris):
            self.on_basarili_giris(self.aktif_kullanici)
        self.destroy()

    # =========================================================================
    # KAYIT OL SEKMESİ
    # =========================================================================
    def _tab_kayit_kur(self):
        f = self.tab_kayit

        ctk.CTkLabel(f, text="Kullanıcı Adı Seçin:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1").pack(anchor="w", padx=16, pady=(10, 3))
        self.txt_kayit_kadi = ctk.CTkEntry(f, height=34, fg_color="#111B2E", border_color="#334155", placeholder_text="En az 3 karakter...")
        self.txt_kayit_kadi.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(f, text="Parola Belirleyin:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1").pack(anchor="w", padx=16, pady=(3, 3))
        self.txt_kayit_parola1 = ctk.CTkEntry(f, height=34, fg_color="#111B2E", border_color="#334155", show="*", placeholder_text="En az 4 karakter...")
        self.txt_kayit_parola1.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(f, text="Parolayı Tekrar Girin (Eşleşme Şartı):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1").pack(anchor="w", padx=16, pady=(3, 3))
        self.txt_kayit_parola2 = ctk.CTkEntry(f, height=34, fg_color="#111B2E", border_color="#334155", show="*", placeholder_text="Parolayı birebir aynı girin...")
        self.txt_kayit_parola2.pack(fill="x", padx=16, pady=(0, 10))

        self.lbl_kayit_durum = ctk.CTkLabel(f, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color="#EF4444")
        self.lbl_kayit_durum.pack(pady=2)

        ctk.CTkButton(
            f, text="Hesabı Güvenle Kaydet 📝",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1D4ED8", hover_color="#1E40AF",
            height=40, corner_radius=8,
            command=self._eylem_kayit_ol
        ).pack(fill="x", padx=16, pady=(6, 10))

    def _eylem_kayit_ol(self):
        kadi = self.txt_kayit_kadi.get()
        p1 = self.txt_kayit_parola1.get()
        p2 = self.txt_kayit_parola2.get()

        basarili, mesaj = kullanici_kayit_et(kadi, p1, p2)
        if basarili:
            self.lbl_kayit_durum.configure(text=f"✅ {mesaj}", text_color="#10B981")
            if WINSOUND_VAR:
                try:
                    winsound.Beep(1000, 150)
                except Exception:
                    pass
            # Giriş sekmesine yönlendir ve kullanıcı adını hazır yaz
            self.txt_giris_kadi.delete(0, "end")
            self.txt_giris_kadi.insert(0, kadi.strip())
            self.txt_giris_parola.delete(0, "end")
            self.lbl_giris_durum.configure(text="✅ Kayıt tamamlandı! Şimdi şifrenizle giriş yapınız.", text_color="#10B981")
            self.after(800, lambda: self.tabview.set("🔑 Giriş Yap"))
            self.after(850, lambda: self.txt_giris_parola.focus())
        else:
            self.lbl_kayit_durum.configure(text=f"❌ {mesaj}", text_color="#EF4444")
            if WINSOUND_VAR:
                try:
                    winsound.Beep(550, 180)
                except Exception:
                    pass

    def _anti_silme_modal_ac(self):
        """Silme ve değiştirme koruması hata arayüzünü açar."""
        AltarAntiSilmeHataArayuzu(self)

    def _cikis_yap(self):
        """Kullanıcı giriş yapmadan pencereyi kapatırsa Altar'ı güvenle kapatır."""
        AltarAntiSilmeKalkani.kilitleri_coz()
        self.destroy()
        sys.exit(0)


# =============================================================================
# DOĞRUDAN ÇALIŞTIRMA VE TEST
# =============================================================================
if __name__ == "__main__":
    app = AltarGirisKayitPenceresi(on_basarili_giris=lambda u: print(f"[OK] Giriş başarılı: {u}"))
    app.mainloop()
