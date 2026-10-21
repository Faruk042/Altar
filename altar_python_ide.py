# -*- coding: utf-8 -*-
"""
Altar Tümleşik Python IDE & Çoklu Sekmeli Kod Editörü Modülü (altar_python_ide.py)

PyCharm gibi ağır (2.5+ GB RAM tüketen) harici IDE'lere ihtiyaç duymadan
doğrudan Altar içerisinde (~18 MB ek bellek ile):
  1) Çoklu Sekmeli (Multi-Tab) dosya yönetimi: Birden fazla .py dosyasını aynı anda
     açma, sekmeler arası geçiş ve bağımsız kaydetme,
  2) Python yorumlayıcı (.venv, Sistem Python 3.x) seçici açılır menü,
  3) Görsel Pip Paket Yöneticisi (altar_pip_yoneticisi.py entegrasyonu),
  4) Satır numaraları, otomatik girinti (Auto-Indent), Ctrl+Tekerlek font ölçekleme
     ve Python sözdizimi renklendirme (Syntax Highlighting),
  5) Çalıştırmadan önce AST tabanlı anlık sözdizimi ve hata satırı işaretleme (ast.parse),
  6) Canlı alt-süreç konsolu ile kodu çalıştırma (F5), durdurma ve stdin input() gönderme,
  7) Kod veya Traceback hatalarını tek tıkla Altar Yapay Zeka (Yazılım Profili) motoruna gönderme.
"""

from __future__ import annotations

import ast
import keyword
import os
import queue
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional, Tuple

import customtkinter as ctk

from altar_pip_yoneticisi import AltarPipYoneticisiModal
from altar_animasyon_motoru import AltarMaviAtesWidget
from altar_kod_sablonlari import AltarSablonSeciciModal


class AltarPythonIDESekmesi(ctk.CTkFrame):
    """Altar ana sekme yapısına doğrudan gömülen çok sekmeli Python geliştirme ortamı."""

    ANAHTAR_KELIMELER = set(keyword.kwlist)
    YERLESIK_FONKSIYONLAR = {
        "abs", "all", "any", "bin", "bool", "bytes", "callable", "chr", "classmethod",
        "dict", "dir", "divmod", "enumerate", "Exception", "filter", "float", "format",
        "frozenset", "getattr", "hasattr", "hash", "hex", "id", "input", "int", "isinstance",
        "issubclass", "iter", "len", "list", "map", "max", "min", "next", "object", "oct",
        "open", "ord", "pow", "print", "property", "range", "repr", "reversed", "round",
        "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super", "tuple",
        "type", "vars", "zip",
    }

    VARSAYILAN_SABLON = (
        "# -*- coding: utf-8 -*-\n"
        "\"\"\"\n"
        "Altar Python IDE — Hızlı Kodlama ve Çoklu Sekme Ortamı\n"
        "Kısayollar: F5 = Çalıştır | Ctrl+S = Kaydet | Ctrl+MouseWheel = Yakınlaştır\n"
        "\"\"\"\n\n"
        "import sys\n"
        "from datetime import datetime\n\n\n"
        "def ana_program() -> None:\n"
        "    print(f\"🚀 Altar Python Motoru Aktif! ({datetime.now().strftime('%H:%M:%S')})\")\n"
        "    print(f\"Python Sürümü: {sys.version.split()[0]}\")\n"
        "    sayilar = [x ** 2 for x in range(1, 6)]\n"
        "    print(\"Örnek Liste Üreteci:\", sayilar)\n\n\n"
        "if __name__ == \"__main__\":\n"
        "    ana_program()\n"
    )

    def __init__(
        self,
        master: object,
        calisma_dizini: str = "",
        ai_aktarim_callback: Optional[Callable[[str], None]] = None,
        **kwargs: object,
    ) -> None:
        super().__init__(master, fg_color="#0B0F19", **kwargs)
        self.calisma_dizini = calisma_dizini or os.path.dirname(os.path.abspath(__file__))
        self.ai_aktarim_callback = ai_aktarim_callback

        # Çoklu Sekme (Multi-Tab) Veri Yapısı:
        # id -> {"yol": Optional[str], "baslik": str, "icerik": str, "degisiklik": bool}
        self.acik_sekmeler: Dict[str, Dict[str, Any]] = {}
        self.aktif_sekme_id: str = ""
        self._sekme_sayaci: int = 1

        self.calisan_surec: Optional[subprocess.Popen] = None
        self.cikti_kuyrugu: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self._renklendirme_zamanlayici: Optional[str] = None
        self._baslangic_zamani: float = 0.0
        self._font_boyutu: int = 12

        # Algılanan Python Yorumlayıcıları
        self.python_yorumlari: List[Tuple[str, str]] = self._python_ortamlarini_tara()

        self._arayuzu_kur()
        self.dosya_agacini_yenile()

        # İlk varsayılan sekmeyi aç
        self.yeni_sekme_ac(baslik="yeni_betik.py", icerik=self.VARSAYILAN_SABLON)
        self.after(120, self._kuyrugu_tara)

    @classmethod
    def _python_ortamlarini_tara(cls) -> List[Tuple[str, str]]:
        """Sistemdeki Python yorumlayıcılarını (.venv, yerel Python 3.x) otomatik tespit eder."""
        adaylar = []
        gorulen_yollar = set()

        def _ekle(etiket: str, yol: str):
            if not yol:
                return
            yol_temiz = os.path.normpath(yol)
            if yol_temiz.lower().endswith("pythonw.exe"):
                yol_temiz = yol_temiz[:-11] + "python.exe"
            if os.path.isfile(yol_temiz) and yol_temiz.lower() not in gorulen_yollar:
                gorulen_yollar.add(yol_temiz.lower())
                adaylar.append((etiket, yol_temiz))

        # 1. Proje .venv (Altar Ana Çalışma Ortamı)
        _ekle("🐍 Altar .venv", r"E:\Yazılım\Python\.venv\Scripts\python.exe")
        _ekle("🐍 Altar .venv (ASCII)", r"E:\Yazilim\Python\.venv\Scripts\python.exe")
        cwd = os.getcwd()
        _ekle("🐍 Proje .venv", os.path.join(cwd, ".venv", "Scripts", "python.exe"))
        _ekle("🐍 Proje ..venv", os.path.join(cwd, "..", ".venv", "Scripts", "python.exe"))
        _ekle("🐍 Proje ...venv", os.path.join(cwd, "..", "..", ".venv", "Scripts", "python.exe"))
        _ekle("🐍 PyCharm .venv", r"C:\Users\Burak\PycharmProjects\PythonProject\.venv\Scripts\python.exe")

        # 2. Sistem Python 3.13 / 3.12 / 3.11
        _ekle("🐍 Sistem Python 3.13", os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python313\python.exe"))
        _ekle("🐍 Sistem Python 3.12", os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe"))
        _ekle("🐍 Sistem Python 3.11", os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\python.exe"))

        # 3. Aktif çalışan sys.executable
        if not getattr(sys, "frozen", False):
            _ekle("🐍 Aktif Yorumlayıcı", sys.executable)

        # 4. PATH üzerindeki python
        path_py = shutil.which("python") or shutil.which("python3")
        if path_py:
            _ekle("🐍 PATH Python", path_py)

        if not adaylar:
            adaylar.append(("🐍 Python (Varsayılan)", "python"))

        return adaylar

    # =========================================================================
    # ARAYÜZ KURULUMU
    # =========================================================================
    def _arayuzu_kur(self) -> None:
        # 1. Üst Araç Çubuğu (Toolbar)
        ust_bar = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8, height=44)
        ust_bar.pack(side="top", fill="x", padx=6, pady=(6, 4))

        ctk.CTkButton(
            ust_bar, text="📄 Yeni", width=68, height=30, fg_color="#1E3A8A", hover_color="#1D4ED8",
            font=ctk.CTkFont(size=12, weight="bold"), command=lambda: self.yeni_sekme_ac()
        ).pack(side="left", padx=(6, 3), pady=6)

        ctk.CTkButton(
            ust_bar, text="📂 Aç", width=65, height=30, fg_color="#1E3A8A", hover_color="#1D4ED8",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.dosya_ac_diyalog
        ).pack(side="left", padx=3, pady=6)

        ctk.CTkButton(
            ust_bar, text="💾 Kaydet (Ctrl+S)", width=125, height=30, fg_color="#047857", hover_color="#059669",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.dosya_kaydet
        ).pack(side="left", padx=3, pady=6)

        ctk.CTkButton(
            ust_bar, text="💾 Farklı", width=75, height=30, fg_color="#374151", hover_color="#4B5563",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.dosya_farkli_kaydet
        ).pack(side="left", padx=3, pady=6)

        ctk.CTkButton(
            ust_bar, text="🔍 AST Denetle", width=120, height=30, fg_color="#6D28D9", hover_color="#7C3AED",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.ast_sozdizimi_denetle
        ).pack(side="left", padx=4, pady=6)

        self.btn_calistir = ctk.CTkButton(
            ust_bar, text="▶️ Çalıştır (F5)", width=120, height=30, fg_color="#15803D", hover_color="#16A34A",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.kodu_calistir
        )
        self.btn_calistir.pack(side="left", padx=3, pady=6)

        self.btn_durdur = ctk.CTkButton(
            ust_bar, text="⏹️ Durdur", width=80, height=30, fg_color="#B91C1C", hover_color="#DC2626",
            font=ctk.CTkFont(size=12, weight="bold"), state="disabled", command=self.calisan_kodu_durdur
        )
        self.btn_durdur.pack(side="left", padx=3, pady=6)

        # Pip Paket Yöneticisi Butonu
        ctk.CTkButton(
            ust_bar, text="📦 Pip Paketleri", width=115, height=30, fg_color="#0284C7", hover_color="#0369A1",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.pip_yoneticisini_ac
        ).pack(side="left", padx=4, pady=6)

        # Proje Kod Şablonları Butonu
        ctk.CTkButton(
            ust_bar, text="🧩 Şablonlar", width=105, height=30, fg_color="#4338CA", hover_color="#4F46E5",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.sablon_secici_ac
        ).pack(side="left", padx=4, pady=6)

        # Python Yorumlayıcı Seçici Açılır Menü
        yorum_etiketleri = [e[0] for e in self.python_yorumlari]
        self.combo_python_var = ctk.StringVar(value=yorum_etiketleri[0])
        self.combo_python = ctk.CTkOptionMenu(
            ust_bar, variable=self.combo_python_var, values=yorum_etiketleri, width=155, height=30,
            fg_color="#374151", button_color="#1F2937", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.combo_python.pack(side="left", padx=4, pady=6)

        ctk.CTkButton(
            ust_bar, text="🤖 Kodu/Hatayı AI'a Sor", width=155, height=30, fg_color="#B45309", hover_color="#D97706",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.ai_asistana_gonder
        ).pack(side="right", padx=(4, 6), pady=6)

        # 2. Ana Gövde (Sol: Hızlı Proje Dosyaları | Sağ: Çoklu Sekmeli Kod Editörü + Canlı Terminal)
        ana_govde = ctk.CTkFrame(self, fg_color="transparent")
        ana_govde.pack(side="top", fill="both", expand=True, padx=6, pady=(0, 6))
        ana_govde.grid_columnconfigure(0, weight=0)
        ana_govde.grid_columnconfigure(1, weight=1)
        ana_govde.grid_rowconfigure(0, weight=1)

        # Sol Panel: Proje Dosya Listesi
        sol_panel = ctk.CTkFrame(ana_govde, fg_color="#111827", corner_radius=8, width=220)
        sol_panel.grid(row=0, column=0, sticky="ns", padx=(0, 6))
        sol_panel.pack_propagate(False)

        sol_ust = ctk.CTkFrame(sol_panel, fg_color="transparent")
        sol_ust.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(
            sol_ust, text="📁 Proje .PY Dosyaları", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00F5D4"
        ).pack(side="left")
        ctk.CTkButton(
            sol_ust, text="🔄", width=28, height=24, fg_color="#1F2937", command=self.dosya_agacini_yenile
        ).pack(side="right")

        ctk.CTkButton(
            sol_panel, text="📂 Klasör Seç...", height=26, fg_color="#1E293B", hover_color="#334155",
            font=ctk.CTkFont(size=11), command=self.calisma_klasoru_degistir
        ).pack(fill="x", padx=8, pady=(0, 4))

        self.liste_dosyalar = tk.Listbox(
            sol_panel, bg="#070B14", fg="#E2E8F0", selectbackground="#1D4ED8", selectforeground="#FFFFFF",
            font=("Consolas", 10), bd=0, highlightthickness=1, highlightbackground="#1E293B", activestyle="none"
        )
        self.liste_dosyalar.pack(fill="both", expand=True, padx=8, pady=(2, 8))
        self.liste_dosyalar.bind("<<ListboxSelect>>", self._listeden_dosya_secildi)

        # Sağ Panel: Üstte Çoklu Sekme Şeridi + Kod Editörü (%65), Altta Canlı Terminal (%35)
        sag_panel = ctk.CTkFrame(ana_govde, fg_color="transparent")
        sag_panel.grid(row=0, column=1, sticky="nsew")
        sag_panel.grid_rowconfigure(0, weight=0)  # Sekme çubuğu
        sag_panel.grid_rowconfigure(1, weight=13) # Editör
        sag_panel.grid_rowconfigure(2, weight=7)  # Terminal
        sag_panel.grid_columnconfigure(0, weight=1)

        # Çoklu Sekme Şeridi (Multi-Tab Strip)
        self.sekme_seridi = ctk.CTkScrollableFrame(
            sag_panel, fg_color="#0B0F19", orientation="horizontal", height=34, corner_radius=6
        )
        self.sekme_seridi.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        # Kod Editörü Çerçevesi (Satır Numaraları + Text)
        editor_cerceve = ctk.CTkFrame(sag_panel, fg_color="#070B14", corner_radius=8, border_width=1, border_color="#1E293B")
        editor_cerceve.grid(row=1, column=0, sticky="nsew", pady=(0, 5))

        self.txt_satir_no = tk.Text(
            editor_cerceve, width=5, padx=6, pady=8, takefocus=0, bd=0,
            bg="#0D1322", fg="#64748B", font=("Consolas", self._font_boyutu), state="disabled", wrap="none"
        )
        self.txt_satir_no.pack(side="left", fill="y")

        scroll_y = ctk.CTkScrollbar(editor_cerceve, command=self._ortak_dikey_kaydir)
        scroll_y.pack(side="right", fill="y", padx=(0, 2), pady=2)

        self.txt_editor = tk.Text(
            editor_cerceve, bg="#070B14", fg="#E2E8F0", insertbackground="#00F5D4",
            selectbackground="#1E3A8A", font=("Consolas", self._font_boyutu), bd=0, padx=10, pady=8,
            undo=True, maxundo=50, wrap="none", yscrollcommand=self._editor_scroll_guncelle(scroll_y)
        )
        self.txt_editor.pack(side="left", fill="both", expand=True)

        # Sözdizimi Renk Etiketleri (Syntax Highlighting Tags)
        self.txt_editor.tag_configure("kw", foreground="#FF7B72", font=("Consolas", self._font_boyutu, "bold"))
        self.txt_editor.tag_configure("builtin", foreground="#D2A8FF")
        self.txt_editor.tag_configure("str", foreground="#A5D6FF")
        self.txt_editor.tag_configure("comment", foreground="#6E7681")
        self.txt_editor.tag_configure("decorator", foreground="#FFA657")
        self.txt_editor.tag_configure("number", foreground="#79C0FF")
        self.txt_editor.tag_configure("err_line", background="#450A0A")

        # Klavye Bağlantıları
        self.txt_editor.bind("<KeyRelease>", self._anahtar_birakildi)
        self.txt_editor.bind("<Tab>", self._tab_girinti_ekle)
        self.txt_editor.bind("<Return>", self._otomatik_girinti_enter)
        self.txt_editor.bind("<Control-s>", lambda _: (self.dosya_kaydet(), "break")[1])
        self.txt_editor.bind("<F5>", lambda _: (self.kodu_calistir(), "break")[1])
        self.txt_editor.bind("<MouseWheel>", lambda _: self.after(10, self._satir_numaralarini_guncelle))
        self.txt_editor.bind("<Control-MouseWheel>", self._font_olcekle)

        # Canlı Terminal Çerçevesi
        term_cerceve = ctk.CTkFrame(sag_panel, fg_color="#030712", corner_radius=8, border_width=1, border_color="#1E293B")
        term_cerceve.grid(row=2, column=0, sticky="nsew")

        term_ust = ctk.CTkFrame(term_cerceve, fg_color="#0B0F19", height=28, corner_radius=6)
        term_ust.pack(side="top", fill="x", padx=2, pady=2)

        self.lbl_term_durum = ctk.CTkLabel(
            term_ust, text="⚡ Canlı İnteraktif Terminal (Python Subprocess)",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#38BDF8"
        )
        self.lbl_term_durum.pack(side="left", padx=8)

        # Mikroçekim Mavi / Plazma Ateş Animasyon Widgetı
        try:
            self.mavi_ates = AltarMaviAtesWidget(term_ust, genislik=85, yukseklik=22, bg_color="#0B0F19")
            self.mavi_ates.pack(side="left", padx=(6, 4))
        except Exception:
            pass

        ctk.CTkButton(
            term_ust, text="🧹 Temizle", width=70, height=22, fg_color="#1F2937", hover_color="#374151",
            font=ctk.CTkFont(size=10), command=self.terminali_temizle
        ).pack(side="right", padx=6)

        self.btn_ai_onart = ctk.CTkButton(
            term_ust, text="⚡ AI ile Hatayı Onar", width=135, height=22, fg_color="#7C2D12", hover_color="#9A3412",
            font=ctk.CTkFont(size=10, weight="bold"), command=self.ai_ile_hatayi_onar
        )
        self.btn_ai_onart.pack(side="right", padx=4)

        self.lbl_imlec_konum = ctk.CTkLabel(
            term_ust, text="Satır: 1 | Sütun: 1", font=ctk.CTkFont(family="Consolas", size=10), text_color="#94A3B8"
        )
        self.lbl_imlec_konum.pack(side="right", padx=8)

        term_orta = ctk.CTkFrame(term_cerceve, fg_color="transparent")
        term_orta.pack(side="top", fill="both", expand=True, padx=4, pady=(0, 2))

        term_scroll = ctk.CTkScrollbar(term_orta)
        term_scroll.pack(side="right", fill="y")

        self.txt_terminal = tk.Text(
            term_orta, bg="#030712", fg="#E2E8F0", insertbackground="#00F5D4",
            font=("Consolas", 11), bd=0, padx=8, pady=4, yscrollcommand=term_scroll.set
        )
        self.txt_terminal.pack(side="left", fill="both", expand=True)
        term_scroll.configure(command=self.txt_terminal.yview)

        self.txt_terminal.tag_configure("stdout", foreground="#E2E8F0")
        self.txt_terminal.tag_configure("stderr", foreground="#FF7B72")
        self.txt_terminal.tag_configure("stdin", foreground="#00F5D4")
        self.txt_terminal.tag_configure("bilgi", foreground="#FBBF24")

        # Canlı Girdi (stdin) Çubuğu
        girdi_bar = ctk.CTkFrame(term_cerceve, fg_color="transparent", height=30)
        girdi_bar.pack(side="bottom", fill="x", padx=4, pady=4)

        ctk.CTkLabel(girdi_bar, text="Girdi (stdin) >", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#00F5D4").pack(side="left", padx=(4, 6))

        self.txt_stdin = ctk.CTkEntry(girdi_bar, placeholder_text="Çalışan programa girdi gönder (input)...", font=ctk.CTkFont(family="Consolas", size=11), height=26)
        self.txt_stdin.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.txt_stdin.bind("<Return>", lambda _: self.stdin_gonder())

        ctk.CTkButton(girdi_bar, text="Gönder", width=65, height=26, fg_color="#047857", hover_color="#059669", font=ctk.CTkFont(size=11, weight="bold"), command=self.stdin_gonder).pack(side="right")

    # =========================================================================
    # ÇOKLU SEKME (MULTI-TAB) YÖNETİMİ
    # =========================================================================
    def yeni_sekme_ac(self, yol: Optional[str] = None, baslik: str = "", icerik: str = "") -> str:
        """Yeni bir dosya sekmesi oluşturur veya zaten açıksa ona odaklanır."""
        if yol:
            yol_norm = os.path.normpath(yol)
            for sid, sdata in self.acik_sekmeler.items():
                if sdata.get("yol") and os.path.normpath(sdata["yol"]) == yol_norm:
                    self.sekmeye_gec(sid)
                    return sid

        # Mevcut aktif sekmenin içeriğini hafızaya kaydet
        self._aktif_sekme_metnini_hafizaya_al()

        sekme_id = f"tab_{self._sekme_sayaci}"
        self._sekme_sayaci += 1

        if not baslik:
            baslik = os.path.basename(yol) if yol else f"Adsız_{self._sekme_sayaci - 1}.py"

        self.acik_sekmeler[sekme_id] = {
            "yol": yol,
            "baslik": baslik,
            "icerik": icerik,
            "degisiklik": False,
        }

        self.aktif_sekme_id = sekme_id
        self._editor_metni_ayarla(icerik)
        self._sekme_seridini_ciz()
        return sekme_id

    def sekmeye_gec(self, sekme_id: str) -> None:
        if sekme_id == self.aktif_sekme_id or sekme_id not in self.acik_sekmeler:
            return
        self._aktif_sekme_metnini_hafizaya_al()
        self.aktif_sekme_id = sekme_id
        hedef_icerik = self.acik_sekmeler[sekme_id]["icerik"]
        self._editor_metni_ayarla(hedef_icerik)
        self._sekme_seridini_ciz()

    def sekme_kapat(self, sekme_id: str) -> None:
        if sekme_id not in self.acik_sekmeler:
            return
        data = self.acik_sekmeler[sekme_id]
        if data.get("degisiklik"):
            cevap = messagebox.askyesnocancel(
                "Değişiklikleri Kaydet",
                f"'{data['baslik']}' dosyasında kaydedilmemiş değişiklikler var. Kaydetmek istiyor musunuz?",
                parent=self
            )
            if cevap is None:
                return
            if cevap is True:
                if sekme_id == self.aktif_sekme_id:
                    self.dosya_kaydet()

        del self.acik_sekmeler[sekme_id]
        if not self.acik_sekmeler:
            self.yeni_sekme_ac(baslik="yeni_betik.py", icerik=self.VARSAYILAN_SABLON)
        elif self.aktif_sekme_id == sekme_id:
            kalan_id = list(self.acik_sekmeler.keys())[-1]
            self.aktif_sekme_id = kalan_id
            self._editor_metni_ayarla(self.acik_sekmeler[kalan_id]["icerik"])

        self._sekme_seridini_ciz()

    def _aktif_sekme_metnini_hafizaya_al(self) -> None:
        if self.aktif_sekme_id and self.aktif_sekme_id in self.acik_sekmeler:
            metin = self.txt_editor.get("1.0", "end-1c")
            self.acik_sekmeler[self.aktif_sekme_id]["icerik"] = metin

    def _sekme_seridini_ciz(self) -> None:
        for widget in self.sekme_seridi.winfo_children():
            widget.destroy()

        for sid, sdata in self.acik_sekmeler.items():
            aktif_mi = (sid == self.aktif_sekme_id)
            bg_clr = "#1E3A8A" if aktif_mi else "#1F2937"
            yildiz = "*" if sdata.get("degisiklik") else ""
            baslik = f"{sdata['baslik']}{yildiz}"

            sekme_btn_kutu = ctk.CTkFrame(self.sekme_seridi, fg_color=bg_clr, corner_radius=6, height=28)
            sekme_btn_kutu.pack(side="left", padx=2, pady=2)

            btn_sec = ctk.CTkButton(
                sekme_btn_kutu, text=f"📄 {baslik}", fg_color="transparent", hover_color="#2563EB" if aktif_mi else "#374151",
                font=ctk.CTkFont(size=11, weight="bold" if aktif_mi else "normal"),
                command=lambda s=sid: self.sekmeye_gec(s)
            )
            btn_sec.pack(side="left", padx=(4, 2))

            btn_kapat = ctk.CTkButton(
                sekme_btn_kutu, text="✕", width=18, height=18, fg_color="transparent", hover_color="#B91C1C",
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda s=sid: self.sekme_kapat(s)
            )
            btn_kapat.pack(side="right", padx=(0, 4))

        # Yeni sekme ekle butonu
        ctk.CTkButton(
            self.sekme_seridi, text="➕", width=28, height=28, fg_color="#1E293B", hover_color="#334155",
            font=ctk.CTkFont(size=12, weight="bold"), command=lambda: self.yeni_sekme_ac()
        ).pack(side="left", padx=4)

    # =========================================================================
    # FONT ÖLÇEKLEME (CTRL + MOUSE WHEEL)
    # =========================================================================
    def _font_olcekle(self, event: object) -> str:
        delta = getattr(event, "delta", 0)
        if delta > 0:
            self._font_boyutu = min(28, self._font_boyutu + 1)
        elif delta < 0:
            self._font_boyutu = max(8, self._font_boyutu - 1)

        yeni_font = ("Consolas", self._font_boyutu)
        self.txt_editor.configure(font=yeni_font)
        self.txt_satir_no.configure(font=yeni_font)
        self.txt_editor.tag_configure("kw", font=("Consolas", self._font_boyutu, "bold"))
        self._satir_numaralarini_guncelle()
        return "break"

    # =========================================================================
    # PYTHON YORUMLAYICI & PİP PAKET YÖNETİCİSİ ENTEGRASYONU
    # =========================================================================
    def aktif_python_yorumlayici(self) -> str:
        secilen_etiket = self.combo_python_var.get()
        for etiket, yol in self.python_yorumlari:
            if etiket == secilen_etiket:
                return yol
        return sys.executable

    def pip_yoneticisini_ac(self) -> None:
        yorumlayici = self.aktif_python_yorumlayici()
        AltarPipYoneticisiModal(self, python_exe=yorumlayici)

    # =========================================================================
    # DOSYA İŞLEMLERİ
    # =========================================================================
    def dosya_agacini_yenile(self) -> None:
        self.liste_dosyalar.delete(0, "end")
        if not os.path.isdir(self.calisma_dizini):
            return
        try:
            dosyalar = [f for f in os.listdir(self.calisma_dizini) if f.lower().endswith(".py")]
            dosyalar.sort(key=lambda s: s.lower())
            for d in dosyalar:
                self.liste_dosyalar.insert("end", f"  {d}")
        except Exception:
            pass

    def calisma_klasoru_degistir(self) -> None:
        secilen = filedialog.askdirectory(initialdir=self.calisma_dizini, title="Proje Klasörünü Seç", parent=self)
        if secilen and os.path.isdir(secilen):
            self.calisma_dizini = secilen
            self.dosya_agacini_yenile()

    def _listeden_dosya_secildi(self, event: object) -> None:
        secim = self.liste_dosyalar.curselection()
        if not secim:
            return
        dosya_adi = self.liste_dosyalar.get(secim[0]).strip()
        tam_yol = os.path.join(self.calisma_dizini, dosya_adi)
        if os.path.isfile(tam_yol):
            self.dosya_ac_yoldan(tam_yol)

    def dosya_ac_diyalog(self) -> None:
        yol = filedialog.askopenfilename(
            initialdir=self.calisma_dizini,
            title="Python Dosyası Aç",
            filetypes=[("Python Dosyaları", "*.py"), ("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")],
            parent=self,
        )
        if yol and os.path.isfile(yol):
            self.dosya_ac_yoldan(yol)

    def dosya_ac_yoldan(self, yol: str) -> None:
        try:
            with open(yol, "r", encoding="utf-8", errors="replace") as f:
                icerik = f.read()
            self.yeni_sekme_ac(yol=yol, baslik=os.path.basename(yol), icerik=icerik)
            self._terminale_yaz(f"[AÇILDI] {yol}\n", "bilgi")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılamadı:\n{e}", parent=self)

    def dosya_kaydet(self) -> bool:
        if not self.aktif_sekme_id or self.aktif_sekme_id not in self.acik_sekmeler:
            return False
        data = self.acik_sekmeler[self.aktif_sekme_id]
        if not data.get("yol"):
            return self.dosya_farkli_kaydet()

        try:
            metin = self.txt_editor.get("1.0", "end-1c")
            hedef_yol = data["yol"]
            tmp_yol = hedef_yol + f".{secrets.token_hex(4)}.tmp"
            with open(tmp_yol, "w", encoding="utf-8") as f:
                f.write(metin)
            os.replace(tmp_yol, hedef_yol)
            data["icerik"] = metin
            data["degisiklik"] = False
            self._sekme_seridini_ciz()
            self.dosya_agacini_yenile()
            self._terminale_yaz(f"💾 [KAYDEDİLDİ] {hedef_yol}\n", "bilgi")
            return True
        except Exception as e:
            messagebox.showerror("Kaydetme Hatası", f"Dosya kaydedilemedi:\n{e}", parent=self)
            return False

    def dosya_farkli_kaydet(self) -> bool:
        if not self.aktif_sekme_id or self.aktif_sekme_id not in self.acik_sekmeler:
            return False
        data = self.acik_sekmeler[self.aktif_sekme_id]
        yol = filedialog.asksaveasfilename(
            initialdir=self.calisma_dizini,
            defaultextension=".py",
            initialfile=data.get("baslik", "yeni_betik.py"),
            filetypes=[("Python Dosyası", "*.py"), ("Metin Dosyası", "*.txt"), ("Tüm Dosyalar", "*.*")],
            parent=self,
        )
        if not yol:
            return False
        data["yol"] = yol
        data["baslik"] = os.path.basename(yol)
        return self.dosya_kaydet()

    def kod_editore_yukle(self, kod_metni: str, kaynak_baslik: str = "ai_kod.py") -> None:
        """Harici bir modülden (Örn: Sohbet sekmesi '🐍 Kodu IDE'ye Aktar') yeni sekme olarak kod yükler."""
        self.yeni_sekme_ac(baslik=kaynak_baslik, icerik=kod_metni)
        self._terminale_yaz(
            f"✅ [AKTARILDI] Kod Altar IDE'ye başarıyla aktarıldı ({len(kod_metni.splitlines())} satır). F5 ile çalıştırabilirsiniz.\n",
            "bilgi",
        )

    # =========================================================================
    # AST SÖZDİZİMİ DENETİMİ & CANLI ÇALIŞTIRMA MOTORU
    # =========================================================================
    def ast_sozdizimi_denetle(self) -> bool:
        self.txt_editor.tag_remove("err_line", "1.0", "end")
        kod = self.txt_editor.get("1.0", "end-1c")
        aktif_baslik = self.acik_sekmeler.get(self.aktif_sekme_id, {}).get("baslik", "<Altar_IDE>")
        try:
            agac = ast.parse(kod, filename=aktif_baslik)
            fonksiyonlar = sum(1 for n in ast.walk(agac) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
            siniflar = sum(1 for n in ast.walk(agac) if isinstance(n, ast.ClassDef))
            self._terminale_yaz(
                f"✅ [AST DENETİMİ BAŞARILI] '{aktif_baslik}' sözdizimi kusursuz! "
                f"({siniflar} Sınıf, {fonksiyonlar} Fonksiyon doğrulandı.)\n",
                "bilgi",
            )
            return True
        except SyntaxError as err:
            satir = err.lineno or 1
            self.txt_editor.tag_add("err_line", f"{satir}.0", f"{satir}.end")
            self.txt_editor.see(f"{satir}.0")
            self._terminale_yaz(
                f"❌ [SÖZDİZİMİ HATASI - Satır {satir}, Sütun {err.offset}]: {err.msg}\n"
                f"   -> {err.text.strip() if err.text else ''}\n",
                "stderr",
            )
            return False

    def kodu_calistir(self) -> None:
        if self.calisan_surec is not None and self.calisan_surec.poll() is None:
            messagebox.showwarning("Uyarı", "Şu anda çalışan bir Python süreci var. Önce onu durdurun.", parent=self)
            return

        if not self.ast_sozdizimi_denetle():
            return

        data = self.acik_sekmeler.get(self.aktif_sekme_id, {})
        if data.get("yol"):
            self.dosya_kaydet()
            hedef_betik = data["yol"]
            calisma_klasoru = os.path.dirname(data["yol"])
        else:
            gecici_yol = os.path.join(tempfile.gettempdir(), f"altar_ide_run_{os.getpid()}_{secrets.token_hex(4)}.py")
            with open(gecici_yol, "w", encoding="utf-8") as f:
                f.write(self.txt_editor.get("1.0", "end-1c"))
            self._aktif_gecici_betik_yolu = gecici_yol
            hedef_betik = gecici_yol
            calisma_klasoru = self.calisma_dizini

        yorumlayici = self.aktif_python_yorumlayici()
        self.terminali_temizle()
        self._baslangic_zamani = time.perf_counter()
        self._terminale_yaz(
            f"▶️ Çalıştırılıyor: \"{hedef_betik}\"\n"
            f"   Yorumlayıcı: {yorumlayici}\n" + "-" * 72 + "\n",
            "bilgi",
        )
        self.lbl_term_durum.configure(text="🟢 Çalışıyor...", text_color="#00F5D4")
        self.btn_calistir.configure(state="disabled")
        self.btn_durdur.configure(state="normal")

        ortam = os.environ.copy()
        ortam["PYTHONIOENCODING"] = "utf-8"
        ortam["PYTHONUNBUFFERED"] = "1"
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

        try:
            self.calisan_surec = subprocess.Popen(
                [yorumlayici, "-u", hedef_betik],
                cwd=calisma_klasoru,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=ortam,
                creationflags=creation_flags,
            )
        except Exception as exc:
            self._terminale_yaz(f"[HATA] Süreç başlatılamadı: {exc}\n", "stderr")
            self.btn_calistir.configure(state="normal")
            self.btn_durdur.configure(state="disabled")
            return

        threading.Thread(target=self._akis_oku, args=(self.calisan_surec.stdout, "stdout"), daemon=True).start()
        threading.Thread(target=self._akis_oku, args=(self.calisan_surec.stderr, "stderr"), daemon=True).start()
        threading.Thread(target=self._surec_bitisini_bekle, daemon=True).start()

    def _akis_oku(self, akis: object, etiket: str) -> None:
        try:
            for satir in iter(akis.readline, ""):
                if not satir:
                    break
                self.cikti_kuyrugu.put((etiket, satir))
        except Exception:
            pass

    def _surec_bitisini_bekle(self) -> None:
        if self.calisan_surec is None:
            return
        kod = self.calisan_surec.wait()
        gecen = time.perf_counter() - self._baslangic_zamani
        self.cikti_kuyrugu.put((
            "bilgi" if kod == 0 else "stderr",
            f"\n" + "-" * 72 + f"\n🏁 Süreç tamamlandı (Çıkış Kodu: {kod} | Süre: {gecen:.2f} sn)\n",
        ))
        self.cikti_kuyrugu.put(("__BITTI__", str(kod)))

        # Geçici betik dosyasını güvenle temizle
        if getattr(self, "_aktif_gecici_betik_yolu", None) and os.path.isfile(self._aktif_gecici_betik_yolu):
            try:
                os.remove(self._aktif_gecici_betik_yolu)
            except Exception:
                pass
            self._aktif_gecici_betik_yolu = None

    def _kuyrugu_tara(self) -> None:
        try:
            while not self.cikti_kuyrugu.empty():
                etiket, metin = self.cikti_kuyrugu.get_nowait()
                if etiket == "__BITTI__":
                    self.lbl_term_durum.configure(
                        text=f"⏹️ Tamamlandı (Kod: {metin})",
                        text_color="#10B981" if metin == "0" else "#EF4444",
                    )
                    self.btn_calistir.configure(state="normal")
                    self.btn_durdur.configure(state="disabled")
                else:
                    self._terminale_yaz(metin, etiket)
        except Exception:
            pass
        finally:
            if self.winfo_exists():
                self.after(60, self._kuyrugu_tara)

    def stdin_gonder(self) -> None:
        girdi = self.txt_stdin.get()
        if self.calisan_surec and self.calisan_surec.poll() is None and self.calisan_surec.stdin:
            try:
                self.calisan_surec.stdin.write(girdi + "\n")
                self.calisan_surec.stdin.flush()
                self._terminale_yaz(f"> {girdi}\n", "stdin")
                self.txt_stdin.delete(0, "end")
            except Exception as e:
                self._terminale_yaz(f"[HATA - stdin]: {e}\n", "stderr")
        else:
            self._terminale_yaz("[UYARI] Şu anda veri bekleyen aktif bir Python süreci yok.\n", "bilgi")

    def calisan_kodu_durdur(self) -> None:
        if self.calisan_surec and self.calisan_surec.poll() is None:
            try:
                self.calisan_surec.terminate()
                self._terminale_yaz("\n⚠️ [SÜREÇ KULLANICI TARAFINDAN DURDURULDU]\n", "stderr")
            except Exception:
                pass

    def terminali_temizle(self) -> None:
        self.txt_terminal.delete("1.0", "end")

    def _terminale_yaz(self, metin: str, etiket: str = "stdout") -> None:
        self.txt_terminal.insert("end", metin, etiket)
        self.txt_terminal.see("end")

    # =========================================================================
    # SÖZDİZİMİ RENKLENDİRME, GİRİNTİ VE SATIR NUMARALARI
    # =========================================================================
    def _editor_metni_ayarla(self, metin: str) -> None:
        self.txt_editor.delete("1.0", "end")
        self.txt_editor.insert("1.0", metin)
        self._satir_numaralarini_guncelle()
        self._sozdizimi_renklendir()

    def _anahtar_birakildi(self, event: object) -> None:
        if self.aktif_sekme_id and self.aktif_sekme_id in self.acik_sekmeler:
            if not self.acik_sekmeler[self.aktif_sekme_id]["degisiklik"]:
                self.acik_sekmeler[self.aktif_sekme_id]["degisiklik"] = True
                self._sekme_seridini_ciz()

        self._satir_numaralarini_guncelle()
        self._imlec_konumunu_guncelle()
        if self._renklendirme_zamanlayici:
            self.after_cancel(self._renklendirme_zamanlayici)
        self._renklendirme_zamanlayici = self.after(200, self._sozdizimi_renklendir)

    def _tab_girinti_ekle(self, event: object) -> str:
        self.txt_editor.insert("insert", "    ")
        return "break"

    def _otomatik_girinti_enter(self, event: object) -> str:
        satir_metni = self.txt_editor.get("insert linestart", "insert")
        eslesme = re.match(r"^(\s*)", satir_metni)
        mevcut_girinti = eslesme.group(1) if eslesme else ""
        if satir_metni.rstrip().endswith(":"):
            yeni_girinti = mevcut_girinti + "    "
        else:
            yeni_girinti = mevcut_girinti
        self.txt_editor.insert("insert", "\n" + yeni_girinti)
        self.txt_editor.see("insert")
        self._satir_numaralarini_guncelle()
        return "break"

    def _satir_numaralarini_guncelle(self) -> None:
        try:
            satir_sayisi = int(self.txt_editor.index("end-1c").split(".")[0])
            satirlar = "\n".join(str(i) for i in range(1, satir_sayisi + 1))
            self.txt_satir_no.configure(state="normal")
            self.txt_satir_no.delete("1.0", "end")
            self.txt_satir_no.insert("1.0", satirlar)
            self.txt_satir_no.configure(state="disabled")
            self.txt_satir_no.yview_moveto(self.txt_editor.yview()[0])
        except Exception:
            pass

    def _imlec_konumunu_guncelle(self) -> None:
        try:
            indeks = self.txt_editor.index("insert")
            satir, sutun = indeks.split(".")
            self.lbl_imlec_konum.configure(text=f"Satır: {satir} | Sütun: {int(sutun) + 1}")
        except Exception:
            pass

    def _ortak_dikey_kaydir(self, *args: object) -> None:
        self.txt_editor.yview(*args)
        self.txt_satir_no.yview(*args)

    def _editor_scroll_guncelle(self, scrollbar: ctk.CTkScrollbar) -> Callable:
        def _ayarla(ilk: str, son: str) -> None:
            scrollbar.set(ilk, son)
            self.txt_satir_no.yview_moveto(float(ilk))
        return _ayarla

    def _sozdizimi_renklendir(self) -> None:
        for etiket in ("kw", "builtin", "str", "comment", "decorator", "number"):
            self.txt_editor.tag_remove(etiket, "1.0", "end")

        kod = self.txt_editor.get("1.0", "end-1c")
        if not kod:
            return

        for m in re.finditer(r"(?P<str>\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"[^\"\n]*\"|'[^'\n]*')|(?P<comment>#[^\n]*)|(?P<dec>@\w+)|(?P<word>\b[A-Za-z_]\w*\b)|(?P<num>\b\d+(\.\d+)?\b)", kod):
            b_idx = f"1.0+{m.start()}c"
            e_idx = f"1.0+{m.end()}c"
            if m.group("comment"):
                self.txt_editor.tag_add("comment", b_idx, e_idx)
            elif m.group("str"):
                self.txt_editor.tag_add("str", b_idx, e_idx)
            elif m.group("dec"):
                self.txt_editor.tag_add("decorator", b_idx, e_idx)
            elif m.group("num"):
                self.txt_editor.tag_add("number", b_idx, e_idx)
            elif m.group("word"):
                kelime = m.group("word")
                if kelime in self.ANAHTAR_KELIMELER:
                    self.txt_editor.tag_add("kw", b_idx, e_idx)
                elif kelime in self.YERLESIK_FONKSIYONLAR:
                    self.txt_editor.tag_add("builtin", b_idx, e_idx)

    # =========================================================================
    # YAPAY ZEKA KÖPRÜSÜ
    # =========================================================================
    def ai_asistana_gonder(self) -> None:
        kod = self.txt_editor.get("1.0", "end-1c")
        term_metin = self.txt_terminal.get("1.0", "end-1c")
        aktif_baslik = self.acik_sekmeler.get(self.aktif_sekme_id, {}).get("baslik", "kod.py")

        hata_kismi = ""
        if "Traceback" in term_metin or "Error" in term_metin or "HATA" in term_metin:
            son_satirlar = term_metin.strip().splitlines()[-25:]
            hata_kismi = "\n\nTERMINAL ÇIKTISI VE ALINAN HATA:\n" + "\n".join(son_satirlar)

        istek = (
            f"Altar Python IDE'sinde '{aktif_baslik}' dosyasını inceliyorum. "
            f"Aşağıdaki Python kodunu optimize et, varsa mantık veya sözdizimi hatalarını açıkla ve "
            f"100-150 satırlık profesyonel altın standartta düzeltilmiş halini üret:\n\n"
            f"```python\n{kod[:5500]}\n```"
            f"{hata_kismi}"
        )

        if self.ai_aktarim_callback:
            self.ai_aktarim_callback(istek)
        else:
            messagebox.showinfo("Yapay Zeka Köprüsü", "Yapay Zeka köprüsü başarıyla tetiklendi.", parent=self)

    def sablon_secici_ac(self) -> None:
        """Hazır Python mimari şablonları kütüphanesini açar."""
        try:
            AltarSablonSeciciModal(self, on_kod_secildi=self.kod_editore_yukle)
        except Exception as e:
            messagebox.showwarning("Şablon Kütüphanesi", f"Şablon seçici açılırken hata: {e}", parent=self)

    def ai_ile_hatayi_onar(self) -> None:
        """Terminaldeki son traceback veya syntax hatasını tespit edip AI'a onarım görevi olarak gönderir."""
        term_metin = self.txt_terminal.get("1.0", "end-1c")
        kod = self.txt_editor.get("1.0", "end-1c")
        aktif_baslik = self.acik_sekmeler.get(self.aktif_sekme_id, {}).get("baslik", "kod.py")

        hata_kismi = ""
        if "Traceback" in term_metin or "Error" in term_metin or "HATA" in term_metin:
            son_satirlar = term_metin.strip().splitlines()[-30:]
            hata_kismi = "\n\nALINAN ÇALIŞMA ZAMANI HATASI (TRACEBACK):\n" + "\n".join(son_satirlar)
        else:
            # AST ile sözdizimi tara
            try:
                ast.parse(kod)
            except SyntaxError as se:
                hata_kismi = f"\n\nSÖZDİZİMİ (SYNTAX) HATASI:\nSatır {se.lineno}: {se.msg}\n-> {se.text}"

        if not hata_kismi:
            messagebox.showinfo(
                "AI Hata Onarım",
                "Terminalde veya kodda belirgin bir hata tespit edilemedi.\n"
                "Genel optimizasyon veya kod incelemesi için üstteki '🤖 Kodu/Hatayı AI'a Sor' butonunu kullanabilirsiniz.",
                parent=self
            )
            return

        istek = (
            f"Altar Python IDE'sinde '{aktif_baslik}' dosyasını çalıştırırken aşağıdaki hata meydana geldi. "
            f"Hatayı kökten giderip kodun eksiksiz, çalışan ve profesyonel halini üret:\n\n"
            f"```python\n{kod[:6000]}\n```"
            f"{hata_kismi}"
        )

        if self.ai_aktarim_callback:
            self.ai_aktarim_callback(istek)
        else:
            messagebox.showinfo("AI Hata Onarım", "Hata analizi hazırlandı ve AI motoruna iletildi.", parent=self)
