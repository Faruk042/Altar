import os
import threading
import secrets
from cryptography.fernet import Fernet, InvalidToken

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


def sifrele(dosya_adi):
    """Dosyayı Fernet (AES-128-CBC + HMAC-SHA256) ile şifreler ve (BaşarıDurumu, Token/Hata) döndürür."""
    try:
        anahtar = Fernet.generate_key()
        fernet = Fernet(anahtar)

        if not os.path.isfile(dosya_adi) or os.path.islink(dosya_adi):
            return False, "Geçerli bir normal dosya seçilmedi."
        if os.path.getsize(dosya_adi) > 4 * 1024 * 1024 * 1024:
            return False, "Dosya boyutu 4 GB sınırını aşıyor."

        with open(dosya_adi, 'rb') as dosya:
            orijinal_veri = dosya.read()

        if orijinal_veri.startswith((b"gAAAA", b"ALTAR_VAULT_V2\n")):
            return False, "Bu dosya zaten şifrelenmiş görünüyor! Çift şifrelemeyi önlemek için işlem durduruldu."

        sifreli_veri = fernet.encrypt(orijinal_veri)
        del orijinal_veri

        # Atomik yazma (Veri kaybını ve bozulmasını önleme)
        tmp_dosya = dosya_adi + f".{secrets.token_hex(4)}.tmp"
        with open(tmp_dosya, 'wb') as dosya:
            dosya.write(sifreli_veri)
        os.replace(tmp_dosya, dosya_adi)

        anahtar_str = anahtar.decode()
        print("\n[+] BAŞARILI: Dosya başarıyla şifrelendi!")
        print("-" * 50)
        print(f"[!] LÜTFEN BU ANAHTARI (TOKEN) GÜVENLİ BİR YERE KAYDEDİN:\n{anahtar_str}")
        print("-" * 50)
        print("[!] DİKKAT: Anahtarı kaybederseniz dosyayı bir daha ASLA deşifre edemezsiniz!\n")
        return True, anahtar_str

    except Exception as e:
        hata = f"Şifreleme sırasında beklenmeyen bir sorun oluştu: {e}"
        print(f"\n[-] HATA: {hata}\n")
        return False, hata


def desifre_et(dosya_adi, anahtar_str):
    """Şifrelenmiş dosyayı verilen Token ile deşifre eder ve (BaşarıDurumu, Mesaj) döndürür."""
    try:
        anahtar = anahtar_str.strip().encode()
        fernet = Fernet(anahtar)

        with open(dosya_adi, 'rb') as dosya:
            sifreli_veri = dosya.read()

        desifreli_veri = fernet.decrypt(sifreli_veri)

        # Atomik yazma (Veri kaybını ve bozulmasını önleme)
        tmp_dosya = dosya_adi + f".{secrets.token_hex(4)}.tmp"
        with open(tmp_dosya, 'wb') as dosya:
            dosya.write(desifreli_veri)
        os.replace(tmp_dosya, dosya_adi)

        msg = "Token doğrulandı! Dosya başarıyla deşifre edildi ve eski haline getirildi."
        print(f"\n[+] BAŞARILI: {msg}\n")
        return True, msg

    except InvalidToken:
        msg = "Geçersiz veya yanlış anahtar (token)! Dosya deşifre edilemedi."
        print(f"\n[-] HATA: {msg}\n")
        return False, msg
    except Exception as e:
        msg = f"Deşifreleme sırasında beklenmeyen bir sorun oluştu: {e}"
        print(f"\n[-] HATA: {msg}\n")
        return False, msg


if CTK_AVAILABLE:
    class DosyaSifrelemePaneli(ctk.CTkFrame):
        """
        Güvenlik sekmesi altındaki 2'ye bölünmüş alanın 2. Bölümü (Sağ Taraf):
        Fernet (AES-128-CBC + HMAC-SHA256) Dosya Şifreleme ve Deşifreleme Arayüzü.
        """
        def __init__(self, parent):
            super().__init__(parent, fg_color="#0B1320", corner_radius=8, border_width=1, border_color="#1E293B")
            self._islem_aktif = False
            self._arayuz_kur()

        def _arayuz_kur(self):
            ust = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=6)
            ust.pack(side="top", fill="x", padx=6, pady=4)

            ctk.CTkLabel(
                ust, text="🔐 2. BÖLÜM: FERNET KRİPTOGRAFİK DOSYA ŞİFRELEME & DEŞİFRELEME",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#FFD700"
            ).pack(side="left", padx=8, pady=3)

            # Hedef Dosya Seçim Satırı
            dosya_bar = ctk.CTkFrame(self, fg_color="transparent")
            dosya_bar.pack(side="top", fill="x", padx=6, pady=2)

            ctk.CTkLabel(dosya_bar, text="Hedef Dosya:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(2, 4))
            self.entry_dosya = ctk.CTkEntry(
                dosya_bar, placeholder_text="Şifrelenecek / Deşifre edilecek dosya yolunu seçin veya yazın...",
                height=24, font=ctk.CTkFont(family="Consolas", size=11)
            )
            self.entry_dosya.pack(side="left", fill="x", expand=True, padx=4)

            ctk.CTkButton(
                dosya_bar, text="📂 Dosya Seç", width=95, height=24,
                fg_color="#1f538d", command=self.dosya_sec_diyalog
            ).pack(side="right", padx=2)

            # Anahtar (Token) ve İşlem Butonları Satırı
            token_bar = ctk.CTkFrame(self, fg_color="transparent")
            token_bar.pack(side="top", fill="x", padx=6, pady=2)

            ctk.CTkLabel(token_bar, text="Token/Anahtar:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(2, 4))
            self.entry_token = ctk.CTkEntry(
                token_bar, placeholder_text="Şifrelemede otomatik üretilir | Deşifreleme için anahtarı buraya yapıştırın...",
                height=24, font=ctk.CTkFont(family="Consolas", size=11)
            )
            self.entry_token.pack(side="left", fill="x", expand=True, padx=4)

            ctk.CTkButton(
                token_bar, text="📋 Kopyala", width=75, height=24,
                fg_color="#4B0082", command=self.anahtari_kopyala
            ).pack(side="left", padx=2)

            self.btn_sifrele = ctk.CTkButton(
                token_bar, text="🔒 1. Şifrele", width=95, height=24,
                fg_color="#8B0000", hover_color="#5c0000", command=self.arayuz_sifrele
            )
            self.btn_sifrele.pack(side="left", padx=2)

            self.btn_desifre = ctk.CTkButton(
                token_bar, text="🔓 2. Deşifre Et", width=105, height=24,
                fg_color="#00A86B", hover_color="#007F50", command=self.arayuz_desifre_et
            )
            self.btn_desifre.pack(side="left", padx=2)

            # Log ve Anahtar Çıktı Kutusu
            self.txt_kripto_log = ctk.CTkTextbox(
                self, font=ctk.CTkFont(family="Consolas", size=11),
                fg_color="#05080F", text_color="#E2E8F0", height=90, wrap="word"
            )
            self.txt_kripto_log.pack(side="top", fill="both", expand=True, padx=6, pady=(2, 6))
            self.txt_kripto_log.insert(
                "end",
                "[*] Fernet Kriptografi Motoru Hazır.\n"
                "• Dosya seçip '🔒 1. Şifrele' butonuna bastığınızda üretilen Token otomatik olarak kutuya yazılır.\n"
            )

        def dosya_sec_diyalog(self):
            yol = filedialog.askopenfilename(title="Şifrelenecek veya Deşifre Edilecek Dosyayı Seçin")
            if yol:
                self.entry_dosya.delete(0, "end")
                self.entry_dosya.insert(0, yol)

        def anahtari_kopyala(self):
            anahtar = self.entry_token.get().strip()
            if anahtar:
                self.clipboard_clear()
                self.clipboard_append(anahtar)
                self.txt_kripto_log.insert("end", "[+] Anahtar (Token) panoya kopyalandı!\n")
                self.txt_kripto_log.see("end")

        def arayuz_sifrele(self):
            if self._islem_aktif:
                return
            hedef = self.entry_dosya.get().strip().strip('"')
            if not hedef or not os.path.exists(hedef):
                messagebox.showwarning("Dosya Bulunamadı", "Lütfen geçerli bir dosya seçin!")
                return

            self._islem_aktif = True
            self.txt_kripto_log.insert("end", f"[*] '{os.path.basename(hedef)}' arka planda şifreleniyor...\n")
            self.txt_kripto_log.see("end")

            def _worker():
                try:
                    basarili, sonuc = sifrele(hedef)

                    def _ui():
                        if not self.winfo_exists():
                            return
                        if basarili:
                            self.entry_token.delete(0, "end")
                            self.entry_token.insert(0, sonuc)
                            self.txt_kripto_log.insert(
                                "end",
                                f"[+] ŞİFRELENDİ: {os.path.basename(hedef)}\n"
                                f"🔑 ÜRETİLEN ANAHTAR (TOKEN): {sonuc}\n"
                                f"⚠️ DİKKAT: Bu anahtarı güvenli bir yere kaydedin!\n"
                            )
                        else:
                            self.txt_kripto_log.insert("end", f"[-] HATA: {sonuc}\n")
                        self.txt_kripto_log.see("end")

                    self.after(0, _ui)
                finally:
                    self._islem_aktif = False

            threading.Thread(target=_worker, daemon=True).start()

        def arayuz_desifre_et(self):
            if self._islem_aktif:
                return
            hedef = self.entry_dosya.get().strip().strip('"')
            anahtar = self.entry_token.get().strip()
            if not hedef or not os.path.exists(hedef):
                messagebox.showwarning("Dosya Bulunamadı", "Lütfen deşifre edilecek dosyayı seçin!")
                return
            if not anahtar:
                messagebox.showwarning("Eksik Anahtar", "Lütfen deşifreleme anahtarını (Token) kutuya yapıştırın!")
                return

            self._islem_aktif = True
            self.txt_kripto_log.insert("end", f"[*] '{os.path.basename(hedef)}' arka planda deşifre ediliyor...\n")
            self.txt_kripto_log.see("end")

            def _worker():
                try:
                    basarili, mesaj = desifre_et(hedef, anahtar)

                    def _ui():
                        if not self.winfo_exists():
                            return
                        if basarili:
                            self.txt_kripto_log.insert("end", f"[+] DEŞİFRE EDİLDİ: {os.path.basename(hedef)} -> {mesaj}\n")
                        else:
                            self.txt_kripto_log.insert("end", f"[-] HATA: {mesaj}\n")
                        self.txt_kripto_log.see("end")

                    self.after(0, _ui)
                finally:
                    self._islem_aktif = False

            threading.Thread(target=_worker, daemon=True).start()


def ana_program():
    print("=== Gelişmiş Dosya Şifreleme ve Deşifreleme Aracı ===")
    dosya_adi = input("Lütfen işlem yapmak istediğiniz dosyanın adını (uzantısıyla birlikte, örn: gizli_bilgi.txt) girin: ")

    if not os.path.exists(dosya_adi):
        print(f"\n[-] HATA: '{dosya_adi}' adlı dosya bulunamadı. Lütfen dosyanın kod ile aynı dizinde olduğundan emin olun.")
        return

    while True:
        print(f"Hedef Dosya: {dosya_adi}")
        print("1. Dosyayı Şifrele")
        print("2. Dosyayı Deşifre Et")
        print("3. Programdan Çık")

        secim = input("Lütfen yapmak istediğiniz işlemi seçin (1/2/3): ")

        if secim == '1':
            sifrele(dosya_adi)
        elif secim == '2':
            anahtar_girdisi = input("\nLütfen deşifreleme için anahtarı (token) yapıştırın: ")
            desifre_et(dosya_adi, anahtar_girdisi.strip())
        elif secim == '3':
            print("\nÇıkış yapılıyor. İyi çalışmalar!")
            break
        else:
            print("\n[-] Geçersiz seçim. Lütfen sadece 1, 2 veya 3 tuşlayın.\n")


if __name__ == "__main__":
    ana_program()