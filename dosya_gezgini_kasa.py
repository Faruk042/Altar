import os
import sys
import base64
import hashlib
import secrets
import threading
import subprocess
from collections import deque
from datetime import datetime
from typing import Any, Callable, Optional
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None  # type: ignore[assignment, misc]

    class InvalidToken(Exception):  # type: ignore[no-redef]
        """Fernet kütüphanesi kurulu olmadığında hata yakalama için yedek sınıf."""
        pass

_ANA_DIZIN = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
_KASA_IMZA = b"ALTAR_VAULT_V2\n"
_KASA_UZANTI = ".altar_lock"
_EV_DIZINI = os.path.normcase(os.path.realpath(os.path.expanduser("~")))
_MAX_FERNET_BOYUT = 4 * 1024 * 1024 * 1024  # 4 GB güvenli bellek ve şifreleme sınırı
_MAX_HASH_BOYUT = 2 * 1024 * 1024 * 1024    # 2 GB üzeri dosyalarda önizleme SHA-256 disk/CPU blokaj sınırı

# Bu dizinlerin kendisi, alt dizinleri ve bunları içeren üst dizinler kilitlenemez.
_KRITIK_KOKLER = tuple(
    os.path.normcase(os.path.realpath(os.path.abspath(yol)))
    for yol in (
        _ANA_DIZIN,
        os.environ.get("WINDIR", r"C:\Windows" if os.name == "nt" else "/etc"),
        os.environ.get("PROGRAMFILES", r"C:\Program Files" if os.name == "nt" else "/usr"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)" if os.name == "nt" else "/bin"),
    )
    if yol and os.path.exists(yol)
)


def _boyut_formatla(bayt_degeri: int) -> str:
    """Bayt cinsinden verilen boyutu insan tarafından okunabilir birime çevirir."""
    if bayt_degeri < 1024:
        return f"{bayt_degeri} B"
    if bayt_degeri < 1024 ** 2:
        return f"{bayt_degeri / 1024:.1f} KB"
    if bayt_degeri < 1024 ** 3:
        return f"{bayt_degeri / (1024 ** 2):.2f} MB"
    return f"{bayt_degeri / (1024 ** 3):.2f} GB"


def _paroladan_fernet_anahtari_uret(parola: str, salt: bytes) -> bytes:
    """Kullanıcı şifresinden PBKDF2-HMAC-SHA256 (200.000 iterasyon) ile 32-bayt Fernet anahtarı üretir."""
    ham_anahtar = hashlib.pbkdf2_hmac(
        "sha256",
        parola.encode("utf-8"),
        salt,
        200_000,
        dklen=32
    )
    return base64.urlsafe_b64encode(ham_anahtar)


def _yol_ayni_veya_altinda(yol: str, kok: str) -> bool:
    """Yolun kok ile aynı ya da kok dizininin altında olup olmadığını kontrol eder."""
    try:
        return os.path.normcase(os.path.commonpath([yol, kok])) == os.path.normcase(kok)
    except (ValueError, OSError):
        return False


def _bag_veya_junction_mi(yol: str) -> bool:
    """Yolun sembolik bağ veya Windows NTFS Junction (Reparse Point) olup olmadığını denetler."""
    try:
        if os.path.islink(yol):
            return True
        if hasattr(os.path, "isjunction") and os.path.isjunction(yol):  # type: ignore[attr-defined]
            return True
    except OSError:
        return True
    return False


def _hedef_yol_guvenli_mi(hedef_yol: str) -> tuple[bool, str]:
    """Hedef dizin veya dosyanın kilitlenmesinin güvenli olup olmadığını denetler."""
    if _bag_veya_junction_mi(hedef_yol):
        return False, "Sembolik bağ veya NTFS Junction hedefleri güvenlik nedeniyle işlenemez."

    gercek_yol = os.path.realpath(os.path.abspath(os.path.expanduser(hedef_yol)))
    hedef = os.path.normcase(gercek_yol)

    surucu, kalan = os.path.splitdrive(hedef)
    surucu_koku = os.path.normcase(surucu + os.sep) if surucu else os.sep
    if (
        hedef == os.path.normcase(surucu_koku)
        or os.path.dirname(hedef) == hedef
        or (surucu.startswith("\\\\") and not kalan.strip("\\/"))
    ):
        return False, "Sürücü veya kök dizin doğrudan şifrelenemez."

    hedef_dizin_mi = os.path.isdir(gercek_yol)
    for korunan in _KRITIK_KOKLER:
        if _yol_ayni_veya_altinda(hedef, korunan) or (hedef_dizin_mi and _yol_ayni_veya_altinda(korunan, hedef)):
            return False, f"Kritik sistem veya uygulama diziniyle çakışan hedef korunuyor: '{hedef_yol}'."

    if hedef == _EV_DIZINI or (hedef_dizin_mi and _yol_ayni_veya_altinda(_EV_DIZINI, hedef)):
        return False, "Kullanıcı ana ev dizininin tamamı veya onu kapsayan üst dizin kilitlenemez."

    return True, ""


class DosyaGezginiVeKasaSekmesi(ctk.CTkFrame):
    """
    Altar Dosya Gezgini & Kriptografik Kasa Sekmesi:
    Disklerde hızlı gezinme, salt-okunur dosya/hex önizleme, SHA-256 doğrulama
    ve kullanıcı şifreli (PBKDF2 + Fernet) Dizin/Dosya Kasası.
    """

    def __init__(self, parent: Any, ai_analiz_callback: Optional[Callable[[str], None]] = None) -> None:
        super().__init__(parent, fg_color="transparent")
        self.ai_analiz_callback = ai_analiz_callback

        self.aktif_dizin: str = os.path.expanduser("~/Desktop")
        if not os.path.exists(self.aktif_dizin):
            self.aktif_dizin = os.path.expanduser("~")

        self.gecmis_yigin: list[str] = []
        self.secili_tam_yol: str = ""
        self._tarama_id: int = 0
        self._onizleme_id: int = 0
        self._kasa_islem_aktif: bool = False
        self._son_satirlar_bellek: list[tuple[str, str, str, str, str, bool]] = []
        self._oge_yollari: dict[str, str] = {}  # Tkinter Treeview IID -> Tam Dosya Yolu eşlemesi

        # Thread-Safe UI ve Log Kuyrukları
        self._ui_kuyrugu: deque[Callable[[], Any]] = deque()
        self._log_kuyrugu: deque[str] = deque(maxlen=250)

        self._arayuz_olustur()
        self.after(80, self._ui_zamanlayici_dongusu)
        self.after(150, lambda: self.dizini_yukle(self.aktif_dizin, gecmise_ekle=False))

    # =========================================================================
    # MERKEZİ THREAD-SAFE UI KUYRUK DÖNGÜSÜ (ANA THREAD)
    # =========================================================================
    def _ui_gorevi_ekle(self, fonk: Callable[[], Any]) -> None:
        """Arka plan iş parçacıklarından Tkinter görevlerini güvenle ana iş parçacığına aktarır."""
        self._ui_kuyrugu.append(fonk)

    def _kasa_log_yaz(self, mesaj: str) -> None:
        """Arka plan iş parçacıklarından kasa günlüğüne mesaj bırakır."""
        saat = datetime.now().strftime("%H:%M:%S")
        self._log_kuyrugu.append(f"[{saat}] {mesaj}")

    def _ui_zamanlayici_dongusu(self) -> None:
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        islenen = 0
        while self._ui_kuyrugu and islenen < 25:
            try:
                gorev = self._ui_kuyrugu.popleft()
                gorev()
            except Exception as exc:
                self._kasa_log_yaz(f"UI görevi yürütülürken hata: {exc}")
            islenen += 1

        if self._log_kuyrugu:
            satirlar = []
            while self._log_kuyrugu:
                satirlar.append(self._log_kuyrugu.popleft())
            try:
                self.txt_kasa_log.configure(state="normal")
                self.txt_kasa_log.insert("end", "\n".join(satirlar) + "\n")
                self.txt_kasa_log.see("end")
                self.txt_kasa_log.configure(state="disabled")
            except Exception:
                return

        try:
            self.after(90, self._ui_zamanlayici_dongusu)
        except Exception:
            pass

    # =========================================================================
    # GÖRSEL ARAYÜZ KURULUMU
    # =========================================================================
    def _arayuz_olustur(self) -> None:
        # 1. ÜST GEZİNME VE SÜRÜCÜ ÇUBUĞU
        ust_bar = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1B263B")
        ust_bar.pack(side="top", fill="x", padx=6, pady=(4, 6))

        ctk.CTkLabel(
            ust_bar, text="💾 Sürücü:", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#00FFCC"
        ).pack(side="left", padx=(10, 4), pady=6)

        suruculer = self._mevcut_suruculeri_bul()
        self.surucu_var = ctk.StringVar(value=suruculer[0] if suruculer else ("C:\\" if os.name == "nt" else "/"))
        self.combo_surucu = ctk.CTkOptionMenu(
            ust_bar, variable=self.surucu_var, values=suruculer or ["/"], width=80, height=26,
            fg_color="#1f538d", command=lambda s: self.dizini_yukle(s)
        )
        self.combo_surucu.pack(side="left", padx=4, pady=6)

        ctk.CTkButton(
            ust_bar, text="⬅️ Geri", width=65, height=26, fg_color="#374151", command=self.geri_git
        ).pack(side="left", padx=2, pady=6)

        ctk.CTkButton(
            ust_bar, text="⬆️ Üst", width=65, height=26, fg_color="#374151", command=self.ust_dizine_cik
        ).pack(side="left", padx=2, pady=6)

        ctk.CTkButton(
            ust_bar, text="🖥️ Masaüstü", width=95, height=26, fg_color="#374151",
            command=lambda: self.dizini_yukle(os.path.expanduser("~/Desktop"))
        ).pack(side="left", padx=2, pady=6)

        ctk.CTkButton(
            ust_bar, text="📥 İndirilenler", width=95, height=26, fg_color="#374151",
            command=lambda: self.dizini_yukle(os.path.expanduser("~/Downloads"))
        ).pack(side="left", padx=2, pady=6)

        self.entry_yol = ctk.CTkEntry(
            ust_bar, font=ctk.CTkFont(family="Consolas", size=12), height=26,
            fg_color="#050811", border_color="#00A86B"
        )
        self.entry_yol.pack(side="left", fill="x", expand=True, padx=6, pady=6)
        self.entry_yol.bind("<Return>", lambda _: self.dizini_yukle(self.entry_yol.get().strip()))

        ctk.CTkButton(
            ust_bar, text="📂 Klasör Seç", width=95, height=26, fg_color="#4B0082", command=self.diyalogla_dizin_sec
        ).pack(side="left", padx=3, pady=6)

        ctk.CTkButton(
            ust_bar, text="🔄 Yenile", width=78, height=26, fg_color="#00A86B",
            command=lambda: self.dizini_yukle(self.aktif_dizin, gecmise_ekle=False)
        ).pack(side="right", padx=(2, 10), pady=6)

        # 2. ORTA BÖLÜNMÜŞ GÖVDE
        govde = ctk.CTkFrame(self, fg_color="transparent")
        govde.pack(side="top", fill="both", expand=True, padx=6, pady=(0, 6))
        govde.grid_columnconfigure(0, weight=12)
        govde.grid_columnconfigure(1, weight=10)
        govde.grid_rowconfigure(0, weight=1)

        # --- SOL PANEL: DOSYA VE KLASÖR TABLOSU ---
        sol_panel = ctk.CTkFrame(govde, fg_color="#0B1320", corner_radius=8, border_width=1, border_color="#1E293B")
        sol_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        filtre_bar = ctk.CTkFrame(sol_panel, fg_color="#161B22", corner_radius=6)
        filtre_bar.pack(side="top", fill="x", padx=8, pady=6)

        ctk.CTkLabel(
            filtre_bar, text="🔎 Filtrele:", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#FFD700"
        ).pack(side="left", padx=8, pady=4)

        self.entry_filtre = ctk.CTkEntry(
            filtre_bar, placeholder_text="Dosya veya klasör adına göre anlık filtrele...",
            height=24, font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.entry_filtre.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        self.entry_filtre.bind("<KeyRelease>", lambda _: self._bellekten_tabloyu_filtrele())

        self.lbl_dizin_ozet = ctk.CTkLabel(
            filtre_bar, text="0 Klasör | 0 Dosya",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#58A6FF"
        )
        self.lbl_dizin_ozet.pack(side="right", padx=10, pady=4)

        tablo_cerceve = ctk.CTkFrame(sol_panel, fg_color="#05080F", corner_radius=6)
        tablo_cerceve.pack(side="top", fill="both", expand=True, padx=8, pady=(0, 8))

        stil = ttk.Style()
        try:
            stil.theme_use("clam")
        except Exception:
            pass
        stil.configure(
            "Altar.Treeview",
            background="#05080F",
            foreground="#E2E8F0",
            fieldbackground="#05080F",
            rowheight=25,
            font=("Consolas", 10)
        )
        stil.configure(
            "Altar.Treeview.Heading",
            background="#161B22",
            foreground="#00FFCC",
            font=("Consolas", 10, "bold")
        )
        stil.map("Altar.Treeview", background=[("selected", "#1f538d")], foreground=[("selected", "#FFFFFF")])

        sutunlar = ("ad", "tur", "boyut", "tarih")
        self.tree = ttk.Treeview(tablo_cerceve, columns=sutunlar, show="headings", style="Altar.Treeview")
        self.tree.heading("ad", text="📂 Dosya / Klasör Adı", anchor="w")
        self.tree.heading("tur", text="Tür / Durum", anchor="w")
        self.tree.heading("boyut", text="Boyut", anchor="e")
        self.tree.heading("tarih", text="Değiştirilme Tarihi", anchor="center")

        self.tree.column("ad", width=290, anchor="w")
        self.tree.column("tur", width=110, anchor="w")
        self.tree.column("boyut", width=95, anchor="e")
        self.tree.column("tarih", width=135, anchor="center")

        scroll_y = ttk.Scrollbar(tablo_cerceve, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._secim_degisti_onizle)
        self.tree.bind("<Double-1>", self._cift_tiklama_islem)

        # --- SAĞ PANEL: SALT-OKUNUR ÖNİZLEME & KASA ---
        sag_panel = ctk.CTkFrame(govde, fg_color="transparent")
        sag_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        sag_panel.grid_rowconfigure(0, weight=11)
        sag_panel.grid_rowconfigure(1, weight=10)
        sag_panel.grid_columnconfigure(0, weight=1)

        # SAĞ ÜST: ÖNİZLEME & SHA-256 KİMLİK KARTI
        onizleme_kutu = ctk.CTkFrame(sag_panel, fg_color="#0B1320", corner_radius=8, border_width=1, border_color="#1E293B")
        onizleme_kutu.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        onizleme_ust = ctk.CTkFrame(onizleme_kutu, fg_color="#161B22", corner_radius=6)
        onizleme_ust.pack(side="top", fill="x", padx=8, pady=6)

        ctk.CTkLabel(
            onizleme_ust, text="👁️ SALT-OKUNUR ÖNİZLEME & SHA-256 KİMLİK",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#00E5FF"
        ).pack(side="left", padx=8, pady=4)

        ctk.CTkButton(
            onizleme_ust, text="🧠 AI Analiz", width=88, height=24,
            fg_color="#008080", hover_color="#005959", command=self.secili_dosyayi_ai_gonder
        ).pack(side="right", padx=3, pady=4)

        ctk.CTkButton(
            onizleme_ust, text="🔍 Kopya & Bütünlük", width=128, height=24,
            fg_color="#6A0DAD", hover_color="#4B0082", command=self.kopya_ve_butunluk_taramasi_baslat
        ).pack(side="right", padx=3, pady=4)

        ctk.CTkButton(
            onizleme_ust, text="🚀 Çalıştır/Aç", width=88, height=24,
            fg_color="#1f538d", command=self.secili_ogeyi_varsayilan_ac
        ).pack(side="right", padx=3, pady=4)

        self.txt_onizleme = ctk.CTkTextbox(
            onizleme_kutu, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#A6E3A1", wrap="word"
        )
        self.txt_onizleme.pack(side="top", fill="both", expand=True, padx=8, pady=(0, 8))
        self.txt_onizleme.insert(
            "1.0",
            "📌 Sol listeden bir dosya veya klasör seçtiğinizde:\n"
            "• Boyut, SHA-256 bütünlük özeti ve kilit durumu,\n"
            "• Metin/Kod dosyalarının içeriği veya İkili (Hex) başlığı\n"
            "%100 salt-okunur olarak burada gösterilir."
        )
        self.txt_onizleme.configure(state="disabled")

        # SAĞ ALT: KULLANICI ŞİFRELİ DİZİN & DOSYA KASASI
        kasa_kutu = ctk.CTkFrame(sag_panel, fg_color="#0B1320", corner_radius=8, border_width=1, border_color="#1E293B")
        kasa_kutu.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

        kasa_baslik = ctk.CTkFrame(kasa_kutu, fg_color="#161B22", corner_radius=6)
        kasa_baslik.pack(side="top", fill="x", padx=8, pady=6)

        ctk.CTkLabel(
            kasa_baslik, text="🔐 KULLANICI ŞİFRELİ DİZİN & DOSYA KASASI (PBKDF2 + Fernet)",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#FFD700"
        ).pack(side="left", padx=8, pady=4)

        hedef_frame = ctk.CTkFrame(kasa_kutu, fg_color="transparent")
        hedef_frame.pack(side="top", fill="x", padx=8, pady=2)

        ctk.CTkLabel(hedef_frame, text="Hedef:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(2, 4))
        self.entry_kasa_hedef = ctk.CTkEntry(
            hedef_frame, placeholder_text="Şifrelenecek / Kilidi açılacak dosya veya klasör yolu...",
            height=26, font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.entry_kasa_hedef.pack(side="left", fill="x", expand=True, padx=2)

        sifre_frame = ctk.CTkFrame(kasa_kutu, fg_color="transparent")
        sifre_frame.pack(side="top", fill="x", padx=8, pady=4)

        ctk.CTkLabel(sifre_frame, text="Kasa Şifresi:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(2, 4))
        self.entry_kasa_sifre = ctk.CTkEntry(
            sifre_frame, placeholder_text="Güçlü şifrenizi girin...", show="*",
            width=165, height=26, font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.entry_kasa_sifre.pack(side="left", padx=2)

        self.sifre_goster_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            sifre_frame, text="Göster", variable=self.sifre_goster_var, width=60, checkbox_width=16, checkbox_height=16,
            font=ctk.CTkFont(size=11),
            command=lambda: self.entry_kasa_sifre.configure(show="" if self.sifre_goster_var.get() else "*")
        ).pack(side="left", padx=4)

        self.btn_kilitle = ctk.CTkButton(
            sifre_frame, text="🔒 Şifrele & Kilitle", width=120, height=26,
            fg_color="#C62828", hover_color="#8E0000", font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.kasa_islemi_baslat(kilitle=True)
        )
        self.btn_kilitle.pack(side="left", padx=3)

        self.btn_coz = ctk.CTkButton(
            sifre_frame, text="🔓 Kilidi Aç (Çöz)", width=120, height=26,
            fg_color="#00A86B", hover_color="#007F50", font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.kasa_islemi_baslat(kilitle=False)
        )
        self.btn_coz.pack(side="left", padx=3)

        self.txt_kasa_log = ctk.CTkTextbox(
            kasa_kutu, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05080F", text_color="#00FF88", height=95, wrap="word"
        )
        self.txt_kasa_log.pack(side="top", fill="both", expand=True, padx=8, pady=(2, 8))
        self.txt_kasa_log.insert(
            "1.0",
            "[*] Altar Kriptografik Kasa Hazır. Sol listeden seçtiğiniz klasör veya dosyayı kendi şifrenizle kilitleyebilirsiniz.\n"
        )
        self.txt_kasa_log.configure(state="disabled")

    # =========================================================================
    # DİZİN TARAMA VE GEZİNME METOTLARI
    # =========================================================================
    @staticmethod
    def _mevcut_suruculeri_bul() -> list[str]:
        if os.name == "nt":
            suruculer = []
            for harf in "CDEFGHIJKLMNOPQRSTUVWXYZ":
                yol = f"{harf}:\\"
                if os.path.exists(yol):
                    suruculer.append(yol)
            return suruculer or ["C:\\"]
        return ["/"]

    def diyalogla_dizin_sec(self) -> None:
        secilen = filedialog.askdirectory(initialdir=self.aktif_dizin, title="Gezinilecek Klasörü Seçin")
        if secilen:
            self.dizini_yukle(secilen)

    def geri_git(self) -> None:
        if self.gecmis_yigin:
            onceki = self.gecmis_yigin.pop()
            self.dizini_yukle(onceki, gecmise_ekle=False)

    def ust_dizine_cik(self) -> None:
        ust = os.path.dirname(os.path.abspath(self.aktif_dizin))
        if ust and os.path.exists(ust) and ust != self.aktif_dizin:
            self.dizini_yukle(ust)

    def dizini_yukle(self, hedef_yol: str, gecmise_ekle: bool = True) -> None:
        ham_girdi = os.path.expanduser(hedef_yol.strip().strip('"'))
        if os.name == "nt" and len(ham_girdi) == 2 and ham_girdi[1] == ":":
            ham_girdi += "\\"
        hedef_yol = os.path.abspath(ham_girdi)
        if not os.path.isdir(hedef_yol):
            messagebox.showwarning("Geçersiz Dizin", f"Klasör bulunamadı veya erişilemiyor:\n{hedef_yol}", parent=self)
            return

        if gecmise_ekle and self.aktif_dizin and self.aktif_dizin != hedef_yol:
            self.gecmis_yigin.append(self.aktif_dizin)

        self.aktif_dizin = hedef_yol
        surucu_harfi = os.path.splitdrive(hedef_yol)[0]
        if surucu_harfi:
            surucu_koku = surucu_harfi.upper() + "\\"
            if surucu_koku in self.combo_surucu.cget("values"):
                self.surucu_var.set(surucu_koku)
        self.entry_yol.delete(0, "end")
        self.entry_yol.insert(0, hedef_yol)
        self.entry_kasa_hedef.delete(0, "end")
        self.entry_kasa_hedef.insert(0, hedef_yol)

        self._tarama_id += 1
        mevcut_id = self._tarama_id
        threading.Thread(target=self._arka_plan_dizin_tara, args=(hedef_yol, mevcut_id), daemon=True).start()

    def _arka_plan_dizin_tara(self, dizin_yolu: str, islem_id: int) -> None:
        klasorler: list[tuple[str, str, str, str, str, bool]] = []
        dosyalar: list[tuple[str, str, str, str, str, bool]] = []

        try:
            with os.scandir(dizin_yolu) as it:
                for entry in it:
                    if islem_id != self._tarama_id:
                        return
                    try:
                        st = entry.stat(follow_symlinks=False)
                        tarih_str = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
                        junction_mi = bool(entry.is_junction()) if hasattr(entry, "is_junction") else False  # type: ignore[attr-defined]
                        if entry.is_symlink() or junction_mi:
                            dosyalar.append((
                                f"🔗 {entry.name}",
                                "Sembolik Bağ",
                                _boyut_formatla(st.st_size),
                                tarih_str,
                                entry.path,
                                False
                            ))
                        elif entry.is_dir(follow_symlinks=False):
                            klasorler.append((
                                f"📁 {entry.name}",
                                "Klasör",
                                "-",
                                tarih_str,
                                entry.path,
                                True
                            ))
                        else:
                            uzanti = os.path.splitext(entry.name)[1].lower()
                            kilitli = entry.name.endswith(_KASA_UZANTI)
                            ikon = "🔒" if kilitli else "📄"
                            tur_str = "Şifreli Kasa" if kilitli else (f"{uzanti.upper()} Dosyası" if uzanti else "Dosya")
                            dosyalar.append((
                                f"{ikon} {entry.name}",
                                tur_str,
                                _boyut_formatla(st.st_size),
                                tarih_str,
                                entry.path,
                                False
                            ))
                    except (OSError, PermissionError):
                        continue
        except PermissionError:
            self._ui_gorevi_ekle(
                lambda: messagebox.showwarning("Erişim Engellendi", f"Bu klasörü okumak için yetkiniz yok:\n{dizin_yolu}", parent=self)
            )
            return
        except OSError as exc:
            self._kasa_log_yaz(f"Dizin tarama hatası: {exc}")
            return

        klasorler.sort(key=lambda x: os.path.basename(x[4]).lower())
        dosyalar.sort(key=lambda x: os.path.basename(x[4]).lower())
        birlesik = klasorler + dosyalar

        def _tabloyu_guncelle() -> None:
            if islem_id != self._tarama_id or not self.winfo_exists():
                return
            self._son_satirlar_bellek = birlesik
            self.lbl_dizin_ozet.configure(text=f"{len(klasorler)} Klasör | {len(dosyalar)} Dosya")
            self._bellekten_tabloyu_filtrele()

        self._ui_gorevi_ekle(_tabloyu_guncelle)

    def _bellekten_tabloyu_filtrele(self) -> None:
        filtre = self.entry_filtre.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        self._oge_yollari.clear()

        for ad, tur, boyut, tarih, tam_yol, _ in self._son_satirlar_bellek:
            if not filtre or filtre in ad.lower() or filtre in tur.lower():
                iid = self.tree.insert("", "end", values=(ad, tur, boyut, tarih))
                self._oge_yollari[iid] = tam_yol

    def _cift_tiklama_islem(self, _event: Any = None) -> None:
        secim = self.tree.selection()
        if not secim:
            return
        tam_yol = self._oge_yollari.get(secim[0], "")
        if not tam_yol:
            return

        self.secili_tam_yol = tam_yol
        if os.path.isdir(tam_yol) and not _bag_veya_junction_mi(tam_yol):
            self.dizini_yukle(tam_yol)
        else:
            self.secili_ogeyi_varsayilan_ac()

    def secili_ogeyi_varsayilan_ac(self) -> None:
        if not self.secili_tam_yol or not os.path.exists(self.secili_tam_yol):
            return
        if _bag_veya_junction_mi(self.secili_tam_yol):
            messagebox.showwarning("Sembolik Bağ", "Sembolik bağlar veya NTFS Junction hedefleri güvenlik nedeniyle doğrudan açılamaz.", parent=self)
            return
        if self.secili_tam_yol.endswith(_KASA_UZANTI):
            messagebox.showinfo(
                "Kilitli Dosya",
                "Bu dosya Altar Kasası ile şifrelenmiştir.\nÖnce sağ alttan şifrenizi girerek '🔓 Kilidi Aç' butonuna basın.",
                parent=self
            )
            return

        # MP4 ve Video Medyalarn Altar Sinematik Tam Ekran Oynatc ile A
        if self.secili_tam_yol.lower().endswith((".mp4", ".mkv", ".avi", ".mov")):
            try:
                from altar_video_oynatici import sinematik_video_oynat
                sinematik_video_oynat(self.secili_tam_yol, parent=self)
                return
            except Exception:
                pass

        try:
            if hasattr(os, "startfile"):
                os.startfile(self.secili_tam_yol)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.secili_tam_yol])
            else:
                subprocess.Popen(["xdg-open", self.secili_tam_yol])
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılamadı:\n{e}", parent=self)

    # =========================================================================
    # SALT-OKUNUR ÖNİZLEME VE SHA-256 ANALİZİ
    # =========================================================================
    def _secim_degisti_onizle(self, _event: Any = None) -> None:
        secim = self.tree.selection()
        if not secim:
            return
        tam_yol = self._oge_yollari.get(secim[0], "")
        if not tam_yol:
            return

        self.secili_tam_yol = tam_yol
        self.entry_kasa_hedef.delete(0, "end")
        self.entry_kasa_hedef.insert(0, tam_yol)

        self._onizleme_id += 1
        mevcut_id = self._onizleme_id

        def _onizleme_worker() -> None:
            try:
                if _bag_veya_junction_mi(tam_yol):
                    rapor = (
                        "🔗 [SEMBOLİK BAĞ / JUNCTION]\n"
                        f"• Adı        : {os.path.basename(tam_yol)}\n"
                        f"• Tam Konum  : {tam_yol}\n"
                        "• Güvenlik   : Önizleme hedef dosyayı takip etmemek için kapatıldı."
                    )
                elif os.path.isdir(tam_yol):
                    alt_klasor, alt_dosya, kilitli_sayisi = 0, 0, 0
                    try:
                        with os.scandir(tam_yol) as it:
                            for e in it:
                                if e.is_dir(follow_symlinks=False):
                                    alt_klasor += 1
                                else:
                                    alt_dosya += 1
                                    if e.name.endswith(_KASA_UZANTI):
                                        kilitli_sayisi += 1
                    except (OSError, PermissionError):
                        pass

                    rapor = (
                        f"📁 [KLASÖR KİMLİK KARTI]\n"
                        f"• Klasör Adı   : {os.path.basename(tam_yol)}\n"
                        f"• Tam Konum    : {tam_yol}\n"
                        f"• İçerik Özeti : {alt_klasor} Alt Klasör, {alt_dosya} Dosya\n"
                        f"• Kasa Durumu  : {kilitli_sayisi} Şifreli Dosya Mevcut\n\n"
                        "💡 İPUCU: Klasörün içine girmek için çift tıklayın veya sağ alttan tüm klasörü şifreleyin."
                    )
                else:
                    boyut = os.path.getsize(tam_yol)
                    with open(tam_yol, "rb") as f:
                        ornek = f.read(65536)

                    if boyut > _MAX_HASH_BOYUT:
                        sha256_ozet = f"Dosya çok büyük ({_boyut_formatla(boyut)} > 2 GB); disk performansını korumak için tam SHA-256 atlandı."
                    else:
                        sha256_hesaplayici = hashlib.sha256()
                        with open(tam_yol, "rb") as hash_dosyasi:
                            for parca in iter(lambda: hash_dosyasi.read(1024 * 1024), b""):
                                if mevcut_id != self._onizleme_id:
                                    return
                                sha256_hesaplayici.update(parca)
                        sha256_ozet = sha256_hesaplayici.hexdigest()
                    kilitli_mi = ornek.startswith(_KASA_IMZA) or tam_yol.endswith(_KASA_UZANTI)

                    ust_bilgi = (
                        f"📄 [DOSYA KİMLİK KARTI]\n"
                        f"• Dosya Adı : {os.path.basename(tam_yol)}\n"
                        f"• Boyut     : {_boyut_formatla(boyut)} ({boyut:,} B)\n"
                        f"• Durum     : {'🔒 ALTAR KASA İLE ŞİFRELİ' if kilitli_mi else '🔓 AÇIK (STANDART)'}\n"
                        f"• SHA-256   : {sha256_ozet}\n"
                        f"{'-'*52}\n"
                    )

                    if kilitli_mi:
                        icerik_onizleme = (
                            "🔒 Bu dosya PBKDF2-HMAC-SHA256 + Fernet ile şifrelenmiştir.\n"
                            "İçeriği görüntülemek için sağ alttaki Kasa paneline şifrenizi girip '🔓 Kilidi Aç' butonuna tıklayın."
                        )
                    elif boyut == 0:
                        icerik_onizleme = "[DOSYA BOŞ - 0 Bayt]"
                    elif b"\x00" not in ornek[:1024]:
                        try:
                            metin = ornek[:8192].decode("utf-8")
                        except UnicodeDecodeError:
                            metin = ornek[:8192].decode("latin-1", errors="replace")
                        icerik_onizleme = f"[METİN / KOD ÖNİZLEMESİ - İlk 8 KB]:\n\n{metin}"
                    else:
                        hex_satirlar = []
                        for i in range(0, min(len(ornek), 512), 16):
                            parca = ornek[i:i + 16]
                            hex_k = " ".join(f"{b:02X}" for b in parca)
                            asc_k = "".join(chr(b) if 32 <= b <= 126 else "." for b in parca)
                            hex_satirlar.append(f"{i:04X} | {hex_k:<47} | {asc_k}")
                        icerik_onizleme = "[İKİLİ (BINARY / HEX) BAŞLIK ÖNİZLEMESİ]:\n\n" + "\n".join(hex_satirlar)

                    rapor = ust_bilgi + icerik_onizleme

                def _ekrana_yaz() -> None:
                    if mevcut_id != self._onizleme_id or not self.winfo_exists():
                        return
                    self.txt_onizleme.configure(state="normal")
                    self.txt_onizleme.delete("1.0", "end")
                    self.txt_onizleme.insert("1.0", rapor)
                    self.txt_onizleme.configure(state="disabled")

                self._ui_gorevi_ekle(_ekrana_yaz)
            except (OSError, PermissionError):
                pass

        threading.Thread(target=_onizleme_worker, daemon=True).start()

    def secili_dosyayi_ai_gonder(self) -> None:
        metin = self.txt_onizleme.get("1.0", "end").strip()
        if not metin or "Sol listeden bir dosya" in metin:
            messagebox.showwarning("Seçim Yok", "Lütfen önce listeden analiz edilecek bir dosya seçin.", parent=self)
            return
        if self.ai_analiz_callback:
            self.ai_analiz_callback(f"DOSYA GEZGİNİ SEÇİLİ ÖĞE ANALİZİ:\n{metin[:5500]}")

    # =========================================================================
    # KULLANICI ŞİFRELİ DİZİN & DOSYA KASASI (PBKDF2 + FERNET)
    # =========================================================================
    @staticmethod
    def _tek_dosya_sifrele(dosya_yolu: str, parola: str) -> tuple[bool, str]:
        """Dosyayı şifreler; çıktı varsa üzerine yazmaz ve kaynak dosyayı en son siler."""
        if not CRYPTO_AVAILABLE or Fernet is None:
            return False, "cryptography kütüphanesi kurulu değil."
        if os.path.islink(dosya_yolu):
            return False, "Sembolik bağ dosyaları güvenlik nedeniyle işlenmiyor."
        if dosya_yolu.endswith(_KASA_UZANTI):
            return False, "Zaten şifreli uzantıya sahip; atlandı."

        try:
            boyut = os.path.getsize(dosya_yolu)
            if boyut > _MAX_FERNET_BOYUT:
                return False, f"Dosya çok büyük ({_boyut_formatla(boyut)}). Güvenli işlem sınırı 4 GB'dir."
            with open(dosya_yolu, "rb") as f:
                ham_veri = f.read()
        except OSError as exc:
            return False, f"Kaynak dosya okunamadı: {exc}"

        if ham_veri.startswith(_KASA_IMZA):
            return False, "Dosya zaten Altar Kasa imzası taşıyor."

        salt = secrets.token_bytes(16)
        anahtar = _paroladan_fernet_anahtari_uret(parola, salt)
        fernet_obj = Fernet(anahtar)
        sifreli_veri = fernet_obj.encrypt(ham_veri)
        del ham_veri
        kilitli_yol = dosya_yolu + _KASA_UZANTI
        hedef_olusturuldu = False

        try:
            with open(kilitli_yol, "xb") as f_out:
                hedef_olusturuldu = True
                f_out.write(_KASA_IMZA + salt + sifreli_veri)
                f_out.flush()
                os.fsync(f_out.fileno())
        except FileExistsError:
            return False, f"Hedef zaten var; üzerine yazılmadı: {kilitli_yol}"
        except OSError as exc:
            if hedef_olusturuldu:
                try:
                    os.remove(kilitli_yol)
                except OSError:
                    pass
            return False, f"Şifreli çıktı yazılamadı: {exc}"

        try:
            os.remove(dosya_yolu)
        except OSError as exc:
            return True, f"{kilitli_yol} (şifrelendi; fakat kaynak silinemedi: {exc})"
        return True, kilitli_yol

    @staticmethod
    def _tek_dosya_coz(kilitli_yol: str, parola: str) -> tuple[bool, str]:
        """Şifreyi çözer; mevcut özgün dosyanın üzerine yazmaz."""
        if not CRYPTO_AVAILABLE or Fernet is None:
            return False, "cryptography kütüphanesi kurulu değil."
        if os.path.islink(kilitli_yol):
            return False, "Sembolik bağ dosyaları güvenlik nedeniyle işlenmiyor."

        try:
            with open(kilitli_yol, "rb") as f:
                paket = f.read()
        except OSError as exc:
            return False, f"Şifreli dosya okunamadı: {exc}"

        baslik_uzunlugu = len(_KASA_IMZA)
        if not paket.startswith(_KASA_IMZA) or len(paket) < baslik_uzunlugu + 16:
            return False, "Geçerli veya eksiksiz bir Altar Kasa dosyası değil."

        salt = paket[baslik_uzunlugu:baslik_uzunlugu + 16]
        sifreli_veri = paket[baslik_uzunlugu + 16:]
        del paket
        anahtar = _paroladan_fernet_anahtari_uret(parola, salt)
        fernet_obj = Fernet(anahtar)

        try:
            cozulmus_veri = fernet_obj.decrypt(sifreli_veri)
            del sifreli_veri
        except InvalidToken:
            return False, "HATALI ŞİFRE veya bozuk şifreli veri; kaynak dosya korunuyor."
        except Exception as exc:
            return False, f"Şifre çözme hatası: {exc}"

        if kilitli_yol.endswith(_KASA_UZANTI):
            orijinal_yol = kilitli_yol[:-len(_KASA_UZANTI)]
        else:
            orijinal_yol = kilitli_yol + ".decrypted"

        if os.path.lexists(orijinal_yol):
            return False, f"Çözülen dosya hedefi zaten mevcut; üzerine yazılmadı: {orijinal_yol}"

        hedef_olusturuldu = False
        try:
            with open(orijinal_yol, "xb") as f_out:
                hedef_olusturuldu = True
                f_out.write(cozulmus_veri)
                f_out.flush()
                os.fsync(f_out.fileno())
        except FileExistsError:
            return False, f"Hedef zaten mevcut; üzerine yazılmadı: {orijinal_yol}"
        except OSError as exc:
            if hedef_olusturuldu:
                try:
                    os.remove(orijinal_yol)
                except OSError:
                    pass
            return False, f"Çözülmüş dosya yazılamadı: {exc}"

        try:
            os.remove(kilitli_yol)
        except OSError as exc:
            return True, f"{orijinal_yol} (dosya çözüldü; fakat şifreli kaynak silinemedi: {exc})"
        return True, orijinal_yol

    def kasa_islemi_baslat(self, kilitle: bool) -> None:
        if not CRYPTO_AVAILABLE:
            messagebox.showerror("Eksik Kütüphane", "Kriptografik kasa için 'pip install cryptography' kurmalısınız.", parent=self)
            return
        if self._kasa_islem_aktif:
            return

        hedef = os.path.abspath(os.path.expanduser(self.entry_kasa_hedef.get().strip().strip('"')))
        parola = self.entry_kasa_sifre.get()

        if not hedef or not os.path.exists(hedef):
            messagebox.showwarning("Hedef Yok", "Lütfen geçerli bir dosya veya klasör seçin.", parent=self)
            return
        if _bag_veya_junction_mi(hedef):
            messagebox.showerror("Güvenlik Koruması", "Sembolik bağ veya NTFS Junction hedefleri işlenmiyor. Gerçek dosya/klasör yolunu seçin.", parent=self)
            return
        hedef = os.path.realpath(hedef)

        if kilitle and len(parola) < 8:
            messagebox.showwarning(
                "Şifre Gerekli",
                "Yeni şifreleme için en az 8 karakterli bir parola girin; daha uzun ve benzersiz bir parola tercih edin.",
                parent=self
            )
            return
        if not kilitle and not parola:
            messagebox.showwarning("Şifre Gerekli", "Kilidi açmak için dosyayı şifrelerken kullandığınız parolayı girin.", parent=self)
            return

        guvenli, uyari_mesaji = _hedef_yol_guvenli_mi(hedef)
        if not guvenli:
            messagebox.showerror("Güvenlik Koruması", uyari_mesaji, parent=self)
            return

        islem_adi = "ŞİFRELEME (KİLİTLEME)" if kilitle else "KİLİT AÇMA (ŞİFRE ÇÖZME)"
        onay = messagebox.askyesno(
            f"Altar Kasa - {islem_adi}",
            f"Hedef: {hedef}\n\nBu konum üzerinde '{islem_adi}' işlemi uygulanacak. Onaylıyor musunuz?",
            parent=self
        )
        if not onay:
            return

        self._kasa_islem_aktif = True
        self.btn_kilitle.configure(state="disabled")
        self.btn_coz.configure(state="disabled")
        self._kasa_log_yaz(f"⏳ {islem_adi} başlatıldı: {os.path.basename(hedef)}...")

        def _worker() -> None:
            basarili_sayac = 0
            hatali_sayac = 0
            sifre_hatasi_var = False

            try:
                if os.path.isfile(hedef):
                    ok, bilgi = self._tek_dosya_sifrele(hedef, parola) if kilitle else self._tek_dosya_coz(hedef, parola)
                    if ok:
                        basarili_sayac += 1
                        self._kasa_log_yaz(f"✅ İşlem tamamlandı: {os.path.basename(bilgi)}")
                    else:
                        hatali_sayac += 1
                        self._kasa_log_yaz(f"❌ Atlandı / Hata: {bilgi}")
                        if "HATALI ŞİFRE" in bilgi:
                            sifre_hatasi_var = True

                elif os.path.isdir(hedef):
                    for kok, dirs, files in os.walk(hedef, followlinks=False):
                        dirs[:] = [
                            d for d in dirs
                            if d not in (".git", ".venv", "venv", "__pycache__", "node_modules")
                            and not _bag_veya_junction_mi(os.path.join(kok, d))
                        ]
                        for d_adi in files:
                            tam_dosya = os.path.join(kok, d_adi)
                            try:
                                if kilitle and not d_adi.endswith(_KASA_UZANTI):
                                    ok, bilgi = self._tek_dosya_sifrele(tam_dosya, parola)
                                    if ok:
                                        basarili_sayac += 1
                                        self._kasa_log_yaz(f"✅ Şifrelendi: {os.path.basename(tam_dosya)}")
                                    else:
                                        hatali_sayac += 1
                                        self._kasa_log_yaz(f"⚠️ Atlandı / Hata ({tam_dosya}): {bilgi}")
                                elif not kilitle and d_adi.endswith(_KASA_UZANTI):
                                    ok, bilgi = self._tek_dosya_coz(tam_dosya, parola)
                                    if ok:
                                        basarili_sayac += 1
                                        self._kasa_log_yaz(f"✅ Kilidi açıldı: {os.path.basename(bilgi)}")
                                    else:
                                        hatali_sayac += 1
                                        self._kasa_log_yaz(f"⚠️ Atlandı / Hata ({tam_dosya}): {bilgi}")
                                        if "HATALI ŞİFRE" in bilgi:
                                            sifre_hatasi_var = True
                                            break
                            except Exception as exc:
                                hatali_sayac += 1
                                self._kasa_log_yaz(f"❌ Dosya işlenemedi ({tam_dosya}): {exc}")
                        if sifre_hatasi_var:
                            break

                ozet = f"🏁 {islem_adi} Tamamlandı -> Başarılı: {basarili_sayac} | Hata/Atlanan: {hatali_sayac}"
                self._kasa_log_yaz(ozet)

                def _bitis_bildir() -> None:
                    if not self.winfo_exists():
                        return
                    self.dizini_yukle(self.aktif_dizin, gecmise_ekle=False)
                    if sifre_hatasi_var:
                        messagebox.showerror("Hatalı Şifre", "Girdiğiniz Kasa Şifresi yanlış. Şifreli kaynak dosyalar korunmuştur.", parent=self)
                    else:
                        messagebox.showinfo("Kasa İşlemi Tamamlandı", ozet, parent=self)

                self._ui_gorevi_ekle(_bitis_bildir)
            except Exception as exc:
                self._kasa_log_yaz(f"❌ Kasa işlemi beklenmeyen hatayla durdu: {exc}")
                hata_metni = str(exc)
                self._ui_gorevi_ekle(
                    lambda: messagebox.showerror("Kasa İşlemi Hatası", hata_metni, parent=self)
                    if self.winfo_exists() else None
                )
            finally:
                def _kilidi_kaldir() -> None:
                    self._kasa_islem_aktif = False
                    if self.winfo_exists():
                        self.btn_kilitle.configure(state="normal")
                        self.btn_coz.configure(state="normal")
                self._ui_gorevi_ekle(_kilidi_kaldir)

        threading.Thread(target=_worker, daemon=True).start()

    # =========================================================================
    # %100 SALT-OKUNUR KOPYA DOSYA (SHA-256) VE BÜYÜK DOSYA DENETLEYİCİSİ
    # =========================================================================
    def kopya_ve_butunluk_taramasi_baslat(self) -> None:
        """
        Aktif dizindeki dosyaları %100 salt-okunur (hiçbir dosyayı silmeden/değiştirmeden)
        tarayarak birebir aynı SHA-256 özetine sahip kopya dosyaları ve en büyük dosyaları raporlar.
        """
        hedef_dizin = self.aktif_dizin
        if not hedef_dizin or not os.path.isdir(hedef_dizin):
            return

        self._onizleme_yaz(f"🔍 '{hedef_dizin}' dizininde %100 Salt-Okunur SHA-256 Kopya & Bütünlük taraması yapılıyor...")
        self._kasa_log_yaz(f"🔍 Salt-okunur kopya ve bütünlük analizi başlatıldı: {hedef_dizin}")

        def _tara_worker() -> None:
            boyut_gruplari: dict[int, list[str]] = {}
            tum_dosyalar: list[tuple[int, str]] = []
            taranan = 0
            maks_dosya = 400

            try:
                for kok_d, alt_d, dosyalar in os.walk(hedef_dizin):
                    alt_d[:] = [
                        d for d in alt_d
                        if not os.path.islink(os.path.join(kok_d, d))
                        and d not in (".git", ".venv", "venv", "node_modules", "__pycache__")
                    ]
                    for d_adi in dosyalar:
                        tam = os.path.join(kok_d, d_adi)
                        if os.path.islink(tam):
                            continue
                        try:
                            b = os.path.getsize(tam)
                            tum_dosyalar.append((b, tam))
                            if 0 < b <= 150 * 1024 * 1024:
                                boyut_gruplari.setdefault(b, []).append(tam)
                            taranan += 1
                            if taranan >= maks_dosya:
                                break
                        except OSError:
                            continue
                    if taranan >= maks_dosya:
                        break

                hash_gruplari: dict[str, list[tuple[str, int]]] = {}
                for b_degeri, adaylar in boyut_gruplari.items():
                    if len(adaylar) < 2:
                        continue
                    for yol in adaylar:
                        ozet = self._dosya_sha256_hesapla(yol, maks_mb=150)
                        if len(ozet) == 64:
                            hash_gruplari.setdefault(ozet, []).append((yol, b_degeri))

                kopyalar = {h: liste for h, liste in hash_gruplari.items() if len(liste) > 1}
                tum_dosyalar.sort(key=lambda x: x[0], reverse=True)

                rapor = [
                    "==================================================================",
                    "   🔍 %100 SALT-OKUNUR KOPYA DOSYA & SHA-256 BÜTÜNLÜK RAPORU",
                    "==================================================================",
                    f"Taranan Dizin    : {hedef_dizin}",
                    f"İncelenen Dosya  : {taranan} adet (Hiçbir dosyaya müdahale edilmedi)",
                    f"Bulunan Kopya Gr.: {len(kopyalar)} grup",
                    "------------------------------------------------------------------"
                ]

                if kopyalar:
                    rapor.append("📌 BİREBİR AYNI (SHA-256 EŞLEŞEN) KOPYA DOSYALAR:")
                    for idx, (h_deger, liste) in enumerate(list(kopyalar.items())[:15], 1):
                        rapor.append(f"\n[{idx}] SHA-256: {h_deger[:24]}... ({_boyut_formatla(liste[0][1])})")
                        for y_yol, _ in liste:
                            rapor.append(f"   • {os.path.relpath(y_yol, hedef_dizin)}")
                else:
                    rapor.append("✅ Bu dizinde birebir kopya (mükerrer) dosya tespit edilmedi.")

                rapor.append("\n------------------------------------------------------------------")
                rapor.append("📊 DİZİNDEKİ EN BÜYÜK İLK 8 DOSYA:")
                for b_boy, y_yol in tum_dosyalar[:8]:
                    rapor.append(f"   • {_boyut_formatla(b_boy):>10}  |  {os.path.relpath(y_yol, hedef_dizin)}")

                son_metin = "\n".join(rapor)
                self._ui_gorevi_ekle(lambda: self._onizleme_yaz(son_metin))
                self._kasa_log_yaz(f"✅ Kopya & Bütünlük taraması tamamlandı ({len(kopyalar)} kopya grubu bulundu).")
            except Exception as exc:
                self._kasa_log_yaz(f"⚠️ Tarama uyarısı: {exc}")

        threading.Thread(target=_tara_worker, daemon=True).start()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    kok = ctk.CTk()
    kok.title("Altar - Dosya Gezgini & Kriptografik Kasa")
    kok.geometry("1280x780")
    kok.after(20, lambda: kok.attributes("-fullscreen", True))
    kok.bind("<F11>", lambda _: kok.attributes("-fullscreen", not kok.attributes("-fullscreen")))
    kok.bind("<Escape>", lambda _: kok.attributes("-fullscreen", False))
    sekme = DosyaGezginiVeKasaSekmesi(kok)
    sekme.pack(fill="both", expand=True, padx=10, pady=10)
    kok.mainloop()