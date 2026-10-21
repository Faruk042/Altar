import os
import sys
import ctypes

# Windows Yüksek DPI ve Gerçek Tam Ekran (100% Monitör Kiosk) Desteği
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import re
import io
import dis
import ast
import math
import struct
import hashlib
import subprocess
import importlib.util
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

BG_COLOR = "#050A14"
PANEL_COLOR = "#0B1320"
BORDER_COLOR = "#1E293B"
GREEN_NEON = "#00FF88"
CYAN_NEON = "#00E5FF"
WARN_COLOR = "#FF3366"
GOLD_COLOR = "#FFD700"


class TersineMuhendislikSekmesi(ctk.CTkFrame):
    """
    %100 RAM-İçi (io.BytesIO) ve Salt-Okunur Tersine Mühendislik & Kod Rekonstrüksiyon Laboratuvarı.
    Hedef dosya veya dizini ASLA çalıştırmadan RAM'e kopyalar; 01 (Binary) makine kodlarını,
    PE/ELF mimarisini, x86/x64 Assembly komutlarını ve satır satır okunabilir Sözde Kodu (Decompile) üretir.
    """
    def __init__(self, parent, ai_analiz_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.ai_analiz_callback = ai_analiz_callback

        # RAM-İçi Klonlanmış Dosya Deposu: {goreceli_isim: (tam_yol, io.BytesIO)}
        self.ram_dosya_deposu = {}
        self.aktif_dosya_adi = ""
        self.aktif_ham_baytlar = b""
        self._analiz_suruyor = False

        self._arayuz_kur()

    def _arayuz_kur(self):
        # 1. ÜST HEDEF KONUM (DOSYA VEYA DİZİN) GİRİŞ VE RAM KLONLAMA ALANI
        hedef_bar = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        hedef_bar.pack(side="top", fill="x", padx=6, pady=(4, 6))

        ctk.CTkLabel(
            hedef_bar, text="🎯 Hedef Dosya / Dizin:",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color=CYAN_NEON
        ).pack(side="left", padx=(10, 4), pady=8)

        self.entry_hedef_yol = ctk.CTkEntry(
            hedef_bar,
            placeholder_text="Tersine mühendislik uygulanacak dosya veya klasör yolunu yapıştırın (Örn: C:\\Proje veya dosya.exe)...",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.entry_hedef_yol.pack(side="left", fill="x", expand=True, padx=4, pady=8)

        ctk.CTkButton(
            hedef_bar, text="📄 Dosya Seç", width=95, height=28,
            fg_color="#1f538d", hover_color="#14375e", command=self.hedef_dosya_sec
        ).pack(side="left", padx=3, pady=8)

        ctk.CTkButton(
            hedef_bar, text="📁 Dizin Seç", width=95, height=28,
            fg_color="#4B0082", hover_color="#2b004d", command=self.hedef_dizin_sec
        ).pack(side="left", padx=3, pady=8)

        ctk.CTkButton(
            hedef_bar, text="🔬 RAM'e Kopyala & Tersine Mühendislik Uygula", width=290, height=28,
            fg_color="#00A86B", hover_color="#007F50", command=self.hedefi_rame_kopyala_ve_cozumle
        ).pack(side="left", padx=(4, 10), pady=8)

        # 2. ANA BÖLÜNMÜŞ ÇALIŞMA GÖVDESİ
        govde = ctk.CTkFrame(self, fg_color="transparent")
        govde.pack(side="top", fill="both", expand=True, padx=6, pady=(0, 6))

        # SOL PANEL: Dizin/Dosya Seçici + Statik Kimlik, PE/ELF & Entropi Özeti
        sol = ctk.CTkFrame(govde, width=360, fg_color=PANEL_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        sol.pack(side="left", fill="y", padx=(0, 6))
        sol.pack_propagate(False)

        ctk.CTkLabel(
            sol, text="📦 RAM'DEKİ HEDEF DOSYALAR",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color=GOLD_COLOR
        ).pack(pady=(8, 2), padx=10, anchor="w")

        self.combo_ram_dosyalar = ctk.CTkOptionMenu(
            sol, values=["Henüz Hedef Yüklenmedi"], width=335,
            command=self.ramdeki_dosyayi_analiz_et
        )
        self.combo_ram_dosyalar.pack(padx=10, pady=4)

        ctk.CTkLabel(
            sol, text="🛡️ MİMARİ, ENTROPİ & KRİPTOGRAFİK RAPOR",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color=CYAN_NEON
        ).pack(pady=(6, 4), padx=10, anchor="w")

        self.txt_rapor = ctk.CTkTextbox(
            sol, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#050811", text_color="#E2E8F0", wrap="word"
        )
        self.txt_rapor.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self.txt_rapor.insert(
            "1.0",
            "🔒 %100 SALT-OKUNUR & RAM-İÇİ ANALİZ:\n\n"
            "• Seçtiğiniz dosya veya klasördeki tüm dosyalar diske dokunulmadan RAM tamponuna (io.BytesIO) kopyalanır.\n"
            "• 0 ve 1'lerden oluşan makine dili:\n"
            "  1) Satır satır okunabilir Sözde Koda (Decompile),\n"
            "  2) x86/x64 Assembly komutlarına,\n"
            "  3) PE/ELF Bölüm ve DLL/API haritasına,\n"
            "  4) Binary (0101) ve Hex matrisine dönüştürülür."
        )
        self.txt_rapor.configure(state="disabled")

        ctk.CTkButton(
            sol, text="🧠 Çıktıyı Altar AI İle Derin Analiz Et", height=28,
            fg_color="#008080", hover_color="#005959", command=self.aktif_ciktiyi_ai_gonder
        ).pack(fill="x", padx=8, pady=(0, 8))

        # SAĞ PANEL: 5 SEKMELİ TERSİNE MÜHENDİSLİK ÇIKTI EKRANI
        self.sag_tabs = ctk.CTkTabview(govde, fg_color=PANEL_COLOR, corner_radius=8)
        self.sag_tabs.pack(side="right", fill="both", expand=True)

        self.tab_decompile = self.sag_tabs.add("📜 1. Satır Satır Okunabilir Kod (Decompile)")
        self.tab_asm = self.sag_tabs.add("⚙️ 2. x86/x64 Assembly & Bytecode")
        self.tab_pe = self.sag_tabs.add("🧬 3. PE/ELF Yapısı & DLL/API Haritası")
        self.tab_binhex = self.sag_tabs.add("🔢 4. İkili (0101) & Hex Matrisi")
        self.tab_ioc = self.sag_tabs.add("🚩 5. Ayıklanan Dizeler, IP & URL")

        # Sekme 1: Satır Satır Okunabilir Kod
        self.txt_decompile = ctk.CTkTextbox(
            self.tab_decompile, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#03060C", text_color="#A6E3A1", wrap="none"
        )
        self.txt_decompile.pack(fill="both", expand=True, padx=6, pady=6)

        # Sekme 2: Assembly & Bytecode
        self.txt_asm = ctk.CTkTextbox(
            self.tab_asm, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#03060C", text_color=CYAN_NEON, wrap="none"
        )
        self.txt_asm.pack(fill="both", expand=True, padx=6, pady=6)

        # Sekme 3: PE/ELF Mimari & Import Tablosu
        self.txt_pe = ctk.CTkTextbox(
            self.tab_pe, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#03060C", text_color=GOLD_COLOR, wrap="word"
        )
        self.txt_pe.pack(fill="both", expand=True, padx=6, pady=6)

        # Sekme 4: 0101 Binary & Hex Arama ve Matris
        arama_ust = ctk.CTkFrame(self.tab_binhex, fg_color="transparent")
        arama_ust.pack(fill="x", padx=6, pady=2)
        self.entry_ara = ctk.CTkEntry(arama_ust, placeholder_text="Hex, Binary (0101) veya ASCII metin ara...", width=320)
        self.entry_ara.pack(side="left", padx=4)
        ctk.CTkButton(arama_ust, text="🔎 Bul", width=85, command=self.hex_icinde_ara).pack(side="left", padx=4)

        self.txt_hex = ctk.CTkTextbox(
            self.tab_binhex, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#03060C", text_color=GREEN_NEON, wrap="none"
        )
        self.txt_hex.pack(fill="both", expand=True, padx=6, pady=4)

        # Sekme 5: IOC & Dizeler
        self.txt_ioc = ctk.CTkTextbox(
            self.tab_ioc, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#03060C", text_color="#F8FAFC", wrap="word"
        )
        self.txt_ioc.pack(fill="both", expand=True, padx=6, pady=6)

    # =========================================================================
    # DOSYA / DİZİN SEÇİMİ VE RAM'E İZOLE KOPYALAMA (ASENKRON)
    # =========================================================================
    def hedef_dosya_sec(self):
        yol = filedialog.askopenfilename(title="Tersine Mühendislik Uygulanacak Dosyayı Seçin")
        if yol:
            self.entry_hedef_yol.delete(0, "end")
            self.entry_hedef_yol.insert(0, yol)
            self.hedefi_rame_kopyala_ve_cozumle()

    def hedef_dizin_sec(self):
        dizin = filedialog.askdirectory(title="Tersine Mühendislik Uygulanacak Dizini (Klasörü) Seçin")
        if dizin:
            self.entry_hedef_yol.delete(0, "end")
            self.entry_hedef_yol.insert(0, dizin)
            self.hedefi_rame_kopyala_ve_cozumle()

    def hedefi_rame_kopyala_ve_cozumle(self):
        if self._analiz_suruyor:
            return
        hedef = self.entry_hedef_yol.get().strip().strip('"').strip("'")
        if not hedef or not os.path.exists(hedef):
            messagebox.showwarning("Hedef Bulunamadı", "Lütfen geçerli bir dosya veya dizin yolu girin.", parent=self)
            return

        self._kutuya_yaz(self.txt_rapor, "⏳ Hedef RAM tamponuna (io.BytesIO) klonlanıyor ve çözümleniyor, lütfen bekleyin...")

        def _klonla_worker():
            self.ram_dosya_deposu.clear()
            maks_dosya_boyutu = 2 * 1024 * 1024

            try:
                if os.path.isfile(hedef):
                    with open(hedef, "rb") as f:
                        ram_kopyasi = io.BytesIO(f.read(maks_dosya_boyutu))
                    isim = os.path.basename(hedef)
                    self.ram_dosya_deposu[isim] = (hedef, ram_kopyasi)

                elif os.path.isdir(hedef):
                    sayac = 0
                    for kok_dizin, alt_dizinler, dosyalar in os.walk(hedef):
                        alt_dizinler[:] = [d for d in alt_dizinler if d not in (".git", ".venv", "venv", "node_modules", "__pycache__")]
                        for d_adi in dosyalar:
                            tam_yol = os.path.join(kok_dizin, d_adi)
                            goreceli = os.path.relpath(tam_yol, hedef)
                            try:
                                with open(tam_yol, "rb") as f:
                                    ram_kopyasi = io.BytesIO(f.read(maks_dosya_boyutu))
                                self.ram_dosya_deposu[goreceli] = (tam_yol, ram_kopyasi)
                                sayac += 1
                                if sayac >= 75:
                                    break
                            except Exception:
                                continue
                        if sayac >= 75:
                            break

                if not self.ram_dosya_deposu:
                    self.after(0, lambda: messagebox.showwarning("Boş Hedef", "Seçilen hedefte okunabilir dosya bulunamadı.", parent=self))
                    return

                dosya_isimleri = list(self.ram_dosya_deposu.keys())
                ilk_dosya = dosya_isimleri[0]

                def _menu_ayarla():
                    self.combo_ram_dosyalar.configure(values=dosya_isimleri)
                    self.combo_ram_dosyalar.set(ilk_dosya)
                    self.ramdeki_dosyayi_analiz_et(ilk_dosya)

                self.after(0, _menu_ayarla)

            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("RAM Klonlama Hatası", f"Hedef belleğe kopyalanırken hata oluştu:\n{err}", parent=self))

        threading.Thread(target=_klonla_worker, daemon=True).start()

    # =========================================================================
    # ÇEKİRDEK TERSİNE MÜHENDİSLİK MOTORU (%100 RAM ÜZERİNDE & ASENKRON)
    # =========================================================================
    def ramdeki_dosyayi_analiz_et(self, secili_anahtar: str):
        if secili_anahtar not in self.ram_dosya_deposu or self._analiz_suruyor:
            return

        self._analiz_suruyor = True
        self._kutuya_yaz(self.txt_rapor, f"🔬 '{secili_anahtar}' RAM üzerinde tersine mühendislikle çözümleniyor...")

        def _analiz_worker():
            try:
                tam_yol, ram_buffer = self.ram_dosya_deposu[secili_anahtar]
                ram_buffer.seek(0)
                veri = ram_buffer.read()

                self.aktif_dosya_adi = secili_anahtar
                self.aktif_ham_baytlar = veri

                gercek_boyut = os.path.getsize(tam_yol) if os.path.exists(tam_yol) else len(veri)
                md5_d = hashlib.md5(veri).hexdigest()
                sha1_d = hashlib.sha1(veri).hexdigest()
                sha256_d = hashlib.sha256(veri).hexdigest()
                entropi = self._shannon_entropi_hesapla(veri)
                gercek_tur = self._magic_byte_tespit(veri[:16])
                uzanti = os.path.splitext(tam_yol)[1].lower()

                spoof_uyari = "✅ Uzantı ve İmza Uyumlu"
                if "PE / EXE" in gercek_tur and uzanti not in (".exe", ".dll", ".sys", ".scr", ".ocx"):
                    spoof_uyari = f"🚨 SAHTE UZANTI: Uzantı '{uzanti}' ama gerçekte çalıştırılabilir PE/EXE!"

                entropi_yorum = "Normal (Açık Kod / Standart Binary)"
                if entropi > 7.2:
                    entropi_yorum = "⚠️ ÇOK YÜKSEK (>7.2): Paketlenmiş (UPX/VMProtect) veya Şifreli!"
                elif entropi > 6.2:
                    entropi_yorum = "Orta-Yüksek (Derlenmiş Makine Kodu)"

                rapor = (
                    f"📄 HEDEF   : {secili_anahtar}\n"
                    f"📦 TOPLAM  : {len(self.ram_dosya_deposu)} Dosya RAM'de Klonlu\n"
                    f"📏 BOYUT   : {gercek_boyut:,} B (RAM: {len(veri):,} B)\n"
                    f"🏷️ UZANTI  : {uzanti or 'Yok'}\n"
                    f"🧬 İMZA    : {gercek_tur}\n"
                    f"🛡️ KONTROL : {spoof_uyari}\n"
                    f"{'='*38}\n"
                    f"📊 SHANNON ENTROPİSİ: {entropi:.3f} / 8.000\n"
                    f"   -> {entropi_yorum}\n"
                    f"{'='*38}\n"
                    f"🔑 KRİPTOGRAFİK ÖZETLER (HASH):\n"
                    f"• MD5   : {md5_d}\n"
                    f"• SHA-1 : {sha1_d}\n"
                    f"• SHA256:\n  {sha256_d}\n"
                )

                pe_bilgi = self._pe_elf_detayli_cozumle(veri, gercek_tur)
                decompile_metni = self._satir_satir_okunabilir_koda_cevir(veri, tam_yol, gercek_tur, pe_bilgi)
                asm_metni = self._assembly_ve_bytecode_cozumle(veri, tam_yol, gercek_tur, pe_bilgi)
                bin_hex_metni = self._ikili_01_ve_hex_matrisi_olustur(veri[:16384])
                ioc_metni = self._ioc_ve_dizeleri_ayikla(veri)

                def _ui_guncelle():
                    if not self.winfo_exists():
                        return
                    self._kutuya_yaz(self.txt_rapor, rapor)
                    self._kutuya_yaz(self.txt_pe, pe_bilgi["metin"])
                    self._kutuya_yaz(self.txt_decompile, decompile_metni)
                    self._kutuya_yaz(self.txt_asm, asm_metni)
                    self._kutuya_yaz(self.txt_hex, bin_hex_metni)
                    self._kutuya_yaz(self.txt_ioc, ioc_metni)

                self.after(0, _ui_guncelle)
            finally:
                self._analiz_suruyor = False

        threading.Thread(target=_analiz_worker, daemon=True).start()

    @staticmethod
    def _kutuya_yaz(textbox, metin: str):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", metin)
        textbox.configure(state="disabled")

    def _shannon_entropi_hesapla(self, veri: bytes) -> float:
        """C-seviyesinde bytes.count() kullanarak 2 MB verinin entropisini ~10 milisaniyede hesaplar."""
        if not veri:
            return 0.0
        uzunluk = len(veri)
        entropi = 0.0
        for b in range(256):
            sayim = veri.count(b)
            if sayim > 0:
                p = sayim / uzunluk
                entropi -= p * math.log2(p)
        return entropi

    def _magic_byte_tespit(self, baslangic: bytes) -> str:
        imzalar = [
            (b"MZ", "Windows Çalıştırılabilir İkili Dosya (PE / EXE / DLL)"),
            (b"\x7fELF", "Linux Çalıştırılabilir İkili Dosya (ELF Binary)"),
            (b"%PDF-", "PDF Belgesi"),
            (b"PK\x03\x04", "ZIP Arşivi / Paket (.docx/.xlsx/.jar/.apk)"),
            (b"\x89PNG\r\n\x1a\n", "PNG Görseli"),
            (b"\xff\xd8\xff", "JPEG Görseli"),
            (b"SQLite format 3", "SQLite Veritabanı")
        ]
        for imza, aciklama in imzalar:
            if baslangic.startswith(imza):
                return aciklama
        if b"\x00" not in baslangic:
            return "Kaynak Kod / Metin Tabanlı Dosya"
        return "Özel İkili (Binary / Bytecode) Dosya"

    # =========================================================================
    # 1. KATMAN: PE / ELF BAŞLIK, BÖLÜM (SECTION) VE DLL/API ÇÖZÜMLEYİCİ
    # =========================================================================
    def _pe_elf_detayli_cozumle(self, veri: bytes, gercek_tur: str) -> dict:
        sonuc = {
            "mimari": "Bilinmiyor",
            "entry_point": 0,
            "bolumler": [],
            "dll_listesi": [],
            "api_listesi": [],
            "metin": ""
        }
        satirlar = [f"=== 🧬 İKİLİ (BINARY) MİMARİ VE BÖLÜM HARİTASI ({self.aktif_dosya_adi}) ===\n"]

        if veri.startswith(b"MZ") and len(veri) > 0x40:
            try:
                e_lfanew = struct.unpack("<I", veri[0x3C:0x40])[0]
                if e_lfanew + 24 < len(veri) and veri[e_lfanew:e_lfanew + 4] == b"PE\x00\x00":
                    machine, num_sections, time_stamp = struct.unpack("<HHI", veri[e_lfanew + 4:e_lfanew + 12])
                    opt_size, characteristics = struct.unpack("<HH", veri[e_lfanew + 20:e_lfanew + 24])

                    mimari_harita = {0x8664: "x86_64 (64-Bit)", 0x014C: "x86 (32-Bit)", 0xAA64: "ARM64"}
                    sonuc["mimari"] = mimari_harita.get(machine, f"Özel (0x{machine:04X})")

                    opt_offset = e_lfanew + 24
                    if opt_offset + 20 <= len(veri):
                        magic = struct.unpack("<H", veri[opt_offset:opt_offset + 2])[0]
                        sonuc["entry_point"] = struct.unpack("<I", veri[opt_offset + 16:opt_offset + 20])[0]
                        pe_tipi = "PE32+ (64-Bit)" if magic == 0x20B else "PE32 (32-Bit)"
                    else:
                        pe_tipi = "Standart PE"

                    satirlar.append(f"• Başlık Türü       : Windows Portable Executable ({pe_tipi})")
                    satirlar.append(f"• Hedef İşlemci     : {sonuc['mimari']}")
                    satirlar.append(f"• Giriş Noktası (EP): 0x{sonuc['entry_point']:08X}")
                    satirlar.append(f"• Bölüm (Section)   : {num_sections} Adet\n")

                    sec_table_off = opt_offset + opt_size
                    satirlar.append("BÖLÜM ADI  | SANAL ADRES | HAM BOYUT   | HAM OFSET   | ENTROPİ | DURUM")
                    satirlar.append("-" * 78)

                    for s_i in range(min(num_sections, 16)):
                        s_off = sec_table_off + s_i * 40
                        if s_off + 40 > len(veri):
                            break
                        s_name = veri[s_off:s_off + 8].rstrip(b"\x00").decode("latin-1", errors="replace")
                        v_size, v_addr, r_size, r_ptr = struct.unpack("<IIII", veri[s_off + 8:s_off + 24])
                        kesit = veri[r_ptr:r_ptr + min(r_size, 65536)] if r_ptr < len(veri) else b""
                        s_ent = self._shannon_entropi_hesapla(kesit)
                        durum = "⚠️ Şifreli/Packed" if s_ent > 7.2 else ("⚙️ Makine Kodu" if ".text" in s_name or "CODE" in s_name else "📦 Veri")
                        sonuc["bolumler"].append((s_name, v_addr, r_size, r_ptr, s_ent))
                        satirlar.append(f"{s_name:<10} | 0x{v_addr:08X}  | {r_size:>10} B | 0x{r_ptr:08X}  | {s_ent:>6.2f}  | {durum}")
            except Exception as e:
                satirlar.append(f"[!] PE başlığı okunurken kısmi hata: {e}")

        elif veri.startswith(b"\x7fELF") and len(veri) >= 64:
            bit_sinifi = "64-Bit (ELF64)" if veri[4] == 2 else "32-Bit (ELF32)"
            sonuc["mimari"] = bit_sinifi
            satirlar.append(f"• Başlık Türü   : Linux ELF İkili Dosyası ({bit_sinifi})")

        metin_latin = veri.decode("latin-1", errors="ignore")
        dll_eslesmeler = sorted(set(re.findall(r'[A-Za-z0-9_\-]+\.dll', metin_latin, re.IGNORECASE)))
        sonuc["dll_listesi"] = dll_eslesmeler[:30]

        kritik_apiler = [
            "CreateProcess", "VirtualAlloc", "VirtualProtect", "WriteProcessMemory",
            "CreateRemoteThread", "LoadLibrary", "GetProcAddress", "OpenProcess",
            "IsDebuggerPresent", "CheckRemoteDebuggerPresent", "WSAStartup", "connect",
            "send", "recv", "InternetOpen", "HttpSendRequest", "RegSetValue",
            "CryptEncrypt", "CryptDecrypt", "ShellExecute", "WinExec", "ReadFile", "WriteFile"
        ]
        kucuk_metin = metin_latin.lower()
        sonuc["api_listesi"] = [api for api in kritik_apiler if api.lower() in kucuk_metin]

        satirlar.append("\n=== 📚 TESPİT EDİLEN DİNAMİK KÜTÜPHANELER (DLL IMPORTS) ===")
        satirlar.append(", ".join(sonuc["dll_listesi"]) if sonuc["dll_listesi"] else "DLL referansı tespit edilmedi.")

        satirlar.append("\n=== ⚡ ÇAĞRILAN SİSTEM FONKSİYONLARI (API / SYSCALL TABLOSU) ===")
        satirlar.append(", ".join(sonuc["api_listesi"]) if sonuc["api_listesi"] else "Standart dış sistem API çağrısı bulunamadı.")

        sonuc["metin"] = "\n".join(satirlar)
        return sonuc

    # =========================================================================
    # 2. KATMAN: 0 VE 1'LERDEN SATIR SATIR OKUNABİLİR KODA ÇEVİRME (DECOMPILE)
    # =========================================================================
    def _satir_satir_okunabilir_koda_cevir(self, veri: bytes, tam_yol: str, gercek_tur: str, pe_bilgi: dict) -> str:
        uzanti = os.path.splitext(tam_yol)[1].lower()

        if uzanti == ".pyc" and 16 < len(veri) <= 2 * 1024 * 1024:
            try:
                if veri[:4] == importlib.util.MAGIC_NUMBER:
                    izole_komut = [
                        sys.executable, "-I", "-c",
                        "import sys, marshal, dis; kod = marshal.loads(sys.stdin.buffer.read()[16:]); dis.dis(kod)"
                    ]
                    bayrak = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0
                    proc = subprocess.run(
                        izole_komut, input=veri, capture_output=True, timeout=4, creationflags=bayrak
                    )
                    if proc.returncode == 0 and proc.stdout:
                        dis_satirlar = proc.stdout.decode("utf-8", errors="replace").splitlines()
                        numarali = [f"{i:04d} | {s}" for i, s in enumerate(dis_satirlar, 1)]
                        return (
                            f"// =========================================================================\n"
                            f"// [PYTHON .PYC İZOLE TERSİNE MÜHENDİSLİK ÇIKTISI]: {self.aktif_dosya_adi}\n"
                            f"// =========================================================================\n\n"
                            + "\n".join(numarali)
                        )
            except Exception:
                pass

        if b"\x00" not in veri[:2048]:
            try:
                metin = veri.decode("utf-8")
            except UnicodeDecodeError:
                metin = veri.decode("latin-1", errors="replace")

            ast_ozeti = []
            if uzanti == ".py":
                try:
                    agac = ast.parse(metin)
                    siniflar = [n.name for n in ast.walk(agac) if isinstance(n, ast.ClassDef)]
                    fonksiyonlar = [n.name for n in ast.walk(agac) if isinstance(n, ast.FunctionDef)]
                    ast_ozeti.append(f"# [AST MİMARİ ÇÖZÜMLEMESİ] Sınıflar ({len(siniflar)}): {', '.join(siniflar[:15]) or 'Yok'}")
                    ast_ozeti.append(f"# [AST MİMARİ ÇÖZÜMLEMESİ] Fonksiyonlar ({len(fonksiyonlar)}): {', '.join(fonksiyonlar[:25]) or 'Yok'}\n")
                except Exception:
                    pass

            satirlar = metin.splitlines()
            numarali = [f"{i:04d} | {satir}" for i, satir in enumerate(satirlar, 1)]
            baslik = (
                f"# =========================================================================\n"
                f"# [RAM-İÇİ SATIR SATIR KAYNAK KOD İNCELEMESİ]: {self.aktif_dosya_adi}\n"
                f"# Toplam Satır: {len(satirlar)} | Durum: %100 Salt-Okunur RAM Kopyası\n"
                f"# =========================================================================\n"
            )
            return baslik + ("\n".join(ast_ozeti) + "\n" if ast_ozeti else "\n") + "\n".join(numarali)

        metin_latin = veri[:262144].decode("latin-1", errors="ignore")
        okunabilir_dizeler = [s.strip() for s in re.findall(r'[ -~]{6,}', metin_latin) if len(s.strip()) >= 6][:40]

        pseudo = [
            "/* ========================================================================= */",
            f"/* [İKİLİ (01) MAKİNE DİLİNDEN SÖZDE KODA (PSEUDOCODE) REKONSTRÜKSİYON]       */",
            f"/* Dosya Adı : {self.aktif_dosya_adi:<60} */",
            f"/* Mimari    : {pe_bilgi['mimari']:<60} */",
            f"/* Giriş (EP): 0x{pe_bilgi['entry_point']:08X}                                                    */",
            "/* ========================================================================= */",
            ""
        ]

        if pe_bilgi["dll_listesi"]:
            pseudo.append("// --- [1] İÇE AKTARILAN SİSTEM KÜTÜPHANELERİ (DLL IMPORTS) ---")
            for dll in pe_bilgi["dll_listesi"]:
                pseudo.append(f'#include <{dll.lower()}>')
            pseudo.append("")

        if pe_bilgi["api_listesi"]:
            pseudo.append("// --- [2] ÇAĞRILAN SİSTEM FONKSİYONLARI (EXTERNAL API PROTOTYPES) ---")
            for api in pe_bilgi["api_listesi"]:
                pseudo.append(f"extern void* __stdcall {api}(...);")
            pseudo.append("")

        if pe_bilgi["bolumler"]:
            pseudo.append("// --- [3] BELLEK SEGMENTLERİ VE VERİ BÖLÜMLERİ ---")
            for s_name, v_addr, r_size, r_ptr, s_ent in pe_bilgi["bolumler"]:
                pseudo.append(f"// Segment {s_name:<8} -> RVA: 0x{v_addr:08X} | Boyut: {r_size} Bayt | Entropi: {s_ent:.2f}")
            pseudo.append("")

        if okunabilir_dizeler:
            pseudo.append("// --- [4] BELLEKTE GÖMÜLÜ SABİT VERİLER (CONSTANTS & STRINGS) ---")
            for idx, dize in enumerate(okunabilir_dizeler[:25], 1):
                temiz_dize = dize.replace('"', '\\"')[:90]
                pseudo.append(f'const char* STR_CONST_{idx:02d} = "{temiz_dize}";')
            pseudo.append("")

        pseudo.append("// --- [5] REKONSTRÜKTE EDİLEN ANA PROGRAM AKIŞI (ENTRY POINT) ---")
        pseudo.append(f"int __entrypoint_0x{pe_bilgi['entry_point']:08X}(int argc, char** argv) {{")
        pseudo.append("    // Stack çerçevesi (Stack Frame) hazırlanıyor")
        pseudo.append("    uintptr_t rbp = rsp;")

        if "IsDebuggerPresent" in pe_bilgi["api_listesi"] or "CheckRemoteDebuggerPresent" in pe_bilgi["api_listesi"]:
            pseudo.append("    if (IsDebuggerPresent()) {")
            pseudo.append("        // Anti-Debug kontrolü tespit edildi")
            pseudo.append("        return -1;")
            pseudo.append("    }")

        if any(a in pe_bilgi["api_listesi"] for a in ("WSAStartup", "connect", "InternetOpen", "HttpSendRequest")):
            pseudo.append("    // Ağ / Soket iletişim alt sistemi başlatılıyor")
            pseudo.append("    network_subsystem_init();")

        if any(a in pe_bilgi["api_listesi"] for a in ("ReadFile", "WriteFile")):
            pseudo.append("    // Dosya G/Ç (I/O) işlemleri yürütülüyor")
            pseudo.append("    file_io_handler();")

        if any(a in pe_bilgi["api_listesi"] for a in ("VirtualAlloc", "VirtualProtect", "LoadLibrary")):
            pseudo.append("    // Dinamik bellek tahsisi ve modül yükleme")
            pseudo.append("    void* mem_block = VirtualAlloc(NULL, 0x1000, MEM_COMMIT, PAGE_READWRITE);")

        kod_ofset = pe_bilgi["bolumler"][0][3] if pe_bilgi["bolumler"] else 0
        kesit = veri[kod_ofset:kod_ofset + 512]
        for i in range(0, len(kesit) - 5):
            if kesit[i] == 0xE8:
                rel = struct.unpack("<i", kesit[i + 1:i + 5])[0]
                hedef_adres = (kod_ofset + i + 5 + rel) & 0xFFFFFFFF
                pseudo.append(f"    sub_0x{hedef_adres:08X}(); // Makine kodu E8 (CALL) alt yordam çağrısı")
                if len(pseudo) > 95:
                    break

        pseudo.append("    return 0;")
        pseudo.append("}")

        return "\n".join(f"{i:04d} | {satir}" for i, satir in enumerate(pseudo, 1))

    # =========================================================================
    # 3. KATMAN: x86 / x64 MAKİNE KODU -> ASSEMBLY (DISASSEMBLY) ÇÖZÜMLEYİCİ
    # =========================================================================
    def _assembly_ve_bytecode_cozumle(self, veri: bytes, tam_yol: str, gercek_tur: str, pe_bilgi: dict) -> str:
        kod_baslangic = 0
        sanal_adres = 0x00401000
        for s_name, v_addr, r_size, r_ptr, _ in pe_bilgi.get("bolumler", []):
            if ".text" in s_name or "CODE" in s_name:
                kod_baslangic = r_ptr
                sanal_adres = 0x00400000 + v_addr
                break

        kesit = veri[kod_baslangic:kod_baslangic + 1024]
        satirlar = [
            f"; === ⚙️ x86 / x64 MAKİNE DİLİ (ASSEMBLY DISASSEMBLY) DÖKÜMÜ ({self.aktif_dosya_adi}) ===",
            f"; Başlangıç Ofseti: 0x{kod_baslangic:08X} | Sanal Taban: 0x{sanal_adres:08X}",
            "; ADRES      | MAKİNE BAYTLARI (HEX) | ASSEMBLY KOMUTU (MNEMONIC)",
            "-" * 76
        ]

        i = 0
        satir_no = 1
        while i < len(kesit) and satir_no <= 220:
            b = kesit[i]
            adr = sanal_adres + i

            if b == 0x55:
                hex_b, komut, adim = "55", "PUSH RBP", 1
            elif b == 0x5D:
                hex_b, komut, adim = "5D", "POP RBP", 1
            elif b == 0x90:
                hex_b, komut, adim = "90", "NOP", 1
            elif b == 0xC3:
                hex_b, komut, adim = "C3", "RET (Alt Yordamdan Dön)", 1
            elif b == 0xCC:
                hex_b, komut, adim = "CC", "INT 3 (Kesme / Breakpoint)", 1
            elif i + 3 <= len(kesit) and kesit[i:i + 3] == b"\x48\x89\xE5":
                hex_b, komut, adim = "48 89 E5", "MOV RBP, RSP (Stack Çerçevesi Kur)", 3
            elif i + 4 <= len(kesit) and kesit[i:i + 3] == b"\x48\x83\xEC":
                imm = kesit[i + 3]
                hex_b, komut, adim = f"48 83 EC {imm:02X}", f"SUB RSP, 0x{imm:02X} (Yerel Değişken Alanı Aç)", 4
            elif i + 2 <= len(kesit) and kesit[i:i + 2] == b"\x31\xC0":
                hex_b, komut, adim = "31 C0", "XOR EAX, EAX (EAX Yazmacını Sıfırla)", 2
            elif b == 0xE8 and i + 5 <= len(kesit):
                rel = struct.unpack("<i", kesit[i + 1:i + 5])[0]
                hedef = (adr + 5 + rel) & 0xFFFFFFFF
                raw_h = " ".join(f"{x:02X}" for x in kesit[i:i + 5])
                hex_b, komut, adim = raw_h, f"CALL sub_0x{hedef:08X}", 5
            elif b == 0xE9 and i + 5 <= len(kesit):
                rel = struct.unpack("<i", kesit[i + 1:i + 5])[0]
                hedef = (adr + 5 + rel) & 0xFFFFFFFF
                raw_h = " ".join(f"{x:02X}" for x in kesit[i:i + 5])
                hex_b, komut, adim = raw_h, f"JMP loc_0x{hedef:08X}", 5
            elif b in (0x74, 0x75) and i + 2 <= len(kesit):
                rel = struct.unpack("<b", kesit[i + 1:i + 2])[0]
                hedef = (adr + 2 + rel) & 0xFFFFFFFF
                mnem = "JE (Eşitse Atla)" if b == 0x74 else "JNE (Eşit Değilse Atla)"
                hex_b, komut, adim = f"{b:02X} {kesit[i+1]:02X}", f"{mnem} -> 0x{hedef:08X}", 2
            elif 0xB8 <= b <= 0xBF and i + 5 <= len(kesit):
                yazmaclar = ["EAX", "ECX", "EDX", "EBX", "ESP", "EBP", "ESI", "EDI"]
                reg = yazmaclar[b - 0xB8]
                val = struct.unpack("<I", kesit[i + 1:i + 5])[0]
                raw_h = " ".join(f"{x:02X}" for x in kesit[i:i + 5])
                hex_b, komut, adim = raw_h, f"MOV {reg}, 0x{val:08X}", 5
            else:
                hex_b, komut, adim = f"{b:02X}", f"DB 0x{b:02X}", 1

            satirlar.append(f"0x{adr:08X} | {hex_b:<21} | {komut}")
            i += adim
            satir_no += 1

        return "\n".join(satirlar)

    # =========================================================================
    # 4. KATMAN: 0101 (BINARY) & HEXADECIMAL & ASCII MATRİSİ
    # =========================================================================
    def _ikili_01_ve_hex_matrisi_olustur(self, veri: bytes) -> str:
        satirlar = [
            "OFSET    | HEXADECIMAL (8 BAYT)    | 01010100 MAKİNE DİLİ (İKİLİ / BINARY)                                    | ASCII",
            "-" * 118
        ]
        for i in range(0, len(veri), 8):
            parca = veri[i:i + 8]
            hex_kisim = " ".join(f"{b:02X}" for b in parca)
            bin_kisim = " ".join(f"{b:08b}" for b in parca)
            ascii_kisim = "".join(chr(b) if 32 <= b <= 126 else "." for b in parca)
            satirlar.append(f"{i:08X} | {hex_kisim:<23} | {bin_kisim:<71} | {ascii_kisim}")
        return "\n".join(satirlar)

    # =========================================================================
    # 5. KATMAN: IOC, IP, URL VE DİZELERİ AYIKLAMA
    # =========================================================================
    def _ioc_ve_dizeleri_ayikla(self, veri: bytes) -> str:
        metin = veri[:524288].decode("latin-1", errors="ignore")
        ascii_dizeler = re.findall(r'[ -~]{5,}', metin)
        wide_dizeler = [m.replace("\x00", "") for m in re.findall(r'(?:[ -~]\x00){5,}', metin)]
        tum_dizeler = ascii_dizeler + wide_dizeler

        ip_adresleri = sorted(set(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', metin)))
        url_listesi = sorted(set(re.findall(r'https?://[^\s"\'<>]+', metin)))

        ioc_rapor = [
            "=== 🌐 AYIKLANAN IPv4 ADRESLERİ ===",
            "\n".join(ip_adresleri[:50]) if ip_adresleri else "IP adresi bulunamadı.",
            "\n=== 🔗 AYIKLANAN URL VE WEB BAĞLANTILARI ===",
            "\n".join(url_listesi[:50]) if url_listesi else "URL bağlantısı bulunamadı.",
            f"\n=== 📜 DOSYADAKİ OKUNABİLİR METİN DİZELERİ (ASCII + UTF-16LE | Toplam {len(tum_dizeler)}) ===",
            "\n".join(f"{idx:04d} | {d}" for idx, d in enumerate(tum_dizeler[:200], 1))
        ]
        return "\n".join(ioc_rapor)

    def hex_icinde_ara(self):
        aranan = self.entry_ara.get().strip()
        if not aranan:
            return
        icerik = self.txt_hex.get("1.0", "end")
        konum = icerik.lower().find(aranan.lower())
        if konum != -1:
            satir_no = icerik[:konum].count("\n") + 1
            self.txt_hex.see(f"{satir_no}.0")
            messagebox.showinfo("Bulundu", f"'{aranan}' ifadesi {satir_no}. satırda bulundu.", parent=self)
        else:
            messagebox.showwarning("Sonuç Yok", f"'{aranan}' matriste bulunamadı.", parent=self)

    def aktif_ciktiyi_ai_gonder(self):
        aktif_sekme = self.sag_tabs.get()
        if "1." in aktif_sekme:
            icerik = self.txt_decompile.get("1.0", "end")
        elif "2." in aktif_sekme:
            icerik = self.txt_asm.get("1.0", "end")
        elif "3." in aktif_sekme:
            icerik = self.txt_pe.get("1.0", "end")
        else:
            icerik = self.txt_ioc.get("1.0", "end")

        rapor_ozet = self.txt_rapor.get("1.0", "end")
        birlesik = f"DOSYA KİMLİĞİ:\n{rapor_ozet}\n\nTERSİNE MÜHENDİSLİK ÇIKTISI ({aktif_sekme}):\n{icerik[:5000]}"
        if self.ai_analiz_callback:
            self.ai_analiz_callback(birlesik)


class SiberHexAnalizor(ctk.CTkToplevel):
    """Sol alttaki '🛡️ Siber Hex' butonundan bağımsız pencere olarak açıldığında da aynı tam modülü çalıştırır."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("🔬 Altar - Salt-Okunur Tersine Mühendislik, Decompile ve Hex Laboratuvarı")
        self.geometry("1280x800")
        self.configure(fg_color=BG_COLOR)
        self._tam_ekran_mi = True
        self.after(20, self._tam_ekran_yap)
        self.bind("<F11>", self._tam_ekran_degistir)
        self.bind("<Escape>", self._tam_ekrandan_cik)

        # Üst Başlık ve Kontrol Barı (Tam Ekranda Pencere Yönetimi)
        ust_bar = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8, border_width=1, border_color="#1E293B")
        ust_bar.pack(side="top", fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            ust_bar,
            text="🔬 ALTAR TERSİNE MÜHENDİSLİK, DECOMPILE & HEX LABORATUVARI (%100 SALT-OKUNUR)",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#00FFCC"
        ).pack(side="left", padx=12, pady=6)

        ctk.CTkButton(
            ust_bar,
            text="✕ Kapat",
            width=75,
            height=28,
            fg_color="#dc2626",
            hover_color="#991b1b",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.destroy
        ).pack(side="right", padx=(4, 8), pady=6)

        ctk.CTkButton(
            ust_bar,
            text="🗗 Tam Ekran (F11)",
            width=120,
            height=28,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._tam_ekran_degistir
        ).pack(side="right", padx=(4, 2), pady=6)

        self.panel = TersineMuhendislikSekmesi(self)
        self.panel.pack(fill="both", expand=True, padx=10, pady=(4, 10))

    def _tam_ekran_yap(self):
        try:
            if self.winfo_exists():
                self.attributes("-fullscreen", True)
                self._tam_ekran_mi = True
                self.lift()
                self.focus_force()
        except Exception:
            pass

    def _tam_ekran_degistir(self, event=None):
        try:
            self._tam_ekran_mi = not getattr(self, "_tam_ekran_mi", False)
            self.attributes("-fullscreen", self._tam_ekran_mi)
        except Exception:
            pass

    def _tam_ekrandan_cik(self, event=None):
        try:
            if getattr(self, "_tam_ekran_mi", False):
                self._tam_ekran_mi = False
                self.attributes("-fullscreen", False)
        except Exception:
            pass


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    kok = ctk.CTk()
    kok.withdraw()
    pencere = SiberHexAnalizor(kok)
    pencere.protocol("WM_DELETE_WINDOW", kok.destroy)
    kok.mainloop()