import os
import sys
import time
import queue
import threading
from datetime import datetime
import numpy as np
import sounddevice as sd
import soundfile as sf

try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

# Standart mikrofonlar için uyumlu ses kalitesi parametreleri
SAMPLE_RATE = 48000  # Desteklenmezse otomatik 44100 Hz'e düşer
CHANNELS = 1         # Mono kanal (Maksimum mikrofon uyumluluğu)
FILENAME = "ders_kaydi.wav"

KAYIT_KLASORU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Ses_Kayitlari")
os.makedirs(KAYIT_KLASORU, exist_ok=True)

q = queue.Queue()


def callback(indata, frames, time_info, status):
    """Mikrofondan gelen sesi anlık olarak kuyruğa aktarır."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())


class GelismisSesKayitMotoru:
    """
    Arka planda kesintisiz çalışan, Duraklat/Devam Et (Pause/Resume),
    Canlı Ses Seviyesi (VU Meter) ve Otomatik Frekans Dengeleme destekli ses kayıt motoru.
    """
    def __init__(self):
        self.kayit_aktif = False
        self.duraklatildi = False
        self.ses_kuyrugu = queue.Queue()
        self.anlik_seviye = 0.0
        self.baslangic_zamani = 0.0
        self.toplam_sure = 0.0
        self.aktif_dosya_yolu = ""
        self.aktif_ornekleme_hizi = SAMPLE_RATE

    @staticmethod
    def mikrofonlari_listele() -> list:
        cihazlar = []
        try:
            for idx, d in enumerate(sd.query_devices()):
                if d.get('max_input_channels', 0) > 0:
                    cihazlar.append(f"{idx}: {d.get('name', 'Mikrofon')}")
        except Exception:
            pass
        return cihazlar if cihazlar else ["Varsayılan Mikrofon"]

    def _stream_callback(self, indata, frames, time_info, status):
        if not self.kayit_aktif or self.duraklatildi:
            self.anlik_seviye = 0.0
            return
        self.ses_kuyrugu.put_nowait(indata.copy())
        try:
            rms = float(np.sqrt(np.mean(np.square(indata))))
            self.anlik_seviye = min(1.0, rms * 8.5)
        except Exception:
            self.anlik_seviye = 0.0

    def kaydi_baslat(self, ozel_dosya_adi: str = "", cihaz_indeksi: int = None, bitti_callback=None) -> str:
        if self.kayit_aktif:
            return self.aktif_dosya_yolu

        # Önceki kayıttan kalan kuyruk verisi varsa temizle
        while not self.ses_kuyrugu.empty():
            try:
                self.ses_kuyrugu.get_nowait()
            except queue.Empty:
                break

        temiz_girdi = "".join(
            c for c in os.path.basename(ozel_dosya_adi.strip())
            if c not in '<>:"/\\|?*'
        ).strip(". ")
        if not temiz_girdi:
            zaman_etiketi = datetime.now().strftime("%Y%m%d_%H%M%S")
            ozel_dosya_adi = f"Altar_Kayit_{zaman_etiketi}.wav"
        elif not temiz_girdi.lower().endswith((".wav", ".flac")):
            ozel_dosya_adi = temiz_girdi + ".wav"
        else:
            ozel_dosya_adi = temiz_girdi

        self.aktif_dosya_yolu = os.path.join(KAYIT_KLASORU, ozel_dosya_adi)
        self.kayit_aktif = True
        self.duraklatildi = False
        self.toplam_sure = 0.0
        self.baslangic_zamani = time.time()

        def _yazici_thread():
            denenen_hizlar = [SAMPLE_RATE, 44100, 16000]
            basarili = False

            for hiz in denenen_hizlar:
                try:
                    self.aktif_ornekleme_hizi = hiz
                    with sf.SoundFile(self.aktif_dosya_yolu, mode='w', samplerate=hiz, channels=CHANNELS) as file:
                        with sd.InputStream(
                            samplerate=hiz, channels=CHANNELS, device=cihaz_indeksi, callback=self._stream_callback
                        ):
                            basarili = True
                            son_zaman = time.time()
                            while self.kayit_aktif:
                                simdi = time.time()
                                if not self.duraklatildi:
                                    self.toplam_sure += (simdi - son_zaman)
                                son_zaman = simdi
                                try:
                                    ilk_veri = self.ses_kuyrugu.get(timeout=0.15)
                                    file.write(ilk_veri)
                                    # Kuyrukta biriken diğer blokları tek seferde boşalt (Batch I/O)
                                    while not self.ses_kuyrugu.empty():
                                        file.write(self.ses_kuyrugu.get_nowait())
                                except queue.Empty:
                                    continue
                    break
                except Exception:
                    if self.kayit_aktif:
                        continue
                    break

            self.kayit_aktif = False
            self.anlik_seviye = 0.0
            if bitti_callback:
                bitti_callback(basarili, self.aktif_dosya_yolu)

        threading.Thread(target=_yazici_thread, daemon=True).start()
        return self.aktif_dosya_yolu

    def duraklat_devam_et(self) -> bool:
        if not self.kayit_aktif:
            return False
        self.duraklatildi = not self.duraklatildi
        return self.duraklatildi

    def kaydi_durdur(self) -> str:
        self.kayit_aktif = False
        self.duraklatildi = False
        self.anlik_seviye = 0.0
        return self.aktif_dosya_yolu

    @staticmethod
    def ses_dosyasini_oynat(dosya_yolu: str):
        if not os.path.exists(dosya_yolu):
            return
        def _oynat():
            try:
                sd.stop()
                veri, fs = sf.read(dosya_yolu, dtype='float32')
                sd.play(veri, fs)
                sd.wait()
            except Exception:
                pass
        threading.Thread(target=_oynat, daemon=True).start()

    @staticmethod
    def kaydi_metne_cevir(dosya_yolu: str) -> str:
        if not STT_AVAILABLE:
            return "[!] Metne çevirme için 'SpeechRecognition' kütüphanesi gerekli."
        if not os.path.exists(dosya_yolu):
            return "[!] Ses dosyası bulunamadı."
        try:
            r = sr.Recognizer()
            with sr.AudioFile(dosya_yolu) as kaynak:
                ses = r.record(kaynak)
            return r.recognize_google(ses, language="tr-TR")
        except Exception as e:
            return f"[!] Ses metne çevrilemedi: {e}"


# =========================================================================
# ALTAR GELİŞMİŞ SES STÜDYOSU PENCERESİ (KÜÇÜK BUTONDAN AÇILAN MERKEZ)
# =========================================================================
if CTK_AVAILABLE:
    class AltarSesKaydediciPenceresi(ctk.CTkToplevel):
        def __init__(self, parent, motor: GelismisSesKayitMotoru = None, metin_aktar_callback=None):
            super().__init__(parent)
            self.title("🎙️ Altar Ses Kayıt ve Transkripsiyon Stüdyosu")
            self.geometry("620x440")
            self.resizable(False, False)
            self.transient(parent)
            self.configure(fg_color="#090D16")

            self.motor = motor if motor else GelismisSesKayitMotoru()
            self.metin_aktar_callback = metin_aktar_callback
            self._son_sure_metni = ""

            self._arayuz_olustur()
            self._kayit_listesini_yenile()
            self._canli_sayac_guncelle()

        def _arayuz_olustur(self):
            ctk.CTkLabel(
                self, text="🎙️ ALTAR PROFESYONEL SES KAYIT STÜDYOSU (48kHz WAV)",
                font=ctk.CTkFont(family="Consolas", size=15, weight="bold"), text_color="#00FFCC"
            ).pack(pady=(12, 6))

            # Cihaz ve Dosya Adı Seçimi
            ayar_frame = ctk.CTkFrame(self, fg_color="#121824", corner_radius=8)
            ayar_frame.pack(fill="x", padx=16, pady=6)

            ctk.CTkLabel(ayar_frame, text="Mikrofon:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=8, pady=6, sticky="w")
            cihazlar = self.motor.mikrofonlari_listele()
            self.combo_cihaz = ctk.CTkOptionMenu(ayar_frame, values=cihazlar, width=230)
            self.combo_cihaz.grid(row=0, column=1, padx=6, pady=6)

            ctk.CTkLabel(ayar_frame, text="Dosya Adı:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=2, padx=8, pady=6, sticky="w")
            self.entry_dosya_adi = ctk.CTkEntry(ayar_frame, placeholder_text="ders_kaydi.wav", width=155)
            self.entry_dosya_adi.grid(row=0, column=3, padx=6, pady=6)
            self.entry_dosya_adi.insert(0, f"ders_kaydi_{datetime.now().strftime('%H%M%S')}.wav")

            # Canlı Süre ve VU Meter (Ses Seviyesi Çubuğu)
            sayac_frame = ctk.CTkFrame(self, fg_color="#05080F", corner_radius=8, border_width=1, border_color="#1E293B")
            sayac_frame.pack(fill="x", padx=16, pady=6)

            self.lbl_sure = ctk.CTkLabel(
                sayac_frame, text="⏺️ 00:00:00 | Durum: Hazır",
                font=ctk.CTkFont(family="Consolas", size=18, weight="bold"), text_color="#00FF88"
            )
            self.lbl_sure.pack(pady=(8, 4))

            self.vu_bar = ctk.CTkProgressBar(sayac_frame, width=520, height=14, progress_color="#00FF88")
            self.vu_bar.pack(pady=(2, 10))
            self.vu_bar.set(0.0)

            # Kayıt Kontrol Butonları
            btn_frame = ctk.CTkFrame(self, fg_color="transparent")
            btn_frame.pack(fill="x", padx=16, pady=6)

            self.btn_baslat = ctk.CTkButton(
                btn_frame, text="🔴 Kaydı Başlat", width=140, height=34,
                fg_color="#C62828", hover_color="#8E0000", font=ctk.CTkFont(weight="bold"),
                command=self.kayit_baslat_tetikle
            )
            self.btn_baslat.pack(side="left", padx=4, expand=True, fill="x")

            self.btn_duraklat = ctk.CTkButton(
                btn_frame, text="⏸️ Duraklat", width=120, height=34,
                fg_color="#B85C00", hover_color="#8F4700", state="disabled",
                command=self.duraklat_tetikle
            )
            self.btn_duraklat.pack(side="left", padx=4, expand=True, fill="x")

            self.btn_durdur = ctk.CTkButton(
                btn_frame, text="⏹️ Bitir & Kaydet", width=140, height=34,
                fg_color="#2E7D32", hover_color="#1B5E20", state="disabled",
                command=self.kayit_durdur_tetikle
            )
            self.btn_durdur.pack(side="left", padx=4, expand=True, fill="x")

            # Kayıt Arşivi, Dinleme ve AI Metne Çevirme
            arsiv_frame = ctk.CTkFrame(self, fg_color="#121824", corner_radius=8)
            arsiv_frame.pack(fill="both", expand=True, padx=16, pady=(6, 12))

            ust_arsiv = ctk.CTkFrame(arsiv_frame, fg_color="transparent")
            ust_arsiv.pack(fill="x", padx=8, pady=6)

            ctk.CTkLabel(ust_arsiv, text="📂 Kayıtlar:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
            self.combo_kayitlar = ctk.CTkOptionMenu(ust_arsiv, values=["Kayıt Yok"], width=230)
            self.combo_kayitlar.pack(side="left", padx=6)

            ctk.CTkButton(
                ust_arsiv, text="▶️ Dinle", width=80, height=26,
                fg_color="#1f538d", command=self.secili_kaydi_dinle
            ).pack(side="left", padx=3)

            ctk.CTkButton(
                ust_arsiv, text="⏹️ Sustur", width=75, height=26,
                fg_color="#374151", command=lambda: sd.stop()
            ).pack(side="left", padx=3)

            ctk.CTkButton(
                ust_arsiv, text="📝 Metne Çevir & Sohbete Aktar", width=190, height=26,
                fg_color="#008080", command=self.secili_kaydi_metne_cevir
            ).pack(side="right", padx=4)

            self.txt_durum = ctk.CTkTextbox(
                arsiv_frame, font=ctk.CTkFont(family="Consolas", size=11),
                fg_color="#05080F", text_color="#E2E8F0", height=85
            )
            self.txt_durum.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            self.txt_durum.insert("1.0", f"[*] Kayıt Dizini: {KAYIT_KLASORU}\n")

        def kayit_baslat_tetikle(self):
            secim_str = self.combo_cihaz.get()
            cihaz_idx = int(secim_str.split(":")[0]) if ":" in secim_str and secim_str.split(":")[0].isdigit() else None
            dosya_adi = self.entry_dosya_adi.get().strip()

            yol = self.motor.kaydi_baslat(ozel_dosya_adi=dosya_adi, cihaz_indeksi=cihaz_idx, bitti_callback=self._kayit_tamamlandi_cb)
            self.btn_baslat.configure(state="disabled")
            self.btn_duraklat.configure(state="normal")
            self.btn_durdur.configure(state="normal")
            self.txt_durum.insert("end", f"🔴 Kayıt Başladı: {os.path.basename(yol)}\n")
            self.txt_durum.see("end")

        def duraklat_tetikle(self):
            durum = self.motor.duraklat_devam_et()
            if durum:
                self.btn_duraklat.configure(text="▶️ Devam Et", fg_color="#00A86B")
                self.txt_durum.insert("end", "⏸️ Kayıt duraklatıldı.\n")
            else:
                self.btn_duraklat.configure(text="⏸️ Duraklat", fg_color="#B85C00")
                self.txt_durum.insert("end", "▶️ Kayıt devam ediyor.\n")

        def kayit_durdur_tetikle(self):
            self.motor.kaydi_durdur()
            self.btn_baslat.configure(state="normal")
            self.btn_duraklat.configure(state="disabled", text="⏸️ Duraklat", fg_color="#B85C00")
            self.btn_durdur.configure(state="disabled")

        def _kayit_tamamlandi_cb(self, basarili: bool, dosya_yolu: str):
            def _ui():
                if not self.winfo_exists():
                    return
                if basarili:
                    self.txt_durum.insert("end", f"✅ Kayıt Tamamlandı ({self.motor.aktif_ornekleme_hizi} Hz): {os.path.basename(dosya_yolu)}\n")
                    self.entry_dosya_adi.delete(0, "end")
                    self.entry_dosya_adi.insert(0, f"ders_kaydi_{datetime.now().strftime('%H%M%S')}.wav")
                    self._kayit_listesini_yenile()
                else:
                    self.txt_durum.insert("end", "❌ Kayıt sırasında mikrofon hatası oluştu.\n")
                self.txt_durum.see("end")
            self.after(0, _ui)

        def _kayit_listesini_yenile(self):
            dosyalar = sorted(
                [f for f in os.listdir(KAYIT_KLASORU) if f.lower().endswith((".wav", ".flac"))],
                reverse=True
            )
            if dosyalar:
                self.combo_kayitlar.configure(values=dosyalar)
                self.combo_kayitlar.set(dosyalar[0])

        def secili_kaydi_dinle(self):
            secili = self.combo_kayitlar.get()
            tam_yol = os.path.join(KAYIT_KLASORU, secili)
            if os.path.exists(tam_yol):
                self.txt_durum.insert("end", f"▶️ Oynatılıyor: {secili}\n")
                self.motor.ses_dosyasini_oynat(tam_yol)

        def secili_kaydi_metne_cevir(self):
            secili = self.combo_kayitlar.get()
            tam_yol = os.path.join(KAYIT_KLASORU, secili)
            if not os.path.exists(tam_yol):
                return
            self.txt_durum.insert("end", f"[*] '{secili}' metne dönüştürülüyor...\n")

            def _cevir():
                metin = self.motor.kaydi_metne_cevir(tam_yol)
                def _yaz():
                    if not self.winfo_exists():
                        return
                    self.txt_durum.insert("end", f"📝 Döküm: {metin}\n")
                    self.txt_durum.see("end")
                    if self.metin_aktar_callback and not metin.startswith("[!]"):
                        self.metin_aktar_callback(metin)
                self.after(0, _yaz)

            threading.Thread(target=_cevir, daemon=True).start()

        def _canli_sayac_guncelle(self):
            if not self.winfo_exists():
                return
            if self.motor.kayit_aktif:
                sn = int(self.motor.toplam_sure)
                saat, kalan = divmod(sn, 3600)
                dk, saniye = divmod(kalan, 60)
                durum_ek = "DURAKLATILDI" if self.motor.duraklatildi else "KAYITTA"
                renk = "#FFD700" if self.motor.duraklatildi else "#FF4444"
                yeni_metin = f"🔴 {saat:02d}:{dk:02d}:{saniye:02d} | {durum_ek}"
                if yeni_metin != self._son_sure_metni:
                    self._son_sure_metni = yeni_metin
                    self.lbl_sure.configure(text=yeni_metin, text_color=renk)
                self.vu_bar.set(self.motor.anlik_seviye)
            else:
                hazir_metin = "⏺️ 00:00:00 | Durum: Hazır"
                if self._son_sure_metni != hazir_metin:
                    self._son_sure_metni = hazir_metin
                    self.lbl_sure.configure(text=hazir_metin, text_color="#00FF88")
                    self.vu_bar.set(0.0)
            self.after(140, self._canli_sayac_guncelle)


def ses_kaydet():
    print("=" * 50)
    print("🎙️  Kayıt Programı Başlatılıyor...")
    print("=" * 50)

    try:
        with sf.SoundFile(FILENAME, mode='w', samplerate=SAMPLE_RATE, channels=CHANNELS) as file:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
                print(f"\n🔴 Kayıt başladı! Sesi şu dosyaya yazıyor: {FILENAME}")
                print("⏹️  Kaydı bitirmek ve kaydetmek için 'Ctrl + C' tuşlarına basın.\n")
                while True:
                    file.write(q.get())
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print(f"✅ Kayıt başarıyla durduruldu ve kaydedildi: {FILENAME}")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Beklenmeyen bir hata oluştu: {e}")


if __name__ == "__main__":
    ses_kaydet()